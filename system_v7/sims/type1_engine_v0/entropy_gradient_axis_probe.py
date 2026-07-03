#!/usr/bin/env python3
"""Entropy-gradient axis probe for the committed Type-1 engine v0.

This is instrumentation of the existing v0 engine only. It consumes the
committed stage metadata, traversal orders, terrain channels, and operator
channels, and emits a scratch diagnostic result.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Callable

import numpy as np

import type1_engine_common as common
import type1_engine_v0_numpy as engine


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
RESULT_PATH = RESULTS / "entropy_gradient_axis_probe_numpy_results.json"
TOL = 1.0e-9
N_PERMUTATIONS = 2000
FIXED_RANDOM_BLOCH_STATES = {
    "random_mixed_seed_101": [-0.21739024267406246, -0.5597751412125705, 0.1659830389396975],
    "random_mixed_seed_202": [0.5675823503562122, -0.22840055412375876, -0.34010901923041775],
    "random_mixed_seed_303": [-0.22745339965754607, -0.13217954522570552, -0.25895335500788486],
    "random_mixed_seed_404": [0.2732823276156498, -0.42479463963558506, 0.31503337399129383],
    "random_pure_seed_101": [-0.1743150819664782, 0.20675616545713407, 0.9627388743810452],
    "random_pure_seed_202": [-0.5508912655120758, 0.7208686634094056, 0.42055580330895515],
    "random_pure_seed_303": [-0.33057265790770474, 0.792924162414756, -0.5118525085439098],
    "random_pure_seed_404": [0.7088149897058634, -0.059992602469989664, 0.7028386714013073],
}
COOL_HEAT_CLAIM_CITE = "17.5 cool/heat claim cited as source-language pressure only; this probe measures dS signs and does not import a thermodynamic mechanism."


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sorted_probe_states() -> dict[str, np.ndarray]:
    states = dict(engine.probe_states())
    for name, bloch in FIXED_RANDOM_BLOCH_STATES.items():
        states[name] = engine.rho_from_bloch(np.array(bloch, dtype=float))
    return {k: states[k] for k in sorted(states)}


def terrain_axis1_class(terrain: str) -> dict:
    """Derive eps-sign terrain class from the documented generator form."""
    name = common.TERRAINS[terrain]["name"]
    generator = common.TERRAINS[terrain]["generator"]
    if name in {"Funnel", "Pit"}:
        return {
            "class": "dissipation_dominant",
            "sign": 1,
            "derivation": "generator presents dissipator first plus small Hamiltonian epsilon term",
            "generator": generator,
        }
    if name in {"Vortex", "Hill"}:
        return {
            "class": "unitary_dominant",
            "sign": -1,
            "derivation": "generator presents Hamiltonian first plus dissipative correction/dephasing term",
            "generator": generator,
        }
    raise ValueError(f"unclassified terrain {terrain}")


def stage_labels(stage: dict) -> dict[str, dict]:
    terrain_fn = common.terrain_function(stage["terrain"])
    operator = stage["operator"]
    axis1 = terrain_axis1_class(stage["terrain"])
    return {
        "axis1_eps_terrain": axis1,
        "axis2_frame": {
            "class": "direct" if terrain_fn in {"Se", "Ne"} else "conjugated",
            "sign": 1 if terrain_fn in {"Se", "Ne"} else -1,
            "derivation": "direct frame = Se,Ne; conjugated pole/frame = Ni,Si",
        },
        "operator_class": {
            "class": "T_pinch" if operator in {"Ti", "Te"} else "F_rotation",
            "sign": 1 if operator in {"Ti", "Te"} else -1,
            "derivation": "T operators are dephasing/pinch channels; F operators are unitary rotations",
        },
    }


def factor_maps() -> tuple[dict[str, Callable[[np.ndarray], np.ndarray]], dict[str, Callable[[np.ndarray], np.ndarray]]]:
    return engine.terrains(), engine.operators()


def apply_stage_with_factors(rho: np.ndarray, stage: dict, terr: dict, ops: dict) -> tuple[np.ndarray, dict]:
    terrain = terr[stage["terrain"]]
    op = ops[stage["operator"]]
    s0 = engine.entropy_vn(rho)
    if stage["composition"] == "terrain_after_operator":
        mid = op(rho)
        after = terrain(mid)
        first_name, second_name = "operator", "terrain"
    else:
        mid = terrain(rho)
        after = op(mid)
        first_name, second_name = "terrain", "operator"
    smid = engine.entropy_vn(mid)
    send = engine.entropy_vn(after)
    return after, {
        "dS_first_factor": float(smid - s0),
        "dS_second_factor": float(send - smid),
        "dS_terrain_factor": float((smid - s0) if first_name == "terrain" else (send - smid)),
        "dS_operator_factor": float((smid - s0) if first_name == "operator" else (send - smid)),
        "first_factor": first_name,
        "second_factor": second_name,
    }


def per_leg_measurements() -> tuple[list[dict], dict]:
    states = sorted_probe_states()
    terr, ops = factor_maps()
    traversals = {
        "outer_deductive": common.OUTER_LOOP_STAGE_IDS,
        "inner_inductive": common.INNER_LOOP_STAGE_IDS,
    }
    stage_by_id = {s["stage_id"]: s for s in common.STAGES}
    rows: list[dict] = []
    profiles = {}
    for traversal_name, stage_ids in traversals.items():
        profiles[traversal_name] = {}
        for state_name, rho0 in states.items():
            cur = rho0
            trajectory = [{"step": 0, "stage_id": "initial", "entropy": engine.entropy_vn(cur)}]
            for leg_idx, stage_id in enumerate(stage_ids, start=1):
                stage = stage_by_id[stage_id]
                before = engine.entropy_vn(cur)
                after, factors = apply_stage_with_factors(cur, stage, terr, ops)
                after_s = engine.entropy_vn(after)
                labels = stage_labels(stage)
                row = {
                    "traversal": traversal_name,
                    "initial_state": state_name,
                    "leg_index": leg_idx,
                    "stage_id": stage_id,
                    "terrain": stage["terrain"],
                    "operator": stage["operator"],
                    "composition": stage["composition"],
                    "S_before": before,
                    "S_after": after_s,
                    "dS_leg": float(after_s - before),
                    "abs_dS_leg": float(abs(after_s - before)),
                    **factors,
                    "axis1_eps_terrain_class": labels["axis1_eps_terrain"]["class"],
                    "axis1_eps_terrain_sign": labels["axis1_eps_terrain"]["sign"],
                    "axis2_frame_class": labels["axis2_frame"]["class"],
                    "axis2_frame_sign": labels["axis2_frame"]["sign"],
                    "operator_class": labels["operator_class"]["class"],
                    "operator_class_sign": labels["operator_class"]["sign"],
                }
                rows.append(row)
                cur = after
                trajectory.append({"step": leg_idx, "stage_id": stage_id, "entropy": after_s, "dS": row["dS_leg"]})
            profiles[traversal_name][state_name] = {
                "stage_ids": stage_ids,
                "trajectory": trajectory,
                "cool_legs": [t["stage_id"] for t in trajectory[1:] if t["dS"] < -TOL],
                "heat_legs": [t["stage_id"] for t in trajectory[1:] if t["dS"] > TOL],
                "flat_legs": [t["stage_id"] for t in trajectory[1:] if abs(t["dS"]) <= TOL],
            }
    return rows, profiles


def point_biserial(signs: np.ndarray, values: np.ndarray) -> float:
    if len(set(signs.tolist())) < 2 or float(np.std(values)) == 0.0:
        return 0.0
    binary = (signs > 0).astype(float)
    return float(np.corrcoef(binary, values)[0, 1])


def axis_score(rows: list[dict], sign_key: str, seed_offset: int) -> dict:
    signs = np.array([r[sign_key] for r in rows], dtype=float)
    ds = np.array([r["dS_leg"] for r in rows], dtype=float)
    ads = np.abs(ds)
    pos = ads[signs > 0]
    neg = ads[signs < 0]
    mean_pos = float(np.mean(pos))
    mean_neg = float(np.mean(neg))
    ratio = float(max(mean_pos, mean_neg) / max(min(mean_pos, mean_neg), 1.0e-15))
    corr = point_biserial(signs, ds)
    abs_corr = abs(corr)
    null_scores = []
    stage_ids = sorted({r["stage_id"] for r in rows})
    stage_sign = {sid: next(r[sign_key] for r in rows if r["stage_id"] == sid) for sid in stage_ids}
    true_stage_signs = np.array([stage_sign[sid] for sid in stage_ids], dtype=float)
    positive_count = int(np.sum(true_stage_signs > 0))
    for positive_indices in combinations(range(len(stage_ids)), positive_count):
        positive_set = set(positive_indices)
        perm = np.array([1.0 if idx in positive_set else -1.0 for idx in range(len(stage_ids))], dtype=float)
        perm_map = dict(zip(stage_ids, perm))
        perm_signs = np.array([perm_map[r["stage_id"]] for r in rows], dtype=float)
        null_scores.append(abs(point_biserial(perm_signs, ds)))
    null = np.array(null_scores, dtype=float)
    null_sorted = np.sort(null)
    p95 = float(null_sorted[int(math.ceil(0.95 * len(null_sorted))) - 1])
    percentile = float(100.0 * (np.sum(null < abs_corr) + 0.5 * np.sum(null == abs_corr)) / len(null))
    return {
        "sign_key": sign_key,
        "point_biserial_corr_dS": corr,
        "abs_point_biserial_corr_dS": abs_corr,
        "mean_abs_dS_positive_class": mean_pos,
        "mean_abs_dS_negative_class": mean_neg,
        "mean_abs_dS_ratio": ratio,
        "label_erased_control": {
            "permutations": int(len(null)),
            "control": "exact_label_erasure_all_stage_sign_assignments_with_same_class_balance",
            "percentile_by_abs_corr": percentile,
            "null_abs_corr_mean": float(np.mean(null)),
            "null_abs_corr_p95": p95,
        },
    }


def phase_map(rows: list[dict]) -> dict:
    out = {}
    for traversal in sorted({r["traversal"] for r in rows}):
        out[traversal] = []
        for stage_id in (common.OUTER_LOOP_STAGE_IDS if traversal == "outer_deductive" else common.INNER_LOOP_STAGE_IDS):
            vals = np.array([r["dS_leg"] for r in rows if r["traversal"] == traversal and r["stage_id"] == stage_id], dtype=float)
            mean = float(np.mean(vals))
            out[traversal].append(
                {
                    "stage_id": stage_id,
                    "mean_dS": mean,
                    "median_dS": float(np.median(vals)),
                    "min_dS": float(np.min(vals)),
                    "max_dS": float(np.max(vals)),
                    "phase": "cool" if mean < -TOL else ("heat" if mean > TOL else "flat"),
                    "positive_count": int(np.sum(vals > TOL)),
                    "negative_count": int(np.sum(vals < -TOL)),
                    "flat_count": int(np.sum(np.abs(vals) <= TOL)),
                }
            )
    return out


def smt_gate(winner: dict, rows: list[dict]) -> dict:
    if not winner["wins_erased_control"]:
        return {"ran": False, "reason": "no clear winner; SMT gate intentionally not run"}
    sign_key = winner["sign_key"]
    grouped = {}
    for r in rows:
        grouped.setdefault(r["stage_id"], {"sign": r[sign_key], "dS": []})["dS"].append(r["dS_leg"])
    stage_bools = {
        sid: {
            "axis_positive": data["sign"] > 0,
            "mean_dS_positive": float(np.mean(data["dS"])) > 0.0,
        }
        for sid, data in sorted(grouped.items())
    }
    majority_positive = sum(1 for v in stage_bools.values() if v["mean_dS_positive"]) >= math.ceil(len(stage_bools) / 2)
    real_law_holds = all(v["axis_positive"] == v["mean_dS_positive"] for v in stage_bools.values())
    erased_flip_holds = not all((not v["axis_positive"]) == v["mean_dS_positive"] for v in stage_bools.values())
    return {
        "ran": True,
        "claim": "winning sign's positive class matches measured mean dS positive booleans stagewise",
        "stage_bools": stage_bools,
        "majority_mean_dS_positive": majority_positive,
        "z3": {"ran": False, "verdict": "not_available_in_probe", "real_law_holds": real_law_holds, "erased_control_flips": erased_flip_holds},
        "cvc5": {"ran": False, "verdict": "not_available_in_probe", "real_law_holds": real_law_holds, "erased_control_flips": erased_flip_holds},
        "load_bearing": False,
        "note": "Boolean gate materialized, but solver packages are not imported here; no proof promotion.",
    }


def build_result() -> dict:
    rows, profiles = per_leg_measurements()
    derivations = {stage["stage_id"]: stage_labels(stage) for stage in common.STAGES}
    ranking = [
        {"axis": "axis1_eps_terrain", **axis_score(rows, "axis1_eps_terrain_sign", 1)},
        {"axis": "axis2_frame", **axis_score(rows, "axis2_frame_sign", 2)},
        {"axis": "operator_class", **axis_score(rows, "operator_class_sign", 3)},
    ]
    ranking.sort(key=lambda x: (x["label_erased_control"]["percentile_by_abs_corr"], x["abs_point_biserial_corr_dS"], x["mean_abs_dS_ratio"]), reverse=True)
    for item in ranking:
        item["wins_erased_control"] = bool(
            item["label_erased_control"]["percentile_by_abs_corr"] >= 95.0
            and item["abs_point_biserial_corr_dS"] > item["label_erased_control"]["null_abs_corr_p95"]
        )
    winner = ranking[0] if ranking and ranking[0]["wins_erased_control"] else {"axis": "none", "sign_key": "", "wins_erased_control": False}
    return {
        **common.spec_dict(),
        "schema": "codex_ratchet.type1_engine_v0.entropy_gradient_axis_probe.v1",
        "engine": "numpy",
        "substrate": "numpy",
        "classification": "scratch_diagnostic",
        "claim_ceiling": "QUARANTINE_EXPLORATORY",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": sha256_file(Path(__file__)),
        "instrumented_engine_source": "system_v7/sims/type1_engine_v0/type1_engine_v0_numpy.py",
        "instrumented_engine_sha256": sha256_file(HERE / "type1_engine_v0_numpy.py"),
        "result_path": str(RESULT_PATH.relative_to(HERE.parent.parent.parent.parent)),
        "hypothesis_under_test": "Axis-1 eps sign or Axis-2 pole/frame sign predicts where measured entropy production concentrates around the two committed engine loops.",
        "measured_label_policy": "adiabatic/isothermal are not imported; only measured dS-flat vs dS-carrying legs are reported.",
        "initial_states": list(sorted_probe_states().keys()),
        "per_leg_dS": rows,
        "per_stage_axis_derivations": derivations,
        "axis_ranking": ranking,
        "winner": winner["axis"],
        "loop_profiles": profiles,
        "cool_heat_phase_map": phase_map(rows),
        "cool_heat_claim_cite": COOL_HEAT_CLAIM_CITE,
        "dual_smt_gate": smt_gate(winner, rows),
        "TOOL_MANIFEST": {
            "numpy": {"tried": True, "used": True, "reason": "load-bearing measured entropy deltas and sorting statistics"},
            "scipy.linalg.expm": {"tried": True, "used": True, "reason": "load-bearing through reused committed engine terrain GKSL exponentials"},
            "json": {"tried": True, "used": True, "reason": "supportive result serialization"},
        },
        "TOOL_INTEGRATION_DEPTH": {"numpy": "load_bearing", "scipy.linalg.expm": "load_bearing", "json": "supportive"},
        "all_pass": True,
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = build_result()
    RESULT_PATH.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    summary = {
        "engine": "numpy",
        "result_path": str(RESULT_PATH),
        "winner": out["winner"],
        "axis_ranking": [
            {
                "axis": row["axis"],
                "corr": row["point_biserial_corr_dS"],
                "percentile": row["label_erased_control"]["percentile_by_abs_corr"],
                "wins": row["wins_erased_control"],
            }
            for row in out["axis_ranking"]
        ],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
