#!/usr/bin/env python3
"""igt_quadrant_signed_feature_probe_sim

Signed-feature variant of igt_quadrant_loadbearing_probe_sim. Hypothesis: the
RMS-distance probe erases signed/coherent structure (precedent:
terrain_unique_computing_dynamics_probe, where re-id-degenerate stage pairs
were separated only by signed transient handedness features and a
handedness-erasure control collapsed them).

Feature vector per stage: the full signed Bloch trajectory concatenated across
the four probe states (raw signed time-series, no norm/RMS collapse) PLUS a
second channel of per-tick signed increments (deltas), which carry transient
handedness. Distance = Euclidean in that feature space. Score = silhouette of
the source-table igt_quadrant grouping.

Gates: 200-shuffle null (real >= 95th percentile) and a label-erasure control
that must stay in the null band. Additional localization control: recompute
with handedness erased (absolute value of the delta channel only); if the real
grouping's advantage collapses, the signal lives in the coherent sign.

scratch_diagnostic; promotion_allowed=false. Standalone, CWD-independent,
additive only. A decorative result is a valid diagnostic outcome; nonzero exit
is reserved for broken inputs or runtime errors.
"""
import json, sys
from pathlib import Path

import numpy as np
from scipy.linalg import expm


ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
JOIN_PATH = HERE / "stage_token_join.json"
SOURCE_PATH = ROOT / "reference_docs/engine_math/source_schedule_tables/engine_16_source_stage_slots.json"
RESULT_PATH = Path(__file__).with_name(Path(__file__).stem + "_results.json")

G = 0.35
KAP = 1.0
TH = np.pi / 4
Q = 1.0 - np.exp(-1.0)
N_STEPS = 160

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
NATIVE = {
    0: ("Ti", "Fi"),
    1: ("Ti", "Fi"),
    2: ("Te", "Fe"),
    3: ("Te", "Fe"),
    4: ("Ti", "Fi"),
    5: ("Ti", "Fi"),
    6: ("Te", "Fe"),
    7: ("Te", "Fe"),
}
QUADRANTS = ("LoseWin", "WinLose", "LoseLose", "WinWin")
PROBES = (
    np.array([0.55, 0.35, 0.25]),
    np.array([-0.45, 0.40, 0.30]),
    np.array([0.20, -0.65, 0.25]),
    np.array([0.15, 0.25, -0.70]),
)


def dm(v):
    v = np.array(v, float)
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
        else:
            out = out + KAP * dop(sz, r)
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
    r = r / np.trace(r).real
    return r


def stage_trajectory(ti, opname, axis6_sign):
    X = terrain_rhs(ti)
    O = op(opname)
    dt = 1.0 / N_STEPS
    out = []
    for probe in PROBES:
        r = dm(probe)
        pts = [bloch(r)]
        if axis6_sign == "up":
            r = O(r.copy())
            r = 0.5 * (r + r.conj().T)
            r = r / np.trace(r).real
            pts.append(bloch(r))
            for _ in range(N_STEPS):
                r = rk4_step(X, r, dt)
                pts.append(bloch(r))
        elif axis6_sign == "down":
            for _ in range(N_STEPS):
                r = rk4_step(X, r, dt)
                pts.append(bloch(r))
            r = O(r.copy())
            r = 0.5 * (r + r.conj().T)
            r = r / np.trace(r).real
            pts.append(bloch(r))
        else:
            raise ValueError(f"bad axis6_sign {axis6_sign!r}")
        out.append(np.array(pts))
    return np.array(out)  # shape (4, N_STEPS+2, 3)


def feature_vector(traj, erase_handedness=False):
    """Signed feature vector: raw signed trajectory channel concatenated with
    per-tick signed increment (delta) channel, across all four probes.
    erase_handedness: take |delta| in the delta channel only (trajectory
    channel kept signed) — the localization control."""
    raw = traj.reshape(-1)
    deltas = np.diff(traj, axis=1).reshape(-1)
    if erase_handedness:
        deltas = np.abs(deltas)
    return np.concatenate([raw, deltas])


def pairwise_D(features):
    n = len(features)
    D = np.zeros((n, n), float)
    for i in range(n):
        for j in range(i + 1, n):
            D[i, j] = D[j, i] = float(np.linalg.norm(features[i] - features[j]))
    return D


def silhouette_score(D, labels):
    labels = list(labels)
    scores = []
    for i, lab in enumerate(labels):
        same = [j for j, x in enumerate(labels) if x == lab and j != i]
        other_labs = sorted(set(labels) - {lab})
        a = float(np.mean([D[i, j] for j in same])) if same else 0.0
        b = min(float(np.mean([D[i, j] for j, x in enumerate(labels) if x == olab])) for olab in other_labs)
        scores.append((b - a) / max(a, b, 1e-12))
    return float(np.mean(scores))


