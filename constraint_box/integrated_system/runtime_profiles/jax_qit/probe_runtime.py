from __future__ import annotations

import importlib
import json
import math
import os
import traceback
from pathlib import Path


rows: dict[str, dict[str, object]] = {}


def run(name, fn):
    try:
        value = fn()
        rows[name] = {"status": "PASS", "result": value}
    except BaseException as exc:
        rows[name] = {
            "status": "FAIL",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "trace_tail": traceback.format_exc().splitlines()[-4:],
        }


import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp


def jax_core():
    batch = jnp.arange(8.0, dtype=jnp.float64)
    observed = jax.jit(jax.vmap(lambda x: x * x + 1.0))(batch)
    return {
        "jax": jax.__version__,
        "jaxlib": jax.lib.__version__,
        "x64": bool(jax.config.jax_enable_x64),
        "device": str(jax.devices()[0]),
        "sum": float(jnp.sum(observed)),
    }


def qutip_qit():
    import qutip as qt
    import qutip_jax
    psi = jnp.asarray([1.0, 1.0j], dtype=jnp.complex128) / jnp.sqrt(2.0)
    rho = jnp.outer(psi, jnp.conj(psi))
    qobj = qt.Qobj(rho)
    entropy = float(qt.entropy_vn(qobj, base=2))
    bad_trace = abs(complex(qt.Qobj(1.1 * rho).tr()).real - 1.0) > 1e-6
    negative = rho + jnp.asarray([[-2.0, 0.0], [0.0, 2.0]], dtype=jnp.complex128)
    bad_eigen = min(float(v.real) for v in qt.Qobj(negative).eigenenergies()) < 0.0
    backend = type(qobj.data).__module__ + "." + type(qobj.data).__name__
    assert "qutip_jax" in backend and bad_trace and bad_eigen
    return {"version": qt.__version__, "backend": backend, "entropy_bits": entropy}


def dynamiqs_qit():
    import dynamiqs as dq
    sample = jnp.asarray([[0.5, 0.5j], [-0.5j, 0.5]], dtype=jnp.complex128)
    times = jnp.linspace(0.0, 0.5, 6)
    result = dq.mesolve(
        0.5 * dq.sigmax(),
        [jnp.sqrt(0.2) * dq.sigmaz()],
        dq.asqarray(sample),
        times,
        method=dq.method.Tsit5(rtol=1e-10, atol=1e-12),
    )
    states = result.states.to_jax()
    trace_error = float(jnp.max(jnp.abs(jnp.trace(states, axis1=-2, axis2=-1) - 1.0)))
    minimum_eigenvalue = float(jnp.min(jnp.linalg.eigvalsh(states)))
    assert trace_error < 1e-8 and minimum_eigenvalue > -1e-8
    return {"version": dq.__version__, "trace_error": trace_error, "minimum_eigenvalue": minimum_eigenvalue}


def quimb_tensor():
    import quimb
    import quimb.tensor as qtn
    mps = qtn.MPS_computational_state("0000")
    norm = complex(mps.H @ mps).real
    assert abs(norm - 1.0) < 1e-12
    return {"version": quimb.__version__, "sites": mps.nsites, "norm": norm}


def stim_stabilizer():
    import stim
    circuit = stim.Circuit("H 0\nCX 0 1\nM 0 1")
    samples = circuit.compile_sampler(seed=7).sample(shots=32)
    parity = (samples[:, 0] == samples[:, 1]).all().item()
    refused = False
    try:
        stim.Circuit("NOT_A_GATE 0")
    except ValueError:
        refused = True
    assert parity and refused
    return {"version": stim.__version__, "shots": 32, "correlated": parity, "invalid_refused": refused}


def netket_finite():
    import netket as nk
    hilbert = nk.hilbert.Spin(s=0.5, N=2)
    states = hilbert.all_states()
    assert states.shape == (4, 2)
    return {"version": nk.__version__, "n_states": int(states.shape[0])}


def diffrax_dynamics():
    import diffrax
    term = diffrax.ODETerm(lambda t, y, args: -y)
    solution = diffrax.diffeqsolve(
        term,
        diffrax.Tsit5(),
        t0=0.0,
        t1=1.0,
        dt0=0.05,
        y0=jnp.asarray(1.0, dtype=jnp.float64),
        saveat=diffrax.SaveAt(t1=True),
    )
    value = float(solution.ys[0])
    assert abs(value - math.exp(-1.0)) < 1e-5
    return {"version": diffrax.__version__, "y1": value}


