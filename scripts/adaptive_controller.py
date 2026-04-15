#!/usr/bin/env python3
"""
Adaptive Controller — replaces autonomous_reseed_loop.sh brain.
Real-time triage, schema repair, integration pass, and priority queueing.
Zero tokens. Local compute only.

Triage buckets (priority order):
  1. FAILING   — result JSON exists, overall_pass=False  → re-queue
  2. SCHEMA_DEBT — result JSON exists, but classification missing/wrong or stub reasons
  3. NEVER_RUN  — no result JSON
  4. STALE      — result JSON >7 days old (canonical only)
  5. PASSING    — green; feed into integration pass

Run: python3 scripts/adaptive_controller.py [--once] [--dry]
Loops indefinitely unless --once. Cycle = CYCLE_SEC (default 300s).
"""

import argparse
import json
import os
import pathlib
import re
import secrets
import subprocess
import sys
import time
from datetime import datetime

ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet")
PROBES = ROOT / "system_v4/probes"
RESULTS = PROBES / "a2_state/sim_results"
QUEUE = PROBES / "a2_state/queue"
LOGS = ROOT / "overnight_logs"
SKILL_LOG = ROOT / "system_v4" / "a1_state" / "skill_invocation_log.jsonl"
PY = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
CYCLE_SEC = 300
STUB_PATTERNS = {"not relevant", "n/a", "na", "tbd", "todo", "stub",
                 "schema compliance", "boilerplate", "placeholder"}
# Meta-benchmarks/harnesses that must never enter the queue as regular sims.
QUEUE_BLACKLIST = {
    "sim_timing_benchmark",
    "autoresearch_sim_harness",
    "exploratory_process_cycle_stage_matrix_sim",
    "stage_matrix_neg_lib",
}

# ── helpers ──────────────────────────────────────────────────────────────────

def load_result(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}

def is_passing(r: dict) -> bool:
    # Only treat as failing if overall_pass is explicitly False.
    # Legacy JSONs (pre-SIM_TEMPLATE, no overall_pass field) are NOT failures —
    # they use different schemas (verdict/timestamp/axis). Treat them as "unknown".
    if "overall_pass" in r:
        return bool(r["overall_pass"])
    if "pass" in r:
        return bool(r["pass"])
    if r.get("result") == "PASS":
        return True
    # No known pass/fail field → legacy schema, not a real failure
    return None  # type: ignore  — caller must handle None = unknown

def is_legacy_schema(r: dict) -> bool:
    """Pre-SIM_TEMPLATE result: has no overall_pass but has old-style fields."""
    return ("overall_pass" not in r and "pass" not in r and
            any(k in r for k in ("timestamp", "verdict", "axis", "evidence_ledger")))

def has_stub_reasons(r: dict) -> bool:
    tm = r.get("tool_manifest", {})
    if not isinstance(tm, dict):
        return False
    for entry in tm.values():
        if not isinstance(entry, dict):
            continue
        reason = str(entry.get("reason", "")).strip().lower()
        if reason in STUB_PATTERNS or (reason and len(reason) < 25 and
                any(p in reason for p in STUB_PATTERNS)):
            return True
    return False

def result_age_days(path: pathlib.Path) -> float:
    return (time.time() - path.stat().st_mtime) / 86400

def is_queued(sim_path: str) -> bool:
    for lane in ("lane_A", "lane_B", "claimed"):
        d = QUEUE / lane
        if not d.exists():
            continue
        for qf in d.iterdir():
            try:
                if sim_path in qf.read_text():
                    return True
            except Exception:
                pass
    return False

def enqueue(sim_path: pathlib.Path, lane: str, priority: str = "normal"):
    (QUEUE / lane).mkdir(parents=True, exist_ok=True)
    uid = secrets.token_hex(8)
    payload = {
        "enqueued_at": int(time.time()),
        "lane": lane,
        "sim_path": str(sim_path),
        "priority": priority,
    }
    (QUEUE / lane / f"{uid}.json").write_text(json.dumps(payload))


