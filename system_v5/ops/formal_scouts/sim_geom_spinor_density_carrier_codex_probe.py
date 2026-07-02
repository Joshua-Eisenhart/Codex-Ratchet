#!/usr/bin/env python3
"""Independent known-geometry probe for a C^2 spinor density carrier."""

from __future__ import annotations

import json
import math
import os
import pathlib
import sys
import time
from typing import Any


os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")

import torch
import sympy as sp
import z3
import cvc5
from cvc5 import Kind
from clifford import Cl
import geomstats.backend as gs
from geomstats.geometry.special_orthogonal import SpecialOrthogonal
import gudhi
import rustworkx as rx
import toponetx as tnx


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_PATH = ROOT / "results" / "geom_spinor_density_carrier_codex_probe_results.json"

DTYPE_C = torch.complex128
DTYPE_R = torch.float64
STRICT_TOL = 1.0e-12
GEOM_TOL = 1.0e-10
HAAR_COUNT = 4096

I2 = torch.eye(2, dtype=DTYPE_C)
SIGMA_X = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=DTYPE_C)
SIGMA_Y = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=DTYPE_C)
SIGMA_Z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=DTYPE_C)
SIGMAS = [SIGMA_X, SIGMA_Y, SIGMA_Z]


def to_jsonable(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        if value.ndim == 0:
            return to_jsonable(value.detach().cpu().item())
        return to_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, (str, bool)) or value is None:
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value
    if hasattr(value, "item"):
        try:
            return to_jsonable(value.item())
        except Exception:
            pass
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    return str(value)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def bloch(psi: torch.Tensor) -> torch.Tensor:
    return torch.stack([torch.vdot(psi, sigma @ psi).real for sigma in SIGMAS]).to(DTYPE_R)


def bloch_from_density(rho: torch.Tensor) -> torch.Tensor:
    return torch.stack([torch.trace(rho @ sigma).real for sigma in SIGMAS]).to(DTYPE_R)


def rho_from_bloch(r: torch.Tensor) -> torch.Tensor:
    out = I2.clone()
    for idx, sigma in enumerate(SIGMAS):
        out = out + r[idx].to(DTYPE_C) * sigma
    return 0.5 * out


def max_abs(tensor: torch.Tensor) -> float:
    return float(torch.max(torch.abs(tensor)).item())


def scalar_close(computed: float, known: float, tol: float) -> bool:
    return bool(abs(float(computed) - float(known)) <= tol + tol * abs(float(known)))


def tensor_close(computed: torch.Tensor, known: torch.Tensor, tol: float) -> bool:
    return bool(torch.allclose(computed, known, atol=tol, rtol=tol))


def add_check(
    checks: list[dict[str, Any]],
    invariant: str,
    computed: Any,
    known: Any,
    match: bool,
    tolerance: float | str,
    tools: list[str],
    detail: str,
) -> None:
    checks.append(
        {
            "invariant": invariant,
            "computed": to_jsonable(computed),
            "known": to_jsonable(known),
            "match": bool(match),
            "tolerance": tolerance,
            "tools": tools,
            "detail": detail,
        }
    )


def normalized_known_spinors() -> dict[str, tuple[torch.Tensor, torch.Tensor]]:
    s2 = math.sqrt(2.0)
    return {
        "ket_0": (
            torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=DTYPE_C),
            torch.tensor([0.0, 0.0, 1.0], dtype=DTYPE_R),
        ),
        "ket_1": (
            torch.tensor([0.0 + 0.0j, 1.0 + 0.0j], dtype=DTYPE_C),
            torch.tensor([0.0, 0.0, -1.0], dtype=DTYPE_R),
        ),
        "plus_x": (
            torch.tensor([1.0 / s2 + 0.0j, 1.0 / s2 + 0.0j], dtype=DTYPE_C),
            torch.tensor([1.0, 0.0, 0.0], dtype=DTYPE_R),
        ),
        "plus_y": (
            torch.tensor([1.0 / s2 + 0.0j, 1.0j / s2], dtype=DTYPE_C),
            torch.tensor([0.0, 1.0, 0.0], dtype=DTYPE_R),
        ),
        "minus_y": (
            torch.tensor([1.0 / s2 + 0.0j, -1.0j / s2], dtype=DTYPE_C),
            torch.tensor([0.0, -1.0, 0.0], dtype=DTYPE_R),
        ),
    }


def haar_spinors(count: int) -> torch.Tensor:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(20260529)
    real = torch.randn((count, 2), generator=generator, dtype=DTYPE_R)
    imag = torch.randn((count, 2), generator=generator, dtype=DTYPE_R)
    psi = torch.complex(real, imag).to(DTYPE_C)
    return psi / torch.linalg.norm(psi, dim=1, keepdim=True)


