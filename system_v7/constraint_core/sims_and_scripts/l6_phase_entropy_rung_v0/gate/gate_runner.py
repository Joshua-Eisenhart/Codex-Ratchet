#!/usr/bin/env python3
"""Scratch-diagnostic gate for the l6 phase/entropy rung."""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

sys.dont_write_bytecode = True

import cvc5
import numpy as np
import z3


SCRIPT_DIR = Path(__file__).resolve().parent
RUNG_DIR = SCRIPT_DIR.parent
ENGINE_DIR = (SCRIPT_DIR / ".." / ".." / ".." / "ratchet").resolve()
sys.path.insert(0, str(ENGINE_DIR))

from ratchet_engine import (  # noqa: E402
    _decomposition_census,
    _normalise_partition,
    _pairwise_order_matrix,
    _sha_json,
    compute_frontier_cache,
    execute_schedules,
    ordered_gate_hypotheses,
)


SEED = 0
SIGN_TOL = 1e-12
FAMILY_ORDER = [
    "factorization_boundary",
    "marginal_entropy_level",
    "orientation_winding",
    "shell_position",
]
EXPECTED_EDGE_COUNTS = {
    "factorization_boundary": 16,
    "marginal_entropy_level": 72,
    "orientation_winding": 9,
    "shell_position": 72,
}
ENGINES = ("julia", "jax", "torch", "numpy_control")
RUNG_RECEIPT = SCRIPT_DIR / "rung_receipt_v1.json"
LANE_RECEIPT = SCRIPT_DIR / "gate_lane_receipt_v1.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def rung_relative(path: Path) -> str:
    return Path(os.path.relpath(path.resolve(), RUNG_DIR.resolve())).as_posix()


def scalar_sign(delta: float) -> int:
    if delta > SIGN_TOL:
        return 1
    if delta < -SIGN_TOL:
        return -1
    return 0


def fused_sign(delta: np.ndarray) -> int:
    for value in np.asarray(delta, dtype=np.float64).reshape(-1):
        sign = scalar_sign(float(value))
        if sign:
            return sign
    return 0


def sign_vector(values: np.ndarray, edges: Sequence[tuple[int, int]]) -> list[int]:
    return [fused_sign(values[j] - values[i]) for i, j in edges]


def partition_assignments(values: np.ndarray) -> tuple[int, ...]:
    row_count = int(values.shape[0])
    parents = list(range(row_count))

    def find(item: int) -> int:
        while parents[item] != item:
            parents[item] = parents[parents[item]]
            item = parents[item]
        return item

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parents[right_root] = left_root

    for left in range(row_count):
        for right in range(left + 1, row_count):
            if bool(np.all(np.abs(values[left] - values[right]) <= SIGN_TOL)):
                union(left, right)
    return _normalise_partition([find(row) for row in range(row_count)])


def exact_class_map(rows: Sequence[dict[str, Any]], key_fn: Any) -> tuple[list[int], list[list[int]]]:
    labels: dict[tuple[Any, ...], int] = {}
    row_to_class: list[int] = []
    groups: list[list[int]] = []
    for row in rows:
        key = tuple(key_fn(row))
        if key not in labels:
            labels[key] = len(labels)
            groups.append([])
        class_id = labels[key]
        row_to_class.append(class_id)
        groups[class_id].append(int(row["row_id"]))
    return row_to_class, groups


def phase_erased_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["a"],
        row["shell_radius"],
        row["purity"],
        row["negativity"],
        row["entropy_bits"],
        row["radial_index"],
        abs(row["chern_signed"]),
    )


def full_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["a"],
        row["shell_radius"],
        row["purity"],
        row["negativity"],
        row["entropy_bits"],
        row["radial_index"],
        row["orientation"],
        row["chern_signed"],
    )


def sign_dropped_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["a"],
        row["shell_radius"],
        row["purity"],
        row["negativity"],
        row["entropy_bits"],
        row["radial_index"],
    )


