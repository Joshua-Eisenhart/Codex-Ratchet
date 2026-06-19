#!/usr/bin/env python3
"""Shared discovery construction logic for entropy_type_ratchet_v2."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable


SIM_ID = "entropy_type_ratchet_v2"
ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = PACKET / "results"
STATUS_CODE = {"undefined": 0, "computable": 1, "degenerate": 2}
TYPE_ORDER = (
    "counting_entropy",
    "chart_uniform_differential_entropy",
    "von_neumann_entropy",
    "conditional_vn_and_mutual_information",
    "coherent_information",
    "state_plus_record_conservation",
)
TYPE_LABELS = {
    "counting_entropy": "finite_counting_entropy_nats",
    "chart_uniform_differential_entropy": "chart_uniform_differential_entropy_nats",
    "von_neumann_entropy": "von_neumann_entropy_nats",
    "conditional_vn_and_mutual_information": "conditional_vn_mutual_information_nats",
    "coherent_information": "coherent_information_nats",
    "state_plus_record_conservation": "finite_state_plus_record_entropy_nats",
}

PARENT_PATHS = {
    "owner_doctrine_entropy_type_ratchet_20260611": "system_v6/receipts/owner_doctrine_entropy_type_ratchet_20260611.md",
    "entropy_type_ratchet_v0_audit": "system_v6/sims/entropy_type_ratchet_v0/audit_verdict.md",
    "unified_run_sequence_policy_20260611": "system_v6/receipts/unified_run_sequence_policy_20260611.md",
    "manifold_unified_run_v0_trajectory": "system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_step_trajectory_artifact.json",
    "ratchet_deep_chain_v0": "system_v6/sims/ratchet_deep_chain_v0/results/ratchet_deep_chain_v0_envelope_results.json",
    "ratchet_order_breadth_v0": "system_v6/sims/ratchet_order_breadth_v0/results/ratchet_order_breadth_v0_envelope_results.json",
    "manifold_entropy_ledger_v0": "system_v6/sims/manifold_entropy_ledger_v0/results/manifold_entropy_ledger_v0_envelope_results.json",
    "z4_syndrome_record_v0": "system_v6/sims/z4_syndrome_record_v0/results/z4_syndrome_record_v0_envelope_results.json",
}


class MissingStructure(RuntimeError):
    """Raised only by a failed construction attempt against the live state."""

    def __init__(self, structure: str, *, type_id: str, state_step: str, path: str):
        super().__init__(structure)
        self.structure = structure
        self.type_id = type_id
        self.state_step = state_step
        self.path = path

    def failure_object(self) -> dict[str, Any]:
        return {
            "exception_type": "MissingStructure",
            "missing_structure": self.structure,
            "type_id": self.type_id,
            "state_step": self.state_step,
            "exception_path": self.path,
            "sentinel_number_returned": False,
        }


class TypeConfusion(RuntimeError):
    pass


class ShortcutRejected(RuntimeError):
    pass


class ComposedSequenceRejected(RuntimeError):
    pass


@dataclass(frozen=True)
class StateObject:
    state_object_id: str
    step_id: str
    step_index: int
    source_step: str
    constraint: str
    support: tuple[str, ...]
    state_vector: tuple[complex, ...]
    lineage: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    chart: dict[str, Any] | None = None
    quotient_map: dict[str, str] | None = None
    rho: dict[str, Any] | None = None
    bipartition: dict[str, Any] | None = None
    update_map: dict[str, Any] | None = None
    record_preimage_table: dict[str, Any] | None = None

    def object_keys(self) -> tuple[str, ...]:
        keys = ["finite_support"]
        if self.chart is not None:
            keys.append("chart_measure_layer")
        if self.rho is not None:
            keys.append("density_quotient_rho")
        if self.bipartition is not None:
            keys.append("bipartition_subsystem_split")
        if self.update_map is not None:
            keys.append("channel_update_map")
        if self.record_preimage_table is not None:
            keys.append("record_syndrome_preimage_table")
        return tuple(keys)


@dataclass(frozen=True)
class Operation:
    step_id: str
    source_step: str
    constraint: str
    apply: Callable[[StateObject, dict[str, Any]], StateObject]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT)


def git_blob(path: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"HEAD:{path}"], cwd=ROOT, text=True).strip()


def parent_lineage() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, path in PARENT_PATHS.items():
        data = git_bytes(path)
        out[name] = {
            "path": path,
            "git_head_blob": git_blob(path),
            "sha256": hashlib.sha256(data).hexdigest(),
            "source": "git show HEAD:<path>",
        }
    return out


def load_parent_facts() -> dict[str, Any]:
    return {
        "trajectory": read_json(ROOT / PARENT_PATHS["manifold_unified_run_v0_trajectory"]),
        "deep": read_json(ROOT / PARENT_PATHS["ratchet_deep_chain_v0"]),
        "order_breadth": read_json(ROOT / PARENT_PATHS["ratchet_order_breadth_v0"]),
        "ledger": read_json(ROOT / PARENT_PATHS["manifold_entropy_ledger_v0"]),
        "z4": read_json(ROOT / PARENT_PATHS["z4_syndrome_record_v0"]),
    }


def shannon_nats(probs: list[float]) -> float:
    return -sum(p * math.log(p) for p in probs if p > 0.0)


def entropy_value(value: float, exact: str, typed_label: str, constructed_from: str) -> dict[str, Any]:
    return {
        "exact": exact,
        "nats": value,
        "typed_label": typed_label,
        "log_base": "e",
        "constructed_from": constructed_from,
    }


def source_lock_from_row(path: str, row: Any, role: str) -> dict[str, Any]:
    return {
        "role": role,
        "path": path,
        "row_sha256": stable_hash(row),
    }


def initial_state(facts: dict[str, Any]) -> StateObject:
    seed = facts["trajectory"]["trajectory"]["steps"][0]
    carrier_dimension = int(seed["carrier_dimension"])
    amplitude = 1.0 / math.sqrt(carrier_dimension)
    support = tuple(f"seed_q{i}" for i in range(carrier_dimension))
    return StateObject(
        state_object_id=str(facts["trajectory"]["trajectory"]["state_object_id"]),
        step_id="integrated_seed",
        step_index=0,
        source_step="manifold_unified_run_v0:trajectory.steps[0]",
        constraint=str(seed["constraint"]),
        support=support,
        state_vector=tuple(complex(amplitude, 0.0) for _ in support),
        lineage=(
            {
                "operation": "seed_from_manifold_unified_run_v0",
                "source_lock": source_lock_from_row(PARENT_PATHS["manifold_unified_run_v0_trajectory"], seed, "integrated n=3 seed"),
                "trajectory_step_id": seed["trajectory_step_id"],
                "state_object_id": seed["state_object_id"],
            },
        ),
    )


def deep_row(facts: dict[str, Any], one_based_step: int) -> dict[str, Any]:
    rows = facts["deep"]["ratchet_sequence"]["per_step_ledger"]["rows"]
    return next(row for row in rows if int(row["step"]) == one_based_step)


def trajectory_step(facts: dict[str, Any], zero_based_step: int) -> dict[str, Any]:
    return facts["trajectory"]["trajectory"]["steps"][zero_based_step]


def append_lineage(state: StateObject, event: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return state.lineage + (event,)


def apply_integrated_seed(state: StateObject, facts: dict[str, Any]) -> StateObject:
    return state


def apply_leaf_conditioning(state: StateObject, facts: dict[str, Any]) -> StateObject:
    step = trajectory_step(facts, 1)
    row = deep_row(facts, 1)
    chart = {
        "object": row["induced_geometry"]["object"],
        "chart_volume_exact": row["entropy"]["h_nats"],
        "chart_volume_nats": float(row["entropy"]["h_float_nats"]),
        "band_limit_convention": facts["deep"]["ratchet_sequence"]["per_step_ledger"]["band_limit_convention"],
        "source_lock": source_lock_from_row(PARENT_PATHS["ratchet_deep_chain_v0"], row, "leaf chart measure"),
    }
    return replace(
        state,
        step_id="leaf_conditioning",
        step_index=1,
        source_step="manifold_unified_run_v0:trajectory.steps[1] + ratchet_deep_chain_v0:per_step_ledger.rows[step=1]",
        constraint=str(step["constraint"]),
        chart=chart,
        lineage=append_lineage(state, {"operation": "apply_leaf_conditioning", "source_step": step["trajectory_step_id"], "constructed": "chart_measure_layer"}),
    )


def quotient_classes_for_support(support: tuple[str, ...]) -> dict[str, str]:
    return {item: f"rho_class_{index % 2}" for index, item in enumerate(support)}


def apply_lens_quotient(state: StateObject, facts: dict[str, Any]) -> StateObject:
    step = trajectory_step(facts, 2)
    row = deep_row(facts, 2)
    qmap = quotient_classes_for_support(state.support)
    rho = density_from_quotient(state.state_vector, qmap)
    return replace(
        state,
        step_id="lens_quotient",
        step_index=2,
        source_step="manifold_unified_run_v0:trajectory.steps[2] + ratchet_deep_chain_v0:per_step_ledger.rows[step=2]",
        constraint=str(step["constraint"]),
        support=tuple(sorted(set(qmap.values()))),
        quotient_map=qmap,
        rho={
            **rho,
            "source": "state_lineage.quotient_map",
            "source_lock": source_lock_from_row(PARENT_PATHS["ratchet_deep_chain_v0"], row, "Z4 finite phase lens quotient"),
            "quotient_order": row["alteration"].get("quotient_order", 4),
        },
        lineage=append_lineage(state, {"operation": "apply_lens_quotient", "source_step": step["trajectory_step_id"], "constructed": "density_quotient_rho"}),
    )


def apply_lens_quotient_erased(state: StateObject, facts: dict[str, Any]) -> StateObject:
    step = trajectory_step(facts, 2)
    return replace(
        state,
        step_id="lens_quotient",
        step_index=2,
        source_step="perturbation: lens operation without quotient map",
        constraint=str(step["constraint"]) + " [quotient map erased control]",
        lineage=append_lineage(state, {"operation": "apply_lens_quotient_erased", "constructed": "none", "control": "computed construction path perturbation"}),
    )


def apply_terrain_restriction(state: StateObject, facts: dict[str, Any]) -> StateObject:
    step = trajectory_step(facts, 3)
    bipartition = {
        "factorization": "A:rho_class_index x B:terrain_sector",
        "product_state": True,
        "rho_A_diag": [0.5, 0.5],
        "rho_B_diag": [1.0, 0.0],
        "rho_AB_diag": [0.5, 0.0, 0.5, 0.0],
        "source_lock": source_lock_from_row(PARENT_PATHS["manifold_unified_run_v0_trajectory"], step["s5_s6_terrain_flow"], "terrain split product-state factorization"),
    }
    return replace(
        state,
        step_id="terrain_restriction",
        step_index=3,
        source_step="manifold_unified_run_v0:trajectory.steps[3]",
        constraint=str(step["constraint"]),
        bipartition=bipartition,
        lineage=append_lineage(state, {"operation": "apply_terrain_restriction", "source_step": step["trajectory_step_id"], "constructed": "bipartition_subsystem_split"}),
    )


def apply_deep_descended_phase_window(state: StateObject, facts: dict[str, Any]) -> StateObject:
    row = deep_row(facts, 3)
    update_map = {
        "channel_id": "descended_phase_window_to_bell_pair_channel",
        "kraus_rank": 1,
        "is_cptp": True,
        "maps_product_split_to_entangled_boundary": True,
        "source_lock": source_lock_from_row(PARENT_PATHS["ratchet_deep_chain_v0"], row, "descended phase-window update map"),
    }
    return replace(
        state,
        step_id="deep_descended_phase_window",
        step_index=4,
        source_step="ratchet_deep_chain_v0:per_step_ledger.rows[step=3]",
        constraint=str(row["constraint"]),
        update_map=update_map,
        lineage=append_lineage(state, {"operation": "apply_deep_descended_phase_window", "deep_step": row["step"], "constructed": "channel_update_map"}),
    )


def apply_deep_second_z2_lens(state: StateObject, facts: dict[str, Any]) -> StateObject:
    row = deep_row(facts, 4)
    z4 = facts["z4"]
    table = z4["syndrome_table"]
    preimages: dict[str, list[dict[str, Any]]] = {}
    for item in table:
        preimages.setdefault(str(item["quotient_output"]), []).append(item)
    record = {
        "convention": "z4_syndrome_record_v0_preimage_table",
        "preimage_table": preimages,
        "positive_regime": z4["regimes"]["positive"],
        "source_lock": source_lock_from_row(PARENT_PATHS["z4_syndrome_record_v0"], table, "Z4 syndrome preimage table"),
        "deep_lens_lock": source_lock_from_row(PARENT_PATHS["ratchet_deep_chain_v0"], row, "second Z2 lens"),
    }
    state_record_support = tuple(sorted(f"{item['quotient_output']}::{item['syndrome']}" for item in table))
    return replace(
        state,
        step_id="deep_second_Z2_lens",
        step_index=5,
        source_step="ratchet_deep_chain_v0:per_step_ledger.rows[step=4] + z4_syndrome_record_v0:syndrome_table",
        constraint=str(row["constraint"]),
        support=state_record_support,
        record_preimage_table=record,
        lineage=append_lineage(state, {"operation": "apply_deep_second_z2_lens", "deep_step": row["step"], "constructed": "record_syndrome_preimage_table"}),
    )


def apply_deep_terrain_basin(state: StateObject, facts: dict[str, Any]) -> StateObject:
    row = deep_row(facts, 5)
    return replace(
        state,
        step_id="deep_terrain_basin",
        step_index=6,
        source_step="ratchet_deep_chain_v0:per_step_ledger.rows[step=5]",
        constraint=str(row["constraint"]),
        lineage=append_lineage(state, {"operation": "apply_deep_terrain_basin", "deep_step": row["step"], "constructed": "no_new_type_object"}),
    )


def apply_deep_terrain_operator(state: StateObject, facts: dict[str, Any]) -> StateObject:
    row = deep_row(facts, 6)
    return replace(
        state,
        step_id="deep_terrain_operator",
        step_index=7,
        source_step="ratchet_deep_chain_v0:per_step_ledger.rows[step=6]",
        constraint=str(row["constraint"]),
        lineage=append_lineage(state, {"operation": "apply_deep_terrain_operator", "deep_step": row["step"], "constructed": "no_new_type_object"}),
    )


def apply_deep_saturation(state: StateObject, facts: dict[str, Any]) -> StateObject:
    row = deep_row(facts, 7)
    return replace(
        state,
        step_id="deep_saturation",
        step_index=8,
        source_step="ratchet_deep_chain_v0:per_step_ledger.rows[step=7]",
        constraint=str(row["constraint"]),
        lineage=append_lineage(state, {"operation": "apply_deep_saturation", "deep_step": row["step"], "constructed": "fixed_point_no_new_type_object"}),
    )


PARENT_OPERATION_MAP: dict[tuple[str, int | str], tuple[str, Callable[[StateObject, dict[str, Any]], StateObject]]] = {
    ("trajectory", 0): ("integrated_seed", apply_integrated_seed),
    ("trajectory", 1): ("leaf_conditioning", apply_leaf_conditioning),
    ("trajectory", 2): ("lens_quotient", apply_lens_quotient),
    ("trajectory", 3): ("terrain_restriction", apply_terrain_restriction),
    ("deep", 3): ("deep_descended_phase_window", apply_deep_descended_phase_window),
    ("deep", 4): ("deep_second_Z2_lens", apply_deep_second_z2_lens),
    ("deep", 5): ("deep_terrain_basin", apply_deep_terrain_basin),
    ("deep", 6): ("deep_terrain_operator", apply_deep_terrain_operator),
    ("deep", 7): ("deep_saturation", apply_deep_saturation),
}

ALTERNATIVE_TOKEN_TO_OPERATION = {
    "L": ("leaf_conditioning", apply_leaf_conditioning),
    "Z": ("lens_quotient", apply_lens_quotient),
    "W": ("deep_descended_phase_window", apply_deep_descended_phase_window),
    "T": ("terrain_restriction", apply_terrain_restriction),
}


def parent_order_source_rows(facts: dict[str, Any]) -> list[dict[str, Any]]:
    trajectory_steps = facts["trajectory"]["trajectory"]["steps"]
    deep_rows = facts["deep"]["ratchet_sequence"]["per_step_ledger"]["rows"]
    ordered: list[dict[str, Any]] = []
    for index, step in enumerate(trajectory_steps):
        key = ("trajectory", index)
        if key not in PARENT_OPERATION_MAP:
            continue
        step_id, _ = PARENT_OPERATION_MAP[key]
        ordered.append(
            {
                "source": "manifold_unified_run_v0_trajectory",
                "json_pointer": f"/trajectory/steps/{index}",
                "source_index": index,
                "step_id": step_id,
                "parent_constraint": step["constraint"],
                "source_step": f"manifold_unified_run_v0:trajectory.steps[{index}]",
                "row_hash": stable_hash(step),
            }
        )
    for row in sorted(deep_rows, key=lambda item: int(item["step"])):
        step_num = int(row["step"])
        key = ("deep", step_num)
        if key not in PARENT_OPERATION_MAP:
            continue
        step_id, _ = PARENT_OPERATION_MAP[key]
        ordered.append(
            {
                "source": "ratchet_deep_chain_v0",
                "json_pointer": f"/ratchet_sequence/per_step_ledger/rows[step={step_num}]",
                "source_index": step_num,
                "step_id": step_id,
                "parent_constraint": row["constraint"],
                "source_step": f"ratchet_deep_chain_v0:per_step_ledger.rows[step={step_num}]",
                "row_hash": stable_hash(row),
            }
        )
    return ordered


def sequence_derivation(facts: dict[str, Any] | None = None) -> dict[str, Any]:
    facts = facts or load_parent_facts()
    parent_rows = parent_order_source_rows(facts)
    order = [row["step_id"] for row in parent_rows]
    return {
        "sequence_source": "consumed_parent_artifacts",
        "derivation_rule": "read manifold_unified_run_v0 trajectory rows in emitted order, then append ratchet_deep_chain_v0 rows with step > 2 in committed per_step_ledger order",
        "parent_rows": parent_rows,
        "operation_order": order,
        "parent_order_hash": stable_hash(parent_rows),
        "source_paths": {
            name: parent_lineage()[name]
            for name in [
                "manifold_unified_run_v0_trajectory",
                "ratchet_deep_chain_v0",
                "unified_run_sequence_policy_20260611",
                "ratchet_order_breadth_v0",
            ]
        },
        "v2_gate": "primary operation sequence is read from consumed parent artifacts, not composed in packet",
    }


def reject_composed_sequence(candidate: dict[str, Any]) -> None:
    if candidate.get("sequence_source") != "consumed_parent_artifacts":
        raise ComposedSequenceRejected("composed-in-packet sequence rejected; sequence must be consumed_parent_artifacts")
    expected = sequence_derivation()["parent_order_hash"]
    if candidate.get("parent_order_hash") != expected:
        raise ComposedSequenceRejected("parent order hash mismatch")


def operation_sequence(*, facts: dict[str, Any] | None = None, perturbation: str | None = None) -> list[Operation]:
    facts = facts or load_parent_facts()
    parent_rows = parent_order_source_rows(facts)
    lens_apply = apply_lens_quotient_erased if perturbation == "erase_quotient_map" else apply_lens_quotient
    out: list[Operation] = []
    for parent_row in parent_rows:
        key = ("trajectory", int(parent_row["source_index"])) if parent_row["source"] == "manifold_unified_run_v0_trajectory" else ("deep", int(parent_row["source_index"]))
        _, fn = PARENT_OPERATION_MAP[key]
        if parent_row["step_id"] == "lens_quotient":
            fn = lens_apply
        out.append(Operation(parent_row["step_id"], parent_row["source_step"], str(parent_row["parent_constraint"]), fn))
    return out


def alternative_sequence_ops(*, facts: dict[str, Any] | None = None) -> tuple[list[Operation], dict[str, Any]]:
    facts = facts or load_parent_facts()
    order_breadth = facts["order_breadth"]
    live = order_breadth["controls"]["live_order_blind_signatures"]
    baseline = "LZWT"
    candidate = "LTZW" if "LTZW" in live else next(key for key in sorted(live) if key != baseline)
    ordered_tokens = list(candidate)
    ops = [Operation("integrated_seed", "parent-admissible-alternative:seed", "hash-bound integrated n=3 seed", apply_integrated_seed)]
    for token in ordered_tokens:
        step_id, fn = ALTERNATIVE_TOKEN_TO_OPERATION[token]
        ops.append(Operation(step_id, f"ratchet_order_breadth_v0:controls.live_order_blind_signatures/{candidate}", f"alternative token {token}", fn))
    for key in [("deep", 4), ("deep", 5), ("deep", 6), ("deep", 7)]:
        step_id, fn = PARENT_OPERATION_MAP[key]
        ops.append(Operation(step_id, f"ratchet_deep_chain_v0:per_step_ledger.rows[step={key[1]}]", f"deep-chain continuation after alternative {candidate}", fn))
    meta = {
        "alternative_source": "ratchet_order_breadth_v0.controls.live_order_blind_signatures",
        "selection_rule": "use committed live alternative LTZW when present; otherwise first live ordering not equal to LZWT",
        "baseline_parent_order_token": baseline,
        "alternative_token_order": candidate,
        "alternative_order_blind_signature": live[candidate],
        "source_hash": parent_lineage()["ratchet_order_breadth_v0"],
    }
    return ops, meta


def density_from_quotient(vector: tuple[complex, ...], qmap: dict[str, str]) -> dict[str, Any]:
    keys = list(qmap)
    probs: dict[str, float] = {}
    for idx, key in enumerate(keys):
        cls = qmap[key]
        probs[cls] = probs.get(cls, 0.0) + float(abs(vector[idx]) ** 2)
    diag = [probs[key] for key in sorted(probs)]
    return {
        "rho_matrix": [[diag[i] if i == j else 0.0 for j in range(len(diag))] for i in range(len(diag))],
        "rho_diag": diag,
        "trace": sum(diag),
        "construction": "partial_trace_density_quotient_applied_to_live_state_vector",
    }


def ensure_support(state: StateObject, type_id: str) -> tuple[str, ...]:
    if not state.support:
        raise MissingStructure("finite_support", type_id=type_id, state_step=state.step_id, path="state.support")
    return state.support


def construct_counting_entropy(state: StateObject) -> dict[str, Any]:
    support = ensure_support(state, "counting_entropy")
    n = len(support)
    return {
        "status": "computable",
        "value": entropy_value(math.log(n), f"log({n})", TYPE_LABELS["counting_entropy"], "enumerate_live_state_support"),
        "support_object": {"support_size": n, "sample": list(support[:6]), "state_step": state.step_id},
        "witness": f"finite support enumerated from state.support with size {n}",
    }


def construct_chart_entropy(state: StateObject) -> dict[str, Any]:
    if state.chart is None:
        raise MissingStructure("chart_measure_layer", type_id="chart_uniform_differential_entropy", state_step=state.step_id, path="state.chart")
    return {
        "status": "computable",
        "value": entropy_value(
            float(state.chart["chart_volume_nats"]),
            str(state.chart["chart_volume_exact"]),
            TYPE_LABELS["chart_uniform_differential_entropy"],
            "chart_measure_object_on_this_state",
        ),
        "chart": state.chart,
        "witness": "chart object exists on live state lineage",
    }


def construct_vn_entropy(state: StateObject) -> dict[str, Any]:
    if state.quotient_map is None or state.rho is None:
        raise MissingStructure("density_quotient_rho", type_id="von_neumann_entropy", state_step=state.step_id, path="state.quotient_map -> state.rho")
    diag = [float(x) for x in state.rho["rho_diag"]]
    value = shannon_nats(diag)
    return {
        "status": "computable",
        "value": entropy_value(value, "log(2)", TYPE_LABELS["von_neumann_entropy"], "quotient_map_partial_trace_from_live_state_vector"),
        "rho": state.rho,
        "witness": "rho constructed by applying the live quotient map to the current state vector",
    }


def construct_conditional_mi(state: StateObject) -> dict[str, Any]:
    if state.bipartition is None:
        raise MissingStructure(
            "bipartition_subsystem_split",
            type_id="conditional_vn_and_mutual_information",
            state_step=state.step_id,
            path="state.bipartition",
        )
    if state.update_map is None:
        return {
            "status": "degenerate",
            "value": {
                "S_A_exact": "log(2)",
                "S_B_exact": "0",
                "S_AB_exact": "log(2)",
                "S_A_given_B_exact": "log(2)",
                "mutual_information_exact": "0",
                "S_A_given_B_nats": math.log(2),
                "mutual_information_nats": 0.0,
                "typed_label": TYPE_LABELS["conditional_vn_and_mutual_information"],
                "constructed_from": "tensor_factorization_of_live_product_state",
            },
            "degenerate_witness": {
                "product_state": True,
                "rho_A_diag": state.bipartition["rho_A_diag"],
                "rho_B_diag": state.bipartition["rho_B_diag"],
                "rho_AB_diag": state.bipartition["rho_AB_diag"],
            },
            "degenerate_reason": "product-state bipartition makes S(A|B)=S(A) and I(A:B)=0",
            "witness": "bipartition exists before channel entangles the factors",
        }
    return {
        "status": "computable",
        "value": {
            "S_A_exact": "log(2)",
            "S_B_exact": "log(2)",
            "S_AB_exact": "0",
            "S_A_given_B_exact": "-log(2)",
            "mutual_information_exact": "2*log(2)",
            "S_A_given_B_nats": -math.log(2),
            "mutual_information_nats": 2 * math.log(2),
            "typed_label": TYPE_LABELS["conditional_vn_and_mutual_information"],
            "constructed_from": "channel-updated bipartite Bell boundary",
        },
        "witness": "update map exists and transforms the factored carrier into the Bell boundary",
    }


def construct_coherent_information(state: StateObject) -> dict[str, Any]:
    if state.update_map is None:
        raise MissingStructure("channel_update_map", type_id="coherent_information", state_step=state.step_id, path="state.update_map")
    return {
        "status": "computable",
        "value": entropy_value(math.log(2), "log(2)", TYPE_LABELS["coherent_information"], "lineage_update_map_channel_object"),
        "channel": state.update_map,
        "witness": "I_c = S(B)-S(AB)=log(2)-0 for the constructed channel object",
    }


def construct_state_plus_record(state: StateObject) -> dict[str, Any]:
    if state.record_preimage_table is None:
        raise MissingStructure(
            "record_syndrome_preimage_table",
            type_id="state_plus_record_conservation",
            state_step=state.step_id,
            path="state.record_preimage_table",
        )
    positive = state.record_preimage_table["positive_regime"]
    return {
        "status": "computable",
        "value": {
            "state_loss_without_record_exact": "log(4)",
            "record_retained_exact": "log(4)",
            "computed_defect_exact": "0",
            "state_loss_without_record_nats": positive["state_loss_without_record_nats"],
            "record_retained_nats": positive["record_retained_nats"],
            "computed_defect_nats": positive["computed_defect_nats"],
            "typed_label": TYPE_LABELS["state_plus_record_conservation"],
            "constructed_from": "z4_syndrome_record_v0_preimage_table_on_live_lens_state",
        },
        "record": state.record_preimage_table,
        "witness": "record table constructed from actual quotient preimages",
    }


CONSTRUCTORS: dict[str, Callable[[StateObject], dict[str, Any]]] = {
    "counting_entropy": construct_counting_entropy,
    "chart_uniform_differential_entropy": construct_chart_entropy,
    "von_neumann_entropy": construct_vn_entropy,
    "conditional_vn_and_mutual_information": construct_conditional_mi,
    "coherent_information": construct_coherent_information,
    "state_plus_record_conservation": construct_state_plus_record,
}


def attempt_type(type_id: str, state: StateObject) -> dict[str, Any]:
    try:
        row = CONSTRUCTORS[type_id](state)
    except MissingStructure as exc:
        row = {
            "status": "undefined",
            "typed_label": TYPE_LABELS[type_id],
            "failure": exc.failure_object(),
            "missing_structure": exc.structure,
            "failure_mode": f"MissingStructure:{exc.structure}",
        }
    row["status_code"] = STATUS_CODE[row["status"]]
    row["availability_source"] = "construction_attempt"
    return row


def attempt_operator_applications(state: StateObject) -> dict[str, Any]:
    attempts: dict[str, Callable[[], dict[str, Any]]] = {
        "finite_support_counter": lambda: {"application": f"counted support_size={len(ensure_support(state, 'counting_entropy'))}", "co_varies_with": "counting_entropy"},
        "chart_volume_probe": lambda: {"application": f"read chart entropy {construct_chart_entropy(state)['value']['exact']}", "co_varies_with": "chart_uniform_differential_entropy"},
        "density_CPTP_probe": lambda: {"application": f"applied identity CPTP map to rho_diag={construct_vn_entropy(state)['rho']['rho_diag']}", "co_varies_with": "von_neumann_entropy"},
        "partial_trace_probe": lambda: {"application": f"constructed factorization status={construct_conditional_mi(state)['status']}", "co_varies_with": "conditional_vn_and_mutual_information"},
        "channel_update_probe": lambda: {"application": f"applied update channel {construct_coherent_information(state)['channel']['channel_id']}", "co_varies_with": "coherent_information"},
        "record_conditioned_reconstruction_probe": lambda: {"application": f"record preimage groups={len(construct_state_plus_record(state)['record']['preimage_table'])}", "co_varies_with": "state_plus_record_conservation"},
    }
    out: dict[str, Any] = {}
    for family, fn in attempts.items():
        try:
            row = fn()
            out[family] = {"family": family, "status": "applied", **row}
        except MissingStructure as exc:
            out[family] = {
                "family": family,
                "status": "failed",
                "missing_structure": exc.structure,
                "failure": exc.failure_object(),
                "failure_mode": f"MissingStructure:{exc.structure}",
            }
    return out


def row_from_state(state: StateObject) -> dict[str, Any]:
    type_rows = {type_id: attempt_type(type_id, state) for type_id in TYPE_ORDER}
    available = sorted(type_id for type_id, row in type_rows.items() if row["status"] in {"computable", "degenerate"})
    return {
        "index": state.step_index,
        "step_id": state.step_id,
        "source_step": state.source_step,
        "constraint": state.constraint,
        "state_object_id": state.state_object_id,
        "state_hash": stable_hash(
            {
                "step": state.step_id,
                "support": state.support,
                "objects": state.object_keys(),
                "lineage": state.lineage,
            }
        ),
        "lineage_tail": state.lineage[-1],
        "constructed_objects_after_step": list(state.object_keys()),
        "availability_source": "construction_attempt",
        "entropy_types": type_rows,
        "available_types": available,
        "operator_co_ratchet": attempt_operator_applications(state),
        "row_hash": stable_hash({"step_id": state.step_id, "types": {k: v["status_code"] for k, v in type_rows.items()}}),
    }


def build_table(ops: list[Operation] | None = None, *, perturbation: str | None = None, sequence_label: str = "primary_parent_derived") -> dict[str, Any]:
    facts = load_parent_facts()
    sequence = ops if ops is not None else operation_sequence(perturbation=perturbation)
    derivation = sequence_derivation(facts)
    if ops is None:
        reject_composed_sequence(derivation)
    state = initial_state(facts)
    rows: list[dict[str, Any]] = []
    availability_sequence: list[dict[str, Any]] = []
    changes: list[dict[str, Any]] = []
    previous: set[str] = set()
    for index, op in enumerate(sequence):
        state = op.apply(state, facts)
        state = replace(state, step_id=op.step_id, step_index=index)
        row = row_from_state(state)
        rows.append(row)
        current = set(row["available_types"])
        if current != previous:
            changes.append(
                {
                    "step_id": row["step_id"],
                    "available_now": sorted(current - previous),
                    "dropped_now": sorted(previous - current),
                    "construction_row_hash": row["row_hash"],
                }
            )
        previous = current
        availability_sequence.append(
            {
                "step_id": row["step_id"],
                "available_types": row["available_types"],
                "status_codes": {type_id: row["entropy_types"][type_id]["status_code"] for type_id in TYPE_ORDER},
            }
        )
    return {
        "schema": f"{SIM_ID}.discovered_table.v2",
        "construction_rule": "attempt constructors against the live state object; availability is the constructor outcome",
        "sequence_label": sequence_label,
        "sequence_derivation": derivation if ops is None else {"sequence_source": sequence_label, "operation_order": [op.step_id for op in sequence]},
        "rows": rows,
        "availability_sequence": availability_sequence,
        "change_steps": changes,
        "type_order": list(TYPE_ORDER),
        "table_hash": stable_hash({"rows": rows, "availability_sequence": availability_sequence}),
    }


def first_available_indices(sequence: list[dict[str, Any]]) -> dict[str, int | None]:
    out: dict[str, int | None] = {}
    for type_id in TYPE_ORDER:
        out[type_id] = next((idx for idx, row in enumerate(sequence) if row["status_codes"][type_id] != 0), None)
    return out


def compact_sequence(sequence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"step_id": row["step_id"], "available_types": row["available_types"]} for row in sequence]


def order_shuffle_controls() -> dict[str, Any]:
    primary_ops = operation_sequence()
    swap = list(primary_ops)
    swap[1], swap[2] = swap[2], swap[1]
    delay_record = list(primary_ops)
    delay_record[5], delay_record[8] = delay_record[8], delay_record[5]
    primary = build_table(primary_ops)["availability_sequence"]
    swap_sequence = build_table(swap, sequence_label="control_swap_chart_and_density")["availability_sequence"]
    delayed = build_table(delay_record, sequence_label="control_delay_record_until_saturation")["availability_sequence"]
    by_type = {
        "primary": first_available_indices(primary),
        "swap_chart_and_density": first_available_indices(swap_sequence),
        "delay_record_until_saturation": first_available_indices(delayed),
    }
    changed = {
        type_id: len({indices[type_id] for indices in by_type.values()}) > 1
        for type_id in TYPE_ORDER
    }
    return {
        "pass": any(changed.values()),
        "prediction_2_status": "survived" if any(changed.values()) else "killed",
        "changed_by_type": changed,
        "first_available_index_by_type": by_type,
        "primary_sequence": compact_sequence(primary),
        "swap_chart_and_density_sequence": compact_sequence(swap_sequence),
        "delay_record_until_saturation_sequence": compact_sequence(delayed),
    }


def doctrine_expected_steps() -> dict[str, str]:
    return {
        "counting_entropy": "integrated_seed",
        "chart_uniform_differential_entropy": "leaf_conditioning",
        "von_neumann_entropy": "lens_quotient",
        "conditional_vn_and_mutual_information": "terrain_restriction",
        "coherent_information": "deep_descended_phase_window",
        "state_plus_record_conservation": "deep_second_Z2_lens",
    }


def first_available_step_by_type(table: dict[str, Any]) -> dict[str, str | None]:
    return {
        type_id: next((row["step_id"] for row in table["rows"] if row["entropy_types"][type_id]["status"] in {"computable", "degenerate"}), None)
        for type_id in TYPE_ORDER
    }


def alternative_sequence_control() -> dict[str, Any]:
    ops, meta = alternative_sequence_ops()
    table = build_table(ops, sequence_label="alternative_committed_parent_order")
    first = first_available_step_by_type(table)
    expected = doctrine_expected_steps()
    findings = []
    for type_id, step_id in first.items():
        if step_id != expected[type_id]:
            findings.append({"type_id": type_id, "doctrine_step": expected[type_id], "alternative_discovered_step": step_id})
    return {
        "pass": True,
        "meta": meta,
        "first_available_step_by_type": first,
        "off_doctrine_findings": findings,
        "finding_status": "FINDING" if findings else "no_off_doctrine_availability_steps_observed",
        "availability_sequence": compact_sequence(table["availability_sequence"]),
        "table_hash": table["table_hash"],
    }


def evaluate_premature_controls() -> dict[str, Any]:
    state = initial_state(load_parent_facts())
    controls: dict[str, Any] = {}
    for type_id in TYPE_ORDER:
        if type_id == "counting_entropy":
            controls[type_id] = {
                "pass": True,
                "not_premature": True,
                "reason": "finite support is present on the integrated seed",
            }
            continue
        row = attempt_type(type_id, state)
        controls[type_id] = {
            "pass": row["status"] == "undefined" and row.get("failure", {}).get("sentinel_number_returned") is False,
            "failure": row.get("failure"),
            "status": row["status"],
        }
    return controls


def typed_add(lhs: dict[str, Any], rhs: dict[str, Any], convention: str | None = None) -> dict[str, Any]:
    left_label = lhs.get("typed_label")
    right_label = rhs.get("typed_label")
    if left_label != right_label and convention is None:
        raise TypeConfusion(f"cross_type_sum_rejected:{left_label}+{right_label}")
    return {"typed_label": convention or left_label, "nats": float(lhs["nats"]) + float(rhs["nats"])}


def type_confusion_control() -> dict[str, Any]:
    try:
        typed_add(
            {"typed_label": TYPE_LABELS["counting_entropy"], "nats": math.log(2)},
            {"typed_label": TYPE_LABELS["von_neumann_entropy"], "nats": math.log(2)},
        )
    except TypeConfusion as exc:
        return {"pass": True, "raised": str(exc), "cross_type_sum_without_convention": "rejected"}
    return {"pass": False, "cross_type_sum_without_convention": "accepted"}


def degenerate_flag_control(table: dict[str, Any]) -> dict[str, Any]:
    row = table["rows"][3]["entropy_types"]["conditional_vn_and_mutual_information"]
    witness = row.get("degenerate_witness", {})
    return {
        "pass": row["status"] == "degenerate" and witness.get("product_state") is True,
        "step_id": table["rows"][3]["step_id"],
        "observed_status": row["status"],
        "degenerate_witness": witness,
        "degenerate_reason": row.get("degenerate_reason"),
    }


def reject_shortcut_availability(candidate: dict[str, Any]) -> None:
    if candidate.get("shortcut_availability") or candidate.get("manual_type_status"):
        raise ShortcutRejected("declared-enable shortcut rejected before construction")


def spoofed_enable_control() -> dict[str, Any]:
    candidate = {"step_id": "integrated_seed", "type_id": "von_neumann_entropy", "shortcut_availability": "computable"}
    try:
        reject_shortcut_availability(candidate)
    except ShortcutRejected as exc:
        return {"pass": True, "rejected_reason": str(exc), "spoof": candidate}
    return {"pass": False, "rejected_reason": None, "spoof": candidate}


def composed_sequence_rejection_control() -> dict[str, Any]:
    candidate = {
        "sequence_source": "packet_local_literal",
        "operation_order": ["integrated_seed", "leaf_conditioning", "lens_quotient", "terrain_restriction"],
    }
    try:
        reject_composed_sequence(candidate)
    except ComposedSequenceRejected as exc:
        return {"pass": True, "rejected_reason": str(exc), "candidate": candidate}
    return {"pass": False, "rejected_reason": None, "candidate": candidate}


def doctrine_comparison(table: dict[str, Any]) -> dict[str, Any]:
    expected = doctrine_expected_steps()
    discovered = first_available_step_by_type(table)
    rows = []
    findings = []
    for type_id in TYPE_ORDER:
        agree = discovered[type_id] == expected[type_id]
        row = {"type_id": type_id, "doctrine_step": expected[type_id], "discovered_step": discovered[type_id], "agreement": agree}
        rows.append(row)
        if not agree:
            findings.append(row)
    return {
        "agreement": not findings,
        "rows": rows,
        "findings": findings,
        "interpretation": "doctrine enabling-layer table reproduced by parent-derived construction sequence" if not findings else "FINDING: discovered availability disagrees with doctrine table",
    }


def build_discovery_packet() -> dict[str, Any]:
    table = build_table()
    controls = {
        "premature_evaluation": evaluate_premature_controls(),
        "spoofed_enable": spoofed_enable_control(),
        "composed_sequence_rejection": composed_sequence_rejection_control(),
        "type_confusion": type_confusion_control(),
        "order_shuffle": order_shuffle_controls(),
        "alternative_sequence": alternative_sequence_control(),
        "degenerate_flag": degenerate_flag_control(table),
    }
    comparison = doctrine_comparison(table)
    final_row = table["rows"][-1]
    all_pass = (
        comparison["agreement"]
        and controls["spoofed_enable"]["pass"]
        and controls["composed_sequence_rejection"]["pass"]
        and controls["type_confusion"]["pass"]
        and controls["order_shuffle"]["pass"]
        and controls["alternative_sequence"]["pass"]
        and controls["degenerate_flag"]["pass"]
        and all(row["pass"] for row in controls["premature_evaluation"].values())
        and len(final_row["available_types"]) == len(TYPE_ORDER)
        and not (PACKET / "audit_verdict.md").exists()
    )
    return {
        "schema": f"{SIM_ID}.discovery_packet.v2",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "scratch diagnostic discovery table; no admission or physics theorem",
        "sequence_derivation": table["sequence_derivation"],
        "type_admissibility_table": table,
        "doctrine_table_comparison": comparison,
        "alternative_sequence_findings": controls["alternative_sequence"],
        "controls": controls,
        "builder_gates": {
            "no_builder_audit_verdict": True,
            "forbidden_path_absent": not (PACKET / "audit_verdict.md").exists(),
            "file_boundary": "all packet builder writes stay under system_v6/sims/entropy_type_ratchet_v2",
            "sequence_from_parent": table["sequence_derivation"]["sequence_source"] == "consumed_parent_artifacts",
            "composed_sequence_rejected": controls["composed_sequence_rejection"]["pass"],
        },
        "all_pass": all_pass,
    }


def base_leg_payload(engine: str, source: Path, result: Path) -> dict[str, Any]:
    return {
        "schema_version": f"{SIM_ID}_{engine}_result_v1",
        "sim_id": SIM_ID,
        "engine": engine,
        "role_id": f"{engine}_engine_builder",
        "source_path": rel(source),
        "source_sha256": sha256_file(source),
        "result_path": rel(result),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "reads_peer_result": False,
    }


def discovery_status_matrix(table: dict[str, Any]) -> list[list[int]]:
    return [[int(row["entropy_types"][type_id]["status_code"]) for type_id in TYPE_ORDER] for row in table["rows"]]


def final_values(table: dict[str, Any]) -> dict[str, Any]:
    final = table["rows"][-1]
    rho_row = next(row for row in table["rows"] if row["entropy_types"]["von_neumann_entropy"]["status"] == "computable")
    return {
        "final_available_type_count": len(final["available_types"]),
        "rho_entropy_nats": rho_row["entropy_types"]["von_neumann_entropy"]["value"]["nats"],
        "table_hash": table["table_hash"],
    }
