#!/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
"""Compile declared-reference relative entropy values and all demanded edge signs."""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from pathlib import Path
from typing import Any

import numpy as np


WORK_DIR = Path(__file__).resolve().parent
REPO_ROOT = WORK_DIR.parents[5]
SURFACE_PATH = REPO_ROOT / "system_v7/constraint_core/sims_and_scripts/l6_phase_entropy_rung_v0/surface/surface_v1.json"
DEMANDS_PATH = REPO_ROOT / "system_v7/constraint_core/sims_and_scripts/l6_phase_entropy_rung_v0/surface/demand_families_v1.json"
ROWS_PATH = WORK_DIR / "rows_v1.json"
REFERENCES_PATH = WORK_DIR / "references_v1.json"
JULIA_OUTPUT_PATH = WORK_DIR / "julia_out_v1.json"
JAX_OUTPUT_PATH = WORK_DIR / "jax_out_v1.json"
TORCH_OUTPUT_PATH = WORK_DIR / "torch_out_v1.json"
BEHAVIOR_PATH = WORK_DIR / "behavior_v1.json"

SIM_PYTHON = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
JULIA = "/opt/homebrew/bin/julia"
JULIA_PROJECT = "/Users/joshuaeisenhart/.julia/environments/v1.12"
ZERO_TOLERANCE = 1.0e-12
ALIAS_TOLERANCE = 1.0e-9

