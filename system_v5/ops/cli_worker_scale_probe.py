#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

TASKS: list[dict[str, str]] = [
    {
        "id": "lanes-status",
        "prompt": "Read system_v5/docs/plans/lanes.md and output TI-03 and M-05 statuses in <=12 words.",
    },
    {
        "id": "worker-model",
        "prompt": "Read system_v5/docs/plans/plans/controller-harness-integration-status.md and output the admitted worker model in <=12 words.",
    },
    {
        "id": "smoke-tests-1-3",
        "prompt": "Read system_v5/docs/plans/plans/new-process-smoke-test-plan.md and output the names of Tests 1-3 in <=12 words.",
    },
    {
        "id": "proved-claude-path",
        "prompt": "Read system_v5/docs/plans/plans/subagent-wiki-harness-integration-contract.md and output the current proved Claude path in <=12 words.",
    },
    {
        "id": "m05-state",
        "prompt": "Read system_v5/docs/plans/plans/controller-harness-integration-status.md and output M-05 state in <=12 words.",
    },
    {
        "id": "maintenance-overlay",
        "prompt": "Read system_v5/docs/plans/lanes.md and output M-01 to M-04 statuses in <=12 words.",
    },
    {
        "id": "smoke-stop-rule",
        "prompt": "Read system_v5/docs/plans/plans/new-process-smoke-test-plan.md and output the stop rule in <=12 words.",
    },
    {
        "id": "wiki-separation",
        "prompt": "Read system_v5/docs/plans/plans/wiki-automation-run-contract.md and output the core separation rule in <=12 words.",
    },
    {
        "id": "claude-receipt",
        "prompt": "Read system_v5/docs/plans/plans/claude-worker-utilization-receipt.md and output the current proved Claude scale in <=12 words.",
    },
    {
        "id": "biggest-blocker",
        "prompt": "Read system_v5/docs/plans/plans/controller-harness-integration-status.md and output the biggest blocker family in <=12 words.",
    },
]

CLAUDE_SCHEMA = json.dumps(
    {
        "type": "object",
        "properties": {"out": {"type": "string"}},
        "required": ["out"],
        "additionalProperties": False,
    },
    separators=(",", ":"),
)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run bounded parallel CLI worker scale probes.")
    ap.add_argument("--provider", choices=["claude", "gemini"], required=True)
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--model", default=None)
    ap.add_argument("--effort", default=None)
    ap.add_argument("--max-turns", type=int, default=5)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--summary-path", required=True)
    return ap.parse_args()


def build_command(provider: str, prompt: str, model: str | None, effort: str | None, max_turns: int) -> list[str]:
    if provider == "claude":
        cmd = [
            "claude",
            "-p",
            prompt,
            "--allowedTools",
            "Read",
            "--output-format",
            "json",
            "--json-schema",
            CLAUDE_SCHEMA,
            "--max-turns",
            str(max_turns),
        ]
        if model:
            cmd.extend(["--model", model])
        if effort:
            cmd.extend(["--effort", effort])
        return cmd
    cmd = [
        "gemini",
        "-p",
        prompt,
        "--approval-mode",
        "plan",
        "--output-format",
        "json",
    ]
    if model:
        cmd.extend(["-m", model])
    return cmd


def extract_json_blob(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON object found in output")
    return json.loads(text[start : end + 1])


def summarize_payload(provider: str, payload: dict[str, Any]) -> dict[str, Any]:
    if provider == "claude":
        return {
            "ok": payload.get("subtype") == "success",
            "subtype": payload.get("subtype"),
            "terminal_reason": payload.get("terminal_reason"),
            "result": payload.get("structured_output", {}).get("out") or payload.get("result"),
            "cost": payload.get("total_cost_usd"),
            "modelUsage": payload.get("modelUsage"),
            "session_id": payload.get("session_id"),
            "num_turns": payload.get("num_turns"),
            "api_error_status": payload.get("api_error_status"),
        }
    stats = payload.get("stats", {})
    return {
        "ok": True,
        "subtype": "success",
        "terminal_reason": "completed",
        "result": payload.get("response"),
        "cost": None,
        "modelUsage": stats.get("models"),
        "session_id": payload.get("session_id"),
        "num_turns": None,
        "api_error_status": None,
    }


def main() -> int:
    args = parse_args()
    if args.count < 1:
        raise SystemExit("--count must be >= 1")
    if args.count > len(TASKS):
        raise SystemExit(f"--count must be <= {len(TASKS)}")

    workdir = Path(args.workdir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    procs: list[dict[str, Any]] = []
    launched_at = time.time()
    for task in TASKS[: args.count]:
        raw_path = output_dir / f"{args.provider}_{task['id']}.json"
        cmd = build_command(args.provider, task["prompt"], args.model, args.effort, args.max_turns)
        proc = subprocess.Popen(
            cmd,
            cwd=str(workdir),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        procs.append({"task": task, "proc": proc, "raw_path": raw_path, "cmd": cmd})

    results: list[dict[str, Any]] = []
    for item in procs:
        proc: subprocess.Popen[str] = item["proc"]
        stdout, stderr = proc.communicate()
        combined = stdout if stdout.strip() else stderr
        item["raw_path"].write_text(combined, encoding="utf-8")
        record: dict[str, Any] = {
            "task_id": item["task"]["id"],
            "prompt": item["task"]["prompt"],
            "command": item["cmd"],
            "exit_code": proc.returncode,
            "raw_path": str(item["raw_path"]),
        }
        try:
            payload = extract_json_blob(combined)
            record["payload"] = summarize_payload(args.provider, payload)
        except Exception as exc:  # noqa: BLE001
            record["payload_error"] = str(exc)
            record["payload_preview"] = combined[:1200]
        results.append(record)

    success_count = sum(1 for r in results if r.get("payload", {}).get("ok") and r.get("exit_code") == 0)
    summary = {
        "provider": args.provider,
        "count": args.count,
        "model": args.model,
        "effort": args.effort,
        "max_turns": args.max_turns,
        "workdir": str(workdir),
        "launched_at": launched_at,
        "duration_seconds": round(time.time() - launched_at, 3),
        "success_count": success_count,
        "failure_count": len(results) - success_count,
        "all_success": success_count == len(results),
        "results": results,
    }
    summary_path = Path(args.summary_path).resolve()
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
