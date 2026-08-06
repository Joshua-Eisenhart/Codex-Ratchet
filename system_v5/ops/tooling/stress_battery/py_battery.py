#!/usr/bin/env python3
"""Deep stress battery — Python side. Every probe performs a REAL operation with a
checkable result (positive), and where cheap a negative/boundary case. Receipt: JSON."""
import json, os, time, traceback, sys

os.environ.setdefault("JAX_ENABLE_X64", "1")
os.environ.setdefault("GEOMSTATS_BACKEND", "numpy")
RESULTS = {}

def probe(name):
    def deco(fn):
        def run():
            t0 = time.time()
            try:
                detail = fn()
                RESULTS[name] = {"status": "PASS", "sec": round(time.time()-t0, 2), "detail": detail}
            except Exception as e:
                RESULTS[name] = {"status": "FAIL", "sec": round(time.time()-t0, 2),
                                 "error": f"{type(e).__name__}: {str(e)[:200]}"}
        run.__name__ = name
        return run
    return deco

PROBES = []
def reg(name):
    def deco(fn):
        PROBES.append(probe(name)(fn)); return fn
    return deco

# ---------- gates ----------
@reg("z3_unsat_sat_flip")
def _():
    import z3
    x = z3.Int('x')
    s1 = z3.Solver(); s1.add(x > 0, x < 0)           # impossible
    s2 = z3.Solver(); s2.add(x > 0, x < 2)           # erased control
    assert s1.check() == z3.unsat and s2.check() == z3.sat
    return "UNSAT with contradiction, SAT when erased (flip real)"

@reg("cvc5_unsat_sat_flip")
def _():
    import cvc5
    def check(lo_gt, hi_lt):
        slv = cvc5.Solver(); slv.setLogic("QF_LIA")
        x = slv.mkConst(slv.getIntegerSort(), "x")
        slv.assertFormula(slv.mkTerm(cvc5.Kind.GT, x, slv.mkInteger(lo_gt)))
        slv.assertFormula(slv.mkTerm(cvc5.Kind.LT, x, slv.mkInteger(hi_lt)))
        return slv.checkSat()
    r1, r2 = check(0, 0), check(0, 2)
    assert r1.isUnsat() and r2.isSat()
    return "UNSAT/SAT flip real"

@reg("z3_cvc5_agreement")
def _():
    import z3, cvc5
    # same structural claim in both: no integer strictly between 1 and 2
    x = z3.Int('x'); s = z3.Solver(); s.add(x > 1, x < 2)
    z3_verdict = s.check() == z3.unsat
    slv = cvc5.Solver(); slv.setLogic("QF_LIA")
    y = slv.mkConst(slv.getIntegerSort(), "y")
    slv.assertFormula(slv.mkTerm(cvc5.Kind.GT, y, slv.mkInteger(1)))
    slv.assertFormula(slv.mkTerm(cvc5.Kind.LT, y, slv.mkInteger(2)))
    cvc5_verdict = slv.checkSat().isUnsat()
    assert z3_verdict and cvc5_verdict
    return "both solvers agree UNSAT on the same claim"

# ---------- symbolic ----------
@reg("sympy_exact_identity")
def _():
    import sympy as sp
    x = sp.Symbol('x')
    assert sp.simplify(sp.sin(x)**2 + sp.cos(x)**2 - 1) == 0
    assert sp.factorint(2**31 - 1) == {2147483647: 1}   # Mersenne prime, boundary
    return "trig identity exact; M31 primality"

# ---------- jax stack ----------
@reg("jax_x64_grad_vmap")
def _():
    import jax, jax.numpy as jnp
    assert jnp.array(1.0).dtype == jnp.float64, "x64 not active"
    g = jax.grad(lambda x: jnp.sin(x)**2)(0.3)
    expected = 2*jnp.sin(0.3)*jnp.cos(0.3)
    assert abs(g - expected) < 1e-12
    v = jax.vmap(lambda x: x**2)(jnp.arange(5.0))
    assert float(v[3]) == 9.0
    return f"x64 live; grad exact to {abs(float(g-expected)):.1e}; vmap ok"

