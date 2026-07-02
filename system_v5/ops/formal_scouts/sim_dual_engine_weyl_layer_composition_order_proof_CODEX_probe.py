#!/usr/bin/env python3
from jax import config as jax_config

jax_config.update("jax_enable_x64", True)

import cmath
import json
import math
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax.numpy as jnp
import torch
import z3


CLASSIFICATION = "diagnostic_only"
PROMOTION_ALLOWED = False
SIM_ID = "dual_engine_weyl_layer_composition_order_proof_CODEX_probe"
RESULT_PATH = Path("results/dual_engine_weyl_layer_composition_order_proof_CODEX_probe_results.json")
EPS = 1.0e-9
TORCH_DTYPE = torch.complex128
OPERATOR_ORDER = ["U1a", "U1b", "Rsu2", "AD", "DEPH"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex128 CPTP composition pipeline for the requested 2-qubit carrier",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent x64 complex CPTP composition pipeline for cross-engine comparison",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing real-arithmetic contradiction: measured gaps plus all-gaps-commute bound is UNSAT while zero-erased gaps are SAT",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT cross-check of the same real-vs-zero order-gap contradiction",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def torch_kron(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return torch.kron(a, b)


def jax_kron(a: jnp.ndarray, b: jnp.ndarray) -> jnp.ndarray:
    return jnp.kron(a, b)


def one_qubit_torch(op: torch.Tensor) -> torch.Tensor:
    ident = torch.eye(2, dtype=TORCH_DTYPE)
    return torch_kron(op, ident)


def one_qubit_jax(op: jnp.ndarray) -> jnp.ndarray:
    ident = jnp.eye(2, dtype=jnp.complex128)
    return jax_kron(op, ident)


def bell_left_weyl_density_torch() -> tuple[torch.Tensor, dict[str, Any]]:
    ident = torch.eye(2, dtype=TORCH_DTYPE)
    gamma5_left_sector = torch.eye(2, dtype=TORCH_DTYPE)
    p_left = (ident + gamma5_left_sector) / 2
    psi = torch.zeros(4, dtype=TORCH_DTYPE)
    psi[0] = 1 / math.sqrt(2)
    psi[3] = 1 / math.sqrt(2)
    rho = torch.outer(psi, psi.conj())
    projector = one_qubit_torch(p_left)
    projected = projector @ rho @ projector.conj().T
    projected = projected / torch.trace(projected)
    return projected, {
        "gamma5_convention": "two-component left-Weyl sector after P_L projection; gamma5 restricts to +I on qubit0, so P_L=(I+gamma5)/2 is identity on the active left-Weyl spinor sector",
        "projection_idempotent": bool(torch.allclose(p_left @ p_left, p_left, atol=1.0e-12, rtol=0.0)),
        "projection_trace_distance_from_entangled_carrier": trace_distance_torch(rho, projected),
        "qubit0_entropy_nats": reduced_entropy_qubit0_torch(projected),
    }


def bell_left_weyl_density_jax() -> tuple[jnp.ndarray, dict[str, Any]]:
    ident = jnp.eye(2, dtype=jnp.complex128)
    gamma5_left_sector = jnp.eye(2, dtype=jnp.complex128)
    p_left = (ident + gamma5_left_sector) / 2
    psi = jnp.zeros((4,), dtype=jnp.complex128)
    psi = psi.at[0].set(1 / math.sqrt(2))
    psi = psi.at[3].set(1 / math.sqrt(2))
    rho = jnp.outer(psi, jnp.conj(psi))
    projector = one_qubit_jax(p_left)
    projected = projector @ rho @ jnp.conj(projector.T)
    projected = projected / jnp.trace(projected)
    return projected, {
        "projection_idempotent": bool(jnp.allclose(p_left @ p_left, p_left, atol=1.0e-12, rtol=0.0)),
        "projection_trace_distance_from_entangled_carrier": trace_distance_jax(rho, projected),
        "qubit0_entropy_nats": reduced_entropy_qubit0_jax(projected),
    }


def reduced_qubit0_torch(rho: torch.Tensor) -> torch.Tensor:
    reshaped = rho.reshape(2, 2, 2, 2)
    return torch.einsum("abcb->ac", reshaped)


def reduced_qubit0_jax(rho: jnp.ndarray) -> jnp.ndarray:
    reshaped = rho.reshape(2, 2, 2, 2)
    return jnp.einsum("abcb->ac", reshaped)


def reduced_entropy_qubit0_torch(rho: torch.Tensor) -> float:
    red = reduced_qubit0_torch(rho)
    eigs = torch.clamp(torch.real(torch.linalg.eigvalsh((red + red.conj().T) / 2)), min=1.0e-15)
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def reduced_entropy_qubit0_jax(rho: jnp.ndarray) -> float:
    red = reduced_qubit0_jax(rho)
    eigs = jnp.maximum(jnp.real(jnp.linalg.eigvalsh((red + jnp.conj(red.T)) / 2)), 1.0e-15)
    return float(-jnp.sum(eigs * jnp.log(eigs)))


def trace_distance_torch(a: torch.Tensor, b: torch.Tensor) -> float:
    diff = (a - b + (a - b).conj().T) / 2
    eigs = torch.linalg.eigvalsh(diff)
    return float((0.5 * torch.sum(torch.abs(eigs))).item())


def trace_distance_jax(a: jnp.ndarray, b: jnp.ndarray) -> float:
    diff = (a - b + jnp.conj((a - b).T)) / 2
    eigs = jnp.linalg.eigvalsh(diff)
    return float(0.5 * jnp.sum(jnp.abs(eigs)))


def density_checks_torch(rho: torch.Tensor) -> dict[str, Any]:
    herm = (rho + rho.conj().T) / 2
    trace = torch.trace(rho)
    eigs = torch.linalg.eigvalsh(herm)
    return {
        "trace_real": float(torch.real(trace).item()),
        "trace_imag_abs": abs(float(torch.imag(trace).item())),
        "min_eigenvalue": float(torch.min(torch.real(eigs)).item()),
        "hermitian_max_abs_delta": float(torch.max(torch.abs(rho - rho.conj().T)).item()),
        "valid": bool(
            abs(float(torch.real(trace).item()) - 1.0) <= 1.0e-10
            and abs(float(torch.imag(trace).item())) <= 1.0e-10
            and float(torch.min(torch.real(eigs)).item()) >= -1.0e-10
            and float(torch.max(torch.abs(rho - rho.conj().T)).item()) <= 1.0e-10
        ),
    }


def torch_ops() -> dict[str, list[torch.Tensor]]:
    ident = torch.eye(2, dtype=TORCH_DTYPE)
    x = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=TORCH_DTYPE)
    z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=TORCH_DTYPE)
    u1a = torch.diag(torch.tensor([1.0 + 0.0j, cmath.exp(1j * 0.7)], dtype=TORCH_DTYPE))
    u1b = torch.diag(torch.tensor([1.0 + 0.0j, cmath.exp(1j * 1.3)], dtype=TORCH_DTYPE))
    rsu2 = math.cos(0.9 / 2) * ident + 1j * math.sin(0.9 / 2) * x
    ad_k0 = torch.diag(torch.tensor([1.0 + 0.0j, math.sqrt(0.6) + 0.0j], dtype=TORCH_DTYPE))
    ad_k1 = torch.tensor([[0.0, math.sqrt(0.4)], [0.0, 0.0]], dtype=TORCH_DTYPE)
    deph_k0 = math.sqrt(0.7) * ident
    deph_k1 = math.sqrt(0.3) * z
    return {
        "U1a": [u1a],
        "U1b": [u1b],
        "Rsu2": [rsu2],
        "AD": [ad_k0, ad_k1],
        "DEPH": [deph_k0, deph_k1],
    }


