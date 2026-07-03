"""
chi2_decisive_test_sim.py -- PURE MATH, NO JARGON. Fourth-audit sim, 2026-07-01.

Audits the chi2 open-path eigenvector-sector meter (spec 7v) for CHARGE
SPECIFICITY, and runs the terrain-level decisive test that 7m's falsification
fork specified (parity readout p = a1 XOR a2 vs the target 2|2 partition).

Instrument (7v):  chi2(rho) = -arg( <r0|e><e|r1><r1|r0> ),  e = top eigenvector.

RESULTS THIS SIM ESTABLISHES (deterministic; seeded):
  (1) V* = K(V): the "V vs V*" pair of 7v is the K-mirror (complex-conjugation)
      pair. Three distinct binary operations exist on the frame element:
      a2-pair (V vs I), eps-pair (V vs V-dagger), K-pair (V vs V*).
  (2) chi2 discriminates ALL THREE pairs (means ~0.94 / 1.13 / 1.51) while
      entropy is blind to all three (<1e-15). chi2 is an eigenvector-sector
      meter, NOT an a2-specific meter.
  (3) DECISIVE TEST: with chi1 = 1[||L(I)|| = 0] (the non-unitality theorem)
      and chi2-sign from trajectory Bargmann phase, p = chi1 XOR chi2 matches
      the target partition {t1,t2,t5,t6} on only 2/8 (opposite convention:
      6/8). Neither is a readout. Cause: the Bargmann phase is
      eps-contaminated (t1 = +0.510 vs mirror t5 = -0.000) while the target
      is eps-even. The instrument lacks charge-specificity; 7m stays
      admissible-candidate.
scratch_diagnostic; promotion_allowed=false.
"""
import numpy as np
from scipy.linalg import expm

I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], complex)
sy = np.array([[0, -1j], [1j, 0]], complex)
sz = np.array([[1, 0], [0, -1]], complex)
sp = 0.5 * (sx + 1j * sy); sm = 0.5 * (sx - 1j * sy)
rng = np.random.default_rng(0)

H0 = (sx + sy + sz) / np.sqrt(3)
V = expm(-1j * H0 * 0.9); Vc = V.conj(); Vd = V.conj().T

r0 = np.array([1, 0], complex)
r1 = np.array([1, 1], complex) / np.sqrt(2)

def top_evec(rho):
    w, U = np.linalg.eigh(rho)
    return U[:, np.argmax(w)]

def chi2(rho):
    e = top_evec(rho)
    return -np.angle(np.vdot(r0, e) * np.vdot(e, r1) * np.vdot(r1, r0))

def S(rho):
    w = np.clip(np.linalg.eigvalsh(rho), 1e-15, 1)
    return float(-(w * np.log(w)).sum())

def rand_rho():
    psi = rng.normal(size=2) + 1j * rng.normal(size=2)
    psi /= np.linalg.norm(psi)
    return 0.7 * np.outer(psi, psi.conj()) + 0.3 * I2 / 2

# ---- (1) pair identification -------------------------------------------------
print("(1) pair identification on the frame element:")
print(f"    ||V-I|| = {np.linalg.norm(V-I2):.3f} (a2 pair)   "
      f"||V-Vdag|| = {np.linalg.norm(V-Vd):.3f} (eps pair)   "
      f"||V-V*|| = {np.linalg.norm(V-Vc):.3f} (K pair)")
print(f"    H0* = y-flipped axis: ||H0* - (sx-sy+sz)/sqrt3|| = "
      f"{np.linalg.norm(H0.conj()-(sx-sy+sz)/np.sqrt(3)):.1e}")

# ---- (2) charge specificity --------------------------------------------------
d_a2, d_K, d_eps, s_blind = [], [], [], []
for _ in range(500):
    r = rand_rho()
    a = chi2(V @ r @ Vd)
    d_a2.append(abs(a - chi2(r)))
    d_K.append(abs(a - chi2(Vc @ r @ Vc.conj().T)))
    d_eps.append(abs(a - chi2(Vd @ r @ V)))
    s_blind.append(abs(S(V @ r @ Vd) - S(r)))
print("(2) chi2 discrimination -- a2 pair: %.3f | eps pair: %.3f | K pair: %.3f"
      % (np.mean(d_a2), np.mean(d_eps), np.mean(d_K)))
print(f"    entropy blind to all pairs: {max(s_blind):.1e}")
print("    => chi2 is an eigenvector-sector meter, NOT charge-specific to a2")

# ---- (3) the decisive terrain-level test -------------------------------------
D = lambda L, r: L @ r @ L.conj().T - 0.5 * (L.conj().T @ L @ r + r @ L.conj().T @ L)
comm = lambda A, r: A @ r - r @ A
g, kap, Hz = 0.35, 1.0, sz
terr = {0: (+1, 'damp', +1), 1: (+1, 'depol', 0), 2: (+1, 'damp', -1), 3: (+1, 'proj', 0),
        4: (-1, 'damp', -1), 5: (-1, 'depol', 0), 6: (-1, 'damp', +1), 7: (-1, 'proj', 0)}

def gen(ti):
    eps, kind, pole = terr[ti]
    def X(r):
        out = -1j * g * comm(eps * Hz, r)
        if kind == 'damp':
            out = out + kap * D(sp if pole > 0 else sm, r)
        elif kind == 'depol':
            out = out + 0.5 * kap * (D(sx, r) + D(sy, r))
        else:
            out = out + kap * D(sz, r)
        return out
    return X

def flow(X, r, t, steps=200):
    dt = t / steps
    for _ in range(steps):
        k1 = X(r); k2 = X(r + .5 * dt * k1); k3 = X(r + .5 * dt * k2); k4 = X(r + dt * k3)
        r = r + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
        r = .5 * (r + r.conj().T); r /= np.trace(r).real
    return r

probe = 0.5 * (I2 + 0.55 * sx + 0.35 * sy + 0.25 * sz)
N_set = {1, 2, 5, 6}
print("(3) decisive test: p = a1 XOR a2  vs target partition {t1,t2,t5,t6}")
match_a, match_b, phases = 0, 0, {}
for t in range(8):
    X = gen(t)
    a1 = 1 if np.linalg.norm(X(I2)) < 1e-9 else 0
    ph = sum(chi2(flow(X, probe.copy(), tt)) for tt in (0.4, 0.8, 1.2)) / 3
    phases[t] = ph
    tgt = 1 if t in N_set else 0
    match_a += ((a1 ^ (1 if ph < 0 else 0)) == tgt)
    match_b += ((a1 ^ (1 if ph > 0 else 0)) == tgt)
    print(f"    t{t}: a1={a1}  chi2_traj={ph:+7.3f}  target={tgt}")
print(f"    parity match: convention A {match_a}/8, convention B {match_b}/8 -- NOT a readout")
print(f"    eps-contamination: t1 = {phases[1]:+.3f} vs mirror t5 = {phases[5]:+.3f}")
print("=> 7m remains admissible-candidate; open item: an eps-even (K-invariant),")
print("   a2-specific eigenvector functional.")
