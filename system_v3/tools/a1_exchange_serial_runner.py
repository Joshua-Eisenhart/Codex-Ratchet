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
REPORT_NAME = "a1_external_memo_batch_driver_report.json"
SERIAL_REPORT_NAME = "a1_exchange_serial_runner_report.json"

# Import helper from driver for memo construction.
sys.path.insert(0, str((SYSTEM_V3 / "tools").resolve()))
from a1_external_memo_batch_driver import _build_memo  # type: ignore
from a1_selector_warning_snapshot import (
    extract_selector_provenance_fields,
    extract_selector_warning_fields,
    selector_stop_summary,
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _augment_terms_for_local_stub(terms: list[str]) -> list[str]:
    out = [str(t).strip() for t in terms if str(t).strip()]
    extras: list[str] = []
    if "density_matrix" in out:
        extras.extend(["positive_semidefinite", "trace_one"])
    for term in extras:
        if term not in out:
            out.append(term)
    return out


def _replay_stall_detail(last_row: dict) -> str:
    failure_sequence = int(last_row.get("first_failure_sequence", 0) or 0)
    surface = str(last_row.get("first_failure_surface", "") or "").strip()
    summary = str(last_row.get("first_failure_summary", "") or "").strip()
    if not summary and str(last_row.get("run_stop_reason", "") or "").strip() == "STOPPED__PACK_SELECTOR_FAILED":
        summary = _selector_stop_summary(last_row)
    prefix = f"seq {failure_sequence} " if failure_sequence > 0 else ""
    if surface and summary:
        return f"{prefix}{surface}: {summary}".strip()
    if surface:
        return f"{prefix}{surface}".strip()
    if summary:
        return f"{prefix}{summary}".strip()
    return ""


def _selector_stop_summary(row: dict) -> str:
    return selector_stop_summary(row)


def _next_unanswered_request(run_dir: Path) -> Path | None:
    req_dir = run_dir / "a1_sandbox" / "external_memo_exchange" / "requests"
    if not req_dir.exists():
        return None
    request_candidates = sorted(req_dir.glob("*__A1_EXTERNAL_MEMO_REQUEST__*.json"))
    if not request_candidates:
        return None

    seq_to_latest_request: dict[int, Path] = {}
    responded_sequences: set[int] = set()
    for path in request_candidates:
        try:
            seq = int(path.name.split("__", 1)[0])
        except ValueError:
            continue
        seq_to_latest_request[seq] = path
    for path in req_dir.glob("*__A1_EXTERNAL_MEMO_RESPONSE__*.json"):
        try:
            responded_sequences.add(int(path.name.split("__", 1)[0]))
        except ValueError:
            continue

    for seq in sorted(seq_to_latest_request):
        if seq not in responded_sequences:
            return seq_to_latest_request[seq]
    return None


def _write_response(*, request_path: Path) -> Path:
    req = _read_json(request_path)
    run_id = str(req.get("run_id", ""))
    sequence = int(req.get("sequence", 0) or 0)
    required_roles = [str(x).strip().upper() for x in (req.get("required_roles") or []) if str(x).strip()]
    term_candidates = [str(x).strip() for x in (req.get("term_candidates") or []) if str(x).strip()]
    support_term_candidates = [str(x).strip() for x in (req.get("support_term_candidates") or []) if str(x).strip()]
    rescue_targets = [str(x).strip() for x in (req.get("graveyard_rescue_targets") or []) if str(x).strip()]
    priority_negative_classes = [
        str(x).strip().upper() for x in (req.get("priority_negative_classes") or []) if str(x).strip()
    ]
    priority_claims = [str(x).strip() for x in (req.get("priority_claims") or []) if str(x).strip()]
    term_specificity_mode = str(req.get("focus_term_mode", "broad")).strip().lower()

    # Keep deterministic and bounded.
    proposed_terms = _augment_terms_for_local_stub(term_candidates[:24])
    rescue_targets = rescue_targets[:12]

    memos = []
    for role in required_roles:
        memos.append(
            _build_memo(
                run_id=run_id,
                sequence=sequence,
                role=role,
                proposed_terms=proposed_terms,
                support_terms=support_term_candidates,
                rescue_targets=rescue_targets,
                extra_negative_classes=priority_negative_classes,
                extra_claims=priority_claims,
                term_specificity_mode=term_specificity_mode,
            )
        )

    response = {
        "schema": "A1_EXTERNAL_MEMO_RESPONSE_v1",
        "run_id": run_id,
        "sequence": sequence,
        "memos": memos,
        "ts_utc": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
    }

    response_path = request_path.with_name(request_path.name.replace("REQUEST", "RESPONSE"))
    response_path.parent.mkdir(parents=True, exist_ok=True)
    response_path.write_text(json.dumps(response, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return response_path


def _run_driver(args: list[str]) -> Path:
    cmd = ["python3", str(DRIVER)] + args
    proc = subprocess.run(cmd, cwd=str(REPO), check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"driver failed: {proc.stderr.strip() or proc.stdout.strip()}")
    payload_raw = (proc.stdout or "").strip()
    if payload_raw:
        try:
            payload = json.loads(payload_raw)
        except Exception:
            payload = {}
        report_out = str(payload.get("out", "")).strip()
        if report_out:
            report_path = Path(report_out)
            if report_path.exists():
                return report_path
    return Path("")


def _load_latest_report(run_dir: Path, report_path: Path | None = None) -> dict:
    report = report_path if report_path is not None and str(report_path).strip() else run_dir / "reports" / REPORT_NAME
    if not report.exists():
        raise FileNotFoundError(str(report))
    return _read_json(report)


def _write_serial_report(run_dir: Path, payload: dict) -> Path:
    report = run_dir / "reports" / SERIAL_REPORT_NAME
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return report


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
    ap.add_argument("--seed-target-terms", default="")
    ap.add_argument("--priority-terms", default="")
    ap.add_argument("--path-build-allowed-terms", default="")
    ap.add_argument("--rescue-allowed-terms", default="")
    ap.add_argument("--seed-allowed-terms", default="")
    ap.add_argument("--probe-companion-terms", default="")
    ap.add_argument("--priority-negative-classes", default="")
    ap.add_argument("--priority-claims", default="")
    ap.add_argument("--track", default="ENGINE_ENTROPY_EXPLORATION")
    ap.add_argument("--debate-strategy", choices=["fixed", "graveyard_then_recovery"], default="graveyard_then_recovery")
    ap.add_argument("--debate-mode", choices=["balanced", "graveyard_first", "graveyard_recovery"], default="graveyard_first")
    ap.add_argument(
        "--focus-term-mode",
        choices=[
            "broad",
            "concept_plus_rescue",
            "concept_priority_rescue",
            "phase_seed_broad_then_priority",
            "concept_only",
            "concept_local_rescue",
        ],
        default="broad",
    )
    ap.add_argument("--fill-until-fuel-coverage", action="store_true")
    ap.add_argument("--fill-fuel-coverage-target", type=float, default=1.0)
    ap.add_argument("--fill-min-graveyard-term-count", type=int, default=16)
    ap.add_argument("--fill-until-library-coverage", action="store_true")
    ap.add_argument("--fill-library-coverage-target", type=float, default=1.0)
    ap.add_argument("--fill-until-graveyard-dominates", action="store_true")
    ap.add_argument("--fill-graveyard-minus-canonical-min", type=int, default=0)
    ap.add_argument("--graveyard-fill-cycles", type=int, default=8)
    ap.add_argument("--graveyard-fill-max-stall-cycles", type=int, default=1)
    ap.add_argument("--path-build-min-cycles", type=int, default=8)
    ap.add_argument("--path-build-max-cycles", type=int, default=40)
    ap.add_argument("--path-build-novelty-stall-max", type=int, default=8)
    ap.add_argument("--rescue-novelty-stall-max", type=int, default=6)
    ap.add_argument("--rescue-start-min-canonical", type=int, default=25)
    ap.add_argument("--rescue-start-min-graveyard", type=int, default=80)
    ap.add_argument("--rescue-start-min-kill-diversity", type=int, default=5)
    ap.add_argument("--seed-max-terms-per-cycle", type=int, default=24)
    ap.add_argument("--path-max-terms-per-cycle", type=int, default=18)
    ap.add_argument("--rescue-max-terms-per-cycle", type=int, default=16)
    ap.add_argument("--campaign-graveyard-fill-policy", choices=["anchor_replay", "fuel_full_load"], default="fuel_full_load")
    ap.add_argument("--campaign-forbid-rescue-during-graveyard-fill", action="store_true")
    ap.add_argument("--campaign-recovery-min-rescue-from-fields", type=int, default=1)
    ap.add_argument("--graveyard-library-terms", default="")
    ap.add_argument("--goal-min-graveyard-count", type=int, default=45)
    ap.add_argument("--goal-min-sim-registry-count", type=int, default=450)
    ap.add_argument("--min-executed-cycles-before-goal", type=int, default=16)
    ap.add_argument("--memo-prefill-depth", type=int, default=2)
    ap.add_argument("--target-executed-per-call", type=int, default=1)
    ap.add_argument("--max-wait-cycles", type=int, default=1)
    ap.add_argument("--seed-force-transition-min-executed", type=int, default=-1)
    ap.add_argument("--seed-force-transition-min-graveyard", type=int, default=0)
    ap.add_argument("--seed-force-transition-min-kill-diversity", type=int, default=0)
    ap.add_argument("--strict-local-gate-check", action="store_true")
    args = ap.parse_args(argv)

    run_id = str(args.run_id).strip()
    run_dir = Path(args.runs_root).expanduser().resolve() / run_id

    executed = 0
    waits = 0
    clean_flag = bool(args.clean)
    replay_retry_used = False
    timeline_rows: list[dict] = []
    last_status = ""
    last_stop_reason = ""
    last_sequence = 0
    last_first_failure_sequence = 0
    last_first_failure_surface = ""
    last_first_failure_summary = ""
    last_selector_cold_core_sequence = 0
    last_cold_core_sequence_mismatch_stage = ""
    last_selector_warning_count = 0
    last_selector_warning_codes: list[str] = []
    last_selector_warning_categories: list[str] = []
    last_selector_support_warning_present = False
    last_selector_warning_examples: list[str] = []

    try:
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
                "--seed-target-terms",
                str(args.seed_target_terms),
                "--priority-terms",
                str(args.priority_terms),
                "--path-build-allowed-terms",
                str(args.path_build_allowed_terms),
                "--rescue-allowed-terms",
                str(args.rescue_allowed_terms),
                "--seed-allowed-terms",
                str(args.seed_allowed_terms),
                "--probe-companion-terms",
                str(args.probe_companion_terms),
                "--priority-negative-classes",
                str(args.priority_negative_classes),
                "--priority-claims",
                str(args.priority_claims),
                "--track",
                str(args.track),
                "--debate-strategy",
                str(args.debate_strategy),
                "--debate-mode",
                str(args.debate_mode),
                "--focus-term-mode",
                str(args.focus_term_mode),
                "--memo-provider-mode",
                "exchange",
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
            if bool(args.fill_until_library_coverage):
                driver_args.append("--fill-until-library-coverage")
                driver_args.extend(["--fill-library-coverage-target", str(float(args.fill_library_coverage_target))])
            if bool(args.fill_until_graveyard_dominates):
                driver_args.append("--fill-until-graveyard-dominates")
            driver_args.extend(["--fill-graveyard-minus-canonical-min", str(int(args.fill_graveyard_minus_canonical_min))])
            driver_args.extend(["--graveyard-fill-cycles", str(int(args.graveyard_fill_cycles))])
            driver_args.extend(["--graveyard-fill-max-stall-cycles", str(int(args.graveyard_fill_max_stall_cycles))])
            driver_args.extend(["--seed-force-transition-min-executed", str(int(args.seed_force_transition_min_executed))])
            driver_args.extend(["--seed-force-transition-min-graveyard", str(int(args.seed_force_transition_min_graveyard))])
            driver_args.extend(["--seed-force-transition-min-kill-diversity", str(int(args.seed_force_transition_min_kill_diversity))])
            driver_args.extend(["--path-build-min-cycles", str(int(args.path_build_min_cycles))])
            driver_args.extend(["--path-build-max-cycles", str(int(args.path_build_max_cycles))])
            driver_args.extend(["--path-build-novelty-stall-max", str(int(args.path_build_novelty_stall_max))])
            driver_args.extend(["--rescue-novelty-stall-max", str(int(args.rescue_novelty_stall_max))])
            driver_args.extend(["--rescue-start-min-canonical", str(int(args.rescue_start_min_canonical))])
            driver_args.extend(["--rescue-start-min-graveyard", str(int(args.rescue_start_min_graveyard))])
            driver_args.extend(["--rescue-start-min-kill-diversity", str(int(args.rescue_start_min_kill_diversity))])
            driver_args.extend(["--seed-max-terms-per-cycle", str(int(args.seed_max_terms_per_cycle))])
            driver_args.extend(["--path-max-terms-per-cycle", str(int(args.path_max_terms_per_cycle))])
            driver_args.extend(["--rescue-max-terms-per-cycle", str(int(args.rescue_max_terms_per_cycle))])
            driver_args.extend(["--campaign-graveyard-fill-policy", str(args.campaign_graveyard_fill_policy)])
            if bool(args.campaign_forbid_rescue_during_graveyard_fill):
                driver_args.append("--campaign-forbid-rescue-during-graveyard-fill")
            driver_args.extend(
                ["--campaign-recovery-min-rescue-from-fields", str(int(args.campaign_recovery_min_rescue_from_fields))]
            )
            if str(args.graveyard_library_terms).strip():
                driver_args.extend(["--graveyard-library-terms", str(args.graveyard_library_terms).strip()])
            driver_args.extend(["--goal-min-graveyard-count", str(int(args.goal_min_graveyard_count))])
            driver_args.extend(["--goal-min-sim-registry-count", str(int(args.goal_min_sim_registry_count))])
            driver_args.extend(["--min-executed-cycles-before-goal", str(int(args.min_executed_cycles_before_goal))])
            if clean_flag:
                driver_args.append("--clean")
                clean_flag = False
            if bool(args.strict_local_gate_check):
                driver_args.append("--strict-local-gate-check")

            report_path = _run_driver(driver_args)
            report = _load_latest_report(run_dir, report_path if report_path else None)
            timeline = report.get("timeline", []) or []
            last = timeline[-1] if timeline else {}
            status = str(last.get("status", ""))
            executed_this_call = int(report.get("executed_cycles", 0) or 0)
            last_status = status
            last_stop_reason = str(last.get("run_stop_reason", "") or "")
            last_sequence = int(last.get("sequence", 0) or 0)
            last_first_failure_sequence = int(last.get("first_failure_sequence", 0) or 0)
            last_first_failure_surface = str(last.get("first_failure_surface", "") or "")
            last_first_failure_summary = str(last.get("first_failure_summary", "") or "")
            if not last_first_failure_summary and last_stop_reason == "STOPPED__PACK_SELECTOR_FAILED":
                last_first_failure_summary = _selector_stop_summary(last if isinstance(last, dict) else {})
            selector_provenance_fields = extract_selector_provenance_fields(last if isinstance(last, dict) else {})
            last_selector_cold_core_sequence = int(selector_provenance_fields.get("selector_cold_core_sequence", 0) or 0)
            last_cold_core_sequence_mismatch_stage = str(selector_provenance_fields.get("cold_core_sequence_mismatch_stage", "") or "")
            selector_warning_fields = extract_selector_warning_fields(last if isinstance(last, dict) else {})
            last_selector_warning_count = int(selector_warning_fields.get("selector_warning_count", 0) or 0)
            last_selector_warning_codes = list(selector_warning_fields.get("selector_warning_codes", []) or [])
            last_selector_warning_categories = list(selector_warning_fields.get("selector_warning_categories", []) or [])
            last_selector_support_warning_present = bool(selector_warning_fields.get("selector_support_warning_present", False))
            last_selector_warning_examples = list(selector_warning_fields.get("selector_warning_examples", []) or [])
            timeline_row = {
                "status": last_status,
                "sequence": last_sequence,
                "process_phase": str(last.get("process_phase", "") or ""),
                "run_stop_reason": last_stop_reason,
                "first_failure_sequence": last_first_failure_sequence,
                "first_failure_surface": last_first_failure_surface,
                "first_failure_summary": last_first_failure_summary,
                "executed_this_call": executed_this_call,
            }
            if last_selector_cold_core_sequence > 0:
                timeline_row["selector_cold_core_sequence"] = last_selector_cold_core_sequence
            if last_cold_core_sequence_mismatch_stage:
                timeline_row["cold_core_sequence_mismatch_stage"] = last_cold_core_sequence_mismatch_stage
            if last_selector_warning_count > 0:
                timeline_row["selector_warning_count"] = int(last_selector_warning_count)
                timeline_row["selector_support_warning_present"] = bool(last_selector_support_warning_present)
            if last_selector_warning_codes:
                timeline_row["selector_warning_codes"] = list(last_selector_warning_codes)
            if last_selector_warning_categories:
                timeline_row["selector_warning_categories"] = list(last_selector_warning_categories)
            if last_selector_warning_examples:
                timeline_row["selector_warning_examples"] = list(last_selector_warning_examples)
            timeline_rows.append(timeline_row)

            if executed_this_call > 0:
                replay_retry_used = False
                executed += executed_this_call
                continue
            if status == "WAITING_FOR_MEMOS":
                waits += 1
                latest_req = _next_unanswered_request(run_dir)
                if not latest_req:
                    if last_stop_reason == "STOPPED__RESCUE_NOVELTY_STALL":
                        break
                    ingest_rows = last.get("exchange_ingest_rows", []) if isinstance(last, dict) else []
                    prepack_rows = last.get("exchange_prepack_rows", []) if isinstance(last, dict) else []
                    if ingest_rows or prepack_rows:
                        if not replay_retry_used:
                            replay_retry_used = True
                            continue
                        detail = _replay_stall_detail(last if isinstance(last, dict) else {})
                        if detail:
                            raise RuntimeError(f"Exchange replay stalled after consuming existing responses ({detail}).")
                        raise RuntimeError("Exchange replay stalled after consuming existing responses.")
                    raise RuntimeError("No exchange request found to answer.")
                replay_retry_used = False
                _write_response(request_path=latest_req)
                continue
            break
    finally:
        request_dir = run_dir / "a1_sandbox" / "external_memo_exchange" / "requests"
        latest_request_by_seq: dict[int, Path] = {}
        responded_sequences: list[int] = []
        if request_dir.exists():
            for path in sorted(request_dir.glob("*__A1_EXTERNAL_MEMO_RESPONSE__*.json")):
                try:
                    responded_sequences.append(int(path.name.split("__", 1)[0]))
                except ValueError:
                    continue
            for path in sorted(request_dir.glob("*__A1_EXTERNAL_MEMO_REQUEST__*.json")):
                try:
                    seq = int(path.name.split("__", 1)[0])
                except ValueError:
                    continue
                latest_request_by_seq[seq] = path
        unanswered_sequences = [seq for seq in sorted(latest_request_by_seq) if seq not in set(responded_sequences)]
        report_payload = {
            "schema": "A1_EXCHANGE_SERIAL_RUNNER_REPORT_v1",
            "run_id": run_id,
            "requested_steps": int(args.steps),
            "executed_cycles_total": int(executed),
            "wait_cycles_total": int(waits),
            "last_status": last_status,
            "last_stop_reason": last_stop_reason,
            "last_sequence": int(last_sequence),
            "last_first_failure_sequence": int(last_first_failure_sequence),
            "last_first_failure_surface": last_first_failure_surface,
            "last_first_failure_summary": last_first_failure_summary,
            "timeline": timeline_rows,
            "responded_sequences": responded_sequences,
            "unanswered_sequences": unanswered_sequences,
        }
        if last_selector_cold_core_sequence > 0:
            report_payload["last_selector_cold_core_sequence"] = int(last_selector_cold_core_sequence)
        if last_cold_core_sequence_mismatch_stage:
            report_payload["last_cold_core_sequence_mismatch_stage"] = last_cold_core_sequence_mismatch_stage
        if last_selector_warning_count > 0:
            report_payload["last_selector_warning_count"] = int(last_selector_warning_count)
            report_payload["last_selector_support_warning_present"] = bool(last_selector_support_warning_present)
        if last_selector_warning_codes:
            report_payload["last_selector_warning_codes"] = list(last_selector_warning_codes)
        if last_selector_warning_categories:
            report_payload["last_selector_warning_categories"] = list(last_selector_warning_categories)
        if last_selector_warning_examples:
            report_payload["last_selector_warning_examples"] = list(last_selector_warning_examples)
        _write_serial_report(run_dir, report_payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
