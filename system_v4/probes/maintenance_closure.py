#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
TRUTH_AUDIT_PATH = RESULTS_DIR / "probe_truth_audit_results.json"
CONTROLLER_AUDIT_PATH = RESULTS_DIR / "controller_alignment_audit_results.json"


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return payload


def validate_cli_args(
    *,
    result_json: str,
    truth_row: str | None,
    backlog_row: str | None,
    registry_row: str | None,
    tool_row: str | None,
    dry_run: bool,
    write: bool,
) -> None:
    if not result_json:
        raise ValueError("result_json is required")
    if not any([truth_row, backlog_row, registry_row, tool_row]):
        raise ValueError("at least one explicit target selector is required")
    if dry_run and write:
        raise ValueError("dry-run and write cannot be used together")


def summary_all_pass(payload: dict[str, Any]) -> bool:
    summary = payload.get("summary", {})
    if not isinstance(summary, dict):
        return False
    all_pass = summary.get("all_pass")
    if isinstance(all_pass, bool):
        return all_pass
    tests_passed = summary.get("tests_passed")
    tests_total = summary.get("tests_total")
    if isinstance(tests_passed, int) and isinstance(tests_total, int):
        return tests_passed == tests_total
    total_pass = summary.get("total_pass")
    total_tests = summary.get("total_tests")
    if isinstance(total_pass, int) and isinstance(total_tests, int):
        return total_pass == total_tests
    passed = summary.get("passed")
    failed = summary.get("failed")
    if isinstance(passed, int) and isinstance(failed, int):
        return failed == 0 and passed >= 0
    return False


def manifest_has_complete_reasons(payload: dict[str, Any]) -> bool:
    manifest = payload.get("tool_manifest")
    if not isinstance(manifest, dict) or not manifest:
        return False
    for info in manifest.values():
        if not isinstance(info, dict):
            return False
        reason = info.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            return False
    return True


def has_tool_integration_depth(payload: dict[str, Any]) -> bool:
    depth = payload.get("tool_integration_depth")
    return isinstance(depth, dict) and bool(depth)


def has_nonbaseline_load_bearing_tool(payload: dict[str, Any]) -> bool:
    manifest = payload.get("tool_manifest")
    depth = payload.get("tool_integration_depth")
    if not isinstance(manifest, dict) or not isinstance(depth, dict):
        return False
    for tool, integration in depth.items():
        if not isinstance(integration, str):
            continue
        if "load" not in integration.lower():
            continue
        info = manifest.get(tool)
        if not isinstance(info, dict):
            continue
        if info.get("used") is True:
            return True
    return False


def derive_truth_label(
    payload: dict[str, Any],
    *,
    truth_audit_ok: bool,
    controller_audit_ok: bool,
) -> dict[str, Any]:
    classification = payload.get("classification")
    audits_green = truth_audit_ok and controller_audit_ok
    all_pass = summary_all_pass(payload)
    complete_manifest = manifest_has_complete_reasons(payload)
    has_depth = has_tool_integration_depth(payload)
    has_load_bearing_tool = has_nonbaseline_load_bearing_tool(payload)

    if not audits_green:
        return {
            "truth_label": "runs",
            "blocked": True,
            "reason": "fresh audit outputs are not fully green",
        }

    if all_pass and classification == "canonical" and complete_manifest and has_depth and has_load_bearing_tool:
        return {
            "truth_label": "canonical by process",
            "blocked": False,
            "reason": "artifact and fresh audits satisfy canonical process gates",
        }

    if all_pass:
        return {
            "truth_label": "passes local rerun",
            "blocked": False,
            "reason": "bounded packet passes locally but does not satisfy every canonical process gate",
        }

    return {
        "truth_label": "runs",
        "blocked": False,
        "reason": "artifact exists but local pass evidence is incomplete",
    }


def parse_markdown_row(row: str) -> list[str]:
    text = row.strip()
    if not text.startswith("|") or not text.endswith("|"):
        raise ValueError("row is not a markdown table row")
    return [cell.strip() for cell in text.strip("|").split("|")]



def format_markdown_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"



def replace_markdown_table_row(markdown: str, row_match_fragment: str, new_row: str) -> str:
    lines = markdown.splitlines()
    matches = [idx for idx, line in enumerate(lines) if row_match_fragment in line]
    if not matches:
        raise ValueError(f"target row not found for fragment: {row_match_fragment}")
    if len(matches) > 1:
        raise ValueError(f"target row is ambiguous for fragment: {row_match_fragment}")
    lines[matches[0]] = new_row
    replacement = "\n".join(lines)
    if markdown.endswith("\n"):
        replacement += "\n"
    return replacement



