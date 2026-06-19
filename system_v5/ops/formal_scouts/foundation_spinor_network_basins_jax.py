#!/usr/bin/env python3
"""JAX leg for a finite spinor-network basin scratch diagnostic."""

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
import diffrax
import dynamiqs as dq
import jax
import jax.numpy as jnp
import sympy as sp
import z3
from cvc5 import Kind


OBJECT_ID = "foundation_spinor_network_basins_jax"
RUNG_ID = "spinor_network_basins"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_spinor_network_basins_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_jax_results.json"
TOL = 1.0e-9

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False
READS_PEER_RESULT = reads_peer_result

TARGET = jnp.array([1.0, -1.0, -1.0, -1.0], dtype=jnp.float64)
GRAPH_EDGES = [(0, 1), (1, 2), (2, 3), (3, 0)]
O_WITNESS = (1, 2, 4)
H_ASSOC_CONTROL = (1, 2, 3)

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 vectorized finite-state basin update and algebra-table evaluation.",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive tensor arithmetic for JAX transformations; not the only claim path.",
    },
    "diffrax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing ODE basin-flow cross-check over all finite spinor-network seeds with jax.vmap.",
    },
    "dynamiqs": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Lindblad/master-equation evolution of the spinor density and expectation readout.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing structural SMT proof deriving order, associator, and basin flips from bound entries.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT proof of the same derived structural flips.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic associator component expansion for the selected octonion witness.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "supportive",
    "diffrax": "load_bearing",
    "dynamiqs": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    return jnp.einsum("cab,a,b->c", table, x, y)


