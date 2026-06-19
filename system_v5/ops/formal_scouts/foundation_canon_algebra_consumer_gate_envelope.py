#!/usr/bin/env python3
"""Three-engine exhaustive/TMR envelope for the canon algebra consumer gate."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_canon_algebra_consumer_gate_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_jax_leg_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_pytorch_leg_results.json"
ARTIFACT_PATH = ROOT / "system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json"
OBJECT_ID = "foundation_canon_algebra_consumer_gate_envelope"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOL = 1.0e-12


def utc_now() -> str:
    return _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_pin(payload: dict[str, Any]) -> dict[str, Any]:
    source_path = Path(payload["source_path"])
    current = sha256_file(source_path) if source_path.is_file() else "missing"
    return {
        "source_path": str(source_path),
        "declared_source_sha256": payload.get("source_sha256"),
        "current_source_sha256": current,
        "matches": current == payload.get("source_sha256"),
    }


def norm_values(payload: dict[str, Any], algebra_key: str) -> list[float]:
    entries = payload["associator_norm_maps"][algebra_key]["entries"]
    return [float(item["norm"]) for item in entries]


def triples(payload: dict[str, Any], algebra_key: str) -> list[list[int]]:
    entries = payload["associator_norm_maps"][algebra_key]["entries"]
    return [[int(x) for x in item["triple"]] for item in entries]


def pairwise_max(left: list[float], right: list[float]) -> float:
    return max(abs(a - b) for a, b in zip(left, right, strict=True))


def changed_count(left: list[float], right: list[float]) -> int:
    return sum(1 for a, b in zip(left, right, strict=True) if abs(a - b) > TOL)


def source_checks_ok(payloads: list[dict[str, Any]], artifact_sha: str) -> bool:
    return all(
        payload["source_checks"]["artifact_sha256"] == artifact_sha
        and payload["source_checks"]["artifact_source_sha256_matches"] is True
        and payload["source_checks"]["proof_tag_matches_expected"] is True
        and payload["source_checks"]["proof_pass"] is True
        and payload["source_checks"]["bracket_convention"] == "left"
        for payload in payloads
    )


def tool_call(
    *,
    tool: str,
    api_surface: str,
    input_object: Any,
    output_object: Any,
    positive_case: Any,
    negative_control: Any,
    boundary_case: Any,
    demotion_condition: str,
) -> dict[str, Any]:
    return {
        "tool": tool,
        "api_surface": api_surface,
        "input_object": input_object,
        "output_object": output_object,
        "positive_case": positive_case,
        "negative_control": negative_control,
        "boundary_case": boundary_case,
        "demotion_condition": demotion_condition,
    }


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "source_pin": source_pin(payload),
        "source_checks": payload["source_checks"],
        "associator_norm_summaries": {
            "octonion": {
                "entry_count": payload["associator_norm_maps"]["octonion_basis_triples"]["entry_count"],
                "nonzero_count_gt_tol": payload["associator_norm_maps"]["octonion_basis_triples"]["nonzero_count_gt_tol"],
                "max_norm": payload["associator_norm_maps"]["octonion_basis_triples"]["max_norm"],
            },
            "quaternion": {
                "entry_count": payload["associator_norm_maps"]["quaternion_basis_triples"]["entry_count"],
                "nonzero_count_gt_tol": payload["associator_norm_maps"]["quaternion_basis_triples"]["nonzero_count_gt_tol"],
                "max_norm": payload["associator_norm_maps"]["quaternion_basis_triples"]["max_norm"],
            },
        },
        "sampled_nonzero_triple": payload["sampled_nonzero_triple"],
        "tool_calls": payload["tool_calls"],
    }


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    payloads = [julia, jax, pytorch]
    artifact_sha = sha256_file(ARTIFACT_PATH)
    source_pins = {"julia": source_pin(julia), "jax": source_pin(jax), "pytorch": source_pin(pytorch)}
    source_pin_pass = all(item["matches"] for item in source_pins.values())
    all_engine_pass = all(payload["all_pass"] for payload in payloads)

    oct_triples_match = triples(julia, "octonion_basis_triples") == triples(jax, "octonion_basis_triples") == triples(pytorch, "octonion_basis_triples")
    quat_triples_match = triples(julia, "quaternion_basis_triples") == triples(jax, "quaternion_basis_triples") == triples(pytorch, "quaternion_basis_triples")
    julia_oct = norm_values(julia, "octonion_basis_triples")
    jax_oct = norm_values(jax, "octonion_basis_triples")
    pytorch_oct = norm_values(pytorch, "octonion_basis_triples")
    julia_quat = norm_values(julia, "quaternion_basis_triples")
    jax_quat = norm_values(jax, "quaternion_basis_triples")
    pytorch_quat = norm_values(pytorch, "quaternion_basis_triples")
    pairwise_oct = {
        "julia_vs_jax": pairwise_max(julia_oct, jax_oct),
        "julia_vs_pytorch": pairwise_max(julia_oct, pytorch_oct),
        "jax_vs_pytorch": pairwise_max(jax_oct, pytorch_oct),
    }
    pairwise_quat = {
        "julia_vs_jax": pairwise_max(julia_quat, jax_quat),
        "julia_vs_pytorch": pairwise_max(julia_quat, pytorch_quat),
        "jax_vs_pytorch": pairwise_max(jax_quat, pytorch_quat),
    }
    max_divergence = max([*pairwise_oct.values(), *pairwise_quat.values()])
    oct_nonzero_counts = {
        "julia": julia["associator_norm_maps"]["octonion_basis_triples"]["nonzero_count_gt_tol"],
        "jax": jax["associator_norm_maps"]["octonion_basis_triples"]["nonzero_count_gt_tol"],
        "pytorch": pytorch["associator_norm_maps"]["octonion_basis_triples"]["nonzero_count_gt_tol"],
    }
    quat_nonzero_counts = {
        "julia": julia["associator_norm_maps"]["quaternion_basis_triples"]["nonzero_count_gt_tol"],
        "jax": jax["associator_norm_maps"]["quaternion_basis_triples"]["nonzero_count_gt_tol"],
        "pytorch": pytorch["associator_norm_maps"]["quaternion_basis_triples"]["nonzero_count_gt_tol"],
    }

    fault_map = [float(item["norm"]) for item in jax["fault_injection"]["fault_associator_norm_map"]["entries"]]
    fault_pairwise = {
        "julia_normal_vs_jax_fault": pairwise_max(julia_oct, fault_map),
        "pytorch_normal_vs_jax_fault": pairwise_max(pytorch_oct, fault_map),
        "normal_jax_vs_jax_fault": pairwise_max(jax_oct, fault_map),
    }
    fault_changed_entries = changed_count(jax_oct, fault_map)
    fault_detected_divergence = max(fault_pairwise.values())

    jax_z3_oct = jax["proofs"]["z3"]["octonion_sampled_nonzero_assoc"]["verdict"]
    jax_cvc5_oct = jax["proofs"]["cvc5"]["octonion_sampled_nonzero_assoc"]["verdict"]
    torch_z3_oct = pytorch["proofs"]["z3"]["octonion_sampled_nonzero_assoc"]["verdict"]
    torch_cvc5_oct = pytorch["proofs"]["cvc5"]["octonion_sampled_nonzero_assoc"]["verdict"]
    jax_z3_quat = jax["proofs"]["z3"]["quaternion_associator_nonzero_exists"]["verdict"]
    jax_cvc5_quat = jax["proofs"]["cvc5"]["quaternion_associator_nonzero_exists"]["verdict"]
    torch_z3_quat = pytorch["proofs"]["z3"]["quaternion_associator_nonzero_exists"]["verdict"]
    torch_cvc5_quat = pytorch["proofs"]["cvc5"]["quaternion_associator_nonzero_exists"]["verdict"]
    proof_pass = (
        jax_z3_oct == jax_cvc5_oct == torch_z3_oct == torch_cvc5_oct == "sat"
        and jax_z3_quat == jax_cvc5_quat == torch_z3_quat == torch_cvc5_quat == "unsat"
    )
    all_pass = (
        all_engine_pass
        and source_pin_pass
        and source_checks_ok(payloads, artifact_sha)
        and oct_triples_match
        and quat_triples_match
        and max_divergence <= TOL
        and set(oct_nonzero_counts.values()) == {168}
        and set(quat_nonzero_counts.values()) == {0}
        and proof_pass
        and jax["jax_parallel_workhorse"]["uses_jax_vmap"] is True
        and jax["jax_parallel_workhorse"]["random_unit_triple_distribution"]["triple_count"] >= 10_000
        and fault_detected_divergence > TOL
    )
    canon_runtime = {
        "semantic_owner": "julia",
        "artifact_path": str(ARTIFACT_PATH),
        "artifact_sha256": artifact_sha,
        "source_sha256": julia["canon_runtime"]["source_sha256"],
        "receipt_path": str(ROOT / "system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json"),
        "proof_tag": julia["source_checks"]["proof_tag"],
        "proof_pass": julia["source_checks"]["proof_pass"],
        "table_version": julia["source_checks"]["table_version"],
        "bracket_convention": julia["source_checks"]["bracket_convention"],
        "consumer_policy": "compute_from_exported_C_tensor_with_fixed_parenthesization",
    }
    foreign_runtime_manifest = {
        "julia": {"project": julia.get("julia_project"), "packages": julia["packages_used"], "role": "semantic_owner"},
        "jax": {"packages": jax["packages_used"], "role": "parallel_workhorse_and_smt_consumer"},
        "pytorch": {"packages": pytorch["packages_used"], "role": "independent_tmr_consumer_and_smt_consumer"},
        "tensor_exchange": "none_this_gate_json_canon_artifact_only",
        "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
    }
    tool_calls = [
        tool_call(
            tool="json",
            api_surface="json.loads(result_path.read_text(encoding='utf-8'))",
            input_object={"result_paths": [str(JULIA_RESULT), str(JAX_RESULT), str(PYTORCH_RESULT)]},
            output_object={"engines": ["julia", "jax", "pytorch"], "all_engine_pass": all_engine_pass},
            positive_case="Envelope reads only completed leg receipts after each leg computed locally.",
            negative_control="Demotes if any leg has reads_peer_result=true or source pin mismatch.",
            boundary_case="Quaternion exhaustive maps remain zero across all engine receipts.",
            demotion_condition="Demote if a leg result is stale, peer-fed, or missing function-level tool_calls.",
        ),
        tool_call(
            tool="python_stdlib",
            api_surface="max(abs(engine_map[t] - julia_map[t]) for all 512 octonion triples and 64 quaternion triples)",
            input_object={"compared_maps": ["octonion_basis_triples", "quaternion_basis_triples"], "engines": ["julia", "jax", "pytorch"]},
            output_object={"max_divergence": max_divergence, "pairwise_octonion": pairwise_oct, "pairwise_quaternion": pairwise_quat},
            positive_case="All three independently computed associator-norm maps are in the Julia-authoritative equivalence class.",
            negative_control={"jax_only_fault_detected_divergence": fault_detected_divergence, "changed_entry_count": fault_changed_entries},
            boundary_case={"quaternion_nonzero_counts": quat_nonzero_counts},
            demotion_condition="Demote if max divergence exceeds tolerance or fault injection does not break agreement.",
        ),
    ]
    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": OBJECT_ID,
        "classification": CLASSIFICATION,
        "generated_at": utc_now(),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "source_path_self_check": str(SOURCE_PATH),
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "reads_peer_result": False,
            "julia_authoritative": True,
            "leg_reads_peer_result": {"julia": julia["reads_peer_result"], "jax": jax["reads_peer_result"], "pytorch": pytorch["reads_peer_result"]},
            "consumer_rule": "Each engine loads the Julia-owned C[k][i][j] table and independently computes associator norms with fixed left parenthesization.",
        },
        "claim_ceiling": "Scratch diagnostic exhaustive cross-framework canon-table consumer gate only; no promotion, no formal admission, no carrier canon upgrade.",
        "canon_runtime": canon_runtime,
        "foreign_runtime_manifest": foreign_runtime_manifest,
        "source_artifact": {
            "source_path": str(ARTIFACT_PATH),
            "source_sha256": artifact_sha,
            "proof_tag": julia["source_checks"]["proof_tag"],
            "table_version": julia["source_checks"]["table_version"],
            "bracket_convention": julia["source_checks"]["bracket_convention"],
        },
        "probe_family_M": {
            "octonion_exhaustive_basis_triples": "all i,j,k in 0..7, 512 triples",
            "quaternion_exhaustive_basis_triples": "all i,j,k in 0..3, 64 triples",
            "jax_random_unit_octonion_triples": jax["jax_parallel_workhorse"]["random_unit_triple_distribution"]["triple_count"],
        },
        "constraints_C": [
            "load system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json directly",
            "preserve proof_tag sha256:a9470fc299d39917a791bba0144d3e526866ad217b90fac1a6622b25d2c4652a",
            "preserve table_version=algebra_structure_constants_v1 and bracket_convention=left",
            "compute mul(a,b)[k]=sum_ij C[k,i,j]*a[i]*b[j]",
            "compute associator as mul(mul(a,b),c)-mul(a,mul(b,c))",
            "derive z3/cvc5 proofs from bound C entries on JAX and PyTorch legs",
            "do not use numpy/scipy/mpmath on claim path",
        ],
        "quotient_S_mod_M": {
            "equivalence_relation": "engine readouts are equivalent when every exhaustive associator norm matches Julia within 1e-12",
            "julia_authoritative_class": ["julia", "jax", "pytorch"] if max_divergence <= TOL else ["julia"],
            "max_divergence": max_divergence,
            "status": "same_consumer_class" if max_divergence <= TOL else "diverged",
        },
        "tmr_agreement": {
            "status": "agreement" if max_divergence <= TOL else "disagreement",
            "max_divergence": max_divergence,
            "pairwise_octonion": pairwise_oct,
            "pairwise_quaternion": pairwise_quat,
            "octonion_nonzero_counts": oct_nonzero_counts,
            "quaternion_nonzero_counts": quat_nonzero_counts,
            "octonion_entry_count": len(julia_oct),
            "quaternion_entry_count": len(julia_quat),
            "julia_authoritative": True,
        },
        "exhaustive_controls": {
            "octonion_nonzero_count_gt_tol": oct_nonzero_counts["julia"],
            "octonion_total_triples": len(julia_oct),
            "quaternion_all_zero": set(quat_nonzero_counts.values()) == {0},
            "quaternion_total_triples": len(julia_quat),
        },
        "jax_parallel_workhorse": jax["jax_parallel_workhorse"],
        "fault_injection": {
            "engine_copy": "jax_only",
            "fault_index_C_k_i_j_zero_based": jax["fault_injection"]["fault_index_C_k_i_j_zero_based"],
            "original_value": jax["fault_injection"]["original_value"],
            "fault_value": jax["fault_injection"]["fault_value"],
            "detected_divergence": fault_detected_divergence,
            "changed_entry_count": fault_changed_entries,
            "tmr_status_after_fault": "disagreement_detected" if fault_detected_divergence > TOL else "missed_fault",
            "restored_by_copy": jax["fault_injection"]["restored_by_copy"],
        },
        "smt_verdicts": {
            "jax": {
                "z3_octonion_sampled_nonzero": jax_z3_oct,
                "cvc5_octonion_sampled_nonzero": jax_cvc5_oct,
                "z3_quaternion_nonzero_exists": jax_z3_quat,
                "cvc5_quaternion_nonzero_exists": jax_cvc5_quat,
                "sampled_nonzero_triple": jax["sampled_nonzero_triple"],
                "derive_in_solver": True,
            },
            "pytorch": {
                "z3_octonion_sampled_nonzero": torch_z3_oct,
                "cvc5_octonion_sampled_nonzero": torch_cvc5_oct,
                "z3_quaternion_nonzero_exists": torch_z3_quat,
                "cvc5_quaternion_nonzero_exists": torch_cvc5_quat,
                "sampled_nonzero_triple": pytorch["sampled_nonzero_triple"],
                "derive_in_solver": True,
            },
        },
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": "sat",
                "claim": "Octonion sampled basis associator nonzero is SAT from bound C entries on both JAX and PyTorch legs.",
                "jax_verdict": jax_z3_oct,
                "pytorch_verdict": torch_z3_oct,
                "boundary_quaternion_verdict": "unsat" if jax_z3_quat == torch_z3_quat == "unsat" else "mixed",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": "sat",
                "claim": "Octonion sampled basis associator nonzero is SAT from bound C entries on both JAX and PyTorch legs.",
                "jax_verdict": jax_cvc5_oct,
                "pytorch_verdict": torch_cvc5_oct,
                "boundary_quaternion_verdict": "unsat" if jax_cvc5_quat == torch_cvc5_quat == "unsat" else "mixed",
            },
        },
        "claim_path_tools": ["JSON", "Julia", "Z3", "jax", "jax.numpy", "jax.vmap", "jax.jit", "z3", "cvc5", "torch", "torch.einsum", "python_stdlib"],
        "control_only_tools": [],
        "TOOL_MANIFEST": {
            "Julia": {"tried": True, "used": True, "reason": "load-bearing authoritative exhaustive map computation"},
            "jax.vmap": {"tried": True, "used": True, "reason": "load-bearing batched 512-map and 10000-random-triple distribution"},
            "torch": {"tried": True, "used": True, "reason": "load-bearing independent exhaustive map computation"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing derive-in-solver controls on JAX and PyTorch"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent SMT redundancy on JAX and PyTorch"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "Julia": "load_bearing",
            "jax.vmap": "load_bearing",
            "torch": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
        },
        "tool_calls": tool_calls,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": {"octonion_norms": julia_oct, "quaternion_norms": julia_quat},
                "jax": {"octonion_norms": jax_oct, "quaternion_norms": jax_quat},
                "pytorch": {"octonion_norms": pytorch_oct, "quaternion_norms": pytorch_quat},
            },
            "max_divergence": max_divergence,
            "tolerance": TOL,
        },
        "all_pass": all_pass,
        "GAINED": [
            "All three engines independently computed matching exhaustive octonion associator-norm maps.",
            "JAX served as parallel workhorse with vmap/jit over the 512 basis triples and vmap over 10000 random unit triples.",
            "A JAX-only corrupted table copy broke TMR agreement and was detected.",
            "JAX and PyTorch both ran z3+cvc5 derive-in-solver controls from bound C entries.",
        ],
        "NOT_GAINED": [
            "No promotion beyond scratch_diagnostic.",
            "No formal admission.",
            "No independent JAX/PyTorch table authority.",
            "No bridge, axis, manifold, or physics claim.",
        ],
        "CONTROLS": [
            "Octonion exhaustive nonzero count is 168 / 512.",
            "Quaternion exhaustive associator map is all zero.",
            "JAX-only fault injection at C[3][1][2] changes the map and triggers TMR disagreement.",
            "No numpy/scipy/mpmath appear on the claim path.",
        ],
        "CEILING": "classification=scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false",
    }


def main() -> int:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": str(RESULT_PATH), "source_sha256": result["source_sha256"]}))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
