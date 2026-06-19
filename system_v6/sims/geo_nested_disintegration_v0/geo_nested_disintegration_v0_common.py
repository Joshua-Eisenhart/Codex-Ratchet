#!/usr/bin/env python3
"""Shared constants for geo_nested_disintegration_v0."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "geo_nested_disintegration_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
ENGINE_MODE = "julia_canon_plus_jax_diagnostic"
PYTHON = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
JULIA = "/opt/homebrew/bin/julia"
JULIA_PROJECT = "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier"

ETA1_LABEL = "pi/6"
ETA2_LABEL = "pi/4"

SEEDS = {
    "python_jax": 2026061101,
    "julia": 2026061101,
    "finite_solver_grid_N": 8,
    "finite_eta_layers": ["pi/12", "pi/4", "5*pi/12"],
    "union_shells": [ETA1_LABEL, ETA2_LABEL],
}

PIN_SPEC = (
    "geo_nested_disintegration_v0|"
    "purpose=close_CAVEAT_NESTED_SCOPE_iterated_and_multi_leaf_conditioning|"
    "base_measure=round_uniform_S3_volume|"
    "outer_foliation=S3_union_eta_T_eta|eta_range=[0,pi/2]|"
    "stage1_eta_marginal=sin(2*eta)|stage1_conditional_chart_density=1/(4*pi^2)|"
    "stage2_leaf_foliation=Hopf_phi_circles_inside_T_eta|physical_chi_period=pi|"
    "stage2_chi_marginal_physical=1/pi|stage2_phi_conditional=1/(2*pi)|"
    "double_chart_chi_marginal=1/(2*pi)|chart_double_cover=(phi,chi)~(phi+pi,chi+pi)|"
    "tower_property=eta_then_chi_then_phi_recovers_global_measure_for_cover_invariant_rows|"
    "union_shells=eta1=pi/6,eta2=pi/4|union_weights=sin(2eta_i)/sum_j_sin(2eta_j)|"
    "intersection_eta1_ne_eta2=empty|empty_conditioning_undefined=branch_mortality|"
    "order_row=eta_torus_then_phi_equals_direct_Hopf_fiber_disintegration_on_common_refinement|"
    "controls=wrong_stage2_marginal,equal_union_weights,naive_union_zero_denominator,single_leaf_limit|"
    "solver_row=finite_nested_tower_identity_with_erased_stage2_marginal_flip|"
    "engine_mode=julia_canon_plus_jax_diagnostic|pytorch_omitted=no_graph_network_autograd_claim|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

CONVENTION_PIN = {
    "coordinate_chart": "z1=cos(eta) exp(i(phi+chi)), z2=sin(eta) exp(i(phi-chi))",
    "eta_range": "[0, pi/2]",
    "volume_form_double_chart": "(1/2)*sin(2*eta) d_eta d_phi d_chi",
    "physical_torus_area": "2*pi^2*sin(2*eta)",
    "s3_volume": "2*pi^2",
    "stage1_eta_marginal": "sin(2*eta) d_eta",
    "stage1_conditional_chart_density": "1/(4*pi^2) d_phi d_chi on [0,2*pi)^2",
    "stage2_leaf_foliation": "Hopf fiber circles: phi varies at fixed physical chi class",
    "stage2_physical_chi_base": "chi modulo pi, represented by chi in [0, pi)",
    "stage2_physical_chi_marginal": "1/pi d_chi on [0, pi)",
    "stage2_fiber_conditional": "1/(2*pi) d_phi on [0, 2*pi)",
    "stage2_double_chart_chi_marginal": "1/(2*pi) d_chi on [0, 2*pi)",
    "physical_common_refinement_density": "sin(2*eta)/(2*pi^2) d_eta d_chi d_phi on eta in [0,pi/2], chi in [0,pi), phi in [0,2*pi)",
    "double_cover": "(phi, chi) ~ (phi + pi, chi + pi)",
    "finite_grid_rule": "even N chart has N^2 points and N^2/2 physical quotient classes; physical chi classes are N/2",
}

LINEAGE_CITATIONS = {
    "parent_fixed_eta_packet": [
        "system_v6/sims/geo_disintegration_machinery_v0/audit_verdict.md#CAVEAT_NESTED_SCOPE",
        "system_v6/sims/geo_disintegration_machinery_v0/results/geo_disintegration_machinery_v0_envelope_results.json#/summary",
    ],
    "geometry_program_mode4": [
        "system_v6/receipts/geometry_sim_program_canonical_20260610.md:10-14",
        "system_v6/receipts/geometry_sim_program_canonical_20260610.md:18",
    ],
    "s2_torus_area_and_cover": [
        "system_v6/sims/geo_s2_connection_flux_foliation_v0/results/geo_s2_connection_flux_foliation_v0_envelope_results.json#/receipts/S2.T",
        "system_v6/sims/geo_s2_connection_flux_foliation_v0/results/geo_s2_connection_flux_foliation_v0_envelope_results.json#/receipts/S2.K",
    ],
}

PARENT_SOURCE_PATH = "system_v6/sims/geo_disintegration_machinery_v0/geo_disintegration_machinery_v0_common.py"
PARENT_RESULT_PATH = "system_v6/sims/geo_disintegration_machinery_v0/results/geo_disintegration_machinery_v0_envelope_results.json"
PARENT_PIN_PATH = f"{PARENT_SOURCE_PATH}#/PIN_SPEC"
CALIBRATION_RECEIPT_PATH = "system_v6/receipts/audit_bar_calibration_20260610.md"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_json_sha256(obj: Any) -> str:
    return sha256_text(json.dumps(obj, sort_keys=True, separators=(",", ":")))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def parent_lineage() -> dict[str, dict[str, str]]:
    parent_result = json.loads((ROOT / PARENT_RESULT_PATH).read_text(encoding="utf-8"))
    return {
        "geo_disintegration_machinery_v0_source": {
            "path": PARENT_SOURCE_PATH,
            "sha256": file_sha256(ROOT / PARENT_SOURCE_PATH),
        },
        "geo_disintegration_machinery_v0_result": {
            "path": PARENT_RESULT_PATH,
            "sha256": file_sha256(ROOT / PARENT_RESULT_PATH),
        },
        "geo_disintegration_machinery_v0_pin": {
            "path": PARENT_PIN_PATH,
            "sha256": parent_result["pin_sha256"],
        },
        "audit_bar_calibration_20260610": {
            "path": CALIBRATION_RECEIPT_PATH,
            "sha256": file_sha256(ROOT / CALIBRATION_RECEIPT_PATH),
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
