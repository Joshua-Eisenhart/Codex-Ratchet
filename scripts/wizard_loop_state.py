#!/usr/bin/env python3
"""Emit the live LOOP_STATE for the wizard loop controller — deterministic, read-only.

The mechanical half of the route-truth control function: external-controller
packets and agent receipts are receipt_candidate evidence; this script reads
the actual git/filesystem state so the controller verifies against ground
truth instead of prose. The Claude route-truth-agent remains the semantic
half (claim adjudication); this script never interprets, only observes.

Usage: wizard_loop_state.py [--repo PATH] [--commits N] [--json-indent N]
                            [--prior-state PATH] [--run-receipt PATH]
                            [--prompt-packet PATH] [--original-goal TEXT]
                            [--frontier TEXT]
Output: one JSON object on stdout, including a best-effort system_load guard
for heavy local lanes. Read-only; never writes the repo.
"""

from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


CEILING_RANK = {
    "exists": 1,
    "runs": 2,
    "passes_local": 3,
    "canonical": 4,
    "scratch_diagnostic": 3,
    "GENUINE-WITH-CAVEATS": 3,
}


def run(args, cwd):
    out = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=120)
    return out.stdout.strip()


def run_local(args):
    out = subprocess.run(args, capture_output=True, text=True, timeout=10)
    return out.stdout.strip()


def load_json(path):
    if not path:
        return None
    return json.loads(Path(path).read_text())


def load_average() -> tuple[float, float, float]:
    try:
        raw = run_local(["sysctl", "-n", "vm.loadavg"]).strip("{} ")
        parts = raw.split()
        if len(parts) >= 3:
            return float(parts[0]), float(parts[1]), float(parts[2])
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return tuple(float(v) for v in os.getloadavg())


def memory_pressure() -> dict:
    try:
        memsize = int(run_local(["sysctl", "-n", "hw.memsize"]))
        vm = run_local(["vm_stat"])
        page_size = 4096
        counts = {}
        for line in vm.splitlines():
            if "page size of" in line:
                page_size = int(line.split("page size of", 1)[1].split("bytes", 1)[0].strip())
                continue
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            counts[key.strip().lower()] = int(value.strip().rstrip(".").replace(".", ""))
        free_pages = counts.get("pages free", 0) + counts.get("pages speculative", 0)
        active_pages = counts.get("pages active", 0)
        inactive_pages = counts.get("pages inactive", 0)
        free_bytes = free_pages * page_size
        active_bytes = active_pages * page_size
        inactive_bytes = inactive_pages * page_size
        return {
            "free_gb": round(free_bytes / (1024**3), 2),
            "active_gb": round(active_bytes / (1024**3), 2),
            "inactive_gb": round(inactive_bytes / (1024**3), 2),
            "total_gb": round(memsize / (1024**3), 2),
            "free_fraction": round(free_bytes / memsize, 3) if memsize else None,
            "source": "vm_stat",
        }
    except (OSError, subprocess.SubprocessError, ValueError, IndexError) as exc:
        return {"unavailable": str(exc)}


def system_load() -> dict:
    try:
        load_1m, load_5m, load_15m = load_average()
        cpu_count = os.cpu_count()
        load_per_core = round(load_1m / cpu_count, 3) if cpu_count else None
        advice = "ok_to_launch" if load_per_core is not None and load_per_core < 0.8 else "queue_heavy_lanes"
        return {
            "load_avg_1m": round(load_1m, 3),
            "load_avg_5m": round(load_5m, 3),
            "load_avg_15m": round(load_15m, 3),
            "cpu_count": cpu_count,
            "load_per_core_1m": load_per_core,
            "memory_pressure": memory_pressure(),
            "heavy_lane_advice": advice,
        }
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        return {"unavailable": str(exc)}


def compact_state_fingerprint(state: dict) -> dict:
    return {
        "head": state.get("head"),
        "open_lanes": state.get("open_lanes", []),
        "modified_tracked_files": state.get("modified_tracked_files", []),
        "current_claim_under_test": (
            (state.get("horizon") or {}).get("current_claim_under_test")
            or state.get("current_claim_under_test")
        ),
        "blocked_on": state.get("blocked_on"),
    }


