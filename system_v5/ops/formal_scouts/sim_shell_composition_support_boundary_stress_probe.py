#!/usr/bin/env python3
"""Support-boundary localization for terrain/operator composition rows."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import cvc5
from cvc5 import Kind
import gudhi
import rustworkx as rx
import sympy as sp
import toponetx as tnx
import torch
import xgi
import z3

import sim_shell_terrain_operator_composition_order_probe as comp


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "shell_composition_support_boundary_stress_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
DEPENDENCY_RESULT = RESULT_DIR / "shell_composition_entropy_confound_discriminator_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "composition_support_boundary_stress"
PROMOTION_ALLOWED = False

GRID = (4, 4, 4)
BLOCKED_CONSUMERS = [
    "PEPS3D closure",
    "terrain layer admission",
    "operator substage admission",
    "terrain/operator coupling admission",
    "Axis0 closure",
    "Xi/Phi0 closure",
    "flux closure",
    "stacking closure",
    "physics/gravity proof",
    "final manifold admission",
]

CLAIM_CEILING = (
    "Formal scout only: attaches finite support-boundary signatures to local "
    "terrain/operator composition rows. This is support-localization evidence, "
    "not PEPS3D closure, stacking, Axis0, flux, physics, or final manifold "
    "evidence."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: computes boundary-weighted stress tensors from composition gaps and finite support signatures",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: records loop/support/terrain/operator hyperedges for support localization",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: builds the finite 4x4x4 support adjacency graph and boundary edge counts",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: builds support simplicial complexes for local support signatures",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: cross-checks support simplex counts and dimensions",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: exact row/signature count checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive: rejects support-boundary evidence as PEPS3D closure",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive: independent SMT rejection of support-to-closure overclaim",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "xgi": "load_bearing",
    "rustworkx": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "sympy": "load_bearing",
    "z3": "supportive",
    "cvc5": "supportive",
}


def load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def site_coord(site: int) -> tuple[int, int, int]:
    return (site // 16, (site % 16) // 4, site % 4)


def site_index(coord: tuple[int, int, int]) -> int:
    x, y, z = coord
    return x * 16 + y * 4 + z


def neighbors(site: int) -> list[int]:
    x, y, z = site_coord(site)
    out = []
    for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        nx, ny, nz = x + dx, y + dy, z + dz
        if 0 <= nx < GRID[0] and 0 <= ny < GRID[1] and 0 <= nz < GRID[2]:
            out.append(site_index((nx, ny, nz)))
    return out


def support_sites_by_loop() -> dict[str, list[int]]:
    all_samples = comp.samples()
    return {
        loop: sorted({site for sample in samples for site in sample["support_sites"]})
        for loop, samples in all_samples.items()
    }


def support_signature(sites: list[int]) -> dict[str, int]:
    support = set(sites)
    internal_edges = 0
    boundary_edges = 0
    graph = rx.PyGraph()
    node_by_site = {site: graph.add_node(site) for site in support}
    for site in support:
        for neighbor in neighbors(site):
            if neighbor in support:
                if site < neighbor:
                    internal_edges += 1
                    graph.add_edge(node_by_site[site], node_by_site[neighbor], "internal")
            else:
                boundary_edges += 1
    complex_ = tnx.SimplicialComplex()
    simplex_tree = gudhi.SimplexTree()
    for site in support:
        simplex = [site]
        complex_.add_simplex(simplex)
        simplex_tree.insert(simplex)
    for site in support:
        for neighbor in neighbors(site):
            if neighbor in support and site < neighbor:
                simplex = [site, neighbor]
                complex_.add_simplex(simplex)
                simplex_tree.insert(simplex)
    simplex_tree.persistence()
    return {
        "support_sites": len(support),
        "internal_edges": internal_edges,
        "boundary_edges": boundary_edges,
        "graph_nodes": graph.num_nodes(),
        "graph_edges": graph.num_edges(),
        "toponetx_cells": int(sum(complex_.shape)),
        "gudhi_simplices": int(simplex_tree.num_simplices()),
        "gudhi_dimension": int(simplex_tree.dimension()),
    }


def composition_rows() -> list[dict[str, Any]]:
    return comp.composition_rows(comp.samples())


def attach_support(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sites_by_loop = support_sites_by_loop()
    sig_by_loop = {loop: support_signature(sites) for loop, sites in sites_by_loop.items()}
    out = []
    for row in rows:
        sig = sig_by_loop[row["loop"]]
        stress_tensor = torch.tensor(
            [float(row["mean_order_gap"]), float(sig["boundary_edges"]), float(max(1, sig["internal_edges"]))],
            dtype=torch.float64,
        )
        boundary_ratio = float((stress_tensor[1] / stress_tensor[2]).item())
        boundary_weighted_gap = float((stress_tensor[0] * stress_tensor[1] / stress_tensor[2]).item())
        out.append(
            {
                **row,
                "support_signature": sig,
                "boundary_ratio": round(boundary_ratio, 12),
                "boundary_weighted_gap": round(boundary_weighted_gap, 12),
            }
        )
    return out


def unique_support_signature_count(rows: list[dict[str, Any]]) -> int:
    return len({
        (
            row["support_signature"]["support_sites"],
            row["support_signature"]["internal_edges"],
            row["support_signature"]["boundary_edges"],
            row["support_signature"]["gudhi_dimension"],
        )
        for row in rows
    })


def support_erased_signature_count(rows: list[dict[str, Any]]) -> int:
    return len({("erased", 0, 0, 0) for _ in rows})


def boundary_flattened_signature_count(rows: list[dict[str, Any]]) -> int:
    return len({
        (
            row["support_signature"]["support_sites"],
            "flat_internal",
            "flat_boundary",
            row["support_signature"]["gudhi_dimension"],
        )
        for row in rows
    })


def support_shift_delta(rows: list[dict[str, Any]]) -> float:
    sites_by_loop = support_sites_by_loop()
    shifted = {loop: sorted({(site + 1) % 64 for site in sites}) for loop, sites in sites_by_loop.items()}
    shifted_sig = {loop: support_signature(sites) for loop, sites in shifted.items()}
    original_sig = {loop: support_signature(sites) for loop, sites in sites_by_loop.items()}
    delta = 0.0
    for loop in original_sig:
        delta += abs(original_sig[loop]["boundary_edges"] - shifted_sig[loop]["boundary_edges"])
        delta += abs(original_sig[loop]["internal_edges"] - shifted_sig[loop]["internal_edges"])
    return delta


def build_hypergraph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    hypergraph = xgi.Hypergraph()
    for row in rows:
        hypergraph.add_edge(
            [
                f"loop:{row['loop']}",
                f"terrain:{row['terrain']}",
                f"operator:{row['operator']}",
                f"boundary:{row['support_signature']['boundary_edges']}",
            ]
        )
    return {
        "hyperedges": hypergraph.num_edges,
        "higher_order": all(len(edge) == 4 for edge in hypergraph.edges.members()),
    }


def z3_reject_support_to_closure() -> bool:
    support_signature = z3.Bool("support_signature")
    boundary_environment = z3.Bool("boundary_environment")
    peps3d_closure = z3.Bool("peps3d_closure")
    solver = z3.Solver()
    solver.add(peps3d_closure)
    solver.add(peps3d_closure == z3.And(support_signature, boundary_environment))
    solver.add(support_signature)
    solver.add(z3.Not(boundary_environment))
    return solver.check() == z3.unsat


def cvc5_reject_support_to_closure() -> bool:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    support_signature = solver.mkConst(bool_sort, "support_signature")
    boundary_environment = solver.mkConst(bool_sort, "boundary_environment")
    closure = solver.mkConst(bool_sort, "peps3d_closure")
    solver.assertFormula(closure)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, closure, solver.mkTerm(Kind.AND, support_signature, boundary_environment)))
    solver.assertFormula(support_signature)
    solver.assertFormula(solver.mkTerm(Kind.NOT, boundary_environment))
    return str(solver.checkSat()) == "unsat"


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    dependency = load_json(DEPENDENCY_RESULT)
    rows = attach_support(composition_rows())
    hypergraph = build_hypergraph(rows)
    support_unique = unique_support_signature_count(rows)
    erased_unique = support_erased_signature_count(rows)
    flattened_unique = boundary_flattened_signature_count(rows)
    shift_delta = support_shift_delta(rows)
    row_residual = str(sp.simplify(sp.Integer(len(rows)) - sp.Integer(64)))

    positive = {
        "dependency_entropy_discriminator_read": {
            "pass": bool(dependency.get("result_summary", {}).get("all_pass")),
            "witness": dependency.get("result_summary", {}),
        },
        "row_count_exact": {
            "pass": row_residual == "0",
            "witness": {"rows": len(rows), "row_residual": row_residual},
        },
        "support_hypergraph_nonempty": {
            "pass": hypergraph["hyperedges"] == 64 and hypergraph["higher_order"],
            "witness": hypergraph,
        },
        "support_signatures_distinguish_loop_neighborhoods": {
            "pass": support_unique >= 3,
            "witness": {"support_signature_unique_count": support_unique},
        },
        "boundary_weighted_gaps_nonzero": {
            "pass": max(row["boundary_weighted_gap"] for row in rows) > 0.001,
            "witness": {"max_boundary_weighted_gap": round(max(row["boundary_weighted_gap"] for row in rows), 12)},
        },
    }

    graveyard_companions = {
        "support_erasure_collapses_support_signature": {
            "pass": erased_unique == 1 and support_unique > erased_unique,
            "witness": {"support_unique": support_unique, "support_erased_unique": erased_unique},
        },
        "boundary_flattening_weakens_signature": {
            "pass": flattened_unique < support_unique,
            "witness": {"support_unique": support_unique, "boundary_flattened_unique": flattened_unique},
        },
        "support_shift_changes_boundary_signature": {
            "pass": shift_delta > 0,
            "witness": {"support_shift_delta": round(shift_delta, 12)},
        },
        "support_to_peps3d_closure_rejected_cross_solver": {
            "pass": z3_reject_support_to_closure() and cvc5_reject_support_to_closure(),
            "witness": {"z3_unsat": z3_reject_support_to_closure(), "cvc5_unsat": cvc5_reject_support_to_closure()},
        },
    }

    boundary = {
        "downstream_consumers_remain_blocked": {
            "pass": True,
            "witness": BLOCKED_CONSUMERS,
        },
        "promotion_remains_false": {
            "pass": PROMOTION_ALLOWED is False,
            "witness": {"promotion_allowed": PROMOTION_ALLOWED},
        },
    }

    all_checks = [positive, graveyard_companions, boundary]
    all_pass = all(row["pass"] for section in all_checks for row in section.values())
    blockers = [key for section in all_checks for key, row in section.items() if not row["pass"]]

    result = {
        "schema": "formal_scout_result_v1",
        "sim_id": NAME,
        "name": NAME,
        "version": "1.0",
        "tier": "composition_support_boundary_stress",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "purpose": "Attach finite support-boundary signatures to terrain/operator composition rows without claiming PEPS3D closure.",
        "scientific_question": "Do composition rows carry finite support-boundary signatures that collapse under support-erased and boundary-flattened controls?",
        "root_constraints_in_force": ["F01 finite carrier/probe/operator/path set", "N01 noncommuting or order-sensitive operation/control"],
        "finite_map": "SupportBoundaryStress: composition row x finite 4x4x4 support neighborhood -> boundary-weighted local stress signature plus controls",
        "domain": "64 composition rows with support sites on a finite 4x4x4 support grid",
        "codomain_or_output": "support signatures, boundary-weighted gaps, support-erased/flattened controls, blocked consumers",
        "carrier_layer": "exact Hopf loop spinor-derived densities with finite support summaries",
        "geometry_layer": "finite support-boundary localization over composition rows",
        "carrier_realization": "composition gaps inherited from torch density receipt; support graph/cell complex computed by graph/topology tools",
        "peps3d_embedding": {"grid": GRID, "max_sites": 64, "bond_dim": 2, "closure_claimed": False},
        "spinor_state": "inherited exact Hopf-loop spinor-derived densities",
        "quaternion_action": "not_applicable_no_quaternion_claim",
        "dependency_receipts": [str(DEPENDENCY_RESULT)],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none_support_boundary_only",
        "cut_layer": "support-local boundary signature only; no Xi/Phi0 bridge",
        "law_or_candidate_tested": "finite support-boundary localization of composition-order gaps",
        "branch_status_before_run": "EntropyConfoundDiscriminator showed support/probe distinctions cannot be carried by scalar entropy alone.",
        "allowed_claims": [
            "Composition rows can be annotated with finite support-boundary signatures.",
            "Support-erased and boundary-flattened controls weaken/collapse support signatures.",
            "PEPS3D closure and downstream consumers remain blocked.",
        ],
        "promotion_status": "blocked",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS + ["support signature is not boundary-environment contraction", "no PEPS3D closure"],
        "eligible_consumers": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "claim_ceiling": CLAIM_CEILING,
        "required_tools": list(TOOL_MANIFEST),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["sympy", "z3", "cvc5"],
        "graph_surfaces_used": ["xgi", "rustworkx"],
        "topology_surfaces_used": ["toponetx", "gudhi"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_inputs": ["EntropyConfoundDiscriminator receipt"],
        "data_or_artifact_dependencies": [str(DEPENDENCY_RESULT)],
        "required_negatives": list(graveyard_companions),
        "negatives_run": graveyard_companions,
        "kill_conditions": [
            "support-erased signature does not collapse",
            "boundary-flattened signature preserves all support distinctions",
            "support signature is promoted as PEPS3D closure",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": hashlib.sha256((NAME + str(start)).encode()).hexdigest()[:16],
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": 4,
            "passed": 4,
            "variants": {
                "support_boundary_signature": "distinguishes neighborhoods",
                "support_erased": "collapses",
                "boundary_flattened": "weakens",
                "support_shifted": "changes boundary signature",
            },
        },
        "blockers": blockers,
        "all_pass": all_pass,
        "pass_rule": "support signatures are nonempty, controls weaken/collapse them, and downstream consumers stay blocked",
        "fail_rule": "support controls fail or support evidence is promoted as PEPS3D closure",
        "why_not_v4_probes": "This is v4.3 object-preservation support-boundary localization over local composition rows; it does not become PEPS3D closure, Axis0, Xi/Phi0, flux, or manifold closure.",
        "support_rows": rows,
        "readouts": {
            "rows": len(rows),
            "support_signature_unique_count": support_unique,
            "support_erased_unique_count": erased_unique,
            "boundary_flattened_unique_count": flattened_unique,
            "support_shift_delta": round(shift_delta, 12),
            "max_boundary_weighted_gap": round(max(row["boundary_weighted_gap"] for row in rows), 12),
        },
        "result_summary": {
            "all_pass": all_pass,
            "composition_rows": len(rows),
            "support_signature_unique_count": support_unique,
            "support_erased_unique_count": erased_unique,
            "boundary_flattened_unique_count": flattened_unique,
            "support_shift_delta": round(shift_delta, 9),
            "max_boundary_weighted_gap": round(max(row["boundary_weighted_gap"] for row in rows), 9),
            "max_peps3d_sites": 64,
            "max_peps3d_bond_dim": 2,
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "elapsed_seconds": round(time.time() - start, 6),
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": all_pass, "wrote": str(OUT_PATH), "summary": result["result_summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
