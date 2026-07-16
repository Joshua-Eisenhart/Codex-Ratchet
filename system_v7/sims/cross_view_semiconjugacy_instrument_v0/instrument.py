#!/usr/bin/env python3
"""Finite cross-view semiconjugacy instrument for the contract Fe operation.

This is a deterministic classical scratch diagnostic.  It reimplements the
read-only oracle's Fe unitary locally, evaluates three finite projections by
one common induced-map pipeline, and appends one immutable JSON record per run.
"""

from __future__ import annotations

import json
import math
import os

import numpy as np


# Frozen before execution.  These values are specification, not fitted data.
SEED = 0
N_DIRECTIONS = 4096
RADII = (0.25, 0.5, 0.75, 0.99)
N_SECTORS = 8
SECTOR_WIDTH = math.pi / 4.0
EXPECTED_TH = math.pi / 4.0
EXPECTED_Q = 0.6321205588285577
DEFECT_TOLERANCE = 1.0e-3
MIN_INFORMATION_BITS = 1.0
BAD_CONTROL_MIN_DEFECT = 0.25
BOUNDARY_EPS_RADIANS = 1.0e-9
MAX_BOUNDARY_EXCLUDED_FRACTION = 1.0e-3
FE_CROSSCHECK_TOLERANCE = 1.0e-12
FE_CROSSCHECK_STATES = 16
EXPECTED_GOOD_T_D = list(range(1, N_SECTORS)) + [0]

# Repo contract metadata.  The scratch fences deliberately block promotion.
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "numpy": {
        "used": True,
        "reason": "load-bearing exhaustive finite dynamics, partition fitting, defect measurement, and density-matrix cross-check",
    },
    "constraint_core_import": {
        "used": False,
        "reason": "forbidden by CARD; Fe is reimplemented locally while frozen constants are read from targets.json",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "constraint_core_import": None,
}

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TARGETS_PATH = os.path.join(
    REPO_ROOT, "system_v7", "constraint_core", "engines", "targets.json"
)
RESULTS_PATH = os.path.join(HERE, "results_v1.json")


def load_frozen_constants() -> tuple[float, float]:
    """Read the frozen target constants without importing constraint_core."""

    with open(TARGETS_PATH, "r", encoding="utf-8") as handle:
        targets = json.load(handle)
    constants = targets["model_constants"]
    th = float(constants["TH"])
    q = float(constants["Q"])
    if th != EXPECTED_TH:
        raise RuntimeError(f"frozen TH mismatch: {th!r} != {EXPECTED_TH!r}")
    if q != EXPECTED_Q:
        raise RuntimeError(f"frozen Q mismatch: {q!r} != {EXPECTED_Q!r}")
    return th, q


def fibonacci_bloch_sample() -> np.ndarray:
    """Return the exhaustive frozen 4096-direction by four-radius sample."""

    # Required deterministic RNG declaration.  The grid itself is nonrandom.
    _rng = np.random.default_rng(SEED)
    if _rng.bit_generator.__class__.__name__ != "PCG64":
        raise RuntimeError("unexpected NumPy default RNG implementation")

    indices = np.arange(N_DIRECTIONS, dtype=np.float64)
    z = 1.0 - 2.0 * (indices + 0.5) / float(N_DIRECTIONS)
    radial_xy = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    golden_angle = math.pi * (3.0 - math.sqrt(5.0))
    azimuth = golden_angle * indices
    directions = np.column_stack(
        (radial_xy * np.cos(azimuth), radial_xy * np.sin(azimuth), z)
    )
    states = np.concatenate([radius * directions for radius in RADII], axis=0)
    expected_shape = (N_DIRECTIONS * len(RADII), 3)
    if states.shape != expected_shape:
        raise RuntimeError(f"sample shape {states.shape!r} != {expected_shape!r}")
    return states


def fe_bloch(states: np.ndarray, th: float) -> np.ndarray:
    """Apply the Fe Bloch map: active rotation by th about the z axis."""

    c = math.cos(th)
    s = math.sin(th)
    out = np.empty_like(states, dtype=np.float64)
    out[:, 0] = c * states[:, 0] - s * states[:, 1]
    out[:, 1] = s * states[:, 0] + c * states[:, 1]
    out[:, 2] = states[:, 2]
    return out


def bloch_to_density(state: np.ndarray) -> np.ndarray:
    x, y, z = (float(value) for value in state)
    return 0.5 * np.array(
        [[1.0 + z, x - 1j * y], [x + 1j * y, 1.0 - z]],
        dtype=np.complex128,
    )


