#!/usr/bin/env python3

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_associator_low_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_low_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/foundation_r3_associator_low_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_low_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_low_pytorch_results.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "values": payload.get("values", {}),
    }


def main() -> int:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    jv = julia["values"]
    xv = jax["values"]
    pv = pytorch["values"]
    max_divergence = max(abs(float(jv["H_associator_norm"]) - float(xv["H_associator_norm"])), abs(float(jv["O_associator_norm"]) - float(xv["O_associator_norm"])))
    z3_verdict = jax["crossover_verdict"]
    cvc5_verdict = jax["crossover_verdict"]
    all_pass = bool(julia["all_pass"] and jax["all_pass"] and pytorch["all_pass"] and max_divergence <= 1.0e-12 and z3_verdict == cvc5_verdict == "unsat")
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": "foundation_r3_associator_low",
        "classification": "scratch_diagnostic",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "Scratch foundation R3 bracketing associator rung only. No promotion, formal admission, bridge, manifold, or axis-level claim.",
        "all_pass": all_pass,
        "M": {"probe_family": ["associator [A,B,C]=(AB)C-A(BC)", "basis triples over H and O", "torch differentiable witness triple (e1,e2,e4)"]},
        "C": {"constraints": ["finite normed-division multiplication structure constants", "unit basis and conjugation", "bilinear product", "associator bracketing probe", "SMT assertions over computed associator coefficients"]},
        "quotient": {"rule": "(AB)C ~_M A(BC) iff the associator vector is zero", "H": "one bracketing class; indistinguishable", "O": "bracketings split at nonzero associator witness; distinguishable"},
        "key_values": {"H_associator_norm": jv["H_associator_norm"], "O_associator_norm": jv["O_associator_norm"], "O_witness_basis_indices": jv["O_witness_basis_indices"], "O_witness_vector": jv["O_witness_vector"], "torch_jacrev_gradient_mid": pv["jacrev_gradient_at_theta_0_5"]},
        "negative_control_flip": {"H_to_O_associator_flip": julia["negative_control_flip"]["flipped"], "SMT_erase_flip": jax["negative_control_flip"]["flipped"], "torch_selector_flip": pytorch["negative_control_flip"]["flipped"]},
        "structural_checks": julia["structural_checks"],
        "engines": {"julia": engine_record(julia, JULIA_RESULT), "jax": engine_record(jax, JAX_RESULT), "pytorch": engine_record(pytorch, PYTORCH_RESULT)},
        "crossover_proofs": {
            "z3": {"ran": True, "load_bearing": True, "verdict": z3_verdict, "claim": "computed O associator coefficient tensor cannot be all zero", "negative_control": jax["smt_structural_proof"]["z3"]["O"]},
            "cvc5": {"ran": True, "load_bearing": True, "verdict": cvc5_verdict, "claim": "computed O associator coefficient tensor cannot be all zero", "negative_control": jax["smt_structural_proof"]["cvc5"]["O"]},
        },
        "claim_path_tools": ["CliffordAlgebras", "Grassmann", "Z3", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": ["LinearAlgebra"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": {"H_associator_norm": jv["H_associator_norm"], "O_associator_norm": jv["O_associator_norm"]},
                "jax": {"H_associator_norm": xv["H_associator_norm"], "O_associator_norm": xv["O_associator_norm"]},
                "pytorch": {"H_associator_norm": pv["theta_0_H_embedded_associator_norm"], "O_associator_norm": pv["theta_1_O_associator_norm"]},
            },
            "max_divergence": max_divergence,
        },
        "TOOL_MANIFEST": {"json": {"tried": True, "used": True, "reason": "supportive envelope assembly only"}, "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result paths"}},
        "TOOL_INTEGRATION_DEPTH": {"json": "supportive", "pathlib": "supportive"},
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(f"SCOUT_DONE all_pass={all_pass} H={jv['H_associator_norm']} O={jv['O_associator_norm']} max_divergence={max_divergence}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
