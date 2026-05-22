#!/usr/bin/env python3
"""Build a noncanonical archive index for the grok_sim sidequest estate.

This is a map for cleanup, not an archive mover. It records which sidequest
receipts are citeable bundles, incomplete archive material, or graveyard inputs.
"""
from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GROK_ROOT = ROOT / "system_v5" / "grok_sim"
LOOP_ROOT = GROK_ROOT / "loop_runner"
RECEIPTS = LOOP_ROOT / "receipts"
CONTRACTS = LOOP_ROOT / "contracts"
PROPOSED = LOOP_ROOT / "proposed_formal_sims"
OUT_JSON = ROOT / "system_v5" / "evidence" / "grok_sim_archive_index.json"
OUT_MD = ROOT / "system_v5" / "docs" / "GROK_SIM_ARCHIVE_INDEX.md"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_json_error": str(exc)}
    return data if isinstance(data, dict) else {"_json_error": "json root is not an object"}


def literal_module_assignment(path: Path, name: str) -> Any:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(text)
    except Exception:
        return None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        try:
            return ast.literal_eval(node.value)
        except Exception:
            return None
    return None


def dir_size_and_file_count(path: Path) -> tuple[int, int]:
    total = 0
    files = 0
    if not path.exists():
        return total, files
    for item in path.rglob("*"):
        if item.is_file():
            files += 1
            try:
                total += item.stat().st_size
            except OSError:
                pass
    return total, files


def phase_pass_from_payload(payload: dict[str, Any]) -> bool | None:
    observable = payload.get("observable")
    if isinstance(observable, dict) and "phase_pass" in observable:
        return bool(observable["phase_pass"])
    for key in ("phase_pass", "pass", "all_pass"):
        if key in payload:
            return bool(payload[key])
    return None