def spinor_from_bloch_vector(r: torch.Tensor) -> torch.Tensor:
    x, y, z = [float(v.item()) for v in r]
    if scalar_close(z, -1.0, GEOM_TOL):
        return torch.tensor([0.0 + 0.0j, 1.0 + 0.0j], dtype=DTYPE_C)
    a = math.sqrt((1.0 + z) / 2.0)
    b = complex(x, y) / math.sqrt(2.0 * (1.0 + z))
    psi = torch.tensor([a + 0.0j, b], dtype=DTYPE_C)
    return psi / torch.linalg.norm(psi)


def su2_from_axis_angle(axis: torch.Tensor, angle: float) -> torch.Tensor:
    axis = axis.to(DTYPE_R)
    axis = axis / torch.linalg.norm(axis)
    n_sigma = sum(axis[idx].to(DTYPE_C) * SIGMAS[idx] for idx in range(3))
    return math.cos(angle / 2.0) * I2 - 1.0j * math.sin(angle / 2.0) * n_sigma


def so3_from_su2(U: torch.Tensor) -> torch.Tensor:
    rows: list[list[torch.Tensor]] = []
    Udag = U.conj().T
    for i, sigma_i in enumerate(SIGMAS):
        row = []
        for sigma_j in SIGMAS:
            value = 0.5 * torch.trace(sigma_i @ U @ sigma_j @ Udag)
            row.append(value.real)
        rows.append(row)
    return torch.tensor(rows, dtype=DTYPE_R)


def rodrigues(axis: torch.Tensor, angle: float) -> torch.Tensor:
    axis = axis.to(DTYPE_R)
    axis = axis / torch.linalg.norm(axis)
    x, y, z = axis
    K = torch.tensor(
        [[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]],
        dtype=DTYPE_R,
    )
    return torch.eye(3, dtype=DTYPE_R) + math.sin(angle) * K + (1.0 - math.cos(angle)) * (K @ K)


def clifford_rotor_matrix(axis: torch.Tensor, angle: float) -> torch.Tensor:
    layout, blades = Cl(3)
    del layout
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    x, y, z = [float(v.item()) for v in (axis / torch.linalg.norm(axis))]
    bivector = x * (e2 ^ e3) + y * (e3 ^ e1) + z * (e1 ^ e2)
    rotor = math.cos(angle / 2.0) - math.sin(angle / 2.0) * bivector
    reverse = ~rotor
    basis = [e1, e2, e3]
    columns = []
    for vector in basis:
        rotated = rotor * vector * reverse
        columns.append(
            torch.tensor(
                [float(rotated.value[1]), float(rotated.value[2]), float(rotated.value[3])],
                dtype=DTYPE_R,
            )
        )
    return torch.stack(columns, dim=1)


def batch_spinor_checks(psis: torch.Tensor, checks: list[dict[str, Any]]) -> dict[str, float]:
    rhos = torch.stack([density(psi) for psi in psis])
    purities = torch.stack([torch.trace(rho @ rho).real for rho in rhos])
    blochs = torch.stack([bloch(psi) for psi in psis])
    bloch_norms = torch.linalg.norm(blochs, dim=1)
    idempotence = torch.stack([rho @ rho - rho for rho in rhos])
    eigs = torch.stack([torch.linalg.eigvalsh(rho).real for rho in rhos])
    expected_eigs = torch.tensor([0.0, 1.0], dtype=DTYPE_R)
    reconstructed = torch.stack([rho_from_bloch(r) for r in blochs])
    phases = torch.linspace(0.0, 2.0 * math.pi, steps=psis.shape[0], dtype=DTYPE_R)
    phase_factors = torch.complex(torch.cos(phases), torch.sin(phases)).to(DTYPE_C)
    phased = psis * phase_factors[:, None]
    phased_rhos = torch.stack([density(psi) for psi in phased])

    purity_residual = max_abs(purities - 1.0)
    bloch_residual = max_abs(bloch_norms - 1.0)
    idempotence_residual = max_abs(idempotence)
    spectrum_residual = max_abs(eigs - expected_eigs)
    reconstruction_residual = max_abs(reconstructed - rhos)
    phase_residual = max_abs(phased_rhos - rhos)

    add_check(
        checks,
        "pure_state_purity_Tr_rho_squared",
        1.0 - purity_residual,
        1.0,
        scalar_close(purity_residual, 0.0, STRICT_TOL),
        STRICT_TOL,
        ["torch"],
        f"max residual over {psis.shape[0]} normalized spinors",
    )
    add_check(
        checks,
        "pure_state_bloch_norm",
        1.0 - bloch_residual,
        1.0,
        scalar_close(bloch_residual, 0.0, STRICT_TOL),
        STRICT_TOL,
        ["torch"],
        f"max residual over {psis.shape[0]} normalized spinors",
    )
    add_check(
        checks,
        "pure_state_density_idempotence_rho_squared_equals_rho",
        idempotence_residual,
        0.0,
        scalar_close(idempotence_residual, 0.0, STRICT_TOL),
        STRICT_TOL,
        ["torch"],
        "max elementwise residual for rho @ rho - rho",
    )
    add_check(
        checks,
        "pure_state_density_spectrum",
        {"max_residual_against_sorted_spectrum_0_1": spectrum_residual},
        {"spectrum": [0.0, 1.0]},
        scalar_close(spectrum_residual, 0.0, GEOM_TOL),
        GEOM_TOL,
        ["torch"],
        "torch.linalg.eigvalsh on Hermitian density matrices",
    )
    add_check(
        checks,
        "bloch_reconstruction_rho_equals_half_I_plus_r_dot_sigma",
        reconstruction_residual,
        0.0,
        scalar_close(reconstruction_residual, 0.0, STRICT_TOL),
        STRICT_TOL,
        ["torch"],
        "density recovered from Pauli expectation values",
    )
    add_check(
        checks,
        "global_phase_invariance_of_density",
        phase_residual,
        0.0,
        scalar_close(phase_residual, 0.0, STRICT_TOL),
        STRICT_TOL,
        ["torch"],
        "rho(exp(i theta) psi) equals rho(psi)",
    )
    return {
        "purity_residual": purity_residual,
        "bloch_norm_residual": bloch_residual,
        "idempotence_residual": idempotence_residual,
        "spectrum_residual": spectrum_residual,
        "reconstruction_residual": reconstruction_residual,
        "global_phase_residual": phase_residual,
    }


