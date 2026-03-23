#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
import zipfile
from pathlib import Path


MINING_SCHEMA_TO_LOG = {
    "FUEL_DIGEST_v1": "fuel_digests.jsonl",
    "ROSETTA_MAP_v1": "rosetta_maps.jsonl",
    "OVERLAY_SAVE_DOC_v1": "overlay_save_docs.jsonl",
    "EXPORT_CANDIDATE_PACK_v1": "export_candidate_packs.jsonl",
}


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_zip_member_json(zf: zipfile.ZipFile, name: str) -> dict:
    return json.loads(zf.read(name).decode("utf-8"))


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _iter_mining_payloads(zf: zipfile.ZipFile) -> list[tuple[str, dict]]:
    payloads: list[tuple[str, dict]] = []
    for name in sorted(zf.namelist()):
        if not name.endswith(".json"):
            continue
        try:
            payload = _read_zip_member_json(zf, name)
        except Exception:
            continue
        schema = str(payload.get("schema", "")).strip()
        if schema in MINING_SCHEMA_TO_LOG:
            payloads.append((name, payload))
    return payloads


def _ingest_mining_payloads(
    *,
    a2_state_dir: Path,
    zip_path: Path,
    zip_sha: str,
    payloads: list[tuple[str, dict]],
) -> dict[str, int]:
    counts = {schema: 0 for schema in MINING_SCHEMA_TO_LOG}
    for member_name, payload in payloads:
        schema = str(payload.get("schema", "")).strip()
        log_name = MINING_SCHEMA_TO_LOG.get(schema, "")
        if not log_name:
            continue
        row = {
            "schema": f"{schema}__INGEST_EVENT_v1",
            "ts_utc": _utc_now(),
            "zip_path": zip_path.as_posix(),
            "zip_sha256": zip_sha,
            "zip_member": member_name,
            "payload": payload,
        }
        _append_jsonl(a2_state_dir / log_name, row)
        counts[schema] += 1
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ingest A2 distillery output ZIP into system_v3/a2_state append logs.")
    ap.add_argument("--zip", required=True, help="Path to A2_DISTILLERY_TEST_OUTPUT__*.zip")
    ap.add_argument("--a2-state-dir", default="system_v3/a2_state")
    ap.add_argument("--max-a2-entries", type=int, default=0, help="If >0, cap A2 'entries' ingested.")
    ap.add_argument("--max-rosetta", type=int, default=0, help="If >0, cap rosetta_candidates ingested.")
    args = ap.parse_args(argv)

    zip_path = Path(args.zip).expanduser().resolve()
    if not zip_path.is_file():
        raise SystemExit(f"missing zip: {zip_path}")

    a2_state_dir = Path(args.a2_state_dir).expanduser().resolve()
    if not a2_state_dir.is_dir():
        raise SystemExit(f"missing a2_state_dir: {a2_state_dir}")

    zip_sha = _sha256_file(zip_path)

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(zf.namelist())
        a2_json = next((n for n in names if n.startswith("A2_BRAIN_UPDATE_PACKET__") and n.endswith(".json")), "")
        a1_json = next((n for n in names if n.startswith("A1_BRAIN_ROSETTA_UPDATE_PACKET__") and n.endswith(".json")), "")
        report_md = next((n for n in names if n.startswith("DISTILLERY_REPORT__") and n.endswith(".md")), "")
        mining_payloads = _iter_mining_payloads(zf)
        if not a2_json and not a1_json and not mining_payloads:
            raise SystemExit(f"zip missing distillery packets: {zip_path}")

        a2_packet = _read_zip_member_json(zf, a2_json) if a2_json else {}
        a1_packet = _read_zip_member_json(zf, a1_json) if a1_json else {}
        report_head = ""
        if report_md:
            report_head = zf.read(report_md).decode("utf-8", errors="ignore").splitlines()[:80]
            report_head = "\n".join(report_head).strip()

    # A2 memory append (canonical A2 brain log surface)
    memory_jsonl = a2_state_dir / "memory.jsonl"
    a2_entries = list(a2_packet.get("entries", []) or []) if isinstance(a2_packet, dict) else []
    if args.max_a2_entries and args.max_a2_entries > 0:
        a2_entries = a2_entries[: args.max_a2_entries]

    if a2_packet:
        _append_jsonl(
            memory_jsonl,
            {
                "schema": "A2_DISTILLERY_INGEST_EVENT_v1",
                "ts_utc": _utc_now(),
                "zip_path": zip_path.as_posix(),
                "zip_sha256": zip_sha,
                "packet_id": str(a2_packet.get("packet_id", "")),
                "source_archive": str(a2_packet.get("source_archive", "")),
                "source_files": a2_packet.get("source_files", {}),
                "entries": a2_entries,
                "report_head": report_head,
            },
        )

    # A1 rosetta append (A1 brain surface stored under a2_state for cross-role continuity)
    a1_brain_jsonl = a2_state_dir / "a1_brain.jsonl"
    rosetta = list(a1_packet.get("rosetta_candidates", []) or []) if isinstance(a1_packet, dict) else []
    if args.max_rosetta and args.max_rosetta > 0:
        rosetta = rosetta[: args.max_rosetta]

    if a1_packet:
        _append_jsonl(
            a1_brain_jsonl,
            {
                "schema": "A1_ROSETTA_DISTILLERY_INGEST_EVENT_v1",
                "ts_utc": _utc_now(),
                "zip_path": zip_path.as_posix(),
                "zip_sha256": zip_sha,
                "packet_id": str(a1_packet.get("packet_id", "")),
                "source_archive": str(a1_packet.get("source_archive", "")),
                "source_files": a1_packet.get("source_files", {}),
                "rosetta_candidates": rosetta,
            },
        )

    mining_counts = _ingest_mining_payloads(
        a2_state_dir=a2_state_dir,
        zip_path=zip_path,
        zip_sha=zip_sha,
        payloads=mining_payloads,
    )

    print(
        json.dumps(
            {
                "ok": True,
                "zip_sha256": zip_sha,
                "a2_entries": len(a2_entries),
                "rosetta": len(rosetta),
                "mining_payloads": mining_counts,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
