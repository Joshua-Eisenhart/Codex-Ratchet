"""
nonunitality_theorem_sim.py  —  PURE MATH, NO JARGON.  2026-07-01.

Upgrades §7q's numerical containment split to an exact theorem: the operator-geometry fusion
bit is exactly non-unitality.

THEOREM: the 8/8 fusion split = 1[ ||L(I)|| != 0 ].
  - All 4 operator generators are UNITAL: Ti(I)=Te(I)=Fi(I)=Fe(I)=0 (dephasing ½(σρσ−ρ) and
    coherent −i[H,ρ] both annihilate I). => any span of them is unital.
  - Source-locked (amplitude-damping) terrains carry D[σ±]: ||L(I)|| = √2 != 0 exactly
    (t0,t2,t4,t6). Fused (depol/proj) terrains: ||L(I)|| = 0 exactly (t1,t3,t5,t7).
  - Therefore source-locked generators cannot lie in the operator algebra, in ANY frame:
    unitality is basis-independent (L(I)=0 <=> ULU†(I)=0). No co-moving frame can rescue
    containment -- this replaces the falsified frame test with a one-line identity.

scratch_diagnostic; promotion_allowed=false. Requires: numpy.
"""
import numpy as np
I2=np.eye(2,dtype=complex)
SX=np.array([[0,1],[1,0]],complex); SY=np.array([[0,-1j],[1j,0]],complex); SZ=np.array([[1,0],[0,-1]],complex)
sp=0.5*(SX+1j*SY); sm=0.5*(SX-1j*SY); H0=SZ.copy()
def D(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def cm(A,r): return A@r-r@A
g=0.35; kap=1.0
terr={0:(+1,+1,'damp'),1:(+1,0,'depol'),2:(+1,-1,'damp'),3:(+1,0,'proj'),
      4:(-1,-1,'damp'),5:(-1,0,'depol'),6:(-1,+1,'damp'),7:(-1,0,'proj')}
def terr_L(ti):
    eps,pole,kind=terr[ti]
    def X(r):
        out=-1j*g*cm(eps*H0,r)
        if kind=='damp': out=out+kap*D(sp if pole>0 else sm,r)
        elif kind=='depol': out=out+0.5*kap*(D(SX,r)+D(SY,r))
        elif kind=='proj': out=out+kap*D(SZ,r)
        return out
    return X
ops={'Ti':lambda r:0.6*D(SZ,r),'Te':lambda r:0.6*D(SX,r),'Fi':lambda r:-1j*cm(0.5*SX,r),'Fe':lambda r:-1j*cm(0.5*SZ,r)}
if __name__=="__main__":
    print("operators (must all be unital, ||L(I)||=0):")
    for nm,L in ops.items(): print(f"  {nm}: ||L(I)|| = {np.linalg.norm(L(I2)):.2e}")
    print("terrains (source-locked non-unital, fused unital):")
    for ti in range(8):
        v=np.linalg.norm(terr_L(ti)(I2))
        print(f"  t{ti} [{terr[ti][2]:5s}]: ||L(I)|| = {v:.4f}  {'NON-UNITAL' if v>1e-9 else 'unital'}")
    # basis-independence check: a random unitary leaves ||L(I)|| invariant for a damping terrain
    from numpy.linalg import qr
    U,_=qr(np.random.default_rng(0).normal(size=(2,2))+1j*np.random.default_rng(1).normal(size=(2,2)))
    L=terr_L(0); Lc=lambda r: U@L(U.conj().T@r@U)@U.conj().T
    print(f"basis-independence: ||L(I)||={np.linalg.norm(L(I2)):.4f} vs conjugated ||ULU†(I)||={np.linalg.norm(Lc(I2)):.4f}")
