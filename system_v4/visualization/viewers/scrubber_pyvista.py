from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

from system_v4.visualization.capabilities import BASE_POINT, FIBER_PHASE, FIBER_SAMPLES, FRAME, HOLONOMY
from system_v4.visualization.schema_v1 import MESH_PATCH_ENTITY_KIND, POINT_FRAME_ENTITY_KIND
from system_v4.visualization.validator import validate_run_dir


def load_run(run_dir: Path) -> tuple[dict, dict, list[dict], dict]:
    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    scene = json.loads((run_dir / "scene.json").read_text(encoding="utf-8"))
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    frames = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((run_dir / "frames").glob("*.json"))
    ]
    return manifest, scene, frames, summary


def _prepare_matplotlib_runtime() -> str:
    configured = os.environ.get("MPLCONFIGDIR")
    if configured:
        Path(configured).mkdir(parents=True, exist_ok=True)
        return configured

    fallback = Path("/tmp/codex_ratchet_matplotlib")
    fallback.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(fallback)
    return str(fallback)


def _require_capabilities(manifest: dict) -> None:
    capabilities = set(manifest.get("capabilities", []))
    required = {BASE_POINT, FRAME}
    missing = sorted(required - capabilities)
    if missing:
        raise RuntimeError(f"Run is missing required scrubber capabilities: {', '.join(missing)}")


def _primary_entity(frame: dict) -> dict:
    entities = frame.get("entities", [])
    for entity in entities:
        if entity.get("entity_kind", POINT_FRAME_ENTITY_KIND) == POINT_FRAME_ENTITY_KIND and entity.get("entity_id") == "carrier_0":
            return entity
    for entity in entities:
        if entity.get("entity_kind", POINT_FRAME_ENTITY_KIND) == POINT_FRAME_ENTITY_KIND:
            return entity
    if not entities:
        raise RuntimeError("frame contains no entities")
    return entities[0]


def _line_mesh_for_entity(pv, entity: dict):
    points = entity.get("points_xyz")
    line_indices = entity.get("line_indices")
    if not isinstance(points, list) or not isinstance(line_indices, list):
        return None
    points_array = np.array(points, dtype=float)
    if points_array.ndim != 2 or points_array.shape[1] != 3 or len(points_array) < 2:
        return None
    line_segments = []
    for pair in line_indices:
        if not isinstance(pair, list) or len(pair) != 2:
            continue
        start, end = pair
        if not isinstance(start, int) or not isinstance(end, int):
            continue
        if not (0 <= start < len(points_array) and 0 <= end < len(points_array)):
            continue
        line_segments.append(points_array[start])
        line_segments.append(points_array[end])
    if len(line_segments) < 2:
        return None
    return pv.lines_from_points(np.array(line_segments, dtype=float), close=False)


def _surface_mesh_for_entity(pv, entity: dict):
    points = entity.get("points_xyz")
    cell_indices = entity.get("cell_indices")
    if not isinstance(points, list) or not isinstance(cell_indices, list):
        return None
    points_array = np.array(points, dtype=float)
    if points_array.ndim != 2 or points_array.shape[1] != 3 or len(points_array) < 3:
        return None
    cells = []
    for triple in cell_indices:
        if not isinstance(triple, list) or len(triple) != 3:
            continue
        if not all(isinstance(index, int) and 0 <= index < len(points_array) for index in triple):
            continue
        cells.extend([3, triple[0], triple[1], triple[2]])
    if not cells:
        return None
    import numpy as _np
    return pv.PolyData(points_array, _np.array(cells, dtype=_np.int64))


def _seam_mesh_for_entity(pv, entity: dict):
    points = entity.get("points_xyz")
    seam_edges = entity.get("seam_edges")
    if not isinstance(points, list) or not isinstance(seam_edges, list):
        return None
    points_array = np.array(points, dtype=float)
    if points_array.ndim != 2 or points_array.shape[1] != 3:
        return None
    segments = []
    for pair in seam_edges:
        if not isinstance(pair, list) or len(pair) != 2:
            continue
        start, end = pair
        if not isinstance(start, int) or not isinstance(end, int):
            continue
        if not (0 <= start < len(points_array) and 0 <= end < len(points_array)):
            continue
        segments.append(points_array[start])
        segments.append(points_array[end])
    if len(segments) < 2:
        return None
    return pv.lines_from_points(np.array(segments, dtype=float), close=False)


