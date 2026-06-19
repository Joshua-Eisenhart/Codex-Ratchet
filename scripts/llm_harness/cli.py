"""Minimal CLI for the offline LLM harness.

Usage:
    python -m scripts.llm_harness.cli run <task.json> [--output-dir DIR]

The task.json is a TaskSpec-shaped object plus a "provider"/"model"/"output"
binding.  For the offline core the default provider is the deterministic
FakeSuccessProvider; pass "provider": "local_tool" with a "command" argv to run
a real local subprocess.

This is a thin stub: load a task, run a provider, gate, print the receipt +
gate result as JSON.  Timestamps are passed explicitly so the printed receipt
is reproducible given a fixed --started-at / --completed-at.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .gates import gate
from .providers import (
    FakeFailureProvider,
    FakeMalformedProvider,
    FakeSuccessProvider,
    FakeTimeoutProvider,
    LocalToolProvider,
)
from .runner import run_job
from .types import ModelJob, TaskSpec

_PROVIDERS = {
    "fake_success": FakeSuccessProvider,
    "fake_failure": FakeFailureProvider,
    "fake_timeout": FakeTimeoutProvider,
    "fake_malformed": FakeMalformedProvider,
    "local_tool": LocalToolProvider,
}


def _load_job(task_path: Path, output_dir: Path) -> ModelJob:
    payload = json.loads(task_path.read_text(encoding="utf-8"))
    task = TaskSpec(
        task_id=payload["task_id"],
        role=payload.get("role", "builder"),
        prompt=payload.get("prompt", ""),
        classification=payload.get("classification", "scratch_diagnostic"),
        claim_ceiling=payload.get("claim_ceiling", ""),
        gate_ceiling_rung=payload.get("gate_ceiling_rung", "scratch_diagnostic"),
        input_refs=list(payload.get("input_refs", [])),
        audit_required=bool(payload.get("audit_required", False)),
    )
    provider_name = payload.get("provider", "fake_success")
    output_path = payload.get("output") or str(output_dir / f"{task.task_id}.out")
    return ModelJob(
        task=task,
        provider=provider_name,
        model=payload.get("model", "offline-fake"),
        output_path=output_path,
        command=payload.get("command"),
        cwd=payload.get("cwd"),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scripts.llm_harness.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run_p = sub.add_parser("run", help="run a task.json through a provider + gate")
    run_p.add_argument("task", type=Path)
    run_p.add_argument("--output-dir", type=Path, default=Path.cwd() / "llm_harness_out")
    run_p.add_argument("--started-at", default="1970-01-01T00:00:00+00:00")
    run_p.add_argument("--completed-at", default="1970-01-01T00:00:01+00:00")
    run_p.add_argument("--timeout", type=float, default=60.0)

    args = parser.parse_args(argv)
    if args.cmd == "run":
        args.output_dir.mkdir(parents=True, exist_ok=True)
        job = _load_job(args.task, args.output_dir)
        provider_cls = _PROVIDERS.get(job.provider)
        if provider_cls is None:
            print(f"unknown provider: {job.provider}", file=sys.stderr)
            return 2
        provider = provider_cls()
        receipt_path = args.output_dir / f"{job.task.task_id}.receipt.json"
        receipt = run_job(
            job,
            provider,
            timeout=args.timeout,
            started_at=args.started_at,
            completed_at=args.completed_at,
            receipt_path=receipt_path,
        )
        result = gate(receipt)
        print(json.dumps({"receipt": receipt.to_dict(), "gate": result.to_dict()}, indent=2))
        return 0 if result.admitted else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
