# Certo v0.1.17

The example benchmark file now ships with Certo. This release also
contains [v0.1.16](release-notes-v0.1.16.md) and the unpublished versions
before it.

## New: `bench.yaml.example` comes with the package

After `pip install` or `uv tool install`, the example benchmark file used
to be missing, and the docs told you to download it. Now it is installed
with Certo, next to the model file examples. When there is no
`bench.yaml`, `certo bench` prints the command that copies it:

```text
Configuration error: benchmark file not found: bench.yaml. Certo ships an example to start from; copy it and name the models to compare:
  cp /path/to/certo/examples/bench.yaml.example bench.yaml
```

The path is where Certo is installed on your machine. See
[Write a benchmark file](../guides/write-a-benchmark-file.md).

## Changed: the examples use `qwen3.8-27b-local`

The example `models.yaml` and `bench.yaml` now name `qwen3.8-27b-local`
as the local model, instead of `qwen3.6-35b-local`. In Certo's
[0.1.15 benchmark](../benchmark/baseline-0.1.15.md), qwen3.8 passed 24 of
27 runs, and qwen3.6 none on the Ollama setup used. Your own copies of the
files are not changed.
