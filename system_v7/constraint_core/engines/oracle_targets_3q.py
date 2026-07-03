"""
oracle_targets_3q.py -- 3-QUBIT lift of the 16-stage engine contract.
Writes engines/targets_3q.json. PURE MATH, structural indices only.

WHY 3 qubits (owner floor: "at least 3 qubits for many things to really run"):
the carrier is C^8 = C^2 (x) C^2 (x) C^2 == the Cl(0,6)/octonion spinor dim.
The readout is no longer a 3-vector (Bloch) but the 63-dim Pauli-expectation
vector over all non-identity 3-qubit Pauli strings.

FAITHFUL, NON-TRIVIAL lift (the honest part): the terrain dynamics + operators
act on the CARRIER qubit q0, BUT the coherent Hamiltonian carries a genuine
entangling coupling J across the qubit chain (ZZ_{01}+ZZ_{12}). This makes the
3-qubit evolution NON-FACTORIZING: it generates real entanglement between q0 and
q1q2, so the 63-vector holds multi-qubit correlations the 1-qubit contract
cannot. If J=0 the contract would trivially reduce to the 1-qubit one -- we
assert negativity>0 to prove it does not. Same model constants as the 1-qubit
oracle; J_COUP is the one new parameter.
scratch_diagnostic; promotion_allowed=false.
"""
import json, os, itertools
import numpy as np
from scipy.linalg import expm

I2 = np.eye(2, dtype=complex)
sx = np.array([[0,1],[1,0]], complex); sy = np.array([[0,-1j],[1j,0]], complex)
sz = np.array([[1,0],[0,-1]], complex); sp = 0.5*(sx+1j*sy); sm = 0.5*(sx-1j*sy)
PAULI = {'I':I2,'X':sx,'Y':sy,'Z':sz}

# ---- model constants (shared with 1-qubit oracle) + one new coupling ----
G = 0.35; KAP = 1.0; Q = 1.0-float(np.exp(-1.0)); TH = np.pi/4
T_FLOW = 1.0; N_STEPS = 400
J_COUP = 0.5      # NEW: qubit-chain ZZ coupling; J=0 would factorize to 1-qubit
PROBE_B = (0.55, 0.35, 0.25)   # carrier-qubit Bloch; q1,q2 start in |+> to couple

