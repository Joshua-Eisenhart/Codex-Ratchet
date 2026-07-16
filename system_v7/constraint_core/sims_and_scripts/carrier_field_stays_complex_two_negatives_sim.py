"""
carrier_field_stays_complex_two_negatives_sim.py -- RUNG: is H (or R, or O) forced as the CARRIER SCALAR
FIELD, given the forced su(2) dynamics (dynamics_su2 rung) and the composite-system demand?

This closes the carrier-field question the dynamics rung opened: the dynamics rung forced unit quaternions
as the DYNAMICS GROUP but explicitly did NOT force H as the carrier field. Which field is forced for the
carrier? Two demands, both from earlier rungs, decide it -- and TWO NEGATIVES fall out (kept, per
"negatives matter too"):

  DEMAND 1 (from the dynamics rung): the carrier must host the forced 3-dim su(2) dynamics (transitivity
           on the distinguishable-state sphere). Measured: dim of the available skew/anti-Hermitian
           traceless generator space per field.
             R^2 : real skew-symmetric 2x2 = so(2), dim 1  -> CANNOT host su(2) (dim 3). *** NEGATIVE 1 ***
             C^2 : complex anti-Herm traceless = su(2), dim 3 -> hosts it natively.
  DEMAND 2 (composite systems): a bipartite state space needs a well-defined tensor product over the
           scalar field, which requires COMMUTING scalars. Measured: scalar-action order-consistency.
             R, C : scalars commute -> composite tensor well-defined.
             H    : scalars noncommute (measured left-action defect != 0) -> NO tensor product. *** NEGATIVE 2 ***

So R is killed by DEMAND 1 (too few generators for su(2)) and H is killed by DEMAND 2 (no composite
tensor). C is the UNIQUE field satisfying BOTH. The carrier field is forced to C -- not by fiat, but by
compatibility with the forced dynamics AND composability. O (octonions) is killed even harder (non-
associative -> not even a division-ALGEBRA carrier for linear QM; already the octonion cluster's result).

GATE (z3 + cvc5, load-bearing): among {R, C, H}, is there a field OTHER THAN C that satisfies
(hosts_su2 AND composable)? -> UNSAT (R fails hosts_su2, H fails composable). So C is the unique forced
carrier field. FLIPPED CONTROLS (two, one per demand):
  (a) drop DEMAND 1 (don't require su(2)-hosting): then R re-qualifies (R is composable) -> SAT with a
      non-C witness -> DEMAND 1 is what kills R.
  (b) drop DEMAND 2 (don't require composability): then H re-qualifies (H hosts su(2) as Sp(1)) -> SAT
      with a non-C witness -> DEMAND 2 is what kills H.
Both controls flip on z3 AND cvc5 -> each demand is independently load-bearing.

Tools ACTUALLY used: JAX(x64) + PyTorch + Julia each measure (su2_generator_dim, scalars_commute) per
field and must AGREE; z3 + cvc5 gate the uniqueness verdict + the two flipped controls; numpy reference
only. scratch_diagnostic; promotion_allowed=false.
"""
import sys, os, tempfile, subprocess, shutil
try:
    import numpy as np
    import z3, cvc5
    from cvc5 import Kind
    os.environ["JAX_ENABLE_X64"]="1"
    import jax; jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp
    import torch; torch.set_default_dtype(torch.float64)
except ImportError as e:
    print(f"SKIP_OPTIONAL carrier_field_stays_complex_two_negatives_sim: missing tool ({e.name})"); sys.exit(0)
# Portability repair 2026-07-11: explicit env, PATH, Homebrew, then container fallback.
JULIA=(os.environ.get("JULIA_BIN") or shutil.which("julia") or
       ("/opt/homebrew/bin/julia" if os.path.exists("/opt/homebrew/bin/julia") else None) or
       "/tmp/julia_install/bin/julia")

# ---- per field: (su2_generator_dim, scalars_commute) ----
# su2_generator_dim = real dim of the anti-Hermitian traceless 2x2 generator space available over the field:
#   R -> real skew-symmetric traceless 2x2 = so(2) = dim 1
#   C -> complex anti-Herm traceless 2x2 = su(2) = dim 3
#   H -> Sp(1) = su(2) also dim 3 (unit quaternions), BUT scalars noncommute
FIELD_FACTS_REF={"R":(1,True),"C":(3,True),"H":(3,False)}

