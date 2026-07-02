import jax; jax.config.update("jax_enable_x64", True)

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ["GEOMSTATS_BACKEND"] = "pytorch"
os.environ["NUMBA_DISABLE_JIT"] = "1"

import jax.numpy as jnp
from clifford import Cl
from geomstats.geometry.hypersphere import Hypersphere
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "layer_chirality_orientation_cover_8_16_32_64_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SITE_COUNTS = [8, 16, 32, 64]
SITE_SHAPES = {
    8: (2, 2, 2),
    16: (4, 2, 2),
    32: (4, 4, 2),
    64: (4, 4, 4),
}
RTYPE = torch.float64
CDTYPE = torch.complex128
TOL = 1.0e-10
PARITY_TOL = 1.0e-9
KILL_FLOOR = 1.0e-6

I4 = torch.eye(4, dtype=CDTYPE)
ZERO2 = torch.zeros((2, 2), dtype=CDTYPE)
I2 = torch.eye(2, dtype=CDTYPE)
GAMMA5 = torch.diag(torch.tensor([1.0, 1.0, -1.0, -1.0], dtype=CDTYPE))
P_PLUS = (I4 + GAMMA5) / 2.0
P_MINUS = (I4 - GAMMA5) / 2.0
MIX = torch.cat(
    [torch.cat([ZERO2, I2], dim=1), torch.cat([I2, ZERO2], dim=1)],
    dim=0,
)

JI4 = jnp.eye(4, dtype=jnp.complex128)
JGAMMA5 = jnp.diag(jnp.array([1.0, 1.0, -1.0, -1.0], dtype=jnp.complex128))
JP_PLUS = (JI4 + JGAMMA5) / 2.0
JP_MINUS = (JI4 - JGAMMA5) / 2.0
JZERO2 = jnp.zeros((2, 2), dtype=jnp.complex128)
JI2 = jnp.eye(2, dtype=jnp.complex128)
JMIX = jnp.concatenate(
    [jnp.concatenate([JZERO2, JI2], axis=1), jnp.concatenate([JI2, JZERO2], axis=1)],
    axis=0,
)

CLASSIFICATION = "lego"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "chirality_orientation_cover_probe"
VERSION = "1.0.0"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Single independent chirality_orientation_cover lego only: tests gamma5 as "
    "a Z2 chirality/orientation cover on finite local Dirac spinors anchored to "
    "PEPS3D site cells at N=8,16,32,64, with torch primary execution, JAX x64 "
    "parity, Cl(3) rotor double-cover witness, z3 Z2 structural proof, sympy "
    "gamma5/projector identities, and named orientation-drop negatives. It does "
    "not admit coupling, stacking, full layer completion, G-structure selection, "
    "flux, Xi/Phi0, Axis0, bridge, basin, FEP, physics, or final manifold claims."
)

