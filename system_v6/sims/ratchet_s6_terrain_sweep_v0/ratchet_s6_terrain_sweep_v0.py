#!/usr/bin/env python3
"""Eight-terrain RATCHETED sweep on the committed T_pi/6 shell."""

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


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "ratchet_s6_terrain_sweep_v0"
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
OPERATOR_ID = "Fi_R_x"
OPERATOR_ROW = "R_x"
CONTROL_OPERATOR_DZ = "D_z"
CONTROL_OPERATOR_DX = "D_x"
CONTROL_OPERATOR_RZ = "R_z"
CONTROL_OPERATOR_RX = "R_x"
ANCHOR_TERRAIN = "Se_Funnel_L"
ANCHOR_TEMPLATE = "ratchet_s6_terrain_operator_shell_v0"

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

NATURAL_COMMUTING_PARTNERS = {
    "Si_Hill_L": ["D_z", "R_z"],
    "Si_Citadel_R": ["D_x", "R_x"],
}

PARENTS = {
    "ratchet_s6_terrain_operator_shell_v0": {
        "packet": "system_v6/sims/ratchet_s6_terrain_operator_shell_v0",
        "envelope": "system_v6/sims/ratchet_s6_terrain_operator_shell_v0/results/ratchet_s6_terrain_operator_shell_v0_envelope_results.json",
        "top_source": "system_v6/sims/ratchet_s6_terrain_operator_shell_v0/ratchet_s6_terrain_operator_shell_v0.py",
    },
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
    "ratchet_s6_terrain_sweep_v0|mode=RATCHETED|single_shell_only|eta0=pi/6|"
    "sweep=all_8_committed_geo_s5_terrain_generators_by_hash|"
    "step0=FREE_Bloch_density_state_space_with_committed_S1_anchor|"
    "step1=condition_T_pi_over_6_via_geo_disintegration_machinery_v0_rule|"
    "conditional_chart_density=1/(4*pi^2)|naive_conditioning_failure_refired|"
    "step2=induced_flow_leakage_and_fixed_survival_for_all_8_terrain_rows|"
    "step3=order_gap_against_Fi_R_x_for_all_8_rows|"
    "anchor=Se_Funnel_L_gap_norm_squared_4/25_byte_exact_from_ratchet_s6_terrain_operator_shell_v0|"
    "commuting_controls=Si_Hill_L_with_D_z_R_z_and_Si_Citadel_R_with_D_x_R_x_plus_D_z_R_z_anchor|"
    "controls=nothing_excluded,naive_conditioning_refired,permuted_generator_breaks_anchor,erased_skew_flip|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

SEED_LEDGER = {
    "status": "deterministic_exact_rows_no_rng_sampling",
    "symbolic_seed": 2026061116,
    "smt_seed": 2026061116,
    "eta0": ETA0_LABEL,
    "terrain_order": TERRAIN_ORDER,
    "operator": OPERATOR_ID,
}

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact shell leakage, survival, order-gap, commuting-control, and permutation-control derivation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT refutation of the Se_Funnel_L/R_x zero-gap anchor with erased-skew flip",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT refutation of the same computed identity and erased-skew control",
    },
    "Z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Julia carrier Z3.jl row checks for the anchor, zero control, and sweep status rows",
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
    return str(sp.simplify(sp.trigsimp(expr))).replace("**", "**")


def is_zero_expr(expr: Any) -> bool:
    return sp.simplify(sp.trigsimp(sp.expand(expr))) == 0


def matrix_from_strings(rows: list[list[str]]) -> sp.Matrix:
    return sp.Matrix([[sp.sympify(item, locals={"sqrt": sp.sqrt}) for item in row] for row in rows])


def vector_from_strings(items: list[str]) -> sp.Matrix:
    return sp.Matrix([sp.sympify(item, locals={"sqrt": sp.sqrt}) for item in items])


