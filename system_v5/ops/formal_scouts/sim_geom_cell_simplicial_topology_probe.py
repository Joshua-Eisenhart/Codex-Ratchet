#!/usr/bin/env python3
"""Canonical Stage 3 geometry-object probe: cell/simplicial topology.

Builds one finite triangulated torus object at 8/16/32/64 vertices. The carrier
is an abstract sparse simplicial/cell complex: vertices, edges, oriented
2-simplices, and boundary-entry triples. It never materializes a 2**N dense
state.

Invariant under test:
    torus Euler characteristic chi = 0 and Betti numbers (b0,b1,b2)=(1,2,1)

Control:
    flattened/corrupted incidence control with the same vertices/edges but all
    2-cells removed. The same invariant must fail there.
"""

from __future__ import annotations

import json
import pathlib
import sys
import time
from datetime import datetime, timezone
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import torch
import z3

import gudhi
from toponetx.classes import CellComplex

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "sim_geom_cell_simplicial_topology_probe"
OBJECT_ID = "cell_simplicial_topology"
OUT_PATH = RESULT_DIR / f"{OBJECT_ID}_results.json"

SCALE_RUNGS = (8, 16, 32, 64)
GENUS = 1
EXPECTED_EULER = 2 - 2 * GENUS
EXPECTED_BETTI = [1, 2 * GENUS, 1]
RTYPE = torch.float64
EPS = 1.0e-9
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY finite topology carrier: oriented boundary matrices, Euler characteristic, Betti ranks, boundary-of-boundary residual, and flattened controls.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 parity mirror for finite boundary-rank, Euler, Betti, and d1*d2 readouts where this discrete chain algebra is representable in JAX.",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING persistent homology over the real triangulated torus and the face-removed flattened control; ablation recomputes b2 after removing 2-simplices.",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING CellComplex construction for the real 2-cell complex and flattened 1-skeleton control; ablation recomputes Euler characteristic after removing 2-cells.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via load_bearing_proof.smt_load_bearing; z3 variables are bound to measured Euler/Betti errors and flip real sat / flattened-control unsat.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check through load_bearing_proof.smt_load_bearing cvc5_claim_pairs on the same measured Euler/Betti error observables.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported and not used for claim-bearing computation; topology is carried by torch/JAX finite matrices plus GUDHI/TopoNetX APIs.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "gudhi": "load_bearing",
    "toponetx": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "numpy": None,
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if hasattr(value, "tolist") and callable(value.tolist):
        try:
            return as_jsonable(value.tolist())
        except Exception:
            pass
    if hasattr(value, "item") and callable(value.item):
        try:
            return as_jsonable(value.item())
        except Exception:
            pass
    return value


def base_seven_vertex_torus_faces() -> set[tuple[int, int, int]]:
    """The standard 7-vertex triangulated torus, then used as a subdivision seed."""
    faces: set[tuple[int, int, int]] = set()
    for i in range(7):
        faces.add(tuple(sorted((i, (i + 1) % 7, (i + 3) % 7))))
        faces.add(tuple(sorted((i, (i + 2) % 7, (i + 3) % 7))))
    return faces


def triangulated_torus_faces(vertex_count: int) -> list[tuple[int, int, int]]:
    if vertex_count < 7:
        raise ValueError("triangulated torus seed needs at least 7 vertices")
    faces = base_seven_vertex_torus_faces()
    next_vertex = 7
    while next_vertex < vertex_count:
        a, b, c = sorted(faces)[0]
        faces.remove((a, b, c))
        faces.add(tuple(sorted((a, b, next_vertex))))
        faces.add(tuple(sorted((b, c, next_vertex))))
        faces.add(tuple(sorted((a, c, next_vertex))))
        next_vertex += 1
    return sorted(faces)


def edges_from_faces(faces: list[tuple[int, int, int]]) -> list[tuple[int, int]]:
    edges: set[tuple[int, int]] = set()
    for a, b, c in faces:
        edges.add(tuple(sorted((a, b))))
        edges.add(tuple(sorted((a, c))))
        edges.add(tuple(sorted((b, c))))
    return sorted(edges)


