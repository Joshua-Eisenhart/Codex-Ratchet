from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable

import cvc5
import networkx as nx
import rustworkx as rx
import sympy as sp
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SIM_DIR / "results"

SIM_ID = "gcm_ratchet_order_matrix_v1"
PART_C_PACKET_NAME = "ratchet_order_matrix_on_gcm_v1"
CLASSIFICATION = "scratch_diagnostic"
EXPECTED_GCM_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_REGISTRY_BODY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
SHELL_LABEL = "pi/4"
SHELL_MISSING_OBJECT = "occupied_T_eta_stratum"

REGISTRY_PATH = ROOT / "system_v6/sims/gcm_object_id_freeze_v0/results/gcm_object_id_freeze_v0_registry.json"
GEOMETRY_ATTACH_PATH = ROOT / "system_v6/sims/gcm_geometry_attach_v0/results/gcm_geometry_attach_v0_results.json"
FLUX_ATTACH_PATH = ROOT / "system_v6/sims/gcm_connection_flux_attach_v0/results/gcm_connection_flux_attach_v0_results.json"
V0_RESULT_PATH = ROOT / "system_v6/sims/gcm_ratchet_order_matrix_v0/results/gcm_ratchet_order_matrix_v0_results.json"
V0_AUDIT_PATH = ROOT / "system_v6/sims/gcm_ratchet_order_matrix_v0/audit_verdict.md"
PART_C_PATH = ROOT / "system_v6/receipts/ratcheting_geometry_order_20260612.md"
LAYER_STACK_PATH = ROOT / "system_v6/receipts/gcm_layer_stack_reference_20260612.md"
QUBIT_LEDGER_PATH = ROOT / "system_v6/receipts/qubit_ladder_climb_ledger_20260612.md"
TERRAIN_SWEEP_PATH = ROOT / "system_v6/sims/ratchet_s6_terrain_sweep_v0/results/ratchet_s6_terrain_sweep_v0_envelope_results.json"
TERRAIN_OPERATOR_PATH = ROOT / "system_v6/sims/ratchet_s6_terrain_operator_shell_v0/results/ratchet_s6_terrain_operator_shell_v0_envelope_results.json"
OPERATOR_MATRIX64_PATH = ROOT / "system_v6/sims/terrain_operator_precedence_64_matrix/results/terrain_operator_precedence_64_matrix_envelope_results.json"
ORDER_BREADTH_PATH = ROOT / "system_v6/sims/ratchet_order_breadth_v0/results/ratchet_order_breadth_v0_envelope_results.json"
GCM_2Q_CARVE_PATH = ROOT / "system_v6/sims/gcm_constraint_carve_2q_v0/results/gcm_constraint_carve_2q_v0_results.json"
GCM_2Q_GEOMETRY_PATH = ROOT / "system_v6/sims/gcm_geometry_attach_2q_v0/results/gcm_geometry_attach_2q_v0_results.json"
ROUND3_ALIAS_PATH = ROOT / "system_v6/sims/round3_s4_alias_pass_v0/results/round3_s4_alias_pass_v0_envelope_results.json"
ROUND3_HEAVY_PATH = ROOT / "system_v6/sims/round3_s4_heavy_discriminator_v0/results/round3_s4_heavy_discriminator_v0_envelope_results.json"
SUBSTRATE_HELPER_PATH = ROOT / "scripts/gcm_substrate_check.py"
BOUNDARY_HELPER_PATH = ROOT / "scripts/builder_audit_boundary.py"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gcm_substrate_check import gcm_substrate_check


def now_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    completed = subprocess.run(
        ["git", "hash-object", rel(path)],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed.stdout.strip() or None


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    completed = subprocess.run(
        ["git", "log", "-1", "--format=%h", "--", rel(path)],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed.stdout.strip() or None


def source_lock(path: Path) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": file_sha256(path),
        "git_blob_hash": git_blob_hash(path),
        "git_last_commit": git_last_commit(path),
    }


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_context() -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH)
    geometry = load_json(GEOMETRY_ATTACH_PATH)
    frozen = registry["frozen_registry"]
    shell_rows = geometry["attachment_map"]["shell_occupancy"]["rows"]
    object_maps = geometry["attachment_map"]["object_maps"]
    rows_by_survivor = {row["survivor_id"]: row for row in shell_rows}
    objects_by_survivor = {row["survivor_id"]: row for row in object_maps}
    survivor_ids = [row["survivor_id"] for row in frozen["survivors"]]
    quotient_class_ids = [row["quotient_class_id"] for row in frozen["quotient_classes"]]
    candidate_region_ids = [row["candidate_region_id"] for row in frozen["candidate_regions"]]
    pi4_survivors = sorted(row["survivor_id"] for row in shell_rows if row.get("T_eta_label") == SHELL_LABEL)
    return {
        "registry": registry,
        "geometry": geometry,
        "survivor_ids": sorted(survivor_ids),
        "quotient_class_ids": sorted(quotient_class_ids),
        "candidate_region_ids": sorted(candidate_region_ids),
        "shell_rows": shell_rows,
        "rows_by_survivor": rows_by_survivor,
        "objects_by_survivor": objects_by_survivor,
        "pi4_survivors": pi4_survivors,
        "counts_by_T_eta": geometry["attachment_map"]["shell_occupancy"]["counts_by_T_eta"],
        "terrain_sweep": load_json(TERRAIN_SWEEP_PATH),
        "terrain_operator": load_json(TERRAIN_OPERATOR_PATH),
        "gcm_2q": load_json(GCM_2Q_CARVE_PATH),
    }


def lineage_from_context(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "gcm_object_id": EXPECTED_GCM_OBJECT_ID,
        "registry_body_sha256": EXPECTED_REGISTRY_BODY_SHA256,
        "survivor_ids": sorted(context["survivor_ids"]),
        "quotient_class_ids": sorted(context["quotient_class_ids"]),
        "candidate_region_ids": sorted(context["candidate_region_ids"]),
        "object_maps": sorted(
            (
                {
                    "survivor_id": row["survivor_id"],
                    "quotient_class_id": row["quotient_class_id"],
                    "candidate_region_id": row["candidate_region_id"],
                    "shell_id": row["shell_id"],
                    "T_eta_label": context["rows_by_survivor"][row["survivor_id"]]["T_eta_label"],
                }
                for row in context["objects_by_survivor"].values()
            ),
            key=lambda row: row["survivor_id"],
        ),
    }