REFERENCE_GRID = (
    ("ref_maximally_mixed", "maximally_mixed", (0.0, 0.0, 0.0), 0.0, 0.0, "phase_blind"),
    ("ref_z_plus_r060", "z_plus", (0.0, 0.0, 0.6), 0.0, 0.0, "phase_blind"),
    ("ref_z_minus_r060", "z_minus", (0.0, 0.0, -0.6), math.pi, 0.0, "phase_blind"),
    ("ref_z_plus_near_pure_r098", "z_plus_near_pure", (0.0, 0.0, 0.98), 0.0, 0.0, "phase_blind"),
    ("ref_z_minus_near_pure_r098", "z_minus_near_pure", (0.0, 0.0, -0.98), math.pi, 0.0, "phase_blind"),
    ("ref_x_plus_r060_phase0", "equatorial_phase_0", (0.6, 0.0, 0.0), math.pi / 2.0, 0.0, "phase_breaking"),
    ("ref_x_minus_r060_phasepi", "equatorial_phase_pi", (-0.6, 0.0, 0.0), math.pi / 2.0, math.pi, "phase_breaking"),
    ("ref_xy_r060_phasepi3", "equatorial_phase_pi_over_3", (0.3, 0.5196152422706632, 0.0), math.pi / 2.0, math.pi / 3.0, "phase_breaking"),
    ("ref_y_plus_r060_phasepi2", "equatorial_phase_pi_over_2", (0.0, 0.6, 0.0), math.pi / 2.0, math.pi / 2.0, "phase_blind"),
    ("ref_xy_r060_phase2pi3", "equatorial_phase_2pi_over_3", (-0.3, 0.5196152422706632, 0.0), math.pi / 2.0, 2.0 * math.pi / 3.0, "phase_breaking"),
    ("ref_tilted_xz_near_pure_r098", "tilted_xz_near_pure", (0.6929646455628166, 0.0, 0.6929646455628166), math.pi / 4.0, 0.0, "phase_breaking"),
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    return json.loads(raw), raw


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _write_inputs(surface: dict[str, Any], surface_sha256: str) -> list[dict[str, Any]]:
    rows = surface["row_blocks"]["fixture_observations"]
    if len(rows) != 18 or [int(row["row_id"]) for row in rows] != list(range(18)):
        raise ValueError("fixture rows must be ordered row_id 0 through 17")
    _write_json(
        ROWS_PATH,
        {
            "schema_version": "l6_phase_entropy_candidate_rows/1.0",
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "surface_sha256": surface_sha256,
            "rows": rows,
        },
    )

    references = []
    for variant_id, name, vector, polar_angle, phase_angle, symmetry in REFERENCE_GRID:
        radius = math.sqrt(sum(component * component for component in vector))
        lambda_plus = (1.0 + radius) / 2.0
        lambda_minus = (1.0 - radius) / 2.0
        if not (lambda_minus > 0.0 and lambda_plus < 1.0):
            raise ValueError(f"reference {variant_id} is not full rank")
        references.append(
            {
                "variant_id": variant_id,
                "reference_name": name,
                "reference_bloch_vector": list(vector),
                "reference_radius": radius,
                "reference_eigenvalues_descending": [lambda_plus, lambda_minus],
                "reference_polar_angle_rad": polar_angle,
                "reference_phase_angle_rad": phase_angle,
                "reference_phase_symmetry": symmetry,
                "regularization": {
                    "kind": "declared_full_rank_bloch_radius",
                    "minimum_eigenvalue": lambda_minus,
                    "literal_rank_one": False,
                },
                "log_base": "nats",
                "formula": "D(rho_row||sigma_ref)=Tr[rho_row(log(rho_row)-log(sigma_ref))]",
            }
        )
    _write_json(
        REFERENCES_PATH,
        {
            "schema_version": "l6_phase_entropy_declared_references/1.0",
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "reference_count": 11,
            "references": references,
        },
    )
    return rows


def _run_legs() -> None:
    julia_env = os.environ.copy()
    julia_env["JULIA_PROJECT"] = JULIA_PROJECT
    julia_env["JULIA_LOAD_PATH"] = "@:@stdlib"
    jax_env = os.environ.copy()
    jax_env["JAX_ENABLE_X64"] = "1"
    commands = (
        ([JULIA, "--startup-file=no", "julia_leg.jl", "rows_v1.json", "references_v1.json", "julia_out_v1.json"], julia_env),
        ([SIM_PYTHON, "jax_leg.py", "rows_v1.json", "references_v1.json", "jax_out_v1.json"], jax_env),
        ([SIM_PYTHON, "torch_leg.py", "rows_v1.json", "references_v1.json", "torch_out_v1.json"], os.environ.copy()),
    )
    for command, environment in commands:
        subprocess.run(
            command,
            cwd=WORK_DIR,
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )


def _numpy_row_density(row: dict[str, Any]) -> np.ndarray:
    angle = float(row["a"])
    orientation = float(row["orientation"])
    psi = np.asarray([math.cos(angle), orientation * math.sin(angle)], dtype=np.complex128)
    return np.outer(psi, np.conjugate(psi))


def _numpy_reference_density(reference: dict[str, Any]) -> np.ndarray:
    x, y, z = (float(value) for value in reference["reference_bloch_vector"])
    return np.asarray(
        [[(1.0 + z) / 2.0, complex(x, -y) / 2.0], [complex(x, y) / 2.0, (1.0 - z) / 2.0]],
        dtype=np.complex128,
    )


def _numpy_relative_entropy_nats(rho: np.ndarray, sigma: np.ndarray) -> float:
    rho_values = np.linalg.eigvalsh(rho)
    positive = rho_values[rho_values > 1.0e-300]
    rho_log_rho = float(np.sum(positive * np.log(positive), dtype=np.float64))
    sigma_values, sigma_vectors = np.linalg.eigh(sigma)
    log_sigma = (sigma_vectors * np.log(sigma_values)[None, :]) @ np.conjugate(sigma_vectors.T)
    return rho_log_rho - float(np.real(np.trace(rho @ log_sigma)))


def _numpy_controls(rows: list[dict[str, Any]], references: list[dict[str, Any]]) -> dict[str, list[float]]:
    row_densities = [_numpy_row_density(row) for row in rows]
    return {
        reference["variant_id"]: [
            _numpy_relative_entropy_nats(rho, _numpy_reference_density(reference))
            for rho in row_densities
        ]
        for reference in references
    }


def _load_leg(path: Path, substrate: str, expected_ids: list[str]) -> tuple[dict[str, list[float]], str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("classification") != "scratch_diagnostic" or payload.get("promotion_allowed") is not False:
        raise ValueError(f"{substrate} output ceiling fields differ from the declared family")
    variants = {item["variant_id"]: [float(value) for value in item["values"]] for item in payload["variants"]}
    if list(variants) != expected_ids:
        raise ValueError(f"{substrate} variant ids/order differ from the declared references")
    if any(len(values) != 18 for values in variants.values()):
        raise ValueError(f"{substrate} contains a value vector with length other than 18")
    return variants, str(payload["version"])


def _sign(delta: float) -> int:
    if abs(delta) <= ZERO_TOLERANCE:
        return 0
    return 1 if delta > 0.0 else -1


def _sign_predictions(
    edges: list[dict[str, Any]],
    julia_values: list[float],
    jax_values: list[float],
    torch_values: list[float],
) -> list[dict[str, Any]]:
    predictions = []
    for edge in edges:
        row_i = int(edge["row_i"])
        row_j = int(edge["row_j"])
        signs = {
            "sign_julia": _sign(julia_values[row_j] - julia_values[row_i]),
            "sign_jax": _sign(jax_values[row_j] - jax_values[row_i]),
            "sign_torch": _sign(torch_values[row_j] - torch_values[row_i]),
        }
        predictions.append(
            {
                "row_i": row_i,
                "row_j": row_j,
                **signs,
                "legs_agree": len(set(signs.values())) == 1,
            }
        )
    return predictions


def _raw_deltas(*value_vectors: list[float]) -> float:
    arrays = [np.asarray(values, dtype=np.float64) for values in value_vectors]
    return max(float(np.max(np.abs(left - right))) for index, left in enumerate(arrays) for right in arrays[index + 1 :])


def _alias_groups(julia_values: dict[str, list[float]], expected_ids: list[str]) -> list[list[str]]:
    groups: list[list[str]] = []
    for variant_id in expected_ids:
        vector = np.asarray(julia_values[variant_id], dtype=np.float64)
        for group in groups:
            if all(
                float(np.max(np.abs(vector - np.asarray(julia_values[other], dtype=np.float64)))) < ALIAS_TOLERANCE
                for other in group
            ):
                group.append(variant_id)
                break
        else:
            groups.append([variant_id])
    return [group for group in groups if len(group) > 1]


def _sign_tallies(predictions: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, int]]:
    tallies = {}
    for family, edges in predictions.items():
        counts = {"plus": 0, "minus": 0, "zero": 0}
        for edge in edges:
            sign = int(edge["sign_julia"])
            counts["plus" if sign > 0 else "minus" if sign < 0 else "zero"] += 1
        tallies[family] = counts
    return tallies


def main() -> None:
    surface, surface_bytes = _read_json(SURFACE_PATH)
    demands, demands_bytes = _read_json(DEMANDS_PATH)
    surface_sha256 = _sha256(surface_bytes)
    demands_sha256 = _sha256(demands_bytes)
    rows = _write_inputs(surface, surface_sha256)
    references = json.loads(REFERENCES_PATH.read_text(encoding="utf-8"))["references"]
    expected_ids = [reference["variant_id"] for reference in references]
    _run_legs()

    julia_values, julia_version = _load_leg(JULIA_OUTPUT_PATH, "julia", expected_ids)
    jax_values, jax_version = _load_leg(JAX_OUTPUT_PATH, "jax", expected_ids)
    torch_values, torch_version = _load_leg(TORCH_OUTPUT_PATH, "torch", expected_ids)
    controls = _numpy_controls(rows, references)

    variants = []
    tallies = {}
    for reference in references:
        variant_id = reference["variant_id"]
        family_predictions = {
            family_name: _sign_predictions(
                family_payload["edges"],
                julia_values[variant_id],
                jax_values[variant_id],
                torch_values[variant_id],
            )
            for family_name, family_payload in demands["families"].items()
        }
        cross_delta = _raw_deltas(julia_values[variant_id], jax_values[variant_id], torch_values[variant_id])
        control_delta = _raw_deltas(
            julia_values[variant_id], jax_values[variant_id], torch_values[variant_id], controls[variant_id]
        )
        variants.append(
            {
                "variant_id": variant_id,
                "parameters": {key: value for key, value in reference.items() if key != "variant_id"},
                "per_row_values": {
                    "julia": julia_values[variant_id],
                    "jax": jax_values[variant_id],
                    "torch": torch_values[variant_id],
                    "numpy_control": controls[variant_id],
                },
                "cross_substrate_max_delta": cross_delta,
                "numpy_control_max_delta": control_delta,
                "induced_sign_predictions": family_predictions,
            }
        )
        tallies[variant_id] = _sign_tallies(family_predictions)

    blind_ids = [reference["variant_id"] for reference in references if reference["reference_phase_symmetry"] == "phase_blind"]
    breaking_ids = [reference["variant_id"] for reference in references if reference["reference_phase_symmetry"] == "phase_breaking"]
    for variant in variants:
        orientation = variant["induced_sign_predictions"]["orientation_winding"]
        if variant["variant_id"] in blind_ids and any(edge["sign_julia"] != 0 for edge in orientation):
            raise ValueError(f"phase-blind reference {variant['variant_id']} separated an orientation_winding edge")
        if not all(edge["legs_agree"] for edges in variant["induced_sign_predictions"].values() for edge in edges):
            raise ValueError(f"engine sign disagreement for {variant['variant_id']}")
    if not any(
        any(edge["sign_julia"] != 0 for edge in variant["induced_sign_predictions"]["orientation_winding"])
        for variant in variants
        if variant["variant_id"] in breaking_ids
    ):
        raise ValueError("declared phase-breaking references produced no orientation contrast")

    worst_cross_delta = max(float(variant["cross_substrate_max_delta"]) for variant in variants)
    behavior = {
        "schema_version": "l6_phase_entropy_candidate_behavior/1.0",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "candidate_family": "relative-entropy-ref",
        "seed": 0,
        "inputs": {
            "surface": {"path": str(SURFACE_PATH), "sha256": surface_sha256},
            "demands": {"path": str(DEMANDS_PATH), "sha256": demands_sha256},
        },
        "engines": {
            "julia": {
                "cmd": f"JULIA_LOAD_PATH=@:@stdlib JULIA_PROJECT={JULIA_PROJECT} {JULIA} --startup-file=no julia_leg.jl rows_v1.json references_v1.json julia_out_v1.json",
                "julia_project": JULIA_PROJECT,
                "version": julia_version,
            },
            "jax": {
                "cmd": f"JAX_ENABLE_X64=1 {SIM_PYTHON} jax_leg.py rows_v1.json references_v1.json jax_out_v1.json",
                "version": jax_version,
                "x64": True,
            },
            "torch": {
                "cmd": f"{SIM_PYTHON} torch_leg.py rows_v1.json references_v1.json torch_out_v1.json",
                "version": torch_version,
                "dtype": "float64/complex128",
            },
            "numpy_control": {"version": np.__version__, "role": "comparison_only_control"},
        },
        "variants": variants,
        "alias_groups": _alias_groups(julia_values, expected_ids),
        "summary": {
            "variant_count": 11,
            "worst_cross_substrate_max_delta": worst_cross_delta,
            "per_variant_per_family_sign_tallies": tallies,
        },
    }
    _write_json(BEHAVIOR_PATH, behavior)
    print("variants: 11")
    print("edges_per_variant: 169")
    print(f"phase_blind_variants: {len(blind_ids)}")
    print(f"phase_breaking_variants: {len(breaking_ids)}")
    print(f"worst_cross_substrate_max_delta: {worst_cross_delta}")


if __name__ == "__main__":
    main()
