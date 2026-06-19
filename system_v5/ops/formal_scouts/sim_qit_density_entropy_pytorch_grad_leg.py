#!/usr/bin/env python3
"""PyTorch GHZ density entropy gradient leg.

Scratch diagnostic only. The claim path is torch complex128 density
construction, torch.linalg.eigvalsh entropy, and torch.func.jacrev dS/dp.
"""

from __future__ import annotations

import datetime as _dt
import json
import math
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


OBJECT_ID = "qit_density_entropy_pytorch_grad_leg"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/qit_density_entropy_pytorch_grad_leg_results.json"
P_VALUE = 0.3
TINY_EPS = 1.0e-15
FD_STEP = 1.0e-6

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing float64/complex128 density construction and Hermitian eigenspectrum entropy",
    },
    "torch.func.jacrev": {
        "tried": True,
        "used": True,
        "reason": "load-bearing autodiff call that produces the reported dS/dp",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, timestamp, paths, and finite-difference control arithmetic",
    },
    "NumPy": {
        "tried": False,
        "used": False,
        "reason": "not used; numpy/scipy are control-only and not needed for this pinned check",
    },
    "SciPy": {
        "tried": False,
        "used": False,
        "reason": "not used; numpy/scipy are control-only and not needed for this pinned check",
    },
    "JAX": {
        "tried": False,
        "used": False,
        "reason": "not used; this leg must not read or mirror peer results",
    },
    "Julia": {
        "tried": False,
        "used": False,
        "reason": "not used; this leg must not read or mirror peer results",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.func.jacrev": "load_bearing",
    "Python stdlib": "supportive",
    "NumPy": None,
    "SciPy": None,
    "JAX": None,
    "Julia": None,
}

RHO_SPEC = {
    "state": "GHZ_3qubit",
    "formula": "(1-p)|psi><psi| + p*I8/8",
    "p": 0.3,
    "basis": "computational e0..e7, |000>=e0, |111>=e7",
    "dephasing": False,
    "entropy_base": "e",
}


def scalar_float(value: torch.Tensor | float) -> float:
    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().item())
    return float(value)


def ghz_state() -> torch.Tensor:
    psi = torch.zeros(8, dtype=torch.complex128)
    amp = torch.tensor(1.0 / math.sqrt(2.0), dtype=torch.float64).to(torch.complex128)
    psi[0] = amp
    psi[7] = amp
    return psi


def rho_of_p(p: torch.Tensor) -> torch.Tensor:
    p64 = p.to(dtype=torch.float64)
    psi = ghz_state()
    pure = torch.outer(psi, psi.conj())
    identity = torch.eye(8, dtype=torch.complex128)
    one = torch.tensor(1.0, dtype=torch.float64)
    return (one - p64).to(torch.complex128) * pure + p64.to(torch.complex128) * identity / 8.0


def von_neumann_entropy(rho: torch.Tensor) -> torch.Tensor:
    rho_h = 0.5 * (rho + rho.conj().T)
    eigvals = torch.linalg.eigvalsh(rho_h).real
    terms = torch.where(eigvals > TINY_EPS, eigvals * torch.log(eigvals), torch.zeros_like(eigvals))
    return -torch.sum(terms)


def entropy_of_p(p: torch.Tensor) -> torch.Tensor:
    return von_neumann_entropy(rho_of_p(p))


def finite_difference_grad(p_value: float) -> float:
    step = torch.tensor(FD_STEP, dtype=torch.float64)
    p = torch.tensor(p_value, dtype=torch.float64)
    plus = entropy_of_p(p + step)
    minus = entropy_of_p(p - step)
    return scalar_float((plus - minus) / (2.0 * step))


def analytic_control(p: float) -> tuple[float, float]:
    high = 1.0 - 7.0 * p / 8.0
    low = p / 8.0
    entropy = -(high * math.log(high) + 7.0 * low * math.log(low))
    derivative = (7.0 / 8.0) * math.log(high / low)
    return entropy, derivative


