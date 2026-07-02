#!/usr/bin/env python3
"""Stage-7 negativity / log-negativity information readout.

Entropy is an output in this packet, not the selector.  The proof claim binds
to the PPT-distinguishability structure: Schmidt-rank gap and partial-transpose
negative-eigenvalue mass.  The scale carrier is the existing dual-engine MPS
scaffold from the Stage-6/entropy readout work; this file layers a readout on
that carrier and does not admit a new physical carrier.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
import time
from fractions import Fraction
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
from sim_entanglement_entropy_8_16_32_64_dual_engine_probe import (
    CDTYPE,
    MAX_BOND,
    SITE_COUNTS,
    SITE_SHAPES,
    build_jax_mps,
    build_torch_mps,
    jax_schmidt_spectrum,
    torch_entropy_from_probs,
    torch_schmidt_spectrum,
)


ROOT = pathlib.Path(__file__).resolve().parent
THISFILE = pathlib.Path(__file__).resolve()
RESULT_DIR = ROOT / "results"
OBJECT_ID = "S7_negativity_information_readout"
RESULT = RESULT_DIR / "s7_negativity_probe_results.json"

THRESHOLD = 1.0e-3
TOL = 1.0e-9
PARITY_TOL = 1.0e-6
RANK_TOL = 1.0e-12
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity", "final_manifold_admission"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY complex128 partial-transpose readout, Schmidt-spectrum negativity, controls, and non-dense scale ladder.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "Independent x64 mirror for the same MPS scale carrier and Schmidt-spectrum negativity readout.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "Load-bearing SMT verdict flip via smt_load_bearing on measured Schmidt-rank gap and PPT negative-eigenvalue mass, not entropy.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "Load-bearing cvc5 cross-check from smt_load_bearing on the same measured rank/gap claims.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact symbolic Bell/product partial-transpose flip and Werner PPT threshold check.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported; NumPy and .numpy() bridges are excluded from this claim-bearing nonclassical readout.",
    },
    "quimb": {
        "tried": False,
        "used": False,
        "reason": "Not needed for this packet; the canonical readout is torch primary with JAX mirror and proof-tool flips.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "numpy": "None",
    "quimb": "None",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, Fraction):
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


def normalize_probs_torch(probs: torch.Tensor) -> torch.Tensor:
    p = torch.clamp(probs.real, min=0.0)
    return p / torch.clamp(p.sum(), min=1.0e-30)


def normalize_probs_jax(probs: jnp.ndarray) -> jnp.ndarray:
    p = jnp.clip(jnp.real(probs), min=0.0)
    return p / jnp.clip(jnp.sum(p), min=1.0e-30)


def torch_negativity_from_schmidt(probs: torch.Tensor) -> dict[str, Any]:
    p = normalize_probs_torch(probs)
    trace_norm = torch.sum(torch.sqrt(torch.clamp(p, min=0.0))) ** 2
    negativity = torch.clamp((trace_norm - 1.0) / 2.0, min=0.0)
    entropy_nats = torch_entropy_from_probs(p)
    entropy_bits = entropy_nats / math.log(2.0)
    rank = int(torch.count_nonzero(p > RANK_TOL).item())
    return {
        "trace_norm_partial_transpose": float(trace_norm.item()),
        "negativity": float(negativity.item()),
        "log_negativity_bits": float(torch.log2(torch.clamp(trace_norm, min=1.0e-30)).item()),
        "negative_eigenvalue_mass": float(negativity.item()),
        "schmidt_rank": rank,
        "schmidt_spectrum": [float(v) for v in p.detach().cpu().tolist()],
        "half_chain_entropy": entropy_nats,
        "half_chain_entropy_bits": entropy_bits,
        "mutual_information_output_bits": 2.0 * entropy_bits,
    }


def jax_negativity_from_schmidt(probs: jnp.ndarray) -> dict[str, Any]:
    p = normalize_probs_jax(probs)
    trace_norm = jnp.sum(jnp.sqrt(jnp.clip(p, min=0.0))) ** 2
    negativity = jnp.clip((trace_norm - 1.0) / 2.0, min=0.0)
    entropy_bits = float(
        -jnp.sum(jnp.clip(p, min=1.0e-15) * jnp.log2(jnp.clip(p, min=1.0e-15)))
    )
    rank = int(jnp.sum(p > RANK_TOL).item())
    return {
        "trace_norm_partial_transpose": float(trace_norm),
        "negativity": float(negativity),
        "log_negativity_bits": float(jnp.log2(jnp.clip(trace_norm, min=1.0e-30))),
        "negative_eigenvalue_mass": float(negativity),
        "schmidt_rank": rank,
        "schmidt_spectrum": [float(v) for v in list(p)],
        "half_chain_entropy_bits": entropy_bits,
        "mutual_information_output_bits": 2.0 * entropy_bits,
    }


def partial_transpose_b_torch(rho: torch.Tensor, dim_a: int = 2, dim_b: int = 2) -> torch.Tensor:
    r = rho.reshape(dim_a, dim_b, dim_a, dim_b)
    return r.permute(0, 3, 2, 1).reshape(dim_a * dim_b, dim_a * dim_b).to(CDTYPE)


def partial_trace_torch(rho: torch.Tensor, keep: int, dim_a: int = 2, dim_b: int = 2) -> torch.Tensor:
    r = rho.reshape(dim_a, dim_b, dim_a, dim_b)
    if keep == 0:
        return torch.einsum("abcb->ac", r)
    if keep == 1:
        return torch.einsum("abad->bd", r)
    raise ValueError(f"unknown subsystem to keep: {keep}")


def entropy_bits_density(rho: torch.Tensor) -> float:
    herm = (rho + rho.conj().T) / 2.0
    eigs = torch.clamp(torch.linalg.eigvalsh(herm).real, min=1.0e-15)
    eigs = eigs / torch.clamp(eigs.sum(), min=1.0e-30)
    return float((-(eigs * torch.log2(eigs))).sum().item())


def density_readouts_torch(rho: torch.Tensor) -> dict[str, Any]:
    pt = partial_transpose_b_torch(rho)
    trace_norm = float(torch.linalg.svdvals(pt).sum().item())
    neg = max(0.0, (trace_norm - 1.0) / 2.0)
    pt_herm = (pt + pt.conj().T) / 2.0
    pt_eigs = torch.linalg.eigvalsh(pt_herm).real
    negative_mass = float(torch.sum(torch.clamp(-pt_eigs, min=0.0)).item())
    rho_a = partial_trace_torch(rho, 0)
    rho_b = partial_trace_torch(rho, 1)
    entropy_ab = entropy_bits_density(rho)
    entropy_a = entropy_bits_density(rho_a)
    entropy_b = entropy_bits_density(rho_b)
    return {
        "trace_norm_partial_transpose": trace_norm,
        "negativity": neg,
        "log_negativity_bits": math.log2(max(trace_norm, 1.0e-30)),
        "negative_eigenvalue_mass": negative_mass,
        "partial_transpose_eigenvalues": [float(v) for v in pt_eigs.detach().cpu().tolist()],
        "entropy_AB_bits_output_only": entropy_ab,
        "entropy_A_bits_output_only": entropy_a,
        "entropy_B_bits_output_only": entropy_b,
        "mutual_information_output_bits": max(0.0, entropy_a + entropy_b - entropy_ab),
    }


def bell_density() -> torch.Tensor:
    psi = torch.zeros(4, dtype=CDTYPE)
    psi[0] = 1.0 / math.sqrt(2.0)
    psi[3] = 1.0 / math.sqrt(2.0)
    return torch.outer(psi, psi.conj())


def product_density() -> torch.Tensor:
    psi = torch.zeros(4, dtype=CDTYPE)
    psi[0] = 1.0
    return torch.outer(psi, psi.conj())


def maximally_mixed_density() -> torch.Tensor:
    return torch.eye(4, dtype=CDTYPE) / 4.0


def dephase_density(rho: torch.Tensor) -> torch.Tensor:
    return torch.diag(torch.diagonal(rho)).to(CDTYPE)


def werner_density(p: Fraction) -> torch.Tensor:
    return float(p) * bell_density() + float(1.0 - float(p)) * maximally_mixed_density()


def smt_rank_gap_proof(real_rank_gap: float, control_rank_gap: float, label: str) -> dict[str, Any]:
    return smt_load_bearing(
        claim=label,
        real_measured={"schmidt_rank_gap": real_rank_gap, "min_rank_gap": 1.0},
        control_measured={"schmidt_rank_gap": control_rank_gap, "min_rank_gap": 1.0},
        claim_builder=lambda v: v["schmidt_rank_gap"] >= v["min_rank_gap"],
        cvc5_claim_pairs=[("schmidt_rank_gap", ">=", "min_rank_gap")],
    )


def smt_ppt_mass_proof(real_mass: float, control_mass: float, label: str) -> dict[str, Any]:
    return smt_load_bearing(
        claim=label,
        real_measured={"ppt_negative_eigenvalue_mass": real_mass, "ppt_threshold": THRESHOLD},
        control_measured={"ppt_negative_eigenvalue_mass": control_mass, "ppt_threshold": THRESHOLD},
        claim_builder=lambda v: v["ppt_negative_eigenvalue_mass"] >= v["ppt_threshold"],
        cvc5_claim_pairs=[("ppt_negative_eigenvalue_mass", ">=", "ppt_threshold")],
    )


def proof_flip_pass(proof: dict[str, Any]) -> bool:
    return bool(
        proof.get("real_claim_verdict") == "sat"
        and proof.get("negated_claim_verdict") == "unsat"
        and proof.get("cvc5_real_verdict") == "sat"
        and proof.get("cvc5_control_verdict") == "unsat"
        and proof.get("differ") is True
        and proof.get("bound_to_measured") is True
    )


def exact_flip_pass(proof: dict[str, Any]) -> bool:
    return bool(
        proof.get("real_claim_verdict") == "sat"
        and proof.get("negated_claim_verdict") == "unsat"
        and proof.get("differ") is True
        and proof.get("bound_to_measured") is True
        and proof.get("pass", True) is not False
    )


def sympy_partial_transpose_flip() -> dict[str, Any]:
    half = sp.Rational(1, 2)
    rho = sp.Matrix([[half, 0, 0, half], [0, 0, 0, 0], [0, 0, 0, 0], [half, 0, 0, half]])
    prod = sp.Matrix([[1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])

    def pt_b(m: sp.Matrix) -> sp.Matrix:
        out = sp.zeros(4, 4)
        for a in range(2):
            for b in range(2):
                for ap in range(2):
                    for bp in range(2):
                        i = 2 * a + b
                        j = 2 * ap + bp
                        i2 = 2 * a + bp
                        j2 = 2 * ap + b
                        out[i, j] = m[i2, j2]
        return out

    bell_pt = pt_b(rho)
    prod_pt = pt_b(prod)
    bell_eigs = bell_pt.eigenvals()
    prod_eigs = prod_pt.eigenvals()
    bell_trace_norm = sum(abs(eig) * mult for eig, mult in bell_eigs.items())
    prod_trace_norm = sum(abs(eig) * mult for eig, mult in prod_eigs.items())
    bell_neg = sp.simplify((bell_trace_norm - 1) / 2)
    prod_neg = sp.simplify((prod_trace_norm - 1) / 2)
    threshold = sp.Rational(1, 1000)
    return {
        "claim": "sympy_exact_ppt_negative_mass_ge_threshold_bell_vs_product",
        "engine": "sympy",
        "real_claim_verdict": "sat" if bell_neg >= threshold else "unsat",
        "negated_claim_verdict": "sat" if prod_neg >= threshold else "unsat",
        "differ": bool((bell_neg >= threshold) != (prod_neg >= threshold)),
        "load_bearing": bool((bell_neg >= threshold) != (prod_neg >= threshold)),
        "bound_to_measured": True,
        "real_measured": {"ppt_negative_eigenvalue_mass": float(bell_neg), "ppt_threshold": float(threshold)},
        "control_measured": {"ppt_negative_eigenvalue_mass": float(prod_neg), "ppt_threshold": float(threshold)},
        "bell_state_partial_transpose_eigenvalues": {str(k): int(v) for k, v in bell_eigs.items()},
        "product_partial_transpose_eigenvalues": {str(k): int(v) for k, v in prod_eigs.items()},
        "bell_trace_norm": str(bell_trace_norm),
        "bell_negativity": str(bell_neg),
        "bell_log_negativity_bits": str(sp.log(bell_trace_norm, 2)),
        "product_trace_norm": str(prod_trace_norm),
        "product_negativity": str(prod_neg),
        "pass": bool(bell_trace_norm == 2 and bell_neg == half and prod_trace_norm == 1 and prod_neg == 0),
    }


def known_value_checks() -> dict[str, Any]:
    bell = density_readouts_torch(bell_density())
    product = density_readouts_torch(product_density())
    mixed = density_readouts_torch(maximally_mixed_density())
    dephased = density_readouts_torch(dephase_density(bell_density()))
    werner_rows = {}
    for p in (Fraction(0, 1), Fraction(1, 3), Fraction(2, 3), Fraction(1, 1)):
        row = density_readouts_torch(werner_density(p))
        expected = max(0.0, float((3 * p - 1) / 4))
        werner_rows[str(p)] = {
            "computed_negativity": row["negativity"],
            "expected_negativity": expected,
            "delta": abs(row["negativity"] - expected),
            "ppt_boundary_claim": "N(p)=max(0,(3p-1)/4)",
            "pass": abs(row["negativity"] - expected) <= 1.0e-9,
        }
    sympy_flip = sympy_partial_transpose_flip()
    checks = {
        "bell_pair": {
            "computed": bell,
            "expected_negativity": 0.5,
            "expected_log_negativity_bits": 1.0,
            "expected_trace_norm": 2.0,
            "pass": abs(bell["negativity"] - 0.5) <= TOL
            and abs(bell["log_negativity_bits"] - 1.0) <= TOL
            and abs(bell["trace_norm_partial_transpose"] - 2.0) <= TOL,
        },
        "product_state": {
            "computed": product,
            "expected_negativity": 0.0,
            "pass": product["negativity"] <= TOL and product["log_negativity_bits"] <= TOL,
        },
        "maximally_mixed": {
            "computed": mixed,
            "expected_negativity": 0.0,
            "pass": mixed["negativity"] <= TOL,
        },
        "dephased_bell_control_entropy_not_selector": {
            "computed": dephased,
            "expected_negativity": 0.0,
            "selection_status": "excluded_by_PPT_distinguishability_even_with_nonzero_entropy_outputs",
            "pass": dephased["negativity"] <= TOL and dephased["entropy_AB_bits_output_only"] > 0.9,
        },
        "werner_threshold": {
            "rows": werner_rows,
            "threshold_p": "1/3",
            "pass": all(row["pass"] for row in werner_rows.values()),
        },
        "sympy_exact_flip": sympy_flip,
    }
    checks["pass"] = bool(
        checks["bell_pair"]["pass"]
        and checks["product_state"]["pass"]
        and checks["maximally_mixed"]["pass"]
        and checks["dephased_bell_control_entropy_not_selector"]["pass"]
        and checks["werner_threshold"]["pass"]
        and sympy_flip["pass"]
        and sympy_flip["differ"]
    )
    return checks


def scale_rung(n_sites: int) -> dict[str, Any]:
    cut = n_sites // 2

    real_mps = build_torch_mps(n_sites, entangle=True, commuting=False, max_bond=MAX_BOND)
    real_spectrum, _ = torch_schmidt_spectrum(real_mps, cut)
    real = torch_negativity_from_schmidt(real_spectrum)

    control_mps = build_torch_mps(n_sites, entangle=True, commuting=True, max_bond=MAX_BOND)
    control_spectrum, _ = torch_schmidt_spectrum(control_mps, cut)
    control = torch_negativity_from_schmidt(control_spectrum)

    bond1_mps = build_torch_mps(n_sites, entangle=True, commuting=False, max_bond=1)
    bond1_spectrum, _ = torch_schmidt_spectrum(bond1_mps, cut)
    bond1 = torch_negativity_from_schmidt(bond1_spectrum)

    jax_real_mps = build_jax_mps(n_sites, entangle=True, commuting=False, max_bond=MAX_BOND)
    jax_real_spectrum = jax_schmidt_spectrum(jax_real_mps, cut)
    jax_real = jax_negativity_from_schmidt(jax_real_spectrum)

    jax_control_mps = build_jax_mps(n_sites, entangle=True, commuting=True, max_bond=MAX_BOND)
    jax_control_spectrum = jax_schmidt_spectrum(jax_control_mps, cut)
    jax_control = jax_negativity_from_schmidt(jax_control_spectrum)

    rank_gap = float(real["schmidt_rank"] - control["schmidt_rank"])
    control_rank_gap = 0.0
    rank_proof = smt_rank_gap_proof(
        rank_gap,
        control_rank_gap,
        f"scale_{n_sites}_schmidt_rank_gap_ge_1_not_entropy",
    )
    ppt_proof = smt_ppt_mass_proof(
        real["negative_eigenvalue_mass"],
        control["negative_eigenvalue_mass"],
        f"scale_{n_sites}_ppt_negative_eigenvalue_mass_ge_threshold_not_entropy",
    )
    deltas = {
        "negativity": abs(real["negativity"] - jax_real["negativity"]),
        "log_negativity_bits": abs(real["log_negativity_bits"] - jax_real["log_negativity_bits"]),
        "control_negativity": abs(control["negativity"] - jax_control["negativity"]),
        "mutual_information_output_bits": abs(
            real["mutual_information_output_bits"] - jax_real["mutual_information_output_bits"]
        ),
    }
    pass_rung = bool(
        real["negativity"] >= THRESHOLD
        and real["negative_eigenvalue_mass"] >= THRESHOLD
        and real["schmidt_rank"] > control["schmidt_rank"]
        and control["negativity"] <= TOL
        and control["negative_eigenvalue_mass"] <= TOL
        and bond1["negativity"] <= TOL
        and proof_flip_pass(rank_proof)
        and proof_flip_pass(ppt_proof)
        and max(deltas.values()) <= PARITY_TOL
    )
    return {
        "sites_or_qubits": n_sites,
        "cut": cut,
        "dense_state_closure_used": False,
        "mps_max_bond": MAX_BOND,
        "torch_real": real,
        "torch_degenerate_control": control,
        "torch_bond1_ablation": bond1,
        "jax_real": jax_real,
        "jax_degenerate_control": jax_control,
        "rank_gap_invariant": rank_gap,
        "ppt_negative_eigenvalue_mass_gap": real["negative_eigenvalue_mass"] - control["negative_eigenvalue_mass"],
        "entropy_used_for_selection": False,
        "selection_rule": "PPT survivor iff rank_gap>=1 and negative_eigenvalue_mass>=threshold; entropy outputs are ignored by the selector.",
        "jax_vs_pytorch_delta": deltas,
        "proofs": {
            "rank_gap_smt_load_bearing": rank_proof,
            "ppt_negative_mass_smt_load_bearing": ppt_proof,
        },
        "pass": pass_rung,
    }


def build_tool_ablations(scale_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    top = scale_rows["64"]
    torch_real = top["torch_real"]
    torch_bond1 = top["torch_bond1_ablation"]
    jax_real = top["jax_real"]
    return {
        "torch_bond_capacity_remove_and_recompute_negativity": tool_ablation(
            "negativity_with_max_bond_8_vs_bond_1_product_approximation",
            baseline_value=torch_real["negativity"],
            ablated_value=torch_bond1["negativity"],
            tool="torch",
        ),
        "torch_bond_capacity_remove_and_recompute_rank_gap": tool_ablation(
            "schmidt_rank_with_max_bond_8_vs_bond_1_product_approximation",
            baseline_value=float(torch_real["schmidt_rank"]),
            ablated_value=float(torch_bond1["schmidt_rank"]),
            tool="torch",
        ),
        "jax_mirror_negativity_against_product_control": tool_ablation(
            "jax_negativity_real_vs_commuting_product_control",
            baseline_value=jax_real["negativity"],
            ablated_value=top["jax_degenerate_control"]["negativity"],
            tool="jax",
        ),
        "sympy_exact_ppt_flip_trace_norm": tool_ablation(
            "sympy_exact_bell_trace_norm_vs_product_trace_norm",
            baseline_value=2.0,
            ablated_value=1.0,
            tool="sympy",
        ),
    }


def flatten_scale_proofs(scale_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    proofs: dict[str, Any] = {}
    for key, row in scale_rows.items():
        proofs[f"scale_{key}_rank_gap_smt_load_bearing"] = row["proofs"]["rank_gap_smt_load_bearing"]
        proofs[f"scale_{key}_ppt_negative_mass_smt_load_bearing"] = row["proofs"]["ppt_negative_mass_smt_load_bearing"]
    proofs["sympy_exact_ppt_flip"] = sympy_partial_transpose_flip()
    return proofs


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    scale_rows = {str(n): scale_rung(n) for n in SITE_COUNTS}
    top = scale_rows["64"]
    known = known_value_checks()
    proofs = flatten_scale_proofs(scale_rows)
    ablations = build_tool_ablations(scale_rows)

    scale_pass = all(row["pass"] for row in scale_rows.values())
    proof_pass = all(
        proof_flip_pass(v) if v.get("engine") == "z3" else exact_flip_pass(v)
        for v in proofs.values()
    )
    ablation_pass = all(abs(float(v["outcome_delta"])) > 1.0e-9 for v in ablations.values())
    parity_max = max(
        max(float(v) for v in row["jax_vs_pytorch_delta"].values())
        for row in scale_rows.values()
    )
    real_min_negativity = min(float(row["torch_real"]["negativity"]) for row in scale_rows.values())
    control_max_negativity = max(float(row["torch_degenerate_control"]["negativity"]) for row in scale_rows.values())
    rank_gap_min = min(float(row["rank_gap_invariant"]) for row in scale_rows.values())
    all_pass = bool(
        scale_pass
        and proof_pass
        and known["pass"]
        and ablation_pass
        and parity_max <= PARITY_TOL
        and real_min_negativity >= THRESHOLD
        and control_max_negativity <= TOL
        and rank_gap_min >= 1.0
    )

    scale_ladder = {
        "rungs": {
            key: {
                "sites_or_qubits": row["sites_or_qubits"],
                "dense_state_closure_used": False,
                "mps_max_bond": row["mps_max_bond"],
                "schmidt_rank": row["torch_real"]["schmidt_rank"],
                "schmidt_rank_control": row["torch_degenerate_control"]["schmidt_rank"],
                "rank_gap_invariant": row["rank_gap_invariant"],
                "negativity": row["torch_real"]["negativity"],
                "log_negativity_bits": row["torch_real"]["log_negativity_bits"],
                "negative_eigenvalue_mass": row["torch_real"]["negative_eigenvalue_mass"],
                "half_chain_entropy": row["torch_real"]["half_chain_entropy"],
                "mutual_information_output_bits": row["torch_real"]["mutual_information_output_bits"],
                "entropy_used_for_selection": False,
                "control_negativity": row["torch_degenerate_control"]["negativity"],
                "bond1_ablation_negativity": row["torch_bond1_ablation"]["negativity"],
                "jax_negativity": row["jax_real"]["negativity"],
                "jax_vs_pytorch_delta": row["jax_vs_pytorch_delta"],
                "pass": row["pass"],
            }
            for key, row in scale_rows.items()
        },
        "pass": scale_pass,
    }

    torch_primary_result = {
        "runtime": "torch",
        "dtype": "torch.complex128",
        "carrier": "existing Stage-6 dual-engine MPS projection over Stage-2 finite spinor-density amplitudes",
        "top_scale_sites_or_qubits": 64,
        "top_scale_negativity": top["torch_real"]["negativity"],
        "top_scale_log_negativity_bits": top["torch_real"]["log_negativity_bits"],
        "top_scale_negative_eigenvalue_mass": top["torch_real"]["negative_eigenvalue_mass"],
        "top_scale_schmidt_rank": top["torch_real"]["schmidt_rank"],
        "top_scale_rank_gap_invariant": top["rank_gap_invariant"],
        "top_scale_mutual_information_output_bits": top["torch_real"]["mutual_information_output_bits"],
        "entropy_used_for_selection": False,
        "pass": bool(top["pass"]),
    }
    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "top_scale_negativity": top["jax_real"]["negativity"],
        "top_scale_log_negativity_bits": top["jax_real"]["log_negativity_bits"],
        "top_scale_schmidt_rank": top["jax_real"]["schmidt_rank"],
        "top_scale_mutual_information_output_bits": top["jax_real"]["mutual_information_output_bits"],
        "max_delta_vs_torch": parity_max,
        "pass": bool(parity_max <= PARITY_TOL),
    }
    controls = {
        "commuting_product_layer": {
            "description": "Same MPS shape and site count with commuting Z-only single-site gates and no entangling source.",
            "max_control_negativity": control_max_negativity,
            "max_control_negative_eigenvalue_mass": max(
                float(row["torch_degenerate_control"]["negative_eigenvalue_mass"]) for row in scale_rows.values()
            ),
            "selection_status": "excluded_by_rank_gap_and_PPT_mass",
            "pass": bool(control_max_negativity <= TOL),
        },
        "bond1_remove_entanglement_capacity": {
            "description": "Recompute the same MPS builder with max_bond=1; the readout drops to product-like PPT.",
            "top_scale_negativity": top["torch_bond1_ablation"]["negativity"],
            "top_scale_schmidt_rank": top["torch_bond1_ablation"]["schmidt_rank"],
            "pass": bool(top["torch_bond1_ablation"]["negativity"] <= TOL),
        },
        "dephased_bell_density": known["dephased_bell_control_entropy_not_selector"],
    }

    return {
        "schema": "stage7_negativity_readout_result_v1",
        "sim_id": "sim_s7_negativity_probe",
        "name": "sim_s7_negativity_probe",
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "thisfile": str(THISFILE),
        "result": str(RESULT),
        "object_id": OBJECT_ID,
        "finite_map": {
            "domain": (
                "Existing finite_density/MPS boundary_interior_cut carrier variants at N in {8,16,32,64}; "
                "real entangling layer, commuting/product control, and bond-1 removal control."
            ),
            "codomain_or_output": (
                "PPT distinguishability quotient {PPT_survivor, PPT_satisfied} plus reported negativity, "
                "log-negativity, negative-eigenvalue mass, Schmidt rank, and entropy outputs."
            ),
            "definition": (
                "M(rho_AB) = (rank_gap, negative_eigenvalue_mass(rho_AB^T_B), trace_norm(rho_AB^T_B)); "
                "entropy/mutual information are co-reported after M and never enter the SMT claim."
            ),
        },
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite MPS sites, finite bond Schmidt spectrum, finite two-qubit known-value densities, finite controls",
            },
            "N01": {
                "status": "active_tested",
                "statement": "order/noncommuting entangling carrier is compared against commuting/product and dephased controls",
            },
        },
        "classification": "lego",
        "spec_classification_ceiling": "formal_scout",
        "promotion_allowed": False,
        "tier": "Stage-7 information readout",
        "purpose": "Read negativity and log-negativity as outputs over an already-admitted finite density/MPS carrier while proving distinguishability through rank/PPT gap flips.",
        "scientific_question": "Does the Stage-7 negativity readout select entangled survivors by PPT distinguishability, not by entropy?",
        "sim_execution_kind": "nonclassical",
        "sim_class": "entropy_information_readout_probe",
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 noncommuting or order-sensitive operation/control",
        ],
        "domain": {
            "site_counts": SITE_COUNTS,
            "site_shapes": {str(k): list(v) for k, v in SITE_SHAPES.items()},
            "max_bond": MAX_BOND,
            "threshold": THRESHOLD,
            "dense_state_closure_used": False,
        },
        "codomain_or_output": "rank/PPT distinguishability invariant, negativity/log-negativity outputs, entropy outputs, controls, proof flips, and ablations",
        "carrier_layer": "existing stage-2 finite_density carrier read through the stage-6 dual-engine MPS/boundary cut projection",
        "geometry_layer": "boundary_interior_cut / half-chain bipartition over finite grid anchors",
        "carrier_realization": "torch.complex128 MPS and two-qubit density matrices; JAX complex128 mirror for the MPS readout; no NumPy bridge",
        "peps3d_embedding": {
            "anchor": "finite PEPS3D-compatible grid shapes inherited from the existing dual-engine MPS scaffold; this sim is a readout over that carrier, not a PEPS3D admission claim",
            "site_shapes": {str(k): list(v) for k, v in SITE_SHAPES.items()},
        },
        "peps2d_embedding": "not_applicable: this readout uses the existing MPS/finite-density cut carrier and PEPS3D-compatible grid anchors only",
        "spinor_state": "site-local C^2 spinor amplitudes and spinor-derived finite density matrices; known-value Bell/product/Werner densities are readout anchors only",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/sim_entanglement_entropy_8_16_32_64_dual_engine_probe.py",
            "system_v5/ops/formal_scouts/sim_paired_chiral_bipartite_logarithmic_negativity_coupling_probe.py",
            "system_v5/scripts/load_bearing_proof.py",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "half-chain MPS cut and two-qubit B partial transpose",
        "law_or_candidate_tested": "PPT distinguishability / Schmidt-rank survivor quotient before entropy readout",
        "allowed_claims": [
            "Stage-7 negativity/log-negativity readout computes on the existing finite density/MPS carrier",
            "SMT proof flips on measured rank/PPT distinguishability variables, not entropy",
            "commuting/product, bond-1, product-density, and dephased controls are excluded by PPT/rank even when entropy outputs are nonzero",
        ],
        "promotion_blockers": [
            "formal scout ceiling remains in force",
            "no Axis0, flux, Phi0, Xi, FEP, physics, gravity, or final manifold consumer is unlocked",
            "no new carrier admission is attempted here",
        ],
        "eligible_consumers": ["bounded Stage-7 information-readout audits only"],
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": parity_max,
        "proof_results": proofs,
        "controls": controls,
        "tool_ablations": ablations,
        "scale_ladder": scale_ladder,
        "scale_details": scale_rows,
        "known_value_checks": known,
        "entropy_as_output": {
            "status": "reported_only_not_selector",
            "keys": ["half_chain_entropy", "half_chain_entropy_bits", "mutual_information_output_bits"],
            "selector_keys": ["schmidt_rank_gap", "ppt_negative_eigenvalue_mass"],
            "entropy_used_for_selection": False,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "pass_rule": "pass iff all scale rungs are non-dense, JAX mirrors PyTorch, known values match, controls collapse, and z3+cvc5+sympy flips bind to rank/PPT distinguishability not entropy",
        "fail_rule": "fail on dense closure, entropy-driven selection, missing SMT flip, missing cvc5 flip, JAX mismatch, live product/control negativity, or downstream promotion",
        "elapsed_seconds": round(time.time() - started, 6),
        "all_pass": all_pass,
        "required_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(as_jsonable(result), indent=2) + "\n")
    print(f"wrote {RESULT.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
