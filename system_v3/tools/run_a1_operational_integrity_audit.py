#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

from a1_selector_warning_snapshot import build_process_warning_snapshot


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_run_state(run_dir: Path) -> dict:
    state = _read_json(run_dir / "state.json")
    heavy = _read_json(run_dir / "state.heavy.json")
    if not isinstance(state, dict):
        state = {}
    if isinstance(heavy, dict):
        state.update(heavy)
    return state


def _canonical_terms(state: dict) -> set[str]:
    out: set[str] = set()
    for term, row in (state.get("term_registry", {}) or {}).items():
        if isinstance(row, dict) and str(row.get("state", "")) == "CANONICAL_ALLOWED":
            out.add(str(term))
    return out


def _strategy_objs_from_zip_packets(run_dir: Path, *, last_n: int = 12) -> list[dict]:
    zip_dir = run_dir / "zip_packets"
    paths = sorted(zip_dir.glob("*_A1_TO_A0_STRATEGY_ZIP.zip"))[-int(last_n) :]
    out: list[dict] = []
    for path in paths:
        try:
            with ZipFile(path, "r") as zf:
                with zf.open("A1_STRATEGY_v1.json") as fh:
                    obj = json.loads(fh.read().decode("utf-8"))
            if isinstance(obj, dict):
                out.append(obj)
        except Exception:
            continue
    return out


def _strategy_objs_from_outgoing_or_zip(run_dir: Path, *, last_n: int = 12) -> tuple[list[dict], str]:
    outgoing_dir = run_dir / "a1_sandbox" / "outgoing"
    paths = sorted(outgoing_dir.glob("*_A1_STRATEGY_v1__PACK_SELECTOR.json"))[-int(last_n) :]
    strategy_objs: list[dict] = []
    source_surface = "a1_sandbox_outgoing"
    for path in paths:
        obj = _read_json(path)
        if isinstance(obj, dict):
            strategy_objs.append(obj)
    if strategy_objs:
        return strategy_objs, source_surface
    strategy_objs = _strategy_objs_from_zip_packets(run_dir, last_n=last_n)
    if strategy_objs:
        return strategy_objs, "zip_packets"
    return [], "none"


def _rescue_uniqueness(outgoing_dir: Path, *, run_dir: Path, last_n: int = 12) -> dict:
    strategy_objs, source_surface = _strategy_objs_from_outgoing_or_zip(run_dir, last_n=last_n)
    if not strategy_objs:
        return {"avg_unique_rescue_from": 0.0, "sample_count": 0, "source_surface": "none"}
    uniques: list[int] = []
    for obj in strategy_objs:
        vals: list[str] = []
        for item in obj.get("alternatives", []) if isinstance(obj, dict) else []:
            if not isinstance(item, dict):
                continue
            for df in item.get("def_fields", []) or []:
                if isinstance(df, dict) and str(df.get("name", "")).strip() == "RESCUE_FROM":
                    v = str(df.get("value", "")).strip()
                    if v:
                        vals.append(v)
        uniques.append(len(set(vals)))
    avg = sum(uniques) / float(len(uniques))
    return {"avg_unique_rescue_from": avg, "sample_count": len(uniques), "source_surface": source_surface}


