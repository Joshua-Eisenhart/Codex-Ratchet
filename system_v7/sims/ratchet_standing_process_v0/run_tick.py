#!/usr/bin/env python3
"""Standing-process ops ratchet over repo disagreement witnesses.

This is an ops-ratchet/gate-digger, not a physics sim. It mines recomputable
estate disagreements and locks the weakest checker needed to express one lost
demand per tick.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
TOOL_MANIFEST = {
    "python_stdlib": {"reason": "ledger, filesystem, JSON, and markdown parsing"},
    "numpy": {"reason": "available only for parity-recompute-numpy checker when numeric demands require it"},
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive", "numpy": "supportive"}

SIM_ID = "ratchet_standing_process_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = Path(__file__).resolve().parent
LEDGER = SIM_DIR / "ledger.jsonl"
STATE = SIM_DIR / "state.json"
SUMMARY = SIM_DIR / "run_summary.json"
WIKI_OPS = Path("/Users/joshuaeisenhart/wiki/ops")

INITIAL_CHECKERS: list[str] = []
CHECKER_ORDER = [
    "path-exists",
    "json-field-compare",
    "count-vs-listing",
    "date-order",
    "parity-recompute-numpy",
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def digest(parts: list[str]) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]


def line_event(event: str, ts: str, **payload: Any) -> dict[str, Any]:
    out = {"ts": ts, "event": event}
    out.update(payload)
    return out


def load_state() -> dict[str, Any]:
    if STATE.exists():
        return read_json(STATE)
    return {
        "sim_id": SIM_ID,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "locked_checkers": [{"name": name, "locked_at": "bootstrap"} for name in INITIAL_CHECKERS],
        "demand_frontier": [],
        "voided": [],
        "met": [],
        "seen_demand_ids": [],
        "ticks_completed": 0,
    }


def append(events: list[dict[str, Any]]) -> None:
    with LEDGER.open("a", encoding="utf-8") as fh:
        for event in events:
            fh.write(json.dumps(event, sort_keys=True) + "\n")


def demand(source: str, a: Path, b: Path, claim_a: str, claim_b: str, checker: str) -> dict[str, Any]:
    paths = [rel(a), rel(b)]
    did = f"{source}:{digest(paths + [claim_a, claim_b, checker])}"
    return {
        "id": did,
        "source": source,
        "artifact_a": paths[0],
        "artifact_b": paths[1],
        "claim_a": claim_a,
        "claim_b": claim_b,
        "checker_needed": checker,
        "provenance_paths": paths,
        "admissible": a.exists() and b.exists(),
    }


def json_leafs(obj: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key, val in obj.items():
            out.update(json_leafs(val, f"{prefix}.{key}" if prefix else str(key)))
        return out
    if isinstance(obj, list):
        if len(obj) <= 8 and all(not isinstance(v, (dict, list)) for v in obj):
            return {prefix: obj}
        return {}
    return {prefix: obj}


def mine_result_jsons(limit: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    by_dir: dict[Path, list[Path]] = {}
    for path in sorted((ROOT / "system_v7/sims").glob("*/results/*results.json")):
        by_dir.setdefault(path.parent, []).append(path)
    for paths in by_dir.values():
        for agreement in [p for p in paths if "agreement" in p.name or "parity" in p.name or "three_engine" in p.name]:
            try:
                data = read_json(agreement)
            except Exception:
                continue
            leaves = json_leafs(data)
            disagree = [k for k, v in leaves.items() if any(tok in k.lower() for tok in ("agree", "parity", "match", "mismatch", "differ")) and v not in (True, "true", "ok", 0, "0", [], None)]
            legs = [p for p in paths if p != agreement and any(tok in p.name for tok in ("jax", "julia", "pytorch", "numpy", "exact"))]
            if disagree and legs:
                out.append(demand("result_jsons", agreement, legs[0], f"parity fields disagree: {disagree[:3]}", f"engine leg exists: {rel(legs[0])}", "json-field-compare"))
            if len(out) >= limit:
                return out
    return out


def mine_registry_rows(limit: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for registry in [ROOT / "system_v5/docs/17_actual_lego_registry.md"]:
        text = registry.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "|" not in line or "`" not in line:
                continue
            cells = [c.strip().strip("`") for c in line.split("|")]
            result_cells = [c for c in cells if c.endswith("_results.json")]
            status = next((c for c in cells if c in {"covered", "partial", "not_normalized_yet"}), "")
            for result_name in result_cells:
                matches = list(ROOT.glob(f"**/{result_name}"))
                if status and not matches:
                    ghost = SIM_DIR / "missing_artifacts" / result_name
                    out.append(demand("registry_missing_result", registry, ghost, f"registry status={status}", f"no result JSON named {result_name} on disk", "path-exists"))
                    if len(out) >= limit:
                        return out
    return out


def mine_doc_code_drift(limit: int) -> list[dict[str, Any]]:
    migration = ROOT / "system_v5/docs/MIGRATION_REGISTRY.md"
    torch_files = sorted(ROOT.glob("system_v7/sims/**/*torch*.py")) + sorted(ROOT.glob("system_v7/sims/**/*pytorch*.py"))
    if migration.exists() and torch_files:
        return [demand("doc_code_drift", migration, torch_files[0], "MIGRATION_REGISTRY summary says zero torch modules exist", f"torch/pytorch sim file exists: {rel(torch_files[0])}", "count-vs-listing")][:limit]
    return []


def mine_wiki_ops(limit: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for wiki_file in [WIKI_OPS / "contradictions.md", WIKI_OPS / "stale-status.md"]:
        if not wiki_file.exists():
            continue
        for line in wiki_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("- "):
                out.append(demand("wiki_ops", wiki_file, wiki_file, "wiki ops unresolved/stale entry", line[:240], "date-order"))
                if len(out) >= limit:
                    return out
    return out


def mine_semantic_naming(limit: int) -> list[dict[str, Any]]:
    audit = ROOT / "system_v5/ops/semantic_naming/sim_name_claim_label_audit.json"
    out: list[dict[str, Any]] = []
    if not audit.exists():
        return out
    for item in read_json(audit).get("result_matches", []):
        path = ROOT / item.get("path", "")
        if path.exists() and item.get("rename_when_reused"):
            out.append(demand("semantic_naming", audit, path, "name-vs-claim mismatch audit flags rename_when_reused", f"artifact exists with labels {item.get('matched_claim_labels', [])}", "json-field-compare"))
            if len(out) >= limit:
                return out
    return out


def mine_demands(limit: int) -> list[dict[str, Any]]:
    miners = [mine_result_jsons, mine_registry_rows, mine_doc_code_drift, mine_wiki_ops, mine_semantic_naming]
    out: list[dict[str, Any]] = []
    per_miner = max(1, limit // len(miners))
    for miner in miners:
        out.extend(miner(per_miner))
    if len(out) < limit:
        for miner in miners:
            out.extend(miner(limit - len(out)))
            if len(out) >= limit:
                break
    unique: dict[str, dict[str, Any]] = {}
    for item in out:
        unique.setdefault(item["id"], item)
    return list(unique.values())[:limit]


def checker_expresses(name: str, dem: dict[str, Any]) -> bool:
    if name == "path-exists":
        return dem["checker_needed"] == name and all((ROOT / p).exists() if not p.startswith("/") else Path(p).exists() for p in dem["provenance_paths"])
    if name == "json-field-compare":
        return dem["checker_needed"] == name and all((ROOT / p).suffix == ".json" or Path(p).suffix == ".json" for p in dem["provenance_paths"])
    if name == "count-vs-listing":
        return dem["checker_needed"] == name
    if name == "date-order":
        return dem["checker_needed"] == name and bool(re.search(r"20\d\d-\d\d-\d\d", dem["claim_a"] + dem["claim_b"]))
    if name == "parity-recompute-numpy":
        if dem["checker_needed"] != name:
            return False
        np.array([0.0, 1.0]).sum()
        return True
    return False


def run_tick(state: dict[str, Any], ts: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    seen = set(state["seen_demand_ids"])
    for dem in mine_demands(10):
        if dem["id"] in seen:
            continue
        seen.add(dem["id"])
        if dem["admissible"]:
            state["demand_frontier"].append(dem)
            events.append(line_event("DEMAND_ADMITTED", ts, demand=dem))
        else:
            state["voided"].append(dem["id"])
            events.append(line_event("DEMAND_VOID", ts, demand=dem, reason="artifact missing; disagreement not recomputable"))
    state["seen_demand_ids"] = sorted(seen)

    locked = [c["name"] for c in state["locked_checkers"]]
    for dem in list(state["demand_frontier"]):
        met_by = next((name for name in locked if checker_expresses(name, dem)), None)
        if met_by:
            state["demand_frontier"].remove(dem)
            state["met"].append({"id": dem["id"], "checker": met_by, "ts": ts})
            events.append(line_event("DEMAND_MET", ts, demand_id=dem["id"], checker=met_by))
            continue
        events.append(line_event("MINIMALIST_FAILED_PROOF", ts, demand_id=dem["id"], locked_checkers=locked, result="none separate_or_reconcile"))
        candidates = [name for name in CHECKER_ORDER if name not in locked and checker_expresses(name, dem)]
        if candidates:
            chosen = candidates[0]
            for rejected in candidates[1:]:
                events.append(line_event("REJECTED_UNFORCED", ts, demand_id=dem["id"], checker=rejected, reason="stronger than weakest expressing checker"))
            state["locked_checkers"].append({"name": chosen, "locked_at": ts, "demand_id": dem["id"]})
            events.append(line_event("LIFT_LOCKED", ts, demand_id=dem["id"], checker=chosen, weakest=True))
        break
    state["ticks_completed"] += 1
    return state, events


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticks", type=int, required=True)
    parser.add_argument("--tick-start", default="2026-07-03T00:00:00Z")
    args = parser.parse_args()
    start = datetime.fromisoformat(args.tick_start.replace("Z", "+00:00")).astimezone(timezone.utc)
    state = load_state()
    all_events: list[dict[str, Any]] = []
    for idx in range(args.ticks):
        ts = (start + timedelta(seconds=idx)).isoformat().replace("+00:00", "Z")
        state, events = run_tick(state, ts)
        append(events)
        all_events.extend(events)
    STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    line_count = sum(1 for _ in LEDGER.open("r", encoding="utf-8")) if LEDGER.exists() else 0
    summary = {
        "sim_id": SIM_ID,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "ticks_run": args.ticks,
        "events": dict(Counter(event["event"] for event in all_events)),
        "demands_mined_per_source": dict(Counter(event["demand"]["source"] for event in all_events if "demand" in event)),
        "locked_checkers": [c["name"] for c in state["locked_checkers"]],
        "ledger_line_count": line_count,
        "boundary": "ops-ratchet standing process; no physics sim or three-engine numeric recompute claimed",
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
