#!/usr/bin/env python3
"""Verify archive paths and every hash in a Ratchet Process v1 bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    with zipfile.ZipFile(args.bundle) as zf:
        names = zf.namelist()
        if len(names) != len(set(names)):
            errors.append("duplicate archive member names")
        for name in names:
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts:
                errors.append(f"unsafe path: {name}")
        manifest_name = next((n for n in names if n.endswith("/bundle_manifest.json")), None)
        if not manifest_name:
            errors.append("bundle manifest missing")
            manifest = {}
        else:
            manifest = json.loads(zf.read(manifest_name))
        prefix = PurePosixPath(manifest_name).parent if manifest_name else PurePosixPath()
        expected = {manifest_name} if manifest_name else set()
        for item in manifest.get("included_files", []):
            name = str(prefix / PurePosixPath(item["path"]))
            expected.add(name)
            if name not in names:
                errors.append(f"missing member: {name}")
                continue
            actual = hashlib.sha256(zf.read(name)).hexdigest()
            if actual != item["sha256"]:
                errors.append(f"hash mismatch: {name}")
        extra = sorted(set(names) - expected)
        if extra:
            errors.append(f"unlisted archive members: {extra}")

    result = {
        "schema": "codex_ratchet.curated_process_bundle.validation.v1",
        "bundle": str(args.bundle),
        "bundle_sha256": hashlib.sha256(args.bundle.read_bytes()).hexdigest(),
        "errors": errors,
        "all_pass": not errors,
        "claim_ceiling": "archive integrity only; no scientific admission",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