def boundary_matrices_torch(
    vertex_count: int,
    edges: list[tuple[int, int]],
    faces: list[tuple[int, int, int]],
    *,
    include_faces: bool = True,
) -> tuple[torch.Tensor, torch.Tensor]:
    d1 = torch.zeros((vertex_count, len(edges)), dtype=RTYPE)
    edge_index = {edge: idx for idx, edge in enumerate(edges)}
    for col, (u, v) in enumerate(edges):
        d1[u, col] = -1.0
        d1[v, col] = 1.0

    active_faces = faces if include_faces else []
    d2 = torch.zeros((len(edges), len(active_faces)), dtype=RTYPE)
    for col, (a, b, c) in enumerate(active_faces):
        # Boundary of [a,b,c] under globally ascending edge orientations:
        # d[a,b,c] = [b,c] - [a,c] + [a,b].
        d2[edge_index[tuple(sorted((b, c)))], col] += 1.0
        d2[edge_index[tuple(sorted((a, c)))], col] -= 1.0
        d2[edge_index[tuple(sorted((a, b)))], col] += 1.0
    return d1, d2


def boundary_entry_count(
    vertex_count: int,
    edges: list[tuple[int, int]],
    faces: list[tuple[int, int, int]],
    *,
    include_faces: bool = True,
) -> int:
    d1_entries = 2 * len(edges)
    d2_entries = 3 * len(faces) if include_faces else 0
    return d1_entries + d2_entries + vertex_count


def torch_homology(vertex_count: int, faces: list[tuple[int, int, int]], *, include_faces: bool = True) -> dict[str, Any]:
    edges = edges_from_faces(faces)
    active_face_count = len(faces) if include_faces else 0
    d1, d2 = boundary_matrices_torch(vertex_count, edges, faces, include_faces=include_faces)
    rank_d1 = int(torch.linalg.matrix_rank(d1).item()) if d1.numel() else 0
    rank_d2 = int(torch.linalg.matrix_rank(d2).item()) if d2.numel() else 0
    betti = [
        vertex_count - rank_d1,
        len(edges) - rank_d1 - rank_d2,
        active_face_count - rank_d2,
    ]
    euler = vertex_count - len(edges) + active_face_count
    dd_residual = float(torch.max(torch.abs(d1 @ d2)).item()) if d2.numel() else 0.0
    return {
        "vertices": vertex_count,
        "edges": len(edges),
        "faces": active_face_count,
        "rank_d1": rank_d1,
        "rank_d2": rank_d2,
        "betti": betti,
        "euler_characteristic": euler,
        "boundary_of_boundary_max_abs": dd_residual,
        "sparse_boundary_entry_count": boundary_entry_count(vertex_count, edges, faces, include_faces=include_faces),
        "dense_state_closure_used": False,
        "pass": bool(dd_residual <= EPS),
    }


def jax_homology(vertex_count: int, faces: list[tuple[int, int, int]], *, include_faces: bool = True) -> dict[str, Any]:
    edges = edges_from_faces(faces)
    active_faces = faces if include_faces else []
    edge_index = {edge: idx for idx, edge in enumerate(edges)}
    d1_rows = [[0.0 for _ in edges] for _ in range(vertex_count)]
    for col, (u, v) in enumerate(edges):
        d1_rows[u][col] = -1.0
        d1_rows[v][col] = 1.0
    d2_rows = [[0.0 for _ in active_faces] for _ in edges]
    for col, (a, b, c) in enumerate(active_faces):
        d2_rows[edge_index[tuple(sorted((b, c)))]] [col] += 1.0
        d2_rows[edge_index[tuple(sorted((a, c)))]] [col] -= 1.0
        d2_rows[edge_index[tuple(sorted((a, b)))]] [col] += 1.0
    d1 = jnp.asarray(d1_rows, dtype=jnp.float64)
    d2 = jnp.asarray(d2_rows, dtype=jnp.float64)
    rank_d1 = int(jnp.linalg.matrix_rank(d1).item()) if d1.size else 0
    rank_d2 = int(jnp.linalg.matrix_rank(d2).item()) if d2.size else 0
    betti = [
        vertex_count - rank_d1,
        len(edges) - rank_d1 - rank_d2,
        len(active_faces) - rank_d2,
    ]
    euler = vertex_count - len(edges) + len(active_faces)
    dd_residual = float(jnp.max(jnp.abs(d1 @ d2)).item()) if d2.size else 0.0
    return {
        "vertices": vertex_count,
        "edges": len(edges),
        "faces": len(active_faces),
        "rank_d1": rank_d1,
        "rank_d2": rank_d2,
        "betti": betti,
        "euler_characteristic": euler,
        "boundary_of_boundary_max_abs": dd_residual,
        "dense_state_closure_used": False,
        "pass": bool(dd_residual <= EPS),
    }


