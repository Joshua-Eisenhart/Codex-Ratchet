"""
constraint_core_audit.py
Machine-checked verification of the concrete realization of the constraint-based core.
Run: python constraint_core_audit.py   (requires numpy, scipy)

Verifies the laws that the ℂ²/S³ Hopf realization states about itself:
  C1 sigma_pm identity        C4 all 8 terrain generators CPTP
  C2 Hopf->Bloch->density      C5 derived axis law b6 = -b0*b3
  C3 Weyl Bloch laws           C6 Pit sink / Source fixed points
                               C7 entropy peak at Clifford torus
"""
import numpy as np
from scipy.linalg import expm

I2=np.eye(2,dtype=complex)
sx=np.array([[0,1],[1,0]],dtype=complex); sy=np.array([[0,-1j],[1j,0]],dtype=complex)
sz=np.array([[1,0],[0,-1]],dtype=complex); sm=np.array([[0,0],[1,0]],dtype=complex)
sp=np.array([[0,1],[0,0]],dtype=complex); sig=[sx,sy,sz]
rng=np.random.default_rng(0)

def psi(phi,chi,eta):
    return np.array([np.exp(1j*(phi+chi))*np.cos(eta), np.exp(1j*(phi-chi))*np.sin(eta)],dtype=complex)

# ---- C1 ----
C1 = np.allclose(0.5*(sx+1j*sy),sp) and np.allclose(0.5*(sx-1j*sy),sm)

# ---- C2 ----  NOTE chart-consistent r_y = -sin2eta sin2chi
be=re=fe=0.0
for _ in range(2000):
    phi,chi,eta=rng.uniform(0,2*np.pi),rng.uniform(0,2*np.pi),rng.uniform(0,np.pi/2)
    p=psi(phi,chi,eta); rm=np.array([(p.conj()@s@p).real for s in sig])
    rp=np.array([np.sin(2*eta)*np.cos(2*chi),-np.sin(2*eta)*np.sin(2*chi),np.cos(2*eta)])
    be=max(be,np.max(np.abs(rm-rp)))
    rho=np.outer(p,p.conj()); rho_p=0.5*(I2+sum(rp[i]*sig[i] for i in range(3)))
    re=max(re,np.max(np.abs(rho-rho_p)))
    p2=psi(phi+rng.uniform(0,2*np.pi),chi,eta); fe=max(fe,np.max(np.abs(rho-np.outer(p2,p2.conj()))))

# ---- C3 ----
def bloch_law_err(H,n,sgn):
    e=0.0
    for _ in range(500):
        r=rng.uniform(-1,1,3); r=r/np.linalg.norm(r)*rng.uniform(0,1)
        rho=0.5*(I2+sum(r[i]*sig[i] for i in range(3))); rhod=-1j*(H@rho-rho@H)
        e=max(e,np.max(np.abs(np.array([np.trace(s@rhod).real for s in sig])-sgn*2*np.cross(n,r))))
    return e
n=rng.uniform(-1,1,3); H0=sum(n[i]*sig[i] for i in range(3))
C3L=bloch_law_err(+H0,n,+1); C3R=bloch_law_err(-H0,n,-1)

# ---- C4 ----
def spre(A):return np.kron(np.eye(2),A)
def spost(B):return np.kron(B.T,np.eye(2))
def sand(L):return np.kron(L.conj(),L)
def comm(H):return -1j*(spre(H)-spost(H))
def diss(L):
    LdL=L.conj().T@L; return sand(L)-0.5*(spre(LdL)+spost(LdL))
def tp(S):
    v=np.eye(2).reshape(-1,order='F'); return np.max(np.abs(v.conj()@S))<1e-10
def cp(S,t):
    E=expm(t*S); d=2; C=np.zeros((d*d,d*d),dtype=complex)
    for i in range(d):
        for j in range(d):
            Eij=np.zeros((d,d),dtype=complex);Eij[i,j]=1
            out=(E@Eij.reshape(-1,order='F')).reshape(d,d,order='F'); C+=np.kron(out,Eij)
    return np.linalg.eigvalsh((C+C.conj().T)/2).min()
HL,HR=+H0,-H0; Lk=0.3*I2+0.2*sx+0.1*sy-0.15*sz; Mk=0.25*I2+0.1*sx-0.2*sy+0.05*sz
P0=0.5*(I2+sz);P1=0.5*(I2-sz)
def sidep(Ps,ks):return sum(k*(sand(P)-0.5*(spre(P.conj().T@P)+spost(P.conj().T@P))) for k,P in zip(ks,Ps))
gens={'Se_Funnel_L':diss(Lk)+comm(0.7*HL),'Se_Cannon_R':diss(Lk)+comm(0.7*HR),
 'Ne_Vortex_L':comm(HL)+0.4*diss(Mk),'Ne_Spiral_R':comm(HR)+0.4*diss(Mk),
 'Ni_Pit_L':0.5*diss(sm)+comm(0.6*HL),'Ni_Source_R':0.5*diss(sp)+comm(0.6*HR),
 'Si_Hill_L':comm(HL)+sidep([P0,P1],[0.3,0.3]),'Si_Citadel_R':comm(HR)+sidep([P0,P1],[0.3,0.3])}
C4=all(tp(S) and cp(S,0.5)>-1e-9 and cp(S,3.0)>-1e-9 for S in gens.values())

# ---- C5 ----
terr=[("Se_f",-1,-1,-1),("Si_f",-1,-1,-1),("Ne_f",1,-1,1),("Ni_f",1,-1,1),
      ("Se_b",-1,1,1),("Si_b",-1,1,1),("Ne_b",1,1,-1),("Ni_b",1,1,-1)]
C5=all((-b0*b3)==b6 for _,b0,b3,b6 in terr)

# ---- C6 ----
def rz_inf(S,t=40.0):
    r=np.array([0.3,-0.4,0.2]); rho=0.5*(I2+sum(r[i]*sig[i] for i in range(3)))
    out=(expm(t*S)@rho.reshape(-1,order='F')).reshape(2,2,order='F'); return np.trace(sz@out).real
C6=rz_inf(diss(sm))<-0.99 and rz_inf(diss(sp))>0.99

# ---- C7 ----
def S_orbit(e):
    p=np.array([np.cos(e)**2,np.sin(e)**2]); p=p[p>0]; return float(-(p*np.log(p)).sum())
etas=np.linspace(0.01,np.pi/2-0.01,400); es=etas[int(np.argmax([S_orbit(e) for e in etas]))]
C7=abs(es-np.pi/4)<0.02

for k,v in [("C1 sigma_pm",C1),("C2 bloch_err",be),("C2 density_err",re),("C2 fiber_err",fe),
            ("C3 left",C3L),("C3 right",C3R),("C4 all CPTP",C4),("C5 b6=-b0b3",C5),
            ("C6 sink/source",C6),("C7 entropy peak",C7)]:
    print(f"{k:20s}: {v}")
