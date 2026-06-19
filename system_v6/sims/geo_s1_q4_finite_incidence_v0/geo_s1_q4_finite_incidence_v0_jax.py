#!/usr/bin/env python3
"""JAX/galois/z3/cvc5 leg for exact PG(3,4) finite incidence."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from collections import Counter, deque
from itertools import combinations, product
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import galois
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "geo_s1_q4_finite_incidence_v0"
ENGINE = "jax"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
MODE = "julia_canon_plus_jax_diagnostic"
Q = 4
GF = galois.GF(Q)
NONZERO_SCALARS = [1, 2, 3]
SEEDS = {"finite_enumeration": "deterministic_lexicographic", "scramble_control": "deterministic_line_replacement_v1"}

PIN_BLOCK = {
    "q": 4,
    "field": "GF(4)",
    "field_model": "galois.GF(4), primitive polynomial x^2 + x + 1; integer labels 0,1,alpha,alpha+1",
    "object": "PG(3,4)",
    "projective_quotient": "nonzero vectors of GF(4)^4 modulo GF(4)^*={1,alpha,alpha+1}; exact classes computed with galois.GF(4)",
    "expected_counts": {
        "raw_nonzero_vectors": 255,
        "points": 85,
        "lines": 357,
        "planes": 85,
        "points_per_line": 5,
        "lines_through_point": 21,
        "points_per_plane": 21,
        "lines_per_plane": 21,
        "line_graph_degree": 100,
        "line_graph_edges": 17850,
    },
    "comparison_anchor_q2": "system_v6/sims/twistor_incidence_finite_packet_v0",
    "comparison_anchor_q3": "system_v6/sims/geo_s1_q3_finite_incidence_v0",
    "probe_families": ["P_proj_q4", "P_inc_q4", "P_plane_q4", "P_null_q4", "P_recon_q4", "P_frobenius_q4"],
    "engine_mode": MODE,
}
PIN_BLOCK_CANONICAL = json.dumps(PIN_BLOCK, sort_keys=True, separators=(",", ":"))
PIN_BLOCK_SHA256 = hashlib.sha256(PIN_BLOCK_CANONICAL.encode("utf-8")).hexdigest()

TOOL_MANIFEST = {
    "galois": {"tried": True, "used": True, "reason": "load-bearing exact GF(4) arithmetic, row-space rank, scalar quotient, span construction, and Frobenius boundary"},
    "jax": {"tried": True, "used": True, "reason": "supportive x64 incidence tensor shape and scalar comparison storage"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive exact integer incidence matrix shape check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing SMT polarity check over computed pair-line counts with scrambled SAT control"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent SMT polarity check over the same computed pair-line counts and control"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive graph, hashing, timestamp, and JSON machinery"},
}
TOOL_INTEGRATION_DEPTH = {
    "galois": "load_bearing",
    "jax": "supportive",
    "jax.numpy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gf_tuple(values: Any) -> tuple[int, ...]:
    return tuple(int(x) for x in GF(values).tolist())


def gf_rank(rows: list[tuple[int, ...]]) -> int:
    arr = GF(rows)
    return int(arr.row_space().shape[0])


def add_scaled(acc: tuple[int, ...], coeff: int, vec: tuple[int, ...]) -> tuple[int, ...]:
    return gf_tuple(GF(acc) + GF(coeff) * GF(vec))


def gf_mul_scalar(scalar: int, vec: tuple[int, ...]) -> tuple[int, ...]:
    return gf_tuple(GF(scalar) * GF(vec))


def gf_square_vec(vec: tuple[int, ...]) -> tuple[int, ...]:
    return gf_tuple(GF(vec) ** 2)


def projective_class(v: tuple[int, ...]) -> tuple[int, ...]:
    if all(x == 0 for x in v):
        raise ValueError("zero vector has no projective class")
    return min(gf_mul_scalar(scalar, v) for scalar in NONZERO_SCALARS)


def all_nonzero_vectors() -> list[tuple[int, int, int, int]]:
    return [tuple(v) for v in product(range(Q), repeat=4) if any(v)]


def span_projective_points(basis: list[tuple[int, ...]]) -> tuple[tuple[int, ...], ...]:
    points = set()
    for coeffs in product(range(Q), repeat=len(basis)):
        if not any(coeffs):
            continue
        vec = (0, 0, 0, 0)
        for coeff, base in zip(coeffs, basis):
            vec = add_scaled(vec, coeff, base)
        points.add(projective_class(vec))
    return tuple(sorted(points))


def rref_subspace_bases(k: int) -> list[list[tuple[int, ...]]]:
    bases: list[list[tuple[int, ...]]] = []
    n = 4
    for pivots in combinations(range(n), k):
        nonpivots = [col for col in range(n) if col not in pivots]
        free_positions = [(row, col) for row, pivot in enumerate(pivots) for col in nonpivots if pivot < col]
        for entries in product(range(Q), repeat=len(free_positions)):
            mat = [[0 for _ in range(n)] for _ in range(k)]
            for row, pivot in enumerate(pivots):
                mat[row][pivot] = 1
            for (row, col), value in zip(free_positions, entries):
                mat[row][col] = value
            bases.append([tuple(row) for row in mat])
    return bases


def build_pg34() -> dict[str, Any]:
    raw = all_nonzero_vectors()
    point_classes = sorted({projective_class(v) for v in raw})
    point_id = {p: idx for idx, p in enumerate(point_classes)}
    quotient_rows = [
        {
            "raw_vector": list(v),
            "projective_class": list(projective_class(v)),
            "class_id": point_id[projective_class(v)],
            "scalar_orbit": [list(gf_mul_scalar(scalar, v)) for scalar in NONZERO_SCALARS],
        }
        for v in raw
    ]

    line_list = sorted({tuple(point_id[p] for p in span_projective_points(basis)) for basis in rref_subspace_bases(2)})
    plane_list = sorted({tuple(point_id[p] for p in span_projective_points(basis)) for basis in rref_subspace_bases(3)})

    incidence = [[point in line for line in line_list] for point in range(len(point_classes))]
    plane_incidence = [[point in plane for plane in plane_list] for point in range(len(point_classes))]
    return {
        "points": [list(p) for p in point_classes],
        "quotient_rows": quotient_rows,
        "lines": [list(line) for line in line_list],
        "planes": [list(plane) for plane in plane_list],
        "incidence": incidence,
        "plane_incidence": plane_incidence,
        "incidence_matrix_shape": [len(point_classes), len(line_list)],
        "plane_incidence_matrix_shape": [len(point_classes), len(plane_list)],
    }


def graph_from_lines(lines: list[list[int]]) -> dict[int, set[int]]:
    graph = {idx: set() for idx in range(len(lines))}
    sets = [set(line) for line in lines]
    for i, j in combinations(range(len(lines)), 2):
        if sets[i] & sets[j]:
            graph[i].add(j)
            graph[j].add(i)
    return graph


def components(graph: dict[int, set[int]]) -> list[list[int]]:
    seen: set[int] = set()
    comps: list[list[int]] = []
    for node in graph:
        if node in seen:
            continue
        queue = deque([node])
        seen.add(node)
        comp = []
        while queue:
            cur = queue.popleft()
            comp.append(cur)
            for nxt in graph[cur]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        comps.append(sorted(comp))
    return comps


def graph_invariants(lines: list[list[int]]) -> dict[str, Any]:
    graph = graph_from_lines(lines)
    degrees = sorted(len(neigh) for neigh in graph.values())
    comps = components(graph)
    return {
        "vertex_count": len(lines),
        "edge_count": sum(degrees) // 2,
        "degree_sequence": degrees,
        "degree_histogram": dict(sorted(Counter(degrees).items())),
        "components": len(comps),
        "component_sizes": sorted(len(comp) for comp in comps),
        "degree_formula": "(q+1)*(q^2+q) = 5*20 = 100",
        "edge_formula": "357*100/2 = 17850",
    }


def incidence_from_lines(lines: list[list[int]], point_count: int) -> list[list[bool]]:
    return [[point in line for line in lines] for point in range(point_count)]


def line_pencils(incidence: list[list[bool]]) -> list[list[int]]:
    return [[line_idx for line_idx, flag in enumerate(row) if flag] for row in incidence]


def line_sets_in_planes(lines: list[list[int]], planes: list[list[int]]) -> list[list[int]]:
    line_sets = [set(line) for line in lines]
    return [[idx for idx, line in enumerate(line_sets) if line <= set(plane)] for plane in planes]


def clique_family_check(lines: list[list[int]], planes: list[list[int]], incidence: list[list[bool]]) -> dict[str, Any]:
    graph = graph_from_lines(lines)
    stars = line_pencils(incidence)
    plane_line_sets = line_sets_in_planes(lines, planes)

    def is_clique(items: list[int]) -> bool:
        return all(b in graph[a] for a, b in combinations(items, 2))

    star_sizes = sorted(len(row) for row in stars)
    plane_line_sizes = sorted(len(row) for row in plane_line_sets)
    unique_cliques = {tuple(row) for row in stars} | {tuple(row) for row in plane_line_sets}
    return {
        "clique_number_structural": Q**2 + Q + 1,
        "max_clique_count_structural": len(unique_cliques),
        "point_star_count": len(stars),
        "plane_line_set_count": len(plane_line_sets),
        "point_star_sizes": star_sizes,
        "plane_line_set_sizes": plane_line_sizes,
        "all_point_stars_are_cliques": all(is_clique(row) for row in stars),
        "all_plane_line_sets_are_cliques": all(is_clique(row) for row in plane_line_sets),
        "unique_star_or_plane_clique_count": len(unique_cliques),
        "computed_split_ok": len(stars) == 85
        and len(plane_line_sets) == 85
        and len(unique_cliques) == 170
        and star_sizes == [21] * 85
        and plane_line_sizes == [21] * 85
        and all(is_clique(row) for row in stars)
        and all(is_clique(row) for row in plane_line_sets),
        "method": "construct all point-stars and all plane line-sets; verify each is a 21-line clique in the line-intersection graph",
    }


def pair_line_counts(lines: list[list[int]], point_count: int) -> dict[tuple[int, int], int]:
    counts = {pair: 0 for pair in combinations(range(point_count), 2)}
    for line in lines:
        for pair in combinations(sorted(line), 2):
            counts[pair] += 1
    return counts


def reconstruction(lines: list[list[int]], point_count: int) -> dict[str, Any]:
    incidence = incidence_from_lines(lines, point_count)
    expected = {tuple(row) for row in line_pencils(incidence)}
    recovered: set[tuple[int, ...]] = set()
    bad_pair_overlaps = 0
    for i, j in combinations(range(len(lines)), 2):
        shared = sorted(set(lines[i]) & set(lines[j]))
        if len(shared) > 1:
            bad_pair_overlaps += 1
        if len(shared) == 1:
            p = shared[0]
            recovered.add(tuple(idx for idx, flag in enumerate(incidence[p]) if flag))
    missing = sorted(expected - recovered)
    extra = sorted(recovered - expected)
    return {
        "expected_point_count": point_count,
        "recovered_point_count": len(recovered),
        "mismatch_count": len(missing) + len(extra),
        "bad_pair_overlaps": bad_pair_overlaps,
        "pencil_sizes": sorted(len(row) for row in expected),
        "recovered_pencil_sizes": sorted(len(row) for row in recovered),
        "pass": len(recovered) == point_count and not missing and not extra and bad_pair_overlaps == 0,
    }


def scrambled_incidence_lines(lines: list[list[int]], point_count: int) -> list[list[int]]:
    out = [list(line) for line in lines]
    candidates = [p for p in range(point_count) if p not in out[0]][:3]
    out[1] = sorted([out[0][0], out[0][1], *candidates])
    return out


def z3_pair_uniqueness(counts: dict[tuple[int, int], int]) -> dict[str, Any]:
    solver = z3.Solver()
    solver.add(z3.Or([z3.IntVal(v) != z3.IntVal(1) for v in counts.values()]))
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "verdict": str(solver.check()),
        "claim": "exists a point pair whose computed incident-line count is not exactly one",
        "expected_for_valid_incidence": "unsat",
        "computed_rows_bound": True,
    }


def cvc5_pair_uniqueness(counts: dict[tuple[int, int], int]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    terms = [
        solver.mkTerm(Kind.DISTINCT, solver.mkInteger(int(value)), solver.mkInteger(1))
        for value in counts.values()
    ]
    solver.assertFormula(solver.mkTerm(Kind.OR, *terms))
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "verdict": str(solver.checkSat()).lower(),
        "claim": "exists a point pair whose computed incident-line count is not exactly one",
        "expected_for_valid_incidence": "unsat",
        "computed_rows_bound": True,
    }


def frobenius_boundary(points: list[list[int]], lines: list[list[int]], incidence: list[list[bool]]) -> dict[str, Any]:
    point_tuples = [tuple(p) for p in points]
    point_id = {p: idx for idx, p in enumerate(point_tuples)}
    frob_point_image = {idx: point_id[projective_class(gf_square_vec(p))] for idx, p in enumerate(point_tuples)}
    image_values = sorted(frob_point_image.values())
    line_sets = {tuple(line) for line in lines}
    line_images = []
    for line in lines:
        mapped = tuple(sorted(frob_point_image[p] for p in line))
        line_images.append(mapped)
    incidence_preserved = True
    for p_idx, row in enumerate(incidence):
        mapped_p = frob_point_image[p_idx]
        for line_idx, flag in enumerate(row):
            mapped_line = line_images[line_idx]
            incidence_preserved = incidence_preserved and ((mapped_p in mapped_line) == flag)
    moved_points = sum(1 for idx, image in frob_point_image.items() if idx != image)
    return {
        "map": "coordinatewise Frobenius x -> x^2 over GF(4)",
        "field_label_squares": {str(x): int(GF(x) ** 2) for x in range(Q)},
        "point_permutation": image_values == list(range(len(points))),
        "line_permutation": sorted(line_images) == sorted(line_sets),
        "incidence_preserved": incidence_preserved,
        "nontrivial_on_projective_points": moved_points > 0,
        "moved_projective_point_count": moved_points,
        "involution_on_points": all(frob_point_image[frob_point_image[idx]] == idx for idx in frob_point_image),
        "boundary_case": "char-2 Frobenius is nontrivial for GF(4), unlike prime-field q=2/q=3 rows",
        "pass": image_values == list(range(len(points)))
        and sorted(line_images) == sorted(line_sets)
        and incidence_preserved
        and moved_points > 0
        and all(frob_point_image[frob_point_image[idx]] == idx for idx in frob_point_image),
    }


def load_anchor_q2() -> dict[str, Any]:
    path = ROOT / "system_v6" / "sims" / "twistor_incidence_finite_packet_v0" / "results" / "twistor_incidence_finite_packet_v0_envelope_results.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    values = payload["divergence"]["engine_values"]["jax"]
    return {
        "source_path": str(path),
        "source_sha256": sha256_file(path),
        "q": 2,
        "raw_nonzero_vector_count": values["raw_nonzero_vector_count"],
        "projective_class_count": values["projective_class_count"],
        "point_count": values["point_count"],
        "line_count": values["line_count"],
        "null_graph_edge_count": values["null_graph_edge_count"],
        "null_graph_degree": values["null_graph_degree_min"],
        "recovered_point_count": values["recovered_point_count"],
        "reconstruction_mismatch_count": values["reconstruction_mismatch_count"],
        "surviving_separation": payload["summary"]["surviving_separation"],
    }


def load_anchor_q3() -> dict[str, Any]:
    path = ROOT / "system_v6" / "sims" / "geo_s1_q3_finite_incidence_v0" / "results" / "geo_s1_q3_finite_incidence_v0_envelope_results.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    values = payload["divergence"]["engine_values"]["jax"]
    return {
        "source_path": str(path),
        "source_sha256": sha256_file(path),
        "q": 3,
        "raw_nonzero_vector_count": values["raw_nonzero_vector_count"],
        "projective_class_count": values["projective_class_count"],
        "point_count": values["point_count"],
        "line_count": values["line_count"],
        "null_graph_edge_count": values["null_graph_edge_count"],
        "null_graph_degree": values["null_graph_degree_min"],
        "recovered_point_count": values["recovered_point_count"],
        "reconstruction_mismatch_count": values["reconstruction_mismatch_count"],
        "surviving_separation": payload["summary"]["surviving_separation"],
    }


def build_result() -> dict[str, Any]:
    pg = build_pg34()
    points = pg["points"]
    lines = pg["lines"]
    planes = pg["planes"]
    incidence = pg["incidence"]
    graph_inv = graph_invariants(lines)
    clique_check = clique_family_check(lines, planes, incidence)
    recon = reconstruction(lines, len(points))
    pair_counts = pair_line_counts(lines, len(points))
    scrambled_lines = scrambled_incidence_lines(lines, len(points))
    scrambled_counts = pair_line_counts(scrambled_lines, len(points))
    z3_valid = z3_pair_uniqueness(pair_counts)
    z3_bad = z3_pair_uniqueness(scrambled_counts)
    cvc5_valid = cvc5_pair_uniqueness(pair_counts)
    cvc5_bad = cvc5_pair_uniqueness(scrambled_counts)
    frob = frobenius_boundary(points, lines, incidence)
    q2_anchor = load_anchor_q2()
    q3_anchor = load_anchor_q3()
    pencil_sizes = sorted(len(row) for row in line_pencils(incidence))
    plane_line_sizes = sorted(len(row) for row in line_sets_in_planes(lines, planes))
    values = {
        "raw_nonzero_vector_count": len(pg["quotient_rows"]),
        "projective_class_count": len(points),
        "point_count": len(points),
        "line_count": len(lines),
        "plane_count": len(planes),
        "points_per_line_min": min(len(line) for line in lines),
        "points_per_line_max": max(len(line) for line in lines),
        "lines_through_point_min": min(pencil_sizes),
        "lines_through_point_max": max(pencil_sizes),
        "points_per_plane_min": min(len(plane) for plane in planes),
        "points_per_plane_max": max(len(plane) for plane in planes),
        "lines_per_plane_min": min(plane_line_sizes),
        "lines_per_plane_max": max(plane_line_sizes),
        "pair_count": len(pair_counts),
        "pair_line_count_min": min(pair_counts.values()),
        "pair_line_count_max": max(pair_counts.values()),
        "null_graph_components": graph_inv["components"],
        "null_graph_edge_count": graph_inv["edge_count"],
        "null_graph_degree_min": min(graph_inv["degree_sequence"]),
        "null_graph_degree_max": max(graph_inv["degree_sequence"]),
        "null_graph_clique_number": clique_check["clique_number_structural"],
        "null_graph_max_clique_count": clique_check["max_clique_count_structural"],
        "null_graph_max_clique_point_pencil_count": clique_check["point_star_count"],
        "null_graph_max_clique_plane_line_set_count": clique_check["plane_line_set_count"],
        "recovered_point_count": recon["recovered_point_count"],
        "reconstruction_mismatch_count": recon["mismatch_count"],
        "frobenius_moved_projective_point_count": frob["moved_projective_point_count"],
        "z3_pair_uniqueness_unsat": 1.0 if z3_valid["verdict"] == "unsat" else 0.0,
        "cvc5_pair_uniqueness_unsat": 1.0 if cvc5_valid["verdict"] == "unsat" else 0.0,
    }
    raw_to_projective_ratio = values["raw_nonzero_vector_count"] / values["projective_class_count"]
    q2_ratio = q2_anchor["raw_nonzero_vector_count"] / q2_anchor["projective_class_count"]
    q3_ratio = q3_anchor["raw_nonzero_vector_count"] / q3_anchor["projective_class_count"]
    controls = {
        "drop-projective-quotient": {
            "fired": True,
            "raw_nonzero_vector_count": values["raw_nonzero_vector_count"],
            "projective_class_count": values["projective_class_count"],
            "raw_to_projective_ratio": raw_to_projective_ratio,
            "same_readouts_as_projective": values["raw_nonzero_vector_count"] == values["projective_class_count"],
            "q4_discriminator_fired": values["raw_nonzero_vector_count"] == 3 * values["projective_class_count"],
            "strictly_stronger_than_q3": raw_to_projective_ratio > q3_ratio > q2_ratio,
        },
        "scramble-incidence": {
            "fired": True,
            "pair_line_count_min": min(scrambled_counts.values()),
            "pair_line_count_max": max(scrambled_counts.values()),
            "z3_control_verdict": z3_bad["verdict"],
            "cvc5_control_verdict": cvc5_bad["verdict"],
            "control_fired": z3_bad["verdict"] == "sat" and cvc5_bad["verdict"] == "sat",
        },
        "frobenius-boundary": frob,
    }
    separation_table = [
        {
            "readout": "projective_scalar_quotient",
            "q2_value": {"raw_nonzero_vectors": q2_anchor["raw_nonzero_vector_count"], "projective_classes": q2_anchor["projective_class_count"], "raw_to_projective_ratio": q2_ratio},
            "q3_value": {"raw_nonzero_vectors": q3_anchor["raw_nonzero_vector_count"], "projective_classes": q3_anchor["projective_class_count"], "raw_to_projective_ratio": q3_ratio},
            "q4_value": {"raw_nonzero_vectors": values["raw_nonzero_vector_count"], "projective_classes": values["projective_class_count"], "raw_to_projective_ratio": raw_to_projective_ratio},
            "status_vs_q3": "strengthens" if raw_to_projective_ratio > q3_ratio else "weakens_or_flat",
            "separation": controls["drop-projective-quotient"]["q4_discriminator_fired"],
            "note": "q=4 is the first non-prime-field scalar quotient row; each projective point has three raw representatives.",
        },
        {
            "readout": "reconstruction_behavior",
            "q2_value": {"recovered": q2_anchor["recovered_point_count"], "mismatch_count": q2_anchor["reconstruction_mismatch_count"]},
            "q3_value": {"recovered": q3_anchor["recovered_point_count"], "mismatch_count": q3_anchor["reconstruction_mismatch_count"]},
            "q4_value": {"recovered": recon["recovered_point_count"], "mismatch_count": recon["mismatch_count"]},
            "status_vs_q3": "strengthens" if recon["pass"] and recon["recovered_point_count"] > q3_anchor["recovered_point_count"] else "weakens_or_fails",
            "separation": recon["pass"],
            "note": "point-star reconstruction persists with zero mismatch and grows from q=2 count 15 to q=3 count 40 to q=4 count 85.",
        },
        {
            "readout": "line_intersection_graph_scale",
            "q2_value": {"points": q2_anchor["point_count"], "lines": q2_anchor["line_count"], "degree": q2_anchor["null_graph_degree"], "edges": q2_anchor["null_graph_edge_count"]},
            "q3_value": {"points": q3_anchor["point_count"], "lines": q3_anchor["line_count"], "degree": q3_anchor["null_graph_degree"], "edges": q3_anchor["null_graph_edge_count"]},
            "q4_value": {"points": values["point_count"], "lines": values["line_count"], "degree": values["null_graph_degree_min"], "edges": values["null_graph_edge_count"]},
            "status_vs_q3": "strengthens" if values["line_count"] > q3_anchor["line_count"] and values["null_graph_degree_min"] > q3_anchor["null_graph_degree"] else "weakens_or_flat",
            "separation": values["line_count"] == 357 and values["null_graph_degree_min"] == 100,
            "note": "the incidence/intersection graph remains regular and connected over GF(4); this is a scale/invariant row, not a physics/null-light claim.",
        },
        {
            "readout": "char2_frobenius_boundary",
            "q2_value": "prime field; Frobenius is identity on field elements",
            "q3_value": "prime field; Frobenius x^3 is identity on field elements",
            "q4_value": {"moved_projective_points": frob["moved_projective_point_count"], "incidence_preserved": frob["incidence_preserved"], "line_permutation": frob["line_permutation"]},
            "status_vs_q3": "new_boundary_not_like_for_like_strength",
            "separation": frob["pass"],
            "note": "GF(4) has nontrivial char-2 Frobenius x->x^2; it moves projective points while preserving incidence.",
        },
    ]
    gates = {
        "G1_pg34_counts": {
            "pass": values["point_count"] == 85
            and values["line_count"] == 357
            and values["plane_count"] == 85
            and values["points_per_line_min"] == values["points_per_line_max"] == 5
            and values["lines_through_point_min"] == values["lines_through_point_max"] == 21
            and values["lines_per_plane_min"] == values["lines_per_plane_max"] == 21,
            "values": values,
        },
        "G2_pair_line_uniqueness": {
            "pass": values["pair_line_count_min"] == values["pair_line_count_max"] == 1,
            "z3": z3_valid,
            "cvc5": cvc5_valid,
            "scrambled_controls": {"z3": z3_bad, "cvc5": cvc5_bad},
        },
        "G3_graph_invariants": {
            "pass": graph_inv["vertex_count"] == 357 and graph_inv["edge_count"] == 17850 and graph_inv["components"] == 1 and min(graph_inv["degree_sequence"]) == max(graph_inv["degree_sequence"]) == 100,
            "graph_invariants": graph_inv,
            "clique_family_check": clique_check,
        },
        "G4_projective_quotient_boundary": {
            "pass": controls["drop-projective-quotient"]["q4_discriminator_fired"] and controls["drop-projective-quotient"]["strictly_stronger_than_q3"],
            "control": controls["drop-projective-quotient"],
        },
        "G5_reconstruction_separation": {
            "pass": recon["pass"] and any(row["readout"] == "reconstruction_behavior" and row["status_vs_q3"] == "strengthens" for row in separation_table),
            "reconstruction": recon,
            "separation_table": separation_table,
        },
        "G6_frobenius_boundary": {
            "pass": frob["pass"],
            "frobenius": frob,
        },
    }
    all_pass = all(row["pass"] for row in gates.values()) and controls["scramble-incidence"]["control_fired"]
    return {
        "schema_version": "geo_s1_q4_finite_incidence_v0_leg_v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "mode": MODE,
        "pytorch_omitted_reason": "declared diagnostic mode; no graph/network/autograd claim path",
        "seeds": SEEDS,
        "all_pass": all_pass,
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "packages_used": ["galois", "jax", "jax.numpy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["galois", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {"tool": "galois", "qualified_api/function": "galois.GF(4) arithmetic, scalar multiplication, and Frobenius", "input_object": "GF(4)^4 RREF subspace bases and scalar orbits", "output_object": "quotient-canonical PG(3,4) points, lines, planes, and Frobenius images", "positive_case": "85/357/85 counts", "negative/erased_control": "drop-projective-quotient raw count 255", "boundary_case": "Frobenius x->x^2 over GF(4)", "demotion_condition": "if spans are not quotient-canonicalized through GF(4)^*", "gates": ["G1_pg34_counts", "G4_projective_quotient_boundary", "G6_frobenius_boundary"]},
            {"tool": "z3", "qualified_api/function": "z3.Solver.check", "input_object": "computed point-pair incident-line counts", "output_object": z3_valid["verdict"], "positive_case": "valid PG(3,4) pair-line uniqueness is unsat for count != 1", "negative/erased_control": z3_bad["verdict"], "boundary_case": "3570 point pairs over GF(4)", "demotion_condition": "if solver uses formula constants not computed counts", "gates": ["G2_pair_line_uniqueness"]},
            {"tool": "cvc5", "qualified_api/function": "cvc5.Solver.checkSat", "input_object": "computed point-pair incident-line counts", "output_object": cvc5_valid["verdict"], "positive_case": "valid PG(3,4) pair-line uniqueness is unsat for count != 1", "negative/erased_control": cvc5_bad["verdict"], "boundary_case": "3570 point pairs over GF(4)", "demotion_condition": "if solver uses formula constants not computed counts", "gates": ["G2_pair_line_uniqueness"]},
        ],
        "pin_block_canonical_json": PIN_BLOCK_CANONICAL,
        "pin_block_sha256": PIN_BLOCK_SHA256,
        "source_refs": {
            "twistor_q2_packet": "system_v6/sims/twistor_incidence_finite_packet_v0/",
            "geo_q3_packet": "system_v6/sims/geo_s1_q3_finite_incidence_v0/",
            "engine_mode_rule": "system_v6/receipts/geometry_sim_program_canonical_20260610.md",
        },
        "points": points,
        "lines": lines,
        "planes": planes,
        "incidence_matrix_shape_jax": list(jnp.asarray(incidence, dtype=jnp.int32).shape),
        "plane_incidence_matrix_shape_jax": list(jnp.asarray(pg["plane_incidence"], dtype=jnp.int32).shape),
        "graph_invariants": graph_inv,
        "clique_family_check": clique_check,
        "reconstruction": recon,
        "frobenius_boundary": frob,
        "q2_anchor": q2_anchor,
        "q3_anchor": q3_anchor,
        "values": values,
        "controls": controls,
        "gates": gates,
        "gate_pass": {name: row["pass"] for name, row in gates.items()},
        "separation_table": separation_table,
        "summary": {
            "finite_object": "PG(3,4) projective points/lines/planes via exact GF(4) quotient",
            "twistor_candidate_result": "incidence reconstruction persists; scalar-quotient boundary strengthens from q=3 ratio 2 to q=4 ratio 3",
            "char2_boundary": "nontrivial Frobenius x->x^2 moves projective points but preserves incidence",
            "ceiling": CLASSIFICATION,
            "fence": "finite incidence discriminator only; no physics, spacetime, GR, bridge, axis, manifold, or Penrose-validation claim",
        },
        "kill_condition_met": not any(row["separation"] for row in separation_table),
        "crossover_proofs": {"z3": z3_valid, "cvc5": cvc5_valid},
        "claim_ceiling": {
            "alt_math_discriminator_only": True,
            "no_spacetime_gr_physics_claim": True,
            "no_penrose_validates_language": True,
            "not_canon": True,
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"GEO_S1_Q4_FINITE_INCIDENCE_V0_JAX_DONE all_pass={result['all_pass']} "
        f"points={result['values']['point_count']} lines={result['values']['line_count']} "
        f"planes={result['values']['plane_count']} z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} frob={result['frobenius_boundary']['pass']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