def _frame_status_text(frame: dict, expected_holonomy: float, manifest: dict) -> str:
    entity = _primary_entity(frame)
    scalars = entity["scalars"]
    tags = entity.get("tags", {})
    lines = [
        f"constraint set: {manifest.get('constraint_set')}",
        f"probe family: {manifest.get('probe_family')}",
        f"claim ceiling: {manifest.get('status_label')}",
        f"claim/promotion: {manifest.get('claim_state')} / {manifest.get('promotion_status')}",
        f"admission: {manifest.get('admission_stage')} -> {manifest.get('promotion_target_stage')}",
        f"blocked consumers: {', '.join(manifest.get('blocked_consumers', [])) or '(none)'}",
        f"promotion blockers: {', '.join(manifest.get('promotion_blockers', [])) or '(none)'}",
        f"exclusion criteria: {', '.join(manifest.get('exclusion_criteria', [])) or '(none)'}",
        f"step: {frame['step_index']}",
        f"loop progress: {frame['sim_time']:.3f}",
        f"entities: {len(frame.get('entities', []))}",
        f"primary: {entity.get('entity_id', 'unknown')}",
    ]
    if "arc_id" in tags:
        lines.append(f"arc: {tags['arc_id']}")
    if "loop_theta" in tags:
        lines.append(f"theta: {tags['loop_theta']:.5f}")
    if "hopf_patch_id" in tags:
        lines.append(f"patch: {tags['hopf_patch_id']}")
    if "accumulated_holonomy" in scalars:
        lines.append(f"holonomy: {scalars['accumulated_holonomy']:.5f}")
        lines.append(f"expected: {expected_holonomy:.5f}")
    if "fiber_phase" in scalars:
        lines.append(f"fiber phase: {scalars['fiber_phase']:.5f}")
    if "transport_error" in scalars:
        lines.append(f"transport error: {scalars['transport_error']:.6f}")
    if "tangent_leakage" in scalars:
        lines.append(f"tangent leakage: {scalars['tangent_leakage']:.6f}")
    return "\n".join(lines)


