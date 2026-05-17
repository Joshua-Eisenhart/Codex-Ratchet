#!/usr/bin/env python3
"""Audit the weak GStack lego manifest for naming and coverage drift."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "system_v5" / "evidence" / "qit_gstack_exploratory_wave_manifest_20260513.json"
FORBIDDEN_RE = re.compile(r"axis|engine|qit|bridge|type|carnot|szilard|landauer|entropy|thermo", re.I)
LAYER_HINTS = {
    "finite_carrier": (
        "finite_carrier",
        "simplex",
        "probability",
        "polytope",
        "partition",
        "quotient",
        "integer_interval",
        "interval_refinement",
        "sum_bound",
        "satisfiable",
        "permutation_matrix",
        "polynomial_root",
        "geometric_constraint_manifold",
    ),
    "density_state": (
        "density_state",
        "density",
        "trace",
        "projector",
        "kraus",
        "choi",
        "depolarizing",
        "dephasing",
        "damping",
        "channel",
        "offdiagonal",
        "statevector",
        "unitary",
        "matrix_exponential",
        "stochastic",
    ),
    "spinor_s3": ("spinor_s3", "spinor", "s3", "su2", "weyl"),
    "hopf_projection": (
        "hopf_projection",
        "hopf_coordinate",
        "hopf_map",
        "fiber_phase",
        "base_coordinate",
        "sphere",
        "hypersphere",
        "geodesic",
        "horizontal_lift",
        "hopf_horizontal",
        "symbolic_hopf",
    ),
    "nested_torus": ("nested_torus", "torus", "winding"),
    "connection_loop": ("connection_loop", "connection", "curvature", "holonomy", "phase"),
    "fiber_base_loop": ("fiber_base_loop", "fiber_base", "loop", "endpoint"),
    "clifford_pauli": ("clifford_pauli", "clifford", "pauli", "bivector", "pseudoscalar", "rotor"),
    "topology": (
        "gudhi",
        "toponetx",
        "xgi",
        "rustworkx",
        "graph",
        "cell",
        "simplex_tree",
        "hypergraph",
        "directed_path",
        "reachability",
        "triangle",
        "wedge",
        "incidence",
        "boundary",
        "edge_index",
        "message",
        "path_count",
        "laplacian",
        "component",
        "path_nodes",
        "undirected_edge",
    ),
    "composition_order": (
        "composition_order",
        "order",
        "commutator",
        "noncommut",
        "composition",
        "lie_bracket",
        "jacobi",
        "matrix_product",
    ),
    "calibration": (
        "calibration",
        "rate",
        "hot_cold",
        "two_bath",
        "measurement_feedback",
        "reset",
        "work_heat",
        "information_work",
        "temperature",
        "population",
        "same_bath",
        "swapped_bath",
        "gibbs",
        "record",
        "stationary",
        "generator_exponential",
        "unit_circle",
    ),
}


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    names = [e.get("name", "") for e in entries]
    forbidden = [n for n in names if FORBIDDEN_RE.search(n)]
    nonweak = [
        e for e in entries
        if e.get("classification") != "tool_lego_fit_probe" or e.get("promotion_allowed") is not False
    ]
    layer_counts = {}
    for layer, hints in LAYER_HINTS.items():
        layer_counts[layer] = sum(1 for name in names if any(h in name for h in hints))
    tool_counts = {}
    for e in entries:
        for tool in e.get("load_bearing") or []:
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
    thinnest_layers = sorted(layer_counts.items(), key=lambda item: (item[1], item[0]))[:5]
    thinnest_tools = sorted(tool_counts.items(), key=lambda item: (item[1], item[0]))[:5]
    report = {
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "entry_count_field": manifest.get("entry_count"),
        "entry_count_actual": len(entries),
        "entry_count_matches": manifest.get("entry_count") == len(entries),
        "forbidden_name_hits": forbidden,
        "nonweak_or_promoted_count": len(nonweak),
        "layer_hint_counts": layer_counts,
        "thinnest_layer_hints": [{"layer": layer, "count": count} for layer, count in thinnest_layers],
        "load_bearing_tool_counts": dict(sorted(tool_counts.items())),
        "thinnest_load_bearing_tools": [{"tool": tool, "count": count} for tool, count in thinnest_tools],
        "next_supply_bias": [
            f"{layer}:{count}" for layer, count in thinnest_layers
        ],
        "all_pass": manifest.get("entry_count") == len(entries) and not forbidden and not nonweak,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
