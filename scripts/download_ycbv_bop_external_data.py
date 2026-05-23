from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from huggingface_hub import hf_hub_download


FILES = [
    "ycbv_base.zip",
    "ycbv_models.zip",
    "ycbv_test_all.zip",
]


def _unzip_once(archive: Path, output_dir: Path) -> None:
    marker = output_dir / f".extracted_{archive.name}"
    if marker.exists():
        print(f"[ycbv-download] skip extract {archive.name}: marker exists", flush=True)
        return
    print(f"[ycbv-download] extracting {archive} -> {output_dir}", flush=True)
    subprocess.run(["unzip", "-n", str(archive), "-d", str(output_dir)], check=True)
    marker.write_text("ok\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="/data/openMythosBench_project/external_data/ycbv_bop",
        help="Destination directory for BOP-format YCB-V archives and extracted data.",
    )
    parser.add_argument(
        "--cache-dir",
        default="/data/openMythosBench_project/external_data/hf_cache",
        help="Hugging Face cache directory.",
    )
    parser.add_argument(
        "--repo-id",
        default="bop-benchmark/ycbv",
        help="Hugging Face dataset repository containing BOP YCB-V archives.",
    )
    parser.add_argument("--no-extract", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output)
    downloads_dir = output_dir / "downloads"
    cache_dir = Path(args.cache_dir)
    downloads_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    manifest_lines = [
        "repo_id,filename,local_archive",
    ]
    for filename in FILES:
        print(f"[ycbv-download] downloading {filename}", flush=True)
        archive_path = hf_hub_download(
            repo_id=args.repo_id,
            repo_type="dataset",
            filename=filename,
            cache_dir=str(cache_dir),
            local_dir=str(downloads_dir),
            local_dir_use_symlinks=False,
            resume_download=True,
        )
        archive = Path(archive_path)
        manifest_lines.append(f"{args.repo_id},{filename},{archive}")
        print(f"[ycbv-download] ready {filename}: {archive}", flush=True)
        if not args.no_extract:
            _unzip_once(archive, output_dir)

    manifest = output_dir / "download_manifest.csv"
    manifest.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    print(f"[ycbv-download] complete manifest={manifest}", flush=True)


if __name__ == "__main__":
    main()
