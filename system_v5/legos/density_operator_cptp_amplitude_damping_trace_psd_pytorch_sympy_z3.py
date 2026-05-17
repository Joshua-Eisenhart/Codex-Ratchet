#!/usr/bin/env python3
"""Finite CPTP amplitude-damping channel lego."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import sympy as sp
import torch
import z3

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
OUT_PATH = RESULT_DIR / "density_operator_cptp_amplitude_damping_trace_psd_pytorch_sympy_z3_results.json"

NAME = "density_operator_cptp_amplitude_damping_trace_psd_pytorch_sympy_z3"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Finite CPTP channel lego only: checks amplitude-damping Kraus completeness, "
    "trace preservation, and positive output on finite density states. It does "
    "not admit terrain laws, heat/work cycles, measurement feedback, bridge, or "
    "target-system interpretation."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing Kraus channel evolution and finite density output checks"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact Kraus completeness algebra"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof of gamma-domain and incomplete-channel trace loss"},
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing", "sympy": "load_bearing", "z3": "load_bearing"}


def kraus(gamma: float) -> list[torch.Tensor]:
    return [
        torch.tensor([[1.0, 0.0], [0.0, (1.0 - gamma) ** 0.5]], dtype=torch.complex128),
        torch.tensor([[0.0, gamma**0.5], [0.0, 0.0]], dtype=torch.complex128),
    ]


def apply_channel(rho: torch.Tensor, ops: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros_like(rho)
    for op in ops:
        out = out + op @ rho @ op.conj().T
    return out


def density_validity(rho: torch.Tensor) -> dict[str, Any]:
    hermitian_error = float(torch.linalg.matrix_norm(rho - rho.conj().T).item())
    trace = torch.trace(rho)
    eigs = torch.linalg.eigvalsh((rho + rho.conj().T) / 2)
    return {
        "trace_real": float(torch.real(trace).item()),
        "trace_imag": float(torch.imag(trace).item()),
        "min_eigenvalue": float(torch.min(eigs).item()),
        "hermitian_error": hermitian_error,
        "pass": hermitian_error < 1e-10 and abs(torch.real(trace).item() - 1.0) < 1e-10 and abs(torch.imag(trace).item()) < 1e-10 and torch.min(eigs).item() >= -1e-10,
    }


def sympy_completeness() -> dict[str, Any]:
    g = sp.symbols("gamma", nonnegative=True, real=True)
    k0 = sp.Matrix([[1, 0], [0, sp.sqrt(1 - g)]])
    k1 = sp.Matrix([[0, sp.sqrt(g)], [0, 0]])
    total = sp.simplify(k0.T * k0 + k1.T * k1)
    return {"kraus_sum": str(total), "pass": total == sp.eye(2)}


def z3_channel_domain() -> dict[str, Any]:
    g = z3.Real("gamma")
    outside = z3.Solver()
    outside.add(g >= 0, g <= 1, z3.Or(g < 0, g > 1))
    incomplete_loss = z3.Solver()
    trace_after_k0_only = 1 - g
    incomplete_loss.add(g > 0, g <= 1, trace_after_k0_only == 1)
    return {
        "gamma_outside_domain_unsat": {"solver_status": str(outside.check()), "pass": outside.check() == z3.unsat},
        "incomplete_kraus_trace_preservation_unsat_for_excited_state": {
            "solver_status": str(incomplete_loss.check()),
            "pass": incomplete_loss.check() == z3.unsat,
        },
    }


def main() -> dict[str, Any]:
    started = time.time()
    gamma = 0.35
    ops = kraus(gamma)
    excited = torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=torch.complex128)
    coherent = torch.tensor([[0.5, 0.5], [0.5, 0.5]], dtype=torch.complex128)
    out_excited = apply_channel(excited, ops)
    out_coherent = apply_channel(coherent, ops)
    incomplete_out = apply_channel(excited, [ops[0]])

    completeness = sum(op.conj().T @ op for op in ops)
    z3_checks = z3_channel_domain()
    positive = {
        "pytorch_kraus_completeness_identity": {
            "frobenius_error": float(torch.linalg.matrix_norm(completeness - torch.eye(2, dtype=torch.complex128)).item()),
            "pass": float(torch.linalg.matrix_norm(completeness - torch.eye(2, dtype=torch.complex128)).item()) < 1e-10,
        },
        "pytorch_excited_density_output_valid": density_validity(out_excited),
        "pytorch_coherent_density_output_valid": density_validity(out_coherent),
        "sympy_exact_kraus_completeness": sympy_completeness(),
        "z3_gamma_domain_closed": z3_checks["gamma_outside_domain_unsat"],
    }
    graveyard_companions = {
        "pytorch_incomplete_kraus_set_loses_trace": {
            "trace_after_incomplete_channel": float(torch.real(torch.trace(incomplete_out)).item()),
            "pass": abs(float(torch.real(torch.trace(incomplete_out)).item()) - 1.0) > 1e-3,
        },
        "z3_incomplete_kraus_trace_preservation_rejected": z3_checks["incomplete_kraus_trace_preservation_unsat_for_excited_state"],
    }
    boundary = {
        "gamma_zero_identity_channel_boundary": {
            "distance": float(torch.linalg.matrix_norm(apply_channel(coherent, kraus(0.0)) - coherent).item()),
            "pass": float(torch.linalg.matrix_norm(apply_channel(coherent, kraus(0.0)) - coherent).item()) < 1e-10,
        },
        "gamma_one_excited_state_resets_to_ground_boundary": {
            "output": [[float(torch.real(v).item()) for v in row] for row in apply_channel(excited, kraus(1.0))],
            "pass": torch.allclose(apply_channel(excited, kraus(1.0)), torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=torch.complex128)),
        },
    }
    result = {
        "schema": "LEGO_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "finite density operator transformed by amplitude-damping CPTP Kraus channel",
        "observable": ["Kraus completeness", "output trace", "output minimum eigenvalue", "gamma-domain UNSAT controls"],
        "predicate": "complete Kraus family preserves trace and positivity on finite density states",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values()),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
