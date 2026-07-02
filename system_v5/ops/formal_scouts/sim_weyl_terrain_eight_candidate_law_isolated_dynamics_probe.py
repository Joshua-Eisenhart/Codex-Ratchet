#!/usr/bin/env python3
"""Isolated dynamics sim: the EIGHT Weyl-sheet terrain candidate laws.

Layer (geometric constraint manifold): local Weyl dynamical-law candidates.
Sims this ONE layer in isolation -- it does not stack, order, bridge, or touch
Xi/Phi0/Axis0/flux. It asks only:

  - does each of the 8 candidate laws have the dynamics its shorthand claims?
  - is each law's signature killed by its own negative control?
  - are the 8 laws actually 8 distinct dynamics (left/right pairs separated by
    chirality sign), not 8 labels?
  - what are the entropy/QIT readouts of each law? (Entropy is part of the
    manifold and how the sim works -- it is read on the evolving state, not a
    free scalar.)

Math verbatim from the owner's terrain spec (GKSL forms):
  D[L](rho) = L rho L^dag - 1/2 (L^dag L rho + rho L^dag L)
  H_L = +H_0,  H_R = -H_0,  H_0 = (omega/2) sigma_z   (chirality sign flip)

  Left sheet (H_L):                 Right sheet (H_R):
    Funnel  : depolarizing            Cannon  : depolarizing
    Vortex  : Ham. circ. + weak deph  Spiral  : Ham. circ. + weak deph
    Pit     : sigma_- damping (-> +z) Source  : sigma_+ damping (-> -z)
    Hill    : projector z-dephasing   Citadel : projector z-dephasing
  (Hill/Citadel require [K, P_pm]=0, so K is diagonal in the z-projector basis;
   Citadel uses the opposite chirality sign K_R = -K_L.)

No SMT/z3 here: a z3 wrapper around an already-measured float is decorative.
The load-bearing non-numeric tool is sympy (symbolic derivation of the
depolarizing Bloch contraction rate, which the numeric run must match). The
real evidence is the measured dynamics, the controls that flip, and entropy.

classification: tool_lego_fit_probe (isolated dynamics; promotion_allowed=False)
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
S_MINUS = torch.tensor([[0, 1], [0, 0]], dtype=CDT)  # fixed point |0><0| -> r_z=+1
S_PLUS = torch.tensor([[0, 0], [1, 0]], dtype=CDT)   # fixed point |1><1| -> r_z=-1

OMEGA = 1.0
H0 = 0.5 * OMEGA * SZ
H_L = +H0   # left Weyl sheet
H_R = -H0   # right Weyl sheet (chirality sign flip)


def dag(A):
    return A.conj().transpose(-1, -2)


def comm(A, rho):
    return A @ rho - rho @ A


def dissipator(L, rho):
    LdL = dag(L) @ L
    return L @ rho @ dag(L) - 0.5 * (LdL @ rho + rho @ LdL)


# ---- the eight candidate laws ------------------------------------------- #
def X_funnel(rho, lam=0.15, eps=0.1):
    diss = dissipator(SX, rho) + dissipator(SY, rho) + dissipator(SZ, rho)
    return lam * diss - 1j * eps * comm(H_L, rho)


def X_cannon(rho, lam=0.15, eps=0.1):
    diss = dissipator(SX, rho) + dissipator(SY, rho) + dissipator(SZ, rho)
    return lam * diss - 1j * eps * comm(H_R, rho)


def X_vortex(rho, eps=0.02):
    return -1j * comm(H_L, rho) + eps * dissipator(SZ, rho)


def X_spiral(rho, eps=0.02):
    return -1j * comm(H_R, rho) + eps * dissipator(SZ, rho)


def X_pit(rho, gam=0.3, eps=0.1):
    return gam * dissipator(S_MINUS, rho) - 1j * eps * comm(H_L, rho)


def X_source(rho, gam=0.3, eps=0.1):
    return gam * dissipator(S_PLUS, rho) - 1j * eps * comm(H_R, rho)


def _hill_like(rho, K, kap):
    Pp = 0.5 * (I2 + SZ)
    Pm = 0.5 * (I2 - SZ)
    deph = Pp @ rho @ Pp + Pm @ rho @ Pm - rho
    return -1j * comm(K, rho) + kap * deph


def X_hill(rho, kap=0.25, delta=0.3):
    return _hill_like(rho, +0.5 * delta * SZ, kap)   # [K, P_pm] = 0


def X_citadel(rho, kap=0.25, delta=0.3):
    return _hill_like(rho, -0.5 * delta * SZ, kap)   # opposite chirality sign


LAWS = {
    "funnel": X_funnel, "vortex": X_vortex, "pit": X_pit, "hill": X_hill,
    "cannon": X_cannon, "spiral": X_spiral, "source": X_source, "citadel": X_citadel,
}
LEFT = ["funnel", "vortex", "pit", "hill"]
RIGHT = ["cannon", "spiral", "source", "citadel"]


# ---- finite integrator with hard constraints enforced ------------------- #
def project_density(rho):
    rho = 0.5 * (rho + dag(rho))
    w, V = torch.linalg.eigh(rho)
    w = torch.clamp(w.real, min=0.0).to(CDT)
    rho = (V * w) @ dag(V)
    return rho / torch.trace(rho).real


def bloch(rho):
    return [float(torch.trace(rho @ SX).real),
            float(torch.trace(rho @ SY).real),
            float(torch.trace(rho @ SZ).real)]


def vn_entropy(r_norm):
    """von Neumann entropy of a qubit from its Bloch radius (eigs = (1+-|r|)/2)."""
    rn = min(max(r_norm, 0.0), 1.0)
    p = 0.5 * (1.0 + rn)
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -(p * math.log(p) + (1.0 - p) * math.log(1.0 - p))   # nats; max = ln2


def evolve(rho0, Xfn, n_steps, dt):
    rho = rho0.clone()
    traj_r, traj_purity, traj_S = [], [], []
    max_trace_err, min_eig = 0.0, 1.0
    for _ in range(n_steps):
        rho = project_density(rho + dt * Xfn(rho))
        r = bloch(rho)
        traj_r.append(r)
        traj_purity.append(float(torch.trace(rho @ rho).real))
        traj_S.append(vn_entropy(float(np.linalg.norm(r))))
        max_trace_err = max(max_trace_err, abs(float(torch.trace(rho).real) - 1.0))
        min_eig = min(min_eig, float(torch.linalg.eigvalsh(rho).min()))
    return np.array(traj_r), np.array(traj_purity), np.array(traj_S), max_trace_err, min_eig


def random_state(rng, pure=True):
    z = rng.normal(size=4)
    psi = torch.tensor([z[0] + 1j * z[1], z[2] + 1j * z[3]], dtype=CDT)
    psi = psi / torch.linalg.norm(psi)
    rho = torch.outer(psi, psi.conj())
    if not pure:
        rho = 0.6 * rho + 0.4 * 0.5 * I2
    return project_density(rho)


def signatures(traj_r, traj_purity, traj_S):
    r0, rf = traj_r[0], traj_r[-1]
    ang = np.unwrap(np.arctan2(traj_r[:, 1], traj_r[:, 0]))
    return {
        "final_r_norm": float(np.linalg.norm(rf)),
        "final_rz": float(rf[2]),
        "final_rxy": float(np.linalg.norm(rf[:2])),
        "rz_retention": float(abs(rf[2] - r0[2])),
        "final_purity": float(traj_purity[-1]),
        "signed_xy_angle": float(ang[-1] - ang[0]),
        "final_entropy": float(traj_S[-1]),
        "entropy_production": float(traj_S[-1] - traj_S[0]),
    }


def feature(sig):
    return np.array([sig["final_r_norm"], sig["final_rz"], sig["final_rxy"],
                     sig["final_purity"], 0.1 * sig["signed_xy_angle"]])


def sympy_depolarizing_rate():
    import sympy as sp
    x, y, z, lam = sp.symbols("x y z lam", real=True)
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    rho = (sp.eye(2) + x * sx + y * sy + z * sz) / 2

    def D(L):
        return L * rho * L.H - (L.H * L * rho + rho * L.H * L) / 2

    X = lam * (D(sx) + D(sy) + D(sz))
    ok = all(sp.simplify(sp.trace(X * s) + 4 * lam * v) == 0
             for s, v in [(sx, x), (sy, y), (sz, z)])
    return {"depolarizing_bloch_rate": "-4*lam*(x,y,z)", "verified": bool(ok)}


# ---- per-law negative controls (the dissipative/Hamiltonian piece killed) -- #
def metric(kind, traj_r, traj_purity):
    if kind == "purity_drop":
        return float(traj_purity[0] - traj_purity[-1])
    if kind == "final_rz":
        return float(traj_r[-1][2])
    if kind == "final_rxy":
        return float(np.linalg.norm(traj_r[-1][:2]))
    if kind == "abs_angle":
        ang = np.unwrap(np.arctan2(traj_r[:, 1], traj_r[:, 0]))
        return float(abs(ang[-1] - ang[0]))
    raise ValueError(kind)


CONTROLS = {
    "funnel":  (lambda r: X_funnel(r, lam=0.0),                 "purity_drop", lambda v: v > 0.1,  lambda v: v < 0.05),
    "cannon":  (lambda r: X_cannon(r, lam=0.0),                 "purity_drop", lambda v: v > 0.1,  lambda v: v < 0.05),
    "pit":     (lambda r: X_pit(r, gam=0.0),                    "final_rz",    lambda v: v > 0.85, lambda v: v < 0.85),
    "source":  (lambda r: X_source(r, gam=0.0),                 "final_rz",    lambda v: v < -0.85, lambda v: v > -0.85),
    "vortex":  (lambda r: X_vortex(r) + 1j * comm(H_L, r),      "abs_angle",   lambda v: v > 1.0,  lambda v: v < 0.2),
    "spiral":  (lambda r: X_spiral(r) + 1j * comm(H_R, r),      "abs_angle",   lambda v: v > 1.0,  lambda v: v < 0.2),
    "hill":    (lambda r: X_hill(r, kap=0.0),                   "final_rxy",   lambda v: v < 0.15, lambda v: v > 0.1),
    "citadel": (lambda r: X_citadel(r, kap=0.0),                "final_rxy",   lambda v: v < 0.15, lambda v: v > 0.1),
}


def main():
    rng = np.random.default_rng(7)
    dt, n_steps, n_seeds = 0.01, 1500, 24
    seeds = [random_state(rng, pure=(i % 3 != 0)) for i in range(n_seeds)]

    law_sig, law_feat = {}, {}
    cmax_trace, cmin_eig = 0.0, 1.0
    for name, Xfn in LAWS.items():
        sigs, feats = [], []
        for rho0 in seeds:
            tr, pur, S, te, me = evolve(rho0, Xfn, n_steps, dt)
            cmax_trace, cmin_eig = max(cmax_trace, te), min(cmin_eig, me)
            s = signatures(tr, pur, S)
            sigs.append(s)
            feats.append(feature(s))
        law_sig[name] = {k: float(np.mean([s[k] for s in sigs])) for k in sigs[0]}
        law_feat[name] = np.mean(feats, axis=0)

    # negative controls (real vs structure-killed), averaged over multiple seeds
    ctrl_seeds = seeds[:8]
    control_pass = {}
    for name, (cfn, kind, real_pred, ctrl_pred) in CONTROLS.items():
        real_vals, ctrl_vals = [], []
        for probe in ctrl_seeds:
            tr_r, pur_r, _, _, _ = evolve(probe, LAWS[name], n_steps, dt)
            tr_c, pur_c, _, _, _ = evolve(probe, cfn, n_steps, dt)
            real_vals.append(metric(kind, tr_r, pur_r))
            ctrl_vals.append(metric(kind, tr_c, pur_c))
        control_pass[name] = bool(real_pred(float(np.mean(real_vals)))
                                  and ctrl_pred(float(np.mean(ctrl_vals))))

    # distinguishability: the 8 are 8 distinct dynamics
    names = list(LAWS)
    pair = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            pair[f"{names[i]}__{names[j]}"] = float(np.linalg.norm(law_feat[names[i]] - law_feat[names[j]]))
    min_pair = min(pair.values())

    # left/right chirality separation (same family, opposite Hamiltonian sign)
    def chir(a, b):
        sa, sb = law_sig[a]["signed_xy_angle"], law_sig[b]["signed_xy_angle"]
        return bool(np.sign(sa) != np.sign(sb) and abs(sa) > 0.3 and abs(sb) > 0.3)

    sym = sympy_depolarizing_rate()

    # load-bearing: the MEASURED pure-depolarizing contraction rate must match the
    # symbolic -4*lam (couples sympy to the runtime; not self-certification).
    lam_f = 0.15
    tr_f, _, _, _, _ = evolve(seeds[2], lambda r: X_funnel(r, lam=lam_f, eps=0.0), n_steps, dt)
    rn = np.linalg.norm(tr_f, axis=1)
    m = rn > 0.15
    measured_rate = float(-np.polyfit(np.arange(len(rn))[m] * dt, np.log(rn[m]), 1)[0]) if m.sum() > 5 else 0.0
    sym["measured_depolarizing_rate"] = measured_rate
    sym["symbolic_rate_4lam"] = 4 * lam_f
    sym["rate_matches"] = abs(measured_rate - 4 * lam_f) < 0.05

    # raw (pre-projection) physicality: the Euler step itself must stay ~physical,
    # else the integrator's repair -- not the law -- would be doing the physics.
    raw_min_eig, raw_trace_err = 1.0, 0.0
    for nm in ("funnel", "pit", "vortex"):
        rho = seeds[3].clone()
        for _ in range(n_steps):
            raw = rho + dt * LAWS[nm](rho)
            raw_min_eig = min(raw_min_eig, float(torch.linalg.eigvalsh(0.5 * (raw + dag(raw))).min()))
            raw_trace_err = max(raw_trace_err, abs(float(torch.trace(raw).real) - 1.0))
            rho = project_density(raw)

    verdicts = {
        # positive signatures
        "funnel_contracts": law_sig["funnel"]["final_r_norm"] < 0.15,
        "cannon_contracts": law_sig["cannon"]["final_r_norm"] < 0.15,
        "pit_to_plus_z": law_sig["pit"]["final_rz"] > 0.85,
        "source_to_minus_z": law_sig["source"]["final_rz"] < -0.85,
        "vortex_rotates_keeps_purity": law_sig["vortex"]["signed_xy_angle"] != 0
            and abs(law_sig["vortex"]["signed_xy_angle"]) > 1.0 and law_sig["vortex"]["final_purity"] > 0.6,
        "spiral_rotates_keeps_purity": abs(law_sig["spiral"]["signed_xy_angle"]) > 1.0
            and law_sig["spiral"]["final_purity"] > 0.6,
        "hill_keeps_z_kills_xy": law_sig["hill"]["final_rxy"] < 0.15 and law_sig["hill"]["rz_retention"] < 0.15,
        "citadel_keeps_z_kills_xy": law_sig["citadel"]["final_rxy"] < 0.15 and law_sig["citadel"]["rz_retention"] < 0.15,
        # controls kill each signature
        **{f"{n}_control_kills_signature": control_pass[n] for n in LAWS},
        # distinctness + chirality
        "eight_laws_distinct": min_pair > 0.15,
        "chirality_funnel_vs_cannon": chir("funnel", "cannon"),
        "chirality_hill_vs_citadel": chir("hill", "citadel"),
        # entropy is a real readout that participates
        "funnel_entropy_to_max": law_sig["funnel"]["final_entropy"] > 0.6,   # -> ln2 ~ 0.693
        "cannon_entropy_to_max": law_sig["cannon"]["final_entropy"] > 0.6,
        "pit_entropy_to_zero": law_sig["pit"]["final_entropy"] < 0.1,
        "source_entropy_to_zero": law_sig["source"]["final_entropy"] < 0.1,
        # tooling + constraints
        "sympy_depolarizing_rate_correct": sym["verified"],
        "funnel_rate_matches_symbolic": sym["rate_matches"],          # measured == -4*lam
        "raw_dynamics_stay_physical": raw_min_eig > -1e-2 and raw_trace_err < 1e-3,
    }

    result = {
        "name": "weyl_terrain_eight_candidate_law_isolated_dynamics",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "layer": "local Weyl dynamical-law candidates (8 terrains, both sheets)",
        "finite_map": "WeylLawStep: (rho_s in D(C^2), candidate X, dt) -> rho_s(t+dt)",
        "domain": "single-site Weyl density rho_L/rho_R in D(C^2)",
        "codomain_or_output": "evolved rho_s(t) + Bloch/purity/entropy readouts",
        "root_constraints": {"F01": "dim(H)=2, finite steps/seeds",
                             "N01": "every law has a noncommuting [.,rho] term"},
        "native_scale": {"dt": dt, "n_steps": n_steps, "n_seeds": n_seeds},
        "dynamic_step": True,
        "law_signatures": law_sig,
        "entropy_readouts": {n: {"final_entropy_nats": law_sig[n]["final_entropy"],
                                 "entropy_production": law_sig[n]["entropy_production"],
                                 "max_qubit_entropy_ln2": math.log(2)} for n in LAWS},
        "negative_controls_pass": control_pass,
        "min_pairwise_distance": min_pair,
        "pairwise_distance": pair,
        "load_bearing_sympy": sym,
        "hard_constraints": {"max_trace_err": cmax_trace, "min_eigenvalue": cmin_eig},
        "verdicts": verdicts,
        "all_pass": all(verdicts.values()),
        "blocked_consumers": ["stacking", "order_tests", "Xi", "Phi0", "Axis0", "flux", "FEP", "physics"],
        "tool_manifest": {
            "torch": {"used": True, "reason": "claim-bearing density evolution + Bloch/entropy readouts"},
            "sympy": {"used": True, "reason": "load-bearing symbolic depolarizing contraction rate (numeric must match)"},
            "numpy": {"used": True, "reason": "control/util only"},
        },
        "tool_integration_depth": "load_bearing",
    }

    import contract_emit
    contract_emit.attach(result, {"funnel_vs_pit_final_entropy":
        (law_sig["funnel"]["final_entropy"], law_sig["pit"]["final_entropy"])},
        "native dynamical scale (dt, n_steps, n_seeds); 8/16/32/64 qubit ladder is fake depth here, dropped.",
        torch_primary=float(torch.trace(seeds[0] @ seeds[0]).real))

    out_dir = Path(__file__).resolve().parent / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "weyl_terrain_eight_candidate_law_isolated_dynamics_results.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"all_pass={result['all_pass']}  ({sum(verdicts.values())}/{len(verdicts)} verdicts)")
    for k, v in verdicts.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print("\nlaw signatures (final state + entropy):")
    for n in LEFT + RIGHT:
        s = law_sig[n]
        print(f"  {n:8s} |r|={s['final_r_norm']:.3f} rz={s['final_rz']:+.3f} "
              f"rxy={s['final_rxy']:.3f} pur={s['final_purity']:.3f} "
              f"ang={s['signed_xy_angle']:+.2f} S={s['final_entropy']:.3f}nats")
    print(f"\nmin pairwise distance (8 distinct): {min_pair:.3f}")
    print(f"sympy depolarizing rate -4*lam: {sym['verified']}")
    print(f"result -> {out_path}")


if __name__ == "__main__":
    main()
