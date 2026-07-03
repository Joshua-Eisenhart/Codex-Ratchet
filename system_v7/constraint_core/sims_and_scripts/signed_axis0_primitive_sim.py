"""
signed_axis0_primitive_sim.py -- PURE MATH, no jargon. 2026-07-02, Layer 0.3.

The signed Axis-0 primitive, built as its own foundational object and looped back into the axis-0
gravity layer (0.2). Source: ENTROPIC_MONISM_ORIGIN_AND_COSMOLOGY.md sec 8 ("Entanglement as carrier
| -S(A|B) kernel | Conditional entropy IS the entanglement measure") and the entropy-tables doc
(coherent information = the SIGNED primitive; mutual information = the unsigned companion). sec 5.4 /
4.1: positive entropy disperses (dark-energy/expansion regime), negative entropy binds (gravity/
dark-matter regime) -- "the same constraint acting in different contexts."

The primitive:
    I_c(A>B) = S(rho_B) - S(rho_AB) = -S(A|B)        (coherent information, SIGNED)
    I(A:B)   = S(rho_A) + S(rho_B) - S(rho_AB)       (mutual information, unsigned companion)

RESULTS (deterministic, seeded):
 (1) SIGNED vs UNSIGNED: Bell I_c=+1 / I=+2; product-mixed I_c=-0.88 / I=0; classical-correlation
     I_c=0 / I=+1. The sign of I_c distinguishes quantum binding from classical/dispersing; I(A:B)
     cannot (it is >=0 always).
 (2) STRUCTURAL THEOREM: across 4000 provably-separable states max I_c = -6e-6 (<=0); across 4000
     random entangled states I_c>0 for 100%. Positive I_c is a genuine entanglement witness -- and a
     STRICTER one than entanglement itself: a Werner state p*Bell+(1-p)I/4 is entangled for p>1/3 but
     has I_c>0 only for p>p*=0.7476 (the one-way/coherent boundary). Not all entanglement "binds."
 (3) LOOP-BACK TO GRAVITY (0.2) [DEMONSTRATION-ONLY profile]: a spatial chain of Werner cuts p(x) with a
     high-entanglement core. The core/halo entanglement profile p_x=0.30+0.68*exp(-((x-0.5)/0.13)^2) is a
     CONSTRUCTED Gaussian (a placed demonstration shape), NOT a derived profile. The MEASURED result is
     that I_c changes sign across it (core I_c>0 vs halo I_c<0); the profile itself is illustrative.
     The gravitational potential Phi(x) = -I_c(x) (the -S(A|B) binding kernel). The two regimes --
     binding core (I_c>0, ATTRACTIVE) and dispersing halo (I_c<0) -- are the two MEASURED SIGNS of one
     primitive, with the boundary at the physical threshold p*, NOT a hand-placed +/- (which the 0.2
     sim used as a stand-in). The attractive acceleration toward the core emerges from I_c>0.
 (4) STRUCTURAL GATE (load-bearing, DERIVED inputs): booleans from the measured core/halo signs; law
     "attractive-binding <=> I_c>0" fits (SAT); control "measured-dispersing halo also binds" is UNSAT
     with the law, SAT once dropped. z3 AND cvc5, fit + flipped control.

This RENDERS (hypothetical lane) the sign structure the 0.2 gravity layer asserted: its two regimes are the two signs of
the signed Axis-0 primitive, grounded in the owner's -S(A|B) kernel. Honest scope: still the entropic-
gravity MECHANISM (owner doctrine under test, sec 7 fence), not a derivation of GR.
scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
    import z3, cvc5
    from cvc5 import Kind
except ImportError as e:
    print(f"SKIP_OPTIONAL signed_axis0_primitive_sim: missing tool ({e.name})"); sys.exit(0)

def SvN(rho):
    w=np.linalg.eigvalsh(rho); w=w[w>1e-12]; return float(-np.sum(w*np.log2(w)))
def ptrace_B(rho): r=rho.reshape(2,2,2,2); return np.einsum('ikjk->ij',r)
def ptrace_A(rho): r=rho.reshape(2,2,2,2); return np.einsum('kikj->ij',r)
def coherent_info(rho): return SvN(ptrace_A(rho))-SvN(rho)     # I_c(A>B) = S(B)-S(AB)
def mutual_info(rho):   return SvN(ptrace_B(rho))+SvN(ptrace_A(rho))-SvN(rho)
def bell():
    v=np.array([1,0,0,1],complex)/np.sqrt(2); return np.outer(v,v.conj())
def werner(p): return p*bell()+(1-p)*np.eye(4,dtype=complex)/4

rng=np.random.default_rng(0)
def rpure(): v=rng.normal(size=2)+1j*rng.normal(size=2); v/=np.linalg.norm(v); return np.outer(v,v.conj())
def rsep():
    k=rng.integers(2,6); ps=rng.dirichlet(np.ones(k)); return sum(p*np.kron(rpure(),rpure()) for p,_ in zip(ps,range(k)))
def rent(): v=rng.normal(size=4)+1j*rng.normal(size=4); v/=np.linalg.norm(v); return np.outer(v,v.conj())
rA=np.array([[0.7,0],[0,0.3]],complex); rB=np.array([[0.6,0],[0,0.4]],complex); prodmix=np.kron(rA,rB)
classcorr=0.5*(np.diag([1,0,0,0]).astype(complex)+np.diag([0,0,0,1]).astype(complex))
print(f"(1) Bell I_c={coherent_info(bell()):+.3f}/I={mutual_info(bell()):+.3f}; prod-mix I_c={coherent_info(prodmix):+.3f}/I={mutual_info(prodmix):+.3f}; class-corr I_c={coherent_info(classcorr):+.3f}/I={mutual_info(classcorr):+.3f}")

sep_max=max(coherent_info(rsep()) for _ in range(4000)); ent_frac=np.mean([coherent_info(rent())>1e-9 for _ in range(4000)])
lo,hi=0.7,1.0
for _ in range(60):
    m=(lo+hi)/2
    if coherent_info(werner(m))>0: hi=m
    else: lo=m
pstar=(lo+hi)/2
print(f"(2) separable max I_c={sep_max:+.6f} (<=0); entangled frac I_c>0={ent_frac:.2f}; Werner I_c=0 at p*={pstar:.4f} (entangled from 1/3 -> stricter witness)")

xs=np.linspace(0,1,60); p_x=0.30+0.68*np.exp(-((xs-0.5)/0.13)**2)
Ic_x=np.array([coherent_info(werner(p)) for p in p_x]); Phi=-Ic_x; accel=-np.gradient(Phi,xs); mid=len(xs)//2
print(f"(3) loop-back: core I_c={Ic_x[mid]:+.3f} (binding), halo I_c={Ic_x[0]:+.3f} (dispersing); accel left-of-core={accel[mid-12]:+.3f} (attractive) -- sign is MEASURED, not imposed")

bind_core,bind_halo=int(Ic_x[mid]>0),int(Ic_x[0]>0)
def z3_fit():
    s=z3.Solver(); c,h=z3.Ints('c h'); s.add(c==bind_core,h==bind_halo,c==1,h==0); return str(s.check())
def z3_ctrl(law):
    s=z3.Solver(); h,a=z3.Ints('h a'); s.add(h==bind_halo)
    if law: s.add(a==h)
    s.add(a==1); return str(s.check())
def cvc5_fit():
    s=cvc5.Solver(); s.setLogic("QF_LIA"); I=s.getIntegerSort(); mk=s.mkInteger
    c,h=[s.mkConst(I,n) for n in('c','h')]; eq=lambda a,b:s.mkTerm(Kind.EQUAL,a,b)
    for v,val in ((c,bind_core),(h,bind_halo),(c,1),(h,0)): s.assertFormula(eq(v,mk(val))); 
    return str(s.checkSat())
def cvc5_ctrl(law):
    s=cvc5.Solver(); s.setLogic("QF_LIA"); I=s.getIntegerSort(); mk=s.mkInteger
    h,a=[s.mkConst(I,n) for n in('h','a')]; eq=lambda x,y:s.mkTerm(Kind.EQUAL,x,y)
    s.assertFormula(eq(h,mk(bind_halo)))
    if law: s.assertFormula(eq(a,h))
    s.assertFormula(eq(a,mk(1))); return str(s.checkSat())
zfit,cfit=z3_fit(),cvc5_fit(); zc1,cc1=z3_ctrl(True),cvc5_ctrl(True); zc0,cc0=z3_ctrl(False),cvc5_ctrl(False)
print(f"(4) gate: fit z3={zfit}/cvc5={cfit}; halo-binds z3={zc1}/cvc5={cc1}(w/law) -> {zc0}/{cc0}(w/o)")

assert coherent_info(bell())>0.99 and coherent_info(prodmix)<-0.5 and abs(coherent_info(classcorr))<1e-9, "I_c signs: entangled + / separable-mixed - / classical 0"
assert sep_max<=1e-6 and ent_frac>0.99, "positive I_c is a genuine entanglement witness (separable I_c<=0)"
assert 0.7<pstar<0.8, "Werner coherent-info threshold p* ~ 0.748 (stricter than entanglement)"
assert Ic_x[mid]>0 and Ic_x[0]<0 and accel[mid-12]>0, "two regimes = two measured signs of I_c; core attracts"
assert zfit=="sat" and cfit=="sat" and zc1=="unsat" and cc1=="unsat" and zc0=="sat" and cc0=="sat", "regime law fits; flipped control (z3+cvc5)"
print("\nPASS signed_axis0_primitive_sim")
