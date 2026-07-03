"""
distinguishability_engine_core_sim.py -- THE MODEL CORE. This engages the owner's INTEGRATED model
(OWNER_THESIS_AND_COSMOLOGY.md + CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md) as ONE object rather
than as isolated keyword-demos. The primitive is CONSTRAINT ON DISTINGUISHABILITY -- a finite
quotient Q = S/~_M where s1 ~_M s2 iff every measurement in M agrees. ENTROPY IS A LATER MEASURE,
NOT THE SUBSTANCE (this corrects an earlier sim that wrongly made entropy primitive).

The core mechanism is a=a iff a~b made DYNAMICAL on the Hopf carrier (doc sections 2-3, "verified
against sim results"): the SAME carrier C^2 -> S^3 has two loop placements --
  - FIBER loop (vertical, vary global phase): DENSITY-STATIONARY. The Hopf image depends only on
    fiber-invariant quantities, so the density matrix does not move -> creates NO distinguishability.
    The fiber IS the ~_M equivalence class (a ~ a).
  - BASE loop (horizontal, vary chi): DENSITY-TRAVERSING. The off-diagonal phase rotates -> the
    density matrix moves -> distinguishability is CREATED. The base crosses equivalence classes
    (a !~ b). This is where identity emerges and where the ratchet engages.
The Berry holonomy of the base loop IS the distinguishability created per loop: gamma =
-pi(1-|cos 2eta|), zero on the fiber, maximal (|gamma|=pi) at the Clifford torus (great circle).

FOUR results:
 (A) FIBER vs BASE: fiber loop trace-distance drift ~1e-16 (density-stationary, a~a); base loop
     trace-distance travel 0.93 (density-traversing, a!~b). a=a iff a~b, geometrized.
 (B) BERRY HOLONOMY = distinguishability created: numeric solid-angle holonomy matches the doc's
     closed form -pi(1-|cos2eta|) FOR THE INNER TORI eta<=pi/4 (north-cap reference in the solid-
     angle sum). For outer tori eta>pi/4 the same sum returns the COMPLEMENTARY cap and diverges from
     the closed form -- a reference-convention artifact of solid_angle(), not a physics discrepancy;
     the analytic form is symmetric about the Clifford torus. Checked at eta=pi/8 (-0.920) and the
     Clifford great circle eta=pi/4 (-pi, the max). Zero on
     the fiber, maximal at the Clifford great circle.
 (C) ONTOLOGY (the correction): along the base loop the state stays PURE (von Neumann S=0) while
     trace-distance (distinguishability) grows to 0.93. DISTINGUISHABILITY WITHOUT ENTROPY -> entropy
     is a downstream measure, not the primitive substance.
 (D) STRUCTURAL GATE (load-bearing): the solver inputs are DERIVED FROM THE MEASURED DYNAMICS
     (fib_drift, base_travel) -- NOT hardcoded. Measured booleans: fiber (stationary=1, created=0),
     base (stationary=0, created=1). The single structural law "stationary => not created" FITS the
     measured data on both loops (SAT). CONTROL: assert the MEASURED-stationary fiber ALSO created
     distinguishability -- UNSAT with the law present, SAT once the law is dropped, so the law (not
     arithmetic) is what bites. z3 AND cvc5, both the fit and the flipped control.

Tools: numpy (Hopf geometry, trace distance, von Neumann entropy, Berry solid angle -- control lane)
+ z3 + cvc5 (fiber/base structural gate, load-bearing). scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
    import z3, cvc5
    from cvc5 import Kind
except ImportError as e:
    print(f"SKIP_OPTIONAL distinguishability_engine_core_sim: missing tool ({e.name})"); sys.exit(0)

def psi(phi,chi,eta): return np.array([np.exp(1j*(phi+chi))*np.cos(eta), np.exp(1j*(phi-chi))*np.sin(eta)])
def rho(ps): return np.outer(ps,ps.conj())
def hopf(ps):
    z1,z2=ps; return np.array([2*(z1*z2.conj()).real, 2*(z1*z2.conj()).imag, abs(z1)**2-abs(z2)**2])
def tdist(r1,r2): return 0.5*np.linalg.norm(r1-r2)
def SvN(r):
    w=np.linalg.eigvalsh((r+r.conj().T)/2); w=w[w>1e-12]; return float(-np.sum(w*np.log2(w)))
def solid_angle(curve):
    c=[v/np.linalg.norm(v) for v in curve]; a=np.array([0,0,1.0]); Om=0.0
    for i in range(len(c)):
        b=c[i]; d=c[(i+1)%len(c)]
        Om+=2*np.arctan2(np.dot(a,np.cross(b,d)), 1+np.dot(a,b)+np.dot(b,d)+np.dot(d,a))
    return Om

eta=0.6; phi0,chi0=0.3,0.7; u=np.linspace(0,2*np.pi,200); u1=np.linspace(0,np.pi,300)
fib=[hopf(psi(phi0+t,chi0,eta)) for t in u]; fib_drift=max(tdist(fib[0],p) for p in fib)
base_ps=[psi(phi0,chi0+t,eta) for t in u1]; base=[hopf(p) for p in base_ps]
base_travel=max(tdist(base[0],p) for p in base)
print(f"(A) fiber drift={fib_drift:.2e} (stationary, a~a); base travel={base_travel:.3f} (traversing, a!~b)")

berry_pi8=-0.5*solid_angle([hopf(psi(phi0,chi0+t,np.pi/8)) for t in u1])
berry_cliff=-0.5*solid_angle([hopf(psi(phi0,chi0+t,np.pi/4)) for t in u1])
an_pi8=-np.pi*(1-abs(np.cos(2*np.pi/8))); an_cliff=-np.pi*(1-abs(np.cos(np.pi/2)))
print(f"(B) Berry holonomy: inner(pi/8) numeric={berry_pi8:+.3f} analytic={an_pi8:+.3f}; Clifford numeric={berry_cliff:+.3f} analytic={an_cliff:+.3f}")

S_along=[SvN(rho(p)) for p in base_ps]; dist_along=[tdist(base[0],hopf(p)) for p in base_ps]
print(f"(C) ontology: base-loop max distinguishability={max(dist_along):.3f}, max entropy S={max(S_along):.2e} (distinguishability WITHOUT entropy)")

# (D) STRUCTURAL GATE (load-bearing): the solver inputs are DERIVED FROM THE MEASURED DYNAMICS above
# (fib_drift, base_travel), not hardcoded. Measured booleans per loop: st = "density-stationary"
# (measured trace-distance drift < tol); cr = "created distinguishability" (measured drift > 0.5).
tol=1e-9
st_fib,cr_fib=int(fib_drift<tol),int(fib_drift>0.5)     # from the FIBER-loop measurement
st_bas,cr_bas=int(base_travel<tol),int(base_travel>0.5) # from the BASE-loop measurement
LAW="stationary => not created"
def z3_fit():   # does the single structural law fit BOTH measured loops? (UNSAT if a stationary loop had created)
    s=z3.Solver(); s1,c1,s2,c2=z3.Ints('s1 c1 s2 c2')
    s.add(s1==st_fib,c1==cr_fib,s2==st_bas,c2==cr_bas)
    s.add(z3.Implies(s1==1,c1==0),z3.Implies(s2==1,c2==0)); return str(s.check())
def z3_ctrl(with_law):  # counterfactual: the MEASURED-stationary fiber ALSO creates distinguishability
    s=z3.Solver(); st,cr=z3.Ints('st cr'); s.add(st==st_fib)   # st from fib_drift measurement
    if with_law: s.add(z3.Implies(st==1,cr==0))
    s.add(cr==1); return str(s.check())
def cvc5_fit():
    s=cvc5.Solver(); s.setLogic("QF_LIA"); I=s.getIntegerSort(); mk=s.mkInteger
    s1,c1,s2,c2=[s.mkConst(I,n) for n in('s1','c1','s2','c2')]; eq=lambda a,b:s.mkTerm(Kind.EQUAL,a,b)
    imp=lambda a,b:s.mkTerm(Kind.IMPLIES,a,b)
    for v,val in ((s1,st_fib),(c1,cr_fib),(s2,st_bas),(c2,cr_bas)): s.assertFormula(eq(v,mk(val)))
    s.assertFormula(imp(eq(s1,mk(1)),eq(c1,mk(0)))); s.assertFormula(imp(eq(s2,mk(1)),eq(c2,mk(0))))
    return str(s.checkSat())
def cvc5_ctrl(with_law):
    s=cvc5.Solver(); s.setLogic("QF_LIA"); I=s.getIntegerSort(); mk=s.mkInteger
    st,cr=[s.mkConst(I,n) for n in('st','cr')]; eq=lambda a,b:s.mkTerm(Kind.EQUAL,a,b)
    s.assertFormula(eq(st,mk(st_fib)))
    if with_law: s.assertFormula(s.mkTerm(Kind.IMPLIES,eq(st,mk(1)),eq(cr,mk(0))))
    s.assertFormula(eq(cr,mk(1))); return str(s.checkSat())
zfit,cfit=z3_fit(),cvc5_fit()
zc1,cc1=z3_ctrl(True),cvc5_ctrl(True)      # law present: forbidden -> UNSAT (because fiber measured stationary)
zc0,cc0=z3_ctrl(False),cvc5_ctrl(False)    # law dropped: allowed  -> SAT (law is what bites, not arithmetic)
print(f"(D) gate: data fits law z3={zfit}/cvc5={cfit} (sat); stationary-fiber-creates z3={zc1}/cvc5={cc1} (unsat w/law) -> {zc0}/{cc0} (sat w/o law)")

assert fib_drift<1e-9 and base_travel>0.5, "fiber density-stationary, base density-traversing (a=a iff a~b geometrized)"
assert abs(berry_pi8-an_pi8)<0.01 and abs(berry_cliff-an_cliff)<0.01, "Berry holonomy matches doc closed form"
assert max(dist_along)>0.5 and max(S_along)<1e-9, "distinguishability created with zero entropy (entropy is a later measure)"
assert st_fib==1 and cr_fib==0 and st_bas==0 and cr_bas==1, "measured booleans derived from dynamics (fiber stationary/no-create, base moving/create)"
assert zfit=="sat" and cfit=="sat", "the single structural law FITS the measured data on both loops (z3+cvc5)"
assert zc1=="unsat" and cc1=="unsat" and zc0=="sat" and cc0=="sat", "control flips: measured-stationary fiber cannot have created (UNSAT w/law), SAT once law dropped (z3+cvc5 both halves)"
print("\nPASS distinguishability_engine_core_sim")
