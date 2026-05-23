from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from embodied_stressbench.envs.task_registry import make_env


YCB_OBJECT_NAMES = {
    "002": "master chef can",
    "003": "cracker box",
    "004": "sugar box",
    "005": "tomato soup can",
    "006": "mustard bottle",
    "007": "tuna fish can",
    "008": "pudding box",
    "009": "gelatin box",
    "010": "potted meat can",
    "011": "banana",
    "012": "strawberry",
    "013": "apple",
    "014": "lemon",
    "015": "peach",
    "016": "pear",
    "017": "orange",
    "018": "plum",
    "019": "pitcher base",
    "021": "bleach cleanser",
    "024": "bowl",
    "025": "mug",
    "026": "sponge",
    "029": "plate",
    "030": "fork",
    "031": "spoon",
    "032": "knife",
    "033": "spatula",
    "035": "power drill",
    "036": "wood block",
    "037": "scissors",
    "040": "large marker",
    "042": "adjustable wrench",
    "043": "phillips screwdriver",
    "044": "flat screwdriver",
    "048": "hammer",
    "049": "small clamp",
    "050": "medium clamp",
    "051": "large clamp",
    "052": "extra large clamp",
    "053": "mini soccer ball",
    "054": "softball",
    "055": "baseball",
    "056": "tennis ball",
    "057": "racquetball",
    "058": "golf ball",
    "059": "chain",
    "061": "foam brick",
    "063": "marbles",
    "065": "cups",
    "072": "toy airplane",
    "073": "lego duplo",
    "077": "rubiks cube",
}
GENERIC_LABELS = {
    "",
    "none",
    "object",
    "target object",
    "requested object",
    "thing",
    "item",
    "target",
    "ycb object",
    "ycb_object",
}
TRUSTED_DEBUG_PREFIXES = (
    "env._objs[0]",
    "env.selectable_target_objects.matched",
    "env.obj",
    "env.target_object",
    "actor.",
)


def _normal(value: Any) -> str:
    return str(value or "").strip().lower().replace("_", " ").replace("-", " ")


def _is_generic(value: Any) -> bool:
    return _normal(value) in GENERIC_LABELS


def _resolve_ycb_name(value: Any) -> tuple[str | None, str | None]:
    text = str(value or "").strip().lower()
    if not text:
        return None, None
    text_space = text.replace("_", " ").replace("-", " ")
    for model_id, name in YCB_OBJECT_NAMES.items():
        if re.search(rf"(^|[^0-9]){re.escape(model_id)}([^0-9]|$)", text):
            return name, model_id
        if name in text_space or name.replace(" ", "_") in text:
            return name, model_id
    return None, None


def _safe_repr(value: Any, max_len: int = 320) -> str:
    try:
        text = repr(value)
    except Exception as exc:
        text = f"<repr_error {type(exc).__name__}: {exc}>"
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def _summarize_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_summarize_value(v) for v in list(value)[:12]]
    if isinstance(value, dict):
        return {str(k): _summarize_value(v) for k, v in list(value.items())[:12]}
    if hasattr(value, "__dict__"):
        simple = {}
        for key, item in list(vars(value).items())[:20]:
            if key.startswith("__"):
                continue
            if isinstance(item, (str, int, float, bool)) or item is None:
                simple[key] = item
            else:
                simple[key] = _safe_repr(item)
        return simple or _safe_repr(value)
    return _safe_repr(value)


