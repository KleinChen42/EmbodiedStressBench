from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _save(fig: plt.Figure, out_dir: Path, name: str) -> None:
    fig.savefig(out_dir / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(out_dir / f"{name}.png", dpi=240, bbox_inches="tight")
    plt.close(fig)


def _box(ax, xy, width, height, text, facecolor="#f4f6f8", edgecolor="#334155"):
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        linewidth=1.2,
        edgecolor=edgecolor,
        facecolor=facecolor,
    )
    ax.add_patch(patch)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=9,
        linespacing=1.25,
    )


def _arrow(ax, start, end):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=13,
            linewidth=1.2,
            color="#334155",
        )
    )


def pipeline_overview(out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.6, 3.0))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    boxes = [
        ((0.03, 0.56), "Language query\nRGB-D observation\nDetection list"),
        ((0.28, 0.56), "Query-aware or\nfirst-detection\nselection"),
        ((0.53, 0.56), "RGB-D target\nsource\n3D target"),
        ((0.78, 0.56), "Oracle-gap\nfailure diagnosis\nJSON report"),
    ]
    for xy, text in boxes:
        _box(ax, xy, 0.19, 0.28, text)
    for x in [0.22, 0.47, 0.72]:
        _arrow(ax, (x, 0.70), (x + 0.055, 0.70))

    _box(
        ax,
        (0.17, 0.12),
        0.66,
        0.22,
        "Controlled stressors: semantic distractors, visual occlusion,\n"
        "depth/camera perturbations, and execution offsets",
        facecolor="#eef6f2",
        edgecolor="#2f7d5b",
    )
    _arrow(ax, (0.50, 0.34), (0.50, 0.55))
    ax.text(0.5, 0.95, "EmbodiedStressBench diagnostic pipeline", ha="center", fontsize=11, weight="bold")
    _save(fig, out_dir, "fig_pipeline_overview")


def stressor_taxonomy(out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.4, 3.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    categories = [
        ("Semantic", "same-shape\nsame-color\nnearby distractor", "#e8f1fb"),
        ("Visual", "target occlusion\nvisual occlusion", "#f9efe5"),
        ("Geometric", "depth sparsity\ndepth noise\ncamera pose noise", "#eef6f2"),
        ("Execution", "offset\nstrong offset", "#f4eef9"),
    ]
    x_positions = [0.04, 0.28, 0.52, 0.76]
    for x, (title, body, color) in zip(x_positions, categories):
        _box(ax, (x, 0.30), 0.20, 0.42, f"{title}\n\n{body}", facecolor=color)
    ax.text(0.5, 0.90, "Stressor taxonomy used for diagnostic sweeps", ha="center", fontsize=11, weight="bold")
    ax.text(0.5, 0.13, "Each stressor is evaluated across levels 0--3 with the same metric schema.", ha="center", fontsize=9)
    _save(fig, out_dir, "fig_stressor_taxonomy")


def main() -> None:
    out_dir = Path("paper/generated")
    _ensure_dir(out_dir)
    pipeline_overview(out_dir)
    stressor_taxonomy(out_dir)
    print(f"Wrote diagram figures under {out_dir}")


if __name__ == "__main__":
    main()
