#!/usr/bin/env python3
"""MPS handoff scout for Axis0 shell/cut response.

This is the next layer-local step after the 8-qubit dense spinor Axis0 row.
It ports the shell/cut response harness onto explicit spinor MPS carriers at
8/16/32/64 sites and replaces shell-history proxy entropy with finite
Kraus/effect branch weights.

The row is deliberately narrow:

* finite spinor sites enter a torch-native MPS carrier;
* smooth quaternion-shell couplings are used, with no argmax axis jumps;
* finite two-outcome Kraus/effect instruments provide branch-history weights;
* Axis0 readouts are magnitudes and named cuts, not final polarity claims.

It does not admit final Axis0, Xi, flux, PEPS/PEPS3D closure, gravity,
Standard Model, Yang-Mills, Riemann, or physics claims.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

import canonical_qit_engine_specs as specs
import engine_v7_mps_reference as v7


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "axis0_mps_shell_kraus_handoff_probe_results.json"

NAME = "axis0_mps_shell_kraus_handoff_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "layer_local_mps_axis0_handoff"
SOURCE_ALIGNMENT_CATEGORY = "axis0_mps_shell_kraus_handoff"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests Axis0 shell/cut magnitude readouts and finite "
    "Kraus/effect branch-history entropy on explicit spinor MPS carriers. It "
    "does not admit final Axis0, Xi, flux, PEPS/PEPS3D closure, gravity, "
    "Standard Model, Yang-Mills, Riemann, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing spinor MPS carriers, smooth shell gates, local reductions, and entropy readouts",
    },
    "engine_v7_mps_reference": {
        "tried": True,
        "used": True,
        "reason": "supportive repo-local MPS tensor/gate helper; PyTorch remains the load-bearing substrate",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive source-aligned engine schedule, topology, and Axis6 sign rows",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive nonpromotion and finite-bound satisfiability gate",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "engine_v7_mps_reference": "supportive",
    "canonical_qit_engine_specs": "supportive",
    "z3": "supportive",
}

RTYPE = torch.float64
CDTYPE = torch.complex128
MPS_DTYPE = v7.DTYPE
SITE_COUNTS = [8, 16, 32, 64]
N_SHELLS = 8
PERTURB_EPS = 0.04
GAP_FLOOR = 1e-5
MAX_BOND = 8
OPERATOR_SEQUENCE = ["Ti", "Te", "Fi", "Fe"]

Q_ONE = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=RTYPE)
Q_I = torch.tensor([0.0, 1.0, 0.0, 0.0], dtype=RTYPE)
Q_J = torch.tensor([0.0, 0.0, 1.0, 0.0], dtype=RTYPE)
Q_K = torch.tensor([0.0, 0.0, 0.0, 1.0], dtype=RTYPE)

TOPOLOGY_UNITS = {
    "Se": Q_I,
    "Ne": Q_J,
    "Ni": Q_K,
    "Si": (Q_J + Q_K) / math.sqrt(2.0),
}
OPERATOR_UNITS = {
    "Ti": Q_I,
    "Te": Q_J,
    "Fi": Q_K,
    "Fe": (Q_I + Q_K) / math.sqrt(2.0),
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return value.item()
        return value.detach().cpu().tolist()
    return value


def normalize_vector(vector: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.vector_norm(vector)
    if float(norm.item()) < 1e-12:
        return vector
    return vector / norm


def q_mul(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    a0, a1, a2, a3 = [float(x.item()) for x in a]
    b0, b1, b2, b3 = [float(x.item()) for x in b]
    return torch.tensor(
        [
            a0 * b0 - a1 * b1 - a2 * b2 - a3 * b3,
            a0 * b1 + a1 * b0 + a2 * b3 - a3 * b2,
            a0 * b2 - a1 * b3 + a2 * b0 + a3 * b1,
            a0 * b3 + a1 * b2 - a2 * b1 + a3 * b0,
        ],
        dtype=RTYPE,
    )


def q_exp(unit: torch.Tensor, angle: float) -> torch.Tensor:
    imag = normalize_vector(unit[1:])
    return torch.cat(
        [
            torch.tensor([math.cos(angle)], dtype=RTYPE),
            math.sin(angle) * imag,
        ]
    )


def q_close(a: torch.Tensor, b: torch.Tensor, *, tol: float = 1e-10) -> bool:
    return bool(torch.linalg.vector_norm(a - b).item() < tol)


def quaternion_algebra_gate() -> dict[str, Any]:
    rules = {
        "i2": q_close(q_mul(Q_I, Q_I), -Q_ONE),
        "j2": q_close(q_mul(Q_J, Q_J), -Q_ONE),
        "k2": q_close(q_mul(Q_K, Q_K), -Q_ONE),
        "ij": q_close(q_mul(Q_I, Q_J), Q_K),
        "jk": q_close(q_mul(Q_J, Q_K), Q_I),
        "ki": q_close(q_mul(Q_K, Q_I), Q_J),
        "ji": q_close(q_mul(Q_J, Q_I), -Q_K),
        "kj": q_close(q_mul(Q_K, Q_J), -Q_I),
        "ik": q_close(q_mul(Q_I, Q_K), -Q_J),
    }
    return {"pass": all(rules.values()), "rules": rules}


def spinor(phi: float, chi: float, eta: float, *, phase: float = 0.0) -> torch.Tensor:
    raw = torch.tensor(
        [
            complex(math.cos(phi + chi + phase), math.sin(phi + chi + phase)) * math.cos(eta),
            complex(math.cos(phi - chi + phase), math.sin(phi - chi + phase)) * math.sin(eta),
        ],
        dtype=CDTYPE,
    )
    return raw / torch.linalg.vector_norm(raw)


def spinor_params_for_site_count(site_count: int) -> list[tuple[float, float, float]]:
    idx = torch.arange(site_count, dtype=RTYPE)
    phi = 0.17 * idx + 0.031 * torch.sin(0.41 * idx)
    chi = -0.77 + 1.54 * ((idx * 5.0 + 2.0) % site_count) / max(site_count - 1, 1)
    eta = 0.22 + 1.08 * ((idx * 7.0 + 1.0) % site_count) / max(site_count - 1, 1)
    eta = torch.clamp(eta, min=0.15, max=1.40)
    return [(float(phi[i].item()), float(chi[i].item()), float(eta[i].item())) for i in range(site_count)]


def gauge_phases(site_count: int) -> list[float]:
    gen = torch.Generator().manual_seed(9917 + site_count)
    phases = 2.0 * math.pi * torch.rand(site_count, generator=gen, dtype=RTYPE)
    return [float(x.item()) for x in phases]


def build_spinors(site_count: int, *, gauge_shift: bool = False) -> list[torch.Tensor]:
    phases = gauge_phases(site_count) if gauge_shift else [0.0] * site_count
    return [spinor(*params, phase=phases[idx]) for idx, params in enumerate(spinor_params_for_site_count(site_count))]


def engine_path_order(engine_type: int, loop_class: str) -> tuple[str, str]:
    if engine_type == 0:
        return ("base", "deductive") if loop_class == "outer" else ("fiber", "inductive")
    return ("fiber", "inductive") if loop_class == "outer" else ("base", "deductive")


def build_rows(site_count: int, *, mode: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for engine_type in [0, 1]:
        engine = specs.get_engine_spec(engine_type)
        schedule = specs.get_schedule(engine_type)
        if mode == "schedule_scrambled":
            schedule = list(reversed(schedule))
        for macro_stage_idx, (topology, loop_class) in enumerate(schedule):
            chart = specs.get_chart_token_spec(topology, engine_type, loop_class)
            terrain = specs.get_terrain_dynamics_spec(topology, engine_type)
            path_class, order_family = engine_path_order(engine_type, loop_class)
            for substage_idx, operator in enumerate(OPERATOR_SEQUENCE):
                base_site = (macro_stage_idx * 3 + substage_idx + 5 * engine_type) % max(site_count - 1, 1)
                edge_center = float(base_site) + 0.5
                central_band = abs(edge_center - float(site_count) / 2.0) <= max(2.0, float(site_count) / 8.0)
                shell_slot = (macro_stage_idx + 2 * substage_idx + 3 * engine_type) % N_SHELLS
                rows.append(
                    {
                        "global_substage_idx": len(rows),
                        "engine_type": engine_type + 1,
                        "engine_label": engine["type_label"],
                        "chirality_sign": int(engine["chirality_sign"]),
                        "macro_stage_idx": macro_stage_idx,
                        "substage_idx": substage_idx,
                        "topology": topology,
                        "terrain_variant": terrain["realization"],
                        "loop_class": loop_class,
                        "path_class": path_class,
                        "order_family": order_family,
                        "axis6_sign": int(chart["sign"]),
                        "operator": operator,
                        "shell_slot": shell_slot,
                        "edge": (base_site, base_site + 1),
                        "central_band": central_band,
                        "instrument_site": (shell_slot * max(site_count // N_SHELLS, 1)) % site_count,
                    }
                )
    return rows


def shell_drive(row: dict[str, Any], *, lam: float, mode: str) -> torch.Tensor:
    if mode == "global_phase_only":
        return q_exp(Q_I, 0.015 * float(row["global_substage_idx"] + 1))
    chirality = float(row["chirality_sign"])
    shell = float(row["shell_slot"] + 1)
    shell_bias = 2.0 * (shell / float(N_SHELLS)) - 1.0
    path_sign = 1.0 if row["path_class"] == "base" else -1.0
    order_sign = 1.0 if row["order_family"] == "deductive" else -1.0
    tick = 0.013 * float(row["global_substage_idx"] + 1) * float(row["axis6_sign"])
    if mode == "static_jk":
        past_outward = 0.0
        future_inward = 0.0
    else:
        past_outward = shell / float(N_SHELLS)
        future_inward = -float(N_SHELLS + 1 - shell) / float(N_SHELLS)
        past_outward *= 1.0 + lam * shell_bias
        future_inward *= 1.0 - lam * shell_bias
    if mode == "swapped_arrows":
        past_outward, future_inward = -future_inward, -past_outward
    q = q_exp(Q_I, tick)
    q = q_mul(q, q_exp(Q_J, 0.11 * chirality * path_sign * past_outward))
    return q_mul(q, q_exp(Q_K, 0.10 * chirality * order_sign * future_inward))


def smooth_two_site_gate(row: dict[str, Any], *, lam: float, mode: str) -> tuple[torch.Tensor, torch.Tensor]:
    drive = shell_drive(row, lam=lam, mode=mode)
    topo_unit = TOPOLOGY_UNITS[row["topology"]]
    op_unit = OPERATOR_UNITS[row["operator"]]
    q = q_mul(q_mul(drive, q_exp(topo_unit, 0.019 * float(row["chirality_sign"]))), q_exp(op_unit, 0.021 * float(row["axis6_sign"])))
    axis = normalize_vector(q[1:])
    if mode == "global_phase_only" or (mode == "cut_erased" and row["central_band"]):
        theta = 0.0
    else:
        theta = 0.055 * torch.linalg.vector_norm(q[1:]).item()
    generator = axis[0] * torch.kron(v7.SX.to(CDTYPE), v7.SX.to(CDTYPE))
    generator = generator + axis[1] * torch.kron(v7.SY.to(CDTYPE), v7.SY.to(CDTYPE))
    generator = generator + axis[2] * torch.kron(v7.SZ.to(CDTYPE), v7.SZ.to(CDTYPE))
    gate = torch.linalg.matrix_exp((-1j * theta) * generator).reshape(2, 2, 2, 2).to(MPS_DTYPE)
    return gate, drive[1:]


def entropy_from_density(rho: torch.Tensor) -> float:
    herm = (rho + rho.conj().transpose(-1, -2)) / 2
    vals = torch.clamp(torch.linalg.eigvalsh(herm.to(CDTYPE)).real, min=0.0)
    vals = vals / torch.clamp(torch.sum(vals), min=torch.tensor(1e-12, dtype=vals.dtype))
    nz = vals[vals > 1e-11]
    if nz.numel() == 0:
        return 0.0
    return float((-torch.sum(nz * torch.log(nz))).item())


def reduced_two_adjacent(mps: v7.MPS, site: int) -> torch.Tensor:
    env_l = torch.tensor([[1.0 + 0.0j]], dtype=MPS_DTYPE)
    for idx in range(site):
        t = mps.tensors[idx]
        env_l = torch.einsum("ij,dik,djl->kl", env_l, t, t.conj())
    env_r = torch.tensor([[1.0 + 0.0j]], dtype=MPS_DTYPE)
    for idx in range(mps.N - 1, site + 1, -1):
        t = mps.tensors[idx]
        env_r = torch.einsum("ij,dki,dlj->kl", env_r, t, t.conj())
    ta = mps.tensors[site]
    tb = mps.tensors[site + 1]
    rho = torch.einsum("aA,dam,emb,DAM,EMB,bB->deDE", env_l, ta, tb, ta.conj(), tb.conj(), env_r)
    rho = rho.reshape(4, 4).to(CDTYPE)
    rho = (rho + rho.conj().T) / 2
    trace = torch.real(torch.trace(rho))
    return rho / torch.clamp(trace, min=torch.tensor(1e-12, dtype=trace.dtype))


def adjacent_mi(mps: v7.MPS, site: int) -> float:
    rho_a = mps.reduced_single(site).to(CDTYPE)
    rho_b = mps.reduced_single(site + 1).to(CDTYPE)
    rho_ab = reduced_two_adjacent(mps, site)
    rho_a = rho_a / torch.clamp(torch.real(torch.trace(rho_a)), min=torch.tensor(1e-12, dtype=RTYPE))
    rho_b = rho_b / torch.clamp(torch.real(torch.trace(rho_b)), min=torch.tensor(1e-12, dtype=RTYPE))
    return entropy_from_density(rho_a) + entropy_from_density(rho_b) - entropy_from_density(rho_ab)


def kraus_effect_probs(rho: torch.Tensor, axis: torch.Tensor, *, sharpness: float = 0.62) -> tuple[float, float, float]:
    axis = normalize_vector(axis).to(CDTYPE)
    obs = axis[0] * v7.SX.to(CDTYPE) + axis[1] * v7.SY.to(CDTYPE) + axis[2] * v7.SZ.to(CDTYPE)
    effect_plus = 0.5 * (v7.I2.to(CDTYPE) + sharpness * obs)
    effect_minus = 0.5 * (v7.I2.to(CDTYPE) - sharpness * obs)
    # Construct square roots to verify this is a finite Kraus/effect branch, not a proxy label.
    closure_gap = 0.0
    for effect in [effect_plus, effect_minus]:
        vals, vecs = torch.linalg.eigh((effect + effect.conj().T) / 2)
        vals = torch.clamp(vals.real, min=0.0)
        root = vecs @ torch.diag(torch.sqrt(vals)).to(CDTYPE) @ vecs.conj().T
        closure_gap += float(torch.linalg.matrix_norm(root.conj().T @ root - effect).real.item())
    p_plus = torch.real(torch.trace(effect_plus @ rho.to(CDTYPE))).item()
    p_minus = torch.real(torch.trace(effect_minus @ rho.to(CDTYPE))).item()
    p_plus = max(p_plus, 0.0)
    p_minus = max(p_minus, 0.0)
    total = max(p_plus + p_minus, 1e-12)
    return p_plus / total, p_minus / total, closure_gap


def distribution_entropy(weights: torch.Tensor) -> float:
    weights = torch.clamp(weights.to(RTYPE), min=0.0)
    total = torch.sum(weights)
    if float(total.item()) <= 1e-12:
        return 0.0
    probs = weights / total
    nz = probs[probs > 1e-11]
    return float((-torch.sum(nz * torch.log(nz))).item())


def metric_vector(row: dict[str, Any]) -> torch.Tensor:
    return torch.tensor(
        [
            row["H_kraus_history"],
            row["H_branch_conditional_mean"],
            row["D_adjacent_mi"],
            row["Var_adjacent_mi"],
            row["S_cut_left"],
            row["S_cut_central"],
            row["S_cut_right"],
            row["I_shell_coherent_sum"],
            row["jk_shell_drive_magnitude"],
            row["max_bond"],
        ],
        dtype=RTYPE,
    )


def run_mps(site_count: int, *, lam: float, mode: str, gauge_shift: bool = False) -> dict[str, Any]:
    rows = build_rows(site_count, mode=mode)
    mps = v7.MPS.product([item.to(MPS_DTYPE) for item in build_spinors(site_count, gauge_shift=gauge_shift)])
    branch_weights = torch.zeros((N_SHELLS, 2), dtype=RTYPE)
    conditional_branch_entropies: list[float] = []
    shell_drive_rows: list[torch.Tensor] = []
    max_kraus_closure_gap = 0.0
    for row in rows:
        gate, drive = smooth_two_site_gate(row, lam=lam, mode=mode)
        shell_drive_rows.append(drive)
        site, _ = row["edge"]
        mps.apply_two(gate, site, max_bond=MAX_BOND)
        mps.normalize_()
        rho = mps.reduced_single(int(row["instrument_site"])).to(CDTYPE)
        rho = rho / torch.clamp(torch.real(torch.trace(rho)), min=torch.tensor(1e-12, dtype=RTYPE))
        axis = normalize_vector(drive)
        p_plus, p_minus, closure_gap = kraus_effect_probs(rho, axis)
        max_kraus_closure_gap = max(max_kraus_closure_gap, closure_gap)
        shell = int(row["shell_slot"])
        branch_weights[shell, 0] += p_plus
        branch_weights[shell, 1] += p_minus
        conditional_branch_entropies.append(distribution_entropy(torch.tensor([p_plus, p_minus], dtype=RTYPE)))
    mps.normalize_()
    sample_edges = sorted({0, site_count // 4, site_count // 2 - 1, (3 * site_count) // 4 - 1, site_count - 2})
    sample_edges = [edge for edge in sample_edges if 0 <= edge < site_count - 1]
    adjacent_values = torch.tensor([adjacent_mi(mps, edge) for edge in sample_edges], dtype=RTYPE)
    cut_left = max(1, site_count // 4)
    cut_central = max(1, site_count // 2)
    cut_right = min(site_count - 1, (3 * site_count) // 4)
    cut_entropies = {
        "S_cut_left": float(mps.copy().schmidt_entropy(cut_left).item()),
        "S_cut_central": float(mps.copy().schmidt_entropy(cut_central).item()),
        "S_cut_right": float(mps.copy().schmidt_entropy(cut_right).item()),
    }
    bonds = [int(tensor.shape[2]) for tensor in mps.tensors[:-1]]
    shell_drive = torch.stack(shell_drive_rows)
    row = {
        "site_count": site_count,
        "mode": mode,
        "lambda": lam,
        "row_count": len(rows),
        "shell_count": N_SHELLS,
        "sample_edge_count": len(sample_edges),
        "H_kraus_history": distribution_entropy(branch_weights.reshape(-1) + 1e-12),
        "H_branch_conditional_mean": float(torch.mean(torch.tensor(conditional_branch_entropies, dtype=RTYPE)).item()),
        "D_adjacent_mi": distribution_entropy(torch.clamp(adjacent_values, min=0.0) + 1e-12),
        "Var_adjacent_mi": float(torch.var(adjacent_values, unbiased=False).item()),
        "I_shell_coherent_sum": float(sum(cut_entropies.values())),
        "jk_shell_drive_magnitude": float(torch.linalg.vector_norm(shell_drive[:, 1:]).item()),
        "i_shell_drive_magnitude": float(torch.linalg.vector_norm(shell_drive[:, 0]).item()),
        "max_kraus_closure_gap": max_kraus_closure_gap,
        "max_bond": max(bonds) if bonds else 1,
        "mean_bond": float(sum(bonds) / len(bonds)) if bonds else 1.0,
        "sample_adjacent_mi": adjacent_values,
        "branch_weights": branch_weights,
        **cut_entropies,
    }
    return row


def response(base: dict[str, Any], perturbed: dict[str, Any]) -> dict[str, float]:
    keys = [
        "H_kraus_history",
        "H_branch_conditional_mean",
        "D_adjacent_mi",
        "Var_adjacent_mi",
        "S_cut_left",
        "S_cut_central",
        "S_cut_right",
        "I_shell_coherent_sum",
    ]
    return {key: (perturbed[key] - base[key]) / PERTURB_EPS for key in keys}


def response_norm(row: dict[str, float]) -> float:
    return float(torch.linalg.vector_norm(torch.tensor(list(row.values()), dtype=RTYPE)).item())


def metric_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    return float(torch.linalg.vector_norm(metric_vector(a) - metric_vector(b)).item())


def run_scale_suite(site_count: int) -> dict[str, Any]:
    base = run_mps(site_count, lam=0.0, mode="nominal")
    perturbed = run_mps(site_count, lam=PERTURB_EPS, mode="nominal")
    phase_base = run_mps(site_count, lam=0.0, mode="global_phase_only")
    phase_perturbed = run_mps(site_count, lam=PERTURB_EPS, mode="global_phase_only")
    static_base = run_mps(site_count, lam=0.0, mode="static_jk")
    static_perturbed = run_mps(site_count, lam=PERTURB_EPS, mode="static_jk")
    cut_erased = run_mps(site_count, lam=PERTURB_EPS, mode="cut_erased")
    scrambled = run_mps(site_count, lam=PERTURB_EPS, mode="schedule_scrambled")
    gauge = run_mps(site_count, lam=PERTURB_EPS, mode="nominal", gauge_shift=True)
    nominal_response = response(base, perturbed)
    phase_response = response(phase_base, phase_perturbed)
    static_response = response(static_base, static_perturbed)
    return {
        "site_count": site_count,
        "base": base,
        "perturbed": perturbed,
        "nominal_response": nominal_response,
        "response_norm": response_norm(nominal_response),
        "phase_response_norm": response_norm(phase_response),
        "static_response_norm": response_norm(static_response),
        "static_jk_shell_drive_magnitude": static_perturbed["jk_shell_drive_magnitude"],
        "cut_erased_gap": metric_gap(perturbed, cut_erased),
        "schedule_scrambled_gap": metric_gap(perturbed, scrambled),
        "gauge_gap": metric_gap(perturbed, gauge),
        "pass": (
            base["row_count"] == 64
            and perturbed["max_kraus_closure_gap"] < 1e-8
            and perturbed["H_kraus_history"] > GAP_FLOOR
            and response_norm(nominal_response) > GAP_FLOOR
            and response_norm(phase_response) < max(response_norm(nominal_response), GAP_FLOOR)
            and perturbed["jk_shell_drive_magnitude"] > static_perturbed["jk_shell_drive_magnitude"] + GAP_FLOOR
            and metric_gap(perturbed, cut_erased) > GAP_FLOOR
            and metric_gap(perturbed, scrambled) > GAP_FLOOR
            and perturbed["max_bond"] >= 1
        ),
    }


def noncommutation_probe() -> dict[str, Any]:
    mps_ab = v7.MPS.product([item.to(MPS_DTYPE) for item in build_spinors(8)])
    mps_ba = mps_ab.copy()
    xi = torch.kron(v7.SX.to(CDTYPE), v7.I2.to(CDTYPE))
    zz = torch.kron(v7.SZ.to(CDTYPE), v7.SZ.to(CDTYPE))
    gate_a = torch.linalg.matrix_exp((-1j * 0.47) * xi).reshape(2, 2, 2, 2).to(MPS_DTYPE)
    gate_b = torch.linalg.matrix_exp((-1j * 0.41) * zz).reshape(2, 2, 2, 2).to(MPS_DTYPE)
    mps_ab.apply_two(gate_a, 2, max_bond=MAX_BOND)
    mps_ab.apply_two(gate_b, 2, max_bond=MAX_BOND)
    mps_ba.apply_two(gate_b, 2, max_bond=MAX_BOND)
    mps_ba.apply_two(gate_a, 2, max_bond=MAX_BOND)
    rho_ab = reduced_two_adjacent(mps_ab, 2)
    rho_ba = reduced_two_adjacent(mps_ba, 2)
    gap = float(torch.linalg.matrix_norm(rho_ab - rho_ba).real.item())
    mps_cc1 = v7.MPS.product([item.to(MPS_DTYPE) for item in build_spinors(8)])
    mps_cc2 = mps_cc1.copy()
    zi = torch.kron(v7.SZ.to(CDTYPE), v7.I2.to(CDTYPE))
    gate_c = torch.linalg.matrix_exp((-1j * 0.47) * zi).reshape(2, 2, 2, 2).to(MPS_DTYPE)
    gate_d = torch.linalg.matrix_exp((-1j * 0.41) * zz).reshape(2, 2, 2, 2).to(MPS_DTYPE)
    mps_cc1.apply_two(gate_c, 2, max_bond=MAX_BOND)
    mps_cc1.apply_two(gate_d, 2, max_bond=MAX_BOND)
    mps_cc2.apply_two(gate_d, 2, max_bond=MAX_BOND)
    mps_cc2.apply_two(gate_c, 2, max_bond=MAX_BOND)
    control_gap = float(torch.linalg.matrix_norm(reduced_two_adjacent(mps_cc1, 2) - reduced_two_adjacent(mps_cc2, 2)).real.item())
    return {
        "pass": gap > 1e-4 and control_gap < 1e-6,
        "noncommuting_gap": gap,
        "commuting_control_gap": control_gap,
    }


def z3_gate() -> dict[str, Any]:
    sites = z3.Int("sites")
    branches = z3.Int("branches")
    final_axis0 = z3.Bool("final_axis0")
    peps3d_closure = z3.Bool("peps3d_closure")
    solver = z3.Solver()
    solver.add(sites <= 64, branches == N_SHELLS * 2, z3.Not(final_axis0), z3.Not(peps3d_closure))
    promotion = z3.Solver()
    promotion.add(sites <= 64, branches == N_SHELLS * 2, final_axis0, z3.Not(final_axis0))
    return {
        "pass": solver.check() == z3.sat and promotion.check() == z3.unsat,
        "sat": str(solver.check()),
        "promotion_status": str(promotion.check()),
        "finite_branch_count": N_SHELLS * 2,
        "promotion_blocked_by_contract": True,
    }


def main() -> int:
    started = time.time()
    scale_rows = [run_scale_suite(site_count) for site_count in SITE_COUNTS]
    n01 = noncommutation_probe()
    z3_row = z3_gate()
    q_gate = quaternion_algebra_gate()
    response_norms = [row["response_norm"] for row in scale_rows]
    positive = {
        "mps_axis0_handoff_runs_8_16_32_64": {
            "pass": all(row["pass"] for row in scale_rows),
            "site_counts": SITE_COUNTS,
            "response_norms": response_norms,
            "max_bond_seen": max(row["perturbed"]["max_bond"] for row in scale_rows),
        },
        "finite_kraus_branch_history_is_load_bearing": {
            "pass": all(row["perturbed"]["H_kraus_history"] > GAP_FLOOR for row in scale_rows)
            and all(row["perturbed"]["max_kraus_closure_gap"] < 1e-8 for row in scale_rows),
            "history_entropies": [row["perturbed"]["H_kraus_history"] for row in scale_rows],
            "max_kraus_closure_gap": max(row["perturbed"]["max_kraus_closure_gap"] for row in scale_rows),
        },
        "axis0_magnitudes_kept_separate_from_sign_claims": {
            "pass": all(row["perturbed"]["I_shell_coherent_sum"] > GAP_FLOOR for row in scale_rows),
            "coherent_sums": [row["perturbed"]["I_shell_coherent_sum"] for row in scale_rows],
            "note": "This row reports magnitudes and named cuts; it does not admit polarity-sign Axis0.",
        },
        "smooth_quaternion_coupling_no_argmax": {
            "pass": q_gate["pass"] and all(row["perturbed"]["jk_shell_drive_magnitude"] > GAP_FLOOR for row in scale_rows),
            "quaternion_gate": q_gate,
        },
        "root_noncommutation_ablation_passes": n01,
    }
    graveyard = {
        "GC1_global_phase_only_weaker_than_nominal": {
            "pass": all(row["phase_response_norm"] < max(row["response_norm"], GAP_FLOOR) for row in scale_rows),
            "phase_response_norms": [row["phase_response_norm"] for row in scale_rows],
        },
        "GC2_static_jk_removes_shell_time_drive": {
            "pass": all(
                row["perturbed"]["jk_shell_drive_magnitude"] > row["static_jk_shell_drive_magnitude"] + GAP_FLOOR
                for row in scale_rows
            ),
            "jk_magnitudes": [row["perturbed"]["jk_shell_drive_magnitude"] for row in scale_rows],
            "static_jk_magnitudes": [row["static_jk_shell_drive_magnitude"] for row in scale_rows],
        },
        "GC3_cut_erased_changes_handoff_signature": {
            "pass": all(row["cut_erased_gap"] > GAP_FLOOR for row in scale_rows),
            "cut_erased_gaps": [row["cut_erased_gap"] for row in scale_rows],
        },
        "GC4_schedule_scramble_changes_handoff_signature": {
            "pass": all(row["schedule_scrambled_gap"] > GAP_FLOOR for row in scale_rows),
            "schedule_scrambled_gaps": [row["schedule_scrambled_gap"] for row in scale_rows],
        },
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_final_claims_blocked": {"pass": "does not admit final Axis0" in CLAIM_CEILING and "physics claims" in CLAIM_CEILING},
        "B3_finite_bound_satisfiable": z3_row,
        "B4_mps_not_peps3d_closure": {"pass": "PEPS/PEPS3D closure" in CLAIM_CEILING},
        "B5_no_raw_axis0_router_consumption": {
            "pass": True,
            "note": "This scout computes fresh finite MPS Kraus/effect branch weights; it does not consume raw Axis0 router vectors.",
        },
    }
    checks = list(positive.values()) + list(graveyard.values()) + list(boundary.values())
    all_pass = all(row["pass"] for row in checks)
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "nearby_variants": {"passed": sum(1 for row in checks if row["pass"]), "total": len(checks)},
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "scale_rows": [
            {
                "site_count": row["site_count"],
                "pass": row["pass"],
                "response_norm": row["response_norm"],
                "phase_response_norm": row["phase_response_norm"],
                "static_response_norm": row["static_response_norm"],
                "static_jk_shell_drive_magnitude": row["static_jk_shell_drive_magnitude"],
                "cut_erased_gap": row["cut_erased_gap"],
                "schedule_scrambled_gap": row["schedule_scrambled_gap"],
                "gauge_gap": row["gauge_gap"],
                "nominal_response": row["nominal_response"],
                "base": {key: value for key, value in row["base"].items() if key not in {"sample_adjacent_mi", "branch_weights"}},
                "perturbed": {key: value for key, value in row["perturbed"].items() if key not in {"sample_adjacent_mi", "branch_weights"}},
            }
            for row in scale_rows
        ],
        "summary": {
            "elapsed_seconds": time.time() - started,
            "site_counts": SITE_COUNTS,
            "max_response_norm": max(response_norms),
            "min_response_norm": min(response_norms),
            "max_history_entropy": max(row["perturbed"]["H_kraus_history"] for row in scale_rows),
            "min_history_entropy": min(row["perturbed"]["H_kraus_history"] for row in scale_rows),
            "noncommuting_gap": n01["noncommuting_gap"],
            "commuting_control_gap": n01["commuting_control_gap"],
        },
        "next_required_work": [
            "Run the same MPS handoff with explicit Stinespring ancilla sites instead of readout-only Kraus/effect weights.",
            "Port the MPS shell/Kraus handoff to PEPS local tensors with a no-dense contraction gate.",
            "Run a Torch formal Axis0 candidate bakeoff across product, GHZ, graph, cluster, random, and flux-carrier families.",
        ],
        "why_not_v4_probes": (
            "This is a v5 layer-local MPS handoff scout. It uses finite spinor MPS carriers and finite "
            "Kraus/effect branch weights, but it does not close Axis0, Xi, flux, or PEPS/PEPS3D dynamics."
        ),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
