"""Read-only custody field for the bounded contained-Light operation routes.

This is a probe fixture, not a registry of permanent operations or a policy
engine.  It asks a smaller question than semantic replay: do the checkout,
generated manifest, and installed route describe the same executable material?
The result exposes an observed source-custody boundary as a candidate mountain
pass.  It never repairs a manifest, writes SQLite, or executes a Mini-Lev task.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from hookkernel.cb_light_runtime import ROOT

SCHEMA = "constraintbox.operation-custody-field.v1"


@dataclass(frozen=True)
class Binding:
    """A checkout logical file and the installed module/data file that uses it."""

    label: str
    logical_path: str
    module: str
    module_relative_path: str | None = None


@dataclass(frozen=True)
class Surface:
    """A finite hypothesis about one current contained-Light operation route."""

    surface_id: str
    command: str
    source_custody_enforced_by_route: bool
    bindings: tuple[Binding, ...]


_TRANSITION_BINDINGS = (
    Binding("transition", "light_runtime/src/constraintbox/transition_mini_lev.py", "constraintbox.transition_mini_lev"),
    Binding("core_cli", "light_runtime/src/constraintbox/core_cli.py", "constraintbox.core_cli"),
    Binding("core_tools", "light_runtime/src/constraintbox/core_tools.py", "constraintbox.core_tools"),
    Binding("control_plane", "light_runtime/src/constraintbox/control_plane.py", "constraintbox.control_plane"),
    Binding("probes", "light_runtime/src/constraintbox/cb_light_probes.py", "constraintbox.cb_light_probes"),
    Binding(
        "registry",
        "config/core_tool_registry_v9.json",
        "constraintbox.transition_mini_lev",
        "core_tool_registry_v9.json",
    ),
    Binding("domain", "light_runtime/src/hookkernel/cb_light_domain.py", "hookkernel.cb_light_domain"),
    Binding("mini_lev_state", "light_runtime/src/hookkernel/cb_light_minilev_state.py", "hookkernel.cb_light_minilev_state"),
    Binding("runtime", "light_runtime/src/hookkernel/cb_light_runtime.py", "hookkernel.cb_light_runtime"),
    Binding("state", "light_runtime/src/hookkernel/cb_light_state.py", "hookkernel.cb_light_state"),
)


SURFACES: dict[str, Surface] = {
    "mini_lev_symbolic": Surface(
        surface_id="mini_lev_symbolic",
        command="mini-lev",
        # This path records its own source digest, but does not currently
        # compare it with the checkout-generated manifest before dispatch.
        source_custody_enforced_by_route=False,
        bindings=(
            Binding("core_cli", "light_runtime/src/constraintbox/core_cli.py", "constraintbox.core_cli"),
            Binding("bridge", "light_runtime/src/constraintbox/mini_lev_bridge.py", "constraintbox.mini_lev_bridge"),
            Binding("control_plane", "light_runtime/src/constraintbox/control_plane.py", "constraintbox.control_plane"),
            Binding(
                "registry",
                "config/core_tool_registry_v9.json",
                "constraintbox.mini_lev_bridge",
                "core_tool_registry_v9.json",
            ),
            Binding("mini_lev_state", "light_runtime/src/hookkernel/cb_light_minilev_state.py", "hookkernel.cb_light_minilev_state"),
            Binding("state", "light_runtime/src/hookkernel/cb_light_state.py", "hookkernel.cb_light_state"),
        ),
    ),
    "mini_lev_transition": Surface(
        surface_id="mini_lev_transition",
        command="mini-lev-transition",
        source_custody_enforced_by_route=True,
        bindings=_TRANSITION_BINDINGS,
    ),
}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_file(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, type(exc).__name__
    return (body, None) if isinstance(body, dict) else (None, "NOT_OBJECT")


def _manifest_status(root: Path) -> tuple[dict[str, Any], dict[str, str], tuple[str, ...]]:
    manifest_path = root / "config" / "cb_light_tools_v1.json"
    contract_path = root / "config" / "cb_light_contract_v1.json"
    manifest, manifest_error = _load_json(manifest_path)
    contract, contract_error = _load_json(contract_path)
    source_hashes = manifest.get("source_hashes") if manifest else None
    expected = source_hashes if isinstance(source_hashes, dict) else {}
    manifest_identity_ok = False
    if manifest is not None:
        identity = dict(manifest)
        stored = identity.pop("manifest_sha256", None)
        manifest_identity_ok = (
            manifest.get("schema") == "constraintbox.cb-light-tool-manifest.v1"
            and isinstance(stored, str)
            and hashlib.sha256(_canonical_bytes(identity)).hexdigest() == stored
        )
    required = contract.get("required_source_paths") if contract else None
    contract_paths = tuple(item for item in required if isinstance(item, str)) if isinstance(required, list) else ()
    return (
        {
            "manifest_path": str(manifest_path),
            "manifest_error": manifest_error,
            "manifest_identity_ok": manifest_identity_ok,
            "source_hash_count": len(expected),
            "contract_path": str(contract_path),
            "contract_error": contract_error,
            "contract_source_count": len(contract_paths),
        },
        {str(key): str(value) for key, value in expected.items() if isinstance(value, str)},
        contract_paths,
    )


_RUNTIME_INSPECTOR = """
import importlib
import json
import sys

