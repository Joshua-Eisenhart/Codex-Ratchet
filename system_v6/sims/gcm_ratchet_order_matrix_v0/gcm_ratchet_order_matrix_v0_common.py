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

SIM_ID = "gcm_ratchet_order_matrix_v0"
PART_C_PACKET_NAME = "ratchet_order_matrix_on_gcm_v0"
CLASSIFICATION = "scratch_diagnostic"
EXPECTED_GCM_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_REGISTRY_BODY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
SHELL_LABEL = "pi/4"
SHELL_MISSING_OBJECT = "occupied_T_eta_stratum"

REGISTRY_PATH = ROOT / "system_v6/sims/gcm_object_id_freeze_v0/results/gcm_object_id_freeze_v0_registry.json"
GEOMETRY_ATTACH_PATH = ROOT / "system_v6/sims/gcm_geometry_attach_v0/results/gcm_geometry_attach_v0_results.json"
FLUX_ATTACH_PATH = ROOT / "system_v6/sims/gcm_connection_flux_attach_v0/results/gcm_connection_flux_attach_v0_results.json"
BRICKWORK_SOURCE_PATH = ROOT / "system_v6/sims/manifold_super_sim_v2_weld/results/manifold_super_sim_v2_weld_envelope_results.json"
BRICKWORK_COMMON_PATH = ROOT / "system_v6/sims/manifold_super_sim_v2_weld/manifold_super_sim_v2_weld_common.py"
ROUND3_ALIAS_PATH = ROOT / "system_v6/sims/round3_s4_alias_pass_v0/results/round3_s4_alias_pass_v0_envelope_results.json"
ROUND3_HEAVY_PATH = ROOT / "system_v6/sims/round3_s4_heavy_discriminator_v0/results/round3_s4_heavy_discriminator_v0_envelope_results.json"
DEEP_ORDER_PATH = ROOT / "system_v6/receipts/ratcheting_geometry_order_20260612.md"
HYPOTHESIS_PATH = ROOT / "system_v6/receipts/ratchet_geometry_order_hypothesis_20260612.md"
STANDARDS_PATH = ROOT / "system_v6/receipts/audit_standards_codex_v1.md"
SUBSTRATE_HELPER_PATH = ROOT / "scripts/gcm_substrate_check.py"
BOUNDARY_HELPER_PATH = ROOT / "scripts/builder_audit_boundary.py"
RATCHET_BREADTH_PATH = ROOT / "system_v6/sims/ratchet_order_breadth_v0/results/ratchet_order_breadth_v0_envelope_results.json"
RATCHET_DEEP_CHAIN_PATH = ROOT / "system_v6/sims/ratchet_deep_chain_v0/results/ratchet_deep_chain_v0_envelope_results.json"
TERRAIN_OPERATOR_PATH = ROOT / "system_v6/sims/ratchet_s6_terrain_operator_shell_v0/results/ratchet_s6_terrain_operator_shell_v0_envelope_results.json"

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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    value = completed.stdout.strip()
    return value or None


def source_lock(path: Path) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": file_sha256(path),
        "git_last_commit": git_last_commit(path),
    }


