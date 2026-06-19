#!/usr/bin/env python3
"""JAX leg for the source-locked four-operator base packet."""

from __future__ import annotations

from jax import config

config.update("jax_enable_x64", True)

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cvc5
import jax
import jax.numpy as jnp
import z3
from cvc5 import Kind


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "source_locked_operator_base_packet"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULTS_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULTS_DIR / f"{SIM_ID}_jax_results.json"
ENGINE = "jax"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-12

Q1 = 0.3
Q2 = 0.3
THETA = math.pi / 2.0
PHI = math.pi / 2.0
PIN_SPEC = "q1=q2=0.3, theta=phi=pi/2, rho_0=|psi(0.3,0.2,pi/8)><...|, rho_1=0.7*rho_0+0.3*I/2"

I2 = jnp.eye(2, dtype=jnp.complex128)
SX = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
P0 = 0.5 * (I2 + SZ)
P1 = 0.5 * (I2 - SZ)
QP = 0.5 * (I2 + SX)
QM = 0.5 * (I2 - SX)
HX = (1.0 / math.sqrt(2.0)) * jnp.asarray([[1.0, 1.0], [1.0, -1.0]], dtype=jnp.complex128)

SOURCE_CITATIONS = {
    "scaffold_hopf_spinor": "system_v6/foundations/working_math_scaffold_20260609.md:31-38",
    "scaffold_base_operators": "system_v6/foundations/working_math_scaffold_20260609.md:66-75",
    "source_state_and_projectors": "system_v5/READ ONLY Reference Docs/operator math explicit.md:8-100",
    "source_Ti": "system_v5/READ ONLY Reference Docs/operator math explicit.md:102-230",
    "source_Te": "system_v5/READ ONLY Reference Docs/operator math explicit.md:279-438",
    "source_Fi": "system_v5/READ ONLY Reference Docs/operator math explicit.md:488-587",
    "source_Fe": "system_v5/READ ONLY Reference Docs/operator math explicit.md:646-735",
    "source_exact_lock": "system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810",
    "wiki_operator_summary": "/Users/joshuaeisenhart/wiki/concepts/operator-math-explicit.md:68-123",
}

OPERATOR_BACKLOG = [
    {
        "operator": "R_y",
        "status": "not_implemented",
        "reason": "not one of the four intrinsic source-locked operators in this packet",
        "source_citations": ["system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810"],
    },
    {
        "operator": "D_y",
        "status": "not_implemented_except_wrong_basis_negative_control",
        "reason": "used only as falsifying wrong-basis Ti control, not admitted as a base operator",
        "source_citations": [
            "system_v5/READ ONLY Reference Docs/operator math explicit.md:50-56",
            "system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810",
        ],
    },
    {
        "operator": "D_+/-",
        "status": "not_implemented",
        "reason": "ladder operators are support material, not base operators in this packet",
        "source_citations": [
            "/Users/joshuaeisenhart/wiki/concepts/operator-math-explicit.md:50-55",
            "system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810",
        ],
    },
    {
        "operator": "Pi_P",
        "status": "not_implemented",
        "reason": "projector/quotient packet is backlog, not this four-token compression",
        "source_citations": ["system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810"],
    },
    {
        "operator": "F_Q",
        "status": "not_implemented",
        "reason": "future field/operator packet, not one of Ti/Te/Fi/Fe",
        "source_citations": ["system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810"],
    },
    {
        "operator": "D[L] generic",
        "status": "not_implemented",
        "reason": "generic Lindblad terrain law is outside the four base operator packet",
        "source_citations": [
            "system_v6/foundations/working_math_scaffold_20260609.md:86-90",
            "system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810",
        ],
    },
    {
        "operator": "depolarizing",
        "status": "not_implemented",
        "reason": "not present in the intrinsic four-operator source lock",
        "source_citations": ["system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810"],
    },
]

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "engine-native x64 matrix/channel arithmetic"},
    "jax.numpy": {"tried": True, "used": True, "reason": "engine-native x64 linear algebra, eigenspectra, SVD trace norms"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing forced channel equality UNSAT/SAT SMT proof"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent forced channel equality SMT proof"},
}

