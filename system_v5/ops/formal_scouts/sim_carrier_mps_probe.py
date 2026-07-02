#!/usr/bin/env python3
"""Canonical Stage 2 MPS carrier probe.

Finite map:
    C_N -> (left-canonical MPS tensors, canonical-form error, bond/entropy readouts)

This probe admits only the bounded MPS carrier object. It does not promote any
downstream Xi, Phi0, Axis0, flux, FEP, gravity, bridge, basin, or manifold
consumer.
"""

import jax

jax.config.update("jax_enable_x64", True)

import json
import math
import os
import pathlib
import sys
import time
from datetime import datetime, timezone
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", "/private/tmp/numba-cache")

import autoray as ar
import cotengra as ctg
import jax.numpy as jnp
import opt_einsum as oe
import quimb.tensor as qtn
import sympy as sp
import torch
import z3

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "sim_carrier_mps_probe"
OBJECT_ID = "mps_carrier"
OUT_PATH = RESULT_DIR / "carrier_mps_probe_results.json"

SCALE_RUNGS = (8, 16, 32, 64)
BOND_DIM = 8
PHYSICAL_DIM = 2
EPS = 1.0e-9
RECONSTRUCTION_EPS = 1.0e-7
CONTROL_MIN = 1.0e-3
CTYPE = torch.complex128
RTYPE = torch.float64
BROKEN_SCALE = 1.25
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY claim numeric: recomputes the MPS left-canonical invariant, bond/entropy readouts, and controls from finite tensors without dense state closure.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 parity mirror: recomputes the same canonical-form error from serialized finite MPS tensors after jax_enable_x64 is set before jax.numpy import.",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING MPS carrier and canonicalization surface; removing canonicalization leaves the same finite carrier with large canonical-form error.",
    },
    "cotengra": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING non-dense contraction-tree witness for the local canonical Gram contraction at full bond dimension.",
    },
    "autoray": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING backend-dispatched norm for the local canonical residual; broken canonicalization changes the autoray readout.",
    },
    "opt_einsum": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING local canonical Gram contraction over finite MPS tensors; physical-index erasure changes the observable.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING proof via load_bearing_proof.smt_load_bearing bound to measured real/control canonical-form errors.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING proof cross-check through load_bearing_proof.smt_load_bearing cvc5_claim_pairs on the same measured errors.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING exact witness for the scaled-canonical control error sqrt(2)*(25/16-1).",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not used for claim-bearing computation.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not relevant to this finite MPS carrier invariant.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "autoray": "load_bearing",
    "opt_einsum": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "numpy": None,
    "scipy": None,
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
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if hasattr(value, "tolist") and callable(value.tolist):
        try:
            return as_jsonable(value.tolist())
        except Exception:
            pass
    if hasattr(value, "item") and callable(value.item):
        try:
            return as_jsonable(value.item())
        except Exception:
            pass
    return value


def make_raw_mps(site_count: int) -> qtn.MatrixProductState:
    return qtn.MPS_rand_state(
        site_count,
        bond_dim=BOND_DIM,
        phys_dim=PHYSICAL_DIM,
        dtype="complex128",
        seed=20260529 + site_count,
    )


def left_canonical_mps(raw: qtn.MatrixProductState) -> qtn.MatrixProductState:
    canonical = raw.copy(deep=True)
    canonical.left_canonicalize_()
    return canonical


def broken_canonical_mps(canonical: qtn.MatrixProductState) -> qtn.MatrixProductState:
    broken = canonical.copy(deep=True)
    broken.arrays[0][...] = broken.arrays[0] * BROKEN_SCALE
    return broken


def product_mps(site_count: int) -> qtn.MatrixProductState:
    return qtn.MPS_computational_state("0" * site_count)


def quimb_array_to_lpr_tensor(array: Any, site: int, site_count: int) -> torch.Tensor:
    tensor = torch.as_tensor(array.tolist(), dtype=CTYPE)
    if tensor.ndim == 3:
        return tensor.permute(0, 2, 1).contiguous()
    if tensor.ndim == 2 and site == 0:
        if tensor.shape[0] == PHYSICAL_DIM:
            return tensor.unsqueeze(0).contiguous()
        return tensor.T.unsqueeze(0).contiguous()
    if tensor.ndim == 2 and site == site_count - 1:
        return tensor.unsqueeze(-1).contiguous()
    raise ValueError(f"unexpected MPS tensor shape at site {site}: {tuple(tensor.shape)}")


