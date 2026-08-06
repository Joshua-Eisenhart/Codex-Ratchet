"""ConstraintBox proposed standalone runtime.

The package exposes operational tools only.  No result produced here is a
scientific truth verdict, absolute MSS result, or object-identity proof.
"""

from .applicability import ApplicabilityRegistry, CapabilityDemand
from .advisory_run import AdvisoryRunError, run_advisory_sidecar
from .branching import BranchLedger, MergeEvidence, PruneEvidence
from .constraints import FiniteConstraintProblem, SolverResult, SolverStatus
from .contracts import DecisionRecord, Disposition, TaskRequest
from .controller import (
    AgentProposalProfile,
    ConstraintBoxController,
    FiniteConstraintProfile,
    RegisteredWorkerProfile,
    StrictJsonProfile,
)
from .discharge import Check, Discharge, Observation, Policy, Requirement, discharge
from .ensemble import FiniteHistoryEnsemble
from .evidence import (
    DigestRoute,
    EvidenceError,
    EvidenceRef,
    EvidenceRoute,
    FileRoute,
    RefKind,
    RefStatus,
    RequiredReferenceManifest,
    RunSeal,
    SealFailedClosed,
    SealVerdict,
    SealVerification,
    build_required_manifest,
    observe,
    ref_from_dict,
    required_manifest_from_dict,
    route_table,
    seal_from_dict,
    seal_run,
    verify_seal,
)
from .external_capability import (
    CAPABILITY_ID,
    CapabilityBinding,
    ExternalCapabilityError,
    PytorchJacobianCapabilityBroker,
    derive_pytorch_challenge_case,
    validate_pytorch_capability_receipt,
)
from .external_capability_flow import (
    ExternalCapabilityFlowError,
    run_pytorch_capability_flow,
)
from .failure_repair import (
    FailureRepairError,
    build_repair_plan_from_capability_result,
    load_verified_repair_contract_for_run,
    verify_capability_result,
    write_repair_plan_for_run,
)
from .ledger import HashChainLedger
from .lev_eval_observation import (
    LevEvalObservation,
    LevEvalObservationBinding,
    LevEvalObservationError,
    LevEvalObservationHoldError,
    build_lev_eval_observation_binding,
    lev_eval_observer_profile_sha256,
    observe_lev_eval_bundle,
    verify_lev_eval_observation_snapshot,
)
from .lev_eval_observation_flow import (
    LevEvalObservationFlowError,
    LevEvalObservationFlowResult,
    build_lev_eval_observation_flow,
    load_lev_eval_observation_flow,
    run_lev_eval_observation_flow,
    verify_lev_eval_observation_flow,
)
from .lease import (
    LeaseDenied,
    LeaseError,
    Verdict,
    issue_lease,
    lease_digest,
    read_lease,
    staged_tree_id,
    verify_lease,
    verify_lease_file,
    write_lease,
)
from .formal_registry import (
    TASK_INTEGRATED_WORKLOAD_TRANSITION,
    TASK_LEVOS_FLOWMIND_GRAPH,
    TASK_PHASE_TRANSITION,
    TASK_SYMBOLIC_POLYNOMIAL,
    TASK_WORKFLOW_GRAPH,
    FormalRegistryError,
    FormalRuntimeBackend,
    FormalRuntimePolicy,
    build_formal_controller,
    formal_catalog,
    formal_task_kinds,
    formal_task_policy,
    load_formal_runtime_policy,
    run_formal_task,
    run_temporal_pair,
)
from .integrated_minilev import (
    IntegratedMiniLevError,
    run_integrated_receipt_lease,
)
from .formalcheck import (
    FormalCheckReceipt,
    FormalCheckStatus,
    TemporalCheckProfile,
    run_temporal_check,
)
from .maude_rewrite import MaudeTransitionProfile
from .mini_levos import (
    FlowNode,
    FlowPolicy,
    FlowTransition,
    HookKind,
    HookRegistration,
    HookResult,
    HookSignal,
    MiniLevError,
    MiniLevRuntime,
    handler_code_sha256,
    verify_flow_receipt,
)
from .numeric import NumpyAggregateProfile
from .python_runtime import (
    DEFAULT_PYTHON_RUNTIME_POLICY,
    PythonRuntimeError,
    PythonRuntimePolicy,
    capture_python_runtime,
    load_python_runtime_policy,
    python_runtime_policy_sha256,
    verify_python_runtime_stable,
)
from .ratchet import (
    ObservationBundle,
    RatchetCandidate,
    RatchetResult,
    derive_candidate,
    ratchet_frontier,
)
from .symbolic import SympyRationalPolynomialProfile
from .workflow_graph import WorkflowGraphProfile


