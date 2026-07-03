"""
memory_sim.py -- does the engine STORE and RECALL information? Three mechanisms,
built from the earned stage channels. PURE MATH, structural indices only.

(1) MEMORY CELLS. Write a classical bit (+/- along z), apply a single stage's
    channel N times (hold), read z back. Projective terrains (t3,t7 -- the "Si"
    cells) RETAIN the bit; dissipative/depolarizing terrains ERASE it. This is
    the model's memory substrate: only the projective cells store.

(2) SPINOR PHASE MEMORY. A 2*pi (360deg) rotation sends |psi> -> -|psi>; 4*pi
    returns +|psi>. The loop-count parity is stored in the spinor SIGN and is
    invisible at the density (rho) level -- a topologically protected bit.

(3) MEMORY<->COMPUTATION TRADEOFF. Push two messages through a compute schedule
    then a projective store, varying the per-stage flow time tau. At full
    strength the compute path thermalizes the message before the store (bit
    margin ~0); as tau shrinks the state carries the bit through and the store
    recovers it (margin grows monotonically). An engine that computes hard
    forgets; one that remembers must compute gently.
scratch_diagnostic; promotion_allowed=false.
"""
import numpy as np
from scipy.linalg import expm

I2=np.eye(2,dtype=complex)
sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex)
sz=np.array([[1,0],[0,-1]],complex); sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
G,KAP,Q,TH=0.35,1.0,1.0-np.exp(-1.0),np.pi/4
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
def sL(A): return np.kron(I2,A)
def sR(A): return np.kron(A.T,I2)
def sD(L): Ld=L.conj().T; return sL(L)@sR(Ld)-0.5*(sL(Ld@L)+sR(Ld@L))
def sC(H): return -1j*(sL(H)-sR(H))
def terrain_flow(ti,t=1.0):
    eps,kind,pole=TERR[ti]; L=G*sC(eps*(sx+sy+sz)/np.sqrt(3))
    if kind=='damp': L=L+KAP*sD(sp if pole>0 else sm)
    elif kind=='depol': L=L+0.5*KAP*(sD(sx)+sD(sy))
    else: L=L+KAP*sD(sz)
    return expm(t*L)
def op_super(name):
    P0=.5*(I2+sz);P1=.5*(I2-sz);Qp=.5*(I2+sx);Qm=.5*(I2-sx);E=np.eye(4,dtype=complex)
    if name=='Ti': return (1-Q)*E+Q*(sL(P0)@sR(P0)+sL(P1)@sR(P1))
    if name=='Te': return (1-Q)*E+Q*(sL(Qp)@sR(Qp)+sL(Qm)@sR(Qm))
    U=expm(-1j*TH/2*(sx if name=='Fi' else sz)); return sL(U)@sR(U.conj().T)
def stage(t,o,tau=1.0): return op_super(o)@terrain_flow(t,tau)
def vec(r): return r.T.reshape(-1)
def unvec(v): return v.reshape(2,2).T
def bit_margin_after_hold(t,o,hold):
    S=stage(t,o); outs={}
    for b in (+1,-1):
        r=0.5*(I2+0.9*b*sz)
        for _ in range(hold): r=unvec(S@vec(r)); r=0.5*(r+r.conj().T); r/=np.trace(r).real
        outs[b]=float(np.trace(r@sz).real)
    return outs[+1]-outs[-1]

# (1) memory cells
print("(1) MEMORY CELLS -- z-bit margin after 8 holds:")
cells={}
for t,o,lab in [(3,'Fe','Hill/proj'),(7,'Fe','Citadel/proj'),(0,'Ti','Funnel/damp'),
                (1,'Fi','Vortex/depol'),(5,'Fi','Spiral/depol')]:
    m=bit_margin_after_hold(t,o,8); cells[(t,o)]=m
    print(f"    t{t}:{o} {lab:14s} margin={m:.4f}  {'STORES' if m>0.1 else 'erases'}")
proj_cells=[cells[(3,'Fe')],cells[(7,'Fe')]]
diss_cells=[cells[(0,'Ti')],cells[(1,'Fi')],cells[(5,'Fi')]]

# (2) spinor phase memory
print("\n(2) SPINOR PHASE MEMORY -- loop parity in the spinor sign:")
psi0=np.array([1,0],complex); U=expm(-1j*(np.pi/2)*sy)
signs=[]
for turns,lab in [(2,"360"),(4,"720"),(6,"1080"),(8,"1440")]:
    psi=psi0.copy()
    for _ in range(turns): psi=U@psi
    ov=float(np.real(np.vdot(psi0,psi))); signs.append(ov)
    same=np.allclose(np.outer(psi,psi.conj()),np.outer(psi0,psi0.conj()))
    print(f"    {lab:5s}deg: spinor overlap {ov:+.4f}, density identical: {same}")

# (3) tradeoff
print("\n(3) MEMORY<->COMPUTATION TRADEOFF -- bit margin vs per-stage flow time tau:")
schedule=[(1,'Fi'),(0,'Ti'),(5,'Fi'),(4,'Ti')]+[(3,'Fe')]*3
mA=0.5*(I2+0.8*sz+0.3*sx); mB=0.5*(I2-0.8*sz+0.3*sx)
def run(sch,r0,tau):
    r=r0.copy()
    for t,o in sch: r=unvec(stage(t,o,tau)@vec(r)); r=0.5*(r+r.conj().T); r/=np.trace(r).real
    return float(np.trace(r@sz).real)
margins=[]
for tau in [1.0,0.25,0.1,0.05,0.02]:
    m=run(schedule,mA,tau)-run(schedule,mB,tau); margins.append((tau,m))
    print(f"    tau={tau:.2f}  bit margin={m:.4f}")

# assertions
assert min(proj_cells)>0.1, "projective cells must store the z-bit"
assert max(diss_cells)<0.05, "dissipative/depolarizing cells must erase"
assert abs(signs[0]+1)<1e-9 and abs(signs[1]-1)<1e-9, "spinor 360->-1, 720->+1"
assert margins[-1][1]>margins[0][1]+0.2, "shorter tau must recover more of the stored bit"
print("\nPASS memory_sim")
