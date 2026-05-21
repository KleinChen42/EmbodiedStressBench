from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

import numpy as np

from embodied_stressbench.envs.mock_env import ExecutionResult
from embodied_stressbench.types import Observation


_TASK_TO_ENV_ID = {
    "PickCube": "PickCube-v1",
    "StackCube": "StackCube-v1",
    "PickSingleYCB": "PickSingleYCB-v1",
    "PickClutterYCB": "PickClutterYCB-v1",
}


@dataclass(frozen=True)
class _ObjectSpec:
    actor_name: str
    label: str
    half_size: np.ndarray | None


def _to_numpy(value: Any) -> np.ndarray:
    if hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    return np.asarray(value)


def _first_batch(value: Any) -> np.ndarray:
    arr = _to_numpy(value)
    if arr.ndim > 0 and arr.shape[0] == 1:
        return arr[0]
    return arr


def _info_success(info: Any) -> bool | None:
    if not isinstance(info, dict) or "success" not in info:
        return None
    value = info["success"]
    arr = _to_numpy(value)
    if arr.size == 0:
        return None
    return bool(np.asarray(arr).reshape(-1)[0])


def _as_4x4(matrix: np.ndarray) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=float)
    if matrix.shape == (4, 4):
        return matrix
    if matrix.shape == (3, 4):
        out = np.eye(4, dtype=float)
        out[:3, :4] = matrix
        return out
    raise ValueError(f"Expected camera matrix with shape (3, 4) or (4, 4), got {matrix.shape}")


def _depth_to_meters(depth: np.ndarray) -> np.ndarray:
    depth = np.asarray(depth)
    if depth.ndim == 3 and depth.shape[-1] == 1:
        depth = depth[..., 0]
    depth = depth.astype(np.float32, copy=False)
    if depth.size and float(np.nanmax(depth)) > 20.0:
        depth = depth / 1000.0
    return depth


def _project_points(points_world: np.ndarray, world_to_camera_cv: np.ndarray, intrinsics: np.ndarray) -> np.ndarray:
    points_h = np.concatenate([points_world, np.ones((len(points_world), 1), dtype=float)], axis=1)
    camera = (world_to_camera_cv @ points_h.T).T[:, :3]
    valid = camera[:, 2] > 1e-6
    if not np.any(valid):
        return np.empty((0, 2), dtype=float)
    camera = camera[valid]
    pixels = (intrinsics @ camera.T).T
    pixels = pixels[:, :2] / pixels[:, 2:3]
    return pixels


def _bbox_from_projection(
    center: np.ndarray,
    half_size: np.ndarray | None,
    world_to_camera_cv: np.ndarray,
    intrinsics: np.ndarray,
    image_shape: Tuple[int, int],
) -> list[int]:
    h, w = image_shape
    if half_size is None:
        half_size = np.array([0.03, 0.03, 0.03], dtype=float)
    offsets = np.array(
        [
            [sx, sy, sz]
            for sx in (-half_size[0], half_size[0])
            for sy in (-half_size[1], half_size[1])
            for sz in (-half_size[2], half_size[2])
        ],
        dtype=float,
    )
    pixels = _project_points(center[None, :] + offsets, world_to_camera_cv, intrinsics)
    if len(pixels) == 0:
        pixels = _project_points(center[None, :], world_to_camera_cv, intrinsics)
    if len(pixels) == 0:
        return [0, 0, w, h]

    pad = 4.0
    x1 = int(np.floor(np.nanmin(pixels[:, 0]) - pad))
    y1 = int(np.floor(np.nanmin(pixels[:, 1]) - pad))
    x2 = int(np.ceil(np.nanmax(pixels[:, 0]) + pad))
    y2 = int(np.ceil(np.nanmax(pixels[:, 1]) + pad))
    x1 = int(np.clip(x1, 0, max(0, w - 1)))
    y1 = int(np.clip(y1, 0, max(0, h - 1)))
    x2 = int(np.clip(x2, x1 + 1, w))
    y2 = int(np.clip(y2, y1 + 1, h))
    return [x1, y1, x2, y2]


