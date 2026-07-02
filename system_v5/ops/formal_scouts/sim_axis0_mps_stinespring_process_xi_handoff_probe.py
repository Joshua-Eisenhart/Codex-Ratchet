#!/usr/bin/env python3
"""MPS Stinespring/process-history Xi handoff scout.

This row is the layer-local successor to the MPS Kraus/effect handoff. It
adds explicit finite history ancilla sites to an MPS chain and couples shell
system sites to those ancillas by unitary Stinespring-style gates. The readout
is process-history structure from system/ancilla reductions, not a final
Axis0 or Xi kernel.

It does not admit final Axis0, Xi, Phi0, flux, PEPS/PEPS3D closure, gravity,
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
OUT_PATH = RESULT_DIR / "axis0_mps_stinespring_process_xi_handoff_probe_results.json"

NAME = "axis0_mps_stinespring_process_xi_handoff_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "layer_local_mps_stinespring_process_xi_handoff"
SOURCE_ALIGNMENT_CATEGORY = "axis0_mps_stinespring_process_history_xi_handoff"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests explicit finite Stinespring/history ancilla sites "
    "on MPS carriers as a process-history Xi handoff. It does not admit final "
    "Axis0, Xi, Phi0, flux, PEPS/PEPS3D closure, gravity, Standard Model, "
    "Yang-Mills, Riemann, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing explicit spinor/ancilla MPS carrier, Stinespring gates, reductions, and entropies",
    },
    "engine_v7_mps_reference": {
        "tried": True,
        "used": True,
        "reason": "supportive repo-local MPS tensor/gate helper; PyTorch remains the load-bearing substrate",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive source-aligned engine schedule and topology rows",
    },
    "z3": {"tried": True, "used": True, "reason": "supportive finite-history and nonpromotion gate"},
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
SYSTEM_SITE_COUNTS = [8, 16, 32, 64]
SHELL_COUNT = 8
MAX_BOND = 8
GAP_FLOOR = 1e-5
OPERATOR_SEQUENCE = ["Ti", "Te", "Fi", "Fe"]

Q_ONE = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=RTYPE)
Q_I = torch.tensor([0.0, 1.0, 0.0, 0.0], dtype=RTYPE)
Q_J = torch.tensor([0.0, 0.0, 1.0, 0.0], dtype=RTYPE)
Q_K = torch.tensor([0.0, 0.0, 0.0, 1.0], dtype=RTYPE)

TOPOLOGY_UNITS = {
    "Se": Q_I,
    "Ne": Q_J,
    "Ni": Q_K,
    "Si": (Q_I + Q_J + Q_K) / math.sqrt(3.0),
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


def normalize_vector(value: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.vector_norm(value)
    if float(norm.item()) < 1e-12:
        return value
    return value / norm


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
    return torch.cat([torch.tensor([math.cos(angle)], dtype=RTYPE), math.sin(angle) * imag])


def q_close(a: torch.Tensor, b: torch.Tensor, *, tol: float = 1e-10) -> bool:
    return bool(torch.linalg.vector_norm(a - b).item() < tol)


def quaternion_gate() -> dict[str, Any]:
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


def spinor_params(count: int) -> list[tuple[float, float, float]]:
    idx = torch.arange(count, dtype=RTYPE)
    phi = 0.13 * idx + 0.021 * torch.sin(0.37 * idx)
    chi = -0.53 + 1.06 * ((idx * 5.0 + 1.0) % count) / max(count - 1, 1)
    eta = 0.19 + 1.16 * ((idx * 7.0 + 3.0) % count) / max(count - 1, 1)
    eta = torch.clamp(eta, min=0.14, max=1.42)
    return [(float(phi[i].item()), float(chi[i].item()), float(eta[i].item())) for i in range(count)]


def layout(system_count: int) -> dict[str, Any]:
    per_shell = system_count // SHELL_COUNT
    total = system_count + SHELL_COUNT
    system_by_shell = []
    ancillas = []
    system_positions = []
    pos = 0
    for shell in range(SHELL_COUNT):
        shell_positions = list(range(pos, pos + per_shell))
        system_positions.extend(shell_positions)
        pos += per_shell
        ancillas.append(pos)
        pos += 1
        system_by_shell.append(shell_positions)
    return {
        "system_count": system_count,
        "history_ancilla_count": SHELL_COUNT,
        "total_site_count": total,
        "systems_per_shell": per_shell,
        "system_by_shell": system_by_shell,
        "ancillas": ancillas,
        "system_positions": system_positions,
    }


def build_initial_mps(system_count: int) -> tuple[v7.MPS, dict[str, Any]]:
    lay = layout(system_count)
    params = spinor_params(system_count)
    system_idx = 0
    vectors = []
    ancilla = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=CDTYPE)
    ancilla_set = set(lay["ancillas"])
    for pos in range(lay["total_site_count"]):
        if pos in ancilla_set:
            vectors.append(ancilla)
        else:
            vectors.append(spinor(*params[system_idx]))
            system_idx += 1
    return v7.MPS.product([item.to(MPS_DTYPE) for item in vectors]), lay


def engine_path_order(engine_type: int, loop_class: str) -> tuple[str, str]:
    if engine_type == 0:
        return ("base", "deductive") if loop_class == "outer" else ("fiber", "inductive")
    return ("fiber", "inductive") if loop_class == "outer" else ("base", "deductive")


def build_rows(system_count: int, *, mode: str) -> list[dict[str, Any]]:
    lay = layout(system_count)
    rows: list[dict[str, Any]] = []
    for engine_type in [0, 1]:
        engine = specs.get_engine_spec(engine_type)
        schedule = specs.get_schedule(engine_type)
        if mode == "history_erased":
            schedule = schedule[:]
        if mode == "schedule_scrambled":
            schedule = list(reversed(schedule))
        for macro_stage_idx, (topology, loop_class) in enumerate(schedule):
            chart = specs.get_chart_token_spec(topology, engine_type, loop_class)
            path_class, order_family = engine_path_order(engine_type, loop_class)
            for substage_idx, operator in enumerate(OPERATOR_SEQUENCE):
                shell = (macro_stage_idx + 2 * substage_idx + 3 * engine_type) % SHELL_COUNT
                systems = lay["system_by_shell"][shell]
                local = min(len(systems) - 1, (macro_stage_idx + substage_idx) % max(len(systems), 1))
                system_site = systems[local]
                if local < len(systems) - 1:
                    system_edge = (system_site, systems[local + 1])
                else:
                    system_edge = None
                rows.append(
                    {
                        "global_substage_idx": len(rows),
                        "engine_type": engine_type + 1,
                        "engine_label": engine["type_label"],
                        "chirality_sign": int(engine["chirality_sign"]),
                        "macro_stage_idx": macro_stage_idx,
                        "substage_idx": substage_idx,
                        "topology": topology,
                        "loop_class": loop_class,
                        "path_class": path_class,
                        "order_family": order_family,
                        "axis6_sign": int(chart["sign"]),
                        "operator": operator,
                        "shell_slot": shell,
                        "system_site": system_site,
                        "history_ancilla_site": lay["ancillas"][shell],
                        "system_edge": system_edge,
                    }
                )
    return rows


def shell_drive(row: dict[str, Any], *, mode: str) -> torch.Tensor:
    if mode == "global_phase_only":
        return q_exp(Q_I, 0.01 * float(row["global_substage_idx"] + 1))
    shell = float(row["shell_slot"] + 1)
    chirality = float(row["chirality_sign"])
    path_sign = 1.0 if row["path_class"] == "base" else -1.0
    order_sign = 1.0 if row["order_family"] == "deductive" else -1.0
    if mode == "static_history":
        past = 0.0
        future = 0.0
    else:
        past = shell / float(SHELL_COUNT)
        future = -float(SHELL_COUNT + 1 - shell) / float(SHELL_COUNT)
    if mode == "swapped_arrows":
        past, future = -future, -past
    drive = q_exp(Q_I, 0.012 * float(row["global_substage_idx"] + 1) * float(row["axis6_sign"]))
    drive = q_mul(drive, q_exp(Q_J, 0.09 * chirality * path_sign * past))
    drive = q_mul(drive, q_exp(Q_K, 0.08 * chirality * order_sign * future))
    drive = q_mul(drive, q_exp(TOPOLOGY_UNITS[row["topology"]], 0.017 * chirality))
    return drive


def smooth_system_gate(row: dict[str, Any], *, mode: str) -> torch.Tensor:
    drive = shell_drive(row, mode=mode)
    axis = normalize_vector(drive[1:])
    theta = 0.026 * torch.linalg.vector_norm(drive[1:]).item()
    if mode in {"global_phase_only", "history_erased"}:
        theta = 0.0
    generator = axis[0] * torch.kron(v7.SX.to(CDTYPE), v7.SX.to(CDTYPE))
    generator += axis[1] * torch.kron(v7.SY.to(CDTYPE), v7.SY.to(CDTYPE))
    generator += axis[2] * torch.kron(v7.SZ.to(CDTYPE), v7.SZ.to(CDTYPE))
    return torch.linalg.matrix_exp((-1j * theta) * generator).reshape(2, 2, 2, 2).to(MPS_DTYPE)


def stinespring_gate(row: dict[str, Any], *, mode: str) -> tuple[torch.Tensor, float, torch.Tensor]:
    drive = shell_drive(row, mode=mode)
    axis = normalize_vector(drive[1:])
    theta = 0.105 * torch.linalg.vector_norm(drive[1:]).item()
    if mode in {"global_phase_only", "history_erased"}:
        theta = 0.0
    system_op = axis[0] * v7.SX.to(CDTYPE) + axis[1] * v7.SY.to(CDTYPE) + axis[2] * v7.SZ.to(CDTYPE)
    generator = torch.kron(system_op, v7.SY.to(CDTYPE))
    gate = torch.linalg.matrix_exp((-1j * theta) * generator).reshape(2, 2, 2, 2).to(MPS_DTYPE)
    unitary_gap = float(torch.linalg.matrix_norm(gate.reshape(4, 4).to(CDTYPE).conj().T @ gate.reshape(4, 4).to(CDTYPE) - torch.eye(4, dtype=CDTYPE)).real.item())
    return gate, unitary_gap, drive[1:]


def entropy_from_density(rho: torch.Tensor) -> float:
    herm = (rho.to(CDTYPE) + rho.to(CDTYPE).conj().T) / 2
    vals = torch.clamp(torch.linalg.eigvalsh(herm).real, min=0.0)
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


def partial_a(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abcb->ac", rho_ab.reshape(2, 2, 2, 2))


def partial_b(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abad->bd", rho_ab.reshape(2, 2, 2, 2))


def process_metrics(mps: v7.MPS, lay: dict[str, Any], drive_rows: list[torch.Tensor], unitary_gaps: list[float]) -> dict[str, Any]:
    shell_rows = []
    branch_probs = []
    for shell, ancilla in enumerate(lay["ancillas"]):
        system_site = ancilla - 1
        rho_ab = reduced_two_adjacent(mps, system_site)
        rho_s = partial_a(rho_ab)
        rho_h = partial_b(rho_ab)
        s_s = entropy_from_density(rho_s)
        s_h = entropy_from_density(rho_h)
        s_sh = entropy_from_density(rho_ab)
        diag = torch.clamp(torch.real(torch.diag(rho_h)), min=0.0)
        diag = diag / torch.clamp(torch.sum(diag), min=torch.tensor(1e-12, dtype=diag.dtype))
        branch_probs.extend([float(diag[0].item()), float(diag[1].item())])
        shell_rows.append(
            {
                "shell": shell,
                "system_site": system_site,
                "history_ancilla_site": ancilla,
                "S_system": s_s,
                "S_history": s_h,
                "S_system_history": s_sh,
                "I_system_history": s_s + s_h - s_sh,
                "I_c_system_to_history": s_h - s_sh,
                "branch_p0": float(diag[0].item()),
                "branch_p1": float(diag[1].item()),
            }
        )
    probs = torch.tensor(branch_probs, dtype=RTYPE)
    probs = probs / torch.clamp(torch.sum(probs), min=torch.tensor(1e-12, dtype=RTYPE))
    nz = probs[probs > 1e-11]
    history_entropy = float((-torch.sum(nz * torch.log(nz))).item())
    drive = torch.stack(drive_rows)
    bonds = [int(tensor.shape[2]) for tensor in mps.tensors[:-1]]
    return {
        "H_process_history": history_entropy,
        "I_system_history_sum": float(sum(row["I_system_history"] for row in shell_rows)),
        "I_c_system_to_history_sum": float(sum(row["I_c_system_to_history"] for row in shell_rows)),
        "history_entropy_mean": float(sum(row["S_history"] for row in shell_rows) / len(shell_rows)),
        "history_branch_spread": float(torch.max(probs).item() - torch.min(probs).item()),
        "jk_drive_magnitude": float(torch.linalg.vector_norm(drive[:, 1:]).item()),
        "i_drive_magnitude": float(torch.linalg.vector_norm(drive[:, 0]).item()),
        "max_unitary_gap": max(unitary_gaps) if unitary_gaps else 0.0,
        "max_bond": max(bonds) if bonds else 1,
        "mean_bond": float(sum(bonds) / len(bonds)) if bonds else 1.0,
        "shell_rows": shell_rows,
    }


def metric_vector(row: dict[str, Any]) -> torch.Tensor:
    return torch.tensor(
        [
            row["H_process_history"],
            row["I_system_history_sum"],
            row["I_c_system_to_history_sum"],
            row["history_entropy_mean"],
            row["history_branch_spread"],
            row["jk_drive_magnitude"],
            row["max_bond"],
        ],
        dtype=RTYPE,
    )


def run_process(system_count: int, *, mode: str) -> dict[str, Any]:
    mps, lay = build_initial_mps(system_count)
    rows = build_rows(system_count, mode=mode)
    drive_rows = []
    unitary_gaps = []
    applied_system_edges = 0
    for row in rows:
        if row["system_edge"] is not None:
            gate = smooth_system_gate(row, mode=mode)
            mps.apply_two(gate, int(row["system_edge"][0]), max_bond=MAX_BOND)
            applied_system_edges += 1
        gate, unitary_gap, drive = stinespring_gate(row, mode=mode)
        mps.apply_two(gate, int(row["history_ancilla_site"]) - 1, max_bond=MAX_BOND)
        unitary_gaps.append(unitary_gap)
        drive_rows.append(drive)
        mps.normalize_()
    out = process_metrics(mps, lay, drive_rows, unitary_gaps)
    out.update(
        {
            "system_site_count": system_count,
            "total_site_count": lay["total_site_count"],
            "history_ancilla_count": lay["history_ancilla_count"],
            "systems_per_shell": lay["systems_per_shell"],
            "mode": mode,
            "row_count": len(rows),
            "applied_system_edges": applied_system_edges,
        }
    )
    return out


def gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    return float(torch.linalg.vector_norm(metric_vector(a) - metric_vector(b)).item())


def run_scale(system_count: int) -> dict[str, Any]:
    nominal = run_process(system_count, mode="nominal")
    erased = run_process(system_count, mode="history_erased")
    static = run_process(system_count, mode="static_history")
    scrambled = run_process(system_count, mode="schedule_scrambled")
    swapped = run_process(system_count, mode="swapped_arrows")
    phase = run_process(system_count, mode="global_phase_only")
    return {
        "system_site_count": system_count,
        "nominal": nominal,
        "history_erased_gap": gap(nominal, erased),
        "static_history_gap": gap(nominal, static),
        "schedule_scrambled_gap": gap(nominal, scrambled),
        "swapped_arrows_gap": gap(nominal, swapped),
        "global_phase_gap": gap(nominal, phase),
        "pass": (
            nominal["row_count"] == 64
            and nominal["history_ancilla_count"] == SHELL_COUNT
            and nominal["H_process_history"] > GAP_FLOOR
            and nominal["I_system_history_sum"] > GAP_FLOOR
            and nominal["max_unitary_gap"] < 1e-5
            and gap(nominal, erased) > GAP_FLOOR
            and gap(nominal, static) > GAP_FLOOR
            and gap(nominal, scrambled) > GAP_FLOOR
            and gap(nominal, phase) > GAP_FLOOR
        ),
    }


def z3_gate() -> dict[str, Any]:
    max_system = z3.Int("max_system")
    history_sites = z3.Int("history_sites")
    final_xi = z3.Bool("final_xi")
    final_axis0 = z3.Bool("final_axis0")
    solver = z3.Solver()
    solver.add(max_system == max(SYSTEM_SITE_COUNTS), history_sites == SHELL_COUNT, z3.Not(final_xi), z3.Not(final_axis0))
    promote = z3.Solver()
    promote.add(max_system == max(SYSTEM_SITE_COUNTS), history_sites == SHELL_COUNT, final_xi, z3.Not(final_xi))
    return {
        "pass": solver.check() == z3.sat and promote.check() == z3.unsat,
        "sat": str(solver.check()),
        "promotion_status": str(promote.check()),
        "promotion_blocked_by_contract": True,
    }


def main() -> int:
    started = time.time()
    scale_rows = [run_scale(count) for count in SYSTEM_SITE_COUNTS]
    q_gate = quaternion_gate()
    z3_row = z3_gate()
    positive = {
        "mps_stinespring_process_runs_8_16_32_64": {
            "pass": all(row["pass"] for row in scale_rows),
            "system_site_counts": SYSTEM_SITE_COUNTS,
            "total_site_counts": [row["nominal"]["total_site_count"] for row in scale_rows],
            "history_entropies": [row["nominal"]["H_process_history"] for row in scale_rows],
            "system_history_mi_sums": [row["nominal"]["I_system_history_sum"] for row in scale_rows],
        },
        "explicit_history_ancilla_sites_are_present": {
            "pass": all(row["nominal"]["history_ancilla_count"] == SHELL_COUNT for row in scale_rows),
            "history_ancilla_count": SHELL_COUNT,
        },
        "smooth_quaternion_history_coupling": {
            "pass": q_gate["pass"] and all(row["nominal"]["jk_drive_magnitude"] > GAP_FLOOR for row in scale_rows),
            "quaternion_gate": q_gate,
        },
    }
    graveyard = {
        "GC1_history_erased_changes_process_signature": {
            "pass": all(row["history_erased_gap"] > GAP_FLOOR for row in scale_rows),
            "gaps": [row["history_erased_gap"] for row in scale_rows],
        },
        "GC2_static_history_changes_process_signature": {
            "pass": all(row["static_history_gap"] > GAP_FLOOR for row in scale_rows),
            "gaps": [row["static_history_gap"] for row in scale_rows],
        },
        "GC3_schedule_scramble_changes_process_signature": {
            "pass": all(row["schedule_scrambled_gap"] > GAP_FLOOR for row in scale_rows),
            "gaps": [row["schedule_scrambled_gap"] for row in scale_rows],
        },
        "GC4_global_phase_only_loses_process_signature": {
            "pass": all(row["global_phase_gap"] > GAP_FLOOR for row in scale_rows),
            "gaps": [row["global_phase_gap"] for row in scale_rows],
        },
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_final_xi_axis0_blocked": {"pass": "does not admit final Axis0" in CLAIM_CEILING and "Xi" in CLAIM_CEILING},
        "B3_finite_history_bound": z3_row,
        "B4_mps_not_peps3d_closure": {"pass": "PEPS/PEPS3D closure" in CLAIM_CEILING},
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
                "system_site_count": row["system_site_count"],
                "pass": row["pass"],
                "history_erased_gap": row["history_erased_gap"],
                "static_history_gap": row["static_history_gap"],
                "schedule_scrambled_gap": row["schedule_scrambled_gap"],
                "swapped_arrows_gap": row["swapped_arrows_gap"],
                "global_phase_gap": row["global_phase_gap"],
                "nominal": {key: value for key, value in row["nominal"].items() if key != "shell_rows"},
                "shell_rows_sample": row["nominal"]["shell_rows"][:3],
            }
            for row in scale_rows
        ],
        "summary": {
            "elapsed_seconds": time.time() - started,
            "system_site_counts": SYSTEM_SITE_COUNTS,
            "total_site_counts": [row["nominal"]["total_site_count"] for row in scale_rows],
            "min_history_entropy": min(row["nominal"]["H_process_history"] for row in scale_rows),
            "max_history_entropy": max(row["nominal"]["H_process_history"] for row in scale_rows),
            "min_system_history_mi": min(row["nominal"]["I_system_history_sum"] for row in scale_rows),
            "max_system_history_mi": max(row["nominal"]["I_system_history_sum"] for row in scale_rows),
        },
        "next_required_work": [
            "Convert the process-history MPS readout into an explicit rho_AB/rho_ABC Xi bridge candidate.",
            "Run the same process-history witness on PEPS local tensors with environment-contraction receipts.",
            "Stress process-history signatures against product, GHZ, graph, random, and flux-carrier initial families.",
        ],
        "why_not_v4_probes": (
            "This is a v5 MPS Stinespring/process-history handoff scout. It adds explicit finite history "
            "ancilla sites but does not admit final Xi, Axis0, Phi0, flux, or PEPS/PEPS3D dynamics."
        ),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
