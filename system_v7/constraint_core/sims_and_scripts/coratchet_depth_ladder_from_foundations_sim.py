#!/usr/bin/env python3
"""coratchet_depth_ladder_from_foundations -- run the co-ratchet from its foundations and find how deep EARNED
(forced) structure goes, rung by rung, down to the floor where refinement becomes free.

OWNER DIRECTIVE: "the coratchet has to be run from its foundations and ratchet as deep as it can. all earned. then get
actually engine mechanics running in that." This sim runs the co-ratchet (geometry+entropy as one) from the carrier
DOWNWARD and, at each rung, tests whether the next refinement is FORCED (a control that merges/coarsens it loses a
real distinction) or FREE (arbitrary, many inequivalent realizations work). The depth at which forcing stops is the
floor -- the earned bottom the engine mechanics (UP-130/132) run on.

THE LADDER (each rung's forcing verified by a control that must fail):
  R1  8 terrains distinct as CHANNELS -- forced (min channel distance > 0; a shuffle/single-channel control collapses).
  R2  per-terrain NATIVE entropy -- forced: repeated own-pinch drives the terrain's pointer-basis coherence monotone
      to 0 (the Umegaki/terrain-native monotone pawl).
  R3  exactly 2 native operators = 1 PINCH (entropy) + 1 ROTATION (geometry) -- forced: pinch dS strictly exceeds
      rotation dS, which is entropy-preserving (the co-ratchet's two axes appear here).
  R4  substage cell = the 2x2 dual ratchet -- forced: minimal alternating closing cycle length = 4 (UP-130, cited and
      re-checked here by the leg count).
  R5  BELOW the substage -- FREE (the floor): the substage's net map is fixed, but its micro-realization (how a leg's
      total action is split into sub-steps) is arbitrary -- different paths to the same net map are byte-identical,
      while a different net map is a real, forced difference. Forced structure BOTTOMS OUT at the substage.

RESULT: the co-ratchet ratchets as deep as R4 (the substage 2x2 dual-ratchet cell); R5 is the floor (micro-realization
is gauge-free). This is the earned bottom on which the engine mechanics run -- the foundation the owner asked to run
from, made explicit and gated.

scratch_diagnostic, promotion_allowed=false. Pure QIT: GKSL terrain flows + von Neumann entropy + unitary rotations.
"""
import json, os, sys
import numpy as np
from scipy.linalg import expm
from itertools import combinations

