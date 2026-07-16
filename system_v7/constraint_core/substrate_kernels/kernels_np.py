"""Load-bearing QIT kernels -- NumPy reference implementation. Pure math, no jargon.
These are the exact primitives the engine/foundations sims compute. The cross-substrate agreement harness
runs these against JAX(x64), Julia, and Torch re-implementations and certifies agreement to ~1e-9."""
import numpy as np
sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex); I2=np.eye(2,dtype=complex)
sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
G=0.35; KAP=1.0
# canonical 8 terrains (project TERR table): (eps, kind, pole)
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
def Dop(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def terrain_gen(ti):
    eps,kind,pole=TERR[ti]; H=eps*(sx+sy+sz)/np.sqrt(3)
    def X(r):
        out=-1j*G*(H@r-r@H)
        if kind=='damp': out=out+KAP*Dop(sp if pole>0 else sm,r)
        elif kind=='depol': out=out+0.5*KAP*(Dop(sx,r)+Dop(sy,r))
        else: out=out+KAP*Dop(sz,r)
        return out
    return X
def flow(X,r,t=1.0,steps=400):
    dt=t/steps
    for _ in range(steps): r=r+dt*X(r)
    return r
def vn_entropy(r):
    w=np.linalg.eigvalsh(r); w=w[w>1e-12]; return float(-np.sum(w*np.log(w)))
def liouville_spectrum(ti):
    X=terrain_gen(ti); B=[I2/np.sqrt(2),sx/np.sqrt(2),sy/np.sqrt(2),sz/np.sqrt(2)]
    M=np.zeros((4,4),complex)
    for j,b in enumerate(B):
        img=X(b)
        for i,c in enumerate(B): M[i,j]=np.trace(c.conj().T@img)
    return np.sort(np.abs(np.linalg.eigvals(M)))[::-1]
def coherent_information(rho_AB):
    # I_c(A>B) = S(rho_B) - S(rho_AB); rho_AB is 4x4 (2 qubits)
    rho_AB=rho_AB/np.trace(rho_AB)
    rB=np.zeros((2,2),complex)
    R=rho_AB.reshape(2,2,2,2)
    for i in range(2):
        for j in range(2): rB[i,j]=R[0,i,0,j]+R[1,i,1,j]
    return vn_entropy(rB)-vn_entropy(rho_AB)
def fixed_point(ti):
    return flow(terrain_gen(ti),0.5*I2,t=12.0,steps=3600)
