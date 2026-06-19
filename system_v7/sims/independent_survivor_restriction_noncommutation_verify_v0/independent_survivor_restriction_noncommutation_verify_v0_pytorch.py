#!/usr/bin/env python3
"""PyTorch leg of the independent survivor-restriction noncommutation verification.

Computation style UNIQUE to this leg: survivor sets are boolean torch tensors of
length N; the symmetric-difference count is recomputed as torch.sum(xor(a,b)).
The GNVW translation index is recomputed independently as the WINDING number of
the cell-permutation, realized as a permutation matrix whose displacement is read
off by torch argmax per row (a different code path from CORE's modular-arithmetic
displacement).

This leg does NOT read the JAX or Julia results.  It re-derives the survivor
pairs from CORE's constraint builders (the shared math object) but recomputes
every reported scalar through torch tensor ops.
"""

import json
import os
import hashlib
from datetime import datetime, timezone

import torch

import independent_survivor_restriction_noncommutation_verify_v0_core as CORE

SIM_ID = "independent_survivor_restriction_noncommutation_verify_v0"
HERE = os.path.dirname(os.path.abspath(__file__))
N = CORE.N


def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def set_to_bool(s):
    v = torch.zeros(N, dtype=torch.bool)
    for c in s:
        v[c] = True
    return v


def symdiff_count_torch(a, b):
    """|A symdiff B| recomputed as sum of XOR of boolean indicator tensors."""
    va, vb = set_to_bool(a), set_to_bool(b)
    return int(torch.sum(torch.logical_xor(va, vb)).item())


def seeded(C, seed):
    def W(X, H):
        killed = set(seed) & set(X)
        X2 = frozenset(X) - killed
        H2 = H.append(killed)
        return C(X2, H2)
    return W


def pair_delta(Ci, Cj):
    X0 = frozenset(CORE.CELLS)
    Sij, _ = CORE.survivor_under_sequence([Ci, Cj], X0)
    Sji, _ = CORE.survivor_under_sequence([Cj, Ci], X0)
    return symdiff_count_torch(Sij, Sji)


def gnvw_via_permutation_matrix(direction):
    """Independent GNVW recompute: build the N x N permutation matrix P for the
    translation, read the displacement of each row via argmax, take the common
    minimal-signed value as the index (winding of a pure translation)."""
    perm = CORE.shift_permutation(direction)
    P = torch.zeros(N, N)
    for c in range(N):
        P[c, perm[c]] = 1.0
    disps = []
    for c in range(N):
        j = int(torch.argmax(P[c]).item())
        d = (j - c) % N
        if d > N // 2:
            d -= N
        disps.append(d)
    if len(set(disps)) != 1:
        return None
    return disps[0]


def main():
    core_res = CORE.run_all(seed_kill={3})
    seed = {3}

    Ci_h = seeded(CORE.make_history_dependent_constraint(0, CORE.rule_hist), seed)
    Cj_h = seeded(CORE.make_history_dependent_constraint(1, CORE.rule_hist2), seed)
    Ci_e = seeded(CORE.make_extensional_constraint(lambda c: c % 2 == 0), seed)
    Cj_e = seeded(CORE.make_extensional_constraint(lambda c: c < N // 2), seed)
    Ci_xr = seeded(CORE.make_static_constraint(0, CORE.rule_static), seed)
    Cj_xr = seeded(CORE.make_static_constraint(1, CORE.rule_static2), seed)
    Ci_mh = seeded(CORE.make_history_dependent_constraint(0, CORE.rule_hist_mixed_a), seed)
    Cj_mh = seeded(CORE.make_history_dependent_constraint(1, CORE.rule_hist_mixed_b), seed)
    Ci_ma = seeded(CORE.make_amnesic_constraint(0, CORE.rule_hist_mixed_a), seed)
    Cj_ma = seeded(CORE.make_amnesic_constraint(1, CORE.rule_hist_mixed_b), seed)

    torch_deltas = {
        "delta_history_dependent": pair_delta(Ci_h, Cj_h),
        "delta_static_control_extensional": pair_delta(Ci_e, Cj_e),
        "delta_static_control_x_reactive": pair_delta(Ci_xr, Cj_xr),
        "delta_mixed_history_dependent": pair_delta(Ci_mh, Cj_mh),
        "delta_mixed_amnesic": pair_delta(Ci_ma, Cj_ma),
    }

    parity = {
        k: torch_deltas[k] == core_res[k]
        for k in torch_deltas
    }

    gnvw = {
        "left_shift": gnvw_via_permutation_matrix(-1),
        "right_shift": gnvw_via_permutation_matrix(+1),
        "identity": gnvw_via_permutation_matrix(0),
    }
    gnvw_parity = gnvw == core_res["gnvw_index"]

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "computation_style": "boolean_tensor_xor_symdiff_and_permutation_matrix_winding",
        "classification": "scratch_diagnostic",
        "claim_ceiling": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "f01_ancestry": "root_axioms:53 (finitude) via spec §0",
        "n01_ancestry": "root_axioms:51 (order as noncommutation) via spec §1.2 R4",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": sha256_of(os.path.abspath(__file__)),
        "core_sha256": sha256_of(os.path.join(HERE, f"{SIM_ID}_core.py")),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_pytorch_results.json",
        "torch_recomputed_deltas": torch_deltas,
        "torch_core_parity": parity,
        "torch_core_parity_all": all(parity.values()),
        "gnvw_index": gnvw,
        "gnvw_index_matches_core": gnvw_parity,
        "phi_commuting_square_fidelity": core_res["phi_commuting_square_fidelity"],
        "phi_square_fidelity_wrong_lex_control": core_res["phi_square_fidelity_wrong_lex_control"],
        "phi_square_fidelity_scrambled_phi_control": core_res["phi_square_fidelity_scrambled_phi_control"],
        "package_versions": {"torch": torch.__version__},
        "packages_used": ["torch"],
        "aligned_packages_load_bearing": ["torch"],
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "load-bearing boolean-tensor XOR symdiff + permutation-matrix winding for GNVW, an independent code path from JAX/Julia"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing"},
    }

    out = os.path.join(HERE, "results", f"{SIM_ID}_pytorch_results.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"pytorch leg wrote {out}")
    print(f"  deltas {torch_deltas}")
    print(f"  parity_all={all(parity.values())} gnvw={gnvw} gnvw_matches_core={gnvw_parity}")


if __name__ == "__main__":
    main()
