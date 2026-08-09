#!/usr/bin/env python3
"""Create a controller-side hash manifest for one immutable artifact scope.

The output must remain outside the scope it seals.  It is a packaging snapshot,
not a simulation verifier and not an authority for scientific claims.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


IGNORE_DIRS = {"__pycache__", ".git", "mplconfig", "numba_cache"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    root = args.artifact_root.resolve()
    output = args.output.resolve()
    if not root.is_dir():
        print(f"artifact root does not exist: {root}", file=sys.stderr)
        return 2
    try:
        output.relative_to(root)
    except ValueError:
        pass
    else:
        print("output must be outside artifact root", file=sys.stderr)
        return 2

    hashes: dict[str, str] = {}
    escaping: list[str] = []
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in IGNORE_DIRS]
        for filename in filenames:
            lexical = Path(directory) / filename
            relative = str(lexical.relative_to(root))
            try:
                lexical.resolve().relative_to(root)
            except ValueError:
                escaping.append(relative)
                continue
            # ``./`` makes even a root-level file path-qualified.  The strict
            # consumer deliberately rejects a bare filename because it has no
            # stable scope identity.
            hashes[f"./{relative}"] = sha256(lexical)
    if escaping:
        print(f"artifact root has escaping symlink paths: {escaping}", file=sys.stderr)
        return 1

    receipt = {
        "schema": "cb.sealed-artifact-manifest.v1",
        "artifact_root_label": root.name,
        "artifact_hashes": dict(sorted(hashes.items())),
        "artifact_count": len(hashes),
        "claim_ceiling": "sealed byte-level package snapshot only; no execution, scientific, admission, or release claim",
        "promotion_allowed": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(f"sealed_artifacts={len(hashes)} manifest={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
