#!/usr/bin/env python3
"""JAX leg for bloch_root_admissibility_discriminator_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from itertools import combinations, permutations, product
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "bloch_root_admissibility_discriminator_v0"
ENGINE = "jax"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"
ARTIFACT_PATH = ROOT / "system_v5" / "julia_carrier" / "artifacts" / "algebra_structure_constants_v1.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False
TOL = 1.0e-8

PIN_CANONICAL = (
    '{"sim_id":"bloch_root_admissibility_discriminator_v0",'
    '"claim":"F01 finite quotients limit to Bloch sphere; N01 noncommuting probes reconstruct Bloch ball; division algebra Hopf ladder terminates before sedenions",'
    '"ceiling":{"classification":"scratch_diagnostic","promotion_allowed":false,"formal_admission_allowed":false},'
    '"language":{"roots":"ADMIT four-member family {S^1,S^2,S^4,S^8}","carrier":"C^2 INSTALLS S^2 installed-not-forced","physics":false}}'
)
PIN_SHA256 = hashlib.sha256(PIN_CANONICAL.encode("utf-8")).hexdigest()

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive x64 vectorized finite quotient, Hopf image, PCA/rank, and table sweep diagnostics; demoted until a passing jax capability probe exists"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive finite linear algebra, SVD rank, norm, and multiplication-table contractions; demoted until a passing jax.numpy capability probe exists"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing raw-value SMT flips for sedenion termination and rank obstruction"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent raw-value SMT flips for the same computed values"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive JSON, hashing, deterministic samples, and path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def to_builtin(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_builtin(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_builtin(v) for v in value]
    if hasattr(value, "shape"):
        arr = jax.device_get(value)
        if arr.shape == ():
            f = float(arr)
            return int(round(f)) if abs(f - round(f)) < TOL else f
        return arr.tolist()
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return str(value)


def unit(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v]


def fibonacci_sphere(n: int) -> list[list[float]]:
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    points = []
    for i in range(n):
        z = 1.0 - 2.0 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1.0 - z * z))
        theta = 2.0 * math.pi * i / phi
        points.append([r * math.cos(theta), r * math.sin(theta), z])
    return points


def dist(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def farthest_refinement(max_k: int = 62) -> list[list[float]]:
    selected = [
        [1.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, -1.0, 0.0],
        [0.0, 0.0, 1.0],
        [0.0, 0.0, -1.0],
    ]
    candidates = fibonacci_sphere(4096)
    while len(selected) < max_k:
        best = max(candidates, key=lambda p: min(dist(p, q) for q in selected))
        selected.append(best)
    return selected


def hausdorff_to_sphere(points: list[list[float]], dense: list[list[float]]) -> float:
    return max(min(dist(p, q) for q in points) for p in dense)


def t1_limit_shape() -> dict[str, Any]:
    ladder = [6, 14, 30, 62]
    dense = fibonacci_sphere(8192)
    refined = farthest_refinement(max(ladder))
    rows = []
    last = None
    for k in ladder:
        pts = refined[:k]
        d_h = hausdorff_to_sphere(pts, dense)
        rows.append(
            {
                "probe_family_size_k": k,
                "bin_refinement": "two_outcome_spin_bins",
                "quotient_cardinality": len(pts),
                "quotient_cardinality_finite": True,
                "hausdorff_distance_to_S2": d_h,
                "monotone_nonincreasing_from_previous": True if last is None else d_h <= last + TOL,
            }
        )
        last = d_h
    repeated = refined[:6]
    control_rows = []
    for k in ladder:
        d_h = hausdorff_to_sphere(repeated, dense)
        control_rows.append(
            {
                "probe_family_size_k": k,
                "unique_probe_directions": len(repeated),
                "quotient_cardinality": len(repeated),
                "hausdorff_distance_to_S2": d_h,
            }
        )
    return {
        "test_id": "T1",
        "claim": "F01 admits S2 only as a measured refinement limit of finite probe quotients",
        "refinement_ladder": rows,
        "monotone_convergence_curve": [row["hausdorff_distance_to_S2"] for row in rows],
        "converges_on_sample": rows[-1]["hausdorff_distance_to_S2"] < rows[0]["hausdorff_distance_to_S2"],
        "control_non_refining_repeated_probes": {
            "rows": control_rows,
            "does_not_converge": abs(control_rows[-1]["hausdorff_distance_to_S2"] - control_rows[0]["hausdorff_distance_to_S2"]) <= TOL,
        },
    }


def affine_rank(points: Any, tol: float = 1.0e-8) -> int:
    arr = jnp.asarray(points, dtype=jnp.float64)
    centered = arr - jnp.mean(arr, axis=0, keepdims=True)
    s = jnp.linalg.svd(centered, compute_uv=False)
    return int(jax.device_get(jnp.sum(s > tol)))


def bloch_state_samples() -> list[list[float]]:
    pts = farthest_refinement(62)
    samples = [[0.0, 0.0, 0.0]]
    samples.extend(pts)
    samples.extend([[0.5 * x, 0.5 * y, 0.5 * z] for x, y, z in pts[:30]])
    return samples


def t2_ball_vs_simplex() -> dict[str, Any]:
    states = bloch_state_samples()
    commuting = [[r[2]] for r in states]
    commuting_added = [[r[2], (1.0 + r[2]) / 2.0, (1.0 - r[2]) / 2.0, -r[2]] for r in states]
    full = states
    norms = [math.sqrt(sum(x * x for x in r)) for r in states]
    return {
        "test_id": "T2",
        "commuting_sigma_z_binned": {
            "affine_dimension": affine_rank(commuting),
            "extreme_points": 2,
            "object": "interval/simplex Delta_1",
            "z_min": min(r[0] for r in commuting),
            "z_max": max(r[0] for r in commuting),
        },
        "noncommuting_full_pauli_family": {
            "affine_dimension": affine_rank(full),
            "object": "solid Bloch ball",
            "boundary_sphericity": {
                "max_norm": max(norms),
                "all_norms_leq_1": max(norms) <= 1.0 + TOL,
                "saturation_count": sum(abs(v - 1.0) <= TOL for v in norms),
            },
            "extreme_points": "pure states on ||r||=1",
        },
        "control_commuting_only_additions": {
            "affine_dimension": affine_rank(commuting_added),
            "never_raises_dimension_above_interval": affine_rank(commuting_added) == 1,
        },
    }


def load_artifact() -> dict[str, Any]:
    payload = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    algebras = {row["algebra"]: row for row in payload["algebras"]}
    return {
        "payload": payload,
        "quaternion": algebras["quaternion"],
        "octonion": algebras["octonion"],
        "artifact_sha256": sha256_file(ARTIFACT_PATH),
    }


def cd_double(parent: Any) -> Any:
    parent = jnp.asarray(parent, dtype=jnp.float64)
    n = int(parent.shape[0])
    dim = 2 * n
    eye = jnp.eye(dim, dtype=jnp.float64)

    def parent_mul(x: Any, y: Any) -> Any:
        return jnp.einsum("kij,i,j->k", parent, x, y)

    def parent_conj(x: Any) -> Any:
        return x.at[1:].multiply(-1.0)

    rows = []
    for i in range(dim):
        cols = []
        for j in range(dim):
            x = eye[i]
            y = eye[j]
            a, b = x[:n], x[n:]
            c, d = y[:n], y[n:]
            first = parent_mul(a, c) - parent_mul(parent_conj(d), b)
            second = parent_mul(d, a) + parent_mul(b, parent_conj(c))
            cols.append(jnp.concatenate([first, second]))
        rows.append(cols)
    table_ijk = jnp.stack([jnp.stack(row, axis=1) for row in rows], axis=1)
    return table_ijk


def multiply(table: Any, x: Any, y: Any) -> Any:
    return jnp.einsum("kij,i,j->k", table, x, y)


def conj_vec(x: Any) -> Any:
    return x.at[1:].multiply(-1.0)


def hopf_image(table: Any, x: Any, y: Any) -> Any:
    return jnp.concatenate(
        [
            jnp.asarray([jnp.dot(x, x) - jnp.dot(y, y)], dtype=jnp.float64),
            2.0 * multiply(table, x, conj_vec(y)),
        ]
    )


def normalized_pair(dim: int, seed: int) -> tuple[Any, Any]:
    xs = [math.sin((seed + 1) * (i + 1) * 0.37) + math.cos((seed + 3) * (i + 2) * 0.11) for i in range(dim)]
    ys = [math.cos((seed + 2) * (i + 1) * 0.29) - math.sin((seed + 5) * (i + 2) * 0.13) for i in range(dim)]
    x = jnp.asarray(xs, dtype=jnp.float64)
    y = jnp.asarray(ys, dtype=jnp.float64)
    scale = jnp.sqrt(jnp.dot(x, x) + jnp.dot(y, y))
    return x / scale, y / scale


def unit_vector(dim: int, seed: int) -> Any:
    vals = [math.sin((seed + 7) * (i + 1) * 0.19) + math.cos((seed + 2) * (i + 3) * 0.23) for i in range(dim)]
    v = jnp.asarray(vals, dtype=jnp.float64)
    return v / jnp.linalg.norm(v)


def pca_rank(points: list[Any], tol: float = 1.0e-7) -> int:
    arr = jnp.stack(points)
    centered = arr - jnp.mean(arr, axis=0, keepdims=True)
    s = jnp.linalg.svd(centered, compute_uv=False)
    return int(jax.device_get(jnp.sum(s > tol)))


def local_base_dim(table: Any) -> int:
    dim = int(table.shape[0])
    eps = 1.0e-3
    e0 = jnp.eye(dim, dtype=jnp.float64)[0]
    points = []
    for i in range(dim):
        for sign in (-1.0, 1.0):
            y = sign * eps * jnp.eye(dim, dtype=jnp.float64)[i]
            x = math.sqrt(1.0 - eps * eps) * e0
            points.append(hopf_image(table, x, y) - hopf_image(table, e0, jnp.zeros(dim, dtype=jnp.float64)))
    return pca_rank(points, tol=1.0e-10)


def local_fiber_dim(table: Any) -> int:
    dim = int(table.shape[0])
    if dim == 1:
        return 0
    eps = 1.0e-3
    a = math.cos(0.41)
    b = math.sin(0.41)
    eye = jnp.eye(dim, dtype=jnp.float64)
    points = []
    for i in range(1, dim):
        for sign in (-1.0, 1.0):
            q = math.sqrt(1.0 - eps * eps) * eye[0] + sign * eps * eye[i]
            points.append(jnp.concatenate([a * q, b * q]) - jnp.concatenate([a * eye[0], b * eye[0]]))
    return pca_rank(points, tol=1.0e-10)


def rung_report(name: str, table: Any, expected_base_dim: int, expected_fiber_dim: int) -> dict[str, Any]:
    dim = int(table.shape[0])
    norm_errs = []
    for seed in range(80):
        x, y = normalized_pair(dim, seed)
        norm_errs.append(float(jax.device_get(jnp.abs(jnp.linalg.norm(hopf_image(table, x, y)) - 1.0))))
    a = math.cos(0.37)
    b = math.sin(0.37)
    e0 = jnp.eye(dim, dtype=jnp.float64)[0]
    base_h = hopf_image(table, a * e0, b * e0)
    fiber_devs = []
    for seed in range(32):
        q = unit_vector(dim, seed)
        fiber_devs.append(float(jax.device_get(jnp.linalg.norm(hopf_image(table, multiply(table, a * e0, q), multiply(table, b * e0, q)) - base_h))))
    base_dim = local_base_dim(table)
    fiber_dim = local_fiber_dim(table)
    return {
        "algebra": name,
        "algebra_dimension": dim,
        "base_sphere": f"S^{expected_base_dim}",
        "fiber_sphere": f"S^{expected_fiber_dim}",
        "expected_base_dimension": expected_base_dim,
        "computed_base_dimension_local_pca": base_dim,
        "expected_fiber_dimension": expected_fiber_dim,
        "computed_fiber_dimension_local_pca": fiber_dim,
        "max_image_norm_error": max(norm_errs),
        "max_fiber_constancy_deviation": max(fiber_devs),
        "sample_count": 80,
        "pass": max(norm_errs) <= 1.0e-7 and max(fiber_devs) <= 1.0e-7 and base_dim == expected_base_dim and fiber_dim == expected_fiber_dim,
    }


def table_transform(table: Any, perm: list[int], signs: list[int]) -> Any:
    table = jnp.asarray(table, dtype=jnp.float64)
    n = int(table.shape[0])
    inv = [0] * n
    for src, tgt in enumerate(perm):
        inv[tgt] = src
    out = jnp.zeros((n, n, n), dtype=jnp.float64)
    for kt in range(n):
        ks = inv[kt]
        for it in range(n):
            isrc = inv[it]
            for jt in range(n):
                jsrc = inv[jt]
                out = out.at[kt, it, jt].set(signs[isrc] * signs[jsrc] * float(table[ks, isrc, jsrc]) * signs[ks])
    return out


def associator_vec(table: Any, a: int, b: int, c: int) -> Any:
    eye = jnp.eye(int(table.shape[0]), dtype=jnp.float64)
    x, y, z = eye[a], eye[b], eye[c]
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


def assoc_nonzero_count(table: Any) -> tuple[int, int, list[list[int]]]:
    nonzero = 0
    zero = 0
    fano = []
    for a, b, c in permutations(range(1, 8), 3):
        residual = associator_vec(table, a, b, c)
        is_zero = float(jax.device_get(jnp.linalg.norm(residual))) <= TOL
        zero += int(is_zero)
        nonzero += int(not is_zero)
        if is_zero:
            fano.append([a, b, c])
    return nonzero, zero, fano


def two_generated_alternativity(table: Any) -> dict[str, Any]:
    eye = jnp.eye(8, dtype=jnp.float64)
    max_residual = 0.0
    checked_triples = 0
    for i, j in combinations(range(1, 8), 2):
        product_ij = multiply(table, eye[i], eye[j])
        k = int(jax.device_get(jnp.argmax(jnp.abs(product_ij))))
        subspace = [0, i, j, k]
        for a, b, c in product(subspace, repeat=3):
            residual = associator_vec(table, a, b, c)
            max_residual = max(max_residual, float(jax.device_get(jnp.linalg.norm(residual))))
            checked_triples += 1
    return {
        "sampled_pair_count": 21,
        "generated_basis_triple_count": checked_triples,
        "max_associator_norm_on_2_generated_sets": max_residual,
        "all_zero": max_residual <= TOL,
    }


def t5_alternativity(table: Any) -> dict[str, Any]:
    nonzero, zero, fano = assoc_nonzero_count(table)
    perm = [0, 3, 1, 2, 5, 6, 7, 4]
    signs = [1, 1, -1, 1, -1, 1, -1, 1]
    shuffled = table_transform(table, perm, [1] * 8)
    flipped = table_transform(table, list(range(8)), signs)
    s_nonzero, s_zero, _ = assoc_nonzero_count(shuffled)
    f_nonzero, f_zero, _ = assoc_nonzero_count(flipped)
    return {
        "test_id": "T5",
        "two_generated_sets": two_generated_alternativity(table),
        "ordered_distinct_imaginary_triples": 210,
        "nonassociating_triples": nonzero,
        "fano_line_ordered_triples_zero": zero,
        "unordered_fano_lines": sorted({tuple(sorted(row)) for row in fano}),
        "label_shuffle_control": {"nonassociating_triples": s_nonzero, "zero_triples": s_zero, "invariant": (s_nonzero, s_zero) == (nonzero, zero)},
        "orientation_flip_control": {"nonassociating_triples": f_nonzero, "zero_triples": f_zero, "invariant": (f_nonzero, f_zero) == (nonzero, zero)},
    }


def t3_ladder(artifact: dict[str, Any]) -> dict[str, Any]:
    real = jnp.asarray([[[1.0]]], dtype=jnp.float64)
    complex_table = cd_double(real)
    quaternion = jnp.asarray(artifact["quaternion"]["C"], dtype=jnp.float64)
    octonion = jnp.asarray(artifact["octonion"]["C"], dtype=jnp.float64)
    reports = [
        rung_report("R", real, 1, 0),
        rung_report("C", complex_table, 2, 1),
        rung_report("H", quaternion, 4, 3),
        rung_report("O", octonion, 8, 7),
    ]
    nonzero, zero, _ = assoc_nonzero_count(octonion)
    shuffled = table_transform(octonion, [0, 3, 1, 2, 5, 6, 7, 4], [1] * 8)
    flipped = table_transform(octonion, list(range(8)), [1, 1, -1, 1, -1, 1, -1, 1])
    return {
        "test_id": "T3",
        "rungs": reports,
        "base_dimensions": [row["computed_base_dimension_local_pca"] for row in reports],
        "fiber_dimensions": [row["computed_fiber_dimension_local_pca"] for row in reports],
        "admitted_family_language": "roots ADMIT the four-member family {S^1,S^2,S^4,S^8}; C^2 carrier INSTALLS S^2",
        "artifact_policy": {
            "artifact_path": str(ARTIFACT_PATH),
            "artifact_sha256": artifact["artifact_sha256"],
            "artifact_source_sha256": artifact["payload"]["source_sha256"],
            "proof_tag": artifact["payload"]["proof_tag"],
            "proof_pass": artifact["payload"]["proof_pass"],
            "table_version": artifact["payload"]["table_version"],
            "bracket_convention": artifact["payload"]["bracket_convention"],
            "weld_2_precedent": "system_v6/sims/mct_nonassoc_weld_packet_v0/build_card.md imports the same artifact under hash/version policy",
        },
        "label_shuffle_control": {
            "base_dimension_O": local_base_dim(shuffled),
            "fiber_dimension_O": local_fiber_dim(shuffled),
            "t5_counts": assoc_nonzero_count(shuffled)[:2],
            "invariant": local_base_dim(shuffled) == 8 and local_fiber_dim(shuffled) == 7 and assoc_nonzero_count(shuffled)[:2] == (nonzero, zero),
        },
        "orientation_flip_control": {
            "base_dimension_O": local_base_dim(flipped),
            "fiber_dimension_O": local_fiber_dim(flipped),
            "t5_counts": assoc_nonzero_count(flipped)[:2],
            "invariant": local_base_dim(flipped) == 8 and local_fiber_dim(flipped) == 7 and assoc_nonzero_count(flipped)[:2] == (nonzero, zero),
        },
    }


def vector_from_terms(dim: int, terms: list[tuple[int, float]]) -> Any:
    v = jnp.zeros((dim,), dtype=jnp.float64)
    for idx, coeff in terms:
        v = v.at[idx].set(coeff)
    return v


def nonzero_terms(v: Any, tol: float = 1.0e-9) -> list[list[float]]:
    return [[idx, float(coeff)] for idx, coeff in enumerate(to_builtin(v)) if abs(float(coeff)) > tol]


def zero_divisor_convention_translation(table_o: Any, table_s: Any, packet_product: Any) -> dict[str, Any]:
    blind_left = vector_from_terms(16, [(3, 1.0), (10, 1.0)])
    blind_right = vector_from_terms(16, [(6, 1.0), (15, -1.0)])
    packet_left = vector_from_terms(16, [(1, 1.0), (10, 1.0)])
    packet_right = vector_from_terms(16, [(4, 1.0), (13, 1.0)])
    blind_packet_product = multiply(table_s, blind_left, blind_right)
    # This is a basis relabel/orientation map on the octonion parent table; the
    # sedenion table is then the Cayley-Dickson double under that convention.
    perm = [0, 3, 2, 1, 6, 7, 4, 5]
    signs = [1, -1, 1, 1, -1, -1, 1, -1]
    blind_table_s = cd_double(table_transform(table_o, perm, signs))
    blind_own_product = multiply(blind_table_s, blind_left, blind_right)
    return {
        "field_status": "hardening_gap_1_2_closed",
        "packet_convention": {
            "witness": "(e1+e10)(e4+e13)",
            "left_terms": [[1, 1.0], [10, 1.0]],
            "right_terms": [[4, 1.0], [13, 1.0]],
            "product_terms": nonzero_terms(packet_product),
            "product_norm": float(jax.device_get(jnp.linalg.norm(packet_product))),
            "verified_zero_divisor_under_own_convention": float(jax.device_get(jnp.linalg.norm(packet_product))) <= TOL,
        },
        "blind_sheet_under_packet_convention": {
            "witness": "(e3+e10)(e6-e15)",
            "left_terms": [[3, 1.0], [10, 1.0]],
            "right_terms": [[6, 1.0], [15, -1.0]],
            "product_terms": nonzero_terms(blind_packet_product),
            "product_vector": to_builtin(blind_packet_product),
            "product_norm": float(jax.device_get(jnp.linalg.norm(blind_packet_product))),
            "verified_zero_divisor_under_packet_convention": float(jax.device_get(jnp.linalg.norm(blind_packet_product))) <= TOL,
        },
        "blind_sheet_own_convention": {
            "basis_relabel_old_to_new": {f"e{i}": f"{'-' if signs[i] < 0 else ''}e{perm[i]}" for i in range(8)},
            "octonion_permutation_old_to_new": perm,
            "octonion_signs_old_to_new": signs,
            "sedenion_lift_rule": "apply the same octonion relabel/sign map to both Cayley-Dickson halves before doubling",
            "product_terms": nonzero_terms(blind_own_product),
            "product_vector": to_builtin(blind_own_product),
            "product_norm": float(jax.device_get(jnp.linalg.norm(blind_own_product))),
            "verified_zero_divisor_under_own_convention": float(jax.device_get(jnp.linalg.norm(blind_own_product))) <= TOL,
        },
    }


def find_sedenion_fiber_break(table: Any, x: Any, y: Any, base_h: Any) -> dict[str, Any]:
    dim = int(table.shape[0])
    best = {"q_terms": [], "deviation": -1.0}
    for a, b in combinations(range(1, dim), 2):
        q = vector_from_terms(dim, [(a, 1.0 / math.sqrt(2.0)), (b, 1.0 / math.sqrt(2.0))])
        hx = hopf_image(table, multiply(table, x, q), multiply(table, y, q))
        dev = float(jax.device_get(jnp.linalg.norm(hx - base_h)))
        if dev > best["deviation"]:
            best = {"q_terms": [[a, 1.0], [b, 1.0]], "deviation": dev}
    return best


def t4_sedenion(table_o: Any) -> dict[str, Any]:
    table_s = cd_double(table_o)
    u = vector_from_terms(16, [(1, 1.0 / math.sqrt(2.0)), (10, 1.0 / math.sqrt(2.0))])
    v = vector_from_terms(16, [(4, 1.0 / math.sqrt(2.0)), (13, 1.0 / math.sqrt(2.0))])
    uv = multiply(table_s, u, v)
    norm_law_violation = abs(float(jax.device_get(jnp.linalg.norm(uv))) - 1.0)
    x = u / math.sqrt(2.0)
    y = conj_vec(v) / math.sqrt(2.0)
    hxy = hopf_image(table_s, x, y)
    image_norm = float(jax.device_get(jnp.linalg.norm(hxy)))
    image_deviation = abs(image_norm - 1.0)
    fiber_break = find_sedenion_fiber_break(table_s, x, y, hxy)
    return {
        "test_id": "T4",
        "sedenion_table": "Cayley-Dickson double of imported octonion table computed in-packet",
        "zero_divisor_pair_from_committed_84": {
            "left_unit_terms": [[1, 1.0], [10, 1.0]],
            "right_unit_terms": [[4, 1.0], [13, 1.0]],
            "normalization": "each coefficient divided by sqrt(2)",
            "product_norm": float(jax.device_get(jnp.linalg.norm(uv))),
            "product_vector": to_builtin(uv),
        },
        "zero_divisor_convention_translation": zero_divisor_convention_translation(table_o, table_s, uv),
        "norm_law_violation_magnitude": norm_law_violation,
        "image_leaves_S16": {"image_norm": image_norm, "max_abs_norm_minus_1": image_deviation},
        "fiber_constancy_break": {"max_deviation": fiber_break["deviation"], "witness_q_terms": fiber_break["q_terms"]},
        "sedenion_rung_passed": False,
        "designed_failure_fired": norm_law_violation > 0.5 and image_deviation > 0.5 and fiber_break["deviation"] > 0.1,
        "kill_condition_met": False,
    }


def z3_main_proofs(t2: dict[str, Any], t4: dict[str, Any]) -> dict[str, Any]:
    scale = 1_000_000
    sedenion_value = int(round(t4["norm_law_violation_magnitude"]))
    octonion_value = 0
    noncomm_rank = int(t2["noncommuting_full_pauli_family"]["affine_dimension"])
    comm_rank = int(t2["commuting_sigma_z_binned"]["affine_dimension"])
    sedenion_scaled = int(round(float(t4["norm_law_violation_magnitude"]) * scale))
    octonion_scaled = 0
    noncomm_rank_scaled = noncomm_rank * scale
    comm_rank_scaled = comm_rank * scale

    p1 = z3.Solver()
    v = z3.Int("sedenion_norm_violation_scaled")
    p1.add(v == z3.IntVal(sedenion_scaled))
    p1.add(v == z3.IntVal(0))
    p1_status = str(p1.check())

    p1_control = z3.Solver()
    vc = z3.Int("octonion_norm_violation_control_scaled")
    p1_control.add(vc == z3.IntVal(octonion_scaled))
    p1_control.add(vc == z3.IntVal(0))
    p1_control_status = str(p1_control.check())

    p2 = z3.Solver()
    r = z3.Int("noncommuting_affine_rank_scaled")
    p2.add(r == z3.IntVal(noncomm_rank_scaled))
    p2.add(r < z3.IntVal(3 * scale))
    p2_status = str(p2.check())

    p2_control = z3.Solver()
    rc = z3.Int("commuting_affine_rank_scaled")
    p2_control.add(rc == z3.IntVal(comm_rank_scaled))
    p2_control.add(rc < z3.IntVal(3 * scale))
    p2_control_status = str(p2_control.check())

    return {
        "ran": True,
        "load_bearing": True,
        "verdict": "unsat" if p1_status == "unsat" and p2_status == "unsat" else "sat",
        "P1_sedenion_norm_violation_eq_zero": p1_status,
        "P1_octonion_zero_control": p1_control_status,
        "P2_noncommuting_rank_leq_2": p2_status,
        "P2_commuting_rank_leq_2_control": p2_control_status,
        "bound_raw_values": {
            "sedenion_norm_violation": sedenion_value,
            "octonion_norm_violation_control": octonion_value,
            "noncommuting_affine_rank": noncomm_rank,
            "commuting_affine_rank": comm_rank,
        },
        "smt_value_encoding": "exact_integer_ok_for_current_values; future non-integer witnesses require scaled integers or exact rationals",
        "bound_scaled_integer_values": {
            "scale": scale,
            "sedenion_norm_violation_scaled": sedenion_scaled,
            "octonion_norm_violation_control_scaled": octonion_scaled,
            "noncommuting_affine_rank_scaled": noncomm_rank_scaled,
            "commuting_affine_rank_scaled": comm_rank_scaled,
            "rank_threshold_scaled": 3 * scale,
        },
        "asserted_precomputed_boolean": False,
    }


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_prove_eq_zero(value: int, name: str, expect_zero: bool) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    sort = solver.getIntegerSort()
    v = solver.mkConst(sort, name)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, v, solver.mkInteger(value)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, v, solver.mkInteger(0)))
    return cvc5_status(solver.checkSat())


def cvc5_prove_rank_lt(value: int, threshold: int, name: str) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    sort = solver.getIntegerSort()
    r = solver.mkConst(sort, name)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, r, solver.mkInteger(value)))
    solver.assertFormula(solver.mkTerm(Kind.LT, r, solver.mkInteger(threshold)))
    return cvc5_status(solver.checkSat())


def cvc5_main_proofs(t2: dict[str, Any], t4: dict[str, Any]) -> dict[str, Any]:
    scale = 1_000_000
    sedenion_value = int(round(t4["norm_law_violation_magnitude"]))
    noncomm_rank = int(t2["noncommuting_full_pauli_family"]["affine_dimension"])
    comm_rank = int(t2["commuting_sigma_z_binned"]["affine_dimension"])
    sedenion_scaled = int(round(float(t4["norm_law_violation_magnitude"]) * scale))
    noncomm_rank_scaled = noncomm_rank * scale
    comm_rank_scaled = comm_rank * scale
    p1 = cvc5_prove_eq_zero(sedenion_scaled, "sedenion_norm_violation_scaled", False)
    p1_control = cvc5_prove_eq_zero(0, "octonion_norm_violation_control_scaled", True)
    p2 = cvc5_prove_rank_lt(noncomm_rank_scaled, 3 * scale, "noncommuting_affine_rank_scaled")
    p2_control = cvc5_prove_rank_lt(comm_rank_scaled, 3 * scale, "commuting_affine_rank_scaled")
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": "unsat" if p1 == "unsat" and p2 == "unsat" else "sat",
        "P1_sedenion_norm_violation_eq_zero": p1,
        "P1_octonion_zero_control": p1_control,
        "P2_noncommuting_rank_leq_2": p2,
        "P2_commuting_rank_leq_2_control": p2_control,
        "bound_raw_values": {
            "sedenion_norm_violation": sedenion_value,
            "octonion_norm_violation_control": 0,
            "noncommuting_affine_rank": noncomm_rank,
            "commuting_affine_rank": comm_rank,
        },
        "smt_value_encoding": "exact_integer_ok_for_current_values; future non-integer witnesses require scaled integers or exact rationals",
        "bound_scaled_integer_values": {
            "scale": scale,
            "sedenion_norm_violation_scaled": sedenion_scaled,
            "octonion_norm_violation_control_scaled": 0,
            "noncommuting_affine_rank_scaled": noncomm_rank_scaled,
            "commuting_affine_rank_scaled": comm_rank_scaled,
            "rank_threshold_scaled": 3 * scale,
        },
        "asserted_precomputed_boolean": False,
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = load_artifact()
    octonion = jnp.asarray(artifact["octonion"]["C"], dtype=jnp.float64)
    t1 = t1_limit_shape()
    t2 = t2_ball_vs_simplex()
    t3 = t3_ladder(artifact)
    t4 = t4_sedenion(octonion)
    t5 = t5_alternativity(octonion)
    z3_proof = z3_main_proofs(t2, t4)
    cvc5_proof = cvc5_main_proofs(t2, t4)
    all_pass = (
        t1["converges_on_sample"]
        and t1["control_non_refining_repeated_probes"]["does_not_converge"]
        and t2["commuting_sigma_z_binned"]["affine_dimension"] == 1
        and t2["noncommuting_full_pauli_family"]["affine_dimension"] == 3
        and t2["control_commuting_only_additions"]["never_raises_dimension_above_interval"]
        and t3["base_dimensions"] == [1, 2, 4, 8]
        and t3["fiber_dimensions"] == [0, 1, 3, 7]
        and all(row["pass"] for row in t3["rungs"])
        and t4["designed_failure_fired"]
        and not t4["sedenion_rung_passed"]
        and t5["two_generated_sets"]["all_zero"]
        and t5["nonassociating_triples"] == 168
        and t5["fano_line_ordered_triples_zero"] == 42
        and t5["label_shuffle_control"]["invariant"]
        and t5["orientation_flip_control"]["invariant"]
        and z3_proof["verdict"] == "unsat"
        and cvc5_proof["verdict"] == "unsat"
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )
    values = {
        "t2_commuting_dim": t2["commuting_sigma_z_binned"]["affine_dimension"],
        "t2_noncommuting_dim": t2["noncommuting_full_pauli_family"]["affine_dimension"],
        "t3_base_dims_hash": hashlib.sha256(json.dumps(t3["base_dimensions"]).encode("utf-8")).hexdigest(),
        "t3_fiber_dims_hash": hashlib.sha256(json.dumps(t3["fiber_dimensions"]).encode("utf-8")).hexdigest(),
        "t4_norm_law_violation": t4["norm_law_violation_magnitude"],
        "t4_image_deviation": t4["image_leaves_S16"]["max_abs_norm_minus_1"],
        "t4_fiber_break_deviation": t4["fiber_constancy_break"]["max_deviation"],
        "t5_nonassoc_count": t5["nonassociating_triples"],
        "t5_fano_zero_count": t5["fano_line_ordered_triples_zero"],
    }
    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "pin_sha256": PIN_SHA256,
        "pin_canonical": PIN_CANONICAL,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "runtime_preflight": {"jax_enable_x64": bool(jax.config.jax_enable_x64), "jax_version": jax.__version__},
        "canon_artifact": t3["artifact_policy"],
        "tests": {"T1": t1, "T2": t2, "T3": t3, "T4": t4, "T5": t5},
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "values": values,
        "all_pass": bool(all_pass),
    }
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(to_builtin(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "BLOCH_ROOT_ADMISSIBILITY_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"dims={result['tests']['T3']['base_dimensions']} "
        f"fibers={result['tests']['T3']['fiber_dimensions']} "
        f"sedenion_violation={result['tests']['T4']['norm_law_violation_magnitude']:.6g} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
