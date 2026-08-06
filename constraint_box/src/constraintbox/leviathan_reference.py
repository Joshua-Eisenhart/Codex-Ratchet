"""Bounded Leviathan reference observations for the CB-native Mini-Lev kernel.

This module deliberately does *not* embed Leviathan, FlowMind, a provider, or
an LLM in ConstraintBox.  It extracts a small useful contract from Lev's
``exec-validate`` flow instead:

* an admitted, sealed run has an intent reference and bounded retry policy;
* a tool observation precedes a deterministic gate;
* a failed gate may retry only a bounded number of times; and
* a positive terminal follows an independently recorded gate path.

The default conformance run is pure Python and CB-native.  The optional
``run_leviathan_dry_run_comparison`` function launches Lev with ``--dry-run``
under a fresh XDG root, so it never invokes a model or provider.  Lev is an
external reference observer there, never an authority over CB decisions.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .intake import canonical_json
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
)


SCHEMA = "constraintbox.leviathan-minilev-conformance.v1"
EXTERNAL_SCHEMA = "constraintbox.leviathan-dry-run-comparison.v1"
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_SHA256 = hashlib.sha256
_SOURCE_PATH = Path(__file__).resolve()
_SOURCE_SHA256 = _SHA256(_SOURCE_PATH.read_bytes()).hexdigest()
_LEV_FLOW_RELATIVE_PATH = Path("plugins/sdlc/flows/exec-validate.flow.yaml")
_LEV_REFERENCE_FLOW_NAME = "sdlc-exec-validate"
_LEV_REFERENCE_NODE_ORDER = ("exec", "validate", "escalate", "emit", "done")


class LeviathanReferenceError(RuntimeError):
    """A reference observation or fixed CB conformance flow was invalid."""


def _safe_id(value: str, name: str) -> str:
    if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
        raise LeviathanReferenceError(f"{name} must be one safe identifier")
    return value


def _new_root(path: Path, name: str) -> Path:
    root = Path(path).expanduser()
    if not root.is_absolute():
        raise LeviathanReferenceError(f"{name} must be absolute")
    if root.exists():
        raise LeviathanReferenceError(f"{name} must not already exist")
    root.mkdir(parents=True)
    return root.resolve()


def _registration(
    *,
    hook_id: str,
    kind: HookKind,
    handler: Any,
    allowed_signals: tuple[HookSignal, ...],
    allowed_update_keys: tuple[str, ...] = (),
) -> HookRegistration:
    return HookRegistration(
        hook_id=hook_id,
        kind=kind,
        handler=handler,
        source_path=_SOURCE_PATH,
        source_sha256=_SOURCE_SHA256,
        code_sha256=handler_code_sha256(handler),
        allowed_signals=allowed_signals,
        allowed_update_keys=allowed_update_keys,
    )


def _execute_tool(context: dict[str, Any]) -> HookResult:
    count = int(context.get("exec_count", 0)) + 1
    return HookResult(
        HookSignal.OBSERVED,
        {"execution_round": count},
        {"exec_count": count},
    )


def _validate_gate(context: dict[str, Any]) -> HookResult:
    scenario = context.get("scenario")
    count = int(context.get("validation_count", 0)) + 1
    if scenario == "success_after_retry":
        signal = HookSignal.RETRY if count == 1 else HookSignal.PASS
    elif scenario == "retry_exhausted":
        signal = HookSignal.RETRY
    else:
        return HookResult(HookSignal.BLOCKED, {"scenario_valid": False})
    return HookResult(
        signal,
        {"validation_round": count, "scenario_valid": True},
        {"validation_count": count},
    )


def _emit_tool(context: dict[str, Any]) -> HookResult:
    return HookResult(
        HookSignal.OBSERVED,
        {
            "execution_rounds": int(context.get("exec_count", 0)),
            "validation_rounds": int(context.get("validation_count", 0)),
        },
        {"emitted": True},
    )


def _seal_gate(context: dict[str, Any]) -> HookResult:
    return HookResult(
        HookSignal.PASS if context.get("emitted") is True else HookSignal.BLOCKED,
        {"receipt_ready": context.get("emitted") is True},
    )


def _policy() -> tuple[FlowPolicy, tuple[HookRegistration, ...]]:
    """Build the fixed, provider-free analogue of Lev's exec-validate flow."""

    registrations = (
        _registration(
            hook_id="lev-reference-execute-tool",
            kind=HookKind.TOOL,
            handler=_execute_tool,
            allowed_signals=(HookSignal.OBSERVED,),
            allowed_update_keys=("exec_count",),
        ),
        _registration(
            hook_id="lev-reference-validate-gate",
            kind=HookKind.GATE,
            handler=_validate_gate,
            allowed_signals=(
                HookSignal.PASS,
                HookSignal.RETRY,
                HookSignal.BLOCKED,
            ),
            allowed_update_keys=("validation_count",),
        ),
        _registration(
            hook_id="lev-reference-emit-tool",
            kind=HookKind.TOOL,
            handler=_emit_tool,
            allowed_signals=(HookSignal.OBSERVED,),
            allowed_update_keys=("emitted",),
        ),
        _registration(
            hook_id="lev-reference-seal-gate",
            kind=HookKind.GATE,
            handler=_seal_gate,
            allowed_signals=(HookSignal.PASS, HookSignal.BLOCKED),
        ),
    )
    policy = FlowPolicy(
        flow_id="leviathan-exec-validate-reference-v1",
        entry_node="execute",
        nodes=(
            FlowNode("execute", "lev-reference-execute-tool"),
            FlowNode("validate", "lev-reference-validate-gate"),
            FlowNode("emit", "lev-reference-emit-tool"),
            FlowNode("seal", "lev-reference-seal-gate"),
        ),
        transitions=(
            FlowTransition("execute", HookSignal.OBSERVED, "validate"),
            FlowTransition("execute", HookSignal.HOLD, "HOLD"),
            FlowTransition("validate", HookSignal.PASS, "emit"),
            FlowTransition("validate", HookSignal.RETRY, "execute"),
            FlowTransition("validate", HookSignal.BLOCKED, "BLOCKED"),
            FlowTransition("validate", HookSignal.HOLD, "HOLD"),
            FlowTransition("emit", HookSignal.OBSERVED, "seal"),
            FlowTransition("emit", HookSignal.HOLD, "HOLD"),
            FlowTransition("seal", HookSignal.PASS, "ELIGIBLE"),
            FlowTransition("seal", HookSignal.BLOCKED, "BLOCKED"),
            FlowTransition("seal", HookSignal.HOLD, "HOLD"),
        ),
        terminal_nodes=("ELIGIBLE", "BLOCKED", "HOLD"),
        required_nodes=("execute", "validate", "emit", "seal"),
        max_steps=12,
        max_visits_per_node=4,
        max_retries=2,
        max_context_bytes=8_192,
        max_event_bytes=16_384,
        max_receipt_bytes=262_144,
        claim_ceiling=(
            "one fixed CB-native conformance flow for Lev exec-validate "
            "control semantics; not Lev equivalence, agent authority, provider "
            "execution, user authorization, release, or promotion"
        ),
    )
    return policy, registrations


