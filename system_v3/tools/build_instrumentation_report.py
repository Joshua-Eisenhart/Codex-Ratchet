#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            row = json.loads(text)
        except Exception:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _status(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build INSTRUMENTATION_REPORT_v1 from a run surface.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--out-json", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    summary = _read_json(run_dir / "summary.json")
    state = _read_json(run_dir / "state.json")
    heavy = _read_json(run_dir / "state.heavy.json")
    events = _read_jsonl(run_dir / "logs" / "events.000.jsonl")
    export_tape = _read_jsonl(run_dir / "tapes" / "export_tape.000.jsonl")
    campaign_tape = _read_jsonl(run_dir / "tapes" / "campaign_tape.000.jsonl")
    zip_packets = sorted((run_dir / "zip_packets").glob("*.zip"))

    reject_tags = Counter()
    for row in events:
        for tag in row.get("reject_tags", []) if isinstance(row.get("reject_tags"), list) else []:
            reject_tags[str(tag)] += 1

    warnings: list[str] = []
    if not summary:
        warnings.append("missing_summary_json")
    if not state:
        warnings.append("missing_state_json")
    if len(zip_packets) == 0:
        warnings.append("no_zip_packets")
    if len(events) == 0:
        warnings.append("no_event_log_rows")
    if len(export_tape) == 0:
        warnings.append("no_export_tape_rows")
    if len(campaign_tape) == 0:
        warnings.append("no_campaign_tape_rows")
    if summary and int(summary.get("unresolved_promotion_blocker_count", 0) or 0) > 0:
        warnings.append("promotion_blockers_present")

    report = {
        "schema": "INSTRUMENTATION_REPORT_v1",
        "status": "PASS" if summary or state or heavy else "FAIL",
        "run_dir": str(run_dir),
        "counts": {
            "zip_packet_count": len(zip_packets),
            "event_count": len(events),
            "export_tape_count": len(export_tape),
            "campaign_tape_count": len(campaign_tape),
            "evidence_pending_count": len(state.get("evidence_pending", {}) or {}),
            "reject_log_count": len(state.get("reject_log", []) or {}),
            "kill_log_count": len(state.get("kill_log", []) or {}),
            "sim_registry_count": len(heavy.get("sim_registry", {}) or {}),
            "sim_results_count": len(heavy.get("sim_results", {}) or {}),
            "term_registry_count": len(state.get("term_registry", {}) or {}),
        },
        "digest_pressure": {
            "unique_strategy_digest_count": int(summary.get("unique_strategy_digest_count", 0) or 0),
            "unique_export_content_digest_count": int(summary.get("unique_export_content_digest_count", 0) or 0),
            "unique_export_structural_digest_count": int(summary.get("unique_export_structural_digest_count", 0) or 0),
            "id_churn_signal": bool(summary.get("id_churn_signal", False)),
        },
        "top_reject_tags": [
            {"tag": tag, "count": count}
            for tag, count in sorted(reject_tags.items(), key=lambda row: (-row[1], row[0]))[:10]
        ],
        "warnings": warnings,
        "source_pointers": [
            str(path)
            for path in [
                run_dir / "summary.json",
                run_dir / "state.json",
                run_dir / "state.heavy.json",
                run_dir / "logs" / "events.000.jsonl",
                run_dir / "tapes" / "export_tape.000.jsonl",
                run_dir / "tapes" / "campaign_tape.000.jsonl",
            ]
            if path.exists()
        ],
    }
    out_path = Path(args.out_json).resolve() if str(args.out_json).strip() else None
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
