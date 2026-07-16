#!/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
"""Compile cross-substrate values and induced sign predictions for marginal-vn."""

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
JULIA_OUTPUT_PATH = WORK_DIR / "julia_out_v1.json"
JAX_OUTPUT_PATH = WORK_DIR / "jax_out_v1.json"
TORCH_OUTPUT_PATH = WORK_DIR / "torch_out_v1.json"
BEHAVIOR_PATH = WORK_DIR / "behavior_v1.json"

SIM_PYTHON = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
JULIA = "/opt/homebrew/bin/julia"
JULIA_PROJECT = "/Users/joshuaeisenhart/.julia/environments/v1.12"
ZERO_TOLERANCE = 1.0e-12
ALIAS_TOLERANCE = 1.0e-9

VARIANTS = (
    {
        "variant_id": "mvn_bits_from_radius",
        "reconstruction_route": "from_radius",
        "log_base": "bits",
        "formula": "S(rho) in bits; rho=diag((1+shell_radius)/2, 1-p)",
    },
    {
        "variant_id": "mvn_nats_from_radius",
        "reconstruction_route": "from_radius",
        "log_base": "nats",
        "formula": "S(rho) in nats; rho=diag((1+shell_radius)/2, 1-p)",
    },
    {
        "variant_id": "mvn_bits_from_purity",
        "reconstruction_route": "from_purity",
        "log_base": "bits",
        "formula": "S(rho) in bits; p=(1+sqrt(max(0,2*purity-1)))/2",
    },
    {
        "variant_id": "mvn_nats_from_purity",
        "reconstruction_route": "from_purity",
        "log_base": "nats",
        "formula": "S(rho) in nats; p=(1+sqrt(max(0,2*purity-1)))/2",
    },
    {
        "variant_id": "mvn_bits_from_negativity",
        "reconstruction_route": "from_negativity",
        "log_base": "bits",
        "formula": "S(rho) in bits; p=(1+sqrt(max(0,1-4*negativity^2)))/2",
    },
    {
        "variant_id": "mvn_nats_from_negativity",
        "reconstruction_route": "from_negativity",
        "log_base": "nats",
        "formula": "S(rho) in nats; p=(1+sqrt(max(0,1-4*negativity^2)))/2",
    },
    {
        "variant_id": "mvn_bits_from_state",
        "reconstruction_route": "from_state",
        "log_base": "bits",
        "formula": "S(Tr_B |psi><psi|) in bits; psi=cos(a)|00>+orientation*sin(a)|11>",
    },
    {
        "variant_id": "mvn_nats_from_state",
        "reconstruction_route": "from_state",
        "log_base": "nats",
        "formula": "S(Tr_B |psi><psi|) in nats; psi=cos(a)|00>+orientation*sin(a)|11>",
    },
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    return json.loads(raw), raw


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_rows(surface: dict[str, Any], surface_sha256: str) -> list[dict[str, Any]]:
    rows = surface["row_blocks"]["fixture_observations"]
    if len(rows) != 18:
        raise ValueError(f"expected 18 fixture observations, received {len(rows)}")
    row_ids = [int(row["row_id"]) for row in rows]
    if row_ids != list(range(18)):
        raise ValueError(f"fixture row ids are not ordered 0 through 17: {row_ids}")
    payload = {
        "schema_version": "l6_phase_entropy_candidate_rows/1.0",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "surface_sha256": surface_sha256,
        "rows": rows,
    }
    _write_json(ROWS_PATH, payload)
    return rows


def _run_legs() -> None:
    julia_env = os.environ.copy()
    julia_env["JULIA_PROJECT"] = JULIA_PROJECT
    jax_env = os.environ.copy()
    jax_env["JAX_ENABLE_X64"] = "1"

    commands = (
        (
            [JULIA, "julia_leg.jl", "rows_v1.json", "julia_out_v1.json"],
            julia_env,
        ),
        (
            [SIM_PYTHON, "jax_leg.py", "rows_v1.json", "jax_out_v1.json"],
            jax_env,
        ),
        (
            [SIM_PYTHON, "torch_leg.py", "rows_v1.json", "torch_out_v1.json"],
            os.environ.copy(),
        ),
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


def _numpy_entropy(eigenvalues: np.ndarray, log_base: str) -> float:
    clipped = np.clip(eigenvalues.astype(np.float64), 0.0, None)
    positive = clipped[clipped > 1.0e-300]
    entropy_nats = -float(np.sum(positive * np.log(positive), dtype=np.float64))
    return entropy_nats / math.log(2.0) if log_base == "bits" else entropy_nats


def _numpy_marginal(row: dict[str, Any], route: str) -> np.ndarray:
    if route == "from_state":
        a = float(row["a"])
        orientation = float(row["orientation"])
        psi = np.asarray(
            [math.cos(a), 0.0, 0.0, orientation * math.sin(a)],
            dtype=np.complex128,
        )
        rho_ab = np.outer(psi, np.conjugate(psi)).reshape(2, 2, 2, 2)
        return np.trace(rho_ab, axis1=1, axis2=3)
    if route == "from_radius":
        p = (1.0 + float(row["shell_radius"])) / 2.0
    elif route == "from_purity":
        p = (1.0 + math.sqrt(max(0.0, 2.0 * float(row["purity"]) - 1.0))) / 2.0
    elif route == "from_negativity":
        negativity = float(row["negativity"])
        p = (1.0 + math.sqrt(max(0.0, 1.0 - 4.0 * negativity * negativity))) / 2.0
    else:
        raise ValueError(f"unsupported reconstruction route: {route}")
    return np.asarray([[p, 0.0], [0.0, 1.0 - p]], dtype=np.float64)


def _numpy_controls(rows: list[dict[str, Any]]) -> dict[str, list[float]]:
    controls: dict[str, list[float]] = {}
    for variant in VARIANTS:
        route = variant["reconstruction_route"]
        log_base = variant["log_base"]
        controls[variant["variant_id"]] = [
            _numpy_entropy(np.linalg.eigvalsh(_numpy_marginal(row, route)), log_base)
            for row in rows
        ]
    return controls


def _load_leg(path: Path, substrate: str) -> tuple[dict[str, list[float]], str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("classification") != "scratch_diagnostic":
        raise ValueError(f"{substrate} output classification is not scratch_diagnostic")
    if payload.get("promotion_allowed") is not False:
        raise ValueError(f"{substrate} output promotion_allowed is not false")
    variants = {
        item["variant_id"]: [float(value) for value in item["values"]]
        for item in payload["variants"]
    }
    expected_ids = [variant["variant_id"] for variant in VARIANTS]
    if list(variants) != expected_ids:
        raise ValueError(f"{substrate} variant ids/order differ from the declared grid")
    if any(len(values) != 18 for values in variants.values()):
        raise ValueError(f"{substrate} output contains a value vector with length other than 18")
    version = payload.get("version")
    if version is None:
        version = payload.get("engine", {}).get("version")
    if version is None:
        raise ValueError(f"{substrate} output does not record its engine version")
    return variants, str(version)


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
    predictions: list[dict[str, Any]] = []
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


def _raw_deltas(
    julia_values: list[float],
    jax_values: list[float],
    torch_values: list[float],
    control_values: list[float],
) -> tuple[float, float]:
    julia_array = np.asarray(julia_values, dtype=np.float64)
    jax_array = np.asarray(jax_values, dtype=np.float64)
    torch_array = np.asarray(torch_values, dtype=np.float64)
    control_array = np.asarray(control_values, dtype=np.float64)
    cross = max(
        float(np.max(np.abs(julia_array - jax_array))),
        float(np.max(np.abs(julia_array - torch_array))),
        float(np.max(np.abs(jax_array - torch_array))),
    )
    control = max(
        float(np.max(np.abs(julia_array - control_array))),
        float(np.max(np.abs(jax_array - control_array))),
        float(np.max(np.abs(torch_array - control_array))),
    )
    return cross, control


def _alias_groups(julia_values: dict[str, list[float]]) -> list[list[str]]:
    groups: list[list[str]] = []
    for variant in VARIANTS:
        variant_id = variant["variant_id"]
        vector = np.asarray(julia_values[variant_id], dtype=np.float64)
        placed = False
        for group in groups:
            if all(
                float(np.max(np.abs(vector - np.asarray(julia_values[other], dtype=np.float64))))
                < ALIAS_TOLERANCE
                for other in group
            ):
                group.append(variant_id)
                placed = True
                break
        if not placed:
            groups.append([variant_id])
    return [group for group in groups if len(group) > 1]


def _sign_tallies(predictions: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, int]]:
    tallies: dict[str, dict[str, int]] = {}
    for family, edges in predictions.items():
        counts = {"plus": 0, "minus": 0, "zero": 0}
        for edge in edges:
            sign = int(edge["sign_julia"])
            if sign > 0:
                counts["plus"] += 1
            elif sign < 0:
                counts["minus"] += 1
            else:
                counts["zero"] += 1
        tallies[family] = counts
    return tallies


def main() -> None:
    surface, surface_bytes = _read_json(SURFACE_PATH)
    demands, demands_bytes = _read_json(DEMANDS_PATH)
    surface_sha256 = _sha256(surface_bytes)
    demands_sha256 = _sha256(demands_bytes)
    rows = _write_rows(surface, surface_sha256)
    _run_legs()

    julia_values, julia_version = _load_leg(JULIA_OUTPUT_PATH, "julia")
    jax_values, jax_version = _load_leg(JAX_OUTPUT_PATH, "jax")
    torch_values, torch_version = _load_leg(TORCH_OUTPUT_PATH, "torch")
    controls = _numpy_controls(rows)

    variants: list[dict[str, Any]] = []
    tallies: dict[str, dict[str, dict[str, int]]] = {}
    for variant in VARIANTS:
        variant_id = variant["variant_id"]
        family_predictions: dict[str, list[dict[str, Any]]] = {}
        for family_name, family_payload in demands["families"].items():
            family_predictions[family_name] = _sign_predictions(
                family_payload["edges"],
                julia_values[variant_id],
                jax_values[variant_id],
                torch_values[variant_id],
            )
        cross_delta, control_delta = _raw_deltas(
            julia_values[variant_id],
            jax_values[variant_id],
            torch_values[variant_id],
            controls[variant_id],
        )
        variants.append(
            {
                "variant_id": variant_id,
                "parameters": {
                    "reconstruction_route": variant["reconstruction_route"],
                    "log_base": variant["log_base"],
                    "formula": variant["formula"],
                },
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

    worst_cross_delta = max(float(variant["cross_substrate_max_delta"]) for variant in variants)
    behavior = {
        "schema_version": "l6_phase_entropy_candidate_behavior/1.0",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "candidate_family": "marginal-vn",
        "seed": 0,
        "inputs": {
            "surface": {"path": str(SURFACE_PATH), "sha256": surface_sha256},
            "demands": {"path": str(DEMANDS_PATH), "sha256": demands_sha256},
        },
        "engines": {
            "julia": {
                "cmd": f"JULIA_PROJECT={JULIA_PROJECT} {JULIA} julia_leg.jl rows_v1.json julia_out_v1.json",
                "julia_project": JULIA_PROJECT,
                "version": julia_version,
            },
            "jax": {
                "cmd": f"JAX_ENABLE_X64=1 {SIM_PYTHON} jax_leg.py rows_v1.json jax_out_v1.json",
                "version": jax_version,
                "x64": True,
            },
            "torch": {
                "cmd": f"{SIM_PYTHON} torch_leg.py rows_v1.json torch_out_v1.json",
                "version": torch_version,
                "dtype": "float64",
            },
            "numpy_control": {
                "version": np.__version__,
                "role": "comparison_only_control",
            },
        },
        "variants": variants,
        "alias_groups": _alias_groups(julia_values),
        "summary": {
            "variant_count": 8,
            "worst_cross_substrate_max_delta": worst_cross_delta,
            "per_variant_per_family_sign_tallies": tallies,
        },
    }
    _write_json(BEHAVIOR_PATH, behavior)
    print("variants: 8")
    print(f"worst_cross_substrate_max_delta: {worst_cross_delta}")


if __name__ == "__main__":
    main()