def _run_scenario(root: Path, request_id: str, scenario: str) -> dict[str, Any]:
    policy, registrations = _policy()
    runtime = MiniLevRuntime(
        policy,
        registrations,
        run_id=f"{request_id}-{scenario}",
        ledger_path=root / "flow.jsonl",
    )
    return runtime.run({"scenario": scenario})


def _receipt_summary(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "terminal": receipt["terminal"],
        "steps": receipt["steps"],
        "retries": receipt["retries"],
        "completed_nodes": receipt["completed_nodes"],
        "receipt_sha256": receipt["receipt_sha256"],
        "retained_head_sha256": receipt["ledger"]["retained_head_sha256"],
    }


def _node_blocks_from_lev_flow(source: str) -> tuple[tuple[str, ...], dict[str, str]]:
    """Extract only the fixed node section needed for this reference.

    This deliberately is not a generic YAML parser.  The adapter observes one
    named Lev flow and fails closed if its narrow, indentation-sensitive shape
    changes.  Pulling a general flow authoring surface into CB would blur the
    product boundary and give unreviewed flow text more authority than it has.
    """

    nodes_marker = re.search(r"(?m)^nodes:\s*$", source)
    if nodes_marker is None:
        return (), {}
    section = source[nodes_marker.end() :]
    headings = list(re.finditer(r"(?m)^  ([A-Za-z][A-Za-z0-9_-]*):\s*$", section))
    if not headings:
        return (), {}
    order: list[str] = []
    blocks: dict[str, str] = {}
    for index, heading in enumerate(headings):
        node_id = heading.group(1)
        end = headings[index + 1].start() if index + 1 < len(headings) else len(section)
        if node_id in blocks:
            return (), {}
        order.append(node_id)
        blocks[node_id] = section[heading.end() : end]
    return tuple(order), blocks


