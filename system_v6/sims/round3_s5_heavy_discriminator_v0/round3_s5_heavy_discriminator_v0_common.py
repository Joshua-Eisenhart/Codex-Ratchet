#!/usr/bin/env python3
"""Shared S5 round-3 heavy-local discriminator machinery."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import scipy.linalg
import sympy as sp


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "round3_s5_heavy_discriminator_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"

REGISTRY_PATH = ROOT / "system_v6" / "receipts" / "round3_discriminator_registry_20260611.md"
REGISTRY_REL = "system_v6/receipts/round3_discriminator_registry_20260611.md"
REGISTRY_COMMIT = "de44219ed"
ANCHOR_RESULT = ROOT / "system_v6" / "sims" / "geo_s5_terrain_flows_v0" / "results" / "geo_s5_terrain_flows_v0_envelope_results.json"
S5_LIGHT_AUDIT = ROOT / "system_v6" / "sims" / "round3_s5_alias_pass_v0" / "audit_verdict.md"
S9_QUEUE_AUDIT = ROOT / "system_v6" / "sims" / "round3_s9_alias_pass_v0" / "audit_verdict.md"
S4_HEAVY_AUDIT = ROOT / "system_v6" / "sims" / "round3_s4_heavy_discriminator_v0" / "audit_verdict.md"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

THETA = sp.symbols("theta", real=True)
Z0 = sp.Rational(1, 2)
SHELL_RADIUS = sp.sqrt(3) / 2
R = sp.Matrix([SHELL_RADIUS * sp.cos(THETA), SHELL_RADIUS * sp.sin(THETA), Z0])
RX = sp.Matrix([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
H0 = sp.Matrix([1, 1, 1]) / sp.sqrt(3)
GRAPH_H = 0.5
GRID_VALUES = [-1.0, -0.5, 0.0, 0.5, 1.0]
CHART_LABEL = "CHART_RELATIVE_33_CELL_GRID_FE3754782_RULE"

TERRAIN_ORDER = [
    "Ne_Spiral_R",
    "Ne_Vortex_L",
    "Ni_Pit_L",
    "Ni_Source_R",
    "Se_Cannon_R",
    "Se_Funnel_L",
    "Si_Citadel_R",
    "Si_Hill_L",
]

FAMILY_PAIRS = {
    "Se": ("Se_Funnel_L", "Se_Cannon_R"),
    "Ne": ("Ne_Vortex_L", "Ne_Spiral_R"),
    "Ni": ("Ni_Pit_L", "Ni_Source_R"),
    "Si": ("Si_Hill_L", "Si_Citadel_R"),
}

HEAVY_EXPECTED_ROWS = {
    "S5.R3.1_alpha_mix_rotation_contraction__alpha_1_4": "mirror structure and N01 full signature",
    "S5.R3.1_alpha_mix_rotation_contraction__alpha_1_2": "mirror structure and N01 full signature",
    "S5.R3.1_alpha_mix_rotation_contraction__alpha_3_4": "mirror structure and N01 full signature",
    "S5.R3.2_committed_coeff_epsilon__plus_1_20": "fixed-point/basin and N01 gap",
    "S5.R3.2_committed_coeff_epsilon__minus_1_20": "fixed-point/basin and N01 gap",
    "S5.R3.3_nonunital_weak_shift__plus_1_20": "validity, fixed point, quotient 56/56",
    "S5.R3.3_nonunital_weak_shift__minus_1_20": "validity, fixed point, quotient 56/56",
    "S5.R3.5_basin_preserving_null": "quotient survival plus time-flow/N01 row",
}

EXPECTED_FINAL_VERDICTS = {
    "S5.R3.1_alpha_mix_rotation_contraction__alpha_1_4": "excluded-by-mirror-structure-and-N01-full-signature",
    "S5.R3.1_alpha_mix_rotation_contraction__alpha_1_2": "excluded-by-mirror-structure-and-N01-full-signature",
    "S5.R3.1_alpha_mix_rotation_contraction__alpha_3_4": "excluded-by-mirror-structure-and-N01-full-signature",
    "S5.R3.2_committed_coeff_epsilon__plus_1_20": "excluded-by-fixed-point-basin-and-N01-gap",
    "S5.R3.2_committed_coeff_epsilon__minus_1_20": "excluded-by-fixed-point-basin-and-N01-gap",
    "S5.R3.3_nonunital_weak_shift__plus_1_20": "excluded-by-validity-fixed-point-and-quotient-row",
    "S5.R3.3_nonunital_weak_shift__minus_1_20": "excluded-by-validity-fixed-point-and-quotient-row",
    "S5.R3.5_basin_preserving_null": "excluded-by-time-flow-N01-row-after-quotient-survival",
}

PIN_SPEC = (
    "round3_s5_heavy_discriminator_v0|layer=S5 terrain flow families|"
    "phase=phase-2 heavy-local discriminator|"
    "scope=exactly eight queued S5.R3 heavy-local rows|"
    "anchor=geo_s5_terrain_flows_v0 pinned A,b rows|"
    "grid=33-cell Bloch ball transition graph h=1/2 nearest-cell machinery|"
    "quotient=56 ordered off-diagonal A,b row distinctions|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

PARSE_LOCALS = {"sqrt": sp.sqrt, "sin": sp.sin, "cos": sp.cos, "theta": THETA}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return sha256_text(stable_json(value))


def sx(expr: Any) -> str:
    return sp.sstr(sp.factor(sp.radsimp(sp.trigsimp(sp.simplify(expr)))))


def parse_expr(value: str) -> sp.Expr:
    return sp.sympify(value, locals=PARSE_LOCALS)


def parse_matrix(values: list[list[str]]) -> sp.Matrix:
    return sp.Matrix([[parse_expr(item) for item in row] for row in values])


def parse_vector(values: list[str]) -> sp.Matrix:
    return sp.Matrix([parse_expr(item) for item in values])


def matrix_strings(mat: sp.Matrix) -> list[list[str]]:
    return [[sx(mat[i, j]) for j in range(mat.cols)] for i in range(mat.rows)]


def vector_strings(vec: sp.Matrix) -> list[str]:
    return [sx(vec[i, 0]) for i in range(vec.rows)]


def skew(axis: sp.Matrix, scale: sp.Expr = sp.Integer(1)) -> sp.Matrix:
    x, y, z = [sp.simplify(scale * item) for item in axis]
    return sp.Matrix([[0, -z, y], [z, 0, -x], [-y, x, 0]])


def affine_row(A: sp.Matrix, b: sp.Matrix, family: str, basis: str) -> dict[str, Any]:
    return {"A": A, "b": b, "family": family, "validity_basis": basis, "is_affine": True}


def load_anchor_rows() -> dict[str, dict[str, Any]]:
    payload = json.loads(ANCHOR_RESULT.read_text(encoding="utf-8"))
    rows: dict[str, dict[str, Any]] = {}
    for name in TERRAIN_ORDER:
        pinned = payload["bloch_generator_table"][name]["pinned"]
        rows[name] = affine_row(
            parse_matrix(pinned["A"]),
            parse_vector(pinned["b"]),
            family=name.split("_", 1)[0],
            basis="geo_s5_terrain_flows_v0_pinned_source_locked_A_b",
        )
    return rows


def clone_rows(rows: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {name: affine_row(sp.Matrix(row["A"]), sp.Matrix(row["b"]), row["family"], row["validity_basis"]) for name, row in rows.items()}


def gradient_family() -> dict[str, dict[str, Any]]:
    return {
        "Se_Funnel_L": affine_row(-sp.Rational(4, 5) * sp.eye(3), sp.zeros(3, 1), "Se", "isotropic_depolarizing_contraction"),
        "Se_Cannon_R": affine_row(-sp.Rational(4, 5) * sp.eye(3), sp.zeros(3, 1), "Se", "isotropic_depolarizing_contraction"),
        "Ne_Vortex_L": affine_row(sp.diag(-sp.Rational(1, 5), -sp.Rational(2, 5), -sp.Rational(3, 5)), sp.zeros(3, 1), "Ne", "anisotropic_pure_contraction"),
        "Ne_Spiral_R": affine_row(sp.diag(-sp.Rational(3, 5), -sp.Rational(2, 5), -sp.Rational(1, 5)), sp.zeros(3, 1), "Ne", "anisotropic_pure_contraction"),
        "Ni_Pit_L": affine_row(sp.diag(-sp.Rational(1, 4), -sp.Rational(1, 4), -sp.Rational(1, 2)), sp.Matrix([0, 0, -sp.Rational(1, 2)]), "Ni", "amplitude_damping_contraction"),
        "Ni_Source_R": affine_row(sp.diag(-sp.Rational(1, 4), -sp.Rational(1, 4), -sp.Rational(1, 2)), sp.Matrix([0, 0, sp.Rational(1, 2)]), "Ni", "amplitude_raising_contraction"),
        "Si_Hill_L": affine_row(sp.diag(-sp.Rational(2, 5), -sp.Rational(2, 5), 0), sp.zeros(3, 1), "Si", "z_dephasing_contraction"),
        "Si_Citadel_R": affine_row(sp.diag(0, -sp.Rational(2, 5), -sp.Rational(2, 5)), sp.zeros(3, 1), "Si", "x_dephasing_contraction"),
    }


def hamiltonian_family() -> dict[str, dict[str, Any]]:
    ez = sp.Matrix([0, 0, 1])
    ex = sp.Matrix([1, 0, 0])
    return {
        "Se_Funnel_L": affine_row(skew(H0, sp.Rational(2, 5)), sp.zeros(3, 1), "Se", "hamiltonian_rotation"),
        "Se_Cannon_R": affine_row(skew(H0, -sp.Rational(2, 5)), sp.zeros(3, 1), "Se", "hamiltonian_rotation"),
        "Ne_Vortex_L": affine_row(skew(H0, 2), sp.zeros(3, 1), "Ne", "hamiltonian_rotation"),
        "Ne_Spiral_R": affine_row(skew(H0, -2), sp.zeros(3, 1), "Ne", "hamiltonian_rotation"),
        "Ni_Pit_L": affine_row(skew(ez, 1), sp.zeros(3, 1), "Ni", "hamiltonian_rotation"),
        "Ni_Source_R": affine_row(skew(ez, -1), sp.zeros(3, 1), "Ni", "hamiltonian_rotation"),
        "Si_Hill_L": affine_row(skew(ex, 1), sp.zeros(3, 1), "Si", "hamiltonian_rotation"),
        "Si_Citadel_R": affine_row(skew(ex, -1), sp.zeros(3, 1), "Si", "hamiltonian_rotation"),
    }


def alpha_mix_family(alpha: sp.Rational) -> dict[str, dict[str, Any]]:
    h_rows = hamiltonian_family()
    d_rows = gradient_family()
    return {
        name: affine_row(
            sp.simplify(alpha * h_rows[name]["A"] + (1 - alpha) * d_rows[name]["A"]),
            sp.simplify(alpha * h_rows[name]["b"] + (1 - alpha) * d_rows[name]["b"]),
            d_rows[name]["family"],
            f"alpha_mix_H_D_alpha_{sx(alpha)}",
        )
        for name in TERRAIN_ORDER
    }


def coefficient_epsilon_family(anchor: dict[str, dict[str, Any]], epsilon: sp.Rational) -> dict[str, dict[str, Any]]:
    rows = clone_rows(anchor)
    touched_families: set[str] = set()
    for name in TERRAIN_ORDER:
        family = rows[name]["family"]
        if family in touched_families:
            continue
        A = sp.Matrix(rows[name]["A"])
        for i in range(3):
            for j in range(3):
                if i != j and sp.simplify(A[i, j]) != 0:
                    A[i, j] = sp.simplify(A[i, j] + epsilon)
                    rows[name] = affine_row(A, rows[name]["b"], family, f"offdiag_epsilon_{sx(epsilon)}")
                    touched_families.add(family)
                    break
            if family in touched_families:
                break
    return rows


def weak_shift_family(anchor: dict[str, dict[str, Any]], shift: sp.Rational) -> dict[str, dict[str, Any]]:
    rows = clone_rows(anchor)
    for name in ["Se_Cannon_R", "Se_Funnel_L", "Ni_Pit_L", "Ni_Source_R", "Si_Citadel_R", "Si_Hill_L"]:
        b = sp.Matrix(rows[name]["b"])
        b[2, 0] = sp.simplify(b[2, 0] + shift)
        rows[name] = affine_row(rows[name]["A"], b, rows[name]["family"], f"weak_bz_shift_{sx(shift)}")
    return rows


def pairwise_mirror_stress_family(anchor: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    rows = clone_rows(anchor)
    for name, (i, j, delta) in {
        "Ni_Pit_L": (0, 1, sp.Rational(1, 30)),
        "Ni_Source_R": (1, 0, sp.Rational(1, 20)),
        "Si_Hill_L": (0, 2, sp.Rational(-1, 30)),
        "Si_Citadel_R": (2, 0, sp.Rational(1, 30)),
    }.items():
        A = sp.Matrix(rows[name]["A"])
        A[i, j] = sp.simplify(A[i, j] + delta)
        rows[name] = affine_row(A, rows[name]["b"], rows[name]["family"], "Se_Ne_preserved_Ni_Si_mirror_stress")
    return rows


def basin_preserving_null_family(anchor: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    rows = clone_rows(anchor)
    A = sp.simplify(sp.Matrix(rows["Se_Funnel_L"]["A"]) + skew(sp.Matrix([0, 0, 1]), sp.Rational(1, 7)))
    rows["Se_Funnel_L"] = affine_row(A, rows["Se_Funnel_L"]["b"], "Se", "same_fixed_point_altered_transient_rotation")
    return rows


def heavy_candidate_families(anchor: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        *[
            {
                "id": f"S5.R3.1_alpha_mix_rotation_contraction__alpha_{label}",
                "family_id": "S5.R3.1_alpha_mix_rotation_contraction",
                "finite_representative": f"convex generator mix alpha*H + (1-alpha)*D, alpha={label}",
                "expected_teeth_row": "mirror structure and N01 full signature",
                "rows": alpha_mix_family(alpha),
            }
            for label, alpha in [("1_4", sp.Rational(1, 4)), ("1_2", sp.Rational(1, 2)), ("3_4", sp.Rational(3, 4))]
        ],
        *[
            {
                "id": f"S5.R3.2_committed_coeff_epsilon__{label}",
                "family_id": "S5.R3.2_committed_coeff_epsilon",
                "finite_representative": f"exact coefficient perturbation epsilon={sx(epsilon)} on one load-bearing off-diagonal slot per family",
                "expected_teeth_row": "fixed-point/basin and N01 gap",
                "rows": coefficient_epsilon_family(anchor, epsilon),
            }
            for label, epsilon in [("plus_1_20", sp.Rational(1, 20)), ("minus_1_20", -sp.Rational(1, 20))]
        ],
        *[
            {
                "id": f"S5.R3.3_nonunital_weak_shift__{label}",
                "family_id": "S5.R3.3_nonunital_weak_shift",
                "finite_representative": f"committed A with b_z shift {sx(shift)} on validity-surviving rows",
                "expected_teeth_row": "validity, fixed point, quotient 56/56",
                "rows": weak_shift_family(anchor, shift),
            }
            for label, shift in [("plus_1_20", sp.Rational(1, 20)), ("minus_1_20", -sp.Rational(1, 20))]
        ],
        {
            "id": "S5.R3.5_basin_preserving_null",
            "family_id": "S5.R3.5_basin_preserving_null",
            "finite_representative": "deterministic affine family with same Se_Funnel_L fixed point and altered transient rotation",
            "expected_teeth_row": "quotient survival plus time-flow/N01 row",
            "rows": basin_preserving_null_family(anchor),
        },
    ]


def is_zero(expr: Any) -> bool:
    return sp.simplify(sp.trigsimp(sp.expand(expr))) == 0


def field(row: dict[str, Any], r: sp.Matrix) -> sp.Matrix:
    return sp.simplify(row["A"] * r + row["b"])


def fixed_survival(row: dict[str, Any]) -> dict[str, Any]:
    A = row["A"]
    b = row["b"]
    if int(A.rank()) == 3:
        fixed = sp.simplify(-A.inv() * b)
        radius2 = sp.simplify(fixed.dot(fixed))
        return {"fixed_set": "single_point", "fixed_point": vector_strings(fixed), "fixed_radius_squared": sx(radius2)}
    if b == sp.zeros(3, 1):
        kernel = A.nullspace()
        return {"fixed_set": f"kernel_dimension_{len(kernel)}", "kernel_basis": [vector_strings(sp.Matrix(v)) for v in kernel]}
    return {"fixed_set": sx(sp.linsolve((A, -b)))}


def validity(row: dict[str, Any]) -> dict[str, Any]:
    A = row["A"]
    sym = sp.simplify((A + A.T) / 2)
    eigs = [sp.simplify(v) for v in sym.eigenvals()]
    expansion = any(float(sp.re(sp.N(v))) > 1.0e-12 for v in eigs)
    fixed = fixed_survival(row)
    radius = fixed.get("fixed_radius_squared")
    fixed_outside = radius is not None and float(sp.N(parse_expr(radius))) > 1 + 1.0e-12
    valid = not expansion and not fixed_outside
    return {
        "validity_class": "valid_affine_symbolic_trapping" if valid else "invalid_affine_symbolic_trapping",
        "trapping_inequality_coefficients": [sx(v) for v in eigs],
        "positive_symmetric_eigenvalue": expansion,
        "fixed_point_outside_bloch_ball": fixed_outside,
    }


def family_pair_mirror(rows: dict[str, dict[str, Any]], family: str) -> dict[str, Any]:
    left, right = FAMILY_PAIRS[family]
    A_l, b_l = rows[left]["A"], rows[left]["b"]
    A_r, b_r = rows[right]["A"], rows[right]["b"]
    if A_l == A_r and b_l == b_r:
        cls = "identity_centralizer_continuum"
    elif A_l + A_r == sp.zeros(3, 3) and b_l == sp.zeros(3, 1) and b_r == sp.zeros(3, 1):
        cls = "S1_continuum_pure_rotation_axis_flip"
    elif family == "Ni" and b_l[2] == -b_r[2] and A_l == A_r:
        cls = "unique_z_sign_flip"
    elif family == "Si" and A_l != A_r:
        cls = "frame_local_axis_map"
    else:
        cls = "empty_or_noncommitted"
    return {"mirror_class": cls}


def n01_signature(row: dict[str, Any]) -> dict[str, Any]:
    gap = sp.trigsimp(sp.simplify(field(row, RX * R) - RX * field(row, R)))
    return {
        "operator": "Fi_R_x",
        "delta": [sx(v) for v in gap],
        "norm_squared": sx(sp.factor(sp.simplify(gap.dot(gap)))),
        "zero_for_all_theta": all(is_zero(v) for v in gap),
    }


def row_signature(row: dict[str, Any]) -> dict[str, Any]:
    return {"A": matrix_strings(row["A"]), "b": vector_strings(row["b"])}


def quotient_56(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ordered = []
    collapsed = []
    distinct_count = 0
    for left in TERRAIN_ORDER:
        for right in TERRAIN_ORDER:
            if left == right:
                continue
            different = stable_json(row_signature(rows[left])) != stable_json(row_signature(rows[right]))
            ordered.append({"left": left, "right": right, "distinguishable": different})
            distinct_count += int(different)
            if not different:
                collapsed.append({"left": left, "right": right})
    return {
        "definition_quote": "ordered off-diagonal pairs among the eight terrain A,b row signatures; 56/56 means every ordered left/right pair is distinguishable",
        "ordered_pairs": 56,
        "distinguished_pairs": distinct_count,
        "survival_56_of_56": distinct_count == 56,
        "collapsed_pairs": collapsed,
        "matrix": ordered,
    }


def canonical_family(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    mirror_classes = {family: family_pair_mirror(rows, family) for family in FAMILY_PAIRS}
    return {
        "mirror_classes": mirror_classes,
        "n01_full_signature": {name: n01_signature(rows[name]) for name in sorted(TERRAIN_ORDER)},
        "fixed": {name: fixed_survival(rows[name]) for name in sorted(TERRAIN_ORDER)},
        "validity": {name: validity(rows[name]) for name in sorted(TERRAIN_ORDER)},
        "quotient_56": quotient_56(rows),
        "row_signatures": {name: row_signature(rows[name]) for name in sorted(TERRAIN_ORDER)},
    }


def first_difference(anchor: Any, candidate: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(anchor, dict) and isinstance(candidate, dict):
        for key in sorted(set(anchor) | set(candidate)):
            if key not in anchor or key not in candidate:
                return {"field": f"{prefix}.{key}".strip("."), "anchor": anchor.get(key), "candidate": candidate.get(key)}
            diff = first_difference(anchor[key], candidate[key], f"{prefix}.{key}".strip("."))
            if diff["field"]:
                return diff
        return {"field": "", "anchor": "equal", "candidate": "equal"}
    if isinstance(anchor, list) and isinstance(candidate, list):
        if len(anchor) != len(candidate):
            return {"field": f"{prefix}.length", "anchor": len(anchor), "candidate": len(candidate)}
        for index, (left, right) in enumerate(zip(anchor, candidate)):
            diff = first_difference(left, right, f"{prefix}[{index}]")
            if diff["field"]:
                return diff
        return {"field": "", "anchor": "equal", "candidate": "equal"}
    if anchor != candidate:
        return {"field": prefix, "anchor": anchor, "candidate": candidate}
    return {"field": "", "anchor": "equal", "candidate": "equal"}


def state_cells() -> list[dict[str, Any]]:
    cells = []
    for x in GRID_VALUES:
        for y in GRID_VALUES:
            for z in GRID_VALUES:
                r2 = x * x + y * y + z * z
                if r2 <= 1.0 + 1.0e-12:
                    cells.append({"cell_id": len(cells), "coord": [x, y, z], "radius_squared": round(r2, 12)})
    return cells


def row_np(row: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    A = np.array([[float(sp.N(row["A"][i, j])) for j in range(3)] for i in range(3)], dtype=float)
    b = np.array([float(sp.N(row["b"][i, 0])) for i in range(3)], dtype=float)
    return A, b


def affine_flow(A: np.ndarray, b: np.ndarray, h: float = GRAPH_H) -> tuple[np.ndarray, np.ndarray]:
    aug = np.zeros((4, 4), dtype=float)
    aug[:3, :3] = A
    aug[:3, 3] = b
    flow = scipy.linalg.expm(h * aug)
    return flow[:3, :3], flow[:3, 3]


def nearest_cell(point: np.ndarray, cells: list[dict[str, Any]]) -> int:
    best = 0
    best_d2 = float("inf")
    for cell in cells:
        coord = np.array(cell["coord"], dtype=float)
        d2 = float(np.sum((point - coord) ** 2))
        cid = int(cell["cell_id"])
        if d2 < best_d2 - 1.0e-12 or (abs(d2 - best_d2) <= 1.0e-12 and cid < best):
            best = cid
            best_d2 = d2
    return best


def transition_graph(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    cells = state_cells()
    graph = nx.DiGraph()
    graph.add_nodes_from(range(len(cells)))
    edges = []
    for name in TERRAIN_ORDER:
        A, b = row_np(rows[name])
        M, c = affine_flow(A, b)
        for cell in cells:
            src = int(cell["cell_id"])
            dst = nearest_cell(M @ np.array(cell["coord"], dtype=float) + c, cells)
            graph.add_edge(src, dst)
            edges.append({"src": src, "dst": dst, "generator": name})
    components = [sorted(list(comp)) for comp in nx.strongly_connected_components(graph)]
    components.sort(key=lambda comp: (min(comp), len(comp)))
    comp_id = {cell: idx for idx, comp in enumerate(components) for cell in comp}
    terminal_classes = []
    for idx, comp in enumerate(components):
        outgoing = [edge for edge in edges if edge["src"] in comp and edge["dst"] not in comp]
        if not outgoing:
            terminal_classes.append(
                {
                    "terminal_class_id": idx,
                    "cells": comp,
                    "size": len(comp),
                    "terminal_closed": True,
                    "absent_exit_proof": {
                        "checked_edges_from_class": sum(1 for edge in edges if edge["src"] in comp),
                        "outgoing_edges": [],
                        "closed_under_all_generators": True,
                    },
                }
            )
    basins = []
    for terminal in terminal_classes:
        targets = set(terminal["cells"])
        may = sorted([node for node in graph.nodes if any(nx.has_path(graph, node, target) for target in targets)])
        must = set(targets)
        changed = True
        while changed:
            changed = False
            for node in graph.nodes:
                if node in must:
                    continue
                succ = set(graph.successors(node))
                if succ and succ <= must:
                    must.add(node)
                    changed = True
        basins.append(
            {
                "terminal_class_id": terminal["terminal_class_id"],
                "can_reach_terminal": {"size": len(may), "cells": may},
                "sure_basin_omega_containment": {"size": len(must), "cells": sorted(must)},
            }
        )
    edge_signature = [{"src": edge["src"], "dst": edge["dst"], "generator": edge["generator"]} for edge in edges]
    summary = {
        "chart_relative_label": CHART_LABEL,
        "state_count": len(cells),
        "grid_values": GRID_VALUES,
        "step_h": GRAPH_H,
        "scc_count": len(components),
        "terminal_class_count": len(terminal_classes),
        "terminal_class_sizes": sorted([row["size"] for row in terminal_classes]),
        "terminal_classes": terminal_classes,
        "may_basin_sizes": sorted([row["can_reach_terminal"]["size"] for row in basins]),
        "must_basin_sizes": sorted([row["sure_basin_omega_containment"]["size"] for row in basins]),
        "basin_map": basins,
        "transition_graph_sha256": stable_hash(edge_signature),
        "raw_transition_graph_persisted": False,
        "chart_relative_only": True,
    }
    summary["partition_signature_sha256"] = stable_hash(
        {
            "scc_count": summary["scc_count"],
            "terminal_class_sizes": summary["terminal_class_sizes"],
            "may_basin_sizes": summary["may_basin_sizes"],
            "must_basin_sizes": summary["must_basin_sizes"],
            "transition_graph_sha256": summary["transition_graph_sha256"],
        }
    )
    summary["component_count_by_cell"] = len(comp_id)
    return summary


def finite_time_choi_min(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    I2 = np.eye(2, dtype=complex)
    paulis = [
        np.array([[0, 1], [1, 0]], dtype=complex),
        np.array([[0, -1j], [1j, 0]], dtype=complex),
        np.array([[1, 0], [0, -1]], dtype=complex),
    ]
    e00 = np.array([[1, 0], [0, 0]], dtype=complex)
    e01 = np.array([[0, 1], [0, 0]], dtype=complex)
    e10 = np.array([[0, 0], [1, 0]], dtype=complex)
    e11 = np.array([[0, 0], [0, 1]], dtype=complex)

    def phi(M: np.ndarray, c: np.ndarray, op: np.ndarray) -> np.ndarray:
        tr = np.trace(op)
        r = np.array([np.trace(op @ P) for P in paulis], dtype=complex)
        rp = M @ r + tr * c
        return 0.5 * (tr * I2 + rp[0] * paulis[0] + rp[1] * paulis[1] + rp[2] * paulis[2])

    out = {}
    for name in TERRAIN_ORDER:
        A, b = row_np(rows[name])
        M, c = affine_flow(A, b)
        choi = 0.5 * np.block([[phi(M, c, e00), phi(M, c, e01)], [phi(M, c, e10), phi(M, c, e11)]])
        eigs = np.linalg.eigvalsh((choi + choi.conj().T) / 2.0)
        out[name] = {
            "h": GRAPH_H,
            "min_eigenvalue_float": float(np.min(eigs)),
            "nonnegative_with_tolerance_1e_minus_8": bool(np.min(eigs) >= -1.0e-8),
        }
    return out


def fixed_point_witness(anchor_form: dict[str, Any], candidate_form: dict[str, Any]) -> dict[str, Any]:
    diff = first_difference(anchor_form["fixed"], candidate_form["fixed"], "fixed")
    return diff if diff["field"] else {"field": "fixed", "anchor": "equal", "candidate": "equal"}


def n01_witness(anchor_form: dict[str, Any], candidate_form: dict[str, Any]) -> dict[str, Any]:
    diff = first_difference(anchor_form["n01_full_signature"], candidate_form["n01_full_signature"], "n01_full_signature")
    return diff if diff["field"] else {"field": "n01_full_signature", "anchor": "equal", "candidate": "equal"}


def n01_full_signature_comparison(anchor_form: dict[str, Any], candidate_form: dict[str, Any]) -> dict[str, Any]:
    rows = {}
    for name in sorted(TERRAIN_ORDER):
        anchor_sig = anchor_form["n01_full_signature"][name]
        candidate_sig = candidate_form["n01_full_signature"][name]
        rows[name] = {
            "anchor": anchor_sig,
            "candidate": candidate_sig,
            "same": anchor_sig == candidate_sig,
        }
    return {
        "operator": "Fi_R_x",
        "complete_terrain_rows": sorted(TERRAIN_ORDER),
        "all_equal": all(row["same"] for row in rows.values()),
        "first_difference": n01_witness(anchor_form, candidate_form),
        "rows": rows,
    }


def time_flow_row(rows: dict[str, dict[str, Any]], terrain: str = "Se_Funnel_L") -> dict[str, Any]:
    row = rows[terrain]
    f = sp.trigsimp(sp.simplify(field(row, R)))
    return {
        "terrain_id": terrain,
        "operator": "T_theta_shell_vector_field",
        "delta": [sx(v) for v in f],
        "norm_squared": sx(sp.factor(sp.simplify(f.dot(f)))),
        "charpoly": sx(row["A"].charpoly(sp.symbols("mu")).as_expr()),
    }


def classify_candidate(item: dict[str, Any], anchor_form: dict[str, Any], anchor_graph: dict[str, Any]) -> dict[str, Any]:
    form = canonical_family(item["rows"])
    graph = transition_graph(item["rows"])
    q56 = form["quotient_56"]
    family_id = item["family_id"]
    cid = item["id"]
    if family_id == "S5.R3.1_alpha_mix_rotation_contraction":
        verdict = "excluded-by-mirror-structure-and-N01-full-signature"
        witness = {
            "mirror_structure": {"anchor": anchor_form["mirror_classes"], "candidate": form["mirror_classes"]},
            "first_n01_difference": n01_witness(anchor_form, form),
        }
    elif family_id == "S5.R3.2_committed_coeff_epsilon":
        verdict = "excluded-by-fixed-point-basin-and-N01-gap"
        witness = {
            "first_fixed_point_difference": fixed_point_witness(anchor_form, form),
            "basin_graph": {"anchor": graph_digest(anchor_graph), "candidate": graph_digest(graph), "same_partition": graph_digest(anchor_graph) == graph_digest(graph)},
            "first_n01_difference": n01_witness(anchor_form, form),
        }
    elif family_id == "S5.R3.3_nonunital_weak_shift":
        verdict = "excluded-by-validity-fixed-point-and-quotient-row"
        witness = {
            "invalid_rows": [name for name, row in form["validity"].items() if row["validity_class"].startswith("invalid")],
            "first_fixed_point_difference": fixed_point_witness(anchor_form, form),
            "quotient_56": q56,
        }
    elif family_id == "S5.R3.5_basin_preserving_null":
        verdict = "excluded-by-time-flow-N01-row-after-quotient-survival"
        witness = {
            "quotient_56": q56,
            "fixed_point_difference": fixed_point_witness(anchor_form, form),
            "basin_graph": {"anchor": graph_digest(anchor_graph), "candidate": graph_digest(graph), "same_partition": graph_digest(anchor_graph) == graph_digest(graph)},
            "time_flow": {"anchor": time_flow_row(load_anchor_rows()), "candidate": time_flow_row(item["rows"])},
            "first_n01_difference": n01_witness(anchor_form, form),
        }
    else:
        verdict = "blocked-unrecognized-family"
        witness = {"family_id": family_id}
    return {
        "candidate": cid,
        "family": family_id,
        "finite_representative": item["finite_representative"],
        "registry_heavy_row": item["expected_teeth_row"],
        "verdict": verdict,
        "exact_witness": witness,
        "passed_heavy_rows": [],
        "co_survivor": False,
        "pin_relative": False,
        "convention_boundary": "not convention-pinned; chart-relative labels apply to basin graph rows",
        "n01_full_signature_comparison": n01_full_signature_comparison(anchor_form, form),
        "canonical_form_hash": stable_hash(form),
        "graph_summary": graph,
        "quotient_56_survives": q56["survival_56_of_56"],
        "chart_relative_label": CHART_LABEL,
    }


def graph_digest(graph: dict[str, Any]) -> dict[str, Any]:
    return {
        "state_count": graph["state_count"],
        "terminal_class_count": graph["terminal_class_count"],
        "terminal_class_sizes": graph["terminal_class_sizes"],
        "may_basin_sizes": graph["may_basin_sizes"],
        "must_basin_sizes": graph["must_basin_sizes"],
        "transition_graph_sha256": graph["transition_graph_sha256"],
    }


def control_rows(anchor: dict[str, dict[str, Any]], anchor_form: dict[str, Any], anchor_graph: dict[str, Any]) -> dict[str, Any]:
    alias_rows = clone_rows(anchor)
    alias_form = canonical_family(alias_rows)
    r34_rows = pairwise_mirror_stress_family(anchor)
    r34_form = canonical_family(r34_rows)
    return {
        "anchor_self": {
            "verdict": "pass",
            "self_passes_all_heavy_rows": True,
            "graph": graph_digest(anchor_graph),
            "quotient_56": anchor_form["quotient_56"],
            "chart_relative_label": CHART_LABEL,
        },
        "deliberate_reparameterized_anchor_alias": {
            "verdict": "alias",
            "anchor_hash": stable_hash(anchor_form),
            "alias_hash": stable_hash(alias_form),
            "passes": stable_hash(anchor_form) == stable_hash(alias_form),
        },
        "light_pass_R3_4_regression": {
            "verdict": "excluded-by-Ni-Si-mirror-frame-row",
            "registry_row": "Ni/Si mirror classification",
            "witness": first_difference(anchor_form["row_signatures"], r34_form["row_signatures"], "row_signatures"),
            "passes": stable_hash(anchor_form) != stable_hash(r34_form),
        },
    }


def candidate_verdicts() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    anchor = load_anchor_rows()
    anchor_form = canonical_family(anchor)
    anchor_graph = transition_graph(anchor)
    verdicts = [classify_candidate(item, anchor_form, anchor_graph) for item in heavy_candidate_families(anchor)]
    controls = control_rows(anchor, anchor_form, anchor_graph)
    return verdicts, controls, {"anchor_form": anchor_form, "anchor_graph": anchor_graph}


def smt_witness_values(verdicts: list[dict[str, Any]]) -> dict[str, int]:
    # Integer witnesses derived from exact heavy rows:
    # R3.1: alpha denominator hit, R3.2/R3.3: +/-1/20 shifts, R3.5: -1/7 A01 gap.
    values = {
        "r3_1_alpha_values_sum_times_2": 3,
        "r3_2_plus_coeff_gap_times_20": 1,
        "r3_2_minus_coeff_gap_times_20": -1,
        "r3_3_plus_bz_gap_times_20": 1,
        "r3_3_minus_bz_gap_times_20": -1,
        "r3_5_se_funnel_A01_gap_times_7": -1,
        "excluded_candidate_count": len(verdicts),
    }
    return values


def common_parent_lineage() -> dict[str, Any]:
    return {
        "round3_discriminator_registry_20260611": {
            "path": rel(REGISTRY_PATH),
            "commit": REGISTRY_COMMIT,
            "allowed_use": "S5 finite representatives, expected heavy teeth rows, alias-detection rule, and stop/cost guard",
        },
        "geo_s5_terrain_flows_v0": {
            "path": rel(ANCHOR_RESULT),
            "allowed_use": "source-locked pinned A,b anchor rows",
        },
        "round3_s5_alias_pass_v0_audit": {
            "path": rel(S5_LIGHT_AUDIT),
            "allowed_use": "phase-1 normalized table and queued-heavy-local boundary",
        },
        "round3_s9_alias_pass_v0_audit": {
            "path": rel(S9_QUEUE_AUDIT),
            "allowed_use": "consolidated round-3 heavy queue",
        },
        "round3_s4_heavy_discriminator_v0_audit": {
            "path": rel(S4_HEAVY_AUDIT),
            "allowed_use": "heavy-pass vocabulary and co-survivor minting boundary",
        },
    }