names = json.loads(sys.argv[1])
results = {}
for name in names:
    try:
        module = importlib.import_module(name)
        path = getattr(module, "__file__", None)
        results[name] = {"path": path, "error": None}
    except Exception as exc:
        results[name] = {"path": None, "error": type(exc).__name__}
print(json.dumps(results, sort_keys=True))
"""


def inspect_runtime_modules(python_executable: Path, modules: Iterable[str]) -> dict[str, dict[str, Any]]:
    """Read runtime import origins under isolated mode; never dispatch an operation."""

    names = tuple(sorted(set(modules)))
    completed = subprocess.run(
        [str(python_executable), "-I", "-c", _RUNTIME_INSPECTOR, json.dumps(names)],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    if completed.returncode != 0:
        return {
            name: {"path": None, "error": "RUNTIME_INSPECTOR_FAILED", "returncode": completed.returncode}
            for name in names
        }
    try:
        body = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {name: {"path": None, "error": "RUNTIME_INSPECTOR_INVALID_JSON"} for name in names}
    return body if isinstance(body, dict) else {name: {"path": None, "error": "RUNTIME_INSPECTOR_NOT_OBJECT"} for name in names}


def _binding_row(
    binding: Binding,
    *,
    root: Path,
    expected_hashes: dict[str, str],
    contract_paths: tuple[str, ...],
    runtime_modules: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    runtime_info = runtime_modules.get(binding.module, {})
    raw_runtime = runtime_info.get("path")
    runtime_path = Path(str(raw_runtime)) if isinstance(raw_runtime, str) and raw_runtime else None
    if runtime_path is not None and binding.module_relative_path is not None:
        runtime_path = runtime_path.with_name(binding.module_relative_path)
    checkout_path = root / binding.logical_path
    expected = expected_hashes.get(binding.logical_path)
    checkout_sha = _sha256_file(checkout_path)
    runtime_sha = _sha256_file(runtime_path) if runtime_path is not None else None
    if not isinstance(expected, str) or len(expected) != 64:
        status = "MANIFEST_UNBOUND"
    elif checkout_sha is None:
        status = "CHECKOUT_UNREADABLE"
    elif runtime_sha is None:
        status = "RUNTIME_UNREADABLE"
    elif checkout_sha == expected and runtime_sha == expected:
        status = "CURRENT"
    elif checkout_sha != expected and runtime_sha == expected:
        status = "CHECKOUT_DRIFT"
    elif checkout_sha == expected and runtime_sha != expected:
        status = "RUNTIME_DRIFT"
    else:
        status = "SPLIT_DRIFT"
    return {
        "label": binding.label,
        "logical_path": binding.logical_path,
        "runtime_module": binding.module,
        "runtime_path": str(runtime_path) if runtime_path is not None else None,
        "expected_sha256": expected,
        "checkout_sha256": checkout_sha,
        "runtime_sha256": runtime_sha,
        "contract_bound": binding.logical_path in contract_paths,
        "status": status,
    }


def inspect_surface(
    surface: Surface,
    *,
    root: Path,
    expected_hashes: dict[str, str],
    contract_paths: tuple[str, ...],
    runtime_modules: dict[str, dict[str, Any]],
    global_source_set_ok: bool,
) -> dict[str, Any]:
    rows = [
        _binding_row(
            binding,
            root=root,
            expected_hashes=expected_hashes,
            contract_paths=contract_paths,
            runtime_modules=runtime_modules,
        )
        for binding in surface.bindings
    ]
    blockers = [row["logical_path"] for row in rows if row["status"] != "CURRENT" or not row["contract_bound"]]
    if not global_source_set_ok:
        blockers.append("contained_source_set")
    status = "CUSTODY_CURRENT" if not blockers else "HOLD_SOURCE_CUSTODY"
    return {
        "surface_id": surface.surface_id,
        "command": surface.command,
        "source_custody_enforced_by_route": surface.source_custody_enforced_by_route,
        "status": status,
        "bindings": rows,
        "blockers": sorted(set(blockers)),
        "mountain_pass_hypothesis": {
            "kind": "source_custody",
            "condition": "each bound checkout and runtime digest equals one generated manifest digest and the contained source set is complete",
            "observed_boundary": "HOLD" if blockers else "candidate pass",
            "route_enforced": surface.source_custody_enforced_by_route,
            "ceiling": "a current-code custody boundary only; not semantic replay, operation correctness, selection, or adoption",
        },
    }


def _manifest_builder_status(root: Path, python_executable: Path) -> dict[str, Any]:
    """Run the existing no-output source-set verifier without modifying its manifest."""

    script = root / "scripts" / "build_cb_light_manifest.py"
    completed = subprocess.run(
        [str(python_executable), str(script), "--root", str(root), "--output", os.devnull],
        capture_output=True,
        check=False,
        text=True,
        timeout=60,
    )
    return {
        "attempted": True,
        "returncode": completed.returncode,
        "source_set_current": completed.returncode == 0,
        "stderr_tail": completed.stderr.strip().splitlines()[-1:] if completed.stderr.strip() else [],
        "stdout_tail": completed.stdout.strip().splitlines()[-1:] if completed.stdout.strip() else [],
    }


def _absolute_executable(root: Path, python_executable: Path) -> Path:
    """Make a requested interpreter path absolute without dereferencing a venv symlink."""

    return python_executable if python_executable.is_absolute() else root / python_executable


def run_field(
    *,
    root: Path = ROOT,
    python_executable: Path | None = None,
    surface_ids: Iterable[str] | None = None,
    verify_source_set: bool = True,
) -> dict[str, Any]:
    """Map finite source-custody surfaces; this deliberately performs no route work."""

    selected_ids = tuple(surface_ids or tuple(SURFACES))
    unknown = sorted(set(selected_ids).difference(SURFACES))
    if unknown:
        raise ValueError(f"unknown custody surfaces: {unknown}")
    root = root.resolve()
    # Do not call Path.resolve() here: `.venv/bin/python` is normally a
    # symlink to the base interpreter, and dereferencing it silently removes
    # the virtual environment's site-packages from an isolated subprocess.
    executable = _absolute_executable(root, python_executable or Path(sys.executable))
    manifest_status, expected_hashes, contract_paths = _manifest_status(root)
    builder = _manifest_builder_status(root, executable) if verify_source_set else {
        "attempted": False,
        "returncode": None,
        "source_set_current": False,
        "stderr_tail": [],
        "stdout_tail": [],
    }
    selected = [SURFACES[surface_id] for surface_id in selected_ids]
    modules = (binding.module for surface in selected for binding in surface.bindings)
    runtime_modules = inspect_runtime_modules(executable, modules)
    surfaces = [
        inspect_surface(
            surface,
            root=root,
            expected_hashes=expected_hashes,
            contract_paths=contract_paths,
            runtime_modules=runtime_modules,
            global_source_set_ok=builder["source_set_current"],
        )
        for surface in selected
    ]
    return {
        "schema": SCHEMA,
        "profile": "cb_light",
        "root": str(root),
        "runtime": {"python_executable": str(executable)},
        "manifest": manifest_status,
        "source_set": builder,
        "surfaces": surfaces,
        "counts": {
            "surfaces": len(surfaces),
            "custody_current": sum(surface["status"] == "CUSTODY_CURRENT" for surface in surfaces),
            "held": sum(surface["status"] != "CUSTODY_CURRENT" for surface in surfaces),
        },
        "promotion_allowed": False,
        "claim_ceiling": (
            "read-only contained-Light source/runtime custody field only; no operation execution, semantic replay, "
            "selection, adoption, host-hook, provider, model, CB Heavy, promotion, or release claim"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Map finite CB Light operation source-custody surfaces.")
    parser.add_argument("--python", dest="python_executable", type=Path, default=Path(sys.executable))
    parser.add_argument("--surface", action="append", choices=sorted(SURFACES))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--skip-source-set-check", action="store_true")
    args = parser.parse_args(argv)
    body = run_field(
        python_executable=args.python_executable,
        surface_ids=args.surface,
        verify_source_set=not args.skip_source_set_check,
    )
    rendered = json.dumps(body, sort_keys=True, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
