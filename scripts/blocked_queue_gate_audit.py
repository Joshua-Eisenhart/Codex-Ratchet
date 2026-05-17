#!/usr/bin/env python3
"""Audit blocked queue entries against the current stage-gate classifier."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import queue_claim


ROOT = Path(__file__).resolve().parents[1]
BLOCKED = ROOT / "system_v4" / "probes" / "a2_state" / "queue" / "blocked"


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    records = []
    for path in sorted(BLOCKED.glob("*.json*")):
        data = load_json(path)
        sim_path = str(data.get("sim_path") or "")
        reason = data.get("blocked_reason")
        old_claim = data.get("blocked_stage_claim")
        current_claim = queue_claim._stage_gate_claim_for_sim(sim_path) if sim_path else None
        current_allowed = True if not current_claim else queue_claim._stage_gate_allows_claim(current_claim)
        stale_stage_gate_block = reason == "stage_gate_blocked" and (not current_claim or current_allowed)
        records.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sim_path": sim_path,
                "blocked_reason": reason,
                "old_stage_claim": old_claim,
                "current_stage_claim": current_claim,
                "current_stage_allowed": current_allowed,
                "stale_stage_gate_block": stale_stage_gate_block,
            }
        )

    reason_counts = Counter(record["blocked_reason"] for record in records)
    old_claim_counts = Counter(
        record["old_stage_claim"] for record in records if record["blocked_reason"] == "stage_gate_blocked"
    )
    current_claim_counts = Counter(
        record["current_stage_claim"] for record in records if record["blocked_reason"] == "stage_gate_blocked"
    )
    stale = [record for record in records if record["stale_stage_gate_block"]]
    payload = {
        "all_pass": True,
        "blocked_count": len(records),
        "current_stage_claim_counts": {
            str(key): value for key, value in sorted(current_claim_counts.items(), key=lambda item: str(item[0]))
        },
        "old_stage_claim_counts": {
            str(key): value for key, value in sorted(old_claim_counts.items(), key=lambda item: str(item[0]))
        },
        "reason_counts": dict(reason_counts.most_common()),
        "stale_stage_gate_block_count": len(stale),
        "stale_stage_gate_blocks": stale,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