def density_to_bloch(density: np.ndarray) -> np.ndarray:
    return np.array(
        [
            2.0 * density[0, 1].real,
            -2.0 * density[0, 1].imag,
            (density[0, 0] - density[1, 1]).real,
        ],
        dtype=np.float64,
    )


def verify_fe_density_matrix(states: np.ndarray, th: float) -> dict[str, object]:
    """Cross-check the Bloch rotation against local U rho U-dagger."""

    check_indices = np.linspace(
        0, states.shape[0] - 1, FE_CROSSCHECK_STATES, dtype=np.int64
    )
    selected = states[check_indices]
    expected = fe_bloch(selected, th)
    identity = np.eye(2, dtype=np.complex128)
    sigma_z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    unitary = math.cos(th / 2.0) * identity - 1j * math.sin(th / 2.0) * sigma_z
    observed = []
    for state in selected:
        density = bloch_to_density(state)
        transformed = unitary @ density @ unitary.conj().T
        observed.append(density_to_bloch(transformed))
    observed_array = np.asarray(observed, dtype=np.float64)
    errors = np.linalg.norm(observed_array - expected, axis=1)
    max_error = float(np.max(errors))
    passed = max_error <= FE_CROSSCHECK_TOLERANCE
    if not passed:
        raise RuntimeError(
            "Fe density-matrix cross-check failed: "
            f"{max_error:.17g} > {FE_CROSSCHECK_TOLERANCE:.17g}"
        )
    return {
        "n_states": int(selected.shape[0]),
        "max_bloch_l2_error": max_error,
        "tolerance": FE_CROSSCHECK_TOLERANCE,
        "passed": passed,
    }


def candidate_angles(states: np.ndarray, candidate: str) -> np.ndarray | None:
    if candidate == "good_z_axis_fan":
        raw = np.arctan2(states[:, 1], states[:, 0])
    elif candidate == "bad_x_axis_fan":
        raw = np.arctan2(states[:, 2], states[:, 1])
    elif candidate == "trivial_constant":
        return None
    else:
        raise ValueError(f"unknown candidate {candidate!r}")
    return np.mod(raw, 2.0 * math.pi)


def boundary_mask(angles: np.ndarray | None) -> np.ndarray:
    if angles is None:
        return np.zeros(0, dtype=bool)
    phase = np.mod(angles, SECTOR_WIDTH)
    distance = np.minimum(phase, SECTOR_WIDTH - phase)
    return distance <= BOUNDARY_EPS_RADIANS


def cells_from_angles(angles: np.ndarray | None, n_states: int) -> np.ndarray:
    if angles is None:
        return np.zeros(n_states, dtype=np.int64)
    return np.floor(angles / SECTOR_WIDTH).astype(np.int64) % N_SECTORS


def occupancy_entropy_bits(cells: np.ndarray, n_cells: int) -> float:
    counts = np.bincount(cells, minlength=n_cells).astype(np.float64)
    probabilities = counts[counts > 0.0] / float(cells.size)
    if probabilities.size <= 1:
        return 0.0
    return float(-np.sum(probabilities * np.log2(probabilities)))


