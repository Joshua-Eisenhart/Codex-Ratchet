import jax
jax.config.update("jax_enable_x64", True)

# Tool-capability probe: does netket actually build a TFIM Hamiltonian and
# yield a ground-state energy that matches a direct dense diagonalization?
# classification = "diagnostic_only" (no validator gate; tool-capability check).

import jax.numpy as jnp
import numpy as np
import netket as nk
from scipy.sparse.linalg import eigsh

classification = "diagnostic_only"

# --- x64 honored? Confirm a jnp float array is float64, complex is complex128 ---
_rt = jnp.asarray([1.0, 2.0]).dtype
_ct = (jnp.asarray([1.0, 2.0]) + 0j).dtype
rtype = str(_rt)
cdtype = str(_ct)
assert _rt == jnp.float64, f"x64 NOT honored: real dtype is {rtype}, expected float64"
assert _ct == jnp.complex128, f"x64 NOT honored: complex dtype is {cdtype}, expected complex128"

# --- REAL operation: build N=4 1D TFIM via netket, h=1, J=1 ---
N = 4
h = 1.0
J = 1.0
graph = nk.graph.Chain(length=N, pbc=False)          # open chain
hi = nk.hilbert.Spin(s=0.5, N=N)
H = nk.operator.Ising(hilbert=hi, graph=graph, h=h, J=J)

# NetKet operator ground energy via its own sparse matrix -> ARPACK
H_sparse = H.to_sparse()
nk_eigs = eigsh(H_sparse, k=1, which="SA", return_eigenvectors=False)
E_netket = float(np.min(nk_eigs))

# --- KNOWN/analytic comparison: direct dense eigh on the SAME dense operator ---
H_dense = jnp.asarray(np.asarray(H.to_dense()), dtype=jnp.float64)
assert H_dense.dtype == jnp.float64, f"dense H dtype {H_dense.dtype} not float64"
evals = jnp.linalg.eigvalsh(H_dense)
E_dense = float(jnp.min(evals))

delta = abs(E_netket - E_dense)
match = bool(delta < 1e-8)

print(f"netket {nk.__version__} | jax {jax.__version__}")
print(f"rtype={rtype} cdtype={cdtype} H_dense.dtype={H_dense.dtype}")
print(f"E_netket(ARPACK on sparse) = {E_netket:.15f}")
print(f"E_dense  (eigvalsh dense)  = {E_dense:.15f}")
print(f"|delta| = {delta:.3e}  match(<1e-8) = {match}")

if not match:
    raise SystemExit(f"BLOCKER: netket ground energy {E_netket} != dense {E_dense}, delta={delta}")

print("OK: netket TFIM ground energy matches dense diagonalization")
