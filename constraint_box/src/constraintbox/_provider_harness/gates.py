"""Deterministic admission gate for LLM-run receipts.

This is the DETERMINISTIC PRUNE layer: same receipt in -> identical GateResult
out.  No clock, no random in the verdict.  The gate wraps at least one REAL
check (receipt-schema validity + py_compile of any .py artifact) and enforces
the no-self-grading rule: a receipt may not be GRANTED a ``gate_ceiling_rung``
above ``scratch_diagnostic`` unless ``audit_required`` is satisfied by a
SEPARATE auditor receipt (a different produced_by author + a different task_id).

The ladder is ranked over ``gate_ceiling_rung`` -- the harness promotion field --
NEVER over ``claim_ceiling`` (which is FAMILY free-text scope; ranking a prose
sentence would crash or mislabel.  box-viii L2, 2026-06-15).

A test is load-bearing only if it COULD fail.  Each check records ``could_fail``
so a by-construction always-true check cannot masquerade as evidence.
"""
from __future__ import annotations

import json
import os
import py_compile
import tempfile
from pathlib import Path
from typing import Optional

from .types import (
    GATE_CEILING_LADDER,
    VALID_CLASSIFICATIONS,
    VALID_STATUSES,
    GateResult,
    ModelReceipt,
    RECEIPT_SCHEMA,
    sha256_text,
)
from .signing import verify_payload, normalize_identity

# The single status the gate treats as an admissible successful run.
ADMISSIBLE_STATUS = "success"


def _rung_rank(rung: str) -> int:
    try:
        return GATE_CEILING_LADDER.index(rung)
    except ValueError:
        return -1


def _canonical_receipt_json(receipt: ModelReceipt) -> str:
    return json.dumps(receipt.to_dict(), sort_keys=True, indent=2)


def _check(name: str, passed: bool, could_fail: bool, detail: str = "") -> dict:
    return {"name": name, "passed": passed, "could_fail": could_fail, "detail": detail}


def _schema_valid(receipt: ModelReceipt) -> tuple[bool, str]:
    """REAL check: the receipt carries the expected schema id, a valid
    classification, a valid status, and a gate_ceiling_rung ON the ladder.
    COULD fail (a malformed receipt fails)."""
    if receipt.schema != RECEIPT_SCHEMA:
        return False, f"schema={receipt.schema!r} != {RECEIPT_SCHEMA!r}"
    if receipt.classification not in VALID_CLASSIFICATIONS:
        return False, f"classification={receipt.classification!r} not in {VALID_CLASSIFICATIONS}"
    if receipt.status not in VALID_STATUSES:
        return False, f"status={receipt.status!r} not in {VALID_STATUSES}"
    if receipt.gate_ceiling_rung not in GATE_CEILING_LADDER:
        return False, f"gate_ceiling_rung={receipt.gate_ceiling_rung!r} not on ladder"
    return True, "schema+classification+status+rung valid"


def _artifacts_compile(receipt: ModelReceipt) -> tuple[Optional[bool], str]:
    """REAL check: py_compile every .py artifact on the receipt.

    Returns (None, ...) when there are no .py artifacts (check is N/A -- it is
    NOT vacuously passed, since a vacuous pass is not a test).  Returns
    (True/False, ...) only when a .py artifact actually exists to compile.

    The compiled .pyc goes to a UNIQUE, CLOSED tempfile path per artifact so
    concurrent gate runs cannot collide on a shared cfile (box-viii L5 fix:
    the old NamedTemporaryFile(delete=True) handle was reused across artifacts
    and could race).  We create+close the temp, pass its path as cfile, then
    remove it ourselves.
    """
    py_artifacts = [
        p for p in receipt.artifact_paths if p.endswith(".py") and Path(p).is_file()
    ]
    if not py_artifacts:
        return None, "no .py artifacts to compile"
    failures = []
    for p in py_artifacts:
        fd, cpath = tempfile.mkstemp(suffix=".pyc")
        os.close(fd)  # unique, closed file -- py_compile writes to cpath
        try:
            py_compile.compile(p, cfile=cpath, doraise=True)
        except py_compile.PyCompileError as exc:
            failures.append(f"{p}: {exc.msg}")
        finally:
            try:
                os.unlink(cpath)
            except OSError:
                pass
    if failures:
        return False, "; ".join(failures)
    return True, f"compiled {len(py_artifacts)} artifact(s)"