def _has_flow_line(block: str, key: str, value: str, *, indent: int = 4) -> bool:
    return re.search(
        rf"(?m)^{' ' * indent}{re.escape(key)}:\s*{re.escape(value)}\s*$",
        block,
    ) is not None


def observe_lev_exec_validate_flow(flow_path: Path) -> dict[str, Any]:
    """Read the narrow source-level control shape used as the Lev reference.

    The observation establishes only a fixed graph shape.  In particular, Lev
    still declares both ``exec`` and ``validate`` as ``lev.exec`` operations;
    CB's deterministic ``GATE`` is a deliberate stronger replacement, not a
    claim that Lev's validation node has deterministic authority.
    """

    path = Path(flow_path)
    try:
        raw = path.read_bytes()
        source = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return {
            "valid": False,
            "reason": f"flow source read failed: {type(exc).__name__}: {exc}",
            "checks": {},
        }
    if len(raw) > 262_144:
        return {
            "valid": False,
            "reason": "reference flow exceeds the observation size limit",
            "checks": {},
        }

    node_order, blocks = _node_blocks_from_lev_flow(source)
    validate = blocks.get("validate", "")
    checks = {
        "name": re.search(
            rf"(?m)^name:\s*{_LEV_REFERENCE_FLOW_NAME}\s*$", source
        )
        is not None,
        "entry": re.search(r"(?m)^entry:\s*exec\s*$", source) is not None,
        "node_order": node_order == _LEV_REFERENCE_NODE_ORDER,
        "exec_operation": _has_flow_line(blocks.get("exec", ""), "op", "lev.exec"),
        "exec_to_validate": _has_flow_line(blocks.get("exec", ""), "next", "validate"),
        "validate_operation": _has_flow_line(validate, "op", "lev.exec"),
        "validate_pass_to_emit": _has_flow_line(validate, "pass", "emit", indent=6),
        "validate_fail_to_exec": _has_flow_line(validate, "fail", "exec", indent=6),
        "validate_has_retry_bound": re.search(
            r"(?m)^    max_iterations:\s*\S.*$", validate
        )
        is not None,
        "validate_timeout_to_escalate": _has_flow_line(validate, "on_timeout", "escalate"),
        "emit_to_done": _has_flow_line(blocks.get("emit", ""), "next", "done"),
        "escalate_to_done": _has_flow_line(blocks.get("escalate", ""), "next", "done"),
        "done_terminal": _has_flow_line(blocks.get("done", ""), "terminal", "true"),
    }
    valid = all(checks.values())
    return {
        "valid": valid,
        "reason": "valid_lev_exec_validate_shape" if valid else "lev_exec_validate_shape_mismatch",
        "source_sha256": _SHA256(raw).hexdigest(),
        "checks": checks,
        "observed_structure": {
            "normal_path": ["exec", "validate", "emit", "done"],
            "retry_edge": ["validate", "exec"],
            "timeout_path": ["validate", "escalate", "done"],
            "validate_operation": "lev.exec",
            "authority_note": (
                "Lev validate is an external lev.exec operation; CB does not "
                "treat it as a deterministic gate"
            ),
        },
    }


