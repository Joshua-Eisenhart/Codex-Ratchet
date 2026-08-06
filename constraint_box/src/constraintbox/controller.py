from __future__ import annotations

import dataclasses
import hashlib
import inspect
import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

from .constraints import ConstraintSpecError, FiniteConstraintProblem, SolverStatus
from .contracts import DecisionRecord, Disposition, ProfileOutcome, TaskRequest
from .intake import IntakeError, canonical_json, parse_json_object
from .ledger import HashChainLedger
from .python_runtime import (
    PythonRuntimeError,
    capture_python_runtime,
    python_runtime_policy_sha256,
    verify_python_runtime_stable,
)

_SHA256 = hashlib.sha256


class Profile(Protocol):
    profile_id: str
    claim_ceiling: str

    def evaluate(self, payload: bytes, run_dir: Path) -> ProfileOutcome: ...


@dataclass(frozen=True)
class StrictJsonProfile:
    profile_id: str = "constraintbox.intake.strict-json.v1"
    claim_ceiling: str = "the supplied byte snapshot is unambiguous finite JSON"

    def evaluate(self, payload: bytes, run_dir: Path) -> ProfileOutcome:
        del run_dir
        try:
            body = parse_json_object(payload)
        except IntakeError as exc:
            return ProfileOutcome(
                Disposition.BLOCKED, "strict_intake_failed", {"error": str(exc)}
            )
        return ProfileOutcome(
            Disposition.ELIGIBLE,
            "strict_intake_passed",
            {"root_keys": sorted(body)},
        )


@dataclass(frozen=True)
class AgentProposalProfile:
    """Accepts candidate material while rejecting authority-bearing fields."""

    profile_id: str = "constraintbox.agent.proposal.v1"
    claim_ceiling: str = "untrusted proposal recorded; no execution or admission"
    forbidden_fields: tuple[str, ...] = (
        "command",
        "decision",
        "verdict",
        "pass",
        "all_pass",
        "profile_id",
        "tolerance",
        "promotion_allowed",
        "numeric_engine_required",
        "load_bearing",
        "ran",
    )

    def evaluate(self, payload: bytes, run_dir: Path) -> ProfileOutcome:
        del run_dir
        try:
            body = parse_json_object(payload)
        except IntakeError as exc:
            return ProfileOutcome(
                Disposition.BLOCKED, "strict_intake_failed", {"error": str(exc)}
            )
        forbidden: list[str] = []

        def walk(value: object, path: str = "$") -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    child_path = f"{path}.{key}"
                    if key.casefold() in self.forbidden_fields:
                        forbidden.append(child_path)
                    walk(child, child_path)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, f"{path}[{index}]")

        walk(body)
        if forbidden:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "proposal_attempted_controller_authority",
                {"forbidden_paths": forbidden},
            )
        required = {"proposal_id", "candidate", "falsifiers"}
        if not required.issubset(body):
            return ProfileOutcome(
                Disposition.PARKED,
                "proposal_incomplete",
                {"missing": sorted(required - set(body))},
            )
        return ProfileOutcome(
            Disposition.ELIGIBLE,
            "proposal_recorded",
            {"proposal_sha256": _SHA256(canonical_json(body)).hexdigest()},
        )


