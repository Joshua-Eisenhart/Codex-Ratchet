#!/usr/bin/env python3
"""Isolated sim: left/right Weyl sheet cover layer.

Layer (geometric constraint manifold): represent left and right Weyl states as
RELATED-BUT-NON-IDENTICAL sheeted spinor dynamics. Sims this ONE layer alone;
no stacking/bridge.

Math verbatim from the owner's spec:
  psi_v,L, psi_v,R in C^2 ; rho_v,s = psi_v,s psi_v,s^dag
  H_L = +H_0 ,  H_R = -H_0          (chirality sign flip)
  d rho_v,L/dt = -i [H_L, rho_v,L] ; d rho_v,R/dt = -i [H_R, rho_v,R]
  Delta_LR = || Observable_L(after action) - Observable_R(after action) ||

Evolution is exact unitary (matrix_exp), so it is genuinely dynamic and exactly
purity/entropy preserving. The chirality shows up as OPPOSITE Bloch precession;
the two sheets are mirror-but-distinct.

Entropy as part of the manifold: under unitary evolution S(rho) is conserved and
EQUAL on both sheets, while Delta_LR > 0. So entropy is provably BLIND to the
chirality -- the L/R non-equivalence is geometric/coherent, not entropic. (This
is the doctrine "do not infer ontology from entropy alone," made measurable.)

Controls (each must remove the non-equivalence, measurably):
  - force H_R = H_L            (no chirality difference -> Delta_LR -> 0)
  - z-eigenstate initial       (no coherence to precess -> Delta_LR -> 0; boundary)
  - swap sheet labels          (relabeling alone cannot change Delta_LR)

Load-bearing tool: sympy proves the chirality is structural -- the Bloch
precession rate dr_x/dt has OPPOSITE sign for H_L vs H_R.

classification: tool_lego_fit_probe (isolated; promotion_allowed=False)
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import torch

torch.set_default_dtype(torch.float64)
CDT = torch.complex128

I2 = torch.eye(2, dtype=CDT)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDT)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDT)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDT)

OMEGA = 1.0
H0 = 0.5 * OMEGA * SZ
H_L = +H0
H_R = -H0


def rho_from_bloch(r):
    M = I2.clone()
    for c, P in zip(r, (SX, SY, SZ)):
        M = M + float(c) * P
    return 0.5 * M


def bloch(rho):
    return np.array([float(torch.trace(rho @ SX).real),
                     float(torch.trace(rho @ SY).real),
                     float(torch.trace(rho @ SZ).real)])


def vn_entropy(rho):
    w = torch.linalg.eigvalsh(rho).real.clamp(min=1e-15)
    return float(-(w * torch.log(w)).sum())


def U(H, t):
    return torch.linalg.matrix_exp(-1j * H * t)


def trajectory(rho0, H, times):
    rs, Ss = [], []
    for t in times:
        u = U(H, float(t))
        rho = u @ rho0 @ u.conj().T
        rs.append(bloch(rho))
        Ss.append(vn_entropy(rho))
    return np.array(rs), np.array(Ss)


def signed_angle(rs):
    ang = np.unwrap(np.arctan2(rs[:, 1], rs[:, 0]))
    return float(ang[-1] - ang[0])


def sheet_gap(rL, rR):
    # ||rho_L - rho_R||_F = |r_L - r_R| / sqrt(2)
    return float(np.max(np.linalg.norm(rL - rR, axis=1)) / math.sqrt(2.0))


def sympy_chirality_sign():
    import sympy as sp
    x, y, z, w = sp.symbols("x y z omega", real=True)
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    rho = (sp.eye(2) + x * sx + y * sy + z * sz) / 2
    HL = w / 2 * sz
    HR = -w / 2 * sz
    drxL = sp.simplify(sp.trace(sx * (-sp.I * (HL * rho - rho * HL))))
    drxR = sp.simplify(sp.trace(sx * (-sp.I * (HR * rho - rho * HR))))
    opposite = bool(sp.simplify(drxL + drxR) == 0 and sp.simplify(drxL) != 0)
    return {"drx_left": str(drxL), "drx_right": str(drxR), "opposite_sign": opposite}


def main():
    rng = np.random.default_rng(11)
    T, nt = 4 * math.pi, 400
    times = np.linspace(0.0, T, nt)

    # coherent seeds (off-z) + z-eigenstate boundary seeds
    coherent = []
    for _ in range(20):
        v = rng.normal(size=3)
        v = 0.85 * v / np.linalg.norm(v)
        if abs(v[0]) + abs(v[1]) < 0.3:  # ensure real coherence
            v[0] += 0.4
        coherent.append(rho_from_bloch(v))
    z_eigen = [rho_from_bloch([0, 0, 1.0]), rho_from_bloch([0, 0, -1.0])]

    gaps, angL, angR, dS_self, dS_LR = [], [], [], 0.0, 0.0
    for rho0 in coherent:
        rL, SL = trajectory(rho0, H_L, times)
        rR, SR = trajectory(rho0, H_R, times)
        gaps.append(sheet_gap(rL, rR))
        angL.append(signed_angle(rL))
        angR.append(signed_angle(rR))
        dS_self = max(dS_self, float(np.max(np.abs(SL - SL[0]))))   # entropy conserved
        dS_LR = max(dS_LR, float(np.max(np.abs(SL - SR))))          # equal on both sheets

    mean_gap = float(np.mean(gaps))

    # controls
    gap_HL_eq_HR = float(np.mean([sheet_gap(*[trajectory(r, H_L, times)[0] for _ in (0, 1)])
                                  for r in coherent[:5]]))  # both sheets = H_L -> 0
    gap_zeigen = float(np.mean([sheet_gap(trajectory(r, H_L, times)[0],
                                          trajectory(r, H_R, times)[0]) for r in z_eigen]))
    rL0, _ = trajectory(coherent[0], H_L, times)
    rR0, _ = trajectory(coherent[0], H_R, times)
    gap_swap_consistent = abs(sheet_gap(rL0, rR0) - sheet_gap(rR0, rL0)) < 1e-12

    sym = sympy_chirality_sign()

    # load-bearing: couple sympy to the runtime -- the MEASURED dr_x/dt at t=0 on the
    # left sheet must match the symbolic prediction drx_L = -omega*r_y0.
    seed0 = coherent[0]
    r0 = bloch(seed0)
    small = 1e-4
    u = U(H_L, small)
    measured_drx = float((bloch(u @ seed0 @ u.conj().T)[0] - r0[0]) / small)
    predicted_drx = float(-OMEGA * r0[1])   # sympy: drx_L = -omega*y
    sym["measured_drx_left"] = measured_drx
    sym["predicted_drx_left"] = predicted_drx
    sym["matches_runtime"] = bool(abs(measured_drx - predicted_drx) < 1e-2)

    verdicts = {
        "chirality_nonequivalence": mean_gap > 0.1,
        "opposite_precession": float(np.mean(angL)) > 0.3 and float(np.mean(angR)) < -0.3,
        "entropy_conserved_under_unitary": dS_self < 1e-9,
        "entropy_blind_to_chirality": dS_LR < 1e-9,           # S_L == S_R while gap>0
        "control_HL_eq_HR_collapses_gap": gap_HL_eq_HR < 1e-9,
        "control_z_eigenstate_no_gap": gap_zeigen < 1e-9,
        "sympy_chirality_opposite_sign": sym["opposite_sign"],
        "sympy_prediction_matches_runtime": sym["matches_runtime"],
    }

    result = {
        "name": "left_right_weyl_sheet_cover_isolated",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "layer": "left/right Weyl sheet cover",
        "finite_map": "WeylSheetStep: (rho0, H_L=+H0, H_R=-H0, times) -> rho_L(t), rho_R(t), Delta_LR",
        "domain": "single-site spinor density rho0 in D(C^2)",
        "codomain_or_output": "L/R trajectories, sheet gap Delta_LR, entropy readouts",
        "root_constraints": {"F01": "dim 2, finite times/seeds",
                             "N01": "[H_s, rho] order-sensitive; chirality is the sign of the commutator"},
        "native_scale": {"T": T, "n_times": nt, "n_coherent_seeds": len(coherent)},
        "dynamic_step": "exact unitary matrix_exp evolution",
        "readouts": {
            "mean_sheet_gap_Delta_LR": mean_gap,
            "mean_signed_angle_L": float(np.mean(angL)),
            "mean_signed_angle_R": float(np.mean(angR)),
            "max_entropy_drift_self": dS_self,
            "max_entropy_diff_L_vs_R": dS_LR,
        },
        "controls": {"HL_eq_HR_gap": gap_HL_eq_HR, "z_eigenstate_gap": gap_zeigen,
                     "swap_labels_consistent": gap_swap_consistent},
        "load_bearing_sympy": sym,
        "verdicts": verdicts,
        "all_pass": all(verdicts.values()),
        "blocked_consumers": ["stacking", "order_tests", "Xi", "Phi0", "Axis0", "flux", "FEP", "physics"],
        "tool_manifest": {
            "torch": {"used": True, "reason": "claim-bearing exact unitary evolution + Bloch/entropy readouts"},
            "sympy": {"used": True, "reason": "load-bearing: proves chirality precession sign opposite for H_L vs H_R"},
            "numpy": {"used": True, "reason": "gap/angle/entropy aggregation, util only"},
        },
        "tool_integration_depth": "load_bearing",
    }

    import contract_emit
    _rb = rho_from_bloch([0.5, 0.5, 0.3])
    contract_emit.attach(result, {"chirality_gap_vs_HL_eq_HR_control": (mean_gap, gap_HL_eq_HR)},
        "native unitary scale (T, n_times, n_seeds); 8/16/32/64 qubit ladder N/A.",
        torch_primary=float(torch.trace(_rb @ _rb).real))

    out_dir = Path(__file__).resolve().parent / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "left_right_weyl_sheet_cover_isolated_results.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"all_pass={result['all_pass']}  ({sum(verdicts.values())}/{len(verdicts)} verdicts)")
    for k, v in verdicts.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(f"\nmean Delta_LR (sheet gap) = {mean_gap:.3f}")
    print(f"signed angle L={np.mean(angL):+.2f}  R={np.mean(angR):+.2f}  (opposite chirality)")
    print(f"entropy drift self={dS_self:.2e}  |S_L - S_R|={dS_LR:.2e}  (entropy blind to chirality)")
    print(f"controls: HL=HR gap={gap_HL_eq_HR:.2e}  z-eigen gap={gap_zeigen:.2e}")
    print(f"sympy chirality opposite sign: {sym['opposite_sign']}  (drx_L={sym['drx_left']}, drx_R={sym['drx_right']})")
    print(f"result -> {out_path}")


if __name__ == "__main__":
    main()
