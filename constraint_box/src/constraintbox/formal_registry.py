from __future__ import annotations

import hashlib
import importlib.metadata
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .boundary_contract import BoundaryContractProfile, TASK_BOUNDARY_CONTRACT
from .contracts import DecisionRecord, Disposition, TaskRequest
from .controller import ConstraintBoxController, Profile
from .formalcheck import (
    FormalCheckReceipt,
    FormalCheckStatus,
    TemporalCheckProfile,
    run_temporal_check,
)
from .intake import IntakeError, canonical_json, parse_json_object
from .ledger import HashChainLedger
from .levos_flowmind import LevDnaFlowMindGraphProfile
from .maude_rewrite import MaudeTransitionProfile
from .python_runtime import (
    DEFAULT_PYTHON_RUNTIME_POLICY,
    load_python_runtime_policy,
)
from .runtime_profiles import inspect_active_runtime
from .symbolic import SympyRationalPolynomialProfile
from .workflow_graph import WorkflowGraphProfile


TASK_SYMBOLIC_POLYNOMIAL = "formal.symbolic.polynomial_qq"
TASK_WORKFLOW_GRAPH = "formal.workflow.prerequisite_dag"
TASK_PHASE_TRANSITION = "formal.transition.current_box_phase"
TASK_INTEGRATED_WORKLOAD_TRANSITION = "formal.transition.integrated_workload"
TASK_LEVOS_FLOWMIND_GRAPH = "formal.levos.flowmind_contract_structure"
FORMAL_MAX_PAYLOAD_BYTES = 65_536

_FORMAL_RUNTIME_ROOT = Path(__file__).resolve().parent / "formal_runtime"
DEFAULT_FORMAL_RUNTIME_POLICY = (
    _FORMAL_RUNTIME_ROOT / "formal_runtime_v1.json"
)
_FORMAL_RUNTIME_POLICY_SHA256 = (
    "1d3461b0316348c25f9722bd89e2a3cf36f54e3632406cd77d0c152d59434641"
)
_PAIR_CLAIM_CEILING = (
    "only a PASSED required pair establishes that TLC and Apalache separately "
    "checked the same hash-pinned bounded single-run abstract state-ordering "
    "skeleton and its evidence-removal mutant; even that does not establish "
    "Python-controller correspondence or conformance, decision correctness, "
    "actor identity, evidence provenance, retry, lease, release, liveness, "
    "concurrency, refinement, general correctness, or sim-estate admission"
)
_PAIR_BLOCKED_CONSUMERS = (
    "python_implementation_conformance",
    "decision_correctness_claims",
    "actor_identity_claims",
    "evidence_provenance_claims",
    "retry_safety_claims",
    "lease_safety_claims",
    "release_correctness_claims",
    "liveness_claims",
    "concurrency_claims",
    "refinement_claims",
    "external_sim_estate_admission",
)

_CURRENT_PHASE_STATES = (
    "audit_bound",
    "context_compiled",
    "external_observed",
    "proposal_ready",
    "received",
    "request_assessed",
)
_CURRENT_PHASE_TRANSITIONS = (
    ("audit_bound", "observe_external", "external_observed"),
    ("audit_bound", "skip_external", "proposal_ready"),
    ("context_compiled", "bind_audit", "audit_bound"),
    ("external_observed", "accept_packet_observation", "proposal_ready"),
    ("received", "assess_request", "request_assessed"),
    ("request_assessed", "compile_context", "context_compiled"),
)

