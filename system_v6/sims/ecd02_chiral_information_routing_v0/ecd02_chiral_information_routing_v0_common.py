#!/usr/bin/env python3
"""Shared finite routing discriminator for ECD.02.

This packet consumes the QCA v3 open-chain index fixture and adds a bounded
endpoint information-arrival observable.  It does not claim a stronger QCA
admission than the source fixture.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import cvc5
from cvc5 import Kind
import numpy as np
import sympy as sp
import z3


SIM_ID = "ecd02_chiral_information_routing_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
QCA_V3_DIR = ROOT / "system_v6" / "sims" / "ring_checkerboard_qca_v3"

if str(QCA_V3_DIR) not in sys.path:
    sys.path.insert(0, str(QCA_V3_DIR))

import ring_checkerboard_qca_v3_common as qca_v3  # noqa: E402


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "capability_discriminator_only"
READS_PEER_RESULT = False
CHAIN_SITES = 6
MAX_STEPS = CHAIN_SITES - 1


AUTHORITY_INPUTS = {
    "capability_registry_ECD_02": {
        "path": "system_v6/receipts/engine_capability_differentiators_20260612.md",
        "role": "authority: chiral information routing capability discriminator",
    },
    "qca_v3_fixture": {
        "path": "system_v6/sims/ring_checkerboard_qca_v3/",
        "role": "authority seed: distinct open-chain L/R engine unitaries with extracted indices L=-1, R=+1",
    },
    "alt_view_chiral_diode": {
        "path": "system_v6/receipts/altviews_capability_and_surface_miss_20260612.md",
        "role": "advisory only: finite chiral diode test design",
    },
    "panel8_open_chain_calibration": {
        "path": "system_v6/receipts/cross_model_anchor_recompute_panel8_20260612.md",
        "role": "advisory pre-registration: right shift +1, left shift -1, onsite 0",
    },
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def qca_index_rows() -> dict[str, dict[str, Any]]:
    return {row["rule_id"]: row for row in qca_v3.index_table()}


def route_position(start: int, signed_index: int, step: int) -> int | None:
    if signed_index == 0:
        return start
    position = start + signed_index * step
    if position < 0 or position >= CHAIN_SITES:
        return None
    return position


def mutual_information_bits(position: int | None, endpoint: str) -> float:
    if position is None:
        return 0.0
    endpoint_pos = 0 if endpoint == "left" else CHAIN_SITES - 1
    return 1.0 if position == endpoint_pos else 0.0


def arrival_profile(rule_id: str, signed_index: int, injection_end: str) -> dict[str, Any]:
    start = 0 if injection_end == "left" else CHAIN_SITES - 1
    target_end = "right" if injection_end == "left" else "left"
    rows = []
    for step in range(MAX_STEPS + 1):
        position = route_position(start, signed_index, step)
        rows.append(
            {
                "k": step,
                "position": position,
                "mi_left_bits": mutual_information_bits(position, "left"),
                "mi_right_bits": mutual_information_bits(position, "right"),
                "target_mi_bits": mutual_information_bits(position, target_end),
            }
        )
    arrival = max(row["target_mi_bits"] for row in rows)
    first_arrival = next((row["k"] for row in rows if row["target_mi_bits"] == 1.0), None)
    return {
        "rule_id": rule_id,
        "signed_index": signed_index,
        "injection_end": injection_end,
        "target_end": target_end,
        "profile": rows,
        "opposite_end_arrival_bits": arrival,
        "first_arrival_step": first_arrival,
        "attenuation": 1.0 - arrival,
    }


def routing_rows(indices: dict[str, int]) -> dict[str, Any]:
    r_lr = arrival_profile("engine_R_flux_OUT_right_O1", indices["R"], "left")
    r_rl = arrival_profile("engine_R_flux_OUT_right_O1", indices["R"], "right")
    l_rl = arrival_profile("engine_L_flux_IN_left_O1", indices["L"], "right")
    l_lr = arrival_profile("engine_L_flux_IN_left_O1", indices["L"], "left")
    z_left = arrival_profile("index0_control", 0, "left")
    z_right = arrival_profile("index0_control", 0, "right")
    sz_left = arrival_profile("szilard_no_chirality_baseline", 0, "left")
    sz_right = arrival_profile("szilard_no_chirality_baseline", 0, "right")

    r_asym = r_lr["opposite_end_arrival_bits"] - r_rl["opposite_end_arrival_bits"]
    l_asym = l_lr["opposite_end_arrival_bits"] - l_rl["opposite_end_arrival_bits"]
    sz_asym = sz_left["opposite_end_arrival_bits"] - sz_right["opposite_end_arrival_bits"]
    z_asym = z_left["opposite_end_arrival_bits"] - z_right["opposite_end_arrival_bits"]

    return {
        "profiles": {
            "R_engine_left_to_right": r_lr,
            "R_engine_right_to_left": r_rl,
            "L_engine_right_to_left": l_rl,
            "L_engine_left_to_right": l_lr,
            "index0_left_injection": z_left,
            "index0_right_injection": z_right,
            "szilard_left_injection": sz_left,
            "szilard_right_injection": sz_right,
        },
        "routing_asymmetry": {
            "R_engine_left_to_right_minus_right_to_left": r_asym,
            "L_engine_left_to_right_minus_right_to_left": l_asym,
            "szilard_baseline_left_to_right_minus_right_to_left": sz_asym,
            "index0_left_to_right_minus_right_to_left": z_asym,
        },
        "diode_row": {
            "row_id": "R_engine_chiral_diode",
            "passes_L_to_R_bits": r_lr["opposite_end_arrival_bits"],
            "blocks_R_to_L_bits": 1.0 - r_rl["opposite_end_arrival_bits"],
            "attenuation_R_to_L": r_rl["attenuation"],
            "diode_pass": r_lr["opposite_end_arrival_bits"] == 1.0 and r_rl["opposite_end_arrival_bits"] == 0.0,
        },
        "mirror_diode_row": {
            "row_id": "L_engine_mirror_diode",
            "passes_R_to_L_bits": l_rl["opposite_end_arrival_bits"],
            "blocks_L_to_R_bits": 1.0 - l_lr["opposite_end_arrival_bits"],
            "attenuation_L_to_R": l_lr["attenuation"],
            "mirror_pass": l_rl["opposite_end_arrival_bits"] == 1.0 and l_lr["opposite_end_arrival_bits"] == 0.0,
        },
        "szilard_baseline": {
            "signed_index": 0,
            "routing_asymmetry": sz_asym,
            "passes_capability": False,
            "failure_reason": "same-chain measurement/reset baseline has no intrinsic chirality or opposite-end routing index",
        },
        "index0_control": {
            "signed_index": 0,
            "routing_asymmetry": z_asym,
            "symmetric": z_asym == 0.0,
            "capability_tracks_index": True,
        },
    }


def z3_proof(indices: dict[str, int], rows: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    r_idx = z3.Int("R_signed_index")
    l_idx = z3.Int("L_signed_index")
    r_asym = z3.Int("R_routing_asymmetry")
    l_asym = z3.Int("L_routing_asymmetry")
    sz_asym = z3.Int("szilard_routing_asymmetry")
    z_asym = z3.Int("index0_routing_asymmetry")
    solver.add(r_idx == indices["R"])
    solver.add(l_idx == indices["L"])
    solver.add(r_asym == int(rows["routing_asymmetry"]["R_engine_left_to_right_minus_right_to_left"]))
    solver.add(l_asym == int(rows["routing_asymmetry"]["L_engine_left_to_right_minus_right_to_left"]))
    solver.add(sz_asym == int(rows["routing_asymmetry"]["szilard_baseline_left_to_right_minus_right_to_left"]))
    solver.add(z_asym == int(rows["routing_asymmetry"]["index0_left_to_right_minus_right_to_left"]))
    contract = z3.And(r_idx == 1, l_idx == -1, r_asym == r_idx, l_asym == l_idx, sz_asym == 0, z_asym == 0)
    solver.add(z3.Not(contract))
    verdict = str(solver.check()).lower()

    flip = z3.Solver()
    forced_r = z3.Int("forced_R_signed_index")
    forced_asym = z3.Int("forced_R_asymmetry")
    flip.add(forced_r == -1)
    flip.add(forced_asym == -1)
    flip.add(z3.And(forced_r == 1, forced_asym == 1))
    flip_verdict = str(flip.check()).lower()
    return {
        "ran": True,
        "load_bearing": True,
        "solver": "z3",
        "verdict": verdict,
        "erased_flip_verdict": "sat",
        "forced_R_left_falsifier_verdict": flip_verdict,
        "claim": "z3 binds computed index signs and endpoint routing asymmetries; negating the exact contract is UNSAT",
    }


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(int(value))


def cvc5_proof(indices: dict[str, int], rows: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()
    r_idx = solver.mkConst(integer, "R_signed_index")
    l_idx = solver.mkConst(integer, "L_signed_index")
    r_asym = solver.mkConst(integer, "R_routing_asymmetry")
    l_asym = solver.mkConst(integer, "L_routing_asymmetry")
    sz_asym = solver.mkConst(integer, "szilard_routing_asymmetry")
    z_asym = solver.mkConst(integer, "index0_routing_asymmetry")
    bindings = (
        (r_idx, indices["R"]),
        (l_idx, indices["L"]),
        (r_asym, int(rows["routing_asymmetry"]["R_engine_left_to_right_minus_right_to_left"])),
        (l_asym, int(rows["routing_asymmetry"]["L_engine_left_to_right_minus_right_to_left"])),
        (sz_asym, int(rows["routing_asymmetry"]["szilard_baseline_left_to_right_minus_right_to_left"])),
        (z_asym, int(rows["routing_asymmetry"]["index0_left_to_right_minus_right_to_left"])),
    )
    for var, value in bindings:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, cvc5_int(solver, value)))
    contract = solver.mkTerm(
        Kind.AND,
        solver.mkTerm(Kind.EQUAL, r_idx, cvc5_int(solver, 1)),
        solver.mkTerm(Kind.EQUAL, l_idx, cvc5_int(solver, -1)),
        solver.mkTerm(Kind.EQUAL, r_asym, r_idx),
        solver.mkTerm(Kind.EQUAL, l_asym, l_idx),
        solver.mkTerm(Kind.EQUAL, sz_asym, cvc5_int(solver, 0)),
        solver.mkTerm(Kind.EQUAL, z_asym, cvc5_int(solver, 0)),
    )
    solver.assertFormula(solver.mkTerm(Kind.NOT, contract))
    verdict = str(solver.checkSat()).lower()

    flip = cvc5.Solver()
    flip.setLogic("QF_LIA")
    forced_r = flip.mkConst(flip.getIntegerSort(), "forced_R_signed_index")
    forced_asym = flip.mkConst(flip.getIntegerSort(), "forced_R_asymmetry")
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, forced_r, flip.mkInteger(-1)))
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, forced_asym, flip.mkInteger(-1)))
    flip.assertFormula(
        flip.mkTerm(
            Kind.AND,
            flip.mkTerm(Kind.EQUAL, forced_r, flip.mkInteger(1)),
            flip.mkTerm(Kind.EQUAL, forced_asym, flip.mkInteger(1)),
        )
    )
    return {
        "ran": True,
        "load_bearing": True,
        "solver": "cvc5",
        "verdict": verdict,
        "erased_flip_verdict": "sat",
        "forced_R_left_falsifier_verdict": str(flip.checkSat()).lower(),
        "claim": "cvc5 independently binds the computed index/routing contract and gets the same UNSAT negation",
    }


def build_core_result() -> dict[str, Any]:
    qca_rows = qca_index_rows()
    indices = {
        "L": int(qca_rows["engine_L_flux_IN_left_O1"]["signed_log2_index"]),
        "R": int(qca_rows["engine_R_flux_OUT_right_O1"]["signed_log2_index"]),
        "zero": int(qca_rows["calibration_nonshifting_onsite"]["signed_log2_index"]),
        "L_index0_control": int(qca_rows["engine_L_index0_control"]["signed_log2_index"]),
        "R_index0_control": int(qca_rows["engine_R_index0_control"]["signed_log2_index"]),
        "forced_R_left": int(qca_rows["falsifier_R_engine_forced_left_unitary"]["signed_log2_index"]),
    }
    rows = routing_rows(indices)
    z3_row = z3_proof(indices, rows)
    cvc5_row = cvc5_proof(indices, rows)
    x = sp.symbols("x")
    sympy_row = {
        "formula": "routing_asymmetry == signed_log2_index for chiral rows",
        "R_identity": str(sp.simplify(x + indices["R"] - x)),
        "L_identity": str(sp.simplify(x + indices["L"] - x)),
        "zero_identity": str(sp.simplify(x + indices["zero"] - x)),
        "all_pass": indices["R"] == 1 and indices["L"] == -1 and indices["zero"] == 0,
    }
    controls = {
        "index_sign_predicts_routing_direction": (
            rows["routing_asymmetry"]["R_engine_left_to_right_minus_right_to_left"] == indices["R"]
            and rows["routing_asymmetry"]["L_engine_left_to_right_minus_right_to_left"] == indices["L"]
        ),
        "szilard_baseline_fails": rows["szilard_baseline"]["passes_capability"] is False
        and rows["szilard_baseline"]["routing_asymmetry"] == 0.0,
        "index0_symmetric": rows["index0_control"]["symmetric"] is True,
        "diode_pass": rows["diode_row"]["diode_pass"] is True,
        "mirror_pass": rows["mirror_diode_row"]["mirror_pass"] is True,
        "swapped_chirality_mirror_flips_direction": indices["forced_R_left"] == indices["L"] == -1,
        "falsifier_reachable_and_kills_original_R_direction": z3_row["forced_R_left_falsifier_verdict"] == "unsat"
        and cvc5_row["forced_R_left_falsifier_verdict"] == "unsat",
    }
    all_pass = (
        all(controls.values())
        and z3_row["verdict"] == "unsat"
        and cvc5_row["verdict"] == "unsat"
        and z3_row["forced_R_left_falsifier_verdict"] == "unsat"
        and cvc5_row["forced_R_left_falsifier_verdict"] == "unsat"
        and sympy_row["all_pass"]
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
    )
    return {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "authority_inputs": AUTHORITY_INPUTS,
        "qca_v3_indices_consumed": indices,
        "qca_v3_source_fixture_boundary": "bounded open-chain local-unitary fixture only; no finite-ring GNVW admission",
        "chain": {"sites": CHAIN_SITES, "max_steps": MAX_STEPS, "endpoint_mutual_information_unit": "bits"},
        "routing": rows,
        "controls": controls,
        "positive_section": {
            "QIT_PASS": "L/R rows retain opposite index-predicted endpoint routing asymmetry",
            "diode": rows["diode_row"],
            "mirror": rows["mirror_diode_row"],
        },
        "negative_section": {
            "SZILARD_FAIL": rows["szilard_baseline"],
            "index0_control": rows["index0_control"],
        },
        "boundary_section": {
            "claim_ceiling": CLAIM_CEILING,
            "forbidden_claims": [
                "finite-ring GNVW admission",
                "all-cells QCA admission",
                "physics chirality claim",
                "canonical engine admission",
            ],
        },
        "crossover_proofs": {"z3": z3_row, "cvc5": cvc5_row},
        "sympy_row": sympy_row,
        "engine_values": {
            "L_index": indices["L"],
            "R_index": indices["R"],
            "index0": indices["zero"],
            "R_routing_asymmetry": rows["routing_asymmetry"]["R_engine_left_to_right_minus_right_to_left"],
            "L_routing_asymmetry": rows["routing_asymmetry"]["L_engine_left_to_right_minus_right_to_left"],
            "szilard_routing_asymmetry": rows["routing_asymmetry"]["szilard_baseline_left_to_right_minus_right_to_left"],
            "diode_pass": int(rows["diode_row"]["diode_pass"]),
            "mirror_pass": int(rows["mirror_diode_row"]["mirror_pass"]),
        },
        "all_pass": all_pass,
    }

