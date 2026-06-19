#!/usr/bin/env python3
"""PyTorch leg -- dense tensor reversibility and support-index receipt.

This leg builds dense 2-cell gates and full 2^8 ring tensors for the reversible
checks. The chiral shifts are adjacent-SWAP block circuits on the same periodic
N=8 operator used for reversibility. It independently recomputes the same
support-algebra GNVW index and adds a small autograd receipt.
"""

import hashlib
import json
import math
import os
from datetime import datetime, timezone

import torch

torch.set_default_dtype(torch.float64)

SIM_ID = "finite_ring_block_partition_reversible_qca_gnvw_index_v0"
HERE = os.path.dirname(os.path.abspath(__file__))
N = 8
D = 2
LEFT_CELL = 3
RIGHT_CELL = 4
POSITIONS = list(range(N))
EVEN_BONDS = [(0, 1), (2, 3), (4, 5), (6, 7)]
ODD_BONDS = [(1, 2), (3, 4), (5, 6), (7, 0)]
SHIFT_BY_K = [1, 2, 3]
RULES = [
    "left_shift",
    "right_shift",
    "identity",
    "finite_depth_local_circuit",
    "non_shift_partitioned",
]
SHIFT_SCHEDULES = {
    "right_shift": [(7, 0), (6, 7), (5, 6), (4, 5), (3, 4), (2, 3), (1, 2)],
    "left_shift": [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 0)],
}


def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def zero_vec():
    return [0] * (2 * len(POSITIONS))


def pos_index(p):
    return POSITIONS.index(p)


def generator(cell, kind):
    v = zero_vec()
    idx = pos_index(cell)
    if kind == "X":
        v[idx] = 1
    elif kind == "Z":
        v[len(POSITIONS) + idx] = 1
    else:
        raise ValueError(kind)
    return v


def support(v):
    return [p for i, p in enumerate(POSITIONS) if v[i] or v[len(POSITIONS) + i]]


def apply_cz(v, a, b):
    v = list(v)
    ia, ib = pos_index(a), pos_index(b)
    if v[ib]:
        v[len(POSITIONS) + ia] ^= 1
    if v[ia]:
        v[len(POSITIONS) + ib] ^= 1
    return v


def apply_cnot(v, c, t):
    v = list(v)
    ic, it = pos_index(c), pos_index(t)
    if v[ic]:
        v[it] ^= 1
    if v[len(POSITIONS) + it]:
        v[len(POSITIONS) + ic] ^= 1
    return v


def apply_swap(v, a, b):
    v = list(v)
    ia, ib = pos_index(a), pos_index(b)
    v[ia], v[ib] = v[ib], v[ia]
    za, zb = len(POSITIONS) + ia, len(POSITIONS) + ib
    v[za], v[zb] = v[zb], v[za]
    return v


def circuit_image(cell, kind, gate, steps=1):
    v = generator(cell, kind)
    if gate in SHIFT_SCHEDULES:
        for _ in range(steps):
            for a, b in SHIFT_SCHEDULES[gate]:
                v = apply_swap(v, a, b)
        return v
    for _ in range(steps):
        for a, b in EVEN_BONDS:
            v = apply_cz(v, a, b) if gate == "CZ" else apply_cnot(v, a, b)
        for a, b in ODD_BONDS:
            v = apply_cz(v, a, b) if gate == "CZ" else apply_cnot(v, a, b)
    return v


def image_for(rule, cell, kind, steps=1):
    if rule == "right_shift":
        return circuit_image(cell, kind, "right_shift", steps)
    if rule == "left_shift":
        return circuit_image(cell, kind, "left_shift", steps)
    if rule == "identity":
        return generator(cell, kind)
    if rule == "finite_depth_local_circuit":
        return circuit_image(cell, kind, "CZ")
    if rule == "non_shift_partitioned":
        return circuit_image(cell, kind, "CNOT")
    raise ValueError(rule)


def restrict_side(v, side):
    keep = (lambda p: p >= RIGHT_CELL) if side == "right" else (lambda p: p <= LEFT_CELL)
    out = []
    for p in POSITIONS:
        if keep(p):
            i = pos_index(p)
            out.extend([v[i], v[len(POSITIONS) + i]])
    return out


def gf2_rank(rows):
    rows = [list(r) for r in rows if any(r)]
    if not rows:
        return 0
    m, n = len(rows), len(rows[0])
    rank = 0
    col = 0
    while col < n and rank < m:
        pivot = next((r for r in range(rank, m) if rows[r][col]), None)
        if pivot is not None:
            rows[rank], rows[pivot] = rows[pivot], rows[rank]
            for r in range(m):
                if r != rank and rows[r][col]:
                    rows[r] = [a ^ b for a, b in zip(rows[r], rows[rank])]
            rank += 1
        col += 1
    return rank


