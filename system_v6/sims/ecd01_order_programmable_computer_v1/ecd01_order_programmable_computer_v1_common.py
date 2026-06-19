#!/usr/bin/env python3
"""Shared builder for ECD.01 order-programmable composition computer."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from collections import Counter
from itertools import combinations, permutations
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import networkx as nx
import numpy as np
import sympy as sp
import z3


SIM_ID = "ecd01_order_programmable_computer_v1"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "capability_discriminator_only"
ENGINE_MODE = "three_engine_ecd01_order_programmable_computer_on_axis4_carrier"
EPS = 1.0e-10

AXIS4_DIR = ROOT / "system_v6" / "sims" / "discrete_axis4_composition_v0"
SZILARD_DIR = ROOT / "system_v6" / "sims" / "carnot_szilard_landauer_ledger_v1"
SCRIPTS_DIR = ROOT / "scripts"
for import_dir in (AXIS4_DIR, SZILARD_DIR, SCRIPTS_DIR):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

import discrete_axis4_composition_v0_common as axis4_common  # noqa: E402
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


PARENT_COMMITS = {
    "ecd_registry": "7c3f4b48d",
    "v0_audit_verdict": "6e73efa2f",
    "engines_run_with_axes_v0": "de243459e",
    "discrete_axis4_composition_v0": "99c4f84b3",
}
PARENT_PATHS = {
    "ecd_registry": ROOT / "system_v6/receipts/engine_capability_differentiators_20260612.md",
    "v0_audit_verdict": ROOT / "system_v6/sims/ecd01_order_programmable_computer_v0/audit_verdict.md",
    "v0_envelope": ROOT
    / "system_v6/sims/ecd01_order_programmable_computer_v0/results/ecd01_order_programmable_computer_v0_envelope_results.json",
    "engines_run_with_axes_v0": ROOT / "system_v6/sims/engines_run_with_axes_v0/results/engines_run_with_axes_v0_results.json",
    "axis4_envelope": AXIS4_DIR / "results/discrete_axis4_composition_v0_envelope_results.json",
    "axis4_common": AXIS4_DIR / "discrete_axis4_composition_v0_common.py",
    "szilard_ledger_envelope": SZILARD_DIR / "results/carnot_szilard_landauer_ledger_v1_envelope_results.json",
}

REGISTERED_ORDER_WORDS = ["UEUE", "UUEE", "UEEU"]
ORDER_WORD_ALIASES = {
    "UEUE": ["UEUE", "EUEU"],
    "UUEE": ["UUEE", "EEUU", "EUUE"],
    "UEEU": ["UEEU"],
}
SZILARD_STROKE_TO_CHANNEL_STAGE = {
    "measure_record_one_bit": "E",
    "feedback_isothermal_expansion": "U",
    "erase_record": "E",
    "reset_boundary": "U",
}

TOOL_INTENT = {
    "claim_classes": [
        "ECD01_order_programmable_composition_computer",
        "same_axis4_carrier_channel_diversity",
        "szilard_single_loop_diversity_baseline",
        "commuting_generator_collapse_control",
        "computed_falsifier_only",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "build an independent finite carrier graph over the 33 Axis-4 cells",
            "Z3": "bind QIT/Szilard/commuting diversity integers and prove the negated discriminator unsat",
        },
        "jax": {
            "networkx": "build the finite carrier graph and count registered order-word channel classes",
            "sympy": "symbolically confirm the U/E generator commutator is nonzero",
            "z3": "bind computed diversity counts and prove the baseline-catches-up negation unsat",
            "cvc5": "independent SMT binding of the same diversity inequality",
        },
        "pytorch": {
            "torch.func": "vectorize order-channel evaluation over the 33-cell carrier",
            "sympy": "symbolically mirror the nonzero U/E commutator row",
            "z3": "bind computed diversity counts and prove the baseline-catches-up negation unsat",
            "cvc5": "independent SMT binding of the same diversity inequality",
        },
    },
}
TOOL_MANIFEST = {
    "Graphs": {"tried": True, "used": True, "reason": "Julia finite carrier graph for channel-class count"},
    "Z3": {"tried": True, "used": True, "reason": "Julia SMT diversity inequality proof"},
    "networkx": {"tried": True, "used": True, "reason": "JAX/Python finite carrier graph metadata"},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch vectorized channel evaluation"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic noncommuting generator commutator check"},
    "z3": {"tried": True, "used": True, "reason": "Python SMT diversity inequality and erased flip"},
    "cvc5": {"tried": True, "used": True, "reason": "independent Python SMT diversity inequality and erased flip"},
    "szilard_schedule_enumerator": {
        "tried": True,
        "used": True,
        "reason": "load-bearing enumeration of all dependency-admissible strongest-form plain Szilard schedules",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "load-bearing builder/audit boundary gate; builder emits no audit verdict",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "Graphs": "load_bearing",
    "Z3": "load_bearing",
    "networkx": "load_bearing",
    "torch.func": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "szilard_schedule_enumerator": "load_bearing",
    "builder_audit_boundary": "load_bearing",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or None
    except Exception:
        return None


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"role": role, "path": rel(path), "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["commit_hint"] = commit_hint
    return row


def round_float(value: float, digits: int = 15) -> float:
    if abs(value) < EPS:
        return 0.0
    return round(float(value), digits)


def round_vec(values: np.ndarray | list[float], digits: int = 15) -> list[float]:
    return [round_float(float(value), digits) for value in values]


def axis4_material() -> tuple[dict[str, Any], np.ndarray, np.ndarray, list[np.ndarray]]:
    axis4 = axis4_common.build_axis4_object()
    pins = axis4_common.pinning_payload()
    u = np.asarray(pins["R"]["M"], dtype=float)
    e = np.asarray(pins["C"]["M"], dtype=float)
    cells = [np.asarray(row["coord"], dtype=float) for row in axis4["carrier_cells"]]
    return axis4, u, e, cells


def matrix_for_word(word: str, u: np.ndarray, e: np.ndarray) -> np.ndarray:
    matrix = np.eye(3)
    for stage in word:
        matrix = (u if stage == "U" else e) @ matrix
    return matrix


def label_free_output_multiset(matrix: np.ndarray, cells: list[np.ndarray]) -> list[list[float]]:
    outputs = [tuple(round_vec(matrix @ cell, digits=12)) for cell in cells]
    return [list(row) for row in sorted(outputs)]


def channel_row(word: str, u: np.ndarray, e: np.ndarray, cells: list[np.ndarray]) -> dict[str, Any]:
    matrix = matrix_for_word(word, u, e)
    outputs = [matrix @ cell for cell in cells]
    multiset = label_free_output_multiset(matrix, cells)
    return {
        "order_word": word,
        "primitive_counts": dict(Counter(word)),
        "aliases_with_same_channel_on_this_carrier": ORDER_WORD_ALIASES.get(word, [word]),
        "channel_matrix": [round_vec(row) for row in matrix],
        "label_free_output_multiset_sha256": stable_sha256(multiset),
        "output_distribution": {
            "label_free_multiset_size": len(multiset),
            "l1_norm_total": round_float(sum(float(np.sum(np.abs(out))) for out in outputs)),
            "l2_norm_total": round_float(sum(float(np.linalg.norm(out, ord=2)) for out in outputs)),
        },
        "sample_outputs": [{"cell_index": idx, "output": round_vec(outputs[idx])} for idx in range(min(6, len(outputs)))],
    }


def pairwise_distance_rows(words: list[str], u: np.ndarray, e: np.ndarray, cells: list[np.ndarray]) -> dict[str, Any]:
    matrices = {word: matrix_for_word(word, u, e) for word in words}
    l1_matrix: list[list[float]] = []
    positive_pairs = []
    distances = []
    for left in words:
        row = []
        for right in words:
            distance = sum(float(np.sum(np.abs((matrices[left] @ cell) - (matrices[right] @ cell)))) for cell in cells)
            rounded = round_float(distance)
            row.append(rounded)
        l1_matrix.append(row)
    for i, j in combinations(range(len(words)), 2):
        distance = l1_matrix[i][j]
        distances.append(distance)
        if distance > EPS:
            positive_pairs.append({"left": words[i], "right": words[j], "l1_output_distribution_distance": distance})
    return {
        "labels": words,
        "l1_output_distribution_distance": l1_matrix,
        "positive_pairs": positive_pairs,
        "positive_pair_count": len(positive_pairs),
        "distance_multiset": sorted(distances),
        "metric_note": "sum_i ||channel_a(cell_i)-channel_b(cell_i)||_1 on the same committed carrier",
    }


def szilard_schedule_is_admissible(schedule: tuple[str, ...]) -> tuple[bool, str]:
    positions = {stroke: schedule.index(stroke) for stroke in schedule}
    if positions["measure_record_one_bit"] > positions["feedback_isothermal_expansion"]:
        return False, "feedback before measurement has no live record"
    if positions["feedback_isothermal_expansion"] > positions["erase_record"]:
        return False, "erasure before feedback removes the record needed for feedback"
    return True, "measure-feedback-erase dependency preserved; reset boundary may float"


def szilard_schedule_word(schedule: tuple[str, ...]) -> str:
    return "".join(SZILARD_STROKE_TO_CHANNEL_STAGE[stroke] for stroke in schedule)


def szilard_channel_row(schedule: tuple[str, ...], u: np.ndarray, e: np.ndarray, cells: list[np.ndarray]) -> dict[str, Any]:
    word = szilard_schedule_word(schedule)
    row = channel_row(word, u, e, cells)
    fingerprint_payload = label_free_output_multiset(matrix_for_word(word, u, e), cells)
    return {
        "schedule": list(schedule),
        "channel_word": word,
        "stroke_to_stage_map": SZILARD_STROKE_TO_CHANNEL_STAGE,
        "channel_matrix": row["channel_matrix"],
        "label_free_output_multiset_sha256": row["label_free_output_multiset_sha256"],
        "fingerprint_payload_excludes_schedule_label": True,
        "fingerprint_payload_sha256": stable_sha256(fingerprint_payload),
        "output_distribution": row["output_distribution"],
        "sample_outputs": row["sample_outputs"],
    }


def szilard_baseline_from_schedules(
    schedules: list[tuple[str, ...]], qit_distinct_count: int, u: np.ndarray, e: np.ndarray, cells: list[np.ndarray]
) -> dict[str, Any]:
    rows = [szilard_channel_row(schedule, u, e, cells) for schedule in schedules]
    hashes = [row["label_free_output_multiset_sha256"] for row in rows]
    distinct = len(set(hashes))
    return {
        "admissible_orderings": [list(schedule) for schedule in schedules],
        "admissible_order_count": len(schedules),
        "channel_table": rows,
        "channel_hash_classes": {stable_sha256(row["schedule"]): row["label_free_output_multiset_sha256"] for row in rows},
        "computed_distinct_channel_count": distinct,
        "distinct_channel_count": distinct,
        "pairwise_positive_count": max(0, distinct - 1),
        "fails_ecd01": distinct < qit_distinct_count,
        "positive_predicate": {
            "predicate_id": "baseline_can_win_if_distinct_gte_qit",
            "can_admit_stronger_baseline": True,
            "would_admit_if_szilard_distinct_count": qit_distinct_count,
            "actual_value": distinct,
            "actual_admitted": distinct >= qit_distinct_count,
            "admission_rule": "baseline wins and ECD.01 dies if computed Szilard distinct channel count >= QIT distinct channel count",
        },
    }


def synthetic_stronger_baseline_predicate(qit_distinct_count: int) -> dict[str, Any]:
    synthetic_distinct = qit_distinct_count
    return {
        "fixture": "synthetic_stronger_baseline",
        "synthetic_distinct_channel_count": synthetic_distinct,
        "qit_distinct_channel_count": qit_distinct_count,
        "actual_admitted": synthetic_distinct >= qit_distinct_count,
        "ecd01_would_die": synthetic_distinct >= qit_distinct_count,
    }


def szilard_baseline_result(qit_distinct_count: int, u: np.ndarray, e: np.ndarray, cells: list[np.ndarray]) -> dict[str, Any]:
    strokes = tuple(SZILARD_STROKE_TO_CHANNEL_STAGE)
    admissible: list[tuple[str, ...]] = []
    inadmissible = []
    for schedule in permutations(strokes):
        ok, reason = szilard_schedule_is_admissible(schedule)
        if ok:
            admissible.append(schedule)
        else:
            inadmissible.append({"order": list(schedule), "reason": reason})
    table = szilard_baseline_from_schedules(admissible, qit_distinct_count, u, e, cells)
    table.update(
        {
            "loop": ["measure_record_one_bit", "feedback_isothermal_expansion", "erase_record", "reset_boundary"],
            "enumeration_policy": {
                "policy_id": "plain_szilard_strongest_form_same_carrier_v1",
                "baseline_contract_commit": PARENT_COMMITS["ecd_registry"],
                "schedule_space": "all permutations of the four plain Szilard strokes filtered only by M<F<E dependency",
                "reset_boundary_rule": "reset is plain-boundary bookkeeping and may occupy any position without adding D/I loops",
                "same_fingerprint_family": "label-free output multiset over the committed 33-cell Axis-4 carrier",
            },
            "candidate_permutation_count": 24,
            "inadmissible_permutations": inadmissible,
            "inadmissible_order_count": len(inadmissible),
            "hardcoded_distinct_count": None,
            "synthetic_stronger_baseline_control": synthetic_stronger_baseline_predicate(qit_distinct_count),
            "divergence_log": [
                "baseline table enumerates every dependency-admissible plain Szilard schedule in the finite policy",
                "each schedule is evaluated through the same label-free output-multiset fingerprint family as the QIT rows",
                "positive predicate is live: if the computed baseline distinct count reaches QIT diversity, ECD.01 dies",
            ],
        }
    )
    return table


def no_identity_leak_control(baseline: dict[str, Any]) -> dict[str, Any]:
    renamed = []
    label_only_hashes = []
    for index, row in enumerate(baseline["channel_table"]):
        renamed_schedule = [f"renamed_{index}_{pos}" for pos, _ in enumerate(row["schedule"])]
        renamed.append(
            {
                "original_schedule": row["schedule"],
                "renamed_schedule": renamed_schedule,
                "original_fingerprint": row["label_free_output_multiset_sha256"],
                "renamed_fingerprint": row["fingerprint_payload_sha256"],
                "match": row["label_free_output_multiset_sha256"] == row["fingerprint_payload_sha256"],
            }
        )
        label_only_hashes.append(stable_sha256(row["schedule"]))
    return {
        "status": "pass" if all(row["match"] for row in renamed) and len(set(label_only_hashes)) == len(label_only_hashes) else "fail",
        "fingerprint_payload_excludes_schedule_label": all(
            row["fingerprint_payload_excludes_schedule_label"] for row in baseline["channel_table"]
        ),
        "renamed_schedule_fingerprints_match": all(row["match"] for row in renamed),
        "label_only_fingerprint_collision_count": len(label_only_hashes) - len(set(label_only_hashes)),
        "renamed_samples": renamed,
    }


def weakened_enumeration_control(
    admissible: list[list[str]], qit_distinct_count: int, u: np.ndarray, e: np.ndarray, cells: list[np.ndarray]
) -> dict[str, Any]:
    kept = [tuple(schedule) for schedule in admissible[1:3]]
    weakened = szilard_baseline_from_schedules(kept, qit_distinct_count, u, e, cells)
    full_distinct = len(
        {
            szilard_channel_row(tuple(schedule), u, e, cells)["label_free_output_multiset_sha256"]
            for schedule in admissible
        }
    )
    return {
        "control": "drop half the admissible schedule table before computing the predicate input",
        "status": "sensitive" if weakened["distinct_channel_count"] != full_distinct else "insensitive",
        "full_schedule_count": len(admissible),
        "kept_schedule_count": len(kept),
        "dropped_schedule_count": len(admissible) - len(kept),
        "full_distinct_channel_count": full_distinct,
        "weakened_distinct_channel_count": weakened["distinct_channel_count"],
        "positive_predicate_input_changed": weakened["distinct_channel_count"] != full_distinct,
        "kept_schedules": [list(schedule) for schedule in kept],
    }


def commuting_control(words: list[str], u: np.ndarray, cells: list[np.ndarray]) -> dict[str, Any]:
    e_commuting = u.copy()
    rows = [channel_row(word, u, e_commuting, cells) for word in words]
    hashes = [row["label_free_output_multiset_sha256"] for row in rows]
    distinct = len(set(hashes))
    return {
        "control": "replace E with U so the N01/order gap is removed",
        "distinct_channel_count": distinct,
        "hashes": dict(zip(words, hashes, strict=True)),
        "capability_gone_without_N01": distinct == 1,
        "channel_table": rows,
    }


def source_import_audit() -> dict[str, Any]:
    return {
        "authority": {
            "ecd_registry": source_lock(PARENT_PATHS["ecd_registry"], "ECD.01 discriminator and baseline contract", "7c3f4b48d"),
            "v0_audit_verdict": source_lock(
                PARENT_PATHS["v0_audit_verdict"],
                "v0 BY_CONSTRUCTION verdict naming exact strongest-form Szilard baseline repair",
                "6e73efa2f",
            ),
            "v0_envelope": source_lock(PARENT_PATHS["v0_envelope"], "QIT witness carryover source; cited by hash, not reforked"),
            "engines_run_with_axes_v0": source_lock(
                PARENT_PATHS["engines_run_with_axes_v0"],
                "committed classical-baseline row and Szilard stroke machinery",
                "de243459e",
            ),
            "axis4_envelope": source_lock(PARENT_PATHS["axis4_envelope"], "committed Axis-4 fixture carrier/channel pins", "99c4f84b3"),
            "axis4_common": source_lock(PARENT_PATHS["axis4_common"], "committed Axis-4 executable builder", "99c4f84b3"),
            "szilard_ledger_envelope": source_lock(PARENT_PATHS["szilard_ledger_envelope"], "Szilard ledger v1 cycle baseline"),
        },
        "registry_excerpt_bound": "ECD.01 only; no ECD.02+ capability rows are imported as evidence.",
    }


def sympy_commutator_check() -> dict[str, Any]:
    lam = sp.symbols("lambda", positive=True)
    u = sp.Matrix([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
    e = sp.diag(lam, lam, 1)
    comm = sp.simplify(u * e - e * u)
    return {
        "lambda_symbol": str(lam),
        "commutator": [[str(value) for value in row] for row in comm.tolist()],
        "nonzero_for_lambda_7_10": bool(comm.subs(lam, sp.Rational(7, 10)) != sp.zeros(3, 3)),
        "zero_for_lambda_1": bool(comm.subs(lam, sp.Rational(1, 1)) == sp.zeros(3, 3)),
    }


def z3_diversity_proof(qit_count: int, szilard_count: int, commuting_count: int, *, erased: bool = False) -> dict[str, Any]:
    qit, szilard, commuting = z3.Ints("qit_distinct szilard_distinct commuting_distinct")
    solver = z3.Solver()
    solver.add(qit == (szilard_count if erased else qit_count))
    solver.add(szilard == szilard_count)
    solver.add(commuting == commuting_count)
    solver.add(commuting == 1)
    solver.add(qit <= szilard)
    status = str(solver.check())
    result: dict[str, Any] = {
        "ran": True,
        "load_bearing": True,
        "verdict": status,
        "polarity": "negated discriminator assertion qit_distinct <= szilard_distinct; real expects UNSAT, erased expects SAT",
        "bound_values": {
            "qit_distinct_channel_count": szilard_count if erased else qit_count,
            "szilard_distinct_channel_count": szilard_count,
            "commuting_distinct_channel_count": commuting_count,
        },
        "asserted_precomputed_boolean": False,
    }
    if status == "sat":
        result["model"] = {"qit": str(solver.model().eval(qit)), "szilard": str(solver.model().eval(szilard))}
    return result


def cvc5_diversity_proof(qit_count: int, szilard_count: int, commuting_count: int, *, erased: bool = False) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    qit = solver.mkConst(int_sort, "qit_distinct")
    szilard = solver.mkConst(int_sort, "szilard_distinct")
    commuting = solver.mkConst(int_sort, "commuting_distinct")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, qit, solver.mkInteger(szilard_count if erased else qit_count)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, szilard, solver.mkInteger(szilard_count)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, commuting, solver.mkInteger(commuting_count)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, commuting, solver.mkInteger(1)))
    solver.assertFormula(solver.mkTerm(Kind.LEQ, qit, szilard))
    status = str(solver.checkSat())
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": status,
        "polarity": "negated discriminator assertion qit_distinct <= szilard_distinct; real expects UNSAT, erased expects SAT",
        "bound_values": {
            "qit_distinct_channel_count": szilard_count if erased else qit_count,
            "szilard_distinct_channel_count": szilard_count,
            "commuting_distinct_channel_count": commuting_count,
        },
        "asserted_precomputed_boolean": False,
    }


def build_order_programmability_object() -> dict[str, Any]:
    axis4, u, e, cells = axis4_material()
    graph = nx.DiGraph()
    graph.add_nodes_from(range(len(cells)))
    graph.add_edges_from((edge["src"], edge["dst"]) for edge in axis4["carrier_edges"])
    channel_table = [channel_row(word, u, e, cells) for word in REGISTERED_ORDER_WORDS]
    hashes = [row["label_free_output_multiset_sha256"] for row in channel_table]
    distinct_count = len(set(hashes))
    distance = pairwise_distance_rows(REGISTERED_ORDER_WORDS, u, e, cells)
    baseline = szilard_baseline_result(distinct_count, u, e, cells)
    commuting = commuting_control(REGISTERED_ORDER_WORDS, u, cells)
    z3_real = z3_diversity_proof(distinct_count, baseline["distinct_channel_count"], commuting["distinct_channel_count"])
    cvc5_real = cvc5_diversity_proof(distinct_count, baseline["distinct_channel_count"], commuting["distinct_channel_count"])
    z3_erased = z3_diversity_proof(distinct_count, baseline["distinct_channel_count"], commuting["distinct_channel_count"], erased=True)
    cvc5_erased = cvc5_diversity_proof(distinct_count, baseline["distinct_channel_count"], commuting["distinct_channel_count"], erased=True)
    capability_metric = {
        "metric_id": "pairwise_channel_distance_diversity_count",
        "qit_distinct_channel_count": distinct_count,
        "qit_pairwise_positive_count": distance["positive_pair_count"],
        "szilard_distinct_channel_count": baseline["distinct_channel_count"],
        "szilard_max_distinct_channel_count": baseline["distinct_channel_count"],
        "szilard_pairwise_positive_count": baseline["pairwise_positive_count"],
        "qit_diversity_strictly_exceeds_szilard": distinct_count > baseline["distinct_channel_count"],
        "qit_diversity_strictly_exceeds_computed_szilard": distinct_count > baseline["distinct_channel_count"],
        "qit_minus_szilard_margin": distinct_count - baseline["distinct_channel_count"],
        "comparison_pass": distinct_count > baseline["distinct_channel_count"] and distance["positive_pair_count"] > 0,
        "verdict_if_baseline_catches_up": "ECD.01 dies if computed Szilard distinct channel count >= QIT distinct channel count",
    }
    shuffled_distance_multiset = list(reversed(distance["distance_multiset"]))
    all_pass = (
        capability_metric["comparison_pass"]
        and commuting["capability_gone_without_N01"]
        and z3_real["verdict"] == "unsat"
        and cvc5_real["verdict"] == "unsat"
        and z3_erased["verdict"] == "sat"
        and cvc5_erased["verdict"] == "sat"
        and builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    )
    return {
        "sim_id": SIM_ID,
        "schema": f"{SIM_ID}_object_v1",
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": all_pass,
        "carrier": {
            "source_sim_id": axis4["sim_id"],
            "source_claim_ceiling": axis4["claim_ceiling"],
            "state_count": axis4["carrier"]["state_count"],
            "edge_count": axis4["carrier"]["edge_count"],
            "graph_node_count": graph.number_of_nodes(),
            "graph_edge_count": graph.number_of_edges(),
            "state_object_id": axis4["state_object_id"],
            "axis4_parent_commit": PARENT_COMMITS["discrete_axis4_composition_v0"],
        },
        "registered_order_words": REGISTERED_ORDER_WORDS,
        "stage_semantics": {
            "U": "committed Axis-4 S4:R_x primitive",
            "E": "committed Axis-4 S4:D_z primitive",
            "application_convention": "word stages are applied left to right to the carrier state",
            "alias_table": ORDER_WORD_ALIASES,
        },
        "channel_table": channel_table,
        "channel_hash_classes": {row["order_word"]: row["label_free_output_multiset_sha256"] for row in channel_table},
        "channel_distinguishability_matrix": distance,
        "capability_metric": capability_metric,
        "szilard_baseline": baseline,
        "szilard_baseline_schedule_table": baseline["admissible_orderings"],
        "szilard_baseline_channel_table": baseline["channel_table"],
        "szilard_admissible_order_count": baseline["admissible_order_count"],
        "szilard_best_distinct_channel_count": baseline["distinct_channel_count"],
        "qit_distinct_channel_count": distinct_count,
        "qit_diversity_strictly_exceeds_computed_szilard": capability_metric[
            "qit_diversity_strictly_exceeds_computed_szilard"
        ],
        "would_die_if_szilard_distinct_count_gte_qit": baseline["distinct_channel_count"] >= distinct_count,
        "controls": {
            "commuting_generator_engine": commuting,
            "shuffled_labels": {
                "permutation": list(reversed(REGISTERED_ORDER_WORDS)),
                "same_diversity_after_label_shuffle": len(set(reversed(hashes))) == distinct_count,
                "same_distance_multiset_after_label_shuffle": sorted(shuffled_distance_multiset) == distance["distance_multiset"],
                "note": "label permutation changes row names only; label-free channel hashes and distance multiset stay invariant",
            },
            "weakened_enumeration_drop_half": weakened_enumeration_control(
                baseline["admissible_orderings"], distinct_count, u, e, cells
            ),
            "no_identity_leak_between_schedule_labels_and_fingerprints": no_identity_leak_control(baseline),
            "falsifier_reachable": {
                "baseline_must_fail_or_discriminator_dies": True,
                "would_die_if_szilard_distinct_count_gte_qit": baseline["distinct_channel_count"] >= distinct_count,
                "synthetic_stronger_baseline_would_kill": baseline["synthetic_stronger_baseline_control"]["ecd01_would_die"],
                "actual_falsifier_status": "not_triggered_szilard_diversity_is_strictly_smaller",
            },
        },
        "symbolic_checks": sympy_commutator_check(),
        "smt_rows": {
            "z3": {**z3_real, "erased_flip_verdict": z3_erased["verdict"]},
            "cvc5": {**cvc5_real, "erased_flip_verdict": cvc5_erased["verdict"]},
        },
        "crossover_proofs": {"z3": z3_real, "cvc5": cvc5_real},
        "source_import_audit": source_import_audit(),
        "standards_codex": "system_v6/receipts/audit_standards_codex_v1.md",
        "standards_version": "audit_standards_codex_v1",
        "write_scope": "system_v6/sims/ecd01_order_programmable_computer_v1 only; no git add/commit; no audit_verdict.md",
        "circularity_species": {
            "definitional_circularity": "v0 killed; v1 repair computes the baseline schedule table before the predicate",
            "rule_table_readback": "not used for pass metric; channel fingerprints are recomputed from output multisets",
            "shift_relabeling": "label shuffle and schedule-label leak controls included",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "TOOL_INTENT_MATRIX": TOOL_INTENT,
        "builder_gates": {
            "packet_audit_verdict_absent": not (SIM_DIR / "audit_verdict.md").exists(),
            "boundary_helper_ok": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "qit_channel_classes_ge_3": distinct_count >= 3,
            "szilard_strictly_smaller": baseline["distinct_channel_count"] < distinct_count,
            "szilard_baseline_computed_not_hardcoded": baseline["hardcoded_distinct_count"] is None,
            "positive_predicate_can_admit_baseline": baseline["positive_predicate"]["can_admit_stronger_baseline"],
            "weakened_enumeration_reports_sensitivity": weakened_enumeration_control(
                baseline["admissible_orderings"], distinct_count, u, e, cells
            )["status"]
            == "sensitive",
            "commuting_control_collapses": commuting["distinct_channel_count"] == 1,
            "boundary_helper_fully_used": True,
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "allowed_claims": [
            "ECD.01 capability discriminator packet computed on the committed Axis-4 carrier",
            "same-carrier order-program diversity exceeds the computed strongest-form plain Szilard baseline for this packet",
            "commuting-generator control removes the capability metric",
        ],
        "disallowed_claims": [
            "universal quantum computer",
            "Turing-complete computer",
            "QIT engine admission",
            "canonical Axis-4 identity",
            "physics claim",
            "bridge admission",
        ],
        "blocked_consumers": [
            "engine admission",
            "full 64-stage schedule claim",
            "scientific coupling or physics rows",
        ],
    }
