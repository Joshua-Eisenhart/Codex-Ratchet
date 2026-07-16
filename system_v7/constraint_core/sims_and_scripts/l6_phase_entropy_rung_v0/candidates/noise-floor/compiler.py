#!/usr/bin/env python3
"""Compile deterministic noise-floor candidate behavior across four substrates."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
RUNG_DIR = SCRIPT_DIR.parent.parent
SURFACE_PATH = RUNG_DIR / "surface" / "surface_v1.json"
DEMAND_PATH = RUNG_DIR / "surface" / "demand_families_v1.json"

SIM_PYTHON = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
JULIA = Path("/opt/homebrew/bin/julia")
JULIA_PROJECT = Path("/Users/joshuaeisenhart/.julia/environments/v1.12")

VARIANTS_PATH = SCRIPT_DIR / "variants_v1.json"
INJECTION_PATH = SCRIPT_DIR / "injection_manifest_v1.json"
JULIA_VALUES_PATH = SCRIPT_DIR / "julia_leg_values_v1.json"
JAX_VALUES_PATH = SCRIPT_DIR / "jax_leg_values_v1.json"
TORCH_VALUES_PATH = SCRIPT_DIR / "torch_leg_values_v1.json"
BEHAVIOR_PATH = SCRIPT_DIR / "behavior_v1.json"
RECEIPT_PATH = SCRIPT_DIR / "receipt_v1.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
LANE = "candidates/noise-floor"
SIGN_TOLERANCE = 1e-12

BASIS = [
    "phi1 = a",
    "phi2 = shell_radius",
    "phi3 = purity",
    "phi4 = negativity",
    "phi5 = entropy_bits",
    "phi6 = orientation",
    "phi7 = chern_signed",
    "phi8 = a*entropy_bits",
    "phi9 = shell_radius*purity",
    "phi10 = negativity*entropy_bits",
    "phi11 = a^2",
    "phi12 = entropy_bits^2",
    "phi13 = sin(pi*a)",
    "phi14 = cos(pi*shell_radius)",
    "phi15 = orientation*entropy_bits",
    "phi16 = 1.0",
]


def json_bytes(data: Any) -> bytes:
    text = json.dumps(
        data,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    )
    return (text + "\n").encode("utf-8")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def create_or_require_identical(path: Path, content: bytes) -> bool:
    """Create an absent artifact; otherwise require exact existing bytes."""
    if path.exists():
        existing = path.read_bytes()
        if existing != content:
            print(f"BYTE_IDENTITY_FINDING={path.name}", file=sys.stderr)
            raise RuntimeError(f"existing content differs for {path}")
        return True
    path.write_bytes(content)
    return False


def generate_variant_documents() -> tuple[dict[str, Any], dict[str, Any]]:
    rng = np.random.default_rng(0)
    generated: list[tuple[list[float], str]] = []
    for draw_index in range(32):
        weights = rng.standard_normal(16).astype(np.float64)
        kind = "orientation_blind" if draw_index < 16 else "full_arity"
        if kind == "orientation_blind":
            weights[5] = 0.0
            weights[6] = 0.0
            weights[14] = 0.0
        generated.append(([float(value) for value in weights], kind))

    injected_weights = [0.0] * 16
    injected_weights[4] = 1.0
    injected_weights[5] = 1e-3
    insertion_position = int(rng.integers(0, 33))
    generated.insert(insertion_position, (injected_weights, "injected"))

    variants: list[dict[str, Any]] = []
    orientation_blind_ids: list[str] = []
    full_arity_ids: list[str] = []
    injected_variant_id = ""
    for index, (weights, kind) in enumerate(generated):
        variant_id = f"nf_v{index:02d}"
        variants.append({"variant_id": variant_id, "weights": weights})
        if kind == "orientation_blind":
            orientation_blind_ids.append(variant_id)
        elif kind == "full_arity":
            full_arity_ids.append(variant_id)
        else:
            injected_variant_id = variant_id

    variants_document = {
        "schema_version": "l6_phase_entropy_noise_floor_variants/1.0",
        "seed": 0,
        "basis": BASIS,
        "variants": variants,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
    }
    injection_document = {
        "injected_variant_id": injected_variant_id,
        "construction": (
            "entropy_bits + 1e-3*orientation, expressed as weights in the shared basis"
        ),
        "purpose": (
            "anti-by-construction result-dependent functional; the gate lane must detect "
            "it behaviorally, not by label"
        ),
        "orientation_blind_variant_ids": orientation_blind_ids,
        "full_arity_variant_ids": full_arity_ids,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
    }
    return variants_document, injection_document


def validate_inputs(surface: dict[str, Any], demands: dict[str, Any]) -> list[dict[str, Any]]:
    rows = sorted(
        surface["row_blocks"]["fixture_observations"],
        key=lambda row: int(row["row_id"]),
    )
    row_ids = [int(row["row_id"]) for row in rows]
    if row_ids != list(range(18)):
        raise RuntimeError(f"unexpected row order: {row_ids}")

    required_fields = {
        "row_id",
        "radial_index",
        "a",
        "shell_radius",
        "purity",
        "negativity",
        "entropy_bits",
        "orientation",
        "chern_signed",
    }
    for row in rows:
        missing = required_fields.difference(row)
        if missing:
            raise RuntimeError(f"row {row['row_id']} missing fields: {sorted(missing)}")
        if int(row["orientation"]) not in (-1, 1):
            raise RuntimeError(f"row {row['row_id']} has unexpected orientation")

    expected_counts = {
        "factorization_boundary": 16,
        "marginal_entropy_level": 72,
        "orientation_winding": 9,
        "shell_position": 72,
    }
    actual_names = set(demands["families"])
    if actual_names != set(expected_counts):
        raise RuntimeError(f"unexpected family names: {sorted(actual_names)}")
    for family_name, expected_count in expected_counts.items():
        edges = demands["families"][family_name]["edges"]
        if len(edges) != expected_count:
            raise RuntimeError(f"unexpected edge count for {family_name}: {len(edges)}")
        for edge in edges:
            row_i = int(edge["row_i"])
            row_j = int(edge["row_j"])
            if not (0 <= row_i < row_j < 18):
                raise RuntimeError(f"unexpected edge for {family_name}: {row_i},{row_j}")
    return rows


def numpy_phi(row: dict[str, Any]) -> np.ndarray:
    a = np.float64(row["a"])
    shell_radius = np.float64(row["shell_radius"])
    purity = np.float64(row["purity"])
    negativity = np.float64(row["negativity"])
    entropy_bits = np.float64(row["entropy_bits"])
    orientation = np.float64(row["orientation"])
    chern_signed = np.float64(row["chern_signed"])
    pi = np.float64(np.pi)
    return np.asarray(
        [
            a,
            shell_radius,
            purity,
            negativity,
            entropy_bits,
            orientation,
            chern_signed,
            a * entropy_bits,
            shell_radius * purity,
            negativity * entropy_bits,
            a * a,
            entropy_bits * entropy_bits,
            np.sin(pi * a),
            np.cos(pi * shell_radius),
            orientation * entropy_bits,
            np.float64(1.0),
        ],
        dtype=np.float64,
    )


def numpy_control_values(
    rows: list[dict[str, Any]], variants: list[dict[str, Any]]
) -> dict[str, list[float]]:
    features = [numpy_phi(row) for row in rows]
    values: dict[str, list[float]] = {}
    for variant in variants:
        weights = np.asarray(variant["weights"], dtype=np.float64)
        values[variant["variant_id"]] = [
            float(np.dot(weights, feature)) for feature in features
        ]
    return values


def run_leg(command: list[str], environment: dict[str, str], label: str) -> None:
    completed = subprocess.run(
        command,
        cwd=SCRIPT_DIR,
        env=environment,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        if completed.stdout:
            print(completed.stdout, file=sys.stderr, end="")
        if completed.stderr:
            print(completed.stderr, file=sys.stderr, end="")
        raise RuntimeError(f"{label} leg exited with code {completed.returncode}")


def sign_list(values: list[float], edges: list[dict[str, Any]]) -> list[int]:
    signs: list[int] = []
    for edge in edges:
        delta = float(values[int(edge["row_j"])]) - float(values[int(edge["row_i"])])
        if abs(delta) <= SIGN_TOLERANCE:
            signs.append(0)
        elif delta > 0.0:
            signs.append(1)
        else:
            signs.append(-1)
    return signs


def sign_summary(signs: list[int]) -> dict[str, Any]:
    return {
        "signs": signs,
        "n_pos": signs.count(1),
        "n_neg": signs.count(-1),
        "n_zero": signs.count(0),
    }


def max_pairwise_delta(series: list[list[float]]) -> float:
    maximum = 0.0
    for row_values in zip(*series, strict=True):
        for left_index in range(len(row_values)):
            for right_index in range(left_index + 1, len(row_values)):
                maximum = max(
                    maximum,
                    abs(float(row_values[left_index]) - float(row_values[right_index])),
                )
    return maximum


def max_control_delta(control: list[float], legs: list[list[float]]) -> float:
    return max(
        abs(float(leg_value) - float(control_value))
        for leg in legs
        for leg_value, control_value in zip(leg, control, strict=True)
    )


def assemble_behavior(
    surface_sha256: str,
    demands_sha256: str,
    rows: list[dict[str, Any]],
    demands: dict[str, Any],
    variants_document: dict[str, Any],
    julia_result: dict[str, Any],
    jax_result: dict[str, Any],
    torch_result: dict[str, Any],
    numpy_values: dict[str, list[float]],
) -> dict[str, Any]:
    row_order = [int(row["row_id"]) for row in rows]
    for label, result in (
        ("julia", julia_result),
        ("jax", jax_result),
        ("torch", torch_result),
    ):
        if result["reads_peer_result"] is not False:
            raise RuntimeError(f"{label} reads_peer_result is not false")
        if result["row_order"] != row_order:
            raise RuntimeError(f"{label} row order differs")
        if result["classification"] != CLASSIFICATION:
            raise RuntimeError(f"{label} classification differs")
        if result["promotion_allowed"] is not PROMOTION_ALLOWED:
            raise RuntimeError(f"{label} promotion_allowed differs")

    family_names = sorted(demands["families"])
    behavior_variants: list[dict[str, Any]] = []
    fingerprints: dict[tuple[int, ...], list[str]] = {}
    worst_cross_substrate = 0.0

    for variant in variants_document["variants"]:
        variant_id = variant["variant_id"]
        julia_values = [float(value) for value in julia_result["values"][variant_id]]
        jax_values = [float(value) for value in jax_result["values"][variant_id]]
        torch_values = [float(value) for value in torch_result["values"][variant_id]]
        control_values = [float(value) for value in numpy_values[variant_id]]
        if not all(
            len(values) == 18
            for values in (julia_values, jax_values, torch_values, control_values)
        ):
            raise RuntimeError(f"unexpected value count for {variant_id}")

        cross_delta = max_pairwise_delta([julia_values, jax_values, torch_values])
        control_delta = max_control_delta(
            control_values, [julia_values, jax_values, torch_values]
        )
        worst_cross_substrate = max(worst_cross_substrate, cross_delta)

        sign_predictions: dict[str, Any] = {}
        sign_agreement: dict[str, bool] = {}
        control_match: dict[str, bool] = {}
        fingerprint: list[int] = []
        for family_name in family_names:
            edges = demands["families"][family_name]["edges"]
            julia_signs = sign_list(julia_values, edges)
            jax_signs = sign_list(jax_values, edges)
            torch_signs = sign_list(torch_values, edges)
            control_signs = sign_list(control_values, edges)
            sign_predictions[family_name] = sign_summary(julia_signs)
            sign_agreement[family_name] = (
                jax_signs == julia_signs and torch_signs == julia_signs
            )
            control_match[family_name] = control_signs == julia_signs
            fingerprint.extend(julia_signs)

        fingerprints.setdefault(tuple(fingerprint), []).append(variant_id)
        behavior_variants.append(
            {
                "variant_id": variant_id,
                "parameters": {
                    "weights": variant["weights"],
                    "basis_ref": "variants_v1.json:basis",
                },
                "per_row_values": {
                    "julia": julia_values,
                    "jax": jax_values,
                    "torch": torch_values,
                    "numpy_control": control_values,
                },
                "cross_substrate_max_delta": cross_delta,
                "numpy_control_max_delta": control_delta,
                "sign_predictions": sign_predictions,
                "sign_agreement_across_engines": sign_agreement,
                "numpy_control_sign_match": control_match,
            }
        )

    alias_groups = [group for group in fingerprints.values() if len(group) >= 2]
    return {
        "schema_version": "l6_phase_entropy_candidate_behavior/1.0",
        "lane": LANE,
        "family": "noise_floor_seeded_linear_basis16",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "row_block": "fixture_observations",
        "scope_note": (
            "all demanded edge families reference fixture_observations rows only; "
            "functional arity matches these row fields"
        ),
        "row_order": row_order,
        "inputs": {
            "surface_v1_sha256": surface_sha256,
            "demand_families_v1_sha256": demands_sha256,
            "variants_v1_sha256": sha256_path(VARIANTS_PATH),
        },
        "engines": {
            "julia": {"version": julia_result["engine_versions"]["julia"]},
            "jax": {"version": jax_result["engine_versions"]["jax"], "x64": True},
            "torch": {"version": torch_result["engine_versions"]["torch"]},
            "numpy_control": {
                "version": np.__version__,
                "comparison_only": True,
            },
        },
        "sign_tolerance": SIGN_TOLERANCE,
        "edge_order_ref": (
            "surface/demand_families_v1.json families.<name>.edges order"
        ),
        "variants": behavior_variants,
        "alias_groups": alias_groups,
        "summary": {
            "variant_count": len(behavior_variants),
            "worst_cross_substrate_max_delta": worst_cross_substrate,
            "per_family_edge_counts": {
                name: len(demands["families"][name]["edges"]) for name in family_names
            },
            "n_alias_groups": len(alias_groups),
        },
    }


def append_receipt(
    input_hashes: dict[str, str],
    output_hashes: dict[str, str],
    variant_count: int,
    worst_cross_substrate: float,
    variants_unchanged: bool,
    behavior_unchanged: bool,
) -> None:
    invariant = {
        "schema_version": "l6_phase_entropy_noise_floor_receipt/1.0",
        "lane": LANE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "interpreter_paths": {
            "python": str(SIM_PYTHON),
            "julia": str(JULIA),
            "julia_project": str(JULIA_PROJECT),
        },
        "input_sha256s": input_hashes,
        "output_sha256s": output_hashes,
    }
    run = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "variant_count": variant_count,
        "worst_cross_substrate_max_delta": worst_cross_substrate,
        "unchanged": {
            "variants": variants_unchanged,
            "behavior": behavior_unchanged,
        },
    }
    if RECEIPT_PATH.exists():
        receipt = load_json(RECEIPT_PATH)
        for key, value in invariant.items():
            if receipt.get(key) != value:
                raise RuntimeError(f"receipt invariant differs for {key}")
        runs = receipt.get("runs")
        if not isinstance(runs, list):
            raise RuntimeError("receipt runs is not a list")
        runs.append(run)
    else:
        receipt = {**invariant, "runs": [run]}
    RECEIPT_PATH.write_bytes(json_bytes(receipt))


def main() -> int:
    try:
        surface_bytes = SURFACE_PATH.read_bytes()
        demand_bytes = DEMAND_PATH.read_bytes()
        surface = json.loads(surface_bytes)
        demands = json.loads(demand_bytes)
        surface_sha256 = sha256_bytes(surface_bytes)
        demand_sha256 = sha256_bytes(demand_bytes)
        rows = validate_inputs(surface, demands)

        variants_document, injection_document = generate_variant_documents()
        variants_unchanged = create_or_require_identical(
            VARIANTS_PATH, json_bytes(variants_document)
        )
        create_or_require_identical(INJECTION_PATH, json_bytes(injection_document))

        base_environment = os.environ.copy()
        julia_environment = base_environment.copy()
        julia_environment["JULIA_PROJECT"] = str(JULIA_PROJECT)
        run_leg([str(JULIA), str(SCRIPT_DIR / "julia_leg.jl")], julia_environment, "julia")

        jax_environment = base_environment.copy()
        jax_environment["JAX_ENABLE_X64"] = "1"
        run_leg(
            [str(SIM_PYTHON), str(SCRIPT_DIR / "jax_leg.py")],
            jax_environment,
            "jax",
        )
        run_leg(
            [str(SIM_PYTHON), str(SCRIPT_DIR / "torch_leg.py")],
            base_environment,
            "torch",
        )

        julia_result = load_json(JULIA_VALUES_PATH)
        jax_result = load_json(JAX_VALUES_PATH)
        torch_result = load_json(TORCH_VALUES_PATH)
        numpy_values = numpy_control_values(rows, variants_document["variants"])

        behavior = assemble_behavior(
            surface_sha256,
            demand_sha256,
            rows,
            demands,
            variants_document,
            julia_result,
            jax_result,
            torch_result,
            numpy_values,
        )
        behavior_unchanged = create_or_require_identical(
            BEHAVIOR_PATH, json_bytes(behavior)
        )

        output_paths = {
            "variants_v1": VARIANTS_PATH,
            "injection_manifest_v1": INJECTION_PATH,
            "julia_leg_values_v1": JULIA_VALUES_PATH,
            "jax_leg_values_v1": JAX_VALUES_PATH,
            "torch_leg_values_v1": TORCH_VALUES_PATH,
            "behavior_v1": BEHAVIOR_PATH,
        }
        output_hashes = {name: sha256_path(path) for name, path in output_paths.items()}
        input_hashes = {
            "surface_v1": surface_sha256,
            "demand_families_v1": demand_sha256,
        }
        variant_count = int(behavior["summary"]["variant_count"])
        worst_cross_substrate = float(
            behavior["summary"]["worst_cross_substrate_max_delta"]
        )
        append_receipt(
            input_hashes,
            output_hashes,
            variant_count,
            worst_cross_substrate,
            variants_unchanged,
            behavior_unchanged,
        )

        print(f"VARIANT_COUNT={variant_count}")
        print(f"WORST_CROSS_SUBSTRATE_MAX_DELTA={worst_cross_substrate}")
        print(f"UNCHANGED_VARIANTS={str(variants_unchanged).lower()}")
        print(f"UNCHANGED_BEHAVIOR={str(behavior_unchanged).lower()}")
        return 0
    except Exception as error:
        print(f"COMPILER_FINDING={type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
