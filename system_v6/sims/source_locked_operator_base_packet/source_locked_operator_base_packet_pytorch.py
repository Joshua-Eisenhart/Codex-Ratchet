#!/usr/bin/env python3
"""PyTorch leg for the source-locked four-operator base packet."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import torch
from torch.func import jacfwd


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "source_locked_operator_base_packet"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULTS_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_pytorch.py"
RESULT_PATH = RESULTS_DIR / f"{SIM_ID}_pytorch_results.json"
ENGINE = "pytorch"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-12

Q1 = 0.3
Q2 = 0.3
THETA = math.pi / 2.0
PHI = math.pi / 2.0
PIN_SPEC = "q1=q2=0.3, theta=phi=pi/2, rho_0=|psi(0.3,0.2,pi/8)><...|, rho_1=0.7*rho_0+0.3*I/2"

CDTYPE = torch.complex128
RDTYPE = torch.float64
I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
SY = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=CDTYPE)
SZ = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)
P0 = 0.5 * (I2 + SZ)
P1 = 0.5 * (I2 - SZ)
QP = 0.5 * (I2 + SX)
QM = 0.5 * (I2 - SX)
HX = (1.0 / math.sqrt(2.0)) * torch.tensor([[1.0, 1.0], [1.0, -1.0]], dtype=CDTYPE)

SOURCE_CITATIONS = {
    "scaffold_hopf_spinor": "system_v6/foundations/working_math_scaffold_20260609.md:31-38",
    "scaffold_base_operators": "system_v6/foundations/working_math_scaffold_20260609.md:66-75",
    "source_state_and_projectors": "system_v5/READ ONLY Reference Docs/operator math explicit.md:8-100",
    "source_Ti": "system_v5/READ ONLY Reference Docs/operator math explicit.md:102-230",
    "source_Te": "system_v5/READ ONLY Reference Docs/operator math explicit.md:279-438",
    "source_Fi": "system_v5/READ ONLY Reference Docs/operator math explicit.md:488-587",
    "source_Fe": "system_v5/READ ONLY Reference Docs/operator math explicit.md:646-735",
    "source_exact_lock": "system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810",
    "wiki_operator_summary": "/Users/joshuaeisenhart/wiki/concepts/operator-math-explicit.md:68-123",
}

OPERATOR_BACKLOG = [
    {
        "operator": "R_y",
        "status": "not_implemented",
        "reason": "not one of the four intrinsic source-locked operators in this packet",
        "source_citations": ["system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810"],
    },
    {
        "operator": "D_y",
        "status": "not_implemented_except_wrong_basis_negative_control",
        "reason": "used only as falsifying wrong-basis Ti control, not admitted as a base operator",
        "source_citations": [
            "system_v5/READ ONLY Reference Docs/operator math explicit.md:50-56",
            "system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810",
        ],
    },
    {
        "operator": "D_+/-",
        "status": "not_implemented",
        "reason": "ladder operators are support material, not base operators in this packet",
        "source_citations": [
            "/Users/joshuaeisenhart/wiki/concepts/operator-math-explicit.md:50-55",
            "system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810",
        ],
    },
    {
        "operator": "Pi_P",
        "status": "not_implemented",
        "reason": "projector/quotient packet is backlog, not this four-token compression",
        "source_citations": ["system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810"],
    },
    {
        "operator": "F_Q",
        "status": "not_implemented",
        "reason": "future field/operator packet, not one of Ti/Te/Fi/Fe",
        "source_citations": ["system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810"],
    },
    {
        "operator": "D[L] generic",
        "status": "not_implemented",
        "reason": "generic Lindblad terrain law is outside the four base operator packet",
        "source_citations": [
            "system_v6/foundations/working_math_scaffold_20260609.md:86-90",
            "system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810",
        ],
    },
    {
        "operator": "depolarizing",
        "status": "not_implemented",
        "reason": "not present in the intrinsic four-operator source lock",
        "source_citations": ["system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810"],
    },
]

TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "engine-native complex128 matrix/channel arithmetic"},
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing jacfwd derivation of source-channel Jacobians gates all_pass",
    },
}
TOOL_INTEGRATION_DEPTH = {"torch": "supportive", "torch.func": "load_bearing"}
CAPABILITY_PROBES = {
    "torch": "system_v4/probes/a2_state/sim_results/tool_capability_torch_results.json",
    "torch.func": "system_v4/probes/a2_state/sim_results/sim_pytorch_autograd_gradient_micro_results.json",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def py_float(value: Any) -> float:
    if isinstance(value, torch.Tensor):
        return float(torch.real(value).detach().cpu().item())
    return float(value)


def complex_pair(value: Any) -> dict[str, float]:
    if isinstance(value, torch.Tensor):
        z = complex(value.detach().cpu().item())
    else:
        z = complex(value)
    return {"re": float(z.real), "im": float(z.imag)}


def cexp(angle: float) -> complex:
    return complex(math.cos(angle), math.sin(angle))


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return torch.tensor(
        [
            cexp(phi + chi) * math.cos(eta),
            cexp(phi - chi) * math.sin(eta),
        ],
        dtype=CDTYPE,
    )


def density_from_spinor(psi: torch.Tensor) -> torch.Tensor:
    return psi[:, None] @ torch.conj(psi[None, :])


def pinned_states() -> dict[str, torch.Tensor]:
    rho0 = density_from_spinor(spinor(0.3, 0.2, math.pi / 8.0))
    rho1 = 0.7 * rho0 + 0.3 * I2 / 2.0
    return {"rho_0": rho0, "rho_1": rho1}


def unitary_x(theta: float) -> torch.Tensor:
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    return torch.tensor([[c, -1.0j * s], [-1.0j * s, c]], dtype=CDTYPE)


def unitary_z(phi: float) -> torch.Tensor:
    return torch.tensor([[cexp(-phi / 2.0), 0.0], [0.0, cexp(phi / 2.0)]], dtype=CDTYPE)


def kraus(op: str, q1: float = Q1, q2: float = Q2, theta: float = THETA, phi: float = PHI) -> list[torch.Tensor]:
    if op == "Ti":
        return [math.sqrt(1.0 - q1) * I2, math.sqrt(q1) * P0, math.sqrt(q1) * P1]
    if op == "Te":
        return [math.sqrt(1.0 - q2) * I2, math.sqrt(q2) * QP, math.sqrt(q2) * QM]
    if op == "Fi":
        return [unitary_x(theta)]
    if op == "Fe":
        return [unitary_z(phi)]
    raise ValueError(op)


def apply_kraus(rho: torch.Tensor, ks: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros_like(rho)
    for k in ks:
        out = out + k @ rho @ torch.conj(k.T)
    return out


def source_channel(op: str, rho: torch.Tensor, q1: float = Q1, q2: float = Q2, theta: float = THETA, phi: float = PHI) -> torch.Tensor:
    return apply_kraus(rho, kraus(op, q1, q2, theta, phi))


def bloch(rho: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    return (
        torch.real(torch.trace(rho @ SX)),
        torch.real(torch.trace(rho @ SY)),
        torch.real(torch.trace(rho @ SZ)),
    )


def rho_from_bloch(rx: Any, ry: Any, rz: Any) -> torch.Tensor:
    return 0.5 * (I2 + rx * SX + ry * SY + rz * SZ)


def bloch_channel(op: str, rho: torch.Tensor, q1: float = Q1, q2: float = Q2, theta: float = THETA, phi: float = PHI) -> torch.Tensor:
    rx, ry, rz = bloch(rho)
    if op == "Ti":
        return rho_from_bloch((1.0 - q1) * rx, (1.0 - q1) * ry, rz)
    if op == "Te":
        return rho_from_bloch(rx, (1.0 - q2) * ry, (1.0 - q2) * rz)
    if op == "Fi":
        return rho_from_bloch(rx, ry * math.cos(theta) - rz * math.sin(theta), rz * math.cos(theta) + ry * math.sin(theta))
    if op == "Fe":
        return rho_from_bloch(rx * math.cos(phi) - ry * math.sin(phi), rx * math.sin(phi) + ry * math.cos(phi), rz)
    raise ValueError(op)


def generator_channel(op: str, rho: torch.Tensor) -> torch.Tensor:
    if op == "Ti":
        kappa = -math.log(1.0 - Q1)
        rx, ry, rz = bloch(rho)
        return rho_from_bloch(math.exp(-kappa) * rx, math.exp(-kappa) * ry, rz)
    if op == "Te":
        kappa = -math.log(1.0 - Q2)
        rx, ry, rz = bloch(rho)
        return rho_from_bloch(rx, math.exp(-kappa) * ry, math.exp(-kappa) * rz)
    if op == "Fi":
        u = unitary_x(THETA)
        return u @ rho @ torch.conj(u.T)
    if op == "Fe":
        u = unitary_z(PHI)
        return u @ rho @ torch.conj(u.T)
    raise ValueError(op)


def trace_norm(mat: torch.Tensor) -> float:
    return py_float(torch.sum(torch.linalg.svdvals(mat)))


def max_abs(mat: torch.Tensor) -> float:
    return py_float(torch.max(torch.abs(mat)))


def entropy_vn(rho: torch.Tensor) -> float:
    vals = torch.clamp(torch.real(torch.linalg.eigvalsh(0.5 * (rho + torch.conj(rho.T)))), 0.0, 1.0)
    pieces = torch.where(vals > 1.0e-15, vals * torch.log(vals), torch.zeros_like(vals))
    return py_float(-torch.sum(pieces))


def purity(rho: torch.Tensor) -> float:
    return py_float(torch.real(torch.trace(rho @ rho)))


def choi_from_kraus(ks: list[torch.Tensor]) -> torch.Tensor:
    choi = torch.zeros((4, 4), dtype=CDTYPE)
    for k in ks:
        v = torch.reshape(k, (4, 1))
        choi = choi + v @ torch.conj(v.T)
    return choi


def cptp_certificate(op: str) -> dict[str, Any]:
    ks = kraus(op)
    choi = choi_from_kraus(ks)
    tp = torch.zeros((2, 2), dtype=CDTYPE)
    for k in ks:
        tp = tp + torch.conj(k.T) @ k
    eigvals = torch.real(torch.linalg.eigvalsh(0.5 * (choi + torch.conj(choi.T))))
    return {
        "choi_psd": bool(py_float(torch.min(eigvals)) >= -TOL),
        "choi_min_eig": py_float(torch.min(eigvals)),
        "choi_trace": py_float(torch.real(torch.trace(choi))),
        "trace_preserving": bool(max_abs(tp - I2) <= TOL),
        "tp_residual_max_abs": max_abs(tp - I2),
    }


def representation_certificate(op: str, states: dict[str, torch.Tensor]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    max_diff = 0.0
    for state_name, rho in states.items():
        source = source_channel(op, rho)
        bloch_form = bloch_channel(op, rho)
        generator = generator_channel(op, rho)
        row = {
            "source_vs_bloch_max_abs": max_abs(source - bloch_form),
            "source_vs_generator_max_abs": max_abs(source - generator),
            "bloch_vs_generator_max_abs": max_abs(bloch_form - generator),
        }
        row["pass"] = all(float(v) <= TOL for k, v in row.items() if k.endswith("max_abs"))
        rows[state_name] = row
        max_diff = max(max_diff, row["source_vs_bloch_max_abs"], row["source_vs_generator_max_abs"], row["bloch_vs_generator_max_abs"])
    return {"tol": TOL, "max_diff": max_diff, "pass": max_diff <= TOL, "states": rows}


def property_certificate(op: str, states: dict[str, torch.Tensor]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for state_name, rho in states.items():
        after = source_channel(op, rho)
        if op in {"Ti", "Te"}:
            before_s = entropy_vn(rho)
            after_s = entropy_vn(after)
            row = {
                "entropy_before": before_s,
                "entropy_after": after_s,
                "entropy_delta": after_s - before_s,
                "entropy_non_decreasing": after_s + TOL >= before_s,
            }
            if op == "Ti":
                before_off = rho[0, 1]
                after_off = after[0, 1]
                expected = (1.0 - Q1) * before_off
                residual = abs(complex((after_off - expected).detach().cpu().item()))
                row.update(
                    {
                        "basis": "z",
                        "offdiag_before": complex_pair(before_off),
                        "offdiag_after": complex_pair(after_off),
                        "expected_shrink_factor": 1.0 - Q1,
                        "coherence_shrink_residual": residual,
                        "coherence_shrink_pass": residual <= TOL,
                    }
                )
            else:
                rho_x = torch.conj(HX.T) @ rho @ HX
                after_x = torch.conj(HX.T) @ after @ HX
                before_off = rho_x[0, 1]
                after_off = after_x[0, 1]
                expected = (1.0 - Q2) * before_off
                residual = abs(complex((after_off - expected).detach().cpu().item()))
                row.update(
                    {
                        "basis": "x",
                        "offdiag_before": complex_pair(before_off),
                        "offdiag_after": complex_pair(after_off),
                        "expected_shrink_factor": 1.0 - Q2,
                        "coherence_shrink_residual": residual,
                        "coherence_shrink_pass": residual <= TOL,
                    }
                )
        else:
            before_p = purity(rho)
            after_p = purity(after)
            row = {
                "purity_before": before_p,
                "purity_after": after_p,
                "purity_delta_abs": abs(after_p - before_p),
                "purity_preserved": abs(after_p - before_p) <= TOL,
            }
        row["pass"] = all(v is True for k, v in row.items() if k.endswith("preserved") or k.endswith("non_decreasing") or k.endswith("shrink_pass"))
        rows[state_name] = row
    return {"pass": all(row["pass"] for row in rows.values()), "states": rows}


def commutator_table(rho: torch.Tensor) -> dict[str, Any]:
    ops = ["Ti", "Te", "Fi", "Fe"]
    table: dict[str, dict[str, float]] = {}
    for a in ops:
        table[a] = {}
        for b in ops:
            comm = source_channel(a, source_channel(b, rho)) - source_channel(b, source_channel(a, rho))
            table[a][b] = trace_norm(comm)
    zeros = {"Ti-Fe": table["Ti"]["Fe"], "Te-Fi": table["Te"]["Fi"], "Ti-Te": table["Ti"]["Te"]}
    nonzeros = {"Ti-Fi": table["Ti"]["Fi"], "Te-Fe": table["Te"]["Fe"], "Fi-Fe": table["Fi"]["Fe"]}
    return {
        "norm": "trace_norm",
        "state": "rho_0",
        "table": table,
        "known_zeros": zeros,
        "known_nonzeros": nonzeros,
        "known_zero_pass": all(abs(v) <= TOL for v in zeros.values()),
        "known_nonzero_pass": all(abs(v) > 1.0e-6 for v in nonzeros.values()),
    }


def wrong_basis_ti_y(rho: torch.Tensor) -> torch.Tensor:
    rx, ry, rz = bloch(rho)
    return rho_from_bloch((1.0 - Q1) * rx, ry, (1.0 - Q1) * rz)


def max_channel_diff_with_params(rho: torch.Tensor, params_a: dict[str, float], params_b: dict[str, float]) -> float:
    diffs = []
    for op in ["Ti", "Te", "Fi", "Fe"]:
        lhs = source_channel(op, rho, **params_a)
        rhs = source_channel(op, rho, **params_b)
        diffs.append(trace_norm(lhs - rhs))
    return max(diffs)


def negative_controls(states: dict[str, torch.Tensor]) -> dict[str, Any]:
    wrong_rows = {}
    for state_name, rho in states.items():
        wrong_rows[state_name] = {
            "trace_norm_Dz_minus_Dy": trace_norm(source_channel("Ti", rho) - wrong_basis_ti_y(rho)),
        }
    pinned = {"q1": Q1, "q2": Q2, "theta": THETA, "phi": PHI}
    swapped = {"q1": Q2, "q2": Q1, "theta": PHI, "phi": THETA}
    offpin = {"q1": 0.2, "q2": 0.4, "theta": math.pi / 3.0, "phi": math.pi / 5.0}
    offpin_swapped = {"q1": 0.4, "q2": 0.2, "theta": math.pi / 5.0, "phi": math.pi / 3.0}
    return {
        "wrong_basis_Ti_y": {
            "rows": wrong_rows,
            "different_values": all(row["trace_norm_Dz_minus_Dy"] > 1.0e-6 for row in wrong_rows.values()),
            "purpose": "source-lock falsifier: replacing P0/P1 z-dephasing with y-basis dephasing changes values",
        },
        "swapped_parameter_control": {
            "declared_pin_degenerate": Q1 == Q2 and THETA == PHI,
            "pinned_swap_max_trace_norm_diff": max_channel_diff_with_params(states["rho_0"], pinned, swapped),
            "pinned_swap_is_not_falsifying": max_channel_diff_with_params(states["rho_0"], pinned, swapped) <= TOL,
            "off_pin_sanity_params": {"q1": 0.2, "q2": 0.4, "theta": "pi/3", "phi": "pi/5"},
            "off_pin_swap_max_trace_norm_diff": max_channel_diff_with_params(states["rho_0"], offpin, offpin_swapped),
            "off_pin_swap_falsifies": max_channel_diff_with_params(states["rho_0"], offpin, offpin_swapped) > 1.0e-6,
            "honest_status": "the requested pinned swap is degenerate because q1=q2 and theta=phi; off-pin sanity proves the code path is falsifiable",
        },
    }


def source_vector_channel(op: str, x: torch.Tensor) -> torch.Tensor:
    a, u, v, d = x[0], x[1], x[2], x[3]
    if op == "Ti":
        return torch.stack([a, (1.0 - Q1) * u, (1.0 - Q1) * v, d])
    if op == "Te":
        return torch.stack([(1.0 - Q2 / 2.0) * a + (Q2 / 2.0) * d, u, (1.0 - Q2) * v, (Q2 / 2.0) * a + (1.0 - Q2 / 2.0) * d])
    if op == "Fi":
        c2 = math.cos(THETA / 2.0) ** 2
        s2 = math.sin(THETA / 2.0) ** 2
        st = math.sin(THETA)
        return torch.stack([a * c2 + d * s2 + v * st, u, v * math.cos(THETA) - ((a - d) / 2.0) * st, a * s2 + d * c2 - v * st])
    if op == "Fe":
        return torch.stack([a, u * math.cos(PHI) - v * math.sin(PHI), u * math.sin(PHI) + v * math.cos(PHI), d])
    raise ValueError(op)


def analytic_channel_matrix(op: str) -> torch.Tensor:
    if op == "Ti":
        rows = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0 - Q1, 0.0, 0.0], [0.0, 0.0, 1.0 - Q1, 0.0], [0.0, 0.0, 0.0, 1.0]]
    elif op == "Te":
        rows = [[1.0 - Q2 / 2.0, 0.0, 0.0, Q2 / 2.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0 - Q2, 0.0], [Q2 / 2.0, 0.0, 0.0, 1.0 - Q2 / 2.0]]
    elif op == "Fi":
        rows = [[0.5, 0.0, 1.0, 0.5], [0.0, 1.0, 0.0, 0.0], [-0.5, 0.0, 0.0, 0.5], [0.5, 0.0, -1.0, 0.5]]
    elif op == "Fe":
        rows = [[1.0, 0.0, 0.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
    else:
        raise ValueError(op)
    return torch.tensor(rows, dtype=RDTYPE)


def torch_func_certificate() -> dict[str, Any]:
    x0 = torch.tensor([0.6, 0.1, -0.2, 0.4], dtype=RDTYPE)
    rows: dict[str, Any] = {}
    max_residual = 0.0
    for op in ["Ti", "Te", "Fi", "Fe"]:
        jac = jacfwd(lambda x: source_vector_channel(op, x))(x0)
        expected = analytic_channel_matrix(op)
        residual = py_float(torch.max(torch.abs(jac - expected)))
        rows[op] = {
            "api": "torch.func.jacfwd",
            "input_vector_order": ["a", "u", "v", "d"],
            "jacobian_matches_source_matrix": residual <= TOL,
            "max_abs_residual": residual,
        }
        max_residual = max(max_residual, residual)
    return {"pass": max_residual <= TOL, "max_abs_residual": max_residual, "operators": rows}


def operator_forms() -> dict[str, Any]:
    return {
        "Ti": {
            "source": "Ti(rho)=(1-q1)rho+q1(P0 rho P0+P1 rho P1); Kraus sqrt(1-q1)I,sqrt(q1)P0,sqrt(q1)P1",
            "bloch_map": "(rx,ry,rz)->((1-q1)rx,(1-q1)ry,rz)",
            "generator": "flow at t=1 of L1(rho)=kappa1/2*(sigma_z rho sigma_z-rho), kappa1=-log(1-q1)",
        },
        "Te": {
            "source": "Te(rho)=(1-q2)rho+q2(Q+ rho Q+ + Q- rho Q-); Kraus sqrt(1-q2)I,sqrt(q2)Q+,sqrt(q2)Q-",
            "bloch_map": "(rx,ry,rz)->(rx,(1-q2)ry,(1-q2)rz)",
            "generator": "flow at t=1 of L2(rho)=kappa2/2*(sigma_x rho sigma_x-rho), kappa2=-log(1-q2)",
        },
        "Fi": {
            "source": "Fi(rho)=U_x(theta) rho U_x(theta)^dagger, U_x=exp(-i theta sigma_x/2)",
            "bloch_map": "(rx,ry,rz)->(rx, ry cos(theta)-rz sin(theta), rz cos(theta)+ry sin(theta))",
            "generator": "flow at t=1 of L3(rho)=-i[(theta/2)sigma_x,rho]",
        },
        "Fe": {
            "source": "Fe(rho)=U_z(phi) rho U_z(phi)^dagger, U_z=exp(-i phi sigma_z/2)",
            "bloch_map": "(rx,ry,rz)->(rx cos(phi)-ry sin(phi), rx sin(phi)+ry cos(phi), rz)",
            "generator": "flow at t=1 of L4(rho)=-i[(phi/2)sigma_z,rho]",
        },
    }


def shared_scalars(rep: dict[str, Any], props: dict[str, Any], ctable: dict[str, Any], negatives: dict[str, Any], torch_func: dict[str, Any]) -> dict[str, float]:
    scalars: dict[str, float] = {}
    for op in ["Ti", "Te", "Fi", "Fe"]:
        scalars[f"{op}_representation_max_diff"] = float(rep[op]["max_diff"])
    for a, b in [("Ti", "Fi"), ("Te", "Fe"), ("Fi", "Fe")]:
        scalars[f"commutator_{a}_{b}_rho0_trace_norm"] = float(ctable["table"][a][b])
    for key, value in ctable["known_zeros"].items():
        scalars[f"commutator_{key.replace('-', '_')}_zero_trace_norm"] = float(value)
    for op in ["Ti", "Te"]:
        for state in ["rho_0", "rho_1"]:
            scalars[f"{op}_{state}_entropy_delta"] = float(props[op]["states"][state]["entropy_delta"])
            scalars[f"{op}_{state}_coherence_shrink_residual"] = float(props[op]["states"][state]["coherence_shrink_residual"])
    for op in ["Fi", "Fe"]:
        for state in ["rho_0", "rho_1"]:
            scalars[f"{op}_{state}_purity_delta_abs"] = float(props[op]["states"][state]["purity_delta_abs"])
    scalars["wrong_basis_Ti_y_rho0_trace_norm_diff"] = float(negatives["wrong_basis_Ti_y"]["rows"]["rho_0"]["trace_norm_Dz_minus_Dy"])
    scalars["swapped_parameter_pinned_diff"] = float(negatives["swapped_parameter_control"]["pinned_swap_max_trace_norm_diff"])
    scalars["swapped_parameter_offpin_diff"] = float(negatives["swapped_parameter_control"]["off_pin_swap_max_trace_norm_diff"])
    scalars["torch_func_jacfwd_max_residual"] = float(torch_func["max_abs_residual"])
    return scalars


def build_result() -> dict[str, Any]:
    states = pinned_states()
    rep = {op: representation_certificate(op, states) for op in ["Ti", "Te", "Fi", "Fe"]}
    cptp = {op: cptp_certificate(op) for op in ["Ti", "Te", "Fi", "Fe"]}
    props = {op: property_certificate(op, states) for op in ["Ti", "Te", "Fi", "Fe"]}
    ctable = commutator_table(states["rho_0"])
    negatives = negative_controls(states)
    torch_func = torch_func_certificate()
    controls = {
        "representation_consistency": all(row["pass"] for row in rep.values()),
        "cptp_all": all(row["choi_psd"] and row["trace_preserving"] for row in cptp.values()),
        "property_certificates": all(row["pass"] for row in props.values()),
        "commutator_known_zeros": ctable["known_zero_pass"],
        "commutator_known_nonzeros": ctable["known_nonzero_pass"],
        "wrong_basis_negative_control": negatives["wrong_basis_Ti_y"]["different_values"],
        "swapped_parameter_control_honest": negatives["swapped_parameter_control"]["declared_pin_degenerate"]
        and negatives["swapped_parameter_control"]["pinned_swap_is_not_falsifying"]
        and negatives["swapped_parameter_control"]["off_pin_swap_falsifies"],
        "torch_func_jacfwd_source_matrices": torch_func["pass"],
        "reads_peer_result_false": READS_PEER_RESULT is False,
    }
    all_pass = bool(all(controls.values()))
    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": f"{SIM_ID}_{ENGINE}",
        "engine": ENGINE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "reads_peer_result": READS_PEER_RESULT,
        "engine_contract": {"mode": "all_three_full_sims", "reads_peer_result": READS_PEER_RESULT},
        "pin_spec": PIN_SPEC,
        "pin_identity": {
            "q1": Q1,
            "q2": Q2,
            "theta": "pi/2",
            "phi": "pi/2",
            "rho_0": "psi(0.3,0.2,pi/8) per scaffold 1.1",
            "rho_1": "0.7*rho_0+0.3*I/2",
        },
        "source_citations": SOURCE_CITATIONS,
        "operator_forms": operator_forms(),
        "representation_consistency": rep,
        "cptp_certificates": cptp,
        "property_certificates": props,
        "commutator_table": ctable,
        "negative_controls": negatives,
        "torch_func_certificate": torch_func,
        "operator_backlog": OPERATOR_BACKLOG,
        "controls": controls,
        "shared_scalars": shared_scalars(rep, props, ctable, negatives, torch_func),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_exercise_map": {
            tool: {
                "tool": tool,
                "depth": TOOL_INTEGRATION_DEPTH[tool],
                "capability_receipt_path": CAPABILITY_PROBES.get(tool),
                "computed_what": TOOL_MANIFEST[tool]["reason"],
                "gates": ["all_pass"] if TOOL_INTEGRATION_DEPTH[tool] == "load_bearing" else [],
            }
            for tool in TOOL_MANIFEST
        },
        "packages_used": ["torch", "torch.func"],
        "aligned_packages_load_bearing": ["torch.func"],
        "claim_path_tools": ["torch", "torch.func"],
        "control_only_tools": [],
        "all_pass": all_pass,
    }


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"engine": ENGINE, "result_path": str(RESULT_PATH), "all_pass": result["all_pass"]}, indent=2))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
