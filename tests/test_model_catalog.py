"""Tests for model_catalog.py: pure parsing/classification/scoring, no SDK,
no network. Every YAML fixture is written to tmp_path and parsed for real —
no mocking of yaml.safe_load itself.
"""

from __future__ import annotations

import pytest

from certo.model_catalog import (
    ModelCatalog,
    ModelCatalogEntry,
    ModelCatalogError,
    TaskProfile,
    classify_task,
    load_model_catalog,
    rank_candidates,
    score_entry,
)

_MINIMAL_YAML = """
models:
  - name: only-one
    model: openai/gpt-4o-mini
    ratings: {reasoning: 2, cost: 5}
"""

_FULL_YAML = """
models:
  - name: fast-cheap
    model: openai/gpt-4o-mini
    api_key: sk-fake
    description: "Fast and cheap."
    ratings: {reasoning: 2, cost: 5, precision: 3, code: 3}
  - name: balanced
    model: anthropic/claude-sonnet-4-5-20250929
    ratings: {reasoning: 4, cost: 3, precision: 4, code: 4}
  - name: deep-reasoner
    model: anthropic/claude-opus-4
    base_url: "https://example.invalid"
    reasoning_effort: high
    ratings: {reasoning: 5, cost: 1, precision: 5, code: 5}

task_profiles:
  debugging:
    triggers: [fix, bug, crash]
    weights: {reasoning: 3, precision: 2, code: 1, cost: 0.5}
  scaffolding:
    triggers: [scaffold, "create a new"]
    weights: {cost: 2, code: 1}
  default:
    weights: {reasoning: 1, cost: 1, precision: 1, code: 1}
"""


def _write(tmp_path, text: str) -> str:
    path = tmp_path / "models.yaml"
    path.write_text(text)
    return str(path)


# --- load_model_catalog: happy paths -----------------------------------


def test_loads_minimal_catalog_with_one_model_and_no_profiles(tmp_path):
    catalog = load_model_catalog(_write(tmp_path, _MINIMAL_YAML))

    assert len(catalog.models) == 1
    assert catalog.models[0] == ModelCatalogEntry(
        name="only-one",
        model="openai/gpt-4o-mini",
        ratings={"reasoning": 2.0, "cost": 5.0},
    )
    assert catalog.task_profiles == []


def test_loads_full_catalog_with_profiles(tmp_path):
    catalog = load_model_catalog(_write(tmp_path, _FULL_YAML))

    assert [m.name for m in catalog.models] == ["fast-cheap", "balanced", "deep-reasoner"]
    assert catalog.models[0].api_key == "sk-fake"
    assert catalog.models[2].base_url == "https://example.invalid"
    assert catalog.models[2].reasoning_effort == "high"
    assert {p.name for p in catalog.task_profiles} == {"debugging", "scaffolding", "default"}


# --- activated ---------------------------------------------------------


def test_activated_defaults_to_true_when_omitted(tmp_path):
    catalog = load_model_catalog(_write(tmp_path, _MINIMAL_YAML))

    assert catalog.models[0].activated is True


def test_activated_false_is_parsed(tmp_path):
    path = _write(
        tmp_path,
        "models:\n  - name: foo\n    model: openai/gpt-4o\n    activated: false\n",
    )
    catalog = load_model_catalog(path)

    assert catalog.models[0].activated is False


def test_activated_true_is_parsed(tmp_path):
    path = _write(
        tmp_path,
        "models:\n  - name: foo\n    model: openai/gpt-4o\n    activated: true\n",
    )
    catalog = load_model_catalog(path)

    assert catalog.models[0].activated is True


def test_non_boolean_activated_raises(tmp_path):
    path = _write(
        tmp_path,
        "models:\n  - name: foo\n    model: openai/gpt-4o\n    activated: maybe\n",
    )
    with pytest.raises(ModelCatalogError, match="'activated'"):
        load_model_catalog(path)


def test_duplicate_name_still_raises_when_one_is_deactivated(tmp_path):
    path = _write(
        tmp_path,
        "models:\n"
        "  - name: dup\n    model: openai/gpt-4o\n    activated: false\n"
        "  - name: dup\n    model: anthropic/claude-sonnet-4-5-20250929\n",
    )
    with pytest.raises(ModelCatalogError, match="duplicate model name"):
        load_model_catalog(path)


