#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _compact_ts() -> str:
    return time.strftime("%Y%m%d_%H%M%SZ", time.gmtime())


def _load_id(path: Path, field_name: str) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return str(payload.get(field_name, "")).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build OVERLAY_SAVE_DOC_v1 from fuel digests and Rosetta maps.")
    parser.add_argument("--fuel-digest-json", action="append", default=[])
    parser.add_argument("--rosetta-map-json", action="append", default=[])
    parser.add_argument("--out-json", default="")
    args = parser.parse_args()

    fuel_paths = [Path(raw).resolve() for raw in sorted(set(args.fuel_digest_json))]
    map_paths = [Path(raw).resolve() for raw in sorted(set(args.rosetta_map_json))]
    if not fuel_paths and not map_paths:
        raise SystemExit("must provide at least one fuel digest or Rosetta map")

    payload = {
        "schema": "OVERLAY_SAVE_DOC_v1",
        "overlay_save_id": f"OVERLAY_SAVE__{_compact_ts()}",
        "created_utc": _utc_now(),
        "fuel_digests": [
            {"path": str(path), "digest_id": _load_id(path, "digest_id"), "sha256": _sha256_file(path)}
            for path in fuel_paths
        ],
        "rosetta_maps": [
            {"path": str(path), "map_id": _load_id(path, "map_id"), "sha256": _sha256_file(path)}
            for path in map_paths
        ],
        "provenance": {"source_pointers": [str(path) for path in [*fuel_paths, *map_paths]]},
        "integrity_hashes": {
            "fuel_digest_count": len(fuel_paths),
            "rosetta_map_count": len(map_paths),
        },
    }
    out_path = Path(args.out_json).resolve() if str(args.out_json).strip() else None
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
