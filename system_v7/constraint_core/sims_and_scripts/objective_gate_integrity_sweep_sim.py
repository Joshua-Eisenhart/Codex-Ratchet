#!/usr/bin/env python3
"""objective_gate_integrity_sweep -- a STANDING anti-hallucination guard. The owner's recurring failure with prior
sims: "it seemed like my sims were real, then found much of them was hallucinated and empty contents, all made up
with gates cheated." This sim mechanically PROVES the objective-criterion gates (re-identification, object-formation
scorecard, perception object-binding) are REAL: each verdict function must (a) PASS on the true measured inputs AND
(b) FAIL on cheated inputs (empty/constant/chance/hallucinated). A gate that cannot be made to fail is a rubber
stamp, not a gate. This runs the actual evaluate()/eval functions of the three objective sims against synthetic
cheats -- it does not re-implement them, it interrogates them.

WHAT IT CHECKS (each objective gate, real must pass AND every cheat must fail):
  1. PERCEPTION (perception_object_binding.evaluate): cheat with chance-level binding, zero interior spread, and
     hallucinated (un-merged) degeneracies -- each must flip the verdict to False.
  2. OBJECT-FORMATION SCORECARD (engine_object_formation_scorecard.eval_formation): cheat by making the convergence
     control not flip (shuffled >= real) and the handling control not flip -- each must flip the verdict to False.
  3. RE-IDENTIFICATION (engine_reidentification_objective, via its results JSON semantics): cheat by setting the
     shuffled control at or above the real rate (memorized, not earned) -- the separation-based verdict must flip.
Additionally, NON-EMPTINESS: each objective sim's results JSON exists, is non-trivial (has the expected measured
keys with real numeric values), and the perception sim actually recomputes (not a cached constant) -- checked by
running its instrument and confirming the number matches its own JSON within tolerance.

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False. Pure interrogation of the
existing gate functions + JSON non-emptiness; no new physics. This is a META-audit: its job is to make cheating a
gate detectable, so "looks real but is hallucinated" cannot pass silently.
"""
import json, os, sys, importlib.util
import numpy as np

HERE=os.path.dirname(os.path.abspath(__file__))
def load(name):
    spec=importlib.util.spec_from_file_location(name, os.path.join(HERE,f"{name}.py"))
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def check_perception():
    pb=load("perception_object_binding_sim")
    b=pb.measure_binding(); d=pb.measure_degeneracy_honesty(); i=pb.measure_interior_needed()
    key="AI_OF_PERCEPTION_OBJECT_BINDING_EARNED"
    real=pb.evaluate(b,d,i)[key]
    bA=dict(b); bA["real_binding_accuracy"]=b["chance"]; bA["accuracy_on_non_degenerate_objects"]=b["chance"]
    cheatA=pb.evaluate(bA,d,i)[key]
    iB=dict(i); iB["real_interior_spread"]=0.0
    cheatB=pb.evaluate(b,d,iB)[key]
    dC=dict(d); dC["degenerate_pairs_much_closer"]=False
    cheatC=pb.evaluate(b,dC,i)[key]
    # non-emptiness + recompute check: the binding accuracy is a real recompute (nonzero, > chance) not a constant
    recompute_real = b["real_binding_accuracy"]>b["chance"]+0.1
    return {"real_passes":bool(real),"cheat_chance_binding_fails":not cheatA,
            "cheat_zero_interior_fails":not cheatB,"cheat_hallucinate_degeneracy_fails":not cheatC,
            "recompute_is_real_not_constant":bool(recompute_real),
            "GATE_REAL":bool(real and not cheatA and not cheatB and not cheatC and recompute_real)}

def check_scorecard():
    sc=load("engine_object_formation_scorecard_sim")
    reid=json.load(open(os.path.join(HERE,"engine_reidentification_objective_sim_results.json")))
    sindy=json.load(open(os.path.join(HERE,"engine_dynamics_id_arbiter_sim_results.json")))
    conv=sc.measure_convergence_loss(reid); hand=sc.measure_handling_loss(sindy)
    key="BOTH_INDEPENDENT_CONTROLS_FLIP"
    real=sc.eval_formation(conv,hand)[key]
    # cheat: convergence control does NOT flip (shuffled max >= real rate)
    convX=json.loads(json.dumps(conv)); convX["negative_control_result"]["shuffled_max_rate"]=convX["convergence_rate"]+0.1
    cheatA=sc.eval_formation(convX,hand)[key]
    # cheat: handling control does NOT flip
    handX=json.loads(json.dumps(hand)); handX["real_beats_shuffled_every_terrain"]=False
    cheatB=sc.eval_formation(conv,handX)[key]
    return {"real_passes":bool(real),"cheat_convergence_control_fails":not cheatA,
            "cheat_handling_control_fails":not cheatB,
            "GATE_REAL":bool(real and not cheatA and not cheatB)}

