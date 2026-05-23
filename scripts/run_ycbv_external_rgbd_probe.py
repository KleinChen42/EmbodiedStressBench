from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from PIL import Image

from embodied_stressbench.detectors.grounding_dino import GroundingDinoProvider
from embodied_stressbench.perception.depth_lifting import backproject_pixel
from embodied_stressbench.types import Observation


YCBV_OBJECT_NAMES = {
    1: "master chef can",
    2: "cracker box",
    3: "sugar box",
    4: "tomato soup can",
    5: "mustard bottle",
    6: "tuna fish can",
    7: "pudding box",
    8: "gelatin box",
    9: "potted meat can",
    10: "banana",
    11: "pitcher base",
    12: "bleach cleanser",
    13: "bowl",
    14: "mug",
    15: "power drill",
    16: "wood block",
    17: "scissors",
    18: "large marker",
    19: "large clamp",
    20: "extra large clamp",
    21: "foam brick",
}


THRESHOLDS_M = (0.04, 0.06, 0.08, 0.10)


@dataclass(frozen=True)
class TargetItem:
    scene_id: int
    image_id: int
    gt_index: int
    obj_id: int
    object_name: str
    bbox_xywh: tuple[int, int, int, int]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _bbox_xywh_to_xyxy(bbox: Iterable[Any]) -> list[float]:
    x, y, w, h = [float(v) for v in bbox]
    return [x, y, x + max(0.0, w), y + max(0.0, h)]


def _clip_bbox(bbox: list[float], width: int, height: int) -> tuple[int, int, int, int] | None:
    x1, y1, x2, y2 = [int(round(v)) for v in bbox]
    x1 = max(0, min(width, x1))
    x2 = max(0, min(width, x2))
    y1 = max(0, min(height, y1))
    y2 = max(0, min(height, y2))
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def _iou_xyxy(a: list[float] | None, b: list[float] | None) -> float:
    if a is None or b is None:
        return 0.0
    ax1, ay1, ax2, ay2 = [float(v) for v in a]
    bx1, by1, bx2, by2 = [float(v) for v in b]
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return 0.0 if union <= 0 else float(inter / union)


def _read_rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)


def _read_depth_m(path: Path, depth_scale: float) -> np.ndarray:
    raw = np.asarray(Image.open(path), dtype=np.float32)
    return raw * float(depth_scale) / 1000.0


def _read_mask(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path), dtype=np.uint8) > 0


