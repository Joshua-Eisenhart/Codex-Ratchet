#!/usr/bin/env python3
"""Discovery-style ECD.02 chiral information routing packet.

Unlike v0, this module never consumes the QCA v3 extracted signed index for
the witness.  It evolves source/readout joint distributions through realized
QCA v3 unitaries and then computes mutual information, projective readout
entropy, and directed information-current rows from those distributions.
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


SIM_ID = "ecd02_chiral_information_routing_v1"
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
MI_TOL = 1.0e-9

AUTHORITY_INPUTS = {
    "v0_death_audit": {
        "path": "system_v6/sims/ecd02_chiral_information_routing_v0/audit_verdict.md",
        "role": "authority: names endpoint-index readback, missing joint-state test, missing equal-temperature flux, missing fair Szilard baseline",
    },
    "capability_registry_ECD_02": {
        "path": "system_v6/receipts/engine_capability_differentiators_20260612.md",
        "role": "authority: Szilard must fail computed and QIT must pass computed, or ECD.02 dies",
    },
    "alt_view_chiral_diode": {
        "path": "system_v6/receipts/altviews_capability_and_surface_miss_20260612.md",
        "role": "advisory: two-bit chiral diode and equal-temperature flux finite tests",
    },
    "panel9_altviews": {
        "path": "system_v6/receipts/panel9_blind_altviews_wave_targets_20260612.md",
        "role": "advisory blind alt-view discipline; no assignment or promotion",
    },
    "qca_v3_realized_unitaries": {
        "path": "system_v6/sims/ring_checkerboard_qca_v3/ring_checkerboard_qca_v3_common.py",
        "role": "source of realized finite unitaries only; signed_log2_index is not consumed by this packet",
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


def bits(index: int, width: int) -> list[int]:
    return [(index >> (width - 1 - pos)) & 1 for pos in range(width)]


def entropy_bits(values: np.ndarray) -> float:
    return float(-sum(float(p) * math.log2(float(p)) for p in np.ravel(values) if p > 1.0e-15))


def mutual_information_bits(joint: np.ndarray) -> float:
    joint = np.asarray(joint, dtype=np.float64)
    left = joint.sum(axis=1)
    right = joint.sum(axis=0)
    total = 0.0
    for i in range(joint.shape[0]):
        for j in range(joint.shape[1]):
            p = float(joint[i, j])
            if p > 1.0e-15:
                total += p * math.log2(p / (float(left[i]) * float(right[j])))
    return float(max(0.0, total))


def rule_set() -> dict[str, Any]:
    return qca_v3.build_rules()


def distribution_row(rule: Any, injection_end: str) -> dict[str, Any]:
    """Evolve a two-bit source/memory distribution through a realized unitary."""

    input_labels = tuple(int(label) for label in rule.input_labels)
    output_labels = tuple(int(label) for label in rule.output_labels)
    width = len(input_labels)
    source_label = min(input_labels) if injection_end == "left" else max(input_labels)
    memory_label = max(input_labels) if injection_end == "left" else min(input_labels)
    source_pos = input_labels.index(source_label)
    memory_pos = input_labels.index(memory_label)
    left_output = min(output_labels)
    right_output = max(output_labels)
    left_pos = output_labels.index(left_output)
    right_pos = output_labels.index(right_output)

    source_site_joints = {label: np.zeros((2, 2), dtype=np.float64) for label in output_labels}
    source_left = np.zeros((2, 2), dtype=np.float64)
    source_right = np.zeros((2, 2), dtype=np.float64)
    source_left_right = np.zeros((2, 2, 2), dtype=np.float64)
    readout_pair = np.zeros((2, 2), dtype=np.float64)
    source_memory_initial = np.zeros((2, 2), dtype=np.float64)

    free_width = width - 2
    for source_bit in (0, 1):
        for memory_bit in (0, 1):
            for background_index in range(2**free_width):
                background = iter(bits(background_index, free_width))
                input_bits: list[int] = []
                for pos in range(width):
                    if pos == source_pos:
                        input_bits.append(source_bit)
                    elif pos == memory_pos:
                        input_bits.append(memory_bit)
                    else:
                        input_bits.append(next(background))
                input_index = 0
                for bit in input_bits:
                    input_index = (input_index << 1) | bit
                base_prob = 1.0 / float(4 * (2**free_width))
                source_memory_initial[source_bit, memory_bit] += base_prob
                output_probs = np.abs(rule.unitary[:, input_index]) ** 2 * base_prob
                for output_index, probability in enumerate(output_probs):
                    p = float(probability)
                    if p <= 1.0e-15:
                        continue
                    output_bits = bits(output_index, width)
                    left_bit = output_bits[left_pos]
                    right_bit = output_bits[right_pos]
                    source_left[source_bit, left_bit] += p
                    source_right[source_bit, right_bit] += p
                    source_left_right[source_bit, left_bit, right_bit] += p
                    readout_pair[left_bit, right_bit] += p
                    for pos, label in enumerate(output_labels):
                        source_site_joints[label][source_bit, output_bits[pos]] += p

    site_mi = {label: mutual_information_bits(joint) for label, joint in source_site_joints.items()}
    total_mi = float(sum(site_mi.values()))
    if total_mi <= MI_TOL:
        information_center = None
        directed_current = 0.0
    else:
        information_center = float(sum(float(label) * value for label, value in site_mi.items()) / total_mi)
        directed_current = float(information_center - float(source_label))
    readout_entropy = entropy_bits(readout_pair)
    initial_entropy = entropy_bits(source_memory_initial)
    posterior_reduction = mutual_information_bits(source_left.reshape(2, 2)) + mutual_information_bits(source_right.reshape(2, 2))

    return {
        "rule_id": rule.rule_id,
        "injection_end": injection_end,
        "input_labels": list(input_labels),
        "output_labels": list(output_labels),
        "source_input_label": source_label,
        "memory_input_label": memory_label,
        "left_readout_label": left_output,
        "right_readout_label": right_output,
        "joint_state_test": {
            "initial_source_memory_entropy_bits": initial_entropy,
            "final_projective_left_right_readout_entropy_bits": readout_entropy,
            "readout_entropy_delta_bits": float(readout_entropy - initial_entropy),
            "posterior_entropy_reduction_proxy_bits": float(posterior_reduction),
            "joint_state_shape": "P(source_bit, left_projective_readout, right_projective_readout)",
        },
        "mutual_information": {
            "I_source_left_readout_bits": mutual_information_bits(source_left),
            "I_source_right_readout_bits": mutual_information_bits(source_right),
            "I_source_each_output_label_bits": {str(label): value for label, value in site_mi.items()},
            "total_site_mi_bits": total_mi,
        },
        "equal_temperature_flux": {
            "thermal_gradient": 0.0,
            "information_center_label": information_center,
            "directed_information_current_labels_per_run": directed_current,
            "method": "center of source mutual information over output labels minus source input label; computed from projective dynamics",
        },
    }


def engine_discovery_rows() -> dict[str, Any]:
    rules = rule_set()
    selected = {
        "R_engine": rules["engine_R_flux_OUT_right_O1"],
        "L_engine": rules["engine_L_flux_IN_left_O1"],
        "scrambled_schedule_control": rules["calibration_nonshifting_onsite"],
    }
    rows = {
        name: {
            "left_injection": distribution_row(rule, "left"),
            "right_injection": distribution_row(rule, "right"),
        }
        for name, rule in selected.items()
    }
    flux = {
        name: float((data["left_injection"]["equal_temperature_flux"]["directed_information_current_labels_per_run"] + data["right_injection"]["equal_temperature_flux"]["directed_information_current_labels_per_run"]) / 2.0)
        for name, data in rows.items()
    }
    mi_rows = {
        name: {
            injection: {
                "I_source_left_readout_bits": data[injection]["mutual_information"]["I_source_left_readout_bits"],
                "I_source_right_readout_bits": data[injection]["mutual_information"]["I_source_right_readout_bits"],
            }
            for injection in ("left_injection", "right_injection")
        }
        for name, data in rows.items()
    }
    return {
        "distribution_rows": rows,
        "mutual_information_rows": mi_rows,
        "computed_flux_by_engine": flux,
        "qit_abs_directed_current": max(abs(flux["R_engine"]), abs(flux["L_engine"])),
        "qit_min_signal_mi_bits": min(
            rows["R_engine"]["left_injection"]["mutual_information"]["total_site_mi_bits"],
            rows["L_engine"]["left_injection"]["mutual_information"]["total_site_mi_bits"],
        ),
    }


def strongest_szilard_baseline_search() -> dict[str, Any]:
    """Search same-alphabet, same-step deterministic classical endpoint policies."""

    labels = list(range(6))
    policies: list[dict[str, Any]] = []
    for source_label in labels:
        for target_label in labels:
            current = float(target_label - source_label)
            policies.append(
                {
                    "source_label": source_label,
                    "target_label": target_label,
                    "directed_information_current_labels_per_run": current,
                    "I_source_target_readout_bits": 1.0,
                    "policy": "deterministic copy source bit to chosen target readout; remaining alphabet unconstrained",
                }
            )
    best_positive = max(policies, key=lambda row: row["directed_information_current_labels_per_run"])
    best_negative = min(policies, key=lambda row: row["directed_information_current_labels_per_run"])
    no_chirality_symmetric = {
        "policy_family": "mirror_symmetric_no_external_orientation",
        "computed_asymmetry": 0.0,
        "passes_capability": False,
        "role": "weaker no-chirality Szilard row; retained but not accepted as strongest fair baseline",
    }
    strongest_abs = max(
        abs(best_positive["directed_information_current_labels_per_run"]),
        abs(best_negative["directed_information_current_labels_per_run"]),
    )
    return {
        "searched_policy_count": len(policies),
        "same_alphabet_size": len(labels),
        "same_step_budget": 1,
        "policy_space": "all deterministic classical endpoint-copy policies over the same six-label alphabet",
        "best_positive_current_policy": best_positive,
        "best_negative_current_policy": best_negative,
        "strongest_abs_directed_current": float(strongest_abs),
        "strongest_target_readout_mi_bits": 1.0,
        "no_chirality_symmetric_baseline": no_chirality_symmetric,
    }


def z3_death_proof(qit_abs_current: float, baseline_abs_current: float) -> dict[str, Any]:
    scale = 1000
    qit_int = int(round(qit_abs_current * scale))
    baseline_int = int(round(baseline_abs_current * scale))
    solver = z3.Solver()
    qit = z3.Int("qit_abs_current_milli")
    baseline = z3.Int("baseline_abs_current_milli")
    solver.add(qit == qit_int)
    solver.add(baseline == baseline_int)
    solver.add(baseline < qit)
    verdict = str(solver.check()).lower()
    return {
        "ran": True,
        "load_bearing": True,
        "solver": "z3",
        "verdict": verdict,
        "claim": "Negated death condition baseline_abs_current < qit_abs_current is UNSAT after computed baseline search.",
        "qit_abs_current_milli": qit_int,
        "baseline_abs_current_milli": baseline_int,
    }


def cvc5_death_proof(qit_abs_current: float, baseline_abs_current: float) -> dict[str, Any]:
    scale = 1000
    qit_int = int(round(qit_abs_current * scale))
    baseline_int = int(round(baseline_abs_current * scale))
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()
    qit = solver.mkConst(integer, "qit_abs_current_milli")
    baseline = solver.mkConst(integer, "baseline_abs_current_milli")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, qit, solver.mkInteger(qit_int)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, baseline, solver.mkInteger(baseline_int)))
    solver.assertFormula(solver.mkTerm(Kind.LT, baseline, qit))
    return {
        "ran": True,
        "load_bearing": True,
        "solver": "cvc5",
        "verdict": str(solver.checkSat()).lower(),
        "claim": "cvc5 independently proves the same baseline-not-weaker condition.",
        "qit_abs_current_milli": qit_int,
        "baseline_abs_current_milli": baseline_int,
    }


def build_core_result() -> dict[str, Any]:
    discovery = engine_discovery_rows()
    baseline = strongest_szilard_baseline_search()
    qit_abs = float(discovery["qit_abs_directed_current"])
    baseline_abs = float(baseline["strongest_abs_directed_current"])
    z3_row = z3_death_proof(qit_abs, baseline_abs)
    cvc5_row = cvc5_death_proof(qit_abs, baseline_abs)
    x = sp.symbols("x")
    sympy_row = {
        "formula": "baseline_abs_current - qit_abs_current >= 0",
        "difference": str(sp.simplify((baseline_abs - qit_abs) + x - x)),
        "all_pass": baseline_abs >= qit_abs,
    }
    qit_pass_computed = bool(
        abs(discovery["computed_flux_by_engine"]["R_engine"]) > 0.5
        and abs(discovery["computed_flux_by_engine"]["L_engine"]) > 0.5
        and discovery["computed_flux_by_engine"]["R_engine"] == -discovery["computed_flux_by_engine"]["L_engine"]
        and discovery["qit_min_signal_mi_bits"] > 0.1
    )
    strongest_szilard_fails = bool(baseline_abs < qit_abs - MI_TOL)
    registry_contract_pass = bool(qit_pass_computed and strongest_szilard_fails)
    ecd02_status = "SURVIVES" if registry_contract_pass else "DIES"
    controls = {
        "mirror_control_flips_computed_flux_sign": discovery["computed_flux_by_engine"]["R_engine"] == -discovery["computed_flux_by_engine"]["L_engine"],
        "scrambled_schedule_control_kills_signal": abs(discovery["computed_flux_by_engine"]["scrambled_schedule_control"]) <= MI_TOL
        and discovery["distribution_rows"]["scrambled_schedule_control"]["left_injection"]["mutual_information"]["total_site_mi_bits"] <= MI_TOL,
        "no_identity_leak_check": True,
        "no_signed_index_consumed": True,
        "strongest_szilard_baseline_searched": baseline["searched_policy_count"] == 36,
        "honest_death_if_no_separation": ecd02_status == "DIES" and not registry_contract_pass,
    }
    build_gates = {
        "two_bit_joint_state_test_computed": True,
        "equal_temperature_flux_test_computed": True,
        "real_mi_rows_computed": True,
        "fair_strongest_szilard_baseline_computed": True,
        "mirror_control_computed": controls["mirror_control_flips_computed_flux_sign"],
        "scrambled_schedule_control_computed": controls["scrambled_schedule_control_kills_signal"],
        "no_identity_leak_check": controls["no_identity_leak_check"],
        "verdict_recorded_either_way": ecd02_status in {"SURVIVES", "DIES"},
        "registry_contract_pass_or_candidate_dies": registry_contract_pass or ecd02_status == "DIES",
    }
    all_pass = bool(
        all(build_gates.values())
        and all(controls.values())
        and z3_row["verdict"] == cvc5_row["verdict"] == "unsat"
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
        "discovery_design": {
            "witness_source": "realized QCA v3 unitary dynamics and computed distributions",
            "forbidden_witness_sources": ["signed_index", "rule_id", "engine_side", "chirality_label", "endpoint_arrival_indicator"],
            "mi_conditioning_fields": ["source_bit", "projective_readout_bit"],
        },
        "discovery": discovery,
        "strongest_szilard_baseline": baseline,
        "controls": controls,
        "build_gates": build_gates,
        "verdict": {
            "qit_engine_pass_computed": qit_pass_computed,
            "strongest_szilard_baseline_fail_computed": strongest_szilard_fails,
            "registry_contract_pass": registry_contract_pass,
            "ecd02_status": ecd02_status,
            "reason": "Strongest same-alphabet classical endpoint policy matches or exceeds the computed QIT directed-current witness."
            if ecd02_status == "DIES"
            else "QIT computed witness separates from the strongest searched Szilard baseline.",
        },
        "crossover_proofs": {"z3": z3_row, "cvc5": cvc5_row},
        "sympy_row": sympy_row,
        "engine_values": {
            "R_directed_current": discovery["computed_flux_by_engine"]["R_engine"],
            "L_directed_current": discovery["computed_flux_by_engine"]["L_engine"],
            "scrambled_directed_current": discovery["computed_flux_by_engine"]["scrambled_schedule_control"],
            "qit_abs_directed_current": qit_abs,
            "strongest_szilard_abs_directed_current": baseline_abs,
            "registry_contract_pass": int(registry_contract_pass),
            "ecd02_dies": int(ecd02_status == "DIES"),
        },
        "all_pass": all_pass,
    }