def _cb_reference_structure(result: dict[str, Any]) -> dict[str, Any]:
    """Verify the fixed CB analogue before comparing it with Lev's shape."""

    policy, registrations = _policy()
    hook_kind_by_id = {registration.hook_id: registration.kind.value for registration in registrations}
    node_kind_by_id = {
        node.node_id: hook_kind_by_id.get(node.hook_id)
        for node in policy.nodes
    }
    transition_set = {
        (transition.from_node, transition.signal.value, transition.to_node)
        for transition in policy.transitions
    }
    checks = {
        "entry_execute": policy.entry_node == "execute",
        "node_order": tuple(node.node_id for node in policy.nodes)
        == ("execute", "validate", "emit", "seal"),
        "tool_then_gate": (
            node_kind_by_id.get("execute") == HookKind.TOOL.value
            and node_kind_by_id.get("validate") == HookKind.GATE.value
        ),
        "pass_to_emit": ("validate", HookSignal.PASS.value, "emit") in transition_set,
        "retry_to_execute": (
            "validate",
            HookSignal.RETRY.value,
            "execute",
        )
        in transition_set,
        "emit_to_seal_gate": (
            node_kind_by_id.get("emit") == HookKind.TOOL.value
            and node_kind_by_id.get("seal") == HookKind.GATE.value
            and ("emit", HookSignal.OBSERVED.value, "seal") in transition_set
        ),
        "positive_terminal_after_gate": (
            "seal",
            HookSignal.PASS.value,
            "ELIGIBLE",
        )
        in transition_set,
        "bounded_retry": policy.max_retries == 2,
        "success_control": (
            result.get("success_after_retry", {}).get("terminal") == "ELIGIBLE"
            and result.get("success_after_retry", {}).get("retries") == 1
        ),
        "retry_exhaustion_hold": (
            result.get("retry_exhausted", {}).get("terminal") == "HOLD"
            and result.get("retry_exhausted", {}).get("retries") == policy.max_retries
        ),
    }
    return {
        "valid": all(checks.values()),
        "reason": "valid_cb_reference_structure" if all(checks.values()) else "cb_reference_structure_mismatch",
        "checks": checks,
        "observed_structure": {
            "normal_path": ["execute", "validate", "emit", "seal", "ELIGIBLE"],
            "retry_edge": ["validate", "execute"],
            "retry_exhaustion_terminal": "HOLD",
            "node_kinds": node_kind_by_id,
            "max_retries": policy.max_retries,
        },
    }


def compare_lev_exec_validate_to_cb(
    lev_flow: dict[str, Any], cb_reference: dict[str, Any]
) -> dict[str, Any]:
    """Make the limited structural correspondence explicit and fail closed."""

    lev_structure = lev_flow.get("observed_structure")
    cb_structure = cb_reference.get("observed_structure")
    if not isinstance(lev_structure, dict) or not isinstance(cb_structure, dict):
        return {
            "valid": False,
            "reason": "reference_structure_is_missing",
            "checks": {},
        }
    checks = {
        "both_structures_valid": lev_flow.get("valid") is True and cb_reference.get("valid") is True,
        "two_phase_order": (
            lev_structure.get("normal_path", [])[:2] == ["exec", "validate"]
            and cb_structure.get("normal_path", [])[:2] == ["execute", "validate"]
            and cb_structure.get("node_kinds", {}).get("execute") == HookKind.TOOL.value
            and cb_structure.get("node_kinds", {}).get("validate") == HookKind.GATE.value
        ),
        "bounded_retry_loop": (
            lev_structure.get("retry_edge") == ["validate", "exec"]
            and cb_structure.get("retry_edge") == ["validate", "execute"]
            and isinstance(cb_structure.get("max_retries"), int)
            and cb_structure["max_retries"] > 0
        ),
        "positive_path_after_validation": (
            lev_structure.get("normal_path") == ["exec", "validate", "emit", "done"]
            and cb_structure.get("normal_path")
            == ["execute", "validate", "emit", "seal", "ELIGIBLE"]
        ),
        "intentional_exhaustion_difference": (
            lev_structure.get("timeout_path") == ["validate", "escalate", "done"]
            and cb_structure.get("retry_exhaustion_terminal") == "HOLD"
        ),
        "no_lev_gate_authority_imported": (
            lev_structure.get("validate_operation") == "lev.exec"
            and cb_structure.get("node_kinds", {}).get("validate") == HookKind.GATE.value
        ),
    }
    valid = all(checks.values())
    return {
        "valid": valid,
        "reason": "bounded_lev_cb_structure_correspondence_verified"
        if valid
        else "lev_cb_structure_correspondence_mismatch",
        "checks": checks,
        "mapping": {
            "shared_structure": [
                "two_phase_exec_then_validate",
                "bounded_retry_loop",
                "validated_pass_path_emits_before_terminal",
            ],
            "intentional_difference": (
                "Lev's timeout escalation is not imported: CB ends retry "
                "exhaustion at deterministic HOLD"
            ),
            "authority_difference": (
                "Lev validate remains an observed lev.exec operation; CB's "
                "validate node is a controller-owned deterministic GATE"
            ),
        },
    }


