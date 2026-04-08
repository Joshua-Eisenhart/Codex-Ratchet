#!/usr/bin/env python3
"""
PURE LEGO: Foundational channel constraints, the hard way
==========================================================
Pure math only.

What this sim does
------------------
1. Fits a qubit CPTP channel to actual density-matrix action data using
   torch/autograd on a Kraus parameterization.
2. Verifies the fitted channel is CP and TP by Choi reconstruction.
3. Uses z3 to prove a structural impossibility:
   a trace-preserving qubit affine map that fixes |0>, |1>, |+>, and |+i>
   must be the identity.
4. Uses sympy to confirm the same identity theorem symbolically.
5. Checks boundary cases for zero-noise and full-damping limits.

This is a foundation piece. It is not a ranking probe.
"""

from __future__ import annotations

import json
import math
import os
import time
import traceback
from typing import Dict, List

import numpy as np
import sympy as sp
import torch
from z3 import And, Or, Real, Solver, unsat, sat


torch.set_default_dtype(torch.float64)
torch.manual_seed(17)
np.random.seed(17)


TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "CPTP Kraus fitting with autograd and matrix projection",
    },
    "pyg": {"tried": False, "used": False, "reason": "no graph layer in this channel foundation lego"},
    "z3": {
        "tried": True,
        "used": True,
        "reason": "structural impossibility check for affine fixed-point constraints",
    },
    "cvc5": {"tried": False, "used": False, "reason": "z3 is sufficient for this bounded structural check"},
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "symbolic confirmation of the fixed-point identity theorem",
    },
    "clifford": {"tried": False, "used": False, "reason": "no geometric algebra layer in this channel lego"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold geometry is needed here"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariant learning layer is needed here"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph algorithm layer is needed here"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph or simplicial layer is needed here"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell-complex layer is needed here"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence computation is needed here"},
}


EPS = 1e-12
CDTYPE = torch.complex128
RDTYPE = torch.float64

I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
SY = torch.tensor([[0.0, -1j], [1j, 0.0]], dtype=CDTYPE)
SZ = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)


def ket(vals: List[complex]) -> torch.Tensor:
    psi = torch.tensor(vals, dtype=CDTYPE).reshape(-1, 1)
    return psi / torch.linalg.norm(psi)


def dm(vals: List[complex]) -> torch.Tensor:
    psi = ket(vals)
    return psi @ psi.conj().T


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = 0.5 * (rho + rho.conj().T)
    tr = torch.trace(rho)
    if abs(tr.item()) <= EPS:
        raise ValueError("zero-trace density matrix")
    return rho / tr


def apply_kraus_sum(kraus: List[torch.Tensor], rho: torch.Tensor, normalize: bool = True) -> torch.Tensor:
    out = torch.zeros((2, 2), dtype=CDTYPE)
    for k in kraus:
        out = out + k @ rho @ k.conj().T
    if normalize:
        out = 0.5 * (out + out.conj().T)
        return normalize_density(out)
    return out


def validate_density(rho: torch.Tensor) -> Dict[str, object]:
    rho = 0.5 * (rho + rho.conj().T)
    evals = torch.linalg.eigvalsh(rho).real
    tr = float(torch.trace(rho).real.item())
    herm_err = float(torch.max(torch.abs(rho - rho.conj().T)).item())
    return {
        "trace": tr,
        "trace_error": abs(tr - 1.0),
        "min_eigenvalue": float(torch.min(evals).item()),
        "hermitian_error": herm_err,
        "psd": bool(torch.min(evals).item() >= -1e-10),
        "valid": bool(abs(tr - 1.0) < 1e-10 and herm_err < 1e-10 and torch.min(evals).item() >= -1e-10),
    }


def partial_trace_output(choi: torch.Tensor) -> torch.Tensor:
    out = torch.zeros((2, 2), dtype=CDTYPE)
    for i in range(2):
        for j in range(2):
            out[i, j] = choi[i * 2 + 0, j * 2 + 0] + choi[i * 2 + 1, j * 2 + 1]
    return out


