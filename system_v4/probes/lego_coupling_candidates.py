#!/usr/bin/env python3
"""
Machine routing surface for lego -> coupling progression.

Consumes:
  - lego_stack_audit_results.json
  - live_anchor_spine.json
  - controller_alignment_audit_results.json

Emits:
  - lego_coupling_candidates.json

Goal:
  keep the repo lego-first by making the next pairwise/coupling surfaces
  explicit, and by blocking premature assembly promotion.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
LEGO_AUDIT_PATH = RESULTS_DIR / "lego_stack_audit_results.json"
LIVE_SPINE_PATH = RESULTS_DIR / "live_anchor_spine.json"
ALIGN_PATH = RESULTS_DIR / "controller_alignment_audit_results.json"
OUT_PATH = RESULTS_DIR / "lego_coupling_candidates.json"

COUPLING_TARGETS = {
    "carrier_admission_density_matrix": {
        "pairings": [
            {
                "lego_probe": "sim_density_hopf_geometry.py",
                "coupling_probe": "sim_operator_geometry_compatibility.py",
                "existing_anchor": "operator_geometry_compatibility_results.json",
                "status": "existing_anchor",
                "reason": "Carrier/geometry object should feed operator-vs-geometry compatibility before wider assembly.",
            },
            {
                "lego_probe": "sim_density_hopf_geometry.py",
                "coupling_probe": "sim_integrated_dependency_chain.py",
                "existing_anchor": "integrated_dependency_chain_results.json",
                "status": "existing_anchor",
                "reason": "Density/carrier admission already has a stronger pairwise dependency successor.",
            },
        ],
    },
    "geometry_crosschecks_same_carrier": {
        "pairings": [
            {
                "lego_probe": "sim_foundation_hopf_torus_geomstats_clifford.py",
                "coupling_probe": "sim_operator_geometry_compatibility.py",
                "existing_anchor": "operator_geometry_compatibility_results.json",
                "status": "existing_anchor",
                "reason": "Geometry families should meet operator compatibility before stacking/coexistence.",
            },
            {
                "lego_probe": "sim_berry_qfi_shell_paths.py",
                "coupling_probe": "sim_compound_operator_geometry.py",
                "existing_anchor": "compound_operator_geometry_results.json",
                "status": "supporting_only",
                "reason": "Berry/QFI shell-local geometry can feed the existing compound operator/geometry map, but that successor is still supporting rather than closure-grade.",
            },
        ],
    },
    "graph_cell_complex_geometry": {
        "pairings": [
            {
                "lego_probe": "sim_xgi_family_hypergraph.py",
                "coupling_probe": "sim_xgi_indirect_pathway.py",
                "existing_anchor": "xgi_indirect_pathway_results.json",
                "status": "existing_anchor",
                "reason": "Pure hypergraph family structure already has a pairwise/multi-way pathway successor.",
            },
            {
                "lego_probe": "sim_foundation_shell_graph_topology.py",
                "coupling_probe": "sim_toponetx_state_class_binding.py",
                "existing_anchor": "toponetx_state_class_binding_results.json",
                "status": "existing_anchor",
                "reason": "Shell-local topology should feed state-class binding before assembly.",
            },
            {
                "lego_probe": "sim_foundation_equivariant_graph_backprop.py",
                "coupling_probe": "sim_pyg_dynamic_edge_werner.py",
                "existing_anchor": "pyg_dynamic_edge_werner_results.json",
                "status": "existing_anchor",
                "reason": "PyG foundation lego already has a narrow pairwise/regime successor.",
            },
        ],
    },
    "bipartite_structure_local": {
        "pairings": [
            {
                "lego_probe": "sim_gudhi_concurrence_filtration.py",
                "coupling_probe": "sim_pyg_dynamic_edge_werner.py",
                "existing_anchor": "pyg_dynamic_edge_werner_results.json",
                "status": "existing_anchor",
                "reason": "Local bipartite witnesses should first feed a narrow differentiable/regime coupling surface.",
            },
            {
                "lego_probe": "sim_gudhi_bipartite_entangled.py",
                "coupling_probe": "sim_lego_entropy_bipartite_cut.py",
                "existing_anchor": "lego_entropy_bipartite_cut_results.json",
                "status": "existing_anchor",
                "reason": "Local bipartite topology already has a canonical entropy/cut successor before wider assembly.",
            },
        ],
    },
    "constraint_probe_admissibility": {
        "pairings": [
            {
                "lego_probe": "sim_bc1_fence_investigation.py",
                "coupling_probe": "sim_constraint_shells_binding_crosscheck.py",
                "existing_anchor": "constraint_shells_binding_crosscheck_results.json",
                "status": "existing_anchor",
                "reason": "Constraint/probe legos already feed an explicit canonical binding crosscheck successor.",
            },
        ],
    },
    "operator_family_admission": {
        "pairings": [
            {
                "lego_probe": None,
                "coupling_probe": "sim_operator_geometry_compatibility.py",
                "existing_anchor": "operator_geometry_compatibility_results.json",
                "status": "supporting_only",
                "reason": "Best current operator/geometry successor exists, but it is supporting rather than closure-grade.",
            },
        ],
    },
    "entropy_family_crosschecks": {
        "pairings": [
            {
                "lego_probe": None,
                "coupling_probe": None,
                "existing_anchor": None,
                "status": "blocked_until_better_lego",
                "reason": "Entropy family work is still too tied to later surfaces; lower-layer local entropy witnesses need a cleaner lego set first.",
            },
        ],
    },
    "gauge_group_falsifier": {
        "pairings": [
            {
                "lego_probe": "sim_geom_cp1_u1_projective.py",
                "coupling_probe": None,
                "existing_anchor": None,
                "status": "blocked_from_assembly",
                "reason": "Useful falsifier/root-kill candidate, but not part of the main assembly ladder until lower operator legos are stronger.",
            },
        ],
    },
    "quantum_metric_nonuniqueness": {
        "pairings": [
            {
                "lego_probe": "sim_geomstats_shell_metrics.py",
                "coupling_probe": None,
                "existing_anchor": None,
                "status": "blocked_from_assembly",
                "reason": "Useful geometry pressure surface, but should remain a boundary/selection lego until pairwise metric-choice effects are cleaner.",
            },
        ],
    },
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def spine_rows_by_result() -> dict[str, dict]:
    spine = read_json(LIVE_SPINE_PATH)
    return {row["result_json"]: row for row in spine.get("rows", [])}


def recommended_lego_rows() -> list[dict]:
    lego = read_json(LEGO_AUDIT_PATH)
    rows = []
    for row in lego.get("candidates", []):
        if row.get("assembly_stage") == "lego":
            rows.append(row)
    return rows


def shallow_tools() -> list[str]:
    align = read_json(ALIGN_PATH)
    return align.get("tool_stack_summary", {}).get("shallow_tools", [])


def build_rows() -> list[dict]:
    lego_rows = {row["id"]: row for row in recommended_lego_rows()}
    spine = spine_rows_by_result()
    shallow = set(shallow_tools())

    rows = []
    for lego_id, spec in COUPLING_TARGETS.items():
        row = lego_rows.get(lego_id)
        if row is None:
            continue
        recommended = row.get("recommended_probe_files", [])
        for pairing in spec["pairings"]:
            existing_anchor = pairing["existing_anchor"]
            spine_info = spine.get(existing_anchor, {}) if existing_anchor else {}
            rows.append({
                "lego_family_id": lego_id,
                "lego_probe": pairing["lego_probe"],
                "recommended_lego_probes": recommended,
                "coupling_probe": pairing["coupling_probe"],
                "existing_anchor": existing_anchor,
                "existing_anchor_stage": spine_info.get("stage"),
                "existing_anchor_promotion_ready": spine_info.get("promotion_ready"),
                "status": pairing["status"],
                "topology_rerun_needed": pairing["status"] == "existing_anchor" and lego_id in {
                    "graph_cell_complex_geometry",
                    "geometry_crosschecks_same_carrier",
                },
                "coexistence_rerun_needed": pairing["status"] == "existing_anchor" and lego_id in {
                    "carrier_admission_density_matrix",
                    "graph_cell_complex_geometry",
                    "bipartite_structure_local",
                },
                "blocked_from_assembly": pairing["status"] in {
                    "blocked_from_assembly",
                    "blocked_until_better_lego",
                },
                "reason": pairing["reason"],
                "shallow_tool_pressure": sorted(
                    tool for tool in shallow
                    if tool in json.dumps(pairing).lower() or tool in json.dumps(row).lower()
                ),
            })
    return rows


def main() -> int:
    rows = build_rows()
    report = {
        "name": "lego_coupling_candidates",
        "generated_at": datetime.now(UTC).isoformat(),
        "rows": rows,
        "summary": {
            "pairing_count": len(rows),
            "existing_anchor_count": sum(1 for row in rows if row["status"] == "existing_anchor"),
            "missing_pairwise_count": sum(1 for row in rows if row["status"] == "missing_pairwise"),
            "blocked_from_assembly_count": sum(1 for row in rows if row["blocked_from_assembly"]),
            "supporting_only_count": sum(1 for row in rows if row["status"] == "supporting_only"),
        },
    }
    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"pairing_count={report['summary']['pairing_count']}")
    print(f"missing_pairwise_count={report['summary']['missing_pairwise_count']}")
    print(f"blocked_from_assembly_count={report['summary']['blocked_from_assembly_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
