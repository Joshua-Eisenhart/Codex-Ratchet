#!/usr/bin/env python3
"""loop_unique_computing_dynamics_probe

Ask whether the four source-table engine loops, run as composed 4-stage
hybrid GKSL loops, compute uniquely at the trajectory-data level.

Method is intentionally close to terrain_unique_computing_dynamics_probe:
PySINDy degree-2 polynomial library, STLSQ(threshold=0.02), coefficient-space
distances against a same-loop disjoint-probe self-null, and held-out derivative
scores only. No SINDy forward integration is used.

scratch_diagnostic; promotion_allowed=false. The probe writes one JSON result
next to this script and exits 0 for any honest verdict mix.
"""
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy.linalg import expm


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
JOIN_PATH = HERE / "stage_token_join.json"
SOURCE_PATH = ROOT / "reference_docs/engine_math/source_schedule_tables/engine_16_source_stage_slots.json"
RESULT_PATH = Path(__file__).with_name(Path(__file__).stem + "_results.json")

SEED = 0
G = 0.35
KAP = 1.0
T_FLOW = 1.0
N_STEPS = 80
CYCLES = 3
N_PROBES_PER_SPLIT = 6
RADIUS = 0.62
Q = 1.0 - np.exp(-1.0)
TH = np.pi / 4

sx = np.array([[0, 1], [1, 0]], complex)
sy = np.array([[0, -1j], [1j, 0]], complex)
sz = np.array([[1, 0], [0, -1]], complex)
I2 = np.eye(2, dtype=complex)
sp = 0.5 * (sx + 1j * sy)
sm = 0.5 * (sx - 1j * sy)
H0 = (sx + sy + sz) / np.sqrt(3)

TERR = {
    0: (+1, "damp", +1),
    1: (+1, "depol", 0),
    2: (+1, "damp", -1),
    3: (+1, "proj", 0),
    4: (-1, "damp", -1),
    5: (-1, "depol", 0),
    6: (-1, "damp", +1),
    7: (-1, "proj", 0),
}

LOOP_LABELS = {
    ("Type1_left", "outer_deductive"): "Type1-outer-deductive",
    ("Type1_left", "inner_inductive"): "Type1-inner-inductive",
    ("Type2_right", "outer_inductive"): "Type2-outer-inductive",
    ("Type2_right", "inner_deductive"): "Type2-inner-deductive",
}

CANONICAL_TERRAIN_ORDER = {
    "Se-in": 0,
    "Ne-in": 1,
    "Ni-in": 2,
    "Si-in": 3,
    "Se-out": 0,
    "Ne-out": 1,
    "Ni-out": 2,
    "Si-out": 3,
}


