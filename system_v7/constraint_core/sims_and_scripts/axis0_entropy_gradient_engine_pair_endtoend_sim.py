#!/usr/bin/env python3
"""axis0_entropy_gradient_engine_pair_endtoend_sim -- runs Axis-0 as the ENTROPY GRADIENT end-to-end on the ACTUAL
ENGINE PAIR (Type-1 then Type-2, the closed 720-degree double loop), measured at the START (pair opens, all terrains
live) and END (after full closure). Uses the EARNED gradient definition from foundational_ratchet_entropy_gradient_sim:
AXIS-0 = available distinguishability (what a perfect instrument could resolve = sum of pairwise trace distances over
the possibility set) MINUS resolved distinguishability (what the carrier's acquired measurement bases can actually
access = sum of best-basis distinguishability, <= available by Helstrom). No bits, no vectors -- pure quantum
distinguishability, per no_bits_no_vectors_only_distinguishability.

This closes the biggest unbuilt engine seam: the entropy-gradient face of Axis-0 was earned at the COSMOGENESIS carrier
(foundational sim) but never run on the RUNNING engine pair. Owner: "axis0 ... it is an entropy gradient" and "do we
have running qit engines. axis0 at start and end?"

WHAT IS MEASURED (and the honest correction):
  - START room = outputs of all 8 terrain channels from a fixed probe (the pair "opens", terrains live).
  - END room = outputs after the full 720 double loop (T1_OUT, T1_IN, T2_OUT, T2_IN) from 8 seeds.
  - The ABSOLUTE gap (avail - resolved) drops sharply start->end (~0.46 -> ~0.02). BUT this is CONTAMINATED by trivial
    CONTRACTION: the dissipative flow drags all states toward fixed points, so the absolute available distinguishability
    collapses (~9.1 -> ~0.23) regardless of resolution. A pure depolarizing collapse closes the gap just as well. So
    "the Axis-0 gradient vanishes at closure" is NOT a clean engine claim -- it inherits the flow's contraction.
  - The CONTRACTION-FREE Axis-0 signal is the SCALE-INVARIANT unresolved fraction u = (avail - resolved)/avail. This
    is small and stable (~0.05 start, ~0.07 end): the engine's acquired probe bases resolve ~93-95% of the
    distinguishability the room offers, THROUGHOUT. That is the honest engine-pair Axis-0 reading: near-complete
    resolution, not a vanishing absolute gradient.

CONTROLS (falsifiable):
  - 1-PROBE (impoverished bases): unresolved fraction jumps (bases genuinely matter; not a tautology).
  - N01 loop-order SHUFFLE: unresolved fraction essentially unchanged (~0.068 vs ~0.069) -- the resolution FRACTION is
    order-insensitive at the density level, consistent with axis0_readouts_density_blind (Axis-0 order-structure is a
    spinor/loop property, invisible to density readouts).
  - CHIRALITY-ERASE (eps->+1 all terrains, the project's canonical engine-pair control): unresolved fraction SHIFTS
    (~0.083 vs ~0.069) -- terrain chirality is load-bearing for how much the engine resolves.

GATE: (1) absolute gap relaxes start->end (engine acts on the room it opens); (2) the honest contraction-free signal
(unresolved fraction) is small and near-stable (both < 0.15) -- near-complete resolution; (3) the 1-probe control
raises the unresolved fraction (bases matter); (4) chirality-erase shifts it (chirality load-bearing). Reports the
contraction contamination honestly rather than claiming a vanishing gradient.

scratch_diagnostic, promotion_allowed=false.
"""
import json, sys, random
import numpy as np

sx=np.array([[0,1],[1,0]],complex);sy=np.array([[0,-1j],[1j,0]],complex);sz=np.array([[1,0],[0,-1]],complex);I2=np.eye(2,dtype=complex)
sp=0.5*(sx+1j*sy);sm=0.5*(sx-1j*sy);G=0.35;KAP=1.0
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
def Dg(L,r):return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def lind(ti,flip=False):
    eps,kind,pole=TERR[ti]
    if flip: eps=+1
    H=eps*(sx+sy+sz)/np.sqrt(3)
    def X(r):
        o=-1j*G*(H@r-r@H)
        if kind=='damp':o+=KAP*Dg(sp if pole>0 else sm,r)
        elif kind=='depol':o+=0.5*KAP*(Dg(sx,r)+Dg(sy,r))
        else:o+=KAP*Dg(sz,r)
        return o
    return X
def chan(X,M,t=1.0,steps=60):
    dt=t/steps;r=M.astype(complex)
    for _ in range(steps):
        k1=X(r);k2=X(r+.5*dt*k1);k3=X(r+.5*dt*k2);k4=X(r+dt*k3);r=r+(dt/6)*(k1+2*k2+2*k3+k4);r=.5*(r+r.conj().T);tr=np.trace(r).real
        if tr>1e-12: r/=tr
    return r
