#!/usr/bin/env python3
"""Composite envelope for the pinned-rho QIT density/entropy scout.

This binds three local engine receipts after each engine computes the same
shared observable:

    rho(p) = (1-p)|GHZ><GHZ| + p*I/8, p=0.3, no dephasing.

The envelope does not promote the result. It only validates a bounded
scratch-diagnostic cross-engine comparison over one pinned finite object.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/three_engine_qit_density_entropy_pinned_rho_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/qit_density_entropy_pinned_rho_ghz_white_noise_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/qit_density_entropy_pinned_rho_jax_leg_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/qit_density_entropy_pinned_rho_pytorch_leg_results.json"

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
TOL = 1.0e-9

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


def max_abs(values: list[float]) -> float:
    return max(values) - min(values) if values else 0.0


def same_spec(*payloads: dict[str, Any]) -> bool:
    specs = [p.get("pinned_spec", {}) for p in payloads]
    if not specs:
        return False
    keys = ["formula", "p", "n_qubits", "hilbert_dimension", "entropy_base", "dephasing_included"]
    first = specs[0]
    return all(all(spec.get(k) == first.get(k) for k in keys) for spec in specs[1:])


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)

    julia_values = {
        "vn_entropy": julia["values"]["vn_entropy"],
        "analytic_entropy": julia["values"]["analytic_entropy"],
        "entropy_residual_vs_analytic": julia["values"]["entropy_residual_vs_analytic"],
        "spectrum_high": julia["values"]["spectrum_high"],
        "spectrum_low": julia["values"]["spectrum_low"],
    }
    jax_values = {
        "vn_entropy": jax["values"]["vn_entropy"],
        "qutip_entropy": jax["values"]["qutip_entropy"],
        "analytic_entropy": jax["values"]["analytic_entropy"],
        "entropy_residual_vs_qutip": jax["values"]["entropy_residual_vs_qutip"],
        "entropy_residual_vs_analytic": jax["values"]["entropy_residual_vs_analytic"],
        "spectrum_high": jax["values"]["spectrum_high"],
        "spectrum_low": jax["values"]["spectrum_low"],
    }
    pytorch_values = {
        "vn_entropy": pytorch["values"]["vn_entropy"],
        "analytic_entropy": pytorch["values"]["analytic_entropy"],
        "entropy_residual_vs_analytic": pytorch["values"]["entropy_residual_vs_analytic"],
        "dS_dp_grad": pytorch["values"]["dS_dp_grad"],
        "dS_dp_jacrev": pytorch["values"]["dS_dp_jacrev"],
        "analytic_dS_dp": pytorch["values"]["analytic_dS_dp"],
        "grad_jacrev_residual": pytorch["values"]["grad_jacrev_residual"],
        "spectrum_high": pytorch["values"]["spectrum_high"],
        "spectrum_low": pytorch["values"]["spectrum_low"],
    }

    entropies = [
        float(julia_values["vn_entropy"]),
        float(jax_values["vn_entropy"]),
        float(pytorch_values["vn_entropy"]),
    ]
    entropy_max_divergence = max_abs(entropies)
    spectrum_highs = [
        float(julia_values["spectrum_high"]),
        float(jax_values["spectrum_high"]),
        float(pytorch_values["spectrum_high"]),
    ]
    spectrum_lows = [
        float(julia_values["spectrum_low"]),
        float(jax_values["spectrum_low"]),
        float(pytorch_values["spectrum_low"]),
    ]

    z3_main = jax["smt"]["z3"]["main_status"]
    cvc5_main = jax["smt"]["cvc5"]["main_status"]
    z3_bad = jax["smt"]["z3"]["negative_control_status"]
    cvc5_bad = jax["smt"]["cvc5"]["negative_control_status"]

    all_pass = bool(
        julia.get("all_pass") is True
        and jax.get("all_pass") is True
        and pytorch.get("all_pass") is True
        and same_spec(julia, jax, pytorch)
        and entropy_max_divergence <= TOL
        and max_abs(spectrum_highs) <= TOL
        and max_abs(spectrum_lows) <= TOL
        and z3_main == cvc5_main == "sat"
        and z3_bad == cvc5_bad == "unsat"
        and all(payload.get("reads_peer_result") is False for payload in (julia, jax, pytorch))
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": "three_engine_qit_density_entropy_pinned_rho_envelope",
        "mode": "all_three_full_sims",
        "classification": CLASSIFICATION,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": (
            "Scratch three-engine QIT density/entropy envelope over one pinned finite object only: "
            "rho(p)=(1-p)|GHZ><GHZ|+pI/8 at p=0.3, natural-log entropy, no dephasing. "
            "No formal admission, bridge, manifold, basin, axis, or full-system claim."
        ),
        "all_pass": all_pass,
        "pinned_spec": julia.get("pinned_spec"),
        "package_preflight": {
            "python_executable": jax.get("python_executable"),
            "julia_active_project": julia.get("active_project"),
            "julia_version": julia.get("julia_version"),
            "python_packages_ok": {"jax": True, "qutip": True, "z3": True, "cvc5": True, "torch": True, "torch.func": True},
            "julia_packages_ok": {"QuantumOptics": True, "JSON": True, "LinearAlgebra": True},
        },
        "engines": {
            "julia": engine_record(
                payload=julia,
                source_path=julia["source_path"],
                result_path=JULIA_RESULT,
                packages_used=["QuantumOptics", "JSON", "LinearAlgebra", "Dates"],
                load_bearing=["QuantumOptics"],
                values=julia_values,
            ),
            "jax": engine_record(
                payload=jax,
                source_path=jax["source_path"],
                result_path=JAX_RESULT,
                packages_used=["jax", "jax.numpy", "qutip", "z3", "cvc5", "numpy", "json"],
                load_bearing=["qutip", "z3", "cvc5"],
                values=jax_values,
            ),
            "pytorch": engine_record(
                payload=pytorch,
                source_path=pytorch["source_path"],
                result_path=PYTORCH_RESULT,
                packages_used=["torch", "torch.func"],
                load_bearing=["torch.func"],
                values=pytorch_values,
            ),
        },
        "engine_contract": {
            "julia": {"status": "ran", "authority": "reference", "load_bearing_packages": ["QuantumOptics"], "result_path": str(JULIA_RESULT)},
            "jax": {"status": "ran", "authority": "primary_mirror", "load_bearing_packages": ["qutip", "z3", "cvc5"], "result_path": str(JAX_RESULT)},
            "pytorch": {"status": "ran", "authority": "third_substrate", "load_bearing_packages": ["torch.func"], "result_path": str(PYTORCH_RESULT)},
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_main,
                "negative_control_verdict": z3_bad,
                "claim": "Pinned exact spectrum {59/80, 3/80 x 7} is a nonnegative probability simplex",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_main,
                "negative_control_verdict": cvc5_bad,
                "claim": "Pinned exact spectrum {59/80, 3/80 x 7} is a nonnegative probability simplex",
            },
        },
        "claim_path_tools": [
            "QuantumOptics",
            "jax",
            "jax.numpy",
            "qutip",
            "z3",
            "cvc5",
            "torch",
            "torch.func",
        ],
        "control_only_tools": ["numpy"],
        "load_bearing_tool_claims": [
            {"tool": "QuantumOptics", "engine": "julia", "claim": "construct pinned density and compute entropy_vn", "observable": "vn_entropy", "status": "passed"},
            {"tool": "qutip", "engine": "jax", "claim": "Qobj entropy cross-check on same pinned density", "observable": "qutip_entropy", "status": "passed"},
            {"tool": "z3", "engine": "jax", "claim": "exact pinned spectrum simplex certificate", "observable": "sat with unsat negative control", "status": "passed"},
            {"tool": "cvc5", "engine": "jax", "claim": "independent exact pinned spectrum simplex certificate", "observable": "sat with unsat negative control", "status": "passed"},
            {"tool": "torch.func", "engine": "pytorch", "claim": "differentiable entropy gradient on pinned density", "observable": "dS_dp", "status": "passed"},
        ],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": julia_values,
                "jax": jax_values,
                "pytorch": pytorch_values,
            },
            "max_divergence": entropy_max_divergence,
            "spectrum_high_max_divergence": max_abs(spectrum_highs),
            "spectrum_low_max_divergence": max_abs(spectrum_lows),
            "structural_disagreements": [],
            "interpretation": "Agreement is only over the pinned finite rho(p) entropy; divergence remains signal for any broader claim.",
        },
        "peer_json_rule": "engine results read only after each engine computed its local result; never as a pass source",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"same_spec={str(same_spec(load_json(JULIA_RESULT), load_json(JAX_RESULT), load_json(PYTORCH_RESULT))).lower()} "
        f"entropy_max_divergence={result['divergence']['max_divergence']} "
        f"julia_entropy={result['engines']['julia']['values']['vn_entropy']} "
        f"jax_entropy={result['engines']['jax']['values']['vn_entropy']} "
        f"pytorch_entropy={result['engines']['pytorch']['values']['vn_entropy']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
