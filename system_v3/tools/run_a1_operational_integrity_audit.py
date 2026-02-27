#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_terms(state: dict) -> set[str]:
    out: set[str] = set()
    for term, row in (state.get("term_registry", {}) or {}).items():
        if isinstance(row, dict) and str(row.get("state", "")) == "CANONICAL_ALLOWED":
            out.add(str(term))
    return out


def _rescue_uniqueness(outgoing_dir: Path, *, last_n: int = 12) -> dict:
    paths = sorted(outgoing_dir.glob("*_A1_STRATEGY_v1__PACK_SELECTOR.json"))[-int(last_n) :]
    if not paths:
        return {"avg_unique_rescue_from": 0.0, "sample_count": 0}
    uniques: list[int] = []
    for p in paths:
        obj = _read_json(p)
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
    return {"avg_unique_rescue_from": avg, "sample_count": len(uniques)}


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
    state = _read_json(run_dir / "state.json")
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

    rescue = _rescue_uniqueness(run_dir / "a1_sandbox" / "outgoing")

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
