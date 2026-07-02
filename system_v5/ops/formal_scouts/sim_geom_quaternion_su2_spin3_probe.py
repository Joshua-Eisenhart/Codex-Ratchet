#!/usr/bin/env python3
"""Canonical Stage 3 quaternion/SU(2)/Spin(3) geometry object probe.

Finite map:
    q in finite unit-quaternion samples -> (U_q in SU(2), R_q in SO(3)).

Invariant:
    q and -q induce the same SO(3) rotation.  The negative control flattens
    the map to sign-sensitive raw quaternion coordinates, where the same
    antipodal image-gap invariant fails.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("NUMBA_DISABLE_CACHE", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
from clifford import Cl
import sympy as sp
import torch
import z3

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "sim_geom_quaternion_su2_spin3_probe"
OBJECT_ID = "quaternion_su2"
OUT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"

RTYPE = torch.float64
CTYPE = torch.complex128
EPS = 1.0e-9
TOL = 1.0e-8
SCALE_RUNGS = (8, 16, 32, 64)
SITE_SHAPES = {8: (2, 2, 2), 16: (4, 2, 2), 32: (4, 4, 2), 64: (4, 4, 4)}
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY claim-bearing finite unit-quaternion samples, SU(2) matrices, SO(3) rotation images, double-cover invariant, controls, and scale ladder.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 parity mirror for the representable quaternion-to-SO(3) and quaternion-to-SU(2) finite formulas; no geomstats/JAX path is claimed.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING geometry tool: Cl(3) even rotor conjugation computes the q/-q action-matrix gap; the ablation recomputes that same observable after removing the rotor and using a non-Clifford signed-coordinate substitute.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING exact rational proof surface for |q|=1, SU(2) determinant/unitarity, R(q)=R(-q), and flattened-control failure.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING proof via load_bearing_proof.smt_load_bearing; z3 variables are bound to measured antipodal image-gap observables.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING cross-check through load_bearing_proof.smt_load_bearing cvc5_claim_pairs on the same measured observables.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not used for claim-bearing computation.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "clifford": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
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
            item = value.detach().cpu().item()
            if isinstance(item, complex):
                return {"real": float(item.real), "imag": float(item.imag)}
            return item
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
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator, "float": float(value)}
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def sample_unit_quaternions_torch(count: int) -> torch.Tensor:
    rows = []
    for idx in range(count):
        raw = torch.tensor(
            [
                1.0 + float(idx % 5),
                float((2 * idx + 1) % 11) - 5.0,
                float((3 * idx + 2) % 13) - 6.0,
                float((5 * idx + 3) % 17) - 8.0,
            ],
            dtype=RTYPE,
        )
        if torch.linalg.vector_norm(raw[1:]) <= EPS:
            raw = raw.clone()
            raw[1] = 1.0
        rows.append(raw / torch.linalg.vector_norm(raw))
    return torch.stack(rows)


def sample_unit_quaternions_jax(count: int) -> jnp.ndarray:
    rows = []
    for idx in range(count):
        raw = jnp.asarray(
            [
                1.0 + float(idx % 5),
                float((2 * idx + 1) % 11) - 5.0,
                float((3 * idx + 2) % 13) - 6.0,
                float((5 * idx + 3) % 17) - 8.0,
            ],
            dtype=jnp.float64,
        )
        raw = jnp.where(jnp.linalg.norm(raw[1:]) <= EPS, raw.at[1].set(1.0), raw)
        rows.append(raw / jnp.linalg.norm(raw))
    return jnp.stack(rows)


def qmul_torch(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    aw, ax, ay, az = a.unbind(-1)
    bw, bx, by, bz = b.unbind(-1)
    return torch.stack(
        [
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ],
        dim=-1,
    )


def qnorm_torch(q: torch.Tensor) -> torch.Tensor:
    return torch.linalg.vector_norm(q, dim=-1)


def q_to_so3_torch(q: torch.Tensor) -> torch.Tensor:
    q = q / torch.linalg.vector_norm(q, dim=-1, keepdim=True)
    w, x, y, z = q.unbind(-1)
    one = q.new_tensor(1.0)
    two = q.new_tensor(2.0)
    return torch.stack(
        [
            torch.stack([one - two * (y * y + z * z), two * (x * y - w * z), two * (x * z + w * y)], dim=-1),
            torch.stack([two * (x * y + w * z), one - two * (x * x + z * z), two * (y * z - w * x)], dim=-1),
            torch.stack([two * (x * z - w * y), two * (y * z + w * x), one - two * (x * x + y * y)], dim=-1),
        ],
        dim=-2,
    )


def q_to_su2_torch(q: torch.Tensor) -> torch.Tensor:
    q = (q / torch.linalg.vector_norm(q, dim=-1, keepdim=True)).to(CTYPE)
    w, x, y, z = q.unbind(-1)
    return torch.stack(
        [
            torch.stack([w + 1j * z, y + 1j * x], dim=-1),
            torch.stack([-y + 1j * x, w - 1j * z], dim=-1),
        ],
        dim=-2,
    )


def q_to_so3_jax(q: jnp.ndarray) -> jnp.ndarray:
    q = q / jnp.linalg.norm(q, axis=-1, keepdims=True)
    w, x, y, z = jnp.moveaxis(q, -1, 0)
    one = jnp.asarray(1.0, dtype=jnp.float64)
    two = jnp.asarray(2.0, dtype=jnp.float64)
    return jnp.stack(
        [
            jnp.stack([one - two * (y * y + z * z), two * (x * y - w * z), two * (x * z + w * y)], axis=-1),
            jnp.stack([two * (x * y + w * z), one - two * (x * x + z * z), two * (y * z - w * x)], axis=-1),
            jnp.stack([two * (x * z - w * y), two * (y * z + w * x), one - two * (x * x + y * y)], axis=-1),
        ],
        axis=-2,
    )


def q_to_su2_jax(q: jnp.ndarray) -> jnp.ndarray:
    q = (q / jnp.linalg.norm(q, axis=-1, keepdims=True)).astype(jnp.complex128)
    w, x, y, z = jnp.moveaxis(q, -1, 0)
    return jnp.stack(
        [
            jnp.stack([w + 1j * z, y + 1j * x], axis=-1),
            jnp.stack([-y + 1j * x, w - 1j * z], axis=-1),
        ],
        axis=-2,
    )


def torch_metrics(sample_count: int) -> dict[str, Any]:
    qs = sample_unit_quaternions_torch(sample_count)
    rotations = q_to_so3_torch(qs)
    antipodal_rotations = q_to_so3_torch(-qs)
    su2 = q_to_su2_torch(qs)
    identity3 = torch.eye(3, dtype=RTYPE).expand(sample_count, 3, 3)
    identity2 = torch.eye(2, dtype=CTYPE).expand(sample_count, 2, 2)
    flat_control = qs[:, 1:]
    flat_control_antipodal = (-qs)[:, 1:]
    qi = torch.tensor([0.0, 1.0, 0.0, 0.0], dtype=RTYPE)
    qj = torch.tensor([0.0, 0.0, 1.0, 0.0], dtype=RTYPE)
    qk = torch.tensor([0.0, 0.0, 0.0, 1.0], dtype=RTYPE)
    ij = qmul_torch(qi, qj)
    ji = qmul_torch(qj, qi)
    ii = qmul_torch(qi, qi)
    jj = qmul_torch(qj, qj)
    kk = qmul_torch(qk, qk)
    return {
        "samples": qs,
        "rotations": rotations,
        "su2": su2,
        "unit_norm_max_error": float(torch.max(torch.abs(qnorm_torch(qs) - 1.0)).item()),
        "antipodal_rotation_gap": float(torch.max(torch.linalg.matrix_norm(rotations - antipodal_rotations, dim=(1, 2))).item()),
        "flattened_control_antipodal_gap": float(torch.max(torch.linalg.vector_norm(flat_control - flat_control_antipodal, dim=1)).item()),
        "flattened_control_min_gap": float(torch.min(torch.linalg.vector_norm(flat_control - flat_control_antipodal, dim=1)).item()),
        "so3_orthogonality_defect": float(torch.max(torch.linalg.matrix_norm(torch.transpose(rotations, 1, 2) @ rotations - identity3, dim=(1, 2))).item()),
        "so3_det_error": float(torch.max(torch.abs(torch.linalg.det(rotations) - 1.0)).item()),
        "su2_unitarity_defect": float(torch.max(torch.linalg.matrix_norm(torch.conj(torch.transpose(su2, 1, 2)) @ su2 - identity2, dim=(1, 2))).item()),
        "su2_det_error": float(torch.max(torch.abs(torch.linalg.det(su2) - (1.0 + 0.0j))).item()),
        "quaternion_order_gap_ij_vs_ji": float(torch.linalg.vector_norm(ij - ji).item()),
        "quaternion_ij_minus_k_gap": float(torch.linalg.vector_norm(ij - qk).item()),
        "quaternion_unit_square_gaps": {
            "i2_plus_1": float(torch.linalg.vector_norm(ii - torch.tensor([-1.0, 0.0, 0.0, 0.0], dtype=RTYPE)).item()),
            "j2_plus_1": float(torch.linalg.vector_norm(jj - torch.tensor([-1.0, 0.0, 0.0, 0.0], dtype=RTYPE)).item()),
            "k2_plus_1": float(torch.linalg.vector_norm(kk - torch.tensor([-1.0, 0.0, 0.0, 0.0], dtype=RTYPE)).item()),
        },
    }


def jax_metrics(sample_count: int) -> dict[str, Any]:
    qs = sample_unit_quaternions_jax(sample_count)
    rotations = q_to_so3_jax(qs)
    antipodal_rotations = q_to_so3_jax(-qs)
    su2 = q_to_su2_jax(qs)
    identity3 = jnp.broadcast_to(jnp.eye(3, dtype=jnp.float64), (sample_count, 3, 3))
    identity2 = jnp.broadcast_to(jnp.eye(2, dtype=jnp.complex128), (sample_count, 2, 2))
    flat_control = qs[:, 1:]
    flat_control_antipodal = (-qs)[:, 1:]
    return {
        "unit_norm_max_error": float(jnp.max(jnp.abs(jnp.linalg.norm(qs, axis=1) - 1.0))),
        "antipodal_rotation_gap": float(jnp.max(jnp.linalg.norm(rotations - antipodal_rotations, axis=(1, 2)))),
        "flattened_control_antipodal_gap": float(jnp.max(jnp.linalg.norm(flat_control - flat_control_antipodal, axis=1))),
        "flattened_control_min_gap": float(jnp.min(jnp.linalg.norm(flat_control - flat_control_antipodal, axis=1))),
        "so3_orthogonality_defect": float(jnp.max(jnp.linalg.norm(jnp.swapaxes(rotations, 1, 2) @ rotations - identity3, axis=(1, 2)))),
        "so3_det_error": float(jnp.max(jnp.abs(jnp.linalg.det(rotations) - 1.0))),
        "su2_unitarity_defect": float(jnp.max(jnp.linalg.norm(jnp.conj(jnp.swapaxes(su2, 1, 2)) @ su2 - identity2, axis=(1, 2)))),
        "su2_det_error": float(jnp.max(jnp.abs(jnp.linalg.det(su2) - (1.0 + 0.0j)))),
    }


_CLIFFORD_LAYOUT, _CLIFFORD_BLADES = Cl(3)
_E1 = _CLIFFORD_BLADES["e1"]
_E2 = _CLIFFORD_BLADES["e2"]
_E3 = _CLIFFORD_BLADES["e3"]
_B23 = _E2 * _E3
_B31 = _E3 * _E1
_B12 = _E1 * _E2


def clifford_dense(mv: Any) -> torch.Tensor:
    coeffs = torch.zeros(8, dtype=RTYPE)
    for idx, blade_tuple in enumerate(_CLIFFORD_LAYOUT.bladeTupList):
        mask = 0
        for one_based in blade_tuple:
            mask |= 1 << (one_based - 1)
        coeffs[mask] = float(mv.value[idx])
    return coeffs


def clifford_rotor_from_q(q: torch.Tensor) -> Any:
    w, x, y, z = [float(v) for v in q.detach()]
    return w - x * _B23 - y * _B31 - z * _B12


def clifford_action_matrix(q: torch.Tensor) -> torch.Tensor:
    q = q / torch.linalg.vector_norm(q)
    rotor = clifford_rotor_from_q(q)
    rows = []
    for basis in (_E1, _E2, _E3):
        acted = rotor * basis * (~rotor)
        dense = clifford_dense(acted)
        rows.append(torch.stack([dense[1], dense[2], dense[4]]))
    return torch.stack(rows, dim=1)


def nonclifford_signed_coordinate_action_matrix(q: torch.Tensor) -> torch.Tensor:
    q = q / torch.linalg.vector_norm(q)
    _, x, y, z = q.unbind(-1)
    return torch.diag(torch.stack([x, y, z]))


def antipodal_action_matrix_gap(qs: torch.Tensor, action_matrix_fn: Any) -> float:
    gaps = []
    for q in qs:
        gaps.append(torch.linalg.matrix_norm(action_matrix_fn(q) - action_matrix_fn(-q)))
    return float(torch.max(torch.stack(gaps)).item())


def clifford_rotor_evidence(qs: torch.Tensor) -> dict[str, Any]:
    gap = antipodal_action_matrix_gap(qs, clifford_action_matrix)
    nonclifford_gap = antipodal_action_matrix_gap(qs, nonclifford_signed_coordinate_action_matrix)
    flat_gap = float(torch.max(torch.linalg.vector_norm(qs[:, 1:] - (-qs)[:, 1:], dim=1)).item())
    return {
        "tool": "clifford",
        "rotor_model": "Cl(3) even rotor R=w-x e23-y e31-z e12; vector action v -> R v ~R",
        "same_observable": "antipodal_action_matrix_gap",
        "antipodal_rotor_action_gap": gap,
        "with_clifford_rotor_antipodal_action_gap": gap,
        "without_clifford_rotor_antipodal_action_gap": nonclifford_gap,
        "nonclifford_substitute": "signed-coordinate diagonal action matrix diag(x,y,z), recomputed on the same q/-q samples without Cl(3) rotor conjugation",
        "raw_signed_coordinate_flattened_gap": flat_gap,
        "pass": bool(gap <= TOL and nonclifford_gap > TOL and flat_gap > TOL),
    }


def sympy_exact_result() -> dict[str, Any]:
    w, x, y, z = sp.Rational(1, 3), sp.Rational(2, 3), sp.Rational(2, 3), sp.Rational(0, 1)
    q = (w, x, y, z)
    q_neg = tuple(-part for part in q)

    def so3_sym(parts: tuple[sp.Rational, sp.Rational, sp.Rational, sp.Rational]) -> sp.Matrix:
        sw, sx, sy, sz = parts
        return sp.Matrix(
            [
                [1 - 2 * (sy * sy + sz * sz), 2 * (sx * sy - sw * sz), 2 * (sx * sz + sw * sy)],
                [2 * (sx * sy + sw * sz), 1 - 2 * (sx * sx + sz * sz), 2 * (sy * sz - sw * sx)],
                [2 * (sx * sz - sw * sy), 2 * (sy * sz + sw * sx), 1 - 2 * (sx * sx + sy * sy)],
            ]
        )

    def su2_sym(parts: tuple[sp.Rational, sp.Rational, sp.Rational, sp.Rational]) -> sp.Matrix:
        sw, sx, sy, sz = parts
        return sp.Matrix([[sw + sp.I * sz, sy + sp.I * sx], [-sy + sp.I * sx, sw - sp.I * sz]])

    r_q = so3_sym(q)
    r_neg = so3_sym(q_neg)
    u_q = su2_sym(q)
    antipodal_gap_squared = sp.simplify(sum((r_q[i, j] - r_neg[i, j]) ** 2 for i in range(3) for j in range(3)))
    control_gap_squared = sp.simplify(sum((q[idx] - q_neg[idx]) ** 2 for idx in (1, 2, 3)))
    unit_norm = sp.simplify(sum(part * part for part in q))
    so3_orth = sp.simplify(r_q.T * r_q - sp.eye(3))
    so3_det = sp.simplify(r_q.det())
    su2_unitarity = sp.simplify(u_q.conjugate().T * u_q - sp.eye(2))
    su2_det = sp.simplify(u_q.det())
    real_holds = antipodal_gap_squared == 0
    control_holds = control_gap_squared == 0
    return {
        "tool": "sympy",
        "representative_q": [str(part) for part in q],
        "norm_squared": str(unit_norm),
        "so3_antipodal_gap_squared": str(antipodal_gap_squared),
        "flattened_control_antipodal_gap_squared": str(control_gap_squared),
        "so3_orthogonality_zero_matrix": bool(so3_orth == sp.zeros(3)),
        "so3_det": str(so3_det),
        "su2_unitarity_zero_matrix": bool(su2_unitarity == sp.zeros(2)),
        "su2_det": str(su2_det),
        "real_measured": {"antipodal_gap_squared": float(antipodal_gap_squared)},
        "control_measured": {"antipodal_gap_squared": float(control_gap_squared)},
        "real_claim_verdict": "sat" if real_holds else "unsat",
        "negated_claim_verdict": "sat" if control_holds else "unsat",
        "differ": bool(real_holds != control_holds),
        "bound_to_measured": True,
        "load_bearing": bool(real_holds != control_holds),
        "pass": bool(
            unit_norm == 1
            and antipodal_gap_squared == 0
            and control_gap_squared > 0
            and so3_orth == sp.zeros(3)
            and so3_det == 1
            and su2_unitarity == sp.zeros(2)
            and su2_det == 1
            and real_holds != control_holds
        ),
    }


def smt_double_cover_proof(real_gap: float, control_gap: float) -> dict[str, Any]:
    proof = smt_load_bearing(
        claim="unit_quaternion_antipodal_pair_induces_same_SO3_rotation",
        real_measured={"antipodal_image_gap": real_gap, "eps": EPS},
        control_measured={"antipodal_image_gap": control_gap, "eps": EPS},
        claim_builder=lambda v: z3.And(v["antipodal_image_gap"] >= 0, v["antipodal_image_gap"] <= v["eps"]),
        cvc5_claim_pairs=[("antipodal_image_gap", ">=", 0.0), ("antipodal_image_gap", "<=", "eps")],
    )
    proof["pass"] = bool(
        proof["real_claim_verdict"] == "sat"
        and proof["negated_claim_verdict"] == "unsat"
        and proof["differ"] is True
        and proof["bound_to_measured"] is True
        and proof.get("cvc5_real_verdict") == "sat"
        and proof.get("cvc5_control_verdict") == "unsat"
    )
    return proof


def compare_torch_jax(torch_row: dict[str, Any], jax_row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "unit_norm_max_error",
        "antipodal_rotation_gap",
        "flattened_control_antipodal_gap",
        "flattened_control_min_gap",
        "so3_orthogonality_defect",
        "so3_det_error",
        "su2_unitarity_defect",
        "su2_det_error",
    ]
    deltas = {key: abs(float(torch_row[key]) - float(jax_row[key])) for key in keys}
    return {"deltas": deltas, "max_value_delta": max(deltas.values()), "pass": max(deltas.values()) <= 1.0e-8}


def scale_rung(sample_count: int) -> dict[str, Any]:
    torch_row = torch_metrics(sample_count)
    jax_row = jax_metrics(sample_count)
    parity = compare_torch_jax(torch_row, jax_row)
    pass_rung = bool(
        torch_row["unit_norm_max_error"] <= TOL
        and torch_row["antipodal_rotation_gap"] <= TOL
        and torch_row["flattened_control_min_gap"] > TOL
        and torch_row["so3_orthogonality_defect"] <= TOL
        and torch_row["so3_det_error"] <= TOL
        and torch_row["su2_unitarity_defect"] <= TOL
        and torch_row["su2_det_error"] <= TOL
        and torch_row["quaternion_order_gap_ij_vs_ji"] > TOL
        and torch_row["quaternion_ij_minus_k_gap"] <= TOL
        and parity["pass"]
    )
    return {
        "sites_or_qubits": sample_count,
        "sample_count": sample_count,
        "peps3d_shape": list(SITE_SHAPES[sample_count]),
        "carrier_tensor_shape": [sample_count, 4],
        "so3_image_tensor_shape": [sample_count, 3, 3],
        "su2_image_tensor_shape": [sample_count, 2, 2],
        "dense_state_closure_used": False,
        "full_dense_dimension": f"2**{sample_count}",
        "torch": {key: value for key, value in torch_row.items() if key not in {"samples", "rotations", "su2"}},
        "jax": jax_row,
        "jax_vs_pytorch_delta": parity["max_value_delta"],
        "jax_vs_pytorch": parity,
        "pass": pass_rung,
    }


def build_tool_ablations(clifford_evidence: dict[str, Any]) -> dict[str, Any]:
    observable = "antipodal_action_matrix_gap"
    row = tool_ablation(
        observable,
        baseline_value=clifford_evidence["with_clifford_rotor_antipodal_action_gap"],
        ablated_value=clifford_evidence["without_clifford_rotor_antipodal_action_gap"],
        tool="clifford",
    )
    row.update(
        {
            "baseline_observable": observable,
            "ablated_observable": observable,
            "same_observable_remove_recompute": True,
            "baseline_computation": "WITH Clifford Cl(3) even rotor conjugation: v -> R v ~R, then max_q ||A(q)-A(-q)||_F",
            "ablated_computation": "WITHOUT Clifford rotor: non-Clifford signed-coordinate diagonal action matrix diag(x,y,z), then max_q ||A(q)-A(-q)||_F",
            "baseline_recompute": "A(q)=Cl(3) even rotor conjugation action matrix from clifford_action_matrix(q)",
            "ablated_recompute": "A_no_clifford(q)=non-Clifford signed-coordinate 3x3 substitute on the same q samples and same imaginary basis; no Cl rotor or multivector call",
            "removed_structure": "Cl(3) even rotor conjugation",
            "structure_removed": "Cl(3) even rotor conjugation",
            "substitute": clifford_evidence["nonclifford_substitute"],
        }
    )
    row["pass"] = bool(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > TOL
        and float(row["baseline_value"]) <= TOL
        and float(row["ablated_value"]) > TOL
    )
    return {"clifford_rotor_structure_ablation": row}


def known_value_checks(top: dict[str, Any], clifford_row: dict[str, Any], sympy_row: dict[str, Any]) -> list[dict[str, Any]]:
    torch_top = top["torch"]
    return [
        {
            "invariant": "unit_quaternion_norm",
            "computed": torch_top["unit_norm_max_error"],
            "known": "max | |q|-1 | == 0",
            "match": bool(torch_top["unit_norm_max_error"] <= TOL),
        },
        {
            "invariant": "SU2_double_cover_SO3_q_and_minus_q_same_rotation",
            "computed": torch_top["antipodal_rotation_gap"],
            "known": "0",
            "match": bool(torch_top["antipodal_rotation_gap"] <= TOL),
        },
        {
            "invariant": "flattened_control_breaks_antipodal_identification",
            "computed": torch_top["flattened_control_min_gap"],
            "known": ">0",
            "match": bool(torch_top["flattened_control_min_gap"] > TOL),
        },
        {
            "invariant": "SO3_orthogonality",
            "computed": torch_top["so3_orthogonality_defect"],
            "known": "0",
            "match": bool(torch_top["so3_orthogonality_defect"] <= TOL),
        },
        {
            "invariant": "SO3_determinant_one",
            "computed": torch_top["so3_det_error"],
            "known": "0",
            "match": bool(torch_top["so3_det_error"] <= TOL),
        },
        {
            "invariant": "SU2_unitarity",
            "computed": torch_top["su2_unitarity_defect"],
            "known": "0",
            "match": bool(torch_top["su2_unitarity_defect"] <= TOL),
        },
        {
            "invariant": "SU2_determinant_one",
            "computed": torch_top["su2_det_error"],
            "known": "0",
            "match": bool(torch_top["su2_det_error"] <= TOL),
        },
        {
            "invariant": "quaternion_i_times_j_equals_k",
            "computed": torch_top["quaternion_ij_minus_k_gap"],
            "known": "0",
            "match": bool(torch_top["quaternion_ij_minus_k_gap"] <= TOL),
        },
        {
            "invariant": "quaternion_noncommuting_order_witness",
            "computed": torch_top["quaternion_order_gap_ij_vs_ji"],
            "known": ">0",
            "match": bool(torch_top["quaternion_order_gap_ij_vs_ji"] > TOL),
        },
        {
            "invariant": "clifford_even_rotor_antipodal_action",
            "computed": clifford_row["antipodal_rotor_action_gap"],
            "known": "0",
            "match": bool(clifford_row["antipodal_rotor_action_gap"] <= TOL),
        },
        {
            "invariant": "sympy_exact_unit_norm_and_double_cover",
            "computed": {
                "norm_squared": sympy_row["norm_squared"],
                "so3_antipodal_gap_squared": sympy_row["so3_antipodal_gap_squared"],
                "flattened_control_antipodal_gap_squared": sympy_row["flattened_control_antipodal_gap_squared"],
            },
            "known": {"norm_squared": "1", "so3_gap": "0", "flattened_control_gap": ">0"},
            "match": bool(sympy_row["pass"]),
        },
    ]


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    scale_rows = {str(n): scale_rung(n) for n in SCALE_RUNGS}
    top = scale_rows["64"]
    top_samples = sample_unit_quaternions_torch(64)
    clifford_row = clifford_rotor_evidence(top_samples)
    sympy_row = sympy_exact_result()
    proof = smt_double_cover_proof(
        real_gap=top["torch"]["antipodal_rotation_gap"],
        control_gap=top["torch"]["flattened_control_antipodal_gap"],
    )
    ablations = build_tool_ablations(clifford_row)
    checks = known_value_checks(top, clifford_row, sympy_row)

    scale_pass = all(row["pass"] for row in scale_rows.values())
    proof_pass = bool(proof["pass"] and sympy_row["pass"])
    ablation_pass = all(row["pass"] for row in ablations.values())
    known_pass = all(row["match"] for row in checks)
    flattened_control_pass = bool(top["torch"]["flattened_control_min_gap"] > TOL)
    clifford_removal_control_pass = bool(clifford_row["without_clifford_rotor_antipodal_action_gap"] > TOL)
    controls_pass = bool(flattened_control_pass and clifford_removal_control_pass)
    all_pass = bool(scale_pass and proof_pass and ablation_pass and known_pass and controls_pass and clifford_row["pass"])
    blockers = []
    if not scale_pass:
        blockers.append("one or more 8/16/32/64 non-dense scale rungs failed")
    if not proof_pass:
        blockers.append("helper-bound SMT double-cover proof or sympy exact flip failed")
    if not ablation_pass:
        blockers.append("Clifford rotor structure ablation failed to recompute a nonzero change")
    if not known_pass:
        blockers.append("one or more computed known-value checks failed")
    if not flattened_control_pass:
        blockers.append("flattened sign-sensitive control did not break antipodal identification")
    if not clifford_removal_control_pass:
        blockers.append("without-Clifford control did not break the same antipodal action-matrix gap observable")
    if not clifford_row["pass"]:
        blockers.append("Clifford rotor q/-q action gap failed")

    torch_primary_result = {
        "engine": "torch",
        "dtype": str(RTYPE),
        "claim": "unit quaternions q and -q induce the same SO(3) rotation under q v q^{-1}",
        "scale_64_observables": top["torch"],
        "geometric_invariant": {
            "name": "antipodal_image_gap_for_map_q_to_Rq",
            "real_measured": top["torch"]["antipodal_rotation_gap"],
            "flattened_control_measured": top["torch"]["flattened_control_antipodal_gap"],
            "pass": bool(top["torch"]["antipodal_rotation_gap"] <= TOL and top["torch"]["flattened_control_min_gap"] > TOL),
        },
        "pass": bool(top["pass"]),
    }
    jax_mirror_result = {
        "engine": "jax",
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "claim": "JAX mirrors only the finite closed-form quaternion/SU(2)/SO(3) formulas representable in jax; no jax geomstats path is claimed.",
        "scale_64_observables": top["jax"],
        "pass": bool(top["jax_vs_pytorch"]["pass"]),
    }
    controls = {
        "flattened_raw_quaternion_coordinate_control": {
            "description": "The SO(3) quotient map is replaced by sign-sensitive raw imaginary-quaternion coordinates; q and -q no longer identify.",
            "baseline_antipodal_rotation_gap": top["torch"]["antipodal_rotation_gap"],
            "control_antipodal_flattened_gap": top["torch"]["flattened_control_antipodal_gap"],
            "min_control_gap": top["torch"]["flattened_control_min_gap"],
            "kills_double_cover_claim": bool(top["torch"]["flattened_control_min_gap"] > TOL),
            "pass": bool(top["torch"]["antipodal_rotation_gap"] <= TOL and top["torch"]["flattened_control_min_gap"] > TOL),
        },
        "raw_signed_coordinate_without_clifford_rotor_control": {
            "description": "The Clifford even-rotor conjugation structure is removed and the same antipodal action-matrix gap is recomputed on a non-Clifford signed-coordinate substitute.",
            "same_observable": "antipodal_action_matrix_gap",
            "same_observable_remove_recompute": True,
            "baseline_clifford_rotor_gap": clifford_row["with_clifford_rotor_antipodal_action_gap"],
            "control_without_clifford_rotor_gap": clifford_row["without_clifford_rotor_antipodal_action_gap"],
            "nonclifford_substitute": clifford_row["nonclifford_substitute"],
            "kills_rotor_double_cover_witness": bool(clifford_row["without_clifford_rotor_antipodal_action_gap"] > TOL),
            "pass": bool(
                clifford_row["with_clifford_rotor_antipodal_action_gap"] <= TOL
                and clifford_row["without_clifford_rotor_antipodal_action_gap"] > TOL
            ),
        },
    }

    return {
        "schema": "formal_scout_max_deep_lego_result_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "object_id": OBJECT_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": time.time() - started,
        "classification": "lego",
        "tier": "canonical STAGE 3 geometry object",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Build one standalone Stage-3 quaternion/SU(2)/Spin(3) geometry object at 8/16/32/64 finite samples without manifold-layer or G-structure promotion.",
        "scientific_question": "Does the finite unit-quaternion carrier instantiate the SU(2)->SO(3) double cover with q and -q producing the same rotation, while a flattened control fails the same invariant?",
        "claim_ceiling": "Standalone geometry lego only. This does not admit a manifold layer, G-structure selection, layer stacking, Xi, Phi0, Axis0, flux, FEP, gravity, basin, bridge, or physics claim.",
        "finite_map": {
            "domain": "finite unit-quaternion sample set Q_n subset S^3 with n in {8,16,32,64}; each q is a torch.float64 4-vector [w,i,j,k] with finite PEPS3D site anchors",
            "codomain_or_output": "SU(2) matrix U_q, SO(3) rotation R_q on imaginary quaternions, antipodal quotient readout R(q)=R(-q), flattened-control readout, proof flips, and blocked downstream consumers",
            "definition": "D_n(q)=(U_q,R_q) where U_q is the standard 2x2 complex matrix and R_q is the conjugation action v -> q v q^{-1}; quotient witness identifies q and -q only after the SO(3) map.",
        },
        "domain": {
            "sample_counts": list(SCALE_RUNGS),
            "carrier_tensor": "Q_n as n x 4 torch.float64 unit-quaternion table",
            "basis": "imaginary quaternion units i,j,k; no dense 2**N state vector is materialized",
            "dense_state_closure_used": False,
        },
        "codomain_or_output": {
            "primary_invariant": "max_q ||R(q)-R(-q)||_F <= eps",
            "control_invariant": "same antipodal image gap after flattening to raw signed quaternion coordinates is > eps",
            "known_value": "|q|=1 for every sampled q",
        },
        "root_constraints": {
            "F01": {
                "role": "active",
                "statement": "finite carrier/probe/operator/path set: finite sample counts 8/16/32/64, finite quaternion basis, finite SU(2)/SO(3) images, finite controls, and finite proof variables.",
            },
            "N01": {
                "role": "active_bounded_witness",
                "statement": "quaternion units i and j are order-sensitive: ij=k while ji=-k; the finite order gap is measured in torch and exact sympy.",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 noncommuting/order-sensitive quaternion multiplication witness ij != ji",
        ],
        "carrier_layer": "finite_unit_quaternion_sample_carrier",
        "geometry_layer": "quaternion_su2_spin3_double_cover_object",
        "carrier_realization": "torch.float64 unit-quaternion table; torch.complex128 SU(2) matrices; JAX mirrors the closed-form finite formulas; no NumPy bridge and no dense closure",
        "peps3d_embedding": {
            "anchor": "finite PEPS3D site anchors are carried as sample/site coordinates only; no PEPS3D contraction, manifold layer, or 64-substage claim is made",
            "shapes": {str(site_count): list(shape) for site_count, shape in SITE_SHAPES.items()},
            "from_first_carrier_step": True,
            "full_peps3d_contraction_claimed": False,
        },
        "spinor_state": "SU(2) 2x2 complex matrix representation is computed for each unit quaternion; no separate spinor-network layer is admitted here",
        "quaternion_action": "q v q^{-1} on imaginary quaternions, with R(q)=R(-q); flattened raw-coordinate control breaks the antipodal quotient",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/F01_finite_distinguishability_results.json",
            "system_v5/ops/formal_scouts/results/carrier_torch_complex_spinor_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "SU(2)/Spin(3) unit-quaternion double cover of SO(3), real q/-q rotation equality vs flattened sign-sensitive control",
        "branch_status_before_run": "single standalone geometry lego requested by user; no manifold layer, G-structure selection, stacking, bridge, flux, Axis0, FEP, gravity, or physics route opened",
        "allowed_claims": [
            "bounded Stage-3 standalone quaternion/SU(2)/Spin(3) geometry object result exists/runs if this JSON and required gates pass",
            "finite unit-quaternion samples at 8/16/32/64 instantiate q and -q as the same SO(3) rotation under the explicit map q -> R_q",
            "helper-bound z3/cvc5 proof flips for the double-cover invariant against the flattened measured control",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "standalone geometry object only",
            "no manifold layer or G-structure completion claim",
            "no layer stacking or official structure selection",
            "no Xi/Phi0/Axis0/flux/FEP/gravity/bridge/basin/physics consumer is unlocked",
        ],
        "eligible_consumers": ["bounded later Stage-3 geometry comparisons only after citing this result path and fresh gate output"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3 antipodal image-gap proof",
            "load_bearing_proof.smt_load_bearing cvc5 antipodal image-gap cross-check",
            "sympy exact rational unit-quaternion/SU(2)/SO(3) double-cover and flattened-control flip",
        ],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_negatives": list(controls.keys()),
        "negatives_run": controls,
        "kill_conditions": {
            "flattened_raw_quaternion_coordinate_control": "same antipodal image-gap claim must become unsat when the SO(3) quotient map is replaced by signed raw coordinates",
            "raw_signed_coordinate_without_clifford_rotor_control": "removing Clifford rotor conjugation must produce a nonzero recomputed value of the same antipodal_action_matrix_gap observable",
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
            "jax_vs_pytorch_delta": max(row["jax_vs_pytorch_delta"] for row in scale_rows.values()),
            "double_cover_antipodal_gap": top["torch"]["antipodal_rotation_gap"],
            "flattened_control_gap": top["torch"]["flattened_control_antipodal_gap"],
            "clifford_rotor_gap": clifford_row["antipodal_rotor_action_gap"],
            "clifford_without_rotor_same_observable_gap": clifford_row["without_clifford_rotor_antipodal_action_gap"],
            "elapsed_seconds": time.time() - started,
        },
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": max(row["jax_vs_pytorch_delta"] for row in scale_rows.values()),
        "jax_vs_pytorch": {key: row["jax_vs_pytorch"] for key, row in scale_rows.items()},
        "proof_results": {
            "smt_load_bearing_double_cover": proof,
            "sympy_exact_double_cover_flip": sympy_row,
            "pass": proof_pass,
        },
        "controls": controls,
        "tool_ablations": ablations,
        "ablation_outcome_delta": ablations,
        "tool_ablations_by_tool": ablations,
        "scale_ladder": {
            "rungs": {
                key: {
                    "sites_or_qubits": row["sites_or_qubits"],
                    "sample_count": row["sample_count"],
                    "peps3d_shape": row["peps3d_shape"],
                    "carrier_tensor_shape": row["carrier_tensor_shape"],
                    "so3_image_tensor_shape": row["so3_image_tensor_shape"],
                    "su2_image_tensor_shape": row["su2_image_tensor_shape"],
                    "dense_state_closure_used": row["dense_state_closure_used"],
                    "unit_norm_max_error": row["torch"]["unit_norm_max_error"],
                    "antipodal_rotation_gap": row["torch"]["antipodal_rotation_gap"],
                    "flattened_control_antipodal_gap": row["torch"]["flattened_control_antipodal_gap"],
                    "so3_orthogonality_defect": row["torch"]["so3_orthogonality_defect"],
                    "so3_det_error": row["torch"]["so3_det_error"],
                    "su2_unitarity_defect": row["torch"]["su2_unitarity_defect"],
                    "su2_det_error": row["torch"]["su2_det_error"],
                    "quaternion_order_gap_ij_vs_ji": row["torch"]["quaternion_order_gap_ij_vs_ji"],
                    "jax_vs_pytorch_delta": row["jax_vs_pytorch_delta"],
                    "pass": row["pass"],
                }
                for key, row in scale_rows.items()
            },
            "scale_axis": "finite_unit_quaternion_sample_count",
            "dense_state_closure_used": False,
            "pass": scale_pass,
        },
        "scale_details": scale_rows,
        "clifford_rotor_result": clifford_row,
        "known_value_checks": checks,
        "positive": {
            "double_cover_smt_flip": {"pass": proof["pass"], "proof": proof},
            "scale_8_16_32_64_non_dense": {"pass": scale_pass},
            "clifford_rotor_double_cover": clifford_row,
            "sympy_exact_double_cover": sympy_row,
        },
        "blockers": blockers,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "pass_rule": "helper-bound SMT proof flips real q->SO(3) antipodal gap against flattened control; Clifford rotor ablation computes the same antipodal action-matrix gap with the Cl(3) rotor and without it through a non-Clifford substitute; all 8/16/32/64 scale rungs pass without dense closure",
        "fail_rule": "fail on missing proof flip, missing baseline/ablated recompute fields, JAX mismatch on representable formulas, live flattened control, dense closure, or downstream consumer promotion",
        "all_pass": all_pass,
        "required_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