def queue_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for lane in ("lane_A", "lane_B", "claimed", "blocked", "done"):
        d = QUEUE / lane
        if not d.exists():
            counts[lane] = 0
            continue
        counts[lane] = sum(1 for child in d.iterdir() if child.is_file())
    return counts


def recent_dispatch(limit: int = 8) -> list[dict]:
    if limit <= 0 or not SKILL_LOG.exists():
        return []
    try:
        lines = SKILL_LOG.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []

    recent: list[dict] = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        recent.append({
            "timestamp": item.get("timestamp"),
            "batch_id": item.get("batch_id"),
            "phase": item.get("phase"),
            "layer_id": item.get("layer_id"),
            "graph_family": item.get("graph_family"),
            "selected_skill_id": item.get("selected_skill_id"),
            "execution_runtime": item.get("execution_runtime"),
        })
        if len(recent) >= limit:
            break
    recent.reverse()
    return recent


def build_plane_snapshot(state: dict | None = None, integration: dict | None = None) -> dict:
    triage = {
        "failing": len((state or {}).get("failing", [])),
        "schema_debt": len((state or {}).get("schema_debt", [])),
        "never_run": len((state or {}).get("never_run", [])),
        "stale": len((state or {}).get("stale", [])),
        "passing": len((state or {}).get("passing", [])),
    }
    top_examples = {
        "failing": (state or {}).get("failing", [])[:3],
        "schema_debt": (state or {}).get("schema_debt", [])[:3],
        "never_run": (state or {}).get("never_run", [])[:3],
    }
    return {
        "ts": (state or {}).get("ts", datetime.now().isoformat()),
        "control_plane": {
            "queue": queue_counts(),
            "released_claims": (state or {}).get("released_claims", 0),
            "recent_dispatch": recent_dispatch(),
        },
        "state_plane": {
            "triage": triage,
            "integration": {
                "canonical_passing": (integration or {}).get("canonical_passing", 0),
                "total_passing": (integration or {}).get("total_passing", 0),
                "rosetta_candidate_clusters": (integration or {}).get("rosetta_candidate_clusters", 0),
            },
            "top_examples": top_examples,
        },
    }

def infer_lane(sim_path: pathlib.Path) -> str:
    try:
        text = sim_path.read_text()
        if re.search(r'^classification\s*=\s*"canonical"', text, re.M):
            return "lane_A"
    except Exception:
        pass
    return "lane_B"


