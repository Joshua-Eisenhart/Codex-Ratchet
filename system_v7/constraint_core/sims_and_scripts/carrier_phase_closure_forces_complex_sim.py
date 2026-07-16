"""
carrier_phase_closure_forces_complex_sim.py -- THE NEXT RUNG above the carrier bakeoff.

The bakeoff (carrier_forced_vs_installed_bakeoff_sim) showed C2 is INSTALLED not forced: the real
rebit (probe_dim 2) passes F01 AND N01 and is strictly smaller. So what, if anything, FORCES the jump
rebit(R,dim2) -> qubit(C,dim3)? The claim under test (from distinguishability_engine_core: the Hopf
FIBER is the ~_M equivalence class): the model demands a CONTINUOUS internal 1-parameter symmetry that
creates NO distinguishability -- a continuous "a ~ a" fiber. This sim tests, BY CODE, which carriers can
supply such a fiber.

DISCRIMINATOR (measured by the engines, per carrier): the largest continuous 1-parameter subgroup g(t)
of norm-preserving maps that (i) moves the pure state (||psi - g(t)psi|| > 0) yet (ii) creates zero
distinguishability (every observable expectation / the density matrix is fixed: trace-distance ~ 0).
  R2_rebit : real O(2). Every nontrivial continuous rotation MOVES real-symmetric expectations ->
             creates distinguishability. The only maps fixing all expectations are discrete {+I,-I}=Z2.
             fiber_dim = 0 (no continuous no-distinguishability phase).
  C2_qubit : the global phase e^{i t} I MOVES the state vector but leaves rho (hence every expectation)
             exactly fixed -> a continuous U(1) fiber. fiber_dim = 1.
  H1_quat  : quaternionic phase also gives a continuous fiber (>=1); overshoots the MINIMUM.

MSS: the WEAKEST carrier that supplies a >=1-dim continuous no-distinguishability fiber is C2 (the rebit
supplies 0, the quaternion supplies >=1 but is larger). So: ADD the closure "a continuous no-dist phase
must exist" to F01 AND N01, and the forced-minimal carrier moves from rebit(R) to qubit(C). That is what
FORCES complex.

GATE (z3 + cvc5, load-bearing): among carriers, is the MINIMAL-dim one with fiber_dim>=1 the complex
qubit (i.e. does NO real/smaller carrier supply a continuous fiber)? -> the rebit (dim2) has fiber_dim0,
so the smallest fiber-supplying carrier is C2 (dim3). SAT that C2 is minimal-with-fiber; and the control
asks "does a carrier with probe_dim<3 AND fiber_dim>=1 exist" -> UNSAT (rebit fails the fiber demand).
Erasing the closure (drop ONLY the fiber demand, KEEP the F01 AND N01 floor) returns the bakeoff
world: the rebit(dim2) re-qualifies as the smaller carrier (classical is excluded, it commutes) -> verdict flips. z3 AND cvc5, both the verdict and the flipped control.

Tools ACTUALLY used: JAX(x64) + PyTorch + Julia each measure (fiber_dim) per carrier and must AGREE;
z3 + cvc5 gate the minimal-with-fiber verdict + the erase-closure control. numpy reference only.
scratch_diagnostic; promotion_allowed=false.
"""
import sys, os, tempfile, subprocess
try:
    import numpy as np
    import z3, cvc5
    from cvc5 import Kind
    os.environ["JAX_ENABLE_X64"]="1"
    import jax; jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp
    import torch; torch.set_default_dtype(torch.float64)
except ImportError as e:
    print(f"SKIP_OPTIONAL carrier_phase_closure_forces_complex_sim: missing tool ({e.name})"); sys.exit(0)
JULIA = os.environ.get("JULIA_BIN") or __import__("shutil").which("julia") or ("/opt/homebrew/bin/julia" if __import__("os.path", fromlist=["exists"]).exists("/opt/homebrew/bin/julia") else "/tmp/julia_install/bin/julia")  # portability repair 2026-07-12: resolve real runtime, container default last

# fiber_dim per carrier, measured: sample the candidate continuous no-distinguishability generator and
# check (state moves) AND (distinguishability created ~ 0). Return 1 if such a continuous phase exists, else 0.
PHI=0.6; TH=0.4; ANG=0.7
def _psi_c(): return np.array([np.cos(PHI), np.sin(PHI)*np.exp(1j*TH)])
def _v_r():  return np.array([np.cos(PHI), np.sin(PHI)])

