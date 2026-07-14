#!/usr/bin/env python3
"""Hardened Gap K cross-runtime tensor-chain fit diagnostic.

The primary fixture is a deterministic, full-support, unequal-magnitude
six-qubit state rather than GHZ or a product state. Python/quimb and
Julia/ITensors independently regenerate it and expose MPS-derived Schmidt
spectra. The result is intentionally non-promoting: agreement on this finite
fixture is a function-level tool receipt, not a general engine-equivalence or
scientific claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("NUMBA_CACHE_DIR", "/private/tmp/codex_numba_cache")

import numpy as np
import quimb
import quimb.tensor as qtn


N_QUBITS = 6
CUT = 3
MAX_SCHMIDT_RANK = 2**CUT
TOLERANCE = 2.0e-12
TAMPER_DETECTION_FLOOR = 1.0e-4
CANONICAL_PYTHON_ALIAS = Path(
    "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
)
JULIA_BIN = Path("/opt/homebrew/bin/julia")
JULIA_PROJECT = Path(
    os.environ.get(
        "CODEX_RATCHET_JULIA_PROJECT",
        "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier",
    )
)
SOURCE_DIR = Path(__file__).resolve().parent
JULIA_SOURCE = SOURCE_DIR / "gap_k_tensor_chain_v2.jl"
DEFAULT_RESULT = SOURCE_DIR / "results" / "gap_k_tensor_chain_v2_results.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_state(state: np.ndarray) -> np.ndarray:
    return state / np.linalg.norm(state)


def primary_state() -> np.ndarray:
    state = np.zeros((2,) * N_QUBITS, dtype=np.complex128)
    for bits in np.ndindex(state.shape):
        index = sum(bit << (N_QUBITS - 1 - offset) for offset, bit in enumerate(bits))
        weight = sum(bits)
        real_part = (37 * (index + 1) ** 2 + 11 * (weight + 1) + 5) % 101 - 50
        imag_part = (29 * (index + 3) ** 2 + 7 * (weight + 2) + 13) % 103 - 51
        state[bits] = complex(real_part, imag_part)
    return normalize_state(state)


def ghz_state() -> np.ndarray:
    state = np.zeros((2,) * N_QUBITS, dtype=np.complex128)
    state[(0,) * N_QUBITS] = 1.0 / np.sqrt(2.0)
    state[(1,) * N_QUBITS] = 1.0 / np.sqrt(2.0)
    return state


def product_state() -> np.ndarray:
    state = np.zeros((2,) * N_QUBITS, dtype=np.complex128)
    state[(0,) * N_QUBITS] = 1.0
    return state


def tampered_state() -> np.ndarray:
    state = primary_state()
    state[(1, 0, 1, 1, 0, 1)] *= 1.2 * np.exp(0.123j)
    return normalize_state(state)


def padded_descending(values: np.ndarray) -> np.ndarray:
    result = np.sort(np.abs(np.asarray(values, dtype=np.float64)))[::-1]
    return np.pad(result, (0, max(0, MAX_SCHMIDT_RANK - result.size)))[
        :MAX_SCHMIDT_RANK
    ]


def state_checksum(state: np.ndarray) -> dict[str, Any]:
    flat = state.reshape(-1)
    weights = np.arange(1, flat.size + 1, dtype=np.float64)
    magnitudes = np.abs(flat)
    return {
        "weighted_real": float(np.dot(weights, flat.real)),
        "weighted_imag": float(np.dot(weights, flat.imag)),
        "support": int(np.count_nonzero(magnitudes > 1.0e-15)),
        "min_magnitude": float(np.min(magnitudes)),
        "max_magnitude": float(np.max(magnitudes)),
        "magnitude_spread": float(np.max(magnitudes) - np.min(magnitudes)),
        "selected_amplitudes": {
            str(index): {
                "real": float(flat[index].real),
                "imag": float(flat[index].imag),
            }
            for index in (0, 37, 63)
        },
    }


def measure_with_quimb(state: np.ndarray) -> dict[str, Any]:
    mps = qtn.MatrixProductState.from_dense(
        state,
        dims=[2] * N_QUBITS,
        cutoff=0.0,
        max_bond=MAX_SCHMIDT_RANK,
    )
    norm_squared = complex(mps.H @ mps)
    reconstructed = np.asarray(mps.to_dense()).reshape(state.shape)
    reconstruction_error = float(np.max(np.abs(reconstructed - state)))

    singular_values = padded_descending(mps.singular_values(CUT))
    probabilities = singular_values**2
    entropy_bits = float(mps.entropy(CUT))
    positive = probabilities > 0.0
    entropy_nats = float(-np.sum(probabilities[positive] * np.log(probabilities[positive])))

    dense_singular_values = padded_descending(
        np.linalg.svd(
            state.reshape(2**CUT, 2 ** (N_QUBITS - CUT)),
            compute_uv=False,
        )
    )
    return {
        "state_checksum": state_checksum(state),
        "mps_norm_squared": {
            "real": float(norm_squared.real),
            "imag": float(norm_squared.imag),
        },
        "mps_bond_dimensions": [int(value) for value in mps.bond_sizes()],
        "mps_reconstruction_max_abs_error": reconstruction_error,
        "mps_singular_values": singular_values.tolist(),
        "schmidt_probabilities": probabilities.tolist(),
        "entropy_bits": entropy_bits,
        "entropy_nats": entropy_nats,
        "dense_oracle_singular_values": dense_singular_values.tolist(),
        "mps_vs_dense_spectrum_max_abs": float(
            np.max(np.abs(singular_values - dense_singular_values))
        ),
    }


def python_dimension_negative_control() -> dict[str, Any]:
    try:
        qtn.MatrixProductState.from_dense(
            primary_state(),
            dims=[2] * (N_QUBITS - 1),
            cutoff=0.0,
            max_bond=MAX_SCHMIDT_RANK,
        )
    except Exception as error:  # The exception class/message are part of the receipt.
        return {
            "rejected": True,
            "exception_type": type(error).__name__,
            "message": str(error),
        }
    return {
        "rejected": False,
        "exception_type": None,
        "message": "wrong-site-count input was unexpectedly accepted",
    }


def max_abs(left: list[float], right: list[float]) -> float:
    return float(
        np.max(np.abs(np.asarray(left, dtype=np.float64) - np.asarray(right, dtype=np.float64)))
    )


def checksum_max_abs(left: dict[str, Any], right: dict[str, Any]) -> float:
    values = [
        abs(float(left["weighted_real"]) - float(right["weighted_real"])),
        abs(float(left["weighted_imag"]) - float(right["weighted_imag"])),
        abs(float(left["min_magnitude"]) - float(right["min_magnitude"])),
        abs(float(left["max_magnitude"]) - float(right["max_magnitude"])),
        abs(float(left["magnitude_spread"]) - float(right["magnitude_spread"])),
        abs(int(left["support"]) - int(right["support"])),
    ]
    for index in ("0", "37", "63"):
        values.append(
            abs(
                float(left["selected_amplitudes"][index]["real"])
                - float(right["selected_amplitudes"][index]["real"])
            )
        )
        values.append(
            abs(
                float(left["selected_amplitudes"][index]["imag"])
                - float(right["selected_amplitudes"][index]["imag"])
            )
        )
    return float(max(values))


def run_julia() -> tuple[dict[str, Any] | None, dict[str, Any]]:
    command = [
        str(JULIA_BIN),
        "--startup-file=no",
        "--threads=1",
        f"--project={JULIA_PROJECT}",
        str(JULIA_SOURCE),
    ]
    environment = os.environ.copy()
    environment["JULIA_LOAD_PATH"] = "@:@stdlib"
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        env=environment,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    duration = time.perf_counter() - started
    execution = {
        "command": shlex.join(command),
        "environment_overrides": {"JULIA_LOAD_PATH": "@:@stdlib"},
        "exit_code": completed.returncode,
        "duration_seconds": duration,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "stderr": completed.stderr,
    }
    if completed.returncode != 0:
        execution["stdout"] = completed.stdout
        return None, execution
    try:
        parsed = json.loads(completed.stdout.strip())
    except json.JSONDecodeError as error:
        execution["stdout"] = completed.stdout
        execution["parse_error"] = str(error)
        return None, execution
    return parsed, execution


def build_checks(
    python_cases: dict[str, dict[str, Any]],
    julia_result: dict[str, Any] | None,
    python_dimension_negative: dict[str, Any],
    julia_source_sha256: str,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    checks: dict[str, dict[str, Any]] = {}

    def record(name: str, passed: bool, **details: Any) -> None:
        checks[name] = {"pass": bool(passed), **details}

    actual_python = Path(sys.executable).resolve()
    canonical_python = CANONICAL_PYTHON_ALIAS.resolve()
    record(
        "canonical_python_runtime",
        actual_python == canonical_python,
        requested_alias=str(CANONICAL_PYTHON_ALIAS),
        actual_executable=sys.executable,
        actual_physical=str(actual_python),
        expected_physical=str(canonical_python),
    )
    record(
        "julia_leg_returned_json",
        julia_result is not None,
    )

    primary = python_cases["primary"]
    witness = primary["state_checksum"]
    non_stabilizer_witness = (
        witness["support"] == 2**N_QUBITS
        and witness["min_magnitude"] > 0.0
        and witness["magnitude_spread"] > 0.1
    )
    record(
        "primary_is_full_support_unequal_magnitude_fixture",
        non_stabilizer_witness,
        support=witness["support"],
        expected_support=2**N_QUBITS,
        min_magnitude=witness["min_magnitude"],
        magnitude_spread=witness["magnitude_spread"],
        rationale=(
            "A full-support computational-basis stabilizer state must have equal "
            "nonzero magnitudes; the fixed fixture violates that necessary condition."
        ),
    )
    record(
        "python_quimb_primary_matches_dense_oracle",
        primary["mps_vs_dense_spectrum_max_abs"] < TOLERANCE,
        observed=primary["mps_vs_dense_spectrum_max_abs"],
        tolerance=TOLERANCE,
    )
    record(
        "python_quimb_primary_reconstructs_state",
        primary["mps_reconstruction_max_abs_error"] < TOLERANCE,
        observed=primary["mps_reconstruction_max_abs_error"],
        tolerance=TOLERANCE,
    )
    record(
        "python_quimb_wrong_dimension_rejected",
        python_dimension_negative["rejected"],
        receipt=python_dimension_negative,
    )

    comparison: dict[str, Any] = {}
    if julia_result is None:
        return checks, comparison

    julia_runtime = julia_result["runtime"]
    julia_cases = julia_result["cases"]
    record(
        "julia_carrier_project_exact",
        Path(julia_runtime["active_project"]).resolve()
        == (JULIA_PROJECT / "Project.toml").resolve(),
        observed=julia_runtime["active_project"],
        expected=str(JULIA_PROJECT / "Project.toml"),
    )
    record(
        "julia_load_path_strict",
        julia_runtime["load_path"] == ["@", "@stdlib"],
        observed=julia_runtime["load_path"],
        expected=["@", "@stdlib"],
    )
    record(
        "julia_source_hash_matches_runner",
        julia_result["source_sha256"] == julia_source_sha256,
        julia_reported=julia_result["source_sha256"],
        runner_computed=julia_source_sha256,
    )

    julia_primary = julia_cases["primary"]
    primary_spectrum_delta = max_abs(
        primary["mps_singular_values"], julia_primary["mps_singular_values"]
    )
    primary_probability_delta = max_abs(
        primary["schmidt_probabilities"], julia_primary["schmidt_probabilities"]
    )
    primary_entropy_delta = abs(primary["entropy_bits"] - julia_primary["entropy_bits"])
    primary_checksum_delta = checksum_max_abs(
        primary["state_checksum"], julia_primary["state_checksum"]
    )
    comparison["primary"] = {
        "singular_spectrum_max_abs_delta": primary_spectrum_delta,
        "schmidt_probability_max_abs_delta": primary_probability_delta,
        "entropy_bits_abs_delta": primary_entropy_delta,
        "state_checksum_max_abs_delta": primary_checksum_delta,
    }
    record(
        "independent_primary_fixture_generation_matches",
        primary_checksum_delta < TOLERANCE,
        observed=primary_checksum_delta,
        tolerance=TOLERANCE,
    )
    record(
        "julia_itensors_primary_matches_dense_oracle",
        julia_primary["mps_vs_dense_spectrum_max_abs"] < TOLERANCE,
        observed=julia_primary["mps_vs_dense_spectrum_max_abs"],
        tolerance=TOLERANCE,
    )
    record(
        "julia_itensors_primary_reconstructs_state",
        julia_primary["mps_reconstruction_max_abs_error"] < TOLERANCE,
        observed=julia_primary["mps_reconstruction_max_abs_error"],
        tolerance=TOLERANCE,
    )
    record(
        "primary_nontrivial_schmidt_spectrum",
        sum(value > 1.0e-8 for value in primary["mps_singular_values"])
        == MAX_SCHMIDT_RANK
        and 1.0 < primary["entropy_bits"] < 3.0,
        nonzero_schmidt_rank=sum(
            value > 1.0e-8 for value in primary["mps_singular_values"]
        ),
        entropy_bits=primary["entropy_bits"],
    )
    record(
        "primary_cross_engine_spectrum_and_entropy_agree",
        primary_spectrum_delta < TOLERANCE
        and primary_probability_delta < TOLERANCE
        and primary_entropy_delta < TOLERANCE,
        **comparison["primary"],
        tolerance=TOLERANCE,
    )

    for case_name, expected_entropy, expected_probabilities in (
        ("ghz_control", 1.0, [0.5, 0.5] + [0.0] * 6),
        ("product_control", 0.0, [1.0] + [0.0] * 7),
    ):
        python_case = python_cases[case_name]
        julia_case = julia_cases[case_name]
        probability_delta = max_abs(
            python_case["schmidt_probabilities"], julia_case["schmidt_probabilities"]
        )
        python_expected_delta = max_abs(
            python_case["schmidt_probabilities"], expected_probabilities
        )
        julia_expected_delta = max_abs(
            julia_case["schmidt_probabilities"], expected_probabilities
        )
        entropy_delta = abs(python_case["entropy_bits"] - julia_case["entropy_bits"])
        expected_entropy_delta = max(
            abs(python_case["entropy_bits"] - expected_entropy),
            abs(julia_case["entropy_bits"] - expected_entropy),
        )
        comparison[case_name] = {
            "probability_max_abs_delta": probability_delta,
            "python_expected_probability_delta": python_expected_delta,
            "julia_expected_probability_delta": julia_expected_delta,
            "entropy_bits_abs_delta": entropy_delta,
            "expected_entropy_max_abs_delta": expected_entropy_delta,
        }
        record(
            f"{case_name}_boundary_control",
            max(
                probability_delta,
                python_expected_delta,
                julia_expected_delta,
                entropy_delta,
                expected_entropy_delta,
            )
            < TOLERANCE,
            **comparison[case_name],
            tolerance=TOLERANCE,
        )

    tampered_python = python_cases["tampered"]
    tampered_julia = julia_cases["tampered"]
    tampered_pair_delta = max_abs(
        tampered_python["mps_singular_values"], tampered_julia["mps_singular_values"]
    )
    wrong_pair_delta_python = max_abs(
        primary["mps_singular_values"], tampered_python["mps_singular_values"]
    )
    wrong_pair_delta_julia = max_abs(
        primary["mps_singular_values"], tampered_julia["mps_singular_values"]
    )
    comparison["tampered_state_negative"] = {
        "tampered_cross_engine_max_abs_delta": tampered_pair_delta,
        "untampered_vs_python_tampered_max_abs_delta": wrong_pair_delta_python,
        "untampered_vs_julia_tampered_max_abs_delta": wrong_pair_delta_julia,
    }
    record(
        "tampered_state_wrong_pair_is_detected",
        tampered_pair_delta < TOLERANCE
        and wrong_pair_delta_python > TAMPER_DETECTION_FLOOR
        and wrong_pair_delta_julia > TAMPER_DETECTION_FLOOR,
        **comparison["tampered_state_negative"],
        agreement_tolerance=TOLERANCE,
        detection_floor=TAMPER_DETECTION_FLOOR,
    )

    direct_unit_mismatch = abs(primary["entropy_bits"] - julia_primary["entropy_nats"])
    converted_unit_delta = abs(
        primary["entropy_bits"] - julia_primary["entropy_nats"] / np.log(2.0)
    )
    comparison["entropy_unit_negative"] = {
        "direct_bits_vs_nats_abs_delta": direct_unit_mismatch,
        "nats_div_log2_vs_bits_abs_delta": converted_unit_delta,
    }
    record(
        "bit_vs_nat_convention_mismatch_is_detected_and_repaired",
        direct_unit_mismatch > 0.1 and converted_unit_delta < TOLERANCE,
        **comparison["entropy_unit_negative"],
        mismatch_floor=0.1,
        converted_tolerance=TOLERANCE,
    )
    record(
        "julia_itensors_wrong_dimension_rejected",
        julia_result["dimension_negative"]["rejected"],
        receipt=julia_result["dimension_negative"],
    )
    return checks, comparison


def tool_calls() -> list[dict[str, Any]]:
    return [
        {
            "tool": "quimb",
            "qualified_api": "quimb.tensor.MatrixProductState.from_dense",
            "input_object": "independently generated complex128 2x2x2x2x2x2 state",
            "output_object": "six-site MatrixProductState with explicit bond dimensions",
            "positive_case": "full-support unequal-magnitude deterministic primary fixture",
            "negative_or_erased_control": "wrong five-site dims must raise ValueError",
            "boundary_case": "GHZ and product fixtures",
            "demotion_condition": "dimension input accepted, reconstruction fails, or dense-oracle spectrum diverges",
            "gates": [
                "python_quimb_primary_reconstructs_state",
                "python_quimb_primary_matches_dense_oracle",
                "python_quimb_wrong_dimension_rejected",
                "all_pass",
            ],
            "load_bearing": True,
        },
        {
            "tool": "quimb",
            "qualified_api": "MatrixProductState.singular_values and MatrixProductState.entropy",
            "input_object": "quimb MPS at the 3|3 cut",
            "output_object": "Schmidt singular spectrum and base-2 entropy",
            "positive_case": "rank-eight nontrivial primary spectrum",
            "negative_or_erased_control": "untampered spectrum compared to independently regenerated tampered state",
            "boundary_case": "one-ebit GHZ and zero-ebit product",
            "demotion_condition": "cross-engine or exact-boundary comparison exceeds tolerance",
            "gates": [
                "primary_cross_engine_spectrum_and_entropy_agree",
                "tampered_state_wrong_pair_is_detected",
                "ghz_control_boundary_control",
                "product_control_boundary_control",
                "all_pass",
            ],
            "load_bearing": True,
        },
        {
            "tool": "ITensors/ITensorMPS",
            "qualified_api": "ITensorMPS.MPS(::AbstractArray, sites), inner, contract, orthogonalize!",
            "input_object": "Julia-regenerated ComplexF64 2x2x2x2x2x2 state and Qubit site indices",
            "output_object": "six-site MPS, norm, reconstructed dense state, and orthogonality center",
            "positive_case": "full-support unequal-magnitude deterministic primary fixture",
            "negative_or_erased_control": "five-site Index set must raise DimensionMismatch",
            "boundary_case": "GHZ and product fixtures",
            "demotion_condition": "wrong-dimension input accepted or reconstruction exceeds tolerance",
            "gates": [
                "julia_itensors_primary_reconstructs_state",
                "julia_itensors_wrong_dimension_rejected",
                "all_pass",
            ],
            "load_bearing": True,
        },
        {
            "tool": "ITensors",
            "qualified_api": "ITensors.svd(::ITensor, left_indices; cutoff=0.0, maxdim=8)",
            "input_object": "orthogonalized site-3 MPS tensor split by left-link plus physical index",
            "output_object": "rank-at-most-eight Schmidt singular tensor",
            "positive_case": "rank-eight nontrivial primary spectrum",
            "negative_or_erased_control": "tampered-state wrong-pair comparison must exceed detection floor",
            "boundary_case": "exactly degenerate GHZ and rank-one product spectra",
            "demotion_condition": "dense oracle, cross-engine, or control comparison exceeds tolerance",
            "gates": [
                "julia_itensors_primary_matches_dense_oracle",
                "primary_cross_engine_spectrum_and_entropy_agree",
                "tampered_state_wrong_pair_is_detected",
                "all_pass",
            ],
            "load_bearing": True,
        },
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_RESULT,
        help="Result JSON path (defaults beside this source file).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started_at = utc_now()
    started_timer = time.perf_counter()
    observed_invocation = shlex.join([sys.executable, *sys.argv])

    python_cases = {
        "primary": measure_with_quimb(primary_state()),
        "tampered": measure_with_quimb(tampered_state()),
        "ghz_control": measure_with_quimb(ghz_state()),
        "product_control": measure_with_quimb(product_state()),
    }
    python_dimension_negative = python_dimension_negative_control()
    julia_result, julia_execution = run_julia()
    julia_source_sha256 = sha256_file(JULIA_SOURCE)
    checks, comparison = build_checks(
        python_cases,
        julia_result,
        python_dimension_negative,
        julia_source_sha256,
    )
    all_pass = bool(checks) and all(check["pass"] for check in checks.values())
    finished_at = utc_now()

    python_command = shlex.join(
        [str(CANONICAL_PYTHON_ALIAS), str(Path(__file__).resolve()), "--output", str(args.output)]
    )
    runtime_manifest = {
        "python": {
            "requested_alias": str(CANONICAL_PYTHON_ALIAS),
            "sys_executable": sys.executable,
            "physical_executable": str(Path(sys.executable).resolve()),
            "version": sys.version,
            "platform": platform.platform(),
            "packages": {
                "quimb": {
                    "version": quimb.__version__,
                    "module_path": quimb.__file__,
                    "tensor_module_path": qtn.__file__,
                },
                "numpy": {
                    "version": np.__version__,
                    "module_path": np.__file__,
                    "role": "dense finite oracle and receipt arithmetic; not the tensor-network tool",
                },
            },
            "numba_cache_dir": os.environ.get("NUMBA_CACHE_DIR"),
        },
        "julia": julia_result["runtime"] if julia_result is not None else None,
        "known_blocked_packages_skipped": [
            "dgl",
            "torch_scatter",
            "torch_sparse",
            "bayeux",
        ],
        "package_install_performed": False,
        "active_installer_state": "not_started_by_this_worker",
        "repo_pollution_added": False,
    }

    result = {
        "schema": "codex-ratchet.gap-k-tensor-chain-result.v2",
        "schema_version": "gap_k_tensor_chain_v2_result_v1",
        "sim_id": "gap_k_tensor_chain_v2",
        "name": "Hardened cross-runtime MPS Schmidt-chain fit diagnostic",
        "version": "2.0.0",
        "tier": "tool_stage_pre_lego",
        "purpose": "Test real quimb and ITensors/ITensorMPS MPS APIs on independently generated finite fixtures.",
        "packages_used": ["quimb", "ITensors", "ITensorMPS"],
        "scientific_question": "Do the two concrete tensor-network API paths agree on one nontrivial fixed 6-qubit Schmidt spectrum while rejecting named convention, state, and dimension mistakes?",
        "sim_execution_kind": "classical",
        "sim_class": "tool_lego_fit_probe",
        "classification": "tool_lego_fit_probe",
        "promotion_status": "diagnostic_only",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "created_at": started_at,
        "command": [
            str(CANONICAL_PYTHON_ALIAS),
            str(Path(__file__).resolve()),
            "--output",
            str(args.output.resolve()),
        ],
        "runner_identity": runtime_manifest,
        "source": {
            "python_path": str(Path(__file__).resolve()),
            "python_sha256": sha256_file(Path(__file__).resolve()),
            "julia_path": str(JULIA_SOURCE),
            "julia_sha256": julia_source_sha256,
        },
        "status_label": "passes local rerun" if all_pass else "runs",
        "allowed_claims": [
            "A fresh local rerun exercised the named quimb and ITensors/ITensorMPS functions.",
            "For the fixed primary and boundary fixtures, the MPS-derived spectra and entropies met the recorded tolerances.",
            "The named unit, state-tamper, and dimension controls demoted incorrect comparisons when all_pass is true.",
        ],
        "claim_ceiling": (
            "Fixed-fixture function-level tensor-tool fit diagnostic only. This result does not prove "
            "general quimb/ITensors equivalence, numerical soundness for arbitrary states, Julia "
            "Canon admission, tensor-network science, ratchet dynamics, cosmogenesis, a bridge, an "
            "Axis, a basin, a manifold, or any physics claim."
        ),
        "blocked_consumers": [
            "scientific-canon claims",
            "Julia-Canon admission",
            "general engine-equivalence claims",
            "bridge or Axis claims",
            "basin or manifold claims",
            "ratchet/cosmogenesis/physics promotion",
        ],
        "eligible_consumers": [
            "bounded tool-status audit",
            "future preregistration design",
            "negative-control regression suite",
        ],
        "runner": {
            "started_at_utc": started_at,
            "finished_at_utc": finished_at,
            "duration_seconds": time.perf_counter() - started_timer,
            "cwd": str(Path.cwd()),
            "host": platform.node(),
            "observed_invocation": observed_invocation,
            "reproduction_command": python_command,
        },
        "commands": {
            "python_observed": observed_invocation,
            "python_controller": python_command,
            "julia_leg": julia_execution["command"],
            "julia_environment_overrides": julia_execution["environment_overrides"],
        },
        "source_files": {
            "python": {
                "path": str(Path(__file__).resolve()),
                "sha256": sha256_file(Path(__file__).resolve()),
            },
            "julia": {
                "path": str(JULIA_SOURCE),
                "sha256": julia_source_sha256,
            },
        },
        "runtime_manifest": runtime_manifest,
        "state_generation": {
            "primary": {
                "qubits": N_QUBITS,
                "cut": "3|3",
                "formula": "a_k=((37(k+1)^2+11(w+1)+5) mod 101-50)+i*((29(k+3)^2+7(w+2)+13) mod 103-51), then L2 normalize",
                "why_not_textbook": "It is dense and uses a fixed nonuniform complex coefficient formula, not a named GHZ/product/stabilizer fixture.",
                "non_stabilizer_necessary_condition_witness": "Full computational-basis support plus unequal nonzero magnitudes rules out a stabilizer state.",
            },
            "state_exchange": "none; Python and Julia independently regenerate every fixture",
            "cross_runtime_exchange": "Julia returns only versioned JSON diagnostics; no tensor is copied across runtimes",
        },
        "python_cases": python_cases,
        "julia_leg": julia_result,
        "julia_execution": julia_execution,
        "python_dimension_negative": python_dimension_negative,
        "comparison": comparison,
        "negative_controls": {
            "tampered_state": "Both engines agree on the tampered state, while an untampered-vs-tampered pairing must exceed the detection floor.",
            "entropy_units": "A direct bit-vs-nat comparison must fail; explicit division by ln(2) must recover agreement.",
            "wrong_dimension": "Both MPS constructors must reject a six-qubit array paired with five site dimensions.",
        },
        "boundary_controls": {
            "ghz": "Exactly two Schmidt probabilities of 1/2 and entropy 1 bit.",
            "product": "Exactly one Schmidt probability of 1 and entropy 0 bits.",
        },
        "tool_manifest": [
            {
                "tool": "quimb",
                "status": "claim_load_bearing" if all_pass else "function_call_failed_or_demoted",
                "reason": "MPS construction, reconstruction, Schmidt spectrum, entropy, and dimension rejection gate all_pass.",
            },
            {
                "tool": "ITensors/ITensorMPS",
                "status": "claim_load_bearing" if all_pass else "function_call_failed_or_demoted",
                "reason": "Julia MPS construction, contraction, canonicalization, SVD, and dimension rejection gate all_pass.",
            },
        ],
        "tool_integration_depth": {
            "quimb": "function-level with positive, negative, and boundary gates",
            "ITensors/ITensorMPS": "function-level with positive, negative, and boundary gates",
        },
        "tool_calls": tool_calls(),
        "checks": checks,
        "check_summary": {
            "passed": sum(check["pass"] for check in checks.values()),
            "failed": sum(not check["pass"] for check in checks.values()),
            "total": len(checks),
        },
        "witness_trace": [
            "Python independently generated primary/tampered/GHZ/product dense states.",
            "quimb converted each state to MPS and derived reconstruction, norm, Schmidt spectrum, and entropy.",
            "A strict Julia carrier process independently regenerated the same fixtures.",
            "ITensorMPS converted each Julia array to MPS; ITensors SVD derived the 3|3 Schmidt spectrum.",
            "Each MPS spectrum was checked against a same-runtime dense finite SVD oracle.",
            "Cross-runtime spectra, probabilities, and explicitly base-2 entropies were compared.",
            "GHZ/product boundaries, state tamper, unit mismatch, and dimension rejection gated all_pass.",
        ],
        "artifacts_emitted": [str(args.output.resolve())],
        "all_pass": all_pass,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "result": str(args.output.resolve()),
                "all_pass": all_pass,
                "passed": result["check_summary"]["passed"],
                "failed": result["check_summary"]["failed"],
                "total": result["check_summary"]["total"],
                "primary_entropy_bits": python_cases["primary"]["entropy_bits"],
                "primary_spectrum_max_abs_delta": comparison.get("primary", {}).get(
                    "singular_spectrum_max_abs_delta"
                ),
            },
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