def build_result() -> dict[str, Any]:
    p = torch.tensor(P_VALUE, dtype=torch.float64)
    rho = rho_of_p(p)
    entropy = entropy_of_p(p)
    dS_dp = jacrev(entropy_of_p)(p)
    fd_grad = finite_difference_grad(P_VALUE)
    fd_residual = abs(scalar_float(dS_dp) - fd_grad)
    analytic_entropy, analytic_dS_dp = analytic_control(P_VALUE)

    trace = torch.trace(rho)
    eigvals = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    hermitian_residual = scalar_float(torch.max(torch.abs(rho - rho.conj().T)))
    trace_residual = abs(scalar_float(trace.real) - 1.0) + abs(scalar_float(trace.imag))
    min_eigenvalue = scalar_float(torch.min(eigvals))
    entropy_residual = abs(scalar_float(entropy) - analytic_entropy)
    grad_residual = abs(scalar_float(dS_dp) - analytic_dS_dp)

    core_pass = (
        rho.dtype == torch.complex128
        and p.dtype == torch.float64
        and rho.shape == (8, 8)
        and hermitian_residual <= 1.0e-12
        and trace_residual <= 1.0e-12
        and min_eigenvalue >= -1.0e-12
        and fd_residual <= 1.0e-6
        and entropy_residual <= 1.0e-12
        and grad_residual <= 1.0e-10
        and scalar_float(dS_dp) > 0.0
    )

    result = {
        "schema": "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "rho_spec": RHO_SPEC,
        "vn_entropy": scalar_float(entropy),
        "dS_dp": scalar_float(dS_dp),
        "fd_residual": fd_residual,
        "engine": "pytorch",
        "package": "torch.func.jacrev",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "reads_peer_result": False,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "torch_version": torch.__version__,
        "torch_parameter_dtype": str(p.dtype),
        "torch_density_dtype": str(rho.dtype),
        "eigenvalues": [scalar_float(x) for x in eigvals],
        "finite_difference": {
            "step": FD_STEP,
            "dS_dp_fd": fd_grad,
            "fd_residual": fd_residual,
        },
        "control_only_closed_form": {
            "vn_entropy": analytic_entropy,
            "dS_dp": analytic_dS_dp,
            "entropy_residual": entropy_residual,
            "grad_residual": grad_residual,
        },
        "checks": {
            "core_pass": core_pass,
            "rho_shape": list(rho.shape),
            "rho_is_complex128": rho.dtype == torch.complex128,
            "p_is_float64": p.dtype == torch.float64,
            "trace_real": scalar_float(trace.real),
            "trace_imag": scalar_float(trace.imag),
            "trace_residual": trace_residual,
            "hermitian_residual": hermitian_residual,
            "min_eigenvalue": min_eigenvalue,
            "jacrev_load_bearing": True,
            "fd_residual_lte_1e_minus_6": fd_residual <= 1.0e-6,
            "positive_gradient": scalar_float(dS_dp) > 0.0,
            "no_dephasing": True,
            "no_peer_result_read": True,
        },
        "claim_path": [
            "construct GHZ_3qubit |psi> in computational basis e0..e7",
            "construct rho(p) = (1-p)|psi><psi| + p*I8/8 with torch complex128",
            "compute S = -sum(lambda log(lambda)) using torch.linalg.eigvalsh",
            "compute reported dS/dp using torch.func.jacrev(entropy_of_p)",
        ],
        "control_path": [
            "central finite difference over the same torch entropy function",
            "closed-form scalar values recorded only as control residuals",
        ],
    }
    return result


def main() -> None:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"source_path={Path(__file__).resolve()}")
    print(f"result_path={RESULT_PATH}")
    print(f"vn_entropy={result['vn_entropy']:.15f}")
    print(f"dS_dp={result['dS_dp']:.15f}")
    print(f"fd_residual={result['fd_residual']:.15e}")


if __name__ == "__main__":
    main()
