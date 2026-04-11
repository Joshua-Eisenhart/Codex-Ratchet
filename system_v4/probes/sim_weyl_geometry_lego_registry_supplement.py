#!/usr/bin/env python3
"""
Build a controller-facing supplement for the Weyl/Hopf geometry legos.

This does not edit the registry markdown. It reads the current registry
snapshot plus the new Weyl/Hopf geometry result files, then writes a
supplement JSON that maps the new rows onto existing lego-registry concepts
and flags the concepts that are still not normalized in actual_lego_registry.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"

REGISTRY_PATH = RESULTS_DIR / "actual_lego_registry.json"
OUT_PATH = RESULTS_DIR / "weyl_geometry_lego_registry_supplement_results.json"

REGISTRY_STATUS_ORDER = {
    "covered": 0,
    "partial": 1,
    "not_normalized_yet": 2,
    "missing": 3,
}

ROW_SPECS = [
    {
        "lego_id": "nested_hopf_tori_geometry",
        "lego_name": "Nested Hopf tori geometry",
        "lego_type": "geometry/base",
        "section": "Geometry Legos",
        "concrete_math": (
            "nested Hopf tori with left/right Weyl carriers, torus transport, "
            "and Pauli/Bloch consistency checks"
        ),
        "minimal_honest_sim": (
            "sample nested Hopf torus levels and verify carrier/unitarity/transport closures"
        ),
        "source_docs": "current_results+actual_lego_registry.json",
        "suggested_first_probe": "sim_lego_nested_hopf_tori.py",
        "best_existing_result": "lego_nested_hopf_tori_results.json",
        "result_file": "lego_nested_hopf_tori_results.json",
        "registry_concepts": [
            "nested_torus_geometry",
            "hopf_geometry",
            "torus_geometry",
            "spinor_geometry",
        ],
        "notes": (
            "The new concept itself is not normalized in actual_lego_registry yet; "
            "the supplement maps it onto the existing nested torus / Hopf / spinor rows."
        ),
    },
    {
        "lego_id": "weyl_pauli_transport_geometry",
        "lego_name": "Weyl/Pauli transport geometry",
        "lego_type": "geometry/transport",
        "section": "Loop, Connection, And Placement Legos",
        "concrete_math": (
            "left/right Weyl spinor transport with Pauli/Bloch readouts and bounded torus roundtrips"
        ),
        "minimal_honest_sim": (
            "run left/right spinors through nested torus transport and check chirality-sensitive readouts"
        ),
        "source_docs": "current_results+actual_lego_registry.json",
        "suggested_first_probe": "sim_lego_weyl_pauli_transport.py",
        "best_existing_result": "lego_weyl_pauli_transport_results.json",
        "result_file": "lego_weyl_pauli_transport_results.json",
        "registry_concepts": [
            "spinor_geometry",
            "weyl_chirality_pair",
            "pauli_generator_basis",
            "transport_geometry",
            "base_loop_law",
        ],
        "notes": (
            "The transport geometry itself is not normalized as a first-class row yet; "
            "it currently rides on spinor, Weyl, Pauli, and transport support concepts."
        ),
    },
    {
        "lego_id": "weyl_hopf_pauli_composed_stack",
        "lego_name": "Weyl/Hopf/Pauli composed stack",
        "lego_type": "geometry/composed_stack",
        "section": "Geometry Legos",
        "concrete_math": (
            "layered nested Hopf tori -> Weyl spinors -> Pauli/Bloch -> transport composition"
        ),
        "minimal_honest_sim": (
            "stage the four geometry layers one by one and verify stack-level consistency"
        ),
        "source_docs": "current_results+actual_lego_registry.json",
        "suggested_first_probe": "sim_weyl_hopf_pauli_composed_stack.py",
        "best_existing_result": "weyl_hopf_pauli_composed_stack_results.json",
        "result_file": "weyl_hopf_pauli_composed_stack_results.json",
        "registry_concepts": [
            "nested_torus_geometry",
            "spinor_geometry",
            "pauli_generator_basis",
            "fubini_study_geometry",
            "geometry_preserving_basis_change",
        ],
        "notes": (
            "This composed stack passes numerically, but the composed-stack concept is not "
            "normalized in actual_lego_registry yet."
        ),
    },
    {
        "lego_id": "weyl_geometry_protocol_dag",
        "lego_name": "Weyl geometry protocol DAG",
        "lego_type": "geometry/bridge",
        "section": "Graph / Topology Legos",
        "concrete_math": (
            "layered protocol DAG for nested Hopf torus, Weyl frames, Pauli projection, "
            "and torus transport ordering"
        ),
        "minimal_honest_sim": (
            "validate layered schedule order with graph structure and solver-backed back-edge kills"
        ),
        "source_docs": "current_results+actual_lego_registry.json",
        "suggested_first_probe": "sim_lego_weyl_geometry_protocol_dag.py",
        "best_existing_result": "lego_weyl_geometry_protocol_dag_results.json",
        "result_file": "lego_weyl_geometry_protocol_dag_results.json",
        "registry_concepts": [
            "graph_geometry",
            "loop_order_family",
            "base_loop_law",
            "carrier_probe_support",
        ],
        "notes": (
            "This bridge is clean, but the protocol-DAG concept and carrier-probe support "
            "are still not normalized in actual_lego_registry."
        ),
    },
    {
        "lego_id": "weyl_geometry_carrier_array",
        "lego_name": "Weyl geometry carrier array",
        "lego_type": "geometry/compare",
        "section": "Geometry Legos",
        "concrete_math": (
            "same Weyl-style readout core run across Hopf torus, sphere, graph, and hypergraph carriers"
        ),
        "minimal_honest_sim": (
            "compare the same readout core across multiple geometry carriers and compare invariants"
        ),
        "source_docs": "current_results+actual_lego_registry.json",
        "suggested_first_probe": "sim_lego_weyl_geometry_carrier_compare.py",
        "best_existing_result": "weyl_geometry_carrier_array_results.json",
        "result_file": "weyl_geometry_carrier_array_results.json",
        "registry_concepts": [
            "graph_geometry",
            "hypergraph_geometry",
            "sphere_geometry",
            "channel_space_geometry",
            "carrier_probe_support",
        ],
        "notes": (
            "The carrier-array concept is new; channel-space geometry and carrier-probe support "
            "are still not normalized in actual_lego_registry."
        ),
    },
    {
        "lego_id": "weyl_geometry_graph_proof_alignment",
        "lego_name": "Weyl geometry graph-proof alignment",
        "lego_type": "geometry/bridge",
        "section": "Graph / Topology Legos",
        "concrete_math": (
            "graph/proof bridge around nested Hopf torus, Weyl frames, Pauli projection, "
            "and torus transport"
        ),
        "minimal_honest_sim": (
            "validate the layered geometry schedule against solver-backed legality checks"
        ),
        "source_docs": "current_results+actual_lego_registry.json",
        "suggested_first_probe": "sim_weyl_geometry_graph_proof_alignment.py",
        "best_existing_result": "weyl_geometry_graph_proof_alignment_results.json",
        "result_file": "weyl_geometry_graph_proof_alignment_results.json",
        "registry_concepts": [
            "graph_geometry",
            "carrier_probe_support",
            "geometry_preserving_basis_change",
            "channel_space_geometry",
        ],
        "notes": (
            "This bridge row is research-support quality, but the bridge concept and the carrier "
            "support objects are still not normalized in actual_lego_registry."
        ),
    },
    {
        "lego_id": "weyl_geometry_ladder_audit",
        "lego_name": "Weyl geometry ladder audit",
        "lego_type": "geometry/audit",
        "section": "Loop, Connection, And Placement Legos",
        "concrete_math": (
            "ambient holonomy versus engine response across the nested Hopf torus ladder"
        ),
        "minimal_honest_sim": (
            "test whether the Weyl ambient rung has an independent witness before engine promotion"
        ),
        "source_docs": "current_results+actual_lego_registry.json",
        "suggested_first_probe": "sim_weyl_geometry_ladder_audit.py",
        "best_existing_result": "weyl_geometry_ladder_audit_results.json",
        "result_file": "weyl_geometry_ladder_audit_results.json",
        "registry_concepts": [
            "hopf_geometry",
            "spinor_geometry",
            "transport_geometry",
            "carrier_probe_support",
            "terrain_family_fourfold",
        ],
        "notes": (
            "The Weyl-ambient rung passes as an audit, but carrier support and terrain-family "
            "objects are still not normalized in actual_lego_registry."
        ),
    },
    {
        "lego_id": "weyl_geometry_carrier_compare",
        "lego_name": "Weyl geometry carrier compare",
        "lego_type": "geometry/compare",
        "section": "Graph / Topology Legos",
        "concrete_math": (
            "Weyl-style readout comparison across Hopf torus, sphere, graph, and hypergraph carriers"
        ),
        "minimal_honest_sim": (
            "compare carrier families on the same readout core and check the spread is informative"
        ),
        "source_docs": "current_results+actual_lego_registry.json",
        "suggested_first_probe": "sim_lego_weyl_geometry_carrier_compare.py",
        "best_existing_result": "lego_weyl_geometry_carrier_compare_results.json",
        "result_file": "lego_weyl_geometry_carrier_compare_results.json",
        "registry_concepts": [
            "graph_geometry",
            "hypergraph_geometry",
            "sphere_geometry",
            "carrier_probe_support",
            "channel_space_geometry",
        ],
        "notes": (
            "The carrier compare row is clean and reusable, but the carrier-probe and "
            "channel-space concepts are still not normalized in actual_lego_registry."
        ),
    },
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def current_coverage(registry_rows: dict[str, dict[str, Any]], concept_id: str) -> str:
    row = registry_rows.get(concept_id)
    if row is None:
        return "missing"
    return row.get("current_coverage", "missing")


def result_pass_status(payload: dict[str, Any]) -> bool:
    if "all_pass" in payload:
        return bool(payload["all_pass"])
    summary = payload.get("summary", {})
    if "all_pass" in summary:
        return bool(summary["all_pass"])
    verdict = payload.get("verdict", {})
    if "result" in verdict:
        return verdict["result"] == "PASS"
    return False


def result_classification(payload: dict[str, Any]) -> str | None:
    if payload.get("classification") is not None:
        return payload["classification"]
    summary = payload.get("summary", {})
    if summary.get("classification") is not None:
        return summary["classification"]
    verdict = payload.get("verdict", {})
    if verdict.get("result") == "PASS":
        return "research_support"
    if verdict.get("result") == "KILL":
        return "support_tradition_only"
    return None


def load_result_payload(name: str) -> dict[str, Any]:
    path = RESULTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"missing result file: {path}")
    return load_json(path)


def main() -> int:
    registry = load_json(REGISTRY_PATH)
    registry_rows = {row["lego_id"]: row for row in registry["rows"]}

    row_outputs: list[dict[str, Any]] = []
    source_result_files: list[str] = []

    for spec in ROW_SPECS:
        payload = load_result_payload(spec["result_file"])
        source_result_files.append(spec["result_file"])

        registry_statuses = {
            concept_id: current_coverage(registry_rows, concept_id)
            for concept_id in spec["registry_concepts"]
        }
        normalized_registry_concepts = [
            concept_id for concept_id, status in registry_statuses.items()
            if status in {"covered", "partial"}
        ]
        partial_registry_concepts = [
            concept_id for concept_id, status in registry_statuses.items()
            if status == "partial"
        ]
        not_normalized_registry_concepts = [
            concept_id for concept_id, status in registry_statuses.items()
            if status == "not_normalized_yet"
        ]
        missing_registry_concepts = [
            concept_id for concept_id, status in registry_statuses.items()
            if status == "missing"
        ]

        if not_normalized_registry_concepts or missing_registry_concepts:
            registry_alignment_status = "not_normalized_yet"
        elif partial_registry_concepts:
            registry_alignment_status = "partial"
        else:
            registry_alignment_status = "covered"

        row_outputs.append(
            {
                "section": spec["section"],
                "lego_id": spec["lego_id"],
                "lego_name": spec["lego_name"],
                "lego_type": spec["lego_type"],
                "concrete_math": spec["concrete_math"],
                "minimal_honest_sim": spec["minimal_honest_sim"],
                "source_docs": spec["source_docs"],
                "suggested_first_probe": spec["suggested_first_probe"],
                "best_existing_result": spec["best_existing_result"],
                "new_concept_registry_status": "not_normalized_yet",
                "new_concept_normalized_in_actual_registry": False,
                "current_coverage": registry_alignment_status,
                "result_file": spec["result_file"],
                "result_classification": result_classification(payload),
                "result_all_pass": result_pass_status(payload),
                "registry_concepts": spec["registry_concepts"],
                "normalized_registry_concepts": normalized_registry_concepts,
                "partial_registry_concepts": partial_registry_concepts,
                "not_normalized_registry_concepts": not_normalized_registry_concepts,
                "missing_registry_concepts": missing_registry_concepts,
                "registry_statuses": registry_statuses,
                "useful_if_rejected": "yes",
                "notes": spec["notes"],
            }
        )

    new_concepts_not_in_actual_registry = [row["lego_id"] for row in row_outputs]
    existing_registry_gaps = sorted(
        {
            concept_id
            for row in row_outputs
            for concept_id, status in row["registry_statuses"].items()
            if status == "not_normalized_yet"
        }
    )
    partial_registry_concepts = sorted(
        {
            concept_id
            for row in row_outputs
            for concept_id, status in row["registry_statuses"].items()
            if status == "partial"
        }
    )
    covered_registry_concepts = sorted(
        {
            concept_id
            for row in row_outputs
            for concept_id, status in row["registry_statuses"].items()
            if status == "covered"
        }
    )
    all_results_pass = all(row["result_all_pass"] for row in row_outputs)

    supplement = {
        "name": "weyl_geometry_lego_registry_supplement",
        "classification": "controller_facing_supplement",
        "generated_at": datetime.now(UTC).isoformat(),
        "source_registry": str(REGISTRY_PATH.relative_to(PROJECT_DIR)),
        "source_result_files": source_result_files,
        "summary": {
            "all_pass": all_results_pass,
            "row_count": len(row_outputs),
            "new_concepts_not_in_actual_registry": new_concepts_not_in_actual_registry,
            "existing_registry_gaps": existing_registry_gaps,
            "partial_registry_concepts": partial_registry_concepts,
            "covered_registry_concepts": covered_registry_concepts,
            "scope_note": (
                "Controller-facing supplement for the Weyl/Hopf geometry legos. "
                "It maps the new rows onto existing registry concepts without mutating "
                "actual_lego_registry.json."
            ),
        },
        "rows": row_outputs,
    }

    OUT_PATH.write_text(json.dumps(supplement, indent=2) + "\n", encoding="utf-8")
    print(OUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
