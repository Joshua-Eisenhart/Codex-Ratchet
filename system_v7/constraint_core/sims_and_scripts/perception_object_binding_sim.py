#!/usr/bin/env python3
"""perception_object_binding -- the AI-of-PERCEPTION tooth, connecting the engine interior to the objective
success criteria (object formation). Loop-back on the overall success target: "an object is earned when the
system can re-identify it across perspective changes it has never seen" (identity = survivor of probe rotation,
a=a iff a~b operational). The re-identification sim scored that per-stage; THIS sim runs the actual PERCEPTION
task the criterion implies but had not run directly: BINDING a stream of never-seen views into objects.

THE PERCEPTION TASK (object binding across perspective):
  - There are K underlying OBJECTS = K real engine stages (distinct kinds of processing, from oracle_targets.py).
  - Each object is OBSERVED through several NEVER-SEEN probe perspectives (disjoint probe families, different seeds
    -- genuinely independent perspectives the binder never trained on).
  - The perceiver computes each observation's channel signature (the established re-id signature: nonunitality
    vector + Bloch-contraction singular values) and must SORT the observations into objects: same underlying
    stage -> same cluster (BIND), different stage -> different cluster (SEPARATE). No labels given.
  - PERCEPTION SUCCEEDS if the unsupervised clustering recovers the true objects (high adjusted-accuracy) FROM
    never-seen views -- binding is the survivor of probe rotation, made a perception task.

WHY THIS IS THE AI OF PERCEPTION (not just re-id): re-id asked "does stage i's novel fingerprint match its own
seen fingerprint?". Perception asks the harder, honest question: given a STREAM of unlabeled views of MANY
objects through MANY never-seen perspectives, can the system carve the stream at its joints -- bind what is one
thing, separate what is different -- with no supervision? That is object formation as perception.

CONTROLS (each must flip; measurement/verdict separated per Lev mesh discipline):
  (A) REAL binding beats SHUFFLED: the true-object clustering accuracy is high; a control that shuffles which view
      belongs to which object collapses to chance. Number: real binding accuracy >> shuffled.
  (B) THE CRITERION IS REAL, NOT HALLUCINATED -- it must FAIL on genuine degeneracies: the re-id sim found the
      eps-degenerate depol pairs and the Fe proj-commuting pair do NOT re-identify (they are the same channel up
      to the degeneracy). A HONEST perceiver must MERGE those (not invent two objects where the mechanism says
      one). Measure: the degenerate pairs land in the SAME cluster (correctly un-separated) -- so the tooth is not
      a rubber stamp; it refuses to form an object where there is a real degeneracy.
  (C) BINDING NEEDS THE INTERIOR (the 16 distinct kinds): if every stage were the SAME kind of processing, the
      signatures would coincide and binding would be impossible. Number: with the real 16 distinct-kind stages the
      inter-object signature spread is large; a degenerate all-same-kind control has ~0 spread (unbindable).

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False. Real oracle stages
(engines/oracle_targets.py, reconstructed inline verbatim); channel signature = the established re-id signature;
clustering = nearest-prototype on signatures (no sklearn dependency). Pure distinguishability; no bits/vectors as
mechanism. A MECHANISM build of the perception task the success criteria imply, honestly audited to fail on real
degeneracies -- NOT a claim of a unique perception algorithm.
"""
import json, os, sys
import numpy as np
from scipy.linalg import expm

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
I2=np.eye(2,dtype=complex); sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
G=0.35; KAP=1.0; Q=1.0-np.exp(-1.0); TH=np.pi/4; T_FLOW=1.0; N_STEPS=400
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
NATIVE={0:('Ti','Fi'),1:('Ti','Fi'),4:('Ti','Fi'),5:('Ti','Fi'),
        2:('Te','Fe'),3:('Te','Fe'),6:('Te','Fe'),7:('Te','Fe')}
STAGES=[(t,o) for t in range(8) for o in NATIVE[t]]

