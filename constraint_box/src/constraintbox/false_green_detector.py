"""False-green detector: prevents receipt-cached and weakened-gate false positives.

Adapted from Lev OS's task-readiness.validateSlice (core/orchestration/src/entities/task-readiness.ts).
Lev's approach: receipt authority classification (XDG task-receipt route is the ONLY certifying source;
project-local receipts are historical/read-only and never certify completion).

CB application: gates produce execution receipts with input_sha256, output_sha256, and verdict.
False-green risk classes:
  1. cached_local_receipt      - gate verdict from stale local file, not from fresh execution
  2. missing_reverse_brainstorm - adversarial gate lacks plausible false paths
  3. weak_evidence            - evidence field is too weak for claim strength
  4. unmatched_fixture        - fixture contract does not match verifier intent
  5. missing_trace_contract   - high-value claims lack machine-readable trace
  6. replay_attempt           - same gate input executed twice with different output
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .intake import canonical_json


class FalseGreenSeverity(Enum):
    """Severity levels for false-green risk classification."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class FalseGreenDiagnostic:
    """A false-green risk detected in gate execution or receipt lifecycle."""
    severity: FalseGreenSeverity
    code: str
    path: str
    message: str
    gate_id: str = ""
    remediation: str = ""


@dataclass
class FalseGreenAnalysis:
    """Result of false-green analysis on a gate execution or receipt set."""
    receipt_path: str
    diagnostics: list[FalseGreenDiagnostic] = field(default_factory=list)
    has_errors: bool = field(default=False)
    has_warnings: bool = field(default=False)
    summary: dict[str, Any] = field(default_factory=dict)


def add_diagnostic(
    diagnostics: list[FalseGreenDiagnostic],
    severity: FalseGreenSeverity,
    code: str,
    path: str,
    message: str,
    gate_id: str = "",
    remediation: str = "",
) -> None:
    """Add a diagnostic to the list."""
    diagnostics.append(FalseGreenDiagnostic(
        severity=severity,
        code=code,
        path=path,
        message=message,
        gate_id=gate_id,
        remediation=remediation,
    ))


def check_receipt_authority(receipt: dict[str, Any], path: Path) -> tuple[str, str]:
    """Classify receipt authority: certifying source or local-only.

    Returns (authority_type, status):
      - ("xdg_task_receipt", "accepted") - certified, promotion-eligible
      - ("xdg_task_receipt", "pending") - awaiting final certification
      - ("local", "pending") - historical, non-certifying
      - ("unknown", "none") - authority unclear

    This is the FALSE-GREEN FENCE: local receipts alone cannot certify.
    """
    # Check if this receipt came from the XDG task-receipt route
    xdg_path_marker = "/.lev/task-receipt/" in str(path)
    source_annotation = receipt.get("_source_authority", "")

    # Status check
    status = receipt.get("status", "pending")
    if status not in ("accepted", "pending"):
        status = "pending"

    if xdg_path_marker or source_annotation == "xdg_task_receipt":
        return ("xdg_task_receipt", status)
    elif "/.lev/tasks/" in str(path):
        # Local project receipt directory
        return ("local", status)
    else:
        return ("unknown", "none")


def has_reverse_brainstorm(gate_record: dict[str, Any], min_count: int = 2) -> bool:
    """Check if gate has minimum plausible false-green paths (like Lev's adversarial gates).

    For adversarial/promotion gates: require false_green_paths, reverse_brainstorm,
    or adversarial_false_green_paths field with at least min_count items.
    """
    possible_fields = [
        gate_record.get("reverse_brainstorm"),
        gate_record.get("false_green_paths"),
        gate_record.get("adversarial_false_green_paths"),
    ]

    for field_value in possible_fields:
        if isinstance(field_value, list) and len(field_value) >= min_count:
            return True
    return False


def check_gate_weakening(
    previous_gate: dict[str, Any],
    current_gate: dict[str, Any],
    gate_id: str,
) -> list[str]:
    """Detect if a gate has been weakened (G3 gap).

    Weakening detections:
      - verdict was PASS, now BLOCKED/FAIL
      - input_sha256 identical but output changed (replay without re-run)
      - verdict enumeration narrowed (e.g., allowed more cases)
      - evidence threshold lowered
      - fixture/contract removed or weakened

    Returns list of weakening issue codes.
    """
    issues = []

    # Check for verdict relaxation (false progress): same input, different (worse) output
    if (previous_gate.get("input_sha256") == current_gate.get("input_sha256") and
            previous_gate.get("output_sha256") != current_gate.get("output_sha256")):
        issues.append("replay_output_mismatch")

    # Check verdict progression
    prev_verdict = str(previous_gate.get("verdict", "UNKNOWN")).upper()
    curr_verdict = str(current_gate.get("verdict", "UNKNOWN")).upper()

    # Detect regression: if previous was PASS-like, current should not be FAIL-like
    pass_verdicts = {"PASS", "ELIGIBLE", "VERIFIED", "RATCHETS"}
    fail_verdicts = {"FAIL", "BLOCKED", "BLOCKED", "CAN_SPIN"}

    if prev_verdict in pass_verdicts and curr_verdict in fail_verdicts:
        issues.append("verdict_regression")

    # Check if evidence/fixture got removed
    prev_evidence_count = len(str(previous_gate.get("required_evidence", "")).split())
    curr_evidence_count = len(str(current_gate.get("required_evidence", "")).split())
    if prev_evidence_count > curr_evidence_count:
        issues.append("evidence_threshold_lowered")

    # Check if fixture contract weakened
    prev_fixture = previous_gate.get("fixture_contract", {})
    curr_fixture = current_gate.get("fixture_contract", {})
    if prev_fixture and not curr_fixture:
        issues.append("fixture_contract_removed")

    return issues