def _fiber_overlay_points(entity: dict, max_radius: float = 250.0) -> np.ndarray | None:
    samples = entity.get("fiber_samples_xyz")
    if not isinstance(samples, list) or len(samples) < 2:
        return None

    points = np.array(samples, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3:
        return None

    finite_mask = np.isfinite(points).all(axis=1)
    radius_mask = np.linalg.norm(points, axis=1) <= max_radius
    filtered = points[finite_mask & radius_mask]
    if len(filtered) < 2:
        return None
    return filtered


def _projected_overlay_offset(scene: dict) -> np.ndarray:
    projected_spec = scene.get("projected_path_spec", {})
    offset = projected_spec.get("offset_xyz", [0.0, 0.0, 0.0])
    offset_array = np.array(offset, dtype=float)
    if offset_array.shape != (3,):
        return np.zeros(3, dtype=float)
    return offset_array


def _projected_path_points(scene: dict, max_radius: float = 250.0) -> np.ndarray | None:
    projected_spec = scene.get("projected_path_spec", {})
    vertices = projected_spec.get("vertices")
    if not isinstance(vertices, list) or len(vertices) < 2:
        return None

    points = np.array(vertices, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3:
        return None

    finite_mask = np.isfinite(points).all(axis=1)
    radius_mask = np.linalg.norm(points, axis=1) <= max_radius
    filtered = points[finite_mask & radius_mask]
    if len(filtered) < 2:
        return None
    return filtered


def _projected_frame_point(entity: dict, max_radius: float = 250.0) -> np.ndarray | None:
    point = entity.get("projected_s3_xyz")
    if not isinstance(point, list) or len(point) != 3:
        return None
    point_array = np.array(point, dtype=float)
    if not np.isfinite(point_array).all():
        return None
    if np.linalg.norm(point_array) > max_radius:
        return None
    return point_array


def open_scrubber(
    run_dir: Path,
    glyph_scale: float = 0.35,
    *,
    off_screen: bool = False,
    show: bool = True,
) -> dict:
    report = validate_run_dir(run_dir)
    if not report["ok"]:
        raise RuntimeError(f"Run failed validation: {'; '.join(report['errors'])}")

    manifest, scene, frames, _summary = load_run(run_dir)
    _require_capabilities(manifest)

    _prepare_matplotlib_runtime()
    if off_screen:
        os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")

    try:
        import pyvista as pv
    except ImportError as exc:
        raise RuntimeError(
            "PyVista is required for the scrubber viewer; install requirements-sim-stack.txt "
            "or add pyvista to the active environment"
        ) from exc

    if off_screen:
        pv.OFF_SCREEN = True

    expected_holonomy = float(
        scene.get("expected_invariants", {}).get(
            "expected_holonomy",
            scene.get("expected_invariants", {}).get("expected_berry_phase", 0.0),
        )
    )
    capabilities = set(manifest.get("capabilities", []))
    frame_indices = np.array([frame["step_index"] for frame in frames], dtype=float)
    error_values = np.array(
        [_primary_entity(frame)["scalars"]["transport_error"] for frame in frames],
        dtype=float,
    )
    breadcrumb_points = np.array([_primary_entity(frame)["base_xyz"] for frame in frames], dtype=float)
    projected_offset = _projected_overlay_offset(scene)
    projected_path = _projected_path_points(scene)

    plotter = pv.Plotter(window_size=(1600, 900), off_screen=off_screen)
    plotter.background_color = "#0b1020"
    plotter.add_title(manifest.get("sim_name", "Geometry Scrubber"), font_size=18, color="white")

    sphere = pv.Sphere(radius=1.0, theta_resolution=64, phi_resolution=64)
    plotter.add_mesh(
        sphere,
        color="#dbe4ff",
        opacity=0.14,
        smooth_shading=True,
        name="unit-sphere",
        render=False,
    )

    scene_vertices = np.array(scene.get("path_spec", {}).get("vertices", []), dtype=float)
    if len(scene_vertices) >= 2:
        plotter.add_mesh(
            pv.lines_from_points(scene_vertices, close=False),
            color="#f59e0b",
            line_width=5,
            render_lines_as_tubes=True,
            name="scene-path",
            render=False,
        )

    if len(breadcrumb_points) >= 2:
        plotter.add_mesh(
            pv.lines_from_points(breadcrumb_points, close=False),
            color="#60a5fa",
            line_width=3,
            opacity=0.55,
            render_lines_as_tubes=True,
            name="breadcrumbs",
            render=False,
        )
    if projected_path is not None:
        plotter.add_mesh(
            pv.lines_from_points(projected_path + projected_offset, close=False),
            color="#a78bfa",
            line_width=4,
            opacity=0.75,
            render_lines_as_tubes=True,
            name="projected-s3-path",
            render=False,
        )

    chart_updaters = []
    if HOLONOMY in capabilities:
        holonomy_values = np.array(
            [_primary_entity(frame)["scalars"]["accumulated_holonomy"] for frame in frames],
            dtype=float,
        )
        holonomy_chart = pv.Chart2D(size=(0.42, 0.22), loc=(0.03, 0.02))
        holonomy_chart.title = "Accumulated Holonomy"
        holonomy_chart.x_label = "step"
        holonomy_chart.y_label = "angle"
        holonomy_chart.line(frame_indices, holonomy_values, color="#f59e0b", width=2.5, label="holonomy")
        holonomy_chart.line(
            frame_indices,
            np.full_like(frame_indices, expected_holonomy),
            color="#94a3b8",
            width=1.5,
            style="--",
            label="expected",
        )
        holonomy_cursor = holonomy_chart.scatter(
            [frame_indices[0]],
            [holonomy_values[0]],
            color="#ffffff",
            size=12,
            label="current",
        )
        plotter.add_chart(holonomy_chart)
        chart_updaters.append(lambda index: holonomy_cursor.update([frame_indices[index]], [holonomy_values[index]]))
    elif FIBER_PHASE in capabilities:
        fiber_phase_values = np.array(
            [_primary_entity(frame)["scalars"]["fiber_phase"] for frame in frames],
            dtype=float,
        )
        phase_chart = pv.Chart2D(size=(0.42, 0.22), loc=(0.03, 0.02))
        phase_chart.title = "Fiber Phase"
        phase_chart.x_label = "step"
        phase_chart.y_label = "phase"
        phase_chart.line(frame_indices, fiber_phase_values, color="#a78bfa", width=2.5, label="fiber phase")
        phase_cursor = phase_chart.scatter(
            [frame_indices[0]],
            [fiber_phase_values[0]],
            color="#ffffff",
            size=12,
            label="current",
        )
        plotter.add_chart(phase_chart)
        chart_updaters.append(lambda index: phase_cursor.update([frame_indices[index]], [fiber_phase_values[index]]))

    error_chart = pv.Chart2D(size=(0.42, 0.22), loc=(0.55, 0.02))
    error_chart.title = "Transport Error"
    error_chart.x_label = "step"
    error_chart.y_label = "error"
    error_chart.line(frame_indices, error_values, color="#22d3ee", width=2.5, label="error")
    error_cursor = error_chart.scatter(
        [frame_indices[0]],
        [error_values[0]],
        color="#ffffff",
        size=12,
        label="current",
    )
    plotter.add_chart(error_chart)

    def render_frame(index: int) -> None:
        index = max(0, min(index, len(frames) - 1))
        frame = frames[index]
        entity = _primary_entity(frame)
        frame_entities = frame.get("entities", [])
        mesh_palette = ["#f59e0b", "#c084fc", "#a78bfa", "#22d3ee", "#f472b6", "#34d399"]
        point_palette = ["#ffffff", "#fde68a", "#fca5a5", "#86efac", "#93c5fd", "#c4b5fd"]
        tangent_palette = ["#ef4444", "#f97316", "#dc2626", "#fb7185", "#f59e0b", "#e11d48"]
        normal_palette = ["#22c55e", "#10b981", "#16a34a", "#4ade80", "#84cc16", "#14b8a6"]
        binormal_palette = ["#38bdf8", "#3b82f6", "#60a5fa", "#818cf8", "#06b6d4", "#8b5cf6"]

        for entity_index, frame_entity in enumerate(frame_entities):
            if frame_entity.get("entity_kind") == MESH_PATCH_ENTITY_KIND:
                surface_mesh = _surface_mesh_for_entity(pv, frame_entity)
                if surface_mesh is not None:
                    mesh_suffix = str(frame_entity.get("entity_id", f"mesh_patch_{entity_index}")).replace("/", "_")
                    plotter.add_mesh(
                        surface_mesh,
                        color=mesh_palette[entity_index % len(mesh_palette)],
                        opacity=0.28,
                        show_edges=False,
                        smooth_shading=True,
                        name=f"mesh-surface-{mesh_suffix}",
                        render=False,
                    )
                line_mesh = _line_mesh_for_entity(pv, frame_entity)
                if line_mesh is not None:
                    mesh_suffix = str(frame_entity.get("entity_id", f"mesh_patch_{entity_index}")).replace("/", "_")
                    plotter.add_mesh(
                        line_mesh,
                        color=mesh_palette[entity_index % len(mesh_palette)],
                        line_width=4,
                        opacity=0.9,
                        render_lines_as_tubes=True,
                        name=f"mesh-patch-{mesh_suffix}",
                        render=False,
                    )
                seam_mesh = _seam_mesh_for_entity(pv, frame_entity)
                if seam_mesh is not None:
                    mesh_suffix = str(frame_entity.get("entity_id", f"mesh_patch_{entity_index}")).replace("/", "_")
                    plotter.add_mesh(
                        seam_mesh,
                        color="#ef4444",
                        line_width=8,
                        opacity=1.0,
                        render_lines_as_tubes=True,
                        name=f"mesh-seam-{mesh_suffix}",
                        render=False,
                    )
                continue
            if frame_entity.get("entity_kind", POINT_FRAME_ENTITY_KIND) != POINT_FRAME_ENTITY_KIND:
                continue
            entity_id = str(frame_entity.get("entity_id", f"entity_{entity_index}"))
            suffix = entity_id.replace("/", "_")
            base = np.array(frame_entity["base_xyz"], dtype=float)
            tangent = np.array(frame_entity["frame_vectors"]["tangent"], dtype=float)
            normal = np.array(frame_entity["frame_vectors"]["normal"], dtype=float)
            binormal = np.array(frame_entity["frame_vectors"]["binormal"], dtype=float)
            plotter.add_mesh(
                pv.PolyData(base.reshape(1, 3)),
                color=point_palette[entity_index % len(point_palette)],
                point_size=18 if entity_id == entity.get("entity_id") else 12,
                render_points_as_spheres=True,
                name=f"current-point-{suffix}",
                render=False,
            )
            plotter.add_arrows(
                base.reshape(1, 3),
                tangent.reshape(1, 3),
                mag=glyph_scale,
                color=tangent_palette[entity_index % len(tangent_palette)],
                name=f"tangent-arrow-{suffix}",
                render=False,
            )
            plotter.add_arrows(
                base.reshape(1, 3),
                normal.reshape(1, 3),
                mag=glyph_scale,
                color=normal_palette[entity_index % len(normal_palette)],
                name=f"normal-arrow-{suffix}",
                render=False,
            )
            plotter.add_arrows(
                base.reshape(1, 3),
                binormal.reshape(1, 3),
                mag=glyph_scale,
                color=binormal_palette[entity_index % len(binormal_palette)],
                name=f"binormal-arrow-{suffix}",
                render=False,
            )

        fiber_points = _fiber_overlay_points(entity) if FIBER_SAMPLES in capabilities else None
        projected_point = _projected_frame_point(entity)
        if fiber_points is not None:
            plotter.add_mesh(
                pv.lines_from_points(fiber_points + projected_offset, close=True),
                color="#c084fc",
                line_width=3,
                opacity=0.9,
                render_lines_as_tubes=True,
                name="fiber-ring",
                render=False,
            )
            plotter.add_mesh(
                pv.PolyData(fiber_points + projected_offset),
                color="#e9d5ff",
                point_size=6,
                render_points_as_spheres=True,
                name="fiber-ring-points",
                render=False,
            )
        if projected_point is not None:
            plotter.add_mesh(
                pv.PolyData((projected_point + projected_offset).reshape(1, 3)),
                color="#f5d0fe",
                point_size=16,
                render_points_as_spheres=True,
                name="projected-current-point",
                render=False,
            )
        plotter.add_text(
            _frame_status_text(frame, expected_holonomy, manifest),
            position="upper_right",
            font_size=12,
            color="white",
            name="status-block",
            render=False,
        )
        for update_chart in chart_updaters:
            update_chart(index)
        error_cursor.update([frame_indices[index]], [error_values[index]])
        plotter.render()

    current_index = {"value": 0}

    def set_frame(raw_value: float) -> None:
        index = int(round(raw_value))
        current_index["value"] = max(0, min(index, len(frames) - 1))
        render_frame(current_index["value"])

    def step_by(delta: int) -> None:
        set_frame(current_index["value"] + delta)

    plotter.add_slider_widget(
        set_frame,
        rng=(0, len(frames) - 1),
        value=0,
        title="frame",
        pointa=(0.22, 0.94),
        pointb=(0.78, 0.94),
        fmt="%0.0f",
        interaction_event="always",
    )
    plotter.add_key_event("Left", lambda: step_by(-1))
    plotter.add_key_event("Right", lambda: step_by(1))
    plotter.add_text(
        "Left/Right: step  |  slider: scrub  |  purple: fiber overlay when available",
        position="lower_left",
        font_size=10,
        color="#cbd5e1",
        name="help-text",
        render=False,
    )
    plotter.show_axes()
    render_frame(0)
    if show:
        plotter.show()
    else:
        plotter.close()

    return {
        "ok": True,
        "run_id": manifest.get("run_id"),
        "sim_name": manifest.get("sim_name"),
        "frame_count": len(frames),
        "off_screen": off_screen,
        "show": show,
        "matplotlib_runtime": os.environ.get("MPLCONFIGDIR"),
    }