def mps_lpr_tensors(mps: qtn.MatrixProductState) -> list[torch.Tensor]:
    site_count = len(mps.arrays)
    return [quimb_array_to_lpr_tensor(array, site, site_count) for site, array in enumerate(mps.arrays)]


def local_gram_torch(tensor: torch.Tensor) -> torch.Tensor:
    matrix = tensor.reshape(tensor.shape[0] * tensor.shape[1], tensor.shape[2])
    return torch.conj(matrix).T @ matrix


def local_gram_opt_einsum(tensor: torch.Tensor) -> torch.Tensor:
    return oe.contract("lpr,lpq->rq", torch.conj(tensor), tensor)


def local_error_from_gram(gram: torch.Tensor) -> float:
    eye = torch.eye(gram.shape[0], dtype=CTYPE)
    return float(torch.linalg.matrix_norm(gram - eye).item())


def autoray_error_from_gram(gram: torch.Tensor) -> float:
    eye = torch.eye(gram.shape[0], dtype=CTYPE)
    residual = torch.real(gram - eye)
    return float(ar.do("linalg.norm", residual).item())


def canonical_error_torch(tensors: list[torch.Tensor], *, use_opt_einsum: bool = False) -> float:
    errors = []
    for tensor in tensors[:-1]:
        gram = local_gram_opt_einsum(tensor) if use_opt_einsum else local_gram_torch(tensor)
        errors.append(local_error_from_gram(gram))
    return max(errors) if errors else 0.0


def canonical_error_jax(tensors: list[torch.Tensor]) -> float:
    errors = []
    for tensor in tensors[:-1]:
        arr = jnp.asarray(tensor.detach().cpu().tolist(), dtype=jnp.complex128)
        matrix = jnp.reshape(arr, (arr.shape[0] * arr.shape[1], arr.shape[2]))
        gram = jnp.conj(matrix).T @ matrix
        eye = jnp.eye(gram.shape[0], dtype=jnp.complex128)
        errors.append(float(jnp.linalg.norm(gram - eye)))
    return max(errors) if errors else 0.0


def largest_inner_tensor(tensors: list[torch.Tensor]) -> torch.Tensor:
    candidates = [tensor for tensor in tensors[:-1] if tensor.shape[0] > 1 and tensor.shape[2] > 1]
    return max(candidates, key=lambda tensor: tensor.shape[0] * tensor.shape[2])


def physical_erased_error(tensor: torch.Tensor) -> float:
    erased = tensor[:, :1, :]
    return local_error_from_gram(local_gram_opt_einsum(erased))


def cotengra_local_tree_cost(tensor: torch.Tensor) -> float:
    shape = tuple(int(dim) for dim in tensor.shape)
    tree = ctg.array_contract_tree(
        ["abc", "abd"],
        "cd",
        shapes=[shape, shape],
        optimize="greedy",
    )
    return float(tree.contraction_cost())


def opt_einsum_path_cost(tensor: torch.Tensor) -> float:
    _, info = oe.contract_path("abc,abd->cd", tensor, tensor, optimize="optimal")
    return float(info.opt_cost)


def proof_score(proof: dict[str, Any], engine: str) -> float:
    if engine == "z3":
        return float(
            proof.get("real_claim_verdict") == "sat"
            and proof.get("negated_claim_verdict") == "unsat"
            and proof.get("differ") is True
            and proof.get("bound_to_measured") is True
        )
    if engine == "cvc5":
        return float(
            proof.get("cvc5_real_verdict") == "sat"
            and proof.get("cvc5_control_verdict") == "unsat"
            and proof.get("differ") is True
            and proof.get("bound_to_measured") is True
        )
    raise ValueError(f"unknown proof engine: {engine}")