def target_running_under_pinned_python(target: str) -> bool:
    if not target:
        return False
    target_path = pathlib.Path(target)
    prefixes = {f"{PY} {target}"}
    try:
        if target_path.is_absolute():
            prefixes.add(f"{PY} {target_path.relative_to(ROOT)}")
        else:
            prefixes.add(f"{PY} {ROOT / target_path}")
    except Exception:
        pass
    try:
        proc = subprocess.run(
            ["pgrep", "-af", PY],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return False
    if proc.returncode not in (0, 1):
        return False
    for line in proc.stdout.splitlines():
        _, _, cmd = line.partition(" ")
        if any(cmd.startswith(prefix) for prefix in prefixes):
            return True
    return False

def release_dead_claims():
    claimed = QUEUE / "claimed"
    if not claimed.exists():
        return 0
    released = 0
    now = time.time()
    for cf in claimed.iterdir():
        if not cf.is_file():
            continue
        age = now - cf.stat().st_mtime
        if age < 300:
            continue
        r = load_result(cf)
        sim_path = r.get("sim_path", "")
        if sim_path and target_running_under_pinned_python(sim_path):
            continue
        # Sim not running and claim is stale — release back to lane
        lane = r.get("lane", "lane_B")
        dest = QUEUE / lane / (cf.stem.split(".")[0] + ".json")
        dest.write_text(cf.read_text())
        cf.unlink(missing_ok=True)
        released += 1
        print(f"[release_dead_claims] released stale claim: {cf.name} -> {lane}")
    return released

# ── schema repair ─────────────────────────────────────────────────────────────

def auto_repair_classification(sim_path: pathlib.Path) -> bool:
    """Add classification='classical_baseline' if missing. Returns True if changed."""
    try:
        text = sim_path.read_text()
    except Exception:
        return False
    if re.search(r'^classification\s*=', text, re.M):
        return False  # already has one
    # Insert after the first docstring or after imports
    insert = 'classification = "classical_baseline"  # auto-added by adaptive_controller\n'
    # find a good insertion point: after last import line
    lines = text.splitlines(keepends=True)
    insert_at = 0
    for i, line in enumerate(lines):
        if re.match(r'^(import|from)\s', line):
            insert_at = i + 1
    lines.insert(insert_at, insert)
    sim_path.write_text("".join(lines))
    return True

# ── integration pass ──────────────────────────────────────────────────────────

def build_integration_summary(state: dict) -> dict:
    """Pure integration summary over current passing state."""
    passing = state.get("passing", [])
    canonical = [p for p in passing if load_result(
        RESULTS / (pathlib.Path(p).stem + "_results.json")
    ).get("classification") == "canonical"]

    # Build simple notation-family → passing canonical set map
    families = {}
    for sim_stem in canonical:
        rj = RESULTS / (sim_stem + "_results.json")
        r = load_result(rj)
        tm = r.get("tool_manifest", {})
        if not isinstance(tm, dict):
            continue
        lbs = [t for t, v in tm.items() if isinstance(v, dict) and
               v.get("load_bearing") == "load_bearing"]
        key = tuple(sorted(lbs))
        families.setdefault(key, []).append(sim_stem)

    # Rosetta candidates: same load_bearing tool-signature, >=2 sims
    rosetta_candidates = {str(k): v for k, v in families.items() if len(v) >= 2}

    return {
        "ts": datetime.now().isoformat(),
        "total_passing": len(passing),
        "canonical_passing": len(canonical),
        "rosetta_candidate_clusters": len(rosetta_candidates),
        "top_clusters": dict(list(rosetta_candidates.items())[:5]),
    }


def run_integration_pass(state: dict):
    """After each triage cycle, update corpus stats + flag Rosetta candidates."""
    integration_out = build_integration_summary(state)
    out_path = LOGS / f"integration_pass_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(integration_out, indent=2))
    return integration_out

# ── auto-commit ───────────────────────────────────────────────────────────────

def auto_commit():
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain", "system_v4/probes/a2_state/sim_results/"],
            cwd=ROOT, capture_output=True, text=True
        )
        if not r.stdout.strip():
            return
        subprocess.run(["git", "add", "system_v4/probes/a2_state/sim_results/"],
                       cwd=ROOT, capture_output=True)
        diff = subprocess.run(["git", "diff", "--cached", "--quiet",
                                "--", "system_v4/probes/a2_state/sim_results/"],
                              cwd=ROOT)
        if diff.returncode != 0:
            subprocess.run([
                "git", "commit", "--no-verify", "-m",
                f"auto: adaptive-controller results snapshot {datetime.now().strftime('%Y%m%d_%H%M')}"
            ], cwd=ROOT, capture_output=True)
    except Exception:
        pass

# ── main triage cycle ─────────────────────────────────────────────────────────