def run_leviathan_seal_boundary_controls(record: object) -> dict[str, Any]:
    """Prove the external-reference dry-run boundary rejects real execution."""

    baseline_valid, baseline_reason, _ = normalize_leviathan_dry_run_seal(record)
    if not baseline_valid or not isinstance(record, dict):
        return {
            "valid": False,
            "reason": "seal_boundary_control_input_invalid",
            "checks": {"baseline_dry_run": baseline_valid},
            "observed_reasons": {"baseline": baseline_reason},
        }
    execution_forgery = copy.deepcopy(record)
    execution_forgery.setdefault("seal", {})["outcome"] = "execution_success"
    execution_valid, execution_reason, _ = normalize_leviathan_dry_run_seal(execution_forgery)
    proof_forgery = copy.deepcopy(record)
    proof_receipts = [
        item
        for item in proof_forgery.get("seal", {}).get("evidence_refs", [])
        if isinstance(item, dict) and item.get("kind") == "receipt"
    ]
    if proof_receipts:
        proof_receipts[0]["proof_backed_execution"] = True
        proof_receipts[0]["passed"] = True
    proof_valid, proof_reason, _ = normalize_leviathan_dry_run_seal(proof_forgery)
    checks = {
        "baseline_dry_run": baseline_valid,
        "execution_outcome_refused": not execution_valid,
        "proof_bearing_receipt_refused": bool(proof_receipts) and not proof_valid,
    }
    valid = all(checks.values())
    return {
        "valid": valid,
        "reason": "dry_run_boundary_controls_verified"
        if valid
        else "dry_run_boundary_controls_failed",
        "checks": checks,
        "observed_reasons": {
            "baseline": baseline_reason,
            "execution_outcome": execution_reason,
            "proof_bearing_receipt": proof_reason,
        },
    }