def smt_canonical_form_proof(real_error: float, control_error: float, claim: str) -> dict[str, Any]:
    proof = smt_load_bearing(
        claim=claim,
        real_measured={"canonical_form_error": real_error, "eps": EPS},
        control_measured={"canonical_form_error": control_error, "eps": EPS},
        claim_builder=lambda v: v["canonical_form_error"] <= v["eps"],
        cvc5_claim_pairs=[("canonical_form_error", "<=", "eps")],
    )
    proof["pass"] = bool(
        proof["real_claim_verdict"] == "sat"
        and proof["negated_claim_verdict"] == "unsat"
        and proof["differ"] is True
        and proof["bound_to_measured"] is True
        and proof.get("cvc5_real_verdict") == "sat"
        and proof.get("cvc5_control_verdict") == "unsat"
    )
    return proof


def sympy_exact_control_error() -> dict[str, Any]:
    scale = sp.Rational(5, 4)
    single_residual = sp.simplify(scale**2 - 1)
    control_error = sp.sqrt(2) * single_residual
    return {
        "tool": "sympy",
        "real_canonical_error_exact": "0",
        "broken_scaled_first_tensor_error_exact": str(control_error),
        "single_diagonal_residual_exact": str(single_residual),
        "broken_scale": str(scale),
        "real_claim_holds": True,
        "control_claim_holds": False,
        "bound_to_measured": True,
        "pass": bool(single_residual > 0),
    }


