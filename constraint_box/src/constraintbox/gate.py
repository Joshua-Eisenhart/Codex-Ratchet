"""Standalone entry point for the external ClaimGate verification chain.

Process exit codes and the strict v2 JSON report are a paired public contract.
Neither one is authoritative by itself:

* 0: ``ADMITTED`` — the chain ran and admitted the claim.
* 1: ``REFUSED`` — the chain ran and refused the claim.
* 2: constraintbox usage or I/O failure before the chain starts (``GateError``).
* 3: ``INSUFFICIENT_DEPTH`` — the chain ran but required depth was not met.
* 4: ``PARKED`` — a required checker is unavailable, not a claim failure.
* 5: ``EVALUATION_ERROR`` — the chain started but failed to evaluate.

In particular, chain exit 2 is an evaluation error (exit 5 here); exit 2 is
reserved for failures of the constraintbox invocation itself.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


CHAIN_RELATIVE_PATH = "claimgate_plugin/claim_verify.py"
REGISTRY_RELATIVE_PATH = "claimgate_plugin/gate_registry.json"
GATE_EXIT_CODES = {
    "ADMITTED": 0,
    "REFUSED": 1,
    "INSUFFICIENT_DEPTH": 3,
    "PARKED": 4,
    "EVALUATION_ERROR": 5,
}
CHAIN_VERDICTS_BY_EXIT = {
    0: frozenset({"VERIFIED"}),
    1: frozenset({"REJECTED"}),
    3: frozenset({"INSUFFICIENT_DEPTH", "PENDING_EVIDENCE"}),
}
REPORT_KEYS = frozenset(
    {
        "tool",
        "version",
        "receipt",
        "claim_kind",
        "verdict",
        "execution_evidence",
        "required_tiers",
        "verified_tiers",
        "unverified_tiers",
        "required_unmet",
        "tamper_events",
        "tier_results",
        "claim_verdicts",
    }
)
TIERS = ("tier0", "tier1", "tier2", "tier3", "tier4")
TIER_STATUSES = frozenset({"PASS", "FAIL", "SKIP", "ERROR"})


class GateError(Exception):
    """The requested gate evaluation cannot be started."""


class _ChainReportError(ValueError):
    """The ClaimGate process did not emit its exact structured-report contract."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _ChainReportError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise _ChainReportError(f"non-finite JSON value: {value}")