def run_reference_conformance(*, run_root: Path, request_id: str) -> dict[str, Any]:
    """Run CB's fixed reference flow through success and bounded-retry paths."""

    request_id = _safe_id(request_id, "request_id")
    root = _new_root(run_root, "run_root")
    try:
        success = _run_scenario(root / "success_after_retry", request_id, "success_after_retry")
        exhausted = _run_scenario(root / "retry_exhausted", request_id, "retry_exhausted")
    except (MiniLevError, OSError, ValueError) as exc:
        return {
            "schema": SCHEMA,
            "disposition": "BLOCKED",
            "reason": "reference_flow_execution_error",
            "exception_type": type(exc).__name__,
            "error": str(exc),
            "promotion_allowed": False,
        }

    success_ok = (
        success.get("terminal") == "ELIGIBLE"
        and success.get("retries") == 1
        and success.get("completed_nodes") == ["emit", "execute", "seal", "validate"]
    )
    exhausted_ok = (
        exhausted.get("terminal") == "HOLD"
        and exhausted.get("retries") == 2
        and exhausted.get("completed_nodes") == ["execute"]
    )
    result = {
        "schema": SCHEMA,
        "disposition": "ELIGIBLE" if success_ok and exhausted_ok else "BLOCKED",
        "reason": (
            "fixed_leviathan_reference_semantics_observed"
            if success_ok and exhausted_ok
            else "reference_semantics_mismatch"
        ),
        "reference_contract": {
            "lev_flow": "sdlc-exec-validate",
            "reference_shape": ["exec", "validate", "emit", "escalate", "done"],
            "cb_shape": ["execute", "validate", "emit", "seal"],
            "preserved_semantics": [
                "two_phase_exec_then_validate_structure",
                "bounded_retry_loop_structure",
                "validated_pass_path_emits_before_terminal",
            ],
            "intentional_cb_difference": (
                "retry exhaustion becomes a deterministic HOLD; it does not "
                "invoke Lev escalation, an LLM, or a provider"
            ),
            "authority_difference": (
                "Lev validate is observed as lev.exec only; CB replaces it "
                "with a controller-owned deterministic GATE"
            ),
        },
        "success_after_retry": _receipt_summary(success),
        "retry_exhausted": _receipt_summary(exhausted),
        "controller_selected": True,
        "llm_decision_authority": False,
        "leviathan_decision_authority": False,
        "promotion_allowed": False,
        "claim_ceiling": (
            "CB-native deterministic comparison fixture only; no claim that "
            "Mini-Lev is full Leviathan or that an LLM/provider ran"
        ),
    }
    cb_structure = _cb_reference_structure(result)
    result["cb_reference_structure"] = cb_structure
    if result["disposition"] == "ELIGIBLE" and cb_structure["valid"] is not True:
        result["disposition"] = "BLOCKED"
        result["reason"] = "cb_reference_structure_mismatch"
    result["reference_contract_sha256"] = _SHA256(
        canonical_json(result["reference_contract"])
    ).hexdigest()
    return result


def normalize_leviathan_dry_run_seal(record: object) -> tuple[bool, str, dict[str, Any]]:
    """Validate only the small, portable semantic subset of a Lev dry-run seal."""

    if not isinstance(record, dict):
        return False, "execution seal record must be an object", {}
    if record.get("type") != "execution.sealed":
        return False, "record is not an execution seal", {}
    execution_id = record.get("execution_id")
    if not isinstance(execution_id, str) or not execution_id:
        return False, "execution id is missing", {}
    if record.get("invocation_id") != execution_id:
        return False, "invocation and execution ids differ", {}
    seal = record.get("seal")
    if not isinstance(seal, dict):
        return False, "seal material is missing", {}
    if seal.get("schema") != "lev.run_seal.v1":
        return False, "run seal schema mismatch", {}
    if seal.get("execution_id") != execution_id:
        return False, "seal execution binding mismatch", {}
    if seal.get("outcome") != "dry_run_success":
        return False, "reference run was not a successful dry run", {}
    intent_ref = seal.get("intent_ref")
    if (
        not isinstance(intent_ref, dict)
        or not isinstance(intent_ref.get("uri"), str)
        or not intent_ref["uri"].startswith("urn:lev:source-intent:sha256:")
    ):
        return False, "source intent reference is invalid", {}
    evidence_refs = seal.get("evidence_refs")
    if not isinstance(evidence_refs, list):
        return False, "seal evidence references are missing", {}
    evidence_by_kind = {
        item.get("kind"): item
        for item in evidence_refs
        if isinstance(item, dict) and isinstance(item.get("kind"), str)
    }
    receipt_ref = evidence_by_kind.get("receipt")
    trace_ref = evidence_by_kind.get("trace")
    if not isinstance(receipt_ref, dict) or not isinstance(trace_ref, dict):
        return False, "dry-run receipt and trace references are required", {}
    if (
        receipt_ref.get("dry_run") is not True
        or receipt_ref.get("proof_backed_execution") is not False
        or receipt_ref.get("passed") is not False
    ):
        return False, "reference receipt is not an unexecuted dry-run receipt", {}
    normalized = {
        "run_seal_schema": seal["schema"],
        "outcome": seal["outcome"],
        "intent_ref_scheme": "urn:lev:source-intent:sha256",
        "evidence_kinds": sorted(evidence_by_kind),
        "dry_run": True,
        "proof_backed_execution": False,
        "receipt_passed": False,
    }
    return True, "valid_leviathan_dry_run_seal", normalized


