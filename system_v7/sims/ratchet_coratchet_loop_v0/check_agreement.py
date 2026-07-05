#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

SIM = Path(__file__).resolve().parent
RESULTS = SIM / "results"
ENGINES = ("numpy", "jax", "julia")

def load(e): return json.loads((RESULTS / f"ratchet_coratchet_loop_v0_{e}_results.json").read_text())
def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def summarize(row):
    return {
        r["variant"]: {
            "ticks_run": r["ticks_run"],
            "locks": len(r["locks"]),
            "co_turn_events": len(r["co_turn_events"]),
            "last_new_tick": r.get("last_new_tick"),
            "final_quotient": r["final_quotient"],
        }
        for r in row["run_results"]
    }

def main():
    rows = {e: load(e) for e in ENGINES}
    summaries = {e: summarize(r) for e, r in rows.items()}
    failures = []
    if len({json.dumps(s, sort_keys=True) for s in summaries.values()}) != 1:
        failures.append("three-engine summary mismatch")
    for e, r in rows.items():
        if r.get("classification") != "scratch_diagnostic" or r.get("promotion_allowed") is not False:
            failures.append(f"{e}: classification/promotion failed")
        if r.get("capstone_status") != "DRAFT_UNAUDITED":
            failures.append(f"{e}: capstone not draft")
        if r.get("persistent_k") != 3:
            failures.append(f"{e}: persistent_k mismatch")
        if r.get("headline", {}).get("headline_pass") is not True:
            failures.append(f"{e}: headline discriminator failed")
    canonical = summaries["numpy"]
    feedback_cut_fake = canonical["feedback_cut"]["co_turn_events"] != 0
    if feedback_cut_fake:
        failures.append("feedback-cut produced headline co-turn")
    out = {"schema_version": "ratchet_coratchet_loop_v0_agreement", "engine": "agreement_envelope", "generated_at": now(), "classification": "scratch_diagnostic", "promotion_allowed": False, "formal_admission_allowed": False, "capstone_status": "DRAFT_UNAUDITED", "persistent_k": 3, "all_pass": not failures, "summary": canonical, "engine_summaries": summaries, "feedback_cut_control_passed": not feedback_cut_fake, "failures": failures, "TOOL_MANIFEST": {"python_stdlib": {"tried": True, "used": True, "reason": "supportive agreement check"}}, "TOOL_INTEGRATION_DEPTH": {"python_stdlib": "supportive"}, "divergence_log": ["agreement compares K=3 lock counts, co-turns, last-new ticks, and final quotients; per-engine result files retain lock curves"]}
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "ratchet_coratchet_loop_v0_three_engine_results.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": out["all_pass"], "feedback_cut_control_passed": out["feedback_cut_control_passed"], "summary": canonical}, sort_keys=True))
    return 0 if out["all_pass"] else 1
if __name__ == "__main__":
    raise SystemExit(main())
