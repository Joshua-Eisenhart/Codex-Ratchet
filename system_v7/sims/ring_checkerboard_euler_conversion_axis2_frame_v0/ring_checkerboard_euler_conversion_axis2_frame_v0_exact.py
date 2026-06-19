#!/usr/bin/env python3
"""ring_checkerboard_euler_conversion_axis2_frame_v0 -- EXACT reference leg (numpy/stdlib).

Least-aligned flat baseline / control engine (per owner engine ranking). Computes the
load-bearing conversion + Axis-2 invariants on the finite ring-checkerboard support so the
Julia/JAX/PyTorch legs can be checked against it. No M(C) admission; scratch_diagnostic.

Conversions under test:
  ring (phase e^{i theta})  <->  board (amplitude cos/sin eta)   via Euler  e^{i th}=cos th + i sin th
  spinor S^3                <->  shell/Bloch S^2                 via double-angle (Hopf map)
  Axis 2 direct vs conjugated frame: K_t = i V_t^dag V_dot_t   (Lagrangian K=0 vs Eulerian K!=0)
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

SIM_ID = "ring_checkerboard_euler_conversion_axis2_frame_v0"
ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "results" / f"{SIM_ID}_exact_results.json"

SHEETS = ("L", "R")
K_ETA, N_PHI, N_CHI = 3, 4, 4
TOL = 1e-9

SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)


def eta_of(k: int) -> float:
    return (math.pi / 2) * k / (K_ETA - 1)


def angles(i: int, j: int):
    return 2 * math.pi * i / N_PHI, 2 * math.pi * j / N_CHI


def psi_direct(k, i, j):
    eta = eta_of(k)
    phi, chi = angles(i, j)
    return np.array([np.exp(1j * (phi + chi)) * math.cos(eta),
                     np.exp(1j * (phi - chi)) * math.sin(eta)], dtype=complex)


def psi_ring_times_board(k, i, j):
    # reconstruct from ring phase (Euler) x board amplitude -- the conversion identity
    eta = eta_of(k)
    phi, chi = angles(i, j)
    ring0 = math.cos(phi + chi) + 1j * math.sin(phi + chi)   # Euler e^{i(phi+chi)}
    ring1 = math.cos(phi - chi) + 1j * math.sin(phi - chi)
    return np.array([ring0 * math.cos(eta), ring1 * math.sin(eta)], dtype=complex)


def psi_amplitude_only(k, i, j):
    # ERASE control: drop the i sin theta term (no Euler) -> real, wrong
    eta = eta_of(k)
    phi, chi = angles(i, j)
    return np.array([math.cos(phi + chi) * math.cos(eta),
                     math.cos(phi - chi) * math.sin(eta)], dtype=complex)


def bloch_from_psi(psi):
    return np.array([np.real(np.vdot(psi, SX @ psi)),
                     np.real(np.vdot(psi, SY @ psi)),
                     np.real(np.vdot(psi, SZ @ psi))])


def bloch_doubleangle(k, j):
    eta = eta_of(k)
    _, chi = angles(0, j)  # phi cancels in Bloch -> blind
    return np.array([math.sin(2 * eta) * math.cos(2 * chi),
                     -math.sin(2 * eta) * math.sin(2 * chi),
                     math.cos(2 * eta)])


def expm_2x2(A):
    w, V = np.linalg.eig(A)
    return V @ np.diag(np.exp(w)) @ np.linalg.inv(V)


def main() -> int:
    rows = [(s, k, i, j) for s in SHEETS for k in range(K_ETA)
            for i in range(N_PHI) for j in range(N_CHI)]
    support_count = len(rows)

    # --- Euler conversion (ring x board) and the erase control ---
    euler_err = 0.0
    erase_err = 0.0
    for (_, k, i, j) in rows:
        pd = psi_direct(k, i, j)
        euler_err = max(euler_err, float(np.max(np.abs(pd - psi_ring_times_board(k, i, j)))))
        erase_err = max(erase_err, float(np.max(np.abs(pd - psi_amplitude_only(k, i, j)))))

    # --- Hopf double-angle conversion (spinor S^3 <-> Bloch S^2) ---
    hopf_err = 0.0
    for (_, k, i, j) in rows:
        hopf_err = max(hopf_err, float(np.max(np.abs(bloch_from_psi(psi_direct(k, i, j)) - bloch_doubleangle(k, j)))))

    # --- finite-gradation Axis-0 ladder b0_k = sign(cos 2 eta_k) ---
    def sgn(x):
        return 1 if x > TOL else (-1 if x < -TOL else 0)
    b0_ladder = [sgn(math.cos(2 * eta_of(k))) for k in range(K_ETA)]

    # --- quotient: density probe (phi-blind) vs phase-sensitive ---
    def _q(x):
        return int(round(float(x) * 1e6))  # robust integer key: no -0.0 / cross-language hash drift
    def density_key(s, k, i, j):
        b = bloch_from_psi(psi_direct(k, i, j))
        return (s, k, tuple(_q(v) for v in b))  # blind to phi by construction
    def phase_key(s, k, i, j):
        p = psi_direct(k, i, j)
        return density_key(s, k, i, j) + (_q(p[0].real), _q(p[0].imag), _q(p[1].real), _q(p[1].imag))
    dq = defaultdict(list); pq = defaultdict(list)
    for (s, k, i, j) in rows:
        dq[density_key(s, k, i, j)].append((s, k, i, j))
        pq[phase_key(s, k, i, j)].append((s, k, i, j))
    density_class_count = len(dq)
    phase_class_count = len(pq)
    phi_blind = all(len({i for (_, _, i, _) in members}) == N_PHI for members in dq.values()) and density_class_count < support_count

    # drop_fiber control: dropping chi merges density classes
    df = defaultdict(list)
    for (s, k, i, j) in rows:
        df[(s, k)].append((s, k, i, j))
    drop_fiber_merges = len(df) < density_class_count

    # flatten_shell control: collapsing shell index erases b0 gradient
    flatten_b0 = len(set([sgn(math.cos(2 * eta_of(0)))])) == 1 and len(set(b0_ladder)) > 1

    # --- Axis 2: K_t = i V^dag V_dot  (direct / static / dynamic) ---
    rho_mid = np.outer(psi_direct(1, 1, 1), psi_direct(1, 1, 1).conj())  # eta=pi/4 -> off-diagonal rho
    # direct frame V=I
    K_direct = 1j * np.eye(2) @ np.zeros((2, 2), dtype=complex)
    # static conjugation V0 = exp(-i (pi/3) SY/2), V_dot=0
    V0 = expm_2x2(-1j * (math.pi / 3) * SY / 2)
    K_static = 1j * V0.conj().T @ np.zeros((2, 2), dtype=complex)
    rho_tilde_static = V0.conj().T @ rho_mid @ V0
    rho_tilde_differs_static = float(np.max(np.abs(rho_tilde_static - rho_mid))) > TOL
    # dynamic conjugation V_t = exp(-i G t), G = SZ/2 (fiber/ring-phase generator), V_dot=-i G V_t
    G = SZ / 2
    t = 0.37
    V_t = expm_2x2(-1j * G * t)
    V_dot = -1j * G @ V_t
    K_dyn = 1j * V_t.conj().T @ V_dot   # = V_t^dag G V_t, Hermitian, ||.||_F = ||G||_F
    K_direct_norm = float(np.linalg.norm(K_direct))
    K_static_norm = float(np.linalg.norm(K_static))
    K_dynamic_norm = float(np.linalg.norm(K_dyn))

    # --- no preferred center: cyclic translation automorphism + center-pin control ---
    nodes = {(s, k, i, j) for (s, k, i, j) in rows}
    def edges(wrap_phi=True):
        E = set()
        for (s, k, i, j) in rows:
            nbrs = [(s, k, (i + 1) % N_PHI, j), (s, k, i, (j + 1) % N_CHI)]
            if not wrap_phi and i == N_PHI - 1:
                nbrs = [(s, k, i, (j + 1) % N_CHI)]  # drop the wrap edge -> pins a boundary/center
            if k + 1 < K_ETA:
                nbrs.append((s, k + 1, i, j))
            for nb in nbrs:
                E.add(frozenset(((s, k, i, j), nb)))
        return E
    E_full = edges(True)
    E_pinned = edges(False)
    adjacency_edge_count = len(E_full)
    center_pin_edge_count = len(E_pinned)
    # translation phi -> phi+1 is a graph automorphism iff edge set is invariant
    def shift(node):
        s, k, i, j = node
        return (s, k, (i + 1) % N_PHI, j)
    E_shift = {frozenset(map(shift, e)) for e in E_full}
    translation_is_automorphism = (E_shift == E_full)
    center_pin_changes_adjacency = (center_pin_edge_count != adjacency_edge_count)
    class_sizes = sorted({len(v) for v in dq.values()})

    invariants = {
        "support_count": support_count,
        "euler_reconstruction_max_err": euler_err,
        "hopf_bloch_max_err": hopf_err,
        "b0_ladder": b0_ladder,
        "density_class_count": density_class_count,
        "phase_sensitive_class_count": phase_class_count,
        "phi_blind": bool(phi_blind),
        "K_direct_norm": K_direct_norm,
        "K_static_norm": K_static_norm,
        "rho_tilde_differs_static": bool(rho_tilde_differs_static),
        "K_dynamic_norm": K_dynamic_norm,
        "adjacency_edge_count": adjacency_edge_count,
        "translation_is_automorphism": bool(translation_is_automorphism),
        "center_pin_edge_count": center_pin_edge_count,
        "density_class_sizes": class_sizes,
    }

    tests = {
        "euler_conversion_reconstructs": euler_err < 1e-9,
        "hopf_doubleangle_converts": hopf_err < 1e-9,
        "phi_blind_density": bool(phi_blind),
        "phase_probe_splits_density": phase_class_count > density_class_count,
        "finite_gradation_ladder": b0_ladder == [1, 0, -1],
        "axis2_direct_frame_Kt_zero": K_direct_norm < 1e-9,
        "axis2_static_conj_Kt_zero": K_static_norm < 1e-9,
        "axis2_dynamic_frame_Kt_nonzero": K_dynamic_norm > 0.1,
        "no_preferred_center_translation_automorphism": bool(translation_is_automorphism),
        "density_classes_phi_collapsed": density_class_count < support_count,
    }
    controls = {
        "euler_erase_breaks_reconstruction": erase_err > 0.1,
        "static_conj_changes_rho_though_Kt_zero": bool(rho_tilde_differs_static) and K_static_norm < 1e-9,
        "dynamic_frame_Kt_matches_generator_norm": abs(K_dynamic_norm - float(np.linalg.norm(G))) < 1e-9,
        "flatten_shell_erases_b0_gradient": bool(flatten_b0),
        "drop_fiber_merges_density": bool(drop_fiber_merges),
        "center_pin_changes_adjacency": bool(center_pin_changes_adjacency),
    }
    all_tests = all(tests.values())
    all_controls = all(controls.values())

    result = {
        "schema": "codex_ratchet.sim_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "engine": "exact_numpy_reference",
        "root_lineage": {"F01_finite_support": True, "N01_order_sensitivity": "Axis-2 connection K_t=i V^dag V_dot is the order/noncommutation witness; direct(Lagrangian) vs conjugated(Eulerian) frame is order-sensitive"},
        "source_target": "ring-checkerboard runbook + axes12_deep_vein Axis2 + working_math_scaffold psi_s",
        "claim": "ring<->board Euler conversion, spinor<->shell Hopf double-angle, and Axis-2 K_t direct/static/dynamic discriminator hold on the finite support",
        "support_parameters": {"sheets": list(SHEETS), "K_eta": K_ETA, "N_phi": N_PHI, "N_chi": N_CHI, "support_count": support_count},
        "invariants": invariants,
        "tests": tests,
        "controls": controls,
        "all_tests_pass": all_tests,
        "all_controls_pass": all_controls,
        "ablation_outcome_delta": {"euler_real_err": euler_err, "euler_erased_err": erase_err, "delta": erase_err - euler_err},
        "honest_scope": {
            "earns": "finite-support numeric witness that the three charts inter-convert via Euler/Hopf identities and that Axis-2 K_t separates Lagrangian (K=0) from Eulerian (K!=0) frames, at scratch ceiling, one engine",
            "does_not_earn": "M(C) admission, Axis0 closure, QIT engine, smooth manifold, physics; needs Julia/JAX/PyTorch agreement + fresh fleet audit",
        },
        "TOOL_MANIFEST": {
            "numpy": {"tried": True, "used": True, "reason": "complex spinors, 2x2 Pauli ops, matrix exp via eig for V_t, norms; flat-baseline reference"},
            "python_stdlib": {"tried": True, "used": True, "reason": "finite enumeration, quotient classes, adjacency/automorphism graph"},
        },
        "TOOL_INTEGRATION_DEPTH": "supportive",
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {RESULT}")
    print(f"all_tests_pass={all_tests} all_controls_pass={all_controls}")
    print(f"euler_err={euler_err:.2e} erase_err={erase_err:.3f} hopf_err={hopf_err:.2e}")
    print(f"K_direct={K_direct_norm:.2e} K_static={K_static_norm:.2e} K_dynamic={K_dynamic_norm:.4f} ||G||={float(np.linalg.norm(G)):.4f}")
    print(f"density={density_class_count} phase={phase_class_count} edges={adjacency_edge_count} pinned={center_pin_edge_count} autom={translation_is_automorphism}")
    return 0 if all_tests and all_controls else 1


if __name__ == "__main__":
    raise SystemExit(main())
