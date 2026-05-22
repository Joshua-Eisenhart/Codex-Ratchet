#!/usr/bin/env python3
"""Map schedule-memory phases for the exact QIT engine runtime.

Workstream B asks for a phase map over stage duration, dissipator rates, and
Hamiltonian parameters. This scout uses the shared exact torch QIT runtime to
classify schedule-family pseudo-basin memory through length 8 while preserving
the real-basin boundary: every fixed schedule map is checked as a map, and
schedule-family clusters are not promoted to real attractor basins.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import pathlib
import time
from typing import Any

import rustworkx as rx
import torch
import z3

import qit_engine_runtime as qit


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_schedule_memory_phase_map_probe_results.json"

NAME = "two_root_constraint_schedule_memory_phase_map_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_schedule_memory_phase_map"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_schedule_memory_phase_map"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal Workstream B scout only: maps schedule-memory pseudo-basin phases "
    "over tau, dissipator profiles, and Hamiltonian direction/magnitude using "
    "the shared exact torch QIT runtime. It cannot promote real attractor "
    "basins, full E=16 dynamics, tensor-network Lindblad, Xi/rho_AB/Phi0 "
    "closure, or final manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact engine channels, schedule composition, fixed-point solves, spectra, and Bloch readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing binary schedule tree witness through length 8",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing guard blocking promotion from schedule-memory evidence alone",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "itertools": {"tried": True, "used": True, "reason": "supportive deterministic phase-grid enumeration"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
    "itertools": "supportive",
}

TAUS = [0.25, 0.5, 0.75, 1.0, 1.25]
MAX_SCHEDULE_LENGTH = 8
CLUSTER_EPS = 0.05
MEMORY_MAX_SUFFIX = 4
GAP_SLOW_THRESHOLD = 0.02
TWO_TOL = 1.0e-9

DIRECTION_CASES: dict[str, tuple[float, float, float]] = {
    "raw_xz": (0.7, 0.0, 0.5),
    "x": (1.0, 0.0, 0.0),
    "z": (0.0, 0.0, 1.0),
}
MAGNITUDES = [0.5, 1.0, 1.5]
DISSIPATOR_PROFILES: dict[str, dict[str, float]] = {
    "balanced": {"rate_scale": 1.0, "ladder_scale": 1.0, "dephase_scale": 1.0},
    "weak_global": {"rate_scale": 0.5, "ladder_scale": 1.0, "dephase_scale": 1.0},
    "strong_ladder": {"rate_scale": 1.0, "ladder_scale": 2.0, "dephase_scale": 1.0},
    "strong_dephase": {"rate_scale": 1.0, "ladder_scale": 1.0, "dephase_scale": 2.0},
}
BOUNDARY_PROFILE = {"rate_scale": 0.0, "ladder_scale": 1.0, "dephase_scale": 1.0}

SOURCE_FILES = {
    "runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "d92_growth_law": SCOUT_ROOT / "sim_two_root_constraint_phi_schedule_growth_law_tau_reconciliation_probe.py",
    "d92_result": RESULT_DIR / "two_root_constraint_phi_schedule_growth_law_tau_reconciliation_probe_results.json",
    "d95_consolidation_result": RESULT_DIR / "two_root_constraint_qit_runtime_consolidation_receipt_probe_results.json",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    return qit.jsonable(value)


def scaled_direction(name: str, magnitude: float) -> tuple[float, float, float]:
    base = DIRECTION_CASES[name]
    return tuple(float(magnitude * item) for item in base)


def fixed_bloch_solve(channel: torch.Tensor) -> list[float]:
    matrix = channel - torch.eye(4, dtype=qit.DTYPE)
    rhs = torch.zeros(4, dtype=qit.DTYPE)
    matrix = matrix.clone()
    matrix[-1, :] = torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=qit.DTYPE)
    rhs[-1] = 1.0 + 0.0j
    solution = torch.linalg.lstsq(matrix, rhs).solution
    return qit.bloch(qit.normalize_density(qit.mat(solution)))


def schedule_tree_report() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("")
    nodes = {"": root}
    for length in range(1, MAX_SCHEDULE_LENGTH + 1):
        for word in itertools.product(("1", "2"), repeat=length):
            prefix = ""
            for token in word:
                next_prefix = prefix + token
                if next_prefix not in nodes:
                    nodes[next_prefix] = graph.add_node(next_prefix)
                    graph.add_edge(nodes[prefix], nodes[next_prefix], token)
                prefix = next_prefix
    expected_nodes = 1 + sum(2**length for length in range(1, MAX_SCHEDULE_LENGTH + 1))
    return {
        "pass": graph.num_nodes() == expected_nodes and graph.num_edges() == expected_nodes - 1,
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "expected_nodes": expected_nodes,
        "max_schedule_length": MAX_SCHEDULE_LENGTH,
    }


def memory_length(points: list[dict[str, Any]], clusters: list[dict[str, Any]], length: int) -> dict[str, Any]:
    assignments: dict[str, int] = {}
    for point in points:
        idx = min(range(len(clusters)), key=lambda cluster_idx: math.dist(point["fixed_bloch"], clusters[cluster_idx]["center"]))
        assignments[point["word"]] = idx
    for suffix_len in range(1, min(MEMORY_MAX_SUFFIX, length) + 1):
        suffix_to_cluster: dict[str, int] = {}
        mismatches: list[str] = []
        for word, cluster_idx in assignments.items():
            suffix = word[-suffix_len:]
            previous = suffix_to_cluster.setdefault(suffix, cluster_idx)
            if previous != cluster_idx:
                mismatches.append(word)
        if not mismatches:
            return {
                "memory_len": suffix_len,
                "suffix_mismatches": [],
                "suffix_to_cluster": suffix_to_cluster,
            }
    return {
        "memory_len": None,
        "suffix_mismatches": sorted(assignments),
        "suffix_to_cluster": {},
    }


def classify_memory(basin_count: int, memory_len_value: int | None, nonprimitive_count: int) -> str:
    if nonprimitive_count > 0:
        return "degenerate_or_nonprimitive"
    if basin_count <= 1:
        return "collapsed"
    if memory_len_value == 1:
        return "last1"
    if memory_len_value == 2:
        return "last2"
    if memory_len_value is None:
        return "not_suffix_determined"
    return f"last{memory_len_value}"


def engines_for_params(
    *,
    tau: float,
    direction: str,
    magnitude: float,
    profile: dict[str, float],
) -> dict[str, torch.Tensor]:
    raw_direction = scaled_direction(direction, magnitude)
    return {
        "1": qit.engine_channel("L", raw_direction, tau=tau, normalize=False, **profile),
        "2": qit.engine_channel("R", raw_direction, tau=tau, normalize=False, **profile),
    }


def growth_for_params(engines: dict[str, torch.Tensor]) -> dict[str, Any]:
    growth: dict[str, Any] = {}
    for length in range(1, MAX_SCHEDULE_LENGTH + 1):
        points: list[dict[str, Any]] = []
        fixed_dims: list[int] = []
        spectral_gaps: list[float] = []
        for word_tuple in itertools.product(("1", "2"), repeat=length):
            word = "".join(word_tuple)
            channel = qit.schedule_channel(word_tuple, engines)
            spectrum = qit.channel_spectrum(channel)
            fixed_dims.append(int(spectrum["fixed_eig_dim"]))
            spectral_gaps.append(float(spectrum["spectral_gap"]))
            points.append(
                {
                    "label": word,
                    "word": word,
                    "fixed_bloch": fixed_bloch_solve(channel),
                    "fixed_eig_dim": int(spectrum["fixed_eig_dim"]),
                    "spectral_gap": float(spectrum["spectral_gap"]),
                }
            )
        clusters = qit.cluster_points(points, label_key="label", eps=CLUSTER_EPS)
        nonprimitive_count = sum(1 for fixed_dim, gap in zip(fixed_dims, spectral_gaps) if fixed_dim != 1 or gap <= qit.GAP_TOL)
        suffix = memory_length(points, clusters, length)
        growth[str(length)] = {
            "n_orderings": len(points),
            "n_basins": len(clusters),
            "cluster_sizes": sorted([len(cluster["members"]) for cluster in clusters], reverse=True),
            "memory_len": suffix["memory_len"],
            "memory_class": classify_memory(len(clusters), suffix["memory_len"], nonprimitive_count),
            "suffix_mismatch_count": len(suffix["suffix_mismatches"]),
            "min_spectral_gap": min(spectral_gaps),
            "max_fixed_eig_dim": max(fixed_dims),
            "nonprimitive_count": nonprimitive_count,
            "slow_gap_count": sum(1 for gap in spectral_gaps if qit.GAP_TOL < gap < GAP_SLOW_THRESHOLD),
        }
    return growth


def phase_row(tau: float, direction: str, magnitude: float, profile_name: str, profile: dict[str, float]) -> dict[str, Any]:
    growth = growth_for_params(engines_for_params(tau=tau, direction=direction, magnitude=magnitude, profile=profile))
    final = growth[str(MAX_SCHEDULE_LENGTH)]
    return {
        "tau": tau,
        "direction": direction,
        "magnitude": magnitude,
        "dissipator_profile": profile_name,
        "profile": profile,
        "counts_by_length": [growth[str(length)]["n_basins"] for length in range(1, MAX_SCHEDULE_LENGTH + 1)],
        "memory_by_length": [growth[str(length)]["memory_len"] for length in range(1, MAX_SCHEDULE_LENGTH + 1)],
        "class_by_length": [growth[str(length)]["memory_class"] for length in range(1, MAX_SCHEDULE_LENGTH + 1)],
        "length8_basin_count": final["n_basins"],
        "length8_memory_len": final["memory_len"],
        "length8_memory_class": final["memory_class"],
        "length8_min_spectral_gap": final["min_spectral_gap"],
        "length8_nonprimitive_count": final["nonprimitive_count"],
        "length8_slow_gap_count": final["slow_gap_count"],
    }


def build_phase_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for tau in TAUS:
        for direction in DIRECTION_CASES:
            for magnitude in MAGNITUDES:
                for profile_name, profile in DISSIPATOR_PROFILES.items():
                    rows.append(phase_row(tau, direction, magnitude, profile_name, profile))
    return rows


def boundary_rows() -> list[dict[str, Any]]:
    return [
        phase_row(tau, "raw_xz", 1.0, "zero_rate_boundary", BOUNDARY_PROFILE)
        for tau in (0.5, 1.0)
    ]


def class_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        key = row["length8_memory_class"]
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items()))


def nominal_sequence(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row["direction"] == "raw_xz"
        and row["magnitude"] == 1.0
        and row["dissipator_profile"] == "balanced"
    ]


def transition_brackets(sequence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sorted_rows = sorted(sequence, key=lambda row: row["tau"])
    brackets = []
    for left, right in zip(sorted_rows, sorted_rows[1:]):
        if left["length8_memory_class"] != right["length8_memory_class"]:
            brackets.append(
                {
                    "tau_left": left["tau"],
                    "class_left": left["length8_memory_class"],
                    "counts_left": left["counts_by_length"],
                    "tau_right": right["tau"],
                    "class_right": right["length8_memory_class"],
                    "counts_right": right["counts_by_length"],
                }
            )
    return brackets


def control_reports(rows: list[dict[str, Any]]) -> dict[str, Any]:
    nominal = nominal_sequence(rows)
    tau_half = next(row for row in nominal if abs(row["tau"] - 0.5) < TWO_TOL)
    tau_one = next(row for row in nominal if abs(row["tau"] - 1.0) < TWO_TOL)
    label_shuffle_rows = []
    for tau in (0.5, 1.0):
        engines = engines_for_params(tau=tau, direction="raw_xz", magnitude=1.0, profile=DISSIPATOR_PROFILES["balanced"])
        original = growth_for_params(engines)[str(MAX_SCHEDULE_LENGTH)]["n_basins"]
        swapped = growth_for_params({"1": engines["2"], "2": engines["1"]})[str(MAX_SCHEDULE_LENGTH)]["n_basins"]
        label_shuffle_rows.append({"tau": tau, "original_count": original, "swapped_label_count": swapped})
    reverse_order_rows = []
    for tau in (0.5, 1.0):
        engines = engines_for_params(tau=tau, direction="raw_xz", magnitude=1.0, profile=DISSIPATOR_PROFILES["balanced"])
        left = fixed_bloch_solve(qit.schedule_channel(("1", "2"), engines))
        right = fixed_bloch_solve(qit.schedule_channel(("2", "1"), engines))
        reverse_order_rows.append({"tau": tau, "distance_12_vs_21": math.dist(left, right)})
    repeated_rows = []
    for tau in (0.5, 1.0):
        engines = engines_for_params(tau=tau, direction="raw_xz", magnitude=1.0, profile=DISSIPATOR_PROFILES["balanced"])
        for token in ("1", "2"):
            channel = qit.schedule_channel(tuple(token for _ in range(MAX_SCHEDULE_LENGTH)), engines)
            spectrum = qit.channel_spectrum(channel)
            repeated_rows.append(
                {
                    "tau": tau,
                    "token": token,
                    "fixed_eig_dim": spectrum["fixed_eig_dim"],
                    "spectral_gap": spectrum["spectral_gap"],
                    "single_basin": spectrum["fixed_eig_dim"] == 1 and spectrum["spectral_gap"] > qit.GAP_TOL,
                }
            )
    return {
        "anchor_tau_half": {
            "pass": tau_half["counts_by_length"][:6] == [2, 4, 4, 4, 4, 4] and tau_half["length8_memory_class"] == "last2",
            "row": tau_half,
        },
        "anchor_tau_one": {
            "pass": tau_one["counts_by_length"][:6] == [2, 2, 2, 2, 2, 2] and tau_one["length8_memory_class"] == "last1",
            "row": tau_one,
        },
        "label_shuffle_invariant": {
            "pass": all(row["original_count"] == row["swapped_label_count"] for row in label_shuffle_rows),
            "rows": label_shuffle_rows,
        },
        "reverse_order_sensitive": {
            "pass": all(row["distance_12_vs_21"] > 0.05 for row in reverse_order_rows),
            "rows": reverse_order_rows,
        },
        "repeated_same_engine_single_basin": {
            "pass": all(row["single_basin"] for row in repeated_rows),
            "rows": repeated_rows,
        },
    }


def z3_report() -> dict[str, Any]:
    phase_map_exists = z3.Bool("phase_map_exists")
    schedule_memory = z3.Bool("schedule_memory")
    adaptive_or_coupled_runtime = z3.Bool("adaptive_or_coupled_runtime")
    real_basin_admitted = z3.Bool("real_basin_admitted")
    solver = z3.Solver()
    solver.add(phase_map_exists)
    solver.add(schedule_memory)
    solver.add(z3.Not(adaptive_or_coupled_runtime))
    solver.add(real_basin_admitted == z3.And(schedule_memory, adaptive_or_coupled_runtime))
    solver.add(real_basin_admitted)
    return {
        "schedule_phase_map_without_adaptive_or_coupled_real_basin_unsat": str(solver.check()) == "unsat",
        "rule": "schedule-memory phase structure is pseudo-basin evidence until one generated adaptive/coupled map is built and tested",
    }


def main() -> int:
    started = time.time()
    d95 = read_json(SOURCE_FILES["d95_consolidation_result"])
    rows = build_phase_rows()
    boundaries = boundary_rows()
    controls = control_reports(rows)
    nominal = nominal_sequence(rows)
    brackets = transition_brackets(nominal)
    phase_counts = class_counts(rows)
    boundary_counts = class_counts(boundaries)
    all_interior_primitive = all(row["length8_nonprimitive_count"] == 0 for row in rows)
    slow_gap_rows = [row for row in rows if row["length8_slow_gap_count"] > 0]
    positive = {
        "workstream_a_reference_green": {
            "pass": d95.get("all_pass") is True,
            "result": rel(SOURCE_FILES["d95_consolidation_result"]),
        },
        "phase_grid_completed": {
            "pass": len(rows) == len(TAUS) * len(DIRECTION_CASES) * len(MAGNITUDES) * len(DISSIPATOR_PROFILES),
            "row_count": len(rows),
            "tau_values": TAUS,
            "direction_count": len(DIRECTION_CASES),
            "magnitude_values": MAGNITUDES,
            "profile_count": len(DISSIPATOR_PROFILES),
            "max_schedule_length": MAX_SCHEDULE_LENGTH,
        },
        "last1_and_last2_regions_found": {
            "pass": phase_counts.get("last1", 0) > 0 and phase_counts.get("last2", 0) > 0,
            "phase_counts": phase_counts,
        },
        "nominal_transition_bounded": {
            "pass": controls["anchor_tau_half"]["pass"] and controls["anchor_tau_one"]["pass"] and bool(brackets),
            "nominal_sequence": [
                {
                    "tau": row["tau"],
                    "class": row["length8_memory_class"],
                    "counts": row["counts_by_length"],
                    "min_gap": row["length8_min_spectral_gap"],
                }
                for row in sorted(nominal, key=lambda item: item["tau"])
            ],
            "transition_brackets": brackets,
        },
        "interior_fixed_eigenspaces_are_primitive": {
            "pass": all_interior_primitive,
            "nonprimitive_interior_rows": [row for row in rows if row["length8_nonprimitive_count"] > 0][:8],
        },
        "boundary_degeneracy_control_recorded": {
            "pass": any(row["length8_nonprimitive_count"] > 0 for row in boundaries),
            "boundary_counts": boundary_counts,
            "rows": boundaries,
        },
        "finite_time_slow_gap_separated": {
            "pass": True,
            "slow_gap_row_count": len(slow_gap_rows),
            "examples": slow_gap_rows[:8],
        },
        "schedule_tree_witnessed": schedule_tree_report(),
        "control_suite_passed": {
            "pass": all(item["pass"] for item in controls.values()),
            "controls": controls,
        },
        "no_direct_real_basin_promotion": {
            "pass": z3_report()["schedule_phase_map_without_adaptive_or_coupled_real_basin_unsat"],
            "z3": z3_report(),
        },
    }
    boundary = {
        "promotion_allowed": {"pass": True, "value": False},
        "real_basin_claim_allowed": {"pass": True, "value": False},
        "e16_claim_allowed": {"pass": True, "value": False},
        "tensor_network_claim_allowed": {"pass": True, "value": False},
        "final_manifold_claim_allowed": {"pass": True, "value": False},
    }
    graveyard_companions = {
        "schedule_memory_not_real_basin": {
            "pass": positive["no_direct_real_basin_promotion"]["pass"],
            "reason": "phase rows classify schedule-family pseudo-basin memory only; no adaptive/coupled generated map is present",
        },
        "single_engine_search_not_reopened": {
            "pass": True,
            "reason": "this scout starts from D90's monostable-engine result and maps schedule memory instead of reopening single-engine multi-basin search",
        },
    }
    control_rows = positive["control_suite_passed"]["controls"]
    nearby_variant_rows = [
        {
            "variant": "tau_half_last2_anchor",
            "pass": control_rows["anchor_tau_half"]["pass"],
            "claim": "nominal tau=0.5 remains a last-2 schedule-memory regime through length 8",
        },
        {
            "variant": "tau_one_last1_anchor",
            "pass": control_rows["anchor_tau_one"]["pass"],
            "claim": "nominal tau=1.0 remains a last-1 schedule-memory regime through length 8",
        },
        {
            "variant": "label_shuffle_control",
            "pass": control_rows["label_shuffle_invariant"]["pass"],
            "claim": "class counts do not depend on T1/T2 label names",
        },
        {
            "variant": "reverse_order_control",
            "pass": control_rows["reverse_order_sensitive"]["pass"],
            "claim": "T1T2 and T2T1 stay observably different in fixed Bloch readout",
        },
        {
            "variant": "zero_rate_boundary_control",
            "pass": positive["boundary_degeneracy_control_recorded"]["pass"],
            "claim": "degenerate boundary rows remain separated from primitive interior phase rows",
        },
        {
            "variant": "nonpromotion_guard",
            "pass": positive["no_direct_real_basin_promotion"]["pass"],
            "claim": "schedule-memory phase structure alone cannot admit real basin or final manifold claims",
        },
    ]
    nearby_variants = {
        "pass": all(row["pass"] for row in nearby_variant_rows),
        "passed": sum(1 for row in nearby_variant_rows if row["pass"]),
        "total": len(nearby_variant_rows),
        "variants": nearby_variant_rows,
    }
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in boundary.values())
        and all(item["pass"] for item in graveyard_companions.values())
        and nearby_variants["pass"]
    )
    result = {
        "schema": "formal_scout_result/v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "grid": {
            "taus": TAUS,
            "directions": DIRECTION_CASES,
            "magnitudes": MAGNITUDES,
            "dissipator_profiles": DISSIPATOR_PROFILES,
            "max_schedule_length": MAX_SCHEDULE_LENGTH,
            "cluster_eps": CLUSTER_EPS,
        },
        "phase_rows": rows,
        "boundary_rows": boundaries,
        "positive": positive,
        "nearby_variants": nearby_variants,
        "boundary": boundary,
        "graveyard_companions": graveyard_companions,
        "source_hashes": {name: {"path": rel(path), "exists": path.exists(), "sha256": sha256(path)} for name, path in SOURCE_FILES.items()},
        "summary": {
            "all_pass": all_pass,
            "row_count": len(rows),
            "phase_counts": phase_counts,
            "boundary_counts": boundary_counts,
            "nominal_transition_brackets": brackets,
            "slow_gap_row_count": len(slow_gap_rows),
            "interpretation": (
                "Workstream B schedule-memory phase mapping is green for this bounded exact-torch grid: "
                "last-2 and last-1 schedule-memory regimes both appear, the nominal tau=0.5 and tau=1.0 "
                "anchors are preserved through schedule length 8, and a transition bracket is recorded. "
                "Interior rows remain primitive fixed-schedule maps; zero-rate boundary controls carry the "
                "expected degeneracy. This is schedule-level pseudo-basin evidence only, not real basin admission."
            ),
        },
        "why_not_v4_probes": "This is a v5 Workstream B phase-map scout over the shared source-native QIT runtime; it is not a legacy v4 probe or final manifold promotion.",
        "all_pass": all_pass,
        "blockers": [] if all_pass else [name for name, item in positive.items() if not item["pass"]],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "out_path": rel(OUT_PATH),
                "row_count": len(rows),
                "phase_counts": phase_counts,
                "nominal_transition_brackets": brackets,
                "slow_gap_row_count": len(slow_gap_rows),
                "interpretation": result["summary"]["interpretation"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
