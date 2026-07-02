#!/usr/bin/env python3
"""Stage-5 unitary operator/channel/generator probe.

Finite map:
    U_d: C^d -> C^d for d in {8, 16, 32, 64}
    Phi_U(rho) = U_d rho U_d^*

This probe proves one bounded operator-channel claim: a QR-generated finite
operator has a unitarity residual below the declared bound, while a recomputed
non-isometric control fails the same SMT-bound claim. The proof tools are
load-bearing only through the verdict flip. Numeric rows use genuine
remove-and-recompute controls.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import time
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import torch

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
ARTIFACT_DIR = RESULT_DIR / "stage5_unitary_operator_artifacts"
OBJECT_ID = "stage5_unitary_operator_channel_generator"
OUT_PATH = RESULT_DIR / f"{OBJECT_ID}_results.json"

SEED = 0
SCALES = (8, 16, 32, 64)
DTYPE = torch.complex128
REAL_DTYPE = torch.float64
UNITARITY_EPS = 1.0e-8
SCALED_CONTROL_FACTOR = 0.999
ENTRY_CONTROL_EPS = 1.0e-8
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity", "bridge", "physics"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY numeric carrier: generates QR finite unitary operators, recomputes controls, and emits scale-ladder invariants without NumPy.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "Independent x64 mirror of the emitted finite operators and controls; recomputes unitarity residuals from Python scalar data.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via load_bearing_proof.smt_load_bearing; verdict flips for residual<=eps on real operator versus scaled non-isometric control.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check inside smt_load_bearing over the same measured residual-bound claim; required to flip with z3.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "PROOF mirror using exact rationalized measured residuals; records the same real/control verdict flip without numeric ablation.",
    },
    "clifford": {
        "tried": True,
        "used": False,
        "reason": "Installed but deliberately dropped: this arbitrary QR unitary is not a Clifford rotor/geometric-product claim, so no genuine Clifford ablation row is emitted.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported; tensor-to-NumPy bridges are excluded from claim-bearing computation.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Not imported; QR generation is torch-native rather than scipy.stats.unitary_group.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "None",
    "numpy": "None",
    "scipy": "None",
}


def complex_normal_matrix(n: int) -> torch.Tensor:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(SEED)
    real = torch.randn((n, n), generator=generator, dtype=REAL_DTYPE)
    imag = torch.randn((n, n), generator=generator, dtype=REAL_DTYPE)
    return torch.complex(real, imag)


def unitary_from_qr(n: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Return phase-corrected QR unitary and the raw finite generator matrix."""
    g = complex_normal_matrix(n)
    q, r = torch.linalg.qr(g)
    diag = torch.diagonal(r)
    phase = diag / torch.clamp(torch.abs(diag), min=1.0e-300)
    u = q * phase.unsqueeze(0)
    return u.to(DTYPE), g.to(DTYPE)


def scaled_control(u: torch.Tensor) -> torch.Tensor:
    return torch.as_tensor(SCALED_CONTROL_FACTOR, dtype=REAL_DTYPE) * u


def additive_entry_control(u: torch.Tensor) -> torch.Tensor:
    control = u.clone()
    control[0, 0] = control[0, 0] + torch.as_tensor(ENTRY_CONTROL_EPS, dtype=REAL_DTYPE)
    return control


def row_erased_control(u: torch.Tensor) -> torch.Tensor:
    control = u.clone()
    control[0, :] = torch.zeros_like(control[0, :])
    return control


def identity(n: int) -> torch.Tensor:
    return torch.eye(n, dtype=DTYPE)


def gram(operator: torch.Tensor) -> torch.Tensor:
    return operator @ operator.conj().transpose(-2, -1)


def unitarity_residual_torch(operator: torch.Tensor) -> float:
    defect = gram(operator) - identity(operator.shape[0])
    return float(torch.max(torch.abs(defect)).item())


def frobenius_defect_torch(operator: torch.Tensor) -> float:
    defect = gram(operator) - identity(operator.shape[0])
    return float(torch.linalg.matrix_norm(defect, ord="fro").item())


