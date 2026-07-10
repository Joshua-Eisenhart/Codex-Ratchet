#!/usr/bin/env python3
"""Fail-closed validator for the packet 107 kill-audit result."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
from typing import Callable
import zipfile


SCHEMA = "codex_ratchet.packet_107_up135_up136_kill_audit.v2"
EXPECTED_ZIP_SHA256 = "85144e5bf6077e1a46d7554372f7438f49604f5ea5f035b71e4268b737873cd5"
EXPECTED_MEMBER_SHA256 = {
    "sims_and_scripts/physics_a0_redshift_fork_selected_by_data_sim.py": "20a622db7666acb3e4572e5d214c95d9942694815f07345f19fa8aafcf6b7a28",
    "sims_and_scripts/physics_a0_redshift_fork_selected_by_data_sim_results.json": "f225ea6196d3e6d6e679802801fa908281a3d8f38618ebf8bf770a94c0285d2e",
    "sims_and_scripts/physics_loops_back_into_core_axis0_rate_sim.py": "203b81d205ee27159d28eaa0e19dbc6e47c789833a3be5e212ddcf6a3b030672",
    "sims_and_scripts/physics_loops_back_into_core_axis0_rate_sim_results.json": "e6f64a2b0b32f2b528bdf832e382f0ba9d9454678d573bddecb73e8f722e1d4e",
}
EXPECTED_SOURCES = {
    "milgrom_2017": "https://arxiv.org/abs/1703.06110",
    "genzel_2017": "https://arxiv.org/abs/1703.04310",
    "ciocan_muse_dark_iii_2026": "https://arxiv.org/abs/2604.22613",
}
EXPECTED_SCOPE = {
    "rapid_rise_near_4x_at_z2_disfavored": True,
    "example_one_plus_z_to_three_halves_disfavored": True,
    "smaller_than_local_values_not_excluded": True,
    "available_data_do_not_directly_test_asymptotic_MASR": True,
    "selects_de_Sitter_constant_branch": False,
}
EXPECTED_SELECTOR_CONTROLS = {
    "observation_at_total_H_selects": "total_H",
    "observation_at_frozen_H0_selects": "frozen_H0",
    "observation_at_de_Sitter_selects": "de_Sitter",
}
EXPECTED_SCHEDULE_IMPACT = {
    "source_slots_changed": False,
    "operator_phases_changed": False,
    "type1_type2_schedule_evidence_changed": False,
    "four_substages_earned": False,
    "sixty_four_schedule_earned": False,
}
EXPECTED_CHECK_KEYS = {
    "packet_hash_matches",
    "archive_integrity_pass",
    "packet_member_count_matches",
    "added_members_present_in_archive",
    "all_added_members_present_in_extraction",
    "added_member_hashes_match_expected",
    "added_members_match_archive",
    "2017_scope_does_not_select_constant",
    "2026_measurement_has_positive_redshift_slope",
    "2026_measurement_does_not_prefer_constant_branch",
    "branch_selector_controls_flip",
    "connection_integral_is_gauge_dependent",
    "pole_ray_geometric_phase_is_gauge_invariant_zero",
    "packet_2pi_gate_fails_gauge_invariance",
    "up135_scientific_claim_rejected",
    "up136_scientific_claim_rejected",
    "no_64_schedule_claim_admitted",
}
EXPECTED_UP135_VERDICT = "UP-135 constant/de-Sitter selection is contradicted by current primary-source evidence"
EXPECTED_UP136_VERDICT = (
    "The reported -2*pi is a gauge-dependent connection integral. With the endpoint "
    "phase included, the full and half pole paths have zero geometric phase modulo 2*pi."
)
EXPECTED_WHY_NOT_ADMITTED = (
    "The paper reports a characteristic RAR scale over a broad sample and redshift range; "
    "this fixed z=1 comparison is a discriminator, not a refit. Even the closest total-H "
    "candidate differs by about 4.75 times the reported lower 95% interval half-width, "
    "and the paper reports evolution faster than H(z)."
)
TOP_LEVEL_KEYS = {
    "schema",
    "classification",
    "claim_ceiling",
    "promotion_allowed",
    "packet",
    "up135_observational_audit",
    "up136_geometric_phase_audit",
    "schedule_impact",
    "selector_controls",
    "checks",
    "all_checks_pass",
}
PACKET_KEYS = {
    "zip_sha256",
    "expected_zip_sha256",
    "member_count",
    "expected_member_count",
    "archive_integrity_pass",
    "delta_from_packet_102",
    "expected_added_member_sha256",
    "archive_added_member_sha256",
    "extracted_added_member_sha256",
    "added_member_bytes_match_archive",
}
UP135_KEYS = {
    "sources",
    "milgrom_2017_scope",
    "muse_dark_iii_2026",
    "packet_branch_predictions_at_z_1",
    "absolute_residual_in_lower_95pct_half_width_units",
    "closest_of_packet_candidates",
    "closest_candidate_admitted",
    "why_not_admitted",
    "fork_forced_or_exhaustive",
    "verdict",
}
MUSE_KEYS = {
    "sample_size",
    "redshift_range",
    "reported_a0_at_z_about_1",
    "reported_95pct_ci_lower_half_width",
    "reported_95pct_ci_upper_half_width",
    "reported_linear_slope_per_unit_z",
    "paper_reports_evolution_faster_than_Hz",
}
UP136_KEYS = {
    "full_loop_gauge_zero",
    "full_loop_gauge_one_packet_gauge",
    "full_loop_gauge_two",
    "half_loop_gauge_one_packet_control",
    "projective_path_at_eta_zero",
    "packet_omits_endpoint_phase",
    "verdict",
}


def finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def close_number(value: object, expected: float, tolerance: float = 1e-12) -> bool:
    return finite_number(value) and math.isclose(
        float(value), expected, rel_tol=1e-12, abs_tol=tolerance
    )


def exact_bool_mapping(value: object, expected: dict[str, bool]) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == set(expected)
        and all(value[key] is expected[key] for key in expected)
    )


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strict_json_loads(text: str) -> dict[str, object]:
    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    parsed = json.loads(text, object_pairs_hook=reject_duplicate_keys)
    if not isinstance(parsed, dict):
        raise ValueError("top-level JSON value must be an object")
    return parsed


def expected_predictions() -> dict[str, float]:
    c = 2.99792458e8
    mpc = 3.0856775814913673e22
    h0 = 70e3 / mpc
    omega_m = 0.3
    omega_lambda = 0.7
    z_probe = 1.0
    h_z = h0 * math.sqrt(omega_m * (1.0 + z_probe) ** 3 + omega_lambda)
    return {
        "total_H": c * h_z / (2.0 * math.pi),
        "frozen_H0": c * h0 / (2.0 * math.pi),
        "de_Sitter": c * h0 * math.sqrt(omega_lambda) / (2.0 * math.pi),
    }


def validate_packet(packet: object, errors: list[str]) -> None:
    if not isinstance(packet, dict):
        errors.append("missing packet provenance")
        return
    if set(packet) != PACKET_KEYS:
        errors.append("packet provenance fields are not key-closed")
    if packet.get("zip_sha256") != EXPECTED_ZIP_SHA256:
        errors.append("packet ZIP hash mismatch")
    if packet.get("expected_zip_sha256") != EXPECTED_ZIP_SHA256:
        errors.append("expected packet ZIP hash mismatch")
    if type(packet.get("member_count")) is not int or packet.get("member_count") != 469:
        errors.append("packet member count mismatch")
    if type(packet.get("expected_member_count")) is not int or packet.get("expected_member_count") != 469:
        errors.append("packet member count mismatch")
    if packet.get("archive_integrity_pass") is not True:
        errors.append("archive integrity was not established")

    delta = packet.get("delta_from_packet_102")
    expected_delta = {
        "unchanged": 462,
        "changed": ["CHANGELOG_HARDENING.md", "MODEL_LAYER_LEDGER.md", "run_all.py"],
        "added": list(EXPECTED_MEMBER_SHA256),
        "removed": [],
    }
    if not isinstance(delta, dict) or set(delta) != set(expected_delta):
        errors.append("packet-102 delta fields mismatch")
    elif (
        type(delta.get("unchanged")) is not int
        or delta.get("unchanged") != 462
        or delta.get("changed") != expected_delta["changed"]
        or delta.get("added") != expected_delta["added"]
        or delta.get("removed") != []
    ):
        errors.append("packet-102 delta mismatch")

    expected_hashes = packet.get("expected_added_member_sha256")
    archive_hashes = packet.get("archive_added_member_sha256")
    extracted_hashes = packet.get("extracted_added_member_sha256")
    bindings = packet.get("added_member_bytes_match_archive")
    if expected_hashes != EXPECTED_MEMBER_SHA256:
        errors.append("expected member hashes are incomplete or changed")
    if archive_hashes != EXPECTED_MEMBER_SHA256:
        errors.append("archive member hashes do not match the locked packet")
    if extracted_hashes != EXPECTED_MEMBER_SHA256:
        errors.append("extracted member hashes do not match the locked packet")
    if not exact_bool_mapping(bindings, {member: True for member in EXPECTED_MEMBER_SHA256}):
        errors.append("extracted members are not byte-bound to the ZIP")


def validate_live_provenance(
    result: dict[str, object],
    packet_root: Path,
    packet_zip: Path,
    errors: list[str],
) -> None:
    if not packet_zip.is_file():
        errors.append("live packet ZIP is missing")
        return
    if not packet_root.is_dir():
        errors.append("live packet extraction root is missing")
        return
    if sha256_path(packet_zip) != EXPECTED_ZIP_SHA256:
        errors.append("live packet ZIP hash mismatch")
        return

    try:
        with zipfile.ZipFile(packet_zip) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                errors.append("live packet ZIP has duplicate member names")
            if len(infos) != 469:
                errors.append("live packet ZIP member count mismatch")
            if archive.testzip() is not None:
                errors.append("live packet ZIP integrity check failed")
            for info in infos:
                name = PurePosixPath(info.filename)
                if name.is_absolute() or ".." in name.parts:
                    errors.append("live packet ZIP contains an unsafe member name")
                    break
            live_archive_hashes: dict[str, str] = {}
            for member, expected_hash in EXPECTED_MEMBER_SHA256.items():
                try:
                    info = archive.getinfo(member)
                    if info.is_dir():
                        errors.append(f"live packet member is not a regular file: {member}")
                        continue
                    member_hash = hashlib.sha256(archive.read(info)).hexdigest()
                    live_archive_hashes[member] = member_hash
                    if member_hash != expected_hash:
                        errors.append(f"live archive member hash mismatch: {member}")
                except KeyError:
                    errors.append(f"live packet ZIP member is missing: {member}")
    except zipfile.BadZipFile:
        errors.append("live packet is not a valid ZIP")
        return

    live_extracted_hashes: dict[str, str] = {}
    for member, expected_hash in EXPECTED_MEMBER_SHA256.items():
        extracted_path = packet_root / member
        if not extracted_path.is_file():
            errors.append(f"live extracted packet member is missing: {member}")
            continue
        extracted_hash = sha256_path(extracted_path)
        live_extracted_hashes[member] = extracted_hash
        if extracted_hash != expected_hash:
            errors.append(f"live extracted member hash mismatch: {member}")

    packet = result.get("packet")
    if isinstance(packet, dict):
        if packet.get("archive_added_member_sha256") != live_archive_hashes:
            errors.append("result archive hashes do not match live ZIP")
        if packet.get("extracted_added_member_sha256") != live_extracted_hashes:
            errors.append("result extraction hashes do not match live files")


def validate_up135(up135: object, errors: list[str]) -> None:
    if not isinstance(up135, dict):
        errors.append("missing UP-135 audit")
        return
    if set(up135) != UP135_KEYS:
        errors.append("UP-135 audit fields are not key-closed")
    if up135.get("sources") != EXPECTED_SOURCES:
        errors.append("UP-135 source set mismatch")
    if not exact_bool_mapping(up135.get("milgrom_2017_scope"), EXPECTED_SCOPE):
        errors.append("2017 source scope missing or overpromoted")

    muse = up135.get("muse_dark_iii_2026")
    if not isinstance(muse, dict):
        errors.append("missing 2026 observation record")
    else:
        if set(muse) != MUSE_KEYS:
            errors.append("2026 observation fields are not key-closed")
        redshift_range = muse.get("redshift_range")
        if (
            type(muse.get("sample_size")) is not int
            or muse.get("sample_size") != 79
            or not isinstance(redshift_range, list)
            or len(redshift_range) != 2
            or not close_number(redshift_range[0], 0.33)
            or not close_number(redshift_range[1], 1.44)
            or muse.get("paper_reports_evolution_faster_than_Hz") is not True
        ):
            errors.append("2026 observation metadata mismatch")
        numeric_fields = {
            "reported_a0_at_z_about_1": 2.38e-10,
            "reported_95pct_ci_lower_half_width": 0.10e-10,
            "reported_95pct_ci_upper_half_width": 0.12e-10,
            "reported_linear_slope_per_unit_z": 1.59e-10,
        }
        if any(not close_number(muse.get(key), value, 1e-22) for key, value in numeric_fields.items()):
            errors.append("2026 observation values mismatch or are non-finite")

    predictions = up135.get("packet_branch_predictions_at_z_1")
    expected = expected_predictions()
    if not isinstance(predictions, dict) or set(predictions) != set(expected):
        errors.append("branch predictions are missing")
    else:
        if any(not close_number(predictions[name], value, 1e-22) for name, value in expected.items()):
            errors.append("branch predictions changed or are non-finite")
        if not (predictions["total_H"] > predictions["frozen_H0"] > predictions["de_Sitter"]):
            errors.append("branch prediction ordering invalid")

    residuals = up135.get("absolute_residual_in_lower_95pct_half_width_units")
    expected_residuals = {
        name: abs(value - 2.38e-10) / 0.10e-10 for name, value in expected.items()
    }
    if not isinstance(residuals, dict) or set(residuals) != set(expected_residuals):
        errors.append("branch residuals are missing")
    elif any(not close_number(residuals[name], value) for name, value in expected_residuals.items()):
        errors.append("branch residuals changed or are non-finite")

    if up135.get("closest_of_packet_candidates") != "total_H":
        errors.append("current-data candidate ordering changed")
    if up135.get("closest_candidate_admitted") is not False:
        errors.append("closest candidate must not be admitted")
    if up135.get("fork_forced_or_exhaustive") is not False:
        errors.append("packet fork must remain non-exhaustive")
    if up135.get("why_not_admitted") != EXPECTED_WHY_NOT_ADMITTED:
        errors.append("UP-135 non-admission rationale mismatch")
    if up135.get("verdict") != EXPECTED_UP135_VERDICT:
        errors.append("UP-135 rejection verdict missing")


def validate_phase_path(
    path: object,
    label: str,
    winding: float,
    fraction: float,
    errors: list[str],
) -> None:
    if not isinstance(path, dict):
        errors.append(f"missing geometric-phase path: {label}")
        return
    required = {
        "gauge_winding",
        "path_fraction",
        "connection_integral",
        "endpoint_phase",
        "gauge_invariant_geometric_phase",
    }
    if set(path) != required:
        errors.append(f"geometric-phase path fields mismatch: {label}")
        return
    endpoint = fraction * 2.0 * math.pi
    expected_connection = -winding * endpoint
    expected_endpoint_phase = math.atan2(math.sin(winding * endpoint), math.cos(winding * endpoint))
    expected_values = {
        "gauge_winding": winding,
        "path_fraction": fraction,
        "connection_integral": expected_connection,
        "endpoint_phase": expected_endpoint_phase,
        "gauge_invariant_geometric_phase": 0.0,
    }
    if any(not close_number(path.get(key), value) for key, value in expected_values.items()):
        errors.append(f"geometric-phase path changed or is non-finite: {label}")
        return
    wrapped = (float(path["endpoint_phase"]) + float(path["connection_integral"]) + math.pi) % (2.0 * math.pi) - math.pi
    if not math.isclose(wrapped, 0.0, rel_tol=0.0, abs_tol=1e-12):
        errors.append(f"endpoint-inclusive phase is nonzero: {label}")


def validate_up136(up136: object, errors: list[str]) -> None:
    if not isinstance(up136, dict):
        errors.append("missing UP-136 audit")
        return
    if set(up136) != UP136_KEYS:
        errors.append("UP-136 audit fields are not key-closed")
    path_specs = (
        ("full_loop_gauge_zero", 0.0, 1.0),
        ("full_loop_gauge_one_packet_gauge", 1.0, 1.0),
        ("full_loop_gauge_two", 2.0, 1.0),
        ("half_loop_gauge_one_packet_control", 1.0, 0.5),
    )
    for label, winding, fraction in path_specs:
        validate_phase_path(up136.get(label), label, winding, fraction, errors)
    if up136.get("projective_path_at_eta_zero") != "constant ray":
        errors.append("pole projective path is not recorded as constant")
    if up136.get("packet_omits_endpoint_phase") is not True:
        errors.append("packet endpoint-phase omission is not recorded")
    if up136.get("verdict") != EXPECTED_UP136_VERDICT:
        errors.append("UP-136 gauge-artifact verdict missing")


def validate(result: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if set(result) != TOP_LEVEL_KEYS:
        errors.append("top-level audit fields are not key-closed")
    if result.get("schema") != SCHEMA:
        errors.append("schema mismatch")
    if result.get("classification") != "external_packet_fabrication_audit":
        errors.append("classification mismatch")
    if result.get("claim_ceiling") != "packet_rerun_and_kill_audit_only":
        errors.append("claim ceiling mismatch")
    if result.get("promotion_allowed") is not False:
        errors.append("promotion must remain false")

    validate_packet(result.get("packet"), errors)
    validate_up135(result.get("up135_observational_audit"), errors)
    validate_up136(result.get("up136_geometric_phase_audit"), errors)

    if result.get("selector_controls") != EXPECTED_SELECTOR_CONTROLS:
        errors.append("selector controls are missing or changed")
    if not exact_bool_mapping(result.get("schedule_impact"), EXPECTED_SCHEDULE_IMPACT):
        errors.append("packet 107 must not move schedule claims")

    checks = result.get("checks")
    if not isinstance(checks, dict) or set(checks) != EXPECTED_CHECK_KEYS:
        errors.append("required audit checks are missing or extra")
    elif any(value is not True for value in checks.values()):
        errors.append("one or more audit checks failed")
    if result.get("all_checks_pass") is not True:
        errors.append("audit aggregate did not pass")
    elif isinstance(checks, dict) and result.get("all_checks_pass") != all(
        value is True for value in checks.values()
    ):
        errors.append("audit aggregate is inconsistent with checks")
    return errors


def run_self_test(result_path: Path) -> tuple[bool, dict[str, list[str]]]:
    base = strict_json_loads(result_path.read_text(encoding="utf-8"))
    baseline_errors = validate(base)
    outcomes: dict[str, list[str]] = {"baseline": baseline_errors}

    def remove_checks(record: dict[str, object]) -> None:
        record.pop("checks", None)

    def remove_hashes(record: dict[str, object]) -> None:
        record["packet"].pop("zip_sha256", None)
        record["packet"].pop("expected_zip_sha256", None)

    def empty_schedule(record: dict[str, object]) -> None:
        record["schedule_impact"] = {}

    def inject_nan(record: dict[str, object]) -> None:
        record["up136_geometric_phase_audit"]["full_loop_gauge_zero"]["gauge_invariant_geometric_phase"] = math.nan

    def corrupt_prediction(record: dict[str, object]) -> None:
        record["up135_observational_audit"]["packet_branch_predictions_at_z_1"]["total_H"] = 999.0

    def unbind_member(record: dict[str, object]) -> None:
        member = next(iter(EXPECTED_MEMBER_SHA256))
        record["packet"]["added_member_bytes_match_archive"][member] = False

    def corrupt_source(record: dict[str, object]) -> None:
        record["up135_observational_audit"]["sources"] = {}

    def admit_candidate(record: dict[str, object]) -> None:
        record["up135_observational_audit"]["closest_candidate_admitted"] = True

    def fake_aggregate(record: dict[str, object]) -> None:
        record["checks"]["packet_hash_matches"] = False
        record["all_checks_pass"] = True

    def corrupt_controls(record: dict[str, object]) -> None:
        record["selector_controls"] = {}

    def corrupt_classification(record: dict[str, object]) -> None:
        record["classification"] = "canonical"

    def negate_up135_verdict(record: dict[str, object]) -> None:
        record["up135_observational_audit"]["verdict"] = "UP-135 is not contradicted; total_H is admitted."

    def negate_up136_verdict(record: dict[str, object]) -> None:
        record["up136_geometric_phase_audit"]["verdict"] = "The phase is not gauge-dependent; the general identity is admitted."

    def add_top_level_claim(record: dict[str, object]) -> None:
        record["formal_admission_allowed"] = True

    def add_nested_claim(record: dict[str, object]) -> None:
        record["up135_observational_audit"]["branch_admitted"] = "total_H"

    def corrupt_non_admission_rationale(record: dict[str, object]) -> None:
        record["up135_observational_audit"]["why_not_admitted"] = "total_H is admitted"

    def coerce_boolean_to_integer(record: dict[str, object]) -> None:
        member = next(iter(EXPECTED_MEMBER_SHA256))
        record["packet"]["added_member_bytes_match_archive"][member] = 1

    def coerce_member_count_to_float(record: dict[str, object]) -> None:
        record["packet"]["member_count"] = 469.0

    mutations: list[tuple[str, Callable[[dict[str, object]], None]]] = [
        ("missing_checks", remove_checks),
        ("missing_hashes", remove_hashes),
        ("empty_schedule", empty_schedule),
        ("nan_phase", inject_nan),
        ("corrupt_prediction", corrupt_prediction),
        ("unbound_member", unbind_member),
        ("missing_sources", corrupt_source),
        ("candidate_admitted", admit_candidate),
        ("fake_aggregate", fake_aggregate),
        ("missing_controls", corrupt_controls),
        ("classification_promotion", corrupt_classification),
        ("negated_up135_verdict", negate_up135_verdict),
        ("negated_up136_verdict", negate_up136_verdict),
        ("extra_top_level_claim", add_top_level_claim),
        ("extra_nested_claim", add_nested_claim),
        ("corrupt_non_admission_rationale", corrupt_non_admission_rationale),
        ("integer_boolean_coercion", coerce_boolean_to_integer),
        ("float_member_count_coercion", coerce_member_count_to_float),
    ]
    for name, mutate in mutations:
        candidate = copy.deepcopy(base)
        mutate(candidate)
        outcomes[name] = validate(candidate)

    try:
        strict_json_loads('{"promotion_allowed": true, "promotion_allowed": false}')
        outcomes["duplicate_json_key"] = []
    except ValueError as error:
        outcomes["duplicate_json_key"] = [str(error)]

    passed = (
        not baseline_errors
        and all(outcomes[name] for name, _ in mutations)
        and bool(outcomes["duplicate_json_key"])
    )
    return passed, outcomes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path, nargs="?")
    parser.add_argument("--compare", type=Path)
    parser.add_argument("--packet-root", type=Path)
    parser.add_argument("--packet-zip", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.result is None:
        parser.error("result is required")
    if args.self_test:
        passed, outcomes = run_self_test(args.result)
        print(json.dumps({
            "mutation_cases": len(outcomes) - 1,
            "outcomes": outcomes,
            "pass": passed,
        }, sort_keys=True))
        return 0 if passed else 1

    try:
        result = strict_json_loads(args.result.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError) as error:
        print(json.dumps({
            "deterministic_match": None,
            "errors": [f"strict JSON parse failed: {error}"],
            "pass": False,
            "result": str(args.result),
        }, sort_keys=True))
        return 1
    errors = validate(result)
    if args.packet_root is None or args.packet_zip is None:
        errors.append("live --packet-root and --packet-zip provenance inputs are required")
    else:
        validate_live_provenance(
            result,
            args.packet_root.resolve(),
            args.packet_zip.resolve(),
            errors,
        )
    deterministic = None
    if args.compare:
        deterministic = args.result.read_bytes() == args.compare.read_bytes()
        if not deterministic:
            errors.append("deterministic rerun mismatch")
    print(json.dumps({
        "deterministic_match": deterministic,
        "errors": errors,
        "pass": not errors,
        "result": str(args.result),
    }, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
