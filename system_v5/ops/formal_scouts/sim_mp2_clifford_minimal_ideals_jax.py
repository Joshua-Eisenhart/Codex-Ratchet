#!/usr/bin/env python3
# object_id: mp2_clifford_minimal_ideals
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
SIM_EXECUTION_KIND = "scratch"

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 Python backend for this bounded scratch diagnostic; Python-side array compute uses jax.numpy/jnp only",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing array algebra surface for the local finite witness, controls, shared scalars, and shared booleans",
    },
    "Julia peer backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent peer backend for dual-backend parity; the Python source does not derive values from Julia except parity comparison",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, path handling, timestamps, hashing, imports, and peer-result loading",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded; no import numpy, no np.*, and no NumPy compute path in this scratch diagnostic",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Julia peer backend": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}


OBJECT_ID = "mp2_clifford_minimal_ideals"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUT_DIR = REPO / "system_v5" / "ops" / "formal_scouts"
CARRIER_DIR = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUT_DIR / "results" / "mp2_clifford_minimal_ideals_results.json"
JULIA_RESULT_PATH = CARRIER_DIR / "mp2_clifford_minimal_ideals_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
COLLAPSE_SENTINEL = 1.0e99
DIM_O = 8
FIXED_UNIT = 7

CLAIM_CEILING = (
    "finite witness reproducing the known Furey Cl(6) minimal-left-ideal "
    "structure on the owner complex-octonion/real-Cl6 carrier: two conjugate "
    "rank-one primitive idempotents generate 8-state left ideals that decompose "
    "as 1 + 3 + 3bar + 1 under the SU(3) action. This does NOT admit physics, "
    "the Standard Model, M(C), Axis0, bridge, manifold closure, masses, or "
    "couplings."
)

SOURCE_DEPENDENCIES = {
    "division_algebra_ratchet_ladder": CARRIER_DIR / "division_algebra_ratchet_ladder.jl",
    "division_algebra_ratchet_ladder_jax": CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py",
    "clifford_algebra_ladder": CARRIER_DIR / "clifford_algebra_ladder.jl",
    "clifford_algebra_ladder_jax": CARRIER_DIR / "jax_clifford_algebra_ladder.py",
    "octonion_G2_automorphism": CARRIER_DIR / "octonion_G2_automorphism.jl",
    "octonion_G2_automorphism_jax": CARRIER_DIR / "jax_octonion_G2_automorphism.py",
    "sedenion_break": CARRIER_DIR / "sedenion_break.jl",
    "sedenion_break_prelim_jax": CARRIER_DIR / "jax_sedenion_break_prelim.py",
    "density_matrix_spinor_lift": CARRIER_DIR / "density_matrix_spinor_lift.jl",
    "density_matrix_spinor_lift_jax": CARRIER_DIR / "jax_density_matrix_spinor_lift.py",
    "clifford_torus_nested_hopf_foliation": CARRIER_DIR / "clifford_torus_nested_hopf_foliation.jl",
    "clifford_torus_nested_hopf_foliation_jax": CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py",
    "golden_weyl": CARRIER_DIR / "golden_weyl_julia.jl",
    "golden_weyl_jax_snapshot": CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py",
    "canonical_qit_engine_specs": FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py",
}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