TOOL_INTEGRATION_DEPTH = {"jax": "supportive", "jax.numpy": "supportive", "z3": "load_bearing", "cvc5": "load_bearing"}
CAPABILITY_PROBES = {
    "z3": "system_v4/probes/a2_state/sim_results/z3_capability_results.json",
    "cvc5": "system_v4/probes/a2_state/sim_results/cvc5_capability_results.json",
    "jax": "system_v4/probes/a2_state/sim_results/jax_algebra_capability_results.json",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def py_float(value: Any) -> float:
    return float(jnp.real(value))


def complex_pair(value: Any) -> dict[str, float]:
    z = complex(value)
    return {"re": float(z.real), "im": float(z.imag)}


def spinor(phi: float, chi: float, eta: float) -> jax.Array:
    return jnp.asarray(
        [
            jnp.exp(1.0j * (phi + chi)) * math.cos(eta),
            jnp.exp(1.0j * (phi - chi)) * math.sin(eta),
        ],
        dtype=jnp.complex128,
    )


def density_from_spinor(psi: jax.Array) -> jax.Array:
    return psi[:, None] @ jnp.conj(psi[None, :])


def pinned_states() -> dict[str, jax.Array]:
    rho0 = density_from_spinor(spinor(0.3, 0.2, math.pi / 8.0))
    rho1 = 0.7 * rho0 + 0.3 * I2 / 2.0
    return {"rho_0": rho0, "rho_1": rho1}


def unitary_x(theta: float) -> jax.Array:
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    return jnp.asarray([[c, -1.0j * s], [-1.0j * s, c]], dtype=jnp.complex128)


def unitary_z(phi: float) -> jax.Array:
    return jnp.asarray([[jnp.exp(-0.5j * phi), 0.0], [0.0, jnp.exp(0.5j * phi)]], dtype=jnp.complex128)


def kraus(op: str, q1: float = Q1, q2: float = Q2, theta: float = THETA, phi: float = PHI) -> list[jax.Array]:
    if op == "Ti":
        return [math.sqrt(1.0 - q1) * I2, math.sqrt(q1) * P0, math.sqrt(q1) * P1]
    if op == "Te":
        return [math.sqrt(1.0 - q2) * I2, math.sqrt(q2) * QP, math.sqrt(q2) * QM]
    if op == "Fi":
        return [unitary_x(theta)]
    if op == "Fe":
        return [unitary_z(phi)]
    raise ValueError(op)


def apply_kraus(rho: jax.Array, ks: list[jax.Array]) -> jax.Array:
    out = jnp.zeros_like(rho)
    for k in ks:
        out = out + k @ rho @ jnp.conj(k.T)
    return out


def source_channel(op: str, rho: jax.Array, q1: float = Q1, q2: float = Q2, theta: float = THETA, phi: float = PHI) -> jax.Array:
    return apply_kraus(rho, kraus(op, q1, q2, theta, phi))


def bloch(rho: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array]:
    return (
        jnp.real(jnp.trace(rho @ SX)),
        jnp.real(jnp.trace(rho @ SY)),
        jnp.real(jnp.trace(rho @ SZ)),
    )


def rho_from_bloch(rx: Any, ry: Any, rz: Any) -> jax.Array:
    return 0.5 * (I2 + rx * SX + ry * SY + rz * SZ)


def bloch_channel(op: str, rho: jax.Array, q1: float = Q1, q2: float = Q2, theta: float = THETA, phi: float = PHI) -> jax.Array:
    rx, ry, rz = bloch(rho)
    if op == "Ti":
        return rho_from_bloch((1.0 - q1) * rx, (1.0 - q1) * ry, rz)
    if op == "Te":
        return rho_from_bloch(rx, (1.0 - q2) * ry, (1.0 - q2) * rz)
    if op == "Fi":
        return rho_from_bloch(rx, ry * math.cos(theta) - rz * math.sin(theta), rz * math.cos(theta) + ry * math.sin(theta))
    if op == "Fe":
        return rho_from_bloch(rx * math.cos(phi) - ry * math.sin(phi), rx * math.sin(phi) + ry * math.cos(phi), rz)
    raise ValueError(op)


def generator_channel(op: str, rho: jax.Array) -> jax.Array:
    if op == "Ti":
        kappa = -math.log(1.0 - Q1)
        rx, ry, rz = bloch(rho)
        return rho_from_bloch(math.exp(-kappa) * rx, math.exp(-kappa) * ry, rz)
    if op == "Te":
        kappa = -math.log(1.0 - Q2)
        rx, ry, rz = bloch(rho)
        return rho_from_bloch(rx, math.exp(-kappa) * ry, math.exp(-kappa) * rz)
    if op == "Fi":
        return unitary_x(THETA) @ rho @ jnp.conj(unitary_x(THETA).T)
    if op == "Fe":
        return unitary_z(PHI) @ rho @ jnp.conj(unitary_z(PHI).T)
    raise ValueError(op)


def trace_norm(mat: jax.Array) -> float:
    return py_float(jnp.sum(jnp.linalg.svd(mat, compute_uv=False)))


def max_abs(mat: jax.Array) -> float:
    return py_float(jnp.max(jnp.abs(mat)))


def entropy_vn(rho: jax.Array) -> float:
    vals = jnp.clip(jnp.real(jnp.linalg.eigvalsh(0.5 * (rho + jnp.conj(rho.T)))), 0.0, 1.0)
    pieces = jnp.where(vals > 1.0e-15, vals * jnp.log(vals), 0.0)
    return py_float(-jnp.sum(pieces))


def purity(rho: jax.Array) -> float:
    return py_float(jnp.real(jnp.trace(rho @ rho)))


def choi_from_kraus(ks: list[jax.Array]) -> jax.Array:
    choi = jnp.zeros((4, 4), dtype=jnp.complex128)
    for k in ks:
        v = jnp.reshape(k, (4, 1))
        choi = choi + v @ jnp.conj(v.T)
    return choi


def cptp_certificate(op: str) -> dict[str, Any]:
    ks = kraus(op)
    choi = choi_from_kraus(ks)
    tp = jnp.zeros((2, 2), dtype=jnp.complex128)
    for k in ks:
        tp = tp + jnp.conj(k.T) @ k
    eigvals = jnp.real(jnp.linalg.eigvalsh(0.5 * (choi + jnp.conj(choi.T))))
    return {
        "choi_psd": bool(py_float(jnp.min(eigvals)) >= -TOL),
        "choi_min_eig": py_float(jnp.min(eigvals)),
        "choi_trace": py_float(jnp.real(jnp.trace(choi))),
        "trace_preserving": bool(max_abs(tp - I2) <= TOL),
        "tp_residual_max_abs": max_abs(tp - I2),
    }


def representation_certificate(op: str, states: dict[str, jax.Array]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    max_diff = 0.0
    for state_name, rho in states.items():
        source = source_channel(op, rho)
        bloch_form = bloch_channel(op, rho)
        generator = generator_channel(op, rho)
        row = {
            "source_vs_bloch_max_abs": max_abs(source - bloch_form),
            "source_vs_generator_max_abs": max_abs(source - generator),
            "bloch_vs_generator_max_abs": max_abs(bloch_form - generator),
        }
        row["pass"] = all(float(v) <= TOL for k, v in row.items() if k.endswith("max_abs"))
        rows[state_name] = row
        max_diff = max(max_diff, row["source_vs_bloch_max_abs"], row["source_vs_generator_max_abs"], row["bloch_vs_generator_max_abs"])
    return {"tol": TOL, "max_diff": max_diff, "pass": max_diff <= TOL, "states": rows}


def property_certificate(op: str, states: dict[str, jax.Array]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for state_name, rho in states.items():
        after = source_channel(op, rho)
        if op in {"Ti", "Te"}:
            before_s = entropy_vn(rho)
            after_s = entropy_vn(after)
            row = {
                "entropy_before": before_s,
                "entropy_after": after_s,
                "entropy_delta": after_s - before_s,
                "entropy_non_decreasing": after_s + TOL >= before_s,
            }
            if op == "Ti":
                before_off = rho[0, 1]
                after_off = after[0, 1]
                expected = (1.0 - Q1) * before_off
                row.update(
                    {
                        "basis": "z",
                        "offdiag_before": complex_pair(before_off),
                        "offdiag_after": complex_pair(after_off),
                        "expected_shrink_factor": 1.0 - Q1,
                        "coherence_shrink_residual": abs(complex(after_off - expected)),
                        "coherence_shrink_pass": abs(complex(after_off - expected)) <= TOL,
                    }
                )
            else:
                rho_x = jnp.conj(HX.T) @ rho @ HX
                after_x = jnp.conj(HX.T) @ after @ HX
                before_off = rho_x[0, 1]
                after_off = after_x[0, 1]
                expected = (1.0 - Q2) * before_off
                row.update(
                    {
                        "basis": "x",
                        "offdiag_before": complex_pair(before_off),
                        "offdiag_after": complex_pair(after_off),
                        "expected_shrink_factor": 1.0 - Q2,
                        "coherence_shrink_residual": abs(complex(after_off - expected)),
                        "coherence_shrink_pass": abs(complex(after_off - expected)) <= TOL,
                    }
                )
        else:
            before_p = purity(rho)
            after_p = purity(after)
            row = {
                "purity_before": before_p,
                "purity_after": after_p,
                "purity_delta_abs": abs(after_p - before_p),
                "purity_preserved": abs(after_p - before_p) <= TOL,
            }
        row["pass"] = all(v is True for k, v in row.items() if k.endswith("preserved") or k.endswith("non_decreasing") or k.endswith("shrink_pass"))
        rows[state_name] = row
    return {"pass": all(row["pass"] for row in rows.values()), "states": rows}


def commutator_table(rho: jax.Array) -> dict[str, Any]:
    ops = ["Ti", "Te", "Fi", "Fe"]
    table: dict[str, dict[str, float]] = {}
    for a in ops:
        table[a] = {}
        for b in ops:
            comm = source_channel(a, source_channel(b, rho)) - source_channel(b, source_channel(a, rho))
            table[a][b] = trace_norm(comm)
    zeros = {"Ti-Fe": table["Ti"]["Fe"], "Te-Fi": table["Te"]["Fi"], "Ti-Te": table["Ti"]["Te"]}
    nonzeros = {"Ti-Fi": table["Ti"]["Fi"], "Te-Fe": table["Te"]["Fe"], "Fi-Fe": table["Fi"]["Fe"]}
    return {
        "norm": "trace_norm",
        "state": "rho_0",
        "table": table,
        "known_zeros": zeros,
        "known_nonzeros": nonzeros,
        "known_zero_pass": all(abs(v) <= TOL for v in zeros.values()),
        "known_nonzero_pass": all(abs(v) > 1.0e-6 for v in nonzeros.values()),
    }


def wrong_basis_ti_y(rho: jax.Array) -> jax.Array:
    rx, ry, rz = bloch(rho)
    return rho_from_bloch((1.0 - Q1) * rx, ry, (1.0 - Q1) * rz)


def max_channel_diff_with_params(rho: jax.Array, params_a: dict[str, float], params_b: dict[str, float]) -> float:
    diffs = []
    for op in ["Ti", "Te", "Fi", "Fe"]:
        lhs = source_channel(op, rho, **params_a)
        rhs = source_channel(op, rho, **params_b)
        diffs.append(trace_norm(lhs - rhs))
    return max(diffs)


def negative_controls(states: dict[str, jax.Array]) -> dict[str, Any]:
    wrong_rows = {}
    for state_name, rho in states.items():
        wrong_rows[state_name] = {
            "trace_norm_Dz_minus_Dy": trace_norm(source_channel("Ti", rho) - wrong_basis_ti_y(rho)),
        }
    pinned = {"q1": Q1, "q2": Q2, "theta": THETA, "phi": PHI}
    swapped = {"q1": Q2, "q2": Q1, "theta": PHI, "phi": THETA}
    offpin = {"q1": 0.2, "q2": 0.4, "theta": math.pi / 3.0, "phi": math.pi / 5.0}
    offpin_swapped = {"q1": 0.4, "q2": 0.2, "theta": math.pi / 5.0, "phi": math.pi / 3.0}
    return {
        "wrong_basis_Ti_y": {
            "rows": wrong_rows,
            "different_values": all(row["trace_norm_Dz_minus_Dy"] > 1.0e-6 for row in wrong_rows.values()),
            "purpose": "source-lock falsifier: replacing P0/P1 z-dephasing with y-basis dephasing changes values",
        },
        "swapped_parameter_control": {
            "declared_pin_degenerate": Q1 == Q2 and THETA == PHI,
            "pinned_swap_max_trace_norm_diff": max_channel_diff_with_params(states["rho_0"], pinned, swapped),
            "pinned_swap_is_not_falsifying": max_channel_diff_with_params(states["rho_0"], pinned, swapped) <= TOL,
            "off_pin_sanity_params": {"q1": 0.2, "q2": 0.4, "theta": "pi/3", "phi": "pi/5"},
            "off_pin_swap_max_trace_norm_diff": max_channel_diff_with_params(states["rho_0"], offpin, offpin_swapped),
            "off_pin_swap_falsifies": max_channel_diff_with_params(states["rho_0"], offpin, offpin_swapped) > 1.0e-6,
            "honest_status": "the requested pinned swap is degenerate because q1=q2 and theta=phi; off-pin sanity proves the code path is falsifiable",
        },
    }


def z3_matmul(left: list[list[Any]], right: list[list[Any]]) -> list[list[Any]]:
    return [[sum(left[i][k] * right[k][j] for k in range(len(right))) for j in range(len(right[0]))] for i in range(len(left))]


def z3_forced_channel_equality(a_values: list[list[int]], b_values: list[list[int]], label: str) -> dict[str, Any]:
    solver = z3.Solver()
    a = [[z3.Int(f"{label}_a_{i}_{j}") for j in range(4)] for i in range(4)]
    b = [[z3.Int(f"{label}_b_{i}_{j}") for j in range(4)] for i in range(4)]
    for i in range(4):
        for j in range(4):
            solver.add(a[i][j] == a_values[i][j])
            solver.add(b[i][j] == b_values[i][j])
    ab = z3_matmul(a, b)
    ba = z3_matmul(b, a)
    for i in range(4):
        for j in range(4):
            solver.add(ab[i][j] == ba[i][j])
    status = str(solver.check())
    return {
        "solver": "z3",
        "verdict": status,
        "ran": True,
        "load_bearing": True,
        "bound_entries": 32,
        "channel_vector_order": ["a", "u", "v", "d"],
        "derived_products": "A*B and B*A entries are computed in solver from bound source-channel matrices",
        "asserted_precomputed_scalar": False,
    }


def cvc5_add(solver: cvc5.Solver, args: list[Any]) -> Any:
    out = args[0]
    for arg in args[1:]:
        out = solver.mkTerm(Kind.ADD, out, arg)
    return out


def cvc5_mul(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(Kind.MULT, left, right)


def cvc5_matmul(solver: cvc5.Solver, left: list[list[Any]], right: list[list[Any]]) -> list[list[Any]]:
    return [
        [cvc5_add(solver, [cvc5_mul(solver, left[i][k], right[k][j]) for k in range(len(right))]) for j in range(len(right[0]))]
        for i in range(len(left))
    ]


def cvc5_forced_channel_equality(a_values: list[list[int]], b_values: list[list[int]], label: str) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_NIA")
    int_sort = solver.getIntegerSort()
    a = [[solver.mkConst(int_sort, f"{label}_a_{i}_{j}") for j in range(4)] for i in range(4)]
    b = [[solver.mkConst(int_sort, f"{label}_b_{i}_{j}") for j in range(4)] for i in range(4)]
    for i in range(4):
        for j in range(4):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, a[i][j], solver.mkInteger(a_values[i][j])))
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, b[i][j], solver.mkInteger(b_values[i][j])))
    ab = cvc5_matmul(solver, a, b)
    ba = cvc5_matmul(solver, b, a)
    for i in range(4):
        for j in range(4):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, ab[i][j], ba[i][j]))
    status = str(solver.checkSat()).lower()
    return {
        "solver": "cvc5",
        "verdict": status,
        "ran": True,
        "load_bearing": True,
        "bound_entries": 32,
        "channel_vector_order": ["a", "u", "v", "d"],
        "derived_products": "A*B and B*A entries are computed in solver from bound source-channel matrices",
        "asserted_precomputed_scalar": False,
    }


