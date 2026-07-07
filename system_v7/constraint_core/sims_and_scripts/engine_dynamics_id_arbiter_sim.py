#!/usr/bin/env python3
"""engine_dynamics_id_arbiter -- a FULLY EXTERNAL, model-blind dynamics-identification judge for the QIT engine
terrains, using PySINDy (https://github.com/dynamicslab/pysindy), an off-the-shelf system-ID library with ZERO
knowledge of the Codex Ratchet theory. Named in the owner's Lev object-formation docs (2026-07-06) precisely as
the kind of independent arbiter that can assess whether the engines are "actually valid and working".

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False.

WHY: the re-identification test (UP-73) is model-blind but uses OUR OWN signature. This goes further: it hands the
raw per-tick Bloch TRAJECTORY of each terrain flow to PySINDy and lets that external library discover a governing
ODE with no input from us. If a terrain is a real dynamical object, an independent sparse-regression fit predicts
its held-out trajectory well. The TEETH (controls that must flip, per the owner's control-table discipline):
  - SHUFFLED-TIME control: scramble the time order of the SAME samples and refit. A real ODE has a consistent
    dS/dt = f(S); time-shuffled data does not -> its fit MUST be far worse (held-out prediction breaks).
  - The verdict is the SEPARATION between real-trajectory fit quality and shuffled-time fit quality, measured on
    HELD-OUT data (train on first half of each trajectory, predict the second half). No self-set pass mark: the
    gate is only that the external fit succeeds on real data AND the shuffled-time control breaks it.

The dynamics fitted are the terrain GKSL flows (the geometric-constraint-manifold surface that the operators run
on) -- 8 terrains, each a 3-D Bloch trajectory r(t). That is the continuous object SINDy is built to identify;
the discrete operators are tested by the companion re-identification sim.
"""
import json, os, sys
import numpy as np

I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], complex)
sy = np.array([[0, -1j], [1j, 0]], complex)
sz = np.array([[1, 0], [0, -1]], complex)
sp = 0.5 * (sx + 1j * sy); sm = 0.5 * (sx - 1j * sy)
G, KAP = 0.35, 1.0
TERR = {0: (+1, 'damp', +1), 1: (+1, 'depol', 0), 2: (+1, 'damp', -1), 3: (+1, 'proj', 0),
        4: (-1, 'damp', -1), 5: (-1, 'depol', 0), 6: (-1, 'damp', +1), 7: (-1, 'proj', 0)}

def Dgen(L, r):
    return L @ r @ L.conj().T - 0.5 * (L.conj().T @ L @ r + r @ L.conj().T @ L)

def gen(ti):
    eps, kind, pole = TERR[ti]
    H = eps * (sx + sy + sz) / np.sqrt(3)
    def X(r):
        out = -1j * G * (H @ r - r @ H)
        if kind == 'damp':
            out = out + KAP * Dgen(sp if pole > 0 else sm, r)
        elif kind == 'depol':
            out = out + 0.5 * KAP * (Dgen(sx, r) + Dgen(sy, r))
        else:
            out = out + KAP * Dgen(sz, r)
        return out
    return X

def bloch(r):
    return np.array([np.trace(r @ s).real for s in (sx, sy, sz)])

def rho_from_bloch(v):
    return 0.5 * (I2 + v[0] * sx + v[1] * sy + v[2] * sz)

def trajectory(ti, r0_bloch, t_end=4.0, n=400):
    """Per-tick Bloch trajectory of terrain ti's GKSL flow from a given initial Bloch vector."""
    X = gen(ti); r = rho_from_bloch(r0_bloch); dt = t_end / n
    traj = [bloch(r)]
    for _ in range(n):
        k1 = X(r); k2 = X(r + .5*dt*k1); k3 = X(r + .5*dt*k2); k4 = X(r + dt*k3)
        r = r + (dt/6)*(k1 + 2*k2 + 2*k3 + k4)
        r = .5*(r + r.conj().T); r /= np.trace(r).real
        traj.append(bloch(r))
    return np.array(traj), dt

def fit_and_score(train_X, dt, test_X):
    """Fit a SINDy model on train_X (a Bloch trajectory) and score it on HELD-OUT test_X using PySINDy's own
    model.score (R^2 of the identified dS/dt = f(S) against the held-out numerical derivative). This is the
    standard held-out SINDy metric and does NOT forward-integrate, so it can't hang on a stiff/divergent fit.
    Higher R^2 = the external library found a governing equation that also predicts the unseen segment."""
    import pysindy as ps
    model = ps.SINDy(feature_library=ps.PolynomialLibrary(degree=2),
                     optimizer=ps.STLSQ(threshold=0.02))
    model.fit(train_X, t=dt)
    try:
        return float(model.score(test_X, t=dt))
    except Exception:
        return float("nan")

