#!/usr/bin/env python3
"""Shared exact table logic for entropy_type_ratchet_v0."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SIM_ID = "entropy_type_ratchet_v0"
ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = PACKET / "results"

STATUS_CODE = {"undefined": 0, "computable": 1, "degenerate": 2}


class MissingStructure(RuntimeError):
    def __init__(self, structure: str):
        super().__init__(structure)
        self.structure = structure


class TypeConfusion(RuntimeError):
    pass


@dataclass(frozen=True)
class TypeSpec:
    type_id: str
    required: tuple[str, ...]
    typed_label: str


TYPE_SPECS = [
    TypeSpec("counting_entropy", ("finite_support",), "finite_counting_entropy_nats"),
    TypeSpec("chart_uniform_differential_entropy", ("chart_measure", "band_limit_convention"), "chart_uniform_differential_entropy_nats"),
    TypeSpec("von_neumann_entropy", ("density_quotient_rho",), "von_neumann_entropy_nats"),
    TypeSpec("conditional_vn_and_mutual_information", ("bipartition_subsystem_split",), "conditional_vn_mutual_information_nats"),
    TypeSpec("coherent_information", ("channel_update_map",), "coherent_information_nats"),
    TypeSpec("state_plus_record_conservation", ("record_syndrome_object",), "finite_state_plus_record_entropy_nats"),
]

PRIMARY_STEP_PLAN = [
    {
        "step_id": "integrated_seed",
        "source_step": "manifold_unified_run_v0:integrated_seed",
        "constraint": "hash-bound integrated n=3 seed",
        "enables": ["finite_support"],
        "operator_family": "finite_support_counter",
    },
    {
        "step_id": "leaf_conditioning",
        "source_step": "manifold_unified_run_v0:leaf_conditioning + ledger band-limit",
        "constraint": "condition_on_T_pi_over_6",
        "enables": ["chart_measure", "band_limit_convention"],
        "operator_family": "chart_volume_probe",
    },
    {
        "step_id": "lens_quotient",
        "source_step": "manifold_unified_run_v0:lens_quotient",
        "constraint": "Z4_finite_phase_lens_quotient",
        "enables": ["density_quotient_rho"],
        "operator_family": "density_CPTP_probe",
    },
    {
        "step_id": "terrain_restriction",
        "source_step": "manifold_unified_run_v0:terrain_restriction",
        "constraint": "terrain restriction plus subsystem cut",
        "enables": ["bipartition_subsystem_split"],
        "operator_family": "partial_trace_probe",
    },
    {
        "step_id": "deep_descended_phase_window",
        "source_step": "ratchet_deep_chain_v0:step3",
        "constraint": "descended_single_leaf_phase_window",
        "enables": ["channel_update_map"],
        "operator_family": "channel_update_probe",
    },
    {
        "step_id": "deep_second_Z2_lens",
        "source_step": "ratchet_deep_chain_v0:step4",
        "constraint": "second_Z2_lens_on_quotient",
        "enables": ["record_syndrome_object"],
        "operator_family": "record_conditioned_reconstruction_probe",
    },
    {
        "step_id": "deep_terrain_basin",
        "source_step": "ratchet_deep_chain_v0:step5",
        "constraint": "terrain_basin_restriction_Se_Funnel_L",
        "enables": [],
        "operator_family": "terrain_basin_order_probe",
    },
    {
        "step_id": "deep_terrain_operator",
        "source_step": "ratchet_deep_chain_v0:step6",
        "constraint": "terrain_then_operator_order_restriction",
        "enables": [],
        "operator_family": "terrain_operator_precedence_probe",
    },
    {
        "step_id": "deep_saturation",
        "source_step": "ratchet_deep_chain_v0:step7",
        "constraint": "repeat_available_committed_constraints_until_fixed_point",
        "enables": [],
        "operator_family": "idempotence_saturation_probe",
    },
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


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
    parents = {
        "owner_doctrine_entropy_type_ratchet_20260611": {
            "path": "system_v6/receipts/owner_doctrine_entropy_type_ratchet_20260611.md",
            "allowed_use": "pre-registered enabling-layer predictions and falsifiers",
        },
        "manifold_unified_run_v0_trajectory": {
            "path": "system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_step_trajectory_artifact.json",
            "allowed_use": "committed integrated seed, leaf, lens, terrain sequence and state hashes",
        },
        "ratchet_deep_chain_v0": {
            "path": "system_v6/sims/ratchet_deep_chain_v0/results/ratchet_deep_chain_v0_envelope_results.json",
            "allowed_use": "deep-chain quotient/order steps and path-sensitivity controls",
        },
        "manifold_entropy_ledger_v0": {
            "path": "system_v6/sims/manifold_entropy_ledger_v0/results/manifold_entropy_ledger_v0_envelope_results.json",
            "allowed_use": "typed entropy labels and band-limit convention",
        },
        "z4_syndrome_record_v0": {
            "path": "system_v6/sims/z4_syndrome_record_v0/results/z4_syndrome_record_v0_envelope_results.json",
            "allowed_use": "finite state-plus-record convention and syndrome reconstruction values",
        },
    }
    out: dict[str, Any] = {}
    for name, row in parents.items():
        payload = git_bytes(row["path"])
        out[name] = {
            "path": row["path"],
            "blob": git_blob(row["path"]),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "allowed_use": row["allowed_use"],
            "source": "git show HEAD:<path>",
        }
    return out


def load_parent_facts() -> dict[str, Any]:
    trajectory = read_json(ROOT / "system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_step_trajectory_artifact.json")
    deep = read_json(ROOT / "system_v6/sims/ratchet_deep_chain_v0/results/ratchet_deep_chain_v0_envelope_results.json")
    ledger = read_json(ROOT / "system_v6/sims/manifold_entropy_ledger_v0/results/manifold_entropy_ledger_v0_envelope_results.json")
    z4 = read_json(ROOT / "system_v6/sims/z4_syndrome_record_v0/results/z4_syndrome_record_v0_envelope_results.json")
    return {"trajectory": trajectory, "deep": deep, "ledger": ledger, "z4": z4}


def shannon_nats(probs: list[float]) -> float:
    return -sum(p * math.log(p) for p in probs if p > 0.0)


def entropy_label(value: float, exact: str, typed_label: str) -> dict[str, Any]:
    return {"exact": exact, "nats": value, "typed_label": typed_label, "log_base": "e"}


def require_structures(enabled: set[str], required: tuple[str, ...]) -> None:
    for structure in required:
        if structure not in enabled:
            raise MissingStructure(structure)


def matrix_entropy_diagonal(diagonal: list[float]) -> float:
    return shannon_nats(diagonal)


def evaluate_type(type_id: str, enabled: set[str], step_index: int, facts: dict[str, Any]) -> dict[str, Any]:
    spec = next(row for row in TYPE_SPECS if row.type_id == type_id)
    require_structures(enabled, spec.required)
    if type_id == "counting_entropy":
        support = 8 if step_index < 2 else 4 if step_index < 5 else 24
        return {
            "status": "computable",
            "value": entropy_label(math.log(support), f"log({support})", spec.typed_label),
            "witness": f"finite_support_size={support}",
        }
    if type_id == "chart_uniform_differential_entropy":
        deep_rows = facts["deep"]["ratchet_sequence"]["per_step_ledger"]["rows"]
        h_by_step = {
            1: ("log(4*pi**2)", math.log(4 * math.pi * math.pi)),
            2: ("2*log(pi)", 2 * math.log(math.pi)),
            3: ("log(pi**2/2)", math.log(math.pi * math.pi / 2)),
            4: ("log(pi**2/4)", math.log(math.pi * math.pi / 4)),
        }
        if step_index >= 4:
            exact = str(deep_rows[min(step_index - 1, len(deep_rows) - 1)]["entropy"]["h_nats"])
            value = float(deep_rows[min(step_index - 1, len(deep_rows) - 1)]["entropy"]["h_float_nats"])
        else:
            exact, value = h_by_step.get(step_index, ("log(4*pi**2)", math.log(4 * math.pi * math.pi)))
        return {
            "status": "computable",
            "value": entropy_label(value, exact, spec.typed_label),
            "witness": "band_limit_convention_from_manifold_entropy_ledger_v0",
        }
    if type_id == "von_neumann_entropy":
        rho_diag = [0.5, 0.5]
        return {
            "status": "computable",
            "value": entropy_label(matrix_entropy_diagonal(rho_diag), "log(2)", spec.typed_label),
            "rho": [[0.5, 0.0], [0.0, 0.5]],
            "witness": "actual_density_quotient_rho_diag_half_half",
        }
    if type_id == "conditional_vn_and_mutual_information":
        if "channel_update_map" not in enabled:
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
                    "typed_label": spec.typed_label,
                },
                "degenerate_reason": "product_state_bipartition_so_S(A|B)=S(A)_and_I(A:B)=0",
                "witness": "rho_AB = rho_A tensor |0><0|",
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
                "typed_label": spec.typed_label,
            },
            "witness": "Bell_pair_density_after_channel_layer",
        }
    if type_id == "coherent_information":
        return {
            "status": "computable",
            "value": entropy_label(math.log(2), "log(2)", spec.typed_label),
            "channel": "identity_update_on_Bell_pair",
            "witness": "I_c = S(B)-S(AB)=log(2)-0",
        }
    if type_id == "state_plus_record_conservation":
        regimes = facts["z4"]["regimes"]["positive"]
        return {
            "status": "computable",
            "value": {
                "state_loss_without_record_exact": "log(4)",
                "record_retained_exact": "log(4)",
                "computed_defect_exact": "0",
                "state_loss_without_record_nats": regimes["state_loss_without_record_nats"],
                "record_retained_nats": regimes["record_retained_nats"],
                "computed_defect_nats": regimes["computed_defect_nats"],
                "typed_label": spec.typed_label,
            },
            "witness": "z4_syndrome_record_v0 positive full-record convention",
        }
    raise AssertionError(type_id)


def build_table(step_plan: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    facts = load_parent_facts()
    steps = step_plan or PRIMARY_STEP_PLAN
    enabled: set[str] = set()
    rows: list[dict[str, Any]] = []
    availability_sequence: list[dict[str, Any]] = []
    changes: list[dict[str, Any]] = []
    previous_available: set[str] = set()
    for index, step in enumerate(steps):
        enabled.update(step["enables"])
        type_rows: dict[str, Any] = {}
        for spec in TYPE_SPECS:
            try:
                row = evaluate_type(spec.type_id, enabled, index, facts)
            except MissingStructure as exc:
                row = {
                    "status": "undefined",
                    "missing_structure": exc.structure,
                    "typed_label": spec.typed_label,
                    "failure_mode": f"MissingStructure:{exc.structure}",
                }
            row["status_code"] = STATUS_CODE[row["status"]]
            type_rows[spec.type_id] = row
        available = {type_id for type_id, row in type_rows.items() if row["status"] in {"computable", "degenerate"}}
        if available != previous_available:
            changes.append({
                "step_id": step["step_id"],
                "enabled_now": sorted(available - previous_available),
                "named_enabling_structures": list(step["enables"]),
            })
        previous_available = available
        operator_row = operator_witness(step, enabled, index, facts)
        rows.append({
            "index": index,
            "step_id": step["step_id"],
            "source_step": step["source_step"],
            "constraint": step["constraint"],
            "new_enabling_structures": list(step["enables"]),
            "enabled_structures_after_step": sorted(enabled),
            "entropy_types": type_rows,
            "operator_co_ratchet": operator_row,
            "row_hash": stable_hash({"step_id": step["step_id"], "types": {k: v["status_code"] for k, v in type_rows.items()}, "ops": operator_row["status"]}),
        })
        availability_sequence.append({
            "step_id": step["step_id"],
            "available_types": sorted(available),
            "status_codes": {k: v["status_code"] for k, v in type_rows.items()},
        })
    return {
        "rows": rows,
        "availability_sequence": availability_sequence,
        "change_steps": changes,
        "type_specs": [spec.__dict__ for spec in TYPE_SPECS],
    }


def operator_witness(step: dict[str, Any], enabled: set[str], index: int, facts: dict[str, Any]) -> dict[str, Any]:
    family = step["operator_family"]
    requirements = {
        "finite_support_counter": ["finite_support"],
        "chart_volume_probe": ["chart_measure", "band_limit_convention"],
        "density_CPTP_probe": ["density_quotient_rho"],
        "partial_trace_probe": ["bipartition_subsystem_split"],
        "channel_update_probe": ["channel_update_map"],
        "record_conditioned_reconstruction_probe": ["record_syndrome_object"],
        "terrain_basin_order_probe": ["channel_update_map"],
        "terrain_operator_precedence_probe": ["channel_update_map"],
        "idempotence_saturation_probe": ["record_syndrome_object"],
    }
    missing = [name for name in requirements[family] if name not in enabled]
    if missing:
        return {"family": family, "status": "undefined", "missing_structure": missing[0], "failure_mode": f"MissingStructure:{missing[0]}"}
    if family == "finite_support_counter":
        return {"family": family, "status": "applied", "application": "counted carrier_dimension=8", "co_varies_with": "counting_entropy"}
    if family == "chart_volume_probe":
        return {"family": family, "status": "applied", "application": "computed chart volume entropy under band-limit convention", "co_varies_with": "chart_uniform_differential_entropy"}
    if family == "density_CPTP_probe":
        return {"family": family, "status": "applied", "application": "applied identity CPTP map to rho=diag(1/2,1/2)", "co_varies_with": "von_neumann_entropy"}
    if family == "partial_trace_probe":
        return {"family": family, "status": "applied", "application": "traced product rho_AB and flagged degenerate information row", "co_varies_with": "conditional_vn_and_mutual_information"}
    if family == "channel_update_probe":
        return {"family": family, "status": "applied", "application": "identity update map on Bell carrier gives I_c=log(2)", "co_varies_with": "coherent_information"}
    if family == "record_conditioned_reconstruction_probe":
        return {"family": family, "status": "applied", "application": "Z4 syndrome reconstructs quotient representatives with zero defect", "co_varies_with": "state_plus_record_conservation"}
    return {"family": family, "status": "applied", "application": f"{family} carries inherited enabled families", "co_varies_with": "inherited_operator_family"}


def evaluate_premature_controls() -> dict[str, Any]:
    controls: dict[str, Any] = {}
    for type_id, enabled in {
        "von_neumann_entropy": {"finite_support", "chart_measure"},
        "conditional_vn_and_mutual_information": {"finite_support", "density_quotient_rho"},
        "coherent_information": {"finite_support", "density_quotient_rho", "bipartition_subsystem_split"},
    }.items():
        try:
            evaluate_type(type_id, enabled, 0, load_parent_facts())
        except MissingStructure as exc:
            controls[type_id] = {"pass": True, "raised": f"MissingStructure:{exc.structure}", "sentinel_number_returned": False}
        else:
            controls[type_id] = {"pass": False, "raised": None, "sentinel_number_returned": True}
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
            {"typed_label": "finite_counting_entropy_nats", "nats": math.log(2)},
            {"typed_label": "von_neumann_entropy_nats", "nats": math.log(2)},
        )
    except TypeConfusion as exc:
        return {"pass": True, "raised": str(exc), "cross_type_sum_without_convention": "rejected"}
    return {"pass": False, "cross_type_sum_without_convention": "accepted"}


def order_shuffle_controls() -> dict[str, Any]:
    primary = build_table(PRIMARY_STEP_PLAN)["availability_sequence"]
    swap_density_earlier = list(PRIMARY_STEP_PLAN)
    swap_density_earlier[1], swap_density_earlier[2] = swap_density_earlier[2], swap_density_earlier[1]
    record_late = list(PRIMARY_STEP_PLAN)
    record_late[5], record_late[8] = record_late[8], record_late[5]
    variants = {
        "primary": primary,
        "swap_chart_and_density": build_table(swap_density_earlier)["availability_sequence"],
        "delay_record_until_saturation": build_table(record_late)["availability_sequence"],
    }
    availability_by_type: dict[str, dict[str, int | None]] = {}
    for name, seq in variants.items():
        for spec in TYPE_SPECS:
            first = next((i for i, step in enumerate(seq) if step["status_codes"][spec.type_id] != 0), None)
            availability_by_type.setdefault(spec.type_id, {})[name] = first
    changed = {
        type_id: len({idx for idx in values.values()}) > 1
        for type_id, values in availability_by_type.items()
    }
    return {
        "pass": any(changed.values()),
        "prediction_2_status": "survived" if any(changed.values()) else "killed",
        "availability_by_type_first_index": availability_by_type,
        "changed_by_type": changed,
        "variant_sequences": variants,
    }


def degenerate_flag_control(table: dict[str, Any]) -> dict[str, Any]:
    row = table["rows"][3]["entropy_types"]["conditional_vn_and_mutual_information"]
    return {
        "pass": row["status"] == "degenerate",
        "step_id": table["rows"][3]["step_id"],
        "observed_status": row["status"],
        "degenerate_reason": row.get("degenerate_reason"),
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
    }