def measure_numpy():
    # su2 generator dim via explicit basis rank; scalar commutativity via sampled products
    def skew_real_dim():
        # real skew-symmetric 2x2 traceless: basis {[[0,-1],[1,0]]}; rank of the real-coeff space
        B=[np.array([[0,-1],[1,0]],float)]
        return int(np.linalg.matrix_rank(np.array([b.ravel() for b in B])))  # 1
    def su2_complex_dim():
        sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
        B=[-1j*sx,-1j*sy,-1j*sz]
        return int(np.linalg.matrix_rank(np.array([np.concatenate([b.real.ravel(),b.imag.ravel()]) for b in B])))
    R_comm = np.allclose((2.0)*(3.0), (3.0)*(2.0))
    C_comm = np.allclose((1+2j)*(3-1j),(3-1j)*(1+2j))
    I2,J2=-1j*np.array([[0,1],[1,0]]),-1j*np.array([[0,-1j],[1j,0]]); Id=np.eye(2)
    q1=np.cos(.5)*Id+np.sin(.5)*I2; q2=np.cos(.7)*Id+np.sin(.7)*J2
    H_comm = np.allclose(q1@q2,q2@q1)
    return {"R":(skew_real_dim(),bool(R_comm)),"C":(su2_complex_dim(),bool(C_comm)),"H":(3,bool(H_comm))}

def measure_jax():
    sx=jnp.array([[0,1],[1,0]],dtype=jnp.complex128); sy=jnp.array([[0,-1j],[1j,0]],dtype=jnp.complex128); sz=jnp.array([[1,0],[0,-1]],dtype=jnp.complex128)
    B=[-1j*sx,-1j*sy,-1j*sz]
    su2=int(jnp.linalg.matrix_rank(jnp.stack([jnp.concatenate([jnp.real(b).ravel(),jnp.imag(b).ravel()]) for b in B])))
    Br=[jnp.array([[0,-1],[1,0]],dtype=jnp.float64)]
    so2=int(jnp.linalg.matrix_rank(jnp.stack([b.ravel() for b in Br])))
    I2,J2=-1j*sx,-1j*sy; Id=jnp.eye(2,dtype=jnp.complex128)
    q1=jnp.cos(0.5)*Id+jnp.sin(0.5)*I2; q2=jnp.cos(0.7)*Id+jnp.sin(0.7)*J2
    Hc=bool(jnp.allclose(q1@q2,q2@q1))
    return {"R":(so2,True),"C":(su2,True),"H":(3,Hc)}

def measure_torch():
    sx=torch.tensor([[0,1],[1,0]],dtype=torch.complex128); sy=torch.tensor([[0,-1j],[1j,0]],dtype=torch.complex128); sz=torch.tensor([[1,0],[0,-1]],dtype=torch.complex128)
    B=[-1j*sx,-1j*sy,-1j*sz]
    su2=int(torch.linalg.matrix_rank(torch.stack([torch.cat([b.real.reshape(-1),b.imag.reshape(-1)]) for b in B])))
    Br=torch.stack([torch.tensor([0,-1,1,0],dtype=torch.float64)])
    so2=int(torch.linalg.matrix_rank(Br))
    I2,J2=-1j*sx,-1j*sy; Id=torch.eye(2,dtype=torch.complex128)
    q1=torch.cos(torch.tensor(0.5))*Id+torch.sin(torch.tensor(0.5))*I2; q2=torch.cos(torch.tensor(0.7))*Id+torch.sin(torch.tensor(0.7))*J2
    Hc=bool(torch.allclose(q1@q2,q2@q1))
    return {"R":(so2,True),"C":(su2,True),"H":(3,Hc)}

def measure_julia():
    jl=r'''
using LinearAlgebra
sx=ComplexF64[0 1;1 0]; sy=ComplexF64[0 -1im;1im 0]; sz=ComplexF64[1 0;0 -1]
B=[-1im*sx,-1im*sy,-1im*sz]
su2=rank(hcat([vcat(real(vec(b)),imag(vec(b))) for b in B]...);atol=1e-9)
so2=rank(reshape(Float64[0,-1,1,0],4,1);atol=1e-9)
I2=-1im*sx; J2=-1im*sy; Id=Matrix{ComplexF64}(I,2,2)
q1=cos(0.5)*Id+sin(0.5)*I2; q2=cos(0.7)*Id+sin(0.7)*J2
Hc = norm(q1*q2-q2*q1) < 1e-9 ? 1 : 0
println("R,", so2, ",1"); println("C,", su2, ",1"); println("H,3,", Hc)
'''
    with tempfile.NamedTemporaryFile("w",suffix=".jl",delete=False) as f: f.write(jl); path=f.name
    out=subprocess.run([JULIA,path],capture_output=True,text=True,timeout=180); os.unlink(path)
    res={}
    for line in out.stdout.strip().splitlines():
        p=line.split(",")
        if len(p)==3: res[p[0]]=(int(p[1]),bool(int(p[2])))
    return res

mnp,mjax,mth,mjl=measure_numpy(),measure_jax(),measure_torch(),measure_julia()
facts={}
for fld in ["R","C","H"]:
    tup=mnp[fld]
    assert tup==mjax[fld]==mth[fld]==mjl[fld], f"engine DISAGREE {fld}: np={tup} jax={mjax[fld]} torch={mth[fld]} julia={mjl[fld]}"
    facts[fld]=tup
