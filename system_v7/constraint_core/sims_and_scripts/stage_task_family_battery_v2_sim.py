#!/usr/bin/env python3
"""stage_task_family_battery_v2_sim

Tightened-observable round for the stage task-family battery.

v1 showed KK and UK at ceiling under every variant, so v2 changes only those
two task observables. Calibration is deliberately blind: KK/UK difficulty is
chosen from the all-16 baseline only, before any family-vs-family comparison
or shuffled/null verdict is computed.

scratch_diagnostic; promotion_allowed=false. Additive only.
"""
from __future__ import annotations

import json
import sys
from itertools import permutations
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stage_task_family_battery_sim as base  # noqa: E402


RESULT_PATH = Path(__file__).with_name(Path(__file__).stem + "_results.json")
SEED = 0
TARGET_MIN = 0.60
TARGET_MAX = 0.95
VERDICTS = ("load_bearing", "decorative", "confounded_axis5", "still_at_ceiling")


def stable_seed(*parts):
    text = "|".join(str(p) for p in parts)
    total = 0
    for i, ch in enumerate(text.encode("utf-8")):
        total = (total + (i + 1) * ch) % (2**32)
    return total


def noisy_features(sample, processor_ids, cache, noise, salt):
    vec = base.features(sample, processor_ids, cache)
    if noise <= 0:
        return vec
    rng = np.random.default_rng(stable_seed(sample.sample_id, tuple(processor_ids), salt))
    return vec + rng.normal(scale=noise, size=vec.shape)


def nearest_label_noisy(train_samples, test_sample, processor_ids, cache, label_attr, noise, salt):
    q = noisy_features(test_sample, processor_ids, cache, noise, f"{salt}:query")
    best = None
    best_d = None
    for sample in train_samples:
        v = noisy_features(sample, processor_ids, cache, noise, f"{salt}:proto")
        d = float(np.linalg.norm(q - v))
        if best_d is None or d < best_d:
            best_d = d
            best = getattr(sample, label_attr)
    return best


def kk_score_v2(processor_ids, task_data, cache, params):
    """Harder KK observable: noisy nearest-reference re-identification with
    non-KK decoy prototypes. The decoy/noise parameters are frozen by all-16
    calibration before family comparisons run."""
    if len(processor_ids) == 0:
        raise ValueError("processor_ids cannot be empty")
    train = task_data["KK"]["train"]
    test = task_data["KK"]["test"]
    decoy_pool = task_data["UU"]["known_train"] + task_data["UU"]["test"]
    decoy_count = int(params["decoy_count"])
    noise = float(params["feature_noise"])
    ok = 0
    for sample in test:
        rng = np.random.default_rng(stable_seed("kk_decoys", sample.sample_id, decoy_count))
        if decoy_count:
            picks = rng.choice(len(decoy_pool), size=min(decoy_count, len(decoy_pool)), replace=False)
            candidates = train + [decoy_pool[int(i)] for i in picks]
        else:
            candidates = train
        pred = nearest_label_noisy(candidates, sample, processor_ids, cache, "stage_id", noise, "KK")
        if pred == sample.stage_id:
            ok += 1
    return float(ok / len(test))


def fine_uk_label(sample, stage_by_id):
    stage = stage_by_id[sample.stage_id]
    return f"{stage.engine_side}:{stage.axis6_sign}"


def best_k_cluster_accuracy(assignments, labels):
    labels = list(labels)
    unique = sorted(set(labels))
    k = len(unique)
    best = 0
    for perm in permutations(unique):
        mapping = {i: perm[i] for i in range(k)}
        correct = sum(1 for a, lab in zip(assignments, labels) if mapping[int(a)] == lab)
        best = max(best, correct)
    return float(best / len(labels))


def kmeans_k_accuracy(samples, processor_ids, cache, labels, k, noise, salt):
    if len(processor_ids) == 0:
        raise ValueError("processor_ids cannot be empty")
    X = np.array([noisy_features(s, processor_ids, cache, noise, f"{salt}:{i}") for i, s in enumerate(samples)])
    X = (X - X.mean(axis=0)) / np.maximum(X.std(axis=0), 1e-9)
    centers = [X[0]]
    for _ in range(1, k):
        d = np.min(np.stack([np.linalg.norm(X - c, axis=1) for c in centers], axis=1), axis=1)
        centers.append(X[int(np.argmax(d))])
    centers = np.array(centers)
    assign = np.zeros(len(X), dtype=int)
    for _ in range(30):
        D = np.stack([np.linalg.norm(X - centers[j], axis=1) for j in range(k)], axis=1)
        new_assign = np.argmin(D, axis=1)
        if np.array_equal(new_assign, assign):
            break
        assign = new_assign
        for j in range(k):
            if np.any(assign == j):
                centers[j] = X[assign == j].mean(axis=0)
    return best_k_cluster_accuracy(assign, labels)


