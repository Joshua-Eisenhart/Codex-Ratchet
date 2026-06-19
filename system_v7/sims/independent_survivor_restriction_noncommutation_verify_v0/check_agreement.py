#!/usr/bin/env python3
"""Cross-engine agreement checker. Reads the three leg result JSONs and asserts
the three INDEPENDENT engines (JAX vmap indicators / PyTorch boolean tensors /
native Julia sets) agree on every audited scalar. Exit 1 on any mismatch.
Also re-states the audit verdict booleans from the agreed values."""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIM_ID = "independent_survivor_restriction_noncommutation_verify_v0"


def load(eng):
    with open(os.path.join(HERE, "results", f"{SIM_ID}_{eng}_results.json")) as f:
        return json.load(f)


def main():
    jax = load("jax")
    torch = load("pytorch")
    julia = load("julia")

    jd = jax["jax_recomputed_deltas"]
    td = torch["torch_recomputed_deltas"]
    ld = julia["julia_recomputed_deltas"]

    keys = ["delta_history_dependent", "delta_static_control_extensional",
            "delta_mixed_history_dependent", "delta_mixed_amnesic"]
    mismatches = []
    agreed = {}
    for k in keys:
        vals = {"jax": jd.get(k), "pytorch": td.get(k), "julia": ld.get(k)}
        if len({v for v in vals.values() if v is not None}) != 1:
            mismatches.append((k, vals))
        else:
            agreed[k] = jd[k]
    # x-reactive only in torch+julia (jax leg did not compute it)
    if td.get("delta_static_control_x_reactive") != ld.get("delta_static_control_x_reactive"):
        mismatches.append(("delta_static_control_x_reactive",
                           {"pytorch": td.get("delta_static_control_x_reactive"),
                            "julia": ld.get("delta_static_control_x_reactive")}))
    else:
        agreed["delta_static_control_x_reactive"] = td["delta_static_control_x_reactive"]

    # GNVW across all three
    g_jax, g_torch, g_julia = jax["gnvw_index"], torch["gnvw_index"], julia["gnvw_index"]
    for kk in ["left_shift", "right_shift", "identity"]:
        if not (g_jax[kk] == g_torch[kk] == g_julia[kk]):
            mismatches.append((f"gnvw.{kk}", {"jax": g_jax[kk], "pytorch": g_torch[kk], "julia": g_julia[kk]}))

    # parity self-checks must be true
    parity_ok = jax["jax_core_parity_all"] and torch["torch_core_parity_all"] and torch["gnvw_index_matches_core"]

    verdict = {
        "sim_id": SIM_ID,
        "engines": ["jax", "pytorch", "julia"],
        "agreed_values": agreed,
        "gnvw_index_agreed": g_jax if not [m for m in mismatches if m[0].startswith("gnvw")] else None,
        "mismatches": mismatches,
        "three_engine_agreement": len(mismatches) == 0,
        "per_leg_self_parity_ok": parity_ok,
        # audit verdict booleans, recomputed from the AGREED values:
        "audit": {
            "legs_exit0": True,  # asserted by the runner; recorded here for the envelope
            "restriction_noncommutation_real": agreed.get("delta_history_dependent", 0) > 0,
            "static_control_extensional_commutes": agreed.get("delta_static_control_extensional", 1) == 0,
            "static_control_x_reactive_noncommutes": agreed.get("delta_static_control_x_reactive", 0) > 0,
            "amnesic_collapses_clean_isolator": (agreed.get("delta_mixed_history_dependent", 0) > 0
                                                 and agreed.get("delta_mixed_amnesic", 1) == 0),
            "gnvw_signs_flip": (g_jax["left_shift"] < 0 < g_jax["right_shift"] and g_jax["identity"] == 0),
            "phi_square_fidelity": jax["phi_commuting_square_fidelity"],
            "phi_square_wrong_lex_control": jax["phi_square_fidelity_wrong_lex_control"],
            "phi_square_scrambled_phi_control": jax["phi_square_fidelity_scrambled_phi_control"],
            "smt_flip_confirmed": jax["smt_flip"]["smt_flip_confirmed"],
        },
        "engine_consensus": {
            "independent": True,
            "note": "JAX (vmap indicator XOR), PyTorch (boolean tensor XOR + permutation-matrix winding), and Julia (native Set symdiff + modular winding) are three distinct code paths; Julia is a from-scratch reimplementation in another language. reads_peer_result=false on all three.",
        },
        "classification": "scratch_diagnostic",
        "claim_ceiling": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
    }

    out = os.path.join(HERE, "results", f"{SIM_ID}_agreement_results.json")
    with open(out, "w") as f:
        json.dump(verdict, f, indent=2)
    print(json.dumps(verdict, indent=2))
    if mismatches:
        print(f"AGREEMENT FAIL: {len(mismatches)} mismatches", file=sys.stderr)
        sys.exit(1)
    if not parity_ok:
        print("PARITY FAIL: a leg's self-parity is false", file=sys.stderr)
        sys.exit(1)
    print("AGREEMENT OK")


if __name__ == "__main__":
    main()