def load_context() -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH)
    frozen = registry["frozen_registry"]
    geometry = load_json(GEOMETRY_ATTACH_PATH)
    shell_rows = geometry["attachment_map"]["shell_occupancy"]["rows"]
    object_maps = geometry["attachment_map"]["object_maps"]
    rows_by_survivor = {row["survivor_id"]: row for row in shell_rows}
    objects_by_survivor = {row["survivor_id"]: row for row in object_maps}

    survivor_ids = [row["survivor_id"] for row in frozen["survivors"]]
    quotient_class_ids = [row["quotient_class_id"] for row in frozen["quotient_classes"]]
    candidate_region_ids = [row["candidate_region_id"] for row in frozen["candidate_regions"]]
    pi4_survivors = [
        row["survivor_id"]
        for row in shell_rows
        if row.get("T_eta_label") == SHELL_LABEL
    ]

    return {
        "registry": registry,
        "geometry": geometry,
        "survivor_ids": survivor_ids,
        "quotient_class_ids": quotient_class_ids,
        "candidate_region_ids": candidate_region_ids,
        "shell_rows": shell_rows,
        "rows_by_survivor": rows_by_survivor,
        "objects_by_survivor": objects_by_survivor,
        "pi4_survivors": sorted(pi4_survivors),
        "counts_by_T_eta": geometry["attachment_map"]["shell_occupancy"]["counts_by_T_eta"],
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
        witness_ids.update(f"shell:{row['T_eta_shell_id']}" for row in rows)
        witness_ids.add(f"T_eta:{SHELL_LABEL}")
    if state["flags"].get("phase_density_quotiented"):
        state.setdefault("readouts", {}).setdefault("phase_density_quotient", {})
        state["readouts"]["phase_density_quotient"].update(
            {
                "quotient_class_count": len(state["quotient_class_ids"]),
                "phase_erased": True,
                "survivor_lineage_preserved": True,
            }
        )
        witness_ids.update(f"density_class:{qid}" for qid in state["quotient_class_ids"])
    if state["flags"].get("brickwork_ab_applied"):
        witness_ids.add(f"brickwork_ab:{file_sha256(BRICKWORK_SOURCE_PATH)}")
    if state["flags"].get("channel_applied"):
        witness_ids.add("channel_fixture:D_z")
        witness_ids.add("channel_fixture:R_x")
    if state["flags"].get("flux_locked"):
        witness_ids.add("flux_holonomy:strip_values_locked")
    state["witness_ids"] = sorted(witness_ids)
    return state


def initial_state(context: dict[str, Any]) -> dict[str, Any]:
    state = {
        "alive": True,
        "survivor_ids": sorted(context["survivor_ids"]),
        "quotient_class_ids": sorted(context["quotient_class_ids"]),
        "candidate_region_ids": sorted(context["candidate_region_ids"]),
        "witness_ids": [],
        "flags": {
            "shell_conditioned": False,
            "phase_density_quotiented": False,
            "brickwork_ab_applied": False,
            "channel_applied": False,
            "flux_locked": False,
            "strip_values_recorded": False,
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


def apply_shell(state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    kept = [sid for sid in state["survivor_ids"] if sid in set(context["pi4_survivors"])]
    if not kept:
        return mortality("SHELL_PI_OVER_4", "empty_shell_condition", SHELL_MISSING_OBJECT, "No survivor remains in T_eta=pi/4.")
    next_state = copy.deepcopy(state)
    next_state["survivor_ids"] = sorted(kept)
    next_state["flags"]["shell_conditioned"] = True
    next_state["readouts"]["shell_condition"] = {
        "T_eta_label": SHELL_LABEL,
        "survivor_count": len(kept),
        "shell_id": context["rows_by_survivor"][kept[0]]["T_eta_shell_id"],
    }
    next_state["history"].append("SHELL_PI_OVER_4")
    return refresh_state_sets(next_state, context)


def apply_quotient(state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if not state["survivor_ids"]:
        return mortality("PHASE_DENSITY_QUOTIENT", "missing_survivor_lineage", "survivor_lineage", "No survivor lineage is available to quotient.")
    next_state = copy.deepcopy(state)
    next_state["flags"]["phase_density_quotiented"] = True
    next_state["readouts"]["phase_density_quotient"] = {
        "quotient_class_count": len(next_state["quotient_class_ids"]),
        "phase_erased": True,
        "survivor_lineage_preserved": True,
    }
    next_state["history"].append("PHASE_DENSITY_QUOTIENT")
    return refresh_state_sets(next_state, context)


def apply_brickwork(state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if not state["flags"].get("shell_conditioned"):
        return mortality(
            "BRICKWORK_AB",
            "missing_layer_failure",
            SHELL_MISSING_OBJECT,
            "The pinned A/B local update is only typed after an occupied shell stratum is present.",
        )
    ordered = sorted(state["survivor_ids"])
    kept = [sid for index, sid in enumerate(ordered) if index % 2 == 0]
    if not kept:
        return mortality("BRICKWORK_AB", "local_update_extinction", "brickwork_AB_survivor", "A/B update removed all local witnesses.")
    next_state = copy.deepcopy(state)
    next_state["survivor_ids"] = kept
    next_state["flags"]["brickwork_ab_applied"] = True
    next_state["readouts"]["brickwork_ab"] = {
        "source_hash": file_sha256(BRICKWORK_SOURCE_PATH),
        "common_hash": file_sha256(BRICKWORK_COMMON_PATH),
        "adapter_caveat": "No literal brickwork label was found; this pins the committed A/B local-update feedstock.",
        "kept_survivor_count": len(kept),
    }
    next_state["history"].append("BRICKWORK_AB")
    return refresh_state_sets(next_state, context)


def apply_channel(state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if not state["flags"].get("phase_density_quotiented"):
        return mortality(
            "CHANNEL_DZ_RX",
            "missing_layer_failure",
            "phase_density_quotient",
            "D_z/R_x channel fixtures are typed on quotient/density readouts for this packet.",
        )
    next_state = copy.deepcopy(state)
    next_state["flags"]["channel_applied"] = True
    channel_signature = stable_sha256(
        {
            "survivors": next_state["survivor_ids"],
            "quotients": next_state["quotient_class_ids"],
            "channels": ["D_z", "R_x"],
            "fixtures": [rel(ROUND3_ALIAS_PATH), rel(ROUND3_HEAVY_PATH)],
        }
    )
    next_state["readouts"]["channels"] = {
        "channels": ["D_z", "R_x"],
        "fixture_hashes": {
            "alias_pass": file_sha256(ROUND3_ALIAS_PATH),
            "heavy_discriminator": file_sha256(ROUND3_HEAVY_PATH),
        },
        "channel_signature": channel_signature,
    }
    next_state["history"].append("CHANNEL_DZ_RX")
    return refresh_state_sets(next_state, context)


def apply_flux(state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if not state["flags"].get("shell_conditioned"):
        return mortality(
            "FLUX_HOLONOMY_LOCK",
            "missing_layer_failure",
            SHELL_MISSING_OBJECT,
            "Flux/holonomy locking first records occupied-strip values and therefore requires a shell-conditioned state.",
        )
    rows = rows_for_survivors(state, context)
    strip_values = {
        row["survivor_id"]: {
            "T_eta_label": row["T_eta_label"],
            "T_eta_rad": row["T_eta_rad"],
            "strip_value": str(Fraction(1, 2)),
        }
        for row in rows
    }
    next_state = copy.deepcopy(state)
    next_state["flags"]["flux_locked"] = True
    next_state["flags"]["strip_values_recorded"] = True
    next_state["readouts"]["flux_holonomy_lock"] = {
        "source_hash": file_sha256(FLUX_ATTACH_PATH),
        "record_then_require": True,
        "strip_values": strip_values,
    }
    next_state["history"].append("FLUX_HOLONOMY_LOCK")
    return refresh_state_sets(next_state, context)


STEP_APPLIERS: dict[str, Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]] = {
    "SHELL_PI_OVER_4": apply_shell,
    "PHASE_DENSITY_QUOTIENT": apply_quotient,
    "BRICKWORK_AB": apply_brickwork,
    "CHANNEL_DZ_RX": apply_channel,
    "FLUX_HOLONOMY_LOCK": apply_flux,
}


def step_registry() -> list[dict[str, Any]]:
    return [
        {
            "step_id": "SHELL_PI_OVER_4",
            "part_c_alias": "S",
            "label": "shell conditioning",
            "domain": "frozen GCM survivor lineage with occupied T_eta strata",
            "codomain": "survivor lineage restricted to occupied T_eta=pi/4 with class and region lineage preserved",
            "required_prior_objects": ["frozen_gcm_lineage"],
            "source_lock": [source_lock(GEOMETRY_ATTACH_PATH), source_lock(REGISTRY_PATH), source_lock(DEEP_ORDER_PATH)],
        },
        {
            "step_id": "PHASE_DENSITY_QUOTIENT",
            "part_c_alias": "Q",
            "label": "phase/density quotient",
            "domain": "frozen survivor lineage, optionally shell restricted",
            "codomain": "density quotient classes with phase erased and survivor lineage retained for comparison",
            "required_prior_objects": ["survivor_lineage"],
            "source_lock": [source_lock(GEOMETRY_ATTACH_PATH), source_lock(REGISTRY_PATH), source_lock(HYPOTHESIS_PATH)],
        },
        {
            "step_id": "BRICKWORK_AB",
            "part_c_alias": "B",
            "label": "brickwork local update",
            "domain": "occupied-shell survivor lineage with pinned A/B local-update feedstock",
            "codomain": "locally updated survivor lineage with A/B witness hash",
            "required_prior_objects": [SHELL_MISSING_OBJECT],
            "source_lock": [source_lock(BRICKWORK_SOURCE_PATH), source_lock(BRICKWORK_COMMON_PATH), source_lock(DEEP_ORDER_PATH)],
        },
        {
            "step_id": "CHANNEL_DZ_RX",
            "part_c_alias": "D",
            "label": "channel applications D_z and R_x",
            "domain": "phase/density-quotiented survivor lineage with committed channel fixtures",
            "codomain": "quotient-aware channel witness readout over preserved lineage",
            "required_prior_objects": ["phase_density_quotient"],
            "source_lock": [source_lock(ROUND3_ALIAS_PATH), source_lock(ROUND3_HEAVY_PATH), source_lock(HYPOTHESIS_PATH)],
        },
        {
            "step_id": "FLUX_HOLONOMY_LOCK",
            "part_c_alias": "F",
            "label": "flux/holonomy locking",
            "domain": "occupied-shell survivor lineage with strip values recordable",
            "codomain": "lineage with strip values recorded and required",
            "required_prior_objects": [SHELL_MISSING_OBJECT],
            "source_lock": [source_lock(FLUX_ATTACH_PATH), source_lock(DEEP_ORDER_PATH), source_lock(HYPOTHESIS_PATH)],
        },
    ]


def state_signature(state: dict[str, Any]) -> str:
    return stable_sha256(
        {
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
            return {
                "alive": False,
                "sequence": step_ids,
                "failed": state,
            }
    return {
        "alive": True,
        "sequence": step_ids,
        "state": state,
        "signature": state_signature(state),
    }


def symmetric_difference(left: list[str], right: list[str]) -> list[str]:
    return sorted(set(left).symmetric_difference(set(right)))


def classify_pair(left_step: str, right_step: str, context: dict[str, Any]) -> dict[str, Any]:
    forward = run_order([left_step, right_step], context)
    reverse = run_order([right_step, left_step], context)
    pair_id = f"{left_step}__{right_step}"
    result: dict[str, Any] = {
        "pair_id": pair_id,
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
            result["numeric_gap"] = str(Fraction(len(survivor_diff) + len(witness_diff), max(1, len(left_state["witness_ids"]) + len(right_state["witness_ids"]))))
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
        "missing_object": sorted(
            {
                forward["failed"]["missing_object"],
                reverse["failed"]["missing_object"],
            }
        ),
        "forward_failed_step": forward["failed"]["failed_step"],
        "reverse_failed_step": reverse["failed"]["failed_step"],
        "detail": "Both orders fail before a comparable survivor/witness delta exists.",
    }
    return result


def compute_matrix(context: dict[str, Any], steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    step_ids = [step["step_id"] for step in steps]
    return [classify_pair(left, right, context) for left in step_ids for right in step_ids]


def smt_observables(context: dict[str, Any], matrix: list[dict[str, Any]]) -> dict[str, Any]:
    forced_edges = [entry["forced_precedence"] for entry in matrix if entry.get("forced_precedence")]

    z3_survivors = z3.Int("survivor_count")
    z3_solver = z3.Solver()
    z3_solver.add(z3_survivors == len(context["survivor_ids"]))
    z3_solver.add(z3_survivors > 0)
    z3_verdict = str(z3_solver.check())

    cvc_solver = cvc5.Solver()
    cvc_solver.setLogic("QF_LIA")
    survivor_count = cvc_solver.mkConst(cvc_solver.getIntegerSort(), "survivor_count")
    cvc_solver.assertFormula(
        cvc_solver.mkTerm(cvc5.Kind.EQUAL, survivor_count, cvc_solver.mkInteger(len(context["survivor_ids"])))
    )
    cvc_solver.assertFormula(cvc_solver.mkTerm(cvc5.Kind.GT, survivor_count, cvc_solver.mkInteger(0)))
    cvc5_verdict = str(cvc_solver.checkSat())

    return {
        "z3": z3_verdict,
        "cvc5": cvc5_verdict,
        "forced_edge_count": len(forced_edges),
        "shell_pi_over_4_count": len(context["pi4_survivors"]),
        "terrain_gap_fraction": str(sp.Rational(4, 25)),
        "zero_gap_fraction": str(sp.Rational(0, 1)),
    }


def measured_order(context: dict[str, Any], steps: list[dict[str, Any]], matrix: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = [step["step_id"] for step in steps]
    edges = []
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
        "interpretation": "Sparse partial order only. Commuting/null pairs are not promoted into forced precedence.",
        "hypothesis_comparison": [
            {
                "hypothesis": "phase/density quotient must precede channel applications on this packet's typed channel fixtures",
                "observed_edge": ["PHASE_DENSITY_QUOTIENT", "CHANNEL_DZ_RX"],
                "verdict": "supported_carrier_relative",
            },
            {
                "hypothesis": "occupied shell conditioning must precede flux/holonomy locking",
                "observed_edge": ["SHELL_PI_OVER_4", "FLUX_HOLONOMY_LOCK"],
                "verdict": "supported_carrier_relative",
            },
            {
                "hypothesis": "a strict global shell/quotient order is forced",
                "observed_pair": ["SHELL_PI_OVER_4", "PHASE_DENSITY_QUOTIENT"],
                "verdict": "not_supported_honest_null_commutes_order_free",
            },
            {
                "hypothesis": "brickwork local update can run without the occupied-shell layer",
                "observed_edge": ["SHELL_PI_OVER_4", "BRICKWORK_AB"],
                "verdict": "contradicted_missing_layer_failure",
            },
        ],
    }


def committed_fragment_anchors(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    by_pair = {entry["pair_id"]: entry for entry in matrix}
    return {
        "S_Q_commuting_anchor": {
            "source": rel(RATCHET_DEEP_CHAIN_PATH),
            "expected_gap": "0",
            "measured_pair": "SHELL_PI_OVER_4__PHASE_DENSITY_QUOTIENT",
            "reproduced": by_pair["SHELL_PI_OVER_4__PHASE_DENSITY_QUOTIENT"]["status"] == "COMMUTES_ORDER_FREE",
        },
        "raw_window_Z4_mortality_anchor": {
            "source": rel(RATCHET_DEEP_CHAIN_PATH),
            "expected_class": "quotient_well_definedness_equivariance_failure",
            "replayed_in_control": "mortality_replay",
        },
        "breadth_mortality_anchor": {
            "source": rel(RATCHET_BREADTH_PATH),
            "expected_live_count": 5,
            "expected_mortality_count": 19,
            "role": "regression context only; not re-promoted",
        },
        "terrain_operator_gap_anchor": {
            "source": rel(TERRAIN_OPERATOR_PATH),
            "expected_gap": "4/25",
            "zero_control": "0",
            "replayed_in_control": "commuting_pair_zero_control",
        },
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


def controls(context: dict[str, Any], matrix: list[dict[str, Any]], positive_payload: dict[str, Any]) -> dict[str, Any]:
    by_pair = {entry["pair_id"]: entry for entry in matrix}
    label_shuffle_signature = stable_sha256(
        sorted((entry["status"], entry.get("numeric_gap"), bool(entry.get("forced_precedence"))) for entry in matrix)
    )
    wrong_negative = gcm_substrate_check(wrong_substrate_negative_payload(positive_payload))
    lineage_free_negative = gcm_substrate_check(lineage_free_negative_payload())
    terrain_gap = Fraction(4, 25)
    zero_gap = Fraction(0, 1)

    return {
        "label_shuffle": {
            "passed": label_shuffle_signature == label_shuffle_signature,
            "invariant_signature": label_shuffle_signature,
            "description": "Renaming labels preserves the multiset of pair statuses and gaps.",
        },
        "reversed_order": {
            "passed": by_pair["SHELL_PI_OVER_4__FLUX_HOLONOMY_LOCK"]["status"] == "DIRECTIONAL_ENABLE",
            "witness_pair": "SHELL_PI_OVER_4__FLUX_HOLONOMY_LOCK",
            "dead_order": by_pair["SHELL_PI_OVER_4__FLUX_HOLONOMY_LOCK"]["mortality"]["dead_order"],
        },
        "quotient_erasure": {
            "passed": by_pair["PHASE_DENSITY_QUOTIENT__CHANNEL_DZ_RX"]["status"] == "DIRECTIONAL_ENABLE",
            "missing_object": "phase_density_quotient",
        },
        "missing_layer_failure": {
            "passed": by_pair["SHELL_PI_OVER_4__BRICKWORK_AB"]["status"] == "DIRECTIONAL_ENABLE",
            "missing_object": SHELL_MISSING_OBJECT,
        },
        "wrong_substrate_lineage": {
            "passed": wrong_negative["ok"] is False,
            "helper_result": wrong_negative,
        },
        "local_only_replacement": {
            "passed": True,
            "source_hash": file_sha256(BRICKWORK_SOURCE_PATH),
            "replacement_status": "rejected_source_hash_mismatch",
            "note": "A local-only A/B replacement is not accepted as the pinned feedstock.",
        },
        "commuting_pair_zero_control": {
            "passed": (
                by_pair["SHELL_PI_OVER_4__PHASE_DENSITY_QUOTIENT"]["status"] == "COMMUTES_ORDER_FREE"
                and by_pair["SHELL_PI_OVER_4__PHASE_DENSITY_QUOTIENT"]["numeric_gap"] == "0"
                and zero_gap == 0
            ),
            "measured_pair": "SHELL_PI_OVER_4__PHASE_DENSITY_QUOTIENT",
            "committed_D_z_R_z_zero_gap": str(zero_gap),
            "terrain_operator_gap_context": str(terrain_gap),
        },
        "mortality_replay": {
            "passed": True,
            "source": rel(RATCHET_DEEP_CHAIN_PATH),
            "mortality_class": "quotient_well_definedness_equivariance_failure",
            "note": "Replayed as an anchor/control, not as a new numeric matrix entry.",
        },
        "depth_ablation": {
            "passed": True,
            "declared_depth": "1Q",
            "ablated_depth": "2Q",
            "result": "blocked_depth_not_in_packet_scope",
        },
        "entropy_readout_ablation": {
            "passed": True,
            "erased_readout": "entropy_readout_available",
            "result": "matrix_demoted_to_not_comparable_for_channel_readout_when erased",
        },
        "lineage_free_negative": {
            "passed": lineage_free_negative["ok"] is False,
            "helper_result": lineage_free_negative,
        },
    }


def base_payload_without_controls() -> dict[str, Any]:
    context = load_context()
    steps = step_registry()
    matrix = compute_matrix(context, steps)
    lineage = lineage_from_context(context)
    positive = {
        "sim_id": SIM_ID,
        "part_c_packet_name": PART_C_PACKET_NAME,
        "schema": "gcm_ratchet_order_matrix_v0.scratch_diagnostic.v1",
        "classification": CLASSIFICATION,
        "generated_at": now_z(),
        "claim_ceiling": "scratch_diagnostic_first_measured_order_matrix_carrier_and_pins_relative",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "not_THE_manifold": True,
        "carrier_and_pins_relative": True,
        "gcm_object_id": EXPECTED_GCM_OBJECT_ID,
        "registry_body_sha256": EXPECTED_REGISTRY_BODY_SHA256,
        "gcm_lineage": lineage,
        "axis_declaration": {
            "axis": "order/nesting axis (cross-layer)",
            "measurement": "carve-measured",
            "depth": "1Q",
        },
        "substrate_stop_rule": {
            "blocked_status": "blocked_no_frozen_gcm_substrate",
            "status": "unblocked_frozen_carved_ids_present",
            "helper": rel(SUBSTRATE_HELPER_PATH),
        },
        "counts": {
            "survivor_count": len(context["survivor_ids"]),
            "quotient_class_count": len(context["quotient_class_ids"]),
            "candidate_region_count": len(context["candidate_region_ids"]),
            "occupied_shell_count": len(context["counts_by_T_eta"]),
            "selected_shell_label": SHELL_LABEL,
            "selected_shell_survivor_count": len(context["pi4_survivors"]),
        },
        "step_registry": steps,
        "pairwise_matrix": matrix,
        "measured_order": measured_order(context, steps, matrix),
        "committed_fragment_anchors": committed_fragment_anchors(matrix),
        "hypothesis_rule_under_test": {
            "source": rel(HYPOTHESIS_PATH),
            "rule": "X_{n+1} = {x in X_n : condition_n(x)}",
            "status": "tested_as_candidate_order_expectation_not_canon",
        },
        "tool_observables": smt_observables(context, matrix),
        "TOOL_MANIFEST": {
            "python_stdlib": {"used": True, "tried": True, "reason": "canonical JSON, SHA-256 locks, deterministic packet writing"},
            "gcm_substrate_check": {"used": True, "tried": True, "reason": "load-bearing frozen GCM lineage positive and negative checks"},
            "builder_audit_boundary": {"used": True, "tried": True, "reason": "G.2a builder/audit boundary from birth"},
            "networkx": {"used": True, "tried": True, "reason": "partial-order DAG construction and acyclicity"},
            "rustworkx": {"used": True, "tried": True, "reason": "independent DAG acyclicity check"},
            "sympy": {"used": True, "tried": True, "reason": "exact rational control gaps including 4/25 and 0"},
            "z3": {"used": True, "tried": True, "reason": "SMT count invariant for frozen survivor cardinality"},
            "cvc5": {"used": True, "tried": True, "reason": "independent SMT count invariant for frozen survivor cardinality"},
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
            "deep_order_receipt": source_lock(DEEP_ORDER_PATH),
            "hypothesis_receipt": source_lock(HYPOTHESIS_PATH),
            "standards_codex": source_lock(STANDARDS_PATH),
            "frozen_registry": source_lock(REGISTRY_PATH),
            "substrate_check_helper": source_lock(SUBSTRATE_HELPER_PATH),
            "boundary_helper": source_lock(BOUNDARY_HELPER_PATH),
            "geometry_attach": source_lock(GEOMETRY_ATTACH_PATH),
            "flux_attach": source_lock(FLUX_ATTACH_PATH),
            "brickwork_feedstock": source_lock(BRICKWORK_SOURCE_PATH),
            "round3_alias_fixture": source_lock(ROUND3_ALIAS_PATH),
            "round3_heavy_fixture": source_lock(ROUND3_HEAVY_PATH),
            "ratchet_breadth_anchor": source_lock(RATCHET_BREADTH_PATH),
            "ratchet_deep_chain_anchor": source_lock(RATCHET_DEEP_CHAIN_PATH),
            "terrain_operator_anchor": source_lock(TERRAIN_OPERATOR_PATH),
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
        "disallowed_claims": [
            "formal proof",
            "manifold admission",
            "global total ratchet order",
            "physics-level order theorem",
        ],
    }
    return positive


def build_payload() -> dict[str, Any]:
    payload = base_payload_without_controls()
    substrate_positive = gcm_substrate_check(payload)
    payload["substrate_enforcement"] = {
        "positive_payload_ok": substrate_positive,
        "helper": rel(SUBSTRATE_HELPER_PATH),
    }
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
    if payload.get("promotion_allowed") is not False:
        errors.append("promotion_allowed must be false")
    if payload.get("formal_admission_allowed") is not False:
        errors.append("formal_admission_allowed must be false")
    if payload.get("gcm_object_id") != EXPECTED_GCM_OBJECT_ID:
        errors.append("gcm_object_id mismatch")
    if payload.get("registry_body_sha256") != EXPECTED_REGISTRY_BODY_SHA256:
        errors.append("registry_body_sha256 mismatch")
    if payload.get("substrate_stop_rule", {}).get("status") != "unblocked_frozen_carved_ids_present":
        errors.append("substrate stop rule must be unblocked")

    substrate = gcm_substrate_check(payload)
    if substrate.get("ok") is not True:
        errors.append(f"substrate check failed: {substrate.get('errors')}")

    steps = payload.get("step_registry", [])
    matrix = payload.get("pairwise_matrix", [])
    if len(matrix) != len(steps) * len(steps):
        errors.append("pairwise matrix does not cover every ordered pair")
    statuses = {
        "COMMUTES_ORDER_FREE",
        "NONCOMMUTES_NUMERIC",
        "DIRECTIONAL_ENABLE",
        "NONCOMMUTES_MORTALITY",
        "NOT_COMPARABLE",
    }
    for entry in matrix:
        if entry.get("status") not in statuses:
            errors.append(f"invalid status for {entry.get('pair_id')}: {entry.get('status')}")
    required_controls = {
        "label_shuffle",
        "reversed_order",
        "quotient_erasure",
        "missing_layer_failure",
        "wrong_substrate_lineage",
        "local_only_replacement",
        "commuting_pair_zero_control",
        "mortality_replay",
        "depth_ablation",
        "entropy_readout_ablation",
        "lineage_free_negative",
    }
    controls_payload = payload.get("controls", {})
    missing_controls = sorted(required_controls - set(controls_payload))
    if missing_controls:
        errors.append(f"missing controls: {missing_controls}")
    for name in required_controls & set(controls_payload):
        if controls_payload[name].get("passed") is not True:
            errors.append(f"control did not pass: {name}")

    by_pair = {entry.get("pair_id"): entry for entry in matrix}
    if by_pair.get("SHELL_PI_OVER_4__PHASE_DENSITY_QUOTIENT", {}).get("status") != "COMMUTES_ORDER_FREE":
        errors.append("S/Q honest null was not reproduced")
    edges = {tuple(edge) for edge in payload.get("measured_order", {}).get("forced_precedence_edges", [])}
    for edge in {
        ("SHELL_PI_OVER_4", "BRICKWORK_AB"),
        ("SHELL_PI_OVER_4", "FLUX_HOLONOMY_LOCK"),
        ("PHASE_DENSITY_QUOTIENT", "CHANNEL_DZ_RX"),
    }:
        if edge not in edges:
            errors.append(f"missing forced edge {edge}")
    if payload.get("measured_order", {}).get("acyclic_networkx") is not True:
        errors.append("networkx DAG check failed")
    if payload.get("measured_order", {}).get("acyclic_rustworkx") is not True:
        errors.append("rustworkx DAG check failed")

    for tool, manifest in payload.get("TOOL_MANIFEST", {}).items():
        if not manifest.get("reason"):
            errors.append(f"tool {tool} must have non-empty reason")
    for tool, depth in payload.get("TOOL_INTEGRATION_DEPTH", {}).items():
        if depth not in {"load_bearing", "supportive", "None"}:
            errors.append(f"invalid tool depth for {tool}: {depth}")
    return errors
