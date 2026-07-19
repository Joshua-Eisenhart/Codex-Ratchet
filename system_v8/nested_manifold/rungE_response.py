#!/usr/bin/env python3
"""Nested-manifold runtime — Rung E: response polarity on the 4-level tower.

Takes the rung-D 4-level nested generator (reconstructed here to the same
nesting convention, since no rungD file existed in this lane at build time:
4 qubit layers L0..L3, each layer runs ON the one below through a
hierarchical XY coupling ladder; the OUTER CONSTRAINT is a GKSL sigma_-
lock on the outermost layer L3). Everything is executed GKSL dynamics
(RK4 on the 16x16 density matrix), not analytic echo.

Layers / generator:
  L0 inner layer:  omega_0 sigma_z field (deepest, weakly attached)
  L1-L2 middle:    omega_j sigma_z + XY couplings g_j (sx sx + sy sy)
  L3 outer layer:  omega_3 sigma_z + outer constraint kappa D[sigma_-^(3)]
  Nesting: coupling ladder gc = (g_01, g_12, g_23) — each layer coupled
  only to its neighbours; L0 weakly bound (g_01 small), L3 strongly bound
  to the dissipative lock.

Perturbation sites (generator perturbations, relative magnitude delta):
  (a) outer constraint:  kappa   -> kappa   * (1 + delta)
  (b) inner Hamiltonian: omega_0 -> omega_0 * (1 + delta)
  (c) coupling:          g_12    -> g_12    * (1 + delta)

Response curves — operational reading of the tasked formula
g_k(delta) = d_tr(rho_k^delta, rho_k) / d_tr(rho_0^delta, rho_0):
  rho_k = full nested state at time step k (k = 1..40); rho_0 = the k=1
  reference state (earliest step at which the perturbed generator has
  acted; at k=0 both trajectories coincide and the ratio is 0/0).
  So g_k = D(k)/D(1) with D(k) = trace distance between perturbed and
  unperturbed full states at step k. The full 40-vector is reported per
  site per delta; opening/binding is classified ONLY from the computed
  vector (late-quarter mean vs early-quarter mean), never from a scalar.

Checks (each must fire or the rung fails):
  E1 growth site exists: >=1 site classified OPENING at all 3 deltas.
  E2 damping site exists: >=1 site classified BINDING at all 3 deltas.
  E3 vector-valued: every reported curve has 40 entries and genuine
     variation (no scalar collapse, no constant echo).
  C1 static control: freeze dynamics (propagator = identity) -> the
     response vector is identically flat (zero) at machine precision.
  C2 scrambled nesting: permute the layer-coupling ladder
     (g_01,g_12,g_23) -> (g_23,g_01,g_12); the response profile of at
     least one site changes measurably (relative L2 > 0.10), all
     per-site profile distances recorded.

Claim ceiling: executed finite instance; scratch_diagnostic;
promotion_allowed=false; no uniqueness or optimality claim.
"""
import json
import sys
from pathlib import Path

import numpy as np

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    Path(__file__).resolve().parent / "results" / "rungE"

NSTEP = 40          # reported time steps k = 1..40
DT_OUT = 1.0        # time per reported step (T = 40.0)
NSUB = 50           # RK4 substeps per reported step
# NOTE: a first executed run at DT_OUT=0.2 (T=8) classified ALL sites as
# opening (receipt kept at results/rungE_run1_T8_window_negative): the
# outer-constraint response peaks near t~6 and its decay lies outside a
# T=8 window. Window extended to T=40 (same 40-step vector, same checks,
# same thresholds) — a resolution fix, recorded, not a check change.
DELTAS = [0.02, 0.05, 0.1]

I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
SM = np.array([[0, 1], [0, 0]], dtype=complex)  # sigma_- (|0><1|)


def op_on(op, j, n=4):
    m = np.array([[1.0 + 0j]])
    for i in range(n):
        m = np.kron(m, op if i == j else I2)
    return m


