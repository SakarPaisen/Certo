# Certo v0.1.11

A derived ladder starts on the best cheap model, not the weakest one.

## Changed: how a derived ladder picks its models

When you run `--escalate` without writing a ladder, Certo builds one from
your ratings. Before, it put the least capable model first. That model
was often beaten by another one at the same price: with Devstral (5),
Gemma (5) and Qwen3.8 (8) all free, the first rung was Devstral, and the
three-rung limit could cut Qwen3.8 out entirely.

Now Certo starts from the cheapest models and takes the most capable of
them. Then it moves to more expensive models and keeps one only when it is
more capable than every model already kept: paying more must buy more. The
same example now gives `qwen3.8-27b-local -> gpt-5.6-luna ->
claude-sonnet-5-5`.

`certo check` and the ladder printed before a run name each model left
out, and the model that beats it:

```text
Left out of the derived ladder: gemma-local (qwen-local is at least as capable and costs no more)
```

An explicit ladder in `models_list.yaml` is unchanged and still wins over
a derived one. A `certo bench` arm with `strategy: escalate` and no
`models:` uses the new derived ladder.

## New in the example catalog

`models_list.yaml.example` adds `qwen3.8-27b-local`, `gpt-oss-20b-local`
and `devstral-small-2-local`, and its example ladders start on
`qwen3.8-27b-local`. Your own `models_list.yaml` is not changed: copy the
entries you want.

## Good to know

- The ratings know nothing about speed. To start on a faster model,
  write an explicit ladder.
- A model with no cost rating counts as the most expensive. If no model
  has a cost rating, every model is kept, least capable first, as before.
