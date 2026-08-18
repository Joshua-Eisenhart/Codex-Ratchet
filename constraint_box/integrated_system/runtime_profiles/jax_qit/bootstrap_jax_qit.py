#!/usr/bin/env python3
"""Install and attest the project-neutral JAX/QIT profile.

The profile is intentionally an external runtime.  This module has no imports
from ConstraintBox and never copies a virtual environment into the product.
It only stages the two requirement files and probe source, installs the exact
lock into a caller-selected target, runs the probe with that target's Python,
and writes a bounded manifest plus receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


SCHEMA = "constraintbox.jax-qit-bootstrap.v1"
PROFILE = "jax_qit"
PROFILE_DIR = Path(__file__).resolve().parent
DIRECT_REQUIREMENTS = PROFILE_DIR / "requirements.in"
LOCK_REQUIREMENTS = PROFILE_DIR / "requirements.lock"
PROBE_SOURCE = PROFILE_DIR / "probe_runtime.py"
TEMPLATE_MANIFEST = PROFILE_DIR / "STACK_MANIFEST.template.json"
STATE_FILE = ".cb-jax-qit-profile.json"
TARGET_NAME = "jax-qit-stack"
PASS = 0
HOLD = 2
REFUSE = 3
_PIN_LINE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9_.-]*)==([^\s#]+)\s*$")


class BootstrapError(RuntimeError):
    """A deterministic bootstrap refusal or failed install."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(json_bytes(value))
    temporary.replace(path)