# --- load_model_catalog: error paths -------------------------------------


def test_missing_file_raises_clear_error(tmp_path):
    with pytest.raises(ModelCatalogError, match="no such file"):
        load_model_catalog(str(tmp_path / "does_not_exist.yaml"))


def test_invalid_yaml_raises(tmp_path):
    path = _write(tmp_path, "models: [this is not: valid: yaml: at all")
    with pytest.raises(ModelCatalogError, match="not valid YAML"):
        load_model_catalog(path)


def test_non_mapping_top_level_raises(tmp_path):
    path = _write(tmp_path, "- just\n- a\n- list\n")
    with pytest.raises(ModelCatalogError, match="mapping"):
        load_model_catalog(path)


def test_missing_models_key_raises(tmp_path):
    path = _write(tmp_path, "task_profiles: {}\n")
    with pytest.raises(ModelCatalogError, match="non-empty 'models' list"):
        load_model_catalog(path)


def test_empty_models_list_raises(tmp_path):
    path = _write(tmp_path, "models: []\n")
    with pytest.raises(ModelCatalogError, match="non-empty 'models' list"):
        load_model_catalog(path)


def test_model_entry_missing_name_raises(tmp_path):
    path = _write(tmp_path, "models:\n  - model: openai/gpt-4o\n")
    with pytest.raises(ModelCatalogError, match="'name'"):
        load_model_catalog(path)


def test_model_entry_missing_model_id_raises(tmp_path):
    path = _write(tmp_path, "models:\n  - name: foo\n")
    with pytest.raises(ModelCatalogError, match="'model'"):
        load_model_catalog(path)


def test_duplicate_model_names_raise(tmp_path):
    path = _write(
        tmp_path,
        "models:\n"
        "  - name: dup\n    model: openai/gpt-4o\n"
        "  - name: dup\n    model: anthropic/claude-sonnet-4-5-20250929\n",
    )
    with pytest.raises(ModelCatalogError, match="duplicate model name"):
        load_model_catalog(path)


def test_non_numeric_rating_raises(tmp_path):
    path = _write(
        tmp_path, "models:\n  - name: foo\n    model: openai/gpt-4o\n    ratings: {cost: high}\n"
    )
    with pytest.raises(ModelCatalogError, match="rating"):
        load_model_catalog(path)


def test_ratings_not_a_mapping_raises(tmp_path):
    path = _write(
        tmp_path, "models:\n  - name: foo\n    model: openai/gpt-4o\n    ratings: [1, 2, 3]\n"
    )
    with pytest.raises(ModelCatalogError, match="'ratings'"):
        load_model_catalog(path)


def test_task_profile_non_numeric_weight_raises(tmp_path):
    path = _write(
        tmp_path,
        "models:\n  - name: foo\n    model: openai/gpt-4o\n    ratings: {cost: 5}\n"
        "task_profiles:\n  bogus:\n    weights: {cost: lots}\n",
    )
    with pytest.raises(ModelCatalogError, match="weight"):
        load_model_catalog(path)


# --- classify_task ---------------------------------------------------------


def _catalog_with_profiles(*profiles: TaskProfile) -> ModelCatalog:
    return ModelCatalog(
        models=[ModelCatalogEntry(name="x", model="openai/gpt-4o")],
        task_profiles=list(profiles),
    )


def test_classify_task_matches_a_trigger_case_insensitively():
    debugging = TaskProfile(name="debugging", triggers=("fix", "bug"), weights={"reasoning": 3})
    default = TaskProfile(name="default", weights={"reasoning": 1})
    catalog = _catalog_with_profiles(debugging, default)

    profile = classify_task("Please FIX the crash in the parser", catalog)

    assert profile.name == "debugging"


def test_classify_task_first_declared_match_wins():
    first = TaskProfile(name="first", triggers=("fix",), weights={"a": 1})
    second = TaskProfile(name="second", triggers=("fix",), weights={"a": 2})
    catalog = _catalog_with_profiles(first, second)

    profile = classify_task("please fix this", catalog)

    assert profile.name == "first"


