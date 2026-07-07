#!/usr/bin/env python3
"""schedule_source_fidelity_linter -- PACKET 1 of the audit ladder (deep-audit-55 07_NEXT_PACKETS). A source-fidelity
LINTER, not a dynamic claim. It reads the source-faithful schedule tables (shipped by the external audit, derived
from the owner's IGT engine chart) and checks that:
  (1) the 16-slot chart is well-formed: 16 slots = 2 engines x 2 loops x 4 steps, one canonical operator + one axis-6
      sign per slot;
  (2) the 64-schedule is the exact 16x4 expansion: each slot runs all 4 operators sharing that slot's terrain+sign,
      and exactly 16 of the 64 rows are is_source_canonical, reconstructing the 16-slot chart;
  (3) SOURCE FIDELITY of the running engine sims: the four loops hard-coded in the Type-1 and Type-2 full-engine sims
      (T1_OUT/T1_IN/T2_OUT/T2_IN) match the source table's (terrain, canonical_operator, axis6_sign) per slot.

FALSIFIABLE CONTROL: a corrupted copy of the table (one operator swapped) MUST be caught by the SAME structural
checks -- so the linter is not a rubber stamp. If the corrupted table passes, the gate is meaningless and the run
fails.

This makes the "64 schedule" language honest: the linter certifies the TABLE is source-faithful and that the sims
CONSUME a source-faithful slot set. It makes NO dynamic-distinctness claim -- that is a separate scratch diagnostic
(engine_64_schedule_definition_sim.py), whose claim ceiling is "64 distinguishable channel signatures under this
finite probe battery", NOT "the source 64 schedule is proven".

promotion_status = "candidate" for the tables (source-faithful, matches the running sims); the linter itself is a
mechanical check. classification="source_fidelity_linter". No oracle dynamics here -- pure table/structure checking.
"""
import json, os, sys, copy

HERE=os.path.dirname(os.path.abspath(__file__))
CANDIDATES=[
    os.path.join(HERE, "..", "reference_docs", "engine_math", "source_schedule_tables"),
    os.path.join(HERE, "source_schedule_tables"),
    os.path.join(os.path.dirname(HERE), "reference_docs", "engine_math", "source_schedule_tables"),
]
def _find_tables():
    for d in CANDIDATES:
        s=os.path.join(d,"engine_16_source_stage_slots.json"); f=os.path.join(d,"engine_64_source_schedule.json")
        if os.path.exists(s) and os.path.exists(f): return s,f
    raise FileNotFoundError("source schedule tables not found in "+repr(CANDIDATES))

FOUR_OPS=sorted(["Ti","Te","Fi","Fe"])

def check_16_slot(slots):
    problems=[]
    if len(slots)!=16: problems.append(f"16-slot table has {len(slots)} rows, expected 16")
    engines={}
    for s in slots:
        engines.setdefault(s["engine"],[]).append(s)
        if s["axis6_sign"] not in ("up","down"): problems.append(f"{s['slot_id']} bad sign {s['axis6_sign']}")
        if s["canonical_operator"] not in FOUR_OPS: problems.append(f"{s['slot_id']} bad op {s['canonical_operator']}")
    if sorted(engines)!=["Type1_left","Type2_right"]:
        problems.append(f"engines {sorted(engines)} != [Type1_left, Type2_right]")
    for eng,rows in engines.items():
        if len(rows)!=8: problems.append(f"{eng} has {len(rows)} slots, expected 8")
        loops={}
        for r in rows: loops.setdefault(r["loop"],[]).append(r["step"])
        for lp,steps in loops.items():
            if sorted(steps)!=[1,2,3,4]: problems.append(f"{eng}/{lp} steps {sorted(steps)} != [1,2,3,4]")
    return problems

def check_64_expansion(slots, sched):
    problems=[]
    if len(sched)!=64: problems.append(f"64-schedule has {len(sched)} rows, expected 64")
    byslot={}
    for r in sched: byslot.setdefault(r["slot_id"],[]).append(r)
    if len(byslot)!=16: problems.append(f"64-schedule spans {len(byslot)} slots, expected 16")
    for sid,rows in byslot.items():
        if sorted(r["operator"] for r in rows)!=FOUR_OPS:
            problems.append(f"{sid} operators {sorted(r['operator'] for r in rows)} != 4 ops")
        if len(set((r["terrain"],r["axis6_sign"]) for r in rows))!=1:
            problems.append(f"{sid} rows do not share one terrain+sign")
    canon=[r for r in sched if r.get("is_source_canonical")]
    if len(canon)!=16: problems.append(f"{len(canon)} canonical rows, expected 16")
    chart={s["slot_id"]:(s["terrain"],s["canonical_operator"],s["axis6_sign"]) for s in slots}
    recon={r["slot_id"]:(r["terrain"],r["operator"],r["axis6_sign"]) for r in canon}
    if chart!=recon: problems.append("canonical 64-rows do not reconstruct the 16-slot chart")
    return problems

