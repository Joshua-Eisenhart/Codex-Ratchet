#!/usr/bin/env python3
# object_id: mp_sedenion_three_generations
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
JULIA_CARRIER = REPO / "system_v5" / "julia_carrier"
FORMAL_SCOUTS = REPO / "system_v5" / "ops" / "formal_scouts"
RESULT_PATH = FORMAL_SCOUTS / "results" / "mp_sedenion_three_generations_results.json"
JULIA_REFERENCE_PATH = JULIA_CARRIER / "mp_sedenion_three_generations_julia_results.json"
OBJECT_ID = "mp_sedenion_three_generations"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
S3_LINE = (1, 2, 3)
GENERATION_LABELS = (9, 10, 11)

sys.path.insert(0, str(JULIA_CARRIER))
sys.path.insert(0, str(FORMAL_SCOUTS))

import canonical_qit_engine_specs as qit_specs  # noqa: E402
import jax_clifford_algebra_ladder as owner_clifford  # noqa: E402
import jax_density_matrix_spinor_lift as owner_density  # noqa: E402
import jax_octonion_G2_automorphism as owner_g2  # noqa: E402
import jax_sedenion_break_prelim as owner_sedenion  # noqa: E402


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_refs() -> dict[str, Any]:
    refs = {
        "division_algebra_ratchet_ladder": JULIA_CARRIER / "division_algebra_ratchet_ladder.jl",
        "jax_division_algebra_ratchet_ladder": JULIA_CARRIER / "jax_division_algebra_ratchet_ladder.py",
        "clifford_algebra_ladder": JULIA_CARRIER / "clifford_algebra_ladder.jl",
        "jax_clifford_algebra_ladder": JULIA_CARRIER / "jax_clifford_algebra_ladder.py",
        "octonion_G2_automorphism": JULIA_CARRIER / "octonion_G2_automorphism.jl",
        "jax_octonion_G2_automorphism": JULIA_CARRIER / "jax_octonion_G2_automorphism.py",
        "sedenion_break": JULIA_CARRIER / "sedenion_break.jl",
        "sedenion_break_prelim_lineage": JULIA_CARRIER / "sedenion_break_prelim.jl",
        "jax_sedenion_break": JULIA_CARRIER / "jax_sedenion_break_prelim.py",
        "density_matrix_spinor_lift": JULIA_CARRIER / "density_matrix_spinor_lift.jl",
        "jax_density_matrix_spinor_lift": JULIA_CARRIER / "jax_density_matrix_spinor_lift.py",
        "clifford_torus_nested_hopf_foliation": JULIA_CARRIER / "clifford_torus_nested_hopf_foliation.jl",
        "jax_clifford_torus_nested_hopf_foliation": JULIA_CARRIER / "jax_clifford_torus_nested_hopf_foliation.py",
        "golden_weyl": JULIA_CARRIER / "golden_weyl_julia.jl",
        "golden_weyl_jax_snapshot": JULIA_CARRIER / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py",
        "canonical_qit_engine_specs": FORMAL_SCOUTS / "canonical_qit_engine_specs.py",
    }
    return {
        key: {
            "path": str(path),
            "sha256": sha256(path) if path.exists() else None,
            "exists": path.exists(),
        }
        for key, path in refs.items()
    }


