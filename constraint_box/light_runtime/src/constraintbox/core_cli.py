"""Public CLI for the separately packaged CB Light runtime."""

from __future__ import annotations

import argparse
import hashlib
import importlib
from importlib import metadata
import json
import subprocess
import sys
from pathlib import Path

from .core_tools import doctor, exercise


# These pins bind the typed local control-plane operations. They are also in
# the earned working-set core when installed/exercised with CB consumer path.
_CONTROL_PLANE_EXACT_PINS = {
    "pydantic": "2.12.5",
    "jsonschema": "4.26.0",
}

_PREMORTEM_RESULT_SCHEMA = "constraintbox.premortem-remediation-result.v1"
_PREMORTEM_CLI_CLAIM_CEILING = (
    "CB Light premortem CLI entry boundary only; it does not execute a skill, "
    "model, MMM, formal agent, repair action, browser, UI, or CB Heavy work."
)

# Entry-gate modes for wave/premortem:
#   local_core_probe (default) — fast earned-core probe matrix (runnable spine)
#   broker_status — full contained cb_light_cli status (slow live boundary)
#   cached — reuse fingerprint-bound cache written after a green gate
_ENTRY_GATE_CACHE_NAME = "cb_light_entry_gate_cache.json"
_ENTRY_GATE_MAX_AGE_S = 3600

# These are checkout-owned bindings read directly by the public contained
# broker/status route.  Executable Python sources are intentionally *not*
# listed here: they are discovered from their loaded module paths below.
_ENTRY_GATE_ROOT_BINDINGS = (
    "config/core_tool_registry_v9.json",
    "scripts/cb_light_cli.py",
)
_ENTRY_GATE_CONSTRAINTBOX_SOURCE_NAMES = (
    "core_cli.py",
    "core_tools.py",
    "cb_light_probes.py",
    "control_plane.py",
    "mini_lev_bridge.py",
    "transition_mini_lev.py",
    "verify_operation.py",
    "premortem_contracts.py",
    "premortem_remediation.py",
    "wave_adapters.py",
    "wave_contracts.py",
    "wave_controller.py",
)
_ENTRY_GATE_HOOKKERNEL_SOURCE_NAMES = (
    "cb_light_runtime.py",
    "cb_light_domain.py",
    "cb_light_state.py",
    "cb_light_minilev_state.py",
    "cb_light_wave_state.py",
)


def _entry_gate_mode() -> str:
    import os

    mode = (os.environ.get("CB_LIGHT_ENTRY_GATE_MODE") or "local_core_probe").strip()
    if mode not in {"local_core_probe", "broker_status", "cached"}:
        return "local_core_probe"
    return mode


def _entry_gate_loaded_source_paths() -> tuple[tuple[str, Path], ...]:
    """Return executable sibling paths without importing optional wave modules."""

    # ``cb_light_runtime`` is the one hookkernel import already required by the
    # public entry gate to discover ``ROOT``.  Every other file is only a path
    # sibling: importing it here would turn a missing optional dependency into
    # an exception before the typed dependency gate can return HOLD.
    from hookkernel import cb_light_runtime

    constraintbox_dir = Path(__file__).resolve().parent
    hookkernel_dir = Path(cb_light_runtime.__file__).resolve().parent
    return tuple(
        (f"constraintbox/{name}", constraintbox_dir / name)
        for name in _ENTRY_GATE_CONSTRAINTBOX_SOURCE_NAMES
    ) + tuple(
        (f"hookkernel/{name}", hookkernel_dir / name)
        for name in _ENTRY_GATE_HOOKKERNEL_SOURCE_NAMES
    )


def _entry_gate_fingerprint(root: Path) -> str:
    """Hash loaded Light code plus checkout bindings used directly at runtime.

    ``root/src/constraintbox`` and ``root/light_runtime/src`` are deliberately
    absent from the code half of this fingerprint.  They are checkout copies,
    not proof of which bytes the installed public route imported.
    """

    h = hashlib.sha256()
    for label, path in _entry_gate_loaded_source_paths():
        h.update(label.encode("utf-8"))
        h.update(b"\0")
        if path.is_file():
            h.update(path.read_bytes())
        h.update(b"\n")
    for rel in _ENTRY_GATE_ROOT_BINDINGS:
        path = root / rel
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        if path.is_file():
            h.update(path.read_bytes())
        h.update(b"\n")
    return h.hexdigest()


