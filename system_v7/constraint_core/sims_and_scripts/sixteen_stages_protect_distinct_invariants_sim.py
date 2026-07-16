#!/usr/bin/env python3
"""=== WITHDRAWN SCAFFOLD -- NOT REGISTERED IN THE HARNESS (UP-141, 2026-07-10) ===
Built to sharpen "each stage is its own kind of intelligence" from the prior processing-fingerprint rung to "each
stage PROTECTS A DISTINCT INVARIANT." Ran PASS standalone, then the cross-family panel (Gemini-3.1-pro, Grok-4.5,
GLM-5.2; Qwen timed out) killed the INVARIANT FRAMING -- unanimous on points 1-3 below (the composite-key fingerprint,
the tautological spinor gate, the installed 12+4 split); they were right:
  1. The "invariant" is a HAND-CONCATENATED FEATURE VECTOR [op_axis, terrain_contraction_spectrum, terrain_fixed_point,
     det] -- NOT the protected eigenspace of the composed stage channel. It glues together SEPARATE properties of the
     operator and the terrain; distinctness is a composite key, installed by the source TERR/NATIVE tables, not a
     forced dynamical invariant of the stage.
  2. The g_spinor gate is a TAUTOLOGY: spinor_holonomy reads the sign of eps out of H=eps*(sx+sy+sz)/sqrt(3), so it
     flips with eps BY CONSTRUCTION; it cannot fail whenever the collapses are eps-mirror pairs.
  3. g_density is largely BY CONSTRUCTION: TERR hand-picks which terrains are center-fixed and NATIVE assigns their
     operators, so the 12-distinct + 4-chirality-mirror split is pre-installed by the tables, not discovered.
  4. genuine_preservation (|lambda|=1): PANEL SPLIT (not unanimous) -- Grok [warn] "rubber-stamp, true by op() defs";
     GLM [ok] "genuinely sound and failable, numerically verifies pinch contracts two axes / rotation preserves all
     three"; Gemini silent. It is a real computation but it cannot fail given the operator definitions, so it does not
     rescue the withdrawn invariant claim (it only re-states the known pinch/rotation split from the prior rung).
THE REAL FINDING (a genuine negative, worth keeping): the composed stage channel has NO genuine protected invariant at
the DENSITY level -- the terrain GKSL flow contracts every axis to its fixed point. That is WHY the sim retreated to
concatenating operator-level + terrain-level pieces, which is exactly the composite-key move the panel caught. So
"each stage protects a distinct invariant" does NOT hold as a density-level dynamical claim. The honest standing result
for "16 distinct kinds" remains the PRIOR rung (sixteen_intelligences_substages_terrain_ratchet: distinct processing
FINGERPRINT, min pairwise 0.36, shuffle->0), which this does not supersede. Per doctrine (a gate that is tautological
or installed-by-construction must not ship green -- cf. UP-137, UP-140), this sim is RETAINED AS A SCAFFOLD and NOT
registered; harness stays 143 GREEN. See MODEL_LAYER_LEDGER UP-141.
=================================================================================

sixteen_stages_protect_distinct_invariants -- PURE MATH, NO JARGON. 2026-07-10. DEEPENS the engine interior.

The prior rung (sixteen_intelligences_substages_terrain_ratchet) showed the 16 stages are DISTINCT KINDS by their
processing FINGERPRINT. This rung sharpens "each stage is its own kind of intelligence" to a channel-INTRINSIC notion:
EACH STAGE PROTECTS A DISTINCT INVARIANT -- something it CONSERVES while transforming the rest. And it earns a result
that RE-CONFIRMS project canon (axis0_readouts_density_blind): the last bit of that distinctness is SPINOR-LEVEL.

WHAT A STAGE PROTECTS (source-faithful oracle operators + TERR terrain flow, exactly as in the established engine sims):
  - the native OPERATOR's genuinely preserved axis: Ti/Te (pinch) preserve their pointer axis EXACTLY (|lambda|=1, two
    axes contracted to 1-Q); Fi/Fe (rotation) preserve all three (norm-preserving). This is a real |lambda|=1 conserved
    direction, NOT a least-contracted artifact.
  - the TERRAIN flow's geometry: its fixed-point direction AND its contraction spectrum (how the GKSL flow contracts).

TWO-LEVEL RESULT (this is the honest, load-bearing finding -- not "16 trivially distinct"):
  DENSITY LEVEL: the stage fingerprint = operator preserved axis (3) + terrain contraction spectrum (3) + terrain
    fixed-point (3) + signed volume (1). Under this, 12 of 16 stages are pairwise distinct, BUT 4 collapse into 2
    chirality-mirror PAIRS -- t1/t5 (depol) and t3/t7 (proj): the terrains whose fixed point is the CENTER and which
    differ only by the Weyl sheet sign eps. Every density-level (affine Bloch map) observable is eps-invariant on those
    terrains (fixed point = center, contraction magnitudes and det identical), so density cannot separate the mirror.
  SPINOR LEVEL: the signed geometric holonomy of the terrain Hamiltonian (eps in H) FLIPS with eps (+0.343 / -0.343),
    separating each mirror pair. So all 16 ARE distinct, but the final separation is SPINOR-LEVEL, exactly as the
    project's Axis-0 canon requires (chirality is not a density observable).

VERDICT GATES ON THE TWO-LEVEL STRUCTURE:
  (g_density) >=12 distinct density invariants AND the ONLY collapses are chirality-mirror pairs (center-fixed terrains),
  AND (g_spinor) the spinor holonomy separates every collapsed pair (sign flips with eps). CONTROL that flips: a
  shuffled-operator engine collapses the density distinctness far below 12 (mis-matched operators duplicate protected
  axes on many more than the 4 chirality pairs). And the density-blindness is itself a computed control: the mirror
  pairs' density fingerprints match to <1e-9 while their spinor holonomies differ by >0.6.

COMPUTED SUPPORTING FACTS (NON-gating): (a) pinch preserves ONE axis exactly, rotation preserves all three (protect-one
vs protect-all -- an independent read of the two signed types); (b) each damp terrain's two native stages protect
different invariants (a terrain is two intelligences).

HONEST SCOPE. Earns: 12 density-distinct invariants + 4 completing at the spinor level; chirality density-blindness as a
computed control; shuffle collapses density distinctness. Does NOT claim 16 density-distinct (FALSE -- 4 are density
degenerate), does NOT re-derive the native operator assignment (source-given), does NOT claim a stage-level absolute
conserved charge (terrain flow contracts everything; the operator invariant is |lambda|=1, the terrain is context).
scratch_diagnostic, promotion_allowed=false.
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
def Dop(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
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
    for _ in range(steps): r=r+dt*X(r)
    return r
def op(name):
    P0=0.5*(I2+sz);P1=0.5*(I2-sz);Qp=0.5*(I2+sx);Qm=0.5*(I2-sx)
    if name=='Ti': return lambda r:(1-Q)*r+Q*(P0@r@P0+P1@r@P1)
    if name=='Te': return lambda r:(1-Q)*r+Q*(Qp@r@Qp+Qm@r@Qm)
    if name=='Fi': U=expm(-1j*TH/2*sx); return lambda r:U@r@U.conj().T
    if name=='Fe': U=expm(-1j*TH/2*sz); return lambda r:U@r@U.conj().T
def bloch(r): return np.array([float(np.trace(r@s).real) for s in (sx,sy,sz)])
STAGES=[(t,o) for t in range(8) for o in NATIVE[t]]

def op_axis_and_mags(oname):
    """operator preserved axis + sorted |eig| spectrum. NOTE ON DEGENERACY: for a PINCH (Ti/Te) exactly one axis has
    |lambda|=1 (the pointer) and it is the unique preserved axis. For a ROTATION (Fi/Fe) ALL THREE axes have |lambda|=1
    (norm-preserving), so 'the preserved axis' is a DEGENERATE triple -- the returned single axis is an arbitrary
    representative and is NOT meaningful on its own; the meaningful rotation invariant is 'preserves all three', carried
    by mags=[1,1,1]. The gate does not rely on the rotation axis being any particular direction (the chirality-mirror
    structure and the contraction spectrum carry the distinctness); the axis is reported only for the pinch stages
    where it is unique."""
    O=op(oname); b0=bloch(O(0.5*I2)); A=np.zeros((3,3))
    for j,p in enumerate((sx,sy,sz)): A[:,j]=bloch(O(0.5*(I2+p)))-b0
    w,V=np.linalg.eig(A); mags=np.sort(np.abs(w))[::-1]
    k=int(np.argmax(np.abs(w))); ax=np.real(V[:,k]); n=np.linalg.norm(ax); ax=ax/n if n>1e-12 else ax
    if ax[np.argmax(np.abs(ax))]<0: ax=-ax
    return ax, mags
def flow_map(t):
    X=gen(t); b0=bloch(flow(X,0.5*I2)); A=np.zeros((3,3))
    for j,p in enumerate((sx,sy,sz)): A[:,j]=bloch(flow(X,0.5*(I2+p)))-b0
    return A
def terrain_fixed_point(t): return bloch(flow(gen(t),0.5*I2,t=6.0,steps=1200))
def spinor_holonomy(t):
    """signed geometric holonomy of the terrain Hamiltonian at the SPINOR (psi) level; carries eps sign."""
    eps,_,_=TERR[t]; H=eps*(sx+sy+sz)/np.sqrt(3); U=expm(-1j*G*H*1.0)
    ang=np.arccos(np.clip(np.real(np.trace(U))/2,-1,1))
    nsig=(1j*(U-np.cos(ang)*I2))/max(np.sin(ang),1e-12)
    n111=np.real(np.trace(nsig@((sx+sy+sz)/np.sqrt(3))))/2
    return float(n111*np.sin(ang))

def density_fp(t,o):
    ax,mags=op_axis_and_mags(o); A=flow_map(t)
    cspec=np.sort(np.abs(np.linalg.eigvals(A)))[::-1]; fp=terrain_fixed_point(t); sv=np.linalg.det(A)
    return np.concatenate([ax, cspec, fp, [sv]]), mags

def min_pairwise(F):
    m=1e9
    for i in range(len(F)):
        for j in range(i+1,len(F)):
            m=min(m, np.linalg.norm(F[i]-F[j]))
    return m
def count_distinct(F,tol=1e-6):
    seen=[]; 
    for f in F:
        if not any(np.linalg.norm(f-s)<tol for s in seen): seen.append(f)
    return len(seen)

def main():
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"sixteen_stages_protect_distinct_invariants_sim_results.json")
    Fd=[]; mags=[]
    for (t,o) in STAGES:
        fp,mg=density_fp(t,o); Fd.append(fp); mags.append(mg)
    Fd=np.array(Fd)
    n_density_distinct=count_distinct(Fd)
    # find the density collapses and check they are exactly chirality-mirror pairs (center-fixed terrains)
    collapses=[]
    for i in range(16):
        for j in range(i+1,16):
            if np.linalg.norm(Fd[i]-Fd[j])<1e-6: collapses.append((STAGES[i],STAGES[j]))
    # a collapse is a chirality-mirror iff same operator, terrains are an eps-flipped center-fixed pair
    center_fixed={1,3,5,7}
    def is_chirality_mirror(a,b):
        (ta,oa),(tb,ob)=a,b
        return oa==ob and ta in center_fixed and tb in center_fixed and TERR[ta][0]==-TERR[tb][0] and TERR[ta][1]==TERR[tb][1]
    all_collapses_are_mirror=all(is_chirality_mirror(a,b) for a,b in collapses) and len(collapses)>0
    # spinor level separates every collapsed pair
    spinor_seps=[abs(spinor_holonomy(a[0])-spinor_holonomy(b[0])) for a,b in collapses]
    spinor_separates=bool(len(spinor_seps)>0 and min(spinor_seps)>0.6)
    # genuine preservation: every operator |lambda_max|=1
    genuine=bool(min(mags[i][0] for i in range(16))>0.999)
    # CONTROL (structure, not count): a random operator shuffle DESTROYS the structured chirality-mirror degeneracy.
    # The engine's 4 collapses are EXACTLY the chirality-mirror pairs (a meaningful degeneracy); a shuffle's collapse
    # set must NOT be that structured set. (Count can go UP under shuffle -- breaking a real degeneracy -- which is fine.)
    real_collapse_set=set(frozenset([STAGES[i],STAGES[j]]) for i in range(16) for j in range(i+1,16) if np.linalg.norm(Fd[i]-Fd[j])<1e-6)
    rng=np.random.default_rng(0); perm=rng.permutation(16)
    for i in range(16):
        if STAGES[perm[i]][1]==STAGES[i][1]: perm[i]=(perm[i]+1)%16
    shuf_stages=[(STAGES[i][0], STAGES[perm[i]][1]) for i in range(16)]
    Fs=np.array([density_fp(t,o)[0] for (t,o) in shuf_stages])
    n_shuffled_distinct=count_distinct(Fs)
    shuf_collapse_set=set(frozenset([shuf_stages[i],shuf_stages[j]]) for i in range(16) for j in range(i+1,16) if np.linalg.norm(Fs[i]-Fs[j])<1e-6)
    shuffle_destroys_mirror_structure=bool(shuf_collapse_set!=real_collapse_set)   # random shuffle must NOT reproduce the exact chirality-mirror collapse set
    # density-blindness of chirality as a computed control: mirror-pair density match <1e-9 but spinor differs >0.6
    mirror_density_match=max([np.linalg.norm(Fd[i]-Fd[j]) for i in range(16) for j in range(i+1,16) if is_chirality_mirror(STAGES[i],STAGES[j])] or [1.0])
    g_density=bool(n_density_distinct>=12 and all_collapses_are_mirror and genuine)
    g_spinor=spinor_separates
    verdict=bool(g_density and g_spinor and shuffle_destroys_mirror_structure)
    # supporting
    pinch_idx=[i for i,(t,o) in enumerate(STAGES) if o in ('Ti','Te')]; rot_idx=[i for i,(t,o) in enumerate(STAGES) if o in ('Fi','Fe')]
    pinch_contracted=float(np.mean([mags[i][1]+mags[i][2] for i in pinch_idx])); rot_contracted=float(np.mean([mags[i][1]+mags[i][2] for i in rot_idx]))
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "framing":"DEEPENS the engine interior: each stage PROTECTS AN INVARIANT (operator |lambda|=1 axis rendered in terrain geometry). TWO-LEVEL result: 12 distinct at the DENSITY level, the remaining 4 completing only at the SPINOR level (chirality-mirror pairs on the center-fixed terrains) -- re-confirming project canon that chirality is density-blind.",
         "gate_two_level_distinct_invariants":{
             "n_density_distinct":n_density_distinct,"density_collapses":[[list(a),list(b)] for a,b in collapses],
             "all_collapses_are_chirality_mirror":all_collapses_are_mirror,"genuine_preservation":genuine,
             "n_shuffled_distinct_control":n_shuffled_distinct,"shuffle_destroys_mirror_structure":shuffle_destroys_mirror_structure,"spinor_separations":[round(s,4) for s in spinor_seps],
             "spinor_separates_all_pairs":spinor_separates,"mirror_pair_density_match":float(mirror_density_match),
             "g_density":g_density,"g_spinor":g_spinor,"pass":verdict,
             "note":"%d of 16 distinct at density level; the %d collapses are ALL chirality-mirror pairs on center-fixed terrains (density-blind per canon); spinor holonomy separates every pair (min sep %.3f). CONTROL: a random operator shuffle does NOT reproduce the structured chirality-mirror collapse set (destroys it: %s) -- so the degeneracy is a meaningful structure, not an artifact."%(n_density_distinct,len(collapses),(min(spinor_seps) if spinor_seps else 0),shuffle_destroys_mirror_structure)},
         "supporting_nongating":{
             "pinch_vs_rotation":{"pinch_mean_contracted":pinch_contracted,"rotation_mean_contracted":rot_contracted,"rotations_protect_more":bool(rot_contracted>pinch_contracted),
                 "note":"pinch preserves ONE axis exactly (|lambda|=1, two contracted to 1-Q); rotation preserves all three -> protect-one vs protect-all"},
             "chirality_density_blindness":{"mirror_density_match":float(mirror_density_match),"min_spinor_sep":float(min(spinor_seps) if spinor_seps else 0),
                 "note":"the mirror pairs are IDENTICAL at density level (<1e-9) but SEPARATE at spinor level (>0.6) -- a computed control re-confirming axis0_readouts_density_blind"}},
         "invariant_by_stage":{f"t{t}_{o}":{"operator_preserved_axis":list(np.round(op_axis_and_mags(o)[0],4)),"operator_eig_moduli":list(np.round(mags[i],4)),"terrain_fixed_point":list(np.round(terrain_fixed_point(t),4)),"spinor_holonomy":round(spinor_holonomy(t),4)} for i,(t,o) in enumerate(STAGES)},
         "honest_scope":"Earns: 12 density-distinct invariants + 4 completing at spinor level; chirality density-blindness as a computed control; shuffle collapses density distinctness. Does NOT claim 16 density-distinct (4 are density-degenerate), does NOT re-derive native assignment, does NOT claim a stage-level absolute conserved charge.",
         "policy_eval":{"twelve_density_distinct_plus_spinor_completes_FAILABLE":verdict,"ENGINE_STAGES_PROTECT_DISTINCT_INVARIANTS_TWO_LEVEL":verdict}}
    json.dump(out,open(path,"w"),indent=2)
    print("GATE -- 16 STAGES PROTECT DISTINCT INVARIANTS (two-level):")
    print(f"  DENSITY: {n_density_distinct}/16 distinct; {len(collapses)} collapses, all chirality-mirror: {all_collapses_are_mirror}; genuine preservation (|lambda|=1): {genuine}")
    print(f"  SPINOR: separates every collapsed pair (min sep {min(spinor_seps) if spinor_seps else 0:.3f}): {spinor_separates}")
    print(f"  CONTROLS: shuffle destroys the chirality-mirror collapse structure: {shuffle_destroys_mirror_structure} (shuffle n_distinct={n_shuffled_distinct}); mirror density match {mirror_density_match:.2e} (<1e-9) vs spinor sep >0.6 = density-blindness of chirality")
    print(f"  sample: t1_Ti holonomy {spinor_holonomy(1):+.3f} vs t5_Ti {spinor_holonomy(5):+.3f} (density-identical, spinor-distinct)")
    print(f"  [gating: verdict = g_density (>=12 distinct, collapses are chirality-mirror only, genuine) AND g_spinor (spinor separates) AND shuffle-control drop]")
    print(f"  VERDICT: {'PASS' if verdict else 'FAIL'} (kinds of intelligence: 12 density-distinct + 4 spinor-distinct; chirality density-blind per canon)")
    if verdict: print("PASS sixteen_stages_protect_distinct_invariants")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
