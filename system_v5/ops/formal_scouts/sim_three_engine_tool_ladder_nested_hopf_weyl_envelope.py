#!/usr/bin/env python3
"""Three-engine envelope for the nested Hopf/Weyl tool-ladder scout."""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
OBJECT_ID = "three_engine_tool_ladder_nested_hopf_weyl_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_three_engine_tool_ladder_nested_hopf_weyl_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/three_engine_tool_ladder_nested_hopf_weyl_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/tool_ladder_nested_hopf_weyl_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/tool_ladder_nested_hopf_weyl_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/tool_ladder_nested_hopf_weyl_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from three standalone leg receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], path: Path) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "result_path": str(path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "values": payload["values"],
    }


def max_signature_divergence(signatures: list[list[float]]) -> float:
    max_delta = 0.0
    for idx in range(len(signatures[0])):
        vals = [float(sig[idx]) for sig in signatures]
        max_delta = max(max_delta, max(vals) - min(vals))
    return max_delta


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    signatures = [julia["nested_signature"], jax["nested_signature"], pytorch["nested_signature"]]
    max_divergence = max_signature_divergence(signatures)
    reads_ok = all(payload.get("reads_peer_result") is False for payload in [julia, jax, pytorch])
    status_ok = all(
        payload.get("classification") == CLASSIFICATION
        and payload.get("promotion_allowed") is False
        and payload.get("formal_admission_allowed") is False
        for payload in [julia, jax, pytorch]
    )
    z3_verdict = jax["smt"]["z3"]["verdict"]
    cvc5_verdict = jax["smt"]["cvc5"]["verdict"]
    julia_z3_verdict = julia["julia_z3"]["main_not_expected_3_1_verdict"]
    all_pass = bool(
        julia["all_pass"]
        and jax["all_pass"]
        and pytorch["all_pass"]
        and reads_ok
        and status_ok
        and z3_verdict == cvc5_verdict == julia_z3_verdict == "unsat"
        and max_divergence <= 1.0e-9
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": OBJECT_ID,
        "classification": CLASSIFICATION,
        "evidence_level": "tool_ladder_scout",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "reads_leg_result_jsons": True,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "Scratch diagnostic tool-ladder shakedown only: validates that current Julia, JAX, and PyTorch tool stacks can carry one nested Hopf/Weyl two-layer fixture. No formal admission, no canonical claim, no proof of the larger system.",
        "all_pass": all_pass,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "two_layer_fixture": {
            "layer_1": "Hopf map h:S3->S2 with common fiber-phase invariance",
            "layer_2": "Weyl chirality split gamma7 with 4/4 left-right dimensions",
            "nesting_rule": "Hopf base z=1/2 feeds theta=acos(z)/2 so <psi(theta)|gamma7|psi(theta)>=Hopf_z",
            "negative_control": "identity chirality control flips the expected 3/1 scaled weight proof to SAT",
        },
        "substantive_values": {
            "hopf_base": julia["hopf"]["base"],
            "fiber_invariance_residuals": {
                "julia": julia["values"]["fiber_invariance_residual"],
                "jax": jax["values"]["fiber_invariance_residual"],
                "pytorch": pytorch["values"]["fiber_invariance_residual"],
            },
            "nested_chirality_expectation": {
                "julia": julia["values"]["nested_chirality_expectation"],
                "jax": jax["values"]["nested_chirality_expectation"],
                "pytorch": pytorch["values"]["nested_chirality_expectation"],
            },
            "weyl_dimensions": {"plus": julia["values"]["plus_dim"], "minus": julia["values"]["minus_dim"]},
            "pytorch_nested_jacrev": pytorch["values"]["nested_chirality_jacrev"],
            "julia_grassmann_even_basis_count": julia["values"]["grassmann_even_basis_count"],
            "jax_diffrax_phase_residual": jax["diffrax_phase_ode"]["residual"],
            "jax_quimb_mps_norm_residual": jax["quimb_mps"]["norm_residual"],
            "pytorch_geomstats_fiber_distance": pytorch["geomstats"]["s2_fiber_distance"],
            "pytorch_e3nn_vector_norm_residual": pytorch["e3nn"]["vector_norm_residual"],
            "pytorch_pyg_message_out_norm": pytorch["torch_geometric"]["message_out_norm"],
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_verdict,
                "negative_control_verdict": jax["smt"]["z3"]["negative_control_verdict"],
                "claim": jax["smt"]["z3"]["claim"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "negative_control_verdict": jax["smt"]["cvc5"]["negative_control_verdict"],
                "claim": jax["smt"]["cvc5"]["claim"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia_z3_verdict,
                "negative_control_verdict": julia["julia_z3"]["identity_control_not_expected_3_1_verdict"],
                "claim": "Julia-side Z3 proves the same scaled nested Hopf-to-Weyl weights and identity-control flip.",
            },
        },
        "negative_control_flip": {
            "z3_identity_control_flips": jax["smt"]["z3"]["identity_control_flips"],
            "cvc5_identity_control_flips": jax["smt"]["cvc5"]["identity_control_flips"],
            "julia_z3_identity_control_flips": julia["julia_z3"]["identity_control_flips"],
        },
        "claim_path_tools": [
            "QuantumOptics",
            "CliffordAlgebras",
            "Grassmann",
            "Z3",
            "z3",
            "cvc5",
            "diffrax",
            "quimb",
            "torch_ga",
            "torch.func",
            "geomstats",
            "e3nn",
            "torch_geometric",
        ],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": julia["values"],
                "jax": jax["values"],
                "pytorch": pytorch["values"],
            },
            "max_divergence": max_divergence,
            "structural_disagreements": [],
            "interpretation": "Agreement is only over this finite nested Hopf/Weyl tool fixture. It validates tool-stack execution, not system-level truth.",
        },
        "peer_json_rule": "Engine legs have reads_peer_result=false. This envelope is the only peer-result reader.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "THREE_ENGINE_NESTED_HOPF_WEYL_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"max_divergence={result['divergence']['max_divergence']} "
        f"hopf_z={result['substantive_values']['hopf_base'][2]} "
        f"dims={result['substantive_values']['weyl_dimensions']['plus']}/{result['substantive_values']['weyl_dimensions']['minus']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