def extract_claims(receipt: dict | None) -> list:
    if not isinstance(receipt, dict):
        return []
    claims = receipt.get("claims_checked", [])
    return claims if isinstance(claims, list) else []


def requested_stop_signals(receipt: dict | None) -> list:
    if not isinstance(receipt, dict):
        return []
    signals = receipt.get("stop_signals_fired", [])
    return [s for s in signals if isinstance(s, str)]


def current_blocked_on(current: dict, receipt: dict | None) -> dict:
    blocked = current.get("blocked_on")
    if isinstance(blocked, dict) and blocked.get("item"):
        return blocked
    if isinstance(receipt, dict):
        open_items = receipt.get("open_items", [])
        if isinstance(open_items, list):
            for item in open_items:
                if isinstance(item, dict) and item.get("item"):
                    return {
                        "item": item.get("item"),
                        "why_open": item.get("why_open"),
                        "consecutive_loops_blocked": item.get("consecutive_loops_blocked"),
                    }
    return {}


def mechanically_detected_stop_signals(prior: dict, current: dict, receipt: dict | None, original_goal: str | None, frontier: str | None) -> list:
    signals = []
    if compact_state_fingerprint(prior) == compact_state_fingerprint(current):
        signals.append("no_delta")

    prior_blocked = prior.get("blocked_on") or {}
    current_blocked = current_blocked_on(current, receipt)
    if (
        isinstance(prior_blocked, dict)
        and isinstance(current_blocked, dict)
        and prior_blocked.get("item")
        and prior_blocked.get("item") == current_blocked.get("item")
    ):
        prior_count = int(prior_blocked.get("consecutive_loops_blocked") or 1)
        current_count = int(current_blocked.get("consecutive_loops_blocked") or prior_count + 1)
        if current_count >= 3 or prior_count >= 2:
            signals.append("same_blocker")

    goal = original_goal or ((prior.get("horizon") or {}).get("original_goal"))
    observed_frontier = frontier or ((current.get("horizon") or {}).get("frontier"))
    if goal and observed_frontier:
        goal_tokens = {t for t in str(goal).lower().replace("_", " ").split() if len(t) > 3}
        frontier_tokens = {t for t in str(observed_frontier).lower().replace("_", " ").split() if len(t) > 3}
        if goal_tokens and frontier_tokens and goal_tokens.isdisjoint(frontier_tokens):
            signals.append("scope_drift")

    if any(claim.get("result") in {"refuted", "not_checked"} for claim in extract_claims(receipt)):
        signals.append("verification_fail")

    for signal in requested_stop_signals(receipt):
        if signal not in signals:
            signals.append(signal)

    return signals


def claim_ceiling_accuracy(claims: list) -> float | None:
    if not claims:
        return None
    accurate = 0
    for claim in claims:
        result = claim.get("result")
        ceiling = claim.get("ceiling")
        if result == "confirmed" and CEILING_RANK.get(str(ceiling), 0) >= CEILING_RANK["exists"]:
            accurate += 1
        elif result in {"partial", "refuted", "not_checked"} and str(ceiling) in {"exists", "runs", "passes_local", "scratch_diagnostic"}:
            accurate += 1
    return round(accurate / len(claims), 3)


def loop_health(prior: dict, current: dict, receipt: dict | None, prompt_packet: str | None, original_goal: str | None, frontier: str | None) -> dict:
    prior_fp = compact_state_fingerprint(prior)
    current_fp = compact_state_fingerprint(current)
    claims = extract_claims(receipt)
    failed_claims = [c for c in claims if c.get("result") in {"refuted", "not_checked"}]
    divergent_claims = [c for c in claims if c.get("result") in {"refuted", "partial", "not_checked"}]
    prompt_text = Path(prompt_packet).read_text() if prompt_packet else ""
    stale_context_hits = prompt_text.count("stale") + prompt_text.count("prune")

    return {
        "delta_per_loop": {
            "changed": prior_fp != current_fp,
            "prior": prior_fp,
            "current": current_fp,
        },
        "false_closure_count": len(failed_claims),
        "branch_preservation_score": None,
        "claim_ceiling_accuracy": claim_ceiling_accuracy(claims),
        "verification_yield": round(len(divergent_claims) / len(claims), 3) if claims else None,
        "stale_context_hits": stale_context_hits,
        "stop_signals": mechanically_detected_stop_signals(
            prior, current, receipt, original_goal, frontier
        ),
    }


