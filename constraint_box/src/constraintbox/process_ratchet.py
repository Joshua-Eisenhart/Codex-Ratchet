"""Process-order ratchet: rung advancement refused without re-validated receipts.

A rung is (rung_id, ordinal, evidence paths, gate operations, receipt).
``ProcessRatchet.advance(to_rung_id, ...)`` REFUSES unless every rung below the
target has a receipt in the existing hash-chained ledger that re-validates NOW,
from bytes.  Refusal is a typed state using the existing vocabulary, never an
exception swallowed into a warning:

* ``PARKED``               -- an unmet precondition: a missing lower-rung
                              receipt (named), missing evidence bytes (named),
                              or a declared gate with no execution receipt
                              (named).  Operationalism: a gate identifier that
                              names no executed operation is not a gate.
* ``BLOCKED``              -- a gate executed and its verdict is FAIL, or the
                              target rung is already recorded (progress is
                              chain EXTENSION only; there is no re-entry).
* ``INVARIANT_VIOLATION``  -- recorded state no longer matches bytes: the
                              ledger chain fails verification, the recorded
                              rung sequence is not a prefix of the declared
                              ladder, or a lower rung's evidence digest,
                              ladder-prefix digest, ordinal, or evidence key
                              set changed since it was recorded.  Stop; never
                              repair silently.
* ``HOLD``                 -- the three deciders did not reach three definite,
                              execution-valid, agreeing votes.  Fail closed.

The admissibility decision itself is NOT a Python if/else chain.  Every
measured fact is pinned as an enumerated finite-domain variable, the rung
preconditions are equality requirements over those variables, and the whole
thing is a ``FiniteConstraintProblem`` decided by ``dualsolve.dual_solve``
(z3 + cvc5 + the internal bounded enumeration reference, three-way agreement).
BOUNDED_SAT means the advance is admissible; BOUNDED_UNSAT means it is
refused; anything short of agreement is HOLD.  Python's remaining role after
the verdict is naming WHICH typed refusal applies, by fixed precedence over
the same enumerated measurements.

Every successful advance appends one receipt record to the EXISTING
``HashChainLedger`` (no new chain).  The receipt pins, per rung: the sha256 of
every evidence file's bytes, the executed gate operations (gate_id,
input_sha256, output_sha256, verdict), the recomputed evidence of every lower
rung at the moment of this advance, the full solver decision, the decision
spec and its sha256, and a ladder-prefix sha256 so a silent rewrite of the
ladder below a recorded rung is caught as drift on the next advance.

Doctrine (owner, binding): no score, no ranking, no "best" -- progress is
chain extension only.  No meta-ratchet: re-validating lower rungs is
re-running checks, nothing here ratchets the ratchet.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .dualsolve import dual_solve
from .intake import canonical_json
from .ledger import HashChainLedger
from .ratchet import _is_prefix

RUNG_RECEIPT_SCHEMA = "constraintbox.process-rung-receipt.v1"

ADVANCED = "ADVANCED"
PARKED = "PARKED"
BLOCKED = "BLOCKED"
HOLD = "HOLD"
INVARIANT_VIOLATION = "INVARIANT_VIOLATION"

REFUSAL_STATES = (PARKED, BLOCKED, HOLD, INVARIANT_VIOLATION)

GATE_VERDICTS = ("PASS", "FAIL")

# Enumerated measurement domains.  Decision-bearing fields carry these values
# and nothing else; prose only ever accompanies a decision as commentary.
_LEDGER_DOMAIN = ("intact", "broken")
_CHAIN_DOMAIN = ("prefix_of_ladder", "diverged")
_EXTENSION_DOMAIN = ("next", "already_recorded", "out_of_order")
_RUNG_DOMAIN = ("validated", "missing", "drifted")
_GATE_DOMAIN = ("executed_pass", "executed_fail", "declared_only")
_EVIDENCE_DOMAIN = ("present", "absent")

_HEX_DIGITS = frozenset("0123456789abcdef")


def _sha256_bytes(value: bytes) -> str:
    # Mirrors agentrun._sha256_bytes / manifold_foundation._sha256.  Local copy
    # because agentrun.py must not be edited in this phase (to export it) and
    # importing agentrun pulls the whole agent runtime into this module's
    # import graph.
    return hashlib.sha256(value).hexdigest()


def _require_sha256(value: Any, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _HEX_DIGITS for character in value)
    ):
        raise ValueError(f"{label} must be a 64-character lowercase hex sha256")


def _require_identifier(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a nonempty string")


@dataclass(frozen=True)
class GateExecution:
    """One executed gate operation.  A gate IS its operation.

    A gate identifier is admissible in a rung receipt only through one of
    these: input sha256, output sha256, and an enumerated verdict.  A gate ID
    with no execution receipt is ``declared_only`` and parks the advance.
    """

    gate_id: str
    input_sha256: str
    output_sha256: str
    verdict: str

    def __post_init__(self) -> None:
        _require_identifier(self.gate_id, "gate_id")
        _require_sha256(self.input_sha256, "input_sha256")
        _require_sha256(self.output_sha256, "output_sha256")
        if self.verdict not in GATE_VERDICTS:
            raise ValueError(
                f"verdict must be one of {GATE_VERDICTS}, got {self.verdict!r}"
            )

    def to_dict(self) -> dict[str, str]:
        return {
            "gate_id": self.gate_id,
            "input_sha256": self.input_sha256,
            "output_sha256": self.output_sha256,
            "verdict": self.verdict,
        }


@dataclass(frozen=True)
class RungSpec:
    """One declared rung: identity, position, evidence bytes, gate operations."""

    rung_id: str
    ordinal: int
    evidence_paths: tuple[str, ...]
    gate_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_identifier(self.rung_id, "rung_id")
        if not isinstance(self.ordinal, int) or self.ordinal < 0:
            raise ValueError("ordinal must be a nonnegative integer")
        if not self.evidence_paths:
            raise ValueError(
                "a rung needs at least one evidence path; a rung with no bytes"
                " cannot be re-validated from bytes"
            )
        for path in self.evidence_paths:
            _require_identifier(path, "evidence path")
        if len(set(self.evidence_paths)) != len(self.evidence_paths):
            raise ValueError("duplicate evidence paths")
        for gate_id in self.gate_ids:
            _require_identifier(gate_id, "gate_id")
        if len(set(self.gate_ids)) != len(self.gate_ids):
            raise ValueError("duplicate gate ids")


@dataclass(frozen=True)
class AdvanceResult:
    """Typed outcome of one advance attempt.  ``state`` is the decision."""

    state: str
    rung_id: str
    reason: str
    missing_rungs: tuple[str, ...]
    missing_gates: tuple[str, ...]
    failed_gates: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    drifted: tuple[tuple[str, str, str, str], ...]
    decision: dict[str, Any]
    spec: dict[str, Any]
    receipt_line_sha256: str | None


class ProcessRatchet:
    """Enforced process order over a declared ladder of rungs.

    Composes what already exists: the hash-chained ``HashChainLedger`` for
    receipts (append + full-chain verify on every advance), ``dual_solve`` for
    the admissibility decision, and ``ratchet._is_prefix`` -- the doctrinal
    prefix-chain primitive -- for the chain-extension check.
    """

    def __init__(
        self,
        ladder: tuple[RungSpec, ...],
        ledger: HashChainLedger,
        evidence_root: Path,
    ):
        if not ladder:
            raise ValueError("ladder must be nonempty")
        for position, rung in enumerate(ladder):
            if not isinstance(rung, RungSpec):
                raise ValueError("ladder must contain RungSpec entries")
            if rung.ordinal != position:
                raise ValueError(
                    "ladder ordinals must be contiguous from 0 in order;"
                    f" position {position} declares ordinal {rung.ordinal}"
                )
        identifiers = [rung.rung_id for rung in ladder]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("duplicate rung ids in ladder")
        self.ladder = tuple(ladder)
        self.ledger = ledger
        self.evidence_root = Path(evidence_root)
        self._by_id = {rung.rung_id: rung for rung in self.ladder}
        self._declared_ids = tuple(identifiers)

    # -- recorded state -----------------------------------------------------

    def recorded_receipts(self) -> tuple[dict[str, Any], ...]:
        """Rung receipts already on the chain, in chain order."""
        if not self.ledger.path.exists():
            return ()
        records: list[dict[str, Any]] = []
        try:
            lines = self.ledger.path.read_text(encoding="utf-8").splitlines()
            for line in lines:
                row = json.loads(line)
                record = row.get("record")
                if (
                    isinstance(record, dict)
                    and record.get("schema") == RUNG_RECEIPT_SCHEMA
                ):
                    records.append(record)
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            # An unreadable chain is not a verified prefix of anything; the
            # ledger verify leg refuses the advance independently.
            return ()
        return tuple(records)

    def next_rung(self) -> str | None:
        """The declared rung that chain extension names next, or None."""
        recorded_ids = tuple(
            record.get("rung_id", "") for record in self.recorded_receipts()
        )
        if not _is_prefix(recorded_ids, self._declared_ids):
            return None
        if len(recorded_ids) == len(self._declared_ids):
            return None
        return self._declared_ids[len(recorded_ids)]

    # -- measurement (operations in Python, outcomes enumerated) ------------

    def _ladder_prefix_sha256(self, ordinal: int) -> str:
        payload = [
            {
                "rung_id": rung.rung_id,
                "ordinal": rung.ordinal,
                "evidence_paths": list(rung.evidence_paths),
                "gate_ids": list(rung.gate_ids),
            }
            for rung in self.ladder[: ordinal + 1]
        ]
        return _sha256_bytes(canonical_json(payload))

    def _evidence_digests(
        self, rung: RungSpec
    ) -> tuple[dict[str, str], tuple[str, ...]]:
        digests: dict[str, str] = {}
        missing: list[str] = []
        for path in rung.evidence_paths:
            file_path = self.evidence_root / path
            if not file_path.is_file():
                missing.append(path)
                continue
            digests[path] = _sha256_bytes(file_path.read_bytes())
        return digests, tuple(missing)

    def _revalidate_lower_rung(
        self, rung: RungSpec, record: dict[str, Any]
    ) -> tuple[str, tuple[tuple[str, str, str, str], ...], dict[str, str]]:
        """Recompute a recorded rung's evidence FROM BYTES; compare to record.

        Returns (status in _RUNG_DOMAIN, drift entries, recomputed digests).
        A recorded digest that no longer matches its source is the failure
        case; it is reported, never repaired.
        """
        drift: list[tuple[str, str, str, str]] = []
        recorded_ordinal = record.get("ordinal")
        if recorded_ordinal != rung.ordinal:
            drift.append(
                (rung.rung_id, "ordinal", str(recorded_ordinal), str(rung.ordinal))
            )
        recorded_prefix = record.get("ladder_prefix_sha256")
        current_prefix = self._ladder_prefix_sha256(rung.ordinal)
        if recorded_prefix != current_prefix:
            drift.append(
                (rung.rung_id, "ladder_prefix", str(recorded_prefix), current_prefix)
            )
        recorded_evidence = record.get("evidence")
        if not isinstance(recorded_evidence, dict) or set(
            recorded_evidence
        ) != set(rung.evidence_paths):
            drift.append(
                (
                    rung.rung_id,
                    "evidence_keys",
                    ",".join(sorted(recorded_evidence or {})),
                    ",".join(sorted(rung.evidence_paths)),
                )
            )
            return "drifted", tuple(drift), {}
        recomputed: dict[str, str] = {}
        for path in rung.evidence_paths:
            file_path = self.evidence_root / path
            if not file_path.is_file():
                drift.append(
                    (rung.rung_id, path, str(recorded_evidence[path]), "ABSENT")
                )
                continue
            digest = _sha256_bytes(file_path.read_bytes())
            recomputed[path] = digest
            if digest != recorded_evidence[path]:
                drift.append(
                    (rung.rung_id, path, str(recorded_evidence[path]), digest)
                )
        if drift:
            return "drifted", tuple(drift), recomputed
        return "validated", (), recomputed

    # -- the advance --------------------------------------------------------

    def advance(
        self,
        to_rung_id: str,
        gate_executions: tuple[GateExecution, ...] = (),
    ) -> AdvanceResult:
        target = self._by_id.get(to_rung_id)
        if target is None:
            raise ValueError(f"unknown rung: {to_rung_id}")
        provided: dict[str, GateExecution] = {}
        for execution in gate_executions:
            if not isinstance(execution, GateExecution):
                raise ValueError(
                    "gate_executions must contain GateExecution records"
                )
            if execution.gate_id not in target.gate_ids:
                raise ValueError(
                    f"execution for undeclared gate: {execution.gate_id}"
                )
            if execution.gate_id in provided:
                raise ValueError(
                    f"duplicate gate execution: {execution.gate_id}"
                )
            provided[execution.gate_id] = execution

        # Measurements.  Each operation runs in Python (hashing bytes, walking
        # the chain, parsing rows); each OUTCOME is an enumerated value that
        # the finite spec pins and the solvers decide over.
        ledger_ok, ledger_reason = self.ledger.verify()
        ledger_state = "intact" if ledger_ok else "broken"

        records = self.recorded_receipts() if ledger_ok else ()
        recorded_ids = tuple(record.get("rung_id", "") for record in records)
        chain_state = (
            "prefix_of_ladder"
            if ledger_ok and _is_prefix(recorded_ids, self._declared_ids)
            else "diverged"
        )
        latest_by_id: dict[str, dict[str, Any]] = {}
        for record in records:
            identifier = record.get("rung_id")
            if isinstance(identifier, str):
                latest_by_id[identifier] = record

        if to_rung_id in recorded_ids:
            extension_state = "already_recorded"
        elif target.ordinal == len(recorded_ids):
            extension_state = "next"
        else:
            extension_state = "out_of_order"

        rung_states: dict[str, str] = {}
        missing_rungs: list[str] = []
        drifted: list[tuple[str, str, str, str]] = []
        revalidated_evidence: dict[str, dict[str, str]] = {}
        for lower in self.ladder[: target.ordinal]:
            record = latest_by_id.get(lower.rung_id)
            if record is None:
                rung_states[lower.rung_id] = "missing"
                missing_rungs.append(lower.rung_id)
                continue
            status, drift_entries, recomputed = self._revalidate_lower_rung(
                lower, record
            )
            rung_states[lower.rung_id] = status
            drifted.extend(drift_entries)
            if status == "validated":
                revalidated_evidence[lower.rung_id] = recomputed

        gate_states: dict[str, str] = {}
        missing_gates: list[str] = []
        failed_gates: list[str] = []
        for gate_id in target.gate_ids:
            execution = provided.get(gate_id)
            if execution is None:
                gate_states[gate_id] = "declared_only"
                missing_gates.append(gate_id)
            elif execution.verdict == "PASS":
                gate_states[gate_id] = "executed_pass"
            else:
                gate_states[gate_id] = "executed_fail"
                failed_gates.append(gate_id)

        own_digests, missing_evidence = self._evidence_digests(target)
        evidence_state = "present" if not missing_evidence else "absent"

        # Finite encoding.  Variables are particulars with enumerated domains;
        # constraints pin the measured value of each and require the
        # precondition value.  dual_solve (z3 + cvc5 + bounded enumeration,
        # three definite agreeing votes) IS the admissibility decision.
        measured: dict[str, tuple[tuple[str, ...], str]] = {
            "ledger": (_LEDGER_DOMAIN, ledger_state),
            "chain": (_CHAIN_DOMAIN, chain_state),
            "extension": (_EXTENSION_DOMAIN, extension_state),
            "evidence": (_EVIDENCE_DOMAIN, evidence_state),
        }
        for rung_id, state in rung_states.items():
            measured[f"rung::{rung_id}"] = (_RUNG_DOMAIN, state)
        for gate_id, state in gate_states.items():
            measured[f"gate::{gate_id}"] = (_GATE_DOMAIN, state)
        required: dict[str, str] = {
            "ledger": "intact",
            "chain": "prefix_of_ladder",
            "extension": "next",
            "evidence": "present",
        }
        for rung_id in rung_states:
            required[f"rung::{rung_id}"] = "validated"
        for gate_id in gate_states:
            required[f"gate::{gate_id}"] = "executed_pass"

        spec: dict[str, Any] = {
            "variables": {
                name: list(domain) for name, (domain, _value) in measured.items()
            },
            "constraints": [
                {
                    "op": "eq",
                    "left": {"var": name},
                    "right": {"const": value},
                }
                for name, (_domain, value) in measured.items()
            ]
            + [
                {
                    "op": "eq",
                    "left": {"var": name},
                    "right": {"const": value},
                }
                for name, value in required.items()
            ],
        }
        decision = dual_solve(spec)

        def refusal(state: str, reason: str) -> AdvanceResult:
            return AdvanceResult(
                state=state,
                rung_id=to_rung_id,
                reason=reason,
                missing_rungs=tuple(missing_rungs),
                missing_gates=tuple(missing_gates),
                failed_gates=tuple(failed_gates),
                missing_evidence=missing_evidence,
                drifted=tuple(drifted),
                decision=decision,
                spec=spec,
                receipt_line_sha256=None,
            )

        if not decision.get("agree", False):
            disagreement = decision.get("disagreement", {})
            return refusal(
                HOLD,
                "DECIDERS_NOT_IN_AGREEMENT:"
                + str(disagreement.get("reason", "unknown")),
            )
        admissible = decision["z3"] == "BOUNDED_SAT"

        if not admissible:
            # The refusal KIND is named by fixed precedence over the same
            # enumerated measurements the solvers just refused on.
            if ledger_state == "broken":
                return refusal(
                    INVARIANT_VIOLATION, f"LEDGER_BROKEN:{ledger_reason}"
                )
            if chain_state == "diverged":
                return refusal(
                    INVARIANT_VIOLATION,
                    "CHAIN_DIVERGED:recorded rung sequence is not a prefix"
                    " of the declared ladder",
                )
            if drifted:
                names = ",".join(sorted({entry[0] for entry in drifted}))
                return refusal(
                    INVARIANT_VIOLATION, f"RUNG_EVIDENCE_DRIFT:{names}"
                )
            if missing_rungs:
                return refusal(
                    PARKED, "MISSING_RUNG_RECEIPT:" + ",".join(missing_rungs)
                )
            if missing_evidence:
                return refusal(
                    PARKED, "MISSING_EVIDENCE:" + ",".join(missing_evidence)
                )
            if missing_gates:
                return refusal(
                    PARKED, "GATE_NOT_EXECUTED:" + ",".join(missing_gates)
                )
            if failed_gates:
                return refusal(
                    BLOCKED, "GATE_EXECUTED_FAIL:" + ",".join(failed_gates)
                )
            if extension_state == "already_recorded":
                return refusal(BLOCKED, "RUNG_ALREADY_RECORDED")
            return refusal(HOLD, "UNSAT_WITHOUT_CLASSIFIED_CAUSE")

        # Defensive cross-check: a SAT verdict with any observed cause is a
        # measurement/decision mismatch.  Fail closed rather than advance.
        if (
            missing_rungs
            or missing_gates
            or failed_gates
            or missing_evidence
            or drifted
            or ledger_state != "intact"
            or chain_state != "prefix_of_ladder"
            or extension_state != "next"
        ):
            return refusal(HOLD, "DECISION_MEASUREMENT_MISMATCH")

        record = {
            "schema": RUNG_RECEIPT_SCHEMA,
            "rung_id": target.rung_id,
            "ordinal": target.ordinal,
            "ladder_prefix_sha256": self._ladder_prefix_sha256(target.ordinal),
            "evidence": dict(own_digests),
            "gate_executions": [
                provided[gate_id].to_dict() for gate_id in target.gate_ids
            ],
            "revalidated": dict(rung_states),
            "revalidated_evidence": revalidated_evidence,
            "decision": decision,
            "decision_spec": spec,
            "decision_spec_sha256": _sha256_bytes(canonical_json(spec)),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "promotion_allowed": False,
        }
        line_sha256 = self.ledger.append(record)
        return AdvanceResult(
            state=ADVANCED,
            rung_id=to_rung_id,
            reason="ADVANCED",
            missing_rungs=(),
            missing_gates=(),
            failed_gates=(),
            missing_evidence=(),
            drifted=(),
            decision=decision,
            spec=spec,
            receipt_line_sha256=line_sha256,
        )
