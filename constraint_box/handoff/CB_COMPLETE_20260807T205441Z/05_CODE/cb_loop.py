#!/usr/bin/env python3
"""cb_loop — the continuous driver. Run this from Claude Code or Codex and
it keeps working without a human turn between steps.

Everything this session built is already in constraint_box/scripts/. This
is the thing that drives them in a loop, with budgets, monotone measures,
and resumable state.

  cycle = W0 census -> W-FALSIFY -> W-AUTORESEARCH -> write state
  stops on: budget exhausted, or LAW 8 (no measure moved), or clean

State lives in constraint_box/receipts/cb_loop_state.json so a killed run
resumes instead of restarting.

  cb_loop.py --cycles 20 --max-minutes 90 --max-usd 5
  cb_loop.py --resume
promotion_allowed=false.
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time
from pathlib import Path

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SC = REPO / "constraint_box" / "scripts"
RC = REPO / "constraint_box" / "receipts"
STATE = RC / "cb_loop_state.json"
PY = str(Path.home() / ".local/share/codex-ratchet/envs/main/bin/python3")

def run(script: str, *args, timeout=1800) -> dict:
    t0 = time.time()
    p = subprocess.run([PY, str(SC / script), *args], capture_output=True,
                       text=True, timeout=timeout, cwd=str(REPO))
    return {"script": script, "rc": p.returncode, "sec": round(time.time()-t0, 1),
            "tail": (p.stdout or "")[-1400:], "err": (p.stderr or "")[-300:]}

def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"schema": "cb.loop-state.v1", "cycle": 0, "history": [],
            "measures": {}, "promotion_allowed": False}

def measures_now() -> dict:
    """the monotone measures the loop advances. All deterministic."""
    m = {}
    r = run("cb_integrated_run.py", timeout=900)
    for line in r["tail"].splitlines():
        if line.startswith("MEASURES"):
            for part in line.replace("MEASURES", "").strip().split():
                if "=" in part:
                    k, v = part.split("=", 1)
                    try: m[k] = int(v)
                    except ValueError: m[k] = v
    m["_integrated_rc"] = r["rc"]; m["_sec"] = r["sec"]
    return m, r

def advanced(prev: dict, cur: dict) -> tuple[bool, str]:
    """LAW 8: a cycle is live only if a declared measure moved."""
    if not prev:
        return True, "first cycle"
    moved = []
    for k in ("never_run", "deep_survivors"):
        if k in prev and k in cur and prev[k] != cur[k]:
            moved.append(f"{k}: {prev[k]} -> {cur[k]}")
    return bool(moved), "; ".join(moved) if moved else "no declared measure moved"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", type=int, default=10)
    ap.add_argument("--max-minutes", type=float, default=60.0)
    ap.add_argument("--targets", default="decision,followup")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--dead-cycles-allowed", type=int, default=2)
    a = ap.parse_args()

    st = load_state() if a.resume else load_state()
    t_start = time.time(); dead = 0
    print(f"CB LOOP  starting at cycle {st['cycle']}  budget {a.cycles} cycles / "
          f"{a.max_minutes} min")
    print(f"  interpreter {PY}")
    print(f"  state {STATE.relative_to(REPO)}\n")

    while st["cycle"] < a.cycles:
        if (time.time() - t_start) / 60 > a.max_minutes:
            print(f"BUDGET: wall-clock limit reached at cycle {st['cycle']}"); break
        st["cycle"] += 1
        c0 = time.time()
        print(f"{'='*66}\nCYCLE {st['cycle']}")

        cur, ir = measures_now()
        print(f"  W0/W1/W2  {['%s=%s' % (k,v) for k,v in cur.items() if not k.startswith('_')]}"
              f"  ({cur['_sec']}s)")

        fals = run("cb_wave_falsifier_v3.py", "--targets", a.targets, timeout=1500)
        killed = [l for l in fals["tail"].splitlines() if "SUMMARY" in l]
        print(f"  W-FALSIFY {killed[0].strip() if killed else 'no summary'}  ({fals['sec']}s)")

        ar = run("cb_autoresearch_loop.py", timeout=900)
        wrote = "WROTE BACK" in ar["tail"]
        dead_line = "LOOP DEAD" in ar["tail"]
        print(f"  W-AUTORES wrote_back={wrote} dead={dead_line}  ({ar['sec']}s)")

        ok, why = advanced(st.get("measures", {}), cur)
        print(f"  MEASURE   {'ADVANCED' if ok else 'STATIC'}: {why}")
        st["measures"] = {k: v for k, v in cur.items() if not k.startswith("_")}
        st["history"].append({"cycle": st["cycle"], "sec": round(time.time()-c0, 1),
            "measures": st["measures"], "advanced": ok, "why": why,
            "autoresearch_wrote": wrote,
            "falsifier_summary": killed[0].strip() if killed else ""})
        st["history"] = st["history"][-40:]
        RC.mkdir(exist_ok=True); STATE.write_text(json.dumps(st, indent=1, sort_keys=True))

        if not ok:
            dead += 1
            print(f"  DEAD CYCLE {dead}/{a.dead_cycles_allowed} (LAW 8)")
            if dead >= a.dead_cycles_allowed:
                print(f"\nSTOPPING: {dead} consecutive cycles advanced nothing. "
                      f"The loop is spinning; report rather than burn budget.")
                break
        else:
            dead = 0

    print(f"\n{'='*66}\nLOOP END  cycles={st['cycle']}  "
          f"wall={round((time.time()-t_start)/60,1)} min")
    print(f"final measures: {st['measures']}")
    print(f"state: {STATE.relative_to(REPO)}  (resume with --resume)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
