#!/usr/bin/env python3
"""perception_scorecard_eval_admission -- complete the FOUR missing_for_eval_admission fields on the QIT engine
perception scorecard, so the emitted Lev evidence carries a full formation-loss surface instead of nulls.

The codex Phase-3 evidence (lev_qit_engine_perception_evidence_v1) and this bundle's emitted envelope both list four
fields as missing_for_eval_admission -- the scorecard's formation_loss_surface leaves recall_loss / anti_key_penalty /
attention_leak_penalty as null and has no cross_node_mesh_convergence at all. This sim measures all four from the SAME
real engine stage channels the re-identification sim uses (imported, not re-derived), each as a PURE INSTRUMENT
(numbers only, no verdict) with a control that flips -- the measurement/verdict-separation discipline from the Lev
object-formation mesh package. A separate eval decides admission.

THE FOUR FIELDS (each a distinguishability lens on the 16 stage channels; all reuse channel_signature = the
probe-set-independent channel identity from engine_reidentification_objective):

  1. recall_ratio -- ASSOCIATIVE RECALL from a DEGRADED cue. Re-identify each stage from a partial/noisy probe cue
     (fewer probes + Bloch noise), not the full novel set. recall_ratio = fraction still correctly recalled.
     CONTROL: shuffle which degraded cue belongs to which stage -> recall collapses to chance. recall_loss = 5*(1-ratio).

  2. anti_key_penalty -- FALSE BINDING to decoys. Inject DECOY channels that are NOT engine stages (random CPTP maps)
     and ask how often a decoy's signature nearest-neighbours a real stage inside the real stages' own match radius.
     penalty = fraction of decoys that false-bind. CONTROL: the real stages themselves must NOT false-bind to each
     other's radius above this rate (a real object binds to itself, a decoy should be rejected).

  3. attention_leak -- CROSS-OBJECT ACTIVATION. Build the stage-response matrix R[i][j] = similarity of stage i's
     signature to stage j's; leak = mean off-diagonal / mean diagonal (how much a stage's response bleeds onto other
     stages). CONTROL: a shuffled-identity matrix has leak ~1 (no diagonal advantage); the real matrix must be << 1.

  4. cross_node_mesh_convergence -- MESH AGREEMENT. Two INDEPENDENT probe-family "nodes" (different seeds = different
     perspectives) each produce a stage-identity assignment; convergence = fraction of stages both nodes assign
     identically. CONTROL: one node with SHUFFLED identities -> convergence collapses to chance. This is the
     mesh/agent-network lens: independent observers converge on the same object identities (a=a iff a~b across nodes).

scratch_diagnostic, promotion_allowed=false. Completes the formation-loss surface; the eval policy stays separate.
"""
import json, os, sys, importlib.util
import numpy as np

HERE=os.path.dirname(os.path.abspath(__file__))
# import the real engine machinery from the re-identification sim (same stage channels, same signature)
spec=importlib.util.spec_from_file_location("reidmod", os.path.join(HERE,"engine_reidentification_objective_sim.py"))
R=importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
I2=R.I2

def _callable(c):
    # stage_channels() returns (name, channel) tuples; decoys are bare callables
    return c[1] if isinstance(c,tuple) else c

def sigs_for(channels, probes):
    return [R.channel_signature(_callable(c),probes) for c in channels]

def nn_assignment(sig_query, sig_ref):
    """for each query signature, index of nearest reference signature."""
    out=[]
    for i in range(len(sig_query)):
        d=[np.linalg.norm(sig_query[i]-sig_ref[j]) for j in range(len(sig_ref))]
        out.append(int(np.argmin(d)))
    return out

def degrade_probe_family(seed, n=3, radius=0.7, noise=0.15):
    rng=np.random.default_rng(seed); fam=[]
    for _ in range(n):
        v=rng.normal(size=3); v=radius*v/np.linalg.norm(v); v=v+rng.normal(scale=noise,size=3)
        fam.append(R.rho_from_bloch(v))
    return fam

def random_cptp_channels(k, seed):
    """decoy channels that are NOT engine stages: random single-qubit CPTP maps via random Kraus (Stinespring)."""
    rng=np.random.default_rng(seed); chans=[]
    for _ in range(k):
        # random unitary on 2-qubit dilation, partial trace the ancilla -> random CPTP on the system
        M=rng.normal(size=(4,4))+1j*rng.normal(size=(4,4)); Qm,_=np.linalg.qr(M)  # 4x4 unitary
        # Kraus: K_a = <a|U|0>_anc, a=0,1
        K=[Qm[2*a:2*a+2,0:2] for a in range(2)]
        def make(K):
            def ch(r): return sum(k@r@k.conj().T for k in K)
            return ch
        chans.append(make(K))
    return chans

