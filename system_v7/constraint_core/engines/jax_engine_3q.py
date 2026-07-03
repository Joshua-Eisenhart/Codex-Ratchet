"""
jax_engine_3q.py -- 3-qubit engine as a pure-functional JAX kernel. Exact 64x64
superoperator matrix exponential for the terrain flow (no RK4 truncation) ->
agreement with the numpy RK4 oracle_targets_3q within 1e-6 is a genuine
two-METHOD cross-check on C^8. Reads targets_3q.json constants; writes
jax_results_3q.json in the same schema. scratch_diagnostic; promotion_allowed=false.
"""
import json, os, itertools
import numpy as _np
import jax; jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
from jax.scipy.linalg import expm

HERE=os.path.dirname(os.path.abspath(__file__))
C=json.load(open(os.path.join(HERE,"targets_3q.json")))["model_constants"]
G,KAP,Q,TH,T_FLOW,J_COUP=C["G"],C["KAP"],C["Q"],C["TH"],C["T_FLOW"],C["J_COUP"]
PROBE_B=C["PROBE_B"]

I2=jnp.eye(2,dtype=jnp.complex128)
sx=jnp.array([[0,1],[1,0]],jnp.complex128); sy=jnp.array([[0,-1j],[1j,0]],jnp.complex128)
sz=jnp.array([[1,0],[0,-1]],jnp.complex128); sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
PAULI={'I':I2,'X':sx,'Y':sy,'Z':sz}
I8=jnp.eye(8,dtype=jnp.complex128)
def kron3(a,b,c): return jnp.kron(jnp.kron(a,b),c)
def on0(A): return kron3(A,I2,I2)
ZZ01=kron3(sz,sz,I2); ZZ12=kron3(I2,sz,sz)

# superoperators on vec(rho) (column-stacking: vec(rho)=rho.T.reshape(-1))
def sL(A): return jnp.kron(I8,A)
def sR(A): return jnp.kron(A.T,I8)
def superD(L): Ld=L.conj().T; return sL(L)@sR(Ld)-0.5*(sL(Ld@L)+sR(Ld@L))
def superH(H): return -1j*(sL(H)-sR(H))

TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
NATIVE={0:('Ti','Fi'),1:('Ti','Fi'),4:('Ti','Fi'),5:('Ti','Fi'),
        2:('Te','Fe'),3:('Te','Fe'),6:('Te','Fe'),7:('Te','Fe')}

def gen_super(ti):
    eps,kind,pole=TERR[ti]
    H=on0(eps*(sx+sy+sz)/jnp.sqrt(3.0))+J_COUP*(ZZ01+ZZ12)
    Lgen=G*superH(H)
    if kind=='damp': Lgen=Lgen+KAP*superD(on0(sp if pole>0 else sm))
    elif kind=='depol': Lgen=Lgen+0.5*KAP*(superD(on0(sx))+superD(on0(sy)))
    else: Lgen=Lgen+KAP*superD(on0(sz))
    return Lgen

def op_map(name):
    P0=0.5*(I2+sz);P1=0.5*(I2-sz);Qp=0.5*(I2+sx);Qm=0.5*(I2-sx)
    if name=='Ti': return (1-Q)*jnp.kron(I8,I8)+Q*(sL(on0(P0))@sR(on0(P0))+sL(on0(P1))@sR(on0(P1)))
    if name=='Te': return (1-Q)*jnp.kron(I8,I8)+Q*(sL(on0(Qp))@sR(on0(Qp))+sL(on0(Qm))@sR(on0(Qm)))
    if name=='Fi': U=on0(expm(-1j*TH/2*sx)); return sL(U)@sR(U.conj().T)
    if name=='Fe': U=on0(expm(-1j*TH/2*sz)); return sL(U)@sR(U.conj().T)

def vec(r): return r.T.reshape(-1)
def unvec(v): return v.reshape(8,8).T
STRINGS=[''.join(p) for p in itertools.product('IXYZ',repeat=3) if set(p)!={'I'}]
PMATS=[kron3(PAULI[s[0]],PAULI[s[1]],PAULI[s[2]]) for s in STRINGS]
def pvec(r): return [float(jnp.trace(r@P).real) for P in PMATS]

def main():
    rho0=0.5*(I2+PROBE_B[0]*sx+PROBE_B[1]*sy+PROBE_B[2]*sz)
    plus=0.5*(I2+sx); probe=kron3(rho0,plus,plus)
    stages=[]
    for t in range(8):
        F=expm(T_FLOW*gen_super(t))          # exact terrain channel (64x64)
        for o in NATIVE[t]:
            M=op_map(o)
            down=unvec(M@F@vec(probe)); up=unvec(F@M@vec(probe))
            down=0.5*(down+down.conj().T); up=0.5*(up+up.conj().T)
            dv,uv=pvec(down),pvec(up)
            stages.append({"t":t,"op":o,"pvec_down":dv,"pvec_up":uv,
                           "order_gap":float(_np.linalg.norm(_np.array(dv)-_np.array(uv)))})
    json.dump({"stages":stages},open(os.path.join(HERE,"jax_results_3q.json"),"w"),indent=1)
    print(f"jax_results_3q.json written ({len(stages)} stages); backend={jax.default_backend()}, x64 on")

if __name__=="__main__": main()
