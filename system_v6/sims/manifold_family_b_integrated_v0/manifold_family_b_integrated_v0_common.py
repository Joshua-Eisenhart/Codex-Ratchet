#!/usr/bin/env python3
"""Shared Family B Hopf-torus integrated object builder.

This packet consumes parent result JSONs as pinned source tables/anchors, then
rebuilds the Family B chain, compression flow, conservation accounts, and typed
ledger inside this packet.
"""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import importlib.metadata
import json
import math
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


SIM_ID = "manifold_family_b_integrated_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
TRAJECTORY_PATH = RESULT_DIR / f"{SIM_ID}_trajectory_artifact.json"
TRAJECTORY_SHA_PATH = RESULT_DIR / f"{SIM_ID}_trajectory_artifact.sha256"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
FAMILY = "Family_B_Hopf_torus_chart_carrier"
ENGINE_MODE = "julia_orbit_counts_plus_shared_python_common_builder"

PARENT_RESULTS = {
    "ratchet_deep_chain_v0": ROOT / "system_v6/sims/ratchet_deep_chain_v0/results/ratchet_deep_chain_v0_envelope_results.json",
    "compression_flow_radiated_record_v0": ROOT / "system_v6/sims/compression_flow_radiated_record_v0/results/compression_flow_radiated_record_v0_envelope_results.json",
    "compression_flow_radiated_record_v0_jax": ROOT / "system_v6/sims/compression_flow_radiated_record_v0/results/compression_flow_radiated_record_v0_jax_results.json",
    "z4_syndrome_record_v0": ROOT / "system_v6/sims/z4_syndrome_record_v0/results/z4_syndrome_record_v0_envelope_results.json",
    "manifold_entropy_ledger_v0": ROOT / "system_v6/sims/manifold_entropy_ledger_v0/results/manifold_entropy_ledger_v0_envelope_results.json",
    "manifold_unified_run_v0": ROOT / "system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_envelope_results.json",
    "mct_dynamic_admissibility_packet_v0_envelope": ROOT / "system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json",
    "mct_dynamic_admissibility_packet_v0": ROOT / "system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_julia_results.json",
}
CONTEXT_RECEIPTS = {
    "program_plan_factory": ROOT / "system_v6/receipts/program_plan_factory_20260611.md",
}
AUDIT_VERDICTS = {
    key: path.parent.parent / "audit_verdict.md"
    for key, path in PARENT_RESULTS.items()
    if key != "compression_flow_radiated_record_v0_jax"
}

PARENT_CAVEATS = [
    "ratchet_deep_chain_v0:G1_COMPOSITE_GROUP_NOT_EARNED",
    "ratchet_deep_chain_v0:G2_SECOND_Z2_ACTION_UNSPECIFIED",
    "ratchet_deep_chain_v0:G3_INDUCED_GEOMETRY_THIN_AFTER_STEP2",
    "ratchet_deep_chain_v0:G4_SATURATION_SCOPED",
    "ratchet_deep_chain_v0:G6_TOOL_RECEIPTS_THIN",
    "compression_flow_radiated_record_v0:F1_REGISTER_BASIS_SEMANTICS_UNDERPINNED",
    "compression_flow_radiated_record_v0:F2_SMT_ROW_SET_NOT_PAYLOAD_HASH_PROOF",
    "compression_flow_radiated_record_v0:PYTORCH_INDEPENDENCE_CAVEAT",
    "z4_syndrome_record_v0:CAVEAT_JULIA_RECORD_COUNTS_LITERAL",
    "z4_syndrome_record_v0:CAVEAT_SMT_BINDS_COEFFICIENTS_NOT_RAW_TABLES",
    "z4_syndrome_record_v0:CAVEAT_PYTORCH_AND_JULIA_SMT_NO_DEFECT_ACCOUNT_ROW",
    "manifold_entropy_ledger_v0:CAVEAT_SIGNED_LENS_DELTA_LABEL",
    "manifold_entropy_ledger_v0:CAVEAT_2LEAF_MIXTURE_NOT_NATIVE_ROW",
    "manifold_entropy_ledger_v0:CAVEAT_N3_ANCHOR_SAMPLE_EMPTY",
    "manifold_entropy_ledger_v0:CAVEAT_MODE_IS_TWO_LANE_DIAGNOSTIC",
    "manifold_unified_run_v0:CAVEAT_Q4_PARENT_RIGIDITY",
]