def audit_freshness(d: Path) -> dict:
    """The freshness gate: a packet is closeable only when audit_verdict.md is at
    least as new as every source/result/build-card artifact (or the audit names
    the newer set explicitly — that exception is the controller's to judge)."""
    verdict = d / "audit_verdict.md"
    if not verdict.is_file():
        return {"audit_fresh": None, "newer_than_audit": []}
    audit_mtime = verdict.stat().st_mtime
    watched = (
        list(d.glob("*.py")) + list(d.glob("*.jl")) + list(d.glob("build_card.md"))
        + (list((d / "results").glob("*.json")) if (d / "results").is_dir() else [])
    )
    newer = [p.name for p in watched if p.stat().st_mtime > audit_mtime]
    return {"audit_fresh": not newer, "newer_than_audit": sorted(newer)}


def lane_state(repo: Path, rel_dir: str) -> dict:
    d = repo / rel_dir
    results = sorted(p.name for p in (d / "results").glob("*.json")) if (d / "results").is_dir() else []
    envelope = next((r for r in results if "envelope" in r), None)
    state = {
        "path": rel_dir,
        "tracked": False,
        "source_files": sorted(p.name for p in d.glob("*.py")) + sorted(p.name for p in d.glob("*.jl")),
        "result_files": results,
        "audit_verdict_exists": (d / "audit_verdict.md").is_file(),
        "envelope": None,
        **audit_freshness(d),
    }
    if envelope:
        try:
            env = json.loads((d / "results" / envelope).read_text())
            state["envelope"] = {
                "file": envelope,
                "schema_version": env.get("schema_version"),
                "mode": (env.get("engine_contract") or {}).get("mode"),
                "all_pass": env.get("all_pass"),
                "classification": env.get("classification"),
                "promotion_allowed": env.get("promotion_allowed"),
            }
        except (json.JSONDecodeError, OSError) as exc:
            state["envelope"] = {"file": envelope, "error": str(exc)}
    # The observable lane stage, from artifacts alone (never from prose):
    if not results:
        stage = "building_or_source_only"
    elif not state["audit_verdict_exists"]:
        stage = "built_awaiting_audit"
    else:
        stage = "audited_awaiting_closeout"
    state["stage"] = stage
    return state


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--commits", type=int, default=8)
    ap.add_argument("--json-indent", type=int, default=1)
    ap.add_argument("--prior-state")
    ap.add_argument("--run-receipt")
    ap.add_argument("--prompt-packet")
    ap.add_argument("--original-goal")
    ap.add_argument("--frontier")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()

    untracked = [
        line[3:].rstrip("/")
        for line in run(["git", "status", "--short"], repo).splitlines()
        if line.startswith("?? ") and line[3:].startswith("system_v6/sims/")
    ]
    modified_tracked = [
        line[3:]
        for line in run(["git", "status", "--short"], repo).splitlines()
        if line.startswith(" M ") or line.startswith("M  ")
    ]
    commits = [
        {"hash": h, "subject": s[:140]}
        for h, _, s in (
            line.partition(" ")
            for line in run(["git", "log", f"-{args.commits}", "--oneline"], repo).splitlines()
        )
    ]

    state = {
        "schema": "wizard_loop_state_v1",
        "head": commits[0]["hash"] if commits else None,
        "recent_commits": commits,
        "open_lanes": [lane_state(repo, d) for d in untracked],
        "modified_tracked_files": modified_tracked,
        "system_load": system_load(),
        "note": "stage is derived from artifacts only (results/audit_verdict presence); "
        "background worker liveness is NOT observable here — the controller's task "
        "notifications are authoritative for in-flight builds. Receipts referencing "
        "lanes absent from open_lanes are stale.",
    }
    if args.prior_state:
        prior = load_json(args.prior_state)
        receipt = load_json(args.run_receipt)
        state["loop_health"] = loop_health(
            prior,
            state,
            receipt,
            args.prompt_packet,
            args.original_goal,
            args.frontier,
        )
    json.dump(state, sys.stdout, indent=args.json_indent)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
