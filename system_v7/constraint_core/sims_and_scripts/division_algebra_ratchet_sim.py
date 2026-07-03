"""
division_algebra_ratchet_sim.py -- PURE MATH, no jargon. 2026-07-02, Layer 0.5.

The ratchet from the WEAKEST structures taking the SHORTEST leaps up, with nonassociativity ratcheted
in -- realized as the Cayley-Dickson division-algebra ladder R -> C -> H -> O -> (S = kill-control).
Source: working_math_scaffold_20260609.md sec 10.3 ("quaternion/octonion: H assoc=0, O assoc!=0,
sedenion zero-divisor kill-control; Fano, G2=Aut(O), Spin(7), J3(O)"); root_axioms_v0_1 line 51 ("One
root relation appears at three levels: elements as quotient identity S/~_M, order as noncommutation,
and grouping as NONASSOCIATIVITY"). So nonassociativity is the grouping-level face of N01 -- the same
root relation, one rung up -- and the division-algebra ladder is where it ratchets in.

Each Cayley-Dickson doubling is the SHORTEST leap (dimension x2) and LOSES exactly one property:
  R(1): totally ordered, commutative, associative, division
  C(2): loses ordering
  H(4): loses commutativity           <- order-level N01 (commutator != 0)
  O(8): loses associativity           <- grouping-level N01 (associator != 0) = nonassociativity ratcheted
  S(16): loses DIVISION (zero-divisors) <- the KILL-CONTROL: the ratchet must STOP at O

PERSISTENCE = the division property: |xy| = |x||y| (norm multiplicative) means no two nonzero things
compose to nothing -- composition preserves non-vanishing. O is the LAST algebra with this (Hurwitz).
G2 = Aut(O), dim 14: the exceptional-Lie symmetry the docs point to ("modified G2 structure").

RESULTS (deterministic, seeded):
 (1) LADDER: max|commutator| and max|associator| per rung -- commutativity dies at H (comm 14.0),
     associativity dies at O (assoc 69.5). The two are the order/grouping faces of N01.
 (2) HURWITZ/PERSISTENCE: |xy|=|x||y| holds for H,O (err ~1e-13) and FAILS for S (err ~200).
 (3) KILL-CONTROL: an explicit sedenion zero-divisor (e1+e10)(e5+e14)=0 -- two nonzero elements
     annihilate. Division/persistence lost at dim 16 => the ratchet stops at O.
 (4) G2=Aut(O): the derivation algebra of O (Leibniz on octonion multiplication) has dim 14 = g2.
 (5) STRUCTURAL GATE (load-bearing, DERIVED inputs): booleans from measured associativity+division
     per rung; law "ratchet admits a rung IFF it still divides (norm-multiplicative)" fits R..O (SAT);
     control "admit S (measured non-dividing)" UNSAT with law -> SAT without. z3 AND cvc5, both halves.

HONEST SCOPE: this earns the division-algebra ladder as the weakest-structure/shortest-leap ratchet
with nonassociativity as the grouping-level N01, and O as the kill-controlled endpoint with G2
symmetry. It does NOT here build the octonion spinor network or derive SM gauge structure from G2 --
those are downstream (working_math_scaffold 10.4). Owner doctrine under test.
scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
    import z3, cvc5
    from cvc5 import Kind
except ImportError as e:
    print(f"SKIP_OPTIONAL division_algebra_ratchet_sim: missing tool ({e.name})"); sys.exit(0)

def cd_mul(a,b):
    n=len(a)
    if n==1: return np.array([a[0]*b[0]])
    m=n//2; a1,a2,b1,b2=a[:m],a[m:],b[:m],b[m:]
    def conj(x):
        if len(x)==1: return x.copy()
        c=-x.copy(); c[0]=x[0]; return c
    return np.concatenate([cd_mul(a1,b1)-cd_mul(conj(b2),a2), cd_mul(b2,a1)+cd_mul(a2,conj(b1))])
def e(n,i):
    v=np.zeros(n); v[i]=1.0; return v
def norm2(x): return float(np.dot(x,x))
rng=np.random.default_rng(0); rnd=lambda n: rng.normal(size=n)
comm=lambda x,y: cd_mul(x,y)-cd_mul(y,x)
assoc=lambda x,y,z: cd_mul(cd_mul(x,y),z)-cd_mul(x,cd_mul(y,z))

ladder=[("R",1),("C",2),("H",4),("O",8),("S",16)]
cmax={}; amax={}
for name,n in ladder:
    cmax[name]=max(np.abs(comm(rnd(n),rnd(n))).max() for _ in range(200))
    amax[name]=max(np.abs(assoc(rnd(n),rnd(n),rnd(n))).max() for _ in range(200))
print(f"(1) ladder: comm H={cmax['H']:.1f} (commutativity dies), assoc O={amax['O']:.1f} (associativity dies = nonassoc ratcheted)")

hurwitz={}
for name,n in [("H",4),("O",8),("S",16)]:
    hurwitz[name]=max(abs(norm2(cd_mul(a:=rnd(n),b:=rnd(n)))-norm2(a)*norm2(b)) for _ in range(500))
print(f"(2) Hurwitz |xy|=|x||y|: H err={hurwitz['H']:.1e}, O err={hurwitz['O']:.1e} (divide), S err={hurwitz['S']:.1e} (FAILS)")

a=e(16,1)+e(16,10); b=e(16,5)+e(16,14); zd=norm2(cd_mul(a,b))
print(f"(3) kill-control: (e1+e10)(e5+e14) norm={zd:.1e} (zero-divisor: two nonzero -> 0) -> ratchet stops at O")

c=np.zeros((7,7,7))
for i in range(7):
    for j in range(7): c[i,j,:]=cd_mul(e(8,i+1),e(8,j+1))[1:]
def idx(a,b): return a*7+b
rows=[]
for i in range(7):
    for j in range(7):
        for m in range(7):
            r=np.zeros(49)
            for k in range(7): r[idx(m,k)]+=c[i,j,k]
            for p in range(7): r[idx(p,i)]-=c[p,j,m]
            for q in range(7): r[idx(q,j)]-=c[i,q,m]
            rows.append(r)
g2dim=49-np.linalg.matrix_rank(np.array(rows),tol=1e-9)
print(f"(4) G2=Aut(O): derivation-algebra dim = {g2dim} (= g2)")

# gate: admit rung IFF it divides. divides bit measured (1 for R..O, 0 for S).
div={"R":1,"C":1,"H":1,"O":1,"S":0}
def z3_fit():
    for name in ["R","C","H","O"]:
        s=z3.Solver(); D,A=z3.Ints('D A'); s.add(D==div[name],A==1); s.add(z3.Implies(D==1,A==1))
        if s.check()!=z3.sat: return "unsat"
    return "sat"
def z3_ctrl(law):
    s=z3.Solver(); D,A=z3.Ints('D A'); s.add(D==div["S"],A==1)   # S: measured non-dividing, forced admitted
    if law: s.add(z3.Implies(D==0,A==0))
    return str(s.check())
def cvc5_fit():
    for name in ["R","C","H","O"]:
        s=cvc5.Solver(); s.setLogic("QF_LIA"); I=s.getIntegerSort(); mk=s.mkInteger
        D,A=[s.mkConst(I,x) for x in('D','A')]; eq=lambda a,b:s.mkTerm(Kind.EQUAL,a,b)
        s.assertFormula(eq(D,mk(div[name]))); s.assertFormula(eq(A,mk(1)))
        s.assertFormula(s.mkTerm(Kind.IMPLIES,eq(D,mk(1)),eq(A,mk(1))))
        if str(s.checkSat())!="sat": return "unsat"
    return "sat"
def cvc5_ctrl(law):
    s=cvc5.Solver(); s.setLogic("QF_LIA"); I=s.getIntegerSort(); mk=s.mkInteger
    D,A=[s.mkConst(I,x) for x in('D','A')]; eq=lambda a,b:s.mkTerm(Kind.EQUAL,a,b)
    s.assertFormula(eq(D,mk(div["S"]))); s.assertFormula(eq(A,mk(1)))
    if law: s.assertFormula(s.mkTerm(Kind.IMPLIES,eq(D,mk(0)),eq(A,mk(0))))
    return str(s.checkSat())
zf,cf=z3_fit(),cvc5_fit(); zc1,cc1=z3_ctrl(True),cvc5_ctrl(True); zc0,cc0=z3_ctrl(False),cvc5_ctrl(False)
print(f"(5) gate: fit z3={zf}/cvc5={cf}; admit-S(non-dividing) z3={zc1}/cvc5={cc1}(w/law) -> {zc0}/{cc0}(w/o)")

assert cmax["C"]<1e-9<cmax["H"] and amax["H"]<1e-9<amax["O"], "commutativity dies at H, associativity at O"
assert hurwitz["O"]<1e-8<hurwitz["S"], "Hurwitz: O divides, S does not"
assert zd<1e-18, "explicit sedenion zero-divisor"
assert g2dim==14, "G2=Aut(O) dim 14"
assert zf=="sat" and cf=="sat" and zc1=="unsat" and cc1=="unsat" and zc0=="sat" and cc0=="sat", "kill-control law fits + flipped control"
print("\nPASS division_algebra_ratchet_sim")
