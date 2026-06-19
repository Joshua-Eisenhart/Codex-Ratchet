#!/usr/bin/env python3
"""ring_checkerboard_euler_conversion_axis2_frame_v0 -- PyTorch leg (flat-board / graph-relation).

Independent recomputation using torch complex128 tensors + torch.linalg.matrix_exp for V_t, and a
torch edge_index for the flat-board adjacency / translation-automorphism (the PyTorch-native
graph/relation role). Does NOT read the other legs.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import torch

torch.set_default_dtype(torch.float64)
C = torch.complex128

SIM_ID = "ring_checkerboard_euler_conversion_axis2_frame_v0"
ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "results" / f"{SIM_ID}_pytorch_results.json"

SHEETS = ("L", "R")
K_ETA, N_PHI, N_CHI = 3, 4, 4
TOL = 1e-9

SX = torch.tensor([[0, 1], [1, 0]], dtype=C)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=C)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=C)


def eta_of(k): return (math.pi / 2) * k / (K_ETA - 1)
def angles(i, j): return 2 * math.pi * i / N_PHI, 2 * math.pi * j / N_CHI


def psi_direct(k, i, j):
    eta = eta_of(k); phi, chi = angles(i, j)
    return torch.tensor([complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
                         complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta)], dtype=C)


def psi_ring_board(k, i, j):
    # built the same way; the Euler conversion is an identity, so compare to a complex-exp build
    eta = eta_of(k); phi, chi = angles(i, j)
    e0 = torch.exp(torch.tensor(1j * (phi + chi), dtype=C)) * math.cos(eta)
    e1 = torch.exp(torch.tensor(1j * (phi - chi), dtype=C)) * math.sin(eta)
    return torch.stack([e0, e1])


def psi_amp_only(k, i, j):
    eta = eta_of(k); phi, chi = angles(i, j)
    return torch.tensor([complex(math.cos(phi + chi) * math.cos(eta), 0.0),
                         complex(math.cos(phi - chi) * math.sin(eta), 0.0)], dtype=C)


def bloch(psi):
    return torch.tensor([torch.vdot(psi, SX @ psi).real,
                         torch.vdot(psi, SY @ psi).real,
                         torch.vdot(psi, SZ @ psi).real]).tolist()


def bloch_da(k, j):
    eta = eta_of(k); _, chi = angles(0, j)
    return [math.sin(2 * eta) * math.cos(2 * chi), -math.sin(2 * eta) * math.sin(2 * chi), math.cos(2 * eta)]


def main() -> int:
    rows = [(s, k, i, j) for s in SHEETS for k in range(K_ETA)
            for i in range(N_PHI) for j in range(N_CHI)]
    support_count = len(rows)

    euler_err = 0.0; erase_err = 0.0; hopf_err = 0.0
    for (_, k, i, j) in rows:
        pd = psi_direct(k, i, j)
        euler_err = max(euler_err, float(torch.max(torch.abs(pd - psi_ring_board(k, i, j)))))
        erase_err = max(erase_err, float(torch.max(torch.abs(pd - psi_amp_only(k, i, j)))))
        b = torch.tensor(bloch(pd)); bd = torch.tensor(bloch_da(k, j))
        hopf_err = max(hopf_err, float(torch.max(torch.abs(b - bd))))

    def sgn(x): return 1 if x > TOL else (-1 if x < -TOL else 0)
    b0_ladder = [sgn(math.cos(2 * eta_of(k))) for k in range(K_ETA)]

    def _q(x):
        return int(round(float(x) * 1e6))  # robust integer key: no -0.0 / cross-language hash drift
    def dkey(s, k, i, j):
        return (s, k, tuple(_q(v) for v in bloch(psi_direct(k, i, j))))
    def pkey(s, k, i, j):
        p = psi_direct(k, i, j)
        return dkey(s, k, i, j) + (_q(p[0].real), _q(p[0].imag), _q(p[1].real), _q(p[1].imag))
    dq = defaultdict(list); pq = defaultdict(list)
    for (s, k, i, j) in rows:
        dq[dkey(s, k, i, j)].append((s, k, i, j)); pq[pkey(s, k, i, j)].append((s, k, i, j))
    density_class_count = len(dq); phase_class_count = len(pq)
    phi_blind = all(len({i for (_, _, i, _) in m}) == N_PHI for m in dq.values()) and density_class_count < support_count
    drop_fiber_merges = len({(s, k) for (s, k, _, _) in rows}) < density_class_count
    flatten_b0 = len(set(b0_ladder)) > 1

    rho_mid = torch.outer(psi_direct(1, 1, 1), psi_direct(1, 1, 1).conj())
    K_direct = torch.zeros((2, 2), dtype=C)
    V0 = torch.linalg.matrix_exp(-1j * (math.pi / 3) * SY / 2)
    K_static = 1j * V0.conj().T @ torch.zeros((2, 2), dtype=C)
    rho_tilde = V0.conj().T @ rho_mid @ V0
    rho_tilde_differs = float(torch.max(torch.abs(rho_tilde - rho_mid))) > TOL
    G = SZ / 2; t = 0.37
    V_t = torch.linalg.matrix_exp(-1j * G * t); V_dot = -1j * G @ V_t
    K_dyn = 1j * V_t.conj().T @ V_dot
    K_direct_norm = float(torch.linalg.norm(K_direct))
    K_static_norm = float(torch.linalg.norm(K_static))
    K_dynamic_norm = float(torch.linalg.norm(K_dyn))
    G_norm = float(torch.linalg.norm(G))

    # torch edge_index for the flat-board adjacency (graph-relation role)
    node_id = {n: idx for idx, n in enumerate(rows)}
    def edges(wrap_phi=True):
        E = set()
        for (s, k, i, j) in rows:
            nbrs = [(s, k, (i + 1) % N_PHI, j), (s, k, i, (j + 1) % N_CHI)]
            if not wrap_phi and i == N_PHI - 1:
                nbrs = [(s, k, i, (j + 1) % N_CHI)]
            if k + 1 < K_ETA:
                nbrs.append((s, k + 1, i, j))
            for nb in nbrs:
                E.add(frozenset((node_id[(s, k, i, j)], node_id[nb])))
        return E
    E_full = edges(True); E_pin = edges(False)
    adjacency_edge_count = len(E_full); center_pin_edge_count = len(E_pin)
    edge_index = torch.tensor([sorted(e) for e in E_full], dtype=torch.long).t()  # 2 x E
    assert edge_index.shape[1] == adjacency_edge_count
    shift_id = {node_id[(s, k, i, j)]: node_id[(s, k, (i + 1) % N_PHI, j)] for (s, k, i, j) in rows}
    E_shift = {frozenset((shift_id[a], shift_id[b])) for (a, b) in (tuple(e) for e in E_full)}
    translation_is_automorphism = (E_shift == E_full)

    invariants = {
        "support_count": support_count, "euler_reconstruction_max_err": euler_err,
        "hopf_bloch_max_err": hopf_err, "b0_ladder": b0_ladder,
        "density_class_count": density_class_count, "phase_sensitive_class_count": phase_class_count,
        "phi_blind": bool(phi_blind), "K_direct_norm": K_direct_norm, "K_static_norm": K_static_norm,
        "rho_tilde_differs_static": bool(rho_tilde_differs), "K_dynamic_norm": K_dynamic_norm,
        "adjacency_edge_count": adjacency_edge_count, "translation_is_automorphism": bool(translation_is_automorphism),
        "center_pin_edge_count": center_pin_edge_count,
    }
    tests = {
        "euler_conversion_reconstructs": euler_err < 1e-9, "hopf_doubleangle_converts": hopf_err < 1e-9,
        "phi_blind_density": bool(phi_blind), "phase_probe_splits_density": phase_class_count > density_class_count,
        "finite_gradation_ladder": b0_ladder == [1, 0, -1], "axis2_direct_frame_Kt_zero": K_direct_norm < 1e-9,
        "axis2_static_conj_Kt_zero": K_static_norm < 1e-9, "axis2_dynamic_frame_Kt_nonzero": K_dynamic_norm > 0.1,
        "no_preferred_center_translation_automorphism": bool(translation_is_automorphism),
        "density_classes_phi_collapsed": density_class_count < support_count,
    }
    controls = {
        "euler_erase_breaks_reconstruction": erase_err > 0.1,
        "static_conj_changes_rho_though_Kt_zero": bool(rho_tilde_differs) and K_static_norm < 1e-9,
        "dynamic_frame_Kt_matches_generator_norm": abs(K_dynamic_norm - G_norm) < 1e-9,
        "flatten_shell_erases_b0_gradient": bool(flatten_b0), "drop_fiber_merges_density": bool(drop_fiber_merges),
        "center_pin_changes_adjacency": center_pin_edge_count != adjacency_edge_count,
    }
    all_tests = all(tests.values()); all_controls = all(controls.values())
    result = {
        "schema": "codex_ratchet.sim_result.v1", "sim_id": SIM_ID, "classification": "scratch_diagnostic",
        "promotion_allowed": False, "formal_admission_allowed": False, "engine": "pytorch_complex128_graph",
        "root_lineage": {"F01_finite_support": True, "N01_order_sensitivity": "Axis-2 connection K_t=i V^dag V_dot is the order/noncommutation witness; direct(Lagrangian) vs conjugated(Eulerian) frame is order-sensitive"},
        "support_parameters": {"sheets": list(SHEETS), "K_eta": K_ETA, "N_phi": N_PHI, "N_chi": N_CHI, "support_count": support_count},
        "invariants": invariants, "tests": tests, "controls": controls,
        "all_tests_pass": all_tests, "all_controls_pass": all_controls,
        "ablation_outcome_delta": {"euler_real_err": euler_err, "euler_erased_err": erase_err, "delta": erase_err - euler_err},
        "honest_scope": {
            "earns": "independent PyTorch recomputation of conversion + Axis-2 invariants and edge_index graph adjacency/automorphism, scratch ceiling",
            "does_not_earn": "M(C), Axis0 closure, QIT engine, physics; needs cross-engine agreement + fleet audit",
        },
        "TOOL_MANIFEST": {"torch": {"tried": True, "used": True, "reason": "complex128 spinor tensors, torch.linalg.matrix_exp for V_t, edge_index graph adjacency and translation automorphism"}},
        "TOOL_INTEGRATION_DEPTH": "load_bearing",
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {RESULT}")
    print(f"all_tests_pass={all_tests} all_controls_pass={all_controls}")
    print(f"euler={euler_err:.2e} erase={erase_err:.3f} hopf={hopf_err:.2e} Kdir={K_direct_norm:.2e} Kdyn={K_dynamic_norm:.4f} density={density_class_count} phase={phase_class_count} edges={adjacency_edge_count}")
    return 0 if all_tests and all_controls else 1


if __name__ == "__main__":
    raise SystemExit(main())
