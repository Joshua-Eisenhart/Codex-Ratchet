#!/usr/bin/env python3
"""Packet-local validator for engine_readout_spinor_lift_v0."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "engine_readout_spinor_lift_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_PATH = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    result_path = Path(sys.argv[1]) if len(sys.argv) > 1 else RESULT_PATH
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    errors: list[str] = []

    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "bad schema")
    require(errors, payload.get("mode") == "FIELD", "mode must be FIELD")
    require(errors, payload.get("classification") == "scratch_diagnostic", "classification drift")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    require(errors, len(payload.get("strategy_rows", [])) == 16, "expected 16 strategy rows")
    require(errors, payload.get("values", {}).get("lift_separated_count") == 16, "all 16 lift analogs must separate")
    require(errors, payload.get("values", {}).get("lift_still_repeating_count") == 0, "no lift analog should repeat 720-vs-360")
    require(errors, payload.get("values", {}).get("parent_groups_split_by_lift") == 0, "parent slot groups must not be silently split")
    require(errors, payload.get("values", {}).get("state_count_word") == 8, "word state count must be 8")
    require(errors, payload.get("values", {}).get("state_count_double_720_lift") == 16, "lift double state count must be 16")

    controls = payload.get("controls", {})
    quotient = controls.get("quotient_erasure", {})
    phase = controls.get("phase_randomized", {})
    ref = controls.get("reference_state_independence", {})
    shuffle = controls.get("shuffled_word", {})
    require(errors, quotient.get("collapses_to_committed_repeat_result") is True, "quotient erasure did not collapse to parent")
    require(errors, quotient.get("all_density_sha256_repeat") is True, "density hashes did not repeat")
    require(errors, phase.get("kills_separation") is True, "phase-randomized control did not kill separation")
    require(errors, ref.get("all_references_separate_all_rows") is True, "reference independence check failed")
    require(errors, shuffle.get("copied_parent_control") is True, "shuffled-word parent control not preserved")

    sep_rows = payload.get("separation_table", {}).get("rows", [])
    require(errors, len(sep_rows) == 16, "separation table must contain 16 rows")
    for row in sep_rows:
        sid = row.get("strategy_id", "<missing>")
        require(errors, row.get("separates_720_from_360") is True, f"{sid} did not separate")
        require(errors, row.get("density_quotient_repeats") is True, f"{sid} density quotient did not repeat")
        require(errors, row.get("phase_randomized_repeats") is True, f"{sid} phase-randomized row did not repeat")

    for group in payload.get("distinguishability", {}).get("anti_collapse_group_rows", []):
        require(errors, group.get("lift_splits_parent_group") is False, "a parent anti-collapse group was split unexpectedly")
        require(errors, group.get("finding") == "still_indistinguishable", "anti-collapse group finding drift")

    proofs = payload.get("crossover_proofs", {})
    for key in ("z3", "cvc5", "julia_z3"):
        proof = proofs.get(key, {})
        require(errors, proof.get("ran") is True, f"{key} did not run")
        require(errors, proof.get("load_bearing") is True, f"{key} not load-bearing")
        require(errors, proof.get("verdict") == "unsat", f"{key} expected unsat")
        require(errors, proof.get("control_verdict") == "sat", f"{key} erased control expected sat")

    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))

    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    print(json.dumps({"ok": True, "result_json": str(result_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
