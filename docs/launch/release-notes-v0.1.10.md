# Certo v0.1.10

Your keys in one file, the model catalog in another.

## Changed: `models.yaml` is now two files

What used to be one `models.yaml` is split:

- **`models_list.yaml`**, the catalog: model ids, descriptions, ratings,
  `reasoning_effort`, `timeout_seconds`, task profiles and escalation
  ladders. No keys or addresses, so it can be shared.
- **`models.yaml`**, your personal settings: the models you use, by their
  name in the list, each with its `api_key` or `base_url`, `activated`, and
  optional overrides (ratings axis by axis, `reasoning_effort`,
  `timeout_seconds`, `description`).

Only the models listed in `models.yaml` are used. A name that isn't in the
list is an error: add new models to the list first.

**An existing `models.yaml` stops with an error** that says what to move:
put the model ids, ratings, `task_profiles` and `escalation` in a
`models_list.yaml`, and keep in `models.yaml` only names, keys, addresses
and `activated`.

## New

- **Both files ship as examples only**, `models_list.yaml.example` and
  `models.yaml.example`, inside the package. Certo never reads them: copy
  them and edit your copies. A new release updates the examples and never
  touches your files. When a file is missing, Certo prints the `cp`
  command for your installation.
- **Project files override user files.** Each file is looked up in the
  current folder, then in `~/.config/certo/` (next to the user `.env`).
  `CERTO_MODELS_LIST_FILE` (new) and `CERTO_MODELS_FILE` name a file
  explicitly; in `bench.yaml`, `models_list_file` (new) and `models_file`.
- **`certo check`** shows which two files it found and how many listed
  models aren't used.

## Good to know

- The example list carries ratings anchored to public benchmarks, explained
  in its comments.
- This release also contains everything from 0.1.9 (escalation, the
  `models.yaml` checks, `strategy: escalate`), which was not published on
  its own.

Reference: [models.yaml and models_list.yaml](../reference/models-yaml.md).
