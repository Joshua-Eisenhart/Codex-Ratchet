#!/usr/bin/env python3
"""Deterministic QICS QuantRelEntr fixed-input oracle packet."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np
import qics


HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "spec.json"

TOOL_MANIFEST = {
    "qics": {
        "function": "QuantRelEntr fixed-input epigraph minimization",
        "reason": "Produces every accepted oracle value; failures are fatal.",
    },
    "numpy": {
        "function": "spectral Umegaki comparator and map diagnostics",
        "reason": "Supplies an implementation independent of the QICS cone oracle.",
    },
    "scipy": {
        "function": "QICS runtime dependency",
        "reason": "Supports the pinned QICS model and solver.",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "qics": "load_bearing",
    "numpy": "supportive_independent_comparator",
    "scipy": "supportive_runtime_dependency",
}


def stable_float(value: Any) -> float:
    value = float(np.real(value))
    if not math.isfinite(value):
        raise ValueError(f"non-finite value: {value}")
    return float(f"{value:.15g}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(checkout: Path, *args: str) -> str:
    command = ["/usr/bin/git", "-C", str(checkout), *args]
    return subprocess.check_output(command, text=True).strip()


def distribution_metadata_hash(name: str) -> str:
    text = importlib.metadata.distribution(name).read_text("METADATA")
    if text is None:
        raise RuntimeError(f"missing METADATA for {name}")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_matrix(payload: dict[str, Any]) -> np.ndarray:
    real = np.asarray(payload["real"], dtype=np.float64)
    imag = np.asarray(payload["imag"], dtype=np.float64)
    if real.shape != imag.shape or real.ndim != 2 or real.shape[0] != real.shape[1]:
        raise ValueError("matrix payload must contain square real/imag arrays")
    return np.asarray(real + 1j * imag, dtype=np.complex128)


def state_diagnostics(matrix: np.ndarray) -> dict[str, Any]:
    eigvals = np.linalg.eigvalsh(matrix)
    return {
        "dimension": int(matrix.shape[0]),
        "hermitian_residual": stable_float(np.max(np.abs(matrix - matrix.conj().T))),
        "trace_real": stable_float(np.trace(matrix).real),
        "trace_imag_abs": stable_float(abs(np.trace(matrix).imag)),
        "trace_one_residual": stable_float(abs(np.trace(matrix) - 1.0)),
        "minimum_eigenvalue": stable_float(np.min(eigvals)),
        "maximum_eigenvalue": stable_float(np.max(eigvals)),
    }


def state_is_valid(diag: dict[str, Any], tol: dict[str, float]) -> bool:
    return bool(
        diag["hermitian_residual"] <= tol["hermitian_abs"]
        and diag["trace_one_residual"] <= tol["trace_abs"]
        and diag["trace_imag_abs"] <= tol["trace_abs"]
        and diag["minimum_eigenvalue"] > tol["positive_eigenvalue_floor"]
    )


def spectral_umegaki(rho: np.ndarray, sigma: np.ndarray) -> float:
    """Compute Tr[rho(log rho - log sigma)] using separate eigendecompositions."""
    rho_vals, rho_vecs = np.linalg.eigh(rho)
    sigma_vals, sigma_vecs = np.linalg.eigh(sigma)
    if np.min(rho_vals) <= 0.0 or np.min(sigma_vals) <= 0.0:
        raise ValueError("spectral comparator requires positive-definite inputs")
    log_rho = (rho_vecs * np.log(rho_vals)) @ rho_vecs.conj().T
    log_sigma = (sigma_vecs * np.log(sigma_vals)) @ sigma_vecs.conj().T
    return stable_float(np.trace(rho @ (log_rho - log_sigma)).real)


def qics_fixed_input_value(
    rho: np.ndarray, sigma: np.ndarray, solver_options: dict[str, Any]
) -> dict[str, Any]:
    n = rho.shape[0]
    cone = qics.cones.QuantRelEntr(n, iscomplex=True)
    variable_dim = 1 + 4 * n * n
    c = np.zeros((variable_dim, 1), dtype=np.float64)
    c[0, 0] = 1.0
    A = np.zeros((variable_dim - 1, variable_dim), dtype=np.float64)
    A[:, 1:] = np.eye(variable_dim - 1, dtype=np.float64)
    b = np.vstack(
        [qics.vectorize.mat_to_vec(rho), qics.vectorize.mat_to_vec(sigma)]
    )
    model = qics.Model(c=c, A=A, b=b, cones=[cone])
    solver = qics.Solver(model, **solver_options)
    info = solver.solve()

    solved_rho = np.asarray(info["s_opt"][0][1])
    solved_sigma = np.asarray(info["s_opt"][0][2])
    fixed_residual = max(
        float(np.max(np.abs(solved_rho - rho))),
        float(np.max(np.abs(solved_sigma - sigma))),
    )
    return {
        "value": stable_float(info["p_obj"]),
        "cone_t": stable_float(info["s_opt"][0][0][0, 0]),
        "dual_value": stable_float(info["d_obj"]),
        "solver_status": str(info["sol_status"]),
        "exit_status": str(info["exit_status"]),
        "iterations": int(info["num_iter"]),
        "optimality_gap": stable_float(info["opt_gap"]),
        "primal_feasibility": stable_float(info["p_feas"]),
        "dual_feasibility": stable_float(info["d_feas"]),
        "fixed_input_max_abs_residual": stable_float(fixed_residual),
    }


def pinching(matrix: np.ndarray) -> np.ndarray:
    return np.diag(np.diag(matrix)).astype(np.complex128)


def depolarizing(matrix: np.ndarray, alpha: float) -> np.ndarray:
    n = matrix.shape[0]
    return alpha * matrix + (1.0 - alpha) * np.trace(matrix) * np.eye(n) / n


def transpose_map(matrix: np.ndarray) -> np.ndarray:
    return matrix.T


def trace_scaling(matrix: np.ndarray, scale: float) -> np.ndarray:
    return scale * matrix


def map_function(map_spec: dict[str, Any]) -> Callable[[np.ndarray], np.ndarray]:
    kind = map_spec["kind"]
    if kind == "pinching":
        return pinching
    if kind == "depolarizing":
        alpha = float(map_spec["alpha"])
        return lambda matrix: depolarizing(matrix, alpha)
    if kind == "transpose":
        return transpose_map
    if kind == "trace_scaling":
        scale = float(map_spec["scale"])
        return lambda matrix: trace_scaling(matrix, scale)
    raise ValueError(f"unknown map kind: {kind}")


def map_certificate(map_spec: dict[str, Any], n: int, tolerance: float) -> dict[str, Any]:
    apply_map = map_function(map_spec)
    choi = np.zeros((n * n, n * n), dtype=np.complex128)
    for i in range(n):
        for j in range(n):
            basis = np.zeros((n, n), dtype=np.complex128)
            basis[i, j] = 1.0
            choi[i * n : (i + 1) * n, j * n : (j + 1) * n] = apply_map(basis)
    choi_hermitian_residual = float(np.max(np.abs(choi - choi.conj().T)))
    choi_hermitian = (choi + choi.conj().T) / 2.0
    min_choi_eigenvalue = float(np.min(np.linalg.eigvalsh(choi_hermitian)))
    trace_out = np.empty((n, n), dtype=np.complex128)
    for i in range(n):
        for j in range(n):
            block = choi[i * n : (i + 1) * n, j * n : (j + 1) * n]
            trace_out[i, j] = np.trace(block)
    trace_preserving_residual = float(np.max(np.abs(trace_out - np.eye(n))))
    cp_pass = bool(
        choi_hermitian_residual <= tolerance
        and min_choi_eigenvalue >= -tolerance
    )
    tp_pass = bool(trace_preserving_residual <= tolerance)
    return {
        "dimension": n,
        "choi_hermitian_residual": stable_float(choi_hermitian_residual),
        "minimum_choi_eigenvalue": stable_float(min_choi_eigenvalue),
        "trace_preserving_residual": stable_float(trace_preserving_residual),
        "complete_positivity_pass": cp_pass,
        "trace_preservation_pass": tp_pass,
        "accepted_as_cptp": bool(cp_pass and tp_pass),
    }


def environment_receipt(spec: dict[str, Any]) -> dict[str, Any]:
    pinned = spec["pinned_environment"]
    checkout = Path(pinned["qics_checkout"]).resolve()
    expected_python = Path(pinned["python"]).resolve()
    imported_qics = Path(qics.__file__).resolve()
    qics_commit = git_output(checkout, "rev-parse", "HEAD")
    qics_tree = git_output(checkout, "rev-parse", "HEAD^{tree}")
    qics_status = git_output(checkout, "status", "--porcelain")
    checks = {
        "python_path_exact": Path(sys.executable).resolve() == expected_python,
        "qics_version_exact": qics.__version__ == pinned["qics_version"],
        "qics_commit_exact": qics_commit == pinned["qics_commit"],
        "qics_checkout_clean": qics_status == "",
        "qics_import_from_checkout": imported_qics.is_relative_to(checkout),
    }
    return {
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "qics_version": qics.__version__,
        "qics_module": str(imported_qics),
        "qics_git_commit": qics_commit,
        "qics_git_tree": qics_tree,
        "qics_git_status_porcelain": qics_status,
        "numpy_version": np.__version__,
        "scipy_version": importlib.metadata.version("scipy"),
    }


def source_and_dependency_hashes(spec: dict[str, Any]) -> dict[str, Any]:
    checkout = Path(spec["pinned_environment"]["qics_checkout"]).resolve()
    packet_files = [
        "spec.json",
        "qics_entropy_dpi_numeric_oracle_v0.py",
        "validate_qics_entropy_dpi_numeric_oracle_v0.py",
        "run_all.sh",
    ]
    qics_files = [
        "qics/cones/entropy/quantrelentr.py",
        "qics/model.py",
        "qics/solver.py",
        "qics/vectorize.py",
    ]
    return {
        "algorithm": "sha256",
        "packet_sources": {name: sha256_file(HERE / name) for name in packet_files},
        "qics_sources": {name: sha256_file(checkout / name) for name in qics_files},
        "python_executable_resolved": {
            "path": str(Path(sys.executable).resolve()),
            "sha256": sha256_file(Path(sys.executable).resolve()),
        },
        "distribution_metadata": {
            "numpy": distribution_metadata_hash("numpy"),
            "scipy": distribution_metadata_hash("scipy"),
        },
    }


def evaluate_case(
    rho: np.ndarray,
    sigma: np.ndarray,
    solver_options: dict[str, Any],
    tolerances: dict[str, float],
) -> dict[str, Any]:
    spectral = spectral_umegaki(rho, sigma)
    qics_result = qics_fixed_input_value(rho, sigma, solver_options)
    abs_error = abs(qics_result["value"] - spectral)
    solver_pass = bool(
        qics_result["solver_status"] in {"optimal", "near_optimal"}
        and qics_result["exit_status"] in {"solved", "slow_progress"}
    )
    return {
        "spectral_umegaki": spectral,
        "qics": qics_result,
        "qics_spectral_abs_error": stable_float(abs_error),
        "solver_pass": solver_pass,
        "fixed_input_pass": bool(
            qics_result["fixed_input_max_abs_residual"]
            <= tolerances["fixed_input_abs"]
        ),
        "oracle_agreement_pass": bool(abs_error <= tolerances["qics_spectral_abs"]),
    }


def build_result(spec: dict[str, Any]) -> dict[str, Any]:
    tolerances = spec["tolerances"]
    solver_options = spec["solver_options"]
    environment = environment_receipt(spec)
    if not environment["all_checks_pass"]:
        raise RuntimeError(f"pinned environment check failed: {environment['checks']}")

    dimensions = sorted(
        {len(pair["rho"]["real"]) for pair in spec["density_pairs"]}
    )
    certificates: dict[str, Any] = {}
    all_map_specs = spec["maps"]["accepted"] + spec["maps"]["invalid_controls"]
    for n in dimensions:
        certificates[str(n)] = {
            map_spec["id"]: map_certificate(
                map_spec, n, tolerances["map_certificate_abs"]
            )
            for map_spec in all_map_specs
        }

    pair_results = []
    qics_solves = 0
    dpi_cases = 0
    invalid_controls_rejected = 0
    errors: list[str] = []
    max_oracle_error = 0.0
    max_fixed_residual = 0.0
    direct_margins: list[float] = []
    qics_margins: list[float] = []

    for pair_spec in spec["density_pairs"]:
        pair_id = pair_spec["id"]
        rho = load_matrix(pair_spec["rho"])
        sigma = load_matrix(pair_spec["sigma"])
        n = rho.shape[0]
        rho_diag = state_diagnostics(rho)
        sigma_diag = state_diagnostics(sigma)
        input_valid = state_is_valid(rho_diag, tolerances) and state_is_valid(
            sigma_diag, tolerances
        )
        if not input_valid:
            errors.append(f"{pair_id}: invalid input density pair")

        original = evaluate_case(rho, sigma, solver_options, tolerances)
        qics_solves += 1
        max_oracle_error = max(max_oracle_error, original["qics_spectral_abs_error"])
        max_fixed_residual = max(
            max_fixed_residual, original["qics"]["fixed_input_max_abs_residual"]
        )

        accepted_maps = []
        for map_spec in spec["maps"]["accepted"]:
            map_id = map_spec["id"]
            certificate = certificates[str(n)][map_id]
            apply_map = map_function(map_spec)
            mapped_rho = apply_map(rho)
            mapped_sigma = apply_map(sigma)
            mapped_rho_diag = state_diagnostics(mapped_rho)
            mapped_sigma_diag = state_diagnostics(mapped_sigma)
            mapped_valid = state_is_valid(
                mapped_rho_diag, tolerances
            ) and state_is_valid(mapped_sigma_diag, tolerances)
            mapped = evaluate_case(
                mapped_rho, mapped_sigma, solver_options, tolerances
            )
            qics_solves += 1
            dpi_cases += 1
            direct_margin = original["spectral_umegaki"] - mapped["spectral_umegaki"]
            qics_margin = original["qics"]["value"] - mapped["qics"]["value"]
            direct_margins.append(direct_margin)
            qics_margins.append(qics_margin)
            max_oracle_error = max(max_oracle_error, mapped["qics_spectral_abs_error"])
            max_fixed_residual = max(
                max_fixed_residual, mapped["qics"]["fixed_input_max_abs_residual"]
            )
            direct_dpi_pass = direct_margin >= -tolerances["direct_dpi_slack"]
            qics_dpi_pass = qics_margin >= -tolerances["qics_dpi_slack"]
            map_pass = bool(
                certificate["accepted_as_cptp"]
                and mapped_valid
                and mapped["solver_pass"]
                and mapped["fixed_input_pass"]
                and mapped["oracle_agreement_pass"]
                and direct_dpi_pass
                and qics_dpi_pass
            )
            if not map_pass:
                errors.append(f"{pair_id}/{map_id}: accepted-map check failed")
            accepted_maps.append(
                {
                    "map_id": map_id,
                    "map_certificate": certificate,
                    "mapped_rho_diagnostics": mapped_rho_diag,
                    "mapped_sigma_diagnostics": mapped_sigma_diag,
                    "mapped_states_valid": mapped_valid,
                    "mapped_case": mapped,
                    "direct_contraction_margin": stable_float(direct_margin),
                    "qics_contraction_margin": stable_float(qics_margin),
                    "direct_dpi_pass": direct_dpi_pass,
                    "qics_dpi_pass": qics_dpi_pass,
                    "case_pass": map_pass,
                    "counted_as_dpi_evidence": True,
                }
            )

        invalid_controls = []
        for map_spec in spec["maps"]["invalid_controls"]:
            map_id = map_spec["id"]
            certificate = certificates[str(n)][map_id]
            apply_map = map_function(map_spec)
            control_rho = apply_map(rho)
            control_sigma = apply_map(sigma)
            control_rho_diag = state_diagnostics(control_rho)
            control_sigma_diag = state_diagnostics(control_sigma)
            rejection_reasons = []
            if not certificate["complete_positivity_pass"]:
                rejection_reasons.append("complete_positivity_failed")
            if not certificate["trace_preservation_pass"]:
                rejection_reasons.append("trace_preservation_failed")
            if not state_is_valid(control_rho_diag, tolerances) or not state_is_valid(
                control_sigma_diag, tolerances
            ):
                rejection_reasons.append("density_output_validation_failed")
            rejected = bool(rejection_reasons)
            if rejected:
                invalid_controls_rejected += 1
            else:
                errors.append(f"{pair_id}/{map_id}: invalid control was not rejected")
            diagnostic_value = spectral_umegaki(control_rho, control_sigma)
            invalid_controls.append(
                {
                    "map_id": map_id,
                    "map_certificate": certificate,
                    "rho_diagnostics": control_rho_diag,
                    "sigma_diagnostics": control_sigma_diag,
                    "spectral_value_diagnostic_only": diagnostic_value,
                    "spectral_change_from_input": stable_float(
                        diagnostic_value - original["spectral_umegaki"]
                    ),
                    "rejected": rejected,
                    "rejection_reasons": rejection_reasons,
                    "qics_invoked": False,
                    "counted_as_dpi_evidence": False,
                }
            )

        original_pass = bool(
            input_valid
            and original["solver_pass"]
            and original["fixed_input_pass"]
            and original["oracle_agreement_pass"]
        )
        if not original_pass:
            errors.append(f"{pair_id}: original oracle check failed")
        pair_results.append(
            {
                "pair_id": pair_id,
                "dimension": n,
                "rho_diagnostics": rho_diag,
                "sigma_diagnostics": sigma_diag,
                "input_pair_valid": input_valid,
                "original": original,
                "accepted_maps": accepted_maps,
                "invalid_controls": invalid_controls,
                "pair_pass": bool(
                    original_pass
                    and all(item["case_pass"] for item in accepted_maps)
                    and all(item["rejected"] for item in invalid_controls)
                ),
            }
        )

    expected = spec["expected_counts"]
    count_checks = {
        "input_pairs": len(pair_results) == expected["input_pairs"],
        "qics_solves": qics_solves == expected["qics_solves"],
        "dpi_cases": dpi_cases == expected["dpi_cases"],
        "invalid_controls": invalid_controls_rejected
        == expected["input_pairs"] * expected["invalid_controls_per_pair"],
    }
    if not all(count_checks.values()):
        errors.append(f"count mismatch: {count_checks}")

    load_bearing_qics_pass = bool(
        qics_solves == expected["qics_solves"]
        and all(
            pair["original"]["solver_pass"]
            and pair["original"]["oracle_agreement_pass"]
            and all(
                mapped["mapped_case"]["solver_pass"]
                and mapped["mapped_case"]["oracle_agreement_pass"]
                and mapped["qics_dpi_pass"]
                for mapped in pair["accepted_maps"]
            )
            for pair in pair_results
        )
    )
    tests = {
        "pinned_environment": environment["all_checks_pass"],
        "fixed_inputs_valid": all(pair["input_pair_valid"] for pair in pair_results),
        "accepted_maps_certified": all(
            item["map_certificate"]["accepted_as_cptp"]
            for pair in pair_results
            for item in pair["accepted_maps"]
        ),
        "all_qics_solver_runs": all(
            pair["original"]["solver_pass"]
            and all(item["mapped_case"]["solver_pass"] for item in pair["accepted_maps"])
            for pair in pair_results
        ),
        "all_fixed_input_residuals": max_fixed_residual
        <= tolerances["fixed_input_abs"],
        "all_oracle_agreements": max_oracle_error <= tolerances["qics_spectral_abs"],
        "all_direct_dpi_checks": min(direct_margins) >= -tolerances["direct_dpi_slack"],
        "all_qics_dpi_checks": min(qics_margins) >= -tolerances["qics_dpi_slack"],
        "invalid_controls_rejected_and_excluded": invalid_controls_rejected
        == expected["input_pairs"] * expected["invalid_controls_per_pair"],
        "qics_load_bearing": load_bearing_qics_pass,
        "expected_counts": all(count_checks.values()),
    }
    overall_pass = bool(all(tests.values()) and not errors)

    return {
        "schema": "codex_ratchet.qics_entropy_dpi_numeric_oracle_result.v0",
        "sim_id": spec["sim_id"],
        "classification": spec["classification"],
        "producer_status_label": "runs" if overall_pass else "failed",
        "claim_ceiling": spec["claim_ceiling"],
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "eligible_consumers": spec["eligible_consumers"],
        "blocked_consumers": spec["blocked_consumers"],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "environment": environment,
        "source_and_dependency_hashes": source_and_dependency_hashes(spec),
        "tolerances": tolerances,
        "map_certificates_by_dimension": certificates,
        "pairs": pair_results,
        "metrics": {
            "input_pairs": len(pair_results),
            "accepted_maps": len(spec["maps"]["accepted"]),
            "qics_solves": qics_solves,
            "dpi_cases": dpi_cases,
            "invalid_controls_total": expected["input_pairs"]
            * expected["invalid_controls_per_pair"],
            "invalid_controls_rejected": invalid_controls_rejected,
            "max_qics_spectral_abs_error": stable_float(max_oracle_error),
            "max_fixed_input_abs_residual": stable_float(max_fixed_residual),
            "minimum_direct_contraction_margin": stable_float(min(direct_margins)),
            "minimum_qics_contraction_margin": stable_float(min(qics_margins)),
        },
        "tests": tests,
        "test_count": len(tests),
        "tests_passed": sum(bool(value) for value in tests.values()),
        "errors": errors,
        "all_tests_pass": overall_pass,
        "divergence_log": [
            "QICS cone values are compared case-by-case with a separate spectral implementation.",
            "Accepted-map contraction is checked independently for the two value streams.",
            "Rejected controls are diagnostic only and are never included in the accepted DPI count."
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "result.json")
    args = parser.parse_args()
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    result = build_result(spec)
    output = args.output if args.output.is_absolute() else HERE / args.output
    if output.resolve().parent != HERE:
        raise ValueError("output must stay inside the packet directory")
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(output),
                "all_tests_pass": result["all_tests_pass"],
                "tests": f"{result['tests_passed']}/{result['test_count']}",
                "metrics": result["metrics"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_tests_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