def jax_ops() -> dict[str, list[jnp.ndarray]]:
    ident = jnp.eye(2, dtype=jnp.complex128)
    x = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
    z = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
    u1a = jnp.diag(jnp.array([1.0 + 0.0j, jnp.exp(1j * 0.7)], dtype=jnp.complex128))
    u1b = jnp.diag(jnp.array([1.0 + 0.0j, jnp.exp(1j * 1.3)], dtype=jnp.complex128))
    rsu2 = math.cos(0.9 / 2) * ident + 1j * math.sin(0.9 / 2) * x
    ad_k0 = jnp.diag(jnp.array([1.0 + 0.0j, math.sqrt(0.6) + 0.0j], dtype=jnp.complex128))
    ad_k1 = jnp.array([[0.0, math.sqrt(0.4)], [0.0, 0.0]], dtype=jnp.complex128)
    deph_k0 = math.sqrt(0.7) * ident
    deph_k1 = math.sqrt(0.3) * z
    return {
        "U1a": [u1a],
        "U1b": [u1b],
        "Rsu2": [rsu2],
        "AD": [ad_k0, ad_k1],
        "DEPH": [deph_k0, deph_k1],
    }


def apply_torch(rho: torch.Tensor, kraus_ops: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros_like(rho)
    for k in kraus_ops:
        full = one_qubit_torch(k)
        out = out + full @ rho @ full.conj().T
    return (out + out.conj().T) / 2


def apply_jax(rho: jnp.ndarray, kraus_ops: list[jnp.ndarray]) -> jnp.ndarray:
    out = jnp.zeros_like(rho)
    for k in kraus_ops:
        full = one_qubit_jax(k)
        out = out + full @ rho @ jnp.conj(full.T)
    return (out + jnp.conj(out.T)) / 2


def jax_to_torch(rho: jnp.ndarray) -> torch.Tensor:
    return torch.tensor(rho.tolist(), dtype=TORCH_DTYPE)


def decimal_str(value: float) -> str:
    if abs(value) < 5.0e-18:
        return "0"
    text = format(value, ".18f").rstrip("0").rstrip(".")
    return text if text else "0"


def z3_order_proof(gaps: list[float]) -> dict[str, Any]:
    eps = z3.RealVal(decimal_str(EPS))

    def check(values: list[float]) -> str:
        solver = z3.Solver()
        for idx, value in enumerate(values):
            gap = z3.Real(f"gap_{idx}")
            solver.add(gap == z3.RealVal(decimal_str(value)))
            solver.add(gap <= eps)
        return str(solver.check())

    real_status = check(gaps)
    zero_erased_status = check([0.0 for _ in gaps])
    return {
        "engine": "z3",
        "assertion": "for every measured gap g_i: g_i == measured_value_i and g_i <= eps",
        "eps": EPS,
        "real_data_status": real_status,
        "zero_erased_status": zero_erased_status,
        "load_bearing": real_status == "unsat" and zero_erased_status == "sat",
    }


def cvc5_order_proof(gaps: list[float]) -> dict[str, Any]:
    def check(values: list[float]) -> str:
        solver = cvc5.Solver()
        solver.setLogic("QF_LRA")
        real_sort = solver.getRealSort()
        eps = solver.mkReal(decimal_str(EPS))
        for idx, value in enumerate(values):
            gap = solver.mkConst(real_sort, f"gap_{idx}")
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, gap, solver.mkReal(decimal_str(value))))
            solver.assertFormula(solver.mkTerm(Kind.LEQ, gap, eps))
        return str(solver.checkSat())

    real_status = check(gaps)
    zero_erased_status = check([0.0 for _ in gaps])
    return {
        "engine": "cvc5",
        "assertion": "for every measured gap g_i: g_i == measured_value_i and g_i <= eps",
        "eps": EPS,
        "real_data_status": real_status,
        "zero_erased_status": zero_erased_status,
        "load_bearing": real_status == "unsat" and zero_erased_status == "sat",
    }


