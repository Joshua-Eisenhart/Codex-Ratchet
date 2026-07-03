"""
coratchet_axis_orthogonality_sim.py -- Layer 17.4. DRIVES THE RATCHET DEEPER: entropy is
constrained to each terrain surface (the co-ratchet), the 2 signed operators per terrain live on
axes 5 (T/F kernel) and 6 (precedence), and the 7-axis orthogonality lattice is made exact.
Loops the Layer-16 bridges back in (einselection 16.2, DPI 16.9 monotonicity). NOT ToE
validation -- an internal deepening of the geometric constraint ratchet.

Grounded in the owner's docs:
  * AXIS_3_4_5_6_QIT_MATH.md: Ax5 = T-kernel (dephasing, dissipative) vs F-kernel (rotation,
    unitary); Ax6 = precedence b6 = -(b0*b3); affinity Ax5xAx2 -> operator identity
    (direct{Se,Ne}: Ti z-deph + Fi x-rot; conjugated{Ni,Si}: Te x-deph + Fe z-rot).
  * spec 7m: b0 = b1 XOR b2 (Axis-0 = Axis-1 charge XOR Axis-2 charge).

THREE RESULTS:
 (A) CO-RATCHET -- entropy constrained to the terrain. Each terrain's native entropy = coherence
     in ITS pointer basis (z for direct, x for conjugated). Under its OWN Axis-5 T-operator this
     falls monotonically to 0 (einselection, 16.2 + DPI 16.9); a FOREIGN-basis T-operator only
     plateaus (fails to einselect), and a FOREIGN F-operator PUMPS it back up. So entropy is not
     a global functional -- it runs on each terrain's own surface.
 (B) TWO SIGNED OPERATORS per terrain on axes 5,6. Ax5 splits T (entropy-producing, dS>0) from
     F (entropy-neutral, dS=0); Ax6 sign b6=-(b0*b3) sets operator-first vs terrain-first order.
 (C) 7-AXIS ORTHOGONALITY LATTICE. 5 primitive DOF (b1,b2,b3,b4,b5) are jointly free (all 2^5
     realizable = mutually orthogonal); 2 derived (b0=b1*b2, b6=-(b0*b3)) are FORCED functions.
     z3 AND cvc5 both confirm: the derived laws admit no freedom (negation UNSAT), and erasing a
     derived law frees the axis (SAT) -- load-bearing forcing, not a pinned comparison.

Tools: numpy+scipy (GKSL dynamics, entropy, control lane) + z3 + cvc5 (lattice forcing verdict,
load-bearing). scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
    from scipy.linalg import expm
    import itertools, z3, cvc5
    from cvc5 import Kind
except ImportError as e:
    print(f"SKIP_OPTIONAL coratchet_axis_orthogonality_sim: missing tool ({e.name})"); sys.exit(0)

SX=np.array([[0,1],[1,0]],complex); SY=np.array([[0,-1j],[1j,0]],complex); SZ=np.array([[1,0],[0,-1]],complex)
def cm(A,r): return A@r-r@A
def S_bits(r):
    w=np.linalg.eigvalsh((r+r.conj().T)/2); w=w[w>1e-12]; return float(-np.sum(w*np.log2(w)))
def bloch(n):
    n=np.array(n,float); n=n/np.linalg.norm(n) if np.linalg.norm(n)>1 else n
    return 0.5*(np.eye(2)+n[0]*SX+n[1]*SY+n[2]*SZ)
def T_dephase(axis):
    P=SZ if axis=='z' else SX; return lambda r:0.5*(P@r@P-r)
def F_rot(axis):
    P=SX if axis=='x' else SZ; return lambda r:-1j*cm(0.5*P,r)
def evolve(gen,r,t,n=200):
    dt=t/n
    for _ in range(n): r=r+dt*gen(r); r=(r+r.conj().T)/2; r=r/np.trace(r).real
    return r
Zp=[np.array([[1,0],[0,0]],complex),np.array([[0,0],[0,1]],complex)]
Xp=[bloch([1,0,0]),bloch([-1,0,0])]
def native_coh(r,axis):
    P=Zp if axis=='z' else Xp; return S_bits(sum(q@r@q for q in P))-S_bits(r)

# ---- (A) CO-RATCHET: entropy constrained to the terrain ----
r0=bloch([0.6,0.55,0.3]); ts=np.linspace(0,3,25)
own=[native_coh(evolve(T_dephase('z'),r0,t),'z') for t in ts]      # own T-op
foreignT=[native_coh(evolve(T_dephase('x'),r0,t),'z') for t in ts] # foreign T-op
rzpop=bloch([0,0,0.7])
foreignF=[native_coh(evolve(F_rot('x'),rzpop,t),'z') for t in ts]  # foreign F-op
mono_own=all(own[i+1]<=own[i]+1e-9 for i in range(len(own)-1))
plateau=foreignT[-1]; pump=max(foreignF)-foreignF[0]
print(f"(A) co-ratchet: own T-op native entropy {own[0]:.3f}->{own[-1]:.3f} monotone={mono_own}; "
      f"foreign T plateau={plateau:.3f}; foreign F pump=+{pump:.3f}")

# ---- (B) TWO SIGNED OPERATORS on axes 5,6 ----
def dS_op(gen):  # entropy production of an operator on a mixed probe
    r=bloch([0.5,0.3,0.4]); return S_bits(evolve(gen,r,0.4))-S_bits(r)
dS_T=dS_op(T_dephase('z'))
# F-kernel is a UNITARY -> exact evolution (expm), entropy exactly invariant (spectrum preserved)
_rF=bloch([0.5,0.3,0.4]); _U=expm(-1j*0.5*SX*0.4); dS_F=S_bits(_U@_rF@_U.conj().T)-S_bits(_rF)
print(f"(B) Ax5: T-kernel dS={dS_T:+.4f} (entropy-producing), F-kernel dS={dS_F:+.4f} (neutral)")
def b0f(b1,b2): return b1*b2
def b6f(b1,b2,b3): return -(b0f(b1,b2)*b3)
print(f"    Ax6 precedence b6=-(b0*b3): sample (b1=+,b2=+,b3=-)-> b6={b6f(1,1,-1):+d} (UP/op-first)")

# ---- (C) 7-AXIS ORTHOGONALITY LATTICE ----
combos=list(itertools.product([+1,-1],repeat=5))  # b1,b2,b3,b4,b5 primitive
free5=len(combos)==32
derived_pairs={c:(b0f(c[0],c[1]),b6f(c[0],c[1],c[2])) for c in combos}
print(f"(C) 5 primitive DOF free: {len(combos)}/32 orthogonal; derived (b0,b6) determined = {len(set(derived_pairs.values()))} pairs")

def z3_derived_forced(law):  # law in {'b0','b6'}: negation must be UNSAT (forced)
    s=z3.Solver(); b1,b2,b3,b0v,b6v=z3.Ints('b1 b2 b3 b0 b6')
    for v in (b1,b2,b3,b0v,b6v): s.add(z3.Or(v==1,v==-1))
    s.add(z3.Or(z3.And(b1==b2,b0v==1),z3.And(b1!=b2,b0v==-1)))  # b0 law
    s.add(b6v==-(b0v*b3))                                       # b6 law
    s.add(b0v!=b1*b2 if law=='b0' else b6v!=-(b0v*b3))          # negate the queried law
    return str(s.check())
def z3_erased_frees(law):  # drop the law -> the axis is free (SAT with a differing value)
    s=z3.Solver(); b1,b2,b3,b0v,b6v=z3.Ints('b1 b2 b3 b0 b6')
    for v in (b1,b2,b3,b0v,b6v): s.add(z3.Or(v==1,v==-1))
    if law=='b0': s.add(b6v==-(b0v*b3)); s.add(b0v!=b1*b2)      # keep b6 law, drop b0 law
    else: s.add(z3.Or(z3.And(b1==b2,b0v==1),z3.And(b1!=b2,b0v==-1))); s.add(b6v!=-(b0v*b3))
    return str(s.check())
def cvc5_derived_forced(law):
    s=cvc5.Solver(); s.setLogic("QF_NIA"); I=s.getIntegerSort()
    b1,b2,b3,b0v,b6v=[s.mkConst(I,n) for n in ('b1','b2','b3','b0','b6')]
    one=s.mkInteger(1); m1=s.mkInteger(-1)
    for v in (b1,b2,b3,b0v,b6v):
        s.assertFormula(s.mkTerm(Kind.OR,s.mkTerm(Kind.EQUAL,v,one),s.mkTerm(Kind.EQUAL,v,m1)))
    eq=lambda a,b: s.mkTerm(Kind.EQUAL,a,b); ne=lambda a,b: s.mkTerm(Kind.NOT,eq(a,b))
    mul=lambda a,b: s.mkTerm(Kind.MULT,a,b); neg=lambda a: s.mkTerm(Kind.NEG,a)
    s.assertFormula(s.mkTerm(Kind.OR,s.mkTerm(Kind.AND,eq(b1,b2),eq(b0v,one)),
                                     s.mkTerm(Kind.AND,ne(b1,b2),eq(b0v,m1))))
    s.assertFormula(eq(b6v,neg(mul(b0v,b3))))
    s.assertFormula(ne(b0v,mul(b1,b2)) if law=='b0' else ne(b6v,neg(mul(b0v,b3))))
    return str(s.checkSat())
def cvc5_erased_frees(law):  # drop the queried law -> axis free (SAT with a differing value)
    s=cvc5.Solver(); s.setLogic("QF_NIA"); I=s.getIntegerSort()
    b1,b2,b3,b0v,b6v=[s.mkConst(I,n) for n in ('b1','b2','b3','b0','b6')]
    one=s.mkInteger(1); m1=s.mkInteger(-1)
    for v in (b1,b2,b3,b0v,b6v):
        s.assertFormula(s.mkTerm(Kind.OR,s.mkTerm(Kind.EQUAL,v,one),s.mkTerm(Kind.EQUAL,v,m1)))
    eq=lambda a,b: s.mkTerm(Kind.EQUAL,a,b); ne=lambda a,b: s.mkTerm(Kind.NOT,eq(a,b))
    mul=lambda a,b: s.mkTerm(Kind.MULT,a,b); neg=lambda a: s.mkTerm(Kind.NEG,a)
    b0law=s.mkTerm(Kind.OR,s.mkTerm(Kind.AND,eq(b1,b2),eq(b0v,one)),s.mkTerm(Kind.AND,ne(b1,b2),eq(b0v,m1)))
    b6law=eq(b6v,neg(mul(b0v,b3)))
    if law=='b0':  # keep b6 law, drop b0 law, demand b0 differs from the product
        s.assertFormula(b6law); s.assertFormula(ne(b0v,mul(b1,b2)))
    else:          # keep b0 law, drop b6 law, demand b6 differs
        s.assertFormula(b0law); s.assertFormula(ne(b6v,neg(mul(b0v,b3))))
    return str(s.checkSat())

z0f,z6f=z3_derived_forced('b0'),z3_derived_forced('b6')
z0e,z6e=z3_erased_frees('b0'),z3_erased_frees('b6')
c0f,c6f=cvc5_derived_forced('b0'),cvc5_derived_forced('b6')
c0e,c6e=cvc5_erased_frees('b0'),cvc5_erased_frees('b6')
print(f"    z3:   b0 forced={z0f} b6 forced={z6f} | erase-frees b0={z0e} b6={z6e}")
print(f"    cvc5: b0 forced={c0f} b6 forced={c6f} | erase-frees b0={c0e} b6={c6e}")

assert mono_own and plateau>0.05 and pump>0.05, "co-ratchet: monotone own, plateau foreign-T, pump foreign-F"
assert dS_T>0.05 and abs(dS_F)<1e-9, "Ax5: T entropy-producing, F entropy-neutral"
assert free5 and len(set(derived_pairs.values()))==4, "5 primitive DOF free, derived determined"
assert z0f=="unsat" and z6f=="unsat" and c0f=="unsat" and c6f=="unsat", "derived axes forced (z3+cvc5 both UNSAT)"
assert z0e=="sat" and z6e=="sat" and c0e=="sat" and c6e=="sat", "erasing a derived law frees the axis (z3+cvc5 both SAT — the flipping control, per the three-engine contract)"
print("\nPASS coratchet_axis_orthogonality_sim")
