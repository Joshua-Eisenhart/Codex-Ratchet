#!/usr/bin/env python3
"""Cellular finite fiber-augmented cover v2.

This packet commits a source-side cellular sphere carrier before applying the
finite |F|=3 clutching cover and b6 law test machinery.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any


SIM_ID = "fiber_augmented_cover_v2"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

FIBER_V1_DIR = ROOT / "system_v6" / "sims" / "fiber_augmented_cover_v1"
INCIDENCE_V0_DIR = ROOT / "system_v6" / "sims" / "fiber_cover_incidence_structure_v0"
TOPOLOGY_GUARD_V1_DIR = ROOT / "system_v6" / "sims" / "topology_parity_cell_model_v1"
SCRIPTS_DIR = ROOT / "scripts"

for path in (FIBER_V1_DIR, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402
import fiber_augmented_cover_v1_common as v1_common  # noqa: E402


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "axis_readout_candidate_only + cellular_cover_law_test_v2_no_admission"
SCHEMA = f"{SIM_ID}.object.v1"

FIBER_PHASE_COUNT = 3
SOUTH_POLE = 14
NORTH_POLE = 18
SEAM_LOOP_CELLS = [20, 17, 12, 15]
SEAM_LIFTED_CLUTCHING_STEPS = [1, 1, 1, 0]
SEAM_STEP_BY_PAIR = dict(zip(zip(SEAM_LOOP_CELLS, SEAM_LOOP_CELLS[1:] + SEAM_LOOP_CELLS[:1]), SEAM_LIFTED_CLUTCHING_STEPS))
FIBER_POTENTIAL = {20: 0, 17: 1, 12: 2, 15: 0}

SOURCE_COMMITS = {
    "fiber_cover_incidence_structure_v0": "a04f76e1a",
    "fiber_augmented_cover_v1": "80860aa4f",
    "topology_parity_cell_model_v1_reject": "0207fecaf",
}

TOOL_MANIFEST = {
    "fiber_augmented_cover_v1_common": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source for |F|=3 axis realizations, v1 comparison row, and SMT row machinery",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing cellular sphere construction, sparse boundary composition, hashing, and binomial arithmetic",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing row-local erased-flip contradiction checks through v1 law machinery",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent row-local erased-flip contradiction checks through v1 law machinery",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "load-bearing G.2a post-audit-idempotent builder/audit boundary",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "fiber_augmented_cover_v1_common": "load_bearing",
    "python_stdlib": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "builder_audit_boundary": "load_bearing",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or None
    except Exception:
        return None


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"role": role, "path": rel(path), "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["commit_hint"] = commit_hint
    return row


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def add_entry(entries: dict[tuple[int, int], int], row: int, col: int, value: int) -> None:
    if value == 0:
        return
    key = (int(row), int(col))
    entries[key] = entries.get(key, 0) + int(value)
    if entries[key] == 0:
        del entries[key]


def sparse_matrix(rows: int, cols: int, entries: dict[tuple[int, int], int], role: str) -> dict[str, Any]:
    coo = [
        {"row": row, "col": col, "value": value}
        for (row, col), value in sorted(entries.items(), key=lambda item: (item[0][1], item[0][0]))
    ]
    return {
        "role": role,
        "format": "sparse_coo",
        "shape": [rows, cols],
        "entry_count": len(coo),
        "entries": coo,
        "sha256": stable_sha256({"shape": [rows, cols], "entries": coo}),
    }


def compose(left: dict[str, Any], right: dict[str, Any]) -> dict[tuple[int, int], int]:
    if left["shape"][1] != right["shape"][0]:
        raise ValueError(f"shape mismatch: {left['shape']} after {right['shape']}")
    left_by_col: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for item in left["entries"]:
        left_by_col[int(item["col"])].append((int(item["row"]), int(item["value"])))
    product: dict[tuple[int, int], int] = {}
    for item in right["entries"]:
        mid = int(item["row"])
        right_col = int(item["col"])
        right_value = int(item["value"])
        for left_row, left_value in left_by_col.get(mid, []):
            add_entry(product, left_row, right_col, left_value * right_value)
    return product


def chain_checks(boundaries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks: dict[str, Any] = {"d_squared_zero": True, "composition_errors": [], "composition_entry_counts": {}}
    for left_name, right_name in (("d1", "d2"), ("d2", "d3")):
        if left_name not in boundaries or right_name not in boundaries:
            continue
        product = compose(boundaries[left_name], boundaries[right_name])
        checks["composition_entry_counts"][f"{left_name}_{right_name}"] = len(product)
        if product:
            checks["d_squared_zero"] = False
            checks["composition_errors"].append(
                {
                    "composition": f"{left_name}*{right_name}",
                    "nonzero_entry_count": len(product),
                    "sample": [
                        {"row": row, "col": col, "value": value}
                        for (row, col), value in sorted(product.items())[:12]
                    ],
                }
            )
    return checks


def potential(vertex: int) -> int:
    return FIBER_POTENTIAL.get(int(vertex), 0)


def transition_residue(src: int, dst: int) -> int:
    return (potential(dst) - potential(src)) % FIBER_PHASE_COUNT


def band_cycle_vertices() -> list[int]:
    excluded = {SOUTH_POLE, NORTH_POLE, *SEAM_LOOP_CELLS}
    return [cell_id for cell_id in range(33) if cell_id not in excluded]


def face_vertices() -> list[list[int]]:
    inner = SEAM_LOOP_CELLS
    outer = band_cycle_vertices()
    faces: list[list[int]] = []
    for idx in range(len(inner)):
        faces.append([SOUTH_POLE, inner[idx], inner[(idx + 1) % len(inner)]])

    i = 0
    j = 0
    while i < len(inner) or j < len(outer):
        next_i = (i + 1) / len(inner) if i < len(inner) else 2.0
        next_j = (j + 1) / len(outer) if j < len(outer) else 2.0
        if next_i < next_j:
            faces.append([inner[i % len(inner)], outer[j % len(outer)], inner[(i + 1) % len(inner)]])
            i += 1
        elif next_j < next_i:
            faces.append([inner[i % len(inner)], outer[j % len(outer)], outer[(j + 1) % len(outer)]])
            j += 1
        else:
            faces.append([inner[i % len(inner)], outer[j % len(outer)], outer[(j + 1) % len(outer)], inner[(i + 1) % len(inner)]])
            i += 1
            j += 1

    for idx in range(len(outer)):
        faces.append([NORTH_POLE, outer[(idx + 1) % len(outer)], outer[idx]])
    return faces


@lru_cache(maxsize=1)
def parent_carrier() -> dict[str, Any]:
    return v1_common.parent_objects()["carrier"]


def cellular_edge_key(src: int, dst: int) -> tuple[int, int]:
    return (src, dst) if src < dst else (dst, src)


def face_role(index: int, vertices: list[int]) -> str:
    if vertices[0] == SOUTH_POLE:
        return "south_pole_cap_triangle"
    if vertices[0] == NORTH_POLE:
        return "north_pole_cap_triangle"
    return "band_quad" if len(vertices) == 4 else "band_triangle"


def build_cellular_base() -> dict[str, Any]:
    carrier = parent_carrier()
    cell_by_id = {int(row["cell_id"]): row for row in carrier["cells"]}
    raw_faces = face_vertices()

    edge_keys = sorted({cellular_edge_key(face[idx], face[(idx + 1) % len(face)]) for face in raw_faces for idx in range(len(face))})
    edge_id_by_key = {key: edge_id for edge_id, key in enumerate(edge_keys)}
    edges = [
        {
            "edge_id": edge_id,
            "src": src,
            "dst": dst,
            "label": f"cellular_edge_{edge_id:03d}",
            "fiber_phase_shift_steps": transition_residue(src, dst),
            "source": "v2_committed_cellular_sphere_1_skeleton",
            "in_v1_dense_graph": any(
                (int(row["src"]), int(row["dst"])) in {(src, dst), (dst, src)}
                for row in carrier["edges"]
            ),
        }
        for edge_id, (src, dst) in enumerate(edge_keys)
    ]
    edge_by_key = {cellular_edge_key(row["src"], row["dst"]): row for row in edges}

    edge_incidence: dict[int, list[str]] = defaultdict(list)
    faces = []
    d2_entries: dict[tuple[int, int], int] = {}
    for face_idx, vertices in enumerate(raw_faces):
        boundary = []
        transition_sum = 0
        for local_idx in range(len(vertices)):
            a = vertices[local_idx]
            b = vertices[(local_idx + 1) % len(vertices)]
            key = cellular_edge_key(a, b)
            edge = edge_by_key[key]
            sign = 1 if (a, b) == (edge["src"], edge["dst"]) else -1
            edge_incidence[int(edge["edge_id"])].append(f"face_{face_idx:03d}")
            transition_sum = (transition_sum + transition_residue(a, b)) % FIBER_PHASE_COUNT
            add_entry(d2_entries, int(edge["edge_id"]), face_idx, sign)
            boundary.append(
                {
                    "edge_id": int(edge["edge_id"]),
                    "traversal": [a, b],
                    "canonical_orientation": [edge["src"], edge["dst"]],
                    "orientation_sign": sign,
                    "fiber_transition_residue": transition_residue(a, b),
                }
            )
        faces.append(
            {
                "face_id": f"face_{face_idx:03d}",
                "vertices": vertices,
                "vertex_coords_scaled": [cell_by_id[v]["coord_scaled"] for v in vertices],
                "face_role": face_role(face_idx, vertices),
                "boundary": boundary,
                "fiber_transition_sum_mod_fiber": transition_sum,
                "committed_as_construction_data": True,
            }
        )

    d1_entries: dict[tuple[int, int], int] = {}
    for edge in edges:
        add_entry(d1_entries, edge["dst"], edge["edge_id"], 1)
        add_entry(d1_entries, edge["src"], edge["edge_id"], -1)
    boundaries = {
        "d1": sparse_matrix(33, len(edges), d1_entries, "cellular_base_C1_to_C0"),
        "d2": sparse_matrix(len(edges), len(faces), d2_entries, "cellular_base_C2_to_C1"),
    }
    seam_edges = []
    for src, dst in zip(SEAM_LOOP_CELLS, SEAM_LOOP_CELLS[1:] + SEAM_LOOP_CELLS[:1]):
        edge = edge_by_key[cellular_edge_key(src, dst)]
        seam_edges.append(
            {
                "cellular_edge_id": edge["edge_id"],
                "traversal": [src, dst],
                "canonical_orientation": [edge["src"], edge["dst"]],
                "fiber_transition_residue": transition_residue(src, dst),
                "lifted_clutching_step": SEAM_STEP_BY_PAIR[(src, dst)],
            }
        )
    vertices = [
        {
            "cell_id": int(row["cell_id"]),
            "label": f"base_vertex_{int(row['cell_id']):02d}",
            "coord_scaled": row["coord_scaled"],
            "cellular_role": (
                "south_pole"
                if int(row["cell_id"]) == SOUTH_POLE
                else "north_pole"
                if int(row["cell_id"]) == NORTH_POLE
                else "committed_seam_vertex"
                if int(row["cell_id"]) in SEAM_LOOP_CELLS
                else "band_vertex"
            ),
            "fiber_potential_mod_3": potential(int(row["cell_id"])),
        }
        for row in sorted(carrier["cells"], key=lambda item: int(item["cell_id"]))
    ]
    counts = {"C0": len(vertices), "C1": len(edges), "C2": len(faces)}
    edge_incidence_counts = Counter(len(value) for value in edge_incidence.values())
    face_size_counts = Counter(len(face["vertices"]) for face in faces)
    cellular_adjacency = []
    for edge in edges:
        incident = edge_incidence[int(edge["edge_id"])]
        if len(incident) == 2:
            cellular_adjacency.append(
                {
                    "shared_edge_id": edge["edge_id"],
                    "faces": incident,
                    "edge_vertices": [edge["src"], edge["dst"]],
                }
            )
    base = {
        "construction_status": "committed_cellular_sphere_mesh",
        "construction_rule": (
            "33 v1-labelled vertices; south pole cap over the committed seam loop; "
            "staircase band quads/triangles to the remaining 27-vertex band cycle; north pole cap"
        ),
        "cell_counts": counts,
        "euler_characteristic": counts["C0"] - counts["C1"] + counts["C2"],
        "euler_gate_passed": counts["C0"] - counts["C1"] + counts["C2"] == 2,
        "edge_incidence_counts": {str(key): value for key, value in sorted(edge_incidence_counts.items())},
        "face_size_counts": {str(key): value for key, value in sorted(face_size_counts.items())},
        "all_edges_incident_to_two_faces": set(edge_incidence_counts) == {2},
        "all_face_transition_sums_close_mod_fiber": all(face["fiber_transition_sum_mod_fiber"] == 0 for face in faces),
        "committed_seam_loop_cell_ids": SEAM_LOOP_CELLS,
        "committed_seam_lifted_steps": SEAM_LIFTED_CLUTCHING_STEPS,
        "committed_seam_edges": seam_edges,
        "band_cycle_cell_ids": band_cycle_vertices(),
        "cells": {"C0": vertices, "C1": edges, "C2": faces},
        "cellular_adjacency": cellular_adjacency,
        "boundary_matrices": boundaries,
        "chain_checks": chain_checks(boundaries),
        "v1_dense_graph_relation": {
            "v1_dense_graph_edge_count": int(carrier["edge_count"]),
            "cellular_edge_count": len(edges),
            "v1_dense_graph_role": "distinguishability/generator transition graph used by earlier axis and cover-v1 machinery",
            "v2_cellular_adjacency_role": "surface cell adjacency derived from committed v2 faces sharing cellular edges",
            "objects_have_different_roles": True,
            "fence": "The v1 198-edge graph remains valid as a distinguishability graph; it is not the surface mesh. The v2 92-edge cellular 1-skeleton is the committed surface structure for this packet.",
        },
    }
    base["chain_sha256"] = stable_sha256(
        {
            "cell_counts": counts,
            "cells": base["cells"],
            "boundary_hashes": {name: matrix["sha256"] for name, matrix in boundaries.items()},
        }
    )
    return base


def transition_shift_for_edge(edge: dict[str, Any], *, zero_shift: bool = False) -> int:
    return 0 if zero_shift else int(edge["fiber_phase_shift_steps"]) % FIBER_PHASE_COUNT


def build_cellular_cover(base: dict[str, Any], *, zero_shift: bool = False) -> dict[str, Any]:
    states = []
    for vertex in base["cells"]["C0"]:
        cell_id = int(vertex["cell_id"])
        parent_cell = next(row for row in parent_carrier()["cells"] if int(row["cell_id"]) == cell_id)
        for phase_slot in range(FIBER_PHASE_COUNT):
            axis3 = v1_common.axis3_predicate_row(parent_cell, phase_slot)
            states.append(
                {
                    "cover_state_id": cell_id * FIBER_PHASE_COUNT + phase_slot,
                    "cover_state_label": f"c{cell_id:02d}:cellular_phase_{phase_slot}",
                    "projection_cell_id": cell_id,
                    "base_coord_scaled": vertex["coord_scaled"],
                    "fiber_phase_slot": phase_slot,
                    "fiber_phase_label": v1_common.phase_label(phase_slot),
                    "fiber_phase_radians": v1_common.phase_value(phase_slot),
                    "axis3_loop_family": axis3["pinned_family_formula"],
                    "axis3_predicate": axis3,
                }
            )
    horizontal_edges = []
    transition_rows = []
    for edge in base["cells"]["C1"]:
        shift = transition_shift_for_edge(edge, zero_shift=zero_shift)
        transition_rows.append(
            {
                "cellular_edge_id": int(edge["edge_id"]),
                "src": int(edge["src"]),
                "dst": int(edge["dst"]),
                "fiber_phase_shift_steps": shift,
                "transition_family": "zero_shift_product" if zero_shift else "cellular_degree_one_cocycle",
            }
        )
        for phase in range(FIBER_PHASE_COUNT):
            horizontal_edges.append(
                {
                    "cover_edge_id": f"cellular_base:{edge['edge_id']}:phase:{phase}:shift:{shift}",
                    "edge_type": "cellular_base_lift",
                    "src": int(edge["src"]) * FIBER_PHASE_COUNT + phase,
                    "dst": int(edge["dst"]) * FIBER_PHASE_COUNT + ((phase + shift) % FIBER_PHASE_COUNT),
                    "cellular_edge_id": int(edge["edge_id"]),
                    "projection_src": int(edge["src"]),
                    "projection_dst": int(edge["dst"]),
                    "fiber_phase_slot": phase,
                    "fiber_phase_shift_steps": shift,
                }
            )
    fiber_edges = []
    for vertex in base["cells"]["C0"]:
        cell_id = int(vertex["cell_id"])
        for phase in range(FIBER_PHASE_COUNT):
            fiber_edges.append(
                {
                    "cover_edge_id": f"fiber:{cell_id}:{phase}",
                    "edge_type": "fiber_cycle",
                    "src": cell_id * FIBER_PHASE_COUNT + phase,
                    "dst": cell_id * FIBER_PHASE_COUNT + ((phase + 1) % FIBER_PHASE_COUNT),
                    "projection_cell_id": cell_id,
                    "fiber_phase_slot": phase,
                }
            )
    cover = {
        "cover_kind": "cellular_degree_one_cover" if not zero_shift else "cellular_zero_shift_product_regression",
        "base_state_count": 33,
        "cellular_base_edge_count": len(base["cells"]["C1"]),
        "fiber_phase_count_per_cell": FIBER_PHASE_COUNT,
        "cover_state_count": len(states),
        "cellular_base_lift_edge_count": len(horizontal_edges),
        "fiber_cycle_edge_count": len(fiber_edges),
        "cover_edge_count": len(horizontal_edges) + len(fiber_edges),
        "states": states,
        "cellular_base_lift_edges": horizontal_edges,
        "fiber_edges": fiber_edges,
        "chart_transition_rows": transition_rows,
        "base_lift_phase_shift_counts": {str(key): value for key, value in sorted(Counter(row["fiber_phase_shift_steps"] for row in horizontal_edges).items())},
    }
    cover["cover_sha256"] = stable_sha256(
        {
            "states": [
                {
                    "cover_state_id": row["cover_state_id"],
                    "projection_cell_id": row["projection_cell_id"],
                    "fiber_phase_slot": row["fiber_phase_slot"],
                    "axis3_loop_family": row["axis3_loop_family"],
                }
                for row in states
            ],
            "transition_rows": transition_rows,
            "cover_edge_count": cover["cover_edge_count"],
        }
    )
    return cover


def compute_bundle_witness(base: dict[str, Any], cover: dict[str, Any], *, zero_shift: bool = False) -> dict[str, Any]:
    transition_by_key = {
        frozenset((row["src"], row["dst"])): row
        for row in cover["chart_transition_rows"]
    }
    loop_rows = []
    total = 0
    for src, dst in zip(SEAM_LOOP_CELLS, SEAM_LOOP_CELLS[1:] + SEAM_LOOP_CELLS[:1]):
        row = transition_by_key[frozenset((src, dst))]
        if zero_shift:
            lifted_step = 0
        else:
            lifted_step = SEAM_STEP_BY_PAIR[(src, dst)]
        total += lifted_step
        loop_rows.append(
            {
                "src": src,
                "dst": dst,
                "cellular_edge_id": row["cellular_edge_id"],
                "canonical_orientation": [row["src"], row["dst"]],
                "fiber_phase_shift_steps_mod_fiber": 0 if zero_shift else transition_residue(src, dst),
                "lifted_phase_increment_steps": lifted_step,
            }
        )
    winding = total // FIBER_PHASE_COUNT if total % FIBER_PHASE_COUNT == 0 else None
    return {
        "loop_name": "committed_v2_cellular_equatorial_loop",
        "base_loop_cell_ids": SEAM_LOOP_CELLS,
        "fiber_phase_count": FIBER_PHASE_COUNT,
        "loop_transition_rows": loop_rows,
        "total_lifted_phase_shift_steps": total,
        "directed_winding": winding,
        "euler_class_witness": winding,
        "nontrivial_gate_passed": winding in {-1, 1},
        "trivial_product_witness": winding == 0,
        "witness_rule": "sum lifted fiber phase transitions around committed cellular seam divided by |F|; +/-1 admits law rows, 0 refuses them",
        "witness_sha256": stable_sha256(loop_rows),
        "cellular_base_sha256": base["chain_sha256"],
    }


def quotient_projection(cover: dict[str, Any]) -> dict[str, Any]:
    fiber_sizes = Counter(int(row["projection_cell_id"]) for row in cover["states"])
    return {
        "map": "pi_v2_cover_to_committed_base_axis_cell(cover_state_id)=projection_cell_id",
        "projection_total": len(fiber_sizes) == 33 and sum(fiber_sizes.values()) == cover["cover_state_count"],
        "uniform_fiber_size": set(fiber_sizes.values()) == {FIBER_PHASE_COUNT},
        "fiber_size_by_cell": {str(key): value for key, value in sorted(fiber_sizes.items())},
        "target_axis_realization_scope": "committed v1/base axis realization rows where defined; cellular adjacency is v2-local",
        "projection_sha256": stable_sha256(
            [
                {
                    "cover_state_id": row["cover_state_id"],
                    "projection_cell_id": row["projection_cell_id"],
                    "fiber_phase_slot": row["fiber_phase_slot"],
                }
                for row in cover["states"]
            ]
        ),
    }


def traversal_square(base: dict[str, Any], traversal_src: int, traversal_dst: int, phase: int) -> tuple[int, int, int]:
    edge = next(
        row
        for row in base["cells"]["C1"]
        if {int(row["src"]), int(row["dst"])} == {int(traversal_src), int(traversal_dst)}
    )
    shift = int(edge["fiber_phase_shift_steps"])
    if (traversal_src, traversal_dst) == (edge["src"], edge["dst"]):
        return 1, phase, (phase + shift) % FIBER_PHASE_COUNT
    edge_phase = (phase - shift) % FIBER_PHASE_COUNT
    return -1, edge_phase, edge_phase


def build_total_space_cellular_structure(base: dict[str, Any], cover: dict[str, Any]) -> dict[str, Any]:
    c0 = [
        {
            "cover_state_id": int(row["cover_state_id"]),
            "label": row["cover_state_label"],
            "projection_cell_id": int(row["projection_cell_id"]),
            "fiber_phase_slot": int(row["fiber_phase_slot"]),
        }
        for row in sorted(cover["states"], key=lambda item: int(item["cover_state_id"]))
    ]
    c1 = []
    horizontal_index: dict[tuple[int, int], int] = {}
    for row in sorted(cover["cellular_base_lift_edges"], key=lambda item: (int(item["cellular_edge_id"]), int(item["fiber_phase_slot"]))):
        idx = len(c1)
        horizontal_index[(int(row["cellular_edge_id"]), int(row["fiber_phase_slot"]))] = idx
        c1.append(row)
    vertical_index: dict[tuple[int, int], int] = {}
    for row in sorted(cover["fiber_edges"], key=lambda item: (int(item["projection_cell_id"]), int(item["fiber_phase_slot"]))):
        idx = len(c1)
        vertical_index[(int(row["projection_cell_id"]), int(row["fiber_phase_slot"]))] = idx
        c1.append(row)

    d1_entries: dict[tuple[int, int], int] = {}
    for col, edge in enumerate(c1):
        add_entry(d1_entries, int(edge["dst"]), col, 1)
        add_entry(d1_entries, int(edge["src"]), col, -1)

    c2 = []
    base_face_index: dict[tuple[str, int], int] = {}
    edge_square_index: dict[tuple[int, int], int] = {}
    d2_entries: dict[tuple[int, int], int] = {}

    for face in base["cells"]["C2"]:
        for phase in range(FIBER_PHASE_COUNT):
            col = len(c2)
            base_face_index[(face["face_id"], phase)] = col
            c2.append(
                {
                    "cell_type": "lifted_cellular_base_2_cell",
                    "label": f"{face['face_id']}:phase:{phase}",
                    "base_face_id": face["face_id"],
                    "fiber_phase_slot": phase,
                }
            )
            cursor = phase
            for boundary in face["boundary"]:
                coeff, edge_phase, next_phase = traversal_square(base, boundary["traversal"][0], boundary["traversal"][1], cursor)
                add_entry(d2_entries, horizontal_index[(int(boundary["edge_id"]), edge_phase)], col, coeff)
                cursor = next_phase
            if cursor != phase:
                raise ValueError(f"lifted face failed to close: {face['face_id']} phase {phase} -> {cursor}")

    for edge in base["cells"]["C1"]:
        edge_id = int(edge["edge_id"])
        src = int(edge["src"])
        dst = int(edge["dst"])
        shift = int(edge["fiber_phase_shift_steps"])
        for phase in range(FIBER_PHASE_COUNT):
            col = len(c2)
            edge_square_index[(edge_id, phase)] = col
            c2.append(
                {
                    "cell_type": "cellular_edge_fiber_square",
                    "label": f"cellular_edge_{edge_id:03d}:fiber_square_phase:{phase}",
                    "cellular_edge_id": edge_id,
                    "projection_src": src,
                    "projection_dst": dst,
                    "fiber_phase_slot": phase,
                    "fiber_phase_shift_steps": shift,
                }
            )
            add_entry(d2_entries, horizontal_index[(edge_id, phase)], col, 1)
            add_entry(d2_entries, vertical_index[(dst, (phase + shift) % FIBER_PHASE_COUNT)], col, 1)
            add_entry(d2_entries, horizontal_index[(edge_id, (phase + 1) % FIBER_PHASE_COUNT)], col, -1)
            add_entry(d2_entries, vertical_index[(src, phase)], col, -1)

    c3 = []
    d3_entries: dict[tuple[int, int], int] = {}
    for face in base["cells"]["C2"]:
        for phase in range(FIBER_PHASE_COUNT):
            col = len(c3)
            c3.append(
                {
                    "cell_type": "cellular_base_face_fiber_prism",
                    "label": f"{face['face_id']}:fiber_prism_phase:{phase}",
                    "base_face_id": face["face_id"],
                    "fiber_phase_slot": phase,
                }
            )
            cursor = phase
            for boundary in face["boundary"]:
                coeff, edge_phase, next_phase = traversal_square(base, boundary["traversal"][0], boundary["traversal"][1], cursor)
                add_entry(d3_entries, edge_square_index[(int(boundary["edge_id"]), edge_phase)], col, coeff)
                cursor = next_phase
            add_entry(d3_entries, base_face_index[(face["face_id"], (phase + 1) % FIBER_PHASE_COUNT)], col, 1)
            add_entry(d3_entries, base_face_index[(face["face_id"], phase)], col, -1)

    boundaries = {
        "d1": sparse_matrix(len(c0), len(c1), d1_entries, "total_cellular_C1_to_C0"),
        "d2": sparse_matrix(len(c1), len(c2), d2_entries, "total_cellular_C2_to_C1"),
        "d3": sparse_matrix(len(c2), len(c3), d3_entries, "total_cellular_C3_to_C2"),
    }
    counts = {"C0": len(c0), "C1": len(c1), "C2": len(c2), "C3": len(c3)}
    total = {
        "cell_counts": counts,
        "euler_characteristic": counts["C0"] - counts["C1"] + counts["C2"] - counts["C3"],
        "cell_construction_rule": "v2 cellular base cells x pinned |F|=3 fiber cells, glued by the committed cellular degree-1 cocycle",
        "cells": {"C0": c0, "C1": c1, "C2": c2, "C3": c3},
        "boundary_matrices": boundaries,
        "chain_checks": chain_checks(boundaries),
    }
    total["chain_sha256"] = stable_sha256({"cell_counts": counts, "boundary_hashes": {name: matrix["sha256"] for name, matrix in boundaries.items()}})
    return total


def relation_summary(table: list[dict[str, Any]], witness: dict[str, Any]) -> dict[str, Any]:
    summary = v1_common.relation_summary(table, witness)
    status_map = {
        "holds_on_nontrivial_faithful_cover": "holds_on_cellular_nontrivial_cover",
        "fails_on_nontrivial_faithful_cover": "fails_on_cellular_nontrivial_cover",
        "inconclusive_no_nonneutral_rows": "inconclusive_no_nonneutral_rows",
    }
    summary["table_kind"] = "faithful_cellular_nontrivial_fiber_augmented_cover_table"
    summary["law_test_status"] = status_map[summary["law_test_status"]]
    summary["carrier_note"] = "same 99 cover-state law rows are pulled onto the v2 committed cellular base; cellular adjacency is now surface-structural, not the v1 dense graph"
    return summary


def zero_shift_v2_regression(base: dict[str, Any]) -> dict[str, Any]:
    cover = build_cellular_cover(base, zero_shift=True)
    witness = compute_bundle_witness(base, cover, zero_shift=True)
    return {
        "control_role": "zero_shift_v2_cover_regression",
        "cover_sha256": cover["cover_sha256"],
        "bundle_witness": witness,
        "law_table_ran": False,
        "law_table_refused": not witness["nontrivial_gate_passed"],
        "refusal_reason": "witness gate requires directed winding +/-1 before law rows",
    }


def v1_comparison_row() -> dict[str, Any]:
    result_path = FIBER_V1_DIR / "results/fiber_augmented_cover_v1_results.json"
    if result_path.exists():
        law = load_json(result_path)["b6_law_test"]
    else:
        law = v1_common.build_fiber_augmented_cover_object()["b6_law_test"]
    return {
        "source": rel(result_path),
        "carrier": "fiber_augmented_cover_v1 faithful nontrivial 33x3 cover over dense-graph/source carrier",
        "agreement_count": law["agreement_count"],
        "sample_total": law["sample_total"],
        "violation_count": law["violation_count"],
        "binomial_p_two_sided": law["binomial_p_two_sided"],
        "classification": law["chance_classification"],
        "comparison_note": "v1 result is the at-chance comparison row; v2 reruns the law on the cleaner committed cellular carrier",
    }


def controls(base: dict[str, Any], table: list[dict[str, Any]]) -> dict[str, Any]:
    carried = v1_common.controls(table)
    carried["zero_shift_v2_cover_regression"] = zero_shift_v2_regression(base)
    carried["v1_comparison_row"] = v1_comparison_row()
    return carried


def source_import_audit(base: dict[str, Any]) -> dict[str, Any]:
    return {
        "incidence_packet_honest_block": source_lock(
            INCIDENCE_V0_DIR / "results/fiber_cover_incidence_structure_v0_results.json",
            "a04f76e1a_honest_block_dense_graph_not_surface_mesh_base_euler_minus_153_only_12_derivable_2cells",
            SOURCE_COMMITS["fiber_cover_incidence_structure_v0"],
        ),
        "cover_v1_source": source_lock(
            FIBER_V1_DIR / "fiber_augmented_cover_v1_common.py",
            "80860aa4f_fiber_machinery_and_law_table_source",
            SOURCE_COMMITS["fiber_augmented_cover_v1"],
        ),
        "cover_v1_audit": source_lock(
            FIBER_V1_DIR / "audit_verdict.md",
            "80860aa4f_audited_winding_gate_and_at_chance_law_result",
            SOURCE_COMMITS["fiber_augmented_cover_v1"],
        ),
        "topology_guard_v1_reject": source_lock(
            TOPOLOGY_GUARD_V1_DIR / "audit_verdict.md",
            "0207fecaf_reject_packet_introduced_cell_model",
            SOURCE_COMMITS["topology_parity_cell_model_v1_reject"],
        ),
        "audit_standards_codex": source_lock(
            ROOT / "system_v6/receipts/audit_standards_codex_v1.md",
            "G.2a_from_birth_and_standards_codex",
        ),
        "cellular_base_chain_sha256": base["chain_sha256"],
    }


@lru_cache(maxsize=1)
def build_fiber_augmented_cover_v2_object() -> dict[str, Any]:
    base = build_cellular_base()
    cover = build_cellular_cover(base, zero_shift=False)
    witness = compute_bundle_witness(base, cover)
    if not witness["nontrivial_gate_passed"]:
        raise RuntimeError("v2 construction failed witness gate")
    total_space = build_total_space_cellular_structure(base, cover)
    table = v1_common.relation_rows(cover)
    summary = relation_summary(table, witness)
    variants = v1_common.sign_variant_table(table)
    faith = v1_common.faithfulness_rows(cover, table)
    ctrl = controls(base, table)
    smt = v1_common.smt_rows(table)
    boundary_ok = builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    all_pass = bool(
        base["euler_gate_passed"]
        and base["all_edges_incident_to_two_faces"]
        and base["all_face_transition_sums_close_mod_fiber"]
        and base["chain_checks"]["d_squared_zero"]
        and witness["directed_winding"] == 1
        and total_space["chain_checks"]["d_squared_zero"]
        and faith["axis0"]["projects_to_committed_axis0"]
        and faith["axis3"]["source_backed_equivalent_adapter"]
        and faith["axis3"]["predicate_mismatch_count"] == 0
        and faith["axis6"]["projects_to_committed_axis6"]
        and len(variants) == 8
        and ctrl["zero_shift_v2_cover_regression"]["law_table_refused"]
        and ctrl["scrambled_control"]["ran"]
        and ctrl["convention_flip_control"]["ran"]
        and all(row["verdict"] == "unsat" and row["erased_flip_verdict"] == "sat" for row in smt.values())
        and boundary_ok
    )
    return {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "state_object_id": f"{SIM_ID}:{stable_sha256({'base': base['chain_sha256'], 'cover': cover['cover_sha256'], 'law': summary})}",
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "engine_contract": {
            "mode": "single_python_cellular_chain_packet",
            "three_engine_scoped": False,
            "three_engine_not_scoped_reason": "v2 builds one committed cellular carrier and emits consumer chain complexes; no independent Julia/JAX/PyTorch parity claim is made in this packet",
        },
        "source_import_audit": source_import_audit(base),
        "cellular_base": base,
        "cover": cover,
        "bundle_witness": witness,
        "quotient_projection": quotient_projection(cover),
        "total_space_cellular_structure": total_space,
        "faithfulness": faith,
        "relation_table": table,
        "relation_sign_vector": v1_common.sign_vector(table),
        "relation_sign_vector_sha256": stable_sha256(v1_common.sign_vector(table)),
        "b6_law_test": summary,
        "sign_variant_table": variants,
        "controls": ctrl,
        "smt_rows": smt,
        "betti_computed": False,
        "betti_lane_status": "chain_complexes_emitted_for_guard_v2_consumer_no_betti_in_builder_packet",
        "consumer_boundary": {
            "intended_consumer": "fiber_augmented_cover_v2_guard_or_betti_consumer",
            "allowed_next_use": "consume hash-pinned base and total-space cellular chain complexes",
            "blocked_use": "do not cite Betti, homology, S3, S2xS1, manifold, bridge, physics, or admission from this builder packet",
            "builder_consumer_separation": True,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "no_builder_audit_verdict": boundary_ok,
        "no_builder_audit_verdict_envelope_gate": boundary_ok,
        "builder_gates": {
            "file_disjoint_packet": True,
            "g2a_boundary_from_birth": boundary_ok,
            "cellular_base_euler_gate_chi_2": base["euler_gate_passed"],
            "witness_gate_before_law_table": True,
            "d_squared_zero_gate": total_space["chain_checks"]["d_squared_zero"],
            "no_betti_computation": True,
            "boundary_helper_path": rel(SIM_DIR / f"{SIM_ID}_boundary.py"),
            "shared_boundary_helper": rel(SCRIPTS_DIR / "builder_audit_boundary.py"),
        },
        "allowed_claims": [
            "v2 commits a 33-vertex cellular sphere mesh as construction data",
            "v2 computes a degree-1 |F|=3 cellular cover on that mesh with winding witness 1",
            "v2 emits hash-pinned base and total-space cellular chain complexes with d^2=0",
            "v2 recomputes Axis0, Axis3, and Axis6 faithfulness obligations on the cellular cover mapping",
            "v2 runs the b6=-b0*b3 law table and eight sign variants at scratch-diagnostic ceiling",
        ],
        "disallowed_claims": [
            "Betti computation",
            "homology certificate",
            "S3 or S2xS1 topology claim",
            "formal admission",
            "canonical by process",
            "axis independence proof",
            "bridge or axis-level closure",
            "physics/manifold claim",
            "global disproof of b6 law",
        ],
        "blocked_consumers": [
            "formal_admission",
            "axis_triple_relation_admission",
            "homology_certificate",
            "bridge_or_physics_or_manifold_claim",
        ],
        "divergence_log": (
            "v2 corrects the incidence-v0/topology-v1 blocker by committing a cellular sphere mesh in construction data. "
            "The v1 dense graph remains a distinguishability object, not the v2 surface mesh."
        ),
        "validator_expected_commands": [
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/{SIM_ID}/{SIM_ID}.py",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/{SIM_ID}/{SIM_ID}_envelope.py",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/{SIM_ID}/validate_{SIM_ID}.py",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/{SIM_ID}/tests",
        ],
        "all_pass": all_pass,
        "result_summary": {
            "base_euler_characteristic": base["euler_characteristic"],
            "base_cell_counts": base["cell_counts"],
            "total_cell_counts": total_space["cell_counts"],
            "directed_winding": witness["directed_winding"],
            "law_agreement_count": summary["agreement_count"],
            "law_sample_total": summary["sample_total"],
            "law_status": summary["law_test_status"],
            "v1_comparison": ctrl["v1_comparison_row"],
            "betti_computed": False,
            "all_pass": all_pass,
        },
    }


def build_envelope_payload() -> dict[str, Any]:
    payload = build_fiber_augmented_cover_v2_object()
    return {
        **payload,
        "envelope_result_kind": "builder_envelope",
        "envelope_written_at": now_z(),
        "result_path": rel(RESULT_PATH),
        "envelope_result_path": rel(ENVELOPE_RESULT_PATH),
        "boundary_matrix_hashes": {
            "base": {name: matrix["sha256"] for name, matrix in payload["cellular_base"]["boundary_matrices"].items()},
            "total": {name: matrix["sha256"] for name, matrix in payload["total_space_cellular_structure"]["boundary_matrices"].items()},
        },
    }


def write_result() -> dict[str, Any]:
    payload = build_fiber_augmented_cover_v2_object()
    write_json(RESULT_PATH, payload)
    return payload


def write_envelope_result() -> dict[str, Any]:
    payload = build_envelope_payload()
    write_json(ENVELOPE_RESULT_PATH, payload)
    return payload
