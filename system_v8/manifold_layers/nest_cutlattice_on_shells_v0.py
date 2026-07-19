#!/usr/bin/env python3
"""Rung 3: nest the cut-lattice entropy-geometry on the marginal shell layer.

Tower so far: nest_L3_on_L2_v0 (2q) proved the two-layer nesting laws.
This rung adds the third qubit and nests the CUT LATTICE (ledger L8/L10)
on the shell layer (L3/L5): the three bipartitions A|BC, B|AC, C|AB each
carry an entropy-geometry that lives ON the corresponding marginal shell.

Nesting laws (computed, tol stated):
  M1 per-cut entropy IS inner geometry: S_X = h((1+r_X)/2) for every cut X
     of every sampled pure state (machine precision) — the whole cut-lattice
     entropy table is a function of the three inner radial coordinates.
  M2 metric nesting (2-parameter family): g_joint (Fubini-Study, 2x2) =
     radial pullback + fiber remainder; fiber PSD (>= -1e-9), nonzero,
     not the whole metric.
  M3 per-cut outer restriction: making C product collapses shell_C to
     {r_C=1} while shells A,B keep a continuum — cuts collapse
     independently (nesting is per-edge of the lattice, not global).
  M4 the nested layer CONSTRAINS the inner coordinates: the admissible
     entropy triples obey the triangle constraints |S_B-S_C| <= S_A <=
     S_B+S_C on all 500 seeded random pure states; the corner
     (S_A,S_B,S_C)=(1,0,0) is excluded (named exclusion witness) — the
     cut lattice is not a free product of shells.

Claim ceiling: second executed nesting rung (3q, exact + seeded sample);
scratch_diagnostic; promotion_allowed=false; upgrades no ledger row.
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    Path(__file__).resolve().parent / "results" / "nest_cutlattice_v0"
rng = np.random.default_rng(0)


def h(p):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return float(-(p * np.log2(p) + (1 - p) * np.log2(1 - p)))


def rho_of(v, keep):
    t = v.reshape(2, 2, 2)
    perm = list(keep) + [i for i in range(3) if i not in keep]
    m = np.transpose(t, perm).reshape(2 ** len(keep), -1)
    return m @ m.conj().T


def bloch_r(rho):
    return float(np.sqrt(max(0.0, 2 * float(np.trace(rho @ rho).real) - 1)))


def S_vn(rho):
    ev = np.linalg.eigvalsh(rho)
    ev = ev[ev > 1e-15]
    return float(-(ev * np.log2(ev)).sum())


def family(th, ph):
    v = np.zeros(8)
    v[0], v[6], v[5] = np.cos(th), np.sin(th) * np.cos(ph), \
        np.sin(th) * np.sin(ph)
    return v


def fs_metric(f, th, ph, d=1e-6):
    v = f(th, ph)
    g = np.zeros((2, 2))
    grads = []
    for i, (dt, dp) in enumerate(((d, 0), (0, d))):
        dv = (f(th + dt, ph + dp) - f(th - dt, ph - dp)) / (2 * d)
        grads.append(dv - (v @ dv) * v)
    for i in range(2):
        for j in range(2):
            g[i, j] = grads[i] @ grads[j]
    return g


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to reuse output: {OUT}")
    OUT.mkdir(parents=True)
    # M1 + M4 over 500 seeded random pure states (complex)
    m1_max_err, m4_ok, tri_margin_min = 0.0, True, 1e9
    for _ in range(500):
        v = rng.normal(size=8) + 1j * rng.normal(size=8)
        v /= np.linalg.norm(v)
        S, r = {}, {}
        for q in range(3):
            rq = rho_of(v, [q])
            S[q], r[q] = S_vn(rq), bloch_r(rq)
            m1_max_err = max(m1_max_err, abs(S[q] - h((1 + r[q]) / 2)))
        for a, b, c in itertools.permutations(range(3)):
            margin = S[b] + S[c] - S[a]
            tri_margin_min = min(tri_margin_min, margin)
            if margin < -1e-10:
                m4_ok = False
    # M2 on the 2-parameter family
    th, ph = 0.5, 0.4
    g_joint = fs_metric(family, th, ph)
    d = 1e-6
    J = np.zeros((3, 2))  # d r_q / d(theta, phi)
    for q in range(3):
        for i, (dt, dp) in enumerate(((d, 0), (0, d))):
            J[q, i] = (bloch_r(rho_of(family(th + dt, ph + dp), [q]))
                       - bloch_r(rho_of(family(th - dt, ph - dp), [q]))) \
                      / (2 * d)
    G_shell = np.diag([1.0 / max(1e-12,
                                 1 - bloch_r(rho_of(family(th, ph), [q])) ** 2)
                       for q in range(3)])
    g_radial = J.T @ G_shell @ J
    g_fiber = g_joint - g_radial
    fev = np.linalg.eigvalsh(g_fiber)
    # M3 restriction: product on C
    def fam_prodC(t, p):
        base = np.zeros(4)
        base[0], base[3] = np.cos(t), np.sin(t)
        return np.kron(base, np.array([np.cos(p), np.sin(p)]))
    shells_C = {round(bloch_r(rho_of(fam_prodC(t, p), [2])), 6)
                for t in np.linspace(0.05, 0.7, 8)
                for p in np.linspace(0.1, 1.2, 8)}
    shells_A = {round(bloch_r(rho_of(fam_prodC(t, p), [0])), 6)
                for t in np.linspace(0.05, 0.7, 8)
                for p in np.linspace(0.1, 1.2, 8)}
    checks = {
        "M1_cut_entropies_are_inner_geometry": m1_max_err < 1e-10,
        "M2_fiber_nonzero": float(np.linalg.norm(g_fiber)) > 1e-8,
        "M2_fiber_psd": bool(fev.min() > -1e-9),
        "M2_fiber_not_whole_metric":
            float(np.linalg.norm(g_fiber - g_joint)) > 1e-8,
        "M3_restricted_cut_collapses": shells_C == {1.0},
        "M3_other_cuts_keep_continuum": len(shells_A) > 5,
        "M4_triangle_constraints_hold": m4_ok,
        "M4_excluded_corner": "(S_A,S_B,S_C)=(1,0,0) violates S_A<=S_B+S_C",
    }
    receipt = {
        "schema": "ratchet.v8.nest-cutlattice-on-shells.v0",
        "predecessor": "nest_L3_on_L2_v0 (all 4 laws pass)",
        "checks": checks, "M1_max_error": m1_max_err,
        "M4_min_triangle_margin": tri_margin_min,
        "g_joint": g_joint.tolist(), "g_radial": g_radial.tolist(),
        "g_fiber_eigenvalues": fev.tolist(),
        "all_pass": all(v is True for k, v in checks.items()
                        if isinstance(v, bool)),
        "promotion_allowed": False, "formal_admission_allowed": False,
        "claim_ceiling": "second executed nesting rung (3q); upgrades no "
                         "ledger row; scratch_diagnostic",
    }
    (OUT / "receipt.json").write_text(
        json.dumps(receipt, indent=2, default=float) + "\n")
    print(json.dumps({"all_pass": receipt["all_pass"], "checks": checks,
                      "M1_max_error": m1_max_err,
                      "M4_min_margin": tri_margin_min}, indent=2,
                     default=float))


if __name__ == "__main__":
    main()
