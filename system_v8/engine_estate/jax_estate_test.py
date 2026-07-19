#!/usr/bin/env python3
"""JAX engine-estate test — system_v8.

Phase JAX of the three-engine estate probe. One engine stack loaded (JAX);
gates are code; promotion_allowed: false. NOT proof-level: goal is working
sims where packages do load-bearing work on real manifold content, at scale.

Lanes (scoped by the phase card):
  L13  vmap full 384-Bloch-state terrain census in one shot (jax vmap vs numpy loop, timed)
  L8   diffrax GKSL master-equation trajectory (amplitude damping, Bloch form) vs analytic
  L7   quimb + cotengra tensor-network contraction for a cut entropy (GHZ 12q, 6|6 cut)
  L12  jaxopt + lineax Fisher-metric linear system (dense SPD Fisher, batched RHS)

Smoke lanes (import-plus, so "working" is not import-only):
  e3nn_jax, ott, jraph, netket — one small load-bearing check each.

Receipt: results/jax/receipt.json
"""

import json
import os
import sys
import time
import traceback

import numpy as np

import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

RESULTS_DIR = "/Users/joshuaeisenhart/Codex-Ratchet/system_v8/engine_estate/results/jax"
os.makedirs(RESULTS_DIR, exist_ok=True)

CHECKS = []
TIMINGS = {}
BLOCKED = []


def check(name, passed, details):
    CHECKS.append({"name": name, "pass": bool(passed), "details": details})
    print(f"[{'PASS' if passed else 'FAIL'}] {name}: {details}")


def blocked(pkg, lane, err):
    BLOCKED.append({"package": pkg, "lane": lane, "error": err})
    print(f"[BLOCKED] {pkg} ({lane}): {err}")


def version_of(pkg):
    import importlib.metadata as md
    try:
        return md.version(pkg)
    except Exception:
        try:
            import importlib
            return getattr(importlib.import_module(pkg), "__version__", "unknown")
        except Exception:
            return "unknown"


# ----------------------------------------------------------------------------
# L13 — 384-Bloch-state terrain census, vmapped in one shot
# ----------------------------------------------------------------------------
def lane_l13():
    print("\n=== L13: 384-Bloch-state terrain census (jax.vmap, one shot) ===")
    # Deterministic 16 x 24 (theta, phi) grid -> 384 pure Bloch states.
    n_theta, n_phi = 16, 24
    thetas = np.pi * (np.arange(1, n_theta + 1) - 0.5) / n_theta
    phis = 2 * np.pi * np.arange(n_phi) / n_phi
    TH, PH = np.meshgrid(thetas, phis, indexing="ij")
    TH, PH = TH.ravel(), PH.ravel()          # 384 each
    n_states = TH.size
    assert n_states == 384

    # Census probe family: amplitude-damping channel sweep, 256 strengths g in [0,1],
    # per-state per-strength output von Neumann entropy + Bloch expectations.
    n_g = 256
    gs = np.linspace(0.0, 1.0, n_g)

    def rho_of(theta, phi):
        a = jnp.cos(theta / 2.0)
        b = jnp.exp(1j * phi) * jnp.sin(theta / 2.0)
        psi = jnp.array([a, b], dtype=jnp.complex128)
        return jnp.outer(psi, psi.conj())

    def damp(rho, g):
        K0 = jnp.array([[1.0, 0.0], [0.0, jnp.sqrt(1.0 - g)]], dtype=jnp.complex128)
        K1 = jnp.array([[0.0, jnp.sqrt(g)], [0.0, 0.0]], dtype=jnp.complex128)
        return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T

    def entropy(rho):
        ev = jnp.linalg.eigvalsh(rho)
        ev = jnp.clip(ev.real, 1e-30, 1.0)
        return -jnp.sum(ev * jnp.log(ev))

    def census_one(theta, phi):
        rho0 = rho_of(theta, phi)
        return jax.vmap(lambda g: entropy(damp(rho0, g)))(gs_j)

    gs_j = jnp.asarray(gs)

    census = jax.jit(jax.vmap(census_one))
    th_j, ph_j = jnp.asarray(TH), jnp.asarray(PH)

    # warmup + timed
    S = census(th_j, ph_j).block_until_ready()
    t_best = np.inf
    for _ in range(3):
        t0 = time.perf_counter()
        S = census(th_j, ph_j).block_until_ready()
        t_best = min(t_best, time.perf_counter() - t0)
    S = np.asarray(S)

    # numpy reference loop (same math), timed once
    t0 = time.perf_counter()
    S_np = np.empty((n_states, n_g))
    for i in range(n_states):
        a = np.cos(TH[i] / 2.0)
        b = np.exp(1j * PH[i]) * np.sin(TH[i] / 2.0)
        psi = np.array([a, b], dtype=np.complex128)
        rho0 = np.outer(psi, psi.conj())
        for j in range(n_g):
            g = gs[j]
            K0 = np.array([[1, 0], [0, np.sqrt(1 - g)]], dtype=np.complex128)
            K1 = np.array([[0, np.sqrt(g)], [0, 0]], dtype=np.complex128)
            r = K0 @ rho0 @ K0.conj().T + K1 @ rho0 @ K1.conj().T
            ev = np.clip(np.linalg.eigvalsh(r).real, 1e-30, 1.0)
            S_np[i, j] = -np.sum(ev * np.log(ev))
    t_numpy = time.perf_counter() - t0

    TIMINGS["L13_census_numpy_loop_s"] = t_numpy
    TIMINGS["L13_census_jax_vmap_s"] = t_best
    TIMINGS["L13_census_speedup_x"] = t_numpy / t_best
    TIMINGS["L13_census_shape"] = list(S.shape)

    check("L13.shape", S.shape == (384, 256), f"census shape {S.shape} == (384, 256)")
    check("L13.pure_at_g0", float(np.max(S[:, 0])) < 1e-12,
          f"g=0 column entropy max {np.max(S[:, 0]):.3e} (pure states)")
    check("L13.pure_at_g1", float(np.max(S[:, -1])) < 1e-12,
          f"g=1 column entropy max {np.max(S[:, -1]):.3e} (all damped to |0>)")
    check("L13.entropy_bound", float(np.max(S)) <= np.log(2) + 1e-12,
          f"max entropy {np.max(S):.6f} <= ln2 = {np.log(2):.6f}")
    d = float(np.max(np.abs(S - S_np)))
    check("L13.jax_vs_numpy", d < 1e-10, f"max |jax - numpy| = {d:.3e} over 98304 census cells")
    check("L13.vmap_speedup", t_numpy / t_best > 5.0,
          f"numpy loop {t_numpy:.3f}s vs vmap {t_best:.4f}s -> {t_numpy / t_best:.0f}x")