def _read_entry_gate_cache(
    root: Path, fingerprint: str
) -> tuple[bool, str, dict[str, object]] | None:
    import time

    path = root / "receipts" / _ENTRY_GATE_CACHE_NAME
    if not path.is_file():
        return None
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(body, dict):
        return None
    if body.get("fingerprint") != fingerprint:
        return None
    if body.get("evaluation_allowed") is not True:
        return None
    captured = body.get("captured_at_unix")
    if not isinstance(captured, (int, float)):
        return None
    age = time.time() - float(captured)
    if age < 0 or age > _ENTRY_GATE_MAX_AGE_S:
        return None
    binding = {
        "mode": "entry_gate_cache",
        "cache_path": str(path),
        "fingerprint": fingerprint,
        "age_s": round(age, 3),
        "source_reason": body.get("reason_code"),
        "source_mode": body.get("source_mode"),
    }
    return True, "CB_LIGHT_EVALUATION_GATE_CURRENT_CACHED", binding


def _write_entry_gate_cache(
    root: Path,
    *,
    fingerprint: str,
    allowed: bool,
    reason_code: str,
    source_mode: str,
) -> None:
    import time

    if not allowed:
        return
    path = root / "receipts" / _ENTRY_GATE_CACHE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "schema": "constraintbox.cb-light-entry-gate-cache.v1",
        "fingerprint": fingerprint,
        "evaluation_allowed": True,
        "reason_code": reason_code,
        "source_mode": source_mode,
        "captured_at_unix": time.time(),
        "max_age_s": _ENTRY_GATE_MAX_AGE_S,
        "promotion_allowed": False,
        "claim_ceiling": (
            "fingerprint-bound local entry-gate cache only; not completion/adoption"
        ),
    }
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _evaluation_via_local_core_probe(
    root: Path, fingerprint: str
) -> tuple[bool, str, dict[str, object]]:
    """Fast runnable-spine gate: earned-core probe matrix must be fully satisfied."""

    binding: dict[str, object] = {
        "mode": "local_core_probe_matrix",
        "fingerprint": fingerprint,
        "interpreter": sys.executable,
    }
    try:
        from .cb_light_probes import run_core_probe_matrix

        matrix = run_core_probe_matrix()
    except Exception as exc:  # noqa: BLE001 — gate must fail closed
        binding["error"] = type(exc).__name__
        return False, f"CB_LIGHT_LOCAL_CORE_PROBE_ERROR:{type(exc).__name__}", binding
    binding["all_contracts_satisfied"] = bool(matrix.get("all_contracts_satisfied"))
    binding["contract_set_sha256"] = matrix.get("contract_set_sha256")
    binding["evidence_set_sha256"] = matrix.get("evidence_set_sha256")
    binding["claim_ceiling"] = matrix.get("claim_ceiling")
    allowed = matrix.get("all_contracts_satisfied") is True
    reason = (
        "CB_LIGHT_LOCAL_CORE_PROBE_CURRENT"
        if allowed
        else "CB_LIGHT_LOCAL_CORE_PROBE_INCOMPLETE"
    )
    if allowed:
        _write_entry_gate_cache(
            root,
            fingerprint=fingerprint,
            allowed=True,
            reason_code=reason,
            source_mode="local_core_probe",
        )
    return allowed, reason, binding


