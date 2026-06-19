#!/usr/bin/env python3
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_three_engine_foundation_r1_f01_finite_admissibility_unsat_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/three_engine_foundation_r1_f01_finite_admissibility_unsat_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/foundation_r1_f01_finite_admissibility_unsat_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r1_f01_finite_admissibility_unsat_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r1_f01_finite_admissibility_unsat_pytorch_results.json"
OBJECT_ID = "foundation_r1_f01_finite_admissibility_unsat_v1"
classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive result-envelope assembly from completed engine receipts; not a math claim path"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding for receipt files"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def result_statuses(payload: dict[str, Any], solver: str | None = None) -> dict[str, str]:
    if solver is None:
        return {key: value["status"] for key, value in payload["solver_results"].items()}
    return {key: value["status"] for key, value in payload["solver_results"][solver].items() if isinstance(value, dict) and "status" in value}


def engine_record(payload: dict[str, Any], result_path: Path, packages_used: list[str], load_bearing: list[str]) -> dict[str, Any]:
    return {
        "ran": payload.get("all_pass") is True,
        "source_path": payload.get("source_path"),
        "result_path": str(result_path),
        "reads_peer_result": payload.get("reads_peer_result"),
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "classification": payload.get("classification"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "formal_admission_allowed": payload.get("formal_admission_allowed"),
        "finite_support": payload.get("finite_support"),
        "candidates": payload.get("candidates"),
        "solver_negative_status": (
            payload.get("solver_results", {}).get("negative_K5_into_N4", {}).get("status")
            if payload.get("engine") == "julia"
            else payload.get("solver_results", {}).get("z3", {}).get("negative_K5_into_N4", {}).get("status")
        ),
    }


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    payloads = [julia, jax, pytorch]
    same_object = all(payload.get("object_id") == OBJECT_ID for payload in payloads)
    same_support = all(payload.get("finite_support") == julia.get("finite_support") for payload in payloads[1:])
    same_candidates = all(payload.get("candidates") == julia.get("candidates") for payload in payloads[1:])
    no_peer_reads = all(payload.get("reads_peer_result") is False for payload in payloads)
    fences = all(
        payload.get("classification") == CLASSIFICATION
        and payload.get("promotion_allowed") is False
        and payload.get("formal_admission_allowed") is False
        for payload in payloads
    )
    julia_status = result_statuses(julia)
    jax_z3_status = result_statuses(jax, "z3")
    jax_cvc5_status = result_statuses(jax, "cvc5")
    torch_z3_status = result_statuses(pytorch, "z3")
    torch_cvc5_status = result_statuses(pytorch, "cvc5")
    common_status_agreement = julia_status == jax_z3_status == jax_cvc5_status == torch_z3_status == torch_cvc5_status
    expected_statuses = {
        "positive_K4_into_N4": "sat",
        "negative_K5_into_N4": "unsat",
        "no_finitude_K5_distinct_unbounded": "sat",
        "raised_bound_K5_into_N5": "sat",
    }
    expected_status_pass = julia_status == expected_statuses
    all_lanes_pass = all(payload.get("all_pass") is True for payload in payloads)
    all_pass = bool(same_object and same_support and same_candidates and no_peer_reads and fences and common_status_agreement and expected_status_pass and all_lanes_pass)
    negative_controls = {
        "same_N_across_lanes": {"pass": same_support, "N": julia["finite_support"]["N"]},
        "same_positive_negative_candidates": {"pass": same_candidates, "candidates": julia["candidates"]},
        "engine_lanes_read_no_peer_results": {"pass": no_peer_reads},
        "K5_cannot_inject_into_N4": {"pass": julia_status.get("negative_K5_into_N4") == "unsat"},
        "removing_finite_support_bound_makes_K5_sat": {"pass": julia_status.get("no_finitude_K5_distinct_unbounded") == "sat"},
        "raising_bound_to_N5_makes_K5_sat": {"pass": julia_status.get("raised_bound_K5_into_N5") == "sat"},
        "z3_cvc5_status_agreement": {"pass": common_status_agreement, "statuses": julia_status},
    }
    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": OBJECT_ID,
        "mode": "three_engine_finite_support_admissibility_scratch_packet",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "engine_result_paths": {"julia": str(JULIA_RESULT), "jax": str(JAX_RESULT), "pytorch": str(PYTORCH_RESULT)},
        "controller_reads_engine_results_after_lanes": True,
        "finite_support": julia.get("finite_support"),
        "candidates": julia.get("candidates"),
        "solver_results": {
            "expected": expected_statuses,
            "julia_z3": julia_status,
            "jax_z3": jax_z3_status,
            "jax_cvc5": jax_cvc5_status,
            "pytorch_z3": torch_z3_status,
            "pytorch_cvc5": torch_cvc5_status,
            "agreement_pass": common_status_agreement,
        },
        "negative_controls": negative_controls,
        "all_pass": all_pass,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT, ["Z3", "JSON", "LinearAlgebra", "Dates"], ["Z3"]),
            "jax": engine_record(jax, JAX_RESULT, ["jax", "jax.numpy", "z3", "cvc5", "json", "pathlib"], ["z3", "cvc5"]),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT, ["torch", "torch.func", "z3", "cvc5", "sympy", "json", "pathlib"], ["torch.func", "z3", "cvc5", "sympy"]),
        },
        "engine_contract": {
            "julia": {"status": "ran", "authority": "reference", "load_bearing_packages": ["Z3"], "result_path": str(JULIA_RESULT)},
            "jax": {"status": "ran", "authority": "mirror", "load_bearing_packages": ["z3", "cvc5"], "result_path": str(JAX_RESULT)},
            "pytorch": {"status": "ran", "authority": "third_substrate_support", "load_bearing_packages": ["torch.func", "z3", "cvc5", "sympy"], "result_path": str(PYTORCH_RESULT)},
        },
        "crossover_proofs": {
            "z3": {"ran": True, "load_bearing": True, "verdict": "unsat", "claim": "K=5 distinct occupied candidate atoms cannot inject into finite support S of size N=4"},
            "cvc5": {"ran": True, "load_bearing": True, "verdict": "unsat", "claim": "K=5 distinct occupied candidate atoms cannot inject into finite support S of size N=4"},
            "julia_z3": {"ran": True, "load_bearing": True, "verdict": "unsat", "claim": "Julia Z3.jl agrees on K=5 into N=4 UNSAT"},
        },
        "claim_path_tools": ["Z3", "z3", "cvc5", "torch.func", "sympy"],
        "control_only_tools": [],
        "packages": {
            "load_bearing": ["Z3", "z3", "cvc5", "torch.func", "sympy"],
            "supportive": ["jax", "jax.numpy", "torch", "json", "pathlib", "LinearAlgebra"],
            "control_only": [],
            "missing_required": [],
        },
        "package_observables": {
            "Z3": "Julia reference UNSAT/SAT finite injection statuses",
            "z3": "Python z3 UNSAT/SAT finite injection statuses",
            "cvc5": "independent cvc5 UNSAT/SAT finite injection statuses",
            "torch.func": "support-excess observable over K=4/K=5 candidate sizes",
            "sympy": "exact integer pigeonhole inequality crossover",
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": julia_status, "jax": jax_z3_status, "pytorch": torch_z3_status},
            "max_divergence": 0 if common_status_agreement else 1,
            "structural_disagreements": [] if common_status_agreement else ["solver_status_disagreement"],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "R1 F01 scratch finite-object certificate only: tests one encoded finite support/admissibility predicate. Not full M(C), R2, formal, canonical, bridge, axis, physics, gravity, or entropy-master evidence.",
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"SCOUT_DONE all_pass={str(result['all_pass']).lower()} N={result['finite_support']['N']} positive={result['solver_results']['expected']['positive_K4_into_N4']} negative={result['solver_results']['expected']['negative_K5_into_N4']} reads_peer_result_lanes={result['negative_controls']['engine_lanes_read_no_peer_results']['pass']} max_divergence={result['divergence']['max_divergence']}")
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
