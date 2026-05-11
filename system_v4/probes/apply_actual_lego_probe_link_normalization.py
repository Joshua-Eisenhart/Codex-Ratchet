#!/usr/bin/env python3
"""Fill covered registry rows with their accepted probe/result links.

The coverage-label applier can clear the normalization queue.  Once that
happens, the registry itself must carry the accepted probe/result link instead
of relying on the transient queue overlay.  This script updates only rows whose
Current Coverage is already `covered` and whose accepted normalization target
has an existing local result.
"""

from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
REGISTRY_PATH = PROJECT_DIR / "system_v5" / "docs" / "17_actual_lego_registry.md"
NORMALIZATION_QUEUE_SCRIPT = SCRIPT_DIR / "actual_lego_normalization_queue.py"
OUT_PATH = RESULTS_DIR / "actual_lego_probe_link_normalization_applied.json"


def load_normalization_targets() -> dict[str, dict]:
    spec = importlib.util.spec_from_file_location("actual_lego_normalization_queue", NORMALIZATION_QUEUE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {NORMALIZATION_QUEUE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.NORMALIZATION_TARGETS


def result_name_for_probe(probe: str) -> str:
    stem = probe[:-3] if probe.endswith(".py") else probe
    if stem.startswith("sim_"):
        stem = stem[4:]
    return f"{stem}_results.json"


def update_table_row(line: str, targets: dict[str, dict]) -> tuple[str, dict | None]:
    if not line.startswith("| `"):
        return line, None
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if len(cells) < 11:
        return line, None
    lego_id = cells[0].strip("`")
    current_coverage = cells[8].strip("`")
    target = targets.get(lego_id)
    if current_coverage != "covered" or not target:
        return line, None
    probe = target.get("probe")
    if not probe:
        return line, None
    result_name = result_name_for_probe(probe)
    if not (RESULTS_DIR / result_name).exists():
        return line, None
    old_probe = cells[6]
    old_result = cells[7]
    new_probe = f"`{probe}`"
    new_result = f"`{result_name}`"
    if old_probe == new_probe and old_result == new_result:
        return line, None
    cells[6] = new_probe
    cells[7] = new_result
    return "| " + " | ".join(cells) + " |", {
        "lego_id": lego_id,
        "old_probe": old_probe.strip("`"),
        "new_probe": probe,
        "old_result": old_result.strip("`"),
        "new_result": result_name,
    }


def main() -> int:
    targets = load_normalization_targets()
    original = REGISTRY_PATH.read_text(encoding="utf-8").splitlines()
    rewritten = []
    changed = []
    for line in original:
        next_line, change = update_table_row(line, targets)
        rewritten.append(next_line)
        if change:
            changed.append(change)
    REGISTRY_PATH.write_text("\n".join(rewritten) + "\n", encoding="utf-8")
    payload = {
        "name": "actual_lego_probe_link_normalization_applied",
        "schema": "actual_lego_probe_link_normalization_applied.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "boundary": "source_probe_result_link_update_only_not_admission_or_promotion",
        "inputs": {
            "registry": str(REGISTRY_PATH.relative_to(PROJECT_DIR)),
            "normalization_targets": str(NORMALIZATION_QUEUE_SCRIPT.relative_to(PROJECT_DIR)),
        },
        "summary": {
            "changed_rows": len(changed),
            "promotion_allowed_count": 0,
        },
        "changed_rows": changed,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
