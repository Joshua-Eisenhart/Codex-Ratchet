#!/usr/bin/env python3
"""Decompose blocked queue reasons into actionable sim contract sub-reasons."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import lint_sim_contract


ROOT = Path(__file__).resolve().parents[1]
BLOCKED_DIR = ROOT / "system_v4/probes/a2_state/queue/blocked"
OUT_PATH = ROOT / "system_v5/ops/blocked_reason_breakdown.json"


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def blocked_files() -> list[Path]:
    return sorted(path for path in BLOCKED_DIR.iterdir() if path.is_file() and ".json" in path.name)


def sim_path_from_record(record: dict[str, Any]) -> Path | None:
    raw = record.get("sim_path")
    if not isinstance(raw, str) or not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    return path


def contract_rules_for(path: Path | None) -> list[str]:
    if path is None or not path.exists():
        return ["missing_sim_path"]
    return sorted({violation["rule"] for violation in lint_sim_contract.lint_sim(path)})


def main() -> int:
    rows: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    subreason_counts: Counter[str] = Counter()
    by_blocked_reason: dict[str, Counter[str]] = defaultdict(Counter)

    for path in blocked_files():
        record = load_json(path)
        if record is None:
            continue
        blocked_reason = str(record.get("blocked_reason") or "unknown")
        sim_path = sim_path_from_record(record)
        subreasons = contract_rules_for(sim_path)
        if not subreasons:
            subreasons = ["contract_clean_or_not_static_lint_blocked"]
        reason_counts[blocked_reason] += 1
        for subreason in subreasons:
            subreason_counts[subreason] += 1
            by_blocked_reason[blocked_reason][subreason] += 1
        rows.append(
            {
                "blocked_file": str(path.relative_to(ROOT)),
                "blocked_reason": blocked_reason,
                "blocked_stage_claim": record.get("blocked_stage_claim"),
                "sim_path": str(sim_path.relative_to(ROOT)) if sim_path and sim_path.exists() else record.get("sim_path"),
                "subreasons": subreasons,
            }
        )

    wizard_rows = [row for row in rows if row["blocked_reason"] == "wizard_admission_blocked"]
    report = {
        "schema": "blocked_reason_breakdown_v1",
        "blocked_count": len(rows),
        "wizard_admission_blocked_count": len(wizard_rows),
        "all_rows_have_subreasons": all(bool(row["subreasons"]) for row in wizard_rows),
        "blocked_reasons": dict(reason_counts),
        "contract_subreasons": dict(subreason_counts),
        "by_blocked_reason": {key: dict(value) for key, value in by_blocked_reason.items()},
        "rows": rows,
    }
    OUT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("blocked_count", "wizard_admission_blocked_count", "all_rows_have_subreasons", "blocked_reasons", "contract_subreasons")}, indent=2))
    return 0 if report["all_rows_have_subreasons"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
