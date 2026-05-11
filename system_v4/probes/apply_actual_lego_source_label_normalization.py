#!/usr/bin/env python3
"""Apply accepted machine-backed coverage labels to the markdown lego registry.

This is intentionally narrow: it only updates the Current Coverage column for
rows named in the normalization ledger as machine-covered and awaiting markdown
acceptance.  It does not change admission status, stage gates, notes, or result
classification.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
LEDGER_PATH = RESULTS_DIR / "actual_lego_source_label_normalization_ledger.json"
REGISTRY_PATH = PROJECT_DIR / "system_v5" / "docs" / "17_actual_lego_registry.md"
OUT_PATH = RESULTS_DIR / "actual_lego_source_label_normalization_applied.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def update_table_row(line: str, updates: dict[str, str]) -> tuple[str, dict | None]:
    if not line.startswith("| `"):
        return line, None
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if len(cells) < 11:
        return line, None
    lego_id = cells[0].strip("`")
    if lego_id not in updates:
        return line, None
    old_value = cells[8]
    new_value = f"`{updates[lego_id]}`"
    if old_value == new_value:
        return line, None
    cells[8] = new_value
    return "| " + " | ".join(cells) + " |", {
        "lego_id": lego_id,
        "old_current_coverage": old_value.strip("`"),
        "new_current_coverage": updates[lego_id],
    }


def main() -> int:
    ledger = read_json(LEDGER_PATH)
    updates = {
        row["lego_id"]: row["proposed_markdown_coverage"]
        for row in ledger.get("rows", [])
        if row.get("lego_id")
        and row.get("requires_human_markdown_acceptance") is True
        and row.get("result_all_pass") is True
        and row.get("proposed_markdown_coverage") == "covered"
    }
    original = REGISTRY_PATH.read_text(encoding="utf-8").splitlines()
    changed: list[dict] = []
    rewritten: list[str] = []
    for line in original:
        next_line, change = update_table_row(line, updates)
        rewritten.append(next_line)
        if change:
            changed.append(change)

    missing = sorted(set(updates) - {change["lego_id"] for change in changed})
    REGISTRY_PATH.write_text("\n".join(rewritten) + "\n", encoding="utf-8")
    payload = {
        "name": "actual_lego_source_label_normalization_applied",
        "schema": "actual_lego_source_label_normalization_applied.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "boundary": "markdown_coverage_label_update_only_not_admission_or_promotion",
        "inputs": {
            "ledger": str(LEDGER_PATH.relative_to(PROJECT_DIR)),
            "registry": str(REGISTRY_PATH.relative_to(PROJECT_DIR)),
        },
        "summary": {
            "ledger_update_candidates": len(updates),
            "changed_rows": len(changed),
            "unchanged_or_missing_rows": len(missing),
            "promotion_allowed_count": 0,
        },
        "changed_rows": changed,
        "unchanged_or_missing_lego_ids": missing,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