def gate(
    receipt: ModelReceipt,
    *,
    audit_receipts: Optional[list[ModelReceipt]] = None,
) -> GateResult:
    """Deterministic verdict on a receipt.

    ``audit_receipts`` is the set of OTHER receipts available to satisfy an
    audit requirement.  An audit receipt is valid for this receipt iff it has a
    DIFFERENT task_id (no self-grading), a DIFFERENT produced_by author,
    role == "auditor", status == "success", and it names this receipt's task_id
    in its input_refs.
    """
    audit_receipts = audit_receipts or []
    checks: list[dict] = []
    reasons: list[str] = []
    admitted = True

    # --- REAL check 1: receipt schema validity (could fail) ---
    schema_ok, schema_detail = _schema_valid(receipt)
    checks.append(_check("receipt_schema_valid", schema_ok, True, schema_detail))
    if not schema_ok:
        admitted = False
        reasons.append(f"schema_invalid: {schema_detail}")

    # --- REAL check 2: py_compile of any .py artifact (could fail) ---
    compile_ok, compile_detail = _artifacts_compile(receipt)
    if compile_ok is None:
        # N/A: recorded honestly, NOT counted as a passed test.
        checks.append(_check("artifacts_py_compile", True, False, compile_detail))
    else:
        checks.append(_check("artifacts_py_compile", compile_ok, True, compile_detail))
        if not compile_ok:
            admitted = False
            reasons.append(f"artifact_compile_failed: {compile_detail}")

    # --- Status check: only a successful run can be admitted (could fail) ---
    status_ok = receipt.status == ADMISSIBLE_STATUS
    checks.append(
        _check(
            "status_success",
            status_ok,
            True,
            f"status={receipt.status}, returncode={receipt.returncode}",
        )
    )
    if not status_ok:
        admitted = False
        reasons.append(f"status_not_success: {receipt.status}")

    # --- Signature integrity at BASE (could fail): a PRESENT-but-INVALID signature is tampering and
    # is NOT admitted at ANY rung. An UNSIGNED receipt (signature is None) is allowed to gate-admit
    # only at scratch_diagnostic (it can never be PROMOTED -- see _audit_satisfied -- and the
    # controller adapter will not mark it PASS). box-viii L2: the real fleet showed signature-verify
    # only fired on the promotion path, so a tampered scratch receipt slipped through. ---
    sig_present = receipt.signature is not None
    sig_valid = sig_present and verify_payload(receipt.to_dict())
    if sig_present and not sig_valid:
        admitted = False
        reasons.append("signature_invalid: receipt tampered after signing")
    checks.append(_check(
        "signature_valid_if_present",
        (not sig_present) or sig_valid,
        True,
        "signed+verified" if sig_valid else ("unsigned (scratch-only, adapter will not PASS)" if not sig_present else "TAMPERED"),
    ))

    # --- No-self-grading / audit-required enforcement (could fail) ---
    wants_promotion = _rung_rank(receipt.gate_ceiling_rung) > _rung_rank("scratch_diagnostic")
    audit_satisfied = _audit_satisfied(receipt, audit_receipts)
    if wants_promotion:
        check_pass = audit_satisfied
        checks.append(
            _check(
                "audit_required_satisfied_by_separate_auditor",
                check_pass,
                True,
                _audit_detail(receipt, audit_receipts),
            )
        )
        if not audit_satisfied:
            admitted = False
            reasons.append(
                "self_promotion_blocked: gate_ceiling_rung above scratch_diagnostic "
                "requires a SEPARATE auditor receipt (no self-grading)"
            )
    else:
        # At scratch_diagnostic no audit is needed; record the check as N/A.
        checks.append(
            _check(
                "audit_required_satisfied_by_separate_auditor",
                True,
                False,
                "gate_ceiling_rung=scratch_diagnostic: no audit required",
            )
        )

    # --- Promotion/formal-admission must stay false unless audited (could fail) ---
    if (receipt.promotion_allowed or receipt.formal_admission_allowed) and not audit_satisfied:
        admitted = False
        checks.append(
            _check(
                "promotion_flags_require_audit",
                False,
                True,
                "promotion_allowed/formal_admission_allowed set without a separate audit receipt",
            )
        )
        reasons.append("promotion_flags_without_audit")
    else:
        checks.append(
            _check(
                "promotion_flags_require_audit",
                True,
                True,
                f"promotion_allowed={receipt.promotion_allowed}, "
                f"formal_admission_allowed={receipt.formal_admission_allowed}",
            )
        )

    # The granted rung: full requested rung only if admitted AND audited;
    # otherwise the gate grants only scratch_diagnostic.
    if admitted and (not wants_promotion or audit_satisfied):
        granted_rung = receipt.gate_ceiling_rung
    else:
        granted_rung = "scratch_diagnostic"

    if admitted and not reasons:
        reasons.append("all_checks_passed")

    receipt_sha = sha256_text(_canonical_receipt_json(receipt))
    return GateResult(
        schema=GateResult.GATE_SCHEMA,
        task_id=receipt.task_id,
        receipt_sha256=receipt_sha,
        admitted=admitted,
        verdict="admit" if admitted else "reject",
        reasons=reasons,
        checks=checks,
        granted_rung=granted_rung,
    )