def order_gap_torch(operator: torch.Tensor) -> float:
    n = operator.shape[0]
    signs = torch.tensor([1.0 if i % 2 == 0 else -1.0 for i in range(n)], dtype=REAL_DTYPE)
    probe = torch.diag(torch.complex(signs, torch.zeros_like(signs)))
    gap = operator @ probe - probe @ operator
    return float(torch.linalg.matrix_norm(gap, ord="fro").item())


def trace_preservation_error_torch(operator: torch.Tensor) -> float:
    n = operator.shape[0]
    errors = []
    for i in range(n):
        basis = torch.zeros((n, n), dtype=DTYPE)
        basis[i, i] = 1.0 + 0.0j
        image = operator @ basis @ operator.conj().transpose(-2, -1)
        errors.append(torch.abs(torch.trace(image) - torch.trace(basis)))
    return float(torch.max(torch.stack(errors)).item())


def unitary_score(residual: float) -> float:
    return max(0.0, 1.0 - float(residual))


def jax_array_from_torch(operator: torch.Tensor) -> jax.Array:
    return jnp.array(operator.detach().cpu().tolist(), dtype=jnp.complex128)


def unitarity_residual_jax(operator: jax.Array) -> float:
    n = operator.shape[0]
    defect = operator @ jnp.conjugate(jnp.swapaxes(operator, -1, -2)) - jnp.eye(n, dtype=jnp.complex128)
    return float(jnp.max(jnp.abs(defect)).item())


def frobenius_defect_jax(operator: jax.Array) -> float:
    n = operator.shape[0]
    defect = operator @ jnp.conjugate(jnp.swapaxes(operator, -1, -2)) - jnp.eye(n, dtype=jnp.complex128)
    return float(jnp.linalg.norm(defect, ord="fro").item())


def order_gap_jax(operator: jax.Array) -> float:
    n = operator.shape[0]
    signs = jnp.array([1.0 if i % 2 == 0 else -1.0 for i in range(n)], dtype=jnp.float64)
    probe = jnp.diag(signs.astype(jnp.complex128))
    gap = operator @ probe - probe @ operator
    return float(jnp.linalg.norm(gap, ord="fro").item())


def artifact_checksum(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_operator_artifact(n: int, operator: torch.Tensor) -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    path = ARTIFACT_DIR / f"{OBJECT_ID}_d{n}.pt"
    torch.save({"operator": operator.detach().cpu(), "dimension": n, "seed": SEED}, path)
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": artifact_checksum(path),
        "format": "torch.save complex128 operator tensor",
    }


def sympy_verdict_from_measured(real_residual: float, control_residual: float) -> dict[str, Any]:
    real_r = sp.Rational(str(real_residual))
    control_r = sp.Rational(str(control_residual))
    eps_r = sp.Rational(str(UNITARITY_EPS))
    real_verdict = "sat" if real_r <= eps_r else "unsat"
    control_verdict = "sat" if control_r <= eps_r else "unsat"
    return {
        "claim": "sympy_rationalized_unitarity_residual_le_eps_real_vs_scaled_control",
        "engine": "sympy",
        "real_claim_verdict": real_verdict,
        "negated_claim_verdict": control_verdict,
        "differ": real_verdict != control_verdict,
        "load_bearing": real_verdict != control_verdict,
        "bound_to_measured": True,
        "real_measured": {
            "max_unitarity_residual": float(real_r),
            "eps": float(eps_r),
        },
        "control_measured": {
            "max_unitarity_residual": float(control_r),
            "eps": float(eps_r),
        },
        "exact_rationalized": {
            "real_residual": str(real_r),
            "control_residual": str(control_r),
            "eps": str(eps_r),
        },
    }


def smt_unitarity_proof(real_residual: float, control_residual: float) -> dict[str, Any]:
    return smt_load_bearing(
        claim="unitary_operator_residual_bound_real_vs_scaled_non_isometric_control",
        real_measured={"max_unitarity_residual": real_residual, "eps": UNITARITY_EPS},
        control_measured={"max_unitarity_residual": control_residual, "eps": UNITARITY_EPS},
        claim_builder=lambda v: v["max_unitarity_residual"] <= v["eps"],
        cvc5_claim_pairs=[("max_unitarity_residual", "<=", "eps")],
    )


