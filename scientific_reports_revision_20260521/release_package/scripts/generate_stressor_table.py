from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


DEFAULT_STRESSORS = [
    "same_shape_distractor",
    "same_color_distractor",
    "nearby_distractor",
    "partial_target_occlusion",
    "visual_occlusion",
    "depth_sparsity",
    "depth_noise",
    "camera_pose_noise",
    "execution_offset",
    "execution_offset_strong",
]

DISPLAY_NAMES = {
    "same_shape_distractor": "Same-shape distractor",
    "same_color_distractor": "Same-color distractor",
    "nearby_distractor": "Nearby distractor",
    "partial_target_occlusion": "Partial target occlusion",
    "visual_occlusion": "Visual occlusion",
    "depth_sparsity": "Depth sparsity",
    "depth_noise": "Depth noise",
    "camera_pose_noise": "Camera-pose noise",
    "execution_offset": "Execution offset",
    "execution_offset_strong": "Strong execution offset",
}


NOTE_TEXT = {
    "same_shape_distractor": "List-order distractor.",
    "same_color_distractor": "List-order distractor.",
    "nearby_distractor": "List-order distractor.",
    "partial_target_occlusion": "Target crop only.",
    "visual_occlusion": "Image-level occlusion.",
    "depth_sparsity": "Target crop only.",
    "depth_noise": "Depth noise plus missing depth.",
    "camera_pose_noise": "Translation and rotation perturbation.",
    "execution_offset": "Execution target offset.",
    "execution_offset_strong": "Stronger execution target offset.",
}


def _level_text(value: Any) -> str:
    if isinstance(value, dict):
        if "bbox_shift_fraction" in value:
            return f"shift={value['bbox_shift_fraction']:.2f}"
        if "occlusion_fraction" in value:
            return f"occ={100 * float(value['occlusion_fraction']):.0f}%"
        if "missing_prob" in value and "sigma" not in value:
            return f"missing={100 * float(value['missing_prob']):.0f}%"
        if "sigma" in value:
            return f"sigma={float(value['sigma']):.3f}, miss={100 * float(value.get('missing_prob', 0.0)):.0f}%"
        if "translation_std" in value:
            return f"trans={float(value['translation_std']):.3f}m, rot={float(value.get('rotation_deg_std', 0.0)):.1f}deg"
        if "offset_std" in value:
            return f"std={float(value['offset_std']):.3f}m"
        return "; ".join(f"{k}={v}" for k, v in value.items())
    return str(value)


def _escape_tex(value: object) -> str:
    text = str(value)
    for src, dst in {
        "\\": r"\textbackslash{}",
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
        "$": r"\$",
        "{": r"\{",
        "}": r"\}",
    }.items():
        text = text.replace(src, dst)
    return text


def _latex_table(df: pd.DataFrame) -> str:
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Parameterized stressor levels used in EmbodiedStressBench. Values are generated from YAML stressor configuration files.}",
        r"\label{tab:stressor-parameters}",
        r"\tiny",
        r"\setlength{\tabcolsep}{2pt}",
        r"\begin{tabular}{@{}p{0.16\linewidth}p{0.12\linewidth}p{0.12\linewidth}p{0.12\linewidth}p{0.12\linewidth}p{0.19\linewidth}@{}}",
        r"\hline",
        r"Stressor & Level 0 & Level 1 & Level 2 & Level 3 & Notes \\",
        r"\hline",
    ]
    for _, row in df.iterrows():
        lines.append(
            " & ".join(
                    _escape_tex(row[col])
                for col in ["stressor", "level_0", "level_1", "level_2", "level_3", "notes"]
            )
            + r" \\"
        )
    lines.extend(
        [
            r"\hline",
            r"\end{tabular}",
            r"\begin{flushleft}\footnotesize Semantic-distractor shift is an image-space horizontal displacement measured as a multiple of the target bounding-box width. ``List-order distractor'' means the distractor detection is inserted before the target detection to test first-detection failure; it does not denote physical object ordering.\end{flushleft}",
            r"\end{table*}",
            "",
        ]
    )
    return "\n".join(lines)


def build_table(config_dir: Path, stressors: list[str]) -> pd.DataFrame:
    rows = []
    for name in stressors:
        path = config_dir / f"{name}.yaml"
        if not path.exists():
            rows.append(
                {
                    "stressor": name,
                    "level_0": "MISSING",
                    "level_1": "MISSING",
                    "level_2": "MISSING",
                    "level_3": "MISSING",
                    "notes": f"Missing config file: {path}",
                }
            )
            continue
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        levels = data.get("levels", {})
        rows.append(
            {
                "stressor": DISPLAY_NAMES.get(data.get("name", name), data.get("name", name)),
                "level_0": _level_text(levels.get(0, levels.get("0", ""))),
                "level_1": _level_text(levels.get(1, levels.get("1", ""))),
                "level_2": _level_text(levels.get(2, levels.get("2", ""))),
                "level_3": _level_text(levels.get(3, levels.get("3", ""))),
                "notes": NOTE_TEXT.get(data.get("name", name), data.get("description", "")),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-dir", default="configs/stressors")
    parser.add_argument("--output-csv", default="ieee_access_revision_20260520/stressor_parameter_table.csv")
    parser.add_argument("--output-tex", default="paper/ieee_access/tables/stressor_parameter_table.tex")
    parser.add_argument("--stressors", nargs="*", default=DEFAULT_STRESSORS)
    args = parser.parse_args()

    df = build_table(Path(args.config_dir), args.stressors)
    csv_path = Path(args.output_csv)
    tex_path = Path(args.output_tex)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    tex_path.write_text(_latex_table(df), encoding="utf-8")
    print(f"Wrote {csv_path}")
    print(f"Wrote {tex_path}")


if __name__ == "__main__":
    main()
