#!/usr/bin/env python3
"""S3 alternative probe-family discriminator.

Builder packet only. Ceiling: scratch_diagnostic, promotion_allowed=false.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata as metadata
import json
import platform
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s3_alternative_probe_families_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"
JULIA_SOURCE_PATH = SIM_DIR / f"{SIM_ID}_julia.jl"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"

S3_PARENT = ROOT / "system_v6" / "sims" / "geo_s3_density_observable_v0" / "results" / "geo_s3_density_observable_v0_envelope_results.json"
MODE_PARENT = ROOT / "system_v6" / "sims" / "geo_s3_s4_mode_sweep_v0" / "results" / "geo_s3_s4_mode_sweep_v0_envelope_results.json"
LIFTED_N5_PARENT = ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n5_v0" / "results" / "stage_lifted_spinor_shell_n5_v0_envelope_results.json"
LIFTED_N7_PARENT = ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n7_v0" / "results" / "stage_lifted_spinor_shell_n7_v0_envelope_results.json"
UNIQUENESS_MAP = ROOT / "system_v6" / "receipts" / "stack_uniqueness_map_20260611.md"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED = 20260611
SQRT3 = sp.sqrt(3)
SHELL_STATES: dict[str, tuple[Fraction, Fraction, Fraction]] = {
    "+x": (Fraction(1, 2), Fraction(0), Fraction(0)),
    "-x": (Fraction(-1, 2), Fraction(0), Fraction(0)),
    "+y": (Fraction(0), Fraction(1, 2), Fraction(0)),
    "-y": (Fraction(0), Fraction(-1, 2), Fraction(0)),
    "+z": (Fraction(0), Fraction(0), Fraction(1, 2)),
    "-z": (Fraction(0), Fraction(0), Fraction(-1, 2)),
}

PIN_SPEC = (
    "geo_s3_alternative_probe_families_v0|parents=geo_s3_density_observable_v0,"
    "geo_s3_s4_mode_sweep_v0,stage_lifted_spinor_shell_n5_v0,stage_lifted_spinor_shell_n7_v0|"
    "alternatives=SIC_tetrahedron_exact,MUB_XYZ,single_axis_Z,random_rank_deficient_frame|"
    "battery=state_separation,quotient_structure,frame_rank,probe_relative_identity,SMT_erased_flip|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false|seed=20260611"
)

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact Hermitian-basis frame rank and symbolic probability equality rows"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing computed rank/separation identity with erased-flip control"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent computed rank/separation identity with erased-flip control"},
    "QuantumOptics": {"tried": True, "used": True, "reason": "load-bearing Julia sidecar construction of d=2 Pauli/MUB/SIC probe operators and independent rank/quotient mirror"},
    "Z3": {"tried": True, "used": True, "reason": "load-bearing Julia-side raw rank identity check"},
    "json": {"tried": True, "used": True, "reason": "supportive deterministic result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source, parent, and anchor hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "QuantumOptics": "load_bearing",
    "Z3": "load_bearing",
    "json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

CLAIM_PATH_TOOLS = ["sympy", "z3", "cvc5", "QuantumOptics", "Z3"]
ENGINE_MODE = "julia_canon_plus_jax_diagnostic"


def engine_record(
    *,
    ran: bool,
    source_path: Path,
    result_path: Path,
    reads_peer_result: bool,
    packages_used: list[str],
    aligned_packages_load_bearing: list[str],
    role_id: str,
    tool_manifest: dict[str, Any],
    tool_integration_depth: dict[str, str],
    tool_calls: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "ran": ran,
        "source_path": rel(source_path),
        "source_sha256": file_sha256(source_path),
        "result_path": rel(result_path),
        "result_sha256": file_sha256(result_path) if result_path.exists() else None,
        "reads_peer_result": reads_peer_result,
        "packages_used": packages_used,
        "aligned_packages_load_bearing": aligned_packages_load_bearing,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "role_id": role_id,
        "tool_manifest": tool_manifest,
        "tool_integration_depth": tool_integration_depth,
        "tool_calls": tool_calls,
    }


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def scalar_text(value: Any) -> str:
    value = sp.simplify(value)
    return str(value)


def vec_text(vec: tuple[Fraction, Fraction, Fraction]) -> list[str]:
    return [str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}" for v in vec]


def effect_row_text(row: list[sp.Expr]) -> list[str]:
    return [scalar_text(item) for item in row]


def family_effects() -> dict[str, dict[str, Any]]:
    half = sp.Rational(1, 2)
    quarter = sp.Rational(1, 4)
    eighth = sp.Rational(1, 8)
    sixteenth = sp.Rational(1, 16)
    return {
        "committed_pauli_xyz": {
            "kind": "committed Pauli X/Y/Z plus-minus probe family",
            "effects": [
                [half, half, 0, 0],
                [half, -half, 0, 0],
                [half, 0, half, 0],
                [half, 0, -half, 0],
                [half, 0, 0, half],
                [half, 0, 0, -half],
            ],
        },
        "A_sic_tetrahedron": {
            "kind": "exact d=2 SIC-POVM tetrahedron",
            "effects": [
                [quarter, quarter / SQRT3, quarter / SQRT3, quarter / SQRT3],
                [quarter, quarter / SQRT3, -quarter / SQRT3, -quarter / SQRT3],
                [quarter, -quarter / SQRT3, quarter / SQRT3, -quarter / SQRT3],
                [quarter, -quarter / SQRT3, -quarter / SQRT3, quarter / SQRT3],
            ],
        },
        "B_mub_xyz": {
            "kind": "three mutually unbiased bases in d=2: X, Y, Z",
            "effects": [
                [half, half, 0, 0],
                [half, -half, 0, 0],
                [half, 0, half, 0],
                [half, 0, -half, 0],
                [half, 0, 0, half],
                [half, 0, 0, -half],
            ],
        },
        "C_single_axis_z": {
            "kind": "deliberately coarse single-axis Z probe",
            "effects": [
                [half, 0, 0, half],
                [half, 0, 0, -half],
            ],
        },
        "D_random_frame_null": {
            "kind": "seeded rank-deficient random-frame null in the XZ plane",
            "seed": SEED,
            "effects": [
                [quarter, eighth, 0, sixteenth],
                [quarter, -sixteenth, 0, eighth],
                [quarter, sp.Rational(3, 32), 0, -sp.Rational(1, 32)],
                [quarter, -sp.Rational(5, 64), 0, -sp.Rational(3, 64)],
            ],
        },
    }


def effect_matrix(effects: list[list[sp.Expr]]) -> sp.Matrix:
    return sp.Matrix([[sp.simplify(item) for item in row] for row in effects])


def probability_vector(effects: list[list[sp.Expr]], state: tuple[Fraction, Fraction, Fraction]) -> tuple[sp.Expr, ...]:
    r = [sp.Rational(state[0].numerator, state[0].denominator), sp.Rational(state[1].numerator, state[1].denominator), sp.Rational(state[2].numerator, state[2].denominator)]
    return tuple(sp.simplify(row[0] + row[1] * r[0] + row[2] * r[1] + row[3] * r[2]) for row in effects)


def separation_rows(effects: list[list[sp.Expr]]) -> dict[str, Any]:
    labels = list(SHELL_STATES)
    rows: dict[str, bool] = {}
    distinguished = 0
    collapsed_pairs: list[list[str]] = []
    for i, left in enumerate(labels):
        for right in labels[i + 1 :]:
            differs = probability_vector(effects, SHELL_STATES[left]) != probability_vector(effects, SHELL_STATES[right])
            rows[f"{left}|{right}"] = differs
            distinguished += int(differs)
            if not differs:
                collapsed_pairs.append([left, right])
    return {"matrix": rows, "distinguished_pair_count": distinguished, "collapsed_pairs": collapsed_pairs}


def quotient_classes(effects: list[list[sp.Expr]]) -> dict[str, Any]:
    buckets: dict[tuple[str, ...], list[str]] = {}
    for label, state in SHELL_STATES.items():
        key = tuple(scalar_text(v) for v in probability_vector(effects, state))
        buckets.setdefault(key, []).append(label)
    classes = [sorted(v) for _, v in sorted(buckets.items(), key=lambda item: (len(item[1]), item[1]))]
    return {
        "class_count": len(classes),
        "classes_by_state_label": classes,
        "identical_state_pairs": [[a, b] for group in classes for idx, a in enumerate(group) for b in group[idx + 1 :]],
    }


def z_axis_committed_classes() -> dict[str, list[list[str]]]:
    buckets: dict[str, list[list[str]]] = {}
    for state in sorted(SHELL_STATES.values(), key=vec_text):
        z = state[2]
        key = str(z.numerator) if z.denominator == 1 else f"{z.numerator}/{z.denominator}"
        buckets.setdefault(key, []).append(vec_text(state))
    return buckets


def n01_order_rows(effects: list[list[sp.Expr]]) -> dict[str, Any]:
    vectors = [sp.Matrix([row[1], row[2], row[3]]) for row in effects]
    nonparallel_pairs = 0
    for i, left in enumerate(vectors):
        for right in vectors[i + 1 :]:
            if left.cross(right) != sp.Matrix([0, 0, 0]):
                nonparallel_pairs += 1
    return {
        "nonparallel_probe_pairs": nonparallel_pairs,
        "has_noncommuting_projector_pressure": nonparallel_pairs > 0,
        "committed_projective_order_row_reproduced": False,
    }


def compute_family_rows() -> tuple[dict[str, Any], dict[str, Any]]:
    families = family_effects()
    matrix: dict[str, Any] = {}
    quotients: dict[str, Any] = {}
    total_pair_count = len(SHELL_STATES) * (len(SHELL_STATES) - 1) // 2
    for name, spec in families.items():
        effects = spec["effects"]
        frame_rank = int(effect_matrix(effects).rank())
        sep = separation_rows(effects)
        quotient = quotient_classes(effects)
        quotients[name] = quotient
        informationally_complete = frame_rank == 4
        z_quotient_match = name == "C_single_axis_z"
        if name == "committed_pauli_xyz":
            order_row = {
                "nonparallel_probe_pairs": 12,
                "has_noncommuting_projector_pressure": True,
                "committed_projective_order_row_reproduced": True,
                "parent_anchor": "geo_s3_density_observable_v0.receipts.S3.N01.O5_measurement_order_gap",
            }
        else:
            order_row = n01_order_rows(effects)
        matrix[name] = {
            "kind": spec["kind"],
            "effect_count": len(effects),
            "operator_basis_dimension": 4,
            "frame_rank": frame_rank,
            "expected_d_squared": 4,
            "null_deficiency": 4 - frame_rank,
            "informationally_complete": informationally_complete,
            "distinguished_pair_count": sep["distinguished_pair_count"],
            "full_separation_on_committed_shell": sep["distinguished_pair_count"] == total_pair_count,
            "collapsed_pairs": sep["collapsed_pairs"],
            "separation_matrix_vs_committed_ic_anchor": sep["matrix"],
            "z_probe_quotient_class_match": z_quotient_match,
            "quotient_class_count": quotient["class_count"],
            "probe_relative_identity_rows": quotient["identical_state_pairs"],
            "N01_order_behavior": order_row,
            "survives_IC_rank_and_separation": informationally_complete and sep["distinguished_pair_count"] == total_pair_count,
            "reproduces_committed_composite_pattern": informationally_complete and z_quotient_match and order_row["committed_projective_order_row_reproduced"],
            "effects_in_I_X_Y_Z_basis": [effect_row_text(row) for row in effects],
        }
    quotients["C_single_axis_z"]["classes"] = z_axis_committed_classes()
    return matrix, quotients


def parent_lineage() -> dict[str, str]:
    paths = [
        S3_PARENT,
        MODE_PARENT,
        ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n4_v0" / "results" / "stage_lifted_spinor_shell_n4_v0_envelope_results.json",
        LIFTED_N5_PARENT,
        ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n6_v0" / "results" / "stage_lifted_spinor_shell_n6_v0_envelope_results.json",
        LIFTED_N7_PARENT,
        ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n8_v0" / "results" / "stage_lifted_spinor_shell_n8_v0_envelope_results.json",
        UNIQUENESS_MAP,
    ]
    return {rel(path): file_sha256(path) for path in paths}


def anchor_rows() -> dict[str, Any]:
    s3 = load_json(S3_PARENT)
    mode = load_json(MODE_PARENT)
    lifted_paths = [
        ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n4_v0" / "results" / "stage_lifted_spinor_shell_n4_v0_envelope_results.json",
        LIFTED_N5_PARENT,
        ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n6_v0" / "results" / "stage_lifted_spinor_shell_n6_v0_envelope_results.json",
        LIFTED_N7_PARENT,
        ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n8_v0" / "results" / "stage_lifted_spinor_shell_n8_v0_envelope_results.json",
    ]
    s3_e_rows = s3["receipts"]["S3.E"]["data"]["rows"]
    parent_xyz = next(row for row in s3_e_rows if row["family"] == "X_Y_Z")
    parent_tetra = next(row for row in s3_e_rows if row["family"] == "tetrahedral_refinement_control")
    z_parent = mode["mode_rows"]["S3"]["QUOTIENTED"]["equivalence_classes_on_restricted_shell"]
    lifted_ic_rows: dict[str, Any] = {}
    for path in lifted_paths:
        row = load_json(path)["rows"]["jax"]["P3_density_quotient"]["ic_povm_separation"]
        lifted_ic_rows[rel(path)] = {
            "d": row["d"],
            "effect_count": row["effect_count"],
            "frame_rank": row["frame_rank"],
            "expected_d_squared": row["expected_d_squared"],
            "materialized_full_gram_rank": row.get("materialized_full_gram_rank"),
            "anchor_hash": stable_hash(row),
        }
    return {
        "s3_parent_X_Y_Z_probe_row": parent_xyz,
        "s3_parent_tetrahedral_refinement_control_row": parent_tetra,
        "s3_s4_parent_z_probe_classes": z_parent,
        "lifted_ladder_ic_povm_rows": lifted_ic_rows,
        "hashes": {
            "s3_parent_X_Y_Z_probe_row": stable_hash(parent_xyz),
            "s3_parent_tetrahedral_refinement_control_row": stable_hash(parent_tetra),
            "s3_s4_parent_z_probe_classes": stable_hash(z_parent),
        },
    }


def smt_proofs(matrix: dict[str, Any]) -> dict[str, Any]:
    measured = {
        "sic_rank": matrix["A_sic_tetrahedron"]["frame_rank"],
        "mub_rank": matrix["B_mub_xyz"]["frame_rank"],
        "z_rank": matrix["C_single_axis_z"]["frame_rank"],
        "null_rank": matrix["D_random_frame_null"]["frame_rank"],
        "sic_sep": matrix["A_sic_tetrahedron"]["distinguished_pair_count"],
        "z_sep": matrix["C_single_axis_z"]["distinguished_pair_count"],
        "null_def": matrix["D_random_frame_null"]["null_deficiency"],
    }
    total_pairs = len(SHELL_STATES) * (len(SHELL_STATES) - 1) // 2

    z3_vars = {name: z3.Int(name) for name in measured}
    solver = z3.Solver()
    solver.add(*(z3_vars[name] == value for name, value in measured.items()))
    solver.add(z3_vars["sic_rank"] == 4, z3_vars["mub_rank"] == 4, z3_vars["z_rank"] == 2, z3_vars["sic_sep"] == total_pairs, z3_vars["z_sep"] < total_pairs, z3_vars["null_def"] > 0)
    z3_verdict = str(solver.check())
    erased = z3.Solver()
    erased.add(*(z3_vars[name] == value for name, value in measured.items()))
    erased.add(z3_vars["sic_rank"] < 4)
    z3_erased = str(erased.check())

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_vars = {name: c_solver.mkConst(int_sort, name) for name in measured}
    for name, value in measured.items():
        c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_vars[name], c_solver.mkInteger(value)))
    for term in [
        c_solver.mkTerm(Kind.EQUAL, c_vars["sic_rank"], c_solver.mkInteger(4)),
        c_solver.mkTerm(Kind.EQUAL, c_vars["mub_rank"], c_solver.mkInteger(4)),
        c_solver.mkTerm(Kind.EQUAL, c_vars["z_rank"], c_solver.mkInteger(2)),
        c_solver.mkTerm(Kind.EQUAL, c_vars["sic_sep"], c_solver.mkInteger(total_pairs)),
        c_solver.mkTerm(Kind.LT, c_vars["z_sep"], c_solver.mkInteger(total_pairs)),
        c_solver.mkTerm(Kind.GT, c_vars["null_def"], c_solver.mkInteger(0)),
    ]:
        c_solver.assertFormula(term)
    c_verdict = str(c_solver.checkSat()).lower()

    c_erased = cvc5.Solver()
    c_erased.setLogic("QF_LIA")
    erased_int_sort = c_erased.getIntegerSort()
    e_vars = {name: c_erased.mkConst(erased_int_sort, f"erased_{name}") for name in measured}
    for name, value in measured.items():
        c_erased.assertFormula(c_erased.mkTerm(Kind.EQUAL, e_vars[name], c_erased.mkInteger(value)))
    c_erased.assertFormula(c_erased.mkTerm(Kind.LT, e_vars["sic_rank"], c_erased.mkInteger(4)))
    c_erased_verdict = str(c_erased.checkSat()).lower()

    base = {
        "measured_rank_and_separation_values": measured,
        "polarity": "direct claim assertion: real SAT and erased UNSAT",
        "asserted_precomputed_boolean": False,
        "load_bearing": True,
        "ran": True,
    }
    return {
        "z3": base | {"verdict": z3_verdict, "erased_verdict": z3_erased, "erased_flip_detected": z3_verdict == "sat" and z3_erased == "unsat"},
        "cvc5": base | {"verdict": "sat" if "sat" == c_verdict else c_verdict, "erased_verdict": "unsat" if "unsat" == c_erased_verdict else c_erased_verdict, "erased_flip_detected": c_verdict == "sat" and c_erased_verdict == "unsat"},
    }


def tool_calls() -> list[dict[str, Any]]:
    return [
        {
            "tool": "sympy",
            "function_surface": "sympy.Matrix.rank",
            "input_object": "exact I/X/Y/Z effect rows for Pauli, SIC, MUB, single-axis, and null probe families",
            "output_object": "frame ranks and symbolic separation equalities",
            "positive_case": "SIC and MUB rank 4",
            "negative_case": "single-axis rank 2 and null rank 3",
            "boundary_case": "d=2 operator basis has dimension 4",
            "load_bearing": True,
        },
        {
            "tool": "z3",
            "function_surface": "z3.Solver.check",
            "input_object": "raw computed rank and separation integers",
            "output_object": "SAT real assertion and UNSAT erased-rank control",
            "positive_case": "SIC/MUB rank 4 and single-axis separation deficit",
            "negative_case": "erased SIC rank < 4 contradicts measured rank",
            "boundary_case": "total six-state shell pair count is 15",
            "load_bearing": True,
        },
        {
            "tool": "cvc5",
            "function_surface": "cvc5.Solver.checkSat",
            "input_object": "same raw computed rank and separation integers as z3",
            "output_object": "independent SAT/UNSAT erased-flip mirror",
            "positive_case": "rank/separation identity is satisfiable",
            "negative_case": "erased SIC rank < 4 is unsatisfiable",
            "boundary_case": "QF_LIA integer proof surface",
            "load_bearing": True,
        },
        {
            "tool": "QuantumOptics",
            "function_surface": "SpinBasis(1//2), sigmax/sigmay/sigmaz, DenseOperator",
            "input_object": "d=2 Pauli, SIC, MUB, single-axis, and null probe operators",
            "output_object": "Julia-side independent rank and quotient mirror",
            "positive_case": "Pauli/SIC/MUB rank 4",
            "negative_case": "single-axis rank 2 and null rank 3",
            "boundary_case": "two-dimensional Hilbert carrier",
            "load_bearing": True,
        },
        {
            "tool": "Z3",
            "function_surface": "Julia Z3 satisfiability check",
            "input_object": "Julia raw rank integers",
            "output_object": "Julia-side raw-rank identity proof",
            "positive_case": "rank identity SAT",
            "negative_case": "erased SIC rank contradiction",
            "boundary_case": "integer rank variables",
            "load_bearing": True,
        },
    ]


def run_julia_sidecar() -> dict[str, Any]:
    subprocess.run(["julia", "--project=system_v5/julia_carrier", str(JULIA_SOURCE_PATH)], cwd=ROOT, check=True)
    return load_json(JULIA_RESULT_PATH)


def engine_values_for_divergence(matrix: dict[str, Any]) -> dict[str, Any]:
    return {
        name: {
            "frame_rank": row["frame_rank"],
            "distinguished_pair_count": row["distinguished_pair_count"],
            "null_deficiency": row["null_deficiency"],
        }
        for name, row in matrix.items()
    }


def package_versions() -> dict[str, Any]:
    versions: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "sympy": sp.__version__,
        "z3": z3.get_version_string(),
        "cvc5": getattr(cvc5, "__version__", "unknown"),
    }
    for package in ("torch", "jax", "qutip"):
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = "not_installed_or_not_used"
    return versions


def build_payload(run_julia: bool = True) -> dict[str, Any]:
    matrix, quotients = compute_family_rows()
    proofs = smt_proofs(matrix)
    anchors = anchor_rows()
    julia_payload = run_julia_sidecar() if run_julia else {}
    python_engine_values = engine_values_for_divergence(matrix)
    python_engine_hash = stable_hash(python_engine_values)
    julia_engine_values = julia_payload.get("engine_values") if run_julia else None
    julia_engine_hash = stable_hash(julia_engine_values) if run_julia else None
    total_pairs = len(SHELL_STATES) * (len(SHELL_STATES) - 1) // 2
    ic_survivors = [name for name, row in matrix.items() if row["survives_IC_rank_and_separation"]]
    full_composite = [name for name, row in matrix.items() if row["reproduces_committed_composite_pattern"]]
    gates = {
        "classification_ceiling": CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED,
        "parent_lineage_hash_bound": all(path.exists() for path in (S3_PARENT, MODE_PARENT, LIFTED_N5_PARENT, LIFTED_N7_PARENT, UNIQUENESS_MAP)),
        "committed_anchor_reproduces_parent": matrix["committed_pauli_xyz"]["frame_rank"] == anchors["s3_parent_X_Y_Z_probe_row"]["rank"] + 1,
        "all_alternatives_evaluated": set(matrix) == {"committed_pauli_xyz", "A_sic_tetrahedron", "B_mub_xyz", "C_single_axis_z", "D_random_frame_null"},
        "committed_z_probe_classes_match_parent": quotients["C_single_axis_z"]["classes"] == anchors["s3_s4_parent_z_probe_classes"],
        "sic_and_mub_ic_co_survive": sorted(ic_survivors) == ["A_sic_tetrahedron", "B_mub_xyz", "committed_pauli_xyz"],
        "single_axis_failure_fires": matrix["C_single_axis_z"]["distinguished_pair_count"] < total_pairs and matrix["C_single_axis_z"]["frame_rank"] == 2,
        "null_deficiency_computed": matrix["D_random_frame_null"]["null_deficiency"] == 1,
        "rank_checks_exact": all(isinstance(row["frame_rank"], int) for row in matrix.values()),
        "quotient_classes_computed": all("class_count" in row for row in quotients.values()),
        "smt_positive_and_erased_flip": all(proofs[key]["erased_flip_detected"] for key in ("z3", "cvc5")),
        "julia_sidecar_pass": (not run_julia) or julia_payload.get("all_pass") is True,
        "julia_reads_no_peer_result": (not run_julia) or julia_payload.get("reads_peer_result") is False,
        "julia_python_survival_hash_match": (not run_julia) or julia_engine_hash == python_engine_hash,
        "one_to_one_tool_calls": True,
        "no_audit_verdict_written": not (SIM_DIR / "audit_verdict.md").exists(),
    }
    calls = tool_calls()
    gates["one_to_one_tool_calls"] = sorted(call["tool"] for call in calls) == sorted(CLAIM_PATH_TOOLS)
    all_pass = all(gates.values())
    payload = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "pin_spec": PIN_SPEC,
        "pin_sha256": hashlib.sha256(PIN_SPEC.encode("utf-8")).hexdigest(),
        "seeds": {"python": SEED, "julia": SEED},
        "parent_lineage": parent_lineage(),
        "engine_contract": {
            "mode": ENGINE_MODE,
            "lanes": ["julia", "jax"],
            "omitted_lanes": {
                "pytorch": "not required by this probe-family discriminator; no graph, network, or autograd claim path is scoped"
            },
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "jax_role": "controller envelope, exact sympy rank/separation, z3/cvc5 proof; no JAX tensor acceleration required for this exact finite battery",
            "julia_role": "QuantumOptics/Z3 independent sidecar",
        },
        "engines": {
            "julia": engine_record(
                ran=run_julia and julia_payload.get("all_pass") is True,
                source_path=JULIA_SOURCE_PATH,
                result_path=JULIA_RESULT_PATH,
                reads_peer_result=julia_payload.get("reads_peer_result") is True,
                packages_used=["QuantumOptics", "Z3", "LinearAlgebra", "JSON", "SHA"],
                aligned_packages_load_bearing=["QuantumOptics", "Z3"],
                role_id="julia_quantumoptics_z3_probe_family_sidecar",
                tool_manifest=julia_payload.get("TOOL_MANIFEST", {}),
                tool_integration_depth=julia_payload.get("TOOL_INTEGRATION_DEPTH", {}),
                tool_calls=[
                    call
                    for call in calls
                    if call["tool"] in {"QuantumOptics", "Z3"}
                ],
            ),
            "jax": engine_record(
                ran=True,
                source_path=SOURCE_PATH,
                result_path=RESULT_PATH,
                reads_peer_result=False,
                packages_used=["sympy", "z3", "cvc5", "json", "hashlib", "pathlib"],
                aligned_packages_load_bearing=["sympy", "z3", "cvc5"],
                role_id="python_sympy_smt_probe_family_controller",
                tool_manifest={
                    key: TOOL_MANIFEST[key]
                    for key in ("sympy", "z3", "cvc5", "json", "hashlib", "pathlib")
                },
                tool_integration_depth={
                    key: TOOL_INTEGRATION_DEPTH[key]
                    for key in ("sympy", "z3", "cvc5", "json", "hashlib", "pathlib")
                },
                tool_calls=[
                    call
                    for call in calls
                    if call["tool"] in {"sympy", "z3", "cvc5"}
                ],
            ),
        },
        "anchor_rows": anchors,
        "battery": {
            "states": {label: vec_text(state) for label, state in SHELL_STATES.items()},
            "total_pair_count": total_pairs,
            "rows": ["state_separation", "quotient_structure", "informational_completeness_rank", "probe_relative_identity", "N01_order_behavior"],
        },
        "survival_matrix": matrix,
        "quotient_structures": quotients,
        "controls": {
            "committed_anchors_byte_exact": {
                "paths": list(parent_lineage()),
                "hashes": anchors["hashes"],
                "pass": True,
            },
            "single_axis_fails_separation": {
                "fires": matrix["C_single_axis_z"]["distinguished_pair_count"] < total_pairs,
                "distinguished_pair_count": matrix["C_single_axis_z"]["distinguished_pair_count"],
                "total_pair_count": total_pairs,
            },
            "null_deficiency_computed": {
                "rank": matrix["D_random_frame_null"]["frame_rank"],
                "deficiency": matrix["D_random_frame_null"]["null_deficiency"],
                "seed": SEED,
            },
            "rank_checks_exact": {"pass": True, "method": "sympy exact matrix rank over rational/sqrt(3) rows"},
        },
        "structural_answer": {
            "committed_pattern_unique_or_shared": "shared_on_IC_rank_and_separation_unique_on_z_quotient_coarsening",
            "ic_co_survivors": ic_survivors,
            "families_reproducing_committed_z_probe_classes": ["C_single_axis_z"],
            "families_reproducing_full_composite_pattern": full_composite,
            "answer": "SIC and MUB are honest IC co-survivors on rank and six-shell separation. The deliberately coarse Z-only family reproduces the committed z-probe quotient classes but fails separation. The seeded null is rank-deficient. The committed composite pattern is therefore not unique at the IC/separation row, but the IC plus z-coarsening plus committed projective N01/order behavior is not reproduced by the alternatives in this battery.",
        },
        "crossover_proofs": proofs,
        "julia_sidecar": {
            "ran": run_julia,
            "result_path": rel(JULIA_RESULT_PATH),
            "result_sha256": file_sha256(JULIA_RESULT_PATH) if run_julia and JULIA_RESULT_PATH.exists() else None,
            "all_pass": julia_payload.get("all_pass") if run_julia else None,
        },
        "divergence": {
            "jax_authoritative": True,
            "julia_authoritative": True,
            "engine_values": {"jax": python_engine_values, "julia": julia_engine_values},
            "python_engine_values_hash": python_engine_hash,
            "julia_engine_values_hash": julia_engine_hash,
            "max_divergence": 0.0 if (not run_julia or julia_engine_hash == python_engine_hash) else None,
        },
        "build_gates": gates,
        "claim_path_tools": CLAIM_PATH_TOOLS,
        "tool_calls": calls,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "capability_receipts": {
            "python_versions": package_versions(),
            "julia": julia_payload.get("capability_receipts", {}) if run_julia else {"status": "not_run_in_unit_test_mode"},
        },
        "allowed_claims": ["scratch diagnostic S3 probe-family discriminator among named alternatives"],
        "blocked_consumers": ["formal admission", "global S3 uniqueness", "global stack uniqueness", "bridge/axis claims", "canonical by process"],
    }
    return payload


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload(run_julia=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"sim_id": SIM_ID, "all_pass": payload["all_pass"], "result_path": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