# ----------------------------------------------------------------------------
# L8 — diffrax GKSL trajectory (amplitude damping, Bloch vector form)
# ----------------------------------------------------------------------------
def lane_l8():
    print("\n=== L8: diffrax GKSL amplitude-damping trajectory, 512 gammas batched ===")
    import diffrax as dfx

    omega = 1.3
    T = 4.0
    ts = jnp.linspace(0.0, T, 81)
    n_gamma = 512
    gammas = jnp.linspace(0.05, 2.0, n_gamma)

    # GKSL for amplitude damping to |0> (z=+1), H = (omega/2) sigma_z, Bloch form:
    #   dx/dt = -omega*y - (gamma/2)*x
    #   dy/dt =  omega*x - (gamma/2)*y
    #   dz/dt = -gamma*(z - 1)
    r0 = jnp.array([1.0, 0.0, 0.0])  # |+> state

    def vf(t, r, gamma):
        x, y, z = r
        return jnp.array([-omega * y - 0.5 * gamma * x,
                          omega * x - 0.5 * gamma * y,
                          -gamma * (z - 1.0)])

    term = dfx.ODETerm(vf)
    solver = dfx.Tsit5()
    ctrl = dfx.PIDController(rtol=1e-10, atol=1e-12)

    def solve(gamma):
        sol = dfx.diffeqsolve(term, solver, t0=0.0, t1=T, dt0=0.01, y0=r0,
                              args=gamma, saveat=dfx.SaveAt(ts=ts),
                              stepsize_controller=ctrl, max_steps=100_000)
        return sol.ys

    solve_batch = jax.jit(jax.vmap(solve))
    ys = solve_batch(gammas).block_until_ready()
    t0 = time.perf_counter()
    ys = solve_batch(gammas).block_until_ready()
    TIMINGS["L8_diffrax_512traj_s"] = time.perf_counter() - t0
    ys = np.asarray(ys)  # (512, 81, 3)

    # analytic solution
    g = np.asarray(gammas)[:, None]
    t = np.asarray(ts)[None, :]
    x_an = np.exp(-0.5 * g * t) * np.cos(omega * t)
    y_an = np.exp(-0.5 * g * t) * np.sin(omega * t)
    z_an = 1.0 + (0.0 - 1.0) * np.exp(-g * t)
    err = max(float(np.max(np.abs(ys[:, :, 0] - x_an))),
              float(np.max(np.abs(ys[:, :, 1] - y_an))),
              float(np.max(np.abs(ys[:, :, 2] - z_an))))
    check("L8.gksl_vs_analytic", err < 1e-7,
          f"max |diffrax - analytic| = {err:.3e} over 512 gammas x 81 times x 3 components")

    # entropy law along trajectory: pure at t=0, mixed in between, repurifies as t->inf
    rnorm = np.linalg.norm(ys, axis=2)
    p = np.clip((1 + rnorm) / 2, 1e-15, 1.0)
    q = np.clip((1 - rnorm) / 2, 1e-15, 1.0)
    S = -(p * np.log(p) + q * np.log(q))
    check("L8.entropy_pure_start", float(np.max(S[:, 0])) < 1e-10,
          f"S(t=0) max {np.max(S[:, 0]):.3e}")
    check("L8.entropy_rises", float(np.min(np.max(S, axis=1))) > 0.05,
          f"every trajectory mixes: min over gammas of peak S = {np.min(np.max(S, axis=1)):.4f}")
    check("L8.repurification", float(S[-1, -1]) < 0.01,
          f"largest gamma repurifies toward |0>: S(T) = {S[-1, -1]:.3e}")


