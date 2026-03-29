#!/usr/bin/env python3
"""
Axis 0 Full Constraint-Manifold Guardrail SIM
=============================================

Purpose
-------
Run the full object honestly:
  1. explicit left/right Weyl spinors
  2. on nested Hopf tori T_eta
  3. along exact fiber/base loops from the Hopf chart
  4. through complete 4-stage terrain cycles
  5. with a real L|R cut-state readout

Two modes are compared:
  A. local-only evolution:
     independent L/R terrain channels applied correctly on rho_LR
  B. coupled control:
     same local channels plus an explicit nonlocal entangling bridge

This is a guardrail sim. If local-only evolution generates mutual
information from a product state, the implementation is wrong.
"""

import json
import os
import sys
from datetime import UTC, datetime

import numpy as np
import scipy.linalg as la

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    density_to_bloch,
    left_density,
    left_weyl_spinor,
    right_density,
    right_weyl_spinor,
    torus_coordinates,
)
from proto_ratchet_sim_runner import EvidenceToken, ensure_valid


I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
sm = np.array([[0, 0], [1, 0]], dtype=complex)
sp = np.array([[0, 1], [0, 0]], dtype=complex)

DED_ORDER = ["Se", "Ne", "Ni", "Si"]
IND_ORDER = ["Se", "Si", "Ni", "Ne"]


def vn_entropy(rho: np.ndarray) -> float:
    vals = np.real(np.linalg.eigvalsh((rho + rho.conj().T) / 2))
    vals = vals[vals > 1e-15]
    return float(-np.sum(vals * np.log2(vals))) if len(vals) else 0.0