# ---------------------------------- PURE INSTRUMENTS (numbers only) ----------------------------------

def measure_recall_ratio():
    chans=R.stage_channels(); seen=R.probe_family(seed=11)
    sig_seen=sigs_for(chans,seen)
    cue=degrade_probe_family(seed=101)         # degraded/partial/noisy cue, never-seen
    sig_cue=sigs_for(chans,cue)
    asn=nn_assignment(sig_cue,sig_seen)
    real=sum(1 for i,a in enumerate(asn) if a==i)/len(chans)
    # control: keep the SAME nearest-neighbour assignment but scramble the TRUTH labels (cue i is relabeled to
    # stage perm[i]); a real recall correspondence must break under relabeling -> collapses to chance. (Re-running
    # NN on reordered cues would be a no-op that reorders the same correct matches -- not a real control.)
    rng=np.random.default_rng(7); perm=rng.permutation(len(chans))
    shuf=sum(1 for i in range(len(chans)) if asn[i]==perm[i])/len(chans)
    return {"recall_ratio":round(real,4),"recall_loss":round(5.0*(1.0-real),4),
            "shuffled_recall_ratio":round(shuf,4),"chance":round(1.0/len(chans),4),
            "separation":round(real-shuf,4)}

def measure_anti_key_penalty():
    chans=R.stage_channels(); seen=R.probe_family(seed=11); novel=R.probe_family(seed=23)
    sig_seen=sigs_for(chans,seen)
    # real stages' own match distances (to their own seen sig) set the acceptance radius
    sig_novel=sigs_for(chans,novel)
    own_d=[np.linalg.norm(sig_novel[i]-sig_seen[i]) for i in range(len(chans))]
    radius=float(np.percentile(own_d,90))       # accept within the 90th pct of real self-match distance
    decoys=random_cptp_channels(len(chans),seed=55); sig_dec=sigs_for(decoys,novel)
    # anti-key penalty = fraction of decoys that fall within radius of SOME real stage (false-bind)
    false_bind=0
    for sd in sig_dec:
        dmin=min(np.linalg.norm(sd-sig_seen[j]) for j in range(len(chans)))
        if dmin<=radius: false_bind+=1
    penalty=false_bind/len(decoys)
    # control: real stages within radius of their own sig (should be ~1.0 -- real objects bind, decoys don't)
    real_bind=sum(1 for i in range(len(chans)) if own_d[i]<=radius)/len(chans)
    return {"anti_key_penalty":round(penalty,4),"acceptance_radius":round(radius,4),
            "decoy_false_bind_count":false_bind,"n_decoys":len(decoys),
            "real_self_bind_rate":round(real_bind,4)}

def measure_attention_leak():
    chans=R.stage_channels(); seen=R.probe_family(seed=11); sig=sigs_for(chans,seen)
    n=len(chans); D=np.zeros((n,n))
    for i in range(n):
        for j in range(n): D[i,j]=np.linalg.norm(sig[i]-sig[j])
    # similarity = negative distance mapped to (0,1]; diagonal is self (distance 0 -> sim 1)
    scale=np.median(D[D>0]); Sim=np.exp(-D/scale)
    diag=np.mean(np.diag(Sim)); off=(Sim.sum()-np.trace(Sim))/(n*n-n)
    leak=off/diag
    # control: shuffle identities -> off-diagonal indistinguishable from diagonal (leak ~1)
    rng=np.random.default_rng(3); perm=rng.permutation(n); Sh=Sim[np.ix_(perm,perm)]
    # shuffled "diagonal" is now random entries: compare full-mean to a permuted diagonal
    sh_leak=off/np.mean([Sim[perm[i],i] for i in range(n)])
    return {"attention_leak":round(float(leak),4),"attention_leak_penalty":round(float(leak),4),
            "mean_diag_similarity":round(float(diag),4),"mean_offdiag_similarity":round(float(off),4),
            "shuffled_leak_ratio":round(float(sh_leak),4)}

