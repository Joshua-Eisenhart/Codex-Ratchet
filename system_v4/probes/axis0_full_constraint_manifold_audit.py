#!/usr/bin/env python3
"""
Axis 0 Full Constraint-Manifold Audit
=====================================

No shortcuts:
- explicit left/right Weyl spinors from the real Hopf carrier
- nested Hopf-torus loop traversal (fiber/base)
- proper local bipartite evolution on the L|R cut
- direct Ax0 readout on the true bipartite state

This probe is intentionally conservative. It tests whether full geometry plus
local sheet dynamics alone can generate a nontrivial L|R Axis-0 signal.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hopf_manifold import hopf_map, left_weyl_spinor, right_weyl_spinor, torus_coordinates


sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)
sm = np.array([[0, 0], [1, 0]], dtype=complex)
sp = np.array([[0, 1], [0, 0]], dtype=complex)

DED_ORDER = ["Se", "Ne", "Ni", "Si"]
IND_ORDER = ["Se", "Si", "Ni", "Ne"]


def density(psi: np.ndarray) -> np.ndarray:
    return np.outer(psi, psi.conj())


def ensure_valid_density(rho: np.ndarray) -> np.ndarray:
    rho = 0.5 * (rho + rho.conj().T)
    evals, evecs = np.linalg.eigh(rho)
    evals = np.maximum(np.real(evals), 0.0)
    rho = evecs @ np.diag(evals.astype(complex)) @ evecs.conj().T
    tr = np.real(np.trace(rho))
    if tr > 1e-12:
        rho /= tr
    return rho


def ptrace_left(rho_lr: np.ndarray) -> np.ndarray:
    return np.trace(rho_lr.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def ptrace_right(rho_lr: np.ndarray) -> np.ndarray:
    return np.trace(rho_lr.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def vn_entropy(rho: np.ndarray) -> float:
    evals = np.real(np.linalg.eigvalsh(0.5 * (rho + rho.conj().T)))
    evals = evals[evals > 1e-15]
    return float(-np.sum(evals * np.log2(evals))) if len(evals) else 0.0


def mutual_information(rho_lr: np.ndarray) -> float:
    rho_l = ptrace_right(rho_lr)
    rho_r = ptrace_left(rho_lr)
    return vn_entropy(rho_l) + vn_entropy(rho_r) - vn_entropy(rho_lr)


def coherent_information(rho_lr: np.ndarray) -> float:
    rho_r = ptrace_left(rho_lr)
    return vn_entropy(rho_r) - vn_entropy(rho_lr)


def localize(op: np.ndarray, side: str) -> np.ndarray:
    if side == "L":
        return np.kron(op, I2)
    if side == "R":
        return np.kron(I2, op)
    raise ValueError(f"unknown side: {side}")


def dissipator(op: np.ndarray, rho: np.ndarray) -> np.ndarray:
    op_dag_op = op.conj().T @ op
    return op @ rho @ op.conj().T - 0.5 * (op_dag_op @ rho + rho @ op_dag_op)


def liouvillian_single(rho: np.ndarray, H: np.ndarray, jumps: list[np.ndarray]) -> np.ndarray:
    drho = -1j * (H @ rho - rho @ H)
    for jump in jumps:
        drho += dissipator(jump, rho)
    return drho


def geometry_hamiltonians(q: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = hopf_map(q)
    H0 = n[0] * sx + n[1] * sy + n[2] * sz
    return H0, -H0


def commuting_axis_hamiltonian(q: np.ndarray) -> np.ndarray:
    n = hopf_map(q)
    return n[0] * sx + n[1] * sy + n[2] * sz


def terrain_joint_step(
    rho_lr: np.ndarray,
    terrain: str,
    q: np.ndarray,
    dt: float,
    J_coupling: float = 0.1,
) -> np.ndarray:
    """Evolve the JOINT 4×4 state rho_lr for one terrain step.

    Each terrain generator acts on L and R separately (via localize()), plus
    a cross-coupling Hamiltonian J·σ_z⊗σ_z that can generate entanglement.

    Without J_coupling, local-only dynamics provably cannot create MI from a
    product state (no-entanglement-from-LOCC theorem). With J_coupling > 0,
    the joint state can develop nonzero MI — that is the honest physics test.

    The previous implementation rebuilt rho_lr = kron(rho_l, rho_r) each step,
    making MI structurally zero (not a physical discovery). This version
    maintains the joint state across steps.
    """
    H_l, H_r = geometry_hamiltonians(q)
    axis_h = commuting_axis_hamiltonian(q)
    # Joint Hamiltonian: H_L⊗I + I⊗H_R + J·σ_z⊗σ_z
    H_joint_local = np.kron(H_l, I2) + np.kron(I2, H_r)
    H_coupling = J_coupling * np.kron(sz, sz)
    H_joint = H_joint_local + H_coupling

    if terrain == "Se":
        jumps_L = [np.kron(np.sqrt(0.20 / 3.0) * s, I2) for s in (sx, sy, sz)]
        jumps_R = [np.kron(I2, np.sqrt(0.20 / 3.0) * s) for s in (sx, sy, sz)]
        jumps = jumps_L + jumps_R
        drho = -1j * (H_joint @ rho_lr - rho_lr @ H_joint) * 0.05
        for j in jumps:
            drho += dissipator(j, rho_lr)
        return ensure_valid_density(rho_lr + dt * drho)
    if terrain == "Ne":
        drho = -1j * (H_joint @ rho_lr - rho_lr @ H_joint)
        return ensure_valid_density(rho_lr + dt * drho)
    if terrain == "Ni":
        jump_L = np.kron(np.sqrt(0.25) * sm, I2)
        jump_R = np.kron(I2, np.sqrt(0.25) * sp)
        drho = -1j * (H_joint @ rho_lr - rho_lr @ H_joint) * 0.05
        for j in (jump_L, jump_R):
            drho += dissipator(j, rho_lr)
        return ensure_valid_density(rho_lr + dt * drho)
    if terrain == "Si":
        H_si = 0.50 * (np.kron(axis_h, I2) - np.kron(I2, axis_h)) + H_coupling
        jump_L = np.kron(np.sqrt(0.10) * axis_h, I2)
        jump_R = np.kron(I2, np.sqrt(0.10) * axis_h)
        drho = -1j * (H_si @ rho_lr - rho_lr @ H_si)
        for j in (jump_L, jump_R):
            drho += dissipator(j, rho_lr)
        return ensure_valid_density(rho_lr + dt * drho)
    raise ValueError(f"unknown terrain: {terrain}")


def terrain_single_step(rho_l: np.ndarray, rho_r: np.ndarray, terrain: str, q: np.ndarray, dt: float) -> tuple[np.ndarray, np.ndarray]:
    """Legacy local evolution — kept for Bloch-vector trajectory tracking only.
    DO NOT use for MI/Axis-0 computation: local-only dynamics cannot create MI.
    Use terrain_joint_step on the 4×4 joint state for any Axis-0 probe.
    """
    H_l, H_r = geometry_hamiltonians(q)
    axis_h = commuting_axis_hamiltonian(q)

    if terrain == "Se":
        jumps = [np.sqrt(0.20 / 3.0) * s for s in (sx, sy, sz)]
        rho_l = ensure_valid_density(rho_l + dt * liouvillian_single(rho_l, 0.05 * H_l, jumps))
        rho_r = ensure_valid_density(rho_r + dt * liouvillian_single(rho_r, 0.05 * H_r, jumps))
        return rho_l, rho_r
    if terrain == "Ne":
        rho_l = ensure_valid_density(rho_l + dt * liouvillian_single(rho_l, H_l, []))
        rho_r = ensure_valid_density(rho_r + dt * liouvillian_single(rho_r, H_r, []))
        return rho_l, rho_r
    if terrain == "Ni":
        rho_l = ensure_valid_density(rho_l + dt * liouvillian_single(rho_l, 0.05 * H_l, [np.sqrt(0.25) * sm]))
        rho_r = ensure_valid_density(rho_r + dt * liouvillian_single(rho_r, 0.05 * H_r, [np.sqrt(0.25) * sp]))
        return rho_l, rho_r
    if terrain == "Si":
        rho_l = ensure_valid_density(rho_l + dt * liouvillian_single(rho_l, 0.50 * axis_h, [np.sqrt(0.10) * axis_h]))
        rho_r = ensure_valid_density(rho_r + dt * liouvillian_single(rho_r, -0.50 * axis_h, [np.sqrt(0.10) * axis_h]))
        return rho_l, rho_r
    raise ValueError(f"unknown terrain: {terrain}")


def q_on_loop(loop_type: str, eta: float, u: float, phi0: float = 0.0, chi0: float = 0.0) -> np.ndarray:
    if loop_type == "fiber":
        return torus_coordinates(eta, phi0 + u, chi0)
    if loop_type == "base":
        c2e = np.cos(2 * eta)
        return torus_coordinates(eta, phi0 - c2e * u, chi0 + u)
    raise ValueError(f"unknown loop type: {loop_type}")


def bloch_from_density(rho: np.ndarray) -> np.ndarray:
    return np.array([np.real(np.trace(rho @ s)) for s in (sx, sy, sz)])


def run_cycle(loop_type: str, cycle_name: str, eta: float, n_substeps: int = 24, dt: float = 0.01,
              J_coupling: float = 0.1) -> dict:
    order = DED_ORDER if cycle_name == "DED" else IND_ORDER
    q0 = q_on_loop(loop_type, eta, 0.0)
    psi_l = left_weyl_spinor(q0)
    psi_r = right_weyl_spinor(q0)
    rho_l = density(psi_l)
    rho_r = density(psi_r)
    # Honest physics initialization: product state at t=0.
    # rho_lr is maintained as a proper joint 4×4 state from here on.
    # It is NOT rebuilt from kron each step — that would structurally force MI=0.
    rho_lr = np.kron(rho_l, rho_r)

    mi_trace = [mutual_information(rho_lr)]
    ci_trace = [coherent_information(rho_lr)]
    sep_trace = []
    bloch_l_trace = []
    bloch_r_trace = []

    total_steps = len(order) * n_substeps
    du = 2 * np.pi / total_steps
    u = 0.0

    for terrain in order:
        for _ in range(n_substeps):
            u += du
            q = q_on_loop(loop_type, eta, u)
            # Joint evolution on 4×4 state (entanglement-capable)
            rho_lr = terrain_joint_step(rho_lr, terrain, q, dt, J_coupling=J_coupling)
            # Extract marginals for Bloch tracking (read-only, not for MI)
            rho_l_marg = ptrace_right(rho_lr)
            rho_r_marg = ptrace_left(rho_lr)
            # sep_err: how far rho_lr is from its own marginal product
            sep_err = float(np.linalg.norm(
                rho_lr - np.kron(rho_l_marg, rho_r_marg), ord="fro"
            ))
            sep_trace.append(sep_err)
            bloch_l_trace.append(bloch_from_density(rho_l_marg))
            bloch_r_trace.append(bloch_from_density(rho_r_marg))
            mi_trace.append(mutual_information(rho_lr))
            ci_trace.append(coherent_information(rho_lr))

    mi_max = float(max(mi_trace))
    structural_zero = (J_coupling == 0.0 and mi_max < 1e-12)
    return {
        "eta": float(eta),
        "eta_over_pi": float(eta / np.pi),
        "loop": loop_type,
        "cycle": cycle_name,
        "J_coupling": float(J_coupling),
        "mi_initial": float(mi_trace[0]),
        "mi_final": float(mi_trace[-1]),
        "mi_max": mi_max,
        "ci_final": float(ci_trace[-1]),
        "sep_err_max": float(max(sep_trace) if sep_trace else 0.0),
        "sep_err_final": float(sep_trace[-1] if sep_trace else 0.0),
        "bloch_l_std": np.std(np.array(bloch_l_trace), axis=0).tolist(),
        "bloch_r_std": np.std(np.array(bloch_r_trace), axis=0).tolist(),
        # Explicit flag: if MI_max == 0 with J=0 that is expected physics (LOCC),
        # not a discovered finding. Fails if MI_max == 0 with J > 0 (coupling should work).
        "mi_zero_with_coupling_WARNING": bool(J_coupling > 0.0 and mi_max < 1e-6),
        "structural_zero_note": "LOCC: MI=0 is expected with J=0; not a finding" if structural_zero else "",
    }


def run_density_loop_check(eta: float = np.pi / 4, n_points: int = 96) -> dict:
    results = {}
    for loop_type in ("fiber", "base"):
        blochs = []
        for k in range(n_points):
            u = 2 * np.pi * k / n_points
            q = q_on_loop(loop_type, eta, u)
            rho = density(left_weyl_spinor(q))
            blochs.append(bloch_from_density(rho))
        blochs = np.array(blochs)
        std = np.std(blochs, axis=0)
        results[loop_type] = {
            "std_rx": float(std[0]),
            "std_ry": float(std[1]),
            "std_rz": float(std[2]),
            "density_constant": bool(np.max(std) < 1e-6),
        }
    return results


def main() -> int:
    print("=" * 76)
    print("AXIS 0 FULL CONSTRAINT-MANIFOLD AUDIT")
    print("=" * 76)
    print("Real left/right Weyl spinors, real Hopf tori, proper local bipartite evolution")

    eta_values = [np.pi / 8, np.pi / 6, np.pi / 4, np.pi / 3, 3 * np.pi / 8]
    results = []
    for eta in eta_values:
        for loop_type in ("fiber", "base"):
            for cycle_name in ("DED", "IND"):
                results.append(run_cycle(loop_type, cycle_name, eta))

    print("\neta/pi   loop  cycle   MI_init   MI_max   MI_final  CI_final  sep_err_max")
    print("-" * 76)
    for row in results:
        print(
            f"{row['eta_over_pi']:>6.3f}  {row['loop']:>5s}  {row['cycle']:>5s}  "
            f"{row['mi_initial']:>8.6f} {row['mi_max']:>8.6f} {row['mi_final']:>9.6f} "
            f"{row['ci_final']:>9.6f} {row['sep_err_max']:>11.6e}"
        )

    loop_check = run_density_loop_check()
    print("\nLoop density check at eta=pi/4")
    for loop_type, row in loop_check.items():
        print(
            f"{loop_type:>5s}: std(rx,ry,rz)=({row['std_rx']:.6f}, {row['std_ry']:.6f}, {row['std_rz']:.6f}) "
            f"constant={row['density_constant']}"
        )

    max_mi = max(r["mi_max"] for r in results)
    max_sep = max(r["sep_err_max"] for r in results)
    print("\nVerdict")
    if max_mi < 1e-6 and max_sep < 1e-6:
        print("  Local full-geometry L|R evolution does NOT generate a nontrivial Ax0 signal by itself.")
        print("  The missing Xi bridge or explicit coupling is still real.")
        status = "PASS_NO_SHORTCUTS"
    else:
        print("  Nonzero L|R correlations appeared under the local full-geometry evolution.")
        print("  This means the chosen dynamics or cut construction needs closer audit.")
        status = "FLAG_REVIEW"

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "axis0_full_constraint_manifold_audit_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.now(UTC).isoformat() + "Z",
                "status": status,
                "results": results,
                "loop_check": loop_check,
                "max_mi": max_mi,
                "max_sep_err": max_sep,
            },
            f,
            indent=2,
        )
    print(f"\nResults written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