def _mask_median_target(depth_m: np.ndarray, mask: np.ndarray, intrinsics: np.ndarray) -> tuple[np.ndarray | None, dict[str, Any]]:
    ys, xs = np.where(mask & np.isfinite(depth_m) & (depth_m > 0))
    if len(xs) == 0:
        return None, {"num_valid_mask_depth": 0}
    values = depth_m[ys, xs]
    order = np.argsort(values)
    idx = int(order[len(order) // 2])
    u = float(xs[idx])
    v = float(ys[idx])
    d = float(values[idx])
    return backproject_pixel(u, v, d, intrinsics), {
        "pixel": [u, v],
        "depth": d,
        "num_valid_mask_depth": int(len(xs)),
    }


def _lift_from_bbox(
    depth_m: np.ndarray,
    bbox: list[float] | None,
    intrinsics: np.ndarray,
    target_source: str,
) -> tuple[np.ndarray | None, dict[str, Any], str | None]:
    if bbox is None:
        return None, {}, "no_detection"
    h, w = depth_m.shape[:2]
    clipped = _clip_bbox(bbox, w, h)
    if clipped is None:
        return None, {"bbox": bbox}, "invalid_bbox"
    x1, y1, x2, y2 = clipped
    crop = depth_m[y1:y2, x1:x2]
    yy, xx = np.mgrid[y1:y2, x1:x2]
    mask = np.isfinite(crop) & (crop > 0)

    if target_source == "box_center_depth":
        u = int(round((x1 + x2) / 2))
        v = int(round((y1 + y2) / 2))
        if v < 0 or v >= h or u < 0 or u >= w:
            return None, {"bbox": list(clipped), "pixel": [u, v]}, "invalid_projection"
        d = float(depth_m[v, u])
        if not np.isfinite(d) or d <= 0:
            return None, {"bbox": list(clipped), "pixel": [u, v], "depth": d}, "depth_invalid"
        return backproject_pixel(float(u), float(v), d, intrinsics), {
            "bbox": list(clipped),
            "pixel": [float(u), float(v)],
            "depth": d,
        }, None

    depths = crop[mask]
    xs = xx[mask]
    ys = yy[mask]
    if len(depths) == 0:
        return None, {"bbox": list(clipped), "num_valid": 0}, "no_valid_depth_in_crop"

    if target_source == "crop_trimmed_median_depth" and len(depths) >= 10:
        lo, hi = np.quantile(depths, [0.10, 0.90])
        keep = (depths >= lo) & (depths <= hi)
        if np.any(keep):
            depths, xs, ys = depths[keep], xs[keep], ys[keep]

    if target_source not in {"crop_median_depth", "crop_trimmed_median_depth"}:
        return None, {"bbox": list(clipped)}, f"unknown_target_source:{target_source}"

    order = np.argsort(depths)
    idx = int(order[len(order) // 2])
    u = float(xs[idx])
    v = float(ys[idx])
    d = float(depths[idx])
    return backproject_pixel(u, v, d, intrinsics), {
        "bbox": list(clipped),
        "pixel": [u, v],
        "depth": d,
        "num_valid": int(len(depths)),
    }, None


def _record(
    *,
    item: TargetItem,
    detector: str,
    target_source: str,
    query_variant: str,
    query: str,
    pred: np.ndarray | None,
    ref: np.ndarray | None,
    failure_reason: str | None,
    bbox: list[float] | None,
    target_bbox: list[float],
    debug: dict[str, Any],
) -> dict[str, Any]:
    if pred is None or ref is None:
        target_error = math.nan
        success_008 = False
    else:
        target_error = float(np.linalg.norm(np.asarray(pred, dtype=float) - np.asarray(ref, dtype=float)))
        success_008 = bool(target_error <= 0.08)

    bbox_iou = _iou_xyxy(bbox, target_bbox)
    if failure_reason is not None:
        failure_type = failure_reason
    elif bbox is not None and bbox_iou < 0.25 and not success_008 and detector not in {"oracle_2d_box", "oracle_mask"}:
        failure_type = "wrong_detection_selected"
    elif success_008:
        failure_type = "success"
    else:
        failure_type = "target_error_too_large"

    row: dict[str, Any] = {
        "dataset": "ycbv_bop",
        "scene_id": item.scene_id,
        "image_id": item.image_id,
        "gt_index": item.gt_index,
        "obj_id": item.obj_id,
        "object_name": item.object_name,
        "detector": detector,
        "target_source": target_source,
        "baseline": f"{target_source}_{detector}",
        "query_variant": query_variant,
        "query_used": query,
        "success": success_008,
        "failure_type": failure_type,
        "target_error_l2": None if math.isnan(target_error) else target_error,
        "bbox_iou": bbox_iou,
        "bbox_xyxy": bbox,
        "target_bbox_xyxy": target_bbox,
        "reference_target_3d": None if ref is None else [float(v) for v in ref],
        "predicted_target_3d": None if pred is None else [float(v) for v in pred],
    }
    for threshold in THRESHOLDS_M:
        key = f"success_at_{int(threshold * 100):02d}cm"
        row[key] = bool(not math.isnan(target_error) and target_error <= threshold)
    row["debug"] = debug
    return row


def _build_items(data_root: Path, frame_stride: int, max_targets: int | None) -> list[TargetItem]:
    items: list[TargetItem] = []
    for scene_dir in sorted((data_root / "test").iterdir()):
        if not scene_dir.is_dir() or not scene_dir.name.isdigit():
            continue
        scene_id = int(scene_dir.name)
        gt = _load_json(scene_dir / "scene_gt.json")
        info = _load_json(scene_dir / "scene_gt_info.json")
        image_ids = sorted(int(k) for k in gt.keys())
        for pos, image_id in enumerate(image_ids):
            if frame_stride > 1 and pos % frame_stride != 0:
                continue
            image_key = str(image_id)
            for gt_index, obj in enumerate(gt[image_key]):
                gt_info = info.get(image_key, [{}])[gt_index]
                bbox_xywh = gt_info.get("bbox_visib") or gt_info.get("bbox_obj")
                if not bbox_xywh:
                    continue
                w = int(round(float(bbox_xywh[2])))
                h = int(round(float(bbox_xywh[3])))
                if w <= 1 or h <= 1:
                    continue
                obj_id = int(obj.get("obj_id"))
                items.append(
                    TargetItem(
                        scene_id=scene_id,
                        image_id=image_id,
                        gt_index=gt_index,
                        obj_id=obj_id,
                        object_name=YCBV_OBJECT_NAMES.get(obj_id, f"ycbv object {obj_id}"),
                        bbox_xywh=tuple(int(round(float(v))) for v in bbox_xywh),
                    )
                )
                if max_targets is not None and len(items) >= max_targets:
                    return items
    return items


def _query_for(variant: str, object_name: str) -> str:
    if variant == "generic":
        return "target object"
    if variant == "true_name":
        return object_name
    if variant == "photo_true_name":
        return f"a photo of {object_name}"
    raise ValueError(f"Unknown query variant: {variant}")


def _load_frame(data_root: Path, item: TargetItem) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    scene = data_root / "test" / f"{item.scene_id:06d}"
    camera = _load_json(scene / "scene_camera.json")[str(item.image_id)]
    intrinsics = np.asarray(camera["cam_K"], dtype=float).reshape(3, 3)
    depth_scale = float(camera.get("depth_scale", 1.0))
    rgb = _read_rgb(scene / "rgb" / f"{item.image_id:06d}.png")
    depth = _read_depth_m(scene / "depth" / f"{item.image_id:06d}.png", depth_scale)
    mask_path = scene / "mask_visib" / f"{item.image_id:06d}_{item.gt_index:06d}.png"
    if not mask_path.exists():
        mask_path = scene / "mask" / f"{item.image_id:06d}_{item.gt_index:06d}.png"
    mask = _read_mask(mask_path)
    return rgb, depth, mask, intrinsics, {"depth_scale": depth_scale, "mask_path": str(mask_path)}


def _all_gt_detections(data_root: Path, item: TargetItem) -> list[dict[str, Any]]:
    scene = data_root / "test" / f"{item.scene_id:06d}"
    gt = _load_json(scene / "scene_gt.json")[str(item.image_id)]
    info = _load_json(scene / "scene_gt_info.json")[str(item.image_id)]
    detections: list[dict[str, Any]] = []
    for idx, obj in enumerate(gt):
        bbox_xywh = info[idx].get("bbox_visib") or info[idx].get("bbox_obj")
        if not bbox_xywh:
            continue
        obj_id = int(obj.get("obj_id"))
        detections.append(
            {
                "bbox_xyxy": _bbox_xywh_to_xyxy(bbox_xywh),
                "label": YCBV_OBJECT_NAMES.get(obj_id, f"ycbv object {obj_id}"),
                "score": 1.0,
                "is_target": idx == item.gt_index,
                "source": "gt_box_list",
            }
        )
    return detections


def _get_grounding_dino() -> GroundingDinoProvider | None:
    try:
        return GroundingDinoProvider()
    except Exception as exc:
        print(f"[ycbv-probe] GroundingDINO unavailable: {type(exc).__name__}: {exc}", flush=True)
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-targets", type=int, default=6000)
    parser.add_argument("--frame-stride", type=int, default=10)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--query-variants", nargs="+", default=["generic", "true_name", "photo_true_name"])
    parser.add_argument("--include-grounding-dino", action="store_true")
    parser.add_argument("--flush-every", type=int, default=20)
    args = parser.parse_args()

    data_root = Path(args.data_root)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    records_path = output / "records.jsonl"
    summary_path = output / "summary.json"

    items = _build_items(data_root, max(1, args.frame_stride), args.max_targets)
    shard_items = [item for i, item in enumerate(items) if i % args.num_shards == args.shard_index]
    print(
        f"[ycbv-probe] shard={args.shard_index}/{args.num_shards} "
        f"targets={len(shard_items)} total_selected={len(items)}",
        flush=True,
    )

    detector = _get_grounding_dino() if args.include_grounding_dino else None
    written = 0
    failed_frames = 0
    with records_path.open("w", encoding="utf-8") as handle:
        for item_idx, item in enumerate(shard_items):
            try:
                rgb, depth, mask, intrinsics, frame_debug = _load_frame(data_root, item)
                ref, ref_debug = _mask_median_target(depth, mask, intrinsics)
                target_bbox = _bbox_xywh_to_xyxy(item.bbox_xywh)
                gt_dets = _all_gt_detections(data_root, item)
                first_bbox = gt_dets[0]["bbox_xyxy"] if gt_dets else None
            except Exception as exc:
                failed_frames += 1
                handle.write(
                    json.dumps(
                        {
                            "dataset": "ycbv_bop",
                            "scene_id": item.scene_id,
                            "image_id": item.image_id,
                            "gt_index": item.gt_index,
                            "obj_id": item.obj_id,
                            "object_name": item.object_name,
                            "detector": "frame_loader",
                            "target_source": "none",
                            "success": False,
                            "failure_type": "frame_load_error",
                            "error_message": f"{type(exc).__name__}: {exc}",
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )
                continue

            bbox_sources: list[tuple[str, str, str, list[float] | None, dict[str, Any]]] = [
                ("oracle_2d_box", "oracle", "", target_bbox, {"bbox_source": "gt_visible_bbox"}),
                ("first_gt_box", "oracle", "", first_bbox, {"bbox_source": "first_gt_visible_bbox"}),
            ]

            if detector is not None:
                observation = Observation(
                    rgb=rgb,
                    depth=depth,
                    intrinsics=intrinsics,
                    extrinsics=None,
                    detections=gt_dets,
                    object_metadata={"target_bbox_xyxy": target_bbox, "target_label": item.object_name},
                )
                for variant in args.query_variants:
                    query = _query_for(variant, item.object_name)
                    try:
                        result = detector.detect(observation, query)
                        if result.detections:
                            det = result.detections[0]
                            bbox = [float(v) for v in det.get("bbox_xyxy", [])]
                            debug = {
                                "bbox_source": "grounding_dino",
                                "grounding_dino_score": det.get("score"),
                                "grounding_dino_target_iou": det.get("target_iou"),
                                **result.debug_info,
                            }
                        else:
                            bbox = None
                            debug = {"bbox_source": "grounding_dino", **result.debug_info}
                    except Exception as exc:
                        bbox = None
                        debug = {
                            "bbox_source": "grounding_dino",
                            "selection_failure_reason": "grounding_dino_exception",
                            "error_message": f"{type(exc).__name__}: {exc}",
                        }
                    bbox_sources.append(("grounding_dino", variant, query, bbox, debug))

            for det_name, query_variant, query, bbox, det_debug in bbox_sources:
                for source in ["box_center_depth", "crop_median_depth", "crop_trimmed_median_depth"]:
                    pred, lift_debug, failure = _lift_from_bbox(depth, bbox, intrinsics, source)
                    row = _record(
                        item=item,
                        detector=det_name,
                        target_source=source,
                        query_variant=query_variant,
                        query=query,
                        pred=pred,
                        ref=ref,
                        failure_reason=failure,
                        bbox=bbox,
                        target_bbox=target_bbox,
                        debug={**frame_debug, **ref_debug, **det_debug, **lift_debug},
                    )
                    handle.write(json.dumps(row, sort_keys=True) + "\n")
                    written += 1

            pred, mask_debug = ref, {**frame_debug, **ref_debug, "bbox_source": "oracle_mask"}
            row = _record(
                item=item,
                detector="oracle_mask",
                target_source="mask_median_depth",
                query_variant="oracle",
                query="",
                pred=pred,
                ref=ref,
                failure_reason=None if pred is not None else "no_valid_depth_in_mask",
                bbox=target_bbox,
                target_bbox=target_bbox,
                debug=mask_debug,
            )
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            written += 1

            if args.flush_every and (item_idx + 1) % args.flush_every == 0:
                handle.flush()
                print(
                    f"[ycbv-probe] shard={args.shard_index} "
                    f"targets_done={item_idx + 1}/{len(shard_items)} records={written}",
                    flush=True,
                )

    summary = {
        "data_root": str(data_root),
        "output": str(output),
        "shard_index": args.shard_index,
        "num_shards": args.num_shards,
        "max_targets": args.max_targets,
        "frame_stride": args.frame_stride,
        "total_selected_targets": len(items),
        "shard_targets": len(shard_items),
        "records_written": written,
        "failed_frames": failed_frames,
        "include_grounding_dino": bool(args.include_grounding_dino),
        "query_variants": args.query_variants,
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[ycbv-probe] done summary={summary_path}", flush=True)


if __name__ == "__main__":
    main()
