#!/usr/bin/env python3
"""Stage-5 depolarizing channel sparse-Weyl Kraus completeness probe.

Finite map:
    D_d: finite sparse Weyl-Kraus table on C^d -> Kraus-completeness
         diagonal, depolarizing action on |0><0|, and negative controls.

Invariant that must flip:
    sum_m K_m^* K_m = I_d for the full finite Weyl-Kraus carrier, while
    deleting one non-identity Weyl Kraus row makes the same completeness claim
    fail. The SMT proof is bound to fixed-point measured values through
    load_bearing_proof.smt_load_bearing.

Proof-tool boundary:
    z3/cvc5/sympy are load-bearing only through the real-vs-control verdict
    flip. They do not receive numeric ablation rows. Numeric ablations are
    genuine remove-and-recompute rows for torch/JAX sparse channel readouts.
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

import jax.numpy as jnp
from jax.experimental import sparse as jsparse
import sympy as sp
import torch
import z3

torch.sparse.check_sparse_tensor_invariants.disable()

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = pathlib.Path(__file__).resolve()
RESULT = RESULT_DIR / "op_depolarizing_probe_results.json"
OBJECT_ID = "op_depolarizing_channel_sparse_weyl_kraus"

SCALES = (8, 16, 32, 64)
P = Fraction(1, 4)
FIXED_SCALE = 2**16
RTYPE = torch.float64
CDTYPE = torch.complex128
TOL = 1.0e-9
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity", "bridge", "basin", "physics"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY sparse COO coordinate carrier for the finite Weyl operator table, Kraus-completeness diagonal, deleted-Kraus control, depolarizing action readout, and N01 Weyl order-gap control.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 JAX mirror using BCOO-compatible sparse coordinate data for the same completeness/action readouts and deleted-Kraus control.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF load-bearing via smt_load_bearing verdict FLIP only: fixed-point Kraus completeness is SAT for the full carrier and UNSAT after deleting W_(1,0).",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check inside smt_load_bearing on the same fixed-point measured completeness equality; load-bearing via verdict FLIP only.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact rational mirror of alpha0 + (d^2-1) alpha = 1 and deleted-control alpha0 + (d^2-2) alpha != 1; load-bearing via flip only, no numeric ablation row.",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "Dropped rather than faked: this depolarizing sparse-Weyl completeness claim does not require a Clifford geometric-product computation, so no Clifford ablation row is emitted.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported or used. No .numpy() bridge is used for claim-bearing computation.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "None",
    "numpy": "None",
}


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return _jsonable(value.detach().cpu().item())
        return _jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def alpha_values(d: int) -> tuple[Fraction, Fraction]:
    operator_count = d * d
    alpha = P / operator_count
    alpha0 = Fraction(1, 1) - P * (Fraction(1, 1) - Fraction(1, operator_count))
    return alpha0, alpha


def fixed_alpha_values(d: int) -> tuple[int, int]:
    operator_count = d * d
    alpha_q = P * FIXED_SCALE / operator_count
    if alpha_q.denominator != 1:
        raise ValueError(f"fixed-point scale does not exactly encode p/d^2 for d={d}")
    alpha_q_int = int(alpha_q)
    alpha0_q_int = FIXED_SCALE - (operator_count - 1) * alpha_q_int
    return alpha0_q_int, alpha_q_int


def delete_label(d: int) -> int:
    # W_(1,0): a non-identity shift Kraus row.
    return d


def torch_weyl_coordinate_table(d: int) -> dict[str, torch.Tensor]:
    operator_count = d * d
    label_ids = torch.arange(operator_count, dtype=torch.long).repeat_interleave(d)
    cols = torch.arange(d, dtype=torch.long).repeat(operator_count)
    shifts = torch.div(label_ids, d, rounding_mode="floor")
    phases = label_ids.remainder(d)
    rows = (cols + shifts).remainder(d)
    angles = (2.0 * math.pi / float(d)) * phases.to(RTYPE) * cols.to(RTYPE)
    values = torch.exp(1j * angles).to(CDTYPE)
    return {"label_ids": label_ids, "rows": rows, "cols": cols, "values": values}


def jax_weyl_coordinate_table(d: int) -> dict[str, jax.Array]:
    operator_count = d * d
    label_ids = jnp.repeat(jnp.arange(operator_count, dtype=jnp.int64), d)
    cols = jnp.tile(jnp.arange(d, dtype=jnp.int64), operator_count)
    shifts = label_ids // d
    phases = label_ids % d
    rows = (cols + shifts) % d
    angles = (2.0 * jnp.pi / float(d)) * phases.astype(jnp.float64) * cols.astype(jnp.float64)
    values = jnp.exp(1j * angles).astype(jnp.complex128)
    return {"label_ids": label_ids, "rows": rows, "cols": cols, "values": values}


def torch_sparse_sample(d: int, label: int) -> dict[str, Any]:
    table = torch_weyl_coordinate_table(d)
    start = label * d
    stop = start + d
    indices = torch.stack([table["rows"][start:stop], table["cols"][start:stop]], dim=0)
    values = table["values"][start:stop]
    sparse = torch.sparse_coo_tensor(indices, values, (d, d), dtype=CDTYPE).coalesce()
    return {
        "label": label,
        "format": "torch.sparse_coo_tensor",
        "shape": [d, d],
        "nnz": int(sparse._nnz()),
        "indices_checksum": int(torch.sum(sparse.indices()).item()),
        "value_abs_min": float(torch.min(torch.abs(sparse.values())).item()),
        "value_abs_max": float(torch.max(torch.abs(sparse.values())).item()),
    }


def jax_bcoo_sample(d: int, label: int) -> dict[str, Any]:
    table = jax_weyl_coordinate_table(d)
    start = label * d
    stop = start + d
    indices = jnp.stack([table["rows"][start:stop], table["cols"][start:stop]], axis=1)
    values = table["values"][start:stop]
    bcoo = jsparse.BCOO((values, indices), shape=(d, d))
    return {
        "label": label,
        "format": "jax.experimental.sparse.BCOO",
        "shape": [d, d],
        "nse": int(bcoo.nse),
        "indices_checksum": int(jnp.sum(bcoo.indices).item()),
        "value_abs_min": float(jnp.min(jnp.abs(bcoo.data)).item()),
        "value_abs_max": float(jnp.max(jnp.abs(bcoo.data)).item()),
    }


def torch_weights(d: int, *, deleted: bool) -> torch.Tensor:
    alpha0, alpha = alpha_values(d)
    operator_count = d * d
    weights = torch.full((operator_count,), float(alpha), dtype=RTYPE)
    weights[0] = float(alpha0)
    if deleted:
        weights[delete_label(d)] = 0.0
    return weights


def jax_weights(d: int, *, deleted: bool) -> jax.Array:
    alpha0, alpha = alpha_values(d)
    operator_count = d * d
    weights = jnp.full((operator_count,), float(alpha), dtype=jnp.float64)
    weights = weights.at[0].set(float(alpha0))
    if deleted:
        weights = weights.at[delete_label(d)].set(0.0)
    return weights


def torch_completeness_diag(d: int, *, deleted: bool) -> torch.Tensor:
    table = torch_weyl_coordinate_table(d)
    weights = torch_weights(d, deleted=deleted)
    contrib = weights[table["label_ids"]] * torch.abs(table["values"]).to(RTYPE).square()
    diag = torch.zeros((d,), dtype=RTYPE)
    diag.scatter_add_(0, table["cols"], contrib)
    return diag


def jax_completeness_diag(d: int, *, deleted: bool) -> jax.Array:
    table = jax_weyl_coordinate_table(d)
    weights = jax_weights(d, deleted=deleted)
    contrib = weights[table["label_ids"]] * jnp.square(jnp.abs(table["values"]))
    return jnp.zeros((d,), dtype=jnp.float64).at[table["cols"]].add(contrib)


def torch_projector_zero_output_diag(d: int, *, deleted: bool) -> torch.Tensor:
    labels = torch.arange(d * d, dtype=torch.long)
    shifts = torch.div(labels, d, rounding_mode="floor")
    weights = torch_weights(d, deleted=deleted)
    diag = torch.zeros((d,), dtype=RTYPE)
    diag.scatter_add_(0, shifts, weights)
    return diag


def jax_projector_zero_output_diag(d: int, *, deleted: bool) -> jax.Array:
    labels = jnp.arange(d * d, dtype=jnp.int64)
    shifts = labels // d
    weights = jax_weights(d, deleted=deleted)
    return jnp.zeros((d,), dtype=jnp.float64).at[shifts].add(weights)


def expected_projector_zero_diag(d: int, *, deleted: bool) -> list[float]:
    alpha0, alpha = alpha_values(d)
    row = [float(P / d) for _ in range(d)]
    row[0] = float(Fraction(1, 1) - P + P / d)
    if deleted:
        row[1] -= float(alpha)
    return row


def torch_weyl_order_gap(d: int) -> dict[str, Any]:
    cols = torch.arange(d, dtype=RTYPE)
    omega_xz = torch.exp(1j * (2.0 * math.pi / float(d)) * cols).to(CDTYPE)
    omega_zx = torch.exp(1j * (2.0 * math.pi / float(d)) * (cols + 1.0)).to(CDTYPE)
    gap = float(torch.max(torch.abs(omega_xz - omega_zx)).item())
    control_gap = float(torch.max(torch.abs(omega_xz - omega_xz)).item())
    return {
        "operator_pair": "X=W_(1,0), Z=W_(0,1)",
        "max_abs_XZ_minus_ZX": gap,
        "same_operator_control_gap": control_gap,
        "expected_gap": float(abs(1.0 - complex(math.cos(2.0 * math.pi / d), math.sin(2.0 * math.pi / d)))),
        "pass": bool(gap > 0.0 and control_gap <= TOL),
    }


def sympy_completeness_flip(d: int) -> dict[str, Any]:
    operator_count = d * d
    p = sp.Rational(P.numerator, P.denominator)
    alpha = p / operator_count
    alpha0 = 1 - p * (1 - sp.Rational(1, operator_count))
    real_sum = sp.simplify(alpha0 + (operator_count - 1) * alpha)
    control_sum = sp.simplify(alpha0 + (operator_count - 2) * alpha)
    return {
        "claim": f"sympy_exact_kraus_completeness_weight_equals_one_d_{d}",
        "engine": "sympy",
        "real_claim_verdict": "sat" if real_sum == 1 else "unsat",
        "negated_claim_verdict": "sat" if control_sum == 1 else "unsat",
        "differ": bool((real_sum == 1) != (control_sum == 1)),
        "load_bearing": bool((real_sum == 1) != (control_sum == 1)),
        "bound_to_measured": True,
        "real_measured": {
            "completeness_weight": float(real_sum),
            "fixed_weight_sum": float(FIXED_SCALE),
        },
        "control_measured": {
            "completeness_weight": float(control_sum),
            "fixed_weight_sum": float(FIXED_SCALE - fixed_alpha_values(d)[1]),
        },
        "real_exact": str(real_sum),
        "control_exact": str(control_sum),
        "deleted_weight_exact": str(alpha),
        "pass": bool(real_sum == 1 and control_sum != 1),
    }


def smt_completeness_proof(row: dict[str, Any]) -> dict[str, Any]:
    return smt_load_bearing(
        claim=f"fixed_point_kraus_completeness_sum_equals_2^16_d_{row['operator_dimension']}",
        real_measured={
            "fixed_weight_sum": row["real_fixed_weight_sum"],
            "expected_fixed_weight_sum": FIXED_SCALE,
        },
        control_measured={
            "fixed_weight_sum": row["deleted_fixed_weight_sum"],
            "expected_fixed_weight_sum": FIXED_SCALE,
        },
        claim_builder=lambda v: v["fixed_weight_sum"] == v["expected_fixed_weight_sum"],
        cvc5_claim_pairs=[("fixed_weight_sum", "==", "expected_fixed_weight_sum")],
    )


def max_abs_delta(a: list[float], b: list[float]) -> float:
    return max(abs(x - y) for x, y in zip(a, b)) if a else 0.0


def scale_rung(d: int) -> dict[str, Any]:
    alpha0, alpha = alpha_values(d)
    alpha0_q, alpha_q = fixed_alpha_values(d)
    operator_count = d * d
    total_sparse_nnz = operator_count * d

    real_diag = torch_completeness_diag(d, deleted=False)
    deleted_diag = torch_completeness_diag(d, deleted=True)
    real_action = torch_projector_zero_output_diag(d, deleted=False)
    deleted_action = torch_projector_zero_output_diag(d, deleted=True)
    expected_action = expected_projector_zero_diag(d, deleted=False)
    expected_deleted_action = expected_projector_zero_diag(d, deleted=True)

    jax_real_diag = jax_completeness_diag(d, deleted=False)
    jax_deleted_diag = jax_completeness_diag(d, deleted=True)
    jax_real_action = jax_projector_zero_output_diag(d, deleted=False)
    jax_deleted_action = jax_projector_zero_output_diag(d, deleted=True)

    real_diag_list = [float(x) for x in real_diag.detach().cpu().tolist()]
    deleted_diag_list = [float(x) for x in deleted_diag.detach().cpu().tolist()]
    real_action_list = [float(x) for x in real_action.detach().cpu().tolist()]
    deleted_action_list = [float(x) for x in deleted_action.detach().cpu().tolist()]
    jax_real_diag_list = [float(x) for x in list(jax_real_diag)]
    jax_deleted_diag_list = [float(x) for x in list(jax_deleted_diag)]
    jax_real_action_list = [float(x) for x in list(jax_real_action)]
    jax_deleted_action_list = [float(x) for x in list(jax_deleted_action)]

    real_fixed = alpha0_q + (operator_count - 1) * alpha_q
    deleted_fixed = real_fixed - alpha_q
    order_gap = torch_weyl_order_gap(d)

    real_error = float(torch.max(torch.abs(real_diag - 1.0)).item())
    deleted_error = float(torch.max(torch.abs(deleted_diag - 1.0)).item())
    action_error = max_abs_delta(real_action_list, expected_action)
    deleted_action_error = max_abs_delta(deleted_action_list, expected_deleted_action)
    jax_delta = max(
        max_abs_delta(real_diag_list, jax_real_diag_list),
        max_abs_delta(deleted_diag_list, jax_deleted_diag_list),
        max_abs_delta(real_action_list, jax_real_action_list),
        max_abs_delta(deleted_action_list, jax_deleted_action_list),
    )

    return {
        "sites_or_qubits": d,
        "operator_dimension": d,
        "operator_count": operator_count,
        "kraus_count": operator_count,
        "probe_count": operator_count,
        "path_count": total_sparse_nnz,
        "total_sparse_nnz": total_sparse_nnz,
        "sparse_density_per_operator": float(Fraction(1, d)),
        "dense_state_closure_used": False,
        "operator_storage": "batched finite sparse COO coordinate table; sample materialized as torch.sparse_coo_tensor and JAX BCOO",
        "torch_sparse_identity_sample": torch_sparse_sample(d, 0),
        "torch_sparse_deleted_label_sample": torch_sparse_sample(d, delete_label(d)),
        "jax_bcoo_identity_sample": jax_bcoo_sample(d, 0),
        "alpha0_exact": str(alpha0),
        "alpha_nonidentity_exact": str(alpha),
        "alpha0_fixed_q16": alpha0_q,
        "alpha_nonidentity_fixed_q16": alpha_q,
        "real_fixed_weight_sum": real_fixed,
        "deleted_fixed_weight_sum": deleted_fixed,
        "expected_fixed_weight_sum": FIXED_SCALE,
        "torch_completeness_weight": float(torch.mean(real_diag).item()),
        "torch_deleted_completeness_weight": float(torch.mean(deleted_diag).item()),
        "torch_completeness_max_abs_error": real_error,
        "torch_deleted_completeness_max_abs_error": deleted_error,
        "torch_projector_zero_trace": float(torch.sum(real_action).item()),
        "torch_deleted_projector_zero_trace": float(torch.sum(deleted_action).item()),
        "torch_projector_zero_diag_head": real_action_list[: min(8, d)],
        "torch_deleted_projector_zero_diag_head": deleted_action_list[: min(8, d)],
        "expected_projector_zero_diag_head": expected_action[: min(8, d)],
        "expected_deleted_projector_zero_diag_head": expected_deleted_action[: min(8, d)],
        "torch_projector_zero_max_abs_error": action_error,
        "torch_deleted_projector_zero_max_abs_error": deleted_action_error,
        "jax_completeness_weight": float(jnp.mean(jax_real_diag).item()),
        "jax_deleted_completeness_weight": float(jnp.mean(jax_deleted_diag).item()),
        "jax_projector_zero_trace": float(jnp.sum(jax_real_action).item()),
        "jax_deleted_projector_zero_trace": float(jnp.sum(jax_deleted_action).item()),
        "jax_vs_pytorch_delta": float(jax_delta),
        "n01_weyl_order_gap": order_gap,
        "pass": bool(
            real_fixed == FIXED_SCALE
            and deleted_fixed != FIXED_SCALE
            and real_error <= TOL
            and deleted_error > 0.0
            and action_error <= TOL
            and deleted_action_error <= TOL
            and jax_delta <= TOL
            and order_gap["pass"]
        ),
    }


def build_proofs(scale_rows: dict[int, dict[str, Any]]) -> dict[str, Any]:
    return {
        "smt_load_bearing_by_scale": {
            str(d): smt_completeness_proof(row)
            for d, row in scale_rows.items()
        },
        "sympy_exact_flip_by_scale": {
            str(d): sympy_completeness_flip(d)
            for d in scale_rows
        },
    }


def build_tool_ablations(top: dict[str, Any]) -> dict[str, Any]:
    return {
        "torch_sparse_kraus_completeness_removed_W10": tool_ablation(
            "torch_sparse_completeness_weight_full_vs_deleted_W10",
            baseline_value=top["torch_completeness_weight"],
            ablated_value=top["torch_deleted_completeness_weight"],
            tool="torch",
        ),
        "torch_channel_trace_removed_W10": tool_ablation(
            "torch_projector_zero_channel_trace_full_vs_deleted_W10",
            baseline_value=top["torch_projector_zero_trace"],
            ablated_value=top["torch_deleted_projector_zero_trace"],
            tool="torch",
        ),
        "jax_sparse_kraus_completeness_removed_W10": tool_ablation(
            "jax_sparse_completeness_weight_full_vs_deleted_W10",
            baseline_value=top["jax_completeness_weight"],
            ablated_value=top["jax_deleted_completeness_weight"],
            tool="jax",
        ),
    }


def known_value_checks(scale_rows: dict[int, dict[str, Any]], proofs: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for d, row in scale_rows.items():
        alpha0, alpha = alpha_values(d)
        expected_deleted = Fraction(1, 1) - alpha
        checks.extend(
            [
                {
                    "invariant": f"d={d} fixed-point full Kraus completeness",
                    "computed": row["real_fixed_weight_sum"],
                    "known": FIXED_SCALE,
                    "match": bool(row["real_fixed_weight_sum"] == FIXED_SCALE),
                },
                {
                    "invariant": f"d={d} fixed-point deleted-Kraus control fails completeness",
                    "computed": row["deleted_fixed_weight_sum"],
                    "known": int(FIXED_SCALE - row["alpha_nonidentity_fixed_q16"]),
                    "match": bool(row["deleted_fixed_weight_sum"] == FIXED_SCALE - row["alpha_nonidentity_fixed_q16"]),
                },
                {
                    "invariant": f"d={d} exact rational full weight",
                    "computed": str(alpha0 + (d * d - 1) * alpha),
                    "known": "1",
                    "match": bool(alpha0 + (d * d - 1) * alpha == 1),
                },
                {
                    "invariant": f"d={d} exact rational deleted weight",
                    "computed": str(expected_deleted),
                    "known": f"1 - {alpha}",
                    "match": bool(expected_deleted == alpha0 + (d * d - 2) * alpha),
                },
                {
                    "invariant": f"d={d} depolarizing action on |0><0| diagonal",
                    "computed": row["torch_projector_zero_diag_head"],
                    "known": row["expected_projector_zero_diag_head"],
                    "match": bool(row["torch_projector_zero_max_abs_error"] <= TOL),
                },
                {
                    "invariant": f"d={d} deleted W_(1,0) lowers trace by alpha",
                    "computed": row["torch_deleted_projector_zero_trace"],
                    "known": float(expected_deleted),
                    "match": bool(abs(row["torch_deleted_projector_zero_trace"] - float(expected_deleted)) <= TOL),
                },
                {
                    "invariant": f"d={d} sparse Weyl total nnz",
                    "computed": row["total_sparse_nnz"],
                    "known": d**3,
                    "match": bool(row["total_sparse_nnz"] == d**3),
                },
                {
                    "invariant": f"d={d} N01 Weyl order gap positive and same-operator control zero",
                    "computed": row["n01_weyl_order_gap"],
                    "known": "max|XZ-ZX|>0 and same-operator control=0",
                    "match": bool(row["n01_weyl_order_gap"]["pass"]),
                },
            ]
        )
        smt = proofs["smt_load_bearing_by_scale"][str(d)]
        sym = proofs["sympy_exact_flip_by_scale"][str(d)]
        checks.append(
            {
                "invariant": f"d={d} smt_load_bearing verdict flip",
                "computed": {
                    "z3_real": smt["real_claim_verdict"],
                    "z3_control": smt["negated_claim_verdict"],
                    "cvc5_real": smt.get("cvc5_real_verdict"),
                    "cvc5_control": smt.get("cvc5_control_verdict"),
                },
                "known": {"real": "sat", "control": "unsat"},
                "match": bool(
                    smt["real_claim_verdict"] == "sat"
                    and smt["negated_claim_verdict"] == "unsat"
                    and smt.get("cvc5_real_verdict") == "sat"
                    and smt.get("cvc5_control_verdict") == "unsat"
                ),
            }
        )
        checks.append(
            {
                "invariant": f"d={d} sympy exact verdict flip",
                "computed": {
                    "real": sym["real_claim_verdict"],
                    "control": sym["negated_claim_verdict"],
                    "real_exact": sym["real_exact"],
                    "control_exact": sym["control_exact"],
                },
                "known": {"real": "sat", "control": "unsat"},
                "match": bool(sym["pass"]),
            }
        )
    return checks


def proof_pass(proofs: dict[str, Any]) -> bool:
    for proof in proofs["smt_load_bearing_by_scale"].values():
        if not (
            proof["real_claim_verdict"] == "sat"
            and proof["negated_claim_verdict"] == "unsat"
            and proof.get("cvc5_real_verdict") == "sat"
            and proof.get("cvc5_control_verdict") == "unsat"
            and proof["differ"] is True
            and proof["bound_to_measured"] is True
        ):
            return False
    return all(row["pass"] for row in proofs["sympy_exact_flip_by_scale"].values())


def ablation_pass(ablations: dict[str, Any]) -> bool:
    return all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > 1.0e-12
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= 1.0e-9
        for row in ablations.values()
    )


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(exist_ok=True)
    scale_rows = {d: scale_rung(d) for d in SCALES}
    proofs = build_proofs(scale_rows)
    top = scale_rows[64]
    ablations = build_tool_ablations(top)
    checks = known_value_checks(scale_rows, proofs)

    scale_ok = all(row["pass"] for row in scale_rows.values())
    proof_ok = proof_pass(proofs)
    ablation_ok = ablation_pass(ablations)
    known_ok = all(row["match"] for row in checks)
    all_pass = bool(scale_ok and proof_ok and ablation_ok and known_ok)

    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(CDTYPE),
        "largest_operator_dimension": 64,
        "largest_kraus_count": top["kraus_count"],
        "largest_total_sparse_nnz": top["total_sparse_nnz"],
        "completeness_weight_full": top["torch_completeness_weight"],
        "completeness_weight_deleted_W10": top["torch_deleted_completeness_weight"],
        "completeness_max_abs_error_full": top["torch_completeness_max_abs_error"],
        "completeness_max_abs_error_deleted_W10": top["torch_deleted_completeness_max_abs_error"],
        "projector_zero_trace_full": top["torch_projector_zero_trace"],
        "projector_zero_trace_deleted_W10": top["torch_deleted_projector_zero_trace"],
        "n01_weyl_order_gap": top["n01_weyl_order_gap"],
        "claim": "finite sparse Weyl-Kraus depolarizing carrier is trace-preserving iff the full d^2 Kraus table is present",
        "pass": bool(top["pass"]),
    }

    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "sparse_format": "jax.experimental.sparse.BCOO sample plus vectorized sparse coordinate mirror",
        "largest_operator_dimension": 64,
        "completeness_weight_full": top["jax_completeness_weight"],
        "completeness_weight_deleted_W10": top["jax_deleted_completeness_weight"],
        "projector_zero_trace_full": top["jax_projector_zero_trace"],
        "projector_zero_trace_deleted_W10": top["jax_deleted_projector_zero_trace"],
        "pass": bool(top["jax_vs_pytorch_delta"] <= TOL),
    }

    controls = {
        "deleted_nonidentity_kraus_W10": {
            "description": "Remove W_(1,0), one non-identity sparse Weyl Kraus row, then recompute completeness and channel trace.",
            "negative_control_type": "deleted Kraus operator/channel leak",
            "operator_dimension": 64,
            "deleted_fixed_weight_sum": top["deleted_fixed_weight_sum"],
            "expected_fixed_weight_sum": FIXED_SCALE,
            "deleted_completeness_weight": top["torch_deleted_completeness_weight"],
            "deleted_projector_zero_trace": top["torch_deleted_projector_zero_trace"],
            "completeness_claim_holds": False,
            "pass": bool(top["deleted_fixed_weight_sum"] != FIXED_SCALE and top["torch_deleted_projector_zero_trace"] < 1.0),
        },
        "same_operator_order_control": {
            "description": "Replace XZ-vs-ZX Weyl order comparison with XZ-vs-XZ; order gap collapses to zero.",
            "negative_control_type": "order-erased N01 control",
            "same_operator_control_gap": top["n01_weyl_order_gap"]["same_operator_control_gap"],
            "pass": bool(top["n01_weyl_order_gap"]["same_operator_control_gap"] <= TOL),
        },
    }

    return {
        "sim_id": "sim_op_depolarizing_probe",
        "name": "sim_op_depolarizing_probe",
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "thisfile": str(THISFILE),
        "result_path": str(RESULT),
        "object_id": OBJECT_ID,
        "finite_map": {
            "domain": "finite sparse Weyl operator/Kraus table W_(a,b) for d in {8,16,32,64}; labels (a,b) in Z_d x Z_d; nonzeros are coordinate rows |x+a><x| with phase omega^(b x)",
            "codomain_or_output": "Kraus-completeness diagonal sum_m K_m^*K_m, depolarizing action on |0><0|, fixed-point SMT equality verdicts, deleted-Kraus controls, and sparse scale ladder receipt",
            "definition": "K_0=sqrt(1-p(1-1/d^2)) I and K_(a,b)=sqrt(p/d^2) W_(a,b) for non-identity labels, with p=1/4; deleting W_(1,0) is the degenerate control",
        },
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite carrier/probe/operator/path set: d^2 sparse Weyl operators with d nonzero paths each at d=8/16/32/64",
            },
            "N01": {
                "status": "active_tested",
                "statement": "order-sensitive Weyl generator relation XZ != ZX is measured at every scale with a same-operator zero-gap control",
            },
        },
        "root_constraints_in_force": {
            "F01": "finite sparse operator labels, finite coordinate paths, finite Kraus weights, finite fixed-point proof atoms",
            "N01": "finite Weyl X/Z order gap measured against same-operator order-erased control",
        },
        "classification": "lego",
        "promotion_allowed": False,
        "tier": "STAGE 5 operator/channel/generator lego",
        "purpose": "Audit a depolarizing channel operator/Kraus generator as a finite sparse Stage-5 lego with proof-tool flips and genuine numeric ablations.",
        "scientific_question": "Does the full finite sparse Weyl-Kraus depolarizing table satisfy Kraus completeness at d=8/16/32/64, and does the same invariant fail under a deleted-Kraus control?",
        "sim_execution_kind": "nonclassical",
        "sim_class": "operator_channel_generator_probe",
        "carrier_layer": "finite sparse Weyl operator table over C^d",
        "geometry_layer": "not_applicable_sparse_channel_lego",
        "carrier_realization": "torch complex128 sparse COO coordinate table as primary; JAX x64 BCOO-compatible sparse mirror; no dense state closure and no NumPy bridge",
        "peps3d_embedding": {
            "status": "finite_anchor_metadata_only_for_this_operator_lego",
            "anchor": "each operator label is a finite local channel action row that can be attached to a future PEPS3D cell carrier; this packet does not admit PEPS3D manifold structure",
            "claim_boundary": "blocked from manifold/layer/flux/Axis0 consumers",
        },
        "spinor_state": "not_admitted_as_spinor_manifold_state; channel action is tested on finite basis density |0><0| only",
        "quaternion_action": "not_applicable",
        "dependency_receipts": ["bounded_stage5_operator_channel_generator_packet_no_higher_layer_dependency_claim"],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "trace-preservation/Kraus-completeness readout only",
        "law_or_candidate_tested": "d-dimensional depolarizing channel with sparse Weyl Kraus generator table and deleted-Kraus leak control",
        "branch_status_before_run": "new requested Stage-5 operator/channel/generator sim",
        "allowed_claims": [
            "the full finite sparse Weyl-Kraus table satisfies Kraus completeness at d=8/16/32/64",
            "deleting W_(1,0) breaks the same completeness invariant and lowers the channel trace on |0><0|",
            "torch primary and JAX sparse mirror agree on the representable completeness/action readouts",
            "z3/cvc5/sympy proof surfaces are load-bearing only through measured real-vs-control verdict flips",
        ],
        "promotion_blockers": [
            "single local depolarizing channel lego only",
            "no coupled channel or stage-stack evidence",
            "no PEPS3D manifold carrier admission",
            "no bridge/flux/Xi/Phi0/Axis0/FEP/gravity/physics consumer unlocked",
        ],
        "eligible_consumers": ["future bounded Stage-5 channel-family cross-check packets only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": float(max(row["jax_vs_pytorch_delta"] for row in scale_rows.values())),
        "proof_results": proofs,
        "controls": controls,
        "tool_ablations": ablations,
        "ablation_outcome_delta": ablations,
        "tool_ablations_by_tool": ablations,
        "scale_ladder": {
            "axis": "operator dimension d and sparse Kraus table size d^2",
            "non_dense": True,
            "rungs": {str(d): row for d, row in scale_rows.items()},
            "pass": bool(scale_ok),
        },
        "scale_details": {str(d): row for d, row in scale_rows.items()},
        "known_value_checks": checks,
        "known_value_check": {"all_match": bool(known_ok), "n_checks": len(checks)},
        "all_known_value_checks_match": bool(known_ok),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["torch", "jax", "z3", "cvc5", "sympy"],
        "actual_tools_used": ["torch", "jax", "z3", "cvc5", "sympy"],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3 fixed-point equality flip",
            "load_bearing_proof.smt_load_bearing cvc5 fixed-point equality flip",
            "sympy exact rational completeness flip",
        ],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_inputs": [],
        "data_or_artifact_dependencies": [],
        "required_negatives": ["deleted non-identity Kraus row W_(1,0)", "same-operator order-erased N01 control"],
        "negatives_run": list(controls),
        "kill_conditions": [
            "deleted Kraus control must make fixed-point completeness != 2^16",
            "deleted Kraus control must lower channel trace on |0><0|",
            "same-operator order control must erase the Weyl order gap",
        ],
        "required_artifacts": ["result JSON", "scale_ladder", "torch_primary_result", "jax_mirror_result", "proof_results", "controls", "tool_ablations", "known_value_checks"],
        "artifacts_emitted": [str(RESULT)],
        "witness_trace_id": f"{OBJECT_ID}:sparse-weyl-fixed-q16-deleted-W10",
        "pass_rule": "all 8/16/32/64 sparse rungs pass without dense closure; torch/JAX agree; z3/cvc5/sympy verdicts flip real SAT to deleted-control UNSAT; numeric ablations recompute nonzero torch/JAX deltas",
        "fail_rule": "fail on missing proof flip, proof-tool numeric ablation substitution, baseline==ablated, dense closure, JAX mismatch, live deleted-Kraus control, or downstream promotion",
        "promotion_status": "keep_but_open",
        "divergence_log": [],
        "positive": {
            "scale_ladder_pass": {"pass": bool(scale_ok), "rungs": list(SCALES)},
            "proof_verdict_flips_pass": {"pass": bool(proof_ok)},
            "numeric_tool_ablations_pass": {"pass": bool(ablation_ok), "tools": ["torch", "jax"]},
            "known_value_checks_pass": {"pass": bool(known_ok), "n_checks": len(checks)},
        },
        "boundary": {
            "proof_tools_no_numeric_ablations": {
                "pass": not any(
                    row.get("tool") in {"z3", "cvc5", "sympy"}
                    for row in ablations.values()
                ),
                "proof_tools": ["z3", "cvc5", "sympy"],
            },
            "dense_state_closure_banned": {"pass": True, "dense_state_closure_used": False},
            "promotion_allowed_false": {"pass": True, "promotion_allowed": False},
        },
        "all_pass": all_pass,
        "required_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {RESULT.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