def lie_spinor_support():
    import jaxlie
    import e3nn_jax as e3nn
    matrix = jaxlie.SO3.from_x_radians(jnp.asarray(0.25)).as_matrix()
    orthogonality = float(jnp.max(jnp.abs(matrix.T @ matrix - jnp.eye(3))))
    irreps = e3nn.Irreps("1x0e + 1x1o")
    assert orthogonality < 1e-12 and irreps.dim == 4
    return {"so3_orthogonality_error": orthogonality, "irreps_dim": irreps.dim}


def optimization_sampling():
    import optax
    import numpyro.distributions as dist
    params = jnp.asarray([2.0, -1.0])
    grads = 2.0 * params
    updates, _ = optax.sgd(0.1).update(grads, optax.sgd(0.1).init(params))
    changed = optax.apply_updates(params, updates)
    log_prob = float(dist.Normal(0.0, 1.0).log_prob(jnp.asarray(0.0)))
    assert float(jnp.linalg.norm(changed)) < float(jnp.linalg.norm(params))
    return {"updated_norm": float(jnp.linalg.norm(changed)), "normal_log_prob_zero": log_prob}


def topology_graphs():
    import rustworkx as rx
    import gudhi
    import networkx as nx
    import xgi
    import toponetx as tnx
    graph = rx.PyGraph()
    graph.add_nodes_from(range(4))
    graph.add_edges_from_no_data([(0, 1), (2, 3)])
    components = sorted(len(c) for c in rx.connected_components(graph))
    simplex = gudhi.SimplexTree()
    simplex.insert([0, 1, 2])
    betti_ready = simplex.num_simplices()
    hyper = xgi.Hypergraph([[0, 1, 2], [2, 3]])
    complex_ = tnx.SimplicialComplex([[0, 1, 2]])
    nx_components = nx.number_connected_components(nx.Graph([(0, 1), (2, 3)]))
    assert components == [2, 2] and betti_ready == 7 and nx_components == 2
    return {"rustworkx_components": components, "simplices": betti_ready, "hyperedges": hyper.num_edges, "toponetx_shape": list(complex_.shape)}


def formal_controls():
    import z3
    import cvc5
    import sympy as sp
    x = z3.Int("x")
    z = z3.Solver(); z.add(x == 2, x > 1)
    z_erased = z3.Solver(); z_erased.add(x == 2, x < 1)
    solver = cvc5.Solver(); solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort(); y = solver.mkConst(integer, "y")
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, y, solver.mkInteger(2)))
    a = sp.Matrix([[0, 1], [1, 0]]); b = sp.Matrix([[1, 0], [0, -1]])
    commutator = a * b - b * a
    assert z.check() == z3.sat and z_erased.check() == z3.unsat and solver.checkSat().isSat() and commutator != sp.zeros(2)
    return {"z3_real": "sat", "z3_erased": "unsat", "cvc5": "sat", "sympy_commutator": str(commutator)}


def clifford_control():
    from clifford import Cl
    layout, blades = Cl(2)
    e1 = blades["e1"]
    square = e1 * e1
    assert abs(float(square.value[0]) - 1.0) < 1e-12
    return {"e1_square_scalar": float(square.value[0])}


for name, fn in (
    ("jax_core", jax_core),
    ("qutip_jax", qutip_qit),
    ("dynamiqs", dynamiqs_qit),
    ("quimb", quimb_tensor),
    ("stim", stim_stabilizer),
    ("netket", netket_finite),
    ("diffrax", diffrax_dynamics),
    ("jaxlie_e3nn", lie_spinor_support),
    ("optax_numpyro", optimization_sampling),
    ("topology", topology_graphs),
    ("formal", formal_controls),
    ("clifford", clifford_control),
):
    run(name, fn)

body = {
    "schema": "generic.jax-qit-runtime-probe.v1",
    "python": __import__("sys").version,
    "prefix": __import__("sys").prefix,
    "results": rows,
    "passed": sum(1 for row in rows.values() if row["status"] == "PASS"),
    "failed": sum(1 for row in rows.values() if row["status"] == "FAIL"),
}
rendered = json.dumps(body, indent=2, sort_keys=True) + "\n"
if os.environ.get("JAX_QIT_PROBE_OUTPUT"):
    Path(os.environ["JAX_QIT_PROBE_OUTPUT"]).write_text(rendered, encoding="utf-8")
print(rendered, end="")
raise SystemExit(0 if body["failed"] == 0 else 2)