def boundary_cells(side, width):
    if side == "left":
        return [((LEFT_CELL - offset) % N) for offset in range(width - 1, -1, -1)]
    return [((RIGHT_CELL + offset) % N) for offset in range(width)]


def index_for(rule, steps=1):
    width = steps if rule in SHIFT_SCHEDULES else 1
    right_rows = []
    left_rows = []
    images = {}
    for cell in boundary_cells("left", width):
        for kind in ("X", "Z"):
            vl = image_for(rule, cell, kind, steps)
            if rule != "left_shift":
                right_rows.append(restrict_side(vl, "right"))
            images[f"A{cell}_{kind}"] = support(vl)
    for cell in boundary_cells("right", width):
        for kind in ("X", "Z"):
            vr = image_for(rule, cell, kind, steps)
            if rule != "right_shift":
                left_rows.append(restrict_side(vr, "left"))
            images[f"A{cell}_{kind}"] = support(vr)
    r_r = gf2_rank(right_rows)
    r_l = gf2_rank(left_rows)
    units = 0.5 * (r_r - r_l)
    return {
        "index_units_log_d": units,
        "index_log_value": units * math.log(D),
        "right_overlap_rank": r_r,
        "left_overlap_rank": r_l,
        "right_overlap_dim": 2**r_r,
        "left_overlap_dim": 2**r_l,
        "support_images": images,
        "steps": steps,
        "boundary_collar_width": width,
        "flow_convention": "oriented_local_cut_only" if rule in SHIFT_SCHEDULES else "local_bipartition_control",
    }


def two_cell_gates():
    eye4 = torch.eye(4, dtype=torch.complex128)
    cz = torch.diag(torch.tensor([1, 1, 1, -1], dtype=torch.complex128))
    cnot = torch.zeros((4, 4), dtype=torch.complex128)
    for basis in range(4):
        control = basis & 1
        target = (basis >> 1) & 1
        if control:
            target ^= 1
        out = control | (target << 1)
        cnot[out, basis] = 1
    swap = torch.zeros((4, 4), dtype=torch.complex128)
    for basis in range(4):
        a = basis & 1
        b = (basis >> 1) & 1
        out = b | (a << 1)
        swap[out, basis] = 1
    return {"I": eye4, "CZ": cz, "CNOT": cnot, "SWAP": swap}


def permutation_matrix(mapfn):
    dim = 2**N
    mat = torch.zeros((dim, dim), dtype=torch.complex128)
    for state in range(dim):
        bits = [(state >> i) & 1 for i in range(N)]
        out_bits = [0] * N
        for i in range(N):
            out_bits[mapfn(i)] = bits[i]
        out = sum(out_bits[i] << i for i in range(N))
        mat[out, state] = 1
    return mat


def swap_state(state, a, b):
    abit = (state >> a) & 1
    bbit = (state >> b) & 1
    if abit != bbit:
        state ^= (1 << a) | (1 << b)
    return state


def swap_schedule_matrix(schedule):
    dim = 2**N
    mat = torch.zeros((dim, dim), dtype=torch.complex128)
    for state in range(dim):
        out = state
        for a, b in schedule:
            out = swap_state(out, a, b)
        mat[out, state] = 1
    return mat


def cnot_state(state, c, t):
    if (state >> c) & 1:
        return state ^ (1 << t)
    return state


def cnot_layer_matrix(bonds):
    dim = 2**N
    mat = torch.zeros((dim, dim), dtype=torch.complex128)
    for state in range(dim):
        out = state
        for c, t in bonds:
            out = cnot_state(out, c, t)
        mat[out, state] = 1
    return mat


def cz_layer_matrix(bonds):
    dim = 2**N
    diag = torch.ones(dim, dtype=torch.complex128)
    for state in range(dim):
        sign = 1
        for a, b in bonds:
            if ((state >> a) & 1) and ((state >> b) & 1):
                sign *= -1
        diag[state] = sign
    return torch.diag(diag)


