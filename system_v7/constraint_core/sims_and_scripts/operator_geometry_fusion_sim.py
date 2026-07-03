"""
operator_geometry_fusion_sim.py  —  PURE MATH, NO JARGON.

Tests operator-geometry FUSION: is each terrain generator CONTAINED in its operator algebra?
"The surface IS the operator" (GR-ether: spacetime IS the field, not a background it acts on).
Terrain indices t0..t7; operator indices Ti/Te/Fi/Fe are structural channel names (rosetta maps them
to Se/Ne/Ni/Si native pairings). No personality labels in the math.

OPERATORS (table igt-pattern 470-478):
  Ti: z-dephasing 0.5(sz r sz - r)     Te: x-dephasing 0.5(sx r sx - r)
  Fi: x-rotation  -i[0.5 sx, r]        Fe: z-rotation  -i[0.5 sz, r]

RESULT (containment residual = fraction of the terrain Liouvillian OUTSIDE the 4-operator algebra):
  projective terrains (t3,t7): 0.000  -> surface IS its operator algebra (exact fusion)
  depolarizing (t1,t5):        0.115  -> nearly fused
  source-locked (t0,t2,t4,t6): 0.67-0.71 -> irreducible geometric surplus (sigma_pm pole-seeking)
Co-moving-frame retest does NOT reduce the source-locked residual -> surplus is frame-independent.
CONCLUSION: two-tier fusion. Half the terrains literally ARE their operators; half carry geometry
the operators cannot express. The '2 native operators per terrain' law is an Axis-6 LABELLING, not a
reduction. scratch_diagnostic; promotion_allowed=false.
"""
import numpy as np
from scipy.linalg import expm

I2=np.eye(2,dtype=complex)
SX=np.array([[0,1],[1,0]],complex); SY=np.array([[0,-1j],[1j,0]],complex); SZ=np.array([[1,0],[0,-1]],complex)
SM=np.array([[0,0],[1,0]],complex); SP=np.array([[0,1],[0,0]],complex)
AXIS=np.array([1,1,1.])/np.sqrt(3); H0=AXIS[0]*SX+AXIS[1]*SY+AXIS[2]*SZ
EPS=0.15
def D(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def comm(A,r): return A@r-r@A
OPGEN={"Ti":lambda r:0.5*(SZ@r@SZ-r),"Te":lambda r:0.5*(SX@r@SX-r),
       "Fi":lambda r:-1j*comm(0.5*SX,r),"Fe":lambda r:-1j*comm(0.5*SZ,r)}
TERR=[dict(i=0,s=+1,zt=+0.86,fam="ADamp"),dict(i=1,s=+1,zt=None,fam="Depol"),
      dict(i=2,s=+1,zt=-0.92,fam="Sink"), dict(i=3,s=+1,zt=None,fam="Proj"),
      dict(i=4,s=-1,zt=-0.86,fam="ADamp"),dict(i=5,s=-1,zt=None,fam="Depol"),
      dict(i=6,s=-1,zt=+0.92,fam="Source"),dict(i=7,s=-1,zt=None,fam="Proj")]
def terr_gen(T):
    H=T["s"]*H0; fam=T["fam"]
    if fam=="ADamp":
        zt=T["zt"]; gp=(1+zt)/2; gm=(1-zt)/2
        return lambda r: gp*D(SP,r)+gm*D(SM,r)-1j*EPS*comm(H,r)
    if fam=="Depol": return lambda r:-1j*comm(H,r)+EPS*(D(SX,r)+D(SY,r)+D(SZ,r))
    if fam=="Sink":  return lambda r:D(SM,r)-1j*EPS*comm(H,r)
    if fam=="Source":return lambda r:D(SP,r)-1j*EPS*comm(H,r)
    if fam=="Proj":  return lambda r:-1j*EPS*comm(H,r)+0.7*D(SZ,r)
def superop(g):
    B=[I2/np.sqrt(2),SX/np.sqrt(2),SY/np.sqrt(2),SZ/np.sqrt(2)]
    return np.array([[np.trace(Bk.conj().T@g(Bj)) for Bj in B] for Bk in B])
def containment_residual(T):
    allo=[superop(OPGEN[o]) for o in ["Ti","Te","Fi","Fe"]]
    fb=allo+[a@b-b@a for i,a in enumerate(allo) for b in allo[i+1:]]
    Bm=np.array([b.flatten() for b in fb]).T
    Lg=superop(terr_gen(T)).flatten()
    coef,_,_,_=np.linalg.lstsq(Bm,Lg,rcond=None)
    return float(np.linalg.norm(Lg-Bm@coef)/np.linalg.norm(Lg))

if __name__=="__main__":
    print("terrain  family   containment_residual (0 = surface IS operator)")
    for T in TERR:
        r=containment_residual(T)
        tier="FUSED" if r<0.4 else "source-locked surplus"
        print(f"  t{T['i']}    {T['fam']:8} {r:6.3f}   {tier}")