# ----------------------------------------------------------------------------
# L7 — quimb + cotengra: tensor-network contraction for cut entropy
# ----------------------------------------------------------------------------
def lane_l7():
    print("\n=== L7: quimb+cotengra TN contraction, GHZ-12 cut entropy ===")
    import quimb as qu
    import quimb.tensor as qtn
    import cotengra as ctg

    n = 12
    keep = list(range(6))

    # NOTE (honest finding, 2026-07-19): cotengra 0.8.0's own contraction
    # executor is broken in this env — passing a HyperOptimizer straight into
    # quimb's tn.contract raises IndexError in _parse_tensordot_axes_to_matmul,
    # and tree.contract(arrays) gets killed (exit 137). Load-bearing split:
    # cotengra does the contraction-tree SEARCH (path, cost, width), quimb
    # executes the contraction along that explicit path.
    def cut_entropy_tn(psi_dense):
        mps = qtn.MatrixProductState.from_dense(np.asarray(psi_dense).ravel(), dims=[2] * n)
        bra = mps.H.reindex({f"k{i}": f"b{i}" for i in keep})
        tn = qtn.TensorNetwork(list((mps & bra).tensors))
        kout = [f"k{i}" for i in keep] + [f"b{i}" for i in keep]
        inputs = [t.inds for t in tn]
        sizes = {i: d for t in tn for i, d in zip(t.inds, t.shape)}
        opt = ctg.HyperOptimizer(methods=["greedy"], max_repeats=8,
                                 parallel=False, progbar=False)
        tree = opt.search(inputs, tuple(kout), sizes)
        rho_t = tn.contract(output_inds=kout, optimize=tree.get_path())
        rho = rho_t.to_dense([f"k{i}" for i in keep], [f"b{i}" for i in keep])
        ev = np.clip(np.linalg.eigvalsh(rho).real, 1e-30, 1.0)
        return ev, float(-np.sum(ev * np.log(ev))), tree

    t0 = time.perf_counter()
    ev, S_ghz, tree = cut_entropy_tn(qu.ghz_state(n))
    TIMINGS["L7_tn_contract_ghz_s"] = time.perf_counter() - t0

    top2 = np.sort(ev)[-2:]
    check("L7.ghz_schmidt", float(np.max(np.abs(top2 - 0.5))) < 1e-12
          and float(np.sort(ev)[-3]) < 1e-12,
          f"rho_A(6|6) eigenvalues: two at {top2} rest < 1e-12")
    check("L7.ghz_cut_entropy", abs(S_ghz - np.log(2)) < 1e-10,
          f"S = {S_ghz:.12f} vs ln2 = {np.log(2):.12f}")

    check("L7.cotengra_load_bearing",
          tree.contraction_cost() > 0 and len(tree.get_path()) == 23,
          f"HyperOptimizer tree: cost {tree.contraction_cost():.3g}, "
          f"width {tree.contraction_width():.3g}, path length {len(tree.get_path())} "
          "(cotengra searched the tree; quimb executed along its path — "
          "cotengra's own executor is broken in this env, see lane note)")

    psi_prod = qu.kron(*([qu.plus()] * n))
    _, S_prod, _ = cut_entropy_tn(psi_prod)
    check("L7.product_control", abs(S_prod) < 1e-10,
          f"product |+>^12 control: S = {S_prod:.3e}")