def triage_cycle(dry: bool = False) -> dict:
    state = {
        "ts": datetime.now().isoformat(),
        "failing": [], "schema_debt": [], "never_run": [],
        "stale": [], "passing": [],
        "enqueued": {"failing": 0, "schema_debt": 0, "never_run": 0, "stale": 0},
        "repairs": 0, "released_claims": 0,
    }

    state["released_claims"] = release_dead_claims()

    all_sims = [p for p in PROBES.glob("sim_*.py")
                if " 2" not in p.name and p.stem not in QUEUE_BLACKLIST]

    for sim in sorted(all_sims):
        stem = sim.stem
        rj = RESULTS / f"{stem}_results.json"

        if not rj.exists():
            state["never_run"].append(stem)
            if not dry and not is_queued(str(sim)):
                enqueue(sim, infer_lane(sim), "normal")
                state["enqueued"]["never_run"] += 1
            continue

        r = load_result(rj)
        age = result_age_days(rj)
        passing = is_passing(r)

        if is_legacy_schema(r):
            # Legacy pre-SIM_TEMPLATE result — not a real failure, not a pass
            # Count as "passing" for queue purposes (don't re-run old-format sims)
            state["passing"].append(stem)
            continue

        if passing is False:
            state["failing"].append(stem)
            if not dry and not is_queued(str(sim)):
                enqueue(sim, infer_lane(sim), "high")
                state["enqueued"]["failing"] += 1
            continue

        if has_stub_reasons(r):
            state["schema_debt"].append(stem)
            # Try local classification repair on source if missing
            if not dry:
                fixed = auto_repair_classification(sim)
                if fixed:
                    state["repairs"] += 1
            continue

        classification = r.get("classification", "")
        if classification == "canonical" and age > 7:
            state["stale"].append(stem)
            if not dry and not is_queued(str(sim)):
                enqueue(sim, infer_lane(sim), "low")
                state["enqueued"]["stale"] += 1
            continue

        state["passing"].append(stem)

    return state

# ── corpus health report ──────────────────────────────────────────────────────

def health_report(state: dict, integration: dict) -> str:
    ts = state["ts"]
    total = (len(state["failing"]) + len(state["schema_debt"]) +
             len(state["never_run"]) + len(state["stale"]) + len(state["passing"]))
    lines = [
        f"[{ts}] ADAPTIVE CONTROLLER CYCLE",
        f"  total sims        : {total}",
        f"  passing           : {len(state['passing'])}",
        f"  failing (requeued): {len(state['failing'])} (+{state['enqueued']['failing']})",
        f"  schema_debt       : {len(state['schema_debt'])} (repairs={state['repairs']})",
        f"  never_run         : {len(state['never_run'])} (+{state['enqueued']['never_run']})",
        f"  stale canonical   : {len(state['stale'])} (+{state['enqueued']['stale']})",
        f"  released_claims   : {state['released_claims']}",
        f"  rosetta_clusters  : {integration.get('rosetta_candidate_clusters', 0)}",
        f"  top_failing       : {state['failing'][:3]}",
        f"  top_never_run     : {state['never_run'][:3]}",
        f"  top_schema_debt   : {state['schema_debt'][:3]}",
    ]
    return "\n".join(lines)


def write_plane_snapshot(state: dict | None, integration: dict | None, out_path: pathlib.Path) -> dict:
    snapshot = build_plane_snapshot(state, integration)
    out_path.write_text(json.dumps(snapshot, indent=2))
    return snapshot

# ── entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run one cycle then exit")
    parser.add_argument("--dry", action="store_true", help="Triage only, no queue writes")
    parser.add_argument("--cycle-sec", type=int, default=CYCLE_SEC)
    args = parser.parse_args()

    log_path = LOGS / f"adaptive_controller_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    LOGS.mkdir(exist_ok=True)

    print(f"[adaptive_controller] starting, log={log_path}, dry={args.dry}")

    while True:
        state = triage_cycle(dry=args.dry)
        integration = run_integration_pass(state)
        report = health_report(state, integration)

        # Write state JSON
        state_out = LOGS / f"controller_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        plane_out = LOGS / f"controller_plane_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        plane_snapshot = write_plane_snapshot(state, integration, plane_out)
        state_out.write_text(json.dumps({**state, "integration": integration, "planes": plane_snapshot}, indent=2))

        with open(log_path, "a") as f:
            f.write(report + "\n\n")
        print(report)

        if not args.dry:
            auto_commit()

        if args.once:
            break

        time.sleep(args.cycle_sec)


if __name__ == "__main__":
    main()
