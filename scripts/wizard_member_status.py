#!/usr/bin/env python3
"""Render Wizard v4.1 member status from matrix receipts.

The output is intentionally human-readable: one row per council member/parent,
with attempted/passed/failed counts and degraded model-family truth. It is not a
worker log and it does not open files or browsers.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from wizard_topology import COUNCIL_ORDER, EXPECTED_CURRENT_TOPOLOGY_MEMBERS, OBSOLETE_ROUTES, ROUTES

REQUIRED_ROUTES = ROUTES


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"route": path.stem, "status": "unreadable", "load_error": str(exc), "receipt_path": str(path)}


def group_counts(receipt: dict[str, Any]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for group in receipt.get("groups") or []:
        model = str(group.get("model") or "unknown")
        counts = group.get("counts") or {}
        result.setdefault(model, {"passed": 0, "attempted": 0, "failed": 0, "timed_out": 0, "not_launched": 0, "weak": 0})
        result[model]["passed"] += int(counts.get("completed") or 0)
        result[model]["attempted"] += int(counts.get("total") or 0)
        result[model]["failed"] += int(counts.get("failed") or 0)
        result[model]["timed_out"] += int(counts.get("timed_out") or 0)
        result[model]["not_launched"] += int(counts.get("not_launched") or 0)
        result[model]["weak"] += len(group.get("usefulness_failures") or [])
    gemini = receipt.get("gemini") or {}
    if gemini:
        status = gemini.get("status")
        result["gemini"] = {
            "passed": 1 if status == "completed" else 0,
            "attempted": 1 if status == "completed" else 0,
            "failed": 0,
            "timed_out": 0,
            "not_launched": 1 if status != "completed" else 0,
            "weak": 0,
        }
    return result


def summarize_receipt_data(receipt: dict[str, Any], path: Path) -> dict[str, Any]:
    route = str(receipt.get("route") or path.parent.name)
    council, member = COUNCIL_ORDER.get(route, ("Other", route))
    formal_expected = len(receipt.get("formal_child_obligation") or [])
    formal_passed = len(receipt.get("formal_children_completed") or [])
    groups = group_counts(receipt)
    repair_or_reroute = bool(receipt.get("rescore_existing")) or path.name.startswith("rescored_")
    child_rerouter = receipt.get("child_rerouter") or {}
    if child_rerouter.get("terminal_disposition") not in {None, "", "accepted"}:
        repair_or_reroute = True
    attempted = sum(counts["attempted"] for model, counts in groups.items() if model != "gemini")
    passed = sum(counts["passed"] for model, counts in groups.items() if model != "gemini")
    failed = sum(counts["failed"] + counts["timed_out"] + counts["weak"] for model, counts in groups.items() if model != "gemini")
    degraded = []
    for model, counts in groups.items():
        if counts["not_launched"] and counts["passed"] == 0:
            degraded.append(model)
    missing_formal = sorted(set(receipt.get("formal_child_obligation") or []) - set(receipt.get("formal_children_completed") or []))
    status = str(receipt.get("status") or "unknown")
    if route in OBSOLETE_ROUTES:
        status = "obsolete"
    elif route not in COUNCIL_ORDER:
        status = "unknown_route"
    elif status == "accepted" and formal_expected and formal_passed == formal_expected:
        status = "accepted"
    elif status == "accepted" and (formal_expected and formal_passed < formal_expected):
        status = "partial"
    return {
        "council": council,
        "member": member,
        "route": route,
        "status": status,
        "formal_passed": formal_passed,
        "formal_expected": formal_expected,
        "agents_passed": passed,
        "agents_attempted": attempted,
        "agents_failed_or_weak": failed,
        "first_pass_clean": not repair_or_reroute and failed == 0,
        "degraded": degraded,
        "missing_formal": missing_formal,
        "receipt_path": str(path),
        "run_id": receipt.get("run_id"),
        "obsolete_reason": OBSOLETE_ROUTES.get(route),
    }


def summarize_receipt(path: Path) -> dict[str, Any]:
    return summarize_receipt_data(load_json(path), path)


def find_receipts(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(list(root.rglob("rescored_matrix_receipt.json")) + list(root.rglob("matrix_receipt.json")))


def merge_route_receipts(receipts: list[tuple[Path, dict[str, Any]]]) -> list[tuple[Path, dict[str, Any]]]:
    by_route: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    for path, receipt in receipts:
        route = str(receipt.get("route") or path.parent.name)
        by_route.setdefault(route, []).append((path, receipt))
    merged: list[tuple[Path, dict[str, Any]]] = []
    for route_items in by_route.values():
        if len(route_items) == 1:
            merged.append(route_items[0])
            continue
        route_items = sorted(route_items, key=lambda item: item[0].stat().st_mtime)
        base_path, base = route_items[-1]
        formal_obligation: list[str] = []
        formal_completed: list[str] = []
        formal_paths: dict[str, list[str]] = {}
        groups: list[dict[str, Any]] = []
        statuses: list[str] = []
        run_ids: list[Any] = []
        for _, receipt in route_items:
            statuses.append(str(receipt.get("status") or "unknown"))
            run_ids.append(receipt.get("run_id"))
            for child in receipt.get("formal_child_obligation") or []:
                if child not in formal_obligation:
                    formal_obligation.append(child)
            for child in receipt.get("formal_children_completed") or []:
                if child not in formal_completed:
                    formal_completed.append(child)
            for child, paths in (receipt.get("formal_child_receipt_paths") or {}).items():
                formal_paths.setdefault(child, [])
                for receipt_path in paths:
                    if receipt_path not in formal_paths[child]:
                        formal_paths[child].append(receipt_path)
            groups.extend(receipt.get("groups") or [])
        merged_receipt = dict(base)
        merged_receipt["status"] = (
            "accepted"
            if formal_obligation and set(formal_obligation).issubset(set(formal_completed))
            else str(base.get("status") or "unknown")
        )
        merged_receipt["formal_child_obligation"] = formal_obligation
        merged_receipt["formal_children_completed"] = formal_completed
        merged_receipt["formal_child_receipt_paths"] = formal_paths
        merged_receipt["groups"] = groups
        merged_receipt["receipt_path"] = str(base_path)
        if len(set(run_ids)) == 1:
            merged_receipt["run_id"] = run_ids[0]
        merged.append((base_path, merged_receipt))
    return merged


def add_missing_required_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = {row["route"] for row in rows}
    for route in REQUIRED_ROUTES:
        if route in seen:
            continue
        council, member = COUNCIL_ORDER[route]
        rows.append(
            {
                "council": council,
                "member": member,
                "route": route,
                "status": "missing",
                "formal_passed": 0,
                "formal_expected": 0,
                "agents_passed": 0,
                "agents_attempted": 0,
                "agents_failed_or_weak": 0,
                "first_pass_clean": False,
                "degraded": [],
                "missing_formal": [],
                "receipt_path": "",
                "run_id": None,
                "obsolete_reason": None,
            }
        )
    return rows


def duplicate_route_status(rows: list[dict[str, Any]]) -> list[str]:
    counts: dict[str, int] = {}
    for row in rows:
        if row["route"] in REQUIRED_ROUTES:
            counts[row["route"]] = counts.get(row["route"], 0) + 1
    return sorted(route for route, count in counts.items() if count > 1)


def run_id_failures(rows: list[dict[str, Any]]) -> list[str]:
    current_rows = [row for row in rows if row["route"] in REQUIRED_ROUTES and row["status"] != "missing"]
    run_ids = {row.get("run_id") for row in current_rows}
    if any(not isinstance(run_id, str) or not run_id.strip() or run_id != run_id.strip() for run_id in run_ids):
        return ["missing_run_id"]
    if len(run_ids) > 1:
        return ["mixed_run_id:" + ",".join(sorted(str(item) for item in run_ids))]
    return []


def render(rows: list[dict[str, Any]]) -> str:
    rows = add_missing_required_rows(rows)
    council_rank = ["Management", "Decision", "Failure", "Follow-Up", "Other"]
    rows = sorted(rows, key=lambda row: (council_rank.index(row["council"]) if row["council"] in set(council_rank) else 99, row["member"]))
    lines = [
        "| Council | Member | Status | Formal children | Agents | Weak/failed | First-pass clean | Degraded |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        degraded = ", ".join(row["degraded"]) if row["degraded"] else "-"
        status = row["status"]
        if row.get("obsolete_reason"):
            status += f" ({row['obsolete_reason']})"
        if row["missing_formal"]:
            status += " missing:" + ",".join(row["missing_formal"])
        clean = "yes" if row.get("first_pass_clean") else "no"
        lines.append(
            f"| {row['council']} | {row['member']} | {status} | "
            f"{row['formal_passed']}/{row['formal_expected']} | "
            f"{row['agents_passed']}/{row['agents_attempted']} | "
            f"{row['agents_failed_or_weak']} | {clean} | {degraded} |"
        )
    duplicates = duplicate_route_status(rows)
    run_id_errors = run_id_failures(rows)
    current_count = sum(1 for row in rows if row["route"] in REQUIRED_ROUTES and row["status"] != "missing")
    invalid = [row for row in rows if row["status"] != "accepted"]
    if current_count != EXPECTED_CURRENT_TOPOLOGY_MEMBERS:
        invalid.append(
            {
                "route": "current_topology",
                "status": f"wrong_member_count:{current_count}/{EXPECTED_CURRENT_TOPOLOGY_MEMBERS}",
            }
        )
    if run_id_errors:
        invalid.append({"route": "run_id", "status": ",".join(run_id_errors)})
    if duplicates or invalid:
        lines.append("")
        lines.append("Status: INVALID current topology. Do not call this run FULL.")
        if duplicates:
            lines.append("Duplicate current routes: " + ", ".join(duplicates))
        if run_id_errors:
            lines.append("Run id gate: " + "; ".join(run_id_errors))
        invalid_routes = [f"{row['route']}={row['status']}" for row in invalid]
        if invalid_routes:
            lines.append("Blocking rows: " + "; ".join(invalid_routes))
    return "\n".join(lines)


def main() -> int:
    global REQUIRED_ROUTES, EXPECTED_CURRENT_TOPOLOGY_MEMBERS
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="Receipt file or directory paths")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON instead of Markdown")
    parser.add_argument("--required-routes", default="", help="Comma-separated required route set for compact/diagnostic runs.")
    args = parser.parse_args()
    if args.required_routes.strip():
        requested = tuple(route.strip() for route in args.required_routes.split(",") if route.strip())
        unknown = [route for route in requested if route not in COUNCIL_ORDER]
        if unknown:
            print(json.dumps({"error": "unknown_required_routes", "routes": unknown}, indent=2, sort_keys=True))
            return 2
        REQUIRED_ROUTES = requested
        EXPECTED_CURRENT_TOPOLOGY_MEMBERS = len(requested)

    receipts: list[Path] = []
    for item in args.paths:
        receipts.extend(find_receipts(Path(item)))
    loaded = [(path, load_json(path)) for path in receipts]
    rows = [summarize_receipt_data(receipt, path) for path, receipt in merge_route_receipts(loaded)]
    rows = add_missing_required_rows(rows)
    if args.json:
        print(json.dumps({"members": rows}, indent=2, sort_keys=True))
    else:
        print(render(rows))
    current_count = sum(1 for row in rows if row["route"] in REQUIRED_ROUTES and row["status"] != "missing")
    invalid = (
        any(row["status"] != "accepted" for row in rows)
        or bool(run_id_failures(rows))
        or current_count != EXPECTED_CURRENT_TOPOLOGY_MEMBERS
    )
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
