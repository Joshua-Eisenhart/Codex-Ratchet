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

The falsify leg reaches paid providers (OpenRouter + the claude/codex/gemini
CLIs) through cb_multi_provider. It is OFF unless --allow-paid is passed, so
the default loop is free and offline.

  cb_loop.py --cycles 5                 # free: census + autoresearch
  cb_loop.py --cycles 5 --allow-paid    # adds the falsify leg, bills per cycle
  cb_loop.py --resume                   # continue from saved state
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

def fresh_state() -> dict:
    return {"schema": "cb.loop-state.v1", "cycle": 0, "history": [],
            "measures": {}, "dead": 0, "stop_reason": None,
            "promotion_allowed": False}

def load_state(resume: bool) -> dict:
    """--resume continues from disk; without it the loop starts at cycle 0.

    Both branches used to be identical, so every run silently resumed and
    --cycles N meant "run until the saved cycle count reaches N".
    """
    if resume and STATE.exists():
        st = json.loads(STATE.read_text())
        st.setdefault("dead", 0)
        st.setdefault("stop_reason", None)
        return st
    return fresh_state()

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

MEASURE_KEYS = ("unmentioned", "deep_survivors")

def advanced(prev: dict, cur: dict) -> tuple[bool, str]:
    """LAW 8: a cycle is live only if it emitted a receipt AND a measure moved.

    Both conjuncts are tested. The receipt conjunct used to be missing, so a
    crashed census read as an ordinary static cycle.
    """
    if cur.get("_integrated_rc") != 0:
        return False, f"census failed (rc={cur.get('_integrated_rc')}) — no receipt"
    if not any(k in cur for k in MEASURE_KEYS):
        return False, "census emitted no MEASURES line"
    if not prev:
        return True, "first cycle"
    moved = [f"{k}: {prev[k]} -> {cur[k]}" for k in MEASURE_KEYS
             if k in prev and k in cur and prev[k] != cur[k]]
    return bool(moved), "; ".join(moved) if moved else "no declared measure moved"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", type=int, default=10)
    ap.add_argument("--max-minutes", type=float, default=60.0)
    ap.add_argument("--targets", default="decision,followup")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--dead-cycles-allowed", type=int, default=2)
    ap.add_argument("--allow-paid", action="store_true",
                    help="enable the falsify leg, which bills provider calls")
    a = ap.parse_args()

    st = load_state(a.resume)
    t_start = time.time(); dead = st.get("dead", 0)
    st["stop_reason"] = None
    print(f"CB LOOP  starting at cycle {st['cycle']}  budget {a.cycles} cycles / "
          f"{a.max_minutes} min")
    print(f"  interpreter {PY}")
    print(f"  state {STATE.relative_to(REPO)}"
          f"{'  (resumed)' if a.resume and st['cycle'] else '  (fresh)'}")
    print(f"  falsify leg {'ENABLED — bills providers' if a.allow_paid else 'OFF (free run)'}\n")

    while st["cycle"] < a.cycles:
        if (time.time() - t_start) / 60 > a.max_minutes:
            print(f"BUDGET: wall-clock limit reached at cycle {st['cycle']}")
            st["stop_reason"] = "wall_clock_budget"; break
        st["cycle"] += 1
        c0 = time.time()
        print(f"{'='*66}\nCYCLE {st['cycle']}")

        cur, ir = measures_now()
        print(f"  W0/W1/W2  {['%s=%s' % (k,v) for k,v in cur.items() if not k.startswith('_')]}"
              f"  ({cur['_sec']}s)")

        if a.allow_paid:
            fals = run("cb_wave_falsifier_v3.py", "--targets", a.targets, timeout=1500)
            killed = [l for l in fals["tail"].splitlines() if "SUMMARY" in l]
            print(f"  W-FALSIFY {killed[0].strip() if killed else 'no summary'}"
                  f"  ({fals['sec']}s, rc={fals['rc']})")
            fals_summary = killed[0].strip() if killed else ""
        else:
            print("  W-FALSIFY skipped — reaches paid providers, needs --allow-paid")
            fals_summary = "skipped (unpaid run)"

        ar = run("cb_autoresearch_loop.py", timeout=900)
        wrote = "WROTE BACK" in ar["tail"]
        dead_line = "LOOP DEAD" in ar["tail"]
        # rc=1 WITH the LAW 8 line is the leg correctly refusing to write back.
        # rc!=0 WITHOUT it is a real crash. Reporting both as "failed" hid a
        # KeyError for the whole life of this loop.
        if ar["rc"] != 0 and not dead_line:
            print(f"  W-AUTORES CRASHED rc={ar['rc']}  ({ar['sec']}s)")
            err = ar["err"].strip().splitlines()
            print(f"            {err[-1] if err else '(no stderr captured)'}")
        elif dead_line:
            print(f"  W-AUTORES dead (LAW 8: advanced nothing, refused to write)"
                  f"  ({ar['sec']}s)")
        else:
            print(f"  W-AUTORES wrote_back={wrote}  ({ar['sec']}s)")

        ok, why = advanced(st.get("measures", {}), cur)
        print(f"  MEASURE   {'ADVANCED' if ok else 'STATIC'}: {why}")
        st["measures"] = {k: v for k, v in cur.items() if not k.startswith("_")}
        st["history"].append({"cycle": st["cycle"], "sec": round(time.time()-c0, 1),
            "measures": st["measures"], "advanced": ok, "why": why,
            "census_rc": cur.get("_integrated_rc"),
            "autoresearch_rc": ar["rc"], "autoresearch_wrote": wrote,
            "autoresearch_err": ar["err"].strip()[-200:] if ar["rc"] else "",
            "falsify_leg": "paid" if a.allow_paid else "skipped",
            "falsifier_summary": fals_summary})
        st["history"] = st["history"][-40:]

        if not ok:
            dead += 1
            print(f"  DEAD CYCLE {dead}/{a.dead_cycles_allowed} (LAW 8)")
        else:
            dead = 0
        st["dead"] = dead
        RC.mkdir(exist_ok=True); STATE.write_text(json.dumps(st, indent=1, sort_keys=True))

        if not ok and dead >= a.dead_cycles_allowed:
            print(f"\nSTOPPING: {dead} consecutive cycles advanced nothing. "
                  f"The loop is spinning; report rather than burn budget.")
            st["stop_reason"] = f"law8_dead_cycles({dead})"
            STATE.write_text(json.dumps(st, indent=1, sort_keys=True))
            break

    if st["stop_reason"] is None:
        st["stop_reason"] = f"cycle_budget({a.cycles})"
    RC.mkdir(exist_ok=True); STATE.write_text(json.dumps(st, indent=1, sort_keys=True))
    print(f"\n{'='*66}\nLOOP END  cycles={st['cycle']}  "
          f"wall={round((time.time()-t_start)/60,1)} min")
    print(f"stop reason: {st['stop_reason']}")
    print(f"final measures: {st['measures']}")
    print(f"state: {STATE.relative_to(REPO)}  (resume with --resume)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
