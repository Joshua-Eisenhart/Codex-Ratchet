"""
coupled_coratchet_dualloop_sim.py -- Layer 17.5. THE COUPLED CO-RATCHET: entropy ratchet and
operator ratchet run as ONE loop around the 720deg double cover (inner + outer 4-beat loops),
where each beat's operator acts on the state the previous beat left -- the two ratchets constrain
each other rather than being tested separately. Implements the owner's DUAL_LOOP_SPINOR_GRAMMAR
(a documented runtime GAP: the grammar was "not yet modeled as first-class objects"). Loops the
Landauer (16.1), einselection (16.2) and noncommutation (16.7) bridges back in. Also the owner's
Carnot/Szilard structural analogy: an engine pumping entropy around an information cycle.
NOT ToE validation -- an internal deepening of the geometric constraint ratchet.

Grounded in DUAL_LOOP_SPINOR_GRAMMAR.md:
  Left-handed engine  = cooling OUTER, heating INNER;  Right-handed = heating OUTER, cooling INNER.
  The difference is the PLACEMENT/ORDER of the loops, not "one heats one cools".

Operators (model-aligned):
  COOL = amplitude damping toward a pure pointer |0> (NON-UNITAL, source-locked terrain sigma-;
         S -> 0, the Landauer erasure limit).   HEAT = rotation-into-coherence + dephase (S up).

THREE results:
 (A) Cooling drives S->0 (pure pointer, erasure); heating drives S->1 (max mixed). The two are a
     genuine ratchet pair with opposite fixed points.
 (B) COUPLED LOOP, CHIRALITY ASYMMETRY: around the same 4-beat loop the LEFT ordering (cool-first)
     and RIGHT ordering (heat-first) pump DIFFERENT net entropy -- and LEFT-minus-RIGHT net flux is
     SIGN-CONSISTENT across 200 random probes (a robust chirality signature, not probe-dependent).
 (C) The two orderings NONCOMMUTE (mean ||CH-HC|| ~0.22 > 0): the dual-loop grammar is not a
     relabeling. Genuine combinatorial proof -- z3 AND cvc5 ENUMERATE all 2^4 length-4 words over
     {cool,heat}; the ALTERNATING constraint (adjacent beats differ) yields exactly 2 models (the
     two chiralities CHCH, HCHC), vs 16 unconstrained. Both solvers agree; the count flips 2<->16
     with the constraint (model-counting, not a pinned comparison).

Tools: numpy+scipy (GKSL/Kraus dynamics, entropy, control lane) + z3 + cvc5 (model-counting of the
chirality words, load-bearing). scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
    from scipy.linalg import expm
    import z3, cvc5
    from cvc5 import Kind
except ImportError as e:
    print(f"SKIP_OPTIONAL coupled_coratchet_dualloop_sim: missing tool ({e.name})"); sys.exit(0)

SX=np.array([[0,1],[1,0]],complex); SY=np.array([[0,-1j],[1j,0]],complex); SZ=np.array([[1,0],[0,-1]],complex)
def S_bits(r):
    w=np.linalg.eigvalsh((r+r.conj().T)/2); w=w[w>1e-12]; return float(-np.sum(w*np.log2(w)))
def bloch(n):
    n=np.array(n,float); nn=np.linalg.norm(n); n=n/nn if nn>1 else n
    return 0.5*(np.eye(2)+n[0]*SX+n[1]*SY+n[2]*SZ)
def cool(r,g=0.6):  # amplitude damping -> |0> (non-unital, S->0)
    K0=np.array([[1,0],[0,np.sqrt(1-g)]],complex); K1=np.array([[0,np.sqrt(g)],[0,0]],complex)
    return K0@r@K0.conj().T+K1@r@K1.conj().T
def heat(r,th=0.9,q=0.6):  # rotate into coherence + dephase (S up)
    U=expm(-1j*th*0.5*SX); r=U@r@U.conj().T
    P0=np.array([[1,0],[0,0]],complex); P1=np.array([[0,0],[0,1]],complex)
    return (1-q)*r+q*(P0@r@P0+P1@r@P1)
def loop(r0,order):
    r=r0.copy(); traj=[S_bits(r)]
    ops=[cool,heat,cool,heat] if order=='cool_first' else [heat,cool,heat,cool]
    for op in ops: r=op(r); traj.append(S_bits(r))
    return r,traj

# (A) opposite fixed points
rc=bloch([0.5,0.3,0.4])
for _ in range(30): rc=cool(rc)
rh=bloch([0.5,0.3,0.4])
for _ in range(30): rh=heat(rh)
Sc,Sh=S_bits(rc),S_bits(rh)
print(f"(A) cooling fixed pt S={Sc:.4f} (->0 pure pointer, Landauer); heating fixed pt S={Sh:.4f} (->1 max mixed)")

# (B) chirality asymmetry, sign-consistent
np.random.seed(0); probes=[bloch(np.random.randn(3)*0.5) for _ in range(200)]
fluxes=[]
for p in probes:
    _,tL=loop(p,'cool_first'); _,tR=loop(p,'heat_first')
    fluxes.append((tL[-1]-tL[0])-(tR[-1]-tR[0]))
signcons=all(f>0 for f in fluxes); meanflux=float(np.mean(fluxes))
print(f"(B) LEFT-minus-RIGHT net S-flux: mean {meanflux:+.4f}, sign-consistent across 200 probes: {signcons}")

# (C) noncommutation + model-counting of chirality words
def cnorm(r): return np.linalg.norm(cool(heat(r))-heat(cool(r)))
cn=float(np.mean([cnorm(p) for p in probes]))
def z3_count(alt):
    s=z3.Solver(); w=[z3.Int(f'w{i}') for i in range(4)]
    for x in w: s.add(z3.Or(x==0,x==1))
    if alt:
        for i in range(3): s.add(w[i]!=w[i+1])
    n=0
    while s.check()==z3.sat:
        m=s.model(); vals=[m[wi].as_long() for wi in w]; n+=1
        s.add(z3.Or([w[i]!=vals[i] for i in range(4)]))
    return n
def cvc5_count(alt):
    s=cvc5.Solver(); s.setOption("produce-models","true"); s.setLogic("QF_LIA")
    I=s.getIntegerSort(); w=[s.mkConst(I,f'w{i}') for i in range(4)]
    z,o=s.mkInteger(0),s.mkInteger(1)
    for x in w: s.assertFormula(s.mkTerm(Kind.OR,s.mkTerm(Kind.EQUAL,x,z),s.mkTerm(Kind.EQUAL,x,o)))
    if alt:
        for i in range(3): s.assertFormula(s.mkTerm(Kind.NOT,s.mkTerm(Kind.EQUAL,w[i],w[i+1])))
    n=0
    while s.checkSat().isSat():
        vals=[int(s.getValue(wi).getIntegerValue()) for wi in w]; n+=1
        s.assertFormula(s.mkTerm(Kind.OR,*[s.mkTerm(Kind.NOT,s.mkTerm(Kind.EQUAL,w[i],s.mkInteger(vals[i]))) for i in range(4)]))
    return n
za,zall=z3_count(True),z3_count(False); ca,call=cvc5_count(True),cvc5_count(False)
print(f"(C) noncommute mean ||CH-HC||={cn:.4f}; model count alternating: z3={za} cvc5={ca} (2 chiralities), all: z3={zall} cvc5={call}")

assert Sc<1e-6 and Sh>0.99, "cooling->pure (S=0), heating->max mixed (S=1): opposite fixed points"
assert signcons and meanflux>0.05, "chirality asymmetry sign-consistent across all probes"
assert cn>0.05, "the two loop orderings noncommute"
assert za==ca==2 and zall==call==16, "z3+cvc5 agree: alternating constraint -> 2 chiralities, else 16 (count flips)"
print("\nPASS coupled_coratchet_dualloop_sim")