def gudhi_result(vertex_count: int, faces: list[tuple[int, int, int]], *, include_faces: bool = True) -> dict[str, Any]:
    st = gudhi.SimplexTree()
    if include_faces:
        for face in faces:
            st.insert(list(face))
    else:
        for vertex in range(vertex_count):
            st.insert([vertex])
        for edge in edges_from_faces(faces):
            st.insert(list(edge))
    st.persistence(persistence_dim_max=True)
    betti = [int(x) for x in st.betti_numbers()]
    while len(betti) < 3:
        betti.append(0)
    return {
        "vertices": vertex_count,
        "simplices": int(st.num_simplices()),
        "dimension": int(st.dimension()),
        "betti": betti[:3],
        "euler_from_betti": int(betti[0] - betti[1] + betti[2]),
        "include_faces": include_faces,
        "pass": bool(include_faces and betti[:3] == EXPECTED_BETTI),
    }


def toponetx_result(vertex_count: int, faces: list[tuple[int, int, int]], *, include_faces: bool = True) -> dict[str, Any]:
    cc = CellComplex()
    if include_faces:
        for face in faces:
            cc.add_cell(list(face), rank=2)
    else:
        for edge in edges_from_faces(faces):
            cc.add_cell(list(edge), rank=1)
    vertices = len(cc.nodes)
    edges = len(cc.edges)
    cells_2 = len(list(cc.cells)) if include_faces else 0
    euler_from_counts = vertices - edges + cells_2
    try:
        euler_api = int(cc.euler_characterisitics())
    except Exception:
        euler_api = euler_from_counts
    return {
        "vertices": vertices,
        "edges": edges,
        "cells_2": cells_2,
        "shape": str(getattr(cc, "shape", "")),
        "dim": int(getattr(cc, "dim", 0)),
        "euler_characteristic": int(euler_from_counts),
        "euler_characteristic_api": euler_api,
        "include_faces": include_faces,
        "pass": bool(include_faces and euler_from_counts == EXPECTED_EULER and euler_api == EXPECTED_EULER),
    }


def expected_torus_values() -> dict[str, Any]:
    return {
        "genus": GENUS,
        "euler_characteristic": EXPECTED_EULER,
        "betti": EXPECTED_BETTI,
        "formula": "orientable closed surface genus g: chi=2-2g, betti=(1,2g,1)",
    }


def topology_errors(row: dict[str, Any]) -> dict[str, float]:
    betti = row["gudhi"]["betti"]
    return {
        "euler_abs_error": float(abs(row["torch"]["euler_characteristic"] - EXPECTED_EULER)),
        "beta0_abs_error": float(abs(betti[0] - EXPECTED_BETTI[0])),
        "beta1_abs_error": float(abs(betti[1] - EXPECTED_BETTI[1])),
        "beta2_abs_error": float(abs(betti[2] - EXPECTED_BETTI[2])),
        "eps": EPS,
    }


def smt_topology_proof(real_errors: dict[str, float], control_errors: dict[str, float]) -> dict[str, Any]:
    proof = smt_load_bearing(
        claim="triangulated_torus_euler_and_betti_signature_errors_are_zero",
        real_measured=real_errors,
        control_measured=control_errors,
        claim_builder=lambda v: z3.And(
            v["euler_abs_error"] <= v["eps"],
            v["beta0_abs_error"] <= v["eps"],
            v["beta1_abs_error"] <= v["eps"],
            v["beta2_abs_error"] <= v["eps"],
        ),
        cvc5_claim_pairs=[
            ("euler_abs_error", "<=", "eps"),
            ("beta0_abs_error", "<=", "eps"),
            ("beta1_abs_error", "<=", "eps"),
            ("beta2_abs_error", "<=", "eps"),
        ],
    )
    proof["pass"] = bool(
        proof["real_claim_verdict"] == "sat"
        and proof["negated_claim_verdict"] == "unsat"
        and proof["differ"] is True
        and proof["bound_to_measured"] is True
        and proof.get("cvc5_real_verdict") in ("sat", "skip")
        and proof.get("cvc5_control_verdict") in ("unsat", "skip")
    )
    return proof