def _evaluation_via_broker_status(
    root: Path, fingerprint: str
) -> tuple[bool, str, dict[str, object]]:
    from hookkernel.cb_light_runtime import MANDATED_INTERPRETER

    status_script = root / "scripts" / "cb_light_cli.py"
    binding: dict[str, object] = {
        "mode": "contained_cb_light_status_live_boundary",
        "interpreter": str(MANDATED_INTERPRETER),
        "status_script": str(status_script),
        "fingerprint": fingerprint,
    }
    if not MANDATED_INTERPRETER.is_file() or not status_script.is_file():
        return False, "CB_LIGHT_EVALUATION_GATE_UNAVAILABLE", binding
    try:
        completed = subprocess.run(
            [str(MANDATED_INTERPRETER), "-I", str(status_script), "status"],
            cwd=root.parent,
            capture_output=True,
            text=True,
            check=False,
            timeout=360,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"CB_LIGHT_EVALUATION_GATE_ERROR:{type(exc).__name__}", binding
    binding.update(
        {
            "returncode": completed.returncode,
            "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
        }
    )
    try:
        status = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return False, "CB_LIGHT_EVALUATION_GATE_OUTPUT_INVALID", binding
    if not isinstance(status, dict):
        return False, "CB_LIGHT_EVALUATION_GATE_OUTPUT_INVALID", binding
    binding["evaluation_reason_code"] = str(status.get("reason_code", ""))
    allowed = completed.returncode == 0 and status.get("evaluation_allowed") is True
    reason = (
        "CB_LIGHT_EVALUATION_GATE_CURRENT"
        if allowed
        else f"CB_LIGHT_EVALUATION_GATE_HOLD:{binding['evaluation_reason_code']}"
    )
    if allowed:
        _write_entry_gate_cache(
            root,
            fingerprint=fingerprint,
            allowed=True,
            reason_code=reason,
            source_mode="broker_status",
        )
    return bool(allowed), reason, binding


def _current_cb_light_evaluation_for_wave() -> tuple[bool, str, dict[str, object]]:
    """Gate wave/premortem on a current CB Light evaluation surface.

    Default is the fast local earned-core probe matrix (runnable spine map).
    Set CB_LIGHT_ENTRY_GATE_MODE=broker_status for the slow contained status
    boundary, or =cached to require a fingerprint-bound cache hit only.
    """

    from hookkernel.cb_light_basin_view import hold_result_if_incomplete
    from hookkernel.cb_light_runtime import ROOT

    held = hold_result_if_incomplete()
    if held is not None:
        return (
            False,
            "HOLD_BASIN_FIELD_INCOMPLETE",
            {
                "mode": "current_basin_view",
                "evaluation_reason_code": held["reason_code"],
                "basin_view": held["basin_view"],
            },
        )

    fingerprint = _entry_gate_fingerprint(ROOT)
    mode = _entry_gate_mode()

    cached = _read_entry_gate_cache(ROOT, fingerprint)
    if mode == "cached":
        if cached is not None:
            return cached
        return (
            False,
            "CB_LIGHT_ENTRY_GATE_CACHE_MISS",
            {
                "mode": "entry_gate_cache",
                "fingerprint": fingerprint,
                "cache_path": str(ROOT / "receipts" / _ENTRY_GATE_CACHE_NAME),
            },
        )
    if cached is not None and mode in {"local_core_probe", "broker_status"}:
        # Reuse only when caller did not force a fresh broker re-run.
        if mode == "local_core_probe":
            return cached

    if mode == "broker_status":
        return _evaluation_via_broker_status(ROOT, fingerprint)
    return _evaluation_via_local_core_probe(ROOT, fingerprint)


def _current_control_plane_dependencies_for_wave() -> tuple[bool, str, dict[str, object]]:
    """Require exact typed-operation dependencies before opening a wave DB.

    A typed control-plane operation verifies that its current interpreter can
    import the two exact pins at the moment it starts.  That is operation
    evidence, not a permanent admission or authority claim for either tool.
    """

    binding: dict[str, object] = {
        "mode": "exact_control_plane_dependency_versions",
        # Preserve the invoked venv path.  Resolving this symlink would make a
        # profile receipt misleadingly name the shared base Python executable.
        "interpreter": str(Path(sys.executable)),
        "expected_versions": dict(_CONTROL_PLANE_EXACT_PINS),
        "installed": {},
    }
    installed: dict[str, object] = {}
    missing: list[str] = []
    import_errors: dict[str, str] = {}
    for distribution, expected_version in _CONTROL_PLANE_EXACT_PINS.items():
        try:
            module = importlib.import_module(distribution)
            observed_version = metadata.version(distribution)
        except metadata.PackageNotFoundError:
            missing.append(distribution)
            continue
        except ModuleNotFoundError as exc:
            missing.append(exc.name or distribution)
            continue
        except Exception as exc:
            import_errors[distribution] = type(exc).__name__
            continue
        installed[distribution] = {
            "expected_version": expected_version,
            "observed_version": observed_version,
            "module_file": str(getattr(module, "__file__", "")),
        }
    binding["installed"] = installed
    if missing:
        binding["missing"] = sorted(set(missing))
        return False, "HOLD_WAVE_CONTRACT_DEPENDENCY_MISSING", binding
    if import_errors:
        binding["import_errors"] = import_errors
        return False, "HOLD_WAVE_CONTRACT_DEPENDENCY_IMPORT_ERROR", binding
    mismatches = {
        distribution: details
        for distribution, details in installed.items()
        if details["observed_version"] != details["expected_version"]
    }
    if mismatches:
        binding["version_mismatches"] = mismatches
        return False, "HOLD_WAVE_CONTRACT_DEPENDENCY_VERSION_MISMATCH", binding
    return True, "CONTROL_PLANE_DEPENDENCIES_CURRENT", binding


def _premortem_cli_result(
    terminal: str,
    reason_code: str,
    detail: str,
    *,
    entry_gate: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return the typed no-controller result for a CLI boundary refusal/hold."""

    outcomes = {
        "VERIFIED_DONE": "SETTLED",
        "HOLD": "HOLD",
        "REFUSE": "REFUSE",
        "EXHAUSTED": "EXPIRED",
        "PROPOSED_FOR_OWNER": "HOLD",
    }
    return {
        "schema": _PREMORTEM_RESULT_SCHEMA,
        "terminal": terminal,
        "state_outcome": outcomes[terminal],
        "reason_code": reason_code,
        "detail": detail,
        "claim_ceiling": _PREMORTEM_CLI_CLAIM_CEILING,
        "issue_scope": "no_remediation_request_processed",
        "attempt_id": None,
        "attempt": None,
        "selection_sha256": None,
        "gate_sha256s": [],
        "continuation": None,
        "external_action_execution": "not_claimed",
        "state_verification": {},
        "entry_gate": None if entry_gate is None else dict(entry_gate),
    }


def _reject_duplicate_object_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Make the request parser reject ambiguous duplicate-key JSON objects."""

    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    """Reject non-standard JSON constants such as NaN and Infinity."""

    raise ValueError(f"non-standard JSON constant: {value}")


def _read_strict_premortem_request(path: Path) -> tuple[dict[str, object] | None, str | None]:
    """Read a JSON object without starting the remediation controller or SQLite."""

    try:
        raw_text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None, "REFUSE_PREMORTEM_REQUEST_UNREADABLE"
    try:
        raw = json.loads(
            raw_text,
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
        )
    except (json.JSONDecodeError, ValueError):
        return None, "REFUSE_PREMORTEM_REQUEST_INVALID_JSON"
    if not isinstance(raw, dict):
        return None, "REFUSE_PREMORTEM_REQUEST_NOT_OBJECT"
    return raw, None


def _run_premortem_remediation(
    request: dict[str, object], *, db_path: Path | None
) -> dict[str, object]:
    """Lazily load the Light-only controller after the request boundary passes."""

    from .premortem_remediation import run_remediation

    return run_remediation(request, db_path=db_path)


def _render_structured_json(body: dict[str, object], output: Path | None) -> None:
    """Emit the same structured JSON to the requested receipt path and stdout."""

    rendered = json.dumps(body, sort_keys=True, indent=2) + "\n"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="constraintbox")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("doctor", "exercise"):
        command = commands.add_parser(name)
        command.add_argument("--json", action="store_true", dest="as_json")
    control_plane = commands.add_parser(
        "control-plane",
        help="run a bounded typed CB Light candidate-evaluation consumer",
    )
    control_plane.add_argument("--request", type=Path, required=True)
    control_plane.add_argument("--db", type=Path)
    control_plane.add_argument("--output", type=Path)
    mini_lev = commands.add_parser(
        "mini-lev",
        help="run one bounded receipt-bound CB Light Mini-Lev operation",
    )
    mini_lev.add_argument("--request", type=Path, required=True)
    mini_lev.add_argument("--db", type=Path)
    mini_lev.add_argument("--output", type=Path)
    transition_mini_lev = commands.add_parser(
        "mini-lev-transition",
        help="run one fixed finite-state receipt-bound CB Light Mini-Lev operation",
    )
    transition_mini_lev.add_argument("--request", type=Path, required=True)
    transition_mini_lev.add_argument("--db", type=Path)
    transition_mini_lev.add_argument("--output", type=Path)
    verify_operation = commands.add_parser(
        "verify-operation",
        help=(
            "read-only bind one supplied candidate-evaluation output to its "
            "existing CB Light SQLite row"
        ),
    )
    verify_operation.add_argument("--receipt", type=Path, required=True)
    verify_operation.add_argument("--db", type=Path)
    selector = verify_operation.add_mutually_exclusive_group(required=True)
    selector.add_argument("--operation-id")
    selector.add_argument("--request-id")
    wave = commands.add_parser(
        "wave",
        help="run the bounded local three-probe CB Light fixture wave",
    )
    wave.add_argument("--request", type=Path, required=True)
    wave.add_argument("--db", type=Path)
    wave.add_argument("--output", type=Path)
    premortem = commands.add_parser(
        "premortem",
        help="run one receipt-bound CB Light premortem remediation round",
    )
    premortem.add_argument("--request", type=Path, required=True)
    premortem.add_argument("--db", type=Path)
    premortem.add_argument("--output", type=Path)
    cb_light = commands.add_parser(
        "cb-light",
        help="run the contained CB Light deterministic gate front door",
    )
    cb_light.add_argument("gate_args", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> None:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    if raw_args and raw_args[0] == "cb-light":
        from hookkernel.cb_light_gate import main as cb_light_main

        raise SystemExit(cb_light_main(raw_args[1:]))

    args = build_parser().parse_args(raw_args)
    if args.command == "control-plane":
        from .control_plane import run_candidate_evaluation_file
        from hookkernel.cb_light_state import default_db_path

        body = run_candidate_evaluation_file(
            args.request,
            db_path=args.db or default_db_path(),
        )
        rendered = json.dumps(body, sort_keys=True, indent=2) + "\n"
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        if body["disposition"] != "CANDIDATE_EVALUATED_LOCAL":
            raise SystemExit(2)
        return

    if args.command == "mini-lev":
        from .mini_lev_bridge import SUCCESS, run_mini_lev_bridge_file
        from hookkernel.cb_light_state import default_db_path

        body = run_mini_lev_bridge_file(
            args.request,
            db_path=args.db or default_db_path(),
        )
        rendered = json.dumps(body, sort_keys=True, indent=2) + "\n"
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        if body["disposition"] != SUCCESS:
            raise SystemExit(2)
        return

    if args.command == "mini-lev-transition":
        from .transition_mini_lev import (
            SUCCESS,
            TransitionMiniLevError,
            _attest_executing_source_custody,
            _result,
            run_transition_mini_lev_file,
        )

        # This preflight is deliberately ahead of both request parsing and the
        # SQLite default-path import.  The transition operation's own custody
        # attestation binds the executing module and checkout logical sources
        # to the generated Light manifest; it is not a cached wave/status
        # decision and it does not repeat the parent-operation checks below.
        try:
            _attest_executing_source_custody()
        except TransitionMiniLevError as exc:
            body = _result("HOLD", exc.reason_code, detail=exc.detail)
            _render_structured_json(body, args.output)
            raise SystemExit(2)

        from hookkernel.cb_light_state import default_db_path

        body = run_transition_mini_lev_file(
            args.request,
            db_path=args.db or default_db_path(),
        )
        rendered = json.dumps(body, sort_keys=True, indent=2) + "\n"
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        if body["disposition"] != SUCCESS:
            raise SystemExit(2)
        return

    if args.command == "verify-operation":
        from .verify_operation import SUCCESS, verify_operation_file
        from hookkernel.cb_light_state import default_db_path

        body = verify_operation_file(
            args.receipt,
            db_path=args.db or default_db_path(),
            operation_id=args.operation_id,
            request_id=args.request_id,
        )
        print(json.dumps(body, sort_keys=True, indent=2))
        if body["verification_status"] != SUCCESS:
            raise SystemExit(2)
        return

    if args.command == "wave":
        from .wave_controller import _result, run_fixture_wave_file
        from hookkernel.cb_light_state import default_db_path

        evaluation_allowed, evaluation_reason, evaluation_binding = (
            _current_cb_light_evaluation_for_wave()
        )
        if not evaluation_allowed:
            body = _result(
                "HOLD",
                "HOLD_WAVE_REQUIRES_CURRENT_CB_LIGHT_EVALUATION",
                evaluation_reason,
                persisted=False,
                entry_gate=evaluation_binding,
            )
        else:
            dependencies_allowed, dependencies_reason, dependencies_binding = (
                _current_control_plane_dependencies_for_wave()
            )
            entry_gate = dict(evaluation_binding)
            entry_gate["control_plane_dependencies"] = dependencies_binding
            if not dependencies_allowed:
                body = _result(
                    "HOLD",
                    dependencies_reason,
                    dependencies_reason,
                    persisted=False,
                    entry_gate=entry_gate,
                )
            else:
                body = run_fixture_wave_file(
                    args.request,
                    db_path=args.db or default_db_path(),
                )
                body["entry_gate"] = entry_gate
        rendered = json.dumps(body, sort_keys=True, indent=2) + "\n"
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        # A local counterexample is valuable fixture evidence, but it must not
        # look like shell-level admission.  Only a non-refuted local fixture
        # settlement returns zero; HOLD, REFUSE, and SETTLED_REFUTED return 2.
        if body["disposition"] != "SETTLED":
            raise SystemExit(2)
        return

    if args.command == "premortem":
        evaluation_allowed, evaluation_reason, evaluation_binding = (
            _current_cb_light_evaluation_for_wave()
        )
        if not evaluation_allowed:
            body = _premortem_cli_result(
                "HOLD",
                "HOLD_PREMORTEM_REQUIRES_CURRENT_CB_LIGHT_EVALUATION",
                evaluation_reason,
                entry_gate=evaluation_binding,
            )
        else:
            request, request_reason = _read_strict_premortem_request(args.request)
            if request is None:
                body = _premortem_cli_result(
                    "REFUSE",
                    request_reason or "REFUSE_PREMORTEM_REQUEST_INVALID_JSON",
                    "The premortem request was refused before controller or SQLite access.",
                    entry_gate=evaluation_binding,
                )
            else:
                body = dict(
                    _run_premortem_remediation(request, db_path=args.db)
                )
                body["entry_gate"] = dict(evaluation_binding)
        _render_structured_json(body, args.output)
        if body["terminal"] != "VERIFIED_DONE":
            raise SystemExit(2)
        return

    body = doctor() if args.command == "doctor" else exercise()
    if args.as_json:
        print(json.dumps(body, indent=2, sort_keys=True))
    elif args.command == "doctor":
        print("ConstraintBox Light declared tool contracts")
        for row in body["rows"]:
            state = "visible" if row["import_visible"] else "missing"
            print(f"- {row['id']}: {state} ({row['version'] or 'no distribution version'})")
    else:
        print(
            f"ConstraintBox Light exercised {len(body['observations'])} declared tool contracts"
        )
        print(f"observation_sha256={body['observation_sha256']}")


if __name__ == "__main__":
    main()
