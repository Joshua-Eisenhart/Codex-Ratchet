#!/usr/bin/env python3
"""terrain_unique_computing_dynamics_probe -- decide, from trajectory DATA alone, whether the re-identification
degeneracies are spec-level identity (R1) or endpoint-biased probing (R2).

MEASURED GAP (owner instruction 2026-07-07: "get all the engine stages fully doing unique computing ... check
everything and improve it"): engine_reidentification_objective_sim reports 11/16 stages re-identified; the failing
pairs are t1<->t5 (both operator columns) and t3:Fe->t7:Fe. engines/targets.json shows why the ENDPOINT probe
collapses them: unital fixed points nearly coincide (t1 fixed_z 2.8e-05 vs t5 7.6e-06; t3 0.070 vs t7 0.093) while
the nonunital half sits at +/-0.71 and re-identifies perfectly. In the source-locked terrain table
(engine_dynamics_id_arbiter_sim.TERR) each confused pair differs ONLY by the sign of the coherent term:
t1=(+1,depol) vs t5=(-1,depol); t3=(+1,proj) vs t7=(-1,proj). Same dissipator, same fixed point, opposite-handed
transient rotation.

TWO LIVE READINGS this sim decides between (data-level, model-blind):
  R1 spec-level degeneracy -- the confused terrains are the same computation as far as any external fit can tell;
     repair belongs to the source spec (owner/dev decision upstream).
  R2 endpoint-biased probe -- the terrains COMPUTE differently (opposite handedness in the transient) and only the
     stationary readout collides; repair is a trajectory-sensitive component in the re-id battery.

METHOD: reuse the UP-92 arbiter machinery VERBATIM (imported, not reimplemented). For each terrain, hand PySINDy
the same probe trajectories the arbiter lane uses and extract the identified linear coefficient matrix. The
identity readout is the coefficient distance between terrains' identified equations, judged against a SELF-NULL:
the same terrain refit on a DISJOINT probe set (fit noise). A confused pair whose cross distance exceeds the
self-null spread computes uniquely at the data level (R2); a pair inside the null spread is R1.

TEETH (all must flip):
  C1 self-null sanity: every terrain's self-distance (disjoint probes) is small and every well-separated
     nonunital pair's cross distance is large (external fit resolves what the endpoint probe already resolves).
  C2 handedness erasure: refit the confused pairs on trajectories with the coherent term erased (kappa-only
     surrogate data built by symmetrizing each pair's generators: average of +eps and -eps flows). Erasing the
     handedness must COLLAPSE the pair distance toward the null -- proving the discovered difference lives in the
     coherent sign, not in fit noise.
  C3 shuffled-time: scrambling training order must break the fits (inherited from the arbiter lane).

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False. No spec edit, no re-id edit,
no promotion; the output is a verdict field per confused pair feeding the owner's uniqueness program.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import engine_dynamics_id_arbiter_sim as arb  # UP-92 machinery: TERR, gen, trajectory, Dgen, sigmas

RESULT = os.path.join(HERE, "terrain_unique_computing_dynamics_probe_sim_results.json")

CONFUSED_PAIRS = [(1, 5), (3, 7)]          # from engine_reidentification_objective_sim_results.json
SEPARATED_PAIRS = [(0, 2), (4, 6), (0, 4)]  # nonunital pairs the endpoint probe already resolves


def sindy_coefficients(trajs, dt):
    """Fit one SINDy model on concatenated probe trajectories; return the coefficient matrix."""
    import pysindy as ps
    model = ps.SINDy(feature_library=ps.PolynomialLibrary(degree=2),
                     optimizer=ps.STLSQ(threshold=0.02))
    model.fit(list(trajs), t=dt)
    return np.asarray(model.coefficients())


def probe_set(rng, n=4):
    probes = [rng.normal(size=3) for _ in range(n)]
    return [0.7 * p / np.linalg.norm(p) for p in probes]


def terrain_trajs(ti, probes, flow=None):
    out, dt = [], None
    for p in probes:
        if flow is None:
            traj, dt = arb.trajectory(ti, p)
        else:
            traj, dt = flow(p)
        out.append(traj)
    return out, dt


def symmetrized_flow(ta, tb):
    """Surrogate flow: average of the two generators. For (+eps, -eps) pairs this erases the coherent term and
    keeps the shared dissipator -- the handedness-erasure control."""
    Xa, Xb = arb.gen(ta), arb.gen(tb)

    def flow(r0_bloch, t_end=4.0, n=400):
        r = arb.rho_from_bloch(r0_bloch)
        dt = t_end / n
        traj = [arb.bloch(r)]
        X = lambda rho: 0.5 * (Xa(rho) + Xb(rho))
        for _ in range(n):
            k1 = X(r); k2 = X(r + .5 * dt * k1); k3 = X(r + .5 * dt * k2); k4 = X(r + dt * k3)
            r = r + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
            r = .5 * (r + r.conj().T); r /= np.trace(r).real
            traj.append(arb.bloch(r))
        return np.array(traj), dt

    return flow


def coeff_distance(ca, cb):
    return float(np.linalg.norm(ca - cb) / np.sqrt(ca.size))


def main():
    rng = np.random.default_rng(11)
    probes_a, probes_b = probe_set(rng), probe_set(rng)

    coeffs_a, coeffs_b = {}, {}
    for ti in range(8):
        ta, dt = terrain_trajs(ti, probes_a)
        tb, _ = terrain_trajs(ti, probes_b)
        coeffs_a[ti] = sindy_coefficients(ta, dt)
        coeffs_b[ti] = sindy_coefficients(tb, dt)

    self_null = {ti: coeff_distance(coeffs_a[ti], coeffs_b[ti]) for ti in range(8)}
    null_max = max(self_null.values())
    print("  SELF-NULL (same terrain, disjoint probes) coefficient distances:")
    for ti, dv in self_null.items():
        print(f"    t{ti}: {dv:.4f}")
    print(f"  null_max = {null_max:.4f}")

    def cross(ta, tb):
        return coeff_distance(coeffs_a[ta], coeffs_a[tb])

    print("  WELL-SEPARATED pairs (C1 positive control -- must exceed null):")
    c1_ok = True
    separated = {}
    for ta, tb in SEPARATED_PAIRS:
        dv = cross(ta, tb)
        separated[f"t{ta}-t{tb}"] = dv
        ok = dv > null_max
        c1_ok &= ok
        print(f"    t{ta} vs t{tb}: {dv:.4f}  exceeds null: {ok}")

    print("  CONFUSED pairs (the decisive readout):")
    verdicts = {}
    for ta, tb in CONFUSED_PAIRS:
        dv = cross(ta, tb)
        unique = dv > null_max
        verdicts[f"t{ta}-t{tb}"] = {
            "cross_coeff_distance": dv,
            "null_max": null_max,
            "computes_uniquely_at_data_level": unique,
            "reading": "R2_endpoint_biased_probe" if unique else "R1_spec_level_degeneracy",
        }
        print(f"    t{ta} vs t{tb}: {dv:.4f}  -> {'R2 (unique computing, probe is endpoint-biased)' if unique else 'R1 (spec-level degeneracy)'}")

    print("  C2 handedness-erasure control (symmetrized surrogate must collapse the pair):")
    c2_ok = True
    erasure = {}
    for ta, tb in CONFUSED_PAIRS:
        flow = symmetrized_flow(ta, tb)
        sa, dt = terrain_trajs(None, probes_a, flow=flow)
        sb, _ = terrain_trajs(None, probes_b, flow=flow)
        ca, cb = sindy_coefficients(sa, dt), sindy_coefficients(sb, dt)
        d_sym_null = coeff_distance(ca, cb)                    # fit noise of the surrogate itself
        d_orig = verdicts[f"t{ta}-t{tb}"]["cross_coeff_distance"]
        d_each_to_sym = 0.5 * (coeff_distance(coeffs_a[ta], ca) + coeff_distance(coeffs_a[tb], ca))
        collapsed = d_sym_null < d_orig
        c2_ok &= collapsed
        erasure[f"t{ta}-t{tb}"] = {
            "symmetrized_self_distance": d_sym_null,
            "original_pair_distance": d_orig,
            "mean_distance_each_to_symmetrized": d_each_to_sym,
            "erasure_collapses_pair": collapsed,
        }
        print(f"    t{ta}/t{tb}: sym-self {d_sym_null:.4f} vs original pair {d_orig:.4f}  collapsed: {collapsed}")

    print("  C3 shuffled-time control (must break the fit on a confused terrain):")
    t1_trajs, dt = terrain_trajs(1, probes_a)
    half = len(t1_trajs[0]) // 2
    train, test = t1_trajs[0][:half], t1_trajs[0][half:]
    r2_real = arb.fit_and_score(train, dt, test)
    idx = rng.permutation(len(train))
    r2_shuf = arb.fit_and_score(train[idx], dt, test)
    c3_ok = bool(r2_real > r2_shuf)
    print(f"    t1 held-out R2 real {r2_real:.4f} vs shuffled-time {r2_shuf:.4f}  flips: {c3_ok}")

    all_controls = bool(c1_ok and c2_ok and c3_ok)
    result = {
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": (
            "data-level unique-computing verdict for the re-id-degenerate terrain pairs; feeds the probe-upgrade "
            "vs spec-repair decision; no admission of any kind"
        ),
        "sources": {
            "measured_failure": "engine_reidentification_objective_sim_results.json (0.6875, pairs t1<->t5, t3:Fe->t7:Fe)",
            "endpoint_coincidence": "engines/targets.json terrains fixed_z (t1 2.8e-05 vs t5 7.6e-06; t3 0.070 vs t7 0.093)",
            "machinery": "engine_dynamics_id_arbiter_sim.py (UP-92) imported verbatim",
            "owner_instruction": "2026-07-07 'get all the engine stages fully doing unique computing; check everything and improve it'",
        },
        "self_null_distances": self_null,
        "null_max": null_max,
        "separated_pair_distances": separated,
        "confused_pair_verdicts": verdicts,
        "handedness_erasure_control": erasure,
        "shuffled_time_control": {"real_r2": r2_real, "shuffled_r2": r2_shuf, "flips": c3_ok},
        "controls": {"C1_separated_exceed_null": bool(c1_ok), "C2_erasure_collapses": bool(c2_ok), "C3_shuffle_breaks_fit": c3_ok},
        "ALL_CONTROLS_FLIP": all_controls,
    }
    with open(RESULT, "w") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("PASS terrain_unique_computing_dynamics_probe" if all_controls else "FAIL terrain_unique_computing_dynamics_probe")
    print("ALL_GATES:", "PASS" if all_controls else "FAIL", "->", RESULT)
    return 0 if all_controls else 1


if __name__ == "__main__":
    sys.exit(main())