@dataclass(frozen=True)
class FiniteConstraintProfile:
    backend: str = "enumeration"
    max_states: int = 100_000
    expected_status: SolverStatus = SolverStatus.BOUNDED_SAT
    profile_id: str = "constraintbox.constraints.finite.v1"
    claim_ceiling: str = "one finite encoding was checked within its declared bound"

    def __post_init__(self) -> None:
        if self.backend not in {"enumeration", "z3"}:
            raise ValueError("backend must be enumeration or z3")
        if (
            not isinstance(self.max_states, int)
            or isinstance(self.max_states, bool)
            or self.max_states < 1
        ):
            raise ValueError("max_states must be a positive integer")
        if self.expected_status not in {
            SolverStatus.BOUNDED_SAT,
            SolverStatus.BOUNDED_UNSAT,
        }:
            raise ValueError("expected_status must be BOUNDED_SAT or BOUNDED_UNSAT")

    def evaluate(self, payload: bytes, run_dir: Path) -> ProfileOutcome:
        del run_dir
        try:
            body = parse_json_object(payload)
            problem = FiniteConstraintProblem.from_spec(body)
        except (IntakeError, ConstraintSpecError, TypeError, ValueError) as exc:
            return ProfileOutcome(
                Disposition.BLOCKED, "finite_problem_invalid", {"error": str(exc)}
            )
        try:
            result = (
                problem.solve_z3(self.max_states)
                if self.backend == "z3"
                else problem.solve_enumerated(self.max_states)
            )
        except Exception as exc:  # fail closed at the solver boundary
            return ProfileOutcome(
                Disposition.PARKED,
                "bounded_solver_error",
                {
                    "backend": self.backend,
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
        evidence = {
            "solver_status": result.status.value,
            "expected_status": self.expected_status.value,
            "backend": result.backend,
            "explored": result.explored,
            "reason": result.reason,
            "state_count": problem.state_count,
            "witness": result.witness,
        }
        if result.status is SolverStatus.UNKNOWN:
            return ProfileOutcome(Disposition.PARKED, "bounded_solver_unknown", evidence)
        if result.status is not self.expected_status:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "bounded_solver_polarity_mismatch",
                evidence,
            )
        return ProfileOutcome(
            Disposition.ELIGIBLE,
            "bounded_expected_status_observed",
            evidence,
        )


@dataclass(frozen=True)
class RegisteredWorkerProfile:
    profile_id: str
    worker_id: str
    argv_template: tuple[str, ...]
    source_path: Path
    source_sha256: str
    timeout_seconds: float = 10.0
    claim_ceiling: str = "one registered worker ran and emitted a bound artifact"

    def evaluate(self, payload: bytes, run_dir: Path) -> ProfileOutcome:
        actual_source_sha = _SHA256(self.source_path.read_bytes()).hexdigest()
        if actual_source_sha != self.source_sha256:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "worker_source_digest_mismatch",
                {"expected": self.source_sha256, "actual": actual_source_sha},
            )
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "request_run_directory_already_exists",
                {"run_directory": str(run_dir)},
            )
        input_path = run_dir / "input.json"
        output_path = run_dir / "output.json"
        input_path.write_bytes(payload)
        substitutions = {
            "{source}": str(self.source_path),
            "{input}": str(input_path),
            "{output}": str(output_path),
        }
        argv = tuple(substitutions.get(part, part) for part in self.argv_template)
        try:
            proc = subprocess.run(
                argv,
                cwd=run_dir,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return ProfileOutcome(Disposition.PARKED, "worker_timeout")
        evidence = {
            "worker_id": self.worker_id,
            "source_sha256": actual_source_sha,
            "argv_sha256": _SHA256("\0".join(argv).encode()).hexdigest(),
            "exit_code": proc.returncode,
            "stdout_sha256": _SHA256(proc.stdout).hexdigest(),
            "stderr_sha256": _SHA256(proc.stderr).hexdigest(),
        }
        if proc.returncode != 0:
            return ProfileOutcome(
                Disposition.BLOCKED, "worker_nonzero_exit", evidence
            )
        if not output_path.exists():
            return ProfileOutcome(
                Disposition.BLOCKED, "worker_output_missing", evidence
            )
        try:
            output = parse_json_object(output_path.read_bytes())
        except IntakeError as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "worker_output_invalid",
                {**evidence, "error": str(exc)},
            )
        evidence.update(
            {
                "output_sha256": _SHA256(output_path.read_bytes()).hexdigest(),
                "output_root_keys": sorted(output),
            }
        )
        return ProfileOutcome(
            Disposition.ELIGIBLE, "registered_worker_executed", evidence
        )


