#!/usr/bin/env python3
"""Report never-run sim cohorts without queueing or executing them."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import adaptive_controller
import lint_sim_contract


ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "system_v5/ops/never_run_cohorts.json"


def has_result(path: Path) -> bool:
    return adaptive_controller.find_result_file(path.stem) is not None


def main() -> int:
    rows = []
    family_counts: Counter[str] = Counter()
    bucket_counts: Counter[str] = Counter()
    debt_counts: Counter[str] = Counter()
    for path in sorted(adaptive_controller.PROBES.glob("sim_*.py")):
        if not path.is_file() or " 2" in path.name or has_result(path):
            continue
        family = adaptive_controller.sim_family(path.name)
        bucket = adaptive_controller.plan_bucket(path.name)
        violations = sorted({item["rule"] for item in lint_sim_contract.lint_sim(path)})
        family_counts[family] += 1
        bucket_counts[bucket] += 1
        for rule in violations or ["contract_clean"]:
            debt_counts[rule] += 1
        rows.append(
            {
                "sim": str(path.relative_to(ROOT)),
                "family": family,
                "bucket": bucket,
                "runner_class": adaptive_controller.runner_class_for(path),
                "contract_rules": violations,
            }
        )
    report = {
        "schema": "never_run_cohorts_v1",
        "mode": "audit_no_queue_mutation",
        "never_run_count": len(rows),
        "family_counts": dict(family_counts.most_common()),
        "bucket_counts": dict(bucket_counts),
        "contract_rule_counts": dict(debt_counts.most_common()),
        "rows": rows,
    }
    OUT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"never_run_count": len(rows), "top_families": dict(family_counts.most_common(10)), "path": str(OUT_PATH.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
