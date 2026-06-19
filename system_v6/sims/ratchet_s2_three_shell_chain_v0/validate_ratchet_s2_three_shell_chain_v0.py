#!/usr/bin/env python3
"""Validate ratchet_s2_three_shell_chain_v0 result shape and gates."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "ratchet_s2_three_shell_chain_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
DEFAULT_RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = SIM_DIR / "results" / f"{SIM_ID}_validator_results.json"


def rel(path: Path) -> str:
    if not path.is_absolute():
        path = ROOT / path
    return str(path.relative_to(ROOT))


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    require(payload.get("schema_version") == "three_engine_sim_result_v1", errors, "schema_version mismatch")
    require(payload.get("sim_id") == SIM_ID, errors, "sim_id mismatch")
    require(payload.get("mode") == "RATCHETED", errors, "mode must be RATCHETED")
    require(payload.get("engine_contract", {}).get("mode") == "RATCHETED", errors, "engine_contract.mode must be RATCHETED")
    require(payload.get("engine_contract", {}).get("lanes") == ["julia", "jax"], errors, "engine_contract lanes must be julia,jax")
    require("pytorch" in payload.get("engine_contract", {}).get("omitted_lanes", {}), errors, "pytorch omission reason required")
    require(payload.get("classification") == "scratch_diagnostic", errors, "classification must be scratch_diagnostic")
    require(payload.get("promotion_allowed") is False, errors, "promotion_allowed must be false")
    require(payload.get("formal_admission") is False, errors, "formal_admission must be false")
    require(payload.get("formal_admission_allowed") is False, errors, "formal_admission_allowed must be false")
    require(payload.get("all_pass") is True, errors, "all_pass must be true")

    engines = as_dict(payload.get("engines"), "engines", errors)
    require(set(engines) == {"julia", "jax"}, errors, "engines must contain scoped julia and jax lanes only")
    for engine_name in ("julia", "jax"):
        engine = as_dict(engines.get(engine_name), f"engines.{engine_name}", errors)
        require(engine.get("ran") is True, errors, f"{engine_name} must be marked ran")
        require(engine.get("reads_peer_result") is False, errors, f"{engine_name} must not read peer result")
        require(bool(engine.get("source_path")), errors, f"{engine_name} source_path required")
        require(bool(engine.get("aligned_packages_load_bearing")), errors, f"{engine_name} aligned load-bearing packages required")

    lineage = as_dict(payload.get("parent_lineage"), "parent_lineage", errors)
    for name, commit in (("geo_union_rule_k_leaves_v0", "8a46c8627"), ("ratchet_s2_two_shell_flux_v0", "15b1d1899")):
        block = as_dict(lineage.get(name), f"parent_lineage.{name}", errors)
        require(block.get("commit") == commit, errors, f"{name} commit mismatch")
        for key in ("source", "result", "audit"):
            row = as_dict(block.get(key), f"parent_lineage.{name}.{key}", errors)
            require(bool(row.get("path")), errors, f"{name}.{key}.path required")
            require(bool(row.get("sha256")), errors, f"{name}.{key}.sha256 required")

    sequence = as_dict(payload.get("ratchet_sequence"), "ratchet_sequence", errors)
    step1 = as_dict(sequence.get("step1"), "ratchet_sequence.step1", errors)
    joint = as_dict(step1.get("exact_joint_object"), "step1.exact_joint_object", errors)
    weight_block = as_dict(joint.get("weight_block"), "step1.weight_block", errors)
    weights = as_dict(weight_block.get("weights"), "step1.weights", errors)
    require(weights.get("sum") == "1", errors, "weights must sum to 1")
    require(weights.get("eta_pi_over_12", {}).get("rho_sin_2eta") == "1/2", errors, "eta pi/12 rho mismatch")
    require(weights.get("eta_pi_over_6", {}).get("rho_sin_2eta") == "sqrt(3)/2", errors, "eta pi/6 rho mismatch")
    require(weights.get("eta_pi_over_4", {}).get("rho_sin_2eta") == "1", errors, "eta pi/4 rho mismatch")
    require(
        weight_block.get("equal_weight_subtlety", {}).get("arises_here") is False,
        errors,
        "equal-weight subtlety must be explicitly absent",
    )
    per_leaf = as_dict(joint.get("per_leaf_geometry"), "step1.per_leaf_geometry", errors)
    require(
        per_leaf.get("eta_pi_over_12", {}).get("connection_pullback", {}).get("phi_chi_basis", {}).get("dchi")
        == "sqrt(3)/2",
        errors,
        "eta pi/12 dchi coefficient mismatch",
    )
    require(
        per_leaf.get("eta_pi_over_6", {}).get("connection_pullback", {}).get("phi_chi_basis", {}).get("dchi") == "1/2",
        errors,
        "eta pi/6 dchi coefficient mismatch",
    )
    require(
        per_leaf.get("eta_pi_over_4", {}).get("connection_pullback", {}).get("phi_chi_basis", {}).get("dchi") == "0",
        errors,
        "eta pi/4 dchi coefficient must vanish",
    )

    step2 = as_dict(sequence.get("step2"), "ratchet_sequence.step2", errors)
    chain = as_dict(step2.get("flux_chain"), "step2.flux_chain", errors)
    require(chain.get("physical_chi_period_honoring_2_to_1_cover") == "pi", errors, "physical chi period must be pi")
    annuli = as_dict(chain.get("annuli"), "step2.annuli", errors)
    require(
        annuli.get("pi_over_12_to_pi_over_6", {}).get("flux_integral_physical_chi_period")
        == "pi*(-1/2 + sqrt(3)/2)",
        errors,
        "flux 12 mismatch",
    )
    require(
        annuli.get("pi_over_6_to_pi_over_4", {}).get("flux_integral_physical_chi_period") == "pi/2",
        errors,
        "flux 23 mismatch",
    )
    require(
        annuli.get("pi_over_12_to_pi_over_4_total", {}).get("flux_integral_physical_chi_period") == "sqrt(3)*pi/2",
        errors,
        "flux 13 mismatch",
    )
    additivity = as_dict(chain.get("chain_additivity"), "chain_additivity", errors)
    require(additivity.get("computed_by_sum_of_adjacent_fluxes") == "sqrt(3)*pi/2", errors, "chain sum mismatch")
    require(additivity.get("computed_by_direct_total_flux") == "sqrt(3)*pi/2", errors, "direct total mismatch")
    require(additivity.get("defect") == "0", errors, "chain defect must be zero")
    gaps = as_dict(chain.get("pairwise_holonomy_gaps"), "pairwise_holonomy_gaps", errors)
    require(gaps.get("gap_13_equals_gap_12_plus_gap_23") is True, errors, "pairwise holonomy gap additivity must pass")
    require(gaps.get("defect") == "0", errors, "holonomy gap defect must be zero")

    step3 = as_dict(sequence.get("step3"), "ratchet_sequence.step3", errors)
    quotient = as_dict(step3.get("quotient_rows"), "step3.quotient_rows", errors)
    require(quotient.get("flux_rows_survive") is True, errors, "flux rows must survive Z4 quotient")
    require(quotient.get("chain_additivity_survives") is True, errors, "chain additivity must survive Z4 quotient")
    require(quotient.get("global_phase_gaps", {}).get("gap_13") == "0", errors, "global phase gap 13 must be zero")
    require(quotient.get("alpha_generator_gaps", {}).get("gap_13") == "sqrt(3)*pi/2", errors, "alpha gap 13 mismatch")
    require(quotient.get("beta_generator_gaps", {}).get("gap_13") == "-sqrt(3)*pi/2", errors, "beta gap 13 mismatch")

    signatures = as_dict(payload.get("ratchet_signatures"), "ratchet_signatures", errors)
    path_specificity = as_dict(signatures.get("path_specificity"), "path_specificity", errors)
    require(path_specificity.get("agreement") is True, errors, "direct vs pairwise-then-extend must agree")
    require(
        path_specificity.get("expectation_source") == "8a46c8627:system_v6/sims/geo_union_rule_k_leaves_v0",
        errors,
        "path-specificity expectation source mismatch",
    )

    controls = as_dict(payload.get("controls"), "controls", errors)
    require(
        controls.get("identity_constraint_excludes_nothing", {}).get("byte_exact_on_exact_rows") is True,
        errors,
        "nothing-excluded control must be byte-exact",
    )
    wrong_weights = as_dict(controls.get("wrong_weights_union_equal_weights"), "wrong_weights_union_equal_weights", errors)
    require(wrong_weights.get("propagates_into_both_fluxes") is True, errors, "equal-weights defect must propagate into both fluxes")
    require(wrong_weights.get("annulus_12", {}).get("control_fired") is True, errors, "annulus 12 equal-weight control must fire")
    require(wrong_weights.get("annulus_23", {}).get("control_fired") is True, errors, "annulus 23 equal-weight control must fire")
    require(controls.get("wrong_order_stokes_orientation", {}).get("control_fired") is True, errors, "wrong orientation control must fire")
    require(controls.get("naive_joint_conditioning_fails", {}).get("pass") is True, errors, "naive P=0 control must pass")
    anchor = as_dict(controls.get("two_shell_anchor_pi_over_6_to_pi_over_4"), "two_shell_anchor", errors)
    require(anchor.get("byte_exact_under_stable_json") is True, errors, "two-shell anchor row must be byte-exact")
    require(anchor.get("source_commit") == "15b1d1899", errors, "two-shell anchor source commit mismatch")

    proofs = as_dict(payload.get("crossover_proofs"), "crossover_proofs", errors)
    for solver in ("z3", "cvc5"):
        row = as_dict(proofs.get(solver), f"crossover_proofs.{solver}", errors)
        require(row.get("ran") is True, errors, f"{solver} must run")
        require(row.get("load_bearing") is True, errors, f"{solver} must be load-bearing")
        require(row.get("verdict") == "unsat", errors, f"{solver} positive verdict must be unsat")
        require(row.get("erased_flip_detected") is True, errors, f"{solver} erased flip must be detected")
    julia_z3 = as_dict(proofs.get("julia_z3"), "crossover_proofs.julia_z3", errors)
    require(julia_z3.get("ran") is True, errors, "julia_z3 must run")
    require(julia_z3.get("load_bearing") is True, errors, "julia_z3 must be load-bearing")
    require(julia_z3.get("verdict") == "unsat", errors, "julia_z3 positive verdict must be unsat")
    require(julia_z3.get("erased_flip_detected") is True, errors, "julia_z3 erased flip must be detected")

    calls = payload.get("tool_calls")
    require(isinstance(calls, list) and len(calls) == 4, errors, "tool_calls must contain exactly four rows")
    if isinstance(calls, list):
        require([call.get("tool") for call in calls] == ["sympy", "z3", "cvc5", "Z3"], errors, "tool call order mismatch")
        require(all(call.get("load_bearing") is True for call in calls), errors, "all declared tool calls must be load-bearing")
    require(payload.get("claim_path_tools") == ["sympy", "z3", "cvc5", "Z3"], errors, "claim_path_tools mismatch")

    gates = as_dict(payload.get("build_gates"), "build_gates", errors)
    for gate in (
        "mode_declared_ratcheted",
        "ceilings_preserved",
        "parent_lineage_hashes_present",
        "k_leaf_rule_cited",
        "union_weights_exact",
        "per_leaf_geometry_computed",
        "flux_chain_additivity",
        "holonomy_gap_additivity",
        "z4_quotient_chain_survives",
        "path_specificity_agrees",
        "controls_fired",
        "smt_positive_and_erased_flip",
        "julia_result_loaded",
        "julia_source_hash_matches",
        "julia_reads_no_peer_result",
        "julia_engine_values_match_python_exact_rows",
        "julia_z3_positive_and_erased_flip",
        "one_to_one_tool_calls",
        "capability_receipts_present",
    ):
        require(gates.get(gate) is True, errors, f"gate {gate} must be true")

    divergence = as_dict(payload.get("divergence"), "divergence", errors)
    require(divergence.get("julia_authoritative") is True, errors, "divergence.julia_authoritative must be true")
    require(divergence.get("max_divergence") == 0.0, errors, "max_divergence must be 0.0")
    engine_values = as_dict(divergence.get("engine_values"), "divergence.engine_values", errors)
    if set(engine_values) == {"julia", "jax"}:
        require(engine_values["julia"] == engine_values["jax"], errors, "julia and jax values must match exactly")
    else:
        errors.append("divergence.engine_values must contain julia and jax")

    return errors


def main(argv: list[str]) -> int:
    result_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_RESULT
    if not result_path.is_absolute():
        result_path = ROOT / result_path
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    errors = validate(payload)
    out = {
        "ok": not errors,
        "result_json": rel(result_path),
        "validator": rel(Path(__file__)),
        "validated_mode": payload.get("mode"),
        "errors": errors,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    VALIDATOR_RESULT.parent.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
