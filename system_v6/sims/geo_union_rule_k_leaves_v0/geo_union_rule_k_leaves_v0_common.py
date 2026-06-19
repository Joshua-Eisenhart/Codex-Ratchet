#!/usr/bin/env python3
"""Shared constants for geo_union_rule_k_leaves_v0."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "geo_union_rule_k_leaves_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
ENGINE_MODE = "julia_symbolics_plus_python_sympy_smt_diagnostic"
PYTHON = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
JULIA = "/opt/homebrew/bin/julia"
JULIA_PROJECT = "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier"

COMMITTED_PARENT_SIM_ID = "geo_nested_disintegration_v0"
PARENT_SIM_DIR = ROOT / "system_v6" / "sims" / COMMITTED_PARENT_SIM_ID
PARENT_COMMON_PATH = "system_v6/sims/geo_nested_disintegration_v0/geo_nested_disintegration_v0_common.py"
PARENT_JAX_SOURCE_PATH = "system_v6/sims/geo_nested_disintegration_v0/geo_nested_disintegration_v0_jax.py"
PARENT_JULIA_SOURCE_PATH = "system_v6/sims/geo_nested_disintegration_v0/geo_nested_disintegration_v0_julia.jl"
PARENT_ENVELOPE_SOURCE_PATH = "system_v6/sims/geo_nested_disintegration_v0/geo_nested_disintegration_v0_envelope.py"
PARENT_JAX_RESULT_PATH = "system_v6/sims/geo_nested_disintegration_v0/results/geo_nested_disintegration_v0_jax_results.json"
PARENT_JULIA_RESULT_PATH = "system_v6/sims/geo_nested_disintegration_v0/results/geo_nested_disintegration_v0_julia_results.json"
PARENT_ENVELOPE_RESULT_PATH = "system_v6/sims/geo_nested_disintegration_v0/results/geo_nested_disintegration_v0_envelope_results.json"
PARENT_R3_JSON_POINTER = f"{PARENT_JAX_RESULT_PATH}#/receipts/R3_union_two_shell_conditioning"

SEEDS = {
    "python_sympy_smt": 2026061102,
    "julia_symbolics_z3": 2026061102,
    "riemann_midpoint_N": [4, 8, 16, 32, 64],
    "committed_shells": ["pi/12", "pi/6", "pi/4", "pi/3"],
    "k3_shells": ["pi/12", "pi/6", "pi/4"],
    "k4_shells": ["pi/12", "pi/6", "pi/4", "pi/3"],
}

PIN_SPEC = (
    "geo_union_rule_k_leaves_v0|"
    "purpose=extend_committed_geo_nested_disintegration_two_leaf_union_rule_to_finite_k_leaves|"
    "parent=geo_nested_disintegration_v0_read_only|"
    "base_measure=round_uniform_S3_volume|outer_foliation=S3_union_eta_T_eta|eta_range=[0,pi/2]|"
    "leaf_density=rho(eta)=sin(2*eta)|"
    "finite_k_distinct_union_rule=mu(.|union_i_T_eta_i)=sum_i_sin(2eta_i)/sum_j_sin(2eta_j)*mu(.|T_eta_i)|"
    "k2_reduction=byte_exact_R3_union_two_shell_conditioning_parent_row|"
    "concrete_shells=pi/12,pi/6,pi/4,pi/3|"
    "assoc_order_row=((1u2)u3)==(1u(2u3))==direct_3_leaf_when_group_mass_is_summed|"
    "degenerate_repeated_leaf=collapse_unique_shells_before_weighting_no_double_count|"
    "boundary_eta0=sin(0)=0_weight_vanishes|"
    "equal_weights_control=k3_cos2eta_defect_nonzero|"
    "mortality_boundary=no_finite_k_naive_conditioning_definable;continuum_all_eta_shells=S3_a.e._recovers_FREE_unconditioned_measure|"
    "solver_row=k3_weight_identity_z3_cvc5_and_julia_z3_with_erased_weight_formula_flip|"
    "engine_mode=julia_symbolics_plus_python_sympy_smt_diagnostic|"
    "pytorch_omitted=no_graph_network_autograd_claim|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

CONVENTION_PIN = {
    "coordinate_chart": "z1=cos(eta) exp(i(phi+chi)), z2=sin(eta) exp(i(phi-chi))",
    "eta_range": "[0, pi/2]",
    "s3_volume": "2*pi^2",
    "parent_stage1_eta_marginal": "sin(2*eta) d_eta",
    "leaf": "T_eta = fixed-eta Hopf torus leaf",
    "leaf_density": "rho(eta)=sin(2*eta)",
    "finite_union_band_limit": "T_eta_i replaced by [eta_i-eps, eta_i+eps], eps -> 0+",
    "finite_k_scope": "finite distinct leaves only unless a degenerate collapse row is explicitly named",
    "mortality_boundary": "finite leaf unions have S3 measure zero; all eta leaves recover S3 a.e.",
}

LINEAGE_CITATIONS = {
    "committed_two_leaf_parent": [
        PARENT_R3_JSON_POINTER,
        f"{PARENT_ENVELOPE_RESULT_PATH}#/summary/anchor_values",
    ],
    "fixed_leaf_parent": [
        "system_v6/sims/geo_disintegration_machinery_v0/results/geo_disintegration_machinery_v0_envelope_results.json#/summary/anchor_values",
    ],
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_json_sha256(obj: Any) -> str:
    return sha256_text(json.dumps(obj, sort_keys=True, separators=(",", ":")))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_parent_jax_result() -> dict[str, Any]:
    return json.loads((ROOT / PARENT_JAX_RESULT_PATH).read_text(encoding="utf-8"))


def load_parent_envelope_result() -> dict[str, Any]:
    return json.loads((ROOT / PARENT_ENVELOPE_RESULT_PATH).read_text(encoding="utf-8"))


def committed_parent_r3_row() -> dict[str, Any]:
    return load_parent_jax_result()["receipts"]["R3_union_two_shell_conditioning"]


def parent_lineage() -> dict[str, dict[str, str]]:
    parent_jax = load_parent_jax_result()
    parent_envelope = load_parent_envelope_result()
    parent_r3 = committed_parent_r3_row()
    return {
        "geo_nested_disintegration_v0_common_source": {
            "path": PARENT_COMMON_PATH,
            "sha256": file_sha256(ROOT / PARENT_COMMON_PATH),
        },
        "geo_nested_disintegration_v0_jax_source": {
            "path": PARENT_JAX_SOURCE_PATH,
            "sha256": file_sha256(ROOT / PARENT_JAX_SOURCE_PATH),
        },
        "geo_nested_disintegration_v0_julia_source": {
            "path": PARENT_JULIA_SOURCE_PATH,
            "sha256": file_sha256(ROOT / PARENT_JULIA_SOURCE_PATH),
        },
        "geo_nested_disintegration_v0_envelope_source": {
            "path": PARENT_ENVELOPE_SOURCE_PATH,
            "sha256": file_sha256(ROOT / PARENT_ENVELOPE_SOURCE_PATH),
        },
        "geo_nested_disintegration_v0_jax_result": {
            "path": PARENT_JAX_RESULT_PATH,
            "sha256": file_sha256(ROOT / PARENT_JAX_RESULT_PATH),
        },
        "geo_nested_disintegration_v0_julia_result": {
            "path": PARENT_JULIA_RESULT_PATH,
            "sha256": file_sha256(ROOT / PARENT_JULIA_RESULT_PATH),
        },
        "geo_nested_disintegration_v0_envelope_result": {
            "path": PARENT_ENVELOPE_RESULT_PATH,
            "sha256": file_sha256(ROOT / PARENT_ENVELOPE_RESULT_PATH),
        },
        "geo_nested_disintegration_v0_pin": {
            "path": f"{PARENT_ENVELOPE_RESULT_PATH}#/pin_sha256",
            "sha256": parent_envelope["pin_sha256"],
        },
        "geo_nested_disintegration_v0_R3_union_two_shell_conditioning": {
            "path": PARENT_R3_JSON_POINTER,
            "sha256": stable_json_sha256(parent_r3),
        },
        "geo_nested_disintegration_v0_jax_pin": {
            "path": f"{PARENT_JAX_RESULT_PATH}#/pin_sha256",
            "sha256": parent_jax["pin_sha256"],
        },
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
