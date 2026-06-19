#!/usr/bin/env python3
"""Source-derived incidence packet for the fiber cover topology guard repair."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


SIM_ID = "fiber_cover_incidence_structure_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

FIBER_V1_DIR = ROOT / "system_v6" / "sims" / "fiber_augmented_cover_v1"
TOPOLOGY_GUARD_DIR = ROOT / "system_v6" / "sims" / "topology_parity_cell_model_v1"
SCRIPTS_DIR = ROOT / "scripts"
for path in (FIBER_V1_DIR, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402
import fiber_augmented_cover_v1_common as cover_v1_common  # noqa: E402


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "scratch_diagnostic_committed_incidence_structure_plumbing_only_no_betti"
SOURCE_COVER_COMMIT = "80860aa4f"
REJECT_GUARD_COMMIT = "0207fecaf"

TOOL_MANIFEST = {
    "fiber_augmented_cover_v1_common": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source of committed 33-cell carrier, 198 transition rows, |F|=3, and seam shifts",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing deterministic cycle enumeration, sparse boundary composition, hashing, and JSON serialization",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "G.2a post-audit-idempotent builder/audit boundary gate from birth",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "fiber_augmented_cover_v1_common": "load_bearing",
    "python_stdlib": "load_bearing",
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


def edge_phase_from_cover_edge(row: dict[str, Any]) -> int:
    return int(row["src"]) % cover_v1_common.FIBER_PHASE_COUNT


def carrier_and_cover() -> tuple[dict[str, Any], dict[str, Any]]:
    carrier = cover_v1_common.parent_objects()["carrier"]
    cover = cover_v1_common.build_cover(zero_shift=False)
    return carrier, cover


def derive_directed_4_cycle_faces(carrier: dict[str, Any], cover: dict[str, Any]) -> list[dict[str, Any]]:
    cells_by_id = {int(row["cell_id"]): row for row in carrier["cells"]}
    edge_by_id = {int(row["edge_id"]): row for row in carrier["edges"]}
    shift_by_edge = {int(row["projection_edge_id"]): int(row["fiber_phase_shift_steps"]) for row in cover["chart_transition_rows"]}
    adjacency: dict[int, list[tuple[int, int, str]]] = defaultdict(list)
    for row in carrier["edges"]:
        src = int(row["src"])
        dst = int(row["dst"])
        if src == dst:
            continue
        adjacency[src].append((dst, int(row["edge_id"]), str(row.get("generator"))))

    seen: set[tuple[int, int, int, int]] = set()
    faces: list[dict[str, Any]] = []
    for a in sorted(cells_by_id):
        for b, eab, gab in sorted(adjacency[a]):
            for c, ebc, gbc in sorted(adjacency[b]):
                if c in {a, b}:
                    continue
                for d, ecd, gcd in sorted(adjacency[c]):
                    if d in {a, b, c}:
                        continue
                    for a2, eda, gda in sorted(adjacency[d]):
                        if a2 != a:
                            continue
                        vertices = [a, b, c, d]
                        rotations = [tuple(vertices[i:] + vertices[:i]) for i in range(4)]
                        key = min(rotations)
                        if key in seen:
                            continue
                        seen.add(key)
                        edge_ids = [eab, ebc, ecd, eda]
                        generators = [gab, gbc, gcd, gda]
                        shifts = [shift_by_edge[edge_id] for edge_id in edge_ids]
                        includes_pole = any(cells_by_id[v]["coord_scaled"] in ([0, 0, -2], [0, 0, 2]) for v in vertices)
                        face_role = (
                            "pole_spanning_committed_4_cycle"
                            if includes_pole
                            else "band_quad_committed_R_x_4_cycle"
                            if set(generators) == {"R_x"}
                            else "mixed_generator_committed_4_cycle"
                        )
                        faces.append(
                            {
                                "face_id": f"base_face_{len(faces):03d}",
                                "vertices": vertices,
                                "vertex_coords_scaled": [cells_by_id[v]["coord_scaled"] for v in vertices],
                                "source_edge_ids": edge_ids,
                                "source_edge_rows": [
                                    {
                                        "edge_id": edge_id,
                                        "src": int(edge_by_id[edge_id]["src"]),
                                        "dst": int(edge_by_id[edge_id]["dst"]),
                                        "generator": edge_by_id[edge_id].get("generator"),
                                        "fiber_phase_shift_steps": shift_by_edge[edge_id],
                                    }
                                    for edge_id in edge_ids
                                ],
                                "generators": generators,
                                "fiber_phase_shift_steps": shifts,
                                "fiber_phase_shift_sum": sum(shifts),
                                "fiber_phase_shift_mod_fiber": sum(shifts) % cover_v1_common.FIBER_PHASE_COUNT,
                                "face_role": face_role,
                                "introduced": False,
                                "derivation_rule": "simple directed non-self 4-cycle in committed generator-labelled carrier adjacency",
                            }
                        )
    return faces


def build_base_incidence(carrier: dict[str, Any], faces: list[dict[str, Any]]) -> dict[str, Any]:
    c0 = [
        {
            "cell_id": int(row["cell_id"]),
            "label": f"base_vertex_{int(row['cell_id']):02d}",
            "coord_scaled": row["coord_scaled"],
            "nesting_band": "inner" if sum(int(v) * int(v) for v in row["coord_scaled"]) <= 1 else "outer",
            "pole_role": "south_pole" if row["coord_scaled"] == [0, 0, -2] else "north_pole" if row["coord_scaled"] == [0, 0, 2] else "non_pole",
        }
        for row in sorted(carrier["cells"], key=lambda item: int(item["cell_id"]))
    ]
    c1 = [
        {
            "edge_id": int(row["edge_id"]),
            "label": f"base_edge_{int(row['edge_id']):03d}",
            "src": int(row["src"]),
            "dst": int(row["dst"]),
            "generator": row.get("generator"),
        }
        for row in sorted(carrier["edges"], key=lambda item: int(item["edge_id"]))
    ]
    edge_index = {row["edge_id"]: idx for idx, row in enumerate(c1)}
    d1_entries: dict[tuple[int, int], int] = {}
    for col, edge in enumerate(c1):
        add_entry(d1_entries, edge["dst"], col, 1)
        add_entry(d1_entries, edge["src"], col, -1)
    d2_entries: dict[tuple[int, int], int] = {}
    for col, face in enumerate(faces):
        for edge_id in face["source_edge_ids"]:
            add_entry(d2_entries, edge_index[int(edge_id)], col, 1)
    boundaries = {
        "d1": sparse_matrix(len(c0), len(c1), d1_entries, "base_C1_to_C0"),
        "d2": sparse_matrix(len(c1), len(faces), d2_entries, "base_C2_to_C1"),
    }
    counts = {"C0": len(c0), "C1": len(c1), "C2": len(faces)}
    return {
        "cell_counts": counts,
        "euler_characteristic": counts["C0"] - counts["C1"] + counts["C2"],
        "cells": {"C0": c0, "C1": c1, "C2": faces},
        "boundary_matrices": boundaries,
        "chain_checks": chain_checks(boundaries),
        "chain_sha256": stable_sha256({"cells": {"C0": c0, "C1": c1, "C2": faces}, "boundaries": boundaries}),
    }


def build_total_space_incidence(carrier: dict[str, Any], cover: dict[str, Any], faces: list[dict[str, Any]]) -> dict[str, Any]:
    fiber_n = cover_v1_common.FIBER_PHASE_COUNT
    c0 = [
        {
            "cover_state_id": int(row["cover_state_id"]),
            "label": row["cover_state_label"],
            "projection_cell_id": int(row["projection_cell_id"]),
            "fiber_phase_slot": int(row["fiber_phase_slot"]),
        }
        for row in sorted(cover["states"], key=lambda item: int(item["cover_state_id"]))
    ]
    c1: list[dict[str, Any]] = []
    horizontal_index: dict[tuple[int, int], int] = {}
    for row in sorted(cover["base_lift_edges"], key=lambda item: (int(item["projection_edge_id"]), edge_phase_from_cover_edge(item))):
        phase = edge_phase_from_cover_edge(row)
        idx = len(c1)
        horizontal_index[(int(row["projection_edge_id"]), phase)] = idx
        c1.append(
            {
                "cell_type": "base_lift_edge",
                "label": row["cover_edge_id"],
                "src": int(row["src"]),
                "dst": int(row["dst"]),
                "projection_edge_id": int(row["projection_edge_id"]),
                "projection_src": int(row["projection_src"]),
                "projection_dst": int(row["projection_dst"]),
                "fiber_phase_slot": phase,
                "fiber_phase_shift_steps": int(row["fiber_phase_shift_steps"]),
            }
        )
    vertical_index: dict[tuple[int, int], int] = {}
    for row in sorted(cover["fiber_edges"], key=lambda item: (int(item["projection_src"]), int(item["src"]) % fiber_n)):
        phase = int(row["src"]) % fiber_n
        idx = len(c1)
        vertical_index[(int(row["projection_src"]), phase)] = idx
        c1.append(
            {
                "cell_type": "fiber_cycle_edge",
                "label": row["cover_edge_id"],
                "src": int(row["src"]),
                "dst": int(row["dst"]),
                "projection_cell_id": int(row["projection_src"]),
                "fiber_phase_slot": phase,
            }
        )

    d1_entries: dict[tuple[int, int], int] = {}
    for col, edge in enumerate(c1):
        add_entry(d1_entries, edge["dst"], col, 1)
        add_entry(d1_entries, edge["src"], col, -1)

    shift_by_edge = {int(row["projection_edge_id"]): int(row["fiber_phase_shift_steps"]) for row in cover["chart_transition_rows"]}
    edge_by_id = {int(row["edge_id"]): row for row in carrier["edges"]}
    c2: list[dict[str, Any]] = []
    base_face_index: dict[tuple[str, int], int] = {}
    edge_square_index: dict[tuple[int, int], int] = {}
    d2_entries: dict[tuple[int, int], int] = {}

    for face in faces:
        for phase in range(fiber_n):
            col = len(c2)
            base_face_index[(face["face_id"], phase)] = col
            c2.append(
                {
                    "cell_type": "lifted_base_2_cell",
                    "label": f"{face['face_id']}:phase:{phase}",
                    "base_face_id": face["face_id"],
                    "fiber_phase_slot": phase,
                    "source_edge_ids": face["source_edge_ids"],
                }
            )
            cursor = phase
            for edge_id in face["source_edge_ids"]:
                add_entry(d2_entries, horizontal_index[(int(edge_id), cursor)], col, 1)
                cursor = (cursor + shift_by_edge[int(edge_id)]) % fiber_n

    for edge in sorted(carrier["edges"], key=lambda item: int(item["edge_id"])):
        edge_id = int(edge["edge_id"])
        src = int(edge["src"])
        dst = int(edge["dst"])
        shift = shift_by_edge[edge_id]
        for phase in range(fiber_n):
            col = len(c2)
            edge_square_index[(edge_id, phase)] = col
            c2.append(
                {
                    "cell_type": "edge_fiber_square",
                    "label": f"base_edge_{edge_id:03d}:fiber_square_phase:{phase}",
                    "projection_edge_id": edge_id,
                    "projection_src": src,
                    "projection_dst": dst,
                    "fiber_phase_slot": phase,
                    "fiber_phase_shift_steps": shift,
                }
            )
            add_entry(d2_entries, horizontal_index[(edge_id, phase)], col, 1)
            add_entry(d2_entries, vertical_index[(dst, (phase + shift) % fiber_n)], col, 1)
            add_entry(d2_entries, horizontal_index[(edge_id, (phase + 1) % fiber_n)], col, -1)
            add_entry(d2_entries, vertical_index[(src, phase)], col, -1)

    c3: list[dict[str, Any]] = []
    d3_entries: dict[tuple[int, int], int] = {}
    for face in faces:
        for phase in range(fiber_n):
            col = len(c3)
            c3.append(
                {
                    "cell_type": "base_face_fiber_prism",
                    "label": f"{face['face_id']}:fiber_prism_phase:{phase}",
                    "base_face_id": face["face_id"],
                    "fiber_phase_slot": phase,
                }
            )
            cursor = phase
            for edge_id in face["source_edge_ids"]:
                add_entry(d3_entries, edge_square_index[(int(edge_id), cursor)], col, 1)
                cursor = (cursor + shift_by_edge[int(edge_id)]) % fiber_n
            add_entry(d3_entries, base_face_index[(face["face_id"], (phase + 1) % fiber_n)], col, 1)
            add_entry(d3_entries, base_face_index[(face["face_id"], phase)], col, -1)

    boundaries = {
        "d1": sparse_matrix(len(c0), len(c1), d1_entries, "total_C1_to_C0"),
        "d2": sparse_matrix(len(c1), len(c2), d2_entries, "total_C2_to_C1"),
        "d3": sparse_matrix(len(c2), len(c3), d3_entries, "total_C3_to_C2"),
    }
    counts = {"C0": len(c0), "C1": len(c1), "C2": len(c2), "C3": len(c3)}
    return {
        "cell_counts": counts,
        "euler_characteristic": counts["C0"] - counts["C1"] + counts["C2"] - counts["C3"],
        "gluing_source": "committed chart_transition_rows from fiber_augmented_cover_v1",
        "cell_construction_rule": "base cells x fiber cells with horizontal edges glued by committed seam shifts",
        "cells": {"C0": c0, "C1": c1, "C2": c2, "C3": c3},
        "boundary_matrices": boundaries,
        "chain_checks": chain_checks(boundaries),
        "chain_sha256": stable_sha256({"cell_counts": counts, "boundaries": boundaries}),
    }


def source_cover_summary(cover: dict[str, Any]) -> dict[str, Any]:
    witness = cover_v1_common.compute_bundle_witness(cover)
    return {
        "source_sim_id": "fiber_augmented_cover_v1",
        "commit": SOURCE_COVER_COMMIT,
        "cover_sha256": cover["cover_sha256"],
        "base_state_count": cover["base_state_count"],
        "base_edge_count": cover["base_edge_count"],
        "fiber_phase_count": cover["fiber_phase_count_per_cell"],
        "cover_state_count": cover["cover_state_count"],
        "base_lift_edge_count": cover["base_lift_edge_count"],
        "fiber_cycle_edge_count": cover["fiber_cycle_edge_count"],
        "cover_edge_count": cover["cover_edge_count"],
        "seam_loop_cell_ids": witness["base_loop_cell_ids"],
        "seam_loop_edge_pairs": witness["base_loop_edge_pairs"],
        "seam_lifted_shift_steps": [row["lifted_phase_increment_steps"] for row in witness["loop_transition_rows"]],
        "seam_projection_edge_ids": [row["projection_edge_id"] for row in witness["loop_transition_rows"]],
        "directed_winding": witness["directed_winding"],
        "witness_sha256": witness["witness_sha256"],
    }


def source_import_audit(cover: dict[str, Any], carrier: dict[str, Any]) -> dict[str, Any]:
    return {
        "reject_verdict": source_lock(
            TOPOLOGY_GUARD_DIR / "audit_verdict.md",
            "0207fecaf_rejects_packet_introduced_33_face_boundary_model",
            REJECT_GUARD_COMMIT,
        ),
        "fiber_augmented_cover_v1_source": source_lock(
            FIBER_V1_DIR / "fiber_augmented_cover_v1_common.py",
            "committed_cover_v1_construction_data_only",
            SOURCE_COVER_COMMIT,
        ),
        "fiber_augmented_cover_v1_result": source_lock(
            FIBER_V1_DIR / "results/fiber_augmented_cover_v1_results.json",
            "committed_cover_v1_result_hash_context",
            SOURCE_COVER_COMMIT,
        ),
        "carrier_transition_graph_sha256": carrier["transition_graph_sha256"],
        "carrier_source_rows_sha256": carrier["source_rows_sha256"],
        "cover_sha256": cover["cover_sha256"],
    }


def build_fiber_cover_incidence_structure_object() -> dict[str, Any]:
    carrier, cover = carrier_and_cover()
    faces = derive_directed_4_cycle_faces(carrier, cover)
    base = build_base_incidence(carrier, faces)
    total = build_total_space_incidence(carrier, cover, faces)
    boundary_ok = builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    derivation_incomplete_reasons = [
        "no committed exhaustive 2-cell incidence table was found in fiber_augmented_cover_v1",
        "coordinate-square and pole-cap mesh rules are not emitted because the committed generator adjacency did not supply those perimeter rows",
        "packet emits all simple committed directed non-self 4-cycles and blocks Betti consumption pending independent source-side 2-cell incidence admission",
    ]
    derivation = {
        "face_derivation_rule": "all simple committed directed non-self 4-cycles",
        "face_source": "committed generator-labelled carrier adjacency rows from fiber_augmented_cover_v1",
        "base_2_cell_count": len(faces),
        "derivation_introduced_count": 0,
        "derivation_incomplete": True,
        "derivation_incomplete_reasons": derivation_incomplete_reasons,
        "exhaustive_for_declared_cycle_rule": True,
        "exhaustive_as_base_s2_cell_structure": False,
        "face_derivation_table": [
            {
                "face_id": face["face_id"],
                "face_role": face["face_role"],
                "vertices": face["vertices"],
                "source_edge_ids": face["source_edge_ids"],
                "generators": face["generators"],
                "fiber_phase_shift_steps": face["fiber_phase_shift_steps"],
                "fiber_phase_shift_sum": face["fiber_phase_shift_sum"],
                "fiber_phase_shift_mod_fiber": face["fiber_phase_shift_mod_fiber"],
                "introduced": face["introduced"],
            }
            for face in faces
        ],
    }
    all_pass = bool(
        len(faces) == 12
        and derivation["derivation_introduced_count"] == 0
        and base["chain_checks"]["d_squared_zero"]
        and total["chain_checks"]["d_squared_zero"]
        and total["cell_counts"] == {"C0": 99, "C1": 693, "C2": 630, "C3": 36}
        and boundary_ok
    )
    return {
        "schema": f"{SIM_ID}.object.v0",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_import_audit": source_import_audit(cover, carrier),
        "source_cover": source_cover_summary(cover),
        "derivation_honesty": derivation,
        "base_incidence": base,
        "total_space_incidence": total,
        "betti_computed": False,
        "betti_lane_status": "blocked_until_source_side_exhaustive_2_cell_incidence_is_admitted",
        "consumer_boundary": {
            "intended_consumer": "topology_parity_cell_model_v2_or_guard_v2",
            "allowed_next_use": "consume explicit incidence and rerun guard checks without changing this builder packet",
            "blocked_use": "do not compute or cite Betti from this packet while derivation_incomplete is true",
            "builder_consumer_separation": True,
        },
        "allowed_claims": [
            "source-derived directed 4-cycle incidence rows were enumerated from committed cover-v1 carrier adjacency",
            "total-space chain cells were emitted as base cells x fiber cells with committed seam shifts",
            "sparse boundary matrices are explicit and hash-pinned",
            "boundary-of-boundary is zero for the emitted base and total-space complexes",
            "Euler characteristic is reported as a derived check only",
        ],
        "disallowed_claims": [
            "Betti computation",
            "homology certificate",
            "S3 or S2xS1 topology claim",
            "formal admission",
            "canonical by process",
            "physics/manifold/axis/bridge claim",
            "exhaustive base S2 cell structure",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "no_builder_audit_verdict": boundary_ok,
        "no_builder_audit_verdict_envelope_gate": boundary_ok,
        "builder_gates": {
            "file_disjoint_packet": True,
            "g2a_boundary_from_birth": boundary_ok,
            "boundary_helper_path": rel(SIM_DIR / f"{SIM_ID}_boundary.py"),
            "shared_boundary_helper": rel(SCRIPTS_DIR / "builder_audit_boundary.py"),
            "no_betti_computation": True,
            "derivation_introduced_count_must_be_zero": True,
        },
        "validator_expected_commands": [
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/{SIM_ID}/{SIM_ID}.py",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/{SIM_ID}/{SIM_ID}_envelope.py",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/{SIM_ID}/validate_{SIM_ID}.py",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/{SIM_ID}/tests",
        ],
        "all_pass": all_pass,
        "result_summary": {
            "base_2_cell_count": len(faces),
            "derivation_introduced_count": derivation["derivation_introduced_count"],
            "derivation_incomplete": derivation["derivation_incomplete"],
            "base_d_squared_zero": base["chain_checks"]["d_squared_zero"],
            "total_d_squared_zero": total["chain_checks"]["d_squared_zero"],
            "base_euler_characteristic": base["euler_characteristic"],
            "total_euler_characteristic": total["euler_characteristic"],
            "betti_computed": False,
            "betti_lane_status": "blocked",
            "all_pass": all_pass,
        },
    }


def build_envelope_payload() -> dict[str, Any]:
    payload = build_fiber_cover_incidence_structure_object()
    return {
        "schema": f"{SIM_ID}.envelope.v0",
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": now_z(),
        "result_path": rel(RESULT_PATH),
        "envelope_result_path": rel(ENVELOPE_RESULT_PATH),
        "all_pass": payload["all_pass"],
        "result_summary": payload["result_summary"],
        "source_cover": payload["source_cover"],
        "derivation_honesty": {
            key: value
            for key, value in payload["derivation_honesty"].items()
            if key != "face_derivation_table"
        },
        "base_chain_sha256": payload["base_incidence"]["chain_sha256"],
        "total_chain_sha256": payload["total_space_incidence"]["chain_sha256"],
        "boundary_matrix_hashes": {
            "base": {name: matrix["sha256"] for name, matrix in payload["base_incidence"]["boundary_matrices"].items()},
            "total": {name: matrix["sha256"] for name, matrix in payload["total_space_incidence"]["boundary_matrices"].items()},
        },
        "betti_computed": False,
        "betti_lane_status": payload["betti_lane_status"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "no_builder_audit_verdict": payload["no_builder_audit_verdict"],
        "no_builder_audit_verdict_envelope_gate": payload["no_builder_audit_verdict_envelope_gate"],
        "builder_gates": payload["builder_gates"],
    }


def write_result() -> dict[str, Any]:
    payload = build_fiber_cover_incidence_structure_object()
    write_json(RESULT_PATH, payload)
    return payload


def write_envelope_result() -> dict[str, Any]:
    payload = build_envelope_payload()
    write_json(ENVELOPE_RESULT_PATH, payload)
    return payload
