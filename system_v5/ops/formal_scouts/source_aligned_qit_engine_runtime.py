#!/usr/bin/env python3
"""Source-aligned single-qubit QIT engine runtime.

This module is the small torch-native replacement path for the older
PERCEPTION_L_MATRICES replay boundary. It keeps four layers separate:

- topology/terrain identity: Se, Ne, Ni, Si;
- engine chart: Type 1 / Type 2 outer-inner token order;
- operator maps: Ti, Te, Fi, Fe;
- terrain laws: Funnel/Cannon, Vortex/Spiral, Pit/Source, Hill/Citadel.

It is intentionally one-qubit and finite. It does not claim tensor-network
runtime, PEPS/MPDO dynamics, or Axis-0 Xi bridge closure.
"""

from __future__ import annotations

import math
from typing import Any

import torch


DTYPE = torch.complex128
RTYPE = torch.float64

I2 = torch.eye(2, dtype=DTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
SIGMA_MINUS = torch.tensor([[0, 0], [1, 0]], dtype=DTYPE)
SIGMA_PLUS = torch.tensor([[0, 1], [0, 0]], dtype=DTYPE)

H0 = 0.5 * SX + 0.3 * SY + 0.7 * SZ
DEFAULT_DT = 0.12

TOPOLOGY_AXIS: dict[str, dict[str, Any]] = {
    "Se": {"A0": "A0-", "A0_bit": -1, "A1": "open_isothermal", "A2": "expansion_direct"},
    "Ne": {"A0": "A0+", "A0_bit": +1, "A1": "closed_adiabatic", "A2": "expansion_direct"},
    "Ni": {"A0": "A0+", "A0_bit": +1, "A1": "open_isothermal", "A2": "compression_conjugated"},
    "Si": {"A0": "A0-", "A0_bit": -1, "A1": "closed_adiabatic", "A2": "compression_conjugated"},
}

ENGINE_CHARTS: dict[str, list[dict[str, str]]] = {
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


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = torch.as_tensor(rho, dtype=DTYPE)
    rho = (rho + rho.conj().T) / 2
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=1e-14)
    out = vecs @ torch.diag(vals.to(DTYPE)) @ vecs.conj().T
    return out / torch.real(torch.trace(out))


def rho_from_bloch(x: float, y: float, z: float) -> torch.Tensor:
    return normalize_density(0.5 * (I2 + x * SX + y * SY + z * SZ))


def rho_from_bloch_vec(r: torch.Tensor) -> torch.Tensor:
    return rho_from_bloch(float(r[0]), float(r[1]), float(r[2]))


def bloch(rho: torch.Tensor) -> torch.Tensor:
    rho = torch.as_tensor(rho, dtype=DTYPE)
    return torch.stack([
        torch.real(torch.trace(SX @ rho)),
        torch.real(torch.trace(SY @ rho)),
        torch.real(torch.trace(SZ @ rho)),
    ]).to(RTYPE)


def entropy(rho: torch.Tensor) -> float:
    vals = torch.clamp(torch.linalg.eigvalsh(normalize_density(rho)).real, min=1e-14)
    vals = vals / vals.sum()
    return float(-(vals * torch.log(vals)).sum().item())


def purity(rho: torch.Tensor) -> float:
    rho = normalize_density(rho)
    return float(torch.real(torch.trace(rho @ rho)).item())


def eigvals(rho: torch.Tensor) -> list[float]:
    return [float(v) for v in torch.linalg.eigvalsh(normalize_density(rho)).real.tolist()]


def valid_density(rho: torch.Tensor) -> bool:
    rho = torch.as_tensor(rho, dtype=DTYPE)
    vals = eigvals(rho)
    return (
        torch.linalg.matrix_norm(rho - rho.conj().T).item() < 1e-9
        and abs(float(torch.real(torch.trace(rho)).item()) - 1.0) < 1e-9
        and min(vals) > -1e-10
    )


def unitary(H: torch.Tensor, angle: float) -> torch.Tensor:
    return torch.linalg.matrix_exp(-1j * float(angle) * H)


def apply_dephase(rho: torch.Tensor, axis: str, q: float) -> torch.Tensor:
    if axis == "z":
        projectors = [(I2 + SZ) / 2, (I2 - SZ) / 2]
    elif axis == "x":
        projectors = [(I2 + SX) / 2, (I2 - SX) / 2]
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
        U = unitary(SX / 2, sign * 0.35 * dt)
        return normalize_density(U @ rho @ U.conj().T)
    if operator == "Fe":
        U = unitary(SZ / 2, sign * 0.31 * dt)
        return normalize_density(U @ rho @ U.conj().T)
    raise ValueError(operator)


def apply_terrain(rho: torch.Tensor, topology: str, engine: str, dt: float = DEFAULT_DT) -> tuple[torch.Tensor, str]:
    h_sign = +1 if engine == "T1" else -1
    H = h_sign * H0

    if topology == "Se":
        U = unitary(H, 0.18 * dt)
        rho = normalize_density(U @ rho @ U.conj().T)
        strength = 1 - math.exp(-4 * 0.28 * dt)
        return apply_depolarize(rho, strength=strength), "Funnel" if engine == "T1" else "Cannon"

    if topology == "Ne":
        U = unitary(H, 0.8 * dt)
        rho = normalize_density(U @ rho @ U.conj().T)
        strength = 1 - math.exp(-4 * 0.025 * dt)
        return apply_depolarize(rho, strength=strength), "Vortex" if engine == "T1" else "Spiral"

    if topology == "Ni":
        U = unitary(H, 0.12 * dt)
        rho = normalize_density(U @ rho @ U.conj().T)
        p = 1 - math.exp(-0.55 * dt)
        if engine == "T1":
            return apply_amplitude_to_z_minus(rho, p), "Pit"
        return apply_amplitude_to_z_plus(rho, p), "Source"

    if topology == "Si":
        Hs = h_sign * SZ / 2
        U = unitary(Hs, 0.35 * dt)
        rho = normalize_density(U @ rho @ U.conj().T)
        return apply_dephase(rho, "z", q=0.16), "Hill" if engine == "T1" else "Citadel"

    raise ValueError(topology)


def parse_operator(token: str, topology: str) -> tuple[str, str, int]:
    if token.startswith(topology):
        return token[len(topology):], "terrain_first", -1
    if token.endswith(topology):
        return token[: -len(topology)], "operator_first", +1
    raise ValueError(f"token {token!r} does not contain topology {topology!r}")


def a3_chart_role_bit(loop: str) -> int:
    return +1 if loop == "outer" else -1


def a3_path_bit(path: str) -> int:
    return +1 if path == "base" else -1


def run_stage(rho: torch.Tensor, engine: str, stage: dict[str, str], idx: int) -> tuple[torch.Tensor, dict[str, Any]]:
    topology = stage["topology"]
    token = stage["token"]
    operator, precedence, a6_bit = parse_operator(token, topology)
    source_axis = TOPOLOGY_AXIS[topology]
    expected_a6 = -source_axis["A0_bit"] * a3_chart_role_bit(stage["loop"])
    path_expected_a6 = -source_axis["A0_bit"] * a3_path_bit(stage["path"])

    before = normalize_density(rho)
    if precedence == "operator_first":
        rho = apply_operator(before, operator, a6_bit)
        rho, terrain_realization = apply_terrain(rho, topology, engine)
    else:
        rho, terrain_realization = apply_terrain(before, topology, engine)
        rho = apply_operator(rho, operator, a6_bit)

    record = {
        "idx": idx,
        "engine": engine,
        "token": token,
        "topology": topology,
        "terrain_realization": terrain_realization,
        "operator": operator,
        "loop": stage["loop"],
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
        "final_density": rho,
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
        "final_density": rho,
        "final_bloch": [float(v) for v in bloch(rho).tolist()],
        "final_entropy": entropy(rho),
        "final_valid_density": valid_density(rho),
    }


def jsonable_density(rho: torch.Tensor) -> dict[str, Any]:
    rho = normalize_density(rho)
    return {
        "density_real": [[float(x.real) for x in row] for row in rho.tolist()],
        "density_imag": [[float(x.imag) for x in row] for row in rho.tolist()],
        "bloch": [float(v) for v in bloch(rho).tolist()],
        "entropy": entropy(rho),
        "purity": purity(rho),
        "eigenvalues": eigvals(rho),
        "valid_density": valid_density(rho),
    }


def json_slim_engine_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "engine": result["engine"],
        "cycles": result["cycles"],
        "final_state": jsonable_density(result["final_density"]),
        "last_cycle_drift_fro": result["last_cycle_drift_fro"],
        "all_stage_valid": result["all_stage_valid"],
        "all_a6_xor_ok": result["all_a6_xor_ok"],
        "all_raw_path_xor_ok": result["all_raw_path_xor_ok"],
        "tokens_seen": result["tokens_seen"],
        "terrain_realizations_seen": result["terrain_realizations_seen"],
        "trajectory_head": result["trajectory_head"],
        "trajectory_tail": result["trajectory_tail"],
    }
