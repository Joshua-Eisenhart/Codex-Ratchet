#!/usr/bin/env python3
"""Validate the S6/S7 RESTRICTED + QUOTIENTED mode-sweep packet."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s6_s7_mode_sweep_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_PATH = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = SIM_DIR / "results" / f"{SIM_ID}_validator_results.json"
S6_PARENT = ROOT / "system_v6" / "sims" / "geo_s6_stacked_flows_hopf_v0" / "results" / "geo_s6_stacked_flows_hopf_v0_envelope_results.json"
S7_PARENT = ROOT / "system_v6" / "sims" / "geo_s7_discrete_refinement_v0" / "results" / "geo_s7_discrete_refinement_v0_envelope_results.json"


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    if not RESULT_PATH.exists():
        errors.append(f"missing result: {RESULT_PATH.relative_to(ROOT)}")
        result = {
            "ok": False,
            "validator_ok": False,
            "declared_modes_ok": False,
            "sim_id": SIM_ID,
            "result_path": str(RESULT_PATH.relative_to(ROOT)),
            "errors": errors,
        }
        VALIDATOR_RESULT.parent.mkdir(parents=True, exist_ok=True)
        VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    payload = load(RESULT_PATH)
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version drift")
    require(errors, payload.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    require(errors, payload.get("mode_program", {}).get("executed_modes") == ["RESTRICTED", "QUOTIENTED"], "executed modes must be RESTRICTED and QUOTIENTED")
    require(errors, "RATCHETED" in payload.get("mode_program", {}).get("excluded_modes", {}), "RATCHETED exclusion must be explicit")

    parent_lineage = payload.get("parent_lineage", {})
    require(errors, str(S6_PARENT.relative_to(ROOT)) in parent_lineage, "S6 parent lineage missing")
    require(errors, str(S7_PARENT.relative_to(ROOT)) in parent_lineage, "S7 parent lineage missing")

    engine_contract = payload.get("engine_contract", {})
    require(errors, engine_contract.get("mode") == "julia_canon_plus_jax_diagnostic", "engine mode must be standard Julia + JAX diagnostic")
    require(errors, engine_contract.get("lanes") == ["julia", "jax"], "engine lanes must be Julia + JAX")
    require(errors, "pytorch" in engine_contract.get("omitted_lanes", {}), "PyTorch omission must be declared")
    require(errors, "pytorch" not in payload.get("engines", {}), "PyTorch engine record must be absent")
    require(errors, isinstance(payload.get("engines", {}).get("jax"), dict), "JAX engine record must be present as an object")
    shape_receipt = payload.get("shape_only_repair_receipt", {})
    require(errors, shape_receipt.get("computed_rows_preserved") is True, "shape-only repair must preserve computed row hashes")
    for pair in shape_receipt.get("preserved_subtree_hash_pairs", []):
        require(errors, pair.get("hash_equal") is True, f"{pair.get('subtree')} hash must be preserved")

    mode_rows = payload.get("mode_rows", {})
    s6 = mode_rows.get("S6", {})
    s7 = mode_rows.get("S7", {})
    require(errors, s6.get("RESTRICTED", {}).get("mode") == "RESTRICTED", "S6 restricted mode tag missing")
    require(errors, s6.get("QUOTIENTED", {}).get("mode") == "QUOTIENTED", "S6 quotiented mode tag missing")
    require(errors, s7.get("RESTRICTED", {}).get("mode") == "RESTRICTED", "S7 restricted mode tag missing")
    require(errors, s7.get("QUOTIENTED", {}).get("mode") == "QUOTIENTED", "S7 quotiented mode tag missing")

    s6_restricted = s6.get("RESTRICTED", {})
    narrowing = s6_restricted.get("narrowing_signature", {})
    require(errors, narrowing.get("before_eta_row_count") == 40, "S6 before eta-row count must be 40")
    require(errors, narrowing.get("after_eta_row_count") == 16, "S6 shell-band count must be 16")
    require(errors, narrowing.get("excluded_eta_row_count") == 24, "S6 excluded count must be 24")
    require(errors, narrowing.get("before_class_counts") == {"cross_shell": 10, "leave_foliation": 25, "projected_shell_preserve_but_Hopf_leave": 5}, "S6 parent class counts drift")
    require(errors, narrowing.get("after_class_counts") == {"cross_shell": 4, "leave_foliation": 10, "projected_shell_preserve_but_Hopf_leave": 2}, "S6 restricted class counts drift")
    require(errors, narrowing.get("surviving_classes") == ["cross_shell", "leave_foliation", "projected_shell_preserve_but_Hopf_leave"], "S6 surviving classes drift")
    require(errors, narrowing.get("pass") is True, "S6 narrowing must pass")
    require(errors, s6_restricted.get("nothing_excluded_control", {}).get("byte_exact_equal") is True, "S6 no-op restriction must be byte-exact")

    s6_q = s6.get("QUOTIENTED", {})
    class_rows = s6_q.get("class_level_well_definedness", {})
    require(errors, class_rows.get("projected_shell_preserve_but_Hopf_leave", {}).get("descends") is True, "S6 projected preserve class must descend")
    require(errors, class_rows.get("cross_shell", {}).get("descends") is False, "S6 cross-shell class must be excluded")
    require(errors, class_rows.get("leave_foliation", {}).get("descends") is False, "S6 leave-foliation class must be excluded")
    require(errors, sorted(s6_q.get("descended_classes", [])) == ["projected_shell_preserve_but_Hopf_leave"], "S6 descended class list drift")
    require(errors, sorted(s6_q.get("excluded_classes", [])) == ["cross_shell", "leave_foliation"], "S6 excluded class list drift")

    s7_restricted = s7.get("RESTRICTED", {})
    reduced = s7_restricted.get("reduced_grid_reruns", {})
    require(errors, reduced.get("kept_N_values") == [8, 16, 32], "S7 restricted kept N values drift")
    require(errors, reduced.get("excluded_N_values") == [2, 4, 64], "S7 restricted excluded N values drift")
    require(errors, reduced.get("cover_honored_all_rows") is True, "S7 restricted 2:1 cover must hold")
    require(errors, reduced.get("area_rows_count") == 21, "S7 restricted area row count drift")
    require(errors, reduced.get("holonomy_rows_count") == 21, "S7 restricted holonomy row count drift")
    require(errors, reduced.get("flux_stokes_rows_count") == 27, "S7 restricted flux/Stokes row count drift")
    require(errors, s7_restricted.get("nothing_excluded_control", {}).get("byte_exact_equal") is True, "S7 no-op restriction must be byte-exact")

    s7_q = s7.get("QUOTIENTED", {})
    q_rows = {row.get("N"): row for row in s7_q.get("grid_quotient_admissibility_rows", [])}
    for n in [8, 16, 32, 64]:
        require(errors, q_rows.get(n, {}).get("admits_lens_quotient") is True, f"S7 N={n} must admit quotient")
    for n in [3, 5, 6, 10]:
        require(errors, q_rows.get(n, {}).get("admits_lens_quotient") is False, f"S7 N={n} must fail quotient honestly")
        require(errors, q_rows.get(n, {}).get("failure_kind") == "incommensurate_with_lens_order", f"S7 N={n} failure kind drift")
    require(errors, s7_q.get("lens_order") == 4, "S7 lens order must be 4")

    order = payload.get("order_control_rows", {})
    require(errors, order.get("S6", {}).get("N01_order_gap") == 0, "S6 order gap must be 0")
    require(errors, order.get("S7", {}).get("N01_order_gap") == 0, "S7 order gap must be 0")
    for stage in ("S6", "S7"):
        row = order.get(stage, {})
        require(errors, isinstance(row.get("restrict_then_quotient_rows"), list) and row.get("restrict_then_quotient_rows"), f"{stage} restrict-then-quotient rows missing")
        require(errors, isinstance(row.get("quotient_then_restrict_rows"), list) and row.get("quotient_then_restrict_rows"), f"{stage} quotient-then-restrict rows missing")
        require(errors, row.get("restrict_then_quotient_count") == len(row.get("restrict_then_quotient_rows", [])), f"{stage} restrict count mismatch")
        require(errors, row.get("quotient_then_restrict_count") == len(row.get("quotient_then_restrict_rows", [])), f"{stage} quotient count mismatch")

    proofs = payload.get("crossover_proofs", {})
    require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 proof must be unsat")
    require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 proof must be unsat")
    require(errors, proofs.get("z3", {}).get("erased_flip_control_can_fail") is True, "z3 erased flip control must fail")
    require(errors, proofs.get("cvc5", {}).get("erased_flip_control_can_fail") is True, "cvc5 erased flip control must fail")

    build_gates = payload.get("build_gates", {})
    require(errors, bool(build_gates) and all(build_gates.values()), "all build gates must be true")
    require(errors, build_gates.get("julia_symbolics_z3_mirror") is True, "Julia Symbolics/Z3 mirror gate must pass")
    require(errors, len(payload.get("tool_calls", [])) == len(payload.get("TOOL_MANIFEST", {})), "one-to-one tool_calls/TOOL_MANIFEST mismatch")
    require(errors, "fixture" not in json.dumps(payload).lower(), "fixture wording must be absent")

    result = {
        "ok": not errors,
        "validator_ok": not errors,
        "declared_modes_ok": not errors,
        "sim_id": SIM_ID,
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "errors": errors,
    }
    VALIDATOR_RESULT.parent.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