def _policy_jsonable(value: Any) -> Any:
    """Convert effective policy settings without falling back to prose/repr."""

    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value.resolve())
    if isinstance(value, tuple):
        return [_policy_jsonable(item) for item in value]
    if isinstance(value, list):
        raise TypeError(
            "effective policy cannot contain a mutable list; use a tuple"
        )
    if isinstance(value, dict):
        raise TypeError(
            "effective policy cannot contain a mutable dict; use a frozen "
            "controller-owned representation"
        )
    raise TypeError(
        f"effective policy contains unsupported value type: {type(value).__name__}"
    )


def _profile_policy_material(profile: Profile) -> dict[str, Any]:
    """Bind the profile implementation and every dataclass policy setting."""

    if not dataclasses.is_dataclass(profile):
        raise TypeError(
            f"profile {type(profile).__name__} must be a frozen dataclass"
        )
    dataclass_parameters = getattr(type(profile), "__dataclass_params__", None)
    if dataclass_parameters is None or dataclass_parameters.frozen is not True:
        raise TypeError(
            f"profile {type(profile).__name__} must be a frozen dataclass"
        )
    source_name = inspect.getsourcefile(type(profile))
    if source_name is None:
        raise TypeError(
            f"profile source is not locatable: {type(profile).__name__}"
        )
    source_path = Path(source_name).resolve()
    if not source_path.is_file():
        raise TypeError(f"profile source is not a file: {source_path}")
    settings = {
        field.name: _policy_jsonable(getattr(profile, field.name))
        for field in dataclasses.fields(profile)
    }
    return {
        "class": f"{type(profile).__module__}.{type(profile).__qualname__}",
        "source_sha256": _SHA256(source_path.read_bytes()).hexdigest(),
        "settings": settings,
    }