# This is the state machine for the fixed high-assurance workload.  It is not
# a claim about a user request or a scientific workflow: every state names one
# controller-owned evidence stage below.  The integrated runner can advance
# only after it has recorded the preceding stage's real receipt.
_INTEGRATED_WORKLOAD_STATES = (
    "complete",
    "lease_validated",
    "levos_observed",
    "received",
    "smt_crosschecked",
    "suite_observed",
    "symbolic_validated",
    "temporal_validated",
    "workflow_validated",
)
_INTEGRATED_WORKLOAD_TRANSITIONS = (
    ("lease_validated", "validate_workflow", "workflow_validated"),
    ("levos_observed", "validate_symbolic", "symbolic_validated"),
    ("received", "observe_suite", "suite_observed"),
    ("smt_crosschecked", "validate_lease", "lease_validated"),
    ("suite_observed", "cross_check", "smt_crosschecked"),
    ("symbolic_validated", "check_temporal", "temporal_validated"),
    ("temporal_validated", "complete", "complete"),
    ("workflow_validated", "observe_levos_flowmind", "levos_observed"),
)


class FormalRegistryError(ValueError):
    pass


class FormalRuntimeUnavailable(RuntimeError):
    """A declared external formal runtime is not configured on this host."""


@dataclass(frozen=True)
class FormalRuntimeBackend:
    checker_artifact_relative_path: Path
    required: bool


@dataclass(frozen=True)
class FormalRuntimePolicy:
    policy_sha256: str
    profile_dir: Path
    expected_expectations_sha256: str
    runtime_directory_env: str
    java_command: str
    timeout_seconds: float
    backends: dict[str, FormalRuntimeBackend]


@dataclass(frozen=True)
class FormalRuntimeResolved:
    """One installation-specific observation of the declared formal tools."""

    runtime_directory: Path
    java_executable: Path
    checker_artifacts: dict[str, Path]


def formal_task_policy() -> dict[str, Profile]:
    """Return the complete controller-owned per-request formal policy."""

    return {
        TASK_BOUNDARY_CONTRACT: BoundaryContractProfile(),
        TASK_SYMBOLIC_POLYNOMIAL: SympyRationalPolynomialProfile(),
        TASK_WORKFLOW_GRAPH: WorkflowGraphProfile(
            required_reachability=(("intake", "proposal_ready"),),
            max_nodes=64,
            max_edges=256,
        ),
        TASK_LEVOS_FLOWMIND_GRAPH: LevDnaFlowMindGraphProfile(),
        TASK_PHASE_TRANSITION: MaudeTransitionProfile(
            states=_CURRENT_PHASE_STATES,
            transitions=_CURRENT_PHASE_TRANSITIONS,
            max_states=len(_CURRENT_PHASE_STATES),
            max_rules=len(_CURRENT_PHASE_TRANSITIONS),
            max_applications=1,
            timeout_seconds=5.0,
        ),
        TASK_INTEGRATED_WORKLOAD_TRANSITION: MaudeTransitionProfile(
            states=_INTEGRATED_WORKLOAD_STATES,
            transitions=_INTEGRATED_WORKLOAD_TRANSITIONS,
            max_states=len(_INTEGRATED_WORKLOAD_STATES),
            max_rules=len(_INTEGRATED_WORKLOAD_TRANSITIONS),
            max_applications=1,
            timeout_seconds=5.0,
        ),
    }


def formal_task_kinds() -> tuple[str, ...]:
    return tuple(sorted(formal_task_policy()))


def build_formal_controller(run_root: Path) -> ConstraintBoxController:
    """Build the fixed formal controller and its append-only decision ledger."""

    if not isinstance(run_root, Path) or not run_root.is_absolute():
        raise ValueError("run_root must be an absolute pathlib.Path")
    ledger = HashChainLedger(run_root / "formal_decisions.jsonl")
    return ConstraintBoxController(
        formal_task_policy(),
        run_root,
        ledger=ledger,
        max_payload_bytes=FORMAL_MAX_PAYLOAD_BYTES,
    )


def run_formal_task(
    *,
    task_kind: str,
    request_id: str,
    payload: bytes,
    run_root: Path,
) -> DecisionRecord:
    from .formal_flow import run_formal_flow

    return run_formal_flow(
        task_kind=task_kind,
        request_id=request_id,
        payload=payload,
        run_root=run_root,
    )