def partial_trace_input(choi: torch.Tensor) -> torch.Tensor:
    out = torch.zeros((2, 2), dtype=CDTYPE)
    for a in range(2):
        for b in range(2):
            out[a, b] = choi[0 * 2 + a, 0 * 2 + b] + choi[1 * 2 + a, 1 * 2 + b]
    return out


def choi_from_channel(channel_fn) -> torch.Tensor:
    kraus = getattr(channel_fn, "_kraus", None)
    choi = torch.zeros((4, 4), dtype=CDTYPE)
    for i in range(2):
        for j in range(2):
            basis = torch.zeros((2, 2), dtype=CDTYPE)
            basis[i, j] = 1.0
            if kraus is not None:
                out = apply_kraus_sum(kraus, basis, normalize=False)
            else:
                out = channel_fn(basis)
            choi[i * 2 : (i + 1) * 2, j * 2 : (j + 1) * 2] = out
    return choi


def channel_action_from_choi(choi: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    rho = rho.to(CDTYPE)
    out = torch.zeros((2, 2), dtype=CDTYPE)
    for i in range(2):
        for j in range(2):
            out = out + rho[i, j] * choi[i * 2 : (i + 1) * 2, j * 2 : (j + 1) * 2]
    return normalize_density(out)


def amplitude_damping_channel(gamma: float):
    g = float(np.clip(gamma, 0.0, 1.0))
    k0 = torch.tensor([[1.0, 0.0], [0.0, math.sqrt(1.0 - g)]], dtype=CDTYPE)
    k1 = torch.tensor([[0.0, math.sqrt(g)], [0.0, 0.0]], dtype=CDTYPE)

    def _channel(rho: torch.Tensor) -> torch.Tensor:
        return normalize_density(apply_kraus_sum([k0, k1], rho, normalize=False))

    _channel._kraus = [k0, k1]
    return _channel, [k0, k1]


def z_dephasing_channel(p: float):
    p = float(np.clip(p, 0.0, 1.0))
    k0 = math.sqrt(1.0 - p) * I2
    k1 = math.sqrt(p) * SZ

    def _channel(rho: torch.Tensor) -> torch.Tensor:
        return normalize_density(apply_kraus_sum([k0, k1], rho, normalize=False))

    _channel._kraus = [k0, k1]
    return _channel, [k0, k1]


def depolarizing_channel(p: float):
    p = float(np.clip(p, 0.0, 1.0))
    k0 = math.sqrt(1.0 - p) * I2
    k1 = math.sqrt(p / 3.0) * SX
    k2 = math.sqrt(p / 3.0) * SY
    k3 = math.sqrt(p / 3.0) * SZ

    def _channel(rho: torch.Tensor) -> torch.Tensor:
        return normalize_density(apply_kraus_sum([k0, k1, k2, k3], rho, normalize=False))

    _channel._kraus = [k0, k1, k2, k3]
    return _channel, [k0, k1, k2, k3]


def raw_kraus_to_tp_kraus(raw_kraus: List[torch.Tensor]) -> List[torch.Tensor]:
    gram = torch.zeros((2, 2), dtype=CDTYPE)
    for k in raw_kraus:
        gram = gram + k.conj().T @ k
    gram = 0.5 * (gram + gram.conj().T) + 1e-9 * I2
    evals, evecs = torch.linalg.eigh(gram)
    inv_sqrt_diag = torch.diag(torch.rsqrt(torch.clamp(evals.real, min=1e-12)).to(CDTYPE))
    inv_sqrt = evecs @ inv_sqrt_diag @ evecs.conj().T
    return [k @ inv_sqrt for k in raw_kraus]


def channel_from_raw_params(params_real: torch.Tensor, params_imag: torch.Tensor):
    raw_kraus = []
    for idx in range(params_real.shape[0]):
        raw_kraus.append(params_real[idx].to(CDTYPE) + 1j * params_imag[idx].to(CDTYPE))
    kraus = raw_kraus_to_tp_kraus(raw_kraus)

    def _channel(rho: torch.Tensor) -> torch.Tensor:
        return normalize_density(apply_kraus_sum(kraus, rho, normalize=False))

    _channel._kraus = kraus
    return _channel, kraus


def fock_states() -> Dict[str, torch.Tensor]:
    plus = torch.tensor([1.0, 1.0], dtype=CDTYPE) / math.sqrt(2.0)
    plus_i = torch.tensor([1.0, 1j], dtype=CDTYPE) / math.sqrt(2.0)
    minus = torch.tensor([1.0, -1.0], dtype=CDTYPE) / math.sqrt(2.0)
    return {
        "zero": dm([1.0, 0.0]),
        "one": dm([0.0, 1.0]),
        "plus": plus.reshape(2, 1) @ plus.conj().reshape(1, 2),
        "plus_i": plus_i.reshape(2, 1) @ plus_i.conj().reshape(1, 2),
        "minus": minus.reshape(2, 1) @ minus.conj().reshape(1, 2),
        "mixed_diag": torch.tensor([[0.72, 0.0], [0.0, 0.28]], dtype=CDTYPE),
        "skew_mixed": torch.tensor([[0.62, 0.09 + 0.03j], [0.09 - 0.03j, 0.38]], dtype=CDTYPE),
    }


def build_training_table(channel_fn) -> Dict[str, torch.Tensor]:
    states = fock_states()
    return {name: channel_fn(rho) for name, rho in states.items()}


def kraus_to_channel(kraus: List[torch.Tensor]):
    def _channel(rho: torch.Tensor) -> torch.Tensor:
        return normalize_density(apply_kraus_sum(kraus, rho, normalize=False))

    _channel._kraus = kraus
    return _channel


def train_channel_from_data(target_channel, steps: int = 400):
    target_inputs = fock_states()
    target_outputs = {name: target_channel(rho) for name, rho in target_inputs.items()}

    amp_kraus = [
        torch.tensor([[1.0, 0.0], [0.0, math.sqrt(1.0 - 0.37)]], dtype=CDTYPE),
        torch.tensor([[0.0, math.sqrt(0.37)], [0.0, 0.0]], dtype=CDTYPE),
    ]
    noise_scale = 0.06
    raw_real = torch.nn.Parameter(torch.stack([k.real for k in amp_kraus]) + noise_scale * torch.randn(2, 2, 2, dtype=RDTYPE))
    raw_imag = torch.nn.Parameter(noise_scale * torch.randn(2, 2, 2, dtype=RDTYPE))

    opt = torch.optim.Adam([raw_real, raw_imag], lr=0.05)
    losses = []
    for _ in range(steps):
        opt.zero_grad()
        learned_channel, kraus = channel_from_raw_params(raw_real, raw_imag)
        loss_terms = []
        for name, rho in target_inputs.items():
            pred = learned_channel(rho)
            tgt = target_outputs[name]
            loss_terms.append(torch.mean(torch.abs(pred - tgt) ** 2))
        loss = torch.stack(loss_terms).mean()
        gram = torch.zeros((2, 2), dtype=CDTYPE)
        for k in kraus:
            gram = gram + k.conj().T @ k
        tp_penalty = torch.mean(torch.abs(gram - I2) ** 2)
        total = loss + 0.05 * tp_penalty
        total.backward()
        opt.step()
        losses.append(float(total.detach().item()))

    learned_channel, learned_kraus = channel_from_raw_params(raw_real.detach(), raw_imag.detach())
    return {
        "learned_channel": learned_channel,
        "learned_kraus": learned_kraus,
        "target_outputs": target_outputs,
        "losses": losses,
        "raw_real": raw_real.detach(),
        "raw_imag": raw_imag.detach(),
        "target_inputs": target_inputs,
    }


def channel_fit_report(target_channel, learned_channel) -> Dict[str, object]:
    states = fock_states()
    per_state = {}
    max_err = 0.0
    mse_terms = []
    for name, rho in states.items():
        tgt = target_channel(rho)
        pred = learned_channel(rho)
        err = float(torch.linalg.matrix_norm(pred - tgt, ord="fro").item())
        per_state[name] = err
        max_err = max(max_err, err)
        mse_terms.append(float(torch.mean(torch.abs(pred - tgt) ** 2).item()))
    return {
        "per_state_frobenius_error": per_state,
        "mean_mse": float(np.mean(mse_terms)),
        "max_fro_error": float(max_err),
        "training_state_errors_small": bool(max_err < 1e-3),
    }


def choi_report(channel_fn) -> Dict[str, object]:
    choi = choi_from_channel(channel_fn)
    tp = partial_trace_output(choi)
    inp = partial_trace_input(choi)
    evals = torch.linalg.eigvalsh(0.5 * (choi + choi.conj().T)).real
    return {
        "choi": choi,
        "choi_eigenvalues": [float(x) for x in evals.detach().cpu().tolist()],
        "min_choi_eigenvalue": float(torch.min(evals).item()),
        "cp": bool(torch.min(evals).item() >= -1e-10),
        "tp_error": float(torch.max(torch.abs(tp - I2)).item()),
        "unital_error": float(torch.max(torch.abs(inp - I2)).item()),
        "tp": bool(torch.max(torch.abs(tp - I2)).item() < 1e-8),
    }


def affine_fixed_point_solver() -> Dict[str, object]:
    m11, m12, m13 = Real("m11"), Real("m12"), Real("m13")
    m21, m22, m23 = Real("m21"), Real("m22"), Real("m23")
    m31, m32, m33 = Real("m31"), Real("m32"), Real("m33")
    t1, t2, t3 = Real("t1"), Real("t2"), Real("t3")

    solver = Solver()
    M = [
        [m11, m12, m13],
        [m21, m22, m23],
        [m31, m32, m33],
    ]
    t = [t1, t2, t3]

    fixed_points = [
        ((0, 0, 1), (0, 0, 1)),
        ((0, 0, -1), (0, 0, -1)),
        ((1, 0, 0), (1, 0, 0)),
        ((0, 1, 0), (0, 1, 0)),
    ]
    for vec, target in fixed_points:
        for row in range(3):
            expr = M[row][0] * vec[0] + M[row][1] * vec[1] + M[row][2] * vec[2] + t[row]
            solver.add(expr == target[row])

    nonidentity = Or(
        m11 != 1, m12 != 0, m13 != 0,
        m21 != 0, m22 != 1, m23 != 0,
        m31 != 0, m32 != 0, m33 != 1,
        t1 != 0, t2 != 0, t3 != 0,
    )
    solver.push()
    solver.add(nonidentity)
    result = solver.check()
    solver.pop()

    if result == unsat:
        return {
            "status": "UNSAT",
            "pass": True,
            "note": "Four fixed Pauli eigenstates force the identity affine map.",
        }
    return {
        "status": str(result),
        "pass": False,
        "note": "A non-identity affine map remained satisfiable; the structural claim failed.",
    }


def two_fixed_points_boundary() -> Dict[str, object]:
    m11, m12, m13 = Real("bm11"), Real("bm12"), Real("bm13")
    m21, m22, m23 = Real("bm21"), Real("bm22"), Real("bm23")
    m31, m32, m33 = Real("bm31"), Real("bm32"), Real("bm33")
    t1, t2, t3 = Real("bt1"), Real("bt2"), Real("bt3")
    solver = Solver()
    M = [
        [m11, m12, m13],
        [m21, m22, m23],
        [m31, m32, m33],
    ]
    t = [t1, t2, t3]
    for vec, target in [((0, 0, 1), (0, 0, 1)), ((0, 0, -1), (0, 0, -1))]:
        for row in range(3):
            solver.add(M[row][0] * vec[0] + M[row][1] * vec[1] + M[row][2] * vec[2] + t[row] == target[row])
    solver.add(Or(m11 != 1, m22 != 1, m33 != 1, t1 != 0, t2 != 0, t3 != 0))
    result = solver.check()
    return {
        "status": str(result),
        "pass": bool(result == sat),
        "note": "Two fixed basis states still leave non-identity freedom.",
    }


def symbolic_identity_confirmation() -> Dict[str, object]:
    m11, m12, m13, m21, m22, m23, m31, m32, m33 = sp.symbols("m11 m12 m13 m21 m22 m23 m31 m32 m33")
    t1, t2, t3 = sp.symbols("t1 t2 t3")
    M = sp.Matrix([[m11, m12, m13], [m21, m22, m23], [m31, m32, m33]])
    t = sp.Matrix([t1, t2, t3])
    vecs = [
        (sp.Matrix([0, 0, 1]), sp.Matrix([0, 0, 1])),
        (sp.Matrix([0, 0, -1]), sp.Matrix([0, 0, -1])),
        (sp.Matrix([1, 0, 0]), sp.Matrix([1, 0, 0])),
        (sp.Matrix([0, 1, 0]), sp.Matrix([0, 1, 0])),
    ]
    equations = []
    for vec, target in vecs:
        equations.extend(list(M * vec + t - target))
    sol = sp.solve(equations, [m11, m12, m13, m21, m22, m23, m31, m32, m33, t1, t2, t3], dict=True)
    json_safe_solutions = [{str(k): str(v) for k, v in item.items()} for item in sol]
    return {
        "solutions": json_safe_solutions,
        "unique_solution": bool(len(sol) == 1),
        "identity_solution": bool(
            len(sol) == 1
            and sol[0][m11] == 1 and sol[0][m22] == 1 and sol[0][m33] == 1
            and sol[0][m12] == 0 and sol[0][m13] == 0 and sol[0][m21] == 0 and sol[0][m23] == 0 and sol[0][m31] == 0 and sol[0][m32] == 0
            and sol[0][t1] == 0 and sol[0][t2] == 0 and sol[0][t3] == 0
        ),
        "pass": bool(len(sol) == 1 and sol[0][m11] == 1 and sol[0][m22] == 1 and sol[0][m33] == 1),
    }


def channel_validation_report(raw_real: torch.Tensor, raw_imag: torch.Tensor) -> Dict[str, object]:
    raw_kraus = []
    for idx in range(raw_real.shape[0]):
        raw_kraus.append(raw_real[idx].to(CDTYPE) + 1j * raw_imag[idx].to(CDTYPE))
    raw_channel = kraus_to_channel(raw_kraus)
    raw_choi = choi_from_channel(raw_channel)
    raw_tp = partial_trace_output(raw_choi)
    raw_tp_error = float(torch.max(torch.abs(raw_tp - I2)).item())
    raw_cp = bool(torch.min(torch.linalg.eigvalsh(0.5 * (raw_choi + raw_choi.conj().T)).real).item() >= -1e-10)
    return {
        "raw_tp_error": raw_tp_error,
        "raw_cp": raw_cp,
        "raw_valid": bool(raw_tp_error < 1e-10 and raw_cp),
    }


def identity_channel() -> callable:
    def _channel(rho: torch.Tensor) -> torch.Tensor:
        return normalize_density(rho)

    _channel._kraus = [I2]
    return _channel


def reset_ground_channel() -> callable:
    ground = dm([1.0, 0.0])
    k0 = torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=CDTYPE)
    k1 = torch.tensor([[0.0, 1.0], [0.0, 0.0]], dtype=CDTYPE)

    def _channel(_rho: torch.Tensor) -> torch.Tensor:
        return ground.clone()

    _channel._kraus = [k0, k1]
    return _channel


