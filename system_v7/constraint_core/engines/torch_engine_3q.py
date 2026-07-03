"""
torch_engine_3q.py -- 3-qubit engine on PyTorch (complex128). Independent route:
torch.linalg.matrix_exp on the 64x64 superoperator per stage. Reads
targets_3q.json constants; writes torch_results_3q.json in the 3q schema
(63-dim Pauli-expectation readout). scratch_diagnostic; promotion_allowed=false.
"""
import json, os, itertools
import numpy as np
import torch

HERE=os.path.dirname(os.path.abspath(__file__))
C=json.load(open(os.path.join(HERE,"targets_3q.json")))["model_constants"]
G,KAP,Q,TH,T_FLOW,J_COUP=C["G"],C["KAP"],C["Q"],C["TH"],C["T_FLOW"],C["J_COUP"]
PROBE_B=C["PROBE_B"]

dev="cuda" if torch.cuda.is_available() else "cpu"
dt=torch.complex128
I2=torch.eye(2,dtype=dt,device=dev)
sx=torch.tensor([[0,1],[1,0]],dtype=dt,device=dev)
sy=torch.tensor([[0,-1j],[1j,0]],dtype=dt,device=dev)
sz=torch.tensor([[1,0],[0,-1]],dtype=dt,device=dev)
sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
PAULI={'I':I2,'X':sx,'Y':sy,'Z':sz}
def kron(A,B): return torch.kron(A.contiguous(),B.contiguous())
def kron3(a,b,c): return kron(kron(a,b),c)
def on0(A): return kron3(A,I2,I2)
I8=torch.eye(8,dtype=dt,device=dev)
ZZ01=kron3(sz,sz,I2); ZZ12=kron3(I2,sz,sz)
def sL(A): return kron(I8,A)
def sR(A): return kron(A.T,I8)
def sD(L): Ld=L.conj().T; return sL(L)@sR(Ld)-0.5*(sL(Ld@L)+sR(Ld@L))
def sC(H): return -1j*(sL(H)-sR(H))

TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
NATIVE={0:('Ti','Fi'),1:('Ti','Fi'),4:('Ti','Fi'),5:('Ti','Fi'),
        2:('Te','Fe'),3:('Te','Fe'),6:('Te','Fe'),7:('Te','Fe')}

def terrain_super(ti):
    eps,kind,pole=TERR[ti]
    H=on0(eps*(sx+sy+sz)/np.sqrt(3.0))+J_COUP*(ZZ01+ZZ12)
    Ls=G*sC(H)
    if kind=='damp': Ls=Ls+KAP*sD(on0(sp if pole>0 else sm))
    elif kind=='depol': Ls=Ls+0.5*KAP*(sD(on0(sx))+sD(on0(sy)))
    else: Ls=Ls+KAP*sD(on0(sz))
    return Ls

def op_super(name):
    P0=0.5*(I2+sz);P1=0.5*(I2-sz);Qp=0.5*(I2+sx);Qm=0.5*(I2-sx)
    E64=torch.eye(64,dtype=dt,device=dev)
    if name=='Ti': return (1-Q)*E64+Q*(sL(on0(P0))@sR(on0(P0))+sL(on0(P1))@sR(on0(P1)))
    if name=='Te': return (1-Q)*E64+Q*(sL(on0(Qp))@sR(on0(Qp))+sL(on0(Qm))@sR(on0(Qm)))
    U=on0(torch.linalg.matrix_exp(-1j*TH/2*(sx if name=='Fi' else sz)))
    return sL(U)@sR(U.conj().T)

def vec(r): return r.T.reshape(64)
def unvec(v): return v.reshape(8,8).T
STRINGS=[''.join(p) for p in itertools.product('IXYZ',repeat=3) if set(p)!={'I'}]
PMATS=[kron3(PAULI[s[0]],PAULI[s[1]],PAULI[s[2]]) for s in STRINGS]
def pvec(r): return [float(torch.trace(r@P).real) for P in PMATS]

def main():
    rho0=0.5*(I2+PROBE_B[0]*sx+PROBE_B[1]*sy+PROBE_B[2]*sz)
    plus=0.5*(I2+sx); probe=kron3(rho0,plus,plus)
    stage_list=[(t,o) for t in range(8) for o in NATIVE[t]]
    stages=[]
    for t,o in stage_list:
        F=torch.linalg.matrix_exp(T_FLOW*terrain_super(t))
        M=op_super(o); pv=vec(probe)
        down=unvec(M@(F@pv)); up=unvec(F@(M@pv))
        down=0.5*(down+down.conj().T); up=0.5*(up+up.conj().T)
        dv,uv=pvec(down),pvec(up)
        stages.append({"t":t,"op":o,"pvec_down":dv,"pvec_up":uv,
                       "order_gap":float(np.linalg.norm(np.array(dv)-np.array(uv)))})
    json.dump({"substrate":"torch","device":dev,"stages":stages},
              open(os.path.join(HERE,"torch_results_3q.json"),"w"),indent=1)
    print(f"torch_results_3q.json written (16 stages, 63-dim Pauli) on {dev}, torch {torch.__version__}")

if __name__=="__main__": main()
