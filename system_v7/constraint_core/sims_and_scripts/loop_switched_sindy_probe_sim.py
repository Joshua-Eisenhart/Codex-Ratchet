#!/usr/bin/env python3
"""loop_switched_sindy_probe

Follow-up to loop_unique_computing_dynamics_probe_sim.py after the global
loop-level degree-2 SINDy instrument proved invalid for a switched 4-stage
cycle. This probe uses known stage boundaries: fit one SINDy model per
continuous GKSL terrain-flow segment, then treat a loop as the ordered tuple
of its four segment models.

Each segment model has:
  - load-bearing PySINDy coefficients for the autonomous GKSL flow segment;
  - a measured affine Bloch-map for the discrete operator channel, used only
    for localization controls.

scratch_diagnostic; promotion_allowed=false. Honest verdict mixes exit 0.
"""
import json
import sys
import warnings
from itertools import combinations, permutations
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
N_STEPS = 220
CYCLES = 3
N_PROBES = 9
RADIUS = 0.62
Q = 1.0 - np.exp(-1.0)
TH = np.pi / 4
R2_GATE = 0.90

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


def terrain_rhs(ti, erased=False):
    if erased:
        return lambda r: np.zeros_like(r)
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


def op(name, erased=False):
    if erased:
        return lambda r: r.copy()
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


def normalize_rho(r):
    r = 0.5 * (r + r.conj().T)
    return r / np.trace(r).real


def rk4_step(X, r, dt):
    k1 = X(r)
    k2 = X(r + 0.5 * dt * k1)
    k3 = X(r + 0.5 * dt * k2)
    k4 = X(r + dt * k3)
    return normalize_rho(r + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4))


def flow_trajectory(X, r):
    dt = T_FLOW / N_STEPS
    pts = [bloch(r)]
    for _ in range(N_STEPS):
        r = rk4_step(X, r, dt)
        pts.append(bloch(r))
    return r, np.asarray(pts), dt


def probe_set(rng, n=N_PROBES):
    probes = []
    for _ in range(n):
        p = rng.normal(size=3)
        probes.append(RADIUS * p / np.linalg.norm(p))
    return probes


def load_and_validate_sources():
    join = json.loads(JOIN_PATH.read_text())
    source_rows = json.loads(SOURCE_PATH.read_text())
    if join.get("blocked"):
        raise ValueError("stage_token_join is blocked")
    if len(join.get("stage_join", [])) != 16:
        raise ValueError("stage_token_join must contain 16 rows")
    terrain_by_name = {row["terrain_name"]: row["terrain_index"] for row in join["terrain_index_map"]}
    join_by_slot = {row["source_slot_id"]: row for row in join["stage_join"]}
    enriched = []
    for src in source_rows:
        joined = join_by_slot.get(src["slot_id"])
        if joined is None:
            raise ValueError(f"{src['slot_id']} missing from stage_token_join")
        for field in ("terrain", "canonical_token", "axis6_sign", "igt_quadrant"):
            if src[field] != joined[field]:
                raise ValueError(f"{src['slot_id']} {field} mismatch")
        if src["canonical_operator"] != joined["operator"]:
            raise ValueError(f"{src['slot_id']} operator mismatch")
        row = dict(src)
        row["terrain_index"] = terrain_by_name[row["terrain"]]
        enriched.append(row)
    loops = {}
    for row in enriched:
        label = LOOP_LABELS[(row["engine"], row["loop"])]
        loops.setdefault(label, []).append(row)
    for label, rows in loops.items():
        rows.sort(key=lambda r: r["step"])
        if len(rows) != 4:
            raise ValueError(f"{label} has {len(rows)} segments, expected 4")
    return loops


def collect_segment_data(slots, probes, operator_erased=False, terrain_erased=False):
    segments = [{"flow_trajs": [], "op_in": [], "op_out": []} for _ in range(4)]
    for probe in probes:
        r = dm(probe)
        for _ in range(CYCLES):
            for pos, slot in enumerate(slots):
                X = terrain_rhs(slot["terrain_index"], erased=terrain_erased)
                O = op(slot["canonical_operator"], erased=operator_erased)
                if slot["axis6_sign"] == "up":
                    before = bloch(r)
                    r = normalize_rho(O(r.copy()))
                    after = bloch(r)
                    segments[pos]["op_in"].append(before)
                    segments[pos]["op_out"].append(after)
                    r, traj, _ = flow_trajectory(X, r)
                    segments[pos]["flow_trajs"].append(traj)
                elif slot["axis6_sign"] == "down":
                    r, traj, _ = flow_trajectory(X, r)
                    segments[pos]["flow_trajs"].append(traj)
                    before = bloch(r)
                    r = normalize_rho(O(r.copy()))
                    after = bloch(r)
                    segments[pos]["op_in"].append(before)
                    segments[pos]["op_out"].append(after)
                else:
                    raise ValueError(f"bad axis6_sign {slot['axis6_sign']!r}")
    return segments