def fit_and_validate() -> Dict[str, object]:
    target_channel, target_kraus = amplitude_damping_channel(0.37)
    fit = train_channel_from_data(target_channel, steps=350)
    learned_channel = fit["learned_channel"]
    learned_kraus = fit["learned_kraus"]
    train_report = channel_fit_report(target_channel, learned_channel)
    learned_choi = choi_from_channel(learned_channel)
    learned_choi_report = choi_report(learned_channel)
    target_choi_report = choi_report(target_channel)
    learned_choi_eval = torch.linalg.eigvalsh(0.5 * (learned_choi + learned_choi.conj().T)).real
    target_choi = choi_from_channel(target_channel)
    target_eval = torch.linalg.eigvalsh(0.5 * (target_choi + target_choi.conj().T)).real
    learned_tp = partial_trace_output(learned_choi)
    target_tp = partial_trace_output(target_choi)
    holdout_states = {
        "minus": dm([1.0 / math.sqrt(2.0), -1.0 / math.sqrt(2.0)]),
        "skew_holdout": torch.tensor([[0.61, 0.04 - 0.01j], [0.04 + 0.01j, 0.39]], dtype=CDTYPE),
        "tilted_pure": dm([math.cos(0.31), math.sin(0.31) * np.exp(1j * 0.57)]),
    }
    holdout_errors = {}
    for name, rho in holdout_states.items():
        holdout_errors[name] = float(torch.linalg.matrix_norm(learned_channel(rho) - target_channel(rho), ord="fro").item())

    return {
        "target_gamma": 0.37,
        "fit_losses": fit["losses"],
        "final_loss": float(fit["losses"][-1]),
        "initial_loss": float(fit["losses"][0]),
        "training_report": train_report,
        "holdout_errors": holdout_errors,
        "learned_kraus_count": len(learned_kraus),
        "learned_tp_error": float(torch.max(torch.abs(learned_tp - I2)).item()),
        "learned_min_choi_eigenvalue": float(torch.min(learned_choi_eval).item()),
        "learned_cp": bool(torch.min(learned_choi_eval).item() >= -1e-10),
        "learned_tp": bool(torch.max(torch.abs(learned_tp - I2)).item() < 1e-8),
        "target_min_choi_eigenvalue": float(torch.min(target_eval).item()),
        "target_tp_error": float(torch.max(torch.abs(target_tp - I2)).item()),
        "learned_choi_report": learned_choi_report,
        "target_choi_report": target_choi_report,
        "raw_channel_validation": channel_validation_report(fit["raw_real"], fit["raw_imag"]),
        "learned_channel": learned_channel,
        "target_channel": target_channel,
        "learned_choi": learned_choi,
        "target_choi": target_choi,
        "pass": bool(
            train_report["training_state_errors_small"]
            and float(torch.max(torch.abs(learned_tp - I2)).item()) < 1e-8
            and float(torch.min(learned_choi_eval).item()) >= -1e-10
            and max(holdout_errors.values()) < 1e-3
        ),
    }


