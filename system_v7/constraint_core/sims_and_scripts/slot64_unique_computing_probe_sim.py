#!/usr/bin/env python3
"""slot64_unique_computing_probe

Per-slot uniqueness at 64 granularity, with by-construction cells excluded.

The only verdict-bearing slot comparisons are matched-content pairs: same
terrain and same operator. Different terrain/operator pairs are counted as
excluded_trivial because their SINDy generators differ by construction.

The switched-SINDy instrument is reused from loop_switched_sindy_probe_sim.py:
degree-2 polynomial library, STLSQ(threshold=0.02), per-segment held-out R2,
and coefficient-distance self-null from independent probe draws.

scratch_diagnostic; promotion_allowed=false. Honest verdict mixes exit 0.
"""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import loop_switched_sindy_probe_sim as sw  # noqa: E402


JOIN_PATH = HERE / "stage_token_join.json"
SOURCE64_PATH = ROOT / "reference_docs/engine_math/source_schedule_tables/engine_64_source_schedule.json"
RESULT_PATH = Path(__file__).with_name(Path(__file__).stem + "_results.json")

SEED = 0
R2_GATE = 0.90
T1_RESEED_N = 20


def load_sources():
    join = json.loads(JOIN_PATH.read_text())
    rows64 = json.loads(SOURCE64_PATH.read_text())
    if join.get("blocked"):
        raise ValueError("stage_token_join is blocked")
    terrain_by_name = {row["terrain_name"]: row["terrain_index"] for row in join["terrain_index_map"]}
    if len(rows64) != 64:
        raise ValueError(f"64-source schedule has {len(rows64)} rows, expected 64")
    rows = []
    for idx, row in enumerate(rows64):
        r = dict(row)
        r["row_index"] = idx
        r["terrain_index"] = terrain_by_name[r["terrain"]]
        rows.append(r)
    canonical = [r for r in rows if r["is_source_canonical"]]
    if len(canonical) != 16:
        raise ValueError(f"64-source schedule has {len(canonical)} source-canonical rows, expected 16")
    loops = {}
    for row in canonical:
        label = sw.LOOP_LABELS[(row["engine"], row["loop"])]
        loops.setdefault(label, []).append(as_sw_slot(row))
    for label, slots in loops.items():
        slots.sort(key=lambda s: s["step"])
        if len(slots) != 4:
            raise ValueError(f"{label} has {len(slots)} canonical slots, expected 4")
    return rows, loops


def as_sw_slot(row):
    return {
        "slot_id": row["slot_id"],
        "engine": row["engine"],
        "loop": row["loop"],
        "step": row["step"],
        "terrain": row["terrain"],
        "terrain_index": row["terrain_index"],
        "canonical_operator": row["operator"],
        "axis6_sign": row["axis6_sign"],
        "canonical_token": row["candidate_word"],
    }


def loop_label(row):
    return sw.LOOP_LABELS[(row["engine"], row["loop"])]


def advance_canonical_stage(slot, r):
    X = sw.terrain_rhs(slot["terrain_index"])
    O = sw.op(slot["canonical_operator"])
    if slot["axis6_sign"] == "up":
        r = sw.normalize_rho(O(r.copy()))
        r, _, _ = sw.flow_trajectory(X, r)
        return r
    if slot["axis6_sign"] == "down":
        r, _, _ = sw.flow_trajectory(X, r)
        r = sw.normalize_rho(O(r.copy()))
        return r
    raise ValueError(f"bad axis6_sign {slot['axis6_sign']!r}")


def candidate_slot_flow(row, r):
    X = sw.terrain_rhs(row["terrain_index"])
    O = sw.op(row["operator"])
    if row["axis6_sign"] == "up":
        rc = sw.normalize_rho(O(r.copy()))
        _, traj, _ = sw.flow_trajectory(X, rc)
        return traj
    if row["axis6_sign"] == "down":
        _, traj, _ = sw.flow_trajectory(X, r.copy())
        return traj
    raise ValueError(f"bad axis6_sign {row['axis6_sign']!r}")