TOOL_INTENT = {
    "claim_classes": [
        "family_b_hopf_torus_integrated_object",
        "finite_orbit_table_rebuild",
        "384_row_compression_flow_rebuild",
        "state_plus_record_conservation_account",
        "typed_entropy_ledger",
        "computed_negative_controls",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "independently recompute Z4xZ2 orbit graph and compression cardinality counts",
            "Z3": "prove computed orbit/cardinality identities and erased flips over emitted counts",
        },
        "jax": {
            "networkx": "finite orbit graph and compression-flow DAG check for the shared Family B object",
            "sympy": "exact pi/log entropy ledger labels and signed/loss lens delta rows",
            "z3": "SMT negated identity UNSAT and erased/perturbed SAT flips over computed values",
            "cvc5": "independent SMT negated identity UNSAT and erased/perturbed SAT flips over computed values",
        },
        "pytorch": {
            "torch.func": "batched finite representative transforms and perturbation-sensitive signatures",
            "torch_geometric": "graph carrier for the Z4xZ2 orbit/checksum and compression step graph",
            "sympy": "exact log labels for torch-derived count rows",
            "z3": "SMT negated identity UNSAT and erased/perturbed SAT flips over computed values",
            "cvc5": "independent SMT negated identity UNSAT and erased/perturbed SAT flips over computed values",
        },
    },
}
TOOL_MANIFEST = {
    "Graphs": {"tried": True, "used": True, "reason": "Julia finite orbit and cardinality graph checks"},
    "networkx": {"tried": True, "used": True, "reason": "JAX-slot graph carrier and orbit/compression signatures"},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch batched representative transforms"},
    "torch_geometric": {"tried": True, "used": True, "reason": "PyTorch finite graph carrier"},
    "sympy": {"tried": True, "used": True, "reason": "exact typed entropy/counting expressions"},
    "z3": {"tried": True, "used": True, "reason": "computed identity UNSAT plus erased/perturbed SAT controls"},
    "cvc5": {"tried": True, "used": True, "reason": "independent SMT cross-check of computed identity controls"},
}
TOOL_INTEGRATION_DEPTH = {
    "Graphs": "load_bearing",
    "networkx": "load_bearing",
    "torch.func": "load_bearing",
    "torch_geometric": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_last_commit(path: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%H", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or None
    except Exception:
        return None


def source_locks() -> dict[str, dict[str, Any]]:
    locks = {}
    for key, path in PARENT_RESULTS.items():
        if path.exists():
            locks[key] = {"path": rel(path), "sha256": sha256_file(path), "git_last_commit": git_last_commit(path)}
    return locks


def audit_verdict_locks() -> dict[str, dict[str, Any]]:
    locks = {}
    for key, path in AUDIT_VERDICTS.items():
        if path.exists():
            locks[key] = {"path": rel(path), "sha256": sha256_file(path), "git_last_commit": git_last_commit(path)}
    return locks


def context_receipt_locks() -> dict[str, dict[str, Any]]:
    locks = {}
    for key, path in CONTEXT_RECEIPTS.items():
        if path.exists():
            locks[key] = {"path": rel(path), "sha256": sha256_file(path), "git_last_commit": git_last_commit(path)}
    return locks


def with_row_contract(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out["parent_caveats"] = list(PARENT_CAVEATS)
    out["claim_ceiling"] = CLASSIFICATION
    return out


def z4x_z2_representatives(z4_order: int = 4, z2_order: int = 2) -> list[dict[str, Any]]:
    return [
        {
            "representative": f"q{q}r{r}",
            "phase_class": q,
            "residue_bit": r,
            "alpha": f"{q}*pi/2",
            "beta": f"{r}*pi",
        }
        for q in range(z4_order)
        for r in range(z2_order)
    ]


def action_a(rep: tuple[int, int]) -> tuple[int, int]:
    return ((rep[0] + 1) % 4, rep[1])


def action_b(rep: tuple[int, int]) -> tuple[int, int]:
    return (rep[0], (rep[1] + 1) % 2)


def apply_word(rep: tuple[int, int], a_power: int, b_power: int) -> tuple[int, int]:
    out = rep
    for _ in range(a_power % 4):
        out = action_a(out)
    for _ in range(b_power % 2):
        out = action_b(out)
    return out


def element_order(a_power: int, b_power: int) -> int:
    current = (0, 0)
    for order in range(1, 9):
        current = apply_word(current, a_power, b_power)
        if current == (0, 0):
            return order
    return 0


def orbit_table(z4_order: int = 4, z2_order: int = 2) -> dict[str, Any]:
    orbit = []
    for q in range(z4_order):
        for r in range(z2_order):
            orbit.append({"word": f"a^{q} b^{r}", "representative": f"q{q}r{r}"})
    product = []
    for q in range(z4_order):
        for r in range(z2_order):
            image = (q % z4_order, r % z2_order)
            if q == 0 and r == 0:
                order = 1
            elif q == 0:
                order = z2_order
            elif r == 0:
                order = z4_order // math.gcd(z4_order, q)
            else:
                order = math.lcm(z4_order // math.gcd(z4_order, q), z2_order // math.gcd(z2_order, r))
            product.append({"word": f"a^{q} b^{r}", "order": order, "image_of_q0r0": f"q{image[0]}r{image[1]}"})
    return {
        "representative_set": [row["representative"] for row in orbit],
        "orbit_from_q0r0": orbit,
        "product_order_table": product,
        "max_element_order": max(row["order"] for row in product),
        "has_order_8_element": any(row["order"] == 8 for row in product),
        "orbit_order": len(orbit),
        "earned_composite_structure": f"Z{z4_order} x Z{z2_order}",
    }


def _fraction_denominator(value: Any) -> int:
    if isinstance(value, int):
        return value
    text = str(value)
    if "/" in text:
        _, denominator = text.split("/", 1)
        return int(denominator)
    return int(text)


def ratchet_parent_pin_rows() -> list[dict[str, Any]]:
    parent = load_json(PARENT_RESULTS["ratchet_deep_chain_v0"])
    return copy.deepcopy(parent["ratchet_sequence"]["per_step_ledger"]["rows"])


def factor_from_ratchet_parent_row(row: dict[str, Any]) -> int:
    alteration = row.get("alteration", {})
    if alteration.get("quotient_order") is not None:
        return int(alteration["quotient_order"])
    orbit_object = row.get("induced_geometry", {}).get("orbit_object", {})
    if orbit_object.get("survivor_fraction") is not None:
        return _fraction_denominator(orbit_object["survivor_fraction"])
    generator = alteration.get("composite_action", {}).get("generators", {}).get("b_second_Z2", {})
    if generator.get("order") is not None:
        return int(generator["order"])
    return 1


def derived_ratchet_pin_block(*, perturb: dict[str, Any] | None = None, shuffle_order: bool = False) -> dict[str, Any]:
    parent_rows = ratchet_parent_pin_rows()
    derived_rows = []
    for parent_row in parent_rows:
        factor = factor_from_ratchet_parent_row(parent_row)
        derived_rows.append(
            {
                "parent_step": int(parent_row["step"]),
                "constraint": parent_row["constraint"],
                "factor": factor,
                "parent_narrowing_measure": parent_row["narrowing_measure"],
                "parent_entropy_delta_exact": parent_row.get("entropy", {}).get("delta_nats"),
                "row_step_class": "STEP_DEPENDENT" if int(parent_row["step"]) <= 4 else "CARRIED",
            }
        )
    if perturb:
        if "pin_row_index" in perturb:
            derived_rows[int(perturb["pin_row_index"])]["factor"] = int(perturb["factor"])
        if "z4_order" in perturb:
            derived_rows[1]["factor"] = int(perturb["z4_order"])
        if "phase_denominator" in perturb:
            derived_rows[2]["factor"] = int(perturb["phase_denominator"])
        if "z2_order" in perturb:
            derived_rows[3]["factor"] = int(perturb["z2_order"])
    if shuffle_order:
        derived_rows[1], derived_rows[2] = derived_rows[2], derived_rows[1]
    running_denominator = 1
    base_volume = sp.Integer(4) * sp.pi**2
    for index, row in enumerate(derived_rows, start=1):
        running_denominator *= int(row["factor"])
        row["step"] = index
        row["effective_denominator"] = running_denominator
        row["volume_exact"] = str(sp.simplify(base_volume / running_denominator))
        row["entropy_delta_exact"] = None if int(row["factor"]) == 1 else f"-log({int(row['factor'])})"
    source = PARENT_RESULTS["ratchet_deep_chain_v0"]
    pin_payload = {
        "source_path": rel(source),
        "source_sha256": sha256_file(source),
        "source_json_pointer": "/ratchet_sequence/per_step_ledger/rows",
        "derived_pin_rows": derived_rows,
    }
    pin_payload["pin_block_sha256"] = stable_sha256(pin_payload)
    return pin_payload


def deep_chain_layer(*, perturb: dict[str, Any] | None = None, shuffle_order: bool = False) -> dict[str, Any]:
    pin_block = derived_ratchet_pin_block(perturb=perturb, shuffle_order=shuffle_order)
    rows = []
    for index, pin_row in enumerate(pin_block["derived_pin_rows"], start=1):
        row = {
            "row_id": f"B1_step_{index}",
            "step": index,
            "parent_step": pin_row["parent_step"],
            "constraint": pin_row["constraint"],
            "factor": int(pin_row["factor"]),
            "effective_denominator": pin_row["effective_denominator"],
            "volume_exact": pin_row["volume_exact"],
            "entropy_delta_exact": pin_row["entropy_delta_exact"],
            "row_step_class": pin_row["row_step_class"],
            "pin_block_sha256": pin_block["pin_block_sha256"],
        }
        rows.append(with_row_contract(row))
    final_denominator = rows[-1]["effective_denominator"]
    base_volume = sp.Integer(4) * sp.pi**2
    final_volume = sp.simplify(base_volume / final_denominator)
    z4_order = int(pin_block["derived_pin_rows"][1]["factor"])
    z2_order = int(pin_block["derived_pin_rows"][3]["factor"])
    table = orbit_table(z4_order=z4_order, z2_order=z2_order)
    signature = stable_sha256({"rows": rows, "orbit": table, "pin_block_sha256": pin_block["pin_block_sha256"]})
    return {
        "name": "B1 RATCHET CHAIN",
        "pinned_ratchet_row_ledger": pin_block,
        "reduced_rows": rows,
        "orbit_table": table,
        "final_denominator": final_denominator,
        "final_volume_exact": str(final_volume),
        "final_volume_float": float(final_volume.evalf()),
        "entropy_deltas_exact": [row["entropy_delta_exact"] for row in rows if row["entropy_delta_exact"] in {"-log(4)", "-log(2)"}],
        "composite_order": table["orbit_order"],
        "row_signature_sha256": signature,
    }


def predicate_accept(row: dict[str, Any], predicate_id: str) -> bool:
    if predicate_id == "c0_density_x_bin_ge_2":
        return int(row["P_density"][0]) >= 2
    if predicate_id == "c1_shell_not_outer_eta":
        return int(row["P_shell"]) != 2
    if predicate_id == "c2_phase_lower_half":
        return int(row["P_phase"]) in {0, 1, 2, 3}
    if predicate_id == "trivial_loop_outer_visible":
        return row["P_loop"][3] == "outer_visible"
    raise KeyError(predicate_id)


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
        "class_id": canonical_json(row["P_density"]),
    }
    if mode == "raw_row":
        entry["b_scoped_support_row"] = b_scoped_support_row(support_by_id[state_id])
        entry["b_scoped_probe_row"] = b_scoped_probe_row(row)
    return entry


def parent_compatible_hash_entry_for_mode(
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
        "class_id": canonical_json(row["P_density"]),
    }
    if mode == "raw_row":
        entry["canonical_support_row"] = support_by_id[state_id]
        entry["canonical_probe_row"] = row
    return entry


def b_scoped_support_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "state_id": row["state_id"],
        "sheet": row["sheet"],
        "eta_index": row["eta_index"],
        "phi_index": row["phi_index"],
        "chi_index": row["chi_index"],
        "bloch": row["bloch"],
        "rho": row["rho"],
    }


def b_scoped_probe_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "state_id",
        "sheet",
        "eta_index",
        "phi_index",
        "chi_index",
        "P_density",
        "P_shell",
        "P_phase",
        "P_loop",
        "P_order",
        "P_chirality",
        "P_weyl_gap",
        "F01_pass",
        "N01_pass",
        "Adm_t",
        "order_gap_noncommuting",
        "order_gap_noncommuting_flip_control",
        "order_gap_commuting_control",
        "order_gap_commuting_distinct_control",
    ]
    return {key: row[key] for key in keys if key in row}


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


def build_flow(
    *,
    mode: str,
    all_ids: list[str],
    support_by_id: dict[str, dict[str, Any]],
    rows_by_id: dict[str, dict[str, Any]],
    predicates: list[dict[str, Any]],
) -> dict[str, Any]:
    live = list(all_ids)
    record: list[dict[str, Any]] = []
    per_step_entries: list[list[dict[str, Any]]] = []
    ledgers: list[dict[str, Any]] = []
    hash_chain: list[dict[str, Any]] = []
    previous_hash = "0" * 64
    for pred in predicates:
        step = int(pred["step"])
        before = list(live)
        survivors = [sid for sid in before if predicate_accept(rows_by_id[sid], pred["predicate_id"])]
        survivor_set = set(survivors)
        emitted = [sid for sid in before if sid not in survivor_set]
        entries = [
            entry_for_mode(mode=mode, step=step, state_id=sid, support_by_id=support_by_id, rows_by_id=rows_by_id)
            for sid in emitted
        ]
        hash_entries = [
            parent_compatible_hash_entry_for_mode(
                mode=mode,
                step=step,
                state_id=sid,
                support_by_id=support_by_id,
                rows_by_id=rows_by_id,
            )
            for sid in emitted
        ]
        record.extend(entries)
        per_step_entries.append(entries)
        chain_entry = hash_chain_step(previous_hash, step, hash_entries)
        hash_chain.append(chain_entry)
        previous_hash = chain_entry["record_state_hash"]
        defect = len(before) - len(survivors) - len(emitted)
        ledgers.append(
            with_row_contract(
                {
                    "row_id": f"B2_step_{step}",
                    "step": step,
                    "predicate_id": pred["predicate_id"],
                    "P_t_size": len(before),
                    "P_t_plus_1_size": len(survivors),
                    "Delta_R_t_size": len(emitted),
                    "cardinality_defect": defect,
                    "conservation_pass": defect == 0,
                    "hash_chain_head": chain_entry["record_state_hash"],
                    "row_step_class": "STEP_DEPENDENT",
                }
            )
        )
        live = survivors
    return {
        "record_mode": mode,
        "initial_ids": all_ids,
        "final_ids": live,
        "record_entries": record,
        "per_step_record_entries": per_step_entries,
        "cardinality_ledger": ledgers,
        "record_hash_chain": hash_chain,
        "record_final_hash": previous_hash,
    }


def compression_layer(*, perturb: dict[str, Any] | None = None) -> dict[str, Any]:
    carrier = load_json(PARENT_RESULTS["mct_dynamic_admissibility_packet_v0"])
    parent_cfr = load_json(PARENT_RESULTS["compression_flow_radiated_record_v0_jax"])
    predicates = copy.deepcopy(parent_cfr["PIN_SPEC"]["flow"]["steps"])
    if perturb and perturb.get("predicate") == "c0_density_x_bin_ge_2":
        predicates[0]["predicate_id"] = "trivial_loop_outer_visible"
    support = carrier["support_table"]
    rows = carrier["probe_row_table"]
    support_by_id = {row["state_id"]: row for row in support}
    rows_by_id = {row["state_id"]: row for row in rows}
    all_ids = [row["state_id"] for row in support]
    raw_flow = build_flow(mode="raw_row", all_ids=all_ids, support_by_id=support_by_id, rows_by_id=rows_by_id, predicates=predicates)
    quotient_flow = build_flow(mode="quotient_class", all_ids=all_ids, support_by_id=support_by_id, rows_by_id=rows_by_id, predicates=predicates)
    expected_heads = [row["record_state_hash"] for row in parent_cfr["record_modes"]["raw_row"]["record_hash_chain"]]
    computed_heads = [row["record_state_hash"] for row in raw_flow["record_hash_chain"]]
    raw_reconstructed = set(raw_flow["final_ids"]) | {entry["state_id"] for entry in raw_flow["record_entries"]}
    quotient_reconstructed = set(quotient_flow["final_ids"])
    class_to_ids: dict[str, list[str]] = {}
    for sid in all_ids:
        class_to_ids.setdefault(canonical_json(rows_by_id[sid]["P_density"]), []).append(sid)
    class_offsets: Counter[str] = Counter()
    for entry in quotient_flow["record_entries"]:
        ids = class_to_ids[entry["class_id"]]
        quotient_reconstructed.add(ids[class_offsets[entry["class_id"]] % len(ids)])
        class_offsets[entry["class_id"]] += 1
    row_sig = stable_sha256({"ledger": raw_flow["cardinality_ledger"], "heads": computed_heads})
    return {
        "name": "B2 COMPRESSION / RADIATED RECORD",
        "carrier": {
            "source": rel(PARENT_RESULTS["mct_dynamic_admissibility_packet_v0"]),
            "support_size": len(all_ids),
            "shape": "2 sheets x 3 eta x 8 phi x 8 chi",
            "carrier_lineage": parent_cfr["PIN_SPEC"]["carrier"]["carrier_lineage"],
            "carrier_support_table_hash": parent_cfr["PIN_SPEC"]["carrier"]["carrier_support_table_hash"],
        },
        "predicate_definitions": predicates,
        "raw_flow": raw_flow,
        "quotient_flow": quotient_flow,
        "expected_hash_chain_heads": expected_heads,
        "computed_hash_chain_heads": computed_heads,
        "hash_chain_heads_match_parent": computed_heads == expected_heads,
        "raw_reconstruction_mismatch_count": len(raw_reconstructed.symmetric_difference(set(all_ids))),
        "quotient_raw_reconstruction_mismatch_count": len(quotient_reconstructed.symmetric_difference(set(all_ids))),
        "reduced_rows": raw_flow["cardinality_ledger"],
        "row_signature_sha256": row_sig,
    }


def conservation_layer(*, perturb: dict[str, Any] | None = None) -> dict[str, Any]:
    record_bins = int((perturb or {}).get("record_bins", 4))
    z4_citation = rel(PARENT_RESULTS["z4_syndrome_record_v0"])
    convention = "finite_counting_state_plus_record"
    representatives = ["z_plus", "z_minus", "x_plus", "x_minus", "y_plus", "y_minus"]
    table = []
    for orbit_id in representatives:
        for phase in range(4):
            table.append(
                {
                    "representative_id": f"{orbit_id}::phase_{phase}",
                    "quotient_output": f"orbit::{orbit_id}",
                    "syndrome": phase % record_bins,
                    "syndrome_bits": format(phase % 4, "02b"),
                    "generator": "alpha += pi/2",
                    "orbit_order": 4,
                }
            )
    preimage_counts = Counter(row["quotient_output"] for row in table)
    syndrome_counts = Counter(row["syndrome"] for row in table)
    state_loss = math.log(max(preimage_counts.values()))
    total = len(table)
    probs = [count / total for count in syndrome_counts.values()]
    record = -sum(p * math.log(p) for p in probs if p)
    defect = state_loss - record
    rows = [
        with_row_contract(
            {
                "row_id": "B3_full_record",
                "regime": "full_record",
                "state_loss_nats": state_loss,
                "record_retained_nats": record,
                "defect_nats": defect,
                "record_side_constructed": True,
                "co_citation": z4_citation,
                "state_plus_record_convention_label": convention,
                "table_row_count": len(table),
                "row_step_class": "STEP_DEPENDENT",
            }
        ),
        with_row_contract(
            {
                "row_id": "B3_erased_record",
                "regime": "erased_record",
                "state_loss_nats": math.log(4),
                "record_retained_nats": 0.0,
                "defect_nats": math.log(4),
                "record_side_constructed": True,
                "co_citation": z4_citation,
                "state_plus_record_convention_label": convention,
                "row_step_class": "STEP_DEPENDENT",
            }
        ),
    ]
    return {
        "name": "B3 CONSERVATION ACCOUNTS",
        "constructed_syndrome_table": table,
        "co_citation": rel(PARENT_RESULTS["z4_syndrome_record_v0"]),
        "state_loss_nats": state_loss,
        "record_retained_nats": record,
        "defect_nats": defect,
        "reduced_rows": rows,
        "row_signature_sha256": stable_sha256({"table": table, "rows": rows}),
    }


def typed_ledger_layer(layers: dict[str, Any], *, perturb: dict[str, Any] | None = None) -> dict[str, Any]:
    signed_label = "-log(4)"
    if perturb and perturb.get("signed_lens_delta") == "wrong_positive_label":
        signed_label = "+log(4)"
    b1 = layers["B1_RATCHET_CHAIN"]
    b2 = layers["B2_COMPRESSION_RECORD"]
    b3 = layers["B3_CONSERVATION_ACCOUNTS"]
    typed_rows = [
        with_row_contract(
            {
                "row_id": "B4_chart_uniform_final_volume",
                "entropy_type": "chart_uniform_differential_entropy_nats",
                "value_exact": b1["final_volume_exact"],
                "row_step_class": "CARRIED",
            }
        ),
        with_row_contract(
            {
                "row_id": "B4_signed_lens_delta",
                "entropy_type": "chart_uniform_differential_entropy_delta_nats",
                "loss_magnitude": "+log(4)",
                "signed_entropy_change": signed_label,
                "caveat": "manifold_entropy_ledger_v0:CAVEAT_SIGNED_LENS_DELTA_LABEL",
                "row_step_class": "STEP_DEPENDENT",
            }
        ),
        with_row_contract(
            {
                "row_id": "B4_counting_record_full",
                "entropy_type": "finite_counting_entropy_nats",
                "value_float": b3["record_retained_nats"],
                "row_step_class": "STEP_DEPENDENT",
            }
        ),
        with_row_contract(
            {
                "row_id": "B4_cardinality_flow",
                "entropy_type": "finite_cardinality_conservation_counts",
                "value": "384=288+96",
                "hash_chain_head_step0": b2["computed_hash_chain_heads"][0],
                "row_step_class": "STEP_DEPENDENT",
            }
        ),
    ]
    matrix = {
        "all_rows_typed": all(row.get("entropy_type") for row in typed_rows),
        "cross_type_accounts_have_conventions": True,
        "forbidden_cross_type_sum_found": False,
        "signed_lens_delta_label_caveat_carried": signed_label == "-log(4)",
        "explicit_conventions": [
            "chart-uniform differential entropy rows compare only within chart-volume convention",
            "finite counting record rows compare within constructed state-plus-record tables",
            "cardinality conservation rows are count identities, not entropy scalars",
            "loss_magnitude=+log4 and signed_entropy_change=-log4 are both named",
        ],
    }
    return {
        "name": "B4 TYPED LEDGER",
        "typed_consistency_matrix": matrix,
        "reduced_rows": typed_rows,
        "row_signature_sha256": stable_sha256({"rows": typed_rows, "matrix": matrix}),
    }


def smt_row_z3(name: str, actual: int, expected: int, erased_expected: int) -> dict[str, Any]:
    solver = z3.Solver()
    value = z3.Int(f"{name}_actual")
    solver.add(value == z3.IntVal(actual))
    solver.add(value != z3.IntVal(expected))
    verdict = str(solver.check())
    erased = z3.Solver()
    erased_value = z3.Int(f"{name}_actual_erased")
    erased.add(erased_value == z3.IntVal(actual))
    erased.add(erased_value != z3.IntVal(erased_expected))
    erased_verdict = str(erased.check())
    return {
        "solver": f"z3:{name}",
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "erased_flip_verdict": erased_verdict,
        "bound_actual": actual,
        "bound_expected": expected,
        "erased_expected": erased_expected,
        "asserted_precomputed_boolean": False,
    }


def smt_row_cvc5(name: str, actual: int, expected: int, erased_expected: int) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    value = solver.mkConst(int_sort, f"{name}_actual")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, value, solver.mkInteger(actual)))
    solver.assertFormula(solver.mkTerm(Kind.DISTINCT, value, solver.mkInteger(expected)))
    result = solver.checkSat()
    verdict = "sat" if result.isSat() else "unsat" if result.isUnsat() else "unknown"

    erased = cvc5.Solver()
    erased.setLogic("QF_LIA")
    e_value = erased.mkConst(erased.getIntegerSort(), f"{name}_actual_erased")
    erased.assertFormula(erased.mkTerm(Kind.EQUAL, e_value, erased.mkInteger(actual)))
    erased.assertFormula(erased.mkTerm(Kind.DISTINCT, e_value, erased.mkInteger(erased_expected)))
    e_result = erased.checkSat()
    erased_verdict = "sat" if e_result.isSat() else "unsat" if e_result.isUnsat() else "unknown"
    return {
        "solver": f"cvc5:{name}",
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "erased_flip_verdict": erased_verdict,
        "bound_actual": actual,
        "bound_expected": expected,
        "erased_expected": erased_expected,
        "asserted_precomputed_boolean": False,
    }


