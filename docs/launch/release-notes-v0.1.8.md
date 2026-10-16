# Certo v0.1.8

Give slow models the time they need.

## New

- **`CERTO_LLM_TIMEOUT_SECONDS`** sets how long one call to the model may
  take (default 300 seconds, as before; `0` means no limit). A call that
  takes longer fails and is tried again from the start, up to 5 more
  times, so a local model that needs more than 5 minutes per answer used to
  never get one. Raise it, for example to `900`, for a large local model.
- **`timeout_seconds` in `models.yaml`**, per model, with the same meaning
  and the same default of 300. Like the other fields of an entry, it is
  not taken from `.env`. It applies to `--auto-model` and `certo bench`.

Guide: [Ollama and local models](../guides/ollama-and-local-models.md#make-sure-the-model-fits-in-memory).
