#!/usr/bin/env python3
"""Composite envelope for the three-engine finite spinor-network basin sim."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


OBJECT_ID = "foundation_spinor_network_basins_envelope"
RUNG_ID = "spinor_network_basins"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_spinor_network_basins_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_spinor_network_basins_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_pytorch_results.json"

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from independently computed engine receipts.",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source-pinning for the envelope source.",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding for engine receipt files.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_summary(payload: dict[str, Any]) -> dict[str, float]:
    return {
        "order_gap_noncommuting": float(payload["algebra"]["order_gap_noncommuting"]),
        "order_gap_commuting_control": float(payload["algebra"]["order_gap_commuting_control"]),
        "octonion_associator_norm": float(payload["algebra"]["octonion_associator_norm"]),
        "quaternion_associator_control_norm": float(payload["algebra"]["quaternion_associator_control_norm"]),
        "real_attractor_count": float(payload["basins"]["finite_real"]["attractor_count"]),
        "control_attractor_count": float(payload["basins"]["finite_erased_control"]["attractor_count"]),
        "real_largest_basin_fraction": max(float(v) for v in payload["basins"]["finite_real"]["basin_fractions"].values()),
        "control_largest_basin_fraction": max(
            float(v) for v in payload["basins"]["finite_erased_control"]["basin_fractions"].values()
        ),
        "coherent_information": float(payload["qit_readout"]["coherent_information_q0_to_q1"]),
        "erased_coherent_information": float(payload["qit_readout"]["erased_coherent_information_q0_to_q1"]),
    }


def max_divergence(values: dict[str, dict[str, float]]) -> float:
    keys = sorted(set.intersection(*(set(v) for v in values.values())))
    diffs: list[float] = []
    for key in keys:
        vals = [values[engine][key] for engine in values]
        diffs.append(max(vals) - min(vals))
    return max(abs(x) for x in diffs) if diffs else 0.0


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
        "values": engine_summary(payload),
        "tool_calls": payload["tool_calls"],
    }


def proof_matrix(julia: dict[str, Any], jax: dict[str, Any], pytorch: dict[str, Any]) -> dict[str, Any]:
    rows = {
        "julia": julia["smt"],
        "jax": jax["smt"],
        "pytorch": pytorch["smt"],
    }
    return {
        engine: {
            solver: {
                "order_noncommuting_commute_assertion": data[solver]["order_noncommuting_commute_assertion"],
                "order_commuting_control": data[solver]["order_commuting_control"],
                "octonion_assoc_zero_assertion": data[solver]["octonion_assoc_zero_assertion"],
                "quaternion_assoc_zero_control": data[solver]["quaternion_assoc_zero_control"],
                "real_basin_counterexample": data[solver]["real_basin_counterexample"],
                "erased_basin_counterexample": data[solver]["erased_basin_counterexample"],
            }
            for solver in ("z3", "cvc5")
        }
        for engine, data in rows.items()
    }


def build_result() -> dict[str, Any]:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    values = {
        "julia": engine_summary(julia),
        "jax": engine_summary(jax),
        "pytorch": engine_summary(pytorch),
    }
    proofs = proof_matrix(julia, jax, pytorch)
    all_z3_real = all(proofs[engine]["z3"]["real_basin_counterexample"] == "unsat" for engine in proofs)
    all_cvc5_real = all(proofs[engine]["cvc5"]["real_basin_counterexample"] == "unsat" for engine in proofs)
    all_z3_erased = all(proofs[engine]["z3"]["erased_basin_counterexample"] == "sat" for engine in proofs)
    all_cvc5_erased = all(proofs[engine]["cvc5"]["erased_basin_counterexample"] == "sat" for engine in proofs)
    controls_flip = {
        "commuting_control_order_gap_to_zero": all(
            values[engine]["order_gap_noncommuting"] > 1.0 and values[engine]["order_gap_commuting_control"] <= 1.0e-9
            for engine in values
        ),
        "associative_control_associator_to_zero": all(
            values[engine]["octonion_associator_norm"] > 1.0
            and values[engine]["quaternion_associator_control_norm"] <= 1.0e-9
            for engine in values
        ),
        "basin_control_real_structured_erased_degenerate": all(
            values[engine]["real_attractor_count"] == 2.0 and values[engine]["control_attractor_count"] == 16.0
            for engine in values
        ),
        "carrier_erasure_qit_collapse": all(
            values[engine]["coherent_information"] > 0.0 and values[engine]["erased_coherent_information"] < 0.0
            for engine in values
        ),
        "drop_probe_strictly_coarsens_quotient": all(
            payload["M_C_quotient"]["drop_probe_strictly_coarsens"] is True
            for payload in (julia, jax, pytorch)
        ),
        "z3_cvc5_derive_flip_all_engines": all_z3_real and all_cvc5_real and all_z3_erased and all_cvc5_erased,
    }
    all_pass = bool(julia["all_pass"] and jax["all_pass"] and pytorch["all_pass"] and all(controls_flip.values()))
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
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": (
            "Scratch diagnostic finite spinor-network basin sim only. No canon, no formal admission, "
            "no bridge, no physics, no Axis0, no IGT truth."
        ),
        "M": julia["M_C_quotient"]["M"],
        "C": julia["M_C_quotient"]["C"],
        "S_quotient_M": {
            "quotient_classes_under_M": julia["M_C_quotient"]["quotient_classes_under_M"],
            "drop_edge03_control_classes": julia["M_C_quotient"]["drop_edge03_control_classes"],
            "drop_probe_strictly_coarsens": julia["M_C_quotient"]["drop_probe_strictly_coarsens"],
        },
        "negative_control_flip_result": controls_flip,
        "all_pass": all_pass,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT, "authoritative"),
            "jax": engine_record(jax, JAX_RESULT, "rich_mirror"),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT, "third_substrate"),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": "unsat",
                "claim": "No real-constraint finite seed escapes the two structured attractors; solver derives transition from finite state variables.",
                "negative_control_verdict": "sat",
                "per_engine": {engine: proofs[engine]["z3"] for engine in proofs},
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": "unsat",
                "claim": "Same finite basin counterexample query as z3, independently derived by cvc5 on each engine leg.",
                "negative_control_verdict": "sat",
                "per_engine": {engine: proofs[engine]["cvc5"] for engine in proofs},
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["smt"]["z3"]["real_basin_counterexample"],
                "claim": "Julia Z3.jl finite basin counterexample query.",
            },
        },
        "claim_path_tools": [
            "Quaternions",
            "Octonions",
            "CliffordAlgebras",
            "QuantumOptics",
            "Attractors",
            "DynamicalSystems",
            "DifferentialEquations",
            "Manifolds",
            "Z3",
            "cvc5",
            "jax",
            "jax.numpy",
            "diffrax",
            "dynamiqs",
            "z3",
            "cvc5",
            "sympy",
            "torch",
            "torch.func",
            "torch_ga",
            "torch_geometric",
            "geomstats",
        ],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": values,
            "max_divergence": max_divergence(values),
            "notes": [
                "All three engines compute locally with reads_peer_result=false.",
                "Envelope divergence is over scalar order, associator, basin, and QIT readout fields.",
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FOUNDATION_SPINOR_NETWORK_BASINS_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"max_divergence={result['divergence']['max_divergence']:.6e} "
        f"result={RESULT_PATH}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
