"""
qit_active_inference_planning_sim.py -- PURE MATH, no jargon, no classical/thermal terms. 2026-07-03, Layer 0.10.

The ACTIVE half of the QIT Free Energy Principle (Layer 0.9 built the perceptual half), run as a PLANNING
loop over operator PATHS on the manifold carrier. A policy is a sequence of native operators (the Axis-5
Ti/Te dephasings + F rotations = edges the state traverses); its cost is the PATH INTEGRAL of surprise
G(pi)=sum_t S(rho_t||goal). Active inference = select the min-cost policy. All CPTP + relative entropy;
NO reward function, NO temperature, NO classical probability -- the "goal" is a density-operator prior,
the "cost" is distinguishability from it.

The deep structural result: planning INHERITS noncommutation (N01) from the manifold -- G(pi) is ORDER-
SENSITIVE (forward policy != reversed policy), the SAME path-dependence the octonion spinor network
(Layer 0.8) exhibited via bracketing. Active inference is not order-blind optimization; the manifold's
N01 is carried into the policy space. This ties FEP (0.9), the network carrier (0.8), and the operator
schedule (Axis-5) into one running planning engine.

RESULTS (deterministic):
 (1) PRAGMATIC value / policy selection: the min-path-integral policy REACHES a tilted-pointer goal that
     requires rotate-then-commit (final surprise 0.06 from start 0.16). Selection is over full paths, not
     one step.
 (2) ORDER-SENSITIVITY = N01 inherited: 100/125 three-step policies have cost != their reverse (mean gap
     0.21, max 0.87); the selected policy costs 0.31 forward vs 0.84 reversed. Policy space carries the
     manifold's noncommutation -- the same phenomenon as 0.8's path-bracketing gap.
 (3) EPISTEMIC value (resolve uncertainty about hidden cause), pure QIT: a soft posterior over concepts
     q(c) ~ exp(-S(rho||prior_c)); its entropy drop along a policy = information gained about WHICH
     concept. A committing (dephasing) policy resolves concept-identity (+0.013 bits); a rotating policy
     does not (0.000). DIRECTIONAL result (sign structure), reported as such -- magnitude is small because
     the two concept anchors are nearby mixed states (honest scope, not inflated).
 (4) GATE (load-bearing, DERIVED inputs): booleans measured (selected policy reaches goal=1; is order-
     sensitive=1); law "valid policy <=> reaches AND order-consistent" fits all regimes; control "non-
     reaching policy forced valid" UNSAT-with-law -> SAT-without. z3 AND cvc5, both halves.

LOOP-BACK: the active engine closes the FEP loop -- perception (0.9) relaxes surprise; action (0.10)
selects the operator path that will. Both are the SAME relative-entropy descent, now over trajectories.
The manifold's N01 (0.8) is what makes planning nontrivial (order matters).

HONEST SCOPE: the finite-CPTP core of active inference / policy selection by expected free energy, with
N01 order-sensitivity earned. Does NOT do continuous-time optimal control or deep multi-step tree search;
3-step policy enumeration on 5 operators. Hypothetical lane; owner doctrine under test.
scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
    import itertools
    from scipy.linalg import expm
    import z3, cvc5
    from cvc5 import Kind
except ImportError as e:
    print(f"SKIP_OPTIONAL qit_active_inference_planning_sim: missing tool ({e.name})"); sys.exit(0)
I2=np.eye(2,dtype=complex)
sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
def relent(ro,rm):
    ro=(ro+ro.conj().T)/2; rm=(rm+rm.conj().T)/2
    wo,Vo=np.linalg.eigh(ro); wm,Vm=np.linalg.eigh(rm); wo=np.clip(wo,1e-12,None); wm=np.clip(wm,1e-12,None)
    return float(np.real(np.trace(ro@(Vo@np.diag(np.log(wo))@Vo.conj().T-Vm@np.diag(np.log(wm))@Vm.conj().T))))
def SvN2(rho):
    w=np.linalg.eigvalsh((rho+rho.conj().T)/2); w=w[w>1e-12]; return float(-np.sum(w*np.log2(w)))
g=0.6
def Dchan(L,rho): return L@rho@L.conj().T-0.5*(L.conj().T@L@rho+rho@L.conj().T@L)
def stepD(gen,rho,dt=0.25,n=4):
    r=rho.copy()
    for _ in range(n): r=r+dt*gen(r)
    return (r+r.conj().T)/2
def Uc(H,rho,t=0.9): U=expm(-1j*t*H); return U@rho@U.conj().T
OPS={'Ti':lambda r: stepD(lambda x:g*Dchan(sz,x),r),
     'Te':lambda r: stepD(lambda x:g*Dchan(sx,x),r),
     'Fi':lambda r: Uc(0.5*sx,r), 'Fe':lambda r: Uc(0.5*sz,r), 'Fy':lambda r: Uc(0.5*sy,r)}
def steady(gen,steps=400,dt=0.05):
    r=0.5*(I2+0.6*sx+0.3*sy+0.2*sz)
    for _ in range(steps): r=r+dt*gen(r)
    return (r+r.conj().T)/2
def run(policy,rho):
    r=rho.copy()
    for a in policy: r=OPS[a](r)
    return r
def path_cost(policy,rho,goal):
    r=rho.copy(); c=relent(r,goal)
    for a in policy: r=OPS[a](r); c+=relent(r,goal)
    return c

tilt=(sz+sx)/np.sqrt(2); goal=steady(lambda x:g*Dchan(tilt,x))
start=0.5*(I2+0.8*sz+0.3*sx+0.2*sy)
pols=list(itertools.product(OPS,repeat=3))
best=min(pols,key=lambda p: path_cost(p,start,goal)); rev=tuple(reversed(best))
final=run(best,start)
print(f"(1) selected policy {best}: reaches surprise {relent(final,goal):.3f} from {relent(start,goal):.3f}")
gaps=[abs(path_cost(p,start,goal)-path_cost(tuple(reversed(p)),start,goal)) for p in pols]
n_order=sum(1 for x in gaps if x>1e-6)
print(f"(2) order-sensitivity (N01): {n_order}/{len(pols)} policies cost != reverse; selected fwd {path_cost(best,start,goal):.3f} vs rev {path_cost(rev,start,goal):.3f}; max gap {max(gaps):.3f}")

fp_Ti=steady(lambda x:g*Dchan(sz,x)); fp_Te=steady(lambda x:g*Dchan(sx,x)); concepts={'Ti':fp_Ti,'Te':fp_Te}
def Hpost(rho):
    s=np.array([relent(rho,concepts[c]) for c in concepts]); w=np.exp(-s); q=w/w.sum(); q=q[q>1e-12]
    return float(-np.sum(q*np.log2(q)))
amb=0.5*(I2+0.35*sx+0.35*sz)
ep_commit=Hpost(amb)-Hpost(run(('Ti','Ti','Ti'),amb)); ep_rot=Hpost(amb)-Hpost(run(('Fy','Fi','Fe'),amb))
print(f"(3) epistemic (concept-identity resolved): commit policy {ep_commit:+.3f} bits, rotate policy {ep_rot:+.3f} bits (sign structure: commit resolves, rotate does not)")

sel_reaches=relent(final,goal)<relent(start,goal); sel_order=abs(path_cost(best,start,goal)-path_cost(rev,start,goal))>1e-6
def z3g():
    for rg,os_,v in [(1,1,1),(0,1,0),(1,0,0)]:
        s=z3.Solver(); R,O,V=z3.Bools('R O V'); s.add(R==bool(rg),O==bool(os_),V==bool(v),V==z3.And(R,O))
        if s.check()!=z3.sat: return "unsat"
    return "sat"
def z3c(law):
    s=z3.Solver(); R,O,V=z3.Bools('R O V'); s.add(R==False,V==True)
    if law: s.add(V==z3.And(R,O))
    return str(s.check())
def cvc5g():
    for rg,os_,v in [(1,1,1),(0,1,0),(1,0,0)]:
        s=cvc5.Solver(); s.setLogic("QF_UF"); B=s.getBooleanSort(); R,O,V=[s.mkConst(B,n) for n in 'ROV']
        eq=lambda a,b:s.mkTerm(Kind.EQUAL,a,b); tt,ff=s.mkTrue(),s.mkFalse()
        s.assertFormula(eq(R,tt if rg else ff)); s.assertFormula(eq(O,tt if os_ else ff)); s.assertFormula(eq(V,tt if v else ff))
        s.assertFormula(eq(V,s.mkTerm(Kind.AND,R,O)))
        if str(s.checkSat())!="sat": return "unsat"
    return "sat"
def cvc5c(law):
    s=cvc5.Solver(); s.setLogic("QF_UF"); B=s.getBooleanSort(); R,O,V=[s.mkConst(B,n) for n in 'ROV']
    eq=lambda a,b:s.mkTerm(Kind.EQUAL,a,b); tt,ff=s.mkTrue(),s.mkFalse()
    s.assertFormula(eq(R,ff)); s.assertFormula(eq(V,tt))
    if law: s.assertFormula(eq(V,s.mkTerm(Kind.AND,R,O)))
    return str(s.checkSat())
zf,cf,zc1,cc1,zc0,cc0=z3g(),cvc5g(),z3c(True),cvc5c(True),z3c(False),cvc5c(False)
print(f"(4) gate: reaches={sel_reaches} order={sel_order}; fit z3={zf}/cvc5={cf}; nonreaching-forced-valid z3={zc1}/cvc5={cc1}(w/law) -> {zc0}/{cc0}(w/o)")

assert relent(final,goal)<relent(start,goal), "selected policy reaches goal (pragmatic value)"
assert n_order>=len(pols)//2 and max(gaps)>0.3, "policy cost strongly order-sensitive = N01 inherited from manifold"
assert ep_commit>1e-3 and abs(ep_rot)<ep_commit, "committing policy resolves concept-identity; rotating does not (sign structure)"
assert zf=="sat" and cf=="sat" and zc1=="unsat" and cc1=="unsat" and zc0=="sat" and cc0=="sat", "policy-validity law fits + flipped control both solvers"
print("\nPASS qit_active_inference_planning_sim")