def _selector_support_metadata_summary(run_dir: Path, *, last_n: int = 12) -> dict:
    strategy_objs, source_surface = _strategy_objs_from_outgoing_or_zip(run_dir, last_n=last_n)
    if not strategy_objs:
        return {
            "strategy_count": 0,
            "source_surface": "none",
            "warning_count": 0,
            "warning_codes": [],
            "warning_categories": [],
            "mining_support_terms": [],
            "mining_artifact_input_count": 0,
            "max_mining_negative_pressure_count": 0,
            "support_warning_present": False,
        }

    warnings_seen: list[str] = []
    warning_codes: list[str] = []
    warning_categories: list[str] = []
    mining_terms: list[str] = []
    mining_artifact_inputs: set[str] = set()
    max_negative_pressure = 0
    max_warning_count = 0
    support_warning_present = False

    for strategy in strategy_objs:
        if not isinstance(strategy, dict):
            continue
        admissibility = strategy.get("admissibility", {}) if isinstance(strategy.get("admissibility", {}), dict) else {}
        process_audit = admissibility.get("process_audit", {}) if isinstance(admissibility.get("process_audit", {}), dict) else {}
        raw_warnings = process_audit.get("warnings", []) if isinstance(process_audit.get("warnings", []), list) else []
        for raw in raw_warnings:
            msg = str(raw).strip()
            if msg and msg not in warnings_seen:
                warnings_seen.append(msg)
        raw_warning_codes = process_audit.get("warning_codes", []) if isinstance(process_audit.get("warning_codes", []), list) else []
        for raw in raw_warning_codes:
            code = str(raw).strip()
            if code and code not in warning_codes:
                warning_codes.append(code)
        raw_warning_categories = process_audit.get("warning_categories", []) if isinstance(process_audit.get("warning_categories", []), list) else []
        for raw in raw_warning_categories:
            category = str(raw).strip()
            if category and category not in warning_categories:
                warning_categories.append(category)
        try:
            warning_count = int(process_audit.get("warning_count", 0) or 0)
        except Exception:
            warning_count = 0
        if warning_count > max_warning_count:
            max_warning_count = warning_count
        for raw in (process_audit.get("mining_support_terms", []) or []):
            term = str(raw).strip()
            if term and term not in mining_terms:
                mining_terms.append(term)
        for raw in (process_audit.get("mining_artifact_inputs", []) or []):
            value = str(raw).strip()
            if value:
                mining_artifact_inputs.add(value)
        try:
            negative_pressure = int(process_audit.get("mining_negative_pressure_count", 0) or 0)
        except Exception:
            negative_pressure = 0
        if negative_pressure > max_negative_pressure:
            max_negative_pressure = negative_pressure
        fallback_snapshot = build_process_warning_snapshot(raw_warnings)
        fallback_warning_codes = fallback_snapshot.get("warning_codes", []) if isinstance(fallback_snapshot.get("warning_codes", []), list) else []
        for raw in fallback_warning_codes:
            code = str(raw).strip()
            if code and code not in warning_codes:
                warning_codes.append(code)
        fallback_warning_categories = fallback_snapshot.get("warning_categories", []) if isinstance(fallback_snapshot.get("warning_categories", []), list) else []
        for raw in fallback_warning_categories:
            category = str(raw).strip()
            if category and category not in warning_categories:
                warning_categories.append(category)
        try:
            fallback_warning_count = int(fallback_snapshot.get("warning_count", 0) or 0)
        except Exception:
            fallback_warning_count = 0
        if fallback_warning_count > max_warning_count:
            max_warning_count = fallback_warning_count
        if (
            bool(process_audit.get("support_warning_present", False))
            or "noncanon_mining_support_only" in warning_codes
            or "support_boundary" in warning_categories
            or bool(fallback_snapshot.get("support_warning_present", False))
        ):
            support_warning_present = True

    return {
        "strategy_count": len(strategy_objs),
        "source_surface": source_surface,
        "warning_count": max(len(warnings_seen), int(max_warning_count)),
        "warning_codes": warning_codes,
        "warning_categories": warning_categories,
        "mining_support_terms": mining_terms,
        "mining_artifact_input_count": len(mining_artifact_inputs),
        "max_mining_negative_pressure_count": max_negative_pressure,
        "support_warning_present": support_warning_present,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Operational integrity audit for A1 sandbox run output.")
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--min-canonical-terms", type=int, default=35)
    ap.add_argument("--min-graveyard-count", type=int, default=45)
    ap.add_argument("--min-kill-token-diversity", type=int, default=5)
    ap.add_argument("--min-avg-unique-rescue-from", type=float, default=3.0)
    ap.add_argument(
        "--phase",
        choices=["mixed", "graveyard_fill", "recovery"],
        default="mixed",
        help="Audit phase; graveyard_fill skips rescue-uniqueness threshold by design.",
    )
    args = ap.parse_args(argv)

    run_dir = Path(args.run_dir).expanduser().resolve()
    state = _read_run_state(run_dir)
    canonical = _canonical_terms(state)
    graveyard_count = len(state.get("graveyard", {}) or {})

    kill_tokens = Counter(
        str(row.get("token", "")).strip()
        for row in (state.get("kill_log", []) or [])
        if isinstance(row, dict) and str(row.get("tag", "")).strip() == "KILL_SIGNAL"
    )
    kill_diversity = len([k for k in kill_tokens.keys() if k])

    zeros = "0" * 64
    zero_hash_rows = 0
    for row in (state.get("sim_results", {}) or {}).values():
        if not isinstance(row, dict):
            continue
        for key in ("code_hash_sha256", "input_hash_sha256", "output_hash_sha256", "run_manifest_sha256"):
            if str(row.get(key, "")).strip() == zeros:
                zero_hash_rows += 1
                break

    tier_counts = Counter()
    for row in (state.get("sim_registry", {}) or {}).values():
        if not isinstance(row, dict):
            continue
        tier_counts[str(row.get("tier", "UNKNOWN")).strip()] += 1
    required_tiers = {"T0_ATOM", "T1_COMPOUND", "T2_OPERATOR", "T3_STRUCTURE", "T6_WHOLE_SYSTEM"}
    missing_tiers = sorted(t for t in required_tiers if tier_counts.get(t, 0) <= 0)

    rescue = _rescue_uniqueness(run_dir / "a1_sandbox" / "outgoing", run_dir=run_dir)
    selector_support = _selector_support_metadata_summary(run_dir)

    failures: list[str] = []
    if str(args.phase) != "graveyard_fill" and len(canonical) < int(args.min_canonical_terms):
        failures.append("canonical_terms_below_threshold")
    if graveyard_count < int(args.min_graveyard_count):
        failures.append("graveyard_count_below_threshold")
    if kill_diversity < int(args.min_kill_token_diversity):
        failures.append("kill_token_diversity_below_threshold")
    if str(args.phase) != "graveyard_fill" and float(rescue.get("avg_unique_rescue_from", 0.0)) < float(
        args.min_avg_unique_rescue_from
    ):
        failures.append("rescue_uniqueness_below_threshold")
    if zero_hash_rows > 0:
        failures.append("zero_hash_sim_results_present")
    if missing_tiers:
        failures.append("missing_sim_tier_coverage")

    master_status = ""
    sim_results = state.get("sim_results", {}) if isinstance(state.get("sim_results", {}), dict) else {}
    if isinstance(sim_results.get("SIM_MASTER_QIT_FULL"), dict):
        master_status = str(sim_results.get("SIM_MASTER_QIT_FULL", {}).get("status", "")).strip()
    if not master_status:
        sim_promotion = state.get("sim_promotion_status", {}) if isinstance(state.get("sim_promotion_status", {}), dict) else {}
        master_status = str(sim_promotion.get("SIM_MASTER_T6", "")).strip() or str(sim_promotion.get("SIM_MASTER_QIT_FULL", "")).strip()

    report = {
        "schema": "A1_OPERATIONAL_INTEGRITY_AUDIT_REPORT_v1",
        "run_dir": str(run_dir),
        "phase": str(args.phase),
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "metrics": {
            "canonical_term_count": len(canonical),
            "graveyard_count": graveyard_count,
            "kill_token_diversity": kill_diversity,
            "kill_tokens": dict(kill_tokens),
            "avg_unique_rescue_from_last_window": rescue.get("avg_unique_rescue_from", 0.0),
            "rescue_window_sample_count": rescue.get("sample_count", 0),
            "rescue_window_source_surface": rescue.get("source_surface", "none"),
            "selector_support_strategy_count": selector_support.get("strategy_count", 0),
            "selector_support_source_surface": selector_support.get("source_surface", "none"),
            "selector_warning_count": selector_support.get("warning_count", 0),
            "selector_warning_codes": selector_support.get("warning_codes", []),
            "selector_warning_categories": selector_support.get("warning_categories", []),
            "selector_mining_support_terms": selector_support.get("mining_support_terms", []),
            "selector_mining_artifact_input_count": selector_support.get("mining_artifact_input_count", 0),
            "selector_max_mining_negative_pressure_count": selector_support.get("max_mining_negative_pressure_count", 0),
            "selector_support_warning_present": bool(selector_support.get("support_warning_present", False)),
            "zero_hash_sim_result_rows": zero_hash_rows,
            "sim_tier_counts": dict(tier_counts),
            "missing_required_tiers": missing_tiers,
            "master_sim_status": master_status,
        },
        "thresholds": {
            "min_canonical_terms": int(args.min_canonical_terms),
            "min_graveyard_count": int(args.min_graveyard_count),
            "min_kill_token_diversity": int(args.min_kill_token_diversity),
            "min_avg_unique_rescue_from": float(args.min_avg_unique_rescue_from),
        },
    }
    out = run_dir / "reports" / "a1_operational_integrity_audit_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"schema": report["schema"], "status": report["status"], "report_path": str(out)}, sort_keys=True))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