def _audit_satisfied(receipt: ModelReceipt, audit_receipts: list[ModelReceipt]) -> bool:
    # The WORK receipt must itself be validly SIGNED by the trusted boundary and name its author.
    # An unsigned / hand-edited receipt is forgeable, so it can never be promoted (box-viii L1c:
    # produced_by is mintable free text until the signature binds it; verified by the real fleet).
    if not normalize_identity(receipt.produced_by):
        return False
    if not verify_payload(receipt.to_dict()):
        return False
    for a in audit_receipts:
        if (
            a.task_id != receipt.task_id  # different task
            and a.role == "auditor"
            and a.status == ADMISSIBLE_STATUS
            and receipt.task_id in a.input_refs  # the auditor actually examined this task
            and normalize_identity(a.produced_by)                                       # auditor author named
            and normalize_identity(a.produced_by) != normalize_identity(receipt.produced_by)  # DIFFERENT author label (normalized: trailing-space/case can't fake distinctness)
            and _producers_key_distinct(a, receipt)                                     # KEY-backed distinctness (executor/notary split): different per-identity key, not just a different label
            and verify_payload(a.to_dict())                                             # auditor receipt itself validly signed (not hand-forged)
            and _schema_valid(a)[0]                                                     # auditor receipt itself passes the gate's schema check (transitive validity)
        ):
            return True
    return False


def _producers_key_distinct(auditor: ModelReceipt, work: ModelReceipt) -> bool:
    """KEY-backed author distinctness for the executor/notary split.

    When both receipts carry a notary ``key_id``, the auditor must be signed under a DIFFERENT
    per-identity key than the work receipt -- so the SAME producer cannot self-promote by minting a
    fresh-task_id "auditor" receipt under its OWN key (same key_id == same producer).  If either
    receipt is a legacy single-key receipt (no key_id), this clause is a no-op and the label-based
    distinctness check above governs (backward compatible).
    """
    if auditor.key_id and work.key_id:
        return auditor.key_id != work.key_id
    return True


def _audit_detail(receipt: ModelReceipt, audit_receipts: list[ModelReceipt]) -> str:
    if _audit_satisfied(receipt, audit_receipts):
        return "separate completed auditor receipt referencing this task found"
    if not audit_receipts:
        return "no auditor receipts supplied"
    return (
        "no valid auditor receipt: need role=auditor, status=success, "
        f"different task_id, different produced_by, and input_refs containing {receipt.task_id!r}"
    )