def normalize_candidates(
    candidate_root: Path,
) -> tuple[list[dict[str, Any]], list[str], list[str], list[Path]]:
    candidates: list[dict[str, Any]] = []
    landed: list[str] = []
    behavior_paths: list[Path] = []
    all_directories = sorted(path for path in candidate_root.iterdir() if path.is_dir())
    for directory in all_directories:
        behavior_path = directory / "behavior_v1.json"
        if not behavior_path.is_file():
            continue
        landed.append(directory.name)
        behavior_paths.append(behavior_path)
        payload = load_json(behavior_path)
        variants = payload["variants"]
        if isinstance(variants, dict):
            variant_items = [(variant_id, variants[variant_id]) for variant_id in sorted(variants)]
        else:
            variant_items = [(variant["variant_id"], variant) for variant in variants]
        for variant_id, variant in variant_items:
            values: dict[str, np.ndarray] = {}
            for engine in ENGINES:
                array = np.asarray(variant["per_row_values"][engine], dtype=np.float64)
                if array.ndim == 1:
                    array = array.reshape(-1, 1)
                if array.ndim != 2 or array.shape[0] != 18:
                    raise ValueError(
                        f"invalid value shape for {directory.name}:{variant_id}:{engine}: {array.shape}"
                    )
                values[engine] = array

            declared: dict[str, list[int]] = {}
            for family in FAMILY_ORDER:
                if directory.name == "noise-floor":
                    declared[family] = [int(value) for value in variant["sign_predictions"][family]["signs"]]
                elif directory.name == "marginal-vn":
                    declared[family] = [
                        int(row["sign_julia"])
                        for row in variant["induced_sign_predictions"][family]
                    ]
                elif directory.name == "orientation-augmented":
                    declared[family] = [
                        int(row["fused_sign"])
                        for row in variant["induced_sign_predictions"][family]
                    ]
                else:
                    raise ValueError(f"unsupported landed candidate family: {directory.name}")
            candidates.append(
                {
                    "lane_family": directory.name,
                    "variant_id": str(variant_id),
                    "candidate_id": f"{directory.name}:{variant_id}",
                    "values": values,
                    "declared_signs": declared,
                }
            )
    missing = sorted(directory.name for directory in all_directories if not (directory / "behavior_v1.json").is_file())
    return candidates, landed, missing, behavior_paths


def build_behaviours(
    candidates: list[dict[str, Any]],
    demands: dict[str, list[tuple[int, int]]],
) -> tuple[list[dict[str, Any]], dict[str, tuple[int, ...]]]:
    grouped: dict[tuple[int, ...], dict[str, Any]] = {}
    assignments_by_candidate: dict[str, tuple[int, ...]] = {}
    for candidate in candidates:
        assignments = partition_assignments(candidate["values"]["julia"])
        assignments_by_candidate[candidate["candidate_id"]] = assignments
        if assignments not in grouped:
            collapsed = {
                family: sum(assignments[left] == assignments[right] for left, right in edges)
                for family, edges in demands.items()
            }
            grouped[assignments] = {
                "id": candidate["candidate_id"],
                "members": [],
                "lane_families": [],
                "assignments": list(assignments),
                "partition_digest": _sha_json(list(assignments)),
                "cell_count": len(set(assignments)),
                "variant_count": 0,
                "collapsed_demand_edges": collapsed,
            }
        row = grouped[assignments]
        row["members"].append(candidate["candidate_id"])
        row["lane_families"].append(candidate["lane_family"])
        row["variant_count"] += 1
    behaviours = sorted(grouped.values(), key=lambda row: (row["cell_count"], row["partition_digest"]))
    for index, row in enumerate(behaviours):
        row["behaviour_index"] = index
        row["lane_families"] = sorted(set(row["lane_families"]))
    return behaviours, assignments_by_candidate