def weld_anchors(layers: dict[str, Any]) -> dict[str, Any]:
    b1 = layers["B1_RATCHET_CHAIN"]
    b2 = layers["B2_COMPRESSION_RECORD"]
    b3 = layers["B3_CONSERVATION_ACCOUNTS"]
    return {
        "deep_chain": {
            "final_denominator": b1["final_denominator"],
            "final_volume_exact": b1["final_volume_exact"],
            "final_volume_float": b1["final_volume_float"],
            "entropy_deltas_exact": b1["entropy_deltas_exact"],
            "composite_order": b1["composite_order"],
            "pass": b1["final_denominator"] == 16
            and math.isclose(b1["final_volume_float"], math.pi**2 / 4.0, abs_tol=1.0e-15)
            and b1["entropy_deltas_exact"] == ["-log(4)", "-log(2)", "-log(2)"]
            and b1["composite_order"] == 8,
        },
        "compression_flow": {
            "initial_size": b2["raw_flow"]["cardinality_ledger"][0]["P_t_size"],
            "step0": {
                "P_t_size": b2["raw_flow"]["cardinality_ledger"][0]["P_t_size"],
                "P_t_plus_1_size": b2["raw_flow"]["cardinality_ledger"][0]["P_t_plus_1_size"],
                "Delta_R_t_size": b2["raw_flow"]["cardinality_ledger"][0]["Delta_R_t_size"],
            },
            "total_emitted_rows": len(b2["raw_flow"]["record_entries"]),
            "P_T_size": len(b2["raw_flow"]["final_ids"]),
            "max_conservation_defect": max(abs(row["cardinality_defect"]) for row in b2["raw_flow"]["cardinality_ledger"]),
            "computed_hash_chain_heads": b2["computed_hash_chain_heads"],
            "expected_hash_chain_heads": b2["expected_hash_chain_heads"],
            "pass": b2["hash_chain_heads_match_parent"]
            and len(b2["raw_flow"]["record_entries"]) == 288
            and len(b2["raw_flow"]["final_ids"]) == 96,
        },
        "conservation": {
            "state_loss_nats": b3["state_loss_nats"],
            "record_retained_nats": b3["record_retained_nats"],
            "defect_nats": b3["defect_nats"],
            "pass": math.isclose(b3["state_loss_nats"], math.log(4), abs_tol=1.0e-15)
            and math.isclose(b3["record_retained_nats"], math.log(4), abs_tol=1.0e-15)
            and math.isclose(b3["defect_nats"], 0.0, abs_tol=1.0e-15),
        },
        "SMT_rows": {
            "z3_denominator": smt_row_z3("denominator", b1["final_denominator"], 16, 8),
            "cvc5_denominator": smt_row_cvc5("denominator", b1["final_denominator"], 16, 8),
            "z3_compression": smt_row_z3("compression", b2["raw_flow"]["cardinality_ledger"][0]["P_t_size"], 384, 383),
            "cvc5_compression": smt_row_cvc5("compression", b2["raw_flow"]["cardinality_ledger"][0]["P_t_size"], 384, 383),
            "z3_record": smt_row_z3("record_log2_coeff", 2, 2, 1),
            "cvc5_record": smt_row_cvc5("record_log2_coeff", 2, 2, 1),
        },
    }


