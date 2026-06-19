#!/usr/bin/env python3
"""PyTorch leg: sparse-adjacency reachability closure.

The only shared input is spec.json. This file does not import the v6 feedstock
and does not read Julia or JAX results.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

import torch

torch.set_default_dtype(torch.float64)

SIM_ID = "mixed_radix_endofunction_scc_terminal_quotient_under_z2_involution_v0"
HERE = os.path.dirname(os.path.abspath(__file__))


def sha256_of(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def encode(coords: tuple[int, int, int, int], shape: list[int]) -> int:
    out = 0
    for value, modulus in zip(coords, shape):
        out = out * modulus + value
    return int(out)


def decode(state_id: int, shape: list[int]) -> tuple[int, int, int, int]:
    values = []
    rest = int(state_id)
    for modulus in reversed(shape):
        values.append(rest % modulus)
        rest //= modulus
    return tuple(reversed(values))  # type: ignore[return-value]


def readout_sign(spec: dict, orientation: str, d0: int, d1: int) -> int:
    word = spec["orientation_tables"][orientation]["radix_digit_0_word_rows"][d0][d1]
    component = spec["word_readout_components"][word][d0]
    return int(spec["readout_sign_map"][component])


def base_next(spec: dict, orientation: str, state_id: int) -> tuple[int, bool, int]:
    shape = spec["mixed_radix_shape"]
    d0, d1, d2, z = decode(state_id, shape)
    current = readout_sign(spec, orientation, d0, d1)
    nxt = readout_sign(spec, orientation, d0, (d1 + 1) % shape[1])
    next_d2 = (d2 + (1 if d0 == 0 else 3)) % shape[2]
    next_d0, next_d1 = d0, d1
    if next_d2 == 0:
        inc = 1 if current != nxt else 2
        next_d1 += inc
        while next_d1 >= shape[1]:
            next_d1 -= shape[1]
            next_d0 = (next_d0 + 1) % shape[0]
    boundary = (next_d0 != d0) or (next_d1 != d1)
    return encode((next_d0, next_d1, next_d2, z), shape), boundary, readout_sign(spec, orientation, next_d0, next_d1)


def event_selected(spec: dict, orientation: str, state_id: int) -> bool:
    _base_id, boundary, next_sign = base_next(spec, orientation, state_id)
    d0, _d1, _d2, _z = decode(state_id, spec["mixed_radix_shape"])
    orientation_sign = int(spec["orientation_tables"][orientation]["orientation_sign"])
    orientation_row = (orientation_sign > 0 and d0 == 0) or (orientation_sign < 0 and d0 == 1)
    return bool(boundary and orientation_row and orientation_sign * next_sign < 0)


def apply_law(spec: dict, orientation: str, state_id: int, law: str) -> int:
    shape = spec["mixed_radix_shape"]
    base_id, _boundary, _next = base_next(spec, orientation, state_id)
    d0, d1, d2, _z = decode(base_id, shape)
    old_z = decode(state_id, shape)[3]
    event = event_selected(spec, orientation, state_id)
    if law == "conserved_control":
        next_z = old_z
    elif law == "parity_flipping_law":
        next_z = 1 if (event and old_z == 0) else old_z
    elif law == "reference_toggle_law":
        next_z = 1 - old_z if event else old_z
    else:
        raise ValueError(law)
    return encode((d0, d1, d2, next_z), shape)


def transition_table(spec: dict, orientation: str, law: str) -> list[int]:
    values = [apply_law(spec, orientation, state_id, law) for state_id in range(64)]
    return [int(v) for v in torch.tensor(values, dtype=torch.int64).tolist()]


def reachability_scc_summary(table: list[int]) -> dict:
    n = len(table)
    src = torch.arange(n, dtype=torch.int64)
    dst = torch.tensor(table, dtype=torch.int64)
    indices = torch.stack([src, dst], dim=0)
    values = torch.ones(n, dtype=torch.float64)
    sparse = torch.sparse_coo_tensor(indices, values, (n, n)).coalesce()
    base = sparse.to_dense().to(torch.bool)
    reach = torch.eye(n, dtype=torch.bool) | base
    cur = base.clone()
    base_i = base.to(torch.int64)
    for _ in range(1, n):
        cur = (cur.to(torch.int64) @ base_i) > 0
        reach |= cur

    seen = [False] * n
    classes = []
    for i in range(n):
        if seen[i]:
            continue
        members = [j for j in range(n) if bool(reach[i, j]) and bool(reach[j, i])]
        for member in members:
            seen[member] = True
        classes.append(sorted(members))
    classes.sort(key=lambda row: (min(row), len(row)))
    class_of = {}
    for idx, members in enumerate(classes):
        for member in members:
            class_of[member] = idx
    outgoing = {idx: set() for idx in range(len(classes))}
    for src_id, dst_id in enumerate(table):
        a, b = class_of[src_id], class_of[dst_id]
        if a != b:
            outgoing[a].add(b)
    terminal = [idx for idx in range(len(classes)) if not outgoing[idx]]
    return {
        "scc_count": len(classes),
        "scc_classes": classes,
        "quotient_classes": classes,
        "quotient_class_count": len(classes),
        "terminal_scc_count": len(terminal),
        "terminal_scc_sizes": sorted(len(classes[idx]) for idx in terminal),
        "terminal_scc_class_ids": terminal,
        "condensation_edge_count": sum(len(v) for v in outgoing.values()),
        "reachability_closure_all_reflexive": bool(torch.diagonal(reach).all().item()),
    }


def sigma_table(shape: list[int]) -> list[int]:
    out = []
    for state_id in range(64):
        d0, d1, d2, z = decode(state_id, shape)
        out.append(encode((d0, d1, d2, 1 - z), shape))
    return out


def direct_separators(table: list[int], sigma: list[int]) -> list[dict[str, int]]:
    rows = []
    for state_id in range(len(table)):
        left = table[sigma[state_id]]
        right = sigma[table[state_id]]
        if left != right:
            rows.append({"state_id": state_id, "left_image": left, "right_image": right})
    return rows


def main() -> None:
    with open(os.path.join(HERE, "spec.json"), encoding="utf-8") as handle:
        spec = json.load(handle)
    shape = spec["mixed_radix_shape"]
    laws = list(spec["update_law_identifiers"].keys())
    orientations = ["map_plus", "map_minus"]
    sigma = sigma_table(shape)
    summaries = {}
    direct = {}
    for orientation in orientations:
        summaries[orientation] = {}
        direct[orientation] = {}
        for law in laws:
            table = transition_table(spec, orientation, law)
            summary = reachability_scc_summary(table)
            summary["endofunction_table"] = table
            summaries[orientation][law] = summary
            direct[orientation][law] = direct_separators(table, sigma)
    selected = {orientation: summaries[orientation]["parity_flipping_law"] for orientation in orientations}
    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "computation_style": "torch_sparse_adjacency_power_reachability_closure",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": sha256_of(os.path.abspath(__file__)),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_pytorch_results.json",
        "mixed_radix_shape": shape,
        "finite_set_size": 64,
        "state_labels": [str(i) for i in range(64)],
        "transition_map": {k: v["endofunction_table"] for k, v in selected.items()},
        "endofunction_table": {k: v["endofunction_table"] for k, v in selected.items()},
        "scc_count": {k: v["scc_count"] for k, v in selected.items()},
        "scc_classes": {k: v["scc_classes"] for k, v in selected.items()},
        "quotient_classes": {k: v["quotient_classes"] for k, v in selected.items()},
        "quotient_class_count": {k: v["quotient_class_count"] for k, v in selected.items()},
        "terminal_scc_count": {k: v["terminal_scc_count"] for k, v in selected.items()},
        "terminal_scc_sizes": {k: v["terminal_scc_sizes"] for k, v in selected.items()},
        "involution_definition": spec["involution_definition"],
        "involution_is_equivariant": {
            orientation: {law: len(direct[orientation][law]) == 0 for law in laws}
            for orientation in orientations
        },
        "per_orientation": summaries,
        "lineage": spec["lineage"],
        "legacy_project_labels": spec["legacy_project_labels"],
        "legacy_paths": spec["legacy_paths"],
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "load-bearing sparse adjacency powers and boolean reachability closure for SCC membership"}
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing"},
        "packages_used": ["torch"],
        "aligned_packages_load_bearing": ["torch"]
    }
    out = os.path.join(HERE, "results", f"{SIM_ID}_pytorch_results.json")
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"pytorch leg wrote {out}")
    print(json.dumps(result["terminal_scc_sizes"], sort_keys=True))


if __name__ == "__main__":
    main()
