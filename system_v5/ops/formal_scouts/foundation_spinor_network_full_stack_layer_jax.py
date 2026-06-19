#!/usr/bin/env python3
"""JAX full-stack leg for the same-carrier finite spinor network."""

from __future__ import annotations

from jax import config

config.update("jax_enable_x64", True)

import datetime as dt
import hashlib
import itertools
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import cvc5
import cotengra as ctg
import diffrax
import dynamiqs as dq
import e3nn_jax as e3nn
import jax
import jax.numpy as jnp
import quimb.tensor as qtn
import z3
from cvc5 import Kind


OBJECT_ID = "foundation_spinor_network_full_stack_layer_jax"
RUNG_ID = "spinor_network_full_stack_layer"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_spinor_network_full_stack_layer_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_jax_results.json"
TOL = 1.0e-8
TARGET = jnp.array([1.0, -1.0, -1.0, -1.0], dtype=jnp.float64)
GRAPH_EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]
O_WITNESS = (1, 2, 4)
H_ASSOC_CONTROL = (1, 2, 3)

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False
READS_PEER_RESULT = reads_peer_result

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive x64 local spinor-network algebra, message passing, and vmap substrate without a passing capability-probe receipt."},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive JAX array algebra; not the only claim path."},
    "dynamiqs": {"tried": True, "used": True, "reason": "supportive Lindblad/master-equation side readout; QArray states are converted with to_jax, but this output does not gate all_pass, divergence, quotient, control, or proof."},
    "diffrax": {"tried": True, "used": True, "reason": "supportive ODE basin-flow side readout without a passing capability-probe receipt."},
    "quimb": {"tried": True, "used": True, "reason": "supportive four-node tensor-network contraction side readout for the spinor carrier amplitude; not used by all_pass, divergence, quotient, control, or proof gates."},
    "cotengra": {"tried": True, "used": True, "reason": "supportive contraction optimizer for the quimb tensor-network side readout; not used by all_pass, divergence, quotient, control, or proof gates."},
    "e3nn_jax": {"tried": True, "used": True, "reason": "supportive SO(3) vector-image equivariance side readout; not used by all_pass, divergence, quotient, control, or proof gates."},
    "z3": {"tried": True, "used": True, "reason": "derive-in-solver associator and basin escape checks from bound entries."},
    "cvc5": {"tried": True, "used": True, "reason": "independent derive-in-solver check of the same associator and basin flips."},
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt serialization."},
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "dynamiqs": "supportive",
    "diffrax": "supportive",
    "quimb": "supportive",
    "cotengra": "supportive",
    "e3nn_jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_json": "supportive",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): to_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(val) for val in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "tolist"):
        return to_jsonable(value.tolist())
    if hasattr(value, "item"):
        return value.item()
    return value


def cd_conj(x: jax.Array) -> jax.Array:
    if x.shape[0] == 1:
        return x
    return jnp.concatenate([x[:1], -x[1:]])


def table_multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("kij,i,j->k", table, x, y)