def resolve_target(
    target: str | Path | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Resolve a target without binding the profile to a project checkout."""

    env = os.environ if environ is None else environ
    if target is not None:
        return Path(target).expanduser().resolve()
    configured = env.get("CB_JAX_QIT_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    data_home = env.get("XDG_DATA_HOME")
    base = Path(data_home).expanduser() if data_home else (home or Path.home()) / ".local" / "share"
    return (base / TARGET_NAME).resolve()


def virtualenv_python(target: Path) -> Path:
    if os.name == "nt":
        return target / "Scripts" / "python.exe"
    return target / "bin" / "python"


def normalize_distribution_name(name: str) -> str:
    """Apply the PEP 503 normalization used for distribution identity."""

    return re.sub(r"[-_.]+", "-", name).lower()


def locked_distributions(lock_path: Path = LOCK_REQUIREMENTS) -> dict[str, str]:
    """Read every exact ``name==version`` line from the committed lock."""

    pins: dict[str, str] = {}
    for line in lock_path.read_text(encoding="utf-8").splitlines():
        match = _PIN_LINE.match(line)
        if not match:
            continue
        name = normalize_distribution_name(match.group(1))
        version = match.group(2)
        previous = pins.get(name)
        if previous is not None and previous != version:
            raise BootstrapError(f"REFUSE_LOCK_DUPLICATE_PIN:{name}")
        pins[name] = version
    if not pins:
        raise BootstrapError("REFUSE_LOCK_HAS_NO_EXACT_PINS")
    return pins


def _target_is_external(target: Path) -> None:
    target = target.expanduser().resolve()
    try:
        target.relative_to(PROFILE_DIR.resolve())
    except ValueError:
        return
    raise BootstrapError("REFUSE_TARGET_INSIDE_PRODUCT_PROFILE")


def _require_profile_inputs(profile_root: Path) -> None:
    missing = [str(path.name) for path in (DIRECT_REQUIREMENTS, LOCK_REQUIREMENTS, PROBE_SOURCE) if not path.is_file()]
    if missing:
        raise BootstrapError("REFUSE_PROFILE_INPUT_MISSING:" + ",".join(missing))
    if profile_root.resolve() != PROFILE_DIR.resolve():
        raise BootstrapError("REFUSE_PROFILE_ROOT_MISMATCH")


def _relative_profile_path(path: Path) -> str:
    return path.name


def build_plan(
    *,
    target: Path,
    python_executable: str | Path,
    installer: str,
    uv_executable: str | Path | None = None,
) -> dict[str, Any]:
    """Return the exact plan; this function performs no filesystem writes."""

    _require_profile_inputs(PROFILE_DIR)
    target = target.expanduser().resolve()
    _target_is_external(target)
    if installer not in {"auto", "uv", "pip"}:
        raise BootstrapError(f"REFUSE_UNKNOWN_INSTALLER:{installer}")
    selected_installer = choose_installer(installer, uv_executable)
    chosen_uv = str(uv_executable or shutil.which("uv") or "uv")
    python = str(Path(python_executable).expanduser())
    return {
        "schema": SCHEMA,
        "profile": PROFILE,
        "operation": "install",
        "target": str(target),
        "target_python": str(virtualenv_python(target)),
        "build_python": python,
        "requested_installer": installer,
        "installer": selected_installer,
        "uv_executable": chosen_uv if selected_installer == "uv" else None,
        "inputs": {
            "requirements": _relative_profile_path(DIRECT_REQUIREMENTS),
            "requirements_sha256": sha256_file(DIRECT_REQUIREMENTS),
            "lock": _relative_profile_path(LOCK_REQUIREMENTS),
            "lock_sha256": sha256_file(LOCK_REQUIREMENTS),
            "probe": _relative_profile_path(PROBE_SOURCE),
            "probe_sha256": sha256_file(PROBE_SOURCE),
        },
        "writes": [
            "requirements.in",
            "requirements.lock",
            "probe_runtime.py",
            STATE_FILE,
            "PROBE_RECEIPT.json",
            "STACK_MANIFEST.json",
        ],
        "claim_ceiling": "local generic capability runtime only; not a physical manifold, quantum advantage, production environment, or package portability claim",
    }


def choose_installer(requested: str, uv_executable: str | Path | None = None) -> str:
    if requested == "pip":
        return "pip"
    if requested == "uv":
        if uv_executable is None and shutil.which("uv") is None:
            raise BootstrapError("HOLD_UV_MISSING")
        return "uv"
    return "uv" if (uv_executable or shutil.which("uv")) else "pip"


def install_commands(
    *,
    target: Path,
    python_executable: str | Path,
    installer: str,
    uv_executable: str | Path | None = None,
) -> list[list[str]]:
    """Build install commands without executing them."""

    selected = choose_installer(installer, uv_executable)
    target_python = virtualenv_python(target)
    if selected == "uv":
        uv = str(uv_executable or shutil.which("uv") or "uv")
        commands: list[list[str]] = []
        if not target_python.is_file():
            commands.append([uv, "venv", "--python", str(python_executable), str(target)])
        commands.append([uv, "pip", "sync", "--python", str(target_python), str(LOCK_REQUIREMENTS)])
        return commands
    commands = []
    if not target_python.is_file():
        commands.append([str(python_executable), "-m", "venv", str(target)])
    commands.append(
        [
            str(target_python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--requirement",
            str(LOCK_REQUIREMENTS),
        ]
    )
    return commands


def _target_is_safe(target: Path) -> None:
    if not target.exists():
        return
    if not target.is_dir():
        raise BootstrapError("REFUSE_TARGET_NOT_DIRECTORY")
    state = target / STATE_FILE
    if not state.is_file():
        try:
            next(target.iterdir())
        except StopIteration:
            return
        raise BootstrapError("REFUSE_TARGET_NOT_OWNED")


def _run_commands(commands: Sequence[Sequence[str]], runner: Callable[..., Any] | None = None) -> None:
    run = runner or subprocess.run
    for argv in commands:
        completed = run(argv, check=False, capture_output=True, text=True)
        if int(getattr(completed, "returncode", 1)) != 0:
            stderr = str(getattr(completed, "stderr", ""))[-1200:]
            raise BootstrapError(f"FAIL_INSTALL_COMMAND:{' '.join(map(str, argv))}:{stderr}")


def _copy_profile_sources(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for source in (DIRECT_REQUIREMENTS, LOCK_REQUIREMENTS, PROBE_SOURCE):
        shutil.copy2(source, target / source.name)


def _probe_source_for(target: Path) -> Path:
    candidate = target / PROBE_SOURCE.name
    return candidate if candidate.is_file() else PROBE_SOURCE


def verify_locked_distributions(target: Path, *, timeout: float = 60.0) -> dict[str, Any]:
    """Check the target's installed distribution metadata against every pin.

    This reads ``importlib.metadata`` through the target interpreter and does
    not invoke pip, uv, or any package installer.  Extra distributions are
    reported but are not rejected; every locked distribution must be present
    at its exact normalized version.
    """

    target_python = virtualenv_python(target)
    if not target_python.is_file():
        return {"status": "HOLD", "reason_code": "HOLD_TARGET_PYTHON_MISSING", "target": str(target)}
    inventory_script = (
        "import importlib.metadata as m, json, re; "
        "normalize=lambda n: re.sub(r'[-_.]+', '-', n).lower(); "
        "rows={}; "
        "[(rows.__setitem__(normalize(d.metadata.get('Name')), d.version)) "
        "for d in m.distributions() if d.metadata.get('Name')]; "
        "print(json.dumps(rows, sort_keys=True))"
    )
    try:
        completed = subprocess.run(
            [str(target_python), "-I", "-c", inventory_script],
            cwd=target,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "HOLD", "reason_code": "HOLD_METADATA_INSPECTION", "detail": f"{type(exc).__name__}:{exc}"}
    if completed.returncode != 0:
        return {
            "status": "HOLD",
            "reason_code": "HOLD_METADATA_INSPECTION",
            "returncode": completed.returncode,
            "stderr_tail": completed.stderr[-1200:],
        }
    try:
        observed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"status": "HOLD", "reason_code": "HOLD_METADATA_OUTPUT_INVALID", "stdout_tail": completed.stdout[-1200:]}
    if not isinstance(observed, dict):
        return {"status": "HOLD", "reason_code": "HOLD_METADATA_OUTPUT_INVALID"}
    expected = locked_distributions()
    missing = sorted(name for name in expected if name not in observed)
    mismatched = {
        name: {"expected": expected[name], "observed": observed.get(name)}
        for name in expected
        if name in observed and str(observed[name]) != expected[name]
    }
    if missing or mismatched:
        return {
            "status": "REFUSE",
            "reason_code": "REFUSE_LOCK_MISMATCH",
            "expected_count": len(expected),
            "observed_count": len(observed),
            "missing": missing,
            "mismatched": mismatched,
        }
    return {
        "status": "PASS",
        "expected_count": len(expected),
        "observed_count": len(observed),
        "lock_sha256": sha256_file(LOCK_REQUIREMENTS),
    }


def _owned_state(target: Path) -> bool:
    state_path = target / STATE_FILE
    if not state_path.is_file():
        return False
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(state, dict) and state.get("schema") == "constraintbox.jax-qit-profile-state.v1" and state.get("profile") == PROFILE


def _source_integrity(target: Path) -> dict[str, Any]:
    """Validate any already-copied profile source before using it."""

    for source in (DIRECT_REQUIREMENTS, LOCK_REQUIREMENTS, PROBE_SOURCE):
        candidate = target / source.name
        if candidate.exists() and sha256_file(candidate) != sha256_file(source):
            return {"status": "REFUSE", "reason_code": "REFUSE_PROFILE_SOURCE_MISMATCH", "file": source.name}
    return {"status": "PASS"}


def run_probe(target: Path, *, timeout: float = 300.0, probe_source: Path | None = None) -> dict[str, Any]:
    target_python = virtualenv_python(target)
    if not target_python.is_file():
        return {"status": "HOLD", "reason_code": "HOLD_TARGET_PYTHON_MISSING", "target": str(target)}
    source = probe_source or _probe_source_for(target)
    completed = subprocess.run(
        [str(target_python), "-I", str(source)],
        cwd=target,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        env={"PYTHONDONTWRITEBYTECODE": "1"},
    )
    try:
        probe = json.loads(completed.stdout)
    except json.JSONDecodeError:
        probe = {"stdout_tail": completed.stdout[-2000:]}
    if not isinstance(probe, dict):
        probe = {"raw": probe}
    status = "PASS" if completed.returncode == 0 and probe.get("failed", 1) == 0 else "FAIL"
    return {
        "status": status,
        "returncode": completed.returncode,
        "target": str(target),
        "probe": probe,
        "stderr_tail": completed.stderr[-2000:],
    }


def write_attestation(target: Path, probe_run: Mapping[str, Any]) -> dict[str, Any]:
    probe = probe_run.get("probe")
    probe_obj = dict(probe) if isinstance(probe, Mapping) else {}
    receipt: dict[str, Any] = {
        "schema": "constraintbox.jax-qit-profile-receipt.v1",
        "profile": PROFILE,
        "status": probe_run.get("status"),
        "runtime_root": str(target),
        "requirements_sha256": sha256_file(target / DIRECT_REQUIREMENTS.name),
        "lock_sha256": sha256_file(target / LOCK_REQUIREMENTS.name),
        "probe_source_sha256": sha256_file(target / PROBE_SOURCE.name),
        "returncode": probe_run.get("returncode"),
        "probe": probe_obj,
        "claim_ceiling": "local generic capability runtime only; not a physical manifold, quantum advantage, production environment, or package portability claim",
        "promotion_allowed": False,
    }
    receipt_path = target / "PROBE_RECEIPT.json"
    write_json(receipt_path, receipt)
    manifest = {
        "schema": "constraintbox.jax-qit-stack-manifest.v1",
        "profile": PROFILE,
        "status": "VERIFIED_LOCAL" if probe_run.get("status") == "PASS" else str(probe_run.get("status")),
        "purpose": "project-neutral JAX, QIT, finite-manifold, solver, tensor-network, spinor-Lie, and topology capability runtime",
        "runtime_root": str(target),
        "requirements": {
            "direct": DIRECT_REQUIREMENTS.name,
            "lock": LOCK_REQUIREMENTS.name,
            "direct_sha256": receipt["requirements_sha256"],
            "lock_sha256": receipt["lock_sha256"],
        },
        "probe": {
            "source": PROBE_SOURCE.name,
            "source_sha256": receipt["probe_source_sha256"],
            "receipt": receipt_path.name,
            "receipt_sha256": sha256_file(receipt_path),
            "passed": probe_obj.get("passed"),
            "failed": probe_obj.get("failed"),
        },
        "boundaries": {
            "project_source_installed": False,
            "cb_light_runtime": False,
            "julia_included": False,
            "pytorch_included": False,
            "model_or_provider_code_included": False,
            "numpy_is_transitive_numeric_substrate": True,
            "numpy_is_not_manifold_authority": True,
        },
        "claim_ceiling": receipt["claim_ceiling"],
        "promotion_allowed": False,
    }
    write_json(target / "STACK_MANIFEST.json", manifest)
    return manifest


def install_profile(
    *,
    target: Path,
    python_executable: str | Path,
    installer: str,
    uv_executable: str | Path | None = None,
    runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    _require_profile_inputs(PROFILE_DIR)
    _target_is_external(target)
    _target_is_safe(target)
    target.mkdir(parents=True, exist_ok=True)
    write_json(
        target / STATE_FILE,
        {
            "schema": "constraintbox.jax-qit-profile-state.v1",
            "profile": PROFILE,
            "status": "INSTALLING",
            "lock_sha256": sha256_file(LOCK_REQUIREMENTS),
        },
    )
    selected = choose_installer(installer, uv_executable)
    _run_commands(
        install_commands(
            target=target,
            python_executable=python_executable,
            installer=selected,
            uv_executable=uv_executable,
        ),
        runner=runner,
    )
    lock_result = verify_locked_distributions(target)
    if lock_result.get("status") != "PASS":
        write_json(
            target / STATE_FILE,
            {
                "schema": "constraintbox.jax-qit-profile-state.v1",
                "profile": PROFILE,
                "status": "LOCK_FAILED",
                "lock_sha256": sha256_file(LOCK_REQUIREMENTS),
            },
        )
        return lock_result
    _copy_profile_sources(target)
    result = run_probe(target)
    if result.get("status") != "PASS":
        write_json(
            target / STATE_FILE,
            {"schema": "constraintbox.jax-qit-profile-state.v1", "profile": PROFILE, "status": "PROBE_FAILED"},
        )
        return result
    manifest = write_attestation(target, result)
    write_json(
        target / STATE_FILE,
        {
            "schema": "constraintbox.jax-qit-profile-state.v1",
            "profile": PROFILE,
            "status": "VERIFIED",
            "lock_sha256": manifest["requirements"]["lock_sha256"],
            "manifest_sha256": sha256_file(target / "STACK_MANIFEST.json"),
        },
    )
    return {"status": "PASS", "manifest": manifest}


def attest_existing(target: Path) -> dict[str, Any]:
    """Probe an owned target without installing or mutating packages.

    An unowned directory is deliberately a HOLD.  Use ``adopt_existing`` via
    the explicit CLI flag after deciding that the directory is the intended
    external runtime.
    """

    if not target.is_dir():
        return {"status": "HOLD", "reason_code": "HOLD_TARGET_MISSING", "target": str(target)}
    if not _owned_state(target):
        return {"status": "HOLD", "reason_code": "HOLD_TARGET_NOT_OWNED", "target": str(target)}
    source_result = _source_integrity(target)
    if source_result.get("status") != "PASS":
        return source_result
    lock_result = verify_locked_distributions(target)
    if lock_result.get("status") != "PASS":
        return lock_result
    result = run_probe(target)
    if result.get("status") == "PASS":
        _copy_profile_sources(target)
        return {"status": "PASS", "manifest": write_attestation(target, result)}
    return result


def adopt_existing(target: Path) -> dict[str, Any]:
    """Explicitly adopt an existing environment after lock and probe checks.

    No files are written until the target interpreter exists, every exact lock
    pin matches, and the complete API probe passes.  This is the only path
    that may adopt a directory without the profile state marker.
    """

    _target_is_external(target)
    if not target.is_dir():
        return {"status": "HOLD", "reason_code": "HOLD_TARGET_MISSING", "target": str(target)}
    target_python = virtualenv_python(target)
    if not target_python.is_file():
        return {"status": "HOLD", "reason_code": "HOLD_TARGET_PYTHON_MISSING", "target": str(target)}
    lock_result = verify_locked_distributions(target)
    if lock_result.get("status") != "PASS":
        return lock_result
    result = run_probe(target, probe_source=PROBE_SOURCE)
    if result.get("status") != "PASS":
        return result
    # Explicit adoption has now earned permission to add only profile-owned
    # metadata and declarative inputs; it never runs an installer.
    _copy_profile_sources(target)
    manifest = write_attestation(target, result)
    write_json(
        target / STATE_FILE,
        {
            "schema": "constraintbox.jax-qit-profile-state.v1",
            "profile": PROFILE,
            "status": "ADOPTED",
            "lock_sha256": manifest["requirements"]["lock_sha256"],
            "manifest_sha256": sha256_file(target / "STACK_MANIFEST.json"),
        },
    )
    return {"status": "PASS", "mode": "ADOPT_EXISTING", "manifest": manifest, "lock": lock_result}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "install", "probe"):
        command = subparsers.add_parser(name)
        command.add_argument("--target", type=Path)
        command.add_argument("--json", action="store_true", help="retained for explicit machine-readable output")
        if name in {"plan", "install"}:
            command.add_argument("--python", dest="python_executable", default=os.environ.get("CB_JAX_QIT_BUILD_PYTHON", sys.executable))
            command.add_argument("--installer", choices=("auto", "uv", "pip"), default="auto")
            command.add_argument("--uv", dest="uv_executable")
        else:
            command.add_argument(
                "--adopt-existing",
                action="store_true",
                help="explicitly adopt an existing external environment after lock and probe verification",
            )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    target = resolve_target(args.target)
    try:
        if args.command == "plan":
            plan = build_plan(
                target=target,
                python_executable=args.python_executable,
                installer=args.installer,
                uv_executable=args.uv_executable,
            )
            print(json.dumps(plan, indent=2, sort_keys=True))
            return PASS
        if args.command == "install":
            result = install_profile(
                target=target,
                python_executable=args.python_executable,
                installer=args.installer,
                uv_executable=args.uv_executable,
            )
        else:
            result = adopt_existing(target) if args.adopt_existing else attest_existing(target)
        print(json.dumps(result, indent=2, sort_keys=True))
        if result.get("status") == "PASS":
            return PASS
        if result.get("status") == "REFUSE":
            return REFUSE
        return HOLD
    except BootstrapError as exc:
        reason = str(exc)
        status = "HOLD" if reason.startswith("HOLD_") else "REFUSE"
        print(json.dumps({"schema": SCHEMA, "status": status, "reason": reason}, sort_keys=True))
        return HOLD if status == "HOLD" else REFUSE
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"schema": SCHEMA, "status": "HOLD", "reason": f"{type(exc).__name__}:{exc}"}, sort_keys=True))
        return HOLD


if __name__ == "__main__":
    raise SystemExit(main())
