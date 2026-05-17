#!/usr/bin/env python3
"""Resolve custom receipt paths from the broad tmp engine_v2 execution pass."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "attractor_basin_tmp_engine_v2_receipt_resolution_probe_results.json"
SOURCE_RESULT = RESULT_DIR / "attractor_basin_tmp_engine_v2_full_wave_execution_probe_results.json"

NAME = "attractor_basin_tmp_engine_v2_receipt_resolution_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: resolves custom /tmp/engine_v2 receipt paths printed "
    "by broad tmp wave/iter sims and reclassifies their proposal outputs. It "
    "does not admit tmp results, engine, Axis0, FEP, Holodeck, physics, "
    "cognition, world-model, or canonical architecture claims."
)

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "load-bearing source/result receipt parsing"},
    "re": {"tried": True, "used": True, "reason": "load-bearing extraction of printed custom receipt paths"},
    "pathlib": {"tried": True, "used": True, "reason": "load-bearing bounded path checks"},
    "hashlib": {"tried": True, "used": True, "reason": "load-bearing receipt hash capture"},
}
TOOL_INTEGRATION_DEPTH = {
    "json": "load_bearing",
    "re": "load_bearing",
    "pathlib": "load_bearing",
    "hashlib": "load_bearing",
}

RECEIPT_RE = re.compile(r"(?:Receipt|Results JSON):\s+(/(?:private/)?tmp/engine_v2/[^\s]+?\.json)")


def sha256_file(path: pathlib.Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json_maybe(path: pathlib.Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"_parse_error": str(exc)[:240]}


def normalize_tmp_path(text_path: str) -> pathlib.Path:
    path = pathlib.Path(text_path)
    if str(path).startswith("/tmp/engine_v2"):
        return pathlib.Path("/private/tmp/engine_v2") / path.relative_to("/tmp/engine_v2")
    return path


def classify(data: dict[str, Any] | None) -> str:
    if data is None:
        return "unresolved_missing_receipt"
    if data.get("_parse_error"):
        return "unparseable_resolved_receipt"
    if data.get("all_pass") is True:
        return "resolved_green"
    if data.get("all_pass") is False:
        return "resolved_negative"
    return "resolved_schema_odd"


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def main() -> int:
    started = time.time()
    source = load_json(SOURCE_RESULT)
    source_rows = source.get("rows", [])
    rows: list[dict[str, Any]] = []
    for row in source_rows:
        if row.get("classification") != "missing_result":
            continue
        text = "\n".join([row.get("stdout_tail") or "", row.get("stderr_tail") or ""])
        matches = RECEIPT_RE.findall(text)
        receipt_path = normalize_tmp_path(matches[-1]) if matches else None
        data = load_json_maybe(receipt_path)
        rows.append(
            {
                "script_name": row.get("script_name"),
                "original_classification": row.get("classification"),
                "printed_receipt_path": str(receipt_path) if receipt_path else None,
                "receipt_exists": bool(receipt_path and receipt_path.exists()),
                "receipt_sha256": sha256_file(receipt_path) if receipt_path else None,
                "resolved_classification": classify(data),
                "reported_all_pass": None if data is None else data.get("all_pass"),
                "reported_classification": None if data is None else data.get("classification"),
                "reported_promotion_allowed": None if data is None else data.get("promotion_allowed"),
                "reported_name": None if data is None else data.get("name"),
            }
        )
    class_counts = count_by(rows, "resolved_classification")
    positive = {
        "missing_result_rows_loaded": {"pass": len(rows) > 0, "count": len(rows)},
        "custom_receipts_resolved": {
            "pass": sum(1 for row in rows if row["receipt_exists"]) >= 10,
            "resolved_count": sum(1 for row in rows if row["receipt_exists"]),
            "classification_counts": class_counts,
        },
        "resolved_rows_classified": {"pass": bool(class_counts), "classification_counts": class_counts},
    }
    graveyards = {
        "missing_result_was_runner_resolution_gap": {
            "pass": class_counts.get("unresolved_missing_receipt", 0) < len(rows),
            "reason": "Many first-pass missing-result rows did execute and print custom receipt names.",
        },
        "resolved_green_rows_remain_unpromoted": {
            "pass": PROMOTION_ALLOWED is False,
            "reason": "Resolved tmp green receipts are still conversion candidates, not current evidence.",
        },
        "resolved_negative_rows_remain_visible": {
            "pass": class_counts.get("resolved_negative", 0) >= 1,
            "reason": "Negative tmp receipts stay as anti/open-basin evidence.",
        },
    }
    boundary = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "source_result_loaded": {
            "pass": source.get("name") == "attractor_basin_tmp_engine_v2_full_wave_execution_probe",
            "source_sha256": sha256_file(SOURCE_RESULT),
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "attractor_basin_tmp_engine_v2_receipt_resolution",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "source_result": str(SOURCE_RESULT),
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "rows": rows,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "why_not_v4_probes": [
            "This resolves custom tmp receipt paths from current broad execution output.",
            "It does not rerun or promote tmp claims.",
        ],
        "blockers": [],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  rows={len(rows)} class_counts={class_counts}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
