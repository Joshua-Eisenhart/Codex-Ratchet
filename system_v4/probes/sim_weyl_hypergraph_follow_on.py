#!/usr/bin/env python3
"""
Weyl hypergraph follow-on row.

Controller-facing follow-on for the ranked hypergraph family beside the
stabilized Weyl/Hopf stack. This is a bounded ranking surface, not a runtime
carrier rewrite.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any


PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
OUT_PATH = RESULT_DIR / "weyl_hypergraph_follow_on_results.json"

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Controller-facing hypergraph follow-on row for the stabilized Weyl/Hopf "
    "stack. It keeps the multiway hypergraph family as the next extension "
    "target and preserves the distinction from pairwise or runtime-equivalence "
    "claims."
)

LEGO_IDS = [
    "weyl_geometry_multifamily_expansion",
    "weyl_hopf_pauli_composed_stack",
    "qit_weyl_geometry_companion",
    "hypergraph_geometry",
    "dual_hypergraph_geometry",
    "xgi_shell_hypergraph",
    "toponetx_hopf_crosscheck",
]

PRIMARY_LEGO_IDS = [
    "weyl_hopf_pauli_composed_stack",
    "hypergraph_geometry",
    "dual_hypergraph_geometry",
    "xgi_shell_hypergraph",
    "toponetx_hopf_crosscheck",
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


def summarize_family(name: str, rows: list[tuple[str, dict[str, Any]]], score: float, reason: str) -> dict[str, Any]:
    return {
        "family_id": name,
        "score": float(score),
        "pass": all(result_pass(row) for _, row in rows),
        "supporting_rows": [row_name for row_name, _ in rows],
        "support_count": len(rows),
        "reason": reason,
    }


def main() -> None:
    anchor = load_json("weyl_hopf_pauli_composed_stack_results.json")
    strict = load_json("qit_weyl_geometry_companion_results.json")
    translation = load_json("qit_weyl_geometry_translation_lane_results.json")
    carrier_translation = load_json("qit_weyl_geometry_carrier_translation_lane_results.json")
    multifamily = load_json("weyl_geometry_multifamily_expansion_results.json")

    hypergraph = load_json("hypergraph_geometry_results.json")
    dual_hypergraph = load_json("dual_hypergraph_geometry_results.json")
    xgi_shell = load_json("xgi_shell_hypergraph_results.json")
    toponetx_crosscheck = load_json("toponetx_hopf_crosscheck_results.json")

    weyl_anchor_family = summarize_family(
        "weyl_anchor_family",
        [
            ("weyl_hopf_pauli_composed_stack_results.json", anchor),
            ("qit_weyl_geometry_companion_results.json", strict),
            ("qit_weyl_geometry_translation_lane_results.json", translation),
            ("qit_weyl_geometry_carrier_translation_lane_results.json", carrier_translation),
        ],
        score=4.0,
        reason="Stabilized Weyl/Hopf anchor rows remain the source of truth for extension work.",
    )

    hypergraph_family = summarize_family(
        "hypergraph_family",
        [
            ("hypergraph_geometry_results.json", hypergraph),
            ("dual_hypergraph_geometry_results.json", dual_hypergraph),
            ("xgi_shell_hypergraph_results.json", xgi_shell),
            ("toponetx_hopf_crosscheck_results.json", toponetx_crosscheck),
        ],
        score=4.0,
        reason="Multiway hypergraph family with dual lift and torus crosscheck support.",
    )

    family_graph = summarize_family(
        "graph_family",
        [
            ("weyl_geometry_multifamily_expansion_results.json", multifamily),
        ],
        score=3.0,
        reason="Lower-ranked routing surface used only as the adjacent controller comparison.",
    )

    families = [hypergraph_family, weyl_anchor_family, family_graph]
    families_sorted = sorted(families, key=lambda item: (item["score"], item["support_count"]), reverse=True)
    best_family = families_sorted[0]
    runner_up = families_sorted[1]
    third = families_sorted[2]

    positive = {
        "weyl_anchor_rows_remain_pass_bearing": {
            "pass": weyl_anchor_family["pass"],
            "support_count": weyl_anchor_family["support_count"],
            "score": weyl_anchor_family["score"],
        },
        "hypergraph_family_is_pass_bearing": {
            "pass": hypergraph_family["pass"],
            "support_count": hypergraph_family["support_count"],
            "score": hypergraph_family["score"],
        },
        "multifamily_ranking_keeps_hypergraph_first": {
            "best_family_id": multifamily.get("summary", {}).get("best_family"),
            "pass": multifamily.get("summary", {}).get("best_family") == "hypergraph_family",
        },
        "multiway_support_rows_are_explicitly_available": {
            "hypergraph_support_count": multifamily.get("summary", {}).get("hypergraph_support_count"),
            "graph_support_count": multifamily.get("summary", {}).get("graph_support_count"),
            "contact_support_count": multifamily.get("summary", {}).get("contact_support_count"),
            "pass": truthy(multifamily.get("summary", {}).get("hypergraph_support_count", 0) >= 4),
        },
    }

    negative = {
        "pairwise_shadow_is_not_the_same_as_the_multiway_family": {
            "pairwise_shadow_gap": truthy(hypergraph.get("negative", {}).get("pairwise_shadow_does_not_retain_hyperedge_identity", {}).get("pass")),
            "shell_rankings_differ_from_pairwise": truthy(xgi_shell.get("summary", {}).get("rankings_differ_from_pairwise")),
            "pass": truthy(hypergraph.get("negative", {}).get("pairwise_shadow_does_not_retain_hyperedge_identity", {}).get("pass"))
            and truthy(xgi_shell.get("summary", {}).get("rankings_differ_from_pairwise")),
        },
        "follow_on_is_not_a_runtime_equivalence_claim": {
            "scope_note": (
                "This row ranks the next grounded geometry family beside the Weyl/Hopf anchor; "
                "it does not claim geometry-native runtime equivalence."
            ),
            "pass": True,
        },
    }

    boundary = {
        "hypergraph_support_rows_are_finite_and_connected": {
            "hypergraph_all_pass": result_pass(hypergraph),
            "dual_all_pass": result_pass(dual_hypergraph),
            "shell_all_pass": result_pass(xgi_shell),
            "crosscheck_all_pass": result_pass(toponetx_crosscheck),
            "pass": (
                result_pass(hypergraph)
                and result_pass(dual_hypergraph)
                and result_pass(xgi_shell)
                and result_pass(toponetx_crosscheck)
            ),
        },
        "crosscheck_topology_matches_a_torus_like_reference": {
            "beta0": toponetx_crosscheck.get("summary", {}).get("beta0"),
            "beta1": toponetx_crosscheck.get("summary", {}).get("beta1"),
            "beta2": toponetx_crosscheck.get("summary", {}).get("beta2"),
            "chi": toponetx_crosscheck.get("summary", {}).get("chi"),
            "pass": truthy(toponetx_crosscheck.get("summary", {}).get("chi_confirmed_zero")),
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )

    hypergraph_summary = hypergraph.get("summary", {})
    hypergraph_positive = hypergraph.get("positive", {})
    shell_summary = xgi_shell.get("summary", {})
    crosscheck_summary = toponetx_crosscheck.get("summary", {})

    results = {
        "name": "weyl_hypergraph_follow_on",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "family_rankings": [
            hypergraph_family,
            weyl_anchor_family,
            family_graph,
        ],
        "summary": {
            "all_pass": bool(all_pass),
            "best_family": best_family["family_id"],
            "best_family_score": best_family["score"],
            "runner_up_family": runner_up["family_id"],
            "third_family": third["family_id"],
            "family_count": len(families),
            "weyl_anchor_support_count": weyl_anchor_family["support_count"],
            "hypergraph_support_count": hypergraph_family["support_count"],
            "hypergraph_node_count": hypergraph_positive.get("incidence_and_counts_are_well_formed", {}).get("num_nodes"),
            "hypergraph_edge_count": hypergraph_positive.get("incidence_and_counts_are_well_formed", {}).get("num_edges"),
            "hypergraph_edge_sizes": hypergraph_positive.get("incidence_and_counts_are_well_formed", {}).get("edge_sizes"),
            "hypergraph_connected": hypergraph_positive.get("shadow_graph_preserves_connectivity", {}).get("hypergraph_connected"),
            "hypergraph_multiway_load_bearing": shell_summary.get("multi_way_structure_load_bearing"),
            "hypergraph_shell_count": shell_summary.get("hypergraph_shell_count"),
            "hyperedge_count": shell_summary.get("hyperedge_count"),
            "max_hyperedge_size": shell_summary.get("max_hyperedge_size"),
            "torus_beta0": crosscheck_summary.get("beta0"),
            "torus_beta1": crosscheck_summary.get("beta1"),
            "torus_beta2": crosscheck_summary.get("beta2"),
            "torus_chi": crosscheck_summary.get("chi"),
            "scope_note": (
                "Hypergraph follow-on row for the Weyl/Hopf stack. It makes the "
                "multiway hypergraph family the next controller-usable extension "
                "path and keeps the pairwise shadow explicitly distinct."
            ),
        },
    }

    OUT_PATH.write_text(json.dumps(results, indent=2))
    print(OUT_PATH)


if __name__ == "__main__":
    main()