def compute_table() -> dict[str, Any]:
    rho_t, left_projection_t = bell_left_weyl_density_torch()
    rho_j, left_projection_j = bell_left_weyl_density_jax()
    ops_t = torch_ops()
    ops_j = jax_ops()
    rows = []
    max_rho_trace_delta = 0.0
    max_rho_element_delta = 0.0
    max_gap_delta = 0.0
    all_density_checks = []

    for first, second in combinations(OPERATOR_ORDER, 2):
        rho_t_first_after_second = apply_torch(apply_torch(rho_t, ops_t[second]), ops_t[first])
        rho_t_second_after_first = apply_torch(apply_torch(rho_t, ops_t[first]), ops_t[second])
        rho_j_first_after_second = apply_jax(apply_jax(rho_j, ops_j[second]), ops_j[first])
        rho_j_second_after_first = apply_jax(apply_jax(rho_j, ops_j[first]), ops_j[second])

        torch_gap = trace_distance_torch(rho_t_first_after_second, rho_t_second_after_first)
        jax_gap = trace_distance_jax(rho_j_first_after_second, rho_j_second_after_first)
        commute_torch = bool(torch_gap < EPS)
        commute_jax = bool(jax_gap < EPS)

        jax_first_as_torch = jax_to_torch(rho_j_first_after_second)
        jax_second_as_torch = jax_to_torch(rho_j_second_after_first)
        delta_first = trace_distance_torch(rho_t_first_after_second, jax_first_as_torch)
        delta_second = trace_distance_torch(rho_t_second_after_first, jax_second_as_torch)
        elem_first = float(torch.max(torch.abs(rho_t_first_after_second - jax_first_as_torch)).item())
        elem_second = float(torch.max(torch.abs(rho_t_second_after_first - jax_second_as_torch)).item())
        max_rho_trace_delta = max(max_rho_trace_delta, delta_first, delta_second)
        max_rho_element_delta = max(max_rho_element_delta, elem_first, elem_second)
        max_gap_delta = max(max_gap_delta, abs(torch_gap - jax_gap))

        checks = [
            density_checks_torch(rho_t_first_after_second),
            density_checks_torch(rho_t_second_after_first),
            density_checks_torch(jax_first_as_torch),
            density_checks_torch(jax_second_as_torch),
        ]
        all_density_checks.extend(checks)

        rows.append(
            {
                "pair": [first, second],
                "orders_compared": [f"{first}_after_{second}", f"{second}_after_{first}"],
                "torch_order_gap": torch_gap,
                "jax_order_gap": jax_gap,
                "gap_abs_delta": abs(torch_gap - jax_gap),
                "commute_torch": commute_torch,
                "commute_jax": commute_jax,
                "classification": "commute" if commute_torch else "not_commute",
                "torch_jax_rho_trace_delta": max(delta_first, delta_second),
                "torch_jax_rho_element_delta": max(elem_first, elem_second),
            }
        )

    noncommuting_pairs = [row["pair"] for row in rows if not row["commute_torch"]]
    commuting_pairs = [row["pair"] for row in rows if row["commute_torch"]]
    same_table = all(row["commute_torch"] == row["commute_jax"] for row in rows)
    sole_source = bool(noncommuting_pairs) and all("Rsu2" in pair for pair in noncommuting_pairs)

    return {
        "rho_torch": rho_t,
        "rows": rows,
        "commuting_pairs": commuting_pairs,
        "noncommuting_pairs": noncommuting_pairs,
        "same_table": same_table,
        "sole_source_of_noncommutation": sole_source,
        "max_rho_delta": max_rho_trace_delta,
        "max_rho_trace_delta": max_rho_trace_delta,
        "max_rho_element_delta": max_rho_element_delta,
        "max_gap_delta": max_gap_delta,
        "left_weyl_projection": {
            "torch": left_projection_t,
            "jax": left_projection_j,
        },
        "density_checks_all_valid": all(row["valid"] for row in all_density_checks),
        "density_checks_worst": {
            "max_trace_real_error": max(abs(row["trace_real"] - 1.0) for row in all_density_checks),
            "max_trace_imag_abs": max(row["trace_imag_abs"] for row in all_density_checks),
            "min_eigenvalue": min(row["min_eigenvalue"] for row in all_density_checks),
            "max_hermitian_delta": max(row["hermitian_max_abs_delta"] for row in all_density_checks),
        },
    }