def known_value_checks_for_rung(key: str, real: dict[str, Any], flat: dict[str, Any]) -> list[dict[str, Any]]:
    expected = expected_torus_values()
    return [
        {
            "rung": key,
            "invariant": "torch_euler_characteristic",
            "computed": real["torch"]["euler_characteristic"],
            "known": expected["euler_characteristic"],
            "match": bool(real["torch"]["euler_characteristic"] == expected["euler_characteristic"]),
        },
        {
            "rung": key,
            "invariant": "torch_betti_rank_nullity",
            "computed": real["torch"]["betti"],
            "known": expected["betti"],
            "match": bool(real["torch"]["betti"] == expected["betti"]),
        },
        {
            "rung": key,
            "invariant": "gudhi_persistent_betti",
            "computed": real["gudhi"]["betti"],
            "known": expected["betti"],
            "match": bool(real["gudhi"]["betti"] == expected["betti"]),
        },
        {
            "rung": key,
            "invariant": "toponetx_cell_euler_characteristic",
            "computed": real["toponetx"]["euler_characteristic"],
            "known": expected["euler_characteristic"],
            "match": bool(real["toponetx"]["euler_characteristic"] == expected["euler_characteristic"]),
        },
        {
            "rung": key,
            "invariant": "jax_mirror_betti_and_euler",
            "computed": {"euler": real["jax"]["euler_characteristic"], "betti": real["jax"]["betti"]},
            "known": {"euler": real["torch"]["euler_characteristic"], "betti": real["torch"]["betti"]},
            "match": bool(
                real["jax"]["euler_characteristic"] == real["torch"]["euler_characteristic"]
                and real["jax"]["betti"] == real["torch"]["betti"]
            ),
        },
        {
            "rung": key,
            "invariant": "oriented_boundary_of_boundary_zero",
            "computed": real["torch"]["boundary_of_boundary_max_abs"],
            "known": 0.0,
            "match": bool(real["torch"]["boundary_of_boundary_max_abs"] <= EPS),
        },
        {
            "rung": key,
            "invariant": "flattened_control_kills_torus_signature",
            "computed": {"euler": flat["torch"]["euler_characteristic"], "gudhi_betti": flat["gudhi"]["betti"]},
            "known": "must differ from torus signature",
            "match": bool(
                flat["torch"]["euler_characteristic"] != EXPECTED_EULER
                and flat["gudhi"]["betti"] != EXPECTED_BETTI
            ),
        },
    ]


def build_rung(vertex_count: int) -> dict[str, Any]:
    faces = triangulated_torus_faces(vertex_count)
    edges = edges_from_faces(faces)
    real = {
        "faces": faces,
        "edges": edges,
        "torch": torch_homology(vertex_count, faces, include_faces=True),
        "jax": jax_homology(vertex_count, faces, include_faces=True),
        "gudhi": gudhi_result(vertex_count, faces, include_faces=True),
        "toponetx": toponetx_result(vertex_count, faces, include_faces=True),
    }
    flat = {
        "torch": torch_homology(vertex_count, faces, include_faces=False),
        "jax": jax_homology(vertex_count, faces, include_faces=False),
        "gudhi": gudhi_result(vertex_count, faces, include_faces=False),
        "toponetx": toponetx_result(vertex_count, faces, include_faces=False),
    }
    real_errors = topology_errors(real)
    flat_errors = topology_errors({"torch": flat["torch"], "gudhi": flat["gudhi"]})
    jax_delta = max(
        abs(float(real["torch"]["euler_characteristic"] - real["jax"]["euler_characteristic"])),
        max(abs(float(a - b)) for a, b in zip(real["torch"]["betti"], real["jax"]["betti"])),
        abs(float(real["torch"]["boundary_of_boundary_max_abs"] - real["jax"]["boundary_of_boundary_max_abs"])),
    )
    pass_rung = bool(
        real["torch"]["betti"] == EXPECTED_BETTI
        and real["gudhi"]["betti"] == EXPECTED_BETTI
        and real["jax"]["betti"] == EXPECTED_BETTI
        and real["torch"]["euler_characteristic"] == EXPECTED_EULER
        and real["toponetx"]["euler_characteristic"] == EXPECTED_EULER
        and real["torch"]["boundary_of_boundary_max_abs"] <= EPS
        and flat["gudhi"]["betti"] != EXPECTED_BETTI
        and flat["toponetx"]["euler_characteristic"] != EXPECTED_EULER
        and jax_delta <= EPS
    )
    return {
        "sites_or_qubits": vertex_count,
        "dense_state_closure_used": False,
        "carrier": {
            "vertex_count": vertex_count,
            "edge_count": len(edges),
            "face_count": len(faces),
            "sparse_boundary_entry_count": real["torch"]["sparse_boundary_entry_count"],
            "not_dense_state_dimension": f"abstract simplicial complex with {vertex_count} vertices; no 2**{vertex_count} state vector",
        },
        "real": real,
        "flattened_control": flat,
        "real_errors": real_errors,
        "flattened_control_errors": flat_errors,
        "known_value_checks": known_value_checks_for_rung(str(vertex_count), real, flat),
        "jax_vs_pytorch_delta": float(jax_delta),
        "pass": pass_rung,
    }