def within_between(D, labels):
    within, between = [], []
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            (within if labels[i] == labels[j] else between).append(D[i, j])
    return float(np.mean(within)), float(np.mean(between)), float(np.mean(within) / max(np.mean(between), 1e-12))


def random_partition(rng):
    idx = rng.permutation(16)
    labels = [None] * 16
    for q, lab in enumerate(QUADRANTS):
        for i in idx[4 * q : 4 * (q + 1)]:
            labels[int(i)] = lab
    return labels


def validate_join(join, source_rows):
    rows = join.get("stage_join", [])
    if join.get("blocked"):
        raise ValueError("stage_token_join is blocked; no measurement allowed")
    if len(rows) != 16:
        raise ValueError(f"stage_token_join has {len(rows)} rows, expected 16")
    by_slot = {r["slot_id"]: r for r in source_rows}
    seen = set()
    for row in rows:
        key = (row["terrain_index"], row["operator"])
        if key in seen:
            raise ValueError(f"duplicate battery stage {key}")
        seen.add(key)
        if row["operator"] not in NATIVE[row["terrain_index"]]:
            raise ValueError(f"{row['battery_stage']} is not native under TERR/NATIVE")
        src = by_slot.get(row["source_slot_id"])
        if not src:
            raise ValueError(f"missing source slot {row['source_slot_id']}")
        for field in ("terrain", "canonical_operator", "canonical_token", "axis6_sign", "igt_quadrant"):
            expected = row["operator"] if field == "canonical_operator" else row[field]
            if src[field] != expected:
                raise ValueError(f"{row['source_slot_id']} {field} mismatch: join={expected!r} source={src[field]!r}")
    counts = {q: sum(1 for row in rows if row["igt_quadrant"] == q) for q in QUADRANTS}
    if sorted(counts.values()) != [4, 4, 4, 4]:
        raise ValueError(f"quadrant counts are not 4x4: {counts}")
    return rows, counts


def score_space(D, labels, null_labels):
    real_score = silhouette_score(D, labels)
    null_scores = np.array([silhouette_score(D, labs) for labs in null_labels])
    percentile = 100.0 * float((np.sum(null_scores < real_score) + 0.5 * np.sum(null_scores == real_score)) / len(null_scores))
    p05, p50, p95 = [float(x) for x in np.percentile(null_scores, [5, 50, 95])]
    return real_score, percentile, p05, p50, p95


