from __future__ import annotations

from embodied_stressbench.envs.maniskill_env import ManiSkillManipulationEnv
from embodied_stressbench.envs.mock_env import MockManipulationEnv


def make_env(task: str, backend: str = "mock", seed: int = 0):
    if backend == "mock":
        return MockManipulationEnv(task=task, seed=seed)
    if backend == "maniskill":
        return ManiSkillManipulationEnv(task=task, seed=seed)
    raise ValueError(f"Unknown backend: {backend}")
