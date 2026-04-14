#!/usr/bin/env python3
"""
Parse the markdown lego registry into a machine-readable JSON artifact.

Consumes:
  - system_v5/new docs/17_actual_lego_registry.md

Emits:
  - system_v4/probes/a2_state/sim_results/actual_lego_registry.json

Goal:
  keep the actual one-row-per-lego registry usable by controller code
  without asking later surfaces to scrape markdown ad hoc.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
REGISTRY_PATH = PROJECT_DIR / "new docs" / "17_actual_lego_registry.md"
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
OUT_PATH = RESULTS_DIR / "actual_lego_registry.json"
QUEUE_PATH = RESULTS_DIR / "actual_lego_normalization_queue.json"
SUPPLEMENT_PATH = RESULTS_DIR / "actual_lego_registry_supplement.json"

DIRECT_PROBE_PREFERENCES = {
    "bures_geometry": "sim_bures_geometry.py",
    "fubini_study_geometry": "sim_fubini_study_geometry.py",
    "nested_torus_geometry": "sim_nested_torus_geometry.py",
    "sphere_geometry": "sim_sphere_geometry.py",
    "eigenvalue_spectrum_view": "sim_eigenvalue_spectrum_view.py",
    "schmidt_mode_truncation": "sim_schmidt_mode_truncation.py",
    "geometry_preserving_basis_change": "sim_geometry_preserving_basis_change.py",
    "entanglement_spectrum": "sim_entanglement_spectrum.py",
    "stokes_parameterization": "sim_stokes_parameterization.py",
    "graph_shell_geometry": "sim_graph_shell_geometry.py",
    "operator_coordinate_representation": "sim_operator_coordinate_representation.py",
    "representation_violation_check": "sim_representation_violation_check.py",
    "pauli_generator_basis": "sim_pauli_generator_basis.py",
    "clifford_generator_basis": "sim_clifford_generator_basis.py",
    "commutator_algebra": "sim_commutator_algebra.py",
    "pauli_algebra_relations": "sim_pauli_algebra_relations.py",
    "local_operator_action": "sim_local_operator_action.py",
    "joint_operator_action": "sim_joint_operator_action.py",
    "channel_capacity": "sim_channel_capacity.py",
    "characteristic_representation": "sim_characteristic_representation.py",
    "husimi_phase_space_representation": "sim_husimi_phase_space_representation.py",
    "channel_space_geometry": "sim_channel_space_geometry.py",
    "base_loop_law": "sim_base_loop_law.py",
    "loop_vector_fields": "sim_loop_vector_fields.py",
    "loop_order_family": "sim_loop_order_family.py",
    "history_window_entropy": "sim_history_window_entropy.py",
    "transport_weighted_entropy": "sim_transport_weighted_entropy.py",
    "operator_ordered_entropy": "sim_operator_ordered_entropy.py",
    "history_window_support": "sim_history_window_support.py",
    "branch_weight": "sim_branch_weight.py",
    "path_entropy": "sim_path_entropy.py",
    "torus_seat_entropy": "sim_torus_seat_entropy.py",
    "bridge_family_xi_shell": "sim_bridge_family_xi_shell.py",
    "bridge_family_xi_history": "sim_bridge_family_xi_history.py",
    "shell_fuzz_jk": "sim_shell_fuzz_jk.py",
    "ring_checkerboard_support": "sim_ring_checkerboard_support.py",
    "shell_indexed_tensor_network": "sim_shell_indexed_tensor_network.py",
    "discrete_axis0_field": "sim_discrete_axis0_field.py",
    "bridge_family_xi_point": "sim_bridge_family_xi_point.py",
    "axis0_kernel_phi0": "sim_axis0_kernel_phi0.py",
    "unsigned_entropy_family": "sim_unsigned_entropy_family.py",
    "shell_weighted_entropy_field": "sim_shell_weighted_entropy_field.py",
    "shell_window_support": "sim_shell_window_support.py",
    "relative_entropy_nonmetric_boundary": "sim_relative_entropy_nonmetric_boundary.py",
    "hilbert_schmidt_flatness_rejection": "sim_hilbert_schmidt_flatness_rejection.py",
    "real_only_geometry_rejection": "sim_real_only_geometry_rejection.py",
    "gauge_group_correspondence": "sim_gauge_group_correspondence.py",
    "viability_vs_attractor": "sim_viability_vs_attractor.py",
    "commutative_geometry_collapse": "sim_commutative_geometry_collapse.py",
    "hypergraph_geometry": "sim_hypergraph_geometry.py",
    "dual_hypergraph_geometry": "sim_dual_hypergraph_geometry.py",
    "state_class_binding_geometry": "sim_state_class_binding_geometry.py",
    "conditional_entropy": "sim_conditional_entropy.py",
    "von_neumann_entropy": "sim_von_neumann_entropy.py",
    "entanglement_entropy": "sim_entanglement_entropy.py",
    "holevo_quantity": "sim_holevo_quantity.py",
    "relative_entropy_js": "sim_relative_entropy_js.py",
    "shannon_entropy": "sim_shannon_entropy.py",
    "coherent_information_measure": "sim_coherent_information_measure.py",
    "helstrom_guess_bound": "sim_helstrom_guess_bound.py",
    "distinguishability_relation": "sim_distinguishability_relation.py",
    "negativity_measure": "sim_negativity_measure.py",
    "logarithmic_negativity": "sim_negativity_measure.py",
}

TABLE_SECTIONS = {
    "Root And Admission Legos",
    "Constraint And Carrier Reference Legos",
    "State Representation Legos",
    "Compression And Spectral Legos",
    "Geometry Legos",
    "Loop, Connection, And Placement Legos",
    "Operator And Channel Legos",
    "Graph / Topology Legos",
    "Bipartite And Correlation Legos",
    "Entropy Legos",
    "Bridge, Axis, And Support Legos",
    "Boundary Falsifier Legos",
    "Math-Source Coverage Notes",
}


def parse_table_line(line: str) -> list[str]:
    return [normalize_cell(cell.strip()) for cell in line.strip().strip("|").split("|")]


def normalize_cell(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        return value[1:-1]
    return value


def normalize_key(label: str) -> str:
    return (
        label.strip()
        .lower()
        .replace("/", " ")
        .replace("-", " ")
        .replace("(", "")
        .replace(")", "")
        .replace(".", "")
        .replace(":", "")
        .replace("`", "")
        .replace(" ", "_")
    )


def result_path_for_probe(probe: str | None) -> Path | None:
    if not probe or not probe.endswith(".py"):
        return None
    stem = probe[:-3]
    if stem.startswith("sim_"):
        stem = stem[4:]
    return RESULTS_DIR / f"{stem}_results.json"


def probe_result_truth(probe: str | None) -> dict:
    path = result_path_for_probe(probe)
    if path is None or not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    all_pass = data.get("all_pass")
    if all_pass is None:
        all_pass = data.get("summary", {}).get("all_pass")
    return {
        "probe": probe,
        "result_json": path.name,
        "classification": data.get("classification"),
        "all_pass": all_pass,
    }


def parse_registry() -> dict:
    text = REGISTRY_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    status_line = next((line for line in lines if line.startswith("Status: ")), "")
    sections: dict[str, list[dict]] = {}

    current_section: str | None = None
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            heading = line[3:].strip()
            current_section = heading if heading in TABLE_SECTIONS else None
            i += 1
            continue

        if current_section and line.startswith("| ") and i + 1 < len(lines) and lines[i + 1].startswith("| ---"):
            headers = parse_table_line(line)
            key_headers = [normalize_key(h) for h in headers]
            rows: list[dict] = []
            i += 2
            while i < len(lines) and lines[i].startswith("| "):
                values = parse_table_line(lines[i])
                if len(values) == len(key_headers):
                    rows.append(dict(zip(key_headers, values, strict=True)))
                i += 1
            sections[current_section] = rows
            continue

        i += 1

    registry_sections = {
        name: rows for name, rows in sections.items() if name != "Math-Source Coverage Notes"
    }
    coverage_rows = sections.get("Math-Source Coverage Notes", [])

    all_rows = [
        {
            "section": section,
            **row,
        }
        for section, rows in registry_sections.items()
        for row in rows
    ]

    if SUPPLEMENT_PATH.exists():
        supplement = json.loads(SUPPLEMENT_PATH.read_text(encoding="utf-8"))
        all_rows.extend(supplement.get("rows", []))

    queue_rows_by_id = {}
    if QUEUE_PATH.exists():
        queue_payload = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
        queue_rows_by_id = {
            row["lego_id"]: row
            for row in queue_payload.get("rows", [])
        }

    derived_covered_count = 0
    for row in all_rows:
        lego_id = row.get("lego_id")
        qrow = queue_rows_by_id.get(lego_id)
        direct_probe = DIRECT_PROBE_PREFERENCES.get(lego_id)
        direct_truth = probe_result_truth(direct_probe)
        if not qrow:
            row["machine_current_coverage"] = row.get("current_coverage", "")
            if direct_truth:
                row["machine_best_probe"] = direct_truth.get("probe")
                row["machine_best_result"] = direct_truth.get("result_json")
                row["machine_result_classification"] = direct_truth.get("classification")
                row["machine_mapping_confidence"] = "high"
                row["machine_needs_new_probe"] = False
                if direct_truth.get("classification") == "canonical":
                    row["machine_current_coverage"] = "covered"
                    derived_covered_count += 1
            elif row.get("current_coverage") == "covered":
                row["machine_best_probe"] = row.get("suggested_first_probe")
                row["machine_best_result"] = row.get("best_existing_result")
                row["machine_result_classification"] = None
                row["machine_mapping_confidence"] = "high" if row.get("suggested_first_probe") else "low"
                row["machine_needs_new_probe"] = False if row.get("suggested_first_probe") else True
            continue

        machine_probe = qrow.get("reusable_probe")
        machine_result = qrow.get("existing_result_json")
        machine_classification = qrow.get("existing_result_classification")
        machine_confidence = qrow.get("mapping_confidence")
        machine_needs_new_probe = qrow.get("needs_new_probe")
        machine_coverage = row.get("current_coverage", "")

        if (
            direct_truth
            and direct_truth.get("classification") == "canonical"
            and direct_truth.get("result_json")
        ):
            machine_probe = direct_truth.get("probe")
            machine_result = direct_truth.get("result_json")
            machine_classification = direct_truth.get("classification")
            machine_confidence = "high"
            machine_needs_new_probe = False

        row["machine_best_probe"] = machine_probe
        row["machine_best_result"] = machine_result
        row["machine_result_classification"] = machine_classification
        row["machine_mapping_confidence"] = machine_confidence
        row["machine_needs_new_probe"] = machine_needs_new_probe
        row["machine_suggested_first_probe"] = machine_probe or row.get("suggested_first_probe")
        row["machine_best_existing_result"] = machine_result or row.get("best_existing_result")

        if (
            machine_classification == "canonical"
            and machine_probe
            and machine_result
            and not qrow.get("result_truth_warning")
        ):
            machine_coverage = "covered"
            derived_covered_count += 1
        row["machine_current_coverage"] = machine_coverage

    section_counts = {
        section: len(rows)
        for section, rows in registry_sections.items()
    }

    coverage_counts: dict[str, int] = {}
    for row in all_rows:
        status = row.get("machine_current_coverage", row.get("current_coverage", ""))
        coverage_counts[status] = coverage_counts.get(status, 0) + 1

    source_docs = sorted(
        {
            token.strip()
            for row in all_rows
            for token in row.get("source_docs", "").split(",")
            if token.strip()
        }
    )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_markdown": str(REGISTRY_PATH.relative_to(PROJECT_DIR)),
        "status_line": normalize_cell(status_line.removeprefix("Status: ").strip()),
        "row_count": len(all_rows),
        "section_count": len(registry_sections),
        "section_counts": section_counts,
        "coverage_counts": coverage_counts,
        "machine_overlay_source": str(QUEUE_PATH.relative_to(PROJECT_DIR)) if QUEUE_PATH.exists() else None,
        "supplement_source": str(SUPPLEMENT_PATH.relative_to(PROJECT_DIR)) if SUPPLEMENT_PATH.exists() else None,
        "machine_overlay_promoted_to_covered_count": derived_covered_count,
        "source_doc_keys_seen": source_docs,
        "rows": all_rows,
        "coverage_notes": coverage_rows,
    }


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = parse_registry()
    OUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"Rows: {payload['row_count']}")


if __name__ == "__main__":
    main()
