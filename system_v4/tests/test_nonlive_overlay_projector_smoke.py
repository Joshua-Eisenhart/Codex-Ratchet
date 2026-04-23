"""Smoke tests for dedicated non-live archive overlay projection."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from system_v4.skills.nonlive_overlay_projector import (
    SNAPSHOT_PREFIX,
    _allowed_external_temp_roots,
    build_archive_snapshot_path,
    build_temp_snapshot_path,
    project_archive_overlay_to_nonlive_snapshot,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _node_without_overlay(node: dict[str, object]) -> dict[str, object]:
    clone = json.loads(json.dumps(node))
    properties = clone.get("properties", {})
    if isinstance(properties, dict):
        properties.pop("overlay_provenance_audit", None)
    return clone


def _canonical_live_paths(repo_root: Path) -> tuple[Path, Path]:
    live_base = (
        repo_root
        / "system_v4"
        / "a2_state"
        / "graphs"
        / "system_graph_a2_refinery.json"
    )
    live_overlay = (
        repo_root
        / "system_v4"
        / "a2_state"
        / "audit_logs"
        / "STRIPPED_PROVENANCE_OVERLAY__2026_03_20__v1.json"
    )
    return live_base, live_overlay


def _materialize_temp_repo_surfaces(
    temp_repo: Path,
    live_base: Path,
    live_overlay: Path,
    *,
    base_mode: str,
    overlay_mode: str,
) -> None:
    graphs = temp_repo / "system_v4" / "a2_state" / "graphs"
    audits = temp_repo / "system_v4" / "a2_state" / "audit_logs"
    graphs.mkdir(parents=True)
    audits.mkdir(parents=True)

    external_base = temp_repo.parent / "external_base.json"
    external_overlay = temp_repo.parent / "external_overlay.json"
    shutil.copyfile(live_base, external_base)
    shutil.copyfile(live_overlay, external_overlay)

    canonical_base = graphs / "system_graph_a2_refinery.json"
    canonical_overlay = audits / "STRIPPED_PROVENANCE_OVERLAY__2026_03_20__v1.json"
    if base_mode == "symlink":
        canonical_base.symlink_to(external_base)
    else:
        shutil.copyfile(live_base, canonical_base)
    if overlay_mode == "symlink":
        canonical_overlay.symlink_to(external_overlay)
    else:
        shutil.copyfile(live_overlay, canonical_overlay)


def test_nonlive_overlay_projector_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    overlay_path = (
        repo_root
        / "system_v4"
        / "a2_state"
        / "audit_logs"
        / "STRIPPED_PROVENANCE_OVERLAY__2026_03_20__v1.json"
    )
    live_refinery_path = (
        repo_root
        / "system_v4"
        / "a2_state"
        / "graphs"
        / "system_graph_a2_refinery.json"
    )
    live_intent_control_path = (
        repo_root / "system_v4" / "a2_state" / "A2_INTENT_CONTROL__CURRENT__v1.json"
    )
    live_stripped_path = repo_root / "system_v4" / "a1_state" / "a1_stripped_graph_v1.json"
    live_overlay_before = _sha256(overlay_path)
    live_refinery_before = _sha256(live_refinery_path)
    live_intent_control_before = _sha256(live_intent_control_path)
    live_stripped_before = _sha256(live_stripped_path)

    output_json_path = build_temp_snapshot_path(repo_root, "SMOKE_RUN", "smoke")
    result = project_archive_overlay_to_nonlive_snapshot(
        repo_root,
        output_json_path,
    )
    assert result["status"] == "projected_nonlive_snapshot"
    snapshot = json.loads(output_json_path.read_text(encoding="utf-8"))
    target_node_id = result["target_node_id"]
    snapshot_node = snapshot["nodes"][target_node_id]
    live_graph = json.loads(live_refinery_path.read_text(encoding="utf-8"))
    live_node = live_graph["nodes"][target_node_id]

    assert "overlay_provenance_audit" in snapshot_node["properties"]
    assert snapshot_node["properties"]["overlay_provenance_audit"]["overlay_kind"] == (
        "stripped_provenance_archive_projection"
    )
    assert snapshot_node["lineage_refs"] == live_node["lineage_refs"]
    assert snapshot_node["witness_refs"] == live_node["witness_refs"]
    assert snapshot_node["properties"].get("runtime_policy") == live_node["properties"].get(
        "runtime_policy"
    )
    assert snapshot_node["properties"].get("control") == live_node["properties"].get(
        "control"
    )
    assert set(snapshot["nodes"]) == set(live_graph["nodes"])
    assert snapshot["edges"] == live_graph["edges"]
    for node_id, base_node in live_graph["nodes"].items():
        if node_id == target_node_id:
            assert _node_without_overlay(snapshot["nodes"][node_id]) == base_node
        else:
            assert snapshot["nodes"][node_id] == base_node
    assert str(output_json_path.relative_to(repo_root)).startswith("work/audit_tmp/overlay_projector/")

    assert _sha256(overlay_path) == live_overlay_before
    assert _sha256(live_refinery_path) == live_refinery_before
    assert _sha256(live_intent_control_path) == live_intent_control_before
    assert _sha256(live_stripped_path) == live_stripped_before


def test_nonlive_overlay_projector_allows_explicit_live_overlay_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    _, live_overlay_path = _canonical_live_paths(repo_root)
    output_json_path = build_temp_snapshot_path(repo_root, "LIVE_OVERLAY", "explicit_overlay")
    result = project_archive_overlay_to_nonlive_snapshot(
        repo_root,
        output_json_path,
        overlay_json_path=live_overlay_path,
    )
    assert result["status"] == "projected_nonlive_snapshot"
    assert result["overlay_json_path"] == str(live_overlay_path.resolve())


def test_nonlive_overlay_projector_allows_explicit_live_refinery_base_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    live_refinery_path, _ = _canonical_live_paths(repo_root)
    output_json_path = build_temp_snapshot_path(repo_root, "LIVE_BASE", "explicit_base")
    result = project_archive_overlay_to_nonlive_snapshot(
        repo_root,
        output_json_path,
        base_graph_json_path=live_refinery_path,
    )
    assert result["status"] == "projected_nonlive_snapshot"
    assert result["base_graph_json_path"] == str(live_refinery_path.resolve())


def test_nonlive_overlay_projector_rejects_owner_surface_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    live_owner_path, _ = _canonical_live_paths(repo_root)
    try:
        project_archive_overlay_to_nonlive_snapshot(repo_root, live_owner_path)
    except ValueError as exc:
        assert "temp or archive non-live snapshot path" in str(exc)
    else:
        raise AssertionError("Expected non-live projector to reject active owner output path")


def test_nonlive_overlay_projector_rejects_repo_local_copy_base_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    live_refinery_path, _ = _canonical_live_paths(repo_root)
    repo_tmp_root = repo_root / "work" / "audit_tmp"
    repo_tmp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=repo_tmp_root) as td:
        repo_local_copy = Path(td) / "base_graph_copy.json"
        repo_local_copy.write_bytes(live_refinery_path.read_bytes())

        output_json_path = build_temp_snapshot_path(repo_root, "REPO_LOCAL", "repo_local")
        try:
            project_archive_overlay_to_nonlive_snapshot(
                repo_root,
                output_json_path,
                base_graph_json_path=repo_local_copy,
            )
        except ValueError as exc:
            assert "authoritative refinery graph or a hermetic external temp proof copy" in str(
                exc
            )
        else:
            raise AssertionError("Expected projector to reject repo-local copied base graph")


def test_nonlive_overlay_projector_rejects_repo_local_overlay_copy_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    _, live_overlay_path = _canonical_live_paths(repo_root)
    repo_tmp_root = repo_root / "work" / "audit_tmp"
    repo_tmp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=repo_tmp_root) as td:
        repo_local_copy = Path(td) / live_overlay_path.name
        repo_local_copy.write_bytes(live_overlay_path.read_bytes())

        output_json_path = build_temp_snapshot_path(repo_root, "REPO_OVERLAY", "repo_overlay")
        try:
            project_archive_overlay_to_nonlive_snapshot(
                repo_root,
                output_json_path,
                overlay_json_path=repo_local_copy,
            )
        except ValueError as exc:
            assert "authoritative archive overlay or a hermetic external temp proof copy" in str(
                exc
            )
        else:
            raise AssertionError("Expected projector to reject repo-local copied overlay")


def test_nonlive_overlay_projector_rejects_repo_sibling_graph_base_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    sibling_graph_path = (
        repo_root / "system_v4" / "a2_state" / "graphs" / "a2_high_intake_graph_v1.json"
    )
    output_json_path = build_temp_snapshot_path(repo_root, "SIBLING", "sibling_graph")
    try:
        project_archive_overlay_to_nonlive_snapshot(
            repo_root,
            output_json_path,
            base_graph_json_path=sibling_graph_path,
        )
    except ValueError as exc:
        assert "authoritative refinery graph or a hermetic external temp proof copy" in str(
            exc
        )
    else:
        raise AssertionError("Expected projector to reject sibling repo graph as base input")


def test_nonlive_overlay_projector_rejects_default_canonical_base_symlink_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    live_base, live_overlay = _canonical_live_paths(repo_root)
    with tempfile.TemporaryDirectory() as td:
        temp_repo = Path(td) / "repo"
        _materialize_temp_repo_surfaces(
            temp_repo,
            live_base,
            live_overlay,
            base_mode="symlink",
            overlay_mode="copy",
        )

        output_json_path = build_temp_snapshot_path(temp_repo, "DEFAULT_BASE_SYMLINK", "default_base")
        try:
            project_archive_overlay_to_nonlive_snapshot(temp_repo, output_json_path)
        except ValueError as exc:
            assert "base_graph_json_path must not be a symlink" in str(exc)
        else:
            raise AssertionError("Expected default canonical base symlink to be rejected")


def test_nonlive_overlay_projector_rejects_default_canonical_overlay_symlink_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    live_base, live_overlay = _canonical_live_paths(repo_root)
    with tempfile.TemporaryDirectory() as td:
        temp_repo = Path(td) / "repo"
        _materialize_temp_repo_surfaces(
            temp_repo,
            live_base,
            live_overlay,
            base_mode="copy",
            overlay_mode="symlink",
        )

        output_json_path = build_temp_snapshot_path(temp_repo, "DEFAULT_OVERLAY_SYMLINK", "default_overlay")
        try:
            project_archive_overlay_to_nonlive_snapshot(temp_repo, output_json_path)
        except ValueError as exc:
            assert "overlay_json_path must not be a symlink" in str(exc)
        else:
            raise AssertionError("Expected default canonical overlay symlink to be rejected")


def test_nonlive_overlay_projector_rejects_projected_base_path_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    base_snapshot_path = build_temp_snapshot_path(repo_root, "BASE_RUN", "base")
    project_archive_overlay_to_nonlive_snapshot(repo_root, base_snapshot_path)

    second_output_path = build_temp_snapshot_path(repo_root, "SECOND_RUN", "second")
    try:
        project_archive_overlay_to_nonlive_snapshot(
            repo_root,
            second_output_path,
            base_graph_json_path=base_snapshot_path,
        )
    except ValueError as exc:
        assert "previously projected non-live snapshot" in str(exc)
    else:
        raise AssertionError("Expected projector to reject projected snapshot as base input")


def test_nonlive_overlay_projector_rejects_parent_symlink_alias_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    live_graph_dir = repo_root / "system_v4" / "a2_state" / "graphs"
    with tempfile.TemporaryDirectory() as td:
        parent_link = Path(td) / "graphs_link"
        parent_link.symlink_to(live_graph_dir)
        via_parent_link = parent_link / "system_graph_a2_refinery.json"

        output_json_path = build_temp_snapshot_path(repo_root, "PARENT_ALIAS", "parent_alias")
        try:
            project_archive_overlay_to_nonlive_snapshot(
                repo_root,
                output_json_path,
                base_graph_json_path=via_parent_link,
            )
        except ValueError as exc:
            assert "must not be a symlink" in str(exc)
        else:
            raise AssertionError("Expected projector to reject parent-directory symlink alias of authoritative graph")


def test_nonlive_overlay_projector_rejects_symlink_to_projected_snapshot_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    base_snapshot_path = build_temp_snapshot_path(repo_root, "BASE_LINK_RUN", "base")
    project_archive_overlay_to_nonlive_snapshot(repo_root, base_snapshot_path)

    with tempfile.TemporaryDirectory() as td:
        projected_symlink_path = Path(td) / "projected_snapshot_symlink.json"
        projected_symlink_path.symlink_to(base_snapshot_path)

        second_output_path = build_temp_snapshot_path(repo_root, "LINKED_RUN", "linked")
        try:
            project_archive_overlay_to_nonlive_snapshot(
                repo_root,
                second_output_path,
                base_graph_json_path=projected_symlink_path,
            )
        except ValueError as exc:
            assert "previously projected non-live snapshot" in str(exc)
        else:
            raise AssertionError("Expected projector to reject symlink alias of projected snapshot")


def test_nonlive_overlay_projector_allows_external_exact_copy_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    live_refinery_path, _ = _canonical_live_paths(repo_root)
    with tempfile.TemporaryDirectory() as td:
        external_copy_path = Path(td) / "base_graph_copy.json"
        shutil.copyfile(live_refinery_path, external_copy_path)

        output_json_path = build_temp_snapshot_path(repo_root, "EXTERNAL_COPY", "exact_copy")
        result = project_archive_overlay_to_nonlive_snapshot(
            repo_root,
            output_json_path,
            base_graph_json_path=external_copy_path,
        )
        assert result["status"] == "projected_nonlive_snapshot"
        assert result["base_graph_json_path"] == str(external_copy_path.resolve())


def test_nonlive_overlay_projector_allows_external_exact_overlay_copy_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    _, live_overlay_path = _canonical_live_paths(repo_root)
    with tempfile.TemporaryDirectory() as td:
        external_copy_path = Path(td) / live_overlay_path.name
        shutil.copyfile(live_overlay_path, external_copy_path)

        output_json_path = build_temp_snapshot_path(repo_root, "EXTERNAL_OVERLAY", "exact_overlay")
        result = project_archive_overlay_to_nonlive_snapshot(
            repo_root,
            output_json_path,
            overlay_json_path=external_copy_path,
        )
        assert result["status"] == "projected_nonlive_snapshot"
        assert result["overlay_json_path"] == str(external_copy_path.resolve())


def test_nonlive_overlay_projector_rejects_external_symlink_alias_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    live_refinery_path, _ = _canonical_live_paths(repo_root)
    with tempfile.TemporaryDirectory() as td:
        symlink_path = Path(td) / "live_refinery_symlink.json"
        symlink_path.symlink_to(live_refinery_path)

        output_json_path = build_temp_snapshot_path(repo_root, "SYMLINK", "symlink")
        try:
            project_archive_overlay_to_nonlive_snapshot(
                repo_root,
                output_json_path,
                base_graph_json_path=symlink_path,
            )
        except ValueError as exc:
            assert "must not be a symlink" in str(exc)
        else:
            raise AssertionError("Expected projector to reject external symlink alias of authoritative graph")


def test_nonlive_overlay_projector_rejects_external_overlay_symlink_alias_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    _, live_overlay_path = _canonical_live_paths(repo_root)
    with tempfile.TemporaryDirectory() as td:
        symlink_path = Path(td) / live_overlay_path.name
        symlink_path.symlink_to(live_overlay_path)

        output_json_path = build_temp_snapshot_path(repo_root, "OVERLAY_SYMLINK", "overlay_symlink")
        try:
            project_archive_overlay_to_nonlive_snapshot(
                repo_root,
                output_json_path,
                overlay_json_path=symlink_path,
            )
        except ValueError as exc:
            assert "overlay_json_path must not be a symlink" in str(exc)
        else:
            raise AssertionError("Expected projector to reject external symlink alias of authoritative overlay")


def test_nonlive_overlay_projector_rejects_external_hardlink_alias_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    live_refinery_path, _ = _canonical_live_paths(repo_root)
    with tempfile.TemporaryDirectory() as td:
        hardlink_path = Path(td) / "live_refinery_hardlink.json"
        os.link(live_refinery_path, hardlink_path)

        output_json_path = build_temp_snapshot_path(repo_root, "HARDLINK", "hardlink")
        try:
            project_archive_overlay_to_nonlive_snapshot(
                repo_root,
                output_json_path,
                base_graph_json_path=hardlink_path,
            )
        except ValueError as exc:
            assert "must be a copy, not an alias" in str(exc)
        else:
            raise AssertionError("Expected projector to reject external hard-link alias of authoritative graph")


def test_nonlive_overlay_projector_rejects_external_overlay_hardlink_alias_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    _, live_overlay_path = _canonical_live_paths(repo_root)
    with tempfile.TemporaryDirectory() as td:
        hardlink_path = Path(td) / live_overlay_path.name
        os.link(live_overlay_path, hardlink_path)

        output_json_path = build_temp_snapshot_path(repo_root, "OVERLAY_HARDLINK", "overlay_hardlink")
        try:
            project_archive_overlay_to_nonlive_snapshot(
                repo_root,
                output_json_path,
                overlay_json_path=hardlink_path,
            )
        except ValueError as exc:
            assert "overlay_json_path must be a copy, not an alias" in str(exc)
        else:
            raise AssertionError("Expected projector to reject external hard-link alias of authoritative overlay")


def test_nonlive_overlay_projector_rejects_projected_base_content_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    live_refinery_path, live_overlay_path = _canonical_live_paths(repo_root)
    with tempfile.TemporaryDirectory() as td:
        temp_repo = Path(td) / "repo"
        _materialize_temp_repo_surfaces(
            temp_repo,
            live_refinery_path,
            live_overlay_path,
            base_mode="copy",
            overlay_mode="copy",
        )

        canonical_base_path = (
            temp_repo
            / "system_v4"
            / "a2_state"
            / "graphs"
            / "system_graph_a2_refinery.json"
        )
        graph = json.loads(canonical_base_path.read_text(encoding="utf-8"))
        target_node_id = "A1_STRIPPED::CONSTRAINT_MANIFOLD_FORMAL_DERIVATION"
        graph["nodes"][target_node_id]["properties"]["overlay_provenance_audit"] = {
            "status": "audit_only_nonoperative",
            "runtime_effect": "none",
            "audit_only": True,
            "overlay_kind": "preexisting_projection_marker",
        }
        canonical_base_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")

        second_output_path = build_temp_snapshot_path(temp_repo, "CANONICAL_MARKER", "out")
        try:
            project_archive_overlay_to_nonlive_snapshot(
                temp_repo,
                second_output_path,
            )
        except ValueError as exc:
            assert "already contains overlay_provenance_audit" in str(exc)
        else:
            raise AssertionError("Expected projector to reject canonical base graph with overlay marker content")


def test_nonlive_overlay_projector_rejects_external_noncopy_overlay_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    _, live_overlay_path = _canonical_live_paths(repo_root)
    with tempfile.TemporaryDirectory() as td:
        external_copy_path = Path(td) / live_overlay_path.name
        overlay = json.loads(live_overlay_path.read_text(encoding="utf-8"))
        overlay["overlay_kind"] = "mutated_overlay_probe"
        external_copy_path.write_text(json.dumps(overlay, indent=2), encoding="utf-8")

        output_json_path = build_temp_snapshot_path(repo_root, "OVERLAY_NONCOPY", "overlay_noncopy")
        try:
            project_archive_overlay_to_nonlive_snapshot(
                repo_root,
                output_json_path,
                overlay_json_path=external_copy_path,
            )
        except ValueError as exc:
            assert "exact byte copy of the authoritative archive overlay" in str(exc)
        else:
            raise AssertionError("Expected projector to reject external temp overlay that is not an exact copy")


def test_nonlive_overlay_projector_rejects_invalid_external_overlay_before_parse_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory() as td:
        external_overlay_path = Path(td) / "STRIPPED_PROVENANCE_OVERLAY__2026_03_20__v1.json"
        external_overlay_path.write_text("{bad json", encoding="utf-8")

        output_json_path = build_temp_snapshot_path(repo_root, "OVERLAY_INVALID", "overlay_invalid")
        try:
            project_archive_overlay_to_nonlive_snapshot(
                repo_root,
                output_json_path,
                overlay_json_path=external_overlay_path,
            )
        except ValueError as exc:
            assert "exact byte copy of the authoritative archive overlay" in str(exc)
        else:
            raise AssertionError("Expected invalid external overlay to fail exact-copy admission before parse")


def test_nonlive_overlay_projector_rejects_external_noncopy_base_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    live_refinery_path, _ = _canonical_live_paths(repo_root)
    with tempfile.TemporaryDirectory() as td:
        external_copy_path = Path(td) / "base_graph_copy.json"
        graph = json.loads(live_refinery_path.read_text(encoding="utf-8"))
        graph["nodes"]["A1_STRIPPED::CONSTRAINT_MANIFOLD_FORMAL_DERIVATION"]["description"] = (
            "mutated external proof copy"
        )
        external_copy_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")

        output_json_path = build_temp_snapshot_path(repo_root, "NONCOPY", "noncopy")
        try:
            project_archive_overlay_to_nonlive_snapshot(
                repo_root,
                output_json_path,
                base_graph_json_path=external_copy_path,
            )
        except ValueError as exc:
            assert "exact byte copy" in str(exc)
        else:
            raise AssertionError("Expected projector to reject external temp base that is not an exact copy")


def test_nonlive_overlay_projector_rejects_invalid_external_base_before_load_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory() as td:
        external_base_path = Path(td) / "base_graph_copy.json"
        external_base_path.write_text("{bad json", encoding="utf-8")

        output_json_path = build_temp_snapshot_path(repo_root, "BASE_INVALID", "base_invalid")
        try:
            project_archive_overlay_to_nonlive_snapshot(
                repo_root,
                output_json_path,
                base_graph_json_path=external_base_path,
            )
        except ValueError as exc:
            assert "exact byte copy of the authoritative refinery graph" in str(exc)
        else:
            raise AssertionError("Expected invalid external base to fail exact-copy admission before load")


def test_nonlive_overlay_projector_rejects_prefix_lookalike_output_paths_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    bad_temp_output = (
        repo_root
        / "work"
        / "audit_tmp"
        / "overlay_projector_evil"
        / "RUN"
        / f"{SNAPSHOT_PREFIX}evil.json"
    )
    bad_archive_output = (
        repo_root
        / "archive"
        / "overlay_projector_evil"
        / "RUN"
        / f"{SNAPSHOT_PREFIX}evil.json"
    )
    for output_json_path in (bad_temp_output, bad_archive_output):
        try:
            project_archive_overlay_to_nonlive_snapshot(repo_root, output_json_path)
        except ValueError as exc:
            assert "temp or archive non-live snapshot path" in str(exc)
        else:
            raise AssertionError("Expected projector to reject prefix-lookalike output path")


def test_nonlive_overlay_projector_temp_root_allowlist_is_fixed_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    roots = _allowed_external_temp_roots()
    assert repo_root.parent.resolve() not in roots
    assert Path("/private/tmp").resolve() in roots
    assert Path("/private/var/folders").resolve() in roots


def test_nonlive_overlay_projector_archive_path_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    archive_path = build_archive_snapshot_path(repo_root, "RUN_CONTRACT", "contract_smoke")
    assert str(archive_path).endswith(
        "archive/overlay_projector/RUN_CONTRACT/system_graph_overlay_projection__contract_smoke.json"
    )


if __name__ == "__main__":
    test_nonlive_overlay_projector_smoke()
    test_nonlive_overlay_projector_allows_explicit_live_overlay_smoke()
    test_nonlive_overlay_projector_allows_explicit_live_refinery_base_smoke()
    test_nonlive_overlay_projector_rejects_owner_surface_smoke()
    test_nonlive_overlay_projector_rejects_repo_local_copy_base_smoke()
    test_nonlive_overlay_projector_rejects_repo_local_overlay_copy_smoke()
    test_nonlive_overlay_projector_rejects_repo_sibling_graph_base_smoke()
    test_nonlive_overlay_projector_rejects_default_canonical_base_symlink_smoke()
    test_nonlive_overlay_projector_rejects_default_canonical_overlay_symlink_smoke()
    test_nonlive_overlay_projector_rejects_projected_base_path_smoke()
    test_nonlive_overlay_projector_rejects_parent_symlink_alias_smoke()
    test_nonlive_overlay_projector_rejects_symlink_to_projected_snapshot_smoke()
    test_nonlive_overlay_projector_allows_external_exact_copy_smoke()
    test_nonlive_overlay_projector_allows_external_exact_overlay_copy_smoke()
    test_nonlive_overlay_projector_rejects_external_symlink_alias_smoke()
    test_nonlive_overlay_projector_rejects_external_overlay_symlink_alias_smoke()
    test_nonlive_overlay_projector_rejects_external_hardlink_alias_smoke()
    test_nonlive_overlay_projector_rejects_external_overlay_hardlink_alias_smoke()
    test_nonlive_overlay_projector_rejects_projected_base_content_smoke()
    test_nonlive_overlay_projector_rejects_external_noncopy_overlay_smoke()
    test_nonlive_overlay_projector_rejects_invalid_external_overlay_before_parse_smoke()
    test_nonlive_overlay_projector_rejects_external_noncopy_base_smoke()
    test_nonlive_overlay_projector_rejects_invalid_external_base_before_load_smoke()
    test_nonlive_overlay_projector_rejects_prefix_lookalike_output_paths_smoke()
    test_nonlive_overlay_projector_temp_root_allowlist_is_fixed_smoke()
    test_nonlive_overlay_projector_archive_path_smoke()
    print("PASS: test_nonlive_overlay_projector_smoke")