def _run_formal_task_core(
    *,
    task_kind: str,
    request_id: str,
    payload: bytes,
    run_root: Path,
) -> DecisionRecord:
    """Execute the fixed controller below the mini-LevOS wrapper."""

    controller = build_formal_controller(run_root)
    return controller.run(
        TaskRequest(
            task_kind=task_kind,
            payload=payload,
            request_id=request_id,
        )
    )


def _distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def formal_catalog() -> dict[str, Any]:
    """Describe roles and callers without granting any instrument authority."""

    profiles = formal_task_policy()
    python_policy = load_python_runtime_policy()
    return {
        "schema": "constraintbox.formal-catalog.v1",
        "execution_substrate": {
            "name": "CPython",
            "profile_ids": list(python_policy.profile_ids),
            "policy_path": str(DEFAULT_PYTHON_RUNTIME_POLICY.resolve()),
            "policy_sha256": python_policy.policy_sha256,
            "operation_ids": list(python_policy.operation_ids),
            "active_runtime": inspect_active_runtime(),
            "role": (
                "required core executor for the controller, finite reference "
                "algorithms, hooks, ledgers, and Python-facing tool adapters"
            ),
            "callers": [
                "ConstraintBoxController.run",
                "MiniLevRuntime.run",
                "dual_solve",
            ],
            "decision_authority": False,
            "promotion_allowed": False,
        },
        "controller_policy": {
            task: {
                "profile_id": profile.profile_id,
                "claim_ceiling": profile.claim_ceiling,
                "caller": "constraintbox formal run",
                "default_policy": True,
            }
            for task, profile in sorted(profiles.items())
        },
        "instruments": [
            {
                "name": "Z3",
                "distribution": "z3-solver",
                "version": _distribution_version("z3-solver"),
                "role": "required request-gate SMT decider",
                "caller": "assess_user_request",
                "decision_authority": False,
            },
            {
                "name": "CVC5",
                "distribution": "cvc5",
                "version": _distribution_version("cvc5"),
                "role": "required independent request-gate SMT decider",
                "caller": "assess_user_request",
                "decision_authority": False,
            },
            {
                "name": "SymPy",
                "distribution": "sympy",
                "version": _distribution_version("sympy"),
                "role": "bounded typed exact-polynomial instrument",
                "caller": "constraintbox formal run",
                "decision_authority": False,
            },
            {
                "name": "Rustworkx",
                "distribution": "rustworkx",
                "version": _distribution_version("rustworkx"),
                "role": "bounded workflow DAG and reachability instrument",
                "caller": "constraintbox formal run",
                "decision_authority": False,
            },
            {
                "name": "Maude",
                "distribution": "maude",
                "version": _distribution_version("maude"),
                "role": (
                    "fresh-subprocess one-step controller-transition "
                    "instrument"
                ),
                "caller": "constraintbox formal run",
                "decision_authority": False,
            },
            {
                "name": "TLC",
                "distribution": None,
                "version": None,
                "controller_expected_version": "2.19",
                "version_evidence": "must come from the current temporal receipt",
                "role": "required offline bounded lifecycle checker",
                "caller": "constraintbox formal temporal",
                "decision_authority": False,
            },
            {
                "name": "Apalache",
                "distribution": None,
                "version": None,
                "controller_expected_version": "0.58.3",
                "version_evidence": "must come from the current temporal receipt",
                "role": "required independent offline bounded lifecycle checker",
                "caller": "constraintbox formal temporal",
                "decision_authority": False,
            },
        ],
        "internal_reference_methods": [
            {
                "name": "bounded exhaustive enumeration",
                "role": (
                    "reference algorithm executed by the profile-verified active CPython using "
                    "itertools.product, math.prod, builtins, dictionaries, "
                    "comparisons, and bounded controller loops"
                ),
                "external_tool": False,
                "caller": "dual_solve",
                "decision_authority": False,
            }
        ],
        "test_only": [
            {
                "name": "Hypothesis",
                "distribution": "hypothesis",
                "version": _distribution_version("hypothesis"),
                "role": (
                    "fixed-seed deterministic hostile test generation and "
                    "regeneration"
                ),
                "diagnostic_import": (
                    "the general doctor may import Hypothesis only to report "
                    "its installed state"
                ),
                "runtime_authority": False,
            }
        ],
        "optional_not_default": [
            {
                "name": "NumPy",
                "distribution": "numpy",
                "version": _distribution_version("numpy"),
                "role": "allowed bounded numeric extension",
                "reason": (
                    "not required by the formal kernel and not registered in "
                    "the default formal task policy"
                ),
            }
        ],
        "external_system_boundary": (
            "The cb:external-sim-validation-adapter is contained source, but its "
            "sim:* operation profiles, installed JAX/PyTorch/Julia/PySINDy/PyDMD/"
            "SciPy/Diffrax/graph/QIT engines, CR, and the larger sim estate are "
            "external test subjects or consumers, not this formal decision policy"
        ),
        "promotion_allowed": False,
    }