def partial_trace_A(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_B(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def mutual_info(rho_ab: np.ndarray) -> float:
    rho_a = partial_trace_B(rho_ab)
    rho_b = partial_trace_A(rho_ab)
    return vn_entropy(rho_a) + vn_entropy(rho_b) - vn_entropy(rho_ab)


def coherent_info(rho_ab: np.ndarray) -> float:
    rho_b = partial_trace_A(rho_ab)
    return vn_entropy(rho_b) - vn_entropy(rho_ab)


def orthogonal_spinor(psi: np.ndarray) -> np.ndarray:
    return np.array([-np.conj(psi[1]), np.conj(psi[0])], dtype=complex)


def q_from_chart(phi: float, chi: float, eta: float) -> np.ndarray:
    return torus_coordinates(eta, phi + chi, phi - chi)


def q_on_loop(phi0: float, chi0: float, eta: float, u: float, loop_type: str) -> np.ndarray:
    if loop_type == "fiber":
        return q_from_chart(phi0 + u, chi0, eta)
    if loop_type == "base":
        c2 = np.cos(2.0 * eta)
        return q_from_chart(phi0 - c2 * u, chi0 + u, eta)
    raise ValueError(f"unknown loop_type: {loop_type}")


def depolarizing_kraus(p: float) -> list[np.ndarray]:
    p = float(np.clip(p, 0.0, 1.0))
    return [
        np.sqrt(max(0.0, 1.0 - 3.0 * p / 4.0)) * I2,
        np.sqrt(p / 4.0) * sx,
        np.sqrt(p / 4.0) * sy,
        np.sqrt(p / 4.0) * sz,
    ]


def unitary_kraus(axis: np.ndarray, angle: float) -> list[np.ndarray]:
    n = np.array(axis, dtype=float)
    norm = np.linalg.norm(n)
    if norm < 1e-12:
        n = np.array([0.0, 0.0, 1.0])
    else:
        n = n / norm
    H = 0.5 * (n[0] * sx + n[1] * sy + n[2] * sz)
    U = la.expm(-1j * angle * H)
    return [U]


def amplitude_damping_kraus(gamma: float, raising: bool = False) -> list[np.ndarray]:
    gamma = float(np.clip(gamma, 0.0, 1.0))
    K0 = np.array([[1.0, 0.0], [0.0, np.sqrt(1.0 - gamma)]], dtype=complex)
    K1 = np.sqrt(gamma) * sm
    if not raising:
        return [K0, K1]
    return [sx @ K0 @ sx, sx @ K1 @ sx]


def dephasing_basis_kraus(psi: np.ndarray, p: float) -> list[np.ndarray]:
    p = float(np.clip(p, 0.0, 1.0))
    psi = psi / np.linalg.norm(psi)
    phi = orthogonal_spinor(psi)
    P0 = np.outer(psi, np.conj(psi))
    P1 = np.outer(phi, np.conj(phi))
    return [
        np.sqrt(max(0.0, 1.0 - p)) * I2,
        np.sqrt(p) * P0,
        np.sqrt(p) * P1,
    ]


def apply_local_channel(rho_ab: np.ndarray, kraus_L: list[np.ndarray], kraus_R: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((4, 4), dtype=complex)
    for KL in kraus_L:
        for KR in kraus_R:
            K = np.kron(KL, KR)
            out += K @ rho_ab @ K.conj().T
    return ensure_valid(out)


def coupling_unitary(eta: float, loop_type: str, terrain: str) -> np.ndarray:
    geom = 0.5 + 0.5 * abs(np.cos(2.0 * eta))
    loop_gain = 1.0 if loop_type == "base" else 0.7
    terrain_gain = {
        "Se": 0.9,
        "Ne": 0.4,
        "Ni": 1.0,
        "Si": 0.5,
    }[terrain]
    g = 0.06 * geom * loop_gain * terrain_gain
    H_int = np.kron(sx, sx) + 0.5 * np.kron(sz, sz)
    return la.expm(-1j * g * H_int)


def terrain_kraus_pair(terrain: str, q: np.ndarray) -> tuple[list[np.ndarray], list[np.ndarray]]:
    rho_geom_L = left_density(q)
    rho_geom_R = right_density(q)
    nL = density_to_bloch(rho_geom_L)
    nR = density_to_bloch(rho_geom_R)
    psiL = left_weyl_spinor(q)
    psiR = right_weyl_spinor(q)

    if terrain == "Se":
        return depolarizing_kraus(0.10), depolarizing_kraus(0.10)
    if terrain == "Ne":
        return unitary_kraus(nL, 0.18), unitary_kraus(-nR, 0.18)
    if terrain == "Ni":
        return amplitude_damping_kraus(0.12, raising=False), amplitude_damping_kraus(0.12, raising=True)
    if terrain == "Si":
        return dephasing_basis_kraus(psiL, 0.12), dephasing_basis_kraus(psiR, 0.12)
    raise ValueError(f"unknown terrain: {terrain}")


def loop_density_variation(eta: float, loop_type: str, n_points: int = 64) -> dict:
    phi0 = 0.0
    chi0 = 0.0
    bloch = []
    rho0 = None
    dists = []
    for k in range(n_points):
        u = 2.0 * np.pi * k / n_points
        q = q_on_loop(phi0, chi0, eta, u, loop_type)
        rho = left_density(q)
        if rho0 is None:
            rho0 = rho
        dists.append(0.5 * np.sum(np.abs(np.linalg.eigvalsh(rho - rho0))))
        bloch.append(density_to_bloch(rho))
    bloch = np.array(bloch)
    return {
        "loop_type": loop_type,
        "eta": float(eta),
        "max_trace_distance_from_start": float(np.max(dists)),
        "std_rx": float(np.std(bloch[:, 0])),
        "std_ry": float(np.std(bloch[:, 1])),
        "std_rz": float(np.std(bloch[:, 2])),
    }


def run_cycle(order: list[str], eta: float, loop_type: str, mode: str, n_substeps: int = 16) -> dict:
    phi0 = 0.0
    chi0 = 0.0
    q0 = q_on_loop(phi0, chi0, eta, 0.0, loop_type)
    rho_ab = np.kron(left_density(q0), right_density(q0))

    mi_trace = [mutual_info(rho_ab)]
    ci_trace = [coherent_info(rho_ab)]

    total_steps = len(order) * n_substeps
    for stage_idx, terrain in enumerate(order):
        for sub_idx in range(n_substeps):
            global_idx = stage_idx * n_substeps + sub_idx + 1
            u = 2.0 * np.pi * global_idx / total_steps
            q = q_on_loop(phi0, chi0, eta, u, loop_type)
            kraus_L, kraus_R = terrain_kraus_pair(terrain, q)
            rho_ab = apply_local_channel(rho_ab, kraus_L, kraus_R)
            if mode == "coupled_control":
                U = coupling_unitary(eta, loop_type, terrain)
                rho_ab = ensure_valid(U @ rho_ab @ U.conj().T)
            mi_trace.append(mutual_info(rho_ab))
            ci_trace.append(coherent_info(rho_ab))

    return {
        "eta": float(eta),
        "loop_type": loop_type,
        "order_name": "DED" if order == DED_ORDER else "IND",
        "mode": mode,
        "MI_initial": float(mi_trace[0]),
        "MI_final": float(mi_trace[-1]),
        "MI_max": float(max(mi_trace)),
        "CI_final": float(ci_trace[-1]),
        "CI_min": float(min(ci_trace)),
        "trace_length": len(mi_trace),
    }


def main():
    print("=" * 72)
    print("AXIS 0 FULL CONSTRAINT-MANIFOLD GUARDRAIL SIM")
    print("=" * 72)

    eta_values = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]
    records = []

    print("\nGeometry loop check:")
    geometry = []
    for eta in eta_values:
        for loop_type in ["fiber", "base"]:
            g = loop_density_variation(eta, loop_type)
            geometry.append(g)
            print(
                f"  eta/pi={eta/np.pi:.3f} {loop_type:5s} "
                f"max_d={g['max_trace_distance_from_start']:.6f} "
                f"std(r)=({g['std_rx']:.6f},{g['std_ry']:.6f},{g['std_rz']:.6f})"
            )

    print("\nCycle results:")
    print(f"{'mode':>15} {'eta/pi':>7} {'loop':>6} {'ord':>4} {'MI_fin':>10} {'MI_max':>10} {'CI_fin':>10}")
    print("-" * 72)
    for eta in eta_values:
        for loop_type in ["fiber", "base"]:
            for order in [DED_ORDER, IND_ORDER]:
                for mode in ["local_only", "coupled_control"]:
                    rec = run_cycle(order, eta, loop_type, mode)
                    records.append(rec)
                    print(
                        f"{mode:>15} {eta/np.pi:>7.3f} {loop_type:>6s} {rec['order_name']:>4s} "
                        f"{rec['MI_final']:>10.6f} {rec['MI_max']:>10.6f} {rec['CI_final']:>10.6f}"
                    )

    local_records = [r for r in records if r["mode"] == "local_only"]
    coupled_records = [r for r in records if r["mode"] == "coupled_control"]

    local_mi_max = max(r["MI_max"] for r in local_records)
    coupled_mi_max = max(r["MI_max"] for r in coupled_records)
    fiber_constant_ok = all(
        g["max_trace_distance_from_start"] < 1e-10
        for g in geometry
        if g["loop_type"] == "fiber"
    )
    base_varies_ok = all(
        (g["std_rx"] > 1e-3 or g["std_ry"] > 1e-3 or g["std_rz"] > 1e-3)
        for g in geometry
        if g["loop_type"] == "base"
    )

    print("\nGuardrail verdict:")
    print(f"  local-only max MI        : {local_mi_max:.6e}")
    print(f"  coupled-control max MI   : {coupled_mi_max:.6f}")
    print(f"  fiber density stationary : {fiber_constant_ok}")
    print(f"  base density varies      : {base_varies_ok}")

    tokens = []
    if local_mi_max < 1e-8:
        tokens.append(EvidenceToken(
            "E_SIM_AXIS0_LOCAL_NO_BRIDGE_OK",
            "S_SIM_AXIS0_FULL_CONSTRAINT_MANIFOLD_GUARDRAIL",
            "PASS",
            float(local_mi_max),
        ))
    else:
        tokens.append(EvidenceToken(
            "",
            "S_SIM_AXIS0_FULL_CONSTRAINT_MANIFOLD_GUARDRAIL",
            "KILL",
            float(local_mi_max),
            "LOCAL_ONLY_CREATED_CORRELATION",
        ))

    if coupled_mi_max > 0.02:
        tokens.append(EvidenceToken(
            "E_SIM_AXIS0_COUPLED_CONTROL_OK",
            "S_SIM_AXIS0_FULL_CONSTRAINT_MANIFOLD_GUARDRAIL",
            "PASS",
            float(coupled_mi_max),
        ))
    else:
        tokens.append(EvidenceToken(
            "",
            "S_SIM_AXIS0_FULL_CONSTRAINT_MANIFOLD_GUARDRAIL",
            "KILL",
            float(coupled_mi_max),
            "COUPLED_CONTROL_FAILED_TO_BUILD_CORRELATION",
        ))

    if fiber_constant_ok and base_varies_ok:
        tokens.append(EvidenceToken(
            "E_SIM_AXIS0_LOOP_GEOMETRY_OK",
            "S_SIM_AXIS0_FULL_CONSTRAINT_MANIFOLD_GUARDRAIL",
            "PASS",
            1.0,
        ))
    else:
        tokens.append(EvidenceToken(
            "",
            "S_SIM_AXIS0_FULL_CONSTRAINT_MANIFOLD_GUARDRAIL",
            "KILL",
            0.0,
            "LOOP_GEOMETRY_FAILED",
        ))

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "axis0_full_constraint_manifold_guardrail_results.json")
    with open(out_path, "w") as f:
        json.dump({
            "schema": "SIM_EVIDENCE_v1",
            "file": os.path.basename(__file__),
            "timestamp": datetime.now(UTC).isoformat(),
            "geometry": geometry,
            "records": records,
            "summary": {
                "local_mi_max": local_mi_max,
                "coupled_mi_max": coupled_mi_max,
                "fiber_constant_ok": fiber_constant_ok,
                "base_varies_ok": base_varies_ok,
            },
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2)

    print(f"\nResults written to {out_path}")
    for t in tokens:
        print(f"  [{t.status}] {t.sim_spec_id} :: {t.token_id or t.kill_reason}")

    if any(t.status == "KILL" for t in tokens):
        sys.exit(1)


if __name__ == "__main__":
    main()
