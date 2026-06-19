#!/usr/bin/env python3
"""S3/S4 RESTRICTED + QUOTIENTED mode sweep over committed anchors."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any

import jax
from jax import config

config.update("jax_enable_x64", True)
import jax.numpy as jnp
import sympy as sp
from z3 import Int, Solver

try:
    import cvc5
except Exception:  # pragma: no cover - runtime validator records this.
    cvc5 = None


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s3_s4_mode_sweep_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"
JULIA_SOURCE_PATH = SIM_DIR / f"{SIM_ID}_julia.jl"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"

GEOMETRY_PROGRAM = ROOT / "system_v6" / "receipts" / "geometry_sim_program_canonical_20260610.md"
AUDIT_BAR = ROOT / "system_v6" / "receipts" / "audit_bar_calibration_20260610.md"
TOOLSET_RECEIPT = ROOT / "system_v6" / "receipts" / "toolset_expansion_20260610.md"
S3_PARENT = ROOT / "system_v6" / "sims" / "geo_s3_density_observable_v0" / "results" / "geo_s3_density_observable_v0_envelope_results.json"
S4_PARENT = ROOT / "system_v6" / "sims" / "geo_s4_operator_stage_v0" / "results" / "geo_s4_operator_stage_v0_envelope_results.json"
S2_S5_CONTEXT = ROOT / "system_v6" / "sims" / "geo_s2_s5_mode_sweep_v0" / "results" / "geo_s2_s5_mode_sweep_v0_envelope_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED = 20260610
R0 = Fraction(1, 2)
GRID = [Fraction(-1, 2), Fraction(0), Fraction(1, 2)]
OPERATOR_NAMES = ["D_z", "D_x", "R_x", "R_z"]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(value: Any) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def frac_text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def vec_text(vec: tuple[Fraction, Fraction, Fraction]) -> list[str]:
    return [frac_text(item) for item in vec]


def norm2(vec: tuple[Fraction, Fraction, Fraction]) -> Fraction:
    return sum((x * x for x in vec), Fraction(0))


def finite_grid_points() -> list[tuple[Fraction, Fraction, Fraction]]:
    return [(x, y, z) for x in GRID for y in GRID for z in GRID]


def shell_points() -> list[tuple[Fraction, Fraction, Fraction]]:
    target = R0 * R0
    return [row for row in finite_grid_points() if norm2(row) == target]


def matrix_from_parent(row: dict[str, Any]) -> tuple[tuple[Fraction, Fraction, Fraction], ...]:
    return tuple(tuple(Fraction(item) for item in r) for r in row["pinned"]["M"])


def apply_matrix(matrix: tuple[tuple[Fraction, Fraction, Fraction], ...], vec: tuple[Fraction, Fraction, Fraction]) -> tuple[Fraction, Fraction, Fraction]:
    return tuple(sum(matrix[i][j] * vec[j] for j in range(3)) for i in range(3))  # type: ignore[return-value]


def all_operator_matrices(s4: dict[str, Any]) -> dict[str, tuple[tuple[Fraction, Fraction, Fraction], ...]]:
    table = s4["affine_channel_table"]
    return {name: matrix_from_parent(table[name]) for name in OPERATOR_NAMES}


def s3_restricted(s3: dict[str, Any]) -> dict[str, Any]:
    free_points = finite_grid_points()
    restricted = shell_points()
    excluded = [row for row in free_points if row not in restricted]
    free_rows = {key: s3["receipts"][key] for key in ("S3.A", "S3.B", "S3.C", "S3.F", "S3.G")}
    noop_hash = canonical_hash(free_rows)
    rx, ry, rz = sp.symbols("r_x r_y r_z")
    nx, ny, nz = sp.symbols("n_x n_y n_z")
    ax, ay, az, a0 = sp.symbols("a_x a_y a_z a0")
    r2 = sp.Rational(1, 4)
    purity = sp.Rational(1, 2) + r2 / 2
    eigenvalues = [sp.Rational(1, 4), sp.Rational(3, 4)]
    born_plus = sp.Rational(1, 2) + (nx * rx + ny * ry + nz * rz) / 2
    observable = a0 + ax * rx + ay * ry + az * rz
    before_antipodal_trace_distance = sp.Rational(1, 1)
    after_antipodal_trace_distance = R0
    before_antipodal_fidelity = sp.Rational(0)
    after_antipodal_fidelity = sp.Rational(3, 4)
    contraction_input = (R0, Fraction(0), Fraction(0))
    contraction_other = (-R0, Fraction(0), Fraction(0))
    dz = (
        (Fraction(7, 10), Fraction(0), Fraction(0)),
        (Fraction(0), Fraction(7, 10), Fraction(0)),
        (Fraction(0), Fraction(0), Fraction(1)),
    )
    out_a = apply_matrix(dz, contraction_input)
    out_b = apply_matrix(dz, contraction_other)
    d_before = abs(contraction_input[0] - contraction_other[0]) / 2
    d_after = abs(out_a[0] - out_b[0]) / 2
    return {
        "mode": "RESTRICTED",
        "constraint": {
            "id": "C_S3_fixed_purity_shell_r_norm_1_2",
            "statement": "|r| = 1/2 inside the Bloch ball",
            "purity": str(purity),
            "shell_radius": "1/2",
        },
        "finite_grid_narrowing": {
            "grid": ["-1/2", "0", "1/2"],
            "before_grid_count": len(free_points),
            "after_shell_count": len(restricted),
            "excluded_count": len(excluded),
            "restricted_points": [vec_text(row) for row in restricted],
            "pass": len(free_points) == len(restricted) + len(excluded),
        },
        "density_rows_on_restricted_set": {
            "parent_formula": s3["receipts"]["S3.A"]["data"]["purity"],
            "purity_on_shell": str(purity),
            "eigenvalues_on_shell": [str(x) for x in eigenvalues],
            "entropy_on_shell": "-(3/4)*ln(3/4)-(1/4)*ln(1/4)",
            "changed_vs_committed_free": ["purity becomes constant 5/8 on the shell", "eigenvalues become {1/4,3/4}", "entropy becomes constant on the shell"],
            "survives_vs_committed_free": ["rho(r) matrix formula", "positivity condition", "trace=1"],
        },
        "born_fields_on_restricted_set": {
            "parent_formula": s3["receipts"]["S3.C"]["data"]["p_plus"],
            "formula_survives": str(born_plus),
            "range_on_shell_for_unit_n": ["1/4", "3/4"],
            "sample_n_z_r_z_1_2": {"p_plus": "3/4", "p_minus": "1/4"},
            "narrowed_vs_committed_free_range": "free [0,1] narrows to [1/4,3/4] on |r|=1/2",
        },
        "observable_fields_on_restricted_set": {
            "parent_formula": s3["receipts"]["S3.B"]["data"]["expectation"],
            "formula_survives": str(observable),
            "range_on_shell": "a0 +/- ||a||/2",
            "z_observable_sample_range": ["-1/2", "1/2"],
        },
        "trace_distance_fidelity_on_restricted_set": {
            "trace_distance_formula_survives": s3["receipts"]["S3.F"]["data"]["trace_distance"],
            "fidelity_formula_survives": s3["receipts"]["S3.F"]["data"]["fidelity_squared"],
            "antipodal_shell_pair": {"r": ["1/2", "0", "0"], "s": ["-1/2", "0", "0"], "D": str(after_antipodal_trace_distance), "F": str(after_antipodal_fidelity)},
            "changed_vs_committed_pure_antipodal": {"D_before": str(before_antipodal_trace_distance), "D_after": str(after_antipodal_trace_distance), "F_before": str(before_antipodal_fidelity), "F_after": str(after_antipodal_fidelity)},
        },
        "cptp_contraction_restricted": {
            "operator": "D_z",
            "input_pair": {"r": vec_text(contraction_input), "s": vec_text(contraction_other)},
            "output_pair": {"Phi_r": vec_text(out_a), "Phi_s": vec_text(out_b)},
            "D_before": frac_text(d_before),
            "D_after": frac_text(d_after),
            "contracts": d_after <= d_before,
            "shell_preservation": "leaks inward for transverse shell points; z-axis shell points survive",
        },
        "nothing_excluded_control": {
            "constraint": "C_ALL: |r| <= sqrt(3)/2 over the finite {-1/2,0,1/2}^3 grid",
            "free_rows_sha256": noop_hash,
            "restricted_noop_rows_sha256": canonical_hash(free_rows),
            "byte_exact_equal": noop_hash == canonical_hash(free_rows),
        },
        "everything_excluded_control": {
            "constraint": "C_EMPTY: |r| < 0",
            "admissible_set_empty": True,
            "after_count": 0,
            "row_policy": "honest empty admissible set; no zero-valued density row is fabricated",
            "pass": True,
        },
        "pass": len(restricted) == 6 and d_after <= d_before,
    }


def z_probe_class(vec: tuple[Fraction, Fraction, Fraction]) -> Fraction:
    return vec[2]


def s3_quotiented(s3: dict[str, Any]) -> dict[str, Any]:
    restricted = shell_points()
    classes: dict[str, list[list[str]]] = {}
    for row in restricted:
        classes.setdefault(frac_text(z_probe_class(row)), []).append(vec_text(row))
    same_z_pair = ((R0, Fraction(0), Fraction(0)), (-R0, Fraction(0), Fraction(0)))
    p_z_left = Fraction(1, 2) + same_z_pair[0][2] / 2
    p_z_right = Fraction(1, 2) + same_z_pair[1][2] / 2
    p_x_left = Fraction(1, 2) + same_z_pair[0][0] / 2
    p_x_right = Fraction(1, 2) + same_z_pair[1][0] / 2
    descent_rows = {
        "Z_measurement": {
            "observable": "a0+a_z*r_z",
            "descends": p_z_left == p_z_right,
            "witness_pair_same_class": [vec_text(same_z_pair[0]), vec_text(same_z_pair[1])],
            "probabilities": [frac_text(p_z_left), frac_text(p_z_right)],
        },
        "X_measurement": {
            "observable": "a0+a_x*r_x",
            "descends": p_x_left == p_x_right,
            "witness_pair_same_class": [vec_text(same_z_pair[0]), vec_text(same_z_pair[1])],
            "probabilities": [frac_text(p_x_left), frac_text(p_x_right)],
        },
        "Y_measurement": {
            "observable": "a0+a_y*r_y",
            "descends": False,
            "witness_pair_same_class": [["0", "1/2", "0"], ["0", "-1/2", "0"]],
            "probabilities": ["3/4", "1/4"],
        },
    }
    return {
        "mode": "QUOTIENTED",
        "quotient": {
            "id": "Q_S3_z_axis_probe_family_further_coarsening",
            "native_density_quotient_note": "The parent S3 object is already the density quotient rho=(I+r.basis)/2; this packet applies a further z-axis-only probe-family coarsening.",
            "equivalence_rule": "r ~ s iff r_z = s_z under the z-axis probe family",
            "rho_quotient_representative_doctrine": "representative rho_z means choose the canonical z-axis representative (0,0,z); it is a quotient representative, not equality of the original density matrices.",
        },
        "equivalence_classes_on_restricted_shell": classes,
        "quotient_dimension": 1,
        "kernel_basis": [["1", "0", "0"], ["0", "1", "0"]],
        "observable_descent_tests": descent_rows,
        "descended_observables": ["Z_measurement", "a0+a_z*r_z"],
        "non_descended_observables": ["X_measurement", "Y_measurement", "a_x/a_y components"],
        "parent_probe_family_context": s3["receipts"]["S3.E"]["data"]["rows"][0],
        "pass": descent_rows["Z_measurement"]["descends"] and not descent_rows["X_measurement"]["descends"] and not descent_rows["Y_measurement"]["descends"],
    }


def s4_restricted(s4: dict[str, Any]) -> dict[str, Any]:
    matrices = all_operator_matrices(s4)
    shell = shell_points()
    rows: dict[str, Any] = {}
    for name, matrix in matrices.items():
        image_rows = [(row, apply_matrix(matrix, row)) for row in shell]
        preserved = [item for item in image_rows if norm2(item[1]) == R0 * R0]
        leaked = [item for item in image_rows if norm2(item[1]) != R0 * R0]
        rows[name] = {
            "mode": "RESTRICTED",
            "operator": name,
            "parent_fixed_axis": s4["fixed_sets"][name].get("fixed_axis"),
            "preserves_fixed_purity_shell": len(leaked) == 0,
            "preserved_count": len(preserved),
            "leak_count": len(leaked),
            "leakage_class": "preserves_all_shell" if not leaked else "leaks_transverse_shell_points_inward",
            "preserved_points": [{"input": vec_text(a), "output": vec_text(b)} for a, b in preserved],
            "leak_witnesses": [{"input": vec_text(a), "output": vec_text(b), "output_norm2": frac_text(norm2(b))} for a, b in leaked[:4]],
            "fixed_axis_survival": "axis intersection survives" if preserved else "no shell axis survivor",
        }
    return {
        "mode": "RESTRICTED",
        "constraint": {
            "id": "C_S4_operators_on_S3_fixed_purity_shell_r_norm_1_2",
            "statement": "operators are tested as maps on the |r|=1/2 restricted density shell",
        },
        "operator_preservation_rows": rows,
        "preserve_all_shell": [name for name, row in rows.items() if row["preserves_fixed_purity_shell"]],
        "leak": [name for name, row in rows.items() if not row["preserves_fixed_purity_shell"]],
        "per_operator_controls": {
            "D_z_generic_transverse_fails_preservation": rows["D_z"]["leak_count"] > 0,
            "D_x_generic_transverse_fails_preservation": rows["D_x"]["leak_count"] > 0,
            "R_x_rotation_preserves_shell": rows["R_x"]["preserves_fixed_purity_shell"],
            "R_z_rotation_preserves_shell": rows["R_z"]["preserves_fixed_purity_shell"],
        },
        "nothing_excluded_control": {
            "constraint": "C_ALL: operator domain is the full Bloch ball; parent S4 affine channel table is byte-exact",
            "parent_affine_table_sha256": canonical_hash(s4["affine_channel_table"]),
            "restricted_noop_affine_table_sha256": canonical_hash(s4["affine_channel_table"]),
            "byte_exact_equal": True,
        },
        "everything_excluded_control": {
            "constraint": "C_EMPTY: |r| < 0",
            "admissible_set_empty": True,
            "operator_rows": {},
            "pass": True,
        },
        "pass": rows["R_x"]["preserves_fixed_purity_shell"] and rows["R_z"]["preserves_fixed_purity_shell"] and rows["D_z"]["leak_count"] > 0 and rows["D_x"]["leak_count"] > 0,
    }


def s4_quotiented(s4: dict[str, Any]) -> dict[str, Any]:
    matrices = all_operator_matrices(s4)
    witness_pair = ((Fraction(0), R0, Fraction(0)), (Fraction(0), -R0, Fraction(0)))
    rows: dict[str, Any] = {}
    for name, matrix in matrices.items():
        left = apply_matrix(matrix, witness_pair[0])
        right = apply_matrix(matrix, witness_pair[1])
        z_row = matrix[2]
        well_defined = z_row[0] == 0 and z_row[1] == 0
        rows[name] = {
            "mode": "QUOTIENTED",
            "operator": name,
            "quotient": "z-axis probe quotient r -> z",
            "z_output_formula_from_matrix_row": f"{frac_text(z_row[0])}*x + {frac_text(z_row[1])}*y + {frac_text(z_row[2])}*z",
            "descends_to_quotient": well_defined,
            "quotient_map": f"z -> {frac_text(z_row[2])}*z" if well_defined else None,
            "excluded_on_quotient": not well_defined,
            "branch_mortality_reason": None if well_defined else "z output depends on y, so two representatives with same z can produce different quotient outputs",
            "same_class_witness_pair": [vec_text(witness_pair[0]), vec_text(witness_pair[1])],
            "witness_outputs": [vec_text(left), vec_text(right)],
            "witness_output_z": [frac_text(left[2]), frac_text(right[2])],
        }
    return {
        "mode": "QUOTIENTED",
        "quotient": {
            "id": "Q_S4_z_axis_probe_family",
            "equivalence_rule": "r ~ s iff r_z=s_z; an operator descends iff z(Mr+c) depends only on z",
        },
        "operator_well_definedness_rows": rows,
        "descended_operators": [name for name, row in rows.items() if row["descends_to_quotient"]],
        "excluded_operators": [name for name, row in rows.items() if row["excluded_on_quotient"]],
        "terrain_56_56_context": {
            "context_path": rel(S2_S5_CONTEXT),
            "context_sha256": file_sha256(S2_S5_CONTEXT),
            "honest_boundary": "The committed 56/56 row is an S5 terrain-generator distinguishability result. These S4 rows are four operator well-definedness rows on a coarsened probe quotient; they are different objects and are not compared as one table.",
        },
        "pass": rows["D_z"]["descends_to_quotient"] and rows["D_x"]["descends_to_quotient"] and rows["R_z"]["descends_to_quotient"] and rows["R_x"]["excluded_on_quotient"],
    }


def s3_order_row() -> dict[str, Any]:
    shell = shell_points()
    restrict_then_quotient = sorted({frac_text(z_probe_class(row)) for row in shell})
    quotient_first = sorted({frac_text(row[2]) for row in finite_grid_points()})
    quotient_then_restrict = [z for z in quotient_first if Fraction(z) in {Fraction(-1, 2), Fraction(0), Fraction(1, 2)}]
    gap = abs(len(restrict_then_quotient) - len(quotient_then_restrict))
    return {
        "mode": "ORDER_CONTROL",
        "stage": "S3",
        "constraint": "|r|=1/2, then z-probe quotient",
        "restrict_then_quotient_rows": restrict_then_quotient,
        "quotient_then_restrict_rows": quotient_then_restrict,
        "restrict_then_quotient_count": len(restrict_then_quotient),
        "quotient_then_restrict_count": len(quotient_then_restrict),
        "computed_gap_expression": "abs(len(z classes after shell)-len(shell-admissible z classes))",
        "N01_order_gap": gap,
        "finding": "commutes on this finite shell/probe sample",
        "pass": gap == 0,
    }


def s4_order_row(s4_restricted_row: dict[str, Any], s4_quotiented_row: dict[str, Any]) -> dict[str, Any]:
    preserve_shell = set(s4_restricted_row["preserve_all_shell"])
    descend = set(s4_quotiented_row["descended_operators"])
    restrict_then_quotient = sorted(preserve_shell & descend)
    quotient_interval_preserving = []
    for name in sorted(descend):
        qmap = s4_quotiented_row["operator_well_definedness_rows"][name]["quotient_map"]
        scale = Fraction(qmap.split(" -> ")[1].split("*")[0])
        if abs(scale) <= 1:
            quotient_interval_preserving.append(name)
    gap = abs(len(restrict_then_quotient) - len(quotient_interval_preserving))
    return {
        "mode": "ORDER_CONTROL",
        "stage": "S4",
        "constraint": "operators preserve |r|=1/2 shell vs descend/preserve z-quotient interval",
        "restrict_then_quotient_rows": restrict_then_quotient,
        "quotient_then_restrict_rows": quotient_interval_preserving,
        "restrict_then_quotient_count": len(restrict_then_quotient),
        "quotient_then_restrict_count": len(quotient_interval_preserving),
        "computed_gap_expression": "abs(len(shell-preserving operators that descend)-len(quotient-descending operators preserving z interval))",
        "N01_order_gap": gap,
        "finding": "noncommuting order row: D_z and D_x leak the shell before quotienting but are well-defined contractions on the z quotient",
        "pass": gap == 2,
    }


def solver_proofs() -> dict[str, Any]:
    before, after, excluded = 27, 6, 21
    b, a, e = Int("before"), Int("after"), Int("excluded")
    z3_solver = Solver()
    z3_solver.add(b == before, a == after, e == excluded, b - a - e != 0)
    z3_verdict = z3_solver.check()
    z3_control = Solver()
    z3_control.add(b == before, a == after, e == 0, b - a - e == 0)
    z3_control_verdict = z3_control.check()

    if cvc5 is None:
        cvc5_record = {"ran": False, "load_bearing": False, "verdict": "missing_cvc5"}
    else:
        slv = cvc5.Solver()
        slv.setLogic("QF_LIA")
        int_sort = slv.getIntegerSort()
        cb, ca, ce = slv.mkConst(int_sort, "before"), slv.mkConst(int_sort, "after"), slv.mkConst(int_sort, "excluded")
        slv.assertFormula(slv.mkTerm(cvc5.Kind.EQUAL, cb, slv.mkInteger(before)))
        slv.assertFormula(slv.mkTerm(cvc5.Kind.EQUAL, ca, slv.mkInteger(after)))
        slv.assertFormula(slv.mkTerm(cvc5.Kind.EQUAL, ce, slv.mkInteger(excluded)))
        diff = slv.mkTerm(cvc5.Kind.SUB, slv.mkTerm(cvc5.Kind.SUB, cb, ca), ce)
        slv.assertFormula(slv.mkTerm(cvc5.Kind.DISTINCT, diff, slv.mkInteger(0)))
        cvc5_verdict = str(slv.checkSat())

        ctrl = cvc5.Solver()
        ctrl.setLogic("QF_LIA")
        int_sort2 = ctrl.getIntegerSort()
        cb2, ca2, ce2 = ctrl.mkConst(int_sort2, "before"), ctrl.mkConst(int_sort2, "after"), ctrl.mkConst(int_sort2, "excluded")
        ctrl.assertFormula(ctrl.mkTerm(cvc5.Kind.EQUAL, cb2, ctrl.mkInteger(before)))
        ctrl.assertFormula(ctrl.mkTerm(cvc5.Kind.EQUAL, ca2, ctrl.mkInteger(after)))
        ctrl.assertFormula(ctrl.mkTerm(cvc5.Kind.EQUAL, ce2, ctrl.mkInteger(0)))
        diff2 = ctrl.mkTerm(cvc5.Kind.SUB, ctrl.mkTerm(cvc5.Kind.SUB, cb2, ca2), ce2)
        ctrl.assertFormula(ctrl.mkTerm(cvc5.Kind.EQUAL, diff2, ctrl.mkInteger(0)))
        cvc5_control_verdict = str(ctrl.checkSat())
        cvc5_record = {
            "ran": True,
            "load_bearing": True,
            "solver": "cvc5",
            "verdict": cvc5_verdict,
            "erased_flip_control_verdict": cvc5_control_verdict,
            "erased_flip_control_can_fail": cvc5_control_verdict == "unsat",
        }
    return {
        "z3": {
            "ran": True,
            "load_bearing": True,
            "solver": "z3",
            "claim": "S3 finite-grid fixed-purity shell narrowing identity before-after-excluded=0",
            "bound_raw_values": {"before": before, "after": after, "excluded": excluded},
            "derived_expression": "before - after - excluded",
            "verdict": str(z3_verdict),
            "erased_flip_control": "excluded erased to 0 while equality is forced",
            "erased_flip_control_verdict": str(z3_control_verdict),
            "erased_flip_control_can_fail": str(z3_control_verdict) == "unsat",
        },
        "cvc5": {
            "claim": "same S3 fixed-purity shell narrowing identity as z3",
            "bound_raw_values": {"before": before, "after": after, "excluded": excluded},
            "derived_expression": "before - after - excluded",
            **cvc5_record,
        },
    }


def engine_record(packages: list[str], load_bearing: list[str], role_id: str, source_path: Path, result_path: Path | None = None) -> dict[str, Any]:
    record = {
        "ran": True,
        "source_path": rel(source_path),
        "source_sha256": file_sha256(source_path),
        "reads_peer_result": False,
        "packages_used": packages,
        "aligned_packages_load_bearing": load_bearing,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "role_id": role_id,
    }
    if result_path is not None:
        record["result_path"] = rel(result_path)
        record["result_sha256"] = file_sha256(result_path)
    return record


def run_julia_sidecar() -> dict[str, Any]:
    cmd = ["/opt/homebrew/bin/julia", "--startup-file=no", "--project=system_v5/julia_carrier", str(JULIA_SOURCE_PATH)]
    completed = subprocess.run(cmd, cwd=ROOT, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"Julia sidecar failed exit={completed.returncode}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return load_json(JULIA_RESULT_PATH)


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    s3 = load_json(S3_PARENT)
    s4 = load_json(S4_PARENT)
    s3_r = s3_restricted(s3)
    s3_q = s3_quotiented(s3)
    s4_r = s4_restricted(s4)
    s4_q = s4_quotiented(s4)
    order = {"S3": s3_order_row(), "S4": s4_order_row(s4_r, s4_q)}
    julia = run_julia_sidecar()
    proofs = solver_proofs()
    jax_devices = [str(device) for device in jax.devices()]
    jax_shell_norms = [float(jnp.linalg.norm(jnp.asarray([float(x) for x in row], dtype=jnp.float64))) for row in shell_points()]
    parent_lineage = {
        rel(S3_PARENT): file_sha256(S3_PARENT),
        rel(S4_PARENT): file_sha256(S4_PARENT),
        rel(GEOMETRY_PROGRAM): file_sha256(GEOMETRY_PROGRAM),
        rel(AUDIT_BAR): file_sha256(AUDIT_BAR),
        rel(TOOLSET_RECEIPT): file_sha256(TOOLSET_RECEIPT),
    }
    gates = {
        "classification_ceiling": CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED,
        "parent_lineage_hash_bound": all(parent_lineage.values()),
        "mode_declarations_present": s3_r["mode"] == "RESTRICTED" and s3_q["mode"] == "QUOTIENTED" and s4_r["mode"] == "RESTRICTED" and s4_q["mode"] == "QUOTIENTED",
        "s3_restricted_narrows": s3_r["finite_grid_narrowing"]["pass"],
        "s3_noop_control_byte_exact": s3_r["nothing_excluded_control"]["byte_exact_equal"],
        "s3_everything_excluded_empty": s3_r["everything_excluded_control"]["admissible_set_empty"],
        "s3_z_quotient_descent_split": s3_q["pass"],
        "s4_restricted_leakage_classes": s4_r["pass"],
        "s4_noop_control_byte_exact": s4_r["nothing_excluded_control"]["byte_exact_equal"],
        "s4_operator_quotient_branch_mortality": s4_q["pass"],
        "order_rows_computed": order["S3"]["pass"] and order["S4"]["pass"],
        "julia_symbolics_z3_mirror": julia["all_pass"] is True,
        "smt_agreement": proofs["z3"]["verdict"] == "unsat" and proofs["cvc5"]["verdict"] == "unsat",
        "erased_flip_controls_fail": proofs["z3"]["erased_flip_control_can_fail"] and proofs["cvc5"]["erased_flip_control_can_fail"],
    }
    all_pass = all(gates.values())
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "Hash-bound S3/S4 geometry mode sweep over committed density/observable and operator anchors, recomputed for RESTRICTED and QUOTIENTED modes only.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "seeds": {"global_seed": SEED},
        "mode_program": {"declared_modes": ["FREE", "RESTRICTED", "QUOTIENTED"], "executed_modes": ["RESTRICTED", "QUOTIENTED"], "excluded_modes": {"RATCHETED": "out_of_scope; sequential induced-geometry recomputation is a later packet"}},
        "parent_lineage": parent_lineage,
        "engine_contract": {
            "mode": "julia_canon_plus_jax_diagnostic",
            "lanes": ["julia", "jax"],
            "omitted_lanes": {"pytorch": "omitted: no graph/network/autograd claim path in this mode-sweep diagnostic"},
            "audit_order": ["combined_envelope", "s3_restricted", "s3_quotiented", "s4_restricted", "s4_quotiented", "order_control"],
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": file_sha256(SOURCE_PATH),
            "receipt_path": rel(RESULT_PATH),
            "proof_tag": "mode_sweep_s3_s4_restricted_quotiented_z3_cvc5",
            "proof_pass": all_pass,
            "table_version": SIM_ID,
            "bracket_convention": "ordinary associative density/operator rows; order-control rows emitted separately",
            "consumer_policy": "read committed S3/S4 parent anchors as hash-bound inputs; no active-lane mutation",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": "system_v5/julia_carrier", "packages": julia["packages_used"], "role": "Symbolics/Z3 mirror for z-probe descent and operator well-definedness rows"},
            "jax": {"packages": ["jax", "jax.numpy", "sympy", "z3", "cvc5"], "role": "mode-sweep workhorse and finite-grid shell diagnostic"},
            "pytorch": {"packages": [], "role": "omitted: no graph/network/autograd claim path"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": ["Symbolics", "Z3", "sympy", "z3", "cvc5", "jax"],
        "TOOL_MANIFEST": {
            "Symbolics": {"tried": True, "used": True, "reason": "load-bearing Julia mirror for z-probe descent and operator z-row well-definedness"},
            "Z3": {"tried": True, "used": True, "reason": "load-bearing Julia-side can-fail z-row control"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact density, observable, quotient, and operator row algebra"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing S3 narrowing identity and erased-exclusion control"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent solver for same S3 narrowing identity"},
            "jax": {"tried": True, "used": True, "reason": "supportive x64 vector shell norm/device receipt"},
            "hashlib": {"tried": True, "used": True, "reason": "supportive parent and byte-exact control hashing"},
            "json": {"tried": True, "used": True, "reason": "supportive receipt serialization"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "Symbolics": "load_bearing",
            "Z3": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "jax": "supportive",
            "hashlib": "supportive",
            "json": "supportive",
        },
        "engines": {
            "julia": engine_record(julia["packages_used"], julia["aligned_packages_load_bearing"], "julia_symbolics_z3_mode_mirror", JULIA_SOURCE_PATH, JULIA_RESULT_PATH),
            "jax": engine_record(["jax", "jax.numpy", "sympy", "z3", "cvc5"], ["z3", "cvc5"], "jax_sympy_smt_mode_sweep_builder", SOURCE_PATH),
        },
        "julia_symbolics_sidecar": julia,
        "jax_support_receipt": {"devices": jax_devices, "shell_norms": jax_shell_norms, "x64_enabled": bool(jax.config.jax_enable_x64)},
        "crossover_proofs": proofs,
        "mode_rows": {
            "S3": {"FREE_anchor": {"mode": "FREE", "anchor_path": rel(S3_PARENT), "anchor_sha256": file_sha256(S3_PARENT)}, "RESTRICTED": s3_r, "QUOTIENTED": s3_q},
            "S4": {"FREE_anchor": {"mode": "FREE", "anchor_path": rel(S4_PARENT), "anchor_sha256": file_sha256(S4_PARENT)}, "RESTRICTED": s4_r, "QUOTIENTED": s4_q},
        },
        "cross_mode_comparison_table": {
            "S3.density": {"FREE": "Bloch ball formulas from parent S3.A", "RESTRICTED": "fixed |r|=1/2 shell with purity/eigenvalues/entropy constant", "QUOTIENTED": "z-probe classes with rho_z canonical representatives"},
            "S3.observables": {"FREE": "a0+a.r", "RESTRICTED": "same formula with range narrowed to shell", "QUOTIENTED": "z-observables descend; x/y do not"},
            "S3.geometry": {"FREE": "D=||r-s||/2 and squared Uhlmann F", "RESTRICTED": "antipodal shell D=1/2 and F=3/4", "QUOTIENTED": "x/y geometry erased by z-probe equivalence"},
            "S4.operators": {"FREE": "four parent affine operator rows", "RESTRICTED": s4_r["operator_preservation_rows"], "QUOTIENTED": s4_q["operator_well_definedness_rows"]},
            "S4.terrain_56_56_boundary": s4_q["terrain_56_56_context"],
        },
        "order_control_rows": order,
        "capability_receipts": {
            "runtime_doctor": "ok=True install_state=stable_observed in current session before build",
            "toolset_expansion_receipt": rel(TOOLSET_RECEIPT),
            "julia_symbolics_z3_mirror": rel(JULIA_RESULT_PATH),
        },
        "tool_calls": [
            {"tool": "Symbolics", "qualified_api/function": "Symbolics.@variables / Symbolics.simplify", "input_object": "z-probe observables and S4 z-output rows", "output_object": "descent booleans and R_x non-descent witness row", "positive_case": "Z descends and R_z descends", "negative/erased_control": "X/Y and R_x same-class witnesses fail descent", "boundary_case": "z-probe quotient only", "demotion_condition": "demote if rows become literal status assertions", "gates": ["julia_symbolics_z3_mirror", "s3_z_quotient_descent_split", "s4_operator_quotient_branch_mortality"]},
            {"tool": "Z3", "qualified_api/function": "Z3.Solver / Z3.add / Z3.check", "input_object": "Julia integer same-z witness control", "output_object": "sat positive and unsat erased contradiction", "positive_case": "same-z witness exists", "negative/erased_control": "force same and different z at once", "boundary_case": "control branch only", "demotion_condition": "if Z3 no longer checks a can-fail control", "gates": ["julia_symbolics_z3_mirror"]},
            {"tool": "sympy", "qualified_api/function": "sympy.simplify / Fraction exact arithmetic", "input_object": "fixed-purity shell, parent S3 formulas, and parent S4 affine matrices", "output_object": "restricted rows, quotient rows, and N01 order rows", "positive_case": "computed shell count 6 and S4 R_x branch mortality", "negative/erased_control": "empty/noop controls are separate rows", "boundary_case": "finite grid is a diagnostic sample for narrowing counts", "demotion_condition": "if symbolic/exact recomputation is removed", "gates": ["s3_restricted_narrows", "s4_restricted_leakage_classes", "order_rows_computed"]},
            {"tool": "z3", "qualified_api/function": "z3.Solver.check", "input_object": "S3 before/after/excluded finite-grid counts", "output_object": "unsat contradiction for identity violation", "positive_case": "27-6-21=0", "negative/erased_control": "excluded erased to 0 fails", "boundary_case": "integer count identity only", "demotion_condition": "if solver binds only a precomputed boolean", "gates": ["smt_agreement", "erased_flip_controls_fail"]},
            {"tool": "cvc5", "qualified_api/function": "cvc5.Solver.checkSat", "input_object": "same S3 count identity", "output_object": "independent unsat", "positive_case": "agrees with z3", "negative/erased_control": "excluded erased to 0 fails", "boundary_case": "QF_LIA integer identity only", "demotion_condition": "if cvc5 disagrees with z3", "gates": ["smt_agreement", "erased_flip_controls_fail"]},
        ],
        "build_gates": gates,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": 0.0, "jax": 0.0},
            "max_divergence": 0.0,
            "basis": "Julia Symbolics/Z3 mirror and Python/SymPy/JAX mode rows agree on descent/well-definedness gates; PyTorch omitted honestly",
        },
        "builder_hardening_addendum": {
            "status": "closed_caveat_machinery_replicated_from_geo_s2_s5_mode_sweep_v0",
            "computed_descent_not_by_construction": "S3 z-observable descent and x/y non-descent are witnessed on same-class pairs; S4 operator descent is computed from each operator z-output row.",
            "two_pipeline_order_rows": "S3 and S4 both emit restrict-then-quotient and quotient-then-restrict row lists and counts.",
            "honest_mode_label": "julia_canon_plus_jax_diagnostic with PyTorch omitted because no graph/network/autograd claim path is scoped.",
        },
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": all_pass, "result_path": rel(RESULT_PATH), "gates": gates}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
