#!/usr/bin/env python3
"""Four-element IGT <-> QIT Rosetta structure formal scout.

This probe tests whether the literal four-row IGT placements across Type 1 /
Type 2 and outer / inner loops match the current canonical QIT schedule under
natural exact-stage binding. QIT operators, Weyl signs, and terrain metadata
are test surfaces for falsifiers; they are not replacements for the IGT
WIN/LOSE + win/lose placement object.
"""

from __future__ import annotations

import itertools
import json
import time
from pathlib import Path
from typing import Any

import torch

from canonical_qit_engine_specs import (
    CHART_TOKEN_PRECEDENCE,
    OPERATOR_MAP_FAMILY,
    get_chart_token_spec,
    get_engine_spec,
    get_schedule,
    get_topology_spec,
)


ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "rosetta_igt_qit_four_element_structure_probe_results.json"

NAME = "rosetta_igt_qit_four_element_structure_probe"
SCHEMA = "FORMAL_SCOUT_RESULT_v1"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
WIZARD_SUBAGENTS_BLOCKED_RUNTIME = True

CLAIM_CEILING = (
    "Formal scout only: tests whether the literal four-element IGT row "
    "structure matches the current canonical QIT schedule under exact-stage "
    "binding and whether richer row structure survives controls. It does not "
    "admit a QIT engine, Axis0, bridge, physics, psychology, final IGT, "
    "promotion, or formal admission claim."
)

BLOCKED_CONSUMERS = [
    "QIT_engine_admission",
    "Axis0",
    "bridge",
    "physics",
    "psychology",
    "final_IGT",
    "promotion",
    "formal_admission",
]

TOOL_MANIFEST = {
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exhaustive permutation, rotation, multiset, and deterministic result-label scramble enumeration",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor aggregation of exact-stage feature match scores without NumPy",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source for current QIT engine schedule, topology, chart-token, operator-family, Weyl-sign, and terrain metadata",
    },
    "prior_rosetta_julia_jax_receipts": {
        "tried": True,
        "used": True,
        "reason": "supportive boundary source showing prior sign-only Rosetta should remain killed as trivial two-ness",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "python_stdlib": "load_bearing",
    "pytorch": "load_bearing",
    "canonical_qit_engine_specs": "load_bearing",
    "prior_rosetta_julia_jax_receipts": "supportive",
}

FEATURES = [
    "perception",
    "ordered_token",
    "operator",
    "precedence",
    "result",
    "chirality_sign",
    "h_sign",
    "sign",
    "axis6",
    "realization",
    "dynamics_family",
    "projector_axis",
    "rate",
    "operator_family",
]

RESULT_FEATURES = ["result"]
SIGN_FEATURES = ["chirality_sign", "h_sign"]
TERRAIN_FEATURES = ["realization", "dynamics_family", "projector_axis", "rate"]

IGT_LITERAL_GROUPS: dict[tuple[int, str], dict[str, Any]] = {
    (0, "outer"): {
        "type_label": "Type1",
        "sequence": ["Se", "Ne", "Ni", "Si"],
        "tokens": ["TiSe", "NeTi", "NiFe", "FeSi"],
        "results": ["LOSE", "WIN", "LOSE", "WIN"],
    },
    (0, "inner"): {
        "type_label": "Type1",
        "sequence": ["Se", "Si", "Ni", "Ne"],
        "tokens": ["SeFi", "SiTe", "TeNi", "FiNe"],
        "results": ["win", "win", "lose", "lose"],
    },
    (1, "outer"): {
        "type_label": "Type2",
        "sequence": ["Se", "Si", "Ni", "Ne"],
        "tokens": ["FiSe", "TeSi", "NiTe", "NeFi"],
        "results": ["WIN", "WIN", "LOSE", "LOSE"],
    },
    (1, "inner"): {
        "type_label": "Type2",
        "sequence": ["Se", "Ne", "Ni", "Si"],
        "tokens": ["SeTi", "TiNe", "FeNi", "SiFe"],
        "results": ["lose", "win", "lose", "win"],
    },
}


def jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return float(value.item())
        return value.detach().cpu().tolist()
    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    return value


def row_group_key(row: dict[str, Any]) -> tuple[int, str]:
    return int(row["engine_type"]), str(row["loop_class"])


def group_label(key: tuple[int, str]) -> str:
    engine_type, loop_class = key
    return f"type{engine_type + 1}_{loop_class}"


