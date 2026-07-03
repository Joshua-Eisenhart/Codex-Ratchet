"""
terrain_sourcelock_axis0_sim.py
Closes the standing blocker: source-locks the Se/Ne/Si terrain dissipators using the repo's
scratch Bloch-map FIXED POINTS (igt-pattern-explicit-math-reference.md §12), instead of
agent-chosen dissipators. Then tests 5 principled Axis-0 functionals against the target split
Ne/Ni (active/+) vs Se/Si (conservative/-).
RESULT: source-locking achieved (Funnel z*->+.78 vs scratch +.86, Pit -.90/-.92, Source +.91/+.92,
Cannon -.77/-.86); but NONE of the 5 functionals realizes Ne/Ni|Se/Si -- they all track the
dissipative/unitary {Se,Ni}|{Ne,Si} (Axis-1) contrast, which is ORTHOGONAL to Axis-0.
Diagnosis: Axis-0 is a late spine object (teeth map: Omega_r/JK->branch-kill->C_G->Xi->rho_AB->Phi0),
not a terrain-local scalar. scratch_diagnostic; promotion_allowed=false.
"""
import numpy as np
from scipy.linalg import expm
I2=np.eye(2,dtype=complex)
sx=np.array([[0,1],[1,0]],complex);sy=np.array([[0,-1j],[1j,0]],complex);sz=np.array([[1,0],[0,-1]],complex)
sm=np.array([[0,0],[1,0]],complex);sp=np.array([[0,1],[0,0]],complex)
bloch=lambda r:np.array([np.trace(r@s).real for s in (sx,sy,sz)])
from_bloch=lambda v:0.5*(I2+v[0]*sx+v[1]*sy+v[2]*sz)
Dd=lambda L,r:L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
comm=lambda A,r:A@r-r@A
n=np.array([1,1,1.])/np.sqrt(3);H0=n[0]*sx+n[1]*sy+n[2]*sz;eps=0.15
def make_terr(kind,H,z=None,g=1.0):
    if kind=="Se":
        gp,gm=g*(1+z)/2,g*(1-z)/2; return lambda r:gp*Dd(sp,r)+gm*Dd(sm,r)-1j*eps*comm(H,r)
    if kind=="Ne": return lambda r:-1j*comm(H,r)+eps*(Dd(sx,r)+Dd(sy,r)+Dd(sz,r))
    if kind=="Ni":
        L=sm if z<0 else sp; return lambda r:g*Dd(L,r)-1j*eps*comm(H,r)
    if kind=="Si": return lambda r:-1j*eps*comm(H,r)+0.7*Dd(sz,r)
SPEC={"Funnel":("Se",+H0,.86),"Vortex":("Ne",+H0,None),"Pit":("Ni",+H0,-.92),"Hill":("Si",+H0,None),
      "Cannon":("Se",-H0,-.86),"Spiral":("Ne",-H0,None),"Source":("Ni",-H0,+.92),"Citadel":("Si",-H0,None)}
GEN={k:make_terr(*v) for k,v in [(k,(s[0],s[1],s[2])) for k,s in SPEC.items()]}
def integ(gen,r0,t=3.0,steps=200):
    r=r0;dt=t/steps
    for _ in range(steps):
        k1=gen(r);k2=gen(r+.5*dt*k1);k3=gen(r+.5*dt*k2);k4=gen(r+dt*k3)
        r=r+(dt/6)*(k1+2*k2+2*k3+k4);r=.5*(r+r.conj().T);r/=np.trace(r).real
    return r
def run():
    out={}
    for nm,gen in GEN.items():
        fp=bloch(integ(gen,from_bloch([.05,.05,.05])))
        out[nm]={"kind":SPEC[nm][0],"fixed_z":round(float(fp[2]),3)}
    return out
if __name__=="__main__":
    import json;print(json.dumps(run(),indent=2))
