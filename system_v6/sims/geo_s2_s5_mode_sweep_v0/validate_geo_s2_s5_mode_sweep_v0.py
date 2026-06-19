#!/usr/bin/env python3
"""Validate the S2/S5 RESTRICTED + QUOTIENTED mode-sweep packet."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s2_s5_mode_sweep_v0"
RESULT_PATH = ROOT / "system_v6" / "sims" / SIM_ID / "results" / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = ROOT / "system_v6" / "sims" / SIM_ID / "results" / f"{SIM_ID}_validator_results.json"


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    payload = load(RESULT_PATH)
    errors: list[str] = []
    require(errors, payload.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("mode_program", {}).get("executed_modes") == ["RESTRICTED", "QUOTIENTED"], "executed modes must be RESTRICTED and QUOTIENTED")
    require(errors, "RATCHETED" in payload.get("mode_program", {}).get("excluded_modes", {}), "RATCHETED exclusion must be explicit")
    engine_contract = payload.get("engine_contract", {})
    require(errors, engine_contract.get("mode") == "julia_canon_plus_jax_diagnostic", "engine mode must honestly be julia_canon_plus_jax_diagnostic")
    require(errors, engine_contract.get("lanes") == ["julia", "jax"], "engine lanes must be Julia + JAX only")
    require(errors, "pytorch" in engine_contract.get("omitted_lanes", {}), "PyTorch omission must be declared")
    require(errors, "pytorch" not in payload.get("engines", {}), "PyTorch engine record must not be present for this two-lane diagnostic")

    mode_rows = payload.get("mode_rows", {})
    s2 = mode_rows.get("S2", {})
    s5 = mode_rows.get("S5", {})
    require(errors, s2.get("RESTRICTED", {}).get("mode") == "RESTRICTED", "S2 restricted row missing mode tag")
    require(errors, s2.get("QUOTIENTED", {}).get("mode") == "QUOTIENTED", "S2 quotiented row missing mode tag")
    require(errors, s5.get("RESTRICTED", {}).get("mode") == "RESTRICTED", "S5 restricted row missing mode tag")
    require(errors, s5.get("QUOTIENTED", {}).get("mode") == "QUOTIENTED", "S5 quotiented row missing mode tag")

    narrowing = s2.get("RESTRICTED", {}).get("narrowing_signature", {})
    require(errors, narrowing.get("before_loop_count") == 5, "S2 before loop count must be 5")
    require(errors, narrowing.get("after_loop_count") == 2, "S2 restricted loop count must be 2")
    require(errors, narrowing.get("excluded_loop_count") == 3, "S2 excluded loop count must be 3")
    require(errors, narrowing.get("pass") is True, "S2 narrowing signature must pass")
    require(errors, s2.get("RESTRICTED", {}).get("nothing_excluded_control", {}).get("byte_exact_equal") is True, "S2 no-op restriction must be byte-exact")
    require(errors, s2.get("RESTRICTED", {}).get("maximal_restriction_control", {}).get("admissible_set_empty") is True, "S2 max restriction must report empty")

    descended = s2.get("QUOTIENTED", {}).get("descended_rows", {})
    require(errors, descended.get("F", {}).get("status") == "descends", "S2 F must descend")
    require(errors, descended.get("A", {}).get("status") == "does_not_descend", "S2 A must not descend")
    gauge_a = descended.get("A", {}).get("gauge_computation", {})
    gauge_f = descended.get("F", {}).get("gauge_computation", {})
    require(errors, gauge_a.get("computed_delta_A", {}).get("d_chi") == "alpha1", "G1 must compute nonzero delta-A d_chi=alpha1")
    require(errors, gauge_a.get("computed_delta_A_nonzero_sample_alpha_chi", {}).get("d_chi") == "1", "G1 must compute nonzero alpha=chi sample")
    require(errors, gauge_f.get("computed_delta_F_eta_chi") == "0", "G1 must compute symbolic delta-F=0")
    require(errors, gauge_f.get("F_invariant_symbolically") is True, "G1 must mark F invariant from computation")

    s5_summary = s5.get("RESTRICTED", {}).get("survival_summary", {})
    require(errors, "Ni_Pit_L" in s5_summary.get("excluded", []), "S5 restricted row must exclude Ni_Pit_L")
    require(errors, "Ni_Source_R" in s5_summary.get("survive_full", []), "S5 restricted row must preserve Ni_Source_R")
    require(errors, s5.get("RESTRICTED", {}).get("jaxopt_lineax_sidecar", {}).get("pass") is True, "S5 jaxopt/lineax sidecar must pass")

    after_matrix = s5.get("QUOTIENTED", {}).get("probe_family_separation_matrix_after", {})
    matrix = after_matrix.get("matrix", [])
    require(errors, len(matrix) == 8 and all(len(row) == 8 for row in matrix), "S5 quotient matrix must be 8x8")
    require(errors, after_matrix.get("collapsed_pairs") == [], "S5 quotient must report named collapsed pairs; expected none for this anchor")

    order_rows = payload.get("order_control_rows", {})
    require(errors, order_rows.get("S2", {}).get("N01_order_gap") == 0, "S2 order gap must be computed and equal 0 for visible eta-band constraint")
    require(errors, order_rows.get("S5", {}).get("N01_order_gap") == 0, "S5 order gap must be computed and equal 0 for visible z constraint")
    for stage in ("S2", "S5"):
        row = order_rows.get(stage, {})
        require(errors, isinstance(row.get("restrict_then_quotient_rows"), list) and row.get("restrict_then_quotient_rows"), f"{stage} restrict-then-quotient rows must be emitted")
        require(errors, isinstance(row.get("quotient_then_restrict_rows"), list) and row.get("quotient_then_restrict_rows"), f"{stage} quotient-then-restrict rows must be emitted")
        require(errors, row.get("restrict_then_quotient_count") == len(row.get("restrict_then_quotient_rows", [])), f"{stage} restrict-then-quotient count must come from emitted rows")
        require(errors, row.get("quotient_then_restrict_count") == len(row.get("quotient_then_restrict_rows", [])), f"{stage} quotient-then-restrict count must come from emitted rows")

    proofs = payload.get("crossover_proofs", {})
    require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 proof must be unsat")
    require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 proof must be unsat")
    require(errors, proofs.get("z3", {}).get("erased_flip_control_can_fail") is True, "z3 erased flip control must fail")
    require(errors, proofs.get("cvc5", {}).get("erased_flip_control_can_fail") is True, "cvc5 erased flip control must fail")

    build_gates = payload.get("build_gates", {})
    require(errors, bool(build_gates) and all(build_gates.values()), "all build gates must be true")
    require(errors, build_gates.get("julia_symbolics_gauge_mirror") is True, "Julia Symbolics gauge mirror gate must pass")
    addendum = payload.get("harden_addendum", {})
    require(errors, addendum.get("status") == "builder_hardening_verdicts_stand_pending_reaudit", "builder-hardening addendum status missing")
    for gap in ("G1", "G2", "G3"):
        require(errors, gap in addendum and "closed" in addendum.get(gap, ""), f"builder-hardening addendum must name {gap} closed")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")

    result = {
        "ok": not errors,
        "validator_ok": not errors,
        "declared_modes_ok": not errors,
        "sim_id": SIM_ID,
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "errors": errors,
    }
    VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