def update_truth_row(
    existing_row: str,
    *,
    truth_label: str,
    canonical_note: str,
    notes_note: str | None,
    preserve_notes: bool = False,
) -> str:
    cells = parse_markdown_row(existing_row)
    if len(cells) != 7:
        raise ValueError(f"truth row must have 7 columns, got {len(cells)}")

    cells[2] = "yes"
    if truth_label in {"runs", "passes local rerun", "canonical by process"}:
        cells[3] = "yes, fresh local rerun"
    else:
        cells[3] = "no"

    if truth_label in {"passes local rerun", "canonical by process"}:
        cells[4] = "yes, fresh local rerun"
    else:
        cells[4] = "no"

    cells[5] = canonical_note
    if not (preserve_notes and notes_note is None):
        cells[6] = notes_note or cells[6]
    return format_markdown_row(cells)



def find_markdown_table_row(markdown: str, row_match_fragment: str) -> str:

    matches = [line for line in markdown.splitlines() if row_match_fragment in line]
    if not matches:
        raise ValueError(f"target row not found for fragment: {row_match_fragment}")
    if len(matches) > 1:
        raise ValueError(f"target row is ambiguous for fragment: {row_match_fragment}")
    return matches[0]



def prepare_truth_surface_update(
    markdown: str,
    *,
    row_match_fragment: str,
    truth_label: str,
    canonical_note: str,
    notes_note: str | None = None,
    preserve_notes: bool = False,
) -> dict[str, str]:
    old_row = find_markdown_table_row(markdown, row_match_fragment)
    new_row = update_truth_row(
        old_row,
        truth_label=truth_label,
        canonical_note=canonical_note,
        notes_note=notes_note,
        preserve_notes=preserve_notes,
    )
    updated_text = replace_markdown_table_row(markdown, row_match_fragment, new_row)
    return {
        "old_row": old_row,
        "new_row": new_row,
        "updated_text": updated_text,
    }



