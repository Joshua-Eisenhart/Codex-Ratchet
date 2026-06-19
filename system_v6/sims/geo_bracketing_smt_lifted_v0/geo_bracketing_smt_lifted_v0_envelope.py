#!/usr/bin/env python3
"""Envelope for geo_bracketing_smt_lifted_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "geo_bracketing_smt_lifted_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_leg(engine: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{SIM_ID}_{engine}_results.json"
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": payload["result_path"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "reads_peer_result": payload["reads_peer_result"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "role_id": payload["role_id"],
        "pin_sha256": payload["pin_sha256"],
        "seed": payload["seed"],
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
        "tool_calls": payload.get("tool_calls", []),
        "acceptance": payload["acceptance"],
        "values": payload["values"],
        "n4_source_refs": payload["n4_source_refs"],
        "n4_values": payload["n4_values"],
        "n4_raw_object": payload["n4_raw_object"],
        "n4_positive": payload["n4_positive"],
        "n4_negative": payload["n4_negative"],
        "n4_boundary": payload["n4_boundary"],
        "n5_source_refs": payload["n5_source_refs"],
        "n5_values": payload["n5_values"],
        "n5_raw_object": payload["n5_raw_object"],
        "n5_positive": payload["n5_positive"],
        "n5_negative": payload["n5_negative"],
        "n5_boundary": payload["n5_boundary"],
        "n6_source_refs": payload["n6_source_refs"],
        "n6_values": payload["n6_values"],
        "n6_raw_object": payload["n6_raw_object"],
        "n6_positive": payload["n6_positive"],
        "n6_negative": payload["n6_negative"],
        "n6_boundary": payload["n6_boundary"],
        "n7_source_refs": payload["n7_source_refs"],
        "n7_values": payload["n7_values"],
        "n7_raw_object": payload["n7_raw_object"],
        "n7_positive": payload["n7_positive"],
        "n7_negative": payload["n7_negative"],
        "n7_boundary": payload["n7_boundary"],
        "n8_source_refs": payload["n8_source_refs"],
        "n8_values": payload["n8_values"],
        "n8_raw_object": payload["n8_raw_object"],
        "n8_positive": payload["n8_positive"],
        "n8_negative": payload["n8_negative"],
        "n8_boundary": payload["n8_boundary"],
    }


def source_hash_fresh(payload: dict[str, Any]) -> bool:
    source_path = ROOT / payload["source_path"]
    return source_path.exists() and sha256_file(source_path) == payload["source_sha256"]


def result_hashes(legs: dict[str, dict[str, Any]]) -> dict[str, str]:
    return {engine: sha256_file(ROOT / payload["result_path"]) for engine, payload in legs.items()}


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    keys = ["lifted_gap_squared_num", "lifted_gap_squared_den", "lifted_gap_decimal", "erased_gap_squared", "matrix_associator_norm"]
    engine_values = {engine: {key: float(payload["values"][key]) for key in keys} for engine, payload in legs.items()}
    rows = []
    max_div = 0.0
    max_key = None
    for key in keys:
        values = {engine: engine_values[engine][key] for engine in legs}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_div:
            max_div = diff
            max_key = key
    return {
        "julia_authoritative": True,
        "engine_values": engine_values,
        "max_divergence": max_div,
        "max_divergence_key": max_key,
        "comparison": {"rows": rows, "within_tolerance": max_div <= 1.0e-12, "same_named_observable_sets": True},
    }


def n4_divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    keys = ["lifted_gap_squared_num", "lifted_gap_squared_den", "lifted_gap_decimal", "erased_gap_squared", "matrix_associator_norm"]
    engine_values = {engine: {key: float(payload["n4_values"][key]) for key in keys} for engine, payload in legs.items()}
    rows = []
    max_div = 0.0
    max_key = None
    for key in keys:
        values = {engine: engine_values[engine][key] for engine in legs}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_div:
            max_div = diff
            max_key = key
    return {
        "julia_authoritative": True,
        "engine_values": engine_values,
        "max_divergence": max_div,
        "max_divergence_key": max_key,
        "comparison": {"rows": rows, "within_tolerance": max_div <= 1.0e-12, "same_named_observable_sets": True},
    }


def n5_divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    keys = ["lifted_gap_squared_num", "lifted_gap_squared_den", "lifted_gap_decimal", "erased_gap_squared", "matrix_associator_norm"]
    engine_values = {engine: {key: float(payload["n5_values"][key]) for key in keys} for engine, payload in legs.items()}
    rows = []
    max_div = 0.0
    max_key = None
    for key in keys:
        values = {engine: engine_values[engine][key] for engine in legs}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_div:
            max_div = diff
            max_key = key
    return {
        "julia_authoritative": True,
        "engine_values": engine_values,
        "max_divergence": max_div,
        "max_divergence_key": max_key,
        "comparison": {"rows": rows, "within_tolerance": max_div <= 1.0e-12, "same_named_observable_sets": True},
    }


def n6_divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    keys = ["lifted_gap_squared_num", "lifted_gap_squared_den", "lifted_gap_decimal", "erased_gap_squared", "matrix_associator_norm"]
    engine_values = {engine: {key: float(payload["n6_values"][key]) for key in keys} for engine, payload in legs.items()}
    rows = []
    max_div = 0.0
    max_key = None
    for key in keys:
        values = {engine: engine_values[engine][key] for engine in legs}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_div:
            max_div = diff
            max_key = key
    return {
        "julia_authoritative": True,
        "engine_values": engine_values,
        "max_divergence": max_div,
        "max_divergence_key": max_key,
        "comparison": {"rows": rows, "within_tolerance": max_div <= 1.0e-12, "same_named_observable_sets": True},
    }


def n7_divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    keys = ["lifted_gap_squared_num", "lifted_gap_squared_den", "lifted_gap_decimal", "erased_gap_squared", "matrix_associator_norm"]
    engine_values = {engine: {key: float(payload["n7_values"][key]) for key in keys} for engine, payload in legs.items()}
    rows = []
    max_div = 0.0
    max_key = None
    for key in keys:
        values = {engine: engine_values[engine][key] for engine in legs}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_div:
            max_div = diff
            max_key = key
    return {
        "julia_authoritative": True,
        "engine_values": engine_values,
        "max_divergence": max_div,
        "max_divergence_key": max_key,
        "comparison": {"rows": rows, "within_tolerance": max_div <= 1.0e-12, "same_named_observable_sets": True},
    }


def n8_divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    keys = ["lifted_gap_squared_num", "lifted_gap_squared_den", "lifted_gap_decimal", "erased_gap_squared", "matrix_associator_norm"]
    engine_values = {engine: {key: float(payload["n8_values"][key]) for key in keys} for engine, payload in legs.items()}
    rows = []
    max_div = 0.0
    max_key = None
    for key in keys:
        values = {engine: engine_values[engine][key] for engine in legs}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_div:
            max_div = diff
            max_key = key
    return {
        "julia_authoritative": True,
        "engine_values": engine_values,
        "max_divergence": max_div,
        "max_divergence_key": max_key,
        "comparison": {"rows": rows, "within_tolerance": max_div <= 1.0e-12, "same_named_observable_sets": True},
    }


def build_result() -> dict[str, Any]:
    legs = {engine: load_leg(engine) for engine in ("julia", "jax")}
    div = divergence(legs)
    n4_div = n4_divergence(legs)
    n5_div = n5_divergence(legs)
    n6_div = n6_divergence(legs)
    n7_div = n7_divergence(legs)
    n8_div = n8_divergence(legs)
    jax = legs["jax"]
    julia = legs["julia"]
    z3_proof = jax["crossover_proofs"]["z3"]
    cvc5_proof = jax["crossover_proofs"]["cvc5"]
    julia_z3 = julia["crossover_proofs"]["julia_z3"]
    n4_z3_proof = jax["n4_crossover_proofs"]["z3"]
    n4_cvc5_proof = jax["n4_crossover_proofs"]["cvc5"]
    n4_julia_z3 = julia["n4_crossover_proofs"]["julia_z3"]
    n5_z3_proof = jax["n5_crossover_proofs"]["z3"]
    n5_cvc5_proof = jax["n5_crossover_proofs"]["cvc5"]
    n5_julia_z3 = julia["n5_crossover_proofs"]["julia_z3"]
    n6_z3_proof = jax["n6_crossover_proofs"]["z3"]
    n6_cvc5_proof = jax["n6_crossover_proofs"]["cvc5"]
    n6_julia_z3 = julia["n6_crossover_proofs"]["julia_z3"]
    n7_z3_proof = jax["n7_crossover_proofs"]["z3"]
    n7_cvc5_proof = jax["n7_crossover_proofs"]["cvc5"]
    n7_julia_z3 = julia["n7_crossover_proofs"]["julia_z3"]
    n8_z3_proof = jax["n8_crossover_proofs"]["z3"]
    n8_cvc5_proof = jax["n8_crossover_proofs"]["cvc5"]
    n8_julia_z3 = julia["n8_crossover_proofs"]["julia_z3"]
    gate_pass = {
        "legs_all_pass": all(payload["all_pass"] is True for payload in legs.values()),
        "pin_identical": len({payload["pin_sha256"] for payload in legs.values()}) == 1,
        "seeds_declared_identical": len({payload["seed"] for payload in legs.values()}) == 1,
        "source_hashes_fresh": all(source_hash_fresh(payload) for payload in legs.values()),
        "ceiling_exact": all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is PROMOTION_ALLOWED
            and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
            for payload in legs.values()
        ),
        "no_peer_result_reads": all(payload["reads_peer_result"] is False for payload in legs.values()),
        "positive_z3_cvc5_agree_unsat": z3_proof["verdict"] == "unsat" and cvc5_proof["verdict"] == "unsat",
        "erased_control_flips_sat": z3_proof["erased_control_verdict"] == "sat" and cvc5_proof["erased_control_verdict"] == "sat",
        "unit_killed_nonzero_unsat": z3_proof["unit_killed_nonzero_verdict"] == "unsat" and cvc5_proof["unit_killed_nonzero_verdict"] == "unsat",
        "julia_z3_mirror_positive_unsat": julia_z3["verdict"] == "unsat",
        "julia_z3_mirror_erased_flip": julia_z3["erased_control_verdict"] == "sat",
        "julia_z3_mirror_unit_boundary": julia_z3["unit_killed_nonzero_verdict"] == "unsat",
        "sympy_exact_crosscheck": jax["sympy_exact_crosscheck"]["pass"] is True,
        "divergence_ok": div["comparison"]["within_tolerance"],
        "n4_positive_z3_cvc5_agree_unsat": n4_z3_proof["verdict"] == "unsat" and n4_cvc5_proof["verdict"] == "unsat",
        "n4_erased_control_flips_sat": n4_z3_proof["erased_control_verdict"] == "sat" and n4_cvc5_proof["erased_control_verdict"] == "sat",
        "n4_unit_killed_nonzero_unsat": n4_z3_proof["unit_killed_nonzero_verdict"] == "unsat" and n4_cvc5_proof["unit_killed_nonzero_verdict"] == "unsat",
        "n4_julia_z3_mirror_positive_unsat": n4_julia_z3["verdict"] == "unsat",
        "n4_julia_z3_mirror_erased_flip": n4_julia_z3["erased_control_verdict"] == "sat",
        "n4_julia_z3_mirror_unit_boundary": n4_julia_z3["unit_killed_nonzero_verdict"] == "unsat",
        "n4_sympy_exact_crosscheck": jax["n4_sympy_exact_crosscheck"]["pass"] is True,
        "n4_divergence_ok": n4_div["comparison"]["within_tolerance"],
        "n4_read_only_imports_present": jax["acceptance"]["n4_read_only_imports_present"] is True
        and julia["acceptance"]["n4_read_only_imports_present"] is True,
        "n5_positive_z3_cvc5_agree_unsat": n5_z3_proof["verdict"] == "unsat" and n5_cvc5_proof["verdict"] == "unsat",
        "n5_erased_control_flips_sat": n5_z3_proof["erased_control_verdict"] == "sat" and n5_cvc5_proof["erased_control_verdict"] == "sat",
        "n5_unit_killed_nonzero_unsat": n5_z3_proof["unit_killed_nonzero_verdict"] == "unsat" and n5_cvc5_proof["unit_killed_nonzero_verdict"] == "unsat",
        "n5_julia_z3_mirror_positive_unsat": n5_julia_z3["verdict"] == "unsat",
        "n5_julia_z3_mirror_erased_flip": n5_julia_z3["erased_control_verdict"] == "sat",
        "n5_julia_z3_mirror_unit_boundary": n5_julia_z3["unit_killed_nonzero_verdict"] == "unsat",
        "n5_sympy_exact_crosscheck": jax["n5_sympy_exact_crosscheck"]["pass"] is True,
        "n5_divergence_ok": n5_div["comparison"]["within_tolerance"],
        "n5_read_only_imports_present": jax["acceptance"]["n5_read_only_imports_present"] is True
        and julia["acceptance"]["n5_read_only_imports_present"] is True,
        "n6_positive_z3_cvc5_agree_unsat": n6_z3_proof["verdict"] == "unsat" and n6_cvc5_proof["verdict"] == "unsat",
        "n6_erased_control_flips_sat": n6_z3_proof["erased_control_verdict"] == "sat" and n6_cvc5_proof["erased_control_verdict"] == "sat",
        "n6_unit_killed_nonzero_unsat": n6_z3_proof["unit_killed_nonzero_verdict"] == "unsat" and n6_cvc5_proof["unit_killed_nonzero_verdict"] == "unsat",
        "n6_julia_z3_mirror_positive_unsat": n6_julia_z3["verdict"] == "unsat",
        "n6_julia_z3_mirror_erased_flip": n6_julia_z3["erased_control_verdict"] == "sat",
        "n6_julia_z3_mirror_unit_boundary": n6_julia_z3["unit_killed_nonzero_verdict"] == "unsat",
        "n6_sympy_exact_crosscheck": jax["n6_sympy_exact_crosscheck"]["pass"] is True,
        "n6_divergence_ok": n6_div["comparison"]["within_tolerance"],
        "n6_read_only_imports_present": jax["acceptance"]["n6_read_only_imports_present"] is True
        and julia["acceptance"]["n6_read_only_imports_present"] is True,
        "n7_positive_z3_cvc5_agree_unsat": n7_z3_proof["verdict"] == "unsat" and n7_cvc5_proof["verdict"] == "unsat",
        "n7_erased_control_flips_sat": n7_z3_proof["erased_control_verdict"] == "sat" and n7_cvc5_proof["erased_control_verdict"] == "sat",
        "n7_unit_killed_nonzero_unsat": n7_z3_proof["unit_killed_nonzero_verdict"] == "unsat" and n7_cvc5_proof["unit_killed_nonzero_verdict"] == "unsat",
        "n7_julia_z3_mirror_positive_unsat": n7_julia_z3["verdict"] == "unsat",
        "n7_julia_z3_mirror_erased_flip": n7_julia_z3["erased_control_verdict"] == "sat",
        "n7_julia_z3_mirror_unit_boundary": n7_julia_z3["unit_killed_nonzero_verdict"] == "unsat",
        "n7_sympy_exact_crosscheck": jax["n7_sympy_exact_crosscheck"]["pass"] is True,
        "n7_divergence_ok": n7_div["comparison"]["within_tolerance"],
        "n7_read_only_imports_present": jax["acceptance"]["n7_read_only_imports_present"] is True
        and julia["acceptance"]["n7_read_only_imports_present"] is True,
        "n8_positive_z3_cvc5_agree_unsat": n8_z3_proof["verdict"] == "unsat" and n8_cvc5_proof["verdict"] == "unsat",
        "n8_erased_control_flips_sat": n8_z3_proof["erased_control_verdict"] == "sat" and n8_cvc5_proof["erased_control_verdict"] == "sat",
        "n8_unit_killed_nonzero_unsat": n8_z3_proof["unit_killed_nonzero_verdict"] == "unsat" and n8_cvc5_proof["unit_killed_nonzero_verdict"] == "unsat",
        "n8_julia_z3_mirror_positive_unsat": n8_julia_z3["verdict"] == "unsat",
        "n8_julia_z3_mirror_erased_flip": n8_julia_z3["erased_control_verdict"] == "sat",
        "n8_julia_z3_mirror_unit_boundary": n8_julia_z3["unit_killed_nonzero_verdict"] == "unsat",
        "n8_sympy_exact_crosscheck": jax["n8_sympy_exact_crosscheck"]["pass"] is True,
        "n8_divergence_ok": n8_div["comparison"]["within_tolerance"],
        "n8_read_only_imports_present": jax["acceptance"]["n8_read_only_imports_present"] is True
        and julia["acceptance"]["n8_read_only_imports_present"] is True,
        "pytorch_not_scoped": True,
    }
    all_pass = all(gate_pass.values())
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "claim": "On the committed n=3 raw object and extension-built committed n=4/n5/n6/n7/n8 raw objects, z3 and cvc5 derive that lifted path grouping equality is UNSAT, while the density-erased quotient flips to SAT. The unit anti-associativity boundary kills every nonzero a.",
        "allowed_claims": [
            "G5 scratch diagnostic closed for n=3 only",
            "extension-built n=4 raw-object bracketing rows pending re-audit",
            "extension-built n=5 raw-object bracketing rows pending re-audit",
            "extension-built n=6 raw-object bracketing rows pending re-audit",
            "extension-built n=7 raw-object bracketing rows pending re-audit",
            "extension-built n=8 raw-object bracketing rows pending re-audit",
            "z3 and cvc5 agree on lifted raw-object bracketing polarity",
            "density-erased control flips to zero-gap satisfiable polarity",
            "Julia Z3.jl mirrors the positive, erased, and boundary polarities",
        ],
        "disallowed_claims": [
            "stage closure",
            "audited n=4 closure",
            "audited n=5 closure",
            "audited n=6 closure",
            "audited n=7 closure",
            "audited n=8 closure",
            "formal admission",
            "canonical proof beyond scratch diagnostic",
            "PyTorch graph/autograd evidence",
        ],
        "pin_block": jax["pin_block"],
        "pin_spec": jax["pin_spec"],
        "pin_sha256": jax["pin_sha256"],
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "engine_result_sha256": result_hashes(legs),
        "engine_contract": {
            "mode": "julia_canon_plus_jax_diagnostic",
            "lanes": ["julia", "jax"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
            "reads_peer_result": False,
            "pytorch": {
                "status": "not_scoped",
                "reason": "No graph/network/autograd/PyTorch-native role exists for this finite raw-object SMT bracketing proof.",
            },
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": julia.get("julia_project"),
            "role": "Julia strict-carrier Z3.jl mirror owns the canon-side SMT polarity check; Python/JAX-side performs z3+cvc5+sympy diagnostic proof.",
            "classification": CLASSIFICATION,
            "proof_tag": "geo_bracketing_smt_lifted_v0_raw_object_flip",
            "proof_pass": gate_pass["julia_z3_mirror_positive_unsat"] and gate_pass["julia_z3_mirror_erased_flip"],
            "bracket_convention": "n=3 uses lifted path composition order e01->e12 versus e12->e01; n=4, n=5, n=6, n=7, and n=8 extensions use e01->e12->e23 versus e23->e12->e01; density quotient erases path order",
            "consumer_policy": "read-only consumption of committed n=3, n=4, n=5, n=6, n=7, and n=8 exported JSONs; no promotion beyond scratch diagnostic",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia.get("julia_project"), "packages": julia["packages_used"], "role": "semantic_owner_z3_mirror"},
            "jax": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": jax["packages_used"], "role": "z3_cvc5_sympy_diagnostic"},
            "pytorch": {"status": "not_scoped", "packages": [], "role": "none"},
            "tensor_exchange": "none; engines independently read the same committed n=3, n=4, n=5, n=6, n=7, and n=8 JSON exports",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": sorted(set(julia["claim_path_tools"] + jax["claim_path_tools"])),
        "TOOL_MANIFEST": {engine: legs[engine]["TOOL_MANIFEST"] for engine in legs},
        "TOOL_INTEGRATION_DEPTH": {engine: legs[engine]["TOOL_INTEGRATION_DEPTH"] for engine in legs},
        "engines": {engine: engine_record(payload) for engine, payload in legs.items()},
        "positive": {
            "lifted_raw_object": jax["positive"],
            "julia_z3_mirror": julia["positive"],
            "pass": gate_pass["positive_z3_cvc5_agree_unsat"] and gate_pass["julia_z3_mirror_positive_unsat"],
        },
        "negative": {
            "density_quotient_erased_control": jax["negative"],
            "julia_z3_mirror": julia["negative"],
            "pass": gate_pass["erased_control_flips_sat"] and gate_pass["julia_z3_mirror_erased_flip"],
        },
        "n4_positive": {
            "lifted_raw_object": jax["n4_positive"],
            "julia_z3_mirror": julia["n4_positive"],
            "pass": gate_pass["n4_positive_z3_cvc5_agree_unsat"] and gate_pass["n4_julia_z3_mirror_positive_unsat"],
        },
        "n4_negative": {
            "density_quotient_erased_control": jax["n4_negative"],
            "julia_z3_mirror": julia["n4_negative"],
            "pass": gate_pass["n4_erased_control_flips_sat"] and gate_pass["n4_julia_z3_mirror_erased_flip"],
        },
        "n5_positive": {
            "lifted_raw_object": jax["n5_positive"],
            "julia_z3_mirror": julia["n5_positive"],
            "pass": gate_pass["n5_positive_z3_cvc5_agree_unsat"] and gate_pass["n5_julia_z3_mirror_positive_unsat"],
        },
        "n5_negative": {
            "density_quotient_erased_control": jax["n5_negative"],
            "julia_z3_mirror": julia["n5_negative"],
            "pass": gate_pass["n5_erased_control_flips_sat"] and gate_pass["n5_julia_z3_mirror_erased_flip"],
        },
        "n6_positive": {
            "lifted_raw_object": jax["n6_positive"],
            "julia_z3_mirror": julia["n6_positive"],
            "pass": gate_pass["n6_positive_z3_cvc5_agree_unsat"] and gate_pass["n6_julia_z3_mirror_positive_unsat"],
        },
        "n6_negative": {
            "density_quotient_erased_control": jax["n6_negative"],
            "julia_z3_mirror": julia["n6_negative"],
            "pass": gate_pass["n6_erased_control_flips_sat"] and gate_pass["n6_julia_z3_mirror_erased_flip"],
        },
        "n7_positive": {
            "lifted_raw_object": jax["n7_positive"],
            "julia_z3_mirror": julia["n7_positive"],
            "pass": gate_pass["n7_positive_z3_cvc5_agree_unsat"] and gate_pass["n7_julia_z3_mirror_positive_unsat"],
        },
        "n7_negative": {
            "density_quotient_erased_control": jax["n7_negative"],
            "julia_z3_mirror": julia["n7_negative"],
            "pass": gate_pass["n7_erased_control_flips_sat"] and gate_pass["n7_julia_z3_mirror_erased_flip"],
        },
        "n8_positive": {
            "lifted_raw_object": jax["n8_positive"],
            "julia_z3_mirror": julia["n8_positive"],
            "pass": gate_pass["n8_positive_z3_cvc5_agree_unsat"] and gate_pass["n8_julia_z3_mirror_positive_unsat"],
        },
        "n8_negative": {
            "density_quotient_erased_control": jax["n8_negative"],
            "julia_z3_mirror": julia["n8_negative"],
            "pass": gate_pass["n8_erased_control_flips_sat"] and gate_pass["n8_julia_z3_mirror_erased_flip"],
        },
        "boundary": {
            "unit_killed_anti_associativity": jax["boundary"],
            "julia_z3_mirror": julia["boundary"],
            "pass": gate_pass["unit_killed_nonzero_unsat"] and gate_pass["julia_z3_mirror_unit_boundary"],
        },
        "n4_boundary": {
            "unit_killed_anti_associativity": jax["n4_boundary"],
            "julia_z3_mirror": julia["n4_boundary"],
            "pass": gate_pass["n4_unit_killed_nonzero_unsat"] and gate_pass["n4_julia_z3_mirror_unit_boundary"],
        },
        "n5_boundary": {
            "unit_killed_anti_associativity": jax["n5_boundary"],
            "julia_z3_mirror": julia["n5_boundary"],
            "pass": gate_pass["n5_unit_killed_nonzero_unsat"] and gate_pass["n5_julia_z3_mirror_unit_boundary"],
        },
        "n6_boundary": {
            "unit_killed_anti_associativity": jax["n6_boundary"],
            "julia_z3_mirror": julia["n6_boundary"],
            "pass": gate_pass["n6_unit_killed_nonzero_unsat"] and gate_pass["n6_julia_z3_mirror_unit_boundary"],
        },
        "n7_boundary": {
            "unit_killed_anti_associativity": jax["n7_boundary"],
            "julia_z3_mirror": julia["n7_boundary"],
            "pass": gate_pass["n7_unit_killed_nonzero_unsat"] and gate_pass["n7_julia_z3_mirror_unit_boundary"],
        },
        "n8_boundary": {
            "unit_killed_anti_associativity": jax["n8_boundary"],
            "julia_z3_mirror": julia["n8_boundary"],
            "pass": gate_pass["n8_unit_killed_nonzero_unsat"] and gate_pass["n8_julia_z3_mirror_unit_boundary"],
        },
        "raw_object": jax["raw_object"],
        "n4_raw_object": jax["n4_raw_object"],
        "n5_raw_object": jax["n5_raw_object"],
        "n6_raw_object": jax["n6_raw_object"],
        "n7_raw_object": jax["n7_raw_object"],
        "n8_raw_object": jax["n8_raw_object"],
        "gate_pass": gate_pass,
        "crossover_proofs": {
            "z3": z3_proof,
            "cvc5": cvc5_proof,
            "julia_z3": julia_z3,
        },
        "n4_crossover_proofs": {
            "z3": n4_z3_proof,
            "cvc5": n4_cvc5_proof,
            "julia_z3": n4_julia_z3,
        },
        "n5_crossover_proofs": {
            "z3": n5_z3_proof,
            "cvc5": n5_cvc5_proof,
            "julia_z3": n5_julia_z3,
        },
        "n6_crossover_proofs": {
            "z3": n6_z3_proof,
            "cvc5": n6_cvc5_proof,
            "julia_z3": n6_julia_z3,
        },
        "n7_crossover_proofs": {
            "z3": n7_z3_proof,
            "cvc5": n7_cvc5_proof,
            "julia_z3": n7_julia_z3,
        },
        "n8_crossover_proofs": {
            "z3": n8_z3_proof,
            "cvc5": n8_cvc5_proof,
            "julia_z3": n8_julia_z3,
        },
        "divergence": div,
        "n4_divergence": n4_div,
        "n5_divergence": n5_div,
        "n6_divergence": n6_div,
        "n7_divergence": n7_div,
        "n8_divergence": n8_div,
        "source_refs": {
            "n3_jax_result": jax["source_refs"]["n3_jax_result"],
            "n3_julia_result": jax["source_refs"]["n3_julia_result"],
            "n3_jax_sha256": jax["source_refs"]["n3_jax_sha256"],
            "n3_julia_sha256": jax["source_refs"]["n3_julia_sha256"],
            "n4_jax_result": jax["n4_source_refs"]["n4_jax_result"],
            "n4_julia_result": jax["n4_source_refs"]["n4_julia_result"],
            "n4_jax_sha256": jax["n4_source_refs"]["n4_jax_sha256"],
            "n4_julia_sha256": jax["n4_source_refs"]["n4_julia_sha256"],
            "n4_support_field": jax["n4_source_refs"]["n4_support_field"],
            "n4_boundary_field": jax["n4_source_refs"]["n4_boundary_field"],
            "n4_path_lineage": jax["n4_source_refs"]["n4_path_lineage"],
            "n5_jax_result": jax["n5_source_refs"]["n5_jax_result"],
            "n5_julia_result": jax["n5_source_refs"]["n5_julia_result"],
            "n5_jax_sha256": jax["n5_source_refs"]["n5_jax_sha256"],
            "n5_julia_sha256": jax["n5_source_refs"]["n5_julia_sha256"],
            "n5_support_field": jax["n5_source_refs"]["n5_support_field"],
            "n5_boundary_field": jax["n5_source_refs"]["n5_boundary_field"],
            "n5_path_lineage": jax["n5_source_refs"]["n5_path_lineage"],
            "n6_jax_result": jax["n6_source_refs"]["n6_jax_result"],
            "n6_julia_result": jax["n6_source_refs"]["n6_julia_result"],
            "n6_jax_sha256": jax["n6_source_refs"]["n6_jax_sha256"],
            "n6_julia_sha256": jax["n6_source_refs"]["n6_julia_sha256"],
            "n6_support_field": jax["n6_source_refs"]["n6_support_field"],
            "n6_boundary_field": jax["n6_source_refs"]["n6_boundary_field"],
            "n6_path_lineage": jax["n6_source_refs"]["n6_path_lineage"],
            "n7_jax_result": jax["n7_source_refs"]["n7_jax_result"],
            "n7_julia_result": jax["n7_source_refs"]["n7_julia_result"],
            "n7_jax_sha256": jax["n7_source_refs"]["n7_jax_sha256"],
            "n7_julia_sha256": jax["n7_source_refs"]["n7_julia_sha256"],
            "n7_support_field": jax["n7_source_refs"]["n7_support_field"],
            "n7_boundary_field": jax["n7_source_refs"]["n7_boundary_field"],
            "n7_path_lineage": jax["n7_source_refs"]["n7_path_lineage"],
            "n8_jax_result": jax["n8_source_refs"]["n8_jax_result"],
            "n8_julia_result": jax["n8_source_refs"]["n8_julia_result"],
            "n8_jax_sha256": jax["n8_source_refs"]["n8_jax_sha256"],
            "n8_julia_sha256": jax["n8_source_refs"]["n8_julia_sha256"],
            "n8_support_field": jax["n8_source_refs"]["n8_support_field"],
            "n8_boundary_field": jax["n8_source_refs"]["n8_boundary_field"],
            "n8_path_lineage": jax["n8_source_refs"]["n8_path_lineage"],
            "audit_gap": "system_v6/sims/stage_lifted_spinor_shell_n3_v0/audit_verdict.md#G5",
        },
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": str(RESULT_PATH.relative_to(ROOT))}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