@reg("diffrax_ode_solve")
def _():
    import diffrax, jax.numpy as jnp
    term = diffrax.ODETerm(lambda t, y, args: -y)
    sol = diffrax.diffeqsolve(term, diffrax.Dopri5(), t0=0, t1=1.0, dt0=0.01,
                              y0=jnp.array(1.0), saveat=diffrax.SaveAt(t1=True))
    err = abs(float(sol.ys[0]) - 2.718281828459045**-1)
    assert err < 1e-6
    return f"dy/dt=-y solved, |err|={err:.1e}"

@reg("optimistix_fixed_point")
def _():
    import optimistix as optx, jax.numpy as jnp
    # fixed point of cos: x* = 0.7390851332...
    sol = optx.fixed_point(lambda x, args: jnp.cos(x), optx.FixedPointIteration(rtol=1e-10, atol=1e-10),
                           jnp.array(1.0), max_steps=10000)
    err = abs(float(sol.value) - 0.7390851332151607)
    assert err < 1e-8
    return f"Dottie number found, |err|={err:.1e}"

@reg("lineax_linear_solve")
def _():
    import lineax as lx, jax.numpy as jnp
    A = jnp.array([[2.0, 1.0], [1.0, 3.0]]); b = jnp.array([3.0, 5.0])
    x = lx.linear_solve(lx.MatrixLinearOperator(A), b).value
    assert float(jnp.max(jnp.abs(A @ x - b))) < 1e-12
    return "2x2 solve exact"

@reg("ott_sinkhorn_transport")
def _():
    import jax.numpy as jnp
    from ott.geometry import pointcloud
    from ott.solvers.linear import sinkhorn
    from ott.problems.linear import linear_problem
    x = jnp.linspace(0, 1, 5).reshape(-1, 1); y = x + 0.5
    prob = linear_problem.LinearProblem(pointcloud.PointCloud(x, y))
    out = sinkhorn.Sinkhorn()(prob)
    assert bool(out.converged)
    return f"Sinkhorn converged, cost={float(out.reg_ot_cost):.4f}"

@reg("quimb_tn_contraction")
def _():
    import quimb.tensor as qtn
    mps = qtn.MPS_rand_state(6, bond_dim=4, seed=0)
    n = mps.H @ mps
    assert abs(float(n) - 1.0) < 1e-10
    return "6-site MPS norm contraction = 1"

@reg("cotengra_path")
def _():
    import cotengra as ctg, numpy as np
    arrays = [np.random.RandomState(i).randn(8, 8) for i in range(4)]
    out = ctg.einsum("ab,bc,cd,de->ae", *arrays)
    ref = arrays[0] @ arrays[1] @ arrays[2] @ arrays[3]
    assert np.max(np.abs(out - ref)) < 1e-10
    return "einsum chain contraction matches direct matmul"

@reg("netket_hilbert")
def _():
    import netket as nk
    hi = nk.hilbert.Spin(s=0.5, N=4)
    assert hi.n_states == 16
    return "4-spin Hilbert space, 16 states"

@reg("dynamiqs_sesolve")
def _():
    import dynamiqs as dq, jax.numpy as jnp
    H = dq.sigmaz()
    psi0 = dq.basis(2, 0)
    res = dq.sesolve(H, psi0, jnp.linspace(0, 1.0, 5))
    assert res.states.shape[0] == 5
    return "sigma_z evolution, 5 time points"

# ---------- torch stack ----------
@reg("torch_autograd_f64")
def _():
    import torch
    x = torch.tensor(0.3, dtype=torch.float64, requires_grad=True)
    y = torch.sin(x)**2; y.backward()
    expected = 2*torch.sin(torch.tensor(0.3, dtype=torch.float64))*torch.cos(torch.tensor(0.3, dtype=torch.float64))
    assert abs(float(x.grad - expected)) < 1e-14
    return "f64 autograd exact"

