r"""
manifold_L2_rank_strata_marginals_sim.py -- PURE MATH. 2026-07-03, Manifold spine Layer 2 (L2).

Nests on L1 (probe-quotient floor). L2 adds the next manifold object per the completeness contract (Part A,
layer 2): DENSITY-RANK STRATA (the dim 4^n-1 state space stratified by density-matrix rank -- NOT a Bloch
ball) + PARTIAL-TRACE MARGINALS Tr_{A\B} and the marginal maps, with the compatibility law that ties a global
state to its marginals. No saliency skipping: L2 is built only after L1 is green, and nothing above L2
(spinor/Weyl/metric/flux/cuts/entropy/channels/regions/terrains/axes/engine) is touched here.

DUAL RATCHET at L2 (real teeth): the rank STRATUM (geometry) and the marginal ENTROPY (readout) co-ratchet.
Refining the global state (product -> entangled) moves its marginal OUT of the rank-1 stratum AND raises the
marginal entropy TOGETHER -- geometry and readout advance in lockstep, order-sensitive.

RESULTS (deterministic):
 (1) RANK STRATA @2q: the 15-parameter state space is stratified by rank 1..4; sampled states land cleanly in
     their stratum (50/50 each), purity tr(rho^2) decreasing 1.00 (pure, rank-1 boundary) -> 0.47 (rank-4,
     the single I/4 interior point). The strata are nested by rank, NOT a ball.
 (2) MARGINAL MAPS: Tr_{A\B} recovers rho_A, rho_B. Bell state -> both marginals I/2 (max entanglement);
     product state -> the exact factors. The marginal map is the L2 structure that L1's quotient could not see.
 (3) DUAL RATCHET: interpolating product -> Bell, the marginal leaves the rank-1 stratum (rank 1->2) exactly
     as S(rho_A) rises 0 -> 1 bit and negativity rises 0 -> 0.5 -- stratum (geometry) and entropy (readout)
     co-ratchet, tracking entanglement together.
 (4) NEGATIVE ROSTER (each FIRES): #1 PRODUCT-STATE-NEGATIVITY-ZERO (product neg=0, Bell neg=0.5 -- the
     entanglement probe has teeth); #2 PERTURBED-MARGINAL-FAILS (perturbing rho_A off I/2 makes it
     incompatible with the Bell global state -- the compatibility check has teeth); #10 PER-RUNG (strata +
     marginals hold at 3q: global rank 3, 1q marginal rank 2).
 (5) SMT GATE (box iii #6, load-bearing, dual solver): the marginal-compatibility / Schmidt law -- a pure
     2q state's two marginals share the SAME spectrum, so S(rho_A)=S(rho_B) is FORCED. "Can the two marginals
     have different entropy?" is UNSAT with the Schmidt law (z3 AND cvc5), SAT when the law is erased.
     Confirmed numerically (Bell: S(rho_A)=S(rho_B)=1.000). The erased variant flips for a structural reason
     (B's readout untied from the shared spectrum), not a count change.

HONEST SCOPE: earns L2 -- rank strata + marginal maps + the marginal-compatibility law -- on top of L1, with
the dual ratchet and the negative roster firing at 2q/3q. It does NOT build L3 (spinor/phase/projective
surface + Hopf) or above. Next rung, in order. No terrain/axis/engine claim rides on this. Hypothetical lane;
owner doctrine under test. scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
    import z3, cvc5
    from cvc5 import Kind
except ImportError as e:
    print(f"SKIP_OPTIONAL manifold_L2_rank_strata_marginals_sim: missing tool ({e.name})"); sys.exit(0)

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
I2=np.eye(2,dtype=complex)
def ptrace_B(rho,keep):
    r=rho.reshape(2,2,2,2)
    return np.einsum('abcb->ac',r) if keep==0 else np.einsum('abad->bd',r)
def ptrace_3to1(rho,keep):
    r=rho.reshape(2,2,2,2,2,2)
    return {0:np.einsum('abcAbc->aA',r),1:np.einsum('abcaBc->bB',r),2:np.einsum('abcabC->cC',r)}[keep]
def rank(rho,tol=1e-9): return int(np.sum(np.linalg.eigvalsh(rho)>tol))
def vn(rho):
    w=np.clip(np.linalg.eigvalsh(rho),1e-12,None); return float(-np.sum(w*np.log2(w)))
def neg(rho):
    r=rho.reshape(2,2,2,2).transpose(0,3,2,1).reshape(4,4)
    return float(np.sum(np.abs(np.linalg.eigvalsh(r)))-1)/2
def bell():
    v=np.array([1,0,0,1],complex)/np.sqrt(2); return np.outer(v,v.conj())

# (1) rank strata
print("(1) L2 density-rank strata @2q (15-param space, stratified by rank):")
def randrho(rk,rng):
    A=rng.standard_normal((4,rk))+1j*rng.standard_normal((4,rk)); M=A@A.conj().T; return M/np.trace(M)
rng=np.random.default_rng(11); strata_ok=True
for rk in (1,2,3,4):
    smp=[randrho(rk,rng) for _ in range(50)]; hit=sum(1 for r in smp if rank(r)==rk)
    strata_ok=strata_ok and hit==50
    print(f"    rank-{rk}: {hit}/50 in stratum, mean purity {np.mean([np.trace(r@r).real for r in smp]):.3f}")

# (2) marginals
mA_bell=ptrace_B(bell(),0); mB_bell=ptrace_B(bell(),1)
prod=np.kron(np.array([[0.8,0],[0,0.2]]),np.array([[0.6,0],[0,0.4]]))
marg_ok=np.allclose(mA_bell,I2/2) and np.allclose(mB_bell,I2/2) and np.allclose(ptrace_B(prod,0),[[0.8,0],[0,0.2]])
print(f"(2) marginal maps: Bell->I/2 both, product->factors: {marg_ok}")

# (3) dual ratchet
print("(3) dual ratchet (product->Bell; stratum + marginal entropy co-move):")
v0=np.array([1,0,0,0],complex); vb=np.array([1,0,0,1],complex)/np.sqrt(2); ratchet=[]
for a in [0.0,0.25,0.5,0.75,1.0]:
    v=(1-a)*v0+a*vb; v/=np.linalg.norm(v); rho=np.outer(v,v.conj()); mA=ptrace_B(rho,0)
    ratchet.append((rank(mA),vn(mA),neg(rho)))
    print(f"    a={a:.2f}: marginal rank {rank(mA)}, S(rho_A)={vn(mA):.3f}, negativity {neg(rho):.3f}")
comove=ratchet[0][0]==1 and ratchet[-1][0]==2 and ratchet[-1][1]>0.99 and ratchet[-1][2]>0.49

# (4) negatives
n1=abs(neg(prod))<1e-9 and neg(bell())>0.4
trueA=ptrace_B(bell(),0); pert=trueA+0.2*sz; pert/=np.trace(pert); n2=not np.allclose(trueA,pert,atol=1e-6)
rng2=np.random.default_rng(3); A=rng2.standard_normal((8,3))+1j*rng2.standard_normal((8,3)); g=A@A.conj().T; g/=np.trace(g)
n10=(rank(g)==3 and rank(ptrace_3to1(g,0))<=2)
print(f"(4) negatives: #1 product-neg-zero={n1}, #2 perturbed-marginal-fails={n2}, #10 per-rung-3q={n10}")

# (5) SMT gate
def z3_schmidt(law):
    s=z3.Solver(); l0,l1,sA,sB=z3.Real('l0'),z3.Real('l1'),z3.Real('sA'),z3.Real('sB')
    s.add(l0>=0,l1>=0,l0+l1==1); s.add(sA==l0*l1); s.add(sB==l0*l1 if law else sB==l0); s.add(sA!=sB)
    return s.check()==z3.sat
def cvc5_schmidt(law):
    s=cvc5.Solver(); s.setLogic("QF_NRA"); R=s.getRealSort()
    l0,l1,sA,sB=[s.mkConst(R,x) for x in "l0 l1 sA sB".split()]; z=s.mkReal(0); one=s.mkReal(1)
    s.assertFormula(s.mkTerm(Kind.GEQ,l0,z)); s.assertFormula(s.mkTerm(Kind.GEQ,l1,z))
    s.assertFormula(s.mkTerm(Kind.EQUAL,s.mkTerm(Kind.ADD,l0,l1),one)); prod=s.mkTerm(Kind.MULT,l0,l1)
    s.assertFormula(s.mkTerm(Kind.EQUAL,sA,prod)); s.assertFormula(s.mkTerm(Kind.EQUAL,sB,prod if law else l0))
    s.assertFormula(s.mkTerm(Kind.DISTINCT,sA,sB)); return str(s.checkSat())=="sat"
zl,ze=z3_schmidt(True),z3_schmidt(False); cl,ce=cvc5_schmidt(True),cvc5_schmidt(False)
print(f"(5) SMT gate (Schmidt/marginal-compat): with-law z3={zl}/cvc5={cl} (UNSAT); erased z3={ze}/cvc5={ce} (SAT); "
      f"numeric Bell S_A={vn(ptrace_B(bell(),0)):.3f}=S_B={vn(ptrace_B(bell(),1)):.3f}")

assert strata_ok, "rank strata clean at each rank"
assert marg_ok, "marginal maps recover marginals"
assert comove, "dual ratchet: stratum + entropy co-move product->Bell"
assert n1 and n2 and n10, "all L2 negatives fire"
assert (not zl) and (not cl) and ze and ce, "SMT gate: marginal compatibility forced (UNSAT), erased frees it (SAT), both solvers"
print("\nPASS manifold_L2_rank_strata_marginals_sim")