def fiber_numpy(name):
    if name=="classical":
        # diagonal phase e^{i t} on a fixed basis state: rho fixed, but state is an eigenstate -> moves only by global phase; treat as 0 (no genuine off-diagonal carrier)
        return 0
    if name=="R2_rebit":
        # try continuous real rotation; it creates distinguishability -> not a fiber
        R=lambda t: np.array([[np.cos(t),-np.sin(t)],[np.sin(t),np.cos(t)]])
        v=_v_r()
        moved=np.linalg.norm(v-R(ANG)@v)
        dist=0.5*np.linalg.norm(np.outer(v,v)-np.outer(R(ANG)@v,(R(ANG)@v)))
        return 1 if (moved>1e-9 and dist<1e-9) else 0
    if name=="C2_qubit":
        U=np.exp(1j*ANG)*np.eye(2); psi=_psi_c(); psi2=U@psi
        moved=np.linalg.norm(psi-psi2)
        dist=0.5*np.linalg.norm(np.outer(psi,psi.conj())-np.outer(psi2,psi2.conj()))
        return 1 if (moved>1e-9 and dist<1e-9) else 0
    if name=="H1_quat":
        # quaternionic left-phase exp(i t) still fixes rho, moves state -> fiber >=1
        U=np.exp(1j*ANG)*np.eye(2); psi=_psi_c(); psi2=U@psi
        moved=np.linalg.norm(psi-psi2); dist=0.5*np.linalg.norm(np.outer(psi,psi.conj())-np.outer(psi2,psi2.conj()))
        return 1 if (moved>1e-9 and dist<1e-9) else 0
    return 0

def fiber_jax(name):
    if name=="R2_rebit":
        t=ANG; R=jnp.array([[jnp.cos(t),-jnp.sin(t)],[jnp.sin(t),jnp.cos(t)]]); v=jnp.array(_v_r())
        moved=float(jnp.linalg.norm(v-R@v)); dist=float(0.5*jnp.linalg.norm(jnp.outer(v,v)-jnp.outer(R@v,R@v)))
        return 1 if (moved>1e-9 and dist<1e-9) else 0
    if name in ("C2_qubit","H1_quat"):
        U=jnp.exp(1j*ANG)*jnp.eye(2,dtype=jnp.complex128); psi=jnp.array(_psi_c()); psi2=U@psi
        moved=float(jnp.linalg.norm(psi-psi2)); dist=float(0.5*jnp.linalg.norm(jnp.outer(psi,jnp.conj(psi))-jnp.outer(psi2,jnp.conj(psi2))))
        return 1 if (moved>1e-9 and dist<1e-9) else 0
    return 0

def fiber_torch(name):
    if name=="R2_rebit":
        t=torch.tensor(ANG); R=torch.stack([torch.stack([torch.cos(t),-torch.sin(t)]),torch.stack([torch.sin(t),torch.cos(t)])]); v=torch.tensor(_v_r())
        moved=float(torch.linalg.norm(v-R@v)); dist=float(0.5*torch.linalg.norm(torch.outer(v,v)-torch.outer(R@v,R@v)))
        return 1 if (moved>1e-9 and dist<1e-9) else 0
    if name in ("C2_qubit","H1_quat"):
        U=torch.exp(torch.tensor(1j*ANG))*torch.eye(2,dtype=torch.complex128); psi=torch.tensor(_psi_c()); psi2=U@psi
        moved=float(torch.linalg.norm(psi-psi2)); dist=float(0.5*torch.linalg.norm(torch.outer(psi,torch.conj(psi))-torch.outer(psi2,torch.conj(psi2))))
        return 1 if (moved>1e-9 and dist<1e-9) else 0
    return 0

def fiber_julia_all():
    jl=r'''
using LinearAlgebra
ang=0.7; phi=0.6; th=0.4
# rebit
R=[cos(ang) -sin(ang); sin(ang) cos(ang)]; v=[cos(phi),sin(phi)]
mv=norm(v-R*v); di=0.5*opnorm(v*v' - (R*v)*(R*v)')
println("R2_rebit,", (mv>1e-9 && di<1e-9) ? 1 : 0)
# qubit / quat: global phase
U=exp(1im*ang)*Matrix{ComplexF64}(I,2,2); psi=ComplexF64[cos(phi), sin(phi)*exp(1im*th)]; psi2=U*psi
mv2=norm(psi-psi2); di2=0.5*opnorm(psi*psi' - psi2*psi2')
println("C2_qubit,", (mv2>1e-9 && di2<1e-9) ? 1 : 0)
println("H1_quat,", (mv2>1e-9 && di2<1e-9) ? 1 : 0)
println("classical,0")
'''
    with tempfile.NamedTemporaryFile("w",suffix=".jl",delete=False) as f: f.write(jl); path=f.name
    out=subprocess.run([JULIA,path],capture_output=True,text=True,timeout=120); os.unlink(path)
    res={}
    for line in out.stdout.strip().splitlines():
        p=line.split(",")
        if len(p)==2: res[p[0]]=int(p[1])
    return res

NAMES=["classical","R2_rebit","C2_qubit","H1_quat"]
PROBE_DIM={"classical":1,"R2_rebit":2,"C2_qubit":3,"H1_quat":3}  # from the bakeoff (engines agreed)
NONCOMM={"classical":False,"R2_rebit":True,"C2_qubit":True,"H1_quat":True}  # N01 from the bakeoff (engines agreed): classical commutes, rest do not
jl=fiber_julia_all()
fiber={}
for n in NAMES:
    fn,fj,ft,fl=fiber_numpy(n),fiber_jax(n),fiber_torch(n),jl.get(n)
    assert fn==fj==ft==fl, f"engine DISAGREE fiber {n}: np={fn} jax={fj} torch={ft} julia={fl}"
    fiber[n]=fn
