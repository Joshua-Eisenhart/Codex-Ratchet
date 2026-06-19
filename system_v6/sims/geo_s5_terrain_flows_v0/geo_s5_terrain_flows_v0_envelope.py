#!/usr/bin/env python3
"""Envelope assembler for geo_s5_terrain_flows_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import sympy as sp


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s5_terrain_flows_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
SPEC = ROOT / "system_v6" / "receipts" / "s5_build_spec_20260610.md"
SPEC_COPY = SIM_DIR / "s5_build_spec_20260610.md"
DIRECTIVE_COPY = SIM_DIR / "directive_addendum.md"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

REQUIRED_POSITIVE_RECEIPTS = {
    "P1_source_lineage_and_pins",
    "P2_exact_bloch_generator_table",
    "P3_flow_solutions_exact",
    "P4_cptp_all_t_proof",
    "P5_fixed_points_exact",
    "P6_basin_limits_exact",
    "P7_pure_hamiltonian_purity_preserved",
    "P8_nonunitality_witnesses",
    "P9_executed_negative_controls",
    "P10_claim_ceiling",
}

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from fresh engine receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source, copied-input, result, and PIN hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing cross-engine pinned A,b normalization; row disagreement is fatal"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive", "sympy": "load_bearing"}
ENGINE_ROW_TOL = 1.0e-6


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
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
        "convention_pin": payload["convention_pin"],
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
        "tool_calls": payload.get("tool_calls", []),
    }


def current_source_hash_ok(payload: dict[str, Any]) -> bool:
    source = ROOT / payload["source_path"]
    return source.exists() and file_sha256(source) == payload["source_sha256"]


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def copied_input_records() -> dict[str, Any]:
    return {
        "s5_build_spec": {
            "source_path": rel(SPEC),
            "copy_path": rel(SPEC_COPY),
            "source_sha256": file_sha256(SPEC),
            "copy_sha256": file_sha256(SPEC_COPY),
            "exists": SPEC_COPY.exists(),
            "matches_source": SPEC_COPY.exists() and file_sha256(SPEC_COPY) == file_sha256(SPEC),
        },
        "directive_addendum": {
            "copy_path": rel(DIRECTIVE_COPY),
            "copy_sha256": file_sha256(DIRECTIVE_COPY),
            "exists": DIRECTIVE_COPY.exists(),
            "source": "user directive plus s5_build_spec directive rules; no separate /tmp S5 directive file was present",
        },
    }


def positive_ledger(jax: dict[str, Any]) -> dict[str, Any]:
    return {
        key: {
            "pass": jax["receipts"][key]["pass"],
            "exact_strength": jax["receipts"][key]["exact_strength"],
        }
        for key in sorted(REQUIRED_POSITIVE_RECEIPTS)
    }


def numeric_expr(value: str) -> float:
    return float(sp.N(sp.sympify(value.replace("//", "/"), locals={"sqrt": sp.sqrt}), 40))


def numeric_matrix(values: list[list[str]]) -> list[list[float]]:
    return [[numeric_expr(item) for item in row] for row in values]


def numeric_vector(values: list[str]) -> list[float]:
    return [numeric_expr(item) for item in values]


def max_abs_diff(left: list[Any], right: list[Any]) -> float:
    diffs: list[float] = []
    for a, b in zip(left, right, strict=True):
        if isinstance(a, list):
            diffs.append(max_abs_diff(a, b))
        else:
            diffs.append(abs(float(a) - float(b)))
    return max(diffs) if diffs else 0.0


def cross_engine_consistency(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    jax_rows = payloads["jax"]["bloch_generator_table"]
    julia_rows = payloads["julia"]["density_generator_derivation"]["rows"]
    torch_rows = payloads["pytorch"]["affine_batch"]["rows"]
    row_reports: dict[str, Any] = {}
    for row_key in sorted(jax_rows):
        jax_A = numeric_matrix(jax_rows[row_key]["pinned"]["A"])
        jax_b = numeric_vector(jax_rows[row_key]["pinned"]["b"])
        julia_A = numeric_matrix(julia_rows[row_key]["pinned"]["A"])
        julia_b = numeric_vector(julia_rows[row_key]["pinned"]["b"])
        torch_A = numeric_matrix(torch_rows[row_key]["pinned_A_fractional"])
        torch_b = numeric_vector(torch_rows[row_key]["pinned_b_fractional"])
        diffs = {
            "jax_vs_julia_A": max_abs_diff(jax_A, julia_A),
            "jax_vs_julia_b": max_abs_diff(jax_b, julia_b),
            "jax_vs_pytorch_A": max_abs_diff(jax_A, torch_A),
            "jax_vs_pytorch_b": max_abs_diff(jax_b, torch_b),
            "julia_vs_pytorch_A": max_abs_diff(julia_A, torch_A),
            "julia_vs_pytorch_b": max_abs_diff(julia_b, torch_b),
        }
        row_reports[row_key] = {
            "load_bearing_row": True,
            "tolerance": ENGINE_ROW_TOL,
            "max_abs_diff": max(diffs.values()),
            "pairwise_diffs": diffs,
            "pass": max(diffs.values()) <= ENGINE_ROW_TOL,
        }
    max_diff = max(row["max_abs_diff"] for row in row_reports.values())
    return {
        "method": "fatal pinned A,b row comparison across independent Julia/JAX/PyTorch derivations",
        "tolerance": ENGINE_ROW_TOL,
        "rows": row_reports,
        "max_abs_diff": max_diff,
        "all_pass": all(row["pass"] is True for row in row_reports.values()),
    }


def main() -> int:
    payloads = {
        "julia": load_json(JULIA_RESULT),
        "jax": load_json(JAX_RESULT),
        "pytorch": load_json(PYTORCH_RESULT),
    }
    julia = payloads["julia"]
    jax = payloads["jax"]
    pytorch = payloads["pytorch"]
    copied_inputs = copied_input_records()
    pin_hashes = {payload["pin_sha256"] for payload in payloads.values()}
    convention_pin_ok = julia["convention_pin"] == jax["convention_pin"] == pytorch["convention_pin"]
    claim_path_tools = collect_claim_tools(payloads)
    controls = jax["negative_controls"]
    receipts = jax["receipts"]
    cross_engine = cross_engine_consistency(payloads)
    gates = {
        "engine_legs_pass": all(payload["all_pass"] is True for payload in payloads.values()),
        "identical_pin_sha256": len(pin_hashes) == 1,
        "identical_structured_convention_pin": convention_pin_ok,
        "source_sha256_current": all(current_source_hash_ok(payload) for payload in payloads.values()),
        "ceilings_preserved": all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is PROMOTION_ALLOWED
            and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
            for payload in payloads.values()
        ),
        "required_positive_receipts_present": REQUIRED_POSITIVE_RECEIPTS <= set(receipts),
        "required_positive_receipts_pass": all(receipts[key]["pass"] is True for key in REQUIRED_POSITIVE_RECEIPTS),
        "exact_generator_rows_eight": len(jax["bloch_generator_table"]) == 8,
        "pure_ne_A_extraction_fixed": jax["generator_consistency_gates"]["all_pass"] is True,
        "flow_round_trip_gate": jax["flow_round_trip_gates"]["all_pass"] is True,
        "fixed_set_consistency_from_exported_A_b": all(row["fixed"]["pass"] is True for row in jax["fixed_points_and_basins"].values()),
        "basin_orbit_consistency_from_exported_A_b": all(row["basin_or_orbit"]["pass"] is True for row in jax["fixed_points_and_basins"].values()),
        "cross_engine_load_bearing_rows_agree": cross_engine["all_pass"] is True,
        "flow_rows_eight": len(jax["flow_solutions"]) == 8,
        "fixed_basin_rows_eight": len(jax["fixed_points_and_basins"]) == 8,
        "gksl_all_t_proof_not_sample_only": all(row["pass"] is True for row in jax["gksl_all_t_proofs"].values())
        and all(row["sampled_only_not_all_t_proof"] is True for row in jax["sampled_choi_fixtures"].values()),
        "sampled_choi_regressions_pass": all(row["pass"] is True for row in jax["sampled_choi_fixtures"].values()),
        "negative_controls_executed_can_fail": controls["all_executed_can_fail"] is True
        and all(
            row["executed"] is True and row["expected_failure_observed"] is True and row["gate_passed_after_mutation"] is False
            for key, row in controls.items()
            if key.startswith("C")
        ),
        "pure_ne_separate_from_weak_ne": jax["ne_variant_boundary"]["pure_ne_rows"] == ["Ne_Vortex_L", "Ne_Spiral_R"]
        and jax["purity_preservation"]["weak_ne_negative_control"]["expected_failure_observed"] is True,
        "ni_nonunitality_and_non_ni_unitality": jax["nonunitality_witnesses"]["Ni_Pit_L"]["pass"] is True
        and jax["nonunitality_witnesses"]["Ni_Source_R"]["pass"] is True
        and all(
            row["pass"] is True
            for key, row in jax["nonunitality_witnesses"].items()
            if key not in {"Ni_Pit_L", "Ni_Source_R", "Ni_sign_convention"}
        ),
        "julia_density_generator_derivation_pass": julia["density_generator_derivation"]["all_pass"] is True,
        "pytorch_pinned_mirror_pass": pytorch["affine_batch"]["pass"] is True
        and pytorch["flow_and_basin"]["pass"] is True
        and "not symbolic" in pytorch["limits"],
        "smt_agreement_and_can_fail_controls": (
            jax["crossover_proofs"]["z3"]["verdict"] == "unsat"
            and jax["crossover_proofs"]["cvc5"]["verdict"] == "unsat"
            and julia["crossover_proofs"]["julia_z3"]["verdict"] == "unsat"
            and pytorch["crossover_proofs"]["z3"]["verdict"] == "unsat"
            and pytorch["crossover_proofs"]["cvc5"]["verdict"] == "unsat"
            and jax["crossover_proofs"]["z3"]["wrong_control_can_fail"]
            and jax["crossover_proofs"]["cvc5"]["wrong_control_can_fail"]
            and julia["crossover_proofs"]["julia_z3"]["wrong_control_can_fail"]
            and pytorch["crossover_proofs"]["z3"]["wrong_control_can_fail"]
            and pytorch["crossover_proofs"]["cvc5"]["wrong_control_can_fail"]
        ),
        "smt_scope_honest_pinned_entry_only": all(
            proof.get("proof_scope") == "pinned_entry_contradiction_not_full_symbolic_flow_or_basin_proof"
            for proof in [
                jax["crossover_proofs"]["z3"],
                jax["crossover_proofs"]["cvc5"],
                julia["crossover_proofs"]["julia_z3"],
                pytorch["crossover_proofs"]["z3"],
                pytorch["crossover_proofs"]["cvc5"],
            ]
        ),
        "source_locks_present": jax["source_locks"]["all_fresh"] is True,
        "julia_flow_solver_route": julia["flow_solver_route"]["all_pass"] is True,
        "jax_flow_solver_route": jax["flow_solver_route"]["all_pass"] is True,
        "copied_spec_and_directive_present": copied_inputs["s5_build_spec"]["exists"]
        and copied_inputs["s5_build_spec"]["matches_source"]
        and copied_inputs["directive_addendum"]["exists"],
        "no_peer_result_reads": all(payload["reads_peer_result"] is False for payload in payloads.values()),
        "control_only_tools_absent_from_claim_path": not ({"numpy", "scipy", "mpmath"} & set(claim_path_tools)),
        "quotient_erasure_boundary_present": "global spinor phase" in jax["quotient_erasure_note"]["erases"],
    }
    all_pass = all(gates.values())
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "Bounded S5 one-qubit terrain-generator flow packet over the source-locked density/Bloch quotient: exact A,b rows, exact flow/fixed/basin receipts, GKSL all-time CPTP boundary, pure-Ne purity, Ni non-unitality, and executed can-fail controls.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "copied_inputs": copied_inputs,
        "pin_spec": jax["pin_spec"],
        "pin_sha256": next(iter(pin_hashes)),
        "convention_pin": jax["convention_pin"],
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": julia.get("julia_project"),
            "artifact_path": rel(SIM_DIR),
            "artifact_sha256": None,
            "source_sha256": julia["source_sha256"],
            "receipt_path": julia["result_path"],
            "proof_tag": "S5_terrain_flow_julia_density_generator_derivation_z3_pinned_entry",
            "proof_pass": bool(julia["all_pass"]),
            "table_version": "geo_s5_terrain_flows_v0_source_locked_standard_bloch",
            "bracket_convention": "ordinary associative M2(C) density-generator algebra; affine Bloch flow order explicit",
            "consumer_policy": "independent engine recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia.get("julia_project"), "packages": julia["packages_used"], "role": "carrier-side density-generator derivation plus Z3 pinned-entry control"},
            "jax": {"packages": jax["packages_used"], "role": "SymPy exact A,b/flow/fixed/basin derivation plus z3/cvc5 controls"},
            "pytorch": {"packages": pytorch["packages_used"], "role": "pinned tensor/autograd mirror plus z3/cvc5 controls"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": claim_path_tools,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "source_lineage": jax["source_lineage"],
        "source_locks": jax["source_locks"],
        "se_source_vs_prior_packet_caveat": jax["se_source_vs_prior_packet_caveat"],
        "ne_variant_boundary": jax["ne_variant_boundary"],
        "positive_ledger": positive_ledger(jax),
        "receipts": receipts,
        "bloch_generator_table": jax["bloch_generator_table"],
        "flow_solutions": jax["flow_solutions"],
        "flow_round_trip_gates": jax["flow_round_trip_gates"],
        "fixed_points_and_basins": jax["fixed_points_and_basins"],
        "generator_consistency_gates": jax["generator_consistency_gates"],
        "cross_engine_consistency": cross_engine,
        "gksl_all_t_proofs": jax["gksl_all_t_proofs"],
        "sampled_choi_fixtures": jax["sampled_choi_fixtures"],
        "purity_preservation": jax["purity_preservation"],
        "nonunitality_witnesses": jax["nonunitality_witnesses"],
        "negative_controls": jax["negative_controls"],
        "flow_solver_routes": {
            "julia": julia["flow_solver_route"],
            "jax": jax["flow_solver_route"],
            "matrix_exponential_role": "exact constant-affine special-case parity check; not the primary flow-evolution claim path",
        },
        "julia_density_generator_derivation": julia["density_generator_derivation"],
        "pytorch_pinned_mirror": {
            "affine_batch": pytorch["affine_batch"],
            "flow_and_basin": pytorch["flow_and_basin"],
            "purity": pytorch["purity"],
            "unitality": pytorch["unitality"],
        },
        "crossover_proofs": {
            "z3": jax["crossover_proofs"]["z3"],
            "cvc5": jax["crossover_proofs"]["cvc5"],
            "julia_z3": julia["crossover_proofs"]["julia_z3"],
            "pytorch_z3": pytorch["crossover_proofs"]["z3"],
            "pytorch_cvc5": pytorch["crossover_proofs"]["cvc5"],
        },
        "strength_tokens": jax["strength_tokens"],
        "quotient_erasure_note": jax["quotient_erasure_note"],
        "build_gates": gates,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": 0.0, "jax": 0.0, "pytorch": cross_engine["max_abs_diff"]},
            "max_divergence": cross_engine["max_abs_diff"],
            "meaning": "maximum pinned A,b row disagreement after independent Julia/JAX/PyTorch derivations; any load-bearing row above tolerance fails the envelope",
        },
        "self_check_notice": "Builder self-checks are local sanity checks only and are not independent audit evidence.",
        "limits": "scratch_diagnostic only; no formal admission, canonical terrain-family completion, Axis-level admission, runtime closure, physics, S6 stacking, Hopf holonomy, or Matrix64 closure claim.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": rel(RESULT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
