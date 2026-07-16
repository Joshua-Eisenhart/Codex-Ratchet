#!/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
"""Compile orientation-augmented candidate values and induced sign data."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

import numpy as np


HERE = Path(__file__).resolve().parent
SURFACE_PATH = (
    HERE.parent.parent / "surface" / "surface_v1.json"
).resolve()
DEMANDS_PATH = (
    HERE.parent.parent / "surface" / "demand_families_v1.json"
).resolve()
ROWS_PATH = HERE / "rows_input_v1.json"

PYTHON = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
JULIA = "/opt/homebrew/bin/julia"
JULIA_PROJECT = "/Users/joshuaeisenhart/.julia/environments/v1.12"
EXPECTED_HASHES = {
    str(SURFACE_PATH): "613aeae34d354c97f842ee5597abebf18ddc5d2c38217584ee72c50585f586c4",
    str(DEMANDS_PATH): "883550cbcebe2dbd01000c4884411efff4d5cb99ed63d2968d794d20344bb374",
}
ROW_FIELDS = (
    "row_id",
    "radial_index",
    "shell_radius",
    "entropy_bits",
    "negativity",
    "purity",
    "orientation",
    "chern_signed",
    "a",
)
LEG_OUTPUTS = {
    "julia": HERE / "julia_values_v1.json",
    "jax": HERE / "jax_values_v1.json",
    "torch": HERE / "torch_values_v1.json",
}
TIE_TOLERANCE = 1.0e-12


VARIANTS = {
    "OA01_tooth_r_sigma": {
        "parameters": {},
        "formula": "[r, sig]",
        "channels": ["radial", "orientation"],
    },
    "OA02_tooth_H2_sigma": {
        "parameters": {},
        "formula": "[H2, sig]",
        "channels": ["entropy", "orientation"],
    },
    "OA03_tooth_neg_sigma": {
        "parameters": {},
        "formula": "[neg, sig]",
        "channels": ["negativity", "orientation"],
    },
    "OA04_tooth_linent_sigma": {
        "parameters": {},
        "formula": "[1 - pur, sig]",
        "channels": ["linear_entropy", "orientation"],
    },
    "OA05_signed_entropy": {
        "parameters": {},
        "formula": "sig * H2",
        "channels": ["signed_entropy"],
    },
    "OA06_signed_entropy_affine": {
        "parameters": {"offset": 1.0},
        "formula": "sig * (1 + H2)",
        "channels": ["signed_entropy_affine"],
    },
    "OA07_signed_negativity": {
        "parameters": {},
        "formula": "sig * neg",
        "channels": ["signed_negativity"],
    },
    "OA08_signed_linear_entropy": {
        "parameters": {},
        "formula": "sig * (1 - pur)",
        "channels": ["signed_linear_entropy"],
    },
    "OA09_signed_renyi2": {
        "parameters": {},
        "formula": "sig * R2, where R2 = -log2(pur)",
        "channels": ["signed_renyi2"],
    },
    "OA10_signed_entropy_deficit": {
        "parameters": {},
        "formula": "sig * (1 - H2)",
        "channels": ["signed_entropy_deficit"],
    },
    "OA11_chern_weighted_entropy": {
        "parameters": {},
        "formula": "ch * H2",
        "channels": ["chern_weighted_entropy"],
    },
    "OA12_chern_weighted_entropy_affine": {
        "parameters": {"offset": 1.0},
        "formula": "ch * (1 + H2)",
        "channels": ["chern_weighted_entropy_affine"],
    },
    "OA13_radius_plus_signed_entropy_l05": {
        "parameters": {"lambda": 0.5},
        "formula": "r + 0.5 * sig * H2",
        "channels": ["radius_plus_signed_entropy"],
    },
    "OA14_radius_plus_signed_entropy_l2": {
        "parameters": {"lambda": 2.0},
        "formula": "r + 2.0 * sig * H2",
        "channels": ["radius_plus_signed_entropy"],
    },
    "OA15_entropy_plus_signed_radius": {
        "parameters": {"lambda": 1.0},
        "formula": "H2 + sig * r",
        "channels": ["entropy_plus_signed_radius"],
    },
    "OA16_signed_entropy_sqrtprod": {
        "parameters": {},
        "formula": "sig * sqrt(max(H2 * (1 - H2), 0))",
        "channels": ["signed_entropy_sqrtprod"],
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json_new(path: Path, payload) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def next_free_path(stem: str) -> Path:
    version = 1
    while True:
        candidate = HERE / f"{stem}_v{version}.json"
        if not candidate.exists():
            return candidate
        version += 1


def binary_entropy_numpy(radius: np.float64) -> np.float64:
    p = np.float64((np.float64(1.0) + radius) / np.float64(2.0))
    one_minus_p = np.float64(1.0) - p
    left = np.float64(0.0) if p == 0.0 else -p * np.log2(p)
    right = (
        np.float64(0.0)
        if one_minus_p == 0.0
        else -one_minus_p * np.log2(one_minus_p)
    )
    return np.float64(left + right)


def numpy_control(rows: list[dict]) -> dict[str, list[list[float]]]:
    values = {variant_id: [] for variant_id in VARIANTS}
    for row in rows:
        r = np.float64(row["shell_radius"])
        neg = np.float64(row["negativity"])
        pur = np.float64(row["purity"])
        sig = np.float64(row["orientation"])
        ch = np.float64(row["chern_signed"])
        h2 = binary_entropy_numpy(r)
        r2 = -np.log2(pur)
        product = np.maximum(h2 * (np.float64(1.0) - h2), np.float64(0.0))
        row_values = {
            "OA01_tooth_r_sigma": [r, sig],
            "OA02_tooth_H2_sigma": [h2, sig],
            "OA03_tooth_neg_sigma": [neg, sig],
            "OA04_tooth_linent_sigma": [np.float64(1.0) - pur, sig],
            "OA05_signed_entropy": [sig * h2],
            "OA06_signed_entropy_affine": [sig * (np.float64(1.0) + h2)],
            "OA07_signed_negativity": [sig * neg],
            "OA08_signed_linear_entropy": [sig * (np.float64(1.0) - pur)],
            "OA09_signed_renyi2": [sig * r2],
            "OA10_signed_entropy_deficit": [sig * (np.float64(1.0) - h2)],
            "OA11_chern_weighted_entropy": [ch * h2],
            "OA12_chern_weighted_entropy_affine": [
                ch * (np.float64(1.0) + h2)
            ],
            "OA13_radius_plus_signed_entropy_l05": [
                r + np.float64(0.5) * sig * h2
            ],
            "OA14_radius_plus_signed_entropy_l2": [
                r + np.float64(2.0) * sig * h2
            ],
            "OA15_entropy_plus_signed_radius": [h2 + sig * r],
            "OA16_signed_entropy_sqrtprod": [sig * np.sqrt(product)],
        }
        for variant_id, channel_values in row_values.items():
            values[variant_id].append([float(value) for value in channel_values])
    return values


def max_pairwise_delta(engine_values: list[list[list[float]]]) -> float:
    maximum = 0.0
    for left_index in range(len(engine_values)):
        left = np.asarray(engine_values[left_index], dtype=np.float64)
        for right_index in range(left_index + 1, len(engine_values)):
            right = np.asarray(engine_values[right_index], dtype=np.float64)
            maximum = max(maximum, float(np.max(np.abs(left - right))))
    return maximum


def max_control_delta(
    control_values: list[list[float]], engine_values: list[list[list[float]]]
) -> float:
    control = np.asarray(control_values, dtype=np.float64)
    return max(
        float(np.max(np.abs(control - np.asarray(values, dtype=np.float64))))
        for values in engine_values
    )


def sign_of(delta: float) -> int:
    if abs(delta) <= TIE_TOLERANCE:
        return 0
    return 1 if delta > 0.0 else -1


def predictions_for_engine(
    values: list[list[float]], rows: list[dict], demands: dict
) -> tuple[dict[str, list[dict]], tuple[int, ...]]:
    row_positions = {row["row_id"]: index for index, row in enumerate(rows)}
    by_family = {}
    flat_fused = []
    for family_name, family in demands["families"].items():
        predictions = []
        for edge in family["edges"]:
            row_i = edge["row_i"]
            row_j = edge["row_j"]
            left = values[row_positions[row_i]]
            right = values[row_positions[row_j]]
            signs = [sign_of(float(b) - float(a)) for a, b in zip(left, right)]
            fused = next((value for value in signs if value != 0), 0)
            predictions.append(
                {
                    "row_i": row_i,
                    "row_j": row_j,
                    "sign_per_channel": signs,
                    "fused_sign": fused,
                }
            )
            flat_fused.append(fused)
        by_family[family_name] = predictions
    return by_family, tuple(flat_fused)


def main() -> int:
    started_at = utc_now()
    fixed_outputs = [ROWS_PATH, *LEG_OUTPUTS.values()]
    existing = [str(path) for path in fixed_outputs if path.exists()]
    if existing:
        raise FileExistsError(
            "refusing to overwrite fixed append-only output(s): " + ", ".join(existing)
        )

    surface_hash = sha256_file(SURFACE_PATH)
    demands_hash = sha256_file(DEMANDS_PATH)
    surface = load_json(SURFACE_PATH)
    demands = load_json(DEMANDS_PATH)
    rows = [
        {field: source_row[field] for field in ROW_FIELDS}
        for source_row in sorted(
            surface["row_blocks"]["fixture_observations"],
            key=lambda item: item["row_id"],
        )
    ]
    if len(rows) != 18:
        raise ValueError(f"expected 18 rows, found {len(rows)}")
    write_json_new(
        ROWS_PATH,
        {"schema_version": "l6_phase_entropy_candidate_rows/1.0", "rows": rows},
    )

    commands = {
        "julia": {
            "command": [JULIA, "julia_leg.jl"],
            "env": {"JULIA_PROJECT": JULIA_PROJECT},
        },
        "jax": {
            "command": [PYTHON, "jax_leg.py"],
            "env": {"JAX_ENABLE_X64": "1"},
        },
        "torch": {
            "command": [PYTHON, "torch_leg.py"],
            "env": {},
        },
    }
    exit_codes = {}
    captured = {}
    for substrate in ("julia", "jax", "torch"):
        command_record = commands[substrate]
        environment = os.environ.copy()
        environment.update(command_record["env"])
        completed = subprocess.run(
            command_record["command"],
            cwd=HERE,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        exit_codes[substrate] = completed.returncode
        captured[substrate] = {
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }

    failed = {name: code for name, code in exit_codes.items() if code != 0}
    if failed:
        for substrate, streams in captured.items():
            if streams["stdout"]:
                print(f"[{substrate} stdout]\n{streams['stdout']}", end="")
            if streams["stderr"]:
                print(f"[{substrate} stderr]\n{streams['stderr']}", end="")
        raise RuntimeError(f"leg failures: {failed}")

    leg_documents = {name: load_json(path) for name, path in LEG_OUTPUTS.items()}
    for substrate, document in leg_documents.items():
        if document["substrate"] != substrate:
            raise ValueError(
                f"{substrate} output declares substrate {document['substrate']!r}"
            )
        if set(document["variants"]) != set(VARIANTS):
            raise ValueError(f"{substrate} variant registry differs from compiler")
        for variant_id, metadata in VARIANTS.items():
            if document["variants"][variant_id]["channels"] != metadata["channels"]:
                raise ValueError(f"{substrate} channel registry differs for {variant_id}")

    control = numpy_control(rows)
    variant_payloads = {}
    alias_keys = {}
    worst_delta = 0.0
    for variant_id, metadata in VARIANTS.items():
        per_engine = {
            substrate: leg_documents[substrate]["variants"][variant_id]["values"]
            for substrate in ("julia", "jax", "torch")
        }
        cross_delta = max_pairwise_delta(list(per_engine.values()))
        numpy_delta = max_control_delta(control[variant_id], list(per_engine.values()))
        worst_delta = max(worst_delta, cross_delta)

        prediction_documents = {}
        fused_maps = {}
        for substrate in ("julia", "jax", "torch"):
            prediction_documents[substrate], fused_maps[substrate] = (
                predictions_for_engine(per_engine[substrate], rows, demands)
            )
        jax_disagreements = sum(
            left != right
            for left, right in zip(fused_maps["julia"], fused_maps["jax"])
        )
        torch_disagreements = sum(
            left != right
            for left, right in zip(fused_maps["julia"], fused_maps["torch"])
        )
        sign_agreement = (
            fused_maps["julia"] == fused_maps["jax"] == fused_maps["torch"]
        )
        alias_keys[variant_id] = fused_maps["julia"]
        variant_payloads[variant_id] = {
            "parameters": metadata["parameters"],
            "formula": metadata["formula"],
            "channels": metadata["channels"],
            "per_row_values": {
                "julia": per_engine["julia"],
                "jax": per_engine["jax"],
                "torch": per_engine["torch"],
                "numpy_control": control[variant_id],
            },
            "cross_substrate_max_delta": cross_delta,
            "numpy_control_max_delta": numpy_delta,
            "sign_agreement_across_engines": sign_agreement,
            "engine_fused_sign_disagreement_counts": {
                "jax_vs_julia": jax_disagreements,
                "torch_vs_julia": torch_disagreements,
            },
            "induced_sign_predictions": prediction_documents["julia"],
        }

    grouped_aliases = {}
    for variant_id, fused_map in alias_keys.items():
        grouped_aliases.setdefault(fused_map, []).append(variant_id)
    alias_classes = sorted(
        (sorted(members) for members in grouped_aliases.values()),
        key=lambda members: members[0],
    )

    source_records = {
        "surface": {
            "path": str(SURFACE_PATH),
            "sha256": surface_hash,
            "expected_sha256": EXPECTED_HASHES[str(SURFACE_PATH)],
            "matches_expected_sha256": (
                surface_hash == EXPECTED_HASHES[str(SURFACE_PATH)]
            ),
        },
        "demand_families": {
            "path": str(DEMANDS_PATH),
            "sha256": demands_hash,
            "expected_sha256": EXPECTED_HASHES[str(DEMANDS_PATH)],
            "matches_expected_sha256": (
                demands_hash == EXPECTED_HASHES[str(DEMANDS_PATH)]
            ),
        },
    }
    behavior = {
        "schema_version": "l6_phase_entropy_candidate_behavior/1.0",
        "candidate_family": "orientation-augmented",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "claim_ceiling": (
            "scratch_diagnostic — values and induced sign predictions only; "
            "no gate logic; survival is adjudicated by the gate runner, not this lane"
        ),
        "seed": 0,
        "sources": source_records,
        "sign_rule": {
            "tie_tolerance": TIE_TOLERANCE,
            "fused": "lexicographic over declared channel order",
            "canonical_leg": "julia",
        },
        "variant_count": len(VARIANTS),
        "worst_cross_substrate_max_delta": worst_delta,
        "alias_classes": alias_classes,
        "variants": variant_payloads,
    }
    behavior_path = next_free_path("behavior")
    write_json_new(behavior_path, behavior)

    output_hashes = {}
    for path in [ROWS_PATH, *LEG_OUTPUTS.values(), behavior_path]:
        output_hashes[path.name] = sha256_file(path)
    receipt = {
        "what_ran": [
            {
                "substrate": "compiler",
                "command": [PYTHON, "compiler.py"],
                "env": {},
            },
            *[
            {
                "substrate": substrate,
                "command": commands[substrate]["command"],
                "env": commands[substrate]["env"],
            }
            for substrate in ("julia", "jax", "torch")
            ],
        ],
        "exit_codes": exit_codes,
        "timestamps_utc": {"started": started_at, "finished": utc_now()},
        "inputs": source_records,
        "outputs": output_hashes,
        "input_hash_mismatches": [
            record["path"]
            for record in source_records.values()
            if not record["matches_expected_sha256"]
        ],
        "worst_cross_substrate_max_delta": worst_delta,
        "cross_substrate_max_deltas": {
            variant_id: payload["cross_substrate_max_delta"]
            for variant_id, payload in variant_payloads.items()
        },
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "note": "no verdicts; gate logic lives in the gate-runner lane",
    }
    receipt_path = next_free_path("receipt")
    write_json_new(receipt_path, receipt)

    print(f"variant count: {len(VARIANTS)}")
    print(f"worst cross-substrate max delta: {worst_delta:.17g}")
    for variant_id in VARIANTS:
        item = variant_payloads[variant_id]
        print(
            f"{variant_id}: cross_substrate_max_delta="
            f"{item['cross_substrate_max_delta']:.17g}, "
            f"numpy_control_max_delta={item['numpy_control_max_delta']:.17g}"
        )
    print(f"leg exit codes: {exit_codes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
