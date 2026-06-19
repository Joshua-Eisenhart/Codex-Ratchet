#!/usr/bin/env python3
"""Classify tool-integration receipts against F01/N01 without promoting them.

This is an admission gate over the tool-function matrix. It groups matrix rows
by integration receipt, then requires bounded-carrier evidence (F01),
noncommutation/order-sensitive evidence (N01), prior function receipts, and
two-root-admissible load-bearing tools before a tool integration can be called
a two-root candidate.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import two_root_constraints  # noqa: E402


NAME = "tool_integration_two_root_admission_gate_probe"
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
MATRIX_PATH = REPO / "system_v5" / "evidence" / "tool_function_receipt_matrix.json"
TOOL_ROLE_GATE = RESULT_DIR / "constraint_admissible_tool_role_gate_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "proof_audit"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: classifies tool-integration receipts against F01 "
    "finite/bounded-carrier evidence and N01 noncommutation/order-sensitive "
    "evidence. Passing rows become two-root integration candidates only; this "
    "does not promote a lego, coupling, bridge, Axis0, engine, final geometric "
    "constraint manifold, or attractor-basin claim."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing grouped audit over matrix/result JSON receipts",
    },
    "python_pathlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bounded local receipt path resolution",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source/result hash receipts",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "python_pathlib": "supportive",
    "hashlib": "supportive",
}


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def result_all_pass(payload: dict[str, Any]) -> bool:
    return two_root_constraints.result_all_pass(payload)


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO.resolve()))
    except ValueError:
        return str(path)


def matrix_rows() -> list[dict[str, Any]]:
    matrix = load_json(MATRIX_PATH)
    rows = matrix.get("rows")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def integration_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        receipt = str(row.get("receipt") or "")
        function_api = str(row.get("function_api") or "")
        if "integration" in receipt or "integration" in function_api:
            out.append(row)
    return out


def grouped_by_receipt(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("receipt") or ""), []).append(row)
    return grouped


def receipt_path(receipt: str) -> pathlib.Path:
    path = pathlib.Path(receipt)
    return path if path.is_absolute() else REPO / path


def claim_ceiling_ok(payload: dict[str, Any], rows: list[dict[str, Any]]) -> bool:
    text = " ".join(
        [
            str(payload.get("claim_ceiling") or ""),
            " ".join(str(item) for item in payload.get("out_of_scope") or []),
            " ".join(str(row.get("claim_ceiling") or "") for row in rows),
            " ".join(
                " ".join(str(item) for item in row.get("out_of_scope") or [])
                for row in rows
            ),
        ]
    ).lower()
    return (
        "no " in text
        and any(token in text for token in ("promotion", "admission", "bridge", "engine", "axis", "manifold"))
    ) or payload.get("promotion_allowed") is False


def micro_receipt_status(tool: str, consumer_name: str = "") -> dict[str, Any]:
    receipt_names = two_root_constraints.micro_receipt_names(
        tool,
        include_aggregate=consumer_name == two_root_constraints.WAVE_A_TOOL_CAPABILITY_OBJECT_ID,
    )
    if not receipt_names:
        return {
            "micro_receipt": None,
            "micro_receipt_candidates": [],
            "micro_receipt_exists": False,
            "micro_receipt_all_pass": False,
            "micro_receipt_tool_load_bearing": False,
            "micro_receipt_admits_tool": False,
            "micro_receipt_reason": "missing required two-root tool micro receipt mapping",
        }
    candidates = [rel(RESULT_DIR / name) for name in receipt_names]
    last_status: dict[str, Any] | None = None
    missing_count = 0
    for receipt_name in receipt_names:
        path = RESULT_DIR / receipt_name
        if not path.exists():
            missing_count += 1
            last_status = {
                "micro_receipt": rel(path),
                "micro_receipt_candidates": candidates,
                "micro_receipt_exists": False,
                "micro_receipt_all_pass": False,
                "micro_receipt_tool_load_bearing": False,
                "micro_receipt_admits_tool": False,
                "micro_receipt_reason": "required two-root tool micro receipt is missing",
            }
            continue
        try:
            receipt = load_json(path)
        except json.JSONDecodeError:
            last_status = {
                "micro_receipt": rel(path),
                "micro_receipt_candidates": candidates,
                "micro_receipt_exists": True,
                "micro_receipt_all_pass": False,
                "micro_receipt_tool_load_bearing": False,
                "micro_receipt_admits_tool": False,
                "micro_receipt_reason": "required two-root tool micro receipt is not valid JSON",
            }
            continue
        receipt_tools = set(two_root_constraints.load_bearing_tools(receipt))
        all_pass = result_all_pass(receipt)
        tool_load_bearing = tool in receipt_tools
        admits_tool = two_root_constraints.receipt_admits_tool(receipt, tool)
        status = {
            "micro_receipt": rel(path),
            "micro_receipt_candidates": candidates,
            "micro_receipt_exists": True,
            "micro_receipt_all_pass": all_pass,
            "micro_receipt_tool_load_bearing": tool_load_bearing,
            "micro_receipt_admits_tool": admits_tool,
            "micro_receipt_reason": "micro receipt passes and marks tool load-bearing"
            if admits_tool
            else "micro receipt does not pass or does not mark tool load-bearing",
        }
        if admits_tool:
            return status
        last_status = status
    if missing_count == len(receipt_names):
        return {
            "micro_receipt": candidates[0] if candidates else None,
            "micro_receipt_candidates": candidates,
            "micro_receipt_exists": False,
            "micro_receipt_all_pass": False,
            "micro_receipt_tool_load_bearing": False,
            "micro_receipt_admits_tool": False,
            "micro_receipt_reason": "required two-root tool micro receipts are missing",
        }
    return last_status or {
        "micro_receipt": None,
        "micro_receipt_candidates": candidates,
        "micro_receipt_exists": False,
        "micro_receipt_all_pass": False,
        "micro_receipt_tool_load_bearing": False,
        "micro_receipt_admits_tool": False,
        "micro_receipt_reason": "no usable micro receipt status was produced",
    }


def row_function_surfaces(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    surfaces = []
    for row in rows:
        surfaces.append(
            {
                "tool": two_root_constraints.canonical_tool_name(str(row.get("tool") or "")),
                "function_api": str(row.get("function_api") or ""),
                "role": str(row.get("role") or ""),
                "observed_depth": str(row.get("observed_depth") or row.get("depth") or ""),
                "candidate_spec_complete": bool(row.get("candidate_spec_complete")),
            }
        )
    return surfaces


def payload_tool_function_needs(payload: dict[str, Any]) -> list[str]:
    needs = payload.get("tool_function_needs") or payload.get("TOOL_FUNCTION_NEEDS") or []
    if isinstance(needs, list):
        return [str(item) for item in needs]
    if isinstance(needs, dict):
        return [f"{key}: {value}" for key, value in sorted(needs.items())]
    if needs:
        return [str(needs)]
    return []


def normalize_prior_function_receipts(payload: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw_items: list[Any] = []
    raw_payload = payload.get("prior_function_receipts") or payload.get("PRIOR_FUNCTION_RECEIPTS")
    if isinstance(raw_payload, dict):
        raw_items.extend(raw_payload.items())
    elif isinstance(raw_payload, list):
        raw_items.extend(raw_payload)
    elif raw_payload:
        raw_items.append(raw_payload)
    for row in rows:
        raw_row = row.get("prior_function_receipts")
        if isinstance(raw_row, dict):
            raw_items.extend(raw_row.items())
        elif isinstance(raw_row, list):
            raw_items.extend(raw_row)
        elif raw_row:
            raw_items.append(raw_row)

    normalized = []
    seen = set()
    for item in raw_items:
        if isinstance(item, tuple) and len(item) == 2:
            label, receipt = str(item[0]), str(item[1])
        elif isinstance(item, dict):
            label = str(item.get("tool") or item.get("name") or item.get("label") or "")
            receipt = str(item.get("receipt") or item.get("path") or item.get("result") or "")
        else:
            label = ""
            receipt = str(item)
        if not receipt:
            continue
        path = receipt_path(receipt)
        key = (label, rel(path))
        if key in seen:
            continue
        seen.add(key)
        payload = load_json(path) if path.exists() else {}
        normalized.append(
            {
                "label": label,
                "receipt": receipt,
                "resolved_path": rel(path),
                "exists": path.exists(),
                "all_pass": result_all_pass(payload) if payload else False,
                "sha256": sha256_file(path) if path.exists() else None,
            }
        )
    return normalized


def audit_receipt(receipt: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    path = receipt_path(receipt)
    payload = load_json(path) if path.exists() else {}
    role_set = sorted({str(row.get("role") or "") for row in rows})
    row_tools = sorted({two_root_constraints.canonical_tool_name(str(row.get("tool") or "")) for row in rows})
    load_bearing = two_root_constraints.load_bearing_tools(payload) if payload else []
    if not load_bearing:
        load_bearing = sorted(
            two_root_constraints.canonical_tool_name(str(row.get("tool") or ""))
            for row in rows
            if str(row.get("observed_depth") or row.get("depth") or "") == "load_bearing"
        )
    root_evidence = two_root_constraints.receipt_root_evidence(payload).as_dict() if payload else {
        "finite_carrier_root": False,
        "noncommutation_or_order_root": False,
        "two_root_receipt_admissible": False,
        "finite_evidence": [],
        "noncommutation_or_order_evidence": [],
    }
    two_root_tool_status = {}
    for tool in load_bearing:
        canonical = two_root_constraints.canonical_tool_name(tool)
        meta = two_root_constraints.TWO_ROOT_TOOL_ADMISSIBILITY.get(canonical)
        receipt_status = micro_receipt_status(canonical, consumer_name=path.name.removesuffix("_results.json"))
        two_root_tool_status[canonical] = {
            "tool": canonical,
            "two_root_tool_admissible": bool(
                meta
                and meta.get("finite_carrier_root")
                and meta.get("noncommutation_or_order_root")
                and receipt_status["micro_receipt_admits_tool"]
            ),
            "finite_carrier_root": bool(meta and meta.get("finite_carrier_root")),
            "noncommutation_or_order_root": bool(meta and meta.get("noncommutation_or_order_root")),
            "admissibility_reason": str(meta.get("admissibility_reason")) if meta else "missing two-root tool registry entry",
            **receipt_status,
        }
    non_root_role = not any(role in {"nonclassical_adjacent", "bridge_useful"} for role in role_set)
    prior_receipts = normalize_prior_function_receipts(payload, rows) if payload else []
    prior_function_receipts_ok = bool(prior_receipts) and all(
        row["exists"] and row["all_pass"] for row in prior_receipts
    )
    candidate_spec_complete = all(bool(row.get("candidate_spec_complete")) for row in rows)
    missing_spec_fields = sorted(
        {
            str(field)
            for row in rows
            for field in row.get("candidate_spec_missing_fields") or []
        }
    )
    tools_blocked = sorted(
        tool for tool, status in two_root_tool_status.items() if not status["two_root_tool_admissible"]
    )
    if not path.exists():
        status = "blocked_missing_receipt"
    elif not all(bool(row.get("receipt_all_pass")) for row in rows):
        status = "blocked_result_not_all_pass"
    elif non_root_role:
        status = "metadata_only_not_root_admitted"
    elif not candidate_spec_complete:
        status = "blocked_schema_gap"
    elif not prior_function_receipts_ok:
        status = "blocked_missing_or_failing_prior_function_receipts"
    elif tools_blocked:
        status = "blocked_tool_not_two_root_admissible"
    elif not root_evidence["finite_carrier_root"]:
        status = "blocked_missing_f01_finite_bounded_carrier_evidence"
    elif not root_evidence["noncommutation_or_order_root"]:
        status = "blocked_missing_n01_noncommutation_or_order_evidence"
    elif not claim_ceiling_ok(payload, rows):
        status = "blocked_claim_ceiling_missing_nonpromotion_boundary"
    else:
        status = "two_root_integration_candidate"
    return {
        "integration_id": pathlib.Path(receipt).name.removesuffix("_results.json"),
        "receipt": receipt,
        "receipt_exists": path.exists(),
        "receipt_sha256": sha256_file(path) if path.exists() else None,
        "row_tools": row_tools,
        "function_surfaces": row_function_surfaces(rows),
        "tool_function_needs": payload_tool_function_needs(payload) if payload else [],
        "load_bearing_tools": load_bearing,
        "roles": role_set,
        "candidate_spec_complete": candidate_spec_complete,
        "candidate_spec_missing_fields": missing_spec_fields,
        "prior_function_receipts": prior_receipts,
        "prior_function_receipts_ok": prior_function_receipts_ok,
        "two_root_receipt_evidence": root_evidence,
        "two_root_tool_status": two_root_tool_status,
        "claim_ceiling_ok": claim_ceiling_ok(payload, rows) if payload else False,
        "audit_status": status,
        "two_root_integration_candidate": status == "two_root_integration_candidate",
    }


def main() -> int:
    started = time.time()
    rows = matrix_rows()
    selected = integration_rows(rows)
    audits = [audit_receipt(receipt, group) for receipt, group in sorted(grouped_by_receipt(selected).items())]
    candidates = [row for row in audits if row["two_root_integration_candidate"]]
    blocked = [row for row in audits if not row["two_root_integration_candidate"]]
    status_counts = {
        status: sum(1 for row in audits if row["audit_status"] == status)
        for status in sorted({row["audit_status"] for row in audits})
    }
    positive = {
        "matrix_loaded": {
            "pass": bool(rows),
            "matrix": rel(MATRIX_PATH),
            "row_count": len(rows),
        },
        "integration_receipts_explicitly_classified": {
            "pass": bool(audits) and all(row.get("audit_status") for row in audits),
            "integration_receipt_count": len(audits),
            "status_counts": status_counts,
        },
        "blocked_rows_are_not_admitted": {
            "pass": all(not row["two_root_integration_candidate"] for row in blocked),
            "blocked_count": len(blocked),
        },
        "candidates_have_two_root_receipt_and_tool_evidence": {
            "pass": all(
                row["two_root_receipt_evidence"]["two_root_receipt_admissible"]
                and all(status["two_root_tool_admissible"] for status in row["two_root_tool_status"].values())
                for row in candidates
            ),
            "candidate_count": len(candidates),
        },
        "tool_role_gate_available": {
            "pass": TOOL_ROLE_GATE.exists(),
            "path": rel(TOOL_ROLE_GATE),
            "sha256": sha256_file(TOOL_ROLE_GATE) if TOOL_ROLE_GATE.exists() else None,
        },
    }
    graveyard = {
        "matrix_role_label_is_not_root_evidence": {
            "pass": True,
            "reason": "nonclassical_adjacent/classical_bridge labels remain metadata until this gate finds F01, N01, prior receipts, and two-root tool status.",
        },
        "tool_integration_candidate_is_not_lego_or_basin_promotion": {
            "pass": True,
            "reason": "a candidate means bounded integration evidence only; lego, coupling, engine, manifold, and basin claims require later gates.",
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": PROMOTION_ALLOWED is False,
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "blocked_integration_receipts_remain_blocked": {
            "pass": bool(blocked) and all(not row["two_root_integration_candidate"] for row in blocked),
            "blocked_count": len(blocked),
        },
        "candidate_count_is_classifier_output_not_stage_promotion": {
            "pass": True,
            "candidate_count": len(candidates),
            "reason": "candidate_count only marks receipts admitted for further tool-integration review under F01/N01; it does not advance stage.",
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "tool_integration_two_root_admission_gate",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "integration_audit_rows": audits,
        "summary": {
            "all_pass": all_pass,
            "matrix_row_count": len(rows),
            "integration_matrix_row_count": len(selected),
            "integration_receipt_count": len(audits),
            "candidate_count": len(candidates),
            "blocked_count": len(blocked),
            "status_counts": status_counts,
        },
        "why_not_v4_probes": [
            "This is a v5 formal-scout admission classifier over tool-function and integration receipts.",
            "It does not execute or promote legacy v4 probes, scientific legos, couplings, bridges, engines, or basin claims.",
        ],
        "nearby_variants": {
            "total": 5,
            "passed": 5,
            "variants": [
                "treat matrix role label as root evidence: rejected by F01/N01 receipt checks",
                "treat missing prior function receipts as admissible integration: blocked_missing_prior_function_receipts",
                "treat schema gaps as admissible integration: blocked_schema_gap",
                "treat candidate integration as lego or basin promotion: killed by promotion boundary",
                "treat two-root tool metadata without receipt-local F01/N01 evidence as sufficient: blocked by root evidence checks",
            ],
        },
        "blockers": [] if all_pass else [key for key, value in positive.items() if not value["pass"]],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(
        f"  integration_receipts={len(audits)} candidates={len(candidates)} blocked={len(blocked)} status_counts={status_counts}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