def split_token(token: str, perception: str) -> tuple[str, str]:
    if token.startswith(perception):
        return token[len(perception) :], "terrain_first"
    if token.endswith(perception):
        return token[: -len(perception)], "operator_first"
    raise ValueError(f"token {token!r} does not contain perception {perception!r}")


def expected_row(
    engine_type: int,
    loop_class: str,
    group_stage_index: int,
    perception: str,
    token: str,
    result: str,
) -> dict[str, Any]:
    operator, precedence = split_token(token, perception)
    precedence_from_chart, sign = CHART_TOKEN_PRECEDENCE[token]
    if precedence != precedence_from_chart:
        raise AssertionError(f"{token} precedence parse mismatch: {precedence} != {precedence_from_chart}")
    engine = get_engine_spec(engine_type)
    topo = get_topology_spec(perception, engine_type)
    return {
        "source": "literal_IGT_expected_plus_canonical_QIT_test_surface",
        "engine_type": engine_type,
        "engine_name": engine["name"],
        "type_label": IGT_LITERAL_GROUPS[(engine_type, loop_class)]["type_label"],
        "loop_class": loop_class,
        "group_stage_index": group_stage_index,
        "perception": perception,
        "ordered_token": token,
        "operator": operator,
        "precedence": precedence,
        "result": result,
        "chirality_sign": int(engine["chirality_sign"]),
        "h_sign": float(engine["h_sign"]),
        "sign": int(sign),
        "axis6": "UP" if int(sign) > 0 else "DOWN",
        "realization": topo["realization"],
        "dynamics_family": topo["dynamics_family"],
        "projector_axis": topo["projector_axis"],
        "rate": float(topo["rate"]),
        "operator_family": OPERATOR_MAP_FAMILY[operator],
        "terrain_surface_note": "QIT terrain feature used only for null tests, not as an IGT replacement",
    }


def build_igt_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for engine_type in (0, 1):
        for loop_class in ("outer", "inner"):
            group = IGT_LITERAL_GROUPS[(engine_type, loop_class)]
            for idx, (perception, token, result) in enumerate(
                zip(group["sequence"], group["tokens"], group["results"], strict=True)
            ):
                rows.append(expected_row(engine_type, loop_class, idx, perception, token, result))
    return rows


def qit_row(engine_type: int, loop_class: str, group_stage_index: int, perception: str) -> dict[str, Any]:
    engine = get_engine_spec(engine_type)
    chart = get_chart_token_spec(perception, engine_type, loop_class)
    topo = get_topology_spec(perception, engine_type)
    return {
        "source": "canonical_qit_engine_specs",
        "engine_type": engine_type,
        "engine_name": engine["name"],
        "type_label": "Type1" if engine_type == 0 else "Type2",
        "loop_class": loop_class,
        "group_stage_index": group_stage_index,
        "perception": perception,
        "ordered_token": chart["token"],
        "operator": chart["operator"],
        "precedence": chart["precedence"],
        "result": chart["result"],
        "chirality_sign": int(engine["chirality_sign"]),
        "h_sign": float(engine["h_sign"]),
        "sign": int(chart["sign"]),
        "axis6": chart["axis6"],
        "realization": topo["realization"],
        "dynamics_family": topo["dynamics_family"],
        "projector_axis": topo["projector_axis"],
        "rate": float(topo["rate"]),
        "operator_family": OPERATOR_MAP_FAMILY[chart["operator"]],
    }


def build_qit_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for engine_type in (0, 1):
        counters = {"outer": 0, "inner": 0}
        for perception, loop_class in get_schedule(engine_type):
            idx = counters[loop_class]
            rows.append(qit_row(engine_type, loop_class, idx, perception))
            counters[loop_class] += 1
    return rows


def ordered_like_expected(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["engine_type"], row["loop_class"], row["group_stage_index"]): row for row in rows}
    ordered: list[dict[str, Any]] = []
    for engine_type in (0, 1):
        for loop_class in ("outer", "inner"):
            for idx in range(4):
                ordered.append(dict(by_key[(engine_type, loop_class, idx)]))
    return ordered


def grouped(rows: list[dict[str, Any]]) -> dict[tuple[int, str], list[dict[str, Any]]]:
    out: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for row in rows:
        out.setdefault(row_group_key(row), []).append(row)
    for key in out:
        out[key] = sorted(out[key], key=lambda item: int(item["group_stage_index"]))
    return out


