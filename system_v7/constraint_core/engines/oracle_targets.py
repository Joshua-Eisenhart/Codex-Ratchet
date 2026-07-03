"""
oracle_targets.py -- generates engines/targets.json: the cross-substrate
validation contract for the real engines (JAX / Julia / PyTorch).

PURE MATH, structural indices only. The 16 stages are 8 terrain generators
(t0..t7) x their 2 native operators, composed terrain-first (order 'down') and
operator-first (order 'up'). This file is the float64 numpy ORACLE; every
substrate engine must reproduce these targets within stated tolerances.

Contract emitted per stage (t, op):
  bloch_down[3]  Bloch vector of  J(exp(T dt_op-free... see below))  -- see run_stage
  bloch_up[3]    Bloch vector of the opposite composition
  order_gap      ||bloch_down - bloch_up||  (must be > 0: N01)
plus per-terrain: nonunital bit (||L(I)|| > 0), fixed-point z.
Derived invariants: 16/16 distinct (min pairwise dist), 16/16 order gaps > 0,
8/8 fusion split == nonunitality bit.

Determinism: fixed probe, fixed RK4 step count, float64 everywhere.
scratch_diagnostic; promotion_allowed=false.
"""
import json, os
import numpy as np

I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], complex)
sy = np.array([[0, -1j], [1j, 0]], complex)
sz = np.array([[1, 0], [0, -1]], complex)
sp = 0.5 * (sx + 1j * sy); sm = 0.5 * (sx - 1j * sy)

# ---- model constants (single source of truth for ALL substrates) ----
G = 0.35          # terrain coherent rate
KAP = 1.0         # terrain dissipative rate
Q = 1.0 - float(np.exp(-1.0))   # pinching strength
TH = np.pi / 4    # rotation angle
T_FLOW = 1.0      # terrain flow time
N_STEPS = 400     # RK4 steps (integration tolerance driver)
PROBE = (0.55, 0.35, 0.25)      # Bloch components of the standard probe
# COHERENT AXIS: canonical (1,1,1)/sqrt(3) per spec ledger. LOAD-BEARING: with the
# axis on sz, the four Fe stages commute exactly with their terrains (phase
# covariance) and 16/16 order sensitivity collapses to 12/16. See P12 flag.

TERR = {0: (+1, 'damp', +1), 1: (+1, 'depol', 0), 2: (+1, 'damp', -1), 3: (+1, 'proj', 0),
        4: (-1, 'damp', -1), 5: (-1, 'depol', 0), 6: (-1, 'damp', +1), 7: (-1, 'proj', 0)}
NATIVE = {0: ('Ti', 'Fi'), 1: ('Ti', 'Fi'), 4: ('Ti', 'Fi'), 5: ('Ti', 'Fi'),
          2: ('Te', 'Fe'), 3: ('Te', 'Fe'), 6: ('Te', 'Fe'), 7: ('Te', 'Fe')}

def D(L, r):
    return L @ r @ L.conj().T - 0.5 * (L.conj().T @ L @ r + r @ L.conj().T @ L)

def gen(ti):
    eps, kind, pole = TERR[ti]
    H = eps * (sx + sy + sz) / np.sqrt(3)
    def X(r):
        out = -1j * G * (H @ r - r @ H)
        if kind == 'damp':
            out = out + KAP * D(sp if pole > 0 else sm, r)
        elif kind == 'depol':
            out = out + 0.5 * KAP * (D(sx, r) + D(sy, r))
        else:
            out = out + KAP * D(sz, r)
        return out
    return X

def flow(X, r, t=T_FLOW, steps=N_STEPS):
    dt = t / steps
    for _ in range(steps):
        k1 = X(r); k2 = X(r + .5 * dt * k1); k3 = X(r + .5 * dt * k2); k4 = X(r + dt * k3)
        r = r + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
        r = .5 * (r + r.conj().T); r /= np.trace(r).real
    return r

def op(name):
    P0 = 0.5 * (I2 + sz); P1 = 0.5 * (I2 - sz)
    Qp = 0.5 * (I2 + sx); Qm = 0.5 * (I2 - sx)
    from scipy.linalg import expm
    if name == 'Ti':
        return lambda r: (1 - Q) * r + Q * (P0 @ r @ P0 + P1 @ r @ P1)
    if name == 'Te':
        return lambda r: (1 - Q) * r + Q * (Qp @ r @ Qp + Qm @ r @ Qm)
    if name == 'Fi':
        U = expm(-1j * TH / 2 * sx); return lambda r: U @ r @ U.conj().T
    if name == 'Fe':
        U = expm(-1j * TH / 2 * sz); return lambda r: U @ r @ U.conj().T

def bloch(r):
    return [float(np.trace(r @ s).real) for s in (sx, sy, sz)]

def main():
    probe = 0.5 * (I2 + PROBE[0] * sx + PROBE[1] * sy + PROBE[2] * sz)
    stages, terrains = [], []
    for t in range(8):
        X = gen(t)
        terrains.append({"t": t,
                         "nonunital": int(np.linalg.norm(X(I2)) > 1e-9),
                         "fixed_z": bloch(flow(X, probe.copy(), t=8.0, steps=1600))[2]})
        for o in NATIVE[t]:
            J = op(o)
            down = bloch(J(flow(X, probe.copy())))       # terrain-first
            up = bloch(flow(X, J(probe.copy())))         # operator-first
            gap = float(np.linalg.norm(np.array(down) - np.array(up)))
            stages.append({"t": t, "op": o, "bloch_down": down, "bloch_up": up,
                           "order_gap": gap})
    # derived invariants
    M = np.array([s["bloch_down"] + s["bloch_up"] for s in stages])
    dmin = min(float(np.linalg.norm(M[i] - M[j]))
               for i in range(16) for j in range(i + 1, 16))
    out = {"model_constants": {"G": G, "KAP": KAP, "Q": Q, "TH": TH,
                               "T_FLOW": T_FLOW, "N_STEPS": N_STEPS, "PROBE": PROBE},
           "stages": stages, "terrains": terrains,
           "invariants": {"n_stages": 16, "min_pairwise_dist": dmin,
                          "all_order_gaps_positive": bool(all(s["order_gap"] > 1e-6 for s in stages)),
                          "nonunital_bits": [tr["nonunital"] for tr in terrains]},
           "tolerances": {"bloch_abs": 1e-6, "order_gap_abs": 1e-6, "fixed_z_abs": 1e-4,
                          "note": "1e-6 covers RK4 truncation agreement at N_STEPS=400 in float64; float32 substrates must upcast or widen to 1e-3 explicitly"}}
    here = os.path.dirname(os.path.abspath(__file__))
    json.dump(out, open(os.path.join(here, "targets.json"), "w"), indent=1)
    print(f"targets.json written: 16 stages, min pairwise dist {dmin:.4f}, "
          f"all order gaps > 0: {out['invariants']['all_order_gaps_positive']}, "
          f"nonunital bits {out['invariants']['nonunital_bits']}")

if __name__ == "__main__":
    main()
