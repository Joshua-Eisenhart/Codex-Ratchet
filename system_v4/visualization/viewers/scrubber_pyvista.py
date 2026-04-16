from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from system_v4.visualization.capabilities import BASE_POINT, FIBER_PHASE, FIBER_SAMPLES, FRAME, HOLONOMY
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


def _require_capabilities(manifest: dict) -> None:
    capabilities = set(manifest.get("capabilities", []))
    required = {BASE_POINT, FRAME}
    missing = sorted(required - capabilities)
    if missing:
        raise RuntimeError(f"Run is missing required scrubber capabilities: {', '.join(missing)}")


def _frame_status_text(frame: dict, expected_holonomy: float) -> str:
    entity = frame["entities"][0]
    scalars = entity["scalars"]
    tags = entity.get("tags", {})
    lines = [
        f"step: {frame['step_index']}",
        f"loop progress: {frame['sim_time']:.3f}",
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


def open_scrubber(run_dir: Path, glyph_scale: float = 0.35) -> None:
    report = validate_run_dir(run_dir)
    if not report["ok"]:
        raise RuntimeError(f"Run failed validation: {'; '.join(report['errors'])}")

    manifest, scene, frames, _summary = load_run(run_dir)
    _require_capabilities(manifest)

    try:
        import pyvista as pv
    except ImportError as exc:
        raise RuntimeError(
            "PyVista is required for the scrubber viewer; install requirements-sim-stack.txt "
            "or add pyvista to the active environment"
        ) from exc

    expected_holonomy = float(
        scene.get("expected_invariants", {}).get(
            "expected_holonomy",
            scene.get("expected_invariants", {}).get("expected_berry_phase", 0.0),
        )
    )
    capabilities = set(manifest.get("capabilities", []))
    frame_indices = np.array([frame["step_index"] for frame in frames], dtype=float)
    error_values = np.array(
        [frame["entities"][0]["scalars"]["transport_error"] for frame in frames],
        dtype=float,
    )
    breadcrumb_points = np.array([frame["entities"][0]["base_xyz"] for frame in frames], dtype=float)
    projected_offset = _projected_overlay_offset(scene)
    projected_path = _projected_path_points(scene)

    plotter = pv.Plotter(window_size=(1600, 900))
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
            [frame["entities"][0]["scalars"]["accumulated_holonomy"] for frame in frames],
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
            [frame["entities"][0]["scalars"]["fiber_phase"] for frame in frames],
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
        entity = frame["entities"][0]
        base = np.array(entity["base_xyz"], dtype=float)
        tangent = np.array(entity["frame_vectors"]["tangent"], dtype=float)
        normal = np.array(entity["frame_vectors"]["normal"], dtype=float)
        binormal = np.array(entity["frame_vectors"]["binormal"], dtype=float)
        fiber_points = _fiber_overlay_points(entity) if FIBER_SAMPLES in capabilities else None
        projected_point = _projected_frame_point(entity)

        point_mesh = pv.PolyData(base.reshape(1, 3))
        plotter.add_mesh(
            point_mesh,
            color="#ffffff",
            point_size=18,
            render_points_as_spheres=True,
            name="current-point",
            render=False,
        )
        plotter.add_arrows(
            base.reshape(1, 3),
            tangent.reshape(1, 3),
            mag=glyph_scale,
            color="#ef4444",
            name="tangent-arrow",
            render=False,
        )
        plotter.add_arrows(
            base.reshape(1, 3),
            normal.reshape(1, 3),
            mag=glyph_scale,
            color="#22c55e",
            name="normal-arrow",
            render=False,
        )
        plotter.add_arrows(
            base.reshape(1, 3),
            binormal.reshape(1, 3),
            mag=glyph_scale,
            color="#38bdf8",
            name="binormal-arrow",
            render=False,
        )
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
            _frame_status_text(frame, expected_holonomy),
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
    plotter.show()
