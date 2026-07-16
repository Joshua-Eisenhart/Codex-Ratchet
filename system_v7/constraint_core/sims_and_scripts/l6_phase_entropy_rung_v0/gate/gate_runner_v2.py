#!/usr/bin/env python3
"""Held-out, anti-luck Gate V2 for the L6 phase/entropy rung.

This remains a scratch diagnostic.  It intentionally does not broaden the
executed grammar beyond total partitions of the fixed eighteen-row surface.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, Sequence

sys.dont_write_bytecode = True

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import gate_runner as gate_v1


RUNG_DIR = SCRIPT_DIR.parent
CANDIDATE_ROOT = RUNG_DIR / "candidates"
RUNG_RECEIPT = SCRIPT_DIR / "rung_receipt_v2.json"

RAW_FAMILY_ORDER = (
    "factorization_boundary",
    "marginal_entropy_level",
    "orientation_winding",
    "shell_position",
)
ACTIVE_FAMILY_ORDER = (
    "factorization_boundary",
    "marginal_entropy_level",
    "orientation_winding",
)
FAMILY_ALIASES = {
    "factorization_boundary": ("factorization_boundary",),
    "marginal_entropy_level": ("marginal_entropy_level", "shell_position"),
    "orientation_winding": ("orientation_winding",),
}
EXPECTED_CANDIDATE_FAMILIES = (
    "coherence-functionals",
    "marginal-vn",
    "noise-floor",
    "orientation-augmented",
    "relative-entropy-ref",
    "weaker-carriers",
)
REQUIRED_V1_CONTROL_FAMILY = "noise-floor"
SPLIT_SEEDS = (0, 1, 2)
FRESH_NOISE_SEEDS = (1, 2, 3)
PHASE_CHANCE_ACCURACY = 0.5
SIGN_TOL = gate_v1.SIGN_TOL
ENGINES = gate_v1.ENGINES

REFEREE_ATTACK = (
    "external_packet_audits/grok45_referee_carrier_rung_20260711.md"
)
NOISE_BASIS_EXPRESSIONS = (
    "a",
    "shell_radius",
    "purity",
    "negativity",
    "entropy_bits",
    "orientation",
    "chern_signed",
    "a*entropy_bits",
    "shell_radius*purity",
    "negativity*entropy_bits",
    "a^2",
    "entropy_bits^2",
    "sin(pi*a)",
    "cos(pi*shell_radius)",
    "orientation*entropy_bits",
    "1.0",
)


@dataclass(frozen=True)
class FrozenInput:
    path: Path
    content: bytes

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()

    def json(self) -> Any:
        return json.loads(self.content.decode("utf-8"))


@dataclass(frozen=True)
class InputSnapshot:
    files: tuple[FrozenInput, ...]
    candidate_directories: tuple[str, ...]
    behavior_files: tuple[FrozenInput, ...]
    present_families: tuple[str, ...]
    absent_families: tuple[str, ...]

    def by_path(self, path: Path) -> FrozenInput:
        target = path.resolve()
        for item in self.files:
            if item.path.resolve() == target:
                return item
        raise KeyError(path)


def freeze(path: Path) -> FrozenInput:
    return FrozenInput(path=path, content=path.read_bytes())


def rung_relative(path: Path) -> str:
    return Path(os.path.relpath(path.resolve(), RUNG_DIR.resolve())).as_posix()


def discover_inputs() -> InputSnapshot:
    directories = tuple(
        sorted(path.name for path in CANDIDATE_ROOT.iterdir() if path.is_dir())
    )
    known_families = tuple(sorted(set(EXPECTED_CANDIDATE_FAMILIES) | set(directories)))
    behavior_paths = tuple(
        sorted(
            (path for path in CANDIDATE_ROOT.glob("*/behavior_v1.json") if path.is_file()),
            key=lambda path: path.parent.name,
        )
    )
    behavior_files = tuple(freeze(path) for path in behavior_paths)
    present = tuple(item.path.parent.name for item in behavior_files)
    absent = tuple(family for family in known_families if family not in present)

    fixed_paths = [
        RUNG_DIR / "surface" / "surface_v1.json",
        RUNG_DIR / "surface" / "demand_families_v1.json",
        SCRIPT_DIR / "gate_runner.py",
        SCRIPT_DIR / "gate_runner_v2.py",
        SCRIPT_DIR / "rung_receipt_v1.json",
        gate_v1.ENGINE_DIR / "ratchet_engine.py",
        gate_v1.ENGINE_DIR / "schemas" / "ratchet_order_open_run.schema.json",
        RUNG_DIR.parent.parent / REFEREE_ATTACK,
    ]
    optional_paths = [
        CANDIDATE_ROOT / "noise-floor" / "compiler.py",
        CANDIDATE_ROOT / "noise-floor" / "variants_v1.json",
        CANDIDATE_ROOT / "noise-floor" / "injection_manifest_v1.json",
    ]
    optional_paths.extend(
        sorted((CANDIDATE_ROOT / "noise-floor").glob("BUILD_CARD*"))
    )
    fixed_files = tuple(freeze(path) for path in fixed_paths)
    optional_files = tuple(freeze(path) for path in optional_paths if path.is_file())
    return InputSnapshot(
        files=fixed_files + optional_files + behavior_files,
        candidate_directories=directories,
        behavior_files=behavior_files,
        present_families=present,
        absent_families=absent,
    )


def edge_pairs(payload: dict[str, Any], family: str) -> list[tuple[int, int]]:
    return [
        (int(edge["row_i"]), int(edge["row_j"]))
        for edge in payload["families"][family]["edges"]
    ]


def validate_surface_and_demands(
    surface: dict[str, Any], demand_payload: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, list[tuple[int, int]]]]:
    rows = list(surface["row_blocks"]["fixture_observations"])
    if len(rows) != 18 or [int(row["row_id"]) for row in rows] != list(range(18)):
        raise ValueError("Gate V2 requires the frozen ordered eighteen-row surface")
    if tuple(demand_payload["families"].keys()) != RAW_FAMILY_ORDER:
        if set(demand_payload["families"]) != set(RAW_FAMILY_ORDER):
            raise ValueError("unexpected demand-family names")
    demands = {family: edge_pairs(demand_payload, family) for family in RAW_FAMILY_ORDER}
    expected_counts = gate_v1.EXPECTED_EDGE_COUNTS
    actual_counts = {family: len(edges) for family, edges in demands.items()}
    if actual_counts != expected_counts:
        raise ValueError(f"unexpected demand edge counts: {actual_counts}")
    if sorted(demands["marginal_entropy_level"]) != sorted(demands["shell_position"]):
        raise ValueError(
            "declared no-double-counting rule failed: marginal_entropy_level and "
            "shell_position edge multisets differ"
        )
    return rows, demands


def variant_items(payload: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    variants = payload["variants"]
    if isinstance(variants, dict):
        return [(str(key), variants[key]) for key in sorted(variants)]
    items: list[tuple[str, dict[str, Any]]] = []
    for variant in variants:
        variant_id = variant.get("variant_id")
        if not variant_id:
            raise ValueError("list-form behavior variant lacks variant_id")
        items.append((str(variant_id), variant))
    return sorted(items, key=lambda item: item[0])


def declared_signs(
    variant: dict[str, Any],
    family: str,
    expected_edges: Sequence[tuple[int, int]],
) -> list[int] | None:
    source = variant.get("sign_predictions")
    if source is None:
        source = variant.get("induced_sign_predictions")
    if not isinstance(source, dict) or family not in source:
        return None
    family_rows = source[family]
    if isinstance(family_rows, dict) and isinstance(family_rows.get("signs"), list):
        return [int(value) for value in family_rows["signs"]]
    if not isinstance(family_rows, list):
        return None
    signs: list[int] = []
    observed_edges: list[tuple[int, int]] = []
    for row in family_rows:
        if not isinstance(row, dict):
            return None
        observed_edges.append((int(row["row_i"]), int(row["row_j"])))
        if "fused_sign" in row:
            signs.append(int(row["fused_sign"]))
        elif "sign_julia" in row:
            signs.append(int(row["sign_julia"]))
        elif "sign" in row:
            signs.append(int(row["sign"]))
        else:
            return None
    if observed_edges != list(expected_edges):
        raise ValueError(f"declared edge order differs for {family}")
    return signs


def normalize_candidates(
    behavior_files: Sequence[FrozenInput],
    demands: dict[str, list[tuple[int, int]]],
    *,
    surface_sha256: str,
    demands_sha256: str,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for frozen in behavior_files:
        lane_family = frozen.path.parent.name
        payload = frozen.json()
        inputs = payload.get("inputs")
        if isinstance(inputs, dict):
            declared_surface = inputs.get("surface_v1_sha256")
            declared_demands = inputs.get("demand_families_v1_sha256")
            if isinstance(inputs.get("surface"), dict):
                declared_surface = inputs["surface"].get("sha256", declared_surface)
            if isinstance(inputs.get("demands"), dict):
                declared_demands = inputs["demands"].get("sha256", declared_demands)
            if declared_surface is not None and str(declared_surface) != surface_sha256:
                raise ValueError(f"stale surface hash declared by {lane_family}")
            if declared_demands is not None and str(declared_demands) != demands_sha256:
                raise ValueError(f"stale demand hash declared by {lane_family}")
        declared_row_order = payload.get("row_order")
        if declared_row_order is not None and list(declared_row_order) != list(range(18)):
            raise ValueError(f"stale or unsupported row order declared by {lane_family}")
        for variant_id, variant in variant_items(payload):
            values: dict[str, np.ndarray] = {}
            per_row = variant.get("per_row_values")
            if not isinstance(per_row, dict):
                raise ValueError(f"{lane_family}:{variant_id} lacks per_row_values")
            for engine in ENGINES:
                if engine not in per_row:
                    raise ValueError(f"{lane_family}:{variant_id} lacks {engine} values")
                array = np.asarray(per_row[engine], dtype=np.float64)
                if array.ndim == 1:
                    array = array.reshape(-1, 1)
                if array.ndim != 2 or array.shape[0] != 18:
                    raise ValueError(
                        "UNSUPPORTED_PARTIAL_PRESENTATION: "
                        f"{lane_family}:{variant_id}:{engine} has shape {array.shape}; "
                        "Gate V2 does not impute abstaining or missing rows"
                    )
                if not bool(np.all(np.isfinite(array))):
                    raise ValueError(
                        "UNSUPPORTED_PARTIAL_PRESENTATION: "
                        f"{lane_family}:{variant_id}:{engine} contains NaN or infinity"
                    )
                values[engine] = array
            shapes = {engine: tuple(array.shape) for engine, array in values.items()}
            if len(set(shapes.values())) != 1:
                raise ValueError(
                    f"cross-substrate value shapes differ for {lane_family}:{variant_id}: {shapes}"
                )
            candidates.append(
                {
                    "lane_family": lane_family,
                    "variant_id": variant_id,
                    "candidate_id": f"{lane_family}:{variant_id}",
                    "values": values,
                    "declared_signs": {
                        family: declared_signs(variant, family, demands[family])
                        for family in RAW_FAMILY_ORDER
                    },
                }
            )
    candidates.sort(key=lambda row: row["candidate_id"])
    if not candidates:
        raise ValueError("no behavior_v1.json candidates were present at run time")
    return candidates


def validate_candidate_behaviors(
    candidates: Sequence[dict[str, Any]],
    demands: dict[str, list[tuple[int, int]]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cross_substrate: list[dict[str, Any]] = []
    sign_crosscheck: list[dict[str, Any]] = []
    open_digs: list[dict[str, Any]] = []
    for candidate in candidates:
        values = candidate["values"]
        pair_rows: dict[str, dict[str, Any]] = {}
        for label, left, right in (
            ("julia_vs_jax", "julia", "jax"),
            ("julia_vs_torch", "julia", "torch"),
            ("jax_vs_torch", "jax", "torch"),
        ):
            maximum = float(np.max(np.abs(values[left] - values[right])))
            pair_rows[label] = {"max_abs_delta": maximum, "lt_1e-9": maximum < 1e-9}
            if maximum >= 1e-9:
                open_digs.append(
                    {
                        "kind": "cross_substrate_validity",
                        "candidate_id": candidate["candidate_id"],
                        "comparison": label,
                        "max_abs_delta": maximum,
                    }
                )
        cross_substrate.append(
            {
                "candidate_id": candidate["candidate_id"],
                "three_engine_pairs": pair_rows,
                "numpy_control_vs_julia": {
                    "max_abs_delta": float(
                        np.max(np.abs(values["numpy_control"] - values["julia"]))
                    ),
                    "comparison_only": True,
                },
            }
        )
        mismatch_counts: dict[str, int | None] = {}
        for family, edges in demands.items():
            declared = candidate["declared_signs"][family]
            if declared is None:
                mismatch_counts[family] = None
                open_digs.append(
                    {
                        "kind": "declared_signs_absent",
                        "candidate_id": candidate["candidate_id"],
                        "family": family,
                        "observed_signs_recomputed": True,
                    }
                )
                continue
            observed = gate_v1.sign_vector(values["julia"], edges)
            if len(declared) != len(observed):
                raise ValueError(
                    f"declared sign count differs for {candidate['candidate_id']}:{family}"
                )
            mismatch = sum(
                left != right for left, right in zip(observed, declared, strict=True)
            )
            mismatch_counts[family] = mismatch
            if mismatch:
                open_digs.append(
                    {
                        "kind": "declared_sign_crosscheck",
                        "candidate_id": candidate["candidate_id"],
                        "family": family,
                        "mismatch_count": mismatch,
                    }
                )
        sign_crosscheck.append(
            {"candidate_id": candidate["candidate_id"], "mismatch_counts": mismatch_counts}
        )
    return {
        "cross_substrate": cross_substrate,
        "declared_sign_crosscheck": sign_crosscheck,
    }, open_digs


def make_edge_splits(
    demands: dict[str, list[tuple[int, int]]], seed: int
) -> dict[str, dict[str, Any]]:
    splits: dict[str, dict[str, Any]] = {}
    for active_family in ACTIVE_FAMILY_ORDER:
        edges = demands[active_family]
        ranked_ids = sorted(
            range(len(edges)),
            key=lambda index: hashlib.sha256(
                (
                    f"gate-v2:{seed}:{active_family}:{index}:"
                    f"{edges[index][0]}:{edges[index][1]}"
                ).encode("utf-8")
            ).hexdigest(),
        )
        heldout_count = len(edges) // 3
        heldout_ids = sorted(ranked_ids[:heldout_count])
        fit_ids = sorted(ranked_ids[heldout_count:])
        splits[active_family] = {
            "reported_names": list(FAMILY_ALIASES[active_family]),
            "edge_count": len(edges),
            "fit_count": len(fit_ids),
            "heldout_count": len(heldout_ids),
            "fit_edge_ids": fit_ids,
            "heldout_edge_ids": heldout_ids,
            "fit_edges": [list(edges[index]) for index in fit_ids],
            "heldout_edges": [list(edges[index]) for index in heldout_ids],
            "fit_edge_digest": gate_v1._sha_json(
                [list(edges[index]) for index in fit_ids]
            ),
            "heldout_edge_digest": gate_v1._sha_json(
                [list(edges[index]) for index in heldout_ids]
            ),
        }
    return splits


def demands_from_split(
    splits: dict[str, dict[str, Any]], key: str
) -> dict[str, list[tuple[int, int]]]:
    return {
        family: [tuple(edge) for edge in splits[family][key]]
        for family in ACTIVE_FAMILY_ORDER
    }


def build_behaviours(
    candidates: Sequence[dict[str, Any]],
    demands: dict[str, list[tuple[int, int]]],
    *,
    fit_induced_assignments: bool = False,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, ...], dict[str, Any]] = {}
    for candidate in candidates:
        assignments = (
            partition_assignments_on_edges(candidate["values"]["julia"], demands)
            if fit_induced_assignments
            else gate_v1.partition_assignments(candidate["values"]["julia"])
        )
        row = grouped.setdefault(
            assignments,
            {
                "id": candidate["candidate_id"],
                "members": [],
                "lane_families": [],
                "assignments": list(assignments),
                "partition_digest": gate_v1._sha_json(list(assignments)),
                "cell_count": len(set(assignments)),
                "variant_count": 0,
                "collapsed_demand_edges": {
                    family: sum(assignments[left] == assignments[right] for left, right in edges)
                    for family, edges in demands.items()
                },
            },
        )
        row["members"].append(candidate["candidate_id"])
        row["lane_families"].append(candidate["lane_family"])
        row["variant_count"] += 1
    behaviours = sorted(
        grouped.values(), key=lambda row: (row["cell_count"], row["partition_digest"])
    )
    for index, row in enumerate(behaviours):
        row["behaviour_index"] = index
        row["members"] = sorted(row["members"])
        row["lane_families"] = sorted(set(row["lane_families"]))
    return behaviours


def partition_assignments_on_edges(
    values: np.ndarray, demands: dict[str, list[tuple[int, int]]]
) -> tuple[int, ...]:
    """Build a total fit-induced partition without consulting held-out pairs."""
    parents = list(range(int(values.shape[0])))

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

    for edges in demands.values():
        for left, right in edges:
            if bool(np.all(np.abs(values[left] - values[right]) <= SIGN_TOL)):
                union(left, right)
    return gate_v1._normalise_partition([find(row) for row in range(len(parents))])


def expected_phase_signs(
    rows: Sequence[dict[str, Any]], edges: Sequence[tuple[int, int]]
) -> list[int]:
    expected: list[int] = []
    for left, right in edges:
        sign = gate_v1.scalar_sign(
            float(rows[right]["orientation"]) - float(rows[left]["orientation"])
        )
        if sign == 0:
            raise ValueError(f"orientation_winding edge {left},{right} has zero target sign")
        expected.append(sign)
    return expected


def score_candidate_heldout(
    candidate: dict[str, Any],
    rows: Sequence[dict[str, Any]],
    heldout_demands: dict[str, list[tuple[int, int]]],
) -> dict[str, Any]:
    values = candidate["values"]["julia"]
    per_family: dict[str, Any] = {}
    for family, edges in heldout_demands.items():
        observed = gate_v1.sign_vector(values, edges)
        separated = sum(sign != 0 for sign in observed)
        row: dict[str, Any] = {
            "reported_names": list(FAMILY_ALIASES[family]),
            "edge_count": len(edges),
            "separated_count": separated,
            "collapsed_demand_edges": len(edges) - separated,
            "separation_accuracy": separated / len(edges),
            "observed_signs": observed,
        }
        if family == "orientation_winding":
            expected = expected_phase_signs(rows, edges)
            correct = sum(
                left == right for left, right in zip(observed, expected, strict=True)
            )
            row.update(
                {
                    "expected_signs": expected,
                    "direction_correct_count": correct,
                    "phase_edge_accuracy": correct / len(edges),
                    "at_or_below_chance": 2 * correct <= len(edges),
                }
            )
        per_family[family] = row
    phase_accuracy = per_family["orientation_winding"]["phase_edge_accuracy"]
    return {
        "candidate_id": candidate["candidate_id"],
        "per_family": per_family,
        "heldout_phase_edge_accuracy": phase_accuracy,
        "heldout_all_demands_separated": all(
            row["collapsed_demand_edges"] == 0 for row in per_family.values()
        ),
        "chance_threshold": PHASE_CHANCE_ACCURACY,
        "luck_suspect": per_family["orientation_winding"]["at_or_below_chance"],
    }


def evaluate_split_seed(
    candidates: Sequence[dict[str, Any]],
    rows: Sequence[dict[str, Any]],
    demands: dict[str, list[tuple[int, int]]],
    seed: int,
) -> dict[str, Any]:
    splits = make_edge_splits(demands, seed)
    fit_demands = demands_from_split(splits, "fit_edges")
    heldout_demands = demands_from_split(splits, "heldout_edges")
    behaviours = build_behaviours(
        candidates, fit_demands, fit_induced_assignments=True
    )
    cache = gate_v1.compute_frontier_cache(behaviours, list(ACTIVE_FAMILY_ORDER))
    schedules = gate_v1.ordered_gate_hypotheses(ACTIVE_FAMILY_ORDER)
    schedule_receipts = gate_v1.execute_schedules(
        schedules, list(ACTIVE_FAMILY_ORDER), cache
    )
    full_mask = (1 << len(ACTIVE_FAMILY_ORDER)) - 1
    candidate_by_id = {row["candidate_id"]: row for row in candidates}
    fit_survivor_ids: list[str] = []
    for candidate in candidates:
        assignments = partition_assignments_on_edges(
            candidate["values"]["julia"], fit_demands
        )
        if all(
            assignments[left] != assignments[right]
            for edges in fit_demands.values()
            for left, right in edges
        ):
            fit_survivor_ids.append(candidate["candidate_id"])
    fit_survivor_ids.sort()
    scores = [
        score_candidate_heldout(candidate_by_id[candidate_id], rows, heldout_demands)
        for candidate_id in fit_survivor_ids
    ]
    eligible_ids = sorted(
        row["candidate_id"] for row in scores if not row["luck_suspect"]
    )
    eligible_candidates = [candidate_by_id[candidate_id] for candidate_id in eligible_ids]
    eligible_behaviours = build_behaviours(
        eligible_candidates, fit_demands, fit_induced_assignments=True
    )
    eligible_cache = gate_v1.compute_frontier_cache(
        eligible_behaviours, list(ACTIVE_FAMILY_ORDER)
    )
    postluck_frontier_candidate_ids = sorted(
        candidate_id
        for row in eligible_cache[full_mask]["frontier"]
        for candidate_id in row["members"]
    )
    return {
        "seed": seed,
        "split_rule": {
            "algorithm": "sha256 rank of seed, canonical family, edge index, row_i, row_j",
            "fit_count": "n-floor(n/3)",
            "heldout_count": "floor(n/3)",
            "selection_uses": "fit_edges_only",
            "fit_partition_rule": (
                "union only candidate-equal fit-edge endpoints; all other row-pair "
                "relations, including held-out pairs, are ignored"
            ),
            "scoring_uses": "heldout_edges_only",
        },
        "edge_splits": splits,
        "fit_behaviours": behaviours,
        "fit_frontier": {
            "behaviour_ids": cache[full_mask]["frontier_ids"],
            "behaviour_fingerprint": cache[full_mask]["frontier_fingerprint"],
            "candidate_ids": sorted(
                candidate_id
                for row in cache[full_mask]["frontier"]
                for candidate_id in row["members"]
            ),
        },
        "fit_survivor_candidate_ids": fit_survivor_ids,
        "postluck_eligible_pool_candidate_ids": eligible_ids,
        "postluck_frontier": {
            "behaviour_ids": eligible_cache[full_mask]["frontier_ids"],
            "behaviour_fingerprint": eligible_cache[full_mask]["frontier_fingerprint"],
            "candidate_ids": postluck_frontier_candidate_ids,
        },
        "heldout_scores": scores,
        "frontier_cache_summary": {
            str(mask): {
                "active_families": cache[mask]["active_families"],
                "survivor_count": cache[mask]["survivor_count"],
                "frontier_ids": cache[mask]["frontier_ids"],
                "frontier_fingerprint": cache[mask]["frontier_fingerprint"],
            }
            for mask in range(1 << len(ACTIVE_FAMILY_ORDER))
        },
        "gate_order_search": {
            "schedule_hypotheses_executed": len(schedule_receipts),
            "schedule_receipts": schedule_receipts,
            "pairwise_order_matrix": gate_v1._pairwise_order_matrix(
                list(ACTIVE_FAMILY_ORDER), cache
            ),
            "decomposition_census": gate_v1._decomposition_census(schedule_receipts),
            "distinct_endpoint_fingerprint_count": len(
                {row["final_frontier_fingerprint"] for row in schedule_receipts}
            ),
        },
    }


def consolidate_candidate_stability(
    candidates: Sequence[dict[str, Any]], split_results: Sequence[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        selected_seeds: list[int] = []
        postluck_frontier_seeds: list[int] = []
        phase_accuracy_by_seed: dict[str, float] = {}
        suspect_seeds: list[int] = []
        for split in split_results:
            score = next(
                (
                    row
                    for row in split["heldout_scores"]
                    if row["candidate_id"] == candidate_id
                ),
                None,
            )
            if score is None:
                continue
            seed = int(split["seed"])
            selected_seeds.append(seed)
            if candidate_id in split["postluck_frontier"]["candidate_ids"]:
                postluck_frontier_seeds.append(seed)
            accuracy = float(score["heldout_phase_edge_accuracy"])
            phase_accuracy_by_seed[str(seed)] = accuracy
            if score["luck_suspect"]:
                suspect_seeds.append(seed)
        stable_fit = selected_seeds == list(SPLIT_SEEDS)
        stable_postluck_frontier = postluck_frontier_seeds == list(SPLIT_SEEDS)
        luck_suspect = bool(suspect_seeds)
        enters_frontier = stable_postluck_frontier and not luck_suspect
        if luck_suspect:
            verdict = "LUCK_SUSPECT"
        elif stable_fit:
            verdict = "LUCK_CLEARED"
        elif selected_seeds:
            verdict = "FIT_UNSTABLE"
        else:
            verdict = "NOT_FIT_SURVIVOR"
        rows.append(
            {
                "candidate_id": candidate_id,
                "fit_selected_seeds": selected_seeds,
                "postluck_frontier_seeds": postluck_frontier_seeds,
                "heldout_phase_edge_accuracy_by_seed": phase_accuracy_by_seed,
                "luck_suspect_seeds": suspect_seeds,
                "luck_verdict": verdict,
                "stable_fit_survivor": stable_fit,
                "stable_postluck_frontier": stable_postluck_frontier,
                "enters_v2_frontier": enters_frontier,
            }
        )
    frontier = sorted(row["candidate_id"] for row in rows if row["enters_v2_frontier"])
    return rows, frontier


def import_noise_compiler(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("l6_noise_floor_compiler_v1", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot build import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize_basis_expression(value: str) -> str:
    expression = value.split("=", 1)[-1].strip()
    return "".join(expression.split()).lower()


def basis_lists(value: Any) -> Iterable[list[str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            if "basis" in str(key).lower() and isinstance(child, list) and all(
                isinstance(item, str) for item in child
            ):
                yield child
            yield from basis_lists(child)
    elif isinstance(value, list):
        for child in value:
            yield from basis_lists(child)


def validate_build_card_basis(card: FrozenInput) -> dict[str, Any]:
    expected = [normalize_basis_expression(value) for value in NOISE_BASIS_EXPRESSIONS]
    text = card.content.decode("utf-8")
    candidates: list[list[str]] = []
    try:
        candidates.extend(basis_lists(json.loads(text)))
    except json.JSONDecodeError:
        compact = "".join(text.split()).lower()
        positions: list[int] = []
        for index, expression in enumerate(NOISE_BASIS_EXPRESSIONS, start=1):
            declaration = f"phi{index}={expression}".replace(" ", "").lower()
            position = compact.find(declaration)
            if position < 0:
                positions = []
                break
            positions.append(position)
        if positions and positions == sorted(positions):
            candidates.append(list(NOISE_BASIS_EXPRESSIONS))
    for candidate in candidates:
        normalized = [normalize_basis_expression(value) for value in candidate]
        if normalized == expected:
            return {
                "path": rung_relative(card.path),
                "sha256": card.sha256,
                "validated_basis_expressions": list(NOISE_BASIS_EXPRESSIONS),
            }
    raise RuntimeError(
        f"BUILD_CARD does not declare the exact supported ordered noise basis: {card.path}"
    )


def fresh_noise_basis(
    rows: Sequence[dict[str, Any]], snapshot: InputSnapshot
) -> tuple[np.ndarray, dict[str, Any]]:
    compiler_path = CANDIDATE_ROOT / "noise-floor" / "compiler.py"
    try:
        module = import_noise_compiler(compiler_path)
        matrix = np.vstack([module.numpy_phi(dict(row)) for row in rows]).astype(np.float64)
        if matrix.shape != (18, 16):
            raise ValueError(f"noise compiler basis has shape {matrix.shape}")
        return matrix, {
            "method": "imported_noise_floor_compiler.numpy_phi",
            "compiler_path": rung_relative(compiler_path),
            "compiler_sha256": snapshot.by_path(compiler_path).sha256,
            "basis": list(module.BASIS),
            "build_card_fallback_present": any(
                (CANDIDATE_ROOT / "noise-floor").glob("BUILD_CARD*")
            ),
        }
    except Exception as exc:
        cards = sorted((CANDIDATE_ROOT / "noise-floor").glob("BUILD_CARD*"))
        if not cards:
            raise RuntimeError(
                "noise-floor compiler was not importable and no BUILD_CARD was present"
            ) from exc
        validations: list[dict[str, Any]] = []
        validation_errors: list[str] = []
        for path in cards:
            try:
                validations.append(validate_build_card_basis(snapshot.by_path(path)))
            except Exception as card_exc:
                validation_errors.append(f"{path.name}: {type(card_exc).__name__}: {card_exc}")
        if not validations:
            raise RuntimeError(
                "noise-floor compiler import failed and no BUILD_CARD declared the exact "
                f"supported basis; findings={validation_errors}"
            ) from exc
        matrix = gate_v1.basis_matrix(list(rows))
        return matrix, {
            "method": "rederived_after_exact_BUILD_CARD_basis_validation",
            "compiler_import_error": f"{type(exc).__name__}: {exc}",
            "validated_build_cards": validations,
            "rejected_build_card_findings": validation_errors,
            "basis_contract": list(NOISE_BASIS_EXPRESSIONS),
        }


def make_fresh_noise_candidates(
    base: np.ndarray, fresh_seed: int
) -> list[dict[str, Any]]:
    rng = np.random.default_rng(fresh_seed)
    candidates: list[dict[str, Any]] = []
    for draw_index in range(32):
        weights = rng.standard_normal(16).astype(np.float64)
        kind = "orientation_blind" if draw_index < 16 else "full_arity"
        if kind == "orientation_blind":
            weights[5] = 0.0
            weights[6] = 0.0
            weights[14] = 0.0
        values = (base @ weights).reshape(-1, 1)
        variant_id = f"fresh_seed_{fresh_seed}_v{draw_index:02d}"
        candidates.append(
            {
                "lane_family": "fresh-noise-control",
                "variant_id": variant_id,
                "candidate_id": f"fresh-noise-control:{variant_id}",
                "noise_kind": kind,
                "weights": [float(value) for value in weights],
                "values": {engine: values.copy() for engine in ENGINES},
                "declared_signs": {family: None for family in RAW_FAMILY_ORDER},
            }
        )
    return candidates


def run_fresh_noise_stability(
    rows: Sequence[dict[str, Any]],
    demands: dict[str, list[tuple[int, int]]],
    snapshot: InputSnapshot,
) -> dict[str, Any]:
    base, basis_provenance = fresh_noise_basis(rows, snapshot)
    variants_path = CANDIDATE_ROOT / "noise-floor" / "variants_v1.json"
    manifest_path = CANDIDATE_ROOT / "noise-floor" / "injection_manifest_v1.json"
    recorded_variants = snapshot.by_path(variants_path).json()["variants"]
    injected_id = str(snapshot.by_path(manifest_path).json()["injected_variant_id"])
    noise_behavior_frozen = next(
        item for item in snapshot.behavior_files if item.path.parent.name == "noise-floor"
    )
    noise_behavior = noise_behavior_frozen.json()
    declared_variants_hash = (noise_behavior.get("inputs") or {}).get(
        "variants_v1_sha256"
    )
    if declared_variants_hash is not None and str(declared_variants_hash) != snapshot.by_path(
        variants_path
    ).sha256:
        raise RuntimeError("noise-floor behavior declares a stale variants_v1 hash")
    recorded_random_weights = [
        np.asarray(variant["weights"], dtype=np.float64)
        for variant in recorded_variants
        if str(variant["variant_id"]) != injected_id
    ]
    regenerated_seed0 = make_fresh_noise_candidates(base, 0)
    if len(recorded_random_weights) != len(regenerated_seed0):
        raise RuntimeError("seed-0 noise rederivation count differs from recorded variants")
    seed0_max_delta = max(
        float(np.max(np.abs(recorded - np.asarray(generated["weights"], dtype=np.float64))))
        for recorded, generated in zip(
            recorded_random_weights, regenerated_seed0, strict=True
        )
    )
    if seed0_max_delta != 0.0:
        raise RuntimeError(
            f"seed-0 noise rederivation differs from recorded variants: {seed0_max_delta}"
        )
    recorded_random_behaviors = [
        variant
        for variant_id, variant in variant_items(noise_behavior)
        if variant_id != injected_id
    ]
    if len(recorded_random_behaviors) != len(regenerated_seed0):
        raise RuntimeError("seed-0 noise behavior count differs after injected exclusion")
    seed0_max_value_delta = 0.0
    for recorded, generated in zip(
        recorded_random_behaviors, regenerated_seed0, strict=True
    ):
        generated_values = generated["values"]["julia"]
        for engine in ENGINES:
            recorded_values = np.asarray(
                recorded["per_row_values"][engine], dtype=np.float64
            ).reshape(18, -1)
            seed0_max_value_delta = max(
                seed0_max_value_delta,
                float(np.max(np.abs(recorded_values - generated_values))),
            )
    if seed0_max_value_delta >= 1e-9:
        raise RuntimeError(
            "seed-0 noise output rederivation differs from recorded behavior: "
            f"{seed0_max_value_delta}"
        )
    batches: list[dict[str, Any]] = []
    passing_ids: list[str] = []
    for fresh_seed in FRESH_NOISE_SEEDS:
        candidates = make_fresh_noise_candidates(base, fresh_seed)
        split_results = [
            evaluate_split_seed(candidates, rows, demands, split_seed)
            for split_seed in SPLIT_SEEDS
        ]
        stability, frontier = consolidate_candidate_stability(candidates, split_results)
        strict_passing_ids = sorted(
            candidate_id
            for candidate_id in frontier
            if all(
                next(
                    row
                    for row in split["heldout_scores"]
                    if row["candidate_id"] == candidate_id
                )["heldout_all_demands_separated"]
                for split in split_results
            )
        )
        passing_ids.extend(strict_passing_ids)
        batches.append(
            {
                "fresh_seed": fresh_seed,
                "generated_random_functionals": len(candidates),
                "orientation_blind_count": 16,
                "full_arity_count": 16,
                "stability": stability,
                "postluck_frontier_before_all_demand_heldout_check": frontier,
                "heldout_passing_frontier": strict_passing_ids,
            }
        )
    passing_ids = sorted(passing_ids)
    cohorts_with_passers = [
        batch["fresh_seed"] for batch in batches if batch["heldout_passing_frontier"]
    ]
    return {
        "fresh_seeds": list(FRESH_NOISE_SEEDS),
        "basis_provenance": basis_provenance,
        "seed0_rederivation_validation": {
            "recorded_random_functional_count": len(recorded_random_weights),
            "injected_variant_excluded": injected_id,
            "max_abs_weight_delta": seed0_max_delta,
            "max_abs_recorded_value_delta": seed0_max_value_delta,
            "value_tolerance": 1e-9,
            "pass": True,
        },
        "batches": batches,
        "fresh_random_functionals_passed_heldout": bool(passing_ids),
        "fresh_seed_cohorts_with_passers": cohorts_with_passers,
        "every_fresh_seed_cohort_has_passer": cohorts_with_passers
        == list(FRESH_NOISE_SEEDS),
        "heldout_passing_candidate_ids": passing_ids,
        "packet_verdict_component": (
            "SURFACE_UNDERCONSTRAINED" if passing_ids else "NO_FRESH_NOISE_SURVIVOR"
        ),
        "finding_scope": "surface finding, never a candidate result",
    }


def input_receipts(snapshot: InputSnapshot) -> list[dict[str, str]]:
    return [
        {"path": rung_relative(item.path), "sha256": item.sha256}
        for item in sorted(snapshot.files, key=lambda item: rung_relative(item.path))
    ]


def snapshot_manifest(snapshot: InputSnapshot) -> dict[str, Any]:
    return {
        "candidate_directories": list(snapshot.candidate_directories),
        "present_families": list(snapshot.present_families),
        "absent_families": list(snapshot.absent_families),
        "files": input_receipts(snapshot),
    }


def build_receipt(snapshot: InputSnapshot) -> dict[str, Any]:
    surface_path = RUNG_DIR / "surface" / "surface_v1.json"
    demand_path = RUNG_DIR / "surface" / "demand_families_v1.json"
    surface = snapshot.by_path(surface_path).json()
    demand_payload = snapshot.by_path(demand_path).json()
    rows, demands = validate_surface_and_demands(surface, demand_payload)
    candidates = normalize_candidates(
        snapshot.behavior_files,
        demands,
        surface_sha256=snapshot.by_path(surface_path).sha256,
        demands_sha256=snapshot.by_path(demand_path).sha256,
    )
    if REQUIRED_V1_CONTROL_FAMILY not in snapshot.present_families:
        raise RuntimeError(
            "MISSING_REQUIRED_CONTROL_FAMILY: noise-floor behavior is required to retain "
            "the v1 source-attribution and anti-by-construction controls; no v2 receipt written"
        )
    required_noise_sidecars = (
        CANDIDATE_ROOT / "noise-floor" / "compiler.py",
        CANDIDATE_ROOT / "noise-floor" / "variants_v1.json",
        CANDIDATE_ROOT / "noise-floor" / "injection_manifest_v1.json",
    )
    frozen_paths = {item.path.resolve() for item in snapshot.files}
    missing_sidecars = [
        rung_relative(path) for path in required_noise_sidecars if path.resolve() not in frozen_paths
    ]
    if missing_sidecars:
        raise RuntimeError(
            "MISSING_REQUIRED_CONTROL_SIDECAR: " + ", ".join(missing_sidecars)
        )
    validity, open_digs = validate_candidate_behaviors(candidates, demands)

    split_results = [
        evaluate_split_seed(candidates, rows, demands, seed) for seed in SPLIT_SEEDS
    ]
    stability, v2_frontier = consolidate_candidate_stability(candidates, split_results)

    full_behaviours = build_behaviours(candidates, demands)

    phase_erasure, erased_class, phase_groups, phase_pairs = gate_v1.run_phase_erasure(
        rows, list(candidates), demands
    )
    noise_candidates = [
        candidate for candidate in candidates if candidate["lane_family"] == "noise-floor"
    ]
    variants_path = CANDIDATE_ROOT / "noise-floor" / "variants_v1.json"
    manifest_path = CANDIDATE_ROOT / "noise-floor" / "injection_manifest_v1.json"
    variants_payload = snapshot.by_path(variants_path).json()
    detector, detector_outcomes = gate_v1.run_detector(
        rows, demands["orientation_winding"], noise_candidates, variants_payload
    )
    detected_noise_ids = sorted(
        candidate["variant_id"]
        for candidate in noise_candidates
        if detector_outcomes.get(candidate["variant_id"], False)
    )
    injection_manifest = snapshot.by_path(manifest_path).json()
    manifest_id = str(injection_manifest["injected_variant_id"])
    attribution = {
        "manifest_injected_id": manifest_id,
        "detected_ids": detected_noise_ids,
        "detected_contains_manifest_id": manifest_id in detected_noise_ids,
        "extra_flags": [value for value in detected_noise_ids if value != manifest_id],
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
    smt = gate_v1.run_smt(rows, demands, erased_class)
    fresh_noise = run_fresh_noise_stability(rows, demands, snapshot)

    open_digs.extend(
        {"kind": "missing_candidate_family", "candidate_family": family}
        for family in snapshot.absent_families
    )
    open_attacks = [
        {
            "attack_id": "total_partition_grammar_excludes_partial_presentations",
            "status": "OPEN",
            "finding": (
                "The executed grammar's primitive is a total partition of fixed X. "
                "Candidates that abstain on rows are partial presentations and are not yet in "
                "the grammar; totality may be doing unearned work."
            ),
            "citation": REFEREE_ATTACK,
            "blocked_consumer": "carrier-rung or L6 closure over a broader candidate grammar",
        },
        {
            "attack_id": "missing_candidate_families_at_run_time",
            "status": "OPEN" if snapshot.absent_families else "NOT_TRIGGERED",
            "present": list(snapshot.present_families),
            "absent": list(snapshot.absent_families),
            "blocked_consumer": "claim that the candidate-family packet was complete",
        },
        {
            "attack_id": "eighteen_row_surface_size",
            "status": "OPEN",
            "finding": (
                "All selection and held-out scoring remains internal to eighteen rows; "
                "the result does not establish out-of-surface generalization."
            ),
            "observed_row_count": len(rows),
            "blocked_consumer": "general or asymptotic L6 claim",
        },
        {
            "attack_id": "noncooperating_inventory_publication_race",
            "status": "OPEN",
            "finding": (
                "The runner freezes inputs and performs pre-publication rescans, but no "
                "shared writer lock binds independent family landers between the final "
                "rescan and atomic receipt link. Detected drift blocks publication; an "
                "uncooperating write in that residual interval is not mechanically excluded."
            ),
            "blocked_consumer": "claim of lock-serial inventory completeness",
        },
    ]

    checks: list[dict[str, Any]] = []
    gate_v1.add_check(checks, "fixture_row_count", len(rows) == 18, len(rows))
    gate_v1.add_check(
        checks,
        "duplicate_edge_families_identical",
        sorted(demands["marginal_entropy_level"])
        == sorted(demands["shell_position"]),
    )
    gate_v1.add_check(checks, "active_survivor_family_count", len(ACTIVE_FAMILY_ORDER) == 3)
    for split in split_results:
        seed = split["seed"]
        for family, row in split["edge_splits"].items():
            fit = set(row["fit_edge_ids"])
            heldout = set(row["heldout_edge_ids"])
            gate_v1.add_check(
                checks, f"split_{seed}_{family}_disjoint", not (fit & heldout)
            )
            gate_v1.add_check(
                checks,
                f"split_{seed}_{family}_exhaustive",
                fit | heldout == set(range(row["edge_count"])),
            )
        gate_v1.add_check(
            checks,
            f"split_{seed}_all_fit_survivors_scored",
            len(split["fit_survivor_candidate_ids"]) == len(split["heldout_scores"]),
        )
        gate_v1.add_check(
            checks,
            f"split_{seed}_luck_suspects_excluded",
            not (
                {
                    row["candidate_id"]
                    for row in split["heldout_scores"]
                    if row["luck_suspect"]
                }
                & set(split["postluck_eligible_pool_candidate_ids"])
            ),
        )
        gate_v1.add_check(
            checks,
            f"split_{seed}_ordered_set_partition_schedule_count",
            split["gate_order_search"]["schedule_hypotheses_executed"] == 13,
            split["gate_order_search"]["schedule_hypotheses_executed"],
        )
        gate_v1.add_check(
            checks,
            f"split_{seed}_frontier_cache_mask_count",
            len(split["frontier_cache_summary"]) == 8,
            len(split["frontier_cache_summary"]),
        )
    gate_v1.add_check(
        checks,
        "phase_classes_match_orientation_edges",
        sorted(tuple(sorted(pair)) for pair in phase_pairs)
        == sorted(tuple(sorted(pair)) for pair in demands["orientation_winding"]),
    )
    phase_targets = expected_phase_signs(rows, demands["orientation_winding"])
    gate_v1.add_check(
        checks,
        "phase_direction_targets_all_positive",
        phase_targets == [1] * len(demands["orientation_winding"]),
        phase_targets,
    )
    gate_v1.add_check(checks, "phase_erased_class_count", len(phase_groups) == 9)
    gate_v1.add_check(
        checks,
        "phase_erased_class_sizes",
        all(len(group) == 2 for group in phase_groups),
        [len(group) for group in phase_groups],
    )
    gate_v1.add_check(
        checks,
        "phase_erasure_zeroes_all_orientation_signs",
        phase_erasure["all_orientation_signs_zero_after"],
    )
    gate_v1.add_check(
        checks,
        "phase_erasure_flips_every_previously_carrying_variant",
        phase_erasure["all_previously_carrying_flipped"],
    )
    gate_v1.add_check(
        checks,
        "anti_result_copy_flagged",
        detector_outcomes["gate_anti_result_copy"] is True,
    )
    gate_v1.add_check(
        checks,
        "declared_arity_counter_not_flagged",
        detector_outcomes["gate_declared_arity_counter"] is False,
    )
    gate_v1.add_check(
        checks,
        "manifest_injected_functional_detected_behaviorally",
        attribution["detected_contains_manifest_id"],
        detected_noise_ids,
    )
    real_by_id = {row["instance_id"]: row for row in smt["real_instances"]}
    for solver in ("z3", "cvc5"):
        gate_v1.add_check(
            checks,
            f"real_orientation_winding_unsat_{solver}",
            real_by_id["real_orientation_winding"]["solvers"][solver]["result"]
            == "UNSAT",
        )
        for control_name in ("erased_control_a", "erased_control_b"):
            gate_v1.add_check(
                checks,
                f"{control_name}_sat_{solver}",
                smt[control_name]["solvers"][solver]["result"] == "SAT",
            )
    gate_v1.add_check(
        checks, "all_smt_instances_solver_agreement", smt["all_solver_results_agree"]
    )
    gate_v1.add_check(
        checks,
        "erased_control_a_has_zero_edges",
        smt["erased_control_a"]["edge_count"] == 0,
    )
    gate_v1.add_check(
        checks,
        "v2_frontier_contains_no_luck_suspect",
        not any(
            row["enters_v2_frontier"] and row["luck_verdict"] == "LUCK_SUSPECT"
            for row in stability
        ),
    )
    gate_v1.add_check(
        checks, "fresh_noise_seed_count", len(fresh_noise["fresh_seeds"]) == 3
    )
    gate_v1.add_check(
        checks,
        "fresh_noise_seed0_rederivation_matches",
        fresh_noise["seed0_rederivation_validation"]["pass"],
    )
    failed = [row["name"] for row in checks if not row["pass"]]
    if failed:
        raise RuntimeError(f"Gate V2 internal validation failed: {failed[0]}")

    schema_path = gate_v1.ENGINE_DIR / "schemas" / "ratchet_order_open_run.schema.json"
    schema = snapshot.by_path(schema_path).json()
    receipt: dict[str, Any] = {
        "schema_version": "l6_phase_entropy_rung_receipt/2.0",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "claim_ceiling": (
            "scratch_diagnostic held-out gate over a total-partition grammar on eighteen "
            "rows; no L6 rung adjudication, partial-presentation coverage, manifold, or "
            "physics claim"
        ),
        "executed_grammar_boundary": {
            "carrier": "fixed X with eighteen rows",
            "presentation_type": "total partition assignment over every row",
            "partial_presentations_supported": False,
            "abstaining_or_missing_row_policy": "fail closed; never impute",
        },
        "determinism": {
            "in_memory_build_count": 2,
            "byte_identity_required": True,
            "byte_identity_pass": True,
            "timestamps_excluded_from_rung_receipt": True,
        },
        "inputs": input_receipts(snapshot),
        "candidate_families": {
            "inventory_semantics": (
                "frozen process-start snapshot with best-effort pre-publication rescans; "
                "detected drift blocks atomic publication, while the explicitly recorded "
                "noncooperating rescan-to-link race remains open"
            ),
            "expected_or_discovered": sorted(
                set(EXPECTED_CANDIDATE_FAMILIES) | set(snapshot.candidate_directories)
            ),
            "hard_prerequisite_for_retained_v1_controls": REQUIRED_V1_CONTROL_FAMILY,
            "present": list(snapshot.present_families),
            "absent": list(snapshot.absent_families),
            "behavior_files_read": [
                rung_relative(item.path) for item in snapshot.behavior_files
            ],
        },
        "demand_family_rule": {
            "raw_reported_names": list(RAW_FAMILY_ORDER),
            "active_survivor_math_families": list(ACTIVE_FAMILY_ORDER),
            "aliases": {key: list(value) for key, value in FAMILY_ALIASES.items()},
            "no_double_counting_declaration": (
                "marginal_entropy_level and shell_position have identical ordered row-pair "
                "edge sets on this branch and contribute one demand family to survivor math; "
                "both names remain reported"
            ),
        },
        "validity": validity,
        "full_packet_coface_behaviours_reporting_only": full_behaviours,
        "heldout_edge_gate": {
            "split_seeds": list(SPLIT_SEEDS),
            "phase_chance_accuracy": PHASE_CHANCE_ACCURACY,
            "phase_accuracy_target": (
                "sign(surface[row_j].orientation - surface[row_i].orientation); "
                "every current orientation_winding target is nonzero and +1"
            ),
            "chance_model": (
                "iid fair binary sign conditional on a nonzero prediction; zero is wrong; "
                "at-or-below chance is tested exactly as 2*correct <= heldout_count"
            ),
            "small_heldout_limitation": (
                "orientation_winding has only three held-out edges per split and split "
                "overlap is possible; no statistical-confidence claim is made"
            ),
            "luck_rule": (
                "a fit-selected candidate with held-out phase-edge directional accuracy "
                "less than or equal to 0.5 on any split seed is LUCK_SUSPECT and excluded"
            ),
            "split_results": split_results,
            "candidate_stability": stability,
            "frontier_candidate_ids": v2_frontier,
        },
        "fresh_seed_noise_stability": fresh_noise,
        "packet_verdict_components": [
            {
                "component": "heldout_candidate_frontier",
                "verdict": "COMPUTED_WITH_LUCK_EXCLUSION",
                "frontier_candidate_ids": v2_frontier,
            },
            {
                "component": "fresh_seed_noise_surface_test",
                "verdict": fresh_noise["packet_verdict_component"],
                "scope": "surface finding, not a candidate result",
            },
        ],
        "controls": {
            "phase_erasure": phase_erasure,
            "behavioral_source_attribution": detector,
            "anti_by_construction": anti_by_construction,
        },
        "kill_attribution": {
            "behavioral_source_attribution": attribution,
            "luck_suspects": [
                row for row in stability if row["luck_verdict"] == "LUCK_SUSPECT"
            ],
        },
        "smt": smt,
        "open_attacks": open_attacks,
        "open_digs": open_digs,
        "tool_manifest": {
            "numpy": "deterministic finite edge splits, value arrays, and fresh-noise controls",
            "ratchet_engine": "load-bearing partition-refinement frontier and all ordered set-partitions",
            "z3": "load-bearing direct structural inequality instance with erased-control flip",
            "cvc5": "independent load-bearing cross-check of the same structural polarity",
        },
        "tool_integration_depth": {
            "ratchet_engine": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "numpy": "supportive",
        },
        "engine_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "z3": gate_v1.z3.get_version_string(),
            "cvc5": gate_v1.cvc5.__version__,
        },
        "v0_5_schema_fit": {},
        "internal_validation": {"checks": checks, "all_pass": True},
    }
    missing_schema_keys = [
        key for key in schema.get("required", []) if key not in receipt
    ]
    receipt["v0_5_schema_fit"] = {
        "fits_required_top_level_keys": not missing_schema_keys,
        "required_keys_lacked": missing_schema_keys,
    }
    return receipt


def canonical_bytes(data: Any) -> bytes:
    return (json.dumps(data, sort_keys=True, indent=2) + "\n").encode("utf-8")


def write_receipt_append_only(content: bytes, snapshot: InputSnapshot) -> None:
    """Publish a new v2 receipt atomically after a final frozen-input rescan."""
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".rung_receipt_v2.pending.",
            dir=SCRIPT_DIR,
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if snapshot_manifest(discover_inputs()) != snapshot_manifest(snapshot):
            raise RuntimeError(
                "INPUT_DRIFT_DURING_RUN: candidate inventory or input bytes changed "
                "before atomic receipt publication"
            )
        try:
            os.link(temporary_path, RUNG_RECEIPT)
        except FileExistsError:
            if RUNG_RECEIPT.read_bytes() != content:
                raise RuntimeError(
                    "BYTE_IDENTITY_FINDING: existing rung_receipt_v2.json differs from this run"
                )
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def print_summary(receipt: dict[str, Any]) -> None:
    heldout = receipt["heldout_edge_gate"]
    print("HEADLINE TABLE")
    print(
        "candidate_id | fit_selected_seeds | heldout_phase_accuracy[s0,s1,s2] | "
        "luck_verdict | v2_frontier"
    )
    for row in heldout["candidate_stability"]:
        accuracies = row["heldout_phase_edge_accuracy_by_seed"]
        display = ",".join(
            "-" if str(seed) not in accuracies else f"{accuracies[str(seed)]:.6f}"
            for seed in SPLIT_SEEDS
        )
        print(
            f"{row['candidate_id']} | {row['fit_selected_seeds']} | {display} | "
            f"{row['luck_verdict']} | {'yes' if row['enters_v2_frontier'] else 'no'}"
        )
    print(f"FRONTIER candidate_ids={heldout['frontier_candidate_ids']}")
    for split in heldout["split_results"]:
        print(
            f"FRONTIER seed={split['seed']} fit_only={split['fit_frontier']['candidate_ids']} "
            f"postluck={split['postluck_frontier']['candidate_ids']}"
        )
    for row in heldout["candidate_stability"]:
        if row["fit_selected_seeds"]:
            print(
                f"LUCK candidate={row['candidate_id']} verdict={row['luck_verdict']} "
                f"accuracies={json.dumps(row['heldout_phase_edge_accuracy_by_seed'], sort_keys=True)}"
            )
    fresh = receipt["fresh_seed_noise_stability"]
    print(
        f"SURFACE verdict={fresh['packet_verdict_component']} "
        f"fresh_heldout_passing_count={len(fresh['heldout_passing_candidate_ids'])}"
    )
    print(
        "CANDIDATE_FAMILIES "
        f"present={receipt['candidate_families']['present']} "
        f"absent={receipt['candidate_families']['absent']}"
    )
    print(
        f"INTERNAL_VALIDATION: ALL PASS "
        f"({len(receipt['internal_validation']['checks'])} checks; two byte-identical builds)"
    )


def main() -> int:
    snapshot = discover_inputs()
    first = canonical_bytes(build_receipt(snapshot))
    second = canonical_bytes(build_receipt(snapshot))
    if first != second:
        print("BYTE_IDENTITY_FINDING: two in-memory Gate V2 builds differ", file=sys.stderr)
        return 1
    current_snapshot = discover_inputs()
    if snapshot_manifest(current_snapshot) != snapshot_manifest(snapshot):
        print(
            "INPUT_DRIFT_DURING_RUN: candidate inventory or input bytes changed",
            file=sys.stderr,
        )
        return 1
    write_receipt_append_only(first, snapshot)
    print_summary(json.loads(first.decode("utf-8")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            f"INTERNAL_VALIDATION: FAIL (exception: {type(exc).__name__}: {exc})",
            file=sys.stderr,
        )
        raise SystemExit(1)