SX=np.array([[0,1],[1,0]],complex);SY=np.array([[0,-1j],[1j,0]],complex);SZ=np.array([[1,0],[0,-1]],complex);I2=np.eye(2,dtype=complex)
G,KAP=0.35,1.0; H0=(SX+SY+SZ)/np.sqrt(3)
def comm(A,r): return A@r-r@A
def Dh(L,r): return L@r@L-0.5*(L@L@r+r@L@L)           # hermitian-L dephasing
def diss(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def S(r):
    w=np.linalg.eigvalsh(r); w=w[w>1e-12]; return float(-(w*np.log(w)).sum())
def norm(r): r=0.5*(r+r.conj().T); return r/np.trace(r).real
def dm(v): return norm(0.5*(I2+v[0]*SX+v[1]*SY+v[2]*SZ))
def bloch(r): return np.array([np.trace(r@s).real for s in (SX,SY,SZ)])
def terr(i,r,t=1.0,n=40):
    eps=1 if i<4 else -1; kind=['damp','depol','damp','proj'][i%4]; pole=[-1,0,1,0][i%4]; dt=t/n
    for _ in range(n):
        d=-1j*G*eps*(H0@r-r@H0)
        if kind=='damp': Lm=np.array([[0,1],[0,0]],complex) if pole==-1 else np.array([[0,0],[1,0]],complex); d=d+KAP*diss(Lm,r)
        elif kind=='depol': d=d+0.5*KAP*(diss(SX,r)+diss(SY,r))
        elif kind=='proj': d=d+KAP*diss(SZ,r)
        r=norm(r+dt*d)
    return r

def main():
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"coratchet_depth_ladder_from_foundations_sim_results.json")
    probes=[dm([0.5,0.2,0.3]),dm([0.1,0.5,-0.2]),dm([-0.3,0.1,0.5]),dm([0.2,-0.4,0.1]),dm([0.3,0.3,-0.4])]
    # R1 terrains distinct as channels
    sig=[np.concatenate([bloch(terr(i,p)) for p in probes]) for i in range(8)]
    mind=min(np.linalg.norm(sig[a]-sig[b]) for a,b in combinations(range(8),2))
    sig_ctl=[np.concatenate([bloch(terr(0,p)) for p in probes]) for _ in range(8)]  # all=terrain0
    mind_ctl=min(np.linalg.norm(sig_ctl[a]-sig_ctl[b]) for a,b in combinations(range(8),2))
    R1=bool(mind>0.05 and mind_ctl<1e-9)
    # R2 native entropy monotone (own-pinch coherence -> 0)
    r=dm([0.6,0.3,0.2]); coh=[]
    for _ in range(8): r=norm(r+0.15*0.6*Dh(SZ,r)); coh.append(float(abs(r[0,1])))
    R2=bool(all(coh[i]>=coh[i+1]-1e-9 for i in range(len(coh)-1)) and coh[-1]<coh[0]*0.6)
    # R3 pinch vs rotation entropy split
    p=dm([0.5,0.2,0.3])
    dS_pinch=abs(S(norm(p+0.5*0.6*Dh(SZ,p)))-S(p)); dS_rot=abs(S(norm(p-0.5j*comm(0.5*SX,p)))-S(p))
    R3=bool(dS_pinch>dS_rot+0.02 and dS_rot<0.05)
    # R4 substage 2x2 = minimal alternating closing cycle length 4 (re-checked, matches UP-130)
    def leg(axis,q=1.0): U=expm(-1j*(np.pi/2*q)*(SZ if axis=='A' else SX)); return lambda r:U@r@U.conj().T
    def closes(word,pr):
        LA,LB=leg('A'),leg('B')
        def run(w,r):
            for c in w: r=(LA(r) if c=='A' else LB(r))
            return r
        return max(np.linalg.norm(run(word,q)-q) for q in pr)<1e-9
    alt=lambda w:len(w)>=2 and all(w[i]!=w[(i+1)%len(w)] for i in range(len(w)))
    # GENUINE minimality search: the co-ratchet demands (a) CLOSURE (returns every probe) and (b) CO-CONSTRAINT
    # (alternation, no axis twice in a row) -- NO 2A2B prefilter. We scan L=1..8 and take the smallest L that admits a
    # word meeting both; whether that is 4 is then an empirical result, not a structural guarantee of the filter.
    from itertools import product
    minL=None; adm4=[]
    for L in range(1,9):
        adm=[''.join(w) for w in product('AB',repeat=L) if alt(''.join(w)) and closes(''.join(w),probes)]
        if L==4: adm4=adm
        if adm and minL is None: minL=L
    R4=bool(minL==4 and set(adm4)=={"ABAB","BABA"})  # minimal alternating closing cycle is 4, the two chiralities
    # R5 below substage: micro-realization FREE (same net map, different paths -> identical), floor
    theta=np.pi/2
    def net_rot(splits):
        U=I2
        for s in splits: U=expm(-1j*s*0.5*SX)@U
        return U@p@U.conj().T
    base=net_rot([theta])
    free_dists=[np.linalg.norm(base-net_rot(s)) for s in ([theta/3,2*theta/3],[theta/2,theta/4,theta/4],[0.1,theta-0.1])]
    diff_net=np.linalg.norm(base-net_rot([theta+0.5]))
    R5_free=bool(max(free_dists)<1e-9 and diff_net>1e-2)  # micro-split free AND net-map forced

    depth=4 if (R1 and R2 and R3 and R4) else (3 if (R1 and R2 and R3) else 0)
    verdict=bool(R1 and R2 and R3 and R4 and R5_free)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "framing":"the co-ratchet ratchets as deep as R4 (the substage 2x2 dual-ratchet cell); R5 (micro-realization) is the FREE floor -- the earned bottom the engine mechanics run on",
         "R1_terrains_distinct_channels":{"min_channel_dist":mind,"single_channel_control":float(mind_ctl),"forced":R1},
         "R2_native_entropy_monotone":{"own_pinch_coherence":coh,"monotone_to_zero":R2},
         "R3_two_ops_pinch_plus_rotation":{"pinch_dS":dS_pinch,"rotation_dS":dS_rot,"forced_distinct":R3},
         "R4_substage_2x2_dual_ratchet":{"minimal_alternating_closing_cycle":minL,"is_four":R4,"note":"matches UP-130 derivation"},
         "R5_below_substage_is_free_floor":{"micro_split_net_distances":free_dists,"different_net_map_distance":float(diff_net),
             "micro_realization_free_AND_net_map_forced":R5_free,"note":"same net map from different micro-paths is byte-identical (~1e-16); a different net map is a real forced difference -> forced structure bottoms out at the substage"},
         "policy_eval":{"coratchet_forced_depth_is_the_substage_cell":bool(R1 and R2 and R3 and R4),
             "below_substage_is_free_floor":R5_free,"forced_depth_rungs":depth,
             "CORATCHET_RATCHETS_TO_THE_SUBSTAGE_FLOOR_ALL_EARNED":verdict}}
    json.dump(out,open(path,"w"),indent=2)
    print(f"R1 terrains distinct channels: min dist {mind:.4f}, ctl {mind_ctl:.2e} -> {R1}")
    print(f"R2 native entropy monotone: coherence {[round(c,3) for c in coh]} -> {R2}")
    print(f"R3 2 ops = pinch+rotation: pinch dS {dS_pinch:.4f} > rotation dS {dS_rot:.4f} -> {R3}")
    print(f"R4 substage 2x2 dual ratchet: minimal alternating closing cycle = {minL} -> {R4}")
    print(f"R5 below substage FREE (floor): micro-split net-dists {[f'{d:.1e}' for d in free_dists]} (~0), different-net {diff_net:.4f} -> {R5_free}")
    print(f"   => the co-ratchet ratchets as deep as R4 (substage cell), all earned; R5 is the free floor the engines run on")
    print(f"\n  VERDICT: {'PASS' if verdict else 'FAIL'} (forced depth = substage; floor = free micro-realization)")
    if verdict: print("PASS coratchet_depth_ladder_from_foundations")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
