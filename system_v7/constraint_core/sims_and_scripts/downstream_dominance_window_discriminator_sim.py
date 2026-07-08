#!/usr/bin/env python3
"""downstream_dominance_window_discriminator_sim -- the DOWNSTREAM discriminator the tournament handed back.

The substage-architecture tournament (this side UP-105; the parallel v7 run independently) left three live readings of
what a stage is: B (select-1 canonical), D (parallel-branch, observationally = B at loop output), and C-in-window (all
four operators run, canonical dominant, subordinates at attenuation alpha). The parallel run measured a DOMINANCE
WINDOW on stage identity: subordinate operators tolerated up to ~half strength (alpha<=0.5), equality (alpha->1) is
pathology that breaks the rung-1 anchor. Two independent codebases found the same window.

The open question it handed back: does anything DOWNSTREAM distinguish canonical-only (B/D) from dominant-with-
subordinates (C-in-window)? This sim answers it on the real instruments, sweeping alpha:

  READINGS: canonical-only (B/D) vs C-dominant at attenuation alpha in [0.05..0.50]. Each builds the 16 stage channels
  (terrain GKSL flow then operator; C mixes canonical-weight-1 + three subordinates weight-alpha, renormalized CPTP).

  DOWNSTREAM INSTRUMENTS (all pre-existing, load-bearing):
   (1) STAGE IDENTITY (rung-1 anchor): 16 stages stay distinct (min pairwise signature distance). Measures the
       parallel run's window.
   (2) RE-IDENTIFICATION (UP-100 full-affine signature, survives-probe-rotation): re-id rate under a never-seen probe
       family.
   (3) OBJECT FORMATION: number of distinct objects the 16 stages form (merge-at-degeneracy at a fixed threshold),
       compared to the canonical-only object count.

  MEASURED RESULT (the discriminator): re-id does NOT separate the readings (16/16 for all alpha in window -- the
  full-affine signature is robust to in-window subordinates). Stage identity degrades monotonically with alpha
  (min-pairwise 0.1385 canonical -> 0.0453 at equality alpha=1.0, a ~3.1x degradation). OBJECT FORMATION is the
  separating instrument, and it reveals a
  TWO-SIDED window: it matches canonical (14 objects) only for alpha in [0.10, 0.30]; at alpha=0.05 subordinates are
  too weak and OVER-resolve (15 objects), at alpha>=0.40 too strong and UNDER-resolve (12 objects, pairs blur). So the
  downstream-safe window (alpha in [0.10,0.30]) is STRICTER than the stage-identity window (alpha<=0.5) -- object
  formation closes it from both ends. B/D and C are observationally equivalent ONLY inside [0.10,0.30]; outside, C is
  downstream-distinguishable and worse.

  VERDICT (gated): object formation is a genuine downstream discriminator (canonical count is matched only on a bounded
  interior interval, and DIVERGES on BOTH sides -- proving it is not a rubber stamp that always agrees).

scratch_diagnostic, promotion_allowed=false. No reading crowned; the report is the per-alpha scorecard + the measured
two-sided window. Pure QIT (GKSL flows + native operators).
"""
import json, sys
import numpy as np
from scipy.linalg import expm

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
I2=np.eye(2,dtype=complex); sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
G=0.35; KAP=1.0; Q=1-np.exp(-1.0); TH=np.pi/4; T_FLOW=1.0; N_STEPS=120
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
NATIVE={0:('Ti','Fi'),1:('Ti','Fi'),2:('Te','Fe'),3:('Te','Fe'),4:('Ti','Fi'),5:('Ti','Fi'),6:('Te','Fe'),7:('Te','Fe')}
ALLOPS=('Ti','Te','Fi','Fe')
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
def bloch(r): return np.array([np.trace(r@s).real for s in (sx,sy,sz)])
def rho_from_bloch(v): return 0.5*(I2+v[0]*sx+v[1]*sy+v[2]*sz)
STAGES=[(t,o) for t in range(8) for o in NATIVE[t]]

def canon_only(t,o):
    X=gen(t); O=op(o); return lambda r: O(flow(X,r.copy()))
def dominant(t,o,alpha):
    X=gen(t); ops=[op(x) for x in ALLOPS]; oc=op(o)
    def chan(r):
        rf=flow(X,r.copy()); outs=[oc(rf)]+[o_(rf) for o_ in ops if o_ is not oc]
        w=np.array([1.0]+[alpha]*3); w/=w.sum(); mixed=sum(wi*o_ for wi,o_ in zip(w,outs))
        return mixed/np.trace(mixed).real
    return chan