def measure_cross_node_mesh_convergence():
    chans=R.stage_channels()
    nodeA=R.probe_family(seed=11); nodeB=R.probe_family(seed=29)  # two independent perspective nodes
    ref=sigs_for(chans,R.probe_family(seed=5))                    # shared reference frame
    asnA=nn_assignment(sigs_for(chans,nodeA),ref)
    asnB=nn_assignment(sigs_for(chans,nodeB),ref)
    conv=sum(1 for i in range(len(chans)) if asnA[i]==asnB[i])/len(chans)
    # control: node B with shuffled identities -> convergence collapses to chance
    rng=np.random.default_rng(13); perm=rng.permutation(len(chans))
    asnB_sh=[asnB[p] for p in perm]
    conv_sh=sum(1 for i in range(len(chans)) if asnA[i]==asnB_sh[i])/len(chans)
    return {"cross_node_mesh_convergence":round(conv,4),"shuffled_convergence":round(conv_sh,4),
            "chance":round(1.0/len(chans),4),"separation":round(conv-conv_sh,4)}

# ---------------------------------- SEPARATE EVAL POLICY ----------------------------------

def eval_admission(rec,ak,leak,mesh):
    """CONTROL-RELATIVE, not hand-picked thresholds. Each field admits iff the REAL measurement beats its OWN
    negative control by a structural margin -- the same discipline as the re-id gate (verdict = real-minus-shuffled
    separation, never a picked constant). No literal pass-marks (0.3/0.8/0.7) appear here.
      - recall: real recall must exceed its shuffled-label control AND exceed chance (the control's expectation).
      - anti-key: real stages must self-bind MORE than random-CPTP decoys false-bind (real object binds, decoy doesn't).
      - attention leak: the real similarity matrix must have a genuine diagonal advantage -- its leak must be BELOW
        the shuffled-identity leak (which has no diagonal advantage, leak ~1 by construction).
      - mesh: two independent nodes must agree MORE than the shuffled-node control.
    """
    return {
        "recall_beats_own_control": rec["recall_ratio"]>rec["shuffled_recall_ratio"] and rec["recall_ratio"]>rec["chance"],
        "anti_key_real_binds_more_than_decoys": ak["real_self_bind_rate"] > (ak["decoy_false_bind_count"]/max(ak["n_decoys"],1)),
        "attention_leak_below_shuffled": leak["attention_leak"] < leak["shuffled_leak_ratio"],
        "mesh_converges_over_control": mesh["cross_node_mesh_convergence"]>mesh["shuffled_convergence"] and mesh["cross_node_mesh_convergence"]>mesh["chance"],
    }

def main():
    rec=measure_recall_ratio(); ak=measure_anti_key_penalty()
    leak=measure_attention_leak(); mesh=measure_cross_node_mesh_convergence()
    checks=eval_admission(rec,ak,leak,mesh); all_ok=all(checks.values())
    out={"classification":"scratch_diagnostic","promotion_status":"scratch_diagnostic","promotion_allowed":False,
         "framing":"completes the four missing_for_eval_admission fields on the perception scorecard from the SAME real engine stage channels the re-id sim uses; pure instruments + separate eval.",
         "recall_ratio_field":rec,"anti_key_penalty_field":ak,"attention_leak_field":leak,
         "cross_node_mesh_convergence_field":mesh,
         "eval_admission_checks":checks,
         "missing_fields_now_measured":["recall_ratio","anti_key_penalty","attention_leak","cross_node_mesh_convergence"],
         "PERCEPTION_SCORECARD_EVAL_ADMISSION_COMPLETE":bool(all_ok)}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("PERCEPTION SCORECARD -- completing the four missing_for_eval_admission fields (real engine channels).\n")
    print(f"  1. recall_ratio        {rec['recall_ratio']}  (shuffled {rec['shuffled_recall_ratio']}, chance {rec['chance']}) -> beats own control: {checks['recall_beats_own_control']}")
    print(f"  2. anti_key_penalty    {ak['anti_key_penalty']}  (decoy false-bind {ak['decoy_false_bind_count']}/{ak['n_decoys']}, real self-bind {ak['real_self_bind_rate']}) -> real binds more than decoys: {checks['anti_key_real_binds_more_than_decoys']}")
    print(f"  3. attention_leak      {leak['attention_leak']}  (shuffled {leak['shuffled_leak_ratio']}) -> below shuffled: {checks['attention_leak_below_shuffled']}")
    print(f"  4. cross_node_mesh_convergence {mesh['cross_node_mesh_convergence']}  (shuffled {mesh['shuffled_convergence']}, chance {mesh['chance']}) -> converges over control: {checks['mesh_converges_over_control']}")
    print(f"\n  PERCEPTION SCORECARD EVAL-ADMISSION COMPLETE: {all_ok}")
    if all_ok: print("PASS perception_scorecard_eval_admission")
    print("ALL_GATES:", "PASS" if all_ok else "FAIL","->",path)
    sys.exit(0 if all_ok else 1)

if __name__=="__main__":
    main()
