import jax
jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import lineax as lx

# classification = "diagnostic_only"
# Tool-capability probe: lineax JAX-native linear solve / least-squares.
# Verifies a REAL solve A x = b against a known/analytic reference.
# No validator gate (tool-capability check only).

# --- Known well-conditioned SPD 4x4 system ----------------------------------
# Build an SPD matrix A = M^T M + 4 I (guaranteed symmetric positive definite,
# well-conditioned) and a known b. Solve A x = b two ways and compare to a
# reference (jnp.linalg.solve), plus check the residual ||A x - b||.
M = jnp.array(
    [
        [2.0, 0.5, 0.1, 0.0],
        [0.3, 3.0, 0.2, 0.4],
        [0.0, 0.1, 2.5, 0.6],
        [0.2, 0.0, 0.3, 4.0],
    ],
    dtype=jnp.float64,
)
A = M.T @ M + 4.0 * jnp.eye(4, dtype=jnp.float64)
b = jnp.array([1.0, -2.0, 3.0, 0.5], dtype=jnp.float64)

# --- x64 honored check -------------------------------------------------------
assert A.dtype == jnp.float64, f"A dtype is {A.dtype}, expected float64"
assert b.dtype == jnp.float64, f"b dtype is {b.dtype}, expected float64"
rtype = str(A.dtype)
cdtype = str((A.astype(jnp.complex128)).dtype)
print(f"x64 honored: A.dtype={rtype}, complex cast dtype={cdtype}")

# --- REAL lineax operation ---------------------------------------------------
operator = lx.MatrixLinearOperator(A)
sol = lx.linear_solve(operator, b)
x = sol.value
print(f"lineax x = {x}")

# --- Reference / analytic comparison ----------------------------------------
x_ref = jnp.linalg.solve(A, b)
print(f"jnp.linalg.solve x_ref = {x_ref}")

residual = float(jnp.linalg.norm(A @ x - b))
max_err_vs_ref = float(jnp.max(jnp.abs(x - x_ref)))

print(f"residual ||A x - b|| = {residual:.3e}")
print(f"max |x - x_ref|      = {max_err_vs_ref:.3e}")

# --- Known-value boolean (never hardcoded True) ------------------------------
RES_TOL = 1e-10
REF_TOL = 1e-10
match = bool((residual < RES_TOL) and (max_err_vs_ref < REF_TOL))

# x is float64 only if x64 propagated through the lineax solve
assert x.dtype == jnp.float64, f"solution dtype is {x.dtype}, expected float64"

print(f"match = {match}")
if not match:
    raise SystemExit(
        f"BLOCKER: lineax solve failed known-value check "
        f"(residual={residual:.3e} tol={RES_TOL}, "
        f"max_err_vs_ref={max_err_vs_ref:.3e} tol={REF_TOL})"
    )

print("OK: lineax linear_solve matches reference at float64 precision")