# ----------------------------------------------------------------------------
# L12 — jaxopt + lineax: Fisher-metric linear system, batched
# ----------------------------------------------------------------------------
def lane_l12():
    print("\n=== L12: Fisher-metric linear system (lineax + jaxopt), 256 RHS batched ===")
    import lineax as lx
    from jaxopt import linear_solve as jls

    # Fisher metric of a smooth probability model p(theta): G = J^T diag(1/p) J,
    # 512 outcomes, 128 parameters -> dense SPD 128x128.
    rng = np.random.default_rng(20260719)
    n_out, n_par, n_rhs = 512, 128, 256
    logits = rng.normal(size=n_out)
    W = rng.normal(size=(n_out, n_par)) / np.sqrt(n_par)

    logits_j = jnp.asarray(logits)
    W_j = jnp.asarray(W)

    def probs(theta):
        return jax.nn.softmax(logits_j + W_j @ theta)

    theta0 = jnp.zeros(n_par)
    p = probs(theta0)
    J = jax.jacfwd(probs)(theta0)            # (512, 128)
    G = J.T @ (J / p[:, None])               # Fisher metric at theta0
    G = 0.5 * (G + G.T) + 1e-10 * jnp.eye(n_par)

    B = jnp.asarray(rng.normal(size=(n_rhs, n_par)))

    op = lx.MatrixLinearOperator(G, lx.positive_semidefinite_tag)
    solve_chol = jax.jit(jax.vmap(lambda b: lx.linear_solve(op, b, solver=lx.Cholesky()).value))
    solve_cg_jaxopt = jax.jit(jax.vmap(
        lambda b: jls.solve_cg(lambda x: G @ x, b, tol=1e-12, maxiter=2000)))

    X_lx = solve_chol(B).block_until_ready()
    t0 = time.perf_counter()
    X_lx = solve_chol(B).block_until_ready()
    TIMINGS["L12_lineax_chol_256rhs_s"] = time.perf_counter() - t0

    X_jo = solve_cg_jaxopt(B).block_until_ready()
    t0 = time.perf_counter()
    X_jo = solve_cg_jaxopt(B).block_until_ready()
    TIMINGS["L12_jaxopt_cg_256rhs_s"] = time.perf_counter() - t0

    # numpy loop reference, timed
    Gn, Bn = np.asarray(G), np.asarray(B)
    t0 = time.perf_counter()
    X_np = np.empty_like(Bn)
    for i in range(n_rhs):
        X_np[i] = np.linalg.solve(Gn, Bn[i])
    TIMINGS["L12_numpy_loop_256rhs_s"] = time.perf_counter() - t0

    res = float(np.max(np.linalg.norm(np.asarray(X_lx) @ Gn.T - Bn, axis=1)
                       / np.linalg.norm(Bn, axis=1)))
    check("L12.lineax_residual", res < 1e-8,
          f"max relative residual ||Gx-b||/||b|| = {res:.3e} over 256 RHS")
    d1 = float(np.max(np.abs(np.asarray(X_lx) - X_np)))
    check("L12.lineax_vs_numpy", d1 < 1e-6, f"max |lineax - numpy.solve| = {d1:.3e}")
    d2 = float(np.max(np.abs(np.asarray(X_jo) - X_np)))
    check("L12.jaxopt_vs_numpy", d2 < 1e-5, f"max |jaxopt CG - numpy.solve| = {d2:.3e}")
    check("L12.fisher_spd", bool(np.all(np.linalg.eigvalsh(Gn) > 0)),
          f"Fisher metric eigenvalues in [{np.linalg.eigvalsh(Gn).min():.3e}, "
          f"{np.linalg.eigvalsh(Gn).max():.3e}] (SPD)")


# ----------------------------------------------------------------------------
# Smoke lanes — small load-bearing checks so "working" is not import-only
# ----------------------------------------------------------------------------
def lane_smoke_e3nn():
    import e3nn_jax as e3nn
    v = jnp.array([0.3, -1.1, 0.7])
    # random rotation via matrix exponential of antisymmetric generator
    A = jnp.array([[0.0, 0.4, -0.2], [-0.4, 0.0, 0.9], [0.2, -0.9, 0.0]])
    R = jax.scipy.linalg.expm(A)
    y1 = e3nn.spherical_harmonics("2e", v, normalize=True).array
    y2 = e3nn.spherical_harmonics("2e", R @ v, normalize=True).array
    d = float(abs(jnp.linalg.norm(y1) - jnp.linalg.norm(y2)))
    check("smoke.e3nn_jax", d < 1e-12 and y1.shape == (5,),
          f"l=2 SH norm rotation-invariant: |d| = {d:.3e}, shape {y1.shape}")