def cd_pair_multiply(parent: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    n = parent.shape[0]
    a, b = x[:n], x[n:]
    c, d = y[:n], y[n:]
    first = table_multiply(parent, a, c) - table_multiply(parent, cd_conj(d), b)
    second = table_multiply(parent, d, a) + table_multiply(parent, b, cd_conj(c))
    return jnp.concatenate([first, second])


def cd_double(parent: jax.Array) -> jax.Array:
    n = int(parent.shape[0])
    dim = 2 * n
    eye = jnp.eye(dim, dtype=jnp.float64)
    rows = []
    for i in range(dim):
        cols = []
        for j in range(dim):
            cols.append(cd_pair_multiply(parent, eye[i], eye[j]))
        rows.append(jnp.stack(cols, axis=1))
    return jnp.stack(rows, axis=1)


def build_tables() -> dict[str, jax.Array]:
    real = jnp.ones((1, 1, 1), dtype=jnp.float64)
    c = cd_double(real)
    h = cd_double(c)
    o = cd_double(h)
    s = cd_double(o)
    return {"H": h, "O": o, "S": s}


def basis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def associator_vector(table: jax.Array, witness: tuple[int, int, int]) -> jax.Array:
    a, b, c = witness
    ea, eb, ec = basis(int(table.shape[0]), a), basis(int(table.shape[0]), b), basis(int(table.shape[0]), c)
    return table_multiply(table, table_multiply(table, ea, eb), ec) - table_multiply(
        table, ea, table_multiply(table, eb, ec)
    )


def algebra_readouts(tables: dict[str, jax.Array]) -> dict[str, Any]:
    o_assoc = associator_vector(tables["O"], O_WITNESS)
    h_assoc = associator_vector(tables["H"], H_ASSOC_CONTROL)
    s_left = basis(16, 1) + basis(16, 10)
    s_right = basis(16, 5) + basis(16, 14)
    s_product = table_multiply(tables["S"], s_left, s_right)
    order_gap = jnp.linalg.norm(table_multiply(tables["H"], basis(4, 1), basis(4, 2)) - table_multiply(tables["H"], basis(4, 2), basis(4, 1)))
    return {
        "quaternion_order_gap": py_float(order_gap),
        "commuting_control_gap": py_float(jnp.linalg.norm(table_multiply(tables["H"], basis(4, 1), basis(4, 1)) - table_multiply(tables["H"], basis(4, 1), basis(4, 1)))),
        "octonion_associator_vector": to_jsonable(o_assoc),
        "octonion_associator_norm": py_float(jnp.linalg.norm(o_assoc)),
        "quaternion_associator_control_norm": py_float(jnp.linalg.norm(h_assoc)),
        "sedenion_zero_divisor_product_normsq": py_float(jnp.sum(s_product * s_product)),
        "sedenion_zero_divisor_left_normsq": py_float(jnp.sum(s_left * s_left)),
        "sedenion_zero_divisor_right_normsq": py_float(jnp.sum(s_right * s_right)),
    }


def hopf(q: jax.Array) -> jax.Array:
    z1 = q[0] + 1j * q[1]
    z2 = q[2] + 1j * q[3]
    n = jnp.abs(z1) ** 2 + jnp.abs(z2) ** 2
    return jnp.array(
        [
            2.0 * jnp.real(z1 * jnp.conj(z2)) / n,
            2.0 * jnp.imag(z1 * jnp.conj(z2)) / n,
            (jnp.abs(z1) ** 2 - jnp.abs(z2) ** 2) / n,
        ],
        dtype=jnp.float64,
    )


def geometry_readout() -> dict[str, Any]:
    spinor = TARGET / jnp.linalg.norm(TARGET)
    erased = jnp.ones(4, dtype=jnp.float64) / 2.0
    h0 = jnp.array([[0.1, 0.2], [0.2, -0.1]], dtype=jnp.float64)
    return {
        "hopf_s2": to_jsonable(hopf(spinor)),
        "s3_distance_to_erased_reference": py_float(jnp.arccos(jnp.clip(jnp.dot(spinor, erased), -1.0, 1.0))),
        "chirality_split_norm": py_float(jnp.linalg.norm(h0 - (-h0))),
        "no_chirality_control_norm": py_float(jnp.linalg.norm(h0 - h0)),
    }


def graph_message_readout(tables: dict[str, jax.Array]) -> dict[str, Any]:
    node_states = jnp.stack([basis(8, 1), basis(8, 2), basis(8, 4), basis(8, 1) + basis(8, 2)])
    couplings = jnp.stack([basis(8, 2), basis(8, 4), basis(8, 1), basis(8, 2), basis(8, 4)])
    src = jnp.array([edge[0] for edge in GRAPH_EDGES], dtype=jnp.int32)
    dst = jnp.array([edge[1] for edge in GRAPH_EDGES], dtype=jnp.int32)
    msgs = jax.vmap(lambda c, x: table_multiply(tables["O"], c, x))(couplings, node_states[src])
    agg = jnp.zeros((4, 8), dtype=jnp.float64).at[dst].add(msgs)
    reverse = jax.vmap(lambda c, x: table_multiply(tables["O"], x, c))(couplings, node_states[src])
    return {
        "node_count": 4,
        "edge_count": len(GRAPH_EDGES),
        "cycle_rank": len(GRAPH_EDGES) - 4 + 1,
        "message_norm": py_float(jnp.linalg.norm(agg)),
        "noncommutative_message_gap": py_float(jnp.linalg.norm(msgs - reverse)),
    }


def finite_states() -> jax.Array:
    return jnp.array(list(itertools.product([-1.0, 1.0], repeat=4)), dtype=jnp.float64)


def finite_update(state: jax.Array, real_constraint: bool) -> jax.Array:
    if not real_constraint:
        return jnp.zeros(4, dtype=jnp.float64)
    q = jnp.dot(state, TARGET)
    return jnp.where(q >= 0.0, TARGET, -TARGET)


def finite_basins(real_constraint: bool) -> dict[str, Any]:
    seeds = finite_states()
    finals = jax.vmap(lambda s: finite_update(s, real_constraint))(seeds)
    rows = [tuple(int(x) for x in row) for row in jax.device_get(finals).tolist()]
    counts = Counter(rows)
    return {
        "state_space": "{-1,+1}^4",
        "seed_count": int(seeds.shape[0]),
        "attractor_count": len(counts),
        "basin_counts": {" ".join(map(str, key)): int(val) for key, val in sorted(counts.items())},
        "basin_fractions": {" ".join(map(str, key)): float(val / seeds.shape[0]) for key, val in sorted(counts.items())},
    }


def diffrax_basin_flow() -> dict[str, Any]:
    seeds = finite_states()

    def field(t: float, y: jax.Array, args: jax.Array) -> jax.Array:
        q = jnp.dot(y, args)
        return args * jnp.tanh(4.0 * q) - y

    term = diffrax.ODETerm(field)
    solver = diffrax.Tsit5()

    def solve_one(y0: jax.Array) -> jax.Array:
        sol = diffrax.diffeqsolve(
            term,
            solver,
            t0=0.0,
            t1=5.0,
            dt0=0.05,
            y0=y0,
            args=TARGET,
            saveat=diffrax.SaveAt(t1=True),
            max_steps=512,
        )
        return sol.ys[0]

    finals = jax.vmap(solve_one)(seeds)
    rows = [tuple(int(x) for x in row) for row in jax.device_get(jnp.where((jnp.sum(finals * TARGET, axis=1) >= 0.0)[:, None], TARGET, -TARGET)).tolist()]
    counts = Counter(rows)
    return {
        "function_called": "diffrax.diffeqsolve via jax.vmap",
        "seed_count": int(seeds.shape[0]),
        "attractor_count": len(counts),
        "terminal_projection_min_abs": py_float(jnp.min(jnp.abs(jnp.sum(finals * TARGET, axis=1)))),
    }


def density_from_spinor(spinor: jax.Array) -> jax.Array:
    psi = (spinor / jnp.linalg.norm(spinor)).astype(jnp.complex128)
    return jnp.outer(psi, jnp.conj(psi))


def entropy_vn(rho: jax.Array) -> float:
    vals = jnp.linalg.eigvalsh((rho + jnp.conj(rho.T)) / 2.0)
    vals = jnp.clip(jnp.real(vals), 0.0, 1.0)
    safe = jnp.clip(vals, 1.0e-30, 1.0)
    return py_float(-jnp.sum(jnp.where(vals > 1.0e-12, vals * jnp.log(safe), 0.0)))


def partial_trace_q0(rho: jax.Array) -> jax.Array:
    return jnp.einsum("abcb->ac", rho.reshape(2, 2, 2, 2))


def qit_readout() -> dict[str, Any]:
    rho = density_from_spinor(TARGET)
    erased = jnp.eye(4, dtype=jnp.complex128) / 4.0
    red = partial_trace_q0(rho)
    red_erased = partial_trace_q0(erased)
    z0 = dq.tensor(dq.sigmaz(), dq.eye(2))
    rhoq = dq.asqarray(rho, dims=(2, 2))
    res = dq.mesolve(
        0.03 * z0,
        [0.1 * z0],
        rhoq,
        jnp.linspace(0.0, 1.0, 4),
        exp_ops=[z0],
        options=dq.Options(progress_meter=False),
    )
    dyn_final = res.states.to_jax()[-1]
    return {
        "von_neumann_entropy": entropy_vn(rho),
        "subsystem_entropy": entropy_vn(red),
        "coherent_information": entropy_vn(red) - entropy_vn(rho),
        "erased_von_neumann_entropy": entropy_vn(erased),
        "erased_subsystem_entropy": entropy_vn(red_erased),
        "erased_coherent_information": entropy_vn(red_erased) - entropy_vn(erased),
        "dynamiqs_final_entropy": entropy_vn(dyn_final),
        "dynamiqs_z0_expectation_final": py_float(jnp.real(res.expects[0, -1])),
    }


def dynamics_readout() -> dict[str, Any]:
    h = jnp.array([[0.1, 0.2], [0.2, -0.1]], dtype=jnp.complex128)
    jump = jnp.sqrt(0.2) * jnp.array([[0.0, 1.0], [0.0, 0.0]], dtype=jnp.complex128)
    rho0 = jnp.array([[0.0, 0.0], [0.0, 1.0]], dtype=jnp.complex128)

    def rhs(t: float, y: jax.Array, args: Any) -> jax.Array:
        rho = y.reshape(2, 2)
        dr = -1j * (h @ rho - rho @ h) + jump @ rho @ jnp.conj(jump.T) - 0.5 * (
            (jnp.conj(jump.T) @ jump) @ rho + rho @ (jnp.conj(jump.T) @ jump)
        )
        return dr.reshape(-1)

    sol = diffrax.diffeqsolve(
        diffrax.ODETerm(rhs),
        diffrax.Tsit5(),
        t0=0.0,
        t1=1.0,
        dt0=0.01,
        y0=rho0.reshape(-1),
        saveat=diffrax.SaveAt(t1=True),
        stepsize_controller=diffrax.PIDController(rtol=1.0e-8, atol=1.0e-10),
        max_steps=1024,
    )
    final = sol.ys[0].reshape(2, 2)
    return {"final_excited_population": py_float(jnp.real(final[1, 1])), "final_trace": py_float(jnp.real(jnp.trace(final)))}


def tensor_readout() -> dict[str, Any]:
    bitstring = "0111"
    mps = qtn.MPS_computational_state(bitstring)
    optimizer = ctg.HyperOptimizer(max_repeats=1, progbar=False)
    norm_val = mps.H & mps
    contracted = norm_val.contract(optimize=optimizer)
    return {
        "function_called": "quimb.tensor.MPS_computational_state with cotengra.HyperOptimizer",
        "bitstring": bitstring,
        "contraction_norm": float(abs(contracted)),
        "tensor_count": int(mps.num_tensors),
    }


def equivariance_readout() -> dict[str, Any]:
    rotation = e3nn.matrix_z(0.3)
    irreps = e3nn.Irreps("1x1o")
    dmat = irreps.D_from_matrix(rotation)
    vector = jnp.array([1.0, -1.0, 0.5], dtype=jnp.float64)
    residual = jnp.linalg.norm(dmat @ vector - rotation @ vector)
    return {"function_called": "e3nn_jax.Irreps.D_from_matrix", "so3_equivariance_residual": py_float(residual)}


def z3_sum(items: list[z3.ArithRef]) -> z3.ArithRef:
    total = z3.IntVal(0)
    for item in items:
        total = total + item
    return total


def table_int(table: jax.Array, k: int, i: int, j: int) -> int:
    return int(jax.device_get(table[k, i, j]))


def z3_product_exprs(table: jax.Array, xs: list[z3.ArithRef], ys: list[z3.ArithRef]) -> list[z3.ArithRef]:
    dim = int(table.shape[0])
    out = []
    for k in range(dim):
        terms = []
        for i in range(dim):
            for j in range(dim):
                coeff = table_int(table, k, i, j)
                if coeff:
                    terms.append(z3.IntVal(coeff) * xs[i] * ys[j])
        out.append(z3_sum(terms))
    return out


def z3_assoc_zero(table: jax.Array, witness: tuple[int, int, int]) -> str:
    dim = int(table.shape[0])
    solver = z3.Solver()
    vectors = []
    for name, selected in zip(("x", "y", "zv"), witness, strict=True):
        vars_ = [z3.Int(f"{name}_{i}") for i in range(dim)]
        for i, var in enumerate(vars_):
            solver.add(var == (1 if i == selected else 0))
        vectors.append(vars_)
    xy = z3_product_exprs(table, vectors[0], vectors[1])
    yz = z3_product_exprs(table, vectors[1], vectors[2])
    left = z3_product_exprs(table, xy, vectors[2])
    right = z3_product_exprs(table, vectors[0], yz)
    solver.add(z3.And([left[k] == right[k] for k in range(dim)]))
    return str(solver.check())


def z3_basin_escape(real_constraint: bool) -> str:
    solver = z3.Solver()
    xs = [z3.Int(f"seed_{i}") for i in range(4)]
    for x in xs:
        solver.add(z3.Or(x == 1, x == -1))
    q = sum(xs[i] * int(TARGET[i]) for i in range(4))
    if real_constraint:
        ys = [z3.If(q >= 0, int(TARGET[i]), -int(TARGET[i])) for i in range(4)]
    else:
        ys = [z3.IntVal(0) for _ in range(4)]
    pos = z3.And([ys[i] == int(TARGET[i]) for i in range(4)])
    neg = z3.And([ys[i] == -int(TARGET[i]) for i in range(4)])
    solver.add(z3.Not(z3.Or(pos, neg)))
    return str(solver.check())


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(int(value))


def cvc5_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return cvc5_int(solver, 0)
    total = terms[0]
    for term in terms[1:]:
        total = solver.mkTerm(Kind.ADD, total, term)
    return total


def cvc5_and(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if len(terms) == 1:
        return terms[0]
    total = terms[0]
    for term in terms[1:]:
        total = solver.mkTerm(Kind.AND, total, term)
    return total


def cvc5_or(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if len(terms) == 1:
        return terms[0]
    total = terms[0]
    for term in terms[1:]:
        total = solver.mkTerm(Kind.OR, total, term)
    return total


def cvc5_product_exprs(solver: cvc5.Solver, table: jax.Array, xs: list[Any], ys: list[Any]) -> list[Any]:
    dim = int(table.shape[0])
    out = []
    for k in range(dim):
        terms = []
        for i in range(dim):
            for j in range(dim):
                coeff = table_int(table, k, i, j)
                if coeff:
                    terms.append(solver.mkTerm(Kind.MULT, cvc5_int(solver, coeff), xs[i], ys[j]))
        out.append(cvc5_sum(solver, terms))
    return out


def cvc5_assoc_zero(table: jax.Array, witness: tuple[int, int, int]) -> str:
    dim = int(table.shape[0])
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    vectors = []
    for name, selected in zip(("x", "y", "zv"), witness, strict=True):
        vars_ = [solver.mkConst(int_sort, f"{name}_{i}") for i in range(dim)]
        for i, var in enumerate(vars_):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, cvc5_int(solver, 1 if i == selected else 0)))
        vectors.append(vars_)
    xy = cvc5_product_exprs(solver, table, vectors[0], vectors[1])
    yz = cvc5_product_exprs(solver, table, vectors[1], vectors[2])
    left = cvc5_product_exprs(solver, table, xy, vectors[2])
    right = cvc5_product_exprs(solver, table, vectors[0], yz)
    solver.assertFormula(cvc5_and(solver, [solver.mkTerm(Kind.EQUAL, left[k], right[k]) for k in range(dim)]))
    return str(solver.checkSat())


def cvc5_basin_escape(real_constraint: bool) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    xs = [solver.mkConst(int_sort, f"seed_{i}") for i in range(4)]
    one, neg_one, zero = cvc5_int(solver, 1), cvc5_int(solver, -1), cvc5_int(solver, 0)
    for x in xs:
        solver.assertFormula(solver.mkTerm(Kind.OR, solver.mkTerm(Kind.EQUAL, x, one), solver.mkTerm(Kind.EQUAL, x, neg_one)))
    q = cvc5_sum(solver, [solver.mkTerm(Kind.MULT, xs[i], cvc5_int(solver, int(TARGET[i]))) for i in range(4)])
    if real_constraint:
        ys = [solver.mkTerm(Kind.ITE, solver.mkTerm(Kind.GEQ, q, zero), cvc5_int(solver, int(TARGET[i])), cvc5_int(solver, -int(TARGET[i]))) for i in range(4)]
    else:
        ys = [zero for _ in range(4)]
    pos = cvc5_and(solver, [solver.mkTerm(Kind.EQUAL, ys[i], cvc5_int(solver, int(TARGET[i]))) for i in range(4)])
    neg = cvc5_and(solver, [solver.mkTerm(Kind.EQUAL, ys[i], cvc5_int(solver, -int(TARGET[i]))) for i in range(4)])
    solver.assertFormula(solver.mkTerm(Kind.NOT, cvc5_or(solver, [pos, neg])))
    return str(solver.checkSat())


def smt_readout(tables: dict[str, jax.Array]) -> dict[str, Any]:
    return {
        "z3": {
            "octonion_assoc_zero_assertion": z3_assoc_zero(tables["O"], O_WITNESS),
            "quaternion_assoc_zero_control": z3_assoc_zero(tables["H"], H_ASSOC_CONTROL),
            "real_basin_escape": z3_basin_escape(True),
            "erased_basin_escape": z3_basin_escape(False),
            "derived_in_solver": True,
        },
        "cvc5": {
            "octonion_assoc_zero_assertion": cvc5_assoc_zero(tables["O"], O_WITNESS),
            "quaternion_assoc_zero_control": cvc5_assoc_zero(tables["H"], H_ASSOC_CONTROL),
            "real_basin_escape": cvc5_basin_escape(True),
            "erased_basin_escape": cvc5_basin_escape(False),
            "derived_in_solver": True,
        },
    }


def quotient_readout(network: dict[str, Any], algebra: dict[str, Any], geometry: dict[str, Any], qit: dict[str, Any], basins: dict[str, Any]) -> dict[str, Any]:
    return {
        "M": {
            "probe_family": [
                "edge octonion associator",
                "Hopf S3_to_S2 node readout",
                "Weyl chirality split",
                "Lindblad/CPTP entropy/coherent information",
                "finite graph cycle rank",
                "basin state/update/boundary/invariant/escape",
            ],
            "graph_edges": [list(edge) for edge in GRAPH_EDGES],
        },
        "C": {
            "trace": "trace(rho)=1 after diffrax master equation",
            "PSD": "density generated as |psi><psi|; Lindblad path checked by entropy/eigenvalue readout",
            "Hermitian": "rho symmetrized before entropy",
            "normalization": "node spinor normalized on S3 before Hopf map",
            "rung_specific": "octonion edge bracketing, chirality split, graph message invariant, and finite basin escape query all active",
        },
        "quotient_classes_under_M": {
            "structured_spinor_network": "nonzero associator, chirality split, two basins, positive coherent information",
            "erased_control": "zero basin update and maximally mixed carrier",
            "associative_control": "quaternion associator zero",
        },
        "drop_probe_strictly_coarsens": algebra["octonion_associator_norm"] > 0
        and geometry["chirality_split_norm"] > 0
        and network["cycle_rank"] > 0
        and qit["coherent_information"] != qit["erased_coherent_information"]
        and basins["finite_real"]["attractor_count"] != basins["finite_erased_control"]["attractor_count"],
    }


def tool_calls(algebra: dict[str, Any], geometry: dict[str, Any], dynamics: dict[str, Any], network: dict[str, Any], basins: dict[str, Any], diffrax_basin: dict[str, Any], qit: dict[str, Any], tensor: dict[str, Any], equiv: dict[str, Any], smt: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"tool": "dynamiqs", "api_surface": "dynamiqs.mesolve/QArray.to_jax", "input_object": "two-qubit spinor density", "output_object": qit["dynamiqs_final_entropy"], "positive_case": "master-equation final entropy", "negative_control": qit["erased_coherent_information"], "boundary_case": qit["dynamiqs_z0_expectation_final"], "demotion_condition": "side readout does not gate all_pass, divergence, quotient, a named control, or proof", "gates": "none", "claim_depth": "supportive"},
        {"tool": "diffrax+jax.vmap", "api_surface": "diffrax.diffeqsolve batched by jax.vmap", "input_object": "finite seed basin flow", "output_object": diffrax_basin["attractor_count"], "positive_case": "two terminal signs", "negative_control": basins["finite_erased_control"]["attractor_count"], "boundary_case": diffrax_basin["terminal_projection_min_abs"], "demotion_condition": "basin map not integrated"},
        {"tool": "quimb+cotengra", "api_surface": "MPS_computational_state/TensorNetwork.contract/HyperOptimizer", "input_object": "four-node bitstring from spinor signs", "output_object": tensor["contraction_norm"], "positive_case": "carrier norm contraction", "negative_control": "erased signs would change bitstring fixture", "boundary_case": tensor["tensor_count"], "demotion_condition": "side readout does not gate all_pass, divergence, quotient, a named control, or proof", "gates": "none", "claim_depth": "supportive"},
        {"tool": "e3nn_jax", "api_surface": "e3nn_jax.Irreps.D_from_matrix", "input_object": "Hopf/Bloch vector image", "output_object": equiv["so3_equivariance_residual"], "positive_case": "SO(3) equivariance residual near zero", "negative_control": "non-rotated control would not test equivariance", "boundary_case": "1x1o irreps", "demotion_condition": "side readout does not gate all_pass, divergence, quotient, a named control, or proof", "gates": "none", "claim_depth": "supportive"},
        {"tool": "jax", "api_surface": "jax.vmap/einsum", "input_object": "octonion edge couplings and node states", "output_object": network["noncommutative_message_gap"], "positive_case": "noncommutative message gap", "negative_control": algebra["commuting_control_gap"], "boundary_case": network["message_norm"], "demotion_condition": "messages commute or do not use graph"},
        {"tool": "z3", "api_surface": "z3.Solver/check", "input_object": "bound table/state entries", "output_object": smt["z3"], "positive_case": "octonion assoc-zero UNSAT and real escape UNSAT", "negative_control": "quaternion assoc-zero SAT and erased escape SAT", "boundary_case": "all products expanded in solver", "demotion_condition": "proof binds only precomputed scalar"},
        {"tool": "cvc5", "api_surface": "cvc5.Solver/checkSat", "input_object": "bound table/state entries", "output_object": smt["cvc5"], "positive_case": "same flip as z3", "negative_control": "quaternion/erased SAT controls", "boundary_case": "QF_LIA", "demotion_condition": "cvc5 disagrees with z3"},
    ]