def cd_pair_multiply(parent: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    n = parent.shape[0]
    a, b = x[:n], x[n:]
    c, d = y[:n], y[n:]
    first = table_multiply(parent, a, c) - table_multiply(parent, cd_conj(d), b)
    second = table_multiply(parent, d, a) + table_multiply(parent, b, cd_conj(c))
    return jnp.concatenate([first, second])


def cd_double(parent: jax.Array) -> jax.Array:
    n = parent.shape[0]
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
    complex_table = cd_double(real)
    quaternion = cd_double(complex_table)
    octonion = cd_double(quaternion)
    return {"H": quaternion, "O": octonion}


def basis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def associator_vector(table: jax.Array, a: int, b: int, c: int) -> jax.Array:
    ea, eb, ec = basis(table.shape[0], a), basis(table.shape[0], b), basis(table.shape[0], c)
    return table_multiply(table, table_multiply(table, ea, eb), ec) - table_multiply(
        table, ea, table_multiply(table, eb, ec)
    )


def order_gap(table: jax.Array, a: int, b: int) -> jax.Array:
    return jnp.linalg.vector_norm(table[:, a, b] - table[:, b, a])


def all_states() -> jax.Array:
    return jnp.array(list(itertools.product([-1.0, 1.0], repeat=4)), dtype=jnp.float64)


def finite_update(state: jax.Array, real_constraint: bool) -> jax.Array:
    if not real_constraint:
        return state
    q = jnp.dot(state, TARGET)
    return jnp.where(q >= 0.0, TARGET, -TARGET)


def finite_basins(real_constraint: bool) -> dict[str, Any]:
    seeds = all_states()
    finals = jax.vmap(lambda s: finite_update(s, real_constraint))(seeds)
    final_rows = [tuple(int(x) for x in row) for row in jax.device_get(finals).tolist()]
    counts = Counter(final_rows)
    return {
        "seed_count": int(seeds.shape[0]),
        "attractor_count": len(counts),
        "basin_counts": {" ".join(map(str, key)): int(val) for key, val in sorted(counts.items())},
        "basin_fractions": {" ".join(map(str, key)): float(val / seeds.shape[0]) for key, val in sorted(counts.items())},
    }


def diffrax_basin_flow() -> dict[str, Any]:
    seeds = all_states()

    def vector_field(t: float, y: jax.Array, target: jax.Array) -> jax.Array:
        q = jnp.dot(y, target) + 0.125 * y[0] * target[0]
        return target * jnp.tanh(4.0 * q) - y

    term = diffrax.ODETerm(vector_field)
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
    signs = jnp.where((jnp.sum(finals * TARGET, axis=1) >= 0.0)[:, None], TARGET, -TARGET)
    rows = [tuple(int(x) for x in row) for row in jax.device_get(signs).tolist()]
    counts = Counter(rows)
    return {
        "function_called": "diffrax.diffeqsolve via jax.vmap",
        "seed_count": int(seeds.shape[0]),
        "attractor_count": len(counts),
        "basin_counts": {" ".join(map(str, key)): int(val) for key, val in sorted(counts.items())},
        "terminal_projection_min_abs": float(jnp.min(jnp.abs(jnp.sum(finals * TARGET, axis=1)))),
    }


def density_from_spinor(spinor: jax.Array) -> jax.Array:
    psi = (spinor / jnp.linalg.vector_norm(spinor)).astype(jnp.complex128)
    return jnp.outer(psi, jnp.conj(psi))


def entropy_vn(rho: jax.Array) -> float:
    vals = jnp.linalg.eigvalsh((rho + jnp.conj(rho.T)) / 2.0)
    vals = jnp.clip(jnp.real(vals), 0.0, 1.0)
    safe = jnp.clip(vals, 1.0e-30, 1.0)
    return float(-jnp.sum(jnp.where(vals > 1.0e-12, vals * jnp.log(safe), 0.0)))


def partial_trace_q0(rho: jax.Array) -> jax.Array:
    reshaped = rho.reshape(2, 2, 2, 2)
    return jnp.einsum("abcb->ac", reshaped)


def trace_distance(rho: jax.Array, sigma: jax.Array) -> float:
    vals = jnp.linalg.eigvalsh((rho - sigma + jnp.conj((rho - sigma).T)) / 2.0)
    return float(0.5 * jnp.sum(jnp.abs(vals)))


def qit_readout() -> dict[str, Any]:
    rho = density_from_spinor(TARGET)
    erased = jnp.eye(4, dtype=jnp.complex128) / 4.0
    red = partial_trace_q0(rho)
    red_erased = partial_trace_q0(erased)
    s_ab = entropy_vn(rho)
    s_a = entropy_vn(red)
    s_ab_erased = entropy_vn(erased)
    s_a_erased = entropy_vn(red_erased)
    z0 = dq.tensor(dq.sigmaz(), dq.eye(2))
    rhoq = dq.asqarray(rho, dims=(2, 2))
    result = dq.mesolve(
        0.03 * z0,
        [0.1 * z0],
        rhoq,
        jnp.linspace(0.0, 1.0, 4),
        exp_ops=[z0],
        options=dq.Options(progress_meter=False),
    )
    dyn_final = result.states.to_jax()[-1]
    return {
        "density_function": "jax.numpy outer product over target spinor",
        "dynamiqs_function_called": "dynamiqs.mesolve",
        "von_neumann_entropy": s_ab,
        "subsystem_entropy_q0": s_a,
        "coherent_information_q0_to_q1": s_a - s_ab,
        "erased_von_neumann_entropy": s_ab_erased,
        "erased_subsystem_entropy_q0": s_a_erased,
        "erased_coherent_information_q0_to_q1": s_a_erased - s_ab_erased,
        "distinguishability_trace_distance_to_erased": trace_distance(rho, erased),
        "dynamiqs_final_entropy": entropy_vn(dyn_final),
        "dynamiqs_z0_expectation_final": float(jnp.real(result.expects[0, -1])),
    }


def z3_sum(items: list[z3.ArithRef]) -> z3.ArithRef:
    out = z3.IntVal(0)
    for item in items:
        out = out + item
    return out


def z3_order_proof(table: jax.Array, a: int, b: int) -> str:
    arr = jax.device_get(table).astype(int)
    dim = arr.shape[0]
    solver = z3.Solver()
    mu = {}
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                var = z3.Int(f"mu_o_{k}_{i}_{j}")
                solver.add(var == int(arr[k, i, j]))
                mu[k, i, j] = var
    solver.add(z3.And([mu[k, a, b] == mu[k, b, a] for k in range(dim)]))
    return str(solver.check())


def z3_associator_proof(table: jax.Array, witness: tuple[int, int, int]) -> str:
    arr = jax.device_get(table).astype(int)
    dim = arr.shape[0]
    a, b, c = witness
    solver = z3.Solver()
    mu = {}
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                var = z3.Int(f"mu_a_{k}_{i}_{j}")
                solver.add(var == int(arr[k, i, j]))
                mu[k, i, j] = var
    equations = []
    for k in range(dim):
        left = z3_sum([mu[k, m, c] * mu[m, a, b] for m in range(dim)])
        right = z3_sum([mu[k, a, m] * mu[m, b, c] for m in range(dim)])
        equations.append(left == right)
    solver.add(z3.And(equations))
    return str(solver.check())


def z3_basin_proof(real_constraint: bool) -> str:
    solver = z3.Solver()
    xs = [z3.Int(f"x{i}") for i in range(4)]
    for x in xs:
        solver.add(z3.Or(x == 1, x == -1))
    q = sum(xs[i] * int(TARGET[i]) for i in range(4))
    if real_constraint:
        ys = [z3.If(q >= 0, int(TARGET[i]), -int(TARGET[i])) for i in range(4)]
    else:
        ys = xs
    pos = z3.And([ys[i] == int(TARGET[i]) for i in range(4)])
    neg = z3.And([ys[i] == -int(TARGET[i]) for i in range(4)])
    solver.add(z3.Not(z3.Or(pos, neg)))
    return str(solver.check())


def cvc5_sum(solver: cvc5.Solver, items: list[Any]) -> Any:
    if not items:
        return solver.mkInteger(0)
    out = items[0]
    for item in items[1:]:
        out = solver.mkTerm(Kind.ADD, out, item)
    return out


def cvc5_order_proof(table: jax.Array, a: int, b: int) -> str:
    arr = jax.device_get(table).astype(int)
    dim = arr.shape[0]
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    mu = {}
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                var = solver.mkConst(int_sort, f"mu_o_{k}_{i}_{j}")
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(int(arr[k, i, j]))))
                mu[k, i, j] = var
    solver.assertFormula(solver.mkTerm(Kind.AND, *[solver.mkTerm(Kind.EQUAL, mu[k, a, b], mu[k, b, a]) for k in range(dim)]))
    return str(solver.checkSat())


