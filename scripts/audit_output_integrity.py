from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit EmbodiedStressBench JSON output integrity.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--show-first-error", action="store_true")
    args = parser.parse_args()

    root = Path(args.input)
    filenames = []
    counts = Counter()
    for path in root.rglob("*.json"):
        if path.name == "experiment_config_snapshot.json":
            continue
        filenames.append(path.name)
        item = json.loads(path.read_text(encoding="utf-8"))
        counts["episodes"] += 1
        counts["success"] += int(bool(item.get("success")))
        counts["runner_exception"] += int(item.get("failure_type") == "runner_exception" or item.get("status") == "error")
        counts["no_detection"] += int(item.get("failure_type") == "no_detection")
        debug = (item.get("prediction") or {}).get("debug_info") or {}
        reason = debug.get("selection_failure_reason")
        if reason:
            counts[f"selection_failure_reason::{reason}"] += 1
    duplicate_names = len([name for name, count in Counter(filenames).items() if count > 1])
    counts["duplicate_result_filenames"] = duplicate_names
    for key in sorted(counts):
        print(f"{key}: {counts[key]}")
    if args.show_first_error:
        for path in root.rglob("*.json"):
            if path.name == "experiment_config_snapshot.json":
                continue
            item = json.loads(path.read_text(encoding="utf-8"))
            if item.get("failure_type") == "runner_exception" or item.get("status") == "error":
                print(f"first_error_path: {path}")
                print(f"first_error_type: {item.get('error_type')}")
                print(f"first_error_message: {item.get('error_message')}")
                traceback = str(item.get("traceback", ""))
                print("first_error_traceback_head:")
                print("\n".join(traceback.splitlines()[:12]))
                break


if __name__ == "__main__":
    main()