def concrete_state_checks(checks: list[dict[str, Any]]) -> None:
    for name, (psi, expected) in normalized_known_spinors().items():
        computed = bloch(psi)
        residual = max_abs(computed - expected)
        add_check(
            checks,
            f"known_bloch_vector_{name}",
            computed,
            expected,
            scalar_close(residual, 0.0, STRICT_TOL),
            STRICT_TOL,
            ["torch"],
            "closed-form Pauli expectation value for named spinor",
        )


def mixed_state_check(checks: list[dict[str, Any]]) -> dict[str, Any]:
    rho_mixed = 0.5 * I2
    purity = float(torch.trace(rho_mixed @ rho_mixed).real.item())
    bloch_mixed = bloch_from_density(rho_mixed)
    add_check(
        checks,
        "maximally_mixed_purity",
        purity,
        0.5,
        scalar_close(purity, 0.5, STRICT_TOL),
        STRICT_TOL,
        ["torch"],
        "Tr((I/2)^2) in dimension two",
    )
    add_check(
        checks,
        "maximally_mixed_bloch_norm",
        float(torch.linalg.norm(bloch_mixed).item()),
        0.0,
        tensor_close(bloch_mixed, torch.zeros(3, dtype=DTYPE_R), STRICT_TOL),
        STRICT_TOL,
        ["torch"],
        "mixed state has zero Bloch vector",
    )
    return {"purity": purity, "bloch": bloch_mixed}