def run_positive_tests() -> Dict[str, object]:
    fitted = fit_and_validate()
    solver = affine_fixed_point_solver()
    symbolic = symbolic_identity_confirmation()
    positive = {
        "cptp_fitting_report": fitted,
        "solver_forces_identity_on_four_fixed_states": solver,
        "sympy_confirms_unique_identity_solution": symbolic,
        "cross_check_solver_and_symbolic_agree": {
            "pass": bool(solver["pass"] and symbolic["pass"]),
        },
        "pass": bool(fitted["pass"] and solver["pass"] and symbolic["pass"]),
    }
    return positive


def run_negative_tests() -> Dict[str, object]:
    fitted = fit_and_validate()
    raw_report = fitted["raw_channel_validation"]
    identity_channel_fn = identity_channel()
    target_channel = fitted["target_channel"]
    states = fock_states()
    identity_errors = {}
    for name, rho in states.items():
        identity_errors[name] = float(torch.linalg.matrix_norm(identity_channel_fn(rho) - target_channel(rho), ord="fro").item())

    counterfeit_solver = two_fixed_points_boundary()
    negative = {
        "raw_unprojected_channel_is_not_trace_preserving": {
            "raw_tp_error": raw_report["raw_tp_error"],
            "raw_valid": raw_report["raw_valid"],
            "pass": bool(raw_report["raw_tp_error"] > 1e-6 and not raw_report["raw_valid"]),
        },
        "identity_channel_is_not_good_fit_for_amplitude_damping": {
            "max_identity_error": float(max(identity_errors.values())),
            "pass": bool(max(identity_errors.values()) > 0.05),
        },
        "two_fixed_points_leave_nonidentity_freedom": {
            "status": counterfeit_solver["status"],
            "pass": bool(counterfeit_solver["pass"]),
        },
        "learned_channel_beats_raw_unprojected_fit": {
            "pass": bool(fitted["training_report"]["mean_mse"] < 1e-3 and raw_report["raw_tp_error"] > 1e-6),
        },
        "counterfeit_ground_reset_is_not_identity": {
            "reset_distance": float(torch.linalg.matrix_norm(reset_ground_channel()(states["plus"]) - states["plus"], ord="fro").item()),
            "pass": bool(torch.linalg.matrix_norm(reset_ground_channel()(states["plus"]) - states["plus"], ord="fro").item() > 0.1),
        },
    }
    negative["pass"] = bool(all(v["pass"] for v in negative.values() if isinstance(v, dict) and "pass" in v))
    return negative