def build_result() -> dict[str, Any]:
    computed = compute_table()
    gaps = [row["torch_order_gap"] for row in computed["rows"]]
    z3_proof = z3_order_proof(gaps)
    cvc5_proof = cvc5_order_proof(gaps)
    proof_load_bearing = bool(z3_proof["load_bearing"] and cvc5_proof["load_bearing"])
    result = {
        "sim_id": SIM_ID,
        "name": "Dual-engine Weyl layer composition order proof CODEX probe",
        "version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "tier": "bounded layer-composition order diagnostic",
        "purpose": "Independently compute a 2-qubit left-Weyl spinor layer-composition order table in torch and JAX, then prove that all-gaps-commute is inconsistent for the real data.",
        "scientific_question": "Which requested one-qubit CPTP maps commute on an entangled 2-qubit left-Weyl spinor carrier, and does the independent JAX table match torch?",
        "sim_execution_kind": "nonclassical",
        "sim_class": "dual_engine_order_test",
        "root_constraints_in_force": [
            "F01 finite 2-qubit carrier, five finite CPTP operator maps, and ten unordered operator pairs",
            "N01 order-sensitive composition readout by trace distance between Phi_X(Phi_Y(rho)) and Phi_Y(Phi_X(rho))",
        ],
        "finite_map": "for each unordered pair {X,Y}: (X,Y,rho_left_weyl_entangled) -> trace_distance(Phi_X(Phi_Y(rho)), Phi_Y(Phi_X(rho))) and commute/not_commute at eps=1e-9",
        "domain": {
            "carrier": "2-qubit density matrix; qubit0 is the two-component left-Weyl spinor sector, qubit1 is entangled by a Bell carrier",
            "operators_on_qubit0": {
                "U1a": "diag(1, exp(i*0.7))",
                "U1b": "diag(1, exp(i*1.3))",
                "Rsu2": "exp(i*0.9*X/2)",
                "AD": "amplitude damping gamma=0.4 with K0=diag(1,sqrt(0.6)), K1=sqrt(0.4)|0><1|",
                "DEPH": "dephasing p=0.3 with sqrt(0.7)I and sqrt(0.3)Z",
            },
        },
        "codomain_or_output": "ten-pair order-gap table, torch/JAX rho deltas, same_table verdict, and z3/cvc5 real-vs-zero proof verdicts",
        "carrier_layer": "left-Weyl two-component spinor sector on qubit0 with entangled qubit1 witness",
        "geometry_layer": "local Weyl/order-composition diagnostic only",
        "carrier_realization": "torch complex128 density matrix and independent JAX complex128 density matrix",
        "peps3d_embedding": "not_admitted; this diagnostic does not claim PEPS3D layer completion or carrier promotion",
        "spinor_state": "qubit0 left-Weyl two-component spinor sector in a Bell density with qubit1",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [],
        "downstream_blocks": ["flux", "Xi", "Phi0", "Axis0", "bridge", "basin", "physics", "layer_completion"],
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "requested CPTP map composition order sensitivity on qubit0",
        "branch_status_before_run": "diagnostic independent cross-model comparison requested",
        "allowed_claims": [
            "local order table for the requested five maps on the requested 2-qubit carrier",
            "torch/JAX classification agreement for this finite diagnostic",
            "z3/cvc5 contradiction for the claim that all measured gaps are <= eps",
        ],
        "promotion_blockers": [
            "diagnostic_only by request",
            "no PEPS3D embedding admission",
            "single carrier state only",
            "no downstream layer, flux, Axis0, bridge, basin, physics, or completion claim",
        ],
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3_real_gap_all_commute_unsat", "cvc5_real_gap_all_commute_unsat"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_inputs": ["operator constants from user request"],
        "data_or_artifact_dependencies": [],
        "required_negatives": ["zero-erased all-gaps control"],
        "negatives_run": ["all measured gaps erased to 0 in z3 and cvc5"],
        "kill_conditions": [
            "torch and JAX commute classifications differ",
            "z3 or cvc5 real-data all-commute assertion is SAT",
            "z3 or cvc5 zero-erased all-commute control is UNSAT",
            "any composed density fails trace/Hermitian/PSD checks",
        ],
        "required_artifacts": [str(RESULT_PATH)],
        "artifacts_emitted": [str(RESULT_PATH)],
        "witness_trace_id": f"{SIM_ID}:torch_jax_z3_cvc5",
        "eps": EPS,
        "operator_order": OPERATOR_ORDER,
        "commutation_table": computed["rows"],
        "commuting_pairs": computed["commuting_pairs"],
        "noncommuting_pairs": computed["noncommuting_pairs"],
        "same_table": computed["same_table"],
        "sole_source_of_noncommutation": computed["sole_source_of_noncommutation"],
        "Rsu2_is_sole_source_of_noncommutation": computed["sole_source_of_noncommutation"],
        "max_rho_delta": computed["max_rho_delta"],
        "max_rho_trace_delta": computed["max_rho_trace_delta"],
        "max_rho_element_delta": computed["max_rho_element_delta"],
        "max_gap_delta": computed["max_gap_delta"],
        "density_checks_all_valid": computed["density_checks_all_valid"],
        "density_checks_worst": computed["density_checks_worst"],
        "left_weyl_projection": computed["left_weyl_projection"],
        "proof": {
            "z3": z3_proof,
            "cvc5": cvc5_proof,
            "load_bearing": proof_load_bearing,
            "real_data_expected": "UNSAT because at least one measured order gap exceeds eps",
            "zero_erased_expected": "SAT because all asserted gaps are 0 and <= eps",
        },
        "pass_rule": "Pass iff torch and JAX classify all ten pairs identically, composed densities remain valid, z3/cvc5 real data are UNSAT, z3/cvc5 zero-erased controls are SAT, and promotion remains blocked.",
        "fail_rule": "Fail on engine classification mismatch, invalid density, proof verdict mismatch, missing result artifact, or promotion_allowed=true.",
        "promotion_status": "diagnostic_only",
        "eligible_consumers": ["cross_model_comparison_diagnostic_only"],
        "blocked_consumers": ["canonical_layer_admission", "PEPS3D_admission", "flux", "Xi", "Phi0", "Axis0", "bridge", "basin", "physics"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "independence_note": "This CODEX probe computes from the user-specified math and does not read any external/opus probe or result file.",
    }
    result["result_summary"] = {
        "pair_count": len(result["commutation_table"]),
        "commuting_pair_count": len(result["commuting_pairs"]),
        "noncommuting_pair_count": len(result["noncommuting_pairs"]),
        "same_table": result["same_table"],
        "max_rho_delta": result["max_rho_delta"],
        "proof_load_bearing": proof_load_bearing,
        "sole_source_of_noncommutation": result["sole_source_of_noncommutation"],
        "promotion_allowed": result["promotion_allowed"],
        "classification": result["classification"],
    }
    result["pass"] = bool(
        result["same_table"]
        and result["density_checks_all_valid"]
        and proof_load_bearing
        and not result["promotion_allowed"]
        and result["classification"] == "diagnostic_only"
    )
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result["result_summary"], indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