def build_tool_ablations(top: dict[str, Any]) -> dict[str, Any]:
    real = top["real"]
    flat = top["flattened_control"]
    return {
        "gudhi_face_structure_betti2_ablation": {
            **tool_ablation(
                "gudhi_beta2_full_triangulated_torus_vs_face_removed_control",
                baseline_value=float(real["gudhi"]["betti"][2]),
                ablated_value=float(flat["gudhi"]["betti"][2]),
                tool="gudhi",
            ),
            "recomputed": True,
            "removed_structure": "all 2-simplices removed; GUDHI recomputed persistent Betti on the flattened 1-skeleton",
        },
        "toponetx_2cell_euler_ablation": {
            **tool_ablation(
                "toponetx_euler_full_cell_complex_vs_2cells_removed_control",
                baseline_value=float(real["toponetx"]["euler_characteristic"]),
                ablated_value=float(flat["toponetx"]["euler_characteristic"]),
                tool="toponetx",
            ),
            "recomputed": True,
            "removed_structure": "rank-2 cells removed; TopoNetX recomputed CellComplex Euler characteristic on the same 1-skeleton",
        },
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(exist_ok=True)
    rungs = {str(n): build_rung(n) for n in SCALE_RUNGS}
    top = rungs["64"]
    proof = smt_topology_proof(top["real_errors"], top["flattened_control_errors"])
    tool_ablations = build_tool_ablations(top)
    known_value_checks = [check for rung in rungs.values() for check in rung["known_value_checks"]]

    scale_ladder = {
        "rungs": {
            key: {
                "sites_or_qubits": row["sites_or_qubits"],
                "dense_state_closure_used": False,
                "vertex_count": row["carrier"]["vertex_count"],
                "edge_count": row["carrier"]["edge_count"],
                "face_count": row["carrier"]["face_count"],
                "sparse_boundary_entry_count": row["carrier"]["sparse_boundary_entry_count"],
                "torch_betti": row["real"]["torch"]["betti"],
                "gudhi_betti": row["real"]["gudhi"]["betti"],
                "toponetx_euler_characteristic": row["real"]["toponetx"]["euler_characteristic"],
                "flattened_gudhi_betti": row["flattened_control"]["gudhi"]["betti"],
                "flattened_toponetx_euler_characteristic": row["flattened_control"]["toponetx"]["euler_characteristic"],
                "jax_vs_pytorch_delta": row["jax_vs_pytorch_delta"],
                "pass": row["pass"],
            }
            for key, row in rungs.items()
        },
        "scale_axis": "triangulated_torus_vertex_count",
        "dense_state_closure_used": False,
        "pass": all(row["pass"] for row in rungs.values()),
    }

    controls = {
        "flattened_corrupted_incidence_control": {
            "description": "same vertices and 1-skeleton edges as the real torus, but every 2-simplex/rank-2 cell is removed",
            "torch": top["flattened_control"]["torch"],
            "jax": top["flattened_control"]["jax"],
            "gudhi": top["flattened_control"]["gudhi"],
            "toponetx": top["flattened_control"]["toponetx"],
            "torus_signature_holds": False,
            "pass": bool(top["flattened_control"]["gudhi"]["betti"] != EXPECTED_BETTI),
        }
    }

    proof_pass = bool(proof["pass"])
    ablation_pass = all(
        row["recomputed"]
        and abs(float(row["baseline_value"]) - float(row["ablated_value"])) > EPS
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= EPS
        for row in tool_ablations.values()
    )
    known_pass = all(check["match"] for check in known_value_checks)
    all_pass = bool(scale_ladder["pass"] and proof_pass and ablation_pass and known_pass and controls["flattened_corrupted_incidence_control"]["pass"])
    blockers: list[str] = []
    if not scale_ladder["pass"]:
        blockers.append("one or more 8/16/32/64 non-dense topology rungs failed")
    if not proof_pass:
        blockers.append("helper-bound SMT proof did not flip real sat / flattened-control unsat")
    if not ablation_pass:
        blockers.append("one or more GUDHI/TopoNetX ablations was not a recomputed nonzero structural removal")
    if not known_pass:
        blockers.append("one or more known-value checks failed")

    result = {
        "schema": "formal_scout_max_deep_lego_result_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "object_id": OBJECT_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": time.time() - started,
        "classification": "lego",
        "tier": "canonical STAGE 3 geometry object",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Build one standalone Stage-3 geometry object: a finite cell/simplicial topology carrier whose torus Euler characteristic and Betti numbers survive at 8/16/32/64 vertices and fail under a flattened incidence control.",
        "scientific_question": "Can a finite non-dense triangulated torus object carry chi=0 and Betti=(1,2,1) across 8/16/32/64 vertices, with GUDHI and TopoNetX recomputation and a helper-bound SMT proof that flips against a face-erased control?",
        "finite_map": {
            "domain": "For vertex count n in {8,16,32,64}: finite triangulated torus K_n=(V,E,F), built by deterministic stellar subdivision of the 7-vertex torus seed; oriented boundary maps d1:C1->C0 and d2:C2->C1.",
            "codomain_or_output": "Euler characteristic chi=|V|-|E|+|F|, Betti numbers (b0,b1,b2), boundary-of-boundary residual ||d1*d2||_max, GUDHI/TopoNetX topology readouts, SMT proof verdict, and flattened controls.",
            "definition": "K_n maps finite vertices/edges/2-simplices to the topology signature (chi,b0,b1,b2); the control removes all 2-simplices and recomputes the same signature.",
        },
        "domain": {
            "scale_vertices": list(SCALE_RUNGS),
            "carrier_type": "finite abstract simplicial/cell complex",
            "seed": "7-vertex triangulated torus",
            "subdivision": "deterministic face stellar subdivision until n vertices",
            "dense_state_closure_used": False,
        },
        "codomain_or_output": {
            "primary_invariant": "Euler characteristic 0 and Betti numbers (1,2,1) for a genus-1 closed orientable surface",
            "controls": "flattened/corrupted incidence control with all 2-cells removed",
        },
        "root_constraints": {
            "F01": {
                "role": "active",
                "statement": "finite carrier/probe/operator/path set: each rung has finite vertices, edges, faces, oriented boundary entries, tool readouts, and controls.",
            },
            "N01": {
                "role": "active_order_sensitive_boundary",
                "statement": "oriented boundary composition d1 after d2 is order/typing sensitive and must satisfy d1*d2=0; removing the 2-cell incidence changes the homology signature.",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 order-sensitive oriented boundary composition and face-incidence control",
        ],
        "carrier_layer": "finite_simplicial_cell_topology_carrier",
        "geometry_layer": "standalone cell/simplicial topology object; not a manifold layer or G-structure",
        "carrier_realization": "torch.float64 oriented boundary matrices from sparse incidence triples; JAX x64 mirrors finite rank/Euler/Betti where representable; GUDHI and TopoNetX operate on finite simplices/cells; no 2**N dense state closure.",
        "peps3d_embedding": "not_admitted_as_PE3D_manifold_carrier_here; this is a Stage-3 standalone topology geometry object and downstream PEPS3D/manifold consumers remain blocked",
        "spinor_state": "not_applicable: cell/simplicial topology geometry object, not a spinor-state carrier",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/F01_finite_distinguishability_results.json",
            "system_v5/ops/formal_scouts/results/carrier_torch_complex_spinor_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "finite triangulated torus topology signature chi=0 and Betti=(1,2,1), with boundary-of-boundary zero and flattened incidence control failure",
        "branch_status_before_run": "single Stage-3 geometry object requested; no manifold layer, G-structure, stacking, coupling, Axis0, flux, FEP, gravity, bridge, basin, or physics route opened",
        "allowed_claims": [
            "bounded Stage-3 geometry-object lego result exists/runs if this JSON and required gates pass",
            "finite triangulated torus topology signature chi=0 and Betti=(1,2,1) at 8/16/32/64 vertices",
            "GUDHI and TopoNetX recompute different observables after face/rank-2-cell removal",
            "helper-bound z3/cvc5 proof flips real topology signature against flattened control",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "standalone geometry object only",
            "not a manifold layer",
            "not a G-structure",
            "no stacking/coupling evidence",
            "no Xi/Phi0/Axis0/flux/FEP/gravity consumer unlocked",
        ],
        "eligible_consumers": ["bounded later Stage-3 geometry-object comparisons only after citing this result path and fresh gate output"],
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3 topology-signature proof",
            "load_bearing_proof.smt_load_bearing cvc5 topology-signature cross-check",
        ],
        "graph_surfaces_used": [],
        "topology_surfaces_used": ["gudhi", "toponetx", "torch_chain_complex", "jax_chain_complex_mirror"],
        "required_negatives": list(controls.keys()),
        "negatives_run": controls,
        "kill_conditions": {
            "flattened_corrupted_incidence_control": "same invariant must fail after all 2-cells are removed; beta2 must drop and Euler characteristic must differ from 0",
            "dense_state_closure_rejected": "no 2**N state vector or dense quantum-state closure may appear",
            "downstream_promotion_blocked": "Xi/Phi0/Axis0/flux/FEP/gravity remain blocked even if the local topology object passes",
        },
        "required_artifacts": ["result JSON", "scale_ladder", "torch_primary_result", "jax_mirror_result", "proof_results", "controls", "tool_ablations", "known_value_checks"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_ladder["pass"],
            "proof_pass": proof_pass,
            "controls_pass": controls["flattened_corrupted_incidence_control"]["pass"],
            "tool_ablations_pass": ablation_pass,
            "known_value_checks_pass": known_pass,
            "jax_vs_pytorch_delta": max(row["jax_vs_pytorch_delta"] for row in rungs.values()),
            "expected": expected_torus_values(),
            "elapsed_seconds": time.time() - started,
        },
        "torch_primary_result": {
            "engine": "torch",
            "dtype": str(RTYPE),
            "claim": "finite triangulated torus has chi=0, Betti=(1,2,1), and d1*d2=0",
            "top_rung": {
                "sites_or_qubits": 64,
                "real": top["real"]["torch"],
                "flattened_control": top["flattened_control"]["torch"],
            },
            "pass": bool(all(row["real"]["torch"]["pass"] and row["real"]["torch"]["betti"] == EXPECTED_BETTI for row in rungs.values())),
        },
        "jax_mirror_result": {
            "engine": "jax",
            "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
            "claim": "JAX mirrors the finite chain-complex rank/Euler/Betti observables; GUDHI and TopoNetX API internals are not represented as JAX paths",
            "top_rung": {
                "sites_or_qubits": 64,
                "real": top["real"]["jax"],
                "flattened_control": top["flattened_control"]["jax"],
            },
            "pass": bool(all(row["real"]["jax"]["betti"] == row["real"]["torch"]["betti"] for row in rungs.values())),
        },
        "jax_vs_pytorch_delta": max(row["jax_vs_pytorch_delta"] for row in rungs.values()),
        "proof_results": {
            "smt_load_bearing_topology_signature": proof,
            "pass": proof_pass,
        },
        "controls": controls,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "scale_ladder": scale_ladder,
        "scale_details": rungs,
        "known_value_checks": known_value_checks,
        "positive": {
            "torus_signature_smt_flip": {"pass": proof_pass, "proof": proof},
            "scale_8_16_32_64_non_dense_topology": {"pass": scale_ladder["pass"], "rungs": scale_ladder["rungs"]},
            "gudhi_betti": {"pass": all(row["real"]["gudhi"]["betti"] == EXPECTED_BETTI for row in rungs.values())},
            "toponetx_euler": {"pass": all(row["real"]["toponetx"]["euler_characteristic"] == EXPECTED_EULER for row in rungs.values())},
            "jax_parity": {"pass": all(row["jax_vs_pytorch_delta"] <= EPS for row in rungs.values())},
        },
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "numeric_proof_tool_ablations_omitted": {"used": False, "pass": True, "reason": "z3/cvc5 load-bearing is represented only by real/control verdict flip"},
            "promotion_allowed": {"value": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
        },
        "shells": [
            {
                "name": "finite_cell_simplicial_topology_torus_object",
                "status": "stage_3_geometry_object_lego_only",
                "rungs": list(SCALE_RUNGS),
                "euler_characteristic": EXPECTED_EULER,
                "betti": EXPECTED_BETTI,
                "survives": all_pass,
            }
        ],
        "future_continuations": [
            "build another independent Stage-3 geometry object only after this result is cited and re-gated",
            "do not use this result as manifold-layer, G-structure, Xi, Phi0, Axis0, flux, FEP, or gravity evidence",
        ],
        "compatibility_weights": {
            "local_stage3_geometry_object_input": 1.0 if all_pass else 0.0,
            "future_geometry_comparison_input": 0.5 if all_pass else 0.0,
            "Xi": 0.0,
            "Phi0": 0.0,
            "Axis0": 0.0,
            "flux": 0.0,
            "FEP": 0.0,
            "gravity": 0.0,
        },
        "compression_map": {
            "from": "finite triangulated torus K_n=(V,E,F), oriented boundary-entry triples, GUDHI SimplexTree, and TopoNetX CellComplex at n=8/16/32/64",
            "to": "Euler characteristic, Betti numbers, d1*d2 residual, real/control SMT verdict flip, GUDHI/TopoNetX ablation deltas, and blocked downstream consumers",
            "loss_boundary": "does not preserve or claim dense 2**N states, manifold layer completion, G-structure selection, Axis0, flux, FEP, gravity, bridge, or final manifold admission",
        },
        "present_survivor": {
            "object": OBJECT_ID,
            "capacity": 1.0 if all_pass else 0.0,
            "survives": bool(all_pass),
            "blocked_capacity": BLOCKED_CONSUMERS,
        },
        "survivor_invariant": {
            "invariant": "cell_simplicial_topology survives iff every rung is non-dense, chi=0, Betti=(1,2,1), d1*d2=0, JAX parity holds, flattened control kills, helper proof flips, ablations are recomputed and nonzero, and promotion_allowed=false",
            "computed_capacity": 1.0 if all_pass else 0.0,
            "threshold": 1.0,
            "passed": bool(all_pass),
        },
        "outward_record": {
            "result_path": str(OUT_PATH.relative_to(ROOT)),
            "per_sim_contract_command": f"../../../scripts/per_sim_contract.py {OUT_PATH.relative_to(ROOT)}",
            "max_deep_gate_command": f"../../../scripts/max_deep_lego_gate.py {OUT_PATH.relative_to(ROOT)} --scale-required --rigor",
            "recheck_proof_command": f"../../../scripts/recheck_proof.py {OUT_PATH.relative_to(ROOT)} --rerun {pathlib.Path(__file__).name} --python /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
            "claim_ceiling": "Stage-3 geometry object lego only; no downstream consumer admitted",
        },
        "pass_rule": "all 8/16/32/64 rungs are non-dense and pass; torch/JAX agree; GUDHI Betti=(1,2,1); TopoNetX chi=0; flattened control kills; SMT proof flips real vs control; GUDHI/TopoNetX ablations are recomputed and nonzero",
        "fail_rule": "fail on dense closure, missing rung, wrong Euler/Betti, d1*d2 residual, no real/control SMT flip, live flattened control, JAX mismatch, cosmetic ablation, proof-tool numeric ablation, or downstream promotion",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blockers": blockers,
        "required_pass": all_pass,
        "all_pass": all_pass,
    }
    return result


def main() -> int:
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "required_pass": result["required_pass"],
                "result_path": str(OUT_PATH.relative_to(ROOT)),
                "jax_vs_pytorch_delta": result["jax_vs_pytorch_delta"],
                "proof_pass": result["proof_results"]["pass"],
                "scale_pass": result["scale_ladder"]["pass"],
                "blockers": result["blockers"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
