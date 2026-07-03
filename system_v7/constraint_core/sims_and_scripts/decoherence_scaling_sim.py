"""
decoherence_scaling_sim.py -- HOW FAST einselection wins as the system grows: the decoherence
rate of a macroscopic superposition scales with system size, so the quantum->classical
boundary is a SCALING LAW, not a threshold. Extends bridge 2 (einselection) from WHICH states
survive to HOW FAST. NOT a ToE validation. numpy+scipy only.

  * independent baths (each qubit dephases at gamma): GHZ end-to-end coherence decays at rate
    ~ 2*n*gamma -- LINEAR in n.
  * collective bath (D[Jz], correlated coupling): rate ~ 2*n^2*gamma -- QUADRATIC
    (superdecoherence). The |0..0> vs |1..1> Jz-difference is 2n, and the rate goes as its
    square.
  Either way: bigger system => faster decoherence => macroscopic superpositions never seen.

scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
    from scipy.linalg import expm
except ImportError as e:
    print(f"SKIP_OPTIONAL decoherence_scaling_sim: missing tool ({e.name})"); sys.exit(0)

sz=np.array([[1,0],[0,-1]],complex)
def coherence(rho): return float(np.sum(np.abs(rho-np.diag(np.diag(rho)))))
def Zk(n,k):
    ops=[np.eye(2)]*n; ops[k]=sz; Z=ops[0]
    for o in ops[1:]: Z=np.kron(Z,o)
    return Z
def L_independent(n,g):
    dim=2**n; I=np.eye(dim); L=np.zeros((dim*dim,dim*dim),complex)
    for k in range(n):
        Z=Zk(n,k); L += g*(np.kron(Z,Z.conj())-np.kron(I,I))
    return L
def L_collective(n,g):
    dim=2**n; J=sum(Zk(n,k) for k in range(n)); I=np.eye(dim)
    return g*(np.kron(J,J.conj().T)-0.5*np.kron(J@J,I)-0.5*np.kron(I,(J@J).T))
def rate(n,Lfun,g,dt=0.02):
    dim=2**n; psi=np.zeros(dim,complex); psi[0]=psi[-1]=1/np.sqrt(2)
    rho0=np.outer(psi,psi.conj()); rhoT=(expm(Lfun(n,g)*dt)@rho0.reshape(-1)).reshape(dim,dim)
    return -np.log(coherence(rhoT)/coherence(rho0))/dt

g=1.0
ind=[rate(n,L_independent,g) for n in range(1,6)]
col=[rate(n,L_collective,g) for n in range(1,6)]
print("decoherence rate of an n-qubit GHZ superposition:")
print(f"  {'n':3s} {'independent':>12s} {'rate/n':>8s} {'collective':>12s} {'rate/n^2':>9s}")
for i,n in enumerate(range(1,6)):
    print(f"  {n:<3d} {ind[i]:>12.3f} {ind[i]/n:>8.3f} {col[i]:>12.3f} {col[i]/n**2:>9.3f}")

assert all(abs(ind[i]/(i+1)-2.0)<1e-6 for i in range(5)), "independent baths must scale LINEARLY (rate=2n)"
assert all(abs(col[i]/(i+1)**2-2.0)<1e-6 for i in range(5)), "collective bath must scale QUADRATICALLY (rate=2n^2)"
print("\n => independent: rate=2n (linear); collective: rate=2n^2 (superdecoherence). Bigger=faster.")
print("PASS decoherence_scaling_sim")