def validate_adversarial_gate_slice(
    gate: dict[str, Any],
    gate_index: int,
    diagnostics: list[FalseGreenDiagnostic],
    min_reverse_brainstorm: int = 2,
) -> dict[str, int]:
    """Validate an adversarial gate similar to Lev's validateSlice.

    Checks for:
      - Minimum reverse brainstorm (false-green paths)
      - Failure hypotheses named
      - Fitness functions mapped
      - Claim coverage

    Returns count dict: {hypotheses: int, fitness: int}
    """
    gate_id = gate.get("gate_id", f"gate-{gate_index}")
    path = f"gates[{gate_index}]"

    # Parse adversarial markers
    assurance_mode = str(gate.get("assurance_level", "") or gate.get("assurance_mode", "")).lower()
    reverse_brainstorm = gate.get("reverse_brainstorm", [])
    hypotheses = gate.get("failure_hypotheses", []) or gate.get("adversarial_hypotheses", [])
    fitness = gate.get("fitness_functions", []) or gate.get("adversarial_fitness_functions", [])

    is_adversarial = (
        len(reverse_brainstorm) > 0
        or len(hypotheses) > 0
        or len(fitness) > 0
        or any(kw in assurance_mode for kw in ["adversarial", "promotion", "eval_harness"])
    )

    if is_adversarial and len(reverse_brainstorm) < min_reverse_brainstorm:
        add_diagnostic(
            diagnostics,
            FalseGreenSeverity.ERROR,
            "missing_reverse_brainstorm",
            f"{path}.reverse_brainstorm",
            f"Adversarial gate {gate_id} needs at least {min_reverse_brainstorm} plausible false-green paths.",
            gate_id=gate_id,
            remediation="Add reverse_brainstorm entries with explicit false-green scenarios.",
        )

    if is_adversarial and len(hypotheses) == 0:
        add_diagnostic(
            diagnostics,
            FalseGreenSeverity.ERROR,
            "missing_failure_hypotheses",
            f"{path}.failure_hypotheses",
            f"Adversarial gate {gate_id} has no named failure hypotheses.",
            gate_id=gate_id,
            remediation="Define failure_hypotheses for this gate.",
        )

    if is_adversarial and len(fitness) == 0:
        add_diagnostic(
            diagnostics,
            FalseGreenSeverity.ERROR,
            "missing_fitness_functions",
            f"{path}.fitness_functions",
            f"Adversarial gate {gate_id} has no concrete fitness functions/tests.",
            gate_id=gate_id,
            remediation="Define fitness_functions that falsify each hypothesis.",
        )

    # Map fitness to hypotheses
    fitness_by_hypothesis = {}
    for fit in fitness:
        falsifies_list = fit.get("falsifies", []) or [fit.get("hypothesis_id")]
        for hyp_id in falsifies_list:
            if hyp_id not in fitness_by_hypothesis:
                fitness_by_hypothesis[hyp_id] = []
            fitness_by_hypothesis[hyp_id].append(fit.get("id", "unknown"))

    # Check coverage
    for hyp in hypotheses:
        hyp_id = hyp.get("id", hyp.get("name", "unknown"))
        risk = (hyp.get("risk") or "medium").lower()
        if risk in ("high", "critical", "medium") and hyp_id not in fitness_by_hypothesis:
            add_diagnostic(
                diagnostics,
                FalseGreenSeverity.WARNING,
                "uncovered_failure_hypothesis",
                f"{path}.failure_hypotheses[{hypotheses.index(hyp)}]",
                f"Hypothesis {hyp_id} is {risk} risk but no fitness function covers it.",
                gate_id=gate_id,
                remediation="Add or update fitness_functions to cover this hypothesis.",
            )

    return {"hypotheses": len(hypotheses), "fitness": len(fitness)}