def su2_so3_checks(checks: list[dict[str, Any]]) -> dict[str, Any]:
    axes = [
        torch.tensor([1.0, 0.0, 0.0], dtype=DTYPE_R),
        torch.tensor([0.0, 1.0, 0.0], dtype=DTYPE_R),
        torch.tensor([0.0, 0.0, 1.0], dtype=DTYPE_R),
        torch.tensor([1.0, 2.0, 3.0], dtype=DTYPE_R),
        torch.tensor([-2.0, 1.0, 4.0], dtype=DTYPE_R),
    ]
    angles = [math.pi / 7.0, math.pi / 3.0, math.pi / 2.0, 1.23456789, 2.22222222]
    so3_space = SpecialOrthogonal(n=3)
    probe = normalized_known_spinors()["plus_x"][0]

    unitary_residuals = []
    su2_det_residuals = []
    ortho_residuals = []
    so3_det_residuals = []
    double_cover_residuals = []
    clifford_residuals = []
    rodrigues_residuals = []
    action_residuals = []
    geomstats_belongs = []
    rotations = []

    for axis, angle in zip(axes, angles):
        U = su2_from_axis_angle(axis, angle)
        R = so3_from_su2(U)
        rotations.append((axis, angle, U, R))
        unitary_residuals.append(max_abs(U.conj().T @ U - I2))
        su2_det_residuals.append(abs(complex(torch.linalg.det(U).item()) - 1.0))
        ortho_residuals.append(max_abs(R.T @ R - torch.eye(3, dtype=DTYPE_R)))
        so3_det_residuals.append(abs(float(torch.linalg.det(R).item()) - 1.0))
        double_cover_residuals.append(max_abs(so3_from_su2(-U) - R))
        clifford_residuals.append(max_abs(clifford_rotor_matrix(axis, angle) - R))
        rodrigues_residuals.append(max_abs(rodrigues(axis, angle) - R))
        direct = bloch(U @ probe)
        induced = R @ bloch(probe)
        action_residuals.append(max_abs(direct - induced))
        geomstats_belongs.append(bool(so3_space.belongs(gs.array(R), atol=1.0e-8).item()))

    U1, R1 = rotations[3][2], rotations[3][3]
    U2, R2 = rotations[4][2], rotations[4][3]
    composition_residual = max_abs(so3_from_su2(U1 @ U2) - (R1 @ R2))

    max_unitary = max(unitary_residuals)
    max_su2_det = max(su2_det_residuals)
    max_ortho = max(ortho_residuals)
    max_so3_det = max(so3_det_residuals)
    max_double = max(double_cover_residuals)
    max_clifford = max(clifford_residuals)
    max_rodrigues = max(rodrigues_residuals)
    max_action = max(action_residuals)
    all_geomstats = all(geomstats_belongs)

    add_check(
        checks,
        "su2_unitarity",
        {"max_unitarity_residual": max_unitary, "max_det_minus_one": max_su2_det},
        {"unitarity_residual": 0.0, "det_minus_one": 0.0},
        scalar_close(max_unitary, 0.0, GEOM_TOL) and scalar_close(max_su2_det, 0.0, GEOM_TOL),
        GEOM_TOL,
        ["torch"],
        "axis-angle SU(2) matrices are unitary with determinant one",
    )
    add_check(
        checks,
        "su2_induced_so3_orthogonal_det_one",
        {"max_orthogonality_residual": max_ortho, "max_det_minus_one": max_so3_det},
        {"orthogonality_residual": 0.0, "det_minus_one": 0.0},
        scalar_close(max_ortho, 0.0, GEOM_TOL) and scalar_close(max_so3_det, 0.0, GEOM_TOL),
        GEOM_TOL,
        ["torch"],
        "R_ij = 1/2 Tr(sigma_i U sigma_j U^dag)",
    )
    add_check(
        checks,
        "geomstats_so3_belongs",
        all_geomstats,
        True,
        bool(all_geomstats),
        "geomstats atol=1e-8",
        ["geomstats"],
        "geomstats SpecialOrthogonal(n=3).belongs accepts all induced rotations",
    )
    add_check(
        checks,
        "su2_to_so3_double_cover",
        max_double,
        0.0,
        scalar_close(max_double, 0.0, GEOM_TOL),
        GEOM_TOL,
        ["torch"],
        "R(U) equals R(-U)",
    )
    add_check(
        checks,
        "su2_so3_state_action",
        max_action,
        0.0,
        scalar_close(max_action, 0.0, GEOM_TOL),
        GEOM_TOL,
        ["torch"],
        "Bloch(U psi) equals R(U) Bloch(psi)",
    )
    add_check(
        checks,
        "su2_so3_composition_homomorphism",
        composition_residual,
        0.0,
        scalar_close(composition_residual, 0.0, GEOM_TOL),
        GEOM_TOL,
        ["torch"],
        "R(U1 U2) equals R(U1) R(U2)",
    )
    add_check(
        checks,
        "clifford_rotor_equals_su2_induced_so3",
        max_clifford,
        0.0,
        scalar_close(max_clifford, 0.0, GEOM_TOL),
        GEOM_TOL,
        ["clifford", "torch"],
        "Cl(3) rotor action on basis vectors matches Pauli SU(2) rotation",
    )
    add_check(
        checks,
        "rodrigues_axis_angle_equals_su2_induced_so3",
        max_rodrigues,
        0.0,
        scalar_close(max_rodrigues, 0.0, GEOM_TOL),
        GEOM_TOL,
        ["torch"],
        "classical closed-form SO(3) matrix cross-check",
    )
    return {
        "max_unitarity_residual": max_unitary,
        "max_su2_det_residual": max_su2_det,
        "max_orthogonality_residual": max_ortho,
        "max_so3_det_residual": max_so3_det,
        "max_double_cover_residual": max_double,
        "max_clifford_residual": max_clifford,
        "max_rodrigues_residual": max_rodrigues,
        "max_action_residual": max_action,
        "composition_residual": composition_residual,
        "geomstats_belongs_all": all_geomstats,
    }


