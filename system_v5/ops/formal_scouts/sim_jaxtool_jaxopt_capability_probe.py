import jax
jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import jaxopt

# classification: diagnostic_only
# Tool-capability check for jaxopt under the codex-ratchet jax env.
# No validator gate. ONE real operation: minimize a convex quadratic
# whose analytic minimizer is known, then compare to the known value.

classification = "diagnostic_only"


def main():
    # --- x64 honored check (live) -------------------------------------
    x_probe = jnp.array([1.0, 2.0, 3.0])
    rtype = str(x_probe.dtype)
    assert x_probe.dtype == jnp.float64, f"x64 NOT honored: real dtype is {rtype}"

    c_probe = jnp.array([1.0 + 2.0j])
    cdtype = str(c_probe.dtype)
    assert c_probe.dtype == jnp.complex128, f"x64 NOT honored: complex dtype is {cdtype}"

    # --- REAL operation: convex quadratic minimization ----------------
    # f(x) = sum((x - b)^2), analytic minimizer x* = b.
    b = jnp.array([3.0, -1.5, 0.0, 7.25, -4.0])

    def f(x):
        return jnp.sum((x - b) ** 2)

    x0 = jnp.zeros_like(b)

    # GradientDescent solve
    gd = jaxopt.GradientDescent(fun=f, stepsize=0.1, maxiter=2000, tol=1e-12)
    gd_res = gd.run(x0)
    x_gd = gd_res.params

    # LBFGS solve (independent solver, same problem)
    lbfgs = jaxopt.LBFGS(fun=f, maxiter=500, tol=1e-12)
    lbfgs_res = lbfgs.run(x0)
    x_lbfgs = lbfgs_res.params

    err_gd = float(jnp.max(jnp.abs(x_gd - b)))
    err_lbfgs = float(jnp.max(jnp.abs(x_lbfgs - b)))
    max_err = max(err_gd, err_lbfgs)

    # KNOWN/analytic value: x* == b. Tolerance per task: < 1e-5.
    tol = 1e-5
    match = bool(max_err < tol)  # never hardcoded True

    # Confirm solver output also carries float64 (x64 through the solve).
    solve_dtype = str(x_gd.dtype)
    assert x_gd.dtype == jnp.float64, f"solver lost x64: {solve_dtype}"

    print("classification:", classification)
    print("jaxopt solvers: GradientDescent, LBFGS")
    print("rtype:", rtype, "cdtype:", cdtype, "solve_dtype:", solve_dtype)
    print("b (known x*):", [float(v) for v in b])
    print("x_gd:        ", [float(v) for v in x_gd])
    print("x_lbfgs:     ", [float(v) for v in x_lbfgs])
    print("err_gd:", err_gd, "err_lbfgs:", err_lbfgs)
    print("max_err:", max_err, "tol:", tol)
    print("invariant: argmin sum((x-b)^2) == b")
    print("match:", match)

    assert match, f"jaxopt minimizer did not reach known value b; max_err={max_err}"
    return match


if __name__ == "__main__":
    ok = main()
    print("PROBE_OK" if ok else "PROBE_FAIL")
