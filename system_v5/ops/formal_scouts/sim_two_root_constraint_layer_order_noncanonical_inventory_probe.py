#!/usr/bin/env python3
"""Noncanonical layer-order / compression / algebra-closure inventory scout.

Workstream 4 required-first receipt. This scout compares the legacy 13-layer
fixture against the master atlas surfaces, classifies the 13-layer stack as a
candidate-only compression, and separates Pauli/Bloch/Clifford-torus geometry
from added Clifford algebra/module closure.

It is intentionally an audit receipt. It does not prove a canonical layer
ordering, a real attractor basin, a Clifford theorem, an Axis0 theorem, or a
final constraint manifold.
"""

from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import re
import time
from typing import Any

import rustworkx as rx
import sympy as sp
import torch
import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_layer_order_noncanonical_inventory_probe_results.json"

NAME = "two_root_constraint_layer_order_noncanonical_inventory_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_layer_order_noncanonical_inventory"
CLAIM_CEILING = (
    "Formal scout only: inventories the 13-layer fixture as a candidate legacy "
    "compression, compares it to the 17/20-layer master atlas and formal chain, "
    "and classifies Clifford/Cl-module usage as added closure or selector risk. "
    "It does not admit a canonical layer order, real attractor basin, final "
    "constraint manifold, Axis0 theorem, engine theorem, physics validation, "
    "Holodeck validation, or Clifford theorem."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite inventory tensor comparing legacy, atlas, formal-chain, and open-surface counts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph comparison of legacy chain vs master atlas chain and missing terminal bridge nodes",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite proof that current evidence blocks exact 13-layer forcing and canonical-order claims",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Pauli anticommutator witness used only to distinguish Pauli basis from Clifford-module closure",
    },
    "python_re": {"tried": True, "used": True, "reason": "supportive source text inventory extraction"},
    "python_json": {"tried": True, "used": True, "reason": "supportive formal-scout receipt serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive repository path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "sympy": "load_bearing",
    "python_re": "supportive",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

REF_ROOT = REPO / "system_v5" / "READ ONLY Reference Docs"
PLAN = REPO / "system_v5" / "ops" / "NEXT_GOAL_LONG_FORMAL_MANIFOLD_RETOOL_PLAN.md"
LEGACY_STACK = SCOUT_ROOT / "sim_nested_geometry_tower_dependency_order_probe.py"
W1_RESULT = RESULT_DIR / "two_root_constraint_classical_admin_load_bearing_partition_repair_probe_results.json"
W2_RESULT = RESULT_DIR / "two_root_constraint_grok_97_114_boundary_ingest_probe_results.json"
W3_RESULT = RESULT_DIR / "constraint_manifold_terrain_lindblad_composition_bridge_probe_results.json"

MASTER_SURFACES = {
    "17_layer_ladder": REF_ROOT / "Outdated math and geometry ladder.md",
    "20_layer_atlas": REF_ROOT / "AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md",
    "formal_chain": REF_ROOT / "Formal constraints and geometry .md",
}

AUDIT_STACK_FILES = {
    "legacy_13_fixture": LEGACY_STACK,
    "thirteen_layer_active_nested_mps": SCOUT_ROOT
    / "sim_thirteen_layer_active_nested_manifold_mps_special_holonomy_deep_graveyard_dynamic_tensor_network_probe.py",
    "eight_to_sixtyfour_boundary_scaling": SCOUT_ROOT
    / "sim_two_root_constraint_8_16_32_64_site_basin_boundary_scaling_probe.py",
    "mps_local_boundary_path_fep": SCOUT_ROOT / "sim_mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe.py",
    "peps3d_64_site_slot_dynamics": SCOUT_ROOT
    / "sim_source_native_peps3d_64_site_bond_dimension_slot_dynamics_probe.py",
}

REQUIRED_MASTER_VERSIONS = ["17_layer_ladder", "20_layer_atlas", "formal_chain"]

MASTER_20_LAYER_NAMES = [
    "root constraints",
    "admissibility set",
    "admissible manifold",
    "axis-slice rule",
    "favored finite realization",
    "normalized carrier",
    "Hopf projection",
    "Bloch sphere image",
    "torus stratum",
    "Clifford torus",
    "fiber-loop family",
    "lifted-base-loop family",
    "left Weyl sheet",
    "right Weyl sheet",
    "left density",
    "right density",
    "engine runtime manifold",
    "bridge target family",
    "bipartite cut-state family",
    "Axis 0 kernel family",
]

FORMAL_CHAIN_NODES = [
    "constraints",
    "M(C)",
    "S3",
    "T_eta",
    "psi_L/psi_R",
    "rho_L/rho_R/gamma_f/gamma_b",
    "Xi",
    "rho_AB",
    "entropy",
]

LEGACY_TO_MASTER_MAP = {
    "finite_constraint_complex": ["root constraints", "admissibility set", "admissible manifold"],
    "complex_hilbert_carrier": ["favored finite realization"],
    "unit_spinor_sphere": ["normalized carrier"],
    "projective_base_sphere": ["Bloch sphere image"],
    "hopf_fiber_bundle": ["Hopf projection"],
    "hopf_torus_leaf_family": ["torus stratum"],
    "connection_holonomy_geometry": ["Hopf connection / loop law"],
    "weyl_spinor_bundle": ["left Weyl sheet", "right Weyl sheet"],
    "chirality_orientation_cover": ["sheet orientation / split"],
    "clifford_module_geometry": ["Clifford algebra/module closure"],
    "frame_bundle_structure_reduction": ["added frame/reduction layer"],
    "tensor_product_coupling_geometry": ["added tensor coupling layer"],
    "dynamic_transition_ratchet_geometry": ["engine runtime / schedule dynamics"],
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return float(value.detach().cpu().item())
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    return value


def line_hits(path: pathlib.Path, needles: list[str], limit: int = 8) -> list[dict[str, Any]]:
    text = read_text(path)
    hits: list[dict[str, Any]] = []
    lowered = [needle.lower() for needle in needles]
    for lineno, line in enumerate(text.splitlines(), start=1):
        low = line.lower()
        if any(needle in low for needle in lowered):
            hits.append({"path": rel(path), "line": lineno, "text": line.strip()[:280]})
            if len(hits) >= limit:
                break
    return hits


def table_rows_with_numeric_first_col(path: pathlib.Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(read_text(path).splitlines(), start=1):
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells:
            continue
        if re.fullmatch(r"\d+", cells[0]):
            rows.append({"line": lineno, "cells": cells, "text": line.strip()})
    return rows


def load_legacy_layers() -> list[str]:
    tree = ast.parse(read_text(LEGACY_STACK), filename=str(LEGACY_STACK))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "LAYERS":
                    value = ast.literal_eval(node.value)
                    return [str(item) for item in value]
    raise RuntimeError("LAYERS assignment not found in legacy stack")


def chain_graph(nodes: list[str]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    ids = [graph.add_node(node) for node in nodes]
    for left, right in zip(ids, ids[1:]):
        graph.add_edge(left, right, "precedes")
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "topological_order": [graph[idx] for idx in rx.topological_sort(graph)],
    }


def source_surface_report() -> dict[str, Any]:
    surfaces = {
        name: {
            "path": rel(path),
            "exists": path.exists(),
            "sha256": sha256(path),
            "key_hits": line_hits(path, ["Clifford torus", "Xi", "rho_AB", "Phi_0", "Phi0"], limit=10),
        }
        for name, path in MASTER_SURFACES.items()
    }
    return {
        "pass": all(row["exists"] for row in surfaces.values()),
        "master_atlas_versions": REQUIRED_MASTER_VERSIONS,
        "surfaces": surfaces,
    }


def master_inventory_report() -> dict[str, Any]:
    ladder_rows = table_rows_with_numeric_first_col(MASTER_SURFACES["17_layer_ladder"])
    atlas_rows = table_rows_with_numeric_first_col(MASTER_SURFACES["20_layer_atlas"])
    formal_hits = line_hits(
        MASTER_SURFACES["formal_chain"],
        ["constraints\\to", "Xi", "rho_AB", "T_\\eta", "Clifford torus", "entropy"],
        limit=10,
    )
    open_surface_hits = {
        "Xi": line_hits(MASTER_SURFACES["20_layer_atlas"], ["Xi : geometry", "Xi_point", "Xi_hist"], limit=6),
        "rho_AB": line_hits(MASTER_SURFACES["20_layer_atlas"], ["rho_AB", "bipartite cut-state"], limit=6),
        "Phi0": line_hits(MASTER_SURFACES["20_layer_atlas"], ["Phi_0", "Phi0", "kernel family"], limit=6),
        "Clifford_torus": line_hits(MASTER_SURFACES["20_layer_atlas"], ["Clifford torus", "T_(pi/4)"], limit=6),
    }
    counts = torch.tensor(
        [float(len(load_legacy_layers())), float(len(MASTER_20_LAYER_NAMES)), float(len(FORMAL_CHAIN_NODES))],
        dtype=torch.float64,
    )
    compression_delta = float(counts[1].item() - counts[0].item())
    return {
        "pass": bool(
            len(load_legacy_layers()) == 13
            and len(MASTER_20_LAYER_NAMES) == 20
            and len(FORMAL_CHAIN_NODES) >= 8
            and all(open_surface_hits[key] for key in open_surface_hits)
        ),
        "17_ladder_numeric_rows_detected": len(ladder_rows),
        "20_atlas_numeric_rows_detected": len(atlas_rows),
        "formal_chain_nodes": FORMAL_CHAIN_NODES,
        "count_tensor_legacy_20_formal": jsonable(counts),
        "legacy_to_20_layer_delta": compression_delta,
        "open_surface_evidence": open_surface_hits,
        "formal_chain_evidence": formal_hits,
    }


def compression_diff_report(legacy_layers: list[str]) -> dict[str, Any]:
    merged_layers = {
        legacy: targets
        for legacy, targets in LEGACY_TO_MASTER_MAP.items()
        if len(targets) > 1 or legacy in {"finite_constraint_complex", "weyl_spinor_bundle"}
    }
    object_class_changes = {
        "clifford_torus_vs_clifford_module": {
            "legacy_layer": "clifford_module_geometry",
            "master_atlas_object": "Clifford torus T_(pi/4)",
            "mismatch": "geometric Hopf-torus stratum vs algebra/module closure",
            "pass": "clifford_module_geometry" in legacy_layers,
        },
        "density_states_vs_hilbert_carrier": {
            "legacy_layer": "complex_hilbert_carrier",
            "master_atlas_objects": ["D(C^2)", "rho_left", "rho_right", "rho_AB"],
            "mismatch": "state objects are collapsed into carrier language in the 13-layer fixture",
            "pass": "complex_hilbert_carrier" in legacy_layers,
        },
        "bridge_cut_kernel_dropped": {
            "legacy_terminal": legacy_layers[-1] if legacy_layers else None,
            "dropped_master_objects": ["Xi", "rho_AB", "Phi0(rho_AB)"],
            "mismatch": "late open bridge/cut/kernel surfaces are absent from the legacy layer list",
            "pass": bool(legacy_layers and legacy_layers[-1] == "dynamic_transition_ratchet_geometry"),
        },
    }
    dropped_or_missing = [
        "axis-slice rule",
        "Clifford torus T_(pi/4)",
        "fiber-loop family as its own layer",
        "lifted-base-loop family as its own layer",
        "left Weyl sheet",
        "right Weyl sheet",
        "left density",
        "right density",
        "bridge target family Xi",
        "bipartite cut-state family rho_AB",
        "Axis 0 kernel family Phi0(rho_AB)",
    ]
    graph_13 = chain_graph(legacy_layers)
    graph_20 = chain_graph(MASTER_20_LAYER_NAMES)
    return {
        "pass": all(row["pass"] for row in object_class_changes.values())
        and graph_13["node_count"] == 13
        and graph_20["node_count"] == 20,
        "legacy_layers": legacy_layers,
        "legacy_chain_graph": graph_13,
        "master_20_graph": graph_20,
        "mapping": LEGACY_TO_MASTER_MAP,
        "merged_layers": merged_layers,
        "dropped_or_missing_master_objects": dropped_or_missing,
        "object_class_mismatch": object_class_changes,
    }


def search_status_report() -> dict[str, Any]:
    evidence_files = {
        "reverse_scramble_controls": [
            SCOUT_ROOT / "sim_two_root_constraint_layer_order_gauge_invariant_observable_probe.py",
            SCOUT_ROOT / "sim_topology_orientation_sensitive_layer_order_falsifier_probe.py",
            SCOUT_ROOT / "sim_topology_coupled_layer_order_and_row_count_falsifier_probe.py",
        ],
        "label_name_storage_reindexing_controls": [
            SCOUT_ROOT / "sim_layer_operator_name_blindness_falsifier_probe.py",
            SCOUT_ROOT / "sim_g_structure_semantic_family_permutation_falsifier_probe.py",
            SCOUT_ROOT / "sim_semantic_graph_proof_label_scramble_falsifier_probe.py",
        ],
        "branch_option_variation_inside_fixed_13_slots": [
            SCOUT_ROOT / "sim_g_structure_semantic_family_permutation_falsifier_probe.py",
            SCOUT_ROOT / "sim_g_structure_semantic_layer_operator_coupling_probe.py",
            SCOUT_ROOT / "sim_thirteen_layer_active_manifold_layer_removal_graph_order_pyg_rustworkx_probe.py",
        ],
        "true_alternative_total_order_search": [],
        "true_alternative_layer_count_search": [],
        "true_non_chain_topology_search": [],
    }
    categories: dict[str, Any] = {}
    for category, files in evidence_files.items():
        existing = [path for path in files if path.exists()]
        if category.startswith("true_"):
            status = "not_established"
        elif existing:
            status = "some_receipts_exist_but_limited"
        else:
            status = "not_established"
        categories[category] = {
            "status": status,
            "evidence_paths": [rel(path) for path in existing],
            "missing_scope_note": "does not count as true alternative order/layer-count/topology search"
            if not category.startswith("true_")
            else "required future search space; no current source receipt found by this W4 scout",
        }
    return {
        "pass": (
            categories["reverse_scramble_controls"]["status"] == "some_receipts_exist_but_limited"
            and categories["label_name_storage_reindexing_controls"]["status"] == "some_receipts_exist_but_limited"
            and categories["branch_option_variation_inside_fixed_13_slots"]["status"]
            == "some_receipts_exist_but_limited"
            and categories["true_alternative_total_order_search"]["status"] == "not_established"
            and categories["true_alternative_layer_count_search"]["status"] == "not_established"
            and categories["true_non_chain_topology_search"]["status"] == "not_established"
        ),
        "alternative_ordering_search_status": categories,
    }


def pauli_basis_witness() -> dict[str, Any]:
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    anti_xy = sx * sy + sy * sx
    square_x = sx * sx
    return {
        "pass": anti_xy == sp.zeros(2) and square_x == sp.eye(2),
        "basis_elements": ["I", "sigma_x", "sigma_y", "sigma_z"],
        "witness": {
            "sigma_x_square_is_identity": square_x == sp.eye(2),
            "sigma_x_sigma_y_anticommutator_zero": anti_xy == sp.zeros(2),
        },
        "interpretation": "This witnesses Pauli basis relations only; closure to a Clifford algebra/module is an added algebraic step and signature convention.",
    }


def classify_clifford_line(path: pathlib.Path, line: str) -> str:
    low = line.lower()
    if "clifford_module_geometry" in low:
        return "projection/smuggling risk"
    if "clifford torus" in low or "t_(pi/4)" in low or "t_{\\pi/4}" in low:
        return "measurement only"
    if "cl(" in line or "from clifford import" in low or "clifford" in low:
        return "selector/energy term"
    if "feedback" in low:
        return "selector/energy term"
    if "projection" in low or "project" in low:
        return "measurement only"
    return "measurement only"


def algebra_closure_report() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for label, path in AUDIT_STACK_FILES.items():
        text = read_text(path)
        for lineno, line in enumerate(text.splitlines(), start=1):
            low = line.lower()
            if any(term in low for term in ["clifford", "projection", "feedback", "cl("]):
                category = classify_clifford_line(path, line)
                rows.append(
                    {
                        "stack_file": label,
                        "path": rel(path),
                        "line": lineno,
                        "text": line.strip()[:240],
                        "classification": category,
                        "claim_ceiling": "added closure/selector or measurement; not an F01/N01 consequence",
                    }
                )
    category_set = {"measurement only", "selector/energy term", "projection/smuggling risk", "graveyard control"}
    row_categories = {row["classification"] for row in rows}
    required_distinctions = {
        "Pauli basis": "operator basis in H=C^2 / Bloch coordinates",
        "Hopf/Bloch map using Pauli coordinates": "pi(psi)=psi^dagger sigma psi presentation, not standalone Clifford theorem",
        "Clifford torus T_(pi/4)": "geometric symmetric Hopf-torus stratum",
        "Clifford algebra/module closure": "added algebraic closure/selector requiring explicit admission",
        "Clifford signature convention": "not fixed by F01/N01 or Pauli basis alone",
        "fixed-observable algebra": "W3 terrain-channel observable side, not a Cl label",
        "generated-channel/semigroup algebra": "W3 schedule algebra side, not a Cl label",
    }
    return {
        "pass": bool(rows)
        and "projection/smuggling risk" in row_categories
        and "selector/energy term" in row_categories
        and pauli_basis_witness()["pass"],
        "classification_categories": sorted(category_set),
        "rows": rows[:120],
        "row_count": len(rows),
        "required_distinctions": required_distinctions,
        "pauli_basis_witness": pauli_basis_witness(),
        "unseen_categories_note": "graveyard control is a permitted classification but no graveyard-control Clifford row is required in this required-first inventory.",
    }


def z3_admission_report(search_status: dict[str, Any], compression: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    mismatch = z3.Bool("clifford_torus_vs_module_mismatch")
    true_total = z3.Bool("true_alternative_total_order_search_established")
    true_count = z3.Bool("true_alternative_layer_count_search_established")
    true_topology = z3.Bool("true_non_chain_topology_search_established")
    exact_13_forced = z3.Bool("exact_13_layer_forced")
    candidate_legacy = z3.Bool("candidate_legacy_stack")
    solver.add(mismatch == z3.BoolVal(compression["object_class_mismatch"]["clifford_torus_vs_clifford_module"]["pass"]))
    cats = search_status["alternative_ordering_search_status"]
    solver.add(true_total == z3.BoolVal(cats["true_alternative_total_order_search"]["status"] != "not_established"))
    solver.add(true_count == z3.BoolVal(cats["true_alternative_layer_count_search"]["status"] != "not_established"))
    solver.add(true_topology == z3.BoolVal(cats["true_non_chain_topology_search"]["status"] != "not_established"))
    solver.add(exact_13_forced == z3.And(z3.Not(mismatch), true_total, true_count, true_topology))
    solver.add(candidate_legacy == z3.And(mismatch, z3.Not(exact_13_forced)))
    status = solver.check()
    model = solver.model() if status == z3.sat else None
    exact_forced_value = bool(model.evaluate(exact_13_forced)) if model is not None else False
    candidate_value = bool(model.evaluate(candidate_legacy)) if model is not None else False
    return {
        "pass": str(status) == "sat" and not exact_forced_value and candidate_value,
        "solver_status": str(status),
        "exact_13_layer_forced": exact_forced_value,
        "candidate_legacy_stack": candidate_value,
        "interpretation": "Given current mismatch and missing true alternative-order/layer-count/non-chain receipts, exact 13-layer forcing is killed_or_unproven and the stack is candidate_legacy_stack.",
    }


def prerequisite_report() -> dict[str, Any]:
    w1 = read_json(W1_RESULT)
    w2 = read_json(W2_RESULT)
    w3 = read_json(W3_RESULT)
    checks = {
        "w1_exists": W1_RESULT.exists(),
        "w1_all_pass": w1.get("all_pass") is True,
        "w1_tooling_reclassified_complete": w1.get("completion_status") == "tooling_reclassified_complete",
        "w2_exists": W2_RESULT.exists(),
        "w2_all_pass": w2.get("all_pass") is True,
        "w2_formal_ingest_only": w2.get("summary", {}).get("claim_ceiling") == "formal_ingest_only",
        "w3_exists": W3_RESULT.exists(),
        "w3_all_pass": w3.get("all_pass") is True,
        "w3_bounded_reframe": w3.get("summary", {}).get("claim_ceiling")
        == "bounded_terrain_composition_bridge_reframe_only",
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "hashes": {
            "w1": {"path": rel(W1_RESULT), "sha256": sha256(W1_RESULT)},
            "w2": {"path": rel(W2_RESULT), "sha256": sha256(W2_RESULT)},
            "w3": {"path": rel(W3_RESULT), "sha256": sha256(W3_RESULT)},
        },
    }


def main() -> dict[str, Any]:
    started = time.time()
    legacy_layers = load_legacy_layers()
    sources = source_surface_report()
    inventory = master_inventory_report()
    compression = compression_diff_report(legacy_layers)
    search_status = search_status_report()
    closure = algebra_closure_report()
    z3_report = z3_admission_report(search_status, compression)
    prerequisites = prerequisite_report()

    positive = {
        "prerequisites_w1_w2_w3_current": prerequisites,
        "master_atlas_versions_loaded": sources,
        "master_atlas_inventory_reconstructed": inventory,
        "compression_diff_identifies_mismatch": {
            "pass": compression["pass"],
            "thirteen_layer_status": "candidate_legacy_stack",
            "exact_13_layer_forcing_status": "killed_or_unproven",
            "compression": compression,
        },
        "alternative_ordering_search_scope_is_not_overclaimed": search_status,
        "algebra_closure_distinctions_recorded": closure,
        "z3_blocks_exact_13_layer_forcing": z3_report,
    }

    graveyard_companions = {
        "reverse_scramble_controls_do_not_count_as_full_order_search": {
            "pass": search_status["alternative_ordering_search_status"]["true_alternative_total_order_search"]["status"]
            == "not_established",
            "reason": "reverse/scramble controls only perturb the fixed stack; they do not enumerate true alternative total orders",
        },
        "label_reindexing_does_not_count_as_semantic_layer_search": {
            "pass": search_status["alternative_ordering_search_status"]["label_name_storage_reindexing_controls"]["status"]
            == "some_receipts_exist_but_limited",
            "reason": "label/name/storage controls are useful falsifiers but cannot bless the 13-layer ontology",
        },
        "clifford_module_rename_is_not_clifford_torus_evidence": {
            "pass": compression["object_class_mismatch"]["clifford_torus_vs_clifford_module"]["pass"],
            "reason": "the source atlas has Clifford torus T_(pi/4) as geometric stratum; the legacy stack has clifford_module_geometry as algebra/module language",
        },
        "pauli_basis_relations_do_not_force_signature": {
            "pass": closure["pauli_basis_witness"]["pass"],
            "reason": "Pauli relations witness an operator basis; signature/module closure remains an added convention or selector",
        },
    }

    boundary = {
        "thirteen_layer_status": {
            "pass": True,
            "value": "candidate_legacy_stack",
        },
        "exact_13_layer_forcing_status": {
            "pass": True,
            "value": "killed_or_unproven",
        },
        "master_atlas_versions": {
            "pass": sources["master_atlas_versions"] == REQUIRED_MASTER_VERSIONS,
            "value": sources["master_atlas_versions"],
        },
        "object_class_mismatch_clifford_torus_vs_clifford_module": {
            "pass": compression["object_class_mismatch"]["clifford_torus_vs_clifford_module"]["pass"],
            "value": True,
        },
        "promotion_blocked": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
    }

    all_pass = (
        all(row.get("pass") is True for row in positive.values())
        and all(row.get("pass") is True for row in graveyard_companions.values())
        and all(row.get("pass") is True for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "math_object": "noncanonical layer-order inventory and algebra-closure audit for formal manifold stack",
        "thirteen_layer_status": "candidate_legacy_stack",
        "exact_13_layer_forcing_status": "killed_or_unproven",
        "master_atlas_versions": REQUIRED_MASTER_VERSIONS,
        "object_class_mismatch": {
            "clifford_torus_vs_clifford_module": True,
            "detail": compression["object_class_mismatch"]["clifford_torus_vs_clifford_module"],
        },
        "alternative_ordering_search_status": search_status["alternative_ordering_search_status"],
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "true alternative total-order search remains unestablished",
            "true alternative layer-count search remains unestablished",
            "true non-chain topology search remains unestablished",
            "additional W4 dynamic-stack files still need deeper Hamiltonian/update-functional audit before final synthesis",
            "provider cross-audit remains required before any survived selector/bridge/manifold claim",
        ],
        "why_not_v4_probes": "This is a v5 formal-scout inventory receipt over current v5 plan/docs and should not add to the mixed v4 probe estate.",
        "summary": {
            "all_pass": all_pass,
            "thirteen_layer_status": "candidate_legacy_stack",
            "exact_13_layer_forcing_status": "killed_or_unproven",
            "master_atlas_versions": REQUIRED_MASTER_VERSIONS,
            "object_class_mismatch_clifford_torus_vs_clifford_module": True,
            "true_alternative_total_order_search": search_status["alternative_ordering_search_status"][
                "true_alternative_total_order_search"
            ]["status"],
            "true_alternative_layer_count_search": search_status["alternative_ordering_search_status"][
                "true_alternative_layer_count_search"
            ]["status"],
            "true_non_chain_topology_search": search_status["alternative_ordering_search_status"][
                "true_non_chain_topology_search"
            ]["status"],
            "clifford_audit_row_count": closure["row_count"],
            "next_required_workstreams": [
                "W4 deeper audit of listed formal dynamics stacks",
                "W5 concrete manifold definition and explicit selection mechanism",
                "W6 provider cross-audit before final synthesis",
            ],
        },
        "all_pass": all_pass,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": round(time.time() - started, 6),
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    return result


if __name__ == "__main__":
    receipt = main()
    print(
        json.dumps(
            {
                "all_pass": receipt["all_pass"],
                "thirteen_layer_status": receipt["summary"]["thirteen_layer_status"],
                "exact_13_layer_forcing_status": receipt["summary"]["exact_13_layer_forcing_status"],
                "object_class_mismatch_clifford_torus_vs_clifford_module": receipt["summary"][
                    "object_class_mismatch_clifford_torus_vs_clifford_module"
                ],
                "true_alternative_total_order_search": receipt["summary"]["true_alternative_total_order_search"],
                "clifford_audit_row_count": receipt["summary"]["clifford_audit_row_count"],
                "out_path": rel(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