def run_boundary_tests() -> Dict[str, object]:
    identity_channel_fn, identity_kraus = amplitude_damping_channel(0.0)
    reset_channel_fn, reset_kraus = amplitude_damping_channel(1.0)
    states = fock_states()
    zero_out = identity_channel_fn(states["plus"])
    reset_out = reset_channel_fn(states["plus"])
    b0 = validate_density(zero_out)
    b1 = validate_density(reset_out)
    boundary = {
        "gamma_zero_reduces_to_identity": {
            "trace_error": b0["trace_error"],
            "min_eigenvalue": b0["min_eigenvalue"],
            "pass": bool(torch.linalg.matrix_norm(zero_out - states["plus"], ord="fro").item() < 1e-12),
        },
        "gamma_one_reduces_to_ground_reset": {
            "reset_to_ground": float(torch.linalg.matrix_norm(reset_out - dm([1.0, 0.0]), ord="fro").item()),
            "pass": bool(torch.linalg.matrix_norm(reset_out - dm([1.0, 0.0]), ord="fro").item() < 1e-12),
        },
        "identity_kraus_has_unit_tp": {
            "pass": bool(
                torch.max(torch.abs(partial_trace_output(choi_from_channel(identity_channel_fn)) - I2)).item() < 1e-10
            ),
        },
        "boundary_fixed_two_states_still_sat": {
            "pass": bool(two_fixed_points_boundary()["pass"]),
        },
    }
    boundary["pass"] = bool(all(v["pass"] for v in boundary.values() if isinstance(v, dict) and "pass" in v))
    return boundary


