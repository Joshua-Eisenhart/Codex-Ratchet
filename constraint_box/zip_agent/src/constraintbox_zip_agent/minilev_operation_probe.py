"""Bounded ZIP-side adapter for the contained CB Light polynomial Mini-Lev.

This module is deliberately a subprocess adapter.  The ZIP-agent interpreter
must not accidentally resolve ``constraintbox`` from the legacy checkout
``src`` tree: the operation is run with the declared contained-Light
interpreter and an isolated ``-I`` process after comparing installed source
bytes with ``light_runtime/src``.  A temporary SQLite backup is used for every
case, so even the successful append-only Mini-Lev attempt never writes the
caller-owned state.

The probe cohort is evidence about this one bounded operation.  It records the
actual five-role path (Pydantic + JSON Schema boundary, Rustworkx topology,
SymPy witness, CVC5 degree cross-check, and Z3 independent cross-check),
severs/injects each role in a fresh process, and records a real AB/BA
composition.  Nothing here updates a core list or makes an admission claim.
"""

from __future__ import annotations

import copy
import json
import os
import re
import sqlite3
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .protocol import (
    TaskSpec,
    ZipJobRefusal,
    build_packet,
    canonical_json_bytes,
    sha256_bytes,
    strict_json_loads,
)


SCHEMA = "constraintbox.minilev_operation_probe.v1"
COHORT_SCHEMA = "constraintbox.minilev_operation_probe_cohort.v1"
REQUEST_SCHEMA = "constraintbox.mini-lev-polynomial-request.v1"
LIGHT_SUCCESS = "MINILEV_BRIDGE_EVALUATED_LOCAL"

# This ceiling is intentionally narrower than the contained Light runtime's
# own statement: this adapter additionally refuses any portability, provider,
# core, or admission interpretation of a local observation.
CLAIM_CEILING = (
    "contained-Light Mini-Lev polynomial operation and bounded role/order "
    "observations only;not core;not admission;not provider;not portability;"
    "not release;not semantic truth"
)

LIGHT_ROOT_ENV = "CB_LIGHT_ROOT"
LIGHT_INTERPRETER_ENV = "CB_LIGHT_INTERPRETER"

# These are the exact source files used by the current installed bridge.  The
# registry is part of the bridge's source digest and the state companion is
# imported by the bridge when constructing that digest.
LIGHT_SOURCE_FILES: dict[str, str] = {
    "constraintbox/mini_lev_bridge.py": "light_runtime/src/constraintbox/mini_lev_bridge.py",
    "constraintbox/core_tool_registry_v9.json": "light_runtime/src/constraintbox/core_tool_registry_v9.json",
    "hookkernel/cb_light_minilev_state.py": "light_runtime/src/hookkernel/cb_light_minilev_state.py",
}

ROLE_IDS = (
    "pydantic_jsonschema_typed_boundary",
    "rustworkx_topology",
    "sympy_witness",
    "cvc5_degree_crosscheck",
    "z3_independent_crosscheck",
)

_ROLE_SYMBOLS = {
    ROLE_IDS[0]: (
        "Draft202012Validator.validate",
        "_MiniLevRequest.model_validate",
    ),
    ROLE_IDS[1]: ("rustworkx.PyDiGraph",),
    ROLE_IDS[2]: ("sympy.Poly.degree",),
    ROLE_IDS[3]: ("cvc5.Solver",),
    ROLE_IDS[4]: ("z3.Solver",),
}