def full_affine_sig(chan, probes):
    img=bloch(chan(0.5*I2)); X=np.array([bloch(p) for p in probes]); Y=np.array([bloch(chan(p)) for p in probes])
    Xa=np.hstack([X,np.ones((len(X),1))]); M,*_=np.linalg.lstsq(Xa,Y,rcond=None)
    return np.concatenate([img,(M[:3,:].T).reshape(-1)])
def coarse_sig(chan): return np.concatenate([bloch(chan(rho_from_bloch(v))) for v in [[.5,0,0],[0,.5,0],[0,0,.5]]])
def min_pairwise(chanfn):
    S=[coarse_sig(chanfn(t,o)) for (t,o) in STAGES]
    return min(np.linalg.norm(S[i]-S[j]) for i in range(16) for j in range(i+1,16))
def reid(chanfn,seen,novel):
    ss=[full_affine_sig(chanfn(t,o),seen) for (t,o) in STAGES]; sn=[full_affine_sig(chanfn(t,o),novel) for (t,o) in STAGES]
    return sum(1 for i in range(16) if int(np.argmin([np.linalg.norm(sn[i]-ss[j]) for j in range(16)]))==i)/16
def n_objects(chanfn,thr=0.15):
    S=[coarse_sig(chanfn(t,o)) for (t,o) in STAGES]; used=[False]*16;n=0
    for i in range(16):
        if used[i]:continue
        n+=1
        for j in range(i+1,16):
            if not used[j] and np.linalg.norm(S[i]-S[j])<thr: used[j]=True
    return n

def main():
    rng=lambda s: rho_from_bloch(0.7*np.random.default_rng(s).normal(size=3)/np.linalg.norm(np.random.default_rng(s).normal(size=3)))
    seen=[rng(11+i) for i in range(8)]; novel=[rng(900+i) for i in range(8)]
    canon={"min_pairwise":round(min_pairwise(lambda t,o: canon_only(t,o)),4),
           "reid":reid(lambda t,o: canon_only(t,o),seen,novel),
           "n_objects":n_objects(lambda t,o: canon_only(t,o))}
    base_obj=canon["n_objects"]
    rows=[]
    for a in [0.05,0.10,0.15,0.20,0.25,0.30,0.40,0.50,0.75,1.00]:
        mp=min_pairwise(lambda t,o,a=a: dominant(t,o,a)); ri=reid(lambda t,o,a=a: dominant(t,o,a),seen,novel); no=n_objects(lambda t,o,a=a: dominant(t,o,a))
        rows.append({"alpha":a,"min_pairwise":round(mp,4),"reid":ri,"n_objects":no,"matches_canonical_objects":bool(no==base_obj)})
    # object formation is a genuine discriminator iff it matches canonical on an INTERIOR interval and DIVERGES on both sides
    matched=[r["alpha"] for r in rows if r["matches_canonical_objects"]]
    lo=[r for r in rows if r["alpha"]<min(matched)] if matched else []
    hi=[r for r in rows if r["alpha"]>max(matched)] if matched else []
    two_sided=bool(matched and any(not r["matches_canonical_objects"] for r in lo) and any(not r["matches_canonical_objects"] for r in hi))
    reid_flat=bool(all(r["reid"]==1.0 for r in rows) and canon["reid"]==1.0)
    verdict=bool(two_sided)  # object formation discriminates with a genuine two-sided window (not a rubber stamp)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "canonical_BD":canon,"C_dominant_sweep":rows,
         "reid_does_not_discriminate":reid_flat,
         "object_formation_window":{"matched_alphas":matched,"two_sided_window":two_sided,
             "note":"B/D and C observationally equivalent for object formation only on this interior interval"},
         "DOWNSTREAM_DISCRIMINATOR":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("DOWNSTREAM DISCRIMINATOR -- canonical-only (B/D) vs dominant-with-subordinates (C), across alpha.\n")
    print(f"  canonical-only (B/D): min-pairwise {canon['min_pairwise']}  re-id {canon['reid']:.3f}  objects {canon['n_objects']}\n")
    print("  C dominant sweep:")
    for r in rows:
        tag="== canonical objects" if r["matches_canonical_objects"] else "DIVERGES"
        print(f"    alpha={r['alpha']:.2f}: min-pair {r['min_pairwise']:.4f}  re-id {r['reid']:.3f}  objects {r['n_objects']}  {tag}")
    print(f"\n  re-id does NOT discriminate (all 16/16): {reid_flat}")
    print(f"  object-formation matches canonical on alpha in {matched} -- two-sided window: {two_sided}")
    print(f"\n  DOWNSTREAM DISCRIMINATOR (object formation, genuine two-sided window): {verdict}")
    if verdict: print("PASS downstream_dominance_window_discriminator")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