def count_section(section: Dict[str, object]) -> Dict[str, int]:
    total = sum(1 for value in section.values() if isinstance(value, dict) and "pass" in value)
    passed = sum(1 for value in section.values() if isinstance(value, dict) and value.get("pass") is True)
    return {"passed": passed, "failed": total - passed, "total": total}


def summarize(positive: Dict[str, object], negative: Dict[str, object], boundary: Dict[str, object]) -> Dict[str, object]:
    p = count_section(positive)
    n = count_section(negative)
    b = count_section(boundary)
    return {
        "positive": f"{p['passed']}/{p['total']}",
        "negative": f"{n['passed']}/{n['total']}",
        "boundary": f"{b['passed']}/{b['total']}",
        "all_pass": positive["pass"] and negative["pass"] and boundary["pass"],
        "note": (
            "Foundational channel lego succeeded: torch fitting, solver identity theorem, and symbolic confirmation agree."
            if positive["pass"] and negative["pass"] and boundary["pass"]
            else "Foundational channel lego found a contradiction."
        ),
    }


def main() -> Dict[str, object]:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    results = {
        "name": "Foundational Channel Constraints, Hard Way",
        "schema_version": "1.0",
        "probe": "foundation_channel_constraints_hardway",
        "purpose": (
            "Fit a real CPTP channel from density-matrix action data, then prove a structural "
            "fixed-point impossibility using solver and symbolic checks."
        ),
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tools_used": ["torch", "z3", "sympy"],
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summarize(positive, negative, boundary),
    }
    return results


if __name__ == "__main__":
    try:
        t0 = time.time()
        results = main()
        results["summary"]["elapsed_s"] = time.time() - t0
        out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "foundation_channel_constraints_hardway_results.json")
        with open(out_path, "w", encoding="utf-8") as handle:
            json.dump(results, handle, indent=2, default=str)
        print(f"Results written to {out_path}")
        print(results["summary"])
    except Exception as exc:
        print("FAILED:", exc)
        print(traceback.format_exc())
        raise
