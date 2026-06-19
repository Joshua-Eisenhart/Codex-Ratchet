#!/usr/bin/env python3
"""Composite envelope for foundation_r5_hopf_fibration three-engine rung."""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r5_hopf_fibration"
OBJECT_ID = "foundation_foundation_r5_hopf_fibration_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r5_hopf_fibration_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r5_hopf_fibration_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r5_hopf_fibration_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r5_hopf_fibration_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r5_hopf_fibration_pytorch_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from three independent leg receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


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
        "values": payload["summary"],
    }


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    z3_verdict = jax["crossover_proofs"]["z3"]["verdict"]
    cvc5_verdict = jax["crossover_proofs"]["cvc5"]["verdict"]
    julia_value = float(julia["summary"]["hopf_linking_number"])
    jax_value = float(jax["summary"]["max_s2_image_norm_residual"])
    negative = {
        "hopf_linking_vs_trivial_control_flips": julia["negative_control_flip"]["Hopf_vs_trivial_linking_flips"],
        "drop_probe_coarsens_quotient": julia["negative_control_flip"]["drop_Hopf_projection_probe_coarsens_quotient"]
        and jax["negative_control_flip"]["drop_Hopf_projection_probe_coarsens_quotient"]
        and pytorch["negative_control_flip"]["drop_Hopf_projection_probe_coarsens_quotient"],
        "smt_erase_constraint_flips": jax["negative_control_flip"]["erase_s3_normalization_z3_unsat_to_sat"]
        and jax["negative_control_flip"]["erase_s3_normalization_cvc5_unsat_to_sat"],
        "torch_trivial_projection_control_flips": pytorch["negative_control_flip"]["trivial_coordinate_projection_not_fiber_invariant"],
    }
    all_pass = bool(
        julia["all_pass"]
        and jax["all_pass"]
        and pytorch["all_pass"]
        and z3_verdict == cvc5_verdict == "unsat"
        and all(negative.values())
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "classification": classification,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "Scratch diagnostic foundation rung only: Hopf S^3->S^2 projection, S^1 fibers, and linked-fiber control. No promotion, formal admission, bridge, axis, or canonical claim.",
        "all_pass": all_pass,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "M": {
            "name": "Hopf_projection_probe",
            "explicit_probe_family": [
                "h(q) = (2(ac+bd), 2(bc-ad), a^2+b^2-c^2-d^2)",
                "fiber-linking probe on two sampled Hopf fibers",
                "torch.func differential fiber-kernel probe",
            ],
        },
        "C": {
            "trace_equals_one": "rank-one q*q^T probe projectors have trace 1",
            "psd": "rank-one q*q^T probe projectors are PSD",
            "hermiticity": "rank-one q*q^T probe projectors are Hermitian",
            "normalization": "S^3 spinor constraint a^2+b^2+c^2+d^2=1",
            "rung_specific_constraint": "Hopf projection h maps S^3 to S^2 and identifies S^1 fibers",
        },
        "S_mod_M": {
            "definition": "q ~_M q' iff Hopf projection probes agree",
            "julia_classes": julia["S_mod_M"]["classes"],
            "jax_class_count": jax["S_mod_M"]["class_count"],
            "drop_probe_class_count": 1,
        },
        "substantive_values": {
            "hopf_linking_number": julia["summary"]["hopf_linking_number"],
            "hopf_linking_number_raw": julia["summary"]["hopf_linking_number_raw"],
            "trivial_control_linking_number": julia["summary"]["trivial_control_linking_number"],
            "trivial_control_linking_number_raw": julia["summary"]["trivial_control_linking_number_raw"],
            "smt_scope": jax["summary"]["smt_scope"],
            "torch_fiber_image_velocity_norm": pytorch["summary"]["fiber_image_velocity_norm"],
            "torch_trivial_projection_fiber_velocity_norm": pytorch["summary"]["trivial_projection_fiber_velocity_norm"],
        },
        "negative_control_flip": negative,
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_verdict,
                "negative_control_verdict": jax["crossover_proofs"]["z3"]["negative_control_verdict"],
                "erase_flip_verdict": jax["crossover_proofs"]["z3"]["erase_flip_verdict"],
                "claim": jax["crossover_proofs"]["z3"]["claim"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "negative_control_verdict": jax["crossover_proofs"]["cvc5"]["negative_control_verdict"],
                "erase_flip_verdict": jax["crossover_proofs"]["cvc5"]["erase_flip_verdict"],
                "claim": jax["crossover_proofs"]["cvc5"]["claim"],
            },
            "julia_scope_note": {
                "ran": True,
                "load_bearing": True,
                "verdict": "not_smt",
                "claim": "Julia computes the sampled Hopf fiber Gauss linking number; SMT is scoped to the algebraic S^2 image relation.",
            },
        },
        "claim_path_tools": ["CliffordAlgebras", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": ["LinearAlgebra"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": julia_value,
                "jax": jax_value,
                "pytorch": float(pytorch["summary"]["fiber_image_velocity_norm"]),
            },
            "max_divergence": abs(julia_value - 1.0),
            "notes": [
                "Julia value is the authoritative rounded Hopf fiber linking number.",
                "JAX value is the max S^2 image residual for its finite probe rows plus dual-SMT UNSAT proof.",
                "PyTorch value is the fiber-tangent image velocity norm from torch.func.jacrev.",
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FOUNDATION_R5_HOPF_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"hopf_linking={result['substantive_values']['hopf_linking_number']} "
        f"trivial_control={result['substantive_values']['trivial_control_linking_number']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
