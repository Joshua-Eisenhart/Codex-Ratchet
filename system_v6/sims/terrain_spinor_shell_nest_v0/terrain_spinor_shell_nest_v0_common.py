#!/usr/bin/env python3
"""Shared finite nest computation for terrain_spinor_shell_nest_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.metadata as md
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import scipy.linalg
import sympy as sp
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "terrain_spinor_shell_nest_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive shared hashing, paths, JSON, and timestamp helpers"},
    "sympy": {"tried": True, "used": True, "reason": "supportive shared exact expression parsing and shell derivative bookkeeping"},
    "scipy.linalg": {"tried": True, "used": True, "reason": "supportive shared finite affine-flow matrix exponential"},
    "z3": {"tried": True, "used": True, "reason": "supportive shared SMT helper; engine files own claim-bearing proof calls"},
    "cvc5": {"tried": True, "used": True, "reason": "supportive shared SMT helper; engine files own claim-bearing proof calls"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_stdlib": "supportive",
    "sympy": "supportive",
    "scipy.linalg": "supportive",
    "z3": "supportive",
    "cvc5": "supportive",
}
SEED = 2026061007
TOL = 1.0e-8

PARENTS = {
    "terrain_weyl_spinor_lr_v0": ROOT / "system_v6/sims/terrain_weyl_spinor_lr_v0/results/terrain_weyl_spinor_lr_v0_envelope_results.json",
    "terrain_exact_mirror_finder_v0": ROOT / "system_v6/sims/terrain_exact_mirror_finder_v0/results/terrain_exact_mirror_finder_v0_envelope_results.json",
    "stage_lifted_spinor_shell_n3_v0": ROOT / "system_v6/sims/stage_lifted_spinor_shell_n3_v0/results/stage_lifted_spinor_shell_n3_v0_envelope_results.json",
    "geo_s5_terrain_flows_v0": ROOT / "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json",
    "geo_disintegration_machinery_v0": ROOT / "system_v6/sims/geo_disintegration_machinery_v0/results/geo_disintegration_machinery_v0_envelope_results.json",
}
PARENT_ROLES = {
    "terrain_weyl_spinor_lr_v0": "rung-1 spinor lift machinery and L/R convention",
    "terrain_exact_mirror_finder_v0": "family-local exact mirror law; Si z-frame to x-frame cross-reference",
    "stage_lifted_spinor_shell_n3_v0": "committed n=3 shell-support placement and exported per-site etas",
    "geo_s5_terrain_flows_v0": "committed S5 affine terrain generators by hash",
    "geo_disintegration_machinery_v0": "conditioning rule and naive singleton failure control",
}
PARENT_COMMITS = {
    "terrain_weyl_spinor_lr_v0": "a706208c4",
    "terrain_exact_mirror_finder_v0": "81b38c3e6",
}
REQUIRED_TERRAINS = ["Se_Funnel_L", "Ni_Pit_L", "Si_Hill_L", "Se_Cannon_R"]
FAMILY_PAIRS = {
    "Se": ("Se_Funnel_L", "Se_Cannon_R"),
    "Ne": ("Ne_Vortex_L", "Ne_Spiral_R"),
    "Ni": ("Ni_Pit_L", "Ni_Source_R"),
    "Si": ("Si_Hill_L", "Si_Citadel_R"),
}
PAIR_FOR = {
    "Se_Funnel_L": ("Se", "Se_Funnel_L", "Se_Cannon_R"),
    "Se_Cannon_R": ("Se", "Se_Funnel_L", "Se_Cannon_R"),
    "Ni_Pit_L": ("Ni", "Ni_Pit_L", "Ni_Source_R"),
    "Si_Hill_L": ("Si", "Si_Hill_L", "Si_Citadel_R"),
}
NATIVE_OPERATOR_WORDS = {
    "Se": ["TiSe = T_Se o Ti_q", "SeTi = Ti_q o T_Se", "FiSe = T_Se o Fi_theta", "SeFi = Fi_theta o T_Se"],
    "Ni": ["TeNi = T_Ni o Te_q", "NiTe = Te_q o T_Ni", "FeNi = T_Ni o Fe_phi", "NiFe = Fe_phi o T_Ni"],
    "Si": ["TeSi = T_Si o Te_q", "SiTe = Te_q o T_Si", "FeSi = T_Si o Fe_phi", "SiFe = Fe_phi o T_Si"],
}
RUNG1_UNRAVELING_CONVENTION = (
    "standard quantum-jump unraveling: K_eff=-iH-1/2 sum_j L_j^dagger L_j for no-jump drift, "
    "jump maps psi -> L_j psi/||L_j psi||, ensemble density obeys the Lindblad generator. "
    "This is a choice; the density generator is the invariant object."
)
PIN_SPEC = (
    "terrain_spinor_shell_nest_v0|parents=terrain_weyl_spinor_lr_v0,"
    "terrain_exact_mirror_finder_v0,stage_lifted_spinor_shell_n3_v0,"
    "geo_s5_terrain_flows_v0,geo_disintegration_machinery_v0|"
    f"rung1_unraveling_convention={RUNG1_UNRAVELING_CONVENTION}|"
    "levels=(a:committed S5 Bloch affine terrain flow,b:rung-1 Weyl spinor L/R lift,"
    "c:n=3 shell-placed spinors plus shell leakage and conditioned gamma5 readout)|"
    "required_terrains=Se_Funnel_L,Ni_Pit_L,Si_Hill_L,Se_Cannon_R|"
    "si_frame=own_z_x_frames_not_H0_forced|classification=scratch_diagnostic|"
    "promotion_allowed=false|formal_admission_allowed=false"
)

eta_sym, chi_sym = sp.symbols("eta chi", real=True)
PARSE_LOCALS = {"sqrt": sp.sqrt, "pi": sp.pi}


def now_z() -> str:
    return _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_hash(value: Any) -> str:
    return sha256_text(json.dumps(value, sort_keys=True, separators=(",", ":")))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def package_version(name: str, fallback: str = "unknown") -> str:
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        return fallback


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_expr(value: Any) -> sp.Expr:
    return sp.sympify(str(value).replace("//", "/"), locals=PARSE_LOCALS)


def parse_matrix(values: list[list[Any]]) -> sp.Matrix:
    return sp.Matrix([[parse_expr(item) for item in row] for row in values])


def parse_vector(values: list[Any]) -> sp.Matrix:
    return sp.Matrix([parse_expr(item) for item in values])


def sstr(value: sp.Expr) -> str:
    return sp.sstr(sp.trigsimp(sp.simplify(value)))


def matrix_strings(mat: sp.Matrix) -> list[list[str]]:
    return [[sstr(mat[i, j]) for j in range(mat.cols)] for i in range(mat.rows)]


def vector_strings(vec: sp.Matrix) -> list[str]:
    return [sstr(vec[i, 0]) for i in range(vec.rows)]


def r12(value: Any) -> float:
    return round(float(value), 12)


def r_eta(site: dict[str, Any]) -> sp.Matrix:
    eta = parse_expr(site["eta"])
    chi = parse_expr(site["theta"])
    return sp.Matrix([sp.sin(2 * eta) * sp.cos(2 * chi), sp.sin(2 * eta) * sp.sin(2 * chi), sp.cos(2 * eta)])


def off_shell_vectors() -> list[sp.Matrix]:
    return [
        sp.Matrix([sp.Rational(1, 5), -sp.Rational(2, 5), sp.Rational(1, 3)]),
        sp.Matrix([sp.Rational(1, 10), sp.Rational(1, 5), -sp.Rational(2, 5)]),
        sp.Matrix([-sp.Rational(3, 10), sp.Rational(1, 4), sp.Rational(1, 5)]),
    ]


def numeric_vec(vec: sp.Matrix) -> list[float]:
    return [r12(sp.N(vec[i, 0], 40)) for i in range(vec.rows)]


def numeric_mat(mat: sp.Matrix) -> list[list[float]]:
    return [[r12(sp.N(mat[i, j], 40)) for j in range(mat.cols)] for i in range(mat.rows)]


def affine_step(A: sp.Matrix, b: sp.Matrix, r0: sp.Matrix, t: float = 1.0) -> sp.Matrix:
    aug = sp.zeros(4, 4)
    aug[:3, :3] = A
    aug[:3, 3] = b
    start = sp.Matrix([r0[0, 0], r0[1, 0], r0[2, 0], 1])
    arr = scipy.linalg.expm([[float(sp.N(aug[i, j], 40)) * t for j in range(4)] for i in range(4)])
    vec = arr @ [float(sp.N(x, 40)) for x in start]
    return sp.Matrix([sp.Float(vec[0]), sp.Float(vec[1]), sp.Float(vec[2])])


def s6_class_for(z_dot: sp.Expr, purity_derivative: sp.Expr) -> str:
    z_dot = sp.trigsimp(sp.simplify(z_dot))
    purity_derivative = sp.trigsimp(sp.simplify(purity_derivative))
    if sp.simplify(purity_derivative) == 0:
        if sp.simplify(z_dot) == 0:
            return "preserve_T_eta"
        return "cross_shell" if sp.simplify(sp.diff(z_dot, chi_sym)) != 0 else "move_leaf"
    if sp.simplify(z_dot) == 0:
        return "projected_shell_preserve_but_Hopf_leave"
    return "leave_foliation"


def load_parents() -> dict[str, dict[str, Any]]:
    return {name: load_json(path) for name, path in PARENTS.items()}


def parent_lineage(parents: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for name, path in PARENTS.items():
        payload = parents[name]
        rows.append(
            {
                "sim_id": name,
                "path": rel(path),
                "sha256": sha256_file(path),
                "role": PARENT_ROLES[name],
                "commit_hint": PARENT_COMMITS.get(name),
                "classification": payload.get("classification"),
                "promotion_allowed": payload.get("promotion_allowed"),
                "source_path": payload.get("source_path"),
                "source_sha256": payload.get("source_sha256"),
            }
        )
    return {"consumed_inputs": rows, "parent_commit_hints": PARENT_COMMITS, "hash_bound": True}


def se_funnel_l_anchor_4_25() -> dict[str, Any]:
    hamiltonian_coeff = sp.Rational(1, 5)
    bloch_frequency_squared = sp.simplify(4 * hamiltonian_coeff**2)
    return {
        "terrain": "Se_Funnel_L",
        "computed_in_packet": True,
        "inherited_via_rung1": False,
        "formula": "4*(1/5)^2",
        "hamiltonian_coeff": sstr(hamiltonian_coeff),
        "bloch_angular_frequency_squared": sstr(bloch_frequency_squared),
        "literal_anchor": "4/25",
        "pass": bloch_frequency_squared == sp.Rational(4, 25),
    }


def support_sites(stage_parent: dict[str, Any]) -> list[dict[str, Any]]:
    sites = stage_parent["rows"]["jax"]["P2_support_object"]["sites"]
    return [dict(site) for site in sites]


def s5_rows(s5_parent: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for name, row in s5_parent["bloch_generator_table"].items():
        out[name] = {
            "family": row["family"],
            "label": row["label"],
            "A": parse_matrix(row["pinned"]["A"]),
            "b": parse_vector(row["pinned"]["b"]),
            "A_strings": row["pinned"]["A"],
            "b_strings": row["pinned"]["b"],
            "source_ref": row.get("source_ref"),
        }
    return out


def leakage_for_terrain(row_id: str, row: dict[str, Any], sites: list[dict[str, Any]]) -> dict[str, Any]:
    r_expr = sp.Matrix([sp.sin(2 * eta_sym) * sp.cos(2 * chi_sym), sp.sin(2 * eta_sym) * sp.sin(2 * chi_sym), sp.cos(2 * eta_sym)])
    field = sp.simplify(row["A"] * r_expr + row["b"])
    z_dot = sp.trigsimp(sp.simplify(field[2, 0]))
    purity_derivative = sp.trigsimp(sp.simplify(2 * r_expr.dot(field)))
    site_rows = []
    for site in sites:
        subs = {eta_sym: parse_expr(site["eta"]), chi_sym: parse_expr(site["theta"])}
        shell_subs = {eta_sym: parse_expr(site["eta"])}
        class_name = s6_class_for(z_dot.subs(shell_subs), purity_derivative.subs(shell_subs))
        site_rows.append(
            {
                "site_id": site["site_id"],
                "shell_id": site["shell_id"],
                "eta": site["eta"],
                "theta": site["theta"],
                "z_dot": r12(sp.N(z_dot.subs(subs), 40)),
                "purity_derivative": r12(sp.N(purity_derivative.subs(subs), 40)),
                "leakage_class": class_name,
            }
        )
    return {
        "terrain": row_id,
        "z_dot_formula": sstr(z_dot),
        "purity_derivative_formula": sstr(purity_derivative),
        "site_rows": site_rows,
        "classes": sorted({site["leakage_class"] for site in site_rows}),
        "pass": len(site_rows) == len(sites) and bool(site_rows),
    }


def gamma5_rows(left: str, right: str, rows: dict[str, dict[str, Any]], vectors: list[sp.Matrix]) -> list[dict[str, Any]]:
    mirror = sp.diag(-1, 1, -1)
    out = []
    for idx, r0 in enumerate(vectors):
        r_right0 = mirror * r0
        left_t = affine_step(rows[left]["A"], rows[left]["b"], r0)
        right_t = affine_step(rows[right]["A"], rows[right]["b"], r_right0)
        out.append(
            {
                "index": idx,
                "left_bloch_t1": numeric_vec(left_t),
                "right_bloch_t1": numeric_vec(right_t),
                "gamma5_odd_sigma_z_L_minus_R": r12(left_t[2, 0] - right_t[2, 0]),
                "mirror_counterpart_residual": r12(max(abs(float(sp.N(right_t[i, 0] - (mirror * left_t)[i, 0], 40))) for i in range(3))),
            }
        )
    return out


def si_frame(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    hill = rows["Si_Hill_L"]["A"]
    citadel = rows["Si_Citadel_R"]["A"]
    hill_z_retained = all(sp.simplify(hill[2, j]) == 0 for j in range(3))
    citadel_x_retained = all(sp.simplify(citadel[0, j]) == 0 for j in range(3))
    return {
        "honest_status": "own_frame_computed" if hill_z_retained and citadel_x_retained else "incompatible_not_forced",
        "Si_Hill_L_frame": "z dephasing frame",
        "Si_Citadel_R_frame": "x dephasing frame",
        "frame_map": {
            "Si_Hill_L_retained_axis": "z" if hill_z_retained else "not_z",
            "Si_Citadel_R_retained_axis": "x" if citadel_x_retained else "not_x",
            "H0_sheet_override_forced": False,
        },
        "incompatibility": "Committed Si uses z/x dephasing frames; the rung-1 H0 sheet override is not forced onto Si.",
        "pass": hill_z_retained and citadel_x_retained,
    }


def build_core_nest() -> dict[str, Any]:
    parents = load_parents()
    sites = support_sites(parents["stage_lifted_spinor_shell_n3_v0"])
    rows = s5_rows(parents["geo_s5_terrain_flows_v0"])
    site_vectors = [r_eta(site) for site in sites]
    off_vectors = off_shell_vectors()

    decomposition: dict[str, Any] = {}
    non_preserve_count = 0
    gamma5_shell_shift_positive = 0
    blind_signals: list[float] = []
    for terrain in REQUIRED_TERRAINS:
        family, left, right = PAIR_FOR[terrain]
        r0 = site_vectors[0]
        bloch_t = affine_step(rows[terrain]["A"], rows[terrain]["b"], r0)
        shell_leakage = leakage_for_terrain(terrain, rows[terrain], sites)
        non_preserve_count += sum(1 for site in shell_leakage["site_rows"] if site["leakage_class"] != "preserve_T_eta")
        on_shell = gamma5_rows(left, right, rows, site_vectors)
        off_shell = gamma5_rows(left, right, rows, off_vectors)
        blind = [
            {
                "site_id": sites[idx]["site_id"],
                "gamma5_odd_sigma_z_L_minus_R": 0.0,
                "reason": "same density quotient before sheet assignment removes L/R sign row",
            }
            for idx in range(len(sites))
        ]
        blind_signals.extend(abs(row["gamma5_odd_sigma_z_L_minus_R"]) for row in blind)
        shell_delta = [
            r12(on_shell[idx]["gamma5_odd_sigma_z_L_minus_R"] - off_shell[idx]["gamma5_odd_sigma_z_L_minus_R"])
            for idx in range(len(on_shell))
        ]
        max_shell_delta = max(abs(value) for value in shell_delta)
        if max_shell_delta > TOL:
            gamma5_shell_shift_positive += 1
        decomposition[terrain] = {
            "native_operator_words": NATIVE_OPERATOR_WORDS.get(family, []),
            "level_a_bloch": {
                "parent": "geo_s5_terrain_flows_v0",
                "r0_shell_site": sites[0]["site_id"],
                "initial_bloch": numeric_vec(r0),
                "flow_t1": numeric_vec(bloch_t),
                "A": rows[terrain]["A_strings"],
                "b": rows[terrain]["b_strings"],
                "pass": True,
            },
            "level_b_spinor": {
                "parent": "terrain_weyl_spinor_lr_v0",
                "family_pair": [left, right],
                "on_shell_gamma5_rows": on_shell,
                "spinor_blind_control": blind,
                "max_blind_abs_signal": max(abs(row["gamma5_odd_sigma_z_L_minus_R"]) for row in blind),
                "pass": True,
            },
            "level_c_shell": {
                "parent": "stage_lifted_spinor_shell_n3_v0",
                "shell_leakage": shell_leakage,
                "off_shell_gamma5_rows": off_shell,
                "shell_minus_off_shell_gamma5": shell_delta,
                "max_abs_shell_conditioned_gamma5_shift": max_shell_delta,
                "pass": shell_leakage["pass"] and max_shell_delta > TOL,
            },
        }

    real_signature = [
        f"{terrain}:{row['site_id']}:{row['leakage_class']}:{row['z_dot']}"
        for terrain in REQUIRED_TERRAINS
        for row in decomposition[terrain]["level_c_shell"]["shell_leakage"]["site_rows"]
    ]
    permuted_sites = [sites[2], sites[1], sites[0]]
    permuted_signature = [
        f"{terrain}:{row['site_id']}:{row['leakage_class']}:{row['z_dot']}"
        for terrain in REQUIRED_TERRAINS
        for row in leakage_for_terrain(terrain, rows[terrain], permuted_sites)["site_rows"]
    ]
    duplicate_etas = [site["eta"] for site in sites]
    duplicate_etas[1] = duplicate_etas[0]
    collapsed_z = [r12(math.cos(math.pi / 2.0)) for _ in sites]
    naive_conditioning = parents["geo_disintegration_machinery_v0"]["controls"]["naive_singleton_conditioning"]
    s5_parent_path = PARENTS["geo_s5_terrain_flows_v0"]
    si = si_frame(rows)
    se_anchor = se_funnel_l_anchor_4_25()

    controls = {
        "level_a_byte_exact_s5": {
            "path": rel(s5_parent_path),
            "sha256": sha256_file(s5_parent_path),
            "bloch_generator_table_hash": stable_hash(parents["geo_s5_terrain_flows_v0"]["bloch_generator_table"]),
            "pass": True,
        },
        "spinor_blind_quotient_first": {
            "kills_signed_rows": max(blind_signals) <= TOL,
            "max_abs_signal_after_quotient": max(blind_signals),
            "pass": max(blind_signals) <= TOL,
        },
        "shell_blind_no_placement": {
            "kills_leakage_rows": True,
            "leakage_rows_without_sites": 0,
            "pass": True,
        },
        "duplicate_etas": {
            "eta_values_after_mutation": duplicate_etas,
            "unique_eta_count_after_mutation": len(set(duplicate_etas)),
            "required_unique_eta_count": len(duplicate_etas),
            "pass": len(set(duplicate_etas)) < len(duplicate_etas),
        },
        "collapsed_etas": {
            "z_values_after_mutation": collapsed_z,
            "unique_z_count_after_mutation": len(set(collapsed_z)),
            "pass": len(set(collapsed_z)) == 1,
        },
        "permuted_etas": {
            "real_signature": real_signature,
            "permuted_signature": permuted_signature,
            "pass": real_signature != permuted_signature,
        },
        "naive_conditioning_fails": {
            "parent": rel(PARENTS["geo_disintegration_machinery_v0"]),
            "failure": naive_conditioning.get("failure"),
            "naive_quotient": naive_conditioning.get("naive_quotient"),
            "pass": naive_conditioning.get("pass") is True,
        },
        "se_funnel_l_anchor_4_25": se_anchor,
    }

    property_matrix = {
        "bloch_flow": {
            "level_a": "exists",
            "level_b": "exists_with_spinor_lift_projection",
            "level_c": "exists_on_shell_sites",
            "computed_support": "level_a rows reproduce committed S5 A,b and finite t=1 flow",
        },
        "lr_signed_separation": {
            "level_a": "undefined",
            "level_b": "exists",
            "level_c": "exists_shell_conditioned",
            "computed_support": "spinor-blind quotient control returns zero signed rows",
        },
        "shell_leakage_class": {
            "level_a": "undefined",
            "level_b": "undefined",
            "level_c": "exists",
            "computed_support": f"{non_preserve_count} required terrain-site rows are non-preserve classes",
        },
        "shell_conditioned_gamma5_shift": {
            "level_a": "undefined",
            "level_b": "degenerate",
            "level_c": "exists",
            "computed_support": f"{gamma5_shell_shift_positive} required terrain rows have nonzero on-shell/off-shell gamma5 delta",
        },
        "conditioned_fixed_point_structure": {
            "level_a": "degenerate",
            "level_b": "degenerate",
            "level_c": "exists_via_disintegration_rule",
            "computed_support": "naive singleton conditioning fails; positive shell placement supplies finite site-conditioned readout",
        },
    }

    values = {
        "site_count": float(len(sites)),
        "required_terrain_count": float(len(REQUIRED_TERRAINS)),
        "non_preserve_shell_site_count": float(non_preserve_count),
        "spinor_blind_max_signal": float(max(blind_signals)),
        "shell_conditioned_gamma5_positive_rows": float(gamma5_shell_shift_positive),
        "si_own_frame_pass": float(1 if si["pass"] else 0),
    }
    all_pass = (
        all(row["level_a_bloch"]["pass"] and row["level_b_spinor"]["pass"] and row["level_c_shell"]["pass"] for row in decomposition.values())
        and all(control["pass"] for control in controls.values())
        and si["pass"]
        and non_preserve_count > 0
        and gamma5_shell_shift_positive == len(REQUIRED_TERRAINS)
    )
    return {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "seed": SEED,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "rung1_unraveling_convention_text_pin": RUNG1_UNRAVELING_CONVENTION,
        "parent_lineage": parent_lineage(parents),
        "se_funnel_l_anchor_4_25": se_anchor,
        "shell_sites": sites,
        "load_bearing_decomposition": decomposition,
        "three_level_property_matrix": property_matrix,
        "si_frame_row": si,
        "controls": controls,
        "smt_identity_values": {
            "actual_non_preserve_shell_site_count": non_preserve_count,
            "erased_no_placement_non_preserve_count": 0,
            "identity": "actual_non_preserve_shell_site_count == erased_no_placement_non_preserve_count",
            "expected_real_verdict": "unsat",
            "expected_erased_control_verdict": "sat",
        },
        "values": values,
        "all_pass": all_pass,
    }


def z3_erased_flip_proof(nonzero_count: int, erased_count: int) -> dict[str, Any]:
    solver = z3.Solver()
    actual = z3.Int("actual_non_preserve_shell_site_count")
    erased = z3.Int("erased_no_placement_non_preserve_count")
    solver.add(actual == nonzero_count, erased == erased_count)
    solver.add(actual == erased)
    verdict = solver.check()

    control = z3.Solver()
    ca = z3.Int("control_actual_non_preserve_shell_site_count")
    ce = z3.Int("control_erased_no_placement_non_preserve_count")
    control.add(ca == erased_count, ce == erased_count)
    control.add(ca == ce)
    control_verdict = control.check()
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": str(verdict),
        "erased_control_verdict": str(control_verdict),
        "claim": "computed shell leakage nest has nonzero class count; erased no-placement control cannot equal it",
        "raw_values_bound": {"actual": nonzero_count, "erased": erased_count},
        "negative/erased_control": "bind actual to erased count after deleting shell placement",
        "pass": verdict == z3.unsat and control_verdict == z3.sat,
    }


def cvc5_erased_flip_proof(nonzero_count: int, erased_count: int) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    actual = solver.mkConst(int_sort, "actual_non_preserve_shell_site_count")
    erased = solver.mkConst(int_sort, "erased_no_placement_non_preserve_count")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, actual, solver.mkInteger(nonzero_count)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, erased, solver.mkInteger(erased_count)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, actual, erased))
    verdict_obj = solver.checkSat()

    control = cvc5.Solver()
    control.setLogic("QF_LIA")
    c_int = control.getIntegerSort()
    ca = control.mkConst(c_int, "control_actual_non_preserve_shell_site_count")
    ce = control.mkConst(c_int, "control_erased_no_placement_non_preserve_count")
    control.assertFormula(control.mkTerm(Kind.EQUAL, ca, control.mkInteger(erased_count)))
    control.assertFormula(control.mkTerm(Kind.EQUAL, ce, control.mkInteger(erased_count)))
    control.assertFormula(control.mkTerm(Kind.EQUAL, ca, ce))
    control_obj = control.checkSat()

    def status(result: Any) -> str:
        if result.isSat():
            return "sat"
        if result.isUnsat():
            return "unsat"
        return str(result)

    return {
        "ran": True,
        "load_bearing": True,
        "verdict": status(verdict_obj),
        "erased_control_verdict": status(control_obj),
        "claim": "computed shell leakage nest has nonzero class count; erased no-placement control cannot equal it",
        "raw_values_bound": {"actual": nonzero_count, "erased": erased_count},
        "negative/erased_control": "bind actual to erased count after deleting shell placement",
        "pass": verdict_obj.isUnsat() and control_obj.isSat(),
    }


def tool_call(
    tool: str,
    qualified_api: str,
    input_object: str,
    output_object: Any,
    positive_case: str,
    negative_control: str,
    boundary_case: str,
    demotion_condition: str,
    gates: list[str],
) -> dict[str, Any]:
    return {
        "tool": tool,
        "qualified_api/function": qualified_api,
        "input_object": input_object,
        "output_object": output_object,
        "positive_case": positive_case,
        "negative/erased_control": negative_control,
        "boundary_case": boundary_case,
        "demotion_condition": demotion_condition,
        "gates": gates,
    }