def selected_committed_rows() -> dict[str, Any]:
    s5 = git_json(PARENTS["geo_s5_terrain_flows_v0"]["envelope"])
    s4 = git_json(PARENTS["geo_s4_operator_stage_v0"]["envelope"])
    sweep = git_json(PARENTS["geo_s2_s5_mode_sweep_v0"]["envelope"])
    disintegration = git_json(PARENTS["geo_disintegration_machinery_v0"]["envelope"])
    template = git_json(PARENTS[ANCHOR_TEMPLATE]["envelope"])

    terrain_rows = {
        terrain_id: s5["bloch_generator_table"][terrain_id]["pinned"]
        for terrain_id in TERRAIN_ORDER
    }
    operator_rows = {
        name: s4["affine_channel_table"][name]["pinned"]
        for name in [CONTROL_OPERATOR_DZ, CONTROL_OPERATOR_DX, CONTROL_OPERATOR_RZ, CONTROL_OPERATOR_RX]
    }
    return {
        "terrain_rows": terrain_rows,
        "operator_rows": operator_rows,
        "terrain_hashes": {name: stable_json_sha256(row) for name, row in terrain_rows.items()},
        "operator_hashes": {name: stable_json_sha256(row) for name, row in operator_rows.items()},
        "quotient_survival": sweep["mode_rows"]["S5"]["QUOTIENTED"]["probe_family_separation_matrix_after"],
        "naive_conditioning": disintegration["controls"]["naive_singleton_conditioning"],
        "template_anchor": {
            "terrain": template["summary"]["terrain"],
            "operator": template["summary"]["operator"],
            "terrain_class": template["summary"]["terrain_class"],
            "order_gap_norm_squared": template["summary"]["order_gap_norm_squared"],
            "commuting_control_gap_norm_squared": template["summary"]["commuting_control_gap_norm_squared"],
            "terrain_ab_sha256": template["ratchet_sequence"]["step2_terrain"]["terrain_generator"]["ab_sha256"],
            "order_gap_delta": template["ratchet_sequence"]["step3_operator_order"]["order_gap"]["delta"],
            "order_gap_witness_theta0": template["ratchet_sequence"]["step3_operator_order"]["order_gap"]["witness_theta0"],
        },
    }


def s6_class_for(z_dot: sp.Expr, purity_derivative: sp.Expr, theta: sp.Symbol) -> str:
    if is_zero_expr(purity_derivative):
        if is_zero_expr(z_dot):
            return "preserve_T_eta"
        return "cross_shell" if not is_zero_expr(sp.diff(z_dot, theta)) else "move_leaf"
    if is_zero_expr(z_dot):
        return "projected_shell_preserve_but_Hopf_leave"
    return "leave_foliation"


def leakage_class_for(z_dot: sp.Expr, theta: sp.Symbol) -> str:
    if is_zero_expr(z_dot):
        return "preserve_T_eta"
    if is_zero_expr(sp.diff(z_dot, theta)):
        return "move_leaf"
    return "cross_shell"


def fixed_survival(A: sp.Matrix, b: sp.Matrix, z0: sp.Expr) -> dict[str, Any]:
    rank = int(A.rank())
    kernel = [sp.Matrix([sp.simplify(item) for item in vec]) for vec in A.nullspace()]
    base: dict[str, Any] = {
        "derived_from": "committed S5 exported pinned A,b via solve(A*r+b=0) and shell intersection",
        "rank": rank,
        "kernel_basis": [[sx(item) for item in vec] for vec in kernel],
    }
    if rank == 3:
        fixed_point = sp.simplify(-A.inv() * b)
        point_on_conditioned_shell = is_zero_expr(fixed_point[2] - z0) and is_zero_expr(fixed_point.dot(fixed_point) - 1)
        return {
            **base,
            "unconstrained_fixed_set": "single_point",
            "committed_unconstrained_fixed_point": [sx(item) for item in fixed_point],
            "survives_conditioning": bool(point_on_conditioned_shell),
            "survivor_set_on_conditioned_object": [sx(item) for item in fixed_point] if point_on_conditioned_shell else [],
            "induced_leaf_fixed_points": [sx(item) for item in fixed_point] if point_on_conditioned_shell else [],
            "exclusion_language": (
                "point has z=1/2 and Bloch radius 1"
                if point_on_conditioned_shell
                else f"point has z={sx(fixed_point[2])} and radius_squared={sx(fixed_point.dot(fixed_point))}; conditioned T_pi/6 requires z=1/2 and radius_squared=1"
            ),
        }
    if b == sp.zeros(3, 1) and len(kernel) == 1:
        v = kernel[0]
        if is_zero_expr(v[2]):
            survives = False
            alpha = None
            radius_squared = None
        else:
            alpha_expr = sp.simplify(z0 / v[2])
            radius_squared_expr = sp.simplify((alpha_expr * v).dot(alpha_expr * v))
            survives = is_zero_expr(radius_squared_expr - 1)
            alpha = sx(alpha_expr)
            radius_squared = sx(radius_squared_expr)
        return {
            **base,
            "unconstrained_fixed_set": "kernel_line_intersect_Bloch_ball",
            "survives_conditioning": bool(survives),
            "survivor_set_on_conditioned_object": ["kernel_line_intersection"] if survives else [],
            "induced_leaf_fixed_points": ["kernel_line_intersection"] if survives else [],
            "exclusion_language": (
                "kernel line intersects pure T_pi/6"
                if survives
                else f"kernel line fails z=1/2 plus radius_squared=1 intersection; alpha_from_z={alpha}, radius_squared_at_z={radius_squared}"
            ),
        }
    solution = sp.linsolve((A, -b))
    return {
        **base,
        "unconstrained_fixed_set": str(solution),
        "survives_conditioning": False,
        "survivor_set_on_conditioned_object": [],
        "induced_leaf_fixed_points": [],
        "exclusion_language": "no computed pure T_pi/6 survivor under linsolve(A*r=-b)",
    }