def test_classify_task_falls_back_to_default_profile():
    debugging = TaskProfile(name="debugging", triggers=("fix",), weights={"reasoning": 3})
    default = TaskProfile(name="default", weights={"reasoning": 1})
    catalog = _catalog_with_profiles(debugging, default)

    profile = classify_task("Write a haiku about clouds", catalog)

    assert profile.name == "default"


def test_classify_task_with_no_default_profile_synthesizes_empty_weights():
    debugging = TaskProfile(name="debugging", triggers=("fix",), weights={"reasoning": 3})
    catalog = _catalog_with_profiles(debugging)

    profile = classify_task("Write a haiku about clouds", catalog)

    assert profile.weights == {}


# --- score_entry / rank_candidates -----------------------------------------


def test_score_entry_is_a_weighted_sum():
    entry = ModelCatalogEntry(name="x", model="openai/gpt-4o", ratings={"reasoning": 4, "cost": 2})

    score = score_entry(entry, {"reasoning": 3, "cost": 1})

    assert score == 4 * 3 + 2 * 1


def test_score_entry_treats_a_missing_axis_as_zero():
    entry = ModelCatalogEntry(name="x", model="openai/gpt-4o", ratings={"reasoning": 4})

    score = score_entry(entry, {"reasoning": 1, "cost": 100})

    assert score == 4


def test_rank_candidates_sorts_descending_by_score():
    cheap = ModelCatalogEntry(name="cheap", model="a", ratings={"reasoning": 1, "cost": 5})
    smart = ModelCatalogEntry(name="smart", model="b", ratings={"reasoning": 5, "cost": 1})
    catalog = ModelCatalog(models=[cheap, smart], task_profiles=[])

    ranked = rank_candidates(catalog, {"reasoning": 1, "cost": 0})

    assert [e.name for e in ranked] == ["smart", "cheap"]


def test_rank_candidates_breaks_ties_by_declared_order():
    a = ModelCatalogEntry(name="a", model="x", ratings={"reasoning": 3})
    b = ModelCatalogEntry(name="b", model="y", ratings={"reasoning": 3})
    catalog = ModelCatalog(models=[a, b], task_profiles=[])

    ranked = rank_candidates(catalog, {"reasoning": 1})

    assert [e.name for e in ranked] == ["a", "b"]


def test_rank_candidates_works_with_a_single_model_catalog():
    only = ModelCatalogEntry(name="only", model="x", ratings={"reasoning": 3})
    catalog = ModelCatalog(models=[only], task_profiles=[])

    ranked = rank_candidates(catalog, {"reasoning": 1})

    assert ranked == [only]


def test_rank_candidates_excludes_deactivated_models():
    active = ModelCatalogEntry(name="active", model="x", ratings={"reasoning": 1})
    inactive = ModelCatalogEntry(
        name="inactive", model="y", ratings={"reasoning": 5}, activated=False
    )
    catalog = ModelCatalog(models=[active, inactive], task_profiles=[])

    ranked = rank_candidates(catalog, {"reasoning": 1})

    # inactive scores higher (5 vs 1) but must still be excluded entirely.
    assert ranked == [active]


def test_rank_candidates_raises_when_every_model_is_deactivated():
    only = ModelCatalogEntry(name="only", model="x", ratings={"reasoning": 3}, activated=False)
    catalog = ModelCatalog(models=[only], task_profiles=[])

    with pytest.raises(ModelCatalogError, match="activated"):
        rank_candidates(catalog, {"reasoning": 1})


# --- timeout_seconds -------------------------------------------------------------


def test_timeout_seconds_defaults_to_300_and_can_be_set(tmp_path):
    catalog = load_model_catalog(
        _write(
            tmp_path,
            """
models:
  - name: cloud
    model: openai/gpt-4o
  - name: slow-local
    model: ollama/qwen3-coder:30b
    timeout_seconds: 1200
  - name: no-limit
    model: ollama/big
    timeout_seconds: 0
""",
        )
    )

    assert [m.timeout_seconds for m in catalog.models] == [300, 1200, 0]


