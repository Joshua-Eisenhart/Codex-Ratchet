#!/usr/bin/env python3
"""Build a deterministic, lean source ZIP for the integrated ConstraintBox system.

The archive is a source-and-evidence package, not a Python virtual environment.
It keeps the Light controller, the ZIP Agent transport, the curated wave/MMM
material, and the current context in one reproducible tree while keeping the
JAX/Heavy interpreter outside the archive.  The source package roots are merged
under ``runtime/controller_src`` and ``runtime/zip_agent_src`` so a fresh
extract has one unambiguous package location for each runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable


VERSION = "0.1.0"
TOP_LEVEL = "constraintbox-integrated-system-v1"
MANIFEST_SCHEMA = "constraintbox.integrated-system-manifest.v1"
METADATA_SCHEMA = "constraintbox.integrated-system-metadata.v1"
BUILD_SCHEMA = "constraintbox.integrated-system-build.v1"

_EXCLUDED_PARTS = frozenset(
    {
        ".git",
        ".hypothesis",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        "build",
        "dist",
        "*.egg-info",
        ".DS_Store",
        ".AppleDouble",
        "cache",
        "caches",
    }
)
_EXCLUDED_SUFFIXES = frozenset({".pyc", ".pyo", ".sqlite", ".sqlite3", ".db"})
_EXCLUDED_NAMES = frozenset(
    {
        "probe_rows.jsonl",
        "gate_rows.jsonl",
        "events.jsonl",
        "run.log",
        "latest.log",
    }
)
_RAW_ROW_MARKERS = ("probe_rows", "gate_rows", "raw_rows")

# The root source package contains many historical and experimental modules.
# Only these additional modules are merged into the current Light package.  A
# same-named file already supplied by Light is retained once, from Light.
_ROOT_CONTROLLER_MODULES = (
    "basin_view_valve.py",
    "bound_quotient.py",
    "contained_light.py",
    "claude_bridge_adapter.py",
    "codex_cli_adapter.py",
    "grok_cli_adapter.py",
    "hook_adapter.py",
    "hook_lifecycle.py",
    "ingress_capture.py",
    "intake.py",
    "manifold_foundation.py",
    "mmm_load_gate.py",
    "provider_call_receipt.py",
    "quarantine_broker.py",
    "distinguishability.py",
)

_ROOT_SCRIPT_FILES = (
    "audit_cb_light_heavy_separation.py",
    "build_cb_light_manifest.py",
    "cb_light_cli.py",
    "cb_light_install_probe.py",
    "cb_light_metadata_probe.py",
    "cb_light_select.py",
    "cb_light_tool_status_ledger.py",
    "exercise_cb_light_hook_boundaries.py",
    "install_cb_universal_hooks.py",
    "prove_dependencies_used.py",
    "verify_install.py",
    "verify_wheel.py",
)

_ROOT_TEST_PREFIXES = (
    "test_bound_quotient.py",
    "test_cb_light",
    "test_contained_light.py",
    "test_claude_bridge_adapter.py",
    "test_codex_cli_adapter.py",
    "test_constraints",
    "test_control_plane.py",
    "test_distinguishability.py",
    "test_dualsolve.py",
    "test_entropic_time_field.py",
    "test_hook",
    "test_grok_cli_adapter.py",
    "test_ingress_capture.py",
    "test_manifold_foundation.py",
    "test_mini_lev",
    "test_mmm",
    "test_package_resources.py",
    "test_premortem",
    "test_provider_call_receipt.py",
    "test_wave",
)


class BundleError(ValueError):
    """Raised when the source tree cannot form the declared artifact."""


@dataclass(frozen=True)
class Payload:
    """One archive payload and its source path."""

    destination: str
    source: Path | None
    data: bytes
    mode: int


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")


def _safe_destination(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise BundleError(f"unsafe archive destination: {value!r}")
    return path.as_posix()


def _is_excluded(path: Path) -> bool:
    name = path.name
    if name in _EXCLUDED_NAMES or path.suffix in _EXCLUDED_SUFFIXES:
        return True
    if any(part in _EXCLUDED_PARTS or part.endswith(".egg-info") for part in path.parts):
        return True
    lower_name = name.lower()
    return any(marker in lower_name for marker in _RAW_ROW_MARKERS)


def _assert_not_symlink(path: Path, label: str) -> None:
    if path.is_symlink():
        raise BundleError(f"symlink {label} is not permitted: {path}")


def _iter_files(root: Path) -> Iterable[Path]:
    """Yield ordinary files in stable order, rejecting symlinked entries."""

    if not root.exists() or not root.is_dir():
        raise BundleError(f"required directory is missing: {root}")
    _assert_not_symlink(root, "directory")
    for current, directories, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        kept_directories: list[str] = []
        for name in sorted(directories):
            child = current_path / name
            if child.is_symlink():
                raise BundleError(f"symlink source directory is not permitted: {child}")
            if not _is_excluded(child):
                kept_directories.append(name)
        directories[:] = kept_directories
        for name in sorted(files):
            path = current_path / name
            if path.is_symlink():
                raise BundleError(f"symlink payload is not permitted: {path}")
            if not _is_excluded(path) and path.is_file():
                yield path


def _read_source(path: Path, *, label: str) -> tuple[bytes, int]:
    if not path.exists() or not path.is_file():
        raise BundleError(f"required file is missing ({label}): {path}")
    _assert_not_symlink(path, "file")
    return path.read_bytes(), stat.S_IMODE(path.stat().st_mode)


def _payload_from_file(source: Path, destination: str, *, label: str) -> Payload:
    data, mode = _read_source(source, label=label)
    return Payload(_safe_destination(destination), source, data, mode)


def _add_tree(
    payloads: list[Payload],
    *,
    box_root: Path,
    source_relative: str,
    destination_prefix: str,
    predicate: Callable[[Path], bool] | None = None,
) -> None:
    source_root = box_root / source_relative
    for source in _iter_files(source_root):
        if predicate is not None and not predicate(source):
            continue
        relative = source.relative_to(source_root).as_posix()
        payloads.append(
            _payload_from_file(
                source,
                f"{destination_prefix.rstrip('/')}/{relative}",
                label=source_relative,
            )
        )


def _add_optional_tree(
    payloads: list[Payload],
    *,
    box_root: Path,
    source_relative: str,
    destination_prefix: str,
    predicate: Callable[[Path], bool] | None = None,
) -> None:
    if (box_root / source_relative).is_dir():
        _add_tree(
            payloads,
            box_root=box_root,
            source_relative=source_relative,
            destination_prefix=destination_prefix,
            predicate=predicate,
        )


def _root_test_selected(path: Path) -> bool:
    name = path.name
    return any(name == prefix or name.startswith(prefix) for prefix in _ROOT_TEST_PREFIXES)


def _integrated_selected(path: Path) -> bool:
    # Keep current run receipts and context, but not generated caches, SQLite,
    # bytecode, or raw campaign rows.  The full prompt corpus is intentional:
    # it is the durable context requested by the owner, not an execution log.
    return True


def _payload_paths(box_root: Path) -> list[Payload]:
    """Collect the exact source closure used by the integrated ZIP."""

    required_files = (
        ("integrated_system/00_READ_THIS_FIRST.md", "00_READ_THIS_FIRST.md"),
        ("integrated_system/SYSTEM_ARCHITECTURE.md", "SYSTEM_ARCHITECTURE.md"),
        ("integrated_system/HOW_TO_RUN.md", "HOW_TO_RUN.md"),
        ("integrated_system/WHAT_IS_PROVEN.md", "WHAT_IS_PROVEN.md"),
        ("integrated_system/bin/cb", "bin/cb"),
        ("integrated_system/context/current/OWNER_OBJECT.md", "PROJECT/constraint_box/integrated_system/context/current/OWNER_OBJECT.md"),
        ("integrated_system/context/current/CURRENT_PLAN.md", "PROJECT/constraint_box/integrated_system/context/current/CURRENT_PLAN.md"),
        ("integrated_system/context/current/FAILURE_MEMORY.md", "PROJECT/constraint_box/integrated_system/context/current/FAILURE_MEMORY.md"),
        ("integrated_system/state/GENESIS.json", "PROJECT/constraint_box/integrated_system/state/GENESIS.json"),
        ("integrated_system/skills/MANIFEST.txt", "PROJECT/constraint_box/integrated_system/skills/MANIFEST.txt"),
    )
    payloads: list[Payload] = []
    for source_relative, destination in required_files:
        payloads.append(
            _payload_from_file(box_root / source_relative, destination, label=source_relative)
        )

    # Keep the complete integrated context, skill, MMM, fixture, run, test, and
    # script surfaces.  The iterator removes caches and raw row dumps.
    _add_tree(
        payloads,
        box_root=box_root,
        source_relative="integrated_system",
        destination_prefix="PROJECT/constraint_box/integrated_system",
        predicate=_integrated_selected,
    )

    # Canonical controller source: Light first, then only root modules that do
    # not already exist under Light.  This gives one package path and prevents
    # PYTHONPATH order from selecting an accidental legacy duplicate.
    controller_destination = "PROJECT/constraint_box/integrated_system/runtime/controller_src"
    light_src = box_root / "light_runtime/src"
    light_source_relative = "light_runtime/src"
    if not light_src.is_dir():
        # A fresh extract already has the merged source.  Rebuilding from that
        # extract is supported and remains byte-stable; no second package tree
        # is synthesized.
        light_src = box_root / "integrated_system/runtime/controller_src"
        light_source_relative = "integrated_system/runtime/controller_src"
    _add_tree(
        payloads,
        box_root=box_root,
        source_relative=light_source_relative,
        destination_prefix=controller_destination,
    )
    light_names = {
        path.relative_to(light_src).as_posix() for path in _iter_files(light_src)
    }
    for name in _ROOT_CONTROLLER_MODULES:
        source = box_root / "src/constraintbox" / name
        if not source.is_file():
            # The canonical merged tree is already authoritative in a bundle
            # extracted from this builder.  It does not carry the legacy root
            # source tree, so there is no additional module to merge here.
            if (light_src / "constraintbox" / name).is_file():
                continue
            if (
                box_root
                / "integrated_system"
                / "runtime"
                / "controller_src"
                / "constraintbox"
                / name
            ).is_file():
                continue
            raise BundleError(f"selected controller module is missing: {source}")
        relative = f"constraintbox/{name}"
        if relative in light_names:
            light_bytes = (light_src / relative).read_bytes()
            root_bytes = source.read_bytes()
            if light_bytes != root_bytes:
                raise BundleError(
                    f"duplicate controller module differs between Light and root: {name}"
                )
            continue
        payloads.append(
            _payload_from_file(
                source,
                f"{controller_destination}/{relative}",
                label="selected root controller module",
            )
        )

    # The root package has a few data files used by older modules.  The Light
    # copy is the sole runtime authority; a differing root copy is intentionally
    # omitted rather than creating a second registry with ambiguous meaning.
    for relative in ("constraintbox/core_tool_registry_v9.json",):
        source = box_root / "src" / relative
        if source.is_file():
            destination = f"{controller_destination}/{relative}"
            light_source = light_src / relative
            if not light_source.is_file():
                payloads.append(_payload_from_file(source, destination, label="controller data"))

    # ZIP Agent is a separate runtime package, not merged into constraintbox.
    zip_source_relative = "zip_agent/src"
    if not (box_root / zip_source_relative).is_dir():
        zip_source_relative = "integrated_system/runtime/zip_agent_src"
    _add_tree(
        payloads,
        box_root=box_root,
        source_relative=zip_source_relative,
        destination_prefix="PROJECT/constraint_box/integrated_system/runtime/zip_agent_src",
    )
    if (box_root / "zip_agent/src").is_dir():
        _add_tree(
            payloads,
            box_root=box_root,
            source_relative="zip_agent/src",
            destination_prefix="PROJECT/constraint_box/zip_agent/src",
        )

    # Keep package metadata, ZIP documentation/tests, and selected runnable
    # Light scripts.  Source tests are evidence and do not become authority.
    for source_relative, destination in (
        ("light_runtime/pyproject.toml", "PROJECT/constraint_box/light_runtime/pyproject.toml"),
        ("zip_agent/pyproject.toml", "PROJECT/constraint_box/zip_agent/pyproject.toml"),
        ("zip_agent/README.md", "PROJECT/constraint_box/zip_agent/README.md"),
        ("mmm/README.md", "PROJECT/constraint_box/mmm/README.md"),
    ):
        source = box_root / source_relative
        if source.is_file():
            payloads.append(_payload_from_file(source, destination, label=source_relative))
    _add_tree(
        payloads,
        box_root=box_root,
        source_relative="mmm/packs",
        destination_prefix="PROJECT/constraint_box/mmm/packs",
    )

    # Preserve the canonical Light build source as a build-input surface.  The
    # merged controller tree above is the execution overlay; this tree exists
    # so `bootstrap-light` can rebuild the wheel and re-attest the 72-path
    # Light contract after fresh extraction.
    if (box_root / "light_runtime/src").is_dir():
        _add_tree(
            payloads,
            box_root=box_root,
            source_relative="light_runtime/src",
            destination_prefix="PROJECT/constraint_box/light_runtime/src",
        )
    for source_relative, destination in (
        (".gitignore", "PROJECT/constraint_box/.gitignore"),
        ("light_runtime/.gitignore", "PROJECT/constraint_box/light_runtime/.gitignore"),
        ("CB_FOUNDATION_REQUIREMENTS.md", "PROJECT/constraint_box/CB_FOUNDATION_REQUIREMENTS.md"),
    ):
        source = box_root / source_relative
        if source.is_file():
            payloads.append(_payload_from_file(source, destination, label=source_relative))
    _add_tree(
        payloads,
        box_root=box_root,
        source_relative="config",
        destination_prefix="PROJECT/constraint_box/config",
    )
    _add_optional_tree(
        payloads,
        box_root=box_root,
        source_relative="requirements",
        destination_prefix="PROJECT/constraint_box/requirements",
    )
    _add_tree(
        payloads,
        box_root=box_root,
        source_relative="fixtures",
        destination_prefix="PROJECT/constraint_box/fixtures",
    )
    _add_tree(
        payloads,
        box_root=box_root,
        source_relative="scripts/contained_light",
        destination_prefix="PROJECT/constraint_box/scripts/contained_light",
    )
    for name in _ROOT_SCRIPT_FILES:
        source = box_root / "scripts" / name
        if source.is_file():
            payloads.append(
                _payload_from_file(source, f"PROJECT/constraint_box/scripts/{name}", label="Light script")
            )
    _add_tree(
        payloads,
        box_root=box_root,
        source_relative="hooks",
        destination_prefix="PROJECT/constraint_box/hooks",
    )
    claude_hook_root = box_root / "integrated_system" / "hooks" / "claude"
    if claude_hook_root.is_dir():
        for source in _iter_files(claude_hook_root):
            relative = source.relative_to(claude_hook_root).as_posix()
            payloads.append(
                _payload_from_file(
                    source,
                    f"PROJECT/.claude/{relative}",
                    label="portable Claude project hook",
                )
            )
    _add_optional_tree(
        payloads,
        box_root=box_root,
        source_relative="bin",
        destination_prefix="PROJECT/constraint_box/bin",
    )
    _add_optional_tree(
        payloads,
        box_root=box_root,
        source_relative="experiments/manifold_capability/v1",
        destination_prefix="PROJECT/constraint_box/experiments/manifold_capability/v1",
    )
    _add_tree(
        payloads,
        box_root=box_root,
        source_relative="zip_agent/tests",
        destination_prefix="PROJECT/constraint_box/zip_agent/tests",
    )
    _add_tree(
        payloads,
        box_root=box_root,
        source_relative="zip_agent/skills",
        destination_prefix="PROJECT/constraint_box/zip_agent/skills",
    )
    root_tests = box_root / "tests"
    if root_tests.is_dir():
        _add_tree(
            payloads,
            box_root=box_root,
            source_relative="tests",
            destination_prefix="PROJECT/constraint_box/tests",
            predicate=_root_test_selected,
        )

    # Root source files are useful for audit only when selected explicitly.  A
    # full second package tree would recreate the very ambiguity this bundle
    # is intended to remove.
    by_destination: dict[str, Payload] = {}
    for payload in payloads:
        if payload.destination in by_destination:
            previous = by_destination[payload.destination]
            if previous.data != payload.data:
                raise BundleError(f"duplicate destination has different bytes: {payload.destination}")
            # Identical duplicate source selections are still dropped so the
            # ZIP has one member and the manifest has one row.
            continue
        by_destination[payload.destination] = payload
    return [by_destination[name] for name in sorted(by_destination)]


def _manifest(payloads: list[Payload]) -> dict[str, object]:
    rows = [
        {
            "path": payload.destination,
            "bytes": len(payload.data),
            "sha256": _sha256(payload.data),
            "mode": f"{payload.mode:04o}",
        }
        for payload in payloads
    ]
    return {
        "schema": MANIFEST_SCHEMA,
        "bundle_kind": "integrated-source-system",
        "version": VERSION,
        "top_level": TOP_LEVEL,
        "file_count": len(rows),
        "payload_bytes": sum(row["bytes"] for row in rows),
        "files": rows,
        "layout": {
            "entrypoint": "bin/cb",
            "controller_source": "PROJECT/constraint_box/integrated_system/runtime/controller_src",
            "light_build_source": "PROJECT/constraint_box/light_runtime/src",
            "zip_agent_source": "PROJECT/constraint_box/integrated_system/runtime/zip_agent_src",
            "integrated_system": "PROJECT/constraint_box/integrated_system",
            "context_corpus": "PROJECT/constraint_box/integrated_system/context/full/prompt_plan_progress_corpus.jsonl",
        },
        "light_heavy_boundary": {
            "light_source_is_merged_controller": True,
            "jax_in_light": False,
            "heavy_interpreter_included": False,
            "heavy_source_included": False,
            "provider_credentials_included": False,
        },
        "excluded": {
            "virtual_environments": True,
            "caches_and_bytecode": True,
            "bulk_receipts": True,
            "raw_campaign_rows": True,
            "project_state_object_store": True,
            "external_heavy_estate": True,
        },
        "promotion_allowed": False,
    }


def _metadata(manifest: dict[str, object], manifest_bytes: bytes) -> dict[str, object]:
    rows = manifest["files"]
    assert isinstance(rows, list)
    return {
        "schema": METADATA_SCHEMA,
        "bundle_kind": manifest["bundle_kind"],
        "version": VERSION,
        "top_level": TOP_LEVEL,
        "manifest_sha256": _sha256(manifest_bytes),
        "payload_file_count": len(rows),
        "payload_bytes": manifest["payload_bytes"],
        "deterministic_zip": True,
        "zip_timestamp": "1980-01-01T00:00:00Z",
        # Do not bind the archive to the builder checkout's ambient Git HEAD.
        # The manifest hashes are the source identity and remain stable after a
        # fresh extract or on a machine without Git.
        "source_revision": None,
        "claim_ceiling": (
            "source-contained integrated candidate with local fresh-extract checks; "
            "not portable installation, provider execution, Heavy admission, "
            "scientific validation, or promotion"
        ),
        "promotion_allowed": False,
    }

def _checksums(payloads: list[Payload], manifest_bytes: bytes, metadata_bytes: bytes) -> bytes:
    rows = [(f"{TOP_LEVEL}/{payload.destination}", _sha256(payload.data)) for payload in payloads]
    rows.extend(
        [
            (f"{TOP_LEVEL}/SYSTEM_MANIFEST.json", _sha256(manifest_bytes)),
            (f"{TOP_LEVEL}/BUNDLE_METADATA.json", _sha256(metadata_bytes)),
        ]
    )
    return "".join(f"{digest}  {path}\n" for path, digest in sorted(rows, key=lambda item: item[0])).encode("utf-8")


def _zip_info(name: str, mode: int) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    regular_mode = stat.S_IFREG | (mode & 0o7777)
    info.external_attr = regular_mode << 16
    return info


def build_bundle(box_root: Path, output: Path) -> dict[str, object]:
    """Build one archive atomically; refuse to overwrite an existing artifact."""

    box_root = box_root.expanduser().absolute()
    output = output.expanduser().absolute()
    if not box_root.is_dir():
        raise BundleError(f"box root is not a directory: {box_root}")
    if output.exists():
        raise BundleError(f"refusing to overwrite existing output: {output}")
    payloads = _payload_paths(box_root)
    manifest = _manifest(payloads)
    manifest_bytes = _json_bytes(manifest)
    metadata = _metadata(manifest, manifest_bytes)
    metadata_bytes = _json_bytes(metadata)
    checksums_bytes = _checksums(payloads, manifest_bytes, metadata_bytes)
    envelope = {
        "manifest": Payload(f"{TOP_LEVEL}/SYSTEM_MANIFEST.json", None, manifest_bytes, 0o644),
        "metadata": Payload(f"{TOP_LEVEL}/BUNDLE_METADATA.json", None, metadata_bytes, 0o644),
        "checksums": Payload(f"{TOP_LEVEL}/SHA256SUMS", None, checksums_bytes, 0o644),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    os.close(file_descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(
            temporary,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
            strict_timestamps=True,
        ) as archive:
            for payload in payloads:
                archive.writestr(
                    _zip_info(f"{TOP_LEVEL}/{payload.destination}", payload.mode),
                    payload.data,
                )
            for payload in envelope.values():
                archive.writestr(_zip_info(payload.destination, payload.mode), payload.data)
        temporary.replace(output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return {
        "schema": BUILD_SCHEMA,
        "state": "BUILT",
        "bundle": str(output),
        "bundle_sha256": _sha256(output.read_bytes()),
        "bundle_bytes": output.stat().st_size,
        "manifest_sha256": _sha256(manifest_bytes),
        "manifest_file_count": manifest["file_count"],
        "payload_bytes": manifest["payload_bytes"],
        "top_level": TOP_LEVEL,
        "promotion_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--box-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = build_bundle(args.box_root, args.output)
    except (BundleError, OSError, zipfile.BadZipFile) as exc:
        print(
            json.dumps(
                {
                    "schema": BUILD_SCHEMA,
                    "state": "FAILED",
                    "error": str(exc),
                    "promotion_allowed": False,
                },
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
