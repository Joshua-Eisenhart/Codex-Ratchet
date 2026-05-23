#!/usr/bin/env python3
"""Source-aligned QIT engine smoke using the corrected A0/A1/A2 terrain square.

This is deliberately small:

- one qubit density carrier;
- source-correct A0/A1/A2 terrain square;
- source token charts for Type 1 and Type 2;
- source terrain law families as finite CPTP approximations;
- source operator maps Ti/Te/Fi/Fe;
- stage receipts with A0..A6, including the A6 XOR check.

It is not a tensor-network engine and does not close the Axis 0 Xi bridge. It
answers the narrow question: with the corrected axes, do the single-qubit QIT
engines run as valid density-matrix maps, and do the previously confused axis
projections stop contradicting the source?
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import torch


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "system_v5/ops/axis_audits/axis_corrected_qit_engine_smoke_20260522.json"

DTYPE = torch.complex128
RTYPE = torch.float64

I2 = torch.eye(2, dtype=DTYPE)
X = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
Y = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
Z = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
SIGMA_MINUS = torch.tensor([[0, 0], [1, 0]], dtype=DTYPE)  # fixed point z=-1
SIGMA_PLUS = torch.tensor([[0, 1], [0, 0]], dtype=DTYPE)   # fixed point z=+1

H0 = 0.5 * X + 0.3 * Y + 0.7 * Z
DEFAULT_DT = 0.12

TOPOLOGY_AXIS = {
    "Se": {"A0": "A0-", "A0_bit": -1, "A1": "open_isothermal", "A2": "expansion_direct"},
    "Ne": {"A0": "A0+", "A0_bit": +1, "A1": "closed_adiabatic", "A2": "expansion_direct"},
    "Ni": {"A0": "A0+", "A0_bit": +1, "A1": "open_isothermal", "A2": "compression_conjugated"},
    "Si": {"A0": "A0-", "A0_bit": -1, "A1": "closed_adiabatic", "A2": "compression_conjugated"},
}

ENGINE_CHARTS = {
    "T1": [
        {"topology": "Se", "loop": "outer", "path": "base", "A4": "deductive", "token": "TiSe"},
        {"topology": "Ne", "loop": "outer", "path": "base", "A4": "deductive", "token": "NeTi"},
        {"topology": "Ni", "loop": "outer", "path": "base", "A4": "deductive", "token": "NiFe"},
        {"topology": "Si", "loop": "outer", "path": "base", "A4": "deductive", "token": "FeSi"},
        {"topology": "Se", "loop": "inner", "path": "fiber", "A4": "inductive", "token": "SeFi"},
        {"topology": "Ne", "loop": "inner", "path": "fiber", "A4": "inductive", "token": "FiNe"},
        {"topology": "Ni", "loop": "inner", "path": "fiber", "A4": "inductive", "token": "TeNi"},
        {"topology": "Si", "loop": "inner", "path": "fiber", "A4": "inductive", "token": "SiTe"},
    ],
    "T2": [
        {"topology": "Se", "loop": "outer", "path": "fiber", "A4": "inductive", "token": "FiSe"},
        {"topology": "Si", "loop": "outer", "path": "fiber", "A4": "inductive", "token": "TeSi"},
        {"topology": "Ni", "loop": "outer", "path": "fiber", "A4": "inductive", "token": "NiTe"},
        {"topology": "Ne", "loop": "outer", "path": "fiber", "A4": "inductive", "token": "NeFi"},
        {"topology": "Se", "loop": "inner", "path": "base", "A4": "deductive", "token": "SeTi"},
        {"topology": "Si", "loop": "inner", "path": "base", "A4": "deductive", "token": "SiFe"},
        {"topology": "Ni", "loop": "inner", "path": "base", "A4": "deductive", "token": "FeNi"},
        {"topology": "Ne", "loop": "inner", "path": "base", "A4": "deductive", "token": "TiNe"},
    ],
}

OPERATOR_FAMILY = {"Ti": "dephasing", "Te": "dephasing", "Fi": "rotation", "Fe": "rotation"}
TOKEN_OPERATOR = {"Ti": "Ti", "Te": "Te", "Fi": "Fi", "Fe": "Fe"}


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + rho.conj().T) / 2
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=1e-14)
    out = vecs @ torch.diag(vals.to(DTYPE)) @ vecs.conj().T
    return out / torch.real(torch.trace(out))


def rho_from_bloch(x: float, y: float, z: float) -> torch.Tensor:
    return normalize_density(0.5 * (I2 + x * X + y * Y + z * Z))


def bloch(rho: torch.Tensor) -> torch.Tensor:
    return torch.stack([
        torch.real(torch.trace(X @ rho)),
        torch.real(torch.trace(Y @ rho)),
        torch.real(torch.trace(Z @ rho)),
    ]).to(RTYPE)


def rho_from_bloch_vec(r: torch.Tensor) -> torch.Tensor:
    return normalize_density(0.5 * (I2 + float(r[0]) * X + float(r[1]) * Y + float(r[2]) * Z))


def entropy(rho: torch.Tensor) -> float:
    vals = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real, min=1e-14)
    vals = vals / vals.sum()
    return float(-(vals * torch.log(vals)).sum().item())


def purity(rho: torch.Tensor) -> float:
    return float(torch.real(torch.trace(rho @ rho)).item())


def eigvals(rho: torch.Tensor) -> list[float]:
    return [float(v) for v in torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real.tolist()]


def valid_density(rho: torch.Tensor) -> bool:
    vals = eigvals(rho)
    return (
        torch.linalg.matrix_norm(rho - rho.conj().T).item() < 1e-9
        and abs(float(torch.real(torch.trace(rho)).item()) - 1.0) < 1e-9
        and min(vals) > -1e-10
    )


def unitary(H: torch.Tensor, angle: float) -> torch.Tensor:
    return torch.linalg.matrix_exp(-1j * angle * H)


def apply_dephase(rho: torch.Tensor, axis: str, q: float) -> torch.Tensor:
    if axis == "z":
        projectors = [(I2 + Z) / 2, (I2 - Z) / 2]
    elif axis == "x":
        projectors = [(I2 + X) / 2, (I2 - X) / 2]
    else:
        raise ValueError(axis)
    pinched = sum(P @ rho @ P for P in projectors)
    return normalize_density((1 - q) * rho + q * pinched)


def apply_depolarize(rho: torch.Tensor, strength: float) -> torch.Tensor:
    r = bloch(rho) * float(1 - strength)
    return rho_from_bloch_vec(r)


def apply_amplitude_to_z_minus(rho: torch.Tensor, p: float) -> torch.Tensor:
    K0 = torch.tensor([[math.sqrt(1 - p), 0], [0, 1]], dtype=DTYPE)
    K1 = torch.tensor([[0, 0], [math.sqrt(p), 0]], dtype=DTYPE)
    return normalize_density(K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T)


def apply_amplitude_to_z_plus(rho: torch.Tensor, p: float) -> torch.Tensor:
    K0 = torch.tensor([[1, 0], [0, math.sqrt(1 - p)]], dtype=DTYPE)
    K1 = torch.tensor([[0, math.sqrt(p)], [0, 0]], dtype=DTYPE)
    return normalize_density(K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T)


def apply_operator(rho: torch.Tensor, operator: str, sign: int, dt: float = DEFAULT_DT) -> torch.Tensor:
    if operator == "Ti":
        return apply_dephase(rho, "z", q=0.22)
    if operator == "Te":
        return apply_dephase(rho, "x", q=0.22)
    if operator == "Fi":
        U = unitary(X / 2, sign * 0.35 * dt)
        return normalize_density(U @ rho @ U.conj().T)
    if operator == "Fe":
        U = unitary(Z / 2, sign * 0.31 * dt)
        return normalize_density(U @ rho @ U.conj().T)
    raise ValueError(operator)


def apply_terrain(rho: torch.Tensor, topology: str, engine: str, dt: float = DEFAULT_DT) -> tuple[torch.Tensor, str]:
    h_sign = +1 if engine == "T1" else -1
    H = h_sign * H0

    if topology == "Se":
        # Source terrain law: isotropic dissipator plus sheet Hamiltonian.
        U = unitary(H, 0.18 * dt)
        rho = U @ rho @ U.conj().T
        return apply_depolarize(rho, strength=1 - math.exp(-4 * 0.28 * dt)), "Funnel" if engine == "T1" else "Cannon"

    if topology == "Ne":
        # Source terrain law: Hamiltonian circulation plus optional weak dissipator.
        U = unitary(H, 0.8 * dt)
        rho = normalize_density(U @ rho @ U.conj().T)
        return apply_depolarize(rho, strength=1 - math.exp(-4 * 0.025 * dt)), "Vortex" if engine == "T1" else "Spiral"

    if topology == "Ni":
        # Source terrain law: Pit sigma_- on Type 1, Source sigma_+ on Type 2.
        U = unitary(H, 0.12 * dt)
        rho = normalize_density(U @ rho @ U.conj().T)
        p = 1 - math.exp(-0.55 * dt)
        if engine == "T1":
            return apply_amplitude_to_z_minus(rho, p), "Pit"
        return apply_amplitude_to_z_plus(rho, p), "Source"

    if topology == "Si":
        # Source terrain law: commuting Hamiltonian plus invariant-strata dephasing.
        Hs = h_sign * Z / 2
        U = unitary(Hs, 0.35 * dt)
        rho = normalize_density(U @ rho @ U.conj().T)
        return apply_dephase(rho, "z", q=0.16), "Hill" if engine == "T1" else "Citadel"

    raise ValueError(topology)


def parse_operator(token: str, topology: str) -> tuple[str, str, int]:
    if token.startswith(topology):
        operator = token[len(topology):]
        return operator, "terrain_first", -1
    if token.endswith(topology):
        operator = token[: -len(topology)]
        return operator, "operator_first", +1
    raise ValueError(f"token {token} does not contain topology {topology}")


def a3_chart_role_bit(loop: str) -> int:
    """Source XOR bit: outer/inner chart role, not raw fiber/base path.

    The atlas has two A3 surfaces that must stay visible:
    - geometry path: fiber versus lifted base;
    - chart role: inner versus outer token set.

    The b6 = -b0*b3 table is written against inner/outer. If raw path is used
    instead, Type 2 rows all invert because Type 2 swaps fiber/base roles.
    """
    return +1 if loop == "outer" else -1


def a3_path_bit(path: str) -> int:
    """Diagnostic only: this is the geometric path bit, not the XOR bit."""
    return +1 if path == "base" else -1


def run_stage(rho: torch.Tensor, engine: str, stage: dict[str, str], idx: int) -> tuple[torch.Tensor, dict[str, Any]]:
    topology = stage["topology"]
    token = stage["token"]
    operator, precedence, a6_bit = parse_operator(token, topology)
    source_axis = TOPOLOGY_AXIS[topology]
    expected_a6 = -source_axis["A0_bit"] * a3_chart_role_bit(stage["loop"])
    path_expected_a6 = -source_axis["A0_bit"] * a3_path_bit(stage["path"])

    before = rho
    if precedence == "operator_first":
        rho = apply_operator(rho, operator, a6_bit)
        rho, terrain_realization = apply_terrain(rho, topology, engine)
    else:
        rho, terrain_realization = apply_terrain(rho, topology, engine)
        rho = apply_operator(rho, operator, a6_bit)

    record = {
        "idx": idx,
        "engine": engine,
        "token": token,
        "topology": topology,
        "terrain_realization": terrain_realization,
        "operator": operator,
        "axis_values": {
            "A0": source_axis["A0"],
            "A1": source_axis["A1"],
            "A2": source_axis["A2"],
            "A3_geometry_path": stage["path"],
            "A3_chart_role": stage["loop"],
            "A4": stage["A4"],
            "A5": OPERATOR_FAMILY[operator],
            "A6_token_precedence": precedence,
            "A6_bit": a6_bit,
            "A6_xor_uses": "A3_chart_role_inner_outer",
            "A6_xor_expected": expected_a6,
            "A6_xor_ok": a6_bit == expected_a6,
            "A6_path_expected_if_raw_geometry_used": path_expected_a6,
            "A6_path_xor_ok": a6_bit == path_expected_a6,
        },
        "loop": stage["loop"],
        "trace": float(torch.real(torch.trace(rho)).item()),
        "valid_density": valid_density(rho),
        "bloch_before": [float(v) for v in bloch(before).tolist()],
        "bloch_after": [float(v) for v in bloch(rho).tolist()],
        "entropy_after": entropy(rho),
        "purity_after": purity(rho),
        "eigenvalues_after": eigvals(rho),
    }
    return rho, record


def run_engine(engine: str, rho_init: torch.Tensor, cycles: int = 20) -> dict[str, Any]:
    rho = normalize_density(rho_init)
    trajectory: list[dict[str, Any]] = []
    cycle_end_states: list[torch.Tensor] = []
    for cycle in range(cycles):
        for idx, stage in enumerate(ENGINE_CHARTS[engine]):
            rho, record = run_stage(rho, engine, stage, idx)
            record["cycle"] = cycle
            trajectory.append(record)
        cycle_end_states.append(rho)
    drift_last = float(torch.linalg.matrix_norm(cycle_end_states[-1] - cycle_end_states[-2]).item()) if cycles > 1 else 0.0
    return {
        "engine": engine,
        "cycles": cycles,
        "final_density_real": [[float(x.real) for x in row] for row in rho.tolist()],
        "final_density_imag": [[float(x.imag) for x in row] for row in rho.tolist()],
        "final_bloch": [float(v) for v in bloch(rho).tolist()],
        "final_entropy": entropy(rho),
        "final_purity": purity(rho),
        "final_eigenvalues": eigvals(rho),
        "final_valid_density": valid_density(rho),
        "last_cycle_drift_fro": drift_last,
        "all_stage_valid": all(r["valid_density"] for r in trajectory),
        "all_a6_xor_ok": all(r["axis_values"]["A6_xor_ok"] for r in trajectory),
        "all_raw_path_xor_ok": all(r["axis_values"]["A6_path_xor_ok"] for r in trajectory),
        "tokens_seen": sorted({r["token"] for r in trajectory}),
        "terrain_realizations_seen": sorted({r["terrain_realization"] for r in trajectory}),
        "trajectory_head": trajectory[:8],
        "trajectory_tail": trajectory[-8:],
    }


def run_schedule(order: list[str], rho_init: torch.Tensor, repeats: int = 8) -> dict[str, Any]:
    rho = normalize_density(rho_init)
    for _ in range(repeats):
        for engine in order:
            for idx, stage in enumerate(ENGINE_CHARTS[engine]):
                rho, _ = run_stage(rho, engine, stage, idx)
    return {
        "order": order,
        "repeats": repeats,
        "final_bloch": [float(v) for v in bloch(rho).tolist()],
        "final_entropy": entropy(rho),
        "final_valid_density": valid_density(rho),
        "final_density": rho,
    }


def current_canonical_spec_mismatches() -> list[dict[str, Any]]:
    """Known old-spec mismatch summary, not a source parser."""
    return [
        {
            "surface": "system_v5/ops/formal_scouts/canonical_qit_engine_specs.py",
            "field": "PERCEPTION_L_MATRICES",
            "issue": "Older per-perception L table maps Se->sigma_z, Ne->sigma_+, Ni->-i sigma_y, Si->sigma_-. Source terrain packet now requires sheet-specific terrain laws: Se isotropic Pauli dissipator, Ne Hamiltonian circulation, Ni Pit/Source ladder, Si projector strata.",
            "status": "engine_core_runs_but_not_source_repaired",
        }
    ]


def main() -> int:
    rho0 = rho_from_bloch(0.23, -0.17, 0.41)
    t1 = run_engine("T1", rho0)
    t2 = run_engine("T2", rho0)
    schedule_t1_t2 = run_schedule(["T1", "T2"], rho0)
    schedule_t2_t1 = run_schedule(["T2", "T1"], rho0)
    order_gap = float(torch.linalg.matrix_norm(schedule_t1_t2["final_density"] - schedule_t2_t1["final_density"]).item())
    t_gap = float(
        torch.linalg.matrix_norm(
            torch.tensor(t1["final_density_real"], dtype=DTYPE) + 1j * torch.tensor(t1["final_density_imag"], dtype=DTYPE)
            - (torch.tensor(t2["final_density_real"], dtype=DTYPE) + 1j * torch.tensor(t2["final_density_imag"], dtype=DTYPE))
        ).item()
    )

    checks = {
        "T1_runs_valid": t1["final_valid_density"] and t1["all_stage_valid"],
        "T2_runs_valid": t2["final_valid_density"] and t2["all_stage_valid"],
        "T1_axis_xor_ok": t1["all_a6_xor_ok"],
        "T2_axis_xor_ok": t2["all_a6_xor_ok"],
        "T1_T2_distinct": t_gap > 1e-3,
        "schedule_order_matters": order_gap > 1e-4,
        "T1_converges_under_repeated_cycles": t1["last_cycle_drift_fro"] < 1e-3,
        "T2_converges_under_repeated_cycles": t2["last_cycle_drift_fro"] < 1e-3,
    }

    payload = {
        "kind": "axis_corrected_qit_engine_smoke",
        "generated_at": "2026-05-22T00:00:00-07:00",
        "classification": "source_aligned_engine_smoke_pass" if all(checks.values()) else "source_aligned_engine_smoke_partial",
        "ok": all(checks.values()),
        "TOOL_MANIFEST": [
            {
                "tool": "pytorch",
                "reason": "load-bearing density-matrix channels, matrix exponentials, eigenvalue checks, and source-aligned engine iteration",
            }
        ],
        "TOOL_INTEGRATION_DEPTH": "load_bearing",
        "scope": {
            "answers": "corrected single-qubit axis/terrain/operator engine runs and finite math-projection consistency",
            "does_not_answer": [
                "full MPDO/MPS/PEPS engine",
                "Axis 0 Xi bridge closure",
                "canonical replacement of existing formal_scouts engine_core",
                "multi-basin proof beyond finite schedule order gap",
            ],
        },
        "checks": checks,
        "distances": {
            "T1_T2_final_fro": t_gap,
            "schedule_T1T2_vs_T2T1_fro": order_gap,
        },
        "engines": {"T1": t1, "T2": t2},
        "schedules": {
            "T1_then_T2": {k: v for k, v in schedule_t1_t2.items() if k != "final_density"},
            "T2_then_T1": {k: v for k, v in schedule_t2_t1.items() if k != "final_density"},
        },
        "current_formal_scout_spec_mismatches": current_canonical_spec_mismatches(),
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"ok": payload["ok"], "classification": payload["classification"], "receipt": str(OUT.relative_to(ROOT))}, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
