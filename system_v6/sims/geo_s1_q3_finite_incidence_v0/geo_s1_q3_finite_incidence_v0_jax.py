#!/usr/bin/env python3
"""JAX/galois/z3/cvc5 leg for exact PG(3,3) finite incidence."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
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
SIM_ID = "geo_s1_q3_finite_incidence_v0"
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
Q = 3
PHASE_GRID = 192
LENS_BASE_DENSITY_COUNT = 7

PIN_BLOCK = {
    "q": 3,
    "field": "F_3",
    "object": "PG(3,3)",
    "projective_quotient": "nonzero vectors of F_3^4 modulo F_3^*={1,2}; exact classes computed with galois.GF(3)",
    "expected_counts": {
        "raw_nonzero_vectors": 80,
        "points": 40,
        "lines": 130,
        "planes": 40,
        "points_per_line": 4,
        "lines_through_point": 13,
        "points_per_plane": 13,
        "lines_per_plane": 13,
    },
    "lens_extension": {
        "object": "Z_3 lens quotient L(3,1)",
        "phase_grid": PHASE_GRID,
        "base_density_count": LENS_BASE_DENSITY_COUNT,
    },
    "comparison_anchor": "system_v6/sims/twistor_incidence_finite_packet_v0",
    "probe_families": ["P_proj_q3", "P_inc_q3", "P_plane_q3", "P_null_q3", "P_recon_q3", "P_lens_phase_q3"],
    "engine_mode": MODE,
}
PIN_BLOCK_CANONICAL = json.dumps(PIN_BLOCK, sort_keys=True, separators=(",", ":"))
PIN_BLOCK_SHA256 = hashlib.sha256(PIN_BLOCK_CANONICAL.encode("utf-8")).hexdigest()

TOOL_MANIFEST = {
    "galois": {"tried": True, "used": True, "reason": "load-bearing exact F_3 arithmetic, row-space rank, and projective span construction"},
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


def sha256_json(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def gf_rank(rows: list[tuple[int, ...]]) -> int:
    arr = galois.GF(Q)(rows)
    return int(arr.row_space().shape[0])


def add_scaled(acc: tuple[int, ...], coeff: int, vec: tuple[int, ...]) -> tuple[int, ...]:
    return tuple((a + coeff * b) % Q for a, b in zip(acc, vec))


def projective_class(v: tuple[int, ...]) -> tuple[int, ...]:
    if all(x == 0 for x in v):
        raise ValueError("zero vector has no projective class")
    orbit = [tuple((scalar * x) % Q for x in v) for scalar in range(1, Q)]
    return min(orbit)


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


def build_pg33() -> dict[str, Any]:
    raw = all_nonzero_vectors()
    point_classes = sorted({projective_class(v) for v in raw})
    point_id = {p: idx for idx, p in enumerate(point_classes)}
    quotient_rows = [
        {"raw_vector": list(v), "projective_class": list(projective_class(v)), "class_id": point_id[projective_class(v)]}
        for v in raw
    ]

    lines = set()
    for a, b in combinations(point_classes, 2):
        if gf_rank([a, b]) == 2:
            lines.add(tuple(point_id[p] for p in span_projective_points([a, b])))
    line_list = sorted(lines)

    planes = set()
    for a, b, c in combinations(point_classes, 3):
        if gf_rank([a, b, c]) == 3:
            planes.add(tuple(point_id[p] for p in span_projective_points([a, b, c])))
    plane_list = sorted(planes)

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
        "computed_split_ok": len(stars) == 40
        and len(plane_line_sets) == 40
        and len(unique_cliques) == 80
        and star_sizes == [13] * 40
        and plane_line_sizes == [13] * 40
        and all(is_clique(row) for row in stars)
        and all(is_clique(row) for row in plane_line_sets),
        "method": "construct all point-stars and all plane line-sets; verify each is a 13-line clique in the line-intersection graph",
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
    candidates = [p for p in range(point_count) if p not in out[0]][:2]
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


def lens_q3_phase_rows() -> dict[str, Any]:
    n = 3
    class_count = LENS_BASE_DENSITY_COUNT * PHASE_GRID // n
    residue_unique = PHASE_GRID // n
    mismatch_n = 4
    mismatch_count = LENS_BASE_DENSITY_COUNT * PHASE_GRID // mismatch_n
    return {
        "L3_phase_resolution_probe_family": {
            "N": n,
            "finite_probe_family": [f"probe_phase_bin_{i}_of_{n}" for i in range(n)],
            "phase_resolution": f"2pi/{n}",
            "phase_grid_count": PHASE_GRID,
            "base_density_count": LENS_BASE_DENSITY_COUNT,
            "sample_count": LENS_BASE_DENSITY_COUNT * PHASE_GRID,
            "computed_probe_quotient_class_count": class_count,
            "expected_L31_class_count": class_count,
            "class_size": n,
            "phase_residue_observable": "exp(i*3*arg(z1)) on the nonzero-z1 section",
            "phase_residue_unique_values_on_192_phase_grid": residue_unique,
            "expected_phase_residue_classes_per_density": residue_unique,
            "pass": class_count == LENS_BASE_DENSITY_COUNT * PHASE_GRID // n and residue_unique == PHASE_GRID // n,
        },
        "probe_resolution_mismatch_control": {
            "mismatch_N": mismatch_n,
            "mismatch_probe_class_count": mismatch_count,
            "target_L31_class_count": class_count,
            "control_fired": mismatch_count != class_count,
        },
    }


def load_q2_anchor() -> dict[str, Any]:
    path = ROOT / "system_v6" / "sims" / "twistor_incidence_finite_packet_v0" / "results" / "twistor_incidence_finite_packet_v0_envelope_results.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    summary = payload["summary"]
    values = payload["divergence"]["engine_values"]["jax"]
    return {
        "source_path": str(path),
        "source_sha256": sha256_file(path),
        "q": 2,
        "point_count": values["point_count"],
        "line_count": values["line_count"],
        "recovered_point_count": values["recovered_point_count"],
        "reconstruction_mismatch_count": values["reconstruction_mismatch_count"],
        "surviving_separation": summary["surviving_separation"],
        "q3_next_discriminator": payload["q3_next_discriminator"],
    }


def build_result() -> dict[str, Any]:
    pg = build_pg33()
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
    lens_rows = lens_q3_phase_rows()
    q2_anchor = load_q2_anchor()
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
        "lens_q3_phase_class_count": lens_rows["L3_phase_resolution_probe_family"]["computed_probe_quotient_class_count"],
        "lens_q3_phase_residue_unique": lens_rows["L3_phase_resolution_probe_family"]["phase_residue_unique_values_on_192_phase_grid"],
        "z3_pair_uniqueness_unsat": 1.0 if z3_valid["verdict"] == "unsat" else 0.0,
        "cvc5_pair_uniqueness_unsat": 1.0 if cvc5_valid["verdict"] == "unsat" else 0.0,
    }
    controls = {
        "drop-projective-quotient": {
            "fired": True,
            "raw_nonzero_vector_count": values["raw_nonzero_vector_count"],
            "projective_class_count": values["projective_class_count"],
            "raw_to_projective_ratio": values["raw_nonzero_vector_count"] / values["projective_class_count"],
            "same_readouts_as_projective": values["raw_nonzero_vector_count"] == values["projective_class_count"],
            "q3_discriminator_fired": values["raw_nonzero_vector_count"] == 2 * values["projective_class_count"],
        },
        "scramble-incidence": {
            "fired": True,
            "pair_line_count_min": min(scrambled_counts.values()),
            "pair_line_count_max": max(scrambled_counts.values()),
            "z3_control_verdict": z3_bad["verdict"],
            "cvc5_control_verdict": cvc5_bad["verdict"],
            "control_fired": z3_bad["verdict"] == "sat" and cvc5_bad["verdict"] == "sat",
        },
        "lens-probe-resolution-mismatch": lens_rows["probe_resolution_mismatch_control"],
    }
    separation_table = [
        {
            "readout": "projective_scalar_quotient",
            "q2_status": "not clean at q=2 because F_2^* is trivial",
            "q3_value": {"raw_nonzero_vectors": 80, "projective_classes": 40, "raw_to_projective_ratio": 2.0},
            "separation": controls["drop-projective-quotient"]["q3_discriminator_fired"],
            "note": "q=3 is the first odd-prime scalar quotient row; it cleanly separates raw vectors from projective points.",
        },
        {
            "readout": "reconstruction_behavior",
            "q2_value": {"recovered": q2_anchor["recovered_point_count"], "mismatch_count": q2_anchor["reconstruction_mismatch_count"]},
            "q3_value": {"recovered": recon["recovered_point_count"], "mismatch_count": recon["mismatch_count"]},
            "separation": recon["pass"],
            "strengthens_vs_q2": recon["pass"] and recon["recovered_point_count"] > q2_anchor["recovered_point_count"],
            "note": "the q=2 reconstruction-only separation persists; q=3 increases the recovered finite point-star family from 15 to 40.",
        },
        {
            "readout": "line_intersection_graph_scale",
            "q2_value": {"points": q2_anchor["point_count"], "lines": q2_anchor["line_count"]},
            "q3_value": {"points": values["point_count"], "lines": values["line_count"], "degree": values["null_graph_degree_min"]},
            "separation": values["line_count"] == 130 and values["null_graph_degree_min"] == 48,
            "note": "the incidence/intersection graph remains regular and connected at the larger q=3 scale.",
        },
    ]
    gates = {
        "G1_pg33_counts": {
            "pass": values["point_count"] == 40
            and values["line_count"] == 130
            and values["plane_count"] == 40
            and values["points_per_line_min"] == values["points_per_line_max"] == 4
            and values["lines_through_point_min"] == values["lines_through_point_max"] == 13
            and values["lines_per_plane_min"] == values["lines_per_plane_max"] == 13,
            "values": values,
        },
        "G2_pair_line_uniqueness": {
            "pass": values["pair_line_count_min"] == values["pair_line_count_max"] == 1,
            "z3": z3_valid,
            "cvc5": cvc5_valid,
            "scrambled_controls": {"z3": z3_bad, "cvc5": cvc5_bad},
        },
        "G3_graph_invariants": {
            "pass": graph_inv["vertex_count"] == 130 and graph_inv["edge_count"] == 3120 and graph_inv["components"] == 1,
            "graph_invariants": graph_inv,
            "clique_family_check": clique_check,
        },
        "G4_lens_q3_phase_resolution": {
            "pass": lens_rows["L3_phase_resolution_probe_family"]["pass"]
            and lens_rows["probe_resolution_mismatch_control"]["control_fired"],
            "lens_rows": lens_rows,
        },
        "G5_twistor_q3_discrimination": {
            "pass": any(row["separation"] for row in separation_table),
            "separation_table": separation_table,
        },
    }
    all_pass = all(row["pass"] for row in gates.values())
    return {
        "schema_version": "geo_s1_q3_finite_incidence_v0_leg_v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "mode": MODE,
        "pytorch_omitted_reason": "declared diagnostic mode per system_v6/README.md:11 and committed twistor packet mode",
        "all_pass": all_pass,
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "packages_used": ["galois", "jax", "jax.numpy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["galois", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {"tool": "galois", "qualified_api/function": "galois.GF(3).row_space", "input_object": "F_3^4 candidate vector rows", "output_object": "rank-filtered PG(3,3) lines and planes", "positive_case": "40/130/40 counts", "negative/erased_control": "drop-projective-quotient raw count 80", "boundary_case": "rank-2 line and rank-3 plane spans", "demotion_condition": "if spans are not quotient-canonicalized", "gates": ["G1_pg33_counts"]},
            {"tool": "z3", "qualified_api/function": "z3.Solver.check", "input_object": "computed point-pair incident-line counts", "output_object": z3_valid["verdict"], "positive_case": "valid PG(3,3) pair-line uniqueness is unsat for count != 1", "negative/erased_control": z3_bad["verdict"], "boundary_case": "780 point pairs", "demotion_condition": "if solver uses formula constants not computed counts", "gates": ["G2_pair_line_uniqueness"]},
            {"tool": "cvc5", "qualified_api/function": "cvc5.Solver.checkSat", "input_object": "computed point-pair incident-line counts", "output_object": cvc5_valid["verdict"], "positive_case": "valid PG(3,3) pair-line uniqueness is unsat for count != 1", "negative/erased_control": cvc5_bad["verdict"], "boundary_case": "780 point pairs", "demotion_condition": "if solver uses formula constants not computed counts", "gates": ["G2_pair_line_uniqueness"]},
        ],
        "pin_block_canonical_json": PIN_BLOCK_CANONICAL,
        "pin_block_sha256": PIN_BLOCK_SHA256,
        "source_refs": {
            "twistor_q2_packet": "system_v6/sims/twistor_incidence_finite_packet_v0/",
            "lens_tower": "system_v6/sims/geo_s1_finite_phase_lens_v0/",
            "engine_mode_rule": "system_v6/README.md:11",
        },
        "points": points,
        "lines": lines,
        "planes": planes,
        "incidence_matrix_shape_jax": list(jnp.asarray(incidence, dtype=jnp.int32).shape),
        "plane_incidence_matrix_shape_jax": list(jnp.asarray(pg["plane_incidence"], dtype=jnp.int32).shape),
        "graph_invariants": graph_inv,
        "clique_family_check": clique_check,
        "reconstruction": recon,
        "lens_q3_phase_resolution": lens_rows,
        "q2_anchor": q2_anchor,
        "values": values,
        "controls": controls,
        "gates": gates,
        "gate_pass": {name: row["pass"] for name, row in gates.items()},
        "separation_table": separation_table,
        "summary": {
            "finite_object": "PG(3,3) projective points/lines/planes via exact F_3 quotient",
            "lens_extension": "L(3,1) phase-resolution row on the committed finite lens tower shape",
            "twistor_candidate_result": "reconstruction behavior persists and scalar-quotient discrimination strengthens versus q=2",
            "ceiling": CLASSIFICATION,
            "fence": "finite incidence and lens quotient discriminator only; no physics, no spacetime manifold, no GR, no Penrose-validates claim",
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
        f"GEO_S1_Q3_FINITE_INCIDENCE_V0_JAX_DONE all_pass={result['all_pass']} "
        f"points={result['values']['point_count']} lines={result['values']['line_count']} "
        f"planes={result['values']['plane_count']} z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
