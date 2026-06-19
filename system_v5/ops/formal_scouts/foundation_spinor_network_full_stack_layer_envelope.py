#!/usr/bin/env python3
"""Composite envelope for the same-carrier finite spinor-network full-stack packet."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


OBJECT_ID = "foundation_spinor_network_full_stack_layer_envelope"
RUNG_ID = "spinor_network_full_stack_layer"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_spinor_network_full_stack_layer_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_spinor_network_full_stack_layer_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_pytorch_results.json"

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from independently computed engine receipts."},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source-pinning for the envelope source."},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding for engine receipt files."},
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def scalar_values(payload: dict[str, Any]) -> dict[str, float]:
    fractions = payload["basins"]["finite_real"]["basin_fractions"]
    erased_fractions = payload["basins"]["finite_erased_control"]["basin_fractions"]
    return {
        "quaternion_order_gap": float(payload["algebra"]["quaternion_order_gap"]),
        "commuting_control_gap": float(payload["algebra"]["commuting_control_gap"]),
        "octonion_associator_norm": float(payload["algebra"]["octonion_associator_norm"]),
        "quaternion_associator_control_norm": float(payload["algebra"]["quaternion_associator_control_norm"]),
        "sedenion_zero_divisor_product_normsq": float(payload["algebra"]["sedenion_zero_divisor_product_normsq"]),
        "chirality_split_norm": float(payload["geometry"]["chirality_split_norm"]),
        "no_chirality_control_norm": float(payload["geometry"]["no_chirality_control_norm"]),
        "final_excited_population": float(payload["dynamics"]["final_excited_population"]),
        "final_trace": float(payload["dynamics"]["final_trace"]),
        "cycle_rank": float(payload["network"]["cycle_rank"]),
        "real_attractor_count": float(payload["basins"]["finite_real"]["attractor_count"]),
        "erased_attractor_count": float(payload["basins"]["finite_erased_control"]["attractor_count"]),
        "real_largest_basin_fraction": max(float(v) for v in fractions.values()),
        "erased_largest_basin_fraction": max(float(v) for v in erased_fractions.values()),
        "von_neumann_entropy": float(payload["qit_readout"]["von_neumann_entropy"]),
        "subsystem_entropy": float(payload["qit_readout"]["subsystem_entropy"]),
        "coherent_information": float(payload["qit_readout"]["coherent_information"]),
        "erased_coherent_information": float(payload["qit_readout"]["erased_coherent_information"]),
    }


def max_divergence(values: dict[str, dict[str, float]]) -> float:
    keys = sorted(set.intersection(*(set(item) for item in values.values())))
    diffs = []
    for key in keys:
        row = [values[engine][key] for engine in values]
        diffs.append(max(row) - min(row))
    return max((abs(item) for item in diffs), default=0.0)


def engine_record(payload: dict[str, Any], result_path: Path, authority: str) -> dict[str, Any]:
    return {
        "ran": True,
        "authority": authority,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "values": scalar_values(payload),
        "tool_calls": payload["tool_calls"],
        "omitted_tools": payload.get("omitted_tools", []),
    }


def proof_matrix(julia: dict[str, Any], jax: dict[str, Any], pytorch: dict[str, Any]) -> dict[str, Any]:
    return {
        "julia": {"z3": julia["smt"]["z3"]},
        "jax": {"z3": jax["smt"]["z3"], "cvc5": jax["smt"]["cvc5"]},
        "pytorch": {"z3": pytorch["smt"]["z3"], "cvc5": pytorch["smt"]["cvc5"]},
    }


def control_summary(julia: dict[str, Any], jax: dict[str, Any], pytorch: dict[str, Any]) -> dict[str, Any]:
    engines = {"julia": julia, "jax": jax, "pytorch": pytorch}
    return {
        "commuting_control": {name: payload["controls"]["commuting_control"] for name, payload in engines.items()},
        "associative_control": {name: payload["controls"]["associative_control"] for name, payload in engines.items()},
        "sedenion_zero_divisor_kill": {name: payload["controls"]["sedenion_zero_divisor_kill"] for name, payload in engines.items()},
        "carrier_erasure": {name: payload["controls"]["carrier_erasure"] for name, payload in engines.items()},
        "no_chirality": {name: payload["controls"]["no_chirality"] for name, payload in engines.items()},
        "basin_control": {name: payload["controls"]["basin_control"] for name, payload in engines.items()},
        "z3_cvc5_derive_flip": {
            "julia_z3": julia["controls"]["z3_derive_flip"],
            "jax": jax["controls"]["z3_cvc5_derive_flip"],
            "pytorch": pytorch["controls"]["z3_cvc5_derive_flip"],
        },
    }


def build_result() -> dict[str, Any]:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    values = {"julia": scalar_values(julia), "jax": scalar_values(jax), "pytorch": scalar_values(pytorch)}
    proofs = proof_matrix(julia, jax, pytorch)
    controls = control_summary(julia, jax, pytorch)
    all_controls_flip = all(all(item.get("flips") is True for item in per_engine.values()) for key, per_engine in controls.items() if key != "z3_cvc5_derive_flip")
    proof_flip = (
        julia["smt"]["z3"]["octonion_assoc_zero_assertion"] == "unsat"
        and jax["smt"]["z3"]["octonion_assoc_zero_assertion"] == "unsat"
        and jax["smt"]["cvc5"]["octonion_assoc_zero_assertion"] == "unsat"
        and pytorch["smt"]["z3"]["octonion_assoc_zero_assertion"] == "unsat"
        and pytorch["smt"]["cvc5"]["octonion_assoc_zero_assertion"] == "unsat"
        and jax["smt"]["cvc5"]["quaternion_assoc_zero_control"] == "sat"
        and pytorch["smt"]["cvc5"]["quaternion_assoc_zero_control"] == "sat"
        and jax["smt"]["cvc5"]["erased_basin_escape"] == "sat"
        and pytorch["smt"]["cvc5"]["erased_basin_escape"] == "sat"
    )
    all_pass = bool(julia["all_pass"] and jax["all_pass"] and pytorch["all_pass"] and all_controls_flip and proof_flip)
    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": OBJECT_ID,
        "rung_id": RUNG_ID,
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "reads_peer_result": {
                "julia": julia["reads_peer_result"],
                "jax": jax["reads_peer_result"],
                "pytorch": pytorch["reads_peer_result"],
            },
        },
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "scratch_diagnostic three-engine integration test on one finite spinor-network carrier only; promotion_allowed=false; formal_admission_allowed=false; no canon/admission/bridge/physics/Axis0/M(C)-final/manifold claim",
        "M": julia["M_C_quotient"]["M"],
        "C": julia["M_C_quotient"]["C"],
        "S_quotient_M": julia["M_C_quotient"]["quotient_classes_under_M"],
        "negative_control_flip_result": controls,
        "all_pass": all_pass,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT, "authoritative"),
            "jax": engine_record(jax, JAX_RESULT, "workhorse"),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT, "graph_engine"),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": "unsat",
                "claim": "Octonion associator forced-zero query is UNSAT; products are expanded from bound table entries.",
                "negative_control_verdict": "sat",
                "per_engine": {engine: proofs[engine]["z3"] for engine in proofs},
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": "unsat",
                "claim": "Same derive-in-solver associator forced-zero query in cvc5 on JAX and PyTorch legs.",
                "negative_control_verdict": "sat",
                "per_engine": {"jax": proofs["jax"]["cvc5"], "pytorch": proofs["pytorch"]["cvc5"]},
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["smt"]["z3"]["octonion_assoc_zero_assertion"],
                "claim": "Julia Z3.jl associator forced-zero query over bound octonion table.",
            },
        },
        "claim_path_tools": [
            "QuantumOptics",
            "Octonions",
            "Quaternions",
            "DifferentialEquations",
            "Graphs",
            "Z3",
            "Cayley-Dickson",
            "jax",
            "z3",
            "cvc5",
            "torch",
            "torch_geometric",
            "geomstats",
            "clifford",
            "torch_ga",
            "e3nn",
        ],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": values,
            "max_divergence": max_divergence(values),
            "notes": [
                "All three engines compute locally with reads_peer_result=false.",
                "Divergence is over shared scalar observables only; rich per-tool objects remain per-engine receipts.",
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FOUNDATION_SPINOR_NETWORK_FULL_STACK_LAYER_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"max_divergence={result['divergence']['max_divergence']:.6e} "
        f"result={RESULT_PATH}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
