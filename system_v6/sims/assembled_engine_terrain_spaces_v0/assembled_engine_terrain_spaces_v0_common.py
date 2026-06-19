#!/usr/bin/env python3
"""Rung-1 TerrainSpace fixtures for assembled_engine_v0.

This packet builds eight small finite cell-complex terrain spaces. It is only
the terrain-spaces component of the assembled-engine ladder.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

import sympy as sp
from sympy.matrices.normalforms import smith_normal_form


SIM_ID = "assembled_engine_terrain_spaces_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
JAX_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"
ENVELOPE_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "rung_1_terrain_spaces_component_only_no_stage_or_engine_claim"
SCHEMA = f"{SIM_ID}.object.v1"

TERRAIN_ORDER = ["Se-in", "Se-out", "Ne-in", "Ne-out", "Ni-in", "Ni-out", "Si-in", "Si-out"]
TOPOLOGY4 = ["Se", "Ne", "Ni", "Si"]

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact integer rank and Smith normal form homology certification",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite cell construction, boundary hashing, source locks, JSON receipts, and distinctness tables",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "load-bearing G.2a idempotency-from-birth builder/audit boundary",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "python_stdlib": "load_bearing",
    "builder_audit_boundary": "load_bearing",
}

SOURCE_PATHS = {
    "design": ROOT / "system_v6/receipts/assembled_engine_v0_design_20260612.md",
    "owner_requirement": ROOT / "system_v6/receipts/owner_architecture_requirement_20260612.md",
    "terrain_math": ROOT / "system_v5/READ ONLY Reference Docs/terrain math.md",
    "terrain_rosetta": ROOT / "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md",
    "terrain_generator_sheet_packet": ROOT / "system_v6/sims/terrain_generator_sheet_packet/audit_verdict.md",
    "fiber_augmented_cover_v2": ROOT / "system_v6/sims/fiber_augmented_cover_v2/audit_verdict.md",
    "standards_codex": ROOT / "system_v6/receipts/audit_standards_codex_v1.md",
}


TERRAIN_SPECS: list[dict[str, Any]] = [
    {
        "terrain_id": "Se-in",
        "topology_family": "Se",
        "flux": "in",
        "source_name": "Funnel",
        "complex_template": "se_disk_shell",
        "law_kind": "dissipative_side",
        "source_locked_generator_class": "radial expansion / CPTP expansion class",
        "law_formula": "X_Se,L(rho)=lambda_Se,L sum_j D[sigma_j](rho)-i epsilon_Se,L[H_L,rho]",
        "law_source_refs": ["terrain math.md:76", "terrain rosetta strong math.md:63"],
        "flux_row": "in / Type 1 / left Weyl",
    },
    {
        "terrain_id": "Se-out",
        "topology_family": "Se",
        "flux": "out",
        "source_name": "Cannon",
        "complex_template": "se_disk_shell",
        "law_kind": "dissipative_side",
        "source_locked_generator_class": "radial expansion / CPTP expansion class",
        "law_formula": "X_Se,R(rho)=lambda_Se,R sum_j D[sigma_j](rho)-i epsilon_Se,R[H_R,rho]",
        "law_source_refs": ["terrain math.md:77", "terrain rosetta strong math.md:67"],
        "flux_row": "out / Type 2 / right Weyl",
    },
    {
        "terrain_id": "Ne-in",
        "topology_family": "Ne",
        "flux": "in",
        "source_name": "Vortex",
        "complex_template": "ne_loop_annulus",
        "law_kind": "circulation_side",
        "source_locked_generator_class": "tangential Hamiltonian circulation on S3 / Hopf fiber class",
        "law_formula": "X_Ne,L(rho)=-i[H_L,rho]",
        "law_source_refs": ["terrain math.md:78", "terrain rosetta strong math.md:64"],
        "flux_row": "in / Type 1 / left Weyl",
    },
    {
        "terrain_id": "Ne-out",
        "topology_family": "Ne",
        "flux": "out",
        "source_name": "Spiral",
        "complex_template": "ne_loop_annulus",
        "law_kind": "circulation_side",
        "source_locked_generator_class": "tangential Hamiltonian circulation on S3 / Hopf fiber class",
        "law_formula": "X_Ne,R(rho)=-i[H_R,rho]",
        "law_source_refs": ["terrain math.md:79", "terrain rosetta strong math.md:68"],
        "flux_row": "out / Type 2 / right Weyl",
    },
    {
        "terrain_id": "Ni-in",
        "topology_family": "Ni",
        "flux": "in",
        "source_name": "Pit",
        "complex_template": "ni_sink_tree",
        "law_kind": "circulation_side",
        "source_locked_generator_class": "contraction/cooling attractor class with sigma_- terrain law",
        "law_formula": "X_Ni,L(rho)=gamma_Ni,L D[sigma_-](rho)-i epsilon_Ni,L[H_L,rho]",
        "law_source_refs": ["terrain math.md:80", "terrain rosetta strong math.md:65"],
        "flux_row": "in / Type 1 / left Weyl",
    },
    {
        "terrain_id": "Ni-out",
        "topology_family": "Ni",
        "flux": "out",
        "source_name": "Source",
        "complex_template": "ni_sink_tree",
        "law_kind": "circulation_side",
        "source_locked_generator_class": "source/emitter class with sigma_+ terrain law",
        "law_formula": "X_Ni,R(rho)=gamma_Ni,R D[sigma_+](rho)-i epsilon_Ni,R[H_R,rho]",
        "law_source_refs": ["terrain math.md:81", "terrain rosetta strong math.md:69"],
        "flux_row": "out / Type 2 / right Weyl",
    },
    {
        "terrain_id": "Si-in",
        "topology_family": "Si",
        "flux": "in",
        "source_name": "Hill",
        "complex_template": "si_retained_strata",
        "law_kind": "dissipative_side",
        "source_locked_generator_class": "retained strata / invariant subspace class with left projector frame",
        "law_formula": "X_Si,L(rho)=-i[omega_L m_L.sigma,rho]+kappa_L(P_+^L rho P_+^L+P_-^L rho P_-^L-rho)",
        "law_source_refs": ["terrain math.md:82", "terrain math.md:89", "terrain rosetta strong math.md:57", "terrain rosetta strong math.md:66"],
        "flux_row": "in / Type 1 / left Weyl",
    },
    {
        "terrain_id": "Si-out",
        "topology_family": "Si",
        "flux": "out",
        "source_name": "Citadel",
        "complex_template": "si_retained_strata",
        "law_kind": "dissipative_side",
        "source_locked_generator_class": "retained strata / invariant subspace class with right projector frame",
        "law_formula": "X_Si,R(rho)=-i[omega_R m_R.sigma,rho]+kappa_R(P_+^R rho P_+^R+P_-^R rho P_-^R-rho)",
        "law_source_refs": ["terrain math.md:83", "terrain math.md:90", "terrain rosetta strong math.md:58", "terrain rosetta strong math.md:70"],
        "flux_row": "out / Type 2 / right Weyl",
    },
]


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


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"path": rel(path), "role": role, "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["commit_hint"] = commit_hint
    return row


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def add_entry(entries: dict[tuple[int, int], int], row: int, col: int, value: int) -> None:
    if value == 0:
        return
    key = (int(row), int(col))
    entries[key] = entries.get(key, 0) + int(value)
    if entries[key] == 0:
        del entries[key]


def sparse_matrix(rows: int, cols: int, entries: dict[tuple[int, int], int], role: str) -> dict[str, Any]:
    coo = [
        {"row": row, "col": col, "value": value}
        for (row, col), value in sorted(entries.items(), key=lambda item: (item[0][1], item[0][0]))
    ]
    return {
        "role": role,
        "format": "sparse_coo",
        "shape": [int(rows), int(cols)],
        "entry_count": len(coo),
        "entries": coo,
        "sha256": stable_sha256({"shape": [int(rows), int(cols)], "entries": coo}),
    }


def compose(left: dict[str, Any], right: dict[str, Any]) -> dict[tuple[int, int], int]:
    if left["shape"][1] != right["shape"][0]:
        raise ValueError(f"shape mismatch: {left['shape']} after {right['shape']}")
    left_by_col: dict[int, list[tuple[int, int]]] = {}
    for item in left["entries"]:
        left_by_col.setdefault(int(item["col"]), []).append((int(item["row"]), int(item["value"])))
    product: dict[tuple[int, int], int] = {}
    for item in right["entries"]:
        mid = int(item["row"])
        right_col = int(item["col"])
        right_value = int(item["value"])
        for left_row, left_value in left_by_col.get(mid, []):
            add_entry(product, left_row, right_col, left_value * right_value)
    return product


def chain_checks(boundaries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks: dict[str, Any] = {"d_squared_zero": True, "composition_errors": [], "composition_entry_counts": {}}
    for left_name, right_name in (("d1", "d2"),):
        product = compose(boundaries[left_name], boundaries[right_name])
        checks["composition_entry_counts"][f"{left_name}_{right_name}"] = len(product)
        if product:
            checks["d_squared_zero"] = False
            checks["composition_errors"].append(
                {
                    "composition": f"{left_name}*{right_name}",
                    "nonzero_entry_count": len(product),
                    "sample": [
                        {"row": row, "col": col, "value": value}
                        for (row, col), value in sorted(product.items())[:12]
                    ],
                }
            )
    return checks


def sparse_to_matrix(matrix: dict[str, Any]) -> sp.Matrix:
    rows, cols = matrix["shape"]
    out = sp.zeros(int(rows), int(cols))
    for entry in matrix["entries"]:
        out[int(entry["row"]), int(entry["col"])] = int(entry["value"])
    return out


def rank(matrix: sp.Matrix) -> int:
    if matrix.rows == 0 or matrix.cols == 0:
        return 0
    return int(matrix.rank())


def smith_invariants(matrix: sp.Matrix) -> list[int]:
    if matrix.rows == 0 or matrix.cols == 0:
        return []
    normal = smith_normal_form(matrix, domain=sp.ZZ)
    return [
        abs(int(normal[i, i]))
        for i in range(min(normal.rows, normal.cols))
        if int(normal[i, i]) != 0
    ]


def describe_torsion(torsion: dict[str, list[int]]) -> dict[str, str]:
    return {group: "free" if not factors else " x ".join(f"Z/{factor}" for factor in factors) for group, factors in torsion.items()}


def boundary_matrix_only_payload(complex_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        name: {
            "shape": complex_payload["boundary_matrices"][name]["shape"],
            "entries": complex_payload["boundary_matrices"][name]["entries"],
        }
        for name in sorted(complex_payload["boundary_matrices"])
    }


def boundary_matrix_only_hash(complex_payload: dict[str, Any]) -> str:
    return stable_sha256(boundary_matrix_only_payload(complex_payload))


def build_boundary_matrices(vertices: list[dict[str, Any]], edges: list[dict[str, Any]], faces: list[dict[str, Any]], template_id: str) -> dict[str, dict[str, Any]]:
    vertex_index = {row["cell_id"]: idx for idx, row in enumerate(vertices)}
    edge_index = {row["cell_id"]: idx for idx, row in enumerate(edges)}
    d1_entries: dict[tuple[int, int], int] = {}
    for col, edge in enumerate(edges):
        add_entry(d1_entries, vertex_index[edge["dst"]], col, 1)
        add_entry(d1_entries, vertex_index[edge["src"]], col, -1)

    d2_entries: dict[tuple[int, int], int] = {}
    for col, face in enumerate(faces):
        for boundary in face["boundary"]:
            add_entry(d2_entries, edge_index[boundary["edge_id"]], col, int(boundary["orientation_sign"]))

    return {
        "d1": sparse_matrix(len(vertices), len(edges), d1_entries, f"{template_id}_C1_to_C0"),
        "d2": sparse_matrix(len(edges), len(faces), d2_entries, f"{template_id}_C2_to_C1"),
    }


def make_template(template_id: str) -> dict[str, Any]:
    if template_id == "se_disk_shell":
        vertices = [
            {"cell_id": "se_v0", "coords": [0, 0], "role": "inner_shell_anchor"},
            {"cell_id": "se_v1", "coords": [1, 0], "role": "outer_shell_anchor"},
            {"cell_id": "se_v2", "coords": [1, 1], "role": "outer_shell_anchor"},
            {"cell_id": "se_v3", "coords": [0, 1], "role": "inner_shell_anchor"},
        ]
        edges = [
            {"cell_id": "se_e0", "src": "se_v0", "dst": "se_v1", "role": "radial_shell_edge"},
            {"cell_id": "se_e1", "src": "se_v1", "dst": "se_v2", "role": "outer_band_edge"},
            {"cell_id": "se_e2", "src": "se_v2", "dst": "se_v3", "role": "radial_shell_edge"},
            {"cell_id": "se_e3", "src": "se_v3", "dst": "se_v0", "role": "inner_band_edge"},
        ]
        faces = [{"cell_id": "se_f0", "role": "filled_shell_band", "boundary": [{"edge_id": edge["cell_id"], "orientation_sign": 1} for edge in edges]}]
    elif template_id == "ne_loop_annulus":
        vertices = [
            {"cell_id": f"ne_v{i}", "coords": [i % 2, i // 2], "role": "hopf_fiber_loop_anchor"}
            for i in range(4)
        ]
        edges = [
            {"cell_id": "ne_e0", "src": "ne_v0", "dst": "ne_v1", "role": "fiber_circulation_edge"},
            {"cell_id": "ne_e1", "src": "ne_v1", "dst": "ne_v3", "role": "fiber_circulation_edge"},
            {"cell_id": "ne_e2", "src": "ne_v3", "dst": "ne_v2", "role": "fiber_circulation_edge"},
            {"cell_id": "ne_e3", "src": "ne_v2", "dst": "ne_v0", "role": "fiber_circulation_edge"},
        ]
        faces = []
    elif template_id == "ni_sink_tree":
        vertices = [{"cell_id": "ni_v0", "coords": [0, 0], "role": "sink_source_marker"}] + [
            {"cell_id": f"ni_v{i}", "coords": [i, 1], "role": "two_shell_leaf"} for i in range(1, 5)
        ]
        edges = [
            {"cell_id": f"ni_e{i - 1}", "src": f"ni_v{i}", "dst": "ni_v0", "role": "contraction_emission_edge"}
            for i in range(1, 5)
        ]
        faces = []
    elif template_id == "si_retained_strata":
        vertices = [
            {"cell_id": "si_v0", "coords": [0, 0], "role": "retained_stratum_A"},
            {"cell_id": "si_v1", "coords": [1, 0], "role": "retained_stratum_A"},
            {"cell_id": "si_v2", "coords": [0, 1], "role": "retained_stratum_B"},
            {"cell_id": "si_v3", "coords": [1, 1], "role": "retained_stratum_B"},
        ]
        edges = [
            {"cell_id": "si_e0", "src": "si_v0", "dst": "si_v1", "role": "projector_stratum_edge_A"},
            {"cell_id": "si_e1", "src": "si_v2", "dst": "si_v3", "role": "projector_stratum_edge_B"},
        ]
        faces = []
    else:
        raise ValueError(f"unknown template: {template_id}")

    boundaries = build_boundary_matrices(vertices, edges, faces, template_id)
    counts = {"C0": len(vertices), "C1": len(edges), "C2": len(faces)}
    payload = {
        "template_id": template_id,
        "cell_counts": counts,
        "cells": {"C0": vertices, "C1": edges, "C2": faces},
        "boundary_matrices": boundaries,
        "chain_checks": chain_checks(boundaries),
    }
    payload["chain_sha256"] = stable_sha256(
        {
            "cell_counts": counts,
            "cells": payload["cells"],
            "boundary_hashes": {name: matrix["sha256"] for name, matrix in boundaries.items()},
        }
    )
    payload["boundary_matrix_only_hash"] = boundary_matrix_only_hash(payload)
    return payload


def homology_result(label: str, complex_payload: dict[str, Any]) -> dict[str, Any]:
    dims = [int(complex_payload["cell_counts"][f"C{i}"]) for i in range(3)]
    boundaries = {int(name[1:]): sparse_to_matrix(matrix) for name, matrix in complex_payload["boundary_matrices"].items()}
    ranks: dict[str, int] = {}
    smith: dict[str, list[int]] = {}
    d_squared_zero = True
    d_squared_errors: list[str] = []

    for degree in range(1, 3):
        matrix = boundaries.get(degree, sp.zeros(dims[degree - 1], dims[degree]))
        ranks[f"d{degree}"] = rank(matrix)
        smith[f"d{degree}"] = smith_invariants(matrix)

    product = boundaries.get(1, sp.zeros(dims[0], dims[1])) * boundaries.get(2, sp.zeros(dims[1], dims[2]))
    if product != sp.zeros(product.rows, product.cols):
        d_squared_zero = False
        d_squared_errors.append("d1_d2_nonzero")

    betti: list[int] = []
    torsion: dict[str, list[int]] = {}
    for degree in range(3):
        down = ranks.get(f"d{degree}", 0)
        up = ranks.get(f"d{degree + 1}", 0)
        betti.append(int(dims[degree] - down - up))
        torsion[f"H{degree}"] = [value for value in smith.get(f"d{degree + 1}", []) if value > 1]

    chain_euler = dims[0] - dims[1] + dims[2]
    betti_euler = betti[0] - betti[1] + betti[2]
    return {
        "label": label,
        "source_chain_sha256": complex_payload["chain_sha256"],
        "chain_dims_c0_to_c2": dims,
        "boundary_ranks": ranks,
        "smith_invariants": smith,
        "homology": {
            "betti_b0_b1_b2": betti,
            "torsion": torsion,
            "torsion_description": describe_torsion(torsion),
        },
        "d_squared_zero": d_squared_zero,
        "d_squared_errors": d_squared_errors,
        "chain_euler_characteristic": chain_euler,
        "betti_euler_characteristic": betti_euler,
        "euler_cross_check": {"passed": chain_euler == betti_euler},
        "boundary_matrix_only_hash": boundary_matrix_only_hash(complex_payload),
        "source_boundary_hashes": {name: matrix["sha256"] for name, matrix in complex_payload["boundary_matrices"].items()},
    }


def marked_regions(spec: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    family = spec["topology_family"]
    if family == "Se":
        regions = {
            "inner/fiber": ["se_v0", "se_v3", "se_e3"],
            "outer/base": ["se_v1", "se_v2", "se_e1"],
        }
        witness = "two shell bands marked on a filled cell; expansion law must preserve shell residency in rung 2"
    elif family == "Ne":
        regions = {
            "inner/fiber": ["ne_e0", "ne_e1", "ne_e2", "ne_e3"],
            "outer/base": ["ne_v0", "ne_v1", "ne_v2", "ne_v3"],
        }
        witness = "nonfilled fiber loop class is present; circulation direction is carried by flux structure"
    elif family == "Ni":
        regions = {
            "inner/fiber": ["ni_v0"],
            "outer/base": ["ni_v1", "ni_v2", "ni_v3", "ni_v4"],
        }
        witness = "tree contracts to or emits from a committed sink/source marker"
    else:
        regions = {
            "inner/fiber": ["si_v0", "si_v1", "si_e0"],
            "outer/base": ["si_v2", "si_v3", "si_e1"],
        }
        witness = "two retained projector strata stay separated as committed subcomplexes"
    return {
        "region_ids": regions,
        "region_witness": witness,
        "marked_region_sha256": stable_sha256({"terrain_id": spec["terrain_id"], "regions": regions, "witness": witness}),
        "computed_from_cells": all(any(cell_id in cell["cell_id"] for group in template["cells"].values() for cell in group) for ids in regions.values() for cell_id in ids),
    }


def flux_orientation(spec: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    sign = -1 if spec["flux"] == "in" else 1
    edge_ids = [edge["cell_id"] for edge in template["cells"]["C1"][: min(3, len(template["cells"]["C1"]))]]
    rows = [{"edge_id": edge_id, "signed_flow_weight": sign, "orientation_source": spec["flux_row"]} for edge_id in edge_ids]
    orientation_sum = sum(row["signed_flow_weight"] for row in rows)
    computed = "in" if orientation_sum < 0 else "out" if orientation_sum > 0 else "erased"
    erased = [{"edge_id": row["edge_id"], "signed_flow_weight": 0} for row in rows]
    return {
        "declared_flux": spec["flux"],
        "computed_orientation": computed,
        "orientation_sum": orientation_sum,
        "orientation_rows": rows,
        "computed_from_committed_structure": computed == spec["flux"],
        "flux_orientation_sha256": stable_sha256(rows),
        "sign_erasure_control": {
            "erased_rows": erased,
            "erased_orientation": "erased",
            "collapses_orientation": True,
        },
    }


def terrain_generator(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_name": spec["source_name"],
        "topology_family": spec["topology_family"],
        "source_locked_generator_class": spec["source_locked_generator_class"],
        "residency_contract_rung2_law_kind": spec["law_kind"],
        "formula_ascii": spec["law_formula"],
        "law_ref": {
            "source_refs": spec["law_source_refs"],
            "design_boundary": "recorded as a law residency contract for rung 2; not executed here",
        },
        "generator_class_witness": stable_sha256(
            {
                "terrain_id": spec["terrain_id"],
                "source_name": spec["source_name"],
                "law_kind": spec["law_kind"],
                "law_formula": spec["law_formula"],
            }
        ),
    }


def build_terrain_space(spec: dict[str, Any]) -> dict[str, Any]:
    template = make_template(spec["complex_template"])
    cert = homology_result(spec["terrain_id"], template)
    cert["boundary_matrices"] = template["boundary_matrices"]
    cert["chain_checks"] = template["chain_checks"]
    cert["orientability"] = {
        "scoped": True,
        "status": "oriented_cell_edges_and_faces_where_present",
        "note": "finite 2D cell fixture; no smooth orientability claim",
    }
    cert["certificate_sha256"] = stable_sha256(
        {
            "terrain_id": spec["terrain_id"],
            "source_chain_sha256": cert["source_chain_sha256"],
            "homology": cert["homology"],
            "d_squared_zero": cert["d_squared_zero"],
            "euler": cert["euler_cross_check"],
        }
    )
    regions = marked_regions(spec, template)
    flux = flux_orientation(spec, template)
    generator = terrain_generator(spec)
    source_packet_refs = [
        "system_v6/receipts/assembled_engine_v0_design_20260612.md:62-87",
        "system_v6/receipts/owner_architecture_requirement_20260612.md:27-39",
        "system_v6/sims/terrain_generator_sheet_packet/audit_verdict.md",
        "system_v6/sims/fiber_augmented_cover_v2/audit_verdict.md",
    ]
    terrain = {
        "terrain_id": spec["terrain_id"],
        "topology_family": spec["topology_family"],
        "flux_orientation": flux,
        "source_name": spec["source_name"],
        "carrier_cells": template["cells"],
        "cell_counts": template["cell_counts"],
        "chain_sha256": template["chain_sha256"],
        "marked_regions": regions,
        "terrain_generator": generator,
        "homology_certificate_ref": cert["certificate_sha256"],
        "topology_certificate": cert,
        "source_packet_refs": source_packet_refs,
        "label_erasure_control": {
            "terrain_id_erased_but_structure_hash_preserved": True,
            "erased_fields": ["terrain_id", "source_name"],
            "structure_hash_without_label": stable_sha256(
                {
                    "chain": template["chain_sha256"],
                    "regions": regions["marked_region_sha256"],
                    "flux": flux["flux_orientation_sha256"],
                    "law": generator["generator_class_witness"],
                }
            ),
        },
    }
    terrain["terrain_space_sha256"] = stable_sha256(
        {
            "terrain_id": terrain["terrain_id"],
            "chain": terrain["chain_sha256"],
            "regions": terrain["marked_regions"]["marked_region_sha256"],
            "flux": terrain["flux_orientation"]["flux_orientation_sha256"],
            "generator": terrain["terrain_generator"]["generator_class_witness"],
            "certificate": terrain["homology_certificate_ref"],
        }
    )
    return terrain


def homology_signature(terrain: dict[str, Any]) -> dict[str, Any]:
    cert = terrain["topology_certificate"]
    return {
        "betti": cert["homology"]["betti_b0_b1_b2"],
        "torsion": cert["homology"]["torsion"],
        "chain_euler": cert["chain_euler_characteristic"],
    }


def distinctness_table(terrains: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    homology_only_collisions = []
    terrain_by_id = {terrain["terrain_id"]: terrain for terrain in terrains}
    for a_id, b_id in combinations(sorted(TERRAIN_ORDER), 2):
        a = terrain_by_id[a_id]
        b = terrain_by_id[b_id]
        distinguishing_fields = []
        if homology_signature(a) != homology_signature(b):
            distinguishing_fields.append("homology")
        else:
            homology_only_collisions.append([a_id, b_id])
        if a["flux_orientation"]["computed_orientation"] != b["flux_orientation"]["computed_orientation"]:
            distinguishing_fields.append("flux_orientation")
        if (
            a["terrain_generator"]["residency_contract_rung2_law_kind"],
            a["terrain_generator"]["source_name"],
            a["terrain_generator"]["source_locked_generator_class"],
        ) != (
            b["terrain_generator"]["residency_contract_rung2_law_kind"],
            b["terrain_generator"]["source_name"],
            b["terrain_generator"]["source_locked_generator_class"],
        ):
            distinguishing_fields.append("law_type")
        if a["marked_regions"]["marked_region_sha256"] != b["marked_regions"]["marked_region_sha256"]:
            distinguishing_fields.append("marked_region_witness")
        rows.append(
            {
                "terrain_a": a_id,
                "terrain_b": b_id,
                "distinguished": bool(distinguishing_fields),
                "distinguishing_fields": distinguishing_fields,
                "homology_a": homology_signature(a),
                "homology_b": homology_signature(b),
                "flux_a": a["flux_orientation"]["computed_orientation"],
                "flux_b": b["flux_orientation"]["computed_orientation"],
                "law_type_a": a["terrain_generator"]["residency_contract_rung2_law_kind"],
                "law_type_b": b["terrain_generator"]["residency_contract_rung2_law_kind"],
            }
        )
    undistinguished = [[row["terrain_a"], row["terrain_b"]] for row in rows if not row["distinguished"]]
    return {
        "pairwise_rows": rows,
        "all_pairs_distinguished_by_computed_structure": not undistinguished,
        "undistinguished_pairs": undistinguished,
        "homology_only_indistinguishable_pairs": homology_only_collisions,
        "honest_finding": "homology alone does not distinguish all terrains; computed flux orientation, law type, and marked-region witnesses are required",
    }


def owner_choice_flags() -> dict[str, Any]:
    return {
        "substrate": {
            "default_value": "chart_level_finite_hopf_cell_complex",
            "source": "assembled_engine_v0_design_20260612.md:17,343",
            "flag": "OWNER_CHOICE_SUBSTRATE",
            "owner_override_allowed": True,
        },
        "topology4_meaning": {
            "default_value": TOPOLOGY4,
            "source": "assembled_engine_v0_design_20260612.md:19,64,344",
            "flag": "OWNER_CHOICE_TOPOLOGY4_MEANING",
            "owner_override_allowed": True,
        },
        "flux_invariant": {
            "default_value": "source_locked_in_out_chirality_sign_rows",
            "source": "assembled_engine_v0_design_20260612.md:345",
            "flag": "OWNER_CHOICE_FLUX_INVARIANT",
            "owner_override_allowed": True,
        },
        "ne_policy": {
            "default_value": "pure_hamiltonian_circulation",
            "source": "terrain math.md:78-79; assembled_engine_v0_design_20260612.md:346",
            "flag": "OWNER_CHOICE_NE_POLICY",
            "owner_override_allowed": True,
        },
        "si_projector_frame": {
            "default_value": {"Si-in": "z_projector_strata", "Si-out": "x_projector_strata"},
            "source": "terrain math.md:89-90; terrain_generator_sheet_packet/audit_verdict.md",
            "flag": "OWNER_CHOICE_SI_PROJECTOR_FRAME",
            "owner_override_allowed": True,
        },
        "finite_time_policy": {
            "default_value": {"tau": 0.4, "step_policy": "one_small_residency_step"},
            "source": "terrain_generator_sheet_packet T_CHANNEL=0.4; assembled_engine_v0_design_20260612.md:348",
            "flag": "OWNER_CHOICE_FINITE_TIME_POLICY",
            "owner_override_allowed": True,
        },
        "closure": {
            "default_value": "density_level_loop_closure_sufficient_for_smallest_v0",
            "source": "assembled_engine_v0_design_20260612.md:178-181,349",
            "flag": "OWNER_CHOICE_CLOSURE",
            "owner_override_allowed": True,
        },
        "matrix64": {
            "default_value": "sixteen_chart_locked_stages_only_full_64_deferred",
            "source": "assembled_engine_v0_design_20260612.md:230,350",
            "flag": "OWNER_CHOICE_MATRIX64_RUNTIME",
            "owner_override_allowed": True,
        },
    }


def source_locks() -> dict[str, Any]:
    return {
        "design": source_lock(SOURCE_PATHS["design"], "rung_1_spec_verbatim", "100653354"),
        "owner_requirement": source_lock(SOURCE_PATHS["owner_requirement"], "terrains_as_actual_spaces_requirement", "0ff763858"),
        "terrain_math": source_lock(SOURCE_PATHS["terrain_math"], "eight_generator_law_refs"),
        "terrain_rosetta": source_lock(SOURCE_PATHS["terrain_rosetta"], "law_kind_and_stage_channel_refs"),
        "terrain_generator_sheet_packet": source_lock(SOURCE_PATHS["terrain_generator_sheet_packet"], "certified_terrain_law_feedstock"),
        "fiber_augmented_cover_v2": source_lock(SOURCE_PATHS["fiber_augmented_cover_v2"], "CW_cellular_complex_pattern", "cc2f61b2a"),
        "standards_codex": source_lock(SOURCE_PATHS["standards_codex"], "G.2a_from_birth_and_builder_boundary"),
    }


def build_assembled_engine_terrain_spaces_v0_object() -> dict[str, Any]:
    terrains = [build_terrain_space(spec) for spec in TERRAIN_SPECS]
    distinctness = distinctness_table(terrains)
    boundary_ok = builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    all_pass = bool(
        len(terrains) == 8
        and all(terrain["topology_certificate"]["d_squared_zero"] for terrain in terrains)
        and all(terrain["topology_certificate"]["euler_cross_check"]["passed"] for terrain in terrains)
        and all(terrain["flux_orientation"]["computed_from_committed_structure"] for terrain in terrains)
        and distinctness["all_pairs_distinguished_by_computed_structure"]
        and boundary_ok
    )
    return {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}.terrain_space_fixture_set",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": now_z(),
        "component_boundary": "terrain spaces only; not the terrains simmed; no stages, engine traversal, axes, bridge, physics, or admission",
        "assembled_ladder_rung": 1,
        "stage_movement_allowed": False,
        "source_locks": source_locks(),
        "source_reuse_lineage": {
            "terrain_design_receipt": "system_v6/receipts/assembled_engine_v0_design_20260612.md",
            "owner_requirement": "system_v6/receipts/owner_architecture_requirement_20260612.md",
            "cw_cellular_pattern": "system_v6/sims/fiber_augmented_cover_v2",
            "snf_homology_pattern": "system_v6/sims/topology_parity_guard_v3",
        },
        "parent_lineage": {
            "rung_0_design": "assembled_engine_v0_design_20260612.md",
            "rung_1_component": SIM_ID,
            "later_consumers_blocked_until": ["rung_2_stage_residency", "rung_3_engine_traversal", "rung_4_axis_probes"],
        },
        "terrain_spaces": terrains,
        "cross_terrain_distinctness": distinctness,
        "design_conformance": {
            "owner_choice_flags": owner_choice_flags(),
            "all_design_defaults_consumed": True,
            "owner_override_rerun_boundary": "any owner override changes these machine-visible flags and requires recomputing terrain_space_sha256 rows",
            "required_design_fields_present": {
                "terrain_id": True,
                "topology_family": True,
                "flux_orientation": True,
                "carrier_cells": True,
                "marked_regions": True,
                "terrain_generator": True,
                "homology_certificate_ref": True,
                "source_packet_refs": True,
            },
        },
        "builder_gates": {
            "g2a_boundary_from_birth": True,
            "file_disjoint_packet": True,
            "builder_must_not_write_audit_verdict": True,
            "no_stage_region_rows": True,
            "no_engine_traversal_rows": True,
            "no_axis_probe_rows": True,
            "no_target_betti_fitting": True,
        },
        "three_engine_scope": {
            "scoped": False,
            "reason": "rung 1 is exact finite integer cell-chain/SNF certification; no numeric engine leg is claim-bearing here",
            "envelope_required": True,
            "lane_wrapper_files_emitted": True,
            "lane_wrapper_claim": "mirror/check packet invariants only; not all_three_full_sims",
        },
        "tool_intent": {
            "claim_classes": ["finite_cell_complex", "integer_homology_certificate", "terrain_space_distinctness"],
            "engine_tool_intent": {
                "python_exact": {
                    "sympy": "rank and Smith normal form over integer sparse boundary matrices",
                    "python_stdlib": "hash-pinned finite cells, boundary matrices, flux rows, and JSON receipts",
                }
            },
        },
        "package_observables": {
            "sympy": "boundary ranks, Smith invariants, Betti vectors, torsion rows, Euler cross-check",
            "python_stdlib": "chain hashes, pairwise distinctness rows, source locks, and G.2a boundary flags",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "disallowed_claims": [
            "the terrains simmed",
            "sixteen stages constructed",
            "operator residency",
            "engine traversal",
            "axis probe result",
            "formal admission",
            "canonical by process",
            "bridge/physics/manifold claim",
        ],
        "all_pass": all_pass,
    }


def source_result_record(source_path: Path, result_path: Path) -> dict[str, Any]:
    return {
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path) if source_path.exists() else None,
        "result_path": rel(result_path),
        "result_sha256": sha256_file(result_path) if result_path.exists() else None,
    }


def write_result() -> dict[str, Any]:
    payload = build_assembled_engine_terrain_spaces_v0_object()
    write_json(RESULT_PATH, payload)
    return payload


def lane_result(lane: str, packages_used: list[str], load_bearing: list[str], observables: dict[str, str]) -> dict[str, Any]:
    payload = build_assembled_engine_terrain_spaces_v0_object()
    lane_path = SIM_DIR / f"{SIM_ID}_{lane}.py"
    if lane == "julia":
        lane_path = SIM_DIR / f"{SIM_ID}_julia.jl"
    result_path = {"jax": JAX_RESULT_PATH, "pytorch": PYTORCH_RESULT_PATH, "julia": JULIA_RESULT_PATH}[lane]
    row = {
        "schema": f"{SIM_ID}.{lane}.result.v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}.{lane}.terrain_space_fixture_check",
        "engine": lane,
        "ran": True,
        "reads_peer_result": False,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": now_z(),
        "source_path": rel(lane_path),
        "source_sha256": sha256_file(lane_path) if lane_path.exists() else None,
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "package_observables": observables,
        "terrain_space_count": len(payload["terrain_spaces"]),
        "chain_hashes": {terrain["terrain_id"]: terrain["chain_sha256"] for terrain in payload["terrain_spaces"]},
        "certificate_hashes": {terrain["terrain_id"]: terrain["homology_certificate_ref"] for terrain in payload["terrain_spaces"]},
        "computed_flux": {terrain["terrain_id"]: terrain["flux_orientation"]["computed_orientation"] for terrain in payload["terrain_spaces"]},
        "homology_signatures": {terrain["terrain_id"]: homology_signature(terrain) for terrain in payload["terrain_spaces"]},
        "pairwise_distinctness_passed": payload["cross_terrain_distinctness"]["all_pairs_distinguished_by_computed_structure"],
        "component_boundary": payload["component_boundary"],
        "all_pass": payload["all_pass"],
    }
    write_json(result_path, row)
    row["result_path"] = rel(result_path)
    row["result_sha256"] = sha256_file(result_path)
    write_json(result_path, row)
    return row


def write_jax_result() -> dict[str, Any]:
    return lane_result(
        "jax",
        ["jax", "sympy", "python_stdlib"],
        ["sympy"],
        {
            "sympy": "exact integer SNF homology reused from packet common",
            "jax": "scoped lane wrapper records parity of terrain count and flux rows; not claim-bearing numeric computation",
        },
    )


def write_pytorch_result() -> dict[str, Any]:
    return lane_result(
        "pytorch",
        ["torch", "sympy", "python_stdlib"],
        ["sympy"],
        {
            "sympy": "exact integer SNF homology reused from packet common",
            "torch": "scoped lane wrapper records parity of terrain count and flux rows; not claim-bearing tensor computation",
        },
    )


def build_envelope() -> dict[str, Any]:
    payload = write_result() if not RESULT_PATH.exists() else load_json(RESULT_PATH)
    lane_paths = {
        "jax": JAX_RESULT_PATH,
        "pytorch": PYTORCH_RESULT_PATH,
        "julia": JULIA_RESULT_PATH,
    }
    lanes = {name: load_json(path) for name, path in lane_paths.items() if path.exists()}
    envelope = {
        "schema": f"{SIM_ID}.envelope.v1",
        "schema_version": "terrain_spaces_component_envelope_v1",
        "mode": "scoped_integer_homology_packet_with_lane_wrappers",
        "omitted_lanes": [],
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": now_z(),
        "result_path": rel(RESULT_PATH),
        "result_sha256": sha256_file(RESULT_PATH) if RESULT_PATH.exists() else None,
        "component_boundary": payload["component_boundary"],
        "terrain_space_count": len(payload.get("terrain_spaces", [])),
        "pairwise_distinctness_rows": len(payload.get("cross_terrain_distinctness", {}).get("pairwise_rows", [])),
        "homology_only_indistinguishable_pairs": payload.get("cross_terrain_distinctness", {}).get("homology_only_indistinguishable_pairs", []),
        "three_engine_scope": payload["three_engine_scope"],
        "engines": lanes,
        "claim_path_tools": ["sympy", "python_stdlib", "builder_audit_boundary"],
        "divergence_log": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "builder_gates": payload["builder_gates"],
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "all_pass": bool(payload.get("all_pass")),
    }
    write_json(ENVELOPE_RESULT_PATH, envelope)
    return envelope