TERR = {0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
        4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
NATIVE = {0:('Ti','Fi'),1:('Ti','Fi'),4:('Ti','Fi'),5:('Ti','Fi'),
          2:('Te','Fe'),3:('Te','Fe'),6:('Te','Fe'),7:('Te','Fe')}

def kron3(a,b,c): return np.kron(np.kron(a,b),c)
def on0(A): return kron3(A,I2,I2)          # single-qubit op lifted to q0

ZZ01 = kron3(sz,sz,I2); ZZ12 = kron3(I2,sz,sz)   # genuine 3-qubit coupling

def D(L,r): return L@r@L.conj().T - 0.5*(L.conj().T@L@r + r@L.conj().T@L)

def gen(ti):
    eps,kind,pole = TERR[ti]
    Hloc = eps*(sx+sy+sz)/np.sqrt(3)
    H = on0(Hloc) + J_COUP*(ZZ01+ZZ12)     # coherent part is genuinely 3-qubit
    Ld = on0(sp if pole>0 else sm)
    def X(r):
        out = -1j*G*(H@r - r@H)
        if kind=='damp':  out = out + KAP*D(Ld,r)
        elif kind=='depol': out = out + 0.5*KAP*(D(on0(sx),r)+D(on0(sy),r))
        else:             out = out + KAP*D(on0(sz),r)
        return out
    return X

def flow(X,r,t=T_FLOW,steps=N_STEPS):
    dt=t/steps
    for _ in range(steps):
        k1=X(r);k2=X(r+.5*dt*k1);k3=X(r+.5*dt*k2);k4=X(r+dt*k3)
        r=r+(dt/6)*(k1+2*k2+2*k3+k4); r=.5*(r+r.conj().T); r/=np.trace(r).real
    return r

def op(name):
    P0=0.5*(I2+sz);P1=0.5*(I2-sz);Qp=0.5*(I2+sx);Qm=0.5*(I2-sx)
    if name=='Ti': return lambda r:(1-Q)*r+Q*(on0(P0)@r@on0(P0)+on0(P1)@r@on0(P1))
    if name=='Te': return lambda r:(1-Q)*r+Q*(on0(Qp)@r@on0(Qp)+on0(Qm)@r@on0(Qm))
    if name=='Fi': U=on0(expm(-1j*TH/2*sx)); return lambda r:U@r@U.conj().T
    if name=='Fe': U=on0(expm(-1j*TH/2*sz)); return lambda r:U@r@U.conj().T

# 63 non-identity Pauli strings on 3 qubits
STRINGS=[''.join(p) for p in itertools.product('IXYZ',repeat=3) if set(p)!={'I'}]
PMATS={s:kron3(PAULI[s[0]],PAULI[s[1]],PAULI[s[2]]) for s in STRINGS}
def pvec(r): return [float(np.trace(r@PMATS[s]).real) for s in STRINGS]

def negativity(r):  # entanglement across q0 | q1q2 (partial transpose on q0)
    R=r.reshape(2,4,2,4).transpose(2,1,0,3).reshape(8,8)
    ev=np.linalg.eigvalsh(0.5*(R+R.conj().T))
    return float(sum(abs(e) for e in ev if e<0))

def main():
    rho0_q0=0.5*(I2+PROBE_B[0]*sx+PROBE_B[1]*sy+PROBE_B[2]*sz)
    plus=0.5*(I2+sx)
    probe=kron3(rho0_q0,plus,plus)          # q1,q2 in |+> so ZZ coupling bites
    stages,terrains=[],[]
    for t in range(8):
        X=gen(t)
        fp=flow(X,probe.copy(),t=8.0,steps=1600)
        terrains.append({"t":t,"nonunital":int(np.linalg.norm(X(np.eye(8,dtype=complex)))>1e-9),
                         "neg_fixed":negativity(fp)})
        for o in NATIVE[t]:
            J=op(o)
            down=pvec(J(flow(X,probe.copy())))     # terrain-first
            up=pvec(flow(X,J(probe.copy())))       # operator-first
            gap=float(np.linalg.norm(np.array(down)-np.array(up)))
            neg=negativity(J(flow(X,probe.copy())))
            stages.append({"t":t,"op":o,"pvec_down":down,"pvec_up":up,
                           "order_gap":gap,"negativity":neg})
    M=np.array([s["pvec_down"]+s["pvec_up"] for s in stages])
    dmin=min(float(np.linalg.norm(M[i]-M[j])) for i in range(16) for j in range(i+1,16))
    maxneg=max(s["negativity"] for s in stages)
    out={"model_constants":{"G":G,"KAP":KAP,"Q":Q,"TH":TH,"T_FLOW":T_FLOW,
                            "N_STEPS":N_STEPS,"J_COUP":J_COUP,"PROBE_B":PROBE_B},
         "pauli_strings":STRINGS,"stages":stages,"terrains":terrains,
         "invariants":{"n_stages":16,"n_pauli":63,"min_pairwise_dist":dmin,
                       "all_order_gaps_positive":bool(all(s["order_gap"]>1e-6 for s in stages)),
                       "nonunital_bits":[tr["nonunital"] for tr in terrains],
                       "max_negativity":maxneg,
                       "genuinely_3q":bool(maxneg>1e-3)},
         "tolerances":{"pvec_abs":1e-6,"order_gap_abs":1e-6,"neg_abs":1e-4}}
    here=os.path.dirname(os.path.abspath(__file__))
    json.dump(out,open(os.path.join(here,"targets_3q.json"),"w"),indent=1)
    print(f"targets_3q.json: 16 stages in 63-dim Pauli space, min pairwise {dmin:.4f}, "
          f"all order gaps>0: {out['invariants']['all_order_gaps_positive']}, "
          f"nonunital {out['invariants']['nonunital_bits']}, max negativity {maxneg:.4f}, "
          f"genuinely 3q: {out['invariants']['genuinely_3q']}")

if __name__=="__main__": main()