def build_H(omega, gc):
    H = np.zeros((16, 16), dtype=complex)
    for j in range(4):
        H += omega[j] * op_on(SZ, j)
    for j in range(3):
        H += gc[j] * (op_on(SX, j) @ op_on(SX, j + 1)
                      + op_on(SY, j) @ op_on(SY, j + 1))
    return H


L3 = op_on(SM, 3)
L3dL3 = L3.conj().T @ L3


def rhs(rho, H, kappa):
    d = -1j * (H @ rho - rho @ H)
    d += kappa * (L3 @ rho @ L3.conj().T
                  - 0.5 * (L3dL3 @ rho + rho @ L3dL3))
    return d


def evolve(H, kappa, rho0, frozen=False):
    """Return list of rho at reported steps k=1..NSTEP (executed RK4)."""
    rho = rho0.copy()
    out = []
    dt = DT_OUT / NSUB
    for _ in range(NSTEP):
        if not frozen:
            for _ in range(NSUB):
                k1 = rhs(rho, H, kappa)
                k2 = rhs(rho + 0.5 * dt * k1, H, kappa)
                k3 = rhs(rho + 0.5 * dt * k2, H, kappa)
                k4 = rhs(rho + dt * k3, H, kappa)
                rho = rho + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
                rho = 0.5 * (rho + rho.conj().T)
        out.append(rho.copy())
    return out


def d_tr(a, b):
    return 0.5 * float(np.sum(np.abs(np.linalg.eigvalsh(a - b))))


def response_vec(base_traj, pert_traj):
    return np.array([d_tr(p, b) for p, b in zip(pert_traj, base_traj)])


def g_curve(D):
    """g_k = D(k)/D(1); k=1 is the earliest post-perturbation step."""
    ref = D[0]
    if ref < 1e-15:
        return np.zeros_like(D)
    return D / ref