@reg("torch_geometric_message_passing")
def _():
    import torch
    from torch_geometric.nn import GCNConv
    from torch_geometric.data import Data
    edge_index = torch.tensor([[0, 1, 1, 2], [1, 0, 2, 1]], dtype=torch.long)
    x = torch.randn(3, 4, dtype=torch.float32)
    out = GCNConv(4, 2)(x, edge_index)
    assert out.shape == (3, 2)
    return "GCN forward on 3-node graph"

@reg("e3nn_irrep_tensor_product")
def _():
    import torch
    from e3nn import o3
    tp = o3.FullyConnectedTensorProduct("1x1o", "1x1o", "1x0e")
    out = tp(torch.randn(1, 3), torch.randn(1, 3))
    assert out.shape == (1, 1)
    return "1o x 1o -> 0e tensor product (invariant extraction)"

@reg("geomstats_sphere_geodesic")
def _():
    import numpy as np
    from geomstats.geometry.hypersphere import Hypersphere
    s2 = Hypersphere(dim=2)
    p, q = np.array([1.0, 0, 0]), np.array([0, 1.0, 0])
    d = s2.metric.dist(p, q)
    assert abs(d - np.pi/2) < 1e-10
    return f"great-circle distance = pi/2 exact ({d:.10f})"

# ---------- system id / topology / graphs ----------
@reg("pysindy_recover_ode")
def _():
    import numpy as np, pysindy as ps
    t = np.linspace(0, 5, 500); x = 3.0*np.exp(-2.0*t).reshape(-1, 1)
    model = ps.SINDy(); model.fit(x, t=t)
    coef = model.coefficients()
    assert abs(coef[0][1] + 2.0) < 0.01   # dx/dt = -2x recovered
    return f"recovered dx/dt = {coef[0][1]:.4f}·x (true -2)"

@reg("gudhi_persistence")
def _():
    import gudhi
    rc = gudhi.RipsComplex(points=[[0, 0], [1, 0], [0, 1], [1, 1]], max_edge_length=2.0)
    st = rc.create_simplex_tree(max_dimension=2)
    diag = st.persistence()
    h1 = [p for p in diag if p[0] == 1]
    assert len(h1) == 1   # the square has one 1-cycle
    return "unit square: one H1 class found"

@reg("rustworkx_dag")
def _():
    import rustworkx as rx
    g = rx.PyDiGraph()
    nodes = g.add_nodes_from(range(4))
    g.add_edges_from([(0, 1, None), (1, 2, None), (0, 3, None), (3, 2, None)])
    order = rx.topological_sort(g)
    assert list(order)[0] == 0 and rx.is_directed_acyclic_graph(g)
    return "4-node DAG toposort ok"

@reg("xgi_hypergraph")
def _():
    import xgi
    H = xgi.Hypergraph([[1, 2, 3], [2, 3, 4], [1, 4]])
    assert H.num_nodes == 4 and H.num_edges == 3
    return "3-edge hypergraph built"

# ---------- QIT crosscheck ----------
@reg("qutip_lindblad")
def _():
    import qutip as qt, numpy as np
    H = qt.sigmaz(); rho0 = qt.ket2dm((qt.basis(2,0)+qt.basis(2,1)).unit())
    res = qt.mesolve(H, rho0, np.linspace(0, 1, 5), c_ops=[0.5*qt.sigmam()])
    tr = res.states[-1].tr()
    assert abs(tr - 1.0) < 1e-9
    return f"Lindblad evolution trace-preserving ({tr:.12f})"

# ---------- control lane ----------
@reg("numba_jit")
def _():
    from numba import njit
    @njit(cache=False)
    def f(n):
        s = 0
        for i in range(n): s += i*i
        return s
    assert f(100) == 328350
    return "JIT sum of squares"

@reg("sklearn_fit")
def _():
    import numpy as np
    from sklearn.linear_model import LinearRegression
    X = np.arange(10).reshape(-1, 1); y = 3*X.ravel() + 1
    m = LinearRegression().fit(X, y)
    assert abs(m.coef_[0] - 3) < 1e-12
    return "exact linear recovery"

