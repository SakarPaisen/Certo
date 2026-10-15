# Certo v0.1.3

Two changes since 0.1.1: Certo's LLM settings get their own prefix, and
every command gets `--version`. (0.1.2 was never published on its own;
its `--version` change ships here.)

## Breaking change: `LLM_*` is now `CERTO_LLM_*`

Certo's LLM settings now use their own prefix, so they can't clash with
other tools that read `LLM_MODEL`:

| 0.1.1 and earlier | 0.1.3 |
| --- | --- |
| `LLM_MODEL` | `CERTO_LLM_MODEL` |
| `LLM_API_KEY` | `CERTO_LLM_API_KEY` |
| `LLM_BASE_URL` | `CERTO_LLM_BASE_URL` |
| `LLM_REASONING_EFFORT` | `CERTO_LLM_REASONING_EFFORT` |

The old names are no longer read at all. Rename them in your `.env` or
shell, for example:

```bash
sed -i '' -E 's/^LLM_(MODEL|API_KEY|BASE_URL|REASONING_EFFORT)=/CERTO_LLM_\1=/' .env   # macOS
sed -i -E 's/^LLM_(MODEL|API_KEY|BASE_URL|REASONING_EFFORT)=/CERTO_LLM_\1=/' .env      # Linux
```

If you forget, the "required" error names the old variables it found and
the rename to make, without printing their values.

## New

- **`--version`** on `certo`, `certo-admin` and `certo-server`
  (`certo --version` prints `certo 0.1.3`). `certo-server --version` works
  without the `server` extra.

## Upgrading

```bash
uv tool upgrade certo      # or: pip install -U certo
```

Then rename your `LLM_*` variables as above.
