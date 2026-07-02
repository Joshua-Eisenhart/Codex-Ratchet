import jax; jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

# Tool-capability probe: ott-jax (Optimal Transport Tools in JAX)
# Intended role: optimal transport for shell-distribution comparison.
# Operation: solve an entropic OT (Sinkhorn) between two small discrete
#   distributions a, b over point clouds. KNOWN: the recovered transport
#   plan P has row-marginals == a and col-marginals == b (max marginal
#   violation < 1e-4) and cost >= 0. Verify x64 (float64) is honored.
# classification = "diagnostic_only"  (no validator gate; tool-capability check)

classification = "diagnostic_only"

from ott.geometry import pointcloud
from ott.problems.linear import linear_problem
from ott.solvers.linear import sinkhorn


def main():
    # --- x64 honored? -------------------------------------------------------
    probe_arr = jnp.asarray([1.0, 2.0, 3.0])
    rtype = str(probe_arr.dtype)
    cdtype = str((probe_arr + 1j * probe_arr).dtype)
    assert probe_arr.dtype == jnp.float64, f"x64 NOT honored: float dtype is {probe_arr.dtype}"
    assert (probe_arr + 1j * probe_arr).dtype == jnp.complex128, f"x64 NOT honored: complex dtype is {cdtype}"

    # --- two small discrete distributions over point clouds -----------------
    # Source cloud x (3 points in 2D), target cloud y (4 points in 2D).
    x = jnp.asarray([[0.0, 0.0],
                     [1.0, 0.0],
                     [0.0, 1.0]])
    y = jnp.asarray([[1.0, 1.0],
                     [2.0, 0.0],
                     [0.0, 2.0],
                     [1.5, 1.5]])

    # Non-uniform mass distributions (must sum to 1).
    a = jnp.asarray([0.5, 0.2, 0.3])
    b = jnp.asarray([0.1, 0.4, 0.25, 0.25])
    assert abs(float(a.sum()) - 1.0) < 1e-12
    assert abs(float(b.sum()) - 1.0) < 1e-12

    # --- solve entropic OT (Sinkhorn) ---------------------------------------
    geom = pointcloud.PointCloud(x, y, epsilon=1e-2)
    prob = linear_problem.LinearProblem(geom, a=a, b=b)
    solver = sinkhorn.Sinkhorn(threshold=1e-6, max_iterations=5000)
    out = solver(prob)

    assert bool(out.converged), "Sinkhorn did not converge"

    # Recover the transport plan P and its marginals.
    P = out.matrix  # shape (3, 4)
    assert str(P.dtype) == "float64", f"transport plan dtype not float64: {P.dtype}"

    row_marg = P.sum(axis=1)   # should equal a
    col_marg = P.sum(axis=0)   # should equal b

    row_viol = float(jnp.max(jnp.abs(row_marg - a)))
    col_viol = float(jnp.max(jnp.abs(col_marg - b)))
    max_marg_viol = max(row_viol, col_viol)

    # Transport cost (entropic regularized OT cost). For PSD ground cost it is >= 0.
    cost = float(out.reg_ot_cost)
    transport_cost = float(jnp.sum(P * geom.cost_matrix))

    # --- KNOWN-value check (boolean, never hardcoded) -----------------------
    KNOWN_marg_tol = 1e-4
    marg_ok = max_marg_viol < KNOWN_marg_tol
    cost_ok = transport_cost >= 0.0
    match = bool(marg_ok and cost_ok)

    invariant = ("Sinkhorn plan marginals match (a, b) with max violation < 1e-4 "
                 "AND transport cost >= 0")
    computed = (f"max_marginal_violation={max_marg_viol:.3e} (row={row_viol:.3e}, "
                f"col={col_viol:.3e}), transport_cost={transport_cost:.6f}, "
                f"reg_ot_cost={cost:.6f}")
    known = "max_marginal_violation < 1e-4 and transport_cost >= 0"

    print(f"rtype={rtype} cdtype={cdtype}")
    print(f"P.dtype={P.dtype} shape={P.shape}")
    print(f"row_marginals={row_marg}")
    print(f"a            ={a}")
    print(f"col_marginals={col_marg}")
    print(f"b            ={b}")
    print(f"invariant: {invariant}")
    print(f"computed:  {computed}")
    print(f"known:     {known}")
    print(f"match:     {match}")

    if not match:
        print("STATUS=blocker")
        raise SystemExit(1)

    print("STATUS=works")


if __name__ == "__main__":
    main()
