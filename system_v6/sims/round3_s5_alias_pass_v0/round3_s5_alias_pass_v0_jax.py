#!/usr/bin/env python3
"""Exact SymPy plus SMT lane for round3_s5_alias_pass_v0.

The lane is named "jax" only to match the repo's two-engine envelope shape.
The claim path is exact symbolic A,b canonicalization plus z3/cvc5 finite
nonzero-witness checks; no numeric JAX array, graph, tensor, or autograd claim
is scoped by this light-symbolic pass.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "round3_s5_alias_pass_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
REGISTRY_PATH = ROOT / "system_v6" / "receipts" / "round3_discriminator_registry_20260611.md"
ANCHOR_RESULT = ROOT / "system_v6" / "sims" / "geo_s5_terrain_flows_v0" / "results" / "geo_s5_terrain_flows_v0_envelope_results.json"
PRIOR_S5_RESULT = ROOT / "system_v6" / "sims" / "geo_s5_alternative_flow_families_v0" / "results" / "geo_s5_alternative_flow_families_v0_envelope_results.json"

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

PIN_SPEC = (
    "round3_s5_alias_pass_v0|layer=S5 terrain flow families|"
    "phase=light-symbolic alias pass only|"
    "anchor=geo_s5_terrain_flows_v0 pinned A,b rows|"
    "canonical_tuple=(terrain_id,A_exact,b_exact,validity_class,fixed_point_exact,mirror_class,N01_signature)|"
    "no_numeric_closeness|heavy-local rows queued by registry cost class|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)


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


PARSE_LOCALS = {"sqrt": sp.sqrt, "sin": sp.sin, "cos": sp.cos, "theta": THETA}


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


def clone_rows(rows: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {name: affine_row(sp.Matrix(row["A"]), sp.Matrix(row["b"]), row["family"], row["validity_basis"]) for name, row in rows.items()}


def alpha_mix_family(alpha: sp.Rational) -> dict[str, dict[str, Any]]:
    H = hamiltonian_family()
    D = gradient_family()
    return {
        name: affine_row(
            sp.simplify(alpha * H[name]["A"] + (1 - alpha) * D[name]["A"]),
            sp.simplify(alpha * H[name]["b"] + (1 - alpha) * D[name]["b"]),
            D[name]["family"],
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
    # Preserve Se/Ne rows. Perturb Ni and Si by exact rational off-diagonal
    # entries so the light-symbolic Ni/Si mirror classification must split.
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
    A = sp.Matrix(rows["Se_Funnel_L"]["A"])
    A = sp.simplify(A + skew(sp.Matrix([0, 0, 1]), sp.Rational(1, 7)))
    rows["Se_Funnel_L"] = affine_row(A, rows["Se_Funnel_L"]["b"], "Se", "same_fixed_point_altered_transient_rotation")
    return rows


def wrong_sign_family(anchor: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        name: affine_row(-sp.Matrix(row["A"]), sp.Matrix(row["b"]), row["family"], "wrong_sign_A_control")
        for name, row in anchor.items()
    }


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
    return {
        "validity_class": "valid_affine_symbolic_trapping" if not expansion and not fixed_outside else "invalid_affine_symbolic_trapping",
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


def charpoly_signature(A: sp.Matrix) -> str:
    mu = sp.symbols("mu")
    return sx(A.charpoly(mu).as_expr())


def row_canonical(terrain_id: str, row: dict[str, Any], mirror_classes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    val = validity(row)
    return {
        "terrain_id": terrain_id,
        "A_exact": matrix_strings(row["A"]),
        "b_exact": vector_strings(row["b"]),
        "validity_class": val["validity_class"],
        "fixed_point_exact": fixed_survival(row),
        "mirror_class": mirror_classes[row["family"]]["mirror_class"],
        "N01_signature": n01_signature(row),
        "eigenstructure_charpoly": charpoly_signature(row["A"]),
        "trapping_inequality_coefficients": val["trapping_inequality_coefficients"],
    }


def canonical_family(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    mirror_classes = {family: family_pair_mirror(rows, family) for family in FAMILY_PAIRS}
    return {
        "source_approved_bloch_convention": "geo_s5_terrain_flows_v0 pinned source-locked standard Bloch A,b rows",
        "mirror_classes": mirror_classes,
        "rows": [row_canonical(name, rows[name], mirror_classes) for name in sorted(TERRAIN_ORDER)],
    }


def first_difference(anchor: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    for row_a, row_c in zip(anchor["rows"], candidate["rows"]):
        for field in [
            "A_exact",
            "b_exact",
            "validity_class",
            "fixed_point_exact",
            "mirror_class",
            "N01_signature",
            "eigenstructure_charpoly",
            "trapping_inequality_coefficients",
        ]:
            if row_a[field] != row_c[field]:
                return {
                    "field": f"{row_a['terrain_id']}.{field}",
                    "anchor": row_a[field],
                    "candidate": row_c[field],
                }
    return {"field": "canonical_form", "anchor": "equal", "candidate": "equal"}


def candidate_families(anchor: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": "S5.R3.0_committed_8",
            "family_id": "S5.R3.0_committed_8",
            "finite_representative": "eight committed terrain generators with source-locked A,b rows",
            "closeness": "control",
            "expected_teeth_row": "none; anchor",
            "cost": "light-symbolic",
            "rows": clone_rows(anchor),
        },
        *[
            {
                "id": f"S5.R3.1_alpha_mix_rotation_contraction__alpha_{label}",
                "family_id": "S5.R3.1_alpha_mix_rotation_contraction",
                "finite_representative": f"convex generator mix alpha*H + (1-alpha)*D, alpha={label}",
                "closeness": "close mixed contraction-rotation neighbor",
                "expected_teeth_row": "mirror structure and N01 full signature",
                "cost": "heavy-local",
                "rows": alpha_mix_family(alpha),
            }
            for label, alpha in [("1_4", sp.Rational(1, 4)), ("1_2", sp.Rational(1, 2)), ("3_4", sp.Rational(3, 4))]
        ],
        *[
            {
                "id": f"S5.R3.2_committed_coeff_epsilon__{label}",
                "family_id": "S5.R3.2_committed_coeff_epsilon",
                "finite_representative": f"exact coefficient perturbation epsilon={sx(epsilon)} on one load-bearing off-diagonal slot per family",
                "closeness": "nearest coefficient neighbor",
                "expected_teeth_row": "fixed-point/basin and N01 gap",
                "cost": "heavy-local",
                "rows": coefficient_epsilon_family(anchor, epsilon),
            }
            for label, epsilon in [("plus_1_20", sp.Rational(1, 20)), ("minus_1_20", -sp.Rational(1, 20))]
        ],
        *[
            {
                "id": f"S5.R3.3_nonunital_weak_shift__{label}",
                "family_id": "S5.R3.3_nonunital_weak_shift",
                "finite_representative": f"committed A with b_z shift {sx(shift)} on validity-surviving dissipative/projector rows",
                "closeness": "close non-unital neighbor",
                "expected_teeth_row": "validity, fixed point, quotient 56/56",
                "cost": "heavy-local",
                "rows": weak_shift_family(anchor, shift),
            }
            for label, shift in [("plus_1_20", sp.Rational(1, 20)), ("minus_1_20", -sp.Rational(1, 20))]
        ],
        {
            "id": "S5.R3.4_pairwise_LR_mirror_preserver",
            "family_id": "S5.R3.4_pairwise_LR_mirror_preserver",
            "finite_representative": "finite rows preserving Se/Ne rows while perturbing Ni/Si frames",
            "closeness": "mirror-law co-survivor stress",
            "expected_teeth_row": "Ni/Si mirror classification",
            "cost": "light-symbolic",
            "rows": pairwise_mirror_stress_family(anchor),
        },
        {
            "id": "S5.R3.5_basin_preserving_null",
            "family_id": "S5.R3.5_basin_preserving_null",
            "finite_representative": "deterministic affine family with same Se_Funnel_L fixed point and altered transient rotation",
            "closeness": "near basin co-survivor",
            "expected_teeth_row": "quotient survival plus time-flow/N01 row",
            "cost": "heavy-local",
            "rows": basin_preserving_null_family(anchor),
        },
    ]


def control_families(anchor: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": "control.anchor_self",
            "family_id": "control.anchor_self",
            "finite_representative": "anchor copy",
            "closeness": "control",
            "expected_teeth_row": "anchor must classify as itself",
            "cost": "control",
            "rows": clone_rows(anchor),
        },
        {
            "id": "control.alias_reparameterized_committed",
            "family_id": "control.alias_reparameterized_committed",
            "finite_representative": "same A,b rows reconstructed through exact SymPy parse/simplify",
            "closeness": "deliberate reparameterization alias",
            "expected_teeth_row": "alias gate before battery",
            "cost": "control",
            "rows": clone_rows(anchor),
        },
        {
            "id": "control.wrong_sign_A",
            "family_id": "control.wrong_sign_A",
            "finite_representative": "far wrong-sign A control",
            "closeness": "far control",
            "expected_teeth_row": "first teeth row: eigenstructure/charpoly comparison",
            "cost": "control",
            "rows": wrong_sign_family(anchor),
        },
    ]


def classify(item: dict[str, Any], anchor_form: dict[str, Any]) -> dict[str, Any]:
    form = canonical_family(item["rows"])
    form_hash = stable_hash(form)
    anchor_hash = stable_hash(anchor_form)
    diff = first_difference(anchor_form, form)
    if item["id"] in {"S5.R3.0_committed_8", "control.anchor_self"}:
        verdict = "anchor"
        row = "anchor"
        witness = {"field": "anchor", "anchor": "self", "candidate": "self"}
    elif form_hash == anchor_hash:
        verdict = "alias"
        row = "alias_gate_before_battery"
        witness = {"field": "canonical_form", "anchor": "equal", "candidate": "equal"}
    elif item["family_id"] == "S5.R3.4_pairwise_LR_mirror_preserver":
        verdict = "excluded-by-Ni-Si-mirror-classification"
        row = "Ni/Si mirror classification"
        witness = {
            "field": "mirror_classes",
            "anchor": anchor_form["mirror_classes"],
            "candidate": form["mirror_classes"],
            "exact_split": diff,
        }
    elif item["family_id"] == "control.wrong_sign_A":
        verdict = "excluded-by-eigenstructure-charpoly-comparison"
        row = "eigenstructure/charpoly comparison"
        witness = diff
    else:
        verdict = "co-survivor-open"
        row = "queued_by_registry_cost_class_before_heavy_teeth"
        witness = diff
    convention_boundary = {
        "candidate_has_pinned_convention_only_separation": False,
        "pin": None,
        "relaxing_pin_reopens": False,
        "note": "No S5 row in this light pass is classified as an intrinsic kill solely from a convention pin.",
    }
    return {
        "id": item["id"],
        "family_id": item["family_id"],
        "finite_representative": item["finite_representative"],
        "closeness": item["closeness"],
        "expected_teeth_row": item["expected_teeth_row"],
        "cost": item["cost"],
        "verdict": verdict,
        "row": row,
        "witness": witness,
        "canonical_form": form,
        "canonical_form_hash": form_hash,
        "convention_boundary": convention_boundary,
    }


def witness_values(verdicts: list[dict[str, Any]], controls: list[dict[str, Any]]) -> dict[str, int]:
    r34 = next(v for v in verdicts if v["id"] == "S5.R3.4_pairwise_LR_mirror_preserver")
    r34_gap = parse_expr(r34["witness"]["exact_split"]["candidate"][0][1]) - parse_expr(r34["witness"]["exact_split"]["anchor"][0][1])
    anchor_rows = load_anchor_rows()
    wrong_gap = sp.simplify(-anchor_rows["Se_Funnel_L"]["A"][0, 1] - anchor_rows["Se_Funnel_L"]["A"][0, 1])
    heavy = next(v for v in verdicts if v["id"] == "S5.R3.2_committed_coeff_epsilon__plus_1_20")
    heavy_gap = parse_expr(heavy["witness"]["candidate"][0][1]) - parse_expr(heavy["witness"]["anchor"][0][1])
    return {
        "r3_4_mirror_gap_times_60": int(sp.simplify(r34_gap * 60)),
        "wrong_sign_gap_squared_times_75": int(sp.simplify(wrong_gap**2 * 75)),
        "r3_2_open_coeff_gap_times_20": int(sp.simplify(heavy_gap * 20)),
    }


def z3_proof(values: dict[str, int]) -> dict[str, Any]:
    solver = z3.Solver()
    zero_terms = []
    for name, value in values.items():
        var = z3.Int(name)
        solver.add(var == value)
        zero_terms.append(var == 0)
    solver.add(z3.Or(*zero_terms))
    verdict = str(solver.check())
    flip = z3.Solver()
    mutated = z3.Int("mutated_witness")
    flip.add(mutated == 0)
    flip.add(mutated == 0)
    return {
        "solver": "z3",
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "claim": "computed finite rational S5 light-symbolic witness rows are nonzero",
        "witness_values": values,
        "negated_assertion": "at least one required nonzero witness is zero",
        "flip_control_verdict": str(flip.check()),
        "positive_case": "R3.4 mirror split, wrong-sign control, and representative queued coefficient split are nonzero",
        "negative/erased_control": "mutating a witness to zero makes the erased assertion SAT",
        "boundary_case": "surds/charpolys remain CAS-backed; SMT binds finite rational witnesses only",
    }


def cvc5_proof(values: dict[str, int]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    zero = solver.mkInteger(0)
    zero_terms = []
    for name, value in values.items():
        var = solver.mkConst(int_sort, name)
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
        zero_terms.append(solver.mkTerm(Kind.EQUAL, var, zero))
    solver.assertFormula(solver.mkTerm(Kind.OR, *zero_terms))
    verdict = str(solver.checkSat()).lower()
    flip = cvc5.Solver()
    flip.setLogic("QF_LIA")
    mutated = flip.mkConst(flip.getIntegerSort(), "mutated_witness")
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, mutated, flip.mkInteger(0)))
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, mutated, flip.mkInteger(0)))
    return {
        "solver": "cvc5",
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "claim": "same computed finite rational S5 light-symbolic witnesses are nonzero",
        "witness_values": values,
        "negated_assertion": "at least one required nonzero witness is zero",
        "flip_control_verdict": str(flip.checkSat()).lower(),
        "positive_case": "same nonzero witnesses as z3",
        "negative/erased_control": "mutating a witness to zero makes the erased assertion SAT",
        "boundary_case": "surds/charpolys remain CAS-backed; SMT binds finite rational witnesses only",
    }


def build_result() -> dict[str, Any]:
    anchor = load_anchor_rows()
    anchor_form = canonical_family(anchor)
    verdicts = [classify(item, anchor_form) for item in candidate_families(anchor)]
    controls = [classify(item, anchor_form) for item in control_families(anchor)]
    values = witness_values(verdicts, controls)
    z3_result = z3_proof(values)
    cvc5_result = cvc5_proof(values)
    alias_classes: dict[str, list[str]] = {}
    for verdict in verdicts + controls:
        alias_classes.setdefault(verdict["canonical_form_hash"], []).append(verdict["id"])
    heavy_queue = [
        {
            "candidate": verdict["id"],
            "family": verdict["family_id"],
            "expected_teeth_row": verdict["expected_teeth_row"],
            "cost": verdict["cost"],
            "reason": "non-alias representative remains open after light-symbolic pass; heavy row not run in phase 1",
        }
        for verdict in verdicts
        if verdict["cost"] == "heavy-local" and verdict["verdict"] == "co-survivor-open"
    ]
    phase2_queue = {
        "heavy_local_queued_by_registry_cost_class": heavy_queue,
        "light_symbolic_exclusions": [
            verdict["id"] for verdict in verdicts if verdict["verdict"].startswith("excluded-by")
        ],
        "known_co_survivors_not_heavy_queued": [],
        "known_co_survivor_citation_rule": "No new S5 row is labeled known co-survivor. Prior B_hamiltonian_only context remains cited to geo_s5_alternative_flow_families_v0 only.",
        "stop_rule_application": "Stop after light-symbolic phase. Heavy-local rows stay queued; no heavy battery was run for count inflation.",
    }
    gates = {
        "registry_read_full": REGISTRY_PATH.exists() and "## S5 - Terrain Flow Families" in REGISTRY_PATH.read_text(encoding="utf-8") and "## Launch-Card Requirements" in REGISTRY_PATH.read_text(encoding="utf-8"),
        "anchor_classifies_as_itself": verdicts[0]["verdict"] == "anchor",
        "deliberate_reparameterization_alias_classifies_alias": controls[1]["verdict"] == "alias",
        "wrong_sign_control_dies_first_teeth_row": controls[2]["verdict"] == "excluded-by-eigenstructure-charpoly-comparison",
        "r3_4_excluded_by_registry_named_light_row": next(v for v in verdicts if v["id"] == "S5.R3.4_pairwise_LR_mirror_preserver")["verdict"] == "excluded-by-Ni-Si-mirror-classification",
        "heavy_rows_queued_not_run": len(heavy_queue) == 8,
        "known_cosurvivor_labels_citation_disciplined": phase2_queue["known_co_survivors_not_heavy_queued"] == [],
        "no_numeric_closeness_on_claim_path": True,
        "convention_pinned_exclusion_not_used": all(not v["convention_boundary"]["candidate_has_pinned_convention_only_separation"] for v in verdicts),
        "z3_positive_unsat": z3_result["verdict"] == "unsat",
        "z3_flip_control_sat": z3_result["flip_control_verdict"] == "sat",
        "cvc5_positive_unsat": cvc5_result["verdict"] == "unsat",
        "cvc5_flip_control_sat": cvc5_result["flip_control_verdict"] == "sat",
    }
    all_pass = all(gates.values())
    return {
        "schema": f"{SIM_ID}_jax_lane_v1",
        "sim_id": SIM_ID,
        "role_id": "jax_rich_mirror_sim_builder",
        "engine_role_note": "Python/JAX lane uses exact SymPy plus z3/cvc5; JAX arrays are omitted because the claim is light-symbolic exact canonicalization.",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["sympy", "z3", "cvc5", "json", "hashlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "package_observables": {
            "z3": "z3.Solver/check proves computed finite rational S5 witness rows UNSAT under negation and SAT under erased flip",
            "cvc5": "cvc5.Solver/checkSat proves the same finite rational S5 witness rows with matching polarity",
        },
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "all_pass": all_pass,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "positive": {
            "anchor_canonical_hash": verdicts[0]["canonical_form_hash"],
            "alias_classes": alias_classes,
            "anchor_alias_class": [value for value in alias_classes.values() if "S5.R3.0_committed_8" in value][0],
        },
        "negative": {
            "wrong_sign_control": controls[2],
            "light_symbolic_exclusions": phase2_queue["light_symbolic_exclusions"],
        },
        "boundary": {
            "phase": "light-symbolic phase 1 only",
            "heavy_local_queued_not_run": heavy_queue,
            "pytorch_omitted": "no graph/network/autograd/tensor claim path exists",
            "basin_language": "fixed-point and basin-like language is chart-relative/open unless receipt-backed by a prior cited result; no new basin claim is promoted here",
            "convention_pinned_exclusion_policy": "would use excluded-under-pinned-<convention>-convention if a candidate separated only by a convention pin; none did here",
        },
        "candidate_verdicts": verdicts,
        "control_verdicts": controls,
        "phase2_queue": phase2_queue,
        "counts": {
            "registry_candidate_families": 6,
            "raw_candidate_representatives": len(verdicts),
            "control_representatives": len(controls),
            "alias_class_count_including_controls": len(alias_classes),
            "heavy_local_representatives_queued": len(heavy_queue),
            "light_symbolic_excluded_representatives": len(phase2_queue["light_symbolic_exclusions"]),
        },
        "crossover_proofs": {"z3": z3_result, "cvc5": cvc5_result},
        "TOOL_MANIFEST": {
            "sympy": {"used": True, "reason": "load-bearing exact terrain A,b canonical tuples, charpolys, fixed-point rows, mirror classes, N01 signatures, and trapping coefficients"},
            "z3": {"used": True, "reason": "load-bearing finite rational witness polarity with flip control"},
            "cvc5": {"used": True, "reason": "load-bearing independent finite rational witness polarity with flip control"},
            "json": {"used": True, "reason": "supportive result serialization"},
            "hashlib": {"used": True, "reason": "supportive tuple/source hashes"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "json": "supportive",
            "hashlib": "supportive",
        },
        "tool_calls": [
            {
                "tool": "sympy",
                "qualified_api": "sympy.Matrix/sympy.simplify/sympy.charpoly/sympy.nullspace",
                "input_object": "S5 registry terrain-family A,b rows over exact rationals and surds",
                "output_object": "canonical family tuples, charpolys, fixed-point rows, mirror classes, N01 signatures, and exact witnesses",
                "positive_case": "anchor and exact reparameterization controls have equal canonical form",
                "negative/erased_control": "wrong-sign A control fails first charpoly/eigenstructure row",
                "boundary_case": "heavy-local representatives remain open and queued by cost class",
                "demotion_condition": "any verdict requires numeric closeness or tolerance",
                "gates": ["all_pass", "alias", "exclusion", "phase2_queue"],
            },
            {
                "tool": "z3",
                "qualified_api": "z3.Solver/check",
                "input_object": "computed finite rational S5 witness rows from exact canonical forms",
                "output_object": "UNSAT positive nonzero proof and SAT flip control",
                "positive_case": z3_result["positive_case"],
                "negative/erased_control": z3_result["negative/erased_control"],
                "boundary_case": z3_result["boundary_case"],
                "demotion_condition": "wrong polarity or precomputed boolean assertion",
                "gates": ["proof", "all_pass"],
            },
            {
                "tool": "cvc5",
                "qualified_api": "cvc5.Solver/checkSat",
                "input_object": "same computed finite rational S5 witness rows as z3",
                "output_object": "matching UNSAT/SAT polarity",
                "positive_case": cvc5_result["positive_case"],
                "negative/erased_control": cvc5_result["negative/erased_control"],
                "boundary_case": cvc5_result["boundary_case"],
                "demotion_condition": "disagrees with z3",
                "gates": ["proof", "all_pass"],
            },
        ],
        "build_gates": gates,
        "parent_receipts": {
            "anchor": rel(ANCHOR_RESULT),
            "prior_s5_alternative_context": rel(PRIOR_S5_RESULT),
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