def summarize_receipt_dir(path: Path, live_phase_count: int) -> dict[str, Any]:
    summary_paths = sorted(path.glob("*_summary.json")) or sorted(path.glob("summary.json"))
    manifest_paths = sorted(path.glob("*_frozen_manifest.json"))
    run_hash_paths = sorted(path.glob("*_run_hash.txt"))
    phase_paths = sorted(path.glob("phase_*_results.json"))
    summary = read_json(summary_paths[0]) if summary_paths else {}
    summary_phases = summary.get("phases") if isinstance(summary.get("phases"), list) else []
    phase_passes: list[bool] = []
    if summary_phases:
        phase_passes = [bool(row.get("pass")) for row in summary_phases if isinstance(row, dict) and "pass" in row]
    else:
        for phase_path in phase_paths:
            value = phase_pass_from_payload(read_json(phase_path))
            if value is not None:
                phase_passes.append(value)
    phase_payloads = [read_json(phase_path) for phase_path in phase_paths]
    phase_payload_error_count = sum(1 for payload in phase_payloads if "_json_error" in payload)
    classifications = sorted(
        {
            str(payload.get("classification"))
            for payload in phase_payloads
            if isinstance(payload, dict) and payload.get("classification")
        }
    )
    promotion_values = [
        payload.get("promotion_allowed")
        for payload in phase_payloads
        if isinstance(payload, dict) and "promotion_allowed" in payload
    ]
    promotion_allowed_true_count = sum(
        1 for value in promotion_values if value is True or str(value).lower() == "true"
    )
    phases_run = len(summary_phases) if summary_phases else len(phase_paths)
    phases_pass = sum(1 for value in phase_passes if value)
    has_summary = bool(summary_paths)
    has_manifest = bool(manifest_paths)
    has_run_hash = bool(run_hash_paths)
    has_phase_receipts = bool(phase_paths)
    complete_bundle = has_summary and has_manifest and has_run_hash and has_phase_receipts
    all_phases_pass = bool(phases_run and phases_pass == phases_run)
    if promotion_allowed_true_count:
        archive_bucket = "quarantine_required_phase_promotion_allowed_true"
    elif not has_summary:
        archive_bucket = "archive_only_missing_summary"
    elif not has_manifest or not has_run_hash:
        archive_bucket = "archive_only_incomplete_receipt_bundle"
    elif phase_payload_error_count:
        archive_bucket = "archive_only_incomplete_receipt_bundle"
    elif all_phases_pass and phases_run >= live_phase_count:
        archive_bucket = "phase_count_at_least_live_contract_count_hash_review"
    elif all_phases_pass:
        archive_bucket = "keep_complete_historical_pass_bundle"
    elif complete_bundle:
        archive_bucket = "keep_negative_or_repair_evidence_bundle"
    else:
        archive_bucket = "archive_only_incomplete_receipt_bundle"
    return {
        "run_dir": rel(path),
        "run_id": str(summary.get("run_id") or path.name),
        "candidate": str(summary.get("candidate") or ""),
        "summary_path": rel(summary_paths[0]) if summary_paths else "",
        "frozen_manifest_path": rel(manifest_paths[0]) if manifest_paths else "",
        "run_hash_path": rel(run_hash_paths[0]) if run_hash_paths else "",
        "phase_receipt_count": len(phase_paths),
        "phase_payload_read_count": len(phase_payloads),
        "phase_payload_error_count": phase_payload_error_count,
        "phases_run": phases_run,
        "phases_pass": phases_pass,
        "phases_fail": max(phases_run - phases_pass, 0),
        "all_phases_pass": all_phases_pass,
        "complete_bundle": complete_bundle,
        "citeable_sidequest_bundle": bool(
            complete_bundle
            and all_phases_pass
            and phase_payload_error_count == 0
            and promotion_allowed_true_count == 0
        ),
        "live_contract_phase_count": live_phase_count,
        "classification_samples": classifications,
        "promotion_allowed_samples": sorted({str(value) for value in promotion_values}),
        "promotion_allowed_true_count": promotion_allowed_true_count,
        "strict_validation_status": "presence_only_hash_manifest_validation_not_run",
        "strict_validation_blockers": ["hash_manifest_strict_validation_not_run"],
        "archive_bucket": archive_bucket,
        "public_status_label": "exists",
        "claim_ceiling": "sidequest_only_not_canonical",
    }


def proposed_bucket(path: Path, classification: Any, promotion_allowed: Any) -> str:
    path_text = rel(path)
    name = path.name
    if "_quarantine_jargon" in path_text:
        return "keep_graveyard_quarantine"
    if promotion_allowed is True:
        return "quarantine_required_promotion_allowed_true"
    if name == "sim_proposed_constraint_manifold_assembly_handbuilt.py":
        return "keep_current_handbuilt_proposal_source"
    if name.startswith("sim_proposed_constraint_manifold_assembly_"):
        return "keep_graveyard_generated_assembly_candidate"
    if "manifold_legos_nonclassical" in path_text:
        return "keep_noncanonical_lego_shelf_candidate"
    if str(classification or "").startswith("formal_scout"):
        return "keep_noncanonical_formal_scout_proposal"
    return "keep_sidequest_proposal_or_archive_review"


def summarize_proposed_sources() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not PROPOSED.exists():
        return rows
    for path in sorted(PROPOSED.rglob("*.py")):
        classification = literal_module_assignment(path, "classification")
        if classification is None:
            classification = literal_module_assignment(path, "CLASSIFICATION")
        promotion_allowed = literal_module_assignment(path, "promotion_allowed")
        if promotion_allowed is None:
            promotion_allowed = literal_module_assignment(path, "PROMOTION_ALLOWED")
        rows.append(
            {
                "path": rel(path),
                "classification_assignment": classification,
                "promotion_allowed_assignment": promotion_allowed,
                "archive_bucket": proposed_bucket(path, classification, promotion_allowed),
                "public_status_label": "exists",
                "claim_ceiling": "sidequest_proposal_only_not_canonical",
            }
        )
    return rows