# The integrated workload imports the external capability registry, which in
# turn imports every external adapter.  Eagerly loading it here meant that a
# worker invoked with ``python -m constraintbox.<adapter>`` could find its own
# module already present in ``sys.modules`` while ``runpy`` was trying to
# execute it.  That produced a RuntimeWarning on stderr and, correctly, the
# deterministic worker protocol rejected the run as unclean.  Keep the public
# root-level API, but defer this high-level orchestration import until someone
# actually requests it.  A capability worker must start with only the modules
# it explicitly imports.
_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "IntegratedWorkloadError": ("integrated_workload", "IntegratedWorkloadError"),
    "run_integrated_core_workload": (
        "integrated_workload",
        "run_integrated_core_workload",
    ),
}


def __getattr__(name: str):
    """Load high-level orchestration exports without polluting worker startup."""

    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    module = import_module(f".{target[0]}", __name__)
    value = getattr(module, target[1])
    globals()[name] = value
    return value

__all__ = [
    "AgentProposalProfile",
    "AdvisoryRunError",
    "ApplicabilityRegistry",
    "BranchLedger",
    "CapabilityDemand",
    "CapabilityBinding",
    "CAPABILITY_ID",
    "Check",
    "ConstraintBoxController",
    "DecisionRecord",
    "DigestRoute",
    "Discharge",
    "Disposition",
    "EvidenceError",
    "EvidenceRef",
    "EvidenceRoute",
    "ExternalCapabilityError",
    "ExternalCapabilityFlowError",
    "FailureRepairError",
    "FileRoute",
    "FiniteConstraintProblem",
    "FiniteConstraintProfile",
    "FiniteHistoryEnsemble",
    "FormalCheckReceipt",
    "FormalCheckStatus",
    "FormalRegistryError",
    "FormalRuntimeBackend",
    "FormalRuntimePolicy",
    "FlowNode",
    "FlowPolicy",
    "FlowTransition",
    "HashChainLedger",
    "HookKind",
    "HookRegistration",
    "HookResult",
    "HookSignal",
    "IntegratedMiniLevError",
    "IntegratedWorkloadError",
    "LeaseDenied",
    "LeaseError",
    "LevEvalObservation",
    "LevEvalObservationBinding",
    "LevEvalObservationError",
    "LevEvalObservationFlowError",
    "LevEvalObservationFlowResult",
    "LevEvalObservationHoldError",
    "MergeEvidence",
    "MaudeTransitionProfile",
    "MiniLevError",
    "MiniLevRuntime",
    "NumpyAggregateProfile",
    "Observation",
    "ObservationBundle",
    "Policy",
    "PruneEvidence",
    "PytorchJacobianCapabilityBroker",
    "PythonRuntimeError",
    "PythonRuntimePolicy",
    "RatchetCandidate",
    "RatchetResult",
    "RefKind",
    "RefStatus",
    "RequiredReferenceManifest",
    "RegisteredWorkerProfile",
    "Requirement",
    "RunSeal",
    "SealFailedClosed",
    "SealVerdict",
    "SealVerification",
    "SolverResult",
    "SolverStatus",
    "StrictJsonProfile",
    "SympyRationalPolynomialProfile",
    "TASK_INTEGRATED_WORKLOAD_TRANSITION",
    "TASK_LEVOS_FLOWMIND_GRAPH",
    "TASK_PHASE_TRANSITION",
    "TASK_SYMBOLIC_POLYNOMIAL",
    "TASK_WORKFLOW_GRAPH",
    "TaskRequest",
    "TemporalCheckProfile",
    "Verdict",
    "WorkflowGraphProfile",
    "DEFAULT_PYTHON_RUNTIME_POLICY",
    "build_formal_controller",
    "build_lev_eval_observation_binding",
    "build_lev_eval_observation_flow",
    "build_repair_plan_from_capability_result",
    "build_required_manifest",
    "capture_python_runtime",
    "derive_candidate",
    "derive_pytorch_challenge_case",
    "discharge",
    "issue_lease",
    "handler_code_sha256",
    "lease_digest",
    "load_formal_runtime_policy",
    "load_lev_eval_observation_flow",
    "load_verified_repair_contract_for_run",
    "load_python_runtime_policy",
    "lev_eval_observer_profile_sha256",
    "observe",
    "observe_lev_eval_bundle",
    "formal_catalog",
    "formal_task_kinds",
    "formal_task_policy",
    "ratchet_frontier",
    "read_lease",
    "ref_from_dict",
    "required_manifest_from_dict",
    "route_table",
    "run_formal_task",
    "run_integrated_core_workload",
    "run_integrated_receipt_lease",
    "run_advisory_sidecar",
    "run_lev_eval_observation_flow",
    "run_pytorch_capability_flow",
    "run_temporal_check",
    "run_temporal_pair",
    "seal_from_dict",
    "seal_run",
    "staged_tree_id",
    "verify_lease",
    "verify_lease_file",
    "verify_flow_receipt",
    "verify_lev_eval_observation_flow",
    "verify_lev_eval_observation_snapshot",
    "verify_capability_result",
    "verify_python_runtime_stable",
    "validate_pytorch_capability_receipt",
    "verify_seal",
    "write_repair_plan_for_run",
    "write_lease",
    "python_runtime_policy_sha256",
]
