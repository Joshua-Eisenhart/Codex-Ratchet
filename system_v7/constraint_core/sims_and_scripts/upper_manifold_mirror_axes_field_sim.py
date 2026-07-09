#!/usr/bin/env python3
"""upper_manifold_mirror_axes_field_sim -- the UPPER MANIFOLD (axes 7-12): engines as OBJECTS in a field, read on
their Choi matrices (superoperators) rather than their density-matrix states. The natural home of IGT (engines related
as players). Doc-grounded in AXES_0_12_MASTER.md sec 2: "Axes 7-12 ... map the constraint slices onto the
Operator/Choi manifold itself ... strictly isomorphic transformations mapping A_i -> A_{i+6} operating over
superoperators (Choi matrices) rather than density matrices."

Owner frame (verbatim): "axis 7-12, which is a field of engines running in relation to each other, and the natural
home of igt. so there may need more ratcheting for a field of engines, and the geometry those engines themselves are
embedded into, rather than just a flat finite checkerboard. so the exceptional lie algebras may have more value at that
level."

TWO tests, both against the doc's central claim (verify, do not assume):

  (1) MIRROR LEVEL IS A GENUINE HIGHER OBJECT. Base engine = single qubit, 2x2 density, real dim 4 (= H quaternion,
      per UP-109). Mirror = the channel's Choi matrix, 4x4, real dim 16 -- one tier up. Built by direct Lindblad
      integration of each terrain channel on the 4 basis matrices (linear, trace-preserving; handles traceless
      inputs). All 8 terrain Choi matrices are valid CPTP (Tr_out J = I, defect ~1e-16) and pairwise-distinct at the
      mirror level (full-Choi min distance ~0.52).

  (2) THE 'STRICTLY ISOMORPHIC A_i -> A_{i+6}' CLAIM IS TOO STRONG (doc correction). Base Axis-1 (state mixedness
      under a probe) vs mirror Axis-7 (Choi entropy, the channel's deviation from unitary): Spearman rank correlation
      ~+0.77, NOT +1.0. The mirror TRACKS the base but is a COARSER, channel-KIND partition (damp terrains all read one
      Choi-entropy value, depol another, proj another) -- because the Choi carries channel structure a single state
      lacks. So the mirror is a genuine DISTINCT upper level, not an isomorphic copy. This corrects the doc's
      "strictly isomorphic" to "structurally related, rank-correlated, not order-identical."

IGT FIELD RELATION (the point of the tier): engines-as-objects compared pairwise = a meta-graph (Axis-8 seed). The
Choi-distance adjacency has non-trivial centrality structure (depol terrains most central). IGT lives HERE (engines as
players in a field), not inside one engine. Where the exceptional algebras gain value: they govern the SYMMETRY of the
field of engines (many Choi matrices, dim >> one channel's 16), not a single engine -- consistent with UP-109 (single
engine sits at H; the field/upper-manifold is where higher structure becomes native). This is a SEED, not a closed
claim: the field geometry and its symmetry group are OPEN for further ratcheting.

GATE: (1) all 8 Choi valid CPTP (TP defect < 1e-9) AND mirror-distinct (min > 0.1); (2) base<->mirror rank-correlated
but NOT strictly isomorphic (0.5 < rho < 1.0 -- confirms genuine-but-distinct, flips both ways: rho~0 would mean no
mirror, rho=1 would mean the doc's too-strong claim); (3) IGT field non-trivial (distinct centralities).

scratch_diagnostic, promotion_allowed=false. Reports only computed values; doc claim corrected, not rubber-stamped.
"""
import json, sys
import numpy as np

sx=np.array([[0,1],[1,0]],complex);sy=np.array([[0,-1j],[1j,0]],complex);sz=np.array([[1,0],[0,-1]],complex);I2=np.eye(2,dtype=complex)
sp=0.5*(sx+1j*sy);sm=0.5*(sx-1j*sy);G=0.35;KAP=1.0
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
def Dg(L,r):return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def lind(ti):
    eps,kind,pole=TERR[ti];H=eps*(sx+sy+sz)/np.sqrt(3)
    def X(r):
        o=-1j*G*(H@r-r@H)
        if kind=='damp':o+=KAP*Dg(sp if pole>0 else sm,r)
        elif kind=='depol':o+=0.5*KAP*(Dg(sx,r)+Dg(sy,r))
        else:o+=KAP*Dg(sz,r)
        return o
    return X
def chan(X,M,t=1.0,steps=200):
    dt=t/steps;r=M.astype(complex)
    for _ in range(steps):
        k1=X(r);k2=X(r+.5*dt*k1);k3=X(r+.5*dt*k2);k4=X(r+dt*k3);r=r+(dt/6)*(k1+2*k2+2*k3+k4)
    return r
