#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
RUNS = SYSTEM_V3 / "runs"
BOOTPACK = SYSTEM_V3 / "runtime" / "bootpack_b_kernel_v1"
RUNNER = BOOTPACK / "a1_a0_b_sim_runner.py"
PROMPT_TOOL = SYSTEM_V3 / "tools" / "a1_request_to_codex_prompt.py"
PACKET_TOOL = SYSTEM_V3 / "tools" / "codex_json_to_a1_strategy_packet_zip.py"


def _read_state(run_dir: Path) -> dict:
    path = run_dir / "state.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _state_metrics(state: dict) -> dict:
    return {
        "survivor_count": len(state.get("survivor_ledger", {}) or {}),
        "park_count": len(state.get("park_set", {}) or {}),
        "graveyard_count": len(state.get("graveyard", {}) or {}),
        "kill_log_count": len(state.get("kill_log", []) or []),
        "term_registry_count": len(state.get("term_registry", {}) or {}),
        "canonical_term_count": sum(
            1
            for row in (state.get("term_registry", {}) or {}).values()
            if isinstance(row, dict) and str(row.get("state", "")) == "CANONICAL_ALLOWED"
        ),
        "sim_registry_count": len(state.get("sim_registry", {}) or {}),
        "sim_results_count": len(state.get("sim_results", {}) or {}),
    }


def _run_cmd(cmd: list[str], *, cwd: Path) -> str:
    return subprocess.check_output(cmd, cwd=str(cwd), text=True).strip()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "One Codex-as-A1 packet cycle helper: "
            "emit deterministic prompt from latest A0_SAVE_SUMMARY, "
            "ingest a schema-valid strategy JSON as A1 packet, then run one packet step."
        )
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--strategy-json", default="", help="Path to A1_STRATEGY_v1 JSON. If omitted, only prompt is emitted.")
    ap.add_argument("--fuel-max-bytes", type=int, default=60_000)
    ap.add_argument("--prompt-out", default="", help="Optional path to write A1 prompt text.")
    ap.add_argument("--init-if-missing", action="store_true", help="Initialize run by executing one packet step if run dir missing.")
    ap.add_argument("--clean-init", action="store_true", help="With --init-if-missing, initialize as clean run.")
    args = ap.parse_args(argv)

    run_id = str(args.run_id).strip()
    if not run_id:
        raise SystemExit("missing run-id")

    run_dir = RUNS / run_id
    if not run_dir.exists():
        if not args.init_if_missing:
            raise SystemExit(f"missing run dir: {run_dir}")
        init_cmd = ["python3", str(RUNNER), "--a1-source", "packet", "--run-id", run_id, "--steps", "1"]
        if bool(args.clean_init):
            init_cmd.append("--clean")
        _run_cmd(init_cmd, cwd=BOOTPACK)

    prompt = _run_cmd(
        [
            "python3",
            str(PROMPT_TOOL),
            "--run-id",
            run_id,
            "--fuel-max-bytes",
            str(int(args.fuel_max_bytes)),
        ],
        cwd=REPO,
    )
    prompt_out = Path(args.prompt_out).expanduser().resolve() if str(args.prompt_out).strip() else (run_dir / "a1_prompt_for_codex.txt")
    prompt_out.parent.mkdir(parents=True, exist_ok=True)
    prompt_out.write_text(prompt + "\n", encoding="utf-8")

    result: dict = {
        "schema": "CODEX_A1_PACKET_CYCLE_RESULT_v1",
        "run_id": run_id,
        "prompt_path": str(prompt_out),
        "status": "PROMPT_EMITTED",
    }

    strategy_json = str(args.strategy_json).strip()
    if not strategy_json:
        print(json.dumps(result, sort_keys=True))
        return 0

    strategy_path = Path(strategy_json).expanduser().resolve()
    packet_result_raw = _run_cmd(
        [
            "python3",
            str(PACKET_TOOL),
            "--run-id",
            run_id,
            "--strategy-json",
            str(strategy_path),
        ],
        cwd=REPO,
    )
    packet_result = json.loads(packet_result_raw)

    runner_result = _run_cmd(
        ["python3", str(RUNNER), "--a1-source", "packet", "--run-id", run_id, "--steps", "1"],
        cwd=BOOTPACK,
    )

    state = _read_state(run_dir)
    result.update(
        {
            "status": "STEP_EXECUTED",
            "strategy_json_path": str(strategy_path),
            "packet_result": packet_result,
            "runner_stdout_last_line": runner_result.splitlines()[-1] if runner_result else "",
            "state_metrics": _state_metrics(state),
        }
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))

