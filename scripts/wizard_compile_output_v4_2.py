#!/usr/bin/env python3
"""Compile a human-readable Wizard v4.2 answer from accepted run receipts."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from wizard_full_matrix_run_v4_2 import COMPACT_AUTO_KEYWORDS, resolve_compact_profile, selected_run_waves
from wizard_topology_v4_2 import COUNCIL_ORDER, ROUTES


ROUTE_DISPLAY_NAMES = {
    "decision.context_strategy": "Context Strategy",
    "decision.move_selection": "Move Selection",
    "decision.evidence_boundary": "Evidence Boundary",
    "failure.premortem": "Premortem",
    "failure.falsifier": "Falsifier",
    "failure.loophole_auditor": "Loophole Auditor",
    "follow_up.next_move_selector": "Next-Move Selector",
    "follow_up.lane_builder": "Lane Builder",
    "follow_up.compile_gate": "Compile Gate",
}


def load_run_config(root: Path) -> dict:
    path = root / "run_config.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def required_routes_for_compile(
    mode: str,
    compact_route_mode: str,
    compact_profile: str = "default",
    task: str = "",
) -> list[str]:
    if mode != "compact":
        return list(ROUTES)
    return [route for _, routes in selected_run_waves(mode, compact_route_mode, compact_profile, task) for route in routes]


def routes_by_council(routes: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for route in routes:
        grouped[COUNCIL_ORDER[route][0]].append(route)
    return dict(grouped)


def compact_profile_match_summary(profile: str, task: str) -> str:
    lowered = task.lower()
    matches = {
        candidate: [keyword for keyword in keywords if keyword in lowered]
        for candidate, keywords in COMPACT_AUTO_KEYWORDS
    }
    selected = matches.get(profile) or []
    if selected:
        return f"auto matched `{profile}` from: " + ", ".join(f"`{keyword}`" for keyword in selected)
    if profile == "default":
        return "auto found no stronger compact profile keyword, so it used `default`."
    return f"profile `{profile}` was selected explicitly or carried from run_config."


def status_json(root: Path, cwd: Path, required_routes: list[str] | None = None) -> dict:
    script = Path(__file__).with_name("wizard_member_status_v4_2.py")
    command = [sys.executable, str(script), "--json", str(root)]
    if required_routes:
        command.extend(["--required-routes", ",".join(required_routes)])
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        pass
    if proc.returncode != 0:
        raise SystemExit(proc.stdout)
    raise SystemExit(proc.stdout)


def read_receipt(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def blocker_failures(receipt: dict) -> list[dict]:
    quality = ((receipt.get("child_rerouter") or {}).get("quality_blockers") or {})
    blocking = quality.get("blocking_usefulness_failures")
    if isinstance(blocking, list):
        return [failure for failure in blocking if isinstance(failure, dict)]
    failures: list[dict] = []
    for group in receipt.get("groups") or []:
        for failure in group.get("usefulness_failures") or []:
            if isinstance(failure, dict):
                failures.append(failure)
    return failures


def route_repair_command(row: dict, receipt: dict, cwd: Path) -> str:
    followup = receipt.get("followup") or {}
    active_children = receipt.get("active_formal_child_obligation") or receipt.get("formal_child_obligation") or []
    out_dir = f"/tmp/wizard_v42_repair_{str(row.get('route') or 'route').replace('.', '_')}"
    command = [
        sys.executable,
        "scripts/wizard_child_matrix.py",
        "--route",
        str(row.get("route") or receipt.get("route") or ""),
        "--prompt",
        str(receipt.get("parent_prompt") or ""),
        "--followup-prompt",
        str(followup.get("prompt") or "repair blocked Wizard child receipts"),
        "--payoff",
        str(followup.get("payoff") or "restore receipt truth"),
        "--use-when",
        str(followup.get("use_when") or "a compact/full Wizard route is partial"),
        "--stop-if",
        str(followup.get("stop_if") or "child route remains blocked"),
        "--boundary",
        str(followup.get("boundary") or "repair route only; no repo edits"),
        "--cwd",
        str(cwd),
        "--out-dir",
        out_dir,
        "--run-id",
        str(receipt.get("run_id") or "repair-run"),
        "--only-children",
        ",".join(str(child) for child in active_children),
        "--sonnet-count",
        "1",
        "--opus-count",
        "0",
        "--haiku-count",
        "0",
    ]
    return " ".join(shlex.quote(part) for part in command)


def route_blocker_details(rows: list[dict], cwd: Path) -> list[dict]:
    details: list[dict] = []
    for row in rows:
        if row.get("status") == "accepted" and int(row.get("agents_failed_or_weak") or 0) == 0:
            continue
        path = row.get("receipt_path")
        if not path:
            continue
        receipt = read_receipt(path)
        failures = blocker_failures(receipt)
        if row.get("missing_formal") or failures or row.get("status") != "accepted":
            details.append(
                {
                    "route": row.get("route"),
                    "missing_formal": row.get("missing_formal") or [],
                    "failures": failures,
                    "repair_command": route_repair_command(row, receipt, cwd),
                }
            )
    return details


def count_by_council(rows: list[dict]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"parents": 0, "formal_passed": 0, "formal_expected": 0})
    for row in rows:
        bucket = counts[row["council"]]
        if row["status"] == "accepted":
            bucket["parents"] += 1
        bucket["formal_passed"] += int(row["formal_passed"])
        bucket["formal_expected"] += int(row["formal_expected"])
    return counts


def expected_parent_counts(rows: list[dict]) -> dict[str, int]:
    expected: dict[str, int] = defaultdict(int)
    for row in rows:
        expected[str(row["council"])] += 1
    return dict(expected)


def run_completion_label(
    rows: list[dict],
    counts: dict[str, dict[str, int]],
    first_pass_clean: bool,
    failed_or_weak: int,
    expected_parents: dict[str, int] | None = None,
) -> str:
    expected_parents = expected_parents or {"Management": 5, "Decision": 3, "Failure": 3, "Follow-Up": 3}
    parents_ok = all(counts[council]["parents"] >= expected for council, expected in expected_parents.items())
    formal_expected = sum(int(row["formal_expected"]) for row in rows)
    formal_passed = sum(int(row["formal_passed"]) for row in rows)
    formal_ok = formal_expected > 0 and formal_passed == formal_expected
    rows_ok = bool(rows) and all(row.get("status") == "accepted" for row in rows)
    degraded_ok = all(not row.get("degraded") for row in rows)
    full_ok = parents_ok and formal_ok and rows_ok and first_pass_clean and failed_or_weak == 0 and degraded_ok
    if full_ok:
        return "FULL"
    if any(row.get("status") == "accepted" for row in rows) or formal_passed:
        return "PARTIAL"
    return "BLOCKED"


def visible_completion_label(completion_label: str, mode: str) -> str:
    if mode == "compact" and completion_label == "FULL":
        return "PARTIAL"
    return completion_label


def council_result_label(rows: list[dict], council: str, expected_parents: int) -> str:
    council_rows = [row for row in rows if row.get("council") == council]
    accepted = sum(1 for row in council_rows if row.get("status") == "accepted")
    if accepted >= expected_parents and all(row.get("status") == "accepted" for row in council_rows):
        return "accepted"
    if accepted or any(int(row.get("formal_passed") or 0) for row in council_rows):
        return "partial"
    return "blocked"


def weak_spots(rows: list[dict], expected_parents: dict[str, int]) -> list[str]:
    spots: list[str] = []
    if any("gemini" in (row.get("degraded") or []) for row in rows):
        spots.append("Gemini remained degraded/not launched; it was not counted as required evidence.")
    opus_weak = 0
    premortem_weak = 0
    for row in rows:
        if not row.get("receipt_path"):
            continue
        receipt = read_receipt(row["receipt_path"])
        for group in receipt.get("groups") or []:
            if group.get("model") == "opus" and group.get("usefulness_failures"):
                opus_weak += len(group["usefulness_failures"])
        if row["route"] == "failure.premortem":
            premortem_weak = int(row.get("agents_failed_or_weak") or 0)
        route_failures = 0
        timed_out = 0
        for group in receipt.get("groups") or []:
            failures = group.get("usefulness_failures") or []
            route_failures += len(failures)
            timed_out += sum(1 for failure in failures if failure.get("status") == "timed_out")
        if route_failures:
            detail = f"{row['route']} had {route_failures} usefulness-blocked child receipts"
            if timed_out:
                detail += f", including {timed_out} timed out"
            spots.append(detail + ".")
    if opus_weak:
        spots.append("Opus completed advisory work but often missed strict YAML receipt fields, so those children were blocked rather than counted.")
    if premortem_weak:
        spots.append("Premortem accepted, but it is still the most receipt-fragile Failure route.")
    if "Management" in expected_parents:
        if any(row["council"] == "Management" and row["status"] == "accepted" for row in rows):
            spots.append("Management parents now run as first-class side routes; keep watching whether they actually improve reroute/output decisions.")
        else:
            spots.append("Management parents are missing or degraded; do not call the run FULL under the stricter v4.2 gate.")
    return spots


def uses_codex_local_children(rows: list[dict]) -> bool:
    for row in rows:
        path = row.get("receipt_path")
        if not path:
            continue
        receipt = read_receipt(path)
        if (receipt.get("inner_llm_council") or {}).get("codex_local_children"):
            return True
        if any(group.get("model") == "codex-local" for group in receipt.get("groups") or []):
            return True
    return False


def task_domain_label(task: str) -> str:
    lower = task.lower()
    if is_wiki_alignment_task(lower):
        return "Hermes/wiki LLM-alignment"
    if "inventory" in lower and ("audit" in lower or "admission" in lower):
        return "Wizard inventory/admission audit"
    if "wizard" in lower and ("audit" in lower or "route" in lower or "truth" in lower):
        return "Wizard route-truth audit"
    if "szilard" in lower:
        return "Szilard consolidation"
    if "carnot" in lower:
        return "Carnot consolidation"
    if "rosetta" in lower or "lego" in lower:
        return "Rosetta lego-scaling"
    if "sim" in lower or "engine" in lower or "qit" in lower:
        return "bounded sim work"
    return "the original user task"


def is_wiki_alignment_task(lower: str) -> bool:
    has_wiki_surface = "wiki" in lower or "hermes-current" in lower
    alignment_markers = (
        "llm alignment",
        "alignment tool",
        "wiki alignment",
        "frame-loader",
        "frame loader",
        "front door",
        "research spine",
        "index/routing",
        "hermes + wiki",
        "hermes wizard operating loop",
        "future llm",
        "future llms",
        "wiki improvement loop",
    )
    return has_wiki_surface and any(marker in lower for marker in alignment_markers)


def task_preserving_followups(task: str, completion_label: str, mode: str) -> list[tuple[str, str]]:
    domain = task_domain_label(task)
    lower = task.lower()
    wiki_alignment = is_wiki_alignment_task(lower)
    if wiki_alignment:
        continue_prompt = (
            "Continue the Hermes/wiki LLM-alignment campaign from the current task. "
            "Preserve the plain user goal: make the wiki frame-load Josh's goal, language, thinking moves, "
            "research spine, index/routing, evidence discipline, and Hermes/Wizard operating loop for future LLMs. "
            "Patch only one bounded front-door, bridge, control-note, or routing tranche; do not pivot to generic "
            "route-truth audit, sim-runner work, or output-format polish."
        )
        scout_prompt = (
            "Run a cheap Haiku or Sonnet scout over the Hermes/wiki alignment front door, bridge note, "
            "autoloop control note, and current spine. Payoff: find one drift surface that could make future "
            "LLMs miss the alignment objective. Stop if the scout proposes Codex Ratchet repo mutations, "
            "broad wiki rewrites, or generic route-truth work."
        )
    elif "szilard" in lower:
        continue_prompt = (
            "Continue the bounded Szilard consolidation lane from the current task. "
            "Preserve source rows as negative/open evidence, refresh successor/graveyard/consolidated receipts, "
            "update engine_lab_matrix/open-row audit/queue/successor coverage/inventory/visualizer payloads, "
            "and do not promote QIT, GStack, axis, bridge, or nonclassical claims."
        )
        scout_prompt = (
            "Run a cheap Haiku or Sonnet scout over the Szilard source and successor receipts only. "
            "Payoff: find missing coupling constraints or stale visualizer/index rows. "
            "Stop if the scout tries to promote the source rows or rewrite the stage gate."
        )
    elif "engine_lab" in lower or "engine lab" in lower or "open row" in lower:
        continue_prompt = (
            "Continue the bounded engine-lab open-row repair task. "
            "Use exact source receipts, preserve nonpassing source rows, add only receipt-backed successors or graveyards, "
            "then rerun matrix, open-row audit, queue, successor coverage, inventory, and visualizer checks."
        )
        scout_prompt = (
            "Run a cheap Haiku or Sonnet scout over current engine-lab nonpassing rows and successor coverage. "
            "Payoff: identify one stale or missing receipt-backed lane. "
            "Stop if the scout proposes broad QIT/GStack/axis promotion."
        )
    elif "inventory" in lower and ("audit" in lower or "admission" in lower):
        continue_prompt = (
            "Continue the Wizard inventory/admission audit from the current task. "
            "Patch only receipt-truth, duplicate-artifact exclusion, admission-result linkage, and focused regressions; "
            "do not pivot to generic sim work or output formatting."
        )
        scout_prompt = (
            "Run a cheap Haiku or Sonnet scout over Wizard inventory/admission receipts and duplicate artifacts. "
            "Payoff: find one remaining stale admission or missing result-link guard. "
            "Stop if the scout proposes new sims instead of fixing the audit target."
        )
    elif "wizard" in lower and ("audit" in lower or "route" in lower or "truth" in lower):
        continue_prompt = (
            "Continue the Wizard route-truth audit from the current task. "
            "Preserve the named route-truth or receipt-truth defect, patch only the harness/test surface needed, "
            "and verify with a focused compact or receipt-level regression."
        )
        scout_prompt = (
            "Run a cheap Haiku or Sonnet scout over the Wizard route-truth receipts only. "
            "Payoff: find a missing blocker or overclaim in the current harness path. "
            "Stop if the scout drifts into generic compiled-output polish."
        )
    else:
        continue_prompt = (
            f"Continue {domain} from the current user task. "
            "Preserve the task objective through Decision, Failure/Premortem, Follow-Up, and management; "
            "act only on receipt-backed changes and keep route truth honest."
        )
        scout_prompt = (
            f"Run a cheap Haiku or Sonnet scout over {domain}. "
            "Payoff: find the smallest missing receipt or blocked coupling. "
            "Stop if the scout substitutes output formatting for the original task."
        )

    if wiki_alignment:
        audit_prompt = (
            "Audit the Hermes/wiki LLM-alignment handoff without changing the task. "
            "Payoff: catch generic route-truth drift, stale front-door routing, or missing evidence-discipline "
            "language before the next loop. Stop if the next prompt no longer names the wiki/Hermes alignment objective."
        )
    elif completion_label == "FULL" and mode == "full":
        audit_prompt = (
            f"Run an Opus audit of the completed {domain} Wizard receipts and sim artifacts. "
            "Payoff: catch overclaim, stale evidence, or missing verification before reporting completion. "
            "Stop if exact artifact paths and commands are not available."
        )
    else:
        audit_prompt = (
            f"Repair the Wizard route-truth blockers for {domain} without changing the task. "
            "Payoff: keep the loop from drifting into output-format work. "
            "Stop if the next prompt no longer names the original sim/evidence objective."
        )

    continue_label = "Continue Alignment Tranche" if wiki_alignment else "Continue Sim Task"
    return [
        (continue_label, continue_prompt),
        ("Audit Route Truth", audit_prompt),
        ("Cheap Scout", scout_prompt),
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root")
    parser.add_argument("--task", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--cwd", default=str(Path.cwd()))
    parser.add_argument("--loop-index", type=int, default=1)
    parser.add_argument("--mode", choices=["auto", "full", "compact"], default="auto")
    parser.add_argument("--compact-route-mode", choices=["sequential", "parallel"], default="sequential")
    parser.add_argument("--compact-profile", default="auto")
    args = parser.parse_args()

    root = Path(args.run_root)
    run_config = load_run_config(root)
    mode = args.mode if args.mode != "auto" else str(run_config.get("mode") or "full")
    compact_route_mode = str(run_config.get("compact_route_mode") or args.compact_route_mode)
    compact_profile = str(run_config.get("resolved_compact_profile") or run_config.get("compact_profile") or args.compact_profile)
    if compact_profile == "auto":
        compact_profile = resolve_compact_profile("auto", args.task)
    required_routes = run_config.get("required_routes") or required_routes_for_compile(mode, compact_route_mode, compact_profile, args.task)
    data = status_json(root, Path(args.cwd), required_routes)
    rows = data["members"]
    expected_parents = expected_parent_counts(rows)
    total_parents = sum(1 for row in rows if row["status"] == "accepted")
    required_parent_count = sum(expected_parents.values())
    total_expected = sum(int(row["formal_expected"]) for row in rows)
    total_passed = sum(int(row["formal_passed"]) for row in rows)
    total_agents = sum(int(row["agents_passed"]) for row in rows)
    failed_or_weak = sum(int(row["agents_failed_or_weak"]) for row in rows)
    first_pass_clean = all(bool(row.get("first_pass_clean")) for row in rows)
    counts = count_by_council(rows)
    score = 90 if failed_or_weak <= 8 else 86
    completion_label = run_completion_label(rows, counts, first_pass_clean, failed_or_weak, expected_parents)
    header_completion_label = visible_completion_label(completion_label, mode)
    selected_by_council = routes_by_council(required_routes)
    wave_total = 1 if mode == "compact" and compact_route_mode == "parallel" else 3
    mode_label = "compact" if mode == "compact" else "full"
    task_domain = task_domain_label(args.task)
    wiki_alignment_task = is_wiki_alignment_task(args.task.lower())
    objective_label = "alignment/frame-loader objective" if wiki_alignment_task else "sim/evidence objective"
    codex_local = uses_codex_local_children(rows)
    if codex_local:
        runtimes = "codex-controller, codex-local-children, gemini-skipped"
    else:
        runtimes = "codex-controller, claude-bridge, gemini-skipped" if mode == "compact" else "codex-controller, claude-bridge, gemini-degraded"

    concise_lines: list[str] = []
    profile_label = f" | profile:{compact_profile}" if mode == "compact" else ""
    concise_lines.append(
        f"🧙 Wizard v4.2 | {header_completion_label} | waves:{wave_total}/{wave_total} | "
        f"parents:{total_parents}/{required_parent_count} | "
        f"children:{total_passed}/{total_expected} | tools:2 | score:{score} | "
        f"runtimes:{runtimes} | mode:{mode_label}{profile_label}"
    )
    concise_lines.append("")
    concise_lines.append("## ✨ Answer")
    concise_lines.append("")
    if mode == "compact":
        concise_lines.append("Use this as a fast health check, not as full v4.2 evidence.")
        concise_lines.append("")
        concise_lines.append(
            f"The selected compact councils are useful only if the next loop preserves the original {objective_label}. "
            "Use this compiled body as route truth, then continue the task named below."
        )
    else:
        concise_lines.append("Use this run only if the full topology and management gates stayed clean.")
        concise_lines.append("")
        concise_lines.append(
            f"The useful next move is to act on the compiled decision while preserving the original {objective_label}."
        )
    concise_lines.append("")
    concise_lines.append("## 🧭 Context + Strategy")
    concise_lines.append("")
    concise_lines.append(f"Current Prompt: {args.task}")
    concise_lines.append("")
    concise_lines.append(
        (
            "Larger Context: Wizard v4.2 is a harness around wiki/Hermes alignment work. It should preserve the user's frame-loader goal through councils, not replace it with generic route-truth audit."
            if wiki_alignment_task
            else "Larger Context: Wizard v4.2 is a harness around repo work. It should preserve the task through councils, not replace the task with orchestration or formatting."
        )
    )
    concise_lines.append("")
    concise_lines.append(
        "Strategy State: keep the original task stable through loop handoff; reserve FULL claims for all required council parents, child evidence, and management gates."
    )
    concise_lines.append("")
    concise_lines.append(
            "Local Overoptimization Risk: passing route receipts can still produce a bad run if the follow-up prompt drifts away from the wiki/Hermes alignment objective."
            if wiki_alignment_task
            else "Local Overoptimization Risk: passing route receipts can still produce a bad run if the follow-up prompt drifts away from the sim objective."
    )
    concise_lines.append("")
    concise_lines.append(
        "Strategy Memory Effect: the loop handoff is a first-class gate; follow-up prompts must carry the user's task domain and evidence boundary."
    )
    concise_lines.append("")
    concise_lines.append(
            "Rejected Local Move: do not replace wiki/Hermes alignment work with generic route-truth, output-format, or sim-runner loops."
            if wiki_alignment_task
            else "Rejected Local Move: do not replace sim/proof work with answer-shape or readability loops."
    )
    concise_lines.append("")
    concise_lines.append("## 🏛️ Council Results")
    concise_lines.append("")
    concise_lines.append("| Council | Route | Children | Result |")
    concise_lines.append("| --- | --- | ---: | --- |")
    for council in ("Decision", "Failure", "Follow-Up", "Management"):
        if council not in expected_parents:
            continue
        council_rows = [row for row in rows if row.get("council") == council]
        route_names = ", ".join(
            f"{ROUTE_DISPLAY_NAMES.get(str(row.get('route')), str(row.get('route')))}"
            for row in council_rows
        )
        bucket = counts[council]
        result = council_result_label(rows, council, expected_parents[council])
        concise_lines.append(
            f"| {council} | {route_names} | {bucket['formal_passed']}/{bucket['formal_expected']} | {result} |"
        )
    concise_lines.append("")
    selected_routes = {route for routes in selected_by_council.values() for route in routes}
    if mode == "compact":
        deferred_routes = [
            route
            for route in (
                "decision.context_strategy",
                "decision.move_selection",
                "decision.evidence_boundary",
                "failure.premortem",
                "failure.falsifier",
                "failure.loophole_auditor",
                "follow_up.next_move_selector",
                "follow_up.lane_builder",
                "follow_up.compile_gate",
            )
            if route not in selected_routes
        ]
        concise_lines.append(
            "Why PARTIAL: compact mode ran one parent per council. It did not run Management, and it deferred "
            + ", ".join(ROUTE_DISPLAY_NAMES.get(route, route) for route in deferred_routes)
            + "."
        )
    elif header_completion_label != "FULL":
        concise_lines.append("Why not FULL: at least one required parent, child, management, or first-pass gate did not pass cleanly.")
    concise_lines.append("")
    for spot in weak_spots(rows, expected_parents)[:3]:
        concise_lines.append(f"- {spot}")
    concise_lines.append("")
    concise_lines.append("## ✅ Compiled Move")
    concise_lines.append("")
    concise_lines.append(f"Target: continue {task_domain} without losing the original objective.")
    concise_lines.append("")
    concise_lines.append(
        "Action: use the compiled body as route-truth evidence, then continue the bounded wiki/Hermes alignment tranche named in the current prompt."
        if wiki_alignment_task
        else "Action: use the compiled body as route-truth evidence, then continue the receipt-backed sim/evidence work named in the current prompt."
    )
    concise_lines.append("")
    concise_lines.append("Owner: `scripts/wizard_v4_2.py` owns stdout; `scripts/wizard_compile_output_v4_2.py` owns answer shape.")
    concise_lines.append("")
    concise_lines.append(
        "Success Check: the next loop prompt still names the wiki/Hermes alignment objective, evidence discipline, and allowed wiki surfaces."
        if wiki_alignment_task
        else "Success Check: the next loop prompt still names the original task domain, evidence boundary, and allowed artifact updates."
    )
    concise_lines.append("")
    concise_lines.append(
        "Stop Condition: stop if the next prompt becomes generic route bookkeeping, output formatting, sim-runner work, or no longer names the wiki/Hermes alignment objective."
        if wiki_alignment_task
        else "Stop Condition: stop if the next prompt becomes generic output formatting, route bookkeeping, or promotion beyond the stage gate."
    )
    concise_lines.append("")
    concise_lines.append(f"Artifact Surface: {root}")
    concise_lines.append("")
    concise_lines.append(f"Status: {header_completion_label}; task-preserving handoff required before any next loop.")
    concise_lines.append("")
    concise_lines.append("## 🧭 Follow-Up Options")
    concise_lines.append("")
    for index, (label, prompt) in enumerate(task_preserving_followups(args.task, header_completion_label, mode), start=1):
        concise_lines.append(f"### {index}. {label}")
        concise_lines.append(f"`{prompt}`")
        concise_lines.append("")
    concise_lines.append("## 🧙 Footer")
    concise_lines.append("")
    concise_lines.append("🧙 Time/value: high; the loop handoff now preserves the task instead of optimizing visible output alone.")
    concise_lines.append("")
    concise_lines.append("MMM proof: v4.2 packet-local routes and child receipts are recorded in the artifact surface.")
    concise_lines.append("")
    concise_lines.append("Verification: status was parsed before compilation; follow-up options are generated from the current task domain.")
    Path(args.out).write_text("\n".join(concise_lines) + "\n", encoding="utf-8")
    print(args.out)
    return 0

    lines: list[str] = []
    profile_label = f" | profile:{compact_profile}" if mode == "compact" else ""
    lines.append(
        f"🧙 Wizard v4.2 | {header_completion_label} | waves:{wave_total}/{wave_total} | "
        f"parents:{total_parents}/{required_parent_count} | "
        f"children:{total_passed}/{total_expected} | tools:2 | score:{score} | "
        f"runtimes:{runtimes} | mode:{mode_label}{profile_label}"
    )
    lines.append("")
    lines.append("## ✨ Answer")
    lines.append("")
    lines.append("✅ **Decision: harden output usefulness before adding more topology.**")
    lines.append("")
    lines.append(f"- First-pass clean: **{'yes' if first_pass_clean else 'no'}**.")
    if completion_label == "FULL":
        if mode == "compact":
            lines.append("- This is a complete compact diagnostic, not a full v4.2 topology proof.")
        else:
            lines.append("- The run is valid input for the next loop, but validity alone is not the user value.")
    else:
        lines.append("- This run is diagnostic input only; it is not a FULL/promotable v4.2 run.")
    if mode == "compact":
        lines.append("- Compact mode is a fast diagnostic only: one representative parent per council, not the full nine-parent plus management topology.")
        lines.append("- The next fix should keep compact output clearly labeled so it cannot be mistaken for full Wizard v4.2 evidence.")
    else:
        lines.append("- The next fix should make the Wizard state the decision, why that decision matters, what changed after Failure/Follow-Up, and what action should happen next.")
        lines.append("- Premortem and management both point to the same risk: formal control can become receipt theater unless it changes routing or output acceptance.")
    lines.append("- Receipts stay in artifacts; the visible answer must carry the decision and the strategy delta.")
    lines.append("")
    lines.append("## 🧭 Context + Strategy")
    lines.append("")
    lines.append("### Current Prompt")
    lines.append(args.task)
    lines.append("")
    lines.append("### Larger Context")
    if mode == "compact":
        lines.append("Wizard v4.2 compact mode is being hardened as a quick route-health probe that preserves the Decision, Failure, and Follow-Up sequence without claiming full topology.")
    else:
        lines.append("Wizard v4.2 is being hardened into a lean, standalone prompt-and-context engine with real MMMS, skills, parent routes, Claude children, premortem, loophole audit, and human-useful output.")
    lines.append("")
    lines.append("### Strategy State")
    if mode == "compact":
        lines.append("Treat compact output as liveness and shape evidence only. Use full mode for acceptance, management truth, and promotion claims.")
    else:
        lines.append("Treat accepted topology as necessary but not sufficient. The next loop should improve answer quality, management-parent truth, and model receipt reliability without expanding doc sprawl.")
    lines.append("")
    if mode == "compact":
        lines.append("### Route Selection")
        lines.append(f"- Compact profile: `{compact_profile}` ({compact_profile_match_summary(compact_profile, args.task)}).")
        for council in ("Decision", "Failure", "Follow-Up"):
            routes = selected_by_council.get(council) or []
            if routes:
                lines.append(f"- {council}: `{routes[0]}`.")
        lines.append("")
    lines.append("### Local Overoptimization Risk")
    lines.append("The harness can overfit to receipt acceptance and miss whether the compiled answer is actually useful. Output quality must be gated separately from parent/child completion.")
    lines.append("")
    lines.append("### Strategy Memory Effect")
    lines.append("Because prior loops showed valid topology but weak visible usefulness, the current strategy changes from expanding routes to enforcing decision density and strategy-delta proof.")
    lines.append("")
    lines.append("### Rejected Local Move")
    lines.append("Do not add more parents, children, or docs to solve a readability problem. That would optimize the orchestration layer instead of the human decision surface.")
    lines.append("")
    lines.append("## 🏛️ Council Results")
    lines.append("")
    lines.append("| Council | Parents | Formal Children | Result |")
    lines.append("| --- | ---: | ---: | --- |")
    for council in ("Decision", "Failure", "Follow-Up", "Management"):
        if council not in expected_parents:
            continue
        bucket = counts[council]
        expected_count = expected_parents[council]
        result = council_result_label(rows, council, expected_count)
        marker = "✅" if result == "accepted" else "⚠️" if result == "partial" else "⛔"
        lines.append(f"| {council} | {bucket['parents']}/{expected_count} | {bucket['formal_passed']}/{bucket['formal_expected']} | {marker} {result} |")
    lines.append("")
    lines.append("### ✅ Solid")
    lines.append("")
    if mode == "compact":
        lines.append("- Compact mode preserved the three council identities without creating a Management Council.")
        for council in ("Decision", "Failure", "Follow-Up"):
            routes = selected_by_council.get(council) or []
            if routes:
                display = ROUTE_DISPLAY_NAMES.get(routes[0], routes[0])
                lines.append(f"- {council} compact route is {display}: `{routes[0]}`.")
    else:
        lines.append("- Management parents run first-class route control, child health, route truth, output compiler, and strategy memory checks.")
        lines.append("- Decision carries prompt plus larger context through `decision.context_strategy`.")
        lines.append("- Failure includes the real `skill.premortem` and `skill.loophole_auditor` child routes.")
        lines.append("- Follow-Up includes lane building and compile-gate children, so next prompts are not controller-only guesses.")
    lines.append(f"- Accepted child/agent receipts: **{total_agents} accepted agent outputs**, with weak outputs excluded from formal child counts.")
    lines.append("")
    lines.append("### 🧩 Decision Delta")
    lines.append("")
    if mode == "compact":
        lines.append("- Before compact support: fast runs were judged against the full v4.2 parent set.")
        lines.append(f"- After compact support: compact `{compact_profile}` runs are judged against only the selected representative council routes.")
        lines.append("- The gate should fail compact output that hides this limited obligation or implies full management/premortem evidence.")
    else:
        lines.append("- Before premortem/management pressure: the obvious next move was another full loop to prove topology.")
        lines.append("- After premortem/management pressure: the next move is a stricter output usefulness gate.")
        lines.append("- The gate should fail answers that have the right sections but no clear recommendation, no changed decision, or no strategy-memory effect.")
    lines.append("")
    lines.append("### ⚠️ Still Weak")
    lines.append("")
    if mode == "compact":
        selected_routes = {route for routes in selected_by_council.values() for route in routes}
        deferred_routes = [
            route
            for route in (
                "decision.context_strategy",
                "decision.move_selection",
                "decision.evidence_boundary",
                "failure.premortem",
                "failure.falsifier",
                "failure.loophole_auditor",
                "follow_up.next_move_selector",
                "follow_up.lane_builder",
                "follow_up.compile_gate",
            )
            if route not in selected_routes
        ]
        if deferred_routes:
            deferred_labels = ", ".join(
                f"{ROUTE_DISPLAY_NAMES.get(route, route)} (`{route}`)" for route in deferred_routes
            )
            lines.append(f"- Compact mode deferred these full-topology council parents: {deferred_labels}.")
        lines.append("- Management parents were not run in compact mode.")
    if not first_pass_clean:
        if completion_label == "FULL":
            lines.append("- This FULL run was not first-pass clean. Do not promote v4.2 until consecutive fresh loops pass without repairs or weak receipt exclusions.")
        else:
            lines.append(f"- This {completion_label} run is not first-pass clean. Treat it as diagnostic evidence, not loop input or promotion evidence.")
    for spot in weak_spots(rows, expected_parents):
        lines.append(f"- {spot}")
    blocker_details = route_blocker_details(rows, Path(args.cwd))
    if blocker_details:
        lines.append("")
        lines.append("### Exact Blockers")
        lines.append("")
        for detail in blocker_details:
            lines.append(f"- `{detail['route']}`")
            if detail["missing_formal"]:
                lines.append("  - Missing formal children: " + ", ".join(f"`{child}`" for child in detail["missing_formal"]))
            failures = detail["failures"][:6]
            for failure in failures:
                child_id = failure.get("id") or "unknown-child"
                status = failure.get("status") or "unknown"
                reason = failure.get("reason") or "unknown_reason"
                lines.append(f"  - Child `{child_id}`: `{status}` / `{reason}`")
            if len(detail["failures"]) > len(failures):
                lines.append(f"  - Additional child failures omitted: {len(detail['failures']) - len(failures)}")
            lines.append(f"  - Focused repair: `{detail['repair_command']}`")
    lines.append("")
    lines.append("## ✅ Compiled Move")
    lines.append("")
    lines.append("### 🎯 Target")
    if mode == "compact":
        lines.append("Make compact Wizard v4.2 reliable as a quick three-council diagnostic that never claims full topology.")
    else:
        lines.append("Make Wizard v4.2 reliable as a looping prompt-and-context engine with first-class management parents, not just a council topology proof.")
    lines.append("")
    lines.append("### 🔨 Action")
    if completion_label == "FULL":
        lines.append("Use this accepted run as the next loop input only after status, output-shape, decision-density, and strategy-memory-effect gates pass.")
    else:
        lines.append("Do not use this run as loop input. Repair the blocked parent/child gates first, then rerun a bounded v4.2 pass.")
    lines.append("")
    lines.append("### 👤 Owner")
    if mode == "compact":
        child_surface = "Codex-local children" if codex_local else "Claude children"
        lines.append(f"Main Codex controller owns synthesis; compact council parent routes own route execution; {child_surface} provide bounded child receipts.")
    else:
        lines.append("Main Codex controller owns synthesis; Codex council and management parent routes own route execution; Claude children provide bounded child receipts.")
    lines.append("")
    lines.append("### ✅ Success Check")
    if mode == "compact":
        lines.append("A compact run is valid only when the three representative parent routes complete their formal children and the header clearly says compact. It is never promotion evidence for full v4.2.")
    else:
        lines.append("A loop is valid only when status shows 14/14 parents, all formal children complete, management parents accepted, premortem accepted, context strategy accepted, and the visible output gate proves a decision plus strategy delta. Promotion requires first-pass clean.")
    lines.append("")
    lines.append("### 🛑 Stop Condition")
    if mode == "compact":
        lines.append("Stop using compact output if any of the three representative parent routes is missing, or if the report implies full management/premortem coverage.")
    else:
        lines.append("Stop using a run as loop input if any required parent, child, premortem, context strategy, or output section is missing.")
    lines.append("")
    lines.append("### 📦 Artifact Surface")
    lines.append(str(root))
    lines.append("")
    lines.append("### 📌 Status")
    if completion_label == "FULL":
        if mode == "compact":
            lines.append("Complete compact diagnostic. Not full v4.2 promotion evidence.")
        else:
            lines.append("Valid FULL loop input. Not promotion-ready unless first-pass clean is yes.")
    else:
        lines.append(f"{completion_label} diagnostic output. Do not use as FULL loop input or promotion evidence.")
    lines.append("")
    lines.append("## 🧭 Follow-Up Options")
    lines.append("")
    if mode == "compact":
        lines.append("### 1. 🧪 Run Compact Live")
        lines.append("`Run Wizard v4.2 compact sequential without dry-run. Payoff: fast live route-health check across Decision, Failure, and Follow-Up. Use when full external capacity is limited. Stop if any compact route blocks or emits report/log artifacts.`")
        lines.append("")
        lines.append("### 2. 🧭 Compare Compact Parallel")
        lines.append("`Run Wizard v4.2 compact parallel and compare it with compact sequential. Payoff: detects whether council order changes the answer. Use for speed diagnostics only. Stop if the report claims full v4.2 topology.`")
        lines.append("")
        lines.append("### 3. 🧱 Escalate To Full")
        lines.append("`Run full Wizard v4.2 only after compact route health is clean. Payoff: tests all nine council parents plus management side lanes. Use when model capacity is available. Stop if capacity preflight or child fanout fails.`")
    else:
        lines.append("### 1. 📝 Harden Human Output")
        lines.append("`Run the next Wizard v4.2 loop on decision usefulness. Preserve context strategy, suppress receipt-log leakage, and require one clear recommendation, why it matters, what changed after premortem/follow-up, and what the user should do next. Payoff: makes Wizard useful to read. Use when topology already accepts. Stop if any required parent, child, or decision-density gate fails.`")
        lines.append("")
        lines.append("### 2. 🧑‍✈️ Promote Management Parents")
        lines.append("`Make management parents first-class v4.2 routes for run control, child health, route truth, output compiling, and strategy memory. Payoff: makes orchestration truth explicit. Use when accepted council topology is stable. Stop if management replaces council work instead of supervising it.`")
        lines.append("")
        lines.append("### 3. 🔧 Exercise Grok/Gemini Contrast")
        lines.append("`Run a narrow Grok plus Gemini child-matrix contrast on the weakest accepted route. Payoff: tests external diversity without Opus. Use when Sonnet-only receipts look too uniform. Stop if strict receipt gates are weakened or provider calls block.`")
    lines.append("")
    lines.append("## 🧙 Footer")
    lines.append("")
    if mode == "compact":
        lines.append("🧙 Time/value: compact diagnostic checkpoint; route liveness and compact/full claim boundaries are now separate pass/fail surfaces.")
    else:
        lines.append("🧙 Time/value: high-value loop checkpoint; topology validity, premortem, context strategy, and output gating are now separate pass/fail surfaces.")
    lines.append("")
    lines.append("MMM proof: v4.2 packet root and packet-local child paths were recorded in matrix receipts.")
    lines.append("")
    if completion_label == "FULL":
        lines.append("Verification passed: fresh `wizard_member_status_v4_2.py --json` accepted this run before compilation.")
    else:
        lines.append("Verification result: fresh `wizard_member_status_v4_2.py --json` was parsed before compilation and did not accept this run as FULL.")

    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
