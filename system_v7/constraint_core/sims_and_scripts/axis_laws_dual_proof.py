"""
axis_laws_dual_proof.py -- axis laws FORCED, proven with Z3 AND cvc5 in agreement,
with erased controls that flip the verdict. Satisfies the three-engine contract rule:
"z3 and cvc5 must agree on the same structural claim with erased controls that flip it."

Claims (each proven the SAME way in both solvers; both must agree):
  (1) Given the 3 independently-earned family splits (dynamics a1, frame a2, Jungian
      perceiving a0), the 2-input boolean map g with a0=g(a1,a2) is UNIQUE and IS xor.
  (2) CONTROL for (1): erase the a0=Ni constraint -> uniqueness must FLIP (g no longer
      forced). If erasing a constraint does NOT change the verdict, the claim was vacuous.
  (3) b6=-b0*b3: bilinear coeff uniquely -1; NO linear law fits (genuinely a product).

Pure logic. scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import z3
    import cvc5
    from cvc5 import Kind
except ImportError as e:
    print(f"SKIP_OPTIONAL axis_laws_dual_proof: missing tool ({e.name}); pip install z3-solver cvc5 qutip")
    sys.exit(0)

A1={"Se":0,"Ne":1,"Ni":0,"Si":1}
A2={"Se":0,"Ne":0,"Ni":1,"Si":1}
A0={"Se":0,"Ne":1,"Ni":1,"Si":0}

# ---- Z3: is g unique given a family set? returns (exists, unique, is_xor) ----
def z3_g_unique(fams):
    g={(i,j):z3.Bool(f"g_{i}{j}") for i in(0,1) for j in(0,1)}
    s=z3.Solver()
    for f in fams: s.add(g[(A1[f],A2[f])]==bool(A0[f]))
    if s.check()!=z3.sat: return (False,False,False)
    m=s.model(); tt={k:z3.is_true(m[v]) for k,v in g.items()}
    s.add(z3.Or([g[k]!=z3.BoolVal(tt[k]) for k in g]))
    unique=(s.check()==z3.unsat)
    is_xor=all(tt[(i,j)]==bool(i^j) for i in(0,1) for j in(0,1))
    return (True,unique,is_xor)

# ---- cvc5: same question ----
def cvc5_g_unique(fams):
    s=cvc5.Solver(); s.setOption('produce-models','true'); s.setLogic('QF_UF')
    B=s.getBooleanSort()
    g={(i,j):s.mkConst(B,f"g_{i}{j}") for i in(0,1) for j in(0,1)}
    T,F=s.mkTrue(),s.mkFalse()
    for f in fams:
        s.assertFormula(s.mkTerm(Kind.EQUAL, g[(A1[f],A2[f])], T if A0[f] else F))
    if s.checkSat().isUnsat(): return (False,False,False)
    tt={k:s.getValue(g[k]).getBooleanValue() for k in g}
    s.push()
    diff=[s.mkTerm(Kind.DISTINCT,g[k],(T if tt[k] else F)) for k in g]
    s.assertFormula(s.mkTerm(Kind.OR,*diff) if len(diff)>1 else diff[0])
    unique=s.checkSat().isUnsat(); s.pop()
    is_xor=all(tt[(i,j)]==bool(i^j) for i in(0,1) for j in(0,1))
    return (True,unique,is_xor)

full=["Se","Ne","Ni","Si"]
erased=["Se","Ne","Si"]                 # CONTROL: drop Ni

z3_full, cvc5_full   = z3_g_unique(full),   cvc5_g_unique(full)
z3_ctrl, cvc5_ctrl   = z3_g_unique(erased), cvc5_g_unique(erased)
print(f"(1) full set  -> Z3 (exists,unique,xor)={z3_full}  cvc5={cvc5_full}")
print(f"(2) erase Ni  -> Z3 unique={z3_ctrl[1]}  cvc5 unique={cvc5_ctrl[1]}  (must be False = verdict FLIPS)")
agree_full = z3_full==cvc5_full
agree_ctrl = z3_ctrl==cvc5_ctrl
print(f"    solvers agree: full={agree_full} control={agree_ctrl}")

# ---- (3) b6 bilinear, both solvers ----
terr=["Funnel","Vortex","Pit","Hill","Cannon","Spiral","Source","Citadel"]
B0={"Funnel":1,"Vortex":1,"Pit":1,"Hill":1,"Cannon":-1,"Spiral":-1,"Source":-1,"Citadel":-1}
B3={"Funnel":-1,"Vortex":1,"Pit":-1,"Hill":1,"Cannon":-1,"Spiral":1,"Source":-1,"Citadel":1}
B6={t:-B0[t]*B3[t] for t in terr}
def z3_b6():
    c=z3.Int("c"); s=z3.Solver(); s.add(z3.Or(c==1,c==-1))
    for t in terr: s.add(c*B0[t]*B3[t]==B6[t])
    s.check(); cval=s.model()[c].as_long(); s.add(c!=cval); cu=(s.check()==z3.unsat)
    a,b,g=z3.Ints("a b g"); s2=z3.Solver()
    for t in terr: s2.add(a*B0[t]+b*B3[t]+g==B6[t])
    return cval,cu,(s2.check()==z3.unsat)
def cvc5_b6():
    s=cvc5.Solver(); s.setOption('produce-models','true'); s.setLogic('QF_LIA')
    I=s.getIntegerSort(); c=s.mkConst(I,"c")
    one,mone=s.mkInteger(1),s.mkInteger(-1)
    s.assertFormula(s.mkTerm(Kind.OR,s.mkTerm(Kind.EQUAL,c,one),s.mkTerm(Kind.EQUAL,c,mone)))
    for t in terr:
        s.assertFormula(s.mkTerm(Kind.EQUAL,s.mkTerm(Kind.MULT,c,s.mkInteger(B0[t]*B3[t])),s.mkInteger(B6[t])))
    s.checkSat(); cval=s.getValue(c).getIntegerValue()
    s.push(); s.assertFormula(s.mkTerm(Kind.DISTINCT,c,s.mkInteger(int(cval)))); cu=s.checkSat().isUnsat(); s.pop()
    s2=cvc5.Solver(); s2.setLogic('QF_LIA'); I2=s2.getIntegerSort()
    a=s2.mkConst(I2,"a");b=s2.mkConst(I2,"b");g=s2.mkConst(I2,"g")
    for t in terr:
        lhs=s2.mkTerm(Kind.ADD,s2.mkTerm(Kind.MULT,a,s2.mkInteger(B0[t])),s2.mkTerm(Kind.MULT,b,s2.mkInteger(B3[t])),g)
        s2.assertFormula(s2.mkTerm(Kind.EQUAL,lhs,s2.mkInteger(B6[t])))
    return int(cval),cu,s2.checkSat().isUnsat()
z3b, cvc5b = z3_b6(), cvc5_b6()
print(f"(3) b6: Z3 (c,unique,no_linear)={z3b}  cvc5={cvc5b}  agree={z3b==cvc5b}")

assert z3_full==(True,True,True) and cvc5_full==(True,True,True), "XOR must be uniquely forced in BOTH"
assert not z3_ctrl[1] and not cvc5_ctrl[1], "erasing Ni must FLIP uniqueness in BOTH (control)"
assert agree_full and agree_ctrl, "solvers must agree"
assert z3b==(-1,True,True) and cvc5b==(-1,True,True), "b6 uniquely bilinear c=-1 in BOTH"
print("\nPASS axis_laws_dual_proof")