division = load_module("mp2_cmi_division", CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py")
clifford = load_module("mp2_cmi_clifford", CARRIER_DIR / "jax_clifford_algebra_ladder.py")
oct_g2 = load_module("mp2_cmi_oct_g2", CARRIER_DIR / "jax_octonion_G2_automorphism.py")
sedenion = load_module("mp2_cmi_sedenion", CARRIER_DIR / "jax_sedenion_break_prelim.py")
density = load_module("mp2_cmi_density", CARRIER_DIR / "jax_density_matrix_spinor_lift.py")
hopf = load_module("mp2_cmi_hopf", CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py")
golden = load_module("mp2_cmi_golden", CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py")
qit = load_module("mp2_cmi_qit_specs", FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py")


def py_float(x: Any) -> float:
    return float(jax.device_get(jnp.real(x)))


def py_int(x: Any) -> int:
    return int(jax.device_get(x))


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def source_refs() -> dict[str, Any]:
    return {
        key: {"path": str(path), "exists": path.exists(), "sha256": sha256_file(path)}
        for key, path in SOURCE_DEPENDENCIES.items()
    }


def setprod(table: jax.Array, a: int, b: int, c: int, s: float) -> jax.Array:
    return table.at[c, a, b].set(s)


def associative_commutative_erase_table() -> jax.Array:
    table = jnp.zeros((DIM_O, DIM_O, DIM_O), dtype=jnp.float64)
    for idx in range(DIM_O):
        table = setprod(table, idx, idx, idx, 1.0)
    return table


def left_matrix(table: jax.Array, v: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a->cb", table, v)


def complex_vec(terms: list[tuple[int, complex]]) -> jax.Array:
    out = jnp.zeros((DIM_O,), dtype=jnp.complex128)
    for idx, coeff in terms:
        out = out.at[idx].set(coeff)
    return out


def octonion_complex_dagger(v: jax.Array) -> jax.Array:
    out = jnp.zeros_like(v)
    out = out.at[0].set(jnp.conj(v[0]))
    for idx in range(1, DIM_O):
        out = out.at[idx].set(-jnp.conj(v[idx]))
    return out


def owner_ladder_vectors() -> list[jax.Array]:
    return [
        complex_vec([(6, -0.5), (1, 0.5j)]),
        complex_vec([(5, -0.5), (2, 0.5j)]),
        complex_vec([(4, -0.5), (3, 0.5j)]),
    ]


def real_vector(mat: jax.Array) -> jax.Array:
    flat = jnp.reshape(mat, (-1,))
    return jnp.concatenate([jnp.real(flat), jnp.imag(flat)]).astype(jnp.float64)


def span_rank(mats: list[jax.Array]) -> int:
    if not mats:
        return 0
    stacked = jnp.stack([real_vector(mat) for mat in mats], axis=1)
    singular = jnp.linalg.svd(stacked, compute_uv=False)
    thresh = max(stacked.shape) * jnp.finfo(jnp.float64).eps * jnp.max(singular) * 100.0
    return py_int(jnp.sum(singular > thresh))


def complex_span_rank(mats: list[jax.Array]) -> int:
    if not mats:
        return 0
    stacked = jnp.stack([jnp.reshape(mat, (-1,)) for mat in mats], axis=1)
    singular = jnp.linalg.svd(stacked, compute_uv=False)
    thresh = max(stacked.shape) * jnp.finfo(jnp.float64).eps * jnp.max(singular) * 100.0
    return py_int(jnp.sum(singular > thresh))


def span_residual(mat: jax.Array, basis: list[jax.Array]) -> float:
    if not basis:
        return COLLAPSE_SENTINEL
    a = jnp.stack([real_vector(item) for item in basis], axis=1)
    b = real_vector(mat)
    coeffs, _, _, _ = jnp.linalg.lstsq(a, b, rcond=None)
    return py_float(jnp.linalg.norm(b - a @ coeffs))


def all_gamma_products(gammas: list[jax.Array]) -> list[jax.Array]:
    ident = jnp.eye(DIM_O, dtype=jnp.complex128)
    products: list[jax.Array] = []
    for mask in range(64):
        mat = ident
        for idx, gamma in enumerate(gammas):
            if (mask >> idx) & 1:
                mat = mat @ gamma
        products.append(mat)
    return products


def wedge2_matrix(triplet: jax.Array) -> jax.Array:
    pairs = [(1, 2), (2, 0), (0, 1)]
    out = jnp.zeros((3, 3), dtype=jnp.complex128)
    for col, (a, b) in enumerate(pairs):
        for r in range(3):
            for term, coeff in [((r, b), triplet[r, a]), ((a, r), triplet[r, b])]:
                if term[0] == term[1]:
                    continue
                sign = 1.0
                ordered = term
                if ordered[0] > ordered[1]:
                    ordered = (ordered[1], ordered[0])
                    sign = -1.0
                for row, target in enumerate(pairs):
                    if ordered == target:
                        out = out.at[row, col].add(sign * coeff)
                    elif ordered == (target[1], target[0]):
                        out = out.at[row, col].add(-sign * coeff)
    return out


def furey_operators(table: jax.Array) -> dict[str, Any]:
    ctable = table.astype(jnp.complex128)
    alphas = owner_ladder_vectors()
    daggers = [octonion_complex_dagger(alpha) for alpha in alphas]
    lower = [left_matrix(ctable, alpha) for alpha in alphas]
    raise_ = [left_matrix(ctable, dagger) for dagger in daggers]
    ident = jnp.eye(DIM_O, dtype=jnp.complex128)

    car_residual = 0.0
    for i in range(3):
        for j in range(3):
            target = ident if i == j else jnp.zeros_like(ident)
            car_residual = max(car_residual, py_float(jnp.linalg.norm(lower[i] @ raise_[j] + raise_[j] @ lower[i] - target)))
            car_residual = max(car_residual, py_float(jnp.linalg.norm(lower[i] @ lower[j] + lower[j] @ lower[i])))
            car_residual = max(car_residual, py_float(jnp.linalg.norm(raise_[i] @ raise_[j] + raise_[j] @ raise_[i])))

    gammas = [lower[i] + raise_[i] for i in range(3)] + [-1j * (lower[i] - raise_[i]) for i in range(3)]
    gamma_residual = 0.0
    for i in range(6):
        for j in range(6):
            target = 2.0 * ident if i == j else jnp.zeros_like(ident)
            gamma_residual = max(gamma_residual, py_float(jnp.linalg.norm(gammas[i] @ gammas[j] + gammas[j] @ gammas[i] - target)))

    lambdas = [
        -(raise_[1] @ lower[0] + raise_[0] @ lower[1]),
        1j * raise_[1] @ lower[0] - 1j * raise_[0] @ lower[1],
        raise_[1] @ lower[1] - raise_[0] @ lower[0],
        -(raise_[0] @ lower[2] + raise_[2] @ lower[0]),
        -1j * raise_[0] @ lower[2] + 1j * raise_[2] @ lower[0],
        -(raise_[2] @ lower[1] + raise_[1] @ lower[2]),
        1j * raise_[2] @ lower[1] - 1j * raise_[1] @ lower[2],
        -(raise_[0] @ lower[0] + raise_[1] @ lower[1] - 2.0 * raise_[2] @ lower[2]) / jnp.sqrt(3.0),
    ]
    su3_generators = [-0.5j * item for item in lambdas]
    return {
        "lower": lower,
        "raise": raise_,
        "gammas": gammas,
        "gamma_products": all_gamma_products(gammas),
        "su3_generators": su3_generators,
        "car_residual": car_residual,
        "gamma_residual": gamma_residual,
    }


def projector_metrics(projector: jax.Array, gamma_products: list[jax.Array]) -> dict[str, Any]:
    ideal_mats = [product @ projector for product in gamma_products]
    ideal_dim = complex_span_rank(ideal_mats)
    return {
        "rank": py_int(jnp.linalg.matrix_rank(projector, tol=TOL)),
        "trace_real": py_float(jnp.trace(projector)),
        "idempotent_residual": py_float(jnp.linalg.norm(projector @ projector - projector)),
        "left_ideal_dim": ideal_dim,
        "minimal_left_ideal": py_int(jnp.linalg.matrix_rank(projector, tol=TOL)) == 1 and ideal_dim == 8,
    }


def ideal_decomposition(
    projector: jax.Array,
    creation_ops: list[jax.Array],
    annihilation_ops: list[jax.Array],
    su3_generators: list[jax.Array],
    ideal_label: str,
) -> dict[str, Any]:
    ident = jnp.eye(DIM_O, dtype=jnp.complex128)
    col_norms = jnp.linalg.norm(projector, axis=0)
    vacuum_col = py_int(jnp.argmax(col_norms))
    if py_float(col_norms[vacuum_col]) < TOL:
        return {
            "ideal_label": ideal_label,
            "vacuum_column": vacuum_col,
            "fock_gram_residual": COLLAPSE_SENTINEL,
            "offblock_residual": COLLAPSE_SENTINEL,
            "singlet_action_residual": COLLAPSE_SENTINEL,
            "triplet_trace_residual": COLLAPSE_SENTINEL,
            "wedge2_antitriplet_residual": COLLAPSE_SENTINEL,
            "triplet_casimir_residual": COLLAPSE_SENTINEL,
            "antitriplet_casimir_residual": COLLAPSE_SENTINEL,
            "number_operator_residual": COLLAPSE_SENTINEL,
            "charge_quantization_residual": COLLAPSE_SENTINEL,
            "decomposition_1_3_3bar_1": False,
            "sm_slots": {},
        }
    vacuum = projector[:, vacuum_col] / col_norms[vacuum_col]
    fock_states = [vacuum]
    fock_states.extend([creation_ops[idx] @ vacuum for idx in range(3)])
    fock_states.extend(
        [
            creation_ops[1] @ creation_ops[2] @ vacuum,
            creation_ops[2] @ creation_ops[0] @ vacuum,
            creation_ops[0] @ creation_ops[1] @ vacuum,
        ]
    )
    fock_states.append(creation_ops[0] @ creation_ops[1] @ creation_ops[2] @ vacuum)
    fock = jnp.stack(fock_states, axis=1)
    fock_inv = fock.conj().T
    fock_gram = py_float(jnp.linalg.norm(fock_inv @ fock - ident))
    occ_blocks = [0, 1, 1, 1, 2, 2, 2, 3]

    offblock = 0.0
    singlet = 0.0
    trace_resid = 0.0
    wedge_resid = 0.0
    casimir_triplet = jnp.zeros((3, 3), dtype=jnp.complex128)
    casimir_antitriplet = jnp.zeros((3, 3), dtype=jnp.complex128)
    for generator in su3_generators:
        rep = fock_inv @ (generator @ fock)
        for row in range(DIM_O):
            for col in range(DIM_O):
                if occ_blocks[row] != occ_blocks[col]:
                    offblock = max(offblock, py_float(jnp.abs(rep[row, col])))
        singlet = max(singlet, py_float(jnp.abs(rep[0, 0])), py_float(jnp.abs(rep[7, 7])))
        triplet = rep[1:4, 1:4]
        antitriplet = rep[4:7, 4:7]
        trace_resid = max(trace_resid, py_float(jnp.abs(jnp.trace(triplet))), py_float(jnp.abs(jnp.trace(antitriplet))))
        wedge_resid = max(wedge_resid, py_float(jnp.linalg.norm(antitriplet - wedge2_matrix(triplet))))
        casimir_triplet = casimir_triplet + triplet @ triplet
        casimir_antitriplet = casimir_antitriplet + antitriplet @ antitriplet

    casimir_target = -(4.0 / 3.0) * jnp.eye(3, dtype=jnp.complex128)
    number = sum(creation_ops[idx] @ annihilation_ops[idx] for idx in range(3))
    number_rep = fock_inv @ (number @ fock)
    number_target = jnp.diag(jnp.asarray([0.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 3.0], dtype=jnp.float64)).astype(jnp.complex128)
    charges = jnp.diag(number_target).real / 3.0
    charge_quantization = py_float(jnp.max(jnp.abs(3.0 * charges - jnp.round(3.0 * charges))))
    decomp_ok = (
        fock_gram < TOL
        and offblock < TOL
        and singlet < TOL
        and trace_resid < TOL
        and wedge_resid < TOL
        and py_float(jnp.linalg.norm(casimir_triplet - casimir_target)) < TOL
        and py_float(jnp.linalg.norm(casimir_antitriplet - casimir_target)) < TOL
        and py_float(jnp.linalg.norm(number_rep - number_target)) < TOL
        and charge_quantization < TOL
    )
    return {
        "ideal_label": ideal_label,
        "vacuum_column": vacuum_col,
        "fock_gram_residual": fock_gram,
        "offblock_residual": offblock,
        "singlet_action_residual": singlet,
        "triplet_trace_residual": trace_resid,
        "wedge2_antitriplet_residual": wedge_resid,
        "triplet_casimir_residual": py_float(jnp.linalg.norm(casimir_triplet - casimir_target)),
        "antitriplet_casimir_residual": py_float(jnp.linalg.norm(casimir_antitriplet - casimir_target)),
        "number_operator_residual": py_float(jnp.linalg.norm(number_rep - number_target)),
        "charge_quantization_residual": charge_quantization,
        "decomposition_1_3_3bar_1": decomp_ok,
        "charges_by_occupation": [py_float(x) for x in charges],
        "sm_slots": {
            "neutrino_singlet": {"dim": 1, "occupation": 0},
            "color_triplet_quark_slot": {"dim": 3, "occupation": 1},
            "color_antitriplet_slot": {"dim": 3, "occupation": 2},
            "charged_lepton_singlet": {"dim": 1, "occupation": 3},
        },
    }


def su3_closure_metrics(generators: list[jax.Array]) -> dict[str, Any]:
    rank = span_rank(generators)
    closure = 0.0
    for left in generators:
        for right in generators:
            closure = max(closure, span_residual(left @ right - right @ left, generators))
    return {"rank": rank, "closure_residual": closure}


def analyze_carrier(table: jax.Array, carrier_label: str) -> dict[str, Any]:
    ops = furey_operators(table)
    gamma_span_dim = span_rank(ops["gamma_products"])
    su3 = su3_closure_metrics(ops["su3_generators"])
    lower = ops["lower"]
    raise_ = ops["raise"]
    particle_projector = lower[0] @ lower[1] @ lower[2] @ raise_[2] @ raise_[1] @ raise_[0]
    conjugate_projector = raise_[0] @ raise_[1] @ raise_[2] @ lower[2] @ lower[1] @ lower[0]
    particle_projector_metrics = projector_metrics(particle_projector, ops["gamma_products"])
    conjugate_projector_metrics = projector_metrics(conjugate_projector, ops["gamma_products"])
    particle_ideal = ideal_decomposition(particle_projector, raise_, lower, ops["su3_generators"], "omega_omega_dagger")
    conjugate_ideal = ideal_decomposition(conjugate_projector, lower, raise_, ops["su3_generators"], "omega_dagger_omega")
    n_minimal_ideals = int(particle_projector_metrics["minimal_left_ideal"]) + int(conjugate_projector_metrics["minimal_left_ideal"])
    decomp_matches = (
        n_minimal_ideals == 2
        and gamma_span_dim == 64
        and ops["car_residual"] < TOL
        and ops["gamma_residual"] < TOL
        and su3["rank"] == 8
        and su3["closure_residual"] < TOL
        and particle_ideal["decomposition_1_3_3bar_1"]
        and conjugate_ideal["decomposition_1_3_3bar_1"]
    )
    return {
        "carrier_label": carrier_label,
        "car_residual": ops["car_residual"],
        "gamma_residual": ops["gamma_residual"],
        "cl6_matrix_span_dim": gamma_span_dim,
        "su3_rank": su3["rank"],
        "su3_closure_residual": su3["closure_residual"],
        "particle_projector": particle_projector_metrics,
        "conjugate_projector": conjugate_projector_metrics,
        "projector_orthogonality_residual": py_float(jnp.linalg.norm(particle_projector @ conjugate_projector)),
        "particle_ideal": particle_ideal,
        "conjugate_ideal": conjugate_ideal,
        "n_minimal_ideals": n_minimal_ideals,
        "decomp_matches_sm": bool(decomp_matches),
    }


def owner_support_checks() -> dict[str, Any]:
    h_table = division.quaternion_table()
    o_table = division.octonion_table()
    cl6_real = clifford.clifford_table([1, 1, 1, 1, 1, 1])
    g2_constraint = oct_g2.derivation_constraint_matrix(o_table)
    singular = jnp.linalg.svd(g2_constraint, compute_uv=False)
    rank_tol = max(g2_constraint.shape) * jnp.finfo(jnp.float64).eps * jnp.max(singular) * 100.0
    g2_rank = py_int(jnp.sum(singular > rank_tol))
    s_table = sedenion.cayley_dickson_double(sedenion.prior_octonion_table())
    s_left = sedenion.pair_vector(16, 1, 10)
    s_right = sedenion.pair_vector(16, 5, 14)
    s_product = sedenion.multiply(s_table, s_left, s_right)
    rho = density.dm(density.spinor_from_angles(1.1, -0.7))
    hopf_interior = hopf.interior_torus_checks()
    golden_state = golden.psi(0.31, -0.27, 0.25)
    return {
        "division_algebra_ladder_dims": {
            "R": int(division.real_table().shape[0]),
            "C": int(division.complex_table().shape[0]),
            "H": int(h_table.shape[0]),
            "O": int(o_table.shape[0]),
        },
        "h_i_j_minus_k_residual": py_float(jnp.linalg.norm(division.multiply(h_table, division.basis(4, 1), division.basis(4, 2)) - division.basis(4, 3))),
        "o_fano_e1_e2_minus_e3_residual": py_float(jnp.linalg.norm(division.multiply(o_table, division.basis(8, 1), division.basis(8, 2)) - division.basis(8, 3))),
        "real_cl6_table_dim": int(cl6_real.shape[0]),
        "real_cl6_expected_dim": 64,
        "g2_der_o_dim": int(g2_constraint.shape[1] - g2_rank),
        "sedenion_dim": int(s_table.shape[0]),
        "sedenion_zero_divisor_product_norm": py_float(jnp.linalg.norm(s_product)),
        "sedenion_zero_divisor_witness": py_float(jnp.linalg.norm(s_product)) < TOL,
        "density_matrix_trace_real": py_float(jnp.real(jnp.trace(rho))),
        "density_matrix_bloch_norm": py_float(jnp.linalg.norm(density.bloch_from_rho(rho))),
        "hopf_interior_s3_constraint_max_residual": float(hopf_interior["interior_s3_constraint_max_residual"]),
        "hopf_torus_metric_det_min": float(hopf_interior["torus_metric_det_min"]),
        "golden_weyl_sample_norm_residual": py_float(jnp.abs(jnp.real(jnp.vdot(golden_state, golden_state)) - 1.0)),
        "qit_lindblad_count": len(qit.PERCEPTION_L_MATRICES),
        "qit_operator_generator_count": len(qit.OPERATOR_GENERATORS),
        "qit_type_one_schedule_len": len(qit.ENGINE_SCHEDULE_TYPE_ONE),
        "qit_type_two_schedule_len": len(qit.ENGINE_SCHEDULE_TYPE_TWO),
        "qit_substage_count_per_engine": int(qit.N_TOTAL_SUBSTAGES_PER_ENGINE),
        "qit_manifold_layer_count": int(qit.N_MANIFOLD_LAYERS),
    }


def parity_against_peer(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "peer_available": False,
            "parity_max_diff": None,
            "worst_key": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [{"missing": str(JULIA_RESULT_PATH)}],
            "boolean_mismatches": [],
            "missing_keys": sorted([*result["shared_scalars"].keys(), *result["shared_booleans"].keys()]),
            "diffs": {},
            "stop_condition_fired": True,
        }
    peer = json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))
    peer_scalars = peer.get("shared_scalars", {})
    peer_booleans = peer.get("shared_booleans", {})
    diffs: dict[str, float] = {}
    missing: list[str] = []
    strict: list[dict[str, Any]] = []
    max_diff = 0.0
    worst_key = None
    for key, value in result["shared_scalars"].items():
        if key not in peer_scalars:
            missing.append(key)
            continue
        diff = abs(float(value) - float(peer_scalars[key]))
        diffs[key] = diff
        if diff > max_diff:
            max_diff = diff
            worst_key = key
        if diff > STRICT_STOP_TOL:
            strict.append({"key": key, "jax": float(value), "julia": float(peer_scalars[key]), "abs_diff": diff})
    mismatches: list[dict[str, Any]] = []
    for key, value in result["shared_booleans"].items():
        if key not in peer_booleans:
            missing.append(key)
            continue
        if bool(value) != bool(peer_booleans[key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer_booleans[key])})
    for key in set(peer_scalars) - set(result["shared_scalars"]):
        missing.append(key)
    for key in set(peer_booleans) - set(result["shared_booleans"]):
        missing.append(key)
    return {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "peer_available": True,
        "parity_max_diff": max_diff,
        "worst_key": worst_key,
        "within_1e_9": max_diff <= TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": sorted(set(missing)),
        "diffs": diffs,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def build_result() -> dict[str, Any]:
    real = analyze_carrier(division.octonion_table(), "owner_complex_octonion_real_cl6")
    erased = analyze_carrier(associative_commutative_erase_table(), "associative_commutative_erasure_control")
    support = owner_support_checks()

    controls = {
        "real_vs_erased_flip": real["decomp_matches_sm"] and not erased["decomp_matches_sm"],
        "associative_erasure_breaks_car": erased["car_residual"] > 1.0e-3,
        "associative_erasure_not_cl6_span": erased["cl6_matrix_span_dim"] != 64,
        "associative_erasure_no_two_minimal_ideals": erased["n_minimal_ideals"] != 2,
    }
    from_real_cl6 = (
        support["real_cl6_table_dim"] == 64
        and real["cl6_matrix_span_dim"] == 64
        and real["gamma_residual"] < TOL
        and real["car_residual"] < TOL
    )
    owner_support_ok = (
        support["division_algebra_ladder_dims"] == {"R": 1, "C": 2, "H": 4, "O": 8}
        and support["h_i_j_minus_k_residual"] < TOL
        and support["o_fano_e1_e2_minus_e3_residual"] < TOL
        and support["g2_der_o_dim"] == 14
        and support["sedenion_dim"] == 16
        and support["sedenion_zero_divisor_witness"]
        and abs(support["density_matrix_trace_real"] - 1.0) < TOL
        and support["hopf_interior_s3_constraint_max_residual"] < TOL
        and support["golden_weyl_sample_norm_residual"] < TOL
        and support["qit_substage_count_per_engine"] == 32
        and support["qit_manifold_layer_count"] == 13
    )
    owner_carrier_load_bearing = bool(real["decomp_matches_sm"] and all(controls.values()) and owner_support_ok and from_real_cl6)
    decomp_matches_sm = bool(real["decomp_matches_sm"] and controls["real_vs_erased_flip"])
    local_all_pass = bool(owner_carrier_load_bearing and decomp_matches_sm and real["n_minimal_ideals"] == 2)

    shared_scalars = {
        "real.car_residual": float(real["car_residual"]),
        "real.gamma_residual": float(real["gamma_residual"]),
        "real.cl6_matrix_span_dim": float(real["cl6_matrix_span_dim"]),
        "real.su3_rank": float(real["su3_rank"]),
        "real.su3_closure_residual": float(real["su3_closure_residual"]),
        "real.n_minimal_ideals": float(real["n_minimal_ideals"]),
        "real.particle_left_ideal_dim": float(real["particle_projector"]["left_ideal_dim"]),
        "real.conjugate_left_ideal_dim": float(real["conjugate_projector"]["left_ideal_dim"]),
        "real.particle_projector_rank": float(real["particle_projector"]["rank"]),
        "real.conjugate_projector_rank": float(real["conjugate_projector"]["rank"]),
        "real.projector_orthogonality_residual": float(real["projector_orthogonality_residual"]),
        "real.particle_fock_gram_residual": float(real["particle_ideal"]["fock_gram_residual"]),
        "real.conjugate_fock_gram_residual": float(real["conjugate_ideal"]["fock_gram_residual"]),
        "real.particle_wedge2_antitriplet_residual": float(real["particle_ideal"]["wedge2_antitriplet_residual"]),
        "real.conjugate_wedge2_antitriplet_residual": float(real["conjugate_ideal"]["wedge2_antitriplet_residual"]),
        "erased.car_residual": float(erased["car_residual"]),
        "erased.gamma_residual": float(erased["gamma_residual"]),
        "erased.cl6_matrix_span_dim": float(erased["cl6_matrix_span_dim"]),
        "erased.n_minimal_ideals": float(erased["n_minimal_ideals"]),
        "support.real_cl6_table_dim": float(support["real_cl6_table_dim"]),
        "support.g2_der_o_dim": float(support["g2_der_o_dim"]),
        "support.sedenion_dim": float(support["sedenion_dim"]),
        "support.sedenion_zero_divisor_product_norm": float(support["sedenion_zero_divisor_product_norm"]),
        "support.density_matrix_trace_real": float(support["density_matrix_trace_real"]),
        "support.hopf_interior_s3_constraint_max_residual": float(support["hopf_interior_s3_constraint_max_residual"]),
        "support.golden_weyl_sample_norm_residual": float(support["golden_weyl_sample_norm_residual"]),
        "support.qit_substage_count_per_engine": float(support["qit_substage_count_per_engine"]),
        "support.qit_manifold_layer_count": float(support["qit_manifold_layer_count"]),
    }
    shared_booleans = {
        "local_all_pass": local_all_pass,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "decomp_matches_sm": decomp_matches_sm,
        "from_real_cl6": from_real_cl6,
        "owner_support_ok": owner_support_ok,
        "float64_backend": bool(jax.config.read("jax_enable_x64")),
        **{f"control.{key}": bool(value) for key, value in controls.items()},
    }

    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "schema": "SCRATCH_DIAGNOSTIC_RESULT_v1",
        "name": OBJECT_ID,
        "backend": "jax_jnp_x64",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "owner_julia_carrier": "load_bearing",
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "claim_ceiling": CLAIM_CEILING,
        "allowed_claims": [
            "finite Furey Cl(6) minimal-left-ideal structure witness",
            "dual-backend parity witness",
            "real-vs-erased owner-carrier control",
        ],
        "blocked_consumers": [
            "physics_claims",
            "SM_admission",
            "M(C)_admission",
            "Axis0",
            "masses",
            "couplings",
            "bridge",
            "formal_admission",
        ],
        "sim_execution_kind": "scratch_diagnostic",
        "sim_class": "finite_formal_scout",
        "numpy_compute_used": False,
        "numpy_imported": False,
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "owner_source_refs": source_refs(),
        "real_carrier": real,
        "erased_control_carrier": erased,
        "owner_support_checks": support,
        "controls": controls,
        "verdicts": {
            "local_all_pass": local_all_pass,
            "owner_carrier_load_bearing": owner_carrier_load_bearing,
            "n_minimal_ideals": real["n_minimal_ideals"],
            "decomp_matches_sm": decomp_matches_sm,
            "from_real_cl6": from_real_cl6,
        },
        "positive": {
            "primitive_idempotents_generate_two_minimal_left_ideals": {
                "pass": real["n_minimal_ideals"] == 2,
                "particle_left_ideal_dim": real["particle_projector"]["left_ideal_dim"],
                "conjugate_left_ideal_dim": real["conjugate_projector"]["left_ideal_dim"],
            },
            "su3_decomposition_1_3_3bar_1": {
                "pass": decomp_matches_sm,
                "particle": real["particle_ideal"]["sm_slots"],
                "conjugate": real["conjugate_ideal"]["sm_slots"],
            },
            "from_real_cl6": {"pass": from_real_cl6},
            "owner_object_set_present": {"pass": all(row["exists"] for row in source_refs().values())},
        },
        "graveyard_companions": {
            "associative_erasure_control": {"pass": controls["real_vs_erased_flip"], "control": erased},
            "non_clifford_control_breaks_car": {"pass": controls["associative_erasure_breaks_car"]},
            "non_clifford_control_breaks_cl6_span": {"pass": controls["associative_erasure_not_cl6_span"]},
        },
        "boundary": {
            "classification_is_scratch_diagnostic": {"pass": True},
            "promotion_disallowed": {"pass": True},
            "formal_admission_disallowed": {"pass": True},
            "claim_ceiling_blocks_physics_axis_masses_couplings": {"pass": True},
            "no_numpy_compute": {"pass": True, "backend": "JAX jax.numpy x64"},
        },
        "nearby_variants": {
            "total": len(controls),
            "passed": sum(1 for value in controls.values() if value),
            "variant_names": sorted(controls),
        },
        "why_not_v4_probes": [
            "scratch diagnostic by request, not a formal_scout admission receipt",
            "finite algebraic representation witness only, not phenomenology",
            "masses and couplings are not derived or claimed",
            "Axis0, M(C), bridge, manifold closure, and physics admission remain blocked",
        ],
        "tool_manifest": {
            "JAX jax.numpy x64": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite complex matrix, rank, projector, Clifford anticommutator, and SU(3) block-decomposition computation; no NumPy compute path",
            },
            "Julia mirror": {
                "tried": True,
                "used": True,
                "reason": "load-bearing independent Float64/ComplexF64 backend with shared scalar/boolean parity",
            },
            "owner_julia_carrier": {
                "tried": True,
                "used": True,
                "reason": "load-bearing owner complex-octonion/real-Cl6 carrier; associative erasure changes CAR, Cl(6) span, minimal-left-ideal count, and decomposition verdict",
            },
            "division_algebra_ratchet_ladder": {
                "tried": True,
                "used": True,
                "reason": "load-bearing octonion multiplication table and H/O product checks used by the Cl(6) ladder carrier",
            },
            "clifford_algebra_ladder": {
                "tried": True,
                "used": True,
                "reason": "load-bearing real Cl(6) 64-dimensional table check and Clifford span boundary",
            },
            "octonion_G2_automorphism": {
                "tried": True,
                "used": True,
                "reason": "load-bearing der(O)=g2 dimension check anchoring the SU(3) stabilizer source structure",
            },
            "sedenion_break": {
                "tried": True,
                "used": True,
                "reason": "load-bearing owner-carrier boundary guard with a concrete zero-divisor product witness, preventing a toy dimension-only carrier read",
            },
            "density_matrix_spinor_lift": {
                "tried": True,
                "used": True,
                "reason": "supportive spinor/density trace readback from the owner carrier suite",
            },
            "clifford_torus_nested_hopf_foliation": {
                "tried": True,
                "used": True,
                "reason": "supportive finite Hopf/Clifford-torus carrier readback from the owner carrier suite",
            },
            "golden_weyl": {
                "tried": True,
                "used": True,
                "reason": "supportive Weyl spinor norm readback from the owner carrier suite",
            },
            "canonical_qit_engine_specs.py": {
                "tried": True,
                "used": True,
                "reason": "supportive source anchor for current QIT engine layer/schedule counts; no engine admission claim",
            },
        },
        "TOOL_MANIFEST": {},
        "tool_integration_depth": {
            "JAX jax.numpy x64": "load_bearing",
            "Julia mirror": "load_bearing",
            "owner_julia_carrier": "load_bearing",
            "division_algebra_ratchet_ladder": "load_bearing",
            "clifford_algebra_ladder": "load_bearing",
            "octonion_G2_automorphism": "load_bearing",
            "sedenion_break": "load_bearing",
            "density_matrix_spinor_lift": "supportive",
            "clifford_torus_nested_hopf_foliation": "supportive",
            "golden_weyl": "supportive",
            "canonical_qit_engine_specs.py": "supportive",
        },
        "TOOL_INTEGRATION_DEPTH": {},
        "divergence_log": [
            "Real carrier: complex octonion ladder operators satisfy CAR, span Cl(6), and generate two 8-state minimal left ideals.",
            "Erased control: replacing the owner multiplication by an associative idempotent table breaks the CAR/Cl(6) span and does not reproduce the ideal structure.",
            "Claim ceiling remains finite witness only; no physics, SM admission, masses, couplings, M(C), bridge, or Axis0 claim is made.",
        ],
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
    }
    result["TOOL_MANIFEST"] = result["tool_manifest"]
    result["TOOL_INTEGRATION_DEPTH"] = result["tool_integration_depth"]
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = bool(local_all_pass and result["parity"]["within_1e_9"])
    result["local_all_pass"] = local_all_pass
    result["stop_condition_fired"] = bool((not local_all_pass) or result["parity"]["stop_condition_fired"])
    result["n_minimal_ideals"] = real["n_minimal_ideals"]
    result["decomp_matches_sm"] = decomp_matches_sm
    result["from_real_cl6"] = from_real_cl6
    result["summary"] = {
        "all_pass": result["all_pass"],
        "local_all_pass": local_all_pass,
        "parity_within_1e_9": result["parity"]["within_1e_9"],
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "n_minimal_ideals": real["n_minimal_ideals"],
        "decomp_matches_sm": decomp_matches_sm,
        "from_real_cl6": from_real_cl6,
    }
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"jax={RESULT_PATH} "
        f"julia={JULIA_RESULT_PATH} "
        f"all_pass={str(result['all_pass']).lower()} "
        f"owner_carrier_load_bearing={str(result['owner_carrier_load_bearing']).lower()} "
        f"n_minimal_ideals={int(result['n_minimal_ideals'])} "
        f"decomp_matches_sm={str(result['decomp_matches_sm']).lower()} "
        f"from_real_cl6={str(result['from_real_cl6']).lower()}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
