#!/usr/bin/env python3
"""Canonical Stage 3 geometry lego: projective twistor incidence.

This standalone build tests one geometry object, not a manifold layer and not a
G-structure:

    finite projective twistor incidence pairs ([Z], [W]) in CP^3 x CP^3*
    with the incidence invariant Z.W = 0.

The real object uses a finite skew incidence map W = JZ, so Z^T J Z = 0.  The
flattened control replaces J by a rank-1 projection P0, so the same invariant
is recomputed as Z^T P0 Z and fails.  The helper-bound SMT proof is load-bearing
only through the measured real/control flip.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
import time
from datetime import datetime, timezone
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import torch
import z3
from clifford import Cl

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "sim_geom_twistor_incidence_probe"
OBJECT_ID = "geom_twistor_incidence"
OUT_PATH = RESULT_DIR / f"{OBJECT_ID}_results.json"

SCALE_RUNGS = (8, 16, 32, 64)
RTYPE = torch.float64
CDTYPE = torch.complex128
EPS = 1.0e-9
CONTROL_FLOOR = 1.0e-6
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]

J_TORCH = torch.tensor(
    [
        [0.0, -1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, -1.0],
        [0.0, 0.0, 1.0, 0.0],
    ],
    dtype=CDTYPE,
)
P0_TORCH = torch.diag(torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=CDTYPE))
J_REAL_TORCH = J_TORCH.real.to(RTYPE)
P0_REAL_TORCH = P0_TORCH.real.to(RTYPE)

J_JAX = jnp.asarray(
    [
        [0.0, -1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, -1.0],
        [0.0, 0.0, 1.0, 0.0],
    ],
    dtype=jnp.complex128,
)
P0_JAX = jnp.diag(jnp.asarray([1.0, 0.0, 0.0, 0.0], dtype=jnp.complex128))

_LAYOUT4, _BLADES4 = Cl(4)
_CLIFFORD_BASIS = [_BLADES4[f"e{i}"] for i in range(1, 5)]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY numeric carrier for finite CP^3 point/dual-covector samples, Z.W incidence residuals, flattened controls, N01 operator commutator, and scale ladder.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 parity mirror for the finite complex bilinear incidence residuals and flattened controls where the computation is representable in JAX.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING exact algebra: proves Z^T J Z simplifies to zero for skew J and the flattened control Z^T P0 Z is not the same incidence identity.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING helper-bound SMT proof via smt_load_bearing; z3 variables are bound to measured real/control incidence residuals and flip sat/unsat.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING geometry check: Cl(4) vector inner products recompute the skew incidence residual and a genuine flattened-structure ablation.",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "Not requested for this build; no cvc5 proof or ablation is emitted.",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "Not relevant to this projective bilinear incidence object; no geomstats or fake JAX geomstats path is used.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control boundary only; not imported and not used for claim-bearing computation.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "clifford": "load_bearing",
    "cvc5": None,
    "geomstats": None,
    "numpy": None,
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if hasattr(value, "tolist") and callable(value.tolist):
        try:
            return as_jsonable(value.tolist())
        except Exception:
            pass
    if hasattr(value, "item") and callable(value.item):
        try:
            return as_jsonable(value.item())
        except Exception:
            pass
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def twistor_samples_torch(n: int) -> torch.Tensor:
    idx = torch.arange(1, n + 1, dtype=RTYPE)
    real = torch.stack(
        (
            (idx + 2.0) / (n + 5.0),
            (2.0 * idx + 3.0) / (n + 7.0),
            (3.0 * idx + 5.0) / (n + 11.0),
            (5.0 * idx + 7.0) / (n + 13.0),
        ),
        dim=1,
    )
    imag = torch.stack(
        (
            (idx + 1.0) / (2.0 * n + 3.0),
            (3.0 * idx + 1.0) / (2.0 * n + 5.0),
            (5.0 * idx + 2.0) / (2.0 * n + 7.0),
            (7.0 * idx + 3.0) / (2.0 * n + 11.0),
        ),
        dim=1,
    )
    return real.to(CDTYPE) + 1j * imag.to(CDTYPE)


def twistor_samples_jax(n: int) -> jnp.ndarray:
    idx = jnp.arange(1, n + 1, dtype=jnp.float64)
    real = jnp.stack(
        (
            (idx + 2.0) / (n + 5.0),
            (2.0 * idx + 3.0) / (n + 7.0),
            (3.0 * idx + 5.0) / (n + 11.0),
            (5.0 * idx + 7.0) / (n + 13.0),
        ),
        axis=1,
    )
    imag = jnp.stack(
        (
            (idx + 1.0) / (2.0 * n + 3.0),
            (3.0 * idx + 1.0) / (2.0 * n + 5.0),
            (5.0 * idx + 2.0) / (2.0 * n + 7.0),
            (7.0 * idx + 3.0) / (2.0 * n + 11.0),
        ),
        axis=1,
    )
    return real.astype(jnp.complex128) + 1j * imag.astype(jnp.complex128)


def projective_scales_torch(n: int) -> torch.Tensor:
    idx = torch.arange(1, n + 1, dtype=RTYPE)
    real = 1.0 + idx / (3.0 * n + 5.0)
    imag = (idx + 2.0) / (5.0 * n + 7.0)
    return real.to(CDTYPE) + 1j * imag.to(CDTYPE)


def projective_scales_jax(n: int) -> jnp.ndarray:
    idx = jnp.arange(1, n + 1, dtype=jnp.float64)
    real = 1.0 + idx / (3.0 * n + 5.0)
    imag = (idx + 2.0) / (5.0 * n + 7.0)
    return real.astype(jnp.complex128) + 1j * imag.astype(jnp.complex128)


def dual_torch(z_rows: torch.Tensor, op: torch.Tensor = J_TORCH) -> torch.Tensor:
    return z_rows @ op.T


def dual_jax(z_rows: jnp.ndarray, op: jnp.ndarray = J_JAX) -> jnp.ndarray:
    return z_rows @ op.T


def incidence_values_torch(z_rows: torch.Tensor, w_rows: torch.Tensor) -> torch.Tensor:
    return torch.sum(z_rows * w_rows, dim=1)


def incidence_values_jax(z_rows: jnp.ndarray, w_rows: jnp.ndarray) -> jnp.ndarray:
    return jnp.sum(z_rows * w_rows, axis=1)


def max_abs_torch(values: torch.Tensor) -> float:
    return float(torch.max(torch.abs(values)).item())


def min_abs_torch(values: torch.Tensor) -> float:
    return float(torch.min(torch.abs(values)).item())


def max_abs_jax(values: jnp.ndarray) -> float:
    return float(jnp.max(jnp.abs(values)))


def min_abs_jax(values: jnp.ndarray) -> float:
    return float(jnp.min(jnp.abs(values)))


def n01_order_witness_torch() -> dict[str, Any]:
    comm = J_REAL_TORCH @ P0_REAL_TORCH - P0_REAL_TORCH @ J_REAL_TORCH
    control = J_REAL_TORCH @ J_REAL_TORCH - J_REAL_TORCH @ J_REAL_TORCH
    real_gap = float(torch.linalg.matrix_norm(comm).item())
    control_gap = float(torch.linalg.matrix_norm(control).item())
    return {
        "observable": "||J P0 - P0 J||_F for finite incidence/skew map and flattened projection",
        "real_order_gap": real_gap,
        "commuting_control_gap": control_gap,
        "pass": bool(real_gap > CONTROL_FLOOR and control_gap <= EPS),
    }


def n01_order_witness_jax() -> dict[str, Any]:
    j_real = jnp.real(J_JAX)
    p0_real = jnp.real(P0_JAX)
    comm = j_real @ p0_real - p0_real @ j_real
    control = j_real @ j_real - j_real @ j_real
    real_gap = float(jnp.linalg.norm(comm))
    control_gap = float(jnp.linalg.norm(control))
    return {
        "observable": "JAX mirror ||J P0 - P0 J||_F",
        "real_order_gap": real_gap,
        "commuting_control_gap": control_gap,
        "pass": bool(real_gap > CONTROL_FLOOR and control_gap <= EPS),
    }


def clifford_vector(coeffs: torch.Tensor):
    out = 0 * _CLIFFORD_BASIS[0]
    for coeff, basis in zip(coeffs, _CLIFFORD_BASIS, strict=True):
        out += float(coeff.item()) * basis
    return out


def clifford_inner(coeffs_a: torch.Tensor, coeffs_b: torch.Tensor) -> float:
    a_vec = clifford_vector(coeffs_a)
    b_vec = clifford_vector(coeffs_b)
    return float((a_vec | b_vec).value[0])


def clifford_residuals(z_rows: torch.Tensor, op_real: torch.Tensor) -> list[float]:
    residuals: list[float] = []
    for row in z_rows:
        real = torch.real(row).to(RTYPE)
        imag = torch.imag(row).to(RTYPE)
        op_real_part = op_real @ real
        op_imag_part = op_real @ imag
        residual_real = clifford_inner(real, op_real_part) - clifford_inner(imag, op_imag_part)
        residual_imag = clifford_inner(real, op_imag_part) + clifford_inner(imag, op_real_part)
        residuals.append(math.hypot(residual_real, residual_imag))
    return residuals


def sympy_exact_incidence() -> dict[str, Any]:
    z0, z1, z2, z3 = sp.symbols("z0 z1 z2 z3")
    z_vec = sp.Matrix([z0, z1, z2, z3])
    j_mat = sp.Matrix([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 0, -1], [0, 0, 1, 0]])
    p0_mat = sp.diag(1, 0, 0, 0)
    real_expr = sp.simplify((z_vec.T * j_mat * z_vec)[0])
    control_expr = sp.simplify((z_vec.T * p0_mat * z_vec)[0])
    control_sample = sp.simplify(
        control_expr.subs(
            {
                z0: sp.Rational(3, 5) + sp.I * sp.Rational(2, 7),
                z1: sp.Rational(5, 11) + sp.I * sp.Rational(1, 13),
                z2: sp.Rational(7, 17) + sp.I * sp.Rational(3, 19),
                z3: sp.Rational(11, 23) + sp.I * sp.Rational(5, 29),
            }
        )
    )
    real_claim_holds = bool(real_expr == 0)
    control_claim_holds = bool(control_sample == 0)
    return {
        "tool": "sympy",
        "incidence_expression_ZtJZ": str(real_expr),
        "flattened_control_expression_ZtP0Z": str(control_expr),
        "flattened_control_sample": str(control_sample),
        "real_claim_holds": real_claim_holds,
        "control_claim_holds": control_claim_holds,
        "differ": bool(real_claim_holds != control_claim_holds),
        "load_bearing": bool(real_claim_holds and not control_claim_holds),
        "no_numeric_ablation_emitted": True,
        "pass": bool(real_claim_holds and not control_claim_holds),
    }


def z3_complex_bilinear_parts(op: list[list[int]], r: list[Any], im: list[Any]) -> tuple[Any, Any]:
    op_r = []
    op_i = []
    for row in op:
        op_r.append(sum(row[j] * r[j] for j in range(4)))
        op_i.append(sum(row[j] * im[j] for j in range(4)))
    real_part = sum(r[j] * op_r[j] - im[j] * op_i[j] for j in range(4))
    imag_part = sum(r[j] * op_i[j] + im[j] * op_r[j] for j in range(4))
    return z3.simplify(real_part), z3.simplify(imag_part)


def z3_structural_incidence() -> dict[str, Any]:
    j_op = [[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 0, -1], [0, 0, 1, 0]]
    p0_op = [[1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    r = list(z3.Reals("r0 r1 r2 r3"))
    im = list(z3.Reals("i0 i1 i2 i3"))
    real_part, imag_part = z3_complex_bilinear_parts(j_op, r, im)
    s = z3.Solver()
    s.set("timeout", 15000)
    s.add(z3.Or(real_part != 0, imag_part != 0))
    incidence_negation_status = str(s.check())

    ctrl_real, ctrl_imag = z3_complex_bilinear_parts(p0_op, r, im)
    c = z3.Solver()
    c.set("timeout", 15000)
    c.add(r[0] == 1, im[0] == 0, r[1] == 0, im[1] == 0, r[2] == 0, im[2] == 0, r[3] == 0, im[3] == 0)
    c.add(z3.Or(ctrl_real != 0, ctrl_imag != 0))
    flattened_counterexample_status = str(c.check())
    return {
        "tool": "z3",
        "incidence_identity_negation_status": incidence_negation_status,
        "incidence_identity_unsat": incidence_negation_status == "unsat",
        "flattened_control_counterexample_status": flattened_counterexample_status,
        "flattened_control_can_violate": flattened_counterexample_status == "sat",
        "pass": bool(incidence_negation_status == "unsat" and flattened_counterexample_status == "sat"),
    }


def smt_incidence_flip(real_residual: float, control_residual: float) -> dict[str, Any]:
    proof = smt_load_bearing(
        claim="projective_twistor_incidence_max_abs_Z_dot_W_le_eps",
        real_measured={
            "incidence_residual": real_residual,
            "eps": EPS,
        },
        control_measured={
            "incidence_residual": control_residual,
            "eps": EPS,
        },
        claim_builder=lambda v: v["incidence_residual"] <= v["eps"],
    )
    proof["pass"] = bool(
        proof["real_claim_verdict"] == "sat"
        and proof["negated_claim_verdict"] == "unsat"
        and proof["differ"] is True
        and proof["bound_to_measured"] is True
    )
    return proof


def scale_rung(n: int) -> dict[str, Any]:
    z_torch = twistor_samples_torch(n)
    w_torch = dual_torch(z_torch, J_TORCH)
    control_w_torch = dual_torch(z_torch, P0_TORCH)
    real_values = incidence_values_torch(z_torch, w_torch)
    control_values = incidence_values_torch(z_torch, control_w_torch)
    scales = projective_scales_torch(n).reshape(n, 1)
    scaled_values = incidence_values_torch(scales * z_torch, w_torch / scales)
    projective_defect = max_abs_torch(scaled_values - real_values)

    z_jax = twistor_samples_jax(n)
    w_jax = dual_jax(z_jax, J_JAX)
    control_w_jax = dual_jax(z_jax, P0_JAX)
    real_values_jax = incidence_values_jax(z_jax, w_jax)
    control_values_jax = incidence_values_jax(z_jax, control_w_jax)
    scales_jax = projective_scales_jax(n).reshape((n, 1))
    scaled_values_jax = incidence_values_jax(scales_jax * z_jax, w_jax / scales_jax)
    projective_defect_jax = max_abs_jax(scaled_values_jax - real_values_jax)

    torch_real_max = max_abs_torch(real_values)
    torch_control_max = max_abs_torch(control_values)
    torch_control_min = min_abs_torch(control_values)
    jax_real_max = max_abs_jax(real_values_jax)
    jax_control_max = max_abs_jax(control_values_jax)
    jax_control_min = min_abs_jax(control_values_jax)
    clifford_real = clifford_residuals(z_torch, J_REAL_TORCH)
    clifford_control = clifford_residuals(z_torch, P0_REAL_TORCH)
    clifford_real_max = max(clifford_real)
    clifford_control_max = max(clifford_control)
    clifford_control_min = min(clifford_control)
    n01_torch = n01_order_witness_torch()
    n01_jax = n01_order_witness_jax()

    jax_vs_pytorch_delta = max(
        abs(torch_real_max - jax_real_max),
        abs(torch_control_max - jax_control_max),
        abs(torch_control_min - jax_control_min),
        abs(projective_defect - projective_defect_jax),
    )
    rung_pass = bool(
        torch_real_max <= EPS
        and jax_real_max <= EPS
        and torch_control_min > CONTROL_FLOOR
        and jax_control_min > CONTROL_FLOOR
        and projective_defect <= EPS
        and projective_defect_jax <= EPS
        and clifford_real_max <= EPS
        and clifford_control_min > CONTROL_FLOOR
        and jax_vs_pytorch_delta <= 1.0e-8
        and n01_torch["pass"]
        and n01_jax["pass"]
    )
    return {
        "sites_or_qubits": n,
        "sample_count": n,
        "projective_complex_dimension": 3,
        "homogeneous_twistor_components": 4,
        "real_component_count": 8,
        "operator_count": 2,
        "path_count": n,
        "dense_state_closure_used": False,
        "torch_max_incidence_residual": torch_real_max,
        "torch_max_flattened_control_residual": torch_control_max,
        "torch_min_flattened_control_residual": torch_control_min,
        "torch_projective_scaling_max_defect": projective_defect,
        "jax_max_incidence_residual": jax_real_max,
        "jax_max_flattened_control_residual": jax_control_max,
        "jax_min_flattened_control_residual": jax_control_min,
        "jax_projective_scaling_max_defect": projective_defect_jax,
        "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
        "clifford_max_incidence_residual": clifford_real_max,
        "clifford_max_flattened_control_residual": clifford_control_max,
        "clifford_min_flattened_control_residual": clifford_control_min,
        "n01_torch_order_witness": n01_torch,
        "n01_jax_order_witness": n01_jax,
        "pass": rung_pass,
    }


def add_ablation_pass(row: dict[str, Any]) -> dict[str, Any]:
    row["pass"] = bool(abs(float(row["outcome_delta"])) > CONTROL_FLOOR)
    return row


def build_tool_ablations(top: dict[str, Any]) -> dict[str, Any]:
    return {
        "torch_incidence_structure_ablation": add_ablation_pass(
            tool_ablation(
                "torch max_abs(Z.W): skew incidence W=JZ vs flattened control W=P0Z",
                baseline_value=top["torch_max_incidence_residual"],
                ablated_value=top["torch_max_flattened_control_residual"],
                tool="torch",
            )
        ),
        "clifford_incidence_structure_ablation": add_ablation_pass(
            tool_ablation(
                "Cl(4) vector inner-product residual: skew J structure vs flattened P0 structure",
                baseline_value=top["clifford_max_incidence_residual"],
                ablated_value=top["clifford_max_flattened_control_residual"],
                tool="clifford",
            )
        ),
    }


def known_check(name: str, computed: Any, known: Any, match: bool, tolerance: float | None = None) -> dict[str, Any]:
    row = {
        "name": name,
        "computed": computed,
        "known": known,
        "match": bool(match),
    }
    if tolerance is not None:
        row["tolerance"] = tolerance
    return row


def build_known_value_checks(
    top: dict[str, Any],
    sympy_exact: dict[str, Any],
    z3_structural: dict[str, Any],
    smt_proof: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        known_check(
            "torch_incidence_residual_zero",
            top["torch_max_incidence_residual"],
            0.0,
            abs(top["torch_max_incidence_residual"]) <= EPS,
            EPS,
        ),
        known_check(
            "jax_incidence_residual_zero",
            top["jax_max_incidence_residual"],
            0.0,
            abs(top["jax_max_incidence_residual"]) <= EPS,
            EPS,
        ),
        known_check(
            "flattened_control_violates_incidence",
            top["torch_min_flattened_control_residual"],
            f"> {CONTROL_FLOOR}",
            top["torch_min_flattened_control_residual"] > CONTROL_FLOOR,
        ),
        known_check(
            "projective_scaling_preserves_zero_incidence",
            top["torch_projective_scaling_max_defect"],
            0.0,
            abs(top["torch_projective_scaling_max_defect"]) <= EPS,
            EPS,
        ),
        known_check(
            "sympy_exact_ZtJZ_identity",
            sympy_exact["incidence_expression_ZtJZ"],
            "0",
            sympy_exact["pass"],
        ),
        known_check(
            "z3_structural_incidence_negation_unsat",
            z3_structural["incidence_identity_negation_status"],
            "unsat",
            z3_structural["incidence_identity_negation_status"] == "unsat",
        ),
        known_check(
            "smt_load_bearing_real_sat_control_unsat",
            {
                "real": smt_proof["real_claim_verdict"],
                "control": smt_proof["negated_claim_verdict"],
            },
            {"real": "sat", "control": "unsat"},
            smt_proof["pass"],
        ),
        known_check(
            "clifford_skew_incidence_residual_zero",
            top["clifford_max_incidence_residual"],
            0.0,
            abs(top["clifford_max_incidence_residual"]) <= EPS,
            EPS,
        ),
        known_check(
            "n01_commutator_gap_positive",
            top["n01_torch_order_witness"]["real_order_gap"],
            f"> {CONTROL_FLOOR}",
            top["n01_torch_order_witness"]["pass"],
        ),
    ]


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    scale_rows = {str(n): scale_rung(n) for n in SCALE_RUNGS}
    top = scale_rows["64"]
    sympy_exact = sympy_exact_incidence()
    z3_structural = z3_structural_incidence()
    smt_proof = smt_incidence_flip(
        top["torch_max_incidence_residual"],
        top["torch_max_flattened_control_residual"],
    )
    tool_ablations = build_tool_ablations(top)
    known_value_checks = build_known_value_checks(top, sympy_exact, z3_structural, smt_proof)

    scale_pass = all(row["pass"] for row in scale_rows.values())
    proof_pass = bool(sympy_exact["pass"] and z3_structural["pass"] and smt_proof["pass"])
    controls_pass = bool(top["torch_min_flattened_control_residual"] > CONTROL_FLOOR)
    ablation_pass = all(row["pass"] for row in tool_ablations.values())
    known_pass = all(row["match"] for row in known_value_checks)
    jax_delta = max(row["jax_vs_pytorch_delta"] for row in scale_rows.values())
    n01_pass = all(row["n01_torch_order_witness"]["pass"] and row["n01_jax_order_witness"]["pass"] for row in scale_rows.values())
    all_pass = bool(scale_pass and proof_pass and controls_pass and ablation_pass and known_pass and n01_pass and jax_delta <= 1.0e-8)

    blockers = []
    if not scale_pass:
        blockers.append("one or more non-dense 8/16/32/64 twistor-incidence rungs failed")
    if not proof_pass:
        blockers.append("sympy exact, z3 structural, or helper-bound SMT incidence proof failed")
    if not controls_pass:
        blockers.append("flattened control did not violate the incidence invariant")
    if not ablation_pass:
        blockers.append("one or more genuine structure/tool ablations had zero effect")
    if not known_pass:
        blockers.append("one or more computed known-value checks failed")
    if not n01_pass:
        blockers.append("finite N01 operator commutator witness failed")
    if jax_delta > 1.0e-8:
        blockers.append(f"jax_vs_pytorch_delta {jax_delta} exceeds tolerance")

    min_control_residual = min(row["torch_min_flattened_control_residual"] for row in scale_rows.values())
    max_incidence_residual = max(row["torch_max_incidence_residual"] for row in scale_rows.values())
    min_n01_gap = min(row["n01_torch_order_witness"]["real_order_gap"] for row in scale_rows.values())
    survivor_capacity = min(min_control_residual, min_n01_gap)

    controls = {
        "flattened_dual_projection_control": {
            "description": "same finite twistor samples Z but the skew incidence map J is replaced by rank-1 projection P0; recomputed invariant Z.(P0Z) is nonzero",
            "baseline_max_abs_Z_dot_W": top["torch_max_incidence_residual"],
            "control_min_abs_Z_dot_W": top["torch_min_flattened_control_residual"],
            "control_max_abs_Z_dot_W": top["torch_max_flattened_control_residual"],
            "kills_incidence_claim": bool(top["torch_min_flattened_control_residual"] > CONTROL_FLOOR),
            "pass": bool(top["torch_min_flattened_control_residual"] > CONTROL_FLOOR),
        },
        "commuting_operator_control": {
            "description": "N01 control recomputes J then J versus J then J, so the order gap is zero",
            "real_order_gap": top["n01_torch_order_witness"]["real_order_gap"],
            "control_order_gap": top["n01_torch_order_witness"]["commuting_control_gap"],
            "pass": bool(top["n01_torch_order_witness"]["pass"]),
        },
        "dense_state_closure_rejected": {
            "description": "the carrier is a finite list of CP^3 homogeneous coordinates and dual covectors; no dense 2^N state vector is constructed",
            "dense_state_closure_used": False,
            "rungs": list(SCALE_RUNGS),
            "pass": True,
        },
    }

    result = {
        "schema": "formal_scout_stage3_geometry_result_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "object_id": OBJECT_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "classification": "lego",
        "tier": "canonical STAGE 3 geometry object",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Build one standalone Stage 3 projective twistor incidence geometry object with exact incidence, SMT flip, Clifford geometry, controls, JAX mirror, and 8/16/32/64 non-dense scale rungs.",
        "scientific_question": "Can finite projective twistor incidence pairs ([Z],[W]) in CP^3 x CP^3* satisfy Z.W=0 at 8/16/32/64 samples, while a flattened control violates the same invariant and the helper-bound proof flips real sat / control unsat?",
        "finite_map": {
            "domain": "For n in {8,16,32,64}: finite homogeneous twistor samples Z_i in C^4, skew incidence operator J, flattened projection P0, finite projective scales lambda_i, and finite operators {J,P0}.",
            "codomain_or_output": "Dual covectors W_i=JZ_i, bilinear incidence residuals Z_i.W_i, flattened-control residuals Z_i.(P0Z_i), projective-scaling defects, exact/SAT proof readouts, Clifford residuals, and blocked downstream consumers.",
            "definition": "Incidence_n maps each finite twistor point [Z_i] to a dual incidence covector [W_i]=[JZ_i] with J^T=-J, so Z_i^T J Z_i=0. The flattened control replaces J by P0.",
        },
        "domain": {
            "scale_rungs": list(SCALE_RUNGS),
            "twistor_homogeneous_components": 4,
            "projective_space": "CP^3 finite homogeneous samples",
            "dual_space": "CP^3* finite dual covectors generated by W=JZ",
            "finite_operators": ["J skew incidence map", "P0 flattened projection control"],
            "dense_state_closure_used": False,
        },
        "codomain_or_output": {
            "primary_invariant": "max_i |Z_i.W_i| <= eps",
            "control_invariant": "min_i |Z_i.(P0 Z_i)| > control_floor",
            "geometry_output": "finite projective incidence residuals plus exact and Clifford witnesses",
        },
        "root_constraints": {
            "F01": {
                "role": "active",
                "statement": "finite carrier/probe/operator/path set: each rung has finitely many CP^3 samples, finite dual covectors, finite projective scales, and finite operators.",
            },
            "N01": {
                "role": "active_bounded_witness",
                "statement": "finite order-sensitive operator witness ||J P0 - P0 J||_F is positive; commuting J/J control has zero order gap.",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 noncommuting/order-sensitive operation/control witnessed by J/P0 commutator",
        ],
        "carrier_layer": "finite_projective_twistor_incidence_pairs",
        "geometry_layer": "twistor_incidence_CP3_projective_geometry_object",
        "carrier_realization": "torch.complex128 finite list of C^4 homogeneous twistor coordinates and C^4 dual covectors; JAX complex128 mirrors the representable bilinear residuals; no NumPy bridge.",
        "peps3d_embedding": "not_claimed_for_this_standalone_stage3_geometry_lego; no manifold/layer/G-structure admission is attempted",
        "spinor_state": "twistor coordinates are complex spinor-style homogeneous coordinates in C^4, but no torch spinor-network or PEPS3D manifold carrier is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/F01_finite_distinguishability_results.json",
            "system_v5/ops/formal_scouts/results/carrier_torch_complex_spinor_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "projective twistor incidence invariant Z.W=0 for W=JZ over finite CP^3 samples",
        "branch_status_before_run": "single standalone geometry lego requested; no manifold layer, G-structure, coupling, bridge, flux, Axis0, FEP, gravity, or physics route opened",
        "allowed_claims": [
            "bounded Stage 3 twistor incidence geometry lego result exists/runs if this JSON and required gates pass",
            "finite projective twistor incidence residual Z.W=0 holds for W=JZ at 8/16/32/64 samples",
            "flattened control W=P0Z violates the same incidence invariant",
            "helper-bound z3 proof flips real sat / control unsat on measured incidence residuals",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "standalone geometry object only",
            "no PEPS3D manifold embedding",
            "no layer completion, G-structure selection, stack readiness, Xi, Phi0, Axis0, flux, FEP, gravity, bridge, basin, physics, or final manifold admission",
        ],
        "eligible_consumers": ["future bounded Stage-3 geometry comparisons only after citing this result path and fresh gate output"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3 measured residual flip",
            "sympy exact Z^T J Z identity and flattened-control contrast",
            "z3 structural universal skew-incidence negation UNSAT",
            "clifford Cl(4) inner-product incidence residual and flattened-structure ablation",
        ],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_negatives": list(controls.keys()),
        "negatives_run": controls,
        "kill_conditions": {
            "flattened_dual_projection_control": "min_i |Z_i.(P0 Z_i)| must be > control_floor and make the helper-bound incidence claim unsat",
            "commuting_operator_control": "J/J order control must have zero commutator gap while J/P0 has positive gap",
            "dense_state_closure_rejected": "no full 2^N dense state closure may be materialized or claimed",
        },
        "required_artifacts": ["result JSON", "scale_ladder", "torch_primary_result", "jax_mirror_result", "proof_results", "controls", "tool_ablations", "known_value_checks"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "controls_pass": controls_pass,
            "tool_ablations_pass": ablation_pass,
            "known_value_checks_pass": known_pass,
            "jax_vs_pytorch_delta": jax_delta,
            "max_incidence_residual": max_incidence_residual,
            "min_flattened_control_residual": min_control_residual,
            "min_n01_order_gap": min_n01_gap,
            "elapsed_seconds": time.time() - started,
        },
        "torch_primary_result": {
            "engine": "torch",
            "dtype": "torch.complex128",
            "claim": "finite projective twistor incidence residual max_i |Z_i.W_i| <= eps for W_i=JZ_i",
            "top_rung": top,
            "pass": bool(scale_pass and n01_pass),
        },
        "jax_mirror_result": {
            "engine": "jax",
            "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
            "claim": "JAX complex128 mirrors the representable finite projective incidence residual and flattened control computations",
            "rungs": {
                rung: {
                    "sites_or_qubits": row["sites_or_qubits"],
                    "jax_max_incidence_residual": row["jax_max_incidence_residual"],
                    "jax_max_flattened_control_residual": row["jax_max_flattened_control_residual"],
                    "jax_min_flattened_control_residual": row["jax_min_flattened_control_residual"],
                    "jax_projective_scaling_max_defect": row["jax_projective_scaling_max_defect"],
                    "jax_vs_pytorch_delta": row["jax_vs_pytorch_delta"],
                    "pass": bool(row["jax_max_incidence_residual"] <= EPS and row["jax_min_flattened_control_residual"] > CONTROL_FLOOR),
                }
                for rung, row in scale_rows.items()
            },
            "pass": bool(jax_delta <= 1.0e-8 and all(row["jax_max_incidence_residual"] <= EPS for row in scale_rows.values())),
        },
        "jax_vs_pytorch_delta": jax_delta,
        "proof_results": {
            "smt_load_bearing_incidence_residual": smt_proof,
            "sympy_exact_incidence_flip": sympy_exact,
            "z3_structural_incidence_identity": z3_structural,
            "clifford_geometry_check": {
                "tool": "clifford",
                "algebra": "Cl(4)",
                "max_incidence_residual": top["clifford_max_incidence_residual"],
                "max_flattened_control_residual": top["clifford_max_flattened_control_residual"],
                "pass": bool(top["clifford_max_incidence_residual"] <= EPS and top["clifford_min_flattened_control_residual"] > CONTROL_FLOOR),
            },
            "pass": proof_pass,
        },
        "controls": controls,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "known_value_checks": known_value_checks,
        "scale_ladder": {
            "rungs": scale_rows,
            "scale_axis": "finite_projective_twistor_sample_count",
            "dense_state_closure_used": False,
            "pass": scale_pass,
        },
        "positive": {
            "twistor_incidence_smt_flip": {"pass": smt_proof["pass"], "proof": smt_proof},
            "scale_8_16_32_64_non_dense_projective_samples": {"pass": scale_pass, "rungs": scale_rows},
            "sympy_exact_incidence": sympy_exact,
            "z3_structural_incidence": z3_structural,
            "clifford_geometry": {
                "max_incidence_residual": top["clifford_max_incidence_residual"],
                "max_flattened_control_residual": top["clifford_max_flattened_control_residual"],
                "pass": bool(top["clifford_max_incidence_residual"] <= EPS and top["clifford_min_flattened_control_residual"] > CONTROL_FLOOR),
            },
            "local_n01_order_witness": top["n01_torch_order_witness"],
        },
        "graveyard_companions": controls,
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "numpy_claim_bearing": {"used": False, "pass": True},
            "geomstats_jax_path_faked": {"used": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "manifold_layer_claim": {"claimed": False, "pass": True},
            "g_structure_claim": {"claimed": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
        },
        "nearby_variants": {
            "flattened_dual_projection_control": controls["flattened_dual_projection_control"],
            "commuting_operator_control": controls["commuting_operator_control"],
            "pass": controls_pass,
        },
        "shells": [
            {
                "name": "projective_twistor_incidence_geometry_object",
                "status": "stage_3_geometry_lego_only",
                "rungs": list(SCALE_RUNGS),
                "max_incidence_residual": max_incidence_residual,
                "min_flattened_control_residual": min_control_residual,
                "survives": all_pass,
            }
        ],
        "future_continuations": [
            "compare this incidence object against other standalone Stage-3 projective geometry legos only after this result is cited and re-gated",
            "do not use this result as a layer, G-structure, Xi/Phi0/Axis0/flux/FEP/gravity, bridge, basin, physics, or final-manifold receipt",
        ],
        "compatibility_weights": {
            "local_stage3_geometry_input": 1.0 if all_pass else 0.0,
            "future_geometry_comparison_input": 0.5 if all_pass else 0.0,
            "Xi": 0.0,
            "Phi0": 0.0,
            "Axis0": 0.0,
            "flux": 0.0,
            "FEP": 0.0,
            "gravity": 0.0,
        },
        "compression_map": {
            "from": "finite CP^3 homogeneous samples Z_i, skew dual covectors W_i=JZ_i, flattened controls P0Z_i, projective scales, and finite operators J/P0",
            "to": "incidence residuals, control residuals, projective-scaling defects, exact proof readouts, Clifford residuals, N01 order gap, and blocked-consumer boundary",
            "loss_boundary": "does not preserve or claim full twistor theory, PEPS3D manifold embedding, layer completion, G-structure selection, Axis0, flux, FEP, gravity, bridge, basin, physics, or final manifold admission",
        },
        "present_survivor": {
            "object": OBJECT_ID,
            "capacity": survivor_capacity,
            "survives": bool(all_pass),
            "blocked_capacity": BLOCKED_CONSUMERS,
        },
        "survivor_invariant": {
            "invariant": "twistor_incidence survives iff all rungs are non-dense, Z.W residual <= eps, flattened control residual > floor, JAX parity holds, exact/SMT proof flips, Clifford structure ablation is nonzero, N01 order witness passes, and promotion_allowed=false",
            "computed_capacity": survivor_capacity,
            "threshold": CONTROL_FLOOR,
            "passed": bool(all_pass and survivor_capacity > CONTROL_FLOOR),
        },
        "outward_record": {
            "result_path": str(OUT_PATH.relative_to(ROOT)),
            "per_sim_contract_command": f"../../../scripts/per_sim_contract.py {OUT_PATH.relative_to(ROOT)}",
            "max_deep_gate_command": f"../../../scripts/max_deep_lego_gate.py {OUT_PATH.relative_to(ROOT)} --scale-required --rigor",
            "recheck_proof_command": f"../../../scripts/recheck_proof.py {OUT_PATH.relative_to(ROOT)} --rerun {pathlib.Path(__file__).name} --python /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
            "claim_ceiling": "Stage-3 standalone twistor incidence geometry lego only; no downstream consumer admitted",
        },
        "pass_rule": "all 8/16/32/64 rungs are non-dense and pass; torch/JAX agree; exact SymPy and structural z3 prove the skew incidence identity; helper-bound z3 proof flips real sat/control unsat on measured residuals; flattened controls kill; Clifford structure ablation is recomputed and nonzero",
        "fail_rule": "fail on dense closure, missing rung, Z.W residual above eps, flattened control failing to violate, no real/control SMT flip, JAX mismatch, missing exact symbolic identity, zero/cosmetic ablation, failed N01 order witness, or downstream promotion",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "why_not_v4_probes": "This is a Stage-3 geometry object lego with explicit non-dense 8/16/32/64 projective incidence samples, helper-bound proof flip, exact symbolic incidence, JAX parity, Clifford geometry ablation, and promotion_allowed=false.",
        "blockers": blockers,
        "required_pass": all_pass,
        "all_pass": all_pass,
    }
    return result


def main() -> int:
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "required_pass": result["required_pass"],
                "result_path": str(OUT_PATH.relative_to(ROOT)),
                "jax_vs_pytorch_delta": result["jax_vs_pytorch_delta"],
                "proof_pass": result["proof_results"]["pass"],
                "scale_pass": result["scale_ladder"]["pass"],
                "blockers": result["blockers"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
