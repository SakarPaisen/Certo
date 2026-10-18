"""Rough model prices, for a cost estimate before anything runs: the
benchmark plan and the escalation prompt. From LiteLLM's price list; a
local model costs nothing."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

from .model_catalog import ModelCatalogEntry

# A rough per-run token count for the cost estimate, before any run has
# happened. One sample task run in the README used ~800k tokens, most of
# them cached input; this errs on the expensive side.
ESTIMATE_INPUT_TOKENS = 500_000
ESTIMATE_OUTPUT_TOKENS = 20_000
_LOCAL_PREFIXES = ("ollama", "ollama_chat", "lm_studio", "hosted_vllm", "llamafile")


def is_local_model_id(model: str) -> bool:
    """A model id whose provider prefix is a local server (Ollama and
    friends). Without the entry's address this is all that is known."""
    return model.split("/", 1)[0] in _LOCAL_PREFIXES


def is_local(entry: ModelCatalogEntry) -> bool:
    """A model served on this machine or this network (Ollama and friends)."""
    if is_local_model_id(entry.model):
        return True
    host = urlparse(entry.base_url or "").hostname
    if not host:
        return False
    if host == "localhost":
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return address.is_private or address.is_loopback or address.is_unspecified


def estimate_run_cost(entry: ModelCatalogEntry) -> float | None:
    """A rough cost of one run in USD, from LiteLLM's prices, or None when
    the model has no known price."""
    if is_local(entry):
        return 0.0
    try:
        import litellm

        prompt, completion = litellm.cost_per_token(
            model=entry.model,
            prompt_tokens=ESTIMATE_INPUT_TOKENS,
            completion_tokens=ESTIMATE_OUTPUT_TOKENS,
        )
    except Exception:  # noqa: BLE001 - unknown model or pricing: no estimate
        return None
    total = prompt + completion
    return total if total > 0 else None
