#!/usr/bin/env python3
"""cb_agents — see what agents and background jobs are doing, right now.

Built 2026-08-07 after a 21-minute workflow ran with no visibility into whether
its agents were working or spinning. Polling a file for a result is not
monitoring: it cannot tell "slow" from "stuck".

  cb_agents.py                 one-shot status
  cb_agents.py --watch         refresh until everything is idle
  cb_agents.py --stuck-min 4   flag any agent silent longer than this
  cb_agents.py --kill-stuck    terminate local cb_* jobs past the stall bound

Reads the Claude Code session transcripts under
  ~/.claude/projects/<slug>/<session>/subagents/workflows/<run>/
where each agent appends to agent-*.jsonl and the run appends journal.jsonl.
An agent that has not appended for --stuck-min is STALLED: that is a wall-clock
fact, not an inference about its reasoning.

Also lists local cb_*.py processes with their elapsed time, because the swarm
scripts are the other thing that runs long.

promotion_allowed=false.
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, time
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
STALL_DEFAULT = 4.0          # minutes of silence before an agent is STALLED


def _mtime_age_min(p: Path) -> float:
    try:
        return (time.time() - p.stat().st_mtime) / 60.0
    except OSError:
        return float("inf")


def find_runs(limit_hours: float = 12.0) -> list:
    """Every workflow run directory touched recently, newest first."""
    runs = []
    if not PROJECTS.is_dir():
        return runs
    for wf in PROJECTS.glob("*/*/subagents/workflows/*"):
        if not wf.is_dir():
            continue
        j = wf / "journal.jsonl"
        agents = sorted(wf.glob("agent-*.jsonl"))
        newest = max([_mtime_age_min(x) * -1 for x in agents + ([j] if j.exists() else [])],
                     default=None)
        if newest is None:
            continue
        age = -newest
        if age > limit_hours * 60:
            continue
        runs.append({"dir": wf, "age_min": age, "journal": j, "agents": agents})
    return sorted(runs, key=lambda r: r["age_min"])


def _tail_json(p: Path, n: int = 400) -> list:
    out = []
    try:
        with p.open("r", errors="ignore") as fh:
            lines = fh.readlines()[-n:]
    except OSError:
        return out
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out


def _last_activity(rec: dict) -> str:
    """One short line describing whatever the agent last did."""
    t = rec.get("type", "")
    if t == "assistant":
        msg = rec.get("message", {})
        for c in msg.get("content", []) or []:
            if c.get("type") == "tool_use":
                nm = c.get("name", "tool")
                inp = c.get("input", {}) or {}
                arg = (inp.get("command") or inp.get("file_path")
                       or inp.get("pattern") or inp.get("query") or "")
                return f"{nm}: {str(arg)[:70]}"
            if c.get("type") == "text" and c.get("text", "").strip():
                return "thinking/text: " + " ".join(c["text"].split())[:70]
        return "assistant turn"
    if t == "user":
        return "tool result"
    if t == "result":
        return "RETURNED"
    return t or "?"


def journal_state(journal: Path) -> tuple:
    """(started_ids, returned_ids) from the run journal.

    Completion is recorded in journal.jsonl as {"type":"result","agentId":...},
    NOT in the agent's own transcript. Reading only the transcript made every
    finished agent look STALLED, because a finished agent stops writing — which
    is exactly what silence looks like.
    """
    started, returned = set(), set()
    for r in _tail_json(journal, n=100000):
        aid = r.get("agentId")
        if not aid:
            continue
        if r.get("type") == "started":
            started.add(aid)
        elif r.get("type") == "result":
            returned.add(aid)
    return started, returned


def agent_status(p: Path, stall_min: float, returned: set = frozenset()) -> dict:
    recs = _tail_json(p)
    # agent-<id>.jsonl -> <id>
    aid = p.stem.split("-", 1)[1] if "-" in p.stem else p.stem
    done = aid in returned or any(r.get("type") == "result" for r in recs)
    idle = _mtime_age_min(p)
    tool_calls = sum(1 for r in recs if r.get("type") == "assistant"
                     for c in (r.get("message", {}).get("content") or [])
                     if c.get("type") == "tool_use")
    last = _last_activity(recs[-1]) if recs else "no records"
    if done:
        state = "DONE"
    elif idle >= stall_min:
        state = "STALLED"
    else:
        state = "working"
    return {"file": p.name, "state": state, "idle_min": round(idle, 1),
            "tool_calls": tool_calls, "last": last}


def local_jobs() -> list:
    """cb_*.py processes running on this machine, with elapsed time."""
    try:
        out = subprocess.run(["ps", "-eo", "pid,etime,command"],
                             capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return []
    jobs = []
    for ln in out.splitlines()[1:]:
        if "cb_" not in ln or "cb_agents.py" in ln or " grep " in ln:
            continue
        m = re.match(r"\s*(\d+)\s+(\S+)\s+(.*)", ln)
        if not m:
            continue
        pid, et, cmd = m.groups()
        script = next((Path(w).name for w in cmd.split()
                       if w.endswith(".py") and "cb_" in w), None)
        if script:
            jobs.append({"pid": int(pid), "elapsed": et, "script": script})
    return jobs


def _etime_min(et: str) -> float:
    parts = et.split("-")
    days = int(parts[0]) if len(parts) == 2 else 0
    hms = (parts[1] if len(parts) == 2 else parts[0]).split(":")
    hms = [float(x) for x in hms]
    while len(hms) < 3:
        hms.insert(0, 0.0)
    return days * 1440 + hms[0] * 60 + hms[1] + hms[2] / 60


def render(stall_min: float, quiet_runs_min: float = 90.0) -> tuple:
    lines, any_active = [], False
    runs = find_runs()
    lines.append(f"{'='*74}\nAGENTS  {time.strftime('%H:%M:%S')}   "
                 f"stall bound {stall_min} min\n{'='*74}")
    if not runs:
        lines.append("  no workflow runs in the last 12h")
    for r in runs:
        if r["age_min"] > quiet_runs_min:
            continue
        _, returned = journal_state(r["journal"])
        sts = [agent_status(a, stall_min, returned) for a in r["agents"]]
        done = sum(1 for s in sts if s["state"] == "DONE")
        stalled = [s for s in sts if s["state"] == "STALLED"]
        working = [s for s in sts if s["state"] == "working"]
        if working or stalled:
            any_active = True
        lines.append(f"\nRUN {r['dir'].name}   {len(sts)} agents   "
                     f"{done} done / {len(working)} working / {len(stalled)} STALLED   "
                     f"(last write {r['age_min']:.1f}m ago)")
        for s in sts:
            if s["state"] == "DONE":
                continue
            flag = "!!" if s["state"] == "STALLED" else "  "
            lines.append(f"  {flag} {s['file']:<30}{s['state']:<9}"
                         f"idle {s['idle_min']:>5.1f}m  {s['tool_calls']:>3} calls  {s['last']}")
        if done == len(sts) and sts:
            lines.append("     all agents returned")

    jobs = local_jobs()
    lines.append(f"\n{'-'*74}\nLOCAL cb_* PROCESSES")
    if not jobs:
        lines.append("  none")
    for j in jobs:
        mins = _etime_min(j["elapsed"])
        flag = "!!" if mins > 20 else "  "
        if mins > 0:
            any_active = True
        lines.append(f"  {flag} pid {j['pid']:<7}{j['elapsed']:>10}  {j['script']}")
    stalled_all = []
    for r in runs:
        if r["age_min"] > quiet_runs_min:
            continue
        _, ret = journal_state(r["journal"])
        stalled_all += [s for s in (agent_status(a, stall_min, ret) for a in r["agents"])
                        if s["state"] == "STALLED"]
    return "\n".join(lines), any_active, stalled_all


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--every", type=int, default=20, help="watch refresh seconds")
    ap.add_argument("--stuck-min", type=float, default=STALL_DEFAULT)
    ap.add_argument("--kill-stuck", action="store_true",
                    help="terminate local cb_* jobs over 40 min")
    a = ap.parse_args()

    while True:
        text, active, stalled = render(a.stuck_min)
        os.system("clear") if a.watch else None
        print(text)
        if stalled:
            print(f"\n{len(stalled)} STALLED agent(s) — silent past the "
                  f"{a.stuck_min}-minute bound. Silence is the measurement; it "
                  f"does not say why.")
        if a.kill_stuck:
            for j in local_jobs():
                if _etime_min(j["elapsed"]) > 40:
                    print(f"  killing pid {j['pid']} ({j['script']}, {j['elapsed']})")
                    subprocess.run(["kill", str(j["pid"])])
        if not a.watch:
            return 1 if stalled else 0
        if not active:
            print("\nidle — nothing running")
            return 0
        time.sleep(a.every)


if __name__ == "__main__":
    sys.exit(main())