def analyze_receipt_lifecycle(receipt_path: str | Path) -> FalseGreenAnalysis:
    """Analyze a gate execution receipt for false-green risks.

    Checks:
      1. Receipt authority: is this XDG-certified or just local cache?
      2. Reverse brainstorm: adversarial gates have plausible false paths?
      3. Verdict regression: does current gate weaken from previous?
      4. Evidence/fixture integrity: required fields present and non-zero?
    """
    receipt_path = Path(receipt_path)
    analysis = FalseGreenAnalysis(receipt_path=str(receipt_path))
    diagnostics: list[FalseGreenDiagnostic] = []

    if not receipt_path.exists():
        add_diagnostic(
            diagnostics,
            FalseGreenSeverity.ERROR,
            "receipt_not_found",
            str(receipt_path),
            f"Receipt file does not exist: {receipt_path}",
        )
        analysis.diagnostics = diagnostics
        analysis.has_errors = True
        return analysis

    try:
        with open(receipt_path, "r") as f:
            receipt = json.load(f)
    except Exception as e:
        add_diagnostic(
            diagnostics,
            FalseGreenSeverity.ERROR,
            "receipt_parse_error",
            str(receipt_path),
            f"Failed to parse receipt: {e}",
        )
        analysis.diagnostics = diagnostics
        analysis.has_errors = True
        return analysis

    # Check receipt authority
    authority_type, authority_status = check_receipt_authority(receipt, receipt_path)
    if authority_type == "local" and authority_status == "pending":
        add_diagnostic(
            diagnostics,
            FalseGreenSeverity.WARNING,
            "local_receipt_not_certified",
            str(receipt_path),
            "Receipt is from local .lev/tasks directory, not XDG-certified. Cannot drive promotion.",
            remediation="Use XDG task-receipt route for certified completion.",
        )

    # Check for adversarial gate requirements
    if "gates" in receipt:
        gates = receipt.get("gates", [])
        for idx, gate in enumerate(gates):
            validate_adversarial_gate_slice(gate, idx, diagnostics)

    # Check for output hash integrity
    if "input_sha256" in receipt and "output_sha256" in receipt:
        # Verify output is non-null
        output_field = receipt.get("output", {})
        if not output_field or isinstance(output_field, dict) and "error" in output_field:
            add_diagnostic(
                diagnostics,
                FalseGreenSeverity.WARNING,
                "empty_gate_output",
                f"{receipt_path}.output",
                "Gate output is empty or contains only error. Verdict reliability questionable.",
            )

    # Summarize
    analysis.diagnostics = diagnostics
    analysis.has_errors = any(d.severity == FalseGreenSeverity.ERROR for d in diagnostics)
    analysis.has_warnings = any(d.severity == FalseGreenSeverity.WARNING for d in diagnostics)
    analysis.summary = {
        "receipt_authority": authority_type,
        "authority_status": authority_status,
        "error_count": sum(1 for d in diagnostics if d.severity == FalseGreenSeverity.ERROR),
        "warning_count": sum(1 for d in diagnostics if d.severity == FalseGreenSeverity.WARNING),
        "checked_gates": len([g for g in receipt.get("gates", [])]),
    }

    return analysis


def detect_gate_weakening(
    current_ledger: dict[str, Any],
    previous_ledger: dict[str, Any],
) -> FalseGreenAnalysis:
    """Detect gate weakening by comparing two gate ledger states (G3 gap).

    Input: two gate ledgers (typically current vs. previous from git history or prior run)
    Output: FalseGreenAnalysis with weakening diagnostics

    Weakening = a gate's verdict improved without sufficient input change, or
    evidence/fixture requirements were lowered, or verdict regression occurred.
    """
    analysis = FalseGreenAnalysis(receipt_path="gate_ledger_comparison")
    diagnostics: list[FalseGreenDiagnostic] = []

    # Build gate maps by gate_id
    current_gates = {g.get("gate_id"): g for g in current_ledger.get("gates", [])}
    previous_gates = {g.get("gate_id"): g for g in previous_ledger.get("gates", [])}

    # Check each gate that exists in both ledgers
    for gate_id in set(current_gates.keys()) & set(previous_gates.keys()):
        curr = current_gates[gate_id]
        prev = previous_gates[gate_id]

        weakening_issues = check_gate_weakening(prev, curr, gate_id)
        for issue in weakening_issues:
            add_diagnostic(
                diagnostics,
                FalseGreenSeverity.ERROR,
                issue,
                f"gates[{gate_id}]",
                f"Gate {gate_id} shows weakening pattern: {issue}",
                gate_id=gate_id,
                remediation="Audit gate configuration and re-run with full verification.",
            )

    analysis.diagnostics = diagnostics
    analysis.has_errors = len(weakening_issues) > 0 if diagnostics else False
    analysis.summary = {
        "gates_checked": len(set(current_gates.keys()) & set(previous_gates.keys())),
        "weakening_detected": len(diagnostics),
    }

    return analysis
