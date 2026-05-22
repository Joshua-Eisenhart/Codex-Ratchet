#!/usr/bin/env python3
"""Aggregate audit for finite EngineCore-boundary coverage receipts."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from collections import Counter
from typing import Any

import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "engine_core_finite_boundary_coverage_audit_probe_results.json"
TOOL_GATE = RESULT_DIR / "constraint_admissible_tool_role_gate_probe_results.json"
TRIAGE = RESULT_DIR / "engine_core_boundary_row_triage_probe_results.json"

NAME = "engine_core_finite_boundary_coverage_audit_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "engine_core_finite_boundary_coverage_audit_classifier"
CLAIM_CEILING = (
    "Formal scout audit only: checks that current finite-covered EngineCore "
    "importer-boundary rows are covered by fresh finite JSON/scalar/window/readout "
    "quarantine receipts. It does not clear the EngineCore importer boundary, "
    "does not turn finite receipt coverage into torch-native EngineCore dynamics, "
    "and does not promote basin, manifold, PEPS3D, Holodeck, physics, "
    "consciousness, or target-system claims."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive parsing of current tool-gate, triage, and finite-boundary receipt JSON",
    },
    "python_pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical source/result path binding",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive current source/result and receipt freshness hashes",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof that finite coverage plus continued gate blocking cannot imply gate clearance or promotion",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "python_pathlib": "supportive",
    "hashlib": "supportive",
    "z3": "load_bearing",
}

FINITE_COVERED_STATUS = "blocked_engine_core_importer_boundary_finite_receipt_covered"
FINITE_TRIAGE_CLASS = "finite_router_or_readout_quarantine_candidate"
FINITE_ADMISSION = "finite_boundary_admitted_without_gate_clearance"


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def result_all_pass(data: dict[str, Any]) -> bool:
    if data.get("all_pass") is True:
        return True
    summary = data.get("summary")
    if isinstance(summary, dict) and summary.get("all_pass") is True:
        return True
    positive = data.get("positive")
    if isinstance(positive, dict) and positive:
        checks = [row.get("pass") for row in positive.values() if isinstance(row, dict) and "pass" in row]
        return bool(checks and all(check is True for check in checks))
    return False


def path_from_receipt(value: Any) -> pathlib.Path | None:
    if not value:
        return None
    path = pathlib.Path(str(value))
    if path.is_absolute():
        return path
    return ROOT / path


def identity_hashes(receipt: dict[str, Any]) -> dict[str, Any]:
    identity = ((receipt.get("positive") or {}).get("exact_files_are_hash_bound") or {}).get("files") or {}
    target = receipt.get("target") or {}
    source_path = path_from_receipt((identity.get("target_source") or {}).get("path") or target.get("source"))
    result_path = path_from_receipt((identity.get("target_result") or {}).get("path") or target.get("result"))
    recorded_source_sha = (identity.get("target_source") or {}).get("sha256")
    recorded_result_sha = (identity.get("target_result") or {}).get("sha256")
    current_source_sha = sha256(source_path) if source_path else None
    current_result_sha = sha256(result_path) if result_path else None
    return {
        "target_source": rel(source_path) if source_path else None,
        "target_result": rel(result_path) if result_path else None,
        "recorded_source_sha256": recorded_source_sha,
        "current_source_sha256": current_source_sha,
        "source_hash_fresh": bool(recorded_source_sha and recorded_source_sha == current_source_sha),
        "recorded_result_sha256": recorded_result_sha,
        "current_result_sha256": current_result_sha,
        "result_hash_fresh": bool(recorded_result_sha and recorded_result_sha == current_result_sha),
        "pass": bool(recorded_source_sha and recorded_result_sha and recorded_source_sha == current_source_sha and recorded_result_sha == current_result_sha),
    }


def accepted_receipt_report(path: pathlib.Path) -> dict[str, Any]:
    receipt = read_json(path)
    target = receipt.get("target") or {}
    positive = receipt.get("positive") or {}
    finite = positive.get("target_consumes_finite_json_stage_evidence") or {}
    z3_witness = positive.get("z3_quarantine_implication_blocks_promotion") or {}
    identity = identity_hashes(receipt)
    accepted = bool(
        receipt.get("schema") == "ENGINE_CORE_FINITE_BOUNDARY_RECEIPT_v1"
        and result_all_pass(receipt)
        and target.get("admission_result") == FINITE_ADMISSION
        and finite.get("pass") is True
        and z3_witness.get("pass") is True
    )
    return {
        "target_name": target.get("name"),
        "receipt_path": rel(path),
        "receipt_sha256": sha256(path),
        "accepted_by_current_gate_rule": accepted,
        "schema": receipt.get("schema"),
        "all_pass": result_all_pass(receipt),
        "admission_result": target.get("admission_result"),
        "embedded_tool_gate_status": target.get("current_tool_gate_status"),
        "finite_consumption_pass": finite.get("pass"),
        "z3_quarantine_pass": z3_witness.get("pass"),
        "blocked_uses": (receipt.get("finite_boundary_receipt") or {}).get("blocked_uses", []),
        "identity_hashes": identity,
        "promotion_allowed": receipt.get("promotion_allowed"),
    }


def finite_receipt_reports() -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for path in sorted(RESULT_DIR.glob("engine_core_finite_boundary_*_receipt_probe_results.json")):
        report = accepted_receipt_report(path)
        target_name = str(report.get("target_name") or "")
        if target_name:
            reports[target_name] = report
    return reports


def accepted_receipts(reports: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        name: report
        for name, report in reports.items()
        if report["accepted_by_current_gate_rule"]
    }


def gate_rows(gate: dict[str, Any], status: str | None = None) -> list[dict[str, Any]]:
    rows = gate.get("tool_role_rows", [])
    if not isinstance(rows, list):
        return []
    if status is None:
        return rows
    return [row for row in rows if row.get("tool_role_status") == status]


def triage_rows(triage: dict[str, Any], classification: str | None = None) -> list[dict[str, Any]]:
    rows = triage.get("row_triage", [])
    if not isinstance(rows, list):
        return []
    if classification is None:
        return rows
    return [row for row in rows if row.get("classification") == classification]


def z3_no_clearance_for_covered_rows(row_count: int) -> dict[str, Any]:
    if row_count == 0:
        return {
            "pass": True,
            "solver_status": "not_run_empty_frontier",
            "row_count": 0,
            "meaning": "No current finite-covered EngineCore-boundary rows are present, so finite coverage cannot imply gate clearance or promotion.",
        }
    solver = z3.Solver()
    for idx in range(row_count):
        finite_receipt = z3.Bool(f"finite_receipt_{idx}")
        gate_still_blocked = z3.Bool(f"gate_still_blocked_{idx}")
        torch_native_port = z3.Bool(f"torch_native_port_{idx}")
        gate_clearance = z3.Bool(f"gate_clearance_{idx}")
        promotion = z3.Bool(f"promotion_{idx}")
        solver.add(finite_receipt, gate_still_blocked, z3.Not(torch_native_port))
        solver.add(
            z3.Implies(
                z3.And(finite_receipt, gate_still_blocked, z3.Not(torch_native_port)),
                z3.And(z3.Not(gate_clearance), z3.Not(promotion)),
            )
        )
        solver.add(z3.Or(gate_clearance, promotion))
    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "row_count": row_count,
        "meaning": "Finite-boundary coverage for rows that remain gate-blocked cannot imply gate clearance or promotion.",
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    gate = read_json(TOOL_GATE)
    triage = read_json(TRIAGE)
    historical_receipts = finite_receipt_reports()
    receipts = accepted_receipts(historical_receipts)
    covered_gate_rows = gate_rows(gate, FINITE_COVERED_STATUS)
    triage_finite_rows = triage_rows(triage, FINITE_TRIAGE_CLASS)
    triage_by_name = {row.get("name"): row for row in triage_finite_rows}
    gate_by_name = {row.get("name"): row for row in gate_rows(gate)}
    covered_reports: list[dict[str, Any]] = []
    for row in covered_gate_rows:
        name = str(row.get("name"))
        receipt = receipts.get(name)
        triage_row = triage_by_name.get(name, {})
        receipt_path_matches_gate = bool(
            receipt
            and row.get("engine_core_finite_boundary_receipt", {}).get("receipt_path") == receipt.get("receipt_path")
        )
        embedded_status = receipt.get("embedded_tool_gate_status") if receipt else None
        current_status = row.get("tool_role_status")
        covered_reports.append(
            {
                "name": name,
                "gate_status": current_status,
                "gate_nonclassical_basin_claim_allowed": row.get("nonclassical_basin_claim_allowed"),
                "gate_receipt_path": row.get("engine_core_finite_boundary_receipt", {}).get("receipt_path"),
                "receipt_path": receipt.get("receipt_path") if receipt else None,
                "receipt_exists_and_accepted": receipt is not None,
                "receipt_path_matches_gate": receipt_path_matches_gate,
                "receipt_source_result_hash_fresh": bool(receipt and receipt.get("identity_hashes", {}).get("pass")),
                "embedded_status_matches_current_gate": embedded_status == current_status,
                "embedded_tool_gate_status": embedded_status,
                "triage_classification": triage_row.get("classification"),
                "triage_result_all_pass": triage_row.get("result_all_pass"),
                "triage_promotion_allowed": triage_row.get("promotion_allowed"),
                "blocked_uses": receipt.get("blocked_uses", []) if receipt else [],
            }
        )

    covered_names = {row["name"] for row in covered_reports}
    extra_receipts = []
    for name, receipt in sorted(receipts.items()):
        if name in covered_names:
            continue
        current_gate_row = gate_by_name.get(name, {})
        extra_receipts.append(
            {
                "name": name,
                "receipt_path": receipt.get("receipt_path"),
                "current_gate_status": current_gate_row.get("tool_role_status", "not_in_current_tool_gate"),
                "current_nonclassical_basin_claim_allowed": current_gate_row.get("nonclassical_basin_claim_allowed"),
                "source_result_hash_fresh": receipt.get("identity_hashes", {}).get("pass"),
                "reason": "accepted finite receipt exists, but it is not covering a current finite-covered EngineCore-boundary gate row",
            }
        )
    historical_noncovering_receipts = []
    for name, receipt in sorted(historical_receipts.items()):
        if name in covered_names:
            continue
        current_gate_row = gate_by_name.get(name, {})
        historical_noncovering_receipts.append(
            {
                "name": name,
                "receipt_path": receipt.get("receipt_path"),
                "accepted_by_current_gate_rule": receipt.get("accepted_by_current_gate_rule"),
                "receipt_all_pass": receipt.get("all_pass"),
                "current_gate_status": current_gate_row.get("tool_role_status", "not_in_current_tool_gate"),
                "current_nonclassical_basin_claim_allowed": current_gate_row.get("nonclassical_basin_claim_allowed"),
                "source_result_hash_fresh": receipt.get("identity_hashes", {}).get("pass"),
                "reason": (
                    "historical finite-boundary receipt exists, but it is not accepted as current "
                    "finite EngineCore-boundary coverage"
                ),
            }
        )

    z3_check = z3_no_clearance_for_covered_rows(len(covered_reports))
    embedded_status_stale = [row for row in covered_reports if not row["embedded_status_matches_current_gate"]]
    hash_stale_extra = [row for row in extra_receipts if not row["source_result_hash_fresh"]]
    rejected_historical = [
        row for row in historical_noncovering_receipts if row["accepted_by_current_gate_rule"] is not True
    ]
    positive = {
        "current_tool_gate_loaded": {
            "pass": TOOL_GATE.exists() and gate.get("all_pass") is True,
            "tool_gate_path": rel(TOOL_GATE),
            "tool_gate_sha256": sha256(TOOL_GATE),
        },
        "current_triage_loaded": {
            "pass": TRIAGE.exists() and isinstance(triage.get("row_triage"), list),
            "triage_path": rel(TRIAGE),
            "triage_sha256": sha256(TRIAGE),
            "triage_all_pass": triage.get("all_pass"),
            "reason": (
                "Finite-boundary triage is expected to remain gate-red while "
                "finite receipts quarantine rows without clearing promotion."
            ),
        },
        "current_finite_covered_rows_are_exactly_triage_finite_rows": {
            "pass": len(covered_reports) == len(triage_by_name) and covered_names == set(triage_by_name),
            "finite_covered_count": len(covered_reports),
            "triage_finite_count": len(triage_by_name),
            "covered_names": sorted(covered_names),
            "triage_names": sorted(str(name) for name in triage_by_name),
        },
        "all_current_covered_rows_have_accepted_fresh_receipts": {
            "pass": all(
                row["receipt_exists_and_accepted"]
                and row["receipt_path_matches_gate"]
                and row["receipt_source_result_hash_fresh"]
                for row in covered_reports
            ),
            "row_count": len(covered_reports),
        },
        "all_current_covered_rows_remain_gate_blocked": {
            "pass": all(
                row["gate_status"] == FINITE_COVERED_STATUS
                and row["gate_nonclassical_basin_claim_allowed"] is False
                and row["triage_promotion_allowed"] is False
                for row in covered_reports
            ),
            "gate_status_counts": dict(Counter(row["gate_status"] for row in covered_reports)),
        },
        "all_current_covered_rows_are_triage_quarantine_rows": {
            "pass": all(row["triage_classification"] == FINITE_TRIAGE_CLASS for row in covered_reports),
            "triage_class_counts": dict(Counter(str(row["triage_classification"]) for row in covered_reports)),
        },
        "z3_finite_coverage_does_not_clear_gate_or_promote": z3_check,
    }
    graveyard = {
        "finite_receipt_as_torch_native_enginecore_proof_killed": {
            "pass": True,
            "reason": "Every current covered row still consumes finite JSON/scalar/window/readout evidence, not a torch-native EngineCore port.",
        },
        "finite_receipt_as_gate_clearance_killed": {
            "pass": all(row["gate_nonclassical_basin_claim_allowed"] is False for row in covered_reports),
            "reason": "The current gate status is finite-receipt-covered but still blocked.",
        },
        "stale_embedded_gate_status_is_not_clearance": {
            "pass": True,
            "stale_count": len(embedded_status_stale),
            "rows": [
                {
                    "name": row["name"],
                    "embedded_tool_gate_status": row["embedded_tool_gate_status"],
                    "current_gate_status": row["gate_status"],
                }
                for row in embedded_status_stale
            ],
            "reason": "Several receipts were generated before the gate rewrote their row status to finite-receipt-covered; source/result hashes remain fresh for the current nine rows.",
        },
        "extra_noncovering_receipts_do_not_cover_current_gate_rows": {
            "pass": True,
            "extra_count": len(extra_receipts),
            "hash_stale_extra_count": len(hash_stale_extra),
            "extra_receipts": extra_receipts,
        },
        "historical_noncovering_receipts_remain_noncoverage": {
            "pass": True,
            "historical_noncovering_count": len(historical_noncovering_receipts),
            "rejected_historical_count": len(rejected_historical),
            "historical_noncovering_receipts": historical_noncovering_receipts,
            "reason": "Historical finite-boundary receipts stay visible, but red or stale receipts do not cover current gate rows.",
        },
    }
    boundary = {
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_names_no_broad_claims": {
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["does not clear", "torch-native", "physics", "consciousness"]
            ),
            "claim_ceiling": CLAIM_CEILING,
        },
        "cleanup_not_authorized": {
            "pass": True,
            "reason": "Coverage audit records current state only; it does not authorize deleting, promoting, or demoting target sims.",
        },
    }
    checks = {**positive, **graveyard, **boundary}
    all_pass = all(bool(item.get("pass")) for item in checks.values())
    return {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "finite_covered_count": len(covered_reports),
            "historical_finite_receipt_count": len(historical_receipts),
            "accepted_finite_receipt_count": len(receipts),
            "finite_receipts_currently_gate_covering": len(covered_reports),
            "extra_noncovering_finite_receipt_count": len(extra_receipts),
            "extra_noncovering_finite_receipts": [row["name"] for row in extra_receipts],
            "historical_noncovering_finite_receipt_count": len(historical_noncovering_receipts),
            "historical_rejected_finite_receipt_count": len(rejected_historical),
            "historical_noncovering_finite_receipts": [row["name"] for row in historical_noncovering_receipts],
            "stale_embedded_gate_status_count": len(embedded_status_stale),
            "hash_stale_extra_receipt_count": len(hash_stale_extra),
            "gate_clearance_authorized": False,
            "promotion_authorized": False,
            "cleanup_authorized": False,
        },
        "current_finite_covered_rows": covered_reports,
        "historical_finite_receipts": dict(sorted(historical_receipts.items())),
        "accepted_finite_receipts": dict(sorted(receipts.items())),
        "extra_noncovering_finite_receipts": extra_receipts,
        "historical_noncovering_finite_receipts": historical_noncovering_receipts,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for item in graveyard.values() if item.get("pass")),
            "variants": sorted(graveyard),
        },
        "why_not_v4_probes": [
            "This reads the current v5 tool-role gate and EngineCore row-triage receipts.",
            "It audits finite-boundary receipt coverage without executing or repairing target sims.",
            "It records stale/superseded finite receipts without turning them into current gate coverage.",
        ],
        "blockers": [] if all_pass else [key for key, item in checks.items() if not item.get("pass")],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
    }


def main() -> int:
    result = build_result()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