def build_index() -> dict[str, Any]:
    grok_size, grok_files = dir_size_and_file_count(GROK_ROOT)
    receipts_size, receipts_files = dir_size_and_file_count(RECEIPTS)
    contract_phase_paths = sorted(CONTRACTS.glob("phase_*.py"))
    receipt_dirs = sorted(path for path in RECEIPTS.iterdir() if path.is_dir()) if RECEIPTS.exists() else []
    receipt_rows = [summarize_receipt_dir(path, len(contract_phase_paths)) for path in receipt_dirs]
    proposed_rows = summarize_proposed_sources()
    receipt_bucket_counts = Counter(row["archive_bucket"] for row in receipt_rows)
    proposed_bucket_counts = Counter(row["archive_bucket"] for row in proposed_rows)
    complete_bundles = [row for row in receipt_rows if row["complete_bundle"]]
    citeable_bundles = [row for row in receipt_rows if row["citeable_sidequest_bundle"]]
    all_pass_bundles = [row for row in receipt_rows if row["all_phases_pass"]]
    complete_all_pass_bundles = [
        row
        for row in all_pass_bundles
        if row["complete_bundle"]
        and row["phase_payload_error_count"] == 0
        and row["promotion_allowed_true_count"] == 0
    ]
    phase_count_at_least_live = [
        row for row in receipt_rows if row["archive_bucket"] == "phase_count_at_least_live_contract_count_hash_review"
    ]
    high_risk_proposals = [
        row
        for row in proposed_rows
        if row["archive_bucket"] == "quarantine_required_promotion_allowed_true"
    ]
    return {
        "schema": "grok_sim_archive_index.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "boundary": "sidequest_archive_index_only_not_canonical_not_archive_move",
        "summary": {
            "grok_sim_size_bytes": grok_size,
            "grok_sim_file_count": grok_files,
            "receipt_tree_size_bytes": receipts_size,
            "receipt_tree_file_count": receipts_files,
            "receipt_run_dir_count": len(receipt_dirs),
            "summary_count": sum(1 for row in receipt_rows if row["summary_path"]),
            "frozen_manifest_count": sum(1 for row in receipt_rows if row["frozen_manifest_path"]),
            "run_hash_count": sum(1 for row in receipt_rows if row["run_hash_path"]),
            "phase_receipt_count": sum(row["phase_receipt_count"] for row in receipt_rows),
            "complete_bundle_count": len(complete_bundles),
            "citeable_sidequest_bundle_count": len(citeable_bundles),
            "all_pass_bundle_count": len(all_pass_bundles),
            "complete_all_pass_bundle_count": len(complete_all_pass_bundles),
            "phase_payload_error_count": sum(row["phase_payload_error_count"] for row in receipt_rows),
            "phase_promotion_allowed_true_count": sum(row["promotion_allowed_true_count"] for row in receipt_rows),
            "phase_count_at_least_live_contract_count_bundle_count": len(phase_count_at_least_live),
            "contract_phase_count": len(contract_phase_paths),
            "contract_extra_count": len(sorted(CONTRACTS.glob("contract_*.py"))),
            "proposed_source_count": len(proposed_rows),
            "high_risk_proposal_count": len(high_risk_proposals),
            "receipt_archive_bucket_counts": dict(receipt_bucket_counts),
            "proposed_archive_bucket_counts": dict(proposed_bucket_counts),
        },
        "contract_phase_paths": [rel(path) for path in contract_phase_paths],
        "receipt_samples": receipt_rows[:100],
        "phase_count_at_least_live_contract_count_receipts": phase_count_at_least_live,
        "all_pass_receipt_samples": all_pass_bundles[:25],
        "complete_all_pass_receipt_samples": complete_all_pass_bundles[:25],
        "high_risk_proposals": high_risk_proposals,
        "proposed_source_samples": proposed_rows[:100],
        "rows": {
            "receipt_runs": receipt_rows,
            "proposed_sources": proposed_rows,
        },
    }