def summarize_artifact_evidence(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    passed = summary.get("tests_passed") or summary.get("total_pass") or summary.get("passed")
    total = summary.get("total_tests") or summary.get("tests_total")
    classification = payload.get("classification") or "unclassified"
    depth = payload.get("tool_integration_depth") or {}
    load_bearing = [t for t, d in depth.items() if isinstance(d, str) and "load" in d.lower()]
    parts: list[str] = [f"classification: `{classification}`"]
    if isinstance(passed, int) and isinstance(total, int):
        parts.append(f"{passed}/{total} tests passing")
    if load_bearing:
        parts.append("load-bearing: " + ", ".join(f"`{t}`" for t in load_bearing))
    return "; ".join(parts)


def build_truth_notes(
    *,
    truth_label: str,
    reason: str,
    result_json_name: str,
    payload: dict[str, Any] | None = None,
) -> tuple[str, str]:
    if truth_label == "canonical by process":
        canonical_note = "`canonical by process` — fresh artifact and fresh audits support process promotion"
    elif truth_label == "passes local rerun":
        canonical_note = "no — fresh rerun is real but the packet remains below canonical by process"
    elif truth_label == "runs":
        canonical_note = "no — execution evidence exists but the packet is not promotable from the current audit state"
    else:
        canonical_note = "no — file exists but stronger rerun/process evidence is not yet recorded"
    notes_note = f"{result_json_name}: {reason}"
    if payload is not None:
        evidence = summarize_artifact_evidence(payload)
        if evidence:
            notes_note = f"{notes_note}; {evidence}"
    return canonical_note, notes_note



def execute_truth_surface_update(
    *,
    surface_path: Path,
    row_match_fragment: str,
    truth_label: str,
    reason: str,
    result_json_name: str,
    write: bool,
    payload: dict[str, Any] | None = None,
    notes_note: str | None = None,
    preserve_notes: bool = False,
) -> dict[str, Any]:
    markdown = surface_path.read_text(encoding="utf-8")
    canonical_note, auto_notes = build_truth_notes(
        truth_label=truth_label,
        reason=reason,
        result_json_name=result_json_name,
        payload=payload,
    )
    # Priority: explicit override > preserve existing > auto-generated
    notes_note = notes_note if notes_note is not None else (None if preserve_notes else auto_notes)
    plan = prepare_truth_surface_update(
        markdown,
        row_match_fragment=row_match_fragment,
        truth_label=truth_label,
        canonical_note=canonical_note,
        notes_note=notes_note,
        preserve_notes=preserve_notes,
    )
    changed = apply_surface_update(surface_path, plan["updated_text"], write=write)
    return {
        "surface_path": str(surface_path),
        "old_row": plan["old_row"],
        "new_row": plan["new_row"],
        "changed": changed,
    }



def update_backlog_row(existing_row: str, *, current_state: str, next_move: str | None) -> str:
    cells = parse_markdown_row(existing_row)
    if len(cells) != 5:
        raise ValueError(f"backlog row must have 5 columns, got {len(cells)}")
    cells[2] = current_state
    if next_move is not None:
        cells[3] = next_move
    return format_markdown_row(cells)



def update_registry_row(
    existing_row: str,
    *,
    current_coverage: str,
    result_json_name: str,
    notes_note: str,
) -> str:
    cells = parse_markdown_row(existing_row)
    if len(cells) != 11:
        raise ValueError(f"registry row must have 11 columns, got {len(cells)}")
    cells[7] = f"`{result_json_name}`"
    cells[8] = current_coverage
    cells[10] = notes_note
    return format_markdown_row(cells)



def execute_backlog_surface_update(
    *,
    surface_path: Path,
    row_match_fragment: str,
    current_state: str,
    next_move: str | None,
    write: bool,
) -> dict[str, Any]:
    markdown = surface_path.read_text(encoding="utf-8")
    old_row = find_markdown_table_row(markdown, row_match_fragment)
    new_row = update_backlog_row(old_row, current_state=current_state, next_move=next_move)
    updated_text = replace_markdown_table_row(markdown, row_match_fragment, new_row)
    changed = apply_surface_update(surface_path, updated_text, write=write)
    return {
        "surface_path": str(surface_path),
        "old_row": old_row,
        "new_row": new_row,
        "changed": changed,
    }



def execute_registry_surface_update(
    *,
    surface_path: Path,
    row_match_fragment: str,
    current_coverage: str,
    result_json_name: str,
    notes_note: str,
    write: bool,
) -> dict[str, Any]:
    markdown = surface_path.read_text(encoding="utf-8")
    old_row = find_markdown_table_row(markdown, row_match_fragment)
    new_row = update_registry_row(
        old_row,
        current_coverage=current_coverage,
        result_json_name=result_json_name,
        notes_note=notes_note,
    )
    updated_text = replace_markdown_table_row(markdown, row_match_fragment, new_row)
    changed = apply_surface_update(surface_path, updated_text, write=write)
    return {
        "surface_path": str(surface_path),
        "old_row": old_row,
        "new_row": new_row,
        "changed": changed,
    }



def apply_surface_update(surface_path: Path, updated_text: str, *, write: bool) -> bool:
    if not write:
        return False
    surface_path.write_text(updated_text, encoding="utf-8")
    return True


def truth_audit_ok_from_payload(payload: dict[str, Any]) -> bool:
    summary = payload.get("summary", {})
    return bool(summary.get("ok")) if isinstance(summary, dict) else False


def controller_audit_ok_from_payload(payload: dict[str, Any]) -> bool:
    return bool(payload.get("docs_current")) and bool(payload.get("controller_contract_current"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Derive maintenance-closure truth labels for explicit controller targets.")
    parser.add_argument("--result-json", required=True)
    parser.add_argument("--lego-id")
    parser.add_argument("--truth-row")
    parser.add_argument("--backlog-row")
    parser.add_argument("--registry-row")
    parser.add_argument("--tool-row")
    parser.add_argument("--notes-fragment")
    parser.add_argument("--allow-noop", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--preserve-notes",
        action="store_true",
        help="keep existing Notes column text unless --notes-fragment is supplied",
    )
    return parser


def resolve_result_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = PROJECT_DIR / path
    return path


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    validate_cli_args(
        result_json=args.result_json,
        truth_row=args.truth_row,
        backlog_row=args.backlog_row,
        registry_row=args.registry_row,
        tool_row=args.tool_row,
        dry_run=args.dry_run,
        write=args.write,
    )

    result_path = resolve_result_path(args.result_json)
    if not result_path.exists():
        raise SystemExit(f"missing result json: {result_path}")

    payload = read_json(result_path)
    truth_payload = read_json(TRUTH_AUDIT_PATH) if TRUTH_AUDIT_PATH.exists() else {"summary": {"ok": False}}
    controller_payload = read_json(CONTROLLER_AUDIT_PATH) if CONTROLLER_AUDIT_PATH.exists() else {}
    decision = derive_truth_label(
        payload,
        truth_audit_ok=truth_audit_ok_from_payload(truth_payload),
        controller_audit_ok=controller_audit_ok_from_payload(controller_payload),
    )

    truth_label = decision["truth_label"]
    surfaces_touched: list[str] = []
    blocked_reason: str | None = decision["reason"] if decision["blocked"] else None
    row_proposals: dict[str, dict[str, str]] = {}

    # Truth surface
    if args.truth_row and not decision["blocked"]:
        truth_surface_path = PROJECT_DIR / "system_v5" / "new docs" / "plans" / "sim_truth_audit.md"
        if truth_surface_path.exists():
            try:
                report = execute_truth_surface_update(
                    surface_path=truth_surface_path,
                    row_match_fragment=args.truth_row,
                    truth_label=truth_label,
                    reason=decision["reason"],
                    result_json_name=result_path.name,
                    write=args.write,
                    payload=payload,
                    notes_note=args.notes_fragment,
                    preserve_notes=args.preserve_notes,
                )
                row_proposals["truth_row"] = {
                    "surface": report["surface_path"],
                    "old_row": report["old_row"][:120] + ("..." if len(report["old_row"]) > 120 else ""),
                    "new_row": report["new_row"][:120] + ("..." if len(report["new_row"]) > 120 else ""),
                }
                if report["changed"]:
                    surfaces_touched.append(report["surface_path"])
            except ValueError as exc:
                blocked_reason = str(exc)

    # Backlog surface
    if args.backlog_row and not decision["blocked"]:
        backlog_surface_path = PROJECT_DIR / "system_v5" / "new docs" / "plans" / "sim_backlog_matrix.md"
        if backlog_surface_path.exists():
            try:
                report = execute_backlog_surface_update(
                    surface_path=backlog_surface_path,
                    row_match_fragment=f"| {args.backlog_row} |",
                    current_state=truth_label,
                    next_move=args.notes_fragment,
                    write=args.write,
                )
                row_proposals["backlog_row"] = {
                    "surface": report["surface_path"],
                    "old_row": report["old_row"][:120] + ("..." if len(report["old_row"]) > 120 else ""),
                    "new_row": report["new_row"][:120] + ("..." if len(report["new_row"]) > 120 else ""),
                }
                if report["changed"]:
                    surfaces_touched.append(report["surface_path"])
            except ValueError as exc:
                blocked_reason = str(exc)

    # Registry surface
    if args.registry_row and not decision["blocked"]:
        registry_surface_path = PROJECT_DIR / "system_v5" / "new docs" / "17_actual_lego_registry.md"
        if registry_surface_path.exists():
            try:
                report = execute_registry_surface_update(
                    surface_path=registry_surface_path,
                    row_match_fragment=f"`{args.registry_row}`",
                    current_coverage=truth_label,
                    result_json_name=result_path.name,
                    notes_note=args.notes_fragment or f"{result_path.name}: {decision['reason']}",
                    write=args.write,
                )
                row_proposals["registry_row"] = {
                    "surface": report["surface_path"],
                    "old_row": report["old_row"][:120] + ("..." if len(report["old_row"]) > 120 else ""),
                    "new_row": report["new_row"][:120] + ("..." if len(report["new_row"]) > 120 else ""),
                }
                if report["changed"]:
                    surfaces_touched.append(report["surface_path"])
            except ValueError as exc:
                blocked_reason = str(exc)

    report = {
        "result_json": str(result_path),
        "truth_label": truth_label,
        "blocked": decision["blocked"],
        "reason": decision["reason"],
        "targets": {
            "truth_row": args.truth_row,
            "backlog_row": args.backlog_row,
            "registry_row": args.registry_row,
            "tool_row": args.tool_row,
        },
        "mode": "write" if args.write else "dry-run" if args.dry_run else "report-only",
        "surfaces_touched": surfaces_touched,
        "blocked_reason": blocked_reason,
        "row_proposals": row_proposals,
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