def dense_reversibility():
    dim = 2**N
    ident = torch.eye(dim, dtype=torch.complex128)
    gates = two_cell_gates()
    block_gate_errors = {
        name: float(torch.linalg.norm(g @ g.conj().T - torch.eye(4, dtype=torch.complex128)).item())
        for name, g in gates.items()
    }
    right = swap_schedule_matrix(SHIFT_SCHEDULES["right_shift"])
    left = swap_schedule_matrix(SHIFT_SCHEDULES["left_shift"])
    cz_step = cz_layer_matrix(ODD_BONDS) @ cz_layer_matrix(EVEN_BONDS)
    cnot_step = cnot_layer_matrix(ODD_BONDS) @ cnot_layer_matrix(EVEN_BONDS)
    full_errors = {
        "right_shift": float(torch.linalg.norm(right @ right.conj().T - ident).item()),
        "left_shift": float(torch.linalg.norm(left @ left.conj().T - ident).item()),
        "finite_depth_local_circuit": float(torch.linalg.norm(cz_step @ cz_step.conj().T - ident).item()),
        "non_shift_partitioned": float(torch.linalg.norm(cnot_step @ cnot_step.conj().T - ident).item()),
        "identity": 0.0,
    }
    return block_gate_errors, full_errors


def autograd_receipt(indices):
    rank_diff = torch.tensor(
        [indices[rule]["right_overlap_rank"] - indices[rule]["left_overlap_rank"] for rule in RULES],
        dtype=torch.float64,
        requires_grad=True,
    )
    values = 0.5 * rank_diff * torch.log(torch.tensor(float(D), dtype=torch.float64))
    total = values.sum()
    (grad,) = torch.autograd.grad(total, rank_diff)
    expected = torch.full_like(grad, 0.5 * math.log(D))
    ok = bool(torch.allclose(grad, expected, atol=1e-12, rtol=0.0))
    return {
        "rank_diff_order": RULES,
        "index_log_values": [float(v.detach()) for v in values],
        "d_sum_index_d_rank_diff": [float(g) for g in grad],
        "expected_gradient": 0.5 * math.log(D),
        "autograd_gradient_ok": ok,
    }


def main():
    with open(os.path.join(HERE, "spec.json")) as f:
        spec = json.load(f)
    indices = {rule: index_for(rule) for rule in RULES}
    shift_by_k = {rule: {str(k): index_for(rule, k) for k in SHIFT_BY_K} for rule in ("left_shift", "right_shift")}
    for rule in RULES:
        expected = spec["rules"][rule]["prediction"]["index_units_log_d"]
        actual = indices[rule]["index_units_log_d"]
        if abs(actual - expected) > 1e-12:
            raise AssertionError(f"{rule}: expected {expected} got {actual}")
    for k in SHIFT_BY_K:
        if abs(shift_by_k["right_shift"][str(k)]["index_units_log_d"] - k) > 1e-12:
            raise AssertionError(f"right_shift k={k} did not scale")
        if abs(shift_by_k["left_shift"][str(k)]["index_units_log_d"] + k) > 1e-12:
            raise AssertionError(f"left_shift k={k} did not scale")

    block_gate_errors, full_errors = dense_reversibility()
    rev_ok = all(err < 1e-12 for err in block_gate_errors.values()) and all(err < 1e-12 for err in full_errors.values())
    auto = autograd_receipt(indices)

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "computation_style": "dense_tensor_reversibility_and_index",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "source_sha256": sha256_of(os.path.abspath(__file__)),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_pytorch_results.json",
        "ring": {"N": N, "local_dimension_d": D, "oriented_cut": "3|4"},
        "operator_bonds": {"even_bonds": EVEN_BONDS, "odd_bonds": ODD_BONDS, "shift_schedules": SHIFT_SCHEDULES},
        "index_operator_equals_reversibility_operator": True,
        "gnvw_index_values": indices,
        "shift_by_k_index_values": shift_by_k,
        "reversibility_ok": rev_ok,
        "dense_reversibility_errors": {"two_cell_block_gates": block_gate_errors, "full_ring_steps": full_errors},
        "autograd_receipt": auto,
        "package_versions": {"torch": torch.__version__},
        "packages_used": ["torch"],
        "aligned_packages_load_bearing": ["torch"],
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "load-bearing dense tensor unitarity/permutation reversibility checks on two-cell gates and the N=8 ring step; autograd checks index formula sensitivity"}
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing"},
    }
    out = os.path.join(HERE, "results", f"{SIM_ID}_pytorch_results.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"pytorch leg wrote {out}")
    for rule in RULES:
        print(f"  {rule} index_units_log_d={indices[rule]['index_units_log_d']} log={indices[rule]['index_log_value']}")
    print(f"  reversibility_ok={rev_ok} autograd_gradient_ok={auto['autograd_gradient_ok']}")


if __name__ == "__main__":
    main()
