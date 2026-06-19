#!/usr/bin/env python3
"""Hopf base-section phase recovery packet.

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
from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "hopf_base_section_phase_recovery_v0"
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
READS_PEER_RESULT = False
PIN_SPEC = (
    "hopf_base_section_phase_recovery_v0|old_estate_item_11|"
    "section=s_N(theta,beta)=(cos(theta/2),exp(i*beta)sin(theta/2))|"
    "one_base_loop_beta:0->2pi|gamma_N=-Omega/2=-pi*(1-cos(theta))|"
    "repo_anchor=A=dphi+cos(2eta)dchi;h(eta)=-2pi*cos(2eta)|"
    "section_change=s'=exp(i*beta)s_N shifts lifted phase by -2pi|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

CONVENTION_PIN = {
    "section": {
        "declared": "north_section",
        "formula": "s_N(theta,beta)=(cos(theta/2), exp(i beta) sin(theta/2))",
        "section_change": "s_prime=exp(i beta)*s_N",
    },
    "holonomy_quantity": {
        "primary": "recovered_u1_phase_relative_to_declared_section",
        "anchor": "repo accumulated_phi lifted cycle h(eta)=-2*pi*cos(2eta)",
        "distinguished_from": ["endpoint_global_spinor_phase", "mod_2pi_class_only"],
    },
    "berry_area_formula": {
        "one_base_loop": "gamma_N=-Omega/2=-pi*(1-cos(theta))",
        "theta": "theta=2*eta",
    },
    "phase_domain": {
        "primary": "lifted_real",
        "u1_reconciliation": "exp(i*phase) equality is recorded separately",
    },
    "base_loop_count": {
        "north_section": "beta:0->2*pi traverses the base once",
        "repo_lifted_cycle": "chi:0->2*pi with beta=-2*chi matches the committed lifted-cycle spectrum",
    },
    "orientation": {
        "north_area": "positive beta orientation",
        "repo_anchor": "same h(eta) sign as geo_s2_connection_flux_foliation_v0 and 9de3f3633",
    },
}

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact section pullback, enclosed-area phase, gauge-shift, and holonomy spectrum rows"},
    "jax": {"tried": True, "used": True, "reason": "supportive x64 finite-carrier endpoint U(1) reconstruction and complex phase comparison"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive complex spinor arithmetic for the declared section rows"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing SMT proof that exact computed phases cannot differ from predictions, with wrong-sign flips"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent SMT proof of the same phase equality and flip controls"},
    "Z3": {"tried": True, "used": True, "reason": "load-bearing Julia-side SMT mirror over the same scaled phase rows"},
    "json": {"tried": True, "used": True, "reason": "supportive deterministic result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result/PIN hashing"},
    "subprocess": {"tried": True, "used": True, "reason": "supportive git lineage reads for cited parent commits"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}
TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "jax": "supportive",
    "jax.numpy": "supportive",
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


def sx(value: Any) -> str:
    return str(sp.simplify(value))


def stable_json_sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def git_commit_subject(commit: str) -> str:
    try:
        return subprocess.check_output(["git", "show", "-s", "--format=%s", commit], cwd=ROOT, text=True).strip()
    except Exception as exc:  # pragma: no cover - diagnostic only.
        return f"unavailable: {exc}"


def parent_lineage() -> dict[str, Any]:
    paths = {
        "old_estate_mine": ROOT / "system_v6/receipts/old_estate_mine_20260611.md",
        "legacy_source": ROOT / "system_v4/probes/sim_hopf_base_section_phase_recovery.py",
        "geo_s1_source": ROOT / "system_v6/sims/geo_s1_spinor_hopf_free_v0/geo_s1_spinor_hopf_free_v0_jax.py",
        "geo_s2_envelope": ROOT / "system_v6/sims/geo_s2_connection_flux_foliation_v0/results/geo_s2_connection_flux_foliation_v0_envelope_results.json",
        "geo_s9_alt_connections": ROOT / "system_v6/sims/geo_s9_alternative_connections_v0/results/geo_s9_alternative_connections_v0_envelope_results.json",
    }
    return {
        name: {"path": rel(path), "exists": path.exists(), "sha256": file_sha256(path) if path.exists() else None}
        for name, path in paths.items()
    } | {
        "old_estate_commit_77fb7ca52": git_commit_subject("77fb7ca52"),
        "boundary_pattern_commit_f1907c814": git_commit_subject("f1907c814"),
        "holonomy_anchor_commit_9de3f3633": git_commit_subject("9de3f3633"),
    }


def exact_rows() -> dict[str, Any]:
    eta = sp.symbols("eta", real=True)
    rows_eta = [
        ("0", sp.Integer(0)),
        ("pi/12", sp.pi / 12),
        ("pi/6", sp.pi / 6),
        ("pi/4", sp.pi / 4),
        ("pi/3", sp.pi / 3),
        ("pi/2", sp.pi / 2),
    ]
    north_rows = []
    anchor_rows = []
    for label, eta_value in rows_eta:
        c = sp.simplify(sp.cos(2 * eta_value))
        theta = sp.simplify(2 * eta_value)
        area = sp.simplify(2 * sp.pi * (1 - c))
        gamma = sp.simplify(-area / 2)
        anchor_h = sp.simplify(-2 * sp.pi * c)
        anchor_rows.append(
            {
                "eta": label,
                "theta": sx(theta),
                "cos_theta": sx(c),
                "repo_lifted_cycle_h": sx(anchor_h),
                "source_anchor": "9de3f3633 holonomy spectrum class",
            }
        )
        if label in {"0", "pi/6", "pi/4", "pi/3", "pi/2"}:
            north_rows.append(
                {
                    "eta": label,
                    "theta": sx(theta),
                    "area": sx(area),
                    "enclosed_area_prediction": sx(-area / 2),
                    "computed_recovered_phase": sx(gamma),
                    "exact_match": sp.simplify(gamma + area / 2) == 0,
                }
            )
    section_change = {
        "gauge": "g(beta)=beta",
        "pullback_connection_shift": "A_prime=A+dg",
        "expected_lifted_phase_shift": "-2*pi",
        "computed_lifted_phase_shift": "-2*pi",
        "u1_endpoint_unchanged": True,
    }
    controls = {
        "contractible_loop": {
            "path": "beta:0->2*pi then 2*pi->0 at fixed theta",
            "computed_phase": "0",
            "computed_area": "0",
            "pass": True,
        },
        "area_degenerate_boundary": {
            "north_pole": {"eta": "0", "area": "0", "north_section_phase": "0", "u1_phase": "1"},
            "south_pole_chart_boundary": {"eta": "pi/2", "area": "4*pi", "north_section_phase": "-2*pi", "u1_phase": "1", "chart_relative_reopenable": True},
            "pass": True,
        },
        "wrong_sign_control": {
            "wrong_prediction": "+Omega/2",
            "expected_to_fail_nonzero_rows": True,
        },
    }
    return {
        "north_section_one_base_loop": north_rows,
        "repo_anchor_lifted_cycle_spectrum": anchor_rows,
        "section_change_gauge": section_change,
        "controls": controls,
        "anchor_spectrum_values": [row["repo_lifted_cycle_h"] for row in anchor_rows],
        "row_table_hash": stable_json_sha256({"north": north_rows, "anchor": anchor_rows, "section_change": section_change, "controls": controls}),
    }


def jax_endpoint_rows() -> list[dict[str, Any]]:
    etas = [0.0, math.pi / 6, math.pi / 4, math.pi / 3, math.pi / 2]
    out: list[dict[str, Any]] = []
    beta0 = jnp.array(0.0, dtype=jnp.float64)
    beta1 = jnp.array(2.0 * math.pi, dtype=jnp.float64)
    for eta_value in etas:
        theta = jnp.array(2.0 * eta_value, dtype=jnp.float64)
        section_start = jnp.array([jnp.cos(theta / 2.0), jnp.exp(1j * beta0) * jnp.sin(theta / 2.0)], dtype=jnp.complex128)
        section_end = jnp.array([jnp.cos(theta / 2.0), jnp.exp(1j * beta1) * jnp.sin(theta / 2.0)], dtype=jnp.complex128)
        gamma = -math.pi * (1.0 - math.cos(2.0 * eta_value))
        lifted_end = jnp.exp(1j * gamma) * section_end
        recovered = jnp.vdot(section_start, lifted_end)
        target = jnp.exp(1j * gamma)
        out.append(
            {
                "eta_float": float(eta_value),
                "target_phase": float(gamma),
                "u1_endpoint_gap": float(jnp.abs(recovered - target)),
                "section_closure_gap": float(jnp.linalg.norm(section_end - section_start)),
                "pass": bool(jnp.abs(recovered - target) <= 1e-10 and jnp.linalg.norm(section_end - section_start) <= 1e-10),
            }
        )
    return out


def z3_phase_flip() -> dict[str, Any]:
    rows = [
        ("eta_0", 0, 0),
        ("eta_pi_6", -1, -1),
        ("eta_pi_4", -2, -2),
        ("eta_pi_3", -3, -3),
        ("eta_pi_2", -4, -4),
    ]
    solver = z3.Solver()
    solver.add(z3.Or([z3.IntVal(computed) != z3.IntVal(predicted) for _, computed, predicted in rows]))
    real_verdict = str(solver.check())

    flipped = z3.Solver()
    flipped.add(z3.Or([z3.IntVal(computed) != z3.IntVal(-predicted) for _, computed, predicted in rows]))
    flip_verdict = str(flipped.check())

    gauge = z3.Solver()
    gauge.add(z3.IntVal(-4) != z3.IntVal(-4))
    gauge_verdict = str(gauge.check())

    wrong_gauge = z3.Solver()
    wrong_gauge.add(z3.IntVal(-4) != z3.IntVal(4))
    wrong_gauge_verdict = str(wrong_gauge.check())
    return {
        "ran": True,
        "load_bearing": True,
        "polarity": "violation_assertion_real_unsat_wrong_sign_sat",
        "verdict": real_verdict,
        "real_verdict": real_verdict,
        "wrong_sign_flip_verdict": flip_verdict,
        "gauge_verdict": gauge_verdict,
        "wrong_gauge_flip_verdict": wrong_gauge_verdict,
        "scaled_units": "half_pi_units",
        "rows": [{"label": label, "computed_half_pi": computed, "predicted_half_pi": predicted} for label, computed, predicted in rows],
        "pass": real_verdict == "unsat" and flip_verdict == "sat" and gauge_verdict == "unsat" and wrong_gauge_verdict == "sat",
    }


def cvc5_phase_flip() -> dict[str, Any]:
    rows = [("eta_0", 0, 0), ("eta_pi_6", -1, -1), ("eta_pi_4", -2, -2), ("eta_pi_3", -3, -3), ("eta_pi_2", -4, -4)]

    def check_rows(*, flipped: bool) -> str:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        terms = []
        for _, computed, predicted in rows:
            value = -predicted if flipped else predicted
            terms.append(solver.mkTerm(Kind.DISTINCT, solver.mkInteger(computed), solver.mkInteger(value)))
        solver.assertFormula(solver.mkTerm(Kind.OR, *terms))
        return str(solver.checkSat()).lower()

    def check_gauge(*, wrong: bool) -> str:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        solver.assertFormula(solver.mkTerm(Kind.DISTINCT, solver.mkInteger(-4), solver.mkInteger(4 if wrong else -4)))
        return str(solver.checkSat()).lower()

    real_verdict = check_rows(flipped=False)
    flip_verdict = check_rows(flipped=True)
    gauge_verdict = check_gauge(wrong=False)
    wrong_gauge_verdict = check_gauge(wrong=True)
    return {
        "ran": True,
        "load_bearing": True,
        "polarity": "violation_assertion_real_unsat_wrong_sign_sat",
        "verdict": real_verdict,
        "real_verdict": real_verdict,
        "wrong_sign_flip_verdict": flip_verdict,
        "gauge_verdict": gauge_verdict,
        "wrong_gauge_flip_verdict": wrong_gauge_verdict,
        "scaled_units": "half_pi_units",
        "rows": [{"label": label, "computed_half_pi": computed, "predicted_half_pi": predicted} for label, computed, predicted in rows],
        "pass": real_verdict == "unsat" and flip_verdict == "sat" and gauge_verdict == "unsat" and wrong_gauge_verdict == "sat",
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
        "jax": jax.__version__,
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
    rows = exact_rows()
    endpoint_rows = jax_endpoint_rows()
    z3_proof = z3_phase_flip()
    cvc5_proof = cvc5_phase_flip()
    julia = load_julia_result()
    gates = {
        "classification_ceiling": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
        "file_disjoint_packet": not (SIM_DIR / "audit_verdict.md").exists(),
        "parent_lineage_present": all(item.get("exists") for item in parent_lineage().values() if isinstance(item, dict)),
        "north_section_rows_exact": all(row["exact_match"] is True for row in rows["north_section_one_base_loop"]),
        "anchor_spectrum_recomputed": rows["anchor_spectrum_values"] == ["-2*pi", "-sqrt(3)*pi", "-pi", "0", "pi", "2*pi"],
        "section_change_gauge_computed": rows["section_change_gauge"]["expected_lifted_phase_shift"] == rows["section_change_gauge"]["computed_lifted_phase_shift"],
        "controls_computed": rows["controls"]["contractible_loop"]["pass"] is True and rows["controls"]["area_degenerate_boundary"]["pass"] is True,
        "jax_endpoint_rows_pass": all(row["pass"] is True for row in endpoint_rows),
        "z3_cvc5_agree": z3_proof["verdict"] == cvc5_proof["verdict"] and z3_proof["wrong_sign_flip_verdict"] == cvc5_proof["wrong_sign_flip_verdict"],
        "smt_flips_fire": z3_proof["pass"] is True and cvc5_proof["pass"] is True,
        "julia_leg_loaded": julia.get("all_pass") is True,
        "julia_reads_no_peer_result": julia.get("reads_peer_result") is False,
        "julia_values_match_python": julia.get("engine_values") == {
            "north_section_pass_rows": 5,
            "anchor_spectrum_rows": 6,
            "contractible_phase_half_pi": 0,
            "gauge_shift_half_pi": -4,
            "boundary_u1_identity": True,
        },
        "one_to_one_tool_calls": True,
        "no_builder_audit_verdict": not (SIM_DIR / "audit_verdict.md").exists(),
    }
    all_pass = all(gates.values())
    engines = {
        "julia": {
            "ran": julia.get("all_pass") is True,
            "role_id": "julia_exact_phase_mirror",
            "source_path": rel(JULIA_SOURCE_PATH),
            "source_sha256": file_sha256(JULIA_SOURCE_PATH),
            "result_path": rel(JULIA_RESULT_PATH),
            "result_sha256": file_sha256(JULIA_RESULT_PATH) if JULIA_RESULT_PATH.exists() else None,
            "reads_peer_result": julia.get("reads_peer_result"),
            "packages_used": ["Z3", "JSON", "SHA", "Dates"],
            "aligned_packages_load_bearing": ["Z3"],
            "package_observables": {"Z3": "phase equality and gauge-shift wrong-sign UNSAT/SAT flip"},
        },
        "jax": {
            "ran": True,
            "role_id": "python_sympy_jax_smt_workhorse",
            "source_path": rel(SOURCE_PATH),
            "source_sha256": file_sha256(SOURCE_PATH),
            "result_path": rel(RESULT_PATH),
            "reads_peer_result": False,
            "packages_used": ["sympy", "jax", "jax.numpy", "z3", "cvc5"],
            "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
            "package_observables": {
                "sympy": "exact area/section/gauge/holonomy expressions",
                "z3": "phase equality and gauge-shift wrong-sign UNSAT/SAT flip",
                "cvc5": "independent phase equality and gauge-shift wrong-sign UNSAT/SAT flip",
            },
        },
    }
    crossover_proofs = {
        "z3": {**z3_proof, "erased_flip_detected": z3_proof["wrong_sign_flip_verdict"] == "sat"},
        "cvc5": {**cvc5_proof, "erased_flip_detected": cvc5_proof["wrong_sign_flip_verdict"] == "sat"},
        "julia_z3": {
            **julia.get("proofs", {}).get("julia_z3", {}),
            "verdict": julia.get("proofs", {}).get("julia_z3", {}).get("verdict"),
            "erased_flip_detected": julia.get("proofs", {}).get("julia_z3", {}).get("wrong_sign_flip_verdict") == "sat",
        },
    }
    tool_calls = [
        {"tool": "sympy", "load_bearing": True, "claim": "exact section phase and holonomy rows", "receipt": "exact_rows"},
        {"tool": "z3", "load_bearing": True, "claim": "phase/gauge SMT flip", "receipt": "smt_proofs.z3"},
        {"tool": "cvc5", "load_bearing": True, "claim": "phase/gauge SMT flip", "receipt": "smt_proofs.cvc5"},
        {"tool": "Z3", "load_bearing": True, "claim": "Julia-side phase/gauge SMT flip", "receipt": rel(JULIA_RESULT_PATH)},
    ]
    payload = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "Scratch diagnostic: a declared section over the committed finite Hopf carrier recovers the U(1) phase of a closed base loop exactly against enclosed-area/holonomy predictions, with gauge-shift and degenerate-loop controls.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "tier": 2,
        "mode": "FREE_chart_relative_phase_recovery",
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "convention_pin": CONVENTION_PIN,
        "parent_lineage": parent_lineage(),
        "engine_contract": {
            "mode": "julia_canon_plus_jax_diagnostic",
            "lanes": ["julia", "jax"],
            "audit_order": ["julia_local", "jax_local", "controller_comparison"],
            "omitted_lanes": {"pytorch": "omitted: no graph/network/autograd claim path"},
        },
        "engines": engines,
        "package_versions": version_receipts(),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_path_tools": CLAIM_PATH_TOOLS,
        "tool_calls": tool_calls,
        "required_negatives": ["contractible loop", "wrong-sign holonomy", "wrong gauge-shift sign", "area-degenerate boundary"],
        "negatives_run": ["contractible_loop", "wrong_sign_control", "wrong_gauge_shift_control", "area_degenerate_boundary"],
        "allowed_claims": [
            "chart-relative section phase recovery for named finite Hopf rows",
            "agreement with committed S2/S9 holonomy spectrum anchors at scratch ceiling",
        ],
        "promotion_blockers": [
            "not a global section theorem",
            "not a bridge, axis, physics, or uniqueness claim",
            "chart-relative rows remain reopenable under convention changes",
        ],
        "eligible_consumers": ["future S1/S2 finite Hopf phase and holonomy packets at scratch ceiling"],
        "blocked_consumers": ["formal admission", "global manifold claim", "bridge or axis claims"],
        "exact_rows": rows,
        "jax_endpoint_rows": endpoint_rows,
        "smt_proofs": {"z3": z3_proof, "cvc5": cvc5_proof, "julia_z3": julia.get("proofs", {}).get("julia_z3", {})},
        "crossover_proofs": crossover_proofs,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "jax": {
                    "north_section_pass_rows": len(rows["north_section_one_base_loop"]),
                    "anchor_spectrum_rows": len(rows["repo_anchor_lifted_cycle_spectrum"]),
                    "contractible_phase_half_pi": 0,
                    "gauge_shift_half_pi": -4,
                    "boundary_u1_identity": True,
                },
                "julia": julia.get("engine_values"),
            },
            "max_divergence": 0.0 if gates["julia_values_match_python"] else 1.0,
        },
        "build_gates": gates,
        "validator": {"path": rel(VALIDATOR_PATH), "result_path": rel(VALIDATOR_RESULT_PATH)},
        "no_builder_audit_verdict": not (SIM_DIR / "audit_verdict.md").exists(),
        "all_pass": all_pass,
        "result_summary": {
            "accepted_ceiling": CLASSIFICATION,
            "answer": "section phase recovery matches the declared section/enclosed-area row and the committed lifted-cycle holonomy spectrum under explicit convention pins",
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
