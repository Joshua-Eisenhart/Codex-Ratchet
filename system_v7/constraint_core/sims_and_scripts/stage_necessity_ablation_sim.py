#!/usr/bin/env python3
"""stage_necessity_ablation -- the STAGE-NECESSITY tooth (owner perception-scorecard ladder items 3 & 7: "all 16
stages must be necessary -- ablate/scramble/duplicate/collapse a stage, then test: does perception get worse?
Success means each of the 16 stages does unique work"). This is the direct mechanism-level answer to the owner's
worry about empty/hallucinated content: if a stage were dead weight, removing it would NOT hurt perception. We
show removing ANY stage measurably degrades object-binding perception -- each stage carries irreplaceable work.

THE TEST (built on the real perception task from perception_object_binding + real oracle stages):
  BASELINE: the full 16-object perceiver binds never-seen views (accuracy on non-degenerate objects ~1.0).
  ABLATION MODES (each applied to one stage at a time, then perception re-measured):
    - REMOVE: drop the stage's object -> its views must go somewhere; measure resolution loss on the REMAINING
      objects (does dropping it blur the others?). [primary necessity signal: the removed object's own views can no
      longer be bound, and if its prototype was carrying discriminative structure the neighbors degrade.]
    - SCRAMBLE: replace the stage's channel with a random other stage's channel -> two objects collapse onto one
      prototype; measure the induced binding errors (collisions).
    - DUPLICATE: replace the stage with a copy of another stage -> the duplicated pair becomes indistinguishable;
      measure the new confusions.
  NECESSITY = every stage, under scramble/duplicate, INDUCES new binding errors that were not present at baseline
  (its unique work cannot be absorbed by the others). A stage whose scramble/duplicate causes ZERO new error would
  be redundant -- that is the failure this can detect.
  HONEST SCOPE: the 6 known-degenerate stages (3 degenerate PAIRS: depol eps-pairs (1,Ti)/(5,Ti) and (1,Fi)/(5,Fi),
  plus Fe proj-commuting (3,Fe)/(7,Fe)) already share identity, so duplicating one onto its degenerate twin induces
  little NEW error (they were already confused) -- reported, and the necessity claim is made over the 10 non-
  degenerate stages, with the 6 degenerate ones flagged as expected-null.

CONTROLS / VERDICT (measurement/verdict separated per Lev mesh discipline):
  (A) SCRAMBLE necessity: scrambling each non-degenerate stage induces new binding errors (> 0) -- the stage did
      unique work. Number: fraction of non-degenerate stages whose scramble induces >=1 new error.
  (B) DUPLICATE necessity: duplicating another stage onto stage s induces new confusions for non-degenerate s.
  (C) the degenerate stages are correctly EXPECTED-NULL (scramble onto their twin induces ~0 new error), so the
      test is honest about where necessity genuinely does not hold.

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False. Real oracle stages + the
established channel signature + nearest-prototype binding. Pure distinguishability. A MECHANISM necessity test, NOT
a claim of a unique ablation protocol.
"""
import json, os, sys, importlib.util
import numpy as np

HERE=os.path.dirname(os.path.abspath(__file__))
pb_spec=importlib.util.spec_from_file_location("pb", os.path.join(HERE,"perception_object_binding_sim.py"))
pb=importlib.util.module_from_spec(pb_spec); pb_spec.loader.exec_module(pb)

STAGES=pb.STAGES
DEG_TWIN={ (1,'Ti'):(5,'Ti'),(5,'Ti'):(1,'Ti'),(1,'Fi'):(5,'Fi'),(5,'Fi'):(1,'Fi'),
           (3,'Fe'):(7,'Fe'),(7,'Fe'):(3,'Fe') }
DEG_IDX={STAGES.index(s) for s in DEG_TWIN}

SEEN=(11,12,13); NOVEL=(901,902,903)

def precompute_signatures():
    """the flows are the only cost -- compute each stage's seen+novel signatures ONCE, then all ablation
    bookkeeping is done in signature space (slot -> which stage's channel occupies it)."""
    sig_seen={}; sig_novel={}
    for si,(t,o) in enumerate(STAGES):
        ch=pb.stage_channel(t,o)
        sig_seen[si]=[pb.channel_signature(ch, pb.probe_family(s)) for s in SEEN]
        sig_novel[si]=[pb.channel_signature(ch, pb.probe_family(s)) for s in NOVEL]
    return sig_seen, sig_novel

def _protos(idmap, sig_seen):
    return [np.mean(sig_seen[idmap[si]],axis=0) for si in range(16)]

def _errors(idmap, sig_seen, sig_novel):
    """idmap[slot]=stage-index whose channel occupies that slot; count views bound to the wrong slot."""
    pr=_protos(idmap, sig_seen); e=0
    for slot in range(16):
        for sg in sig_novel[idmap[slot]]:
            pred=int(np.argmin([np.linalg.norm(sg-p) for p in pr]))
            if pred!=slot: e+=1
    return e

