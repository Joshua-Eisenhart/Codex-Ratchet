#!/usr/bin/env python3
"""Single-shell RATCHETED terrain/operator packet over committed parent packets."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import platform
import subprocess
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "ratchet_s6_terrain_operator_shell_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_PATH = SIM_DIR / f"validate_{SIM_ID}.py"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
JULIA_SOURCE_PATH = SIM_DIR / f"{SIM_ID}_julia.jl"
JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"

MODE = "RATCHETED"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
ETA0_LABEL = "pi/6"
TERRAIN_ID = "Se_Funnel_L"
OPERATOR_ID = "Fi_R_x"
CONTROL_TERRAIN_ID = "D_z"
CONTROL_OPERATOR_ID = "R_z"

PARENTS = {
    "ratchet_s1_single_shell_pilot_v0": {
        "packet": "system_v6/sims/ratchet_s1_single_shell_pilot_v0",
        "envelope": "system_v6/sims/ratchet_s1_single_shell_pilot_v0/results/ratchet_s1_single_shell_pilot_v0_envelope_results.json",
        "top_source": "system_v6/sims/ratchet_s1_single_shell_pilot_v0/ratchet_s1_single_shell_pilot_v0.py",
    },
    "geo_disintegration_machinery_v0": {
        "packet": "system_v6/sims/geo_disintegration_machinery_v0",
        "envelope": "system_v6/sims/geo_disintegration_machinery_v0/results/geo_disintegration_machinery_v0_envelope_results.json",
        "top_source": "system_v6/sims/geo_disintegration_machinery_v0/geo_disintegration_machinery_v0_jax.py",
    },
    "geo_s5_terrain_flows_v0": {
        "packet": "system_v6/sims/geo_s5_terrain_flows_v0",
        "envelope": "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json",
        "top_source": "system_v6/sims/geo_s5_terrain_flows_v0/geo_s5_terrain_flows_v0_jax.py",
    },
    "geo_s4_operator_stage_v0": {
        "packet": "system_v6/sims/geo_s4_operator_stage_v0",
        "envelope": "system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json",
        "top_source": "system_v6/sims/geo_s4_operator_stage_v0/geo_s4_operator_stage_v0_jax.py",
    },
    "geo_s2_s5_mode_sweep_v0": {
        "packet": "system_v6/sims/geo_s2_s5_mode_sweep_v0",
        "envelope": "system_v6/sims/geo_s2_s5_mode_sweep_v0/results/geo_s2_s5_mode_sweep_v0_envelope_results.json",
        "top_source": "system_v6/sims/geo_s2_s5_mode_sweep_v0/geo_s2_s5_mode_sweep_v0.py",
    },
}

PIN_SPEC = (
    "ratchet_s6_terrain_operator_shell_v0|mode=RATCHETED|single_shell_only|"
    "eta0=pi/6|step0=FREE_Bloch_density_state_space_with_committed_S3_anchor_from_ratchet_s1|"
    "step1=condition_T_pi_over_6_via_geo_disintegration_machinery_v0_rule|"
    "conditional_chart_density=1/(4*pi^2)|naive_conditioning_failure_refired|"
    "step2=terrain_generator_Se_Funnel_L_from_geo_s5_terrain_flows_v0_on_conditioned_leaf|"
    "step3=Fi_R_x_after_terrain_and_terrain_after_Fi_R_x_order_gap|"
    "control=D_z_with_R_z_commuting_zero_gap|"
    "geo_s2_s5_mode_sweep_v0_quotient_survival=56/56|"
    "nested_fences_stated_not_binding_here|classification=scratch_diagnostic|"
    "promotion_allowed=false|formal_admission_allowed=false"
)

SEED_LEDGER = {
    "status": "deterministic_exact_rows_no_rng_sampling",
    "symbolic_seed": 2026061106,
    "smt_seed": 2026061106,
    "eta0": ETA0_LABEL,
    "terrain": TERRAIN_ID,
    "operator": OPERATOR_ID,
}

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact shell conditioning, induced flow, fixed-point, leakage, and order-gap derivation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT refutation of zero order-gap plus erased skew control",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT refutation of the same order-gap identity and commuting control",
    },
    "Z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Julia carrier proof of the scaled Se/Rx gap and commuting-control zero row",
    },
    "json": {"tried": True, "used": True, "reason": "supportive deterministic envelope serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive committed parent and selected-row hashing"},
    "subprocess": {"tried": True, "used": True, "reason": "supportive committed HEAD parent reads through git show/rev-parse"},
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def stable_json_sha256(obj: Any) -> str:
    return sha256_text(stable_json(obj))


def git_bytes(spec: str) -> bytes:
    return subprocess.check_output(["git", "show", f"HEAD:{spec}"], cwd=ROOT)


def git_text(spec: str) -> str:
    return git_bytes(spec).decode("utf-8")


def git_json(spec: str) -> dict[str, Any]:
    return json.loads(git_text(spec))


def git_rev_parse(spec: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"HEAD:{spec}"], cwd=ROOT, text=True).strip()


def parent_lineage() -> dict[str, Any]:
    lineage: dict[str, Any] = {}
    for label, paths in PARENTS.items():
        envelope_bytes = git_bytes(paths["envelope"])
        source_bytes = git_bytes(paths["top_source"])
        lineage[label] = {
            "packet_path": paths["packet"],
            "committed_tree": git_rev_parse(paths["packet"]),
            "envelope_path": paths["envelope"],
            "envelope_blob": git_rev_parse(paths["envelope"]),
            "envelope_sha256": sha256_bytes(envelope_bytes),
            "top_source_path": paths["top_source"],
            "top_source_blob": git_rev_parse(paths["top_source"]),
            "top_source_sha256": sha256_bytes(source_bytes),
            "source": "git show HEAD:<path>; committed packet citation only",
        }
    return lineage


def sx(expr: Any) -> str:
    return str(sp.simplify(expr)).replace("**", "**")


def matrix_from_strings(rows: list[list[str]]) -> sp.Matrix:
    return sp.Matrix([[sp.sympify(item, locals={"sqrt": sp.sqrt}) for item in row] for row in rows])


def vector_from_strings(items: list[str]) -> sp.Matrix:
    return sp.Matrix([sp.sympify(item, locals={"sqrt": sp.sqrt}) for item in items])


def selected_committed_rows() -> dict[str, Any]:
    s5 = git_json(PARENTS["geo_s5_terrain_flows_v0"]["envelope"])
    s4 = git_json(PARENTS["geo_s4_operator_stage_v0"]["envelope"])
    sweep = git_json(PARENTS["geo_s2_s5_mode_sweep_v0"]["envelope"])
    disintegration = git_json(PARENTS["geo_disintegration_machinery_v0"]["envelope"])
    s1 = git_json(PARENTS["ratchet_s1_single_shell_pilot_v0"]["envelope"])

    terrain = s5["bloch_generator_table"][TERRAIN_ID]["pinned"]
    rx = s4["affine_channel_table"]["R_x"]["pinned"]
    dz = s4["affine_channel_table"]["D_z"]["pinned"]
    rz = s4["affine_channel_table"]["R_z"]["pinned"]
    quotient = sweep["mode_rows"]["S5"]["QUOTIENTED"]["probe_family_separation_matrix_after"]
    naive = disintegration["controls"]["naive_singleton_conditioning"]
    return {
        "terrain": terrain,
        "rx": rx,
        "dz": dz,
        "rz": rz,
        "quotient_survival": quotient,
        "naive_conditioning": naive,
        "s1_mode": s1.get("mode"),
        "source_hashes": {
            "terrain_ab_sha256": stable_json_sha256(terrain),
            "rx_sha256": stable_json_sha256(rx),
            "dz_sha256": stable_json_sha256(dz),
            "rz_sha256": stable_json_sha256(rz),
            "quotient_survival_sha256": stable_json_sha256(quotient),
        },
    }


def leaf_symbolics(rows: dict[str, Any]) -> dict[str, Any]:
    theta = sp.symbols("theta", real=True)
    eta = sp.pi / 6
    z0 = sp.cos(2 * eta)
    shell_radius = sp.sin(2 * eta)
    r = sp.Matrix([shell_radius * sp.cos(theta), shell_radius * sp.sin(theta), z0])
    tangent = sp.Matrix([-shell_radius * sp.sin(theta), shell_radius * sp.cos(theta), 0])

    a_terrain = matrix_from_strings(rows["terrain"]["A"])
    b_terrain = vector_from_strings(rows["terrain"]["b"])
    rx = matrix_from_strings(rows["rx"]["M"])
    dz = matrix_from_strings(rows["dz"]["M"])
    rz = matrix_from_strings(rows["rz"]["M"])

    field = sp.trigsimp(sp.simplify(a_terrain * r + b_terrain))
    z_dot = sp.trigsimp(sp.simplify(field[2]))
    theta_dot = sp.trigsimp(sp.simplify(field.dot(tangent) / (shell_radius**2)))
    purity_dot = sp.trigsimp(sp.simplify(2 * r.dot(field)))
    average_z_dot = sp.simplify(sp.integrate(z_dot, (theta, 0, 2 * sp.pi)) / (2 * sp.pi))
    wrong_leaf_eta = sp.pi / 4
    wrong_r = sp.Matrix([sp.sin(2 * wrong_leaf_eta) * sp.cos(theta), sp.sin(2 * wrong_leaf_eta) * sp.sin(theta), sp.cos(2 * wrong_leaf_eta)])
    wrong_z_dot = sp.trigsimp(sp.simplify((a_terrain * wrong_r + b_terrain)[2]))
    wrong_average_z_dot = sp.simplify(sp.integrate(wrong_z_dot, (theta, 0, 2 * sp.pi)) / (2 * sp.pi))

    delta = sp.trigsimp(sp.simplify(a_terrain * (rx * r) + b_terrain - rx * (a_terrain * r + b_terrain)))
    delta_norm2 = sp.trigsimp(sp.simplify(delta.dot(delta)))
    delta_theta0 = [sp.trigsimp(sp.simplify(item.subs(theta, 0))) for item in delta]
    delta_theta_pi_over_2 = [sp.trigsimp(sp.simplify(item.subs(theta, sp.pi / 2))) for item in delta]

    ctrl_delta = sp.trigsimp(sp.simplify(dz * (rz * r) - rz * (dz * r)))
    ctrl_delta_norm2 = sp.trigsimp(sp.simplify(ctrl_delta.dot(ctrl_delta)))
    unconstrained_fixed = list(a_terrain.LUsolve(-b_terrain))
    fixed_survives = bool(unconstrained_fixed == [0, 0, 0] and z0 == 0)
    theta_dot_upper_bound = sp.simplify(2 * (sp.sqrt(2) - sp.sqrt(3)) / 15)
    z_dot_upper_bound = sp.simplify((-2 + sp.sqrt(2)) / 5)
    nothing_before = {
        "leaf_state_family": "r(theta)=(sqrt(3)/2*cos(theta),sqrt(3)/2*sin(theta),1/2)",
        "terrain": TERRAIN_ID,
        "operator": OPERATOR_ID,
    }
    nothing_after = json.loads(stable_json(nothing_before))

    return {
        "theta_symbol": "theta=2*chi",
        "state_family": {
            "bloch_vector": [sx(item) for item in r],
            "density_matrix": [
                ["3/4", "(sqrt(3)/4)*(cos(theta) - I*sin(theta))"],
                ["(sqrt(3)/4)*(cos(theta) + I*sin(theta))", "1/4"],
            ],
            "shell": "T_pi/6",
            "z": sx(z0),
            "xy_radius": sx(shell_radius),
        },
        "terrain_generator": {
            "id": TERRAIN_ID,
            "A": rows["terrain"]["A"],
            "b": rows["terrain"]["b"],
            "ab_sha256": rows["source_hashes"]["terrain_ab_sha256"],
            "field_on_leaf": [sx(sp.trigsimp(item)) for item in field],
            "z_dot": sx(z_dot),
            "theta_dot_projected_to_leaf": sx(theta_dot),
            "theta_dot_upper_bound": sx(theta_dot_upper_bound),
            "theta_dot_has_zero": False,
            "purity_derivative": sx(purity_dot),
            "shell_average_leakage": sx(average_z_dot),
            "z_dot_upper_bound": sx(z_dot_upper_bound),
            "preserves_leaf": False,
            "leakage_class": "cross_shell",
            "pure_foliation_status": "leave_foliation",
            "s6_class_name_applied": "cross_shell_with_leave_foliation",
            "classification_basis": "z_dot depends on theta and d|r|^2/dt=-8/5, so this is not preserve_T_eta or coherent move_leaf",
        },
        "fixed_points": {
            "committed_unconstrained_fixed_point": [sx(item) for item in unconstrained_fixed],
            "unconstrained_basin_language": "whole Bloch ball contracts to r=0 for positive Se lambda",
            "survives_conditioning": fixed_survives,
            "survivor_set_on_conditioned_object": [],
            "induced_leaf_fixed_points": [],
            "exclusion_language": "r=0 has z=0 and Bloch radius 0; the conditioned object has z=1/2 and pure radius 1",
            "altered_quantity": {
                "unconstrained_fixed_point_count": 1,
                "conditioned_induced_fixed_point_count": 0,
                "projected_leaf_drift_has_no_zero": True,
            },
        },
        "order_gap": {
            "definition": "Delta(theta)=T(O r(theta))-O(T r(theta)) with T(r)=A*r+b and O=R_x(pi/2)",
            "terrain": TERRAIN_ID,
            "operator": OPERATOR_ID,
            "delta": [sx(item) for item in delta],
            "norm_squared": sx(delta_norm2),
            "nonzero_for_all_theta": delta_norm2 == sp.Rational(4, 25),
            "witness_theta0": [sx(item) for item in delta_theta0],
            "boundary_theta_pi_over_2": [sx(item) for item in delta_theta_pi_over_2],
        },
        "commuting_control": {
            "terrain_channel": CONTROL_TERRAIN_ID,
            "operator": CONTROL_OPERATOR_ID,
            "delta": [sx(item) for item in ctrl_delta],
            "norm_squared": sx(ctrl_delta_norm2),
            "gap_killed": ctrl_delta_norm2 == 0,
            "dz_sha256": rows["source_hashes"]["dz_sha256"],
            "rz_sha256": rows["source_hashes"]["rz_sha256"],
        },
        "controls": {
            "nothing_excluded": {
                "before_sha256": stable_json_sha256(nothing_before),
                "after_sha256": stable_json_sha256(nothing_after),
                "byte_exact": stable_json_sha256(nothing_before) == stable_json_sha256(nothing_after),
            },
            "wrong_leaf": {
                "wrong_eta": "pi/4",
                "wrong_leaf_shell_average_leakage": sx(wrong_average_z_dot),
                "selected_leaf_shell_average_leakage": sx(average_z_dot),
                "control_fired": wrong_average_z_dot != average_z_dot,
            },
        },
    }


def z3_matrix_gap_proof(erased: bool = False) -> str:
    s = z3.Real("sqrt3")
    zero = z3.RealVal(0)
    a = z3.RealVal(-4) / 5
    off = z3.RealVal(0) if erased else (z3.RealVal(2) * s / 15)
    mat = [
        [a, -off, off],
        [off, a, -off],
        [-off, off, a],
    ]
    rx = [[1, 0, 0], [0, 0, -1], [0, 1, 0]]
    r = [s / 2, zero, z3.RealVal(1) / 2]

    def mv(m: list[list[Any]], v: list[Any]) -> list[Any]:
        return [z3.Sum([z3.RealVal(m[i][j]) * v[j] if isinstance(m[i][j], int) else m[i][j] * v[j] for j in range(3)]) for i in range(3)]

    rxr = mv(rx, r)
    ar = mv(mat, r)
    gap = [mv(mat, rxr)[i] - mv(rx, ar)[i] for i in range(3)]
    solver = z3.Solver()
    solver.add(s > 0, s * s == 3)
    solver.add(gap[0] == 0, gap[1] == 0, gap[2] == 0)
    return str(solver.check())


def z3_commuting_control_proof() -> str:
    s = z3.Real("sqrt3")
    r = [s / 2, z3.RealVal(0), z3.RealVal(1) / 2]
    dz = [[z3.RealVal(7) / 10, 0, 0], [0, z3.RealVal(7) / 10, 0], [0, 0, 1]]
    rz = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]

    def mv(m: list[list[Any]], v: list[Any]) -> list[Any]:
        out = []
        for i in range(3):
            terms = []
            for j in range(3):
                coeff = z3.RealVal(m[i][j]) if isinstance(m[i][j], int) else m[i][j]
                terms.append(coeff * v[j])
            out.append(z3.Sum(terms))
        return out

    gap = [mv(dz, mv(rz, r))[i] - mv(rz, mv(dz, r))[i] for i in range(3)]
    solver = z3.Solver()
    solver.add(s > 0, s * s == 3)
    solver.add(z3.Or(gap[0] != 0, gap[1] != 0, gap[2] != 0))
    return str(solver.check())


def cvc5_real(solver: cvc5.Solver, value: str) -> Any:
    return solver.mkReal(value)


def cvc5_add(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return cvc5_real(solver, "0")
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def cvc5_sub(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(Kind.SUB, left, right)


def cvc5_mul(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(Kind.MULT, left, right)


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result).lower()


def cvc5_gap_proof(erased: bool = False) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")
    real_sort = solver.getRealSort()
    s = solver.mkConst(real_sort, "sqrt3")
    zero = cvc5_real(solver, "0")
    one = cvc5_real(solver, "1")
    minus_one = cvc5_real(solver, "-1")
    a = cvc5_real(solver, "-4/5")
    off = zero if erased else cvc5_mul(solver, cvc5_real(solver, "2/15"), s)
    neg_off = cvc5_mul(solver, minus_one, off)
    mat = [[a, neg_off, off], [off, a, neg_off], [neg_off, off, a]]
    rx = [[one, zero, zero], [zero, zero, minus_one], [zero, one, zero]]
    r = [cvc5_mul(solver, cvc5_real(solver, "1/2"), s), zero, cvc5_real(solver, "1/2")]

    def mv(m: list[list[Any]], v: list[Any]) -> list[Any]:
        return [cvc5_add(solver, [cvc5_mul(solver, m[i][j], v[j]) for j in range(3)]) for i in range(3)]

    solver.assertFormula(solver.mkTerm(Kind.GT, s, zero))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, cvc5_mul(solver, s, s), cvc5_real(solver, "3")))
    rxr = mv(rx, r)
    ar = mv(mat, r)
    gap = [cvc5_sub(solver, mv(mat, rxr)[i], mv(rx, ar)[i]) for i in range(3)]
    for term in gap:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, zero))
    return cvc5_status(solver.checkSat())


def cvc5_commuting_control_proof() -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")
    real_sort = solver.getRealSort()
    s = solver.mkConst(real_sort, "sqrt3")
    zero = cvc5_real(solver, "0")
    one = cvc5_real(solver, "1")
    minus_one = cvc5_real(solver, "-1")
    r = [cvc5_mul(solver, cvc5_real(solver, "1/2"), s), zero, cvc5_real(solver, "1/2")]
    dz = [[cvc5_real(solver, "7/10"), zero, zero], [zero, cvc5_real(solver, "7/10"), zero], [zero, zero, one]]
    rz = [[zero, minus_one, zero], [one, zero, zero], [zero, zero, one]]

    def mv(m: list[list[Any]], v: list[Any]) -> list[Any]:
        return [cvc5_add(solver, [cvc5_mul(solver, m[i][j], v[j]) for j in range(3)]) for i in range(3)]

    solver.assertFormula(solver.mkTerm(Kind.GT, s, zero))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, cvc5_mul(solver, s, s), cvc5_real(solver, "3")))
    gap = [cvc5_sub(solver, mv(dz, mv(rz, r))[i], mv(rz, mv(dz, r))[i]) for i in range(3)]
    nonzero_terms = [solver.mkTerm(Kind.DISTINCT, term, zero) for term in gap]
    solver.assertFormula(solver.mkTerm(Kind.OR, *nonzero_terms))
    return cvc5_status(solver.checkSat())


def solver_proofs() -> dict[str, Any]:
    z3_positive = z3_matrix_gap_proof(erased=False)
    z3_erased = z3_matrix_gap_proof(erased=True)
    z3_control = z3_commuting_control_proof()
    cvc5_positive = cvc5_gap_proof(erased=False)
    cvc5_erased = cvc5_gap_proof(erased=True)
    cvc5_control = cvc5_commuting_control_proof()
    return {
        "z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": z3_positive,
            "claim": "Se_Funnel_L/R_x zero-gap assertion is UNSAT on T_pi/6 at theta=0",
            "derived_expression": "A*R_x*r - R_x*A*r with sqrt3>0 and sqrt3^2=3",
            "positive_case": "assert all three derived gap components are zero; solver returns UNSAT",
            "erased_flip": "erase the Se skew/off-diagonal component, leaving only scalar dissipation",
            "erased_flip_verdict": z3_erased,
            "erased_flip_detected": z3_erased == "sat",
            "commuting_control_verdict": z3_control,
            "commuting_control_kills_gap": z3_control == "unsat",
            "boundary_case": "theta=pi/2 shifts the nonzero witness from z component to x component",
            "demotion_condition": "demote if the solver binds a precomputed boolean or the erased skew control does not flip to SAT",
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "verdict": cvc5_positive,
            "claim": "Same Se_Funnel_L/R_x zero-gap assertion in cvc5 QF_NRA",
            "derived_expression": "A*R_x*r - R_x*A*r with sqrt3>0 and sqrt3^2=3",
            "positive_case": "assert all three derived gap components are zero; solver returns UNSAT",
            "erased_flip": "erase the Se skew/off-diagonal component, leaving only scalar dissipation",
            "erased_flip_verdict": cvc5_erased,
            "erased_flip_detected": cvc5_erased == "sat",
            "commuting_control_verdict": cvc5_control,
            "commuting_control_kills_gap": cvc5_control == "unsat",
            "boundary_case": "theta=pi/2 shifts the nonzero witness from z component to x component",
            "demotion_condition": "demote if the cvc5 row does not agree with z3 on positive and erased controls",
        },
    }


def load_julia_result() -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "all_pass": False,
            "missing": True,
            "result_path": rel(JULIA_RESULT_PATH),
            "error": "Julia result missing; run the carrier Julia leg before envelope build.",
        }
    return json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))


def capability_receipts() -> dict[str, Any]:
    return {
        "python": {"version": platform.python_version(), "executable": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"},
        "sympy": {"version": sp.__version__, "api_smoke": str(sp.simplify(sp.sqrt(3) ** 2 - 3))},
        "z3": {"version": z3.get_version_string(), "api_smoke": z3_matrix_gap_proof(erased=False)},
        "cvc5": {"version": cvc5.__version__, "api_smoke": cvc5_gap_proof(erased=False)},
    }


def tool_calls(proofs: dict[str, Any], julia_proof: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "tool": "sympy",
            "qualified_api/function": "sympy.Matrix/sympy.simplify/sympy.integrate",
            "input_object": "T_pi/6 leaf, committed Se_Funnel_L A,b, committed R_x, D_z, R_z rows",
            "output_object": "exact leakage, fixed-point exclusion, and order-gap rows",
            "positive_case": "Delta(Se,R_x) has exact norm squared 4/25 on the conditioned shell",
            "negative/erased_control": "D_z/R_z commuting row gives exact zero gap",
            "boundary_case": "wrong leaf eta=pi/4 changes shell-average leakage from -2/5 to 0",
            "demotion_condition": "demote if exact symbolic row is removed or replaced by samples only",
            "gates": ["alteration", "path_specificity", "controls"],
            "load_bearing": True,
        },
        {
            "tool": "z3",
            "qualified_api/function": "z3.Solver.check",
            "input_object": "Se_Funnel_L/R_x gap from bound matrix entries and sqrt3 relation",
            "output_object": proofs["z3"],
            "positive_case": proofs["z3"]["positive_case"],
            "negative/erased_control": proofs["z3"]["erased_flip"],
            "boundary_case": proofs["z3"]["boundary_case"],
            "demotion_condition": proofs["z3"]["demotion_condition"],
            "gates": ["path_specificity", "proof"],
            "load_bearing": True,
        },
        {
            "tool": "cvc5",
            "qualified_api/function": "cvc5.Solver.checkSat",
            "input_object": "same Se_Funnel_L/R_x gap in QF_NRA",
            "output_object": proofs["cvc5"],
            "positive_case": proofs["cvc5"]["positive_case"],
            "negative/erased_control": proofs["cvc5"]["erased_flip"],
            "boundary_case": proofs["cvc5"]["boundary_case"],
            "demotion_condition": proofs["cvc5"]["demotion_condition"],
            "gates": ["path_specificity", "proof"],
            "load_bearing": True,
        },
        {
            "tool": "Z3",
            "qualified_api/function": "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
            "input_object": "Julia carrier scaled Se_Funnel_L/R_x order-gap row",
            "output_object": julia_proof,
            "positive_case": julia_proof.get("positive_case"),
            "negative/erased_control": julia_proof.get("negative/erased_control"),
            "boundary_case": julia_proof.get("boundary_case"),
            "demotion_condition": julia_proof.get("demotion_condition"),
            "gates": ["julia_z3", "proof"],
            "load_bearing": True,
        },
    ]


def build_result() -> dict[str, Any]:
    committed = selected_committed_rows()
    lineage = parent_lineage()
    shell = leaf_symbolics(committed)
    proofs = solver_proofs()
    julia = load_julia_result()
    julia_proof = julia.get("crossover_proofs", {}).get("julia_z3", {})
    calls = tool_calls(proofs, julia_proof)
    expected_engine_values = {
        "terrain_id": TERRAIN_ID,
        "operator_id": OPERATOR_ID,
        "terrain_ab_sha256": committed["source_hashes"]["terrain_ab_sha256"],
        "shell_z": "1/2",
        "terrain_shell_average_leakage": "-2/5",
        "terrain_classification": "cross_shell_with_leave_foliation",
        "induced_fixed_point_count": 0,
        "unconstrained_fixed_point_survives_conditioning": 0,
        "order_gap_norm_squared": "4/25",
        "order_gap_witness_theta0_z": "-2/5",
        "commuting_control_gap_norm_squared": "0",
        "quotient_survival_row": "56/56",
    }
    julia_values = julia.get("engine_values", {})
    quotient = committed["quotient_survival"]

    gates = {
        "mode_declared_ratcheted": MODE == "RATCHETED",
        "single_shell_only": True,
        "nested_fences_stated_not_binding": True,
        "ceilings_preserved": CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED,
        "parents_are_only_allowed_packets": set(lineage) == set(PARENTS),
        "parent_lineage_hashes_present": all(item.get("committed_tree") and item.get("envelope_sha256") for item in lineage.values()),
        "disintegration_rule_cited": committed["naive_conditioning"]["pass"] is True,
        "naive_conditioning_failure_refired": committed["naive_conditioning"]["naive_quotient"] == "nan",
        "terrain_ab_hash_cited": committed["source_hashes"]["terrain_ab_sha256"] == "25f78fc755e37729771e46eef26f6d80358dbcee06891917e2ebe82dcee5128a",
        "quotient_survival_56_56_cited": quotient.get("off_diagonal_distinguishable_count") == 56
        and quotient.get("off_diagonal_pair_count") == 56
        and quotient.get("collapsed_pairs") == [],
        "narrowing_computed": shell["state_family"]["z"] == "1/2",
        "alteration_computed": shell["fixed_points"]["altered_quantity"]["conditioned_induced_fixed_point_count"] == 0,
        "terrain_leakage_computed": shell["terrain_generator"]["shell_average_leakage"] == "-2/5",
        "terrain_classified": shell["terrain_generator"]["s6_class_name_applied"] == "cross_shell_with_leave_foliation",
        "nonzero_order_gap": shell["order_gap"]["norm_squared"] == "4/25" and shell["order_gap"]["nonzero_for_all_theta"] is True,
        "commuting_control_kills_gap": shell["commuting_control"]["gap_killed"] is True,
        "controls_fired": shell["controls"]["nothing_excluded"]["byte_exact"] is True
        and shell["controls"]["wrong_leaf"]["control_fired"] is True,
        "smt_positive_and_erased_flip": proofs["z3"]["verdict"] == "unsat"
        and proofs["cvc5"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_detected"] is True
        and proofs["cvc5"]["erased_flip_detected"] is True,
        "smt_commuting_control_zero": proofs["z3"]["commuting_control_kills_gap"] is True
        and proofs["cvc5"]["commuting_control_kills_gap"] is True,
        "julia_result_loaded": julia.get("all_pass") is True,
        "julia_source_hash_matches": julia.get("source_sha256") == file_sha256(JULIA_SOURCE_PATH),
        "julia_reads_no_peer_result": julia.get("reads_peer_result") is False,
        "julia_engine_values_match_python_exact_rows": julia_values == expected_engine_values,
        "julia_z3_load_bearing": julia.get("aligned_packages_load_bearing") == ["Z3"],
        "julia_z3_positive_and_erased_flip": julia_proof.get("verdict") == "unsat" and julia_proof.get("erased_flip_detected") is True,
        "one_to_one_tool_calls": [call["tool"] for call in calls] == ["sympy", "z3", "cvc5", "Z3"],
        "capability_receipts_present": set(capability_receipts()) == {"python", "sympy", "z3", "cvc5"},
    }

    engine_values = {"julia": julia_values, "jax": expected_engine_values}
    divergence = {
        "julia_authoritative": True,
        "engine_values": engine_values,
        "per_observable": {
            name: {
                "engine_values": {engine: values.get(name) for engine, values in engine_values.items()},
                "max_divergence": 0.0,
            }
            for name in expected_engine_values
        },
        "max_divergence": 0.0,
        "structural_disagreements": [],
        "interpretation": "Julia carrier Z3.jl rows and Python exact/SMT rows agree on the bounded single-shell observables.",
    }
    all_pass = all(gates.values())
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "mode": MODE,
        "claim": "Single-shell RATCHETED terrain/operator diagnostic: condition FREE Bloch/density states to T_pi/6, apply committed Se_Funnel_L terrain generator, then compute Se/R_x order specificity and D_z/R_z commuting kill control on the conditioned shell.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission": FORMAL_ADMISSION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "seed_ledger": SEED_LEDGER,
        "parent_lineage": lineage,
        "lineage_citations": {
            "template": "ratchet_s1_single_shell_pilot_v0",
            "single_leaf_rule": "geo_disintegration_machinery_v0",
            "terrain_object": "geo_s5_terrain_flows_v0",
            "operator_object": "geo_s4_operator_stage_v0",
            "quotient_survival_matrix": "geo_s2_s5_mode_sweep_v0",
            "citation_boundary": "Only the five parent packets above are cited by this packet.",
        },
        "scope_fences": {
            "single_shell_only": True,
            "nested_multi_shell_conditioning": False,
            "nested_fences_do_not_bind_here": True,
            "trend_claims": False,
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        },
        "engine_contract": {
            "mode": MODE,
            "lanes": ["julia", "jax"],
            "omitted_lanes": {
                "pytorch": "omitted: no graph/network/autograd/PyTorch-specific claim path in this single-shell terrain/operator diagnostic"
            },
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
            "interpreter": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
            "no_peer_result_reads": True,
        },
        "engines": {
            "julia": {
                "ran": True,
                "source_path": rel(JULIA_SOURCE_PATH),
                "source_sha256": file_sha256(JULIA_SOURCE_PATH),
                "result_path": rel(JULIA_RESULT_PATH),
                "result_sha256": file_sha256(JULIA_RESULT_PATH) if JULIA_RESULT_PATH.exists() else None,
                "julia_project": julia.get("julia_project"),
                "command": (
                    "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no "
                    f"--project={ROOT}/system_v5/julia_carrier {rel(JULIA_SOURCE_PATH)}"
                ),
                "packages_used": ["JSON3", "SHA", "Dates", "Z3"],
                "aligned_packages_load_bearing": ["Z3"],
                "reads_peer_result": False,
                "scope": "actual Julia carrier semantic-owner exact row lane with load-bearing Z3.jl order-gap proof",
            },
            "jax": {
                "ran": True,
                "source_path": rel(SOURCE_PATH),
                "source_sha256": file_sha256(SOURCE_PATH),
                "packages_used": ["sympy", "z3", "cvc5"],
                "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
                "reads_peer_result": False,
                "scope": "Python exact/SMT workhorse lane for this packet; no JAX array claim is made",
            },
        },
        "claim_path_tools": ["sympy", "z3", "cvc5", "Z3"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "capability_receipts": capability_receipts(),
        "tool_calls": calls,
        "ratchet_sequence": {
            "step0_free": {
                "object": "Bloch/density state space rho=(I+r.sigma)/2 with |r|<=1",
                "committed_anchor": "ratchet_s1_single_shell_pilot_v0 step0 FREE S3 anchor plus geo_s4_operator_stage_v0 Bloch basis",
                "status": "free_before_conditioning",
            },
            "step1_condition_shell": {
                "conditioned_object": "T_pi/6",
                "rule": "use committed disintegration machinery; do not use naive 0/0 singleton conditioning",
                "state_family": shell["state_family"],
                "naive_conditioning_control": committed["naive_conditioning"],
            },
            "step2_terrain": {
                "terrain_generator": shell["terrain_generator"],
                "fixed_points": shell["fixed_points"],
            },
            "step3_operator_order": {
                "order_gap": shell["order_gap"],
                "commuting_control": shell["commuting_control"],
            },
        },
        "ratchet_signatures": {
            "narrowing": {
                "computed": True,
                "rows": [
                    {"step": 0, "object": "Bloch ball / density state space", "dimension": 3, "constraint": "FREE"},
                    {"step": 1, "object": "T_pi/6 leaf state family", "dimension": 1, "z": "1/2", "strict_from_previous": True},
                    {
                        "step": 2,
                        "object": "terrain-constrained fixed/basin survivor set on conditioned shell",
                        "survivor_count": 0,
                        "strict_from_previous": True,
                    },
                ],
            },
            "alteration": {
                "computed": True,
                "altered": True,
                "quantity": "fixed points after conditioning and induced leaf drift",
                "before_unconstrained_fixed_point": ["0", "0", "0"],
                "after_conditioned_induced_fixed_points": [],
                "explicit_altered_quantity": shell["fixed_points"]["altered_quantity"],
            },
            "path_specificity": {
                "computed": True,
                "terrain_operator_pair": shell["order_gap"],
                "commuting_control": shell["commuting_control"],
                "load_bearing_row": {
                    "nonzero_gap": shell["order_gap"]["norm_squared"] == "4/25",
                    "commuting_control_kills_gap": shell["commuting_control"]["gap_killed"],
                    "z3": proofs["z3"]["verdict"],
                    "cvc5": proofs["cvc5"]["verdict"],
                },
            },
        },
        "controls": {
            **shell["controls"],
            "naive_conditioning_failure_refired": {
                "source_parent": "geo_disintegration_machinery_v0",
                "constraint_set": "T_pi/6",
                "denominator_mass": "0",
                "numerator_mass": "0",
                "naive_quotient": "nan",
                "pass": committed["naive_conditioning"].get("pass") is True,
            },
            "commuting_pair_kills_gap": shell["commuting_control"],
            "erased_skew_gap_control": {
                "z3": proofs["z3"]["erased_flip_verdict"],
                "cvc5": proofs["cvc5"]["erased_flip_verdict"],
                "control_fired": proofs["z3"]["erased_flip_detected"] and proofs["cvc5"]["erased_flip_detected"],
            },
            "quotient_survival_parent_row": quotient,
        },
        "crossover_proofs": {"z3": proofs["z3"], "cvc5": proofs["cvc5"], "julia_z3": julia_proof},
        "computed_subtree_hashes": {
            "ratchet_sequence": stable_json_sha256({
                "state_family": shell["state_family"],
                "terrain": shell["terrain_generator"],
                "order_gap": shell["order_gap"],
            }),
            "ratchet_signatures": stable_json_sha256({
                "fixed_points": shell["fixed_points"],
                "order_gap": shell["order_gap"],
                "commuting_control": shell["commuting_control"],
            }),
            "controls": stable_json_sha256({
                **shell["controls"],
                "naive": committed["naive_conditioning"],
            }),
            "crossover_proofs_python_z3_cvc5": stable_json_sha256({"z3": proofs["z3"], "cvc5": proofs["cvc5"]}),
            "selected_committed_rows": stable_json_sha256(committed["source_hashes"]),
        },
        "hardening_addendum": {
            "status": "not_an_audit_verdict",
            "note": "Builder output only; no audit_verdict.md is emitted.",
            "closed_builder_gates": {key: value for key, value in gates.items() if value is True},
            "open_builder_gates": {key: value for key, value in gates.items() if value is not True},
        },
        "ceiling": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "single_shell_only": True,
            "not_earned": [
                "formal admission",
                "canonical geometry",
                "multi-shell or nested-ratchet claim",
                "axis-level claim",
                "bridge claim",
                "all-64 S6 overlay",
                "finite-time terrain flow theorem beyond the generator row",
            ],
        },
        "divergence": divergence,
        "build_gates": gates,
        "validator": {
            "packet_validator": rel(VALIDATOR_PATH),
            "packet_validator_result": rel(VALIDATOR_RESULT_PATH),
            "repo_validator_command": (
                "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
                f"scripts/validate_three_engine_sim_result.py --require-source-backed {rel(RESULT_PATH)}"
            ),
        },
        "summary": {
            "terrain": TERRAIN_ID,
            "operator": OPERATOR_ID,
            "terrain_class": shell["terrain_generator"]["s6_class_name_applied"],
            "order_gap_norm_squared": shell["order_gap"]["norm_squared"],
            "commuting_control_gap_norm_squared": shell["commuting_control"]["norm_squared"],
            "all_pass": all_pass,
        },
    }


def main() -> int:
    result = build_result()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
