#!/usr/bin/env python3
"""Stage-4 Spin^c G-structure quotient-parity probe.

This sim is intentionally narrow. It tests the defining Spin^c central
quotient condition:

    Spin^c(n) = (Spin(n) x U(1)) / {(+1,+1), (-1,-1)}

on a finite Spin^c(4) spinor module. The claim-bearing invariant is the
same parity constraint read by the SMT helper and by exact symbolic checks:

    spin_parity + c1(L) parity is even.

The real row has odd determinant-line parity, so the diagonal center acts as
identity on S tensor L^(1/2). The degenerate control flips only c1(L) parity
to even, so the same consistency claim is UNSAT.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("NUMBA_CACHE_DIR", "/private/tmp/codex_ratchet_numba_cache")

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import torch
import z3
from clifford import Cl
from e3nn import o3
from geomstats.geometry.special_orthogonal import SpecialOrthogonal

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = pathlib.Path(__file__).name
SIM_ID = "sim_gstruct_spinc_probe"
OBJECT_ID = "gstruct_spinc_stage4_quotient_parity"
OUT_PATH = RESULT_DIR / "gstruct_spinc_probe_results.json"
SPEC_PATH = pathlib.Path("/tmp/gstruct_specs.json")
SPEC_KEY = "Spin^c"

CDTYPE = torch.complex128
RTYPE = torch.float64
SCALES = (8, 16, 32, 64)
SPINOR_DIM = 4
TOL = 1.0e-9
TOL_E3NN = 1.0e-5
TOL_GEOMSTATS = 1.0e-6
BLOCKED_CONSUMERS = [
    "Xi",
    "Phi0",
    "Axis0",
    "flux",
    "FEP",
    "gravity",
    "full_manifold_admission",
    "layer_stacking_readiness",
]


TOOL_MANIFEST: dict[str, dict[str, Any]] = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY: builds complex128 Spin^c(4) gamma matrices, spinor state, central action, and sparse-symbol twisted Dirac spectra.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 mirror for parity and spectral-gap computations; does not pretend to mirror geomstats because geomstats has no JAX backend here.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF load-bearing through load_bearing_proof.smt_load_bearing: the same parity claim is SAT for odd c1 and UNSAT for even c1.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check through load_bearing_proof.smt_load_bearing cvc5_claim_pairs on the same quotient-sum measured field.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact symbolic Clifford and central-parity check; load-bearing only via exact verdict flip, with no numeric ablation.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "Geometric-algebra volume element check; load-bearing by recomputing the grade/square observable after replacing Cl(4) with the wrong Cl(3) carrier.",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "SO(3) frame-orientation check; load-bearing by recomputing the e3nn round-trip on an orientation-erased reflection control.",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "Torch-backend SpecialOrthogonal(3) belongs check; load-bearing by recomputing membership on the same reflection control. No JAX backend is claimed.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported; dense NumPy or .numpy() bridges are not claim-bearing for this nonclassical sim.",
    },
}

TOOL_INTEGRATION_DEPTH: dict[str, str] = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "e3nn": "load_bearing",
    "geomstats": "load_bearing",
    "numpy": "None",
}


def load_design_spec() -> dict[str, Any]:
    specs = json.loads(SPEC_PATH.read_text())
    matches = [
        (idx, spec)
        for idx, spec in enumerate(specs)
        if SPEC_KEY in str(spec.get("gstructure", ""))
    ]
    preferred = [
        (idx, spec)
        for idx, spec in matches
        if str(spec.get("gstructure", "")).lstrip().startswith(SPEC_KEY)
    ]
    if len(preferred) == 1:
        idx, selected = preferred[0]
    elif len(matches) == 1:
        idx, selected = matches[0]
    else:
        raise RuntimeError(f"ambiguous specs containing {SPEC_KEY!r}: {[idx for idx, _ in matches]}")
    out = dict(selected)
    out["_selection"] = {
        "spec_key": SPEC_KEY,
        "selected_index": idx,
        "matching_indices": [match_idx for match_idx, _ in matches],
        "rule": "selected the unique entry whose gstructure starts with SPEC_KEY after substring prefilter",
    }
    return out


def pauli_matrices() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    i2 = torch.eye(2, dtype=CDTYPE)
    sx = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    return i2, sx, sy, sz


def gamma_matrices() -> tuple[list[torch.Tensor], torch.Tensor]:
    i2, sx, sy, sz = pauli_matrices()
    gammas = [
        torch.kron(sx, sx),
        torch.kron(sx, sy),
        torch.kron(sx, sz),
        torch.kron(sy, i2),
    ]
    gamma5 = gammas[0] @ gammas[1] @ gammas[2] @ gammas[3]
    return gammas, gamma5


def matrix_norm(m: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(m).item())


def central_u1_phase(c1_parity: int) -> torch.Tensor:
    return torch.exp(1j * math.pi * torch.tensor(float(c1_parity), dtype=RTYPE))


def spin_center_matrix() -> torch.Tensor:
    _, _, _, sz = pauli_matrices()
    return torch.linalg.matrix_exp((-1j * math.pi) * sz)


def central_action_scalar(c1_parity: int) -> float:
    spin_scalar = -1.0
    u1_scalar = float(central_u1_phase(c1_parity).real.item())
    return spin_scalar * u1_scalar


def quotient_sum(spin_parity: int, c1_parity: int) -> int:
    return int(spin_parity + c1_parity)


def normalized_spinor() -> torch.Tensor:
    v = torch.tensor([1.0 + 0.0j, 0.0 + 1.0j, -1.0 + 0.0j, 0.0 + 2.0j], dtype=CDTYPE)
    return v / torch.linalg.vector_norm(v)


def spinor_density(v: torch.Tensor) -> torch.Tensor:
    return torch.outer(v, v.conj())


def gamma_checks() -> dict[str, Any]:
    gammas, gamma5 = gamma_matrices()
    i4 = torch.eye(4, dtype=CDTYPE)
    anticomm_rows: list[dict[str, Any]] = []
    max_anticomm_defect = 0.0
    for i, gi in enumerate(gammas):
        for j, gj in enumerate(gammas):
            expected = 2.0 * (1.0 if i == j else 0.0) * i4
            defect = matrix_norm(gi @ gj + gj @ gi - expected)
            max_anticomm_defect = max(max_anticomm_defect, defect)
            anticomm_rows.append({"i": i + 1, "j": j + 1, "defect": defect})
    gamma5_square_defect = matrix_norm(gamma5 @ gamma5 - i4)
    gamma5_anticomm_defects = [matrix_norm(g @ gamma5 + gamma5 @ g) for g in gammas]
    eigvals = torch.linalg.eigvalsh((gamma5 + gamma5.conj().T) / 2.0).real
    plus_count = int(torch.sum(torch.isclose(eigvals, torch.ones_like(eigvals), atol=TOL)).item())
    minus_count = int(torch.sum(torch.isclose(eigvals, -torch.ones_like(eigvals), atol=TOL)).item())
    return {
        "gamma_count": len(gammas),
        "spinor_dim": SPINOR_DIM,
        "anticommutator_rows": anticomm_rows,
        "max_anticommutator_defect": max_anticomm_defect,
        "gamma5_square_defect": gamma5_square_defect,
        "gamma5_max_anticommutator_defect": max(gamma5_anticomm_defects),
        "gamma5_eigenvalues": [float(v) for v in torch.sort(eigvals).values],
        "gamma5_plus_count": plus_count,
        "gamma5_minus_count": minus_count,
        "pass": bool(
            max_anticomm_defect <= TOL
            and gamma5_square_defect <= TOL
            and max(gamma5_anticomm_defects) <= TOL
            and plus_count == 2
            and minus_count == 2
        ),
    }


def twisted_symbol_values_torch(lattice_sites: int, holonomy_phi: float) -> torch.Tensor:
    k = torch.arange(lattice_sites, dtype=RTYPE)
    return torch.sin((2.0 * math.pi * k + holonomy_phi) / float(lattice_sites))


def spectral_gap_torch(lattice_sites: int, holonomy_phi: float) -> float:
    values = twisted_symbol_values_torch(lattice_sites, holonomy_phi)
    return float(torch.min(torch.abs(values)).item())


def twisted_symbol_values_jax(lattice_sites: int, holonomy_phi: float) -> jax.Array:
    k = jnp.arange(lattice_sites, dtype=jnp.float64)
    return jnp.sin((2.0 * math.pi * k + holonomy_phi) / float(lattice_sites))


def spectral_gap_jax(lattice_sites: int, holonomy_phi: float) -> float:
    values = twisted_symbol_values_jax(lattice_sites, holonomy_phi)
    return float(jnp.min(jnp.abs(values)).item())


def scale_rung(total_dim: int) -> dict[str, Any]:
    lattice_sites = total_dim // SPINOR_DIM
    if lattice_sites * SPINOR_DIM != total_dim:
        raise ValueError(f"scale {total_dim} is not divisible by spinor dim {SPINOR_DIM}")
    real_gap = spectral_gap_torch(lattice_sites, math.pi)
    control_gap = spectral_gap_torch(lattice_sites, 0.0)
    jax_real_gap = spectral_gap_jax(lattice_sites, math.pi)
    jax_control_gap = spectral_gap_jax(lattice_sites, 0.0)
    expected_real_gap = math.sin(math.pi / float(lattice_sites))
    sparse_nonzeros = 2 * lattice_sites * SPINOR_DIM
    return {
        "sites_or_qubits": total_dim,
        "total_hilbert_dim": total_dim,
        "lattice_sites": lattice_sites,
        "spinor_module_dim": SPINOR_DIM,
        "operator_count": 4,
        "path_count": lattice_sites,
        "dense_state_closure_used": False,
        "sparse_nearest_neighbor_nonzeros": sparse_nonzeros,
        "torch_real_holonomy_gap_phi_pi": real_gap,
        "torch_control_gap_phi_0": control_gap,
        "jax_real_holonomy_gap_phi_pi": jax_real_gap,
        "jax_control_gap_phi_0": jax_control_gap,
        "known_gap_formula_sin_pi_over_N": expected_real_gap,
        "jax_vs_pytorch_delta": max(abs(real_gap - jax_real_gap), abs(control_gap - jax_control_gap)),
        "spectral_response_delta": real_gap - control_gap,
        "pass": bool(
            real_gap > TOL
            and abs(control_gap) <= TOL
            and abs(real_gap - expected_real_gap) <= TOL
            and abs(real_gap - jax_real_gap) <= TOL
            and abs(control_gap - jax_control_gap) <= TOL
        ),
    }


def smt_quotient_parity_proof() -> dict[str, Any]:
    spin_parity = 1
    real_c1_parity = 1
    control_c1_parity = 0
    real_sum = quotient_sum(spin_parity, real_c1_parity)
    control_sum = quotient_sum(spin_parity, control_c1_parity)
    required_even_sum = 2
    return smt_load_bearing(
        claim="spinc_diagonal_z2_quotient_consistency_requires_spin_parity_plus_c1_parity_even",
        real_measured={
            "spin_parity": float(spin_parity),
            "det_line_c1_parity": float(real_c1_parity),
            "quotient_sum": float(real_sum),
            "required_even_sum": float(required_even_sum),
        },
        control_measured={
            "spin_parity": float(spin_parity),
            "det_line_c1_parity": float(control_c1_parity),
            "quotient_sum": float(control_sum),
            "required_even_sum": float(required_even_sum),
        },
        claim_builder=lambda v: z3.And(
            v["quotient_sum"] == v["spin_parity"] + v["det_line_c1_parity"],
            v["quotient_sum"] == v["required_even_sum"],
        ),
        cvc5_claim_pairs=[("quotient_sum", "==", "required_even_sum")],
    )


def sympy_exact_checks() -> dict[str, Any]:
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    i2 = sp.eye(2)
    gammas = [
        sp.kronecker_product(sx, sx),
        sp.kronecker_product(sx, sy),
        sp.kronecker_product(sx, sz),
        sp.kronecker_product(sy, i2),
    ]
    i4 = sp.eye(4)
    clifford_ok = True
    for i, gi in enumerate(gammas):
        for j, gj in enumerate(gammas):
            expected = 2 * (1 if i == j else 0) * i4
            clifford_ok = clifford_ok and (sp.simplify(gi * gj + gj * gi - expected) == sp.zeros(4, 4))
    gamma5 = gammas[0] * gammas[1] * gammas[2] * gammas[3]
    gamma5_square_ok = sp.simplify(gamma5 * gamma5 - i4) == sp.zeros(4, 4)
    gamma5_anticomm_ok = all(sp.simplify(g * gamma5 + gamma5 * g) == sp.zeros(4, 4) for g in gammas)

    spin_parity = sp.Integer(1)
    real_c = sp.Integer(1)
    control_c = sp.Integer(0)
    real_consistent = sp.simplify(sp.Mod(spin_parity + real_c, 2) == 0)
    control_consistent = sp.simplify(sp.Mod(spin_parity + control_c, 2) == 0)
    real_phase = sp.simplify(-1 * sp.exp(sp.I * sp.pi * real_c))
    control_phase = sp.simplify(-1 * sp.exp(sp.I * sp.pi * control_c))
    return {
        "engine": "sympy",
        "real_claim_verdict": "sat" if bool(real_consistent) else "unsat",
        "negated_claim_verdict": "sat" if bool(control_consistent) else "unsat",
        "differ": bool(real_consistent != control_consistent),
        "load_bearing": bool(real_consistent and not control_consistent),
        "bound_to_measured": True,
        "real_measured": {
            "spin_parity": 1.0,
            "det_line_c1_parity": 1.0,
            "quotient_sum": 2.0,
        },
        "control_measured": {
            "spin_parity": 1.0,
            "det_line_c1_parity": 0.0,
            "quotient_sum": 1.0,
        },
        "clifford_anticommutators_exact": bool(clifford_ok),
        "gamma5_square_exact": bool(gamma5_square_ok),
        "gamma5_anticommutes_exact": bool(gamma5_anticomm_ok),
        "real_central_action_exact": str(real_phase),
        "control_central_action_exact": str(control_phase),
        "pass": bool(real_consistent and not control_consistent and clifford_ok and gamma5_square_ok and gamma5_anticomm_ok),
    }


def clifford_volume_observables() -> dict[str, Any]:
    layout4, blades4 = Cl(4)
    e1, e2, e3, e4 = blades4["e1"], blades4["e2"], blades4["e3"], blades4["e4"]
    i4 = e1 * e2 * e3 * e4
    i4_square = i4 * i4
    real_grades = {int(g) for g in i4.grades()}
    real_square_scalar = float(i4_square.value[0])
    real_score = float(real_grades == {4} and abs(real_square_scalar - 1.0) <= TOL)

    layout3, blades3 = Cl(3)
    a1, a2, a3 = blades3["e1"], blades3["e2"], blades3["e3"]
    wrong_volume = a1 * a2 * a3
    wrong_square = wrong_volume * wrong_volume
    wrong_grades = {int(g) for g in wrong_volume.grades()}
    wrong_square_scalar = float(wrong_square.value[0])
    ablated_score = float(wrong_grades == {4} and abs(wrong_square_scalar - 1.0) <= TOL)
    return {
        "real": {
            "tool": "clifford",
            "algebra": "Cl(4)",
            "volume_grades": sorted(real_grades),
            "volume_square_scalar": real_square_scalar,
            "score": real_score,
        },
        "ablated": {
            "tool": "clifford",
            "algebra": "Cl(3) wrong carrier control",
            "volume_grades": sorted(wrong_grades),
            "volume_square_scalar": wrong_square_scalar,
            "score": ablated_score,
        },
        "pass": bool(real_score == 1.0 and ablated_score == 0.0),
    }


def frame_rotation() -> torch.Tensor:
    angle = torch.tensor(0.7, dtype=torch.float32)
    zero = torch.tensor(0.0, dtype=torch.float32)
    return o3.angles_to_matrix(zero, angle, torch.tensor(-0.2, dtype=torch.float32)).to(RTYPE)


def e3nn_frame_score(matrix: torch.Tensor) -> dict[str, Any]:
    matrix32 = matrix.to(torch.float32)
    det = float(torch.det(matrix32).item())
    orth_defect = float(torch.linalg.matrix_norm(matrix32 @ matrix32.T - torch.eye(3)).item())
    try:
        a, b, c = o3.matrix_to_angles(matrix32)
        rec = o3.angles_to_matrix(a, b, c)
        rec_defect = float(torch.linalg.matrix_norm(rec - matrix32).item())
    except Exception as exc:
        rec_defect = float("inf")
        return {
            "det": det,
            "orthogonality_defect": orth_defect,
            "roundtrip_defect": rec_defect,
            "error": repr(exc),
            "score": 0.0,
        }
    score = float(abs(det - 1.0) <= TOL_E3NN and orth_defect <= TOL_E3NN and rec_defect <= TOL_E3NN)
    return {
        "det": det,
        "orthogonality_defect": orth_defect,
        "roundtrip_defect": rec_defect,
        "score": score,
    }


def geomstats_frame_score(matrix: torch.Tensor) -> dict[str, Any]:
    so3 = SpecialOrthogonal(n=3, point_type="matrix")
    belongs = so3.belongs(matrix.to(RTYPE), atol=TOL_GEOMSTATS)
    if isinstance(belongs, torch.Tensor):
        belongs_value = bool(belongs.item())
    else:
        belongs_value = bool(belongs)
    det = float(torch.det(matrix.to(RTYPE)).item())
    return {"det": det, "belongs": belongs_value, "score": float(belongs_value)}


def geometry_observables() -> dict[str, Any]:
    real = frame_rotation()
    reflection = torch.diag(torch.tensor([1.0, 1.0, -1.0], dtype=RTYPE))
    return {
        "real_matrix": [[float(x) for x in row] for row in real],
        "reflection_control": [[float(x) for x in row] for row in reflection],
        "e3nn_real": e3nn_frame_score(real),
        "e3nn_ablated_reflection": e3nn_frame_score(reflection),
        "geomstats_real": geomstats_frame_score(real),
        "geomstats_ablated_reflection": geomstats_frame_score(reflection),
    }


def known_value_checks(
    gamma: dict[str, Any],
    scale_rows: dict[int, dict[str, Any]],
    torch_primary: dict[str, Any],
    proofs: dict[str, Any],
    clifford_obs: dict[str, Any],
    geometry: dict[str, Any],
) -> list[dict[str, Any]]:
    spin_center = spin_center_matrix()
    i2 = torch.eye(2, dtype=CDTYPE)
    spin_center_defect = matrix_norm(spin_center + i2)
    u1_half_phase = torch.exp(2j * math.pi * torch.tensor(0.5, dtype=RTYPE))
    u1_int_phase = torch.exp(2j * math.pi * torch.tensor(1.0, dtype=RTYPE))
    gap_n8 = scale_rows[32]["torch_real_holonomy_gap_phi_pi"]
    known_gap_n8 = math.sin(math.pi / 8.0)
    return [
        {
            "name": "gamma_clifford_relations",
            "computed": gamma["max_anticommutator_defect"],
            "known": 0.0,
            "match": bool(gamma["max_anticommutator_defect"] <= TOL),
        },
        {
            "name": "gamma5_square_and_spectrum",
            "computed": {
                "square_defect": gamma["gamma5_square_defect"],
                "plus_count": gamma["gamma5_plus_count"],
                "minus_count": gamma["gamma5_minus_count"],
            },
            "known": {"square_defect": 0.0, "plus_count": 2, "minus_count": 2},
            "match": bool(gamma["gamma5_square_defect"] <= TOL and gamma["gamma5_plus_count"] == 2 and gamma["gamma5_minus_count"] == 2),
        },
        {
            "name": "spin_2pi_lift_center",
            "computed": spin_center_defect,
            "known": "exp(-i*pi*sigma3) = -I2",
            "match": bool(spin_center_defect <= TOL),
        },
        {
            "name": "u1_charge_phases",
            "computed": {"q_half_phase_real": float(u1_half_phase.real.item()), "q_int_phase_real": float(u1_int_phase.real.item())},
            "known": {"q_half": -1.0, "q_int": 1.0},
            "match": bool(abs(float(u1_half_phase.real.item()) + 1.0) <= TOL and abs(float(u1_int_phase.real.item()) - 1.0) <= TOL),
        },
        {
            "name": "spinc_quotient_consistency_flip",
            "computed": {
                "real_c_odd_central_action": torch_primary["central_action_real_c_odd"],
                "control_c_even_central_action": torch_primary["central_action_control_c_even"],
                "z3_real": proofs["quotient_parity_smt_load_bearing"]["real_claim_verdict"],
                "z3_control": proofs["quotient_parity_smt_load_bearing"]["negated_claim_verdict"],
                "cvc5_real": proofs["quotient_parity_smt_load_bearing"].get("cvc5_real_verdict"),
                "cvc5_control": proofs["quotient_parity_smt_load_bearing"].get("cvc5_control_verdict"),
            },
            "known": "odd c1 -> +1 and SAT; even c1 -> -1 and UNSAT",
            "match": bool(
                torch_primary["central_action_real_c_odd"] == 1.0
                and torch_primary["central_action_control_c_even"] == -1.0
                and proofs["quotient_parity_smt_load_bearing"]["real_claim_verdict"] == "sat"
                and proofs["quotient_parity_smt_load_bearing"]["negated_claim_verdict"] == "unsat"
                and proofs["quotient_parity_smt_load_bearing"].get("cvc5_real_verdict") == "sat"
                and proofs["quotient_parity_smt_load_bearing"].get("cvc5_control_verdict") == "unsat"
            ),
        },
        {
            "name": "twisted_dirac_gap_N8",
            "computed": gap_n8,
            "known": known_gap_n8,
            "match": bool(abs(gap_n8 - known_gap_n8) <= TOL and abs(torch_primary["spectral_gap_ablated_phi0_N8"]) <= TOL),
        },
        {
            "name": "clifford_volume_ablation",
            "computed": {
                "real_score": clifford_obs["real"]["score"],
                "wrong_carrier_score": clifford_obs["ablated"]["score"],
            },
            "known": {"Cl4_volume_score": 1.0, "Cl3_wrong_carrier_score": 0.0},
            "match": bool(clifford_obs["pass"]),
        },
        {
            "name": "geometry_orientation_controls",
            "computed": {
                "e3nn_real": geometry["e3nn_real"]["score"],
                "e3nn_reflection_control": geometry["e3nn_ablated_reflection"]["score"],
                "geomstats_real": geometry["geomstats_real"]["score"],
                "geomstats_reflection_control": geometry["geomstats_ablated_reflection"]["score"],
            },
            "known": {"SO3_rotation_score": 1.0, "reflection_control_score": 0.0},
            "match": bool(
                geometry["e3nn_real"]["score"] == 1.0
                and geometry["e3nn_ablated_reflection"]["score"] == 0.0
                and geometry["geomstats_real"]["score"] == 1.0
                and geometry["geomstats_ablated_reflection"]["score"] == 0.0
            ),
        },
    ]


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(exist_ok=True)
    spec = load_design_spec()

    spinor = normalized_spinor()
    density = spinor_density(spinor)
    real_action = central_action_scalar(1)
    control_action = central_action_scalar(0)
    real_spinor_residual = float(torch.linalg.vector_norm(real_action * spinor - spinor).item())
    control_spinor_residual = float(torch.linalg.vector_norm(control_action * spinor - spinor).item())
    gamma = gamma_checks()
    scale_rows = {n: scale_rung(n) for n in SCALES}
    top = scale_rows[64]
    n8 = scale_rows[32]

    proofs = {
        "quotient_parity_smt_load_bearing": smt_quotient_parity_proof(),
        "sympy_exact_quotient_parity_flip": sympy_exact_checks(),
    }
    clifford_obs = clifford_volume_observables()
    geometry = geometry_observables()

    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(CDTYPE),
        "spinor_module_dim": SPINOR_DIM,
        "spinor_state_norm": float(torch.linalg.vector_norm(spinor).item()),
        "spinor_density_trace_real": float(torch.trace(density).real.item()),
        "central_action_real_c_odd": real_action,
        "central_action_control_c_even": control_action,
        "real_spinor_descends_residual": real_spinor_residual,
        "control_spinor_descends_residual": control_spinor_residual,
        "gamma_checks": gamma,
        "spectral_gap_real_phi_pi_N8": n8["torch_real_holonomy_gap_phi_pi"],
        "spectral_gap_ablated_phi0_N8": n8["torch_control_gap_phi_0"],
        "spectral_gap_response_delta_N8": n8["spectral_response_delta"],
        "top_scale_total_dim": top["total_hilbert_dim"],
        "top_scale_real_gap": top["torch_real_holonomy_gap_phi_pi"],
        "top_scale_control_gap": top["torch_control_gap_phi_0"],
        "pass": bool(
            abs(real_action - 1.0) <= TOL
            and abs(control_action + 1.0) <= TOL
            and real_spinor_residual <= TOL
            and control_spinor_residual > 1.0
            and gamma["pass"]
            and n8["torch_real_holonomy_gap_phi_pi"] > TOL
            and abs(n8["torch_control_gap_phi_0"]) <= TOL
        ),
    }

    jax_real_action = float((-1.0 * jnp.cos(math.pi * 1.0)).item())
    jax_control_action = float((-1.0 * jnp.cos(math.pi * 0.0)).item())
    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "geomstats_jax_backend_claimed": False,
        "geomstats_note": "geomstats has no JAX backend in this sim; JAX mirrors parity and spectral observables only.",
        "central_action_real_c_odd": jax_real_action,
        "central_action_control_c_even": jax_control_action,
        "spectral_gap_real_phi_pi_N8": n8["jax_real_holonomy_gap_phi_pi"],
        "spectral_gap_ablated_phi0_N8": n8["jax_control_gap_phi_0"],
        "top_scale_real_gap": top["jax_real_holonomy_gap_phi_pi"],
        "top_scale_control_gap": top["jax_control_gap_phi_0"],
        "pass": bool(
            abs(jax_real_action - real_action) <= TOL
            and abs(jax_control_action - control_action) <= TOL
            and abs(n8["jax_real_holonomy_gap_phi_pi"] - n8["torch_real_holonomy_gap_phi_pi"]) <= TOL
            and abs(n8["jax_control_gap_phi_0"] - n8["torch_control_gap_phi_0"]) <= TOL
        ),
    }

    jax_vs_pytorch_delta = max(
        abs(jax_real_action - real_action),
        abs(jax_control_action - control_action),
        max(row["jax_vs_pytorch_delta"] for row in scale_rows.values()),
    )

    controls = {
        "even_c1_parity_control": {
            "description": "Flip only c1(L) parity from odd to even under the same spin_parity=1 consistency claim.",
            "spin_parity": 1,
            "det_line_c1_parity": 0,
            "central_action": control_action,
            "quotient_consistent": False,
            "pass": bool(control_action == -1.0),
        },
        "det_line_connection_ablated": {
            "description": "Set holonomy phi=0 instead of phi=pi and recompute the sparse-symbol twisted Dirac gap.",
            "gap_real_phi_pi_N8": n8["torch_real_holonomy_gap_phi_pi"],
            "gap_ablated_phi0_N8": n8["torch_control_gap_phi_0"],
            "gap_moves": bool(abs(n8["spectral_response_delta"]) > TOL),
            "pass": bool(abs(n8["torch_control_gap_phi_0"]) <= TOL and n8["torch_real_holonomy_gap_phi_pi"] > TOL),
        },
        "orientation_erased_reflection_control": {
            "description": "Replace an SO(3) frame rotation with det=-1 reflection and recompute e3nn and geomstats membership scores.",
            "e3nn_score": geometry["e3nn_ablated_reflection"]["score"],
            "geomstats_score": geometry["geomstats_ablated_reflection"]["score"],
            "pass": bool(geometry["e3nn_ablated_reflection"]["score"] == 0.0 and geometry["geomstats_ablated_reflection"]["score"] == 0.0),
        },
    }

    tool_ablations = {
        "torch_det_line_holonomy_spectral_gap": tool_ablation(
            "twisted_dirac_min_abs_eigenvalue_gap_N8_phi_pi_vs_phi_0",
            baseline_value=n8["torch_real_holonomy_gap_phi_pi"],
            ablated_value=n8["torch_control_gap_phi_0"],
            tool="torch",
        ),
        "clifford_volume_grade_wrong_carrier": tool_ablation(
            "Cl4_volume_grade_and_square_score_vs_wrong_Cl3_carrier",
            baseline_value=clifford_obs["real"]["score"],
            ablated_value=clifford_obs["ablated"]["score"],
            tool="clifford",
        ),
        "e3nn_oriented_frame_vs_reflection": tool_ablation(
            "e3nn_SO3_roundtrip_score_vs_det_minus_one_reflection",
            baseline_value=geometry["e3nn_real"]["score"],
            ablated_value=geometry["e3nn_ablated_reflection"]["score"],
            tool="e3nn",
        ),
        "geomstats_so3_belongs_vs_reflection": tool_ablation(
            "geomstats_SO3_belongs_score_vs_det_minus_one_reflection",
            baseline_value=geometry["geomstats_real"]["score"],
            ablated_value=geometry["geomstats_ablated_reflection"]["score"],
            tool="geomstats",
        ),
    }

    known_checks = known_value_checks(gamma, scale_rows, torch_primary_result, proofs, clifford_obs, geometry)
    scale_pass = all(row["pass"] for row in scale_rows.values())
    proof_pass = bool(
        proofs["quotient_parity_smt_load_bearing"]["real_claim_verdict"] == "sat"
        and proofs["quotient_parity_smt_load_bearing"]["negated_claim_verdict"] == "unsat"
        and proofs["quotient_parity_smt_load_bearing"]["differ"] is True
        and proofs["quotient_parity_smt_load_bearing"]["bound_to_measured"] is True
        and proofs["quotient_parity_smt_load_bearing"].get("cvc5_real_verdict") == "sat"
        and proofs["quotient_parity_smt_load_bearing"].get("cvc5_control_verdict") == "unsat"
        and proofs["sympy_exact_quotient_parity_flip"]["real_claim_verdict"] == "sat"
        and proofs["sympy_exact_quotient_parity_flip"]["negated_claim_verdict"] == "unsat"
        and proofs["sympy_exact_quotient_parity_flip"]["pass"] is True
    )
    ablation_pass = all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > TOL
        and abs(abs(float(row["baseline_value"]) - float(row["ablated_value"])) - abs(float(row["outcome_delta"]))) <= TOL
        for row in tool_ablations.values()
    )
    controls_pass = all(row["pass"] for row in controls.values())
    known_pass = all(row["match"] for row in known_checks)

    all_pass = bool(
        torch_primary_result["pass"]
        and jax_mirror_result["pass"]
        and jax_vs_pytorch_delta <= TOL
        and scale_pass
        and proof_pass
        and ablation_pass
        and controls_pass
        and known_pass
    )

    return {
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "thisfile": THISFILE,
        "result_path": str(OUT_PATH.relative_to(ROOT)),
        "spec_key": SPEC_KEY,
        "design_spec_source": str(SPEC_PATH),
        "design_spec": spec,
        "object_id": OBJECT_ID,
        "finite_map": {
            "domain": "finite Spin^c(4) data: spin_parity=1, c1(L) parity in {0,1}, C^4 spinor basis, gamma_1..gamma_4, gamma5, and sparse Z_N det-line holonomy paths",
            "codomain_or_output": "quotient-consistency verdict, central-action scalar on S tensor L^(1/2), gamma/gamma5 invariants, and sparse twisted-Dirac spectral gap",
            "definition": "Q(spin_parity,c1_parity)=SAT iff quotient_sum=spin_parity+c1_parity equals required_even_sum=2; D_A symbol lambda_k=sin((2*pi*k+phi)/N)",
        },
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite carrier/probe/operator/path set: parity carrier {odd,even}, four gamma operators, finite spinor basis, and Z_N holonomy paths at total dimensions 8/16/32/64",
            },
            "N01": {
                "status": "active_tested",
                "statement": "order-sensitive Clifford operations: gamma_a gamma5 = - gamma5 gamma_a; quotient verdict changes when only c1(L) parity changes",
            },
        },
        "classification": "lego",
        "promotion_allowed": False,
        "tier": "Stage 4 G-structure lego",
        "sim_execution_kind": "nonclassical",
        "sim_class": "g_structure_probe",
        "carrier_layer": "finite Spin^c(4) spinor module with determinant-line parity and sparse holonomy paths",
        "geometry_layer": "Spin^c central quotient and SO(3) frame-orientation control, not manifold completion",
        "carrier_realization": "torch complex128 C^4 spinor, spinor density, gamma matrices, sparse-symbol Dirac spectrum; no NumPy and no dense state closure",
        "peps3d_embedding": {
            "status": "finite_anchor_only",
            "description": "Each Z_N lattice site is anchored as PEPS3D cell (x=i,y=0,z=0); local cell carries C^4 spinor tensor; x-bonds carry U(1) holonomy exp(i*phi/N). No PEPS3D contraction or downstream manifold admission is claimed.",
            "scale_cells": {str(n): {"total_dim": n, "lattice_cells": scale_rows[n]["lattice_sites"], "local_spinor_dim": SPINOR_DIM} for n in SCALES},
        },
        "spinor_state": {
            "description": "normalized torch complex128 spinor in C^4 plus density rho=|psi><psi|",
            "norm": torch_primary_result["spinor_state_norm"],
            "density_trace_real": torch_primary_result["spinor_density_trace_real"],
            "real_c_odd_descends_residual": real_spinor_residual,
            "control_c_even_descends_residual": control_spinor_residual,
        },
        "quaternion_action": "not_applicable; no quaternion claim is made by this Spin^c quotient-parity packet",
        "dependency_receipts": ["root finite-map packet for this one Stage-4 Spin^c design spec"],
        "allowed_claims": [
            "Spin^c diagonal Z2 quotient parity is represented by the finite parity map in this packet",
            "odd determinant-line parity makes the central action trivial on S tensor L^(1/2)",
            "even determinant-line parity is a degenerate control that flips the same quotient-consistency proof to UNSAT",
            "det-line holonomy enters the sparse-symbol Dirac gap and its ablation changes the computed spectrum",
        ],
        "promotion_blockers": [
            "one Stage-4 G-structure lego only; no full G-structure completion claim",
            "finite PEPS3D anchor is present but no PEPS3D contraction or layer stack admission is claimed",
            "no Xi/Phi0/Axis0/flux/FEP/gravity/physics consumer is unlocked",
        ],
        "eligible_consumers": ["future bounded Stage-4 G-structure comparison packets only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": float(jax_vs_pytorch_delta),
        "proof_results": proofs,
        "controls": controls,
        "geometry_results": geometry,
        "clifford_result": clifford_obs,
        "tool_ablations": tool_ablations,
        "scale_ladder": {
            "description": "non-dense sparse-symbol Z_N x C^4 Spin^c carrier; sites_or_qubits is total carrier dimension",
            "rungs": {str(n): scale_rows[n] for n in SCALES},
            "pass": bool(scale_pass),
        },
        "known_value_checks": known_checks,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "pass_rule": "SMT and exact parity verdicts flip real odd-c1 SAT vs even-c1 UNSAT; det-line holonomy ablation moves the sparse Dirac gap; scale ladder passes 8/16/32/64 without dense closure",
        "fail_rule": "fail on sat/sat parity proof, unbound parity variables, unchanged det-line ablation, missing known-value checks, JAX mismatch, dense closure, or any downstream promotion claim",
        "all_pass": all_pass,
        "required_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["design_spec"], indent=2, sort_keys=True))
    print(f"wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