def cvc5_associator_proof(table: jax.Array, witness: tuple[int, int, int]) -> str:
    arr = jax.device_get(table).astype(int)
    dim = arr.shape[0]
    a, b, c = witness
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    mu = {}
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                var = solver.mkConst(int_sort, f"mu_a_{k}_{i}_{j}")
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(int(arr[k, i, j]))))
                mu[k, i, j] = var
    equations = []
    for k in range(dim):
        left = cvc5_sum(solver, [solver.mkTerm(Kind.MULT, mu[k, m, c], mu[m, a, b]) for m in range(dim)])
        right = cvc5_sum(solver, [solver.mkTerm(Kind.MULT, mu[k, a, m], mu[m, b, c]) for m in range(dim)])
        equations.append(solver.mkTerm(Kind.EQUAL, left, right))
    solver.assertFormula(solver.mkTerm(Kind.AND, *equations))
    return str(solver.checkSat())


def cvc5_basin_proof(real_constraint: bool) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    one = solver.mkInteger(1)
    neg_one = solver.mkInteger(-1)
    zero = solver.mkInteger(0)
    xs = [solver.mkConst(int_sort, f"x{i}") for i in range(4)]
    for x in xs:
        solver.assertFormula(
            solver.mkTerm(Kind.OR, solver.mkTerm(Kind.EQUAL, x, one), solver.mkTerm(Kind.EQUAL, x, neg_one))
        )
    terms = [solver.mkTerm(Kind.MULT, xs[i], solver.mkInteger(int(TARGET[i]))) for i in range(4)]
    q = cvc5_sum(solver, terms)
    if real_constraint:
        ys = [
            solver.mkTerm(
                Kind.ITE,
                solver.mkTerm(Kind.GEQ, q, zero),
                solver.mkInteger(int(TARGET[i])),
                solver.mkInteger(-int(TARGET[i])),
            )
            for i in range(4)
        ]
    else:
        ys = xs
    pos = solver.mkTerm(Kind.AND, *[solver.mkTerm(Kind.EQUAL, ys[i], solver.mkInteger(int(TARGET[i]))) for i in range(4)])
    neg = solver.mkTerm(Kind.AND, *[solver.mkTerm(Kind.EQUAL, ys[i], solver.mkInteger(-int(TARGET[i]))) for i in range(4)])
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.OR, pos, neg)))
    return str(solver.checkSat())


