"""Fixed, deterministic integration workload for ConstraintBox's core tools.

This is deliberately not an agent runner.  The only input is a bounded run
identifier and a new output directory.  The controller owns the stage order,
the solver formulation, the workflow graph, the symbolic expression, and the
Maude lifecycle.  An LLM can neither select a stage nor turn a non-pass into a
pass.

The external capability suite remains outside the CB kernel.  Its fresh
receipt is used here as a workload input: the controller derives a finite
obligation from every component and the three independent finite deciders must
agree before the remaining core instruments run.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from .capability_suite import RECEIPT_NAME as CAPABILITY_SUITE_RECEIPT
from .capability_suite import CapabilitySuiteError, run_capability_suite
from .crosscheck import CrossCheckResult, cross_check
from .formal_flow import FORMAL_FLOW_LEDGER, FORMAL_FLOW_RECEIPT, FormalFlowError
from .formal_registry import (
    TASK_INTEGRATED_WORKLOAD_TRANSITION,
    TASK_LEVOS_FLOWMIND_GRAPH,
    TASK_SYMBOLIC_POLYNOMIAL,
    TASK_WORKFLOW_GRAPH,
    run_formal_task,
    run_temporal_pair,
)
from .gate import GateError, run_gate
from .integrated_minilev import (
    IntegratedMiniLevError,
    run_integrated_receipt_lease,
)
from .intake import canonical_json


SCHEMA = "constraintbox.integrated-core-workload-receipt.v1"
RECEIPT_NAME = "integrated_core_workload_receipt.json"
_SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,95}")

_TOOL_RUN_ORDER = (
    "external_capability_suite",
    "z3_cvc5_enumeration_crosscheck",
    "maude_observe_suite",
    "maude_cross_check",
    "minilev_receipt_lease_gate",
    "maude_validate_lease",
    "rustworkx_workflow_gate",
    "maude_validate_workflow",
    "levos_flowmind_observation_gate",
    "maude_observe_levos_flowmind",
    "sympy_exact_gate",
    "maude_validate_symbolic",
    "tlc_apalache_temporal_pair",
    "maude_validate_temporal",
    "claimgate_control_gate",
    "maude_complete",
)


class IntegratedWorkloadError(ValueError):
    """The fixed workload could not establish its own local run boundary."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _write_new_json(path: Path, body: dict[str, Any]) -> None:
    """Write one canonical receipt without allowing a pre-existing overwrite."""

    if path.exists():
        raise IntegratedWorkloadError(f"refusing to overwrite existing artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_bytes(canonical_json(body) + b"\n")
        temporary.replace(path)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise IntegratedWorkloadError(f"could not persist {path.name}: {exc}") from exc


def _disposition(value: object) -> str:
    if hasattr(value, "value"):
        value = getattr(value, "value")
    return value if isinstance(value, str) else "HOLD"


def _terminal_from_stage(disposition: str) -> str:
    if disposition == "ELIGIBLE":
        return "ELIGIBLE"
    if disposition == "PARKED":
        return "PARKED"
    if disposition == "BLOCKED":
        return "BLOCKED"
    return "HOLD"


def _exit_code(disposition: str) -> int:
    return {
        "ELIGIBLE": 0,
        "BLOCKED": 1,
        "PARKED": 4,
    }.get(disposition, 5)


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _artifact(path: Path, root: Path) -> dict[str, str]:
    if not path.is_file():
        raise IntegratedWorkloadError(f"required child artifact is missing: {path}")
    return {"path": _relative(path, root), "sha256": _sha256_file(path)}


def _crosscheck_dict(result: CrossCheckResult) -> dict[str, Any]:
    return {
        "agreement": result.agreement,
        "reason": result.reason,
        "outcomes": [
            {
                "decider": outcome.decider,
                "status": outcome.status,
                "raw_verdict": outcome.raw_verdict,
                "normal_verdict": outcome.normal_verdict,
                "detail": outcome.detail,
            }
            for outcome in result.outcomes
        ],
    }


def _all_verdicts(result: CrossCheckResult, verdict: str) -> bool:
    return (
        result.agreement == "AGREE"
        and bool(result.outcomes)
        and all(
            outcome.status == "DECIDED" and outcome.normal_verdict == verdict
            for outcome in result.outcomes
        )
    )


def _suite_facts(receipt: dict[str, Any]) -> tuple[dict[str, list[int]], list[dict[str, Any]]]:
    """Extract one solver fact per actual capability component, fail closed."""

    if receipt.get("schema") != "constraintbox.capability-suite-receipt.v1":
        raise IntegratedWorkloadError("capability suite schema mismatch")
    components = receipt.get("components")
    if not isinstance(components, list) or not components:
        raise IntegratedWorkloadError("capability suite supplies no component rows")

    variables: dict[str, list[int]] = {}
    observations: list[dict[str, Any]] = []
    for index, component in enumerate(components):
        if not isinstance(component, dict):
            raise IntegratedWorkloadError("capability suite component is not an object")
        capability_id = component.get("capability_id")
        result = component.get("result")
        replay = component.get("independent_replay")
        if (
            not isinstance(capability_id, str)
            or not isinstance(result, dict)
            or not isinstance(replay, dict)
        ):
            raise IntegratedWorkloadError("capability suite component lacks bound result/replay")
        eligible = (
            component.get("state") == "ELIGIBLE"
            and result.get("disposition") == "ELIGIBLE"
            and replay.get("disposition") == "ELIGIBLE"
        )
        variable = f"component_{index:02d}"
        variables[variable] = [1 if eligible else 0]
        observations.append(
            {
                "variable": variable,
                "capability_id": capability_id,
                "eligible_from_receipt": eligible,
                "component_result_sha256": component.get("result_sha256"),
                "independent_replay_sha256": component.get(
                    "independent_replay_sha256"
                ),
            }
        )
    return variables, observations


def _finite_obligation(variables: dict[str, list[int]]) -> dict[str, Any]:
    if not variables:
        raise IntegratedWorkloadError("finite obligation needs at least one component")
    return {
        "variables": variables,
        "constraints": [
            {
                "op": "eq",
                "left": {"var": name},
                "right": {"const": 1},
            }
            for name in sorted(variables)
        ],
    }


def _erased_obligation(variables: dict[str, list[int]]) -> dict[str, Any]:
    """A fixed wrong-structure control that must flip all three deciders."""

    erased = {name: list(values) for name, values in variables.items()}
    erased[sorted(erased)[0]] = [0]
    return _finite_obligation(erased)


def _formal_stage(
    *,
    root: Path,
    request_id: str,
    name: str,
    task_kind: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    run_dir = root / "formal" / name
    decision = run_formal_task(
        task_kind=task_kind,
        request_id=request_id,
        payload=canonical_json(payload),
        run_root=run_dir,
    )
    return {
        "stage": name,
        "task_kind": task_kind,
        "disposition": _disposition(decision.disposition),
        "reason": decision.reason,
        "decision": decision.to_dict(),
        "input_sha256": _sha256_bytes(canonical_json(payload)),
        "formal_flow_receipt": _artifact(run_dir / FORMAL_FLOW_RECEIPT, root),
        "formal_flow_ledger": _artifact(run_dir / FORMAL_FLOW_LEDGER, root),
    }


def _transition_stage(
    *,
    root: Path,
    request_id: str,
    sequence: int,
    source: str,
    action: str,
    target: str,
) -> dict[str, Any]:
    return _formal_stage(
        root=root,
        request_id=f"{request_id}-transition-{sequence:02d}",
        name=f"{sequence:02d}_maude_{action}",
        task_kind=TASK_INTEGRATED_WORKLOAD_TRANSITION,
        payload={
            "from_state": source,
            "action": action,
            "to_state": target,
        },
    )


def _workflow_payload(suite_receipt_sha256: str) -> dict[str, Any]:
    suite_node = f"suite_{suite_receipt_sha256[:16]}"
    nodes = sorted(
        (
            "intake",
            suite_node,
            "smt_crosschecked",
            "lease_validated",
            "workflow_validated",
            "levos_flowmind_observed",
            "symbolic_validated",
            "temporal_validated",
            "proposal_ready",
        )
    )
    edges = sorted(
        (
            ["intake", suite_node],
            [suite_node, "smt_crosschecked"],
            ["smt_crosschecked", "lease_validated"],
            ["lease_validated", "workflow_validated"],
            ["workflow_validated", "levos_flowmind_observed"],
            ["levos_flowmind_observed", "symbolic_validated"],
            ["symbolic_validated", "temporal_validated"],
            ["temporal_validated", "proposal_ready"],
        )
    )
    return {"nodes": nodes, "edges": edges}


def _pinned_levos_flowmind_observation() -> tuple[dict[str, Any], str]:
    """Load the bundled, non-authoritative Lev DNA.compile observation.

    The input is deliberately a pinned fixture rather than a live Lev command.
    It exercises the CB Mini-Lev/Rustworkx adapter as a contained structural
    test and must never be described as a current LevOS execution result.
    """

    path = (
        Path(__file__).resolve().parents[2]
        / "fixtures"
        / "formal"
        / "levos_flowmind_dna_compile_pinned_topology_fixture.json"
    )
    try:
        raw = path.read_bytes()
        body = json.loads(raw)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise IntegratedWorkloadError(
            "bundled Lev FlowMind observation is unavailable or invalid"
        ) from exc
    if not isinstance(body, dict):
        raise IntegratedWorkloadError("bundled Lev FlowMind observation is not an object")
    return body, _sha256_bytes(raw)


def _symbolic_payload(eligible_count: int, component_count: int) -> dict[str, Any]:
    # Both quantities were derived from the suite receipt.  The profile accepts
    # typed rationals only; it never evaluates model-provided SymPy text.
    coefficients = [
        {"degree": 0, "numerator": eligible_count, "denominator": 1},
        {"degree": 1, "numerator": component_count, "denominator": 1},
    ]
    if eligible_count == 0:
        coefficients = coefficients[1:]
    return {"coefficients": coefficients, "claimed_canonical": coefficients}


def _claim_gate_control(root: Path) -> dict[str, Any]:
    """Exercise ClaimGate without pretending it admits the external workload.

    ClaimGate's current evaluator-owned registry has no binding for this
    workload receipt family.  A claimless ``field_only`` control therefore
    proves that the local ClaimGate chain runs, while the parent receipt keeps
    its independent sim-evidence and no-release ceiling.
    """

    control = {
        "classification": "scratch_diagnostic",
        "claim_kind": "field_only",
        "produced_by": "constraintbox_integrated_workload",
    }
    input_path = root / "claimgate_control_input.json"
    _write_new_json(input_path, control)
    try:
        result = run_gate(input_path)
    except GateError as exc:
        return {
            "stage": "claimgate_control_gate",
            "disposition": "HOLD",
            "reason": "claimgate_execution_error",
            "error": str(exc),
            "control_input": _artifact(input_path, root),
            "role": "ClaimGate chain health control only; no sim admission",
        }
    return {
        "stage": "claimgate_control_gate",
        "disposition": "ELIGIBLE" if result.get("disposition") == "ADMITTED" else "BLOCKED",
        "reason": "claimgate_claimless_control_admitted"
        if result.get("disposition") == "ADMITTED"
        else "claimgate_claimless_control_not_admitted",
        "control_input": _artifact(input_path, root),
        "gate_result": result,
        "role": "ClaimGate chain health control only; no sim admission",
    }


def _finish(
    *,
    root: Path,
    request_id: str,
    disposition: str,
    reason: str,
    stages: list[dict[str, Any]],
    suite_receipt: dict[str, Any] | None,
    suite_artifact: dict[str, str] | None,
    observations: list[dict[str, Any]] | None,
) -> tuple[dict[str, Any], int]:
    receipt = {
        "schema": SCHEMA,
        "request_id": request_id,
        "disposition": disposition,
        "reason": reason,
        "accepted_status_label": "passes local rerun"
        if disposition == "ELIGIBLE"
        else "runs",
        "controller_selected_order": list(_TOOL_RUN_ORDER),
        "llm_decision_authority": False,
        "llm_input_used": False,
        "controller_only_stage_selection": True,
        "external_workload": {
            "name": "constraintbox.capability-suite",
            "outside_cb_kernel": True,
            "receipt": suite_artifact,
            "reported_disposition": suite_receipt.get("disposition")
            if suite_receipt is not None
            else None,
            "component_observations": observations,
        },
        "stages": stages,
        "claim_gate_linked_to_sim_admission": False,
        "release_allowed": False,
        "promotion_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "claim_ceiling": (
            "one fixed local workload ran real external capability profiles and "
            "the named CB core instruments, including a Mini-LevOS leased hook, "
            "and one bundled Lev FlowMind observation, under controller-owned "
            "order; it does not establish that the FlowMind input is a current "
            "LevOS execution; it also does not establish full sim-estate "
            "coverage, runtime portability, "
            "ClaimGate admission of the sim receipt, temporal-model conformance "
            "to Python, scientific/CR truth, or release permission"
        ),
        "source_sha256": _sha256_file(Path(__file__)),
    }
    _write_new_json(root / RECEIPT_NAME, receipt)
    return receipt, _exit_code(disposition)


def run_integrated_core_workload(
    *,
    request_id: str,
    run_root: Path,
) -> tuple[dict[str, Any], int]:
    """Run the one fixed high-assurance integration workload.

    ``run_root`` must be a new absolute directory.  No caller can substitute a
    component, SMT formula, workflow topology, formal task, state transition,
    or ClaimGate policy.
    """

    if not isinstance(request_id, str) or _SAFE_REQUEST_ID.fullmatch(request_id) is None:
        raise IntegratedWorkloadError("request_id must be one bounded safe identifier")
    if not isinstance(run_root, Path) or not run_root.is_absolute():
        raise IntegratedWorkloadError("run_root must be one absolute pathlib.Path")
    try:
        run_root.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise IntegratedWorkloadError(
            f"integrated workload run directory must be new: {exc}"
        ) from exc

    stages: list[dict[str, Any]] = []
    suite_receipt: dict[str, Any] | None = None
    suite_artifact: dict[str, str] | None = None
    observations: list[dict[str, Any]] | None = None
    try:
        suite_root = run_root / "01_external_capability_suite"
        suite_receipt, suite_exit = run_capability_suite(
            request_id=f"{request_id}-suite",
            run_root=suite_root,
        )
        suite_path = suite_root / CAPABILITY_SUITE_RECEIPT
        suite_artifact = _artifact(suite_path, run_root)
        stages.append(
            {
                "stage": "external_capability_suite",
                "disposition": _disposition(suite_receipt.get("disposition")),
                "reason": suite_receipt.get("reason"),
                "exit_code": suite_exit,
                "receipt": suite_artifact,
            }
        )
        variables, observations = _suite_facts(suite_receipt)
        real_claim = _finite_obligation(variables)
        erased_claim = _erased_obligation(variables)
        real_result = cross_check("finite_constraint_satisfiability", real_claim)
        erased_result = cross_check("finite_constraint_satisfiability", erased_claim)
        smt_path = run_root / "02_smt_crosscheck.json"
        smt_record = {
            "schema": "constraintbox.integrated-smt-crosscheck.v1",
            "suite_receipt": suite_artifact,
            "component_observations": observations,
            "real_obligation": real_claim,
            "real_result": _crosscheck_dict(real_result),
            "erased_component_control": erased_claim,
            "erased_component_result": _crosscheck_dict(erased_result),
            "real_expected": "SAT",
            "erased_expected": "UNSAT",
        }
        _write_new_json(smt_path, smt_record)
        smt_ok = _all_verdicts(real_result, "SAT") and _all_verdicts(
            erased_result, "UNSAT"
        )
        stages.append(
            {
                "stage": "z3_cvc5_enumeration_crosscheck",
                "disposition": "ELIGIBLE" if smt_ok else "BLOCKED",
                "reason": "real_sat_and_erased_control_unsat"
                if smt_ok
                else "solver_crosscheck_or_erasure_control_failed",
                "receipt": _artifact(smt_path, run_root),
            }
        )
        # A failed external component is not allowed to bypass the formal
        # deciders.  Its receipt-derived variable is fixed to zero, so all
        # three paths must reject the same all-components obligation before the
        # controller stops.  A structurally invalid suite instead fails closed
        # in _suite_facts above.
        if suite_receipt.get("disposition") != "ELIGIBLE" or suite_exit != 0:
            return _finish(
                root=run_root,
                request_id=request_id,
                disposition=_terminal_from_stage(_disposition(suite_receipt.get("disposition"))),
                reason="external_capability_suite_not_eligible",
                stages=stages,
                suite_receipt=suite_receipt,
                suite_artifact=suite_artifact,
                observations=observations,
            )
        if not smt_ok:
            return _finish(
                root=run_root,
                request_id=request_id,
                disposition="BLOCKED",
                reason="solver_crosscheck_or_erasure_control_failed",
                stages=stages,
                suite_receipt=suite_receipt,
                suite_artifact=suite_artifact,
                observations=observations,
            )

        transition = _transition_stage(
            root=run_root,
            request_id=request_id,
            sequence=3,
            source="received",
            action="observe_suite",
            target="suite_observed",
        )
        stages.append({**transition, "stage": "maude_observe_suite"})
        if transition["disposition"] != "ELIGIBLE":
            return _finish(
                root=run_root,
                request_id=request_id,
                disposition=_terminal_from_stage(transition["disposition"]),
                reason="maude_observe_suite_not_eligible",
                stages=stages,
                suite_receipt=suite_receipt,
                suite_artifact=suite_artifact,
                observations=observations,
            )

        transition = _transition_stage(
            root=run_root,
            request_id=request_id,
            sequence=4,
            source="suite_observed",
            action="cross_check",
            target="smt_crosschecked",
        )
        stages.append({**transition, "stage": "maude_cross_check"})
        if transition["disposition"] != "ELIGIBLE":
            return _finish(
                root=run_root,
                request_id=request_id,
                disposition=_terminal_from_stage(transition["disposition"]),
                reason="maude_cross_check_not_eligible",
                stages=stages,
                suite_receipt=suite_receipt,
                suite_artifact=suite_artifact,
                observations=observations,
            )

        lease = run_integrated_receipt_lease(
            run_root=run_root / "05_minilev_receipt_lease",
            request_id=f"{request_id}-lease",
            suite_receipt_sha256=suite_artifact["sha256"],
            smt_crosscheck_sha256=_sha256_file(smt_path),
        )
        lease_path = run_root / "05_minilev_receipt_lease.json"
        _write_new_json(lease_path, lease)
        stages.append(
            {
                "stage": "minilev_receipt_lease_gate",
                "disposition": _disposition(lease.get("disposition")),
                "reason": lease.get("reason"),
                "receipt": _artifact(lease_path, run_root),
            }
        )
        if lease.get("disposition") != "ELIGIBLE":
            return _finish(
                root=run_root,
                request_id=request_id,
                disposition=_terminal_from_stage(_disposition(lease.get("disposition"))),
                reason="minilev_receipt_lease_not_eligible",
                stages=stages,
                suite_receipt=suite_receipt,
                suite_artifact=suite_artifact,
                observations=observations,
            )

        transition = _transition_stage(
            root=run_root,
            request_id=request_id,
            sequence=6,
            source="smt_crosschecked",
            action="validate_lease",
            target="lease_validated",
        )
        stages.append({**transition, "stage": "maude_validate_lease"})
        if transition["disposition"] != "ELIGIBLE":
            return _finish(
                root=run_root,
                request_id=request_id,
                disposition=_terminal_from_stage(transition["disposition"]),
                reason="maude_validate_lease_not_eligible",
                stages=stages,
                suite_receipt=suite_receipt,
                suite_artifact=suite_artifact,
                observations=observations,
            )

        workflow = _formal_stage(
            root=run_root,
            request_id=f"{request_id}-workflow",
            name="07_rustworkx_workflow",
            task_kind=TASK_WORKFLOW_GRAPH,
            payload=_workflow_payload(suite_artifact["sha256"]),
        )
        stages.append({**workflow, "stage": "rustworkx_workflow_gate"})
        if workflow["disposition"] != "ELIGIBLE":
            return _finish(
                root=run_root,
                request_id=request_id,
                disposition=_terminal_from_stage(workflow["disposition"]),
                reason="rustworkx_workflow_gate_not_eligible",
                stages=stages,
                suite_receipt=suite_receipt,
                suite_artifact=suite_artifact,
                observations=observations,
            )

        transition = _transition_stage(
            root=run_root,
            request_id=request_id,
            sequence=8,
            source="lease_validated",
            action="validate_workflow",
            target="workflow_validated",
        )
        stages.append({**transition, "stage": "maude_validate_workflow"})
        if transition["disposition"] != "ELIGIBLE":
            return _finish(
                root=run_root,
                request_id=request_id,
                disposition=_terminal_from_stage(transition["disposition"]),
                reason="maude_validate_workflow_not_eligible",
                stages=stages,
                suite_receipt=suite_receipt,
                suite_artifact=suite_artifact,
                observations=observations,
            )

        levos_payload, levos_fixture_sha256 = _pinned_levos_flowmind_observation()
        levos_flowmind = _formal_stage(
            root=run_root,
            request_id=f"{request_id}-levos-flowmind",
            name="09_levos_flowmind_observation",
            task_kind=TASK_LEVOS_FLOWMIND_GRAPH,
            payload=levos_payload,
        )
        stages.append(
            {
                **levos_flowmind,
                "stage": "levos_flowmind_observation_gate",
                "input_role": (
                    "bundled pinned foreign Lev DNA.compile observation; "
                    "not a live LevOS execution"
                ),
                "source_fixture_sha256": levos_fixture_sha256,
            }
        )
        if levos_flowmind["disposition"] != "ELIGIBLE":
            return _finish(
                root=run_root,
                request_id=request_id,
                disposition=_terminal_from_stage(levos_flowmind["disposition"]),
                reason="levos_flowmind_observation_not_eligible",
                stages=stages,
                suite_receipt=suite_receipt,
                suite_artifact=suite_artifact,
                observations=observations,
            )

        transition = _transition_stage(
            root=run_root,
            request_id=request_id,
            sequence=10,
            source="workflow_validated",
            action="observe_levos_flowmind",
            target="levos_observed",
        )
        stages.append({**transition, "stage": "maude_observe_levos_flowmind"})
        if transition["disposition"] != "ELIGIBLE":
            return _finish(
                root=run_root,
                request_id=request_id,
                disposition=_terminal_from_stage(transition["disposition"]),
                reason="maude_observe_levos_flowmind_not_eligible",
                stages=stages,
                suite_receipt=suite_receipt,
                suite_artifact=suite_artifact,
                observations=observations,
            )

        symbolic = _formal_stage(
            root=run_root,
            request_id=f"{request_id}-symbolic",
            name="11_sympy_exact",
            task_kind=TASK_SYMBOLIC_POLYNOMIAL,
            payload=_symbolic_payload(
                sum(values[0] for values in variables.values()),
                len(variables),
            ),
        )
        stages.append({**symbolic, "stage": "sympy_exact_gate"})
        if symbolic["disposition"] != "ELIGIBLE":
            return _finish(
                root=run_root,
                request_id=request_id,
                disposition=_terminal_from_stage(symbolic["disposition"]),
                reason="sympy_exact_gate_not_eligible",
                stages=stages,
                suite_receipt=suite_receipt,
                suite_artifact=suite_artifact,
                observations=observations,
            )

        transition = _transition_stage(
            root=run_root,
            request_id=request_id,
            sequence=12,
            source="levos_observed",
            action="validate_symbolic",
            target="symbolic_validated",
        )
        stages.append({**transition, "stage": "maude_validate_symbolic"})
        if transition["disposition"] != "ELIGIBLE":
            return _finish(
                root=run_root,
                request_id=request_id,
                disposition=_terminal_from_stage(transition["disposition"]),
                reason="maude_validate_symbolic_not_eligible",
                stages=stages,
                suite_receipt=suite_receipt,
                suite_artifact=suite_artifact,
                observations=observations,
            )

        temporal = run_temporal_pair()
        temporal_path = run_root / "13_temporal_pair.json"
        _write_new_json(temporal_path, temporal)
        temporal_disposition = _disposition(temporal.get("disposition"))
        stages.append(
            {
                "stage": "tlc_apalache_temporal_pair",
                "disposition": temporal_disposition,
                "reason": temporal.get("reason"),
                "receipt": _artifact(temporal_path, run_root),
            }
        )
        if temporal_disposition != "ELIGIBLE":
            return _finish(
                root=run_root,
                request_id=request_id,
                disposition=_terminal_from_stage(temporal_disposition),
                reason="temporal_pair_not_eligible",
                stages=stages,
                suite_receipt=suite_receipt,
                suite_artifact=suite_artifact,
                observations=observations,
            )

        transition = _transition_stage(
            root=run_root,
            request_id=request_id,
            sequence=14,
            source="symbolic_validated",
            action="check_temporal",
            target="temporal_validated",
        )
        stages.append({**transition, "stage": "maude_validate_temporal"})
        if transition["disposition"] != "ELIGIBLE":
            return _finish(
                root=run_root,
                request_id=request_id,
                disposition=_terminal_from_stage(transition["disposition"]),
                reason="maude_validate_temporal_not_eligible",
                stages=stages,
                suite_receipt=suite_receipt,
                suite_artifact=suite_artifact,
                observations=observations,
            )

        claim_gate = _claim_gate_control(run_root)
        stages.append(claim_gate)
        if claim_gate["disposition"] != "ELIGIBLE":
            return _finish(
                root=run_root,
                request_id=request_id,
                disposition=_terminal_from_stage(claim_gate["disposition"]),
                reason="claimgate_control_not_eligible",
                stages=stages,
                suite_receipt=suite_receipt,
                suite_artifact=suite_artifact,
                observations=observations,
            )

        transition = _transition_stage(
            root=run_root,
            request_id=request_id,
            sequence=16,
            source="temporal_validated",
            action="complete",
            target="complete",
        )
        stages.append({**transition, "stage": "maude_complete"})
        if transition["disposition"] != "ELIGIBLE":
            return _finish(
                root=run_root,
                request_id=request_id,
                disposition=_terminal_from_stage(transition["disposition"]),
                reason="maude_complete_not_eligible",
                stages=stages,
                suite_receipt=suite_receipt,
                suite_artifact=suite_artifact,
                observations=observations,
            )

        return _finish(
            root=run_root,
            request_id=request_id,
            disposition="ELIGIBLE",
            reason="all_fixed_external_and_core_instruments_eligible",
            stages=stages,
            suite_receipt=suite_receipt,
            suite_artifact=suite_artifact,
            observations=observations,
        )
    except (
        CapabilitySuiteError,
        FormalFlowError,
        IntegratedMiniLevError,
        IntegratedWorkloadError,
        OSError,
        ValueError,
    ) as exc:
        stages.append(
            {
                "stage": "controller_exception",
                "disposition": "HOLD",
                "reason": "integrated_workload_exception",
                "exception_type": type(exc).__name__,
                "error": str(exc),
            }
        )
        return _finish(
            root=run_root,
            request_id=request_id,
            disposition="HOLD",
            reason="integrated_workload_exception",
            stages=stages,
            suite_receipt=suite_receipt,
            suite_artifact=suite_artifact,
            observations=observations,
        )