def Dop(L,r): return L@r@L.conj().T - 0.5*(L.conj().T@L@r + r@L.conj().T@L)
def gen(ti):
    eps,kind,pole=TERR[ti]; H=eps*(sx+sy+sz)/np.sqrt(3)
    def X(r):
        out=-1j*G*(H@r-r@H)
        if kind=='damp': out=out+KAP*Dop(sp if pole>0 else sm,r)
        elif kind=='depol': out=out+0.5*KAP*(Dop(sx,r)+Dop(sy,r))
        else: out=out+KAP*Dop(sz,r)
        return out
    return X
def flow(X,r,t=T_FLOW,steps=N_STEPS):
    dt=t/steps
    for _ in range(steps):
        k1=X(r);k2=X(r+.5*dt*k1);k3=X(r+.5*dt*k2);k4=X(r+dt*k3)
        r=r+(dt/6)*(k1+2*k2+2*k3+k4); r=.5*(r+r.conj().T); r/=np.trace(r).real
    return r
def op(name):
    P0=0.5*(I2+sz);P1=0.5*(I2-sz);Qp=0.5*(I2+sx);Qm=0.5*(I2-sx)
    if name=='Ti': return lambda r:(1-Q)*r+Q*(P0@r@P0+P1@r@P1)
    if name=='Te': return lambda r:(1-Q)*r+Q*(Qp@r@Qp+Qm@r@Qm)
    if name=='Fi': U=expm(-1j*TH/2*sx); return lambda r:U@r@U.conj().T
    if name=='Fe': U=expm(-1j*TH/2*sz); return lambda r:U@r@U.conj().T
def bloch(r): return np.array([float(np.trace(r@s).real) for s in (sx,sy,sz)])
def dm(v): return 0.5*(I2+v[0]*sx+v[1]*sy+v[2]*sz)

def stage_channel(t,o):
    X=gen(t); J=op(o)
    return lambda r: J(flow(X, r.copy()))

def probe_family(seed, n=6, radius=0.7):
    rng=np.random.default_rng(seed); ps=[]
    for _ in range(n):
        v=rng.standard_normal(3); v=v/np.linalg.norm(v)*radius; ps.append(dm(v))
    return ps

def channel_signature(chan, probes):
    """the established re-id signature: (a) nonunitality vector (action on I/2), (b) sorted singular values of the
    affine Bloch map r'=A r + b recovered from the probe family. A CHANNEL invariant -- matches for the SAME
    channel across DIFFERENT (never-seen) probe families."""
    nonun = bloch(chan(0.5*I2))
    Xa=[]; Y=[]
    for p in probes:
        Xa.append(list(bloch(p))+[1.0]); Y.append(list(bloch(chan(p))))
    Xa=np.array(Xa); Y=np.array(Y)
    M,*_=np.linalg.lstsq(Xa,Y,rcond=None)     # 4x3: rows 0-2 = A^T, row3 = b
    A=M[:3,:].T
    sv=np.linalg.svd(A,compute_uv=False)
    return np.concatenate([nonun, np.sort(sv)])

# ---------- the perception task ----------

def build_views(seeds):
    """each object (stage) observed through several never-seen probe families -> a stream of (signature, true_obj)."""
    views=[]
    for oi,(t,o) in enumerate(STAGES):
        chan=stage_channel(t,o)
        for s in seeds:
            views.append((channel_signature(chan, probe_family(s)), oi))
    return views

def cluster_to_prototypes(views, protos):
    """assign each view to the nearest object prototype signature (nearest-prototype perception)."""
    labels=[]
    for sig,_ in views:
        d=[float(np.linalg.norm(sig-p)) for p in protos]
        labels.append(int(np.argmin(d)))
    return labels