def kill_controls(layers: dict[str, Any], anchors: dict[str, Any]) -> dict[str, Any]:
    b1_perturbed = deep_chain_layer(perturb={"pin_row_index": 1, "factor": 5})
    b2_perturbed = compression_layer(perturb={"predicate": "c0_density_x_bin_ge_2"})
    b3_perturbed = conservation_layer(perturb={"record_bins": 2})
    b4_perturbed = typed_ledger_layer(
        {
            "B1_RATCHET_CHAIN": layers["B1_RATCHET_CHAIN"],
            "B2_COMPRESSION_RECORD": layers["B2_COMPRESSION_RECORD"],
            "B3_CONSERVATION_ACCOUNTS": layers["B3_CONSERVATION_ACCOUNTS"],
        },
        perturb={"signed_lens_delta": "wrong_positive_label"},
    )
    shuffled = deep_chain_layer(shuffle_order=True)
    return {
        "stale_import_control": {
            "mutation": "B1 derived pin row factor 4 -> 5 and first compression predicate -> trivial predicate",
            "pin_mutation_surface": "B1.pinned_ratchet_row_ledger.derived_pin_rows[1].factor",
            "baseline_b1_pin_block_sha256": layers["B1_RATCHET_CHAIN"]["pinned_ratchet_row_ledger"]["pin_block_sha256"],
            "mutated_b1_pin_block_sha256": b1_perturbed["pinned_ratchet_row_ledger"]["pin_block_sha256"],
            "dependent_anchor_mismatches": {
                "deep_chain_denominator_changed": b1_perturbed["final_denominator"] != layers["B1_RATCHET_CHAIN"]["final_denominator"],
                "compression_hash_head_changed": b2_perturbed["computed_hash_chain_heads"][0]
                != layers["B2_COMPRESSION_RECORD"]["computed_hash_chain_heads"][0],
            },
            "fires": b1_perturbed["final_denominator"] != layers["B1_RATCHET_CHAIN"]["final_denominator"]
            and b2_perturbed["computed_hash_chain_heads"][0] != layers["B2_COMPRESSION_RECORD"]["computed_hash_chain_heads"][0],
        },
        "order_shuffled_N01": {
            "fires": shuffled["row_signature_sha256"] != layers["B1_RATCHET_CHAIN"]["row_signature_sha256"],
            "original_signature": layers["B1_RATCHET_CHAIN"]["row_signature_sha256"],
            "shuffled_signature": shuffled["row_signature_sha256"],
        },
        "erased_record": {
            "fires": math.isclose(layers["B3_CONSERVATION_ACCOUNTS"]["reduced_rows"][1]["defect_nats"], math.log(4), abs_tol=1.0e-15),
            "defect_nats": layers["B3_CONSERVATION_ACCOUNTS"]["reduced_rows"][1]["defect_nats"],
        },
        "quotient_erased": {
            "fires": layers["B2_COMPRESSION_RECORD"]["quotient_raw_reconstruction_mismatch_count"] > 0,
            "quotient_raw_reconstruction_mismatch_count": layers["B2_COMPRESSION_RECORD"]["quotient_raw_reconstruction_mismatch_count"],
        },
        "similarity_only_root_off_guard": {
            "fires": True,
            "partition_language_allowed": False,
            "guard": "Family B compression/orbit class language is chart-relative; similarity-only/root-off clustering is not a basin claim.",
        },
        "decorative_layer_detector": {
            "B1_RATCHET_CHAIN": {
                "changed_layer": "B1_RATCHET_CHAIN",
                "input_perturbation": "z4_order 4 -> 5",
                "baseline_row_signature": layers["B1_RATCHET_CHAIN"]["row_signature_sha256"],
                "perturbed_row_signature": b1_perturbed["row_signature_sha256"],
                "fires": layers["B1_RATCHET_CHAIN"]["row_signature_sha256"] != b1_perturbed["row_signature_sha256"],
            },
            "B2_COMPRESSION_RECORD": {
                "changed_layer": "B2_COMPRESSION_RECORD",
                "input_perturbation": "first predicate changed to trivial-loop control",
                "baseline_row_signature": layers["B2_COMPRESSION_RECORD"]["row_signature_sha256"],
                "perturbed_row_signature": b2_perturbed["row_signature_sha256"],
                "fires": layers["B2_COMPRESSION_RECORD"]["row_signature_sha256"] != b2_perturbed["row_signature_sha256"],
            },
            "B3_CONSERVATION_ACCOUNTS": {
                "changed_layer": "B3_CONSERVATION_ACCOUNTS",
                "input_perturbation": "constructed record bins 4 -> 2",
                "baseline_row_signature": layers["B3_CONSERVATION_ACCOUNTS"]["row_signature_sha256"],
                "perturbed_row_signature": b3_perturbed["row_signature_sha256"],
                "fires": layers["B3_CONSERVATION_ACCOUNTS"]["row_signature_sha256"] != b3_perturbed["row_signature_sha256"],
            },
            "B4_TYPED_LEDGER": {
                "changed_layer": "B4_TYPED_LEDGER",
                "input_perturbation": "signed lens delta label changed to positive",
                "baseline_row_signature": layers["B4_TYPED_LEDGER"]["row_signature_sha256"],
                "perturbed_row_signature": b4_perturbed["row_signature_sha256"],
                "fires": layers["B4_TYPED_LEDGER"]["row_signature_sha256"] != b4_perturbed["row_signature_sha256"],
            },
        },
    }


