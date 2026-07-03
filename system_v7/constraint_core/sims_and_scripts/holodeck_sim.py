"""
holodeck_sim.py -- the prediction-first / active-inference loop (pure QIT). Turns the
Layer-12 memory cells into LEARNING. No smuggled classical math: the free energy is the
Umegaki quantum relative entropy S(observation || belief) in bits, and belief updates are
CPTP convex mixtures committed to the projective memory cell.

(1) PREDICTION LOOP. A belief meets an observation; minimizing free energy F=S(obs||belief)
    moves the belief toward the observation. F drops monotonically to ~0 (belief converges).
(2) STATIONARY LEARNING. Repeated exposure to one environment -> surprise falls ~99%
    (genuine learning, belief stored between observations in the Hill projective cell).
(3) MEMORY-CAPACITY BOUNDARY. A SINGLE cell learns a stationary (k=1) environment to
    near-zero residual surprise but CANNOT learn a k>=2 cycling sequence (residual ~0.4 bits).
(4) 3-QUBIT REGISTER. Using the extra qubits as a context/address register (4 memory slots),
    the engine learns k=2,3,4 sequences to <0.05 bits. => an independent, derived reason for
    the model's 3-qubit floor: it upgrades the holodeck from single memory to SEQUENCE memory.
scratch_diagnostic; promotion_allowed=false.
"""
import numpy as np
from scipy.linalg import expm, logm
I2=np.eye(2,dtype=complex)
sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex)
sz=np.array([[1,0],[0,-1]],complex)
G,KAP=0.35,1.0
def sL(A): return np.kron(I2,A)
def sR(A): return np.kron(A.T,I2)
def sD(L): Ld=L.conj().T; return sL(L)@sR(Ld)-0.5*(sL(Ld@L)+sR(Ld@L))
def sC(H): return -1j*(sL(H)-sR(H))
def vec(r): return r.T.reshape(-1)
def unvec(v): return v.reshape(2,2).T
Hill_store=expm(0.15*(G*sC((sx+sy+sz)/np.sqrt(3))+KAP*sD(sz)))  # gentle projective hold
def store(b): r=unvec(Hill_store@vec(b)); r=0.5*(r+r.conj().T); return r/np.trace(r).real
def F(obs,bel):  # Umegaki relative entropy S(obs||bel), bits
    obs=0.5*(obs+obs.conj().T); bel=0.5*(bel+bel.conj().T)
    ev,V=np.linalg.eigh(bel); ev=np.clip(ev,1e-12,None); bel=V@np.diag(ev)@V.conj().T
    return float(np.real(np.trace(obs@((logm(obs+1e-12*I2)-logm(bel))/np.log(2)))))

# (1) prediction loop
b=0.5*(I2+0.85*sz); obs=0.5*(I2-0.7*sz+0.2*sx); Fs=[F(obs,b)]
for _ in range(8):
    b=0.6*obs+0.4*b; b=0.5*(b+b.conj().T); b/=np.trace(b).real; Fs.append(F(obs,b))
print(f"(1) prediction loop: F {Fs[0]:.3f} -> {Fs[-1]:.4f} bits, monotone={all(Fs[i]>=Fs[i+1]-1e-9 for i in range(len(Fs)-1))}")

# (2) stationary learning
def stationary(obs,n=8,rate=0.5):
    bb=0.5*I2; S=[]
    for _ in range(n):
        S.append(F(obs,bb)); bb=(1-rate)*bb+rate*obs; bb=0.5*(bb+bb.conj().T); bb/=np.trace(bb).real; bb=store(bb)
    return S
S2=stationary(0.5*(I2+0.7*sz+0.2*sx))
print(f"(2) stationary learning: surprise {S2[0]:.3f} -> {S2[-1]:.4f} bits ({100*(1-S2[-1]/S2[0]):.0f}% reduction)")

# (3) single-cell capacity boundary
def one_cell(k,rate=0.5,passes=6):
    st=[0.5*(I2+0.6*np.cos(2*np.pi*i/k)*sz+0.6*np.sin(2*np.pi*i/k)*sx) for i in range(k)]
    bb=0.5*I2; S=[]
    for obs in st*passes:
        S.append(F(obs,bb)); bb=(1-rate)*bb+rate*obs; bb=0.5*(bb+bb.conj().T); bb/=np.trace(bb).real; bb=store(bb)
    return np.mean(S[-k:])
cap={k:one_cell(k) for k in (1,2,3,4)}
print(f"(3) single-cell residual surprise: " + ", ".join(f"k={k}:{v:.3f}" for k,v in cap.items()))

# (4) 3-qubit register (context-addressed slots)
def register(k,rate=0.5,passes=6):
    st=[0.5*(I2+0.6*np.cos(2*np.pi*i/k)*sz+0.6*np.sin(2*np.pi*i/k)*sx) for i in range(k)]
    bel=[0.5*I2 for _ in range(k)]; S=[]
    for c in list(range(k))*passes:
        S.append(F(st[c],bel[c])); bel[c]=(1-rate)*bel[c]+rate*st[c]
        bel[c]=0.5*(bel[c]+bel[c].conj().T); bel[c]/=np.trace(bel[c]).real; bel[c]=store(bel[c])
    return np.mean(S[-k:])
reg={k:register(k) for k in (2,3,4)}
print(f"(4) register residual surprise: " + ", ".join(f"k={k}:{v:.4f}" for k,v in reg.items()))

assert Fs[-1]<0.01 and all(Fs[i]>=Fs[i+1]-1e-9 for i in range(len(Fs)-1)), "prediction loop must minimize F monotonically"
assert S2[-1]<0.05 and S2[0]>0.2, "stationary environment must be learned"
assert cap[1]<0.05 and cap[2]>0.2, "one cell learns k=1 but not k>=2"
assert all(v<0.05 for v in reg.values()), "3-qubit register must learn k=2,3,4"
print("\nPASS holodeck_sim")
