#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path


LEGACY_WRAPPER_RE = re.compile(r"^(?:BOOTPACK_THREAD_|THREAD_(?:A|B|M|S|SIM)\b)")
ALLOWED_PREFIXES = (
    "AUDIT_",
    "CAMPAIGN_",
    "EXPORT_",
    "FUEL_",
    "OVERLAY_",
    "PROJECT_",
    "ROSETTA_",
    "TAPE_",
)
ALLOWED_EXACT = {
    "SIM_EVIDENCE",
    "SIM_EVIDENCE_PACK",
}


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _compact_ts() -> str:
    return time.strftime("%Y%m%d_%H%M%SZ", time.gmtime())


def _is_kernel_lane_candidate(anchor: str) -> bool:
    token = str(anchor).strip().upper()
    if not token:
        return False
    if LEGACY_WRAPPER_RE.match(token):
        return False
    if token.endswith("_SHA256") or token.endswith("_ID"):
        return False
    if token in ALLOWED_EXACT:
        return True
    return any(token.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EXPORT_CANDIDATE_PACK_v1 from Rosetta maps and fuel digests.")
    parser.add_argument("--rosetta-map-json", action="append", default=[])
    parser.add_argument("--fuel-digest-json", action="append", default=[])
    parser.add_argument("--out-json", default="")
    args = parser.parse_args()

    candidate_items: list[dict] = []
    negative_pressure: list[dict] = []
    source_pointers: list[str] = []
    counter = 0

    for raw in sorted(set(args.rosetta_map_json)):
        path = Path(raw).resolve()
        source_pointers.append(str(path))
        payload = json.loads(path.read_text(encoding="utf-8"))
        entries = payload.get("entries", []) if isinstance(payload.get("entries"), list) else []
        for row in entries:
            if not isinstance(row, dict):
                continue
            if str(row.get("status", "")).strip() != "BOUND":
                continue
            kernel_anchor = str(row.get("kernel_anchor", "")).strip()
            if not _is_kernel_lane_candidate(kernel_anchor):
                continue
            counter += 1
            candidate_items.append(
                {
                    "candidate_id": f"ECP_{counter:05d}",
                    "kernel_anchor": kernel_anchor,
                    "anchor_type": str(row.get("anchor_type", "")).strip(),
                    "source_term": str(row.get("source_term", "")).strip(),
                    "source_pointers": list(row.get("source_pointers", []) or []),
                }
            )

    for raw in sorted(set(args.fuel_digest_json)):
        path = Path(raw).resolve()
        source_pointers.append(str(path))
        payload = json.loads(path.read_text(encoding="utf-8"))
        claims = payload.get("extracted_claims", []) if isinstance(payload.get("extracted_claims"), list) else []
        for row in claims:
            if not isinstance(row, dict):
                continue
            text = str(row.get("text", "")).strip().lower()
            if any(flag in text for flag in ("forbidden", "must not", "never", "deny", "append-only")):
                negative_pressure.append(
                    {
                        "pressure_id": str(row.get("claim_id", "")).strip(),
                        "text": str(row.get("text", "")).strip(),
                        "source_pointer": str(row.get("source_pointer", "")).strip(),
                    }
                )

    payload = {
        "schema": "EXPORT_CANDIDATE_PACK_v1",
        "pack_id": f"EXPORT_CANDIDATE_PACK__{_compact_ts()}",
        "created_utc": _utc_now(),
        "candidate_items": sorted(candidate_items, key=lambda row: (row["anchor_type"], row["kernel_anchor"], row["source_term"], row["candidate_id"])),
        "required_dependencies": [],
        "negative_pressure": sorted(negative_pressure, key=lambda row: (row["source_pointer"], row["pressure_id"])),
        "source_pointers": sorted(set(source_pointers)),
    }
    out_path = Path(args.out_json).resolve() if str(args.out_json).strip() else None
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
