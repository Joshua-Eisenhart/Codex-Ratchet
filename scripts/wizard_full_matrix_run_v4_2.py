#!/usr/bin/env python3
"""Run Wizard v4.2 with council waves and parallel routes inside each wave."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from wizard_topology_v4_2 import COUNCIL_ORDER, FORMAL_CHILDREN, MANAGEMENT_PARENTS, ROUTES


COUNCIL_ROUTES = {
    "Decision": [route for route in ROUTES if COUNCIL_ORDER[route][0] == "Decision"],
    "Failure": [route for route in ROUTES if COUNCIL_ORDER[route][0] == "Failure"],
    "Follow-Up": [route for route in ROUTES if COUNCIL_ORDER[route][0] == "Follow-Up"],
}
MANAGEMENT_ROUTES = list(MANAGEMENT_PARENTS)
MANAGEMENT_SIDE_ROUTES = {
    "Decision": ["manager.run_controller", "manager.child_health"],
    "Failure": ["manager.strategy_memory"],
    "Follow-Up": ["manager.route_truth", "manager.output_compiler"],
}
COMPACT_COUNCIL_ROUTES = {
    "Decision": ["decision.move_selection"],
    "Failure": ["failure.falsifier"],
    "Follow-Up": ["follow_up.compile_gate"],
}
COMPACT_PROFILE_ROUTES = {
    "default": {
        "Decision": "decision.move_selection",
        "Failure": "failure.falsifier",
        "Follow-Up": "follow_up.compile_gate",
    },
    "audit": {
        "Decision": "decision.evidence_boundary",
        "Failure": "failure.loophole_auditor",
        "Follow-Up": "follow_up.compile_gate",
    },
    "strategy": {
        "Decision": "decision.context_strategy",
        "Failure": "failure.premortem",
        "Follow-Up": "follow_up.lane_builder",
    },
    "followup": {
        "Decision": "decision.move_selection",
        "Failure": "failure.falsifier",
        "Follow-Up": "follow_up.next_move_selector",
    },
    "formatting": {
        "Decision": "decision.evidence_boundary",
        "Failure": "failure.falsifier",
        "Follow-Up": "follow_up.compile_gate",
    },
}
COMPACT_AUTO_KEYWORDS = (
    ("audit", ("audit", "verify", "evidence", "overclaim", "route truth", "loophole", "regression", "safety")),
    ("strategy", ("strategy", "context", "state", "sequence", "plan", "preserve", "memory", "roadmap")),
    ("followup", ("follow-up", "follow up", "next prompt", "next move", "options", "lane", "prompt")),
    ("formatting", ("format", "formatting", "nice", "clean output", "compiled", "report", "header", "readable")),
)
CAPACITY_BLOCK_PATTERNS = (
    "you've hit your limit",
    "hit your limit",
    "you have exhausted your capacity",
    "quota will reset",
)
PREMORTEM_ARTIFACT_PATTERNS = (
    "premortem-report-*.html",
    "premortem-transcript-*.md",
)
CANONICAL_CLAUDE_BRIDGE = Path.home() / ".codex/skills/claude-bridge/scripts/claude_bridge.py"


def claude_python_executable() -> str:
    configured = os.environ.get("WIZARD_CLAUDE_PYTHON", "").strip()
    if configured:
        return configured
    return shutil.which("python3") or sys.executable


def run_command(command: list[str], cwd: Path, stdout=None) -> int:
    proc = subprocess.run(command, cwd=str(cwd), text=True, stdout=stdout, stderr=subprocess.STDOUT, check=False)
    return proc.returncode


def route_prompt(route: str, task: str, repair_children: list[str] | None = None) -> str:
    council, member = COUNCIL_ORDER[route]
    if repair_children:
        return (
            f"Repair Wizard v4.2 {council} parent route {route} / {member} by rerunning only these "
            f"formal children: {', '.join(repair_children)}. Preserve prompt plus larger context plus strategy state. "
            "Return concise YAML receipt fields only; no repo edits, no logs, no browser."
        )
    if council == "Management":
        return (
            f"Run Wizard v4.2 Management parent route {route} / {member} for this task: {task}. "
            "Supervise route truth, liveness, reroute decisions, output compiling, and strategy memory. "
            "Do not replace council work. Return management receipt fields and concise route-specific findings only; no logs."
        )
    return (
        f"Run Wizard v4.2 {council} parent route {route} / {member} for this task: {task}. "
        "Process both the current prompt and the larger active context. Preserve strategy state, identify local-overoptimization risk, "
        "and return concise route-specific findings plus parent/child truth. Do not emit process logs."
    )


def compact_active_children(route: str, args: argparse.Namespace) -> list[str]:
    """Return the formal child obligation that compact mode actually launches."""
    if getattr(args, "mode", "full") != "compact":
        return []
    formal_children = FORMAL_CHILDREN.get(route, [])
    if not formal_children:
        return []
    requested_count = max(1, args.sonnet_count, args.opus_count, args.haiku_count)
    return formal_children[: min(requested_count, len(formal_children))]


def route_command(args: argparse.Namespace, route: str, root: Path, repair_children: list[str] | None = None) -> list[str]:
    script = Path(__file__).with_name("wizard_child_matrix.py")
    sonnet_count = args.sonnet_count
    opus_count = args.opus_count
    haiku_count = args.haiku_count
    if getattr(args, "mode", "full") == "compact" and not repair_children:
        formal_count = len(FORMAL_CHILDREN.get(route, []))
        if formal_count:
            sonnet_count = min(sonnet_count, formal_count)
            opus_count = min(opus_count, formal_count)
            haiku_count = min(haiku_count, formal_count)
    if repair_children:
        repair_count = len(repair_children)
        if repair_count:
            sonnet_count = min(sonnet_count, repair_count)
            opus_count = min(opus_count, repair_count)
            haiku_count = min(haiku_count, repair_count)
    command = [
        sys.executable,
        str(script),
        "--route",
        route,
        "--prompt",
        route_prompt(route, args.task, repair_children),
        "--followup-prompt",
        args.followup_prompt,
        "--payoff",
        args.payoff,
        "--use-when",
        args.use_when,
        "--stop-if",
        args.stop_if,
        "--boundary",
        args.boundary,
        "--cwd",
        str(args.cwd),
        "--out-dir",
        str(root),
        "--run-id",
        args.run_id,
        "--sonnet-timeout-sec",
        str(args.sonnet_timeout_sec),
        "--opus-timeout-sec",
        str(args.opus_timeout_sec),
        "--haiku-timeout-sec",
        str(args.haiku_timeout_sec),
        "--grok-timeout-sec",
        str(getattr(args, "grok_timeout_sec", 90)),
        "--sonnet-count",
        str(sonnet_count),
        "--opus-count",
        str(opus_count),
        "--haiku-count",
        str(haiku_count),
        "--sonnet-budget",
        str(args.sonnet_budget),
        "--opus-budget",
        str(args.opus_budget),
        "--haiku-budget",
        str(args.haiku_budget),
        "--global-max-active",
        str(args.global_max_active),
        "--max-concurrency",
        str(args.max_concurrency),
    ]
    if repair_children:
        command.extend(["--only-children", ",".join(repair_children)])
    else:
        active_children = compact_active_children(route, args)
        if active_children:
            command.extend(["--only-children", ",".join(active_children)])
    if args.parallel_model_groups:
        command.append("--parallel-model-groups")
    if getattr(args, "codex_local_children", False):
        command.append("--codex-local-children")
    repair_mode = bool(repair_children)
    if args.full_model_council and not (repair_mode and args.repair_single_model):
        command.append("--full-model-council")
    if args.attempt_gemini and not args.skip_gemini and not (repair_mode and args.repair_skip_gemini):
        command.append("--attempt-gemini")
    if getattr(args, "attempt_grok", False) and not repair_mode:
        command.append("--attempt-grok")
    if args.dry_run:
        command.append("--dry-run")
    return command


def run_route(args: argparse.Namespace, route: str, root: Path, repair_children: list[str] | None = None) -> int:
    command = route_command(args, route, root, repair_children)
    print(f"== {'repair ' if repair_children else ''}{route} ==")
    return run_command(command, Path(args.cwd))


def run_routes_parallel(
    args: argparse.Namespace,
    routes: list[str],
    root: Path,
    repair_by_route: dict[str, list[str]] | None = None,
) -> dict[str, int]:
    """Launch sibling parent routes together; each route handles its own child fanout."""
    procs: dict[str, tuple[subprocess.Popen, object]] = {}
    repair_by_route = repair_by_route or {}
    for route in routes:
        repair_children = repair_by_route.get(route)
        route_dir = root / route
        route_dir.mkdir(parents=True, exist_ok=True)
        log_path = route_dir / ("repair_stdout.log" if repair_children else "runner_stdout.log")
        log_handle = log_path.open("w", encoding="utf-8")
        command = route_command(args, route, root, repair_children)
        label = f"repair {route}" if repair_children else route
        print(f"== launch {label} ==")
        proc = subprocess.Popen(
            command,
            cwd=str(args.cwd),
            text=True,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
        )
        procs[route] = (proc, log_handle)

    results: dict[str, int] = {}
    for route, (proc, log_handle) in procs.items():
        results[route] = proc.wait()
        log_handle.close()
        print(f"== done {route}: {results[route]} ==")
    return results


def resolve_compact_profile(profile: str, task: str = "") -> str:
    if profile != "auto":
        return profile if profile in COMPACT_PROFILE_ROUTES else "default"
    lowered = task.lower()
    best_profile = "default"
    best_score = 0
    for candidate, keywords in COMPACT_AUTO_KEYWORDS:
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > best_score:
            best_profile = candidate
            best_score = score
    return best_profile


def compact_council_routes(council: str, compact_profile: str = "default", task: str = "") -> list[str]:
    profile = resolve_compact_profile(compact_profile, task)
    return [COMPACT_PROFILE_ROUTES[profile][council]]


def council_wave_routes(council: str, mode: str = "full", compact_profile: str = "default", task: str = "") -> list[str]:
    if mode == "compact":
        return compact_council_routes(council, compact_profile, task)
    return [*COUNCIL_ROUTES[council], *MANAGEMENT_SIDE_ROUTES.get(council, [])]


def selected_run_waves(
    mode: str,
    compact_route_mode: str,
    compact_profile: str = "default",
    task: str = "",
) -> list[tuple[str, list[str]]]:
    if mode == "compact" and compact_route_mode == "parallel":
        return [
            (
                "Compact",
                [route for council in ("Decision", "Failure", "Follow-Up") for route in compact_council_routes(council, compact_profile, task)],
            )
        ]
    return [(council, council_wave_routes(council, mode, compact_profile, task)) for council in ("Decision", "Failure", "Follow-Up")]


def required_routes_for_run(
    mode: str,
    compact_route_mode: str,
    compact_profile: str = "default",
    task: str = "",
) -> list[str] | None:
    if mode != "compact":
        return None
    return [route for _, routes in selected_run_waves(mode, compact_route_mode, compact_profile, task) for route in routes]


def status_json(root: Path, cwd: Path, required_routes: list[str] | None = None) -> tuple[int, dict]:
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
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {"parse_error": proc.stdout}
    return proc.returncode, data


def capacity_blockers(root: Path) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    for path in root.rglob("*"):
        if not capacity_scan_candidate(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            continue
        for pattern in CAPACITY_BLOCK_PATTERNS:
            if pattern in text:
                blockers.append({"path": str(path), "pattern": pattern})
                break
        if len(blockers) >= 20:
            break
    return blockers


def capacity_scan_candidate(path: Path) -> bool:
    return path.is_file() and path.suffix in {".json", ".log", ".txt"}


def premortem_artifacts(cwd: Path) -> set[str]:
    artifacts: set[str] = set()
    for pattern in PREMORTEM_ARTIFACT_PATTERNS:
        artifacts.update(str(path) for path in cwd.glob(pattern) if path.is_file())
    return artifacts


def new_premortem_artifacts(cwd: Path, baseline: set[str]) -> list[str]:
    return sorted(premortem_artifacts(cwd) - baseline)


def text_capacity_pattern(text: str) -> str | None:
    lowered = text.lower()
    for pattern in CAPACITY_BLOCK_PATTERNS:
        if pattern in lowered:
            return pattern
    return None


def external_capacity_preflight(args: argparse.Namespace, root: Path) -> dict[str, object]:
    """Run tiny bridge probes before launching the expensive v4.2 fanout."""
    if getattr(args, "codex_local_children", False):
        return {"status": "skipped", "reason": "codex_local_children", "probes": []}
    if args.dry_run and not args.capacity_preflight_only or not args.capacity_preflight:
        return {"status": "skipped", "reason": "dry_run_or_disabled", "probes": []}
    bridge = CANONICAL_CLAUDE_BRIDGE
    if not bridge.exists():
        return {"status": "blocked", "reason": "missing_claude_bridge", "path": str(bridge), "probes": []}
    preflight_dir = root / "_capacity_preflight"
    preflight_dir.mkdir(parents=True, exist_ok=True)
    probes: list[dict[str, object]] = []
    for model in args.capacity_preflight_models.split(","):
        model = model.strip()
        if not model:
            continue
        out_dir = preflight_dir / model
        out_dir.mkdir(parents=True, exist_ok=True)
        command = [
            claude_python_executable(),
            str(bridge),
            "--model",
            model,
            "--effort",
            "low",
            "--budget",
            str(args.capacity_preflight_budget),
            "--timeout-sec",
            str(args.capacity_preflight_timeout_sec),
            "--cwd",
            str(args.cwd),
            "--out-dir",
            str(out_dir),
            "--name",
            f"wizard-v4-2-capacity-preflight-{model}",
            "--prompt",
            "Return YAML only: id: capacity_preflight status: accepted conclusion: ready",
        ]
        completed = subprocess.run(
            command,
            cwd=str(args.cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        pattern = text_capacity_pattern(completed.stdout)
        probe = {
            "model": model,
            "returncode": completed.returncode,
            "capacity_pattern": pattern,
            "stdout_preview": completed.stdout[:500],
        }
        probes.append(probe)
        if pattern:
            return {"status": "blocked", "reason": "external_model_capacity", "probes": probes}
    failed = [probe for probe in probes if probe["returncode"]]
    if failed:
        return {"status": "blocked", "reason": "external_model_preflight_failed", "probes": probes}
    return {"status": "passed", "probes": probes}


def repair_children_by_route(
    status: dict,
    *,
    repair_first_pass_unclean: bool = False,
    max_repair_routes: int | None = None,
) -> dict[str, list[str]]:
    repair: dict[str, list[str]] = {}
    for row in status.get("members") or []:
        route = row.get("route")
        if route not in FORMAL_CHILDREN:
            continue
        missing_formal = row.get("missing_formal") or []
        if row.get("status") == "missing":
            repair[route] = list(FORMAL_CHILDREN[route])
        elif missing_formal:
            repair[route] = list(missing_formal)
        elif row.get("status") != "accepted":
            repair[route] = list(FORMAL_CHILDREN[route])
        elif repair_first_pass_unclean and not row.get("first_pass_clean"):
            repair[route] = list(FORMAL_CHILDREN[route])
        if max_repair_routes is not None and len(repair) >= max_repair_routes:
            break
    return repair


def all_members_first_pass_clean(status: dict) -> bool:
    members = status.get("members") or []
    return bool(members) and all(
        row.get("status") == "accepted" and bool(row.get("first_pass_clean"))
        for row in members
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--cwd", default=str(Path.cwd()))
    parser.add_argument("--out-dir", default="/tmp/wizard_v4_2_full")
    parser.add_argument("--mode", choices=["full", "compact"], default="full")
    parser.add_argument("--compact-route-mode", choices=["sequential", "parallel"], default="sequential", help="Compact mode can preserve council order or launch the three selected representatives together.")
    parser.add_argument("--compact-profile", choices=["auto", *COMPACT_PROFILE_ROUTES.keys()], default="default", help="Compact member selection profile. Use auto to choose one member per council from task keywords.")
    parser.add_argument("--max-repair-loops", type=int, default=3)
    parser.add_argument("--max-repair-routes", type=int, default=3, help="Maximum parent routes to repair in one loop; keeps v4.2 from launching unbounded repair storms.")
    parser.add_argument("--followup-prompt", default="Produce the best next prompt for hardening v4.2, preserving prompt plus larger context plus strategy state.")
    parser.add_argument("--payoff", default="Validate Wizard v4.2 as a full runnable topology with context-aware output.")
    parser.add_argument("--use-when", default="Running Wizard v4.2 end to end.")
    parser.add_argument("--stop-if", default="Stop if a required route or formal child cannot complete after bounded repair.")
    parser.add_argument("--boundary", default="No repo edits from child routes; receipts only under /tmp.")
    parser.add_argument("--sonnet-timeout-sec", type=int, default=260)
    parser.add_argument("--opus-timeout-sec", type=int, default=320)
    parser.add_argument("--haiku-timeout-sec", type=int, default=160)
    parser.add_argument("--grok-timeout-sec", type=int, default=90)
    parser.add_argument("--sonnet-count", type=int, default=0)
    parser.add_argument("--opus-count", type=int, default=0)
    parser.add_argument("--haiku-count", type=int, default=1)
    parser.add_argument("--sonnet-budget", type=float, default=1.5)
    parser.add_argument("--opus-budget", type=float, default=2.0)
    parser.add_argument("--haiku-budget", type=float, default=0.5)
    parser.add_argument("--global-max-active", type=int, default=4)
    parser.add_argument("--max-concurrency", type=int, default=4)
    parser.add_argument("--parallel-model-groups", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--full-model-council", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--codex-local-children", action="store_true", help="Use local Codex child receipts instead of Claude/Gemini fanout. Best for compact diagnostics during external quota blocks.")
    parser.add_argument("--attempt-gemini", action="store_true", default=False)
    parser.add_argument("--attempt-grok", action="store_true", default=False)
    parser.add_argument("--skip-gemini", action="store_true")
    parser.add_argument("--repair-single-model", action=argparse.BooleanOptionalAction, default=True, help="Use a smaller repair fanout instead of another full model council.")
    parser.add_argument("--repair-skip-gemini", action=argparse.BooleanOptionalAction, default=True, help="Skip Gemini during repair loops unless explicitly disabled.")
    parser.add_argument("--repair-first-pass-unclean", action="store_true", help="Also repair accepted routes that were not first-pass clean. Off by default to avoid costly cosmetic repair storms.")
    parser.add_argument("--capacity-preflight", action=argparse.BooleanOptionalAction, default=True, help="Run tiny external model probes before expensive v4.2 fanout.")
    parser.add_argument("--capacity-preflight-only", action="store_true", help="Run only external capacity preflight, then exit before council waves.")
    parser.add_argument("--capacity-preflight-models", default="sonnet,opus,haiku")
    parser.add_argument("--capacity-preflight-timeout-sec", type=int, default=45)
    parser.add_argument("--capacity-preflight-budget", type=float, default=0.5, help="Budget for tiny external model probes; must cover Claude cached context setup.")
    parser.add_argument("--dry-run", action="store_true", help="Forward dry-run to child matrices for local topology rehearsal only; never counts as FULL.")
    args = parser.parse_args()

    args.cwd = Path(args.cwd)
    if args.mode == "compact":
        args.resolved_compact_profile = resolve_compact_profile(args.compact_profile, args.task)
        if args.sonnet_count == 0:
            args.sonnet_count = 1
        if args.opus_count == 0:
            args.opus_count = 1
        args.haiku_count = 0 if args.haiku_count == 1 else args.haiku_count
        args.full_model_council = False
        args.parallel_model_groups = False if args.compact_route_mode == "sequential" else args.parallel_model_groups
        args.attempt_gemini = False
        args.skip_gemini = True
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    args.run_id = f"wizard-v4-2-{args.mode}-{stamp}"
    root = Path(args.out_dir) / stamp
    root.mkdir(parents=True, exist_ok=True)
    premortem_artifact_baseline = premortem_artifacts(args.cwd)
    run_config = {
        "mode": args.mode,
        "compact_route_mode": args.compact_route_mode,
        "compact_profile": args.compact_profile,
        "resolved_compact_profile": getattr(args, "resolved_compact_profile", None),
        "required_routes": required_routes_for_run(args.mode, args.compact_route_mode, args.compact_profile, args.task),
        "run_id": args.run_id,
        "task": args.task,
        "attempt_gemini": args.attempt_gemini,
        "attempt_grok": args.attempt_grok,
    }
    (root / "run_config.json").write_text(json.dumps(run_config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(root)

    capacity_preflight = external_capacity_preflight(args, root)
    (root / "capacity_preflight.json").write_text(json.dumps(capacity_preflight, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.capacity_preflight_only:
        print("\n== capacity preflight only ==")
        print(json.dumps({"run_root": str(root), "capacity_preflight": capacity_preflight}, indent=2, sort_keys=True))
        return 0 if capacity_preflight.get("status") == "passed" else 1
    if capacity_preflight.get("status") == "blocked":
        print("\n== blocked: external model capacity preflight ==")
        print(json.dumps({"run_root": str(root), "capacity_preflight": capacity_preflight}, indent=2, sort_keys=True))
        return 1

    failures: list[str] = []
    for council, routes in selected_run_waves(args.mode, args.compact_route_mode, args.compact_profile, args.task):
        print(f"\n== {council} Council Wave ==")
        council_results = run_routes_parallel(args, routes, root)
        for route, code in council_results.items():
            if code != 0:
                failures.append(route)
        blockers = capacity_blockers(root)
        if blockers:
            print(f"\n== blocked: external model capacity after {council} wave ==")
            print(json.dumps({"run_root": str(root), "capacity_blockers": blockers[:8]}, indent=2, sort_keys=True))
            return 1
        leaked = new_premortem_artifacts(args.cwd, premortem_artifact_baseline)
        if leaked:
            print(f"\n== blocked: premortem report artifact leak after {council} wave ==")
            print(json.dumps({"run_root": str(root), "premortem_artifacts": leaked}, indent=2, sort_keys=True))
            return 1

    for loop_idx in range(1, args.max_repair_loops + 1):
        code, data = status_json(root, args.cwd, required_routes_for_run(args.mode, args.compact_route_mode, args.compact_profile, args.task))
        if code == 0 and all_members_first_pass_clean(data):
            print(f"\n== accepted after repair loops: {loop_idx - 1} ==")
            print(json.dumps({"run_root": str(root), "run_id": args.run_id}, indent=2, sort_keys=True))
            return 0
        blockers = capacity_blockers(root)
        if blockers:
            print("\n== blocked: external model capacity before repair loop ==")
            print(json.dumps({"run_root": str(root), "capacity_blockers": blockers[:8]}, indent=2, sort_keys=True))
            return 1
        leaked = new_premortem_artifacts(args.cwd, premortem_artifact_baseline)
        if leaked:
            print("\n== blocked: premortem report artifact leak before repair loop ==")
            print(json.dumps({"run_root": str(root), "premortem_artifacts": leaked}, indent=2, sort_keys=True))
            return 1
        repair = repair_children_by_route(
            data,
            repair_first_pass_unclean=args.repair_first_pass_unclean,
            max_repair_routes=args.max_repair_routes,
        )
        if not repair:
            print("\n== blocked: status invalid but no repairable missing children ==")
            print(json.dumps(data, indent=2, sort_keys=True)[:4000])
            return 1
        print(f"\n== repair loop {loop_idx}/{args.max_repair_loops} ==")
        repair_results = run_routes_parallel(args, list(repair), root, repair)
        for route, repair_code in repair_results.items():
            if repair_code != 0:
                failures.append(f"{route}:{','.join(repair[route])}")

    code, data = status_json(root, args.cwd, required_routes_for_run(args.mode, args.compact_route_mode, args.compact_profile, args.task))
    if code == 0 and all_members_first_pass_clean(data):
        print("\n== accepted after repair cap ==")
        print(json.dumps({"run_root": str(root), "run_id": args.run_id}, indent=2, sort_keys=True))
        return 0
    print("\n== final status after repair cap ==")
    print(json.dumps(data, indent=2, sort_keys=True)[:6000])
    return code or 1


if __name__ == "__main__":
    raise SystemExit(main())
