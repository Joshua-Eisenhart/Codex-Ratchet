#!/usr/bin/env python3
"""loop_uniqueness_trajectory_probe -- the LOOP-level analog of the UP-100 stage-probe repair.

UP-100 fixed stage re-identification by using the FULL affine Bloch map (orientation-bearing) instead of its singular
values, lifting stage re-id to 16/16. This probe applies the SAME trajectory-sensitive signature ONE LEVEL UP: to the
four engine LOOPS (T1 outer/deductive, T1 inner/inductive, T2 outer, T2 inner), each a composed 4-stage channel over
the doc-faithful canonical slots. It answers the panel's worth-defending item #2 (order-carried loop uniqueness) and
the v7 loop-dynamics probe's open item, as an INDEPENDENT second implementation (v7 uses per-segment SINDy; this uses
the composed-channel full-affine signature + a trajectory record).

TWO CLAIMS, both gated:
  (1) LOOP IDENTITY SURVIVES PROBE ROTATION. Signature each loop by (a) the full affine Bloch map A of the composed
      loop channel (recovered from a probe family, orientation-bearing, probe-set-independent), and (b) the nonunital
      image of I/2. Fingerprint on a SEEN probe family; re-identify from a disjoint NEVER-SEEN family by nearest
      neighbour. Re-id rate = fraction of the 4 loops correctly matched. Control: shuffled-loop assignment -> chance.
  (2) ORDER IS CARRIED (the loop is not its unordered stage set). For each loop, compare the forward traversal against
      the REVERSE traversal of the same 4 slots. If order is load-bearing, forward and reverse are distinguishable
      channels (full-affine distance > 0 by a margin). Baseline: a SELF-NULL -- the same forward channel signed from a
      disjoint NEVER-SEEN probe family. Because the affine map A is probe-set-independent, the self-null is ~0, so it
      is the noise floor the forward-vs-reverse distance must clear. The gate requires forward-vs-reverse to exceed
      that self-null floor by >10x AND be >1e-2 in absolute terms, for every loop.

scratch_diagnostic, promotion_allowed=false. Pure QIT; no jargon in the mechanism. Reuses the exact engine channel
convention (up=operator-first Phi_T(O(rho)); down=terrain-first O(Phi_T(rho))) from the full-engine sims.
"""
import json, sys
import numpy as np
from scipy.linalg import expm

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
I2=np.eye(2,dtype=complex); sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
G=0.35; KAP=1.0; Q=1-np.exp(-1.0); TH=np.pi/4; T_FLOW=1.0; N_STEPS=200
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
# doc-faithful canonical slots (terrain, operator, axis6 casing)
T1_OUT=[(0,'Ti','up'),(1,'Ti','down'),(2,'Fe','down'),(3,'Fe','up')]
T1_IN =[(0,'Fi','down'),(3,'Te','down'),(2,'Te','up'),(1,'Fi','up')]
T2_OUT=[(4,'Fi','up'),(7,'Te','up'),(6,'Te','down'),(5,'Fi','down')]
T2_IN =[(4,'Ti','down'),(5,'Ti','up'),(6,'Fe','up'),(7,'Fe','down')]
LOOPS={"T1_OUT_deductive":T1_OUT,"T1_IN_inductive":T1_IN,"T2_OUT":T2_OUT,"T2_IN":T2_IN}

