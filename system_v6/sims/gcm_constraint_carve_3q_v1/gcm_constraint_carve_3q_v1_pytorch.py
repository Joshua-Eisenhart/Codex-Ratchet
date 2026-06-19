#!/usr/bin/env python3
"""PyTorch lane for matrix-derived probe and count checks."""

from __future__ import annotations

import json

import sympy as sp
import torch
from torch.func import vmap

from gcm_constraint_carve_3q_v1_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    SIM_ID,
    build_packet,
    rel,
    write_json,
)


RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"


def build_result() -> dict[str, object]:
    packet = build_packet()
    first_xz = torch.tensor(
        [
            [row["constraints"]["C2"]["first_bloch_from_rho_A"][0], row["constraints"]["C2"]["first_bloch_from_rho_A"][2]]
            for row in packet["constraint_matrix"]
        ],
        dtype=torch.float64,
    )

    def signature(xz: torch.Tensor) -> torch.Tensor:
        return torch.round(2.0 * xz)

    signatures = vmap(signature)(first_xz)
    active = torch.any(signatures != 0, dim=1)
    matrix_active = torch.tensor([row["constraints"]["C2"]["pass"] for row in packet["constraint_matrix"]], dtype=torch.bool)
    exact_survivors = sp.Rational(packet["survivor_count"], 1)
    exact_classes = sp.Rational(packet["quotient"]["class_count"], 1)
    all_pass = (
        torch.equal(active, matrix_active)
        and sp.simplify(exact_survivors - 545) == 0
        and sp.simplify(exact_classes - 9) == 0
        and packet["monogamy_ckw_recomputed_from_stored_rho"]["all_party_cuts_satisfy_ckw"] is True
    )
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
        "source_path": rel(__import__("pathlib").Path(__file__)),
        "result_path": rel(RESULT_PATH),
        "packages_used": ["torch", "torch.func", "sympy"],
        "aligned_packages_load_bearing": ["torch.func", "sympy"],
        "package_observables": {
            "torch.func": "vmap recomputes C2 active-probe pass/fail from matrix-derived first-qubit x/z rows",
            "sympy": "sp.Rational exact survivor/class count guards",
        },
        "candidate_count": packet["candidate_space"]["candidate_count"],
        "survivor_count": packet["survivor_count"],
        "quotient_class_count": packet["quotient"]["class_count"],
        "active_probe_true_count": int(torch.sum(active).item()),
        "matrix_active_matches": bool(torch.equal(active, matrix_active)),
        "all_pass": bool(all_pass),
    }


def main() -> int:
    payload = build_result()
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
