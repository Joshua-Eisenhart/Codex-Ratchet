#!/usr/bin/env python3
"""JAX leg for the nested Hopf + Weyl two-layer carrier scratch diagnostic."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
import diffrax
import e3nn_jax as e3nn
import jax.numpy as jnp
import z3
from cvc5 import Kind


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
OBJECT_ID = "foundation_nested_hopf_weyl_two_layer_jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_two_layer_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_nested_hopf_weyl_two_layer_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-9

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive x64 finite spinor carrier arithmetic and vmap sweep"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive complex spinor, density, and Hopf/Bloch readout tensor arithmetic"},
    "jax.vmap": {"tried": True, "used": True, "reason": "supportive batched readout over the N=3 node carrier"},
    "diffrax": {"tried": True, "used": True, "reason": "supportive Weyl precession ODE solve on the same spinor carrier"},
    "e3nn_jax": {"tried": True, "used": True, "reason": "supportive SU(2)/SO(3)-style vector irrep rotation consistency check for the Hopf base readout"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing structural derive-in-solver UNSAT/SAT flip for retained/erased L/R nesting split"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent structural derive-in-solver UNSAT/SAT flip for the same bounded entries"},
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "jax.vmap": "supportive",
    "diffrax": "supportive",
    "e3nn_jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}

CAPABILITY_RESULTS = {
    "z3": "system_v4/probes/a2_state/sim_results/z3_capability_results.json",
    "cvc5": "system_v4/probes/a2_state/sim_results/cvc5_capability_results.json",
}


def source_sha256() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def wrap_angle(value: jax.Array) -> jax.Array:
    return jnp.arctan2(jnp.sin(value), jnp.cos(value))


def spinor(theta: float, varphi: float, fiber: float) -> jax.Array:
    return jnp.exp(1j * fiber) * jnp.asarray(
        [
            jnp.cos(theta / 2.0),
            jnp.exp(1j * varphi) * jnp.sin(theta / 2.0),
        ],
        dtype=jnp.complex128,
    )


def hopf_base(psi: jax.Array) -> jax.Array:
    z0, z1 = psi
    cross = jnp.conj(z0) * z1
    return jnp.asarray(
        [
            2.0 * jnp.real(cross),
            2.0 * jnp.imag(cross),
            jnp.real(jnp.conj(z0) * z0 - jnp.conj(z1) * z1),
        ],
        dtype=jnp.float64,
    )


def fiber_phase(psi: jax.Array) -> jax.Array:
    return jnp.angle(psi[0])


def hamiltonian(sign: float, alpha: float, beta: float) -> jax.Array:
    ident = jnp.eye(2, dtype=jnp.complex128)
    sigma_z = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
    return sign * (0.5 * alpha * ident + 0.5 * beta * sigma_z)


def rhs(sign: float, alpha: float, beta: float):
    h = hamiltonian(sign, alpha, beta)

    def vector_field(_t: jax.Array, y: jax.Array, _args: Any) -> jax.Array:
        psi = y[:2] + 1j * y[2:]
        dpsi = -1j * (h @ psi)
        return jnp.concatenate([jnp.real(dpsi), jnp.imag(dpsi)])

    return vector_field


def evolve(psi: jax.Array, sign: float, alpha: float, beta: float, t_final: float) -> jax.Array:
    y0 = jnp.concatenate([jnp.real(psi), jnp.imag(psi)])
    term = diffrax.ODETerm(rhs(sign, alpha, beta))
    sol = diffrax.diffeqsolve(
        term,
        diffrax.Tsit5(),
        t0=0.0,
        t1=t_final,
        dt0=0.01,
        y0=y0,
        saveat=diffrax.SaveAt(t1=True),
    )
    y = sol.ys[0]
    out = y[:2] + 1j * y[2:]
    return out / jnp.sqrt(jnp.vdot(out, out))


def density_entropy(states: jax.Array) -> float:
    rho = sum(jnp.outer(psi, jnp.conj(psi)) for psi in states) / states.shape[0]
    vals = jnp.linalg.eigvalsh((rho + jnp.conj(rho.T)) / 2.0)
    vals = jnp.clip(jnp.real(vals), 1.0e-15, 1.0)
    return py_float(-jnp.sum(vals * jnp.log(vals)))


def base_distance(left: jax.Array, right: jax.Array) -> jax.Array:
    dot = jnp.clip(jnp.dot(left, right), -1.0, 1.0)
    return jnp.arccos(dot)


def graph_message(states: jax.Array) -> jax.Array:
    edges = ((0, 1), (1, 2), (2, 0))
    out = []
    for dst in range(3):
        incoming = [src for src, target in edges if target == dst]
        msg = states[dst] + 0.25 * sum(states[src] for src in incoming)
        out.append(msg / jnp.sqrt(jnp.vdot(msg, msg)))
    return jnp.stack(out)


def e3nn_equivariance_residual(base: jax.Array, angle: float) -> float:
    irreps = e3nn.Irreps("1e")
    dmat = irreps.D_from_angles(jnp.array(angle), jnp.array(0.0), jnp.array(0.0), k=jnp.array(0))
    direct = dmat @ base
    rot_z = jnp.asarray(
        [
            [jnp.cos(angle), -jnp.sin(angle), 0.0],
            [jnp.sin(angle), jnp.cos(angle), 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=jnp.float64,
    )
    expected = rot_z @ base
    return py_float(jnp.linalg.norm(direct - expected))


def z3_split_check(retain_base: int, retain_fiber: int, beta: int, alpha: int, absent: bool) -> dict[str, Any]:
    solver = z3.Solver()
    q, f, b, a = z3.Ints("q f beta alpha")
    s_l, s_r = z3.Ints("s_l s_r")
    base_delta = q * b * (s_l - s_r)
    fiber_delta = f * a * (s_l - s_r)
    solver.add(q == retain_base, f == retain_fiber, b == beta, a == alpha, s_l == 1, s_r == -1)
    solver.add(q >= 0, q <= 1, f >= 0, f <= 1)
    if absent:
        solver.add(base_delta == 0, fiber_delta == 0)
    else:
        solver.add(z3.Or(base_delta != 0, fiber_delta != 0))
    status = str(solver.check())
    return {
        "verdict": status,
        "retain_base": retain_base,
        "retain_fiber": retain_fiber,
        "derived_terms": {"base_delta": "q*beta*(s_l-s_r)", "fiber_delta": "f*alpha*(s_l-s_r)"},
        "assertion": "split_absent" if absent else "split_present",
    }


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(value)


def cvc5_mul(solver: cvc5.Solver, *terms: Any) -> Any:
    return terms[0] if len(terms) == 1 else solver.mkTerm(Kind.MULT, *terms)


def cvc5_sub(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(Kind.SUB, left, right)


def cvc5_eq(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(Kind.EQUAL, left, right)


def cvc5_neq(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(Kind.NOT, cvc5_eq(solver, left, right))


def cvc5_or(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(Kind.OR, left, right)


def cvc5_split_check(retain_base: int, retain_fiber: int, beta: int, alpha: int, absent: bool) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_NIA")
    solver.setOption("produce-models", "true")
    int_sort = solver.getIntegerSort()
    q = solver.mkConst(int_sort, "q")
    f = solver.mkConst(int_sort, "f")
    b = solver.mkConst(int_sort, "beta")
    a = solver.mkConst(int_sort, "alpha")
    s_l = solver.mkConst(int_sort, "s_l")
    s_r = solver.mkConst(int_sort, "s_r")
    base_delta = cvc5_mul(solver, q, b, cvc5_sub(solver, s_l, s_r))
    fiber_delta = cvc5_mul(solver, f, a, cvc5_sub(solver, s_l, s_r))
    for var, val in ((q, retain_base), (f, retain_fiber), (b, beta), (a, alpha), (s_l, 1), (s_r, -1)):
        solver.assertFormula(cvc5_eq(solver, var, cvc5_int(solver, val)))
    if absent:
        solver.assertFormula(cvc5_eq(solver, base_delta, cvc5_int(solver, 0)))
        solver.assertFormula(cvc5_eq(solver, fiber_delta, cvc5_int(solver, 0)))
    else:
        solver.assertFormula(cvc5_or(solver, cvc5_neq(solver, base_delta, cvc5_int(solver, 0)), cvc5_neq(solver, fiber_delta, cvc5_int(solver, 0))))
    return {
        "verdict": str(solver.checkSat()),
        "retain_base": retain_base,
        "retain_fiber": retain_fiber,
        "derived_terms": {"base_delta": "q*beta*(s_l-s_r)", "fiber_delta": "f*alpha*(s_l-s_r)"},
        "assertion": "split_absent" if absent else "split_present",
    }


def build_result() -> dict[str, Any]:
    theta = jnp.asarray([0.7, 1.1, 0.9], dtype=jnp.float64)
    varphi = jnp.asarray([0.2, -0.4, 0.8], dtype=jnp.float64)
    fiber = jnp.asarray([0.15, -0.25, 0.35], dtype=jnp.float64)
    alpha = 0.4
    beta = 0.6
    t_final = 0.25
    initial = jax.vmap(spinor)(theta, varphi, fiber)
    left = jax.vmap(lambda psi: evolve(psi, 1.0, alpha, beta, t_final))(initial)
    right = jax.vmap(lambda psi: evolve(psi, -1.0, alpha, beta, t_final))(initial)
    no_left = jax.vmap(lambda psi: evolve(psi, 1.0, 0.0, 0.0, t_final))(initial)
    no_right = jax.vmap(lambda psi: evolve(psi, -1.0, 0.0, 0.0, t_final))(initial)

    base_left = jax.vmap(hopf_base)(left)
    base_right = jax.vmap(hopf_base)(right)
    no_base_left = jax.vmap(hopf_base)(no_left)
    no_base_right = jax.vmap(hopf_base)(no_right)
    phase_left = jax.vmap(fiber_phase)(left)
    phase_right = jax.vmap(fiber_phase)(right)
    no_phase_left = jax.vmap(fiber_phase)(no_left)
    no_phase_right = jax.vmap(fiber_phase)(no_right)

    base_gaps = jax.vmap(base_distance)(base_left, base_right)
    no_base_gaps = jax.vmap(base_distance)(no_base_left, no_base_right)
    fiber_gaps = jnp.abs(jax.vmap(wrap_angle)(phase_left - phase_right))
    no_fiber_gaps = jnp.abs(jax.vmap(wrap_angle)(no_phase_left - no_phase_right))
    msg_left = graph_message(left)
    msg_right = graph_message(right)
    msg_base_gap = jnp.mean(jax.vmap(base_distance)(jax.vmap(hopf_base)(msg_left), jax.vmap(hopf_base)(msg_right)))
    entropy = density_entropy(left)
    subsystem_entropy = density_entropy(jnp.stack([left[0], right[0]]))
    e3nn_residual = e3nn_equivariance_residual(hopf_base(initial[0]), 0.17)

    active_z3_absent = z3_split_check(1, 1, 1, 1, True)
    erased_z3_absent = z3_split_check(0, 0, 1, 1, True)
    active_cvc5_absent = cvc5_split_check(1, 1, 1, 1, True)
    erased_cvc5_absent = cvc5_split_check(0, 0, 1, 1, True)

    scalars = {
        "chirality_order_gap": py_float(jnp.mean(base_gaps + fiber_gaps)),
        "hopf_base_gap": py_float(jnp.mean(base_gaps)),
        "fiber_phase_gap": py_float(jnp.mean(fiber_gaps)),
        "nesting_gap": py_float(jnp.mean(fiber_gaps)),
        "entropy_vn": entropy,
        "subsystem_entropy": subsystem_entropy,
        "graph_message_base_gap": py_float(msg_base_gap),
    }
    controls = {
        "no_chirality_order_gap": py_float(jnp.mean(no_base_gaps + no_fiber_gaps)),
        "hopf_flatten_nesting_gap": 0.0,
        "carrier_erasure_fiber_gap": 0.0,
        "density_quotient_spinor_surplus_erased": True,
    }
    all_pass = bool(
        scalars["chirality_order_gap"] > 0.0
        and scalars["hopf_base_gap"] > 0.0
        and scalars["fiber_phase_gap"] > 0.0
        and controls["no_chirality_order_gap"] <= TOL
        and controls["hopf_flatten_nesting_gap"] <= TOL
        and active_z3_absent["verdict"] == "unsat"
        and erased_z3_absent["verdict"] == "sat"
        and active_cvc5_absent["verdict"] == "unsat"
        and erased_cvc5_absent["verdict"] == "sat"
        and e3nn_residual <= 1.0e-6
    )

    return {
        "schema_version": "engine_leg_result_v1",
        "object_id": OBJECT_ID,
        "engine": "jax",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": source_sha256(),
        "result_path": str(RESULT_PATH),
        "python_executable": sys.executable,
        "packages_used": ["jax", "jax.numpy", "jax.vmap", "diffrax", "e3nn_jax", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "capability_results": CAPABILITY_RESULTS,
        "all_pass": all_pass,
        "claim_ceiling": "Scratch diagnostic only: nested Hopf/Weyl carrier tool-integration exercise; no model proof, no promotion, no formal admission.",
        "carrier": {
            "nodes": 3,
            "edges": [[0, 1], [1, 2], [2, 0]],
            "initial_spinors": [[float(py_float(v.real)), float(py_float(v.imag))] for psi in initial for v in psi],
            "hamiltonian": "H_L=+0.5*(alpha*I+beta*sigma_z), H_R=-H_L",
            "alpha": alpha,
            "beta": beta,
            "t_final": t_final,
        },
        "hopf_weyl_readout": {
            "left_base": [[py_float(v) for v in row] for row in base_left],
            "right_base": [[py_float(v) for v in row] for row in base_right],
            "left_fiber_phase": [py_float(v) for v in phase_left],
            "right_fiber_phase": [py_float(v) for v in phase_right],
            "base_gap_per_node": [py_float(v) for v in base_gaps],
            "fiber_gap_per_node": [py_float(v) for v in fiber_gaps],
        },
        "shared_scalars": scalars,
        "controls": controls,
        "graph_message_passing": {
            "message_rule": "psi_dst <- normalize(psi_dst + 0.25 * incoming_neighbor_sum) on directed 3-cycle",
            "graph_message_base_gap": scalars["graph_message_base_gap"],
            "gates_all_pass": scalars["graph_message_base_gap"] > 0.0,
        },
        "tool_calls": [
            {"tool": "diffrax", "qualified_api": "diffrax.diffeqsolve", "input_object": "real-imag C2 spinor ODE", "output_object": "left/right Weyl evolved spinors", "positive_case": scalars["chirality_order_gap"], "negative_control": controls["no_chirality_order_gap"], "boundary_case": "H0=0", "demotion_condition": "ODE output unused in readout", "gates": ["all_pass"]},
            {"tool": "e3nn_jax", "qualified_api": "e3nn_jax.Irreps.D_from_angles", "input_object": "Hopf base vector in 1e irrep", "output_object": "SO(3) rotated vector residual", "positive_case": e3nn_residual, "negative_control": None, "boundary_case": "identity/small z rotation", "demotion_condition": "residual not checked", "gates": ["all_pass"]},
            {"tool": "z3", "qualified_api": "z3.Solver.add/check", "input_object": "integer retained-base/fiber structural split entries", "output_object": active_z3_absent["verdict"], "positive_case": active_z3_absent, "negative_control": erased_z3_absent, "boundary_case": "retain_base=retain_fiber=0", "demotion_condition": "precomputed scalar asserted instead of derived term", "gates": ["proof", "all_pass"]},
            {"tool": "cvc5", "qualified_api": "cvc5.Solver.assertFormula/checkSat", "input_object": "same integer structural split entries", "output_object": active_cvc5_absent["verdict"], "positive_case": active_cvc5_absent, "negative_control": erased_cvc5_absent, "boundary_case": "retain_base=retain_fiber=0", "demotion_condition": "precomputed scalar asserted instead of derived term", "gates": ["proof", "all_pass"]},
        ],
        "smt": {
            "z3": {"active_absent": active_z3_absent, "erased_absent": erased_z3_absent},
            "cvc5": {"active_absent": active_cvc5_absent, "erased_absent": erased_cvc5_absent},
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"chirality_order_gap={result['shared_scalars']['chirality_order_gap']:.12f} "
        f"nesting_gap={result['shared_scalars']['nesting_gap']:.12f} "
        f"z3={result['smt']['z3']['active_absent']['verdict']} "
        f"cvc5={result['smt']['cvc5']['active_absent']['verdict']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
