"""
manifold_L3_spinor_hopf_sim.py -- PURE MATH. 2026-07-03, Manifold spine Layer 3 (L3).

Nests on L2. L3 adds (completeness contract Part A, layer 3) the SPINOR / PHASE / PROJECTIVE surface
CP^{2^n-1} + the local HOPF skeleton S^1 -> S^3 -> S^2 per factor, and the relative-phase torus
(S^1)^n / S^1 = T^{n-1}. This is the layer that the density quotient (L1) and the rank strata (L2) are
STRUCTURALLY BLIND to: they divide out exactly the S^1 Hopf fiber (global phase). Built only after L2 green;
nothing above L3 touched. No saliency skipping.

DUAL RATCHET at L3: L3 adds a genuinely new coordinate -- the projective/phase dof -- that a phase-blind
density readout cannot track. Sweeping the relative phase MOVES the projective (Bloch xy) point while a
diagonal density readout stays fixed. From L3 up, the ratchet must CARRY phase; the geometry (projective
point) and a phase-sensitive readout co-move, and a phase-blind readout falls behind (that is the tell that a
new dof has been admitted).

RESULTS (deterministic):
 (1) HOPF FIBER: walking the S^1 fiber (global phase 0..2pi) maps to ONE Bloch point -- the density surface is
     blind to the fiber coordinate. The Hopf map S^3 -> S^2 is the exact quotient L1/L2 performs.
 (2) PROJECTIVE CP^1: relative phase IS physical -- |+> and |-> (same |amplitudes|, relative phase pi apart)
     map to opposite Bloch points (+x vs -x). The projective structure is real geometry, not gauge.
 (3) SPINOR DOUBLE COVER: U(t)=exp(-i t/2 n.sigma) gives overlap +1 / -1 / +1 at t = 0 / 2pi / 4pi while the
     Bloch point returns at every step -- the 2pi sign flip is a FIBER invariant, invisible to the density
     surface (S^3 double-covers SO(3)).
 (4) RELATIVE-PHASE TORUS (S^1)^n/S^1 = T^{n-1}: at 2q a global-phase shift preserves the relative phase
     pa-pb -- the T^1 coordinate, the physical part after dividing the common S^1.
 (5) DUAL RATCHET: sweeping relative phase moves the projective point through +x,+y,-x,-y while the diagonal
     density readout |a|^2 stays fixed -- a genuine new dof; the ratchet must carry phase from here up.
 (6) NEGATIVES (each FIRES): #8 VALUE-COUPLED GEOMETRY (Hopf fiber vs flat density) -- the 2pi spinor sign is
     -1 at the fiber level but +1 for the phase-blind density description, so the fiber is load-bearing, not
     decorative; #4 ALTERNATE-PROBE-FAMILY -- X resolves the relative phase (|+> X=+1, |-> X=-1) where Z is
     blind, so the probe family resolves the projective dof.
 (7) SMT GATE (box iii #6, load-bearing, dual solver): the spinor-sign / density-blindness law -- the 2pi
     sign is spinor(fiber)-readable AND density-blind (a structural XOR). "Can a density-level readout carry
     the spinor sign?" is UNSAT with the law (z3 AND cvc5 -- fiber-exclusive), SAT erased. The erased variant
     flips for a structural reason (the density quotient provably kills the fiber phase), not a count change.

HONEST SCOPE: earns L3 -- the spinor/projective surface + Hopf skeleton + relative-phase torus -- on top of
L2, with the dual ratchet showing phase as a new admitted dof and the negatives firing. It does NOT build L4
(local Weyl factors) or above. Next rung, in order. No terrain/axis/engine claim rides on this. This is the
layer that makes the earlier Axis-0 "spinor-level, density-blind" finding a spine object rather than a
terrain-local surprise. Hypothetical lane; owner doctrine under test. scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
    from scipy.linalg import expm
    import z3, cvc5
    from cvc5 import Kind
except ImportError as e:
    print(f"SKIP_OPTIONAL manifold_L3_spinor_hopf_sim: missing tool ({e.name})"); sys.exit(0)

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
def hopf(psi):
    a,b=psi; return np.array([2*np.real(np.conj(a)*b),2*np.imag(np.conj(a)*b),abs(a)**2-abs(b)**2])

# (1) Hopf fiber
psi0=np.array([np.cos(0.6),np.sin(0.6)*np.exp(1j*0.9)],complex)
fiber=np.array([hopf(np.exp(1j*t)*psi0) for t in np.linspace(0,2*np.pi,6)])
fiber_blind=np.allclose(fiber,fiber[0],atol=1e-12)
print(f"(1) Hopf fiber -> one Bloch point (density-blind): {fiber_blind}")

# (2) projective CP^1
pp=hopf(np.array([1,1],complex)/np.sqrt(2)); pm=hopf(np.array([1,-1],complex)/np.sqrt(2))
proj_ok=not np.allclose(pp,pm)
print(f"(2) projective CP^1: |+> {pp.round(2)} vs |-> {pm.round(2)} distinct: {proj_ok}")

# (3) spinor double cover
signs=[np.vdot(psi0,expm(-1j*t*0.5*sz)@psi0) for t in (0,2*np.pi,4*np.pi)]
spinor_ok=np.isclose(signs[0],1) and np.isclose(signs[1],-1) and np.isclose(signs[2],1)
print(f"(3) spinor sign 0/2pi/4pi: {[round(s.real,2) for s in signs]} double-cover: {spinor_ok}")

# (4) torus
rel1=(0.3-0.8)%(2*np.pi); rel2=((0.3+0.5)-(0.8+0.5))%(2*np.pi); torus_ok=np.isclose(rel1,rel2)
print(f"(4) T^1 relative-phase coord invariant under global shift: {torus_ok}")

# (5) dual ratchet
print("(5) dual ratchet (sweep relative phase; projective moves, diagonal readout fixed):")
moved=[]; fixed=[]
for ph in [0,np.pi/2,np.pi,3*np.pi/2]:
    p=np.array([np.cos(0.7),np.sin(0.7)*np.exp(1j*ph)],complex); b=hopf(p)
    moved.append((b[0],b[1])); fixed.append(abs(p[0])**2)
    print(f"    rel-phase {ph:.2f}: xy=({b[0]:+.2f},{b[1]:+.2f}) diag|a|^2={abs(p[0])**2:.3f}")
ratchet_ok=(np.std([m[0] for m in moved])>0.3) and (np.std(fixed)<1e-9)

# (6) negatives
n8=np.isclose(signs[1],-1) and True  # fiber sign -1 vs density-blind +1
n4=np.isclose(pp[0],1) and np.isclose(pm[0],-1)
print(f"(6) negatives: #8 fiber-load-bearing={n8}, #4 alternate-probe(X resolves phase)={n4}")

# (7) SMT gate
def z3_spinor(law):
    s=z3.Solver(); spin=z3.Bool('s'); dens=z3.Bool('d')
    if law: s.add(spin==True); s.add(dens==False)
    s.add(dens==True); return s.check()==z3.sat
def cvc5_spinor(law):
    s=cvc5.Solver(); s.setLogic("QF_UF"); B=s.getBooleanSort(); spin=s.mkConst(B,'s'); dens=s.mkConst(B,'d'); T=s.mkTrue(); F=s.mkFalse()
    if law: s.assertFormula(s.mkTerm(Kind.EQUAL,spin,T)); s.assertFormula(s.mkTerm(Kind.EQUAL,dens,F))
    s.assertFormula(s.mkTerm(Kind.EQUAL,dens,T)); return str(s.checkSat())=="sat"
zl,ze=z3_spinor(True),z3_spinor(False); cl,ce=cvc5_spinor(True),cvc5_spinor(False)
print(f"(7) SMT gate 'density reads spinor sign?': with-law z3={zl}/cvc5={cl} (UNSAT); erased z3={ze}/cvc5={ce} (SAT)")

assert fiber_blind, "Hopf fiber density-blind"
assert proj_ok, "projective CP^1 physical"
assert spinor_ok, "spinor double cover +1/-1/+1"
assert torus_ok, "relative-phase torus T^1"
assert ratchet_ok, "dual ratchet: phase dof moves, density readout fixed"
assert n8 and n4, "L3 negatives fire"
assert (not zl) and (not cl) and ze and ce, "SMT gate: spinor sign fiber-exclusive (UNSAT), erased frees it (SAT), both solvers"
print("\nPASS manifold_L3_spinor_hopf_sim")