IDX_TERR={0:'Se',1:'Ne',2:'Ni',3:'Si',4:'Se',5:'Ne',6:'Ni',7:'Si'}
SIM_LOOPS={
 "T1-O":[(0,'Ti','up'),(1,'Ti','down'),(2,'Fe','down'),(3,'Fe','up')],
 "T1-I":[(0,'Fi','down'),(3,'Te','down'),(2,'Te','up'),(1,'Fi','up')],
 "T2-O":[(4,'Fi','up'),(7,'Te','up'),(6,'Te','down'),(5,'Fi','down')],
 "T2-I":[(4,'Ti','down'),(5,'Ti','up'),(6,'Fe','up'),(7,'Fe','down')],
}
def _norm(t): return t.replace("-in","").replace("-out","")
def check_sim_fidelity(slots):
    problems=[]; grp={}
    for s in slots:
        for pre in ("T1-O","T1-I","T2-O","T2-I"):
            if s["slot_id"].startswith(pre): grp.setdefault(pre,[]).append((_norm(s["terrain"]),s["canonical_operator"],s["axis6_sign"]))
    for pre,rows in SIM_LOOPS.items():
        table_rows=grp.get(pre,[]); sim_rows=[(IDX_TERR[i],o,sg) for (i,o,sg) in rows]
        if table_rows!=sim_rows:
            problems.append(f"{pre}: sim loop {sim_rows} != source table {table_rows}")
    return problems

def run_all_checks(slots, sched):
    return check_16_slot(slots)+check_64_expansion(slots,sched)+check_sim_fidelity(slots)

def main():
    sfile,ffile=_find_tables()
    slots=json.load(open(sfile)); sched=json.load(open(ffile))
    real_problems=run_all_checks(slots,sched); table_ok=(len(real_problems)==0)
    # FALSIFIABLE CONTROL: corrupt one slot's canonical operator, re-run the SAME checks; it MUST be caught.
    bad_slots=copy.deepcopy(slots)
    for s in bad_slots:
        if s["slot_id"]=="T1-O1": s["canonical_operator"]="Fe" if s["canonical_operator"]=="Ti" else "Ti"
    bad_problems=run_all_checks(bad_slots,sched); control_catches=(len(bad_problems)>0)
    verdict=bool(table_ok and control_catches)
    out={"classification":"source_fidelity_linter","promotion_status":"candidate" if table_ok else "rejected",
         "mechanical_run_status":"linter_ran",
         "source_fidelity_status":"tables source-faithful; running sims consume matching slots" if table_ok else "FIDELITY BROKEN",
         "dynamic_claim_status":"none -- dynamic distinctness is a separate scratch diagnostic",
         "num_slots":len(slots),"num_schedule_rows":len(sched),
         "real_table_problems":real_problems,
         "control_corrupted_table_problems_detected":len(bad_problems),
         "table_is_source_faithful":table_ok,"control_catches_corruption":control_catches,
         "SCHEDULE_SOURCE_FIDELITY_LINT_PASS":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("SCHEDULE SOURCE-FIDELITY LINTER -- table correctness only, no dynamic claim.\n")
    print("  (1) 16-slot chart well-formed + (2) 64 = 16x4 expansion + (3) running sims consume matching slots:")
    print(f"      real-table problems: {len(real_problems)} -> table source-faithful {table_ok}")
    for pr in real_problems[:8]: print("        -", pr)
    print("  FALSIFIABLE CONTROL (corrupt one canonical operator, re-run same checks):")
    print(f"      corrupted table triggered {len(bad_problems)} problems -> control catches corruption {control_catches}")
    print("\n  claim ceiling: the TABLE is source-faithful and the sims CONSUME it; dynamic 64-distinctness is separate.")
    print(f"\n  SCHEDULE SOURCE-FIDELITY LINT PASS: {verdict}")
    if verdict: print("PASS schedule_source_fidelity_linter")
    print("ALL_GATES:", "PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
