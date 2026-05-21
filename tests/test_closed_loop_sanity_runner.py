from __future__ import annotations

from pathlib import Path

from embodied_stressbench.runners.run_closed_loop_sanity import run_closed_loop_episode


def test_closed_loop_sanity_mock_records_diagnostic_and_task_success():
    output_dir = Path("ieee_access_revision_20260520/test_tmp_closed_loop_sanity")
    output_dir.mkdir(parents=True, exist_ok=True)
    result = run_closed_loop_episode(
        task="PickCube",
        baseline_name="oracle_target",
        seed=0,
        output_dir=output_dir,
        query="red cube",
        backend="mock",
        stressor="none",
        level=0,
    )

    assert result["status"] == "ok"
    assert result["diagnostic_success"] is True
    assert result["task_success"] is True
    assert result["agreement"] is True
    assert result["closed_loop_debug"]["scripted_executor"] == "mock_proxy"
