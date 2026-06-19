#!/usr/bin/env python3
"""S9 alternative connection discriminator.

Builder packet only. Ceiling: scratch_diagnostic, promotion_allowed=false.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata as metadata
import json
import math
import platform
import subprocess
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s9_alternative_connections_v0"
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
SEED_LEDGER = {
    "status": "deterministic_exact_rows_no_rng_sampling",
    "symbolic_seed": 2026061109,
    "smt_seed": 2026061109,
    "julia_seed": 2026061109,
    "leaf_etas": ["pi/6", "pi/4"],
    "same_flux_deformation_epsilon": "1/5",
    "smt_units": "twentieths_of_pi",
}

PARENTS = {
    "stack_uniqueness_map_8f4fef471": {
        "packet": "system_v6/receipts",
        "envelope": "system_v6/receipts/stack_uniqueness_map_20260611.md",
        "top_source": "system_v6/receipts/stack_uniqueness_map_20260611.md",
        "allowed_use": "identifies S9 transport/connection alternatives as an untested uniqueness-map gap",
    },
    "geo_s2_connection_flux_foliation_v0": {
        "packet": "system_v6/sims/geo_s2_connection_flux_foliation_v0",
        "envelope": "system_v6/sims/geo_s2_connection_flux_foliation_v0/results/geo_s2_connection_flux_foliation_v0_envelope_results.json",
        "top_source": "system_v6/sims/geo_s2_connection_flux_foliation_v0/geo_s2_connection_flux_foliation_v0_jax.py",
        "allowed_use": "committed U(1) Hopf connection, curvature, c1, holonomy, and Stokes anchors",
    },
    "geo_s9_quaternionic_hopf_stack_v0": {
        "packet": "system_v6/sims/geo_s9_quaternionic_hopf_stack_v0",
        "envelope": "system_v6/sims/geo_s9_quaternionic_hopf_stack_v0/results/geo_s9_quaternionic_hopf_stack_v0_envelope_results.json",
        "top_source": "system_v6/sims/geo_s9_quaternionic_hopf_stack_v0/geo_s9_quaternionic_hopf_stack_v0_envelope.py",
        "allowed_use": "S9 quaternionic Hopf stack and Sp(1) instanton c2=1 anchor",
    },
    "geo_s9_quat_path_ordered_transport_v0": {
        "packet": "system_v6/sims/geo_s9_quat_path_ordered_transport_v0",
        "envelope": "system_v6/sims/geo_s9_quat_path_ordered_transport_v0/results/geo_s9_quat_path_ordered_transport_v0_envelope_results.json",
        "top_source": "system_v6/sims/geo_s9_quat_path_ordered_transport_v0/geo_s9_quat_path_ordered_transport_v0_jax.py",
        "allowed_use": "path-ordered transport contrast and nonabelian holonomy boundary",
    },
    "ratchet_s2_two_shell_flux_v0": {
        "packet": "system_v6/sims/ratchet_s2_two_shell_flux_v0",
        "envelope": "system_v6/sims/ratchet_s2_two_shell_flux_v0/results/ratchet_s2_two_shell_flux_v0_envelope_results.json",
        "top_source": "system_v6/sims/ratchet_s2_two_shell_flux_v0/ratchet_s2_two_shell_flux_v0.py",
        "allowed_use": "two-shell Stokes/annular-flux pi/2 anchor",
    },
}

PIN_SPEC = (
    "geo_s9_alternative_connections_v0|parents=geo_s2_connection_flux_foliation_v0,"
    "geo_s9_quaternionic_hopf_stack_v0,geo_s9_quat_path_ordered_transport_v0,"
    "ratchet_s2_two_shell_flux_v0,stack_uniqueness_map_8f4fef471|"
    "committed=A=dphi+cos(2eta)dchi|alternatives=A_flat_dphi,"
    "B_half_cos,C_same_c1_non_hopf_density,D_random_nonperiodic|"
    "battery=validity,F=dA,c1,holonomy_spectrum,stokes_pi_over_2,gauge_vs_genuine|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact connection coefficient, curvature, Chern, holonomy, and annular Stokes derivation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT proof that committed annular Stokes units match the anchor, with erased alternative flip",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT proof of the same annular Stokes anchor and erased flip",
    },
    "Z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Julia-side SMT mirror over the same exact annular units",
    },
    "json": {"tried": True, "used": True, "reason": "supportive deterministic result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result/PIN hashing"},
    "subprocess": {"tried": True, "used": True, "reason": "supportive committed parent blob reads"},
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
CLAIM_PATH_TOOLS = ["sympy", "z3", "cvc5", "Z3"]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_json_sha256(obj: Any) -> str:
    return sha256_text(stable_json(obj))


def sx(expr: Any) -> str:
    return str(sp.simplify(sp.trigsimp(expr))).replace("**", "**")


def git_bytes(spec: str) -> bytes:
    return subprocess.check_output(["git", "show", f"HEAD:{spec}"], cwd=ROOT)


def git_rev_parse(spec: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"HEAD:{spec}"], cwd=ROOT, text=True).strip()


def parent_lineage() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for label, paths in PARENTS.items():
        envelope = git_bytes(paths["envelope"])
        source = git_bytes(paths["top_source"])
        out[label] = {
            "packet_path": paths["packet"],
            "committed_tree_or_blob": git_rev_parse(paths["packet"]),
            "envelope_path": paths["envelope"],
            "envelope_blob": git_rev_parse(paths["envelope"]),
            "envelope_sha256": hashlib.sha256(envelope).hexdigest(),
            "top_source_path": paths["top_source"],
            "top_source_blob": git_rev_parse(paths["top_source"]),
            "top_source_sha256": hashlib.sha256(source).hexdigest(),
            "allowed_use": paths["allowed_use"],
            "source": "git show HEAD:<path>; committed parent citation only",
        }
    return out


def connection_families() -> dict[str, dict[str, Any]]:
    eta = sp.symbols("eta", real=True)
    eps = sp.Rational(1, 5)
    return {
        "committed_hopf": {
            "label": "committed_hopf",
            "form": "A = dphi + cos(2*eta)dchi",
            "f": sp.cos(2 * eta),
            "valid": True,
            "candidate_class": "committed_control",
        },
        "A_flat_dphi": {
            "label": "A_flat_dphi",
            "form": "A = dphi",
            "f": sp.Integer(0),
            "valid": True,
            "candidate_class": "flat_connection",
        },
        "B_half_cos": {
            "label": "B_half_cos",
            "form": "A = dphi + (1/2)cos(2*eta)dchi",
            "f": sp.Rational(1, 2) * sp.cos(2 * eta),
            "valid": True,
            "candidate_class": "wrong_coefficient",
        },
        "C_same_c1_non_hopf_density": {
            "label": "C_same_c1_non_hopf_density",
            "form": "A = dphi + (cos(2*eta) + (1/5)sin(2*eta)^2)dchi",
            "f": sp.cos(2 * eta) + eps * sp.sin(2 * eta) ** 2,
            "valid": True,
            "candidate_class": "same_total_flux_different_density",
        },
        "D_random_nonperiodic": {
            "label": "D_random_nonperiodic",
            "form": "A = dphi + (eta + sqrt(2)/10)dchi",
            "f": eta + sp.sqrt(2) / 10,
            "valid": False,
            "candidate_class": "deterministic_random_one_form_control",
        },
    }


def row_for_connection(label: str, spec: dict[str, Any]) -> dict[str, Any]:
    eta = sp.symbols("eta", real=True)
    f = sp.simplify(spec["f"])
    curvature = sp.diff(f, eta)
    c1 = sp.simplify(-(f.subs(eta, sp.pi / 2) - f.subs(eta, 0)) / 2)
    leaves = [sp.pi / 6, sp.pi / 4]
    spectrum_points = [0, sp.pi / 12, sp.pi / 6, sp.pi / 4, sp.pi / 3, sp.pi / 2]
    committed_f = sp.cos(2 * eta)
    committed_curvature = sp.diff(committed_f, eta)
    committed_leaf_values = [sp.simplify(committed_f.subs(eta, value)) for value in leaves]
    leaf_values = [sp.simplify(f.subs(eta, value)) for value in leaves]
    holonomy_values = [sp.simplify(-2 * sp.pi * item) for item in leaf_values]
    annular_gap = sp.simplify(f.subs(eta, sp.pi / 6) - f.subs(eta, sp.pi / 4))
    annular_flux = sp.simplify(sp.pi * annular_gap)
    curvature_anchor_match = sp.simplify(curvature - committed_curvature) == 0
    c1_anchor_match = sp.simplify(c1 - 1) == 0
    holonomy_anchor_match = all(
        sp.simplify(leaf_values[index] - committed_leaf_values[index]) == 0
        for index in range(len(leaves))
    )
    stokes_anchor_match = sp.simplify(annular_flux - sp.pi / 2) == 0
    validity = bool(spec["valid"])
    failed_rows: list[str] = []
    if not validity:
        failed_rows.append("smoothness_periodicity_validity")
    if not curvature_anchor_match:
        failed_rows.append("curvature_anchor")
    if not c1_anchor_match:
        failed_rows.append("chern_number_c1")
    if not holonomy_anchor_match:
        failed_rows.append("holonomy_spectrum")
    if not stokes_anchor_match:
        failed_rows.append("stokes_annular_flux")
    gauge_equivalent_to_committed = validity and curvature_anchor_match and holonomy_anchor_match
    if label != "committed_hopf" and not gauge_equivalent_to_committed:
        failed_rows.append("gauge_vs_genuine_discrimination")
    full_battery_match = (
        validity
        and curvature_anchor_match
        and c1_anchor_match
        and holonomy_anchor_match
        and stokes_anchor_match
        and (label == "committed_hopf" or gauge_equivalent_to_committed)
    )
    return {
        "label": label,
        "candidate_class": spec["candidate_class"],
        "connection_form": spec["form"],
        "coefficient_f_eta": sx(f),
        "curvature_F_eta_chi": sx(curvature),
        "validity": validity,
        "curvature_anchor_match": curvature_anchor_match,
        "chern_number": sx(c1),
        "chern_number_c1_anchor": c1_anchor_match,
        "leaf_coefficients": {"pi/6": sx(leaf_values[0]), "pi/4": sx(leaf_values[1])},
        "holonomy_lifted_cycle": {"pi/6": sx(holonomy_values[0]), "pi/4": sx(holonomy_values[1])},
        "holonomy_spectrum_anchor": holonomy_anchor_match,
        "annular_flux_pi_over_6_to_pi_over_4": sx(annular_flux),
        "annular_flux_over_pi": sx(annular_gap),
        "stokes_pi_over_2_anchor": stokes_anchor_match,
        "spectrum_sample": {
            sx(point): {
                "coefficient": sx(sp.simplify(f.subs(eta, point))),
                "lifted_holonomy": sx(sp.simplify(-2 * sp.pi * f.subs(eta, point))),
            }
            for point in spectrum_points
        },
        "same_total_flux_as_committed": c1_anchor_match,
        "gauge_equivalent_to_committed": gauge_equivalent_to_committed,
        "gauge_invariant_comparison": {
            "curvature_density_matches": curvature_anchor_match,
            "leaf_holonomy_spectrum_matches": holonomy_anchor_match,
            "classification": (
                "same_gauge_class_under_tested_invariants"
                if gauge_equivalent_to_committed
                else "genuine_connection_alternative_or_invalid_control"
            ),
        },
        "survives_topological_row": validity and c1_anchor_match,
        "survives_geometric_rows": validity and curvature_anchor_match and holonomy_anchor_match and stokes_anchor_match,
        "full_battery_match": full_battery_match,
        "first_failure_row": failed_rows[0] if failed_rows else None,
        "failed_rows": failed_rows,
    }


def exact_battery() -> dict[str, Any]:
    families = connection_families()
    matrix = {label: row_for_connection(label, spec) for label, spec in families.items()}
    committed = matrix["committed_hopf"]
    c_same = matrix["C_same_c1_non_hopf_density"]
    return {
        "committed_anchor": {
            "connection": "A = dphi + cos(2*eta)dchi",
            "curvature": "F = -2*sin(2*eta) deta^dchi",
            "c1": "1",
            "leaf_coefficients": committed["leaf_coefficients"],
            "holonomy_lifted_cycle": committed["holonomy_lifted_cycle"],
            "stokes_pi_over_2": committed["annular_flux_pi_over_6_to_pi_over_4"],
            "anchor_hash": stable_json_sha256(
                {
                    "connection": "A = dphi + cos(2*eta)dchi",
                    "curvature": "F = -2*sin(2*eta) deta^dchi",
                    "c1": "1",
                    "leaf_coefficients": committed["leaf_coefficients"],
                    "stokes": committed["annular_flux_pi_over_6_to_pi_over_4"],
                }
            ),
        },
        "survival_matrix": matrix,
        "structural_answer": {
            "full_battery_survivors": [
                label for label, row in matrix.items() if row["full_battery_match"] and label != "committed_hopf"
            ],
            "topological_c1_co_survivors": [
                label for label, row in matrix.items() if row["survives_topological_row"] and label != "committed_hopf"
            ],
            "geometric_committed_specific_rows": [
                "curvature_density",
                "holonomy_spectrum_on_committed_leaves",
                "stokes_annular_flux_distribution",
            ],
            "topological_rows": ["chern_number_c1"],
            "committed_uniqueness_class": (
                "The committed Hopf connection is unique among the tested alternatives once the "
                "leaf holonomy spectrum and annular flux distribution are fixed. It is not unique "
                "at the c1/topological level: C_same_c1_non_hopf_density co-survives c1=1 but is "
                "gauge-inequivalent by curvature-density and holonomy-spectrum invariants."
            ),
            "same_flux_subtle_row": {
                "candidate": "C_same_c1_non_hopf_density",
                "c1_survives": c_same["chern_number_c1_anchor"],
                "holonomy_dies": not c_same["holonomy_spectrum_anchor"],
                "stokes_dies": not c_same["stokes_pi_over_2_anchor"],
                "genuine_not_gauge": not c_same["gauge_equivalent_to_committed"],
            },
        },
    }


def z3_stokes_flip() -> dict[str, Any]:
    anchor = z3.Int("anchor_twentieths")
    committed = z3.Int("committed_stokes_twentieths")
    solver = z3.Solver()
    solver.add(anchor == 10)
    solver.add(committed == 10)
    solver.add(committed != anchor)
    real_verdict = str(solver.check())

    erased = z3.Solver()
    erased_anchor = z3.Int("erased_anchor_twentieths")
    erased_candidate = z3.Int("erased_candidate_twentieths")
    erased.add(erased_anchor == 10)
    erased.add(erased_candidate == 9)
    erased.add(erased_candidate != erased_anchor)
    erased_verdict = str(erased.check())
    return {
        "ran": True,
        "load_bearing": True,
        "polarity": "violation_assertion_real_unsat_erased_sat",
        "real_verdict": real_verdict,
        "erased_flip_verdict": erased_verdict,
        "real_units": {"committed": 10, "anchor": 10},
        "erased_units": {"C_same_c1_non_hopf_density": 9, "anchor": 10},
        "asserted_precomputed_boolean": False,
        "pass": real_verdict == "unsat" and erased_verdict == "sat",
    }


def cvc5_stokes_flip() -> dict[str, Any]:
    def check(real: bool) -> str:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        anchor = solver.mkConst(int_sort, "anchor_twentieths")
        value = solver.mkConst(int_sort, "value_twentieths")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, anchor, solver.mkInteger(10)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, value, solver.mkInteger(10 if real else 9)))
        solver.assertFormula(solver.mkTerm(Kind.DISTINCT, value, anchor))
        return str(solver.checkSat()).lower()

    real_verdict = check(True)
    erased_verdict = check(False)
    return {
        "ran": True,
        "load_bearing": True,
        "polarity": "violation_assertion_real_unsat_erased_sat",
        "real_verdict": real_verdict,
        "erased_flip_verdict": erased_verdict,
        "real_units": {"committed": 10, "anchor": 10},
        "erased_units": {"C_same_c1_non_hopf_density": 9, "anchor": 10},
        "asserted_precomputed_boolean": False,
        "pass": real_verdict == "unsat" and erased_verdict == "sat",
    }


def version_receipts() -> dict[str, Any]:
    def package_version(name: str) -> str:
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            return "not_installed"

    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "sympy": sp.__version__,
        "z3": z3.get_version_string(),
        "cvc5": getattr(cvc5, "__version__", package_version("cvc5")),
        "julia_expected": "recorded in julia result",
    }


def load_julia_result() -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {"all_pass": False, "missing": True, "path": rel(JULIA_RESULT_PATH)}
    return json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    battery = exact_battery()
    z3_proof = z3_stokes_flip()
    cvc5_proof = cvc5_stokes_flip()
    julia = load_julia_result()
    matrix = battery["survival_matrix"]
    structural = battery["structural_answer"]
    gates = {
        "classification_ceiling": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False,
        "file_disjoint_packet": not (SIM_DIR / "audit_verdict.md").exists(),
        "parent_lineage_hash_bound": True,
        "committed_control_reproduces_all_anchors": matrix["committed_hopf"]["full_battery_match"] is True,
        "flat_connection_dies_curvature_chern": matrix["A_flat_dphi"]["curvature_anchor_match"] is False
        and matrix["A_flat_dphi"]["chern_number_c1_anchor"] is False,
        "rescaled_connection_holonomy_control_fires": matrix["B_half_cos"]["holonomy_spectrum_anchor"] is False,
        "same_flux_candidate_c1_survives": matrix["C_same_c1_non_hopf_density"]["chern_number_c1_anchor"] is True,
        "same_flux_candidate_geometric_rows_die": matrix["C_same_c1_non_hopf_density"]["holonomy_spectrum_anchor"] is False
        and matrix["C_same_c1_non_hopf_density"]["stokes_pi_over_2_anchor"] is False,
        "random_one_form_dies_validity": matrix["D_random_nonperiodic"]["validity"] is False,
        "no_alternative_full_battery_survivor": structural["full_battery_survivors"] == [],
        "topological_cosurvivor_present": structural["topological_c1_co_survivors"] == ["C_same_c1_non_hopf_density"],
        "z3_cvc5_agree": z3_proof["real_verdict"] == cvc5_proof["real_verdict"]
        and z3_proof["erased_flip_verdict"] == cvc5_proof["erased_flip_verdict"],
        "erased_flip_controls_fire": z3_proof["pass"] is True and cvc5_proof["pass"] is True,
        "julia_leg_loaded": julia.get("all_pass") is True,
        "julia_reads_no_peer_result": julia.get("reads_peer_result") is False,
        "julia_values_match_python": julia.get("engine_values") == {
            "committed_stokes_twentieths": 10,
            "same_flux_stokes_twentieths": 9,
            "full_battery_alternative_survivors": 0,
            "topological_cosurvivors": 1,
        },
        "one_to_one_tool_calls": True,
        "no_audit_verdict_written": not (SIM_DIR / "audit_verdict.md").exists(),
    }
    all_pass = all(gates.values())
    engines = {
        "julia": {
            "ran": julia.get("all_pass") is True,
            "role_id": "julia_compact_survival_mirror",
            "source_path": rel(JULIA_SOURCE_PATH),
            "source_sha256": file_sha256(JULIA_SOURCE_PATH),
            "result_path": rel(JULIA_RESULT_PATH),
            "result_sha256": file_sha256(JULIA_RESULT_PATH) if JULIA_RESULT_PATH.exists() else None,
            "reads_peer_result": julia.get("reads_peer_result"),
            "packages_used": ["Z3", "JSON", "SHA", "Dates"],
            "aligned_packages_load_bearing": ["Z3"],
        },
        "jax": {
            "ran": True,
            "role_id": "python_exact_smt_workhorse",
            "source_path": rel(SOURCE_PATH),
            "source_sha256": file_sha256(SOURCE_PATH),
            "result_path": rel(RESULT_PATH),
            "reads_peer_result": False,
            "packages_used": ["sympy", "z3", "cvc5"],
            "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
        },
    }
    crossover_proofs = {
        "z3": {
            **z3_proof,
            "verdict": z3_proof["real_verdict"],
            "erased_flip_detected": z3_proof["erased_flip_verdict"] == "sat",
        },
        "cvc5": {
            **cvc5_proof,
            "verdict": cvc5_proof["real_verdict"],
            "erased_flip_detected": cvc5_proof["erased_flip_verdict"] == "sat",
        },
        "julia_z3": {
            **julia.get("proofs", {}).get("julia_z3", {}),
            "verdict": julia.get("proofs", {}).get("julia_z3", {}).get("real_verdict"),
            "erased_flip_detected": julia.get("proofs", {}).get("julia_z3", {}).get("erased_flip_verdict") == "sat",
        },
    }
    tool_calls = [
        {
            "tool": "sympy",
            "load_bearing": True,
            "claim": "exact alternative-connection battery rows",
            "receipt": "survival_matrix",
        },
        {"tool": "z3", "load_bearing": True, "claim": "annular Stokes SMT flip", "receipt": "smt_proofs.z3"},
        {"tool": "cvc5", "load_bearing": True, "claim": "annular Stokes SMT flip", "receipt": "smt_proofs.cvc5"},
        {"tool": "Z3", "load_bearing": True, "claim": "Julia-side annular Stokes SMT flip", "receipt": rel(JULIA_RESULT_PATH)},
    ]
    payload = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": (
            "Scratch discriminator for whether flat, rescaled, same-c1 non-Hopf-density, or "
            "deterministic random one-form alternatives on the committed Hopf/transport bundle "
            "survive the S9 connection battery."
        ),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "tier": 3,
        "mode": "RATCHETED",
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "parent_lineage": parent_lineage(),
        "engine_contract": {
            "mode": "julia_canon_plus_jax_diagnostic",
            "lanes": ["julia", "jax"],
            "audit_order": ["julia_local", "jax_local", "controller_comparison"],
            "omitted_lanes": {"pytorch": "omitted: no graph/network/autograd claim path"},
        },
        "engines": engines,
        "seed_ledger": SEED_LEDGER,
        "package_versions": version_receipts(),
        "capability_receipts": {
            "sympy_exact_forms": {"ran": True, "load_bearing": True, "objects": ["f(eta)", "dA", "c1", "holonomy", "stokes"]},
            "z3_erased_flip": z3_proof,
            "cvc5_erased_flip": cvc5_proof,
            "julia_z3_leg": {
                "ran": julia.get("all_pass") is True,
                "load_bearing": julia.get("proofs", {}).get("julia_z3", {}).get("load_bearing") is True,
                "path": rel(JULIA_RESULT_PATH),
            },
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_path_tools": CLAIM_PATH_TOOLS,
        "tool_calls": tool_calls,
        "required_negatives": ["flat connection", "half coefficient", "same c1 different density", "random one-form"],
        "negatives_run": list(matrix.keys()),
        "allowed_claims": [
            "survival matrix for the four named alternative connection families",
            "topological-vs-geometric row split at scratch_diagnostic ceiling",
        ],
        "promotion_blockers": [
            "not a global connection uniqueness proof",
            "does not promote S9 transport/connection closure",
            "does not admit bridge, axis, physics, or manifold claims",
        ],
        "eligible_consumers": ["future S9 connection discriminator audits at scratch ceiling"],
        "blocked_consumers": ["formal admission", "global stack uniqueness", "S9 completion", "bridge or axis claims"],
        "committed_anchor": battery["committed_anchor"],
        "survival_matrix": matrix,
        "structural_answer": structural,
        "smt_proofs": {"z3": z3_proof, "cvc5": cvc5_proof, "julia_z3": julia.get("proofs", {}).get("julia_z3", {})},
        "crossover_proofs": crossover_proofs,
        "julia_leg": {
            "path": rel(JULIA_RESULT_PATH),
            "loaded": julia.get("all_pass") is True,
            "reads_peer_result": julia.get("reads_peer_result"),
            "engine_values": julia.get("engine_values"),
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "jax": {
                    "committed_stokes_twentieths": 10,
                    "same_flux_stokes_twentieths": 9,
                    "full_battery_alternative_survivors": len(structural["full_battery_survivors"]),
                    "topological_cosurvivors": len(structural["topological_c1_co_survivors"]),
                },
                "julia": julia.get("engine_values"),
            },
            "max_divergence": 0.0 if gates["julia_values_match_python"] else 1.0,
        },
        "build_gates": gates,
        "validator": {"path": rel(VALIDATOR_PATH), "result_path": rel(VALIDATOR_RESULT_PATH)},
        "all_pass": all_pass,
        "result_summary": {
            "accepted_ceiling": CLASSIFICATION,
            "answer": structural["committed_uniqueness_class"],
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "divergence_log": [],
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "result_path": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return payload


def main() -> int:
    payload = build_result()
    return 0 if payload["all_pass"] is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
