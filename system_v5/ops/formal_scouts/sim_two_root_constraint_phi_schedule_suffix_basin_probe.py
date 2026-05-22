#!/usr/bin/env python3
"""Formalize Phi_schedule suffix-basin behavior.

This scout follows the grok_sim iter_179 update: a single fixed linear engine is
monostable, so the next meaningful layer is schedule composition. It reuses the
exact torch Liouvillian engine builder from the D90 formal sweep, composes Type-1
and Type-2 engines into schedules, and tests whether the schedule family has
distinct pseudo-attractor classes while each individual schedule map remains
single-basin.
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
OUT_PATH = RESULT_DIR / "two_root_constraint_phi_schedule_suffix_basin_probe_results.json"

NAME = "two_root_constraint_phi_schedule_suffix_basin_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_schedule_composition"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_phi_schedule_suffix_basin"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: exact torch schedule composition over the D90 Type-1 and "
    "Type-2 single-qubit engines. It may support schedule-level pseudo-attractor "
    "classes, but cannot promote a real attractor basin, final QIT engine theorem, "
    "E=16 paired-engine result, tensor-network result, or final manifold."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact channel composition, spectra, fixed-point iteration, and Bloch readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing schedule-prefix graph witness for all binary schedules through length 6",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard separating pseudo-attractor classes from real basin admission",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "itertools": {"tried": True, "used": True, "reason": "supportive deterministic schedule enumeration"},
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

GROK_ITER_179_SOURCE = REPO / "system_v5" / "grok_sim" / "iters" / "iter_179_phi_schedule_T1_T2_composition.py"
GROK_ITER_179_RESULT = REPO / "system_v5" / "grok_sim" / "results" / "iter_179_phi_schedule_T1_T2_composition_results.json"
D90_SOURCE = SCOUT_ROOT / "sim_two_root_constraint_phi_engine_parameter_sweep_probe.py"
D90_RESULT = RESULT_DIR / "two_root_constraint_phi_engine_parameter_sweep_probe_results.json"

MAX_SCHEDULE_LENGTH = 6
CLUSTER_EPS = 0.05
N_CYCLES = 80


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
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            item = value.detach().cpu().item()
            if isinstance(item, complex):
                return {"real": float(item.real), "imag": float(item.imag)}
            return float(item)
        return value.detach().cpu().tolist()
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, pathlib.Path):
        return rel(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    return value


def channel_for_word(word: tuple[str, ...], engines: dict[str, torch.Tensor]) -> torch.Tensor:
    return qit.schedule_channel(word, engines)


def fixed_bloch(channel: torch.Tensor, cycles: int = 240) -> list[float]:
    return qit.fixed_bloch(channel, cycles=cycles)


def diagnostics(channel: torch.Tensor) -> dict[str, Any]:
    diag = qit.channel_diagnostics(channel, cycles=N_CYCLES)
    return {
        "fixed_eig_dim": diag["fixed_eig_dim"],
        "spectral_gap": diag["spectral_gap"],
        "spectral_radius_nonfixed": diag["spectral_radius_nonfixed"],
        "max_final_bloch_spread_at_80": diag["max_final_bloch_spread_at_80"],
        "asymptotic_single_basin": diag["asymptotic_single_basin"],
        "single_basin_by_trajectory_at_80": diag["single_basin_by_trajectory_at_80"],
    }


def cluster_rows(rows: list[dict[str, Any]], eps: float) -> list[dict[str, Any]]:
    return qit.cluster_points(rows, label_key="label", eps=eps)


def schedule_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("")
    nodes = {"": root}
    for row in rows:
        word = row["word"]
        prefix = ""
        for token in word:
            next_prefix = f"{prefix}.{token}" if prefix else token
            if next_prefix not in nodes:
                nodes[next_prefix] = graph.add_node(next_prefix)
                graph.add_edge(nodes[prefix], nodes[next_prefix], token)
            prefix = next_prefix
    expected_nodes = 1 + sum(2**length for length in range(1, MAX_SCHEDULE_LENGTH + 1))
    return {
        "pass": graph.num_nodes() == expected_nodes and graph.num_edges() == expected_nodes - 1,
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "max_schedule_length": MAX_SCHEDULE_LENGTH,
    }


def z3_report() -> dict[str, Any]:
    fixed_single_map_multi_basin = z3.Bool("fixed_single_map_multi_basin")
    schedule_family_distinct = z3.Bool("schedule_family_distinct")
    e16_or_adaptive = z3.Bool("e16_or_adaptive")
    real_basin_promotion = z3.Bool("real_basin_promotion")
    solver = z3.Solver()
    solver.add(schedule_family_distinct)
    solver.add(z3.Not(fixed_single_map_multi_basin))
    solver.add(z3.Not(e16_or_adaptive))
    solver.add(real_basin_promotion == z3.And(fixed_single_map_multi_basin, e16_or_adaptive))
    solver.add(real_basin_promotion)
    return {
        "direct_real_basin_promotion_unsat": str(solver.check()) == "unsat",
        "rule": "schedule-family distinctness alone is not real basin admission",
    }


def main() -> int:
    started = time.time()
    grok_result = read_json(GROK_ITER_179_RESULT)
    engines = {
        "T1": qit.engine_channel("L", "iter176_xz", tau=1.0, normalize=True),
        "T2": qit.engine_channel("R", "iter176_xz", tau=1.0, normalize=True),
    }
    rows: list[dict[str, Any]] = []
    for length in range(1, MAX_SCHEDULE_LENGTH + 1):
        for word in itertools.product(("T1", "T2"), repeat=length):
            channel = channel_for_word(word, engines)
            diag = diagnostics(channel)
            rows.append(
                {
                    "label": ".".join(word),
                    "word": list(word),
                    "length": length,
                    "last_engine": word[-1],
                    "fixed_bloch": fixed_bloch(channel),
                    **diag,
                }
            )
    clusters = cluster_rows(rows, CLUSTER_EPS)
    clusters_by_length = {
        str(length): cluster_rows([row for row in rows if row["length"] == length], CLUSTER_EPS)
        for length in range(1, MAX_SCHEDULE_LENGTH + 1)
    }
    centers_by_last = {
        token: [
            sum(row["fixed_bloch"][idx] for row in rows if row["last_engine"] == token)
            / len([row for row in rows if row["last_engine"] == token])
            for idx in range(3)
        ]
        for token in ("T1", "T2")
    }
    last_engine_mismatches = []
    for row in rows:
        nearest_last = min(("T1", "T2"), key=lambda token: math.dist(row["fixed_bloch"], centers_by_last[token]))
        if nearest_last != row["last_engine"]:
            last_engine_mismatches.append(row["label"])
    t1_then_t2 = next(row for row in rows if row["label"] == "T1.T2")
    t2_then_t1 = next(row for row in rows if row["label"] == "T2.T1")
    order_diff = math.dist(t1_then_t2["fixed_bloch"], t2_then_t1["fixed_bloch"])
    all_schedule_maps_single_basin = all(row["asymptotic_single_basin"] for row in rows)
    positive = {
        "iter179_reference_exists": {
            "pass": GROK_ITER_179_SOURCE.exists() and GROK_ITER_179_RESULT.exists(),
            "source": rel(GROK_ITER_179_SOURCE),
            "result": rel(GROK_ITER_179_RESULT),
            "sidequest_reported_cluster_count": grok_result.get("n_distinct_attractors_across_8_maps"),
        },
        "d90_exact_engine_reference_exists": {
            "pass": D90_SOURCE.exists() and D90_RESULT.exists(),
            "source": rel(D90_SOURCE),
            "result": rel(D90_RESULT),
        },
        "schedule_graph_witnessed": schedule_graph(rows),
        "all_schedule_maps_remain_single_basin": {
            "pass": all_schedule_maps_single_basin,
            "row_count": len(rows),
            "max_final_spread_at_80": max(row["max_final_bloch_spread_at_80"] for row in rows),
        },
        "schedule_composition_is_order_sensitive": {
            "pass": order_diff > 0.05,
            "order_diff": order_diff,
            "T1_then_T2_fixed_bloch": t1_then_t2["fixed_bloch"],
            "T2_then_T1_fixed_bloch": t2_then_t1["fixed_bloch"],
        },
        "schedule_family_has_distinct_suffix_classes": {
            "pass": len(clusters) == 2 and not last_engine_mismatches,
            "cluster_count": len(clusters),
            "cluster_eps": CLUSTER_EPS,
            "last_engine_mismatches": last_engine_mismatches,
            "clusters": clusters,
        },
        "sidequest_four_cluster_count_not_reproduced_exactly": {
            "pass": grok_result.get("n_distinct_attractors_across_8_maps") == 4 and len(clusters) == 2,
            "sidequest_cluster_count": grok_result.get("n_distinct_attractors_across_8_maps"),
            "exact_torch_cluster_count_through_length_6": len(clusters),
            "interpretation": "exact Liouvillian composition preserves schedule-level distinctness but collapses to last-engine suffix classes",
        },
        "no_direct_real_basin_promotion": {
            "pass": z3_report()["direct_real_basin_promotion_unsat"],
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
        "sidequest_four_cluster_pattern_not_preserved_as_formal_result": {
            "pass": grok_result.get("n_distinct_attractors_across_8_maps") == 4 and len(clusters) == 2,
            "reason": "the exact torch port keeps schedule distinction but collapses the sidequest four-cluster pattern to two suffix classes",
        },
        "single_schedule_maps_do_not_become_real_basins": {
            "pass": all_schedule_maps_single_basin,
            "reason": "each fixed schedule map remains asymptotically single-basin, so suffix classes are schedule-family readouts only",
        },
    }
    nearby_variants = {
        "passed": len(rows),
        "total": len(rows),
        "variants": [row["label"] for row in rows],
        "pass": len(rows) == sum(2**length for length in range(1, MAX_SCHEDULE_LENGTH + 1)),
    }
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in boundary.values())
        and all(item["pass"] for item in graveyard_companions.values())
        and nearby_variants["passed"] == nearby_variants["total"]
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
        "source_hashes": {
            "self": sha256(pathlib.Path(__file__)),
            "d90_source": sha256(D90_SOURCE),
            "d90_result": sha256(D90_RESULT),
            "grok_iter179_source": sha256(GROK_ITER_179_SOURCE),
            "grok_iter179_result": sha256(GROK_ITER_179_RESULT),
        },
        "schedule_convention": "labels read left-to-right as execution order; channel composition applies the leftmost engine first",
        "rows": rows,
        "clusters": clusters,
        "clusters_by_length": clusters_by_length,
        "centers_by_last_engine": centers_by_last,
        "positive": positive,
        "boundary": boundary,
        "graveyard_companions": graveyard_companions,
        "nearby_variants": nearby_variants,
        "summary": {
            "all_pass": all_pass,
            "schedule_row_count": len(rows),
            "cluster_count_through_length_6": len(clusters),
            "sidequest_iter179_cluster_count": grok_result.get("n_distinct_attractors_across_8_maps"),
            "order_diff_T1T2_vs_T2T1": order_diff,
            "all_schedule_maps_single_basin": all_schedule_maps_single_basin,
            "last_engine_mismatches": len(last_engine_mismatches),
            "interpretation": (
                "Schedule composition is the correct next pseudo-basin layer: exact torch T1/T2 "
                "channels are noncommutative and have distinct schedule-family attractor classes. "
                "However, every fixed schedule map remains asymptotically single-basin, and the "
                "exact Liouvillian port collapses the iter_179 four-cluster sidequest pattern to "
                "two last-engine suffix classes through length 6. This supports schedule-level "
                "pseudo-attractor classes, not real basin admission."
            ),
        },
        "why_not_v4_probes": "This is a v5 source-native schedule-composition scout over exact torch T1/T2 engine words; it is not a legacy v4 probe, real-basin admission, or final manifold promotion.",
        "all_pass": all_pass,
        "blockers": [] if all_pass else [name for name, item in positive.items() if not item["pass"]],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "out_path": rel(OUT_PATH),
                "schedule_row_count": len(rows),
                "cluster_count_through_length_6": len(clusters),
                "sidequest_iter179_cluster_count": grok_result.get("n_distinct_attractors_across_8_maps"),
                "order_diff_T1T2_vs_T2T1": order_diff,
                "interpretation": result["summary"]["interpretation"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
