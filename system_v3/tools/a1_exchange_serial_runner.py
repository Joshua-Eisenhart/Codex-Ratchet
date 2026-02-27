#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
RUNS_DEFAULT = SYSTEM_V3 / "runs"
A2_STATE_DEFAULT = SYSTEM_V3 / "a2_state"
DRIVER = SYSTEM_V3 / "tools" / "a1_external_memo_batch_driver.py"
EXCHANGE_BRIDGE = SYSTEM_V3 / "tools" / "a1_external_memo_provider_exchange_bridge.py"
REPORT_NAME = "a1_external_memo_batch_driver_report.json"
EXCHANGE_ROOT = REPO / "work" / "a1_sandbox" / "codex_exchange" / "provider_bridge"

# Import helper from driver for memo construction.
sys.path.insert(0, str((SYSTEM_V3 / "tools").resolve()))
from a1_external_memo_batch_driver import _build_memo  # type: ignore


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_request(exchange_root: Path) -> Path | None:
    req_dir = exchange_root / "requests"
    if not req_dir.exists():
        return None
    candidates = sorted(req_dir.glob("*__A1_EXTERNAL_MEMO_REQUEST__*.json"))
    return candidates[-1] if candidates else None


def _write_response(*, request_path: Path, exchange_root: Path) -> Path:
    req = _read_json(request_path)
    run_id = str(req.get("run_id", ""))
    sequence = int(req.get("sequence", 0) or 0)
    required_roles = [str(x).strip().upper() for x in (req.get("required_roles") or []) if str(x).strip()]
    term_candidates = [str(x).strip() for x in (req.get("term_candidates") or []) if str(x).strip()]
    rescue_targets = [str(x).strip() for x in (req.get("graveyard_rescue_targets") or []) if str(x).strip()]

    # Keep deterministic and bounded.
    proposed_terms = term_candidates[:24]
    rescue_targets = rescue_targets[:12]

    memos = []
    for role in required_roles:
        memos.append(
            _build_memo(
                run_id=run_id,
                sequence=sequence,
                role=role,
                proposed_terms=proposed_terms,
                rescue_targets=rescue_targets,
            )
        )

    response = {
        "schema": "A1_EXTERNAL_MEMO_RESPONSE_v1",
        "run_id": run_id,
        "sequence": sequence,
        "memos": memos,
        "ts_utc": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
    }

    resp_dir = exchange_root / "responses"
    resp_dir.mkdir(parents=True, exist_ok=True)
    response_name = request_path.name.replace("REQUEST", "RESPONSE")
    response_path = resp_dir / response_name
    response_path.write_text(json.dumps(response, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return response_path


def _run_driver(args: list[str]) -> Path:
    cmd = ["python3", str(DRIVER)] + args
    proc = subprocess.run(cmd, cwd=str(REPO), check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"driver failed: {proc.stderr.strip() or proc.stdout.strip()}")
    # Report lives under run_dir/reports
    # We read the latest report path from stdout if present, otherwise fall back.
    return Path("")


def _load_latest_report(run_dir: Path) -> dict:
    report = run_dir / "reports" / REPORT_NAME
    if not report.exists():
        raise FileNotFoundError(str(report))
    return _read_json(report)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Serial exchange runner for A1 external memo provider (Codex-local).")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--runs-root", default=str(RUNS_DEFAULT))
    ap.add_argument("--a2-state-dir", default=str(A2_STATE_DEFAULT))
    ap.add_argument("--preset", default="graveyard13")
    ap.add_argument("--process-mode", default="concept_path_rescue")
    ap.add_argument("--concept-target-terms", default="density_matrix,probe_operator")
    ap.add_argument("--fill-until-fuel-coverage", action="store_true")
    ap.add_argument("--fill-fuel-coverage-target", type=float, default=1.0)
    ap.add_argument("--fill-min-graveyard-term-count", type=int, default=16)
    ap.add_argument("--memo-prefill-depth", type=int, default=2)
    ap.add_argument("--target-executed-per-call", type=int, default=1)
    ap.add_argument("--max-wait-cycles", type=int, default=1)
    ap.add_argument("--strict-local-gate-check", action="store_true")
    args = ap.parse_args(argv)

    run_id = str(args.run_id).strip()
    run_dir = Path(args.runs_root).expanduser().resolve() / run_id

    executed = 0
    clean_flag = bool(args.clean)

    while executed < int(args.steps):
        driver_args = [
            "--run-id",
            run_id,
            "--runs-root",
            str(Path(args.runs_root).expanduser().resolve()),
            "--a2-state-dir",
            str(Path(args.a2_state_dir).expanduser().resolve()),
            "--preset",
            str(args.preset),
            "--process-mode",
            str(args.process_mode),
            "--concept-target-terms",
            str(args.concept_target_terms),
            "--memo-provider-mode",
            "exchange",
            "--provider-script",
            str(EXCHANGE_BRIDGE),
            "--memo-prefill-depth",
            str(int(args.memo_prefill_depth)),
            "--target-executed-cycles",
            str(int(args.target_executed_per_call)),
            "--max-wait-cycles",
            str(int(args.max_wait_cycles)),
        ]
        if bool(args.fill_until_fuel_coverage):
            driver_args.append("--fill-until-fuel-coverage")
            driver_args.extend(["--fill-fuel-coverage-target", str(float(args.fill_fuel_coverage_target))])
            driver_args.extend(["--fill-min-graveyard-term-count", str(int(args.fill_min_graveyard_term_count))])
        if clean_flag:
            driver_args.append("--clean")
            clean_flag = False
        if bool(args.strict_local_gate_check):
            driver_args.append("--strict-local-gate-check")

        _run_driver(driver_args)
        report = _load_latest_report(run_dir)
        timeline = report.get("timeline", []) or []
        last = timeline[-1] if timeline else {}
        status = str(last.get("status", ""))

        if status == "WAITING_FOR_MEMOS":
            latest_req = _latest_request(EXCHANGE_ROOT)
            if not latest_req:
                raise RuntimeError("No exchange request found to answer.")
            _write_response(request_path=latest_req, exchange_root=EXCHANGE_ROOT)
            # Next loop should consume response and execute.
            continue
        if status == "STEP_EXECUTED":
            executed += 1
            continue
        # Any other status ends loop.
        break

    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