def fit_sindy(train_trajs, test_trajs, suppress_sparse_warning=False):
    import pysindy as ps

    dt = T_FLOW / N_STEPS
    model = ps.SINDy(
        feature_library=ps.PolynomialLibrary(degree=2),
        optimizer=ps.STLSQ(threshold=0.02),
    )
    if suppress_sparse_warning:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Sparsity parameter is too big.*", category=UserWarning)
            model.fit([np.asarray(t) for t in train_trajs], t=dt)
    else:
        model.fit([np.asarray(t) for t in train_trajs], t=dt)
    coeffs = np.asarray(model.coefficients())
    try:
        r2 = float(model.score([np.asarray(t) for t in test_trajs], t=dt))
    except Exception:
        r2 = float("nan")
    return coeffs, r2, int(np.count_nonzero(np.abs(coeffs) > 1e-12))


def fit_operator_affine(op_in, op_out):
    x = np.asarray(op_in, float)
    y = np.asarray(op_out, float)
    design = np.column_stack([x, np.ones(len(x))])
    coeff, *_ = np.linalg.lstsq(design, y, rcond=None)
    pred = design @ coeff
    rmse = float(np.sqrt(np.mean((pred - y) ** 2)))
    return coeff.T, rmse


def fit_loop_signature(slots, train_probes, null_probes, test_probes, operator_erased=False, terrain_erased=False):
    train = collect_segment_data(slots, train_probes, operator_erased, terrain_erased)
    null = collect_segment_data(slots, null_probes, operator_erased, terrain_erased)
    test = collect_segment_data(slots, test_probes, operator_erased, terrain_erased)
    sig, null_sig, metrics = [], [], []
    for pos in range(4):
        coeff, r2, nz = fit_sindy(train[pos]["flow_trajs"], test[pos]["flow_trajs"], suppress_sparse_warning=terrain_erased)
        null_coeff, null_r2, null_nz = fit_sindy(null[pos]["flow_trajs"], test[pos]["flow_trajs"], suppress_sparse_warning=terrain_erased)
        op_coeff, op_rmse = fit_operator_affine(train[pos]["op_in"], train[pos]["op_out"])
        null_op_coeff, null_op_rmse = fit_operator_affine(null[pos]["op_in"], null[pos]["op_out"])
        sig.append({"flow": coeff, "operator": op_coeff, "full": np.concatenate([coeff.reshape(-1), op_coeff.reshape(-1)])})
        null_sig.append({"flow": null_coeff, "operator": null_op_coeff, "full": np.concatenate([null_coeff.reshape(-1), null_op_coeff.reshape(-1)])})
        metrics.append({
            "position": pos + 1,
            "heldout_r2": r2,
            "null_refit_heldout_r2": null_r2,
            "nonzero_terms": nz,
            "operator_affine_rmse": op_rmse,
            "null_operator_affine_rmse": null_op_rmse,
            "instrument_valid_at_segment": bool(np.isfinite(r2) and r2 >= R2_GATE),
            "null_refit_valid_at_segment": bool(np.isfinite(null_r2) and null_r2 >= R2_GATE),
            "null_nonzero_terms": null_nz,
        })
    return sig, null_sig, metrics


def segment_distance(a, b, channel="full"):
    va = a[channel].reshape(-1)
    vb = b[channel].reshape(-1)
    return float(np.linalg.norm(va - vb) / np.sqrt(va.size))


def ordered_distance(sig_a, sig_b, channel="full"):
    return float(sum(segment_distance(sig_a[i], sig_b[i], channel) for i in range(4)))


def unordered_distance(sig_a, sig_b, channel="full"):
    best = None
    best_perm = None
    for perm in permutations(range(4)):
        d = float(sum(segment_distance(sig_a[i], sig_b[perm[i]], channel) for i in range(4)))
        if best is None or d < best:
            best = d
            best_perm = perm
    return best, [p + 1 for p in best_perm]


def fit_all_signatures(loops, train_probes, null_probes, test_probes, operator_erased=False, terrain_erased=False):
    sigs, null_sigs, metrics = {}, {}, {}
    for label, slots in sorted(loops.items()):
        sig, null_sig, met = fit_loop_signature(
            slots,
            train_probes,
            null_probes,
            test_probes,
            operator_erased=operator_erased,
            terrain_erased=terrain_erased,
        )
        sigs[label] = sig
        null_sigs[label] = null_sig
        metrics[label] = met
    return sigs, null_sigs, metrics