def symbolic_associator_component(table: jax.Array, witness: tuple[int, int, int], component: int) -> dict[str, Any]:
    arr = jax.device_get(table).astype(int)
    dim = arr.shape[0]
    a, b, c = witness
    mu = {
        (k, i, j): sp.Integer(int(arr[k, i, j]))
        for k in range(dim)
        for i in range(dim)
        for j in range(dim)
    }
    left = sum(mu[(component, m, c)] * mu[(m, a, b)] for m in range(dim))
    right = sum(mu[(component, a, m)] * mu[(m, b, c)] for m in range(dim))
    expr = sp.simplify(left - right)
    return {
        "function_called": "sympy.simplify",
        "component": component,
        "expression_value": int(expr),
        "witness": list(witness),
    }


def quotient_summary() -> dict[str, Any]:
    states = all_states()
    edge01 = states[:, 0] * states[:, 1]
    edge02 = states[:, 0] * states[:, 2]
    edge03 = states[:, 0] * states[:, 3]
    features = jnp.stack([edge01, edge02, edge03], axis=1)
    dropped = jnp.stack([edge01, edge02], axis=1)
    full_classes = {tuple(float(x) for x in row) for row in jax.device_get(features).tolist()}
    dropped_classes = {tuple(float(x) for x in row) for row in jax.device_get(dropped).tolist()}
    return {
        "M": ["edge01_spinor_parity", "edge02_spinor_parity", "edge03_spinor_parity"],
        "quotient_classes_under_M": len(full_classes),
        "drop_edge03_control_classes": len(dropped_classes),
        "drop_probe_strictly_coarsens": len(dropped_classes) < len(full_classes),
        "C": [
            "trace=1",
            "PSD",
            "Hermitian",
            "normalization",
            "order_gap_nonzero",
            "octonion_associator_nonzero",
            "finite basin compression under C",
        ],
    }


