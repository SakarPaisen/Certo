#!/usr/bin/env bash
# Install Certo the way users do and check it works outside the dev venv.
#
#   scripts/release_check.sh                 # build the wheel, then check it
#   scripts/release_check.sh --wheel PATH    # check an already-built wheel
#   scripts/release_check.sh --with-llm      # also run a real agent task
#
# The wheel is `uv tool install`ed into a throwaway UV_TOOL_DIR /
# UV_TOOL_BIN_DIR (never your real ones), and every command runs from an
# empty temp directory, so no repo file and no .env is picked up. Checks:
#
#   - `certo --help` works;
#   - `certo verify` on three fixture projects, with no LLM:
#       pass  - a Python project with passing tests      -> verified, exit 0
#       fail  - a Python project with a failing test     -> failed,   exit 1
#       dep   - tests import a package installed only in
#               the project's own .venv (not pytest)     -> verified, exit 0,
#               pytest installed into that .venv, and
#               nothing installed into Certo's own env;
#   - with --with-llm, the real smoke task against whatever LLM_* variables
#     are exported, expecting `Verification: verified`.
#
# Needs uv and network access (to install the wheel's dependencies and the
# fixtures' packages). Run it directly, not through `uv run`.
set -euo pipefail

usage() { sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'; }

wheel=""
with_llm=0
while [ $# -gt 0 ]; do
  case "$1" in
    --wheel) wheel="${2:?--wheel needs a path}"; shift 2 ;;
    --with-llm) with_llm=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

repo="$(cd "$(dirname "$0")/.." && pwd)"
# `cd && pwd` normalizes the path (e.g. a `//` from TMPDIR) to the form
# Certo prints, so its output can be matched against it.
work="$(cd "$(mktemp -d "${TMPDIR:-/tmp}/certo-release-check.XXXXXX")" && pwd)"
trap 'rm -rf "$work"' EXIT
# Nothing from the caller's virtualenv should leak into the checks.
unset VIRTUAL_ENV CONDA_PREFIX || true

failures=0
pass() { echo "  ok    $1"; }
fail() { echo "  FAIL  $1"; failures=$((failures + 1)); }

echo "== Wheel"
if [ -z "$wheel" ]; then
  uv build --wheel --out-dir "$work/dist" "$repo" >/dev/null
  wheel="$(ls "$work"/dist/certo-*.whl)"
fi
wheel="$(cd "$(dirname "$wheel")" && pwd)/$(basename "$wheel")"
echo "  $wheel"

echo "== uv tool install (throwaway tool dir)"
export UV_TOOL_DIR="$work/tools"
export UV_TOOL_BIN_DIR="$work/bin"
uv tool install --quiet "$wheel"
certo="$UV_TOOL_BIN_DIR/certo"
tool_python="$UV_TOOL_DIR/certo/bin/python"
[ -x "$certo" ] && pass "installed $certo" || fail "certo was not installed"

# run NAME EXPECTED_EXIT EXPECTED_LINE CMD...: run from an empty directory,
# print the full output, and check the exit code and verdict line.
run() {
  local name="$1" want_exit="$2" want_line="$3"
  shift 3
  local cwd="$work/cwd-$name" out code=0
  mkdir -p "$cwd"
  out="$(cd "$cwd" && "$@" 2>&1)" || code=$?
  echo "--- $name: $* (exit $code)"
  echo "$out" | sed 's/^/    /'
  [ "$code" = "$want_exit" ] && pass "$name exit code $code" || fail "$name exit code $code, expected $want_exit"
  if [ -n "$want_line" ]; then
    echo "$out" | grep -qx "$want_line" && pass "$name: $want_line" || fail "$name: missing '$want_line'"
  fi
  last_output="$out"
}

echo "== certo --version"
wheel_version="$(basename "$wheel" | cut -d- -f2)"
run version 0 "certo $wheel_version" "$certo" --version

echo "== certo --help"
run help 0 "" "$certo" --help
echo "$last_output" | grep -q "certo verify \[PATH\]" && pass "help mentions certo verify" || fail "help doesn't mention certo verify"

echo "== Fixtures"
fixtures="$work/fixtures"
mkdir -p "$fixtures/pass" "$fixtures/fail" "$fixtures/dep"

cat > "$fixtures/pass/hello.py" <<'PY'
def hello() -> str:
    return "hello"


if __name__ == "__main__":
    print(hello())
PY
cat > "$fixtures/pass/test_hello.py" <<'PY'
from hello import hello


def test_hello():
    assert hello() == "hello"
PY

cp "$fixtures/pass/hello.py" "$fixtures/fail/hello.py"
cat > "$fixtures/fail/test_hello.py" <<'PY'
from hello import hello


def test_hello():
    assert hello() == "goodbye"
PY

cat > "$fixtures/dep/pyproject.toml" <<'TOML'
[project]
name = "dep-fixture"
version = "0.0.0"
dependencies = ["tomli-w"]
TOML
cat > "$fixtures/dep/render.py" <<'PY'
import tomli_w


def render(data: dict) -> str:
    return tomli_w.dumps(data)
PY
cat > "$fixtures/dep/test_render.py" <<'PY'
from render import render


def test_render():
    assert render({"a": 1}) == "a = 1\n"
PY
# The dependency lives only in the project's own venv, without pytest.
uv venv --quiet "$fixtures/dep/.venv"
uv pip install --quiet --python "$fixtures/dep/.venv/bin/python" tomli-w
if "$tool_python" -c "import tomli_w" 2>/dev/null; then
  fail "tomli_w is importable from Certo's own environment; the dep fixture proves nothing"
fi

echo "== certo verify"
run verify-pass 0 "Verification: verified" "$certo" verify "$fixtures/pass"
run verify-fail 1 "Verification: failed" "$certo" verify "$fixtures/fail"
run verify-dep 0 "Verification: verified" "$certo" verify "$fixtures/dep"
echo "$last_output" | grep -q "Installed pytest into the project environment $fixtures/dep/.venv" \
  && pass "verify-dep: pytest installed into the project's venv" \
  || fail "verify-dep: no notice of pytest being installed into the project's venv"
"$fixtures/dep/.venv/bin/python" -c "import pytest" 2>/dev/null \
  && pass "pytest is in the project's venv" || fail "pytest is not in the project's venv"
if "$tool_python" -c "import pytest" 2>/dev/null; then
  fail "pytest is importable from Certo's own environment"
else
  pass "Certo's own environment still has no pytest"
fi

if [ "$with_llm" = 1 ]; then
  echo "== Live smoke task (--with-llm)"
  if [ -z "${LLM_MODEL:-}" ]; then
    fail "--with-llm needs LLM_MODEL (and LLM_API_KEY or LLM_BASE_URL) exported"
  else
    echo "  model: $LLM_MODEL"
    export CERTO_PROJECTS_DIR="$work/projects"
    run smoke 0 "Verification: verified" \
      "$certo" "Create hello.py that prints hello, plus a pytest test for it" --project smoke
  fi
fi

echo
if [ "$failures" -gt 0 ]; then
  echo "release check FAILED ($failures problem(s))"
  exit 1
fi
echo "release check passed"
