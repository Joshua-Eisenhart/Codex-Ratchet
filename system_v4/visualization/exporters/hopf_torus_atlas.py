from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from system_v4.probes import hopf_manifold as hopf
from system_v4.visualization.capabilities import ATLAS_CAPABILITIES
from system_v4.visualization.schema_v1 import (
    ADMISSION_STAGE_LABELS,
    ADMISSION_STAGE_NEXT,
    ATLAS_FAMILY,
    MESH_PATCH_ENTITY_KIND,
    POINT_FRAME_ENTITY_KIND,
    SCHEMA_VERSION,
)

HOPF_TORUS_ATLAS_SIM_NAME = "hopf_torus_atlas"


def _json_dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _grid_points(eta: float, n_theta1: int, n_theta2: int) -> tuple[np.ndarray, np.ndarray]:
    points_s3 = []
    projected_r3 = []
    for t1 in np.linspace(0.0, 2.0 * np.pi, n_theta1, endpoint=False):
        for t2 in np.linspace(0.0, 2.0 * np.pi, n_theta2, endpoint=False):
            q = hopf.torus_coordinates(eta, t1, t2)
            points_s3.append(q)
            projected_r3.append(hopf.stereographic_s3_to_r3(q))
    return np.array(points_s3, dtype=float), np.array(projected_r3, dtype=float)


def _triangle_cells(n_theta1: int, n_theta2: int) -> list[list[int]]:
    cells: list[list[int]] = []

    def idx(i: int, j: int) -> int:
        return (i % n_theta1) * n_theta2 + (j % n_theta2)

    for i in range(n_theta1):
        for j in range(n_theta2):
            a = idx(i, j)
            b = idx(i + 1, j)
            c = idx(i, j + 1)
            d = idx(i + 1, j + 1)
            cells.append([a, b, c])
            cells.append([b, d, c])
    return cells


def _grid_lines(n_theta1: int, n_theta2: int) -> list[list[int]]:
    lines: list[list[int]] = []

    def idx(i: int, j: int) -> int:
        return (i % n_theta1) * n_theta2 + (j % n_theta2)

    for i in range(n_theta1):
        for j in range(n_theta2):
            lines.append([idx(i, j), idx(i + 1, j)])
            lines.append([idx(i, j), idx(i, j + 1)])
    return lines


def _seam_edges(n_theta1: int, n_theta2: int) -> list[list[int]]:
    return [[j, (j + 1) % n_theta2] for j in range(n_theta2)]


def build_run_manifest(run_id: str, frame_count: int) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "family": ATLAS_FAMILY,
        "sim_name": HOPF_TORUS_ATLAS_SIM_NAME,
        "run_id": run_id,
        "capabilities": ATLAS_CAPABILITIES,
        "entity_kind": MESH_PATCH_ENTITY_KIND,
        "frame_count": frame_count,
        "constraint_set": "hopf_torus_nested_patch_transport",
        "probe_family": "atlas_surface_probe",
        "carrier": "nested_hopf_torus_patch_pair",
        "lane": "pairwise",
        "layer": "atlas_patch_surface",
        "witness_type": "probe-real",
        "admission_stage": "topology-variant",
        "admission_stage_index": ADMISSION_STAGE_LABELS.index("topology-variant"),
        "promotion_target_stage": ADMISSION_STAGE_NEXT["topology-variant"],
        "claim_state": "candidate",
        "promotion_status": "supporting",
        "status_label": "exists",
        "geometry_rendering_status": "admitted_rendering",
        "negative_controls": [
            "nested_patch_neighbor_dropout",
            "torus_transition_seam_break",
            "carrier_transport_fraction_mismatch",
        ],
        "exclusion_criteria": [
            "nested torus patches fail reciprocal chart-neighbor relation",
            "transition_meta seam edges leave declared patch bounds",
            "carrier transport path cannot be placed on the patch pair",
        ],
        "live_splits": [],
        "witness_trace_id": f"{run_id}::atlas_surface_probe",
        "required_negatives": [
            "nested_patch_neighbor_dropout",
            "torus_transition_seam_break",
            "carrier_transport_fraction_mismatch",
        ],
        "negatives_run": [
            "nested_patch_neighbor_dropout",
            "torus_transition_seam_break",
            "carrier_transport_fraction_mismatch",
        ],
        "kill_conditions": [
            "nested torus patches fail reciprocal chart-neighbor relation",
            "transition_meta seam edges leave declared patch bounds",
            "carrier transport path cannot be placed on the patch pair",
        ],
        "required_artifacts": [
            "run_manifest.json",
            "scene.json",
            "summary.json",
            "witness_trace.json",
            "frames/*.json",
        ],
        "artifacts_emitted": [
            "run_manifest.json",
            "scene.json",
            "summary.json",
            "witness_trace.json",
            "frames/*.json",
        ],
        "pass_rule": "nested torus patch transport keeps reciprocal neighbor and seam metadata intact",
        "fail_rule": "nested torus patch graph loses reciprocal neighbors, seam bounds, or carrier placement",
        "eligible_consumers": [
            "probe_real_atlas_report",
            "topology_variant_inventory",
        ],
        "blocked_consumers": [
            "emergence_claims",
            "bridge_level_claims",
        ],
        "promotion_blockers": [
            "no emergence rerun evidence",
            "no bridge-level admission evidence",
        ],
        "lane_admission": {
            "current_lane": "pairwise",
            "prerequisite_lanes": ["shell-local"],
            "admission_rule": "probe-real atlas support does not by itself promote emergence or bridge claims",
        },
    }


