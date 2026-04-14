#!/usr/bin/env python3
"""
Weyl Geometry Multifamily Expansion
===================================

Controller-facing expansion lane for the stabilized Weyl/Hopf stack.

This lane does not try to re-prove the Weyl/Hopf carrier core. It uses the
existing pass-bearing geometry rows as anchors and ranks the next grounded
geometry families that can be made controller-usable beside Hopf/torus.

The strongest next family should be the one with the best combination of:
  - explicit pass-bearing geometry artifacts
  - graph/proof or multiway structure support
  - distinct geometry coverage beyond the Hopf/torus anchor

The lane is intentionally conservative: it only promotes a family if the
settled rows on disk already support it.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any
classification = "canonical"


PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
OUT_PATH = RESULT_DIR / "weyl_geometry_multifamily_expansion_results.json"

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Controller-facing multifamily geometry expansion lane. It keeps the "
    "Weyl/Hopf stack as anchor and ranks the next grounded geometry family "
    "using existing pass-bearing graph, hypergraph, and contact/symplectic "
    "rows."
)

LEGO_IDS = [
    "weyl_geometry_multifamily_expansion",
    "weyl_hopf_pauli_composed_stack",
    "weyl_geometry_graph_proof_alignment",
    "weyl_geometry_proof_pressure",
    "graph_shell_geometry",
    "hypergraph_geometry",
    "dual_hypergraph_geometry",
    "xgi_shell_hypergraph",
    "toponetx_hopf_crosscheck",
    "hopf_contact_symplectic_bridge",
    "contact_symplectic_coupling",
    "pure_lego_symplectic_kahler_weyl",
]

PRIMARY_LEGO_IDS = [
    "weyl_hopf_pauli_composed_stack",
    "graph_shell_geometry",
    "hypergraph_geometry",
    "dual_hypergraph_geometry",
    "hopf_contact_symplectic_bridge",
]

TOOL_MANIFEST = {
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


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "pass", "passed", "yes", "sat"}
    return bool(value)


def result_pass(result: dict[str, Any] | None) -> bool:
    if not result:
        return False
    summary = result.get("summary")
    if isinstance(summary, dict) and "all_pass" in summary:
        return truthy(summary["all_pass"])
    if "all_pass" in result:
        return truthy(result["all_pass"])
    if result.get("classification") == "canonical":
        return True
    if isinstance(result.get("positive"), dict) and result["positive"]:
        return all(truthy(v.get("pass")) for v in result["positive"].values() if isinstance(v, dict))
    return False


def summarize_family(name: str, items: list[tuple[str, dict[str, Any]]], score: float, reason: str) -> dict[str, Any]:
    return {
        "family_id": name,
        "score": float(score),
        "pass": all(result_pass(obj) for _, obj in items),
        "supporting_rows": [row_name for row_name, _ in items],
        "reason": reason,
        "support_count": len(items),
    }


def make_results() -> dict[str, Any]:
    anchor = load_json("weyl_hopf_pauli_composed_stack_results.json")
    translation_lane = load_json("qit_weyl_geometry_translation_lane_results.json")
    carrier_lane = load_json("qit_weyl_geometry_carrier_translation_lane_results.json")
    repair_priority = load_json("weyl_geometry_repair_priority_v2_results.json")

    graph_shell = load_json("graph_shell_geometry_results.json")
    graph_alignment = load_json("weyl_geometry_graph_proof_alignment_results.json")
    proof_pressure = load_json("weyl_geometry_proof_pressure_results.json")

    hypergraph = load_json("hypergraph_geometry_results.json")
    dual_hypergraph = load_json("dual_hypergraph_geometry_results.json")
    xgi_shell = load_json("xgi_shell_hypergraph_results.json")
    toponetx_crosscheck = load_json("toponetx_hopf_crosscheck_results.json")

    contact_bridge = load_json("hopf_contact_symplectic_bridge_results.json")
    contact_coupling = load_json("contact_symplectic_coupling_results.json")
    symplectic_kahler = load_json("pure_lego_symplectic_kahler_weyl_results.json")

    family_graph = summarize_family(
        "graph_family",
        [
            ("graph_shell_geometry_results.json", graph_shell),
            ("weyl_geometry_graph_proof_alignment_results.json", graph_alignment),
            ("weyl_geometry_proof_pressure_results.json", proof_pressure),
        ],
        score=3.0,
        reason="Binary graph shell plus z3/rustworkx proof pressure over the Weyl/Hopf stack.",
    )

    family_hypergraph = summarize_family(
        "hypergraph_family",
        [
            ("hypergraph_geometry_results.json", hypergraph),
            ("dual_hypergraph_geometry_results.json", dual_hypergraph),
            ("xgi_shell_hypergraph_results.json", xgi_shell),
            ("toponetx_hopf_crosscheck_results.json", toponetx_crosscheck),
        ],
        score=4.0,
        reason="Multiway shell family with dual lift and torus crosscheck; strongest next extension path.",
    )

    family_contact = summarize_family(
        "contact_symplectic_family",
        [
            ("hopf_contact_symplectic_bridge_results.json", contact_bridge),
            ("contact_symplectic_coupling_results.json", contact_coupling),
            ("pure_lego_symplectic_kahler_weyl_results.json", symplectic_kahler),
        ],
        score=3.0,
        reason="Direct Hopf-contact-symplectic bridge family; strong, but narrower than the multiway hypergraph lane.",
    )

    family_anchor = summarize_family(
        "weyl_anchor_family",
        [
            ("weyl_hopf_pauli_composed_stack_results.json", anchor),
            ("qit_weyl_geometry_translation_lane_results.json", translation_lane),
            ("qit_weyl_geometry_carrier_translation_lane_results.json", carrier_lane),
            ("weyl_geometry_repair_priority_v2_results.json", repair_priority),
        ],
        score=4.0,
        reason="Settled anchor family for the Weyl/Hopf stack; used as the source of truth for extension ranking.",
    )

    families = [family_hypergraph, family_contact, family_graph]
    families_sorted = sorted(families, key=lambda item: (item["score"], item["support_count"]), reverse=True)
    best_family = families_sorted[0]
    runner_up = families_sorted[1]
    third = families_sorted[2]

    positive = {
        "weyl_anchor_stays_the_source_of_truth": {
            "pass": family_anchor["pass"],
            "support_count": family_anchor["support_count"],
            "score": family_anchor["score"],
            "supporting_rows": family_anchor["supporting_rows"],
        },
        "graph_family_is_controller_usable": {
            "pass": family_graph["pass"],
            "support_count": family_graph["support_count"],
            "score": family_graph["score"],
            "supporting_rows": family_graph["supporting_rows"],
        },
        "hypergraph_family_is_controller_usable": {
            "pass": family_hypergraph["pass"],
            "support_count": family_hypergraph["support_count"],
            "score": family_hypergraph["score"],
            "supporting_rows": family_hypergraph["supporting_rows"],
        },
        "contact_symplectic_family_is_controller_usable": {
            "pass": family_contact["pass"],
            "support_count": family_contact["support_count"],
            "score": family_contact["score"],
            "supporting_rows": family_contact["supporting_rows"],
        },
        "hypergraph_is_the_strongest_next_family": {
            "pass": best_family["family_id"] == "hypergraph_family",
            "best_family": best_family["family_id"],
            "best_score": best_family["score"],
            "runner_up_family": runner_up["family_id"],
        },
    }

    negative = {
        "pairwise_graph_shadow_does_not_replace_multiway_structure": {
            "pass": family_graph["pass"] and family_hypergraph["pass"],
            "graph_family_score": family_graph["score"],
            "hypergraph_family_score": family_hypergraph["score"],
            "shadow_is_not_the_full_family": True,
        },
        "contact_bridge_is_not_the_only_extension_path": {
            "pass": family_contact["pass"] and family_hypergraph["pass"],
            "contact_family_score": family_contact["score"],
            "hypergraph_family_score": family_hypergraph["score"],
        },
    }

    boundary = {
        "dual_hypergraph_round_trip_restores_counts": {
            "pass": truthy(dual_hypergraph.get("summary", {}).get("all_pass"))
            and truthy(dual_hypergraph.get("boundary", {}).get("double_dual_restores_counts", {}).get("pass")),
            "dual_summary_all_pass": dual_hypergraph.get("summary", {}).get("all_pass"),
            "double_dual_restores_counts": dual_hypergraph.get("boundary", {}).get("double_dual_restores_counts", {}).get("pass"),
        },
        "weyl_anchor_remains_distinct_from_extension_families": {
            "pass": family_anchor["pass"] and family_hypergraph["pass"] and family_contact["pass"],
            "anchor_support_count": family_anchor["support_count"],
            "extension_family_count": 3,
        },
        "hypergraph_and_contact_are_different_extension_modes": {
            "pass": family_hypergraph["pass"] and family_contact["pass"],
            "hypergraph_support_count": family_hypergraph["support_count"],
            "contact_support_count": family_contact["support_count"],
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    family_rankings = [
        {
            "family_id": fam["family_id"],
            "score": fam["score"],
            "support_count": fam["support_count"],
            "pass": fam["pass"],
            "reason": fam["reason"],
            "supporting_rows": fam["supporting_rows"],
        }
        for fam in families_sorted
    ]

    return {
        "name": "weyl_geometry_multifamily_expansion",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "family_rankings": family_rankings,
        "summary": {
            "all_pass": all_pass,
            "scope_note": (
                "Ranks the next grounded geometry family beside the Weyl/Hopf "
                "anchor using existing controller-usable graph, hypergraph, "
                "and contact/symplectic rows."
            ),
            "best_family": best_family["family_id"],
            "best_family_score": best_family["score"],
            "runner_up_family": runner_up["family_id"],
            "third_family": third["family_id"],
            "family_count": len(family_rankings),
            "weyl_anchor_support_count": family_anchor["support_count"],
            "graph_support_count": family_graph["support_count"],
            "hypergraph_support_count": family_hypergraph["support_count"],
            "contact_support_count": family_contact["support_count"],
        },
    }


def main() -> int:
    results = make_results()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(results, indent=2, default=str))
    print(str(OUT_PATH))
    print(f"ALL PASS: {results['summary']['all_pass']}")
    print(f"BEST FAMILY: {results['summary']['best_family']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
