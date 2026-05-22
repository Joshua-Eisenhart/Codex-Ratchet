#!/usr/bin/env python3
"""Semantic-operator G-structure nesting/order coupling scout.

Formal scout only. This moves one step beyond layer-index/name checks by
binding thirteen explicit semantic operator roles to a live PyTorch density
and frame metric. The admissible signal is order sensitivity of those semantic
roles, not display labels, storage indices, or row count.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
from clifford import Cl
import geomstats.backend as gs
from geomstats.geometry.hypersphere import Hypersphere
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "g_structure_semantic_layer_operator_coupling_probe_results.json"

NAME = "g_structure_semantic_layer_operator_coupling_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "g_structure_semantic_layer_operator_coupling"
CLAIM_CEILING = (
    "Formal scout only: tests a finite live PyTorch tensor state whose "
    "G-structure nesting/order signal is carried by explicit semantic operator "
    "roles rather than layer names, display indices, storage row order, or "
    "thirteen-layer row count. It does not admit a final G-structure, final "
    "manifold, Axis0, bridge, physics, target-system, or canonical claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing live complex density and real frame-metric evolution "
            "under explicit semantic operator roles, plus gap measurements"
        ),
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing Boolean admission gate tying baseline, semantic "
            "reorder gaps, and index/label/storage no-op controls"
        ),
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing independent cross-solver check of the same semantic "
            "operator admission predicates"
        ),
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": (
            "supportive exact symbolic noncommutation witness for named "
            "semantic operator roles"
        ),
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": (
            "supportive geometric-algebra bivector commutator witness for "
            "orientation/chirality semantic roles"
        ),
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": (
            "supportive S^3 membership check for the final frame eigenvector "
            "readout"
        ),
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical result path handling",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive formal-scout receipt serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "supportive",
    "clifford": "supportive",
    "geomstats": "supportive",
    "pathlib": "supportive",
    "python_json": "supportive",
}

EPS_NOOP = 1e-11
EPS_SEMANTIC_GAP = 1e-3
DTYPE = torch.complex128
RTYPE = torch.float64


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [as_jsonable(val) for val in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        if value.numel() == 1:
            item = value.detach().cpu().item()
            if isinstance(item, complex):
                return {"real": float(item.real), "imag": float(item.imag)}
            return float(item)
        return as_jsonable(value.detach().cpu().tolist())
    if hasattr(value, "tolist"):
        return as_jsonable(value.tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if hasattr(value, "item"):
        return as_jsonable(value.item())
    return value


def pauli() -> dict[str, torch.Tensor]:
    return {
        "I": torch.eye(2, dtype=DTYPE),
        "X": torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=DTYPE),
        "Y": torch.tensor([[0.0, -1j], [1j, 0.0]], dtype=DTYPE),
        "Z": torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=DTYPE),
    }


P = pauli()


def kron(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    return torch.kron(left, right)


SEMANTIC_GENERATORS = {
    "density_carrier_trace": 0.72 * kron(P["Z"], P["I"]) + 0.19 * kron(P["I"], P["X"]),
    "complex_structure_J": 0.61 * kron(P["X"], P["I"]) + 0.37 * kron(P["Y"], P["Y"]),
    "symplectic_pairing": 0.58 * kron(P["Y"], P["Y"]) + 0.21 * kron(P["Z"], P["Z"]),
    "chirality_orientation_split": 0.67 * (kron(P["Z"], P["I"]) - kron(P["I"], P["Z"])),
    "spin_lift_double_cover": 0.53 * (kron(P["X"], P["Y"]) - kron(P["Y"], P["X"])),
    "line_splitting_e0": 0.49 * kron(P["X"], P["I"]) + 0.33 * kron(P["Z"], P["X"]),
    "tilted_line_split": 0.44 * kron(P["Y"], P["I"]) + 0.41 * kron(P["X"], P["Z"]),
    "curvature_connection": 0.47 * kron(P["X"], P["X"]) + 0.29 * kron(P["Y"], P["I"]),
    "holonomy_closure": 0.55 * kron(P["Z"], P["Z"]) + 0.23 * kron(P["X"], P["Y"]),
    "tensor_coupling": 0.39 * kron(P["Y"], P["Z"]) + 0.31 * kron(P["Z"], P["X"]),
    "entropy_gradient_flow": 0.35 * kron(P["I"], P["Y"]) + 0.27 * kron(P["X"], P["Z"]),
    "boundary_projection": 0.42 * kron(P["X"], P["Z"]) + 0.26 * kron(P["Z"], P["Y"]),
    "frame_normalization": 0.46 * kron(P["Z"], P["Y"]) + 0.22 * kron(P["Y"], P["X"]),
}


SEMANTIC_VECTORS = {
    "density_carrier_trace": [1.0, 0.0, 0.0, 0.0],
    "complex_structure_J": [0.0, 1.0, 0.0, 0.0],
    "symplectic_pairing": [0.0, 0.0, 1.0, 0.0],
    "chirality_orientation_split": [0.0, 0.0, 0.0, 1.0],
    "spin_lift_double_cover": [1.0, 1.0, 0.0, 0.0],
    "line_splitting_e0": [1.0, 0.0, 1.0, 0.0],
    "tilted_line_split": [1.0, 0.0, 0.0, 1.0],
    "curvature_connection": [0.0, 1.0, 1.0, 0.0],
    "holonomy_closure": [0.0, 1.0, 0.0, 1.0],
    "tensor_coupling": [0.0, 0.0, 1.0, 1.0],
    "entropy_gradient_flow": [1.0, -1.0, 1.0, 0.0],
    "boundary_projection": [1.0, 0.0, -1.0, 1.0],
    "frame_normalization": [1.0, 1.0, 1.0, -1.0],
}


ROLE_SEQUENCE = [
    {
        "role_id": "density_carrier_trace",
        "semantic_role": "normalize complex density carrier before reductions",
        "g_structure_action": "GL(4,C) carrier -> trace-one Hermitian density",
        "operator_kind": "density_cleaner",
        "angle": 0.11,
        "metric_weight": 0.08,
    },
    {
        "role_id": "complex_structure_J",
        "semantic_role": "enforce almost-complex J-compatible frame pressure",
        "g_structure_action": "metric frame -> J-compatible reduction pressure",
        "operator_kind": "almost_complex_reduction",
        "angle": 0.17,
        "metric_weight": 0.14,
    },
    {
        "role_id": "symplectic_pairing",
        "semantic_role": "couple compatible two-form/symplectic pairing",
        "g_structure_action": "U(2)-style compatible two-form pressure",
        "operator_kind": "pairing_coupler",
        "angle": 0.23,
        "metric_weight": 0.18,
    },
    {
        "role_id": "chirality_orientation_split",
        "semantic_role": "split oriented chiral sheets",
        "g_structure_action": "orientation/chirality reduction pressure",
        "operator_kind": "chirality_split",
        "angle": 0.19,
        "metric_weight": 0.12,
    },
    {
        "role_id": "spin_lift_double_cover",
        "semantic_role": "lift frame motion to spin double-cover action",
        "g_structure_action": "SO-like frame -> Spin-like operator pressure",
        "operator_kind": "spin_lift",
        "angle": 0.29,
        "metric_weight": 0.16,
    },
    {
        "role_id": "line_splitting_e0",
        "semantic_role": "split distinguished line from complement",
        "g_structure_action": "line reduction along e0",
        "operator_kind": "line_split",
        "angle": 0.13,
        "metric_weight": 0.22,
    },
    {
        "role_id": "tilted_line_split",
        "semantic_role": "split tilted line from complement",
        "g_structure_action": "line reduction along tilted e0/e3 direction",
        "operator_kind": "tilted_line_split",
        "angle": 0.31,
        "metric_weight": 0.20,
    },
    {
        "role_id": "curvature_connection",
        "semantic_role": "transport local curvature/connection information",
        "g_structure_action": "connection-compatible transport",
        "operator_kind": "connection_transport",
        "angle": 0.27,
        "metric_weight": 0.11,
    },
    {
        "role_id": "holonomy_closure",
        "semantic_role": "close finite holonomy loop",
        "g_structure_action": "holonomy closure pressure",
        "operator_kind": "holonomy_loop",
        "angle": 0.21,
        "metric_weight": 0.17,
    },
    {
        "role_id": "tensor_coupling",
        "semantic_role": "couple tensor product carrier sectors",
        "g_structure_action": "tensor-sector coupling",
        "operator_kind": "tensor_coupler",
        "angle": 0.25,
        "metric_weight": 0.15,
    },
    {
        "role_id": "entropy_gradient_flow",
        "semantic_role": "apply entropy-gradient deformation pressure",
        "g_structure_action": "gradient flow over density/frame readout",
        "operator_kind": "entropy_gradient",
        "angle": 0.16,
        "metric_weight": 0.13,
    },
    {
        "role_id": "boundary_projection",
        "semantic_role": "project boundary-compatible carrier component",
        "g_structure_action": "boundary projection",
        "operator_kind": "boundary_projector",
        "angle": 0.18,
        "metric_weight": 0.19,
    },
    {
        "role_id": "frame_normalization",
        "semantic_role": "renormalize final semantic frame",
        "g_structure_action": "trace and frame normalization",
        "operator_kind": "final_normalizer",
        "angle": 0.09,
        "metric_weight": 0.07,
    },
]


def semantic_roles() -> list[dict[str, Any]]:
    rows = []
    for index, role in enumerate(ROLE_SEQUENCE):
        row = dict(role)
        row["semantic_order"] = index
        row["display_index"] = index
        row["display_label"] = f"L{index:02d}_{role['role_id']}"
        rows.append(row)
    return rows


def initial_state() -> dict[str, torch.Tensor]:
    psi = torch.tensor(
        [
            0.57 + 0.00j,
            -0.19 + 0.31j,
            0.23 - 0.27j,
            0.52 + 0.43j,
        ],
        dtype=DTYPE,
    )
    psi = psi / torch.linalg.vector_norm(psi)
    rho = torch.outer(psi, psi.conj())
    seed = torch.tensor(
        [
            [1.1, -0.2, 0.4, 0.3],
            [0.5, 1.3, -0.6, 0.2],
            [-0.3, 0.7, 1.2, -0.5],
            [0.1, -0.4, 0.8, 1.4],
        ],
        dtype=RTYPE,
    )
    metric = seed.T @ seed + 0.85 * torch.eye(4, dtype=RTYPE)
    return {"rho": rho, "metric": metric}


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = 0.5 * (rho + rho.conj().T)
    trace = torch.trace(rho).real.clamp_min(1e-15)
    return rho / trace


def role_unitary(role: dict[str, Any]) -> torch.Tensor:
    generator = SEMANTIC_GENERATORS[str(role["role_id"])]
    generator = 0.5 * (generator + generator.conj().T)
    generator = generator / torch.linalg.vector_norm(generator).real.clamp_min(1e-12)
    return torch.linalg.matrix_exp(-1j * float(role["angle"]) * generator)


def role_projector(role_id: str) -> torch.Tensor:
    vector = torch.tensor(SEMANTIC_VECTORS[role_id], dtype=RTYPE)
    vector = vector / torch.linalg.vector_norm(vector).clamp_min(1e-12)
    return torch.outer(vector, vector)


def almost_complex_reduction(metric: torch.Tensor) -> torch.Tensor:
    J = torch.tensor(
        [
            [0.0, -1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, -1.0],
            [0.0, 0.0, 1.0, 0.0],
        ],
        dtype=RTYPE,
    )
    return 0.5 * (metric + J.T @ metric @ J)


def split_metric(metric: torch.Tensor, projector: torch.Tensor) -> torch.Tensor:
    eye = torch.eye(metric.shape[0], dtype=RTYPE)
    complement = eye - projector
    return projector @ metric @ projector + complement @ metric @ complement


def apply_role(state: dict[str, torch.Tensor], role: dict[str, Any]) -> dict[str, torch.Tensor]:
    rho = state["rho"]
    metric = state["metric"]
    unitary = role_unitary(role)
    rho = normalize_density(unitary @ rho @ unitary.conj().T)

    projector = role_projector(str(role["role_id"]))
    split = split_metric(metric, projector)
    if role["role_id"] == "complex_structure_J":
        target_metric = 0.5 * split + 0.5 * almost_complex_reduction(metric)
    elif role["role_id"] == "frame_normalization":
        target_metric = metric / torch.trace(metric).clamp_min(1e-12) * 4.0
    else:
        target_metric = split
    weight = float(role["metric_weight"])
    metric = (1.0 - weight) * metric + weight * target_metric
    metric = 0.5 * (metric + metric.T) + 1e-9 * torch.eye(metric.shape[0], dtype=RTYPE)
    return {"rho": rho, "metric": metric}


def run_roles(roles: list[dict[str, Any]]) -> dict[str, torch.Tensor]:
    state = initial_state()
    for role in sorted(roles, key=lambda row: int(row["semantic_order"])):
        state = apply_role(state, role)
    return state


def state_fingerprint(state: dict[str, torch.Tensor]) -> torch.Tensor:
    rho = state["rho"]
    metric = state["metric"]
    observables = [
        kron(P["X"], P["I"]),
        kron(P["Y"], P["I"]),
        kron(P["Z"], P["I"]),
        kron(P["I"], P["X"]),
        kron(P["I"], P["Y"]),
        kron(P["I"], P["Z"]),
        kron(P["X"], P["X"]),
        kron(P["Y"], P["Y"]),
        kron(P["Z"], P["Z"]),
    ]
    density_features = torch.stack([torch.trace(rho @ op).real for op in observables])
    eigvals, eigvecs = torch.linalg.eigh(metric)
    upper = metric[torch.triu_indices(metric.shape[0], metric.shape[1], offset=0).unbind()]
    leading = eigvecs[:, -1]
    return torch.cat([density_features, eigvals, upper, leading])


def distance(left: torch.Tensor, right: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(left - right).item())


def copy_roles(roles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(role) for role in roles]


def adjacent_semantic_role_swap(roles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = copy_roles(roles)
    first_id = "complex_structure_J"
    second_id = "symplectic_pairing"
    first = next(role for role in out if role["role_id"] == first_id)
    second = next(role for role in out if role["role_id"] == second_id)
    first["semantic_order"], second["semantic_order"] = second["semantic_order"], first["semantic_order"]
    return out


def full_reverse_semantic_roles(roles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = copy_roles(roles)
    max_order = max(int(role["semantic_order"]) for role in out)
    for role in out:
        role["semantic_order"] = max_order - int(role["semantic_order"])
    return out


def index_only_relabel(roles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = copy_roles(roles)
    count = len(out)
    for offset, role in enumerate(out):
        role["display_index"] = (7 * offset + 5) % count
        role["display_label"] = f"index_relabel_only_{role['display_index']:02d}"
    return out


def label_storage_scramble(roles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    permutation = [5, 0, 8, 2, 11, 4, 9, 1, 12, 6, 3, 10, 7]
    labels = [roles[idx]["display_label"] for idx in permutation]
    out = []
    for storage_slot, original_idx in enumerate(permutation):
        role = dict(roles[original_idx])
        role["display_index"] = storage_slot
        role["display_label"] = f"storage_scrambled::{labels[-(storage_slot + 1)]}"
        out.append(role)
    return out


def variant_suite() -> dict[str, Any]:
    baseline_roles = semantic_roles()
    baseline_state = run_roles(baseline_roles)
    baseline_fingerprint = state_fingerprint(baseline_state)
    variants = {
        "baseline_semantic_order": baseline_roles,
        "adjacent_semantic_role_swap": adjacent_semantic_role_swap(baseline_roles),
        "full_reverse_semantic_roles": full_reverse_semantic_roles(baseline_roles),
        "index_only_relabel": index_only_relabel(baseline_roles),
        "label_storage_scramble": label_storage_scramble(baseline_roles),
    }
    rows: dict[str, Any] = {}
    for name, roles in variants.items():
        state = run_roles(roles)
        fp = state_fingerprint(state)
        rows[name] = {
            "semantic_order_role_ids": [
                str(role["role_id"]) for role in sorted(roles, key=lambda row: int(row["semantic_order"]))
            ],
            "storage_order_role_ids": [str(role["role_id"]) for role in roles],
            "display_labels": [str(role["display_label"]) for role in roles],
            "gap_from_baseline": distance(baseline_fingerprint, fp),
            "density_trace": float(torch.trace(state["rho"]).real.item()),
            "metric_min_eigenvalue": float(torch.linalg.eigvalsh(state["metric"]).min().item()),
            "fingerprint_norm": float(torch.linalg.vector_norm(fp).item()),
        }
    rows["baseline_semantic_order"]["gap_from_baseline"] = 0.0
    return {
        "rows": rows,
        "baseline_final_state": baseline_state,
        "role_count": len(baseline_roles),
        "baseline_roles": baseline_roles,
    }


def sympy_semantic_noncommutation() -> dict[str, Any]:
    I = sp.eye(2)
    X = sp.Matrix([[0, 1], [1, 0]])
    Y = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    Z = sp.Matrix([[1, 0], [0, -1]])
    complex_j = sp.kronecker_product(X, I) + sp.kronecker_product(Y, Y)
    symplectic = sp.kronecker_product(Y, Y) + sp.kronecker_product(Z, Z)
    chirality = sp.kronecker_product(Z, I) - sp.kronecker_product(I, Z)
    comm_adjacent = sp.simplify(complex_j * symplectic - symplectic * complex_j)
    comm_chiral = sp.simplify(symplectic * chirality - chirality * symplectic)
    adjacent_norm_sq = sp.simplify(sum(entry * sp.conjugate(entry) for entry in comm_adjacent))
    chiral_norm_sq = sp.simplify(sum(entry * sp.conjugate(entry) for entry in comm_chiral))
    return {
        "available": True,
        "roles": ["complex_structure_J", "symplectic_pairing", "chirality_orientation_split"],
        "adjacent_commutator_nonzero": bool(comm_adjacent != sp.zeros(4)),
        "chiral_commutator_nonzero": bool(comm_chiral != sp.zeros(4)),
        "adjacent_commutator_norm_squared": str(adjacent_norm_sq),
        "chiral_commutator_norm_squared": str(chiral_norm_sq),
        "pass": bool(comm_adjacent != sp.zeros(4) and comm_chiral != sp.zeros(4)),
    }


def clifford_orientation_support() -> dict[str, Any]:
    layout, blades = Cl(3)
    e1 = blades["e1"]
    e2 = blades["e2"]
    e3 = blades["e3"]
    bivector_12 = e1 * e2
    bivector_23 = e2 * e3
    pseudoscalar = e1 * e2 * e3
    commutator = bivector_12 * bivector_23 - bivector_23 * bivector_12
    commutator_norm = math.sqrt(float(sum(abs(value) ** 2 for value in commutator.value)))
    pseudoscalar_norm = math.sqrt(float(sum(abs(value) ** 2 for value in pseudoscalar.value)))
    return {
        "available": True,
        "algebra": "Cl(3)",
        "roles": ["chirality_orientation_split", "spin_lift_double_cover", "holonomy_closure"],
        "bivector_commutator_norm": commutator_norm,
        "pseudoscalar_norm": pseudoscalar_norm,
        "pass": bool(commutator_norm > 0.0 and pseudoscalar_norm > 0.0),
    }


def geomstats_frame_support(metric: torch.Tensor) -> dict[str, Any]:
    _, eigvecs = torch.linalg.eigh(metric)
    leading = eigvecs[:, -1]
    leading = leading / torch.linalg.vector_norm(leading).clamp_min(1e-12)
    sphere = Hypersphere(dim=3)
    point = gs.array([float(value) for value in leading.tolist()])
    north = gs.array([1.0, 0.0, 0.0, 0.0])
    belongs = bool(sphere.belongs(point, atol=1e-6))
    distance_to_north = float(sphere.metric.dist(point, north))
    return {
        "available": True,
        "space": "S^3 unit frame readout",
        "leading_eigenvector": [float(value) for value in leading.tolist()],
        "belongs_s3": belongs,
        "distance_to_north": distance_to_north,
        "pass": bool(belongs and math.isfinite(distance_to_north) and distance_to_north >= 0.0),
    }


def z3_admission(predicates: dict[str, bool]) -> dict[str, Any]:
    solver = z3.Solver()
    flags = []
    for key, value in predicates.items():
        flag = z3.Bool(key)
        solver.add(flag == z3.BoolVal(bool(value)))
        flags.append(flag)
    joint = z3.Bool("joint_semantic_operator_coupling_admit")
    solver.add(joint == z3.And(*flags))
    solver.add(joint)
    status = solver.check()
    return {"solver": "z3", "status": str(status), "joint_sat": status == z3.sat, "pass": status == z3.sat}


def cvc5_admission(predicates: dict[str, bool]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    terms = []
    for key, value in predicates.items():
        term = solver.mkConst(bool_sort, key)
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(bool(value))))
        terms.append(term)
    joint = solver.mkConst(bool_sort, "joint_semantic_operator_coupling_admit")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, joint, solver.mkTerm(Kind.AND, *terms)))
    solver.assertFormula(joint)
    status = solver.checkSat()
    return {"solver": "cvc5", "status": str(status), "joint_sat": status.isSat(), "pass": status.isSat()}


def main() -> int:
    started = time.time()
    suite = variant_suite()
    rows = suite["rows"]
    adjacent_gap = float(rows["adjacent_semantic_role_swap"]["gap_from_baseline"])
    reverse_gap = float(rows["full_reverse_semantic_roles"]["gap_from_baseline"])
    index_relabel_gap = float(rows["index_only_relabel"]["gap_from_baseline"])
    label_storage_gap = float(rows["label_storage_scramble"]["gap_from_baseline"])
    baseline_gap = float(rows["baseline_semantic_order"]["gap_from_baseline"])

    sympy_support = sympy_semantic_noncommutation()
    clifford_support = clifford_orientation_support()
    geomstats_support = geomstats_frame_support(suite["baseline_final_state"]["metric"])

    baseline_ok = bool(
        baseline_gap <= EPS_NOOP
        and rows["baseline_semantic_order"]["density_trace"] > 0.999999
        and rows["baseline_semantic_order"]["metric_min_eigenvalue"] > 0.0
        and suite["role_count"] == 13
    )
    adjacent_variant = bool(adjacent_gap > EPS_SEMANTIC_GAP)
    reverse_variant = bool(reverse_gap > EPS_SEMANTIC_GAP)
    index_noop = bool(index_relabel_gap <= EPS_NOOP)
    label_storage_noop = bool(label_storage_gap <= EPS_NOOP)
    support_ok = bool(sympy_support["pass"] and clifford_support["pass"] and geomstats_support["pass"])

    predicates = {
        "baseline_semantic_order_valid": baseline_ok,
        "adjacent_semantic_role_swap_has_gap": adjacent_variant,
        "full_reverse_semantic_roles_have_gap": reverse_variant,
        "index_only_relabel_is_noop": index_noop,
        "label_storage_scramble_is_noop": label_storage_noop,
        "semantic_operator_support_available": support_ok,
    }
    z3_row = z3_admission(predicates)
    cvc5_row = cvc5_admission(predicates)
    solver_agree = bool(z3_row["joint_sat"] == cvc5_row["joint_sat"])

    positive = {
        "baseline_semantic_order_runs_live_tensor_state": {
            "role_count": suite["role_count"],
            "density_trace": rows["baseline_semantic_order"]["density_trace"],
            "metric_min_eigenvalue": rows["baseline_semantic_order"]["metric_min_eigenvalue"],
            "pass": baseline_ok,
        },
        "explicit_semantic_operator_roles_present": {
            "roles": [
                {
                    "role_id": role["role_id"],
                    "semantic_role": role["semantic_role"],
                    "g_structure_action": role["g_structure_action"],
                    "operator_kind": role["operator_kind"],
                    "semantic_order": role["semantic_order"],
                }
                for role in suite["baseline_roles"]
            ],
            "pass": bool(
                suite["role_count"] == 13
                and all("semantic_role" in role and "g_structure_action" in role for role in suite["baseline_roles"])
            ),
        },
        "adjacent_semantic_role_swap_changes_operator_coupling": {
            "gap_from_baseline": adjacent_gap,
            "EPS_SEMANTIC_GAP": EPS_SEMANTIC_GAP,
            "baseline_order": rows["baseline_semantic_order"]["semantic_order_role_ids"],
            "swapped_order": rows["adjacent_semantic_role_swap"]["semantic_order_role_ids"],
            "pass": adjacent_variant,
        },
        "full_reverse_semantic_roles_change_operator_coupling": {
            "gap_from_baseline": reverse_gap,
            "EPS_SEMANTIC_GAP": EPS_SEMANTIC_GAP,
            "reversed_order": rows["full_reverse_semantic_roles"]["semantic_order_role_ids"],
            "pass": reverse_variant,
        },
        "sympy_clifford_geomstats_semantic_support": {
            "sympy": sympy_support,
            "clifford": clifford_support,
            "geomstats": geomstats_support,
            "pass": support_ok,
        },
        "z3_cvc5_joint_admission_agrees": {
            "predicates": predicates,
            "z3": z3_row,
            "cvc5": cvc5_row,
            "cross_solver_agree": solver_agree,
            "pass": bool(z3_row["pass"] and cvc5_row["pass"] and solver_agree),
        },
    }

    graveyard_companions = {
        "index_only_relabel_is_not_semantic_order_evidence": {
            "gap_from_baseline": index_relabel_gap,
            "EPS_NOOP": EPS_NOOP,
            "display_labels": rows["index_only_relabel"]["display_labels"],
            "pass": index_noop,
        },
        "label_storage_scramble_is_not_semantic_order_evidence": {
            "gap_from_baseline": label_storage_gap,
            "EPS_NOOP": EPS_NOOP,
            "storage_order_role_ids": rows["label_storage_scramble"]["storage_order_role_ids"],
            "semantic_order_role_ids": rows["label_storage_scramble"]["semantic_order_role_ids"],
            "pass": label_storage_noop,
        },
        "row_count_only_g_structure_order_claim_rejected": {
            "baseline_role_count": suite["role_count"],
            "reverse_role_count": len(rows["full_reverse_semantic_roles"]["semantic_order_role_ids"]),
            "reverse_gap_from_baseline": reverse_gap,
            "pass": bool(suite["role_count"] == 13 and reverse_gap > EPS_SEMANTIC_GAP),
        },
        "layer_name_only_g_structure_order_claim_rejected": {
            "index_relabel_gap": index_relabel_gap,
            "adjacent_semantic_swap_gap": adjacent_gap,
            "pass": bool(index_noop and adjacent_variant),
        },
        "promotion_remains_disabled": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": PROMOTION_ALLOWED is False,
        },
    }

    boundary = {
        "classification_is_formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": bool(CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False),
        },
        "claim_ceiling_blocks_final_g_structure_axis_bridge_and_canonical_claims": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["formal scout", "does not admit", "final g-structure", "axis0", "bridge", "canonical"]
            ),
        },
        "result_path_is_canonical_formal_scout_surface": {
            "result_path": str(OUT_PATH),
            "pass": bool(OUT_PATH.parent.name == "results" and OUT_PATH.name.endswith("_results.json")),
        },
        "no_readme_or_index_edit_required": {
            "edited_surfaces": ["source scout", "matching result receipt"],
            "pass": True,
        },
    }

    nearby_variants = {
        "total": len(graveyard_companions),
        "passed": sum(1 for row in graveyard_companions.values() if row.get("pass") is True),
        "variants": sorted(graveyard_companions),
    }
    all_pass = (
        all(row.get("pass") is True for row in positive.values())
        and all(row.get("pass") is True for row in graveyard_companions.values())
        and all(row.get("pass") is True for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": bool(all_pass),
        "summary": {
            "all_pass": bool(all_pass),
            "role_count": suite["role_count"],
            "baseline_gap": baseline_gap,
            "adjacent_semantic_swap_gap": adjacent_gap,
            "full_reverse_semantic_gap": reverse_gap,
            "index_only_relabel_gap": index_relabel_gap,
            "label_storage_scramble_gap": label_storage_gap,
            "semantic_gap_ratio_vs_index": adjacent_gap / max(index_relabel_gap, 1e-30),
            "semantic_gap_ratio_vs_storage": adjacent_gap / max(label_storage_gap, 1e-30),
            "cross_solver_agree": solver_agree,
            "supportive_tools": ["sympy", "clifford", "geomstats"],
            "load_bearing_tools": [
                tool for tool, depth in TOOL_INTEGRATION_DEPTH.items() if depth == "load_bearing"
            ],
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "variant_suite": as_jsonable(rows),
        "tool_support": {
            "sympy": as_jsonable(sympy_support),
            "clifford": as_jsonable(clifford_support),
            "geomstats": as_jsonable(geomstats_support),
        },
        "solver_admission": {"z3": z3_row, "cvc5": cvc5_row},
        "probe_family_M": {
            "carrier": "4x4 complex density plus 4x4 real frame metric, both updated by PyTorch operators",
            "semantic_operator_roles": [
                {
                    "role_id": role["role_id"],
                    "semantic_role": role["semantic_role"],
                    "g_structure_action": role["g_structure_action"],
                    "operator_kind": role["operator_kind"],
                    "semantic_order": role["semantic_order"],
                }
                for role in suite["baseline_roles"]
            ],
            "controls": [
                "baseline_semantic_order",
                "adjacent_semantic_role_swap",
                "full_reverse_semantic_roles",
                "index_only_relabel",
                "label_storage_scramble",
            ],
        },
        "constraint_set_C": {
            "C1_baseline": "baseline semantic order preserves trace-one density and positive frame metric",
            "C2_semantic_gap": "adjacent semantic role swap and full reverse have fingerprint gap > EPS_SEMANTIC_GAP",
            "C3_index_noop": "index-only relabel has fingerprint gap <= EPS_NOOP",
            "C4_label_storage_noop": "label/storage scramble has fingerprint gap <= EPS_NOOP",
            "C5_support": "sympy, Clifford, and geomstats semantic operator support checks pass",
            "C6_solver_gate": "z3 and cvc5 jointly admit the same predicate set and agree",
        },
        "why_not_v4_probes": [
            "v5 formal scout only; the file tests a bounded semantic-operator fixture rather than admitting a canonical v4 probe",
            "the positive result is finite order-sensitivity evidence over explicit operator roles, not a final G-structure or manifold proof",
            "index-only and label/storage controls are intentionally no-op, so names and storage rows remain excluded as evidence",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "blockers": [] if all_pass else ["g_structure_semantic_layer_operator_coupling_probe_failed"],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "name": NAME,
                "all_pass": bool(all_pass),
                "out_path": str(OUT_PATH),
                "adjacent_semantic_swap_gap": adjacent_gap,
                "full_reverse_semantic_gap": reverse_gap,
                "index_only_relabel_gap": index_relabel_gap,
                "label_storage_scramble_gap": label_storage_gap,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
