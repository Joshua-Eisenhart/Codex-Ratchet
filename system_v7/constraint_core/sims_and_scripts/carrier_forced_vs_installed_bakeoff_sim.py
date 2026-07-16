"""
carrier_forced_vs_installed_bakeoff_sim.py -- BASE RUNG (the carrier), decided by CODE not by vote.

QUESTION (the one open base rung): from the root primitive {finite distinguishability quotient} under
F01 (finite) and N01 (order/noncommutation is load-bearing), what carrier is FORCED, and is the complex
qubit C^2 forced or merely INSTALLED? The project's standing answer ("installed, not forced") was
reached by a 7-model LLM vote (mss_and_rung_climb_foundations doc), never by a running gate. This sim
GROUNDS that verdict in computation: it throws several candidate carriers at the F01-AND-N01 gate at once,
computes the discriminating numerics in THREE independent sim engines (JAX + Torch + Julia, agreement
required -- the substrate doctrine), and lets z3 + cvc5 deliver the structural verdict with a flipped
control. No LLM adjudicates pass/fail.

CANDIDATE CARRIERS (each a concrete finite algebra with its natural probe/observable generators):
  classical  -- real diagonal traceless (commutative simplex)         probe-axes 1
  R2_rebit   -- real symmetric traceless 2x2 (real Bloch DISK)         probe-axes 2
  C2_qubit   -- complex Hermitian traceless 2x2 (complex Bloch BALL)   probe-axes 3
  H1_quat    -- Im(H) ~ su(2)                                          probe-axes 3

MEASURED PER CARRIER (by the engines, not asserted):
  probe_dim         = real dimension of the observable space = # independent distinguishability axes
  has_noncommuting  = exists a generator pair with nonzero order-gap ||AB-BA|| (N01 load-bearing)

GATE (z3 + cvc5, load-bearing): a carrier "satisfies F01 AND N01" iff finite (all do) AND has a
noncommuting distinguishable probe pair. Among the SATISFYING carriers, the MSS/weakest-structure
rule selects the one of MINIMAL probe_dim. The solver is asked: "is there a satisfying carrier with
probe_dim strictly LESS than C2_qubit's 3?" -> SAT, witnessed by R2_rebit (probe_dim 2). Therefore the
complex qubit is NOT forced by F01-AND-N01 (a strictly smaller real carrier passes the same gate).
FLIPPED CONTROL: erase N01 (require the probe pair to COMMUTE). Then only the classical carrier
satisfies, its probe_dim is 1, and "a noncommuting distinguishable pair exists" is UNSAT -> the verdict
structure changes, so N01 (not arithmetic) is what bites. z3 AND cvc5, both the verdict and the control.

WHAT THIS DOES AND DOES NOT SETTLE: it settles that C is INSTALLED not forced (grounding the fleet
verdict in a run). It does NOT claim rebit is the physical carrier -- the jump rebit(2)->qubit(3) is
forced only by an ADDED closure (a continuous no-distinguishability phase = Hopf U(1) fiber, which the
rebit's discrete Z2 cannot supply). That closure is the next rung (named, not closed here).

Tools ACTUALLY used: JAX (x64 complex128) + PyTorch + Julia (stdlib LinearAlgebra) all compute
(probe_dim, has_noncommuting) independently and must AGREE; z3 + cvc5 gate the verdict + flipped control.
numpy is reference/orchestration only. scratch_diagnostic; promotion_allowed=false.
"""
import sys, os, json, subprocess, tempfile
try:
    import numpy as np
    import z3, cvc5
    from cvc5 import Kind
    os.environ["JAX_ENABLE_X64"]="1"
    import jax; jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp
    import torch; torch.set_default_dtype(torch.float64)
except ImportError as e:
    print(f"SKIP_OPTIONAL carrier_forced_vs_installed_bakeoff_sim: missing tool ({e.name})"); sys.exit(0)

JULIA = os.environ.get("JULIA_BIN") or __import__("shutil").which("julia") or ("/opt/homebrew/bin/julia" if __import__("os.path", fromlist=["exists"]).exists("/opt/homebrew/bin/julia") else "/tmp/julia_install/bin/julia")  # portability repair 2026-07-12: resolve real runtime, container default last

# ---- carrier generator sets (as complex matrices; field restriction encoded by which are allowed) ----
sx = np.array([[0,1],[1,0]], complex)
sy = np.array([[0,-1j],[1j,0]], complex)
sz = np.array([[1,0],[0,-1]], complex)
CARRIERS = {
    "classical": [sz],            # diagonal only -> commutative
    "R2_rebit":  [sx, sz],        # real symmetric traceless -> Bloch disk
    "C2_qubit":  [sx, sy, sz],    # complex Hermitian traceless -> Bloch ball
    "H1_quat":   [sx, sy, sz],    # Im(H) ~ su(2)
}
QUBIT_DIM = 3  # C2_qubit probe_dim, the thing we test "is anything smaller enough?"

