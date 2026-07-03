"""
axis_loadbearing_n01_sim.py -- P12 guard (fifth audit, 2026-07-01). PURE MATH.

FINDING: the 16/16 N01 order-sensitivity of the stage layer is LOAD-BEARING on
the coherent-axis choice. If the terrain coherent axis equals the Fe rotation
axis (z), the four Fe stages commute EXACTLY with their terrains -- damping
D(s-+), dephasing D(sz) and comm(sz) are all phase-covariant -- and 16/16
collapses to 12/16. The canonical (1,1,1)/sqrt3 axis restores 16/16.
Consequence: the two axis conventions found in this bundle's sims (sz in
engine_type_access_sim; (1,1,1)/sqrt3 in sixteen_stage_engine_sim) are NOT
interchangeable for N01 claims. scratch_diagnostic; promotion_allowed=false.
"""
import numpy as np
from scipy.linalg import expm
I2=np.eye(2,dtype=complex)
sx=np.array([[0,1],[1,0]],complex);sy=np.array([[0,-1j],[1j,0]],complex);sz=np.array([[1,0],[0,-1]],complex)
sm=0.5*(sx-1j*sy)
D=lambda L,r:L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
Fe=lambda r,U=expm(-1j*np.pi/8*sz):U@r@U.conj().T
probe=0.5*(I2+0.55*sx+0.35*sy+0.25*sz)
def flow(X,r,t=1.0,steps=400):
    dt=t/steps
    for _ in range(steps):
        k1=X(r);k2=X(r+.5*dt*k1);k3=X(r+.5*dt*k2);k4=X(r+dt*k3)
        r=r+(dt/6)*(k1+2*k2+2*k3+k4);r=.5*(r+r.conj().T);r/=np.trace(r).real
    return r
b=lambda r:np.array([np.trace(r@s).real for s in (sx,sy,sz)])
for name,H in [("z-axis",sz),("canonical",(sx+sy+sz)/np.sqrt(3))]:
    X=lambda r:-1j*0.35*(H@r-r@H)+1.0*D(sm,r)
    gap=np.linalg.norm(b(Fe(flow(X,probe.copy())))-b(flow(X,Fe(probe.copy()))))
    tag="COMMUTES (N01 gap vanishes)" if gap<1e-10 else "order-sensitive"
    print(f"coherent axis {name:10s}: (damp,Fe) order gap = {gap:.2e}  {tag}")
print("=> 16/16 order sensitivity requires the coherent axis off the operator")
print("   rotation axes; the (1,1,1)/sqrt3 choice is load-bearing, not conventional.")
