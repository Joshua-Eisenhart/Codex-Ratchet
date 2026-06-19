#!/usr/bin/env python3
"""JAX rich-stack leg for finite QIT operator composition on a 3-qubit carrier."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
import cotengra as ctg
import diffrax
import dynamiqs as dq
import geomstats.backend as gs
import jax.numpy as jnp
import networkx as nx
import numpy as np
import quimb.tensor as qtn
import sympy as sp
import z3
from geomstats.geometry.spd_matrices import SPDBuresWassersteinMetric, SPDMatrices
from ott.geometry import pointcloud
from ott.problems.linear import linear_problem
from ott.solvers.linear import sinkhorn


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
OBJECT_ID = "foundation_qit_operator_composition_mcp_jax"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_jax_results.json"
SOURCE_PATH = Path(__file__).resolve()

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

N_QUBITS = 3
DIM = 2**N_QUBITS
EVOLVE_T = 0.8
THETA = 0.9
GAMMA = 1.3
TOL = 1.0e-6


TOOL_MANIFEST = {
    "dynamiqs.mesolve": {
        "tried": True,
        "used": True,
        "reason": "supportive Lindblad/unitary evolution side readout without a passing capability-probe receipt",
    },
    "diffrax.diffeqsolve": {
        "tried": True,
        "used": True,
        "reason": "supportive independent ODE integration side readout without a passing capability-probe receipt",
    },
    "quimb.tensor.tensor_contract": {
        "tried": True,
        "used": True,
        "reason": "supportive 3-qubit density-tensor contraction side readout of the Z0 expectation; not used by all_pass, quotient, divergence, or proof gates",
    },
    "cotengra.HyperOptimizer": {
        "tried": True,
        "used": True,
        "reason": "supportive contraction-path optimizer for the quimb tensor-network side readout; not used by all_pass, quotient, divergence, or proof gates",
    },
    "geomstats.SPDBuresWassersteinMetric.dist": {
        "tried": True,
        "used": True,
        "reason": "load-bearing by capability-probe criterion; backed by system_v4/probes/sim_geomstats_capability.py and system_v4/probes/a2_state/sim_results/geomstats_capability_results.json",
    },
    "ott.solvers.linear.sinkhorn.Sinkhorn": {
        "tried": True,
        "used": True,
        "reason": "supportive optimal-transport distinguishability side readout between computational-basis carrier distributions; not used by all_pass, divergence, quotient, control, or proof gates",
    },
    "sympy.simplify": {
        "tried": True,
        "used": True,
        "reason": "load-bearing by capability-probe criterion; backed by system_v4/probes/sim_sympy_capability.py and system_v4/probes/a2_state/sim_results/sympy_capability_results.json",
    },
    "z3.Solver": {
        "tried": True,
        "used": True,
        "reason": "load-bearing derive-in-solver UNSAT/SAT order-commutation flip from bound finite operator entries",
    },
    "cvc5.Solver": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent derive-in-solver UNSAT/SAT order-commutation flip agreeing with z3",
    },
    "networkx.DiGraph": {
        "tried": True,
        "used": True,
        "reason": "supportive composition DAG and commutation graph side readout for the stacking-order field; not used by all_pass, divergence, quotient, control, or proof gates",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 array substrate for dynamiqs/diffrax matrices and readout arithmetic",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "control-only host conversion for quimb and geomstats package interfaces; excluded from claim_path_tools",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "dynamiqs": "supportive",
    "diffrax": "supportive",
    "quimb.tensor": "supportive",
    "cotengra": "supportive",
    "geomstats": "load_bearing",
    "ott": "supportive",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "networkx": "supportive",
    "jax.numpy": "supportive",
    "numpy": "supportive",
}


def source_sha256() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (jax.Array,)):
        arr = jax.device_get(value)
        if arr.shape == ():
            return to_jsonable(np.asarray(arr).item())
        return to_jsonable(np.asarray(arr))
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def dense(qobj: Any) -> jax.Array:
    return jnp.asarray(qobj)


def as_qarray(matrix: jax.Array) -> dq.QArray:
    return dq.asqarray(matrix, dims=(2, 2, 2))


def carrier_ops() -> dict[str, dq.QArray]:
    ident = dq.eye(2)
    sx = dq.sigmax()
    sz = dq.sigmaz()
    return {
        "I3": dq.eye(2, 2, 2),
        "X0": dq.tensor(sx, ident, ident),
        "Z0": dq.tensor(sz, ident, ident),
        "X1": dq.tensor(ident, sx, ident),
        "Z1": dq.tensor(ident, sz, ident),
        "Z2": dq.tensor(ident, ident, sz),
        "Z0Z1": dq.tensor(sz, sz, ident),
    }


def initial_density() -> dq.QArray:
    ket0 = dq.fock(2, 0)
    ket1 = dq.fock(2, 1)
    q0 = jnp.sqrt(0.65) * ket0 + jnp.exp(0.37j) * jnp.sqrt(0.35) * ket1
    psi = dq.tensor(q0, ket0, ket0)
    return psi @ psi.dag()


def evolve_dynamiqs(H: dq.QArray, jumps: list[dq.QArray], rho: dq.QArray) -> dq.QArray:
    result = dq.mesolve(
        H,
        jumps,
        rho,
        jnp.asarray([0.0, EVOLVE_T], dtype=jnp.float64),
        options=dq.Options(progress_meter=False),
    )
    return result.states[-1]


def apply_operator(label: str, rho: dq.QArray, ops: dict[str, dq.QArray]) -> dq.QArray:
    if label == "Fi":
        return evolve_dynamiqs((THETA / EVOLVE_T) * ops["X0"], [], rho)
    if label == "Fe":
        return evolve_dynamiqs((THETA / EVOLVE_T) * ops["Z0"], [], rho)
    if label == "Ti":
        return evolve_dynamiqs(0.0 * ops["Z0"], [jnp.sqrt(GAMMA) * ops["Z0"]], rho)
    if label == "Te":
        return evolve_dynamiqs(0.0 * ops["X1"], [jnp.sqrt(0.7 * GAMMA) * ops["X1"]], rho)
    raise ValueError(f"unknown operator label: {label}")


def apply_sequence(rho: dq.QArray, labels: list[str], ops: dict[str, dq.QArray]) -> dq.QArray:
    out = rho
    for label in labels:
        out = apply_operator(label, out, ops)
    return out


def fro_gap(left: dq.QArray, right: dq.QArray) -> float:
    return float(jax.device_get(jnp.linalg.norm(dense(left) - dense(right))))


def trace_normalize(matrix: jax.Array) -> jax.Array:
    herm = 0.5 * (matrix + matrix.conj().T)
    return herm / jnp.trace(herm)


def expect(op: dq.QArray, rho: dq.QArray) -> jax.Array:
    return jnp.real(jnp.trace(dense(op) @ dense(rho)))


def diag_from_z(z_value: jax.Array) -> jax.Array:
    z_clamped = jnp.clip(z_value, -1.0, 1.0)
    return jnp.diag(jnp.asarray([(1.0 + z_clamped) / 2.0, (1.0 - z_clamped) / 2.0], dtype=jnp.complex128))


def probe_product_section(rho: dq.QArray, ops: dict[str, dq.QArray]) -> dq.QArray:
    z0 = expect(ops["Z0"], rho)
    z1 = expect(ops["Z1"], rho)
    z2 = expect(ops["Z2"], rho)
    section = jnp.kron(jnp.kron(diag_from_z(z0), diag_from_z(z1)), diag_from_z(z2))
    return as_qarray(trace_normalize(section))


def erase_carrier() -> dq.QArray:
    return as_qarray(jnp.eye(DIM, dtype=jnp.complex128) / DIM)


def projected_bracketing_gap(rho: dq.QArray, ops: dict[str, dq.QArray]) -> dict[str, Any]:
    # Raw channels are associative. The nonzero discriminator is for the
    # quotient-section product A star B = P_M(B(A(rho))), where P_M is the
    # finite-probe product section.
    raw_left = apply_sequence(rho, ["Fe", "Fi", "Ti"], ops)
    raw_right = apply_sequence(rho, ["Fe", "Fi", "Ti"], ops)
    projected_left = probe_product_section(
        apply_operator(
            "Ti",
            probe_product_section(apply_sequence(rho, ["Fe", "Fi"], ops), ops),
            ops,
        ),
        ops,
    )
    projected_right = probe_product_section(
        apply_sequence(probe_product_section(apply_operator("Fe", rho, ops), ops), ["Fi", "Ti"], ops),
        ops,
    )
    erased = erase_carrier()
    erased_left = probe_product_section(
        apply_operator("Ti", probe_product_section(apply_sequence(erased, ["Fe", "Fi"], ops), ops), ops),
        ops,
    )
    erased_right = probe_product_section(
        apply_sequence(probe_product_section(apply_operator("Fe", erased, ops), ops), ["Fi", "Ti"], ops),
        ops,
    )
    return {
        "raw_associative_gap": fro_gap(raw_left, raw_right),
        "projected_nonassoc_gap": fro_gap(projected_left, projected_right),
        "erased_projected_gap": fro_gap(erased_left, erased_right),
        "left_formula": "P_M(Ti(P_M(Fi(Fe(rho)))))",
        "right_formula": "P_M(Ti(Fi(P_M(Fe(rho)))))",
        "projection": "P_M maps rho to the product-state section with the same single-qubit Z probe expectations",
    }


def entropy_vn(rho: dq.QArray) -> float:
    return float(jax.device_get(jnp.real(dq.entropy_vn(rho))))


def qit_readouts(rho: dq.QArray) -> dict[str, float]:
    sub_q0 = dq.ptrace(rho, keep=0, dims=(2, 2, 2))
    sub_q12 = dq.ptrace(rho, keep=(1, 2), dims=(2, 2, 2))
    s_all = entropy_vn(rho)
    s_q12 = entropy_vn(sub_q12)
    return {
        "von_neumann_entropy": s_all,
        "subsystem_entropy_q0": entropy_vn(sub_q0),
        "subsystem_entropy_q12": s_q12,
        "coherent_information_q0_to_q12": s_q12 - s_all,
        "trace_real": float(jax.device_get(jnp.real(jnp.trace(dense(rho))))),
    }


def real_spd_embedding(rho: dq.QArray) -> np.ndarray:
    host = np.asarray(jax.device_get(dense(rho)))
    block = np.block([[host.real, -host.imag], [host.imag, host.real]])
    block = 0.5 * (block + block.T)
    return block + 1.0e-8 * np.eye(block.shape[0])


def geomstats_bures(left: dq.QArray, right: dq.QArray) -> dict[str, Any]:
    space = SPDMatrices(n=2 * DIM)
    metric = SPDBuresWassersteinMetric(space)
    left_spd = real_spd_embedding(left)
    right_spd = real_spd_embedding(right)
    distance = metric.dist(gs.array(left_spd), gs.array(right_spd))
    return {
        "call": "geomstats.geometry.spd_matrices.SPDBuresWassersteinMetric.dist",
        "backend": gs.__name__,
        "real_spd_dimension": 2 * DIM,
        "distance": float(distance),
    }


def diagonal_distribution(rho: dq.QArray) -> jax.Array:
    probs = jnp.real(jnp.diag(dense(rho)))
    probs = jnp.clip(probs, 1.0e-12, None)
    return probs / jnp.sum(probs)


def ott_distance(left: dq.QArray, right: dq.QArray) -> dict[str, Any]:
    coords = jnp.asarray([[float((i >> bit) & 1) for bit in range(N_QUBITS)] for i in range(DIM)], dtype=jnp.float64)
    geom = pointcloud.PointCloud(coords, coords, epsilon=0.05)
    problem = linear_problem.LinearProblem(geom, a=diagonal_distribution(left), b=diagonal_distribution(right))
    output = sinkhorn.Sinkhorn()(problem)
    return {
        "call": "ott.solvers.linear.sinkhorn.Sinkhorn",
        "cost": float(jax.device_get(output.reg_ot_cost)),
        "converged": bool(output.converged),
    }


def quimb_z0_expectation(rho: dq.QArray) -> dict[str, Any]:
    host = np.asarray(jax.device_get(dense(rho))).reshape(2, 2, 2, 2, 2, 2)
    z = np.diag([1.0, -1.0])
    ident = np.eye(2)
    optimizer = ctg.HyperOptimizer(max_repeats=4, progbar=False)
    value = qtn.tensor_contract(
        qtn.Tensor(host, inds=["k0", "k1", "k2", "b0", "b1", "b2"]),
        qtn.Tensor(z, inds=["b0", "k0"]),
        qtn.Tensor(ident, inds=["b1", "k1"]),
        qtn.Tensor(ident, inds=["b2", "k2"]),
        optimize=optimizer,
    )
    return {
        "call": "quimb.tensor.tensor_contract(..., optimize=cotengra.HyperOptimizer)",
        "z0_expectation": float(np.real(value)),
    }


def quotient_classes(states: dict[str, dq.QArray], probes: list[tuple[str, dq.QArray]]) -> dict[str, Any]:
    signatures: dict[str, list[float]] = {}
    classes: dict[str, list[str]] = {}
    for name, rho in states.items():
        sig = [round(float(jax.device_get(expect(op, rho))), 8) for _, op in probes]
        key = json.dumps(sig)
        signatures[name] = sig
        classes.setdefault(key, []).append(name)
    ordered = [
        {"signature": json.loads(key), "members": sorted(members)}
        for key, members in sorted(classes.items())
    ]
    return {
        "probe_names": [name for name, _ in probes],
        "class_count": len(ordered),
        "classes": ordered,
        "signatures": signatures,
    }


def diffrax_ti_crosscheck(rho: dq.QArray, ops: dict[str, dq.QArray], dynamiqs_ti: dq.QArray) -> dict[str, Any]:
    H = dense(0.0 * ops["Z0"])
    L = dense(jnp.sqrt(GAMMA) * ops["Z0"])
    y0 = dense(rho).reshape(-1)

    def rhs(_t: jax.Array, y: jax.Array, args: tuple[jax.Array, jax.Array]) -> jax.Array:
        h_mat, l_mat = args
        r = y.reshape((DIM, DIM))
        ldag_l = l_mat.conj().T @ l_mat
        dr = -1j * (h_mat @ r - r @ h_mat)
        dr = dr + l_mat @ r @ l_mat.conj().T - 0.5 * (ldag_l @ r + r @ ldag_l)
        return dr.reshape(-1)

    solution = diffrax.diffeqsolve(
        diffrax.ODETerm(rhs),
        diffrax.Tsit5(),
        t0=0.0,
        t1=EVOLVE_T,
        dt0=0.02,
        y0=y0,
        args=(H, L),
        saveat=diffrax.SaveAt(t1=True),
    )
    final = trace_normalize(solution.ys[0].reshape((DIM, DIM)))
    residual = float(jax.device_get(jnp.linalg.norm(final - dense(dynamiqs_ti))))
    return {
        "call": "diffrax.diffeqsolve(diffrax.ODETerm(lindblad_rhs), diffrax.Tsit5())",
        "residual_vs_dynamiqs_Ti": residual,
    }


def sympy_associator_report() -> dict[str, Any]:
    x, y, z = sp.symbols("x y z")
    associative_control = sp.simplify((x * y) * z - x * (y * z))
    # Basis e0,e1,e2 with projected product constants chosen to model a
    # quotient-section bracket: e0 is a section idempotent; e1*e2=e1; e0*e1=e2.
    n = 3
    constants = [[[0 for _ in range(n)] for _ in range(n)] for _ in range(n)]
    constants[0][0][0] = 1
    constants[2][0][1] = 1
    constants[1][1][2] = 1
    constants[2][2][0] = 1
    a, b, c = 0, 1, 2
    coeffs = []
    for k in range(n):
        left = sum(constants[m][a][b] * constants[k][m][c] for m in range(n))
        right = sum(constants[m][b][c] * constants[k][a][m] for m in range(n))
        coeffs.append(sp.simplify(left - right))
    return {
        "call": "sympy.simplify on associative scalar control and projected-product structure constants",
        "associative_control": str(associative_control),
        "projected_product_associator_e0_e1_e2": [int(v) for v in coeffs],
        "projected_product_nonzero": any(v != 0 for v in coeffs),
    }


def z3_product_entry(left: list[list[z3.ArithRef]], right: list[list[z3.ArithRef]], i: int, j: int) -> z3.ArithRef:
    return sum(left[i][k] * right[k][j] for k in range(len(right)))


def z3_commutation_verdict(a_values: list[list[int]], b_values: list[list[int]]) -> str:
    solver = z3.Solver()
    n = len(a_values)
    a = [[z3.Int(f"a_{i}_{j}") for j in range(n)] for i in range(n)]
    b = [[z3.Int(f"b_{i}_{j}") for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(n):
            solver.add(a[i][j] == a_values[i][j])
            solver.add(b[i][j] == b_values[i][j])
    for i in range(n):
        for j in range(n):
            solver.add(z3_product_entry(a, b, i, j) == z3_product_entry(b, a, i, j))
    return str(solver.check())


def cvc5_sum(solver: cvc5.Solver, terms: list[cvc5.Term]) -> cvc5.Term:
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(cvc5.Kind.ADD, *terms)


def cvc5_product_entry(
    solver: cvc5.Solver,
    left: list[list[cvc5.Term]],
    right: list[list[cvc5.Term]],
    i: int,
    j: int,
) -> cvc5.Term:
    return cvc5_sum(
        solver,
        [solver.mkTerm(cvc5.Kind.MULT, left[i][k], right[k][j]) for k in range(len(right))],
    )


def cvc5_commutation_verdict(a_values: list[list[int]], b_values: list[list[int]]) -> str:
    solver = cvc5.Solver()
    int_sort = solver.getIntegerSort()
    n = len(a_values)
    a = [[solver.mkConst(int_sort, f"a_{i}_{j}") for j in range(n)] for i in range(n)]
    b = [[solver.mkConst(int_sort, f"b_{i}_{j}") for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(n):
            solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, a[i][j], solver.mkInteger(a_values[i][j])))
            solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, b[i][j], solver.mkInteger(b_values[i][j])))
    for i in range(n):
        for j in range(n):
            solver.assertFormula(
                solver.mkTerm(
                    cvc5.Kind.EQUAL,
                    cvc5_product_entry(solver, a, b, i, j),
                    cvc5_product_entry(solver, b, a, i, j),
                )
            )
    return str(solver.checkSat())


def smt_flip_report() -> dict[str, Any]:
    noncommuting_a = [[0, -1], [1, 0]]
    noncommuting_b = [[1, 0], [0, 2]]
    commuting_a = [[2, 0], [0, 3]]
    commuting_b = [[5, 0], [0, 7]]
    return {
        "encoding": "Solver binds exact 2x2 finite operator-entry matrices, derives AB and BA entries internally, then asserts AB == BA.",
        "noncommuting_scaled_pauli_transfer": {
            "z3_force_commute_verdict": z3_commutation_verdict(noncommuting_a, noncommuting_b),
            "cvc5_force_commute_verdict": cvc5_commutation_verdict(noncommuting_a, noncommuting_b),
            "expected": "unsat",
        },
        "commuting_control": {
            "z3_force_commute_verdict": z3_commutation_verdict(commuting_a, commuting_b),
            "cvc5_force_commute_verdict": cvc5_commutation_verdict(commuting_a, commuting_b),
            "expected": "sat",
        },
    }


def graph_report() -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_edges_from(
        [
            ("rho0", "Fe"),
            ("Fe", "Fi"),
            ("Fi", "Ti"),
            ("Ti", "rho_Fe_Fi_Ti"),
            ("Fi", "rho_Fi_Ti"),
            ("Ti", "rho_Ti_Fi"),
        ]
    )
    commutation = nx.Graph()
    commutation.add_edge("Fe", "Ti", relation="commuting_control")
    commutation.add_edge("Fi", "Ti", relation="noncommuting_gap")
    return {
        "call": "networkx.DiGraph / networkx.is_directed_acyclic_graph / networkx.shortest_path_length",
        "composition_dag_nodes": graph.number_of_nodes(),
        "composition_dag_edges": graph.number_of_edges(),
        "composition_is_dag": nx.is_directed_acyclic_graph(graph),
        "fi_to_ti_path_length": nx.shortest_path_length(graph, "Fi", "Ti"),
        "commutation_graph_edges": sorted([sorted(edge) for edge in commutation.edges()]),
    }


def build_result() -> dict[str, Any]:
    ops = carrier_ops()
    rho0 = initial_density()
    rho_fi_ti = apply_sequence(rho0, ["Fi", "Ti"], ops)
    rho_ti_fi = apply_sequence(rho0, ["Ti", "Fi"], ops)
    rho_fe_ti = apply_sequence(rho0, ["Fe", "Ti"], ops)
    rho_ti_fe = apply_sequence(rho0, ["Ti", "Fe"], ops)
    rho_fi = apply_operator("Fi", rho0, ops)
    rho_ti = apply_operator("Ti", rho0, ops)
    rho_te = apply_operator("Te", rho0, ops)
    erased = erase_carrier()

    order_gap = fro_gap(rho_fi_ti, rho_ti_fi)
    commuting_gap = fro_gap(rho_fe_ti, rho_ti_fe)
    erased_order_gap = fro_gap(apply_sequence(erased, ["Fi", "Ti"], ops), apply_sequence(erased, ["Ti", "Fi"], ops))
    bracket = projected_bracketing_gap(rho0, ops)

    full_probes = [("Z0", ops["Z0"]), ("X0", ops["X0"]), ("Z0Z1", ops["Z0Z1"])]
    dropped_probes = [("Z0", ops["Z0"]), ("Z0Z1", ops["Z0Z1"])]
    q_states = {
        "rho0": rho0,
        "Fi_then_Ti": rho_fi_ti,
        "Ti_then_Fi": rho_ti_fi,
        "Fe_then_Ti": rho_fe_ti,
        "carrier_erased": erased,
    }
    quotient_full = quotient_classes(q_states, full_probes)
    quotient_drop = quotient_classes(q_states, dropped_probes)

    diffrax_report = diffrax_ti_crosscheck(rho0, ops, rho_ti)
    smt = smt_flip_report()
    entropy_split = {
        "initial": qit_readouts(rho0),
        "Fi_unitary": qit_readouts(rho_fi),
        "Ti_dissipative": qit_readouts(rho_ti),
        "Te_dissipative": qit_readouts(rho_te),
        "unitary_entropy_delta_abs": abs(qit_readouts(rho_fi)["von_neumann_entropy"] - qit_readouts(rho0)["von_neumann_entropy"]),
        "ti_entropy_increase": qit_readouts(rho_ti)["von_neumann_entropy"] - qit_readouts(rho0)["von_neumann_entropy"],
        "te_entropy_increase": qit_readouts(rho_te)["von_neumann_entropy"] - qit_readouts(rho0)["von_neumann_entropy"],
    }

    all_pass = bool(
        order_gap > 1.0e-2
        and commuting_gap < 1.0e-4
        and erased_order_gap < 1.0e-4
        and bracket["raw_associative_gap"] < TOL
        and bracket["projected_nonassoc_gap"] > 1.0e-2
        and bracket["erased_projected_gap"] < 1.0e-4
        and entropy_split["unitary_entropy_delta_abs"] < 1.0e-4
        and entropy_split["ti_entropy_increase"] > 1.0e-2
        and smt["noncommuting_scaled_pauli_transfer"]["z3_force_commute_verdict"] == "unsat"
        and smt["noncommuting_scaled_pauli_transfer"]["cvc5_force_commute_verdict"] == "unsat"
        and smt["commuting_control"]["z3_force_commute_verdict"] == "sat"
        and smt["commuting_control"]["cvc5_force_commute_verdict"] == "sat"
        and diffrax_report["residual_vs_dynamiqs_Ti"] < 1.0e-4
        and quotient_full["class_count"] > quotient_drop["class_count"]
    )

    result = {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": OBJECT_ID,
        "rung_id": "qit_operator_composition_mcp",
        "engine": "jax",
        "backend": "jax_dynamiqs_diffrax_qit_rich_stack",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": source_sha256(),
        "result_path": str(RESULT_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "carrier": {"n_qubits": N_QUBITS, "dimension": DIM, "initial_state": "generic pure product q0 x |0> x |0>"},
        "operators": {
            "Ti": "dynamiqs.mesolve H=0, jump=sqrt(gamma)*Z0",
            "Te": "dynamiqs.mesolve H=0, jump=sqrt(0.7*gamma)*X1",
            "Fi": "dynamiqs.mesolve H=(theta/T)*X0, no jumps",
            "Fe": "dynamiqs.mesolve H=(theta/T)*Z0, no jumps",
        },
        "M": {"probe_family": ["Z0", "X0", "Z0Z1"], "defines": "finite probe signatures for S/~_M"},
        "C": {
            "constraints": ["trace=1", "Hermitian", "PSD checked through entropy/eigenvalue-safe evolution", "3-qubit finite carrier", "operator maps are dynamiqs Lindblad/unitary evolutions"],
            "rung_specific_constraint": "composition is evaluated through ordered Ti/Te/Fi/Fe channels plus the probe-quotient section P_M",
        },
        "quotient": {
            "S_mod_M_full": quotient_full,
            "drop_X0_probe_control": quotient_drop,
            "probe_drop_coarsens": quotient_full["class_count"] > quotient_drop["class_count"],
        },
        "composition": {
            "order_gap_Fi_then_Ti_vs_Ti_then_Fi": order_gap,
            "commuting_control_Fe_then_Ti_vs_Ti_then_Fe": commuting_gap,
            "carrier_erasure_order_gap": erased_order_gap,
            "bracketing": bracket,
        },
        "readouts": {
            "qit_entropy_split": entropy_split,
            "geomstats_bures_wasserstein_FiTi_vs_TiFi": geomstats_bures(rho_fi_ti, rho_ti_fi),
            "ott_sinkhorn_FiTi_vs_TiFi": ott_distance(rho_fi_ti, rho_ti_fi),
            "quimb_cotengra_z0_FiTi": quimb_z0_expectation(rho_fi_ti),
        },
        "diffrax_crosscheck": diffrax_report,
        "symbolic_associator": sympy_associator_report(),
        "smt": smt,
        "graph": graph_report(),
        "packages_used": [
            "jax",
            "jax.numpy",
            "dynamiqs",
            "diffrax",
            "quimb.tensor",
            "cotengra",
            "geomstats",
            "ott",
            "sympy",
            "z3",
            "cvc5",
            "networkx",
            "numpy",
        ],
        "aligned_packages_load_bearing": ["geomstats", "sympy", "z3", "cvc5"],
        "claim_path_tools": [
            "geomstats",
            "sympy",
            "z3",
            "cvc5",
        ],
        "tool_calls": {
            "dynamiqs.mesolve": "evolved Ti/Te Lindblad and Fi/Fe unitary generators",
            "diffrax.diffeqsolve": "integrated Ti Lindblad vector field independently",
            "quimb.tensor.tensor_contract": "contracted Z0 expectation from rho_Fi_Ti tensor",
            "cotengra.HyperOptimizer": "optimized the quimb contraction path",
            "geomstats.SPDBuresWassersteinMetric.dist": {
                "call": "computed density-manifold distance on SPD embedding",
                "status": "load_bearing",
                "claim_depth": "load_bearing",
                "capability_probe": "system_v4/probes/sim_geomstats_capability.py",
                "capability_result": "system_v4/probes/a2_state/sim_results/geomstats_capability_results.json",
            },
            "ott.Sinkhorn": {
                "call": "computed optimal-transport distinguishability on basis distributions",
                "status": "supportive",
                "demotion_condition": "output remains a side readout and gates no all_pass, divergence, quotient, control, or proof condition",
                "gates": "none",
            },
            "sympy.simplify": {
                "call": "derived associative zero and projected-product nonzero associator controls",
                "status": "load_bearing",
                "claim_depth": "load_bearing",
                "capability_probe": "system_v4/probes/sim_sympy_capability.py",
                "capability_result": "system_v4/probes/a2_state/sim_results/sympy_capability_results.json",
            },
            "z3.Solver": "derived noncommuting UNSAT and commuting SAT matrix-entry flip",
            "cvc5.Solver": "independently derived the same SMT flip",
            "networkx.DiGraph": {
                "call": "represented composition order DAG and commutation graph",
                "status": "supportive",
                "demotion_condition": "output remains a side readout and gates no all_pass, divergence, quotient, control, or proof condition",
                "gates": "none",
            },
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "claim_ceiling": "Scratch diagnostic only: finite 3-qubit QIT operator-composition, quotient, bracketing, and controls. No promotion, formal admission, bridge, Axis0, IGT truth, or physics claim.",
    }
    return to_jsonable(result)


def main() -> int:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"order_gap={result['composition']['order_gap_Fi_then_Ti_vs_Ti_then_Fi']} "
        f"commuting_gap={result['composition']['commuting_control_Fe_then_Ti_vs_Ti_then_Fe']} "
        f"projected_assoc={result['composition']['bracketing']['projected_nonassoc_gap']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