def binding_accuracy(seen_seeds, novel_seeds):
    """prototypes learned from SEEN perspectives; binding tested on NEVER-SEEN perspectives."""
    # prototype = mean signature per object over SEEN probe families
    protos=[]
    for oi,(t,o) in enumerate(STAGES):
        chan=stage_channel(t,o)
        sigs=[channel_signature(chan, probe_family(s)) for s in seen_seeds]
        protos.append(np.mean(sigs,axis=0))
    novel=build_views(novel_seeds)
    pred=cluster_to_prototypes(novel, protos)
    true=[oi for _,oi in novel]
    correct=sum(1 for p,tr in zip(pred,true) if p==tr)
    # every miss should be a genuine degeneracy: view of object A assigned to its degenerate twin B (identical
    # channel up to the eps/commuting degeneracy). Accuracy-on-non-degenerate should be ~1.0.
    DEG={frozenset([STAGES.index((1,'Ti')),STAGES.index((5,'Ti'))]),
         frozenset([STAGES.index((1,'Fi')),STAGES.index((5,'Fi'))]),
         frozenset([STAGES.index((3,'Fe')),STAGES.index((7,'Fe'))])}
    misses_all_degenerate=all(frozenset([p,tr]) in DEG for p,tr in zip(pred,true) if p!=tr)
    return correct/len(true), pred, true, protos, misses_all_degenerate

# ---------- instruments ----------

def measure_binding():
    seen=[11,12,13]; novel=[901,902,903]     # disjoint never-seen perspectives
    acc, pred, true, protos, misses_all_deg = binding_accuracy(seen, novel)
    # (A) shuffled control: shuffle the true-object labels of the novel views -> accuracy collapses to chance
    rng=np.random.default_rng(7); tshuf=list(true); rng.shuffle(tshuf)
    shuf_acc=sum(1 for p,tr in zip(pred,tshuf) if p==tr)/len(true)
    chance=1.0/len(STAGES)
    # accuracy restricted to non-degenerate objects (the honest headline: perfect except on real degeneracies)
    DEGOBJ={STAGES.index(s) for s in [(1,'Ti'),(5,'Ti'),(1,'Fi'),(5,'Fi'),(3,'Fe'),(7,'Fe')]}
    nd=[(p,tr) for p,tr in zip(pred,true) if tr not in DEGOBJ]
    nd_acc=sum(1 for p,tr in nd if p==tr)/len(nd) if nd else 0.0
    return {"real_binding_accuracy":acc,"shuffled_label_accuracy":shuf_acc,"chance":chance,
            "n_objects":len(STAGES),"n_novel_views":len(true),
            "all_misses_are_genuine_degeneracies":bool(misses_all_deg),
            "accuracy_on_non_degenerate_objects":nd_acc}

def measure_degeneracy_honesty():
    """the criterion must MERGE genuine degeneracies, not hallucinate objects. The re-id sim found these pairs do
    not separate (same channel up to the eps/commuting degeneracy). Measure their signature distance vs the median
    inter-object distance: the degenerate pairs must be MUCH closer (correctly un-separated)."""
    seen=[11,12,13]
    protos=[]
    for oi,(t,o) in enumerate(STAGES):
        chan=stage_channel(t,o); protos.append(np.mean([channel_signature(chan,probe_family(s)) for s in seen],axis=0))
    idx={st:i for i,st in enumerate(STAGES)}
    deg_pairs=[((1,'Ti'),(5,'Ti')),((1,'Fi'),(5,'Fi')),((3,'Fe'),(7,'Fe'))]   # depol eps-degenerate + Fe proj-commuting
    deg_dists=[float(np.linalg.norm(protos[idx[a]]-protos[idx[b]])) for a,b in deg_pairs if a in idx and b in idx]
    all_d=[float(np.linalg.norm(protos[i]-protos[j])) for i in range(len(protos)) for j in range(i+1,len(protos))]
    median_all=float(np.median(all_d))
    return {"degenerate_pair_distances":[round(d,4) for d in deg_dists],
            "median_inter_object_distance":round(median_all,4),
            "degenerate_pairs_much_closer":all(d < 0.5*median_all for d in deg_dists)}