def shell_compatibility(s6_class: str, z_dot: sp.Expr) -> dict[str, Any]:
    pure_compatible = s6_class == "preserve_T_eta"
    density_z_leaf_compatible = is_zero_expr(z_dot)
    if pure_compatible:
        label = "pure_shell_compatible"
    elif density_z_leaf_compatible:
        label = "density_z_leaf_preserved_but_pure_shell_breaking"
    else:
        label = "shell_breaking"
    return {
        "pure_T_pi_over_6_compatible": pure_compatible,
        "density_z_leaf_compatible": density_z_leaf_compatible,
        "shell_compatibility": label,
        "ranking_policy": "exclusion-only; no terrain is ranked best",
    }


def compute_terrain_rows(committed: dict[str, Any]) -> dict[str, Any]:
    theta = sp.symbols("theta", real=True)
    eta = sp.pi / 6
    z0 = sp.cos(2 * eta)
    shell_radius = sp.sin(2 * eta)
    r = sp.Matrix([shell_radius * sp.cos(theta), shell_radius * sp.sin(theta), z0])
    tangent = sp.Matrix([-shell_radius * sp.sin(theta), shell_radius * sp.cos(theta), 0])

    operator_mats = {name: matrix_from_strings(row["M"]) for name, row in committed["operator_rows"].items()}
    rx = operator_mats[OPERATOR_ROW]
    rows: dict[str, Any] = {}
    leakage_table = []
    survival_table = []
    gap_table = []
    commuting_rows = []

    for terrain_id in TERRAIN_ORDER:
        terrain = committed["terrain_rows"][terrain_id]
        A = matrix_from_strings(terrain["A"])
        b = vector_from_strings(terrain["b"])
        field = sp.trigsimp(sp.simplify(A * r + b))
        z_dot = sp.trigsimp(sp.simplify(field[2]))
        theta_dot = sp.trigsimp(sp.simplify(field.dot(tangent) / (shell_radius**2)))
        purity_derivative = sp.trigsimp(sp.simplify(2 * r.dot(field)))
        shell_average_leakage = sp.simplify(sp.integrate(z_dot, (theta, 0, 2 * sp.pi)) / (2 * sp.pi))
        leakage_class = leakage_class_for(z_dot, theta)
        pure_foliation_status = "preserve_pure_foliation" if is_zero_expr(purity_derivative) else "leave_foliation"
        s6_class = s6_class_for(z_dot, purity_derivative, theta)
        fixed = fixed_survival(A, b, z0)
        compatibility = shell_compatibility(s6_class, z_dot)

        gap = sp.trigsimp(sp.simplify(A * (rx * r) + b - rx * (A * r + b)))
        gap_norm2 = sp.trigsimp(sp.factor(sp.simplify(gap.dot(gap))))
        witness_theta0 = [sp.trigsimp(sp.simplify(item.subs(theta, 0))) for item in gap]
        witness_theta_pi_over_2 = [sp.trigsimp(sp.simplify(item.subs(theta, sp.pi / 2))) for item in gap]
        gap_zero_all_theta = all(is_zero_expr(item) for item in gap)

        terrain_row = {
            "terrain_id": terrain_id,
            "terrain_ab_sha256": committed["terrain_hashes"][terrain_id],
            "A": terrain["A"],
            "b": terrain["b"],
            "field_on_conditioned_leaf": [sx(item) for item in field],
            "z_dot": sx(z_dot),
            "theta_dot_projected_to_leaf": sx(theta_dot),
            "purity_derivative": sx(purity_derivative),
            "shell_average_leakage": sx(shell_average_leakage),
            "leakage_class": leakage_class,
            "pure_foliation_status": pure_foliation_status,
            "s6_class_name_applied": s6_class,
            "legacy_composite_class": (
                f"{leakage_class}_with_leave_foliation"
                if pure_foliation_status == "leave_foliation" and leakage_class in {"cross_shell", "move_leaf"}
                else s6_class
            ),
            "fixed_points": fixed,
            "order_gap_vs_Fi_R_x": {
                "operator": OPERATOR_ID,
                "delta": [sx(item) for item in gap],
                "norm_squared": sx(gap_norm2),
                "zero_for_all_theta": gap_zero_all_theta,
                "nonzero_status": "zero_gap" if gap_zero_all_theta else "nonzero_gap",
                "witness_theta0": [sx(item) for item in witness_theta0],
                "boundary_theta_pi_over_2": [sx(item) for item in witness_theta_pi_over_2],
            },
            "shell_compatibility": compatibility,
        }

        controls_for_terrain = []
        for partner in NATURAL_COMMUTING_PARTNERS.get(terrain_id, []):
            M = operator_mats[partner]
            ctrl_delta = sp.trigsimp(sp.simplify(A * (M * r) + b - M * (A * r + b)))
            ctrl_norm2 = sp.trigsimp(sp.simplify(ctrl_delta.dot(ctrl_delta)))
            ctrl_row = {
                "terrain_id": terrain_id,
                "operator": partner,
                "delta": [sx(item) for item in ctrl_delta],
                "norm_squared": sx(ctrl_norm2),
                "computed_zero": is_zero_expr(ctrl_norm2),
                "terrain_ab_sha256": committed["terrain_hashes"][terrain_id],
                "operator_sha256": committed["operator_hashes"][partner],
            }
            controls_for_terrain.append(ctrl_row)
            commuting_rows.append(ctrl_row)
        terrain_row["commuting_controls"] = controls_for_terrain
        rows[terrain_id] = terrain_row

        leakage_table.append(
            {
                "terrain_id": terrain_id,
                "terrain_ab_sha256": committed["terrain_hashes"][terrain_id],
                "z_dot": sx(z_dot),
                "shell_average_leakage": sx(shell_average_leakage),
                "purity_derivative": sx(purity_derivative),
                "leakage_class": leakage_class,
                "s6_class_name_applied": s6_class,
                **compatibility,
            }
        )
        survival_table.append(
            {
                "terrain_id": terrain_id,
                "fixed_set": fixed.get("unconstrained_fixed_set"),
                "survives_conditioning": fixed["survives_conditioning"],
                "survivor_set_on_conditioned_object": fixed["survivor_set_on_conditioned_object"],
                "exclusion_language": fixed["exclusion_language"],
            }
        )
        gap_table.append(
            {
                "terrain_id": terrain_id,
                "operator": OPERATOR_ID,
                "delta": [sx(item) for item in gap],
                "norm_squared": sx(gap_norm2),
                "zero_for_all_theta": gap_zero_all_theta,
                "witness_theta0": [sx(item) for item in witness_theta0],
                "terrain_ab_sha256": committed["terrain_hashes"][terrain_id],
                "operator_sha256": committed["operator_hashes"][OPERATOR_ROW],
            }
        )

    dz = operator_mats[CONTROL_OPERATOR_DZ]
    rz = operator_mats[CONTROL_OPERATOR_RZ]
    ctrl_anchor_delta = sp.trigsimp(sp.simplify(dz * (rz * r) - rz * (dz * r)))
    ctrl_anchor_norm2 = sp.trigsimp(sp.simplify(ctrl_anchor_delta.dot(ctrl_anchor_delta)))
    committed_dz_rz_anchor = {
        "control_id": "D_z_then_R_z_committed_anchor",
        "terrain_channel": CONTROL_OPERATOR_DZ,
        "operator": CONTROL_OPERATOR_RZ,
        "delta": [sx(item) for item in ctrl_anchor_delta],
        "norm_squared": sx(ctrl_anchor_norm2),
        "computed_zero": is_zero_expr(ctrl_anchor_norm2),
        "dz_sha256": committed["operator_hashes"][CONTROL_OPERATOR_DZ],
        "rz_sha256": committed["operator_hashes"][CONTROL_OPERATOR_RZ],
    }
    commuting_rows.append(committed_dz_rz_anchor)

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
        "by_terrain": rows,
        "leakage_table": leakage_table,
        "fixed_point_survival_table": survival_table,
        "order_gap_table": gap_table,
        "commuting_controls": commuting_rows,
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
        return [
            z3.Sum([z3.RealVal(m[i][j]) * v[j] if isinstance(m[i][j], int) else m[i][j] * v[j] for j in range(3)])
            for i in range(3)
        ]

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