def build_validity(
    candidates: list[dict[str, Any]],
    demands: dict[str, list[tuple[int, int]]],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    cross_substrate: list[dict[str, Any]] = []
    sign_crosscheck: list[dict[str, Any]] = []
    validity_failures: list[dict[str, Any]] = []
    sign_mismatches: list[dict[str, Any]] = []
    for candidate in candidates:
        values = candidate["values"]
        pair_rows: dict[str, dict[str, Any]] = {}
        for pair_name, left, right in (
            ("julia_vs_jax", "julia", "jax"),
            ("julia_vs_torch", "julia", "torch"),
            ("jax_vs_torch", "jax", "torch"),
        ):
            maximum = float(np.max(np.abs(values[left] - values[right])))
            pair_rows[pair_name] = {"max_abs_delta": maximum, "lt_1e-9": maximum < 1e-9}
            if maximum >= 1e-9:
                validity_failures.append(
                    {"candidate_id": candidate["candidate_id"], "comparison": pair_name, "max_abs_delta": maximum}
                )
        numpy_delta = float(np.max(np.abs(values["numpy_control"] - values["julia"])))
        cross_substrate.append(
            {
                "candidate_id": candidate["candidate_id"],
                "three_engine_pairs": pair_rows,
                "numpy_control_vs_julia": {
                    "max_abs_delta": numpy_delta,
                    "comparison_only": True,
                },
            }
        )
        mismatch_counts: dict[str, int] = {}
        for family, edges in demands.items():
            observed = sign_vector(values["julia"], edges)
            declared = candidate["declared_signs"][family]
            mismatch_count = sum(left != right for left, right in zip(observed, declared, strict=True))
            mismatch_counts[family] = mismatch_count
            if mismatch_count:
                sign_mismatches.append(
                    {
                        "candidate_id": candidate["candidate_id"],
                        "family": family,
                        "mismatch_count": mismatch_count,
                    }
                )
        sign_crosscheck.append(
            {"candidate_id": candidate["candidate_id"], "mismatch_counts": mismatch_counts}
        )
    return (
        {"cross_substrate": cross_substrate, "declared_sign_crosscheck": sign_crosscheck},
        validity_failures,
        sign_mismatches,
    )


def run_phase_erasure(
    rows: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    demands: dict[str, list[tuple[int, int]]],
) -> tuple[dict[str, Any], list[int], list[list[int]], list[tuple[int, int]]]:
    erased_class, groups = exact_class_map(rows, phase_erased_key)
    records: list[dict[str, Any]] = []
    for candidate in candidates:
        original = candidate["values"]["julia"]
        erased = original.copy()
        for members in groups:
            representative = min(members)
            erased[members, :] = original[representative, :]
        signs_after = {
            family: sign_vector(erased, edges) for family, edges in demands.items()
        }
        erased_assignments = partition_assignments(erased)
        loss_after = {
            family: sum(erased_assignments[left] == erased_assignments[right] for left, right in edges)
            for family, edges in demands.items()
        }
        phase_edges = demands["orientation_winding"]
        signs_before = sign_vector(original, phase_edges)
        carried_before = sum(sign != 0 for sign in signs_before)
        carried_after = sum(sign != 0 for sign in signs_after["orientation_winding"])
        records.append(
            {
                "candidate_id": candidate["candidate_id"],
                "per_family_signs_after": signs_after,
                "collapsed_demand_edges_after": loss_after,
                "carried_before": carried_before,
                "carried_after": carried_after,
                "flipped": carried_before > 0 and carried_after == 0,
                "identity_under_erasure": float(np.max(np.abs(erased - original))) <= 1e-15,
            }
        )
    class_pairs = [tuple(sorted(members)) for members in groups]
    return (
        {
            "projection_fields": [
                "a",
                "shell_radius",
                "purity",
                "negativity",
                "entropy_bits",
                "radial_index",
                "abs(chern_signed)",
            ],
            "row_to_class": erased_class,
            "classes": groups,
            "candidate_records": records,
            "all_orientation_signs_zero_after": all(
                all(sign == 0 for sign in row["per_family_signs_after"]["orientation_winding"])
                for row in records
            ),
            "all_previously_carrying_flipped": all(
                row["carried_before"] == 0 or row["flipped"] for row in records
            ),
        },
        erased_class,
        groups,
        class_pairs,
    )


def basis_matrix(rows: Sequence[dict[str, Any]]) -> np.ndarray:
    matrix: list[list[float]] = []
    for row in rows:
        a = float(row["a"])
        shell_radius = float(row["shell_radius"])
        purity = float(row["purity"])
        negativity = float(row["negativity"])
        entropy_bits = float(row["entropy_bits"])
        orientation = float(row["orientation"])
        chern_signed = float(row["chern_signed"])
        matrix.append(
            [
                a,
                shell_radius,
                purity,
                negativity,
                entropy_bits,
                orientation,
                chern_signed,
                a * entropy_bits,
                shell_radius * purity,
                negativity * entropy_bits,
                a**2,
                entropy_bits**2,
                math.sin(math.pi * a),
                math.cos(math.pi * shell_radius),
                orientation * entropy_bits,
                1.0,
            ]
        )
    return np.asarray(matrix, dtype=np.float64)


def make_perturbed_bases(rows: list[dict[str, Any]]) -> dict[float, list[np.ndarray]]:
    perturbable = ["a", "shell_radius", "purity", "negativity", "entropy_bits"]
    outputs: dict[float, list[np.ndarray]] = {}
    for sigma in (1e-3, 1e-2):
        rng = np.random.default_rng(SEED)
        draws: list[np.ndarray] = []
        for _ in range(8):
            perturbed = [dict(row) for row in rows]
            for row in perturbed:
                for column in perturbable:
                    row[column] = float(row[column]) + sigma * float(rng.standard_normal())
            draws.append(basis_matrix(perturbed))
        outputs[sigma] = draws
    return outputs


def run_detector(
    rows: list[dict[str, Any]],
    orientation_edges: list[tuple[int, int]],
    noise_candidates: list[dict[str, Any]],
    variants_payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, bool]]:
    base = basis_matrix(rows)
    perturbed_bases = make_perturbed_bases(rows)
    weight_map = {
        variant["variant_id"]: np.asarray(variant["weights"], dtype=np.float64)
        for variant in variants_payload["variants"]
    }
    subjects: list[dict[str, Any]] = []
    for candidate in noise_candidates:
        weights = weight_map[candidate["variant_id"]]
        replay = base @ weights
        recorded = candidate["values"]["julia"][:, 0]
        maximum = float(np.max(np.abs(replay - recorded)))
        subjects.append(
            {
                "subject_id": candidate["variant_id"],
                "source": "noise-floor",
                "weights": weights,
                "attributable": maximum < 1e-9,
                "reproduction_max_abs_delta": maximum,
            }
        )
    anti_result = np.zeros(16, dtype=np.float64)
    anti_result[4] = 1.0
    anti_result[5] = 1e-3
    arity_counter = np.zeros(16, dtype=np.float64)
    arity_counter[5] = 1.0
    subjects.extend(
        [
            {
                "subject_id": "gate_anti_result_copy",
                "source": "in_code_control",
                "weights": anti_result,
                "attributable": True,
                "reproduction_max_abs_delta": 0.0,
            },
            {
                "subject_id": "gate_declared_arity_counter",
                "source": "in_code_control",
                "weights": arity_counter,
                "attributable": True,
                "reproduction_max_abs_delta": 0.0,
            },
        ]
    )

    records: list[dict[str, Any]] = []
    outcomes: dict[str, bool] = {}
    for subject in subjects:
        if not subject["attributable"]:
            records.append(
                {
                    "subject_id": subject["subject_id"],
                    "source": subject["source"],
                    "attribution_status": "not_attributable",
                    "reproduction_max_abs_delta": subject["reproduction_max_abs_delta"],
                    "metrics": [
                        {"sigma": sigma, "status": "skipped_not_attributable"}
                        for sigma in (1e-3, 1e-2)
                    ],
                    "flagged": False,
                }
            )
            outcomes[subject["subject_id"]] = False
            continue
        weights = subject["weights"]
        values0 = base @ weights
        d0 = np.asarray([values0[j] - values0[i] for i, j in orientation_edges], dtype=np.float64)
        signs0 = np.asarray([scalar_sign(float(value)) for value in d0], dtype=np.int64)
        baseline_carrying = bool(np.all(np.abs(d0) > SIGN_TOL))
        margin = float(np.min(np.abs(d0))) if len(d0) else 0.0
        metrics: list[dict[str, Any]] = []
        flagged = False
        for sigma in (1e-3, 1e-2):
            input_response = 0.0
            flips = 0
            for perturbed_basis in perturbed_bases[sigma]:
                values_k = perturbed_basis @ weights
                dk = np.asarray([values_k[j] - values_k[i] for i, j in orientation_edges], dtype=np.float64)
                input_response = max(input_response, float(np.max(np.abs(dk - d0))))
                signs_k = np.asarray([scalar_sign(float(value)) for value in dk], dtype=np.int64)
                flips += int(np.sum(signs_k != signs0))
            flip_fraction = flips / float(len(orientation_edges) * 8)
            scale_flagged = baseline_carrying and input_response > margin and flip_fraction >= 0.05
            flagged = flagged or scale_flagged
            metrics.append(
                {
                    "sigma": sigma,
                    "draw_count": 8,
                    "baseline_carrying": baseline_carrying,
                    "margin": margin,
                    "input_response": input_response,
                    "flip_fraction": flip_fraction,
                    "flagged_at_scale": scale_flagged,
                }
            )
        outcomes[subject["subject_id"]] = flagged
        records.append(
            {
                "subject_id": subject["subject_id"],
                "source": subject["source"],
                "attribution_status": "attributable",
                "reproduction_max_abs_delta": subject["reproduction_max_abs_delta"],
                "metrics": metrics,
                "flagged": flagged,
            }
        )
    flagged_ids = [record["subject_id"] for record in records if record["flagged"]]
    return (
        {
            "seed": SEED,
            "sigmas": [1e-3, 1e-2],
            "draws_per_scale": 8,
            "perturbed_columns": ["a", "shell_radius", "purity", "negativity", "entropy_bits"],
            "held_fixed": ["orientation", "chern_signed", "radial_index", "orientation_winding edges"],
            "flag_rule": (
                "baseline_carrying and, at any tested scale, input_response exceeds margin "
                "and flip_fraction is at least 0.05"
            ),
            "flag_meaning": (
                "the phase-edge carrying signal sits below the functional input-response floor "
                "and the carried sign pattern scrambles while the obligation is held fixed"
            ),
            "subject_records": records,
            "flagged_ids": flagged_ids,
        },
        outcomes,
    )