def uk_score_v2(processor_ids, task_data, cache, stage_by_id, params):
    """Harder UK observable: recover a finer hidden invariant
    (engine_side x axis6_sign; four labels), not the old binary engine-side
    split. Noise is calibrated only against the all-16 baseline."""
    samples = task_data["UK"]["examples"]
    labels = [fine_uk_label(s, stage_by_id) for s in samples]
    return kmeans_k_accuracy(samples, processor_ids, cache, labels, len(set(labels)), float(params["feature_noise"]), "UK")


def score_task_v2(task_family, processor_ids, task_data, cache, stage_by_id, calibration):
    if task_family == "KK":
        return kk_score_v2(processor_ids, task_data, cache, calibration["KK"]["params"])
    if task_family == "UK":
        return uk_score_v2(processor_ids, task_data, cache, stage_by_id, calibration["UK"]["params"])
    return base.score_task(task_family, processor_ids, task_data, cache)


def in_target(score):
    return TARGET_MIN <= score <= TARGET_MAX


def choose_best(candidates):
    viable = [c for c in candidates if in_target(c["score"])]
    if viable:
        return viable[0] | {"calibration_pass": True}
    target_mid = 0.5 * (TARGET_MIN + TARGET_MAX)
    return min(candidates, key=lambda c: abs(c["score"] - target_mid)) | {"calibration_pass": False}


def calibrate_observables(stages, task_data, cache, stage_by_id):
    all_ids = [s.idx for s in stages]
    # Calibration sees only all-16 baseline scores. It does not inspect
    # family-diagonal/off-diagonal results, shuffled nulls, or Axis-5 strata.
    kk_candidates = []
    for decoys in (4, 8, 12, 18, 24):
        for noise in (0.00, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.16, 0.20, 0.25, 0.30):
            params = {"feature_noise": noise, "decoy_count": decoys}
            score = kk_score_v2(all_ids, task_data, cache, params)
            kk_candidates.append({"params": params, "score": score})
    uk_candidates = []
    for noise in (0.00, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.16, 0.20, 0.25, 0.30, 0.40, 0.50):
        params = {"feature_noise": noise, "fine_invariant": "engine_side_x_axis6_sign"}
        score = uk_score_v2(all_ids, task_data, cache, stage_by_id, params)
        uk_candidates.append({"params": params, "score": score})
    return {
        "target_range": [TARGET_MIN, TARGET_MAX],
        "blind_to_family_outcomes": True,
        "KK": choose_best(kk_candidates),
        "UK": choose_best(uk_candidates),
        "candidate_trace": {
            "KK": kk_candidates,
            "UK": uk_candidates,
        },
    }


def grouped_ids(stages, family=None, stratum=None, engine_side=None):
    return base.grouped_ids(stages, family=family, stratum=stratum, engine_side=engine_side)


def advantage_for_groups(task_family, groups, task_data, cache, stage_by_id, calibration):
    scores = {
        fam: score_task_v2(task_family, groups[fam], task_data, cache, stage_by_id, calibration)
        for fam in base.FAMILIES
    }
    diag = scores[task_family]
    off = [scores[fam] for fam in base.FAMILIES if fam != task_family]
    return diag - float(np.mean(off)), scores


def stratified_scores(task_family, stages, task_data, cache, stage_by_id, calibration):
    by_family = {}
    stratum_detail = {}
    for fam in base.FAMILIES:
        vals = []
        stratum_detail[fam] = {}
        for stratum in base.AXIS5_STRATA:
            ids = grouped_ids(stages, family=fam, stratum=stratum)
            score = score_task_v2(task_family, ids, task_data, cache, stage_by_id, calibration)
            stratum_detail[fam][stratum] = score
            vals.append(score)
        by_family[fam] = float(np.mean(vals))
    diag = by_family[task_family]
    off = [by_family[fam] for fam in base.FAMILIES if fam != task_family]
    return diag - float(np.mean(off)), by_family, stratum_detail


def stratified_advantage_for_groups(task_family, groups, stages, task_data, cache, stage_by_id, calibration):
    by_stage = {s.idx: s for s in stages}
    fam_scores = {}
    for fam in base.FAMILIES:
        vals = []
        for stratum in base.AXIS5_STRATA:
            ids = [i for i in groups[fam] if by_stage[i].axis5_stratum == stratum]
            vals.append(score_task_v2(task_family, ids, task_data, cache, stage_by_id, calibration))
        fam_scores[fam] = float(np.mean(vals))
    diag = fam_scores[task_family]
    off = [fam_scores[fam] for fam in base.FAMILIES if fam != task_family]
    return diag - float(np.mean(off)), fam_scores


