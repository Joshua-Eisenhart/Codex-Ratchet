#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            row = json.loads(text)
        except Exception:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out


def _tape_digest(rows: list[dict]) -> str:
    return hashlib.sha256((json.dumps(rows, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")).hexdigest()


def _summarize_rows(rows: list[dict]) -> dict:
    seqs = [int(row.get("seq", 0) or 0) for row in rows]
    export_ids = [str(row.get("export_id", "")).strip() for row in rows if str(row.get("export_id", "")).strip()]
    return {
        "entry_count": len(rows),
        "first_seq": min(seqs) if seqs else 0,
        "last_seq": max(seqs) if seqs else 0,
        "first_export_id": export_ids[0] if export_ids else "",
        "last_export_id": export_ids[-1] if export_ids else "",
        "unique_export_id_count": len(set(export_ids)),
        "digest_sha256": _tape_digest(rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build TAPE_SUMMARY_REPORT_v1 for a run surface.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--out-json", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    export_tape_path = run_dir / "tapes" / "export_tape.000.jsonl"
    campaign_tape_path = run_dir / "tapes" / "campaign_tape.000.jsonl"

    export_rows = _read_jsonl(export_tape_path)
    campaign_rows = _read_jsonl(campaign_tape_path)
    export_pairs = {(int(row.get("seq", 0) or 0), str(row.get("export_id", "")).strip()) for row in export_rows}
    campaign_pairs = {(int(row.get("seq", 0) or 0), str(row.get("export_id", "")).strip()) for row in campaign_rows}
    missing_pair_anomalies = [
        {"kind": "campaign_missing_export_pair", "seq": seq, "export_id": export_id}
        for seq, export_id in sorted(campaign_pairs - export_pairs)
    ] + [
        {"kind": "export_missing_campaign_pair", "seq": seq, "export_id": export_id}
        for seq, export_id in sorted(export_pairs - campaign_pairs)
    ]

    summary = {
        "schema": "TAPE_SUMMARY_REPORT_v1",
        "run_dir": str(run_dir),
        "status": "PASS" if export_rows or campaign_rows else "FAIL",
        "export_tape": {
            **_summarize_rows(export_rows),
            "path": str(export_tape_path),
            "file_sha256": _sha256_file(export_tape_path) if export_tape_path.exists() else "",
        },
        "campaign_tape": {
            **_summarize_rows(campaign_rows),
            "path": str(campaign_tape_path),
            "file_sha256": _sha256_file(campaign_tape_path) if campaign_tape_path.exists() else "",
        },
        "missing_pair_anomalies": missing_pair_anomalies,
    }
    out_path = Path(args.out_json).resolve() if str(args.out_json).strip() else None
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