def self_nulls(sigs, null_sigs, channel="full"):
    return {label: ordered_distance(sigs[label], null_sigs[label], channel) for label in sorted(sigs)}


def pair_table(sigs, null_band, null_band_unordered, unordered_null_sigs=None, channel="full"):
    rows = []
    for a, b in combinations(sorted(sigs), 2):
        ordered = ordered_distance(sigs[a], sigs[b], channel)
        unordered, perm = unordered_distance(sigs[a], sigs[b], channel)
        ordered_unique = bool(ordered > null_band)
        unordered_unique = bool(unordered > null_band_unordered)
        if ordered_unique and not unordered_unique:
            localization = "order-carried"
        elif ordered_unique:
            localization = "content-carried"
        else:
            localization = "degenerate"
        rows.append({
            "pair": f"{a} vs {b}",
            "a": a,
            "b": b,
            "ordered_distance": ordered,
            "unordered_best_match_distance": unordered,
            "unordered_best_match_positions_b": perm,
            "ordered_verdict": "unique" if ordered_unique else "degenerate",
            "unordered_verdict": "unique" if unordered_unique else "degenerate",
            "localization": localization,
        })
    return rows


def min_r2(metrics):
    vals = [m["heldout_r2"] for rows in metrics.values() for m in rows]
    return float(np.nanmin(vals))


def mean_r2(metrics):
    vals = [m["heldout_r2"] for rows in metrics.values() for m in rows]
    return float(np.nanmean(vals))


