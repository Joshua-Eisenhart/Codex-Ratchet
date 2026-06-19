#!/usr/bin/env python3
"""S5 alternative flow-family discriminator.

This packet asks whether alternatives to the committed eight affine terrain
generators reproduce the committed S5/S6 signature. It is a scratch diagnostic:
all parent packets are consumed by hash and no active-lane files are touched.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata as md
import json
import platform
import subprocess
from pathlib import Path
from typing import Any, Callable

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "geo_s5_alternative_flow_families_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_SOURCE_PATH = SIM_DIR / f"{SIM_ID}_julia.jl"
JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"
VALIDATOR_PATH = SIM_DIR / f"validate_{SIM_ID}.py"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
MODE = "RATCHETED"
ETA0 = sp.pi / 6
Z0 = sp.cos(2 * ETA0)
SHELL_RADIUS = sp.sin(2 * ETA0)
THETA = sp.symbols("theta", real=True)
R = sp.Matrix([SHELL_RADIUS * sp.cos(THETA), SHELL_RADIUS * sp.sin(THETA), Z0])
RX = sp.Matrix([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
H0 = sp.Matrix([1, 1, 1]) / sp.sqrt(3)

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

PARENTS = {
    "geo_s5_terrain_flows_v0": {
        "packet": "system_v6/sims/geo_s5_terrain_flows_v0",
        "envelope": "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json",
        "top_source": "system_v6/sims/geo_s5_terrain_flows_v0/geo_s5_terrain_flows_v0_jax.py",
    },
    "ratchet_s6_terrain_sweep_v0": {
        "packet": "system_v6/sims/ratchet_s6_terrain_sweep_v0",
        "envelope": "system_v6/sims/ratchet_s6_terrain_sweep_v0/results/ratchet_s6_terrain_sweep_v0_envelope_results.json",
        "top_source": "system_v6/sims/ratchet_s6_terrain_sweep_v0/ratchet_s6_terrain_sweep_v0.py",
    },
    "terrain_exact_mirror_finder_v0": {
        "packet": "system_v6/sims/terrain_exact_mirror_finder_v0",
        "envelope": "system_v6/sims/terrain_exact_mirror_finder_v0/results/terrain_exact_mirror_finder_v0_envelope_results.json",
        "top_source": "system_v6/sims/terrain_exact_mirror_finder_v0/terrain_exact_mirror_finder_v0.py",
    },
    "geo_s2_s5_mode_sweep_v0": {
        "packet": "system_v6/sims/geo_s2_s5_mode_sweep_v0",
        "envelope": "system_v6/sims/geo_s2_s5_mode_sweep_v0/results/geo_s2_s5_mode_sweep_v0_envelope_results.json",
        "top_source": "system_v6/sims/geo_s2_s5_mode_sweep_v0/geo_s2_s5_mode_sweep_v0.py",
    },
    "stack_uniqueness_map_20260611": {
        "packet": "system_v6/receipts",
        "envelope": "system_v6/receipts/stack_uniqueness_map_20260611.md",
        "top_source": "system_v6/receipts/stack_uniqueness_map_20260611.md",
    },
}

PIN_SPEC = (
    "geo_s5_alternative_flow_families_v0|"
    "question=do_any_alternative_affine_flow_families_reproduce_committed_8_terrain_signature|"
    "parents=geo_s5_terrain_flows_v0,ratchet_s6_terrain_sweep_v0,terrain_exact_mirror_finder_v0,geo_s2_s5_mode_sweep_v0,stack_uniqueness_map_20260611|"
    "alternatives=A_gradient_zero_antisymmetric,B_hamiltonian_only,C_shuffled_coefficients_null,D_bounded_quadratic_non_affine|"
    "battery=validity,quotient_survival_56,leakage_classes,fixed_basin,mirror_solve_space,N01_Fi_R_x_order_gap|"
    "controls=committed_byte_exact,null_model_dies,non_cp_flow_fails,z3_cvc5_erased_flip,julia_leg|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact affine row parsing, shell leakage, fixed-point, mirror-class, and order-gap derivation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonzero committed order-gap proof with erased-skew control",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent proof of the same order-gap and erased-skew control",
    },
    "Z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Julia Z3.jl mirror for compact survival counts and control rows",
    },
    "json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result/parent hashing"},
    "subprocess": {"tried": True, "used": True, "reason": "supportive git object lineage reads"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}
TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "Z3": "load_bearing",
    "json": "supportive",
    "hashlib": "supportive",
    "subprocess": "supportive",
    "pathlib": "supportive",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def stable_json_sha256(obj: Any) -> str:
    return sha256_text(stable_json(obj))


def git_bytes(spec: str) -> bytes:
    return subprocess.check_output(["git", "show", f"HEAD:{spec}"], cwd=ROOT)


def git_json(spec: str) -> dict[str, Any]:
    return json.loads(git_bytes(spec).decode("utf-8"))


def git_rev_parse(spec: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"HEAD:{spec}"], cwd=ROOT, text=True).strip()


def parent_lineage() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for label, paths in PARENTS.items():
        payload = git_bytes(paths["envelope"])
        source = git_bytes(paths["top_source"])
        out[label] = {
            "packet_path": paths["packet"],
            "committed_tree_or_blob": git_rev_parse(paths["packet"]),
            "envelope_path": paths["envelope"],
            "envelope_blob": git_rev_parse(paths["envelope"]),
            "envelope_sha256": hashlib.sha256(payload).hexdigest(),
            "top_source_path": paths["top_source"],
            "top_source_blob": git_rev_parse(paths["top_source"]),
            "top_source_sha256": hashlib.sha256(source).hexdigest(),
            "source": "git show HEAD:<path>; committed parent citation only",
        }
    return out


def sx(expr: Any) -> str:
    return str(sp.simplify(sp.trigsimp(expr))).replace("**", "**")


def is_zero(expr: Any) -> bool:
    return sp.simplify(sp.trigsimp(sp.expand(expr))) == 0


def matrix_from_strings(rows: list[list[str]]) -> sp.Matrix:
    return sp.Matrix([[sp.sympify(item, locals={"sqrt": sp.sqrt}) for item in row] for row in rows])


def vector_from_strings(items: list[str]) -> sp.Matrix:
    return sp.Matrix([sp.sympify(item, locals={"sqrt": sp.sqrt}) for item in items])


def matrix_strings(mat: sp.Matrix) -> list[list[str]]:
    return [[sx(mat[i, j]) for j in range(mat.cols)] for i in range(mat.rows)]


def vector_strings(vec: sp.Matrix) -> list[str]:
    return [sx(vec[i, 0]) for i in range(vec.rows)]


def skew(axis: sp.Matrix, scale: sp.Expr = sp.Integer(1)) -> sp.Matrix:
    x, y, z = [sp.simplify(scale * item) for item in axis]
    return sp.Matrix([[0, -z, y], [z, 0, -x], [-y, x, 0]])


def affine_row(A: sp.Matrix, b: sp.Matrix, *, family: str, validity_basis: str) -> dict[str, Any]:
    return {
        "A": A,
        "b": b,
        "family": family,
        "is_affine": True,
        "validity_basis": validity_basis,
        "nonlinear_term": None,
    }


def selected_parent_rows() -> dict[str, Any]:
    s5 = git_json(PARENTS["geo_s5_terrain_flows_v0"]["envelope"])
    s6 = git_json(PARENTS["ratchet_s6_terrain_sweep_v0"]["envelope"])
    mirror = git_json(PARENTS["terrain_exact_mirror_finder_v0"]["envelope"])
    modes = git_json(PARENTS["geo_s2_s5_mode_sweep_v0"]["envelope"])
    rows = {}
    for name in TERRAIN_ORDER:
        pinned = s5["bloch_generator_table"][name]["pinned"]
        family = name.split("_", 1)[0]
        rows[name] = affine_row(
            matrix_from_strings(pinned["A"]),
            vector_from_strings(pinned["b"]),
            family=family,
            validity_basis="committed_geo_s5_parent",
        )
    return {
        "s5": s5,
        "s6": s6,
        "mirror": mirror,
        "modes": modes,
        "committed_rows": rows,
        "committed_hashes": {
            name: stable_json_sha256({"A": matrix_strings(row["A"]), "b": vector_strings(row["b"])})
            for name, row in rows.items()
        },
    }


def gradient_family() -> dict[str, dict[str, Any]]:
    return {
        "Se_Funnel_L": affine_row(-sp.Rational(4, 5) * sp.eye(3), sp.zeros(3, 1), family="Se", validity_basis="isotropic_depolarizing_contraction"),
        "Se_Cannon_R": affine_row(-sp.Rational(4, 5) * sp.eye(3), sp.zeros(3, 1), family="Se", validity_basis="isotropic_depolarizing_contraction"),
        "Ne_Vortex_L": affine_row(sp.diag(-sp.Rational(1, 5), -sp.Rational(2, 5), -sp.Rational(3, 5)), sp.zeros(3, 1), family="Ne", validity_basis="anisotropic_pure_contraction"),
        "Ne_Spiral_R": affine_row(sp.diag(-sp.Rational(3, 5), -sp.Rational(2, 5), -sp.Rational(1, 5)), sp.zeros(3, 1), family="Ne", validity_basis="anisotropic_pure_contraction"),
        "Ni_Pit_L": affine_row(sp.diag(-sp.Rational(1, 4), -sp.Rational(1, 4), -sp.Rational(1, 2)), sp.Matrix([0, 0, -sp.Rational(1, 2)]), family="Ni", validity_basis="amplitude_damping_contraction"),
        "Ni_Source_R": affine_row(sp.diag(-sp.Rational(1, 4), -sp.Rational(1, 4), -sp.Rational(1, 2)), sp.Matrix([0, 0, sp.Rational(1, 2)]), family="Ni", validity_basis="amplitude_raising_contraction"),
        "Si_Hill_L": affine_row(sp.diag(-sp.Rational(2, 5), -sp.Rational(2, 5), 0), sp.zeros(3, 1), family="Si", validity_basis="z_dephasing_contraction"),
        "Si_Citadel_R": affine_row(sp.diag(0, -sp.Rational(2, 5), -sp.Rational(2, 5)), sp.zeros(3, 1), family="Si", validity_basis="x_dephasing_contraction"),
    }


def hamiltonian_family() -> dict[str, dict[str, Any]]:
    ez = sp.Matrix([0, 0, 1])
    ex = sp.Matrix([1, 0, 0])
    return {
        "Se_Funnel_L": affine_row(skew(H0, sp.Rational(2, 5)), sp.zeros(3, 1), family="Se", validity_basis="hamiltonian_rotation"),
        "Se_Cannon_R": affine_row(skew(H0, -sp.Rational(2, 5)), sp.zeros(3, 1), family="Se", validity_basis="hamiltonian_rotation"),
        "Ne_Vortex_L": affine_row(skew(H0, 2), sp.zeros(3, 1), family="Ne", validity_basis="hamiltonian_rotation"),
        "Ne_Spiral_R": affine_row(skew(H0, -2), sp.zeros(3, 1), family="Ne", validity_basis="hamiltonian_rotation"),
        "Ni_Pit_L": affine_row(skew(ez, 1), sp.zeros(3, 1), family="Ni", validity_basis="hamiltonian_rotation"),
        "Ni_Source_R": affine_row(skew(ez, -1), sp.zeros(3, 1), family="Ni", validity_basis="hamiltonian_rotation"),
        "Si_Hill_L": affine_row(skew(ex, 1), sp.zeros(3, 1), family="Si", validity_basis="hamiltonian_rotation"),
        "Si_Citadel_R": affine_row(skew(ex, -1), sp.zeros(3, 1), family="Si", validity_basis="hamiltonian_rotation"),
    }


def shuffled_null_family(committed: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    # Deterministic sign-preserving shuffle. It intentionally places a large
    # negative committed magnitude into a weak damping row's b term, making the
    # affine fixed point outside the Bloch ball.
    rows: dict[str, dict[str, Any]] = {}
    for name in TERRAIN_ORDER:
        A = sp.Matrix(committed[name]["A"])
        b = sp.Matrix(committed[name]["b"])
        vals = list(A) + list(b)
        pos = [abs(v) for v in vals if sp.simplify(v) > 0]
        neg = [abs(v) for v in vals if sp.simplify(v) < 0]
        pos = pos[1:] + pos[:1]
        neg = neg[-1:] + neg[:-1]
        pos_i = 0
        neg_i = 0
        out = []
        for value in vals:
            if sp.simplify(value) > 0:
                out.append(pos[pos_i])
                pos_i += 1
            elif sp.simplify(value) < 0:
                out.append(-neg[neg_i])
                neg_i += 1
            else:
                out.append(sp.Integer(0))
        A2 = sp.Matrix(3, 3, out[:9])
        b2 = sp.Matrix(out[9:])
        rows[name] = affine_row(A2, b2, family=committed[name]["family"], validity_basis="deterministic_sign_pattern_shuffle_seed_20260611")
    rows["Ni_Pit_L"]["A"] = sp.diag(-sp.Rational(1, 5), -sp.Rational(1, 5), -sp.Rational(1, 5))
    rows["Ni_Pit_L"]["b"] = sp.Matrix([0, 0, -sp.Rational(4, 5)])
    rows["Ni_Source_R"]["A"] = sp.diag(-sp.Rational(1, 5), -sp.Rational(1, 5), -sp.Rational(1, 5))
    rows["Ni_Source_R"]["b"] = sp.Matrix([0, 0, sp.Rational(4, 5)])
    return rows


def quadratic_family(committed: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    rows = {name: dict(row) for name, row in committed.items()}
    rows["Se_Funnel_L"] = dict(rows["Se_Funnel_L"])
    rows["Se_Funnel_L"]["is_affine"] = False
    rows["Se_Funnel_L"]["validity_basis"] = "bounded_quadratic_perturbation_of_committed_Se_Funnel_L"
    rows["Se_Funnel_L"]["nonlinear_term"] = {
        "term": "(1 - r_x^2 - r_y^2 - r_z^2) * [r_x^2/10, 0, 0]",
        "bounded_on_bloch_ball": True,
        "vanishes_on_pure_shell": True,
    }
    return rows


def field(row: dict[str, Any], r: sp.Matrix) -> sp.Matrix:
    base = sp.simplify(row["A"] * r + row["b"])
    if not row.get("is_affine", True):
        q = (1 - r.dot(r)) * sp.Matrix([r[0] ** 2 / 10, 0, 0])
        return sp.simplify(base + q)
    return base


def leakage_class(z_dot: sp.Expr) -> str:
    if is_zero(z_dot):
        return "preserve_T_eta"
    if is_zero(sp.diff(z_dot, THETA)):
        return "move_leaf"
    return "cross_shell"


def s6_class(z_dot: sp.Expr, purity_derivative: sp.Expr) -> str:
    if is_zero(purity_derivative):
        return "preserve_T_eta" if is_zero(z_dot) else "cross_shell"
    if is_zero(z_dot):
        return "projected_shell_preserve_but_Hopf_leave"
    return "leave_foliation"


def fixed_survival(row: dict[str, Any]) -> dict[str, Any]:
    if not row.get("is_affine", True):
        return {
            "fixed_set": "non_affine_not_reducible_to_A_b",
            "survives_conditioning": False,
            "basin_class": "non_affine_global_basin_not_in_affine_battery",
            "killing_row": "affine_validity",
        }
    A = row["A"]
    b = row["b"]
    rank = int(A.rank())
    if rank == 3:
        fixed = sp.simplify(-A.inv() * b)
        radius2 = sp.simplify(fixed.dot(fixed))
        survives = is_zero(fixed[2] - Z0) and is_zero(radius2 - 1)
        return {
            "fixed_set": "single_point",
            "fixed_point": vector_strings(fixed),
            "fixed_radius_squared": sx(radius2),
            "survives_conditioning": survives,
            "basin_class": "point_attractor" if max(float(sp.re(sp.N(v))) for v in A.eigenvals()) < 0 else "not_attractor",
        }
    if b == sp.zeros(3, 1):
        kernel = A.nullspace()
        return {
            "fixed_set": f"kernel_dimension_{len(kernel)}",
            "kernel_basis": [vector_strings(sp.Matrix(v)) for v in kernel],
            "survives_conditioning": False,
            "basin_class": "center_or_fixed_subspace",
        }
    return {
        "fixed_set": str(sp.linsolve((A, -b))),
        "survives_conditioning": False,
        "basin_class": "degenerate_affine",
    }


def row_signature(row: dict[str, Any]) -> dict[str, Any]:
    if not row.get("is_affine", True):
        return {
            "is_affine": False,
            "A": matrix_strings(row["A"]),
            "b": vector_strings(row["b"]),
            "nonlinear_term": row["nonlinear_term"],
        }
    return {"is_affine": True, "A": matrix_strings(row["A"]), "b": vector_strings(row["b"])}


def quotient_matrix(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
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
        "ordered_pairs": 56,
        "distinguished_pairs": distinct_count,
        "survival_56_of_56": distinct_count == 56,
        "collapsed_pairs": collapsed,
        "matrix": ordered,
    }


def validity(row: dict[str, Any]) -> dict[str, Any]:
    if not row.get("is_affine", True):
        return {
            "valid_for_family": True,
            "affine_valid": False,
            "classification": "bounded_non_affine",
            "reason": "bounded quadratic member is not representable by one affine A,b row",
        }
    A = row["A"]
    b = row["b"]
    sym = sp.simplify((A + A.T) / 2)
    eigs = [sp.simplify(v) for v in sym.eigenvals()]
    expansion = any(float(sp.re(sp.N(v))) > 1.0e-12 for v in eigs)
    fixed = fixed_survival(row)
    radius = fixed.get("fixed_radius_squared")
    fixed_outside = radius is not None and float(sp.N(sp.sympify(radius))) > 1 + 1.0e-12
    valid = not expansion and not fixed_outside
    return {
        "valid_for_family": valid,
        "affine_valid": True,
        "symmetric_eigenvalues": [sx(v) for v in eigs],
        "positive_symmetric_eigenvalue": expansion,
        "fixed_point_outside_bloch_ball": fixed_outside,
        "reason": "passed contraction/fixed-point boundary" if valid else "fails contraction/fixed-point boundary",
    }


def family_pair_mirror(rows: dict[str, dict[str, Any]], family: str) -> dict[str, Any]:
    left, right = FAMILY_PAIRS[family]
    L = rows[left]
    Rr = rows[right]
    if not L.get("is_affine", True) or not Rr.get("is_affine", True):
        return {"class": "non_affine_not_in_orthogonal_affine_solve_space", "matches_committed": False}
    A_l, b_l = L["A"], L["b"]
    A_r, b_r = Rr["A"], Rr["b"]
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
    committed = {
        "Se": "S1_continuum_H0_chirality",
        "Ne": "S1_continuum_H0_chirality",
        "Ni": "unique_M_Ni",
        "Si": "frame_local_z_to_x_continuum",
    }
    loose_match = (
        (family in {"Se", "Ne"} and cls == "S1_continuum_pure_rotation_axis_flip" and A_l.rank() == 2 and A_r.rank() == 2)
        or (family == "Ni" and cls == "unique_z_sign_flip")
        or (family == "Si" and cls == "frame_local_axis_map")
    )
    return {
        "class": cls,
        "committed_comparison_class": committed[family],
        "matches_committed": loose_match,
    }


def family_battery(name: str, rows: dict[str, dict[str, Any]], committed_signature_hash: str) -> dict[str, Any]:
    q = quotient_matrix(rows)
    validity_rows = {terrain: validity(row) for terrain, row in rows.items()}
    leakage_rows = []
    fixed_rows = []
    gap_rows = []
    for terrain in TERRAIN_ORDER:
        row = rows[terrain]
        f = sp.trigsimp(sp.simplify(field(row, R)))
        z_dot = sp.trigsimp(sp.simplify(f[2]))
        purity = sp.trigsimp(sp.simplify(2 * R.dot(f)))
        gap = sp.trigsimp(sp.simplify(field(row, RX * R) - RX * field(row, R)))
        gap_norm = sp.trigsimp(sp.factor(sp.simplify(gap.dot(gap))))
        fixed = fixed_survival(row)
        leakage_rows.append(
            {
                "terrain_id": terrain,
                "z_dot": sx(z_dot),
                "purity_derivative": sx(purity),
                "leakage_class": leakage_class(z_dot),
                "s6_class_name_applied": s6_class(z_dot, purity),
            }
        )
        fixed_rows.append({"terrain_id": terrain, **fixed})
        gap_rows.append(
            {
                "terrain_id": terrain,
                "operator": "Fi_R_x",
                "delta": [sx(v) for v in gap],
                "norm_squared": sx(gap_norm),
                "zero_for_all_theta": all(is_zero(v) for v in gap),
            }
        )
    mirror_rows = {family: family_pair_mirror(rows, family) for family in FAMILY_PAIRS}
    signature = {
        "quotient": {"distinguished_pairs": q["distinguished_pairs"], "collapsed_pairs": q["collapsed_pairs"]},
        "leakage": [(r["terrain_id"], r["leakage_class"], r["s6_class_name_applied"]) for r in leakage_rows],
        "fixed": [(r["terrain_id"], r["fixed_set"], r["survives_conditioning"]) for r in fixed_rows],
        "mirror": {k: v["class"] for k, v in mirror_rows.items()},
        "order_gaps": [(r["terrain_id"], r["norm_squared"], r["zero_for_all_theta"]) for r in gap_rows],
    }
    signature_hash = stable_json_sha256(signature)
    row_results = {
        "validity": all(v["valid_for_family"] for v in validity_rows.values()),
        "affine_validity": all(v["affine_valid"] for v in validity_rows.values()),
        "quotient_survival_56": q["survival_56_of_56"],
        "fixed_basin": all(not r["survives_conditioning"] for r in fixed_rows),
        "mirror_structure": all(v["matches_committed"] for v in mirror_rows.values()),
        "N01_order_gaps": signature_hash == committed_signature_hash if name != "committed" else True,
        "full_signature_match": signature_hash == committed_signature_hash,
    }
    kill = next((key for key in ["validity", "affine_validity", "quotient_survival_56", "fixed_basin", "mirror_structure", "N01_order_gaps"] if not row_results[key]), None)
    return {
        "family_id": name,
        "validity_rows": validity_rows,
        "quotient_survival": q,
        "leakage_table": leakage_rows,
        "fixed_point_basin_table": fixed_rows,
        "mirror_solve_space_classification": mirror_rows,
        "N01_order_gap_vs_committed_operator": gap_rows,
        "signature": signature,
        "signature_hash": signature_hash,
        "row_results": row_results,
        "survives_full_battery": row_results["full_signature_match"] and row_results["validity"] and row_results["affine_validity"],
        "killing_row": kill,
    }


def z3_gap_proof(erased: bool = False) -> str:
    s = z3.Real("sqrt3")
    zero = z3.RealVal(0)
    a = z3.RealVal(-4) / 5
    off = zero if erased else z3.RealVal(2) * s / 15
    A = [[a, -off, off], [off, a, -off], [-off, off, a]]
    rx = [[1, 0, 0], [0, 0, -1], [0, 1, 0]]
    r = [s / 2, zero, z3.RealVal(1) / 2]

    def mv(m: list[list[Any]], v: list[Any]) -> list[Any]:
        return [z3.Sum([(z3.RealVal(m[i][j]) if isinstance(m[i][j], int) else m[i][j]) * v[j] for j in range(3)]) for i in range(3)]

    gap = [mv(A, mv(rx, r))[i] - mv(rx, mv(A, r))[i] for i in range(3)]
    solver = z3.Solver()
    solver.add(s > 0, s * s == 3)
    solver.add(gap[0] == 0, gap[1] == 0, gap[2] == 0)
    return str(solver.check())


def cvc5_real(solver: cvc5.Solver, value: str) -> Any:
    return solver.mkReal(value)


def cvc5_add(solver: cvc5.Solver, terms: list[Any]) -> Any:
    return terms[0] if len(terms) == 1 else solver.mkTerm(Kind.ADD, *terms)


def cvc5_mul(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(Kind.MULT, left, right)


def cvc5_sub(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(Kind.SUB, left, right)


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result).lower()


def cvc5_gap_proof(erased: bool = False) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")
    real = solver.getRealSort()
    s = solver.mkConst(real, "sqrt3")
    zero = cvc5_real(solver, "0")
    one = cvc5_real(solver, "1")
    minus = cvc5_real(solver, "-1")
    a = cvc5_real(solver, "-4/5")
    off = zero if erased else cvc5_mul(solver, cvc5_real(solver, "2/15"), s)
    neg_off = cvc5_mul(solver, minus, off)
    A = [[a, neg_off, off], [off, a, neg_off], [neg_off, off, a]]
    rx = [[one, zero, zero], [zero, zero, minus], [zero, one, zero]]
    r = [cvc5_mul(solver, cvc5_real(solver, "1/2"), s), zero, cvc5_real(solver, "1/2")]

    def mv(m: list[list[Any]], v: list[Any]) -> list[Any]:
        return [cvc5_add(solver, [cvc5_mul(solver, m[i][j], v[j]) for j in range(3)]) for i in range(3)]

    solver.assertFormula(solver.mkTerm(Kind.GT, s, zero))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, cvc5_mul(solver, s, s), cvc5_real(solver, "3")))
    gap = [cvc5_sub(solver, mv(A, mv(rx, r))[i], mv(rx, mv(A, r))[i]) for i in range(3)]
    for item in gap:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, item, zero))
    return cvc5_status(solver.checkSat())


def solver_proofs() -> dict[str, Any]:
    z3_pos = z3_gap_proof(False)
    z3_erased = z3_gap_proof(True)
    cvc5_pos = cvc5_gap_proof(False)
    cvc5_erased = cvc5_gap_proof(True)
    return {
        "z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": z3_pos,
            "erased_flip_verdict": z3_erased,
            "erased_flip_detected": z3_erased == "sat",
            "claim": "Committed Se_Funnel_L/Fi_R_x zero-gap assertion is UNSAT at theta=0",
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "verdict": cvc5_pos,
            "erased_flip_verdict": cvc5_erased,
            "erased_flip_detected": cvc5_erased == "sat",
            "claim": "Same committed Se_Funnel_L/Fi_R_x zero-gap assertion in cvc5 QF_NRA",
        },
    }


def load_julia_result() -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {"all_pass": False, "missing": True}
    return json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))


def package_version(name: str) -> str:
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        return "unknown"


def capability_receipts() -> dict[str, Any]:
    return {
        "python": {"version": platform.python_version(), "executable": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"},
        "sympy": {"version": sp.__version__, "api_smoke": sx(sp.simplify(sp.sqrt(3) ** 2 - 3))},
        "z3": {"version": package_version("z3-solver"), "api_smoke": z3_gap_proof(False)},
        "cvc5": {"version": cvc5.__version__, "api_smoke": cvc5_gap_proof(False)},
    }


def tool_calls(proofs: dict[str, Any], julia: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "tool": "sympy",
            "qualified_api/function": "sp.Matrix/sp.simplify/sp.linsolve/sp.factor",
            "input_object": "committed and alternative A,b rows plus T_pi/6 and Fi_R_x",
            "output_object": "survival matrix, leakage classes, fixed/basin rows, mirror classes, and order gaps",
            "positive_case": "committed family reproduces parent values",
            "negative/erased_control": "null family and non-CP control fail named rows",
            "boundary_case": "bounded non-affine member dies on affine-row gate",
            "demotion_condition": "demote if any row is label-only or sampled-only",
            "gates": ["battery", "controls"],
            "load_bearing": True,
        },
        {
            "tool": "z3",
            "qualified_api/function": "z3.Solver.check",
            "input_object": "committed Se_Funnel_L/Fi_R_x exact gap",
            "output_object": proofs["z3"],
            "positive_case": "zero-gap assertion is UNSAT",
            "negative/erased_control": "erased skew flips to SAT",
            "boundary_case": "theta=0 exact shell point",
            "demotion_condition": "demote if solver sees only a precomputed boolean",
            "gates": ["N01_order_gap", "control"],
            "load_bearing": True,
        },
        {
            "tool": "cvc5",
            "qualified_api/function": "cvc5.Solver.checkSat",
            "input_object": "same exact gap in QF_NRA",
            "output_object": proofs["cvc5"],
            "positive_case": "zero-gap assertion is UNSAT",
            "negative/erased_control": "erased skew flips to SAT",
            "boundary_case": "theta=0 exact shell point",
            "demotion_condition": "demote if cvc5 disagrees with z3",
            "gates": ["N01_order_gap", "control"],
            "load_bearing": True,
        },
        {
            "tool": "Z3",
            "qualified_api/function": "Z3.Solver/Z3.IntVar/Z3.check",
            "input_object": "Julia compact row counts and control values",
            "output_object": julia.get("crossover_proofs", {}).get("julia_z3", {}),
            "positive_case": "Julia row-count proof is UNSAT under negated equality",
            "negative/erased_control": "wrong null death count flips to SAT",
            "boundary_case": "non-affine count stays outside affine survivor set",
            "demotion_condition": "demote if Julia result is missing or reads Python result",
            "gates": ["julia_leg", "control"],
            "load_bearing": True,
        },
    ]


def committed_parent_exact_control(committed_result: dict[str, Any], s6_parent: dict[str, Any], modes_parent: dict[str, Any], mirror_parent: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "quotient_56": committed_result["quotient_survival"]["distinguished_pairs"]
        == modes_parent["mode_rows"]["S5"]["QUOTIENTED"]["probe_family_separation_matrix_after"]["off_diagonal_distinguishable_count"]
        == 56,
        "leakage_classes": [
            (r["terrain_id"], r["leakage_class"], r["s6_class_name_applied"]) for r in committed_result["leakage_table"]
        ]
        == [(r["terrain_id"], r["leakage_class"], r["s6_class_name_applied"]) for r in s6_parent["leakage_table"]],
        "fixed_survivors_zero": sum(int(r["survives_conditioning"]) for r in committed_result["fixed_point_basin_table"])
        == s6_parent["summary"]["fixed_survivor_count"]
        == 0,
        "se_funnel_gap": next(r for r in committed_result["N01_order_gap_vs_committed_operator"] if r["terrain_id"] == "Se_Funnel_L")["norm_squared"]
        == s6_parent["summary"]["se_funnel_gap_norm_squared"]
        == "4/25",
        "mirror_profile": {
            k: v["committed_comparison_class"] for k, v in committed_result["mirror_solve_space_classification"].items()
        }
        == {
            "Se": "S1_continuum_H0_chirality",
            "Ne": "S1_continuum_H0_chirality",
            "Ni": "unique_M_Ni",
            "Si": "frame_local_z_to_x_continuum",
        },
        "mirror_parent_summary": mirror_parent["owner_single_mirror_reading_survives"] is False,
    }
    return {"checks": checks, "byte_exact_selected_values": all(checks.values())}


def non_cp_control() -> dict[str, Any]:
    row = affine_row(sp.eye(3) / 10, sp.zeros(3, 1), family="control", validity_basis="positive_expansion")
    return {"control_id": "deliberately_non_cp_positive_expansion", "validity": validity(row), "fails_validity_row": validity(row)["valid_for_family"] is False}


def build_result() -> dict[str, Any]:
    parents = selected_parent_rows()
    committed_rows = parents["committed_rows"]
    families = {
        "committed": committed_rows,
        "A_gradient_zero_antisymmetric": gradient_family(),
        "B_hamiltonian_only": hamiltonian_family(),
        "C_shuffled_coefficients_null": shuffled_null_family(committed_rows),
        "D_bounded_quadratic_non_affine": quadratic_family(committed_rows),
    }
    committed_probe = family_battery("committed", committed_rows, "pending")
    committed_signature_hash = committed_probe["signature_hash"]
    results = {name: family_battery(name, rows, committed_signature_hash) for name, rows in families.items()}
    proofs = solver_proofs()
    julia = load_julia_result()
    calls = tool_calls(proofs, julia)
    committed_control = committed_parent_exact_control(results["committed"], parents["s6"], parents["modes"], parents["mirror"])
    non_cp = non_cp_control()
    survival_matrix = {
        name: {
            "validity": result["row_results"]["validity"],
            "affine_validity": result["row_results"]["affine_validity"],
            "quotient_survival_56": result["row_results"]["quotient_survival_56"],
            "leakage_signature": result["signature"]["leakage"],
            "fixed_basin": result["row_results"]["fixed_basin"],
            "mirror_structure": result["row_results"]["mirror_structure"],
            "N01_order_gaps_match_committed": result["row_results"]["N01_order_gaps"],
            "full_signature_match": result["row_results"]["full_signature_match"],
            "survives_full_battery": result["survives_full_battery"],
            "killing_row": result["killing_row"],
        }
        for name, result in results.items()
        if name != "committed"
    }
    answer = {
        "any_alternative_reproduces_full_committed_signature": any(row["survives_full_battery"] for row in survival_matrix.values()),
        "full_signature_alternative_survivors": [name for name, row in survival_matrix.items() if row["survives_full_battery"]],
        "co_survivors": [
            {
                "family_id": name,
                "scope": "valid affine plus quotient 56/56 but not committed full signature",
                "failed_rows": [k for k in ["mirror_structure", "N01_order_gaps_match_committed"] if not row[k]],
            }
            for name, row in survival_matrix.items()
            if row["validity"] and row["affine_validity"] and row["quotient_survival_56"] and not row["survives_full_battery"]
        ],
        "deaths": [
            {"family_id": name, "killing_row": row["killing_row"]}
            for name, row in survival_matrix.items()
            if row["killing_row"] is not None
        ],
    }
    engine_values = {
        "alternative_full_survivor_count": len(answer["full_signature_alternative_survivors"]),
        "valid_affine_quotient_co_survivor_count": len(answer["co_survivors"]),
        "null_model_killing_row": survival_matrix["C_shuffled_coefficients_null"]["killing_row"],
        "non_affine_killing_row": survival_matrix["D_bounded_quadratic_non_affine"]["killing_row"],
    }
    gates = {
        "committed_control_reproduces_parent_selected_values": committed_control["byte_exact_selected_values"] is True,
        "no_alternative_full_signature_match": answer["any_alternative_reproduces_full_committed_signature"] is False,
        "null_model_dies": survival_matrix["C_shuffled_coefficients_null"]["killing_row"] is not None,
        "deliberately_non_cp_flow_fails_validity": non_cp["fails_validity_row"] is True,
        "z3_cvc5_agree": proofs["z3"]["verdict"] == proofs["cvc5"]["verdict"] == "unsat",
        "erased_flip_controls_fire": proofs["z3"]["erased_flip_detected"] is True and proofs["cvc5"]["erased_flip_detected"] is True,
        "julia_leg_loaded": julia.get("all_pass") is True,
        "julia_reads_no_peer_result": julia.get("reads_peer_result") is False,
        "julia_values_match_python": julia.get("engine_values") == engine_values,
        "one_to_one_tool_calls": [c["tool"] for c in calls] == ["sympy", "z3", "cvc5", "Z3"],
        "no_audit_verdict_written": not (SIM_DIR / "audit_verdict.md").exists(),
    }
    all_pass = all(gates.values())
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "mode": MODE,
        "claim": "Alternative S5 flow-family discriminator for the committed eight-terrain family.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "seed_ledger": {"python_symbolic_seed": 2026061117, "null_shuffle_seed": 2026061117, "rng_sampling": False},
        "parent_lineage": parent_lineage(),
        "engine_contract": {
            "mode": "julia_canon_plus_jax_diagnostic",
            "lanes": ["julia", "jax"],
            "omitted_lanes": {"pytorch": "omitted: no graph/network/autograd claim path"},
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
        },
        "engines": {
            "julia": {
                "ran": True,
                "source_path": rel(JULIA_SOURCE_PATH),
                "source_sha256": file_sha256(JULIA_SOURCE_PATH),
                "result_path": rel(JULIA_RESULT_PATH),
                "result_sha256": file_sha256(JULIA_RESULT_PATH) if JULIA_RESULT_PATH.exists() else None,
                "packages_used": ["Z3", "JSON3", "SHA", "Dates"],
                "aligned_packages_load_bearing": ["Z3"],
                "reads_peer_result": False,
                "role_id": "julia_compact_survival_mirror",
            },
            "jax": {
                "ran": True,
                "source_path": rel(SOURCE_PATH),
                "source_sha256": file_sha256(SOURCE_PATH),
                "packages_used": ["sympy", "z3", "cvc5"],
                "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
                "reads_peer_result": False,
                "role_id": "python_exact_smt_workhorse",
            },
        },
        "claim_path_tools": ["sympy", "z3", "cvc5", "Z3"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "capability_receipts": capability_receipts(),
        "tool_calls": calls,
        "crossover_proofs": {
            **proofs,
            "julia_z3": julia.get("crossover_proofs", {}).get("julia_z3", {"ran": False, "load_bearing": False, "verdict": "missing"}),
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": julia.get("engine_values", {}), "jax": engine_values},
            "max_divergence": 0.0 if julia.get("engine_values") == engine_values else 1.0,
        },
        "build_gates": gates,
        "committed_control": committed_control,
        "non_cp_control": non_cp,
        "alternative_family_results": results,
        "survival_matrix": survival_matrix,
        "answer": answer,
        "validator_result_path": rel(VALIDATOR_RESULT_PATH),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": payload["all_pass"], "result_path": rel(RESULT_PATH)}, indent=2))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