@pytest.mark.parametrize("value", ["-1", "'600'", "1.5", "true"])
def test_timeout_seconds_must_be_a_whole_number_of_seconds(tmp_path, value):
    text = f"models:\n  - name: m\n    model: openai/gpt-4o\n    timeout_seconds: {value}\n"
    with pytest.raises(ModelCatalogError, match="timeout_seconds"):
        load_model_catalog(_write(tmp_path, text))


# --- escalation section ----------------------------------------------------------

_TWO_MODELS = """
models:
  - name: local
    model: ollama/qwen3-coder:30b
    base_url: http://localhost:11434
    ratings: {code: 2, cost: 5}
  - name: cloud
    model: openai/gpt-4o
    api_key: sk-fake
    ratings: {code: 5, cost: 2}
"""


def test_no_escalation_section_gives_the_defaults(tmp_path):
    settings = load_model_catalog(_write(tmp_path, _TWO_MODELS)).escalation

    assert settings.cost_axis == "cost"
    assert settings.cost_axis_set is False
    assert settings.max_rungs == 3
    assert settings.ladders == {}


def test_escalation_section_with_both_ladder_forms(tmp_path):
    text = (
        _TWO_MODELS
        + """
escalation:
  cost_axis: price
  max_rungs: 4
  ladders:
    default:
      - model: local
        retries: 1
        reasoning_effort: ""
      - model: cloud
    careful:
      escalate_on_acceptance_failed: true
      rungs:
        - model: local
          reasoning_effort: max
"""
    )
    settings = load_model_catalog(_write(tmp_path, text)).escalation

    assert (settings.cost_axis, settings.cost_axis_set, settings.max_rungs) == ("price", True, 4)
    default = settings.ladders["default"]
    assert [r.model for r in default.rungs] == ["local", "cloud"]
    assert default.rungs[0].retries == 1
    assert default.rungs[0].reasoning_effort is None  # blank means the entry's own
    assert default.rungs[1].retries is None
    assert default.escalate_on_acceptance_failed is False
    careful = settings.ladders["careful"]
    assert careful.escalate_on_acceptance_failed is True
    assert careful.rungs[0].reasoning_effort == "max"


@pytest.mark.parametrize(
    ("section", "message"),
    [
        ("escalation: [a]", "'escalation' must be a mapping"),
        ("escalation: {colour: red}", "unknown key"),
        ("escalation: {max_rungs: 1}", "at least 2"),
        ("escalation: {max_rungs: two}", "at least 2"),
        ("escalation: {cost_axis: ''}", "cost_axis"),
        ("escalation: {ladders: [a]}", "mapping of name"),
        ("escalation: {ladders: {x: local}}", "list of rungs"),
        ("escalation: {ladders: {x: [local]}}", "each rung must be a mapping"),
        ("escalation: {ladders: {x: [{retries: 1}]}}", "'model'"),
        ("escalation: {ladders: {x: [{model: local, retries: 1.5}]}}", "'retries'"),
        ("escalation: {ladders: {x: [{model: local, colour: red}]}}", "unknown key"),
        ("escalation: {ladders: {x: {rungs: [], extra: 1}}}", "unknown key"),
        (
            "escalation: {ladders: {x: {rungs: [], escalate_on_acceptance_failed: 1}}}",
            "true or false",
        ),
    ],
)
def test_escalation_section_shape_errors(tmp_path, section, message):
    with pytest.raises(ModelCatalogError, match=message):
        load_model_catalog(_write(tmp_path, _TWO_MODELS + section + "\n"))


def test_the_commented_example_in_models_yaml_example_parses(tmp_path):
    from pathlib import Path

    text = (Path(__file__).resolve().parent.parent / "models.yaml.example").read_text()
    block = text[text.index("# escalation:") :]
    uncommented = "\n".join(line[2:] for line in block.splitlines() if line.startswith("# "))
    models = text[
        : text.index(
            "# =============================================================================\n# DETERMINISTIC"
        )
    ]
    catalog = load_model_catalog(_write(tmp_path, models + "\n" + uncommented + "\n"))

    assert list(catalog.escalation.ladders) == ["default", "local-only"]
