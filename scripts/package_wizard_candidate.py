#!/usr/bin/env python3
"""Package the Wizard v2.7 candidate directory with a checksum receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATE = (
    ROOT
    / "work"
    / "mmm_wizard_repair"
    / "mmm_wizard_complete_system_packet_v2_7_candidate"
)
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def _default_zip_path(input_path: Path) -> Path:
    return input_path.parent / f"{input_path.name}.zip"


def _sidecar_path(zip_path: Path) -> Path:
    return Path(f"{zip_path}.sha256")


def _is_legacy_v26_manifest(path: Path) -> bool:
    normalized = path.name.lower().replace(".", "_").replace("-", "_")
    return "manifest" in normalized and "v2_6" in normalized


def _is_excluded(path: Path, generated_paths: set[Path]) -> bool:
    if path.name == ".DS_Store":
        return True
    if "__pycache__" in path.parts or path.suffix == ".pyc":
        return True
    if _is_legacy_v26_manifest(path):
        return True
    try:
        if path.resolve() in generated_paths:
            return True
    except FileNotFoundError:
        return False
    return False


def _iter_package_files(input_path: Path, generated_paths: set[Path]) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(input_path):
        dirnames[:] = sorted(name for name in dirnames if name != "__MACOSX")
        base = Path(dirpath)
        for filename in sorted(filenames):
            path = base / filename
            if not _is_excluded(path, generated_paths):
                files.append(path)
    return sorted(files, key=lambda path: path.relative_to(input_path.parent).as_posix())


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_zip(input_path: Path, zip_path: Path, files: Iterable[Path]) -> None:
    temp_path = zip_path.with_name(f".{zip_path.name}.tmp")
    with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive_name = path.relative_to(input_path.parent).as_posix()
            info = zipfile.ZipInfo(archive_name, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    temp_path.replace(zip_path)


def package_candidate(
    input_path: Path | str = DEFAULT_CANDIDATE,
    *,
    zip_path: Path | str | None = None,
    receipt_path: Path | str | None = None,
) -> dict[str, object]:
    input_dir = Path(input_path).expanduser().resolve()
    if not input_dir.exists():
        raise FileNotFoundError(f"input path does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"input path is not a directory: {input_dir}")

    output_zip = Path(zip_path).expanduser().resolve() if zip_path is not None else _default_zip_path(input_dir)
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    sidecar = _sidecar_path(output_zip)
    output_receipt = Path(receipt_path).expanduser().resolve() if receipt_path is not None else None

    generated_paths = {output_zip.resolve(), sidecar.resolve()}
    if output_receipt is not None:
        generated_paths.add(output_receipt)

    files = _iter_package_files(input_dir, generated_paths)
    _write_zip(input_dir, output_zip, files)
    sha256 = _sha256_file(output_zip)
    sidecar.write_text(f"{sha256}  {output_zip.name}\n", encoding="utf-8")

    receipt: dict[str, object] = {
        "input_path": str(input_dir),
        "zip_path": str(output_zip),
        "sha256": sha256,
        "file_count": len(files),
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    if output_receipt is not None:
        output_receipt.parent.mkdir(parents=True, exist_ok=True)
        output_receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Zip a Wizard candidate directory, write a sha256 sidecar, and emit a JSON receipt."
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        default=DEFAULT_CANDIDATE,
        type=Path,
        help=f"candidate directory to package (default: {DEFAULT_CANDIDATE})",
    )
    parser.add_argument(
        "--zip-path",
        type=Path,
        default=None,
        help="output zip path (default: sibling '<candidate-name>.zip')",
    )
    parser.add_argument(
        "--receipt-path",
        type=Path,
        default=None,
        help="optional path to also write the JSON receipt",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        receipt = package_candidate(
            args.input_path,
            zip_path=args.zip_path,
            receipt_path=args.receipt_path,
        )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