def arrival_states_by_context(canonical_loops, probes):
    arrivals = {(label, step): [] for label, slots in canonical_loops.items() for step in range(1, 5)}
    for label, slots in canonical_loops.items():
        for probe in probes:
            r = sw.dm(probe)
            for _ in range(sw.CYCLES):
                for slot in slots:
                    arrivals[(label, slot["step"])].append(r.copy())
                    r = advance_canonical_stage(slot, r)
    return arrivals


def slot_trajs_from_arrivals(row, arrivals):
    label = loop_label(row)
    out = []
    for r in arrivals[(label, row["step"])]:
        out.append(candidate_slot_flow(row, r))
    return out


def slot_trajs_in_context(row, canonical_loops, probes):
    """Fallback/debug path; production run uses arrival_states_by_context."""
    label = loop_label(row)
    slots = canonical_loops[label]
    out = []
    for probe in probes:
        r = sw.dm(probe)
        for _ in range(sw.CYCLES):
            for slot in slots:
                if slot["step"] == row["step"]:
                    out.append(candidate_slot_flow(row, r))
                r = advance_canonical_stage(slot, r)
    return out


def fit_slot(row, train_arrivals, null_arrivals, test_arrivals):
    train = slot_trajs_from_arrivals(row, train_arrivals)
    null = slot_trajs_from_arrivals(row, null_arrivals)
    test = slot_trajs_from_arrivals(row, test_arrivals)
    coeff, r2, nz = sw.fit_sindy(train, test)
    null_coeff, null_r2, null_nz = sw.fit_sindy(null, test)
    return {
        "coefficients": coeff,
        "r2": r2,
        "nonzero_terms": nz,
        "null_coefficients": null_coeff,
        "null_r2": null_r2,
        "null_nonzero_terms": null_nz,
        "self_null": coeff_distance(coeff, null_coeff),
    }


def coeff_distance(a, b):
    return float(np.linalg.norm(a.reshape(-1) - b.reshape(-1)) / np.sqrt(a.size))


def shuffled_fit_score(row, train_arrivals, test_arrivals, seed):
    rng = np.random.default_rng(seed)
    train = slot_trajs_from_arrivals(row, train_arrivals)
    shuffled = [traj[rng.permutation(len(traj))] for traj in train]
    test = slot_trajs_from_arrivals(row, test_arrivals)
    _, r2, _ = sw.fit_sindy(shuffled, test)
    return r2


def enumerate_pair_cells(rows):
    matched = []
    excluded = 0
    by_content = {}
    for row in rows:
        by_content.setdefault((row["terrain"], row["operator"]), []).append(row)
    for a, b in combinations(rows, 2):
        if a["terrain"] == b["terrain"] and a["operator"] == b["operator"]:
            matched.append((a, b))
        else:
            excluded += 1
    return matched, excluded, by_content


