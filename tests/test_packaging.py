"""Builds the real sdist + wheel (`uv build`, exactly as the release workflow
does: the wheel is built from the sdist) and checks what's inside them.

No LLM, no network beyond what `uv build` needs to fetch hatchling. Skipped
when `uv` isn't on PATH.
"""

from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.skipif(shutil.which("uv") is None, reason="uv not installed")


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> dict[str, Path]:
    out = tmp_path_factory.mktemp("dist")
    subprocess.run(
        ["uv", "build", "--quiet", "--out-dir", str(out), str(_REPO_ROOT)],
        check=True,
        capture_output=True,
    )
    (wheel,) = out.glob("*.whl")
    (sdist,) = out.glob("*.tar.gz")
    return {"wheel": wheel, "sdist": sdist}


def _wheel_names(wheel: Path) -> list[str]:
    with zipfile.ZipFile(wheel) as zf:
        return zf.namelist()


def test_wheel_ships_the_builtin_skill_catalog(built):
    names = _wheel_names(built["wheel"])
    shipped = {
        Path(n).relative_to("certo/builtin_skills").as_posix()
        for n in names
        if n.startswith("certo/builtin_skills/")
    }
    repo = {
        p.relative_to(_REPO_ROOT / "src/certo/builtin_skills").as_posix()
        for p in (_REPO_ROOT / "src/certo/builtin_skills").rglob("*.md")
    }
    assert repo, "no built-in skills found in the source tree"
    assert repo <= shipped
    assert any(n.startswith("lifecycle/") for n in shipped)


def test_wheel_installs_exactly_the_certo_console_scripts(built):
    with zipfile.ZipFile(built["wheel"]) as zf:
        (ep_name,) = [n for n in zf.namelist() if n.endswith(".dist-info/entry_points.txt")]
        entry_points = zf.read(ep_name).decode()
    section = entry_points.split("[console_scripts]", 1)[1].split("[", 1)[0]
    scripts = {line.split("=")[0].strip() for line in section.splitlines() if "=" in line}
    assert scripts == {"certo", "certo-server", "certo-admin"}