def z3_instance(
    row_to_class: list[int], edges: list[tuple[int, int]], prefix: str
) -> tuple[str, dict[str, int]]:
    solver = z3.Solver()
    variables = {
        class_id: z3.Int(f"{prefix}_class_{class_id}") for class_id in sorted(set(row_to_class))
    }
    for left, right in edges:
        solver.add(variables[row_to_class[left]] != variables[row_to_class[right]])
    result = solver.check()
    normalized = str(result).upper()
    witness: dict[str, int] = {}
    if result == z3.sat:
        model = solver.model()
        witness = {
            str(class_id): int(model.eval(variable, model_completion=True).as_long())
            for class_id, variable in variables.items()
        }
    return normalized, witness


def cvc5_instance(row_to_class: list[int], edges: list[tuple[int, int]], prefix: str) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer_sort = solver.getIntegerSort()
    variables = {
        class_id: solver.mkConst(integer_sort, f"{prefix}_class_{class_id}")
        for class_id in sorted(set(row_to_class))
    }
    for left, right in edges:
        inequality = solver.mkTerm(
            cvc5.Kind.DISTINCT,
            variables[row_to_class[left]],
            variables[row_to_class[right]],
        )
        solver.assertFormula(inequality)
    return str(solver.checkSat()).upper()


