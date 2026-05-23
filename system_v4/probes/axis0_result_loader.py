#!/usr/bin/env python3
"""
Shared Axis 0 result loader.

Axis 0 probes are transitioning from stripped legacy result names like
`axis0_phase4_results.json` to canonical `sim_axis0_*_results.json`
artifacts. Readers should prefer canonical artifacts when present while
preserving fallback to the legacy names that current packet validators may
still reference.
"""

from __future__ import annotations

import json
from pathlib import Path


AXIS0_RESULT_CANDIDATES: dict[str, tuple[str, ...]] = {
    "axis0_attractor_basin_boundary_results.json": (
        "sim_axis0_attractor_basin_boundary_results.json",
        "axis0_attractor_basin_boundary_results.json",
    ),
    "axis0_bridge_search_results.json": (
        "sim_axis0_bridge_search_results.json",
        "axis0_bridge_search_results.json",
    ),
    "axis0_chiral_deep_search_results.json": (
        "sim_axis0_chiral_deep_search_results.json",
        "axis0_chiral_deep_search_results.json",
    ),
    "axis0_coarising_stress_test_results.json": (
        "sim_axis0_coarising_stress_test_results.json",
        "axis0_coarising_stress_test_results.json",
    ),
    "axis0_cut_kernel_sweep_results.json": (
        "sim_axis0_cut_kernel_sweep_results.json",
        "axis0_cut_kernel_sweep_results.json",
    ),
    "axis0_dynamic_shell_results.json": (
        "sim_axis0_dynamic_shell_results.json",
        "axis0_dynamic_shell_results.json",
    ),
    "axis0_fe_indexed_xi_hist_results.json": (
        "sim_axis0_fe_indexed_xi_hist_results.json",
        "axis0_fe_indexed_xi_hist_results.json",
    ),
    "axis0_fep_compression_results.json": (
        "sim_axis0_fep_compression_framing_results.json",
        "axis0_fep_compression_results.json",
    ),
    "axis0_iscalar_sweep_results.json": (
        "sim_axis0_iscalar_sweep_results.json",
        "axis0_iscalar_sweep_results.json",
    ),
    "axis0_kernel_phi0_results.json": (
        "phi0_signed_kernel_bounded_point_family_results.json",
        "axis0_kernel_phi0_results.json",
    ),
    "phi0_signed_kernel_bounded_point_family_results.json": (
        "phi0_signed_kernel_bounded_point_family_results.json",
        "axis0_kernel_phi0_results.json",
    ),
    "axis0_orbit_phase_alignment_results.json": (
        "sim_axis0_orbit_phase_alignment_results.json",
        "axis0_orbit_phase_alignment_results.json",
    ),
    "axis0_phase3_results.json": (
        "sim_axis0_phase3_composite_results.json",
        "axis0_phase3_results.json",
    ),
    "axis0_phase4_results.json": (
        "sim_axis0_phase4_final_bridge_results.json",
        "axis0_phase4_results.json",
    ),
    "axis0_phase5a_results.json": (
        "sim_axis0_phase5a_marginal_preserving_results.json",
        "axis0_phase5a_results.json",
    ),
    "axis0_phase5b_results.json": (
        "sim_axis0_phase5b_stability_results.json",
        "axis0_phase5b_results.json",
    ),
    "axis0_phase5c_results.json": (
        "sim_axis0_phase5c_earned_vs_smuggled_results.json",
        "axis0_phase5c_results.json",
    ),
    "axis0_phase6_clifford_anomaly_results.json": (
        "sim_axis0_phase6_clifford_anomaly_results.json",
        "axis0_phase6_clifford_anomaly_results.json",
    ),
    "axis0_phase6_point_reference_results.json": (
        "sim_axis0_phase6_point_reference_results.json",
        "axis0_phase6_point_reference_results.json",
    ),
    "axis0_pyg_proxy_results.json": (
        "sim_axis0_pyg_proxy_results.json",
        "axis0_pyg_proxy_results.json",
    ),
    "axis0_through_shells_results.json": (
        "sim_axis0_through_shells_results.json",
        "axis0_through_shells_results.json",
    ),
}


def axis0_result_candidates(result_name: str) -> tuple[str, ...]:
    return AXIS0_RESULT_CANDIDATES.get(result_name, (result_name,))


def resolve_axis0_result_path(results_dir: Path, result_name: str) -> Path:
    candidates = [results_dir / name for name in axis0_result_candidates(result_name)]
    for path in candidates:
        if path.exists():
            return path
    rendered = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Axis 0 result artifact not found. Tried: {rendered}")


def load_axis0_result(results_dir: Path, result_name: str) -> dict:
    path = resolve_axis0_result_path(results_dir, result_name)
    return json.loads(path.read_text(encoding="utf-8"))
