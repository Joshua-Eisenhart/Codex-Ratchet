#!/usr/bin/env python3
"""Independent TopoNetX/GUDHI topology parity guard for fiber_augmented_cover_v1."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import gudhi
import numpy as np
from toponetx.classes import CellComplex


SIM_ID = "topology_parity_micro_v0"
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
COMPLEX_BUILD_RULE = "undirected_lifted_adjacency_flag_2_complex_with_pinned_fiber_cycles"

TOOL_MANIFEST = {
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "builds CellComplex incidence matrices and Hodge Laplacian kernel dimensions for the finite parity complex",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "independently computes Betti numbers on the same finite simplicial complex",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "eigenvalue kernel-count check for TopoNetX Hodge Laplacians",
    },
    "fiber_augmented_cover_v1_common": {
        "tried": True,
        "used": True,
        "reason": "rebuilds the v1 and zero-shift product covers from the committed packet machinery by hash",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "shared builder/audit boundary guard so the builder packet does not claim its own audit verdict",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "numpy": "supportive",
    "fiber_augmented_cover_v1_common": "load_bearing",
    "builder_audit_boundary": "supportive",
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


def betti_from_simplex_tree(st: gudhi.SimplexTree, dims: int = 4) -> list[int]:
    st.compute_persistence(persistence_dim_max=True)
    betti = st.betti_numbers()
    while len(betti) < dims:
        betti.append(0)
    return [int(value) for value in betti[:dims]]


def hodge_kernel_dims(cc: CellComplex, dims: int = 3) -> list[int]:
    b1 = cc.incidence_matrix(1).toarray().astype(float)
    b2 = cc.incidence_matrix(2).toarray().astype(float)
    l0 = b1 @ b1.T
    l1 = b1.T @ b1 + b2 @ b2.T
    l2 = b2.T @ b2
    out = []
    for laplacian in (l0, l1, l2)[:dims]:
        evals = np.linalg.eigvalsh(laplacian)
        out.append(int((evals < 1e-8).sum()))
    return out


def graph_flag_triangles(vertices: list[int], edges: set[tuple[int, int]]) -> set[tuple[int, int, int]]:
    adjacency: dict[int, set[int]] = {vertex: set() for vertex in vertices}
    for left, right in edges:
        adjacency[left].add(right)
        adjacency[right].add(left)
    triangles: set[tuple[int, int, int]] = set()
    for a in vertices:
        for b in sorted(node for node in adjacency[a] if node > a):
            for c in sorted(node for node in adjacency[a] & adjacency[b] if node > b):
                triangles.add((a, b, c))
    return triangles


def lifted_edges_for_cover(cover: dict[str, Any]) -> set[tuple[int, int]]:
    edges: set[tuple[int, int]] = set()
    for row in cover["base_lift_edges"] + cover["fiber_edges"]:
        left, right = int(row["src"]), int(row["dst"])
        if left == right:
            continue
        edges.add(tuple(sorted((left, right))))
    return edges


def analyze_complex(label: str, cover: dict[str, Any]) -> dict[str, Any]:
    vertices = [int(row["cover_state_id"]) for row in cover["states"]]
    edges = lifted_edges_for_cover(cover)
    triangles = graph_flag_triangles(vertices, edges)
    st = simplex_tree_from_simplices(vertices, edges, triangles)
    cc = cell_complex_from_simplices(edges, triangles)
    betti = betti_from_simplex_tree(st)
    hodge = hodge_kernel_dims(cc)
    return {
        "label": label,
        "construction_rule": COMPLEX_BUILD_RULE,
        "source_cover_sha256": cover["cover_sha256"],
        "source_transition_rows_sha256": stable_sha256(cover["chart_transition_rows"]),
        "vertex_count": len(vertices),
        "undirected_nonself_edge_count": len(edges),
        "flag_triangle_count": len(triangles),
        "gudhi_betti_b0_b1_b2_b3": betti,
        "hodge_kernel_dims_b0_b1_b2": hodge,
        "gudhi_hodge_agree_through_b2": betti[:3] == hodge,
        "complex_sha256": stable_sha256(
            {
                "vertices": vertices,
                "edges": sorted(edges),
                "triangles": sorted(triangles),
                "rule": COMPLEX_BUILD_RULE,
            }
        ),
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
    edges = {tuple(sorted(edge)) for tri in triangles for edge in ((tri[0], tri[1]), (tri[0], tri[2]), (tri[1], tri[2]))}
    return topology_control_result("torus_reference", vertices, edges, triangles, [1, 2, 1])


def disk_reference() -> dict[str, Any]:
    vertices = [0, 1, 2, 3]
    triangles = {tuple(sorted((0, 1, 2))), tuple(sorted((0, 2, 3)))}
    edges = {tuple(sorted(edge)) for tri in triangles for edge in ((tri[0], tri[1]), (tri[0], tri[2]), (tri[1], tri[2]))}
    return topology_control_result("disk_reference", vertices, edges, triangles, [1, 0, 0])


def sphere_reference() -> dict[str, Any]:
    vertices = [0, 1, 2, 3]
    triangles = {
        tuple(sorted((0, 1, 2))),
        tuple(sorted((0, 1, 3))),
        tuple(sorted((0, 2, 3))),
        tuple(sorted((1, 2, 3))),
    }
    edges = {tuple(sorted(edge)) for tri in triangles for edge in ((tri[0], tri[1]), (tri[0], tri[2]), (tri[1], tri[2]))}
    return topology_control_result("sphere_reference", vertices, edges, triangles, [1, 0, 1])


def topology_control_result(
    label: str,
    vertices: list[int],
    edges: set[tuple[int, int]],
    triangles: set[tuple[int, int, int]],
    expected: list[int],
) -> dict[str, Any]:
    st = simplex_tree_from_simplices(vertices, edges, triangles)
    cc = cell_complex_from_simplices(edges, triangles)
    betti = betti_from_simplex_tree(st, dims=3)
    hodge = hodge_kernel_dims(cc)
    return {
        "label": label,
        "expected_betti": expected,
        "gudhi_betti": betti,
        "hodge_kernel_dims": hodge,
        "pass": betti == expected and hodge[:3] == expected and betti == hodge[:3],
    }


def run_reference_controls() -> dict[str, Any]:
    torus = torus_reference()
    disk = disk_reference()
    sphere = sphere_reference()
    mislabeled = {
        "label": "mislabeled_torus_as_sphere_negative",
        "input_complex": "torus_reference",
        "claimed_expected_betti": [1, 0, 1],
        "actual_gudhi_betti": torus["gudhi_betti"],
        "actual_hodge_kernel_dims": torus["hodge_kernel_dims"],
        "pass": torus["gudhi_betti"] != [1, 0, 1] and torus["hodge_kernel_dims"] != [1, 0, 1],
    }
    return {
        "torus_reference": torus,
        "disk_reference": disk,
        "sphere_reference": sphere,
        "mislabeled_torus_as_sphere_negative": mislabeled,
        "all_reference_controls_pass": all(row["pass"] for row in (torus, disk, sphere, mislabeled)),
    }


def expected_profiles_preregistered_from_math() -> dict[str, Any]:
    return {
        "v1_degree_one_cover": {
            "ideal_space": "S3_like_total_space",
            "expected_betti_b0_b1_b2_b3": [1, 0, 0, 1],
            "math_reason": "nontrivial circle bundle over S2 with Euler class +/-1 has S3-like homology",
        },
        "zero_shift_product_cover": {
            "ideal_space": "S2xS1_product_total_space",
            "expected_betti_b0_b1_b2_b3": [1, 1, 1, 1],
            "math_reason": "trivial circle bundle over S2 has product homology, including a circle-factor b1",
        },
    }


def parity_adjudication(v1: dict[str, Any], product: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    v1_expected = expected["v1_degree_one_cover"]["expected_betti_b0_b1_b2_b3"]
    product_expected = expected["zero_shift_product_cover"]["expected_betti_b0_b1_b2_b3"]
    v1_betti = v1["gudhi_betti_b0_b1_b2_b3"]
    product_betti = product["gudhi_betti_b0_b1_b2_b3"]
    computed_profiles_differ = v1_betti != product_betti
    ideal_profiles_match = v1_betti == v1_expected and product_betti == product_expected
    if ideal_profiles_match:
        guard_status = "earned_independent_topology_guard"
        outcome = "agreement"
        finding = "computed Betti profiles match the preregistered S3-like versus S2xS1 product expectation"
        caveat = "finite complex construction remains a discretization, but this guard resolves the preregistered profile under this rule"
    elif computed_profiles_differ:
        guard_status = "not_earned_resolution_insufficient"
        outcome = "discretization_fidelity_caveat"
        finding = (
            "the lifted adjacency flag complex distinguishes v1 from the zero-shift product, "
            "but both Betti profiles miss the preregistered ideal-space profile"
        )
        caveat = "the coarse adjacency-derived complex is not sufficient to adjudicate S3-like versus S2xS1 homology"
    else:
        guard_status = "not_earned_profiles_equal"
        outcome = "negative_or_unresolved"
        finding = "the computed finite complexes have equal Betti profiles under this construction"
        caveat = "equal profiles at this resolution cannot support the cover claim without a stronger cell model"
    return {
        "parity_question": "do the v1 and zero-shift product finite complexes differ as the bundle claim predicts",
        "expected_distinction": "v1 ideal b1=0 versus product ideal b1>=1",
        "computed_v1_betti": v1_betti,
        "computed_product_betti": product_betti,
        "computed_profiles_differ": computed_profiles_differ,
        "computed_b1_differs": v1_betti[1] != product_betti[1],
        "ideal_profiles_match": ideal_profiles_match,
        "guard_status": guard_status,
        "outcome": outcome,
        "finding": finding,
        "discretization_fidelity_caveat": caveat,
        "cover_construction_indicted": False,
        "complex_building_resolution_indicted": not ideal_profiles_match,
    }


def source_import_audit(v1_cover: dict[str, Any], zero_cover: dict[str, Any]) -> dict[str, Any]:
    return {
        "consume_row": source_lock(
            ROOT / "system_v6" / "receipts" / "old_sims_complete_consume_20260612.md",
            "gating_condition_for_topology_parity_micro_v0",
        ),
        "old_probe_source": source_lock(
            ROOT / "system_v4" / "probes" / "sim_toponetx_gudhi_hodge_betti_cross.py",
            "mechanics_feedstock_only_not_result_authority",
        ),
        "fiber_augmented_cover_v1_result": source_lock(
            FIBER_V1_DIR / "results" / "fiber_augmented_cover_v1_results.json",
            "primary_cover_artifact",
        ),
        "fiber_augmented_cover_v1_audit": source_lock(FIBER_V1_DIR / "audit_verdict.md", "cover_v1_audit_ceiling_and_g2a_boundary"),
        "v1_cover_sha256": v1_cover["cover_sha256"],
        "zero_shift_cover_sha256": zero_cover["cover_sha256"],
        "v1_transition_rows_sha256": stable_sha256(v1_cover["chart_transition_rows"]),
        "zero_shift_transition_rows_sha256": stable_sha256(zero_cover["chart_transition_rows"]),
    }


def build_topology_parity_object() -> dict[str, Any]:
    expected = expected_profiles_preregistered_from_math()
    v1_cover = cover_v1_common.build_cover(zero_shift=False)
    zero_cover = cover_v1_common.build_cover(zero_shift=True)
    controls = run_reference_controls()
    v1_complex = analyze_complex("v1_degree_one_cover", v1_cover)
    product_complex = analyze_complex("zero_shift_product_cover", zero_cover)
    parity = parity_adjudication(v1_complex, product_complex, expected)
    all_pass = (
        controls["all_reference_controls_pass"]
        and v1_complex["gudhi_hodge_agree_through_b2"]
        and product_complex["gudhi_hodge_agree_through_b2"]
        and builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    )
    return {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": now_z(),
        "preregistration_order": "expected_profiles_declared_before_computation",
        "expected_profiles_preregistered_from_math": expected,
        "source_cover": source_import_audit(v1_cover, zero_cover),
        "complex_build_rule": COMPLEX_BUILD_RULE,
        "complexes": {
            "v1_degree_one_cover": v1_complex,
            "zero_shift_product_cover": product_complex,
        },
        "controls": controls,
        "parity_adjudication": parity,
        "allowed_claims": [
            "TopoNetX/GUDHI toolchain sanity on torus/disk/sphere controls",
            "finite adjacency-derived parity guard for fiber_augmented_cover_v1 only",
            "computed-vs-expected report for the selected finite complex construction",
        ],
        "disallowed_claims": [
            "new bundle claim",
            "formal admission",
            "canonical by process",
            "axis-level closure",
            "physics/manifold claim",
            "cover-v1 audit replacement",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "no_builder_audit_verdict": True,
        "builder_gates": {
            "g2a_boundary_from_birth": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "no_git_add_or_commit_required": True,
        },
        "all_pass": all_pass,
        "result_summary": {
            "reference_controls_pass": controls["all_reference_controls_pass"],
            "v1_vs_product_profiles_differ": parity["computed_profiles_differ"],
            "independent_guard_earned": parity["guard_status"] == "earned_independent_topology_guard",
            "guard_status": parity["guard_status"],
            "claim_ceiling": CLAIM_CEILING,
        },
    }


def write_result() -> dict[str, Any]:
    payload = build_topology_parity_object()
    write_json(RESULT_PATH, payload)
    return payload


def write_envelope() -> dict[str, Any]:
    payload = build_topology_parity_object()
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
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "no_builder_audit_verdict": True,
    }
    write_json(ENVELOPE_RESULT_PATH, envelope)
    return envelope