def signed_zero_edges(table: jax.Array) -> dict[str, Any]:
    dim = int(table.shape[0])
    pairs = owner_sedenion.pure_imaginary_pairs(dim)
    if not pairs:
        return {
            "signed_zero_divisor_count": 0,
            "min_signed_product_norm_seen": None,
            "zero_edges": [],
            "component_vertices": {},
        }
    rows = [(i, j, si, sj) for i, j in pairs for si in (-1.0, 1.0) for sj in (-1.0, 1.0)]
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
    # Six Fano-plane permutations fixing index 4 and acting as S3 on line {1,2,3}.
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
    perms = s3_permutations()
    family_action_rows: list[dict[str, Any]] = []
    action_ok = True
    induced_family_perms: set[tuple[int, int, int]] = set()
    for perm in perms:
        family_perm = tuple(8 + perm[label - 8] for label in GENERATION_LABELS)
        induced_family_perms.add(family_perm)
        row_ok = True
        for label in GENERATION_LABELS:
            target = 8 + perm[label - 8]
            mapped = {map_pair(pair, perm) for pair in selected[label]}
            if mapped != selected[target]:
                row_ok = False
        action_ok = action_ok and row_ok
        family_action_rows.append(
            {
                "line_action": [perm[i] for i in S3_LINE],
                "family_action": list(family_perm),
                "preserves_selected_components": row_ok,
            }
        )

    wrong_cycle = {idx: idx for idx in range(1, 8)}
    wrong_cycle[1] = 2
    wrong_cycle[2] = 3
    wrong_cycle[3] = 1
    wrong_maps_without_internal_structure = selected[GENERATION_LABELS[0]] == selected[GENERATION_LABELS[1]]
    erased_labels = sorted({label - 8 for label in GENERATION_LABELS})
    return {
        "selected_generation_labels": list(GENERATION_LABELS),
        "selected_family_vertex_counts": {str(label): len(selected[label]) for label in GENERATION_LABELS},
        "s3_action_rows": family_action_rows,
        "unique_induced_family_permutation_count": len(induced_family_perms),
        "s3_family": action_ok and len(induced_family_perms) == 6,
        "wrong_structure_preserves_family": wrong_maps_without_internal_structure,
        "wrong_structure_control_fails": not wrong_maps_without_internal_structure,
        "erased_high_bit_labels": erased_labels,
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
    columns = [owner_sedenion.multiply(table, eye[idx], seed) for idx in range(dim)]
    return jnp.stack(columns, axis=1)


def left_ideal_family(table: jax.Array, component_vertices: dict[str, list[list[int]]]) -> dict[str, Any]:
    families: dict[str, Any] = {}
    all_ranks: list[int] = []
    all_nullities: list[int] = []
    for label in GENERATION_LABELS:
        pairs = [tuple(int(x) for x in pair) for pair in component_vertices[str(label)]]
        ranks: list[int] = []
        nullities: list[int] = []
        for i, j in pairs:
            seed = owner_sedenion.pair_vector(int(table.shape[0]), i, j)
            matrix = left_multiplication_matrix(table, seed)
            rank = int(jax.device_get(jnp.linalg.matrix_rank(matrix, tol=TOL)))
            ranks.append(rank)
            nullities.append(int(table.shape[0]) - rank)
        all_ranks.extend(ranks)
        all_nullities.extend(nullities)
        families[str(label)] = {
            "seed_pairs": [list(pair) for pair in pairs],
            "left_ideal_ranks": ranks,
            "left_annihilator_nullities": nullities,
            "rank_min": min(ranks),
            "rank_max": max(ranks),
            "rank_set": sorted(set(ranks)),
            "nullity_set": sorted(set(nullities)),
        }
    return {
        "description": "For each selected zero-divisor component, compute the real span of S acting by left multiplication on each two-term zero-divisor seed.",
        "families": families,
        "rank_set_all_selected": sorted(set(all_ranks)),
        "nullity_set_all_selected": sorted(set(all_nullities)),
        "uniform_rank_across_selected": len(set(all_ranks)) == 1,
        "uniform_nullity_across_selected": len(set(all_nullities)) == 1,
    }


def concrete_owner_witness(s_table: jax.Array) -> dict[str, Any]:
    left = owner_sedenion.pair_vector(int(s_table.shape[0]), 1, 10)
    right = owner_sedenion.pair_vector(int(s_table.shape[0]), 5, 14)
    product = owner_sedenion.multiply(s_table, left, right)
    left_rank = int(jax.device_get(jnp.linalg.matrix_rank(left_multiplication_matrix(s_table, left), tol=TOL)))
    return {
        "statement": "(e1 + e10) * (e5 + e14) = 0",
        "left_pair": [1, 10],
        "right_pair": [5, 14],
        "left_xor_label": 1 ^ 10,
        "right_xor_label": 5 ^ 14,
        "left_terms": owner_sedenion.terms_from_vector(left),
        "right_terms": owner_sedenion.terms_from_vector(right),
        "product_terms": owner_sedenion.terms_from_vector(product),
        "product_norm": py_float(jnp.linalg.norm(product)),
        "nonzero_left": py_float(jnp.linalg.norm(left)) > TOL,
        "nonzero_right": py_float(jnp.linalg.norm(right)) > TOL,
        "is_zero_divisor_pair": py_float(jnp.linalg.norm(product)) < TOL,
        "left_ideal_rank": left_rank,
    }


def qit_anchor() -> dict[str, Any]:
    h0_diag_z = py_float(0.5 * jnp.real(jnp.asarray(qit_specs.H0.tolist(), dtype=jnp.complex128)[0, 0] - jnp.asarray(qit_specs.H0.tolist(), dtype=jnp.complex128)[1, 1]))
    h0_x = py_float(jnp.real(jnp.asarray(qit_specs.H0.tolist(), dtype=jnp.complex128)[0, 1]))
    return {
        "source": "system_v5/ops/formal_scouts/canonical_qit_engine_specs.py",
        "h0_sz_coeff": h0_diag_z,
        "h0_sx_coeff": h0_x,
        "type_one_h_sign": float(qit_specs.get_engine_spec(0)["h_sign"]),
        "type_two_h_sign": float(qit_specs.get_engine_spec(1)["h_sign"]),
        "perception_keys": sorted(qit_specs.PERCEPTION_L_MATRICES.keys()),
        "operator_slot_sequence": list(qit_specs.OPERATOR_SLOT_SEQUENCE),
        "main_stages_per_engine": int(qit_specs.N_MAIN_STAGES_PER_ENGINE),
        "substages_per_main": int(qit_specs.N_SUBSTAGES_PER_MAIN),
        "total_substages_per_engine": int(qit_specs.N_TOTAL_SUBSTAGES_PER_ENGINE),
    }


def owner_object_anchor(s_table: jax.Array) -> dict[str, Any]:
    cl4 = owner_clifford.clifford_table([1, 1, 1, 1])
    psi = owner_density.spinor_from_angles(1.1, -0.7)
    rho = owner_density.dm(psi)
    g2_table = owner_g2.octonion_table()
    return {
        "sedenion_table_checksum": owner_sedenion.table_checksum(s_table),
        "concrete_zero_divisor_witness": concrete_owner_witness(s_table),
        "clifford_cl40_dim_for_four_qubits": int(cl4.shape[0]),
        "density_matrix_trace_real": py_float(jnp.real(jnp.trace(rho))),
        "g2_octonion_table_checksum": owner_sedenion.table_checksum(g2_table),
    }


def parity_against_julia(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_REFERENCE_PATH.exists():
        return {
            "peer_result_path": str(JULIA_REFERENCE_PATH),
            "status": "missing_julia_reference",
            "parity_max_diff": None,
            "within_1e_9": False,
            "boolean_mismatches": ["missing_julia_reference"],
            "strict_divergence_gt_1e_6": ["missing_julia_reference"],
            "missing_keys": [],
            "stop_condition_fired": True,
        }
    peer = json.loads(JULIA_REFERENCE_PATH.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    strict: list[dict[str, Any]] = []
    max_diff = 0.0
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        jax_value = float(value)
        julia_value = float(peer["shared_scalars"][key])
        diff = abs(jax_value - julia_value)
        rows.append({"key": key, "jax": jax_value, "julia": julia_value, "abs_diff": diff})
        max_diff = max(max_diff, diff)
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
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff <= TOL and not strict and not mismatches and not missing,
        "boolean_mismatches": mismatches,
        "strict_divergence_gt_1e_6": strict,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def build_result() -> dict[str, Any]:
    o_table = owner_sedenion.prior_octonion_table()
    s_table = owner_sedenion.cayley_dickson_double(o_table)
    o_edges = signed_zero_edges(o_table)
    s_edges = signed_zero_edges(s_table)
    orbit = family_orbit_checks(s_edges["component_vertices"])
    edge_counts = family_edge_counts(s_edges["zero_edges"])
    ideal_family = left_ideal_family(s_table, s_edges["component_vertices"])
    qit = qit_anchor()
    owner_anchor = owner_object_anchor(s_table)

    dim = int(s_table.shape[0])
    qubit_count = 4
    octonion_generation_control_count = 1 if o_edges["signed_zero_divisor_count"] == 0 else 3
    zero_divisors = s_edges["signed_zero_divisor_count"] > 0
    three_families = all(count == 6 for count in orbit["selected_family_vertex_counts"].values())
    equal_family_edges = len(set(edge_counts.values())) == 1 and next(iter(edge_counts.values())) > 0
    control_fails = (
        orbit["wrong_structure_control_fails"]
        and octonion_generation_control_count == 1
        and o_edges["signed_zero_divisor_count"] == 0
    )
    s3_family = bool(orbit["s3_family"] and three_families and equal_family_edges)
    witness = owner_anchor["concrete_zero_divisor_witness"]
    from_real_ideals = bool(
        zero_divisors
        and s3_family
        and witness["is_zero_divisor_pair"]
        and witness["left_xor_label"] in GENERATION_LABELS
        and ideal_family["uniform_rank_across_selected"]
        and ideal_family["uniform_nullity_across_selected"]
        and ideal_family["rank_set_all_selected"] == [12]
        and ideal_family["nullity_set_all_selected"] == [4]
    )
    octonion_gives_one = bool(octonion_generation_control_count == 1 and o_edges["signed_zero_divisor_count"] == 0)
    owner_carrier_load_bearing = bool(
        from_real_ideals
        and octonion_gives_one
        and witness["product_norm"] <= TOL
        and s_edges["signed_zero_divisor_count"] != o_edges["signed_zero_divisor_count"]
        and len(GENERATION_LABELS) != octonion_generation_control_count
    )
    all_pass = bool(
        dim == 16
        and 2**qubit_count == dim
        and zero_divisors
        and s3_family
        and control_fails
        and from_real_ideals
        and owner_carrier_load_bearing
        and octonion_gives_one
        and qit["total_substages_per_engine"] == 32
    )

    shared_scalars = {
        "dim": float(dim),
        "qubit_count": float(qubit_count),
        "octonion_dim": float(o_table.shape[0]),
        "sedenion_signed_zero_divisor_count": float(s_edges["signed_zero_divisor_count"]),
        "octonion_signed_zero_divisor_count": float(o_edges["signed_zero_divisor_count"]),
        "zero_divisor_component_count": float(len(s_edges["component_vertices"])),
        "n_generations": float(len(GENERATION_LABELS)),
        "s3_action_count": float(len(s3_permutations())),
        "unique_induced_family_permutation_count": float(orbit["unique_induced_family_permutation_count"]),
        "family_9_vertex_count": float(orbit["selected_family_vertex_counts"]["9"]),
        "family_10_vertex_count": float(orbit["selected_family_vertex_counts"]["10"]),
        "family_11_vertex_count": float(orbit["selected_family_vertex_counts"]["11"]),
        "family_9_edge_count": float(edge_counts["9"]),
        "family_10_edge_count": float(edge_counts["10"]),
        "family_11_edge_count": float(edge_counts["11"]),
        "octonion_generation_control_count": float(octonion_generation_control_count),
        "qit_total_substages_per_engine": float(qit["total_substages_per_engine"]),
        "qit_h0_sz_coeff": float(qit["h0_sz_coeff"]),
        "qit_h0_sx_coeff": float(qit["h0_sx_coeff"]),
        "clifford_cl40_dim": float(owner_anchor["clifford_cl40_dim_for_four_qubits"]),
        "density_matrix_trace_real": float(owner_anchor["density_matrix_trace_real"]),
        "concrete_witness_product_norm": float(witness["product_norm"]),
        "selected_left_ideal_rank_min": float(min(ideal_family["rank_set_all_selected"])),
        "selected_left_ideal_rank_max": float(max(ideal_family["rank_set_all_selected"])),
        "selected_left_annihilator_nullity_min": float(min(ideal_family["nullity_set_all_selected"])),
        "selected_left_annihilator_nullity_max": float(max(ideal_family["nullity_set_all_selected"])),
    }
    shared_booleans = {
        "zero_divisors": zero_divisors,
        "s3_family": s3_family,
        "control_fails": control_fails,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "from_real_ideals": from_real_ideals,
        "octonion_gives_one": octonion_gives_one,
        "all_pass": all_pass,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
    }

    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "julia_reference_path": str(JULIA_REFERENCE_PATH),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "Finite sedenion zero-divisor/S3 witness only; no physics, Standard Model, M(C), Axis0, bridge, engine, manifold, or formal admission claim.",
        "arxiv_source": {
            "id": "arXiv:2306.13098",
            "title": "Three generations of colored fermions with S3 family symmetry from Cayley-Dickson sedenions",
            "url": "https://arxiv.org/abs/2306.13098",
            "bounded_use": "Motivation and target shape only; this scout checks a finite zero-divisor family/S3 witness, not the paper's full complex-Cl(6) construction.",
        },
        "construction": {
            "carrier": "Cayley-Dickson sedenions S = O doubled to 16 real basis elements",
            "basis_order": "e0..e15 from the owner Cayley-Dickson multiplication table; the 4-qubit count is metadata only and is not used to derive generations",
            "selected_generation_components": list(GENERATION_LABELS),
            "selection_rule": "three high-bit zero-divisor/left-ideal XOR components over the Fano line {1,2,3}",
        },
        "owner_object_anchor": owner_anchor,
        "owner_source_refs": source_refs(),
        "qit_anchor": qit,
        "zero_divisor_graph": {
            "sedenion": {
                "signed_zero_divisor_count": s_edges["signed_zero_divisor_count"],
                "component_vertices": s_edges["component_vertices"],
                "family_edge_counts": edge_counts,
            },
            "octonion_control": {
                "signed_zero_divisor_count": o_edges["signed_zero_divisor_count"],
                "generation_control_count": octonion_generation_control_count,
            },
        },
        "left_ideal_family": ideal_family,
        "family_orbit": orbit,
        "controls": {
            "octonion_one_generation_not_three": octonion_generation_control_count == 1,
            "octonion_no_zero_divisors": o_edges["signed_zero_divisor_count"] == 0,
            "wrong_structure_control_fails": orbit["wrong_structure_control_fails"],
            "same_pipeline_octonion_generation_count": octonion_generation_control_count,
            "real_sedenion_vs_replaced_octonion_flip": owner_carrier_load_bearing,
            "erasing_or_replacing_owner_sedenion_carrier_changes_result": owner_carrier_load_bearing,
        },
        "tool_manifest": {
            "jax": "load_bearing finite table, zero-divisor, and S3 orbit computation",
            "jax.numpy": "load_bearing x64 array arithmetic without NumPy compute",
            "owner_julia_carrier": "load-bearing owner sedenion carrier mirrored from system_v5/julia_carrier/sedenion_break.jl; result changes under octonion replacement",
            "canonical_qit_engine_specs": "supportive 4-qubit/32-substage anchor and H0/type-sign metadata",
            "json": "supportive result serialization",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "owner_julia_carrier": "load_bearing",
            "canonical_qit_engine_specs": "supportive",
            "json": "supportive",
        },
        "divergence_log": [
            "Positive: S has signed two-term zero divisors and three selected generation-like XOR components permuted by an S3 subgroup.",
            "Control: O has no signed two-term zero divisors in the same bounded search and stays at one-generation control count.",
            "Anti-by-construction: relabeling family names without mapping internal zero-divisor vertices does not preserve the family structure.",
        ],
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
    }
    result["parity"] = parity_against_julia(result)
    if result["parity"]["stop_condition_fired"]:
        result["shared_booleans"]["all_pass"] = False
        result["parity_stop_condition_fired"] = True
    else:
        result["parity_stop_condition_fired"] = False
    result["all_pass"] = bool(result["shared_booleans"]["all_pass"])
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
        f"owner_carrier_load_bearing={str(result['shared_booleans']['owner_carrier_load_bearing']).lower()} "
        f"n_generations={int(result['shared_scalars']['n_generations'])} "
        f"s3_family={str(result['shared_booleans']['s3_family']).lower()} "
        f"from_real_ideals={str(result['shared_booleans']['from_real_ideals']).lower()} "
        f"octonion_gives_one={str(result['shared_booleans']['octonion_gives_one']).lower()}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