def raw_ablation_balanced(task_family, stages, task_data, cache, stage_by_id, calibration):
    all_ids = [s.idx for s in stages]
    without = [s.idx for s in stages if s.task_family != task_family]
    return {
        "all16_score": score_task_v2(task_family, all_ids, task_data, cache, stage_by_id, calibration),
        "remove_only_mapped_family_score": score_task_v2(task_family, without, task_data, cache, stage_by_id, calibration),
        "removed_stage_ids": [s.stage_id for s in stages if s.task_family == task_family],
        "remaining_axis5_balance": {
            st: sum(1 for s in stages if s.task_family != task_family and s.axis5_stratum == st)
            for st in base.AXIS5_STRATA
        },
    }


def evaluate(stages, task_data, cache, calibration):
    rng = np.random.default_rng(SEED)
    stage_by_id = {s.stage_id: s for s in stages}
    raw_groups = {fam: grouped_ids(stages, family=fam) for fam in base.FAMILIES}
    raw_null_groups = [base.random_raw_groups(rng, stages) for _ in range(base.SHUFFLE_DRAWS)]
    strat_null_groups = [base.random_stratified_groups(rng, stages) for _ in range(base.SHUFFLE_DRAWS)]
    type1_ids = grouped_ids(stages, engine_side="Type1_left")
    type2_ids = grouped_ids(stages, engine_side="Type2_right")
    all_ids = [s.idx for s in stages]

    results = {}
    for task_family in base.FAMILIES:
        raw_adv, raw_scores = advantage_for_groups(task_family, raw_groups, task_data, cache, stage_by_id, calibration)
        raw_null = [
            advantage_for_groups(task_family, groups, task_data, cache, stage_by_id, calibration)[0]
            for groups in raw_null_groups
        ]
        strat_adv, strat_scores, stratum_detail = stratified_scores(task_family, stages, task_data, cache, stage_by_id, calibration)
        strat_null = [
            stratified_advantage_for_groups(task_family, groups, stages, task_data, cache, stage_by_id, calibration)[0]
            for groups in strat_null_groups
        ]
        raw_gate = base.percentile_gate(raw_adv, raw_null)
        strat_gate = base.percentile_gate(strat_adv, strat_null)
        same_family = raw_ablation_balanced(task_family, stages, task_data, cache, stage_by_id, calibration)
        same_family["ablation_specificity"] = same_family["all16_score"] - same_family["remove_only_mapped_family_score"]
        diag_score = raw_scores[task_family]
        ablated_ids = [i for fam in base.FAMILIES if fam != task_family for i in raw_groups[fam]]
        ablation_specificity = diag_score - score_task_v2(task_family, ablated_ids, task_data, cache, stage_by_id, calibration)
        strat_ablation_specificity = strat_scores[task_family] - float(np.mean([strat_scores[fam] for fam in base.FAMILIES if fam != task_family]))
        strat_pass = bool(strat_gate["beats_95pct"] and strat_ablation_specificity > 0 and same_family["ablation_specificity"] > 0)
        raw_pass = bool(raw_gate["beats_95pct"] and ablation_specificity > 0)
        calibration_failed = task_family in ("KK", "UK") and not calibration[task_family]["calibration_pass"]
        if calibration_failed:
            verdict = "still_at_ceiling"
        elif strat_pass:
            verdict = "load_bearing"
        elif raw_pass:
            verdict = "confounded_axis5"
        else:
            verdict = "decorative"
        results[task_family] = {
            "task": task_description_v2(task_family),
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
                "all_16_stages": round(float(score_task_v2(task_family, all_ids, task_data, cache, stage_by_id, calibration)), 6),
                "type1_only": round(float(score_task_v2(task_family, type1_ids, task_data, cache, stage_by_id, calibration)), 6),
                "type2_only": round(float(score_task_v2(task_family, type2_ids, task_data, cache, stage_by_id, calibration)), 6),
            },
            "same_family_ablation_preserve_operator_role_balance": same_family,
            "verdict": verdict,
        }
    return results


def task_description_v2(family):
    if family == "KK":
        return "Tightened KK: noisy re-identification among familiar references plus non-KK decoy prototypes; difficulty frozen from all-16 baseline only."
    if family == "UK":
        return "Tightened UK: unsupervised recovery of finer hidden invariant engine_side x axis6_sign, with difficulty frozen from all-16 baseline only."
    return base.task_description(family)


def next_probe(verdict):
    if verdict == "load_bearing":
        return "Freeze this family-specific observable and rerun with independent seeds before any stronger claim."
    if verdict == "confounded_axis5":
        return "Build a matched counterbattery that swaps only task family while preserving Axis-5 role and engine side."
    if verdict == "still_at_ceiling":
        return "Calibration failed; further tighten the all-16 baseline before interpreting family outcomes."
    return "Try a more specific family observable or a narrower same-family removal that preserves more non-target structure."


