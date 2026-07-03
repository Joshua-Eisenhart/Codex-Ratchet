"""
holographic_bound_sim.py -- the constraint core realizes the FINITUDE axiom as the quantum
kernel of the holographic / Bekenstein bound: a bounded region holds BOUNDED information.
NOT a ToE validation -- a check that the engine's states obey confirmed information bounds.

  (1) CAPACITY bound: S(rho) <= log2(dim) bits for ANY state; the maximally-mixed state
      saturates it exactly (S(I/2^n) = n bits). No state, however prepared, exceeds it.
  (2) AREA LAW / Page curve: for a random pure state on n qubits, a subsystem A's entanglement
      entropy is bounded by min(|A|,|B|) -- the SMALLER boundary caps the shared information,
      peaking at the symmetric split. Generic states are near-maximally entangled.

Together: finitude at BOTH whole-system and subsystem level. numpy-only.
scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
except ImportError as e:
    print(f"SKIP_OPTIONAL holographic_bound_sim: missing tool ({e.name})"); sys.exit(0)

def S_bits(rho):
    w=np.linalg.eigvalsh(rho); w=w[w>1e-15]; return float(-np.sum(w*np.log2(w)))
def rand_pure(dim,rng):
    v=rng.normal(size=dim)+1j*rng.normal(size=dim); return v/np.linalg.norm(v)
def rand_mixed(dim,rank,rng):
    A=rng.normal(size=(dim,rank))+1j*rng.normal(size=(dim,rank)); r=A@A.conj().T; return r/np.trace(r).real
def ptrace_keep(psi,dimA,dimB):
    M=psi.reshape(dimA,dimB); return M@M.conj().T

rng=np.random.default_rng(0)
# (1) capacity
print("(1) capacity bound S(rho) <= log2(dim):")
cap_ok=True
for n in [1,2,3]:
    dim=2**n; smax=max(S_bits(rand_mixed(dim,rng.integers(1,dim+1),rng)) for _ in range(400))
    sat=S_bits(np.eye(dim)/dim)
    print(f"    n={n}: max random S={smax:.4f} <= {n}; maximally-mixed saturates S(I/{dim})={sat:.4f}")
    cap_ok = cap_ok and smax<=n+1e-9 and abs(sat-n)<1e-9
# (2) area law
print("(2) area law / Page curve (n=6, random pure states):")
rng2=np.random.default_rng(1); n=6; dim=2**n; area_ok=True
for nA in range(1,n):
    dimA=2**nA; dimB=2**(n-nA); bound=min(nA,n-nA)
    Ss=[S_bits(ptrace_keep(rand_pure(dim,rng2),dimA,dimB)) for _ in range(200)]
    print(f"    |A|={nA}: mean S(A)={np.mean(Ss):.3f}, max={max(Ss):.3f} <= min(|A|,|B|)={bound}")
    area_ok = area_ok and max(Ss)<=bound+1e-9

assert cap_ok, "no state may exceed log2(dim); maximally-mixed must saturate"
assert area_ok, "subsystem entropy must be bounded by min(|A|,|B|)"
print("\nPASS holographic_bound_sim")