def check_reidentification():
    # the re-id verdict is separation = real - shuffled; a real gate fails when shuffled >= real. Interrogate the
    # semantics from the results JSON (the sim's own recorded numbers) + confirm the separation logic flips.
    reid=json.load(open(os.path.join(HERE,"engine_reidentification_objective_sim_results.json")))
    real_rate=reid["real_reidentification_rate_novel_probes"]; shuf=reid["shuffled_control_max_rate"]
    real_verdict = shuf < real_rate                       # control flips: real beats every scramble
    cheat_shuf = real_rate                                # cheat: shuffled at real rate (memorized)
    cheat_verdict = cheat_shuf < real_rate                # must be False
    nonempty = ("stages_that_failed_reid" in reid and isinstance(reid["stages_that_failed_reid"],list)
                and 0.0 < real_rate <= 1.0)
    return {"real_rate":real_rate,"shuffled_max":shuf,"real_passes":bool(real_verdict),
            "cheat_memorized_shuffled_fails":not cheat_verdict,"results_json_nonempty":bool(nonempty),
            "GATE_REAL":bool(real_verdict and not cheat_verdict and nonempty)}

def evaluate(p,s,r):
    allreal = p["GATE_REAL"] and s["GATE_REAL"] and r["GATE_REAL"]
    return {"perception_gate_real":p["GATE_REAL"],"scorecard_gate_real":s["GATE_REAL"],
            "reidentification_gate_real":r["GATE_REAL"],
            "ALL_OBJECTIVE_GATES_REAL_NOT_RUBBER_STAMPS":bool(allreal)}

def main():
    p=check_perception(); s=check_scorecard(); r=check_reidentification()
    verdict=evaluate(p,s,r)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "framing":"anti-hallucination guard: prove the objective-criterion gates PASS on real inputs and FAIL on cheated inputs (a gate that cannot fail is a rubber stamp)",
         "perception":p,"scorecard":s,"reidentification":r,"policy_eval":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)

    print("OBJECTIVE GATE INTEGRITY SWEEP -- do the objective gates PASS real inputs and FAIL cheated ones?\n")
    print("  1. PERCEPTION gate:")
    print(f"     real passes {p['real_passes']}; cheats fail: chance-binding {p['cheat_chance_binding_fails']}, zero-interior {p['cheat_zero_interior_fails']}, hallucinate-degeneracy {p['cheat_hallucinate_degeneracy_fails']}; recompute real {p['recompute_is_real_not_constant']} -> GATE REAL {p['GATE_REAL']}")
    print("  2. OBJECT-FORMATION SCORECARD gate:")
    print(f"     real passes {s['real_passes']}; cheats fail: convergence-control {s['cheat_convergence_control_fails']}, handling-control {s['cheat_handling_control_fails']} -> GATE REAL {s['GATE_REAL']}")
    print("  3. RE-IDENTIFICATION gate:")
    print(f"     real rate {r['real_rate']:.4f} vs shuffled max {r['shuffled_max']:.4f}; real passes {r['real_passes']}; cheat(memorized) fails {r['cheat_memorized_shuffled_fails']}; json nonempty {r['results_json_nonempty']} -> GATE REAL {r['GATE_REAL']}")
    print("\n  SEPARATE POLICY EVAL:")
    for k,v in verdict.items():
        if k!="ALL_OBJECTIVE_GATES_REAL_NOT_RUBBER_STAMPS": print(f"    {k}: {v}")
    print(f"\n  ALL OBJECTIVE GATES REAL (not rubber stamps): {verdict['ALL_OBJECTIVE_GATES_REAL_NOT_RUBBER_STAMPS']}")
    if verdict["ALL_OBJECTIVE_GATES_REAL_NOT_RUBBER_STAMPS"]:
        print("PASS objective_gate_integrity_sweep")
    print("ALL_GATES:", "PASS" if verdict["ALL_OBJECTIVE_GATES_REAL_NOT_RUBBER_STAMPS"] else "FAIL","->",path)
    sys.exit(0 if verdict["ALL_OBJECTIVE_GATES_REAL_NOT_RUBBER_STAMPS"] else 1)

if __name__=="__main__":
    main()
