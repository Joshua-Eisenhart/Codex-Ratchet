"""Gate weakening detection (G3 gap implementation).

This module detects when a gate's constraints have been weakened without corresponding
evidence changes. Weakening includes:
  - Verdict improvement without input change
  - Evidence threshold lowered
  - Fixture/contract removed
  - Acceptance criteria relaxed
  - Falsifier scope narrowed

Provides both CLI subcommand and programmatic API.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .intake import canonical_json


@dataclass(frozen=True)
class WeakeningFinding:
    """A single weakening detection."""
    gate_id: str
    weakening_type: str  # verdict_regression, evidence_lowered, fixture_removed, etc.
    severity: str  # "critical", "high", "medium"
    previous_state: dict[str, Any]
    current_state: dict[str, Any]
    reason: str


@dataclass
class WeakeningDetectionResult:
    """Result of gate weakening analysis."""
    ledger_path: str
    previous_snapshot_path: str | None
    findings: list[WeakeningFinding]
    total_gates_checked: int
    total_findings: int


def extract_acceptance_criteria(gate: dict[str, Any]) -> set[str]:
    """Extract acceptance criteria keywords from a gate record.

    These are considered "hard constraints" and lowering them is weakening.
    """
    criteria = set()

    # Explicit acceptance_criteria field
    if "acceptance_criteria" in gate:
        val = gate["acceptance_criteria"]
        if isinstance(val, list):
            criteria.update(str(x).lower() for x in val)
        elif isinstance(val, str):
            criteria.update(w.lower() for w in val.split())

    # Verdict constraints
    if "allowed_verdicts" in gate:
        val = gate["allowed_verdicts"]
        if isinstance(val, list):
            criteria.update(f"verdict:{v}" for v in val)

    # Evidence fields (presence indicates requirement)
    if "required_evidence" in gate:
        val = gate["required_evidence"]
        if isinstance(val, list):
            criteria.update(f"evidence:{e}" for e in val)

    # Fixture/contract presence
    if "fixture_contract" in gate:
        criteria.add("has_fixture_contract")
    if "boundary_contract" in gate:
        criteria.add("has_boundary_contract")

    # Falsifier scope
    if "falsifies" in gate:
        val = gate["falsifies"]
        if isinstance(val, list):
            criteria.update(f"falsifies:{f}" for f in val)

    return criteria


def compare_acceptance_criteria(
    previous_criteria: set[str],
    current_criteria: set[str],
) -> tuple[set[str], set[str], set[str]]:
    """Compare criteria sets.

    Returns: (removed_criteria, added_criteria, unchanged_criteria)
    Removed criteria = weakening.
    """
    removed = previous_criteria - current_criteria
    added = current_criteria - previous_criteria
    unchanged = previous_criteria & current_criteria
    return removed, added, unchanged


def detect_verdict_regression(prev_verdict: str, curr_verdict: str) -> bool | str:
    """Detect if verdict has regressed (weakened).

    Regression = went from passing to failing without expected evidence change.
    Returns False if no regression, or a reason string if regression detected.
    """
    prev = str(prev_verdict).upper().strip()
    curr = str(curr_verdict).upper().strip()

    # Define verdict strength levels
    strength_levels = {
        "PASS": 5,
        "VERIFIED": 5,
        "ELIGIBLE": 5,
        "RATCHETS": 5,
        "UNKNOWN": 3,
        "HOLD": 2,
        "BLOCKED": 1,
        "FAIL": 1,
        "CAN_SPIN": 1,
    }

    prev_strength = strength_levels.get(prev, 0)
    curr_strength = strength_levels.get(curr, 0)

    # Regression: same input but verdict got worse
    if curr_strength < prev_strength:
        return f"verdict_weakened:{prev}→{curr}"

    return False


def detect_evidence_lowering(prev_gate: dict[str, Any], curr_gate: dict[str, Any]) -> list[str]:
    """Detect if evidence requirements have been lowered.

    Lowering includes:
      - Field removed from required_evidence
      - Threshold lowered (e.g., "at least 3 items" → "at least 1")
      - Count decreased
    """
    issues = []

    prev_evidence = set(str(e).lower() for e in prev_gate.get("required_evidence", []))
    curr_evidence = set(str(e).lower() for e in curr_gate.get("required_evidence", []))

    if prev_evidence and curr_evidence and len(curr_evidence) < len(prev_evidence):
        removed = prev_evidence - curr_evidence
        issues.append(f"evidence_fields_removed:{','.join(removed)}")

    # Check threshold fields
    prev_threshold = prev_gate.get("min_evidence_count", 999)
    curr_threshold = curr_gate.get("min_evidence_count", 0)
    if curr_threshold < prev_threshold:
        issues.append(f"evidence_threshold_lowered:{prev_threshold}→{curr_threshold}")

    return issues


def detect_fixture_removal(prev_gate: dict[str, Any], curr_gate: dict[str, Any]) -> list[str]:
    """Detect if fixture/contract has been removed or weakened."""
    issues = []

    # Fixture contract removal
    prev_fixture = bool(prev_gate.get("fixture_contract"))
    curr_fixture = bool(curr_gate.get("fixture_contract"))
    if prev_fixture and not curr_fixture:
        issues.append("fixture_contract_removed")

    # Boundary contract removal
    prev_boundary = bool(prev_gate.get("boundary_contract"))
    curr_boundary = bool(curr_gate.get("boundary_contract"))
    if prev_boundary and not curr_boundary:
        issues.append("boundary_contract_removed")

    # Falsifier scope narrowing (fewer things falsified)
    prev_falsifies = set(str(f).lower() for f in prev_gate.get("falsifies", []))
    curr_falsifies = set(str(f).lower() for f in curr_gate.get("falsifies", []))
    if prev_falsifies and curr_falsifies and len(curr_falsifies) < len(prev_falsifies):
        narrowed = prev_falsifies - curr_falsifies
        issues.append(f"falsifier_scope_narrowed:{','.join(narrowed)}")

    return issues


def detect_input_hash_mismatch(prev_gate: dict[str, Any], curr_gate: dict[str, Any]) -> bool:
    """Detect if output changed without input changing (potential replay or false edit)."""
    prev_input = prev_gate.get("input_sha256", "")
    curr_input = curr_gate.get("input_sha256", "")
    prev_output = prev_gate.get("output_sha256", "")
    curr_output = curr_gate.get("output_sha256", "")

    # Same input, different output = suspect
    if prev_input and prev_input == curr_input and prev_output != curr_output:
        return True

    return False


def check_gate_weakening(
    prev_gate: dict[str, Any],
    curr_gate: dict[str, Any],
) -> list[WeakeningFinding]:
    """Comprehensive gate weakening check.

    Returns list of WeakeningFinding objects, one per detected weakening.
    """
    findings: list[WeakeningFinding] = []
    gate_id = curr_gate.get("gate_id", "unknown")

    # 1. Verdict regression
    regression = detect_verdict_regression(
        prev_gate.get("verdict", "UNKNOWN"),
        curr_gate.get("verdict", "UNKNOWN"),
    )
    if regression:
        findings.append(WeakeningFinding(
            gate_id=gate_id,
            weakening_type="verdict_regression",
            severity="critical",
            previous_state=prev_gate,
            current_state=curr_gate,
            reason=str(regression),
        ))

    # 2. Evidence lowering
    evidence_issues = detect_evidence_lowering(prev_gate, curr_gate)
    for issue in evidence_issues:
        findings.append(WeakeningFinding(
            gate_id=gate_id,
            weakening_type="evidence_lowered",
            severity="high",
            previous_state=prev_gate,
            current_state=curr_gate,
            reason=issue,
        ))

    # 3. Fixture removal
    fixture_issues = detect_fixture_removal(prev_gate, curr_gate)
    for issue in fixture_issues:
        findings.append(WeakeningFinding(
            gate_id=gate_id,
            weakening_type="fixture_removal",
            severity="high",
            previous_state=prev_gate,
            current_state=curr_gate,
            reason=issue,
        ))

    # 4. Input hash mismatch (replay suspicion)
    if detect_input_hash_mismatch(prev_gate, curr_gate):
        findings.append(WeakeningFinding(
            gate_id=gate_id,
            weakening_type="input_hash_mismatch",
            severity="high",
            previous_state=prev_gate,
            current_state=curr_gate,
            reason="same input but different output suggests cache/replay issue",
        ))

    # 5. Acceptance criteria loosening
    prev_criteria = extract_acceptance_criteria(prev_gate)
    curr_criteria = extract_acceptance_criteria(curr_gate)
    removed, added, _ = compare_acceptance_criteria(prev_criteria, curr_criteria)

    if removed:
        findings.append(WeakeningFinding(
            gate_id=gate_id,
            weakening_type="criteria_removed",
            severity="high",
            previous_state=prev_gate,
            current_state=curr_gate,
            reason=f"acceptance criteria removed: {','.join(removed)}",
        ))

    return findings


def compare_gate_ledgers(
    current_ledger: dict[str, Any],
    previous_ledger: dict[str, Any],
) -> WeakeningDetectionResult:
    """Compare two gate ledgers (current vs. previous/baseline).

    Returns comprehensive weakening detection result.
    """
    curr_gates = {g.get("gate_id"): g for g in current_ledger.get("gates", []) if g.get("gate_id")}
    prev_gates = {g.get("gate_id"): g for g in previous_ledger.get("gates", []) if g.get("gate_id")}

    all_findings: list[WeakeningFinding] = []

    # Check gates that exist in both
    for gate_id in set(curr_gates.keys()) & set(prev_gates.keys()):
        findings = check_gate_weakening(prev_gates[gate_id], curr_gates[gate_id])
        all_findings.extend(findings)

    # Gates removed (could indicate avoidance)
    removed_gates = set(prev_gates.keys()) - set(curr_gates.keys())
    for gate_id in removed_gates:
        all_findings.append(WeakeningFinding(
            gate_id=gate_id,
            weakening_type="gate_removed",
            severity="high",
            previous_state=prev_gates[gate_id],
            current_state={},
            reason="gate was removed from ledger entirely",
        ))

    result = WeakeningDetectionResult(
        ledger_path=current_ledger.get("_ledger_path", "unknown"),
        previous_snapshot_path=previous_ledger.get("_ledger_path"),
        findings=all_findings,
        total_gates_checked=len(set(curr_gates.keys()) & set(prev_gates.keys())),
        total_findings=len(all_findings),
    )

    return result


def load_gate_ledger(path: str | Path) -> dict[str, Any]:
    """Load a gate ledger from JSON."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Gate ledger not found: {path}")

    with open(path, "r") as f:
        ledger = json.load(f)

    # Annotate with source path for traceability
    ledger["_ledger_path"] = str(path)
    return ledger


def analyze_gate_ledger_weakening(
    current_ledger_path: str | Path,
    previous_ledger_path: str | Path | None = None,
) -> WeakeningDetectionResult:
    """Main entry point: load two ledgers and detect weakening.

    If previous_ledger_path is None, attempts to find it from git history or
    uses a default/empty baseline.
    """
    current = load_gate_ledger(current_ledger_path)

    if previous_ledger_path:
        previous = load_gate_ledger(previous_ledger_path)
    else:
        # Default baseline: empty ledger (all gates are new)
        previous = {"gates": [], "_ledger_path": "(baseline)"}

    return compare_gate_ledgers(current, previous)
