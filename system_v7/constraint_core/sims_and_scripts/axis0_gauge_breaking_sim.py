"""
axis0_gauge_breaking_sim.py  v3  —  PURE MATH, NO JARGON.  CORRECTED 2026-07-01.

Structural facts about the gauge charge a2 and symmetry-breaking dissipation.

CORRECTION (2026-07-01, external audit): v1/v2 reported a "linear law
a2-physicality = k*delta, R^2=0.999997". That was an ARTIFACT: the dissipation was a single
Kraus step K0=sqrt(1-delta/2)I, K1=sqrt(delta/2)Z, which maps coherence rho01 -> (1-delta)rho01,
i.e. affine in delta BY CONSTRUCTION (split/delta constant to 5e-17 out to delta=2). The
R^2=1 was an algebraic identity of the parametrization, not a discovered law. WITHDRAWN.

WHAT SURVIVES (both exact, both structural):
  (1) EXACT GAUGE DEGENERACY at delta=0: [V, exp(-iH0 t)]=0, so the two unitary objects
      (a1=1,a2=0) and (a1=1,a2=1) are the IDENTICAL channel (~3e-16). The parity p=a1 XOR a2
      is therefore NOT a single-channel observable there.
  (2) MONOTONE (not linear) co-ratchet link: under a genuine GKSL dephasing semigroup the
      frame bit becomes physical, growing from exactly 0 at delta=0; split/delta FALLS
      (0.15 -> 0.039) as delta grows -- an ordinary saturating first-order response.

Interpretation lives in the rosetta layer. scratch_diagnostic; promotion_allowed=false.
Requires: numpy, scipy.
"""
import numpy as np
from scipy.linalg import expm
I2=np.eye(2,dtype=complex)
SX=np.array([[0,1],[1,0]],complex); SY=np.array([[0,-1j],[1j,0]],complex); SZ=np.array([[1,0],[0,-1]],complex)
AXIS=np.array([1,1,1.])/np.sqrt(3); H0=AXIS[0]*SX+AXIS[1]*SY+AXIS[2]*SZ
V=expm(-1j*H0*0.9); BELL=np.array([1,0,0,1],complex)/np.sqrt(2); RHO0=np.outer(BELL,BELL.conj())

def commutator_norm(): return float(np.linalg.norm(V@expm(-1j*H0*0.7)-expm(-1j*H0*0.7)@V))

def channel_gksl(a2, delta, rho, t=0.7, steps=2000):
    """Unitary about H0 in frame a2, then a GENUINE GKSL dephasing semigroup of rate delta over time 1."""
    Vb=V if a2==1 else I2
    U=np.kron(Vb@expm(-1j*H0*t)@Vb.conj().T, I2); rho=U@rho@U.conj().T
    if delta>0:
        Z=Vb@SZ@Vb.conj().T; L=np.kron(Z,I2); dt=1.0/steps
        for _ in range(steps):
            rho=rho+dt*delta*(L@rho@L.conj().T-0.5*(L.conj().T@L@rho+rho@L.conj().T@L))
    return rho

def a2_split(delta):
    return abs(channel_gksl(1,delta,RHO0.copy())[0,3]-channel_gksl(0,delta,RHO0.copy())[0,3])

if __name__=="__main__":
    print(f"(1) ||[V, exp(-iH0 t)]|| = {commutator_norm():.2e}  (0 => unitary a2 is pure gauge)")
    ch0=channel_gksl(0,0.0,RHO0.copy()); ch1=channel_gksl(1,0.0,RHO0.copy())
    print(f"    identical channel at delta=0: ||ch1-ch0|| = {np.linalg.norm(ch1-ch0):.2e}")
    print("(2) GKSL semigroup -- split and split/delta (NOT constant => no linear law):")
    for d in [0.05,0.1,0.2,0.4,0.6,1.0,1.5,2.0]:
        s=a2_split(d); print(f"      delta={d:.2f}  split={s:.4f}  split/delta={s/d:.4f}")
    print("    monotone increasing, saturating: an ordinary first-order response, NOT a law.")