def main():
    stages, join, counts = base.load_stages()
    task_data = base.build_task_data(stages)
    cache = base.response_cache(stages, task_data)
    stage_by_id = {s.stage_id: s for s in stages}
    calibration = calibrate_observables(stages, task_data, cache, stage_by_id)
    results = evaluate(stages, task_data, cache, calibration)
    verdict_counts = {v: sum(1 for r in results.values() if r["verdict"] == v) for v in VERDICTS}
    out = {
        "classification": "scratch_diagnostic",
        "promotion_status": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "sim_id": "stage_task_family_battery_v2",
        "seed": SEED,
        "source_join": str(base.JOIN_PATH),
        "stage_family_mapping": base.FAMILY_FROM_QUADRANT,
        "calibration": calibration,
        "calibration_discipline": "KK and UK parameters selected using only all-16 baseline scores in target range before any family comparison, shuffled null, or Axis-5 stratification is computed.",
        "engine_conventions": {
            "G": base.G,
            "KAP": base.KAP,
            "H0": "(sx+sy+sz)/sqrt(3)",
            "N_STEPS": base.N_STEPS,
            "axis6_up": "operator first, then terrain RK4 flow",
            "axis6_down": "terrain RK4 flow first, then operator",
        },
        "stage_counts": counts,
        "axis5_stratum_counts_by_family": {
            fam: {st: sum(1 for s in stages if s.task_family == fam and s.axis5_stratum == st) for st in base.AXIS5_STRATA}
            for fam in base.FAMILIES
        },
        "shuffle_draws": base.SHUFFLE_DRAWS,
        "task_family_results": results,
        "verdict_counts": verdict_counts,
        "next_bounded_probe_by_family": {fam: next_probe(res["verdict"]) for fam, res in results.items()},
        "tool_manifest": {
            "numpy": "load-bearing numerical engine for deterministic sampling, feature noise, distances, and clustering metrics",
            "scipy.linalg": "supportive QIT operator/log surfaces inherited from v1 battery",
        },
        "tool_integration_depth": "supportive",
        "claim_ceiling": "scratch_diagnostic only; no promotion/admission claim; exits 0 for any honest verdict mix.",
    }
    RESULT_PATH.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")

    print("STAGE TASK-FAMILY BATTERY V2 -- tightened KK/UK observables")
    print("classification: scratch_diagnostic")
    print("promotion_allowed: false")
    print(f"source_join: {base.JOIN_PATH}")
    print(f"join rows: {len(stages)}; stage-family counts: {counts}")
    print(f"shuffle stage->family null draws: {base.SHUFFLE_DRAWS}")
    print("calibration is all-16 baseline only, frozen before family comparisons")
    print("")
    print("calibration table:")
    for fam in ("KK", "UK"):
        c = calibration[fam]
        print(f"{fam}: score={c['score']:.6f}, pass={c['calibration_pass']}, params={c['params']}")
    print("")
    print("family raw and Axis-5-stratified verdict table:")
    print("family | raw scores KK/KU/UK/UU | raw_adv | raw_p95 | strat scores KK/KU/UK/UU | strat_adv | strat_p95 | ablation | verdict")
    for fam in base.FAMILIES:
        res = results[fam]
        raw = res["raw"]
        strat = res["axis5_stratified"]
        raw_scores = "/".join(f"{raw['scores_by_stage_family'][x]:.3f}" for x in base.FAMILIES)
        strat_scores = "/".join(f"{strat['scores_by_stage_family'][x]:.3f}" for x in base.FAMILIES)
        abl = res["same_family_ablation_preserve_operator_role_balance"]["ablation_specificity"]
        print(
            f"{fam} | {raw_scores} | {raw['diagonal_advantage']:+.6f} | {raw['shuffle_null']['p95']:+.6f} | "
            f"{strat_scores} | {strat['diagonal_advantage']:+.6f} | {strat['shuffle_null']['p95']:+.6f} | "
            f"{abl:+.6f} | {res['verdict']}"
        )
    print("")
    for fam in base.FAMILIES:
        variants = results[fam]["collapsed_and_side_variants"]
        print(f"{fam} variants: all16={variants['all_16_stages']:.6f}, type1_only={variants['type1_only']:.6f}, type2_only={variants['type2_only']:.6f}")
    print(f"verdict counts: {verdict_counts}")
    print(f"ALL_GATES: HONEST_VERDICTS -> {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR stage_task_family_battery_v2: {exc}", file=sys.stderr)
        sys.exit(1)