_SCHEMA_VERSION_RE = re.compile(r'^version\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
_VOLATILE_COLUMNS = frozenset({"captured_at", "created_at", "updated_at"})
_MAX_STATE_TABLES = 256
_MAX_STATE_ROWS = 100_000
_CHILD_TIMEOUT_SECONDS = 120
_SOURCE_TIMEOUT_SECONDS = 30
MINILEV_OPERATION_ID = "run_cb_minilev_operation_v1"
MINILEV_PROBE_OPERATION_ID = "probe_cb_minilev_operation_v1"


class MiniLevAdapterError(RuntimeError):
    """Internal bounded adapter error, converted into a HOLD receipt."""

    def __init__(self, reason_code: str, detail: str = "") -> None:
        super().__init__(f"{reason_code}:{detail}" if detail else reason_code)
        self.reason_code = reason_code
        self.detail = detail


def _path_text(path: Path) -> str:
    """Return an absolute, non-symlink-resolved path for identity receipts."""

    return os.path.normpath(os.path.abspath(os.fspath(path)))


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_light_root(light_root: Path | str | None = None) -> Path | None:
    configured = light_root or os.environ.get(LIGHT_ROOT_ENV)
    if configured:
        candidate = Path(configured).expanduser().absolute()
    else:
        # ``.../constraint_box/zip_agent/src/...`` -> the checkout root.  Do
        # not search arbitrary parents or fall back to the legacy src tree.
        candidate = Path(__file__).resolve().parents[3]
    if not (
        (candidate / "config/cb_light_contract_v1.json").is_file()
        and (candidate / "light_runtime/pyproject.toml").is_file()
    ):
        return None
    return candidate


def _resolve_interpreter(
    light_root: Path, interpreter: Path | str | None = None
) -> Path:
    configured = interpreter or os.environ.get(LIGHT_INTERPRETER_ENV)
    candidate = (
        Path(configured).expanduser().absolute()
        if configured
        else light_root / ".venv" / "bin" / "python"
    )
    return candidate


def _source_gate(
    light_root: Path | str | None,
    interpreter: Path | str | None,
) -> tuple[Path, dict[str, Any]]:
    """Resolve and attest the contained-Light route before request/state work."""

    root = _resolve_light_root(light_root)
    declared = _resolve_interpreter(root, interpreter) if root is not None else Path(str(interpreter or ""))
    source_probe_root: Path | str | None = root
    if root is None and light_root is not None:
        source_probe_root = light_root
    return declared, inspect_light_source_status(
        light_root=source_probe_root,
        interpreter=declared,
    )


def _source_hold(
    *,
    schema: str,
    source_status: Mapping[str, Any],
    interpreter: Path,
    request_sha256: str | None = None,
) -> dict[str, Any]:
    """Build a source-gate HOLD without touching or copying SQLite state."""

    return {
        "schema": schema,
        "disposition": "HOLD",
        "reason_code": str(source_status.get("reason_code", "HOLD_MINILEV_SOURCE_MISMATCH")),
        "request_sha256": request_sha256,
        "source": dict(source_status),
        "interpreter": {"declared": _path_text(interpreter)},
        "state_before": {},
        "state_after": {},
        "no_write_on_refusal": True,
        "state_copy_only": True,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def _source_probe_script() -> str:
    # Keep this script stdlib-only up to the import of the installed Light
    # modules.  It is run with ``-I`` and therefore cannot inherit PYTHONPATH.
    return r'''
import hashlib
import importlib.metadata
import json
import sys
import sysconfig
from pathlib import Path

def digest(path):
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, ValueError):
        return None

body = {
    "interpreter": str(sys.executable),
    "python_version": sys.version,
    "purelib": sysconfig.get_paths().get("purelib"),
}
try:
    import constraintbox
    import constraintbox.mini_lev_bridge as bridge
    import hookkernel
    import hookkernel.cb_light_minilev_state as state

    bridge_path = Path(bridge.__file__ or "")
    state_path = Path(state.__file__ or "")
    package_root = bridge_path.parent
    hook_root = state_path.parent
    files = {
        "constraintbox/mini_lev_bridge.py": bridge_path,
        "constraintbox/core_tool_registry_v9.json": package_root / "core_tool_registry_v9.json",
        "hookkernel/cb_light_minilev_state.py": state_path,
    }
    body.update({
        "constraintbox_origin": str(Path(constraintbox.__file__ or "")),
        "hookkernel_origin": str(Path(hookkernel.__file__ or "")),
        "files": {
            key: {"origin": str(path), "sha256": digest(path)}
            for key, path in files.items()
        },
        "constraintbox_version": importlib.metadata.version("constraintbox"),
    })
except BaseException as exc:
    body.update({
        "files": {},
        "error_type": type(exc).__name__,
        "error": str(exc),
    })
print(json.dumps(body, sort_keys=True, separators=(",", ":")))
'''


def inspect_light_source_status(
    *,
    light_root: Path | str | None = None,
    interpreter: Path | str | None = None,
) -> dict[str, Any]:
    """Compare the installed Light package with the checkout-owned sources.

    The returned status is observational.  A ``MATCH`` is required before any
    Mini-Lev child process is allowed to run; every other status is a HOLD.
    """

    root = _resolve_light_root(light_root)
    if root is None:
        return {
            "status": "HOLD",
            "reason_code": "HOLD_MINILEV_LIGHT_ROOT_UNBOUND",
            "detail": "No checkout with the contained CB Light contract was found.",
            "claim_ceiling": CLAIM_CEILING,
        }
    declared = _resolve_interpreter(root, interpreter)
    expected_root = root / "light_runtime" / "src"
    expected: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for installed_rel, light_rel in LIGHT_SOURCE_FILES.items():
        source = root / light_rel
        if not source.is_file():
            missing.append(light_rel)
            continue
        expected[installed_rel] = {
            "path": _path_text(source),
            "sha256": sha256_bytes(source.read_bytes()),
        }

    if not declared.is_file():
        return {
            "status": "HOLD",
            "reason_code": "HOLD_MINILEV_LIGHT_INTERPRETER_UNAVAILABLE",
            "detail": f"Declared contained-Light interpreter is missing: {_path_text(declared)}",
            "light_root": _path_text(root),
            "interpreter": {"declared": _path_text(declared)},
            "expected": expected,
            "missing_expected": missing,
            "claim_ceiling": CLAIM_CEILING,
        }
    if missing:
        return {
            "status": "HOLD",
            "reason_code": "HOLD_MINILEV_LIGHT_SOURCE_UNAVAILABLE",
            "detail": "One or more declared Light source files are missing.",
            "light_root": _path_text(root),
            "interpreter": {"declared": _path_text(declared)},
            "expected": expected,
            "missing_expected": missing,
            "claim_ceiling": CLAIM_CEILING,
        }

    try:
        completed = subprocess.run(
            [str(declared), "-I", "-c", _source_probe_script()],
            cwd=str(root),
            capture_output=True,
            check=False,
            text=True,
            timeout=_SOURCE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "status": "HOLD",
            "reason_code": "HOLD_MINILEV_SOURCE_PROBE_UNAVAILABLE",
            "detail": f"Contained-Light source probe could not start: {exc}",
            "light_root": _path_text(root),
            "interpreter": {"declared": _path_text(declared)},
            "expected": expected,
            "claim_ceiling": CLAIM_CEILING,
        }
    if completed.returncode != 0:
        return {
            "status": "HOLD",
            "reason_code": "HOLD_MINILEV_SOURCE_PROBE_FAILED",
            "detail": completed.stderr.strip()[-2000:] or "source probe failed",
            "returncode": completed.returncode,
            "light_root": _path_text(root),
            "interpreter": {"declared": _path_text(declared)},
            "expected": expected,
            "claim_ceiling": CLAIM_CEILING,
        }
    try:
        observed = strict_json_loads(completed.stdout.encode("utf-8"), label="Light source probe")
    except Exception as exc:
        return {
            "status": "HOLD",
            "reason_code": "HOLD_MINILEV_SOURCE_PROBE_INVALID",
            "detail": str(exc),
            "light_root": _path_text(root),
            "interpreter": {"declared": _path_text(declared)},
            "expected": expected,
            "claim_ceiling": CLAIM_CEILING,
        }
    if not isinstance(observed, dict):
        observed = {"files": {}, "error": "source probe returned a non-object"}

    installed = observed.get("files")
    if not isinstance(installed, dict):
        installed = {}
    mismatches: list[dict[str, Any]] = []
    purelib_raw = observed.get("purelib")
    purelib = Path(purelib_raw).absolute() if isinstance(purelib_raw, str) and purelib_raw else None
    for installed_rel, expected_row in expected.items():
        row = installed.get(installed_rel)
        if not isinstance(row, dict):
            mismatches.append({"file": installed_rel, "reason": "INSTALLED_FILE_MISSING"})
            continue
        origin_raw = row.get("origin")
        origin = Path(origin_raw).absolute() if isinstance(origin_raw, str) and origin_raw else None
        if origin is None or (purelib is not None and not _inside(origin, purelib)):
            mismatches.append({
                "file": installed_rel,
                "reason": "INSTALLED_ORIGIN_NOT_SITE_PACKAGES",
                "origin": origin_raw,
                "purelib": purelib_raw,
            })
        if row.get("sha256") != expected_row["sha256"]:
            mismatches.append({
                "file": installed_rel,
                "reason": "INSTALLED_SOURCE_SHA256_MISMATCH",
                "expected": expected_row["sha256"],
                "observed": row.get("sha256"),
            })
    declared_norm = _path_text(declared)
    observed_norm = _path_text(Path(str(observed.get("interpreter", "")))) if observed.get("interpreter") else ""
    if observed_norm != declared_norm:
        mismatches.append({
            "file": "interpreter",
            "reason": "DECLARED_INTERPRETER_IDENTITY_MISMATCH",
            "expected": declared_norm,
            "observed": observed.get("interpreter"),
        })
    expected_version = None
    try:
        text = (root / "light_runtime" / "pyproject.toml").read_text(encoding="utf-8")
        match = _SCHEMA_VERSION_RE.search(text)
        expected_version = match.group(1) if match else None
    except OSError:
        pass
    if expected_version is not None and observed.get("constraintbox_version") not in {
        expected_version,
        # The installed distribution may retain a dev suffix while the
        # checkout metadata has been normalized.  Hash equality remains the
        # authority for source currentness.
        expected_version.replace(".dev1", ""),
    }:
        mismatches.append({
            "file": "constraintbox distribution",
            "reason": "INSTALLED_VERSION_MISMATCH",
            "expected": expected_version,
            "observed": observed.get("constraintbox_version"),
        })

    expected_source_digest = sha256_bytes(
        canonical_json_bytes({key: row["sha256"] for key, row in sorted(expected.items())})
    )
    observed_hashes = {
        key: row.get("sha256")
        for key, row in sorted(installed.items())
        if isinstance(row, dict)
    }
    return {
        "status": "MATCH" if not mismatches else "HOLD",
        "reason_code": "LIGHT_INSTALLED_SOURCE_MATCH" if not mismatches else "HOLD_MINILEV_SOURCE_MISMATCH",
        "light_root": _path_text(root),
        "expected_root": _path_text(expected_root),
        "interpreter": {
            "declared": declared_norm,
            "observed": observed.get("interpreter"),
            "python_version": observed.get("python_version"),
        },
        "expected": expected,
        "installed": installed,
        "installed_hashes": observed_hashes,
        "expected_source_sha256": expected_source_digest,
        "installed_source_sha256": sha256_bytes(canonical_json_bytes(observed_hashes)),
        "constraintbox_version": observed.get("constraintbox_version"),
        "mismatches": mismatches,
        "claim_ceiling": CLAIM_CEILING,
    }


def _canonical_request(request: bytes | bytearray | Mapping[str, Any]) -> tuple[dict[str, Any], bytes]:
    if isinstance(request, (bytes, bytearray)):
        try:
            value = strict_json_loads(bytes(request), label="Mini-Lev request")
        except Exception as exc:
            raise MiniLevAdapterError("REFUSE_MINILEV_REQUEST_JSON_INVALID", str(exc)) from exc
    elif isinstance(request, Mapping):
        value = copy.deepcopy(dict(request))
    else:
        raise MiniLevAdapterError(
            "REFUSE_MINILEV_REQUEST_MAPPING_REQUIRED",
            "request must be a JSON object or UTF-8 JSON bytes",
        )
    if not isinstance(value, dict):
        raise MiniLevAdapterError("REFUSE_MINILEV_REQUEST_MAPPING_REQUIRED")
    try:
        return value, canonical_json_bytes(value)
    except Exception as exc:
        raise MiniLevAdapterError("REFUSE_MINILEV_REQUEST_NOT_CANONICAL", str(exc)) from exc


def _sqlite_uri(path: Path) -> str:
    return f"file:{_path_text(path)}?mode=ro"


def _jsonable_sqlite(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, bytes):
        return {"__bytes_hex__": value.hex()}
    return {"__type__": f"{type(value).__module__}.{type(value).__qualname__}", "text": str(value)}


def _state_snapshot(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise MiniLevAdapterError("HOLD_MINILEV_STATE_UNAVAILABLE", f"state does not exist: {_path_text(path)}")
    try:
        connection = sqlite3.connect(_sqlite_uri(path), uri=True, timeout=10.0)
    except (OSError, sqlite3.Error) as exc:
        raise MiniLevAdapterError("HOLD_MINILEV_STATE_UNAVAILABLE", str(exc)) from exc
    try:
        connection.row_factory = sqlite3.Row
        tables = connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        if len(tables) > _MAX_STATE_TABLES:
            raise MiniLevAdapterError("HOLD_MINILEV_STATE_TOO_LARGE", "too many SQLite tables")
        material_tables: list[dict[str, Any]] = []
        row_count = 0
        for table in tables:
            name = str(table["name"])
            quoted = '"' + name.replace('"', '""') + '"'
            columns = [str(row["name"]) for row in connection.execute(f"PRAGMA table_info({quoted})")]
            try:
                rows = connection.execute(f"SELECT rowid, * FROM {quoted} ORDER BY rowid").fetchall()
            except sqlite3.Error:
                rows = connection.execute(f"SELECT * FROM {quoted}").fetchall()
            if row_count + len(rows) > _MAX_STATE_ROWS:
                raise MiniLevAdapterError("HOLD_MINILEV_STATE_TOO_LARGE", "too many SQLite rows")
            normalized_rows: list[list[Any]] = []
            for row in rows:
                values = list(row)
                # A timestamp is useful for the Light state itself but would
                # make a replay receipt non-deterministic.  It is deliberately
                # redacted only in this probe's state fingerprint.
                # ``rowid`` is used only to make ordinary-table ordering
                # deterministic.  It is not part of the material: SQLite may
                # legitimately assign a new rowid when a no-op INSERT OR
                # REPLACE re-materializes a state_meta row.
                if len(values) == len(columns) + 1:
                    values = values[1:]
                normalized: list[Any] = []
                for index, value in enumerate(values):
                    column = columns[index] if index < len(columns) else ""
                    if column in _VOLATILE_COLUMNS:
                        normalized.append("<volatile>")
                    else:
                        normalized.append(_jsonable_sqlite(value))
                normalized_rows.append(normalized)
            normalized_rows.sort(key=canonical_json_bytes)
            row_count += len(normalized_rows)
            material_tables.append({
                "name": name,
                "sql": table["sql"],
                "columns": columns,
                "rows": normalized_rows,
            })
    except MiniLevAdapterError:
        raise
    except (OSError, sqlite3.Error) as exc:
        raise MiniLevAdapterError("HOLD_MINILEV_STATE_UNAVAILABLE", str(exc)) from exc
    finally:
        connection.close()
    material = {"tables": material_tables}
    return {
        "logical_sha256": sha256_bytes(canonical_json_bytes(material)),
        "table_count": len(material_tables),
        "row_count": row_count,
        "table_names": [row["name"] for row in material_tables],
    }


def _backup_state(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_connection: sqlite3.Connection | None = None
    destination_connection: sqlite3.Connection | None = None
    try:
        source_connection = sqlite3.connect(_sqlite_uri(source), uri=True, timeout=10.0)
        destination_connection = sqlite3.connect(destination, timeout=10.0)
        source_connection.backup(destination_connection)
        destination_connection.commit()
    except (OSError, sqlite3.Error) as exc:
        raise MiniLevAdapterError("HOLD_MINILEV_STATE_COPY_FAILED", str(exc)) from exc
    finally:
        if source_connection is not None:
            source_connection.close()
        if destination_connection is not None:
            destination_connection.close()


def _child_script() -> str:
    return r'''
import json
import sys
from pathlib import Path

request_path = Path(sys.argv[1])
db_path = Path(sys.argv[2])
role = sys.argv[3] if len(sys.argv) > 3 else ""
raw = json.loads(request_path.read_text(encoding="utf-8"))

import constraintbox.mini_lev_bridge as bridge

def _role_error(message):
    raise RuntimeError(message)

injected_symbols = []
if role == "pydantic_jsonschema_typed_boundary":
    # Sever both members of the actual typed boundary.  JSON Schema runs first
    # in the Light bridge, so the Pydantic patch is retained as explicit
    # evidence even though this input stops at the first boundary.
    def schema_removed(self, value):
        from jsonschema import ValidationError
        raise ValidationError("role severed: JSON Schema")
    bridge.Draft202012Validator.validate = schema_removed
    injected_symbols.append("Draft202012Validator.validate")
    try:
        def pydantic_removed(cls, value, *args, **kwargs):
            return _role_error("role severed: Pydantic")
        bridge._MiniLevRequest.model_validate = classmethod(pydantic_removed)
        injected_symbols.append("_MiniLevRequest.model_validate")
    except BaseException:
        pass
elif role == "rustworkx_topology":
    import rustworkx
    class RemovedGraph:
        def __init__(self, *args, **kwargs):
            _role_error("role severed: Rustworkx PyDiGraph")
    rustworkx.PyDiGraph = RemovedGraph
    injected_symbols.append("rustworkx.PyDiGraph")
elif role == "sympy_witness":
    import sympy
    def removed_degree(self, *args, **kwargs):
        return _role_error("role severed: SymPy degree witness")
    sympy.Poly.degree = removed_degree
    injected_symbols.append("sympy.Poly.degree")
elif role == "cvc5_degree_crosscheck":
    import cvc5
    class RemovedSolver:
        def __init__(self, *args, **kwargs):
            _role_error("role severed: CVC5 solver")
    cvc5.Solver = RemovedSolver
    injected_symbols.append("cvc5.Solver")
elif role == "z3_independent_crosscheck":
    import z3
    class RemovedSolver:
        def __init__(self, *args, **kwargs):
            _role_error("role severed: Z3 solver")
    z3.Solver = RemovedSolver
    injected_symbols.append("z3.Solver")

try:
    value = bridge.run_mini_lev_bridge(raw, db_path=db_path)
except BaseException as exc:
    value = {
        "disposition": "REFUSE" if role else "HOLD",
        "reason_code": (
            "REFUSE_MINILEV_ROLE_" + role.upper() + "_SEVERED"
            if role else "HOLD_MINILEV_CHILD_EXCEPTION"
        ),
        "detail": f"{type(exc).__name__}: {exc}",
        "role": role or None,
    }
if isinstance(value, dict) and role:
    value = {
        **value,
        "role": role,
        "injected_symbols": injected_symbols,
        "role_severed": True,
    }
print(json.dumps(value, sort_keys=True, separators=(",", ":")))
'''


def _run_child(
    request: Mapping[str, Any],
    db_path: Path,
    interpreter: Path,
    *,
    role: str = "",
) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
        request_path = Path(handle.name)
        handle.write(canonical_json_bytes(dict(request)).decode("utf-8"))
    try:
        try:
            completed = subprocess.run(
                [str(interpreter), "-I", "-c", _child_script(), str(request_path), str(db_path), role],
                cwd=str(db_path.parent),
                capture_output=True,
                check=False,
                text=True,
                timeout=_CHILD_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return {
                "disposition": "HOLD",
                "reason_code": "HOLD_MINILEV_CHILD_UNAVAILABLE",
                "detail": str(exc),
            }
        if completed.returncode != 0:
            return {
                "disposition": "HOLD",
                "reason_code": "HOLD_MINILEV_CHILD_FAILED",
                "detail": completed.stderr.strip()[-2000:] or "Light child failed",
                "returncode": completed.returncode,
            }
        try:
            value = strict_json_loads(completed.stdout.encode("utf-8"), label="Mini-Lev child result")
        except Exception as exc:
            return {
                "disposition": "HOLD",
                "reason_code": "HOLD_MINILEV_CHILD_OUTPUT_INVALID",
                "detail": str(exc),
            }
        if not isinstance(value, dict):
            return {
                "disposition": "HOLD",
                "reason_code": "HOLD_MINILEV_CHILD_OUTPUT_SHAPE",
            }
        return value
    finally:
        try:
            request_path.unlink()
        except OSError:
            pass


def _outer_disposition(light_result: Mapping[str, Any]) -> str:
    disposition = light_result.get("disposition")
    if disposition == LIGHT_SUCCESS:
        return "SUCCEEDED"
    if disposition in {"REFUSE", "HOLD"}:
        return str(disposition)
    return "HOLD"


def _event(
    *,
    scenario: str,
    sequence: int,
    request: Mapping[str, Any],
    light_result: Mapping[str, Any],
    state_before: Mapping[str, Any],
    state_after: Mapping[str, Any],
    source_status: Mapping[str, Any],
    interpreter: Path,
    role: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    outer = _outer_disposition(light_result)
    no_write = bool(
        outer != "SUCCEEDED"
        and state_before.get("logical_sha256") == state_after.get("logical_sha256")
    )
    body: dict[str, Any] = {
        "kind": "minilev_operation",
        "scenario": scenario,
        "sequence": sequence,
        "role": role,
        "request_sha256": sha256_bytes(canonical_json_bytes(dict(request))),
        "disposition": outer,
        "reason_code": light_result.get("reason_code", "HOLD_MINILEV_NO_REASON"),
        "light_disposition": light_result.get("disposition"),
        "light_result": dict(light_result),
        "result_sha256": sha256_bytes(canonical_json_bytes(dict(light_result))),
        "source_status": source_status.get("status"),
        "interpreter": {
            "declared": _path_text(interpreter),
            "path": source_status.get("interpreter", {}).get("observed"),
            "python_version": source_status.get("interpreter", {}).get("python_version"),
        },
        "state_before": dict(state_before),
        "state_after": dict(state_after),
        "no_write_on_refusal": no_write,
        "state_copy_only": True,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    if extra:
        body.update(copy.deepcopy(dict(extra)))
    body["event_id"] = sha256_bytes(canonical_json_bytes(body))
    return body


def _state_source(
    state_path: Path | str,
    temp_root: Path,
) -> tuple[Path, dict[str, Any]]:
    source = Path(state_path).expanduser().absolute()
    before = _state_snapshot(source)
    destination = temp_root / "state.sqlite"
    _backup_state(source, destination)
    return destination, before


def _result_wrapper(
    *,
    request: Mapping[str, Any],
    request_bytes: bytes,
    source_status: Mapping[str, Any],
    interpreter: Path,
    event: Mapping[str, Any],
    state_before: Mapping[str, Any],
    state_after: Mapping[str, Any],
    source_state_before: Mapping[str, Any] | None = None,
    source_state_after: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    receipt = {
        "schema": SCHEMA,
        "request_sha256": sha256_bytes(request_bytes),
        "source": dict(source_status),
        "interpreter": dict(event.get("interpreter", {})),
        "state_before": dict(state_before),
        "state_after": dict(state_after),
        "no_write_on_refusal": bool(event.get("no_write_on_refusal")),
        "state_copy_only": True,
        "source_state_before": dict(source_state_before or state_before),
        "source_state_after": dict(source_state_after or source_state_before or state_before),
        "source_state_unchanged": bool(
            (source_state_before or state_before).get("logical_sha256")
            == (source_state_after or source_state_before or state_before).get("logical_sha256")
        ),
        "event_id": event.get("event_id"),
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    light_result = event.get("light_result")
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "disposition": event.get("disposition", "HOLD"),
        "reason_code": event.get("reason_code"),
        "result": light_result,
        "receipt": receipt,
        "state_before": dict(state_before),
        "state_after": dict(state_after),
        "no_write_on_refusal": receipt["no_write_on_refusal"],
        "source": dict(source_status),
        "interpreter": receipt["interpreter"],
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    return result


def run_minilev_operation(
    request: bytes | bytearray | Mapping[str, Any],
    state_path: Path | str | None = None,
    *,
    state_bytes: bytes | bytearray | None = None,
    light_root: Path | str | None = None,
    interpreter: Path | str | None = None,
) -> dict[str, Any]:
    """Run one canonical request against a temporary copy of Light state."""

    declared, source_status = _source_gate(light_root, interpreter)
    if source_status.get("status") != "MATCH":
        return _source_hold(
            schema=SCHEMA,
            source_status=source_status,
            interpreter=declared,
        )
    if state_bytes is not None:
        with tempfile.TemporaryDirectory(prefix="cb-zip-minilev-input-") as temporary:
            source = Path(temporary) / "input-state.sqlite"
            source.write_bytes(bytes(state_bytes))
            return run_minilev_operation(
                request,
                source,
                light_root=light_root,
                interpreter=interpreter,
            )
    if state_path is None:
        return {
            "schema": SCHEMA,
            "disposition": "HOLD",
            "reason_code": "HOLD_MINILEV_STATE_UNAVAILABLE",
            "detail": "state_path or state_bytes is required",
            "state_copy_only": True,
            "no_write_on_refusal": True,
            "promotion_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }

    try:
        request_value, request_bytes = _canonical_request(request)
    except MiniLevAdapterError as exc:
        return {
            "schema": SCHEMA,
            "disposition": "REFUSE" if exc.reason_code.startswith("REFUSE_") else "HOLD",
            "reason_code": exc.reason_code,
            "detail": exc.detail,
            "request_sha256": None,
            "source": source_status,
            "interpreter": {"declared": _path_text(declared)},
            "state_copy_only": True,
            "no_write_on_refusal": True,
            "promotion_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }
    try:
        original_before = _state_snapshot(Path(state_path).expanduser().absolute())
    except MiniLevAdapterError as exc:
        return {
            "schema": SCHEMA,
            "disposition": "HOLD",
            "reason_code": exc.reason_code,
            "detail": exc.detail,
            "request_sha256": sha256_bytes(request_bytes),
            "source": source_status,
            "state_copy_only": True,
            "no_write_on_refusal": True,
            "promotion_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }
    with tempfile.TemporaryDirectory(prefix="cb-zip-minilev-") as temporary:
        temporary_root = Path(temporary)
        try:
            copied, copied_before = _state_source(state_path, temporary_root)
            light_result = _run_child(request_value, copied, declared)
            copied_after = _state_snapshot(copied)
        except MiniLevAdapterError as exc:
            return {
                "schema": SCHEMA,
                "disposition": "HOLD",
                "reason_code": exc.reason_code,
                "detail": exc.detail,
                "request_sha256": sha256_bytes(request_bytes),
                "source": source_status,
                "state_before": original_before,
                "state_after": original_before,
                "no_write_on_refusal": True,
                "state_copy_only": True,
                "promotion_allowed": False,
                "claim_ceiling": CLAIM_CEILING,
            }
        event = _event(
            scenario="positive",
            sequence=0,
            request=request_value,
            light_result=light_result,
            state_before=copied_before,
            state_after=copied_after,
            source_status=source_status,
            interpreter=declared,
        )
        source_after = _state_snapshot(Path(state_path).expanduser().absolute())
        return _result_wrapper(
            request=request_value,
            request_bytes=request_bytes,
            source_status=source_status,
            interpreter=declared,
            event=event,
            state_before=copied_before,
            state_after=copied_after,
            source_state_before=original_before,
            source_state_after=source_after,
        )


def verify_minilev_result(result: Mapping[str, Any]) -> dict[str, Any]:
    """Verify the narrow shape consumed by the AB composition step.

    This is intentionally a receipt-shape verifier, not a second semantic
    evaluator.  It consumes the actual Mini-Lev result produced by the first
    step and has no SQLite write path.
    """

    if not isinstance(result, Mapping):
        return {"disposition": "REFUSE", "reason_code": "REFUSE_MINILEV_VERIFY_RESULT_SHAPE"}
    if result.get("disposition") != LIGHT_SUCCESS:
        return {"disposition": "REFUSE", "reason_code": "REFUSE_MINILEV_VERIFY_RESULT_NOT_SUCCESS"}
    required = ("symbolic", "topology", "cohort", "attempt_id", "result_sha256")
    if any(key not in result for key in required):
        return {"disposition": "REFUSE", "reason_code": "REFUSE_MINILEV_VERIFY_RESULT_FIELDS"}
    symbolic = result.get("symbolic")
    topology = result.get("topology")
    if not isinstance(symbolic, Mapping) or symbolic.get("smt_status") != "sat" or symbolic.get("z3_status") != "sat":
        return {"disposition": "REFUSE", "reason_code": "REFUSE_MINILEV_VERIFY_SYMBOLIC_WITNESS"}
    if not isinstance(topology, Mapping) or topology.get("edge_count") != 3:
        return {"disposition": "REFUSE", "reason_code": "REFUSE_MINILEV_VERIFY_TOPOLOGY"}
    return {
        "disposition": "VERIFIED",
        "reason_code": "MINILEV_RESULT_SHAPE_VERIFIED",
        "input_sha256": sha256_bytes(canonical_json_bytes(dict(result))),
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def _with_suffix(request: Mapping[str, Any], suffix: str) -> dict[str, Any]:
    value = copy.deepcopy(dict(request))
    base = value.get("bridge_request_id", "minilev")
    value["bridge_request_id"] = f"{base}:{suffix}"
    return value


def _mutated_request(request: Mapping[str, Any]) -> dict[str, Any]:
    value = _with_suffix(request, "mutation")
    payload = value.get("payload")
    if isinstance(payload, dict) and isinstance(payload.get("claimed_degree"), int):
        payload["claimed_degree"] = (int(payload["claimed_degree"]) + 1) % 17
    return value


def _boundary_request(request: Mapping[str, Any]) -> dict[str, Any]:
    value = _with_suffix(request, "boundary")
    payload = value.get("payload")
    if isinstance(payload, dict):
        payload["terms"] = [{"coefficient": {"numerator": 1, "denominator": 1}, "exponent": 0}]
        payload["claimed_degree"] = 0
    return value


def _run_case(
    request: Mapping[str, Any],
    source_path: Path,
    source_before: Mapping[str, Any],
    source_status: Mapping[str, Any],
    interpreter: Path,
    temporary_root: Path,
    *,
    scenario: str,
    sequence: int,
    role: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    copied = temporary_root / f"{sequence:02d}-{scenario}.sqlite"
    _backup_state(source_path, copied)
    copied_before = _state_snapshot(copied)
    value = _run_child(request, copied, interpreter, role=role or "")
    copied_after = _state_snapshot(copied)
    return _event(
        scenario=scenario,
        sequence=sequence,
        request=request,
        light_result=value,
        state_before=copied_before,
        state_after=copied_after,
        source_status=source_status,
        interpreter=interpreter,
        role=role,
        extra=extra,
    )


def run_minilev_probe_cohort(
    request: bytes | bytearray | Mapping[str, Any],
    state_path: Path | str | None = None,
    *,
    state_bytes: bytes | bytearray | None = None,
    light_root: Path | str | None = None,
    interpreter: Path | str | None = None,
) -> dict[str, Any]:
    """Run positive/replay/mutation/boundary, role, and AB/BA observations."""

    declared, source_status = _source_gate(light_root, interpreter)
    if source_status.get("status") != "MATCH":
        return {
            **_source_hold(
                schema=COHORT_SCHEMA,
                source_status=source_status,
                interpreter=declared,
            ),
            "events": [],
            "ranking": [],
        }
    if state_bytes is not None:
        with tempfile.TemporaryDirectory(prefix="cb-zip-minilev-input-cohort-") as temporary:
            source = Path(temporary) / "input-state.sqlite"
            source.write_bytes(bytes(state_bytes))
            return run_minilev_probe_cohort(
                request,
                source,
                light_root=light_root,
                interpreter=interpreter,
            )
    if state_path is None:
        return {
            "schema": COHORT_SCHEMA,
            "disposition": "HOLD",
            "reason_code": "HOLD_MINILEV_STATE_UNAVAILABLE",
            "detail": "state_path or state_bytes is required",
            "events": [],
            "ranking": [],
            "promotion_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }

    try:
        request_value, request_bytes = _canonical_request(request)
    except MiniLevAdapterError as exc:
        return {
            "schema": COHORT_SCHEMA,
            "disposition": "REFUSE" if exc.reason_code.startswith("REFUSE_") else "HOLD",
            "reason_code": exc.reason_code,
            "source": source_status,
            "interpreter": {"declared": _path_text(declared)},
            "events": [],
            "ranking": [],
            "promotion_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }
    source_path = Path(state_path).expanduser().absolute()
    try:
        source_before = _state_snapshot(source_path)
    except MiniLevAdapterError as exc:
        return {
            "schema": COHORT_SCHEMA,
            "disposition": "HOLD",
            "reason_code": exc.reason_code,
            "request_sha256": sha256_bytes(request_bytes),
            "source": source_status,
            "events": [],
            "ranking": [],
            "promotion_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }
    events: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="cb-zip-minilev-cohort-") as temporary:
        temporary_root = Path(temporary)
        # Baseline and replay share one temporary state copy.  The second call
        # therefore exercises the Light bridge's real idempotency row rather
        # than two independent fresh calls.
        replay_db = temporary_root / "00-replay.sqlite"
        _backup_state(source_path, replay_db)
        replay_before = _state_snapshot(replay_db)
        positive_result = _run_child(request_value, replay_db, declared)
        positive_after = _state_snapshot(replay_db)
        events.append(_event(
            scenario="positive",
            sequence=0,
            request=request_value,
            light_result=positive_result,
            state_before=replay_before,
            state_after=positive_after,
            source_status=source_status,
            interpreter=declared,
        ))
        replay_result = _run_child(request_value, replay_db, declared)
        replay_after = _state_snapshot(replay_db)
        events.append(_event(
            scenario="replay",
            sequence=1,
            request=request_value,
            light_result=replay_result,
            state_before=positive_after,
            state_after=replay_after,
            source_status=source_status,
            interpreter=declared,
            extra={
                "replay_stable": positive_result.get("attempt_id") == replay_result.get("attempt_id")
                and positive_result.get("result_sha256") == replay_result.get("result_sha256"),
            },
        ))
        events.append(_run_case(
            _mutated_request(request_value), source_path, source_before, source_status, declared,
            temporary_root, scenario="mutation", sequence=2,
        ))
        events.append(_run_case(
            _boundary_request(request_value), source_path, source_before, source_status, declared,
            temporary_root, scenario="boundary", sequence=3,
        ))
        for offset, role in enumerate(ROLE_IDS, start=4):
            events.append(_run_case(
                _with_suffix(request_value, f"ablation-{role}"), source_path, source_before,
                source_status, declared, temporary_root, scenario="role_ablation", sequence=offset,
                role=role,
                extra={"severed_symbols": list(_ROLE_SYMBOLS[role])},
            ))

        # AB is a true data-dependent composition: Mini-Lev must first produce
        # the result consumed by verify_minilev_result.  BA passes the raw
        # request to that verifier and short-circuits before Mini-Lev, so it is
        # not a pair of independent calls mislabeled as interaction.
        ab_db = temporary_root / "09-ab.sqlite"
        _backup_state(source_path, ab_db)
        ab_before = _state_snapshot(ab_db)
        ab_mini = _run_child(_with_suffix(request_value, "order-ab"), ab_db, declared)
        ab_after_mini = _state_snapshot(ab_db)
        ab_verify = verify_minilev_result(ab_mini)
        ab_after_verify = _state_snapshot(ab_db)
        ab_disposition = (
            "SUCCEEDED"
            if _outer_disposition(ab_mini) == "SUCCEEDED"
            and ab_verify.get("disposition") == "VERIFIED"
            else "REFUSE"
        )
        ab_body = {
            "kind": "minilev_composition",
            "scenario": "order",
            "order": "AB",
            "steps": [
                {"operation": "mini_lev", "disposition": _outer_disposition(ab_mini), "result_sha256": sha256_bytes(canonical_json_bytes(ab_mini))},
                {"operation": "verify_minilev_result", "disposition": ab_verify.get("disposition"), "input_sha256": ab_verify.get("input_sha256")},
            ],
            "disposition": ab_disposition,
            "reason_code": "MINILEV_THEN_VERIFY_COMPOSED" if ab_verify.get("disposition") == "VERIFIED" else "REFUSE_MINILEV_ORDER_AB_FIRST_STEP",
            "state_before": ab_before,
            "state_after": ab_after_verify,
            "intermediate_state_after_mini_lev": ab_after_mini,
            "no_write_on_refusal": ab_disposition != "SUCCEEDED"
            and ab_before.get("logical_sha256") == ab_after_verify.get("logical_sha256"),
            "state_copy_only": True,
            "promotion_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }
        ab_body["event_id"] = sha256_bytes(canonical_json_bytes(ab_body))
        events.append(ab_body)

        ba_db = temporary_root / "10-ba.sqlite"
        _backup_state(source_path, ba_db)
        ba_before = _state_snapshot(ba_db)
        ba_verify = verify_minilev_result(request_value)
        ba_after = _state_snapshot(ba_db)
        ba_body = {
            "kind": "minilev_composition",
            "scenario": "order",
            "order": "BA",
            "steps": [
                {"operation": "verify_minilev_result", "disposition": ba_verify.get("disposition"), "reason_code": ba_verify.get("reason_code")},
                {"operation": "mini_lev", "disposition": "NOT_CALLED", "short_circuited": True},
            ],
            "disposition": "REFUSE",
            "reason_code": "REFUSE_MINILEV_ORDER_VERIFY_BEFORE_RESULT",
            "state_before": ba_before,
            "state_after": ba_after,
            "no_write_on_refusal": ba_before.get("logical_sha256") == ba_after.get("logical_sha256"),
            "state_copy_only": True,
            "short_circuited": True,
            "promotion_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }
        ba_body["event_id"] = sha256_bytes(canonical_json_bytes(ba_body))
        events.append(ba_body)

    baseline = events[0]
    replay = events[1]
    baseline_settled = (
        baseline.get("disposition") == "SUCCEEDED"
        and replay.get("disposition") == "SUCCEEDED"
        and bool(replay.get("replay_stable"))
        and bool(baseline.get("no_write_on_refusal") is False)
    )
    role_rows: list[dict[str, Any]] = []
    for role, event in zip(ROLE_IDS, events[4:9]):
        ablation_settled = event.get("disposition") == "SUCCEEDED"
        settlement_delta = float(baseline_settled) - float(ablation_settled)
        write_zero = bool(event.get("no_write_on_refusal"))
        score = round(max(0.0, settlement_delta) + (1.0 if write_zero else 0.0), 12)
        role_rows.append({
            "role": role,
            "severed_symbols": list(_ROLE_SYMBOLS[role]),
            "baseline_settled": baseline_settled,
            "ablation_disposition": event.get("disposition"),
            "ablation_reason_code": event.get("reason_code"),
            "ablation_settled": ablation_settled,
            "settlement_delta": settlement_delta,
            "no_write_on_refusal": write_zero,
            "ablation_score": score,
            "claim_ceiling": CLAIM_CEILING,
        })
    role_rows.sort(key=lambda row: (-float(row["ablation_score"]), row["role"]))
    for rank, row in enumerate(role_rows, start=1):
        row["rank"] = rank
    ab = next(row for row in events if row.get("kind") == "minilev_composition" and row.get("order") == "AB")
    ba = next(row for row in events if row.get("kind") == "minilev_composition" and row.get("order") == "BA")
    order_summary = {
        "ab_disposition": ab.get("disposition"),
        "ba_disposition": ba.get("disposition"),
        "order_sensitive": ab.get("disposition") != ba.get("disposition"),
        "ab_ba_interaction_observed": bool(ab.get("steps")) and bool(ba.get("short_circuited")),
        "claim_ceiling": CLAIM_CEILING,
    }
    events.sort(key=lambda row: int(row.get("sequence", 1000)))
    return {
        "schema": COHORT_SCHEMA,
        "disposition": "SUCCEEDED" if baseline_settled else "REFUSE",
        "reason_code": "MINILEV_PROBE_COHORT_SETTLED" if baseline_settled else "REFUSE_MINILEV_PROBE_COHORT_NOT_SETTLED",
        "request_sha256": sha256_bytes(request_bytes),
        "source": source_status,
        "state_source_before": source_before,
        "state_source_after": _state_snapshot(source_path),
        "events": events,
        "roles": role_rows,
        "ranking": [row["role"] for row in role_rows],
        "order": order_summary,
        "promotion_allowed": False,
        "admission_allowed": False,
        "core_update": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def run_minilev_operation_bytes(
    request: bytes | bytearray | Mapping[str, Any],
    state_path: Path | str,
    *,
    light_root: Path | str | None = None,
    interpreter: Path | str | None = None,
) -> bytes:
    """Return one canonical JSON receipt for ZIP byte-oriented callers."""

    return canonical_json_bytes(
        run_minilev_operation(
            request,
            state_path,
            light_root=light_root,
            interpreter=interpreter,
        )
    )


def run_minilev_probe_cohort_bytes(
    request: bytes | bytearray | Mapping[str, Any],
    state_path: Path | str,
    *,
    light_root: Path | str | None = None,
    interpreter: Path | str | None = None,
) -> bytes:
    return canonical_json_bytes(
        run_minilev_probe_cohort(
            request,
            state_path,
            light_root=light_root,
            interpreter=interpreter,
        )
    )


def run_minilev_operation_from_state_bytes(
    request: bytes | bytearray | Mapping[str, Any],
    state_bytes: bytes | bytearray,
    *,
    light_root: Path | str | None = None,
    interpreter: Path | str | None = None,
) -> dict[str, Any]:
    """Run the adapter when a ZIP workspace supplies SQLite as member bytes."""

    with tempfile.TemporaryDirectory(prefix="cb-zip-minilev-input-") as temporary:
        source = Path(temporary) / "input-state.sqlite"
        source.write_bytes(bytes(state_bytes))
        return run_minilev_operation(
            request,
            source,
            light_root=light_root,
            interpreter=interpreter,
        )


def run_minilev_probe_cohort_from_state_bytes(
    request: bytes | bytearray | Mapping[str, Any],
    state_bytes: bytes | bytearray,
    *,
    light_root: Path | str | None = None,
    interpreter: Path | str | None = None,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="cb-zip-minilev-input-cohort-") as temporary:
        source = Path(temporary) / "input-state.sqlite"
        source.write_bytes(bytes(state_bytes))
        return run_minilev_probe_cohort(
            request,
            source,
            light_root=light_root,
            interpreter=interpreter,
        )


def run_minilev_zip_operation(
    task: TaskSpec,
    workspace: dict[str, bytes],
    *,
    cohort: bool,
) -> dict[str, bytes]:
    """Execute the contained operation from exact ZIP member bytes."""

    if len(task.input_paths) != 2 or len(task.output_paths) != 1:
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
    request_path, state_path = task.input_paths
    output_path = task.output_paths[0]
    runner = (
        run_minilev_probe_cohort_from_state_bytes
        if cohort
        else run_minilev_operation_from_state_bytes
    )
    result = runner(workspace[request_path], workspace[state_path])
    return {output_path: canonical_json_bytes(result)}


def build_minilev_zip_packet(
    *,
    request: bytes,
    state_bytes: bytes,
    cohort: bool = True,
    job_id: str = "cb-minilev-operation-probe",
) -> bytes:
    """Build one self-contained packet for the real contained-Light route."""

    operation = MINILEV_PROBE_OPERATION_ID if cohort else MINILEV_OPERATION_ID
    output_path = "output/minilev_probe.json" if cohort else "output/minilev_result.json"
    task_path = "tasks/00_minilev.task.json"
    task = {
        "schema": "constraintbox.zip_task.v1",
        "task_id": "minilev-probe" if cohort else "minilev-operation",
        "sequence": 0,
        "operation": operation,
        "input_paths": ["inputs/request.json", "inputs/state.sqlite"],
        "output_paths": [output_path],
        "depends_on": [],
        "preload_files": [],
        "parameters": {},
    }
    return build_packet(
        {
            "schema": "constraintbox.zip_job.v1",
            "job_id": job_id,
            "task_execution_order": [task_path],
            "required_output_file_list": [output_path],
            "allowed_operations": [operation],
            "allowed_child_job_ids": [],
            "max_child_depth": 0,
            "claim_ceiling": CLAIM_CEILING,
        },
        {
            "00_RUN_ME_FIRST.md": (
                b"# Contained-Light Mini-Lev operation\n\n"
                b"CB executes the declared request against a temporary copy of the "
                b"declared SQLite member. The caller state member is never modified.\n"
            ),
            "inputs/request.json": bytes(request),
            "inputs/state.sqlite": bytes(state_bytes),
            task_path: canonical_json_bytes(task),
        },
    )


__all__ = [
    "CLAIM_CEILING",
    "COHORT_SCHEMA",
    "LIGHT_ROOT_ENV",
    "LIGHT_SOURCE_FILES",
    "ROLE_IDS",
    "SCHEMA",
    "inspect_light_source_status",
    "run_minilev_operation",
    "run_minilev_operation_bytes",
    "run_minilev_operation_from_state_bytes",
    "run_minilev_probe_cohort",
    "run_minilev_probe_cohort_bytes",
    "run_minilev_probe_cohort_from_state_bytes",
    "verify_minilev_result",
]
