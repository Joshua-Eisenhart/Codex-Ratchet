"""
axis2_two_layer_sim.py  —  PURE MATH, NO JARGON.  2026-07-01.

Resolves the §7t fork: is Axis-2 the continuous frame V=exp(-iH0 u) (connection K=iV†V̇, §7n)
or the Hadamard involution W=(sx+sz)/sqrt2 that earns the native-operator law (§7t)?

ANSWER: BOTH. Axis-2 is a two-layer object; neither element is wrong.
  - V (continuous): gauge-invariant, phase-sector, connection K=H0 (changes dynamics) -- but
    does NOT implement the direct<->conjugated operator map.
  - W (discrete Z2): gauge-invariant, phase-sector, implements the operator map EXACTLY -- but
    V̇=0 so K=0 (not a continuous frame).
  They compose: W acts on the continuous frame by conjugating its connection, K -> W K W.

scratch_diagnostic; promotion_allowed=false. Requires: numpy, scipy.
"""
import numpy as np
from scipy.linalg import expm
I2=np.eye(2,dtype=complex)
SX=np.array([[0,1],[1,0]],complex); SY=np.array([[0,-1j],[1j,0]],complex); SZ=np.array([[1,0],[0,-1]],complex)
AXIS=np.array([1,1,1.])/np.sqrt(3); H0=AXIS[0]*SX+AXIS[1]*SY+AXIS[2]*SZ
V=expm(-1j*H0*0.9); W=(SX+SZ)/np.sqrt(2)
def bloch(r): return np.array([np.trace(r@s).real for s in (SX,SY,SZ)])
def sup(fn):
    M=np.zeros((4,4),complex)
    for i,E in enumerate([I2,SX,SY,SZ]):
        o=fn(E)
        for j,F in enumerate([I2,SX,SY,SZ]): M[j,i]=0.5*np.trace(F.conj().T@o)
    return M
def D(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def cm(A,r): return A@r-r@A
Ti=sup(lambda r:D(SZ,r)); Te=sup(lambda r:D(SX,r)); Fi=sup(lambda r:-1j*cm(0.5*SX,r)); Fe=sup(lambda r:-1j*cm(0.5*SZ,r))
def conj_ch(S,U): Ws=sup(lambda r:U@r@U.conj().T); return Ws@S@np.linalg.inv(Ws)
if __name__=="__main__":
    rng=np.random.default_rng(0)
    def rr():
        A=rng.normal(size=(2,2))+1j*rng.normal(size=(2,2)); M=A@A.conj().T; return M/np.trace(M)
    for nm,U in [("V",V),("W",W)]:
        e_ti=np.linalg.norm(conj_ch(Ti,U)-Te); e_fi=np.linalg.norm(conj_ch(Fi,U)-Fe)
        print(f"[{nm}] operator-map error: Ti->Te={e_ti:.2e}  Fi->Fe={e_fi:.2e}  (max={max(e_ti,e_fi):.2e})")
    du=1e-6; Vp=(expm(-1j*H0*(0.9+du))-expm(-1j*H0*(0.9-du)))/(2*du)
    K_V=1j*expm(-1j*H0*0.9).conj().T@Vp
    print(f"  (V fails the map on BOTH pairs; W passes both -- the row's V ✗ / W ✓)")
    print(f"connection: V gives K=H0 (||K-H0||={np.linalg.norm(K_V-H0):.1e}); W gives K=0 (V̇=0)")
    print(f"composition: W K W = H0 - 2σy/√3 ; ||WH0W-H0||={np.linalg.norm(W@H0@W-H0):.3f} (WσyW=-σy)")
    print("=> Axis-2 = (V continuous frame) x (W discrete direct/conjugated bit), composing via K->WKW")
