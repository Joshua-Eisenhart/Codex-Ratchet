#!/usr/bin/env python3
"""Shared constants for geo_disintegration_machinery_v0."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "geo_disintegration_machinery_v0"
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

SEEDS = {
    "python_jax": 2026061004,
    "julia": 2026061004,
    "finite_solver_grid_N": 8,
    "finite_eta_layers": ["pi/12", "pi/4", "5*pi/12"],
}

PIN_SPEC = (
    "geo_disintegration_machinery_v0|"
    "purpose=mode4_RATCHETED_prerequisite_conditioning_on_measure_zero_constraint_sets|"
    "base_measure=round_uniform_S3_volume|"
    "foliation=S3_union_eta_T_eta|eta_range=[0,pi/2]|"
    "hopf_torus_area=2*pi^2*sin(2*eta)|S3_volume=2*pi^2|"
    "eta_marginal_normalized=sin(2*eta)|"
    "conditional_on_T_eta=normalized_flat_torus_measure_in_phi_chi_chart|"
    "chart_double_cover=(phi,chi)~(phi+pi,chi+pi)|conditional_chart_density=1/(4*pi^2)|"
    "finite_grid_physical_points=N^2/2|"
    "controls=naive_zero_denominator,positive_eta_band,flat_marginal_wrong,null_set_modification|"
    "solver_row=finite_discretized_recovery_with_erased_controls|"
    "engine_mode=julia_canon_plus_jax_diagnostic|pytorch_omitted=no_graph_network_autograd_claim|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

CONVENTION_PIN = {
    "coordinate_chart": "z1=cos(eta) exp(i(phi+chi)), z2=sin(eta) exp(i(phi-chi))",
    "eta_range": "[0, pi/2]",
    "volume_form_double_chart": "(1/2)*sin(2*eta) d_eta d_phi d_chi",
    "physical_torus_area": "2*pi^2*sin(2*eta)",
    "s3_volume": "2*pi^2",
    "normalized_eta_marginal": "sin(2*eta) d_eta",
    "conditional_chart_density": "1/(4*pi^2) d_phi d_chi",
    "double_cover": "(phi, chi) ~ (phi + pi, chi + pi)",
    "finite_grid_rule": "even N chart has N^2 points and N^2/2 physical quotient classes",
}

LINEAGE_CITATIONS = {
    "geometry_program_mode4": [
        "system_v6/receipts/geometry_sim_program_canonical_20260610.md:10-14",
        "system_v6/receipts/geometry_sim_program_canonical_20260610.md:18",
    ],
    "s2_torus_area_and_cover": [
        "system_v6/sims/geo_s2_connection_flux_foliation_v0/results/geo_s2_connection_flux_foliation_v0_envelope_results.json#/receipts/S2.T",
        "system_v6/sims/geo_s2_connection_flux_foliation_v0/results/geo_s2_connection_flux_foliation_v0_envelope_results.json#/receipts/S2.G",
        "system_v6/sims/geo_s2_connection_flux_foliation_v0/results/geo_s2_connection_flux_foliation_v0_envelope_results.json#/receipts/S2.K",
    ],
    "s6_shell_mode_boundary": [
        "system_v6/sims/geo_s6_stacked_flows_hopf_v0/results/geo_s6_stacked_flows_hopf_v0_envelope_results.json#/claim",
        "system_v6/sims/geo_s6_stacked_flows_hopf_v0/results/geo_s6_stacked_flows_hopf_v0_envelope_results.json#/build_gates",
    ],
    "s7_finite_cover_anchor": [
        "system_v6/sims/geo_s7_discrete_refinement_v0/results/geo_s7_discrete_refinement_v0_envelope_results.json#/parity_cover",
        "system_v6/sims/geo_s7_discrete_refinement_v0/results/geo_s7_discrete_refinement_v0_envelope_results.json#/area_curve",
    ],
    "geomstats_volume_anchor": [
        "system_v6/receipts/toolset_expansion_20260610.md:60-61",
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
