from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSPORT_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "transport_s2.py"
HOPF_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "hopf_bundle.py"
ATLAS_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "synthetic_atlas.py"
REPORTING_PATH = REPO_ROOT / "system_v4" / "visualization" / "reporting.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_render_run_report_includes_core_fields(tmp_path: Path) -> None:
    exporter = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    reporting = _load_module(REPORTING_PATH, "viz_reporting")

    run_dir = exporter.export_transport_s2("report_transport", tmp_path, steps_per_arc=8)
    text = reporting.render_run_report(run_dir)

    assert "Run: report_transport" in text
    assert "Sim: parallel_transport_s2_classical" in text
    assert "Constraint Set: sphere_parallel_transport_octant_loop" in text
    assert "Probe Family: transport_frame_probe" in text
    assert "Admission Stage: shell-local" in text
    assert "Promotion Target Stage: pairwise" in text
    assert "Promotion Status: supporting" in text
    assert "Internal Promotion Restriction: promotion_status=canonical is reserved for bridge-claims" in text
    assert "Claim Ceiling: exists" in text
    assert "Witness Trace ID: report_transport::transport_frame_probe" in text
    assert "Status Label: exists" in text
    assert (
        "Consumer Surfaces: eligible=transport_frame_report, shell_local_geometry_inventory | "
        "blocked=pairwise_coupling_claims, bridge_level_claims | "
        "promotion_blockers=no pairwise coupling evidence, no coexistence rerun evidence"
    ) in text
    assert "Claim-Evidence Table:" in text
    assert "Capabilities: base_point, frame, transport_path, holonomy" in text
    assert "Overlays: base_path, frame_glyphs, holonomy_trace" in text


def test_render_comparison_report_highlights_lane_differences(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    reporting = _load_module(REPORTING_PATH, "viz_reporting")

    left_run = transport.export_transport_s2("report_left", tmp_path, steps_per_arc=8)
    right_run = hopf.export_hopf_bundle("report_right", tmp_path, n_points=16, fiber_points=8, fiber_twist=1.0)
    text = reporting.render_comparison_report(left_run, right_run)

    assert "Left-only Capabilities: holonomy" in text
    assert "Left Probe/Lane: transport_frame_probe / shell-local" in text
    assert "Left Status Label: exists" in text
    assert "Right Status Label: exists" in text
    assert "Internal Promotion Restriction: promotion_status=canonical is reserved for bridge-claims" in text
    assert "Right-only Capabilities: fiber_phase, fiber_samples, mesh_geometry, s3_state" in text
    assert "Right-only Overlays: fiber_ring, mesh_patch_lines, projected_s3_path" in text
    assert "Projected Paths: left=None right=stereographic_s3_path" in text


def test_render_run_report_includes_atlas_overlay_fields(tmp_path: Path) -> None:
    atlas = _load_module(ATLAS_EXPORTER_PATH, "synthetic_atlas_exporter")
    reporting = _load_module(REPORTING_PATH, "viz_reporting")

    run_dir = atlas.export_synthetic_atlas("report_atlas", tmp_path, frame_count=5)
    text = reporting.render_run_report(run_dir)

    assert "Sim: synthetic_two_patch_atlas" in text
    assert "Witness Type: synthetic_fixture" in text
    assert "Claim State: snapshot-labeled" in text
    assert "Admission Stage: coexistence" in text
    assert "Promotion Target Stage: topology-variant" in text
    assert "Exclusion Events: 1" in text
    assert "Status Label: exists" in text
    assert "Capabilities: base_point, frame, mesh_geometry, cell_geometry, chart_patch, seam_markers, transition_meta" in text
    assert "Overlays: base_path, frame_glyphs, mesh_patch_lines, mesh_patch_cells, seam_edges, transition_annotations" in text
    assert "Transitions: 2" in text
    assert "Lineage Records: 2" in text
    assert "Topology Changes: 2" in text