def _read_one_execution_seal(path: Path) -> tuple[bool, str, dict[str, Any] | None]:
    try:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, ValueError, TypeError) as exc:
        return False, f"execution ledger read failed: {type(exc).__name__}: {exc}", None
    seals = [row for row in rows if isinstance(row, dict) and row.get("type") == "execution.sealed"]
    if len(seals) != 1:
        return False, "isolated Lev probe must retain exactly one execution seal", None
    return True, "one execution seal found", seals[0]


def run_leviathan_dry_run_comparison(
    *,
    lev_root: Path,
    subject_root: Path,
    run_root: Path,
    request_id: str,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    """Launch one isolated Lev dry run and compare it with CB's fixed flow.

    This is an external workload adapter.  It is deliberately absent from the
    default CB kernel path, and a missing Lev/Bun/catalog is a PARKED result.
    """

    request_id = _safe_id(request_id, "request_id")
    if not isinstance(timeout_seconds, int) or isinstance(timeout_seconds, bool) or not 1 <= timeout_seconds <= 60:
        raise LeviathanReferenceError("timeout_seconds must be an integer from 1 through 60")
    lev_root = Path(lev_root).expanduser().resolve()
    subject_root = Path(subject_root).expanduser().resolve()
    root = _new_root(run_root, "run_root")
    flow_path = lev_root / _LEV_FLOW_RELATIVE_PATH
    lev_entry = lev_root / "core/poly/bin/lev"
    source_catalog = lev_root / "core/config/dist/source-catalog/bundle.json"
    bun = shutil.which("bun")
    if (
        not lev_root.is_dir()
        or not subject_root.is_dir()
        or not lev_entry.is_file()
        or not flow_path.is_file()
        or not source_catalog.is_file()
        or bun is None
    ):
        return {
            "schema": EXTERNAL_SCHEMA,
            "disposition": "PARKED",
            "reason": "leviathan_dry_run_preflight_unavailable",
            "preflight": {
                "lev_root_is_dir": lev_root.is_dir(),
                "subject_root_is_dir": subject_root.is_dir(),
                "lev_entry_exists": lev_entry.is_file(),
                "flow_exists": flow_path.is_file(),
                "source_catalog_exists": source_catalog.is_file(),
                "bun_available": bun is not None,
            },
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "promotion_allowed": False,
        }
    lev_flow = observe_lev_exec_validate_flow(flow_path)
    if lev_flow["valid"] is not True:
        return {
            "schema": EXTERNAL_SCHEMA,
            "disposition": "BLOCKED",
            "reason": "leviathan_reference_flow_structure_mismatch",
            "lev_flow_structure": lev_flow,
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "promotion_allowed": False,
        }

    xdg = root / "lev_xdg"
    for name in ("config", "data", "state", "cache", "runtime"):
        (xdg / name).mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment.update(
        {
            "XDG_CONFIG_HOME": str(xdg / "config"),
            "XDG_DATA_HOME": str(xdg / "data"),
            "XDG_STATE_HOME": str(xdg / "state"),
            "XDG_CACHE_HOME": str(xdg / "cache"),
            "XDG_RUNTIME_DIR": str(xdg / "runtime"),
            "NO_COLOR": "1",
        }
    )
    task = f"constraintbox-lev-reference-{request_id}"
    command = [
        bun,
        "core/poly/bin/lev",
        "exec",
        "--prompt",
        task,
        "--flow",
        str(flow_path),
        "--dry-run",
        "--surface",
        "shell",
        "--root-path",
        str(subject_root),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=lev_root,
            env=environment,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "schema": EXTERNAL_SCHEMA,
            "disposition": "PARKED",
            "reason": "leviathan_dry_run_launch_failed",
            "exception_type": type(exc).__name__,
            "error": str(exc),
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "promotion_allowed": False,
        }
    stdout = completed.stdout.encode("utf-8", errors="replace")
    stderr = completed.stderr.encode("utf-8", errors="replace")
    command_observation = {
        "returncode": completed.returncode,
        "stdout_sha256": _SHA256(stdout).hexdigest(),
        "stderr_sha256": _SHA256(stderr).hexdigest(),
    }
    if completed.returncode != 0:
        return {
            "schema": EXTERNAL_SCHEMA,
            "disposition": "PARKED",
            "reason": "leviathan_dry_run_nonzero_exit",
            "command_observation": command_observation,
            "stderr_tail": stderr[-1_024:].decode("utf-8", errors="replace"),
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "promotion_allowed": False,
        }
    ledger_path = xdg / "data/lev/execution-ledger/executions.jsonl"
    found, reason, seal = _read_one_execution_seal(ledger_path)
    if not found or seal is None:
        return {
            "schema": EXTERNAL_SCHEMA,
            "disposition": "BLOCKED",
            "reason": "leviathan_execution_seal_missing",
            "detail": reason,
            "command_observation": command_observation,
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "promotion_allowed": False,
        }
    seal_valid, seal_reason, normalized = normalize_leviathan_dry_run_seal(seal)
    cb = run_reference_conformance(
        run_root=root / "constraintbox_reference",
        request_id=request_id,
    )
    cb_structure = cb.get("cb_reference_structure")
    correspondence = compare_lev_exec_validate_to_cb(
        lev_flow,
        cb_structure if isinstance(cb_structure, dict) else {},
    )
    boundary_controls = run_leviathan_seal_boundary_controls(seal)
    eligible = (
        seal_valid
        and cb.get("disposition") == "ELIGIBLE"
        and correspondence["valid"] is True
        and boundary_controls["valid"] is True
    )
    return {
        "schema": EXTERNAL_SCHEMA,
        "disposition": "ELIGIBLE" if eligible else "BLOCKED",
        "reason": (
            "isolated_leviathan_dry_run_and_bounded_cb_conformance_eligible"
            if eligible
            else "leviathan_cb_reference_conformance_failed"
        ),
        "command_observation": command_observation,
        "lev_flow_structure": lev_flow,
        "leviathan_seal": {
            "valid": seal_valid,
            "reason": seal_reason,
            "normalized": normalized,
            "record_sha256": _SHA256(canonical_json(seal)).hexdigest(),
        },
        "constraintbox_reference": cb,
        "reference_correspondence": correspondence,
        "dry_run_boundary_controls": boundary_controls,
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "llm_decision_authority": False,
        "leviathan_decision_authority": False,
        "promotion_allowed": False,
        "claim_ceiling": (
            "one isolated Lev dry run and one CB-native deterministic reference "
            "flow; not a full Lev run, provider execution, equivalence proof, "
            "release, promotion, or agent authorization claim"
        ),
    }


def _write_new_json(path: Path, body: dict[str, Any]) -> None:
    if not path.is_absolute():
        raise LeviathanReferenceError("output path must be absolute")
    if path.exists():
        raise LeviathanReferenceError("output path must not already exist")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_json(body))
        stream.write(b"\n")
        stream.flush()
        os.fsync(stream.fileno())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lev-root", required=True)
    parser.add_argument("--subject-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args(argv)
    try:
        result = run_leviathan_dry_run_comparison(
            lev_root=Path(args.lev_root),
            subject_root=Path(args.subject_root),
            run_root=Path(args.run_root),
            request_id=args.request_id,
            timeout_seconds=args.timeout_seconds,
        )
        _write_new_json(Path(args.output), result)
    except LeviathanReferenceError as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("disposition") == "ELIGIBLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