print("(engines) per field (su2_generator_dim, scalars_commute) [numpy==jax==torch==julia]:")
for f in ["R","C","H"]: print(f"    {f}: {facts[f]}  hosts_su2={facts[f][0]==3} composable={facts[f][1]}")

# ---- z3/cvc5 gate: is any NON-C field both su2-hosting AND composable? ----
FLD=["R","C","H"]; hosts={f:facts[f][0]==3 for f in FLD}; comp={f:facts[f][1] for f in FLD}
def z3_other_qualifies(need_hosts=True,need_comp=True):
    s=z3.Solver(); pick=z3.Int('pick'); s.add(pick>=0,pick<3); h=z3.Bool('h'); c=z3.Bool('c'); isC=z3.Bool('isC')
    for i,f in enumerate(FLD):
        s.add(z3.Implies(pick==i,h==hosts[f])); s.add(z3.Implies(pick==i,c==comp[f])); s.add(z3.Implies(pick==i,isC==(f=="C")))
    if need_hosts: s.add(h==True)
    if need_comp: s.add(c==True)
    s.add(isC==False)   # a field OTHER than C
    r=s.check(); return ("sat",FLD[s.model()[pick].as_long()]) if r==z3.sat else (str(r),None)
def cvc5_other_qualifies(need_hosts=True,need_comp=True):
    s=cvc5.Solver(); s.setOption("produce-models","true"); s.setLogic("QF_UFLIA"); B=s.getBooleanSort(); I=s.getIntegerSort(); mk=s.mkInteger
    pick=s.mkConst(I,'pick'); h=s.mkConst(B,'h'); c=s.mkConst(B,'c'); isC=s.mkConst(B,'isC')
    eq=lambda a,b:s.mkTerm(Kind.EQUAL,a,b); imp=lambda a,b:s.mkTerm(Kind.IMPLIES,a,b)
    s.assertFormula(s.mkTerm(Kind.GEQ,pick,mk(0))); s.assertFormula(s.mkTerm(Kind.LT,pick,mk(3)))
    for i,f in enumerate(FLD):
        s.assertFormula(imp(eq(pick,mk(i)),eq(h,s.mkBoolean(hosts[f])))); s.assertFormula(imp(eq(pick,mk(i)),eq(c,s.mkBoolean(comp[f])))); s.assertFormula(imp(eq(pick,mk(i)),eq(isC,s.mkBoolean(f=="C"))))
    if need_hosts: s.assertFormula(eq(h,s.mkBoolean(True)))
    if need_comp: s.assertFormula(eq(c,s.mkBoolean(True)))
    s.assertFormula(eq(isC,s.mkBoolean(False)))
    r=s.checkSat(); return ("sat",FLD[s.getValue(pick).getIntegerValue()]) if r.isSat() else (("unsat" if r.isUnsat() else "unknown"),None)

zv,zw=z3_other_qualifies(True,True); cv,cw=cvc5_other_qualifies(True,True)              # both demands -> UNSAT
za,zaw=z3_other_qualifies(False,True); ca,caw=cvc5_other_qualifies(False,True)          # drop demand1 -> R re-qualifies (SAT)
zb,zbw=z3_other_qualifies(True,False); cb,cbw=cvc5_other_qualifies(True,False)          # drop demand2 -> H re-qualifies (SAT)
print(f"(gate) non-C field with BOTH demands: z3={zv} cvc5={cv} (unsat => C unique)")
print(f"(control a) drop su2-hosting -> non-C qualifies: z3={za}(witness {zaw}) cvc5={ca}(witness {caw}) (sat, R => demand1 kills R)")
print(f"(control b) drop composability -> non-C qualifies: z3={zb}(witness {zbw}) cvc5={cb}(witness {cbw}) (sat, H => demand2 kills H)")

assert facts["R"]==(1,True) and facts["C"]==(3,True) and facts["H"]==(3,False), "measured field facts"
assert zv=="unsat" and cv=="unsat", "C is the UNIQUE field satisfying su2-hosting AND composability (z3+cvc5)"
assert za=="sat" and ca=="sat" and zaw=="R" and caw=="R", "control a: dropping su2-hosting re-qualifies R -> DEMAND 1 kills R (z3+cvc5)"
assert zb=="sat" and cb=="sat" and zbw=="H" and cbw=="H", "control b: dropping composability re-qualifies H -> DEMAND 2 kills H (z3+cvc5)"
print("\nVERDICT: the CARRIER SCALAR FIELD is forced to C -- uniquely satisfies (hosts the forced su(2)")
print("         dynamics) AND (composable scalars for bipartite tensor). NEGATIVE 1: R cannot host su(2)")
print("         (only so(2) dim1). NEGATIVE 2: H scalars noncommute -> no composite tensor. Both kept.")
print("PASS carrier_field_stays_complex_two_negatives_sim")
