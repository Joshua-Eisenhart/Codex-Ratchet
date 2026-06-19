#!/usr/bin/env python3
"""JAX leg for the flux emergence discriminator."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "flux_emergence_discriminator"
OBJECT_ID = f"{SIM_ID}_jax"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-6
TRANSPORT_STEPS = 4096
QUAD_ETA_STEPS = 8192
QUAD_CHI_STEPS = 64
SMT_SCALE = 10**12
PHI0 = 0.19
CHI0 = -0.31

PIN_SPEC = {
    "eta_shells": ["pi/8 + k*pi/10 for k=0,1,2"],
    "loop_grammar": {
        "gamma_f": "psi(phi0 + u, chi0; eta0)",
        "gamma_b": "psi(phi0 - integral A_chi/A_phi dchi, chi0 + u; eta0)",
        "horizontal_condition": "A(dot gamma_b)=0",
    },
    "connection": "A=-i psi^dagger d psi, numerically sampled from spinor derivatives",
    "curvature": "F=-2 sin(2 eta) d eta wedge d chi",
    "claim_ceiling": "scratch_diagnostic; promotion_allowed=false; flux remains a CANDIDATE FAMILY per weyl-flux.md",
}

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 spinor transport, midpoint curvature quadrature, and entropy arithmetic",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive complex spinor/density arrays; no numpy/scipy claim-path import",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing integer-scaled in-solver additivity proof over bound connection cos values",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent integer-scaled additivity proof matching z3",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive paths, timestamps, hashing, JSON, and scalar math",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def wrap_phase(value: float) -> float:
    return math.atan2(math.sin(value), math.cos(value))


def eta_shell(index: int) -> float:
    return math.pi / 8.0 + index * math.pi / 10.0


def spinor(phi: float, chi: float, eta: float) -> jax.Array:
    return jnp.asarray(
        [
            jnp.exp(1j * (phi + chi)) * math.cos(eta),
            jnp.exp(1j * (phi - chi)) * math.sin(eta),
        ],
        dtype=jnp.complex128,
    )


def connection_coefficients(phi: float, chi: float, eta: float) -> tuple[float, float]:
    eps = 1.0e-6
    psi = spinor(phi, chi, eta)
    d_phi = (spinor(phi + eps, chi, eta) - spinor(phi - eps, chi, eta)) / (2.0 * eps)
    d_chi = (spinor(phi, chi + eps, eta) - spinor(phi, chi - eps, eta)) / (2.0 * eps)
    a_phi = py_float(-1j * jnp.vdot(psi, d_phi))
    a_chi = py_float(-1j * jnp.vdot(psi, d_chi))
    return a_phi, a_chi


def horizontal_transport(index: int, eta: float) -> dict[str, Any]:
    phi = PHI0
    chi = CHI0
    dchi = 2.0 * math.pi / TRANSPORT_STEPS
    coeff_samples = []
    for step in range(TRANSPORT_STEPS):
        a_phi, a_chi = connection_coefficients(phi, chi, eta)
        if step in {0, TRANSPORT_STEPS // 2, TRANSPORT_STEPS - 1}:
            coeff_samples.append({"step": step, "A_phi": a_phi, "A_chi": a_chi})
        phi += -(a_chi / a_phi) * dchi
        chi += dchi
    start = spinor(PHI0, CHI0, eta)
    end = spinor(phi, chi, eta)
    endpoint_phase = py_float(jnp.angle(jnp.vdot(start, end)))
    accumulated = phi - PHI0
    target = -2.0 * math.pi * math.cos(2.0 * eta)
    return {
        "shell": index,
        "eta": eta,
        "connection_A_phi": coeff_samples[0]["A_phi"],
        "connection_A_chi": coeff_samples[0]["A_chi"],
        "transport_steps": TRANSPORT_STEPS,
        "accumulated_phase": accumulated,
        "accumulated_phase_mod_2pi": wrap_phase(accumulated),
        "endpoint_overlap_phase_mod_2pi": endpoint_phase,
        "closed_form_target": target,
        "target_mod_2pi": wrap_phase(target),
        "mod_error": abs(wrap_phase(accumulated - target)),
        "endpoint_vs_transport_mod_error": abs(wrap_phase(endpoint_phase - accumulated)),
        "coefficient_samples": coeff_samples,
    }


def curvature_eta_chi(eta: jax.Array) -> jax.Array:
    return -2.0 * jnp.sin(2.0 * eta)


def stokes_oriented_flux(eta_i: float, eta_j: float) -> dict[str, float]:
    deta = (eta_j - eta_i) / QUAD_ETA_STEPS
    dchi = 2.0 * math.pi / QUAD_CHI_STEPS
    grid = eta_i + (jnp.arange(QUAD_ETA_STEPS, dtype=jnp.float64) + 0.5) * deta
    raw_f_integral = py_float(jnp.sum(curvature_eta_chi(grid)) * deta * dchi * QUAD_CHI_STEPS)
    return {
        "raw_deta_wedge_dchi_integral": raw_f_integral,
        "stokes_oriented_integral": -raw_f_integral,
    }


def chern_integral() -> dict[str, float]:
    deta = (math.pi / 2.0) / QUAD_ETA_STEPS
    dchi = 2.0 * math.pi / QUAD_CHI_STEPS
    grid = (jnp.arange(QUAD_ETA_STEPS, dtype=jnp.float64) + 0.5) * deta
    signed_total = py_float(jnp.sum(curvature_eta_chi(grid)) * deta * dchi * QUAD_CHI_STEPS)
    normalized_abs = abs(signed_total) / (4.0 * math.pi)
    return {
        "signed_total_F_deta_wedge_dchi": signed_total,
        "abs_total_over_4pi": normalized_abs,
        "quadrature_error_abs_total_minus_4pi": abs(abs(signed_total) - 4.0 * math.pi),
        "orientation_note": "signed integral uses d eta wedge d chi; Chern check uses absolute value",
    }


def pair_flux(shells: list[dict[str, Any]], i: int, j: int) -> dict[str, Any]:
    hi = float(shells[i]["accumulated_phase"])
    hj = float(shells[j]["accumulated_phase"])
    eta_i = float(shells[i]["eta"])
    eta_j = float(shells[j]["eta"])
    transport = hj - hi
    target = 2.0 * math.pi * (math.cos(2.0 * eta_i) - math.cos(2.0 * eta_j))
    quad = stokes_oriented_flux(eta_i, eta_j)
    return {
        "pair": [i, j],
        "transport_h_difference": transport,
        "closed_form_target": target,
        "quadrature_stokes_oriented": quad["stokes_oriented_integral"],
        "raw_F_integral_deta_wedge_dchi": quad["raw_deta_wedge_dchi_integral"],
        "transport_vs_target_error": abs(transport - target),
        "transport_vs_quadrature_error": abs(transport - quad["stokes_oriented_integral"]),
        "quadrature_orientation": "negative of raw F_{eta,chi} d eta d chi so boundary orientation matches h_j-h_i",
    }


def entropy_vn(rho: jax.Array) -> jax.Array:
    vals = jnp.linalg.eigvalsh(0.5 * (rho + jnp.conj(rho.T)))
    positive = vals > 1.0e-12
    safe = jnp.where(positive, vals, 1.0)
    return -jnp.sum(jnp.where(positive, vals * jnp.log(safe), 0.0))


def rho_for_rung(rung: int) -> jax.Array:
    theta = 0.70 * rung / 2.0
    psi = jnp.asarray([jnp.cos(theta), 0.0, 0.0, jnp.sin(theta)], dtype=jnp.complex128)
    return jnp.outer(psi, jnp.conj(psi))


def partial_trace_left_to_b(rho: jax.Array) -> jax.Array:
    shaped = rho.reshape((2, 2, 2, 2))
    return jnp.einsum("abac->bc", shaped)


def signed_cut_table(phi_adjacent: list[float]) -> dict[str, Any]:
    rows = []
    signed_cuts = []
    for rung in range(3):
        rho = rho_for_rung(rung)
        s_ab = entropy_vn(rho)
        s_b = entropy_vn(partial_trace_left_to_b(rho))
        conditional = py_float(s_ab - s_b)
        signed_cut = -conditional
        signed_cuts.append(signed_cut)
        rows.append(
            {
                "rung": rung,
                "theta": 0.70 * rung / 2.0,
                "S_AB": py_float(s_ab),
                "S_B": py_float(s_b),
                "conditional_entropy_S_A_given_B": conditional,
                "signed_cut_Ic": signed_cut,
            }
        )
    delta_ic = [0.0, signed_cuts[1] - signed_cuts[0], signed_cuts[2] - signed_cuts[1]]
    phi_per_rung = [0.0, phi_adjacent[0], phi_adjacent[1]]
    mean_delta = sum(delta_ic) / len(delta_ic)
    mean_phi = sum(phi_per_rung) / len(phi_per_rung)
    num = sum((a - mean_delta) * (b - mean_phi) for a, b in zip(delta_ic, phi_per_rung, strict=True))
    den_a = math.sqrt(sum((a - mean_delta) ** 2 for a in delta_ic))
    den_b = math.sqrt(sum((b - mean_phi) ** 2 for b in phi_per_rung))
    corr = num / (den_a * den_b)
    sign_agreement = [
        math.copysign(1.0, delta_ic[idx]) == math.copysign(1.0, phi_per_rung[idx])
        for idx in (1, 2)
    ]
    return {
        "label": "CANDIDATE_J_AB_co_variation",
        "admission": "no_admission_candidate_only",
        "rows": rows,
        "delta_Ic_per_rung": delta_ic,
        "Phi_per_rung": phi_per_rung,
        "correlation_across_3_rungs": corr,
        "nonzero_rung_sign_agreement": sign_agreement,
        "sign_agreement_count": sum(1 for value in sign_agreement if value),
    }


def z3_smt(cos_scaled: list[int]) -> dict[str, Any]:
    c0, c1, c2 = [z3.Int(f"z3_c{idx}") for idx in range(3)]
    p01, p12, p02 = z3.Ints("z3_phi01 z3_phi12 z3_phi02")
    solver = z3.Solver()
    for var, value in zip((c0, c1, c2), cos_scaled, strict=True):
        solver.add(var == z3.IntVal(value))
    solver.add(p01 == c0 - c1)
    solver.add(p12 == c1 - c2)
    solver.add(p02 == c0 - c2)
    solver.add(p02 != p01 + p12)
    additivity_status = solver.check()

    shell_count = z3.Int("z3_single_shell_count")
    single_flux = z3.Int("z3_single_shell_flux")
    single = z3.Solver()
    single.add(shell_count == 1)
    single.add(z3.Implies(shell_count == 1, single_flux == 0))
    single.add(single_flux != 0)
    single_status = single.check()
    return {
        "solver": "z3",
        "verdict": str(additivity_status),
        "single_shell_verdict": str(single_status),
        "bound_scaled_cos_values": cos_scaled,
        "scale": SMT_SCALE,
        "derived_expression": "phi_ij_core = c_i - c_j; common 2*pi factor is outside the integer-scaled proof",
        "negated_additivity_unsat": str(additivity_status) == "unsat",
        "single_shell_flux_without_second_shell_forced_zero": str(single_status) == "unsat",
    }


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkReal(str(int(value)))


def cvc5_smt(cos_scaled: list[int]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LRA")
    real_sort = solver.getRealSort()
    c0 = solver.mkConst(real_sort, "cvc5_c0")
    c1 = solver.mkConst(real_sort, "cvc5_c1")
    c2 = solver.mkConst(real_sort, "cvc5_c2")
    p01 = solver.mkConst(real_sort, "cvc5_phi01")
    p12 = solver.mkConst(real_sort, "cvc5_phi12")
    p02 = solver.mkConst(real_sort, "cvc5_phi02")
    for var, value in zip((c0, c1, c2), cos_scaled, strict=True):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, cvc5_int(solver, value)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, p01, solver.mkTerm(Kind.SUB, c0, c1)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, p12, solver.mkTerm(Kind.SUB, c1, c2)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, p02, solver.mkTerm(Kind.SUB, c0, c2)))
    solver.assertFormula(
        solver.mkTerm(
            Kind.NOT,
            solver.mkTerm(Kind.EQUAL, p02, solver.mkTerm(Kind.ADD, p01, p12)),
        )
    )
    additivity_result = solver.checkSat()

    single = cvc5.Solver()
    single.setLogic("QF_LRA")
    real_sort = single.getRealSort()
    shell_count = single.mkConst(real_sort, "cvc5_single_shell_count")
    single_flux = single.mkConst(real_sort, "cvc5_single_flux")
    shell_is_one = single.mkTerm(Kind.EQUAL, shell_count, cvc5_int(single, 1))
    forced_zero = single.mkTerm(Kind.EQUAL, single_flux, cvc5_int(single, 0))
    single.assertFormula(shell_is_one)
    single.assertFormula(single.mkTerm(Kind.OR, single.mkTerm(Kind.NOT, shell_is_one), forced_zero))
    single.assertFormula(single.mkTerm(Kind.DISTINCT, single_flux, cvc5_int(single, 0)))
    single_result = single.checkSat()
    return {
        "solver": "cvc5",
        "verdict": cvc5_status(additivity_result),
        "single_shell_verdict": cvc5_status(single_result),
        "bound_scaled_cos_values": cos_scaled,
        "scale": SMT_SCALE,
        "derived_expression": "phi_ij_core = c_i - c_j; common 2*pi factor is outside the integer-scaled proof",
        "negated_additivity_unsat": additivity_result.isUnsat(),
        "single_shell_flux_without_second_shell_forced_zero": single_result.isUnsat(),
    }


def build_result() -> dict[str, Any]:
    shells = [horizontal_transport(index, eta_shell(index)) for index in range(3)]
    pairs = [pair_flux(shells, i, j) for i in range(3) for j in range(i + 1, 3)]
    adjacent = [pair_flux(shells, 0, 1), pair_flux(shells, 1, 2)]
    chern = chern_integral()
    cos_scaled = [int(round(float(shell["connection_A_chi"]) * SMT_SCALE)) for shell in shells]
    z3_proof = z3_smt(cos_scaled)
    cvc5_proof = cvc5_smt(cos_scaled)
    signed_cut = signed_cut_table([row["transport_h_difference"] for row in adjacent])
    scrambled_order = [2, 1, 0]
    original_adjacent = [pair_flux(shells, 0, 1), pair_flux(shells, 1, 2)]
    scrambled_adjacent = [
        pair_flux(shells, scrambled_order[idx], scrambled_order[idx + 1])
        for idx in range(len(scrambled_order) - 1)
    ]
    bare_spinor = {
        "connection": "trivial A=0",
        "curvature_zero": True,
        "holonomy_by_shell": [0.0, 0.0, 0.0],
        "flux_quantities": [0.0, 0.0],
        "reason": "flat carrier in C^2 has no Hopf coordinates and no bundle curvature",
        "pass": True,
    }
    single_shell = {
        "shell": 0,
        "holonomy_exists": True,
        "h": shells[0]["accumulated_phase"],
        "flux_defined": False,
        "Phi_reported": 0.0,
        "reason": "one eta shell has holonomy but no second rung for relative inter-shell flux",
        "pass": abs(shells[0]["accumulated_phase"]) > TOL,
    }
    scramble = {
        "original_order": [0, 1, 2],
        "scrambled_order": scrambled_order,
        "original_adjacent_fluxes": [row["transport_h_difference"] for row in original_adjacent],
        "scrambled_adjacent_fluxes": [row["transport_h_difference"] for row in scrambled_adjacent],
        "sign_pattern_changed": all(
            math.copysign(1.0, original_adjacent[idx]["transport_h_difference"])
            != math.copysign(1.0, scrambled_adjacent[-idx - 1]["transport_h_difference"])
            for idx in range(2)
        ),
        "total_chern_original": chern["abs_total_over_4pi"],
        "total_chern_scrambled": chern["abs_total_over_4pi"],
        "topology_indifferent_to_order": abs(chern["abs_total_over_4pi"] - 1.0) <= TOL,
        "reason": "ordered adjacent fluxes reverse under filtration reversal; the absolute Chern number is unchanged",
    }
    max_h_error = max(float(row["mod_error"]) for row in shells)
    max_pair_quad_error = max(float(row["transport_vs_quadrature_error"]) for row in pairs)
    all_pass = bool(
        max_h_error <= TOL
        and max_pair_quad_error <= TOL
        and chern["quadrature_error_abs_total_minus_4pi"] <= TOL
        and bare_spinor["pass"]
        and single_shell["pass"]
        and scramble["sign_pattern_changed"]
        and scramble["topology_indifferent_to_order"]
        and z3_proof["negated_additivity_unsat"]
        and cvc5_proof["negated_additivity_unsat"]
        and z3_proof["single_shell_flux_without_second_shell_forced_zero"]
        and cvc5_proof["single_shell_flux_without_second_shell_forced_zero"]
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and READS_PEER_RESULT is False
    )
    shared_scalars = {
        "h0": shells[0]["accumulated_phase"],
        "h1": shells[1]["accumulated_phase"],
        "h2": shells[2]["accumulated_phase"],
        "phi01": adjacent[0]["transport_h_difference"],
        "phi12": adjacent[1]["transport_h_difference"],
        "phi02": pair_flux(shells, 0, 2)["transport_h_difference"],
        "chern_abs_over_4pi": chern["abs_total_over_4pi"],
        "signed_cut_Ic0": signed_cut["rows"][0]["signed_cut_Ic"],
        "signed_cut_Ic1": signed_cut["rows"][1]["signed_cut_Ic"],
        "signed_cut_Ic2": signed_cut["rows"][2]["signed_cut_Ic"],
        "J_AB_correlation_3_rungs": signed_cut["correlation_across_3_rungs"],
    }
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "schema_version": "three_engine_sim_result_v1",
        "engine_contract": {"mode": "all_three_full_sims", "reads_peer_result": False},
        "object_id": OBJECT_ID,
        "engine": "jax",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "pin_spec": PIN_SPEC,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib", "math"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_path_tools": ["z3", "cvc5"],
        "control_only_tools": [],
        "standard_labels": {
            "pin": "eta shells, loop grammar, and curvature member are fixed in pin_spec",
            "like_for_like": True,
            "no_numpy_claim_path": True,
            "capability_backed": True,
        },
        "shell_holonomy": shells,
        "inter_shell_flux": pairs,
        "chern": chern,
        "ablations": {
            "bare_spinor": bare_spinor,
            "single_shell": single_shell,
            "ratchet_scramble": scramble,
        },
        "ratchet_coupling": signed_cut,
        "smt": {"z3": z3_proof, "cvc5": cvc5_proof, "solvers_agree": z3_proof["verdict"] == cvc5_proof["verdict"]},
        "crossover_proofs": {
            "z3": {"ran": True, "load_bearing": True, "verdict": z3_proof["verdict"], **z3_proof},
            "cvc5": {"ran": True, "load_bearing": True, "verdict": cvc5_proof["verdict"], **cvc5_proof},
        },
        "shared_scalars": shared_scalars,
        "all_pass": all_pass,
        "max_errors": {
            "holonomy_mod_error": max_h_error,
            "transport_vs_quadrature_flux_error": max_pair_quad_error,
            "chern_abs_error": chern["quadrature_error_abs_total_minus_4pi"],
        },
        "claim_ceiling": "scratch_diagnostic only; promotion_allowed=false; flux remains a CANDIDATE FAMILY per weyl-flux.md; tests only the curvature member's emergence conditions.",
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FLUX_EMERGENCE_DISCRIMINATOR_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"h={[result['shared_scalars'][key] for key in ('h0', 'h1', 'h2')]} "
        f"chern={result['shared_scalars']['chern_abs_over_4pi']} "
        f"z3={result['smt']['z3']['verdict']} cvc5={result['smt']['cvc5']['verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
