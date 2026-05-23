from __future__ import annotations

import json
import os


def main() -> None:
    report: dict[str, object] = {"ld_preload": os.environ.get("LD_PRELOAD", "")}
    try:
        import sklearn  # noqa: F401

        report["sklearn_import"] = "ok"
    except Exception as exc:  # pragma: no cover
        report["sklearn_import"] = f"{type(exc).__name__}: {exc}"
    try:
        from embodied_stressbench.detectors.grounding_dino import GroundingDinoProvider

        provider = GroundingDinoProvider()
        report["provider"] = "ok"
        report["model_name"] = provider.model_name
        report["device"] = provider.device
    except Exception as exc:  # pragma: no cover
        report["provider"] = f"{type(exc).__name__}: {exc}"
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
