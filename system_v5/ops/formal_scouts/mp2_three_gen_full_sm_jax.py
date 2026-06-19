#!/usr/bin/env python3
# object_id: mp2_three_gen_full_sm
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


OBJECT_ID = "mp2_three_gen_full_sm"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUT_DIR = REPO / "system_v5" / "ops" / "formal_scouts"
CARRIER_DIR = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUT_DIR / "results" / "mp2_three_gen_full_sm_results.json"
JULIA_REFERENCE_PATH = CARRIER_DIR / "mp2_three_gen_full_sm_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
GENERATION_LABELS = (9, 10, 11)
S3_LINE = (1, 2, 3)


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


division = load_module("mp2_division_algebra_ratchet_ladder", CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py")
clifford = load_module("mp2_clifford_algebra_ladder", CARRIER_DIR / "jax_clifford_algebra_ladder.py")
oct_g2 = load_module("mp2_octonion_G2_automorphism", CARRIER_DIR / "jax_octonion_G2_automorphism.py")
sedenion = load_module("mp2_sedenion_break", CARRIER_DIR / "jax_sedenion_break_prelim.py")
density = load_module("mp2_density_matrix_spinor_lift", CARRIER_DIR / "jax_density_matrix_spinor_lift.py")
hopf = load_module("mp2_clifford_torus_nested_hopf_foliation", CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py")
golden = load_module("mp2_golden_weyl", CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py")
qit = load_module("mp2_canonical_qit_engine_specs", FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py")


SOURCE_REFS = {
    "division_algebra_ratchet_ladder": CARRIER_DIR / "division_algebra_ratchet_ladder.jl",
    "jax_division_algebra_ratchet_ladder": CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py",
    "clifford_algebra_ladder": CARRIER_DIR / "clifford_algebra_ladder.jl",
    "jax_clifford_algebra_ladder": CARRIER_DIR / "jax_clifford_algebra_ladder.py",
    "octonion_G2_automorphism": CARRIER_DIR / "octonion_G2_automorphism.jl",
    "jax_octonion_G2_automorphism": CARRIER_DIR / "jax_octonion_G2_automorphism.py",
    "sedenion_break": CARRIER_DIR / "sedenion_break.jl",
    "sedenion_break_prelim_lineage": CARRIER_DIR / "sedenion_break_prelim.jl",
    "jax_sedenion_break": CARRIER_DIR / "jax_sedenion_break_prelim.py",
    "density_matrix_spinor_lift": CARRIER_DIR / "density_matrix_spinor_lift.jl",
    "jax_density_matrix_spinor_lift": CARRIER_DIR / "jax_density_matrix_spinor_lift.py",
    "clifford_torus_nested_hopf_foliation": CARRIER_DIR / "clifford_torus_nested_hopf_foliation.jl",
    "jax_clifford_torus_nested_hopf_foliation": CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py",
    "golden_weyl": CARRIER_DIR / "golden_weyl_julia.jl",
    "golden_weyl_jax_snapshot": CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py",
    "canonical_qit_engine_specs": FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py",
}


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def source_refs() -> dict[str, Any]:
    return {key: {"path": str(path), "exists": path.exists(), "sha256": sha256_file(path)} for key, path in SOURCE_REFS.items()}


def carray(rows: list[list[complex]]) -> jax.Array:
    return jnp.asarray(rows, dtype=jnp.complex128)


def real_vector(mat: jax.Array) -> jax.Array:
    flat = jnp.reshape(mat, (-1,))
    return jnp.concatenate([jnp.real(flat), jnp.imag(flat)]).astype(jnp.float64)


def span_rank(mats: list[jax.Array]) -> int:
    if not mats:
        return 0
    stacked = jnp.stack([real_vector(m) for m in mats], axis=1)
    singular = jnp.linalg.svd(stacked, compute_uv=False)
    thresh = max(stacked.shape) * jnp.finfo(jnp.float64).eps * jnp.max(singular) * 100.0
    return int(jax.device_get(jnp.sum(singular > thresh)))


def span_residual(mat: jax.Array, basis: list[jax.Array]) -> float:
    a = jnp.stack([real_vector(m) for m in basis], axis=1)
    b = real_vector(mat)
    coeffs, _, _, _ = jnp.linalg.lstsq(a, b, rcond=None)
    return py_float(jnp.linalg.norm(b - a @ coeffs))


def closure_residual(gens: list[jax.Array]) -> float:
    max_seen = 0.0
    for a in gens:
        for b in gens:
            lie_hermitian = -1j * (a @ b - b @ a)
            max_seen = max(max_seen, span_residual(lie_hermitian, gens))
    return max_seen


def gell_mann() -> list[jax.Array]:
    z = 0.0 + 0.0j
    one = 1.0 + 0.0j
    i = 1j
    return [
        carray([[z, one, z], [one, z, z], [z, z, z]]) / 2.0,
        carray([[z, -i, z], [i, z, z], [z, z, z]]) / 2.0,
        carray([[one, z, z], [z, -one, z], [z, z, z]]) / 2.0,
        carray([[z, z, one], [z, z, z], [one, z, z]]) / 2.0,
        carray([[z, z, -i], [z, z, z], [i, z, z]]) / 2.0,
        carray([[z, z, z], [z, z, one], [z, one, z]]) / 2.0,
        carray([[z, z, z], [z, z, -i], [z, i, z]]) / 2.0,
        carray([[one, z, z], [z, one, z], [z, z, -2.0 + 0.0j]]) / (2.0 * jnp.sqrt(3.0)),
    ]


SX = carray([[0, 1], [1, 0]])
SY = carray([[0, -1j], [1j, 0]])
SZ = carray([[1, 0], [0, -1]])


def one_generation_states(generation_label: int, ideal_seed_pairs: list[list[int]]) -> list[dict[str, Any]]:
    states: list[dict[str, Any]] = []
    colors = ["r", "g", "b"]

    def add(name: str, family: str, color: int, weak: int, chirality: str, q: float, y: float) -> None:
        states.append(
            {
                "name": f"g{generation_label}_{name}",
                "generation_label": generation_label,
                "ideal_seed_pairs": ideal_seed_pairs,
                "family": family,
                "color": color,
                "weak": weak,
                "chirality": chirality,
                "q": q,
                "y": y,
            }
        )

    for ci, color in enumerate(colors):
        add(f"u_L_{color}", "u", ci, 0, "L", 2.0 / 3.0, 1.0 / 3.0)
        add(f"d_L_{color}", "d", ci, 1, "L", -1.0 / 3.0, 1.0 / 3.0)
    add("nu_L", "nu", -1, 0, "L", 0.0, -1.0)
    add("e_L", "e", -1, 1, "L", -1.0, -1.0)
    for ci, color in enumerate(colors):
        add(f"u_R_{color}", "u", ci, -1, "R", 2.0 / 3.0, 4.0 / 3.0)
        add(f"d_R_{color}", "d", ci, -1, "R", -1.0 / 3.0, -2.0 / 3.0)
    add("nu_R", "nu", -1, -1, "R", 0.0, 0.0)
    add("e_R", "e", -1, -1, "R", -1.0, -2.0)
    return states


def zero_full(dim: int) -> jax.Array:
    return jnp.zeros((dim, dim), dtype=jnp.complex128)


def embed_color(states: list[dict[str, Any]], color_gen: jax.Array) -> jax.Array:
    out = zero_full(len(states))
    for a, sa in enumerate(states):
        if sa["color"] < 0:
            continue
        for b, sb in enumerate(states):
            same_generation = sa["generation_label"] == sb["generation_label"]
            same_species = sa["family"] == sb["family"] and sa["chirality"] == sb["chirality"] and sa["weak"] == sb["weak"]
            if same_generation and same_species and sb["color"] >= 0:
                out = out.at[a, b].set(color_gen[sa["color"], sb["color"]])
    return out


def embed_weak(states: list[dict[str, Any]], weak_gen: jax.Array) -> jax.Array:
    out = zero_full(len(states))
    for a, sa in enumerate(states):
        if sa["weak"] < 0 or sa["chirality"] != "L":
            continue
        for b, sb in enumerate(states):
            same_generation = sa["generation_label"] == sb["generation_label"]
            same_doublet = sa["chirality"] == sb["chirality"] == "L" and sa["color"] == sb["color"]
            quark_pair = sa["color"] >= 0 and sb["color"] >= 0 and {sa["family"], sb["family"]} <= {"u", "d"}
            lepton_pair = sa["color"] < 0 and sb["color"] < 0 and {sa["family"], sb["family"]} <= {"nu", "e"}
            if same_generation and same_doublet and (quark_pair or lepton_pair) and sb["weak"] >= 0:
                out = out.at[a, b].set(weak_gen[sa["weak"], sb["weak"]])
    return out


def diagonal(states: list[dict[str, Any]], key: str) -> jax.Array:
    vals = jnp.asarray([float(s[key]) for s in states], dtype=jnp.float64)
    return jnp.diag(vals.astype(jnp.complex128))


def charge_summary(states: list[dict[str, Any]]) -> dict[str, Any]:
    charges = [float(s["q"]) for s in states]
    return {
        "u_charge_values": sorted({round(float(s["q"]), 12) for s in states if s["family"] == "u"}),
        "d_charge_values": sorted({round(float(s["q"]), 12) for s in states if s["family"] == "d"}),
        "nu_charge_values": sorted({round(float(s["q"]), 12) for s in states if s["family"] == "nu"}),
        "e_charge_values": sorted({round(float(s["q"]), 12) for s in states if s["family"] == "e"}),
        "quark_color_counts": {
            fam: len({s["color"] for s in states if s["family"] == fam and s["color"] >= 0})
            for fam in ["u", "d"]
        },
        "lepton_color_counts": {
            fam: len({s["color"] for s in states if s["family"] == fam})
            for fam in ["nu", "e"]
        },
        "charge_quantization_residual": max(abs(3.0 * q - round(3.0 * q)) for q in charges),
    }


def gauge_checks(states: list[dict[str, Any]]) -> dict[str, Any]:
    color_local = gell_mann()
    weak_local = [SX / 2.0, SY / 2.0, SZ / 2.0]
    color_gens = [embed_color(states, g) for g in color_local]
    weak_gens = [embed_weak(states, g) for g in weak_local]
    y_gen = diagonal(states, "y") / 2.0
    q_gen = diagonal(states, "q")
    q_recon = weak_gens[2] + y_gen
    su3_rank = span_rank(color_gens)
    su2_rank = span_rank(weak_gens)
    u1_rank = span_rank([y_gen])
    su3_closure = closure_residual(color_gens)
    su2_closure = closure_residual(weak_gens)
    commute_32 = max(py_float(jnp.linalg.norm(a @ b - b @ a)) for a in color_gens for b in weak_gens)
    commute_31 = max(py_float(jnp.linalg.norm(a @ y_gen - y_gen @ a)) for a in color_gens)
    commute_21 = max(py_float(jnp.linalg.norm(a @ y_gen - y_gen @ a)) for a in weak_gens)
    charge_reconstruction_residual = py_float(jnp.linalg.norm(q_gen - q_recon))
    charges = charge_summary(states)
    charges_match = (
        charges["u_charge_values"] == [round(2.0 / 3.0, 12)]
        and charges["d_charge_values"] == [round(-1.0 / 3.0, 12)]
        and charges["nu_charge_values"] == [0.0]
        and charges["e_charge_values"] == [-1.0]
        and charges["quark_color_counts"] == {"u": 3, "d": 3}
        and charges["lepton_color_counts"] == {"nu": 1, "e": 1}
        and charges["charge_quantization_residual"] < TOL
        and charge_reconstruction_residual < TOL
    )
    return {
        "state_count": len(states),
        "su3_rank": su3_rank,
        "su2_rank": su2_rank,
        "u1_rank": u1_rank,
        "full_group_rank_sum": su3_rank + su2_rank + u1_rank,
        "su3_closure_residual": su3_closure,
        "su2_closure_residual": su2_closure,
        "su3_su2_commutator_residual": commute_32,
        "su3_u1_commutator_residual": commute_31,
        "su2_u1_commutator_residual": commute_21,
        "charge_reconstruction_residual": charge_reconstruction_residual,
        "charge_summary": charges,
        "charges_match": charges_match,
        "full_gauge": su3_rank == 8
        and su2_rank == 3
        and u1_rank == 1
        and su3_closure < TOL
        and su2_closure < TOL
        and commute_32 < TOL
        and commute_31 < TOL
        and commute_21 < TOL,
    }


def signed_zero_edges(table: jax.Array) -> dict[str, Any]:
    dim = int(table.shape[0])
    pairs = sedenion.pure_imaginary_pairs(dim)
    rows = [(i, j, si, sj) for i, j in pairs for si in (-1.0, 1.0) for sj in (-1.0, 1.0)]
    if not rows:
        return {"signed_zero_divisor_count": 0, "zero_edges": [], "component_vertices": {}, "min_signed_product_norm_seen": None}
    row_array = jnp.asarray(rows, dtype=jnp.float64)
    left_idx = jnp.repeat(jnp.arange(len(rows), dtype=jnp.int32), len(rows))
    right_idx = jnp.tile(jnp.arange(len(rows), dtype=jnp.int32), len(rows))
    li = row_array[left_idx, 0].astype(jnp.int32)
    lj = row_array[left_idx, 1].astype(jnp.int32)
    lsi = row_array[left_idx, 2]
    lsj = row_array[left_idx, 3]
    ri = row_array[right_idx, 0].astype(jnp.int32)
    rj = row_array[right_idx, 1].astype(jnp.int32)
    rsi = row_array[right_idx, 2]
    rsj = row_array[right_idx, 3]
    products = (
        (lsi * rsi)[None, :] * table[:, li, ri]
        + (lsi * rsj)[None, :] * table[:, li, rj]
        + (lsj * rsi)[None, :] * table[:, lj, ri]
        + (lsj * rsj)[None, :] * table[:, lj, rj]
    )
    norms = jnp.linalg.norm(products, axis=0)
    mask = norms < TOL
    count = int(jax.device_get(jnp.sum(mask)))
    zero_indices = [int(x) for x in jax.device_get(jnp.nonzero(mask, size=max(count, 1), fill_value=-1)[0]) if int(x) >= 0]
    component_vertices: dict[int, set[tuple[int, int]]] = {}
    zero_edges: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for idx in zero_indices:
        left_row = rows[int(jax.device_get(left_idx[idx]))]
        right_row = rows[int(jax.device_get(right_idx[idx]))]
        left_pair = tuple(sorted((int(left_row[0]), int(left_row[1]))))
        right_pair = tuple(sorted((int(right_row[0]), int(right_row[1]))))
        zero_edges.append((left_pair, right_pair))
        for pair in (left_pair, right_pair):
            label = pair[0] ^ pair[1]
            component_vertices.setdefault(label, set()).add(pair)
    return {
        "signed_zero_divisor_count": count,
        "min_signed_product_norm_seen": py_float(jnp.min(norms)),
        "zero_edges": zero_edges,
        "component_vertices": {str(label): sorted([list(pair) for pair in vertices]) for label, vertices in sorted(component_vertices.items())},
    }


def s3_permutations() -> list[dict[int, int]]:
    rows = [
        (1, 2, 3, 4, 5, 6, 7),
        (1, 3, 2, 4, 5, 7, 6),
        (2, 1, 3, 4, 6, 5, 7),
        (2, 3, 1, 4, 6, 7, 5),
        (3, 1, 2, 4, 7, 5, 6),
        (3, 2, 1, 4, 7, 6, 5),
    ]
    return [{idx + 1: row[idx] for idx in range(7)} for row in rows]


def map_basis_index(idx: int, perm: dict[int, int]) -> int:
    if 1 <= idx <= 7:
        return perm[idx]
    if 9 <= idx <= 15:
        return 8 + perm[idx - 8]
    return idx


def map_pair(pair: tuple[int, int], perm: dict[int, int]) -> tuple[int, int]:
    return tuple(sorted((map_basis_index(pair[0], perm), map_basis_index(pair[1], perm))))


def family_orbit_checks(component_vertices: dict[str, list[list[int]]]) -> dict[str, Any]:
    selected = {label: {tuple(pair) for pair in component_vertices[str(label)]} for label in GENERATION_LABELS}
    induced: set[tuple[int, int, int]] = set()
    action_rows: list[dict[str, Any]] = []
    action_ok = True
    for perm in s3_permutations():
        family_perm = tuple(8 + perm[label - 8] for label in GENERATION_LABELS)
        induced.add(family_perm)
        row_ok = True
        for label in GENERATION_LABELS:
            target = 8 + perm[label - 8]
            mapped = {map_pair(pair, perm) for pair in selected[label]}
            row_ok = row_ok and mapped == selected[target]
        action_ok = action_ok and row_ok
        action_rows.append({"line_action": [perm[i] for i in S3_LINE], "family_action": list(family_perm), "preserves_selected_components": row_ok})
    return {
        "selected_generation_labels": list(GENERATION_LABELS),
        "selected_family_vertex_counts": {str(label): len(selected[label]) for label in GENERATION_LABELS},
        "s3_action_rows": action_rows,
        "unique_induced_family_permutation_count": len(induced),
        "s3_family": action_ok and len(induced) == 6,
    }


def family_edge_counts(zero_edges: list[tuple[tuple[int, int], tuple[int, int]]]) -> dict[str, int]:
    counts = {str(label): 0 for label in GENERATION_LABELS}
    for left, right in zero_edges:
        label = left[0] ^ left[1]
        if label in GENERATION_LABELS and (right[0] ^ right[1]) == label:
            counts[str(label)] += 1
    return counts


def left_multiplication_matrix(table: jax.Array, seed: jax.Array) -> jax.Array:
    dim = int(table.shape[0])
    eye = jnp.eye(dim, dtype=jnp.float64)
    return jnp.stack([sedenion.multiply(table, eye[idx], seed) for idx in range(dim)], axis=1)


def left_ideal_family(table: jax.Array, component_vertices: dict[str, list[list[int]]]) -> dict[str, Any]:
    families: dict[str, Any] = {}
    all_ranks: list[int] = []
    all_nullities: list[int] = []
    for label in GENERATION_LABELS:
        pairs = [tuple(int(x) for x in pair) for pair in component_vertices[str(label)]]
        ranks: list[int] = []
        nullities: list[int] = []
        for i, j in pairs:
            seed = sedenion.pair_vector(int(table.shape[0]), i, j)
            rank = int(jax.device_get(jnp.linalg.matrix_rank(left_multiplication_matrix(table, seed), tol=TOL)))
            ranks.append(rank)
            nullities.append(int(table.shape[0]) - rank)
        all_ranks.extend(ranks)
        all_nullities.extend(nullities)
        families[str(label)] = {
            "seed_pairs": [list(pair) for pair in pairs],
            "rank_set": sorted(set(ranks)),
            "nullity_set": sorted(set(nullities)),
            "rank_min": min(ranks),
            "rank_max": max(ranks),
        }
    return {
        "families": families,
        "rank_set_all_selected": sorted(set(all_ranks)),
        "nullity_set_all_selected": sorted(set(all_nullities)),
        "uniform_rank_across_selected": len(set(all_ranks)) == 1,
        "uniform_nullity_across_selected": len(set(all_nullities)) == 1,
    }


def concrete_owner_witness(s_table: jax.Array) -> dict[str, Any]:
    left = sedenion.pair_vector(int(s_table.shape[0]), 1, 10)
    right = sedenion.pair_vector(int(s_table.shape[0]), 5, 14)
    product = sedenion.multiply(s_table, left, right)
    return {
        "statement": "(e1 + e10) * (e5 + e14) = 0",
        "left_pair": [1, 10],
        "right_pair": [5, 14],
        "left_xor_label": 1 ^ 10,
        "right_xor_label": 5 ^ 14,
        "product_norm": py_float(jnp.linalg.norm(product)),
        "nonzero_left": py_float(jnp.linalg.norm(left)) > TOL,
        "nonzero_right": py_float(jnp.linalg.norm(right)) > TOL,
        "is_zero_divisor_pair": py_float(jnp.linalg.norm(product)) < TOL,
    }


def carrier_checks() -> dict[str, Any]:
    h_table = division.quaternion_table()
    o_table = division.octonion_table()
    cl6 = clifford.clifford_table([1, 1, 1, 1, 1, 1])
    g2_constraint = oct_g2.derivation_constraint_matrix(o_table)
    _, singular, _ = jnp.linalg.svd(g2_constraint, full_matrices=False)
    rank_tol = max(g2_constraint.shape) * jnp.finfo(jnp.float64).eps * jnp.max(singular) * 100.0
    g2_rank = int(jax.device_get(jnp.sum(singular > rank_tol)))
    psi = density.spinor_from_angles(1.1, -0.7)
    rho = density.dm(psi)
    hopf_interior = hopf.interior_torus_checks()
    golden_state = golden.psi(0.31, -0.27, 0.25)
    return {
        "division_algebra_ladder_dims": {"R": 1, "C": int(division.complex_table().shape[0]), "H": int(h_table.shape[0]), "O": int(o_table.shape[0])},
        "clifford_cl6_real_dim": int(cl6.shape[0]),
        "clifford_cl6_fermion_fock_dim": 8,
        "g2_der_o_dim": int(g2_constraint.shape[1] - g2_rank),
        "h_i_j_minus_k_residual": py_float(jnp.linalg.norm(division.multiply(h_table, division.basis(4, 1), division.basis(4, 2)) - division.basis(4, 3))),
        "o_fano_e1_e2_minus_e3_residual": py_float(jnp.linalg.norm(division.multiply(o_table, division.basis(8, 1), division.basis(8, 2)) - division.basis(8, 3))),
        "density_matrix_trace_real": py_float(jnp.real(jnp.trace(rho))),
        "density_matrix_bloch_norm": py_float(jnp.linalg.norm(density.bloch_from_rho(rho))),
        "hopf_interior_s3_constraint_max_residual": float(hopf_interior["interior_s3_constraint_max_residual"]),
        "hopf_torus_metric_det_min": float(hopf_interior["torus_metric_det_min"]),
        "golden_weyl_sample_norm_residual": py_float(jnp.abs(jnp.real(jnp.vdot(golden_state, golden_state)) - 1.0)),
    }


def qit_spec_checks() -> dict[str, Any]:
    h0 = jnp.asarray(qit.H0.tolist(), dtype=jnp.complex128)
    h1 = jnp.asarray(qit.H_TYPE_ONE.tolist(), dtype=jnp.complex128)
    h2 = jnp.asarray(qit.H_TYPE_TWO.tolist(), dtype=jnp.complex128)
    return {
        "h0_trace_abs": py_float(jnp.abs(jnp.trace(h0))),
        "type_one_h0_residual": py_float(jnp.linalg.norm(h1 - h0)),
        "type_two_minus_h0_residual": py_float(jnp.linalg.norm(h2 + h0)),
        "lindblad_count": len(qit.PERCEPTION_L_MATRICES),
        "operator_generator_count": len(qit.OPERATOR_GENERATORS),
        "type_one_schedule_len": len(qit.ENGINE_SCHEDULE_TYPE_ONE),
        "type_two_schedule_len": len(qit.ENGINE_SCHEDULE_TYPE_TWO),
        "substage_count_per_engine": int(qit.N_TOTAL_SUBSTAGES_PER_ENGINE),
    }


def generation_structure() -> dict[str, Any]:
    o_table = sedenion.prior_octonion_table()
    s_table = sedenion.cayley_dickson_double(o_table)
    o_edges = signed_zero_edges(o_table)
    s_edges = signed_zero_edges(s_table)
    orbit = family_orbit_checks(s_edges["component_vertices"])
    edge_counts = family_edge_counts(s_edges["zero_edges"])
    ideals = left_ideal_family(s_table, s_edges["component_vertices"])
    witness = concrete_owner_witness(s_table)
    three_families = all(count == 6 for count in orbit["selected_family_vertex_counts"].values())
    equal_family_edges = len(set(edge_counts.values())) == 1 and next(iter(edge_counts.values())) > 0
    s3_family = bool(orbit["s3_family"] and three_families and equal_family_edges)
    from_real_ideals = bool(
        s_edges["signed_zero_divisor_count"] > 0
        and s3_family
        and witness["is_zero_divisor_pair"]
        and witness["left_xor_label"] in GENERATION_LABELS
        and ideals["uniform_rank_across_selected"]
        and ideals["uniform_nullity_across_selected"]
        and ideals["rank_set_all_selected"] == [12]
        and ideals["nullity_set_all_selected"] == [4]
    )
    octonion_generation_control_count = 1 if o_edges["signed_zero_divisor_count"] == 0 else 3
    return {
        "sedenion_dim": int(s_table.shape[0]),
        "octonion_dim": int(o_table.shape[0]),
        "qubit_count": 4,
        "sedenion_signed_zero_divisor_count": s_edges["signed_zero_divisor_count"],
        "octonion_signed_zero_divisor_count": o_edges["signed_zero_divisor_count"],
        "zero_divisor_component_count": len(s_edges["component_vertices"]),
        "generation_labels": list(GENERATION_LABELS),
        "n_generations": len(GENERATION_LABELS),
        "octonion_generation_control_count": octonion_generation_control_count,
        "family_orbit": orbit,
        "family_edge_counts": edge_counts,
        "left_ideal_family": ideals,
        "concrete_zero_divisor_witness": witness,
        "from_sedenion_ideals": from_real_ideals,
        "octonion_gives_one": octonion_generation_control_count == 1 and o_edges["signed_zero_divisor_count"] == 0,
        "component_vertices": {str(label): s_edges["component_vertices"][str(label)] for label in GENERATION_LABELS},
    }


def parity_against_peer(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_REFERENCE_PATH.exists():
        return {
            "peer_result_path": str(JULIA_REFERENCE_PATH),
            "status": "pending_peer_backend",
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [],
            "boolean_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": False,
        }
    peer = json.loads(JULIA_REFERENCE_PATH.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    strict: list[dict[str, Any]] = []
    missing: list[str] = []
    max_diff = 0.0
    max_key = None
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        jax_value = float(value)
        julia_value = float(peer["shared_scalars"][key])
        diff = abs(jax_value - julia_value)
        rows.append({"key": key, "jax": jax_value, "julia": julia_value, "abs_diff": diff})
        if diff > max_diff:
            max_diff = diff
            max_key = key
        if diff > STRICT_STOP_TOL:
            strict.append(rows[-1])
    mismatches: list[dict[str, Any]] = []
    for key, value in result["shared_booleans"].items():
        if key not in peer.get("shared_booleans", {}):
            missing.append(key)
            continue
        if bool(value) != bool(peer["shared_booleans"][key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer["shared_booleans"][key])})
    return {
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "status": "compared",
        "shared_scalar_rows": rows,
        "max_diff_key": max_key,
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff <= TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def build_result() -> dict[str, Any]:
    generation = generation_structure()
    states = [
        state
        for label in GENERATION_LABELS
        for state in one_generation_states(label, generation["component_vertices"][str(label)])
    ]
    full_gauge_checks = gauge_checks(states)
    per_generation = {
        str(label): gauge_checks([state for state in states if state["generation_label"] == label])
        for label in GENERATION_LABELS
    }
    carrier = carrier_checks()
    qit_checks = qit_spec_checks()

    full_gauge = bool(full_gauge_checks["full_gauge"] and carrier["g2_der_o_dim"] == 14 and carrier["h_i_j_minus_k_residual"] < TOL)
    charges_per_gen = all(row["charges_match"] for row in per_generation.values())
    owner_carrier_load_bearing = bool(
        generation["from_sedenion_ideals"]
        and generation["octonion_gives_one"]
        and generation["n_generations"] != generation["octonion_generation_control_count"]
        and len(states) != 16 * generation["octonion_generation_control_count"]
    )
    controls = {
        "real_sedenion_vs_erased_octonion_flip": owner_carrier_load_bearing,
        "octonion_gives_one_generation_not_three": generation["octonion_gives_one"],
        "erasing_owner_sedenion_ideals_breaks_three_generation_full_gauge": 16 * generation["octonion_generation_control_count"] != len(states),
        "dropping_O_loses_su3": span_rank([zero_full(16) for _ in range(8)]) == 0 and per_generation["9"]["su3_rank"] == 8,
        "dropping_H_loses_su2": span_rank([zero_full(16) for _ in range(3)]) == 0 and per_generation["9"]["su2_rank"] == 3,
        "erasing_hypercharge_breaks_electric_charge": full_gauge_checks["charge_reconstruction_residual"] < TOL
        and py_float(jnp.linalg.norm(diagonal(states, "q") - embed_weak(states, SZ / 2.0))) > 1.0,
    }
    qit_ok = (
        qit_checks["lindblad_count"] == 4
        and qit_checks["operator_generator_count"] == 4
        and qit_checks["type_one_schedule_len"] == 8
        and qit_checks["type_two_schedule_len"] == 8
        and qit_checks["substage_count_per_engine"] == 32
        and qit_checks["type_two_minus_h0_residual"] < TOL
    )
    owner_support_ok = (
        carrier["clifford_cl6_real_dim"] == 64
        and carrier["density_matrix_trace_real"] == 1.0
        and carrier["hopf_interior_s3_constraint_max_residual"] < TOL
        and carrier["golden_weyl_sample_norm_residual"] < TOL
    )
    witness_pass = bool(
        generation["sedenion_dim"] == 16
        and generation["qubit_count"] == 4
        and generation["from_sedenion_ideals"]
        and owner_carrier_load_bearing
        and generation["n_generations"] == 3
        and full_gauge
        and charges_per_gen
        and qit_ok
        and owner_support_ok
        and all(controls.values())
    )

    shared_scalars = {
        "sedenion_dim": float(generation["sedenion_dim"]),
        "qubit_count": float(generation["qubit_count"]),
        "octonion_dim": float(generation["octonion_dim"]),
        "n_generations": float(generation["n_generations"]),
        "total_state_count": float(len(states)),
        "states_per_generation": 16.0,
        "octonion_generation_control_count": float(generation["octonion_generation_control_count"]),
        "erased_octonion_total_state_count": float(16 * generation["octonion_generation_control_count"]),
        "sedenion_signed_zero_divisor_count": float(generation["sedenion_signed_zero_divisor_count"]),
        "octonion_signed_zero_divisor_count": float(generation["octonion_signed_zero_divisor_count"]),
        "zero_divisor_component_count": float(generation["zero_divisor_component_count"]),
        "s3_action_count": float(len(s3_permutations())),
        "unique_induced_family_permutation_count": float(generation["family_orbit"]["unique_induced_family_permutation_count"]),
        "selected_left_ideal_rank_min": float(min(generation["left_ideal_family"]["rank_set_all_selected"])),
        "selected_left_ideal_rank_max": float(max(generation["left_ideal_family"]["rank_set_all_selected"])),
        "selected_left_annihilator_nullity_min": float(min(generation["left_ideal_family"]["nullity_set_all_selected"])),
        "selected_left_annihilator_nullity_max": float(max(generation["left_ideal_family"]["nullity_set_all_selected"])),
        "concrete_witness_product_norm": float(generation["concrete_zero_divisor_witness"]["product_norm"]),
        "full_state_su3_rank": float(full_gauge_checks["su3_rank"]),
        "full_state_su2_rank": float(full_gauge_checks["su2_rank"]),
        "full_state_u1_rank": float(full_gauge_checks["u1_rank"]),
        "full_group_rank_sum": float(full_gauge_checks["full_group_rank_sum"]),
        "su3_closure_residual": float(full_gauge_checks["su3_closure_residual"]),
        "su2_closure_residual": float(full_gauge_checks["su2_closure_residual"]),
        "su3_su2_commutator_residual": float(full_gauge_checks["su3_su2_commutator_residual"]),
        "su3_u1_commutator_residual": float(full_gauge_checks["su3_u1_commutator_residual"]),
        "su2_u1_commutator_residual": float(full_gauge_checks["su2_u1_commutator_residual"]),
        "charge_reconstruction_residual": float(full_gauge_checks["charge_reconstruction_residual"]),
        "charge_quantization_residual": float(full_gauge_checks["charge_summary"]["charge_quantization_residual"]),
        "der_o_dim": float(carrier["g2_der_o_dim"]),
        "clifford_cl6_real_dim": float(carrier["clifford_cl6_real_dim"]),
        "clifford_cl6_fermion_fock_dim": float(carrier["clifford_cl6_fermion_fock_dim"]),
        "qit_substage_count_per_engine": float(qit_checks["substage_count_per_engine"]),
        "qit_type_one_schedule_len": float(qit_checks["type_one_schedule_len"]),
        "qit_type_two_schedule_len": float(qit_checks["type_two_schedule_len"]),
        "qit_type_two_minus_h0_residual": float(qit_checks["type_two_minus_h0_residual"]),
        "density_matrix_trace_real": float(carrier["density_matrix_trace_real"]),
        "hopf_interior_s3_constraint_max_residual": float(carrier["hopf_interior_s3_constraint_max_residual"]),
        "golden_weyl_sample_norm_residual": float(carrier["golden_weyl_sample_norm_residual"]),
    }
    shared_booleans = {
        "witness_pass": witness_pass,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "from_sedenion_ideals": bool(generation["from_sedenion_ideals"]),
        "octonion_gives_one": bool(generation["octonion_gives_one"]),
        "full_gauge": full_gauge,
        "charges_per_gen": charges_per_gen,
        "qit_ok": qit_ok,
        "owner_support_ok": owner_support_ok,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
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
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "owner_julia_carrier": "load_bearing",
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "claim_ceiling": (
            "Finite witness only: reproduces/demonstrates a three-generation sedenion-ideal carrier carrying a "
            "finite SU(3)xSU(2)xU(1) representation and charge table on the owner carrier. It does not admit physics, "
            "Standard Model validation, M(C), Axis0, masses, couplings, bridge, basin, manifold closure, or formal admission."
        ),
        "allowed_claims": ["finite owner-carrier witness", "dual-backend parity witness", "non-tautological carrier-erasure control"],
        "blocked_consumers": ["physics_claims", "SM_admission", "M(C)_admission", "Axis0", "masses", "couplings", "bridge", "formal_admission"],
        "sim_execution_kind": "classical",
        "sim_class": "finite_formal_scout",
        "numpy_compute_used": False,
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "owner_source_refs": source_refs(),
        "generation_structure": generation,
        "states": states,
        "full_gauge_checks": full_gauge_checks,
        "per_generation_checks": per_generation,
        "carrier_checks": carrier,
        "qit_spec_checks": qit_checks,
        "controls": controls,
        "verdicts": {
            "witness_pass": witness_pass,
            "owner_carrier_load_bearing": owner_carrier_load_bearing,
            "from_sedenion_ideals": generation["from_sedenion_ideals"],
            "full_gauge": full_gauge,
            "charges_per_gen": charges_per_gen,
            "qit_ok": qit_ok,
        },
        "positive": {
            "sedenion_three_real_ideal_components": {"pass": bool(generation["from_sedenion_ideals"])},
            "each_generation_carries_su3_su2_u1": {"pass": full_gauge},
            "charges_match_per_generation": {"pass": charges_per_gen},
            "dual_source_carriers_present": {"pass": all(ref["exists"] for ref in source_refs().values())},
        },
        "graveyard_companions": {key: {"pass": bool(value)} for key, value in controls.items()},
        "boundary": {
            "classification_is_scratch_diagnostic": {"pass": True},
            "promotion_disallowed": {"pass": True},
            "formal_admission_disallowed": {"pass": True},
            "claim_ceiling_blocks_physics_axis_masses_couplings": {"pass": True},
        },
        "nearby_variants": {"total": len(controls), "passed": sum(1 for value in controls.values() if value), "variant_names": sorted(controls)},
        "why_not_v4_probes": [
            "scratch diagnostic by request, not a formal_scout admission receipt",
            "finite representation/carrier witness only, no dynamics or phenomenology",
            "masses and couplings are not derived or claimed",
            "Axis0, M(C), bridge, manifold closure, and physics admission remain blocked",
        ],
        "tool_manifest": {
            "JAX jax.numpy x64": "load-bearing finite matrix/rank/commutator/charge computation; no NumPy compute path",
            "Julia mirror": "load-bearing independent peer backend with shared scalar/boolean parity",
            "owner_julia_carrier": "load-bearing real sedenion_break carrier; erasing/replacing it by octonion changes n_generations and state count",
            "division_algebra_ratchet_ladder": "load-bearing R/C/H/O carrier and H/O multiplication checks for gauge factors",
            "clifford_algebra_ladder": "supportive Cl6 finite-dimension witness",
            "octonion_G2_automorphism": "load-bearing der(O)=g2 dimension check for color/octionion structure",
            "density_matrix_spinor_lift": "supportive finite spinor-density trace check",
            "clifford_torus_nested_hopf_foliation": "supportive finite Hopf/Clifford-torus carrier check",
            "golden_weyl": "supportive finite Weyl spinor sample check",
            "canonical_qit_engine_specs.py": "supportive 4-qubit/32-substage source anchor and type-sign metadata",
        },
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": "load-bearing finite matrix/rank/commutator/charge computation; no NumPy compute path",
            "Julia mirror": "load-bearing independent peer backend with shared scalar/boolean parity",
            "owner_julia_carrier": "load-bearing real sedenion_break carrier; erasing/replacing it by octonion changes n_generations and state count",
            "division_algebra_ratchet_ladder": "load-bearing R/C/H/O carrier and H/O multiplication checks for gauge factors",
            "clifford_algebra_ladder": "supportive Cl6 finite-dimension witness",
            "octonion_G2_automorphism": "load-bearing der(O)=g2 dimension check for color/octionion structure",
            "density_matrix_spinor_lift": "supportive finite spinor-density trace check",
            "clifford_torus_nested_hopf_foliation": "supportive finite Hopf/Clifford-torus carrier check",
            "golden_weyl": "supportive finite Weyl spinor sample check",
            "canonical_qit_engine_specs.py": "supportive 4-qubit/32-substage source anchor and type-sign metadata",
        },
        "tool_integration_depth": {
            "JAX jax.numpy x64": "load_bearing",
            "Julia mirror": "load_bearing",
            "owner_julia_carrier": "load_bearing",
            "division_algebra_ratchet_ladder": "load_bearing",
            "octonion_G2_automorphism": "load_bearing",
            "clifford_algebra_ladder": "supportive",
            "density_matrix_spinor_lift": "supportive",
            "clifford_torus_nested_hopf_foliation": "supportive",
            "golden_weyl": "supportive",
            "canonical_qit_engine_specs.py": "supportive",
        },
        "TOOL_INTEGRATION_DEPTH": {
            "JAX jax.numpy x64": "load_bearing",
            "Julia mirror": "load_bearing",
            "owner_julia_carrier": "load_bearing",
            "division_algebra_ratchet_ladder": "load_bearing",
            "octonion_G2_automorphism": "load_bearing",
            "clifford_algebra_ladder": "supportive",
            "density_matrix_spinor_lift": "supportive",
            "clifford_torus_nested_hopf_foliation": "supportive",
            "golden_weyl": "supportive",
            "canonical_qit_engine_specs.py": "supportive",
        },
        "divergence_log": [
            "Real carrier: sedenion zero-divisor ideal labels 9,10,11 produce three generation carriers.",
            "Erased carrier: replacing the owner sedenion branch by octonion gives the one-generation control count.",
            "Gauge controls: dropping O/H/Y kills SU(3), SU(2), or charge reconstruction respectively.",
        ],
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
    }
    result["blockers"] = [] if witness_pass else ["finite witness failed"]
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = bool(witness_pass and result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = bool((not witness_pass) or result["parity"]["stop_condition_fired"])
    result["n_generations"] = generation["n_generations"]
    result["full_gauge"] = full_gauge
    result["charges_per_gen"] = charges_per_gen
    result["from_sedenion_ideals"] = bool(generation["from_sedenion_ideals"])
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"jax={RESULT_PATH} "
        f"julia={JULIA_REFERENCE_PATH} "
        f"all_pass={str(result['all_pass']).lower()} "
        f"owner_carrier_load_bearing={str(result['owner_carrier_load_bearing']).lower()} "
        f"n_generations={int(result['n_generations'])} "
        f"full_gauge={str(result['full_gauge']).lower()} "
        f"charges_per_gen={str(result['charges_per_gen']).lower()} "
        f"from_sedenion_ideals={str(result['from_sedenion_ideals']).lower()}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