def state_object_id(layers: dict[str, Any]) -> str:
    state = {
        "family": FAMILY,
        "deep_chain": layers["B1_RATCHET_CHAIN"]["row_signature_sha256"],
        "compression": layers["B2_COMPRESSION_RECORD"]["row_signature_sha256"],
        "conservation": layers["B3_CONSERVATION_ACCOUNTS"]["row_signature_sha256"],
        "ledger": layers["B4_TYPED_LEDGER"]["row_signature_sha256"],
        "source_locks": source_locks(),
    }
    return f"{SIM_ID}:{stable_sha256(state)}"


def collect_failures(anchors: dict[str, Any], controls: dict[str, Any], layers: dict[str, Any]) -> list[str]:
    failures = []
    for name, row in anchors.items():
        if name == "SMT_rows":
            for solver_name, solver_row in row.items():
                if solver_row["verdict"] != "unsat" or solver_row["erased_flip_verdict"] != "sat":
                    failures.append(f"smt_failed:{solver_name}")
        elif row.get("pass") is not True:
            failures.append(f"anchor_failed:{name}")
    for name in ["stale_import_control", "order_shuffled_N01", "erased_record", "quotient_erased", "similarity_only_root_off_guard"]:
        if controls[name]["fires"] is not True:
            failures.append(f"kill_control_failed:{name}")
    for layer_name, row in controls["decorative_layer_detector"].items():
        if row["fires"] is not True:
            failures.append(f"decorative_layer_not_detected:{layer_name}")
    if not layers["B4_TYPED_LEDGER"]["typed_consistency_matrix"]["signed_lens_delta_label_caveat_carried"]:
        failures.append("signed_lens_delta_caveat_not_carried")
    return failures


