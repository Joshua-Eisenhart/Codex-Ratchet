"""
chi2_openpath_readout_sim.py  —  PURE MATH, NO JARGON.  2026-07-01.

Closes the last open item at the current layer: a WORKING readout for the eigenvector-sector
(phase) charge chi2. Closed-loop holonomy failed because it is gauge-invariant and returns to
zero. The Bargmann/Pancharatnam OPEN-PATH phase is nonzero for an open path yet still
gauge-invariant under per-ket rephasing -- exactly what was needed.

  chi2(rho) = -arg( <r0|e><e|r1><r1|r0> ),  e = top eigenvector of rho, r0,r1 fixed references.

*** GRADE CORRECTION (fourth audit, 2026-07-01; see chi2_decisive_test_sim.py and spec 7w). ***
This sim earns chi2 as an EIGENVECTOR-SECTOR meter (properties A-C hold exactly). Property D
below is DEMONSTRATED ON THE K-MIRROR PAIR (V vs V*, complex conjugation), NOT the a2
direct/conjugated pair. chi2 responds to all three frame operations (a2: V-vs-I; eps:
V-vs-Vdag; K: V-vs-V*) and is NOT a2-specific. The a2 bit is earned at the OPERATOR layer
(spec 7t, W-covariance) and provably does not descend to a terrain-generator functional
(spec 7w). Read "the frame bit" in property D as "the K-mirror bit". The math is unchanged.

Verified properties:
  A. open-path (3 distinct states nonzero; closed/degenerate = 0) -- unlike holonomy.
  B. gauge-invariant under |psi> -> e^{i phi}|psi> (the phase gauge).
  C. two-sector orthogonality: chi2 tracks EIGENVECTORS, is constant under spectral change;
     entropy tracks the SPECTRUM, is blind to eigenvectors.
  D. chi2 reads the V-vs-V* (K-MIRROR) frame operation that entropy cannot see. Over 2000
     random probes: entropy |V-vs-V*| < 1e-15 (blind); chi2 reads it on 99.7% (misses only
     the measure-zero set where the eigenvector hits a reference pole). NOTE: this is the
     K-pair, not the a2 pair -- chi2 is a sector meter, not a2-specific (see header).

scratch_diagnostic; promotion_allowed=false. Requires: numpy, scipy.
"""
import numpy as np
from scipy.linalg import expm
I2=np.eye(2,dtype=complex)
SX=np.array([[0,1],[1,0]],complex); SY=np.array([[0,-1j],[1j,0]],complex); SZ=np.array([[1,0],[0,-1]],complex)
def bargmann_phase(p0,p1,p2):
    z=(p0.conj()@p1)*(p1.conj()@p2)*(p2.conj()@p0); return -np.angle(z)
r0=np.array([1,0],complex); r1=np.array([1,1],complex)/np.sqrt(2)
def vN(rho):
    w=np.linalg.eigvalsh(rho); w=w[w>1e-12]; return float(-(w*np.log(w)).sum())
def chi2(rho):
    w,v=np.linalg.eigh(rho); e=v[:,np.argmax(w)]; return bargmann_phase(r0,e,r1)
def bloch_ket(nx,ny,nz):
    n=np.array([nx,ny,nz],float); n=n/np.linalg.norm(n); th=np.arccos(n[2]); ph=np.arctan2(n[1],n[0])
    return np.array([np.cos(th/2),np.exp(1j*ph)*np.sin(th/2)],complex)
def make_rho(ax,spec):
    e=bloch_ket(*ax); P=np.outer(e,e.conj()); rho=spec[0]*P+spec[1]*(I2-P); return rho/np.trace(rho)
H0=(SX+SY+SZ)/np.sqrt(3); V=expm(-1j*H0*0.9); Vc=V.conj()
if __name__=="__main__":
    a=bloch_ket(1,0,0.3); b=bloch_ket(0,1,0.3); c=bloch_ket(-1,0,0.3)
    print(f"A open-path: open={bargmann_phase(a,b,c):+.4f} (nonzero)  closed={bargmann_phase(a,b,a):+.4f} (zero)")
    ph=[0.7,-1.3,2.1]
    g2=bargmann_phase(np.exp(1j*ph[0])*a,np.exp(1j*ph[1])*b,np.exp(1j*ph[2])*c)
    print(f"B gauge-invariant under rephasing: diff={abs(bargmann_phase(a,b,c)-g2):.2e}")
    print("C two-sector (vary eigenvector, S fixed .8/.2):")
    for ax in [(1,0,0.3),(0,1,0.3),(1,1,0.3)]:
        r=make_rho(ax,(0.8,0.2)); print(f"    {str(ax):11s}: chi2={chi2(r):+.4f}  S={vN(r):.4f}")
    print("  (vary spectrum, eigenvector fixed):")
    for sp in [(0.9,0.1),(0.7,0.3),(0.6,0.4)]:
        r=make_rho((0,1,0.3),sp); print(f"    {str(sp):11s}: chi2={chi2(r):+.4f}  S={vN(r):.4f}")
    rng=np.random.default_rng(1); ed=[];cd=[]
    for _ in range(2000):
        n=rng.normal(size=3); n=n/np.linalg.norm(n); rr=rng.uniform(0.3,0.95)
        rho=0.5*(I2+rr*(n[0]*SX+n[1]*SY+n[2]*SZ))
        rd=V@rho@V.conj().T; rcj=Vc@rho@Vc.conj().T
        ed.append(abs(vN(rd)-vN(rcj))); cd.append(abs(chi2(rd)-chi2(rcj)))
    ed=np.array(ed); cd=np.array(cd)
    print(f"D Xi parity over 2000 probes: entropy max|diff|={ed.max():.1e} (blind); "
          f"chi2 reads frame on {np.mean(cd>1e-6)*100:.1f}%, mean={cd.mean():.3f}")