def scale_rung(n: int) -> dict[str, Any]:
    u, raw_g = unitary_from_qr(n)
    scaled = scaled_control(u)
    additive = additive_entry_control(u)
    row_erased = row_erased_control(u)

    torch_residual = unitarity_residual_torch(u)
    torch_scaled_residual = unitarity_residual_torch(scaled)
    torch_additive_residual = unitarity_residual_torch(additive)
    torch_raw_residual = unitarity_residual_torch(raw_g)
    torch_row_erased_residual = unitarity_residual_torch(row_erased)
    torch_fro_defect = frobenius_defect_torch(u)
    torch_order_gap = order_gap_torch(u)
    torch_trace_error = trace_preservation_error_torch(u)

    ju = jax_array_from_torch(u)
    jscaled = jax_array_from_torch(scaled)
    jadditive = jax_array_from_torch(additive)
    jrow_erased = jax_array_from_torch(row_erased)
    jax_residual = unitarity_residual_jax(ju)
    jax_scaled_residual = unitarity_residual_jax(jscaled)
    jax_additive_residual = unitarity_residual_jax(jadditive)
    jax_row_erased_residual = unitarity_residual_jax(jrow_erased)
    jax_fro_defect = frobenius_defect_jax(ju)
    jax_order_gap = order_gap_jax(ju)

    gram_matrix = gram(u)
    diagonal = torch.real(torch.diagonal(gram_matrix))
    offdiag = gram_matrix - torch.diag(torch.diagonal(gram_matrix))
    trace_value = torch.real(torch.trace(gram_matrix))
    artifact = write_operator_artifact(n, u)

    pass_rung = (
        torch_residual <= UNITARITY_EPS
        and jax_residual <= UNITARITY_EPS
        and torch_scaled_residual > UNITARITY_EPS
        and jax_scaled_residual > UNITARITY_EPS
        and torch_raw_residual > UNITARITY_EPS
        and torch_row_erased_residual > UNITARITY_EPS
        and abs(torch_residual - jax_residual) <= 1.0e-12
        and abs(torch_scaled_residual - jax_scaled_residual) <= 1.0e-12
        and torch_order_gap > 1.0e-9
        and jax_order_gap > 1.0e-9
        and torch_trace_error <= UNITARITY_EPS
    )

    return {
        "sites_or_qubits": n,
        "operator_dimension": n,
        "operator_entry_count": n * n,
        "operator_count": 1,
        "path_count": n,
        "probe_count": n,
        "dense_state_closure_used": False,
        "torch_unitarity_residual": torch_residual,
        "torch_scaled_control_residual": torch_scaled_residual,
        "torch_additive_entry_control_residual": torch_additive_residual,
        "torch_raw_generator_control_residual": torch_raw_residual,
        "torch_row_erased_control_residual": torch_row_erased_residual,
        "torch_frobenius_defect": torch_fro_defect,
        "torch_order_gap_with_alternating_phase_probe": torch_order_gap,
        "torch_trace_preservation_error_on_basis_projectors": torch_trace_error,
        "jax_unitarity_residual": jax_residual,
        "jax_scaled_control_residual": jax_scaled_residual,
        "jax_additive_entry_control_residual": jax_additive_residual,
        "jax_row_erased_control_residual": jax_row_erased_residual,
        "jax_frobenius_defect": jax_fro_defect,
        "jax_order_gap_with_alternating_phase_probe": jax_order_gap,
        "jax_vs_pytorch_delta": max(
            abs(torch_residual - jax_residual),
            abs(torch_scaled_residual - jax_scaled_residual),
            abs(torch_additive_residual - jax_additive_residual),
            abs(torch_row_erased_residual - jax_row_erased_residual),
            abs(torch_order_gap - jax_order_gap),
        ),
        "known_value_checks": {
            "computed_from_operator": True,
            "trace_of_UU_adj_expected_from_dimension": float(n),
            "trace_of_UU_adj_real": float(trace_value.item()),
            "trace_delta": abs(float(trace_value.item()) - float(n)),
            "diagonal_min": float(torch.min(diagonal).item()),
            "diagonal_max": float(torch.max(diagonal).item()),
            "max_offdiagonal_abs": float(torch.max(torch.abs(offdiag)).item()),
            "scaled_control_expected_residual": abs(SCALED_CONTROL_FACTOR * SCALED_CONTROL_FACTOR - 1.0),
            "scaled_control_residual_delta": abs(
                torch_scaled_residual - abs(SCALED_CONTROL_FACTOR * SCALED_CONTROL_FACTOR - 1.0)
            ),
            "pass": bool(
                abs(float(trace_value.item()) - float(n)) <= UNITARITY_EPS
                and abs(float(torch.min(diagonal).item()) - 1.0) <= UNITARITY_EPS
                and abs(float(torch.max(diagonal).item()) - 1.0) <= UNITARITY_EPS
                and float(torch.max(torch.abs(offdiag)).item()) <= UNITARITY_EPS
                and abs(torch_scaled_residual - abs(SCALED_CONTROL_FACTOR * SCALED_CONTROL_FACTOR - 1.0)) <= 1.0e-12
            ),
        },
        "artifact": artifact,
        "pass": bool(pass_rung),
    }


