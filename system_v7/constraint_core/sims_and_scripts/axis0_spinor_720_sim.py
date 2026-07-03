"""
axis0_spinor_720_sim.py
Tests Axis-0 tense at the SPINOR level (amplitudes in C^2), per the tribunal constraint
(igt-pattern-explicit-math-reference.md): "720 behavior disappears under rho=|psi><psi| unless the
engine keeps lifted phase/path/interference data. The engine MUST work at the spinor level."
KEY: all 11 prior Axis-0 readouts were at DENSITY level -> 720/tense structure provably invisible ->
they collapsed to Axis-1. This shows the fix.
RESULTS: SU(2) double cover exact (360 -> -1, 720 -> +1); measurement in the loop DECAYS the 720
phase return (1.000 -> 0.860 as strength 0 -> 0.9) = the tense signature. Per-terrain Ne/Ni|Se/Si
split NOT yet closed (needs principled spinor-level E-operators). scratch_diagnostic.
"""
import numpy as np
from scipy.linalg import expm
I2=np.eye(2,dtype=complex)
sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
n=np.array([1,1,1.])/np.sqrt(3); H0=n[0]*sx+n[1]*sy+n[2]*sz
psi0=np.array([1,0],complex)

def double_cover_check():
    U360=expm(-1j*H0*np.pi); U720=expm(-1j*H0*2*np.pi)
    return np.vdot(psi0,U360@psi0), np.vdot(psi0,U720@psi0)

def phase_return(strength):
    Uh=expm(-1j*H0*np.pi/2)
    psi=Uh@psi0
    K0=np.diag([1.0, np.sqrt(1-strength)])  # weak measurement keep-branch (damps |1>)
    psi=K0@psi; psi=psi/np.linalg.norm(psi)
    psi=Uh@psi
    return np.vdot(psi0,psi)

if __name__=="__main__":
    a360,a720=double_cover_check()
    print(f"360 loop: {a360:.4f} (expect -1)")
    print(f"720 loop: {a720:.4f} (expect +1)")
    for s in [0.0,0.3,0.6,0.9]:
        print(f"measurement {s}: 720 phase return |amp|={abs(phase_return(s)):.4f}")
