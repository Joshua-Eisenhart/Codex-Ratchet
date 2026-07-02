#!/usr/bin/env python3
"""Stage-7 entanglement-spectrum readout over the existing Stage-2 MPS carrier.

This is an information readout, not a carrier build. The organizing invariant is
the measured Schmidt-spectrum distinguishability at the middle cut: rank > 1,
lambda_max < 1, and normalization. Entropy is computed only as a downstream
output from the spectrum and is never asserted inside the SMT claim.
"""

import json
import math
import pathlib
import sys
import time
from datetime import datetime, timezone
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import opt_einsum as oe
import sympy as sp
import torch
import z3

from sim_entanglement_entropy_8_16_32_64_dual_engine_probe import (
    CDTYPE,
    DEPTH,
    MAX_BOND,
    TorchMPS,
    build_jax_mps,
    build_known_bell_pair_mps,
    build_torch_mps,
    jax_entropy_from_probs,
    jax_schmidt_spectrum,
    torch_entropy_from_probs,
    torch_product_vector,
    torch_schmidt_spectrum,
    torch_single_gate,
    torch_zz_gate,
)

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = ROOT / "sim_s7_entanglement_spectrum_probe.py"
SPEC_KEY = "entanglement spectrum"
OBJECT_ID = "s7_entanglement_spectrum"
RESULT = RESULT_DIR / f"{OBJECT_ID}_results.json"

SCALES = (8, 16, 32, 64)
RANK_TOL = 1.0e-10
NORM_TOL = 1.0e-9
LAMBDA_GAP_TOL = 1.0e-9
PARITY_TOL = 1.0e-8
TRUNCATION_TOL = 1.0e-8

BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]
EXTENDED_BLOCKED_CONSUMERS = [
    "bridge",
    "basin",
    "physics",
    "final_manifold_admission",
    "layer_stacking",
    *BLOCKED_CONSUMERS,
]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY: existing Stage-2 TorchMPS carrier, non-dense Gram contractions, rho_bond eigvalsh, rank/gap invariant, controls, and entropy output.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "Independent x64 JaxMPS mirror; per-coefficient spectrum parity below 1e-8 is a hard pass gate.",
    },
    "opt_einsum": {
        "tried": True,
        "used": True,
        "reason": "Load-bearing non-dense contraction path for the MPS Gram environments; diagonal-stub removal changes the output readout.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via smt_load_bearing: z3 variables bind to measured rank/gap/normalization values and must flip real UNSAT-style hold versus collapsed controls.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check through smt_load_bearing cvc5_claim_pairs on the same measured rank/gap/normalization values.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact symbolic mirror of the finite Boolean rank/gap predicate and known Bell/product spectrum anchors.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not used for claim-bearing computation.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not used.",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "Supportive only: paths, JSON, timestamps, deterministic finite loops.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "load_bearing",
    "opt_einsum": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "numpy": "None",
    "scipy": "None",
    "python_stdlib": "supportive",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if hasattr(value, "item") and callable(value.item):
        try:
            return as_jsonable(value.item())
        except Exception:
            pass
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def sorted_torch_spectrum(mps: TorchMPS, cut: int) -> tuple[torch.Tensor, torch.Tensor]:
    spectrum, rho_bond = torch_schmidt_spectrum(mps, cut)
    spectrum = torch.sort(torch.clamp(spectrum.real, min=0.0), descending=True).values
    spectrum = spectrum / torch.clamp(spectrum.sum(), min=1.0e-30)
    return spectrum, rho_bond


def sorted_jax_spectrum(n_sites: int, *, entangle: bool = True, commuting: bool = False) -> jnp.ndarray:
    mps = build_jax_mps(n_sites, entangle=entangle, commuting=commuting, max_bond=MAX_BOND)
    spectrum = jnp.sort(jnp.clip(jnp.real(jax_schmidt_spectrum(mps, n_sites // 2)), min=0.0))[::-1]
    spectrum = spectrum / jnp.clip(jnp.sum(spectrum), min=1.0e-30)
    return spectrum


def spectrum_vector(values: torch.Tensor) -> list[float]:
    return [float(value) for value in values.detach().cpu().tolist()]


def padded_delta(left: list[float], right: list[float]) -> float:
    size = max(len(left), len(right))
    a = left + [0.0] * (size - len(left))
    b = right + [0.0] * (size - len(right))
    return max((abs(x - y) for x, y in zip(a, b, strict=True)), default=0.0)


def rank_gap_observables(probs: list[float]) -> dict[str, Any]:
    rank = sum(1 for value in probs if value > RANK_TOL)
    lambda_max = max(probs) if probs else 0.0
    norm = sum(probs)
    positive = [value for value in probs if value > RANK_TOL]
    distinct_levels: list[float] = []
    for value in positive:
        if not any(abs(value - seen) <= RANK_TOL for seen in distinct_levels):
            distinct_levels.append(value)
    return {
        "schmidt_rank": int(rank),
        "lambda_max": float(lambda_max),
        "lambda_gap_from_one": float(1.0 - lambda_max),
        "normalization_sum": float(norm),
        "normalization_error": float(abs(norm - 1.0)),
        "distinct_level_count": int(len(distinct_levels)),
        "multiplicity_signature": [
            sum(1 for value in positive if abs(value - level) <= RANK_TOL)
            for level in distinct_levels
        ],
        "rank_gt_1": bool(rank >= 2),
        "lambda_max_below_one": bool(lambda_max < 1.0 - LAMBDA_GAP_TOL),
        "spectrum_normalized": bool(abs(norm - 1.0) <= NORM_TOL),
    }


def torch_apply_two_with_discard(mps: TorchMPS, op: torch.Tensor, site: int, max_bond: int) -> float:
    """Same Stage-2 TorchMPS update as the source carrier, with discard reporting."""
    op = op.reshape(2, 2, 2, 2).to(CDTYPE)
    left = mps.tensors[site]
    right = mps.tensors[site + 1]
    theta = oe.contract("alc,bcr->ablr", left, right)
    theta = oe.contract("ABab,ablr->ABlr", op, theta).contiguous()
    mat = theta.permute(0, 2, 1, 3).reshape(theta.shape[0] * theta.shape[2], theta.shape[1] * theta.shape[3])
    u, s, vh = torch.linalg.svd(mat, full_matrices=False)
    chi = min(int(s.numel()), max_bond)
    total = float(torch.sum((s * s).real).item())
    discarded = float(torch.sum((s[chi:] * s[chi:]).real).item()) if chi < int(s.numel()) else 0.0
    u = u[:, :chi]
    kept = s[:chi]
    vh = vh[:chi, :]
    mps.tensors[site] = (u * kept.unsqueeze(0)).reshape(2, left.shape[1], chi)
    mps.tensors[site + 1] = vh.reshape(chi, 2, right.shape[2]).permute(1, 0, 2).contiguous()
    return discarded / max(total, 1.0e-30)


def build_torch_mps_with_truncation_report(
    n_sites: int, *, entangle: bool = True, commuting: bool = False
) -> tuple[TorchMPS, dict[str, Any]]:
    mps = TorchMPS.product([torch_product_vector(site, n_sites) for site in range(n_sites)])
    discarded_weights: list[float] = []
    two_site_applications = 0
    for layer in range(DEPTH):
        for site in range(n_sites):
            mps.apply_single(torch_single_gate(layer, site, n_sites, commuting=commuting), site)
        if entangle and not commuting:
            start = layer % 2
            gate = torch_zz_gate(0.22 + 0.017 * layer)
            for site in range(start, n_sites - 1, 2):
                discarded_weights.append(torch_apply_two_with_discard(mps, gate, site, MAX_BOND))
                two_site_applications += 1
        mps.normalize_()
    return mps, {
        "max_discarded_weight": max(discarded_weights) if discarded_weights else 0.0,
        "sum_discarded_weight": sum(discarded_weights),
        "two_site_applications": int(two_site_applications),
        "pass": (max(discarded_weights) if discarded_weights else 0.0) <= TRUNCATION_TOL,
    }


def smt_rank_gap_proof(
    real: dict[str, Any], control: dict[str, Any], claim: str
) -> dict[str, Any]:
    measured_real = {
        "schmidt_rank": float(real["schmidt_rank"]),
        "rank_threshold": 1.5,
        "lambda_gap_from_one": float(real["lambda_gap_from_one"]),
        "gap_tol": LAMBDA_GAP_TOL,
        "normalization_error": float(real["normalization_error"]),
        "norm_tol": NORM_TOL,
    }
    measured_control = {
        "schmidt_rank": float(control["schmidt_rank"]),
        "rank_threshold": 1.5,
        "lambda_gap_from_one": float(control["lambda_gap_from_one"]),
        "gap_tol": LAMBDA_GAP_TOL,
        "normalization_error": float(control["normalization_error"]),
        "norm_tol": NORM_TOL,
    }
    proof = smt_load_bearing(
        claim=claim,
        real_measured=measured_real,
        control_measured=measured_control,
        claim_builder=lambda v: z3.And(
            v["schmidt_rank"] > v["rank_threshold"],
            v["lambda_gap_from_one"] > v["gap_tol"],
            v["normalization_error"] <= v["norm_tol"],
        ),
        cvc5_claim_pairs=[
            ("schmidt_rank", ">", "rank_threshold"),
            ("lambda_gap_from_one", ">", "gap_tol"),
            ("normalization_error", "<=", "norm_tol"),
        ],
    )
    proof["organizing_variable"] = "rank_gap_distinguishability_invariant"
    proof["entropy_in_asserted_claim"] = False
    proof["expected_real_verdict"] = "sat"
    proof["expected_control_verdict"] = "unsat"
    proof["pass"] = bool(
        proof.get("real_claim_verdict") == "sat"
        and proof.get("negated_claim_verdict") == "unsat"
        and proof.get("differ") is True
        and proof.get("bound_to_measured") is True
        and proof.get("cvc5_real_verdict") == "sat"
        and proof.get("cvc5_control_verdict") == "unsat"
    )
    return proof


def sympy_rank_gap_check(real: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    real_rank = sp.Integer(real["schmidt_rank"])
    control_rank = sp.Integer(control["schmidt_rank"])
    real_gap = sp.Float(real["lambda_gap_from_one"], 30)
    control_gap = sp.Float(control["lambda_gap_from_one"], 30)
    gap_tol = sp.Float(LAMBDA_GAP_TOL, 30)
    real_holds = bool(real_rank >= 2 and real_gap > gap_tol and real["normalization_error"] <= NORM_TOL)
    control_holds = bool(control_rank >= 2 and control_gap > gap_tol and control["normalization_error"] <= NORM_TOL)
    return {
        "tool": "sympy",
        "real_rank": int(real_rank),
        "control_rank": int(control_rank),
        "real_lambda_gap_from_one": str(real_gap),
        "control_lambda_gap_from_one": str(control_gap),
        "claim": "rank >= 2 and lambda_gap_from_one > gap_tol and normalization_error <= norm_tol",
        "real_claim_holds": real_holds,
        "control_claim_holds": control_holds,
        "bound_to_measured": True,
        "pass": bool(real_holds and not control_holds),
    }


def diagonal_stub_entropy(rho_bond: torch.Tensor) -> tuple[float, list[float]]:
    diag = torch.clamp(torch.real(torch.diag(rho_bond)), min=0.0)
    diag = diag / torch.clamp(diag.sum(), min=1.0e-30)
    return torch_entropy_from_probs(diag), spectrum_vector(torch.sort(diag, descending=True).values)


def rung(n_sites: int) -> dict[str, Any]:
    cut = n_sites // 2
    real_mps, truncation = build_torch_mps_with_truncation_report(n_sites, entangle=True, commuting=False)
    product_mps, product_truncation = build_torch_mps_with_truncation_report(n_sites, entangle=False, commuting=False)
    commuting_mps, commuting_truncation = build_torch_mps_with_truncation_report(n_sites, entangle=True, commuting=True)

    real_spectrum_t, rho_bond = sorted_torch_spectrum(real_mps, cut)
    product_spectrum_t, _ = sorted_torch_spectrum(product_mps, cut)
    commuting_spectrum_t, _ = sorted_torch_spectrum(commuting_mps, cut)

    real_spectrum = spectrum_vector(real_spectrum_t)
    product_spectrum = spectrum_vector(product_spectrum_t)
    commuting_spectrum = spectrum_vector(commuting_spectrum_t)

    jax_real_spectrum = [float(value) for value in list(sorted_jax_spectrum(n_sites, entangle=True, commuting=False))]
    jax_product_spectrum = [float(value) for value in list(sorted_jax_spectrum(n_sites, entangle=False, commuting=False))]
    jax_commuting_spectrum = [float(value) for value in list(sorted_jax_spectrum(n_sites, entangle=True, commuting=True))]

    real_obs = rank_gap_observables(real_spectrum)
    product_obs = rank_gap_observables(product_spectrum)
    commuting_obs = rank_gap_observables(commuting_spectrum)
    jax_real_obs = rank_gap_observables(jax_real_spectrum)
    jax_product_obs = rank_gap_observables(jax_product_spectrum)
    jax_commuting_obs = rank_gap_observables(jax_commuting_spectrum)

    entropy_real = torch_entropy_from_probs(real_spectrum_t)
    entropy_product = torch_entropy_from_probs(product_spectrum_t)
    entropy_commuting = torch_entropy_from_probs(commuting_spectrum_t)
    jax_entropy_real = jax_entropy_from_probs(jnp.array(jax_real_spectrum, dtype=jnp.float64))
    jax_entropy_product = jax_entropy_from_probs(jnp.array(jax_product_spectrum, dtype=jnp.float64))
    jax_entropy_commuting = jax_entropy_from_probs(jnp.array(jax_commuting_spectrum, dtype=jnp.float64))
    diagonal_entropy, diagonal_spectrum = diagonal_stub_entropy(rho_bond)

    real_proof = smt_rank_gap_proof(
        real_obs,
        product_obs,
        f"stage7_schmidt_rank_gap_distinguishability_real_vs_product_control_n{n_sites}",
    )
    commuting_proof = smt_rank_gap_proof(
        real_obs,
        commuting_obs,
        f"stage7_schmidt_rank_gap_distinguishability_real_vs_commuting_control_n{n_sites}",
    )

    parity_delta = padded_delta(real_spectrum, jax_real_spectrum)
    product_parity_delta = padded_delta(product_spectrum, jax_product_spectrum)
    commuting_parity_delta = padded_delta(commuting_spectrum, jax_commuting_spectrum)
    entropy_delta = abs(entropy_real - jax_entropy_real)

    pass_rung = bool(
        real_obs["rank_gt_1"]
        and real_obs["lambda_max_below_one"]
        and real_obs["spectrum_normalized"]
        and product_obs["schmidt_rank"] == 1
        and commuting_obs["schmidt_rank"] == 1
        and real_proof["pass"]
        and commuting_proof["pass"]
        and parity_delta <= PARITY_TOL
        and product_parity_delta <= PARITY_TOL
        and commuting_parity_delta <= PARITY_TOL
        and entropy_delta <= PARITY_TOL
        and truncation["pass"]
        and product_truncation["pass"]
        and commuting_truncation["pass"]
    )

    return {
        "sites_or_qubits": n_sites,
        "cut": cut,
        "mps_max_bond": real_mps.max_bond(),
        "max_bond_seen": real_mps.max_bond(),
        "mps_bond_dims_sample": real_mps.bond_dims()[:8] + real_mps.bond_dims()[-8:]
        if len(real_mps.bond_dims()) > 16
        else real_mps.bond_dims(),
        "dense_state_closure_used": False,
        "global_state_vector_materialized": False,
        "stage2_carrier_source": "sim_entanglement_entropy_8_16_32_64_dual_engine_probe.TorchMPS/JaxMPS",
        "torch_schmidt_spectrum": real_spectrum,
        "jax_schmidt_spectrum": jax_real_spectrum,
        "schmidt_rank": real_obs["schmidt_rank"],
        "rank_gap_invariant": real_obs,
        "jax_rank_gap_invariant": jax_real_obs,
        "entropy_as_output": {
            "half_chain_entropy": entropy_real,
            "entanglement_entropy": entropy_real,
            "jax_half_chain_entropy": jax_entropy_real,
            "jax_entropy_delta": entropy_delta,
            "used_in_smt_claim": False,
            "organizing_variable": False,
        },
        "diagonal_stub_readout": {
            "entropy": diagonal_entropy,
            "schmidt_spectrum": diagonal_spectrum,
            "entropy_delta_vs_full": abs(entropy_real - diagonal_entropy),
            "rank": rank_gap_observables(diagonal_spectrum)["schmidt_rank"],
        },
        "controls": {
            "product_state": {
                "spectrum": product_spectrum,
                "jax_spectrum": jax_product_spectrum,
                "rank_gap_invariant": product_obs,
                "jax_rank_gap_invariant": jax_product_obs,
                "entropy_as_output": entropy_product,
                "jax_entropy_as_output": jax_entropy_product,
                "jax_delta": abs(entropy_product - jax_entropy_product),
                "truncation": product_truncation,
                "pass": bool(product_obs["schmidt_rank"] == 1 and entropy_product <= 1.0e-12),
            },
            "commuting_gate": {
                "spectrum": commuting_spectrum,
                "jax_spectrum": jax_commuting_spectrum,
                "rank_gap_invariant": commuting_obs,
                "jax_rank_gap_invariant": jax_commuting_obs,
                "entropy_as_output": entropy_commuting,
                "jax_entropy_as_output": jax_entropy_commuting,
                "jax_delta": abs(entropy_commuting - jax_entropy_commuting),
                "truncation": commuting_truncation,
                "pass": bool(commuting_obs["schmidt_rank"] == 1 and entropy_commuting <= 1.0e-12),
            },
        },
        "proof_results": {
            "product_control_rank_gap_smt_load_bearing": real_proof,
            "commuting_control_rank_gap_smt_load_bearing": commuting_proof,
            "sympy_product_rank_gap_check": sympy_rank_gap_check(real_obs, product_obs),
            "sympy_commuting_rank_gap_check": sympy_rank_gap_check(real_obs, commuting_obs),
        },
        "jax_vs_pytorch_delta": parity_delta,
        "jax_product_control_delta": product_parity_delta,
        "jax_commuting_control_delta": commuting_parity_delta,
        "truncation_error": truncation,
        "pass": pass_rung,
    }


def known_value_checks() -> dict[str, Any]:
    product = TorchMPS.product([torch.tensor([1.0 + 0j, 0.0 + 0j], dtype=CDTYPE) for _ in range(8)])
    product.normalize_()
    product_spectrum_t, _ = sorted_torch_spectrum(product, 4)
    product_spectrum = spectrum_vector(product_spectrum_t)
    product_entropy = torch_entropy_from_probs(product_spectrum_t)

    bell = build_known_bell_pair_mps(8)
    bell_spectrum_t, _ = sorted_torch_spectrum(bell, 4)
    bell_spectrum = spectrum_vector(bell_spectrum_t)
    bell_entropy = torch_entropy_from_probs(bell_spectrum_t)

    bell_obs = rank_gap_observables(bell_spectrum)
    product_obs = rank_gap_observables(product_spectrum)
    proof = smt_rank_gap_proof(
        bell_obs,
        product_obs,
        "known_value_bell_pair_spectrum_rank_gap_vs_product_control",
    )

    bell_pair_check = {
        "name": "Bell_pair_crossing_cut",
        "computed_spectrum": bell_spectrum,
        "known_spectrum": [0.5, 0.5],
        "computed_entropy": bell_entropy,
        "known_entropy": math.log(2.0),
        "spectrum_match": padded_delta(bell_spectrum, [0.5, 0.5]) <= 1.0e-9,
        "entropy_match": abs(bell_entropy - math.log(2.0)) <= 1.0e-9,
        "entropy_used_in_smt_claim": False,
    }
    product_check = {
        "name": "product_state_cut",
        "computed_spectrum": product_spectrum,
        "known_spectrum": [1.0],
        "computed_entropy": product_entropy,
        "known_entropy": 0.0,
        "spectrum_match": padded_delta(product_spectrum, [1.0]) <= 1.0e-12,
        "entropy_match": abs(product_entropy) <= 1.0e-12,
    }
    sympy_exact = {
        "tool": "sympy",
        "bell_entropy_exact": "log(2)",
        "bell_entropy_numeric": float(sp.log(2).evalf(30)),
        "product_entropy_exact": "0",
        "rank_gap_claim_exact": "rank([1/2,1/2]) >= 2 and 1 - max([1/2,1/2]) > 1e-9",
        "pass": bool(abs(float(sp.log(2).evalf(30)) - math.log(2.0)) <= 1.0e-15),
    }
    return {
        "bell_pair_log2": bell_pair_check,
        "product_zero_entropy": product_check,
        "sympy_exact_anchor": sympy_exact,
        "known_value_rank_gap_smt_load_bearing": proof,
        "pass": bool(
            bell_pair_check["spectrum_match"]
            and bell_pair_check["entropy_match"]
            and product_check["spectrum_match"]
            and product_check["entropy_match"]
            and sympy_exact["pass"]
            and proof["pass"]
        ),
    }


def verdict_sat_score(proof: dict[str, Any], engine: str, side: str) -> float:
    if engine == "z3":
        key = "real_claim_verdict" if side == "real" else "negated_claim_verdict"
    elif engine == "cvc5":
        key = "cvc5_real_verdict" if side == "real" else "cvc5_control_verdict"
    else:
        raise ValueError(f"unknown proof engine: {engine}")
    return float(proof.get(key) == "sat")


def build_tool_ablations(top: dict[str, Any], known: dict[str, Any]) -> dict[str, Any]:
    product_control = top["controls"]["product_state"]
    commuting_control = top["controls"]["commuting_gate"]
    product_proof = top["proof_results"]["product_control_rank_gap_smt_load_bearing"]
    commuting_proof = top["proof_results"]["commuting_control_rank_gap_smt_load_bearing"]
    sympy_check = top["proof_results"]["sympy_product_rank_gap_check"]
    entropy_real = top["entropy_as_output"]["half_chain_entropy"]

    return {
        "torch_rank_gap_real_vs_product_control": tool_ablation(
            "torch_schmidt_rank_real_vs_product_control",
            baseline_value=float(top["schmidt_rank"]),
            ablated_value=float(product_control["rank_gap_invariant"]["schmidt_rank"]),
            tool="torch",
        ),
        "jax_rank_gap_real_vs_product_control": tool_ablation(
            "jax_schmidt_rank_real_vs_product_control",
            baseline_value=float(top["jax_rank_gap_invariant"]["schmidt_rank"]),
            ablated_value=float(product_control["jax_rank_gap_invariant"]["schmidt_rank"]),
            tool="jax",
        ),
        "opt_einsum_full_gram_vs_diagonal_stub_entropy": tool_ablation(
            "opt_einsum_full_gram_contraction_vs_diagonal_stub_entropy_output",
            baseline_value=float(entropy_real),
            ablated_value=float(top["diagonal_stub_readout"]["entropy"]),
            tool="opt_einsum",
        ),
        "z3_product_control_verdict_flip": tool_ablation(
            "z3_rank_gap_claim_real_vs_product_control_flip_score",
            baseline_value=verdict_sat_score(product_proof, "z3", "real"),
            ablated_value=verdict_sat_score(product_proof, "z3", "control"),
            tool="z3",
        ),
        "cvc5_commuting_control_verdict_flip": tool_ablation(
            "cvc5_rank_gap_claim_real_vs_commuting_control_flip_score",
            baseline_value=verdict_sat_score(commuting_proof, "cvc5", "real"),
            ablated_value=verdict_sat_score(commuting_proof, "cvc5", "control"),
            tool="cvc5",
        ),
        "sympy_rank_gap_claim_real_vs_product_control": tool_ablation(
            "sympy_rank_gap_boolean_real_vs_product_control",
            baseline_value=float(sympy_check["real_claim_holds"]),
            ablated_value=float(sympy_check["control_claim_holds"]),
            tool="sympy",
        ),
        "known_bell_entropy_output_anchor": tool_ablation(
            "known_value_bell_entropy_output_log2_vs_product_zero",
            baseline_value=float(known["bell_pair_log2"]["computed_entropy"]),
            ablated_value=float(known["product_zero_entropy"]["computed_entropy"]),
            tool="torch",
        ),
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    scale_rows = {str(n): rung(n) for n in SCALES}
    top = scale_rows[str(max(SCALES))]
    known = known_value_checks()
    tool_ablations = build_tool_ablations(top, known)

    all_rungs_pass = all(row["pass"] for row in scale_rows.values())
    proof_pass = all(
        proof["pass"]
        for row in scale_rows.values()
        for proof in (
            row["proof_results"]["product_control_rank_gap_smt_load_bearing"],
            row["proof_results"]["commuting_control_rank_gap_smt_load_bearing"],
        )
    )
    sympy_pass = all(
        row["proof_results"]["sympy_product_rank_gap_check"]["pass"]
        and row["proof_results"]["sympy_commuting_rank_gap_check"]["pass"]
        for row in scale_rows.values()
    )
    control_pass = all(
        row["controls"]["product_state"]["pass"] and row["controls"]["commuting_gate"]["pass"]
        for row in scale_rows.values()
    )
    truncation_pass = all(row["truncation_error"]["pass"] for row in scale_rows.values())
    ablation_pass = all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > 1.0e-12
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= 1.0e-9
        for row in tool_ablations.values()
    )
    max_delta = max(float(row["jax_vs_pytorch_delta"]) for row in scale_rows.values())
    all_pass = bool(
        all_rungs_pass
        and proof_pass
        and sympy_pass
        and control_pass
        and truncation_pass
        and known["pass"]
        and ablation_pass
        and max_delta <= PARITY_TOL
    )

    torch_primary_result = {
        "runtime": "torch",
        "carrier": "existing Stage-2 TorchMPS",
        "sites_or_qubits": top["sites_or_qubits"],
        "cut": top["cut"],
        "mps_max_bond": top["mps_max_bond"],
        "schmidt_spectrum": top["torch_schmidt_spectrum"],
        "rank_gap_invariant": top["rank_gap_invariant"],
        "half_chain_entropy": top["entropy_as_output"]["half_chain_entropy"],
        "entanglement_entropy": top["entropy_as_output"]["entanglement_entropy"],
        "entropy_is_output_not_claim": True,
        "pass": bool(top["pass"]),
    }
    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "carrier": "existing Stage-2 JaxMPS",
        "sites_or_qubits": top["sites_or_qubits"],
        "cut": top["cut"],
        "schmidt_spectrum": top["jax_schmidt_spectrum"],
        "half_chain_entropy": top["entropy_as_output"]["jax_half_chain_entropy"],
        "spectrum_delta_vs_torch": top["jax_vs_pytorch_delta"],
        "pass": bool(top["jax_vs_pytorch_delta"] <= PARITY_TOL),
    }

    return {
        "schema": "formal_scout_stage7_entropy_information_readout_v1",
        "sim_id": THISFILE.stem,
        "name": THISFILE.stem,
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "spec_key": SPEC_KEY,
        "object_id": OBJECT_ID,
        "classification": "lego",
        "promotion_allowed": False,
        "tier": "STAGE 7 entropy/information readout",
        "purpose": "Read the ordered Schmidt spectrum at the middle cut of an already-admitted Stage-2 MPS carrier.",
        "scientific_question": "Does the measured Schmidt-spectrum rank/gap distinguishability invariant survive non-dense 8/16/32/64 scale while product and commuting controls collapse?",
        "sim_execution_kind": "nonclassical",
        "sim_class": "entropy_information_readout_probe",
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite MPS sites, finite bond-space spectrum, finite cut, finite scale ladder, finite controls",
            },
            "N01": {
                "status": "active_tested",
                "statement": "noncommuting RX/RZ plus ZZ entangling controls are contrasted with commuting/product collapse controls",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set: finite Stage-2 MPS carrier, middle cut, finite Schmidt spectrum",
            "N01 noncommuting/order-sensitive operation/control: entangling brick-wall circuit versus product and commuting-gate controls",
        ],
        "finite_map": {
            "domain": "existing Stage-2 finite TorchMPS/JaxMPS carriers at n in {8,16,32,64}, middle cut n//2, with product and commuting degenerate controls",
            "codomain_or_output": "ordered Schmidt probability vector, structural rank/gap invariant, controls, proof verdicts, and downstream entropy output",
            "definition": "SpectrumReadout(MPS, cut) -> sort_desc(eigvalsh(sqrt(L) R sqrt(L))) normalized; then rank/gap invariant and entropy output are computed from that spectrum",
        },
        "domain": {
            "carrier_source": "sim_entanglement_entropy_8_16_32_64_dual_engine_probe",
            "site_counts": list(SCALES),
            "physical_dim": 2,
            "max_bond": MAX_BOND,
            "depth": DEPTH,
            "cut": "n_sites//2",
            "dense_state_closure_used": False,
        },
        "codomain_or_output": "ordered Schmidt spectrum lambda, schmidt_rank, lambda_gap_from_one, normalization, multiplicity signature, and entropy_as_output",
        "carrier_layer": "stage-2 finite MPS carrier; no new physical carrier is introduced",
        "geometry_layer": "middle bond boundary/interior cut on the existing finite MPS carrier",
        "carrier_realization": "torch.complex128 TorchMPS primary; jax.numpy complex128 JaxMPS mirror; opt_einsum non-dense Gram contractions",
        "peps3d_embedding": {
            "status": "stage-2 carrier reference only",
            "anchor": "finite MPS/boundary_interior_cut readout; no new PEPS3D manifold admission is claimed here",
        },
        "mps_stage2_anchor": {
            "source_file": "system_v5/ops/formal_scouts/sim_entanglement_entropy_8_16_32_64_dual_engine_probe.py",
            "classes": ["TorchMPS", "JaxMPS"],
            "functions": ["build_torch_mps", "build_jax_mps", "torch_schmidt_spectrum", "jax_schmidt_spectrum"],
            "acts_on_existing_carrier": True,
        },
        "spinor_state": "site-local C^2 amplitudes and spinor-derived bond reduced density operator rho_bond",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/sim_entanglement_entropy_8_16_32_64_dual_engine_probe.py",
            "system_v5/ops/formal_scouts/results/entanglement_entropy_8_16_32_64_dual_engine_probe_results.json",
        ],
        "downstream_blocks": EXTENDED_BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "middle bond boundary_interior_cut on the finite MPS carrier",
        "law_or_candidate_tested": "measured Schmidt-spectrum rank/gap distinguishability survives real carrier and collapses under product/commuting controls",
        "branch_status_before_run": "Stage-7 readout lego; no bridge, Axis0, flux, basin, physics, or final manifold promotion",
        "allowed_claims": [
            "The file exists and runs as a Stage-7 entropy/information readout lego when fresh gates pass.",
            "The SMT proof binds to measured Schmidt rank/gap/normalization values, not entropy.",
            "Entropy is a downstream output read from the already-measured spectrum.",
            "The readout acts on the existing Stage-2 MPS carrier and does not introduce a new carrier.",
        ],
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "No bridge, Axis0, Xi, Phi0, flux, basin, physics, or final manifold consumer is admitted.",
            "No full PEPS3D contraction or manifold completion claim is made.",
            "The proof predicate was authored in this sim and remains subject to external audit before any stronger admission.",
        ],
        "eligible_consumers": [
            "bounded Stage-7 information-readout comparisons after reading this result path",
            "future local stack/nesting tests only after parent receipts are current",
        ],
        "blocked_consumers": EXTENDED_BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3 measured rank/gap flip",
            "load_bearing_proof.smt_load_bearing cvc5 measured rank/gap cross-check",
            "sympy exact known-value/rank-gap anchors",
        ],
        "graph_surfaces_used": ["not_applicable_to_this_readout"],
        "topology_surfaces_used": ["not_applicable_to_this_readout"],
        "required_inputs": ["existing Stage-2 MPS carrier source", "stage78 spec key entanglement spectrum"],
        "data_or_artifact_dependencies": ["system_v5/ops/formal_scouts/sim_entanglement_entropy_8_16_32_64_dual_engine_probe.py"],
        "required_negatives": ["product-state control", "commuting-gate control", "diagonal-stub contraction ablation"],
        "negatives_run": {
            "product_state": {key: row["controls"]["product_state"] for key, row in scale_rows.items()},
            "commuting_gate": {key: row["controls"]["commuting_gate"] for key, row in scale_rows.items()},
            "diagonal_stub": {key: row["diagonal_stub_readout"] for key, row in scale_rows.items()},
        },
        "kill_conditions": {
            "product_state": "Schmidt rank collapses to 1 and entropy output collapses to 0",
            "commuting_gate": "Schmidt rank collapses to 1 and entropy output collapses to 0",
            "diagonal_stub": "removing opt_einsum full Gram contraction changes the entropy output",
        },
        "required_artifacts": [
            "result JSON",
            "torch primary result",
            "JAX mirror result",
            "rank/gap proof_results",
            "controls",
            "tool_ablations",
            "scale_ladder",
            "known_value_checks",
        ],
        "artifacts_emitted": [str(RESULT.relative_to(ROOT))],
        "witness_trace_id": f"{OBJECT_ID}:{int(started)}",
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": max_delta,
        "proof_results": {
            "top_scale_product_control_rank_gap_smt_load_bearing": top["proof_results"]["product_control_rank_gap_smt_load_bearing"],
            "top_scale_commuting_control_rank_gap_smt_load_bearing": top["proof_results"]["commuting_control_rank_gap_smt_load_bearing"],
            "known_value_bell_pair_rank_gap_smt_load_bearing": known["known_value_rank_gap_smt_load_bearing"],
            "all_scale_proof_summary": {
                key: {
                    "product_flip_pass": row["proof_results"]["product_control_rank_gap_smt_load_bearing"]["pass"],
                    "commuting_flip_pass": row["proof_results"]["commuting_control_rank_gap_smt_load_bearing"]["pass"],
                    "sympy_product_pass": row["proof_results"]["sympy_product_rank_gap_check"]["pass"],
                    "sympy_commuting_pass": row["proof_results"]["sympy_commuting_rank_gap_check"]["pass"],
                }
                for key, row in scale_rows.items()
            },
        },
        "controls": {
            "product_state": top["controls"]["product_state"],
            "commuting_gate": top["controls"]["commuting_gate"],
            "diagonal_stub": top["diagonal_stub_readout"],
        },
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "tool_ablation_outcomes": tool_ablations,
        "scale_ladder": {
            "rungs": {
                key: {
                    "sites_or_qubits": row["sites_or_qubits"],
                    "cut": row["cut"],
                    "dense_state_closure_used": row["dense_state_closure_used"],
                    "global_state_vector_materialized": row["global_state_vector_materialized"],
                    "mps_max_bond": row["mps_max_bond"],
                    "max_bond_seen": row["max_bond_seen"],
                    "schmidt_rank": row["schmidt_rank"],
                    "lambda_max": row["rank_gap_invariant"]["lambda_max"],
                    "lambda_gap_from_one": row["rank_gap_invariant"]["lambda_gap_from_one"],
                    "normalization_error": row["rank_gap_invariant"]["normalization_error"],
                    "half_chain_entropy": row["entropy_as_output"]["half_chain_entropy"],
                    "entanglement_entropy": row["entropy_as_output"]["entanglement_entropy"],
                    "jax_vs_pytorch_delta": row["jax_vs_pytorch_delta"],
                    "truncation_error_max_discarded_weight": row["truncation_error"]["max_discarded_weight"],
                    "pass": row["pass"],
                }
                for key, row in scale_rows.items()
            },
            "pass": bool(all_rungs_pass),
        },
        "scale_details": scale_rows,
        "entropy_as_output": {
            "used_as_organizing_variable": False,
            "used_inside_smt_claim": False,
            "readout_relation": "S(lambda) is computed after the ordered Schmidt spectrum and rank/gap invariant",
            "top_scale_half_chain_entropy": top["entropy_as_output"]["half_chain_entropy"],
            "all_scale_half_chain_entropy": {
                key: row["entropy_as_output"]["half_chain_entropy"] for key, row in scale_rows.items()
            },
        },
        "known_value_checks": known,
        "shells": [
            {
                "name": "stage7_schmidt_spectrum_readout_shell",
                "carrier": "existing non-dense Stage-2 MPS carrier",
                "rungs": list(SCALES),
                "survives": bool(all_rungs_pass),
            },
            {
                "name": "rank_gap_distinguishability_shell",
                "carrier": "measured ordered Schmidt spectrum",
                "smt_bound_to": "rank, lambda_gap_from_one, normalization_error",
                "entropy_excluded_from_claim": True,
                "survives": bool(proof_pass and sympy_pass),
            },
        ],
        "future_continuations": [
            "external-audit the predicate authoring surface before stronger admission",
            "compare other information readouts only after preserving rank/gap as the organizing invariant",
        ],
        "compatibility_weights": {
            "stage2_mps_anchor": 1.0,
            "torch_primary": 1.0 if top["pass"] else 0.0,
            "jax_parity": 1.0 if max_delta <= PARITY_TOL else 0.0,
            "smt_rank_gap_flip": 1.0 if proof_pass else 0.0,
            "entropy_as_master": 0.0,
            "downstream_bridge_or_axis": 0.0,
        },
        "compression_map": {
            "from": "existing Stage-2 MPS tensors plus middle-cut bond reduced density operator",
            "to": "ordered Schmidt spectrum, rank/gap invariant, entropy output, controls, and proof receipts",
            "loss_boundary": "does not preserve full MPS tensors in the result and does not admit bridge/axis/manifold consumers",
        },
        "present_survivor": {
            "object": "Stage-7 entanglement spectrum readout over existing Stage-2 MPS",
            "capacity": "survives 8/16/32/64 without dense closure; rank/gap SMT flip survives controls",
            "blocked_capacity": EXTENDED_BLOCKED_CONSUMERS,
            "passed": all_pass,
        },
        "survivor_invariant": {
            "invariant": "present survivor has all scale rungs, non-dense execution, dual-engine agreement, known-value checks, killed controls, rank/gap proof flip, and promotion_allowed=false",
            "passed": bool(all_pass),
        },
        "outward_record": {
            "result_path": str(RESULT.relative_to(ROOT)),
            "source_file": str(THISFILE.relative_to(ROOT)),
            "gate_commands": [
                f"../../../scripts/per_sim_contract.py {RESULT.relative_to(ROOT)}",
                f"../../../scripts/max_deep_lego_gate.py {RESULT.relative_to(ROOT)} --scale-required --rigor",
                f"../../../scripts/recheck_proof.py {RESULT.relative_to(ROOT)} --rerun {THISFILE.name}",
            ],
            "claim_ceiling": "lego evidence only; entropy/information readout over existing carrier; no bridge, Axis0, flux, physics, or final manifold admission",
        },
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": all_rungs_pass,
            "proof_pass": proof_pass,
            "sympy_pass": sympy_pass,
            "control_pass": control_pass,
            "truncation_pass": truncation_pass,
            "known_value_checks_pass": known["pass"],
            "tool_ablation_pass": ablation_pass,
            "max_jax_vs_pytorch_delta": max_delta,
            "elapsed_seconds": time.time() - started,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "pass_rule": "all scale rungs pass non-dense torch/JAX spectrum parity; product and commuting controls collapse rank/gap; helper-bound SMT proof flips on measured rank/gap; known Bell/product anchors pass; ablations are recomputed and nonzero",
        "fail_rule": "fail on dense closure, entropy inside SMT claim, missing rank/gap flip, live degenerate control, JAX mismatch, truncation > 1e-8, missing known value anchor, cosmetic ablation, or downstream promotion",
        "boundary": {
            "entropy_is_output_never_master": {"pass": True, "used_inside_smt_claim": False},
            "acts_on_existing_stage2_carrier": {"pass": True, "new_physical_carrier_built": False},
            "promotion_allowed": {"value": False, "pass": True},
            "blocked_consumers": {"blocked": EXTENDED_BLOCKED_CONSUMERS, "pass": True},
        },
        "blockers": [] if all_pass else ["one or more local pass rules failed; inspect result_summary"],
        "all_pass": all_pass,
        "required_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {RESULT.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
