#!/usr/bin/env python3
"""stage_task_family_battery_sim

KK/KU/UK/UU task-family battery on real 16-stage GKSL outputs.

The stage-to-family map is read from stage_token_join.json:
  LoseWin -> UK, WinLose -> KU, LoseLose -> UU, WinWin -> KK.

Four task families are evaluated against each available stage family:
  KK: re-identify an already-formed object under familiar probe reuse.
  KU: recover an explicitly stated but unmeasured axis6 order parameter.
  UK: recover a hidden engine-side invariant from example trajectories.
  UU: detect model-class failure / novel-regime samples and form a new class.

The known confound from win_lose_as_known_unknown_fep_sim is controlled by an
Axis-5 rerun: every diagonal/off-diagonal comparison is repeated separately
inside the dissipative-generator-role and unitary-generator-role strata, then
averaged. The stratified result is the verdict-bearing result.

scratch_diagnostic; promotion_allowed=false. Additive only.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.linalg import expm, logm


HERE = Path(__file__).resolve().parent
JOIN_PATH = HERE / "stage_token_join.json"
RESULT_PATH = Path(__file__).with_name(Path(__file__).stem + "_results.json")

G = 0.35
KAP = 1.0
TH = np.pi / 4
Q = 1.0 - np.exp(-1.0)
N_STEPS = 120
SHUFFLE_DRAWS = 240

FAMILY_FROM_QUADRANT = {
    "LoseWin": "UK",
    "WinLose": "KU",
    "LoseLose": "UU",
    "WinWin": "KK",
}
FAMILIES = ("KK", "KU", "UK", "UU")
AXIS5_STRATA = ("dissipative_generator_role", "unitary_generator_role")

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


@dataclass(frozen=True)
class Stage:
    idx: int
    stage_id: str
    terrain_index: int
    terrain: str
    operator: str
    token: str
    axis6_sign: str
    quadrant: str
    task_family: str
    engine_side: str
    axis5_stratum: str


@dataclass(frozen=True)
class Sample:
    sample_id: str
    rho: np.ndarray
    stage_id: str
    task_family: str
    axis6_sign: str
    hidden_invariant: str
    is_novel: bool


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


def terrain_flow(ti, r):
    X = terrain_rhs(ti)
    dt = 1.0 / N_STEPS
    for _ in range(N_STEPS):
        r = rk4_step(X, r, dt)
    return r


def apply_stage(stage, r):
    O = op(stage.operator)
    if stage.axis6_sign == "up":
        r = O(r.copy())
        r = 0.5 * (r + r.conj().T)
        r = r / np.trace(r).real
        return terrain_flow(stage.terrain_index, r)
    if stage.axis6_sign == "down":
        r = terrain_flow(stage.terrain_index, r.copy())
        r = O(r)
        r = 0.5 * (r + r.conj().T)
        return r / np.trace(r).real
    raise ValueError(f"bad axis6_sign {stage.axis6_sign!r}")


def s_rel(rho, sig):
    rho = rho + 1e-12 * I2
    sig = sig + 1e-12 * I2
    return float(max(np.trace(rho @ (logm(rho) - logm(sig))).real / np.log(2), 0.0))


def probe_family(seed, n=6, radius=0.68, noise=0.0):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        v = rng.normal(size=3)
        v = radius * v / np.linalg.norm(v)
        if noise:
            v = v + rng.normal(scale=noise, size=3)
        out.append(dm(v))
    return out


def load_stages():
    join = json.loads(JOIN_PATH.read_text())
    rows = join.get("stage_join", [])
    if join.get("blocked"):
        raise ValueError("stage_token_join is blocked")
    if len(rows) != 16:
        raise ValueError(f"stage_token_join has {len(rows)} rows, expected 16")
    stages = []
    seen = set()
    terrain_sides = {
        item["terrain_index"]: item["engine_side"]
        for item in join.get("terrain_index_map", [])
    }
    for idx, row in enumerate(rows):
        key = (row["terrain_index"], row["operator"])
        if key in seen:
            raise ValueError(f"duplicate stage row {key}")
        seen.add(key)
        if row["operator"] not in NATIVE[row["terrain_index"]]:
            raise ValueError(f"{row['battery_stage']} is not native for its terrain")
        family = FAMILY_FROM_QUADRANT[row["igt_quadrant"]]
        stratum = (
            "dissipative_generator_role"
            if row["operator"] in ("Ti", "Te")
            else "unitary_generator_role"
        )
        stages.append(
            Stage(
                idx=idx,
                stage_id=row["battery_stage"],
                terrain_index=row["terrain_index"],
                terrain=row["terrain"],
                operator=row["operator"],
                token=row["canonical_token"],
                axis6_sign=row["axis6_sign"],
                quadrant=row["igt_quadrant"],
                task_family=family,
                engine_side=terrain_sides[row["terrain_index"]],
                axis5_stratum=stratum,
            )
        )
    counts = {fam: sum(1 for s in stages if s.task_family == fam) for fam in FAMILIES}
    if sorted(counts.values()) != [4, 4, 4, 4]:
        raise ValueError(f"task-family counts are not 4x4: {counts}")
    for fam in FAMILIES:
        for stratum in AXIS5_STRATA:
            n = sum(1 for s in stages if s.task_family == fam and s.axis5_stratum == stratum)
            if n != 2:
                raise ValueError(f"{fam}/{stratum} has {n} stages, expected 2")
    return stages, join, counts


def make_samples(stages, family, probes, tag, degrade=0.0):
    out = []
    for stage in stages:
        if stage.task_family != family:
            continue
        for k, probe in enumerate(probes):
            rho = apply_stage(stage, probe)
            if degrade:
                rho = (1.0 - degrade) * rho + degrade * 0.5 * I2
            hidden = stage.engine_side
            out.append(
                Sample(
                    sample_id=f"{tag}:{stage.stage_id}:{k}",
                    rho=rho,
                    stage_id=stage.stage_id,
                    task_family=stage.task_family,
                    axis6_sign=stage.axis6_sign,
                    hidden_invariant=hidden,
                    is_novel=(stage.task_family == "UU"),
                )
            )
    return out


def build_task_data(stages):
    data = {}
    data["KK"] = {
        "train": make_samples(stages, "KK", probe_family(101, n=6), "kk_train"),
        "test": make_samples(stages, "KK", probe_family(101, n=6), "kk_test", degrade=0.035),
    }
    data["KU"] = {
        "train": make_samples(stages, "KU", probe_family(111, n=5), "ku_train"),
        "test": make_samples(stages, "KU", probe_family(112, n=8), "ku_test"),
    }
    data["UK"] = {
        "examples": make_samples(stages, "UK", probe_family(121, n=7), "uk_examples"),
    }
    known_train = []
    known_test = []
    for fam in ("KK", "KU", "UK"):
        known_train.extend(make_samples(stages, fam, probe_family(131, n=3), f"uu_known_train_{fam}"))
        known_test.extend(make_samples(stages, fam, probe_family(132, n=3), f"uu_known_test_{fam}"))
    novel_test = make_samples(stages, "UU", probe_family(133, n=7), "uu_novel_test")
    data["UU"] = {"known_train": known_train, "test": known_test + novel_test}
    return data


def response_cache(stages, task_data):
    samples = []
    for cfg in task_data.values():
        for value in cfg.values():
            samples.extend(value)
    by_id = {}
    for sample in samples:
        if sample.sample_id in by_id:
            continue
        base = bloch(sample.rho)
        per_stage = {}
        for stage in stages:
            out = apply_stage(stage, sample.rho)
            b = bloch(out)
            per_stage[stage.idx] = np.concatenate([b, b - base, [s_rel(sample.rho, out)]])
        by_id[sample.sample_id] = per_stage
    return by_id


def features(sample, processor_ids, cache):
    return np.concatenate([cache[sample.sample_id][i] for i in processor_ids])


def nearest_label(train_samples, test_sample, processor_ids, cache, label_attr):
    q = features(test_sample, processor_ids, cache)
    best = None
    best_d = None
    for sample in train_samples:
        d = float(np.linalg.norm(q - features(sample, processor_ids, cache)))
        if best_d is None or d < best_d:
            best_d = d
            best = getattr(sample, label_attr)
    return best


def centroid_label(train_samples, test_sample, processor_ids, cache, label_attr):
    q = features(test_sample, processor_ids, cache)
    labels = sorted(set(getattr(s, label_attr) for s in train_samples))
    best = None
    best_d = None
    for label in labels:
        vecs = [features(s, processor_ids, cache) for s in train_samples if getattr(s, label_attr) == label]
        center = np.mean(vecs, axis=0)
        d = float(np.linalg.norm(q - center))
        if best_d is None or d < best_d:
            best_d = d
            best = label
    return best


def best_binary_cluster_accuracy(assignments, labels):
    labels = list(labels)
    opts = []
    for flip in (False, True):
        correct = 0
        for a, lab in zip(assignments, labels):
            pred = labels[0] if ((a == 0) ^ flip) else next(x for x in sorted(set(labels)) if x != labels[0])
            if pred == lab:
                correct += 1
        opts.append(correct / len(labels))
    return float(max(opts))


def kmeans2_accuracy(samples, processor_ids, cache):
    X = np.array([features(s, processor_ids, cache) for s in samples])
    labels = [s.hidden_invariant for s in samples]
    X = (X - X.mean(axis=0)) / np.maximum(X.std(axis=0), 1e-9)
    d0 = np.linalg.norm(X - X[0], axis=1)
    centers = np.array([X[0], X[int(np.argmax(d0))]])
    assign = np.zeros(len(X), dtype=int)
    for _ in range(20):
        D = np.stack([np.linalg.norm(X - centers[k], axis=1) for k in range(2)], axis=1)
        new_assign = np.argmin(D, axis=1)
        if np.array_equal(new_assign, assign):
            break
        assign = new_assign
        for k in range(2):
            if np.any(assign == k):
                centers[k] = X[assign == k].mean(axis=0)
    return best_binary_cluster_accuracy(assign, labels)


def roc_auc(scores, labels):
    pos = [s for s, y in zip(scores, labels) if y]
    neg = [s for s, y in zip(scores, labels) if not y]
    wins = 0.0
    total = len(pos) * len(neg)
    for p in pos:
        for n in neg:
            if p > n:
                wins += 1.0
            elif p == n:
                wins += 0.5
    return float(wins / total)


def score_task(task_family, processor_ids, task_data, cache):
    if len(processor_ids) == 0:
        raise ValueError("processor_ids cannot be empty")
    if task_family == "KK":
        train = task_data["KK"]["train"]
        test = task_data["KK"]["test"]
        ok = sum(
            1 for sample in test
            if nearest_label(train, sample, processor_ids, cache, "stage_id") == sample.stage_id
        )
        return ok / len(test)
    if task_family == "KU":
        train = task_data["KU"]["train"]
        test = task_data["KU"]["test"]
        ok = sum(
            1 for sample in test
            if centroid_label(train, sample, processor_ids, cache, "axis6_sign") == sample.axis6_sign
        )
        return ok / len(test)
    if task_family == "UK":
        return kmeans2_accuracy(task_data["UK"]["examples"], processor_ids, cache)
    if task_family == "UU":
        train = task_data["UU"]["known_train"]
        test = task_data["UU"]["test"]
        train_vecs = [features(s, processor_ids, cache) for s in train]
        scores = []
        labels = []
        for sample in test:
            q = features(sample, processor_ids, cache)
            scores.append(min(float(np.linalg.norm(q - v)) for v in train_vecs))
            labels.append(sample.is_novel)
        return roc_auc(scores, labels)
    raise ValueError(f"unknown task family {task_family!r}")


def task_description(family):
    return {
        "KK": "Re-identify one of four already-formed mapped-family objects under familiar probe reuse; score is nearest-reference object identity accuracy.",
        "KU": "Recover the explicitly stated but unmeasured axis6 up/down order parameter from new measurements; score is centroid-classification accuracy.",
        "UK": "Recover a hidden engine-side invariant from example trajectories without supplying that invariant to the clustering step; score is best binary cluster recovery.",
        "UU": "Detect model-class failure / novel-regime samples by distance from known-class prototypes and form a new class; score is ROC AUC for mapped-family novelty.",
    }[family]


def grouped_ids(stages, family=None, stratum=None, engine_side=None):
    ids = []
    for stage in stages:
        if family is not None and stage.task_family != family:
            continue
        if stratum is not None and stage.axis5_stratum != stratum:
            continue
        if engine_side is not None and stage.engine_side != engine_side:
            continue
        ids.append(stage.idx)
    return ids


def advantage_for_groups(task_family, groups, task_data, cache):
    scores = {fam: score_task(task_family, groups[fam], task_data, cache) for fam in FAMILIES}
    diag = scores[task_family]
    off = [scores[fam] for fam in FAMILIES if fam != task_family]
    return diag - float(np.mean(off)), scores


def random_raw_groups(rng, stages):
    perm = rng.permutation([s.idx for s in stages])
    return {fam: list(map(int, perm[i * 4 : (i + 1) * 4])) for i, fam in enumerate(FAMILIES)}


def random_stratified_groups(rng, stages):
    out = {fam: [] for fam in FAMILIES}
    for stratum in AXIS5_STRATA:
        pool = [s.idx for s in stages if s.axis5_stratum == stratum]
        perm = rng.permutation(pool)
        for i, fam in enumerate(FAMILIES):
            out[fam].extend(list(map(int, perm[i * 2 : (i + 1) * 2])))
    return out


def stratified_scores(task_family, stages, task_data, cache):
    by_family = {}
    stratum_detail = {}
    for fam in FAMILIES:
        vals = []
        stratum_detail[fam] = {}
        for stratum in AXIS5_STRATA:
            ids = grouped_ids(stages, family=fam, stratum=stratum)
            score = score_task(task_family, ids, task_data, cache)
            stratum_detail[fam][stratum] = score
            vals.append(score)
        by_family[fam] = float(np.mean(vals))
    diag = by_family[task_family]
    off = [by_family[fam] for fam in FAMILIES if fam != task_family]
    return diag - float(np.mean(off)), by_family, stratum_detail


def stratified_advantage_for_groups(task_family, groups, stages, task_data, cache):
    by_stage = {s.idx: s for s in stages}
    fam_scores = {}
    for fam in FAMILIES:
        vals = []
        for stratum in AXIS5_STRATA:
            ids = [i for i in groups[fam] if by_stage[i].axis5_stratum == stratum]
            vals.append(score_task(task_family, ids, task_data, cache))
        fam_scores[fam] = float(np.mean(vals))
    diag = fam_scores[task_family]
    off = [fam_scores[fam] for fam in FAMILIES if fam != task_family]
    return diag - float(np.mean(off)), fam_scores


def percentile_gate(real, null_values):
    arr = np.array(null_values, float)
    p95 = float(np.percentile(arr, 95))
    pct = 100.0 * float((np.sum(arr < real) + 0.5 * np.sum(arr == real)) / len(arr))
    return {
        "n": int(len(arr)),
        "p05": float(np.percentile(arr, 5)),
        "median": float(np.percentile(arr, 50)),
        "p95": p95,
        "real_percentile": pct,
        "beats_95pct": bool(real > p95),
    }


def evaluate(stages, task_data, cache):
    rng = np.random.default_rng(0)
    raw_groups = {fam: grouped_ids(stages, family=fam) for fam in FAMILIES}
    raw_null_groups = [random_raw_groups(rng, stages) for _ in range(SHUFFLE_DRAWS)]
    strat_null_groups = [random_stratified_groups(rng, stages) for _ in range(SHUFFLE_DRAWS)]
    type1_ids = grouped_ids(stages, engine_side="Type1_left")
    type2_ids = grouped_ids(stages, engine_side="Type2_right")
    all_ids = [s.idx for s in stages]

    results = {}
    for task_family in FAMILIES:
        raw_adv, raw_scores = advantage_for_groups(task_family, raw_groups, task_data, cache)
        raw_null = [
            advantage_for_groups(task_family, groups, task_data, cache)[0]
            for groups in raw_null_groups
        ]
        strat_adv, strat_scores, stratum_detail = stratified_scores(task_family, stages, task_data, cache)
        strat_null = [
            stratified_advantage_for_groups(task_family, groups, stages, task_data, cache)[0]
            for groups in strat_null_groups
        ]
        raw_gate = percentile_gate(raw_adv, raw_null)
        strat_gate = percentile_gate(strat_adv, strat_null)
        ablated_ids = [i for fam in FAMILIES if fam != task_family for i in raw_groups[fam]]
        ablated_score = score_task(task_family, ablated_ids, task_data, cache)
        diag_score = raw_scores[task_family]
        ablation_specificity = diag_score - ablated_score
        strat_ablation_specificity = strat_scores[task_family] - float(
            np.mean([strat_scores[fam] for fam in FAMILIES if fam != task_family])
        )
        strat_pass = bool(strat_gate["beats_95pct"] and strat_ablation_specificity > 0)
        raw_pass = bool(raw_gate["beats_95pct"] and ablation_specificity > 0)
        if strat_pass:
            verdict = "load_bearing"
        elif raw_pass:
            verdict = "confounded_axis5"
        else:
            verdict = "decorative"
        results[task_family] = {
            "task": task_description(task_family),
            "raw": {
                "scores_by_stage_family": {k: round(float(v), 6) for k, v in raw_scores.items()},
                "diagonal_advantage": round(float(raw_adv), 6),
                "ablation_specificity_diag_minus_all_offdiag_pool": round(float(ablation_specificity), 6),
                "shuffle_null": raw_gate,
            },
            "axis5_stratified": {
                "scores_by_stage_family": {k: round(float(v), 6) for k, v in strat_scores.items()},
                "scores_by_stage_family_and_stratum": {
                    fam: {st: round(float(val), 6) for st, val in vals.items()}
                    for fam, vals in stratum_detail.items()
                },
                "diagonal_advantage": round(float(strat_adv), 6),
                "ablation_specificity_diag_minus_mean_offdiag": round(float(strat_ablation_specificity), 6),
                "shuffle_null": strat_gate,
            },
            "collapsed_and_side_variants": {
                "all_16_stages": round(float(score_task(task_family, all_ids, task_data, cache)), 6),
                "type1_only": round(float(score_task(task_family, type1_ids, task_data, cache)), 6),
                "type2_only": round(float(score_task(task_family, type2_ids, task_data, cache)), 6),
            },
            "verdict": verdict,
        }
    return results


def next_probe(verdict):
    if verdict == "load_bearing":
        return "Freeze this family-specific task and rerun with a larger probe bag plus independent seeds before any admission claim."
    if verdict == "confounded_axis5":
        return "Build a matched-operator counterbattery that swaps only quadrant family while preserving Ti/Te vs Fi/Fe role and terrain-side balance."
    return "Tighten the task observable or add a same-family ablation that removes only the mapped stages while preserving operator-role balance."


def main():
    stages, join, counts = load_stages()
    task_data = build_task_data(stages)
    cache = response_cache(stages, task_data)
    results = evaluate(stages, task_data, cache)

    verdict_counts = {v: sum(1 for r in results.values() if r["verdict"] == v) for v in ("load_bearing", "decorative", "confounded_axis5")}
    out = {
        "classification": "scratch_diagnostic",
        "promotion_status": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "sim_id": "stage_task_family_battery",
        "seed": 0,
        "source_join": str(JOIN_PATH),
        "stage_family_mapping": FAMILY_FROM_QUADRANT,
        "engine_conventions": {
            "G": G,
            "KAP": KAP,
            "H0": "(sx+sy+sz)/sqrt(3)",
            "N_STEPS": N_STEPS,
            "TERR": {str(k): list(v) for k, v in TERR.items()},
            "axis6_up": "operator first, then terrain RK4 flow",
            "axis6_down": "terrain RK4 flow first, then operator",
        },
        "axis5_confound_control": "Verdict is based on matched Ti/Te vs Fi/Fe operator-role strata, not the raw four-stage family comparison.",
        "stage_counts": counts,
        "axis5_stratum_counts_by_family": {
            fam: {st: sum(1 for s in stages if s.task_family == fam and s.axis5_stratum == st) for st in AXIS5_STRATA}
            for fam in FAMILIES
        },
        "shuffle_draws": SHUFFLE_DRAWS,
        "task_family_results": results,
        "verdict_counts": verdict_counts,
        "next_bounded_probe_by_family": {fam: next_probe(res["verdict"]) for fam, res in results.items()},
        "TOOL_MANIFEST": {
            "numpy": "density matrices, Bloch vectors, deterministic sampling, nearest-neighbor and clustering metrics",
            "scipy.linalg": "matrix exponential for stage operators and matrix logarithm for response-relative entropy feature",
        },
        "TOOL_INTEGRATION_DEPTH": "supportive",
        "tool_manifest": {
            "numpy": "load-bearing numerical engine for finite density-matrix dynamics and metrics",
            "scipy.linalg": "supportive QIT operator/log surfaces for stage maps and response features",
        },
        "tool_integration_depth": "supportive",
        "claim_ceiling": "scratch_diagnostic only; no promotion/admission claim; exits 0 for any honest verdict mix.",
    }
    RESULT_PATH.write_text(json.dumps(out, indent=1) + "\n")

    print("STAGE TASK-FAMILY BATTERY -- real GKSL stage outputs")
    print("classification: scratch_diagnostic")
    print("promotion_allowed: false")
    print(f"source_join: {JOIN_PATH}")
    print(f"join rows: {len(stages)}; stage-family counts: {counts}")
    print(f"Axis-5 strata per family: {out['axis5_stratum_counts_by_family']}")
    print(f"shuffle stage->family null draws: {SHUFFLE_DRAWS}")
    print("verdict basis: Axis-5-stratified diagonal advantage plus ablation specificity")
    print("")
    print("family  raw_diag_adv  raw_p95  raw_pct  strat_diag_adv  strat_p95  strat_pct  verdict")
    for fam in FAMILIES:
        res = results[fam]
        raw = res["raw"]
        strat = res["axis5_stratified"]
        print(
            f"{fam:>2}      "
            f"{raw['diagonal_advantage']:+.6f}  "
            f"{raw['shuffle_null']['p95']:+.6f}  "
            f"{raw['shuffle_null']['real_percentile']:6.2f}  "
            f"{strat['diagonal_advantage']:+.6f}       "
            f"{strat['shuffle_null']['p95']:+.6f}  "
            f"{strat['shuffle_null']['real_percentile']:6.2f}  "
            f"{res['verdict']}"
        )
    print("")
    for fam in FAMILIES:
        variants = results[fam]["collapsed_and_side_variants"]
        print(
            f"{fam} variants: all16={variants['all_16_stages']:.6f}, "
            f"type1_only={variants['type1_only']:.6f}, type2_only={variants['type2_only']:.6f}"
        )
    print("")
    for fam in FAMILIES:
        print(f"next bounded probe {fam}: {out['next_bounded_probe_by_family'][fam]}")
    print(f"verdict counts: {verdict_counts}")
    print(f"ALL_GATES: HONEST_VERDICTS -> {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR stage_task_family_battery: {exc}", file=sys.stderr)
        sys.exit(1)
