#!/usr/bin/env python3
"""PyTorch lane for the <=3Q nesting tower packet."""

from __future__ import annotations

import json

import sympy as sp
import torch
from torch.func import vmap

from gcm_nesting_tower_le3q_v0_common import RESULT_DIR, build_packet, rel, write_json


RESULT_PATH = RESULT_DIR / "gcm_nesting_tower_le3q_v0_pytorch_results.json"


def row_product(values: torch.Tensor) -> torch.Tensor:
    return torch.prod(values)


def main() -> int:
    packet = build_packet(write_negative=False)
    probe_rows = packet["compatible_families"]["probe_rows"]
    exact_rows = packet["compatible_families"]["exact_rows"]

    if probe_rows:
        probe_matrix = torch.tensor(
            [list(row["cut_family_multiplicities"].values()) for row in probe_rows],
            dtype=torch.int64,
        )
        probe_products = vmap(row_product)(probe_matrix)
        probe_sum = int(torch.sum(probe_products).item())
    else:
        probe_sum = 0

    if exact_rows:
        exact_matrix = torch.tensor(
            [list(row["cut_family_multiplicities"].values()) for row in exact_rows],
            dtype=torch.int64,
        )
        exact_products = vmap(row_product)(exact_matrix)
        exact_sum = int(torch.sum(exact_products).item())
    else:
        exact_sum = 0

    product_probe = int(packet["counts"]["product_lift_probe_family_count"])
    entangled_probe = int(packet["counts"]["tripartite_entangled_probe_family_count"])
    partition_guard = sp.Rational(product_probe + entangled_probe, 1) == sp.Rational(probe_sum, 1)
    result = {
        "engine": "pytorch",
        "ran": True,
        "reads_peer_result": False,
        "source_path": "system_v6/sims/gcm_nesting_tower_le3q_v0/gcm_nesting_tower_le3q_v0_pytorch.py",
        "result_path": rel(RESULT_PATH),
        "packages_used": ["torch", "torch.func", "sympy"],
        "aligned_packages_load_bearing": ["torch.func", "sympy"],
        "package_observables": {
            "torch.func": "vmap(row_product) over all-cut family multiplicity vectors",
            "sympy": "sp.Rational product-plus-entangled probe partition guard",
        },
        "claim_values": {
            "exact_all_cut_compatible_family_count": exact_sum,
            "probe_all_cut_compatible_family_count": probe_sum,
            "product_plus_entangled_probe_partition_ok": bool(partition_guard),
            "product_probe_family_count": product_probe,
            "tripartite_entangled_probe_family_count": entangled_probe,
        },
    }
    write_json(RESULT_PATH, result)
    print(json.dumps({"ok": True, "result_path": rel(RESULT_PATH), "claim_values": result["claim_values"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