def run_task_a(rows, canonical_loops):
    rng = np.random.default_rng(SEED)
    train_probes = sw.probe_set(rng)
    null_probes = sw.probe_set(rng)
    test_probes = sw.probe_set(rng)
    train_arrivals = arrival_states_by_context(canonical_loops, train_probes)
    null_arrivals = arrival_states_by_context(canonical_loops, null_probes)
    test_arrivals = arrival_states_by_context(canonical_loops, test_probes)
    fits = {}
    for row in rows:
        fits[row["row_index"]] = fit_slot(row, train_arrivals, null_arrivals, test_arrivals)
    matched, excluded, by_content = enumerate_pair_cells(rows)
    pair_results = []
    for a, b in matched:
        fa = fits[a["row_index"]]
        fb = fits[b["row_index"]]
        d = coeff_distance(fa["coefficients"], fb["coefficients"])
        band = max(fa["self_null"], fb["self_null"])
        pair_results.append({
            "pair": f"{a['slot_id']}:{a['candidate_word']}@{loop_label(a)} vs {b['slot_id']}:{b['candidate_word']}@{loop_label(b)}",
            "content": {"terrain": a["terrain"], "operator": a["operator"]},
            "distance": d,
            "self_null_band": band,
            "verdict": "position-unique" if d > band else "degenerate",
            "a": slot_summary(a),
            "b": slot_summary(b),
        })
    real_scores = [fits[i]["r2"] for i in fits]
    shuffled_scores = [
        shuffled_fit_score(row, train_arrivals, test_arrivals, SEED + 1000 + row["row_index"])
        for row in rows
    ]
    instrument_valid = bool(all(np.isfinite(x) and x >= R2_GATE for x in real_scores))
    shuffled_flip = bool(float(np.nanmean(real_scores)) > float(np.nanmean(shuffled_scores)))
    return {
        "fits": fits,
        "matched_pairs": matched,
        "pair_results": pair_results,
        "excluded_trivial_count": excluded,
        "content_group_sizes": {f"{k[0]}|{k[1]}": len(v) for k, v in sorted(by_content.items())},
        "instrument": {
            "min_r2": float(np.nanmin(real_scores)),
            "mean_r2": float(np.nanmean(real_scores)),
            "instrument_valid_all_slots": instrument_valid,
            "mean_shuffled_time_r2": float(np.nanmean(shuffled_scores)),
            "shuffled_time_flip": shuffled_flip,
        },
    }


def slot_summary(row):
    return {
        "row_index": row["row_index"],
        "slot_id": row["slot_id"],
        "engine": row["engine"],
        "loop": row["loop"],
        "step": row["step"],
        "terrain": row["terrain"],
        "operator": row["operator"],
        "candidate_word": row["candidate_word"],
        "is_source_canonical": row["is_source_canonical"],
    }


def run_t1_reseed(canonical_loops):
    subset = {
        "Type1-inner-inductive": canonical_loops["Type1-inner-inductive"],
        "Type1-outer-deductive": canonical_loops["Type1-outer-deductive"],
    }
    rows = []
    for seed in range(T1_RESEED_N):
        rng = np.random.default_rng(seed)
        train = sw.probe_set(rng)
        null = sw.probe_set(rng)
        test = sw.probe_set(rng)
        sigs, null_sigs, metrics = sw.fit_all_signatures(subset, train, null, test)
        d, perm = sw.unordered_distance(sigs["Type1-inner-inductive"], sigs["Type1-outer-deductive"], "flow")
        null_band = max(
            sw.unordered_distance(sigs[label], null_sigs[label], "flow")[0]
            for label in sorted(sigs)
        )
        ratio = float(d / max(null_band, 1e-12))
        min_r2 = min(m["heldout_r2"] for vals in metrics.values() for m in vals)
        rows.append({
            "seed": seed,
            "unordered_distance": d,
            "unordered_self_null_band": null_band,
            "margin_over_band_ratio": ratio,
            "exceeds_band": bool(d > null_band),
            "best_match_positions_outer": perm,
            "min_segment_r2": min_r2,
        })
    frac = float(np.mean([r["exceeds_band"] for r in rows]))
    ratios = [r["margin_over_band_ratio"] for r in rows]
    if frac >= 0.8:
        verdict = "content-carried-robust"
    elif frac > 0.0:
        verdict = "content-carried-fragile"
    else:
        verdict = "degenerate"
    return {
        "seeds": rows,
        "fraction_exceeds_band": frac,
        "ratio_min": float(np.min(ratios)),
        "ratio_median": float(np.median(ratios)),
        "ratio_max": float(np.max(ratios)),
        "verdict": verdict,
        "instrument_valid_all_reseeds": bool(all(r["min_segment_r2"] >= R2_GATE for r in rows)),
    }


def json_fit_summary(row, fit):
    return {
        "slot": slot_summary(row),
        "heldout_r2": fit["r2"],
        "self_null": fit["self_null"],
        "nonzero_terms": fit["nonzero_terms"],
    }


