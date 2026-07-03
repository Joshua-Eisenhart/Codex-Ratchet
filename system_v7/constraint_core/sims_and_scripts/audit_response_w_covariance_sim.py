"""
audit_response_w_covariance_sim.py  —  PURE MATH, NO JARGON.  2026-07-01.

The native-operator law earned as an exact symmetry (from the bundle audit).

CLAIM (theorem-shaped): the Hadamard involution W=(sx+sz)/sqrt2 (W=W^dag=W^-1) maps the
DIRECT operator pair to the CONJUGATED pair, exactly as channels:
    W . Ti . W = Te   (z-dephasing -> x-dephasing)
    W . Fi . W = Fe   (x-rotation  -> z-rotation)
Because W sx W = sz and W sz W = sx exactly. So the operator table's definition
"conjugated = x<->z image of direct" IS frame covariance under W.

THE FORK (settled): the spec's Axis-2 element V=exp(-iH0 u) does NOT implement this.
A rotation about the H0 axis (1,1,1)/sqrt3 can send sz->sx (the 120-deg cyclic permutation
x->y->z->x) but then sends sx->sy, mapping Fi to a Y-rotation, NOT Fe. Only the involution W
swaps z<->x for BOTH pairs simultaneously. => the native law is W-covariance; V needs correcting.

scratch_diagnostic; promotion_allowed=false. Requires: numpy, scipy.
"""
import numpy as np
from scipy.linalg import expm
I2=np.eye(2,dtype=complex)
SX=np.array([[0,1],[1,0]],complex); SY=np.array([[0,-1j],[1j,0]],complex); SZ=np.array([[1,0],[0,-1]],complex)

def sup(fn):
    M=np.zeros((4,4),complex)
    for i,E in enumerate([I2,SX,SY,SZ]):
        out=fn(E)
        for j,F in enumerate([I2,SX,SY,SZ]): M[j,i]=0.5*np.trace(F.conj().T@out)
    return M
def D(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def comm(A,r): return A@r-r@A
Ti=sup(lambda r:D(SZ,r)); Te=sup(lambda r:D(SX,r))
Fi=sup(lambda r:-1j*comm(0.5*SX,r)); Fe=sup(lambda r:-1j*comm(0.5*SZ,r))
def conj_channel(S,U):
    Ws=sup(lambda r:U@r@U.conj().T); return Ws@S@np.linalg.inv(Ws)

if __name__=="__main__":
    W=(SX+SZ)/np.sqrt(2)
    print("Hadamard W=(sx+sz)/sqrt2 conjugation on the operator algebra:")
    print(f"  ||W.Ti.W - Te|| = {np.linalg.norm(conj_channel(Ti,W)-Te):.2e}")
    print(f"  ||W.Fi.W - Fe|| = {np.linalg.norm(conj_channel(Fi,W)-Fe):.2e}")
    print(f"  (W sz W = sx: {np.allclose(W@SZ@W,SX)} ; W sx W = sz: {np.allclose(W@SX@W,SZ)})")
    AXIS=np.array([1,1,1.])/np.sqrt(3); H0=AXIS[0]*SX+AXIS[1]*SY+AXIS[2]*SZ
    print("\nDoes the spec's V=exp(-iH0 u) implement the same swap? Scan u:")
    best=None
    for u in np.linspace(0,2*np.pi,4000):
        Vv=expm(-1j*H0*u)
        if np.linalg.norm(Vv@SZ@Vv.conj().T-SX)<1e-3:
            fe_err=np.linalg.norm(conj_channel(Fi,Vv)-Fe); best=(u,fe_err)
            print(f"  u={u:.4f}: V sz V^-1 = sx OK, but ||V.Fi.V^-1 - Fe|| = {fe_err:.3f} (Fi->Y-rot, NOT Fe)")
            break
    print("\n=> native-operator law = exact W-covariance; V=exp(-iH0 u) cannot implement it.")
