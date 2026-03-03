#!/usr/bin/env python3
"""
Master validation runner for CKAN migration backups.

What it validates:
1) API-level counts and sample IDs (validate_backup.py)
2) Dataset/resource metadata diffs (detailed_backup_comparison.py)
3) File content equality by SHA256 + relative path comparison

Usage example:
    python run_full_validation.py \
      --remote-url https://datosgestionabierta.cba.gov.ar \
      --local-url http://localhost:5000 \
      --backup-base ../Back_up_original/var/lib/ckan/datosgestionabierta \
      --target-storage /app/cba_gestionabierta/storage

If --target-storage is not provided, file-content comparison is skipped.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


ROOT = Path(__file__).resolve().parent


def run_command(command: List[str]) -> Tuple[int, str, str]:
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def hash_file_sha256(file_path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as handler:
        while True:
            chunk = handler.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(base_dir: Path) -> Dict[str, Dict[str, object]]:
    manifest: Dict[str, Dict[str, object]] = {}
    if not base_dir.exists():
        return manifest

    for path in sorted(base_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(base_dir).as_posix()
        stat = path.stat()
        manifest[rel] = {
            "sha256": hash_file_sha256(path),
            "size": stat.st_size,
            "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
    return manifest


def compare_manifests(source: Dict[str, Dict[str, object]], target: Dict[str, Dict[str, object]]) -> Dict[str, object]:
    source_paths = set(source.keys())
    target_paths = set(target.keys())

    missing_in_target = sorted(source_paths - target_paths)
    extra_in_target = sorted(target_paths - source_paths)

    content_different = []
    metadata_different = []

    for rel in sorted(source_paths & target_paths):
        source_item = source[rel]
        target_item = target[rel]

        if source_item["sha256"] != target_item["sha256"]:
            content_different.append(
                {
                    "path": rel,
                    "source_sha256": source_item["sha256"],
                    "target_sha256": target_item["sha256"],
                    "source_size": source_item["size"],
                    "target_size": target_item["size"],
                }
            )
        elif (
            source_item.get("size") is not None
            and target_item.get("size") is not None
            and source_item["size"] != target_item["size"]
        ):
            metadata_different.append(
                {
                    "path": rel,
                    "field": "size",
                    "source": source_item["size"],
                    "target": target_item["size"],
                }
            )

    return {
        "source_files": len(source_paths),
        "target_files": len(target_paths),
        "missing_in_target": missing_in_target,
        "extra_in_target": extra_in_target,
        "content_different": content_different,
        "metadata_different": metadata_different,
    }


def build_manifest_from_container(container_name: str, container_dir: str) -> Dict[str, Dict[str, object]]:
    manifest: Dict[str, Dict[str, object]] = {}
    script = (
        "set -e; "
        f"base={container_dir!r}; "
        "if [ ! -d \"$base\" ]; then exit 0; fi; "
        "find \"$base\" -type f -print0 | xargs -0 sha256sum"
    )
    cmd = ["docker", "exec", container_name, "bash", "-lc", script]
    code, stdout, stderr = run_command(cmd)
    if code != 0:
        raise RuntimeError(f"Cannot build container manifest for {container_dir}: {stderr.strip() or stdout.strip()}")

    base_path = Path(container_dir)
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        sha256_value, abs_path = parts
        try:
            rel = Path(abs_path).relative_to(base_path).as_posix()
        except Exception:
            continue
        manifest[rel] = {
            "sha256": sha256_value,
            "size": None,
            "mtime": None,
        }
    return manifest


def summarize_file_comparison(label: str, diff: Dict[str, object]) -> Dict[str, object]:
    missing = len(diff["missing_in_target"])
    extra = len(diff["extra_in_target"])
    content = len(diff["content_different"])
    metadata = len(diff["metadata_different"])

    return {
        "label": label,
        "source_files": diff["source_files"],
        "target_files": diff["target_files"],
        "missing_count": missing,
        "extra_count": extra,
        "content_different_count": content,
        "metadata_different_count": metadata,
        "is_equal": missing == 0 and extra == 0 and content == 0 and metadata == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Master validation for CKAN migration")
    parser.add_argument("--remote-url", required=True, help="Remote CKAN URL")
    parser.add_argument("--local-url", default="http://localhost:5000", help="Local CKAN URL")
    parser.add_argument("--api-key", default=None, help="CKAN API key if needed")
    parser.add_argument(
        "--backup-base",
        default="../Back_up_original/var/lib/ckan/datosgestionabierta",
        help="Backup base folder that contains resources and storage/uploads",
    )
    parser.add_argument(
        "--target-storage",
        default=None,
        help="Target CKAN storage folder that contains resources and uploads",
    )
    parser.add_argument(
        "--target-container",
        default=None,
        help="Docker container name for target CKAN storage comparison",
    )
    parser.add_argument(
        "--target-container-storage",
        default="/app/ckanext-cba_gestionabierta/storage",
        help="Storage base path inside target container",
    )
    parser.add_argument(
        "--output",
        default="full_validation_report.json",
        help="Output report JSON",
    )

    args = parser.parse_args()

    backup_base = Path(args.backup_base).resolve()
    report = {
        "timestamp": datetime.now().isoformat(),
        "inputs": {
            "remote_url": args.remote_url,
            "local_url": args.local_url,
            "backup_base": str(backup_base),
            "target_storage": args.target_storage,
            "target_container": args.target_container,
            "target_container_storage": args.target_container_storage,
        },
        "steps": {},
        "summary": {},
    }

    print("\n=== 1) Running API summary validation ===")
    validate_backup_output = ROOT / "backup_validation.json"
    cmd = [
        sys.executable,
        str(ROOT / "validate_backup.py"),
        "--remote-url",
        args.remote_url,
        "--local-url",
        args.local_url,
        "--output",
        str(validate_backup_output),
    ]
    if args.api_key:
        cmd.extend(["--api-key", args.api_key])

    code, stdout, stderr = run_command(cmd)
    print(stdout)
    if stderr.strip():
        print(stderr)
    report["steps"]["validate_backup"] = {
        "exit_code": code,
        "output_file": str(validate_backup_output),
    }

    print("\n=== 2) Running detailed dataset/resource validation ===")
    detailed_output = ROOT / "detailed_comparison.json"
    cmd = [
        sys.executable,
        str(ROOT / "detailed_backup_comparison.py"),
        "--remote-url",
        args.remote_url,
        "--local-url",
        args.local_url,
        "--output",
        str(detailed_output),
    ]
    if args.api_key:
        cmd.extend(["--api-key", args.api_key])

    code_detailed, stdout_detailed, stderr_detailed = run_command(cmd)
    print(stdout_detailed)
    if stderr_detailed.strip():
        print(stderr_detailed)
    report["steps"]["detailed_backup_comparison"] = {
        "exit_code": code_detailed,
        "output_file": str(detailed_output),
    }

    file_compare_result = None
    file_compare_summary = None

    if args.target_storage or args.target_container:
        print("\n=== 3) Running file-content equality checks (SHA256) ===")
        target_storage = None
        if args.target_storage:
            target_storage = Path(args.target_storage).resolve()

        source_resources = backup_base / "resources"
        source_uploads = backup_base / "storage" / "uploads"

        resources_source_manifest = build_manifest(source_resources)
        uploads_source_manifest = build_manifest(source_uploads)

        if args.target_container:
            container_storage = args.target_container_storage.rstrip("/")
            uploads_dir = f"{container_storage}/uploads"
            check_uploads_cmd = [
                "docker",
                "exec",
                args.target_container,
                "bash",
                "-lc",
                f"test -d {uploads_dir!r}",
            ]
            check_code, _, _ = run_command(check_uploads_cmd)
            if check_code != 0:
                alt_uploads_dir = f"{container_storage}/storage/uploads"
                check_alt_cmd = [
                    "docker",
                    "exec",
                    args.target_container,
                    "bash",
                    "-lc",
                    f"test -d {alt_uploads_dir!r}",
                ]
                alt_code, _, _ = run_command(check_alt_cmd)
                if alt_code == 0:
                    uploads_dir = alt_uploads_dir

            resources_target_manifest = build_manifest_from_container(
                args.target_container,
                f"{container_storage}/resources",
            )
            uploads_target_manifest = build_manifest_from_container(
                args.target_container,
                uploads_dir,
            )
            target_resources_label = f"{args.target_container}:{container_storage}/resources"
            target_uploads_label = f"{args.target_container}:{uploads_dir}"
        else:
            target_resources = target_storage / "resources"
            target_uploads = target_storage / "uploads"
            if not target_uploads.exists():
                alt_uploads = target_storage / "storage" / "uploads"
                if alt_uploads.exists():
                    target_uploads = alt_uploads
            resources_target_manifest = build_manifest(target_resources)
            uploads_target_manifest = build_manifest(target_uploads)
            target_resources_label = str(target_resources)
            target_uploads_label = str(target_uploads)

        resources_diff = compare_manifests(resources_source_manifest, resources_target_manifest)
        uploads_diff = compare_manifests(uploads_source_manifest, uploads_target_manifest)

        file_compare_result = {
            "resources": resources_diff,
            "uploads": uploads_diff,
        }
        file_compare_summary = {
            "resources": summarize_file_comparison("resources", resources_diff),
            "uploads": summarize_file_comparison("uploads", uploads_diff),
        }

        print("Resources:", file_compare_summary["resources"])
        print("Uploads:", file_compare_summary["uploads"])

        report["steps"]["file_content_comparison"] = {
            "enabled": True,
            "source_resources": str(source_resources),
            "target_resources": target_resources_label,
            "source_uploads": str(source_uploads),
            "target_uploads": target_uploads_label,
            "summary": file_compare_summary,
            "details": file_compare_result,
        }
    else:
        report["steps"]["file_content_comparison"] = {
            "enabled": False,
            "reason": "target_storage not provided",
        }

    api_ok = report["steps"]["validate_backup"]["exit_code"] == 0
    detailed_ok = report["steps"]["detailed_backup_comparison"]["exit_code"] == 0

    file_content_enabled = bool(file_compare_summary)
    files_ok = False
    if file_compare_summary:
        files_ok = file_compare_summary["resources"]["is_equal"] and file_compare_summary["uploads"]["is_equal"]

    report["summary"] = {
        "api_summary_ok": api_ok,
        "detailed_metadata_ok": detailed_ok,
        "file_content_enabled": file_content_enabled,
        "file_content_ok": files_ok,
        "overall_ok": api_ok and detailed_ok and files_ok,
    }

    output_path = Path(args.output).resolve()
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n=== FINAL SUMMARY ===")
    print(json.dumps(report["summary"], indent=2))
    print(f"\nFull report saved to: {output_path}")

    if report["summary"]["overall_ok"]:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
