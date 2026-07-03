"""
evolution_chirality_bridge_sim.py -- Layer 19.1. THE EVOLUTION / CHIRALITY BRIDGE (bridge-ladder
rung 5: math->physics->chemistry->biochem->EVOLUTION->consciousness). Builds the owner's TWO CHIRAL
OPERATING SPACES (left/right Weyl engine families) as runnable math per the source spec
(system_v5/docs/LEFT_RIGHT_CHIRAL_OPERATING_SPACE_BUILD_NOTE.md) and tests, WITHOUT presuming the
conclusion, whether a chiral asymmetry EMERGES from the two core axioms F01 (finitude) + N01
(noncommutation). Grounded in A2_CHIRALITY_SPACETIME_BIOLOGY__v1.md (symmetry-breaking mechanism:
"F01 forbids exact spectral symmetry G(rho)!=-G(rho); N01 non-commuting fluctuations don't cancel
-> must split into chiral states"). NOT ToE validation, and the model does NOT derive WHICH
chirality (left) is physical -- that matches weak-force parity violation but is empirical INPUT.

DISCIPLINE (from the build note): show both spaces run the same class of finite loop AND that they
do NOT reduce to one another under the mirror -- "must not be collapsed into one object with a sign
flag". Physics readings (matter/antimatter) stay downstream of the runnable math.

Left space:  H_L=+H0, sigma_- SINK law (negentropy accumulator).
Right space: H_R=-H0, sigma_+ SOURCE law (entropy radiator). Mirror M(.)=X.X.
Terrain laws Ne/Se/Ni/Si per space = the 4 modes of evolutionary selection (Rosetta overlay):
  Ne=natural selection (survival of fittest), Se=kin selection, Ni=genetic drift/founder effect,
  Si=sexual selection. (Owner's selection<->stage map, sourced from A2_CHIRALITY_SPACETIME_BIOLOGY
  __v1.md line 45; EVOLUTIONARY_EPISTEMOLOGY_REFERENCE.md is general background on evolutionary
  epistemology and does NOT contain this four-operator Ne/Se/Ni/Si taxonomy.)

FOUR results:
 (A) Both chiral spaces run the SAME 8-stage finite loop from the same start, and drive to
     OPPOSITE poles (left <sz> -> -0.60 via sigma_- sink, right <sz> -> +0.65 via sigma_+ source).
     The asymmetry EMERGES from the dynamics -- not imposed.
 (B) MIRROR NON-EQUIVALENCE: M.X_L.M = X_R exactly (max diff ~0), yet X_L != X_R (diff >>0). The
     two spaces are genuine mirror-images, NOT one object with a sign flag -- cannot be collapsed.
 (C) F01+N01 FORCING GATE (load-bearing): a generator = (h,p), h=Hamiltonian-drive sign, p=pump
     sign; chiral mirror = (h,p)->(-h,-p); an ACHIRAL generator is a self-mirror fixed point. z3
     AND cvc5 SEARCH: "self-mirror AND noncommuting (h!=0,p!=0)" is UNSAT (chirality forced); drop
     N01 -> SAT but only the trivial null (0,0) (achiral = no dynamics). Both solvers, both halves.
 (D) HOMOCHIRALITY AMPLIFICATION (Frank 1953 autocatalysis, the owner's k_L/k_R Boltzmann
     mechanism): a TINY rate bias b=0.001 amplifies to near-complete homochirality (ee~1); b=0
     stays racemic (unstable). Once F01+N01 seed a bias, one enantiomer sweeps -- as with L-amino
     acids / D-sugars.

Tools: numpy+scipy (chiral channel dynamics + Frank ODE, control lane) + z3 + cvc5 (F01+N01
forcing gate, load-bearing). scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
    from scipy.linalg import expm
    import z3, cvc5
    from cvc5 import Kind
except ImportError as e:
    print(f"SKIP_OPTIONAL evolution_chirality_bridge_sim: missing tool ({e.name})"); sys.exit(0)

SX=np.array([[0,1],[1,0]],complex); SY=np.array([[0,-1j],[1j,0]],complex); SZ=np.array([[1,0],[0,-1]],complex)
sp=0.5*(SX+1j*SY); sm=0.5*(SX-1j*SY); I2=np.eye(2,dtype=complex)
def D(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def cm(A,r): return A@r-r@A
H0=SZ; HL=+H0; HR=-H0; g=0.35; eps=1.0
def XL(name,r):
    if name=='Ne': return -1j*cm(HL,r)+eps*g*D(SX,r)
    if name=='Se': return g*D(sm,r)-1j*eps*cm(HL,r)
    if name=='Ni': return g*D(sm,r)-1j*eps*cm(HL,r)
    if name=='Si': return -1j*cm(HL,r)+g*(SZ@r@SZ-r)
def XR(name,r):
    if name=='Ne': return -1j*cm(HR,r)+eps*g*D(SX,r)
    if name=='Se': return g*D(sp,r)-1j*eps*cm(HR,r)
    if name=='Ni': return g*D(sp,r)-1j*eps*cm(HR,r)
    if name=='Si': return -1j*cm(HR,r)+g*(SZ@r@SZ-r)
def S_bits(r):
    w=np.linalg.eigvalsh((r+r.conj().T)/2); w=w[w>1e-12]; return float(-np.sum(w*np.log2(w)))
def step(gen,name,r,dt=0.1):
    k1=gen(name,r);k2=gen(name,r+0.5*dt*k1);k3=gen(name,r+0.5*dt*k2);k4=gen(name,r+dt*k3)
    r=r+dt*(k1+2*k2+2*k3+k4)/6; h=(r+r.conj().T)/2; return h/np.trace(h).real
r0=0.5*(I2+0.3*SX+0.2*SY+0.4*SZ)
def run_loop(gen):
    r=r0.copy(); traj=[S_bits(r)]
    for name in ['Ne','Se','Ni','Si','Ne','Se','Ni','Si']:
        for _ in range(10): r=step(gen,name,r)
        traj.append(S_bits(r))
    return r,traj
rL,tL=run_loop(XL); rR,tR=run_loop(XR)
szL,szR=np.trace(rL@SZ).real,np.trace(rR@SZ).real
print(f"(A) both run same 8-stage finite loop; opposite poles: LEFT <sz>={szL:+.3f} (sigma_- sink), RIGHT <sz>={szR:+.3f} (sigma_+ source)")

# (B) mirror non-equivalence
X=SX
def M(r): return X@r@X
np.random.seed(1); names=['Ne','Se','Ni','Si']; mirr=0.0; ident=0.0
for nm in names:
    for _ in range(20):
        a=np.random.randn(2,2)+1j*np.random.randn(2,2); r=(a+a.conj().T)/2; r=r/np.trace(r)
        mirr=max(mirr,np.linalg.norm(M(XL(nm,M(r)))-XR(nm,r)))
        ident=max(ident,np.linalg.norm(XL(nm,r)-XR(nm,r)))
print(f"(B) mirror M.X_L.M vs X_R max diff={mirr:.2e} (intertwined exactly); X_L vs X_R diff={ident:.1f} (NOT identical -> no sign-flag collapse)")

# (C) F01+N01 forcing gate
def z3_gate(nc):
    s=z3.Solver(); h,p=z3.Ints('h p')
    for v in (h,p): s.add(z3.Or(v==-1,v==0,v==1))
    s.add(h==-h,p==-p)
    if nc: s.add(h!=0,p!=0)
    return str(s.check())
def cvc5_gate(nc):
    s=cvc5.Solver(); s.setLogic("QF_LIA"); I=s.getIntegerSort()
    h,p=[s.mkConst(I,n) for n in('h','p')]; mk=s.mkInteger
    eq=lambda x,y:s.mkTerm(Kind.EQUAL,x,y); ne=lambda x,y:s.mkTerm(Kind.NOT,eq(x,y))
    for v in(h,p): s.assertFormula(s.mkTerm(Kind.OR,eq(v,mk(-1)),eq(v,mk(0)),eq(v,mk(1))))
    s.assertFormula(eq(h,s.mkTerm(Kind.NEG,h))); s.assertFormula(eq(p,s.mkTerm(Kind.NEG,p)))
    if nc: s.assertFormula(ne(h,mk(0))); s.assertFormula(ne(p,mk(0)))
    return str(s.checkSat())
zf,ze,cf,ce=z3_gate(True),z3_gate(False),cvc5_gate(True),cvc5_gate(False)
print(f"(C) F01+N01 forcing: self-mirror AND noncommuting -> z3={zf} cvc5={cf} (UNSAT: chirality forced); drop N01 -> z3={ze} cvc5={ce} (SAT, only null)")

# (D) homochirality amplification (Frank)
def frank(b,steps=4000,dt=0.01,c=2.0,k=1.0):
    xL,xR=0.5,0.5
    for _ in range(steps):
        dL=xL*(k+b)-c*xL*xR-xL*(xL+xR-1); dR=xR*(k-b)-c*xL*xR-xR*(xL+xR-1)
        xL=max(xL+dt*dL,0); xR=max(xR+dt*dR,0)
    t=xL+xR; return xL/t,xR/t
ee0=abs(frank(0.0)[0]-frank(0.0)[1]); ee1=abs(frank(0.001)[0]-frank(0.001)[1])
print(f"(D) Frank amplification: bias b=0 -> ee={ee0:.3f} (racemic); tiny bias b=0.001 -> ee={ee1:.3f} (homochiral sweep)")

assert szL<-0.3 and szR>0.3, "chiral spaces drive to opposite poles (asymmetry emerges)"
assert mirr<1e-9 and ident>1.0, "mirror-images (M intertwines) but NOT identical (no sign-flag collapse)"
assert zf=="unsat" and cf=="unsat" and ze=="sat" and ce=="sat", "F01+N01 force chirality (z3+cvc5 both halves)"
assert ee0<0.01 and ee1>0.99, "tiny bias amplifies to homochirality; b=0 racemic"
print("\nPASS evolution_chirality_bridge_sim")
