#!/usr/bin/env python3
"""Validate ratchet_g2_family_v0 result shape and bounded math gates."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "ratchet_g2_family_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
DEFAULT_RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = SIM_DIR / "results" / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
EXPECTED_PARENTS = {
    "geo_s10_g2_family_v0",
    "ratchet_s1_single_shell_pilot_v0",
    "ratchet_s2_two_shell_flux_v0",
    "ratchet_s6_terrain_operator_shell_v0",
}


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
    require(payload.get("classification") == "scratch_diagnostic", errors, "classification must be scratch_diagnostic")
    require(payload.get("promotion_allowed") is False, errors, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, errors, "formal_admission_allowed must be false")
    require(payload.get("all_pass") is True, errors, "all_pass must be true")

    parents = as_dict(payload.get("parent_lineage"), "parent_lineage", errors)
    require(set(parents) == EXPECTED_PARENTS, errors, "parent_lineage must contain only the expected prerequisite packets")
    for name in EXPECTED_PARENTS:
        parent = as_dict(parents.get(name), f"parent_lineage.{name}", errors)
        require(bool(parent.get("committed_tree")), errors, f"{name} committed_tree missing")
        require(bool(parent.get("committed_commit")), errors, f"{name} committed_commit missing")
        require(bool(parent.get("envelope_sha256")), errors, f"{name} envelope_sha256 missing")
        require(bool(parent.get("top_source_sha256")), errors, f"{name} top_source_sha256 missing")
    geo_parent = as_dict(parents.get("geo_s10_g2_family_v0"), "geo_s10_g2_family_v0 parent", errors)
    require(str(geo_parent.get("committed_commit", "")).startswith("77a4f5d19"), errors, "geo_s10_g2_family_v0 parent commit must start with 77a4f5d19")

    s10 = as_dict(payload.get("s10_hash_checks"), "s10_hash_checks", errors)
    require(s10.get("compact_derivation_matrix_sha256_match") is True, errors, "compact carrier hash mismatch against S10")
    require(s10.get("split_derivation_matrix_sha256_match") is True, errors, "split carrier hash mismatch against S10")

    sequence = as_dict(payload.get("ratchet_sequence"), "ratchet_sequence", errors)
    step0 = as_dict(sequence.get("step0_free_carrier"), "step0_free_carrier", errors)
    compact_der = as_dict(step0.get("compact_derivation"), "compact_derivation", errors)
    split_der = as_dict(step0.get("split_derivation"), "split_derivation", errors)
    require(compact_der.get("nullity_dim_der") == 14, errors, "compact Der dim must be recomputed as 14")
    require(compact_der.get("rank") == 50, errors, "compact derivation rank must be 50")
    require(split_der.get("nullity_dim_der") == 14, errors, "split Der dim must be recomputed as 14")
    require(split_der.get("rank") == 50, errors, "split derivation rank must be 50")

    step1 = as_dict(sequence.get("step1_stabilizer_constraint"), "step1_stabilizer_constraint", errors)
    stab = as_dict(step1.get("stabilizer"), "stabilizer", errors)
    require(stab.get("constraint_rank_on_derivation_basis") == 6, errors, "compact stabilizer constraint rank must be 6")
    require(stab.get("stabilizer_dim") == 8, errors, "compact stabilizer dim must be 8")
    require(stab.get("coset_dim") == 6, errors, "compact coset dim must be 6")
    require(stab.get("closure_under_commutator") is True, errors, "compact stabilizer must close under commutator")
    require(step1.get("narrowing_signature") == "14 -> 8", errors, "narrowing signature mismatch")

    branch = as_dict(sequence.get("step2_branching"), "step2_branching", errors)
    rep7 = as_dict(branch.get("rep_7"), "rep_7", errors)
    rep14 = as_dict(branch.get("rep_14"), "rep_14", errors)
    rep27 = as_dict(branch.get("rep_27"), "rep_27", errors)
    require(rep7.get("dimension_sum") == 7, errors, "rep7 branch dims must sum to 7")
    require(rep7.get("after") == {"1": 1, "3": 3, "3bar": 3}, errors, "rep7 branch table mismatch")
    require(rep14.get("dimension_sum") == 14, errors, "rep14 branch dims must sum to 14")
    require(rep14.get("after") == {"8": 8, "3": 3, "3bar": 3}, errors, "rep14 branch table mismatch")
    require(rep27.get("dimension_sum") == 27, errors, "rep27 branch dims must sum to 27")
    require(rep27.get("after") == {"singlet_tracefree": 1, "3": 3, "3bar": 3, "6": 6, "6bar": 6, "8": 8}, errors, "rep27 branch table mismatch")
    residuals = as_dict(branch.get("projector_residuals"), "projector_residuals", errors)
    require(all(residuals.values()), errors, "compact projectors must pass idempotency/orthogonality/sum checks")
    raw27 = as_dict(rep27.get("raw_symmetric_projector_ranks"), "rep27.raw_symmetric_projector_ranks", errors)
    require(raw27.get("3x3bar_trace_in_raw") is True, errors, "rep27 trace row must be computed inside 3x3bar raw rank")

    split = as_dict(sequence.get("step3_split_family_fork"), "step3_split_family_fork", errors)
    require(split.get("split_trace_zero_signature") == {"negative": 4, "positive": 3, "zero": 0}, errors, "split trace-zero signature drift")
    rows = as_dict(split.get("rows"), "split rows", errors)
    pos = as_dict(rows.get("spacelike_positive_e1"), "split positive row", errors)
    neg = as_dict(rows.get("timelike_negative_e4"), "split negative row", errors)
    null = as_dict(rows.get("null_e1_plus_e4"), "split null row", errors)
    require(pos.get("u_dot_u") == 1 and pos.get("stabilizer_dim") == 8, errors, "split positive stabilizer row mismatch")
    require("su(2,1)" in str(pos.get("derived_stabilizer_label")), errors, "split positive label must be su(2,1)/su(1,2)")
    require(neg.get("u_dot_u") == -1 and neg.get("stabilizer_dim") == 8, errors, "split negative stabilizer row mismatch")
    require("sl(3,R)" in str(neg.get("derived_stabilizer_label")), errors, "split negative label must be sl(3,R)")
    require(null.get("u_dot_u") == 0 and null.get("stabilizer_dim") == 8, errors, "split null stabilizer dimension row mismatch")
    require("nonreductive" in str(null.get("derived_stabilizer_label")), errors, "split null label must stay nonreductive/deferred")
    require(pos.get("compact_su3_label_copied") is False and neg.get("compact_su3_label_copied") is False, errors, "split labels must not copy compact SU(3)")

    path = as_dict(payload.get("path_specificity"), "path_specificity", errors)
    branch_first = as_dict(path.get("branch_then_stabilize"), "branch_then_stabilize", errors)
    require(path.get("compact_pipelines_agree") is True, errors, "compact path-specificity pipelines must agree")
    require(path.get("compact_order_gap") == 0, errors, "compact path-specificity order gap must be zero")
    require(branch_first.get("stabilizer_dim") == 8, errors, "branch-then-stabilize dim must be 8")
    require(branch_first.get("span_equal_to_stabilize_then_branch") is True, errors, "branch/stabilizer spans must agree")

    signatures = as_dict(payload.get("ratchet_signatures"), "ratchet_signatures", errors)
    narrowing = as_dict(signatures.get("narrowing"), "ratchet_signatures.narrowing", errors)
    alteration = as_dict(signatures.get("alteration"), "ratchet_signatures.alteration", errors)
    sig_path = as_dict(signatures.get("path_specificity"), "ratchet_signatures.path_specificity", errors)
    fork = as_dict(signatures.get("family_fork"), "ratchet_signatures.family_fork", errors)
    require(narrowing.get("computed") is True and narrowing.get("signature") == "14 -> 8", errors, "ratchet narrowing signature missing")
    require(alteration.get("computed") is True, errors, "ratchet alteration signature missing")
    require(sig_path.get("computed") is True and sig_path.get("compact_order_gap") == 0, errors, "ratchet path-specificity signature missing")
    require(fork.get("computed") is True and fork.get("compact_label") == "su(3)", errors, "ratchet family fork signature missing")

    controls = as_dict(payload.get("controls"), "controls", errors)
    wrong = as_dict(controls.get("wrong_unit"), "wrong_unit", errors)
    sign = as_dict(controls.get("sign_flipped_structure_constants"), "sign_flipped_structure_constants", errors)
    perm = as_dict(controls.get("permuted_projector"), "permuted_projector", errors)
    nothing = as_dict(controls.get("nothing_excluded"), "nothing_excluded", errors)
    require(wrong.get("construction_rejected") is True and wrong.get("control_fired") is True, errors, "wrong-unit control must reject/degenerated row")
    require(sign.get("breaks_Der14") is True and sign.get("derivation", {}).get("nullity_dim_der") == 3, errors, "sign-flipped control must break Der=14 to 3")
    require(perm.get("breaks_dim_sum") is True and perm.get("control_fired") is True, errors, "permuted-projector control must break dim sum")
    require(nothing.get("byte_exact") is True and nothing.get("der_dim_after") == 14, errors, "nothing-excluded control must leave Der intact")

    proofs = as_dict(payload.get("crossover_proofs"), "crossover_proofs", errors)
    for solver in ("z3", "cvc5"):
        row = as_dict(proofs.get(solver), f"crossover_proofs.{solver}", errors)
        require(row.get("ran") is True, errors, f"{solver} must run")
        require(row.get("load_bearing") is True, errors, f"{solver} must be load-bearing")
        require(row.get("verdict") == "unsat", errors, f"{solver} positive verdict must be unsat")
        require(row.get("erased_flip_verdict") == "sat", errors, f"{solver} erased flip must be sat")
        require(row.get("erased_flip_detected") is True, errors, f"{solver} erased flip not detected")
    julia_z3 = as_dict(proofs.get("julia_z3"), "julia_z3", errors)
    require(julia_z3.get("verdict") == "unsat", errors, "Julia Z3 positive verdict must be unsat")
    require(julia_z3.get("erased_flip_verdict") == "sat", errors, "Julia Z3 erased flip must be sat")

    calls = payload.get("tool_calls")
    require(isinstance(calls, list) and len(calls) == 4, errors, "tool_calls must contain exactly four rows")
    if isinstance(calls, list):
        require([call.get("tool") for call in calls] == ["sympy", "z3", "cvc5", "Z3"], errors, "tool call order mismatch")
        require(all(call.get("load_bearing") is True for call in calls), errors, "all tool calls must be load-bearing")
    require(payload.get("claim_path_tools") == ["sympy", "z3", "cvc5", "Z3"], errors, "claim_path_tools mismatch")

    gates = as_dict(payload.get("build_gates"), "build_gates", errors)
    for gate in (
        "mode_declared_ratcheted",
        "ceilings_preserved",
        "parent_lineage_hashes_present",
        "s10_parent_hashes_match_recomputed_carrier",
        "compact_der_recomputed_14",
        "compact_stabilizer_solved_8",
        "compact_constraint_rank_6",
        "compact_coset_dim_6",
        "rep7_projection_dims",
        "rep14_projection_dims",
        "rep27_projection_dims",
        "split_positive_negative_computed",
        "path_specificity_compact_agrees",
        "wrong_unit_control_fired",
        "sign_flip_breaks_der14",
        "permuted_projector_breaks_dim_sum",
        "nothing_excluded_byte_exact",
        "smt_positive_and_erased_flip",
        "julia_result_loaded",
        "julia_source_hash_matches",
        "julia_reads_no_peer_result",
        "julia_engine_values_match_python_exact_rows",
        "julia_z3_positive_and_erased_flip",
        "one_to_one_tool_calls",
        "capability_receipts_present",
        "no_audit_verdict_emitted",
    ):
        require(gates.get(gate) is True, errors, f"gate {gate} must be true")

    divergence = as_dict(payload.get("divergence"), "divergence", errors)
    require(divergence.get("julia_authoritative") is True, errors, "divergence.julia_authoritative must be true")
    require(divergence.get("max_divergence") == 0.0, errors, "divergence max must be zero")
    engine_values = as_dict(divergence.get("engine_values"), "divergence.engine_values", errors)
    if set(engine_values) == {"julia", "jax"}:
        require(engine_values["julia"] == engine_values["jax"], errors, "Julia and Python exact engine values must match")
    else:
        errors.append("divergence.engine_values must contain julia and jax only")

    return errors


def main(argv: list[str]) -> int:
    result_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_RESULT
    if not result_path.is_absolute():
        result_path = ROOT / result_path
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    errors = validate(payload)
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
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
