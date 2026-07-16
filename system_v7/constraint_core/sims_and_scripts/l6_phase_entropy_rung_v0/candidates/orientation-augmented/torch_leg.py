#!/usr/bin/env python3
"""Compute orientation-augmented candidate values with Torch float64 ops."""

from __future__ import annotations

import json
from pathlib import Path

import torch


DTYPE = torch.float64
HERE = Path(__file__).resolve().parent
INPUT_PATH = HERE / "rows_input_v1.json"
OUTPUT_PATH = HERE / "torch_values_v1.json"


def binary_entropy_bits(radius: torch.Tensor) -> torch.Tensor:
    """Return H2((1 + radius) / 2), with 0*log2(0) defined as zero."""
    one = torch.tensor(1.0, dtype=DTYPE)
    two = torch.tensor(2.0, dtype=DTYPE)
    probability = (one + radius) / two
    complement = one - probability

    def x_log2_x(value: torch.Tensor) -> torch.Tensor:
        zero = torch.zeros_like(value, dtype=DTYPE)
        return torch.where(value == zero, zero, value * torch.log2(value))

    return -(x_log2_x(probability) + x_log2_x(complement))


def variant_values(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    r = torch.tensor([row["shell_radius"] for row in rows], dtype=DTYPE)
    neg = torch.tensor([row["negativity"] for row in rows], dtype=DTYPE)
    pur = torch.tensor([row["purity"] for row in rows], dtype=DTYPE)
    sig = torch.tensor([row["orientation"] for row in rows], dtype=DTYPE)
    ch = torch.tensor([row["chern_signed"] for row in rows], dtype=DTYPE)

    one = torch.tensor(1.0, dtype=DTYPE)
    half = torch.tensor(0.5, dtype=DTYPE)
    two = torch.tensor(2.0, dtype=DTYPE)
    h2 = binary_entropy_bits(r)
    linear_entropy = one - pur
    renyi2 = -torch.log2(pur)
    sqrt_product = torch.sqrt(torch.clamp(h2 * (one - h2), min=0.0))

    tensors: dict[str, tuple[list[str], torch.Tensor]] = {
        "OA01_tooth_r_sigma": (["radial", "orientation"], torch.stack((r, sig), dim=1)),
        "OA02_tooth_H2_sigma": (["entropy", "orientation"], torch.stack((h2, sig), dim=1)),
        "OA03_tooth_neg_sigma": (["negativity", "orientation"], torch.stack((neg, sig), dim=1)),
        "OA04_tooth_linent_sigma": (
            ["linear_entropy", "orientation"],
            torch.stack((linear_entropy, sig), dim=1),
        ),
        "OA05_signed_entropy": (["signed_entropy"], (sig * h2).reshape(-1, 1)),
        "OA06_signed_entropy_affine": (
            ["signed_entropy_affine"],
            (sig * (one + h2)).reshape(-1, 1),
        ),
        "OA07_signed_negativity": (["signed_negativity"], (sig * neg).reshape(-1, 1)),
        "OA08_signed_linear_entropy": (
            ["signed_linear_entropy"],
            (sig * linear_entropy).reshape(-1, 1),
        ),
        "OA09_signed_renyi2": (["signed_renyi2"], (sig * renyi2).reshape(-1, 1)),
        "OA10_signed_entropy_deficit": (
            ["signed_entropy_deficit"],
            (sig * (one - h2)).reshape(-1, 1),
        ),
        "OA11_chern_weighted_entropy": (
            ["chern_weighted_entropy"],
            (ch * h2).reshape(-1, 1),
        ),
        "OA12_chern_weighted_entropy_affine": (
            ["chern_weighted_entropy_affine"],
            (ch * (one + h2)).reshape(-1, 1),
        ),
        "OA13_radius_plus_signed_entropy_l05": (
            ["radius_plus_signed_entropy"],
            (r + half * sig * h2).reshape(-1, 1),
        ),
        "OA14_radius_plus_signed_entropy_l2": (
            ["radius_plus_signed_entropy"],
            (r + two * sig * h2).reshape(-1, 1),
        ),
        "OA15_entropy_plus_signed_radius": (
            ["entropy_plus_signed_radius"],
            (h2 + sig * r).reshape(-1, 1),
        ),
        "OA16_signed_entropy_sqrtprod": (
            ["signed_entropy_sqrtprod"],
            (sig * sqrt_product).reshape(-1, 1),
        ),
    }

    variants: dict[str, dict[str, object]] = {}
    for variant_id, (channels, values) in tensors.items():
        if values.dtype != DTYPE:
            raise TypeError(f"{variant_id} did not remain torch.float64")
        variants[variant_id] = {
            "channels": channels,
            "values": [[float(value.item()) for value in row] for row in values],
        }
    return variants


def main() -> None:
    torch.manual_seed(0)

    with INPUT_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    rows = sorted(payload["rows"], key=lambda row: row["row_id"])

    result = {
        "substrate": "torch",
        "schema_version": "l6_phase_entropy_candidate_values/1.0",
        "variants": variant_values(rows),
    }
    with OUTPUT_PATH.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