@reg("mpmath_precision")
def _():
    import mpmath as mp
    mp.mp.dps = 50
    v = mp.mpf(2)**mp.mpf('0.5')
    assert str(v).startswith("1.4142135623730950488016887242096980785696718753769")
    return "sqrt(2) to 50 digits"

# ---------- cross-engine integration ----------
@reg("dlpack_torch_to_jax_zero_copy")
def _():
    import torch, jax, jax.numpy as jnp
    t = torch.arange(6, dtype=torch.float64).reshape(2, 3)
    j = jnp.from_dlpack(t)
    assert j.dtype == jnp.float64 and float(j[1, 2]) == 5.0
    back = torch.from_dlpack(jax.device_put(j))
    assert back.shape == (2, 3) and float(back[0, 1]) == 1.0
    return "torch->jax->torch via DLPack, f64 preserved"

@reg("z3_bound_to_computed_value")
def _():
    # the load-bearing pattern: bind a MEASURED value into a solver claim + flip
    import z3, numpy as np
    measured = int(np.linalg.matrix_rank(np.array([[1, 2], [2, 4]])))   # rank 1
    r = z3.Int('r'); s = z3.Solver()
    s.add(r == measured, r == 2)          # claim: rank is 2 -> must be UNSAT
    s2 = z3.Solver(); s2.add(r == measured, r == 1)   # true claim -> SAT
    assert s.check() == z3.unsat and s2.check() == z3.sat
    return "solver bound to computed rank; false claim UNSAT, true claim SAT"

@reg("jax_torch_numerical_agreement")
def _():
    import torch, jax, jax.numpy as jnp, numpy as np
    A = np.random.RandomState(0).randn(8, 8)
    ev_j = np.sort(np.real(np.array(jnp.linalg.eigvals(jnp.array(A)))))
    ev_t = np.sort(np.real(torch.linalg.eigvals(torch.tensor(A)).numpy()))
    d = float(np.max(np.abs(ev_j - ev_t)))
    assert d < 1e-10
    return f"eigenvalue agreement jax vs torch: {d:.1e}"


@reg("kingdon_geometric_algebra")
def _():
    from kingdon import Algebra
    alg = Algebra(3)
    e1, e2 = alg.blades.e1, alg.blades.e2
    assert (e1*e2*e1*e2).e == -1 and (e1*e2 + e2*e1).e == 0
    return "Cl(3): (e1e2)^2=-1, anticommutation exact"

@reg("maude_t01_bracketing_flip")
def _():
    import maude
    maude.init()
    maude.input('fmod PA is sort Elt . ops a b c : -> Elt . op _*_ : Elt Elt -> Elt [assoc] . endfm')
    m = maude.getModule('PA')
    ta = m.parseTerm('(a * b) * c'); tb = m.parseTerm('a * (b * c)')
    ta.reduce(); tb.reduce()
    maude.input('fmod PN is sort Elt . ops a b c : -> Elt . op _*_ : Elt Elt -> Elt . endfm')
    n = maude.getModule('PN')
    tc = n.parseTerm('(a * b) * c'); td = n.parseTerm('a * (b * c)')
    tc.reduce(); td.reduce()
    assert str(ta) == str(tb) and str(tc) != str(td)
    return "bracketings identified WITH assoc, distinct WITHOUT - T01 flip native"

if __name__ == "__main__":
    for p in PROBES:
        p()
        r = RESULTS[p.__name__]
        print(f"{r['status']:4s} {p.__name__} ({r['sec']}s) {r.get('detail', r.get('error',''))}", flush=True)
    npass = sum(1 for r in RESULTS.values() if r["status"] == "PASS")
    out = {"battery": "python_sim_stack", "pass": npass, "fail": len(RESULTS)-npass, "results": RESULTS}
    path = os.environ.get(
        "CODEX_PY_BATTERY_RESULT_PATH",
        os.path.join(os.path.dirname(__file__), "py_battery_results.json"),
    )
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    json.dump(out, open(path, "w"), indent=1)
    print(f"=== {npass}/{len(RESULTS)} PASS -> {path}")
