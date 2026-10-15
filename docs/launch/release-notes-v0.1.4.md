# Certo v0.1.4

From `pip install certo` to a first verified task, with no reading.

## New

- **`certo init [FOLDER]`** creates a ready-to-use workspace (default
  `./certo-workspace`). It asks which provider you use (OpenAI, Anthropic,
  Google Gemini, Ollama, or any LiteLLM model), offers a default model,
  and takes your API key at a hidden prompt, or uses one you've already
  exported (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`). For
  Ollama it lists the models installed on the server. It writes:
  - `.env` with only your settings, plus the other providers' presets
    commented out (permissions `600`);
  - `.gitignore` for `.env`, `projects/` and `artifacts/`;
  - `tasks/`, with two sample tasks;
  - `README.md` with the next steps.

  There's deliberately no `--api-key` flag, because a key on the command
  line ends up in shell history. Flags `--provider`, `--model`,
  `--base-url`, `--yes`, `--force` and `--no-check` skip questions or
  steps. Without a terminal, init asks nothing.
- **A real model check.** After writing `.env`, init makes one request
  that must come back as a tool call, since that's how the agent works. It
  reports `ok: reachable, tool calling works.`, or the problem and its fix
  in one line: a rejected key, an unknown model, an unreachable server,
  no credit, or no tool calling.
- **`certo check`** runs the same check again from your workspace after
  you edit `.env`.
- **Sample tasks:**
  - `tasks/wordle.md`: a terminal Wordle in Python, with pytest tests for
    the repeated-letter rule;
  - `tasks/asteroids.md`: a browser game, with its rules tested by Node's
    built-in test runner. It needs Node 18 or newer and no npm packages.

## Fixed

- Certo could pick up settings from a `.env` outside the current folder.
  LiteLLM loaded one of its own on import, found by searching upward from
  LiteLLM's install folder (for example a `~/.env`), and its values won
  over `./.env`. Certo now turns that off (`LITELLM_MODE=PRODUCTION`,
  unless you set it).

## Default models

| Provider | Default |
| --- | --- |
| OpenAI | `openai/gpt-6.1-sol` |
| Anthropic | `anthropic/claude-sonnet-5-5` |
| Google Gemini | `gemini/gemini-3.8-flash` |
| Ollama | `ollama/qwen3-coder:30b` (smaller: `qwen2.5-coder:7b`) |

LiteLLM 1.105 or newer knows their prices. With an older LiteLLM they
still run, but cost shows as unknown.

## Upgrading

```bash
uv tool upgrade certo      # or: pip install -U certo
certo init
```