def make_smt_instance(
    instance_id: str,
    row_to_class: list[int],
    edges: list[tuple[int, int]],
    *,
    vacuous: bool = False,
) -> dict[str, Any]:
    z3_result, witness = z3_instance(row_to_class, edges, instance_id)
    cvc5_result = cvc5_instance(row_to_class, edges, instance_id)
    return {
        "instance_id": instance_id,
        "row_to_class": row_to_class,
        "edge_count": len(edges),
        "edge_class_pairs": [[row_to_class[left], row_to_class[right]] for left, right in edges],
        "vacuous": vacuous,
        "solvers": {
            "z3": {"name": "z3", "version": z3.get_version_string(), "result": z3_result},
            "cvc5": {"name": "cvc5", "version": cvc5.__version__, "result": cvc5_result},
        },
        "agreement": z3_result == cvc5_result and z3_result in {"SAT", "UNSAT"},
        "z3_witness_model": witness,
    }


def run_smt(
    rows: list[dict[str, Any]],
    demands: dict[str, list[tuple[int, int]]],
    erased_class: list[int],
) -> dict[str, Any]:
    full_class, _ = exact_class_map(rows, full_key)
    sign_dropped_rows = [
        {key: value for key, value in row.items() if key not in {"orientation", "chern_signed"}}
        for row in rows
    ]
    control_a_edges: list[tuple[int, int]] = []
    for left in range(len(sign_dropped_rows)):
        for right in range(left + 1, len(sign_dropped_rows)):
            left_row = sign_dropped_rows[left]
            right_row = sign_dropped_rows[right]
            if (
                "orientation" in left_row
                and "orientation" in right_row
                and left_row["radial_index"] == right_row["radial_index"]
                and left_row["orientation"] != right_row["orientation"]
            ):
                control_a_edges.append((left, right))
    sign_dropped_class, _ = exact_class_map(rows, sign_dropped_key)
    real_instances = [
        make_smt_instance(f"real_{family}", erased_class, demands[family])
        for family in FAMILY_ORDER
    ]
    control_a = make_smt_instance(
        "erased_control_a_drop_sign_columns",
        sign_dropped_class,
        control_a_edges,
        vacuous=True,
    )
    control_b = make_smt_instance(
        "erased_control_b_full_projection",
        full_class,
        demands["orientation_winding"],
    )
    all_instances = real_instances + [control_a, control_b]
    return {
        "structural_claim": (
            "no phase-blind functional in the finite phase-erased projection class can carry "
            "the phase-sign demand edges"
        ),
        "polarity_convention": (
            "inequality constraints encode attempted carrying directly; real orientation_winding "
            "is UNSAT, while erased controls are SAT"
        ),
        "real_instances": real_instances,
        "erased_control_a": control_a,
        "erased_control_b": control_b,
        "all_solver_results_agree": all(instance["agreement"] for instance in all_instances),
    }


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, observed: Any = None) -> None:
    row: dict[str, Any] = {"name": name, "pass": bool(passed)}
    if observed is not None:
        row["observed"] = observed
    checks.append(row)