def main():
    rng = np.random.default_rng(SEED)
    loops = load_and_validate_sources()
    train_probes = probe_set(rng)
    null_probes = probe_set(rng)
    test_probes = probe_set(rng)

    sigs, null_sigs, metrics = fit_all_signatures(loops, train_probes, null_probes, test_probes)
    null = self_nulls(sigs, null_sigs, "flow")
    null_band = max(null.values())
    flow_null = self_nulls(sigs, null_sigs, "flow")
    full_null = self_nulls(sigs, null_sigs, "full")
    operator_null = self_nulls(sigs, null_sigs, "operator")

    # Position-blind self-null uses the same loop's two refits with best-match alignment.
    unordered_self = {
        label: unordered_distance(sigs[label], null_sigs[label], "flow")[0]
        for label in sorted(sigs)
    }
    unordered_null_band = max(unordered_self.values())
    rows = pair_table(sigs, null_band, unordered_null_band, channel="flow")

    op_erased_sigs, op_erased_null_sigs, op_erased_metrics = fit_all_signatures(
        loops, train_probes, null_probes, test_probes, operator_erased=True
    )
    op_erased_null = self_nulls(op_erased_sigs, op_erased_null_sigs, "flow")
    op_erased_band = max(op_erased_null.values())

    terrain_erased_sigs, terrain_erased_null_sigs, terrain_erased_metrics = fit_all_signatures(
        loops, train_probes, null_probes, test_probes, terrain_erased=True
    )
    terrain_erased_null = self_nulls(terrain_erased_sigs, terrain_erased_null_sigs, "operator")
    terrain_erased_band = max(terrain_erased_null.values())

    for row in rows:
        a, b = row["a"], row["b"]
        op_erased_d = ordered_distance(op_erased_sigs[a], op_erased_sigs[b], "flow")
        terrain_erased_d = ordered_distance(terrain_erased_sigs[a], terrain_erased_sigs[b], "operator")
        row["operator_erased_ordered_distance"] = op_erased_d
        row["operator_erased_verdict"] = "unique" if op_erased_d > op_erased_band else "degenerate"
        row["terrain_flow_erased_operator_distance"] = terrain_erased_d
        row["terrain_flow_erased_operator_verdict"] = "unique" if terrain_erased_d > terrain_erased_band else "degenerate"
        if row["ordered_verdict"] == "unique":
            carriers = []
            if row["operator_erased_verdict"] == "unique":
                carriers.append("terrain_flow/order")
            if row["terrain_flow_erased_operator_verdict"] == "unique":
                carriers.append("operator_channel")
            row["component_carrier"] = "+".join(carriers) if carriers else "requires_coupled_flow_operator_context"
        else:
            row["component_carrier"] = "not_unique_ordered"

    instrument_valid = bool(all(m["instrument_valid_at_segment"] for rows_ in metrics.values() for m in rows_))
    null_refits_valid = bool(all(m["null_refit_valid_at_segment"] for rows_ in metrics.values() for m in rows_))

    result = {
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "sim_id": "loop_switched_sindy_probe",
        "seed": SEED,
        "question": "Does switched per-stage SINDy recover a valid loop uniqueness instrument where the global loop fit was instrument-invalid?",
        "instrument_repair": "Known 4-stage boundaries; one SINDy fit per autonomous GKSL terrain-flow segment; primary loop signature is the ordered tuple of 4 SINDy flow-coefficient models.",
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
            "cycles": CYCLES,
            "axis6_up": "operator first, then terrain GKSL flow; SINDy fit sees only the flow segment",
            "axis6_down": "terrain GKSL flow first, then operator; SINDy fit sees only the flow segment",
        },
        "sindy": {
            "library": "PolynomialLibrary(degree=2)",
            "optimizer": "STLSQ(threshold=0.02)",
            "score": "held-out derivative R2 per segment; no forward integration",
            "r2_gate": R2_GATE,
            "min_segment_r2": min_r2(metrics),
            "mean_segment_r2": mean_r2(metrics),
            "instrument_valid_all_segments": instrument_valid,
            "null_refits_valid_all_segments": null_refits_valid,
        },
        "per_segment_metrics": metrics,
        "self_null": {
            "ordered_flow_primary": null,
            "ordered_flow_primary_band_max": null_band,
            "unordered_flow_primary": unordered_self,
            "unordered_flow_primary_band_max": unordered_null_band,
            "full_hybrid_flow_plus_operator": full_null,
            "operator_only": operator_null,
        },
        "pair_verdicts": rows,
        "erasure_controls": {
            "order_erasure": "unordered best-match assignment over the 4 segment models",
            "operator_erasure": {
                "description": "operators replaced by identity, then switched segment models refit",
                "self_null_band_max": op_erased_band,
                "min_segment_r2": min_r2(op_erased_metrics),
                "instrument_valid_all_segments": bool(all(m["instrument_valid_at_segment"] for rows_ in op_erased_metrics.values() for m in rows_)),
            },
            "terrain_flow_erasure": {
                "description": "terrain RHS replaced by zero flow; operator affine channel compared position-wise",
                "operator_self_null_band_max": terrain_erased_band,
                "min_zero_flow_sindy_r2_reported_not_gated": min_r2(terrain_erased_metrics),
            },
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
        "tool_manifest": {
            "pysindy": "load_bearing: per-segment sparse dynamics ID and held-out derivative R2 gate",
            "numpy": "supportive: density matrices, Bloch vectors, distances, seeded probes",
            "scipy.linalg.expm": "supportive: repo-standard Fi/Fe unitary operators",
            "json": "supportive: source/result serialization",
        },
        "tool_integration_depth": {
            "pysindy": "load_bearing",
            "numpy": "supportive",
            "scipy": "supportive",
            "json": "supportive",
        },
        "blocked_consumers": [
            "canonical loop admission",
            "Axis-level claims",
            "bridge/manifold claims",
            "source-table edits",
        ],
        "claim_ceiling": "scratch_diagnostic only; structural loop tokens read but no existing source/result files modified.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")

    print("LOOP SWITCHED-SINDY PROBE")
    print("classification: scratch_diagnostic")
    print("promotion_allowed: false")
    print(f"seed: {SEED}")
    print("instrument: known-boundary switched SINDy; one degree-2 STLSQ model per continuous GKSL segment")
    print(f"segment R2 gate: >= {R2_GATE:.2f}")
    print(f"min/mean segment held-out R2: {min_r2(metrics):.6f} / {mean_r2(metrics):.6f}")
    print(f"instrument_valid_all_segments: {instrument_valid}")
    print(f"ordered self-null band max: {null_band:.6f}")
    print(f"unordered self-null band max: {unordered_null_band:.6f}")
    print("")
    print("per-segment R2 table:")
    print("loop | p1 | p2 | p3 | p4")
    for label in sorted(metrics):
        vals = " | ".join(f"{m['heldout_r2']:.6f}" for m in metrics[label])
        print(f"{label} | {vals}")
    print("")
    print("6-pair ordered-vs-unordered verdict table:")
    print("pair | ordered | unordered | ordered verdict | unordered verdict | localization | op-erased | terrain-erased")
    for row in rows:
        print(
            f"{row['pair']} | {row['ordered_distance']:.6f} | "
            f"{row['unordered_best_match_distance']:.6f} | {row['ordered_verdict']} | "
            f"{row['unordered_verdict']} | {row['localization']} | "
            f"{row['operator_erased_verdict']}({row['operator_erased_ordered_distance']:.6f}) | "
            f"{row['terrain_flow_erased_operator_verdict']}({row['terrain_flow_erased_operator_distance']:.6f})"
        )
    print("")
    print(f"ALL_GATES: honest verdict mix written -> {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