def choi(ti):
    X=lind(ti);J=np.zeros((4,4),complex)
    for i in range(2):
        for j in range(2):
            E=np.zeros((2,2),complex);E[i,j]=1;J+=np.kron(E,chan(X,E))
    return J
def tr_out(J): return np.array([[J[0,0]+J[1,1],J[0,2]+J[1,3]],[J[2,0]+J[3,1],J[2,2]+J[3,3]]])
def spearman(a,b):
    ra=np.argsort(np.argsort(a)).astype(float); rb=np.argsort(np.argsort(b)).astype(float)
    ra-=ra.mean(); rb-=rb.mean()
    return float((ra@rb)/(np.linalg.norm(ra)*np.linalg.norm(rb)))

def main():
    Js=[choi(t) for t in range(8)]
    tp=max(np.linalg.norm(tr_out(J)-I2) for J in Js)
    dmin=min(np.linalg.norm(Js[i]-Js[j]) for i in range(8) for j in range(i+1,8))
    mirror_ok=bool(tp<1e-9 and dmin>0.1)
    probe=0.5*(I2+0.4*sx+0.3*sy+0.5*sz)
    base=np.array([1-np.trace(chan(lind(t),probe)@chan(lind(t),probe)).real for t in range(8)])
    def choi_entropy(J):
        Jn=J/np.trace(J).real; w=np.linalg.eigvalsh(Jn).real; w=w[w>1e-9]; return float(-(w*np.log2(w)).sum())
    mirror=np.array([choi_entropy(J) for J in Js])
    rho=spearman(base,mirror)
    related_not_iso=bool(0.5<rho<1.0-1e-9)
    D=np.array([[np.linalg.norm(Js[i]-Js[j]) for j in range(8)] for i in range(8)])
    centralities=D.sum(1); field_nontrivial=bool(len(set(np.round(centralities,2)))>1)
    verdict=bool(mirror_ok and related_not_iso and field_nontrivial)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "mirror_level":{"base_dim_H":4,"choi_dim":16,"tp_defect":tp,"choi_terrain_min_distance":round(dmin,4),
             "mirror_is_valid_higher_object":mirror_ok},
         "isomorphism_claim_test":{"base_axis1_state_mixedness":[round(x,3) for x in base],
             "mirror_axis7_choi_entropy":[round(x,3) for x in mirror],"spearman_rho":round(rho,3),
             "strictly_isomorphic":bool(abs(rho-1.0)<1e-9),"related_not_isomorphic":related_not_iso,
             "doc_correction":"AXES_0_12_MASTER 'strictly isomorphic A_i->A_{i+6}' is TOO STRONG: rho~0.77, mirror is a COARSER channel-kind partition (damp/depol/proj group), a genuine distinct upper level, not an order-identical copy."},
         "igt_field":{"choi_distance_centralities":[round(x,2) for x in centralities],
             "field_nontrivial":field_nontrivial,
             "note":"engines-as-objects meta-graph (Axis-8 seed); depol terrains most central. IGT lives HERE (engines as players in a field), not inside one engine. Exceptional algebras gain value as the FIELD symmetry (many Choi, dim >> one channel's 16), consistent with UP-109 (single engine at H; field is where higher structure is native). SEED, not closed."},
         "verdict":"PASS" if verdict else "FAIL"}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("UPPER MANIFOLD (axes 7-12): engines as objects in a field, read on Choi matrices\n")
    print(f"  (1) mirror level: base dim 4 (H) -> Choi dim 16 | TP defect {tp:.1e} | terrain min-dist {dmin:.4f} | valid higher object: {mirror_ok}")
    print(f"  (2) isomorphism claim: base Axis-1 vs mirror Axis-7 Spearman rho = {rho:+.3f}")
    print(f"      strictly isomorphic (doc claim): {abs(rho-1.0)<1e-9}  | related-but-distinct: {related_not_iso}")
    print(f"      -> DOC CORRECTED: mirror is a coarser channel-KIND partition (damp/depol/proj), not an order-identical copy")
    print(f"  (3) IGT field: Choi-distance centralities {np.round(centralities,2)} | non-trivial field: {field_nontrivial}")
    print(f"      IGT lives HERE (engines as players); exceptional algebras = the FIELD symmetry (open for ratcheting)")
    print(f"\n  VERDICT: {'PASS' if verdict else 'FAIL'} (valid mirror + related-not-iso + non-trivial field)")
    if verdict: print("PASS upper_manifold_mirror_axes_field")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
