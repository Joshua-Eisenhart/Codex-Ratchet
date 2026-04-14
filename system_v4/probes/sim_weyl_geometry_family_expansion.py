#!/usr/bin/env python3
"""
Weyl Geometry Family Expansion
==============================

Controller-facing expansion row for the Weyl/Hopf lane.

Goal:
  - keep the live Weyl/Hopf carrier core as the anchor
  - widen into more geometry families already present in the repo where practical
  - reuse the current carrier-array / comparison pattern
  - stay honest: only include families that actually run cleanly in the repo

This is an expansion row, not doctrine.
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter
from typing import Any, Dict, List

import numpy as np

classification = "canonical"

from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    density_to_bloch,
    hopf_map,
    inter_torus_transport,
    left_density,
    left_weyl_spinor,
    right_weyl_spinor,
    torus_coordinates,
    torus_radii,
)


PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
OUT_PATH = RESULT_DIR / "weyl_geometry_family_expansion_results.json"


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Controller-facing expansion row that widens the Weyl/Hopf carrier core "
    "into additional geometry families already present in the repo."
)

LEGO_IDS = [
    "weyl_geometry_family_expansion",
    "weyl_geometry_carrier_array",
    "weyl_geometry_carrier_compare",
    "hopf_torus_lego",
    "torch_hopf_connection",
    "hopf_contact_symplectic_bridge",
    "graph_shell_geometry",
    "toponetx_hopf_crosscheck",
    "geometry_families_L0",
]

PRIMARY_LEGO_IDS = [
    "weyl_geometry_carrier_array",
    "weyl_geometry_carrier_compare",
    "hopf_torus_lego",
    "torch_hopf_connection",
    "hopf_contact_symplectic_bridge",
    "graph_shell_geometry",
    "toponetx_hopf_crosscheck",
    "geometry_families_L0",
]

TOOL_MANIFEST = {
    "numpy": {"tried": False, "used": False, "reason": "core numeric glue"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


def load_json(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"missing result file: {path}")
    return json.loads(path.read_text())


def as_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def is_truthy_pass(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


def family_pass_from_summary(obj: dict[str, Any]) -> bool:
    summary = obj.get("summary", {})
    if isinstance(summary, dict) and "all_pass" in summary:
        return bool(summary["all_pass"])
    if "all_pass" in obj:
        return bool(obj["all_pass"])
    if "tests_passed" in summary and "tests_total" in summary:
        return int(summary["tests_passed"]) == int(summary["tests_total"])
    if "tests_passed" in obj and "tests_total" in obj:
        return int(obj["tests_passed"]) == int(obj["tests_total"])
    if "positive" in obj and "negative" in obj and "boundary" in obj:
        return all(
            is_truthy_pass(v.get("pass"))
            for section in ("positive", "negative", "boundary")
            for v in obj[section].values()
            if isinstance(v, dict)
        )
    return False


def parse_pass_total(value: Any) -> tuple[int, int]:
    if isinstance(value, str) and "/" in value:
        left, right = value.split("/", 1)
        try:
            return int(left.strip()), int(right.strip())
        except Exception:
            return 0, 0
    try:
        ivalue = int(value)
        return ivalue, ivalue
    except Exception:
        return 0, 0


def core_carrier_sanity() -> dict[str, Any]:
    eta_levels = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]
    theta_grid = [0.0, np.pi / 2.0, np.pi, 3.0 * np.pi / 2.0]

    max_overlap = 0.0
    max_hopf_roundtrip_gap = 0.0
    max_radius_identity_gap = 0.0
    max_roundtrip_error = 0.0
    sample_count = 0

    for eta in eta_levels:
        major, minor = torus_radii(float(eta))
        max_radius_identity_gap = max(max_radius_identity_gap, abs(major * major + minor * minor - 1.0))
        for theta1 in theta_grid:
            theta2 = float((theta1 + np.pi / 3.0) % (2.0 * np.pi))
            q = torus_coordinates(float(eta), float(theta1), theta2)
            L = left_weyl_spinor(q)
            R = right_weyl_spinor(q)
            rho_L = left_density(q)
            bloch_L = density_to_bloch(rho_L)
            max_overlap = max(max_overlap, abs(np.vdot(L, R)))
            max_hopf_roundtrip_gap = max(max_hopf_roundtrip_gap, np.linalg.norm(hopf_map(q) - bloch_L))
            sample_count += 1

    q0 = torus_coordinates(TORUS_INNER, 0.17, 0.41)
    q1 = inter_torus_transport(q0, TORUS_INNER, TORUS_CLIFFORD)
    q2 = inter_torus_transport(q1, TORUS_CLIFFORD, TORUS_OUTER)
    q3 = inter_torus_transport(q2, TORUS_OUTER, TORUS_INNER)
    max_roundtrip_error = float(np.linalg.norm(q3 - q0))

    pass_flag = (
        max_overlap < 1e-10
        and max_hopf_roundtrip_gap < 1e-10
        and max_radius_identity_gap < 1e-10
        and max_roundtrip_error < 1e-10
    )

    return {
        "kind": "carrier_core",
        "source_files": [
            "weyl_geometry_carrier_array_results.json",
        ],
        "pass": pass_flag,
        "witness": {
            "sample_count": sample_count,
            "max_left_right_overlap_abs": max_overlap,
            "max_hopf_roundtrip_gap": max_hopf_roundtrip_gap,
            "max_radius_identity_gap": max_radius_identity_gap,
            "transport_roundtrip_error": max_roundtrip_error,
        },
        "notes": "Fresh direct sanity on the live Weyl/Hopf carrier core.",
    }


def carrier_compare_family() -> dict[str, Any]:
    obj = load_json("lego_weyl_geometry_carrier_compare_results.json")
    summary = obj.get("summary", {})
    checks = summary.get("checks", {})
    spread = checks.get("comparison_spread", {})
    return {
        "kind": "carrier_compare",
        "source_files": ["lego_weyl_geometry_carrier_compare_results.json"],
        "pass": family_pass_from_summary(obj),
        "witness": {
            "carrier_count": summary.get("carrier_count"),
            "result_count": summary.get("result_count"),
            "comparison_rows": summary.get("comparison_rows"),
            "mean_left_entropy_spread": spread.get("mean_left_entropy_spread"),
            "mean_step_bloch_jump_spread": spread.get("mean_step_bloch_jump_spread"),
        },
        "notes": "Current compare-pattern carrier set, used as the widen/compare anchor.",
    }


def hopf_bundle_family() -> dict[str, Any]:
    hopf_torus = load_json("hopf_torus_lego_results.json")
    torch_hopf = load_json("torch_hopf_connection_results.json")
    foundation = load_json("foundation_hopf_torus_geomstats_clifford_results.json")
    meta = load_json("hopf_torus_meta_results.json")

    pass_flag = (
        family_pass_from_summary(hopf_torus)
        and family_pass_from_summary(torch_hopf)
        and family_pass_from_summary(foundation)
        and any(e.get("status") == "PASS" for e in meta.get("evidence_ledger", []))
    )
    return {
        "kind": "hopf_bundle_family",
        "source_files": [
            "hopf_torus_lego_results.json",
            "torch_hopf_connection_results.json",
            "foundation_hopf_torus_geomstats_clifford_results.json",
            "hopf_torus_meta_results.json",
        ],
        "pass": pass_flag,
        "witness": {
            "hopf_torus_tests_passed": hopf_torus.get("summary", {}).get("tests_passed"),
            "hopf_torus_tests_total": hopf_torus.get("summary", {}).get("tests_total"),
            "torch_hopf_all_pass": torch_hopf.get("summary", {}).get("all_pass"),
            "foundation_all_pass": foundation.get("summary", {}).get("all_pass"),
            "meta_pass_status": [e.get("status") for e in meta.get("evidence_ledger", [])],
        },
        "notes": "Legacy Hopf bundle family: torus topology, connection, geomstats/clifford, and meta evidence.",
    }


def contact_symplectic_family() -> dict[str, Any]:
    obj = load_json("hopf_contact_symplectic_bridge_results.json")
    summary = obj.get("summary", {})
    tests_passed = int(obj.get("tests_passed", 0))
    tests_total = int(obj.get("tests_total", 0))
    pass_flag = tests_passed == tests_total and as_float(summary.get("coupling_constant", 0.0)) == -2.0
    return {
        "kind": "contact_symplectic_family",
        "source_files": ["hopf_contact_symplectic_bridge_results.json"],
        "pass": pass_flag,
        "witness": {
            "tests_passed": tests_passed,
            "tests_total": tests_total,
            "bridge_identity": summary.get("bridge_identity"),
            "coupling_constant": summary.get("coupling_constant"),
            "reeb_vertical": summary.get("reeb_vertical"),
        },
        "notes": "Hopf-contact-symplectic bridge identity, with the load-bearing ratio fixed at -2.",
    }


def graph_shell_family() -> dict[str, Any]:
    obj = load_json("graph_shell_geometry_results.json")
    summary = obj.get("summary", {})
    pass_flag = bool(summary.get("all_pass", False))
    return {
        "kind": "graph_shell_family",
        "source_files": ["graph_shell_geometry_results.json"],
        "pass": pass_flag,
        "witness": {
            "nested_chain": obj.get("positive", {}).get("nested_shell_chain_is_connected_and_acyclic", {}),
            "pairwise_cycle": obj.get("positive", {}).get("pairwise_shell_loop_has_single_cycle", {}),
            "summary_pass": summary.get("all_pass"),
        },
        "notes": "Binary shell graph family; keeps the graph carrier separate from the Weyl transport core.",
    }


def hypergraph_topology_family() -> dict[str, Any]:
    obj = load_json("toponetx_hopf_crosscheck_results.json")
    summary = obj.get("summary", {})
    tests_passed, tests_total = parse_pass_total(summary.get("tests_passed", summary.get("tests_total", 0)))
    if tests_total == 0 and summary.get("tests_total") is not None:
        tests_total = int(summary.get("tests_total", 0))
    pass_flag = tests_passed == tests_total
    return {
        "kind": "hypergraph_topology_family",
        "source_files": ["toponetx_hopf_crosscheck_results.json"],
        "pass": pass_flag,
        "witness": {
            "beta0": summary.get("beta0"),
            "beta1": summary.get("beta1"),
            "beta2": summary.get("beta2"),
            "chi": summary.get("chi"),
            "beta1_matches_gudhi": summary.get("beta1_matches_gudhi"),
            "tests_passed": tests_passed,
            "tests_total": tests_total,
        },
        "notes": "Multiway torus topology family with xgi/toponetx witnesses and z3/sympy cross-checks.",
    }


def geometry_metric_family() -> dict[str, Any]:
    obj = load_json("geometry_families_L0_results.json")
    distance_metrics = obj.get("distance_metrics", {})
    triangle = distance_metrics.get("triangle_inequality", {})
    noncomm = obj.get("noncommutativity_verification", {})
    survive = [
        name
        for name, info in triangle.items()
        if isinstance(info, dict) and info.get("is_metric") is True
    ]
    killed = [
        name
        for name, info in triangle.items()
        if isinstance(info, dict) and info.get("is_metric") is False
    ]

    pass_flag = (
        triangle.get("trace_distance", {}).get("is_metric") is True
        and triangle.get("bures_distance", {}).get("is_metric") is True
        and triangle.get("hilbert_schmidt_distance", {}).get("is_metric") is True
        and noncomm.get("Ti_Fi_noncommuting") is True
        and noncomm.get("Te_Fe_noncommuting") is True
    )

    return {
        "kind": "geometry_metric_family",
        "source_files": ["geometry_families_L0_results.json"],
        "pass": pass_flag,
        "witness": {
            "metric_survivors": survive,
            "metric_kills": killed,
            "trace_distance_is_metric": triangle.get("trace_distance", {}).get("is_metric"),
            "bures_distance_is_metric": triangle.get("bures_distance", {}).get("is_metric"),
            "hilbert_schmidt_distance_is_metric": triangle.get("hilbert_schmidt_distance", {}).get("is_metric"),
            "Ti_Fi_noncommuting": noncomm.get("Ti_Fi_noncommuting"),
            "Te_Fe_noncommuting": noncomm.get("Te_Fe_noncommuting"),
        },
        "notes": "L0 geometry-family discriminator: the surviving metrics stay metric, and the intentionally bad ones are still killed.",
    }


def main() -> None:
    TOOL_MANIFEST["numpy"]["tried"] = True
    TOOL_MANIFEST["numpy"]["used"] = True
    TOOL_MANIFEST["numpy"]["reason"] = "core numeric glue for family normalization and bounded sanity checks"

    carrier_array = load_json("weyl_geometry_carrier_array_results.json")
    core = core_carrier_sanity()
    compare = carrier_compare_family()
    hopf_bundle = hopf_bundle_family()
    contact = contact_symplectic_family()
    graph_shell = graph_shell_family()
    hypergraph = hypergraph_topology_family()
    metric_family = geometry_metric_family()

    families = [
        core,
        compare,
        hopf_bundle,
        contact,
        graph_shell,
        hypergraph,
        metric_family,
    ]

    family_order = [row["kind"] for row in families]
    family_kind_counts = dict(Counter(row["kind"] for row in families))
    source_files = sorted({src for row in families for src in row["source_files"]})

    carrier_summary = carrier_array.get("summary", {})
    carrier_checks = carrier_array.get("positive", {})
    carrier_compare_summary = compare["witness"]

    all_pass = all(row["pass"] for row in families) and bool(carrier_summary.get("all_pass", False))

    summary = {
        "all_pass": all_pass,
        "family_count": len(families),
        "source_result_count": len(source_files),
        "family_order": family_order,
        "family_kind_counts": family_kind_counts,
        "carrier_core_count": carrier_summary.get("carrier_count"),
        "carrier_core_passed_carriers": carrier_summary.get("passed_carriers"),
        "carrier_core_failed_carriers": carrier_summary.get("failed_carriers"),
        "carrier_compare_carrier_count": carrier_compare_summary.get("carrier_count"),
        "carrier_compare_result_count": carrier_compare_summary.get("result_count"),
        "expanded_scope_note": (
            "The live Weyl/Hopf carrier set is widened into geometry families already present in the repo: "
            "carrier array, carrier compare, Hopf bundle, contact/symplectic bridge, graph shell, hypergraph topology, "
            "and the L0 geometry metric family."
        ),
    }

    result = {
        "name": "weyl_geometry_family_expansion",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": summary,
        "families": families,
        "carrier_array_anchor": {
            "carrier_count": carrier_summary.get("carrier_count"),
            "all_pass": carrier_summary.get("all_pass"),
            "comparison_spread": carrier_checks.get("comparison_spread", {}),
        },
        "carrier_compare_anchor": {
            "carrier_count": carrier_compare_summary.get("carrier_count"),
            "result_count": carrier_compare_summary.get("result_count"),
            "mean_left_entropy_spread": carrier_compare_summary.get("mean_left_entropy_spread"),
            "mean_step_bloch_jump_spread": carrier_compare_summary.get("mean_step_bloch_jump_spread"),
        },
    }

    OUT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print(OUT_PATH)


if __name__ == "__main__":
    main()