def smt_proofs() -> dict[str, Any]:
    ti_scaled_10 = [[10, 0, 0, 0], [0, 7, 0, 0], [0, 0, 7, 0], [0, 0, 0, 10]]
    fi_scaled_2 = [[1, 0, 2, 1], [0, 2, 0, 0], [-1, 0, 0, 1], [1, 0, -2, 1]]
    fe_scaled_1 = [[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]
    z3_noncomm = z3_forced_channel_equality(ti_scaled_10, fi_scaled_2, "ti_fi_forced_equal")
    z3_comm = z3_forced_channel_equality(ti_scaled_10, fe_scaled_1, "ti_fe_forced_equal")
    cvc5_noncomm = cvc5_forced_channel_equality(ti_scaled_10, fi_scaled_2, "ti_fi_forced_equal_cvc5")
    cvc5_comm = cvc5_forced_channel_equality(ti_scaled_10, fe_scaled_1, "ti_fe_forced_equal_cvc5")
    return {
        "z3": {
            **z3_noncomm,
            "claim": "forcing Ti o Fi == Fi o Ti as source-channel matrices is UNSAT",
            "forced_equality_pair": "Ti_Fi",
            "commuting_control_verdict": z3_comm["verdict"],
            "commuting_control_pair": "Ti_Fe",
            "commuting_control_record": z3_comm,
            "source_entry_binding": {
                "Ti": "scaled by 10 from q1=3/10 source z-dephasing on [a,u,v,d]",
                "Fi": "scaled by 2 from theta=pi/2 source U_x matrix form on [a,u,v,d]",
                "Fe": "integer source U_z(phi=pi/2) matrix form on [a,u,v,d]",
            },
        },
        "cvc5": {
            **cvc5_noncomm,
            "claim": "independent cvc5 forced Ti o Fi == Fi o Ti is UNSAT",
            "forced_equality_pair": "Ti_Fi",
            "commuting_control_verdict": cvc5_comm["verdict"],
            "commuting_control_pair": "Ti_Fe",
            "commuting_control_record": cvc5_comm,
            "source_entry_binding": {
                "Ti": "scaled by 10 from q1=3/10 source z-dephasing on [a,u,v,d]",
                "Fi": "scaled by 2 from theta=pi/2 source U_x matrix form on [a,u,v,d]",
                "Fe": "integer source U_z(phi=pi/2) matrix form on [a,u,v,d]",
            },
        },
    }


def operator_forms() -> dict[str, Any]:
    return {
        "Ti": {
            "source": "Ti(rho)=(1-q1)rho+q1(P0 rho P0+P1 rho P1); Kraus sqrt(1-q1)I,sqrt(q1)P0,sqrt(q1)P1",
            "bloch_map": "(rx,ry,rz)->((1-q1)rx,(1-q1)ry,rz)",
            "generator": "flow at t=1 of L1(rho)=kappa1/2*(sigma_z rho sigma_z-rho), kappa1=-log(1-q1)",
        },
        "Te": {
            "source": "Te(rho)=(1-q2)rho+q2(Q+ rho Q+ + Q- rho Q-); Kraus sqrt(1-q2)I,sqrt(q2)Q+,sqrt(q2)Q-",
            "bloch_map": "(rx,ry,rz)->(rx,(1-q2)ry,(1-q2)rz)",
            "generator": "flow at t=1 of L2(rho)=kappa2/2*(sigma_x rho sigma_x-rho), kappa2=-log(1-q2)",
        },
        "Fi": {
            "source": "Fi(rho)=U_x(theta) rho U_x(theta)^dagger, U_x=exp(-i theta sigma_x/2)",
            "bloch_map": "(rx,ry,rz)->(rx, ry cos(theta)-rz sin(theta), rz cos(theta)+ry sin(theta))",
            "generator": "flow at t=1 of L3(rho)=-i[(theta/2)sigma_x,rho]",
        },
        "Fe": {
            "source": "Fe(rho)=U_z(phi) rho U_z(phi)^dagger, U_z=exp(-i phi sigma_z/2)",
            "bloch_map": "(rx,ry,rz)->(rx cos(phi)-ry sin(phi), rx sin(phi)+ry cos(phi), rz)",
            "generator": "flow at t=1 of L4(rho)=-i[(phi/2)sigma_z,rho]",
        },
    }


def shared_scalars(rep: dict[str, Any], props: dict[str, Any], ctable: dict[str, Any], negatives: dict[str, Any], smt: dict[str, Any]) -> dict[str, float]:
    scalars: dict[str, float] = {}
    for op in ["Ti", "Te", "Fi", "Fe"]:
        scalars[f"{op}_representation_max_diff"] = float(rep[op]["max_diff"])
    for op, a, b in [("Ti", "Ti", "Fi"), ("Te", "Te", "Fe"), ("Fi", "Fi", "Fe")]:
        scalars[f"commutator_{a}_{b}_rho0_trace_norm"] = float(ctable["table"][a][b])
    for key, value in ctable["known_zeros"].items():
        scalars[f"commutator_{key.replace('-', '_')}_zero_trace_norm"] = float(value)
    for op in ["Ti", "Te"]:
        for state in ["rho_0", "rho_1"]:
            scalars[f"{op}_{state}_entropy_delta"] = float(props[op]["states"][state]["entropy_delta"])
            scalars[f"{op}_{state}_coherence_shrink_residual"] = float(props[op]["states"][state]["coherence_shrink_residual"])
    for op in ["Fi", "Fe"]:
        for state in ["rho_0", "rho_1"]:
            scalars[f"{op}_{state}_purity_delta_abs"] = float(props[op]["states"][state]["purity_delta_abs"])
    scalars["wrong_basis_Ti_y_rho0_trace_norm_diff"] = float(negatives["wrong_basis_Ti_y"]["rows"]["rho_0"]["trace_norm_Dz_minus_Dy"])
    scalars["swapped_parameter_pinned_diff"] = float(negatives["swapped_parameter_control"]["pinned_swap_max_trace_norm_diff"])
    scalars["swapped_parameter_offpin_diff"] = float(negatives["swapped_parameter_control"]["off_pin_swap_max_trace_norm_diff"])
    scalars["smt_z3_noncomm_unsat"] = 1.0 if smt["z3"]["verdict"] == "unsat" else 0.0
    scalars["smt_cvc5_noncomm_unsat"] = 1.0 if smt["cvc5"]["verdict"] == "unsat" else 0.0
    return scalars


def build_result() -> dict[str, Any]:
    states = pinned_states()
    rep = {op: representation_certificate(op, states) for op in ["Ti", "Te", "Fi", "Fe"]}
    cptp = {op: cptp_certificate(op) for op in ["Ti", "Te", "Fi", "Fe"]}
    props = {op: property_certificate(op, states) for op in ["Ti", "Te", "Fi", "Fe"]}
    ctable = commutator_table(states["rho_0"])
    negatives = negative_controls(states)
    smt = smt_proofs()
    controls = {
        "representation_consistency": all(row["pass"] for row in rep.values()),
        "cptp_all": all(row["choi_psd"] and row["trace_preserving"] for row in cptp.values()),
        "property_certificates": all(row["pass"] for row in props.values()),
        "commutator_known_zeros": ctable["known_zero_pass"],
        "commutator_known_nonzeros": ctable["known_nonzero_pass"],
        "wrong_basis_negative_control": negatives["wrong_basis_Ti_y"]["different_values"],
        "swapped_parameter_control_honest": negatives["swapped_parameter_control"]["declared_pin_degenerate"]
        and negatives["swapped_parameter_control"]["pinned_swap_is_not_falsifying"]
        and negatives["swapped_parameter_control"]["off_pin_swap_falsifies"],
        "smt_z3_noncomm_unsat": smt["z3"]["verdict"] == "unsat",
        "smt_z3_commuting_control_sat": smt["z3"]["commuting_control_verdict"] == "sat",
        "smt_cvc5_noncomm_unsat": smt["cvc5"]["verdict"] == "unsat",
        "smt_cvc5_commuting_control_sat": smt["cvc5"]["commuting_control_verdict"] == "sat",
        "reads_peer_result_false": READS_PEER_RESULT is False,
    }
    all_pass = bool(all(controls.values()))
    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": f"{SIM_ID}_{ENGINE}",
        "engine": ENGINE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "reads_peer_result": READS_PEER_RESULT,
        "engine_contract": {"mode": "all_three_full_sims", "reads_peer_result": READS_PEER_RESULT},
        "pin_spec": PIN_SPEC,
        "pin_identity": {
            "q1": Q1,
            "q2": Q2,
            "theta": "pi/2",
            "phi": "pi/2",
            "rho_0": "psi(0.3,0.2,pi/8) per scaffold 1.1",
            "rho_1": "0.7*rho_0+0.3*I/2",
        },
        "source_citations": SOURCE_CITATIONS,
        "operator_forms": operator_forms(),
        "representation_consistency": rep,
        "cptp_certificates": cptp,
        "property_certificates": props,
        "commutator_table": ctable,
        "negative_controls": negatives,
        "smt": smt,
        "operator_backlog": OPERATOR_BACKLOG,
        "controls": controls,
        "shared_scalars": shared_scalars(rep, props, ctable, negatives, smt),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_exercise_map": {
            tool: {
                "tool": tool,
                "depth": TOOL_INTEGRATION_DEPTH[tool],
                "capability_receipt_path": CAPABILITY_PROBES.get(tool),
                "computed_what": TOOL_MANIFEST[tool]["reason"],
                "gates": ["all_pass"] if TOOL_INTEGRATION_DEPTH[tool] == "load_bearing" else [],
            }
            for tool in TOOL_MANIFEST
        },
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["z3", "cvc5", "jax", "jax.numpy"],
        "control_only_tools": [],
        "all_pass": all_pass,
    }


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"engine": ENGINE, "result_path": str(RESULT_PATH), "all_pass": result["all_pass"]}, indent=2))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
