"""
root_axiom_sim.py -- Layer 0.1. THE ROOT AXIOM: a=a iff a~b (identity iff distinguishability),
and ENTROPIC MONISM (the one primitive is constraint on distinguishability; entropy is a LATER
measure of it, not the substance). This is the FOUNDATION beneath the whole
bridge ladder (physics/chemistry/biochem/evolution/consciousness all sit on top of this). Grounded
in the owner's canon-candidate doctrine ROOT_CONSTRAINT_EXTENDED_FOUNDATIONS.md (EC-1/EC-2/EC-3) and
ENTROPIC_MONISM_ORIGIN_AND_COSMOLOGY.md. NOT a metaphysics proof -- it renders the owner's stated
derivation chain as runnable, checkable math and shows the root gate is a genuine (non-vacuous)
structural constraint.

The chain (owner doctrine, entailed by the two root constraints RC-1 finitude + RC-2 noncommutation):
 EC-1 NO PRIMITIVE IDENTITY: "a=a" is admissible only via a FINITE probe family P confirming
      self-consistency (order-invariant). Self-identity costs finite resources.
 EC-2 NO PRIMITIVE EQUALITY: "a~b" := for all p in P, p(a)≈p(b) within precision eps. Weaker than
      identity; always relative to the probe family; different P give different ~ classes.
 EC-3 THE IDENTITY PRINCIPLE: a=a IFF a~b. Self-identity is meaningful iff there exists an OTHER b
      from which a is distinguishable. Without a contrast class, identity collapses to vacuity.
      Implies: identity requires a bipartite cut A|B; determinism iff probability; Turing iff oracle.
 ENTROPIC MONISM (per OWNER_THESIS_AND_COSMOLOGY.md): the one primitive substance is CONSTRAINT ON
      DISTINGUISHABILITY. Entropy is NOT the primitive -- it is a LATER admissible quantitative
      measure of distinguishability. Here von Neumann S is shown to be a MONOTONE of the number of
      distinguishable branches (a measure OF distinguishability), never the substance itself.

FOUR results:
 (A) EC-1/EC-2 -- identity is PROBE-RELATIVE: a coarse probe (z only) merges a~b; a finer probe (x)
     separates them. The ~ equivalence classes CHANGE with the finite probe family -> no primitive
     identity.
 (B) EC-3 ROOT GATE (load-bearing): "object 0 has meaningful self-identity" := exists j!=0
     distinguishable from 0. z3 AND cvc5 SEARCH a finite signature universe: distinction allowed ->
     SAT (a contrast class exists, identity meaningful); erase all distinction (undifferentiated
     entropic-monist substrate, all signatures forced equal) -> UNSAT (identity vacuous). Both
     solvers, both halves, the control flips: a=a truly REQUIRES a~b.
 (C) ENTROPIC MONISM -- entropy is a MEASURE OF distinguishability (not the primitive): von Neumann S of n equally-distinguishable
     branches = log2(n) exactly (n=1 -> 0 bits, "no contrast, identity vacuous"; up to log2 dim).
 (D) EC-3 point 1 -- identity requires a bipartite cut A|B: a subsystem's relational identity
     content = its distinguishability from its complement = mutual information I(A:B). Product state
     (no boundary) I=0 (A has no relational identity); entangled Bell state I=2 bits (A|B boundary
     carries identity). Ties the root axiom to the entanglement-central physics.
 (E) S-KNOT (A2_HOPF_FIBRATION_ENTROPY): the owner's "low-S structured knot (matter/memory/logic)
     compressed from high-S fuzz". Any two distinct Hopf fibers on S^3 link with Gauss linking
     number 1 (a topological invariant); unlinked loops give 0. A discrete conserved identity charge
     the continuous entropic substrate cannot smoothly erase -- a compressed attractor made integer.

Tools: numpy (probe classes, von Neumann entropy, mutual information -- control lane) + z3 + cvc5
(EC-3 root gate, load-bearing). scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
    import z3, cvc5
    from cvc5 import Kind
except ImportError as e:
    print(f"SKIP_OPTIONAL root_axiom_sim: missing tool ({e.name})"); sys.exit(0)

def bloch(th,ph): return np.array([np.sin(th)*np.cos(ph),np.sin(th)*np.sin(ph),np.cos(th)])
def probe_sig(r,axes,eps=0.4): return tuple(int(round(np.dot(r,ax)/eps)) for ax in axes)
objs={'a':bloch(1.2,0.0),'b':bloch(1.2,np.pi),'c':bloch(0.2,0.0)}
def classes(P):
    sig={k:probe_sig(v,P) for k,v in objs.items()}; cl={}
    for k,s in sig.items(): cl.setdefault(s,[]).append(k)
    return sorted([sorted(v) for v in cl.values()])
c_z=classes([np.array([0,0,1.0])]); c_x=classes([np.array([1.0,0,0])])
print(f"(A) EC-1/EC-2 probe-relative: z-only {c_z}; x-only {c_x}; classes change with P = {c_z!=c_x}")

def z3_identity(erase,N=4):
    s=z3.Solver(); sig=[z3.Int(f's{i}') for i in range(N)]
    for v in sig: s.add(v>=0,v<N)
    if erase:
        for i in range(1,N): s.add(sig[i]==sig[0])
    s.add(z3.Or([sig[0]!=sig[j] for j in range(1,N)])); return str(s.check())
def cvc5_identity(erase,N=4):
    s=cvc5.Solver(); s.setLogic("QF_LIA"); I=s.getIntegerSort(); mk=s.mkInteger
    sig=[s.mkConst(I,f's{i}') for i in range(N)]
    ge=lambda x,y:s.mkTerm(Kind.GEQ,x,y); lt=lambda x,y:s.mkTerm(Kind.LT,x,y)
    eq=lambda x,y:s.mkTerm(Kind.EQUAL,x,y); ne=lambda x,y:s.mkTerm(Kind.NOT,eq(x,y))
    for v in sig: s.assertFormula(ge(v,mk(0))); s.assertFormula(lt(v,mk(N)))
    if erase:
        for i in range(1,N): s.assertFormula(eq(sig[i],sig[0]))
    s.assertFormula(s.mkTerm(Kind.OR,*[ne(sig[0],sig[j]) for j in range(1,N)])); return str(s.checkSat())
zf,ze,cf,ce=z3_identity(False),z3_identity(True),cvc5_identity(False),cvc5_identity(True)
print(f"(B) EC-3 gate a=a iff a~b: distinction-allowed z3={zf}/cvc5={cf} (sat); erased z3={ze}/cvc5={ce} (unsat)")

def SvN(rho):
    w=np.linalg.eigvalsh((rho+rho.conj().T)/2); w=w[w>1e-12]; return float(-np.sum(w*np.log2(w)))
ent=[(n,SvN(np.eye(n,dtype=complex)/n)) for n in [1,2,4,8]]
print("(C) entropy = a later MEASURE of distinguishability (not the substance): "+" ".join(f"n{n}->{s:.2f}=log2({n})" for n,s in ent))

def mutual_info(psi):
    rho=np.outer(psi,psi.conj()); r=rho.reshape(2,2,2,2)
    rA=np.einsum('ijkj->ik',r); rB=np.einsum('ijil->jl',r)
    return SvN(rA)+SvN(rB)-SvN(rho)
prod=np.kron([1,0],[1,0.0]); bell=np.array([1,0,0,1],float)/np.sqrt(2)
Iprod,Ibell=mutual_info(prod),mutual_info(bell)
print(f"(D) A|B cut (relational identity = I(A:B)): product={Iprod:.3f}, Bell={Ibell:.3f}")

# (E) S-KNOT: a linked Hopf fiber carries a CONSERVED INTEGER (Gauss linking number) -- the owner's
# "low-S structured knot (matter/memory/logic) compressed from high-S fuzz" (A2_HOPF_FIBRATION_
# ENTROPY). Any two distinct Hopf fibers link with number 1; unlinked loops give 0. A discrete
# identity charge the continuous entropic substrate cannot smoothly erase.
def hopf_fiber(a,b,n=400):
    t=np.linspace(0,2*np.pi,n,endpoint=False); z1=a*np.exp(1j*t); z2=b*np.exp(1j*t)
    d=1-z2.imag; return np.stack([z1.real/d,z1.imag/d,z2.real/d],axis=1)
def gauss_linking(C1,C2):
    dr1=np.roll(C1,-1,0)-C1; dr2=np.roll(C2,-1,0)-C2
    m1=(C1+np.roll(C1,-1,0))/2; m2=(C2+np.roll(C2,-1,0))/2; tot=0.0
    for i in range(len(m1)):
        diff=m1[i]-m2; dist=np.linalg.norm(diff,axis=1)**3+1e-12
        tot+=np.sum(np.sum(diff*np.cross(dr1[i][None,:],dr2),axis=1)/dist)
    return tot/(4*np.pi)
f1=hopf_fiber(np.cos(0.3),np.sin(0.3)*np.exp(1j*0.0)); f2=hopf_fiber(np.cos(1.1),np.sin(1.1)*np.exp(1j*1.7))
Lk=gauss_linking(f1,f2)
c1=np.stack([np.cos(np.linspace(0,2*np.pi,400)),np.sin(np.linspace(0,2*np.pi,400)),np.zeros(400)],1)
Lk0=gauss_linking(c1,c1+np.array([5.0,0,0]))
print(f"(E) S-knot Hopf linking: two distinct fibers = {Lk:.3f} (invariant 1); unlinked control = {Lk0:.3f} (0)")

assert c_z!=c_x, "identity is probe-relative (EC-1/EC-2): ~ classes depend on the finite probe family"
assert abs(Lk-1)<0.05 and abs(Lk0)<0.05, "S-knot: Hopf fibers carry conserved linking integer 1 vs 0"
assert zf=="sat" and cf=="sat" and ze=="unsat" and ce=="unsat", "EC-3: a=a requires a~b (z3+cvc5 both halves)"
assert abs(ent[0][1])<1e-9 and all(abs(s-np.log2(n))<1e-9 for n,s in ent), "entropy = log2(distinguishable branches)"
assert Iprod<1e-9 and Ibell>1.99, "identity needs A|B cut: product I=0, Bell I=2"
print("\nPASS root_axiom_sim")