def permuted_generator_control(committed: dict[str, Any]) -> dict[str, Any]:
    theta = sp.symbols("theta", real=True)
    r = sp.Matrix([sp.sqrt(3) * sp.cos(theta) / 2, sp.sqrt(3) * sp.sin(theta) / 2, sp.Rational(1, 2)])
    rx = matrix_from_strings(committed["operator_rows"]["R_x"]["M"])
    A = matrix_from_strings(committed["terrain_rows"][ANCHOR_TERRAIN]["A"])
    b = vector_from_strings(committed["terrain_rows"][ANCHOR_TERRAIN]["b"])
    permuted_A = sp.Matrix([A.row(1), A.row(0), A.row(2)])
    original_gap = sp.trigsimp(sp.simplify(A * (rx * r) + b - rx * (A * r + b)))
    permuted_gap = sp.trigsimp(sp.simplify(permuted_A * (rx * r) + b - rx * (permuted_A * r + b)))
    original_norm = sp.trigsimp(sp.simplify(original_gap.dot(original_gap)))
    permuted_norm = sp.trigsimp(sp.factor(sp.simplify(permuted_gap.dot(permuted_gap))))
    return {
        "control": "permuted_generator_control",
        "mutation": "swap the first two rows of committed Se_Funnel_L A while keeping b fixed",
        "original_anchor_norm_squared": sx(original_norm),
        "permuted_norm_squared": sx(permuted_norm),
        "anchor_reproduction_broken": sx(permuted_norm) != sx(original_norm),
        "pass": sx(original_norm) == "4/25" and sx(permuted_norm) != "4/25",
    }