def input_rows(paths: Iterable[Path]) -> list[dict[str, str]]:
    return [
        {"path": rung_relative(path), "sha256": sha256_path(path)}
        for path in sorted(paths, key=lambda item: rung_relative(item))
    ]


def main() -> int:
    surface_path = RUNG_DIR / "surface" / "surface_v1.json"
    demand_path = RUNG_DIR / "surface" / "demand_families_v1.json"
    candidate_root = RUNG_DIR / "candidates"
    variants_path = candidate_root / "noise-floor" / "variants_v1.json"
    manifest_path = candidate_root / "noise-floor" / "injection_manifest_v1.json"
    schema_path = ENGINE_DIR / "schemas" / "ratchet_order_open_run.schema.json"
    engine_path = ENGINE_DIR / "ratchet_engine.py"

    surface = load_json(surface_path)
    demand_payload = load_json(demand_path)
    rows = list(surface["row_blocks"]["fixture_observations"])
    demands = {
        family: [(int(edge["row_i"]), int(edge["row_j"])) for edge in demand_payload["families"][family]["edges"]]
        for family in FAMILY_ORDER
    }
    candidates, landed, missing, behavior_paths = normalize_candidates(candidate_root)
    behaviours, _ = build_behaviours(candidates, demands)

    cache = compute_frontier_cache(behaviours, FAMILY_ORDER)
    schedules = ordered_gate_hypotheses(FAMILY_ORDER)
    schedule_receipts = execute_schedules(schedules, FAMILY_ORDER, cache)
    order_matrix = _pairwise_order_matrix(FAMILY_ORDER, cache)
    census = _decomposition_census(schedule_receipts)
    distinct_endpoints = len(
        {receipt["final_frontier_fingerprint"] for receipt in schedule_receipts}
    )

    validity, validity_failures, sign_mismatches = build_validity(candidates, demands)
    phase_erasure, erased_class, phase_groups, phase_pairs = run_phase_erasure(rows, candidates, demands)

    variants_payload = load_json(variants_path)
    noise_candidates = [candidate for candidate in candidates if candidate["lane_family"] == "noise-floor"]
    detector, detector_outcomes = run_detector(
        rows, demands["orientation_winding"], noise_candidates, variants_payload
    )
    detected_noise_ids = [
        candidate["variant_id"]
        for candidate in noise_candidates
        if detector_outcomes.get(candidate["variant_id"], False)
    ]

    # The manifest is intentionally consulted only after behavioral detection.
    injection_manifest = load_json(manifest_path)
    manifest_id = str(injection_manifest["injected_variant_id"])
    attribution = {
        "manifest_injected_id": manifest_id,
        "detected_ids": detected_noise_ids,
        "detected_contains_manifest_id": manifest_id in detected_noise_ids,
        "extra_flags": [variant_id for variant_id in detected_noise_ids if variant_id != manifest_id],
    }
    anti_by_construction = {
        "gate_anti_result_copy": {
            "weights": {"entropy_bits": 1.0, "orientation": 1e-3},
            "expected_flag": True,
            "observed_flag": detector_outcomes["gate_anti_result_copy"],
        },
        "gate_declared_arity_counter": {
            "weights": {"orientation": 1.0},
            "expected_flag": False,
            "observed_flag": detector_outcomes["gate_declared_arity_counter"],
        },
    }

    smt = run_smt(rows, demands, erased_class)
    real_by_id = {row["instance_id"]: row for row in smt["real_instances"]}

    checks: list[dict[str, Any]] = []
    add_check(checks, "fixture_row_count", len(rows) == 18, len(rows))
    add_check(checks, "fixture_row_ids_in_order", [row["row_id"] for row in rows] == list(range(18)))
    add_check(
        checks,
        "demand_family_edge_counts",
        {family: len(edges) for family, edges in demands.items()} == EXPECTED_EDGE_COUNTS,
        {family: len(edges) for family, edges in demands.items()},
    )
    add_check(checks, "normalized_variant_count", len(candidates) == 57, len(candidates))
    add_check(checks, "ordered_set_partition_schedule_count", len(schedules) == 75, len(schedules))
    add_check(checks, "frontier_cache_mask_count", len(cache) == 16, len(cache))
    add_check(checks, "phase_erased_class_count", len(phase_groups) == 9, len(phase_groups))
    add_check(checks, "phase_erased_class_sizes", all(len(group) == 2 for group in phase_groups), [len(group) for group in phase_groups])
    orientation_pairs = sorted(tuple(sorted(edge)) for edge in demands["orientation_winding"])
    add_check(checks, "phase_classes_match_orientation_edges", sorted(phase_pairs) == orientation_pairs)
    add_check(
        checks,
        "phase_erasure_zeroes_all_orientation_signs",
        phase_erasure["all_orientation_signs_zero_after"],
    )
    add_check(
        checks,
        "phase_erasure_flips_every_previously_carrying_variant",
        phase_erasure["all_previously_carrying_flipped"],
    )
    add_check(
        checks,
        "anti_result_copy_flagged",
        detector_outcomes["gate_anti_result_copy"] is True,
        detector_outcomes["gate_anti_result_copy"],
    )
    add_check(
        checks,
        "declared_arity_counter_not_flagged",
        detector_outcomes["gate_declared_arity_counter"] is False,
        detector_outcomes["gate_declared_arity_counter"],
    )
    add_check(
        checks,
        "manifest_injected_functional_detected_behaviorally",
        attribution["detected_contains_manifest_id"],
        detected_noise_ids,
    )
    add_check(
        checks,
        "real_orientation_winding_unsat_z3",
        real_by_id["real_orientation_winding"]["solvers"]["z3"]["result"] == "UNSAT",
    )
    add_check(
        checks,
        "real_orientation_winding_unsat_cvc5",
        real_by_id["real_orientation_winding"]["solvers"]["cvc5"]["result"] == "UNSAT",
    )
    for control_name in ("erased_control_a", "erased_control_b"):
        control = smt[control_name]
        add_check(
            checks,
            f"{control_name}_sat_z3",
            control["solvers"]["z3"]["result"] == "SAT",
        )
        add_check(
            checks,
            f"{control_name}_sat_cvc5",
            control["solvers"]["cvc5"]["result"] == "SAT",
        )
    add_check(checks, "erased_control_a_has_zero_edges", smt["erased_control_a"]["edge_count"] == 0)
    add_check(checks, "all_smt_instances_solver_agreement", smt["all_solver_results_agree"])

    failed_checks = [check["name"] for check in checks if not check["pass"]]
    if failed_checks:
        print(f"INTERNAL_VALIDATION: FAIL ({failed_checks[0]})")
        return 1

    full_mask = (1 << len(FAMILY_ORDER)) - 1
    frontier_summary = {
        str(mask): {
            "active_families": cache[mask]["active_families"],
            "survivor_count": cache[mask]["survivor_count"],
            "frontier_ids": cache[mask]["frontier_ids"],
            "frontier_fingerprint": cache[mask]["frontier_fingerprint"],
        }
        for mask in range(1 << len(FAMILY_ORDER))
    }
    kill_by_behaviour = [
        {
            "behaviour_id": row["id"],
            "families_with_collapsed_demand_edges": {
                family: count
                for family, count in row["collapsed_demand_edges"].items()
                if count > 0
            },
        }
        for row in behaviours
    ]
    open_digs: list[dict[str, Any]] = [
        {"kind": "missing_candidate_family", "candidate_family": family}
        for family in missing
    ]
    open_digs.extend({"kind": "cross_substrate_validity", **row} for row in validity_failures)
    open_digs.extend({"kind": "declared_sign_crosscheck", **row} for row in sign_mismatches)

    receipt: dict[str, Any] = {
        "schema_version": "l6_phase_entropy_rung_receipt/1.0",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "seed": SEED,
        "claim_ceiling": (
            "scratch_diagnostic — the gate computes; receipts report what ran; no rung adjudication"
        ),
        "inputs": input_rows(
            [
                surface_path,
                demand_path,
                *behavior_paths,
                variants_path,
                manifest_path,
                engine_path,
                schema_path,
            ]
        ),
        "candidate_families": {
            "landed": landed,
            "missing_recorded_not_blocking": missing,
        },
        "validity": validity,
        "behaviours": behaviours,
        "frontier_cache_summary": frontier_summary,
        "gate_order_search": {
            "schedule_hypotheses_executed": len(schedule_receipts),
            "schedule_receipts": schedule_receipts,
            "pairwise_order_matrix": order_matrix,
            "decomposition_census": census,
            "distinct_endpoint_fingerprint_count": distinct_endpoints,
        },
        "controls": {
            "phase_erasure": phase_erasure,
            "behavioral_source_attribution": detector,
            "anti_by_construction": anti_by_construction,
        },
        "smt": smt,
        "kill_attribution": {
            "per_behaviour": kill_by_behaviour,
            "behavioral_source_attribution": attribution,
        },
        "open_digs": open_digs,
        "v0_5_schema_fit": {},
        "internal_validation": {"checks": checks, "all_pass": True},
    }
    schema = load_json(schema_path)
    missing_schema_keys = [key for key in schema.get("required", []) if key not in receipt]
    receipt["v0_5_schema_fit"] = {
        "fits_required_top_level_keys": not missing_schema_keys,
        "required_keys_lacked": missing_schema_keys,
    }

    rung_bytes = (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if RUNG_RECEIPT.exists():
        existing = RUNG_RECEIPT.read_bytes()
        if existing != rung_bytes:
            print(
                "BYTE_IDENTITY_FINDING: existing rung_receipt_v1.json differs from this deterministic run",
                file=sys.stderr,
            )
            return 1
    else:
        RUNG_RECEIPT.write_bytes(rung_bytes)

    lane_receipt = {
        "schema_version": "l6_phase_entropy_gate_lane_receipt/1.0",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "z3": z3.get_version_string(),
            "cvc5": cvc5.__version__,
        },
        "rung_receipt_sha256": sha256_bytes(rung_bytes),
        "what_ran": [
            "input_and_candidate_normalization",
            "behavior_pool_and_alias_collapse",
            "imported_frontier_cache",
            "all_ordered_set_partition_schedules",
            "cross_substrate_and_declared_sign_checks",
            "phase_erasure_control",
            "behavioral_source_attribution_control",
            "anti_by_construction_controls",
            "z3_and_cvc5_structural_instances",
            "internal_validation",
        ],
    }
    LANE_RECEIPT.write_text(
        json.dumps(lane_receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )

    full_survivor_ids = {
        row["id"]
        for row in behaviours
        if all(row["collapsed_demand_edges"][family] == 0 for family in FAMILY_ORDER)
    }
    print("HEADLINE TABLE")
    print(
        "behaviour_id | members | cell_count | "
        "L_D[factorization_boundary,marginal_entropy_level,orientation_winding,shell_position] | "
        "survivor_under_all_four"
    )
    for row in behaviours:
        losses = [row["collapsed_demand_edges"][family] for family in FAMILY_ORDER]
        print(
            f"{row['id']} | {len(row['members'])} | {row['cell_count']} | "
            f"{losses[0]},{losses[1]},{losses[2]},{losses[3]} | "
            f"{'yes' if row['id'] in full_survivor_ids else 'no'}"
        )
    print(
        f"FRONTIER full_mask ids={cache[full_mask]['frontier_ids']} "
        f"fingerprint={cache[full_mask]['frontier_fingerprint']}"
    )
    print(f"FRONTIER distinct_endpoint_count={distinct_endpoints}")
    print(f"FRONTIER decomposition_census={json.dumps(census, sort_keys=True)}")
    print(
        "CONTROL phase_erasure "
        f"all_orientation_signs_zero_after={phase_erasure['all_orientation_signs_zero_after']} "
        f"all_previously_carrying_flipped={phase_erasure['all_previously_carrying_flipped']}"
    )
    print(
        "CONTROL detector "
        f"flagged_ids={detector['flagged_ids']} manifest_id={manifest_id} "
        f"manifest_detected={attribution['detected_contains_manifest_id']} "
        f"extra_flags={attribution['extra_flags']}"
    )
    print(
        "CONTROL anti_by_construction "
        f"gate_anti_result_copy={detector_outcomes['gate_anti_result_copy']} "
        f"gate_declared_arity_counter={detector_outcomes['gate_declared_arity_counter']}"
    )
    for instance in smt["real_instances"] + [smt["erased_control_a"], smt["erased_control_b"]]:
        print(
            f"SMT {instance['instance_id']} "
            f"z3={instance['solvers']['z3']['result']} "
            f"cvc5={instance['solvers']['cvc5']['result']} "
            f"agreement={instance['agreement']} edge_count={instance['edge_count']}"
        )
    print(f"INTERNAL_VALIDATION: ALL PASS ({len(checks)} checks)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"INTERNAL_VALIDATION: FAIL (exception: {type(exc).__name__}: {exc})", file=sys.stderr)
        raise SystemExit(1)
