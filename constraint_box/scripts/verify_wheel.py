#!/usr/bin/env python3
"""Verify the portable ConstraintBox *core* from a freshly installed wheel.

This is packaging verification, not a ConstraintBox runtime command.  It is
allowed to invoke pip because it proves an installer boundary; the installed
``constraintbox`` process never installs, selects, or substitutes an
interpreter or a library.

The smoke deliberately covers only the declared lean core: the runtime profile,
the two SMT solvers plus the internal finite reference method, the typed SymPy
operation, and the typed Rustworkx operation.  Sim-engine adapters, MMM/user
profiles, hosted advisers, Maude, and temporal checkers remain separate
contracts and are not made silently load-bearing here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "receipts" / "WHEEL_SMOKE.json"
_ISOLATED = "-I"
_VERIFICATION_SCOPE = "lean_core_install_smoke"
_EXCLUDED_PRODUCT_SURFACES = (
    "user_mmm_and_profile_request_preflight_not_packaged_in_this_wheel",
    "external_sim_engine_adapters_and_estate",
    "maude_and_temporal_external_runtime_profiles",
    "hosted_llm_advisers_and_proposal_release_surfaces",
    "claimgate_full_product_composition",
)
_LEAN_CORE_OPERATION_IDS = (
    "runtime_profile_verification",
    "z3_cvc5_and_internal_finite_reference_agreement",
    "sympy_typed_qq_polynomial",
    "rustworkx_typed_prerequisite_dag",
)


class VerificationError(ValueError):
    """The requested installer-verification boundary is malformed."""


@dataclass(frozen=True)
class Invocation:
    argv: tuple[str, ...]
    returncode: int
    stdout: bytes
    stderr: bytes
    failure_kind: str | None = None


def _bytes(value: bytes | str | None) -> bytes:
    if value is None:
        return b""
    return value if isinstance(value, bytes) else value.encode("utf-8", "replace")


def invoke(
    argv: Iterable[str],
    *,
    timeout: float,
    env: dict[str, str],
) -> Invocation:
    """Run one verifier-owned child and retain failures as receipt data."""

    command = tuple(str(part) for part in argv)
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        return Invocation(
            command,
            124,
            _bytes(exc.stdout),
            _bytes(exc.stderr),
            "timeout",
        )
    except OSError as exc:
        return Invocation(
            command,
            127,
            b"",
            str(exc).encode("utf-8", "replace"),
            "os_error",
        )
    return Invocation(command, completed.returncode, completed.stdout, completed.stderr)


def _fresh_environment() -> dict[str, str]:
    """Prevent a source checkout or caller venv from satisfying the smoke."""

    environment = dict(os.environ)
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        environment.pop(name, None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    return environment


def _venv_python(root: Path) -> Path:
    return (
        root / "Scripts" / "python.exe"
        if os.name == "nt"
        else root / "bin" / "python"
    )


def _json_object(raw: bytes) -> dict[str, Any] | None:
    try:
        value = json.loads(raw)
    except (TypeError, ValueError, UnicodeDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _failure_reason(invocation: Invocation) -> str | None:
    """Return a bounded, portable diagnostic category without copying host logs."""

    if invocation.failure_kind is not None:
        return invocation.failure_kind
    if invocation.returncode == 0:
        return None
    text = (invocation.stdout + b"\n" + invocation.stderr).decode(
        "utf-8", "replace"
    ).casefold()
    if "externally-managed-environment" in text:
        return "externally_managed_python_prevents_venv_bootstrap"
    if "failed to establish a new connection" in text or "nodename nor servname" in text:
        return "package_index_connection_failed"
    if "no matching distribution found" in text:
        return "dependency_not_resolved_from_configured_index"
    if "requires-python" in text or "requires python" in text:
        return "interpreter_outside_declared_python_range"
    return "subprocess_exit_nonzero"


def _lookup(value: dict[str, Any] | None, dotted_path: str) -> object:
    current: object = value
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _check(
    *,
    name: str,
    invocation: Invocation,
    expected_exit: int = 0,
    expected_json: dict[str, object] | None = None,
) -> dict[str, object]:
    body = _json_object(invocation.stdout)
    observed = {
        key: _lookup(body, key)
        for key in sorted((expected_json or {}))
    }
    json_matches = all(
        observed[key] == expected
        for key, expected in (expected_json or {}).items()
    )
    passed = (
        invocation.failure_kind is None
        and invocation.returncode == expected_exit
        and json_matches
    )
    return {
        "name": name,
        "passed": passed,
        "expected_exit": expected_exit,
        "exit": invocation.returncode,
        "expected_json": expected_json or {},
        "observed_json": observed,
        "stdout_sha256": hashlib.sha256(invocation.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(invocation.stderr).hexdigest(),
        "failure_kind": invocation.failure_kind,
        "failure_reason": _failure_reason(invocation),
    }


def _process_check(
    *,
    name: str,
    invocation: Invocation,
    expected_exit: int = 0,
) -> dict[str, object]:
    passed = (
        invocation.failure_kind is None
        and invocation.returncode == expected_exit
    )
    return {
        "name": name,
        "passed": passed,
        "expected_exit": expected_exit,
        "exit": invocation.returncode,
        "stdout_sha256": hashlib.sha256(invocation.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(invocation.stderr).hexdigest(),
        "failure_kind": invocation.failure_kind,
        "failure_reason": _failure_reason(invocation),
    }


def _skipped_check(name: str, reason: str) -> dict[str, object]:
    return {
        "name": name,
        "passed": False,
        "state": "SKIPPED",
        "reason": reason,
    }


def _wheel_candidates(dist: Path) -> tuple[Path, ...]:
    return tuple(sorted(dist.glob("constraintbox-*.whl")))


def discover_wheel(wheel: Path | None) -> Path:
    """Resolve exactly one wheel without selecting a newest arbitrary artifact."""

    if wheel is not None:
        candidate = wheel.expanduser().resolve()
        if not candidate.is_file() or candidate.suffix != ".whl":
            raise VerificationError(f"wheel does not exist or is not a wheel: {candidate}")
        return candidate
    candidates = _wheel_candidates(ROOT / "dist")
    if not candidates:
        raise VerificationError("no constraintbox wheel found; build one before verification")
    if len(candidates) != 1:
        names = ", ".join(candidate.name for candidate in candidates)
        raise VerificationError(
            "wheel selection is ambiguous; pass --wheel explicitly: " + names
        )
    return candidates[0]


def install_argv(
    python: Path,
    wheel: Path,
    *,
    wheelhouse: Path | None,
    offline: bool,
) -> list[str]:
    """Build a normal dependency-resolving installer invocation.

    ``--no-deps`` is intentionally absent.  A wheelhouse is an explicit,
    reproducible offline resolver input; it is never inferred from this host.
    """

    command = [
        str(python),
        _ISOLATED,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
    ]
    if wheelhouse is not None:
        command.extend(("--find-links", str(wheelhouse)))
    if offline:
        command.append("--no-index")
    command.append(str(wheel))
    return command


def _write_payloads(root: Path) -> dict[str, Path]:
    """Write controller-valid inputs owned by the verifier, not checkout fixtures."""

    inputs = root / "inputs"
    inputs.mkdir(parents=True)
    symbolic = inputs / "symbolic.json"
    symbolic.write_text(
        json.dumps(
            {
                "coefficients": [
                    {"degree": 0, "numerator": 1, "denominator": 2},
                    {"degree": 2, "numerator": 3, "denominator": 4},
                ],
                "claimed_canonical": [
                    {"degree": 0, "numerator": 1, "denominator": 2},
                    {"degree": 2, "numerator": 3, "denominator": 4},
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    workflow = inputs / "workflow.json"
    workflow.write_text(
        json.dumps(
            {
                "nodes": ["gate", "intake", "proposal_ready"],
                "edges": [
                    ["gate", "proposal_ready"],
                    ["intake", "gate"],
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return {"symbolic": symbolic, "workflow": workflow}


_INSTALLED_ORIGIN_PROGRAM = """
import json
import sys
from pathlib import Path
import constraintbox