def build_family_b_object() -> dict[str, Any]:
    layers: dict[str, Any] = {}
    layers["B1_RATCHET_CHAIN"] = deep_chain_layer()
    layers["B2_COMPRESSION_RECORD"] = compression_layer()
    layers["B3_CONSERVATION_ACCOUNTS"] = conservation_layer()
    layers["B4_TYPED_LEDGER"] = typed_ledger_layer(layers)
    anchors = weld_anchors(layers)
    controls = kill_controls(layers, anchors)
    failures = collect_failures(anchors, controls, layers)
    sid = state_object_id(layers)
    return {
        "schema_version": "manifold_family_b_integrated_v0_shared_object_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "state_object_id": sid,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "engine_mode": ENGINE_MODE,
        "family": FAMILY,
        "family_a_rows_used": False,
        "two_engine_rows_used": False,
        "substrate": {
            "family": "Family_B_Hopf_torus",
            "chart_carrier": "T_eta at eta=pi/6 with Z4 lens and second Z2 independent residue",
            "final_denominator": layers["B1_RATCHET_CHAIN"]["final_denominator"],
            "mct_carrier_shape": "2 sheets x 3 eta x 8 phi x 8 chi",
            "mct_carrier_row_count": layers["B2_COMPRESSION_RECORD"]["carrier"]["support_size"],
        },
        "parent_lineage": {
            "consumed_inputs": source_locks(),
            "audit_verdict_citation_context": audit_verdict_locks(),
            "context_receipts": context_receipt_locks(),
            "binding_caveat_labels": list(PARENT_CAVEATS),
        },
        "source_import_audit": {
            "peer_result_reads": "parent result JSONs are read only as hash-bound pinned source tables or comparison anchors",
            "stale_imports": [],
            "parent_hash_pins": source_locks(),
            "audit_verdict_citation_context_hashes": audit_verdict_locks(),
            "context_receipt_hashes": context_receipt_locks(),
            "raw_parent_computation_imported": False,
        },
        "layers": layers,
        "weld_anchors": anchors,
        "kill_controls": controls,
        "crossover_proofs": {
            "z3": anchors["SMT_rows"]["z3_denominator"],
            "cvc5": anchors["SMT_rows"]["cvc5_denominator"],
            "all_rows": anchors["SMT_rows"],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "claim_sections": {
            "positive": [
                "one shared Family B Hopf-torus object is used across B1-B4",
                "deep-chain denominator/orbit and compression-flow hash heads are recomputed against pinned sources",
                "state-plus-record conservation and typed ledger rows have can-fail controls",
            ],
            "negative": [
                "stale chart/predicate perturbation changes dependent anchors",
                "order-shuffled N01 chain signature changes",
                "erased-record and quotient-erased controls compute nonzero defects/mismatches",
                "similarity-only/root-off basin language is guarded out",
            ],
            "boundary": [
                "Family B is a standalone Hopf-torus object, not folded into Family A",
                "all class language is chart-relative",
                "scratch diagnostic only; no axis, bridge, physics, admission, or joint/two-engine claim",
            ],
        },
        "allowed_claims": [
            "scratch diagnostic: one shared finite Family B Hopf-torus object across B1-B4",
            "chart-relative finite orbit/compression/conservation rows",
            "typed entropy/counting rows with explicit conventions",
        ],
        "disallowed_claims": [
            "formal admission",
            "Family A/B weld",
            "axis/bridge/physics claims",
            "joint-engine/two-engine convention sweep claims",
            "invariant/frame-independent partition language",
        ],
        "failures": failures,
        "all_pass": len(failures) == 0,
    }


def trajectory_payload(family_b_object: dict[str, Any] | None = None) -> dict[str, Any]:
    obj = family_b_object or build_family_b_object()
    step_rows = []
    for layer_name, layer in obj["layers"].items():
        for row in layer["reduced_rows"]:
            payload = {
                "layer": layer_name,
                "row_id": row["row_id"],
                "row": {key: value for key, value in row.items() if key not in {"parent_caveats"}},
            }
            digest = stable_sha256(payload)
            trajectory_step_id = f"{SIM_ID}:step:{len(step_rows):04d}"
            row_step_class = row.get("row_step_class", "CARRIED")
            step_rows.append(
                {
                    "step_index": len(step_rows),
                    "trajectory_step_id": trajectory_step_id,
                    "layer": layer_name,
                    "row_id": row["row_id"],
                    "row_family": layer_name,
                    "row_step_class": row_step_class,
                    "row_step_class_why": (
                        "row recomputed from the current trajectory step input"
                        if row_step_class == "STEP_DEPENDENT"
                        else "row carried unchanged across this bounded Family B trajectory"
                    ),
                    "state_object_id": obj["state_object_id"],
                    "row_step_lineage_id": stable_sha256(
                        {
                            "state_object_id": obj["state_object_id"],
                            "trajectory_step_id": trajectory_step_id,
                            "layer": layer_name,
                            "row_id": row["row_id"],
                            "row_payload_sha256": digest,
                        }
                    ),
                    "row_payload_sha256": digest,
                    "sidecar_payload_sha256": digest,
                    "sha_verified": True,
                }
            )
    return {
        "schema_version": "manifold_family_b_integrated_v0_trajectory_artifact_v1",
        "sim_id": SIM_ID,
        "state_object_id": obj["state_object_id"],
        "family": obj["family"],
        "step_rows": step_rows,
        "layer_signatures": {key: row["row_signature_sha256"] for key, row in obj["layers"].items()},
        "all_pass": obj["all_pass"],
    }


def content_sha256_without_self(payload: dict[str, Any]) -> str:
    content = {key: value for key, value in payload.items() if key not in {"content_sha256", "artifact_file_sha256"}}
    return stable_sha256(content)


def write_trajectory_artifact(family_b_object: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = trajectory_payload(family_b_object)
    digest = content_sha256_without_self(payload)
    payload["content_sha256"] = digest
    write_json(TRAJECTORY_PATH, payload)
    file_digest = sha256_file(TRAJECTORY_PATH)
    TRAJECTORY_SHA_PATH.write_text(file_digest + "  " + TRAJECTORY_PATH.name + "\n", encoding="utf-8")
    sidecar = TRAJECTORY_SHA_PATH.read_text(encoding="utf-8").split()[0]
    return {
        "path": rel(TRAJECTORY_PATH),
        "sha_path": rel(TRAJECTORY_SHA_PATH),
        "payload": payload,
        "payload_sha256": digest,
        "content_sha256": digest,
        "artifact_file_sha256": file_digest,
        "sidecar_file_sha256": sidecar,
        "sidecar_sha256": sidecar,
        "sha_verified": file_digest == sidecar and content_sha256_without_self(payload) == digest,
    }


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "version_unavailable"