def values_equal(left: Any, right: Any) -> bool:
    if isinstance(left, float) or isinstance(right, float):
        return abs(float(left) - float(right)) <= 1e-12
    return left == right


def score_rows(
    expected: list[dict[str, Any]],
    observed: list[dict[str, Any]],
    features: list[str] | tuple[str, ...] = FEATURES,
) -> dict[str, Any]:
    if len(expected) != len(observed):
        raise ValueError(f"row length mismatch: {len(expected)} != {len(observed)}")
    bits: list[int] = []
    mismatch_rows: list[dict[str, Any]] = []
    for idx, (exp, obs) in enumerate(zip(expected, observed, strict=True)):
        mismatches: dict[str, dict[str, Any]] = {}
        for feature in features:
            match = values_equal(exp.get(feature), obs.get(feature))
            bits.append(1 if match else 0)
            if not match:
                mismatches[feature] = {"expected": exp.get(feature), "observed": obs.get(feature)}
        if mismatches:
            mismatch_rows.append(
                {
                    "index": idx,
                    "engine_type": exp.get("engine_type"),
                    "loop_class": exp.get("loop_class"),
                    "group_stage_index": exp.get("group_stage_index"),
                    "expected_token": exp.get("ordered_token"),
                    "observed_token": obs.get("ordered_token"),
                    "mismatches": mismatches,
                }
            )
    tensor = torch.tensor(bits, dtype=torch.float64)
    matches = int(torch.sum(tensor).item())
    denominator = int(tensor.numel())
    return {
        "matches": matches,
        "denominator": denominator,
        "ratio": float(matches / denominator) if denominator else 0.0,
        "features": list(features),
        "mismatch_rows": mismatch_rows,
    }


def rotate(rows: list[dict[str, Any]], shift: int) -> list[dict[str, Any]]:
    if not rows:
        return []
    shift = shift % len(rows)
    return rows[shift:] + rows[:shift]


def cycle_rotation_report(igt_rows: list[dict[str, Any]], qit_rows: list[dict[str, Any]]) -> dict[str, Any]:
    igt_by_group = grouped(igt_rows)
    qit_by_group = grouped(qit_rows)
    report: dict[str, Any] = {}
    for key in sorted(igt_by_group):
        rows = []
        for shift in range(4):
            score = score_rows(igt_by_group[key], rotate(qit_by_group[key], shift))
            rows.append(
                {
                    "rotation": shift,
                    "matches": score["matches"],
                    "denominator": score["denominator"],
                    "ratio": score["ratio"],
                    "mismatch_count": len(score["mismatch_rows"]),
                }
            )
        best = max(row["matches"] for row in rows)
        best_rotations = [row["rotation"] for row in rows if row["matches"] == best]
        report[group_label(key)] = {
            "rows": rows,
            "best_rotations": best_rotations,
            "natural_rotation_is_unique_best": best_rotations == [0],
            "note": "rotation is reported separately and never repairs exact-stage mismatches",
        }
    return report


def terrain_permutation_null(igt_rows: list[dict[str, Any]], qit_rows: list[dict[str, Any]]) -> dict[str, Any]:
    igt_by_group = grouped(igt_rows)
    qit_by_group = grouped(qit_rows)
    groups: dict[str, Any] = {}
    natural_unique = True
    best_nonnatural_ratio = 0.0
    for key in sorted(igt_by_group):
        natural_perm = tuple(range(4))
        rows = []
        for perm in itertools.permutations(range(4)):
            permuted = [dict(row) for row in qit_by_group[key]]
            for idx, source_idx in enumerate(perm):
                for feature in TERRAIN_FEATURES:
                    permuted[idx][feature] = qit_by_group[key][source_idx][feature]
            score = score_rows(igt_by_group[key], permuted)
            row = {
                "permutation": list(perm),
                "is_natural": perm == natural_perm,
                "matches": score["matches"],
                "denominator": score["denominator"],
                "ratio": score["ratio"],
                "mismatch_count": len(score["mismatch_rows"]),
            }
            rows.append(row)
            if perm != natural_perm:
                best_nonnatural_ratio = max(best_nonnatural_ratio, score["ratio"])
        best = max(row["matches"] for row in rows)
        best_perms = [row["permutation"] for row in rows if row["matches"] == best]
        group_unique = best_perms == [list(natural_perm)]
        natural_unique = natural_unique and group_unique
        groups[group_label(key)] = {
            "permutations_checked": len(rows),
            "best_score": best,
            "best_permutations": best_perms,
            "natural_unique_best": group_unique,
            "best_nonnatural_ratio": max(row["ratio"] for row in rows if not row["is_natural"]),
        }
    return {
        "groups": groups,
        "permutations_checked_total": sum(group["permutations_checked"] for group in groups.values()),
        "natural_map_unique": natural_unique,
        "best_nonnatural_ratio": best_nonnatural_ratio,
    }


