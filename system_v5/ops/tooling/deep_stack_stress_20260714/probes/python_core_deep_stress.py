#!/usr/bin/env python3
"""Deep, non-promoting integration stress receipt for the Python sim stack.

This runner is deliberately diagnostic.  A red tool row is evidence, not a
reason to hide the receipt or relax a gate.  The process exits 0 after writing
a structurally valid receipt even when tool cases are red; exit 2 is reserved
for a broken harness/roster/output boundary.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import shlex
import sys
import tempfile
import time
import traceback
import warnings
from pathlib import Path
from typing import Any, Callable

from python_compat import install_dynamax_xla_alias, jaxga_static_argnames_compat


# These must be fixed before importing JAX/Geomstats/Numba-backed packages.
os.environ.setdefault("JAX_ENABLE_X64", "1")
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("NUMBA_CACHE_DIR", "/private/tmp/codex_numba_cache")
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")


CURRENT_CORE = (
    "blackjax", "chex", "clifford", "cotengra", "cvc5", "cvxpylayers",
    "diffrax", "dynamiqs", "e3nn", "e3nn_jax", "equinox", "flax",
    "geomstats", "gudhi", "haiku", "igraph", "jax", "jaxlib", "jaxopt",
    "jaxtyping", "jraph", "kahypar", "kanren", "lineax", "netket",
    "networkx", "numpy", "numpyro", "opt_einsum", "optax", "optimistix",
    "orbax", "ott", "pandas", "pysindy", "quimb", "qutip", "qutip_jax",
    "rustworkx", "scipy", "sympy", "toponetx", "torch", "torch_ga",
    "torch_geometric", "torchdiffeq", "torchode", "xgi", "xitorch", "z3",
)
CURRENT_OPTIONAL_AVAILABLE = (
    "autoray", "dynamax", "flowMC", "jax_dataclasses", "jaxga", "jaxlie",
    "pymc", "scikit-learn",
)
ADMITTED_QUARANTINED = ("pykoopman",)
LEGACY_UNCLASSIFIED = (
    "ribs", "deap", "evotorch", "datasketch", "pymoo", "hypothesis",
    "optuna", "hdbscan", "umap",
)

IMPORT_NAMES = {
    "scikit-learn": "sklearn",
}
DIST_NAMES = {
    "e3nn_jax": "e3nn-jax",
    "flowMC": "flowMC",
    "haiku": "dm-haiku",
    "igraph": "igraph",
    "jax_dataclasses": "jax-dataclasses",
    "qutip_jax": "qutip-jax",
    "scikit-learn": "scikit-learn",
    "torch_ga": "torch-ga",
    "torch_geometric": "torch-geometric",
}

REPO_ROOT = Path(__file__).resolve().parents[5]
CASE_NAMES = ("positive", "negative", "boundary", "stress")
CaseFn = Callable[[], Any]


@dataclasses.dataclass(frozen=True)
class Spec:
    tool: str
    qualified_api: str
    adjacent_edge: str
    representative_fixture: str
    demotion_condition: str
    integration_role: str
    support_bucket: bool
    control_bucket: bool
    factory: Callable[[], dict[str, CaseFn]]


SPECS: dict[str, Spec] = {}


def register(
    tool: str,
    api: str,
    edge: str,
    fixture: str,
    demotion: str,
    *,
    role: str = "claim_candidate",
    support: bool = False,
    control: bool = True,
):
    def decorate(factory: Callable[[], dict[str, CaseFn]]):
        SPECS[tool] = Spec(
            tool, api, edge, fixture, demotion, role, support, control, factory
        )
        return factory
    return decorate


def four(pos: CaseFn, neg: CaseFn, boundary: CaseFn, stress: CaseFn):
    return {"positive": pos, "negative": neg, "boundary": boundary, "stress": stress}


def checked(condition: Any, detail: Any) -> Any:
    if not bool(condition):
        raise AssertionError(detail)
    return detail


def expect_raises(exc_types: type[BaseException] | tuple[type[BaseException], ...], fn: CaseFn):
    try:
        fn()
    except exc_types as exc:
        return {"expected_exception": type(exc).__name__, "message": str(exc)[:240]}
    raise AssertionError(f"expected {exc_types!r} was not raised")


def jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    if hasattr(value, "item"):
        try:
            return jsonable(value.item())
        except Exception:
            pass
    if hasattr(value, "tolist"):
        try:
            return jsonable(value.tolist())
        except Exception:
            pass
    return repr(value)


def run_case(fn: CaseFn) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        detail = fn()
        return {
            "pass": True,
            "detail": jsonable(detail),
            "error": None,
            "duration_seconds": round(time.perf_counter() - started, 6),
        }
    except BaseException as exc:  # preserve native-extension/API failures as red evidence
        return {
            "pass": False,
            "detail": None,
            "error": {
                "type": type(exc).__name__,
                "message": str(exc)[:1000],
                "traceback": traceback.format_exc(limit=8),
            },
            "duration_seconds": round(time.perf_counter() - started, 6),
        }


def load_repo_module(relative: str, label: str):
    """Import a side-effect-safe capability module without calling its main()."""
    path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(label, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def package_metadata(tool: str) -> dict[str, Any]:
    import_name = IMPORT_NAMES.get(tool, tool)
    module = importlib.import_module(import_name)
    dist = DIST_NAMES.get(tool)
    if dist is None:
        candidates = importlib.metadata.packages_distributions().get(import_name, [])
        dist = candidates[0] if candidates else tool
    try:
        version = importlib.metadata.version(dist)
    except importlib.metadata.PackageNotFoundError:
        version = getattr(module, "__version__", None)
    return {
        "import_name": import_name,
        "distribution": dist,
        "version": version,
        "module_file": getattr(module, "__file__", None),
    }


def membership(tool: str) -> str:
    if tool in CURRENT_CORE:
        return "current_core"
    if tool in CURRENT_OPTIONAL_AVAILABLE:
        return "current_optional_available"
    if tool in ADMITTED_QUARANTINED:
        return "admitted_quarantined_surface"
    return "legacy_unclassified"


# ---- Current core: JAX, differentiable numerics, QIT, and tensor surfaces ----


@register("blackjax", "blackjax.rmh.init/step", "JAX PRNG and autodiff -> MCMC transition", "2D standard-normal RMH chain", "demote if initialization, transition, non-finite control, or repeated chain execution fails")
def probe_blackjax():
    import blackjax
    import jax
    import jax.numpy as jnp

    def algorithm(logp=lambda x: -0.5 * jnp.sum(x * x)):
        proposal=lambda key,x: x + 0.2 * jax.random.normal(key,shape=x.shape)
        return blackjax.rmh(logp, proposal)

    def pos():
        alg = algorithm(); state = alg.init(jnp.array([0.2, -0.1])); state, info = alg.step(jax.random.PRNGKey(1), state)
        return checked(bool(jnp.all(jnp.isfinite(state.position))), {"position": state.position, "accepted": getattr(info, "is_accepted", None)})
    def neg():
        state = algorithm(lambda x: jnp.asarray(jnp.nan)).init(jnp.zeros(2))
        return checked(not bool(jnp.isfinite(state.logdensity)), {"nonfinite_logdensity_detected": True})
    def boundary():
        state = algorithm().init(jnp.zeros(2)); return checked(float(state.logdensity) == 0.0, {"zero_logdensity": float(state.logdensity)})
    def stress():
        alg = algorithm(); state = alg.init(jnp.zeros(2)); key = jax.random.PRNGKey(7)
        accepted = 0
        for _ in range(32):
            key, sub = jax.random.split(key); state, info = alg.step(sub, state); accepted += int(getattr(info, "is_accepted", False))
        return checked(bool(jnp.all(jnp.isfinite(state.position))), {"steps": 32, "accepted": accepted})
    return four(pos, neg, boundary, stress)


@register("chex", "chex.assert_trees_all_close/assert_shape", "JAX pytrees -> runtime invariant controls", "nested JAX array assertions", "demote to import-only if assertions do not accept valid trees and reject drift", role="control_only", support=True)
def probe_chex():
    import chex
    import jax.numpy as jnp
    return four(
        lambda: (chex.assert_trees_all_close({"x": jnp.ones(3)}, {"x": jnp.ones(3)}), {"tree_close": True})[1],
        lambda: expect_raises(AssertionError, lambda: chex.assert_trees_all_close(jnp.zeros(2), jnp.ones(2))),
        lambda: (chex.assert_shape(jnp.zeros((0, 3)), (0, 3)), {"empty_shape": [0, 3]})[1],
        lambda: (chex.assert_trees_all_close([jnp.arange(32.0)] * 64, [jnp.arange(32.0)] * 64), {"leaves": 64})[1],
    )


@register("clifford", "clifford.Cl and MultiVector geometric product", "NumPy coefficients -> geometric algebra witnesses", "Cl(2,0) basis and rotor identities", "demote if metric signs, bivector square, scalar boundary, or repeated products fail")
def probe_clifford():
    import clifford
    layout, blades = clifford.Cl(2)
    e1, e2 = blades["e1"], blades["e2"]
    scalar = lambda x: float(x[()])
    return four(
        lambda: checked(abs(scalar(e1 * e1) - 1.0) < 1e-12, {"e1_squared": scalar(e1 * e1)}),
        lambda: checked(abs(scalar(e1 * e2 + e2 * e1)) < 1e-12, {"anticommutator_scalar": scalar(e1 * e2 + e2 * e1)}),
        lambda: checked(abs((0 * e1).value).max() == 0.0, {"zero_multivector": True}),
        lambda: checked(abs(scalar((e1 * e2) * (e1 * e2)) + 1.0) < 1e-12, {"bivector_square": scalar((e1 * e2) ** 2), "repetitions": 256 if all(scalar(e1*e1) == 1.0 for _ in range(256)) else 0}),
    )


@register("cotengra", "cotengra.array_contract/HyperOptimizer", "tensor network indices -> contraction path -> NumPy result", "matrix-chain contraction versus einsum", "demote if optimized contraction disagrees, accepts incompatible legs, mishandles scalar boundary, or fails chain stress")
def probe_cotengra():
    import cotengra as ctg
    import numpy as np
    opt = ctg.HyperOptimizer(max_repeats=4, parallel=False, progbar=False)
    def contract(arrays, inputs, output): return ctg.array_contract(arrays, inputs, output, optimize=opt)
    return four(
        lambda: checked(np.allclose(contract([np.arange(6.).reshape(2,3), np.ones((3,2))], [(0,1),(1,2)], (0,2)), np.einsum("ab,bc->ac", np.arange(6.).reshape(2,3), np.ones((3,2)))), {"optimized_matches_einsum": True}),
        lambda: expect_raises((ValueError, IndexError), lambda: contract([np.ones((2,3)), np.ones((4,2))], [(0,1),(1,2)], (0,2))),
        lambda: checked(float(contract([np.asarray(3.0), np.asarray(2.0)], [(),()], ())) == 6.0, {"scalar": 6.0}),
        lambda: checked(np.asarray(contract([np.ones((4,4)) for _ in range(8)], [(i,i+1) for i in range(8)], (0,8))).shape == (4,4), {"tensors": 8, "bond": 4}),
    )


def _cvc5_solver(assertions: Callable[[Any, Any, Any], None]):
    import cvc5
    from cvc5 import Kind
    solver = cvc5.Solver(); solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort(); x = solver.mkConst(integer, "x")
    assertions(solver, x, Kind)
    return solver.checkSat()


@register("cvc5", "cvc5.Solver.checkSat", "integer constraints -> independent SMT decision", "SAT/UNSAT linear-integer controls", "demote if solver confuses SAT and UNSAT or fails empty/stress formulas")
def probe_cvc5():
    import cvc5
    return four(
        lambda: checked(_cvc5_solver(lambda s,x,K: s.assertFormula(s.mkTerm(K.GT, x, s.mkInteger(2)))).isSat(), {"sat": True}),
        lambda: checked(_cvc5_solver(lambda s,x,K: [s.assertFormula(s.mkTerm(K.GT,x,s.mkInteger(2))), s.assertFormula(s.mkTerm(K.LT,x,s.mkInteger(0)))]).isUnsat(), {"unsat_control": True}),
        lambda: checked(_cvc5_solver(lambda s,x,K: None).isSat(), {"empty_formula_sat": True}),
        lambda: checked(_cvc5_solver(lambda s,x,K: [s.assertFormula(s.mkTerm(K.GEQ,x,s.mkInteger(i))) for i in range(64)]).isSat(), {"constraints": 64}),
    )


@register("cvxpylayers", "cvxpylayers.torch.CvxpyLayer", "CVXPY DPP problem -> Torch differentiable solve", "projection onto nonnegative orthant", "demote if solve/gradient, invalid-shape rejection, zero boundary, or batch solve fails")
def probe_cvxpylayers():
    import cvxpy as cp
    import torch
    from cvxpylayers.torch import CvxpyLayer
    x = cp.Variable(2); p = cp.Parameter(2)
    layer = CvxpyLayer(cp.Problem(cp.Minimize(cp.sum_squares(x-p)), [x >= 0]), parameters=[p], variables=[x])
    def solve(v): return layer(v)[0]
    def pos():
        p0 = torch.tensor([-1., 2.], requires_grad=True); y = solve(p0); y.sum().backward()
        return checked(torch.allclose(y, torch.tensor([0.,2.],dtype=y.dtype), atol=1e-4) and p0.grad is not None, {"solution": y, "gradient": p0.grad})
    return four(pos, lambda: expect_raises(Exception, lambda: solve(torch.ones(3))), lambda: checked(torch.allclose(solve(torch.zeros(2)), torch.zeros(2,dtype=solve(torch.zeros(2)).dtype), atol=1e-5), {"zero": True}), lambda: checked(solve(torch.randn(24,2)).shape == (24,2), {"batch": 24}))


@register("diffrax", "diffrax.diffeqsolve/Dopri5", "JAX vector field -> adaptive ODE integration", "exponential decay with analytic endpoint", "demote if analytic solve, wrong-sign control, zero fixed state, or vmapped endpoints fail")
def probe_diffrax():
    import diffrax
    import jax
    import jax.numpy as jnp
    def solve(rate, y0):
        term = diffrax.ODETerm(lambda t,y,args: rate*y)
        return diffrax.diffeqsolve(term, diffrax.Dopri5(), t0=0., t1=1., dt0=.05, y0=jnp.asarray(y0), saveat=diffrax.SaveAt(t1=True)).ys[0]
    return four(
        lambda: checked(abs(float(solve(-1., 1.)) - float(jnp.exp(-1.))) < 2e-5, {"endpoint": solve(-1.,1.)}),
        lambda: checked(float(solve(1.,1.)) > 2.7 and float(solve(-1.,1.)) < 0.38, {"sign_control": True}),
        lambda: checked(float(solve(-3.,0.)) == 0.0, {"zero_fixed": True}),
        lambda: checked(jax.vmap(lambda y: solve(-.5,y))(jnp.arange(1.,33.)).shape == (32,), {"vmapped": 32}),
    )


@register("dynamiqs", "dynamiqs.sesolve", "JAX quantum arrays -> Schrödinger evolution", "single-qubit Pauli-X evolution", "demote if norm/unitary evolution, non-Hermitian control, zero-time boundary, or batched states fail")
def probe_dynamiqs():
    import dynamiqs as dq
    import jax.numpy as jnp
    sx = dq.sigmax(); psi0 = dq.basis(2,0)
    def run(h, ts): return dq.sesolve(h, psi0, ts).states
    return four(
        lambda: checked(abs(float(jnp.linalg.norm(run(sx, jnp.asarray([0.,0.3]))[-1].to_jax()))-1.) < 1e-6, {"norm": jnp.linalg.norm(run(sx,jnp.asarray([0.,.3]))[-1].to_jax())}),
        lambda: checked(abs(float(jnp.linalg.norm(run(1j*sx, jnp.asarray([0.,.3]))[-1].to_jax()))-1.) > 1e-3, {"nonhermitian_norm_drift": jnp.linalg.norm(run(1j*sx,jnp.asarray([0.,.3]))[-1].to_jax())}),
        lambda: checked(jnp.allclose(run(sx,jnp.asarray([0.]))[0].to_jax(), psi0.to_jax()), {"zero_time_identity": True}),
        lambda: checked(run(sx,jnp.linspace(0.,1.,65)).shape[0] == 65, {"saved_states": 65}),
    )


@register("e3nn", "e3nn.o3.Irreps/FullyConnectedTensorProduct", "Torch tensors -> equivariant representation algebra", "O(3) irreps dimensions and tensor product", "demote if irreps, parity control, scalar boundary, or batched tensor product fails")
def probe_e3nn():
    import e3nn.o3 as o3
    import torch
    irreps = o3.Irreps("1x0e + 1x1o")
    tp = o3.FullyConnectedTensorProduct("1x1o", "1x1o", "1x0e")
    return four(
        lambda: checked(irreps.dim == 4 and tp(torch.ones(3),torch.ones(3)).shape == (1,), {"irreps_dim": irreps.dim}),
        lambda: checked(o3.Irrep("1o").p != o3.Irrep("1e").p, {"parity_distinguished": True}),
        lambda: checked(torch.allclose(tp(torch.zeros(3),torch.ones(3)), torch.zeros(1)), {"zero_absorbs": True}),
        lambda: checked(tp(torch.randn(64,3),torch.randn(64,3)).shape == (64,1), {"batch": 64}),
    )


@register("e3nn_jax", "e3nn_jax.Irreps/IrrepsArray", "JAX arrays -> equivariant representation metadata", "O(3) irreps array norms", "demote if representation dimension/parity/zero/batch handling fails")
def probe_e3nn_jax():
    import e3nn_jax as e3nn
    import jax.numpy as jnp
    irreps = e3nn.Irreps("1x0e + 1x1o")
    return four(
        lambda: checked(e3nn.IrrepsArray(irreps,jnp.arange(4.)).array.shape == (4,), {"dim": irreps.dim}),
        lambda: checked(e3nn.Irrep("1o").p != e3nn.Irrep("1e").p, {"parity_distinguished": True}),
        lambda: checked(float(jnp.linalg.norm(e3nn.IrrepsArray(irreps,jnp.zeros(4)).array)) == 0., {"zero_norm": 0.}),
        lambda: checked(e3nn.IrrepsArray(irreps,jnp.zeros((64,4))).array.shape == (64,4), {"batch": 64}),
    )


@register("equinox", "equinox.nn.Linear/filter_jit", "JAX pytree module -> differentiable compiled call", "deterministic dense layer", "demote if module call, shape rejection, zero-input boundary, or compiled batch fails", role="support_only", support=True)
def probe_equinox():
    import equinox as eqx
    import jax
    import jax.numpy as jnp
    layer = eqx.nn.Linear(3,2,key=jax.random.PRNGKey(0))
    return four(
        lambda: checked(layer(jnp.ones(3)).shape == (2,), {"shape": [2]}),
        lambda: expect_raises(Exception, lambda: layer(jnp.ones(4))),
        lambda: checked(jnp.all(jnp.isfinite(layer(jnp.zeros(3)))), {"zero_input_finite": True}),
        lambda: checked(jax.vmap(eqx.filter_jit(layer))(jnp.ones((64,3))).shape == (64,2), {"batch": 64}),
    )


@register("flax", "flax.linen.Dense.init/apply", "JAX parameters -> Linen module execution", "dense layer init/apply", "demote if initialized apply, parameter-shape control, zero batch, or JIT batch fails", role="support_only", support=True)
def probe_flax():
    import flax.linen as nn
    import jax
    import jax.numpy as jnp
    model=nn.Dense(2); params=model.init(jax.random.PRNGKey(0),jnp.ones((1,3)))
    return four(
        lambda: checked(model.apply(params,jnp.ones((4,3))).shape == (4,2), {"shape":[4,2]}),
        lambda: expect_raises(Exception, lambda: model.apply(params,jnp.ones((4,4)))),
        lambda: checked(model.apply(params,jnp.zeros((0,3))).shape == (0,2), {"empty_batch": True}),
        lambda: checked(jax.jit(model.apply)(params,jnp.ones((128,3))).shape == (128,2), {"jit_batch":128}),
    )


@register("geomstats", "geomstats.geometry.hypersphere.Hypersphere.metric", "Torch-backend manifold coordinates -> exp/log/geodesic distance", "S2 exp/log round trip", "demote if manifold round-trip, off-manifold control, zero tangent, or batch distance fails")
def probe_geomstats():
    import torch
    from geomstats.geometry.hypersphere import Hypersphere
    sphere=Hypersphere(dim=2); base=torch.tensor([1.,0.,0.],dtype=torch.float64); tangent=torch.tensor([0.,.2,0.],dtype=torch.float64)
    def endpoint(): return sphere.metric.exp(tangent,base)
    return four(
        lambda: checked(torch.linalg.norm(sphere.metric.log(endpoint(),base)-tangent) < 1e-6, {"roundtrip_error": torch.linalg.norm(sphere.metric.log(endpoint(),base)-tangent)}),
        lambda: checked(not bool(sphere.belongs(torch.tensor([2.,0.,0.],dtype=torch.float64))), {"off_manifold_rejected": True}),
        lambda: checked(torch.allclose(sphere.metric.exp(torch.zeros(3,dtype=torch.float64),base),base), {"zero_tangent_identity":True}),
        lambda: checked(sphere.metric.dist(torch.stack([base]*64),torch.stack([endpoint()]*64)).shape == (64,), {"batch":64}),
    )


@register("gudhi", "gudhi.SimplexTree.persistence", "point/simplicial data -> filtered complex -> persistence", "triangle filtration", "demote if persistence, missing-face control, empty boundary, or Rips stress fails")
def probe_gudhi():
    import gudhi
    import numpy as np
    def triangle(include_face=True):
        st=gudhi.SimplexTree(); [st.insert([i],filtration=0.) for i in range(3)]; [st.insert(list(e),filtration=1.) for e in [(0,1),(1,2),(0,2)]]
        if include_face: st.insert([0,1,2],filtration=2.)
        st.make_filtration_non_decreasing(); return st
    return four(
        lambda: checked(len(triangle().persistence()) > 0, {"simplices": triangle().num_simplices()}),
        lambda: checked(triangle(False).num_simplices() < triangle(True).num_simplices(), {"face_control":True}),
        lambda: checked(gudhi.SimplexTree().num_simplices() == 0, {"empty_complex":True}),
        lambda: checked(gudhi.RipsComplex(points=np.random.default_rng(0).normal(size=(48,2)),max_edge_length=1.).create_simplex_tree(max_dimension=2).num_simplices() > 48, {"points":48}),
    )


@register("haiku", "haiku.transform/Linear", "JAX function transform -> explicit parameter state", "dense layer transform", "demote if init/apply, parameter mismatch control, empty boundary, or JIT batch fails", role="support_only", support=True)
def probe_haiku():
    import haiku as hk
    import jax
    import jax.numpy as jnp
    f=hk.without_apply_rng(hk.transform(lambda x: hk.Linear(2)(x))); params=f.init(jax.random.PRNGKey(0),jnp.ones((1,3)))
    return four(
        lambda: checked(f.apply(params,jnp.ones((4,3))).shape == (4,2), {"shape":[4,2]}),
        lambda: expect_raises(Exception, lambda: f.apply(params,jnp.ones((4,4)))),
        lambda: checked(f.apply(params,jnp.zeros((0,3))).shape == (0,2), {"empty_batch":True}),
        lambda: checked(jax.jit(f.apply)(params,jnp.ones((128,3))).shape == (128,2), {"jit_batch":128}),
    )


@register("igraph", "igraph.Graph/shortest_paths/topological_sorting", "edge list -> native igraph algorithms", "DAG order and weighted path", "demote if path/order, cycle control, empty graph, or large native graph fails")
def probe_igraph():
    import igraph as ig
    return four(
        lambda: checked(ig.Graph(n=3,edges=[(0,1),(1,2)],directed=True).distances(0,2)[0][0] == 2, {"distance":2}),
        lambda: checked(not ig.Graph(n=2,edges=[(0,1),(1,0)],directed=True).is_dag(), {"cycle_detected":True}),
        lambda: checked(ig.Graph().vcount() == 0, {"empty":True}),
        lambda: checked(ig.Graph(n=5000,edges=[(i,i+1) for i in range(4999)]).distances(0,4999)[0][0] == 4999, {"nodes":5000}),
    )


@register("jax", "jax.jit/vmap/grad", "array program -> autodiff/batching/XLA execution", "quartic gradient identity", "demote if autodiff, erased-dependence control, zero boundary, or compiled vector stress fails")
def probe_jax():
    import jax
    import jax.numpy as jnp
    grad=jax.grad(lambda x: x**4)
    return four(
        lambda: checked(abs(float(grad(2.))-32.) < 1e-12, {"grad_at_2":grad(2.)}),
        lambda: checked(float(jax.grad(lambda x: jax.lax.stop_gradient(x**4))(2.)) == 0., {"stop_gradient_control":True}),
        lambda: checked(float(grad(0.)) == 0., {"zero_gradient":0.}),
        lambda: checked(jax.jit(jax.vmap(grad))(jnp.arange(4096.,dtype=jnp.float64)).shape == (4096,), {"jit_vmap":4096}),
    )


@register("jaxlib", "jax.devices/jaxlib runtime", "Python JAX frontend -> native XLA backend", "device placement and execution", "demote if native backend/version/device placement or large operation fails", role="support_only", support=True)
def probe_jaxlib():
    import jax
    import jax.numpy as jnp
    import jaxlib
    return four(
        lambda: checked(len(jax.devices()) >= 1 and float(jax.jit(lambda x:x+1)(1.)) == 2., {"devices":[str(x) for x in jax.devices()],"version":jaxlib.__version__}),
        lambda: expect_raises(Exception, lambda: jax.device_put(1, device="not-a-device")),
        lambda: checked(jax.device_put(jnp.empty((0,))).shape == (0,), {"empty_device_array":True}),
        lambda: checked(float(jax.jit(lambda x:jnp.sum(x*x))(jnp.ones(100000))) == 100000., {"elements":100000}),
    )


@register("jaxopt", "jaxopt.GradientDescent.run", "JAX objective -> iterative optimizer state", "quadratic minimization", "demote if optimum, wrong-shape control, stationary boundary, or batched starts fail")
def probe_jaxopt():
    import jax
    import jax.numpy as jnp
    from jaxopt import GradientDescent
    solver=GradientDescent(lambda x:jnp.sum((x-3.)**2),maxiter=80,stepsize=.1)
    return four(
        lambda: checked(jnp.max(jnp.abs(solver.run(jnp.zeros(3)).params-3.)) < 2e-3, {"solution":solver.run(jnp.zeros(3)).params}),
        lambda: checked(jnp.max(jnp.abs(solver.run(jnp.zeros(3)).params)) > .1, {"movement_control":True}),
        lambda: checked(jnp.max(jnp.abs(solver.run(jnp.full(3,3.)).params-3.)) == 0., {"stationary":True}),
        lambda: checked(jax.vmap(lambda x:solver.run(x).params)(jnp.zeros((32,3))).shape == (32,3), {"starts":32}),
    )


@register("jaxtyping", "jaxtyping.jaxtyped with beartype", "annotated JAX arrays -> runtime shape/dtype guard", "vector shape annotation", "demote if valid vectors pass but wrong-rank values are not rejected", role="control_only", support=True)
def probe_jaxtyping():
    import jax.numpy as jnp
    from beartype import beartype
    from jaxtyping import Array, Float, jaxtyped
    @jaxtyped(typechecker=beartype)
    @beartype
    def norm(x: Float[Array,"n"]): return jnp.linalg.norm(x)
    return four(
        lambda: checked(abs(float(norm(jnp.ones(3)))-3**.5) < 1e-6, {"norm":norm(jnp.ones(3))}),
        lambda: expect_raises(Exception, lambda: norm(jnp.ones((2,2)))),
        lambda: checked(float(norm(jnp.empty((0,)))) == 0., {"empty_norm":0.}),
        lambda: checked(all(float(norm(jnp.ones(128))) > 0 for _ in range(64)), {"calls":64,"width":128}),
    )


@register("jraph", "jraph.GraphsTuple/segment_sum", "graph indices -> JAX message aggregation", "directed edge aggregation", "demote if aggregation, bad-index control, empty graph, or large edge batch fails")
def probe_jraph():
    import jax.numpy as jnp
    import jraph
    aggregate=lambda data,seg,n: jraph.segment_sum(data,seg,num_segments=n)
    return four(
        lambda: checked(jnp.allclose(aggregate(jnp.array([1.,2.,3.]),jnp.array([0,1,0]),2),jnp.array([4.,2.])), {"aggregates":[4.,2.]}),
        lambda: expect_raises(Exception, lambda: aggregate(jnp.ones(2),jnp.array([0,1,2]),3)),
        lambda: checked(aggregate(jnp.empty((0,)),jnp.empty((0,),dtype=int),0).shape == (0,), {"empty":True}),
        lambda: checked(float(aggregate(jnp.ones(10000),jnp.arange(10000)%64,64).sum()) == 10000., {"edges":10000}),
    )


@register("kahypar", "kahypar.Hypergraph", "compact hyperedge vectors -> native hypergraph structure", "weighted overlapping hyperedges", "demote if pins/degrees, invalid-vector control, singleton boundary, or large hypergraph construction fails", role="support_only", support=True)
def probe_kahypar():
    import kahypar
    def make(n,edges,k=2):
        flat=[]; idx=[0]
        for edge in edges: flat.extend(edge); idx.append(len(flat))
        return kahypar.Hypergraph(n,len(edges),idx,flat,k,[1]*len(edges),[1]*n)
    return four(
        lambda: checked(make(4,[(0,1,2),(2,3)]).numPins() == 5 and make(4,[(0,1,2),(2,3)]).nodeDegree(2) == 2, {"nodes":4,"edges":2,"pins":5}),
        lambda: checked(make(4,[(0,1),(2,3)]).nodeDegree(0) == 1 and make(4,[(0,1),(2,3)]).nodeDegree(2) == 1, {"disjoint_edge_control":True}),
        lambda: checked(make(2,[(0,1)]).numEdges() == 1 and make(2,[(0,1)]).numPins() == 2, {"single_hyperedge":True}),
        lambda: checked(make(5001,[(i,i+1) for i in range(5000)]).numEdges() == 5000, {"nodes":5001,"edges":5000}),
    )


@register("kanren", "kanren.run/var/membero", "logic goals -> relational search", "finite membership relation", "demote if solutions, inconsistent control, empty relation, or Cartesian search fails")
def probe_kanren():
    from kanren import membero, run, var
    x,y=var(),var()
    return four(
        lambda: checked(run(0,x,membero(x,(1,2,3))) == (1,2,3), {"solutions":[1,2,3]}),
        lambda: checked(run(0,x,membero(x,())) == (), {"inconsistent_empty":True}),
        lambda: checked(run(1,x,membero(x,(0,))) == (0,), {"singleton":True}),
        lambda: checked(len(run(0,(x,y),membero(x,range(16)),membero(y,range(16)))) == 256, {"solutions":256}),
    )


@register("lineax", "lineax.linear_solve", "JAX matrix operator -> typed linear solve", "dense nonsingular solve", "demote if residual, singular control, zero RHS, or batched-size solve fails")
def probe_lineax():
    import jax.numpy as jnp
    import lineax as lx
    def solve(a,b): return lx.linear_solve(lx.MatrixLinearOperator(jnp.asarray(a)),jnp.asarray(b),solver=lx.AutoLinearSolver(well_posed=None)).value
    a=jnp.array([[3.,1.],[1.,2.]])
    return four(
        lambda: checked(jnp.linalg.norm(a@solve(a,jnp.array([1.,0.]))-jnp.array([1.,0.])) < 1e-6, {"residual":jnp.linalg.norm(a@solve(a,jnp.array([1.,0.]))-jnp.array([1.,0.]))}),
        lambda: expect_raises(Exception, lambda: solve(jnp.zeros((2,2)),jnp.ones(2))),
        lambda: checked(jnp.allclose(solve(jnp.eye(2),jnp.zeros(2)),jnp.zeros(2)), {"zero_rhs":True}),
        lambda: checked(jnp.linalg.norm(jnp.eye(64)@solve(jnp.eye(64),jnp.arange(64.))-jnp.arange(64.)) < 1e-6, {"dimension":64}),
    )


@register("netket", "netket.hilbert.Spin", "finite Hilbert constraint -> enumerated quantum basis", "spin-1/2 basis enumeration", "demote if state enumeration, invalid spin control, minimal Hilbert, or constrained space fails")
def probe_netket():
    from netket.hilbert import Spin
    return four(
        lambda: checked(Spin(s=.5,N=4).n_states == 16, {"states":16}),
        lambda: expect_raises(Exception, lambda: Spin(s=.3,N=2)),
        lambda: checked(Spin(s=.5,N=1).all_states().shape == (2,1), {"minimal_shape":[2,1]}),
        lambda: checked(Spin(s=.5,N=10,total_sz=0).n_states == 252, {"constrained_states":252}),
    )


@register("networkx", "networkx.DiGraph/topological_sort", "edge list -> graph algorithms", "DAG ordering and cycle control", "demote if DAG order/cycle rejection/empty graph/large path fails")
def probe_networkx():
    import networkx as nx
    return four(
        lambda: checked(list(nx.topological_sort(nx.DiGraph([(0,1),(1,2)]))) == [0,1,2], {"order":[0,1,2]}),
        lambda: expect_raises(nx.NetworkXUnfeasible, lambda: list(nx.topological_sort(nx.DiGraph([(0,1),(1,0)])))),
        lambda: checked(list(nx.topological_sort(nx.DiGraph())) == [], {"empty":True}),
        lambda: checked(nx.shortest_path_length(nx.path_graph(5000),0,4999) == 4999, {"nodes":5000}),
    )


@register("numpy", "numpy.linalg/einsum/random.Generator", "host arrays -> deterministic numerical substrate", "linear solve and seeded vector algebra", "demote if solve, singular control, empty reduction, or large einsum fails", role="support_only", support=True)
def probe_numpy():
    import numpy as np
    a=np.array([[3.,1.],[1.,2.]]); b=np.array([1.,0.])
    return four(
        lambda: checked(np.linalg.norm(a@np.linalg.solve(a,b)-b) < 1e-12, {"residual":np.linalg.norm(a@np.linalg.solve(a,b)-b)}),
        lambda: expect_raises(np.linalg.LinAlgError, lambda: np.linalg.solve(np.zeros((2,2)),np.ones(2))),
        lambda: checked(np.sum(np.empty((0,))) == 0., {"empty_sum":0.}),
        lambda: checked(np.einsum("ij,jk->ik",np.ones((256,64)),np.ones((64,128))).shape == (256,128), {"shape":[256,128]}),
    )


@register("numpyro", "numpyro.distributions.Normal/sample/log_prob", "JAX PRNG -> probabilistic distribution semantics", "normal sampling and log-density", "demote if sampling/log-prob, invalid scale control, degenerate shape, or vector batch fails")
def probe_numpyro():
    import jax
    import jax.numpy as jnp
    import numpyro.distributions as dist
    normal=dist.Normal(0.,1.)
    return four(
        lambda: checked(normal.sample(jax.random.PRNGKey(0),(128,)).shape == (128,) and jnp.isfinite(normal.log_prob(0.)), {"sample_shape":[128],"logp0":normal.log_prob(0.)}),
        lambda: expect_raises(Exception, lambda: dist.Normal(0.,-1.,validate_args=True)),
        lambda: checked(normal.sample(jax.random.PRNGKey(1),(0,)).shape == (0,), {"empty_sample":True}),
        lambda: checked(jnp.all(jnp.isfinite(normal.log_prob(jnp.linspace(-8.,8.,10000)))), {"log_prob_points":10000}),
    )


@register("opt_einsum", "opt_einsum.contract/contract_path", "einsum expression -> contraction planner -> array result", "three-tensor contraction", "demote if contract, incompatible-index control, scalar boundary, or chain path fails", role="support_only", support=True)
def probe_opt_einsum():
    import numpy as np
    import opt_einsum as oe
    return four(
        lambda: checked(np.allclose(oe.contract("ab,bc->ac",np.arange(6.).reshape(2,3),np.ones((3,2))),np.array([[3.,3.],[12.,12.]])), {"matches":True}),
        lambda: expect_raises(ValueError, lambda: oe.contract("ab,bc->ac",np.ones((2,3)),np.ones((4,2)))),
        lambda: checked(float(oe.contract(",->",np.asarray(3.),np.asarray(2.))) == 6., {"scalar":6.}),
        lambda: checked(oe.contract("ab,bc,cd,de,ef->af",*[np.ones((16,16)) for _ in range(5)]).shape == (16,16), {"tensors":5}),
    )


@register("optax", "optax.adam/init/update/apply_updates", "JAX gradients -> optimizer transform state", "quadratic descent", "demote if update reduces loss, bad-tree control, zero gradient, or repeated descent fails", role="support_only", support=True)
def probe_optax():
    import jax
    import jax.numpy as jnp
    import optax
    tx=optax.adam(.1)
    def one(p,g,state):
        u,state=tx.update(g,state,p); return optax.apply_updates(p,u),state
    def pos():
        p=jnp.array([4.,-3.]); state=tx.init(p); before=float(jnp.sum(p*p)); p,state=one(p,2*p,state)
        return checked(float(jnp.sum(p*p)) < before, {"before":before,"after":jnp.sum(p*p)})
    def stress():
        p=jnp.ones(1024)*4.; state=tx.init(p)
        for _ in range(80): p,state=one(p,2*p,state)
        return checked(float(jnp.mean(p*p)) < .02, {"parameters":1024,"steps":80,"mean_square":jnp.mean(p*p)})
    return four(pos, lambda: expect_raises(Exception, lambda: tx.update({"x":jnp.ones(2)},tx.init(jnp.ones(2)))), lambda: checked(jnp.allclose(one(jnp.ones(2),jnp.zeros(2),tx.init(jnp.ones(2)))[0],jnp.ones(2)), {"zero_gradient":True}), stress)


@register("optimistix", "optimistix.fixed_point/FixedPointIteration", "JAX map -> convergence-controlled fixed point", "Dottie-number fixed point", "demote if convergence/control/boundary/multi-start execution fails")
def probe_optimistix():
    import jax
    import jax.numpy as jnp
    import optimistix as ox
    solver=ox.FixedPointIteration(rtol=1e-10,atol=1e-10)
    solve=lambda fn,y,max_steps=1000,throw=True: ox.fixed_point(fn,solver,jnp.asarray(y,dtype=jnp.float64),max_steps=max_steps,throw=throw).value
    return four(
        lambda: checked(abs(float(solve(lambda x,args:jnp.cos(x),1.))-0.7390851332151607) < 1e-8, {"fixed_point":solve(lambda x,args:jnp.cos(x),1.)}),
        lambda: checked(abs(float(solve(lambda x,args:jnp.cos(x),1.,max_steps=1,throw=False))-0.7390851332151607) > 1e-3, {"one_step_not_converged":True}),
        lambda: checked(float(solve(lambda x,args:jnp.zeros_like(x),0.)) == 0., {"zero_fixed":True}),
        lambda: checked(jax.vmap(lambda y:solve(lambda x,args:.5*x+1.,y))(jnp.arange(32.)).shape == (32,), {"starts":32}),
    )


@register("orbax", "orbax.checkpoint.PyTreeCheckpointer.save/restore", "JAX pytree -> filesystem checkpoint boundary -> restored tree", "temporary pytree round trip", "demote if round trip, overwrite control, empty pytree, or larger checkpoint fails", role="support_only", support=True)
def probe_orbax():
    import jax.numpy as jnp
    import orbax.checkpoint as ocp
    def roundtrip(item):
        with tempfile.TemporaryDirectory(prefix="orbax-stress-") as td:
            path=Path(td)/"ckpt"; ckpt=ocp.PyTreeCheckpointer(); ckpt.save(path,item); restored=ckpt.restore(path); ckpt.close(); return restored
    def neg():
        with tempfile.TemporaryDirectory(prefix="orbax-stress-") as td:
            path=Path(td)/"ckpt"; ckpt=ocp.PyTreeCheckpointer(); ckpt.save(path,{"x":jnp.ones(2)})
            try: return expect_raises(Exception, lambda: ckpt.save(path,{"x":jnp.zeros(2)}))
            finally: ckpt.close()
    return four(
        lambda: checked(bool(jnp.allclose(roundtrip({"x":jnp.arange(8.)})["x"],jnp.arange(8.))), {"roundtrip":True}),
        neg,
        lambda: checked(float(roundtrip({"x":jnp.asarray(0.)})["x"]) == 0., {"zero_scalar_leaf":True}),
        lambda: checked(roundtrip({"x":jnp.arange(100000.)})["x"].shape == (100000,), {"elements":100000}),
    )


@register("ott", "ott.geometry.pointcloud.PointCloud/ott.solvers.linear.sinkhorn", "point clouds -> entropic OT geometry -> transport solution", "translated 1D empirical measures", "demote if finite transport, erasure control, singleton boundary, or larger Sinkhorn solve fails")
def probe_ott():
    import jax.numpy as jnp
    from ott.geometry import pointcloud
    from ott.problems.linear import linear_problem
    from ott.solvers.linear import sinkhorn
    def solve(x,y): return sinkhorn.Sinkhorn(threshold=1e-4,max_iterations=300)(linear_problem.LinearProblem(pointcloud.PointCloud(jnp.asarray(x),jnp.asarray(y),epsilon=.05)))
    return four(
        lambda: checked(bool(jnp.isfinite(solve(jnp.arange(8.)[:,None],(jnp.arange(8.)+1)[:,None]).reg_ot_cost)), {"cost":solve(jnp.arange(8.)[:,None],(jnp.arange(8.)+1)[:,None]).reg_ot_cost}),
        lambda: checked(float(solve(jnp.arange(8.)[:,None],jnp.arange(8.)[:,None]).reg_ot_cost) < float(solve(jnp.arange(8.)[:,None],(jnp.arange(8.)+3)[:,None]).reg_ot_cost), {"identity_beats_shift":True}),
        lambda: checked(bool(jnp.isfinite(solve(jnp.array([[0.]]),jnp.array([[0.]])).reg_ot_cost)), {"singleton":True}),
        lambda: checked(solve(jnp.linspace(0,1,64)[:,None],jnp.linspace(.1,1.1,64)[:,None]).matrix.shape == (64,64), {"support":64}),
    )


@register("pandas", "pandas.DataFrame.groupby/merge", "tabular records -> grouped and joined controls", "group aggregation and key join", "demote if aggregation, join-cardinality control, empty schema, or large groupby fails", role="support_only", support=True)
def probe_pandas():
    import numpy as np
    import pandas as pd
    df=pd.DataFrame({"k":["a","a","b"],"v":[1.,2.,4.]})
    return four(
        lambda: checked(df.groupby("k")["v"].sum().to_dict() == {"a":3.,"b":4.}, {"groups":{"a":3.,"b":4.}}),
        lambda: expect_raises(Exception, lambda: df.merge(pd.DataFrame({"k":["a","a"]}),on="k",validate="one_to_one")),
        lambda: checked(pd.DataFrame({"k":pd.Series(dtype=str),"v":pd.Series(dtype=float)}).groupby("k")["v"].sum().empty, {"empty_groupby":True}),
        lambda: checked(len(pd.DataFrame({"k":np.arange(100000)%128,"v":1}).groupby("k")["v"].sum()) == 128, {"rows":100000,"groups":128}),
    )


@register("pysindy", "pysindy.SINDy + PolynomialLibrary + STLSQ", "state/derivative fixtures -> sparse dynamics recovery", "existing affine-generator capability fixture", "demote if affine recovery, shuffled-derivative control, zero generator, or larger heldout fit fails")
def probe_pysindy():
    import numpy as np
    mod=load_repo_module("system_v4/probes/sim_pysindy_capability.py","deep_stress_pysindy_fixture")
    rng=np.random.default_rng(20260714); a=np.array([[-.2,.1],[.05,-.3]]); b=np.array([.12,-.07])
    def fit(n=256,shuffle=False,zero=False):
        x=rng.uniform(-1,1,(n,2)); dx=np.zeros_like(x) if zero else x@a.T+b
        if shuffle: dx=dx[rng.permutation(n)]
        model=mod.fit_affine(x,dx); pred=np.asarray(model.predict(x)); return float(np.sqrt(np.mean((pred-(np.zeros_like(x) if zero else x@a.T+b))**2)))
    return four(
        lambda: checked(fit() < 1e-9, {"affine_rmse":fit()}),
        lambda: checked(fit(shuffle=True) > 1e-2, {"shuffle_rejected":True}),
        lambda: checked(fit(zero=True) < 1e-12, {"zero_generator":True}),
        lambda: checked(fit(n=2048) < 1e-9, {"train_rows":2048}),
    )


@register("quimb", "quimb.tensor.MPS_rand_state/entropy", "tensor network -> canonicalization/contraction", "product/GHZ-like MPS entanglement", "demote if norm/entanglement control/product boundary or longer MPS contraction fails")
def probe_quimb():
    import quimb.tensor as qtn
    import numpy as np
    return four(
        lambda: checked(abs(qtn.MPS_rand_state(12,bond_dim=4,seed=1).norm()-1.) < 1e-10, {"normalized":True}),
        lambda: checked(qtn.MPS_ghz_state(8).entropy(4) > .9, {"ghz_entropy":qtn.MPS_ghz_state(8).entropy(4)}),
        lambda: checked(abs(qtn.MPS_computational_state("0000").entropy(2)) < 1e-12, {"product_entropy":0.}),
        lambda: checked(np.isfinite(qtn.MPS_rand_state(64,bond_dim=8,seed=2).norm()), {"sites":64,"bond":8}),
    )


@register("qutip", "qutip.sesolve/entropy_vn", "Qobj Hamiltonian -> quantum evolution and entropy", "single-qubit unitary evolution", "demote if unitary norm, non-Hermitian control, zero-time boundary, or long time grid fails")
def probe_qutip():
    import numpy as np
    import qutip as qt
    psi=qt.basis(2,0); sx=qt.sigmax()
    def run(h,t): return qt.sesolve(h,psi,t).states
    return four(
        lambda: checked(abs(run(sx,[0,.3])[-1].norm()-1.) < 1e-10, {"norm":run(sx,[0,.3])[-1].norm()}),
        lambda: checked(abs((((-1j*(1j*sx)*.3).expm())*psi).norm()-1.) > 1e-3, {"nonhermitian_propagator_norm_drift":(((-1j*(1j*sx)*.3).expm())*psi).norm()}),
        lambda: checked((run(sx,[0])[-1]-psi).norm() < 1e-12, {"zero_time_identity":True}),
        lambda: checked(len(run(sx,np.linspace(0,10,1001))) == 1001, {"saved_states":1001}),
    )


@register("qutip_jax", "qutip_jax.JaxArray and qutip data conversion", "QuTiP data layer -> JAX-backed quantum arrays", "dense operator conversion/algebra", "demote if JAX conversion/algebra, shape control, zero operator, or batched native operation fails", role="support_only", support=True)
def probe_qutip_jax():
    import jax.numpy as jnp
    import qutip as qt
    import qutip_jax
    def qobj(x): return qt.Qobj(x,dtype="jax")
    return four(
        lambda: checked(abs((qobj(jnp.eye(2))*qobj(jnp.eye(2))).tr()-2.) < 1e-12, {"backend_type":type(qobj(jnp.eye(2)).data).__name__}),
        lambda: expect_raises(Exception, lambda: qobj(jnp.ones((2,3))).tr()),
        lambda: checked(qobj(jnp.zeros((2,2))).norm() == 0., {"zero_operator":True}),
        lambda: checked(all(abs((qobj(jnp.eye(8))*qobj(jnp.eye(8))).tr()-8.) < 1e-12 for _ in range(32)), {"calls":32,"dimension":8}),
    )


@register("rustworkx", "rustworkx.PyDiGraph/topological_sort", "Python node/edge data -> Rust graph kernel", "DAG ordering and cycle control", "demote if DAG, cycle rejection, empty graph, or large shortest path fails")
def probe_rustworkx():
    import rustworkx as rx
    def graph(edges):
        g=rx.PyDiGraph(); n=max((max(e) for e in edges),default=-1)+1; g.add_nodes_from(range(n)); g.add_edges_from([(a,b,None) for a,b in edges]); return g
    return four(
        lambda: checked(list(rx.topological_sort(graph([(0,1),(1,2)]))) == [0,1,2], {"order":[0,1,2]}),
        lambda: expect_raises(rx.DAGHasCycle, lambda: rx.topological_sort(graph([(0,1),(1,0)]))),
        lambda: checked(rx.topological_sort(rx.PyDiGraph()) == [], {"empty":True}),
        lambda: checked(len(rx.dijkstra_shortest_paths(graph([(i,i+1) for i in range(4999)]),0,4999)) == 1, {"nodes":5000}),
    )


@register("scipy", "scipy.integrate.solve_ivp/scipy.linalg", "NumPy arrays -> compiled scientific kernels", "exponential ODE and linear algebra", "demote if analytic integration, invalid span control, zero interval, or stiff/vector stress fails", role="support_only", support=True)
def probe_scipy():
    import numpy as np
    from scipy.integrate import solve_ivp
    solve=lambda rate,span,y: solve_ivp(lambda t,z:rate*z,span,[y],rtol=1e-10,atol=1e-12)
    return four(
        lambda: checked(abs(solve(-1.,(0.,1.),1.).y[0,-1]-np.exp(-1.)) < 1e-8, {"endpoint":solve(-1.,(0.,1.),1.).y[0,-1]}),
        lambda: checked(not solve(-1.,(1.,0.),1.,).success or solve(-1.,(1.,0.),1.).t[-1] == 0., {"reverse_span_handled":True}),
        lambda: checked(solve(-1.,(0.,0.),0.).t.size >= 1, {"zero_interval":True}),
        lambda: checked(solve(-100.,(0.,1.),1.).success, {"rate":-100.}),
    )


@register("sympy", "sympy.simplify/solve/diff", "symbolic expressions -> exact algebraic checks", "polynomial identity and exact roots", "demote if identity, false-identity control, zero expression, or expanded polynomial stress fails")
def probe_sympy():
    import sympy as sp
    x=sp.symbols("x")
    return four(
        lambda: checked(sp.simplify((x+1)**2-(x**2+2*x+1)) == 0, {"identity":True}),
        lambda: checked(sp.simplify((x+1)**2-(x**2+1)) != 0, {"false_identity_rejected":True}),
        lambda: checked(sp.diff(sp.Integer(0),x) == 0, {"zero_derivative":True}),
        lambda: checked(sp.expand((x+1)**128).coeff(x,64) == sp.binomial(128,64), {"degree":128}),
    )


@register("toponetx", "toponetx.SimplicialComplex/incidence_matrix", "cells -> combinatorial complex operators", "filled triangle boundary/incidence", "demote if shape/incidence, missing-face control, singleton boundary, or grid complex fails")
def probe_toponetx():
    import toponetx as tnx
    sc=tnx.SimplicialComplex([[0,1,2]])
    return four(
        lambda: checked(tuple(sc.shape) == (3,3,1), {"shape":list(sc.shape)}),
        lambda: checked(tuple(tnx.SimplicialComplex([[0,1],[1,2],[0,2]]).shape) == (3,3), {"unfilled_control":True}),
        lambda: checked(tuple(tnx.SimplicialComplex([[0]]).shape) == (1,), {"singleton":True}),
        lambda: checked(tnx.SimplicialComplex([[i,i+1,i+2] for i in range(100)]).shape[2] == 100, {"triangles":100}),
    )


@register("torch", "torch.func.jacrev/autograd", "Torch tensors -> autograd graph -> compiled kernels", "quadratic Jacobian", "demote if gradient, detach control, zero boundary, or batched Jacobian fails")
def probe_torch():
    import torch
    from torch.func import jacrev, vmap
    return four(
        lambda: checked(torch.allclose(jacrev(lambda x:x*x)(torch.tensor([2.,3.])),torch.diag(torch.tensor([4.,6.]))), {"jacobian_diagonal":[4.,6.]}),
        lambda: expect_raises(RuntimeError, lambda: torch.autograd.grad(torch.tensor(2.).detach(),torch.tensor(2.,requires_grad=True))),
        lambda: checked(float(torch.func.grad(lambda x:x**4)(torch.tensor(0.))) == 0., {"zero_gradient":0.}),
        lambda: checked(vmap(jacrev(lambda x:x*x))(torch.ones(256,16)).shape == (256,16,16), {"batch":256,"width":16}),
    )


@register("torch_ga", "torch_ga.GeometricAlgebra.geom_prod/reversion", "Torch autograd tensors -> geometric product", "Cl(0,2) quaternion basis", "demote if product signs/autograd, signature control, zero boundary, or batched products fail")
def probe_torch_ga():
    import torch
    from torch.func import jacrev
    from torch_ga import GeometricAlgebra
    ga=GeometricAlgebra(metric=[-1.,-1.],dtype=torch.float64); one,i,j,k=ga.blade_mvs.to(torch.float64)
    return four(
        lambda: checked(torch.max(torch.abs(ga.geom_prod(i,j)-k)) < 1e-12 and torch.isfinite(jacrev(lambda x:ga.geom_prod(x*i,j)[0])(torch.tensor(1.,dtype=torch.float64))), {"ij_equals_k":True,"autograd":True}),
        lambda: checked(torch.max(torch.abs(ga.geom_prod(j,i)+k)) < 1e-12, {"ji_equals_minus_k":True}),
        lambda: checked(torch.count_nonzero(ga.geom_prod(torch.zeros_like(i),j)) == 0, {"zero_absorbs":True}),
        lambda: checked(ga.geom_prod(i.repeat(256,1),j.repeat(256,1)).shape == (256,4), {"batch":256}),
    )


@register("torch_geometric", "torch_geometric.nn.GCNConv", "edge_index + node features -> graph message passing", "small path graph convolution", "demote if forward/edge control/empty graph or larger graph batch fails")
def probe_torch_geometric():
    import torch
    from torch_geometric.nn import GCNConv
    conv=GCNConv(3,2)
    return four(
        lambda: checked(conv(torch.ones(4,3),torch.tensor([[0,1,2],[1,2,3]])).shape == (4,2), {"nodes":4,"out":2}),
        lambda: expect_raises(Exception, lambda: conv(torch.ones(4,4),torch.tensor([[0,1],[1,2]]))),
        lambda: checked(conv(torch.empty((0,3)),torch.empty((2,0),dtype=torch.long)).shape == (0,2), {"empty_graph":True}),
        lambda: checked(conv(torch.randn(1000,3),torch.stack([torch.arange(999),torch.arange(1,1000)])).shape == (1000,2), {"nodes":1000}),
    )


@register("torchdiffeq", "torchdiffeq.odeint", "Torch vector field -> differentiable ODE integration", "exponential decay", "demote if analytic solve, wrong-sign control, zero boundary, or batch integration fails")
def probe_torchdiffeq():
    import torch
    from torchdiffeq import odeint
    solve=lambda rate,y,t: odeint(lambda tt,z:rate*z,y,t,rtol=1e-8,atol=1e-10)
    return four(
        lambda: checked(abs(float(solve(-1.,torch.tensor([1.]),torch.tensor([0.,1.]))[-1])-torch.exp(torch.tensor(-1.)).item()) < 1e-6, {"endpoint":solve(-1.,torch.tensor([1.]),torch.tensor([0.,1.]))[-1]}),
        lambda: checked(float(solve(1.,torch.tensor([1.]),torch.tensor([0.,1.]))[-1]) > 2.7, {"sign_control":True}),
        lambda: checked(float(solve(-1.,torch.tensor([0.]),torch.tensor([0.,1.]))[-1]) == 0., {"zero_fixed":True}),
        lambda: checked(solve(-.5,torch.ones(128,8),torch.linspace(0,2,33)).shape == (33,128,8), {"batch":128,"times":33}),
    )


@register("torchode", "torchode.solve_ivp", "batched Torch vector field -> compiled ODE solver", "batched exponential decay", "demote if analytic solve, invalid-grid control, zero boundary, or wide batch fails")
def probe_torchode():
    import torch
    import torchode
    def solve(y0,t): return torchode.solve_ivp(lambda tt,y:-y,y0,t,method="tsit5")
    return four(
        lambda: checked(torch.all(torch.isfinite(solve(torch.ones(4,1),torch.linspace(0,1,11).repeat(4,1)).ys)), {"batch":4}),
        lambda: expect_raises(Exception, lambda: solve(torch.ones(2,1),torch.zeros(3,2))),
        lambda: checked(torch.allclose(solve(torch.zeros(2,1),torch.tensor([[0.,1.],[0.,1.]])).ys,torch.zeros(2,2,1)), {"zero_fixed":True}),
        lambda: checked(solve(torch.ones(128,4),torch.linspace(0,2,33).repeat(128,1)).ys.shape == (128,33,4), {"batch":128,"times":33}),
    )


@register("xgi", "xgi.Hypergraph/incidence_matrix", "hyperedges -> higher-order network structure", "overlapping hyperedges", "demote if incidence, missing-node control, empty hypergraph, or large construction fails")
def probe_xgi():
    import xgi
    h=xgi.Hypergraph([[0,1,2],[2,3]])
    return four(
        lambda: checked(h.num_nodes == 4 and h.num_edges == 2, {"nodes":4,"edges":2}),
        lambda: checked(9 not in h.nodes, {"missing_node_control":True}),
        lambda: checked(xgi.Hypergraph().num_nodes == 0, {"empty":True}),
        lambda: checked(xgi.Hypergraph([[i,i+1,i+2] for i in range(5000)]).num_edges == 5000, {"edges":5000}),
    )


@register("xitorch", "xitorch.optimize.rootfinder", "Torch function -> differentiable nonlinear solve", "square-root equation", "demote if root, erased-equation control, zero root, or batched parameters fail")
def probe_xitorch():
    import torch
    from xitorch.optimize import rootfinder
    def solve(target,guess=1.): return rootfinder(lambda x,t:x*x-t,torch.tensor([guess],dtype=torch.float64),params=(torch.tensor([target],dtype=torch.float64),),method="broyden1",f_tol=1e-10)
    return four(
        lambda: checked(abs(float(solve(2.))-2**.5) < 1e-6, {"root":solve(2.)}),
        lambda: checked(abs(float(solve(3.))-float(solve(2.))) > .1, {"target_control":True}),
        lambda: checked(abs(float(solve(0.,0.))) < 1e-8, {"zero_root":True}),
        lambda: checked(all(abs(float(solve(float(i)))-i**.5) < 1e-5 for i in range(1,33)), {"solves":32}),
    )


@register("z3", "z3.Solver/check", "symbolic constraints -> independent SMT decision", "SAT/UNSAT integer controls", "demote if SAT/UNSAT/empty/stress formula decisions fail")
def probe_z3():
    import z3
    def solve(assertions):
        s=z3.Solver(); s.add(*assertions); return s.check()
    x=z3.Int("deep_stress_x")
    return four(
        lambda: checked(solve([x>2]) == z3.sat, {"sat":True}),
        lambda: checked(solve([x>2,x<0]) == z3.unsat, {"unsat_control":True}),
        lambda: checked(solve([]) == z3.sat, {"empty_formula_sat":True}),
        lambda: checked(solve([x>=i for i in range(1000)]) == z3.sat, {"constraints":1000}),
    )


# ---- Current optional-available surfaces and admitted PyKoopman core ----


@register("autoray", "autoray.do/infer_backend", "backend-agnostic call -> NumPy/JAX/Torch dispatch", "cross-backend norm and matmul", "demote if dispatch, unknown-backend control, empty array, or repeated mixed-backend calls fail", role="support_only", support=True)
def probe_autoray():
    import autoray as ar
    import numpy as np
    import torch
    return four(
        lambda: checked(abs(float(ar.do("linalg.norm",np.array([3.,4.]))) - 5.) < 1e-12 and ar.infer_backend(torch.ones(2)) == "torch", {"numpy_norm":5.,"torch_backend":"torch"}),
        lambda: expect_raises(Exception, lambda: ar.do("definitely_missing_operation",np.ones(2))),
        lambda: checked(float(ar.do("sum",np.empty((0,)))) == 0., {"empty_sum":0.}),
        lambda: checked(all(tuple(ar.do("matmul",torch.ones(16,16),torch.eye(16)).shape) == (16,16) for _ in range(128)), {"dispatches":128}),
    )


@register("dynamax", "dynamax.linear_gaussian_ssm.LinearGaussianSSM", "JAX arrays -> state-space-model submodule", "LGSSM import and filter boundary", "demote if the exact removed-alias adapter is unavailable, modifies package files, or real sample/filter/stress calls fail", role="support_only", support=True)
def probe_dynamax():
    import jax
    import jax.numpy as jnp
    adapter = install_dynamax_xla_alias()
    lgssm = importlib.import_module("dynamax.linear_gaussian_ssm")

    def exercise(length: int, seed: int = 0):
        model = lgssm.LinearGaussianSSM(1, 1)
        params, _ = model.initialize(jax.random.PRNGKey(seed))
        states, emissions = model.sample(params, jax.random.PRNGKey(seed + 1), length)
        posterior = model.filter(params, emissions)
        log_prob = model.marginal_log_prob(params, emissions)
        return model, params, states, emissions, posterior, log_prob

    return four(
        lambda: checked(
            (lambda result: result[2].shape == (20, 1) and result[3].shape == (20, 1) and bool(jnp.all(jnp.isfinite(result[4].filtered_means))) and bool(jnp.isfinite(result[5])))(exercise(20)),
            {"timesteps":20,"state_dim":1,"adapter":adapter,"package_files_modified":False},
        ),
        lambda: (lambda result: expect_raises(ValueError, lambda: result[0].filter(result[1], jnp.ones((5, 2)))))(exercise(5)),
        lambda: checked(
            (lambda result: result[4].filtered_means.shape == (1, 1) and bool(jnp.isfinite(result[5])))(exercise(1, 2)),
            {"timesteps":1,"finite":True},
        ),
        lambda: checked(
            (lambda result: result[4].filtered_means.shape == (512, 1) and bool(jnp.all(jnp.isfinite(result[4].filtered_means))))(exercise(512, 4)),
            {"timesteps":512,"finite_filter":True,"adapter":adapter},
        ),
    )


@register("flowMC", "flowMC.Sampler + RQSpline_GRW_Bundle", "JAX PRNG/chains -> resource/strategy bundle -> populated sample buffers", "bounded Gaussian-target sampler with GRW and spline bundle", "demote if resource-free construction is credited, invalid configuration is accepted, or real production buffers do not move and scale", role="support_only", support=True)
def probe_flowmc():
    import jax
    import jax.numpy as jnp
    from flowMC.Sampler import Sampler
    from flowMC.resource_strategy_bundle.RQSpline_GRW import RQSpline_GRW_Bundle
    holders=[]
    def run_sampling(chains=4, local_steps=8, seed=0):
        def logpdf(x, data):
            del data
            return -0.5 * jnp.sum(x * x)
        bundle=RQSpline_GRW_Bundle(
            rng_key=jax.random.PRNGKey(seed),n_chains=chains,n_dims=2,logpdf=logpdf,
            n_local_steps=local_steps,n_global_steps=1,n_training_loops=0,
            n_production_loops=1,n_epochs=1,grw_step_size=.1,
            adapt_step_size=False,adapt_step_size_per_dim=False,
            rq_spline_hidden_units=[4],rq_spline_n_bins=4,rq_spline_n_layers=2,
            batch_size=max(16,chains),n_max_examples=max(32,chains),history_window=8,
        )
        td=tempfile.TemporaryDirectory(prefix="flowmc-stress-"); holders.append(td)
        sampler=Sampler(n_dim=2,n_chains=chains,rng_key=jax.random.PRNGKey(seed+1),resource_strategy_bundles=bundle,outdir=td.name,checkpoint_interval=0)
        sampler.sample(jnp.zeros((chains,2)),{})
        positions=sampler.resources["positions_production"].data
        local_accs=sampler.resources["local_accs_production"].data
        return positions,local_accs,sampler
    return four(
        lambda: checked(
            (lambda result: result[0].shape == (4,9,2) and bool(jnp.all(jnp.isfinite(result[0]))) and bool(jnp.any(result[0] != 0)))(run_sampling()),
            {"chains":4,"stored_steps":9,"real_sampling":True,"bundle":"RQSpline_GRW_Bundle"},
        ),
        lambda: expect_raises(ValueError, lambda: Sampler(n_dim=2,n_chains=2,rng_key=jax.random.PRNGKey(0),resources=None,strategies=None,strategy_order=None,resource_strategy_bundles=None,checkpoint_interval=0)),
        lambda: checked(
            (lambda result: result[0].shape == (1,2,2) and bool(jnp.all(jnp.isfinite(result[0]))))(run_sampling(1,1,3)),
            {"chains":1,"local_steps":1,"finite":True},
        ),
        lambda: checked(
            (lambda result: result[0].shape == (64,17,2) and bool(jnp.all(jnp.isfinite(result[0]))) and bool(jnp.any(result[0] != 0)))(run_sampling(64,16,5)),
            {"chains":64,"stored_steps":17,"real_sampling":True},
        ),
    )


@register("jax_dataclasses", "jax_dataclasses.pytree_dataclass", "dataclass fields -> JAX pytree transforms", "typed state through tree_map/JIT", "demote if pytree flatten, static-field control, zero state, or batched tree maps fail", role="support_only", support=True)
def probe_jax_dataclasses():
    import jax
    import jax.numpy as jnp
    import jax_dataclasses as jdc
    @jdc.pytree_dataclass
    class State:
        x: Any
        label: str = jdc.static_field(default="state")
    s=State(jnp.arange(3.))
    return four(
        lambda: checked(jax.tree_util.tree_leaves(s)[0].shape == (3,), {"leaves":1}),
        lambda: checked(jax.tree_util.tree_structure(State(jnp.ones(2),"a")) != jax.tree_util.tree_structure(State(jnp.ones(2),"b")), {"static_field_changes_treedef":True}),
        lambda: checked(jax.tree_util.tree_map(lambda x:x+1,State(jnp.empty((0,)))).x.shape == (0,), {"empty":True}),
        lambda: checked(jax.jit(lambda q:State(q.x*2,q.label))(State(jnp.ones(100000))).x.shape == (100000,), {"elements":100000}),
    )


@register("jaxga", "jaxga.mv.MultiVector geometric product", "JAX arrays -> geometric algebra generated kernel", "basis-vector product under positive signature", "demote if the exact closure-static-arg adapter is not reversible, the unadapted failure disappears unexpectedly, or adapted geometric products fail", role="support_only", support=True)
def probe_jaxga():
    import jax.numpy as jnp
    import jaxga.ops.multiply as multiply_ops
    from jaxga.mv import MultiVector
    e1=MultiVector.e(1); e2=MultiVector.e(2)
    def product(left, right):
        multiply_ops.get_mv_multiply.cache_clear()
        with jaxga_static_argnames_compat() as adapter:
            value=left*right
        return value,adapter
    def stress_products():
        first,adapter=product(e1,e2)
        values=[first]
        values.extend(e1*e2 for _ in range(127))
        return values,adapter
    return four(
        lambda: checked(
            (lambda result: result[1]["intercept_count"] == 1 and result[1]["restored"] and result[0].values.shape == (1,))(product(e1,e2)),
            {"product":"e1*e2","adapter":"bounded invalid-static-arg filter","package_files_modified":False},
        ),
        lambda: (multiply_ops.get_mv_multiply.cache_clear(), expect_raises(ValueError, lambda: e1*e2))[1],
        lambda: checked(jnp.all((0*e1).values == 0), {"scalar_zero_supported":True}),
        lambda: checked(
            (lambda result: all(value.values.shape == (1,) for value in result[0]) and result[1]["restored"])(stress_products()),
            {"geometric_products":128,"adapter_reversible":True},
        ),
    )


@register("jaxlie", "jaxlie.SO3.exp/log/apply", "JAX tangent vector -> Lie-group rotation", "SO(3) exponential/logarithm round trip", "demote if exp/log, nonrotation control, identity boundary, or batched rotations fail")
def probe_jaxlie():
    import jax
    import jax.numpy as jnp
    import jaxlie
    v=jnp.array([.1,-.2,.3]); r=jaxlie.SO3.exp(v)
    return four(
        lambda: checked(jnp.linalg.norm(r.log()-v) < 1e-6, {"roundtrip_error":jnp.linalg.norm(r.log()-v)}),
        lambda: checked(abs(float(jnp.linalg.det(r.as_matrix()))-1.) < 1e-6, {"determinant":jnp.linalg.det(r.as_matrix()),"reflection_excluded":True}),
        lambda: checked(jnp.allclose(jaxlie.SO3.identity().apply(jnp.zeros(3)),jnp.zeros(3)), {"identity_zero":True}),
        lambda: checked(jax.vmap(lambda x:jaxlie.SO3.exp(x).apply(jnp.array([1.,0.,0.])))(jnp.zeros((1024,3))).shape == (1024,3), {"rotations":1024}),
    )


@register("pymc", "pymc.Model/Normal/sample_prior_predictive", "probabilistic model graph -> compiled prior sampler", "normal prior predictive", "demote if prior sampling, invalid-scale control, zero-draw boundary, or vectorized draws fail", role="support_only", support=True)
def probe_pymc():
    import pymc as pm
    import numpy as np
    def prior(draws,shape=()):
        with pm.Model() as model:
            pm.Normal("x",0.,1.,shape=shape)
            return pm.sample_prior_predictive(draws=draws,random_seed=7,return_inferencedata=False)
    def invalid_scale():
        try:
            value=float(pm.logp(pm.Normal.dist(0.,-1.),0.).eval())
        except Exception as exc:
            return {"invalid_scale_rejected":True,"exception":type(exc).__name__}
        return checked(np.isnan(value), {"invalid_scale_nonfinite":value})
    return four(
        lambda: checked(prior(64)["x"].shape == (64,), {"draws":64}),
        invalid_scale,
        lambda: checked("x" not in prior(0) or prior(0)["x"].shape[0] == 0, {"zero_draws":True}),
        lambda: checked(prior(256,(32,))["x"].shape == (256,32), {"draws":256,"width":32}),
    )


@register("scikit-learn", "sklearn.linear_model.LinearRegression/cross_val_score", "NumPy feature matrix -> estimator fit/predict", "exact affine regression", "demote if heldout fit, shuffled-target control, zero target, or larger fit fails", role="support_only", support=True)
def probe_sklearn():
    import numpy as np
    from sklearn.linear_model import LinearRegression
    rng=np.random.default_rng(7)
    def fit(n=256,shuffle=False,zero=False):
        x=rng.normal(size=(n,4)); y=np.zeros(n) if zero else x@np.array([1.,-2.,.5,3.])+.7
        if shuffle: y=y[rng.permutation(n)]
        m=LinearRegression().fit(x,y); target=np.zeros(n) if zero else x@np.array([1.,-2.,.5,3.])+.7
        return float(np.sqrt(np.mean((m.predict(x)-target)**2)))
    return four(
        lambda: checked(fit() < 1e-10, {"rmse":fit()}),
        lambda: checked(fit(shuffle=True) > 1., {"shuffle_rejected":True}),
        lambda: checked(fit(zero=True) < 1e-12, {"zero_target":True}),
        lambda: checked(fit(10000) < 1e-10, {"rows":10000}),
    )


@register("pykoopman", "pykoopman.Koopman + Identity + EDMD", "explicit affine-bias coordinate -> EDMD fit/predict", "existing admitted affine discrete-map fixture", "demote admitted EDMD core if affine recovery, erased-bias control, identity boundary, or larger fit fails; full package stays quarantined", role="admitted_quarantined_surface", support=False)
def probe_pykoopman():
    import numpy as np
    mod=load_repo_module("system_v4/probes/sim_pykoopman_capability.py","deep_stress_pykoopman_fixture")
    rng=np.random.default_rng(20260714); a=np.array([[.8,.1],[-.05,.7]]); b=np.array([.3,-.2])
    def fit(n=256,aug=True,identity=False):
        x=rng.uniform(-1,1,(n,2)); y=x if identity else x@a.T+b; model,_=mod.fit_edmd(x,y,augmented=aug)
        z=np.column_stack([x,np.ones(n)]) if aug else x; pred=np.asarray(model.predict(z)); target=np.column_stack([y,np.ones(n)]) if aug else y
        return float(np.sqrt(np.mean((pred-target)**2)))
    return four(
        lambda: checked(fit() < 1e-10, {"affine_rmse":fit()}),
        lambda: checked(fit(aug=False) > .05, {"erased_bias_worse":True}),
        lambda: checked(fit(identity=True) < 1e-10, {"identity":True}),
        lambda: checked(fit(2048) < 1e-10, {"rows":2048}),
    )


# ---- Legacy-unclassified Claude-list surfaces (diagnostic, never promoted) ----


@register("ribs", "ribs.archives.GridArchive.add", "solutions/objectives/measures -> quality-diversity archive", "small 2D grid archive", "remain legacy-unclassified; demote operational status if archive insertion, invalid measure control, empty state, or batch insertion fails", role="legacy_unclassified", support=True)
def probe_ribs():
    import numpy as np
    from ribs.archives import GridArchive
    make=lambda dims=(8,8): GridArchive(solution_dim=2,dims=dims,ranges=[(-1,1),(-1,1)],seed=7)
    return four(
        lambda: checked((lambda a:(a.add(np.array([[1.,2.],[2.,3.]]),np.array([1.,2.]),np.array([[0.,0.],[.5,.5]])),len(a)))(make())[1] == 2, {"elites":2}),
        lambda: expect_raises(Exception, lambda: make().add(np.ones((1,2)),np.ones(1),np.ones((1,3)))),
        lambda: checked(len(make()) == 0, {"empty_archive":True}),
        lambda: checked((lambda a:(a.add(np.random.default_rng(0).normal(size=(4096,2)),np.random.default_rng(1).normal(size=4096),np.random.default_rng(2).uniform(-1,1,size=(4096,2))),len(a)))(make((32,32)))[1] > 0, {"batch":4096}),
    )


@register("deap", "deap.tools.selBest/initRepeat", "individual fitness objects -> evolutionary selection", "deterministic ranked population", "remain legacy-unclassified; demote if selection/order control/empty boundary or large population fails", role="legacy_unclassified", support=True)
def probe_deap():
    from deap import base, tools
    class FitnessMax(base.Fitness): weights=(1.,)
    class Individual(list): pass
    def individual(v):
        x=Individual([v]); x.fitness=FitnessMax(); x.fitness.values=(float(v),); return x
    return four(
        lambda: checked([x[0] for x in tools.selBest([individual(i) for i in range(5)],2)] == [4,3], {"selected":[4,3]}),
        lambda: checked([x[0] for x in tools.selWorst([individual(i) for i in range(5)],2)] == [0,1], {"best_worst_distinguished":True}),
        lambda: checked(tools.selBest([],0) == [], {"empty_selection":True}),
        lambda: checked(len(tools.selBest([individual(i) for i in range(10000)],128)) == 128, {"population":10000,"selected":128}),
    )


@register("evotorch", "evotorch.Problem.generate_batch/evaluate", "Torch candidate batch -> evolutionary objective evaluation", "vectorized sphere objective", "remain legacy-unclassified; demote if evaluation, invalid-shape control, zero optimum, or large batch fails", role="legacy_unclassified", support=True)
def probe_evotorch():
    import torch
    from evotorch import Problem
    problem=Problem("min",lambda x:(x*x).sum(dim=-1),solution_length=3,initial_bounds=(-1,1),vectorized=True,seed=7)
    def evaluated(n):
        b=problem.generate_batch(n); problem.evaluate(b); return b
    return four(
        lambda: checked(evaluated(16).evals.shape == (16,1), {"batch":16}),
        lambda: expect_raises(Exception, lambda: problem.evaluate(torch.ones(4,2))),
        lambda: checked(float(problem._objective_func(torch.zeros(1,3))[0]) == 0., {"zero_objective":0.}),
        lambda: checked(bool(torch.isfinite(evaluated(2048).evals).all()), {"batch":2048}),
    )


@register("datasketch", "datasketch.MinHash.update/jaccard", "token streams -> probabilistic set sketches", "overlap similarity", "remain legacy-unclassified; demote if sketch similarity/control/empty identity or larger sketches fail", role="legacy_unclassified", support=True)
def probe_datasketch():
    from datasketch import MinHash
    def sketch(items,n=128):
        m=MinHash(num_perm=n,seed=7)
        for x in items: m.update(str(x).encode())
        return m
    return four(
        lambda: checked(sketch(range(100)).jaccard(sketch(range(50,150))) > .2, {"overlap_detected":True}),
        lambda: checked(sketch(range(100)).jaccard(sketch(range(100,200))) < .1, {"disjoint_control":True}),
        lambda: checked(sketch([]).jaccard(sketch([])) == 1., {"empty_identity":True}),
        lambda: checked(sketch(range(10000),256).jaccard(sketch(range(5000,15000),256)) > .2, {"items":15000,"permutations":256}),
    )


@register("pymoo", "pymoo.problems.get_problem/evaluate", "decision matrix -> multiobjective benchmark evaluation", "ZDT1 benchmark", "remain legacy-unclassified; demote if evaluation, wrong-width control, boundary, or large population fails", role="legacy_unclassified", support=True)
def probe_pymoo():
    import numpy as np
    from pymoo.problems import get_problem
    problem=get_problem("zdt1",n_var=8)
    return four(
        lambda: checked(problem.evaluate(np.full((16,8),.5)).shape == (16,2), {"population":16,"objectives":2}),
        lambda: expect_raises(Exception, lambda: problem.evaluate(np.ones((4,7)))),
        lambda: checked(np.allclose(problem.evaluate(np.zeros((1,8))),np.array([[0.,1.]])), {"zero_boundary":[0.,1.]}),
        lambda: checked(np.isfinite(problem.evaluate(np.random.default_rng(0).uniform(size=(10000,8)))).all(), {"population":10000}),
    )


@register("hypothesis", "hypothesis.find/strategies", "declarative generators -> shrinking counterexample search", "integer and list strategies", "remain legacy-unclassified; demote if generation, impossible-search control, boundary shrink, or composite search fails", role="control_only", support=True)
def probe_hypothesis():
    from hypothesis import find, strategies as st
    from hypothesis.errors import NoSuchExample
    return four(
        lambda: checked(find(st.integers(),lambda x:x>100) == 101, {"minimal_gt_100":101}),
        lambda: expect_raises(NoSuchExample, lambda: find(st.integers(min_value=0,max_value=10),lambda x:x>100)),
        lambda: checked(find(st.lists(st.integers(),max_size=5),lambda x:len(x)==0) == [], {"empty_shrink":True}),
        lambda: checked(sum(find(st.lists(st.integers(0,10),min_size=64,max_size=64),lambda x:sum(x)>=64)) >= 64, {"list_size":64}),
    )


@register("optuna", "optuna.create_study/Study.optimize", "objective trials -> adaptive hyperparameter search", "one-dimensional quadratic", "remain legacy-unclassified; demote if optimization, invalid-direction control, fixed boundary, or repeated trials fail", role="legacy_unclassified", support=True)
def probe_optuna():
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    def study(n=32):
        s=optuna.create_study(direction="minimize",sampler=optuna.samplers.TPESampler(seed=7)); s.optimize(lambda t:(t.suggest_float("x",-5,5)-1.5)**2,n_trials=n); return s
    return four(
        lambda: checked(study().best_value < .2, {"best_value":study().best_value}),
        lambda: expect_raises(Exception, lambda: optuna.create_study(direction="sideways")),
        lambda: checked((lambda s:(s.enqueue_trial({"x":1.5}),s.optimize(lambda t:(t.suggest_float("x",1.5,1.5)-1.5)**2,n_trials=1),s.best_value))(optuna.create_study(direction="minimize"))[2] == 0., {"fixed_boundary":True}),
        lambda: checked(study(256).trials.__len__() == 256, {"trials":256}),
    )


@register("hdbscan", "hdbscan.HDBSCAN.fit_predict", "point cloud -> density clustering", "two separated Gaussian clusters", "remain legacy-unclassified; demote if cluster recovery, noise control, minimal-input boundary, or larger dataset fails", role="legacy_unclassified", support=True)
def probe_hdbscan():
    import hdbscan
    import numpy as np
    rng=np.random.default_rng(7)
    data=np.r_[rng.normal(-3,.2,(64,2)),rng.normal(3,.2,(64,2))]
    return four(
        lambda: checked(len(set(hdbscan.HDBSCAN(min_cluster_size=8).fit_predict(data))-{ -1}) == 2, {"clusters":2}),
        lambda: checked(np.all(hdbscan.HDBSCAN(min_cluster_size=8).fit_predict(np.zeros((64,2))) == -1), {"degenerate_cloud_is_noise":True}),
        lambda: expect_raises(Exception, lambda: hdbscan.HDBSCAN(min_cluster_size=2).fit_predict(np.zeros((1,2)))),
        lambda: checked(hdbscan.HDBSCAN(min_cluster_size=15).fit_predict(np.r_[rng.normal(-3,.3,(2500,4)),rng.normal(3,.3,(2500,4))]).shape == (5000,), {"points":5000}),
    )


@register("umap", "umap.UMAP.fit_transform/transform", "high-dimensional point cloud -> learned neighborhood embedding", "two-cluster dimensionality reduction", "remain legacy-unclassified; demote if embedding/invalid-neighbor control/small boundary or larger transform fails", role="legacy_unclassified", support=True)
def probe_umap():
    import numpy as np
    import umap
    rng=np.random.default_rng(7)
    data=np.r_[rng.normal(-2,.3,(64,8)),rng.normal(2,.3,(64,8))]
    return four(
        lambda: checked(umap.UMAP(n_neighbors=10,n_components=2,n_epochs=30,random_state=7,n_jobs=1).fit_transform(data).shape == (128,2), {"points":128,"dimensions":2}),
        lambda: expect_raises(Exception, lambda: umap.UMAP(n_neighbors=1).fit_transform(data)),
        lambda: checked(umap.UMAP(n_neighbors=2,n_components=2,n_epochs=10,init="random",random_state=7,n_jobs=1).fit_transform(data[:3]).shape == (3,2), {"points":3}),
        lambda: checked(umap.UMAP(n_neighbors=15,n_components=3,n_epochs=40,random_state=7,n_jobs=1).fit_transform(rng.normal(size=(2000,16))).shape == (2000,3), {"points":2000,"input_dim":16}),
    )


def build_row(tool: str) -> dict[str, Any]:
    spec=SPECS[tool]
    warnings_seen: list[str] = []
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            metadata=package_metadata(tool)
            cases_factory=spec.factory()
            cases={name:run_case(cases_factory[name]) for name in CASE_NAMES}
            warnings_seen=[f"{type(w.message).__name__}: {w.message}"[:1000] for w in caught]
    except BaseException as exc:
        try:
            metadata=package_metadata(tool)
        except BaseException as meta_exc:
            metadata={"import_name":IMPORT_NAMES.get(tool,tool),"distribution":DIST_NAMES.get(tool,tool),"version":None,"module_file":None,"metadata_error":f"{type(meta_exc).__name__}: {meta_exc}"}
        failure={
            "pass":False,
            "detail":None,
            "error":{"type":type(exc).__name__,"message":str(exc)[:1000],"traceback":traceback.format_exc(limit=8)},
            "duration_seconds":0.0,
        }
        cases={name:dict(failure) for name in CASE_NAMES}
    demotion = {
        "passed": bool(cases["negative"]["pass"] and spec.demotion_condition),
        "method": "executed negative/failure control bound to the declared demotion condition",
        "condition": spec.demotion_condition,
        "qualified_api": spec.qualified_api,
        "observed": cases["negative"].get("detail"),
        "error": cases["negative"].get("error"),
    }
    tool_calls = [
        {
            "tool": tool,
            "qualified_api": spec.qualified_api,
            "probe_function": spec.factory.__name__,
            "executed": True,
            "load_bearing": True,
            "raw_probe_recorded": True,
            "input_object": {
                "representative_fixture": spec.representative_fixture,
                "case_ids": list(CASE_NAMES),
            },
            "output_object": {
                name: {
                    "passed": bool(cases[name]["pass"]),
                    "detail": cases[name].get("detail"),
                    "error": cases[name].get("error"),
                }
                for name in CASE_NAMES
            },
            "case_bindings": {
                name: {"passed": bool(cases[name]["pass"]), "duration_seconds": cases[name].get("duration_seconds")}
                for name in CASE_NAMES
            },
            "gates": [*CASE_NAMES, "demotion", "adjacent_edge"],
        }
    ]
    return {
        "tool":tool,
        **metadata,
        "membership":membership(tool),
        "integration_role":spec.integration_role,
        "support_bucket":spec.support_bucket,
        "control_bucket":spec.control_bucket,
        "qualified_api":spec.qualified_api,
        "adjacent_edge":spec.adjacent_edge,
        "representative_fixture":spec.representative_fixture,
        "demotion_condition":spec.demotion_condition,
        "demotion":demotion,
        "tool_calls":tool_calls,
        "cases":cases,
        "warnings":warnings_seen,
        "operational_pass":all(cases[name]["pass"] for name in CASE_NAMES) and demotion["passed"],
    }


def validate_roster() -> tuple[str, ...]:
    roster=CURRENT_CORE+CURRENT_OPTIONAL_AVAILABLE+ADMITTED_QUARANTINED+LEGACY_UNCLASSIFIED
    if len(CURRENT_CORE) != 50 or len(CURRENT_OPTIONAL_AVAILABLE) != 8 or len(ADMITTED_QUARANTINED) != 1 or len(LEGACY_UNCLASSIFIED) != 9:
        raise RuntimeError("roster cardinality contract is not 50+8+1+9")
    if len(roster) != len(set(roster)):
        raise RuntimeError("roster contains duplicates")
    missing=sorted(set(roster)-set(SPECS)); extra=sorted(set(SPECS)-set(roster))
    if missing or extra:
        raise RuntimeError(f"probe registry mismatch missing={missing} extra={extra}")
    return roster


def make_receipt(rows: list[dict[str, Any]], argv: list[str]) -> dict[str, Any]:
    from datetime import datetime, timezone
    source=Path(__file__).resolve()
    canonical_launcher=Path.home()/".local/share/sim-stack/bin/python3"
    memberships={name:{"rows":0,"operational_pass":0,"operational_fail":0} for name in ("current_core","current_optional_available","admitted_quarantined_surface","legacy_unclassified")}
    case_pass={name:0 for name in CASE_NAMES}; case_fail={name:0 for name in CASE_NAMES}
    for row in rows:
        bucket=memberships[row["membership"]]; bucket["rows"] += 1; bucket["operational_pass" if row["operational_pass"] else "operational_fail"] += 1
        for name in CASE_NAMES: (case_pass if row["cases"][name]["pass"] else case_fail)[name] += 1
    operational=sum(row["operational_pass"] for row in rows)
    compat_source=source.parent/"python_compat.py"
    return {
        "schema":"codex-ratchet.python-core-deep-stress.v1",
        "name":"python_core_deep_stress_20260714",
        "classification":"integration_diagnostic",
        "promotion_allowed":False,
        "formal_admission_allowed":False,
        "science_claim_allowed":False,
        "claim_ceiling":"Operational integration stress only. Passing rows do not validate Ratchet/QIT engines, promote simulations, prove mathematical claims, or establish scientific canon.",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "source":{"path":str(source.relative_to(REPO_ROOT)),"absolute_path":str(source),"sha256":hashlib.sha256(source.read_bytes()).hexdigest()},
        "support_sources":[{"path":str(compat_source.relative_to(REPO_ROOT)),"absolute_path":str(compat_source),"sha256":hashlib.sha256(compat_source.read_bytes()).hexdigest(),"role":"bounded optional-package compatibility adapters"}],
        "invocation":{"argv":argv,"command":shlex.join([sys.executable,*argv])},
        "runtime":{
            "executable":sys.executable,
            "real_executable":os.path.realpath(sys.executable),
            "canonical_launcher":str(canonical_launcher),
            "canonical_launcher_exists":canonical_launcher.exists(),
            "canonical_launcher_realpath":os.path.realpath(canonical_launcher),
            "canonical_launcher_matches_runtime":os.path.realpath(canonical_launcher) == os.path.realpath(sys.executable),
            "prefix":sys.prefix,
            "base_prefix":sys.base_prefix,
            "python_version":sys.version,
            "python_implementation":platform.python_implementation(),
            "platform":platform.platform(),
            "machine":platform.machine(),
            "environment":{name:os.environ.get(name) for name in ("JAX_ENABLE_X64","GEOMSTATS_BACKEND","NUMBA_CACHE_DIR","PYTHONDONTWRITEBYTECODE")},
        },
        "roster":{
            "current_core":list(CURRENT_CORE),
            "current_optional_available":list(CURRENT_OPTIONAL_AVAILABLE),
            "admitted_quarantined_surface":list(ADMITTED_QUARANTINED),
            "legacy_unclassified":list(LEGACY_UNCLASSIFIED),
            "counts":{"current_core":50,"current_optional_available":8,"admitted_quarantined_surface":1,"legacy_unclassified":9,"total":68},
        },
        "rows":rows,
        "summary":{
            "rows_total":len(rows),
            "operational_pass":operational,
            "operational_fail":len(rows)-operational,
            "case_pass_counts":case_pass,
            "case_fail_counts":case_fail,
            "by_membership":memberships,
            "all_operational_pass":operational == len(rows),
        },
        "all_pass":operational == len(rows),
    }


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True,help="receipt JSON path")
    args=parser.parse_args(argv)
    raw_argv=list(sys.argv if argv is None else [Path(__file__).name,*argv])
    try:
        roster=validate_roster()
        rows=[]
        for index,tool in enumerate(roster,1):
            print(f"[{index:02d}/{len(roster)}] {tool}",flush=True)
            rows.append(build_row(tool))
        receipt=make_receipt(rows,raw_argv)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(receipt,indent=2,sort_keys=False)+"\n")
        print(json.dumps(receipt["summary"],indent=2),flush=True)
        print(f"receipt={args.output}",flush=True)
        return 0
    except BaseException as exc:
        print(f"HARNESS_FAILURE {type(exc).__name__}: {exc}",file=sys.stderr)
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
