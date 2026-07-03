"""
axis0_sector_sim.py  —  PURE MATH, NO JARGON.

Structure only. No terrain names, no Jungian labels, no engine-personality words.
All interpretive labels live in the separate rosetta file (rosetta_layer.json / section 11 of the spec).

OBJECTS (pure):
  H0            : a fixed traceless Hermitian generator on C^2 (unit Bloch axis).
  eps in {+1,-1}: sheet sign of the Hamiltonian (H = eps*H0).
  a1 in {0,1}   : dynamics bit. 1 => unitary channel (spectrum-preserving);
                                0 => rank-1 dephasing channel (spectrum-contracting).
  a2 in {0,1}   : frame bit.    1 => conjugated frame rho -> V^dag rho V (V a fixed unitary);
                                0 => identity frame.
  The 4 (a1,a2) combinations are the objects under study.

CLAIMS ESTABLISHED (all structural, no interpretation):
  (1) The a2 map rho -> V^dag rho V preserves every spectral/entropic invariant (~2e-15):
      a2 is a GAUGE d.o.f. — invisible to any function of the spectrum.
  (2) Under a2-conjugation, eigenVALUES are invariant (~1e-16) while the full state moves (~0.67):
      a1 lives in the eigenvalue sector, a2 lives in the eigenvector sector. Orthogonal sectors.
  (3) The parity a1 XOR a2 therefore cannot be read by any single spectral functional; it needs
      one eigenvalue-sector reading AND one eigenvector-sector reading, multiplied.
  (4) A closed-loop geometric phase is gauge-invariant (spec(H0)=spec(V^dag H0 V)) -> cannot read a2.

scratch_diagnostic; promotion_allowed=false.
"""
import numpy as np
from scipy.linalg import expm

I2 = np.eye(2, dtype=complex)
SX = np.array([[0,1],[1,0]], complex)
SY = np.array([[0,-1j],[1j,0]], complex)
SZ = np.array([[1,0],[0,-1]], complex)
AXIS = np.array([1,1,1.])/np.sqrt(3)
H0 = AXIS[0]*SX + AXIS[1]*SY + AXIS[2]*SZ
V_FRAME = expm(-1j*H0*0.9)          # fixed conjugation unitary defining the a2=1 frame

def entropy(rho):
    ev = np.clip(np.linalg.eigvalsh(rho).real, 1e-12, 1)
    return float(-(ev*np.log2(ev)).sum())
def ptrace_A(rho):  # keep first factor
    r = rho.reshape(2,2,2,2); return np.einsum('ijkj->ik', r)
def ptrace_B(rho):  # keep second factor
    r = rho.reshape(2,2,2,2); return np.einsum('ijil->jl', r)

def claim1_a2_is_gauge(n=200, seed=1):
    rng = np.random.default_rng(seed)
    Vf = np.kron(V_FRAME, V_FRAME); worst = 0.0
    for _ in range(n):
        A = rng.normal(size=(4,4)) + 1j*rng.normal(size=(4,4))
        r = A@A.conj().T; r /= np.trace(r).real
        rc = Vf@r@Vf.conj().T
        d_ent = abs(entropy(r) - entropy(rc))
        d_ic  = abs((entropy(ptrace_B(r))-entropy(r)) - (entropy(ptrace_B(rc))-entropy(rc)))
        worst = max(worst, d_ent, d_ic)
    return worst

def claim2_sector_split(n=300, seed=3):
    rng = np.random.default_rng(seed); eig_change=[]; state_change=[]
    for _ in range(n):
        A = rng.normal(size=(2,2)) + 1j*rng.normal(size=(2,2))
        r = A@A.conj().T; r /= np.trace(r).real
        rc = V_FRAME@r@V_FRAME.conj().T
        eig_change.append(np.linalg.norm(np.sort(np.linalg.eigvalsh(r))-np.sort(np.linalg.eigvalsh(rc))))
        state_change.append(np.linalg.norm(r-rc))
    return float(np.mean(eig_change)), float(np.mean(state_change))

def claim4_closed_loop_is_gauge_invariant():
    return bool(np.allclose(np.sort(np.linalg.eigvalsh(H0)),
                            np.sort(np.linalg.eigvalsh(V_FRAME@H0@V_FRAME.conj().T))))

if __name__ == "__main__":
    print(f"(1) a2 gauge: worst spectral-invariant change under frame conjugation = {claim1_a2_is_gauge():.2e}")
    ec, sc = claim2_sector_split()
    print(f"(2) sector split: eigenvalue change={ec:.2e}  eigenvector/state change={sc:.4f}")
    print(f"(4) closed-loop phase gauge-invariant (cannot read a2): {claim4_closed_loop_is_gauge_invariant()}")