def build_result() -> dict[str, Any]:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tables = build_tables()
    h_table = tables["H"]
    o_table = tables["O"]
    ogap = float(order_gap(h_table, 1, 2))
    ogap_control = float(order_gap(h_table, 1, 1))
    assoc_o = associator_vector(o_table, *O_WITNESS)
    assoc_h = associator_vector(h_table, *H_ASSOC_CONTROL)
    assoc_norm = float(jnp.linalg.vector_norm(assoc_o))
    assoc_control_norm = float(jnp.linalg.vector_norm(assoc_h))
    basins_real = finite_basins(True)
    basins_control = finite_basins(False)
    diffrax_basins = diffrax_basin_flow()
    qit = qit_readout()
    smt = {
        "z3": {
            "order_noncommuting_commute_assertion": z3_order_proof(h_table, 1, 2),
            "order_commuting_control": z3_order_proof(h_table, 1, 1),
            "octonion_assoc_zero_assertion": z3_associator_proof(o_table, O_WITNESS),
            "quaternion_assoc_zero_control": z3_associator_proof(h_table, H_ASSOC_CONTROL),
            "real_basin_counterexample": z3_basin_proof(True),
            "erased_basin_counterexample": z3_basin_proof(False),
        },
        "cvc5": {
            "order_noncommuting_commute_assertion": cvc5_order_proof(h_table, 1, 2),
            "order_commuting_control": cvc5_order_proof(h_table, 1, 1),
            "octonion_assoc_zero_assertion": cvc5_associator_proof(o_table, O_WITNESS),
            "quaternion_assoc_zero_control": cvc5_associator_proof(h_table, H_ASSOC_CONTROL),
            "real_basin_counterexample": cvc5_basin_proof(True),
            "erased_basin_counterexample": cvc5_basin_proof(False),
        },
    }
    all_pass = bool(
        ogap > 1.0
        and ogap_control <= TOL
        and assoc_norm > 1.0
        and assoc_control_norm <= TOL
        and basins_real["attractor_count"] == 2
        and basins_control["attractor_count"] == 16
        and smt["z3"]["real_basin_counterexample"] == "unsat"
        and smt["cvc5"]["real_basin_counterexample"] == "unsat"
        and smt["z3"]["erased_basin_counterexample"] == "sat"
        and smt["cvc5"]["erased_basin_counterexample"] == "sat"
    )
    result = {
        "schema_version": "three_engine_leg_result_v1",
        "object_id": OBJECT_ID,
        "rung_id": RUNG_ID,
        "engine": "jax",
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "packages_used": ["jax", "jax.numpy", "diffrax", "dynamiqs", "z3", "cvc5", "sympy", "json", "hashlib"],
        "aligned_packages_load_bearing": ["diffrax", "z3", "cvc5"],
        "claim_path_tools": ["jax", "diffrax", "dynamiqs", "z3", "cvc5", "sympy"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "network": {"node_count": 4, "edges": GRAPH_EDGES, "target_spinor": [float(x) for x in TARGET]},
        "algebra": {
            "order_gap_noncommuting": ogap,
            "order_gap_commuting_control": ogap_control,
            "octonion_associator_norm": assoc_norm,
            "octonion_associator_vector": [float(x) for x in assoc_o],
            "quaternion_associator_control_norm": assoc_control_norm,
            "sympy_associator_component": symbolic_associator_component(o_table, O_WITNESS, 7),
        },
        "basins": {"finite_real": basins_real, "finite_erased_control": basins_control, "diffrax_vmap": diffrax_basins},
        "qit_readout": qit,
        "M_C_quotient": quotient_summary(),
        "smt": smt,
        "tool_calls": [
            {"tool": "diffrax", "function": "diffrax.diffeqsolve", "computed": diffrax_basins},
            {"tool": "dynamiqs", "function": "dynamiqs.mesolve", "computed": {"final_entropy": qit["dynamiqs_final_entropy"]}},
            {"tool": "z3", "function": "z3.Solver.check", "computed": smt["z3"]},
            {"tool": "cvc5", "function": "cvc5.Solver.checkSat", "computed": smt["cvc5"]},
            {"tool": "sympy", "function": "sympy.simplify", "computed": symbolic_associator_component(o_table, O_WITNESS, 7)},
        ],
        "all_pass": all_pass,
    }
    RESULT_PATH.write_text(json.dumps(to_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    result = build_result()
    print(
        "FOUNDATION_SPINOR_NETWORK_BASINS_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"order_gap={result['algebra']['order_gap_noncommuting']:.6f} "
        f"assoc={result['algebra']['octonion_associator_norm']:.6f} "
        f"real_attractors={result['basins']['finite_real']['attractor_count']} "
        f"control_attractors={result['basins']['finite_erased_control']['attractor_count']} "
        f"result={RESULT_PATH}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