def lane_smoke_ott():
    from ott.geometry import pointcloud
    from ott.problems.linear import linear_problem
    from ott.solvers.linear import sinkhorn
    rng = np.random.default_rng(7)
    X = jnp.asarray(rng.normal(size=(64, 3)))
    shift = jnp.array([2.0, 0.0, 0.0])
    geom = pointcloud.PointCloud(X, X + shift, epsilon=0.05)
    out = sinkhorn.Sinkhorn(max_iterations=20000, threshold=1e-4)(
        linear_problem.LinearProblem(geom))
    cost = float(jnp.sum(out.matrix * geom.cost_matrix))
    check("smoke.ott", bool(out.converged) and abs(cost - 4.0) < 0.05,
          f"Sinkhorn converged={bool(out.converged)} in {int(out.n_iters)} iters, "
          f"transport cost {cost:.4f} vs |shift|^2 = 4.0")


def lane_smoke_jraph():
    import jraph
    senders = jnp.array([0, 1, 2, 3, 1, 2, 3, 0])
    receivers = jnp.array([1, 2, 3, 0, 0, 1, 2, 3])
    feats = jnp.asarray(np.random.default_rng(3).normal(size=(4, 5)))
    agg = jraph.segment_sum(feats[senders], receivers, num_segments=4)
    A = np.zeros((4, 4))
    for s, r in zip(np.asarray(senders), np.asarray(receivers)):
        A[r, s] += 1.0
    d = float(np.max(np.abs(np.asarray(agg) - A @ np.asarray(feats))))
    check("smoke.jraph", d < 1e-12, f"message-passing sum == A @ X: max diff {d:.3e}")


def lane_smoke_netket():
    import netket as nk
    g = nk.graph.Chain(length=4, pbc=True)
    hi = nk.hilbert.Spin(s=1 / 2, N=4)
    H = nk.operator.Ising(hilbert=hi, graph=g, h=1.0)
    e_dense = float(np.linalg.eigvalsh(H.to_dense()).min())
    e_lanc = float(nk.exact.lanczos_ed(H, k=1)[0])
    check("smoke.netket", abs(e_dense - e_lanc) < 1e-8,
          f"TFIM N=4 pbc h=1: dense E0 {e_dense:.10f} == lanczos {e_lanc:.10f}")


def main():
    lanes = [
        ("jax", "L13_census", lane_l13),
        ("diffrax", "L8_gksl", lane_l8),
        ("quimb+cotengra", "L7_cut_entropy", lane_l7),
        ("lineax+jaxopt", "L12_fisher", lane_l12),
        ("e3nn_jax", "smoke", lane_smoke_e3nn),
        ("ott", "smoke", lane_smoke_ott),
        ("jraph", "smoke", lane_smoke_jraph),
        ("netket", "smoke", lane_smoke_netket),
    ]
    for pkg, lane, fn in lanes:
        try:
            fn()
        except Exception as e:
            traceback.print_exc()
            blocked(pkg, lane, f"{type(e).__name__}: {e}"[:400])

    versions = {p: version_of(p) for p in
                ["jax", "jaxlib", "diffrax", "quimb", "cotengra", "e3nn-jax",
                 "ott-jax", "jaxopt", "lineax", "jraph", "netket", "numpy"]}

    n_pass = sum(c["pass"] for c in CHECKS)
    receipt = {
        "engine": "jax",
        "phase": "system_v8 engine_estate JAX phase",
        "date": "2026-07-19",
        "python": sys.version,
        "interpreter": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
        "promotion_allowed": False,
        "claim_ceiling": "working-sim estate probe; not canonical, not proof-level",
        "versions": versions,
        "checks": CHECKS,
        "checks_passed": n_pass,
        "checks_total": len(CHECKS),
        "blocked": BLOCKED,
        "timings": TIMINGS,
    }
    path = os.path.join(RESULTS_DIR, "receipt.json")
    with open(path, "w") as f:
        json.dump(receipt, f, indent=2)
    print(f"\nreceipt: {path}")
    print(f"checks: {n_pass}/{len(CHECKS)} pass, blocked: {len(BLOCKED)}")


if __name__ == "__main__":
    main()