def evaluate_candidate(
    name: str,
    states: np.ndarray,
    transformed_states: np.ndarray,
    n_cells: int,
) -> dict[str, object]:
    """Fit T_d by per-cell mode and measure every candidate identically."""

    source_angles = candidate_angles(states, name)
    target_angles = candidate_angles(transformed_states, name)
    if source_angles is None:
        excluded = np.zeros(states.shape[0], dtype=bool)
    else:
        # Q appears on both sides of the tested equality, so either near-edge
        # evaluation is excluded under the candidate's own angular coordinate.
        excluded = boundary_mask(source_angles) | boundary_mask(target_angles)
    eligible = ~excluded
    n_eligible = int(np.count_nonzero(eligible))
    if n_eligible == 0:
        raise RuntimeError(f"candidate {name} excluded every sample state")

    source_cells_all = cells_from_angles(source_angles, states.shape[0])
    target_cells_all = cells_from_angles(target_angles, states.shape[0])
    source_cells = source_cells_all[eligible]
    target_cells = target_cells_all[eligible]

    induced = np.full(n_cells, -1, dtype=np.int64)
    occupied_cells = []
    for cell in range(n_cells):
        in_cell = source_cells == cell
        if np.any(in_cell):
            counts = np.bincount(target_cells[in_cell], minlength=n_cells)
            induced[cell] = int(np.argmax(counts))
            occupied_cells.append(cell)

    predicted = induced[source_cells]
    mismatches = predicted != target_cells
    defect_fraction = float(np.mean(mismatches))
    per_cell_mismatch = {
        str(cell): float(np.mean(mismatches[source_cells == cell]))
        for cell in occupied_cells
    }
    worst_cell_mismatch = max(per_cell_mismatch.values(), default=0.0)
    information_bits = occupancy_entropy_bits(source_cells, n_cells)
    n_excluded = int(np.count_nonzero(excluded))
    excluded_fraction = n_excluded / float(states.shape[0])
    boundary_exclusion_ok = excluded_fraction < MAX_BOUNDARY_EXCLUDED_FRACTION
    accepted = (
        defect_fraction <= DEFECT_TOLERANCE
        and information_bits >= MIN_INFORMATION_BITS
        and boundary_exclusion_ok
    )

    result: dict[str, object] = {
        "defect_fraction": defect_fraction,
        "worst_cell_mismatch": worst_cell_mismatch,
        "information_retained_bits": information_bits,
        "n_excluded_boundary": n_excluded,
        "excluded_boundary_fraction": excluded_fraction,
        "boundary_exclusion_ok": boundary_exclusion_ok,
        "n_evaluated": n_eligible,
        "n_cells": n_cells,
        "n_occupied_cells": len(occupied_cells),
        "per_cell_mismatch": per_cell_mismatch,
        "accept": bool(accepted),
    }
    if name == "good_z_axis_fan":
        table = [int(value) for value in induced]
        shifts = [int((table[cell] - cell) % n_cells) for cell in range(n_cells)]
        is_cyclic_shift = (
            all(value >= 0 for value in table)
            and len(set(shifts)) == 1
            and shifts[0] != 0
        )
        result["recovered_T_d"] = table
        result["cyclic_shift"] = shifts[0] if is_cyclic_shift else None
        result["is_cyclic_shift"] = bool(is_cyclic_shift)
        result["expected_T_d"] = EXPECTED_GOOD_T_D
        result["is_expected_T_d"] = table == EXPECTED_GOOD_T_D
    return result


def read_existing_records() -> list[dict[str, object]]:
    if not os.path.exists(RESULTS_PATH):
        return []
    records = []
    with open(RESULTS_PATH, "r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise RuntimeError(
                    f"refusing to append after malformed result line {line_number}"
                ) from error
            if not isinstance(record, dict):
                raise RuntimeError(f"result line {line_number} is not a JSON object")
            records.append(record)
    return records


def scientific_payload(record: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in record.items() if key != "run_receipt"}