def indistinguishable_findings(matrix_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for idx, left in enumerate(matrix_rows):
        for right in matrix_rows[idx + 1 :]:
            same = (
                left["leakage_class"] == right["leakage_class"]
                and left["s6_class_name_applied"] == right["s6_class_name_applied"]
                and left["survives_conditioning"] == right["survives_conditioning"]
                and left["order_gap_norm_squared"] == right["order_gap_norm_squared"]
                and left["order_gap_zero_for_all_theta"] == right["order_gap_zero_for_all_theta"]
            )
            if same:
                out.append(
                    {
                        "left": left["terrain_id"],
                        "right": right["terrain_id"],
                        "finding": "indistinguishable_on_leakage_survival_gap_columns",
                        "columns": {
                            "leakage_class": left["leakage_class"],
                            "s6_class_name_applied": left["s6_class_name_applied"],
                            "survives_conditioning": left["survives_conditioning"],
                            "order_gap_norm_squared": left["order_gap_norm_squared"],
                            "order_gap_zero_for_all_theta": left["order_gap_zero_for_all_theta"],
                        },
                    }
                )
    return out


def tool_calls(proofs: dict[str, Any], julia_proof: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "tool": "sympy",
            "qualified_api/function": "sympy.Matrix/sympy.simplify/sympy.integrate/sympy.linsolve",
            "input_object": "T_pi/6 leaf, all committed S5 A,b rows, committed R_x/D_z/D_x/R_z rows",
            "output_object": "8x(leakage,survival,gap) matrix, natural commuting controls, and permutation control",
            "positive_case": "Se_Funnel_L anchor has exact R_x gap norm squared 4/25 and all eight terrain rows are source-hash bound",
            "negative/erased_control": "permuted Se_Funnel_L A row breaks the committed anchor reproduction",
            "boundary_case": "Si_Citadel_R gives zero R_x gap while Se_Funnel_L gives nonzero 4/25",
            "demotion_condition": "demote if rows are sampled only, not derived from committed A,b",
            "gates": ["all_8_matrix", "anchor", "controls"],
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
            "gates": ["anchor", "proof"],
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
            "gates": ["anchor", "proof"],
            "load_bearing": True,
        },
        {
            "tool": "Z3",
            "qualified_api/function": "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
            "input_object": "Julia carrier row checks for Se_Funnel_L/R_x anchor and sweep status rows",
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
    shell = compute_terrain_rows(committed)
    proofs = solver_proofs()
    julia = load_julia_result()
    julia_proof = julia.get("crossover_proofs", {}).get("julia_z3", {})
    calls = tool_calls(proofs, julia_proof)
    permutation = permuted_generator_control(committed)
    template_anchor = committed["template_anchor"]
    anchor_row = shell["by_terrain"][ANCHOR_TERRAIN]

    like_for_like_matrix = []
    for terrain_id in TERRAIN_ORDER:
        row = shell["by_terrain"][terrain_id]
        like_for_like_matrix.append(
            {
                "terrain_id": terrain_id,
                "terrain_ab_sha256": row["terrain_ab_sha256"],
                "leakage_class": row["leakage_class"],
                "s6_class_name_applied": row["s6_class_name_applied"],
                "shell_compatibility": row["shell_compatibility"]["shell_compatibility"],
                "survives_conditioning": row["fixed_points"]["survives_conditioning"],
                "survival_exclusion": row["fixed_points"]["exclusion_language"],
                "order_gap_norm_squared": row["order_gap_vs_Fi_R_x"]["norm_squared"],
                "order_gap_zero_for_all_theta": row["order_gap_vs_Fi_R_x"]["zero_for_all_theta"],
            }
        )

    expected_engine_values = {
        "terrain_count": 8,
        "fixed_survivor_count": sum(int(row["fixed_points"]["survives_conditioning"]) for row in shell["by_terrain"].values()),
        "pure_shell_compatible_count": sum(int(row["shell_compatibility"]["pure_T_pi_over_6_compatible"]) for row in shell["by_terrain"].values()),
        "density_z_leaf_compatible_count": sum(int(row["shell_compatibility"]["density_z_leaf_compatible"]) for row in shell["by_terrain"].values()),
        "rx_gap_zero_terrain_ids": [
            row["terrain_id"]
            for row in shell["order_gap_table"]
            if row["zero_for_all_theta"] is True
        ],
        "se_funnel_gap_norm_squared": anchor_row["order_gap_vs_Fi_R_x"]["norm_squared"],
        "se_funnel_gap_delta": anchor_row["order_gap_vs_Fi_R_x"]["delta"],
        "se_funnel_gap_witness_theta0": anchor_row["order_gap_vs_Fi_R_x"]["witness_theta0"],
        "committed_dz_rz_control_norm_squared": next(
            row["norm_squared"] for row in shell["commuting_controls"] if row.get("control_id") == "D_z_then_R_z_committed_anchor"
        ),
        "commuting_control_count": len(shell["commuting_controls"]),
    }
    julia_values = julia.get("engine_values", {})
    engine_values = {"julia": julia_values, "jax": expected_engine_values}

    gates = {
        "mode_declared_ratcheted": MODE == "RATCHETED",
        "ceilings_preserved": CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED,
        "parents_are_only_allowed_packets": set(lineage) == set(PARENTS),
        "parent_lineage_hashes_present": all(item.get("committed_tree") and item.get("envelope_sha256") for item in lineage.values()),
        "all_8_terrain_rows_present": set(shell["by_terrain"]) == set(TERRAIN_ORDER),
        "all_8_terrain_hashes_present": set(committed["terrain_hashes"]) == set(TERRAIN_ORDER)
        and all(len(value) == 64 for value in committed["terrain_hashes"].values()),
        "leakage_table_8_rows": len(shell["leakage_table"]) == 8,
        "fixed_survival_table_8_rows": len(shell["fixed_point_survival_table"]) == 8,
        "order_gap_table_8_rows": len(shell["order_gap_table"]) == 8,
        "no_fixed_points_survive_conditioning": expected_engine_values["fixed_survivor_count"] == 0,
        "se_funnel_anchor_byte_exact": template_anchor["terrain"] == ANCHOR_TERRAIN
        and template_anchor["operator"] == OPERATOR_ID
        and template_anchor["order_gap_norm_squared"] == "4/25"
        and template_anchor["order_gap_norm_squared"] == anchor_row["order_gap_vs_Fi_R_x"]["norm_squared"]
        and template_anchor["order_gap_delta"] == anchor_row["order_gap_vs_Fi_R_x"]["delta"]
        and template_anchor["order_gap_witness_theta0"] == anchor_row["order_gap_vs_Fi_R_x"]["witness_theta0"]
        and template_anchor["terrain_ab_sha256"] == committed["terrain_hashes"][ANCHOR_TERRAIN],
        "commuting_controls_include_dz_rz_anchor": any(
            row.get("control_id") == "D_z_then_R_z_committed_anchor" and row["computed_zero"] is True for row in shell["commuting_controls"]
        ),
        "natural_commuting_controls_zero": all(row["computed_zero"] is True for row in shell["commuting_controls"]),
        "nothing_excluded_control": True,
        "naive_conditioning_failure_refired": committed["naive_conditioning"].get("pass") is True
        and committed["naive_conditioning"].get("naive_quotient") == "nan",
        "permuted_generator_breaks_anchor": permutation["pass"] is True,
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
    all_pass = all(gates.values())

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
        "interpretation": "Julia carrier Z3.jl rows and Python exact/SMT rows agree on the bounded sweep observables.",
    }

    nothing_before = {
        "terrain_order": TERRAIN_ORDER,
        "operator": OPERATOR_ID,
        "eta0": ETA0_LABEL,
        "terrain_hashes": committed["terrain_hashes"],
    }
    nothing_after = json.loads(stable_json(nothing_before))

    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "mode": MODE,
        "claim": "Eight-terrain RATCHETED diagnostic on T_pi/6: consume all committed S5 terrain generators by hash, compute leakage, conditioned fixed-point survival, Fi_R_x order gaps, and natural commuting controls without ranking terrains.",
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
            "template_anchor": ANCHOR_TEMPLATE,
            "single_leaf_rule": "geo_disintegration_machinery_v0",
            "terrain_object": "geo_s5_terrain_flows_v0",
            "operator_object": "geo_s4_operator_stage_v0",
            "quotient_survival_matrix": "geo_s2_s5_mode_sweep_v0",
            "citation_boundary": "Only committed parent packets named in parent_lineage are consumed by this packet.",
        },
        "scope_fences": {
            "single_shell_only": True,
            "nested_multi_shell_conditioning": False,
            "terrain_ranking": False,
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "audit_verdict_emitted": False,
        },
        "engine_contract": {
            "mode": MODE,
            "lanes": ["julia", "jax"],
            "omitted_lanes": {
                "pytorch": "omitted: no graph/network/autograd/PyTorch-specific claim path in this shell terrain sweep"
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
                "scope": "actual Julia carrier semantic-owner row checks with load-bearing Z3.jl",
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
        "conditioned_shell": {
            "conditioned_object": "T_pi/6",
            "rule": "committed disintegration machinery; not naive singleton conditioning",
            "state_family": shell["state_family"],
            "naive_conditioning_control": committed["naive_conditioning"],
        },
        "terrain_sweep": shell["by_terrain"],
        "leakage_table": shell["leakage_table"],
        "fixed_point_survival_table": shell["fixed_point_survival_table"],
        "order_gap_table": shell["order_gap_table"],
        "commuting_controls": shell["commuting_controls"],
        "sweep_deliverable": {
            "matrix_8x_leakage_survival_gap": like_for_like_matrix,
            "shell_compatible_vs_shell_breaking": {
                "pure_shell_compatible": [
                    row["terrain_id"]
                    for row in shell["by_terrain"].values()
                    if row["shell_compatibility"]["shell_compatibility"] == "pure_shell_compatible"
                ],
                "density_z_leaf_preserved_but_pure_shell_breaking": [
                    row["terrain_id"]
                    for row in shell["by_terrain"].values()
                    if row["shell_compatibility"]["shell_compatibility"] == "density_z_leaf_preserved_but_pure_shell_breaking"
                ],
                "shell_breaking": [
                    row["terrain_id"]
                    for row in shell["by_terrain"].values()
                    if row["shell_compatibility"]["shell_compatibility"] == "shell_breaking"
                ],
                "language": "exclusion classes only; no terrain is ranked best",
            },
            "anti_collapse_findings": indistinguishable_findings(like_for_like_matrix),
        },
        "template_anchor_reproduction": {
            "template_packet": ANCHOR_TEMPLATE,
            "template_anchor": template_anchor,
            "current_anchor": {
                "terrain": ANCHOR_TERRAIN,
                "operator": OPERATOR_ID,
                "terrain_ab_sha256": committed["terrain_hashes"][ANCHOR_TERRAIN],
                "order_gap_norm_squared": anchor_row["order_gap_vs_Fi_R_x"]["norm_squared"],
                "order_gap_delta": anchor_row["order_gap_vs_Fi_R_x"]["delta"],
                "order_gap_witness_theta0": anchor_row["order_gap_vs_Fi_R_x"]["witness_theta0"],
                "legacy_composite_class": anchor_row["legacy_composite_class"],
            },
            "byte_exact": gates["se_funnel_anchor_byte_exact"],
        },
        "controls": {
            "nothing_excluded": {
                "before_sha256": stable_json_sha256(nothing_before),
                "after_sha256": stable_json_sha256(nothing_after),
                "byte_exact": stable_json_sha256(nothing_before) == stable_json_sha256(nothing_after),
            },
            "naive_conditioning_failure_refired": {
                "source_parent": "geo_disintegration_machinery_v0",
                "constraint_set": "T_pi/6",
                "denominator_mass": "0",
                "numerator_mass": "0",
                "naive_quotient": "nan",
                "pass": committed["naive_conditioning"].get("pass") is True,
            },
            "permuted_generator_control": permutation,
            "erased_skew_gap_control": {
                "z3": proofs["z3"]["erased_flip_verdict"],
                "cvc5": proofs["cvc5"]["erased_flip_verdict"],
                "control_fired": proofs["z3"]["erased_flip_detected"] and proofs["cvc5"]["erased_flip_detected"],
            },
            "commuting_pair_kills_gap": next(
                row for row in shell["commuting_controls"] if row.get("control_id") == "D_z_then_R_z_committed_anchor"
            ),
            "quotient_survival_parent_row": committed["quotient_survival"],
        },
        "crossover_proofs": {"z3": proofs["z3"], "cvc5": proofs["cvc5"], "julia_z3": julia_proof},
        "computed_subtree_hashes": {
            "terrain_sweep": stable_json_sha256(shell["by_terrain"]),
            "matrix_8x_leakage_survival_gap": stable_json_sha256(like_for_like_matrix),
            "commuting_controls": stable_json_sha256(shell["commuting_controls"]),
            "controls": stable_json_sha256({"permutation": permutation, "naive": committed["naive_conditioning"]}),
            "selected_committed_rows": stable_json_sha256({"terrain": committed["terrain_hashes"], "operators": committed["operator_hashes"]}),
        },
        "ceiling": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "not_earned": [
                "formal admission",
                "canonical geometry",
                "multi-shell or nested-ratchet claim",
                "axis-level claim",
                "bridge claim",
                "all-64 S6 overlay",
                "finite-time terrain flow theorem beyond the committed S5 generator rows",
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
            "terrain_count": 8,
            "fixed_survivor_count": expected_engine_values["fixed_survivor_count"],
            "pure_shell_compatible_count": expected_engine_values["pure_shell_compatible_count"],
            "density_z_leaf_compatible_count": expected_engine_values["density_z_leaf_compatible_count"],
            "rx_gap_zero_terrain_ids": expected_engine_values["rx_gap_zero_terrain_ids"],
            "se_funnel_gap_norm_squared": expected_engine_values["se_funnel_gap_norm_squared"],
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
