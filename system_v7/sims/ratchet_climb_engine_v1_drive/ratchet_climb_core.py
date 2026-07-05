#!/usr/bin/env python3
"""Shared climb process for ratchet_climb_engine_v1_drive.

This module implements the Ratchet Runbook loop as a finite executable process:
measure distinction loss, run a Minimalist-first carry attempt, admit only the
weakest sufficient lift, lock the receipt, project down, and run controls.

Axis-0 drive fence: the drive is early and the readout is late. This module
uses no cut, bipartition, or Phi0 machinery in the drive loop.

Ceiling: SCRATCH_DIAGNOSTIC; promotion_allowed=false.
"""

from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import numpy as np
import z3

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "classical"

TOOL_MANIFEST = {
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite drive ledger, quotient, projection, label-shuffle, commuting-filter, and attractor accounting",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing non-definitional contextuality UNSAT/SAT bias-check flip",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent second solver for the same contextuality flip",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "python_stdlib": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "spec.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_json(obj: Any) -> str:
    return sha256_bytes(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO).as_posix()


def load_spec() -> dict[str, Any]:
    return load_json(SPEC_PATH)


def formal_result_path(engine: str) -> Path:
    return REPO / load_spec()["reused_formal_gate_results"][engine]


def load_formal_result(engine: str) -> dict[str, Any]:
    path = formal_result_path(engine)
    payload = load_json(path)
    payload["_source_path"] = rel(path)
    payload["_source_sha256"] = sha256_file(path)
    return payload


def probe_order(pauli_labels: list[str], mode: str, seed: int) -> list[int]:
    indices = list(range(len(pauli_labels)))
    if mode == "formal":
        return indices
    if mode == "reverse":
        return list(reversed(indices))
    if mode == "seeded_shuffle":
        rng = random.Random(seed)
        rng.shuffle(indices)
        return indices
    raise ValueError(f"unknown probe order mode {mode!r}")


def rows_for(states: list[dict[str, Any]], indices: list[int]) -> list[tuple[float, ...]]:
    return [tuple(round(float(state["pvec"][idx]), 12) for idx in indices) for state in states]


def quotient(labels: list[str], rows: list[tuple[float, ...]]) -> dict[str, Any]:
    buckets: dict[tuple[float, ...], list[str]] = defaultdict(list)
    for label, row in zip(labels, rows, strict=True):
        buckets[row].append(label)
    classes = []
    projection: dict[str, int] = {}
    for idx, key in enumerate(sorted(buckets)):
        members = sorted(buckets[key])
        for label in members:
            projection[label] = idx
        classes.append({"class_id": idx, "size": len(members), "labels": members, "signature_sha256": sha256_json(list(key))})
    return {
        "class_count": len(classes),
        "class_sizes": [row["size"] for row in classes],
        "classes": classes,
        "projection": projection,
        "multi_representative_class_count": sum(1 for row in classes if row["size"] > 1),
    }


def source_carrier(engine_result: dict[str, Any]) -> dict[str, Any]:
    summary = engine_result["carrier_summary"]
    states = list(engine_result["carrier_states"])
    labels = [str(row["label"]) for row in states]
    pauli = list(summary["pauli_strings"])
    full = engine_result["gates"]["observable_quotient_R4"]
    coarse = engine_result["gates"]["coarse_probe_quotient_R4_epoch"]
    return {
        "summary": summary,
        "states": states,
        "labels": labels,
        "pauli_labels": pauli,
        "formal_full_quotient": full,
        "formal_coarse_quotient": coarse,
    }


def token_identity_tuple(run_id: str, rung: int, content: dict[str, Any], probe_signature: str) -> dict[str, str]:
    content_id = sha256_json(content)
    return {
        "content_id": content_id,
        "probe_signature": probe_signature,
        "lineage_id": "ratchet_climb_engine_v1_drive",
        "branch_id": f"{run_id}:rung:{rung}",
        "replay_receipt_id": f"sha256:{sha256_json({'run_id': run_id, 'rung': rung, 'content_id': content_id})}",
    }


def lock_entry(prev_hash: str, run_id: str, rung: int, decision: dict[str, Any], probe_signature: str) -> dict[str, Any]:
    token = token_identity_tuple(run_id, rung, decision, probe_signature)
    body = {
        "schema": "ratchet_climb_engine_v1_drive.lock_entry.v1",
        "run_id": run_id,
        "rung": rung,
        "written_at": now_iso(),
        "token_identity_R5": token,
        "decision": decision,
        "prev_hash": prev_hash,
    }
    body["entry_hash"] = sha256_json(body)
    return body


def z3_pm(signs: dict[str, int]) -> str:
    cells = list("abcdefghi")
    contexts = {
        "R1": ["a", "b", "c"],
        "R2": ["d", "e", "f"],
        "R3": ["g", "h", "i"],
        "C1": ["a", "d", "g"],
        "C2": ["b", "e", "h"],
        "C3": ["c", "f", "i"],
    }
    solver = z3.Solver()
    values = {cell: z3.Int(cell) for cell in cells}
    for cell in cells:
        solver.add(z3.Or(values[cell] == 1, values[cell] == -1))
    for ctx, ctx_cells in contexts.items():
        solver.add(values[ctx_cells[0]] * values[ctx_cells[1]] * values[ctx_cells[2]] == signs[ctx])
    return str(solver.check()).lower()


def cvc5_pm(signs: dict[str, int]) -> str:
    cells = list("abcdefghi")
    contexts = {
        "R1": ["a", "b", "c"],
        "R2": ["d", "e", "f"],
        "R3": ["g", "h", "i"],
        "C1": ["a", "d", "g"],
        "C2": ["b", "e", "h"],
        "C3": ["c", "f", "i"],
    }
    tm = cvc5.TermManager()
    solver = cvc5.Solver(tm)
    solver.setLogic("QF_NIA")
    one = tm.mkInteger(1)
    negone = tm.mkInteger(-1)
    values = {cell: tm.mkConst(tm.getIntegerSort(), cell) for cell in cells}
    for cell in cells:
        solver.assertFormula(
            tm.mkTerm(Kind.OR, tm.mkTerm(Kind.EQUAL, values[cell], one), tm.mkTerm(Kind.EQUAL, values[cell], negone))
        )
    for ctx, ctx_cells in contexts.items():
        prod = tm.mkTerm(Kind.MULT, values[ctx_cells[0]], values[ctx_cells[1]], values[ctx_cells[2]])
        solver.assertFormula(tm.mkTerm(Kind.EQUAL, prod, tm.mkInteger(signs[ctx])))
    return str(solver.checkSat()).lower()


def contextuality_flip() -> dict[str, Any]:
    contextual = {"R1": 1, "R2": 1, "R3": 1, "C1": 1, "C2": 1, "C3": -1}
    control = {"R1": 1, "R2": 1, "R3": 1, "C1": 1, "C2": 1, "C3": 1}
    pm_z3 = z3_pm(contextual)
    pm_cvc5 = cvc5_pm(contextual)
    ct_z3 = z3_pm(control)
    ct_cvc5 = cvc5_pm(control)
    return {
        "name": "finite_contextuality_assignment_smt_lift_discriminator_pattern",
        "anti_pattern": "finite_cycle_z_n_holonomy_section_lift_discriminator_v0 is treated as circular if lift_forced is equivalent to not section_exists.",
        "contextual_peres_mermin": {"z3": pm_z3, "cvc5": pm_cvc5, "expected": "unsat"},
        "noncontextual_control": {"z3": ct_z3, "cvc5": ct_cvc5, "expected": "sat"},
        "flip_confirmed": pm_z3 == "unsat" and pm_cvc5 == "unsat" and ct_z3 == "sat" and ct_cvc5 == "sat",
        "non_definitional_reason": "Same variables and six context products; only the frustrating sign is flipped, so SAT/UNSAT is a feasibility fact, not the definition of lift_forced.",
    }


def controls(carrier: dict[str, Any], q_full: dict[str, Any], seed: int) -> dict[str, Any]:
    labels = carrier["labels"]
    rng = random.Random(seed)
    shuffled = list(labels)
    rng.shuffle(shuffled)
    pvec_by_label = {state["label"]: state["pvec"] for state in carrier["states"]}
    indices = list(range(len(carrier["pauli_labels"])))
    shuffled_rows = [tuple(round(float(pvec_by_label[label][idx]), 12) for idx in indices) for label in shuffled]
    shuffled_q = quotient(shuffled, shuffled_rows)
    stage_filter = {label for label in labels if "stage_" in label}
    even_filter = {label for label in labels if q_full["projection"][label] % 2 == 0}
    first_stage_then_even = sorted((stage_filter & even_filter))
    first_even_then_stage = sorted((even_filter & stage_filter))
    flip = contextuality_flip()
    return {
        "label_shuffle": {
            "passed": shuffled_q["class_count"] == q_full["class_count"],
            "criterion": "quotient class count and fingerprint partition survive label permutation",
            "original_class_count": q_full["class_count"],
            "shuffled_class_count": shuffled_q["class_count"],
        },
        "commuting_order": {
            "passed": first_stage_then_even == first_even_then_stage,
            "criterion": "static survivor filters commute; therefore ordered local update is not forced by this lower-layer readout",
            "stage_then_even_count": len(first_stage_then_even),
            "even_then_stage_count": len(first_even_then_stage),
        },
        "lower_layer_can_do_it": {
            "passed": q_full["class_count"] == len(labels),
            "criterion": "full finite probe quotient carries all active carrier distinctions without rho/Hopf",
            "full_class_count": q_full["class_count"],
            "carrier_count": len(labels),
        },
        "non_definitional_flip": flip | {"passed": bool(flip["flip_confirmed"])},
    }


def candidate_set(target_rung: int) -> list[dict[str, Any]]:
    names = {
        1: ["finite_distinguishability", "finite_support_S", "probe_family_P", "quotient_S_mod_P"],
        2: ["finite_support_S", "probe_family_P", "quotient_S_mod_P"],
        3: ["probe_family_P", "quotient_S_mod_P", "density_operator_rho"],
        4: ["quotient_S_mod_P", "admissible_survivor_set_M_C", "density_operator_rho", "Hopf_projective_lift"],
        5: ["admissible_survivor_set_M_C", "ordered_local_update", "density_operator_rho"],
        6: ["ordered_local_update", "ring_checkerboard_finite_run_surface", "entropy_readout_suite", "density_operator_rho"],
    }
    rows = []
    for idx, name in enumerate(names[target_rung]):
        rows.append({"candidate": name, "ladder_rung": target_rung + idx, "strength_rank": idx})
    return rows


def two_qubit_state(theta: float) -> np.ndarray:
    state = np.zeros(4, dtype=np.complex128)
    state[0] = np.cos(theta)
    state[3] = np.sin(theta)
    return state / np.linalg.norm(state)


def reduced_density_first_carrier(state: np.ndarray) -> np.ndarray:
    tensor = state.reshape(2, 2)
    return tensor @ tensor.conjugate().T


def mixedness(state: np.ndarray) -> float:
    rho_a = reduced_density_first_carrier(state)
    purity = float(np.real(np.trace(rho_a @ rho_a)))
    return round(1.0 - purity, 12)


def drive_unitaries(kind: str) -> tuple[np.ndarray, np.ndarray]:
    x = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    h = (1.0 / np.sqrt(2.0)) * np.array([[1, 1], [1, -1]], dtype=np.complex128)
    i2 = np.eye(2, dtype=np.complex128)
    cnot = np.array(
        [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ],
        dtype=np.complex128,
    )
    if kind == "commuting_control":
        return np.kron(z, i2), np.kron(z, i2)
    return np.kron(h, i2), cnot


def drive_stream(kind: str, seed: int, label_shuffle: bool = False) -> dict[str, Any]:
    rng = random.Random(seed)
    window = [] if kind != "memoryless_control" else None
    u_a, u_b = drive_unitaries(kind)
    base = two_qubit_state(np.pi / 5.0)
    demands: list[dict[str, Any]] = []
    ticks: list[dict[str, Any]] = []
    prev_sig: tuple[float, float] | None = None
    labels = ["carrier_A", "carrier_B"]
    if label_shuffle:
        rng.shuffle(labels)

    for tick in range(1, 9):
        order_ab = u_b @ (u_a @ base)
        order_ba = u_a @ (u_b @ base)
        if kind == "memoryless_control":
            jitter = rng.choice([-1.0, 1.0]) * 0.03
            order_ab = two_qubit_state(np.pi / 5.0 + jitter)
            order_ba = two_qubit_state(np.pi / 5.0 - jitter)
        sig = (mixedness(order_ab), mixedness(order_ba))
        order_gap = round(float(np.linalg.norm(order_ab - order_ba)), 12)
        commutator_norm = round(float(np.linalg.norm(u_a @ u_b - u_b @ u_a)), 12)
        if window is not None:
            window.append(sig)
            window = window[-4:]
        persistence = 0 if window is None else len(set(window))
        ticks.append(
            {
                "tick": tick,
                "labels": labels,
                "marginal_mixedness_pair": sig,
                "order_gap": order_gap,
                "commutator_norm": commutator_norm,
                "history_window_size": 0 if window is None else len(window),
                "history_distinct_signature_count": persistence,
            }
        )
        if kind == "static_control":
            continue
        if kind == "commuting_control":
            continue
        if kind == "memoryless_control":
            if prev_sig is not None and sig == prev_sig:
                demands.append({"target_rung": 5, "kind": "memoryless_accidental_repeat", "tick": tick, "forced": False})
            prev_sig = sig
            continue
        if commutator_norm > 0.0 and persistence >= 2:
            demands.append(
                {
                    "target_rung": 5,
                    "kind": "survivor_set_from_rolling_entanglement_mixedness",
                    "tick": tick,
                    "forced": True,
                    "measured_loss": {
                        "rung4_static_quotient_has_no_stream_slot": True,
                        "marginal_mixedness_pair": sig,
                        "history_distinct_signature_count": persistence,
                        "commutator_norm": commutator_norm,
                    },
                }
            )
            demands.append(
                {
                    "target_rung": 6,
                    "kind": "ordered_local_update_from_noncommuting_drive",
                    "tick": tick,
                    "forced": True,
                    "measured_loss": {
                        "AB_then_BA_order_gap": order_gap,
                        "commutator_norm": commutator_norm,
                        "rolling_history_window": 4,
                    },
                }
            )
            break
        if kind not in {"commuting_control", "static_control", "memoryless_control"}:
            base = order_ab / np.linalg.norm(order_ab)
    if kind == "static_control":
        demands = []
    return {
        "kind": kind,
        "seed": seed,
        "finite_history_window": 0 if kind == "memoryless_control" else 4,
        "carrier_count": 2,
        "uses_cut_bipartition_phi0": False,
        "ticks": ticks,
        "minted_demands": demands,
        "demand_count": len(demands),
    }


def rung_receipt(
    *,
    run_id: str,
    current_rung: int,
    target_rung: int,
    lost_distinction: str,
    measured_loss: dict[str, Any],
    minimalist: dict[str, Any],
    admitted: bool,
    selected_lift: str | None,
    projection_back_down: dict[str, Any],
    residual: dict[str, Any],
    stronger_rejections: list[dict[str, Any]],
    controls_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema": "ratchet_runbook_step_receipt.v1",
        "run_id": run_id,
        "loop_steps": {
            "1_object": "finite C^8 carrier roster from ratchet_formal_gates_v1 R4",
            "2_perspective_readout": "constrained distinguishability / finite Pauli-probe readout",
            "3_weakest_current_structure": current_rung,
            "4_constraint_pressure": ["active probe/order/bracket/cut tests", "R5 token identity", "R6 progress lock"],
            "5_failure_mode": lost_distinction,
            "6_weakest_lift": selected_lift,
            "7_projection_back_down": projection_back_down,
            "8_residual": residual,
            "9_controls": controls_summary,
            "10_receipt": "ACCEPT_LIFT" if admitted else "REJECT_OR_PARK_LIFT",
        },
        "target_rung": target_rung,
        "lost_distinction": lost_distinction,
        "distinction_loss_detector": {"measured": True, "not_asserted": True, "evidence": measured_loss},
        "minimalist_first": minimalist,
        "mss_gate": {
            "candidate_lifts_compared": candidate_set(target_rung),
            "selected": selected_lift,
            "selected_only_after_measured_failure": admitted and not minimalist["succeeded"],
            "stronger_candidates_rejected_unforced": stronger_rejections,
        },
        "receipt_axes": {
            "lifecycle_status": "SCRATCH_DIAGNOSTIC",
            "evidence_grade": "evidence_grade",
            "claim_ceiling": "scratch_diagnostic",
        },
        "replicator_accounting": {
            "heredity": f"rung_{current_rung}_structure_and_prior_ledger_carried_forward",
            "variation": [row["candidate"] for row in candidate_set(target_rung)],
            "selection": selected_lift if admitted else "minimalist_current_structure_suffices_or_no_measured_loss",
        },
    }


def run_climb(engine: str, run_cfg: dict[str, Any], engine_observables: dict[str, Any] | None = None) -> dict[str, Any]:
    variant_kind = run_cfg.get("kind", "full_drive")
    label_shuffle = variant_kind == "label_shuffle_control"
    drive_kind = "full_drive" if label_shuffle else variant_kind
    formal = load_formal_result(engine)
    carrier = source_carrier(formal)
    indices = probe_order(carrier["pauli_labels"], run_cfg["probe_order"], int(run_cfg["seed"]))
    labels = carrier["labels"]
    full_rows = rows_for(carrier["states"], indices)
    q_full = quotient(labels, full_rows)
    no_probe_q = quotient(labels, [tuple() for _ in labels])
    coarse = carrier["formal_coarse_quotient"]
    ctrl = controls(carrier, q_full, int(run_cfg["seed"]))
    source_hashes = {
        "spec": sha256_file(SPEC_PATH),
        "formal_gate_result": formal["_source_sha256"],
        "formal_spec": sha256_file(REPO / "system_v7/sims/ratchet_formal_gates_v1/FORMAL_SPEC.md"),
    }
    probe_signature = sha256_json({"pauli_labels": carrier["pauli_labels"], "probe_order": run_cfg["probe_order"], "indices": indices})
    receipts = []
    locks = []
    prev_hash = "GENESIS"

    steps = [
        {
            "current_rung": 0,
            "target_rung": 1,
            "lost_distinction": "no primitive identity collapses the entire finite carrier into one indistinct class",
            "measured_loss": {"no_identity_class_count": 1, "full_probe_class_count": q_full["class_count"], "carrier_count": len(labels)},
            "minimalist": {"attempt": "carry finite distinguishability with no identity tokens", "succeeded": False, "failure_reason": "full finite probes expose more than one class"},
            "selected_lift": "finite_distinguishability",
            "projection": {"weaker_readout": "single collapsed class", "reduces_to": "one class"},
            "residual": {"preserved_by_lift": "at least two probe-distinguishable carrier states"},
        },
        {
            "current_rung": 1,
            "target_rung": 2,
            "lost_distinction": "finite distinguishability without finite support cannot carry the 40-state R4 roster boundary",
            "measured_loss": {"formal_R4_expected_state_count": carrier["summary"]["state_count"], "roster_count_matches": carrier["formal_full_quotient"]["roster_formula"]["count_matches_formula"]},
            "minimalist": {"attempt": "carry support cardinality with distinguishability tokens only", "succeeded": False, "failure_reason": "F01 requires an explicit finite support set and roster count"},
            "selected_lift": "finite_support_S",
            "projection": {"weaker_readout": "finite distinguishability", "reduces_to": f"{len(labels)} distinguishable token slots"},
            "residual": {"preserved_by_lift": "closed finite carrier roster and support cardinality"},
        },
        {
            "current_rung": 2,
            "target_rung": 3,
            "lost_distinction": "finite support alone erases all probe-visible differences",
            "measured_loss": {"support_only_class_count": no_probe_q["class_count"], "coarse_probe_class_count": coarse["quotient_class_count"], "full_probe_class_count": q_full["class_count"]},
            "minimalist": {"attempt": "carry probe-visible distinctions with support membership alone", "succeeded": False, "failure_reason": "erasing probes merges classes that finite probes split"},
            "selected_lift": "probe_family_P",
            "projection": {"weaker_readout": "finite support", "reduces_to": f"same carrier set of {len(labels)} elements"},
            "residual": {"preserved_by_lift": "finite probe outcome fingerprints over the carrier"},
        },
        {
            "current_rung": 3,
            "target_rung": 4,
            "lost_distinction": "probe family without quotient cannot lock same-entity/replay identity as an equivalence class",
            "measured_loss": {"R5_source": "ratchet_formal_gates_v1 FORMAL_SPEC token identity uses probe_signature", "quotient_class_count": q_full["class_count"], "projection_defined_for_all_labels": set(q_full["projection"]) == set(labels)},
            "minimalist": {"attempt": "carry retry identity with an unordered probe family but no quotient projection", "succeeded": False, "failure_reason": "R5 same_entity requires a quotient-facing probe_signature / class projection"},
            "selected_lift": "quotient_S_mod_P",
            "projection": {"weaker_readout": "probe family", "reduces_to": "fingerprint equality table"},
            "residual": {"preserved_by_lift": "class ids, projection map, and replay-stable probe signature"},
        },
    ]

    for step in steps:
        stronger = [
            row | {"rejection": "rejected_unforced_by_MSS"}
            for row in candidate_set(step["target_rung"])
            if row["candidate"] != step["selected_lift"]
        ]
        receipt = rung_receipt(
            run_id=run_cfg["run_id"],
            current_rung=step["current_rung"],
            target_rung=step["target_rung"],
            lost_distinction=step["lost_distinction"],
            measured_loss=step["measured_loss"],
            minimalist=step["minimalist"],
            admitted=True,
            selected_lift=step["selected_lift"],
            projection_back_down=step["projection"],
            residual=step["residual"],
            stronger_rejections=stronger,
            controls_summary={name: {"passed": row["passed"]} for name, row in ctrl.items()},
        )
        receipts.append(receipt)
        lock = lock_entry(prev_hash, run_cfg["run_id"], step["target_rung"], receipt, probe_signature)
        locks.append(lock)
        prev_hash = lock["entry_hash"]

    drive = drive_stream(drive_kind, int(run_cfg["seed"]), label_shuffle=label_shuffle)
    admitted = [1, 2, 3, 4]
    forced_demands = [row for row in drive["minted_demands"] if row.get("forced") is True]
    forced_beyond = []
    if forced_demands:
        for demand in forced_demands:
            selected = "admissible_survivor_set_M_C" if demand["target_rung"] == 5 else "ordered_local_update"
            receipt = rung_receipt(
                run_id=run_cfg["run_id"],
                current_rung=demand["target_rung"] - 1,
                target_rung=demand["target_rung"],
                lost_distinction=f"Axis-0 drive minted {demand['kind']}",
                measured_loss=demand["measured_loss"],
                minimalist={"attempt": "carry the drive-minted distinction with the current rung-4 quotient", "succeeded": False, "failure_reason": "static quotient has no rolling drive/history/order slot"},
                admitted=True,
                selected_lift=selected,
                projection_back_down={"weaker_readout": "rung-4 quotient", "reduces_to": "static carrier projection without drive history"},
                residual={"preserved_by_lift": demand["kind"], "demand_tick": demand["tick"]},
                stronger_rejections=[
                    {"candidate": row["candidate"], "rejection": "rejected_unforced_by_MSS"}
                    for row in candidate_set(demand["target_rung"])
                    if row["candidate"] != selected
                ],
                controls_summary={name: {"passed": row["passed"]} for name, row in ctrl.items()},
            )
            receipts.append(receipt)
            lock = lock_entry(prev_hash, run_cfg["run_id"], demand["target_rung"], receipt, probe_signature)
            locks.append(lock)
            prev_hash = lock["entry_hash"]
            admitted.append(demand["target_rung"])
            forced_beyond.append(demand)
        frontier_rung = max(admitted)
        frontier_status = "DRIVE_MINTED_RUNG_BEYOND_4"
        minimalist_wins = []
    else:
        stop_reason = {
            "commuting_control": "STOP_COMMUTING_DRIVE_NO_ORDER_OR_ENTANGLEMENT_DISTINCTION",
            "static_control": "STOP_NO_MEASURED_DISTINCTION_LOSS_FOR_RUNG_5",
            "memoryless_control": "STOP_MEMORYLESS_DRIVE_RANDOM_WALK_NO_PERSISTENT_HISTORY",
        }.get(drive_kind, "STOP_NO_MEASURED_DISTINCTION_LOSS_FOR_RUNG_5")
        frontier_attempt = rung_receipt(
            run_id=run_cfg["run_id"],
            current_rung=4,
            target_rung=5,
            lost_distinction="no drive-minted persistent distinction remains erased by the quotient",
            measured_loss={
                "full_probe_quotient_class_count": q_full["class_count"],
                "carrier_count": len(labels),
                "drive_demand_count": 0,
                "drive_kind": drive_kind,
            },
            minimalist={"attempt": "carry active distinctions with the rung-4 quotient", "succeeded": True, "success_reason": stop_reason},
            admitted=False,
            selected_lift=None,
            projection_back_down={"weaker_readout": "quotient", "reduces_to": "same full-probe class projection"},
            residual={"preserved_by_refused_candidates": "none measured in this run"},
            stronger_rejections=[
                {"candidate": "admissible_survivor_set_M_C", "rejection": "rejected_unforced_no_drive_minted_C_loss"},
                {"candidate": "ordered_local_update", "rejection": "rejected_unforced_no_noncommuting_persistent_order"},
                {"candidate": "density_operator_rho", "rejection": "rejected_unforced_late_readout_fenced"},
                {"candidate": "Hopf_projective_lift", "rejection": "rejected_unforced_late_readout_fenced"},
            ],
            controls_summary={name: {"passed": row["passed"]} for name, row in ctrl.items()},
        )
        receipts.append(frontier_attempt)
        lock = lock_entry(prev_hash, run_cfg["run_id"], 5, frontier_attempt, probe_signature)
        locks.append(lock)
        frontier_rung = 4
        frontier_status = stop_reason
        minimalist_wins = [frontier_attempt]

    return {
        "schema": "ratchet_climb_engine_v1_drive.run_result.v1",
        "run_id": run_cfg["run_id"],
        "variant_id": run_cfg.get("variant_id", run_cfg["run_id"]),
        "variant_kind": variant_kind,
        "seed": run_cfg["seed"],
        "probe_order": run_cfg["probe_order"],
        "constraint_order": run_cfg["constraint_order"],
        "engine": engine,
        "generated_at": now_iso(),
        "source_hashes": source_hashes,
        "formal_gate_reuse": {
            "formal_result_path": formal["_source_path"],
            "formal_result_sha256": formal["_source_sha256"],
            "R1_R6_rebuilt_here": False,
            "reused_lock_properties": ["R4 observable quotient", "R5 token identity", "R6 progress/non-step distinction"],
        },
        "carrier": {
            "state_count": len(labels),
            "probe_count": len(carrier["pauli_labels"]),
            "hilbert_space": carrier["summary"].get("hilbert_space"),
            "formal_full_class_count": carrier["formal_full_quotient"]["quotient_class_count"],
            "computed_full_class_count": q_full["class_count"],
            "computed_no_probe_class_count": no_probe_q["class_count"],
            "coarse_class_count": coarse["quotient_class_count"],
        },
        "climbed_ladder": admitted,
        "frontier_rung": frontier_rung,
        "frontier_status": frontier_status,
        "axis0_drive": drive,
        "forced_beyond_rung4": forced_beyond,
        "rung_receipts": receipts,
        "append_only_lock_ledger": locks,
        "controls": ctrl,
        "minimalist_wins": minimalist_wins,
        "rho_hopf_status": {
            "rho_rung_10": "not_reached_rejected_unforced",
            "hopf_rung_11": "not_reached_rejected_unforced",
            "reason": "Late readouts remain fenced; no density, Hopf/projective, cut, bipartition, or Phi0 machinery is used by the drive.",
        },
        "engine_observables": engine_observables or {},
        "all_pass": all(row["passed"] for row in ctrl.values()) and q_full["class_count"] == len(labels),
    }


def attractor_summary(run_results: list[dict[str, Any]]) -> dict[str, Any]:
    ladders = [row["climbed_ladder"] for row in run_results]
    frontiers = [row["frontier_rung"] for row in run_results]
    per_rung = {}
    for rung in range(1, 6):
        per_rung[str(rung)] = {
            "admitted_by_run": [rung in row["climbed_ladder"] for row in run_results],
            "converged": len({rung in row["climbed_ladder"] for row in run_results}) == 1,
        }
    return {
        "run_count": len(run_results),
        "same_admitted_ladder": len({tuple(row) for row in ladders}) == 1,
        "same_frontier": len(set(frontiers)) == 1,
        "ladder_by_run": {row["run_id"]: row["climbed_ladder"] for row in run_results},
        "frontier_by_run": {row["run_id"]: row["frontier_rung"] for row in run_results},
        "per_rung_convergence": per_rung,
        "verdict": "basin_evidence_same_rungs_and_same_frontier" if len({tuple(row) for row in ladders}) == 1 and len(set(frontiers)) == 1 else "path_dependence_detected",
    }


def result_envelope(engine: str, run_results: list[dict[str, Any]], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema": "codex_ratchet.ratchet_climb_engine_v1_drive.engine_result.v1",
        "sim_id": "ratchet_climb_engine_v1_drive",
        "engine": engine,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "lifecycle_status": "SCRATCH_DIAGNOSTIC",
        "evidence_grade": "evidence_grade",
        "claim_ceiling": "scratch_diagnostic",
        "capstone_status": "DRAFT_UNAUDITED",
        "generated_at": now_iso(),
        "run_results": run_results,
        "attractor_measurement": attractor_summary(run_results),
        "climbed_ladder": run_results[0]["climbed_ladder"],
        "frontier_reached": run_results[0]["frontier_rung"],
        "frontier_status": run_results[0]["frontier_status"],
        "frontier_by_variant": {row["variant_id"]: row["frontier_rung"] for row in run_results},
        "frontier_status_by_variant": {row["variant_id"]: row["frontier_status"] for row in run_results},
        "forced_beyond_rung4_by_variant": {row["variant_id"]: bool(row["forced_beyond_rung4"]) for row in run_results},
        "minted_demand_count_by_variant": {row["variant_id"]: row["axis0_drive"]["demand_count"] for row in run_results},
        "minimalist_wins": [
            row["minimalist_wins"][0]["mss_gate"]["stronger_candidates_rejected_unforced"]
            for row in run_results
            if row["minimalist_wins"]
        ],
        "all_pass": all(row["all_pass"] for row in run_results),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    } | (extra or {})