def append_record(record: dict[str, object]) -> None:
    encoded = (
        json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")
    descriptor = os.open(
        RESULTS_PATH, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644
    )
    try:
        written = 0
        while written < len(encoded):
            chunk_size = os.write(descriptor, encoded[written:])
            if chunk_size <= 0:
                raise RuntimeError(
                    f"append stopped after {written} of {len(encoded)} bytes"
                )
            written += chunk_size
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def build_record() -> dict[str, object]:
    th, q = load_frozen_constants()
    states = fibonacci_bloch_sample()
    transformed = fe_bloch(states, th)
    fe_crosscheck = verify_fe_density_matrix(states, th)

    candidates = {
        "good": evaluate_candidate(
            "good_z_axis_fan", states, transformed, N_SECTORS
        ),
        "bad": evaluate_candidate(
            "bad_x_axis_fan", states, transformed, N_SECTORS
        ),
        "trivial": evaluate_candidate(
            "trivial_constant", states, transformed, 1
        ),
    }
    good = candidates["good"]
    bad = candidates["bad"]
    trivial = candidates["trivial"]

    good_accepted = bool(good["accept"] and good["is_expected_T_d"])
    bad_rejected = bool(bad["defect_fraction"] > BAD_CONTROL_MIN_DEFECT)
    bad_control_fired = bool(
        bad["defect_fraction"] > BAD_CONTROL_MIN_DEFECT
    )
    trivial_flagged = bool(
        not trivial["accept"]
        and trivial["defect_fraction"] <= DEFECT_TOLERANCE
        and trivial["information_retained_bits"] == 0.0
    )
    all_boundary_exclusions_ok = all(
        bool(candidate["boundary_exclusion_ok"])
        for candidate in candidates.values()
    )
    instrument_pass = bool(
        fe_crosscheck["passed"]
        and good_accepted
        and bad_rejected
        and bad_control_fired
        and trivial_flagged
        and all_boundary_exclusions_ok
    )

    return {
        "schema_version": "semiconjugacy_instrument_result_v1",
        "sim_id": "cross_view_semiconjugacy_instrument_v0",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "accepted_status_ceiling": "passes local rerun",
        "engine_contract": {
            "mode": "classical_numpy_finite_exhaustive",
            "semantic_source": "read-only oracle Fe construction",
            "cross_runtime_claim": False,
        },
        "source_contract": {
            "targets_path": TARGETS_PATH,
            "oracle_reference_path": os.path.join(
                REPO_ROOT,
                "system_v7",
                "constraint_core",
                "engines",
                "oracle_targets.py",
            ),
            "TH": th,
            "Q": q,
            "Fe": "U=exp(-i*TH*sz/2); rho maps to U rho U_dagger",
        },
        "frozen_acceptance_rule": {
            "declared_before_run": True,
            "defect_fraction_max": DEFECT_TOLERANCE,
            "information_retained_bits_min": MIN_INFORMATION_BITS,
            "bad_control_defect_min_exclusive": BAD_CONTROL_MIN_DEFECT,
            "boundary_epsilon_radians": BOUNDARY_EPS_RADIANS,
            "excluded_fraction_max_exclusive": MAX_BOUNDARY_EXCLUDED_FRACTION,
        },
        "sample": {
            "seed": SEED,
            "rng_declared": "np.random.default_rng(0)",
            "grid": "Fibonacci sphere",
            "n_directions": N_DIRECTIONS,
            "radii": list(RADII),
            "n_states": int(states.shape[0]),
        },
        "Fe_density_matrix_crosscheck": fe_crosscheck,
        "pipeline": {
            "common_to_all_candidates": True,
            "T_d_fit": "mode of Q(Tx) over eligible x in source cell",
            "mode_tie_policy": "np.argmax chooses the lowest target-cell index",
            "defect": "fraction of eligible states with Q(Tx) != T_d(Qx)",
            "worst_cell_mismatch_reported": True,
            "boundary_policy": "exclude when Q(x) or Q(Tx) lies within candidate-local epsilon of a boundary",
        },
        "candidates": candidates,
        "good_accepted": good_accepted,
        "bad_rejected": bad_rejected,
        "bad_control_fired": bad_control_fired,
        "trivial_flagged": trivial_flagged,
        "all_boundary_exclusions_ok": all_boundary_exclusions_ok,
        "instrument_pass": instrument_pass,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [
            "classical finite diagnostic only",
            "no cross-runtime parity claim",
            "no formal proof or canonical admission claim",
        ],
        "blocked_consumers": [
            "canonical sim admission",
            "bridge or axis claims",
            "physics or manifold claims",
            "cross-runtime agreement claims",
        ],
    }


def print_headlines(record: dict[str, object]) -> None:
    candidates = record["candidates"]
    tolerance = record["frozen_acceptance_rule"]["defect_fraction_max"]
    print(f"defect_tolerance={tolerance:.12g}")
    for label in ("good", "bad", "trivial"):
        result = candidates[label]
        print(
            f"{label.upper()} defect={result['defect_fraction']:.12g} "
            f"worst_cell_mismatch={result['worst_cell_mismatch']:.12g} "
            f"information_retained_bits={result['information_retained_bits']:.12g}"
        )
    print(
        "outcomes "
        f"good_accepted={record['good_accepted']} "
        f"bad_rejected={record['bad_rejected']} "
        f"bad_control_fired={record['bad_control_fired']} "
        f"trivial_flagged={record['trivial_flagged']} "
        f"instrument_pass={record['instrument_pass']}"
    )


def main() -> int:
    existing = read_existing_records()
    record = build_record()
    payload = scientific_payload(record)
    previous_payload = scientific_payload(existing[-1]) if existing else None
    record["run_receipt"] = {
        "run_index": len(existing) + 1,
        "append_only_json_lines": True,
        "matches_previous_scientific_payload": (
            None if previous_payload is None else payload == previous_payload
        ),
    }
    append_record(record)
    print_headlines(record)
    print(
        f"run_index={record['run_receipt']['run_index']} "
        "matches_previous_scientific_payload="
        f"{record['run_receipt']['matches_previous_scientific_payload']}"
    )
    print(f"appended_result={RESULTS_PATH}")
    return 0 if record["instrument_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