def _require_exact_keys(
    value: object,
    expected: set[str],
    where: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise FormalRegistryError(
            f"{where} must contain exactly {sorted(expected)}"
        )
    return value


def _bounded_float(value: object, where: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not 0.1 <= float(value) <= 120.0
    ):
        raise FormalRegistryError(f"{where} must be from 0.1 through 120")
    return float(value)


def load_formal_runtime_policy(
    path: Path = DEFAULT_FORMAL_RUNTIME_POLICY,
) -> FormalRuntimePolicy:
    if path != DEFAULT_FORMAL_RUNTIME_POLICY:
        raise FormalRegistryError("the formal runtime policy path is fixed")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise FormalRegistryError(f"formal runtime policy unavailable: {exc}") from exc
    observed_hash = hashlib.sha256(raw).hexdigest()
    if observed_hash != _FORMAL_RUNTIME_POLICY_SHA256:
        raise FormalRegistryError(
            "formal runtime policy digest differs from the controller pin"
        )
    try:
        body = parse_json_object(raw)
    except IntakeError as exc:
        raise FormalRegistryError(f"invalid formal runtime policy: {exc}") from exc
    _require_exact_keys(
        body,
        {
            "schema",
            "profile_dir",
            "expected_expectations_sha256",
            "runtime_directory_env",
            "java_command",
            "timeout_seconds",
            "backends",
        },
        "$",
    )
    if body["schema"] != "constraintbox.formal-runtime-policy.v2":
        raise FormalRegistryError("formal runtime policy schema mismatch")
    if not isinstance(body["profile_dir"], str):
        raise FormalRegistryError("$.profile_dir must be a string")
    profile_relative = Path(body["profile_dir"])
    if profile_relative.is_absolute() or ".." in profile_relative.parts:
        raise FormalRegistryError("$.profile_dir must stay inside ConstraintBox")
    runtime_root = _FORMAL_RUNTIME_ROOT.resolve()
    profile_dir = (runtime_root / profile_relative).resolve()
    if profile_dir != runtime_root and runtime_root not in profile_dir.parents:
        raise FormalRegistryError("$.profile_dir escaped ConstraintBox")
    expected_hash = body["expected_expectations_sha256"]
    if (
        not isinstance(expected_hash, str)
        or len(expected_hash) != 64
        or any(char not in "0123456789abcdef" for char in expected_hash)
    ):
        raise FormalRegistryError(
            "$.expected_expectations_sha256 must be a lowercase SHA-256"
        )
    if body["runtime_directory_env"] != "CONSTRAINTBOX_FORMAL_RUNTIME_DIR":
        raise FormalRegistryError(
            "$.runtime_directory_env must remain the declared installer setting"
        )
    if body["java_command"] != "java":
        raise FormalRegistryError("$.java_command must remain java")
    raw_backends = _require_exact_keys(
        body["backends"],
        {"apalache", "tlc"},
        "$.backends",
    )
    backends: dict[str, FormalRuntimeBackend] = {}
    for backend_name in ("apalache", "tlc"):
        backend = _require_exact_keys(
            raw_backends[backend_name],
            {"checker_artifact_relative_path", "required"},
            f"$.backends.{backend_name}",
        )
        artifact_value = backend["checker_artifact_relative_path"]
        if not isinstance(artifact_value, str):
            raise FormalRegistryError(
                f"$.backends.{backend_name}.checker_artifact_relative_path must be a string"
            )
        artifact = Path(artifact_value)
        if artifact.is_absolute() or ".." in artifact.parts or not artifact.parts:
            raise FormalRegistryError(
                f"$.backends.{backend_name}.checker artifact must stay inside the configured runtime directory"
            )
        if backend["required"] is not True:
            raise FormalRegistryError(
                f"$.backends.{backend_name}.required must remain true"
            )
        backends[backend_name] = FormalRuntimeBackend(artifact, True)
    return FormalRuntimePolicy(
        policy_sha256=observed_hash,
        profile_dir=profile_dir,
        expected_expectations_sha256=expected_hash,
        runtime_directory_env=body["runtime_directory_env"],
        java_command=body["java_command"],
        timeout_seconds=_bounded_float(body["timeout_seconds"], "$.timeout_seconds"),
        backends=backends,
    )


def resolve_formal_runtime(policy: FormalRuntimePolicy) -> FormalRuntimeResolved:
    """Resolve one administrator-configured formal-runtime directory safely.

    The large TLC and Apalache artifacts are CB formal dependencies, but not
    source payload.  Their install location is explicit and outside untrusted
    requests.  Their bytes and versions remain checked by ``formalcheck``.
    No developer-machine path is encoded in the product policy.
    """

    raw_directory = os.environ.get(policy.runtime_directory_env)
    if not raw_directory:
        raise FormalRuntimeUnavailable(
            f"set {policy.runtime_directory_env} to the installed formal-runtime directory"
        )
    configured_directory = Path(raw_directory)
    if not configured_directory.is_absolute():
        raise FormalRuntimeUnavailable(
            f"{policy.runtime_directory_env} must be an absolute directory"
        )
    try:
        runtime_directory = configured_directory.resolve(strict=True)
    except OSError as exc:
        raise FormalRuntimeUnavailable(
            f"configured formal-runtime directory is unavailable: {exc}"
        ) from exc
    if not runtime_directory.is_dir():
        raise FormalRuntimeUnavailable(
            "configured formal-runtime path is not a directory"
        )

    java_text = shutil.which(policy.java_command)
    if not java_text:
        raise FormalRuntimeUnavailable("java command is unavailable on PATH")
    try:
        java_executable = Path(java_text).resolve(strict=True)
    except OSError as exc:
        raise FormalRuntimeUnavailable("resolved java command is unavailable") from exc
    if not java_executable.is_file() or not os.access(java_executable, os.X_OK):
        raise FormalRuntimeUnavailable("resolved java command is not executable")

    checker_artifacts: dict[str, Path] = {}
    for backend_name, backend in policy.backends.items():
        candidate = runtime_directory / backend.checker_artifact_relative_path
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as exc:
            raise FormalRuntimeUnavailable(
                f"{backend_name} checker artifact is unavailable"
            ) from exc
        if (
            not resolved.is_file()
            or (resolved != runtime_directory and runtime_directory not in resolved.parents)
        ):
            raise FormalRuntimeUnavailable(
                f"{backend_name} checker artifact escaped or is absent from the configured runtime directory"
            )
        checker_artifacts[backend_name] = resolved
    return FormalRuntimeResolved(
        runtime_directory=runtime_directory,
        java_executable=java_executable,
        checker_artifacts=checker_artifacts,
    )


def _semantic_temporal_result(receipt: dict[str, Any]) -> dict[str, Any]:
    evidence = receipt.get("evidence")
    if not isinstance(evidence, dict):
        evidence = {}
    return {
        "backend": receipt.get("backend"),
        "status": receipt.get("status"),
        "disposition": receipt.get("disposition"),
        "reason": receipt.get("reason"),
        "controls": receipt.get("controls"),
        "positive_semantics": evidence.get("positive_semantics"),
        "mutation_semantics": evidence.get("mutation_semantics"),
        "post_run_hashes": evidence.get("post_run_hashes"),
    }


def run_temporal_pair() -> dict[str, Any]:
    """Run both controller-required offline checkers; no caller selects one."""

    try:
        policy = load_formal_runtime_policy()
    except FormalRegistryError as exc:
        return {
            "schema": "constraintbox.formal-pair-receipt.v1",
            "status": "DRIFT",
            "disposition": Disposition.BLOCKED.value,
            "reason": "formal_runtime_policy_invalid",
            "error": str(exc),
            "claim_ceiling": _PAIR_CLAIM_CEILING,
            "blocked_consumers": list(_PAIR_BLOCKED_CONSUMERS),
            "promotion_allowed": False,
        }
    try:
        runtime = resolve_formal_runtime(policy)
    except FormalRuntimeUnavailable as exc:
        return {
            "schema": "constraintbox.formal-pair-receipt.v1",
            "status": "UNAVAILABLE",
            "disposition": Disposition.PARKED.value,
            "reason": "formal_runtime_unavailable",
            "runtime_directory_env": policy.runtime_directory_env,
            "java_command": policy.java_command,
            "error": str(exc),
            "claim_ceiling": _PAIR_CLAIM_CEILING,
            "blocked_consumers": list(_PAIR_BLOCKED_CONSUMERS),
            "promotion_allowed": False,
        }

    results: dict[str, dict[str, Any]] = {}
    statuses: dict[str, FormalCheckStatus] = {}
    for backend_name in ("apalache", "tlc"):
        backend = policy.backends[backend_name]
        profile = TemporalCheckProfile(
            backend=backend_name,
            java_executable=runtime.java_executable,
            checker_artifact=runtime.checker_artifacts[backend_name],
            profile_dir=policy.profile_dir,
            expected_expectations_sha256=(
                policy.expected_expectations_sha256
            ),
            timeout_seconds=policy.timeout_seconds,
        )
        receipt: FormalCheckReceipt = run_temporal_check(profile)
        results[backend_name] = receipt.to_dict()
        statuses[backend_name] = receipt.status

    if all(status is FormalCheckStatus.PASSED for status in statuses.values()):
        status = "PASSED"
        disposition = Disposition.ELIGIBLE
        reason = "required_temporal_checkers_agree"
    elif any(
        status in {FormalCheckStatus.FAILED, FormalCheckStatus.DRIFT}
        for status in statuses.values()
    ):
        status = "FAILED"
        disposition = Disposition.BLOCKED
        reason = "required_temporal_checker_failed"
    else:
        status = "UNAVAILABLE"
        disposition = Disposition.PARKED
        reason = "required_temporal_checker_unavailable"

    semantic_results = {
        name: _semantic_temporal_result(receipt)
        for name, receipt in sorted(results.items())
    }
    return {
        "schema": "constraintbox.formal-pair-receipt.v1",
        "status": status,
        "disposition": disposition.value,
        "reason": reason,
        "required_backends": ["apalache", "tlc"],
        "runtime_policy_sha256": policy.policy_sha256,
        "semantic_results": semantic_results,
        "semantic_results_sha256": hashlib.sha256(
            canonical_json(semantic_results)
        ).hexdigest(),
        "backend_receipts": results,
        "claim_ceiling": _PAIR_CLAIM_CEILING,
        "blocked_consumers": list(_PAIR_BLOCKED_CONSUMERS),
        "promotion_allowed": False,
    }
