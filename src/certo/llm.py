"""Builds the SDK's LLM object from our Config.

The model-agnostic invariant lives in config.py: provider/model selection is
entirely a function of `cfg.model`'s LiteLLM-style prefix (e.g. "anthropic/...",
"openai/...", "ollama/..."). The one provider-aware choice here is the
*default* reasoning effort for Ollama (see `_reasoning_effort_kwargs`); it
never changes which provider or model is called.
"""

from __future__ import annotations

from openhands.sdk import LLM
from pydantic import SecretStr

from .config import Config

# LiteLLM prefixes that route to an Ollama server.
_OLLAMA_PREFIXES = {"ollama", "ollama_chat"}


def _reasoning_effort_kwargs(cfg: Config) -> dict[str, str | None]:
    """The `reasoning_effort` kwarg for `LLM(...)`, or nothing.

    The SDK's own field defaults to "high", and `reasoning_effort=None` is a
    distinct, accepted value meaning "send no reasoning parameter" (its
    chat options skip it when None). So:

    - "none" (config folds "off" into it): pass an explicit None. Passing
      the string "none" through would still reach an Ollama model as
      `think: false`.
    - any other configured value: pass it through unchanged.
    - unset, Ollama model: pass None. LiteLLM turns "high" into
      `think: true`, and Ollama rejects that outright for a model with no
      thinking mode ("... does not support thinking"), failing the very
      first call. A thinking-capable Ollama model can still opt in with
      CERTO_LLM_REASONING_EFFORT.
    - unset, anything else: omit the kwarg so the SDK's "high" applies.
    """
    effort = cfg.reasoning_effort
    if effort == "none":
        return {"reasoning_effort": None}
    if effort:
        return {"reasoning_effort": effort}
    if cfg.model.split("/", 1)[0].lower() in _OLLAMA_PREFIXES:
        return {"reasoning_effort": None}
    return {}


def build_llm(cfg: Config, *, usage_id: str = "certo") -> LLM:
    return LLM(
        usage_id=usage_id,
        model=cfg.model,
        base_url=cfg.base_url,
        api_key=SecretStr(cfg.api_key) if cfg.api_key else None,
        **_reasoning_effort_kwargs(cfg),
    )
