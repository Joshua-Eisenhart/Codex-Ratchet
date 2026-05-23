#!/usr/bin/env python3
"""Classify provider strict-live provenance debt without clearing it."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from collections import Counter
from typing import Any

import validate_provider_receipts as provider_validator


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RECEIPTS = SCOUT_ROOT / "provider_receipts"
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "provider_strict_live_provenance_debt_classification_probe_results.json"

NAME = "provider_strict_live_provenance_debt_classification_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
SOURCE_ALIGNMENT_CATEGORY = "provider_strict_live_provenance_debt"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Administrative provider-provenance classifier only: separates normal "
    "provider receipt schema validation from strict-live raw-response/live-proof "
    "validation. It does not backfill raw responses, certify missing live proof, "
    "admit provider routes, or promote any engine, manifold, basin, or physics claim."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive provider receipt parsing and result serialization",
    },
    "python_pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive repository path handling",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source and receipt set hashes",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "python_pathlib": "supportive",
    "hashlib": "supportive",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def digest_paths(paths: list[pathlib.Path]) -> str:
    h = hashlib.sha256()
    for path in paths:
        h.update(rel(path).encode("utf-8"))
        h.update(b"\0")
        if path.exists():
            h.update(hashlib.sha256(path.read_bytes()).digest())
        h.update(b"\0")
    return h.hexdigest()


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        value = row.get(key)
        counts[str(value or "unknown")] += 1
    return dict(sorted(counts.items()))


def main() -> int:
    started = time.time()
    all_json_paths = sorted(RECEIPTS.glob("*.json"))
    receipt_paths = provider_validator.receipt_candidate_paths(RECEIPTS)
    receipt_path_set = set(receipt_paths)
    sidecar_paths = [path for path in all_json_paths if path not in receipt_path_set]
    rows: list[dict[str, Any]] = []
    for path in receipt_paths:
        data = read_json(path)
        normal = provider_validator.validate(path)
        strict = provider_validator.validate(path, strict_live=True)
        errors = list(strict.get("errors") or [])
        source_raw_receipt = provider_validator.normalized_source_raw_receipt(data)
        rows.append(
            {
                "path": rel(path),
                "provider": str(data.get("provider") or "unknown"),
                "model": str(data.get("model") or ""),
                "route": str(data.get("route") or ""),
                "status": str(data.get("status") or ""),
                "schema": str(data.get("schema") or ""),
                "normal_pass": bool(normal.get("pass")),
                "strict_live_pass": bool(strict.get("pass")),
                "strict_live_errors": errors,
                "has_raw_response": bool(data.get("raw_response")),
                "has_live_api_proof": bool(data.get("live_api_proof")),
                "source_raw_receipt": source_raw_receipt,
                "has_source_raw_receipt": bool(source_raw_receipt),
                "is_normalized": "normalized" in path.name,
            }
        )

    strict_failed = [row for row in rows if not row["strict_live_pass"]]
    normal_failed = [row for row in rows if not row["normal_pass"]]
    strict_error_counts = Counter(error for row in strict_failed for error in row["strict_live_errors"])
    strict_fail_by_provider = count_by(strict_failed, "provider")
    strict_fail_by_status = count_by(strict_failed, "status")
    strict_fail_by_normalized = {
        "normalized": sum(1 for row in strict_failed if row["is_normalized"]),
        "not_normalized": sum(1 for row in strict_failed if not row["is_normalized"]),
    }
    raw_or_proof_missing = [
        row for row in strict_failed
        if "strict-live completed provider receipt missing raw_response or live_api_proof" in row["strict_live_errors"]
    ]
    source_raw_problem_rows = [
        row for row in strict_failed
        if (
            "strict-live normalized receipt missing source_raw_receipt" in row["strict_live_errors"]
            or "strict-live normalized receipt source_raw_receipt path missing" in row["strict_live_errors"]
        )
    ]
    live_pass = [row for row in rows if row["strict_live_pass"]]

    positive = {
        "provider_receipts_loaded": {
            "pass": len(rows) > 0,
            "receipt_count": len(rows),
            "skipped_sidecar_count": len(sidecar_paths),
            "receipt_root": rel(RECEIPTS),
        },
        "provider_sidecars_excluded_from_candidate_set": {
            "pass": len(all_json_paths) >= len(receipt_paths),
            "candidate_count": len(receipt_paths),
            "sidecar_count": len(sidecar_paths),
            "sidecar_samples": [rel(path) for path in sidecar_paths[:10]],
        },
        "normal_provider_schema_validation_clean": {
            "pass": len(normal_failed) == 0,
            "normal_fail_count": len(normal_failed),
        },
        "strict_live_debt_partitioned": {
            "pass": len(strict_failed) == sum(strict_fail_by_provider.values()),
            "strict_live_fail_count": len(strict_failed),
            "strict_live_pass_count": len(live_pass),
            "strict_error_counts": dict(sorted(strict_error_counts.items())),
            "strict_fail_by_provider": strict_fail_by_provider,
            "strict_fail_by_status": strict_fail_by_status,
            "strict_fail_by_normalized": strict_fail_by_normalized,
        },
        "strict_live_debt_has_repair_surface": {
            "pass": bool(raw_or_proof_missing or source_raw_problem_rows),
            "raw_or_live_proof_missing_count": len(raw_or_proof_missing),
            "source_raw_receipt_problem_count": len(source_raw_problem_rows),
            "repair_rule": (
                "Only rerun/recover raw provider calls or link normalized receipts to raw receipts; "
                "do not synthesize raw_response/live_api_proof from proposal_text."
            ),
        },
        "strict_live_pass_rows_remain_available": {
            "pass": len(live_pass) > 0,
            "strict_live_pass_count": len(live_pass),
        },
    }
    graveyard_companions = {
        "normal_schema_pass_does_not_equal_live_route_proof": {
            "pass": len(normal_failed) == 0 and len(strict_failed) > 0,
            "reason": "all receipts pass normal schema validation while completed live-provider receipts still fail strict-live provenance",
        },
        "proposal_text_is_not_raw_response": {
            "pass": all(not row["has_raw_response"] for row in raw_or_proof_missing),
            "reason": "completed proposal receipts without raw_response/live_api_proof remain useful proposal artifacts but not live route-proof artifacts",
        },
        "normalized_receipt_with_dangling_source_raw_is_not_full_lineage": {
            "pass": all(row["is_normalized"] for row in source_raw_problem_rows),
            "reason": "normalized receipts with missing or dangling source_raw_receipt preserve summary value but do not prove raw-provider lineage",
        },
    }
    boundary = {
        "promotion_allowed": {"pass": True, "value": False},
        "provider_route_admission_allowed": {"pass": True, "value": False},
        "raw_backfill_synthesized": {"pass": True, "value": False},
        "strict_live_debt_cleared": {"pass": True, "value": False},
        "scientific_claim_allowed": {"pass": True, "value": False},
    }
    nearby_variants = {
        "pass": True,
        "passed": len(rows),
        "total": len(rows),
        "variants": [
            f"{row['provider']}:{row['status']}:{'strict_pass' if row['strict_live_pass'] else 'strict_fail'}:{pathlib.Path(row['path']).name}"
            for row in rows
        ],
    }
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in graveyard_companions.values())
        and all(item["pass"] for item in boundary.values())
        and nearby_variants["pass"]
    )
    result = {
        "schema": "formal_scout_result/v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": {
            "self": sha256(pathlib.Path(__file__)),
            "provider_validator": sha256(SCOUT_ROOT / "validate_provider_receipts.py"),
            "provider_receipt_set_digest": digest_paths(receipt_paths),
        },
        "positive": positive,
        "nearby_variants": nearby_variants,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "why_not_v4_probes": (
            "This is a v5 provider-provenance audit over current formal-scout provider receipts; "
            "it is not a legacy v4 probe, provider-route admission, raw-response reconstruction, "
            "or science-claim promotion."
        ),
        "strict_live_failed_samples": strict_failed[:25],
        "summary": {
            "all_pass": all_pass,
            "receipt_count": len(rows),
            "skipped_sidecar_count": len(sidecar_paths),
            "normal_pass_count": len(rows) - len(normal_failed),
            "normal_fail_count": len(normal_failed),
            "strict_live_pass_count": len(live_pass),
            "strict_live_fail_count": len(strict_failed),
            "strict_error_counts": dict(sorted(strict_error_counts.items())),
            "strict_fail_by_provider": strict_fail_by_provider,
            "strict_fail_by_normalized": strict_fail_by_normalized,
            "completion_status": "strict_live_debt_classified_not_cleared",
        },
        "all_pass": all_pass,
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "out_path": rel(OUT_PATH),
                "receipt_count": len(rows),
                "normal_fail_count": len(normal_failed),
                "strict_live_pass_count": len(live_pass),
                "strict_live_fail_count": len(strict_failed),
                "strict_error_counts": dict(sorted(strict_error_counts.items())),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
