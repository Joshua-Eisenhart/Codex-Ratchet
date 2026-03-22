"""Project archive-only audit overlays into non-live graph snapshots."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from system_v4.skills.intent_control_surface_builder import (
    GRAPH_REL_PATH,
    PROVENANCE_OVERLAY_REL_PATH,
    build_stripped_provenance_overlay_projection_payload,
)
from system_v4.skills.v4_graph_builder import SystemGraphBuilder

TEMP_SNAPSHOT_DIR_REL = Path("work/audit_tmp/overlay_projector")
ARCHIVE_SNAPSHOT_DIR_REL = Path("archive/overlay_projector")
SNAPSHOT_PREFIX = "system_graph_overlay_projection__"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolved_relative_to_repo(repo_root: Path, path: Path) -> Path | None:
    try:
        return path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return None


def _is_nonlive_snapshot_relpath(relpath: Path | None) -> bool:
    if relpath is None:
        return False
    try:
        relpath.relative_to(TEMP_SNAPSHOT_DIR_REL)
        return True
    except ValueError:
        pass
    try:
        relpath.relative_to(ARCHIVE_SNAPSHOT_DIR_REL)
        return True
    except ValueError:
        return False


def _is_allowed_nonlive_output_path(repo_root: Path, output_json_path: Path) -> bool:
    resolved_repo = repo_root.resolve()
    resolved_output = output_json_path.resolve()

    if output_json_path.suffix != ".json":
        return False
    if not output_json_path.name.startswith(SNAPSHOT_PREFIX):
        return False

    live_graph_dir = resolved_repo / "system_v4" / "a2_state" / "graphs"
    if resolved_output == live_graph_dir / "system_graph_a2_refinery.json":
        return False
    if str(resolved_output).startswith(str(live_graph_dir)):
        return False

    rel = _resolved_relative_to_repo(resolved_repo, resolved_output)
    return _is_nonlive_snapshot_relpath(rel)


def _base_graph_is_projected_snapshot(repo_root: Path, base_graph_json_path: Path) -> bool:
    rel = _resolved_relative_to_repo(repo_root, base_graph_json_path)
    if _is_nonlive_snapshot_relpath(rel):
        return True
    return base_graph_json_path.name.startswith(SNAPSHOT_PREFIX)


def _authoritative_base_graph_path(repo_root: Path) -> Path:
    return (repo_root / GRAPH_REL_PATH).resolve()


def _authoritative_overlay_path(repo_root: Path) -> Path:
    return (repo_root / PROVENANCE_OVERLAY_REL_PATH).resolve()


def _authoritative_base_graph_input_path(repo_root: Path) -> Path:
    return repo_root / GRAPH_REL_PATH


def _authoritative_overlay_input_path(repo_root: Path) -> Path:
    return repo_root / PROVENANCE_OVERLAY_REL_PATH


def _path_is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _allowed_external_temp_roots() -> tuple[Path, ...]:
    roots: list[Path] = []
    for raw in ("/private/tmp", "/tmp", "/private/var/folders", "/var/folders"):
        try:
            resolved = Path(raw).resolve()
        except FileNotFoundError:
            continue
        if resolved not in roots:
            roots.append(resolved)
    return tuple(roots)


def _normalized_absolute_input_path(path: Path) -> Path:
    absolute_path = Path(os.path.abspath(os.fspath(path)))
    raw = str(absolute_path)
    if raw == "/tmp" or raw.startswith("/tmp/"):
        return Path("/private" + raw)
    if raw == "/var" or raw.startswith("/var/"):
        return Path("/private" + raw)
    return absolute_path


def _classify_base_graph_path(
    repo_root: Path,
    base_graph_input_path: Path,
    base_graph_resolved_path: Path,
) -> str:
    authoritative_base_path = _authoritative_base_graph_path(repo_root)
    normalized_input_path = _normalized_absolute_input_path(base_graph_input_path)
    if _base_graph_is_projected_snapshot(repo_root, base_graph_resolved_path):
        raise ValueError("base_graph_json_path must not be a previously projected non-live snapshot")

    if base_graph_resolved_path == authoritative_base_path:
        if normalized_input_path != authoritative_base_path:
            raise ValueError("base_graph_json_path must not be a symlink")
        return "authoritative_live"

    if _resolved_relative_to_repo(repo_root, base_graph_resolved_path) is not None:
        raise ValueError(
            "base_graph_json_path must be the authoritative refinery graph or a hermetic external temp proof copy"
        )
    if normalized_input_path != base_graph_resolved_path:
        raise ValueError("base_graph_json_path must not be a symlink")
    if base_graph_resolved_path.suffix != ".json":
        raise ValueError("base_graph_json_path must reference a JSON graph file")
    if not base_graph_resolved_path.is_file():
        raise ValueError("base_graph_json_path must reference an existing JSON graph file")
    if not any(
        _path_is_within(base_graph_resolved_path, root)
        for root in _allowed_external_temp_roots()
    ):
        raise ValueError(
            "base_graph_json_path must be the authoritative refinery graph or a hermetic external temp proof copy"
        )
    if os.path.samefile(base_graph_resolved_path, authoritative_base_path):
        raise ValueError(
            "base_graph_json_path must be a copy, not an alias of the authoritative refinery graph"
        )
    return "external_temp_proof_copy"


def _classify_overlay_path(
    repo_root: Path,
    overlay_input_path: Path,
    overlay_resolved_path: Path,
) -> str:
    authoritative_overlay_path = _authoritative_overlay_path(repo_root)
    normalized_input_path = _normalized_absolute_input_path(overlay_input_path)

    if overlay_resolved_path == authoritative_overlay_path:
        if normalized_input_path != authoritative_overlay_path:
            raise ValueError("overlay_json_path must not be a symlink")
        return "authoritative_overlay"

    if _resolved_relative_to_repo(repo_root, overlay_resolved_path) is not None:
        raise ValueError(
            "overlay_json_path must be the authoritative archive overlay or a hermetic external temp proof copy"
        )
    if normalized_input_path != overlay_resolved_path:
        raise ValueError("overlay_json_path must not be a symlink")
    if overlay_resolved_path.suffix != ".json":
        raise ValueError("overlay_json_path must reference a JSON overlay file")
    if not overlay_resolved_path.is_file():
        raise ValueError("overlay_json_path must reference an existing JSON overlay file")
    if not any(
        _path_is_within(overlay_resolved_path, root)
        for root in _allowed_external_temp_roots()
    ):
        raise ValueError(
            "overlay_json_path must be the authoritative archive overlay or a hermetic external temp proof copy"
        )
    if os.path.samefile(overlay_resolved_path, authoritative_overlay_path):
        raise ValueError(
            "overlay_json_path must be a copy, not an alias of the authoritative archive overlay"
        )
    return "external_temp_overlay_copy"


def _graph_contains_overlay_projection(builder: SystemGraphBuilder) -> bool:
    for node in builder.pydantic_model.nodes.values():
        props = dict(node.properties)
        if "overlay_provenance_audit" in props:
            return True
    return False


def _safe_run_label(run_label: str) -> str:
    cleaned = "_".join(part for part in str(run_label).strip().split() if part)
    return cleaned or "snapshot"


def build_archive_snapshot_path(repo_root: str | Path, run_id: str, label: str) -> Path:
    safe_label = "_".join(part for part in str(label).strip().split() if part)
    if not safe_label:
        safe_label = "snapshot"
    return (
        Path(repo_root)
        / ARCHIVE_SNAPSHOT_DIR_REL
        / _safe_run_label(run_id)
        / f"{SNAPSHOT_PREFIX}{safe_label}.json"
    )


def build_temp_snapshot_path(repo_root: str | Path, run_id: str, label: str) -> Path:
    safe_label = "_".join(part for part in str(label).strip().split() if part)
    if not safe_label:
        safe_label = "snapshot"
    return (
        Path(repo_root)
        / TEMP_SNAPSHOT_DIR_REL
        / _safe_run_label(run_id)
        / f"{SNAPSHOT_PREFIX}{safe_label}.json"
    )


def project_archive_overlay_to_nonlive_snapshot(
    repo_root: str | Path,
    output_json_path: str | Path,
    *,
    base_graph_json_path: str | Path | None = None,
    overlay_json_path: str | Path | None = None,
) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    output_json_path = Path(output_json_path)
    if not _is_allowed_nonlive_output_path(repo_root, output_json_path):
        raise ValueError("output_json_path must target a temp or archive non-live snapshot path")

    authoritative_base_path = _authoritative_base_graph_path(repo_root)
    authoritative_overlay_path = _authoritative_overlay_path(repo_root)
    if base_graph_json_path is None:
        base_graph_input_path = _authoritative_base_graph_input_path(repo_root)
        base_graph_json_path = base_graph_input_path.resolve()
    else:
        base_graph_input_path = Path(base_graph_json_path)
        base_graph_json_path = base_graph_input_path.resolve()
    if overlay_json_path is None:
        overlay_input_path = _authoritative_overlay_input_path(repo_root)
        overlay_json_path = overlay_input_path.resolve()
    else:
        overlay_input_path = Path(overlay_json_path)
        overlay_json_path = overlay_input_path.resolve()

    base_graph_mode = _classify_base_graph_path(
        repo_root,
        base_graph_input_path,
        base_graph_json_path,
    )
    overlay_mode = _classify_overlay_path(
        repo_root,
        overlay_input_path,
        overlay_json_path,
    )
    if (
        base_graph_mode == "external_temp_proof_copy"
        and _sha256(base_graph_json_path) != _sha256(authoritative_base_path)
    ):
        raise ValueError(
            "base_graph_json_path must be an exact byte copy of the authoritative refinery graph"
        )
    if (
        overlay_mode == "external_temp_overlay_copy"
        and _sha256(overlay_json_path) != _sha256(authoritative_overlay_path)
    ):
        raise ValueError(
            "overlay_json_path must be an exact byte copy of the authoritative archive overlay"
        )

    overlay_payload = json.loads(Path(overlay_json_path).read_text(encoding="utf-8"))
    projection_payload = build_stripped_provenance_overlay_projection_payload(
        overlay_payload
    )
    if not projection_payload:
        raise ValueError("overlay_json_path did not yield a valid archive-only projection payload")

    target_node_id = str((overlay_payload.get("target", {}) or {}).get("node_id", "")).strip()
    if not target_node_id:
        raise ValueError("overlay_json_path is missing target.node_id")

    builder = SystemGraphBuilder(str(repo_root))
    if not builder.load_graph_json_path(base_graph_json_path):
        raise FileNotFoundError(f"Base graph not found: {base_graph_json_path}")
    if _graph_contains_overlay_projection(builder):
        raise ValueError(
            "base_graph_json_path already contains overlay_provenance_audit; refusing snapshot-on-snapshot projection"
        )
    if not builder.node_exists(target_node_id):
        raise ValueError(f"Target node not found in base graph: {target_node_id}")
    if not builder.merge_overlay_audit(
        target_node_id,
        "overlay_provenance_audit",
        projection_payload,
    ):
        raise ValueError("Overlay projection merge failed")

    output_graphml_path = output_json_path.with_suffix(".graphml")
    builder.save_graph_snapshot_paths(output_json_path, output_graphml_path)
    return {
        "status": "projected_nonlive_snapshot",
        "target_node_id": target_node_id,
        "output_json_path": str(output_json_path),
        "output_graphml_path": str(output_graphml_path),
        "base_graph_json_path": str(base_graph_json_path),
        "overlay_json_path": str(overlay_json_path),
    }


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[2]
    out_path = build_archive_snapshot_path(repo, "SELF_TEST", "self_test")
    result = project_archive_overlay_to_nonlive_snapshot(repo, out_path)
    assert Path(result["output_json_path"]).exists()
    print("PASS: nonlive_overlay_projector self-test")