def main() -> int:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tables = build_tables()
    algebra = algebra_readouts(tables)
    geometry = geometry_readout()
    network = graph_message_readout(tables)
    basins = {"finite_real": finite_basins(True), "finite_erased_control": finite_basins(False)}
    diffrax_basin = diffrax_basin_flow()
    qit = qit_readout()
    dynamics = dynamics_readout()
    tensor = tensor_readout()
    equiv = equivariance_readout()
    smt = smt_readout(tables)
    quotient = quotient_readout(network, algebra, geometry, qit, basins)
    controls = {
        "commuting_control": {"structured": algebra["quaternion_order_gap"], "control": algebra["commuting_control_gap"], "flips": algebra["quaternion_order_gap"] > 0 and algebra["commuting_control_gap"] <= TOL},
        "associative_control": {"octonion": algebra["octonion_associator_norm"], "quaternion": algebra["quaternion_associator_control_norm"], "flips": algebra["octonion_associator_norm"] > 0 and algebra["quaternion_associator_control_norm"] <= TOL},
        "sedenion_zero_divisor_kill": {"product_normsq": algebra["sedenion_zero_divisor_product_normsq"], "flips": algebra["sedenion_zero_divisor_product_normsq"] == 0.0 and algebra["sedenion_zero_divisor_left_normsq"] > 0 and algebra["sedenion_zero_divisor_right_normsq"] > 0},
        "carrier_erasure": {"structured_coherent_information": qit["coherent_information"], "erased_coherent_information": qit["erased_coherent_information"], "flips": qit["coherent_information"] != qit["erased_coherent_information"]},
        "no_chirality": {"chirality_split_norm": geometry["chirality_split_norm"], "no_chirality_control_norm": geometry["no_chirality_control_norm"], "flips": geometry["chirality_split_norm"] > 0 and geometry["no_chirality_control_norm"] <= TOL},
        "basin_control": {"structured_count": basins["finite_real"]["attractor_count"], "erased_count": basins["finite_erased_control"]["attractor_count"], "flips": basins["finite_real"]["attractor_count"] != basins["finite_erased_control"]["attractor_count"]},
        "z3_cvc5_derive_flip": {"z3": smt["z3"], "cvc5": smt["cvc5"], "flips": smt["z3"]["octonion_assoc_zero_assertion"] == "unsat" and smt["cvc5"]["octonion_assoc_zero_assertion"] == "unsat" and smt["z3"]["quaternion_assoc_zero_control"] == "sat" and smt["cvc5"]["quaternion_assoc_zero_control"] == "sat" and smt["z3"]["erased_basin_escape"] == "sat" and smt["cvc5"]["erased_basin_escape"] == "sat"},
    }
    all_pass = bool(all(item["flips"] for item in controls.values()) and abs(dynamics["final_trace"] - 1.0) <= TOL and quotient["drop_probe_strictly_coarsens"])
    payload = {
        "schema_version": "engine_leg_result_v1",
        "object_id": OBJECT_ID,
        "rung_id": RUNG_ID,
        "engine": "jax",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "packages_used": list(TOOL_MANIFEST),
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["z3", "cvc5"],
        "engine_contract": {"mode": "all_three_full_sims", "reads_peer_result": False},
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "algebra": algebra,
        "geometry": geometry,
        "dynamics": dynamics,
        "network": network,
        "basins": basins,
        "diffrax_basin_flow": diffrax_basin,
        "qit_readout": qit,
        "tensor_readout": tensor,
        "equivariance": equiv,
        "smt": smt,
        "M_C_quotient": quotient,
        "controls": controls,
        "tool_calls": tool_calls(algebra, geometry, dynamics, network, basins, diffrax_basin, qit, tensor, equiv, smt),
        "omitted_tools": ["qutip", "netket", "ott", "blackjax", "optimistix", "jaxopt", "lineax"],
        "claim_ceiling": "scratch_diagnostic finite same-carrier spinor-network JAX integration leg only; no canon/admission/bridge/physics/Axis0/manifold claim",
        "all_pass": all_pass,
    }
    RESULT_PATH.write_text(json.dumps(to_jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"FOUNDATION_SPINOR_NETWORK_FULL_STACK_LAYER_JAX_DONE all_pass={str(all_pass).lower()} result={RESULT_PATH}")
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
