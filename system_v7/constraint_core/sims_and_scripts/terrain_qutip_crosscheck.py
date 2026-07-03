"""
terrain_qutip_crosscheck.py -- the 8 terrain generators, cross-checked against QuTiP's
standard Lindblad machinery (an independent QIT library; 5th route at the operator level).

Confirms three things with QuTiP, NOT the hand-rolled code:
  (1) each terrain's Liouvillian matches QuTiP's qt.liouvillian to machine precision
  (2) each terrain flow exp(t.L) is a valid CPTP channel (QuTiP Choi matrix PSD)
  (3) the nonunitality pattern [1,0,1,0,1,0,1,0] (QuTiP superoperator applied to I)

QuTiP is control-lane-adjacent but here it is LOAD-BEARING: it independently reproduces
the generator algebra, so a bug in the hand-rolled superoperator would surface as a
mismatch. scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np, qutip as qt
except ImportError as e:
    print(f"SKIP_OPTIONAL terrain_qutip_crosscheck: missing tool ({e.name}); pip install z3-solver cvc5 qutip")
    sys.exit(0)
G,KAP=0.35,1.0
sx,sy,sz=qt.sigmax(),qt.sigmay(),qt.sigmaz(); I2=qt.qeye(2)
sp,sm=0.5*(sx+1j*sy),0.5*(sx-1j*sy); H0=(sx+sy+sz)/np.sqrt(3)
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
Inp=np.eye(2,dtype=complex)
def sL(A): return np.kron(Inp,A)
def sR(A): return np.kron(A.T,Inp)
def sD(L): Ld=L.conj().T; return sL(L)@sR(Ld)-0.5*(sL(Ld@L)+sR(Ld@L))
def sC(H): return -1j*(sL(H)-sR(H))
def eng_L(ti):
    eps,kind,pole=TERR[ti]; L=G*sC(eps*H0.full())
    if kind=='damp': L+=KAP*sD((sp if pole>0 else sm).full())
    elif kind=='depol': L+=0.5*KAP*(sD(sx.full())+sD(sy.full()))
    else: L+=KAP*sD(sz.full())
    return L
def qutip_L(ti):
    eps,kind,pole=TERR[ti]; H=G*eps*H0
    if kind=='damp': cops=[np.sqrt(KAP)*(sp if pole>0 else sm)]
    elif kind=='depol': cops=[np.sqrt(0.5*KAP)*sx, np.sqrt(0.5*KAP)*sy]
    else: cops=[np.sqrt(KAP)*sz]
    return qt.liouvillian(H,cops)

worst=0.0; cptp_ok=True; bits=[]
for ti in range(8):
    d=np.max(np.abs(eng_L(ti)-qutip_L(ti).full())); worst=max(worst,d)
    Lq=qutip_L(ti); choi=qt.to_choi((1.0*Lq).expm())
    if np.min(np.linalg.eigvalsh(choi.full()))<-1e-9: cptp_ok=False
    LI=qt.vector_to_operator(Lq*qt.operator_to_vector(I2)).full()
    bits.append(int(np.linalg.norm(LI)>1e-9))

print(f"(1) max |L_engine - L_qutip| over 8 terrains: {worst:.2e}")
print(f"(2) all 8 flows CPTP (QuTiP Choi PSD): {cptp_ok}")
print(f"(3) nonunitality bits (QuTiP): {bits}")

assert worst<1e-12, "QuTiP liouvillian must match the engine superoperator"
assert cptp_ok, "all terrain channels must be CPTP"
assert bits==[1,0,1,0,1,0,1,0], "nonunitality pattern must match"
print("\nPASS terrain_qutip_crosscheck")
