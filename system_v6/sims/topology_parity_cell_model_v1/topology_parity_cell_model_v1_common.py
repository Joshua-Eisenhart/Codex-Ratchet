#!/usr/bin/env python3
"""Bundle-derived cellular topology guard for fiber_augmented_cover_v1."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import gudhi
import sympy as sp
from sympy.matrices.normalforms import smith_normal_form
from toponetx.classes import CellComplex


SIM_ID = "topology_parity_cell_model_v1"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

FIBER_V1_DIR = ROOT / "system_v6" / "sims" / "fiber_augmented_cover_v1"
SCRIPTS_DIR = ROOT / "scripts"
for path in (FIBER_V1_DIR, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402
import fiber_augmented_cover_v1_common as cover_v1_common  # noqa: E402


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "scratch_diagnostic_independent_topology_guard_for_fiber_augmented_cover_v1_only"
BASE_FACE_COUNT = 33

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing integer boundary-matrix rank and Smith normal form torsion checks",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 0-2 cell-complex sanity checks for the v0 torus/sphere/disk controls",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent Betti checks for the v0 simplicial controls",
    },
    "fiber_augmented_cover_v1_common": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source of the committed 33-cell cover, fiber count, and clutching transition rows",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "G.2a builder/audit boundary check so this builder does not claim its own audit verdict",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "fiber_augmented_cover_v1_common": "load_bearing",
    "builder_audit_boundary": "load_bearing",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or None
    except Exception:
        return None


def source_lock(path: Path, role: str) -> dict[str, Any]:
    row: dict[str, Any] = {"role": role, "path": rel(path), "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    return row


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def matrix(rows: int, cols: int) -> sp.Matrix:
    return sp.zeros(rows, cols)


def rank(mat: sp.Matrix) -> int:
    if mat.rows == 0 or mat.cols == 0:
        return 0
    return int(mat.rank())


def smith_diagonal(mat: sp.Matrix) -> list[int]:
    if mat.rows == 0 or mat.cols == 0:
        return []
    diag = smith_normal_form(mat, domain=sp.ZZ)
    return [abs(int(diag[i, i])) for i in range(min(diag.rows, diag.cols)) if int(diag[i, i]) != 0]


def chain_result(label: str, dims: list[int], boundaries: dict[int, sp.Matrix], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    max_dim = len(dims) - 1
    boundary_ranks = {str(k): rank(boundaries.get(k, matrix(dims[k - 1], dims[k]))) for k in range(1, max_dim + 1)}
    composition_ok = True
    composition_errors: list[str] = []
    for k in range(2, max_dim + 1):
        prev = boundaries.get(k - 1, matrix(dims[k - 2], dims[k - 1]))
        cur = boundaries.get(k, matrix(dims[k - 1], dims[k]))
        product = prev * cur
        if product != sp.zeros(product.rows, product.cols):
            composition_ok = False
            composition_errors.append(f"d{k - 1}_d{k}_nonzero")
    betti = []
    for k in range(max_dim + 1):
        down = rank(boundaries.get(k, matrix(dims[k - 1], dims[k]))) if k > 0 else 0
        up = rank(boundaries.get(k + 1, matrix(dims[k], dims[k + 1]))) if k < max_dim else 0
        betti.append(int(dims[k] - down - up))
    result = {
        "label": label,
        "chain_dims_c0_to_cmax": dims,
        "boundary_ranks": boundary_ranks,
        "d_squared_zero": composition_ok,
        "d_squared_errors": composition_errors,
        "betti_b0_b1_b2_b3": (betti + [0, 0, 0, 0])[:4],
        "chain_sha256": stable_sha256(
            {
                "dims": dims,
                "boundaries": {str(k): [list(map(int, row)) for row in boundaries[k].tolist()] for k in sorted(boundaries)},
                "metadata": metadata or {},
            }
        ),
    }
    if metadata:
        result["metadata"] = metadata
    return result


def reduced_euler_chain(label: str, degree: int) -> dict[str, Any]:
    d2 = sp.Matrix([[degree]])
    row = chain_result(
        label,
        [1, 1, 1, 1],
        {1: sp.zeros(1, 1), 2: d2, 3: sp.zeros(1, 1)},
        {"cell_rule": "homology_reduced_oriented_circle_bundle_over_s2", "euler_degree": degree},
    )
    torsion = [value for value in smith_diagonal(d2) if value > 1]
    row["homology_torsion"] = {"H1": torsion, "H1_description": "free" if not torsion else " x ".join(f"Z/{value}" for value in torsion)}
    row["betti_only_underpowered"] = bool(torsion)
    return row


def expanded_bundle_chain(label: str, degree: int, seam: dict[str, Any]) -> dict[str, Any]:
    n = BASE_FACE_COUNT
    dims = [2, n + 2, 2 * n, n]
    d1 = matrix(dims[0], dims[1])
    for i in range(n):
        d1[0, i] = -1
        d1[1, i] = 1
    d2 = matrix(dims[1], dims[2])
    for i in range(n):
        d2[i, i] -= 1
        d2[(i + 1) % n, i] += 1
    if degree:
        d2[n, 0] += degree
    for i in range(n):
        col = n + i
        d2[n, col] = -1
        d2[n + 1, col] = 1
    d3 = matrix(dims[2], dims[3])
    for i in range(n):
        d3[n + i, i] -= 1
        d3[n + ((i + 1) % n), i] += 1
    return chain_result(
        label,
        dims,
        {1: d1, 2: d2, 3: d3},
        {
            "cell_rule": "33_face_base_s2_times_three_phase_circle_with_clutching_entry",
            "base_face_count": n,
            "euler_degree": degree,
            "clutching_source": seam,
        },
    )


def extract_seam_degree(cover: dict[str, Any]) -> dict[str, Any]:
    rows_by_pair = {(int(row["src"]), int(row["dst"])): row for row in cover["chart_transition_rows"]}
    shifts: list[int] = []
    pairs = cover_v1_common.equator_edge_pairs()
    for src, dst in pairs:
        shifts.append(int(rows_by_pair[(src, dst)]["fiber_phase_shift_steps"]))
    fiber_count = int(cover["fiber_phase_count_per_cell"])
    total = sum(shifts)
    degree = total // fiber_count if total % fiber_count == 0 else None
    return {
        "loop_name": cover_v1_common.EQUATOR_LOOP_NAME,
        "base_loop_cell_ids": list(cover_v1_common.EQUATOR_LOOP_CELLS),
        "base_loop_edge_pairs": [[src, dst] for src, dst in pairs],
        "fiber_phase_count": fiber_count,
        "seam_lifted_shift_steps": shifts,
        "total_lifted_shift_steps": total,
        "degree": degree,
        "degree_source": "sum committed chart_transition_rows on equatorial loop divided by |F|",
    }


def simplex_tree_from_simplices(vertices: list[int], edges: set[tuple[int, int]], triangles: set[tuple[int, int, int]]) -> gudhi.SimplexTree:
    st = gudhi.SimplexTree()
    for vertex in vertices:
        st.insert([vertex], filtration=0.0)
    for edge in sorted(edges):
        st.insert(list(edge), filtration=0.0)
    for triangle in sorted(triangles):
        st.insert(list(triangle), filtration=0.0)
    st.set_dimension(2)
    return st


def cell_complex_from_simplices(edges: set[tuple[int, int]], triangles: set[tuple[int, int, int]]) -> CellComplex:
    cc = CellComplex()
    for edge in sorted(edges):
        cc.add_cell(list(edge), rank=1)
    for triangle in sorted(triangles):
        cc.add_cell(list(triangle), rank=2)
    return cc


def gudhi_betti(vertices: list[int], edges: set[tuple[int, int]], triangles: set[tuple[int, int, int]]) -> list[int]:
    st = simplex_tree_from_simplices(vertices, edges, triangles)
    st.compute_persistence(persistence_dim_max=True)
    out = [int(value) for value in st.betti_numbers()]
    return (out + [0, 0, 0, 0])[:4]


def toponetx_hodge_betti(edges: set[tuple[int, int]], triangles: set[tuple[int, int, int]]) -> list[int]:
    cc = cell_complex_from_simplices(edges, triangles)
    b1 = sp.Matrix(cc.incidence_matrix(1).toarray().astype(int))
    b2 = sp.Matrix(cc.incidence_matrix(2).toarray().astype(int))
    return [int(cc.shape[0] - rank(b1)), int(cc.shape[1] - rank(b1) - rank(b2)), int(cc.shape[2] - rank(b2)), 0]


def topology_control_result(label: str, vertices: list[int], triangles: set[tuple[int, int, int]], expected: list[int]) -> dict[str, Any]:
    edges = {tuple(sorted(edge)) for tri in triangles for edge in ((tri[0], tri[1]), (tri[0], tri[2]), (tri[1], tri[2]))}
    g_betti = gudhi_betti(vertices, edges, triangles)
    h_betti = toponetx_hodge_betti(edges, triangles)
    return {
        "label": label,
        "expected_betti": expected,
        "betti_b0_b1_b2_b3": g_betti,
        "toponetx_hodge_betti_b0_b1_b2_b3": h_betti,
        "gudhi_toponetx_agree_through_b2": g_betti[:3] == h_betti[:3],
        "pass": g_betti[: len(expected)] == expected and h_betti[: len(expected)] == expected,
    }


def torus_reference(n: int = 4) -> dict[str, Any]:
    vertices = [i * n + j for i in range(n) for j in range(n)]

    def v(i: int, j: int) -> int:
        return (i % n) * n + (j % n)

    triangles: set[tuple[int, int, int]] = set()
    for i in range(n):
        for j in range(n):
            a, b, c, d = v(i, j), v(i + 1, j), v(i + 1, j + 1), v(i, j + 1)
            triangles.add(tuple(sorted((a, b, c))))
            triangles.add(tuple(sorted((a, c, d))))
    return topology_control_result("torus_reference", vertices, triangles, [1, 2, 1])


def disk_reference() -> dict[str, Any]:
    triangles = {tuple(sorted((0, 1, 2))), tuple(sorted((0, 2, 3)))}
    return topology_control_result("disk_reference", [0, 1, 2, 3], triangles, [1, 0, 0])


def sphere_reference() -> dict[str, Any]:
    triangles = {
        tuple(sorted((0, 1, 2))),
        tuple(sorted((0, 1, 3))),
        tuple(sorted((0, 2, 3))),
        tuple(sorted((1, 2, 3))),
    }
    return topology_control_result("sphere_reference", [0, 1, 2, 3], triangles, [1, 0, 1])


def run_controls() -> dict[str, Any]:
    torus = torus_reference()
    disk = disk_reference()
    sphere = sphere_reference()
    wrong = reduced_euler_chain("wrong_gluing_erased_v1_seam", 0)
    torsion = reduced_euler_chain("lens_space_torsion_trap_degree_2", 2)
    mislabeled = {
        "label": "mislabeled_torus_as_sphere_negative",
        "input_complex": "torus_reference",
        "claimed_expected_betti": [1, 0, 1],
        "actual_betti_b0_b1_b2_b3": torus["betti_b0_b1_b2_b3"],
        "pass": torus["betti_b0_b1_b2_b3"][:3] != [1, 0, 1],
    }
    return {
        "torus_reference": torus,
        "disk_reference": disk,
        "sphere_reference": sphere,
        "mislabeled_torus_as_sphere_negative": mislabeled,
        "wrong_gluing_erased_v1_seam": {
            "label": wrong["label"],
            "wrong_degree": 0,
            "wrong_betti_b0_b1_b2_b3": wrong["betti_b0_b1_b2_b3"],
            "pass": wrong["betti_b0_b1_b2_b3"] == [1, 1, 1, 1],
        },
        "torsion_trap_degree_2": {
            "label": torsion["label"],
            "degree": 2,
            "betti_b0_b1_b2_b3": torsion["betti_b0_b1_b2_b3"],
            "homology_torsion": torsion["homology_torsion"],
            "betti_only_underpowered": torsion["betti_only_underpowered"],
            "pass": torsion["betti_b0_b1_b2_b3"] == [1, 0, 0, 1] and torsion["homology_torsion"]["H1"] == [2],
        },
        "all_reference_controls_pass": all(row["pass"] for row in (torus, disk, sphere, mislabeled)) and torsion["homology_torsion"]["H1"] == [2],
    }


def run_reference_gate() -> dict[str, Any]:
    s3 = reduced_euler_chain("explicit_s3", 1)
    s3_neg = reduced_euler_chain("explicit_s3_orientation_negative", -1)
    product = reduced_euler_chain("explicit_s2xs1", 0)
    gate = (
        s3["betti_b0_b1_b2_b3"] == [1, 0, 0, 1]
        and s3_neg["betti_b0_b1_b2_b3"] == [1, 0, 0, 1]
        and product["betti_b0_b1_b2_b3"] == [1, 1, 1, 1]
        and s3["d_squared_zero"]
        and product["d_squared_zero"]
    )
    return {
        "explicit_s3": s3,
        "explicit_s3_orientation_negative": s3_neg,
        "explicit_s2xs1": product,
        "reference_gate_passed": gate,
        "gate_rule": "cover rows are skipped unless explicit S3 and S2xS1 reference profiles pass first",
    }


def expected_profiles_preregistered_from_math() -> dict[str, Any]:
    return {
        "v1_degree_one_cover": {
            "ideal_space": "S3_like_total_space",
            "expected_betti_b0_b1_b2_b3": [1, 0, 0, 1],
            "math_reason": "oriented circle bundle over S2 with Euler class +/-1 has S3-like homology",
        },
        "zero_shift_product_cover": {
            "ideal_space": "S2xS1_product_total_space",
            "expected_betti_b0_b1_b2_b3": [1, 1, 1, 1],
            "math_reason": "zero Euler class gives the product S2xS1 homology profile",
        },
    }


def parity_adjudication(v1: dict[str, Any], product: dict[str, Any], reference_gate: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    if not reference_gate["reference_gate_passed"]:
        return {
            "guard_status": "machinery_insufficient",
            "cover_rows_ran": False,
            "finding": "reference gate failed; cover rows skipped",
            "independent_guard_earned": False,
        }
    ideal_match = (
        v1["betti_b0_b1_b2_b3"] == expected["v1_degree_one_cover"]["expected_betti_b0_b1_b2_b3"]
        and product["betti_b0_b1_b2_b3"] == expected["zero_shift_product_cover"]["expected_betti_b0_b1_b2_b3"]
    )
    if ideal_match:
        status = "distinction_resolved_degree_one_side"
        finding = "expanded cellular chain model recovers the preregistered degree-one versus product Betti distinction"
    else:
        status = "still_insufficient"
        finding = "reference fixtures passed but cover profiles missed the preregistered distinction"
    return {
        "guard_status": status,
        "cover_rows_ran": True,
        "computed_v1_betti": v1["betti_b0_b1_b2_b3"],
        "computed_product_betti": product["betti_b0_b1_b2_b3"],
        "ideal_profiles_match": ideal_match,
        "computed_profiles_differ": v1["betti_b0_b1_b2_b3"] != product["betti_b0_b1_b2_b3"],
        "finding": finding,
        "independent_guard_earned": ideal_match,
        "claim_ceiling": CLAIM_CEILING,
    }


def source_import_audit(v1_cover: dict[str, Any], product_cover: dict[str, Any]) -> dict[str, Any]:
    return {
        "topology_parity_micro_v0_result": source_lock(
            ROOT / "system_v6/sims/topology_parity_micro_v0/results/topology_parity_micro_v0_results.json",
            "v0_honest_null_resolution_indicted",
        ),
        "topology_parity_micro_v0_source": source_lock(
            ROOT / "system_v6/sims/topology_parity_micro_v0/topology_parity_micro_v0_common.py",
            "v0_controls_and_preregistered_profiles",
        ),
        "fiber_augmented_cover_v1_source": source_lock(
            FIBER_V1_DIR / "fiber_augmented_cover_v1_common.py",
            "committed_cover_construction_and_clutching_rows",
        ),
        "fiber_augmented_cover_v1_result": source_lock(
            FIBER_V1_DIR / "results/fiber_augmented_cover_v1_results.json",
            "primary_cover_result_artifact",
        ),
        "v1_cover_sha256": v1_cover["cover_sha256"],
        "zero_shift_cover_sha256": product_cover["cover_sha256"],
    }


def build_topology_parity_cell_model_object() -> dict[str, Any]:
    expected = expected_profiles_preregistered_from_math()
    reference_gate = run_reference_gate()
    controls = run_controls()
    v1_cover = cover_v1_common.build_cover(zero_shift=False)
    product_cover = cover_v1_common.build_cover(zero_shift=True)
    v1_seam = extract_seam_degree(v1_cover)
    product_seam = extract_seam_degree(product_cover)
    complexes: dict[str, Any] = {}
    if reference_gate["reference_gate_passed"]:
        complexes = {
            "v1_degree_one_cover": expanded_bundle_chain("v1_degree_one_cover", int(v1_seam["degree"]), v1_seam),
            "zero_shift_product_cover": expanded_bundle_chain("zero_shift_product_cover", int(product_seam["degree"]), product_seam),
        }
        controls["wrong_gluing_erased_v1_seam"]["wrong_betti_b0_b1_b2_b3"] = expanded_bundle_chain(
            "wrong_gluing_erased_v1_seam",
            0,
            {**v1_seam, "degree": 0, "seam_lifted_shift_steps": [0, 0, 0, 0]},
        )["betti_b0_b1_b2_b3"]
        controls["wrong_gluing_erased_v1_seam"]["pass"] = (
            controls["wrong_gluing_erased_v1_seam"]["wrong_betti_b0_b1_b2_b3"]
            != complexes["v1_degree_one_cover"]["betti_b0_b1_b2_b3"]
            and controls["wrong_gluing_erased_v1_seam"]["wrong_betti_b0_b1_b2_b3"]
            == complexes["zero_shift_product_cover"]["betti_b0_b1_b2_b3"]
        )
    parity = parity_adjudication(complexes.get("v1_degree_one_cover", {}), complexes.get("zero_shift_product_cover", {}), reference_gate, expected)
    boundary_ok = builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    all_pass = bool(reference_gate["reference_gate_passed"] and controls["all_reference_controls_pass"] and controls["wrong_gluing_erased_v1_seam"]["pass"] and parity["cover_rows_ran"] and boundary_ok)
    return {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": now_z(),
        "preregistration_order": "cell_rules_and_expected_profiles_declared_before_computation",
        "expected_profiles_preregistered_from_math": expected,
        "source_cover": source_import_audit(v1_cover, product_cover),
        "cell_rules_pinned_before_computation": {
            "base_rule": "33 base faces around one cellular latitude with south/north endpoints, derived from committed 33-cell S2 bundle surface",
            "fiber_rule": "one directed S1 fiber cell pair per base cell, |F|=3 source phases",
            "gluing_rule": "seam edge a->b with shift s glues phase p to p+s mod |F|; chain twist is accumulated lifted seam degree",
            "no_target_betti_fitting": True,
        },
        "cover_inputs": {
            "v1": v1_seam,
            "zero_shift_product": product_seam,
        },
        "reference_gate": reference_gate,
        "complexes": complexes,
        "controls": controls,
        "parity_adjudication": parity,
        "allowed_claims": [
            "reference-fixture-gated cellular homology computation for the cover topology guard",
            "degree extracted from committed cover transition rows, not target Betti values",
            "scratch-diagnostic parity adjudication between degree-one and zero-shift cover chain models",
        ],
        "disallowed_claims": [
            "new bundle claim",
            "formal admission",
            "canonical by process",
            "axis-level closure",
            "bridge claim",
            "physics/manifold claim",
            "cover-v1 audit replacement",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "builder_gates": {
            "g2a_boundary_from_birth": boundary_ok,
            "boundary_helper_path": rel(SIM_DIR / "topology_parity_cell_model_v1_boundary.py"),
            "shared_boundary_helper": rel(SCRIPTS_DIR / "builder_audit_boundary.py"),
            "no_git_add_or_commit_required": True,
        },
        "all_pass": all_pass,
        "result_summary": {
            "reference_gate_passed": reference_gate["reference_gate_passed"],
            "independent_guard_earned": parity.get("independent_guard_earned") is True,
            "guard_status": parity["guard_status"],
            "claim_ceiling": CLAIM_CEILING,
        },
    }


def write_result() -> dict[str, Any]:
    payload = build_topology_parity_cell_model_object()
    write_json(RESULT_PATH, payload)
    return payload


def write_envelope() -> dict[str, Any]:
    payload = build_topology_parity_cell_model_object()
    envelope = {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": now_z(),
        "result_path": rel(RESULT_PATH),
        "all_pass": payload["all_pass"],
        "result_summary": payload["result_summary"],
        "parity_adjudication": payload["parity_adjudication"],
        "reference_gate": payload["reference_gate"],
        "cover_inputs": payload["cover_inputs"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "builder_gates": payload["builder_gates"],
    }
    write_json(ENVELOPE_RESULT_PATH, envelope)
    return envelope
