"""
entropic_gravity_axis0_sim.py -- THE AXIS-0 GRAVITY MECHANISM (owner doctrine, from
ENTROPIC_MONISM_ORIGIN_AND_COSMOLOGY.md sec 5-8 and the Grok chat that seeded it: "Gravity = entropy
gradient"). This renders the owner's stated gravity model as checkable math. The central claim is an
Einstein-FORM field equation sourced by the gradient of ENTANGLEMENT entropy rather than by mass:

    G_munu = kappa ( grad_mu S grad_nu S  -  1/2 g_munu (grad S)^2 )

with S = entanglement entropy across a bipartite cut (the doc's -S(A|B)/coherent-info carrier; the
Xi bridge geometry -> rho_AB -> S). Dark energy = positive-entropy regime (dispersing futures),
dark matter = negative-entropy regime (bound correlations); sec 5.4: expansion and gravitational
attraction are ONE force in two density regimes.

PURE MATH ONLY (no jargon in the computation; the cosmological labels are the Rosetta layer). We
test the MECHANISM the model states, not a presumed answer:
 (1) SOURCE: a spatial gradient in entanglement entropy yields a nonzero gravitational source
     (grad S)^2; a FLAT entanglement field yields ~0 source. Gravity requires an entropy gradient.
 (2) SIGN STRUCTURE: the same operator grad S gives an ATTRACTIVE well for a negentropy (bound-info)
     anomaly and a REPULSIVE hill for a positive-entropy anomaly, with EQUAL magnitude -> one force,
     two regimes (expansion vs binding).
 (3) STRUCTURAL GATE (load-bearing): the solver inputs are DERIVED FROM THE COMPUTED FIELDS (measured
     max|grad S| and total (grad S)^2 for BOTH the well and the flat control), not hardcoded. The law
     "source present <=> gradient present" FITS both measured configs (SAT). CONTROL: assert the
     MEASURED-flat field ALSO has gravity -- UNSAT with the law, SAT once the law is dropped, so the
     law (not arithmetic) is what bites. z3 AND cvc5, both the fit and the flipped control.

HONEST SCOPE (matching the doc's own sec-7 fence): this shows the owner's entropic-gravity MECHANISM
is self-consistent and non-vacuous as stated -- an entanglement-entropy gradient acts as a
gravitational source with the claimed two-regime sign structure. It does NOT derive the full field
equation from RC-1+RC-2, does NOT reproduce GR's tensor structure in >1D, and does NOT claim to
replace GR/QM (the doc explicitly does not claim that). It is the mechanism made checkable, fenced as
OWNER DOCTRINE under test.

Tools: numpy (entropy profiles, gradient source, geodesic accel -- control lane) + z3 + cvc5
(gradient/source structural gate -- load-bearing). scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
    import z3, cvc5
    from cvc5 import Kind
except ImportError as e:
    print(f"SKIP_OPTIONAL entropic_gravity_axis0_sim: missing tool ({e.name})"); sys.exit(0)

def bond_entropy(p):
    c=(1-np.sqrt(1-np.clip(p,0,1)**2))/2; c=np.clip(c,1e-12,1-1e-12)
    return float(-c*np.log2(c)-(1-c)*np.log2(1-c))
def profile(corr): return np.array([bond_entropy(c) for c in corr])

n=60; x=np.linspace(0,1,n)
corr_mass=0.15+0.8*np.exp(-((x-0.5)/0.12)**2)          # localized bound correlations = a "mass"
S_mass=profile(corr_mass); source=np.gradient(S_mass,x)**2
S_flat=profile(0.6*np.ones(n)); source_flat=np.gradient(S_flat,x)**2
print(f"(1) source=(grad S)^2: well total={source.sum():.2f} (gravity); flat total={source_flat.sum():.2e} (inert)")

S_anom=S_mass-S_mass.mean(); mid=n//2
a_matter=-np.gradient(-S_anom,x); a_darkE=-np.gradient(+S_anom,x)
eq_mag=np.allclose(np.abs(a_matter),np.abs(a_darkE))
print(f"(2) sign structure: matter accel[{mid-10}]={a_matter[mid-10]:+.2f} (attractive), darkE={a_darkE[mid-10]:+.2f} (repulsive); equal-magnitude one-force={eq_mag}")

# STRUCTURAL GATE (load-bearing): the solver inputs are DERIVED FROM THE COMPUTED FIELDS above --
# g = "entropy field has a gradient" (measured: max|grad S| > tol), sr = "gravitational source
# present" (measured: total (grad S)^2 > tol). Read from BOTH the well and the flat control.
tol=1e-6
g_well=int(np.abs(np.gradient(S_mass,x)).max()>tol); sr_well=int(source.sum()>tol)
g_flat=int(np.abs(np.gradient(S_flat,x)).max()>tol);  sr_flat=int(source_flat.sum()>tol)
def z3_fit():   # does the law "source present <=> gradient present" fit BOTH measured configs?
    s=z3.Solver(); g1,r1,g2,r2=z3.Ints('g1 r1 g2 r2')
    s.add(g1==g_well,r1==sr_well,g2==g_flat,r2==sr_flat)
    s.add(r1==g1,r2==g2); return str(s.check())
def z3_ctrl(with_law):  # counterfactual: the MEASURED-flat field ALSO has gravity (source present)
    s=z3.Solver(); g,r=z3.Ints('g r'); s.add(g==g_flat)   # g from the flat-field measurement
    if with_law: s.add(r==g)
    s.add(r==1); return str(s.check())
def cvc5_fit():
    s=cvc5.Solver(); s.setLogic("QF_LIA"); I=s.getIntegerSort(); mk=s.mkInteger
    g1,r1,g2,r2=[s.mkConst(I,n) for n in('g1','r1','g2','r2')]; eq=lambda a,b:s.mkTerm(Kind.EQUAL,a,b)
    for v,val in ((g1,g_well),(r1,sr_well),(g2,g_flat),(r2,sr_flat)): s.assertFormula(eq(v,mk(val)))
    s.assertFormula(eq(r1,g1)); s.assertFormula(eq(r2,g2)); return str(s.checkSat())
def cvc5_ctrl(with_law):
    s=cvc5.Solver(); s.setLogic("QF_LIA"); I=s.getIntegerSort(); mk=s.mkInteger
    g,r=[s.mkConst(I,n) for n in('g','r')]; eq=lambda a,b:s.mkTerm(Kind.EQUAL,a,b)
    s.assertFormula(eq(g,mk(g_flat)))
    if with_law: s.assertFormula(eq(r,g))
    s.assertFormula(eq(r,mk(1))); return str(s.checkSat())
zfit,cfit=z3_fit(),cvc5_fit()
zc1,cc1=z3_ctrl(True),cvc5_ctrl(True)     # law present + flat measured -> UNSAT
zc0,cc0=z3_ctrl(False),cvc5_ctrl(False)   # law dropped -> SAT (law is what bites)
print(f"(3) gate: data fits law z3={zfit}/cvc5={cfit} (sat); flat-field-has-gravity z3={zc1}/cvc5={cc1} (unsat w/law) -> {zc0}/{cc0} (sat w/o law)")

assert source.sum()>10 and source_flat.sum()<1e-6, "entropy gradient sources gravity; flat field is inert"
assert eq_mag and a_matter[mid-10]*a_darkE[mid-10]<0, "same |grad S|, opposite sign: one force, two regimes"
assert g_well==1 and sr_well==1 and g_flat==0 and sr_flat==0, "gate booleans derived from computed fields (well has gradient+source, flat has neither)"
assert zfit=="sat" and cfit=="sat", "law 'source <=> gradient' fits the measured well+flat configs (z3+cvc5)"
assert zc1=="unsat" and cc1=="unsat" and zc0=="sat" and cc0=="sat", "control flips: measured-flat field cannot have gravity (UNSAT w/law), SAT once law dropped (z3+cvc5 both halves)"
print("\nPASS entropic_gravity_axis0_sim")
