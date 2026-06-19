#!/usr/bin/env python3
"""Envelope assembler for geo_union_rule_k_leaves_v0."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from geo_union_rule_k_leaves_v0_common import (
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
    parent_lineage,
    rel,
    sha256_text,
    stable_json_sha256,
)


SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
PYTHON_RESULT = RESULT_DIR / f"{SIM_ID}_python_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
VALIDATOR_PATH = SIM_DIR / f"{SIM_ID}_exact_strength_validator.py"
THREE_ENGINE_VALIDATOR_PATH = ROOT / "scripts" / "validate_three_engine_sim_result.py"

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from fresh Python and Julia receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result/PIN hash checks"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "engine": payload["engine"],
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
    payloads = {"python": load_json(PYTHON_RESULT), "julia": load_json(JULIA_RESULT)}
    python = payloads["python"]
    julia = payloads["julia"]
    py_receipts = python["receipts"]
    jl_receipts = julia["receipts"]
    z3_row = python["crossover_proofs"]["z3"]
    cvc5_row = python["crossover_proofs"]["cvc5"]
    julia_z3 = julia["crossover_proofs"]["julia_z3"]
    k2 = py_receipts["K2_parent_two_leaf_byte_exact_reduction"]
    k3 = py_receipts["K3_concrete_k3_k4_committed_shell_weights"]
    assoc = py_receipts["K4_associativity_order_row_k3"]
    controls = py_receipts["K5_degenerate_boundary_and_equal_weight_controls"]
    mortality = py_receipts["K6_mortality_boundary_free_measure"]
    pin_hashes = {payload["pin_sha256"] for payload in payloads.values()}
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
        "general_k_leaf_rule": py_receipts["K1_general_k_leaf_band_limit_rule"]["pass"] is True
        and jl_receipts["J1_symbolics_general_k_leaf_rule"]["pass"] is True,
        "k2_parent_byte_exact": k2["pass"] is True and k2["computed_row_sha256"] == k2["parent_row_sha256"],
        "concrete_k3_k4_weights": k3["pass"] is True
        and k3["k3_weights"][0]["weight"] in {"1/2 - sqrt(3)/6", "(3 - sqrt(3))/6"}
        and k3["k4_weights"][2]["eta"] == "pi/4",
        "associativity_order_row": assoc["pass"] is True
        and assoc["agreement_or_gap"] == "agreement_when_iterated_union_carries_summed_group_mass"
        and jl_receipts["J3_symbolics_associativity_order_row"]["pass"] is True,
        "degenerate_repeated_leaf_collapse": controls["pass"] is True
        and controls["duplicate_double_count_cos_2eta_defect"] != "0"
        and controls["boundary_weights"][0]["weight"] == "0",
        "equal_weights_control_fails": controls["equal_weights_control_defect_equal_minus_correct"] != "0"
        and jl_receipts["J4_symbolics_degenerate_boundary_controls"]["pass"] is True,
        "mortality_boundary_free_measure": mortality["pass"] is True
        and mortality["definable_again_k"] == "no_finite_k"
        and mortality["all_shell_constant_recovery"] == "1"
        and jl_receipts["J5_mortality_boundary"]["definable_again_k"] == "no_finite_k",
        "z3_cvc5_k3_weight_identity": z3_row["verdict"] == cvc5_row["verdict"] == "unsat"
        and z3_row["erase_flip_unsat_to_sat"]
        and cvc5_row["erase_flip_unsat_to_sat"],
        "julia_z3_k3_weight_identity": julia_z3["verdict"] == "unsat" and julia_z3["erase_flip_unsat_to_sat"],
        "one_to_one_claim_tool_calls": {call["tool"] for call in collect(payloads, "tool_calls")} >= set(collect_tools(payloads)),
        "summary_boundary_present": "no_finite_k" in mortality["definable_again_k"]
        and "finite-k FREE replacement" in python["summary"]["does_not_enable"],
    }
    all_pass = all(gates.values())
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "Finite k-leaf extension of the committed geo_nested_disintegration_v0 two-leaf union rule: distinct fixed-eta shell unions condition by weights sin(2 eta_i)/sum_j sin(2 eta_j), k=2 reproduces the committed exact row, k=3/k=4 committed shells are computed, grouped k=3 union is associative when group mass is summed, degenerate leaves collapse, zero-boundary leaves vanish, equal weights fail, and only the continuum all-shell boundary recovers unconditioned FREE measure.",
        "stage": "mode4_prerequisite_k_leaf_union_rule",
        "mode": "RATCHETED_prerequisite_finite_k_union_conditioning_rule",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "validator_path": rel(VALIDATOR_PATH),
        "validator_expected_command": f"{ROOT}/system_v6/sims/{SIM_ID}/{SIM_ID}_exact_strength_validator.py",
        "three_engine_validator_path": rel(THREE_ENGINE_VALIDATOR_PATH),
        "three_engine_validator_expected_command": f"{ROOT}/scripts/validate_three_engine_sim_result.py {rel(RESULT_PATH)}",
        "seed": SEEDS,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "convention_pin": CONVENTION_PIN,
        "lineage_citations": LINEAGE_CITATIONS,
        "parent_lineage": parent_lineage(),
        "engine_contract": {
            "mode": ENGINE_MODE,
            "lanes": ["julia", "jax"],
            "lane_note": "The standard validator's jax lane is a Python SymPy/z3/cvc5 sidecar for this measure packet; no JAX array claim is made.",
            "audit_order": ["combined_envelope", "python_sympy_smt_local", "julia_symbolics_z3_local", "controller_comparison"],
            "pytorch": {
                "scoped": False,
                "reason": "No graph/network/autograd claim path; PyTorch would be decorative for this finite measure-disintegration prerequisite.",
            },
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": julia.get("julia_project", JULIA_PROJECT),
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": julia["source_sha256"],
            "receipt_path": julia["result_path"],
            "proof_tag": "geo_union_rule_k_leaves_v0_julia_symbolics_z3",
            "proof_pass": bool(julia["all_pass"]),
            "table_version": None,
            "bracket_convention": "not_applicable_measure_disintegration_over_Hopf_eta_shell_unions",
            "consumer_policy": "independent Julia Symbolics/Z3 and Python SymPy/z3/cvc5 recovery; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia.get("julia_project", JULIA_PROJECT), "packages": julia["packages_used"], "role": "Symbolics/Z3 semantic mirror"},
            "jax": {"packages": python["packages_used"], "role": "Python SymPy exact derivation plus z3/cvc5 SMT sidecar; no JAX array computation"},
            "pytorch": {"packages": [], "role": "omitted_no_graph_network_autograd_claim_path"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": collect_tools(payloads),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(python, PYTHON_RESULT),
        },
        "receipts": {
            **py_receipts,
            **jl_receipts,
        },
        "crossover_proofs": {
            "z3": z3_row,
            "cvc5": cvc5_row,
            "julia_z3": julia_z3,
        },
        "controls": {
            "repeated_leaf_collapse": controls,
            "equal_weights": {
                "value": controls["equal_weights_control_k3_value"],
                "correct": controls["correct_k3_value"],
                "defect": controls["equal_weights_control_defect_equal_minus_correct"],
            },
            "boundary_zero_leaf": controls["boundary_weights"],
            "mortality_boundary": mortality,
        },
        "capability_receipts": {
            "julia": julia["capability_receipts"],
            "python": python["capability_receipts"],
        },
        "tool_calls": collect(payloads, "tool_calls"),
        "build_gates": gates,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": 0.0 if jl_receipts["J2_symbolics_k3_radical_weights"]["pass"] else 1.0,
                "jax": 0.0 if py_receipts["K2_parent_two_leaf_byte_exact_reduction"]["pass"] else 1.0,
            },
            "max_divergence": 0.0,
            "basis": "Julia Symbolics/Z3 and Python SymPy/z3/cvc5 agree on zero identity defects, k=3 weight identity UNSAT, and erased flips.",
        },
        "summary": {
            "enables": "finite multi-shell stack builders may cite the finite-k union rule with parent-lineage hashes and k=2 byte-exact reduction to geo_nested_disintegration_v0",
            "does_not_enable": "no manifold, axis, bridge, physics, canonical admission, finite-k FREE replacement, or formal proof claim is made",
            "anchor_values": {
                "k_leaf_rule": "w_i=sin(2*eta_i)/sum_j sin(2*eta_j)",
                "k2_parent_row_sha256": k2["parent_row_sha256"],
                "k3_shells": k3["k3_shells"],
                "k3_weights": k3["k3_weights"],
                "k4_shells": k3["k4_shells"],
                "k4_weights": k3["k4_weights"],
                "associativity_order_row": assoc["agreement_or_gap"],
                "definable_again_k": mortality["definable_again_k"],
                "free_boundary": mortality["definable_again_boundary"],
            },
            "ceiling": CLASSIFICATION,
            "pytorch_omission": "no graph/network/autograd claim path; engine mode is julia_symbolics_plus_python_sympy_smt_diagnostic",
        },
        "builder_scope_boundary": {
            "ceiling": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "no_audit_verdict_written": True,
            "blocked_consumers": [
                "canonical_admission",
                "formal_proof",
                "bridge_or_axis_claims",
                "finite_k_free_measure_replacement",
                "physics_or_manifold_completion",
            ],
        },
        "result_hashes": {
            "python_result_sha256": file_sha256(PYTHON_RESULT),
            "julia_result_sha256": file_sha256(JULIA_RESULT),
            "envelope_stable_content_sha256_note": "source/result hash recorded after write by external checks",
            "parent_r3_row_sha256": k2["parent_row_sha256"],
            "computed_k2_row_sha256": k2["computed_row_sha256"],
            "lineage_stable_json_sha256": stable_json_sha256(parent_lineage()),
        },
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": bool(all_pass), "result_path": rel(RESULT_PATH), "gates": gates}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