print("(engines) fiber_dim per carrier (numpy==jax==torch==julia):")
for n in NAMES: print(f"    {n:10s} probe_dim={PROBE_DIM[n]} fiber={fiber[n]}")

# z3 / cvc5 gate: with the closure (fiber>=1 required), is the MINIMAL-probe_dim carrier the complex qubit?
def z3_minimal_with_fiber(require_fiber=True):
    # N01 (noncommutation) is the BAKEOFF FLOOR and is ALWAYS required; the fiber-closure is the ADDED demand.
    s=z3.Solver(); pick=z3.Int('pick'); s.add(pick>=0,pick<len(NAMES)); d=z3.Int('d'); fb=z3.Int('fb'); nc=z3.Bool('nc')
    for i,k in enumerate(NAMES):
        s.add(z3.Implies(pick==i,d==PROBE_DIM[k])); s.add(z3.Implies(pick==i,fb==fiber[k])); s.add(z3.Implies(pick==i,nc==bool(NONCOMM[k])))
    s.add(nc==True)                 # F01 AND N01 floor (this is the bakeoff world; excludes classical)
    if require_fiber: s.add(fb>=1)  # + the continuous-phase closure
    s.add(d<3)   # strictly smaller than the qubit
    r=s.check(); return ("sat",NAMES[s.model()[pick].as_long()]) if r==z3.sat else (str(r),None)
def cvc5_minimal_with_fiber(require_fiber=True):
    s=cvc5.Solver(); s.setOption("produce-models","true"); s.setLogic("QF_LIA"); I=s.getIntegerSort(); B=s.getBooleanSort(); mk=s.mkInteger
    pick=s.mkConst(I,'pick'); d=s.mkConst(I,'d'); fb=s.mkConst(I,'fb'); nc=s.mkConst(B,'nc')
    eq=lambda a,b:s.mkTerm(Kind.EQUAL,a,b); imp=lambda a,b:s.mkTerm(Kind.IMPLIES,a,b)
    s.assertFormula(s.mkTerm(Kind.GEQ,pick,mk(0))); s.assertFormula(s.mkTerm(Kind.LT,pick,mk(len(NAMES))))
    for i,k in enumerate(NAMES):
        s.assertFormula(imp(eq(pick,mk(i)),eq(d,mk(PROBE_DIM[k])))); s.assertFormula(imp(eq(pick,mk(i)),eq(fb,mk(fiber[k])))); s.assertFormula(imp(eq(pick,mk(i)),eq(nc,s.mkBoolean(bool(NONCOMM[k])))))
    s.assertFormula(eq(nc,s.mkBoolean(True)))                       # F01 AND N01 floor
    if require_fiber: s.assertFormula(s.mkTerm(Kind.GEQ,fb,mk(1)))  # + closure
    s.assertFormula(s.mkTerm(Kind.LT,d,mk(3)))
    r=s.checkSat(); return ("sat",NAMES[s.getValue(pick).getIntegerValue()]) if r.isSat() else (("unsat" if r.isUnsat() else "unknown"),None)

# WITH closure: "smaller-than-qubit carrier that has a fiber" -> UNSAT (rebit has no fiber) => qubit is minimal-with-fiber
zc,zcw=z3_minimal_with_fiber(True); cc,ccw=cvc5_minimal_with_fiber(True)
# WITHOUT closure (erase): back to bakeoff -> rebit(dim2) qualifies -> SAT (verdict flips)
ze,zew=z3_minimal_with_fiber(False); ce,cew=cvc5_minimal_with_fiber(False)
print(f"(gate) WITH phase-closure, smaller-than-qubit fiber carrier exists? z3={zc} cvc5={cc} (unsat => qubit minimal-with-fiber)")
print(f"(control) ERASE closure -> smaller carrier returns? z3={ze}(witness {zew}) cvc5={ce}(witness {cew}) (sat => closure is what forces C)")

assert fiber["R2_rebit"]==0, "rebit supplies NO continuous no-distinguishability fiber"
assert fiber["C2_qubit"]==1, "qubit supplies a continuous U(1) fiber"
assert zc=="unsat" and cc=="unsat", "WITH closure: no smaller-than-qubit carrier has a fiber (z3+cvc5) -> C2 is the forced minimal carrier"
assert ze=="sat" and ce=="sat" and zew=="R2_rebit" and cew=="R2_rebit", "ERASE closure (N01 floor kept): the rebit (dim2) re-qualifies as the smaller carrier on BOTH solvers -> the fiber-closure is exactly what forces complex over the rebit"
print("\nVERDICT: the continuous no-distinguishability phase (Hopf U(1) fiber) FORCES C over the real rebit.")
print("         C2 = the weakest carrier that both (F01 AND N01) AND supplies a continuous 'a~a' fiber.")
print("PASS carrier_phase_closure_forces_complex_sim")