def main():
    rows64, canonical_loops = load_sources()
    task_a = run_task_a(rows64, canonical_loops)
    task_b = run_t1_reseed(canonical_loops)
    pair_verdict_counts = {
        verdict: sum(1 for p in task_a["pair_results"] if p["verdict"] == verdict)
        for verdict in ("position-unique", "degenerate")
    }
    result = {
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "sim_id": "slot64_unique_computing_probe",
        "seed": SEED,
        "source_paths": {
            "stage_token_join": str(JOIN_PATH),
            "engine_64_source_schedule": str(SOURCE64_PATH),
            "instrument_source": str(HERE / "loop_switched_sindy_probe_sim.py"),
        },
        "instrument": {
            "method": "per-slot switched SINDy in schedule context; degree-2 PolynomialLibrary + STLSQ(threshold=0.02), held-out derivative R2",
            "r2_gate": R2_GATE,
            **task_a["instrument"],
        },
        "task_a": {
            "total_slots": len(rows64),
            "total_pair_cells": len(rows64) * (len(rows64) - 1) // 2,
            "matched_content_pair_count": len(task_a["matched_pairs"]),
            "excluded_trivial_count": task_a["excluded_trivial_count"],
            "excluded_trivial_rule": "Different terrain or different operator; by-construction generator/operator content difference, not a finding.",
            "content_group_sizes": task_a["content_group_sizes"],
            "pair_verdict_counts": pair_verdict_counts,
            "pair_results": task_a["pair_results"],
            "slot_fit_summaries": [
                json_fit_summary(row, task_a["fits"][row["row_index"]])
                for row in rows64
            ],
        },
        "task_b_t1_reseed_robustness": task_b,
        "tool_manifest": {
            "pysindy": "load_bearing: per-slot/per-loop switched sparse dynamics ID and held-out derivative R2 gate",
            "numpy": "supportive: density matrices, probe draws, coefficient distances, reseed statistics",
            "scipy.linalg": "supportive through imported switched-SINDy instrument operators",
            "json": "supportive source/result serialization",
        },
        "tool_integration_depth": {
            "pysindy": "load_bearing",
            "numpy": "supportive",
            "scipy": "supportive",
            "json": "supportive",
        },
        "claim_ceiling": "scratch_diagnostic only; excludes by-construction cells and makes no admission/source-edit claim.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")

    print("SLOT64 UNIQUE-COMPUTING PROBE")
    print("classification: scratch_diagnostic")
    print("promotion_allowed: false")
    print(f"64-slot rows: {len(rows64)}")
    print(f"matched-content pair count: {len(task_a['matched_pairs'])}")
    print(f"excluded_trivial pair count: {task_a['excluded_trivial_count']}")
    print(f"instrument min/mean R2: {task_a['instrument']['min_r2']:.6f} / {task_a['instrument']['mean_r2']:.6f}")
    print(f"shuffled-time mean R2: {task_a['instrument']['mean_shuffled_time_r2']:.6f}; flip={task_a['instrument']['shuffled_time_flip']}")
    print(f"matched-pair verdict summary: {pair_verdict_counts}")
    print("")
    print("matched-pair sample table:")
    print("pair | distance | self-null | verdict")
    for row in task_a["pair_results"][:12]:
        print(f"{row['pair']} | {row['distance']:.6f} | {row['self_null_band']:.6f} | {row['verdict']}")
    if len(task_a["pair_results"]) > 12:
        print(f"... {len(task_a['pair_results']) - 12} additional matched pairs in JSON")
    print("")
    print("T1-inner vs T1-outer unordered reseed robustness:")
    print(f"seeds: {T1_RESEED_N}")
    print(f"ratio min/median/max: {task_b['ratio_min']:.6f} / {task_b['ratio_median']:.6f} / {task_b['ratio_max']:.6f}")
    print(f"fraction exceeds band: {task_b['fraction_exceeds_band']:.6f}")
    print(f"verdict: {task_b['verdict']}")
    print(f"ALL_GATES: HONEST_VERDICTS -> {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR slot64_unique_computing_probe: {exc}", file=sys.stderr)
        sys.exit(1)
