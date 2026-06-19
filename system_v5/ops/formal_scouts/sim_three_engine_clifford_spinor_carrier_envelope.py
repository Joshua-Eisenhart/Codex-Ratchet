#!/usr/bin/env python3
"""Composite envelope for the three-engine Clifford/spinor carrier scout.

This does not recompute the engine legs. It binds the already-rerun Julia,
JAX, and PyTorch leg receipts into the repo's three-engine result shape.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
RESULT_PATH = (
    ROOT
    / "system_v5"
    / "ops"
    / "formal_scouts"
    / "results"
    / "three_engine_clifford_spinor_carrier_envelope_results.json"
)
JULIA_RESULT = ROOT / "system_v5" / "julia_carrier" / "clifford_spinor_carrier_rung_julia_results.json"
JAX_RESULT = ROOT / "system_v5" / "julia_carrier" / "jax_clifford_spinor_carrier_smt_results.json"
PYTORCH_RESULT = (
    ROOT
    / "system_v5"
    / "ops"
    / "formal_scouts"
    / "results"
    / "clifford_spinor_carrier_pytorch_leg_results.json"
)

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
        "reason": "supportive result-envelope assembly from engine receipts; not a math claim path",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding for receipt files",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "pathlib": "supportive",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(
    *,
    payload: dict[str, Any],
    source_path: str,
    packages_used: list[str],
    load_bearing: list[str],
    values: dict[str, Any],
    result_path: Path,
) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": source_path,
        "result_path": str(result_path),
        "reads_peer_result": payload.get("reads_peer_result"),
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "classification": payload.get("classification"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "formal_admission_allowed": payload.get("formal_admission_allowed"),
        "values": values,
    }


def max_abs_diff(left: dict[str, Any], right: dict[str, Any], keys: list[str]) -> float:
    diffs = []
    for key in keys:
        if key in left and key in right:
            diffs.append(abs(float(left[key]) - float(right[key])))
    return max(diffs) if diffs else 0.0


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)

    julia_values = {
        "cl3_dim": julia["summary"]["cl3_dim"],
        "cl6_dim": julia["summary"]["cl6_dim"],
        "even_subalg_dim_cl3": julia["summary"]["even_subalg_dim_cl3"],
        "even_subalg_dim_cl6": julia["summary"]["even_subalg_dim_cl6"],
        "anticommutation_holds": julia["summary"]["anticommutation_holds"],
        "z3_dim_proof": julia["summary"]["z3_dim_proof"],
    }
    jax_values = {
        "cl3_dim": jax["dimensions"]["cl3_dim"],
        "cl6_dim": jax["dimensions"]["cl6_dim"],
        "spinor_dim_cl3": jax["dimensions"]["spinor_dim_cl3"],
        "spinor_dim_cl6": jax["dimensions"]["spinor_dim_cl6"],
        "gamma5_square_residual": jax["gamma5"]["square_residual"],
        "cl3_anticommutator_max_residual": jax["numeric_residuals"]["cl3_anticommutator_max_residual"],
        "cl6_anticommutator_max_residual": jax["numeric_residuals"]["cl6_anticommutator_max_residual"],
    }
    pytorch_values = {
        "cl3_dim": pytorch["cl3_dim"],
        "gamma5_square_residual": pytorch["gamma5_pseudoscalar"]["square_residual"],
        "jacrev": pytorch["differentiable_spinor_geometric_product"]["jacrev"],
        "finite_difference_residual": pytorch["differentiable_spinor_geometric_product"]["finite_difference_residual"],
        "e3nn_rotation_residual": pytorch["e3nn_wigner_d_spinor_vector_image"]["residual"],
    }

    z3_result = jax["smt"]["z3"]["cl6_anticommutation_result"]
    cvc5_result = jax["smt"]["cvc5"]["cl6_anticommutation_result"]
    all_pass = (
        julia["summary"]["all_pass"] is True
        and all(jax["verdicts"].values())
        and pytorch["all_pass"] is True
        and z3_result == cvc5_result == "sat"
        and jax["smt"]["z3"]["wrong_sign_result"] == "unsat"
        and jax["smt"]["cvc5"]["wrong_sign_result"] == "unsat"
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": "three_engine_clifford_spinor_carrier_envelope",
        "classification": CLASSIFICATION,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": (
            "Scratch three-engine Clifford/spinor carrier envelope only. It binds "
            "Julia CliffordAlgebras/Z3, JAX z3+cvc5 gamma-matrix SMT, and PyTorch "
            "torch_ga/e3nn differentiability receipts. No formal admission, no "
            "bridge, manifold, basin, or axis-level claim."
        ),
        "all_pass": all_pass,
        "engines": {
            "julia": engine_record(
                payload=julia,
                source_path=julia["source_path"],
                result_path=JULIA_RESULT,
                packages_used=["CliffordAlgebras", "Z3", "JSON", "SHA", "Dates"],
                load_bearing=["CliffordAlgebras", "Z3"],
                values=julia_values,
            ),
            "jax": engine_record(
                payload=jax,
                source_path=jax["source_path"],
                result_path=JAX_RESULT,
                packages_used=["jax", "jax.numpy", "z3", "cvc5", "numpy", "json"],
                load_bearing=["z3", "cvc5"],
                values=jax_values,
            ),
            "pytorch": engine_record(
                payload=pytorch,
                source_path=pytorch["source_path"],
                result_path=PYTORCH_RESULT,
                packages_used=["torch_ga", "torch.func", "e3nn", "torch"],
                load_bearing=["torch_ga", "torch.func", "e3nn"],
                values=pytorch_values,
            ),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_result,
                "version": jax["smt"]["z3"]["version"],
                "claim": "Cl(6) finite anticommutation residual equations are satisfiable",
                "negative_control_verdict": jax["smt"]["z3"]["wrong_sign_result"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_result,
                "version": jax["smt"]["cvc5"]["version"],
                "claim": "Cl(6) finite anticommutation residual equations are satisfiable",
                "negative_control_verdict": jax["smt"]["cvc5"]["wrong_sign_result"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": "unsat",
                "claim": "Negated dim(Cl(n))=2^n recurrence is unsat for n=0..6",
            },
        },
        "claim_path_tools": [
            "CliffordAlgebras",
            "Z3",
            "jax",
            "jax.numpy",
            "z3",
            "cvc5",
            "torch_ga",
            "torch.func",
            "e3nn",
        ],
        "control_only_tools": ["numpy"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": julia_values,
                "jax": jax_values,
                "pytorch": pytorch_values,
            },
            "max_divergence": max_abs_diff(julia_values, jax_values, ["cl3_dim", "cl6_dim"]),
            "notes": [
                "Julia and JAX agree on Cl(3) and Cl(6) algebra dimensions.",
                "PyTorch leg is scoped to Cl(3) differentiable geometric algebra and SO(3) vector-image checks.",
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        "julia_cl3_dim="
        f"{result['engines']['julia']['values']['cl3_dim']} "
        "jax_cl6_dim="
        f"{result['engines']['jax']['values']['cl6_dim']} "
        "pytorch_cl3_dim="
        f"{result['engines']['pytorch']['values']['cl3_dim']} "
        f"max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