def main():
    rng = np.random.default_rng(0)
    join = json.loads(JOIN_PATH.read_text())
    source_rows = json.loads(SOURCE_PATH.read_text())
    rows, quadrant_counts = validate_join(join, source_rows)

    trajectories = [
        stage_trajectory(row["terrain_index"], row["operator"], row["axis6_sign"])
        for row in rows
    ]
    feats_signed = [feature_vector(t, erase_handedness=False) for t in trajectories]
    feats_erased = [feature_vector(t, erase_handedness=True) for t in trajectories]
    D_signed = pairwise_D(feats_signed)
    D_erased = pairwise_D(feats_erased)

    labels = [row["igt_quadrant"] for row in rows]
    # shared shuffle set: same 200 random partitions scored in both spaces
    null_labels = [random_partition(rng) for _ in range(200)]

    real_score, percentile, null_p05, null_p50, null_p95 = score_space(D_signed, labels, null_labels)
    real_within, real_between, real_ratio = within_between(D_signed, labels)

    erased_labels = random_partition(rng)
    erased_label_score = silhouette_score(D_signed, erased_labels)
    erasure_in_null_band = bool(null_p05 <= erased_label_score <= null_p95)
    beats_shuffle_gate = bool(percentile >= 95.0)
    erasure_gate = bool(erasure_in_null_band and erased_label_score < real_score)
    gates_pass = bool(beats_shuffle_gate and erasure_gate)
    verdict = "load_bearing_at_this_probe" if gates_pass else "decorative_at_this_probe"

    # handedness-erasure localization control (probe's own erasure control)
    h_score, h_percentile, h_p05, h_p50, h_p95 = score_space(D_erased, labels, null_labels)
    handedness_collapse = bool(percentile >= 95.0 and h_percentile < 95.0)

    nearest = []
    for i, row in enumerate(rows):
        j = min([k for k in range(16) if k != i], key=lambda k: D_signed[i, k])
        nearest.append({
            "stage": row["battery_stage"],
            "canonical_token": row["canonical_token"],
            "igt_quadrant": row["igt_quadrant"],
            "nearest_stage": rows[j]["battery_stage"],
            "nearest_token": rows[j]["canonical_token"],
            "nearest_quadrant": rows[j]["igt_quadrant"],
            "distance": round(float(D_signed[i, j]), 6),
        })

    result = {
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "sim_id": "igt_quadrant_signed_feature_probe",
        "seed": 0,
        "question": "Does the igt_quadrant grouping become load-bearing when signed/coherent trajectory structure is preserved (raw signed Bloch time-series + signed per-tick increments), where the RMS-distance probe was decorative?",
        "precedent": "terrain_unique_computing_dynamics_probe: signed transient (handedness) features separated re-id-degenerate stage pairs; handedness-erasure collapsed them",
        "join_path": str(JOIN_PATH),
        "source_table": str(SOURCE_PATH),
        "engine_conventions": {
            "G": G,
            "KAP": KAP,
            "H0": "(sx+sy+sz)/sqrt(3)",
            "N_STEPS": N_STEPS,
            "TERR": {str(k): list(v) for k, v in TERR.items()},
            "NATIVE": {str(k): list(v) for k, v in NATIVE.items()},
            "axis6_up": "operator first, then terrain RK4 flow",
            "axis6_down": "terrain RK4 flow first, then operator",
        },
        "n_stages": 16,
        "quadrant_counts": quadrant_counts,
        "feature_space": "concat over 4 probe states of [raw signed Bloch trajectory (162x3)] + [per-tick signed increments (161x3)]; Euclidean distance; no norm/RMS collapse",
        "real_grouping": {
            "silhouette": real_score,
            "within_mean": real_within,
            "between_mean": real_between,
            "within_between_ratio": real_ratio,
        },
        "shuffle_null": {
            "n": len(null_labels),
            "p05": null_p05,
            "median": null_p50,
            "p95": null_p95,
            "real_percentile": percentile,
            "real_beats_at_least_95_percent": beats_shuffle_gate,
        },
        "label_erasure_control": {
            "score": erased_label_score,
            "in_null_band_5_95": erasure_in_null_band,
            "drops_below_real": bool(erased_label_score < real_score),
            "passes": erasure_gate,
        },
        "handedness_erasure_control": {
            "description": "delta channel replaced by |delta| (trajectory channel kept signed); same 200 shuffle partitions rescored in the erased space",
            "silhouette": h_score,
            "null_p05": h_p05,
            "null_median": h_p50,
            "null_p95": h_p95,
            "real_percentile": h_percentile,
            "advantage_collapses_under_handedness_erasure": handedness_collapse,
        },
        "gates_pass": gates_pass,
        "verdict": verdict,
        "nearest_stage_by_trajectory": nearest,
        "claim_ceiling": "scratch_diagnostic only; no source table, sim, run_all, or pre-existing result file was modified.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=1) + "\n")

    print("IGT QUADRANT SIGNED-FEATURE PROBE -- signed trajectories + signed increments")
    print("classification: scratch_diagnostic")
    print("promotion_allowed: false")
    print(f"join rows: {len(rows)}; quadrant counts: {quadrant_counts}")
    print(f"feature space: {result['feature_space']}")
    print(f"real silhouette: {real_score:.6f}")
    print(f"real within mean: {real_within:.6f}")
    print(f"real between mean: {real_between:.6f}")
    print(f"real within/between ratio: {real_ratio:.6f}")
    print(f"shuffle null n=200 p05/median/p95: {null_p05:.6f} / {null_p50:.6f} / {null_p95:.6f}")
    print(f"real percentile vs shuffles: {percentile:.2f}")
    print(f"label-erasure score: {erased_label_score:.6f} (in null band: {erasure_in_null_band})")
    print(f"shuffle gate >=95%: {beats_shuffle_gate}")
    print(f"label-erasure gate: {erasure_gate}")
    print(f"handedness-erasure silhouette: {h_score:.6f}")
    print(f"handedness-erasure real percentile: {h_percentile:.2f}")
    print(f"handedness-erasure null p05/median/p95: {h_p05:.6f} / {h_p50:.6f} / {h_p95:.6f}")
    print(f"advantage collapses under handedness erasure: {handedness_collapse}")
    print(f"VERDICT: {verdict}")
    print(f"ALL_GATES: {'PASS' if gates_pass else 'FAIL_DECORATIVE'} -> {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR igt_quadrant_signed_feature_probe: {exc}", file=sys.stderr)
        sys.exit(1)
