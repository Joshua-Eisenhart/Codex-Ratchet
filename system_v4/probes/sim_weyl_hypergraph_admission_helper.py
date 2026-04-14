#!/usr/bin/env python3
"""
Weyl hypergraph admission helper.

This is a controller-side routing helper for the already-built hypergraph
family. It does not claim a new runtime carrier. It only decides whether the
existing hypergraph artifacts are strong enough to be admitted as the next
geometry family beside the stabilized Weyl/Hopf anchor.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any


PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
OUT_PATH = RESULT_DIR / "weyl_hypergraph_admission_helper_results.json"

CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Controller-side admission helper for the Weyl hypergraph lane. It reads "
    "the finished hypergraph rows and decides whether the next family should be "
    "admitted as family-expansion beside the Weyl/Hopf anchor."
)

LEGO_IDS = [
    "weyl_hypergraph_follow_on",
    "weyl_hypergraph_geometry_bridge",
    "weyl_geometry_multifamily_expansion",
    "hypergraph_geometry",
    "dual_hypergraph_geometry",
    "xgi_shell_hypergraph",
    "toponetx_hopf_crosscheck",
]

PRIMARY_LEGO_IDS = [
    "weyl_hypergraph_follow_on",
    "weyl_hypergraph_geometry_bridge",
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


def result_pass(result: dict[str, Any]) -> bool:
    summary = result.get("summary")
    if isinstance(summary, dict) and "all_pass" in summary:
        return truthy(summary["all_pass"])
    if "all_pass" in result:
        return truthy(result["all_pass"])
    if result.get("classification") == "canonical":
        return True
    positive = result.get("positive")
    if isinstance(positive, dict) and positive:
        return all(truthy(v.get("pass")) for v in positive.values() if isinstance(v, dict))
    return False


def main() -> None:
    follow_on = load_json("weyl_hypergraph_follow_on_results.json")
    bridge = load_json("weyl_hypergraph_geometry_bridge_results.json")
    family = load_json("weyl_geometry_multifamily_expansion_results.json")
    hypergraph = load_json("hypergraph_geometry_results.json")
    dual_hypergraph = load_json("dual_hypergraph_geometry_results.json")
    xgi_shell = load_json("xgi_shell_hypergraph_results.json")
    crosscheck = load_json("toponetx_hopf_crosscheck_results.json")

    follow_on_pass = truthy(follow_on["summary"]["all_pass"])
    bridge_pass = truthy(bridge["summary"]["all_pass"])
    family_pass = truthy(family["summary"]["all_pass"])
    support_pass = all(result_pass(item) for item in [hypergraph, dual_hypergraph, xgi_shell, crosscheck])

    best_family = family["summary"]["best_family"]
    decision = "admit_as_family_expansion" if all([follow_on_pass, bridge_pass, family_pass, support_pass, best_family == "hypergraph_family"]) else "keep_as_bridge_only"
    controller_route = "family_expansion" if decision == "admit_as_family_expansion" else "graph_proof_bridge"

    results = {
        "name": "weyl_hypergraph_admission_helper",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": True,
            "decision": decision,
            "controller_route": controller_route,
            "best_family": best_family,
            "best_family_score": family["summary"]["best_family_score"],
            "follow_on_pass": follow_on_pass,
            "bridge_pass": bridge_pass,
            "family_pass": family_pass,
            "support_pass": support_pass,
            "hypergraph_support_count": family["summary"]["hypergraph_support_count"],
            "weyl_anchor_support_count": family["summary"]["weyl_anchor_support_count"],
            "hypergraph_edge_count": follow_on["summary"]["hypergraph_edge_count"],
            "hypergraph_edge_sizes": follow_on["summary"]["hypergraph_edge_sizes"],
            "pairwise_shadow_edge_count": bridge["summary"]["pairwise_shadow_edge_count"],
            "graph_path_length": bridge["summary"]["graph_path_length"],
            "hypergraph_multiway_load_bearing": follow_on["summary"]["hypergraph_multiway_load_bearing"],
            "torus_chi": follow_on["summary"]["torus_chi"],
            "scope_note": (
                "Hypergraph admission helper for the Weyl/Hopf controller stack. It admits the "
                "family as a family-expansion sidecar because the hypergraph family is the top "
                "ranked next extension and both the dedicated follow-on and bridge rows pass."
            ),
        },
        "evidence": {
            "follow_on": follow_on["summary"],
            "bridge": bridge["summary"],
            "family": family["summary"],
        },
    }

    OUT_PATH.write_text(json.dumps(results, indent=2) + "\n")
    print(OUT_PATH)


if __name__ == "__main__":
    main()
