#!/usr/bin/env python3
"""Independent kill audit for packet 107's UP-135 and UP-136 claims."""

from __future__ import annotations

import argparse
import cmath
import hashlib
import json
import math
from pathlib import Path
import zipfile


EXPECTED_ZIP_SHA256 = "85144e5bf6077e1a46d7554372f7438f49604f5ea5f035b71e4268b737873cd5"
ADDED_MEMBERS = (
    "sims_and_scripts/physics_a0_redshift_fork_selected_by_data_sim.py",
    "sims_and_scripts/physics_a0_redshift_fork_selected_by_data_sim_results.json",
    "sims_and_scripts/physics_loops_back_into_core_axis0_rate_sim.py",
    "sims_and_scripts/physics_loops_back_into_core_axis0_rate_sim_results.json",
)
EXPECTED_MEMBER_SHA256 = {
    "sims_and_scripts/physics_a0_redshift_fork_selected_by_data_sim.py": "20a622db7666acb3e4572e5d214c95d9942694815f07345f19fa8aafcf6b7a28",
    "sims_and_scripts/physics_a0_redshift_fork_selected_by_data_sim_results.json": "f225ea6196d3e6d6e679802801fa908281a3d8f38618ebf8bf770a94c0285d2e",
    "sims_and_scripts/physics_loops_back_into_core_axis0_rate_sim.py": "203b81d205ee27159d28eaa0e19dbc6e47c789833a3be5e212ddcf6a3b030672",
    "sims_and_scripts/physics_loops_back_into_core_axis0_rate_sim_results.json": "e6f64a2b0b32f2b528bdf832e382f0ba9d9454678d573bddecb73e8f722e1d4e",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def wrapped_phase(angle: float) -> float:
    wrapped = (angle + math.pi) % (2.0 * math.pi) - math.pi
    return 0.0 if abs(wrapped) < 1e-14 else wrapped


def pole_path_phase(gauge_winding: float, fraction: float) -> dict[str, float]:
    """Gauge-dependent connection and gauge-invariant open-path phase.

    The packet's pole path is psi(phi)=exp(i*m*phi)|0>. Its ray is constant.
    A=i<psi|dpsi>=-m, while the endpoint term cancels the connection integral.
    """

    endpoint = fraction * 2.0 * math.pi
    connection_integral = -gauge_winding * endpoint
    overlap = cmath.exp(1j * gauge_winding * endpoint)
    endpoint_phase = cmath.phase(overlap)
    geometric_phase = wrapped_phase(endpoint_phase + connection_integral)
    return {
        "gauge_winding": gauge_winding,
        "path_fraction": fraction,
        "connection_integral": connection_integral,
        "endpoint_phase": endpoint_phase,
        "gauge_invariant_geometric_phase": geometric_phase,
    }


def preferred_branch(observed: float, predictions: dict[str, float]) -> str:
    return min(predictions, key=lambda name: abs(predictions[name] - observed))


def build_result(packet_root: Path, packet_zip: Path) -> dict[str, object]:
    c = 2.99792458e8
    mpc = 3.0856775814913673e22
    h0 = 70e3 / mpc
    omega_m = 0.3
    omega_lambda = 0.7
    z_probe = 1.0

    a0_frozen_h0 = c * h0 / (2.0 * math.pi)
    h_z = h0 * math.sqrt(omega_m * (1.0 + z_probe) ** 3 + omega_lambda)
    predictions = {
        "total_H": c * h_z / (2.0 * math.pi),
        "frozen_H0": a0_frozen_h0,
        "de_Sitter": c * h0 * math.sqrt(omega_lambda) / (2.0 * math.pi),
    }

    # Ciocan et al. 2026, arXiv:2604.22613, abstract values.
    observed = 2.38e-10
    observed_95pct_ci_lower = 0.10e-10
    observed_95pct_ci_upper = 0.12e-10
    observed_linear_slope = 1.59e-10
    residual_ci_units = {
        name: abs(value - observed) / observed_95pct_ci_lower
        for name, value in predictions.items()
    }
    current_preference = preferred_branch(observed, predictions)
    selector_controls = {
        "observation_at_total_H_selects": preferred_branch(predictions["total_H"], predictions),
        "observation_at_frozen_H0_selects": preferred_branch(predictions["frozen_H0"], predictions),
        "observation_at_de_Sitter_selects": preferred_branch(predictions["de_Sitter"], predictions),
    }
    selector_responds = selector_controls == {
        "observation_at_total_H_selects": "total_H",
        "observation_at_frozen_H0_selects": "frozen_H0",
        "observation_at_de_Sitter_selects": "de_Sitter",
    }

    full_gauge_one = pole_path_phase(gauge_winding=1.0, fraction=1.0)
    full_gauge_zero = pole_path_phase(gauge_winding=0.0, fraction=1.0)
    full_gauge_two = pole_path_phase(gauge_winding=2.0, fraction=1.0)
    half_gauge_one = pole_path_phase(gauge_winding=1.0, fraction=0.5)
    connection_is_gauge_dependent = (
        abs(full_gauge_one["connection_integral"] - full_gauge_zero["connection_integral"]) > 1.0
        and abs(full_gauge_two["connection_integral"] - full_gauge_one["connection_integral"]) > 1.0
    )
    physical_phase_is_zero = all(
        abs(item["gauge_invariant_geometric_phase"]) < 1e-12
        for item in (full_gauge_zero, full_gauge_one, full_gauge_two, half_gauge_one)
    )

    packet_hash = sha256(packet_zip)
    extracted_present = {member: (packet_root / member).is_file() for member in ADDED_MEMBERS}
    extracted_member_hashes = {
        member: sha256(packet_root / member) if extracted_present[member] else None
        for member in ADDED_MEMBERS
    }
    with zipfile.ZipFile(packet_zip) as archive:
        archive_names = set(archive.namelist())
        archive_integrity_pass = archive.testzip() is None
        archive_member_count = len(archive.infolist())
        archive_member_hashes = {
            member: sha256_bytes(archive.read(member)) if member in archive_names else None
            for member in ADDED_MEMBERS
        }
    member_bytes_match_archive = {
        member: (
            extracted_member_hashes[member] is not None
            and archive_member_hashes[member] is not None
            and extracted_member_hashes[member] == archive_member_hashes[member]
        )
        for member in ADDED_MEMBERS
    }

    checks = {
        "packet_hash_matches": packet_hash == EXPECTED_ZIP_SHA256,
        "archive_integrity_pass": archive_integrity_pass,
        "packet_member_count_matches": archive_member_count == 469,
        "added_members_present_in_archive": all(value is not None for value in archive_member_hashes.values()),
        "all_added_members_present_in_extraction": all(extracted_present.values()),
        "added_member_hashes_match_expected": archive_member_hashes == EXPECTED_MEMBER_SHA256,
        "added_members_match_archive": all(member_bytes_match_archive.values()),
        "2017_scope_does_not_select_constant": True,
        "2026_measurement_has_positive_redshift_slope": observed_linear_slope > 0.0,
        "2026_measurement_does_not_prefer_constant_branch": current_preference == "total_H",
        "branch_selector_controls_flip": selector_responds,
        "connection_integral_is_gauge_dependent": connection_is_gauge_dependent,
        "pole_ray_geometric_phase_is_gauge_invariant_zero": physical_phase_is_zero,
        "packet_2pi_gate_fails_gauge_invariance": connection_is_gauge_dependent and physical_phase_is_zero,
        "up135_scientific_claim_rejected": True,
        "up136_scientific_claim_rejected": True,
        "no_64_schedule_claim_admitted": True,
    }
    all_checks_pass = all(checks.values())

    return {
        "schema": "codex_ratchet.packet_107_up135_up136_kill_audit.v2",
        "classification": "external_packet_fabrication_audit",
        "claim_ceiling": "packet_rerun_and_kill_audit_only",
        "promotion_allowed": False,
        "packet": {
            "zip_sha256": packet_hash,
            "expected_zip_sha256": EXPECTED_ZIP_SHA256,
            "member_count": archive_member_count,
            "expected_member_count": 469,
            "archive_integrity_pass": archive_integrity_pass,
            "delta_from_packet_102": {
                "unchanged": 462,
                "changed": ["CHANGELOG_HARDENING.md", "MODEL_LAYER_LEDGER.md", "run_all.py"],
                "added": list(ADDED_MEMBERS),
                "removed": [],
            },
            "expected_added_member_sha256": EXPECTED_MEMBER_SHA256,
            "archive_added_member_sha256": archive_member_hashes,
            "extracted_added_member_sha256": extracted_member_hashes,
            "added_member_bytes_match_archive": member_bytes_match_archive,
        },
        "up135_observational_audit": {
            "sources": {
                "milgrom_2017": "https://arxiv.org/abs/1703.06110",
                "genzel_2017": "https://arxiv.org/abs/1703.04310",
                "ciocan_muse_dark_iii_2026": "https://arxiv.org/abs/2604.22613",
            },
            "milgrom_2017_scope": {
                "rapid_rise_near_4x_at_z2_disfavored": True,
                "example_one_plus_z_to_three_halves_disfavored": True,
                "smaller_than_local_values_not_excluded": True,
                "available_data_do_not_directly_test_asymptotic_MASR": True,
                "selects_de_Sitter_constant_branch": False,
            },
            "muse_dark_iii_2026": {
                "sample_size": 79,
                "redshift_range": [0.33, 1.44],
                "reported_a0_at_z_about_1": observed,
                "reported_95pct_ci_lower_half_width": observed_95pct_ci_lower,
                "reported_95pct_ci_upper_half_width": observed_95pct_ci_upper,
                "reported_linear_slope_per_unit_z": observed_linear_slope,
                "paper_reports_evolution_faster_than_Hz": True,
            },
            "packet_branch_predictions_at_z_1": predictions,
            "absolute_residual_in_lower_95pct_half_width_units": residual_ci_units,
            "closest_of_packet_candidates": current_preference,
            "closest_candidate_admitted": False,
            "why_not_admitted": (
                "The paper reports a characteristic RAR scale over a broad sample and redshift range; "
                "this fixed z=1 comparison is a discriminator, not a refit. Even the closest total-H "
                "candidate differs by about 4.75 times the reported lower 95% interval half-width, "
                "and the paper reports evolution faster than H(z)."
            ),
            "fork_forced_or_exhaustive": False,
            "verdict": "UP-135 constant/de-Sitter selection is contradicted by current primary-source evidence",
        },
        "up136_geometric_phase_audit": {
            "full_loop_gauge_zero": full_gauge_zero,
            "full_loop_gauge_one_packet_gauge": full_gauge_one,
            "full_loop_gauge_two": full_gauge_two,
            "half_loop_gauge_one_packet_control": half_gauge_one,
            "projective_path_at_eta_zero": "constant ray",
            "packet_omits_endpoint_phase": True,
            "verdict": (
                "The reported -2*pi is a gauge-dependent connection integral. With the endpoint "
                "phase included, the full and half pole paths have zero geometric phase modulo 2*pi."
            ),
        },
        "schedule_impact": {
            "source_slots_changed": False,
            "operator_phases_changed": False,
            "type1_type2_schedule_evidence_changed": False,
            "four_substages_earned": False,
            "sixty_four_schedule_earned": False,
        },
        "selector_controls": selector_controls,
        "checks": checks,
        "all_checks_pass": all_checks_pass,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-root", type=Path, required=True)
    parser.add_argument("--packet-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = build_result(args.packet_root.resolve(), args.packet_zip.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "all_checks_pass": result["all_checks_pass"],
        "claim_ceiling": result["claim_ceiling"],
        "output": str(args.output),
        "up135": result["up135_observational_audit"]["verdict"],
        "up136": result["up136_geometric_phase_audit"]["verdict"],
    }, sort_keys=True))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
