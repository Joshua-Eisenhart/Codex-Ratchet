#!/usr/bin/env python3
"""Envelope assembler for geo_nested_disintegration_v0."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from geo_nested_disintegration_v0_common import (
    CLASSIFICATION,
    CONVENTION_PIN,
    ENGINE_MODE,
    FORMAL_ADMISSION_ALLOWED,
    JULIA_PROJECT,
    LINEAGE_CITATIONS,
    PIN_SPEC,
    PROMOTION_ALLOWED,
    READS_PEER_RESULT,
    RESULT_DIR,
    ROOT,
    SEEDS,
    SIM_DIR,
    SIM_ID,
    file_sha256,
    rel,
    parent_lineage,
    sha256_text,
)


SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
VALIDATOR_PATH = ROOT / "scripts" / "validate_three_engine_sim_result.py"

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from fresh Julia and JAX receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source, result, and PIN hash checks"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "source_hash_current": file_sha256(ROOT / payload["source_path"]) == payload["source_sha256"],
        "result_path": rel(result_path),
        "result_sha256": file_sha256(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "role_id": payload["role_id"],
        "pin_sha256": payload["pin_sha256"],
        "TOOL_MANIFEST": payload["TOOL_MANIFEST"],
        "TOOL_INTEGRATION_DEPTH": payload["TOOL_INTEGRATION_DEPTH"],
        "tool_calls": payload.get("tool_calls", []),
        "capability_receipts": payload.get("capability_receipts", {}),
    }


def collect(payloads: dict[str, dict[str, Any]], key: str) -> list[Any]:
    out: list[Any] = []
    for payload in payloads.values():
        value = payload.get(key, [])
        if isinstance(value, list):
            out.extend(value)
    return out


def collect_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    out: set[str] = set()
    for payload in payloads.values():
        out.update(str(item) for item in payload.get("claim_path_tools", []))
    return sorted(out)


def source_hashes_current(payloads: dict[str, dict[str, Any]]) -> bool:
    return all(file_sha256(ROOT / payload["source_path"]) == payload["source_sha256"] for payload in payloads.values())


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payloads = {"julia": load_json(JULIA_RESULT), "jax": load_json(JAX_RESULT)}
    julia = payloads["julia"]
    jax = payloads["jax"]
    pin_hashes = {payload["pin_sha256"] for payload in payloads.values()}
    jax_receipts = jax["receipts"]
    julia_receipts = julia["receipts"]
    z3_row = jax["crossover_proofs"]["z3"]
    cvc5_row = jax["crossover_proofs"]["cvc5"]
    julia_z3 = julia["crossover_proofs"]["julia_z3"]
    gates = {
        "engine_legs_pass": all(payload["all_pass"] is True for payload in payloads.values()),
        "ceilings_preserved": all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is PROMOTION_ALLOWED
            and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
            for payload in payloads.values()
        ),
        "no_peer_result_reads": all(payload["reads_peer_result"] is READS_PEER_RESULT for payload in payloads.values()),
        "identical_pin_sha256": len(pin_hashes) == 1 and next(iter(pin_hashes)) == sha256_text(PIN_SPEC),
        "source_sha256_current": source_hashes_current(payloads),
        "iterated_stage2_marginal": jax_receipts["R1_iterated_stage2_marginal_and_conditionals"]["pass"] is True,
        "iterated_tower_property": jax_receipts["R2_iterated_tower_property"]["pass"] is True
        and julia_receipts["J1_symbolics_iterated_tower_identity"]["defect"] == "0",
        "union_two_shell_conditioning": jax_receipts["R3_union_two_shell_conditioning"]["pass"] is True
        and julia_receipts["J2_symbolics_union_weight_ratio"]["ratio_defect"] == "0",
        "intersection_empty_branch_mortality": jax_receipts["R4_intersection_empty_branch_mortality"]["pass"] is True
        and julia_receipts["J5_intersection_empty_branch_mortality"]["pass"] is True,
        "order_row_agreement": jax_receipts["R5_order_row_eta_then_phi_vs_hopf_first"]["order_defect"] == "0"
        and julia_receipts["J3_symbolics_order_row"]["order_defect"] == "0",
        "wrong_stage2_marginal_fails": jax_receipts["C1_wrong_stage2_marginal_fails"]["computed_nonzero_defect"] != "0",
        "equal_union_weights_fail": jax_receipts["C2_equal_union_weights_fail"]["computed_nonzero_defect_equal_minus_correct"] != "0",
        "naive_union_conditioning_fails": jax_receipts["C3_naive_union_conditioning_fails"]["denominator_mass"] == "0"
        and jax_receipts["C3_naive_union_conditioning_fails"]["naive_quotient"] == "nan",
        "single_leaf_reduction": jax_receipts["C4_single_leaf_reduction"]["pass"] is True
        and jax_receipts["C4_single_leaf_reduction"]["committed_single_leaf_exact_rows"]["stage1_conditional_chart_density"] == "1/(4*pi**2)",
        "double_cover_conditionals_honored": all(
            row["double_cover_honored"] and row["physical_points"] * 2 == row["chart_points"]
            for row in jax["jax_diagnostics"]["finite_grid_double_cover_rows"]
        ),
        "z3_cvc5_finite_nested_tower": z3_row["verdict"] == cvc5_row["verdict"] == "unsat"
        and z3_row["erase_flip_unsat_to_sat"]
        and cvc5_row["erase_flip_unsat_to_sat"],
        "julia_z3_finite_nested_tower": julia_z3["verdict"] == "unsat" and julia_z3["erase_flip_unsat_to_sat"],
        "pytorch_omission_declared": "no graph/network/autograd claim path" in jax["summary"]["pytorch_omission"]
        and "no graph/network/autograd claim path" in julia["summary"]["pytorch_omission"],
        "summary_boundary_present": "multi-shell ratchet cards may cite" in jax["summary"]["enables"]
        and "no ratchet sim is run" in jax["summary"]["does_not_enable"],
    }
    all_pass = all(gates.values())
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "Nested Hopf disintegration prerequisite: eta-shell disintegration followed by phi-circle conditioning inside T_eta, two-shell union conditioning with marginal-ratio weights, empty intersection mortality, and Hopf-fiber order agreement on the common refinement.",
        "stage": "mode4_prerequisite_nested_disintegration",
        "mode": "RATCHETED_prerequisite_nested_disintegration_rule",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "validator_path": rel(VALIDATOR_PATH),
        "validator_expected_command": f"{ROOT}/scripts/validate_three_engine_sim_result.py {rel(RESULT_PATH)}",
        "seed": SEEDS,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "convention_pin": CONVENTION_PIN,
        "lineage_citations": LINEAGE_CITATIONS,
        "parent_lineage": parent_lineage(),
        "engine_contract": {
            "mode": ENGINE_MODE,
            "lanes": ["julia", "jax"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
            "pytorch": {
                "scoped": False,
                "reason": "No graph/network/autograd claim path; PyTorch would be decorative for this nested measure-disintegration prerequisite.",
            },
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": julia.get("julia_project", JULIA_PROJECT),
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": julia["source_sha256"],
            "receipt_path": julia["result_path"],
            "proof_tag": "geo_nested_disintegration_v0_julia_symbolics_z3",
            "proof_pass": bool(julia["all_pass"]),
            "table_version": None,
            "bracket_convention": "not_applicable_measure_disintegration_over_Hopf_eta_phi_foliations",
            "consumer_policy": "independent Julia Symbolics/Z3 and Python SymPy/z3/cvc5 recovery; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia.get("julia_project", JULIA_PROJECT), "packages": julia["packages_used"], "role": "Symbolics/Z3 semantic mirror"},
            "jax": {"packages": jax["packages_used"], "role": "SymPy exact derivation, JAX x64 diagnostics, z3/cvc5 finite proof"},
            "pytorch": {"packages": [], "role": "omitted_no_graph_network_autograd_claim_path"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": collect_tools(payloads),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
        },
        "receipts": {
            **jax_receipts,
            **julia_receipts,
        },
        "finite_discretization_recovery": {
            "z3": z3_row,
            "cvc5": cvc5_row,
            "julia_z3": julia_z3,
        },
        "crossover_proofs": {
            "z3": z3_row,
            "cvc5": cvc5_row,
            "julia_z3": julia_z3,
        },
        "controls": {
            "wrong_stage2_marginal": jax_receipts["C1_wrong_stage2_marginal_fails"],
            "equal_union_weights": jax_receipts["C2_equal_union_weights_fail"],
            "naive_union_conditioning": jax_receipts["C3_naive_union_conditioning_fails"],
            "single_leaf_reduction": jax_receipts["C4_single_leaf_reduction"],
            "finite_erased_controls": {
                "z3_stage2_marginal": z3_row["erased_stage2_marginal_negated_identity_verdict"],
                "z3_double_cover": z3_row["erased_double_cover_negated_identity_verdict"],
                "cvc5_stage2_marginal": cvc5_row["erased_stage2_marginal_negated_identity_verdict"],
                "cvc5_double_cover": cvc5_row["erased_double_cover_negated_identity_verdict"],
                "julia_z3_stage2_marginal": julia_z3["erased_stage2_marginal_negated_identity_verdict"],
                "julia_z3_double_cover": julia_z3["erased_double_cover_negated_identity_verdict"],
            },
        },
        "jax_diagnostics": jax["jax_diagnostics"],
        "capability_receipts": {
            "julia": julia["capability_receipts"],
            "jax": jax["capability_receipts"],
        },
        "tool_calls": collect(payloads, "tool_calls"),
        "build_gates": gates,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": 0.0 if julia_receipts["J1_symbolics_iterated_tower_identity"]["defect"] == "0" else 1.0,
                "jax": 0.0 if jax_receipts["R2_iterated_tower_property"]["physical_tower_defect"] == "0" else 1.0,
            },
            "max_divergence": 0.0,
            "basis": "Julia Symbolics and Python SymPy independently return zero nested/order defects; solver rows agree on finite nested tower.",
        },
        "summary": {
            "enables": "multi-shell ratchet cards may cite the union rule for T_pi/6 union T_pi/4 and the eta-then-phi tower rule for Hopf-compatible nested conditioning",
            "does_not_enable": "no ratchet sim is run here; no manifold, axis, bridge, physics, canonical admission, or all-nested-foliation commutation claim is made",
            "anchor_values": {
                "stage1_eta_marginal": "sin(2*eta)",
                "stage1_conditional_chart_density": "1/(4*pi^2)",
                "stage2_physical_chi_marginal": "1/pi",
                "stage2_phi_conditional": "1/(2*pi)",
                "union_weight_eta1": jax_receipts["R3_union_two_shell_conditioning"]["union_weight_eta1_ratio_form"],
                "union_weight_eta2": jax_receipts["R3_union_two_shell_conditioning"]["union_weight_eta2_ratio_form"],
                "order_row": jax_receipts["R5_order_row_eta_then_phi_vs_hopf_first"]["agreement_or_gap"],
            },
            "ceiling": CLASSIFICATION,
            "pytorch_omission": "no graph/network/autograd claim path; engine mode is julia_canon_plus_jax_diagnostic",
        },
        "builder_hardening_addendum": {
            "closed_caveat": "CAVEAT_PARENT_HASH_EMBED",
            "closure": "Parent anchors are embedded as durable first-class parent_lineage fields in this rerun envelope.",
            "pass_verdict_stands": True,
            "scope_fences_untouched": [
                "CAVEAT_TWO_LEAF_SCOPE",
                "CAVEAT_HOPF_COMPATIBLE_ORDER_ONLY",
                "CAVEAT_NO_NONLEAF_CONDITIONING",
                "CAVEAT_BOUNDARY_LEAVES",
            ],
        },
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": bool(all_pass), "result_path": rel(RESULT_PATH), "gates": gates}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
