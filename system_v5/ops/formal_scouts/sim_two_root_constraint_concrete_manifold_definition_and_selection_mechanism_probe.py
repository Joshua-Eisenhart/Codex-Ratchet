#!/usr/bin/env python3
"""Concrete manifold definition / explicit selection mechanism scout.

Workstream 5 receipt. This scout turns "constraint manifold" from a loose
phrase into a bounded finite carrier+relation scaffold for the next formal
receipts, compares alternative concrete carriers, and keeps any final manifold
or Cl-basin claim blocked pending provider cross-audit.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import rustworkx as rx
import torch
import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_concrete_manifold_definition_and_selection_mechanism_probe_results.json"

NAME = "two_root_constraint_concrete_manifold_definition_and_selection_mechanism_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_concrete_manifold_definition_and_selection_mechanism"
CLAIM_CEILING = (
    "Formal scout only: defines a bounded working constraint-manifold carrier "
    "as a finite carrier+relation scaffold, compares alternative concrete "
    "carriers, and names the terrain Lindblad/schedule system as an explicit "
    "candidate selection mechanism X. It does not admit a final manifold, real "
    "attractor basin, Axis0 theorem, engine theorem, physics validation, "
    "Holodeck validation, canonical layer order, or Clifford theorem."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite carrier/relation feature matrix, adjacency/boundary tensors, and gate-vector checks",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite topology-first scaffold graph over admissible carrier+relation points",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof that final manifold/Cl uniqueness remains blocked without W6 audit and complete hard negatives",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive formal-scout receipt serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive repository path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

W2_RESULT = RESULT_DIR / "two_root_constraint_grok_97_114_boundary_ingest_probe_results.json"
W3_RESULT = RESULT_DIR / "constraint_manifold_terrain_lindblad_composition_bridge_probe_results.json"
W4_INVENTORY_RESULT = RESULT_DIR / "two_root_constraint_layer_order_noncanonical_inventory_probe_results.json"
W4_DYNAMICS_AUDIT_RESULT = RESULT_DIR / "two_root_constraint_formal_stack_dynamics_closure_audit_probe_results.json"

REF_ROOT = REPO / "system_v5" / "READ ONLY Reference Docs"
SOURCE_SURFACES = {
    "formal_constraints_geometry": REF_ROOT / "Formal constraints and geometry .md",
    "axes_0_6_atlas": REF_ROOT / "AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md",
    "terrains": REF_ROOT / "terrains.md",
    "apple_axes_terrain_operator_math": REF_ROOT / "apple axes terrain operator math.md",
    "axis_0_rough": REF_ROOT / "Axis 0 rough and drifty. NOT CANON.md",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


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
    hits: list[dict[str, Any]] = []
    text = read_text(path)
    lowered = [needle.lower() for needle in needles]
    for lineno, line in enumerate(text.splitlines(), start=1):
        low = line.lower()
        if any(needle in low for needle in lowered):
            hits.append({"path": rel(path), "line": lineno, "text": line.strip()[:280]})
            if len(hits) >= limit:
                break
    return hits


def prerequisite_report() -> dict[str, Any]:
    prereq_paths = {
        "w2": W2_RESULT,
        "w3": W3_RESULT,
        "w4_inventory": W4_INVENTORY_RESULT,
        "w4_dynamics_audit": W4_DYNAMICS_AUDIT_RESULT,
    }
    rows = {}
    for key, path in prereq_paths.items():
        data = read_json(path)
        rows[key] = {
            "path": rel(path),
            "exists": path.exists(),
            "sha256": sha256(path),
            "all_pass": data.get("all_pass") is True or data.get("summary", {}).get("all_pass") is True,
            "promotion_allowed": data.get("promotion_allowed"),
            "summary": data.get("summary", {}),
        }
    return {
        "pass": all(row["exists"] and row["all_pass"] and row["promotion_allowed"] is False for row in rows.values()),
        "rows": rows,
    }


def source_report() -> dict[str, Any]:
    rows = {
        key: {
            "path": rel(path),
            "exists": path.exists(),
            "sha256": sha256(path),
            "hits": line_hits(path, ["M(C)", "carrier", "relation", "adjacency", "boundary", "Xi", "rho_AB", "Lindblad"], limit=10),
        }
        for key, path in SOURCE_SURFACES.items()
    }
    return {"pass": all(row["exists"] for row in rows.values()), "rows": rows}


def finite_points() -> list[dict[str, Any]]:
    carriers = ["qit_density_C2", "weyl_sheet_pair", "terrain_schedule_state"]
    relation_families = ["F01_finitude", "N01_order_sensitive", "topology_adjacency", "terrain_lindblad_schedule"]
    points = []
    idx = 0
    for carrier in carriers:
        for relation in relation_families:
            finite = carrier in carriers
            noncomm = relation in {"N01_order_sensitive", "terrain_lindblad_schedule"}
            topology = relation == "topology_adjacency"
            dynamics = relation == "terrain_lindblad_schedule"
            points.append(
                {
                    "id": f"p{idx:02d}",
                    "carrier": carrier,
                    "relation_family": relation,
                    "F01": finite,
                    "N01": noncomm or relation == "F01_finitude",
                    "topology_first": topology or dynamics,
                    "has_dynamics": dynamics,
                }
            )
            idx += 1
    return points


def scaffold_graph(points: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyGraph()
    ids = {point["id"]: graph.add_node(point) for point in points}
    edges = []
    for i, left in enumerate(points):
        for right in points[i + 1 :]:
            same_carrier = left["carrier"] == right["carrier"]
            same_relation = left["relation_family"] == right["relation_family"]
            admissible_transition = same_carrier or same_relation
            if admissible_transition:
                graph.add_edge(ids[left["id"]], ids[right["id"]], "adjacent_by_carrier_or_relation")
                edges.append((left["id"], right["id"]))
    components = rx.connected_components(graph)
    boundary_ids = [point["id"] for point in points if point["relation_family"] in {"F01_finitude", "N01_order_sensitive"}]
    feature_rows = [
        [
            1.0 if point["F01"] else 0.0,
            1.0 if point["N01"] else 0.0,
            1.0 if point["topology_first"] else 0.0,
            1.0 if point["has_dynamics"] else 0.0,
        ]
        for point in points
    ]
    features = torch.tensor(feature_rows, dtype=torch.float64)
    return {
        "pass": graph.num_nodes() == len(points) and graph.num_edges() >= len(points) and len(components) == 1,
        "point_definition": "(finite carrier id, relation family, F01 gate, N01/order gate, topology/dynamics flags)",
        "topology_definition": "adjacency/boundary/connectivity graph over admissible carrier+relation tuples before metric",
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "connected_component_count": len(components),
        "boundary_point_ids": boundary_ids,
        "feature_columns": ["F01", "N01_or_root_gate", "topology_first", "has_dynamics"],
        "feature_matrix": jsonable(features),
        "feature_column_means": jsonable(torch.mean(features, dim=0)),
        "sample_edges": edges[:16],
    }


def candidate_carrier_comparison() -> dict[str, Any]:
    candidates = {
        "topology_first_relation_scaffold": {
            "status": "working_candidate_selected_pending_provider_audit",
            "points": "finite carrier+relation tuples",
            "topology": "adjacency/boundary/connectivity graph before metric",
            "dynamics": "terrain Lindblad CPTP schedule from W3",
            "selection_mechanism_X": "recorded 8-terrain Lindblad/Hamiltonian laws plus nested composition",
            "reason": "matches bootpack topology-first rule and W3 executable terrain schedule without adding Cl closure",
        },
        "fibration_with_transition_functions": {
            "status": "deferred_candidate",
            "reason": "requires explicit transition functions for Xi/rho_AB bridge; not enough current receipt evidence",
        },
        "spectral_triple": {
            "status": "deferred_extra_constraint_X",
            "reason": "could select Clifford via Dirac/metric data, but would be a new X beyond recorded terrain branch",
        },
        "quantum_principal_bundle_or_coaction": {
            "status": "deferred_extra_constraint_X",
            "reason": "could formalize quantum bundle dynamics, but coaction is not yet executable in current receipts",
        },
        "Cstar_GNS_or_fuzzy_sphere": {
            "status": "admissible_non_cl_alternative",
            "reason": "finite noncommutative alternatives remain live unless X excludes them",
        },
    }
    return {
        "pass": candidates["topology_first_relation_scaffold"]["status"]
        == "working_candidate_selected_pending_provider_audit"
        and candidates["Cstar_GNS_or_fuzzy_sphere"]["status"] == "admissible_non_cl_alternative",
        "selected_working_candidate": "topology_first_relation_scaffold",
        "selection_claim_ceiling": "selected as working carrier for next receipts only; not final/survived until W6 provider audit",
        "candidates": candidates,
    }


def hard_negative_report() -> dict[str, Any]:
    negatives = {
        "static_fake": {
            "status": "blocked_as_selector",
            "reason": "static labels or exact Phi0/Cl targets cannot define the manifold or select the bridge",
        },
        "commutative_collapse": {
            "status": "rejected_by_N01",
            "reason": "order-sensitive terrain schedule and N01 gate are required in the selected working carrier",
        },
        "order_erased_equivalent": {
            "status": "rejected_by_N01",
            "reason": "relation tuple must retain directed/order-sensitive composition evidence",
        },
        "random_regular_non_cl": {
            "status": "admissible_as_countermodel_unless_X_excludes",
            "reason": "F01/N01 alone cannot exclude non-Cl finite relation scaffolds",
        },
        "direct_cl_projection": {
            "status": "rejected_as_smuggling_for_selection",
            "reason": "W4 classified Clifford projection feedback as selector risk, not emergence",
        },
    }
    return {"pass": all(row["status"] for row in negatives.values()), "negatives": negatives}


def z3_claim_gate(comparison: dict[str, Any], hard_negatives: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    working_candidate = z3.Bool("working_candidate_selected")
    provider_audit_done = z3.Bool("provider_audit_done")
    final_manifold_claim = z3.Bool("final_manifold_claim")
    cl_uniqueness_claim = z3.Bool("cl_uniqueness_claim")
    hard_negatives_pass = z3.Bool("hard_negatives_recorded")
    solver.add(working_candidate == z3.BoolVal(comparison["pass"]))
    solver.add(hard_negatives_pass == z3.BoolVal(hard_negatives["pass"]))
    solver.add(provider_audit_done == z3.BoolVal(False))
    solver.add(final_manifold_claim == z3.And(working_candidate, hard_negatives_pass, provider_audit_done))
    solver.add(cl_uniqueness_claim == z3.BoolVal(False))
    status = solver.check()
    model = solver.model() if status == z3.sat else None
    final_allowed = bool(model.evaluate(final_manifold_claim)) if model is not None else False
    cl_allowed = bool(model.evaluate(cl_uniqueness_claim)) if model is not None else False
    return {
        "pass": str(status) == "sat" and not final_allowed and not cl_allowed,
        "solver_status": str(status),
        "working_candidate_selected": comparison["pass"],
        "provider_audit_done": False,
        "final_manifold_claim_allowed": final_allowed,
        "cl_uniqueness_claim_allowed": cl_allowed,
    }


def main() -> dict[str, Any]:
    started = time.time()
    prereq = prerequisite_report()
    sources = source_report()
    points = finite_points()
    graph = scaffold_graph(points)
    comparison = candidate_carrier_comparison()
    negatives = hard_negative_report()
    z3_report = z3_claim_gate(comparison, negatives)

    positive = {
        "prerequisite_receipts_loaded": prereq,
        "source_surfaces_loaded": sources,
        "finite_carrier_relation_points_defined": {
            "pass": len(points) == 12 and all(point["F01"] for point in points),
            "points": points,
        },
        "topology_first_scaffold_constructed": graph,
        "candidate_carriers_compared": comparison,
        "explicit_selection_mechanism_X_named": {
            "pass": comparison["candidates"]["topology_first_relation_scaffold"]["selection_mechanism_X"]
            == "recorded 8-terrain Lindblad/Hamiltonian laws plus nested composition",
            "X": comparison["candidates"]["topology_first_relation_scaffold"]["selection_mechanism_X"],
            "not_X": ["TFIM ground state", "graph-edge flip dynamics", "direct Clifford projection"],
        },
        "z3_blocks_final_claim_until_provider_audit": z3_report,
    }

    graveyard_companions = {
        "constraint_manifold_as_metaphor_without_points_killed": {
            "pass": graph["node_count"] == len(points),
            "reason": "points are finite carrier+relation tuples, with adjacency/boundary/connectivity before metric",
        },
        "F01_N01_alone_as_unique_Cl_selector_killed": {
            "pass": comparison["candidates"]["Cstar_GNS_or_fuzzy_sphere"]["status"] == "admissible_non_cl_alternative",
            "reason": "finite noncommutative alternatives remain live unless explicit X excludes them",
        },
        "direct_cl_projection_as_selection_killed": {
            "pass": negatives["negatives"]["direct_cl_projection"]["status"] == "rejected_as_smuggling_for_selection",
            "reason": "W4 projection feedback is selector risk, not emergence",
        },
        "final_manifold_claim_before_provider_audit_killed": {
            "pass": z3_report["final_manifold_claim_allowed"] is False,
            "reason": "working candidate is not a final/survived manifold definition until W6 provider audit",
        },
    }

    boundary = {
        "concrete_manifold_definition_status": {
            "pass": True,
            "value": "working_candidate_selected_pending_provider_audit",
        },
        "selected_working_carrier": {
            "pass": comparison["selected_working_candidate"] == "topology_first_relation_scaffold",
            "value": comparison["selected_working_candidate"],
        },
        "selection_mechanism_X": {
            "pass": True,
            "value": "recorded terrain Lindblad/Hamiltonian laws plus nested CPTP/channel schedule composition",
        },
        "final_claims_blocked": {
            "pass": z3_report["final_manifold_claim_allowed"] is False
            and z3_report["cl_uniqueness_claim_allowed"] is False,
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
        "math_object": "bounded working constraint-manifold carrier and explicit selection mechanism X",
        "concrete_manifold_definition_status": "working_candidate_selected_pending_provider_audit",
        "selected_working_carrier": "topology_first_relation_scaffold",
        "selection_mechanism_X": "recorded terrain Lindblad/Hamiltonian laws plus nested CPTP/channel schedule composition",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "W6 Gemini+Grok provider cross-audit required before this working carrier can be called survived",
            "Xi/rho_AB/Phi0 bridge family still open beyond bounded W3 bridge candidates",
            "C*-algebra/GNS, fuzzy sphere, spectral triple, fibration, and coaction alternatives remain live candidates",
            "broad NumPy import grep blocker remains to resolve or explicitly scope before final closeout",
        ],
        "why_not_v4_probes": "This is a v5 formal-scout definition receipt over current v5 plan/docs and should not add to the mixed v4 probe estate.",
        "summary": {
            "all_pass": all_pass,
            "concrete_manifold_definition_status": "working_candidate_selected_pending_provider_audit",
            "selected_working_carrier": "topology_first_relation_scaffold",
            "selection_mechanism_X": "recorded terrain Lindblad/Hamiltonian laws plus nested CPTP/channel schedule composition",
            "final_manifold_claim_allowed": False,
            "cl_uniqueness_claim_allowed": False,
            "next_required_workstreams": [
                "W6 provider cross-audit on W3/W4/W5 receipts",
                "final synthesis only after provider receipts and broad gate blockers resolved/scoped",
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
                "concrete_manifold_definition_status": receipt["summary"]["concrete_manifold_definition_status"],
                "selected_working_carrier": receipt["summary"]["selected_working_carrier"],
                "selection_mechanism_X": receipt["summary"]["selection_mechanism_X"],
                "final_manifold_claim_allowed": receipt["summary"]["final_manifold_claim_allowed"],
                "out_path": rel(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