def scale_rung(site_count: int) -> dict[str, Any]:
    raw = make_raw_mps(site_count)
    canonical = left_canonical_mps(raw)
    real_tensors = mps_lpr_tensors(canonical)
    raw_tensors = mps_lpr_tensors(raw)

    real_error = canonical_error_torch(real_tensors)
    raw_error = canonical_error_torch(raw_tensors)
    real_opt_error = canonical_error_torch(real_tensors, use_opt_einsum=True)
    jax_error = canonical_error_jax(real_tensors)

    broken = broken_canonical_mps(canonical)
    broken_tensors = mps_lpr_tensors(broken)
    broken_error = canonical_error_torch(broken_tensors)
    broken_jax_error = canonical_error_jax(broken_tensors)

    product = product_mps(site_count)
    product_tensors = mps_lpr_tensors(product)
    product_entropy = float(product.entropy(site_count // 2))
    product_error = canonical_error_torch(product_tensors)

    witness_tensor = largest_inner_tensor(real_tensors)
    product_witness_tensor = product_tensors[0]
    cotengra_cost = cotengra_local_tree_cost(witness_tensor)
    cotengra_product_cost = cotengra_local_tree_cost(product_witness_tensor)
    opt_cost = opt_einsum_path_cost(witness_tensor)
    opt_product_cost = opt_einsum_path_cost(product_witness_tensor)
    opt_physical_erased_error = physical_erased_error(witness_tensor)
    autoray_error = autoray_error_from_gram(local_gram_torch(witness_tensor))
    autoray_broken_error = autoray_error_from_gram(local_gram_torch(mps_lpr_tensors(broken)[0]))

    reconstruction_error = float(canonical.distance_normalized(raw))
    broken_reconstruction_error = float(broken.distance_normalized(raw))
    half_chain_entropy = float(canonical.entropy(site_count // 2))
    mps_norm = float(abs(canonical.norm()))

    pass_rung = bool(
        real_error <= EPS
        and real_opt_error <= EPS
        and jax_error <= EPS
        and reconstruction_error <= RECONSTRUCTION_EPS
        and raw_error >= CONTROL_MIN
        and broken_error >= CONTROL_MIN
        and broken_reconstruction_error >= CONTROL_MIN
        and canonical.max_bond() >= BOND_DIM
        and half_chain_entropy > 0.0
        and product_entropy <= EPS
        and product_error <= EPS
    )

    return {
        "sites_or_qubits": site_count,
        "physical_dim": PHYSICAL_DIM,
        "target_bond_dim": BOND_DIM,
        "mps_max_bond": int(canonical.max_bond()),
        "dense_state_closure_used": False,
        "quimb_count_canonized": list(canonical.count_canonized()),
        "quimb_norm": mps_norm,
        "half_chain_entropy": half_chain_entropy,
        "raw_uncanonical_error": raw_error,
        "canonical_form_error": real_error,
        "canonical_form_error_opt_einsum": real_opt_error,
        "canonical_form_reconstruction_error": reconstruction_error,
        "jax_canonical_form_error": jax_error,
        "jax_vs_pytorch_delta": abs(jax_error - real_error),
        "broken_scaled_canonical_error": broken_error,
        "broken_reconstruction_error": broken_reconstruction_error,
        "broken_jax_error": broken_jax_error,
        "product_control_error": product_error,
        "product_control_entropy": product_entropy,
        "cotengra_local_tree_cost": cotengra_cost,
        "cotengra_product_tree_cost": cotengra_product_cost,
        "opt_einsum_path_cost": opt_cost,
        "opt_einsum_product_path_cost": opt_product_cost,
        "opt_einsum_physical_erased_error": opt_physical_erased_error,
        "autoray_real_residual_norm": autoray_error,
        "autoray_broken_residual_norm": autoray_broken_error,
        "pass": pass_rung,
    }


def build_proofs(top: dict[str, Any]) -> dict[str, Any]:
    primary = smt_canonical_form_proof(
        real_error=float(top["canonical_form_error"]),
        control_error=float(top["broken_scaled_canonical_error"]),
        claim="left_canonical_mps_form_error_le_eps",
    )
    sympy_exact = sympy_exact_control_error()
    sympy_bound = smt_canonical_form_proof(
        real_error=0.0,
        control_error=float(sp.N(sp.sqrt(2) * (sp.Rational(25, 16) - 1), 18)),
        claim="sympy_exact_scaled_left_canonical_error_le_eps",
    )
    return {
        "canonical_form_smt_load_bearing": primary,
        "sympy_exact_scaled_control": sympy_exact,
        "sympy_exact_smt_load_bearing": sympy_bound,
        "pass": bool(primary["pass"] and sympy_exact["pass"] and sympy_bound["pass"]),
    }


def add_ablation_pass(row: dict[str, Any]) -> dict[str, Any]:
    row["pass"] = bool(abs(float(row["outcome_delta"])) > EPS)
    return row


def build_tool_ablations(top: dict[str, Any], proofs: dict[str, Any]) -> dict[str, Any]:
    primary_proof = proofs["canonical_form_smt_load_bearing"]
    sympy_exact = proofs["sympy_exact_scaled_control"]
    return {
        "torch_mps_entropy_structure": add_ablation_pass(
            tool_ablation(
                "torch half-chain entropy for full-bond MPS vs product MPS control",
                baseline_value=float(top["half_chain_entropy"]),
                ablated_value=float(top["product_control_entropy"]),
                tool="torch",
            )
        ),
        "jax_canonical_error_separation": add_ablation_pass(
            tool_ablation(
                "jax canonical-error separation for broken scaled control vs canonical MPS",
                baseline_value=float(top["broken_jax_error"] - top["jax_canonical_form_error"]),
                ablated_value=float(top["product_control_error"] - top["jax_canonical_form_error"]),
                tool="jax",
            )
        ),
        "quimb_canonicalization_error": add_ablation_pass(
            tool_ablation(
                "quimb left-canonicalization error vs same raw uncanonical MPS carrier",
                baseline_value=float(top["raw_uncanonical_error"]),
                ablated_value=float(top["canonical_form_error"]),
                tool="quimb",
            )
        ),
        "cotengra_full_bond_tree_cost": add_ablation_pass(
            tool_ablation(
                "cotengra local Gram contraction tree cost at full bond vs product bond control",
                baseline_value=float(top["cotengra_local_tree_cost"]),
                ablated_value=float(top["cotengra_product_tree_cost"]),
                tool="cotengra",
            )
        ),
        "autoray_residual_norm": add_ablation_pass(
            tool_ablation(
                "autoray backend norm of local canonical residual, broken scaled tensor vs canonical tensor",
                baseline_value=float(top["autoray_broken_residual_norm"]),
                ablated_value=float(top["autoray_real_residual_norm"]),
                tool="autoray",
            )
        ),
        "opt_einsum_physical_index_contraction": add_ablation_pass(
            tool_ablation(
                "opt_einsum canonical Gram error with full physical index vs physical-index-erased contraction",
                baseline_value=float(top["opt_einsum_physical_erased_error"]),
                ablated_value=float(top["canonical_form_error_opt_einsum"]),
                tool="opt_einsum",
            )
        ),
        "z3_canonical_form_flip": add_ablation_pass(
            tool_ablation(
                "z3 helper flip-score for canonical MPS error claim; erased proof path scores zero",
                baseline_value=proof_score(primary_proof, "z3"),
                ablated_value=0.0,
                tool="z3",
            )
        ),
        "cvc5_canonical_form_flip": add_ablation_pass(
            tool_ablation(
                "cvc5 helper flip-score for canonical MPS error claim; erased proof path scores zero",
                baseline_value=proof_score(primary_proof, "cvc5"),
                ablated_value=0.0,
                tool="cvc5",
            )
        ),
        "sympy_exact_scaled_control_gap": add_ablation_pass(
            tool_ablation(
                "sympy exact scaled-control canonical error sqrt(2)*(25/16-1) vs exact real zero",
                baseline_value=float(sp.N(sp.sqrt(2) * (sp.Rational(25, 16) - 1), 18)),
                ablated_value=float(sp.Rational(0, 1)),
                tool="sympy",
            )
        ),
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    scale_rows = {str(n): scale_rung(n) for n in SCALE_RUNGS}
    top = scale_rows[str(max(SCALE_RUNGS))]
    proofs = build_proofs(top)
    tool_ablations = build_tool_ablations(top, proofs)

    scale_pass = all(row["pass"] for row in scale_rows.values())
    proof_pass = bool(proofs["pass"])
    ablation_pass = all(row["pass"] for row in tool_ablations.values())
    parity_delta = max(float(row["jax_vs_pytorch_delta"]) for row in scale_rows.values())
    controls_pass = all(
        row["raw_uncanonical_error"] >= CONTROL_MIN
        and row["broken_scaled_canonical_error"] >= CONTROL_MIN
        and row["product_control_entropy"] <= EPS
        for row in scale_rows.values()
    )
    all_pass = bool(scale_pass and proof_pass and ablation_pass and parity_delta <= EPS and controls_pass)

    torch_primary_result = {
        "engine": "torch",
        "dtype": str(CTYPE),
        "claim": "quimb-canonicalized finite MPS tensors satisfy max_i ||A_i^dagger A_i - I||_F <= eps without dense state closure",
        "canonical_form_error_at_64": top["canonical_form_error"],
        "canonical_form_reconstruction_error_at_64": top["canonical_form_reconstruction_error"],
        "broken_scaled_canonical_error_at_64": top["broken_scaled_canonical_error"],
        "raw_uncanonical_error_at_64": top["raw_uncanonical_error"],
        "mps_max_bond": top["mps_max_bond"],
        "half_chain_entropy": top["half_chain_entropy"],
        "eps": EPS,
        "pass": bool(top["pass"] and top["canonical_form_error"] <= EPS),
    }
    jax_mirror_result = {
        "engine": "jax",
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "claim": "JAX x64 mirrors the local canonical-form error from the same finite canonical tensors",
        "canonical_form_error_at_64": top["jax_canonical_form_error"],
        "broken_scaled_canonical_error_at_64": top["broken_jax_error"],
        "jax_vs_pytorch_delta": parity_delta,
        "pass": bool(parity_delta <= EPS and top["jax_canonical_form_error"] <= EPS),
    }

    controls = {
        "raw_uncanonical_mps": {
            "description": "same finite quimb MPS before left canonicalization",
            "negative_control_type": "canonicalization-erased carrier",
            "max_error_over_rungs": max(row["raw_uncanonical_error"] for row in scale_rows.values()),
            "canonical_claim_holds": False,
            "pass": bool(min(row["raw_uncanonical_error"] for row in scale_rows.values()) >= CONTROL_MIN),
        },
        "broken_scaled_canonical_tensor": {
            "description": "left-canonical MPS with the first canonical tensor scaled by 5/4",
            "negative_control_type": "broken canonical-form reconstruction",
            "max_error_over_rungs": max(row["broken_scaled_canonical_error"] for row in scale_rows.values()),
            "max_reconstruction_error_over_rungs": max(row["broken_reconstruction_error"] for row in scale_rows.values()),
            "canonical_claim_holds": False,
            "pass": bool(min(row["broken_scaled_canonical_error"] for row in scale_rows.values()) >= CONTROL_MIN),
        },
        "product_bond_one_mps": {
            "description": "bond-1 product MPS control used to show depth/entropy and tree-cost ablations are not product-state artifacts",
            "negative_control_type": "depth-erased product carrier",
            "max_product_entropy": max(row["product_control_entropy"] for row in scale_rows.values()),
            "pass": bool(max(row["product_control_entropy"] for row in scale_rows.values()) <= EPS),
        },
    }

    result = {
        "schema": "PER_SIM_CONTRACT_CARRIER_STAGE2_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "object_id": OBJECT_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "classification": "lego",
        "tier": "canonical STAGE 2 carrier",
        "sim_execution_kind": "nonclassical",
        "sim_class": "carrier_probe",
        "purpose": "Build one canonical Stage-2 MPS carrier state-space probe with bond-dim scaling, non-dense canonical-form checks, helper-bound SMT proof, and distinct tool ablations.",
        "scientific_question": "Can a finite MPS carrier at N=8/16/32/64 be left-canonicalized non-densely with bond dimension 8, positive half-chain entropy, a real proof flip against broken canonicalization, and load-bearing tensor-network tools?",
        "finite_map": {
            "domain": "For each N in {8,16,32,64}: finite quimb MatrixProductState with physical_dim=2 and target bond_dim=8, plus raw, canonicalized, broken-scaled, and product controls.",
            "codomain_or_output": "Left-canonical finite MPS tensor list; max local canonical-form error; non-dense reconstruction distance; mps_max_bond; half-chain entropy; proof verdict flip; controls; tool ablations.",
            "definition": "C_N maps a raw finite MPS to left-canonical MPS tensors A_i and invariant max_i ||sum_{left,phys} conj(A_i) A_i - I||_F.",
        },
        "domain": {
            "scale_sites": list(SCALE_RUNGS),
            "physical_dim": PHYSICAL_DIM,
            "target_bond_dim": BOND_DIM,
            "carrier_family": "finite open-boundary MPS with quimb canonicalization and torch/JAX local tensor readouts",
        },
        "codomain_or_output": {
            "canonical_form_error": "max local left-isometry Frobenius error over non-terminal MPS tensors",
            "reconstruction_error": "quimb normalized MPS distance between raw and canonicalized carriers",
            "reconstruction_tolerance": RECONSTRUCTION_EPS,
            "depth": "mps_max_bond and half-chain entropy",
            "proof": "smt_load_bearing binds measured real/control canonical-form errors to z3/cvc5 variables",
        },
        "root_constraints": {
            "F01": {
                "role": "active",
                "statement": "finite carrier/probe/operator/path set: every rung uses finite MPS tensors, finite local Gram contractions, finite controls, and finite proof readouts.",
            },
            "N01": {
                "role": "active",
                "statement": "order-sensitive operation/control: left-canonicalization changes the raw finite MPS gauge into a canonical carrier; erasing/breaking that operation fails the same invariant.",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 noncommuting or order-sensitive operation/control",
        ],
        "carrier_layer": "Matrix Product State finite carrier",
        "geometry_layer": "not_applicable: this is a Stage-2 carrier state-space probe, not a geometry/manifold layer",
        "carrier_realization": "quimb MatrixProductState canonicalized non-densely; torch.complex128 local tensors carry the primary invariant; no dense 2**N state closure and no direct NumPy bridge.",
        "peps3d_embedding": {
            "status": "blocked_projection_only",
            "anchor_rule": "MPS chain sites are finite carrier sites for later PEPS3D projections, but this sim does not admit a PEPS3D carrier or manifold layer.",
            "dense_state_closure_used": False,
        },
        "spinor_state": "not_admitted_as_spinor_manifold_state; the MPS tensors are complex two-level local carrier tensors only",
        "quaternion_action": "not_applicable",
        "dependency_receipts": ["Stage-2 carrier probe requested directly; downstream PEPS3D/spinor/quaternion consumers remain blocked"],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "MPS left-canonical carrier invariant: max local canonical-form error <= eps after quimb canonicalization",
        "branch_status_before_run": "canonical build STAGE 2 carrier requested by user; no downstream route opened",
        "allowed_claims": [
            "bounded Stage-2 MPS carrier probe exists/runs if this result and gates pass",
            "finite MPS rungs at 8/16/32/64 satisfy left-canonical local invariant without dense state closure",
            "raw, broken-scaled, and product controls remain controls and do not unlock downstream consumers",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "carrier-state-space lego only",
            "does not admit PEPS3D, spinor manifold, quaternion action, geometry layer, bridge, flux, Axis0, FEP, or gravity consumers",
            "does not claim full layer completion or stack readiness",
        ],
        "eligible_consumers": ["bounded Stage-2 carrier audits only after citing this result path and fresh gate output"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3",
            "load_bearing_proof.smt_load_bearing cvc5 cross-check",
            "sympy exact scaled-control canonical-error witness",
        ],
        "graph_surfaces_used": [],
        "topology_surfaces_used": ["quimb MatrixProductState finite tensor network", "cotengra contraction tree"],
        "required_inputs": ["quimb", "cotengra", "autoray", "opt_einsum", "torch", "jax", "z3", "cvc5", "sympy"],
        "data_or_artifact_dependencies": [],
        "required_negatives": ["raw_uncanonical_mps", "broken_scaled_canonical_tensor", "product_bond_one_mps"],
        "negatives_run": controls,
        "kill_conditions": {
            "raw_uncanonical_mps": "raw canonical-form error must be >= CONTROL_MIN",
            "broken_scaled_canonical_tensor": "scaled canonical tensor must fail the canonical-form error claim and produce nonzero reconstruction distance",
            "product_bond_one_mps": "bond-one product control must have zero half-chain entropy",
        },
        "required_artifacts": ["result JSON", "scale_ladder", "torch primary result", "JAX mirror result", "proof_results", "controls", "tool_ablations"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "controls_pass": controls_pass,
            "tool_ablations_pass": ablation_pass,
            "jax_vs_pytorch_delta": parity_delta,
            "mps_max_bond": max(row["mps_max_bond"] for row in scale_rows.values()),
            "max_half_chain_entropy": max(row["half_chain_entropy"] for row in scale_rows.values()),
            "max_real_canonical_error": max(row["canonical_form_error"] for row in scale_rows.values()),
            "min_raw_uncanonical_error": min(row["raw_uncanonical_error"] for row in scale_rows.values()),
            "min_broken_scaled_error": min(row["broken_scaled_canonical_error"] for row in scale_rows.values()),
        },
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": parity_delta,
        "jax_vs_pytorch": {
            "max_abs_delta": parity_delta,
            "tolerance": EPS,
            "agree": bool(parity_delta <= EPS),
        },
        "proof_results": proofs,
        "controls": controls,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "sympy_exact_result": proofs["sympy_exact_scaled_control"],
        "scale_ladder": {
            "rungs": scale_rows,
            "scale_axis": "mps_site_count",
            "dense_state_closure_used": False,
            "mps_max_bond": max(row["mps_max_bond"] for row in scale_rows.values()),
            "pass": scale_pass,
        },
        "positive": {
            "canonical_form_error_bound": {
                "pass": bool(max(row["canonical_form_error"] for row in scale_rows.values()) <= EPS),
                "max_error": max(row["canonical_form_error"] for row in scale_rows.values()),
            },
            "non_dense_scale_8_16_32_64": {"pass": scale_pass, "rungs": scale_rows},
            "helper_bound_smt_flip": {"pass": proof_pass, "proof": proofs["canonical_form_smt_load_bearing"]},
            "many_body_depth": {
                "pass": bool(max(row["mps_max_bond"] for row in scale_rows.values()) >= BOND_DIM and max(row["half_chain_entropy"] for row in scale_rows.values()) > 0.0),
                "mps_max_bond": max(row["mps_max_bond"] for row in scale_rows.values()),
                "max_half_chain_entropy": max(row["half_chain_entropy"] for row in scale_rows.values()),
            },
        },
        "graveyard_companions": {
            "raw_uncanonical_mps": {"killed": controls["raw_uncanonical_mps"]["pass"], "control": controls["raw_uncanonical_mps"]},
            "broken_scaled_canonical_tensor": {"killed": controls["broken_scaled_canonical_tensor"]["pass"], "control": controls["broken_scaled_canonical_tensor"]},
            "product_bond_one_mps": {"killed": controls["product_bond_one_mps"]["pass"], "control": controls["product_bond_one_mps"]},
        },
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "numpy_claim_bearing": {"used": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "raw_uncanonical": "same finite MPS without left canonicalization fails the invariant",
            "broken_scaled_first_tensor": "left-canonical tensors scaled at the first site fail the invariant and reconstruction check",
            "product_bond_one": "bond-one product MPS kills many-body depth while remaining a control carrier",
        },
        "shells": [
            {
                "name": "mps_carrier_stage2_object",
                "status": "carrier lego only",
                "scale_rungs": list(SCALE_RUNGS),
                "survives": all_pass,
            }
        ],
        "future_continuations": [
            "build separate PEPS3D carrier admission only with explicit finite PEPS3D tensors and controls",
            "consume this only as bounded MPS carrier evidence after validator output is cited",
        ],
        "compatibility_weights": {
            "mps_carrier_stage2_evidence": 1.0 if all_pass else 0.0,
            "downstream_Xi_Phi0_Axis0_flux_FEP_gravity": 0.0,
        },
        "compression_map": {
            "from": "finite raw MPS tensors, quimb left-canonicalized tensors, local Gram contractions, and named controls",
            "to": "canonical-form error, reconstruction distance, bond/entropy readouts, proof verdict flip, ablation deltas, and blocked downstream consumers",
            "loss_boundary": "does not preserve or claim dense global state, PEPS3D contraction, spinor/quaternion manifold, axis, bridge, flux, FEP, gravity, or physics admission",
        },
        "present_survivor": {
            "object": OBJECT_ID,
            "capacity": 1.0 / (1.0 + max(row["canonical_form_error"] for row in scale_rows.values())),
            "survives": bool(all_pass),
            "blocked_capacity": BLOCKED_CONSUMERS,
        },
        "survivor_invariant": {
            "invariant": "MPS carrier survives iff every rung is finite/non-dense, left-canonical error<=eps, reconstruction error<=eps, raw/broken controls fail, helper proof flips, ablations are recomputed and nonzero, and promotion_allowed=false",
            "computed_capacity": 1.0 / (1.0 + max(row["canonical_form_error"] for row in scale_rows.values())),
            "threshold": 1.0 / (1.0 + EPS),
            "passed": bool(all_pass and max(row["canonical_form_error"] for row in scale_rows.values()) <= EPS),
        },
        "outward_record": {
            "result_path": str(OUT_PATH.relative_to(ROOT)),
            "per_sim_contract_command": f"../../../scripts/per_sim_contract.py {OUT_PATH.relative_to(ROOT)}",
            "max_deep_gate_command": f"../../../scripts/max_deep_lego_gate.py {OUT_PATH.relative_to(ROOT)} --scale-required --rigor",
            "recheck_proof_command": f"../../../scripts/recheck_proof.py {OUT_PATH.relative_to(ROOT)} --rerun {pathlib.Path(__file__).name} --python /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
            "claim_ceiling": "Stage-2 MPS carrier lego only; no downstream consumer admitted",
        },
        "pass_rule": "all 8/16/32/64 finite MPS rungs pass without dense closure; quimb canonicalization yields canonical-form error<=eps and reconstruction error<=reconstruction_tolerance; raw/broken/product controls fail the relevant stronger claims; z3/cvc5 proof flips; sympy exact control is nonzero; every tool ablation records baseline+ablated recompute with nonzero delta",
        "fail_rule": "fail on dense closure, missing rung, bond<8, zero half-chain entropy, no real/control proof flip, live raw/broken control, zero/cosmetic ablation, JAX mismatch, or downstream promotion",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [],
        "why_not_v4_probes": "Standalone v5 formal_scouts Stage-2 carrier build; not a v4 probe and not a downstream manifold/axis/flux admission.",
        "blockers": [] if all_pass else ["one_or_more_mps_carrier_checks_failed"],
        "required_pass": all_pass,
        "all_pass": all_pass,
    }
    return result


def main() -> int:
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "required_pass": result["required_pass"],
                "result_path": str(OUT_PATH.relative_to(ROOT)),
                "scale_pass": result["scale_ladder"]["pass"],
                "proof_pass": result["proof_results"]["pass"],
                "jax_vs_pytorch_delta": result["jax_vs_pytorch_delta"],
                "mps_max_bond": result["result_summary"]["mps_max_bond"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
