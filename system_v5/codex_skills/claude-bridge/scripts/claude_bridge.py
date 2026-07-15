#!/usr/bin/env python3
"""Bounded Claude Code bridge with dry inspection and non-gating receipts.

This is a trimmed repo-held port of the installed Claude bridge wrapper.  It
does not implement provider logic: it only constructs and optionally executes
the documented ``claude -p`` CLI command.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


SCHEMA_ID = "codex-ratchet.claude-bridge-receipt.v1"
PROVIDER = "claude-code-cli"
LAUNCH_CWD = "/tmp"

MODEL_ALIASES = {
    "sonnet": "sonnet",
    "haiku": "haiku",
    "opus": "opus",
    "fable": "fable",
    "fable5": "fable",
    "fable-5": "fable",
    "default": "default",
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_model(value: str) -> str:
    requested = value.strip()
    if not requested:
        raise ValueError("model must be non-empty")
    return MODEL_ALIASES.get(requested.lower(), requested)


def route_metadata(value: str) -> dict[str, str]:
    requested = value.strip()
    routed = resolve_model(requested)
    lowered = requested.lower()
    if lowered == "default":
        kind = "configured_default"
    elif lowered in MODEL_ALIASES:
        kind = "moving_alias"
    else:
        kind = "explicit_passthrough"
    return {
        "requested_model": requested,
        "routed_model": routed,
        "resolution_kind": kind,
    }


def normalize_budget(value: float) -> float:
    budget = float(value)
    if not math.isfinite(budget) or budget <= 0:
        raise ValueError("budget must be a finite number greater than zero")
    return budget


def budget_summary(requested: float, observed: Any) -> dict[str, Any]:
    requested_budget = normalize_budget(requested)
    if observed is None:
        observed_budget = None
        exceeded = None
    else:
        observed_budget = float(observed)
        if not math.isfinite(observed_budget) or observed_budget < 0:
            raise ValueError("observed cost must be a finite non-negative number")
        exceeded = observed_budget > requested_budget
    return {
        "requested_usd": requested_budget,
        "observed_usd": observed_budget,
        "exceeded": exceeded,
        "provider_stop_is_preflight_guarantee": False,
    }


def slugify(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", text.strip().lower()).strip("-")
    return text[:48] or "claude-bridge"


def build_command(
    *,
    requested_model: str,
    budget: float,
    stream: bool,
    tools: str,
    requested_cwd: str,
    effort: str = "",
    fallback_model: str = "",
) -> list[str]:
    route = route_metadata(requested_model)
    requested_budget = normalize_budget(budget)
    command = [
        "claude",
        "-p",
        "--model",
        route["routed_model"],
        "--output-format",
        "stream-json" if stream else "json",
        "--no-session-persistence",
        "--max-budget-usd",
        str(requested_budget),
    ]
    normalized_cwd = str(Path(requested_cwd).expanduser())
    if normalized_cwd and normalized_cwd != LAUNCH_CWD:
        command.extend(["--add-dir", normalized_cwd])
    if stream:
        command.append("--verbose")
    if effort:
        command.extend(["--effort", effort])
    if fallback_model:
        command.extend(["--fallback-model", resolve_model(fallback_model)])
    if tools:
        command.extend(["--allowedTools", tools])
    else:
        command.extend(["--tools", ""])
    return command


def _model_usage(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def summarize_json_text(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {
            "parse_ok": False,
            "parse_error": str(exc),
            "raw_preview": raw[:1000],
            "models": [],
            "model_usage": {},
            "total_cost_usd": None,
        }
    if not isinstance(data, dict):
        return {
            "parse_ok": False,
            "parse_error": "top-level JSON output is not an object",
            "raw_preview": raw[:1000],
            "models": [],
            "model_usage": {},
            "total_cost_usd": None,
        }
    usage = _model_usage(data.get("modelUsage"))
    return {
        "parse_ok": True,
        "result_subtype": data.get("subtype"),
        "is_error": data.get("is_error"),
        "total_cost_usd": data.get("total_cost_usd"),
        "duration_ms": data.get("duration_ms"),
        "models": sorted(usage),
        "model_usage": usage,
        "result_preview": str(data.get("result", ""))[:1000],
    }


def summarize_stream_text(raw: str) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "parse_ok": False,
        "json_lines": 0,
        "agent_tool_calls": 0,
        "task_started": 0,
        "task_completed": 0,
        "rate_limit_events": 0,
        "models": [],
        "model_usage": {},
        "result_subtype": None,
        "is_error": None,
        "total_cost_usd": None,
    }
    usage: dict[str, Any] = {}
    saw_result = False
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        summary["json_lines"] += 1
        if event.get("type") == "rate_limit_event":
            summary["rate_limit_events"] += 1
        if event.get("type") == "system" and event.get("subtype") == "task_started":
            summary["task_started"] += 1
        if (
            event.get("type") == "system"
            and event.get("subtype") == "task_notification"
            and event.get("status") == "completed"
        ):
            summary["task_completed"] += 1
        message = event.get("message") or {}
        if isinstance(message, dict):
            for content in message.get("content") or []:
                if (
                    isinstance(content, dict)
                    and content.get("type") == "tool_use"
                    and content.get("name") in {"Agent", "Task"}
                ):
                    summary["agent_tool_calls"] += 1
        if event.get("type") == "result":
            saw_result = True
            summary["result_subtype"] = event.get("subtype")
            summary["is_error"] = event.get("is_error")
            summary["total_cost_usd"] = event.get("total_cost_usd")
            usage.update(_model_usage(event.get("modelUsage")))
    summary["parse_ok"] = saw_result
    if summary["json_lines"] and not saw_result:
        summary["parse_error"] = "stream contained JSON events but no result event"
    elif not summary["json_lines"]:
        summary["parse_error"] = "stream contained no JSON object events"
    summary["models"] = sorted(usage)
    summary["model_usage"] = usage
    return summary


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect or run Claude Code from Codex with non-gating receipts."
    )
    parser.add_argument(
        "--model",
        default="default",
        help="configured default; moving alias; fable5/fable-5; or explicit full model identifier",
    )
    parser.add_argument("--prompt", help="Prompt text")
    parser.add_argument("--prompt-file", help="Read prompt from file")
    parser.add_argument("--budget", type=float, default=2.0, help="Provider-side max budget in USD")
    parser.add_argument("--effort", default="", help="Optional Claude effort")
    parser.add_argument("--fallback-model", default="", help="Optional fallback alias or full identifier")
    parser.add_argument("--timeout-sec", type=float, default=0.0, help="Wall-clock timeout; 0 disables")
    parser.add_argument("--stream", action="store_true", help="Use stream-json --verbose output")
    parser.add_argument("--tools", default="", help="Comma-separated Claude tools to allow explicitly")
    parser.add_argument("--cwd", default=os.getcwd(), help="Directory exposed to Claude with --add-dir")
    parser.add_argument("--out-dir", default="/tmp/codex_claude_bridge", help="Artifact directory")
    parser.add_argument("--name", default="", help="Optional run name")
    parser.add_argument("--dry-run", action="store_true", help="Write a command-plan receipt without invoking Claude")
    parser.add_argument("--inspect-route", action="store_true", help="Print model routing only; no prompt, files, or provider")
    return parser.parse_args(argv)


def load_prompt(args: argparse.Namespace) -> str:
    if args.prompt and args.prompt_file:
        raise ValueError("use --prompt or --prompt-file, not both")
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    elif args.prompt:
        prompt = args.prompt
    elif not sys.stdin.isatty():
        prompt = sys.stdin.read()
    else:
        raise ValueError("provide --prompt, --prompt-file, or stdin")
    prompt = prompt.strip()
    if not prompt:
        raise ValueError("prompt is empty")
    return prompt


def _artifact_paths(args: argparse.Namespace, prompt: str) -> tuple[Path, Path, Path]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = sha256_text(prompt)[:12]
    run_name = slugify(args.name or prompt[:80])
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = out_dir / f"{timestamp}-{run_name}-{digest}"
    prompt_path = stem.with_suffix(".prompt.txt")
    output_path = stem.with_suffix(".stream.jsonl" if args.stream else ".json")
    receipt_path = stem.with_suffix(".receipt.json")
    return prompt_path, output_path, receipt_path


def run_bridge(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    prompt = load_prompt(args)
    route = route_metadata(args.model)
    budget = normalize_budget(args.budget)
    if args.timeout_sec < 0 or not math.isfinite(args.timeout_sec):
        raise ValueError("timeout must be finite and non-negative")
    command = build_command(
        requested_model=args.model,
        budget=budget,
        stream=args.stream,
        tools=args.tools,
        requested_cwd=args.cwd,
        effort=args.effort,
        fallback_model=args.fallback_model,
    )
    prompt_path, output_path, receipt_path = _artifact_paths(args, prompt)
    prompt_path.write_text(prompt + "\n", encoding="utf-8")

    timed_out = False
    if args.dry_run:
        provider_invoked = False
        provider_returncode = None
        parsed: dict[str, Any] = {
            "parse_ok": True,
            "dry_run": True,
            "models": [],
            "model_usage": {},
            "total_cost_usd": None,
        }
        output_payload = {
            "kind": "claude_bridge_dry_run",
            "provider_invoked": False,
            "route": route,
            "command": command,
        }
        output_text = json.dumps(output_payload, indent=2, sort_keys=True) + "\n"
    else:
        provider_invoked = True
        timeout = args.timeout_sec if args.timeout_sec > 0 else None
        try:
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                cwd=LAUNCH_CWD,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=timeout,
            )
            output_text = completed.stdout
            provider_returncode = completed.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            output_text = exc.stdout or ""
            if isinstance(output_text, bytes):
                output_text = output_text.decode("utf-8", errors="replace")
            output_text += f"\n[TIMEOUT after {args.timeout_sec}s]\n"
            provider_returncode = 124
        parsed = (
            summarize_stream_text(output_text)
            if args.stream
            else summarize_json_text(output_text)
        )

    output_path.write_text(output_text, encoding="utf-8", errors="replace")
    observed_cost = parsed.get("total_cost_usd")
    try:
        budget_data = budget_summary(budget, observed_cost)
    except (TypeError, ValueError):
        budget_data = budget_summary(budget, None)
        parsed["cost_parse_error"] = repr(observed_cost)

    if args.dry_run:
        wrapper_returncode = 0
    elif provider_returncode != 0:
        wrapper_returncode = int(provider_returncode)
    elif not parsed.get("parse_ok"):
        wrapper_returncode = 3
    else:
        wrapper_returncode = 0

    receipt: dict[str, Any] = {
        "schema": SCHEMA_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "execution_mode": "dry_run" if args.dry_run else "live",
        "provider": PROVIDER,
        "provider_invoked": provider_invoked,
        "advisory_only": True,
        "gate_authority": False,
        "evidence_allowed": False,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "release_eligible": False,
        "official_launch_allowed": False,
        "scientific_claim_proven": False,
        "gate_decision": "not_applicable",
        "route": route,
        "fallback_route": route_metadata(args.fallback_model) if args.fallback_model else None,
        "backend_models": parsed.get("models", []),
        "backend_model_truth_source": "output.modelUsage",
        "budget": budget_data,
        "command": command,
        "cwd": LAUNCH_CWD,
        "requested_cwd": str(Path(args.cwd).expanduser()),
        "tools": args.tools,
        "effort": args.effort,
        "prompt_path": str(prompt_path),
        "prompt_sha256": sha256_file(prompt_path),
        "output_path": str(output_path),
        "output_sha256": sha256_file(output_path),
        "receipt_path": str(receipt_path),
        "stream": args.stream,
        "timed_out": timed_out,
        "timeout_sec": args.timeout_sec,
        "provider_returncode": provider_returncode,
        "wrapper_returncode": wrapper_returncode,
        "parsed": parsed,
    }
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return receipt, wrapper_returncode


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.inspect_route:
            route = route_metadata(args.model)
            if args.fallback_model:
                route["fallback_routed_model"] = resolve_model(args.fallback_model)
            print(json.dumps(route, indent=2, sort_keys=True))
            return 0
        receipt, returncode = run_bridge(args)
    except (OSError, ValueError) as exc:
        print(f"claude_bridge: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