class ManiSkillManipulationEnv:
    """ManiSkill RGB-D adapter for target-source diagnostics.

    The adapter intentionally evaluates whether a predicted 3D target lands on
    the object of interest. It does not claim to execute a learned manipulation
    policy; policy rollouts can be layered on after target generation is stable.
    """

    def __init__(
        self,
        task: str,
        seed: int = 0,
        obs_mode: str = "rgbd",
        control_mode: str = "pd_ee_delta_pos",
        render_mode: str = "rgb_array",
        success_threshold: float = 0.08,
    ):
        try:
            import gymnasium as gym
            import mani_skill.envs  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "ManiSkill backend requires gymnasium and mani_skill. "
                "Install the H200 q2g environment or run with backend='mock'."
            ) from e

        if task not in _TASK_TO_ENV_ID:
            raise ValueError(f"Unsupported ManiSkill task: {task}. Available: {sorted(_TASK_TO_ENV_ID)}")

        self.task = task
        self.seed = seed
        self.success_threshold = float(success_threshold)
        self.env_id = _TASK_TO_ENV_ID[task]
        self.env = gym.make(
            self.env_id,
            obs_mode=obs_mode,
            control_mode=control_mode,
            render_mode=render_mode,
        )
        self._last_target: np.ndarray | None = None

    def close(self) -> None:
        self.env.close()

    def reset(self) -> Observation:
        reset_out = self.env.reset(seed=self.seed)
        raw_obs = reset_out[0] if isinstance(reset_out, tuple) else reset_out

        camera_name = next(iter(raw_obs["sensor_data"]))
        sensor_data = raw_obs["sensor_data"][camera_name]
        sensor_param = raw_obs["sensor_param"][camera_name]
        rgb = _first_batch(sensor_data["rgb"]).astype(np.uint8, copy=False)
        depth = _depth_to_meters(_first_batch(sensor_data["depth"]))
        intrinsics = _first_batch(sensor_param["intrinsic_cv"]).astype(float, copy=False)
        world_to_camera_cv = _as_4x4(_first_batch(sensor_param["extrinsic_cv"]))
        camera_to_world_cv = np.linalg.inv(world_to_camera_cv)

        spec = self._object_spec()
        actor = getattr(self.env.unwrapped, spec.actor_name)
        target = _first_batch(actor.pose.p).astype(float, copy=False)
        self._last_target = target
        bbox = _bbox_from_projection(target, spec.half_size, world_to_camera_cv, intrinsics, depth.shape[:2])

        target_name_debug = self._target_name_debug(actor)
        label, label_source = self._actor_label(actor, spec.label, target_name_debug)
        category = self._target_category(label)
        detection = {
            "label": label,
            "score": 1.0,
            "bbox_xyxy": bbox,
            "source": "maniskill_oracle_projection",
            "is_target": True,
            "distractor_type": None,
            "query_aliases": self._query_aliases(label),
        }
        metadata: Dict[str, Any] = {
            "oracle_target_3d": target.tolist(),
            "task": self.task,
            "env_id": self.env_id,
            "target_actor": spec.actor_name,
            "target_label": label,
            "target_label_source": label_source,
            "target_category": category,
            "target_bbox_xyxy": bbox,
            "target_name_debug": target_name_debug,
        }
        return Observation(
            rgb=rgb,
            depth=depth,
            intrinsics=intrinsics,
            extrinsics=camera_to_world_cv,
            detections=[detection],
            object_metadata=metadata,
            debug_info={
                "backend": "maniskill",
                "camera_name": camera_name,
                "depth_units": "meters",
                "diagnostic_execution": True,
            },
        )

    def execute_pick(self, target_3d: np.ndarray | None, execution_offset: np.ndarray | None = None) -> ExecutionResult:
        if target_3d is None:
            return ExecutionResult(False, "no_target", {"diagnostic_execution": True})
        if self._last_target is None:
            return ExecutionResult(False, "environment_not_reset", {"diagnostic_execution": True})
        target = np.asarray(target_3d, dtype=float)
        if execution_offset is not None:
            target = target + np.asarray(execution_offset, dtype=float)
        error = float(np.linalg.norm(target - self._last_target))
        success = error <= self.success_threshold
        return ExecutionResult(
            success=success,
            failure_type=None if success else "target_error_too_large",
            debug_info={
                "target_error_l2": error,
                "success_threshold": self.success_threshold,
                "diagnostic_execution": True,
                "note": "ManiSkill adapter evaluates target-source accuracy, not closed-loop control.",
            },
        )

    def _tcp_position(self) -> np.ndarray | None:
        agent = getattr(self.env.unwrapped, "agent", None)
        tcp = getattr(agent, "tcp", None)
        pose = getattr(tcp, "pose", None)
        if pose is None or not hasattr(pose, "p"):
            return None
        return _first_batch(pose.p).astype(float, copy=False)

    def _delta_action(self, waypoint: np.ndarray, gripper: float) -> np.ndarray | None:
        tcp = self._tcp_position()
        if tcp is None:
            return None
        action = np.zeros(self.env.action_space.shape, dtype=np.float32)
        flat = action.reshape(-1)
        delta = np.clip(waypoint - tcp, -0.035, 0.035)
        flat[: min(3, len(flat))] = delta[: min(3, len(flat))]
        if len(flat) >= 4:
            flat[-1] = float(gripper)
        return action

    def execute_scripted_task(self, target_3d: np.ndarray | None, execution_offset: np.ndarray | None = None) -> ExecutionResult:
        """Best-effort scripted sanity executor for linking target quality to task success.

        This is intentionally simple and is not used as a policy benchmark. The
        runner records failures explicitly when the ManiSkill control interface
        does not expose the expected TCP/action semantics.
        """
        if target_3d is None:
            return ExecutionResult(False, "no_target", {"scripted_executor": "maniskill_delta_pick"})
        target = np.asarray(target_3d, dtype=float)
        if execution_offset is not None:
            target = target + np.asarray(execution_offset, dtype=float)
        if self._tcp_position() is None:
            return ExecutionResult(
                False,
                "scripted_executor_unsupported",
                {"scripted_executor": "maniskill_delta_pick", "reason": "tcp_position_unavailable"},
            )

        waypoints = [
            (target + np.array([0.0, 0.0, 0.12]), 1.0, 16),
            (target + np.array([0.0, 0.0, 0.02]), 1.0, 16),
            (target + np.array([0.0, 0.0, 0.02]), -1.0, 10),
            (target + np.array([0.0, 0.0, 0.18]), -1.0, 24),
        ]
        saw_success = False
        last_info: Dict[str, Any] = {}
        steps = 0
        try:
            for waypoint, gripper, repeat in waypoints:
                for _ in range(repeat):
                    action = self._delta_action(waypoint, gripper)
                    if action is None:
                        return ExecutionResult(
                            False,
                            "scripted_executor_unsupported",
                            {"scripted_executor": "maniskill_delta_pick", "reason": "action_unavailable"},
                        )
                    step_out = self.env.step(action)
                    if len(step_out) == 5:
                        _, _, terminated, truncated, info = step_out
                    else:
                        _, _, done, info = step_out
                        terminated, truncated = done, False
                    last_info = dict(info) if isinstance(info, dict) else {}
                    success = _info_success(last_info)
                    saw_success = saw_success or bool(success)
                    steps += 1
                    if terminated or truncated:
                        break
                if saw_success:
                    break
        except Exception as exc:  # pragma: no cover - depends on ManiSkill runtime
            return ExecutionResult(
                False,
                "scripted_executor_exception",
                {
                    "scripted_executor": "maniskill_delta_pick",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "steps": steps,
                },
            )

        return ExecutionResult(
            saw_success,
            None if saw_success else "scripted_task_failed",
            {
                "scripted_executor": "maniskill_delta_pick",
                "closed_loop_task_success": saw_success,
                "steps": steps,
                "last_info_keys": sorted(last_info.keys()),
            },
        )

    def _object_spec(self) -> _ObjectSpec:
        if self.task == "StackCube":
            return _ObjectSpec("cubeA", "red cube", self._cube_half_size())
        if self.task == "PickCube":
            return _ObjectSpec("cube", "red cube", self._cube_half_size())
        if self.task == "PickClutterYCB":
            return _ObjectSpec("target_object", "target object", None)
        return _ObjectSpec("obj", "target object", None)

    def _cube_half_size(self) -> np.ndarray | None:
        value = getattr(self.env.unwrapped, "cube_half_size", None)
        if value is None:
            return None
        arr = _to_numpy(value).astype(float, copy=False)
        if arr.ndim == 0:
            return np.repeat(arr, 3)
        return np.broadcast_to(arr.reshape(-1)[:3], (3,)).astype(float, copy=False)

    def _target_name_debug(self, actor: Any) -> dict[str, Any]:
        debug: dict[str, Any] = {}
        simple_attrs = [
            "name",
            "_name",
            "model_id",
            "_model_id",
            "model_name",
            "asset_id",
            "asset_name",
            "model_uid",
            "uid",
        ]
        for prefix, obj in [("actor", actor), ("env", self.env.unwrapped)]:
            for attr in simple_attrs:
                if hasattr(obj, attr):
                    value = getattr(obj, attr)
                    if isinstance(value, (str, int, float, bool)):
                        debug[f"{prefix}.{attr}"] = value
        for attr in dir(self.env.unwrapped):
            lower = attr.lower()
            if not any(token in lower for token in ["target", "model", "asset", "ycb"]):
                continue
            if attr.startswith("__"):
                continue
            try:
                value = getattr(self.env.unwrapped, attr)
            except Exception:
                continue
            if isinstance(value, (str, int, float, bool)):
                debug[f"env_scan.{attr}"] = value
            elif isinstance(value, (list, tuple)) and all(isinstance(v, (str, int, float, bool)) for v in value[:8]):
                debug[f"env_scan.{attr}"] = list(value[:8])
            elif isinstance(value, dict):
                simple = {
                    str(k): v
                    for k, v in list(value.items())[:8]
                    if isinstance(v, (str, int, float, bool))
                }
                if simple:
                    debug[f"env_scan.{attr}"] = simple
        return debug

    def _normalize_label_candidate(self, value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        label = value.replace("ycb_", "").replace("_", " ").replace("-", " ").strip().lower()
        generic = {"", "obj", "object", "target object", "target", "target object clone", "actor", "ycb object"}
        if label in generic:
            return None
        if label.isdigit():
            return None
        return label

    def _actor_label(self, actor: Any, fallback: str, debug: dict[str, Any]) -> tuple[str, str]:
        for key in [
            "actor.name",
            "actor._name",
            "actor.model_id",
            "actor._model_id",
            "actor.model_name",
            "actor.asset_id",
            "actor.asset_name",
            "env.target_model_id",
            "env.model_id",
            "env.asset_id",
        ]:
            label = self._normalize_label_candidate(debug.get(key))
            if label:
                return label, key
        for key, value in debug.items():
            label = self._normalize_label_candidate(value)
            if label:
                return label, key
        return fallback, "fallback"

    def _target_category(self, label: str) -> str:
        if self.task in {"PickCube", "StackCube"}:
            return "cube"
        if label and label != "target object":
            return label.split()[-1]
        return "object"

    def _query_aliases(self, label: str) -> list[str]:
        aliases = [label, "target object", "requested object", "object", self._target_category(label)]
        if self.task in {"PickCube", "StackCube"}:
            aliases.extend(["red cube", "cube"])
        return aliases
