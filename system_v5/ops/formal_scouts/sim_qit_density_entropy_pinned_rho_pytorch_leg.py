#!/usr/bin/env python3
"""PyTorch leg for one pinned QIT density/entropy scout.

Scratch diagnostic only. The shared observable is pinned to the same state used
by the Julia and JAX legs:

    rho(p) = (1-p)|GHZ><GHZ| + p*I/8, p=0.3, no dephasing.

PyTorch contributes a differentiable entropy/gradient check with torch.func.
"""

from __future__ import annotations

import datetime as _dt
import json
import math
from pathlib import Path
from typing import Any

import torch
from torch.func import grad, jacrev

OBJECT_ID = "qit_density_entropy_pinned_rho_pytorch_leg"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_qit_density_entropy_pinned_rho_pytorch_leg.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/qit_density_entropy_pinned_rho_pytorch_leg_results.json"
P_VALUE = 0.3
DIM = 8
TOL = 1.0e-10

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False
READS_PEER_RESULT = reads_peer_result
sim_execution_kind = "differentiable_qit_entropy_gradient"
SIM_EXECUTION_KIND = sim_execution_kind

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex128 pinned three-qubit density construction, Hermitian eigenspectrum, and autograd substrate",
    },
    "torch.func.grad": {
        "tried": True,
        "used": True,
        "reason": "load-bearing entropy gradient dS/dp for the pinned rho(p)",
    },
    "torch.func.jacrev": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent torch.func Jacobian check of the same pinned scalar entropy map",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, timestamp, paths, and closed-form scalar formatting",
    },
    "JAX": {
        "tried": False,
        "used": False,
        "reason": "not used: PyTorch leg computes locally and does not read JAX peer results",
    },
    "Julia": {
        "tried": False,
        "used": False,
        "reason": "not used: PyTorch leg computes locally and is not the reference backend",
    },
    "NumPy": {
        "tried": False,
        "used": False,
        "reason": "not imported; no NumPy fallback or parity path is allowed",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.func.grad": "load_bearing",
    "torch.func.jacrev": "load_bearing",
    "Python stdlib": "supportive",
    "JAX": None,
    "Julia": None,
    "NumPy": None,
}


def as_float(value: torch.Tensor | float) -> float:
    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().item())
    return float(value)


def ghz_density() -> torch.Tensor:
    psi = torch.zeros(DIM, dtype=torch.complex128)
    inv_sqrt2 = torch.tensor(1.0 / math.sqrt(2.0), dtype=torch.float64)
    psi[0] = inv_sqrt2.to(torch.complex128)
    psi[DIM - 1] = inv_sqrt2.to(torch.complex128)
    return torch.outer(psi, psi.conj())


def rho_of_p(p: torch.Tensor) -> torch.Tensor:
    p_c = p.to(torch.complex128)
    identity = torch.eye(DIM, dtype=torch.complex128)
    return (1.0 - p_c) * ghz_density() + p_c * identity / float(DIM)


def von_neumann_entropy_from_rho(rho: torch.Tensor) -> torch.Tensor:
    rho_h = 0.5 * (rho + rho.conj().T)
    eigvals = torch.linalg.eigvalsh(rho_h).real
    eigvals = torch.clamp(eigvals, min=1.0e-15)
    return -(eigvals * torch.log(eigvals)).sum()


def entropy_of_p(p: torch.Tensor) -> torch.Tensor:
    return von_neumann_entropy_from_rho(rho_of_p(p))


def analytic_spectrum(p: float) -> list[float]:
    high = 1.0 - 7.0 * p / 8.0
    low = p / 8.0
    return sorted([low] * 7 + [high])


def analytic_entropy_and_grad(p: float) -> tuple[float, float]:
    vals = analytic_spectrum(p)
    entropy = -sum(v * math.log(v) for v in vals if v > 0.0)
    high = 1.0 - 7.0 * p / 8.0
    low = p / 8.0
    derivative = (7.0 / 8.0) * math.log(high / low)
    return entropy, derivative


