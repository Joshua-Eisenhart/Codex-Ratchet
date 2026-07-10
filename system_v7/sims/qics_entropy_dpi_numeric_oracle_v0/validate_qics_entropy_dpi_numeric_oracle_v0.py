#!/usr/bin/env python3
"""Independent structural and numerical validator for the QICS packet."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np


HERE = Path(__file__).resolve().parent
NUMERIC_RECEIPT_ABS = 5e-13


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def distribution_metadata_hash(name: str) -> str:
    text = importlib.metadata.distribution(name).read_text("METADATA")
    if text is None:
        raise RuntimeError(f"missing METADATA for {name}")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_matrix(payload: dict[str, Any]) -> np.ndarray:
    return np.asarray(payload["real"], dtype=np.float64) + 1j * np.asarray(
        payload["imag"], dtype=np.float64
    )


def spectral_umegaki(rho: np.ndarray, sigma: np.ndarray) -> float:
    rho_vals, rho_vecs = np.linalg.eigh(rho)
    sigma_vals, sigma_vecs = np.linalg.eigh(sigma)
    if np.min(rho_vals) <= 0.0 or np.min(sigma_vals) <= 0.0:
        raise ValueError("spectral validator requires positive-definite inputs")
    log_rho = (rho_vecs * np.log(rho_vals)) @ rho_vecs.conj().T
    log_sigma = (sigma_vecs * np.log(sigma_vals)) @ sigma_vecs.conj().T
    return float(np.trace(rho @ (log_rho - log_sigma)).real)


def state_is_valid(matrix: np.ndarray, tol: dict[str, float]) -> bool:
    eigvals = np.linalg.eigvalsh(matrix)
    return bool(
        np.max(np.abs(matrix - matrix.conj().T)) <= tol["hermitian_abs"]
        and abs(np.trace(matrix) - 1.0) <= tol["trace_abs"]
        and np.min(eigvals) > tol["positive_eigenvalue_floor"]
    )


def map_function(map_spec: dict[str, Any]):
    kind = map_spec["kind"]
    if kind == "pinching":
        return lambda matrix: np.diag(np.diag(matrix)).astype(np.complex128)
    if kind == "depolarizing":
        alpha = float(map_spec["alpha"])
        return lambda matrix: alpha * matrix + (
            (1.0 - alpha) * np.trace(matrix) * np.eye(matrix.shape[0]) / matrix.shape[0]
        )
    if kind == "transpose":
        return lambda matrix: matrix.T
    if kind == "trace_scaling":
        scale = float(map_spec["scale"])
        return lambda matrix: scale * matrix
    raise ValueError(f"unknown map kind: {kind}")


def map_certificate(map_spec: dict[str, Any], n: int, tolerance: float) -> dict[str, Any]:
    apply_map = map_function(map_spec)
    choi = np.zeros((n * n, n * n), dtype=np.complex128)
    for i in range(n):
        for j in range(n):
            basis = np.zeros((n, n), dtype=np.complex128)
            basis[i, j] = 1.0
            choi[i * n : (i + 1) * n, j * n : (j + 1) * n] = apply_map(basis)
    hermitian_residual = float(np.max(np.abs(choi - choi.conj().T)))
    min_eigenvalue = float(np.min(np.linalg.eigvalsh((choi + choi.conj().T) / 2.0)))
    trace_out = np.empty((n, n), dtype=np.complex128)
    for i in range(n):
        for j in range(n):
            trace_out[i, j] = np.trace(
                choi[i * n : (i + 1) * n, j * n : (j + 1) * n]
            )
    tp_residual = float(np.max(np.abs(trace_out - np.eye(n))))
    cp_pass = hermitian_residual <= tolerance and min_eigenvalue >= -tolerance
    tp_pass = tp_residual <= tolerance
    return {
        "choi_hermitian_residual": hermitian_residual,
        "minimum_choi_eigenvalue": min_eigenvalue,
        "trace_preserving_residual": tp_residual,
        "complete_positivity_pass": bool(cp_pass),
        "trace_preservation_pass": bool(tp_pass),
        "accepted_as_cptp": bool(cp_pass and tp_pass),
    }


def require_close(actual: Any, expected: float, message: str, errors: list[str]) -> None:
    try:
        difference = abs(float(actual) - float(expected))
    except (TypeError, ValueError, OverflowError):
        errors.append(message)
        return
    require(np.isfinite(difference) and difference <= NUMERIC_RECEIPT_ABS, message, errors)


def result_float(
    value: Any, message: str, errors: list[str], fallback: float
) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError, OverflowError):
        errors.append(message)
        return fallback
    if not np.isfinite(parsed):
        errors.append(message)
        return fallback
    return parsed


def require_certificate(
    actual: dict[str, Any], expected: dict[str, Any], label: str, errors: list[str]
) -> None:
    for key in (
        "choi_hermitian_residual",
        "minimum_choi_eigenvalue",
        "trace_preserving_residual",
    ):
        require_close(actual.get(key), expected[key], f"{label}: {key} mismatch", errors)
    for key in (
        "complete_positivity_pass",
        "trace_preservation_pass",
        "accepted_as_cptp",
    ):
        require(actual.get(key) is expected[key], f"{label}: {key} mismatch", errors)


def validate(result_path: Path, compare_path: Path | None) -> dict[str, Any]:
    errors: list[str] = []
    result = json.loads(result_path.read_text(encoding="utf-8"))
    spec = json.loads((HERE / "spec.json").read_text(encoding="utf-8"))
    tol = spec["tolerances"]
    expected = spec["expected_counts"]

    require(
        result.get("schema")
        == "codex_ratchet.qics_entropy_dpi_numeric_oracle_result.v0",
        "unexpected result schema",
        errors,
    )
    require(result.get("sim_id") == spec["sim_id"], "sim_id mismatch", errors)
    require(
        result.get("classification") == "scratch_diagnostic",
        "classification must remain scratch_diagnostic",
        errors,
    )
    for field in ("promotion_allowed", "formal_admission_allowed", "stage_movement_allowed"):
        require(result.get(field) is False, f"{field} must be false", errors)
    require(
        result.get("blocked_consumers") == spec["blocked_consumers"],
        "blocked_consumers mismatch",
        errors,
    )
    require(result.get("claim_ceiling") == spec["claim_ceiling"], "claim_ceiling mismatch", errors)
    require(
        result.get("eligible_consumers") == spec["eligible_consumers"],
        "eligible_consumers mismatch",
        errors,
    )
    require(
        result.get("tool_integration_depth") == spec["tool_integration_depth"],
        "tool_integration_depth mismatch",
        errors,
    )

    environment = result.get("environment", {})
    require(environment.get("all_checks_pass") is True, "environment checks failed", errors)
    require(
        environment.get("qics_git_commit")
        == spec["pinned_environment"]["qics_commit"],
        "QICS commit mismatch",
        errors,
    )
    require(
        environment.get("qics_version") == spec["pinned_environment"]["qics_version"],
        "QICS version mismatch",
        errors,
    )
    require(
        environment.get("qics_git_status_porcelain") == "",
        "QICS checkout was not clean",
        errors,
    )

    hashes = result.get("source_and_dependency_hashes", {})
    require(hashes.get("algorithm") == "sha256", "hash algorithm mismatch", errors)
    for relative, recorded in hashes.get("packet_sources", {}).items():
        path = (HERE / relative).resolve()
        require(path.parent == HERE, f"packet hash path escaped: {relative}", errors)
        require(path.is_file(), f"missing hashed packet source: {relative}", errors)
        if path.is_file():
            require(sha256_file(path) == recorded, f"packet source hash mismatch: {relative}", errors)
    require(
        set(hashes.get("packet_sources", {}))
        == {
            "spec.json",
            "qics_entropy_dpi_numeric_oracle_v0.py",
            "validate_qics_entropy_dpi_numeric_oracle_v0.py",
            "run_all.sh",
        },
        "packet source hash set mismatch",
        errors,
    )
    checkout = Path(spec["pinned_environment"]["qics_checkout"]).resolve()
    expected_qics_sources = {
        "qics/cones/entropy/quantrelentr.py",
        "qics/model.py",
        "qics/solver.py",
        "qics/vectorize.py",
    }
    require(
        set(hashes.get("qics_sources", {})) == expected_qics_sources,
        "QICS source hash set mismatch",
        errors,
    )
    for relative, recorded in hashes.get("qics_sources", {}).items():
        path = (checkout / relative).resolve()
        require(path.is_relative_to(checkout), f"QICS hash path escaped: {relative}", errors)
        require(path.is_file(), f"missing hashed QICS source: {relative}", errors)
        if path.is_file():
            require(sha256_file(path) == recorded, f"QICS source hash mismatch: {relative}", errors)
    python_receipt = hashes.get("python_executable_resolved", {})
    expected_python = Path(spec["pinned_environment"]["python"]).resolve()
    require(
        Path(python_receipt.get("path", "/missing")).resolve() == expected_python,
        "resolved Python path mismatch",
        errors,
    )
    require(
        python_receipt.get("sha256") == sha256_file(expected_python),
        "Python executable hash mismatch",
        errors,
    )
    metadata_hashes = hashes.get("distribution_metadata", {})
    for distribution in ("numpy", "scipy"):
        require(
            metadata_hashes.get(distribution) == distribution_metadata_hash(distribution),
            f"{distribution} METADATA hash mismatch",
            errors,
        )
    live_commit = subprocess.check_output(
        ["/usr/bin/git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
    ).strip()
    live_status = subprocess.check_output(
        ["/usr/bin/git", "-C", str(checkout), "status", "--porcelain"], text=True
    ).strip()
    require(live_commit == spec["pinned_environment"]["qics_commit"], "live QICS commit mismatch", errors)
    require(live_status == "", "live QICS checkout is dirty", errors)

    pairs = result.get("pairs", [])
    require(len(pairs) == expected["input_pairs"], "input pair count mismatch", errors)
    require(
        [pair.get("pair_id") for pair in pairs]
        == [pair["id"] for pair in spec["density_pairs"]],
        "pair IDs must exactly match the unique ordered spec set",
        errors,
    )
    qics_solves = 0
    dpi_cases = 0
    invalid_controls = 0
    max_error = 0.0
    max_fixed = 0.0
    direct_margins: list[float] = []
    qics_margins: list[float] = []

    pair_specs = {pair["id"]: pair for pair in spec["density_pairs"]}
    accepted_map_specs = {item["id"]: item for item in spec["maps"]["accepted"]}
    invalid_map_specs = {item["id"]: item for item in spec["maps"]["invalid_controls"]}
    for pair in pairs:
        pair_id = pair.get("pair_id")
        require(pair_id in pair_specs, f"unknown pair_id: {pair_id}", errors)
        if pair_id not in pair_specs:
            continue
        pair_spec = pair_specs[pair_id]
        rho = load_matrix(pair_spec["rho"])
        sigma = load_matrix(pair_spec["sigma"])
        require(state_is_valid(rho, tol), f"{pair_id}: recomputed rho invalid", errors)
        require(state_is_valid(sigma, tol), f"{pair_id}: recomputed sigma invalid", errors)
        expected_original_spectral = spectral_umegaki(rho, sigma)
        require(pair.get("input_pair_valid") is True, "invalid fixed input pair", errors)
        original = pair.get("original", {})
        qics_solves += 1
        require_close(
            original.get("spectral_umegaki"),
            expected_original_spectral,
            f"{pair_id}: original spectral value mismatch",
            errors,
        )
        original_qics = result_float(
            original.get("qics", {}).get("value"),
            f"{pair_id}: malformed original QICS value",
            errors,
            float("inf"),
        )
        expected_original_error = abs(original_qics - expected_original_spectral)
        require_close(
            original.get("qics_spectral_abs_error"),
            expected_original_error,
            f"{pair_id}: original oracle error mismatch",
            errors,
        )
        require(original.get("solver_pass") is True, "original QICS solver failed", errors)
        require(original.get("fixed_input_pass") is True, "original fixed-input check failed", errors)
        require(original.get("oracle_agreement_pass") is True, "original oracle mismatch", errors)
        max_error = max(
            max_error,
            result_float(
                original.get("qics_spectral_abs_error"),
                f"{pair_id}: malformed original oracle error",
                errors,
                float("inf"),
            ),
        )
        max_fixed = max(
            max_fixed,
            result_float(
                original.get("qics", {}).get("fixed_input_max_abs_residual"),
                f"{pair_id}: malformed original fixed-input residual",
                errors,
                float("inf"),
            ),
        )
        accepted = pair.get("accepted_maps", [])
        require(len(accepted) == expected["accepted_maps"], "accepted map count mismatch", errors)
        require(
            [item.get("map_id") for item in accepted]
            == [item["id"] for item in spec["maps"]["accepted"]],
            f"{pair_id}: accepted map IDs must exactly match the unique ordered spec set",
            errors,
        )
        for mapped in accepted:
            map_id = mapped.get("map_id")
            require(map_id in accepted_map_specs, f"{pair_id}: unknown accepted map", errors)
            if map_id not in accepted_map_specs:
                continue
            map_spec = accepted_map_specs[map_id]
            expected_certificate = map_certificate(
                map_spec, rho.shape[0], tol["map_certificate_abs"]
            )
            require_certificate(
                mapped.get("map_certificate", {}),
                expected_certificate,
                f"{pair_id}/{map_id}",
                errors,
            )
            apply_map = map_function(map_spec)
            mapped_rho = apply_map(rho)
            mapped_sigma = apply_map(sigma)
            recomputed_states_valid = state_is_valid(
                mapped_rho, tol
            ) and state_is_valid(mapped_sigma, tol)
            expected_mapped_spectral = spectral_umegaki(mapped_rho, mapped_sigma)
            qics_solves += 1
            dpi_cases += 1
            require(mapped.get("counted_as_dpi_evidence") is True, "accepted map not counted", errors)
            require(mapped.get("map_certificate", {}).get("accepted_as_cptp") is True, "accepted map certificate failed", errors)
            require(mapped.get("mapped_states_valid") is True, "accepted map output invalid", errors)
            require(mapped.get("case_pass") is True, "accepted map case failed", errors)
            require(mapped.get("direct_dpi_pass") is True, "direct contraction failed", errors)
            require(mapped.get("qics_dpi_pass") is True, "QICS contraction failed", errors)
            mapped_case = mapped.get("mapped_case", {})
            require_close(
                mapped_case.get("spectral_umegaki"),
                expected_mapped_spectral,
                f"{pair_id}/{map_id}: mapped spectral value mismatch",
                errors,
            )
            mapped_qics = result_float(
                mapped_case.get("qics", {}).get("value"),
                f"{pair_id}/{map_id}: malformed mapped QICS value",
                errors,
                float("inf"),
            )
            expected_mapped_error = abs(mapped_qics - expected_mapped_spectral)
            require_close(
                mapped_case.get("qics_spectral_abs_error"),
                expected_mapped_error,
                f"{pair_id}/{map_id}: oracle error mismatch",
                errors,
            )
            expected_direct_margin = expected_original_spectral - expected_mapped_spectral
            expected_qics_margin = original_qics - mapped_qics
            require_close(
                mapped.get("direct_contraction_margin"),
                expected_direct_margin,
                f"{pair_id}/{map_id}: direct margin mismatch",
                errors,
            )
            require_close(
                mapped.get("qics_contraction_margin"),
                expected_qics_margin,
                f"{pair_id}/{map_id}: QICS margin mismatch",
                errors,
            )
            require(
                mapped.get("mapped_states_valid") is recomputed_states_valid,
                f"{pair_id}/{map_id}: mapped state validity mismatch",
                errors,
            )
            require(mapped_case.get("solver_pass") is True, "mapped QICS solver failed", errors)
            require(mapped_case.get("oracle_agreement_pass") is True, "mapped oracle mismatch", errors)
            max_error = max(
                max_error,
                result_float(
                    mapped_case.get("qics_spectral_abs_error"),
                    f"{pair_id}/{map_id}: malformed mapped oracle error",
                    errors,
                    float("inf"),
                ),
            )
            max_fixed = max(
                max_fixed,
                result_float(
                    mapped_case.get("qics", {}).get("fixed_input_max_abs_residual"),
                    f"{pair_id}/{map_id}: malformed mapped fixed-input residual",
                    errors,
                    float("inf"),
                ),
            )
            direct_margins.append(
                result_float(
                    mapped.get("direct_contraction_margin"),
                    f"{pair_id}/{map_id}: malformed direct margin",
                    errors,
                    -float("inf"),
                )
            )
            qics_margins.append(
                result_float(
                    mapped.get("qics_contraction_margin"),
                    f"{pair_id}/{map_id}: malformed QICS margin",
                    errors,
                    -float("inf"),
                )
            )
        controls = pair.get("invalid_controls", [])
        require(
            len(controls) == expected["invalid_controls_per_pair"],
            "invalid control count mismatch",
            errors,
        )
        require(
            [item.get("map_id") for item in controls]
            == [item["id"] for item in spec["maps"]["invalid_controls"]],
            f"{pair_id}: invalid control IDs must exactly match the unique ordered spec set",
            errors,
        )
        for control in controls:
            map_id = control.get("map_id")
            require(map_id in invalid_map_specs, f"{pair_id}: unknown invalid control", errors)
            if map_id not in invalid_map_specs:
                continue
            map_spec = invalid_map_specs[map_id]
            expected_certificate = map_certificate(
                map_spec, rho.shape[0], tol["map_certificate_abs"]
            )
            require_certificate(
                control.get("map_certificate", {}),
                expected_certificate,
                f"{pair_id}/{map_id}",
                errors,
            )
            apply_map = map_function(map_spec)
            control_rho = apply_map(rho)
            control_sigma = apply_map(sigma)
            expected_reasons = []
            if not expected_certificate["complete_positivity_pass"]:
                expected_reasons.append("complete_positivity_failed")
            if not expected_certificate["trace_preservation_pass"]:
                expected_reasons.append("trace_preservation_failed")
            if not state_is_valid(control_rho, tol) or not state_is_valid(control_sigma, tol):
                expected_reasons.append("density_output_validation_failed")
            expected_control_spectral = spectral_umegaki(control_rho, control_sigma)
            require(
                control.get("rejection_reasons") == expected_reasons,
                f"{pair_id}/{map_id}: rejection reasons mismatch",
                errors,
            )
            require_close(
                control.get("spectral_value_diagnostic_only"),
                expected_control_spectral,
                f"{pair_id}/{map_id}: diagnostic spectral value mismatch",
                errors,
            )
            require_close(
                control.get("spectral_change_from_input"),
                expected_control_spectral - expected_original_spectral,
                f"{pair_id}/{map_id}: diagnostic spectral change mismatch",
                errors,
            )
            invalid_controls += 1
            require(control.get("rejected") is True, "invalid control was not rejected", errors)
            require(bool(control.get("rejection_reasons")), "invalid control lacks rejection reason", errors)
            require(control.get("qics_invoked") is False, "invalid control invoked QICS", errors)
            require(control.get("counted_as_dpi_evidence") is False, "invalid control counted as evidence", errors)
        require(pair.get("pair_pass") is True, "pair_pass false", errors)

    require(qics_solves == expected["qics_solves"], "QICS solve count mismatch", errors)
    require(dpi_cases == expected["dpi_cases"], "DPI case count mismatch", errors)
    require(
        invalid_controls
        == expected["input_pairs"] * expected["invalid_controls_per_pair"],
        "invalid control total mismatch",
        errors,
    )
    require(max_error <= tol["qics_spectral_abs"], "oracle error tolerance exceeded", errors)
    require(max_fixed <= tol["fixed_input_abs"], "fixed-input tolerance exceeded", errors)
    require(
        bool(direct_margins) and min(direct_margins) >= -tol["direct_dpi_slack"],
        "direct contraction margin failed",
        errors,
    )
    require(
        bool(qics_margins) and min(qics_margins) >= -tol["qics_dpi_slack"],
        "QICS contraction margin failed",
        errors,
    )
    require(result.get("all_tests_pass") is True, "producer all_tests_pass false", errors)
    require(result.get("tests_passed") == result.get("test_count"), "producer test count failed", errors)
    require(result.get("tests", {}).get("qics_load_bearing") is True, "load-bearing QICS test failed", errors)

    deterministic_match = None
    if compare_path is not None:
        deterministic_match = result_path.read_bytes() == compare_path.read_bytes()
        require(deterministic_match, "deterministic rerun bytes differ", errors)

    return {
        "validator": "validate_qics_entropy_dpi_numeric_oracle_v0.py",
        "result": str(result_path),
        "compare": str(compare_path) if compare_path else None,
        "deterministic_match": deterministic_match,
        "qics_solves": qics_solves,
        "dpi_cases": dpi_cases,
        "invalid_controls_rejected": invalid_controls,
        "max_qics_spectral_abs_error": max_error,
        "max_fixed_input_abs_residual": max_fixed,
        "minimum_direct_contraction_margin": min(direct_margins),
        "minimum_qics_contraction_margin": min(qics_margins),
        "errors": errors,
        "pass": not errors,
    }


def malformed_numeric_self_test() -> dict[str, Any]:
    cases = [None, "not-a-number", {}, []]
    failures = []
    for index, value in enumerate(cases):
        conversion_errors: list[str] = []
        converted = result_float(value, "malformed", conversion_errors, -123.0)
        if converted != -123.0 or conversion_errors != ["malformed"]:
            failures.append(f"result_float case {index} did not fail closed")
        comparison_errors: list[str] = []
        require_close(value, 0.0, "malformed", comparison_errors)
        if comparison_errors != ["malformed"]:
            failures.append(f"require_close case {index} did not fail closed")
    return {
        "self_test": "malformed_numeric_fields_fail_closed",
        "cases": len(cases) * 2,
        "failures": failures,
        "pass": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", nargs="?", type=Path, default=HERE / "result.json")
    parser.add_argument("--compare", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        report = malformed_numeric_self_test()
        print(json.dumps(report, sort_keys=True))
        return 0 if report["pass"] else 1
    result_path = args.result if args.result.is_absolute() else HERE / args.result
    compare_path = args.compare
    if compare_path is not None and not compare_path.is_absolute():
        compare_path = HERE / compare_path
    for path in [result_path, compare_path]:
        if path is not None and path.resolve().parent != HERE:
            raise ValueError("validator inputs must stay inside the packet directory")
    report = validate(result_path, compare_path)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
