#!/usr/bin/env python3
"""Audit unlinked result JSONs in the sim inventory.

This is a controller/index hygiene audit. It does not promote any sim and does
not mutate git state.
"""

from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime
from typing import Any


CLASSIFICATION = "controller_index"
classification = CLASSIFICATION
divergence_log = (
    "Inventory hygiene audit for result JSONs that are counted by the sim "
    "inventory but not linked to an active source row. This separates expected "
    "controller/classical-mirror support surfaces from possible orphan result "
    "evidence."
)

LEGO_IDS = ["sim_inventory", "result_linkage", "cleanup_gate"]
PRIMARY_LEGO_IDS = ["sim_inventory", "result_linkage"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "load-bearing inventory/result parsing"},
    "pathlib": {"tried": True, "used": True, "reason": "load-bearing path existence and source matching"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_DIR = PROBE_DIR.parents[1]
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
INVENTORY_PATH = PROJECT_DIR / "system_v5" / "evidence" / "sim_inventory_index.json"
OUT_PATH = RESULT_DIR / "inventory_unlinked_result_audit_results.json"


def read_json(path: pathlib.Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return payload


def result_stem(rel_path: str) -> str:
    name = pathlib.Path(rel_path).name
    return name.removesuffix("_results.json").removeprefix("sim_")


def candidate_sources(stem: str) -> list[str]:
    names = [
        f"system_v4/probes/sim_{stem}.py",
        f"system_v4/probes/sim_integration_{stem}.py",
        f"system_v4/probes/{stem}.py",
        f"system_v4/probes/{stem}_sim.py",
        f"system_v4/probes/{stem}_investigation.py",
        f"system_v4/probes/sim_{stem}_probe.py",
        f"system_v4/probes/classical_doctrine_mirrors/sim_{stem}.py",
        f"system_v4/probes/classical_doctrine_mirrors/{stem}.py",
        f"system_v4/{stem}.py",
    ]
    return names


def classify(rel_path: str) -> dict[str, Any]:
    stem = result_stem(rel_path)
    source_candidates = candidate_sources(stem)
    existing_sources = [
        candidate for candidate in source_candidates if (PROJECT_DIR / candidate).exists()
    ]
    if rel_path.startswith("system_v4/probes/a2_state/sim_results/") and (
        stem.endswith("_audit")
        or stem in {
            "controller_alignment_audit",
            "lego_tool_reporting_audit",
            "migration_contract_audit",
            "probe_truth_audit",
            "repo_hygiene_audit",
            "runtime_hygiene_audit",
            "state_dir_ownership_audit",
            "system_hygiene_supervisor",
            "system_hygiene_repair",
        }
    ):
        bucket = "expected_controller_audit_surface"
    elif "/classical_doctrine_mirrors/sim_results/" in rel_path:
        bucket = "expected_classical_mirror_result"
    elif rel_path.startswith("system_v4/a2_state/sim_results/"):
        bucket = "legacy_a2_result_surface"
    elif existing_sources:
        bucket = "source_exists_index_link_gap"
    else:
        bucket = "possible_orphan_result"
    return {
        "result_path": rel_path,
        "stem": stem,
        "bucket": bucket,
        "existing_sources": existing_sources,
        "source_candidate_count": len(source_candidates),
    }


def run() -> dict[str, Any]:
    inventory = read_json(INVENTORY_PATH)
    samples = inventory.get("unlinked_result_samples", [])
    if not isinstance(samples, list):
        samples = []
    rows = [classify(str(path)) for path in samples]
    bucket_counts: dict[str, int] = {}
    for row in rows:
        bucket_counts[row["bucket"]] = bucket_counts.get(row["bucket"], 0) + 1
    possible_orphans = [row for row in rows if row["bucket"] == "possible_orphan_result"]
    source_link_gaps = [row for row in rows if row["bucket"] == "source_exists_index_link_gap"]
    all_pass = not possible_orphans and not source_link_gaps
    return {
        "name": "sim_inventory_unlinked_result_audit",
        "generated_at": datetime.now(UTC).isoformat(),
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "inventory_path": str(INVENTORY_PATH.relative_to(PROJECT_DIR)),
        "sample_count": len(rows),
        "bucket_counts": bucket_counts,
        "rows": rows,
        "summary": {
            "all_pass": all_pass,
            "sample_count": len(rows),
            "possible_orphan_count": len(possible_orphans),
            "source_link_gap_count": len(source_link_gaps),
            "bucket_counts": bucket_counts,
            "claim_ceiling": "inventory_hygiene_only",
            "recommendation": "retool" if not all_pass else "keep",
            "scope_note": divergence_log,
        },
    }


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = run()
    OUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("SIM INVENTORY UNLINKED RESULT AUDIT")
    print(f"ALL PASS: {result['summary']['all_pass']}")
    print(f"SAMPLES: {result['summary']['sample_count']}")
    print(f"POSSIBLE ORPHANS: {result['summary']['possible_orphan_count']}")
    print(f"SOURCE LINK GAPS: {result['summary']['source_link_gap_count']}")


if __name__ == "__main__":
    main()