def Dgen(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def gen(ti):
    eps,kind,pole=TERR[ti]; H=eps*(sx+sy+sz)/np.sqrt(3)
    def X(r):
        out=-1j*G*(H@r-r@H)
        if kind=='damp': out=out+KAP*Dgen(sp if pole>0 else sm,r)
        elif kind=='depol': out=out+0.5*KAP*(Dgen(sx,r)+Dgen(sy,r))
        else: out=out+KAP*Dgen(sz,r)
        return out
    return X
def flow(X,r,t=T_FLOW,steps=N_STEPS):
    dt=t/steps
    for _ in range(steps):
        k1=X(r);k2=X(r+.5*dt*k1);k3=X(r+.5*dt*k2);k4=X(r+dt*k3)
        r=r+(dt/6)*(k1+2*k2+2*k3+k4);r=.5*(r+r.conj().T);r/=np.trace(r).real
    return r
def op(name):
    P0=0.5*(I2+sz);P1=0.5*(I2-sz);Qp=0.5*(I2+sx);Qm=0.5*(I2-sx)
    if name=='Ti': return lambda r:(1-Q)*r+Q*(P0@r@P0+P1@r@P1)
    if name=='Te': return lambda r:(1-Q)*r+Q*(Qp@r@Qp+Qm@r@Qm)
    if name=='Fi': U=expm(-1j*TH/2*sx); return lambda r:U@r@U.conj().T
    if name=='Fe': U=expm(-1j*TH/2*sz); return lambda r:U@r@U.conj().T
def slot_chan(slot):
    t,o,sign=slot; X=gen(t); O=op(o)
    if sign=='up': return lambda r: flow(X,O(r.copy()))      # operator-first
    return lambda r: O(flow(X,r.copy()))                     # terrain-first
def loop_chan(slots):
    chans=[slot_chan(s) for s in slots]
    def f(r):
        for c in chans: r=c(r)
        return r
    return f
def bloch(r): return np.array([np.trace(r@s).real for s in (sx,sy,sz)])
def rho_from_bloch(v): return 0.5*(I2+v[0]*sx+v[1]*sy+v[2]*sz)
def probe_family(seed,n=8,radius=0.7):
    rng=np.random.default_rng(seed); fam=[]
    for _ in range(n):
        v=rng.normal(size=3); v=radius*v/np.linalg.norm(v); fam.append(rho_from_bloch(v))
    return fam
def channel_signature(chan,probes):
    # full affine map A (orientation-bearing) + nonunital I/2 image -- the UP-100 trajectory-sensitive signature
    img=bloch(chan(0.5*I2))
    X=np.array([bloch(p) for p in probes]); Y=np.array([bloch(chan(p)) for p in probes])
    Xa=np.hstack([X,np.ones((len(X),1))]); M,*_=np.linalg.lstsq(Xa,Y,rcond=None)
    A=M[:3,:].T
    return np.concatenate([img,A.reshape(-1)])

def reident_rate(sig_seen,sig_novel,assignment=None):
    n=len(sig_seen); assignment=assignment if assignment is not None else list(range(n)); ok=0
    for i in range(n):
        d=[np.linalg.norm(sig_novel[assignment[i]]-sig_seen[j]) for j in range(n)]
        if int(np.argmin(d))==i: ok+=1
    return ok/n

def main():
    names=list(LOOPS); slots=[LOOPS[k] for k in names]
    seen=probe_family(11); novel=probe_family(999)
    chans=[loop_chan(s) for s in slots]
    sig_seen=[channel_signature(c,seen) for c in chans]
    sig_novel=[channel_signature(c,novel) for c in chans]

    # (1) re-identification under probe rotation
    real_rate=reident_rate(sig_seen,sig_novel)
    rng=np.random.default_rng(7); sh=[]
    from itertools import permutations
    for perm in permutations(range(len(names))):
        if list(perm)==list(range(len(names))): continue
        sh.append(reident_rate(sig_seen,sig_novel,assignment=list(perm)))
    shuffled_mean=float(np.mean(sh)); shuffled_max=float(np.max(sh)); chance=1.0/len(names)
    reid_control_flips=bool(shuffled_mean<=chance+0.05 and real_rate>shuffled_max)

    # (2) order-carried: forward vs reverse traversal of the same 4 slots
    order_rows=[]
    for k,s in zip(names,slots):
        fwd=loop_chan(s); rev=loop_chan(list(reversed(s)))
        sf=channel_signature(fwd,seen); sr=channel_signature(rev,seen)
        # self-null: same loop, disjoint probe family (should be ~0 since A is probe-independent)
        sf2=channel_signature(fwd,novel); selfnull=float(np.linalg.norm(sf-sf2))
        fr_dist=float(np.linalg.norm(sf-sr))
        order_rows.append({"loop":k,"forward_vs_reverse_dist":round(fr_dist,4),"self_null":round(selfnull,6),
                           "order_carried":bool(fr_dist>10*max(selfnull,1e-6) and fr_dist>1e-2)})
    order_sep_min=min(r["forward_vs_reverse_dist"] for r in order_rows)
    selfnull_max=max(r["self_null"] for r in order_rows)
    order_is_carried=bool(all(r["order_carried"] for r in order_rows))

    verdict=bool(reid_control_flips and order_is_carried)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "criterion":"loop-level analog of UP-100: identity survives probe rotation (full-affine signature) AND order is carried (forward != reverse); independent second implementation of the v7 loop-dynamics question",
         "n_loops":len(names),"loop_names":names,
         "reid":{"real_rate":real_rate,"shuffled_mean":shuffled_mean,"shuffled_max":shuffled_max,
                 "chance":chance,"separation":real_rate-shuffled_mean,"control_flips":reid_control_flips},
         "order_carried":{"per_loop":order_rows,"min_forward_vs_reverse_dist":round(order_sep_min,4),
                          "max_self_null":round(selfnull_max,6),"all_loops_order_carried":order_is_carried},
         "LOOP_UNIQUENESS_TRAJECTORY_PROBE":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("LOOP-LEVEL trajectory-sensitive uniqueness probe (UP-100 signature, one level up).\n")
    print(f"(1) RE-ID under probe rotation: real {real_rate:.3f}  shuffled mean {shuffled_mean:.3f} max {shuffled_max:.3f}  (chance {chance:.3f})")
    print(f"    -> control flips (identity survives rotation): {reid_control_flips}\n")
    print("(2) ORDER CARRIED (forward vs reverse traversal):")
    for r in order_rows: print(f"    {r['loop']:18} fwd-vs-rev {r['forward_vs_reverse_dist']:.4f}  self-null {r['self_null']:.2e}  carried: {r['order_carried']}")
    print(f"    min fwd-vs-rev {order_sep_min:.4f}  max self-null {selfnull_max:.2e}  -> all loops order-carried: {order_is_carried}")
    print(f"\n  LOOP UNIQUENESS + ORDER CARRIED: {verdict}")
    if verdict: print("PASS loop_uniqueness_trajectory_probe")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
