#!/usr/bin/env python3
"""PyTorch lane for gcm_nested_geometry_delta_3q_v0."""

from __future__ import annotations

import json

import sympy as sp
import torch
from torch.func import vmap

from gcm_nested_geometry_delta_3q_v0_common import (
    RESULT_DIR,
    build_packet,
    engine_claim_values,
    engine_delta_vectors,
    rel,
    scaled_decimal,
    write_json,
)


RESULT_PATH = RESULT_DIR / "gcm_nested_geometry_delta_3q_v0_pytorch_results.json"


def row_l1(row: torch.Tensor) -> torch.Tensor:
    return torch.sum(torch.abs(row))


def main() -> int:
    packet = build_packet(write_result=False)
    values = engine_claim_values(packet)
    vectors = engine_delta_vectors(packet)
    matrix = torch.tensor(
        [
            vectors["main"],
            vectors["same_input_stable_null"],
            vectors["alternate_pin"],
            vectors["alternate_probe"],
        ],
        dtype=torch.float64,
    )
    l1_values = vmap(row_l1)(matrix)
    recomputed = [scaled_decimal(float(value.item())) for value in l1_values]
    rational_guard = sp.Rational(recomputed[0], 1) != sp.Rational(recomputed[2], 1)
    result = {
        "engine": "pytorch",
        "ran": True,
        "reads_peer_result": False,
        "source_path": "system_v6/sims/gcm_nested_geometry_delta_3q_v0/gcm_nested_geometry_delta_3q_v0_pytorch.py",
        "result_path": rel(RESULT_PATH),
        "packages_used": ["torch", "torch.func", "sympy"],
        "aligned_packages_load_bearing": [],
        "aligned_packages_supportive": ["torch.func", "sympy"],
        "engine_role": "packet_vector_l1_recomputation",
        "claim_path_depth": "supportive",
        "engine_independence_ceiling": "supportive L1 recomputation from packet-built delta vectors; not an independent geometry recompute",
        "package_observables": {
            "torch.func": "supportive vmap(row_l1) over stacked packet-built main/null/alternate delta vectors",
            "sympy": "supportive sp.Rational exact guard that alternate pin changes the scaled L1 delta",
        },
        "claim_values": {
            **values,
            "torch_recomputed_main_delta_l1_scaled": recomputed[0],
            "torch_recomputed_same_input_stable_delta_l1_scaled": recomputed[1],
            "torch_recomputed_alternate_pin_delta_l1_scaled": recomputed[2],
            "torch_recomputed_alternate_probe_delta_l1_scaled": recomputed[3],
            "alternate_pin_scaled_l1_moved": bool(rational_guard),
        },
    }
    write_json(RESULT_PATH, result)
    print(json.dumps({"ok": True, "result_path": rel(RESULT_PATH), "claim_values": result["claim_values"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
