#!/usr/bin/env python3
"""Validate the S3/S4 RESTRICTED + QUOTIENTED mode-sweep packet."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s3_s4_mode_sweep_v0"
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
    require(errors, "system_v6/sims/geo_s3_density_observable_v0/results/geo_s3_density_observable_v0_envelope_results.json" in payload.get("parent_lineage", {}), "S3 parent lineage missing")
    require(errors, "system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json" in payload.get("parent_lineage", {}), "S4 parent lineage missing")

    engine_contract = payload.get("engine_contract", {})
    require(errors, engine_contract.get("mode") == "julia_canon_plus_jax_diagnostic", "engine mode must be julia_canon_plus_jax_diagnostic")
    require(errors, engine_contract.get("lanes") == ["julia", "jax"], "engine lanes must be Julia + JAX only")
    require(errors, "pytorch" in engine_contract.get("omitted_lanes", {}), "PyTorch omission must be declared")
    require(errors, "pytorch" not in payload.get("engines", {}), "PyTorch engine record must be absent")

    mode_rows = payload.get("mode_rows", {})
    s3 = mode_rows.get("S3", {})
    s4 = mode_rows.get("S4", {})
    require(errors, s3.get("RESTRICTED", {}).get("mode") == "RESTRICTED", "S3 restricted mode tag missing")
    require(errors, s3.get("QUOTIENTED", {}).get("mode") == "QUOTIENTED", "S3 quotiented mode tag missing")
    require(errors, s4.get("RESTRICTED", {}).get("mode") == "RESTRICTED", "S4 restricted mode tag missing")
    require(errors, s4.get("QUOTIENTED", {}).get("mode") == "QUOTIENTED", "S4 quotiented mode tag missing")

    s3_restricted = s3.get("RESTRICTED", {})
    narrowing = s3_restricted.get("finite_grid_narrowing", {})
    require(errors, narrowing.get("before_grid_count") == 27, "S3 finite grid before count must be 27")
    require(errors, narrowing.get("after_shell_count") == 6, "S3 fixed-purity shell count must be 6")
    require(errors, narrowing.get("excluded_count") == 21, "S3 excluded count must be 21")
    require(errors, narrowing.get("pass") is True, "S3 narrowing must pass")
    require(errors, s3_restricted.get("nothing_excluded_control", {}).get("byte_exact_equal") is True, "S3 nothing-excluded control must be byte-exact")
    require(errors, s3_restricted.get("everything_excluded_control", {}).get("admissible_set_empty") is True, "S3 everything-excluded control must be empty")
    require(errors, s3_restricted.get("born_fields_on_restricted_set", {}).get("range_on_shell_for_unit_n") == ["1/4", "3/4"], "S3 Born range must narrow")
    require(errors, s3_restricted.get("trace_distance_fidelity_on_restricted_set", {}).get("antipodal_shell_pair", {}).get("D") == "1/2", "S3 restricted trace distance must be 1/2")
    require(errors, s3_restricted.get("trace_distance_fidelity_on_restricted_set", {}).get("antipodal_shell_pair", {}).get("F") == "3/4", "S3 restricted fidelity must be 3/4")

    descent = s3.get("QUOTIENTED", {}).get("observable_descent_tests", {})
    require(errors, descent.get("Z_measurement", {}).get("descends") is True, "z measurement must descend")
    require(errors, descent.get("X_measurement", {}).get("descends") is False, "x measurement must not descend")
    require(errors, descent.get("Y_measurement", {}).get("descends") is False, "y measurement must not descend")
    require(errors, s3.get("QUOTIENTED", {}).get("quotient_dimension") == 1, "S3 z quotient dimension must be 1")

    s4_restricted = s4.get("RESTRICTED", {})
    s4_rows = s4_restricted.get("operator_preservation_rows", {})
    require(errors, s4_restricted.get("preserve_all_shell") == ["R_x", "R_z"], "S4 restricted shell preservers must be R_x/R_z")
    require(errors, s4_restricted.get("leak") == ["D_z", "D_x"], "S4 restricted shell leakers must be D_z/D_x")
    require(errors, s4_rows.get("D_z", {}).get("leak_count", 0) > 0, "D_z must leak generic shell points")
    require(errors, s4_rows.get("D_x", {}).get("leak_count", 0) > 0, "D_x must leak generic shell points")
    require(errors, s4_rows.get("R_x", {}).get("preserves_fixed_purity_shell") is True, "R_x must preserve shell")
    require(errors, s4_rows.get("R_z", {}).get("preserves_fixed_purity_shell") is True, "R_z must preserve shell")
    require(errors, s4_restricted.get("nothing_excluded_control", {}).get("byte_exact_equal") is True, "S4 no-op control must be byte-exact")

    s4_quotiented = s4.get("QUOTIENTED", {})
    qrows = s4_quotiented.get("operator_well_definedness_rows", {})
    require(errors, s4_quotiented.get("descended_operators") == ["D_z", "D_x", "R_z"], "S4 descended operators must be D_z/D_x/R_z")
    require(errors, s4_quotiented.get("excluded_operators") == ["R_x"], "S4 R_x must be excluded on z quotient")
    require(errors, qrows.get("R_x", {}).get("excluded_on_quotient") is True, "R_x branch mortality missing")
    require(errors, "different quotient outputs" in (qrows.get("R_x", {}).get("branch_mortality_reason") or ""), "R_x branch mortality reason missing")
    require(errors, "terrain-generator distinguishability" in s4_quotiented.get("terrain_56_56_context", {}).get("honest_boundary", ""), "terrain/operator boundary must be explicit")

    order = payload.get("order_control_rows", {})
    require(errors, order.get("S3", {}).get("N01_order_gap") == 0, "S3 order gap must be 0")
    require(errors, order.get("S4", {}).get("N01_order_gap") == 2, "S4 order gap must be 2")
    for stage in ("S3", "S4"):
        row = order.get(stage, {})
        require(errors, isinstance(row.get("restrict_then_quotient_rows"), list), f"{stage} restrict-then-quotient rows missing")
        require(errors, isinstance(row.get("quotient_then_restrict_rows"), list), f"{stage} quotient-then-restrict rows missing")
        require(errors, row.get("restrict_then_quotient_count") == len(row.get("restrict_then_quotient_rows", [])), f"{stage} restrict count must match rows")
        require(errors, row.get("quotient_then_restrict_count") == len(row.get("quotient_then_restrict_rows", [])), f"{stage} quotient count must match rows")

    proofs = payload.get("crossover_proofs", {})
    require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 proof must be unsat")
    require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 proof must be unsat")
    require(errors, proofs.get("z3", {}).get("erased_flip_control_can_fail") is True, "z3 erased flip control must fail")
    require(errors, proofs.get("cvc5", {}).get("erased_flip_control_can_fail") is True, "cvc5 erased flip control must fail")

    build_gates = payload.get("build_gates", {})
    require(errors, bool(build_gates) and all(build_gates.values()), "all build gates must be true")
    require(errors, build_gates.get("julia_symbolics_z3_mirror") is True, "Julia Symbolics/Z3 mirror gate must pass")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    addendum = payload.get("builder_hardening_addendum", {})
    require(errors, addendum.get("status") == "closed_caveat_machinery_replicated_from_geo_s2_s5_mode_sweep_v0", "builder hardening addendum status missing")

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