def _scan_object(obj: Any, prefix: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    tokens = ("target", "model", "asset", "ycb", "obj", "object", "id", "uid", "name")
    for attr in dir(obj):
        if attr.startswith("__"):
            continue
        lower = attr.lower()
        if not any(token in lower for token in tokens):
            continue
        try:
            value = getattr(obj, attr)
        except Exception:
            continue
        if callable(value):
            continue
        out[f"{prefix}.{attr}"] = _summarize_value(value)
    return out


def _candidate_strings(payload: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(payload, str):
        strings.append(payload)
    elif isinstance(payload, dict):
        for key, value in payload.items():
            strings.append(str(key))
            strings.extend(_candidate_strings(value))
    elif isinstance(payload, (list, tuple)):
        for value in payload:
            strings.extend(_candidate_strings(value))
    elif payload is not None:
        strings.append(str(payload))
    return strings


def _trusted_candidate_strings(payload: dict[str, Any]) -> list[tuple[str, str]]:
    strings: list[tuple[str, str]] = []
    metadata = payload.get("object_metadata", {})
    target_label = metadata.get("target_label")
    if target_label is not None and not _is_generic(target_label):
        strings.append(("object_metadata.target_label", str(target_label)))
    debug = metadata.get("target_name_debug", {})
    if isinstance(debug, dict):
        for source, value in debug.items():
            if not str(source).startswith(TRUSTED_DEBUG_PREFIXES):
                continue
            for candidate in _candidate_strings(value):
                if not _is_generic(candidate):
                    strings.append((f"target_name_debug.{source}", candidate))
    return strings


def _probe_task_seed(task: str, seed: int) -> dict[str, Any]:
    env = make_env(task=task, backend="maniskill", seed=seed)
    try:
        obs = env.reset()
        unwrapped = getattr(env, "env", env)
        unwrapped = getattr(unwrapped, "unwrapped", unwrapped)
        target_actor_name = obs.object_metadata.get("target_actor")
        actor = getattr(unwrapped, str(target_actor_name), None) if target_actor_name else None
        payload = {
            "object_metadata": obs.object_metadata,
            "env_scan": _scan_object(unwrapped, "env"),
            "actor_scan": _scan_object(actor, "actor") if actor is not None else {},
        }
    finally:
        close = getattr(env, "close", None)
        if callable(close):
            close()

    target_label = obs.object_metadata.get("target_label")
    resolved_name = None
    resolved_id = None
    resolved_source = None
    for source, value in _trusted_candidate_strings(payload):
        name, model_id = _resolve_ycb_name(value)
        if name:
            resolved_name = name
            resolved_id = model_id
            resolved_source = f"{source}: {value}"
            break
    return {
        "task": task,
        "seed": int(seed),
        "target_label": target_label,
        "target_label_is_generic": _is_generic(target_label),
        "target_category": obs.object_metadata.get("target_category"),
        "resolved_object_name": resolved_name or "",
        "resolved_model_id": resolved_id or "",
        "resolved_source": resolved_source or "",
        "resolved_name_available": bool(resolved_name),
        "payload_json": json.dumps(payload, sort_keys=True, default=str),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", nargs="+", default=["PickSingleYCB", "PickClutterYCB"])
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(20)))
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for task in args.tasks:
        for seed in args.seeds:
            try:
                rows.append(_probe_task_seed(task, seed))
            except Exception as exc:
                rows.append(
                    {
                        "task": task,
                        "seed": int(seed),
                        "status": "error",
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    }
                )
    df = pd.DataFrame(rows)
    for column, default in [
        ("status", "ok"),
        ("target_label_is_generic", True),
        ("resolved_name_available", False),
        ("resolved_object_name", ""),
    ]:
        if column not in df:
            df[column] = default
        else:
            df[column] = df[column].fillna(default)
    df.to_csv(out / "target_identity_deep_probe.csv", index=False)
    summary = (
        df.groupby("task", dropna=False)
        .agg(
            probe_rows=("seed", "size"),
            errors=("status", lambda s: int((s == "error").sum()) if len(s) else 0),
            non_generic_target_label_rows=("target_label_is_generic", lambda s: int((s == False).sum())),  # noqa: E712
            resolved_object_name_rows=("resolved_name_available", lambda s: int(s.fillna(False).astype(bool).sum())),
            unique_resolved_names=("resolved_object_name", lambda s: ", ".join(sorted({str(x) for x in s if str(x)})) or "none"),
        )
        .reset_index()
    )
    total_resolved = int(summary["resolved_object_name_rows"].sum()) if len(summary) else 0
    all_tasks_resolved = bool(len(summary) and (summary["resolved_object_name_rows"] > 0).all())
    summary["true_name_ablation_allowed"] = all_tasks_resolved
    summary.to_csv(out / "target_identity_deep_probe_summary.csv", index=False)
    lines = [
        "# ManiSkill YCB Deep Target-Identity Probe",
        "",
        f"- Rows: {len(df)}",
        f"- Errors: {int((df.get('status') == 'error').sum()) if 'status' in df else 0}",
        f"- Resolved object-name rows: {total_resolved}",
        f"- True-name ablation allowed: {all_tasks_resolved}",
        "",
        "A true-name prompt ablation is allowed only when every requested task has at least one trusted target-specific object-name recovery.",
    ]
    (out / "target_identity_deep_probe_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote deep target-identity probe to {out}")


if __name__ == "__main__":
    main()