def build_proofs(top: dict[str, Any]) -> dict[str, Any]:
    smt_proof = smt_unitarity_proof(
        float(top["torch_unitarity_residual"]),
        float(top["torch_scaled_control_residual"]),
    )
    sympy_proof = sympy_verdict_from_measured(
        float(top["torch_unitarity_residual"]),
        float(top["torch_scaled_control_residual"]),
    )
    return {
        "smt_unitarity_residual_bound_flip": smt_proof,
        "sympy_unitarity_residual_bound_flip": sympy_proof,
    }


def proof_passes(proofs: dict[str, Any]) -> bool:
    smt_proof = proofs["smt_unitarity_residual_bound_flip"]
    sympy_proof = proofs["sympy_unitarity_residual_bound_flip"]
    return bool(
        smt_proof["real_claim_verdict"] == "sat"
        and smt_proof["negated_claim_verdict"] == "unsat"
        and smt_proof["differ"] is True
        and smt_proof["bound_to_measured"] is True
        and smt_proof.get("cvc5_real_verdict") == "sat"
        and smt_proof.get("cvc5_control_verdict") == "unsat"
        and sympy_proof["real_claim_verdict"] == "sat"
        and sympy_proof["negated_claim_verdict"] == "unsat"
        and sympy_proof["differ"] is True
        and sympy_proof["bound_to_measured"] is True
    )


def build_tool_ablations(top: dict[str, Any]) -> dict[str, Any]:
    return {
        "torch_scaled_non_isometric_control": tool_ablation(
            "torch_unitarity_score_real_operator_vs_scaled_control",
            baseline_value=unitary_score(float(top["torch_unitarity_residual"])),
            ablated_value=unitary_score(float(top["torch_scaled_control_residual"])),
            tool="torch",
        ),
        "torch_row_erased_control": tool_ablation(
            "torch_unitarity_score_real_operator_vs_row_erased_control",
            baseline_value=unitary_score(float(top["torch_unitarity_residual"])),
            ablated_value=unitary_score(float(top["torch_row_erased_control_residual"])),
            tool="torch",
        ),
        "jax_scaled_non_isometric_control": tool_ablation(
            "jax_unitarity_score_real_operator_vs_scaled_control",
            baseline_value=unitary_score(float(top["jax_unitarity_residual"])),
            ablated_value=unitary_score(float(top["jax_scaled_control_residual"])),
            tool="jax",
        ),
    }