def write_markdown(index: dict[str, Any], path: Path) -> None:
    summary = index["summary"]
    lines = [
        "# Grok Sim Archive Index",
        "",
        f"Generated: `{index['generated_at']}`",
        "",
        "Boundary: sidequest archive index snapshot only. Counts are point-in-time and must be regenerated before being used as current inventory. This does not move, delete, admit, or promote `grok_sim` artifacts.",
        "",
        "## Summary",
        "",
        f"- Grok sim files: `{summary['grok_sim_file_count']}`",
        f"- Grok sim size bytes: `{summary['grok_sim_size_bytes']}`",
        f"- Receipt run directories: `{summary['receipt_run_dir_count']}`",
        f"- Receipt tree files: `{summary['receipt_tree_file_count']}`",
        f"- Receipt tree size bytes: `{summary['receipt_tree_size_bytes']}`",
        f"- Summaries: `{summary['summary_count']}`",
        f"- Frozen manifests: `{summary['frozen_manifest_count']}`",
        f"- Run hashes: `{summary['run_hash_count']}`",
        f"- Phase receipts: `{summary['phase_receipt_count']}`",
        f"- Complete sidequest bundles: `{summary['complete_bundle_count']}`",
        f"- Citeable sidequest bundles: `{summary['citeable_sidequest_bundle_count']}`",
        f"- All-pass sidequest bundles: `{summary['all_pass_bundle_count']}`",
        f"- Complete all-pass sidequest bundles: `{summary['complete_all_pass_bundle_count']}`",
        f"- Bundles with phase count at least live contract count: `{summary['phase_count_at_least_live_contract_count_bundle_count']}`",
        f"- Live phase contracts: `{summary['contract_phase_count']}`",
        f"- Proposed source files: `{summary['proposed_source_count']}`",
        f"- High-risk proposal files: `{summary['high_risk_proposal_count']}`",
        "",
        "## Receipt Archive Buckets",
        "",
    ]
    for key, value in sorted(summary["receipt_archive_bucket_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Proposed Source Buckets", ""]
    for key, value in sorted(summary["proposed_archive_bucket_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += [
        "",
        "## High-Risk Proposals",
        "",
        "| path | classification | promotion_allowed | bucket |",
        "| --- | --- | --- | --- |",
    ]
    if index["high_risk_proposals"]:
        for row in index["high_risk_proposals"]:
            lines.append(
                "| `{path}` | `{classification}` | `{promotion}` | `{bucket}` |".format(
                    path=row["path"],
                    classification=row["classification_assignment"],
                    promotion=row["promotion_allowed_assignment"],
                    bucket=row["archive_bucket"],
                )
            )
    else:
        lines.append("| - | - | - | - |")
    lines += [
        "",
        "## Complete All-Pass Receipt Samples",
        "",
        "| run | phases | candidate | bucket |",
        "| --- | ---: | --- | --- |",
    ]
    for row in index["complete_all_pass_receipt_samples"]:
        lines.append(
            "| `{run}` | {passed}/{run_count} | `{candidate}` | `{bucket}` |".format(
                run=row["run_id"],
                passed=row["phases_pass"],
                run_count=row["phases_run"],
                candidate=row["candidate"],
                bucket=row["archive_bucket"],
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path, default=OUT_JSON)
    parser.add_argument("--md-out", type=Path, default=OUT_MD)
    args = parser.parse_args()
    index = build_index()
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(index, indent=2), encoding="utf-8")
    write_markdown(index, args.md_out)
    summary = index["summary"]
    print(f"wrote {args.json_out}")
    print(f"wrote {args.md_out}")
    print(f"receipt_run_dir_count={summary['receipt_run_dir_count']}")
    print(f"complete_bundle_count={summary['complete_bundle_count']}")
    print(f"high_risk_proposal_count={summary['high_risk_proposal_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