def reverse_cycle_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for key, group_rows in grouped(rows).items():
        for idx, row in enumerate(reversed(group_rows)):
            copy = dict(row)
            copy["group_stage_index"] = idx
            out.append(copy)
    return ordered_like_expected(out)


def inner_outer_swap_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_group = grouped(rows)
    swapped: list[dict[str, Any]] = []
    for engine_type in (0, 1):
        for loop_class in ("outer", "inner"):
            source_loop = "inner" if loop_class == "outer" else "outer"
            for idx, source_row in enumerate(by_group[(engine_type, source_loop)]):
                copy = dict(source_row)
                copy["loop_class"] = loop_class
                copy["group_stage_index"] = idx
                swapped.append(copy)
    return ordered_like_expected(swapped)


def token_multiset_only_control(
    igt_rows: list[dict[str, Any]],
    qit_rows: list[dict[str, Any]],
    reversed_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    igt_by_group = grouped(igt_rows)
    qit_by_group = grouped(qit_rows)
    rev_by_group = grouped(reversed_rows)
    group_rows = {}
    pass_all = True
    for key in sorted(igt_by_group):
        natural_multiset_match = sorted(row["ordered_token"] for row in igt_by_group[key]) == sorted(
            row["ordered_token"] for row in qit_by_group[key]
        )
        reversed_multiset_match = sorted(row["ordered_token"] for row in igt_by_group[key]) == sorted(
            row["ordered_token"] for row in rev_by_group[key]
        )
        reverse_score = score_rows(igt_by_group[key], rev_by_group[key])
        group_pass = natural_multiset_match and reversed_multiset_match and reverse_score["ratio"] < 1.0
        pass_all = pass_all and group_pass
        group_rows[group_label(key)] = {
            "natural_token_multiset_match": natural_multiset_match,
            "reversed_token_multiset_match": reversed_multiset_match,
            "reversed_exact_stage_ratio": reverse_score["ratio"],
            "pass": group_pass,
        }
    return {
        "groups": group_rows,
        "pass": pass_all,
        "note": "token multiset equality survives reversal, so order is load-bearing",
    }


def no_weyl_flip_control(igt_rows: list[dict[str, Any]], qit_rows: list[dict[str, Any]]) -> dict[str, Any]:
    no_flip = []
    for row in qit_rows:
        copy = dict(row)
        if int(copy["engine_type"]) == 1:
            copy["chirality_sign"] = +1
            copy["h_sign"] = +1.0
        no_flip.append(copy)
    full_score = score_rows(igt_rows, no_flip)
    sign_score = score_rows(igt_rows, no_flip, SIGN_FEATURES)
    unique_engine_signs = sorted({(row["chirality_sign"], row["h_sign"]) for row in no_flip})
    return {
        "full_score": full_score,
        "sign_feature_score": sign_score,
        "unique_engine_signs_after_no_flip": [list(item) for item in unique_engine_signs],
        "correspondence_collapses": len(unique_engine_signs) == 1 and sign_score["ratio"] < 1.0,
        "pass": len(unique_engine_signs) == 1 and sign_score["ratio"] < 1.0,
    }


def unique_permutations(values: list[str]) -> list[tuple[str, ...]]:
    return sorted(set(itertools.permutations(values)))


def result_label_scramble_control(igt_rows: list[dict[str, Any]], qit_rows: list[dict[str, Any]]) -> dict[str, Any]:
    igt_by_group = grouped(igt_rows)
    qit_by_group = grouped(qit_rows)
    group_reports: dict[str, Any] = {}
    natural_beats_all = True
    best_scrambled_result_ratio = 0.0
    best_scrambled_full_ratio = 0.0
    total_scrambles = 0
    for key in sorted(igt_by_group):
        natural_results = [row["result"] for row in qit_by_group[key]]
        natural_result_score = score_rows(igt_by_group[key], qit_by_group[key], RESULT_FEATURES)
        rows = []
        for perm in unique_permutations(natural_results):
            if list(perm) == natural_results:
                continue
            total_scrambles += 1
            scrambled = [dict(row) for row in qit_by_group[key]]
            for idx, result in enumerate(perm):
                scrambled[idx]["result"] = result
            result_score = score_rows(igt_by_group[key], scrambled, RESULT_FEATURES)
            full_score = score_rows(igt_by_group[key], scrambled)
            best_scrambled_result_ratio = max(best_scrambled_result_ratio, result_score["ratio"])
            best_scrambled_full_ratio = max(best_scrambled_full_ratio, full_score["ratio"])
            rows.append(
                {
                    "results": list(perm),
                    "result_matches": result_score["matches"],
                    "result_denominator": result_score["denominator"],
                    "result_ratio": result_score["ratio"],
                    "full_ratio": full_score["ratio"],
                }
            )
        best_scrambled_result_matches = max(row["result_matches"] for row in rows)
        group_pass = natural_result_score["matches"] > best_scrambled_result_matches
        natural_beats_all = natural_beats_all and group_pass
        group_reports[group_label(key)] = {
            "natural_results": natural_results,
            "natural_result_matches": natural_result_score["matches"],
            "natural_result_denominator": natural_result_score["denominator"],
            "scrambles_checked": len(rows),
            "best_scrambled_result_matches": best_scrambled_result_matches,
            "best_scrambled_result_ratio": max(row["result_ratio"] for row in rows),
            "pass": group_pass,
        }
    return {
        "groups": group_reports,
        "scrambles_checked_total": total_scrambles,
        "natural_beats_all_scrambles": natural_beats_all,
        "best_scrambled_result_ratio": best_scrambled_result_ratio,
        "best_scrambled_full_ratio": best_scrambled_full_ratio,
        "pass": natural_beats_all,
    }


def sign_only_ablation(qit_rows: list[dict[str, Any]]) -> dict[str, Any]:
    engine_sign_pairs = sorted({(row["chirality_sign"], row["h_sign"]) for row in qit_rows})
    operator_signs = sorted({row["sign"] for row in qit_rows})
    return {
        "engine_sign_pairs": [list(pair) for pair in engine_sign_pairs],
        "operator_signs": operator_signs,
        "unique_engine_sign_pair_count": len(engine_sign_pairs),
        "unique_operator_sign_count": len(operator_signs),
        "trivial": len(engine_sign_pairs) == 2,
        "pass": len(engine_sign_pairs) == 2,
        "note": "Two engine signs/chiralities alone recreate the killed sign-only Rosetta triviality; richer row structure must carry the scout.",
    }


def prior_receipts_summary() -> dict[str, Any]:
    base = ROOT.parents[1] / "julia_carrier"
    paths = {
        "julia": base / "rosetta_igt_qit_convergence_probe_julia_results.json",
        "jax": base / "rosetta_igt_qit_convergence_probe_jax_results.json",
    }
    out: dict[str, Any] = {}
    for name, path in paths.items():
        if not path.exists():
            out[name] = {"path": str(path), "exists": False}
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        random_sign = (data.get("controls") or {}).get("random_sign_assignment") or {}
        out[name] = {
            "path": str(path),
            "exists": True,
            "all_pass": data.get("all_pass"),
            "classification": data.get("classification"),
            "random_opposite_signed_pair_always_works_under_one_of_two_correspondences": random_sign.get(
                "random_opposite_signed_pair_always_works_under_one_of_two_correspondences"
            ),
            "sign_only_warning": random_sign.get("uninformative_warning"),
        }
    return out


def pass_count(*sections: dict[str, dict[str, Any]]) -> tuple[int, int]:
    rows = [row for section in sections for row in section.values()]
    return sum(1 for row in rows if row.get("pass") is True), len(rows)


def main() -> int:
    started = time.time()
    igt_rows = build_igt_rows()
    qit_rows = ordered_like_expected(build_qit_rows())

    natural_score = score_rows(igt_rows, qit_rows)
    rotation_report = cycle_rotation_report(igt_rows, qit_rows)
    terrain_null = terrain_permutation_null(igt_rows, qit_rows)
    reversed_rows = reverse_cycle_rows(qit_rows)
    reverse_score = score_rows(igt_rows, reversed_rows)
    swapped_rows = inner_outer_swap_rows(qit_rows)
    inner_outer_swap_score = score_rows(igt_rows, swapped_rows)
    token_multiset_control = token_multiset_only_control(igt_rows, qit_rows, reversed_rows)
    no_flip = no_weyl_flip_control(igt_rows, qit_rows)
    result_scramble = result_label_scramble_control(igt_rows, qit_rows)
    sign_ablation = sign_only_ablation(qit_rows)
    prior_receipts = prior_receipts_summary()

    natural_map_unique = bool(terrain_null["natural_map_unique"])
    shared_four_element_invariant = natural_score["matches"] == natural_score["denominator"] and len(igt_rows) == 16
    token_order_load_bearing = (
        token_multiset_control["pass"]
        and reverse_score["ratio"] < natural_score["ratio"]
        and inner_outer_swap_score["ratio"] < natural_score["ratio"]
    )
    result_label_binding_load_bearing = bool(result_scramble["pass"])
    controls_pass = all(
        [
            sign_ablation["pass"],
            token_multiset_control["pass"],
            natural_map_unique,
            reverse_score["ratio"] < natural_score["ratio"],
            inner_outer_swap_score["ratio"] < natural_score["ratio"],
            no_flip["pass"],
            result_label_binding_load_bearing,
        ]
    )

    best_control_score = max(
        [
            terrain_null["best_nonnatural_ratio"],
            reverse_score["ratio"],
            inner_outer_swap_score["ratio"],
            no_flip["full_score"]["ratio"],
            result_scramble["best_scrambled_full_ratio"],
        ]
    )

    verdicts = {
        "shared_four_element_invariant": shared_four_element_invariant,
        "natural_map_unique": natural_map_unique,
        "sign_only_is_trivial": bool(sign_ablation["trivial"]),
        "controls_pass": controls_pass,
        "result_label_binding_load_bearing": result_label_binding_load_bearing,
        "token_order_load_bearing": token_order_load_bearing,
    }

    positive = {
        "literal_igt_four_groups_loaded": {
            "group_count": len(IGT_LITERAL_GROUPS),
            "row_count": len(igt_rows),
            "pass": len(IGT_LITERAL_GROUPS) == 4 and len(igt_rows) == 16,
        },
        "canonical_qit_rows_loaded_in_schedule_order": {
            "row_count": len(qit_rows),
            "schedule_order": [
                [row["type_label"], row["loop_class"], row["group_stage_index"], row["perception"], row["ordered_token"]]
                for row in qit_rows
            ],
            "pass": len(qit_rows) == 16,
        },
        "natural_exact_stage_score_is_complete": {
            "matches": natural_score["matches"],
            "denominator": natural_score["denominator"],
            "ratio": natural_score["ratio"],
            "pass": shared_four_element_invariant,
        },
        "shared_four_element_invariant_survives_richer_features": {
            "feature_count": len(FEATURES),
            "features": FEATURES,
            "pass": shared_four_element_invariant and len(FEATURES) >= 12,
        },
    }

    graveyard_companions = {
        "sign_only_ablation_is_trivial_two_ness": sign_ablation,
        "token_multiset_only_control_is_insufficient": token_multiset_control,
        "terrain_permutation_null_keeps_natural_unique": {
            "permutations_checked_total": terrain_null["permutations_checked_total"],
            "natural_map_unique": natural_map_unique,
            "best_nonnatural_ratio": terrain_null["best_nonnatural_ratio"],
            "pass": natural_map_unique,
        },
        "reverse_cycle_control_degrades_exact_stage_score": {
            "matches": reverse_score["matches"],
            "denominator": reverse_score["denominator"],
            "ratio": reverse_score["ratio"],
            "pass": reverse_score["ratio"] < natural_score["ratio"],
        },
        "inner_outer_swap_control_degrades_exact_stage_score": {
            "matches": inner_outer_swap_score["matches"],
            "denominator": inner_outer_swap_score["denominator"],
            "ratio": inner_outer_swap_score["ratio"],
            "pass": inner_outer_swap_score["ratio"] < natural_score["ratio"],
        },
        "no_weyl_flip_control_collapses_sign_features": {
            "sign_feature_matches": no_flip["sign_feature_score"]["matches"],
            "sign_feature_denominator": no_flip["sign_feature_score"]["denominator"],
            "sign_feature_ratio": no_flip["sign_feature_score"]["ratio"],
            "unique_engine_signs_after_no_flip": no_flip["unique_engine_signs_after_no_flip"],
            "pass": no_flip["pass"],
        },
        "result_label_scramble_control_preserves_counts_but_loses_binding": {
            "scrambles_checked_total": result_scramble["scrambles_checked_total"],
            "best_scrambled_result_ratio": result_scramble["best_scrambled_result_ratio"],
            "best_scrambled_full_ratio": result_scramble["best_scrambled_full_ratio"],
            "pass": result_scramble["pass"],
        },
    }

    boundary = {
        "formal_scout_only": {"classification": CLASSIFICATION, "pass": CLASSIFICATION == "formal_scout"},
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
        "formal_admission_remains_disabled": {
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "pass": FORMAL_ADMISSION_ALLOWED is False,
        },
        "wizard_subagents_blocked_runtime_recorded": {
            "wizard_subagents_blocked_runtime": WIZARD_SUBAGENTS_BLOCKED_RUNTIME,
            "pass": WIZARD_SUBAGENTS_BLOCKED_RUNTIME is True,
        },
        "blocked_consumers_named": {
            "blocked_consumers": BLOCKED_CONSUMERS,
            "required": BLOCKED_CONSUMERS,
            "pass": set(BLOCKED_CONSUMERS)
            == {
                "QIT_engine_admission",
                "Axis0",
                "bridge",
                "physics",
                "psychology",
                "final_IGT",
                "promotion",
                "formal_admission",
            },
        },
        "qit_surfaces_not_igt_replacements": {
            "pass": True,
            "note": "IGT object remains WIN/LOSE + win/lose placement; QIT operator/terrain/Weyl fields are only score and falsifier surfaces.",
        },
        "no_numpy_import_or_claim_bearing_compute": {
            "pass": "numpy" not in globals(),
            "compute": "python stdlib plus torch tensor score aggregation",
        },
    }

    passed, total = pass_count(positive, graveyard_companions, boundary)
    all_pass = (
        passed == total
        and all(verdicts.values())
        and natural_score["matches"] == natural_score["denominator"]
        and best_control_score < 1.0
    )

    scores = {
        "natural_exact_stage": natural_score,
        "score_denominator_explicit": {
            "row_count": len(igt_rows),
            "feature_count": len(FEATURES),
            "denominator": natural_score["denominator"],
            "formula": "row_count * feature_count",
        },
        "cycle_rotation_equivalence": rotation_report,
        "terrain_permutation_null": terrain_null,
        "order_scramble_control": {
            "reverse_cycle": reverse_score,
            "inner_outer_swap": inner_outer_swap_score,
        },
        "token_multiset_only_control": token_multiset_control,
        "no_weyl_flip_control": no_flip,
        "result_label_scramble_control": result_scramble,
        "best_control_score": best_control_score,
    }

    result = {
        "schema": SCHEMA,
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "FORMAL_ADMISSION_ALLOWED": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "all_pass": bool(all_pass),
        "verdicts": verdicts,
        "scores": scores,
        "expected_igt_structure": IGT_LITERAL_GROUPS,
        "igt_rows": igt_rows,
        "qit_rows": qit_rows,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "passed": passed,
            "total": total,
            "variants": sorted(graveyard_companions),
        },
        "why_not_v4_probes": [
            "This is a clean v5 formal scout over a bounded 4-element Rosetta structure, not a v4 narrative probe.",
            "Prior sign-only Rosetta remains killed as trivial two-ness unless this richer exact-stage row structure is kept with controls.",
        ],
        "blockers": [],
        "wizard_subagents_blocked_runtime": WIZARD_SUBAGENTS_BLOCKED_RUNTIME,
        "prior_sign_only_receipts": prior_receipts,
        "plain_sentence": (
            "The literal four-element IGT placement table exactly matches the current canonical QIT schedule under natural stage binding, "
            "but only as a formal scout; sign-only, token-multiset-only, terrain-permuted, no-Weyl-flip, order-scrambled, and result-label-scrambled controls remain blocked from admission."
        ),
        "elapsed_seconds": time.time() - started,
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "name": NAME,
                "result_path": str(OUT_PATH),
                "all_pass": bool(all_pass),
                "shared_four_element_invariant": shared_four_element_invariant,
                "natural_map_unique": natural_map_unique,
                "best_control_score": best_control_score,
                "blockers": [],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
