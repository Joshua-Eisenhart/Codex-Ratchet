#!/usr/bin/env python3
"""Mechanical validator for the stage16x4 system-ID result."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


classification = "controller_audit"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "classical"
TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive independent parsing and mechanical result-contract validation",
    }
}
TOOL_INTEGRATION_DEPTH = {"python_json": "supportive"}

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
INPUT = HERE / "results" / "stage16x4_system_id_instrument_v0_results.json"
OUTPUT = HERE / "results" / "stage16x4_system_id_instrument_v0_validator_results.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    result = json.loads(INPUT.read_text())
    aggregate = result["aggregate"]
    source_hashes_match = all(
        (REPO / relative_path).is_file()
        and sha256(REPO / relative_path) == expected_hash
        for relative_path, expected_hash in result["source_hashes"].items()
    )
    checks = {
        "fenced_scratch_diagnostic": result["classification"] == "scratch_diagnostic"
        and result["promotion_allowed"] is False
        and result["formal_admission_allowed"] is False
        and result["stage_movement_allowed"] is False,
        "premise_boundary_blocks_emergence": result["premise_boundary"]["dual_ratchet_emergence_tested"] is False,
        "instrument_checks_all_true": all(result["instrument_checks"].values()),
        "candidate_checks_all_true": all(result["candidate_checks"].values()),
        "sixteen_macro_slots": aggregate["macro_slot_count"] == 16,
        "two_candidate_orientations": aggregate["candidate_orientation_count"] == 2,
        "sixty_four_beats_per_orientation": aggregate["beats_per_one_orientation"] == 64,
        "one_hundred_twenty_eight_models_only_because_two_candidates": aggregate["candidate_beat_model_count"] == 128,
        "all_rows_keep_one_source_sign": all(
            row["checks"]["four_beats_share_source_axis6_sign"] for row in result["stage_rows"]
        ),
        "pykoopman_full_distribution_stays_quarantined": result["package_fingerprint"]["pykoopman"]["full_distribution_admitted"] is False
        and result["package_fingerprint"]["pykoopman"]["package_distribution_contract_clean"] is False,
        "candidate_status_is_local_only": result["accepted_status_label"] == "passes local rerun",
        "blocked_consumers_present": len(result["blocked_consumers"]) >= 8,
        "all_authority_source_hashes_match_live_files": source_hashes_match,
        "result_all_pass": result["all_pass"] is True,
    }
    all_pass = all(checks.values())
    receipt = {
        "schema": "codex_ratchet.stage16x4_system_id_instrument.validator.v0",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "input": str(INPUT),
        "checks": checks,
        "all_pass": all_pass,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "Mechanical validation of a fenced local result only; no scientific or engine promotion.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