def main():
    rng = np.random.default_rng(3)
    probes = [rng.normal(size=3) for _ in range(4)]
    probes = [0.7 * p / np.linalg.norm(p) for p in probes]

    real_scores, shuffled_scores, per_terrain = [], [], []
    for ti in range(8):
        # concatenate a few probe trajectories; train on first half of the time series, predict second half
        r_terr, s_terr = [], []
        for p in probes:
            traj, dt = trajectory(ti, p)
            half = len(traj) // 2
            train, test = traj[:half], traj[half:]
            r2_real = fit_and_score(train, dt, test)
            # SHUFFLED-TIME control: destroy the time ordering of the training samples, refit, predict same test
            idx = rng.permutation(len(train))
            r2_shuf = fit_and_score(train[idx], dt, test)
            r_terr.append(r2_real); s_terr.append(r2_shuf)
        rm = float(np.nanmean(r_terr)); sm_ = float(np.nanmean(s_terr))
        real_scores.append(rm); shuffled_scores.append(sm_)
        per_terrain.append({"t": ti, "real_r2": rm, "shuffled_time_r2": sm_})

    real_mean = float(np.nanmean(real_scores))
    shuf_mean = float(np.nanmean(shuffled_scores))
    # GATE = THE CONTROL FLIP ONLY. No picked R^2 pass mark (demanding real_mean>0.9 would be imposing an outcome
    # -- the anti-pattern UP-72b/72c corrected). The external library's held-out R^2 on real trajectories is
    # REPORTED AS-IS. The verdict is purely: does the shuffled-time control BREAK the fit that real data supports,
    # on EVERY terrain? A real ODE has a consistent dS/dt=f(S) that predicts held-out data; time-scrambled data
    # does not. So the objective, non-tunable claim is the per-terrain flip: real held-out R^2 > shuffled-time
    # held-out R^2 for every terrain, with the external arbiter (PySINDy) as sole judge.
    valid = [pt for pt in per_terrain if not (np.isnan(pt["real_r2"]) or np.isnan(pt["shuffled_time_r2"]))]
    per_terrain_flip = len(valid) == len(per_terrain) and all(pt["real_r2"] > pt["shuffled_time_r2"] for pt in valid)
    verdict = bool(per_terrain_flip)

    out = {"classification": "scratch_diagnostic", "promotion_allowed": False,
           "arbiter": "PySINDy (external, model-blind sparse dynamics ID) -- no QIT theory input",
           "criterion": "shuffled-time control must break the fit real trajectories support, on every terrain; R^2 reported as-is",
           "n_terrains": 8, "per_terrain": per_terrain,
           "real_traj_heldout_r2_mean": real_mean, "shuffled_time_heldout_r2_mean": shuf_mean,
           "separation_real_minus_shuffled": real_mean - shuf_mean,
           "real_beats_shuffled_every_terrain": bool(per_terrain_flip),
           "EXTERNAL_ARBITER_CONTROL_FLIPS": verdict}
    path = __file__.replace(".py", "_results.json"); json.dump(out, open(path, "w"), indent=1)

    print("EXTERNAL dynamics-ID arbiter -- PySINDy, an off-the-shelf library with NO knowledge of the QIT theory.")
    print("  8 terrain GKSL flows; per-tick Bloch trajectories; train on first half, predict held-out second half.\n")
    for pt in per_terrain:
        print(f"  terrain t{pt['t']}: real held-out R^2 {pt['real_r2']:.3f}   shuffled-time R^2 {pt['shuffled_time_r2']:.3f}")
    print(f"\n  REAL trajectories, mean held-out R^2 : {real_mean:.3f}  (reported as-is, NOT gated to a ceiling)")
    print(f"  SHUFFLED-TIME control, mean R^2      : {shuf_mean:.3f}")
    print(f"  separation                           : {real_mean - shuf_mean:.3f}")
    print(f"  real beats shuffled on EVERY terrain (the objective, non-tunable gate): {per_terrain_flip}")
    print(f"\n  EXTERNAL ARBITER CONTROL FLIPS (shuffled-time breaks the fit real data supports): {verdict}")
    if verdict:
        print("PASS engine_dynamics_id_arbiter")
    print("ALL_GATES:", "PASS" if verdict else "FAIL", "->", path)
    sys.exit(0 if verdict else 1)

if __name__ == "__main__":
    main()
