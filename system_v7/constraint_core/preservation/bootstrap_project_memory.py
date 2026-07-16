#!/usr/bin/env python3
"""Emit the minimum complete, machine-grounded project-memory snapshot."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def main() -> int:
    verification = subprocess.run(
        [sys.executable, str(ROOT / "preservation" / "verify_preservation.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if verification.returncode:
        print(verification.stdout or verification.stderr)
        print("PROJECT MEMORY REFUSED: preservation surface is stale or incomplete")
        return 1

    manifest = load("preservation/preservation_manifest.json")
    sims = load("reports/SIM_REGISTRATION_LEDGER.json")
    exceptional = load("reports/EXCEPTIONAL_NONASSOCIATIVE_MATH_STATE.json")
    basins = load("reports/ATTRACTOR_BASIN_STATE.json")
    manifold = load("ratchet/manifold_evidence/manifold_layer_state.json")
    julia = load("julia_canon/artifacts/python_cross_validation_receipt.json")
    direct = load("reports/DIRECT_RERUN_RECEIPTS.json")
    paths = load("reports/STANDALONE_PATH_AUDIT.json")

    snapshot = {
        "bundle": manifest["bundle"],
        "root": "CONSTRAINED_DISTINGUISHABILITY",
        "canon_rule": manifest["canon_rule"],
        "ratchet_drive": "a nonzero surviving entropy-geometry coface gradient; without it no tooth, DIG continues",
        "mss_rule": "packet/grammar/probe/budget-relative provisional antichain; always defeasible by a weaker survivor",
        "simulation_visibility": sims["counts"],
        "manifold": {
            "scientific_layers_admitted": manifold["scientific_manifold_layers_admitted"],
            "layer_state": [{"layer": row["layer"], "status": row["status"]} for row in manifold["layers"]],
        },
        "exceptional_nonassociative": {
            "state": exceptional["overall_state"],
            "forcing_link": exceptional["open_forcing_link"],
            "promotion_allowed": exceptional["promotion_allowed"],
        },
        "attractor_basins": {
            "state": basins["overall_state"],
            "fep_v1": basins["fep_known_unknown_audit_chain"]["v1_allocation_split"],
            "fep_v2": basins["fep_known_unknown_audit_chain"]["v2_engine_allocation"],
            "promotion_allowed": basins["promotion_allowed"],
        },
        "julia_exceptional_source": {
            "status": julia["status"],
            "all_cross_checks_pass": julia["all_pass"],
            "ratchet_admission": julia["ratchet_admission"],
        },
        "direct_reruns": {
            "fresh_pass_count": direct["fresh_pass_count"],
            "blocked_count": direct["blocked_count"],
            "blocked": [row for row in direct["runs"] if row["status"].startswith("BLOCKED")],
            "ratchet_admission_count": direct["ratchet_admission_count"],
            "standalone_path_repairs_pass": paths["all_portable_path_gates_pass"],
        },
        "lineage": {
            "restored_127_to_130_omissions": len(manifest["restored_artifacts"]),
            "all_restored_byte_identical": manifest["lineage_comparison"]["all_dropped_paths_restored_in_131"],
            "known_external_not_materialized": [row["lineage"] for row in manifest["known_external_not_materialized"]],
        },
        "required_human_reports": [
            "reports/EXCEPTIONAL_NONASSOCIATIVE_MATH_STATE.md",
            "reports/ATTRACTOR_BASIN_STATE.md",
            "ratchet/manifold_evidence/MANIFOLD_RATCHET_STATE_REPORT.md",
        ],
    }
    print("PROJECT_MEMORY_SNAPSHOT")
    print(json.dumps(snapshot, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