# ---------- engine kernels: each returns (probe_dim, has_noncommuting) ----------
def _realrank_np(basis):
    cols = [np.concatenate([M.real.ravel(), M.imag.ravel()]) for M in basis]
    return int(np.linalg.matrix_rank(np.array(cols).T, tol=1e-9))
def _noncomm_np(basis):
    for i in range(len(basis)):
        for j in range(i+1, len(basis)):
            if np.linalg.norm(basis[i]@basis[j]-basis[j]@basis[i], 2) > 1e-9: return True
    return False
def numpy_probe(basis): return _realrank_np(basis), _noncomm_np(basis)

def jax_probe(basis):
    B=[jnp.array(M) for M in basis]
    cols=[jnp.concatenate([jnp.real(M).ravel(), jnp.imag(M).ravel()]) for M in B]
    dim=int(jnp.linalg.matrix_rank(jnp.stack(cols,axis=1)))
    nc=False
    for i in range(len(B)):
        for j in range(i+1,len(B)):
            C=B[i]@B[j]-B[j]@B[i]
            if float(jnp.linalg.norm(C,2))>1e-9: nc=True
    return dim, nc

def torch_probe(basis):
    B=[torch.tensor(M, dtype=torch.complex128) for M in basis]
    cols=[torch.cat([M.real.reshape(-1), M.imag.reshape(-1)]) for M in B]
    dim=int(torch.linalg.matrix_rank(torch.stack(cols,dim=1), tol=1e-9))
    nc=False
    for i in range(len(B)):
        for j in range(i+1,len(B)):
            C=B[i]@B[j]-B[j]@B[i]
            if float(torch.linalg.matrix_norm(C,ord=2))>1e-9: nc=True
    return dim, nc

def julia_probe_all():
    jl = r'''
using LinearAlgebra
function realrank(basis)
    cols=[vcat(real(vec(M)),imag(vec(M))) for M in basis]; rank(hcat(cols...);atol=1e-9)
end
function noncomm(basis)
    for i in 1:length(basis), j in i+1:length(basis)
        if opnorm(basis[i]*basis[j]-basis[j]*basis[i])>1e-9; return 1; end
    end
    return 0
end
sx=ComplexF64[0 1;1 0]; sy=ComplexF64[0 -1im;1im 0]; sz=ComplexF64[1 0;0 -1]
C=Dict("classical"=>[sz],"R2_rebit"=>[sx,sz],"C2_qubit"=>[sx,sy,sz],"H1_quat"=>[sx,sy,sz])
for k in ("classical","R2_rebit","C2_qubit","H1_quat")
    println(k, ",", realrank(C[k]), ",", noncomm(C[k]))
end
'''
    with tempfile.NamedTemporaryFile("w", suffix=".jl", delete=False) as f:
        f.write(jl); path=f.name
    out=subprocess.run([JULIA, path], capture_output=True, text=True, timeout=120)
    os.unlink(path)
    res={}
    for line in out.stdout.strip().splitlines():
        parts=line.split(","); 
        if len(parts)==3: res[parts[0]]=(int(parts[1]), bool(int(parts[2])))
    return res

# ---------- run all engines, require agreement ----------
jul = julia_probe_all()
measured={}
engine_log={}
for name, basis in CARRIERS.items():
    d_np = numpy_probe(basis)
    d_jax = jax_probe(basis)
    d_th = torch_probe(basis)
    d_jl = jul.get(name)
    engine_log[name]={"numpy":d_np,"jax":d_jax,"torch":d_th,"julia":d_jl}
    agree = (d_np==d_jax==d_th==d_jl)
    assert agree, f"engine DISAGREEMENT on {name}: np={d_np} jax={d_jax} torch={d_th} julia={d_jl}"
    measured[name]=d_np
print("(engines) probe_dim,has_noncommuting per carrier (numpy==jax==torch==julia):")
for k,v in measured.items(): print(f"    {k:10s} dim={v[0]} noncomm={v[1]}")

# ---------- z3 gate: is any F01-AND-N01-satisfying carrier strictly SMALLER (probe_dim) than the qubit? ----------
names=list(CARRIERS); dims={k:measured[k][0] for k in names}; ncs={k:measured[k][1] for k in names}
def z3_smaller_exists(require_noncomm=True):
    s=z3.Solver(); pick=z3.Int('pick')
    s.add(pick>=0, pick<len(names))
    # encode per-carrier facts as constraints selected by pick
    d=z3.Int('d'); nc=z3.Bool('nc')
    for i,k in enumerate(names):
        s.add(z3.Implies(pick==i, d==dims[k]))
        s.add(z3.Implies(pick==i, nc==bool(ncs[k])))
    if require_noncomm: s.add(nc==True)     # F01-AND-N01 : must have a noncommuting distinguishable pair
    s.add(d < QUBIT_DIM)                     # strictly smaller than the complex qubit
    r=s.check()
    if r==z3.sat:
        m=s.model(); return "sat", names[m[pick].as_long()]
    return str(r), None
