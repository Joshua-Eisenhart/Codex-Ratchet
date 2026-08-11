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


# This is deliberately an optional-profile gate, not a CB Light base-tool
# admission.  The base environment must remain usable without these packages;
# only the typed local control-plane/wave commands require these exact pins.
_CONTROL_PLANE_EXACT_PINS = {
    "pydantic": "2.12.5",
    "jsonschema": "4.26.0",
}


def _current_cb_light_evaluation_for_wave() -> tuple[bool, str, dict[str, object]]:
    """Require the real contained Light gate before a fixture wave can start.

    This is deliberately a subprocess through the public contained broker
    status route rather than a copy of its receipt logic.  That route checks
    current sources/receipts and re-runs the fresh-wheel plus actual-runtime
    boundary audit in a verifier-owned temporary location.
    """

    from hookkernel.cb_light_runtime import MANDATED_INTERPRETER, ROOT

    status_script = ROOT / "scripts" / "cb_light_cli.py"
    binding: dict[str, object] = {
        "mode": "contained_cb_light_status_live_boundary",
        "interpreter": str(MANDATED_INTERPRETER),
        "status_script": str(status_script),
    }
    if not MANDATED_INTERPRETER.is_file() or not status_script.is_file():
        return False, "CB_LIGHT_EVALUATION_GATE_UNAVAILABLE", binding
    try:
        completed = subprocess.run(
            [str(MANDATED_INTERPRETER), "-I", str(status_script), "status"],
            cwd=ROOT.parent,
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
    return (
        bool(allowed),
        (
            "CB_LIGHT_EVALUATION_GATE_CURRENT"
            if allowed
            else f"CB_LIGHT_EVALUATION_GATE_HOLD:{binding['evaluation_reason_code']}"
        ),
        binding,
    )


def _current_control_plane_dependencies_for_wave() -> tuple[bool, str, dict[str, object]]:
    """Require the exact typed-profile dependencies before opening a wave DB.

    The base CB Light gate intentionally does not include Pydantic or
    JSONSchema.  A wave is an optional typed control-plane operation, however,
    so its public CLI must verify the installed interpreter imports the two
    exact declared pins at the moment the operation starts.  This is a live
    operational check, not an assertion that either package belongs to the
    91-root CB Light candidate domain.
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
    wave = commands.add_parser(
        "wave",
        help="run the bounded local three-probe CB Light fixture wave",
    )
    wave.add_argument("--request", type=Path, required=True)
    wave.add_argument("--db", type=Path)
    wave.add_argument("--output", type=Path)
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

    body = doctor() if args.command == "doctor" else exercise()
    if args.as_json:
        print(json.dumps(body, indent=2, sort_keys=True))
    elif args.command == "doctor":
        print("ConstraintBox Light core tools")
        for row in body["rows"]:
            state = "visible" if row["import_visible"] else "missing"
            print(f"- {row['id']}: {state} ({row['version'] or 'no distribution version'})")
    else:
        print(f"ConstraintBox Light exercised {len(body['observations'])} core tools")
        print(f"observation_sha256={body['observation_sha256']}")


if __name__ == "__main__":
    main()