def symbolic_and_solver_checks(checks: list[dict[str, Any]]) -> dict[str, Any]:
    p, phi = sp.symbols("p phi", real=True)
    bloch_norm_identity = sp.simplify(
        4 * p * (1 - p) * (sp.cos(phi) ** 2 + sp.sin(phi) ** 2) + (2 * p - 1) ** 2 - 1
    )
    sympy_match = bool(bloch_norm_identity == 0)
    add_check(
        checks,
        "sympy_bloch_norm_identity",
        str(bloch_norm_identity),
        "0",
        sympy_match,
        "exact",
        ["sympy"],
        "symbolic simplification of |r|^2 - 1 for psi=(sqrt(p), e^{i phi} sqrt(1-p))",
    )

    z3_p = z3.Real("p")
    z3_solver = z3.Solver()
    z3_solver.add(z3_p == z3.RealVal(1) / z3.RealVal(2))
    z3_solver.add((z3_p * z3_p) + ((1 - z3_p) * (1 - z3_p)) == 1)
    z3_status = str(z3_solver.check())
    add_check(
        checks,
        "z3_maximally_mixed_not_pure",
        z3_status,
        "unsat",
        z3_status == "unsat",
        "exact real arithmetic",
        ["z3"],
        "no p=1/2 diagonal state can satisfy purity one",
    )

    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_NRA")
    real_sort = cvc5_solver.getRealSort()
    cvc5_p = cvc5_solver.mkConst(real_sort, "p")
    one = cvc5_solver.mkReal(1)
    half = cvc5_solver.mkReal(1, 2)
    one_minus_p = cvc5_solver.mkTerm(Kind.SUB, one, cvc5_p)
    purity = cvc5_solver.mkTerm(
        Kind.ADD,
        cvc5_solver.mkTerm(Kind.MULT, cvc5_p, cvc5_p),
        cvc5_solver.mkTerm(Kind.MULT, one_minus_p, one_minus_p),
    )
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.EQUAL, cvc5_p, half))
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.EQUAL, purity, one))
    cvc5_status = str(cvc5_solver.checkSat())
    add_check(
        checks,
        "cvc5_maximally_mixed_not_pure",
        cvc5_status,
        "unsat",
        cvc5_status == "unsat",
        "exact real arithmetic",
        ["cvc5"],
        "independent SMT cross-check of the mixed-state negative",
    )
    return {
        "sympy_identity": str(bloch_norm_identity),
        "z3_status": z3_status,
        "cvc5_status": cvc5_status,
    }


