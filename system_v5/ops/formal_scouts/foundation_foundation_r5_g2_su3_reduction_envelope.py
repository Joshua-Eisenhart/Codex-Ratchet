#!/usr/bin/env python3
"""Composite envelope for foundation_r5_g2_su3_reduction.

The envelope reads completed Julia, JAX, and PyTorch leg receipts after the
legs have run. It does not recompute the engine legs or promote the rung.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r5_g2_su3_reduction"
OBJECT_ID = "foundation_r5_g2_su3_reduction_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r5_g2_su3_reduction_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r5_g2_su3_reduction_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r5_g2_su3_reduction_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r5_g2_su3_reduction_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r5_g2_su3_reduction_pytorch_results.json"

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from completed engine receipts; not part of the algebra claim path",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding for source and result receipts",
    },
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], *, result_path: Path, values: dict[str, Any]) -> dict[str, Any]:
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
        "values": values,
    }


def values(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload["summary"]
    return {
        "der_O_dim": int(summary["der_O_dim"]),
        "fix_e1_stabilizer_dim": int(summary["fix_e1_stabilizer_dim"]),
        "fix_e1_e2_stabilizer_dim": int(summary["fix_e1_e2_stabilizer_dim"]),
        "forced_commutative_fix_e1_dim": int(summary["forced_commutative_fix_e1_dim"]),
        "unit_fix_rank": int(summary["unit_fix_rank"]),
    }


def max_divergence(engine_values: dict[str, dict[str, Any]]) -> float:
    keys = [
        "der_O_dim",
        "fix_e1_stabilizer_dim",
        "fix_e1_e2_stabilizer_dim",
        "forced_commutative_fix_e1_dim",
        "unit_fix_rank",
    ]
    diffs = []
    for key in keys:
        vals = [float(row[key]) for row in engine_values.values()]
        diffs.append(max(vals) - min(vals))
    return max(diffs)


def fences_ok(*payloads: dict[str, Any]) -> bool:
    return all(
        payload["classification"] == "scratch_diagnostic"
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        and payload["reads_peer_result"] is False
        for payload in payloads
    )


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)

    julia_values = values(julia)
    jax_values = values(jax)
    pytorch_values = values(pytorch)
    engine_values = {"julia": julia_values, "jax": jax_values, "pytorch": pytorch_values}
    div = max_divergence(engine_values)
    z3_verdict = jax["crossover_proofs"]["z3"]["verdict"]
    cvc5_verdict = jax["crossover_proofs"]["cvc5"]["verdict"]
    negative = {
        "drop_unit_fixing_probe_dim_14_vs_8": bool(
            julia["negative_control_flip"]["drop_unit_fixing_probe_dim_14_vs_8"]
            and jax["negative_control_flip"]["drop_unit_fixing_probe_dim_14_vs_8"]
            and pytorch["negative_control_flip"]["drop_unit_fixing_probe_dim_14_vs_8"]
        ),
        "drop_unit_fixing_probe_z3_unsat_to_sat": bool(jax["negative_control_flip"]["drop_unit_fixing_probe_z3_unsat_to_sat"]),
        "drop_unit_fixing_probe_cvc5_unsat_to_sat": bool(jax["negative_control_flip"]["drop_unit_fixing_probe_cvc5_unsat_to_sat"]),
        "two_independent_units_dim_changes_3_vs_8": bool(
            julia["negative_control_flip"]["two_independent_units_dim_changes_3_vs_8"]
            and jax["negative_control_flip"]["two_independent_units_dim_changes_3_vs_8"]
            and pytorch["negative_control_flip"]["two_independent_units_dim_changes_3_vs_8"]
        ),
        "forced_commutative_unit_fixing_dim_changes": bool(
            julia["negative_control_flip"]["forced_commutative_unit_fixing_dim_changes"]
            and jax["negative_control_flip"]["forced_commutative_unit_fixing_dim_changes"]
            and pytorch["negative_control_flip"]["forced_commutative_unit_fixing_dim_changes"]
        ),
        "forced_commutative_unit_fixing_dim": julia_values["forced_commutative_fix_e1_dim"],
        "torch_func_jacrev_independent_sensitivity": bool(
            pytorch["negative_control_flip"]["torch_func_jacrev_independent_sensitivity"]
        ),
    }
    all_pass = bool(
        julia["all_pass"] is True
        and jax["all_pass"] is True
        and pytorch["all_pass"] is True
        and z3_verdict == cvc5_verdict == "unsat"
        and div == 0.0
        and fences_ok(julia, jax, pytorch)
        and all(value for value in negative.values() if isinstance(value, bool))
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": reads_peer_result,
        "controller_reads_engine_results_after_lanes": True,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": (
            "Scratch foundation R5 G2-to-SU3 reduction rung only: the stabilizer "
            "inside Der(O) fixing one chosen imaginary octonion unit has dimension 8. "
            "This is a structural subalgebra dimension result only; no SM, physics, "
            "color, bridge, or promotion claim."
        ),
        "all_pass": all_pass,
        "M": {
            "name": "unit_fixing_derivation_probe",
            "explicit_probe_family": jax["M"]["explicit_probe_family"],
            "finite_probe_counts": jax["M"]["finite_probe_counts"],
            "measurement_map": "M(D) stacks all derivation residual coordinates and all coordinates of D(e1); indistinguishability is equality of this finite probe vector",
        },
        "C": {
            "trace_eq_1": bool(julia["C"]["trace_eq_1"] and jax["C"]["trace_eq_1"] and pytorch["C"]["trace_eq_1"]),
            "psd": bool(julia["C"]["psd"] and jax["C"]["psd"] and pytorch["C"]["psd"]),
            "hermitian": bool(julia["C"]["hermitian"] and jax["C"]["hermitian"] and pytorch["C"]["hermitian"]),
            "normalization": "basis probes are unit-normalized; QuantumOptics/JAX/PyTorch auxiliary guards are trace-one/PSD/Hermitian and do not determine the result",
            "rung_specific_constraint": "D is an octonion derivation and D(e1)=0 for the chosen imaginary unit e1",
        },
        "S_mod_M": {
            "definition": "S=Der(O), D ~_M D' iff M(D-D')=0; the selected quotient/stabilizer is the unit-fixing kernel inside Der(O)",
            "class_dimensions": {"Der_O": julia_values["der_O_dim"], "fix_e1": julia_values["fix_e1_stabilizer_dim"]},
            "quotient_rank": julia_values["unit_fix_rank"],
            "interpretation": "dim Der(O)=14 and dim stabilizer(e1)=8, matching the structural su(3) stabilizer dimension at scratch ceiling only",
        },
        "stabilizer_dimension_summary": {
            "der_O_dim": julia_values["der_O_dim"],
            "fix_e1_stabilizer_dim": julia_values["fix_e1_stabilizer_dim"],
            "fix_e1_e2_control_dim": julia_values["fix_e1_e2_stabilizer_dim"],
            "forced_commutative_fix_e1_control_dim": julia_values["forced_commutative_fix_e1_dim"],
            "su3_structural_dimension_only": 8,
        },
        "negative_control_flip": negative,
        "engines": {
            "julia": engine_record(julia, result_path=JULIA_RESULT, values=julia_values),
            "jax": engine_record(jax, result_path=JAX_RESULT, values=jax_values),
            "pytorch": engine_record(pytorch, result_path=PYTORCH_RESULT, values=pytorch_values),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_verdict,
                "negative_control_verdict": jax["crossover_proofs"]["z3"]["negative_control_verdict"],
                "claim": jax["crossover_proofs"]["z3"]["claim"],
                "dimension_derived_without_dim_literal": jax["smt"]["z3"]["dimension_derived_without_dim_literal"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "negative_control_verdict": jax["crossover_proofs"]["cvc5"]["negative_control_verdict"],
                "claim": jax["crossover_proofs"]["cvc5"]["claim"],
                "dimension_derived_without_dim_literal": jax["smt"]["cvc5"]["dimension_derived_without_dim_literal"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["julia_z3"]["dimension_not_expected_status"],
                "negative_control_verdict": julia["julia_z3"]["drop_unit_fixing_constraints_status"],
                "claim": julia["julia_z3"]["claim"],
            },
        },
        "claim_path_tools": [
            "QuantumOptics",
            "CliffordAlgebras",
            "Z3",
            "jax",
            "jax.numpy",
            "z3",
            "cvc5",
            "torch",
            "torch.func",
        ],
        "control_only_tools": ["json", "pathlib", "LinearAlgebra"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": div,
            "notes": [
                "Julia is authoritative for the carrier because QuantumOptics binds the finite unit probe, CliffordAlgebras checks the quaternion stage, and Z3 guards the exact unit-fixing kernel.",
                "JAX supplies z3+cvc5 structural proof over computed matrix rows, including the erase flip when D(e1)=0 is removed.",
                "PyTorch supplies torch.func.jacrev sensitivity for moving the fixed probe toward e2; it is a genuine independent differentiable check, not exact algebra authority.",
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = result["stabilizer_dimension_summary"]
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R5_G2_SU3_REDUCTION_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"dim_der_O={summary['der_O_dim']} "
        f"fix_e1_dim={summary['fix_e1_stabilizer_dim']} "
        f"two_unit_dim={summary['fix_e1_e2_control_dim']} "
        f"forced_comm_fix_dim={summary['forced_commutative_fix_e1_control_dim']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
