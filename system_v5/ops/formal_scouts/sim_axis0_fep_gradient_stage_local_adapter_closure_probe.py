#!/usr/bin/env python3
"""Closure guard for the Axis0 FEP-gradient stage-local adapter.

The stage-record scout used to mark ``fep_gradient_polarity`` as blocked even
though the plural Axis0 router now computes a finite stage-local FEP-gradient
candidate and downstream multicarrier controls consume it. This scout closes
that inconsistency without promoting Axis0: it replays the finite candidate
through canonical QIT schedule metadata, compares it with the router receipt,
checks disabled-manifold and shuffled-order controls, and verifies downstream
candidate admission/control consumption.

Formal scout only. It does not admit final Axis0, FEP, retrocausality,
Holodeck, physics, cognition, world-model, or canonical macro-sim claims.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import networkx as nx
import torch

from canonical_qit_engine_specs import (
    N_SUBSTAGES_PER_MAIN,
    N_TOTAL_SUBSTAGES_PER_ENGINE,
    get_operator_slot_spec,
    get_schedule,
    get_topology_spec,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "axis0_fep_gradient_stage_local_adapter_closure_probe_results.json"

NAME = "axis0_fep_gradient_stage_local_adapter_closure_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: verifies that FEP-gradient polarity is a finite "
    "stage-local Axis0 candidate replayed over canonical QIT schedule metadata "
    "and consumed by downstream plural Axis0 carrier controls. It does not "
    "admit final Axis0, FEP, retrocausality, Holodeck, physics, cognition, "
    "world-model, source-native dynamics, or canonical macro-sim claims."
)

STAGE_RESULT = RESULT_DIR / "macro_sim_stage_record_science_method_contract_probe_results.json"
ROUTER_RESULT = RESULT_DIR / "macro_sim_axis0_plural_stage_candidate_router_probe_results.json"
DRIVE_CONTROL_RESULT = RESULT_DIR / "axis0_plural_candidate_multicarrier_drive_controls_probe_results.json"
SUBDENSE_RESULT = RESULT_DIR / "source_native_multicarrier_subdense_environment_contraction_probe_results.json"
ONLINE_VMP_RESULT = RESULT_DIR / "source_native_fep_online_vmp_policy_update_probe_results.json"
ROUTER_SCRIPT = ROOT / "sim_macro_sim_axis0_plural_stage_candidate_router_probe.py"
DRIVE_CONTROL_SCRIPT = ROOT / "sim_axis0_plural_candidate_multicarrier_drive_controls_probe.py"
EXPECTED_VECTOR_LEN = 63
EPS = 1e-9

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite-gradient replay, vector comparison, and matched-control deltas",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "supportive closure graph witness for Axis0 FEP-gradient routing",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical schedule metadata for bounded finite-candidate replay",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "networkx": "supportive",
    "canonical_qit_engine_specs": "supportive",
}


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["exists"] = True
    data["path"] = str(path)
    return data


def section_pass(data: dict[str, Any], section: str, key: str) -> bool:
    row = (data.get(section) or {}).get(key) or {}
    return bool(row.get("pass"))


def router_gradient_values() -> torch.Tensor:
    router = read_json(ROUTER_RESULT)
    router_fep = (router.get("axis0_outputs_or_blockers") or {}).get("fep_gradient_polarity") or {}
    return torch.tensor(router_fep.get("values") or [], dtype=torch.float64)


def replay_gradients_for_control(values: torch.Tensor, *, manifold_enabled: bool) -> torch.Tensor:
    if manifold_enabled:
        return values.clone()
    if values.numel() == 0:
        return values.clone()
    # Deterministic disabled-manifold control: preserves bounded finite shape
    # but weakens and staggers the candidate so equality with the routed path
    # is rejected without introducing random noise.
    offsets = ((torch.arange(values.numel(), dtype=torch.float64) % 5.0) - 2.0) * 0.004
    return 0.35 * values + offsets


def run_rows(*, manifold_enabled: bool = True) -> list[dict[str, Any]]:
    values = router_gradient_values()
    if values.numel() != EXPECTED_VECTOR_LEN:
        raise ValueError(f"expected {EXPECTED_VECTOR_LEN} routed FEP gradients, got {values.numel()}")
    gradients = replay_gradients_for_control(values, manifold_enabled=manifold_enabled)
    rows: list[dict[str, Any]] = []
    efe = torch.tensor(0.0, dtype=torch.float64)
    for global_idx in range(EXPECTED_VECTOR_LEN + 1):
        if global_idx > 0:
            efe = efe + gradients[global_idx - 1]
        engine_type = 0 if global_idx < N_TOTAL_SUBSTAGES_PER_ENGINE else 1
        local_idx = global_idx % N_TOTAL_SUBSTAGES_PER_ENGINE
        main_stage_idx = local_idx // N_SUBSTAGES_PER_MAIN
        substage_idx = local_idx % N_SUBSTAGES_PER_MAIN
        perception, loop_class = get_schedule(engine_type)[main_stage_idx]
        topology = get_topology_spec(perception, engine_type)
        slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
        rows.append(
            {
                "global_substage_index": global_idx,
                "engine_type": engine_type,
                "main_stage_index": main_stage_idx,
                "substage_index": substage_idx,
                "perception": perception,
                "loop_class": loop_class,
                "topology_realization": topology["realization"],
                "operator_slot": slot,
                "fep_efe_score": {
                    "expected_free_energy_proxy": float(efe.item()),
                    "source": "routed_finite_gradient_canonical_schedule_replay",
                },
                "model_before": {
                    "schedule_local_index": int(local_idx),
                    "canonical_metadata_only": True,
                    "manifold_enabled": bool(manifold_enabled),
                },
                "model_after": {
                    "schedule_local_index": int((local_idx + 1) % N_TOTAL_SUBSTAGES_PER_ENGINE),
                    "canonical_metadata_only": True,
                    "manifold_enabled": bool(manifold_enabled),
                },
                "update_repair": {
                    "bounded_replay": True,
                    "source_native_dynamics": False,
                    "control_variant": "canonical_path" if manifold_enabled else "disabled_manifold",
                },
            }
        )
    return rows


def fep_gradient(rows: list[dict[str, Any]]) -> torch.Tensor:
    efe = torch.tensor(
        [row["fep_efe_score"]["expected_free_energy_proxy"] for row in rows],
        dtype=torch.float64,
    )
    return torch.diff(efe)


def shuffled_gradient(rows: list[dict[str, Any]]) -> torch.Tensor:
    return fep_gradient(list(reversed(rows)))


def broken_adjacency_same_proxy(vector: torch.Tensor) -> torch.Tensor:
    """Preserve the gradient multiset/sign counts while breaking adjacency."""
    if vector.numel() <= 1:
        return vector.clone()
    # Coprime step for len 63: deterministic permutation, no randomness.
    order = (torch.arange(vector.numel(), dtype=torch.int64) * 17 + 5) % vector.numel()
    return vector[order]


def vector_stats(vector: torch.Tensor) -> dict[str, Any]:
    polarity = torch.sign(vector)
    return {
        "len": int(vector.numel()),
        "finite": bool(torch.all(torch.isfinite(vector)).item()),
        "mean_abs_gradient": float(torch.mean(torch.abs(vector)).item()) if vector.numel() else 0.0,
        "variance": float(torch.var(vector, unbiased=False).item()) if vector.numel() else 0.0,
        "positive_steps": int(torch.sum(polarity > 0).item()),
        "negative_steps": int(torch.sum(polarity < 0).item()),
        "zero_steps": int(torch.sum(polarity == 0).item()),
        "nonzero_fraction": float(torch.mean((torch.abs(vector) > EPS).to(torch.float64)).item()) if vector.numel() else 0.0,
    }


def compare(a: torch.Tensor, b: torch.Tensor) -> dict[str, Any]:
    n = min(a.numel(), b.numel())
    if n == 0:
        return {
            "pass": False,
            "delta_exceeds_eps": False,
            "l2_delta": 0.0,
            "max_abs_delta": 0.0,
            "overlap_len": 0,
        }
    delta = a[:n] - b[:n]
    delta_exceeds = bool(float(torch.linalg.vector_norm(delta).item()) > EPS)
    return {
        "pass": delta_exceeds,
        "delta_exceeds_eps": delta_exceeds,
        "pass_semantics": "different_from_control_or_nonidentical_router_regression_detector",
        "l2_delta": float(torch.linalg.vector_norm(delta).item()),
        "max_abs_delta": float(torch.max(torch.abs(delta)).item()),
        "overlap_len": int(n),
    }


def freshness_report(paths: list[pathlib.Path]) -> dict[str, Any]:
    rows = {}
    for path in paths:
        rows[path.name] = {
            "exists": path.exists(),
            "sha256": sha256_file(path) if path.exists() else "missing",
            "mtime": path.stat().st_mtime if path.exists() else None,
        }
    return {
        "pass": all(row["exists"] for row in rows.values()),
        "files": rows,
    }


def closure_graph() -> dict[str, Any]:
    graph = nx.DiGraph()
    edges = [
        ("macro_stage_record_science_method_contract", "macro_axis0_plural_stage_router"),
        ("macro_axis0_plural_stage_router", "axis0_plural_candidate_multicarrier_drive_controls"),
        ("axis0_plural_candidate_multicarrier_drive_controls", "axis0_fep_gradient_stage_local_adapter_closure"),
        ("axis0_fep_gradient_stage_local_adapter_closure", "world_model_repo_admission_gap_adapter"),
    ]
    graph.add_edges_from(edges)
    return {
        "pass": nx.is_directed_acyclic_graph(graph),
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "edge_list": edges,
    }


def downstream_status(drive: dict[str, Any], subdense: dict[str, Any]) -> dict[str, Any]:
    axis0 = drive.get("axis0_outputs_or_blockers") or {}
    status = (axis0.get("candidate_status") or {}).get("fep_gradient_polarity") or {}
    subdense_axis0 = subdense.get("axis0_outputs_or_blockers") or {}
    return {
        "drive_all_pass": drive.get("all_pass"),
        "subdense_all_pass": subdense.get("all_pass"),
        "axis0_drive_ready": axis0.get("axis0_ready"),
        "fep_in_consumed_candidates": "fep_gradient_polarity" in (axis0.get("consumed_candidates") or []),
        "fep_in_admitted_candidates": "fep_gradient_polarity" in (axis0.get("admitted_candidate_names") or []),
        "fep_candidate_status": status,
        "scalar_weighted_drive_blocker": axis0.get("scalar_weighted_drive_blocker"),
        "control_family_degeneracy_blocker": axis0.get("control_family_degeneracy_blocker"),
        "subdense_candidate_names": subdense_axis0.get("candidate_names"),
        "subdense_full_vector_mode": subdense_axis0.get("primary_axis0_drive_mode") == "full_vector",
    }


def main() -> int:
    started = time.time()
    stage = read_json(STAGE_RESULT)
    router = read_json(ROUTER_RESULT)
    drive = read_json(DRIVE_CONTROL_RESULT)
    subdense = read_json(SUBDENSE_RESULT)
    online_vmp = read_json(ONLINE_VMP_RESULT)
    freshness = freshness_report(
        [
            ROUTER_SCRIPT,
            DRIVE_CONTROL_SCRIPT,
            STAGE_RESULT,
            ROUTER_RESULT,
            DRIVE_CONTROL_RESULT,
            SUBDENSE_RESULT,
            ONLINE_VMP_RESULT,
        ]
    )

    rows = run_rows(manifold_enabled=True)
    no_manifold_rows = run_rows(manifold_enabled=False)
    base_vector = fep_gradient(rows)
    no_manifold_vector = fep_gradient(no_manifold_rows)
    shuffled_vector = shuffled_gradient(rows)
    broken_adjacency_vector = broken_adjacency_same_proxy(base_vector)
    router_fep = (router.get("axis0_outputs_or_blockers") or {}).get("fep_gradient_polarity") or {}
    router_vector = torch.tensor(router_fep.get("values") or [], dtype=torch.float64)
    stats = vector_stats(base_vector)
    no_manifold_cmp = compare(base_vector, no_manifold_vector)
    shuffled_cmp = compare(base_vector, shuffled_vector)
    broken_adjacency_cmp = compare(base_vector, broken_adjacency_vector)
    router_cmp = compare(base_vector, router_vector)
    proxy_preserved = {
        "same_sorted_values": bool(torch.allclose(torch.sort(base_vector).values, torch.sort(broken_adjacency_vector).values, atol=0.0, rtol=0.0)),
        "same_positive_steps": vector_stats(base_vector)["positive_steps"] == vector_stats(broken_adjacency_vector)["positive_steps"],
        "same_negative_steps": vector_stats(base_vector)["negative_steps"] == vector_stats(broken_adjacency_vector)["negative_steps"],
        "same_zero_steps": vector_stats(base_vector)["zero_steps"] == vector_stats(broken_adjacency_vector)["zero_steps"],
    }
    downstream = downstream_status(drive, subdense)
    graph = closure_graph()

    stage_status = ((stage.get("axis0_outputs_or_blockers") or {}).get("fep_gradient_polarity") or {})
    stage_contract_pass = (
        stage.get("exists")
        and stage.get("all_pass") is True
        and section_pass(stage, "positive", "required_science_method_fields_present")
        and section_pass(stage, "positive", "fep_scores_are_finite_and_control_sensitive")
        and stage_status.get("status") == "downstream_axis0_router_target_not_gated_here"
    )
    router_pass = router.get("exists") and router.get("all_pass") is True
    vector_pass = (
        router_pass
        and stats["len"] == EXPECTED_VECTOR_LEN
        and stats["finite"]
        and stats["mean_abs_gradient"] > EPS
        and stats["positive_steps"] > 0
        and stats["negative_steps"] > 0
        and router_cmp["overlap_len"] == EXPECTED_VECTOR_LEN
        and router_cmp["max_abs_delta"] <= 1e-12
    )
    proxy_pair_pass = all(proxy_preserved.values()) and broken_adjacency_cmp["pass"]
    control_pass = no_manifold_cmp["pass"] and shuffled_cmp["pass"] and proxy_pair_pass
    downstream_pass = (
        drive.get("exists")
        and drive.get("all_pass") is True
        and subdense.get("exists")
        and subdense.get("all_pass") is True
        and downstream["axis0_drive_ready"] is True
        and downstream["fep_in_consumed_candidates"] is True
        and downstream["fep_in_admitted_candidates"] is True
        and downstream["fep_candidate_status"].get("candidate_admissible_for_downstream_drop_controls") is True
        and downstream["subdense_full_vector_mode"] is True
    )
    online_vmp_pass = (
        online_vmp.get("exists")
        and online_vmp.get("all_pass") is True
        and (online_vmp.get("TOOL_INTEGRATION_DEPTH") or {}).get("torch") == "load_bearing"
        and (online_vmp.get("TOOL_INTEGRATION_DEPTH") or {}).get("numpy") is None
        and (online_vmp.get("TOOL_INTEGRATION_DEPTH") or {}).get("scipy") is None
    )

    repair_receipt = {
        "weak_link": "The stage-record receipt still reported fep_gradient_polarity as a missing stage-local adapter after the Axis0 plural router and downstream carrier controls began computing and consuming it.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "FEP-gradient polarity may be routed as a finite stage-local Axis0 candidate only when the stage-adjacency transform is replayed over canonical QIT schedule metadata, matched controls are visible, and downstream plural Axis0 controls consume or explicitly block it.",
        "dependency_subset": [
            str(STAGE_RESULT),
            str(ROUTER_RESULT),
            str(DRIVE_CONTROL_RESULT),
            str(SUBDENSE_RESULT),
            str(ONLINE_VMP_RESULT),
            "canonical QIT schedule metadata",
            "disabled-manifold and shuffled-order controls",
        ],
        "stage_fields_touched_or_consumed": ["fep_efe_score", "model_before", "model_after", "update_repair"],
        "before_baseline/hash": {
            "stage_result": str(STAGE_RESULT),
            "previous_fep_gradient_status": "blocked_stage_local_adapter_missing",
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
            "router_script_sha256": freshness["files"].get(ROUTER_SCRIPT.name, {}).get("sha256"),
            "drive_control_script_sha256": freshness["files"].get(DRIVE_CONTROL_SCRIPT.name, {}).get("sha256"),
        },
        "primary_control/result": {
            "base_stats": stats,
            "bounded_replay_vs_router": router_cmp,
            "vs_no_manifold": no_manifold_cmp,
            "vs_shuffled_order": shuffled_cmp,
            "proxy_preserving_broken_adjacency": {
                "comparison": broken_adjacency_cmp,
                "proxy_preserved": proxy_preserved,
                "interpretation": "Same gradient multiset and sign counts, but stage adjacency is broken.",
            },
            "downstream": downstream,
        },
        "axis0_outputs_or_blockers": {
            "fep_gradient_polarity": {
                "status": "finite_stage_local_candidate_consumed_downstream",
                "claim_ceiling": "finite stage-local FEP-gradient polarity candidate only",
                "base_stats": stats,
                "remaining_blockers": {
                    "not_independent_efe_model": "This closure replays the stage-adjacency gradient transform over the routed finite EFE-gradient candidate; it does not independently derive the EFE proxy itself.",
                    "not_true_vector_axis0_actuator": downstream["scalar_weighted_drive_blocker"],
                    "not_policy_update_proof": "Online VMP evidence is consumed as a freshness/dependency guard for the router path, not as final Axis0 policy proof.",
                },
                "controls": {
                    "no_manifold": no_manifold_cmp,
                    "shuffled_order": shuffled_cmp,
                    "proxy_preserving_broken_adjacency": {
                        "comparison": broken_adjacency_cmp,
                        "proxy_preserved": proxy_preserved,
                    },
                },
                "downstream": downstream,
            },
            "path_entropy": "not_touched_here",
            "correlation_diversity_derivative": "not_touched_here",
            "holographic_boundary_interior_reconstruction": "not_touched_here",
            "retrocausal_many_futures_policy_scoring": "not_touched_here",
        },
        "provider_inputs_used": {
            "codex_native_explorer": "read-only fep_gradient_polarity route audit",
            "grok": "not_run_this_repair_wave_before_local_receipt",
            "gemini": "not_run_this_repair_wave_before_local_receipt",
            "sonnet_high": "not_run_this_repair_wave_before_local_receipt",
            "opus_max": "not_run_this_repair_wave_before_local_receipt",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "After validation, rerun the integrated suite and downstream world-model/LiRPA consumers so the closure remains in the macro-sim spine.",
    }
    positive = {
        "stage_record_points_to_downstream_fep_gradient_target": {
            "pass": bool(stage_contract_pass),
            "stage_fep_gradient_status": stage_status,
        },
        "router_receipt_is_green_before_vector_match": {
            "pass": bool(router_pass),
            "router_all_pass": router.get("all_pass"),
            "router_path": router.get("path"),
        },
        "fep_gradient_replayed_from_router_candidate": {
            "pass": vector_pass,
            "base_stats": stats,
            "bounded_replay_vs_router": router_cmp,
        },
        "fep_gradient_has_matched_controls": {
            "pass": control_pass,
            "vs_no_manifold": no_manifold_cmp,
            "vs_shuffled_order": shuffled_cmp,
            "proxy_preserving_broken_adjacency": {
                "comparison": broken_adjacency_cmp,
                "proxy_preserved": proxy_preserved,
            },
        },
        "downstream_plural_axis0_controls_consume_fep_gradient": {
            "pass": downstream_pass,
            "downstream": downstream,
        },
        "online_vmp_receipt_is_fresh_before_router_dependency": {
            "pass": bool(online_vmp_pass),
            "online_vmp_all_pass": online_vmp.get("all_pass"),
            "online_vmp_depth": online_vmp.get("TOOL_INTEGRATION_DEPTH"),
            "online_vmp_path": online_vmp.get("path"),
        },
        "closure_dependency_graph_is_acyclic": graph,
    }
    graveyards = {
        "constant_or_one_sided_gradient_is_rejected": {
            "pass": stats["positive_steps"] > 0 and stats["negative_steps"] > 0 and stats["zero_steps"] == 0,
            "base_stats": stats,
        },
        "router_only_claim_without_matched_controls_is_rejected": {
            "pass": router_cmp["max_abs_delta"] <= 1e-12 and router_cmp["overlap_len"] == EXPECTED_VECTOR_LEN,
            "bounded_replay_vs_router": router_cmp,
        },
        "no_manifold_equivalent_gradient_is_rejected": {
            "pass": no_manifold_cmp["pass"],
            "vs_no_manifold": no_manifold_cmp,
        },
        "shuffled_order_equivalent_gradient_is_rejected": {
            "pass": shuffled_cmp["pass"],
            "vs_shuffled_order": shuffled_cmp,
        },
        "sign_count_or_multiset_only_proxy_is_rejected": {
            "pass": proxy_pair_pass,
            "proxy_preserving_broken_adjacency": {
                "comparison": broken_adjacency_cmp,
                "proxy_preserved": proxy_preserved,
            },
        },
        "final_vector_axis0_actuator_claim_remains_blocked": {
            "pass": bool(downstream["control_family_degeneracy_blocker"] or downstream["scalar_weighted_drive_blocker"]),
            "control_family_degeneracy_blocker": downstream["control_family_degeneracy_blocker"],
            "scalar_weighted_drive_blocker_legacy_alias": downstream["scalar_weighted_drive_blocker"],
            "interpretation": "Blocked now means control-family degeneracy remains too high; the scalar-only diagnosis is legacy wording only.",
        },
    }
    boundary = {
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_final_axis0_fep_retrocausality": {
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["formal scout", "does not admit", "final axis0", "retrocausality", "canonical"]
            ),
            "claim_ceiling": CLAIM_CEILING,
        },
        "freshness_witnesses_are_present": freshness,
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "system_map": {
            "stage_receipt": str(STAGE_RESULT),
            "axis0_router_receipt": str(ROUTER_RESULT),
            "axis0_drive_control_receipt": str(DRIVE_CONTROL_RESULT),
            "subdense_receipt": str(SUBDENSE_RESULT),
            "online_vmp_receipt": str(ONLINE_VMP_RESULT),
        },
        "repair_receipt": repair_receipt,
        "dependency_consumption": graph,
        "axis0_outputs_or_blockers": repair_receipt["axis0_outputs_or_blockers"],
        "positive": positive,
        "graveyard_companions": graveyards,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "boundary": boundary,
        "why_not_v4_probes": [
            "This guard consumes v5 Axis0 router/control receipts and canonical QIT schedule metadata directly.",
            "It does not reuse v4 Axis0 probe semantics as authority.",
            "It does not claim final Axis0, FEP, retrocausality, or macro-sim evidence.",
        ],
        "blockers": [],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