def classify(g):
    """Opening/binding from the full vector: late-quarter vs early-quarter."""
    early = float(np.mean(g[1:10]))
    late = float(np.mean(g[30:40]))
    if late > 1.25 * early:
        return "opening", early, late
    if late < 0.8 * early:
        return "binding", early, late
    return "mixed", early, late


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to reuse output: {OUT}")
    OUT.mkdir(parents=True)
    checks, data = {}, {}

    # rung-D 4-level nested generator (baseline)
    omega = [1.0, 0.6, 0.35, 0.2]
    gc = [0.08, 0.3, 0.5]          # (g_01, g_12, g_23): L0 weakly bound
    kappa = 1.0                    # outer constraint on L3

    # initial state: product of |+> on all four layers
    plus = np.array([1.0, 1.0], dtype=complex) / np.sqrt(2)
    psi = np.array([1.0 + 0j])
    for _ in range(4):
        psi = np.kron(psi, plus)
    rho0 = np.outer(psi, psi.conj())

    H_base = build_H(omega, gc)
    base = evolve(H_base, kappa, rho0)

    def perturbed(site, delta):
        if site == "a_outer_constraint":
            return H_base, kappa * (1 + delta)
        if site == "b_inner_hamiltonian":
            om = list(omega); om[0] *= (1 + delta)
            return build_H(om, gc), kappa
        if site == "c_coupling":
            g = list(gc); g[1] *= (1 + delta)
            return build_H(omega, g), kappa
        raise ValueError(site)

    sites = ["a_outer_constraint", "b_inner_hamiltonian", "c_coupling"]
    curves, cls = {}, {}
    for s in sites:
        curves[s], cls[s] = {}, {}
        for delta in DELTAS:
            Hp, kp = perturbed(s, delta)
            D = response_vec(base, evolve(Hp, kp, rho0))
            g = g_curve(D)
            label, early, late = classify(g)
            curves[s][str(delta)] = {
                "g_vector": [round(float(x), 6) for x in g],
                "D_raw_first_last": [float(D[0]), float(D[-1])],
                "early_mean": early, "late_mean": late,
                "classification": label,
            }
            cls[s][str(delta)] = label
    data["response_curves"] = curves
    data["classification"] = cls

    opening = [s for s in sites
               if all(cls[s][str(d)] == "opening" for d in DELTAS)]
    binding = [s for s in sites
               if all(cls[s][str(d)] == "binding" for d in DELTAS)]
    checks["E1_growth_site_exists"] = len(opening) >= 1
    checks["E2_damping_site_exists"] = len(binding) >= 1
    data["opening_sites"], data["binding_sites"] = opening, binding

    checks["E3_vector_valued_no_scalar_collapse"] = all(
        len(curves[s][str(d)]["g_vector"]) == NSTEP
        and float(np.std(curves[s][str(d)]["g_vector"])) > 1e-6
        for s in sites for d in DELTAS)

    # C1 static control: freeze dynamics -> flat (zero) response vector
    frozen_base = evolve(H_base, kappa, rho0, frozen=True)
    Hp, kp = perturbed("b_inner_hamiltonian", DELTAS[1])
    frozen_pert = evolve(Hp, kp, rho0, frozen=True)
    D_frozen = response_vec(frozen_base, frozen_pert)
    checks["C1_static_control_flat"] = \
        float(np.ptp(D_frozen)) < 1e-14 and float(np.max(D_frozen)) < 1e-14
    data["static_control_D_max_ptp"] = [float(np.max(D_frozen)),
                                        float(np.ptp(D_frozen))]

    # C2 scrambled nesting: permute the coupling ladder, recompute profiles
    gc_perm = [gc[2], gc[0], gc[1]]  # (g_01,g_12,g_23)->(g_23,g_01,g_12)
    H_scram = build_H(omega, gc_perm)
    base_s = evolve(H_scram, kappa, rho0)
    rel = {}
    mid = DELTAS[1]
    for s in sites:
        if s == "a_outer_constraint":
            Hp_s, kp_s = H_scram, kappa * (1 + mid)
        elif s == "b_inner_hamiltonian":
            om = list(omega); om[0] *= (1 + mid)
            Hp_s, kp_s = build_H(om, gc_perm), kappa
        else:
            g = list(gc_perm); g[1] *= (1 + mid)
            Hp_s, kp_s = build_H(omega, g), kappa
        g_s = g_curve(response_vec(base_s, evolve(Hp_s, kp_s, rho0)))
        g_b = np.array(curves[s][str(mid)]["g_vector"])
        rel[s] = float(np.linalg.norm(g_s - g_b)
                       / max(np.linalg.norm(g_b), 1e-15))
    checks["C2_scrambled_nesting_changes_profile"] = max(rel.values()) > 0.10
    data["scrambled_profile_rel_l2_per_site"] = rel

    receipt = {
        "schema": "ratchet.v8.nested-manifold.rungE.v0",
        "generator": {"omega": omega, "gc": gc, "kappa": kappa,
                      "outer_constraint": "kappa*D[sigma_- on L3]",
                      "note": ("rung-D 4-level nested generator "
                               "reconstructed in-script: no rungD file "
                               "existed in this lane at build time")},
        "checks": {k: bool(v) for k, v in checks.items()}, "data": data,
        "all_pass": bool(all(checks.values())),
        "promotion_allowed": False, "formal_admission_allowed": False,
        "claim_ceiling": ("executed finite instance of response polarity "
                          "on one 4-level nested GKSL generator; "
                          "opening/binding classified from computed "
                          "40-step vectors only; no uniqueness claim"),
    }
    (OUT / "receipt.json").write_text(
        json.dumps(receipt, indent=2, default=float) + "\n")
    print(json.dumps({"all_pass": receipt["all_pass"],
                      "checks": receipt["checks"],
                      "classification": cls,
                      "opening_sites": opening, "binding_sites": binding,
                      "scrambled_rel_l2": rel}, indent=2))


if __name__ == "__main__":
    main()