def ablation_passes(ablations: dict[str, Any]) -> bool:
    return all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > 1.0e-12
        and abs(
            (float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])
        )
        <= 1.0e-12
        for row in ablations.values()
    )


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    scale_rows = {n: scale_rung(n) for n in SCALES}
    top = scale_rows[64]
    proofs = build_proofs(top)
    ablations = build_tool_ablations(top)
    scale_pass = all(row["pass"] and row["known_value_checks"]["pass"] for row in scale_rows.values())
    proof_pass = proof_passes(proofs)
    ablation_pass = ablation_passes(ablations)
    all_pass = bool(scale_pass and proof_pass and ablation_pass)

    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(DTYPE),
        "operator_dimension": top["operator_dimension"],
        "unitarity_residual": top["torch_unitarity_residual"],
        "scaled_control_residual": top["torch_scaled_control_residual"],
        "row_erased_control_residual": top["torch_row_erased_control_residual"],
        "order_gap_with_alternating_phase_probe": top["torch_order_gap_with_alternating_phase_probe"],
        "trace_preservation_error_on_basis_projectors": top[
            "torch_trace_preservation_error_on_basis_projectors"
        ],
        "claim": "max_ij |(U U^*)_ij - I_ij| <= eps and scaled non-isometric control fails the same bound",
        "eps": UNITARITY_EPS,
        "pass": bool(top["torch_unitarity_residual"] <= UNITARITY_EPS and top["torch_scaled_control_residual"] > UNITARITY_EPS),
    }

    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "operator_dimension": top["operator_dimension"],
        "unitarity_residual": top["jax_unitarity_residual"],
        "scaled_control_residual": top["jax_scaled_control_residual"],
        "row_erased_control_residual": top["jax_row_erased_control_residual"],
        "order_gap_with_alternating_phase_probe": top["jax_order_gap_with_alternating_phase_probe"],
        "pass": bool(
            top["jax_unitarity_residual"] <= UNITARITY_EPS
            and top["jax_scaled_control_residual"] > UNITARITY_EPS
            and top["jax_vs_pytorch_delta"] <= 1.0e-12
        ),
    }

    controls = {
        "scaled_non_isometric": {
            "negative_control_type": "scaled unitary control",
            "definition": "C = 0.999 * U, recomputed through the same residual invariant",
            "unitarity_residual": top["torch_scaled_control_residual"],
            "claim_holds": bool(top["torch_scaled_control_residual"] <= UNITARITY_EPS),
            "pass": bool(top["torch_scaled_control_residual"] > UNITARITY_EPS),
        },
        "raw_generator_matrix": {
            "negative_control_type": "raw complex Gaussian generator before QR",
            "definition": "G from fixed-seed torch complex normal draw, with no QR normalization",
            "unitarity_residual": top["torch_raw_generator_control_residual"],
            "claim_holds": bool(top["torch_raw_generator_control_residual"] <= UNITARITY_EPS),
            "pass": bool(top["torch_raw_generator_control_residual"] > UNITARITY_EPS),
        },
        "row_erased": {
            "negative_control_type": "one-row-erased operator",
            "definition": "first row of U set to zero, then residual recomputed",
            "unitarity_residual": top["torch_row_erased_control_residual"],
            "claim_holds": bool(top["torch_row_erased_control_residual"] <= UNITARITY_EPS),
            "pass": bool(top["torch_row_erased_control_residual"] > UNITARITY_EPS),
        },
        "additive_entry_epsilon": {
            "negative_control_type": "single-entry additive perturbation",
            "definition": "C = U + E_00 * 1e-8, recomputed as a near-boundary control",
            "unitarity_residual": top["torch_additive_entry_control_residual"],
            "claim_holds": bool(top["torch_additive_entry_control_residual"] <= UNITARITY_EPS),
            "pass": bool(top["torch_additive_entry_control_residual"] > UNITARITY_EPS),
        },
    }

    return {
        "sim_id": "sim_op_unitary_probe",
        "name": "sim_op_unitary_probe",
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "object_id": OBJECT_ID,
        "finite_map": {
            "domain": "finite complex operator carrier C^d with d in {8,16,32,64}; finite basis vectors e_i and finite basis projectors |e_i><e_i|",
            "codomain_or_output": "complex dxd operator U_d, channel action Phi_U(rho)=U rho U^*, unitarity residual, trace-preservation residual, and order-gap readout",
            "definition": "G is a fixed-seed torch complex normal dxd matrix; QR plus diagonal phase correction yields U=Q diag(R_ii/|R_ii|).",
        },
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite operator dimensions, finite basis probes/projectors, finite control family, finite residual readouts",
            },
            "N01": {
                "status": "active_observed",
                "statement": "order-sensitive witness ||U P - P U||_F with finite alternating phase probe P is recomputed at every scale",
                "top_scale_order_gap": top["torch_order_gap_with_alternating_phase_probe"],
            },
        },
        "classification": "lego",
        "promotion_allowed": False,
        "tier": "Stage 5 operator/channel/generator",
        "sim_execution_kind": "nonclassical",
        "sim_class": "operator_channel_generator_probe",
        "carrier_layer": "finite complex operator/channel carrier",
        "geometry_layer": "operator/channel residual invariant only; no manifold or flux geometry is claimed",
        "carrier_realization": "torch complex128 dxd operator tensors generated by QR; no NumPy import and no dense 2^n state closure",
        "peps3d_embedding": "not_admitted_by_this_operator_channel_packet; PEPS3D/manifold consumers remain blocked",
        "spinor_state": "not_applicable_to_this_unitary_operator_channel_probe",
        "quaternion_action": "not_applicable",
        "dependency_receipts": ["task_local_design_notes:/tmp/op_design/specs.json#unitary maps"],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "allowed_claims": [
            "finite QR-generated unitary operator/channel residual bound at d=8/16/32/64",
            "SMT residual-bound claim flips against a scaled non-isometric control",
            "torch primary and JAX mirror agree on the emitted operator residuals within the declared delta bound",
            "finite order-sensitive probe U P versus P U is observed but not promoted to bridge, flux, or manifold evidence",
        ],
        "promotion_blockers": [
            "no PEPS3D carrier is admitted",
            "no spinor/quaternion/Hopf/manifold claim is made",
            "no coupling/coexistence/topology/emergence evidence is emitted",
            "Clifford is deliberately not used because no genuine rotor/geometric-product ablation exists for this arbitrary QR unitary claim",
        ],
        "eligible_consumers": [
            "future bounded Stage-5 operator/channel generator audits that need a finite unitary residual-bound receipt"
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": float(max(row["jax_vs_pytorch_delta"] for row in scale_rows.values())),
        "proof_results": proofs,
        "controls": controls,
        "tool_ablations": ablations,
        "known_value_checks": top["known_value_checks"],
        "scale_ladder": {
            "rungs": {
                str(n): {
                    "sites_or_qubits": row["sites_or_qubits"],
                    "operator_dimension": row["operator_dimension"],
                    "operator_entry_count": row["operator_entry_count"],
                    "operator_count": row["operator_count"],
                    "path_count": row["path_count"],
                    "probe_count": row["probe_count"],
                    "dense_state_closure_used": row["dense_state_closure_used"],
                    "torch_unitarity_residual": row["torch_unitarity_residual"],
                    "torch_scaled_control_residual": row["torch_scaled_control_residual"],
                    "jax_unitarity_residual": row["jax_unitarity_residual"],
                    "jax_scaled_control_residual": row["jax_scaled_control_residual"],
                    "jax_vs_pytorch_delta": row["jax_vs_pytorch_delta"],
                    "known_value_checks_pass": row["known_value_checks"]["pass"],
                    "artifact": row["artifact"],
                    "pass": row["pass"],
                }
                for n, row in scale_rows.items()
            },
            "pass": bool(scale_pass),
        },
        "scale_details": scale_rows,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["torch", "jax", "z3", "cvc5", "sympy"],
        "actual_tools_used": ["torch", "jax", "z3", "cvc5", "sympy"],
        "proof_surfaces_used": ["z3 residual-bound SMT flip", "cvc5 residual-bound SMT flip", "sympy rationalized residual-bound flip"],
        "required_negatives": ["scaled_non_isometric", "raw_generator_matrix", "row_erased", "additive_entry_epsilon"],
        "negatives_run": list(controls.keys()),
        "kill_conditions": [
            "real operator residual exceeds eps",
            "scaled control satisfies residual bound",
            "proof verdicts do not flip",
            "JAX mirror disagrees with torch beyond delta bound",
            "any emitted scale rung uses dense state closure",
        ],
        "artifacts_emitted": [
            row["artifact"]["path"]
            for row in scale_rows.values()
        ]
        + [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{OBJECT_ID}:seed={SEED}:scales={','.join(str(n) for n in SCALES)}",
        "result_summary": {
            "scale_pass": bool(scale_pass),
            "proof_pass": bool(proof_pass),
            "ablation_pass": bool(ablation_pass),
            "all_pass": bool(all_pass),
        },
        "pass_rule": "all scale rungs pass without dense state closure; z3/cvc5/sympy proof verdicts flip for residual<=eps; torch/JAX controls recompute nonzero numeric ablations",
        "fail_rule": "fail on missing proof flip, cvc5 skip/nonflip, cosmetic ablation fields, JAX mismatch, live degenerate control, dense-state closure, or downstream promotion",
        "promotion_status": "keep_but_open",
        "all_pass": all_pass,
        "required_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    OUT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