def _require_exact_keys(
    value: dict[str, Any],
    expected: frozenset[str],
    *,
    context: str,
) -> None:
    actual = frozenset(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise _ChainReportError(
            f"{context} keys differ: missing={missing}, extra={extra}"
        )


def _require_tier_list(report: dict[str, Any], key: str) -> list[str]:
    value = report[key]
    if not isinstance(value, list) or any(
        not isinstance(item, str) or item not in TIERS for item in value
    ):
        raise _ChainReportError(f"{key} must be a list of known tier names")
    if len(value) != len(set(value)):
        raise _ChainReportError(f"{key} contains duplicate tiers")
    return value


def _parse_chain_report(
    stdout: str,
    *,
    receipt: Path,
    chain_root: Path,
) -> dict[str, Any]:
    try:
        parsed = json.loads(
            stdout,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (json.JSONDecodeError, _ChainReportError) as exc:
        raise _ChainReportError(f"invalid JSON report: {exc}") from exc
    if not isinstance(parsed, dict):
        raise _ChainReportError("report root must be a JSON object")
    report: dict[str, Any] = parsed
    _require_exact_keys(report, REPORT_KEYS, context="report")

    if report["tool"] != "claim_verify":
        raise _ChainReportError("report tool must be exactly 'claim_verify'")
    if type(report["version"]) is not int or report["version"] != 2:
        raise _ChainReportError("report version must be integer 2")
    if not isinstance(report["receipt"], str) or not report["receipt"]:
        raise _ChainReportError("report receipt must be a non-empty string")
    reported_receipt = Path(report["receipt"])
    if not reported_receipt.is_absolute():
        reported_receipt = chain_root / reported_receipt
    if reported_receipt.resolve() != receipt:
        raise _ChainReportError("report receipt does not name the evaluated receipt")
    if report["claim_kind"] is not None and not isinstance(
        report["claim_kind"], str
    ):
        raise _ChainReportError("claim_kind must be a string or null")
    if not isinstance(report["verdict"], str) or report["verdict"] not in {
        "VERIFIED",
        "REJECTED",
        "INSUFFICIENT_DEPTH",
        "PENDING_EVIDENCE",
    }:
        raise _ChainReportError("report verdict is not recognized")
    if (
        not isinstance(report["execution_evidence"], str)
        or not report["execution_evidence"]
    ):
        raise _ChainReportError("execution_evidence must be a non-empty string")

    required_tiers = _require_tier_list(report, "required_tiers")
    verified_tiers = _require_tier_list(report, "verified_tiers")
    unverified_tiers = _require_tier_list(report, "unverified_tiers")
    required_unmet = _require_tier_list(report, "required_unmet")
    if not required_tiers or required_tiers != sorted(required_tiers):
        raise _ChainReportError(
            "required_tiers must be non-empty and canonically ordered"
        )

    tier_results = report["tier_results"]
    if not isinstance(tier_results, list) or len(tier_results) != len(TIERS):
        raise _ChainReportError("tier_results must contain exactly five rows")
    result_by_tier: dict[str, dict[str, Any]] = {}
    tier_result_keys = frozenset({"tier", "status", "evidence_ref", "detail"})
    for index, row in enumerate(tier_results):
        if not isinstance(row, dict):
            raise _ChainReportError(f"tier_results[{index}] must be an object")
        _require_exact_keys(
            row,
            tier_result_keys,
            context=f"tier_results[{index}]",
        )
        tier = row["tier"]
        if not isinstance(tier, str) or tier not in TIERS:
            raise _ChainReportError(f"tier_results[{index}].tier is unknown")
        if tier in result_by_tier:
            raise _ChainReportError(f"tier_results repeats {tier}")
        if (
            not isinstance(row["status"], str)
            or row["status"] not in TIER_STATUSES
        ):
            raise _ChainReportError(f"tier_results[{index}].status is unknown")
        if row["evidence_ref"] is not None and not isinstance(
            row["evidence_ref"], str
        ):
            raise _ChainReportError(
                f"tier_results[{index}].evidence_ref must be a string or null"
            )
        if not isinstance(row["detail"], str):
            raise _ChainReportError(
                f"tier_results[{index}].detail must be a string"
            )
        result_by_tier[tier] = row
    if tuple(row["tier"] for row in tier_results) != TIERS:
        raise _ChainReportError("tier_results must be ordered tier0 through tier4")

    expected_verified = [
        tier for tier in TIERS if result_by_tier[tier]["status"] == "PASS"
    ]
    expected_unverified = [
        tier for tier in TIERS if result_by_tier[tier]["status"] == "SKIP"
    ]
    expected_unmet = {
        tier
        for tier in required_tiers
        if result_by_tier[tier]["status"] != "PASS"
    }
    if verified_tiers != expected_verified:
        raise _ChainReportError("verified_tiers contradicts tier_results")
    if unverified_tiers != expected_unverified:
        raise _ChainReportError("unverified_tiers contradicts tier_results")
    if set(required_unmet) != expected_unmet:
        raise _ChainReportError("required_unmet contradicts tier_results")
    if set(verified_tiers) & set(unverified_tiers):
        raise _ChainReportError("a tier cannot be both verified and unverified")

    tamper_events = report["tamper_events"]
    if not isinstance(tamper_events, list):
        raise _ChainReportError("tamper_events must be a list")
    tamper_keys = frozenset({"tier", "path", "change"})
    for index, event in enumerate(tamper_events):
        if not isinstance(event, dict):
            raise _ChainReportError(f"tamper_events[{index}] must be an object")
        _require_exact_keys(
            event,
            tamper_keys,
            context=f"tamper_events[{index}]",
        )
        if event["tier"] not in TIERS:
            raise _ChainReportError(f"tamper_events[{index}].tier is unknown")
        if not isinstance(event["path"], str) or not event["path"]:
            raise _ChainReportError(
                f"tamper_events[{index}].path must be a non-empty string"
            )
        if (
            not isinstance(event["change"], str)
            or event["change"] not in {"created", "modified"}
        ):
            raise _ChainReportError(
                f"tamper_events[{index}].change is not recognized"
            )

    claim_verdicts = report["claim_verdicts"]
    if not isinstance(claim_verdicts, list):
        raise _ChainReportError("claim_verdicts must be a list")
    claim_keys = frozenset({"claim", "verdict", "evidence_ref"})
    expected_claim_verdicts: list[dict[str, Any]] = []
    for tier in TIERS:
        row = result_by_tier[tier]
        if row["status"] in {"PASS", "FAIL"}:
            expected_claim_verdicts.append(
                {
                    "claim": tier,
                    "verdict": "pass" if row["status"] == "PASS" else "fail",
                    "evidence_ref": row["evidence_ref"],
                }
            )
    for index, claim in enumerate(claim_verdicts):
        if not isinstance(claim, dict):
            raise _ChainReportError(f"claim_verdicts[{index}] must be an object")
        _require_exact_keys(
            claim,
            claim_keys,
            context=f"claim_verdicts[{index}]",
        )
        if claim["claim"] not in TIERS:
            raise _ChainReportError(f"claim_verdicts[{index}].claim is unknown")
        if (
            not isinstance(claim["verdict"], str)
            or claim["verdict"] not in {"pass", "fail"}
        ):
            raise _ChainReportError(
                f"claim_verdicts[{index}].verdict is not recognized"
            )
        if claim["evidence_ref"] is not None and not isinstance(
            claim["evidence_ref"], str
        ):
            raise _ChainReportError(
                f"claim_verdicts[{index}].evidence_ref must be a string or null"
            )
    if claim_verdicts != expected_claim_verdicts:
        raise _ChainReportError("claim_verdicts contradicts tier_results")

    has_failure = any(
        row["status"] in {"FAIL", "ERROR"} for row in tier_results
    )
    if (tamper_events or has_failure) and report["verdict"] != "REJECTED":
        raise _ChainReportError("failed or tampered report must be REJECTED")
    if report["verdict"] == "REJECTED" and not (tamper_events or has_failure):
        raise _ChainReportError("REJECTED report must name a failure or tamper event")
    if report["verdict"] in {"VERIFIED", "PENDING_EVIDENCE"} and required_unmet:
        raise _ChainReportError(
            f"{report['verdict']} report cannot have unmet required tiers"
        )
    return report


def _result(
    receipt: Path,
    receipt_sha256: str,
    registry_sha256: str,
    disposition: str,
    chain_exit_code: int | None,
    report: dict[str, Any] | None,
    chain_root: Path,
    package_root: Path,
    tier0_checker: Path | None,
) -> dict:
    return {
        "schema": "constraintbox.gate.v1",
        "receipt": str(receipt),
        "receipt_sha256": receipt_sha256,
        "disposition": disposition,
        "chain": CHAIN_RELATIVE_PATH,
        "chain_exit_code": chain_exit_code,
        "chain_verdict": (
            report.get("verdict")
            if report is not None and isinstance(report.get("verdict"), str)
            else None
        ),
        "chain_root": str(chain_root),
        "chain_root_inside_box": (
            chain_root == package_root or package_root in chain_root.parents
        ),
        "tier0_checker": str(tier0_checker) if tier0_checker is not None else None,
        "claim_kind": report.get("claim_kind") if report is not None else None,
        "tier_source": "gate_registry.json",
        "registry": REGISTRY_RELATIVE_PATH,
        "registry_sha256": registry_sha256,
        "required_tiers": report.get("required_tiers", []) if report is not None else [],
        "verified_tiers": report.get("verified_tiers", []) if report is not None else [],
        "unverified_tiers": (
            report.get("unverified_tiers", []) if report is not None else []
        ),
        "required_unmet": report.get("required_unmet", []) if report is not None else [],
        "tier_results": report.get("tier_results", []) if report is not None else [],
        "tamper_events": report.get("tamper_events", []) if report is not None else [],
        "promotion_allowed": False,
    }


def _resolve_chain_root(chain_directory: Path) -> Path:
    """Resolve a ClaimGate chain root without requiring a parent checkout.

    A bundled ClaimGate lives at ``<box-root>/claimgate_plugin``.  Its sibling
    ``claimgate.mjs`` and registry are the exact local authority for this
    invocation, so that directory's parent is the chain root even when the
    bundle was extracted outside a Git checkout.  Other chain locations retain
    the legacy repository-root search.
    """
    directory = Path(os.path.abspath(chain_directory))
    if (
        directory.name == "claimgate_plugin"
        and (directory / "claim_verify.py").is_file()
        and (directory / "claimgate.mjs").is_file()
        and (directory / "gate_registry.json").is_file()
    ):
        return directory.parent
    filesystem_root = Path(directory.anchor)
    while directory != filesystem_root:
        if (directory / ".git").is_dir() or (directory / "system_v8").is_dir():
            return directory
        directory = directory.parent
    return Path(os.getcwd())


def _tier0_checker(chain_root: Path) -> tuple[Path | None, tuple[Path, Path]]:
    python_checker = chain_root / "claimgate" / "claimgate.py"
    node_checker = chain_root / "claimgate_plugin" / "claimgate.mjs"
    if python_checker.is_file():
        return python_checker, (python_checker, node_checker)
    if node_checker.is_file():
        return node_checker, (python_checker, node_checker)
    return None, (python_checker, node_checker)


def run_gate(receipt: Path, *, chain: Path | None = None) -> dict:
    receipt = Path(receipt).resolve()
    package_root = Path(__file__).resolve().parents[2]
    chain_path = (
        Path(chain).resolve()
        if chain is not None
        else package_root / CHAIN_RELATIVE_PATH
    )
    registry_path = package_root / REGISTRY_RELATIVE_PATH

    if not receipt.is_file():
        raise GateError(f"missing receipt: {receipt}")
    if not chain_path.is_file():
        raise GateError(f"missing chain: {chain_path}")

    receipt_sha256 = _sha256(receipt)
    registry_sha256 = _sha256(registry_path)
    chain_root = _resolve_chain_root(chain_path.parent)
    tier0_checker, checked_paths = _tier0_checker(chain_root)
    if tier0_checker is None:
        result = _result(
            receipt,
            receipt_sha256,
            registry_sha256,
            "PARKED",
            None,
            None,
            chain_root,
            package_root,
            None,
        )
        result["reason"] = (
            f"tier0 checker unavailable under resolved chain root {chain_root}; "
            f"looked for {checked_paths[0]} and {checked_paths[1]}"
        )
        return result

    try:
        completed = subprocess.run(
            [sys.executable, str(chain_path), str(receipt)],
            capture_output=True,
            text=True,
            timeout=900,
        )
    except subprocess.TimeoutExpired:
        result = _result(
            receipt,
            receipt_sha256,
            registry_sha256,
            "EVALUATION_ERROR",
            None,
            None,
            chain_root,
            package_root,
            tier0_checker,
        )
        result["chain_stderr"] = "chain timed out after 900 seconds"
        result["chain_stdout_head"] = ""
        return result

    code = completed.returncode
    try:
        report = _parse_chain_report(
            completed.stdout,
            receipt=receipt,
            chain_root=chain_root,
        )
        report_error = None
    except _ChainReportError as exc:
        report = None
        report_error = str(exc)

    verdict = report["verdict"] if report is not None else None
    if report is not None and verdict in CHAIN_VERDICTS_BY_EXIT.get(code, ()):
        if code == 0:
            disposition = "ADMITTED"
        elif code == 1:
            disposition = "REFUSED"
        else:
            disposition = "INSUFFICIENT_DEPTH"
    else:
        disposition = "EVALUATION_ERROR"

    result = _result(
        receipt,
        receipt_sha256,
        registry_sha256,
        disposition,
        code,
        report,
        chain_root,
        package_root,
        tier0_checker,
    )
    if report_error is not None:
        result["chain_report_error"] = report_error
        result["chain_stderr"] = completed.stderr[:500]
        result["chain_stdout_head"] = completed.stdout[:500]
    elif disposition == "EVALUATION_ERROR":
        allowed = sorted(CHAIN_VERDICTS_BY_EXIT.get(code, ()))
        result["chain_report_error"] = (
            f"chain exit {code} is inconsistent with verdict {verdict}; "
            f"allowed verdicts={allowed}"
        )
        result["chain_stderr"] = completed.stderr[:500]
        result["chain_stdout_head"] = completed.stdout[:500]
    return result