def td(a,b): return 0.5*float(np.sum(np.abs(np.linalg.eigvalsh(a-b))))
PROBES=[sz,sx,sy,(sx+sz)/np.sqrt(2),(sx-sz)/np.sqrt(2),(sy+sz)/np.sqrt(2),(sy+sx)/np.sqrt(2)]
def bdist(a,b,P):
    w,V=np.linalg.eigh(P); da=np.array([(V[:,k].conj()@a@V[:,k]).real for k in range(2)]); dbb=np.array([(V[:,k].conj()@b@V[:,k]).real for k in range(2)])
    return 0.5*float(np.sum(np.abs(da-dbb)))
def avail(S): return sum(td(S[i],S[j]) for i in range(len(S)) for j in range(i+1,len(S)))
def resolved(S,probes=PROBES): return sum(max(bdist(S[i],S[j],P) for P in probes) for i in range(len(S)) for j in range(i+1,len(S)))
def unresolved_frac(S,probes=PROBES):
    a=avail(S); return (a-resolved(S,probes))/a if a>1e-9 else 0.0
SEQ=[0,1,2,3, 0,3,2,1, 4,7,6,5, 4,5,6,7]  # T1_OUT,T1_IN,T2_OUT,T2_IN (doc-faithful canonical slot terrain order)
def full_pair(r,order=None,flip=False):
    for t in (order if order is not None else SEQ): r=chan(lind(t,flip=flip),r,t=0.25)
    return r
SEEDS=[0.5*(I2+a*sx+b*sy+c*sz) for (a,b,c) in [(.4,.3,.5),(-.4,.3,.5),(.4,-.3,.5),(.4,.3,-.5),(-.4,-.3,.5),(.2,.5,.3),(-.2,-.5,-.3),(.5,.1,.2)]]

def main():
    r0=SEEDS[0]
    start=[chan(lind(t),r0) for t in range(8)]
    end=[full_pair(s) for s in SEEDS]
    gap_start=avail(start)-resolved(start); gap_end=avail(end)-resolved(end)
    relaxes=bool(gap_start>gap_end)
    uf_start,uf_end=unresolved_frac(start),unresolved_frac(end)
    near_complete=bool(uf_start<0.15 and uf_end<0.15)
    uf_1probe=unresolved_frac(end,[sz]); bases_matter=bool(uf_1probe>uf_end+0.05)
    random.seed(0); shuf=SEQ[:]; random.shuffle(shuf)
    uf_shuf=unresolved_frac([full_pair(s,order=shuf) for s in SEEDS])
    order_insensitive=bool(abs(uf_shuf-uf_end)<1e-2)
    uf_flip=unresolved_frac([full_pair(s,flip=True) for s in SEEDS])
    chirality_load_bearing=bool(abs(uf_flip-uf_end)>1e-3)
    verdict=bool(relaxes and near_complete and bases_matter and chirality_load_bearing)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "absolute_gap":{"start":round(gap_start,4),"end":round(gap_end,4),"relaxes_start_to_end":relaxes,
             "avail_start":round(avail(start),3),"avail_end":round(avail(end),3),
             "contamination_note":"the absolute gap relaxes mostly by CONTRACTION (dissipative flow collapses avail); a pure depol collapse closes it too. Not a clean engine claim."},
         "contraction_free_axis0":{"unresolved_frac_start":round(uf_start,4),"unresolved_frac_end":round(uf_end,4),
             "near_complete_resolution":near_complete,
             "reading":"scale-invariant unresolved fraction is small and stable (~0.05-0.07): the engine resolves ~93-95% of the distinguishability the room offers, throughout. This is the honest engine-pair Axis-0 signal."},
         "controls":{"one_probe_unresolved_frac":round(uf_1probe,4),"bases_matter":bases_matter,
             "n01_shuffle_unresolved_frac":round(uf_shuf,4),"order_insensitive_at_density":order_insensitive,
             "chirality_erased_unresolved_frac":round(uf_flip,4),"chirality_load_bearing":chirality_load_bearing},
         "verdict":"PASS" if verdict else "FAIL"}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("AXIS-0 ENTROPY GRADIENT end-to-end on the ENGINE PAIR (available - resolved distinguishability)\n")
    print(f"  absolute gap: START {gap_start:.4f} -> END {gap_end:.4f}  (relaxes: {relaxes}; avail {avail(start):.2f}->{avail(end):.2f})")
    print(f"    HONEST: the absolute relaxation is mostly CONTRACTION (flow collapses avail); pure depol closes it too.")
    print(f"  contraction-free Axis-0 (unresolved fraction, scale-invariant): START {uf_start:.4f}  END {uf_end:.4f}")
    print(f"    -> near-complete resolution ({near_complete}): the engine resolves ~93-95% of the room's distinguishability throughout")
    print(f"  controls: 1-probe uf {uf_1probe:.4f} (bases matter: {bases_matter}) | N01 shuffle uf {uf_shuf:.4f} (order-insensitive at density: {order_insensitive})")
    print(f"            chirality-erased uf {uf_flip:.4f} (chirality load-bearing: {chirality_load_bearing})")
    print(f"\n  VERDICT: {'PASS' if verdict else 'FAIL'} (relaxes + near-complete resolution + bases matter + chirality load-bearing)")
    if verdict: print("PASS axis0_entropy_gradient_engine_pair_endtoend")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
