#!/usr/bin/env python3
"""Wizard v4.2 level/loop wrapper.

This is the human-facing entrypoint for commands such as:

    wizard low loop 2
    wizard auto loop auto

It delegates all receipt-producing work to the existing v4.2 matrix runner and
compiler. The wrapper owns level selection, loop bounds, and feeding the next
compiled prompt into the next pass.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LEVELS = ("low", "medium", "high", "auto")
AUTO_LOOP_MAX = 6
STOP_HEADERS = ("BLOCKED",)
HEADER_RE = re.compile(
    r"^🧙 Wizard v4\.2 \| (?P<status>FULL|PARTIAL|BLOCKED) \| "
    r"waves:(?P<waves_done>\d+)/(?P<waves_total>\d+) \| "
    r"parents:(?P<parents_done>\d+)/(?P<parents_total>\d+) \| "
    r"children:(?P<children_done>\d+)/(?P<children_total>\d+) \| "
    r"tools:(?P<tools>\d+) \| score:(?P<score>\d+) \| runtimes:(?P<runtimes>[^|]+)"
    r"(?: \| (?P<suffix>.*))?$"
)


@dataclass(frozen=True)
class LevelPreset:
    level: str
    mode: str
    compact_route_mode: str
    passes_per_iteration: int
    max_repair_loops: int
    max_repair_routes: int
    sonnet_count: int
    opus_count: int
    haiku_count: int
    parallel_model_groups: bool
    full_model_council: bool
    skip_gemini: bool
    attempt_gemini: bool
    attempt_grok: bool
    capacity_preflight_models: str


PRESETS: dict[str, LevelPreset] = {
    "low": LevelPreset(
        level="low",
        mode="compact",
        compact_route_mode="sequential",
        passes_per_iteration=1,
        max_repair_loops=0,
        max_repair_routes=1,
        sonnet_count=7,
        opus_count=1,
        haiku_count=0,
        parallel_model_groups=False,
        full_model_council=False,
        skip_gemini=True,
        attempt_gemini=False,
        attempt_grok=False,
        capacity_preflight_models="sonnet",
    ),
    "medium": LevelPreset(
        level="medium",
        mode="compact",
        compact_route_mode="sequential",
        passes_per_iteration=2,
        max_repair_loops=1,
        max_repair_routes=2,
        sonnet_count=7,
        opus_count=1,
        haiku_count=0,
        parallel_model_groups=False,
        full_model_council=False,
        skip_gemini=True,
        attempt_gemini=False,
        attempt_grok=False,
        capacity_preflight_models="sonnet",
    ),
    "high": LevelPreset(
        level="high",
        mode="full",
        compact_route_mode="sequential",
        passes_per_iteration=3,
        max_repair_loops=3,
        max_repair_routes=3,
        sonnet_count=0,
        opus_count=0,
        haiku_count=1,
        parallel_model_groups=True,
        full_model_council=True,
        skip_gemini=False,
        attempt_gemini=True,
        attempt_grok=False,
        capacity_preflight_models="sonnet,opus,haiku",
    ),
}


def normalize_invocation(tokens: list[str]) -> tuple[str | None, str | None, list[str]]:
    """Extract friendly positional level/loop words before argparse runs."""
    level: str | None = None
    loop: str | None = None
    rest: list[str] = []
    idx = 0
    option_value_flags = {
        "--task",
        "--cwd",
        "--out-dir",
        "--level",
        "--loop",
        "--compact-profile",
    }
    while idx < len(tokens):
        token = tokens[idx]
        if token in option_value_flags:
            rest.append(token)
            if idx + 1 < len(tokens):
                rest.append(tokens[idx + 1])
                idx += 2
            else:
                idx += 1
            continue
        lowered = token.lower()
        if lowered in LEVELS and level is None:
            level = lowered
            idx += 1
            continue
        if lowered == "loop":
            if idx + 1 < len(tokens) and not tokens[idx + 1].startswith("-"):
                loop = tokens[idx + 1].lower()
                idx += 2
            else:
                loop = "auto"
                idx += 1
            continue
        rest.append(token)
        idx += 1
    return level, loop, rest


def select_auto_level(task: str) -> str:
    lowered = task.lower()
    high_terms = (
        "full",
        "promote",
        "promotion",
        "commit",
        "canonical",
        "evidence snapshot",
        "sim",
        "runner",
        "proof",
        "qit",
        "engine",
        "bridge",
        "axis",
        "stage",
    )
    medium_terms = (
        "audit",
        "verify",
        "route truth",
        "overclaim",
        "repair",
        "bug",
        "regression",
        "premortem",
        "loophole",
        "loop",
    )
    if any(term in lowered for term in high_terms):
        return "high"
    if any(term in lowered for term in medium_terms):
        return "medium"
    return "low"


def loop_limit(value: str | None) -> tuple[int, bool]:
    if value is None:
        return 1, False
    if value.lower() == "auto":
        return AUTO_LOOP_MAX, True
    try:
        count = int(value)
    except ValueError as exc:
        raise SystemExit(f"Invalid loop count: {value!r}. Use an integer or 'auto'.") from exc
    if count < 1:
        raise SystemExit("Loop count must be at least 1.")
    return count, False


def build_runner_command(
    *,
    preset: LevelPreset,
    task: str,
    out_dir: Path,
    cwd: Path,
    dry_run: bool = False,
    codex_local_children: bool = False,
    attempt_gemini: bool = False,
    attempt_grok: bool = False,
    no_capacity_preflight: bool = False,
    compact_profile: str = "auto",
) -> list[str]:
    script = Path(__file__).with_name("wizard_full_matrix_run_v4_2.py")
    command = [
        sys.executable,
        str(script),
        "--task",
        task,
        "--cwd",
        str(cwd),
        "--out-dir",
        str(out_dir),
        "--mode",
        preset.mode,
        "--compact-route-mode",
        preset.compact_route_mode,
        "--compact-profile",
        compact_profile,
        "--max-repair-loops",
        str(preset.max_repair_loops),
        "--max-repair-routes",
        str(preset.max_repair_routes),
        "--sonnet-count",
        str(preset.sonnet_count),
        "--opus-count",
        str(preset.opus_count),
        "--haiku-count",
        str(preset.haiku_count),
        "--global-max-active",
        "6" if preset.level != "high" else "8",
        "--max-concurrency",
        "4",
        "--capacity-preflight-models",
        preset.capacity_preflight_models,
        "--capacity-preflight-timeout-sec",
        "45",
        "--capacity-preflight-budget",
        "0.5",
    ]
    command.append("--parallel-model-groups" if preset.parallel_model_groups else "--no-parallel-model-groups")
    command.append("--full-model-council" if preset.full_model_council else "--no-full-model-council")
    should_attempt_gemini = attempt_gemini or preset.attempt_gemini
    if preset.skip_gemini and not should_attempt_gemini:
        command.append("--skip-gemini")
    if should_attempt_gemini:
        command.append("--attempt-gemini")
    if attempt_grok or preset.attempt_grok:
        command.append("--attempt-grok")
    if dry_run:
        command.append("--dry-run")
    if codex_local_children:
        command.append("--codex-local-children")
    if no_capacity_preflight:
        command.append("--no-capacity-preflight")
    return command


def newest_run_root(out_dir: Path) -> Path | None:
    if not out_dir.exists():
        return None
    candidates = [path for path in out_dir.iterdir() if path.is_dir()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def compile_run(run_root: Path, task: str, cwd: Path, compiled_path: Path) -> tuple[int, str]:
    script = Path(__file__).with_name("wizard_compile_output_v4_2.py")
    command = [
        sys.executable,
        str(script),
        str(run_root),
        "--task",
        task,
        "--out",
        str(compiled_path),
        "--cwd",
        str(cwd),
        "--mode",
        "auto",
    ]
    proc = subprocess.run(command, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return proc.returncode, proc.stdout


def compiled_header(compiled_path: Path) -> str:
    if not compiled_path.exists():
        return ""
    for line in compiled_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            return line.strip()
    return ""


def next_task_from_compiled(compiled_path: Path, fallback: str) -> str:
    if not compiled_path.exists():
        return fallback
    text = compiled_path.read_text(encoding="utf-8", errors="replace")
    followup = text.split("## 🧭 Follow-Up Options", 1)[-1] if "## 🧭 Follow-Up Options" in text else text
    match = re.search(r"`([^`]{24,1200})`", followup)
    if match:
        candidate = " ".join(match.group(1).split())
        if is_output_format_drift(candidate):
            return fallback
        if not preserves_task_domain(candidate, fallback):
            return fallback
        return candidate
    action = text.split("### 🔨 Action", 1)[-1].split("###", 1)[0] if "### 🔨 Action" in text else ""
    action = " ".join(action.split())
    if action and not is_output_format_drift(action) and preserves_task_domain(action, fallback):
        return action
    return fallback


def is_output_format_drift(task: str) -> bool:
    lowered = " ".join(task.lower().split())
    drift_markers = (
        "make the compiled wizard answer shorter",
        "useful output without log collapse",
        "require the same readable output shape",
        "run wizard low with claude children",
        "run full wizard v4.2 only after compact output",
        "tests all nine parents plus management",
        "stdout becomes json or a run log",
    )
    return any(marker in lowered for marker in drift_markers)


GENERIC_TASK_DOMAIN_TOKENS = {"wizard", "audit"}


def preserves_task_domain(candidate: str, fallback: str) -> bool:
    fallback_tokens = task_domain_tokens(fallback)
    if not fallback_tokens:
        return True
    candidate_tokens = task_domain_tokens(candidate)
    if not (candidate_tokens & fallback_tokens):
        return False
    specific_fallback_tokens = fallback_tokens - GENERIC_TASK_DOMAIN_TOKENS
    if specific_fallback_tokens:
        return bool((candidate_tokens - GENERIC_TASK_DOMAIN_TOKENS) & specific_fallback_tokens)
    return True


def task_domain_tokens(task: str) -> set[str]:
    lowered = " ".join(task.lower().split())
    token_groups = {
        "wiki_alignment": (
            "wiki",
            "llm alignment",
            "alignment tool",
            "frame-loader",
            "front door",
            "research spine",
            "index/routing",
            "notebooklm",
            "arxiv",
            "source coverage",
            "current research",
            "hermes-current",
        ),
        "szilard": ("szilard",),
        "carnot": ("carnot",),
        "rosetta": ("rosetta", "lego", "legos"),
        "engine_lab": ("engine-lab", "engine lab", "open-row", "open row"),
        "qit": ("qit",),
        "sim": ("sim", "sims", "simulation", "evidence", "receipt", "receipts"),
        "visualizer": ("visualizer", "payload"),
        "matrix": ("matrix", "inventory", "queue", "successor"),
        "admission": ("admission", "admitted", "result linkage", "duplicate"),
        "wizard": ("wizard", "route-truth", "route truth", "receipt-truth", "receipt truth"),
        "audit": ("audit", "regression", "blocker", "overclaim"),
    }
    return {label for label, markers in token_groups.items() if any(marker in lowered for marker in markers)}


def should_stop_auto_loop(*, header: str, next_task: str, seen_tasks: set[str]) -> str | None:
    if any(marker in header for marker in STOP_HEADERS):
        return "blocked_header"
    if not next_task.strip():
        return "empty_next_task"
    normalized = " ".join(next_task.lower().split())
    if normalized in seen_tasks:
        return "repeated_next_task"
    return None


def write_manifest(session_root: Path, manifest: dict[str, Any]) -> None:
    (session_root / "wizard_loop_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def emit_pass_record(pass_record: dict[str, Any]) -> None:
    print(json.dumps(pass_record, indent=2, sort_keys=True), file=sys.stderr)


def aggregate_loop_header(manifest: dict[str, Any], output_text: str) -> str:
    lines = output_text.splitlines()
    if not lines:
        return output_text
    first = lines[0]
    match = HEADER_RE.match(first)
    if not match:
        return output_text
    iterations = [item for item in manifest.get("iterations", []) if item.get("header")]
    if not iterations:
        return output_text

    totals = {
        "waves_done": 0,
        "waves_total": 0,
        "parents_done": 0,
        "parents_total": 0,
        "children_done": 0,
        "children_total": 0,
        "tools": 0,
    }
    statuses: list[str] = []
    runtimes: list[str] = []
    suffix = match.group("suffix") or ""
    for item in iterations:
        header_match = HEADER_RE.match(str(item.get("header") or ""))
        if not header_match:
            continue
        statuses.append(header_match.group("status"))
        for key in ("waves_done", "waves_total", "parents_done", "parents_total", "children_done", "children_total", "tools"):
            totals[key] += int(header_match.group(key))
        for runtime in header_match.group("runtimes").split(","):
            runtime = runtime.strip()
            if runtime and runtime not in runtimes:
                runtimes.append(runtime)
        suffix = header_match.group("suffix") or suffix
    if not statuses:
        return output_text
    status = "BLOCKED" if "BLOCKED" in statuses else "PARTIAL" if "PARTIAL" in statuses else "FULL"
    completed_loops = len(iterations)
    requested_loops = manifest.get("loop_count_limit") or completed_loops
    lines[0] = (
        f"🧙 Wizard v4.2 | {status} | loops:{completed_loops}/{requested_loops} | "
        f"waves:{totals['waves_done']}/{totals['waves_total']} | "
        f"parents:{totals['parents_done']}/{totals['parents_total']} | "
        f"children:{totals['children_done']}/{totals['children_total']} | "
        f"tools:{totals['tools']} | score:{match.group('score')} | "
        f"runtimes:{', '.join(runtimes)}"
        + (f" | {suffix}" if suffix else "")
    )
    return "\n".join(lines) + ("\n" if output_text.endswith("\n") else "")


def finish_loop(
    *,
    session_root: Path,
    manifest: dict[str, Any],
    stop_reason: str,
    final_task: str,
    exit_code: int,
    emit_output: bool = True,
) -> int:
    manifest["stop_reason"] = stop_reason
    manifest["final_task"] = final_task
    manifest["session_root"] = str(session_root)
    write_manifest(session_root, manifest)
    output_path = session_root / "latest_wizard_output.md"
    if emit_output and output_path.exists():
        output_text = aggregate_loop_header(manifest, output_path.read_text(encoding="utf-8"))
        output_path.write_text(output_text, encoding="utf-8")
        print(output_text, end="")
    else:
        print(session_root, file=sys.stderr)
    return exit_code


def run_level_loop(args: argparse.Namespace, preset: LevelPreset, loop_count: int, loop_auto: bool) -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    session_root = Path(args.out_dir) / f"wizard-{preset.level}-{stamp}"
    session_root.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "schema": "wizard_v4_2_level_loop",
        "requested_level": args.requested_level,
        "resolved_level": preset.level,
        "loop_requested": args.loop_value,
        "loop_count_limit": loop_count,
        "loop_auto": loop_auto,
        "preset": asdict(preset),
        "initial_task": args.task,
        "iterations": [],
    }
    current_task = args.task
    seen_tasks = {" ".join(current_task.lower().split())}
    exit_code = 0
    stop_reason = "loop_limit_reached"

    for iteration in range(1, loop_count + 1):
        for pass_index in range(1, preset.passes_per_iteration + 1):
            pass_dir = session_root / f"iteration_{iteration:02d}_pass_{pass_index:02d}"
            pass_dir.mkdir(parents=True, exist_ok=True)
            command = build_runner_command(
                preset=preset,
                task=current_task,
                out_dir=pass_dir,
                cwd=Path(args.cwd),
                dry_run=args.dry_run,
                codex_local_children=args.codex_local_children,
                attempt_gemini=args.attempt_gemini,
                attempt_grok=getattr(args, "attempt_grok", False),
                no_capacity_preflight=args.no_capacity_preflight,
                compact_profile=getattr(args, "compact_profile", "auto"),
            )
            runner_log = pass_dir / "runner_stdout.log"
            with runner_log.open("w", encoding="utf-8") as handle:
                proc = subprocess.run(command, cwd=str(args.cwd), text=True, stdout=handle, stderr=subprocess.STDOUT, check=False)
            run_root = newest_run_root(pass_dir)
            compiled_path = pass_dir / "compiled.md"
            compile_code = 1
            compile_stdout = "no_run_root"
            header = ""
            next_task = current_task
            if run_root is not None:
                compile_code, compile_stdout = compile_run(run_root, current_task, Path(args.cwd), compiled_path)
                header = compiled_header(compiled_path)
                next_task = next_task_from_compiled(compiled_path, current_task)
                if compiled_path.exists():
                    shutil.copyfile(compiled_path, session_root / "latest_wizard_output.md")
            pass_record = {
                "iteration": iteration,
                "pass": pass_index,
                "task": current_task,
                "runner_returncode": proc.returncode,
                "compile_returncode": compile_code,
                "run_root": str(run_root) if run_root else None,
                "compiled": str(compiled_path) if compiled_path.exists() else None,
                "wizard_output": str(session_root / "latest_wizard_output.md")
                if (session_root / "latest_wizard_output.md").exists()
                else None,
                "header": header,
                "next_task": next_task,
                "runner_log": str(runner_log),
                "compile_stdout": compile_stdout[:1000],
            }
            manifest["iterations"].append(pass_record)
            write_manifest(session_root, manifest)
            emit_pass_record(pass_record)
            if proc.returncode != 0 and run_root is None:
                exit_code = proc.returncode or 1
                return finish_loop(
                    session_root=session_root,
                    manifest=manifest,
                    stop_reason="runner_failed_without_run_root",
                    final_task=current_task,
                    exit_code=exit_code,
                )
            if compile_code != 0 or not header:
                exit_code = compile_code or proc.returncode or 1
                return finish_loop(
                    session_root=session_root,
                    manifest=manifest,
                    stop_reason="compile_failed",
                    final_task=current_task,
                    exit_code=exit_code,
                )
            if any(marker in header for marker in STOP_HEADERS):
                exit_code = proc.returncode or compile_code or 1
                return finish_loop(
                    session_root=session_root,
                    manifest=manifest,
                    stop_reason="blocked_header",
                    final_task=current_task,
                    exit_code=exit_code,
                )
            current_task = next_task
            normalized_next = " ".join(current_task.lower().split())
            if loop_auto:
                reason = should_stop_auto_loop(header=header, next_task=current_task, seen_tasks=seen_tasks)
                if reason:
                    return finish_loop(
                        session_root=session_root,
                        manifest=manifest,
                        stop_reason=reason,
                        final_task=current_task,
                        exit_code=exit_code,
                    )
                seen_tasks.add(normalized_next)

    return finish_loop(
        session_root=session_root,
        manifest=manifest,
        stop_reason=stop_reason,
        final_task=current_task,
        exit_code=exit_code,
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    positional_level, positional_loop, rest = normalize_invocation(argv)
    parser = argparse.ArgumentParser(description="Run Wizard v4.2 by level and optional loop count.")
    parser.add_argument("--task", required=True)
    parser.add_argument("--cwd", default=str(Path.cwd()))
    parser.add_argument("--out-dir", default="/tmp/codex_ratchet_wizard_v4_2")
    parser.add_argument("--level", choices=LEVELS)
    parser.add_argument("--loop")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--codex-local-children", action="store_true")
    parser.add_argument("--attempt-gemini", action="store_true")
    parser.add_argument("--attempt-grok", action="store_true")
    parser.add_argument("--no-capacity-preflight", action="store_true")
    parser.add_argument(
        "--compact-profile",
        choices=["auto", "default", "audit", "strategy", "followup", "formatting"],
        default="auto",
    )
    args = parser.parse_args(rest)
    requested_level = args.level or positional_level or "auto"
    resolved_level = select_auto_level(args.task) if requested_level == "auto" else requested_level
    args.requested_level = requested_level
    args.resolved_level = resolved_level
    args.loop_value = args.loop or positional_loop or "1"
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    loop_count, loop_auto = loop_limit(args.loop_value)
    preset = PRESETS[args.resolved_level]
    return run_level_loop(args, preset, loop_count, loop_auto)


if __name__ == "__main__":
    raise SystemExit(main())