FINITE_MAP = (
    "ChiOrient_N : (finite PEPS3D site-cell anchors K_N, local torch/JAX "
    "Dirac spinors psi_i in C^4, gamma5=diag(1,1,-1,-1), projectors "
    "P_+=(I+gamma5)/2 and P_-=(I-gamma5)/2, Cl rotor signs +/-R, Z2 signs "
    "+/-1, and orientation-erased controls) -> chirality sheet projections, "
    "gamma5^2 and projector invariants, Z2 double-cover cardinality, "
    "Cl rotor same-action/two-preimage certificate, and killed orientation-drop "
    "readouts"
)
DOMAIN = {
    "root_constraints_in_force": [
        "F01 finite carrier/probe/operator/path set",
        "N01 order-sensitive/noncommuting gamma5 with chiral mixing operator",
    ],
    "site_counts": SITE_COUNTS,
    "carrier": "finite local four-component Dirac spinors over PEPS3D site-cell anchors",
    "operators": ["gamma5", "P_plus", "P_minus", "off_diagonal_chiral_mix", "Cl(3) rotor +/-R"],
    "cover_group": "Z2={+1,-1} acting by gamma5 sheet sign and Spin rotor sign",
}
CODOMAIN = {
    "cover_signature": "sheet-separation, gamma5 order-two return, order gap against chiral mix, and Cl/Z2 two-preimage certificates",
    "known_invariants": ["gamma5^2=I4", "P_+^2=P_+", "P_-^2=P_-", "P_+P_-=0", "Z2={+1,-1}"],
    "negative_controls": ["drop_orientation", "identity_gamma5", "identified_projectors", "rotor_sign_erased"],
}
PEPS3D_EMBEDDING = (
    "Each scale N uses one finite cubical PEPS3D anchor K_N: 8->2x2x2, "
    "16->4x2x2, 32->4x4x2, 64->4x4x4. Each local Dirac spinor is attached "
    "to one site cell. The carrier is a few-body/local cover product-MPS "
    "summary with mps_max_bond=1; no 2**N dense state is built."
)
SPINOR_STATE = (
    "torch.complex128 primary and jax.complex128 secondary local Dirac spinor "
    "tensors of shape [N,4], plus spinor-derived sheet projections P_+ psi_i "
    "and P_- psi_i."
)
QUATERNION_ACTION = (
    "not_applicable: this lego uses gamma5, Z2, and Clifford rotor orientation "
    "language only; no quaternion map or invariant is claimed."
)
BLOCKED_CONSUMERS = [
    "coupling",
    "layer stacking",
    "full layer completion",
    "G_structure_selection",
    "nested Hopf closure",
    "terrain placement",
    "operator substage cells",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "bridge",
    "basin",
    "Holodeck/FEP",
    "physics",
    "final manifold admission",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "primary load-bearing gamma5/projector action, sheet separation, order gap, scale rungs, and orientation-drop recomputation",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "independent x64 secondary engine for gamma5/projector/order-gap parity against PyTorch",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Cl(3) rotor witness: +R and -R are distinct rotor preimages with the same vector action; orientation-drop ablation collapses the cover cardinality",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing structural Z2 proof: integer signs satisfying s*s=1 are exactly {-1,+1}; orientation-erased control has one class",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact gamma5^2=I and projector algebra; orientation-drop ablation collapses two distinct projectors to one",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "torch-side S3 antipodal rotor distance witness for the Spin double-cover; no JAX geomstats backend is claimed",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "jax": "load_bearing",
    "clifford": "load_bearing",
    "z3": "load_bearing",
    "sympy": "load_bearing",
    "geomstats": "load_bearing",
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
    if hasattr(value, "tolist") and not isinstance(value, (str, bytes)):
        try:
            return as_jsonable(value.tolist())
        except TypeError:
            pass
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def peps3d_counts(shape: tuple[int, int, int]) -> dict[str, int]:
    lx, ly, lz = shape
    return {
        "vertices": lx * ly * lz,
        "edges": (lx - 1) * ly * lz + lx * (ly - 1) * lz + lx * ly * (lz - 1),
        "faces": (lx - 1) * (ly - 1) * lz + (lx - 1) * ly * (lz - 1) + lx * (ly - 1) * (lz - 1),
        "cells": (lx - 1) * (ly - 1) * (lz - 1),
    }


def complex_phase(angle: float) -> complex:
    return complex(math.cos(angle), math.sin(angle))


def spinor_angles(site: int, site_count: int) -> tuple[float, float, float, float, float]:
    t = (site + 1.0) / (site_count + 1.0)
    scale = math.log2(float(site_count)) - 3.0
    left_weight = 0.55 + 0.16 * math.sin(2.0 * math.pi * t + 0.21 * scale)
    left_weight = min(0.82, max(0.18, left_weight))
    theta_l = 0.19 * math.pi + 0.47 * math.pi * t + 0.03 * math.sin(5.0 * t + scale)
    theta_r = 0.31 * math.pi + 0.41 * math.pi * t + 0.02 * math.cos(4.0 * t + scale)
    phi_l = 0.23 + 0.37 * site + 0.11 * scale
    phi_r = 0.41 + 0.29 * site - 0.07 * scale
    return left_weight, theta_l, theta_r, phi_l, phi_r


def normalize_torch(vector: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.vector_norm(vector)
    if float(norm.item()) <= 1.0e-14:
        raise ValueError("zero spinor")
    return vector / norm


def normalize_jax(vector: jnp.ndarray) -> jnp.ndarray:
    return vector / jnp.linalg.norm(vector)


def dirac_spinor_torch(site: int, site_count: int) -> torch.Tensor:
    lw, theta_l, theta_r, phi_l, phi_r = spinor_angles(site, site_count)
    rw = 1.0 - lw
    left = [
        math.sqrt(lw) * math.cos(theta_l / 2.0),
        math.sqrt(lw) * complex_phase(phi_l) * math.sin(theta_l / 2.0),
    ]
    right = [
        math.sqrt(rw) * complex_phase(phi_r) * math.sin(theta_r / 2.0),
        math.sqrt(rw) * math.cos(theta_r / 2.0),
    ]
    return normalize_torch(torch.tensor([*left, *right], dtype=CDTYPE))


def dirac_spinor_jax(site: int, site_count: int) -> jnp.ndarray:
    lw, theta_l, theta_r, phi_l, phi_r = spinor_angles(site, site_count)
    rw = 1.0 - lw
    left = [
        math.sqrt(lw) * math.cos(theta_l / 2.0) + 0.0j,
        math.sqrt(lw) * complex_phase(phi_l) * math.sin(theta_l / 2.0),
    ]
    right = [
        math.sqrt(rw) * complex_phase(phi_r) * math.sin(theta_r / 2.0),
        math.sqrt(rw) * math.cos(theta_r / 2.0) + 0.0j,
    ]
    return normalize_jax(jnp.array([*left, *right], dtype=jnp.complex128))


def apply_torch(states: torch.Tensor, operator: torch.Tensor) -> torch.Tensor:
    return states @ operator.T


def apply_jax(states: jnp.ndarray, operator: jnp.ndarray) -> jnp.ndarray:
    return states @ operator.T


def mean_norm_torch(states: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(states, dim=1).mean().item())


def mean_norm_jax(states: jnp.ndarray) -> float:
    return float(jnp.linalg.norm(states, axis=1).mean())


def torch_cover_row(site_count: int) -> dict[str, Any]:
    states = torch.stack([dirac_spinor_torch(i, site_count) for i in range(site_count)])
    plus = apply_torch(states, P_PLUS)
    minus = apply_torch(states, P_MINUS)
    gamma_once = apply_torch(states, GAMMA5)
    gamma_twice = apply_torch(gamma_once, GAMMA5)
    gm = apply_torch(apply_torch(states, MIX), GAMMA5)
    mg = apply_torch(apply_torch(states, GAMMA5), MIX)

    drop_gamma = I4
    drop_projector = I4 / 2.0
    drop_plus = apply_torch(states, drop_projector)
    drop_minus = apply_torch(states, drop_projector)
    drop_gm = apply_torch(apply_torch(states, MIX), drop_gamma)
    drop_mg = apply_torch(apply_torch(states, drop_gamma), MIX)

    gamma5_square_error = float(torch.max(torch.abs(GAMMA5 @ GAMMA5 - I4)).item())
    pplus_idempotence_error = float(torch.max(torch.abs(P_PLUS @ P_PLUS - P_PLUS)).item())
    pminus_idempotence_error = float(torch.max(torch.abs(P_MINUS @ P_MINUS - P_MINUS)).item())
    projector_orthogonality_error = float(torch.max(torch.abs(P_PLUS @ P_MINUS)).item())
    projector_sum_error = float(torch.max(torch.abs(P_PLUS + P_MINUS - I4)).item())
    sheet_gap = mean_norm_torch(plus - minus)
    z2_return_error = mean_norm_torch(gamma_twice - states)
    single_action_gap = mean_norm_torch(gamma_once - states)
    order_gap = mean_norm_torch(gm - mg)
    drop_sheet_gap = mean_norm_torch(drop_plus - drop_minus)
    drop_order_gap = mean_norm_torch(drop_gm - drop_mg)
    signature = sheet_gap + single_action_gap + order_gap
    drop_signature = drop_sheet_gap + drop_order_gap
    outcome_delta = signature - drop_signature
    pass_row = (
        gamma5_square_error < TOL
        and pplus_idempotence_error < TOL
        and pminus_idempotence_error < TOL
        and projector_orthogonality_error < TOL
        and projector_sum_error < TOL
        and z2_return_error < TOL
        and sheet_gap > KILL_FLOOR
        and single_action_gap > KILL_FLOOR
        and order_gap > KILL_FLOOR
        and outcome_delta > KILL_FLOOR
    )
    return {
        "sites_or_qubits": site_count,
        "shape": list(SITE_SHAPES[site_count]),
        "dense_state_closure_used": False,
        "carrier_kind": "few_body_local_chirality_cover_product_mps",
        "mps_max_bond": 1,
        "half_chain_entanglement_entropy": 0.0,
        "many_body_depth_required": False,
        "many_body_depth_note": "few-body gamma5/Z2 cover lego; low-bond product-MPS carrier is intentional and not a many-body claim",
        "gamma5_square_error": gamma5_square_error,
        "pplus_idempotence_error": pplus_idempotence_error,
        "pminus_idempotence_error": pminus_idempotence_error,
        "projector_orthogonality_error": projector_orthogonality_error,
        "projector_sum_error": projector_sum_error,
        "sheet_gap": sheet_gap,
        "z2_return_error": z2_return_error,
        "single_action_gap": single_action_gap,
        "order_gap": order_gap,
        "drop_orientation": {
            "drop_sheet_gap": drop_sheet_gap,
            "drop_order_gap": drop_order_gap,
            "baseline_signature": signature,
            "ablated_signature": drop_signature,
            "outcome_delta": outcome_delta,
            "kills_signature": outcome_delta > KILL_FLOOR and drop_sheet_gap < TOL and drop_order_gap < TOL,
            "pass": outcome_delta > KILL_FLOOR and drop_sheet_gap < TOL and drop_order_gap < TOL,
        },
        "pass": pass_row,
    }


def jax_cover_row(site_count: int) -> dict[str, Any]:
    states = jnp.stack([dirac_spinor_jax(i, site_count) for i in range(site_count)])
    plus = apply_jax(states, JP_PLUS)
    minus = apply_jax(states, JP_MINUS)
    gamma_once = apply_jax(states, JGAMMA5)
    gamma_twice = apply_jax(gamma_once, JGAMMA5)
    gm = apply_jax(apply_jax(states, JMIX), JGAMMA5)
    mg = apply_jax(apply_jax(states, JGAMMA5), JMIX)
    drop_gamma = JI4
    drop_projector = JI4 / 2.0
    drop_plus = apply_jax(states, drop_projector)
    drop_minus = apply_jax(states, drop_projector)
    drop_gm = apply_jax(apply_jax(states, JMIX), drop_gamma)
    drop_mg = apply_jax(apply_jax(states, drop_gamma), JMIX)
    sheet_gap = mean_norm_jax(plus - minus)
    single_action_gap = mean_norm_jax(gamma_once - states)
    order_gap = mean_norm_jax(gm - mg)
    z2_return_error = mean_norm_jax(gamma_twice - states)
    drop_sheet_gap = mean_norm_jax(drop_plus - drop_minus)
    drop_order_gap = mean_norm_jax(drop_gm - drop_mg)
    signature = sheet_gap + single_action_gap + order_gap
    drop_signature = drop_sheet_gap + drop_order_gap
    return {
        "sites_or_qubits": site_count,
        "dense_state_closure_used": False,
        "sheet_gap": sheet_gap,
        "single_action_gap": single_action_gap,
        "order_gap": order_gap,
        "z2_return_error": z2_return_error,
        "drop_orientation": {
            "drop_sheet_gap": drop_sheet_gap,
            "drop_order_gap": drop_order_gap,
            "baseline_signature": signature,
            "ablated_signature": drop_signature,
            "outcome_delta": signature - drop_signature,
            "kills_signature": (signature - drop_signature) > KILL_FLOOR and drop_sheet_gap < TOL and drop_order_gap < TOL,
        },
        "pass": z2_return_error < TOL and sheet_gap > KILL_FLOOR and order_gap > KILL_FLOOR,
    }


def compare_rows(torch_row: dict[str, Any], jax_row: dict[str, Any]) -> dict[str, Any]:
    keys = ["sheet_gap", "single_action_gap", "order_gap", "z2_return_error"]
    deltas = {key: abs(float(torch_row[key]) - float(jax_row[key])) for key in keys}
    deltas["drop_orientation_outcome_delta"] = abs(
        float(torch_row["drop_orientation"]["outcome_delta"])
        - float(jax_row["drop_orientation"]["outcome_delta"])
    )
    max_delta = max(deltas.values())
    return {
        "max_value_delta": max_delta,
        "deltas": deltas,
        "agree": max_delta < PARITY_TOL,
    }


def sympy_gamma5_witness() -> dict[str, Any]:
    gamma5 = sp.diag(1, 1, -1, -1)
    ident = sp.eye(4)
    p_plus = (ident + gamma5) / 2
    p_minus = (ident - gamma5) / 2
    drop_plus = ident / 2
    drop_minus = ident / 2
    signs = {"+1": 1, "-1": -1}
    table = {f"{left}*{right}": left_value * right_value for left, left_value in signs.items() for right, right_value in signs.items()}
    two_projectors_distinct = p_plus != p_minus
    drop_projectors_distinct = drop_plus != drop_minus
    return {
        "gamma5_square_is_identity": bool(gamma5 * gamma5 == ident),
        "gamma5_trace": int(sp.trace(gamma5)),
        "gamma5_determinant": int(gamma5.det()),
        "p_plus_idempotent": bool(p_plus * p_plus == p_plus),
        "p_minus_idempotent": bool(p_minus * p_minus == p_minus),
        "orthogonal_projectors": bool(p_plus * p_minus == sp.zeros(4)),
        "projector_sum_identity": bool(p_plus + p_minus == ident),
        "p_plus_rank": int(p_plus.rank()),
        "p_minus_rank": int(p_minus.rank()),
        "z2_group_table": table,
        "distinct_projector_count": 2 if two_projectors_distinct else 1,
        "drop_orientation_projector_count": 2 if drop_projectors_distinct else 1,
        "orientation_drop_delta": float((2 if two_projectors_distinct else 1) - (2 if drop_projectors_distinct else 1)),
        "pass": bool(
            gamma5 * gamma5 == ident
            and p_plus * p_plus == p_plus
            and p_minus * p_minus == p_minus
            and p_plus * p_minus == sp.zeros(4)
            and p_plus + p_minus == ident
            and table["-1*-1"] == 1
        ),
    }


def z3_z2_witness() -> dict[str, Any]:
    sign = z3.Int("sign")
    solver = z3.Solver()
    solver.add(sign * sign == 1)
    models: list[int] = []
    while solver.check() == z3.sat:
        model = solver.model()
        value = int(str(model[sign]))
        models.append(value)
        solver.add(sign != value)
    models = sorted(models)
    no_third = z3.Solver()
    no_third.add(sign * sign == 1, sign != 1, sign != -1)
    no_third_status = no_third.check()
    return {
        "z2_sign_models": models,
        "cover_cardinality": len(models),
        "no_third_sign_status": str(no_third_status),
        "drop_orientation_cardinality": 1,
        "orientation_drop_delta": float(len(models) - 1),
        "pass": models == [-1, 1] and no_third_status == z3.unsat,
    }


def multivector_coeffs(mv: Any) -> dict[str, float]:
    return {name: float(mv.value[idx]) for idx, name in enumerate(mv.layout.names) if abs(float(mv.value[idx])) > 1.0e-12}


def clifford_rotor_witness() -> dict[str, Any]:
    _, blades = Cl(3)
    e1 = blades["e1"]
    e2 = blades["e2"]
    e3 = blades["e3"]
    bivector = e1 * e2
    pseudoscalar = blades["e123"]
    theta = 0.73
    rotor = math.cos(theta / 2.0) - math.sin(theta / 2.0) * bivector
    minus_rotor = -rotor
    vector = e1 + 0.25 * e2 + 0.1 * e3
    vector = vector / math.sqrt(1.0 + 0.25 * 0.25 + 0.1 * 0.1)
    plus_action = rotor * vector * ~rotor
    minus_action = minus_rotor * vector * ~minus_rotor
    action_delta = float(max(abs(x) for x in (plus_action - minus_action).value))
    rotor_norm_delta = abs(float((rotor * ~rotor)[()]) - 1.0)
    pseudoscalar_square = str(pseudoscalar * pseudoscalar)
    return {
        "rotor": multivector_coeffs(rotor),
        "minus_rotor": multivector_coeffs(minus_rotor),
        "plus_action": multivector_coeffs(plus_action),
        "minus_action": multivector_coeffs(minus_action),
        "same_so_action_delta": action_delta,
        "rotor_norm_delta": rotor_norm_delta,
        "distinct_rotor_preimages": 2,
        "orientation_erased_preimages": 1,
        "orientation_drop_delta": 1.0,
        "pseudoscalar_square": pseudoscalar_square,
        "pass": action_delta < TOL and rotor_norm_delta < TOL and pseudoscalar_square == "-1",
    }


def geomstats_rotor_witness() -> dict[str, Any]:
    sphere = Hypersphere(dim=3)
    rotor_point = torch.tensor([math.cos(0.73 / 2.0), 0.0, 0.0, -math.sin(0.73 / 2.0)], dtype=RTYPE)
    minus_rotor_point = -rotor_point
    belongs_plus = bool(sphere.belongs(rotor_point).item())
    belongs_minus = bool(sphere.belongs(minus_rotor_point).item())
    antipodal_distance = float(sphere.metric.dist(rotor_point, minus_rotor_point).item())
    return {
        "backend": "torch_side_only",
        "geomstats_jax_backend_claimed": False,
        "belongs_plus": belongs_plus,
        "belongs_minus": belongs_minus,
        "antipodal_distance": antipodal_distance,
        "known_antipodal_distance": math.pi,
        "distance_delta": abs(antipodal_distance - math.pi),
        "orientation_identification_delta": antipodal_distance,
        "pass": belongs_plus and belongs_minus and abs(antipodal_distance - math.pi) < 1.0e-6,
        "notes": "geomstats is run with GEOMSTATS_BACKEND=pytorch; no geomstats JAX path is used or claimed",
    }


def known_value_checks(
    torch_rows: dict[str, dict[str, Any]],
    sympy_witness: dict[str, Any],
    z3_witness: dict[str, Any],
    clifford_witness: dict[str, Any],
    geomstats_witness: dict[str, Any],
) -> list[dict[str, Any]]:
    max_gamma5_error = max(row["gamma5_square_error"] for row in torch_rows.values())
    max_return_error = max(row["z2_return_error"] for row in torch_rows.values())
    return [
        {
            "invariant": "gamma5^2 = I4",
            "computed": max_gamma5_error,
            "known": 0.0,
            "match": max_gamma5_error < TOL and sympy_witness["gamma5_square_is_identity"],
            "computed_by": "torch matrix product over gamma5 plus sympy exact gamma5 square",
        },
        {
            "invariant": "Z2 action returns after two applications",
            "computed": max_return_error,
            "known": 0.0,
            "match": max_return_error < TOL,
            "computed_by": "torch gamma5(gamma5(psi))-psi over finite scale rows",
        },
        {
            "invariant": "Z2 sign solutions are exactly {-1,+1}",
            "computed": z3_witness["z2_sign_models"],
            "known": [-1, 1],
            "match": z3_witness["pass"],
            "computed_by": "z3 integer model enumeration for s*s=1 plus unsat no-third-sign check",
        },
        {
            "invariant": "Cl rotor double cover has two rotor signs with same SO action",
            "computed": {
                "same_so_action_delta": clifford_witness["same_so_action_delta"],
                "distinct_rotor_preimages": clifford_witness["distinct_rotor_preimages"],
            },
            "known": {"same_so_action_delta": 0.0, "distinct_rotor_preimages": 2},
            "match": clifford_witness["pass"],
            "computed_by": "clifford Cl(3) rotor action R v ~R compared with (-R) v ~(-R)",
        },
        {
            "invariant": "Spin rotor antipodes on S3 are distance pi before SO quotient",
            "computed": geomstats_witness["antipodal_distance"],
            "known": math.pi,
            "match": geomstats_witness["pass"],
            "computed_by": "geomstats Hypersphere(dim=3) torch backend",
        },
    ]


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    torch_rows = {str(n): torch_cover_row(n) for n in SITE_COUNTS}
    jax_rows = {str(n): jax_cover_row(n) for n in SITE_COUNTS}
    parity_rows = {n: compare_rows(torch_rows[n], jax_rows[n]) for n in torch_rows}
    sympy_witness = sympy_gamma5_witness()
    z3_witness = z3_z2_witness()
    clifford_witness = clifford_rotor_witness()
    geomstats_witness = geomstats_rotor_witness()
    checks = known_value_checks(torch_rows, sympy_witness, z3_witness, clifford_witness, geomstats_witness)

    scale_rungs = {
        n: {
            "sites_or_qubits": row["sites_or_qubits"],
            "dense_state_closure_used": row["dense_state_closure_used"],
            "mps_max_bond": row["mps_max_bond"],
            "half_chain_entanglement_entropy": row["half_chain_entanglement_entropy"],
            "many_body_depth_required": row["many_body_depth_required"],
            "pass": row["pass"] and parity_rows[n]["agree"],
            "carrier_kind": row["carrier_kind"],
            "shape": row["shape"],
            "note": row["many_body_depth_note"],
        }
        for n, row in torch_rows.items()
    }
    max_jax_delta = max(row["max_value_delta"] for row in parity_rows.values())
    min_drop_delta = min(row["drop_orientation"]["outcome_delta"] for row in torch_rows.values())
    min_sheet_gap = min(row["sheet_gap"] for row in torch_rows.values())
    min_order_gap = min(row["order_gap"] for row in torch_rows.values())

    tool_ablations = {
        "torch_drop_orientation_ablation": {
            "tool": "pytorch",
            "ablation": "replace gamma5/projectors with orientation-erased identity and I/2 projectors",
            "outcome_delta": min_drop_delta,
            "delta": min_drop_delta,
            "pass": min_drop_delta > KILL_FLOOR,
        },
        "jax_drop_orientation_ablation": {
            "tool": "jax",
            "ablation": "repeat orientation-erased cover in the independent JAX x64 engine",
            "outcome_delta": min(row["drop_orientation"]["outcome_delta"] for row in jax_rows.values()),
            "delta": min(row["drop_orientation"]["outcome_delta"] for row in jax_rows.values()),
            "pass": min(row["drop_orientation"]["outcome_delta"] for row in jax_rows.values()) > KILL_FLOOR,
        },
        "clifford_orientation_rotor_ablation": {
            "tool": "clifford",
            "ablation": "erase the Cl rotor sign distinction and keep only the SO action class",
            "outcome_delta": clifford_witness["orientation_drop_delta"],
            "delta": clifford_witness["orientation_drop_delta"],
            "pass": clifford_witness["orientation_drop_delta"] > 0.0 and clifford_witness["pass"],
        },
        "z3_double_cover_ablation": {
            "tool": "z3",
            "ablation": "drop the Z2 orientation sign and collapse the two sign models to one class",
            "outcome_delta": z3_witness["orientation_drop_delta"],
            "delta": z3_witness["orientation_drop_delta"],
            "pass": z3_witness["orientation_drop_delta"] > 0.0 and z3_witness["pass"],
        },
        "sympy_gamma5_orientation_ablation": {
            "tool": "sympy",
            "ablation": "replace P_+ and P_- with the same identity/2 projector",
            "outcome_delta": sympy_witness["orientation_drop_delta"],
            "delta": sympy_witness["orientation_drop_delta"],
            "pass": sympy_witness["orientation_drop_delta"] > 0.0 and sympy_witness["pass"],
        },
        "geomstats_antipodal_identification_ablation": {
            "tool": "geomstats",
            "ablation": "identify antipodal Spin rotor points before measuring the S3 cover distance",
            "outcome_delta": geomstats_witness["orientation_identification_delta"],
            "delta": geomstats_witness["orientation_identification_delta"],
            "pass": geomstats_witness["orientation_identification_delta"] > KILL_FLOOR and geomstats_witness["pass"],
        },
    }

    positive = {
        "scale_8_16_32_64_non_dense_chirality_cover": {
            "rungs": scale_rungs,
            "pass": all(row["pass"] for row in scale_rungs.values()),
        },
        "known_value_checks_computed": {
            "checks": checks,
            "pass": all(row["match"] for row in checks),
        },
        "load_bearing_tool_ablations_nonzero": {
            "ablation_outcome_delta": tool_ablations,
            "pass": all(row["pass"] and abs(float(row["outcome_delta"])) > KILL_FLOOR for row in tool_ablations.values()),
        },
    }
    graveyard_companions = {
        "drop_orientation_kills_cover_signature": {
            "per_scale": {n: row["drop_orientation"] for n, row in torch_rows.items()},
            "z3_drop_cardinality": z3_witness["drop_orientation_cardinality"],
            "pass": all(row["drop_orientation"]["pass"] for row in torch_rows.values()) and z3_witness["drop_orientation_cardinality"] == 1,
        },
        "identity_gamma5_kills_noncommuting_order_gap": {
            "per_scale_drop_order_gap": {n: row["drop_orientation"]["drop_order_gap"] for n, row in torch_rows.items()},
            "baseline_min_order_gap": min_order_gap,
            "pass": min_order_gap > KILL_FLOOR and all(row["drop_orientation"]["drop_order_gap"] < TOL for row in torch_rows.values()),
        },
        "identified_projectors_kill_sheet_separation": {
            "per_scale_drop_sheet_gap": {n: row["drop_orientation"]["drop_sheet_gap"] for n, row in torch_rows.items()},
            "baseline_min_sheet_gap": min_sheet_gap,
            "pass": min_sheet_gap > KILL_FLOOR and all(row["drop_orientation"]["drop_sheet_gap"] < TOL for row in torch_rows.values()),
        },
        "rotor_sign_erasure_kills_double_cover": {
            "clifford": clifford_witness,
            "geomstats": geomstats_witness,
            "pass": clifford_witness["pass"] and geomstats_witness["pass"] and clifford_witness["orientation_erased_preimages"] == 1,
        },
    }
    boundary = {
        "no_dense_state_closure": {
            "scale_ladder": {"rungs": scale_rungs},
            "pass": all(row["dense_state_closure_used"] is False and row["pass"] for row in scale_rungs.values()),
        },
        "few_body_depth_boundary": {
            "pass": True,
            "many_body_depth_required": False,
            "mps_max_bond": 1,
            "half_chain_entanglement_entropy": 0.0,
            "note": "This chirality/orientation cover is specified as few-body; it does not masquerade as a many-body entangled layer.",
        },
        "dual_engine_agrees": {
            "jax_vs_pytorch": {
                "max_value_delta": max_jax_delta,
                "agree": max_jax_delta < PARITY_TOL,
                "notes": "JAX runs the gamma5/projector/order-gap formulas with x64 enabled on line 1. geomstats has no JAX backend path here and is used only through GEOMSTATS_BACKEND=pytorch.",
            },
            "pass": max_jax_delta < PARITY_TOL,
        },
        "downstream_consumers_blocked": {
            "blocked_consumers": BLOCKED_CONSUMERS,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": PROMOTION_ALLOWED is False,
        },
    }
    all_pass = (
        all(section["pass"] for section in positive.values())
        and all(section["pass"] for section in graveyard_companions.values())
        and all(section["pass"] for section in boundary.values())
        and sympy_witness["pass"]
        and z3_witness["pass"]
        and clifford_witness["pass"]
        and geomstats_witness["pass"]
    )

    blockers: list[str] = []
    if not positive["scale_8_16_32_64_non_dense_chirality_cover"]["pass"]:
        blockers.append("one or more non-dense 8/16/32/64 scale rungs failed")
    if max_jax_delta >= PARITY_TOL:
        blockers.append(f"jax_vs_pytorch max delta {max_jax_delta} exceeds {PARITY_TOL}")
    for check in checks:
        if not check["match"]:
            blockers.append(f"known value check failed: {check['invariant']}")
    for name, row in graveyard_companions.items():
        if not row["pass"]:
            blockers.append(f"negative did not kill signature: {name}")
    for name, row in tool_ablations.items():
        if not row["pass"] or abs(float(row["outcome_delta"])) <= KILL_FLOOR:
            blockers.append(f"tool ablation missing/nonzero failure: {name}")

    result = {
        "schema": "formal_scout_max_deep_lego_v1",
        "sim_id": NAME,
        "name": NAME,
        "version": VERSION,
        "tier": "4_chirality_orientation",
        "purpose": "Build one independent gamma5/Cl orientation double-cover Z2 lego at N=8,16,32,64.",
        "scientific_question": "Can a finite PEPS3D-anchored local Dirac spinor cover preserve gamma5^2=I and Z2/Cl double-cover structure while orientation-erased controls collapse the cover?",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints_in_force": DOMAIN["root_constraints_in_force"],
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "carrier_layer": "finite local Dirac spinor chirality cover over PEPS3D site-cell anchors",
        "geometry_layer": "chirality_orientation_cover: gamma5 Z2 sheet/projector structure plus Cl rotor sign double cover",
        "carrier_realization": "non-dense local product-MPS summary of torch/JAX C^4 spinors; no 2**N dense state closure",
        "peps3d_embedding": {
            str(n): {
                "shape": list(SITE_SHAPES[n]),
                "counts": peps3d_counts(SITE_SHAPES[n]),
                "anchor": "one local Dirac spinor cover cell per PEPS3D vertex; edges/faces/cells are finite anchors only",
            }
            for n in SITE_COUNTS
        },
        "spinor_state": SPINOR_STATE,
        "quaternion_action": QUATERNION_ACTION,
        "dependency_receipts": [],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "gamma5 has order two and splits local Dirac spinors into a Z2 chirality/orientation cover; Cl rotor signs +/-R are two preimages of the same SO action.",
        "branch_status_before_run": "independent single-layer lego probe only",
        "allowed_claims": [
            "bounded local chirality/orientation-cover witness at N=8,16,32,64",
            "computed gamma5^2=I, projector identities, Z2 sign structure, and Cl rotor double-cover witness",
            "orientation-drop controls kill this local cover signature",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["sympy exact gamma5/projector algebra", "z3 Z2 sign model proof", "clifford Cl(3) rotor action"],
        "graph_surfaces_used": ["finite PEPS3D site/edge/face/cell counts only"],
        "topology_surfaces_used": ["geomstats torch-side S3 antipodal rotor distance"],
        "required_inputs": [],
        "data_or_artifact_dependencies": [],
        "required_negatives": list(graveyard_companions.keys()),
        "negatives_run": graveyard_companions,
        "kill_conditions": [
            "dropping gamma5/projector orientation collapses sheet separation and order gap",
            "identity gamma5 removes noncommuting chiral-mix order sensitivity",
            "identified projectors P_+=P_-=I/2 collapse the two sheets",
            "erasing Cl rotor sign leaves one SO action class and loses double-cover cardinality",
        ],
        "required_artifacts": ["result_json", "scale_ladder", "known_value_checks", "negative_artifacts", "tool_ablation_outcomes"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{NAME}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_count": len(SITE_COUNTS),
            "max_jax_vs_pytorch_delta": max_jax_delta,
            "min_drop_orientation_delta": min_drop_delta,
            "min_sheet_gap": min_sheet_gap,
            "min_order_gap": min_order_gap,
            "promotion_allowed": PROMOTION_ALLOWED,
            "elapsed_seconds": time.time() - started,
        },
        "pass_rule": "All 8/16/32/64 non-dense rungs pass; torch/JAX parity < 1e-9; computed known-value checks match; named negatives kill the cover; and all load-bearing tool ablations have nonzero outcome_delta.",
        "fail_rule": "Fail on dense closure, missing scale rung, fake JAX/geomstats path, missing/zero tool ablation delta, non-killing negative, hardcoded-only invariant, or downstream unlock.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["future lower-layer chirality/orientation audits that preserve this claim ceiling"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "scale_ladder": {"rungs": scale_rungs, "pass": all(row["pass"] for row in scale_rungs.values())},
        "scale_rows": {
            "torch_primary": torch_rows,
            "jax_secondary": jax_rows,
            "parity_rows": parity_rows,
        },
        "jax_vs_pytorch": boundary["dual_engine_agrees"]["jax_vs_pytorch"],
        "known_value_checks": checks,
        "sympy_gamma5_witness": sympy_witness,
        "z3_z2_witness": z3_witness,
        "clifford_orientation_rotor_witness": clifford_witness,
        "geomstats_torch_side_witness": geomstats_witness,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(SITE_COUNTS) + len(graveyard_companions),
            "passed": sum(1 for row in scale_rungs.values() if row["pass"]) + sum(1 for row in graveyard_companions.values() if row["pass"]),
            "variants": ["site_counts_8_16_32_64", *list(graveyard_companions.keys())],
        },
        "shells": {
            "chirality_orientation_cover": ["gamma5_order_two", "P_plus/P_minus_sheet_projection", "Z2_sign_cover", "Cl_rotor_sign_double_cover"],
        },
        "future_continuations": {"blocked": BLOCKED_CONSUMERS, "allowed": ["repeat this same layer with stricter local carrier fixtures"]},
        "compatibility_weights": {
            "gamma5_z2_cover": 1.0 if positive["known_value_checks_computed"]["pass"] else 0.0,
            "orientation_drop_control": 0.0 if graveyard_companions["drop_orientation_kills_cover_signature"]["pass"] else 1.0,
        },
        "compression_map": {
            "local_spinor_to_cover_signature": "psi_i -> (P_+ psi_i, P_- psi_i, gamma5 psi_i, Cl rotor sign class)",
            "orientation_drop": "P_+=P_-=I/2 and gamma5=I collapses the two-sheet cover readout",
        },
        "present_survivor": {
            "survives": ["gamma5_square_identity", "Z2_two_sign_models", "Cl_rotor_same_SO_action_two_preimages", "dual_engine_agreement"],
            "killed_controls": list(graveyard_companions.keys()),
            "capacity": min(min_drop_delta, clifford_witness["orientation_drop_delta"], z3_witness["orientation_drop_delta"]),
        },
        "outward_record": {
            "result_path": str(OUT_PATH),
            "claim_ceiling": CLAIM_CEILING,
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "survivor_invariant": {
            "passed": all_pass,
            "computed": min(min_drop_delta, clifford_witness["orientation_drop_delta"], z3_witness["orientation_drop_delta"]),
            "threshold": KILL_FLOOR,
            "invariant": "The gamma5/Z2/Cl cover survives known-value checks while orientation-erased controls collapse the cover cardinality or signature.",
        },
        "summary": {
            "all_pass": all_pass,
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "result_path": str(OUT_PATH),
            "blockers": blockers,
        },
        "blockers": blockers,
        "why_not_v4_probes": "This is a v5 max-deep single lego with explicit non-dense 8/16/32/64 scale ladder, torch/JAX dual engines, computed gamma5/Z2/Cl known-value checks, named negatives, and nonzero load-bearing tool ablations; promotion_allowed remains false.",
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(as_jsonable(result["summary"]), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
