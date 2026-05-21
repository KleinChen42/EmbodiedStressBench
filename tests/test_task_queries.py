from __future__ import annotations

import yaml
from pathlib import Path
from uuid import uuid4

from embodied_stressbench.runners import run_matrix as run_matrix_module
from embodied_stressbench.runners.run_single import run_episode


def test_run_matrix_uses_task_specific_queries(monkeypatch):
    seen: list[tuple[str, str]] = []

    def fake_run_episode(*, task, baseline_name, seed, output_dir, query, backend, stressor, level, query_variant=None):
        seen.append((task, query))
        return {
            "status": "ok",
            "task": task,
            "baseline": baseline_name,
            "seed": seed,
            "stressor": stressor,
            "level": level,
            "success": True,
        }

    cfg = {
        "env_backend": "mock",
        "tasks": ["PickCube", "PickSingleYCB"],
        "baselines": ["oracle_target"],
        "stressors": ["none"],
        "levels": [0],
        "seeds": [0],
        "default_query": "target object",
        "task_queries": {"PickCube": "red cube"},
    }
    root = Path("ieee_access_revision_20260520/test_tmp_task_queries")
    root.mkdir(parents=True, exist_ok=True)
    config_path = root / "config.yaml"
    config_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    monkeypatch.setattr(run_matrix_module, "run_episode", fake_run_episode)

    run_matrix_module.run_matrix(config_path, root / "out")

    assert ("PickCube", "red cube") in seen
    assert ("PickSingleYCB", "target object") in seen


def test_run_matrix_expands_query_variants(monkeypatch):
    seen: list[tuple[str, str | None, str]] = []

    def fake_run_episode(*, task, baseline_name, seed, output_dir, query, backend, stressor, level, query_variant=None):
        seen.append((task, query_variant, query))
        query_part = "" if not query_variant else f"__q-{query_variant}"
        Path(output_dir, f"{task}__{baseline_name}__{stressor}_L{level}__seed{seed}{query_part}.json").write_text(
            "{}",
            encoding="utf-8",
        )
        return {
            "status": "ok",
            "task": task,
            "baseline": baseline_name,
            "seed": seed,
            "stressor": stressor,
            "level": level,
            "query_variant": query_variant,
            "success": True,
        }

    cfg = {
        "env_backend": "mock",
        "tasks": ["PickSingleYCB"],
        "baselines": ["crop_median_depth_grounding_dino"],
        "stressors": ["none"],
        "levels": [0],
        "seeds": [0],
        "default_query": "target object",
        "query_variants": {
            "generic": "target object",
            "label": "{target_label}",
        },
    }
    root = Path("ieee_access_revision_20260520") / f"test_tmp_query_variants_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    config_path = root / "config.yaml"
    config_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    monkeypatch.setattr(run_matrix_module, "run_episode", fake_run_episode)

    run_matrix_module.run_matrix(config_path, root / "out")

    assert ("PickSingleYCB", "generic", "target object") in seen
    assert ("PickSingleYCB", "label", "{target_label}") in seen
    assert (root / "out" / "PickSingleYCB__crop_median_depth_grounding_dino__none_L0__seed0__q-generic.json").exists()
    assert (root / "out" / "PickSingleYCB__crop_median_depth_grounding_dino__none_L0__seed0__q-label.json").exists()


def test_run_episode_formats_target_label_query_template():
    root = Path("ieee_access_revision_20260520") / f"test_tmp_query_template_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)

    result = run_episode(
        task="PickCube",
        baseline_name="oracle_target",
        seed=0,
        output_dir=root,
        query="{target_label}",
        backend="mock",
        stressor="none",
        level=0,
        query_variant="label",
    )

    assert result["query_template"] == "{target_label}"
    assert result["query_original"] == "red cube"
    assert result["query_context"]["target_label"] == "red cube"
