from __future__ import annotations

import json


def _check_clip(model_name: str) -> dict:
    try:
        from transformers import CLIPModel, CLIPProcessor

        CLIPProcessor.from_pretrained(model_name, local_files_only=True)
        CLIPModel.from_pretrained(model_name, local_files_only=True)
        return {"model": model_name, "loadable": True, "error": None}
    except Exception as exc:
        return {"model": model_name, "loadable": False, "error": f"{type(exc).__name__}: {exc}"}


def _check_grounding_dino(model_name: str) -> dict:
    try:
        from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

        AutoProcessor.from_pretrained(model_name, local_files_only=True)
        AutoModelForZeroShotObjectDetection.from_pretrained(model_name, local_files_only=True)
        return {"model": model_name, "loadable": True, "error": None}
    except Exception as exc:
        return {"model": model_name, "loadable": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> None:
    report = {
        "clip": [
            _check_clip("openai/clip-vit-base-patch32"),
            _check_clip("laion/CLIP-ViT-B-32-laion2B-s34B-b79K"),
        ],
        "grounding_dino": [
            _check_grounding_dino("IDEA-Research/grounding-dino-tiny"),
        ],
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
