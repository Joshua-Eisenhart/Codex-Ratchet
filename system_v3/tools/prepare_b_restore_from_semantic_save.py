#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from extract_thread_s_snapshot_from_semantic_save import extract_snapshot_bytes, resolve_semantic_save_source


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Prepare a B-boundary restore bundle from a semantic save surface.")
    ap.add_argument("--project-save-doc", default="")
    ap.add_argument("--full-plus-zip", default="")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)

    project_save_path = Path(args.project_save_doc).expanduser().resolve() if str(args.project_save_doc).strip() else None
    full_plus_zip = Path(args.full_plus_zip).expanduser().resolve() if str(args.full_plus_zip).strip() else None
    if project_save_path is None and full_plus_zip is None:
        raise SystemExit("must provide --project-save-doc and/or --full-plus-zip")

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    resolved_full_plus_zip, _project_payload = resolve_semantic_save_source(
        full_plus_zip=full_plus_zip,
        project_save_doc=project_save_path,
    )
    snapshot_bytes, extraction_report = extract_snapshot_bytes(
        full_plus_zip=resolved_full_plus_zip,
        project_save_doc=project_save_path,
    )

    snapshot_path = out_dir / "THREAD_S_SAVE_SNAPSHOT_v2.txt"
    snapshot_path.write_bytes(snapshot_bytes)

    restore_ready_path = out_dir / "THREAD_B_RESTORE_READY.txt"
    restore_ready_path.write_bytes(snapshot_bytes)

    packet = {
        "schema": "B_RESTORE_PREP_PACKET_v1",
        "created_utc": _utc_now(),
        "project_save_doc": str(project_save_path) if project_save_path is not None else "",
        "full_plus_zip": str(resolved_full_plus_zip),
        "snapshot_path": str(snapshot_path),
        "snapshot_sha256": extraction_report.get("snapshot_sha256", ""),
        "restore_ready_text_path": str(restore_ready_path),
        "next_steps": [
            "audit semantic save if not already audited",
            "use THREAD_S_SAVE_SNAPSHOT_v2.txt as the exact B restore witness",
            "verify B-side state/report surfaces after restore",
            "continue with current A2 controller boot",
        ],
    }

    packet_path = out_dir / "B_RESTORE_PREP_PACKET_v1.json"
    packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = {
        "schema": "B_RESTORE_PREP_REPORT_v1",
        "status": "PASS",
        "packet_path": str(packet_path),
        "snapshot_path": str(snapshot_path),
        "restore_ready_text_path": str(restore_ready_path),
    }
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