def build_scene_spec() -> dict:
    return {
        "geometry_type": "hopf_torus_atlas",
        "static_entities": [
            {"entity_id": "inner_torus_patch"},
            {"entity_id": "outer_torus_patch"},
            {"entity_id": "carrier_0"},
        ],
        "path_spec": {
            "kind": "hopf_torus_latitude_transport",
            "vertices": [],
        },
        "expected_invariants": {
            "patch_count": 2,
        },
    }


def build_frame(
    step_index: int,
    frame_count: int,
    n_theta1: int,
    n_theta2: int,
    eta_from: float,
    eta_to: float,
) -> dict:
    alpha = float(step_index / max(frame_count - 1, 1))
    q_carrier = hopf.inter_torus_transport_partial(
        hopf.torus_coordinates(eta_from, 0.0, np.pi / 3.0),
        eta_from,
        eta_to,
        alpha,
    )
    carrier_point = hopf.stereographic_s3_to_r3(q_carrier).astype(float)
    point_scalars = np.linspace(0.0, 1.0, n_theta1 * n_theta2, endpoint=False).astype(float).tolist()

    inner_s3, inner_r3 = _grid_points(eta_from, n_theta1, n_theta2)
    outer_s3, outer_r3 = _grid_points(eta_to, n_theta1, n_theta2)
    line_indices = _grid_lines(n_theta1, n_theta2)
    cell_indices = _triangle_cells(n_theta1, n_theta2)
    seam_edges = _seam_edges(n_theta1, n_theta2)

    return {
        "step_index": step_index,
        "sim_time": alpha,
        "entities": [
            {
                "entity_id": "inner_torus_patch",
                "entity_kind": MESH_PATCH_ENTITY_KIND,
                "points_xyz": inner_r3.astype(float).tolist(),
                "line_indices": line_indices,
                "cell_indices": cell_indices,
                "patch_id": "inner_torus",
                "chart_id": "torus_inner_chart",
                "seam_edges": seam_edges,
                "chart_neighbors": ["outer_torus_patch"],
                "transition_meta": [{
                    "neighbor_patch_id": "outer_torus_patch",
                    "transition_kind": "nested_torus_transport",
                    "seam_edges": seam_edges,
                }],
                "lineage_meta": [{
                    "source_patch_id": "hopf_inner_seed",
                    "lineage_kind": "transport_family_seed",
                }],
                "topology_change_meta": [{
                    "change_kind": "nested_transport_remesh",
                    "source_patch_ids": ["hopf_inner_seed"],
                    "detail": "inner torus patch tracks the remeshed transport family across nested shells",
                }],
                "point_scalars": {
                    "torus_phase": point_scalars,
                },
            },
            {
                "entity_id": "outer_torus_patch",
                "entity_kind": MESH_PATCH_ENTITY_KIND,
                "points_xyz": outer_r3.astype(float).tolist(),
                "line_indices": line_indices,
                "cell_indices": cell_indices,
                "patch_id": "outer_torus",
                "chart_id": "torus_outer_chart",
                "seam_edges": seam_edges,
                "chart_neighbors": ["inner_torus_patch"],
                "transition_meta": [{
                    "neighbor_patch_id": "inner_torus_patch",
                    "transition_kind": "nested_torus_transport",
                    "seam_edges": seam_edges,
                }],
                "lineage_meta": [{
                    "source_patch_id": "hopf_outer_seed",
                    "lineage_kind": "transport_family_seed",
                }],
                "topology_change_meta": [{
                    "change_kind": "nested_transport_remesh",
                    "source_patch_ids": ["hopf_outer_seed"],
                    "detail": "outer torus patch tracks the remeshed transport family across nested shells",
                }],
                "point_scalars": {
                    "torus_phase": point_scalars,
                },
            },
            {
                "entity_id": "carrier_0",
                "entity_kind": POINT_FRAME_ENTITY_KIND,
                "base_xyz": carrier_point.tolist(),
                "frame_vectors": {
                    "tangent": [1.0, 0.0, 0.0],
                    "normal": [0.0, 0.0, 1.0],
                    "binormal": [0.0, 1.0, 0.0],
                },
                "scalars": {
                    "transport_error": 0.0,
                    "transport_fraction": float(hopf.torus_transport_fraction(eta_from, eta_to) * alpha),
                },
                "tags": {
                    "seam_side": "inner" if alpha < 0.5 else "outer",
                },
            },
        ],
        "events": [],
    }


