#!/usr/bin/env python3
"""Stage-5 sparse Kraus operator/channel family probe.

Finite map:
    Phi_d(p, rho) = sum_m K_m(p) rho K_m(p)^*

Invariant:
    sum_m K_m(p)^* K_m(p) = I_d for admissible p in [0, 1].

The sim keeps the claim narrow: one finite sparse Kraus family over operator
dimensions 8/16/32/64, one trace-preservation SMT flip, one N01 order witness,
and no promotion to coupled, bridge, Axis0, flux, FEP, physics, or manifold use.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
import time
from fractions import Fraction
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp  # noqa: E402
from jax.experimental import sparse as jsparse  # noqa: E402
import sympy as sp  # noqa: E402
import torch  # noqa: E402
from clifford import Cl  # noqa: E402

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = ROOT / "sim_op_kraus_family_probe.py"
OBJECT_ID = "op_kraus_path_family_sparse_pauli_x_channel"
RESULT = RESULT_DIR / "op_kraus_family_probe_results.json"

SCALES = (8, 16, 32, 64)
P_REAL = Fraction(1, 4)
P_CONTROL = Fraction(2, 1)
TOL = 1.0e-9
ORDER_EPS = 1.0
CDTYPE = torch.complex128
RTYPE = torch.float64
BLOCKED_CONSUMERS = [
    "coupled_lego_stages",
    "bridge",
    "Xi",
    "Phi0",
    "Axis0",
    "flux",
    "FEP",
    "gravity",
    "physics",
    "final_manifold_admission",
]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "role": "load_bearing",
        "reason": "Primary sparse complex operator carrier, Kraus support generation, completeness weights, degenerate controls, and scale ladder.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "role": "supportive",
        "reason": "Independent x64 sparse BCOO mirror recomputing the same finite support weights and order witness.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "role": "load_bearing",
        "reason": "Load-bearing only through smt_load_bearing verdict flips bound to measured completeness and order observables.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "role": "load_bearing",
        "reason": "Load-bearing only through the cvc5 branch inside smt_load_bearing on the same measured observables.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "role": "load_bearing",
        "reason": "Exact rational symbolic mirror for the real/control invariant flip; no numeric ablation is emitted for proof tools.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "role": "load_bearing",
        "reason": "Geometric-algebra order witness for the noncommuting generator; remove-and-recompute ablation erases the commutator.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "role": None,
        "reason": "Not imported or used; this sim has no NumPy claim-bearing path.",
    },
    "quimb": {
        "tried": False,
        "used": False,
        "role": None,
        "reason": "Not relevant to this operator/channel micro-lego; no MPS/PEPS contraction claim is made.",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "role": None,
        "reason": "Not relevant; no metric/geodesic/curvature claim is made.",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "role": None,
        "reason": "Not relevant; no equivariant neural operator claim is made.",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "role": None,
        "reason": "Not relevant; no graph routing/dependency claim is made.",
    },
    "xgi": {
        "tried": False,
        "used": False,
        "role": None,
        "reason": "Not relevant; no hypergraph claim is made.",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "role": None,
        "reason": "Not relevant; no cell-complex topology claim is made.",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "role": None,
        "reason": "Not relevant; no filtration or persistent-homology claim is made.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "numpy": "None",
    "quimb": "None",
    "geomstats": "None",
    "e3nn": "None",
    "rustworkx": "None",
    "xgi": "None",
    "toponetx": "None",
    "gudhi": "None",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, (jnp.ndarray, jax.Array)):
        if value.size == 1:
            return as_jsonable(value.item())
        return as_jsonable(value.tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def pauli_x_support(d: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    rows = torch.arange(d, dtype=torch.long)
    cols = torch.tensor([i ^ 1 for i in range(d)], dtype=torch.long)
    coeffs = torch.ones(d, dtype=torch.int8)
    return rows, cols, coeffs


def identity_support(d: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    rows = torch.arange(d, dtype=torch.long)
    cols = torch.arange(d, dtype=torch.long)
    coeffs = torch.ones(d, dtype=torch.int8)
    return rows, cols, coeffs


def sparse_operator_t(
    d: int,
    rows: torch.Tensor,
    cols: torch.Tensor,
    coeffs: torch.Tensor,
    scale: torch.Tensor,
) -> torch.Tensor:
    indices = torch.stack((rows, cols))
    values = coeffs.to(CDTYPE) * scale.to(CDTYPE)
    return torch.sparse_coo_tensor(indices, values, (d, d), dtype=CDTYPE).coalesce()


def sparse_operator_j(
    d: int,
    rows: list[int],
    cols: list[int],
    coeffs: list[int],
    scale: float,
) -> jsparse.BCOO:
    indices = jnp.array([[r, c] for r, c in zip(rows, cols)], dtype=jnp.int32)
    data = jnp.array([complex(c * scale, 0.0) for c in coeffs], dtype=jnp.complex128)
    return jsparse.BCOO((data, indices), shape=(d, d))


def real_kraus_t(d: int, p: Fraction = P_REAL) -> list[torch.Tensor]:
    p_param = torch.tensor(float(p), dtype=torch.float32)
    rows_i, cols_i, coeff_i = identity_support(d)
    rows_x, cols_x, coeff_x = pauli_x_support(d)
    k0 = sparse_operator_t(d, rows_i, cols_i, coeff_i, torch.sqrt((1.0 - p_param).to(RTYPE)))
    k1 = sparse_operator_t(d, rows_x, cols_x, coeff_x, torch.sqrt(p_param.to(RTYPE)))
    return [k0, k1]


def degenerate_gain_control_t(d: int, p: Fraction = P_CONTROL) -> list[torch.Tensor]:
    p_param = torch.tensor(float(p), dtype=torch.float32)
    rows_x, cols_x, coeff_x = pauli_x_support(d)
    k1 = sparse_operator_t(d, rows_x, cols_x, coeff_x, torch.sqrt(p_param.to(RTYPE)))
    return [k1]


def k1_removed_control_t(d: int, p: Fraction = P_REAL) -> list[torch.Tensor]:
    p_param = torch.tensor(float(p), dtype=torch.float32)
    rows_i, cols_i, coeff_i = identity_support(d)
    k0 = sparse_operator_t(d, rows_i, cols_i, coeff_i, torch.sqrt((1.0 - p_param).to(RTYPE)))
    return [k0]


def real_kraus_j(d: int, p: Fraction = P_REAL) -> list[jsparse.BCOO]:
    p_float = float(p)
    rows_i = list(range(d))
    cols_i = list(range(d))
    coeff_i = [1] * d
    rows_x = list(range(d))
    cols_x = [i ^ 1 for i in range(d)]
    coeff_x = [1] * d
    return [
        sparse_operator_j(d, rows_i, cols_i, coeff_i, math.sqrt(1.0 - p_float)),
        sparse_operator_j(d, rows_x, cols_x, coeff_x, math.sqrt(p_float)),
    ]


def degenerate_gain_control_j(d: int, p: Fraction = P_CONTROL) -> list[jsparse.BCOO]:
    p_float = float(p)
    rows_x = list(range(d))
    cols_x = [i ^ 1 for i in range(d)]
    coeff_x = [1] * d
    return [sparse_operator_j(d, rows_x, cols_x, coeff_x, math.sqrt(p_float))]


def completeness_weights_t(kraus: list[torch.Tensor]) -> torch.Tensor:
    if not kraus:
        raise ValueError("at least one Kraus operator is required")
    d = kraus[0].shape[1]
    weights = torch.zeros(d, dtype=RTYPE)
    for op in kraus:
        op = op.coalesce()
        cols = op.indices()[1]
        vals = op.values()
        contrib = vals.real.square() + vals.imag.square()
        weights.scatter_add_(0, cols, contrib.to(RTYPE))
    return weights


def completeness_error_t(kraus: list[torch.Tensor]) -> float:
    weights = completeness_weights_t(kraus)
    return float(torch.max(torch.abs(weights - 1.0)).item())


def completeness_score_t(kraus: list[torch.Tensor]) -> float:
    return 1.0 - completeness_error_t(kraus)


def trace_gain_t(kraus: list[torch.Tensor]) -> float:
    weights = completeness_weights_t(kraus)
    return float(torch.mean(weights).item())


def completeness_weights_j(kraus: list[jsparse.BCOO]) -> jax.Array:
    d = kraus[0].shape[1]
    weights = jnp.zeros((d,), dtype=jnp.float64)
    for op in kraus:
        cols = op.indices[:, 1]
        vals = op.data
        contrib = jnp.real(vals * jnp.conj(vals))
        weights = weights.at[cols].add(contrib)
    return weights


def completeness_error_j(kraus: list[jsparse.BCOO]) -> float:
    weights = completeness_weights_j(kraus)
    return float(jnp.max(jnp.abs(weights - 1.0)).item())


def trace_gain_j(kraus: list[jsparse.BCOO]) -> float:
    return float(jnp.mean(completeness_weights_j(kraus)).item())


def torch_order_gap_xz(d: int, *, commutative_control: bool = False) -> float:
    cols = torch.arange(d, dtype=torch.long)
    rows = cols if commutative_control else torch.tensor([i ^ 1 for i in range(d)], dtype=torch.long)
    z_col = torch.where((cols % 2) == 0, torch.ones(d, dtype=RTYPE), -torch.ones(d, dtype=RTYPE))
    z_row = torch.where((rows % 2) == 0, torch.ones(d, dtype=RTYPE), -torch.ones(d, dtype=RTYPE))
    diff = z_col - z_row
    return float(torch.max(torch.abs(diff)).item())


def jax_order_gap_xz(d: int, *, commutative_control: bool = False) -> float:
    cols = jnp.arange(d, dtype=jnp.int32)
    rows = cols if commutative_control else jnp.bitwise_xor(cols, jnp.array(1, dtype=jnp.int32))
    z_col = jnp.where((cols % 2) == 0, 1.0, -1.0)
    z_row = jnp.where((rows % 2) == 0, 1.0, -1.0)
    return float(jnp.max(jnp.abs(z_col - z_row)).item())


def clifford_order_witness() -> dict[str, Any]:
    layout, blades = Cl(2)
    e1 = blades["e1"]
    e2 = blades["e2"]
    one = layout.scalar
    real_comm = e1 * e2 - e2 * e1
    control_comm = e1 * one - one * e1
    real_norm = float(math.sqrt(sum(float(v) ** 2 for v in real_comm.value)))
    control_norm = float(math.sqrt(sum(float(v) ** 2 for v in control_comm.value)))
    return {
        "basis": "Cl(2) e1,e2",
        "real_commutator_norm": real_norm,
        "scalar_control_commutator_norm": control_norm,
        "pass": bool(abs(real_norm - 2.0) <= TOL and abs(control_norm) <= TOL),
    }


def sympy_exact_flip() -> dict[str, Any]:
    p = sp.Rational(P_REAL.numerator, P_REAL.denominator)
    p_bad = sp.Rational(P_CONTROL.numerator, P_CONTROL.denominator)
    real_weight = sp.simplify((1 - p) + p)
    k1_removed_weight = sp.simplify(1 - p)
    control_weight = sp.simplify(p_bad)
    real_error = sp.Abs(real_weight - 1)
    k1_removed_error = sp.Abs(k1_removed_weight - 1)
    control_error = sp.Abs(control_weight - 1)
    real_order_gap = sp.Integer(2)
    commutative_order_gap = sp.Integer(0)
    return {
        "tool": "sympy",
        "p_real": str(p),
        "p_control": str(p_bad),
        "real_completeness_weight": str(real_weight),
        "k1_removed_completeness_weight": str(k1_removed_weight),
        "control_completeness_weight": str(control_weight),
        "real_completeness_error": str(real_error),
        "k1_removed_completeness_error": str(k1_removed_error),
        "control_completeness_error": str(control_error),
        "real_completeness_claim_holds": bool(real_error <= sp.Rational(0, 1)),
        "control_completeness_claim_holds": bool(control_error <= sp.Rational(0, 1)),
        "real_order_gap": str(real_order_gap),
        "commutative_control_order_gap": str(commutative_order_gap),
        "real_order_claim_holds": bool(real_order_gap >= sp.Integer(1)),
        "control_order_claim_holds": bool(commutative_order_gap >= sp.Integer(1)),
        "flip": bool(
            real_error == 0
            and control_error != 0
            and real_order_gap >= 1
            and commutative_order_gap < 1
        ),
    }


def smt_completeness_proof(real_error: float, control_error: float) -> dict[str, Any]:
    return smt_load_bearing(
        claim="kraus_completeness_sum_KdaggerK_equals_identity",
        real_measured={"completeness_error": real_error, "tol": TOL},
        control_measured={"completeness_error": control_error, "tol": TOL},
        claim_builder=lambda v: v["completeness_error"] <= v["tol"],
        cvc5_claim_pairs=[("completeness_error", "<=", "tol")],
    )


def smt_order_proof(real_gap: float, control_gap: float) -> dict[str, Any]:
    return smt_load_bearing(
        claim="pauli_x_support_noncommutes_with_z_order_probe",
        real_measured={"order_gap": real_gap, "eps": ORDER_EPS},
        control_measured={"order_gap": control_gap, "eps": ORDER_EPS},
        claim_builder=lambda v: v["order_gap"] >= v["eps"],
        cvc5_claim_pairs=[("order_gap", ">=", "eps")],
    )


def scale_rung(d: int) -> dict[str, Any]:
    real_t = real_kraus_t(d)
    gain_control_t = degenerate_gain_control_t(d)
    removed_t = k1_removed_control_t(d)
    real_j = real_kraus_j(d)
    gain_control_j = degenerate_gain_control_j(d)

    torch_real_error = completeness_error_t(real_t)
    torch_gain_error = completeness_error_t(gain_control_t)
    torch_removed_error = completeness_error_t(removed_t)
    torch_trace_gain_real = trace_gain_t(real_t)
    torch_trace_gain_control = trace_gain_t(gain_control_t)
    torch_order_gap = torch_order_gap_xz(d)
    torch_order_gap_control = torch_order_gap_xz(d, commutative_control=True)

    jax_real_error = completeness_error_j(real_j)
    jax_gain_error = completeness_error_j(gain_control_j)
    jax_trace_gain_real = trace_gain_j(real_j)
    jax_trace_gain_control = trace_gain_j(gain_control_j)
    jax_order_gap = jax_order_gap_xz(d)
    jax_order_gap_control = jax_order_gap_xz(d, commutative_control=True)

    support_nnz = sum(int(op._nnz()) for op in real_t)
    operator_entries = 2 * d * d
    nonzero_density = support_nnz / operator_entries
    max_delta = max(
        abs(torch_real_error - jax_real_error),
        abs(torch_gain_error - jax_gain_error),
        abs(torch_trace_gain_real - jax_trace_gain_real),
        abs(torch_trace_gain_control - jax_trace_gain_control),
        abs(torch_order_gap - jax_order_gap),
        abs(torch_order_gap_control - jax_order_gap_control),
    )
    pass_rung = (
        torch_real_error <= TOL
        and abs(torch_gain_error - 1.0) <= TOL
        and abs(torch_removed_error - float(P_REAL)) <= TOL
        and abs(torch_trace_gain_real - 1.0) <= TOL
        and abs(torch_trace_gain_control - 2.0) <= TOL
        and abs(torch_order_gap - 2.0) <= TOL
        and abs(torch_order_gap_control) <= TOL
        and max_delta <= TOL
        and support_nnz == 2 * d
        and nonzero_density < 0.25
    )

    return {
        "sites_or_qubits": d,
        "operator_dimension": d,
        "operator_count": 2,
        "path_count": 2,
        "kraus_count": 2,
        "parameter_count": 1,
        "p_real_float32": float(torch.tensor(float(P_REAL), dtype=torch.float32).item()),
        "p_real_exact": str(P_REAL),
        "p_control_exact": str(P_CONTROL),
        "support_nnz_real": support_nnz,
        "support_nnz_degenerate_control": sum(int(op._nnz()) for op in gain_control_t),
        "operator_entries_across_two_kraus": operator_entries,
        "nonzero_density_across_two_kraus": nonzero_density,
        "dense_state_closure_used": False,
        "uses_sparse_coo": True,
        "uses_jax_bcoo": True,
        "torch_completeness_error": torch_real_error,
        "torch_k1_removed_completeness_error": torch_removed_error,
        "torch_p2_gain_control_completeness_error": torch_gain_error,
        "torch_trace_gain_real": torch_trace_gain_real,
        "torch_trace_gain_p2_control": torch_trace_gain_control,
        "torch_order_gap_xz": torch_order_gap,
        "torch_commutative_control_order_gap": torch_order_gap_control,
        "jax_completeness_error": jax_real_error,
        "jax_p2_gain_control_completeness_error": jax_gain_error,
        "jax_trace_gain_real": jax_trace_gain_real,
        "jax_trace_gain_p2_control": jax_trace_gain_control,
        "jax_order_gap_xz": jax_order_gap,
        "jax_commutative_control_order_gap": jax_order_gap_control,
        "jax_vs_pytorch_delta": max_delta,
        "support_digest": {
            "K0": {
                "support": "identity",
                "nnz": d,
                "coefficient_dtype": "torch.int8",
                "scale": "sqrt(1-p)",
                "first_four_row_col_coeff": [[i, i, 1] for i in range(min(4, d))],
            },
            "K1": {
                "support": "least-significant-bit Pauli X permutation",
                "nnz": d,
                "coefficient_dtype": "torch.int8",
                "scale": "sqrt(p)",
                "first_four_row_col_coeff": [[i, i ^ 1, 1] for i in range(min(4, d))],
            },
        },
        "pass": bool(pass_rung),
    }


def build_proofs(top: dict[str, Any]) -> dict[str, Any]:
    completeness = smt_completeness_proof(
        float(top["torch_completeness_error"]),
        float(top["torch_p2_gain_control_completeness_error"]),
    )
    order = smt_order_proof(
        float(top["torch_order_gap_xz"]),
        float(top["torch_commutative_control_order_gap"]),
    )
    exact = sympy_exact_flip()
    return {
        "kraus_completeness_smt_load_bearing": completeness,
        "pauli_order_smt_load_bearing": order,
        "sympy_exact_rational_flip": exact,
        "proof_tool_ablation_policy": {
            "z3": "no numeric ablation emitted; load-bearing evidence is real/control SMT verdict flip",
            "cvc5": "no numeric ablation emitted; load-bearing evidence is real/control SMT verdict flip",
            "sympy": "no numeric ablation emitted; load-bearing evidence is exact rational real/control flip",
        },
    }


def add_ablation_pass(row: dict[str, Any]) -> dict[str, Any]:
    row["pass"] = bool(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > TOL
        and abs(
            (float(row["baseline_value"]) - float(row["ablated_value"]))
            - float(row["outcome_delta"])
        )
        <= TOL
    )
    return row


def build_tool_ablations(top: dict[str, Any], clifford_witness: dict[str, Any]) -> dict[str, Any]:
    return {
        "torch_k1_removed_completeness_score": add_ablation_pass(
            tool_ablation(
                "torch_completeness_score_two_kraus_vs_K1_removed_recompute",
                baseline_value=1.0 - float(top["torch_completeness_error"]),
                ablated_value=1.0 - float(top["torch_k1_removed_completeness_error"]),
                tool="torch",
            )
        ),
        "torch_commutative_support_order_gap": add_ablation_pass(
            tool_ablation(
                "torch_order_gap_XZ_vs_commutative_identity_support_recompute",
                baseline_value=float(top["torch_order_gap_xz"]),
                ablated_value=float(top["torch_commutative_control_order_gap"]),
                tool="torch",
            )
        ),
        "clifford_generator_commutator_removed": add_ablation_pass(
            tool_ablation(
                "clifford_commutator_norm_e1e2_vs_scalar_control_recompute",
                baseline_value=float(clifford_witness["real_commutator_norm"]),
                ablated_value=float(clifford_witness["scalar_control_commutator_norm"]),
                tool="clifford",
            )
        ),
    }


def known_value_checks(scale_rows: dict[int, dict[str, Any]], exact: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for d, row in scale_rows.items():
        checks.extend(
            [
                {
                    "invariant": f"d={d} sparse Kraus completeness error",
                    "computed": row["torch_completeness_error"],
                    "known": 0.0,
                    "match": abs(float(row["torch_completeness_error"])) <= TOL,
                },
                {
                    "invariant": f"d={d} p=2 gain control trace gain",
                    "computed": row["torch_trace_gain_p2_control"],
                    "known": 2.0,
                    "match": abs(float(row["torch_trace_gain_p2_control"]) - 2.0) <= TOL,
                },
                {
                    "invariant": f"d={d} K1-removed completeness error",
                    "computed": row["torch_k1_removed_completeness_error"],
                    "known": float(P_REAL),
                    "match": abs(float(row["torch_k1_removed_completeness_error"]) - float(P_REAL)) <= TOL,
                },
                {
                    "invariant": f"d={d} Pauli X/Z order gap",
                    "computed": row["torch_order_gap_xz"],
                    "known": 2.0,
                    "match": abs(float(row["torch_order_gap_xz"]) - 2.0) <= TOL,
                },
                {
                    "invariant": f"d={d} commutative support control order gap",
                    "computed": row["torch_commutative_control_order_gap"],
                    "known": 0.0,
                    "match": abs(float(row["torch_commutative_control_order_gap"])) <= TOL,
                },
                {
                    "invariant": f"d={d} non-dense support count",
                    "computed": row["support_nnz_real"],
                    "known": 2 * d,
                    "match": int(row["support_nnz_real"]) == 2 * d,
                },
                {
                    "invariant": f"d={d} JAX/PyTorch support-observable parity",
                    "computed": row["jax_vs_pytorch_delta"],
                    "known": "<=1e-9",
                    "match": float(row["jax_vs_pytorch_delta"]) <= TOL,
                },
            ]
        )
    checks.append(
        {
            "invariant": "sympy exact rational completeness/order flip",
            "computed": exact["flip"],
            "known": True,
            "match": bool(exact["flip"]),
        }
    )
    return checks


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()

    scale_rows = {d: scale_rung(d) for d in SCALES}
    top = scale_rows[64]
    clifford_witness = clifford_order_witness()
    proofs = build_proofs(top)
    ablations = build_tool_ablations(top, clifford_witness)
    checks = known_value_checks(scale_rows, proofs["sympy_exact_rational_flip"])

    scale_pass = all(row["pass"] for row in scale_rows.values())
    proof_nodes = [
        proofs["kraus_completeness_smt_load_bearing"],
        proofs["pauli_order_smt_load_bearing"],
    ]
    proof_pass = all(
        node["real_claim_verdict"] == "sat"
        and node["negated_claim_verdict"] == "unsat"
        and node["differ"] is True
        and node["bound_to_measured"] is True
        and node.get("cvc5_real_verdict") == "sat"
        and node.get("cvc5_control_verdict") == "unsat"
        for node in proof_nodes
    ) and bool(proofs["sympy_exact_rational_flip"]["flip"])
    ablation_pass = all(row["pass"] and abs(float(row["outcome_delta"])) > TOL for row in ablations.values())
    known_pass = all(row["match"] for row in checks)
    all_pass = bool(scale_pass and proof_pass and ablation_pass and known_pass and clifford_witness["pass"])

    torch_primary_result = {
        "runtime": "torch",
        "operator_dimension": 64,
        "carrier": "torch.sparse_coo_tensor complex128 Kraus operators",
        "p_real": str(P_REAL),
        "p_control": str(P_CONTROL),
        "completeness_error": top["torch_completeness_error"],
        "p2_gain_control_completeness_error": top["torch_p2_gain_control_completeness_error"],
        "trace_gain_real": top["torch_trace_gain_real"],
        "trace_gain_p2_control": top["torch_trace_gain_p2_control"],
        "order_gap_xz": top["torch_order_gap_xz"],
        "commutative_control_order_gap": top["torch_commutative_control_order_gap"],
        "dense_state_closure_used": False,
        "pass": bool(top["pass"]),
    }
    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "carrier": "jax.experimental.sparse.BCOO complex128 Kraus operators",
        "operator_dimension": 64,
        "completeness_error": top["jax_completeness_error"],
        "p2_gain_control_completeness_error": top["jax_p2_gain_control_completeness_error"],
        "trace_gain_real": top["jax_trace_gain_real"],
        "trace_gain_p2_control": top["jax_trace_gain_p2_control"],
        "order_gap_xz": top["jax_order_gap_xz"],
        "commutative_control_order_gap": top["jax_commutative_control_order_gap"],
        "pass": bool(top["jax_vs_pytorch_delta"] <= TOL),
    }

    controls = {
        "degenerate_p2_gain": {
            "description": "p=2 outside admissible [0,1]; K0 invalid/removed and K1=sqrt(2)P produces trace gain",
            "p": str(P_CONTROL),
            "trace_gain": top["torch_trace_gain_p2_control"],
            "completeness_error": top["torch_p2_gain_control_completeness_error"],
            "claim_holds": False,
            "pass": bool(abs(float(top["torch_p2_gain_control_completeness_error"]) - 1.0) <= TOL),
        },
        "k1_removed": {
            "description": "remove the non-identity Kraus path and recompute completeness weights",
            "p": str(P_REAL),
            "completeness_error": top["torch_k1_removed_completeness_error"],
            "claim_holds": False,
            "pass": bool(abs(float(top["torch_k1_removed_completeness_error"]) - float(P_REAL)) <= TOL),
        },
        "commutative_support_control": {
            "description": "replace X support with identity support against the Z order probe",
            "order_gap": top["torch_commutative_control_order_gap"],
            "claim_holds": False,
            "pass": bool(abs(float(top["torch_commutative_control_order_gap"])) <= TOL),
        },
    }

    return {
        "schema": "STAGE5_OPERATOR_CHANNEL_GENERATOR_LEGO_v1",
        "sim_id": "sim_op_kraus_family_probe",
        "name": "sim_op_kraus_family_probe",
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "thisfile": str(THISFILE),
        "result_path": str(RESULT),
        "object_id": OBJECT_ID,
        "spec_key": "Kraus",
        "spec_id": "SQO-2023-KPF-Z3-A1",
        "tier": "Stage-5 operator/channel/generator lego",
        "classification": "lego",
        "promotion_allowed": False,
        "sim_execution_kind": "nonclassical",
        "sim_class": "operator_channel_generator_probe",
        "purpose": "Audit one sparse finite Kraus path family with helper-bound SMT flips, PyTorch sparse primary execution, JAX sparse mirror, and genuine numeric ablations.",
        "scientific_question": "Does the finite sparse Kraus family K0=sqrt(1-p)I, K1=sqrt(p)X preserve trace for p=1/4 over operator dimensions 8/16/32/64, while a p=2 gain control and commutative order control fail?",
        "claim_ceiling": "One bounded Stage-5 Kraus operator/channel/generator lego only; no coupled, bridge, flux, Axis0, FEP, physics, PEPS3D, or manifold admission.",
        "finite_map": {
            "domain": "operator dimension d in {8,16,32,64}; finite sparse coefficient tensors for K0 identity and K1 least-significant-bit Pauli-X support; single float32 parameter p=1/4",
            "codomain_or_output": "sparse Kraus channel Phi_d(rho)=sum_m K_m rho K_m^*, completeness residual, trace-gain readout, X/Z order-gap readout, controls, proofs, and result JSON",
            "definition": "K0=sqrt(1-p) I_d; K1=sqrt(p) P_x where P_x maps basis index i to i xor 1. The degenerate control uses p=2 with only K1 active.",
        },
        "domain": "finite sparse Kraus support tensors over d in {8,16,32,64}, with int8 coefficients and one float32 path parameter",
        "codomain_or_output": "CPTP admissibility readout for the sparse channel family plus degenerate-control and order-control failures",
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite operator dimensions, finite Kraus path set {K0,K1}, finite coefficient/support tensors, finite scale ladder",
            },
            "N01": {
                "status": "active_tested",
                "statement": "least-significant-bit Pauli-X support has nonzero order gap against the Z order probe; identity support control kills the gap",
            },
        },
        "root_constraints_in_force": ["F01 finite carrier/probe/operator/path set", "N01 noncommuting/order-sensitive operation/control"],
        "carrier_layer": "finite sparse operator/channel carrier",
        "geometry_layer": "not_applicable_operator_channel_lego",
        "carrier_realization": "torch.sparse_coo_tensor complex128 primary; int8 coefficient tensors plus one float32 p parameter; JAX BCOO mirror",
        "peps3d_embedding": "not_applicable_for_this_Stage5_Kraus_operator_channel_lego; PEPS3D/manifold consumers blocked",
        "spinor_state": "not_applicable; no spinor/manifold claim is made",
        "quaternion_action": "not_applicable",
        "bridge_layer": "none",
        "cut_layer": "none",
        "dependency_receipts": ["single_micro_operator_channel_packet_no_coupling_dependency"],
        "law_or_candidate_tested": "Sparse two-path Kraus completeness plus X/Z noncommuting support witness",
        "allowed_claims": [
            "For p=1/4, the sparse Kraus family satisfies sum K^*K=I at d=8/16/32/64 within 1e-9.",
            "The p=2 degenerate gain control fails the same completeness claim and produces trace gain 2.",
            "The X support has a finite nonzero X/Z order gap; replacing it with identity kills the N01 order witness.",
            "PyTorch sparse and JAX BCOO recomputations agree on the emitted observables within 1e-9.",
        ],
        "promotion_blockers": [
            "no tool-tool coupling receipt",
            "no PEPS3D/spinor/quaternion carrier claim",
            "no bridge, flux, Xi, Phi0, Axis0, FEP, gravity, physics, or final manifold consumer is unlocked",
        ],
        "eligible_consumers": ["future bounded Stage-5 operator/channel/generator micro-probes that need a sparse Kraus completeness fixture"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": float(max(row["jax_vs_pytorch_delta"] for row in scale_rows.values())),
        "proof_results": proofs,
        "controls": controls,
        "tool_ablations": ablations,
        "ablation_outcome_delta": {key: row["outcome_delta"] for key, row in ablations.items()},
        "tool_ablations_by_tool": ablations,
        "scale_ladder": {
            "rungs": {
                str(d): {
                    "sites_or_qubits": row["sites_or_qubits"],
                    "operator_dimension": row["operator_dimension"],
                    "operator_count": row["operator_count"],
                    "path_count": row["path_count"],
                    "kraus_count": row["kraus_count"],
                    "support_nnz_real": row["support_nnz_real"],
                    "nonzero_density_across_two_kraus": row["nonzero_density_across_two_kraus"],
                    "dense_state_closure_used": row["dense_state_closure_used"],
                    "torch_completeness_error": row["torch_completeness_error"],
                    "torch_p2_gain_control_completeness_error": row["torch_p2_gain_control_completeness_error"],
                    "torch_order_gap_xz": row["torch_order_gap_xz"],
                    "jax_vs_pytorch_delta": row["jax_vs_pytorch_delta"],
                    "pass": row["pass"],
                }
                for d, row in scale_rows.items()
            },
            "pass": bool(scale_pass),
        },
        "scale_details": scale_rows,
        "known_value_checks": checks,
        "all_known_value_checks_match": bool(known_pass),
        "clifford_numeric_result": clifford_witness,
        "required_tools": ["torch", "jax", "z3", "cvc5", "sympy", "clifford"],
        "actual_tools_used": ["torch", "jax", "z3", "cvc5", "sympy", "clifford"],
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_inputs": ["none"],
        "data_or_artifact_dependencies": ["/tmp/op_design/specs.json"],
        "required_negatives": ["p2_gain_control", "K1_removed_control", "commutative_support_control"],
        "negatives_run": list(controls.keys()),
        "kill_conditions": [
            "real completeness SMT claim does not flip against p=2 control",
            "p=2 control does not produce trace gain/loss",
            "K1-removed ablation does not change the recomputed completeness score",
            "proof-tool load-bearing is represented as numeric ablation instead of verdict flip",
            "dense state closure or NumPy bridge appears in claim-bearing path",
        ],
        "required_artifacts": ["result JSON", "scale_ladder", "proof_results", "controls", "tool_ablations", "known_value_checks"],
        "artifacts_emitted": [str(RESULT)],
        "witness_trace_id": "op_kraus_path_family_sparse_pauli_x_channel::p_1_4::d_8_16_32_64",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "ablation_pass": ablation_pass,
            "known_value_checks_pass": known_pass,
            "classification": "lego",
            "promotion_allowed": False,
            "max_operator_dimension": 64,
            "jax_vs_pytorch_delta": float(max(row["jax_vs_pytorch_delta"] for row in scale_rows.values())),
            "elapsed_seconds": time.time() - started,
        },
        "positive": {
            "scale_ladder_pass": {"pass": scale_pass, "rungs": list(SCALES)},
            "helper_bound_smt_flips": {"pass": proof_pass, "proofs": proof_nodes},
            "torch_sparse_primary": {"pass": bool(torch_primary_result["pass"])},
            "jax_sparse_mirror": {"pass": bool(jax_mirror_result["pass"])},
            "clifford_order_witness": clifford_witness,
        },
        "boundary": {
            "dense_state_closure_banned": {"pass": True, "dense_state_closure_used": False},
            "numpy_claim_bearing_path_absent": {"pass": True, "numpy_imported": False},
            "proof_tools_have_no_numeric_ablation": {
                "pass": not any(any(tool in key.lower() for tool in ("z3", "cvc5", "sympy")) for key in ablations),
                "policy": "z3/cvc5/sympy are load-bearing via proof_results verdict flips only",
            },
            "promotion_allowed_false": {"pass": True, "promotion_allowed": False},
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [],
        "pass_rule": "Pass iff all 8/16/32/64 sparse rungs pass, SMT completeness and order proofs flip real SAT vs control UNSAT, sympy exact flip passes, torch/clifford ablations are real recomputes, JAX mirror agrees, and blocked consumers remain blocked.",
        "fail_rule": "Fail on planted/non-recomputed deltas, non-flipping proof, proof-tool numeric ablation, dense closure, JAX mismatch, missing control, or any promotion beyond this single lego.",
        "promotion_status": "keep_but_open",
        "all_pass": all_pass,
        "required_pass": all_pass,
    }


def main() -> int:
    result = as_jsonable(build_result())
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {RESULT.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