def dm(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    if n >= 0.98:
        v = v / n * 0.98
    return 0.5 * (I2 + v[0] * sx + v[1] * sy + v[2] * sz)


def bloch(r):
    return np.array([float(np.trace(r @ s).real) for s in (sx, sy, sz)])


def dop(L, r):
    return L @ r @ L.conj().T - 0.5 * (L.conj().T @ L @ r + r @ L.conj().T @ L)


def terrain_rhs(ti):
    eps, kind, pole = TERR[ti]
    H = eps * H0

    def X(r):
        out = -1j * G * (H @ r - r @ H)
        if kind == "damp":
            out = out + KAP * dop(sp if pole > 0 else sm, r)
        elif kind == "depol":
            out = out + 0.5 * KAP * (dop(sx, r) + dop(sy, r))
        elif kind == "proj":
            out = out + KAP * dop(sz, r)
        else:
            raise ValueError(f"unknown terrain kind {kind!r}")
        return out

    return X


def op(name):
    P0 = 0.5 * (I2 + sz)
    P1 = 0.5 * (I2 - sz)
    Qp = 0.5 * (I2 + sx)
    Qm = 0.5 * (I2 - sx)
    if name == "Ti":
        return lambda r: (1 - Q) * r + Q * (P0 @ r @ P0 + P1 @ r @ P1)
    if name == "Te":
        return lambda r: (1 - Q) * r + Q * (Qp @ r @ Qp + Qm @ r @ Qm)
    if name == "Fi":
        U = expm(-1j * TH / 2 * sx)
        return lambda r: U @ r @ U.conj().T
    if name == "Fe":
        U = expm(-1j * TH / 2 * sz)
        return lambda r: U @ r @ U.conj().T
    raise ValueError(f"unknown operator {name!r}")


def rk4_step(X, r, dt):
    k1 = X(r)
    k2 = X(r + 0.5 * dt * k1)
    k3 = X(r + 0.5 * dt * k2)
    k4 = X(r + dt * k3)
    r = r + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
    r = 0.5 * (r + r.conj().T)
    return r / np.trace(r).real


def normalize_rho(r):
    r = 0.5 * (r + r.conj().T)
    return r / np.trace(r).real


def flow_stage(X, r, dt, pts):
    for _ in range(N_STEPS):
        r = rk4_step(X, r, dt)
        pts.append(bloch(r))
    return r


def apply_stage(slot, r, dt, pts):
    X = terrain_rhs(slot["terrain_index"])
    O = op(slot["canonical_operator"])
    if slot["axis6_sign"] == "up":
        r = normalize_rho(O(r.copy()))
        pts.append(bloch(r))
        r = flow_stage(X, r, dt, pts)
    elif slot["axis6_sign"] == "down":
        r = flow_stage(X, r, dt, pts)
        r = normalize_rho(O(r.copy()))
        pts.append(bloch(r))
    else:
        raise ValueError(f"bad axis6_sign {slot['axis6_sign']!r}")
    return r


def loop_trajectory(slots, probe, cycles=CYCLES):
    dt = T_FLOW / N_STEPS
    r = dm(probe)
    pts = [bloch(r)]
    for _ in range(cycles):
        for slot in slots:
            r = apply_stage(slot, r, dt, pts)
    return np.asarray(pts), dt


def probe_set(rng, n=N_PROBES_PER_SPLIT):
    probes = []
    for _ in range(n):
        p = rng.normal(size=3)
        probes.append(RADIUS * p / np.linalg.norm(p))
    return probes


def sindy_fit(train_trajs, test_trajs, dt):
    import pysindy as ps

    model = ps.SINDy(
        feature_library=ps.PolynomialLibrary(degree=2),
        optimizer=ps.STLSQ(threshold=0.02),
    )
    model.fit([np.asarray(t) for t in train_trajs], t=dt)
    coeffs = np.asarray(model.coefficients())
    nonzero_terms = int(np.count_nonzero(np.abs(coeffs) > 1e-12))
    try:
        score = float(model.score([np.asarray(t) for t in test_trajs], t=dt))
    except Exception:
        score = float("nan")
    return {
        "coefficients": coeffs,
        "heldout_derivative_r2": score,
        "nonzero_terms": nonzero_terms,
    }


def coeff_distance(ca, cb):
    return float(np.linalg.norm(ca - cb) / np.sqrt(ca.size))


def load_and_validate_sources():
    join = json.loads(JOIN_PATH.read_text())
    source_rows = json.loads(SOURCE_PATH.read_text())
    if join.get("blocked"):
        raise ValueError("stage_token_join is blocked")
    if len(join.get("stage_join", [])) != 16:
        raise ValueError("stage_token_join must contain 16 stage_join rows")
    terrain_by_name = {row["terrain_name"]: row["terrain_index"] for row in join["terrain_index_map"]}
    by_slot = {row["source_slot_id"]: row for row in join["stage_join"]}
    enriched = []
    for src in source_rows:
        joined = by_slot.get(src["slot_id"])
        if not joined:
            raise ValueError(f"source slot {src['slot_id']} missing from stage_token_join")
        for field in ("terrain", "canonical_token", "axis6_sign", "igt_quadrant"):
            if src[field] != joined[field]:
                raise ValueError(f"{src['slot_id']} {field} mismatch between source table and join")
        if src["canonical_operator"] != joined["operator"]:
            raise ValueError(f"{src['slot_id']} operator mismatch between source table and join")
        row = dict(src)
        row["terrain_index"] = terrain_by_name[src["terrain"]]
        enriched.append(row)
    loops = {}
    for row in enriched:
        label = LOOP_LABELS[(row["engine"], row["loop"])]
        loops.setdefault(label, []).append(row)
    for label, rows in loops.items():
        if len(rows) != 4:
            raise ValueError(f"{label} has {len(rows)} stages, expected 4")
        rows.sort(key=lambda r: r["step"])
    if sorted(loops) != sorted(LOOP_LABELS.values()):
        raise ValueError(f"found loops {sorted(loops)}, expected {sorted(LOOP_LABELS.values())}")
    return loops


def canonical_order(slots):
    return sorted(slots, key=lambda s: (CANONICAL_TERRAIN_ORDER[s["terrain"]], s["canonical_operator"], s["slot_id"]))


def fit_loop_family(loops, probes_train, probes_null, probes_test, shuffle_rng=None):
    train = {}
    null = {}
    test = {}
    dt_seen = None
    for label, slots in loops.items():
        train[label] = []
        null[label] = []
        test[label] = []
        for bucket, probes in ((train[label], probes_train), (null[label], probes_null), (test[label], probes_test)):
            for probe in probes:
                traj, dt = loop_trajectory(slots, probe)
                dt_seen = dt if dt_seen is None else dt_seen
                bucket.append(traj)
        if shuffle_rng is not None:
            train[label] = [traj[shuffle_rng.permutation(len(traj))] for traj in train[label]]
    fits = {
        label: sindy_fit(train[label], test[label], dt_seen)
        for label in sorted(loops)
    }
    null_fits = {
        label: sindy_fit(null[label], test[label], dt_seen)
        for label in sorted(loops)
    }
    return fits, null_fits, dt_seen


def pair_results(fits, null_fits, null_max):
    rows = []
    for a, b in combinations(sorted(fits), 2):
        d = coeff_distance(fits[a]["coefficients"], fits[b]["coefficients"])
        rows.append({
            "pair": f"{a} vs {b}",
            "a": a,
            "b": b,
            "coefficient_distance": d,
            "exceeds_self_null_band": bool(d > null_max),
        })
    return rows


def summarize_fits(fits):
    return {
        label: {
            "heldout_derivative_r2": fits[label]["heldout_derivative_r2"],
            "nonzero_terms": fits[label]["nonzero_terms"],
        }
        for label in sorted(fits)
    }


def finite_mean(xs):
    vals = [x for x in xs if np.isfinite(x)]
    return float(np.mean(vals)) if vals else float("nan")


def main():
    rng = np.random.default_rng(SEED)
    loops = load_and_validate_sources()
    loops_canonical = {label: canonical_order(slots) for label, slots in loops.items()}
    probes_train = probe_set(rng)
    probes_null = probe_set(rng)
    probes_test = probe_set(rng)

    fits, null_fits, dt = fit_loop_family(loops, probes_train, probes_null, probes_test)
    self_null = {
        label: coeff_distance(fits[label]["coefficients"], null_fits[label]["coefficients"])
        for label in sorted(fits)
    }
    null_max = max(self_null.values())
    original_pairs = pair_results(fits, null_fits, null_max)

    order_fits, order_null_fits, _ = fit_loop_family(loops_canonical, probes_train, probes_null, probes_test)
    order_self_null = {
        label: coeff_distance(order_fits[label]["coefficients"], order_null_fits[label]["coefficients"])
        for label in sorted(order_fits)
    }
    order_null_max = max(order_self_null.values())
    order_pairs = pair_results(order_fits, order_null_fits, order_null_max)
    order_by_pair = {row["pair"]: row for row in order_pairs}

    shuffled_fits, _, _ = fit_loop_family(
        loops,
        probes_train,
        probes_null,
        probes_test,
        shuffle_rng=np.random.default_rng(SEED + 1000),
    )
    real_score_mean = finite_mean([fits[label]["heldout_derivative_r2"] for label in sorted(fits)])
    shuffled_score_mean = finite_mean([shuffled_fits[label]["heldout_derivative_r2"] for label in sorted(shuffled_fits)])
    shuffled_degrades_fits = bool(np.isfinite(real_score_mean) and np.isfinite(shuffled_score_mean) and real_score_mean > shuffled_score_mean)

    original_nontrivial = {
        label: bool(fits[label]["nonzero_terms"] > 0)
        for label in sorted(fits)
    }
    all_nontrivial = bool(all(original_nontrivial.values()))

    verdict_rows = []
    for row in original_pairs:
        order_row = order_by_pair[row["pair"]]
        original_unique = bool(row["exceeds_self_null_band"] and all_nontrivial)
        order_unique = bool(order_row["exceeds_self_null_band"])
        if not original_unique:
            verdict = "degenerate"
            locus = "not_unique_against_self_null"
            next_probe = (
                "Split this pair into a switched-SINDy probe with explicit stage-boundary indicators, "
                "then run operator-only and terrain-only erasures to localize the collapse."
            )
        elif not order_unique:
            verdict = "order-carried"
            locus = "loop_schedule_order"
            next_probe = "No degenerate-pair follow-up; next bounded check is a single-pair stage-swap ladder."
        else:
            verdict = "unique"
            locus = "stage_membership_or_operator_content_survives_fixed_order"
            next_probe = "No degenerate-pair follow-up; next bounded check is operator-erasure localization."
        verdict_rows.append({
            "pair": row["pair"],
            "distance": row["coefficient_distance"],
            "self_null_band_max": null_max,
            "order_erased_distance": order_row["coefficient_distance"],
            "order_erased_self_null_band_max": order_null_max,
            "order_erased_exceeds_self_null": order_unique,
            "verdict": verdict,
            "uniqueness_locus": locus,
            "next_bounded_probe": next_probe,
        })

    all_original_pairs_unique = bool(all(row["verdict"] in ("unique", "order-carried") for row in verdict_rows))
    any_order_carried = bool(any(row["verdict"] == "order-carried" for row in verdict_rows))
    any_degenerate = bool(any(row["verdict"] == "degenerate" for row in verdict_rows))

    result = {
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "sim_id": "loop_unique_computing_dynamics_probe",
        "seed": SEED,
        "scratch_diagnostic": True,
        "question": "Do the four 4-stage engine loops, composed in source-table schedule order on real GKSL dynamics, produce dynamically unique computations?",
        "precedent_reused": "terrain_unique_computing_dynamics_probe_sim.py / engine_dynamics_id_arbiter_sim.py: PySINDy PolynomialLibrary(degree=2), STLSQ(threshold=0.02), held-out derivative scoring only, no forward integration",
        "source_paths": {
            "stage_token_join": str(JOIN_PATH),
            "engine_16_source_stage_slots": str(SOURCE_PATH),
        },
        "engine_conventions": {
            "G": G,
            "KAP": KAP,
            "H0": "(sx+sy+sz)/sqrt(3)",
            "integrator": "RK4",
            "stage_flow_time": T_FLOW,
            "n_steps_per_stage": N_STEPS,
            "cycles_per_trajectory": CYCLES,
            "axis6_up": "operator first, then terrain GKSL flow",
            "axis6_down": "terrain GKSL flow first, then operator",
        },
        "loop_schedules": {
            label: [
                {
                    "slot_id": s["slot_id"],
                    "step": s["step"],
                    "terrain": s["terrain"],
                    "terrain_index": s["terrain_index"],
                    "canonical_operator": s["canonical_operator"],
                    "axis6_sign": s["axis6_sign"],
                    "canonical_token": s["canonical_token"],
                }
                for s in slots
            ]
            for label, slots in sorted(loops.items())
        },
        "sindy": {
            "library": "PolynomialLibrary(degree=2)",
            "optimizer": "STLSQ(threshold=0.02)",
            "score": "held-out derivative R2 via PySINDy model.score; no forward integration",
            "dt": dt,
            "train_probe_count": N_PROBES_PER_SPLIT,
            "self_null_probe_count": N_PROBES_PER_SPLIT,
            "heldout_probe_count": N_PROBES_PER_SPLIT,
        },
        "fit_summaries": summarize_fits(fits),
        "self_null_distances": self_null,
        "self_null_band_max": null_max,
        "original_pair_distances": original_pairs,
        "nontrivial_fit_gate": {
            "per_loop_nonzero_terms": original_nontrivial,
            "all_loops_nontrivial": all_nontrivial,
        },
        "shuffled_time_control": {
            "real_heldout_r2_mean": real_score_mean,
            "shuffled_time_heldout_r2_mean": shuffled_score_mean,
            "shuffled_time_degrades_fits": shuffled_degrades_fits,
            "per_loop_shuffled_fit_summaries": summarize_fits(shuffled_fits),
        },
        "order_erasure_control": {
            "fixed_canonical_order": "Se, Ne, Ni, Si within each engine side; stage membership/operators/signs retained",
            "self_null_distances": order_self_null,
            "self_null_band_max": order_null_max,
            "pair_distances": order_pairs,
        },
        "pair_verdicts": verdict_rows,
        "headline": {
            "all_original_pairs_unique_or_order_carried": all_original_pairs_unique,
            "any_order_carried": any_order_carried,
            "any_degenerate": any_degenerate,
            "all_fits_nontrivial": all_nontrivial,
            "shuffled_time_control_flips": shuffled_degrades_fits,
        },
        "tool_manifest": {
            "pysindy": "load_bearing: sparse dynamics ID and held-out derivative scoring decide coefficient distances",
            "numpy": "supportive: density matrices, Bloch vectors, coefficient distances, seeded probes",
            "scipy.linalg.expm": "supportive: repo-standard unitary operators Fi/Fe",
            "json": "supportive: source-table and result serialization",
        },
        "tool_integration_depth": {
            "pysindy": "load_bearing",
            "numpy": "supportive",
            "scipy": "supportive",
            "json": "supportive",
        },
        "blocked_consumers": [
            "canonical engine-loop admission",
            "Axis-level claims",
            "bridge/manifold claims",
            "source-table edits",
        ],
        "claim_ceiling": "scratch_diagnostic only; structural loop-token schedules were read but not promoted or modified.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")

    print("LOOP UNIQUE-COMPUTING DYNAMICS PROBE")
    print("classification: scratch_diagnostic")
    print("promotion_allowed: false")
    print(f"seed: {SEED}")
    print(f"loops: {', '.join(sorted(loops))}")
    print(f"trajectory: {CYCLES} cycles x 4 stages, RK4 n={N_STEPS}/stage, dt={dt:.6f}")
    print("SINDy: PolynomialLibrary(degree=2), STLSQ(threshold=0.02), held-out derivatives only; no forward integration")
    print(f"self-null band max: {null_max:.6f}")
    print(f"order-erasure self-null band max: {order_null_max:.6f}")
    nz_summary = ", ".join(f"{k}: {fits[k]['nonzero_terms']}" for k in sorted(fits))
    print(f"nonzero SINDy terms per loop: {{ {nz_summary} }}")
    print(f"shuffled-time control: real mean R2 {real_score_mean:.6f} vs shuffled {shuffled_score_mean:.6f}; flips={shuffled_degrades_fits}")
    print("")
    print("6-pair verdict table:")
    print("pair | distance | order-erased distance | verdict | locus")
    for row in verdict_rows:
        print(
            f"{row['pair']} | {row['distance']:.6f} | "
            f"{row['order_erased_distance']:.6f} | {row['verdict']} | {row['uniqueness_locus']}"
        )
    if any_degenerate:
        print("")
        print("next bounded probes for degenerate pairs:")
        for row in verdict_rows:
            if row["verdict"] == "degenerate":
                print(f"- {row['pair']}: {row['next_bounded_probe']}")
    else:
        print("")
        print("next bounded probe for degenerate pairs: none in this run")
    print("")
    print(f"ALL_GATES: honest verdict mix written -> {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