class ConstraintBoxController:
    """Controller-owned task policy. Requests cannot select profiles."""

    def __init__(
        self,
        task_policy: dict[str, Profile],
        run_root: Path,
        ledger: HashChainLedger | None = None,
        max_payload_bytes: int = 1_048_576,
    ):
        if max_payload_bytes < 1:
            raise ValueError("max_payload_bytes must be positive")
        self._task_policy = dict(task_policy)
        self._run_root = run_root
        self._ledger = ledger
        self._max_payload_bytes = max_payload_bytes
        self._policy_sha256 = _SHA256(
            canonical_json(
                {
                    "schema": "constraintbox.effective-policy.v2",
                    "max_payload_bytes": self._max_payload_bytes,
                    "python_runtime_policy_sha256": (
                        python_runtime_policy_sha256()
                    ),
                    "tasks": {
                        task: _profile_policy_material(profile)
                        for task, profile in sorted(self._task_policy.items())
                    },
                }
            )
        ).hexdigest()

    @property
    def policy_sha256(self) -> str:
        return self._policy_sha256

    def run(self, request: TaskRequest) -> DecisionRecord:
        try:
            runtime_before = capture_python_runtime()
        except PythonRuntimeError as exc:
            input_sha = (
                _SHA256(request.payload).hexdigest()
                if len(request.payload) <= self._max_payload_bytes
                else None
            )
            record = DecisionRecord(
                "constraintbox.decision.v1",
                request.request_id,
                request.task_kind,
                None,
                self._policy_sha256,
                input_sha,
                Disposition.HOLD,
                "python_runtime_identity_error",
                {
                    "python_runtime": {
                        "expected_policy_sha256": (
                            python_runtime_policy_sha256()
                        ),
                        "error": str(exc),
                        "stable": False,
                    }
                },
                (
                    "controller evaluation did not start because the selected "
                    "CPython execution substrate could not be verified"
                ),
            )
            if self._ledger is not None:
                self._ledger.append(record.to_dict())
            return record

        payload_size = len(request.payload)
        if payload_size > self._max_payload_bytes:
            inspected_prefix = request.payload[: self._max_payload_bytes + 1]
            record = DecisionRecord(
                "constraintbox.decision.v1",
                request.request_id,
                request.task_kind,
                None,
                self._policy_sha256,
                None,
                Disposition.BLOCKED,
                "payload_exceeds_controller_bound",
                {
                    "observed_bytes": payload_size,
                    "maximum_bytes": self._max_payload_bytes,
                    "inspected_prefix_bytes": len(inspected_prefix),
                    "bounded_prefix_sha256": _SHA256(
                        inspected_prefix
                    ).hexdigest(),
                    "input_digest_complete": False,
                },
                (
                    "the payload was rejected from its length before full hashing "
                    "or profile evaluation; only a bounded prefix was committed"
                ),
            )
        else:
            input_sha = _SHA256(request.payload).hexdigest()
            safe_request_id = (
                request.request_id not in {".", ".."}
                and re.fullmatch(
                    r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}",
                    request.request_id,
                )
                is not None
            )
            if not safe_request_id:
                record = DecisionRecord(
                    "constraintbox.decision.v1",
                    request.request_id,
                    request.task_kind,
                    None,
                    self._policy_sha256,
                    input_sha,
                    Disposition.BLOCKED,
                    "invalid_request_id",
                    {},
                    (
                        "the untrusted request identifier was rejected "
                        "before execution"
                    ),
                )
            else:
                profile = self._task_policy.get(request.task_kind)
                if profile is None:
                    record = DecisionRecord(
                        "constraintbox.decision.v1",
                        request.request_id,
                        request.task_kind,
                        None,
                        self._policy_sha256,
                        input_sha,
                        Disposition.BLOCKED,
                        "unknown_task_kind",
                        {},
                        "no bounded work was executed",
                    )
                else:
                    try:
                        outcome = profile.evaluate(
                            request.payload,
                            self._run_root / request.request_id,
                        )
                    except Exception as exc:
                        record = DecisionRecord(
                            "constraintbox.decision.v1",
                            request.request_id,
                            request.task_kind,
                            profile.profile_id,
                            self._policy_sha256,
                            input_sha,
                            Disposition.HOLD,
                            "profile_evaluation_error",
                            {
                                "exception_type": type(exc).__name__,
                                "error": str(exc)[:1024],
                            },
                            (
                                "the registered profile raised before producing "
                                "a controller-admissible outcome"
                            ),
                        )
                    else:
                        if "python_runtime" in outcome.evidence:
                            record = DecisionRecord(
                                "constraintbox.decision.v1",
                                request.request_id,
                                request.task_kind,
                                profile.profile_id,
                                self._policy_sha256,
                                input_sha,
                                Disposition.HOLD,
                                "profile_used_reserved_evidence_key",
                                {},
                                (
                                    "the controller rejected profile evidence that "
                                    "attempted to occupy its runtime-identity field"
                                ),
                            )
                        else:
                            record = DecisionRecord(
                                "constraintbox.decision.v1",
                                request.request_id,
                                request.task_kind,
                                profile.profile_id,
                                self._policy_sha256,
                                input_sha,
                                outcome.disposition,
                                outcome.reason,
                                outcome.evidence,
                                profile.claim_ceiling,
                            )

        runtime_after: dict[str, Any] | None = None
        try:
            runtime_after = capture_python_runtime()
            verify_python_runtime_stable(runtime_before, runtime_after)
        except PythonRuntimeError as exc:
            record = DecisionRecord(
                "constraintbox.decision.v1",
                request.request_id,
                request.task_kind,
                record.profile_id,
                self._policy_sha256,
                record.input_sha256,
                Disposition.HOLD,
                "python_runtime_changed_during_evaluation",
                {
                    "python_runtime": {
                        "before": runtime_before,
                        "after": runtime_after,
                        "error": str(exc),
                        "stable": False,
                    },
                    "superseded_outcome": {
                        "disposition": record.disposition.value,
                        "reason": record.reason,
                    },
                },
                (
                    "the selected CPython execution substrate could not be "
                    "verified after evaluation; no task outcome was admitted"
                ),
            )
        else:
            record = dataclasses.replace(
                record,
                evidence={
                    **record.evidence,
                    "python_runtime": {
                        "expected_policy_sha256": (
                            python_runtime_policy_sha256()
                        ),
                        "before": runtime_before,
                        "after": runtime_after,
                        "stable": True,
                    },
                },
            )
        if self._ledger is not None:
            self._ledger.append(record.to_dict())
        return record
