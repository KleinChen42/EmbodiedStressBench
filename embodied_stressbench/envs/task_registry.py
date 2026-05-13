from __future__ import annotations

from embodied_stressbench.envs.mock_env import MockManipulationEnv


def make_env(task: str, backend: str = "mock", seed: int = 0):
    if backend == "mock":
        return MockManipulationEnv(task=task, seed=seed)
    if backend == "maniskill":
        raise NotImplementedError(
            "ManiSkill backend is not implemented in the starter. "
            "Use CODEX_DAILY_PROMPTS.md Prompt 2 to add it."
        )
    raise ValueError(f"Unknown backend: {backend}")