environment_root = Path(sys.prefix).resolve()
module_path = Path(constraintbox.__file__).resolve()
print(json.dumps({
    "schema": "constraintbox.fresh-install-origin.v1",
    "module": "constraintbox",
    "inside_fresh_environment": environment_root == module_path.parent or environment_root in module_path.parents,
}, sort_keys=True))
"""

_SMT_PROGRAM = """
import json
from constraintbox.dualsolve import dual_solve

spec = {
    "variables": {"x": [0, 1], "y": [0, 1]},
    "constraints": [
        {"op": "neq", "left": {"var": "x"}, "right": {"var": "y"}}
    ],
}
print(json.dumps(dual_solve(spec), sort_keys=True))
"""


def _core_checks(
    *,
    python: Path,
    scratch: Path,
    timeout: float,
    env: dict[str, str],
) -> list[dict[str, object]]:
    payloads = _write_payloads(scratch)
    commands: tuple[tuple[str, list[str], dict[str, object]], ...] = (
        (
            "installed_origin",
            [str(python), _ISOLATED, "-c", _INSTALLED_ORIGIN_PROGRAM],
            {
                "schema": "constraintbox.fresh-install-origin.v1",
                "module": "constraintbox",
                "inside_fresh_environment": True,
            },
        ),
        (
            "runtime_verify",
            [str(python), _ISOLATED, "-m", "constraintbox", "runtime", "verify"],
            {"state": "ELIGIBLE", "promotion_allowed": False},
        ),
        (
            "core_smt_z3_cvc5_enumeration",
            [str(python), _ISOLATED, "-c", _SMT_PROGRAM],
            {
                "agree": True,
                "all_definite": True,
                "z3": "BOUNDED_SAT",
                "cvc5": "BOUNDED_SAT",
                "enumeration": "BOUNDED_SAT",
                "backend_execution.z3.state": "EXECUTED_DEFINITE",
                "backend_execution.cvc5.state": "EXECUTED_DEFINITE",
                "backend_execution.enumeration.state": "EXECUTED_DEFINITE",
            },
        ),
        (
            "formal_symbolic_sympy",
            [
                str(python),
                _ISOLATED,
                "-m",
                "constraintbox",
                "formal",
                "run",
                "--task",
                "formal.symbolic.polynomial_qq",
                "--request-id",
                "wheel-symbolic-smoke",
                "--payload",
                str(payloads["symbolic"]),
                "--run-dir",
                str(scratch / "runs" / "symbolic"),
            ],
            {
                "disposition": "ELIGIBLE",
                "task_kind": "formal.symbolic.polynomial_qq",
                "promotion_allowed": False,
                "evidence.exact_operation_receipt.operation": "poly_qq_as_dict",
            },
        ),
        (
            "formal_workflow_rustworkx",
            [
                str(python),
                _ISOLATED,
                "-m",
                "constraintbox",
                "formal",
                "run",
                "--task",
                "formal.workflow.prerequisite_dag",
                "--request-id",
                "wheel-workflow-smoke",
                "--payload",
                str(payloads["workflow"]),
                "--run-dir",
                str(scratch / "runs" / "workflow"),
            ],
            {
                "disposition": "ELIGIBLE",
                "task_kind": "formal.workflow.prerequisite_dag",
                "promotion_allowed": False,
                "evidence.tool.name": "rustworkx",
                "evidence.reference_result.acyclic": True,
            },
        ),
    )
    return [
        _check(
            name=name,
            invocation=invoke(argv, timeout=timeout, env=env),
            expected_json=expected,
        )
        for name, argv, expected in commands
    ]


def verify_wheel(
    wheel: Path,
    *,
    timeout: float = 120.0,
    wheelhouse: Path | None = None,
    offline: bool = False,
) -> dict[str, object]:
    """Install a wheel into a new venv and run the portable core smoke.

    A resolver failure is a failed installer boundary.  It is not converted
    into a source-run, a ``--no-deps`` install, or a partial passing receipt.
    """

    wheel = wheel.expanduser().resolve()
    if not wheel.is_file() or wheel.suffix != ".whl":
        raise VerificationError(f"wheel does not exist or is not a wheel: {wheel}")
    if timeout <= 0:
        raise VerificationError("timeout must be positive")
    if offline and wheelhouse is None:
        raise VerificationError("--offline requires an explicit --wheelhouse")
    if wheelhouse is not None:
        wheelhouse = wheelhouse.expanduser().resolve()
        if not wheelhouse.is_dir():
            raise VerificationError(f"wheelhouse is not a directory: {wheelhouse}")

    checks: list[dict[str, object]] = []
    environment = _fresh_environment()
    install_mode = (
        "offline_wheelhouse_dependency_resolution"
        if offline
        else "normal_dependency_resolution"
    )
    with tempfile.TemporaryDirectory(prefix="constraintbox-wheel-") as directory:
        root = Path(directory)
        create = _process_check(
            name="fresh_venv_create",
            invocation=invoke(
                [sys.executable, "-m", "venv", str(root)],
                timeout=timeout,
                env=environment,
            ),
        )
        checks.append(create)
        python = _venv_python(root)
        if not create["passed"] or not python.is_file():
            checks.extend(
                _skipped_check(name, "fresh_venv_unavailable")
                for name in (
                    "dependency_resolved_install",
                    "pip_dependency_check",
                    "installed_origin",
                    "runtime_verify",
                    "core_smt_z3_cvc5_enumeration",
                    "formal_symbolic_sympy",
                    "formal_workflow_rustworkx",
                )
            )
            reason = "fresh_venv_creation_failed"
        else:
            install = _process_check(
                name="dependency_resolved_install",
                invocation=invoke(
                    install_argv(
                        python,
                        wheel,
                        wheelhouse=wheelhouse,
                        offline=offline,
                    ),
                    timeout=timeout,
                    env=environment,
                ),
            )
            checks.append(install)
            if not install["passed"]:
                checks.extend(
                    _skipped_check(name, "dependency_resolution_or_wheel_install_failed")
                    for name in (
                        "pip_dependency_check",
                        "installed_origin",
                        "runtime_verify",
                        "core_smt_z3_cvc5_enumeration",
                        "formal_symbolic_sympy",
                        "formal_workflow_rustworkx",
                    )
                )
                reason = "dependency_resolution_or_wheel_install_failed"
            else:
                checks.append(
                    _process_check(
                        name="pip_dependency_check",
                        invocation=invoke(
                            [str(python), _ISOLATED, "-m", "pip", "check"],
                            timeout=timeout,
                            env=environment,
                        ),
                    )
                )
                checks.extend(
                    _core_checks(
                        python=python,
                        scratch=root / "smoke",
                        timeout=timeout,
                        env=environment,
                    )
                )
                reason = (
                    "portable_core_smoke_passed"
                    if all(check.get("passed") is True for check in checks)
                    else "portable_core_smoke_failed"
                )

    passed = all(check.get("passed") is True for check in checks)
    return {
        "schema": "constraintbox.wheel-smoke.v2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "verification_scope": _VERIFICATION_SCOPE,
        "full_constraintbox_product_verified": False,
        "verified_lean_core_operations": list(_LEAN_CORE_OPERATION_IDS),
        "excluded_product_surfaces": list(_EXCLUDED_PRODUCT_SURFACES),
        "claim_ceiling": (
            "a fresh dependency-resolved installation executed the declared "
            "portable lean-core checks only; this is not verification of the "
            "full ConstraintBox product, user MMM/profile resources, external "
            "sim estate, LLM/provider paths, ClaimGate composition, release, "
            "promotion, or scientific truth"
        ),
        "wheel": wheel.name,
        "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "fresh_environment": True,
        "isolated_children": True,
        "installer_verification_only": True,
        "runtime_never_installs_dependencies": True,
        "dependency_resolution_mode": install_mode,
        "wheelhouse_supplied": wheelhouse is not None,
        "checks": checks,
        "reason": reason,
        "state": "READY" if passed else "FAILED",
        "promotion_allowed": False,
    }


def _write_receipt(path: Path, receipt: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="fresh-install verification for the portable ConstraintBox core"
    )
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="resolve only from the explicitly supplied wheelhouse",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        receipt = verify_wheel(
            discover_wheel(args.wheel),
            timeout=args.timeout,
            wheelhouse=args.wheelhouse,
            offline=args.offline,
        )
    except VerificationError as exc:
        receipt = {
            "schema": "constraintbox.wheel-smoke.v2",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "verification_scope": _VERIFICATION_SCOPE,
            "full_constraintbox_product_verified": False,
            "verified_lean_core_operations": list(_LEAN_CORE_OPERATION_IDS),
            "excluded_product_surfaces": list(_EXCLUDED_PRODUCT_SURFACES),
            "claim_ceiling": (
                "installer verification could not start; it is not a full "
                "ConstraintBox product verification"
            ),
            "fresh_environment": False,
            "installer_verification_only": True,
            "runtime_never_installs_dependencies": True,
            "checks": [],
            "reason": "verifier_configuration_error",
            "error": str(exc),
            "state": "FAILED",
            "promotion_allowed": False,
        }
    _write_receipt(args.receipt, receipt)
    if receipt["state"] != "READY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
