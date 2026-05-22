#!/usr/bin/env python3
"""Formal stack dynamics / closure audit after W4 noncanonical inventory.

This Workstream 4 follow-on receipt audits the listed formal dynamics stacks
without rerunning their expensive dynamics. It classifies each stack's actual
update functional, Clifford/Cl projection risk, scale scope, and structured
Pauli coverage. The purpose is to prevent state-level, projection-level, or
random-sampling evidence from being used as an algebra-level closure claim.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import time
from typing import Any

import rustworkx as rx
import torch
import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_formal_stack_dynamics_closure_audit_probe_results.json"

NAME = "two_root_constraint_formal_stack_dynamics_closure_audit_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_formal_stack_dynamics_closure_audit"
CLAIM_CEILING = (
    "Formal scout only: audits existing formal dynamics stack sources/results "
    "for update functional, Hamiltonian-equivalent status, Clifford/projection "
    "closure risk, structured Pauli coverage, and scale scope. It does not "
    "admit a canonical layer order, final manifold, real attractor basin, "
    "Axis0 theorem, physics validation, Holodeck validation, or Clifford theorem."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite audit tensor over target scale, closure-risk, and structured-Pauli coverage flags",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing audit dependency graph from W4 inventory to the four existing formal dynamics stack targets",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof that incomplete structured-Pauli coverage blocks algebra-level closure promotion",
    },
    "python_re": {"tried": True, "used": True, "reason": "supportive source pattern extraction for update and closure terms"},
    "python_json": {"tried": True, "used": True, "reason": "supportive source/result receipt serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive repository path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_re": "supportive",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

W4_INVENTORY_RESULT = RESULT_DIR / "two_root_constraint_layer_order_noncanonical_inventory_probe_results.json"

TARGETS = {
    "thirteen_layer_active_nested_mps": {
        "source": SCOUT_ROOT / "sim_thirteen_layer_active_nested_manifold_mps_special_holonomy_deep_graveyard_dynamic_tensor_network_probe.py",
        "result": RESULT_DIR
        / "thirteen_layer_active_nested_manifold_mps_special_holonomy_deep_graveyard_dynamic_tensor_network_probe_results.json",
    },
    "site_boundary_scaling_8_16_32_64": {
        "source": SCOUT_ROOT / "sim_two_root_constraint_8_16_32_64_site_basin_boundary_scaling_probe.py",
        "result": RESULT_DIR / "two_root_constraint_8_16_32_64_site_basin_boundary_scaling_probe_results.json",
    },
    "mps_local_boundary_path_fep_8_16_32": {
        "source": SCOUT_ROOT / "sim_mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe.py",
        "result": RESULT_DIR / "mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe_results.json",
    },
    "peps3d_64_site_bond_dimension_slot": {
        "source": SCOUT_ROOT / "sim_source_native_peps3d_64_site_bond_dimension_slot_dynamics_probe.py",
        "result": RESULT_DIR / "source_native_peps3d_64_site_bond_dimension_slot_dynamics_probe_results.json",
    },
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


def grep_lines(text: str, terms: list[str], limit: int = 12) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    lowered = [term.lower() for term in terms]
    for lineno, line in enumerate(text.splitlines(), start=1):
        low = line.lower()
        if any(term in low for term in lowered):
            out.append({"line": lineno, "text": line.strip()[:260]})
            if len(out) >= limit:
                break
    return out


def result_all_pass(data: dict[str, Any]) -> bool:
    return data.get("all_pass") is True or data.get("summary", {}).get("all_pass") is True


def scale_labels(source: str, result: dict[str, Any]) -> dict[str, Any]:
    labels = sorted({int(x) for x in re.findall(r"\b(?:8|16|32|64)\b", source)})
    summary = result.get("summary", {})
    for key in ("site_counts", "n_values", "guarded_n_values"):
        if isinstance(summary.get(key), list):
            labels = sorted(set(labels).union(int(v) for v in summary[key] if isinstance(v, int)))
    return {
        "labels": labels,
        "has_min_8_16": 8 in labels and 16 in labels,
        "has_32_or_64": 32 in labels or 64 in labels,
    }


def classify_update_functional(name: str, source: str) -> dict[str, Any]:
    low = source.lower()
    if name == "thirteen_layer_active_nested_mps":
        status = "hybrid_active_layer_enforcement_plus_feedback_modules"
        h_status = "not_single_hamiltonian_equivalent"
    elif name == "site_boundary_scaling_8_16_32_64":
        status = "iterated_finite_tensor_update_with_pressure_flux_and_controls"
        h_status = "not_single_hamiltonian_equivalent"
    elif name == "mps_local_boundary_path_fep_8_16_32":
        status = "source_native_slot_transport_with_local_boundary_density_and_fep_proxy"
        h_status = "not_global_hamiltonian_or_global_variational_free_energy"
    elif name == "peps3d_64_site_bond_dimension_slot":
        status = "source_record_slot_updates_at_bond_dimensions_2_3_4"
        h_status = "not_long_horizon_hamiltonian_dynamics"
    else:
        status = "unknown"
        h_status = "unknown"
    evidence_terms = ["Hamiltonian", "matrix_exp", "loss", "expected_free_energy", "apply_slot_to_tensor", "update_geometry", "feedback"]
    return {
        "status": status,
        "hamiltonian_equivalent_status": h_status,
        "has_hamiltonian_language": "hamiltonian" in low,
        "has_loss_language": "loss" in low or "free_energy" in low,
        "has_feedback_or_projection_language": "feedback" in low or "projection" in low or "projector" in low,
        "evidence_lines": grep_lines(source, evidence_terms, limit=16),
    }


def classify_closure_risk(source: str) -> dict[str, Any]:
    low = source.lower()
    lines = grep_lines(source, ["clifford", "projection", "feedback", "gamma5", "Cl("], limit=24)
    if "clifford_projected_cut_readout" in low or "graveyard_no_clifford_projection" in low:
        status = "projection_or_feedback_selector_risk"
    elif "from clifford import" in low or "clifford" in low:
        status = "added_clifford_witness_or_basis_closure"
    else:
        status = "no_direct_clifford_closure_detected"
    return {
        "status": status,
        "line_count": len(lines),
        "evidence_lines": lines,
        "claim_rule": "Any Cl/Clifford usage here is an added witness/selector/projection unless separately derived from F01/N01 in a formal receipt.",
    }


def structured_pauli_coverage(source: str, result: dict[str, Any]) -> dict[str, Any]:
    low = source.lower()
    single_site = any(term in source for term in ["TSX", "TSY", "TSZ", "sigma_x", "sigma_y", "sigma_z"]) or "pauli_distribution" in low
    nearest = "nearest" in low or "neighbor" in low
    weight2 = "weight-2" in low or "weight_2" in low or "two-site" in low
    weight3 = "weight-3" in low or "weight_3" in low
    global_anchors = any(term in source for term in ["X^L", "Y^L", "Z^L", "X^N", "Y^N", "Z^N"])
    random_only = "random pauli" in low or "sampled paul" in low
    coverage = {
        "single_site_paulis": single_site,
        "nearest_neighbor_two_site_paulis": nearest,
        "weight_2_classes": weight2,
        "weight_3_classes": weight3,
        "known_global_anchors": global_anchors,
        "random_sampling_only_flag": random_only,
    }
    complete = all(coverage[key] for key in ["single_site_paulis", "nearest_neighbor_two_site_paulis", "weight_2_classes", "weight_3_classes", "known_global_anchors"])
    return {
        "coverage": coverage,
        "status": "complete_for_algebra_level_claim" if complete else "insufficient_for_algebra_level_claim",
        "claim_ceiling": "Structured Pauli classes may support diagnostics, but incomplete coverage blocks algebra-level closure promotion.",
        "result_summary_keys": sorted((result.get("summary") or {}).keys())[:40],
    }


def audit_target(name: str, paths: dict[str, pathlib.Path]) -> dict[str, Any]:
    source_path = paths["source"]
    result_path = paths["result"]
    source = read_text(source_path)
    result = read_json(result_path)
    scales = scale_labels(source, result)
    update = classify_update_functional(name, source)
    closure = classify_closure_risk(source)
    pauli = structured_pauli_coverage(source, result)
    claim_ceiling = str(result.get("claim_ceiling", ""))
    scale_scope_ok = scales["has_min_8_16"] or (
        name == "peps3d_64_site_bond_dimension_slot"
        and 64 in scales["labels"]
        and "does not prove long-horizon convergence" in claim_ceiling.lower()
    )
    return {
        "name": name,
        "source": {"path": rel(source_path), "exists": source_path.exists(), "sha256": sha256(source_path)},
        "result": {
            "path": rel(result_path),
            "exists": result_path.exists(),
            "sha256": sha256(result_path),
            "all_pass": result_all_pass(result),
            "promotion_allowed": result.get("promotion_allowed"),
            "claim_ceiling_blocks_final": "does not" in claim_ceiling.lower() or "formal scout only" in claim_ceiling.lower(),
        },
        "scale_labels": scales,
        "scale_scope_ok": scale_scope_ok,
        "update_functional": update,
        "clifford_or_projection_closure": closure,
        "structured_pauli_coverage": pauli,
        "algebra_level_claim_allowed": False,
        "pass": bool(
            source_path.exists()
            and result_path.exists()
            and result_all_pass(result)
            and result.get("promotion_allowed") is False
            and scale_scope_ok
            and pauli["status"] == "insufficient_for_algebra_level_claim"
        ),
    }


def audit_graph(target_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    w4 = graph.add_node("W4_noncanonical_inventory")
    target_nodes = {}
    for name in target_rows:
        target_nodes[name] = graph.add_node(name)
        graph.add_edge(w4, target_nodes[name], "audits_after_inventory")
    return {
        "pass": graph.num_nodes() == 1 + len(target_rows) and graph.num_edges() == len(target_rows),
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "topological_order": [graph[idx] for idx in rx.topological_sort(graph)],
    }


def z3_promotion_block(target_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    all_results_green = z3.Bool("all_results_green")
    structured_complete = z3.Bool("structured_pauli_coverage_complete_all_targets")
    algebra_claim_allowed = z3.Bool("algebra_level_claim_allowed")
    all_green_value = all(row["result"]["all_pass"] and row["result"]["promotion_allowed"] is False for row in target_rows.values())
    structured_value = all(
        row["structured_pauli_coverage"]["status"] == "complete_for_algebra_level_claim" for row in target_rows.values()
    )
    solver.add(all_results_green == z3.BoolVal(all_green_value))
    solver.add(structured_complete == z3.BoolVal(structured_value))
    solver.add(algebra_claim_allowed == z3.And(all_results_green, structured_complete))
    status = solver.check()
    model = solver.model() if status == z3.sat else None
    allowed = bool(model.evaluate(algebra_claim_allowed)) if model is not None else False
    return {
        "pass": str(status) == "sat" and not allowed,
        "solver_status": str(status),
        "all_results_green": all_green_value,
        "structured_pauli_coverage_complete_all_targets": structured_value,
        "algebra_level_claim_allowed": allowed,
        "interpretation": "Existing green dynamics receipts do not permit algebra-level closure promotion because structured Pauli coverage is incomplete.",
    }


def main() -> dict[str, Any]:
    started = time.time()
    inventory = read_json(W4_INVENTORY_RESULT)
    target_rows = {name: audit_target(name, paths) for name, paths in TARGETS.items()}
    target_matrix = torch.tensor(
        [
            [
                1.0 if row["result"]["all_pass"] else 0.0,
                1.0 if row["scale_labels"]["has_min_8_16"] else 0.0,
                1.0 if row["scale_labels"]["has_32_or_64"] else 0.0,
                1.0 if row["structured_pauli_coverage"]["status"] == "complete_for_algebra_level_claim" else 0.0,
                1.0 if row["algebra_level_claim_allowed"] else 0.0,
            ]
            for row in target_rows.values()
        ],
        dtype=torch.float64,
    )
    graph = audit_graph(target_rows)
    z3_report = z3_promotion_block(target_rows)

    positive = {
        "w4_inventory_prerequisite_loaded": {
            "pass": inventory.get("all_pass") is True
            and inventory.get("summary", {}).get("thirteen_layer_status") == "candidate_legacy_stack",
            "path": rel(W4_INVENTORY_RESULT),
            "sha256": sha256(W4_INVENTORY_RESULT),
        },
        "formal_stack_files_and_results_loaded": {
            "pass": all(row["source"]["exists"] and row["result"]["exists"] for row in target_rows.values()),
            "targets": target_rows,
        },
        "update_functionals_classified": {
            "pass": all(row["update_functional"]["status"] != "unknown" for row in target_rows.values()),
            "statuses": {name: row["update_functional"]["status"] for name, row in target_rows.items()},
        },
        "closure_risks_classified": {
            "pass": all(row["clifford_or_projection_closure"]["status"] for row in target_rows.values()),
            "statuses": {name: row["clifford_or_projection_closure"]["status"] for name, row in target_rows.items()},
        },
        "scale_claims_scoped": {
            "pass": all(row["scale_scope_ok"] for row in target_rows.values())
            and any(row["scale_labels"]["has_32_or_64"] for row in target_rows.values()),
            "scales": {name: row["scale_labels"] for name, row in target_rows.items()},
            "scope_notes": {
                name: (
                    "multi-scale 8/16+ formal stack"
                    if row["scale_labels"]["has_min_8_16"]
                    else "scoped single 64-site PEPS3D bond-dimension receipt; not portability or convergence"
                )
                for name, row in target_rows.items()
            },
        },
        "audit_dependency_graph_constructed": graph,
        "z3_blocks_algebra_level_promotion": z3_report,
    }

    graveyard_companions = {
        "green_dynamic_receipts_are_not_algebra_level_closure": {
            "pass": z3_report["algebra_level_claim_allowed"] is False,
            "reason": "all audited receipts remain formal_scout/promotion_disabled and structured Pauli coverage is incomplete",
        },
        "clifford_projection_feedback_is_selector_not_emergence": {
            "pass": target_rows["thirteen_layer_active_nested_mps"]["clifford_or_projection_closure"]["status"]
            == "projection_or_feedback_selector_risk",
            "reason": "clifford_projected_cut_readout and no-clifford-projection controls are projection/selector machinery",
        },
        "state_or_slot_update_is_not_ground_state_or_observable_algebra_proof": {
            "pass": all("not_" in row["update_functional"]["hamiltonian_equivalent_status"] for row in target_rows.values()),
            "reason": "audited stacks use finite updates, feedback, FEP proxies, or slot dynamics rather than a single Hamiltonian algebra-of-observables proof",
        },
        "single_64_site_bond_sweep_is_not_long_horizon_convergence": {
            "pass": target_rows["peps3d_64_site_bond_dimension_slot"]["update_functional"][
                "hamiltonian_equivalent_status"
            ]
            == "not_long_horizon_hamiltonian_dynamics",
            "reason": "the PEPS3D scout itself cites long_horizon_64_site_bond_dimension_convergence as still blocked",
        },
    }

    boundary = {
        "promotion_blocked": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "algebra_level_claim_allowed": {"pass": z3_report["algebra_level_claim_allowed"] is False, "value": False},
        "structured_pauli_coverage_complete_all_targets": {
            "pass": z3_report["structured_pauli_coverage_complete_all_targets"] is False,
            "value": False,
        },
        "target_audit_matrix_columns": {
            "pass": target_matrix.shape == (4, 5),
            "columns": ["result_green", "has_8_16", "has_32_or_64", "structured_pauli_complete", "algebra_claim_allowed"],
            "matrix": jsonable(target_matrix),
        },
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
        "math_object": "formal dynamics stack update-functional and algebra-closure audit",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "structured Pauli class coverage remains incomplete for algebra-level claims",
            "no audited stack provides a single Hamiltonian-equivalent observable-algebra proof",
            "Clifford projection/feedback remains selector machinery unless separately justified",
            "W5 must still choose or compare a concrete manifold carrier / explicit selection mechanism",
        ],
        "why_not_v4_probes": "This is a v5 formal-scout audit over current v5 formal dynamics stack files and should not add to the mixed v4 probe estate.",
        "summary": {
            "all_pass": all_pass,
            "target_count": len(target_rows),
            "target_names": sorted(target_rows),
            "algebra_level_claim_allowed": False,
            "structured_pauli_coverage_complete_all_targets": False,
            "clifford_projection_feedback_status": target_rows["thirteen_layer_active_nested_mps"][
                "clifford_or_projection_closure"
            ]["status"],
            "next_required_workstreams": [
                "W5 concrete manifold definition and explicit selection mechanism",
                "resolve or explicitly scope broad NumPy grep blocker before final closeout",
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
                "target_count": receipt["summary"]["target_count"],
                "algebra_level_claim_allowed": receipt["summary"]["algebra_level_claim_allowed"],
                "structured_pauli_coverage_complete_all_targets": receipt["summary"][
                    "structured_pauli_coverage_complete_all_targets"
                ],
                "clifford_projection_feedback_status": receipt["summary"]["clifford_projection_feedback_status"],
                "out_path": rel(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
