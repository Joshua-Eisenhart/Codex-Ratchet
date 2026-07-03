"""
manifold_L4_local_weyl_factors_sim.py -- PURE MATH. 2026-07-03, Manifold spine Layer 4 (L4).

Nests on L3 (spinor surface) and L2 (marginals). L4 adds (completeness contract Part A, layer 4) the LOCAL
WEYL FACTORS: a global state decomposes into local spinor (Weyl) factors EXACTLY when it is a product state;
entangled states keep mixed marginals and admit NO local pure-spinor factorization. This is where the model's
"Weyl factor" language first gets a real spine referent: the local factor is the L3 spinor of a PURE marginal,
and it exists only on the product-state locus. Built only after L3 green; nothing above L4 touched. No saliency
skipping.

DUAL RATCHET at L4: the factorizability (geometry -- does the Weyl factorization exist) and the marginal
PURITY (readout) co-ratchet. Turning on entanglement dissolves the local Weyl factor exactly as the marginal
purity drops -- geometry and readout move together, and the factor exists iff marginal pure iff product iff
negativity 0.

RESULTS (deterministic):
 (1) PRODUCT state |0>|+>: local Weyl factors EXIST -- both marginals pure (purity 1.000), the top marginal
     eigenvector IS the local spinor factor, and rho = rho_A ⊗ rho_B exactly.
 (2) ENTANGLED (Bell): NO local Weyl factors -- both marginals maximally mixed (purity 0.500), no pure local
     spinor, rho does NOT factor. The Weyl decomposition is admitted exactly on the product locus.
 (3) DUAL RATCHET: sweeping product -> Bell, the local Weyl factor exists only at a=0 (purity 1.000,
     negativity 0); as soon as entanglement turns on (a>0) the factor is gone, purity drops 1.000 -> 0.500,
     negativity rises 0 -> 0.500 -- factorization (geometry) and purity (readout) co-ratchet.
 (4) NEGATIVES (each FIRES): #1 PRODUCT-STATE-NEGATIVITY-ZERO (product neg=0, Bell neg=0.5); #9 ENTANGLED-vs-
     SEPARABLE (the factorization test DIVERGES: product factorizes, Bell does not -- a psi-dependent, not
     decorative, quantity); #10 PER-RUNG 3q (GHZ has a mixed 1q marginal / no local factor, a 3q product has
     a pure marginal / local factor).
 (5) SMT GATE (box iii #6, load-bearing, dual solver): the Weyl-factorization law -- local Weyl factors exist
     IFF the state is a product (pure marginals). "Can an entangled (non-product) state have local Weyl
     factors?" is UNSAT with the law (z3 AND cvc5), SAT when erased. The erased variant flips for a structural
     reason (factorization decoupled from marginal purity), not a count change.

HONEST SCOPE: earns L4 -- the local Weyl factors and their product-state admission locus -- on top of L3, with
the dual ratchet and the negatives firing at 2q/3q. It does NOT build L5 (nested tori -> marginal-radius
shells + Schmidt strata) or above. Next rung, in order. The Weyl CHIRALITY (which handedness) and the
engine-type split are much later objects (they need the flux and cut structure); this layer earns only the
local-factor EXISTENCE criterion, not chirality. No terrain/axis/engine claim rides on this. Hypothetical
lane; owner doctrine under test. scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
    import z3, cvc5
    from cvc5 import Kind
except ImportError as e:
    print(f"SKIP_OPTIONAL manifold_L4_local_weyl_factors_sim: missing tool ({e.name})"); sys.exit(0)

I2=np.eye(2,dtype=complex)
def ptrace(rho,keep):
    r=rho.reshape(2,2,2,2); return np.einsum('abcb->ac',r) if keep==0 else np.einsum('abad->bd',r)
def ptrace3_keep0(rho): return np.einsum('abcAbc->aA',rho.reshape(2,2,2,2,2,2))
def purity(rho): return float(np.real(np.trace(rho@rho)))
def factorizes(rho,tol=1e-8):
    rA,rB=ptrace(rho,0),ptrace(rho,1); return np.allclose(rho,np.kron(rA,rB),atol=tol)
def local_weyl_factor(rho,keep,tol=1e-8):
    m=ptrace(rho,keep); w,V=np.linalg.eigh(m); return (V[:,-1] if w[-1]>1-tol else None)
def neg(rho):
    r=rho.reshape(2,2,2,2).transpose(0,3,2,1).reshape(4,4); return float(np.sum(np.abs(np.linalg.eigvalsh(r)))-1)/2

# (1) product
prod=np.kron(np.outer([1,0],[1,0]),np.outer(np.array([1,1])/np.sqrt(2),np.array([1,1])/np.sqrt(2)))
p1_ok=purity(ptrace(prod,0))>0.999 and local_weyl_factor(prod,0) is not None and factorizes(prod)
print(f"(1) product |0>|+>: marginals pure, Weyl factors exist, factorizes: {p1_ok}")

# (2) entangled
bell=np.outer(np.array([1,0,0,1])/np.sqrt(2),np.array([1,0,0,1])/np.sqrt(2))
p2_ok=purity(ptrace(bell,0))<0.501 and local_weyl_factor(bell,0) is None and not factorizes(bell)
print(f"(2) Bell: marginals mixed, no Weyl factor, no factorization: {p2_ok}")

# (3) dual ratchet
print("(3) dual ratchet (product->Bell; Weyl factor + marginal purity co-move):")
v0=np.array([1,0,0,0],complex); vb=np.array([1,0,0,1],complex)/np.sqrt(2); traj=[]
for a in [0.0,0.25,0.5,0.75,1.0]:
    v=(1-a)*v0+a*vb; v/=np.linalg.norm(v); rho=np.outer(v,v.conj())
    traj.append((purity(ptrace(rho,0)),local_weyl_factor(rho,0) is not None,neg(rho)))
    print(f"    a={a:.2f}: purity {traj[-1][0]:.3f}, Weyl factor={traj[-1][1]}, negativity {traj[-1][2]:.3f}")
ratchet_ok=traj[0][1] and (not traj[-1][1]) and traj[0][2]<1e-9 and traj[-1][2]>0.49

# (4) negatives
prodm=np.kron(np.diag([0.7,0.3]).astype(complex),np.diag([0.6,0.4]).astype(complex))
n1=abs(neg(prodm))<1e-9 and neg(bell)>0.4
n9=factorizes(prodm) and not factorizes(bell)
ghz=np.outer(np.array([1,0,0,0,0,0,0,1])/np.sqrt(2),np.array([1,0,0,0,0,0,0,1])/np.sqrt(2))
prod3=np.kron(np.kron(np.outer([1,0],[1,0]),np.outer([1,0],[1,0])),np.outer(np.array([1,1])/np.sqrt(2),np.array([1,1])/np.sqrt(2)))
n10=purity(ptrace3_keep0(ghz))<0.6 and purity(ptrace3_keep0(prod3))>0.99
print(f"(4) negatives: #1 product-neg-zero={n1}, #9 factorization-diverges={n9}, #10 per-rung-3q={n10}")

# (5) SMT gate
def z3_weyl(law):
    s=z3.Solver(); prod=z3.Bool('p'); weyl=z3.Bool('w'); pm=z3.Bool('m')
    if law: s.add(weyl==z3.And(prod,pm)); s.add(prod==pm)
    s.add(weyl==True); s.add(prod==False); return s.check()==z3.sat
def cvc5_weyl(law):
    s=cvc5.Solver(); s.setLogic("QF_UF"); B=s.getBooleanSort()
    prod=s.mkConst(B,'p'); weyl=s.mkConst(B,'w'); pm=s.mkConst(B,'m'); T=s.mkTrue(); F=s.mkFalse()
    if law: s.assertFormula(s.mkTerm(Kind.EQUAL,weyl,s.mkTerm(Kind.AND,prod,pm))); s.assertFormula(s.mkTerm(Kind.EQUAL,prod,pm))
    s.assertFormula(s.mkTerm(Kind.EQUAL,weyl,T)); s.assertFormula(s.mkTerm(Kind.EQUAL,prod,F)); return str(s.checkSat())=="sat"
zl,ze=z3_weyl(True),z3_weyl(False); cl,ce=cvc5_weyl(True),cvc5_weyl(False)
print(f"(5) SMT gate 'Weyl factors for entangled state?': with-law z3={zl}/cvc5={cl} (UNSAT); erased z3={ze}/cvc5={ce} (SAT)")

assert p1_ok, "product admits local Weyl factors"
assert p2_ok, "entangled admits none"
assert ratchet_ok, "dual ratchet: factor + purity co-move"
assert n1 and n9 and n10, "L4 negatives fire"
assert (not zl) and (not cl) and ze and ce, "SMT gate: Weyl factorization needs product (UNSAT), erased frees it (SAT), both solvers"
print("\nPASS manifold_L4_local_weyl_factors_sim")