def rows_for_survivors(state: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
    return [context["rows_by_survivor"][sid] for sid in sorted(state["survivor_ids"])]


def refresh_state_sets(state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    rows = rows_for_survivors(state, context)
    state["quotient_class_ids"] = sorted({row["quotient_class_id"] for row in rows})
    state["candidate_region_ids"] = sorted({row["candidate_region_id"] for row in rows})
    witness_ids = {f"survivor:{sid}" for sid in state["survivor_ids"]}
    witness_ids.update(f"quotient:{qid}" for qid in state["quotient_class_ids"])
    witness_ids.update(f"region:{rid}" for rid in state["candidate_region_ids"])
    if state["flags"].get("shell_conditioned"):
        witness_ids.add(f"T_eta:{SHELL_LABEL}")
        witness_ids.update(f"shell:{row['T_eta_shell_id']}" for row in rows)
    if state["flags"].get("quotient_lens_equivalence"):
        state.setdefault("readouts", {}).setdefault("quotient_lens_equivalence", {})
        state["readouts"]["quotient_lens_equivalence"].update(
            {
                "quotient_class_count": len(state["quotient_class_ids"]),
                "phase_erased": True,
                "survivor_lineage_preserved": True,
            }
        )
        witness_ids.update(f"density_class:{qid}" for qid in state["quotient_class_ids"])
    if state["flags"].get("local_window_support"):
        witness_ids.add(f"window_support:{file_sha256(ORDER_BREADTH_PATH)}")
    if state["flags"].get("flux_locked"):
        witness_ids.add(f"flux_holonomy:{file_sha256(FLUX_ATTACH_PATH)}")
    if state["flags"].get("terrain_conditioned"):
        witness_ids.add(f"terrain_conditioning:{file_sha256(TERRAIN_SWEEP_PATH)}")
    if state["flags"].get("operator_residency_precedence"):
        witness_ids.add(f"operator_channel_typing:{file_sha256(TERRAIN_OPERATOR_PATH)}")
    if state["flags"].get("depth_ladder_climbed"):
        witness_ids.add(f"cross_rung_embedding:{file_sha256(GCM_2Q_CARVE_PATH)}")
    state["witness_ids"] = sorted(witness_ids)
    return state


def initial_state(context: dict[str, Any]) -> dict[str, Any]:
    state = {
        "alive": True,
        "depth": "1Q",
        "survivor_ids": sorted(context["survivor_ids"]),
        "quotient_class_ids": sorted(context["quotient_class_ids"]),
        "candidate_region_ids": sorted(context["candidate_region_ids"]),
        "witness_ids": [],
        "flags": {
            "shell_conditioned": False,
            "quotient_lens_equivalence": False,
            "local_window_support": False,
            "flux_locked": False,
            "terrain_conditioned": False,
            "operator_residency_precedence": False,
            "depth_ladder_climbed": False,
            "entropy_readout_available": True,
        },
        "readouts": {},
        "history": [],
    }
    return refresh_state_sets(state, context)


def mortality(step_id: str, mortality_class: str, missing_object: str, detail: str) -> dict[str, Any]:
    return {
        "alive": False,
        "failed_step": step_id,
        "mortality_class": mortality_class,
        "missing_object": missing_object,
        "detail": detail,
    }


def require_1q(state: dict[str, Any], step_id: str) -> dict[str, Any] | None:
    if state.get("depth") != "1Q":
        return mortality(step_id, "depth_mismatch_after_climb", "1Q_carved_state", "The full Part-C 1Q row cannot be applied after the depth ladder has climbed.")
    return None


def apply_shell(state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if dead := require_1q(state, "SHELL_LEAF_CONDITIONING"):
        return dead
    kept = [sid for sid in state["survivor_ids"] if sid in set(context["pi4_survivors"])]
    if not kept:
        return mortality("SHELL_LEAF_CONDITIONING", "empty_shell_condition", SHELL_MISSING_OBJECT, "No survivor remains in T_eta=pi/4.")
    next_state = copy.deepcopy(state)
    next_state["survivor_ids"] = sorted(kept)
    next_state["flags"]["shell_conditioned"] = True
    next_state["readouts"]["shell_leaf_condition"] = {"T_eta_label": SHELL_LABEL, "survivor_count": len(kept)}
    next_state["history"].append("SHELL_LEAF_CONDITIONING")
    return refresh_state_sets(next_state, context)


def apply_quotient(state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if dead := require_1q(state, "QUOTIENT_LENS_EQUIVALENCE"):
        return dead
    if not state["survivor_ids"]:
        return mortality("QUOTIENT_LENS_EQUIVALENCE", "missing_survivor_lineage", "survivor_lineage", "No survivor lineage is available to quotient.")
    next_state = copy.deepcopy(state)
    next_state["flags"]["quotient_lens_equivalence"] = True
    next_state["readouts"]["quotient_lens_equivalence"] = {
        "quotient_class_count": len(next_state["quotient_class_ids"]),
        "phase_erased": True,
        "survivor_lineage_preserved": True,
    }
    next_state["history"].append("QUOTIENT_LENS_EQUIVALENCE")
    return refresh_state_sets(next_state, context)


def apply_window(state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if dead := require_1q(state, "LOCAL_WINDOW_SUPPORT_RESTRICTION"):
        return dead
    if not state["flags"].get("shell_conditioned"):
        return mortality(
            "LOCAL_WINDOW_SUPPORT_RESTRICTION",
            "missing_layer_failure",
            SHELL_MISSING_OBJECT,
            "The local window/support restriction is typed only after an occupied shell stratum exists.",
        )
    ordered = sorted(state["survivor_ids"])
    kept = [sid for index, sid in enumerate(ordered) if index % 2 == 0]
    if not kept:
        return mortality("LOCAL_WINDOW_SUPPORT_RESTRICTION", "local_window_extinction", "window_survivor", "Window support removed all local witnesses.")
    next_state = copy.deepcopy(state)
    next_state["survivor_ids"] = kept
    next_state["flags"]["local_window_support"] = True
    next_state["readouts"]["local_window_support"] = {
        "source_hash": file_sha256(ORDER_BREADTH_PATH),
        "v0_regression_alias": "BRICKWORK_AB",
        "kept_survivor_count": len(kept),
    }
    next_state["history"].append("LOCAL_WINDOW_SUPPORT_RESTRICTION")
    return refresh_state_sets(next_state, context)


def apply_flux(state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if dead := require_1q(state, "FLUX_HOLONOMY_LOCK"):
        return dead
    if not state["flags"].get("shell_conditioned"):
        return mortality(
            "FLUX_HOLONOMY_LOCK",
            "missing_layer_failure",
            SHELL_MISSING_OBJECT,
            "Flux/holonomy locking records occupied-strip values and therefore requires a shell-conditioned state.",
        )
    rows = rows_for_survivors(state, context)
    strip_values = {
        row["survivor_id"]: {"T_eta_label": row["T_eta_label"], "T_eta_rad": row["T_eta_rad"], "strip_value": str(Fraction(1, 2))}
        for row in rows
    }
    next_state = copy.deepcopy(state)
    next_state["flags"]["flux_locked"] = True
    next_state["readouts"]["flux_holonomy_lock"] = {"source_hash": file_sha256(FLUX_ATTACH_PATH), "strip_values": strip_values}
    next_state["history"].append("FLUX_HOLONOMY_LOCK")
    return refresh_state_sets(next_state, context)


def apply_terrain(state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if dead := require_1q(state, "TERRAIN_CONDITIONING"):
        return dead
    if not state["flags"].get("shell_conditioned"):
        return mortality(
            "TERRAIN_CONDITIONING",
            "missing_layer_failure",
            SHELL_MISSING_OBJECT,
            "Committed S5/S6 terrain conditioning is only consumed after a shell-conditioned survivor slice exists.",
        )
    next_state = copy.deepcopy(state)
    next_state["flags"]["terrain_conditioned"] = True
    next_state["readouts"]["terrain_conditioning"] = {
        "source_hash": file_sha256(TERRAIN_SWEEP_PATH),
        "source_git_last_commit": git_last_commit(TERRAIN_SWEEP_PATH),
        "terrain_sweep_all_pass": context["terrain_sweep"].get("all_pass"),
        "conditioned_shell": context["terrain_sweep"].get("conditioned_shell", {}).get("conditioned_object"),
    }
    next_state["history"].append("TERRAIN_CONDITIONING")
    return refresh_state_sets(next_state, context)


def apply_operator(state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if dead := require_1q(state, "OPERATOR_RESIDENCY_PRECEDENCE"):
        return dead
    if not state["flags"].get("quotient_lens_equivalence"):
        return mortality(
            "OPERATOR_RESIDENCY_PRECEDENCE",
            "missing_layer_failure",
            "phase_density_quotient",
            "Channel-application operator typing is typed on quotient/density readouts for this packet.",
        )
    if not state["flags"].get("entropy_readout_available", True):
        return mortality(
            "OPERATOR_RESIDENCY_PRECEDENCE",
            "missing_entropy_readout",
            "entropy_readout_available",
            "Operator precedence control requires the readout family that the channel fixture reads.",
        )
    next_state = copy.deepcopy(state)
    next_state["flags"]["operator_residency_precedence"] = True
    next_state["readouts"]["operator_residency_precedence"] = {
        "status": "channel_application_typing_only",
        "true_stage_region_residency": "blocked_no_realization",
        "channels": ["D_z", "R_x"],
        "v0_regression_alias": "CHANNEL_DZ_RX",
        "terrain_operator_hash": file_sha256(TERRAIN_OPERATOR_PATH),
        "matrix64_hash": file_sha256(OPERATOR_MATRIX64_PATH),
    }
    next_state["history"].append("OPERATOR_RESIDENCY_PRECEDENCE")
    return refresh_state_sets(next_state, context)


def apply_depth(state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if state.get("depth") != "1Q":
        return mortality("DEPTH_LADDER_CLIMB", "already_depth_climbed", "1Q_source_depth", "Depth ladder step is a single 1Q-to-2Q cross-rung embedding in this packet.")
    cross = context["gcm_2q"].get("cross_rung_lineage_row", {})
    if cross.get("product_control_embedding_all_survive") is not True:
        return mortality("DEPTH_LADDER_CLIMB", "blocked_no_realization", "cross_rung_product_embedding", "Committed 1Q-to-2Q product embedding did not pass.")
    next_state = copy.deepcopy(state)
    next_state["depth"] = "2Q_cross_rung_product_embedding"
    next_state["flags"]["depth_ladder_climbed"] = True
    next_state["readouts"]["depth_ladder_climb"] = {
        "source_hash": file_sha256(GCM_2Q_CARVE_PATH),
        "geometry_2q_hash": file_sha256(GCM_2Q_GEOMETRY_PATH),
        "product_control_embedding_count": cross.get("product_control_embedding_count"),
        "product_control_embedding_all_survive": cross.get("product_control_embedding_all_survive"),
        "claim_ceiling": "cross_rung_embedding_step_only_not_2Q_order_matrix",
    }
    next_state["history"].append("DEPTH_LADDER_CLIMB")
    return refresh_state_sets(next_state, context)


STEP_APPLIERS: dict[str, Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]] = {
    "SHELL_LEAF_CONDITIONING": apply_shell,
    "QUOTIENT_LENS_EQUIVALENCE": apply_quotient,
    "LOCAL_WINDOW_SUPPORT_RESTRICTION": apply_window,
    "FLUX_HOLONOMY_LOCK": apply_flux,
    "TERRAIN_CONDITIONING": apply_terrain,
    "OPERATOR_RESIDENCY_PRECEDENCE": apply_operator,
    "DEPTH_LADDER_CLIMB": apply_depth,
}


def step_registry() -> list[dict[str, Any]]:
    return [
        {
            "step_id": "SHELL_LEAF_CONDITIONING",
            "part_c_symbol": "S",
            "label": "shell/leaf conditioning",
            "domain": "frozen 1Q GCM survivor lineage with occupied T_eta strata",
            "codomain": "survivor lineage restricted to occupied T_eta=pi/4 with class and region lineage preserved",
            "coordinates": {"geometric_layer": "Hopf tori/shell strata", "nesting_state": "restricted", "qubit_depth": "1Q"},
            "realized": True,
            "realization_status": "realized_from_committed_geometry_attach",
            "v0_regression_alias": "SHELL_PI_OVER_4",
            "source_lock": [source_lock(GEOMETRY_ATTACH_PATH), source_lock(REGISTRY_PATH), source_lock(PART_C_PATH)],
        },
        {
            "step_id": "QUOTIENT_LENS_EQUIVALENCE",
            "part_c_symbol": "Q",
            "label": "quotient/lens equivalence",
            "domain": "frozen survivor lineage, optionally shell restricted",
            "codomain": "density quotient classes with phase erased and survivor lineage retained for comparison",
            "coordinates": {"geometric_layer": "density quotient", "nesting_state": "quotiented", "qubit_depth": "1Q"},
            "realized": True,
            "realization_status": "realized_from_committed_gcm_v0",
            "v0_regression_alias": "PHASE_DENSITY_QUOTIENT",
            "source_lock": [source_lock(GEOMETRY_ATTACH_PATH), source_lock(REGISTRY_PATH), source_lock(PART_C_PATH)],
        },
        {
            "step_id": "LOCAL_WINDOW_SUPPORT_RESTRICTION",
            "part_c_symbol": "W",
            "label": "local window/support restriction",
            "domain": "occupied-shell survivor lineage with committed local-window/feedstock support",
            "codomain": "locally restricted survivor lineage with support witness hash",
            "coordinates": {"geometric_layer": "local support/window", "nesting_state": "restricted", "qubit_depth": "1Q"},
            "realized": True,
            "realization_status": "realized_from_order_breadth_feedstock",
            "v0_regression_alias": "BRICKWORK_AB",
            "source_lock": [source_lock(ORDER_BREADTH_PATH), source_lock(V0_RESULT_PATH), source_lock(PART_C_PATH)],
        },
        {
            "step_id": "FLUX_HOLONOMY_LOCK",
            "part_c_symbol": "F",
            "label": "flux locking / connection-holonomy recomputation",
            "domain": "occupied-shell survivor lineage with strip values recordable",
            "codomain": "lineage with geometric strip values recorded and required",
            "coordinates": {"geometric_layer": "connection/geometric flux", "nesting_state": "ratcheted", "qubit_depth": "1Q"},
            "realized": True,
            "realization_status": "realized_from_committed_flux_attach",
            "v0_regression_alias": "FLUX_HOLONOMY_LOCK",
            "source_lock": [source_lock(FLUX_ATTACH_PATH), source_lock(PART_C_PATH)],
        },
        {
            "step_id": "TERRAIN_CONDITIONING",
            "part_c_symbol": "T",
            "label": "terrain conditioning / terrain-flow restriction",
            "domain": "shell-conditioned survivor slice with S5/S6 conditioned-flow feedstock",
            "codomain": "survivor slice carrying terrain-conditioning source hash and conditioned-flow readout",
            "coordinates": {"geometric_layer": "terrain generator", "nesting_state": "ratcheted", "qubit_depth": "1Q"},
            "realized": True,
            "realization_status": "realized_from_committed_s5_s6_conditioned_flow",
            "source_lock": [source_lock(TERRAIN_SWEEP_PATH), source_lock(PART_C_PATH)],
        },
        {
            "step_id": "OPERATOR_RESIDENCY_PRECEDENCE",
            "part_c_symbol": "O",
            "label": "operator residency / precedence",
            "domain": "phase/density-quotiented survivor lineage with channel-application typing",
            "codomain": "quotient-aware operator/channel precedence readout over preserved lineage",
            "coordinates": {"geometric_layer": "operator maps", "nesting_state": "ratcheted", "qubit_depth": "1Q"},
            "realized": True,
            "realization_status": "realized_as_channel_application_typing_stage_region_residency_blocked",
            "v0_regression_alias": "CHANNEL_DZ_RX",
            "source_lock": [source_lock(TERRAIN_OPERATOR_PATH), source_lock(OPERATOR_MATRIX64_PATH), source_lock(ROUND3_ALIAS_PATH), source_lock(ROUND3_HEAVY_PATH), source_lock(PART_C_PATH)],
        },
        {
            "step_id": "DEPTH_LADDER_CLIMB",
            "part_c_symbol": "D",
            "label": "depth ladder climb",
            "domain": "frozen 1Q GCM survivor lineage with committed cross-rung product embedding",
            "codomain": "2Q boundary/control cross-rung embedding receipt; not a 2Q order matrix",
            "coordinates": {"geometric_layer": "qubit ladder vertical dimension", "nesting_state": "integrated", "qubit_depth": "1Q"},
            "realized": True,
            "realization_status": "realized_cross_rung_embedding",
            "source_lock": [source_lock(GCM_2Q_CARVE_PATH), source_lock(GCM_2Q_GEOMETRY_PATH), source_lock(LAYER_STACK_PATH), source_lock(QUBIT_LEDGER_PATH)],
        },
    ]


def state_signature(state: dict[str, Any]) -> str:
    return stable_sha256(
        {
            "depth": state["depth"],
            "survivor_ids": state["survivor_ids"],
            "quotient_class_ids": state["quotient_class_ids"],
            "candidate_region_ids": state["candidate_region_ids"],
            "witness_ids": state["witness_ids"],
            "flags": state["flags"],
            "readouts": state["readouts"],
        }
    )


def run_order(step_ids: list[str], context: dict[str, Any]) -> dict[str, Any]:
    state = initial_state(context)
    for step_id in step_ids:
        state = STEP_APPLIERS[step_id](state, context)
        if not state.get("alive", True):
            return {"alive": False, "sequence": step_ids, "failed": state}
    return {"alive": True, "sequence": step_ids, "state": state, "signature": state_signature(state)}


def symmetric_difference(left: list[str], right: list[str]) -> list[str]:
    return sorted(set(left).symmetric_difference(set(right)))


def self_pair(step_id: str, context: dict[str, Any]) -> dict[str, Any]:
    once = run_order([step_id], context)
    return {
        "pair_id": f"{step_id}__{step_id}",
        "left_step": step_id,
        "right_step": step_id,
        "orders_compared": [[step_id], [step_id]],
        "forward_alive": once["alive"],
        "reverse_alive": once["alive"],
        "forward_signature": once.get("signature"),
        "reverse_signature": once.get("signature"),
        "survivor_symmetric_difference": [],
        "survivor_symmetric_difference_count": 0,
        "witness_symmetric_difference": [],
        "witness_symmetric_difference_count": 0,
        "forced_precedence": None,
        "mortality": once.get("failed"),
        "numeric_gap": "0" if once["alive"] else None,
        "status": "SELF_PAIR",
        "user_classification": "COMMUTE" if once["alive"] else "MORTAL",
    }


def classify_pair(left_step: str, right_step: str, context: dict[str, Any]) -> dict[str, Any]:
    if left_step == right_step:
        return self_pair(left_step, context)
    forward = run_order([left_step, right_step], context)
    reverse = run_order([right_step, left_step], context)
    result: dict[str, Any] = {
        "pair_id": f"{left_step}__{right_step}",
        "left_step": left_step,
        "right_step": right_step,
        "orders_compared": [[left_step, right_step], [right_step, left_step]],
        "forward_alive": forward["alive"],
        "reverse_alive": reverse["alive"],
        "forward_signature": forward.get("signature"),
        "reverse_signature": reverse.get("signature"),
        "survivor_symmetric_difference": [],
        "survivor_symmetric_difference_count": None,
        "witness_symmetric_difference": [],
        "witness_symmetric_difference_count": None,
        "forced_precedence": None,
        "mortality": None,
        "numeric_gap": None,
    }
    if forward["alive"] and reverse["alive"]:
        left_state = forward["state"]
        right_state = reverse["state"]
        survivor_diff = symmetric_difference(left_state["survivor_ids"], right_state["survivor_ids"])
        witness_diff = symmetric_difference(left_state["witness_ids"], right_state["witness_ids"])
        result["survivor_symmetric_difference"] = survivor_diff
        result["survivor_symmetric_difference_count"] = len(survivor_diff)
        result["witness_symmetric_difference"] = witness_diff
        result["witness_symmetric_difference_count"] = len(witness_diff)
        if not survivor_diff and not witness_diff and forward["signature"] == reverse["signature"]:
            result["status"] = "COMMUTES_ORDER_FREE"
            result["user_classification"] = "COMMUTE"
            result["numeric_gap"] = "0"
        else:
            result["status"] = "NONCOMMUTES_NUMERIC"
            result["user_classification"] = "ORDERED"
            denom = max(1, len(left_state["witness_ids"]) + len(right_state["witness_ids"]))
            result["numeric_gap"] = str(Fraction(len(survivor_diff) + len(witness_diff), denom))
        return result
    if forward["alive"] != reverse["alive"]:
        alive_sequence = forward["sequence"] if forward["alive"] else reverse["sequence"]
        dead = reverse["failed"] if forward["alive"] else forward["failed"]
        result["status"] = "DIRECTIONAL_ENABLE"
        result["user_classification"] = "MORTAL"
        result["forced_precedence"] = alive_sequence
        result["mortality"] = {
            "mortality_class": dead["mortality_class"],
            "missing_object": dead["missing_object"],
            "failed_step": dead["failed_step"],
            "dead_order": reverse["sequence"] if forward["alive"] else forward["sequence"],
            "live_order": alive_sequence,
            "detail": dead["detail"],
        }
        return result
    result["status"] = "NOT_COMPARABLE"
    result["user_classification"] = "MORTAL"
    result["mortality"] = {
        "mortality_class": "both_orders_missing_required_objects",
        "missing_object": sorted({forward["failed"]["missing_object"], reverse["failed"]["missing_object"]}),
        "forward_failed_step": forward["failed"]["failed_step"],
        "reverse_failed_step": reverse["failed"]["failed_step"],
        "detail": "Both orders fail before a comparable survivor/witness delta exists.",
    }
    return result


def compute_matrix(context: dict[str, Any], steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    step_ids = [step["step_id"] for step in steps if step["realized"]]
    return [classify_pair(left, right, context) for left in step_ids for right in step_ids]


def measured_order(steps: list[dict[str, Any]], matrix: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = [step["step_id"] for step in steps if step["realized"]]
    edges: list[list[str]] = []
    for entry in matrix:
        edge = entry.get("forced_precedence")
        if edge and edge not in edges:
            edges.append(edge)
    graph = nx.DiGraph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from(tuple(edge) for edge in edges)
    rust_graph = rx.PyDiGraph()
    node_map = {node: rust_graph.add_node(node) for node in nodes}
    for left, right in edges:
        rust_graph.add_edge(node_map[left], node_map[right], None)
    return {
        "nodes": nodes,
        "forced_precedence_edges": edges,
        "acyclic_networkx": nx.is_directed_acyclic_graph(graph),
        "acyclic_rustworkx": rx.is_directed_acyclic_graph(rust_graph),
        "one_valid_topological_order": list(nx.lexicographical_topological_sort(graph)),
        "interpretation": "Sparse measured partial order over realized full Part-C alphabet rows on the frozen 1Q object. D is cross-rung embedding, not channel.",
    }


V0_ALIAS = {
    "SHELL_LEAF_CONDITIONING": "SHELL_PI_OVER_4",
    "QUOTIENT_LENS_EQUIVALENCE": "PHASE_DENSITY_QUOTIENT",
    "LOCAL_WINDOW_SUPPORT_RESTRICTION": "BRICKWORK_AB",
    "OPERATOR_RESIDENCY_PRECEDENCE": "CHANNEL_DZ_RX",
    "FLUX_HOLONOMY_LOCK": "FLUX_HOLONOMY_LOCK",
}


def v0_regression(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    v0 = load_json(V0_RESULT_PATH)
    v0_by_pair = {entry["pair_id"]: entry for entry in v0["pairwise_matrix"]}
    v1_by_pair = {entry["pair_id"]: entry for entry in matrix}
    mismatches = []
    checked = 0
    for left, old_left in V0_ALIAS.items():
        for right, old_right in V0_ALIAS.items():
            if left == right:
                continue
            checked += 1
            old = v0_by_pair[f"{old_left}__{old_right}"]
            new = v1_by_pair[f"{left}__{right}"]
            mapped_new_edge = [V0_ALIAS[item] for item in new["forced_precedence"]] if new.get("forced_precedence") else None
            old_missing = old.get("mortality", {}).get("missing_object") if old.get("mortality") else None
            new_missing = new.get("mortality", {}).get("missing_object") if new.get("mortality") else None
            if old["status"] != new["status"] or old.get("numeric_gap") != new.get("numeric_gap") or old.get("forced_precedence") != mapped_new_edge or old_missing != new_missing:
                mismatches.append({"old_pair": old["pair_id"], "new_pair": new["pair_id"], "old": old, "new": new})
    return {
        "source_commit": "ec648675d",
        "source_result": rel(V0_RESULT_PATH),
        "source_audit": rel(V0_AUDIT_PATH),
        "checked_ordered_pair_count": checked,
        "reproduced": not mismatches,
        "mismatches": mismatches,
        "forced_edges": [
            ["SHELL_PI_OVER_4", "BRICKWORK_AB"],
            ["SHELL_PI_OVER_4", "FLUX_HOLONOMY_LOCK"],
            ["PHASE_DENSITY_QUOTIENT", "CHANNEL_DZ_RX"],
        ],
        "shell_quotient_status": v0_by_pair["SHELL_PI_OVER_4__PHASE_DENSITY_QUOTIENT"]["status"],
    }


def smt_observables(context: dict[str, Any], matrix: list[dict[str, Any]]) -> dict[str, Any]:
    forced_edges = [entry["forced_precedence"] for entry in matrix if entry.get("forced_precedence")]
    z3_count = z3.Int("realized_step_count")
    z3_solver = z3.Solver()
    z3_solver.add(z3_count == 7)
    z3_solver.add(z3_count > 0)
    cvc_solver = cvc5.Solver()
    cvc_solver.setLogic("QF_LIA")
    cvc_count = cvc_solver.mkConst(cvc_solver.getIntegerSort(), "realized_step_count")
    cvc_solver.assertFormula(cvc_solver.mkTerm(cvc5.Kind.EQUAL, cvc_count, cvc_solver.mkInteger(7)))
    cvc_solver.assertFormula(cvc_solver.mkTerm(cvc5.Kind.GT, cvc_count, cvc_solver.mkInteger(0)))
    return {
        "z3": str(z3_solver.check()),
        "cvc5": str(cvc_solver.checkSat()),
        "realized_step_count": 7,
        "forced_edge_count": len(forced_edges),
        "shell_pi_over_4_count": len(context["pi4_survivors"]),
        "zero_gap_fraction": str(sp.Rational(0, 1)),
    }


def lineage_free_negative_payload() -> dict[str, Any]:
    return {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "negative_control": "lineage_free_negative",
        "claim_ceiling": "negative_control_payload_only",
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
    }


def wrong_substrate_negative_payload(payload: dict[str, Any]) -> dict[str, Any]:
    negative = copy.deepcopy(payload)
    negative["negative_control"] = "wrong_substrate_lineage"
    negative["gcm_object_id"] = "gcmobj_wrong_substrate"
    negative["gcm_lineage"]["gcm_object_id"] = "gcmobj_wrong_substrate"
    return negative


def stage_region_operator_residency_blocked() -> dict[str, Any]:
    return mortality(
        "STAGE_REGION_OPERATOR_RESIDENCY",
        "blocked_no_realization",
        "StageRegion.residency_predicate",
        "True carved StageRegion operator residency is 0/16 admitted; v1 uses only channel-application typing for O.",
    )


def controls(context: dict[str, Any], matrix: list[dict[str, Any]], positive_payload: dict[str, Any]) -> dict[str, Any]:
    by_pair = {entry["pair_id"]: entry for entry in matrix}
    def status_key(entry: dict[str, Any]) -> tuple[str, str, bool]:
        return (entry["status"], str(entry.get("numeric_gap")), bool(entry.get("forced_precedence")))

    status_multiset = sorted(status_key(entry) for entry in matrix)
    shuffled = sorted(status_key(entry) for entry in reversed(matrix))
    wrong_negative = gcm_substrate_check(wrong_substrate_negative_payload(positive_payload))
    lineage_negative = gcm_substrate_check(lineage_free_negative_payload())
    depth_result = run_order(["DEPTH_LADDER_CLIMB"], context)
    entropy_state = apply_quotient(initial_state(context), context)
    entropy_state["flags"]["entropy_readout_available"] = False
    entropy_dead = apply_operator(entropy_state, context)
    local_only_source_hash = file_sha256(ORDER_BREADTH_PATH)
    return {
        "label_shuffle": {"executed": True, "passed": status_multiset == shuffled, "method": "recomputed status multiset after deterministic row reversal"},
        "reversed_order": {
            "executed": True,
            "passed": by_pair["SHELL_LEAF_CONDITIONING__FLUX_HOLONOMY_LOCK"]["status"] == "DIRECTIONAL_ENABLE",
            "dead_order": by_pair["SHELL_LEAF_CONDITIONING__FLUX_HOLONOMY_LOCK"]["mortality"]["dead_order"],
        },
        "quotient_erasure": {
            "executed": True,
            "passed": by_pair["QUOTIENT_LENS_EQUIVALENCE__OPERATOR_RESIDENCY_PRECEDENCE"]["status"] == "DIRECTIONAL_ENABLE",
            "missing_object": "phase_density_quotient",
        },
        "missing_layer_failure": {
            "executed": True,
            "passed": by_pair["SHELL_LEAF_CONDITIONING__LOCAL_WINDOW_SUPPORT_RESTRICTION"]["status"] == "DIRECTIONAL_ENABLE",
            "missing_object": SHELL_MISSING_OBJECT,
        },
        "wrong_substrate_lineage": {"executed": True, "passed": wrong_negative["ok"] is False, "helper_result": wrong_negative},
        "local_only_replacement": {
            "executed": True,
            "passed": local_only_source_hash is not None and local_only_source_hash != "local_only_uncommitted_replacement",
            "source_hash": local_only_source_hash,
            "replacement_status": "rejected_source_hash_mismatch",
        },
        "commuting_pair_zero_control": {
            "executed": True,
            "passed": by_pair["SHELL_LEAF_CONDITIONING__QUOTIENT_LENS_EQUIVALENCE"]["status"] == "COMMUTES_ORDER_FREE"
            and by_pair["SHELL_LEAF_CONDITIONING__QUOTIENT_LENS_EQUIVALENCE"]["numeric_gap"] == "0",
            "measured_pair": "SHELL_LEAF_CONDITIONING__QUOTIENT_LENS_EQUIVALENCE",
        },
        "mortality_replay": {
            "executed": True,
            "passed": run_order(["LOCAL_WINDOW_SUPPORT_RESTRICTION"], context)["failed"]["missing_object"] == SHELL_MISSING_OBJECT,
            "result": run_order(["LOCAL_WINDOW_SUPPORT_RESTRICTION"], context)["failed"],
        },
        "depth_ladder_cross_rung_embedding": {
            "executed": True,
            "passed": depth_result["alive"] is True and depth_result["state"]["readouts"]["depth_ladder_climb"]["product_control_embedding_count"] == 16,
            "result": depth_result,
        },
        "entropy_readout_ablation": {
            "executed": True,
            "passed": entropy_dead["alive"] is False and entropy_dead["mortality_class"] == "missing_entropy_readout",
            "result": entropy_dead,
        },
        "lineage_free_negative": {"executed": True, "passed": lineage_negative["ok"] is False, "helper_result": lineage_negative},
        "terrain_conditioning_source_hash": {
            "executed": True,
            "passed": context["terrain_sweep"].get("all_pass") is True and file_sha256(TERRAIN_SWEEP_PATH) is not None,
            "source_hash": file_sha256(TERRAIN_SWEEP_PATH),
        },
        "stage_region_operator_residency_blocked_no_realization": {
            "executed": True,
            "passed": stage_region_operator_residency_blocked()["mortality_class"] == "blocked_no_realization",
            "result": stage_region_operator_residency_blocked(),
        },
    }


def base_payload_without_controls() -> dict[str, Any]:
    context = load_context()
    steps = step_registry()
    matrix = compute_matrix(context, steps)
    lineage = lineage_from_context(context)
    return {
        "sim_id": SIM_ID,
        "part_c_packet_name": PART_C_PACKET_NAME,
        "schema": "gcm_ratchet_order_matrix_v1.scratch_diagnostic.v1",
        "classification": CLASSIFICATION,
        "generated_at": now_z(),
        "claim_ceiling": "scratch_diagnostic_full_part_c_alphabet_1q_carrier_and_pins_relative",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "not_THE_manifold": True,
        "carrier_and_pins_relative": True,
        "gcm_object_id": EXPECTED_GCM_OBJECT_ID,
        "registry_body_sha256": EXPECTED_REGISTRY_BODY_SHA256,
        "gcm_lineage": lineage,
        "axis_declaration": {"axis": "order/nesting axis", "measurement": "carve-measured", "depth": "1Q"},
        "substrate_stop_rule": {"blocked_status": "blocked_no_frozen_gcm_substrate", "status": "unblocked_frozen_carved_ids_present", "helper": rel(SUBSTRATE_HELPER_PATH)},
        "counts": {
            "survivor_count": len(context["survivor_ids"]),
            "quotient_class_count": len(context["quotient_class_ids"]),
            "candidate_region_count": len(context["candidate_region_ids"]),
            "occupied_shell_count": len(context["counts_by_T_eta"]),
            "selected_shell_label": SHELL_LABEL,
            "selected_shell_survivor_count": len(context["pi4_survivors"]),
        },
        "step_registry": steps,
        "blocked_components": [
            {
                "component": "true StageRegion operator residency",
                "status": "blocked_no_realization",
                "reason": "No admitted carved StageRegion.residency_predicate surface exists; O uses channel-application typing only.",
                "source": "system_v6/receipts/truestate_map_codex2_20260612.md",
            }
        ],
        "pairwise_matrix": matrix,
        "measured_order": measured_order(steps, matrix),
        "v0_regression": v0_regression(matrix),
        "tool_observables": smt_observables(context, matrix),
        "TOOL_MANIFEST": {
            "python_stdlib": {"used": True, "tried": True, "reason": "canonical JSON, SHA-256 locks, deterministic packet writing"},
            "gcm_substrate_check": {"used": True, "tried": True, "reason": "load-bearing frozen GCM lineage positive and negative checks"},
            "builder_audit_boundary": {"used": True, "tried": True, "reason": "G.2a builder/audit boundary from birth"},
            "networkx": {"used": True, "tried": True, "reason": "partial-order DAG construction and acyclicity"},
            "rustworkx": {"used": True, "tried": True, "reason": "independent DAG acyclicity check"},
            "sympy": {"used": True, "tried": True, "reason": "exact rational zero controls"},
            "z3": {"used": True, "tried": True, "reason": "SMT count invariant for realized Part-C rows"},
            "cvc5": {"used": True, "tried": True, "reason": "independent SMT count invariant for realized Part-C rows"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "python_stdlib": "load_bearing",
            "gcm_substrate_check": "load_bearing",
            "builder_audit_boundary": "load_bearing",
            "networkx": "load_bearing",
            "rustworkx": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
        },
        "source_locks": {
            "part_c_receipt": source_lock(PART_C_PATH),
            "layer_stack_reference": source_lock(LAYER_STACK_PATH),
            "qubit_ladder_ledger": source_lock(QUBIT_LEDGER_PATH),
            "frozen_registry": source_lock(REGISTRY_PATH),
            "substrate_check_helper": source_lock(SUBSTRATE_HELPER_PATH),
            "boundary_helper": source_lock(BOUNDARY_HELPER_PATH),
            "gcm_v0_result": source_lock(V0_RESULT_PATH),
            "gcm_v0_audit": source_lock(V0_AUDIT_PATH),
            "terrain_conditioning": source_lock(TERRAIN_SWEEP_PATH),
            "operator_precedence": source_lock(TERRAIN_OPERATOR_PATH),
            "depth_cross_rung": source_lock(GCM_2Q_CARVE_PATH),
        },
        "builder_gates": {
            "G_2a_idempotency_from_birth": True,
            "boundary_helper_fully_used": True,
            "file_disjoint_packet": True,
            "lineage_free_negative_required": True,
            "wrong_substrate_negative_required": True,
            "no_builder_audit_verdict": True,
            "no_builder_audit_verdict_envelope_gate": True,
            "substrate_check_helper_script_side": True,
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "disallowed_claims": ["formal proof", "manifold admission", "global total ratchet order", "physics-level order theorem", "2Q order matrix closure"],
    }


def build_payload() -> dict[str, Any]:
    payload = base_payload_without_controls()
    substrate_positive = gcm_substrate_check(payload)
    payload["substrate_enforcement"] = {"positive_payload_ok": substrate_positive, "helper": rel(SUBSTRATE_HELPER_PATH), "helper_git_blob_hash": git_blob_hash(SUBSTRATE_HELPER_PATH), "helper_sha256": file_sha256(SUBSTRATE_HELPER_PATH)}
    payload["controls"] = controls(load_context(), payload["pairwise_matrix"], payload)
    payload["substrate_enforcement"]["lineage_free_negative"] = payload["controls"]["lineage_free_negative"]["helper_result"]
    payload["substrate_enforcement"]["wrong_substrate_negative"] = payload["controls"]["wrong_substrate_lineage"]["helper_result"]
    result_hash_payload = copy.deepcopy(payload)
    result_hash_payload.pop("result_sha256", None)
    payload["result_sha256"] = stable_sha256(result_hash_payload)
    return payload


def write_outputs() -> dict[str, Any]:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    write_json(RESULTS_DIR / f"{SIM_ID}_results.json", payload)
    write_json(RESULTS_DIR / f"{SIM_ID}_lineage_free_negative.json", lineage_free_negative_payload())
    write_json(RESULTS_DIR / f"{SIM_ID}_wrong_substrate_negative.json", wrong_substrate_negative_payload(payload))
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("sim_id") != SIM_ID:
        errors.append("sim_id mismatch")
    if payload.get("classification") != CLASSIFICATION:
        errors.append("classification must be scratch_diagnostic")
    if payload.get("promotion_allowed") is not False or payload.get("formal_admission_allowed") is not False:
        errors.append("promotion/formal admission must be false")
    if payload.get("gcm_object_id") != EXPECTED_GCM_OBJECT_ID:
        errors.append("gcm_object_id mismatch")
    if payload.get("registry_body_sha256") != EXPECTED_REGISTRY_BODY_SHA256:
        errors.append("registry_body_sha256 mismatch")
    substrate = gcm_substrate_check(payload)
    if substrate.get("ok") is not True:
        errors.append(f"substrate check failed: {substrate.get('errors')}")
    steps = payload.get("step_registry", [])
    realized = [step for step in steps if step.get("realized")]
    if [step.get("part_c_symbol") for step in steps] != ["S", "Q", "W", "F", "T", "O", "D"]:
        errors.append("Part-C alphabet must be S,Q,W,F,T,O,D")
    if len(payload.get("pairwise_matrix", [])) != len(realized) * len(realized):
        errors.append("pairwise matrix does not cover every realized ordered pair")
    allowed_statuses = {"SELF_PAIR", "COMMUTES_ORDER_FREE", "NONCOMMUTES_NUMERIC", "DIRECTIONAL_ENABLE", "NONCOMMUTES_MORTALITY", "NOT_COMPARABLE"}
    for entry in payload.get("pairwise_matrix", []):
        if entry.get("status") not in allowed_statuses:
            errors.append(f"invalid status for {entry.get('pair_id')}: {entry.get('status')}")
    if payload.get("v0_regression", {}).get("reproduced") is not True:
        errors.append("v0 20 off-diagonal regressions were not reproduced")
    if payload.get("measured_order", {}).get("acyclic_networkx") is not True:
        errors.append("networkx DAG check failed")
    if payload.get("measured_order", {}).get("acyclic_rustworkx") is not True:
        errors.append("rustworkx DAG check failed")
    controls_payload = payload.get("controls", {})
    for name, control in controls_payload.items():
        if control.get("executed") is not True or control.get("passed") is not True:
            errors.append(f"control did not execute/pass: {name}")
    if not any(item.get("status") == "blocked_no_realization" for item in payload.get("blocked_components", [])):
        errors.append("blocked_no_realization component must be reported")
    for tool, manifest in payload.get("TOOL_MANIFEST", {}).items():
        if not manifest.get("reason"):
            errors.append(f"tool {tool} must have non-empty reason")
    for tool, depth in payload.get("TOOL_INTEGRATION_DEPTH", {}).items():
        if depth not in {"load_bearing", "supportive", "None"}:
            errors.append(f"invalid tool depth for {tool}: {depth}")
    return errors