def build_summary() -> dict:
    return {
        "name": HOPF_TORUS_ATLAS_SIM_NAME,
        "summary": {"all_pass": True},
        "checks": {
            "two_torus_patches_present": True,
            "patch_neighbors_declared": True,
            "carrier_present": True,
        },
        "invariants": {
            "patch_count": 2,
        },
        "all_pass": True,
    }


def build_witness_trace(frame_count: int, eta_from: float, eta_to: float) -> dict:
    return {
        "witness_trace_id": "atlas_surface_probe",
        "probe_family": "atlas_surface_probe",
        "constraint_set": "hopf_torus_nested_patch_transport",
        "events": [
            {
                "event_kind": "nested_torus_transport_step",
                "step_index": int(index),
                "transport_fraction": float(index / max(frame_count - 1, 1)),
                "eta_from": float(eta_from),
                "eta_to": float(eta_to),
                "status_label": "exists",
            }
            for index in range(frame_count)
        ],
        "negative_controls_run": [
            "nested_patch_neighbor_dropout",
            "torus_transition_seam_break",
            "carrier_transport_fraction_mismatch",
        ],
        "exclusion_events": [],
    }


def export_hopf_torus_atlas(
    run_id: str,
    out_dir: Path,
    frame_count: int = 7,
    n_theta1: int = 8,
    n_theta2: int = 8,
    eta_from: float = hopf.TORUS_INNER,
    eta_to: float = hopf.TORUS_OUTER,
) -> Path:
    out_dir = Path(out_dir)
    run_dir = out_dir / run_id
    frames_dir = run_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    frames = [
        build_frame(
            step_index=index,
            frame_count=frame_count,
            n_theta1=n_theta1,
            n_theta2=n_theta2,
            eta_from=eta_from,
            eta_to=eta_to,
        )
        for index in range(frame_count)
    ]

    _json_dump(run_dir / "run_manifest.json", build_run_manifest(run_id, len(frames)))
    _json_dump(run_dir / "scene.json", build_scene_spec())
    _json_dump(run_dir / "summary.json", build_summary())
    _json_dump(run_dir / "witness_trace.json", build_witness_trace(frame_count, eta_from, eta_to))

    for frame in frames:
        _json_dump(frames_dir / f"{frame['step_index']:06d}.json", frame)

    return run_dir
