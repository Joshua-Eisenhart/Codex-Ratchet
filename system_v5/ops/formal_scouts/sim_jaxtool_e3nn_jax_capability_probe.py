import jax
jax.config.update("jax_enable_x64", True)

# --- e3nn_jax x64 capability probe -------------------------------------------
# classification = "diagnostic_only"
# Role: equivariant geometry checks (rotations / Wigner-D).
# Operation: build an SO(3) rotation from Euler angles via e3nn_jax.angles_to_matrix,
# recover the angles via matrix_to_angles, rebuild the matrix, and check the
# round-trip recovers the original rotation to < 1e-12 at x64, with det(R)==1 and
# R orthogonal (R R^T = I). This re-confirms the earlier spinor-twin finding at x64.
# ANTI-FABRICATION: match is computed from real numerical comparison, never hardcoded.

import jax.numpy as jnp
import e3nn_jax as e3nn

classification = "diagnostic_only"

# --- x64 honored check: a jnp float array must be float64 ---------------------
_probe = jnp.array([1.0, 2.0, 3.0])
rtype = str(_probe.dtype)
x64_honored = (_probe.dtype == jnp.float64)
assert x64_honored, f"x64 not honored: float array dtype is {rtype}, expected float64"

# complex dtype live report (Wigner-D / equivariant ops touch complex128 at x64)
_cprobe = jnp.array([1.0 + 2.0j])
cdtype = str(_cprobe.dtype)
assert _cprobe.dtype == jnp.complex128, f"x64 not honored for complex: {cdtype}"

# --- build a known SO(3) rotation from explicit Euler angles ------------------
# Generic angles away from gimbal-lock (beta != 0, pi) and away from the
# matrix_to_angles branch cut.
alpha = jnp.float64(0.7)
beta = jnp.float64(1.1)
gamma = jnp.float64(-0.4)

R = e3nn.angles_to_matrix(alpha, beta, gamma)
assert R.dtype == jnp.float64, f"rotation matrix not float64: {R.dtype}"

# --- round-trip: matrix -> angles -> matrix -----------------------------------
a2, b2, g2 = e3nn.matrix_to_angles(R)
R_recon = e3nn.angles_to_matrix(a2, b2, g2)

# Compare the reconstructed ROTATION MATRIX to the original. The matrix is the
# canonical, branch-cut-free invariant (Euler angles are multi-valued), so this
# is the honest round-trip check.
recon_err = float(jnp.max(jnp.abs(R_recon - R)))

# --- group-element sanity: det(R) == 1, R orthogonal -------------------------
detR = float(jnp.linalg.det(R))
ortho_err = float(jnp.max(jnp.abs(R @ R.T - jnp.eye(3, dtype=jnp.float64))))

TOL = 1e-12
recon_ok = recon_err < TOL
det_ok = abs(detR - 1.0) < TOL
ortho_ok = ortho_err < TOL

match = bool(recon_ok and det_ok and ortho_ok)

invariant = "matrix_to_angles(angles_to_matrix(a,b,g)) rebuilds R; recon_err<1e-12, det(R)==1, R R^T==I"
computed = (
    f"recon_err={recon_err:.3e} (ok={recon_ok}), "
    f"det(R)={detR:.15f} (ok={det_ok}), "
    f"ortho_err={ortho_err:.3e} (ok={ortho_ok})"
)
known = "recon_err==0, det(R)==1, ortho_err==0 for a proper SO(3) rotation; all < 1e-12 at x64"

print(f"classification = {classification}")
print(f"rtype  = {rtype}")
print(f"cdtype = {cdtype}")
print(f"x64_honored = {x64_honored}")
print(f"R.dtype = {R.dtype}")
print(f"recovered angles: alpha={float(a2):.15f} beta={float(b2):.15f} gamma={float(g2):.15f}")
print(f"INVARIANT: {invariant}")
print(f"COMPUTED : {computed}")
print(f"KNOWN    : {known}")
print(f"MATCH    : {match}")

if not match:
    raise SystemExit(
        f"BLOCKER: e3nn_jax round-trip failed at x64. {computed}"
    )

print("RESULT: works")