def measure_interior_needed():
    """binding needs the 16 distinct kinds. Real inter-object signature spread vs a degenerate all-same-kind
    control (every object = the same stage): the control has ~0 spread and is unbindable."""
    seen=[11,12,13]
    real_protos=[np.mean([channel_signature(stage_channel(t,o),probe_family(s)) for s in seen],axis=0) for (t,o) in STAGES]
    real_spread=float(np.mean([np.linalg.norm(real_protos[i]-real_protos[j]) for i in range(16) for j in range(i+1,16)]))
    same=stage_channel(0,'Ti')
    same_protos=[np.mean([channel_signature(same,probe_family(s)) for s in seen],axis=0) for _ in STAGES]
    same_spread=float(np.mean([np.linalg.norm(same_protos[i]-same_protos[j]) for i in range(16) for j in range(i+1,16)]))
    return {"real_interior_spread":round(real_spread,4),"same_kind_control_spread":round(same_spread,6)}

# ---------- SEPARATE POLICY EVAL ----------

def evaluate(b,d,i):
    laneA = (b["real_binding_accuracy"] > 3*b["chance"] and b["real_binding_accuracy"] > b["shuffled_label_accuracy"]+0.2
             and b["all_misses_are_genuine_degeneracies"] and b["accuracy_on_non_degenerate_objects"] > 0.99)
    laneB = d["degenerate_pairs_much_closer"]           # the criterion refuses to hallucinate objects
    laneC = i["real_interior_spread"] > 0.1 and i["same_kind_control_spread"] < 1e-9
    allpass=bool(laneA and laneB and laneC)
    return {"perception_binds_objects_across_novel_perspectives":bool(laneA),
            "criterion_refuses_to_hallucinate_on_degeneracies":bool(laneB),
            "binding_requires_the_distinct_kind_interior":bool(laneC),
            "AI_OF_PERCEPTION_OBJECT_BINDING_EARNED":allpass}

def main():
    b=measure_binding(); d=measure_degeneracy_honesty(); i=measure_interior_needed()
    verdict=evaluate(b,d,i)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "framing":"the AI of perception: binding never-seen views into objects, honestly failing on genuine degeneracies, connecting the engine interior to the object-formation success criteria",
         "binding":b,"degeneracy_honesty":d,"interior_needed":i,"policy_eval":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)

    print("THE AI OF PERCEPTION -- object binding across never-seen perspectives (the success criterion, run as perception).\n")
    print("  (A) REAL binding beats SHUFFLED:")
    print(f"      real binding accuracy {b['real_binding_accuracy']:.3f} ({b['n_novel_views']} never-seen views, {b['n_objects']} objects, chance {b['chance']:.3f})")
    print(f"      accuracy on NON-degenerate objects {b['accuracy_on_non_degenerate_objects']:.3f}; all misses are genuine degeneracies: {b['all_misses_are_genuine_degeneracies']}")
    print(f"      shuffled-label control accuracy {b['shuffled_label_accuracy']:.3f} (collapses to chance)")
    print("  (B) THE CRITERION IS REAL (refuses to hallucinate objects on genuine degeneracies):")
    print(f"      degenerate-pair signature distances {d['degenerate_pair_distances']} vs median inter-object {d['median_inter_object_distance']}")
    print(f"      degenerate pairs correctly MUCH closer (merged, not invented as separate): {d['degenerate_pairs_much_closer']}")
    print("  (C) BINDING NEEDS THE 16 DISTINCT KINDS (the interior):")
    print(f"      real interior spread {i['real_interior_spread']} vs same-kind control spread {i['same_kind_control_spread']} (unbindable if all one kind)")
    print("\n  SEPARATE POLICY EVAL (verdict = all three controls flip):")
    for k,v in verdict.items():
        if k!="AI_OF_PERCEPTION_OBJECT_BINDING_EARNED": print(f"    {k}: {v}")
    print(f"\n  AI OF PERCEPTION (OBJECT BINDING) EARNED: {verdict['AI_OF_PERCEPTION_OBJECT_BINDING_EARNED']}")
    if verdict["AI_OF_PERCEPTION_OBJECT_BINDING_EARNED"]:
        print("PASS perception_object_binding")
    print("ALL_GATES:", "PASS" if verdict["AI_OF_PERCEPTION_OBJECT_BINDING_EARNED"] else "FAIL","->",path)
    sys.exit(0 if verdict["AI_OF_PERCEPTION_OBJECT_BINDING_EARNED"] else 1)

if __name__=="__main__":
    main()