def build_result() -> dict[str, Any]:
    p = torch.tensor(P_VALUE, dtype=torch.float64)
    rho = rho_of_p(p)
    entropy = entropy_of_p(p)
    dS_dp_grad = grad(entropy_of_p)(p)
    dS_dp_jacrev = jacrev(entropy_of_p)(p)
    analytic_entropy, analytic_dS_dp = analytic_entropy_and_grad(P_VALUE)

    trace_val = torch.trace(rho)
    eigvals = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    eigvals_list = sorted(float(x.detach().cpu().item()) for x in eigvals)
    expected_spectrum = analytic_spectrum(P_VALUE)
    spectrum_residual = max(abs(a - b) for a, b in zip(eigvals_list, expected_spectrum))
    hermitian_residual = as_float(torch.max(torch.abs(rho - rho.conj().T)))
    trace_residual = abs(as_float(trace_val.real) - 1.0) + abs(as_float(trace_val.imag))
    min_eigenvalue = min(eigvals_list)
    entropy_residual = abs(as_float(entropy) - analytic_entropy)
    grad_residual = abs(as_float(dS_dp_grad) - analytic_dS_dp)
    jacrev_residual = abs(as_float(dS_dp_jacrev) - analytic_dS_dp)
    grad_jacrev_residual = abs(as_float(dS_dp_grad) - as_float(dS_dp_jacrev))

    complex128_density = rho.dtype == torch.complex128
    density_valid = (
        complex128_density
        and rho.shape == (DIM, DIM)
        and hermitian_residual <= TOL
        and trace_residual <= TOL
        and min_eigenvalue >= -TOL
        and spectrum_residual <= TOL
    )
    differentiable_entropy_grad = (
        bool(torch.isfinite(dS_dp_grad))
        and bool(torch.isfinite(dS_dp_jacrev))
        and abs(as_float(dS_dp_grad)) > 1.0e-6
        and grad_residual <= TOL
        and jacrev_residual <= TOL
        and grad_jacrev_residual <= TOL
    )
    fences_ok = (
        classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
    )
    no_peer_read = READS_PEER_RESULT is False
    all_pass = bool(density_valid and differentiable_entropy_grad and entropy_residual <= TOL and fences_ok and no_peer_read)

    return {
        "schema": "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "name": OBJECT_ID,
        "version": "1.0",
        "tier": "QIT_DENSITY_ENTROPY_PINNED_RHO_pytorch_leg",
        "backend": "pytorch",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "promotion_status": "diagnostic_only",
        "reads_peer_result": READS_PEER_RESULT,
        "pinned_spec": {
            "name": "GHZ white-noise density, no dephasing",
            "formula": "rho(p) = (1-p)|GHZ><GHZ| + p*I/8",
            "p": P_VALUE,
            "p_exact": "3/10",
            "spectrum_exact": "{59/80, 3/80 x 7}",
            "n_qubits": 3,
            "hilbert_dimension": DIM,
            "basis_order": "computational |000>..|111>; entropy is spectrum-invariant",
            "entropy_base": "natural_log",
            "dephasing_included": False,
        },
        "values": {
            "vn_entropy": as_float(entropy),
            "analytic_entropy": analytic_entropy,
            "entropy_residual_vs_analytic": entropy_residual,
            "dS_dp_grad": as_float(dS_dp_grad),
            "dS_dp_jacrev": as_float(dS_dp_jacrev),
            "analytic_dS_dp": analytic_dS_dp,
            "grad_residual_vs_analytic": grad_residual,
            "jacrev_residual_vs_analytic": jacrev_residual,
            "grad_jacrev_residual": grad_jacrev_residual,
            "spectrum_high": 1.0 - 7.0 * P_VALUE / 8.0,
            "spectrum_low": P_VALUE / 8.0,
        },
        "density_checks": {
            "complex128_density": complex128_density,
            "shape": list(rho.shape),
            "trace_real": as_float(trace_val.real),
            "trace_imag_abs": abs(as_float(trace_val.imag)),
            "trace_residual": trace_residual,
            "hermitian_residual": hermitian_residual,
            "min_eigenvalue": min_eigenvalue,
            "max_eigenvalue": max(eigvals_list),
            "spectrum": eigvals_list,
            "expected_spectrum": expected_spectrum,
            "spectrum_max_abs_residual": spectrum_residual,
            "density_valid": density_valid,
        },
        "positive": {
            "rho_is_three_qubit_complex128_density": {"pass": density_valid},
            "differentiable_entropy_gradient": {"pass": differentiable_entropy_grad},
        },
        "negative": {
            "gradient_not_decorative_zero": {"pass": abs(as_float(dS_dp_grad)) > 1.0e-6, "dS_dp": as_float(dS_dp_grad)},
            "not_peer_parity": {"pass": no_peer_read, "reads_peer_result": READS_PEER_RESULT},
        },
        "boundary": {
            "scratch_fences": {
                "classification": classification,
                "promotion_allowed": promotion_allowed,
                "formal_admission_allowed": formal_admission_allowed,
                "pass": fences_ok,
            },
            "torch_leg_not_reference": {"pass": True},
        },
        "all_pass": all_pass,
        "core_pass": all_pass,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "PyTorch leg for one pinned QIT density/entropy scratch scout: rho(p)=(1-p)|GHZ><GHZ|+pI/8 at p=0.3, torch.func gradient/Jacobian check. No peer reads, no promotion, no formal admission.",
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={result['all_pass']} "
        f"differentiable_entropy_grad={result['positive']['differentiable_entropy_gradient']['pass']} "
        f"dS_dp={result['values']['dS_dp_grad']} "
        f"vn_entropy={result['values']['vn_entropy']} "
        f"reads_peer_result={result['reads_peer_result']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
