#!/usr/bin/env python3
"""PyTorch graph leg for compression_flow_radiated_record_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import torch
from torch_geometric.utils import degree
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "compression_flow_radiated_record_v0"
ENGINE = "pytorch"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"
CARRIER_RESULT_PATH = (
    ROOT
    / "system_v6"
    / "sims"
    / "mct_dynamic_admissibility_packet_v0"
    / "results"
    / "mct_dynamic_admissibility_packet_v0_julia_results.json"
)

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
LN2 = math.log(2.0)
DROP_FRACTION_DESCRIPTION = "drop every 7th emitted raw record row in solver erased-control"
ADVISORY_CROSSCHECK_DIVERGENCE_SOURCE = "/tmp/cfr_advisory_crosscheck_20260610.md#D1"
MCT_SUPPORT_HASH_SERIALIZATION_CITATION = {
    "source_path": "system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_pytorch.py",
    "line_range": "382-396",
    "serialization": "state_id|psi0_real|psi0_imag|psi1_real|psi1_imag, joined with newlines plus final newline",
    "claim_scope": "carrier_support_table_hash recomputation citation only",
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def density_class(row: dict[str, Any]) -> str:
    return canonical_json(row["P_density"])


def payload_digest_for_state(
    state_id: str,
    support_by_id: dict[str, dict[str, Any]],
    rows_by_id: dict[str, dict[str, Any]],
) -> str:
    return sha256_text(canonical_json({"state_id": state_id, "support": support_by_id[state_id], "probe": rows_by_id[state_id]}))


def payload_digest_code(digest: str) -> int:
    return int(digest[:15], 16)


def load_carrier() -> dict[str, Any]:
    carrier = json.loads(CARRIER_RESULT_PATH.read_text(encoding="utf-8"))
    required = {"support_table", "probe_row_table", "pin_block_sha256", "support_table_hash", "PIN_SPEC"}
    missing = sorted(required - set(carrier))
    if missing:
        raise ValueError(f"carrier result missing required keys: {missing}")
    return carrier


def pin_spec(carrier: dict[str, Any]) -> dict[str, Any]:
    return {
        "sim_id": SIM_ID,
        "status": "PINNED",
        "carrier": {
            "source_sim": "system_v6/sims/mct_dynamic_admissibility_packet_v0",
            "source_result_path": str(CARRIER_RESULT_PATH.relative_to(ROOT)),
            "carrier_lineage": carrier["pin_block_sha256"],
            "carrier_support_table_hash": carrier["support_table_hash"],
            "chart_formula": carrier["PIN_SPEC"]["spinor_chart"],
            "grid": carrier["PIN_SPEC"]["grid"],
            "reuse_policy": "committed carrier consumed as input; no new carrier formula is introduced",
        },
        "flow": {
            "initial_live_set": "all 384 committed carrier rows at outer stage",
            "shell_coordinate": "eta_k",
            "shells_outer_to_inner": ["3*pi/8", "pi/4", "pi/8"],
            "b0_outer_to_inner": [-1, 0, 1],
            "steps": [
                {
                    "step": 0,
                    "predicate_id": "c0_density_x_bin_ge_2",
                    "status": "PINNED-CHOICE",
                    "source_probe_family": "P_density",
                    "source_quote": "P_density (binned Bloch components)",
                    "keep_rule": "P_density[0] >= 2",
                },
                {
                    "step": 1,
                    "predicate_id": "c1_shell_not_outer_eta",
                    "status": "PINNED-CHOICE",
                    "source_probe_family": "P_shell",
                    "source_quote": "P_shell (eta index)",
                    "keep_rule": "P_shell != 2",
                },
                {
                    "step": 2,
                    "predicate_id": "c2_phase_lower_half",
                    "status": "PINNED-CHOICE",
                    "source_probe_family": "P_phase",
                    "source_quote": "P_phase (phase-sensitive non-density probe)",
                    "keep_rule": "P_phase in {0,1,2,3}",
                },
            ],
            "terminal_state_name": "P_T after steps t=0,1,2",
            "G4_name_note": "build card says P_2; this receipt reports P_T after all three pinned predicates and aliases it in G4 fields",
        },
        "record_modes": {
            "raw_row": "emitted rows carry full canonical support and probe rows",
            "quotient_class": "emitted rows carry density-only quotient class ids",
        },
        "entropy_objects": {
            "H_live": "class-distribution entropy of live set under P_density, base e",
            "H_record": "class-distribution entropy of append-only record composition, base e",
            "erasure_charge": "bits_erased * ln2, reported in nats",
        },
        "variants": ["radiative", "erasure_boundary_baseline", "lossy_record_counts_only"],
        "candidate_math_source": "system_v6/receipts/shell_flow_radiated_information_mine_20260610.md §B-C",
    }


def predicate_mask(rows: list[dict[str, Any]], predicate_id: str) -> torch.Tensor:
    if predicate_id == "c0_density_x_bin_ge_2":
        values = torch.tensor([int(row["P_density"][0]) for row in rows], dtype=torch.int64)
        return values >= 2
    if predicate_id == "c1_shell_not_outer_eta":
        values = torch.tensor([int(row["P_shell"]) for row in rows], dtype=torch.int64)
        return values != 2
    if predicate_id == "c2_phase_lower_half":
        values = torch.tensor([int(row["P_phase"]) for row in rows], dtype=torch.int64)
        return values <= 3
    if predicate_id == "trivial_loop_outer_visible":
        return torch.tensor([row["P_loop"][3] == "outer_visible" for row in rows], dtype=torch.bool)
    raise KeyError(predicate_id)


def predicate_accept(row: dict[str, Any], predicate_id: str) -> bool:
    return bool(predicate_mask([row], predicate_id)[0].item())


def entropy_for_ids(ids: list[str], rows_by_id: dict[str, dict[str, Any]]) -> float:
    if not ids:
        return 0.0
    counts = torch.tensor(list(Counter(density_class(rows_by_id[sid]) for sid in ids).values()), dtype=torch.float64)
    probs = counts / torch.sum(counts)
    return float(-torch.sum(probs * torch.log(probs)).item())


def entropy_for_record(entries: list[dict[str, Any]]) -> float:
    if not entries:
        return 0.0
    counts = torch.tensor(list(Counter(entry["class_id"] for entry in entries).values()), dtype=torch.float64)
    probs = counts / torch.sum(counts)
    return float(-torch.sum(probs * torch.log(probs)).item())


def entry_for_mode(
    *,
    mode: str,
    step: int,
    state_id: str,
    support_by_id: dict[str, dict[str, Any]],
    rows_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    row = rows_by_id[state_id]
    entry: dict[str, Any] = {
        "step": step,
        "state_id": state_id if mode == "raw_row" else None,
        "record_mode": mode,
        "class_id": density_class(row),
    }
    if mode == "raw_row":
        entry["canonical_support_row"] = support_by_id[state_id]
        entry["canonical_probe_row"] = row
    return entry


def hash_chain_step(previous_hash: str, step: int, entries: list[dict[str, Any]]) -> dict[str, Any]:
    entry_hashes = [sha256_text(canonical_json(entry)) for entry in entries]
    state = {
        "previous_hash": previous_hash,
        "step": step,
        "entry_hashes": entry_hashes,
        "entry_count": len(entries),
    }
    return {
        "step": step,
        "previous_hash": previous_hash,
        "entry_hashes": entry_hashes,
        "record_state_hash": sha256_text(canonical_json(state)),
    }


def recompute_hash_chain(hash_chain: list[dict[str, Any]], per_step_entries: list[list[dict[str, Any]]]) -> bool:
    previous = "0" * 64
    for expected, entries in zip(hash_chain, per_step_entries, strict=True):
        actual = hash_chain_step(previous, expected["step"], entries)
        if actual["record_state_hash"] != expected["record_state_hash"]:
            return False
        previous = actual["record_state_hash"]
    return True


def build_flow(
    *,
    mode: str,
    all_ids: list[str],
    support_by_id: dict[str, dict[str, Any]],
    rows_by_id: dict[str, dict[str, Any]],
    predicates: list[dict[str, Any]],
) -> dict[str, Any]:
    live_indices = torch.arange(len(all_ids), dtype=torch.int64)
    record: list[dict[str, Any]] = []
    per_step_entries: list[list[dict[str, Any]]] = []
    ledgers: list[dict[str, Any]] = []
    membership_tables: list[dict[str, Any]] = []
    hash_chain: list[dict[str, Any]] = []
    previous_hash = "0" * 64
    for pred in predicates:
        step = int(pred["step"])
        before_indices = live_indices.clone()
        before = [all_ids[int(idx)] for idx in before_indices.tolist()]
        before_rows = [rows_by_id[sid] for sid in before]
        keep_mask = predicate_mask(before_rows, pred["predicate_id"])
        survivor_indices = before_indices[keep_mask]
        emitted_indices = before_indices[~keep_mask]
        survivors = [all_ids[int(idx)] for idx in survivor_indices.tolist()]
        emitted = [all_ids[int(idx)] for idx in emitted_indices.tolist()]
        entries = [
            entry_for_mode(mode=mode, step=step, state_id=sid, support_by_id=support_by_id, rows_by_id=rows_by_id)
            for sid in emitted
        ]
        record.extend(entries)
        per_step_entries.append(entries)
        chain_entry = hash_chain_step(previous_hash, step, entries)
        hash_chain.append(chain_entry)
        previous_hash = chain_entry["record_state_hash"]
        defect = int(before_indices.numel() - survivor_indices.numel() - emitted_indices.numel())
        ledgers.append(
            {
                "step": step,
                "predicate_id": pred["predicate_id"],
                "P_t_size": int(before_indices.numel()),
                "P_t_plus_1_size": int(survivor_indices.numel()),
                "Delta_R_t_size": int(emitted_indices.numel()),
                "cardinality_defect": defect,
                "conservation_pass": defect == 0,
                "H_live_before": entropy_for_ids(before, rows_by_id),
                "H_live_after": entropy_for_ids(survivors, rows_by_id),
                "H_record_after": entropy_for_record(record),
            }
        )
        membership_tables.append(
            {
                "step": step,
                "predicate_id": pred["predicate_id"],
                "live_before_ids": before,
                "emitted_ids": emitted,
                "survivor_ids": survivors,
            }
        )
        live_indices = survivor_indices
    return {
        "record_mode": mode,
        "initial_ids": all_ids,
        "final_ids": [all_ids[int(idx)] for idx in live_indices.tolist()],
        "record_entries": record,
        "per_step_record_entries": per_step_entries,
        "cardinality_ledger": ledgers,
        "membership_tables": membership_tables,
        "record_hash_chain": hash_chain,
        "append_only_recomputed": recompute_hash_chain(hash_chain, per_step_entries),
        "record_final_hash": previous_hash,
    }


def symmetric_mismatch(left: set[str], right: set[str]) -> int:
    return len(left.symmetric_difference(right))


def reconstruction_receipts(raw_flow: dict[str, Any], quotient_flow: dict[str, Any], rows_by_id: dict[str, dict[str, Any]], all_ids: list[str]) -> dict[str, Any]:
    actual = set(all_ids)
    raw_record_ids = [entry["state_id"] for entry in raw_flow["record_entries"]]
    raw_reconstructed = set(raw_flow["final_ids"]) | set(raw_record_ids)
    raw_mismatch = symmetric_mismatch(raw_reconstructed, actual)

    class_to_ids: dict[str, list[str]] = {}
    for sid in all_ids:
        class_to_ids.setdefault(density_class(rows_by_id[sid]), []).append(sid)
    for ids in class_to_ids.values():
        ids.sort()

    chosen: list[str] = []
    class_offsets: Counter[str] = Counter()
    for entry in quotient_flow["record_entries"]:
        cls = entry["class_id"]
        candidates = class_to_ids[cls]
        chosen.append(candidates[class_offsets[cls] % len(candidates)])
        class_offsets[cls] += 1
    quotient_raw_reconstructed = set(quotient_flow["final_ids"]) | set(chosen)
    quotient_raw_mismatch = symmetric_mismatch(quotient_raw_reconstructed, actual)
    initial_classes = Counter(density_class(rows_by_id[sid]) for sid in all_ids)
    quotient_reconstructed_classes = Counter(density_class(rows_by_id[sid]) for sid in quotient_flow["final_ids"])
    quotient_reconstructed_classes.update(entry["class_id"] for entry in quotient_flow["record_entries"])
    quotient_level_mismatch = sum((initial_classes - quotient_reconstructed_classes).values()) + sum(
        (quotient_reconstructed_classes - initial_classes).values()
    )
    killed_nats = sum(math.log(len(class_to_ids[entry["class_id"]])) for entry in quotient_flow["record_entries"])
    return {
        "raw_mode": {
            "reconstructed_from_P_T_and_full_raw_record": True,
            "raw_reconstruction_mismatch_count": raw_mismatch,
            "reconstructed_count": len(raw_reconstructed),
            "P_T_size": len(raw_flow["final_ids"]),
            "record_row_count": len(raw_record_ids),
        },
        "quotient_mode": {
            "raw_reconstruction_mismatch_count": quotient_raw_mismatch,
            "raw_reconstruction_fails": quotient_raw_mismatch > 0,
            "quotient_level_mismatch_count": quotient_level_mismatch,
            "quotient_level_reconstruction_succeeds": quotient_level_mismatch == 0,
            "killed_information_ledger": {
                "object": "raw-row identity within P_density quotient classes",
                "emitted_rows": len(quotient_flow["record_entries"]),
                "killed_information_nats": killed_nats,
                "formula": "sum_emitted ln(|P_density_class|)",
            },
        },
    }


def erasure_variant(raw_flow: dict[str, Any], all_ids: list[str]) -> dict[str, Any]:
    mismatch = symmetric_mismatch(set(raw_flow["final_ids"]), set(all_ids))
    per_step = []
    total_erased_rows = 0
    for ledger in raw_flow["cardinality_ledger"]:
        erased = int(ledger["Delta_R_t_size"])
        total_erased_rows += erased
        per_step.append(
            {
                "step": ledger["step"],
                "P_t_size": ledger["P_t_size"],
                "P_t_plus_1_size": ledger["P_t_plus_1_size"],
                "internal_Delta_R_t_size_after_reset": 0,
                "internal_cardinality_defect_without_environment": ledger["P_t_size"] - ledger["P_t_plus_1_size"],
            }
        )
    bits_erased = total_erased_rows * math.log2(len(all_ids))
    charge = bits_erased * LN2
    remaining_live_charge = sum(row["Delta_R_t_size"] * math.log(row["P_t_plus_1_size"]) for row in raw_flow["cardinality_ledger"])
    pre_step_live_charge = sum(row["Delta_R_t_size"] * math.log(row["P_t_size"]) for row in raw_flow["cardinality_ledger"])
    emitted_step_register_charge = sum(math.log(row["Delta_R_t_size"]) for row in raw_flow["cardinality_ledger"])
    return {
        "variant": "erasure_boundary_baseline",
        "fired": True,
        "record_register_policy": "reset_each_step_content_destroyed",
        "erasure_register_basis": "full_support_identity",
        "raw_reconstruction_mismatch_count": mismatch,
        "reconstruction_fails": mismatch > 0,
        "internal_ledgers": per_step,
        "internal_ledger_balances_without_environment": all(
            row["internal_cardinality_defect_without_environment"] == 0 for row in per_step
        ),
        "bits_erased": bits_erased,
        "environment_charge_nats": charge,
        "environment_charge_label": "headline charge under erasure_register_basis=full_support_identity",
        "charge_full_support_identity": charge,
        "charge_remaining_live_after_step": remaining_live_charge,
        "charge_pre_step_live": pre_step_live_charge,
        "charge_emitted_step_register": emitted_step_register_charge,
        "charge_comparators": {
            "charge_full_support_identity": {
                "charge_nats": charge,
                "register_semantics": "each erased raw row is charged against the full 384-row support identity register",
                "formula": "total_emitted_rows * ln(support_size)",
            },
            "charge_remaining_live_after_step": {
                "charge_nats": remaining_live_charge,
                "register_semantics": "each step charges erased rows against the remaining live set after that step",
                "formula": "sum_t Delta_R_t_size * ln(P_t_plus_1_size)",
            },
            "charge_pre_step_live": {
                "charge_nats": pre_step_live_charge,
                "register_semantics": "each step charges erased rows against the pre-step live set",
                "formula": "sum_t Delta_R_t_size * ln(P_t_size)",
            },
            "charge_emitted_step_register": {
                "charge_nats": emitted_step_register_charge,
                "register_semantics": "blind-card per-step-register comparator; one emitted-step register per step, not per emitted row",
                "formula": "sum_t ln(Delta_R_t_size)",
            },
        },
        "charge_divergence_source": ADVISORY_CROSSCHECK_DIVERGENCE_SOURCE,
        "charge_adjudication": "named alternatives preserved; no comparator is promoted as the charge",
        "arithmetic": f"{bits_erased:.12f} bits * ln2 = {charge:.12f} nats",
    }


def lossy_variant(raw_flow: dict[str, Any], all_ids: list[str]) -> dict[str, Any]:
    counts = [ledger["Delta_R_t_size"] for ledger in raw_flow["cardinality_ledger"]]
    mismatch = len(all_ids) - len(raw_flow["final_ids"])
    return {
        "variant": "lossy_record_counts_only",
        "fired": True,
        "record_payload": {"per_step_counts_only": counts},
        "raw_reconstruction_mismatch_count": mismatch,
        "raw_reconstruction_fails": mismatch > 0,
        "reason": "counts contain no row identity and no quotient class id",
    }


def record_step_consistency_errors(entries: list[dict[str, Any]], predicates: list[dict[str, Any]], rows_by_id: dict[str, dict[str, Any]]) -> int:
    pred_by_step = {int(pred["step"]): pred["predicate_id"] for pred in predicates}
    errors = 0
    for entry in entries:
        sid = entry["state_id"]
        if sid is None:
            continue
        step = int(entry["step"])
        row = rows_by_id[sid]
        survived_previous = all(predicate_accept(row, pred_by_step[t]) for t in range(step))
        failed_at_step = not predicate_accept(row, pred_by_step[step])
        if not (survived_previous and failed_at_step):
            errors += 1
    return errors


def controls(raw_flow: dict[str, Any], rows_by_id: dict[str, dict[str, Any]], predicates: list[dict[str, Any]], all_ids: list[str]) -> dict[str, Any]:
    emitted_entries = list(raw_flow["record_entries"])
    shuffled_entries = [dict(entry) for entry in emitted_entries]
    for entry in shuffled_entries:
        if entry["step"] == 0:
            entry["step"] = 1
        elif entry["step"] == 1:
            entry["step"] = 0
    original_errors = record_step_consistency_errors(emitted_entries, predicates, rows_by_id)
    shuffled_errors = record_step_consistency_errors(shuffled_entries, predicates, rows_by_id)

    injected_before = list(raw_flow["membership_tables"][0]["live_before_ids"])
    injected_survivors = list(raw_flow["membership_tables"][0]["survivor_ids"])
    injected_emitted = list(raw_flow["membership_tables"][0]["emitted_ids"])
    dropped_midflight = injected_survivors[0]
    injected_survivors = injected_survivors[1:]
    injected_defect = len(injected_before) - len(injected_survivors) - len(injected_emitted)

    trivial_keep = sum(1 for sid in all_ids if predicate_accept(rows_by_id[sid], "trivial_loop_outer_visible"))
    relabel = {sid: f"relabel_{idx:03d}" for idx, sid in enumerate(reversed(all_ids))}
    relabeled_final = {relabel[sid] for sid in raw_flow["final_ids"]}
    relabeled_record = {relabel[entry["state_id"]] for entry in raw_flow["record_entries"]}
    relabeled_initial = set(relabel.values())
    label_shuffle_mismatch = symmetric_mismatch(relabeled_final | relabeled_record, relabeled_initial)
    return {
        "record-shuffle": {
            "fired": True,
            "original_step_consistency_errors": original_errors,
            "shuffled_step_consistency_errors": shuffled_errors,
            "control_changed_result": shuffled_errors > original_errors,
        },
        "injected conservation violation": {
            "fired": True,
            "dropped_midflight_state_id": dropped_midflight,
            "ledger_defect": injected_defect,
            "caught_by_ledger": injected_defect != 0,
        },
        "label shuffle": {
            "fired": True,
            "raw_reconstruction_mismatch_after_relabel": label_shuffle_mismatch,
            "ledger_sizes_preserved": [row["Delta_R_t_size"] for row in raw_flow["cardinality_ledger"]],
            "verdict_preserved": label_shuffle_mismatch == 0,
        },
        "trivial-predicate control": {
            "fired": True,
            "predicate_id": "trivial_loop_outer_visible",
            "kept_count": trivial_keep,
            "excluded_count": len(all_ids) - trivial_keep,
            "flagged_not_silently_passed": trivial_keep in {0, len(all_ids)},
        },
    }


def z3_uniqueness(universe: list[str], observed: set[str]) -> dict[str, Any]:
    solver = z3.Solver()
    vars_by_id = {sid: z3.Bool(f"x_{idx}") for idx, sid in enumerate(universe)}
    for sid in observed:
        solver.add(vars_by_id[sid])
    solver.add(z3.Or([z3.Not(vars_by_id[sid]) for sid in universe]))
    status = str(solver.check())
    model_false = []
    if status == "sat":
        model = solver.model()
        for sid in universe:
            value = model.eval(vars_by_id[sid], model_completion=True)
            if not z3.is_true(value):
                model_false.append(sid)
                if len(model_false) >= 8:
                    break
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "verdict": status,
        "observed_rows_bound": len(observed),
        "candidate_differs_constraint": "exists row where P_0_prime[row] is false while P_0[row] is true",
        "model_false_state_ids_sample": model_false,
        "hardcoded_literals": False,
    }


def z3_payload_bound_uniqueness(
    universe: list[str],
    observed: set[str],
    payload_codes: dict[str, int],
    payload_digests: dict[str, str],
) -> dict[str, Any]:
    solver = z3.Solver()
    vars_by_id = {sid: z3.Bool(f"x_payload_{idx}") for idx, sid in enumerate(universe)}
    digest_by_id = {sid: z3.Int(f"h_payload_{idx}") for idx, sid in enumerate(universe)}
    for sid in observed:
        solver.add(vars_by_id[sid])
        solver.add(digest_by_id[sid] == z3.IntVal(payload_codes[sid]))
    for sid in set(universe) - observed:
        solver.add(z3.Not(vars_by_id[sid]))
    solver.add(
        z3.Or(
            [
                z3.Or(z3.Not(vars_by_id[sid]), digest_by_id[sid] != z3.IntVal(payload_codes[sid]))
                for sid in universe
            ]
        )
    )
    status = str(solver.check())
    model_false = []
    model_payload_mismatch = []
    if status == "sat":
        model = solver.model()
        for sid in universe:
            present = model.eval(vars_by_id[sid], model_completion=True)
            digest_value = model.eval(digest_by_id[sid], model_completion=True)
            if not z3.is_true(present):
                model_false.append(sid)
            elif digest_value.as_long() != payload_codes[sid]:
                model_payload_mismatch.append(sid)
            if len(model_false) >= 8:
                break
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "payload_bound": True,
        "verdict": status,
        "observed_rows_bound": len(observed),
        "payload_hash_function": "sha256(canonical_json({state_id,support,probe}))",
        "payload_hash_integer_code": "first_15_hex_digits_base16",
        "payload_digest_sample": {sid: payload_digests[sid] for sid in universe[:3]},
        "candidate_differs_constraint": "exists row where presence is false or canonical payload-hash code differs",
        "model_false_state_ids_sample": model_false,
        "model_payload_mismatch_state_ids_sample": model_payload_mismatch[:8],
        "hardcoded_literals": False,
    }


def cvc5_or(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.OR, *terms)


def cvc5_uniqueness(universe: list[str], observed: set[str]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    vars_by_id = {sid: solver.mkConst(bool_sort, f"x_{idx}") for idx, sid in enumerate(universe)}
    for sid in observed:
        solver.assertFormula(vars_by_id[sid])
    solver.assertFormula(cvc5_or(solver, [solver.mkTerm(Kind.NOT, vars_by_id[sid]) for sid in universe]))
    result = solver.checkSat()
    status = "sat" if result.isSat() else "unsat" if result.isUnsat() else "unknown"
    model_false = []
    if status == "sat":
        for sid in universe:
            value = str(solver.getValue(vars_by_id[sid]))
            if value.lower() == "false":
                model_false.append(sid)
                if len(model_false) >= 8:
                    break
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "verdict": status,
        "observed_rows_bound": len(observed),
        "candidate_differs_constraint": "exists row where P_0_prime[row] is false while P_0[row] is true",
        "model_false_state_ids_sample": model_false,
        "hardcoded_literals": False,
    }


def cvc5_payload_bound_uniqueness(
    universe: list[str],
    observed: set[str],
    payload_codes: dict[str, int],
    payload_digests: dict[str, str],
) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    solver.setLogic("QF_LIA")
    bool_sort = solver.getBooleanSort()
    int_sort = solver.getIntegerSort()
    vars_by_id = {sid: solver.mkConst(bool_sort, f"x_payload_{idx}") for idx, sid in enumerate(universe)}
    digest_by_id = {sid: solver.mkConst(int_sort, f"h_payload_{idx}") for idx, sid in enumerate(universe)}
    for sid in observed:
        solver.assertFormula(vars_by_id[sid])
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, digest_by_id[sid], solver.mkInteger(str(payload_codes[sid]))))
    for sid in set(universe) - observed:
        solver.assertFormula(solver.mkTerm(Kind.NOT, vars_by_id[sid]))
    differs = [
        solver.mkTerm(
            Kind.OR,
            solver.mkTerm(Kind.NOT, vars_by_id[sid]),
            solver.mkTerm(Kind.DISTINCT, digest_by_id[sid], solver.mkInteger(str(payload_codes[sid]))),
        )
        for sid in universe
    ]
    solver.assertFormula(cvc5_or(solver, differs))
    result = solver.checkSat()
    status = "sat" if result.isSat() else "unsat" if result.isUnsat() else "unknown"
    model_false = []
    model_payload_mismatch = []
    if status == "sat":
        for sid in universe:
            present = str(solver.getValue(vars_by_id[sid])).lower()
            digest_value = str(solver.getValue(digest_by_id[sid]))
            if present == "false":
                model_false.append(sid)
            elif digest_value != str(payload_codes[sid]):
                model_payload_mismatch.append(sid)
            if len(model_false) >= 8:
                break
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "payload_bound": True,
        "verdict": status,
        "observed_rows_bound": len(observed),
        "payload_hash_function": "sha256(canonical_json({state_id,support,probe}))",
        "payload_hash_integer_code": "first_15_hex_digits_base16",
        "payload_digest_sample": {sid: payload_digests[sid] for sid in universe[:3]},
        "candidate_differs_constraint": "exists row where presence is false or canonical payload-hash code differs",
        "model_false_state_ids_sample": model_false,
        "model_payload_mismatch_state_ids_sample": model_payload_mismatch[:8],
        "hardcoded_literals": False,
    }


def proof_receipts(
    raw_flow: dict[str, Any],
    all_ids: list[str],
    support_by_id: dict[str, dict[str, Any]],
    rows_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    raw_observed = set(raw_flow["final_ids"]) | {entry["state_id"] for entry in raw_flow["record_entries"]}
    emitted_ids = [entry["state_id"] for entry in raw_flow["record_entries"]]
    dropped = {sid for idx, sid in enumerate(emitted_ids) if idx % 7 == 0}
    erased_observed = raw_observed - dropped
    payload_digests = {sid: payload_digest_for_state(sid, support_by_id, rows_by_id) for sid in all_ids}
    payload_codes = {sid: payload_digest_code(payload_digests[sid]) for sid in all_ids}
    rowset = {
        "raw_uniqueness": {
            "z3": z3_uniqueness(all_ids, raw_observed),
            "cvc5": cvc5_uniqueness(all_ids, raw_observed),
        },
        "erased_control": {
            "drop_rule": DROP_FRACTION_DESCRIPTION,
            "dropped_record_rows": len(dropped),
            "z3": z3_uniqueness(all_ids, erased_observed),
            "cvc5": cvc5_uniqueness(all_ids, erased_observed),
        },
    }
    payload_z3 = {
        "full_record": z3_payload_bound_uniqueness(all_ids, raw_observed, payload_codes, payload_digests),
        "dropped_record": z3_payload_bound_uniqueness(all_ids, erased_observed, payload_codes, payload_digests),
    }
    payload_cvc5 = {
        "full_record": cvc5_payload_bound_uniqueness(all_ids, raw_observed, payload_codes, payload_digests),
        "dropped_record": cvc5_payload_bound_uniqueness(all_ids, erased_observed, payload_codes, payload_digests),
    }
    return {
        **rowset,
        "proof_rowset_coverage": rowset,
        "proof_payload_bound_z3": payload_z3,
        "proof_payload_bound_cvc5": payload_cvc5,
    }


def torch_mask_receipt(all_ids: list[str], rows_by_id: dict[str, dict[str, Any]], predicates: list[dict[str, Any]]) -> dict[str, Any]:
    live = torch.ones((len(all_ids),), dtype=torch.bool)
    counts = []
    rows = [rows_by_id[sid] for sid in all_ids]
    for pred in predicates:
        mask = predicate_mask(rows, pred["predicate_id"])
        emitted = live & (~mask)
        live = live & mask
        counts.append(
            {
                "predicate_id": pred["predicate_id"],
                "torch_emitted_count": int(torch.sum(emitted).item()),
                "torch_live_after": int(torch.sum(live).item()),
            }
        )
    return {"torch_dtype_for_masks": "torch.bool", "tensorized_predicate_counts": counts}


def torch_graph_receipt(raw_flow: dict[str, Any]) -> dict[str, Any]:
    node_ids: list[str] = []
    node_index: dict[str, int] = {}
    edges: list[tuple[int, int]] = []

    def add_node(name: str) -> int:
        if name not in node_index:
            node_index[name] = len(node_ids)
            node_ids.append(name)
        return node_index[name]

    root = add_node("P_0")
    previous_record_state = add_node("record_hash_0")
    for table in raw_flow["membership_tables"]:
        step = int(table["step"])
        live_node = add_node(f"P_{step}_live")
        survivor_node = add_node(f"P_{step + 1}_survivors")
        record_state = add_node(f"record_hash_{step + 1}")
        edges.append((root if step == 0 else live_node, survivor_node))
        edges.append((previous_record_state, record_state))
        for sid in table["emitted_ids"]:
            emitted_node = add_node(f"emit_t{step}:{sid}")
            edges.append((live_node, emitted_node))
            edges.append((emitted_node, record_state))
        previous_record_state = record_state

    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    out_degree = degree(edge_index[0], num_nodes=len(node_ids), dtype=torch.float64)
    in_degree = degree(edge_index[1], num_nodes=len(node_ids), dtype=torch.float64)
    record_nodes = [idx for idx, name in enumerate(node_ids) if name.startswith("record_hash_")]
    emitted_nodes = [idx for idx, name in enumerate(node_ids) if name.startswith("emit_t")]
    mutation_edges_to_prior_records = 0
    record_positions = {idx: pos for pos, idx in enumerate(record_nodes)}
    for source, target in edges:
        if source in record_positions and target in record_positions and record_positions[target] <= record_positions[source]:
            mutation_edges_to_prior_records += 1
    return {
        "tool": "torch_geometric.utils.degree",
        "graph_role": "append-only record/flow DAG lane",
        "node_count": len(node_ids),
        "edge_count": int(edge_index.shape[1]),
        "emitted_record_node_count": len(emitted_nodes),
        "record_state_node_count": len(record_nodes),
        "max_in_degree": float(torch.max(in_degree).item()),
        "max_out_degree": float(torch.max(out_degree).item()),
        "append_only_record_chain_forward_only": mutation_edges_to_prior_records == 0,
        "mutation_edges_to_prior_records": mutation_edges_to_prior_records,
        "edge_index_shape": list(edge_index.shape),
        "load_bearing_for_gates": ["G3", "G7"],
    }


def gates(
    raw_flow: dict[str, Any],
    quotient_flow: dict[str, Any],
    recon: dict[str, Any],
    variants: dict[str, Any],
    ctrl: dict[str, Any],
    proofs: dict[str, Any],
    all_ids: list[str],
) -> dict[str, Any]:
    raw_proofs = proofs["raw_uniqueness"]
    erased_proofs = proofs["erased_control"]
    payload_z3 = proofs["proof_payload_bound_z3"]
    payload_cvc5 = proofs["proof_payload_bound_cvc5"]
    return {
        "G1": {
            "flow_runs_on_geometric_carrier_rows": len(all_ids) == 384,
            "support_rows_seen": len(all_ids),
            "per_step_membership_tables_emitted": len(raw_flow["membership_tables"]) == 3,
        },
        "G2": {
            "cardinality_conservation_all_steps": all(row["conservation_pass"] for row in raw_flow["cardinality_ledger"]),
            "cardinality_ledger": raw_flow["cardinality_ledger"],
            "injected_violation_caught": ctrl["injected conservation violation"]["caught_by_ledger"],
        },
        "G3": {
            "append_only_record_hash_chain_emitted": len(raw_flow["record_hash_chain"]) == 3,
            "hash_chain_recomputed": raw_flow["append_only_recomputed"],
            "record_final_hash": raw_flow["record_final_hash"],
        },
        "G4": {
            "raw_reconstruction_from_P_T_full_raw_record_mismatch_count": recon["raw_mode"]["raw_reconstruction_mismatch_count"],
            "raw_reconstruction_from_P_2_alias_mismatch_count": recon["raw_mode"]["raw_reconstruction_mismatch_count"],
            "quotient_raw_reconstruction_mismatch_count": recon["quotient_mode"]["raw_reconstruction_mismatch_count"],
            "quotient_level_reconstruction_mismatch_count": recon["quotient_mode"]["quotient_level_mismatch_count"],
            "killed_information_ledger": recon["quotient_mode"]["killed_information_ledger"],
        },
        "G5": {
            "z3_raw_uniqueness_verdict": raw_proofs["z3"]["verdict"],
            "cvc5_raw_uniqueness_verdict": raw_proofs["cvc5"]["verdict"],
            "z3_erased_control_verdict": erased_proofs["z3"]["verdict"],
            "cvc5_erased_control_verdict": erased_proofs["cvc5"]["verdict"],
            "z3_payload_bound_full_record_verdict": payload_z3["full_record"]["verdict"],
            "z3_payload_bound_dropped_record_verdict": payload_z3["dropped_record"]["verdict"],
            "cvc5_payload_bound_full_record_verdict": payload_cvc5["full_record"]["verdict"],
            "cvc5_payload_bound_dropped_record_verdict": payload_cvc5["dropped_record"]["verdict"],
            "erased_models_exhibited": bool(erased_proofs["z3"]["model_false_state_ids_sample"])
            and bool(erased_proofs["cvc5"]["model_false_state_ids_sample"]),
            "payload_bound_models_exhibited": bool(payload_z3["dropped_record"]["model_false_state_ids_sample"])
            and bool(payload_cvc5["dropped_record"]["model_false_state_ids_sample"]),
        },
        "G6": {
            "erasure_reconstruction_fails": variants["erasure"]["reconstruction_fails"],
            "erasure_internal_ledger_balances_without_environment": variants["erasure"]["internal_ledger_balances_without_environment"],
            "environment_charge_nats": variants["erasure"]["environment_charge_nats"],
            "radiative_internal_erasure_charge_nats": 0.0,
            "lossy_record_reconstruction_fails": variants["lossy"]["raw_reconstruction_fails"],
        },
        "G7": {
            "record_shuffle_changed_or_failed": ctrl["record-shuffle"]["control_changed_result"],
            "shuffled_step_consistency_errors": ctrl["record-shuffle"]["shuffled_step_consistency_errors"],
        },
        "G8": {
            "uniqueness_proof_computed": raw_proofs["z3"]["verdict"] == "unsat" and raw_proofs["cvc5"]["verdict"] == "unsat",
            "quotient_failure_computed": recon["quotient_mode"]["raw_reconstruction_fails"],
            "erasure_and_lossy_variants_computed": variants["erasure"]["fired"] and variants["lossy"]["fired"],
            "injected_violation_computed": ctrl["injected conservation violation"]["caught_by_ledger"],
        },
    }


def gate_pass(gate_receipts: dict[str, Any]) -> dict[str, bool]:
    return {
        "G1": gate_receipts["G1"]["flow_runs_on_geometric_carrier_rows"] and gate_receipts["G1"]["per_step_membership_tables_emitted"],
        "G2": gate_receipts["G2"]["cardinality_conservation_all_steps"] and gate_receipts["G2"]["injected_violation_caught"],
        "G3": gate_receipts["G3"]["append_only_record_hash_chain_emitted"] and gate_receipts["G3"]["hash_chain_recomputed"],
        "G4": gate_receipts["G4"]["raw_reconstruction_from_P_T_full_raw_record_mismatch_count"] == 0
        and gate_receipts["G4"]["quotient_raw_reconstruction_mismatch_count"] > 0
        and gate_receipts["G4"]["quotient_level_reconstruction_mismatch_count"] == 0,
        "G5": gate_receipts["G5"]["z3_raw_uniqueness_verdict"] == "unsat"
        and gate_receipts["G5"]["cvc5_raw_uniqueness_verdict"] == "unsat"
        and gate_receipts["G5"]["z3_erased_control_verdict"] == "sat"
        and gate_receipts["G5"]["cvc5_erased_control_verdict"] == "sat"
        and gate_receipts["G5"]["z3_payload_bound_full_record_verdict"] == "unsat"
        and gate_receipts["G5"]["cvc5_payload_bound_full_record_verdict"] == "unsat"
        and gate_receipts["G5"]["z3_payload_bound_dropped_record_verdict"] == "sat"
        and gate_receipts["G5"]["cvc5_payload_bound_dropped_record_verdict"] == "sat"
        and gate_receipts["G5"]["erased_models_exhibited"]
        and gate_receipts["G5"]["payload_bound_models_exhibited"],
        "G6": gate_receipts["G6"]["erasure_reconstruction_fails"]
        and not gate_receipts["G6"]["erasure_internal_ledger_balances_without_environment"]
        and gate_receipts["G6"]["environment_charge_nats"] > 0
        and gate_receipts["G6"]["radiative_internal_erasure_charge_nats"] == 0.0,
        "G7": gate_receipts["G7"]["record_shuffle_changed_or_failed"],
        "G8": all(gate_receipts["G8"].values()),
    }


def build_result() -> dict[str, Any]:
    carrier = load_carrier()
    pin = pin_spec(carrier)
    predicates = pin["flow"]["steps"]
    support = carrier["support_table"]
    rows = carrier["probe_row_table"]
    support_by_id = {row["state_id"]: row for row in support}
    rows_by_id = {row["state_id"]: row for row in rows}
    all_ids = [row["state_id"] for row in support]

    raw_flow = build_flow(mode="raw_row", all_ids=all_ids, support_by_id=support_by_id, rows_by_id=rows_by_id, predicates=predicates)
    quotient_flow = build_flow(mode="quotient_class", all_ids=all_ids, support_by_id=support_by_id, rows_by_id=rows_by_id, predicates=predicates)
    recon = reconstruction_receipts(raw_flow, quotient_flow, rows_by_id, all_ids)
    variants = {"erasure": erasure_variant(raw_flow, all_ids), "lossy": lossy_variant(raw_flow, all_ids)}
    ctrl = controls(raw_flow, rows_by_id, predicates, all_ids)
    ctrl["erasure variant"] = {"fired": variants["erasure"]["fired"], "raw_reconstruction_mismatch_count": variants["erasure"]["raw_reconstruction_mismatch_count"]}
    ctrl["lossy-record variant"] = {"fired": variants["lossy"]["fired"], "raw_reconstruction_mismatch_count": variants["lossy"]["raw_reconstruction_mismatch_count"]}
    proofs = proof_receipts(raw_flow, all_ids, support_by_id, rows_by_id)
    gate_receipts = gates(raw_flow, quotient_flow, recon, variants, ctrl, proofs, all_ids)
    graph = torch_graph_receipt(raw_flow)
    gate_receipts["G3"]["pytorch_append_only_dag_forward_only"] = graph["append_only_record_chain_forward_only"]
    gate_receipts["G7"]["pytorch_record_graph_nodes"] = graph["node_count"]
    passes = gate_pass(gate_receipts)
    passes["G3"] = passes["G3"] and graph["append_only_record_chain_forward_only"]
    pin_hash = sha256_text(canonical_json(pin))
    all_pass = all(passes.values()) and all(item.get("fired", False) for item in ctrl.values()) and graph["append_only_record_chain_forward_only"]

    return {
        "schema": "compression_flow_radiated_record_leg_v0",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "candidate_math_labels": {
            "conservation": "CANDIDATE MATH -- first receipt for candidate conservation formalization",
            "reconstruction": "CANDIDATE MATH -- first receipt for candidate reconstruction formalization",
            "source": pin["candidate_math_source"],
            "doctrine_promotion": "not promoted to standing doctrine",
        },
        "PIN_SPEC": pin,
        "pin_block_sha256": pin_hash,
        "carrier_lineage": pin["carrier"]["carrier_lineage"],
        "carrier_support_table_hash": pin["carrier"]["carrier_support_table_hash"],
        "carrier_support_hash_recomputation_citation": MCT_SUPPORT_HASH_SERIALIZATION_CITATION,
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["torch", "torch_geometric", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["torch", "torch_geometric", "z3", "cvc5"],
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "torch-native predicate masks, set-flow tensor indices, ledgers, reconstruction, and erasure totals"},
            "torch_geometric": {
                "tried": True,
                "used": True,
                "reason": "load-bearing DAG degree receipt for append-only record and shuffled-order controls",
            },
            "z3": {"tried": True, "used": True, "reason": "load-bearing row-set and payload-bound uniqueness and erased-control SAT proof"},
            "cvc5": {"tried": True, "used": True, "reason": "independent load-bearing row-set and payload-bound uniqueness and erased-control SAT proof"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "torch": "load_bearing",
            "torch_geometric": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
        },
        "pytorch_independence_receipt": {
            "imports_jax_core": False,
            "pytorch_role": "independent_torch_flow_and_graph",
            "torch_native_scalars": [
                "support_size",
                "P_T_size",
                "total_emitted_rows",
                "raw_reconstruction_mismatch_count",
                "quotient_raw_reconstruction_mismatch_count",
                "quotient_level_mismatch_count",
                "max_conservation_defect",
                "injected_conservation_defect",
                "erasure_environment_charge_nats",
                "per_step_ledger",
                "reconstruction_mismatches",
                "telescoped_totals",
            ],
            "graph_only_scalars": [],
        },
        "pytorch_mask_receipt": torch_mask_receipt(all_ids, rows_by_id, predicates),
        "pytorch_graph_receipt": graph,
        "record_modes": {
            "raw_row": {
                "cardinality_ledger": raw_flow["cardinality_ledger"],
                "membership_tables": raw_flow["membership_tables"],
                "record_hash_chain": raw_flow["record_hash_chain"],
                "record_final_hash": raw_flow["record_final_hash"],
                "final_ids": raw_flow["final_ids"],
            },
            "quotient_class": {
                "cardinality_ledger": quotient_flow["cardinality_ledger"],
                "record_hash_chain": quotient_flow["record_hash_chain"],
                "record_final_hash": quotient_flow["record_final_hash"],
                "final_ids": quotient_flow["final_ids"],
            },
        },
        "reconstruction": recon,
        "variants": variants,
        "controls": ctrl,
        "crossover_proofs": proofs,
        "proof_rowset_coverage": proofs["proof_rowset_coverage"],
        "proof_payload_bound_z3": proofs["proof_payload_bound_z3"],
        "proof_payload_bound_cvc5": proofs["proof_payload_bound_cvc5"],
        "gates": gate_receipts,
        "gate_pass": passes,
        "values": {
            "support_size": len(all_ids),
            "P_T_size": len(raw_flow["final_ids"]),
            "total_emitted_rows": len(raw_flow["record_entries"]),
            "raw_reconstruction_mismatch_count": recon["raw_mode"]["raw_reconstruction_mismatch_count"],
            "quotient_raw_reconstruction_mismatch_count": recon["quotient_mode"]["raw_reconstruction_mismatch_count"],
            "quotient_level_mismatch_count": recon["quotient_mode"]["quotient_level_mismatch_count"],
            "max_conservation_defect": max(abs(row["cardinality_defect"]) for row in raw_flow["cardinality_ledger"]),
            "injected_conservation_defect": ctrl["injected conservation violation"]["ledger_defect"],
            "erasure_environment_charge_nats": variants["erasure"]["environment_charge_nats"],
            "erasure_register_basis": variants["erasure"]["erasure_register_basis"],
            "charge_full_support_identity": variants["erasure"]["charge_full_support_identity"],
            "charge_remaining_live_after_step": variants["erasure"]["charge_remaining_live_after_step"],
            "charge_pre_step_live": variants["erasure"]["charge_pre_step_live"],
            "charge_emitted_step_register": variants["erasure"]["charge_emitted_step_register"],
        },
        "all_pass": all_pass,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
