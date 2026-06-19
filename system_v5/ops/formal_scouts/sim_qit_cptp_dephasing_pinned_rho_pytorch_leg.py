#!/usr/bin/env python3
from __future__ import annotations

import datetime as _dt
import json
import math
from pathlib import Path
from typing import Any

import torch
from torch.func import grad, jacrev

OBJECT_ID = "qit_cptp_dephasing_pinned_rho_pytorch_leg"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_qit_cptp_dephasing_pinned_rho_pytorch_leg.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/qit_cptp_dephasing_pinned_rho_pytorch_leg_results.json"
classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False
READS_PEER_RESULT = reads_peer_result
SIM_EXECUTION_KIND = "differentiable_qit_cptp_entropy_gradient"
P = 0.3
GAMMA = 0.4
DIM = 8
TOL = 1e-10

TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "load-bearing complex128 density and dephasing channel construction"},
    "torch.func.grad": {"tried": True, "used": True, "reason": "load-bearing entropy gradient dS/dgamma after dephasing"},
    "torch.func.jacrev": {"tried": True, "used": True, "reason": "load-bearing independent Jacobian check of dS/dgamma"},
    "Python stdlib": {"tried": True, "used": True, "reason": "supportive JSON/timestamp/path logic"},
    "NumPy": {"tried": False, "used": False, "reason": "not imported"},
    "JAX": {"tried": False, "used": False, "reason": "not used"},
    "Julia": {"tried": False, "used": False, "reason": "not used"},
}
TOOL_INTEGRATION_DEPTH = {"torch": "load_bearing", "torch.func.grad": "load_bearing", "torch.func.jacrev": "load_bearing", "Python stdlib": "supportive", "NumPy": None, "JAX": None, "Julia": None}


def as_float(x: torch.Tensor | float) -> float:
    return float(x.detach().cpu().item()) if isinstance(x, torch.Tensor) else float(x)


def rho_pinned() -> torch.Tensor:
    psi = torch.zeros(DIM, dtype=torch.complex128)
    amp = torch.tensor(1.0 / math.sqrt(2.0), dtype=torch.float64).to(torch.complex128)
    psi[0] = amp; psi[DIM-1] = amp
    return (1.0 - P) * torch.outer(psi, psi.conj()) + P * torch.eye(DIM, dtype=torch.complex128) / DIM


def dephase(rho: torch.Tensor, gamma: torch.Tensor) -> torch.Tensor:
    g = gamma.to(torch.complex128)
    return (1.0 - g) * rho + g * torch.diag(torch.diag(rho))


def entropy_rho(rho: torch.Tensor) -> torch.Tensor:
    vals = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    vals = torch.clamp(vals, min=1e-15)
    return -(vals * torch.log(vals)).sum()


def entropy_after_gamma(gamma: torch.Tensor) -> torch.Tensor:
    return entropy_rho(dephase(rho_pinned(), gamma))


def analytic_spectrum_after(gamma: float) -> list[float]:
    a = (1.0 - P) / 2.0 + P / 8.0
    b = (1.0 - gamma) * (1.0 - P) / 2.0
    low = P / 8.0
    return sorted([low]*6 + [a-b, a+b])


def analytic_entropy(vals: list[float]) -> float:
    return -sum(v * math.log(v) for v in vals if v > 0)


def analytic_grad_gamma(gamma: float) -> float:
    a = (1.0 - P) / 2.0 + P / 8.0
    b = (1.0 - gamma) * (1.0 - P) / 2.0
    high = a + b
    mid = a - b
    c = (1.0 - P) / 2.0
    return c * math.log(high / mid)


def build_result() -> dict[str, Any]:
    gamma = torch.tensor(GAMMA, dtype=torch.float64)
    rho0 = rho_pinned(); rho1 = dephase(rho0, gamma)
    before = entropy_rho(rho0); after = entropy_after_gamma(gamma)
    dS = grad(entropy_after_gamma)(gamma); jS = jacrev(entropy_after_gamma)(gamma)
    vals = sorted(float(x.detach().cpu().item()) for x in torch.linalg.eigvalsh(0.5*(rho1+rho1.conj().T)).real)
    expected = analytic_spectrum_after(GAMMA)
    analytic_after = analytic_entropy(expected)
    analytic_grad = analytic_grad_gamma(GAMMA)
    spectrum_residual = max(abs(a-b) for a,b in zip(vals, expected))
    trace_val = torch.trace(rho1)
    density_valid = bool(rho1.dtype == torch.complex128 and rho1.shape == (DIM,DIM) and abs(as_float(trace_val.real)-1.0) <= TOL and abs(as_float(trace_val.imag)) <= TOL and vals[0] >= -TOL and spectrum_residual <= TOL)
    grad_ok = bool(abs(as_float(dS)-analytic_grad) <= TOL and abs(as_float(jS)-analytic_grad) <= TOL and abs(as_float(dS)-as_float(jS)) <= TOL and abs(as_float(dS)) > 1e-6)
    all_pass = bool(density_valid and grad_ok and abs(as_float(after)-analytic_after) <= TOL and after >= before - TOL and not READS_PEER_RESULT)
    return {
        "object_id": OBJECT_ID, "backend": "pytorch", "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00","Z"), "source_path": str(SOURCE_PATH), "result_path": str(RESULT_PATH),
        "classification": CLASSIFICATION, "promotion_allowed": PROMOTION_ALLOWED, "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED, "reads_peer_result": READS_PEER_RESULT,
        "pinned_spec": {"rho_formula":"rho(p)=(1-p)|GHZ><GHZ|+pI/8", "p": P, "channel":"computational_basis_dephasing", "gamma": GAMMA, "entropy_base":"natural_log", "n_qubits":3, "hilbert_dimension":DIM, "spectrum_after_exact":"{239/400, 71/400, 15/400 x 6}"},
        "values": {"vn_entropy_before": as_float(before), "vn_entropy_after": as_float(after), "analytic_entropy_after": analytic_after, "entropy_change": as_float(after-before), "dS_dgamma_grad": as_float(dS), "dS_dgamma_jacrev": as_float(jS), "analytic_dS_dgamma": analytic_grad, "grad_jacrev_residual": abs(as_float(dS)-as_float(jS)), "spectrum_high": 239/400, "spectrum_mid": 71/400, "spectrum_low": 15/400, "entropy_residual_vs_analytic": abs(as_float(after)-analytic_after), "spectrum_max_abs_residual": spectrum_residual},
        "density_checks": {"complex128_density": rho1.dtype == torch.complex128, "shape": list(rho1.shape), "trace_real": as_float(trace_val.real), "trace_imag_abs": abs(as_float(trace_val.imag)), "min_eigenvalue": vals[0], "spectrum": vals, "expected_spectrum": expected, "density_valid": density_valid},
        "all_pass": all_pass, "core_pass": all_pass, "TOOL_MANIFEST": TOOL_MANIFEST, "tool_manifest": TOOL_MANIFEST, "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "PyTorch leg for one pinned CPTP dephasing scratch scout over rho(p), including dS/dgamma via torch.func; no peer reads, no promotion, no formal admission."
    }


def main() -> int:
    result = build_result(); RESULT_PATH.parent.mkdir(parents=True, exist_ok=True); RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(f"SCOUT_DONE all_pass={result['all_pass']} entropy_after={result['values']['vn_entropy_after']} dS_dgamma={result['values']['dS_dgamma_grad']} reads_peer_result={result['reads_peer_result']}")
    return 0 if result["all_pass"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