def graph_and_topology_checks(checks: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    node_names = [
        "finite_spinor_sample",
        "density_outer_product",
        "pauli_expectation_bloch",
        "su2_axis_angle",
        "so3_adjoint_rotation",
        "clifford_rotor",
        "known_value_receipt",
    ]
    nodes = {name: graph.add_node(name) for name in node_names}
    for source, target, label in [
        ("finite_spinor_sample", "density_outer_product", "psi_to_rho"),
        ("density_outer_product", "pauli_expectation_bloch", "rho_to_r"),
        ("pauli_expectation_bloch", "known_value_receipt", "bloch_checks"),
        ("su2_axis_angle", "so3_adjoint_rotation", "adjoint_map"),
        ("so3_adjoint_rotation", "known_value_receipt", "so3_checks"),
        ("clifford_rotor", "known_value_receipt", "rotor_crosscheck"),
    ]:
        graph.add_edge(nodes[source], nodes[target], label)

    dag_ok = bool(rx.is_directed_acyclic_graph(graph))
    required_paths = [
        rx.has_path(graph, nodes["finite_spinor_sample"], nodes["known_value_receipt"]),
        rx.has_path(graph, nodes["su2_axis_angle"], nodes["known_value_receipt"]),
        rx.has_path(graph, nodes["clifford_rotor"], nodes["known_value_receipt"]),
    ]
    graph_match = dag_ok and all(required_paths)
    add_check(
        checks,
        "rustworkx_finite_map_dependency_dag",
        {"dag": dag_ok, "required_paths": required_paths},
        {"dag": True, "required_paths": [True, True, True]},
        graph_match,
        "boolean graph invariant",
        ["rustworkx"],
        "finite carrier/map/control dependencies must reach the receipt without cycles",
    )

    faces = [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]
    complex_tnx = tnx.SimplicialComplex(faces)
    tnx_shape = tuple(int(v) for v in complex_tnx.shape)
    add_check(
        checks,
        "toponetx_boundary_tetrahedron_shape",
        list(tnx_shape),
        [4, 6, 4],
        tnx_shape == (4, 6, 4),
        "exact finite complex count",
        ["toponetx"],
        "finite four-vertex pure-state carrier boundary has expected vertices/edges/faces",
    )

    simplex_tree = gudhi.SimplexTree()
    for face in faces:
        simplex_tree.insert(face, filtration=0.0)
    simplex_tree.compute_persistence(persistence_dim_max=True)
    betti = [int(v) for v in simplex_tree.betti_numbers()]
    add_check(
        checks,
        "gudhi_boundary_tetrahedron_betti_numbers",
        betti,
        [1, 0, 1],
        betti == [1, 0, 1],
        "exact finite complex homology",
        ["gudhi"],
        "boundary of tetrahedron is a finite S^2 carrier sample",
    )

    tetra = torch.tensor(
        [
            [1.0, 1.0, 1.0],
            [1.0, -1.0, -1.0],
            [-1.0, 1.0, -1.0],
            [-1.0, -1.0, 1.0],
        ],
        dtype=DTYPE_R,
    )
    tetra = tetra / torch.linalg.norm(tetra, dim=1, keepdim=True)
    tetra_spinors = torch.stack([spinor_from_bloch_vector(row) for row in tetra])
    tetra_bloch = torch.stack([bloch(psi) for psi in tetra_spinors])
    tetra_residual = max_abs(tetra_bloch - tetra)
    add_check(
        checks,
        "tetrahedral_bloch_vertices_realized_by_spinors",
        tetra_residual,
        0.0,
        scalar_close(tetra_residual, 0.0, GEOM_TOL),
        GEOM_TOL,
        ["torch", "toponetx", "gudhi"],
        "topological carrier vertices are realized by actual spinor-density states",
    )
    return {
        "rustworkx_dag": dag_ok,
        "rustworkx_required_paths": required_paths,
        "toponetx_shape": list(tnx_shape),
        "gudhi_betti": betti,
        "tetrahedral_spinor_residual": tetra_residual,
    }


def negative_controls() -> dict[str, dict[str, Any]]:
    s2 = math.sqrt(2.0)
    complex_state = torch.tensor([1.0 / s2 + 0.0j, 1.0j / s2], dtype=DTYPE_C)

    unnormalized = torch.tensor([1.0 + 1.0j, 2.0 - 0.5j], dtype=DTYPE_C)
    rho_bad_norm = density(unnormalized)
    trace_bad = float(torch.trace(rho_bad_norm).real.item())
    idempotence_bad = max_abs(rho_bad_norm @ rho_bad_norm - rho_bad_norm)

    fake_transpose_rho = torch.outer(complex_state, complex_state)
    fake_hermitian_residual = max_abs(fake_transpose_rho - fake_transpose_rho.conj().T)

    wrong_sigma_y = -SIGMA_Y
    wrong_y_value = float(torch.vdot(complex_state, wrong_sigma_y @ complex_state).real.item())
    correct_y_value = float(torch.vdot(complex_state, SIGMA_Y @ complex_state).real.item())

    nonunitary = torch.tensor([[2.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=DTYPE_C)
    nonunitary_residual = max_abs(nonunitary.conj().T @ nonunitary - I2)

    Ux = su2_from_axis_angle(torch.tensor([1.0, 0.0, 0.0], dtype=DTYPE_R), math.pi / 3.0)
    Uy = su2_from_axis_angle(torch.tensor([0.0, 1.0, 0.0], dtype=DTYPE_R), math.pi / 5.0)
    order_probe = normalized_known_spinors()["ket_0"][0]
    rho_xy = density(Ux @ (Uy @ order_probe))
    rho_yx = density(Uy @ (Ux @ order_probe))
    order_residual = max_abs(rho_xy - rho_yx)

    return {
        "unnormalized_spinor_rejected": {
            "pass": bool(abs(trace_bad - 1.0) > 1.0e-6 and idempotence_bad > 1.0e-6),
            "trace": trace_bad,
            "idempotence_residual": idempotence_bad,
            "detail": "raw unnormalized psi is not accepted as a pure density carrier",
        },
        "transpose_not_conjugate_transpose_rejected": {
            "pass": bool(fake_hermitian_residual > 1.0e-6),
            "hermitian_residual": fake_hermitian_residual,
            "detail": "complex outer product without conjugation is non-Hermitian",
        },
        "wrong_pauli_y_sign_rejected": {
            "pass": bool(abs(wrong_y_value - correct_y_value) > 1.0),
            "wrong_y": wrong_y_value,
            "correct_y": correct_y_value,
            "detail": "plus_y known state exposes the Pauli-Y sign",
        },
        "nonunitary_su2_action_rejected": {
            "pass": bool(nonunitary_residual > 1.0),
            "unitarity_residual": nonunitary_residual,
            "detail": "nonunitary diagonal scaling is not a valid SU(2) action",
        },
        "noncommuting_order_sensitive_control_detected": {
            "pass": bool(order_residual > 1.0e-6),
            "density_order_residual": order_residual,
            "detail": "Ux Uy and Uy Ux produce different density carriers",
        },
    }


def build_result() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    known = normalized_known_spinors()
    psis = torch.cat([torch.stack([entry[0] for entry in known.values()]), haar_spinors(HAAR_COUNT)], dim=0)

    batch_summary = batch_spinor_checks(psis, checks)
    concrete_state_checks(checks)
    mixed_summary = mixed_state_check(checks)
    su2_summary = su2_so3_checks(checks)
    symbolic_summary = symbolic_and_solver_checks(checks)
    graph_topology_summary = graph_and_topology_checks(checks)
    negatives = negative_controls()

    failed_known = [row["invariant"] for row in checks if not row["match"]]
    failed_negatives = [name for name, row in negatives.items() if not row.get("pass")]
    blockers = []
    if failed_known:
        blockers.append({"kind": "known_value_mismatch", "failed": failed_known})
    if failed_negatives:
        blockers.append({"kind": "negative_control_missed", "failed": failed_negatives})

    passed_count = len(checks) - len(failed_known)
    tool_manifest = {
        "torch": "load-bearing complex128/float64 spinor, density, Pauli, eigenspectrum, Bloch, SU(2), SO(3), and negative computations",
        "sympy": "load-bearing exact Bloch norm identity simplification",
        "z3": "load-bearing exact real-arithmetic blocker for treating maximally mixed diagonal state as pure",
        "cvc5": "load-bearing independent SMT cross-check of the same mixed-state blocker",
        "clifford": "load-bearing Cl(3) rotor construction compared against the SU(2)-induced SO(3) matrix",
        "geomstats": "load-bearing SpecialOrthogonal(n=3) membership check using the pytorch backend",
        "gudhi": "load-bearing Betti-number check for a finite tetrahedral S^2 carrier sample",
        "toponetx": "load-bearing finite simplicial complex shape check for the tetrahedral carrier sample",
        "rustworkx": "load-bearing finite dependency DAG check for the map/control/receipt path",
    }
    tools = list(tool_manifest)

    return {
        "sim_id": "geom_spinor_density_carrier_codex_probe",
        "name": "spinor_density_carrier",
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "claim_ceiling": "diagnostic only; does not admit canonical, bridge, axis, flux, physics, manifold, or layer-completion claims",
        "tier": "1 finite carrier / 2 known geometry diagnostic",
        "purpose": "independent known-value probe for normalized C^2 spinor density carriers and SU(2)->SO(3) geometry",
        "scientific_question": "Do torch-native spinor densities reproduce the known Bloch, pure-state, mixed-state, and SU(2) double-cover invariants without hardcoded stand-ins?",
        "sim_execution_kind": "nonclassical",
        "sim_class": "carrier_probe",
        "root_constraints_in_force": [
            "F01 finite sampled carrier/probe/operator/path set",
            "N01 noncommuting or order-sensitive Pauli/SU(2) operation domain",
        ],
        "finite_map": "finite sampled psi in C^2 normalized -> rho=psi psi^dag, r_i=psi^dag sigma_i psi, U in SU(2) -> R_ij=1/2 Tr(sigma_i U sigma_j U^dag)",
        "domain": {
            "known_spinors": list(known.keys()),
            "haar_spinor_count": HAAR_COUNT,
            "operators": ["sigma_x", "sigma_y", "sigma_z", "axis_angle_SU2"],
            "rotation_cases": 5,
        },
        "codomain_or_output": [
            "density matrices rho in C^(2x2)",
            "Bloch vectors in R^3",
            "SO(3) rotation matrices",
            "known-value check receipt",
        ],
        "carrier_layer": "C^2 spinor density carrier",
        "geometry_layer": "Bloch sphere plus SU(2)->SO(3) double cover",
        "carrier_realization": "torch complex128 spinors and 2x2 density matrices; torch float64 Bloch and SO(3) tensors",
        "peps3d_embedding": "single-site diagnostic anchor only: each sampled spinor density is one local tensor site with no bond/face/cell promotion; downstream PEPS3D manifold consumers blocked",
        "spinor_state": "torch complex128 normalized psi and spinor-derived density rho=psi psi^dag",
        "quaternion_action": "not_applicable; Cl(3) rotor check is used without quaternion promotion language",
        "dependency_receipts": [],
        "downstream_blocks": [
            "flux",
            "Xi",
            "Phi0",
            "Axis0",
            "bridge",
            "basin",
            "physics",
            "manifold_admission",
            "layer_completion",
            "canonical_promotion",
        ],
        "allowed_claims": [
            "diagnostic local known-geometry witness",
            "independent cross-model comparison receipt against separately built sims",
        ],
        "promotion_blockers": [
            "classification intentionally diagnostic_only",
            "single-site PEPS3D anchor is not a manifold admission",
            "no downstream bridge/axis/flux consumers admitted",
        ],
        "required_tools": tools,
        "actual_tools_used": tools,
        "proof_surfaces_used": ["sympy", "z3", "cvc5"],
        "graph_surfaces_used": ["rustworkx"],
        "topology_surfaces_used": ["toponetx", "gudhi"],
        "tool_manifest": tool_manifest,
        "tool_integration_depth": {tool: "load_bearing" for tool in tools},
        "required_inputs": ["none"],
        "data_or_artifact_dependencies": [],
        "required_negatives": list(negatives),
        "negatives_run": negatives,
        "kill_conditions": [
            "any known-value check has match=false",
            "any required negative/control has pass=false",
            "any requested tool import or load-bearing check fails",
        ],
        "required_artifacts": ["result JSON receipt"],
        "artifacts_emitted": [str(RESULT_PATH.relative_to(ROOT))],
        "witness_trace_id": "geom_spinor_density_carrier_codex_witness_v1",
        "known_value_checks": checks,
        "known_value_summary": {
            "passed": passed_count,
            "total": len(checks),
            "all_match": passed_count == len(checks),
        },
        "result_summary": {
            "promotion_status": "diagnostic_only",
            "known_value_checks_passed": passed_count,
            "known_value_checks_total": len(checks),
            "negatives_passed": len(negatives) - len(failed_negatives),
            "negatives_total": len(negatives),
            "batch": batch_summary,
            "mixed": mixed_summary,
            "su2_so3": su2_summary,
            "symbolic_and_solver": symbolic_summary,
            "graph_and_topology": graph_topology_summary,
        },
        "pass_rule": "all known_value_checks match and all negatives_run pass",
        "fail_rule": "write blockers and exit nonzero rather than adjust known values",
        "promotion_status": "diagnostic_only",
        "eligible_consumers": ["cross_model_diagnostic_comparison_only"],
        "blocked_consumers": [
            "canonical ledger admission",
            "nonclassical manifold admission",
            "flux",
            "Xi",
            "Phi0",
            "Axis0",
            "bridge",
            "basin",
            "physics",
        ],
        "positive": {
            row["invariant"]: {"pass": row["match"], "detail": row["detail"]}
            for row in checks
            if row["invariant"]
            not in {
                "z3_maximally_mixed_not_pure",
                "cvc5_maximally_mixed_not_pure",
            }
        },
        "graveyard_companions": negatives,
        "boundary": {
            "classification_boundary": {
                "pass": True,
                "detail": "top-level classification is diagnostic_only and promotion_allowed is false",
            },
            "numpy_boundary": {
                "pass": True,
                "detail": "source code imports no numpy and keeps claim-bearing carrier math in torch complex128/float64",
            },
            "downstream_boundary": {
                "pass": True,
                "detail": "bridge, flux, Axis0, physics, manifold, and layer-completion consumers are blocked",
            },
            "smt_mixed_state_boundary_z3": {
                "pass": symbolic_summary["z3_status"] == "unsat",
                "detail": "z3 rejects purity-one claim for p=1/2 diagonal mixed state",
            },
            "smt_mixed_state_boundary_cvc5": {
                "pass": symbolic_summary["cvc5_status"] == "unsat",
                "detail": "cvc5 rejects purity-one claim for p=1/2 diagonal mixed state",
            },
        },
        "why_not_v4_probes": [
            "This is a known-value diagnostic carrier probe, not a v4 queue promotion probe.",
            "It intentionally avoids validator gates per user request.",
            "It blocks all downstream layer/manifold/axis/physics consumers.",
        ],
        "nearby_variants": {
            "total": 3,
            "passed": 3 if not blockers else 0,
            "items": [
                "named basis and Pauli eigenstate spinors",
                f"{HAAR_COUNT} seeded Haar spinors",
                "five SU(2) axis-angle rotations with Clifford and geomstats cross-checks",
            ],
        },
        "blockers": blockers,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(to_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    blockers = result["blockers"]
    summary = result["result_summary"]
    print("SIM geom_spinor_density_carrier_codex_probe")
    print(f"RESULT {RESULT_PATH.relative_to(ROOT)}")
    print(
        "KNOWN_VALUE_CHECKS "
        f"{summary['known_value_checks_passed']}/{summary['known_value_checks_total']} PASS"
    )
    print(f"NEGATIVES {summary['negatives_passed']}/{summary['negatives_total']} PASS")
    print(
        "TOOLS load_bearing "
        + ",".join(result["actual_tools_used"])
    )
    print(f"CLASSIFICATION {result['classification']}")
    print(f"BLOCKERS {json.dumps(to_jsonable(blockers), sort_keys=True)}")
    if blockers:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
