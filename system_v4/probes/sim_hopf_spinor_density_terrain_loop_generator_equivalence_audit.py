#!/usr/bin/env python3
"""Audit whether terrain-loop labels change the Hopf placement generator.

The time-series collision audit left 8 unresolved pairs: same topology and
same evolution loop, but different terrain-loop tag. This receipt checks the
source mechanism directly: does the terrain generator matrix depend on the
terrain-loop coordinate, or only on terrain topology?
"""

from __future__ import annotations

import json
import pathlib
import sys
import time
from collections import defaultdict
from typing import Any

import numpy as np


NAME = "hopf_spinor_density_terrain_loop_generator_equivalence_audit"
CLASSIFICATION = "audit"
classification = CLASSIFICATION

PROBE_DIR = pathlib.Path(__file__).resolve().parent
ROOT = PROBE_DIR.parents[1]
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
TIME_SERIES_RESULT = RESULT_DIR / "hopf_spinor_density_time_series_collision_separation_audit_results.json"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

sys.path.insert(0, str(PROBE_DIR))
import sim_hopf_spinor_density_inner_outer_operator_placement_baseline as baseline  # noqa: E402


TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing for generator matrix equality and norm checks",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "supportive through imported baseline rotor construction",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "clifford": "supportive",
}

CLAIM_CEILING = (
    "source-mechanism audit only: current Hopf spinor-density placement baseline generator matrices "
    "depend on terrain topology but not terrain-loop tag; no 16-placement closure, QIT, GStack, axis, "
    "bridge, engine, flux, Weyl-sheet, bundle, or nonclassical admission"
)


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def terrain_rows() -> list[dict[str, Any]]:
    return [
        {
            "name": terrain["name"],
            "idx": idx,
            "topo": terrain["topo"],
            "loop": terrain["loop"],
        }
        for idx, terrain in enumerate(baseline.TERRAINS)
    ]


def matrix_for(name: str, rotors: dict[str, Any]) -> np.ndarray:
    return np.round(baseline.terrain_generator_matrix(name, rotors), 12)


def main() -> dict[str, Any]:
    started = time.time()
    rows = terrain_rows()
    rotors = baseline._build_cl3_terrain_rotors()
    by_topo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        row["matrix"] = matrix_for(row["name"], rotors)
        by_topo[row["topo"]].append(row)

    topology_pairs = []
    for topo, group in sorted(by_topo.items()):
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                left, right = group[i], group[j]
                distance = float(np.linalg.norm(left["matrix"] - right["matrix"]))
                topology_pairs.append(
                    {
                        "topology": topo,
                        "terrain_i": left["name"],
                        "terrain_j": right["name"],
                        "terrain_loop_i": left["loop"],
                        "terrain_loop_j": right["loop"],
                        "matrix_distance": round(distance, 12),
                        "matrices_equal": distance <= 1e-12,
                    }
                )

    unresolved = json.loads(TIME_SERIES_RESULT.read_text(encoding="utf-8"))["negative"][
        "unresolved_time_series_pairs_block_promotion"
    ]["pairs"]
    all_topology_pairs_equal = all(pair["matrices_equal"] for pair in topology_pairs)
    unresolved_match_generator_equivalence = all(
        row["same_terrain_topo"] and row["same_evolution_loop"] and not row["same_terrain_loop"]
        for row in unresolved
    )
    all_pass = (
        len(topology_pairs) == 4
        and all_topology_pairs_equal
        and len(unresolved) == 8
        and unresolved_match_generator_equivalence
    )

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "all_pass_meaning": (
            "contract pass means the current source mechanism explains unresolved pairs as generator-equivalent; "
            "it does not mean placement distinguishability is closed"
        ),
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": "none; blocker/diagnostic for placement distinguishability authorship",
        "promotion_condition": (
            "No promotion from this audit. A future candidate must either add a terrain-loop-dependent generator "
            "with graveyards or explicitly lower the placement quotient claim."
        ),
        "blocked_until": (
            "blocked from 16-placement closure until terrain-loop-equivalent generator pairs are separated by "
            "a source-level mechanism or admitted as quotient-equivalent"
        ),
        "demotion_condition": "Demote if cited as evidence that the terrain-loop coordinate is physically distinguished.",
        "source_receipt": rel(TIME_SERIES_RESULT),
        "operation_sequence": [
            "load terrain definitions from the Hopf spinor-density baseline source",
            "construct current terrain generator matrices",
            "group terrains by topology",
            "compare f-tag and b-tag generator matrices within each topology",
            "cross-check against unresolved time-series collision pairs",
        ],
        "carrier_topology": "current finite Hopf spinor-density terrain generator table",
        "observable": "Frobenius distance between terrain generator matrices grouped by topology",
        "pass_fail_predicate": (
            "pass iff each topology's f-tag and b-tag generators are matrix-identical and the 8 unresolved "
            "time-series collision pairs match that generator-equivalence pattern"
        ),
        "graveyards": [
            "terrain-loop-dependent generator would yield nonzero f/b matrix distance",
            "unresolved pairs not matching same-topology same-evolution-loop pattern would reject this explanation",
            "future source with f/b-dependent generator must invalidate this blocker",
        ],
        "baselines": [
            "current Hopf spinor-density placement baseline source",
            "time-series collision separation audit",
        ],
        "alternative_formulations": [
            "AST dependency audit of terrain_generator_matrix against terrain loop field",
            "operator-action comparison on a fixed spinor basis",
            "source rewrite candidate with explicit terrain-loop-dependent generator graveyards",
        ],
        "exact_tool_function_needs": {
            "numpy": ["numpy.linalg.norm", "numpy.round"],
            "baseline_module": ["terrain_generator_matrix", "_build_cl3_terrain_rotors", "TERRAINS"],
        },
        "lego_or_coupling_target": "placement distinguishability blocker for terrain-loop coordinate",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "topology_pair_count": len(topology_pairs),
            "all_topology_pairs_equal": all_topology_pairs_equal,
            "unresolved_pair_count": len(unresolved),
            "unresolved_match_generator_equivalence": unresolved_match_generator_equivalence,
            "promotion_allowed": False,
            "all_pass": all_pass,
        },
        "positive": {
            "generator_equivalence_explains_unresolved_pairs": {
                "passed": all_topology_pairs_equal and unresolved_match_generator_equivalence,
                "topology_pairs": topology_pairs,
            }
        },
        "negative": {
            "terrain_loop_not_distinguished_by_current_generator": {
                "passed": all_topology_pairs_equal,
                "interpretation": "current source cannot support 16 distinct terrain-loop generator placements",
            }
        },
        "boundary": {
            "quotient_pressure": {
                "passed": len(unresolved) == 8,
                "unresolved_pairs": unresolved,
            }
        },
        "out_of_scope": [
            "No claim that f-tag and b-tag terrain loops must remain equivalent in future source.",
            "No 16-placement operational closure.",
            "No QIT, GStack, axis, bridge, engine, flux, bundle, Weyl-sheet, or nonclassical admission.",
        ],
        "elapsed_seconds": round(time.time() - started, 6),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(OUT_PATH)
    print(f"ALL PASS: {all_pass}")
    return result


if __name__ == "__main__":
    main()