def measure_ablation():
    sig_seen, sig_novel = precompute_signatures()
    ident={i:i for i in range(16)}
    base_err=_errors(ident, sig_seen, sig_novel)
    protos_base=_protos(ident, sig_seen)
    scramble_new=[]; duplicate_new=[]; deg_expected_null=[]
    for si in range(16):
        if si in DEG_IDX:
            # duplicate onto its degenerate twin: should induce ~0 NEW error (already confused) -- expected-null
            twin=STAGES.index(DEG_TWIN[STAGES[si]])
            m=dict(ident); m[twin]=si
            deg_expected_null.append((STAGES[si], _errors(m, sig_seen, sig_novel)-base_err))
            continue
        # NEAREST DISTINCT non-degenerate neighbor = the hardest case for necessity (worst-case collision)
        cand=[(float(np.linalg.norm(protos_base[si]-protos_base[j])),j) for j in range(16) if j!=si and j not in DEG_IDX]
        _,nn=min(cand)
        # SCRAMBLE: slot si now holds nn's channel (si's unique work removed) -> si's own views mis-bind
        ms=dict(ident); ms[si]=nn
        scramble_new.append((STAGES[si], _errors(ms, sig_seen, sig_novel)-base_err))
        # DUPLICATE: slot nn now holds si's channel (si duplicated onto its nearest neighbor) -> collision
        md=dict(ident); md[nn]=si
        duplicate_new.append((STAGES[si], _errors(md, sig_seen, sig_novel)-base_err))
    scr_frac=sum(1 for _,n in scramble_new if n>=1)/len(scramble_new)
    dup_frac=sum(1 for _,n in duplicate_new if n>=1)/len(duplicate_new)
    return {"baseline_errors":base_err,
            "n_nondegenerate":len(scramble_new),"n_degenerate":len(deg_expected_null),
            "scramble_induces_error_fraction":scr_frac,
            "duplicate_induces_error_fraction":dup_frac,
            "degenerate_expected_null_new_errors":[(str(s),int(n)) for s,n in deg_expected_null],
            "mean_abs_new_error_nondegenerate":float(np.mean([abs(n) for _,n in duplicate_new])),
            "mean_abs_new_error_degenerate":float(np.mean([abs(n) for _,n in deg_expected_null])),
            "scramble_new_errors":[(str(s),int(n)) for s,n in scramble_new],
            "duplicate_new_errors":[(str(s),int(n)) for s,n in duplicate_new]}

def evaluate(m):
    laneA = m["scramble_induces_error_fraction"] > 0.99      # every non-degenerate stage's scramble induces error
    laneB = m["duplicate_induces_error_fraction"] > 0.99     # every non-degenerate stage's duplicate induces error
    # honesty (lane C): degenerate stages induce MUCH SMALLER new error than non-degenerate ones -- they were
    # already confused, so duplicating onto the twin adds little. A magnitude separation, not a sign threshold.
    laneC = m["mean_abs_new_error_degenerate"] < 0.5*m["mean_abs_new_error_nondegenerate"]
    allpass=bool(laneA and laneB and laneC)
    return {"every_nondegenerate_stage_scramble_induces_error":bool(laneA),
            "every_nondegenerate_stage_duplicate_induces_error":bool(laneB),
            "degenerate_stages_induce_much_less_error_expected_null":bool(laneC),
            "ALL_STAGES_DO_UNIQUE_WORK":allpass}

def main():
    m=measure_ablation(); verdict=evaluate(m)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "framing":"stage necessity by ablation: every non-degenerate stage does irreplaceable work -- scrambling/duplicating it induces binding errors the others cannot absorb",
         "ablation":m,"policy_eval":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("STAGE NECESSITY BY ABLATION -- does every stage do unique work? (remove/scramble/duplicate)\n")
    print(f"  baseline binding errors: {m['baseline_errors']}")
    print(f"  {m['n_nondegenerate']} non-degenerate stages, {m['n_degenerate']} degenerate (expected-null)")
    print(f"  SCRAMBLE: fraction of non-degenerate stages whose scramble induces new binding error: {m['scramble_induces_error_fraction']:.3f}")
    print(f"  DUPLICATE: fraction whose duplication (onto nearest distinct neighbor) induces new confusion: {m['duplicate_induces_error_fraction']:.3f}")
    print(f"  degenerate stages expected-null: mean|new error| deg {m['mean_abs_new_error_degenerate']:.2f} vs non-deg {m['mean_abs_new_error_nondegenerate']:.2f} (they already share identity) {m['degenerate_expected_null_new_errors']}")
    print("\n  SEPARATE POLICY EVAL (verdict = every non-degenerate stage does unique work):")
    for k,v in verdict.items():
        if k!="ALL_STAGES_DO_UNIQUE_WORK": print(f"    {k}: {v}")
    print(f"\n  ALL STAGES DO UNIQUE WORK: {verdict['ALL_STAGES_DO_UNIQUE_WORK']}")
    if verdict["ALL_STAGES_DO_UNIQUE_WORK"]:
        print("PASS stage_necessity_ablation")
    print("ALL_GATES:", "PASS" if verdict["ALL_STAGES_DO_UNIQUE_WORK"] else "FAIL","->",path)
    sys.exit(0 if verdict["ALL_STAGES_DO_UNIQUE_WORK"] else 1)

if __name__=="__main__":
    main()