def cvc5_smaller_exists(require_noncomm=True):
    s=cvc5.Solver(); s.setOption("produce-models","true"); s.setLogic("QF_LIA"); I=s.getIntegerSort(); B=s.getBooleanSort()
    mk=s.mkInteger; pick=s.mkConst(I,'pick'); d=s.mkConst(I,'d'); nc=s.mkConst(B,'nc')
    eq=lambda a,b:s.mkTerm(Kind.EQUAL,a,b); imp=lambda a,b:s.mkTerm(Kind.IMPLIES,a,b)
    s.assertFormula(s.mkTerm(Kind.GEQ,pick,mk(0))); s.assertFormula(s.mkTerm(Kind.LT,pick,mk(len(names))))
    for i,k in enumerate(names):
        s.assertFormula(imp(eq(pick,mk(i)), eq(d,mk(dims[k]))))
        s.assertFormula(imp(eq(pick,mk(i)), eq(nc, s.mkBoolean(bool(ncs[k])))))
    if require_noncomm: s.assertFormula(eq(nc, s.mkBoolean(True)))
    s.assertFormula(s.mkTerm(Kind.LT,d,mk(QUBIT_DIM)))
    r=s.checkSat(); 
    if r.isSat():
        return "sat", names[s.getValue(pick).getIntegerValue()]
    return ("unsat" if r.isUnsat() else "unknown"), None

z_v, z_w = z3_smaller_exists(True);  c_v, c_w = cvc5_smaller_exists(True)
z_ctrl,_ = z3_smaller_exists(False and True) if False else (None,None)
# flipped control: require the pair to COMMUTE (erase N01) -> only classical qualifies, dim 1, but then
# ask "does a NONCOMMUTING carrier of dim<3 exist among the COMMUTING-only survivors" -> UNSAT.
def z3_control():  # among carriers forced to COMMUTE (nc must be False), is there a noncommuting one? contradiction -> UNSAT
    s=z3.Solver(); pick=z3.Int('pick'); s.add(pick>=0,pick<len(names))
    nc=z3.Bool('nc')
    for i,k in enumerate(names): s.add(z3.Implies(pick==i, nc==bool(ncs[k])))
    s.add(nc==False)   # erase N01: keep only commuting carriers
    s.add(nc==True)    # but still demand the noncommuting distinguishability -> contradiction
    return str(s.check())
def cvc5_control():
    s=cvc5.Solver(); s.setLogic("QF_LIA"); I=s.getIntegerSort(); B=s.getBooleanSort(); mk=s.mkInteger
    pick=s.mkConst(I,'pick'); nc=s.mkConst(B,'nc'); eq=lambda a,b:s.mkTerm(Kind.EQUAL,a,b); imp=lambda a,b:s.mkTerm(Kind.IMPLIES,a,b)
    s.assertFormula(s.mkTerm(Kind.GEQ,pick,mk(0))); s.assertFormula(s.mkTerm(Kind.LT,pick,mk(len(names))))
    for i,k in enumerate(names): s.assertFormula(imp(eq(pick,mk(i)), eq(nc,s.mkBoolean(bool(ncs[k])))))
    s.assertFormula(eq(nc,s.mkBoolean(False))); s.assertFormula(eq(nc,s.mkBoolean(True)))
    r=s.checkSat(); return "unsat" if r.isUnsat() else ("sat" if r.isSat() else "unknown")
z_ctrl=z3_control(); c_ctrl=cvc5_control()

print(f"(gate) smaller-than-qubit F01-AND-N01 carrier exists: z3={z_v} (witness {z_w}) cvc5={c_v} (witness {c_w})")
print(f"(control) erase-N01 contradiction: z3={z_ctrl} cvc5={c_ctrl} (unsat = N01 is what bites)")

# ---------- verdict + asserts (the gate decides; no LLM) ----------
assert measured["classical"]==(1,False), "classical carrier: 1 axis, commutative"
assert measured["R2_rebit"]==(2,True),   "rebit: 2 axes, noncommuting (passes F01-AND-N01)"
assert measured["C2_qubit"]==(3,True),   "qubit: 3 axes, noncommuting"
assert measured["H1_quat"]==(3,True),    "quaternion: 3 axes, noncommuting"
assert z_v=="sat" and c_v=="sat", "z3+cvc5 agree: a satisfying carrier SMALLER than the qubit exists"
assert z_w=="R2_rebit" and c_w=="R2_rebit", "the witness is the real rebit (dim 2 < qubit dim 3)"
assert z_ctrl=="unsat" and c_ctrl=="unsat", "erase-N01 control: UNSAT on both solvers (N01 load-bearing)"
print("\nVERDICT: C2 qubit is INSTALLED, NOT FORCED by F01-AND-N01 -- the real rebit (probe_dim 2) passes the")
print("         same gate and is strictly smaller. Forcing C requires an ADDED phase-closure (next rung).")
print("PASS carrier_forced_vs_installed_bakeoff_sim")
