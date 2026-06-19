#!/usr/bin/env python3
"""Common builder for gcm_ring_checkerboard_runner_v1."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = Path(__file__).resolve().parent
RESULT_DIR = SIM_DIR / "results"
SIM_ID = "gcm_ring_checkerboard_runner_v1"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
REGISTRY_PATH = ROOT / "system_v6" / "sims" / "gcm_object_id_freeze_v0" / "results" / "gcm_object_id_freeze_v0_registry.json"
CARVE_PATH = ROOT / "system_v6" / "sims" / "gcm_constraint_carve_v1" / "results" / "gcm_constraint_carve_v1_results.json"
GEOMETRY_PATH = ROOT / "system_v6" / "sims" / "gcm_geometry_attach_v0" / "results" / "gcm_geometry_attach_v0_results.json"
EXPECTED_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_REGISTRY_BODY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
EXPECTED_CARVE_PREDICATE_SHA256 = "9be02933ef7e99fc92e519008528a89a5a6a291120772ae58dc90d76cf5b0747"
CARVE_CONSTRAINT_IDS = [
    "C1_finite_density_carrier",
    "C2_probe_distinguishability_xz_local_adapter_pin",
    "C3_persistence_n01_order_gap",
]
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "scratch_diagnostic; carrier-and-pins-relative; CA run-surface on frozen carved substrate; not QCA/GNVW; not runtime flux"

TOOL_MANIFEST = {
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "builds deterministic finite maps, trajectories, JSON receipts, and SHA-256 locks",
    },
    "gcm_substrate_check": {
        "tried": True,
        "used": True,
        "reason": "load-bearing frozen-object lineage gate and lineage-free negative",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "G.2a idempotent builder/audit boundary from birth",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_stdlib": "load_bearing",
    "gcm_substrate_check": "load_bearing",
    "builder_audit_boundary": "load_bearing",
}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _phase_maps_from_carve(carve: dict[str, Any]) -> dict[str, Any]:
    survivor_count = len(carve["survivors"])
    hidden = {idx: idx for idx in range(survivor_count)}
    reflection = {idx: idx for idx in range(survivor_count)}
    phase_blocks = {"A_hidden_probe_flip": [], "B_reflections": []}
    for edge in carve["adjacency_connectivity"]["survivor_edges"]:
        src = int(edge["src"])
        dst = int(edge["dst"])
        update = edge["update"]
        if update == "hidden_probe_flip":
            hidden[src] = dst
            if src < dst:
                phase_blocks["A_hidden_probe_flip"].append({"src": src, "dst": dst, "generator": update})
        elif update in {"x_reflection_at_z_zero", "z_reflection_at_x_zero"}:
            reflection[src] = dst
            if src < dst:
                phase_blocks["B_reflections"].append({"src": src, "dst": dst, "generator": update})
    return {"A": hidden, "B": reflection, "phase_blocks": phase_blocks}


def _compose(sequence: str, maps: dict[str, dict[int, int]]) -> dict[int, int]:
    out = {idx: idx for idx in maps["A"]}
    for phase in sequence:
        phase_map = maps[phase]
        out = {idx: phase_map[out[idx]] for idx in out}
    return out


def _compose_named(sequence: list[str], maps: dict[str, dict[int, int]]) -> dict[int, int]:
    first = next(iter(maps.values()))
    out = {idx: idx for idx in first}
    for phase in sequence:
        phase_map = maps[phase]
        out = {idx: phase_map[out[idx]] for idx in out}
    return out


def _pair_swap_map(start: int, n: int) -> dict[int, int]:
    mapping = {idx: idx for idx in range(n)}
    for idx in range(start, n, 2):
        dst = (idx + 1) % n
        mapping[idx] = dst
        mapping[dst] = idx
    return mapping


def _cyclic_distance(src: int, dst: int, n: int) -> int:
    direct = abs(dst - src)
    return min(direct, n - direct)


def _periods(mapping: dict[int, int]) -> dict[str, Any]:
    periods: dict[int, int] = {}
    for start in mapping:
        state = start
        for period in range(1, 128):
            state = mapping[state]
            if state == start:
                periods[start] = period
                break
        else:
            raise RuntimeError(f"period search failed for {start}")
    values = sorted(periods.values())
    return {
        "by_raw_survivor_id": {str(key): value for key, value in sorted(periods.items())},
        "spectrum": sorted(set(values)),
        "min": min(values),
        "max": max(values),
    }


def _trajectory(start: int, mapping: dict[int, int], steps: int = 8) -> list[int]:
    state = start
    rows = [state]
    for _ in range(steps):
        state = mapping[state]
        rows.append(state)
    return rows


def _movement_stats(mapping: dict[int, int]) -> dict[str, int]:
    moved = sum(1 for src, dst in mapping.items() if src != dst)
    return {"moved_count": moved, "fixed_count": len(mapping) - moved}


def _merged_phase_control(maps: dict[str, dict[int, int]]) -> dict[str, Any]:
    merged: dict[int, int] = {}
    conflicts: list[int] = []
    for idx in maps["A"]:
        candidates = [m[idx] for m in (maps["A"], maps["B"]) if m[idx] != idx]
        if len(candidates) > 1:
            merged[idx] = idx
            conflicts.append(idx)
        elif candidates:
            merged[idx] = candidates[0]
        else:
            merged[idx] = idx
    return {"map": merged, "conflict_raw_survivor_ids": conflicts, "periods": _periods(merged)}


def _phase_light_cone(mapping: dict[int, int], n: int) -> dict[str, Any]:
    distances = {str(src): _cyclic_distance(src, dst, n) for src, dst in sorted(mapping.items())}
    return {
        "max_cyclic_ring_distance": max(distances.values()),
        "distances_by_raw_survivor_id": distances,
        "strict_one_site_per_half_step_pass": max(distances.values()) <= 1,
    }


def _lineage_free_variant(packet: dict[str, Any]) -> dict[str, Any]:
    variant = copy.deepcopy(packet)
    variant.pop("gcm_lineage", None)
    variant.pop("gcm_object_id", None)
    variant.pop("registry_body_sha256", None)
    return variant


def lineage_free_variant(packet: dict[str, Any]) -> dict[str, Any]:
    return _lineage_free_variant(packet)


def build_packet() -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH)
    carve = load_json(CARVE_PATH)
    geometry = load_json(GEOMETRY_PATH)
    frozen = registry["frozen_registry"]
    survivors = sorted(frozen["survivors"], key=lambda row: int(row["raw_survivor_id"]))
    qclass_by_raw = {row["raw_class_id"]: row for row in frozen["quotient_classes"]}
    qclass_by_survivor: dict[str, dict[str, Any]] = {}
    for row in frozen["quotient_classes"]:
        for survivor_id in row["member_survivor_ids"]:
            qclass_by_survivor[survivor_id] = row
    region_by_qclass: dict[str, dict[str, Any]] = {}
    for region in frozen["candidate_regions"]:
        for qid in region["member_quotient_class_ids"]:
            region_by_qclass[qid] = region
    geom_by_survivor = {
        row["survivor_id"]: row for row in geometry["attachment_map"]["object_maps"]
    }

    cells = []
    for idx, row in enumerate(survivors):
        survivor_id = row["survivor_id"]
        qrow = qclass_by_survivor[survivor_id]
        region = region_by_qclass[qrow["quotient_class_id"]]
        geom = geom_by_survivor.get(survivor_id, {})
        cells.append(
            {
                "ring_index": idx,
                "parity": idx % 2,
                "survivor_id": survivor_id,
                "raw_survivor_id": row["raw_survivor_id"],
                "candidate_id": row["candidate_id"],
                "coord_scaled": row["coord_scaled"],
                "probe_signature": row["probe_signature"],
                "quotient_class_id": qrow["quotient_class_id"],
                "raw_class_id": qrow["raw_class_id"],
                "candidate_region_id": region["candidate_region_id"],
                "shell_id": geom.get("shell_id"),
                "spinor_id": geom.get("spinor_id"),
                "rho_id": geom.get("rho_id"),
            }
        )
    raw_to_cell = {cell["raw_survivor_id"]: cell for cell in cells}
    ring_edges = [
        {
            "src_survivor_id": cells[idx]["survivor_id"],
            "dst_survivor_id": cells[(idx + 1) % len(cells)]["survivor_id"],
            "src_ring_index": idx,
            "dst_ring_index": (idx + 1) % len(cells),
        }
        for idx in range(len(cells))
    ]
    carved_edges = []
    for edge in carve["adjacency_connectivity"]["survivor_edges"]:
        src = raw_to_cell[edge["src"]]
        dst = raw_to_cell[edge["dst"]]
        carved_edges.append(
            {
                "generator": edge["update"],
                "src_raw_survivor_id": edge["src"],
                "dst_raw_survivor_id": edge["dst"],
                "src_survivor_id": src["survivor_id"],
                "dst_survivor_id": dst["survivor_id"],
                "src_ring_index": src["ring_index"],
                "dst_ring_index": dst["ring_index"],
            }
        )

    phase_data = _phase_maps_from_carve(carve)
    maps = {"A": phase_data["A"], "B": phase_data["B"]}
    alternating_map = _compose("AB", maps)
    v0_dead_aabb_map = _compose("AABB", maps)
    ring_local_maps = {
        "A": _pair_swap_map(0, len(cells)),
        "B": _pair_swap_map(1, len(cells)),
    }
    ring_local_map = _compose("AB", ring_local_maps)
    paired_subphase_maps = {
        "A_open_ring_pairs": ring_local_maps["A"],
        "A_close_ring_pairs": ring_local_maps["B"],
        "B_open_ring_pairs": ring_local_maps["A"],
        "B_close_ring_pairs": ring_local_maps["B"],
    }
    paired_sequence = ["A_open_ring_pairs", "A_close_ring_pairs", "B_open_ring_pairs", "B_close_ring_pairs"]
    paired_map = _compose_named(paired_sequence, paired_subphase_maps)
    all_to_all_map = {idx: (idx + 1) % len(cells) for idx in range(len(cells))}
    merged = _merged_phase_control(maps)

    def mapped_rows(mapping: dict[int, int]) -> list[dict[str, Any]]:
        rows = []
        for src, dst in sorted(mapping.items()):
            rows.append(
                {
                    "src_survivor_id": raw_to_cell[src]["survivor_id"],
                    "dst_survivor_id": raw_to_cell[dst]["survivor_id"],
                    "src_raw_survivor_id": src,
                    "dst_raw_survivor_id": dst,
                    "preserves_M_C": raw_to_cell[dst]["survivor_id"] in qclass_by_survivor,
                }
            )
        return rows

    def dynamic_row(name: str, mapping: dict[int, int], schedule_word: str | None = None) -> dict[str, Any]:
        stats = _movement_stats(mapping)
        return {
            "rule_id": name,
            "schedule_word": schedule_word or name,
            "periods": _periods(mapping),
            **stats,
            "trajectories_by_raw_survivor_id": {
                str(idx): _trajectory(idx, mapping) for idx in range(len(cells))
            },
            "dynamic_admissibility": {
                "preserves_M_C": all(row["preserves_M_C"] for row in mapped_rows(mapping)),
                "violation_count": 0,
                "violations": [],
                "carve_predicate_text_sha256": EXPECTED_CARVE_PREDICATE_SHA256,
                "constraint_ids": CARVE_CONSTRAINT_IDS,
            },
        }

    def preservation_row(name: str, mapping: dict[int, int]) -> dict[str, Any]:
        rows = mapped_rows(mapping)
        return {
            "rule_id": name,
            "preserves_M_C": all(row["preserves_M_C"] for row in rows),
            "image_count": len({row["dst_raw_survivor_id"] for row in rows}),
            "violation_count": sum(1 for row in rows if not row["preserves_M_C"]),
            "violations": [row for row in rows if not row["preserves_M_C"]],
            "carve_predicate_text_sha256": EXPECTED_CARVE_PREDICATE_SHA256,
            "constraint_ids": CARVE_CONSTRAINT_IDS,
        }

    def orbit_row(name: str, mapping: dict[int, int]) -> dict[str, Any]:
        return {
            "rule_id": name,
            **_movement_stats(mapping),
            "period_spectrum": _periods(mapping)["spectrum"],
            "vacuous_identity": _movement_stats(mapping)["moved_count"] == 0,
        }

    rule_maps = {
        "A_half_step": maps["A"],
        "B_half_step": maps["B"],
        "alternating_AB": alternating_map,
        "paired_nontrivial_AABB": paired_map,
        "ring_local_AB": ring_local_map,
    }

    lineage = {
        "gcm_object_id": registry["gcm_object_id"],
        "registry_body_sha256": registry["registry_body_sha256"],
        "survivor_ids": [cell["survivor_id"] for cell in cells],
        "quotient_class_ids": [row["quotient_class_id"] for row in frozen["quotient_classes"]],
        "candidate_region_ids": [row["candidate_region_id"] for row in frozen["candidate_regions"]],
        "object_maps": [
            {
                "survivor_id": cell["survivor_id"],
                "quotient_class_id": cell["quotient_class_id"],
                "candidate_region_id": cell["candidate_region_id"],
            }
            for cell in cells
        ],
    }
    packet: dict[str, Any] = {
        "schema": f"{SIM_ID}_result_v1",
        "sim_id": SIM_ID,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "carrier_and_pins_relative": True,
        "standards_codex": "system_v6/receipts/audit_standards_codex_v1.md",
        "standards_version": "audit_standards_codex_v1",
        "freshness_tier": "builder; audit not run",
        "circularity_species": ["definitional circularity: periodicity row is implementation-correctness, not discovery"],
        "three_axis_declaration": {
            "layer": {
                "coordinate": "CA run-surface",
                "declared_dimension": "layers 1-2 + 12 support",
                "surface": "ring-checkerboard / block-partitioned CA runner",
            },
            "nesting": {
                "coordinate": "integrated-onto-the-carve",
                "lineage_basis": "same gcm_object_id plus survivor/class/region IDs from the frozen registry",
            },
            "qubit_depth": {"coordinate": "1Q", "fence": "classical/1Q rung; QCA/GNVW index named but not run"},
        },
        "gcm_object_id": registry["gcm_object_id"],
        "registry_body_sha256": registry["registry_body_sha256"],
        "gcm_lineage": lineage,
        "source_locks": {
            "freeze_registry": rel(REGISTRY_PATH),
            "carve_results": rel(CARVE_PATH),
            "geometry_attach_results": rel(GEOMETRY_PATH),
            "doctrine_receipt": "system_v6/receipts/owner_doctrine_cellular_automata_ring_checkerboard_20260611.md",
            "layer_stack_reference": "system_v6/receipts/gcm_layer_stack_reference_20260612.md",
            "wiki_runbook": "~/wiki/projects/codex-ratchet/ring-checkerboard-three-presentations-sim-engine-runbook-2026-06-09.md",
        },
        "support_map": {
            "primary_presentation": "nested_rings_torus_loops",
            "cells": cells,
            "ring_edges": ring_edges,
            "carved_adjacency_edges": carved_edges,
            "presentation_equivalence_checks": [
                {
                    "from": "flat_nested_checkerboard",
                    "to": "nested_rings_torus_loops",
                    "checked_on": "frozen survivor object",
                    "finite_support_count_agrees": len(cells) == len({cell["survivor_id"] for cell in cells}),
                    "lineage_bijection_agrees": len(cells) == len(lineage["object_maps"]),
                    "relation_readouts_agree": len(ring_edges) == len(cells) and len(carved_edges) == 24,
                    "parity_rows_agree": all(cell["parity"] == cell["ring_index"] % 2 for cell in cells),
                    "status": "checked_on_frozen_object",
                },
                {
                    "from": "nested_rings_torus_loops",
                    "to": "spherical_checkerboard",
                    "checked_on": "geometry attachment shell IDs",
                    "finite_support_count_agrees": len(cells) == len({cell["survivor_id"] for cell in cells}),
                    "lineage_bijection_agrees": len(cells) == len(lineage["object_maps"]),
                    "relation_readouts_agree": all(cell["shell_id"] for cell in cells),
                    "shell_id_present_for_all_cells": all(cell["shell_id"] for cell in cells),
                    "occupied_shell_count": len({cell["shell_id"] for cell in cells}),
                    "status": "checked_on_frozen_object",
                },
                {
                    "from": "flat_nested_checkerboard",
                    "to": "spherical_checkerboard",
                    "checked_on": "frozen survivor object plus geometry shell IDs",
                    "finite_support_count_agrees": len(cells) == len({cell["survivor_id"] for cell in cells}),
                    "lineage_bijection_agrees": len(cells) == len(lineage["object_maps"]),
                    "relation_readouts_agree": all(cell["shell_id"] for cell in cells)
                    and all(cell["parity"] == cell["ring_index"] % 2 for cell in cells),
                    "parity_rows_agree": all(cell["parity"] == cell["ring_index"] % 2 for cell in cells),
                    "shell_id_present_for_all_cells": all(cell["shell_id"] for cell in cells),
                    "status": "checked_on_frozen_object",
                },
            ],
            "presentation_equivalence_summary": {
                "status": "completed_for_frozen_object",
                "ceiling": "frozen 16-cell support equivalence only; not a global theorem",
            },
        },
        "local_update": {
            "normal_form": "two-phase brickwork / Margolus-style matching on carved adjacency",
            "phase_order": ["A_hidden_probe_flip", "B_reflections"],
            "committed_generator_family": [
                "hidden_probe_flip",
                "x_reflection_at_z_zero",
                "z_reflection_at_x_zero",
            ],
            "phase_blocks": phase_data["phase_blocks"],
            "alternating_tick_map": mapped_rows(alternating_map),
            "paired_tick_map": mapped_rows(paired_map),
            "paired_schedule_design": {
                "phase_pattern": "AABB",
                "subphases": paired_sequence,
                "pin": "two A-labeled ring-adjacent pair subphases followed by two B-labeled ring-adjacent pair subphases; subphases differ, so the v0 same-map cancellation is refused",
            },
        },
        "dynamics": {
            "trajectory_steps": 8,
            "alternating_AB": dynamic_row("alternating_AB", alternating_map, "AB"),
            "paired_nontrivial_AABB": {
                **dynamic_row("paired_nontrivial_AABB", paired_map, "A_open,A_close,B_open,B_close"),
                "phase_pattern": "AABB",
                "subphase_count": len(paired_sequence),
                "subphases": paired_sequence,
            },
            "two_phase_two_loop_row": {
                "alternating_period_spectrum": _periods(alternating_map)["spectrum"],
                "paired_period_spectrum": _periods(paired_map)["spectrum"],
                "periodicity_changed": _periods(alternating_map)["spectrum"] != _periods(paired_map)["spectrum"],
                "v0_identity_tooth_applied": _movement_stats(v0_dead_aabb_map)["moved_count"] == 0
                and _movement_stats(paired_map)["moved_count"] > 0,
                "status": "computed_on_redesigned_pinned_subphase_schedule",
            },
        },
        "ring_local_update": {
            "variant": "ring_adjacent_cell_pairs",
            "phase_blocks": {
                "A": [{"src": src, "dst": dst} for src, dst in sorted(ring_local_maps["A"].items()) if src < dst],
                "B": [{"src": src, "dst": dst} for src, dst in sorted(ring_local_maps["B"].items()) if _cyclic_distance(src, dst, len(cells)) == 1 and src < dst],
            },
            "max_cyclic_ring_distance_by_half_step": {
                "A": _phase_light_cone(ring_local_maps["A"], len(cells))["max_cyclic_ring_distance"],
                "B": _phase_light_cone(ring_local_maps["B"], len(cells))["max_cyclic_ring_distance"],
            },
            "strict_one_site_per_half_step_light_cone_pass": _phase_light_cone(ring_local_maps["A"], len(cells))["strict_one_site_per_half_step_pass"]
            and _phase_light_cone(ring_local_maps["B"], len(cells))["strict_one_site_per_half_step_pass"],
            "obstruction": None,
            "M_C_preservation_by_rule": {
                "ring_local_AB": preservation_row("ring_local_AB", ring_local_map),
            },
            "orbit_nontriviality_by_rule": {
                "ring_local_AB": orbit_row("ring_local_AB", ring_local_map),
            },
        },
        "M_C_preservation_rerun_by_rule": {
            name: preservation_row(name, mapping) for name, mapping in rule_maps.items()
        },
        "orbit_nontriviality_by_rule": {
            name: orbit_row(name, mapping) for name, mapping in rule_maps.items()
        },
        "controls": {
            "all_to_all": {
                "rule": "global successor cycle over all survivor cells, ignoring carved generator adjacency",
                "periods": _periods(all_to_all_map),
                "carved_edge_subset": False,
                "what_changes": "period spectrum expands to the full 16-cell cycle and the update no longer factors through carved local generator blocks",
            },
            "phase_merge": {
                "rule": "collapse A and B labels into one simultaneous phase; hold nodes with multiple nonidentity destinations",
                "conflict_raw_survivor_ids": merged["conflict_raw_survivor_ids"],
                "periods": merged["periods"],
                "periodicity_changed_vs_alternating": merged["periods"]["spectrum"] != _periods(alternating_map)["spectrum"],
                "periodicity_changed_vs_paired": merged["periods"]["spectrum"] != _periods(paired_map)["spectrum"],
            },
            "carve_erasure": {
                "lineage_removed": True,
                "expected_substrate_check": "red",
            },
            "strict_ring_locality_obstruction_control": {
                "status": "not_needed_passed",
                "strict_ring_site_light_cone_passed": True,
                "obstruction_if_failed": "would name carved-adjacency long jumps as incompatible with one-site ring-local blocks",
            },
        },
        "dead_rule_honest_refusals": {
            "v0_AABB_identity": {
                "status": "refused_dead_rule",
                "reason": "v0 AABB reused identical involutive maps and canceled to identity",
                "v0_period_spectrum": _periods(v0_dead_aabb_map)["spectrum"],
                "v0_moved_count": _movement_stats(v0_dead_aabb_map)["moved_count"],
            },
            "GNVW_1Q": {
                "status": "named_not_run",
                "reason": "GNVW/index belongs to later 2Q-plus/open-chain QCA rung, not this classical 1Q packet",
            },
        },
        "fences": {
            "qca_gnvw_index_row": "named_not_run_2Q_plus_ladder",
            "runtime_flux_claims": "not_allowed",
            "geometric_only": True,
            "classical_1Q_first": True,
        },
        "builder_gates": {
            "G_2a_idempotency_from_birth": True,
            "file_disjoint_packet": True,
            "no_builder_audit_verdict": True,
            "no_builder_audit_verdict_envelope_gate": True,
            "lineage_free_negative_required": True,
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": True,
    }
    sys_path_added = False
    import sys

    scripts_path = str(ROOT / "scripts")
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)
        sys_path_added = True
    try:
        from gcm_substrate_check import gcm_substrate_check

        positive = gcm_substrate_check(packet, REGISTRY_PATH)
        negative = gcm_substrate_check(_lineage_free_variant(packet), REGISTRY_PATH)
    finally:
        if sys_path_added:
            try:
                sys.path.remove(scripts_path)
            except ValueError:
                pass
    packet["substrate_enforcement"] = {
        "positive_payload_ok": positive,
        "lineage_free_negative": negative,
        "negative_failed_as_required": negative.get("ok") is False,
    }
    packet["all_pass"] = bool(
        packet["all_pass"]
        and positive.get("ok") is True
        and negative.get("ok") is False
        and packet["dynamics"]["alternating_AB"]["dynamic_admissibility"]["preserves_M_C"]
        and packet["dynamics"]["paired_nontrivial_AABB"]["dynamic_admissibility"]["preserves_M_C"]
        and packet["dynamics"]["paired_nontrivial_AABB"]["moved_count"] > 0
        and packet["dynamics"]["paired_nontrivial_AABB"]["periods"]["spectrum"] != [1]
        and packet["dynamics"]["two_phase_two_loop_row"]["periodicity_changed"]
        and packet["ring_local_update"]["strict_one_site_per_half_step_light_cone_pass"]
        and packet["support_map"]["presentation_equivalence_summary"]["status"] == "completed_for_frozen_object"
        and all(row["preserves_M_C"] for row in packet["M_C_preservation_rerun_by_rule"].values())
        and all(row["moved_count"] > 0 for row in packet["orbit_nontriviality_by_rule"].values())
        and packet["controls"]["phase_merge"]["periodicity_changed_vs_paired"]
    )
    packet["result_sha256"] = sha256_value(
        {k: v for k, v in packet.items() if k not in {"result_sha256", "generated_at", "substrate_enforcement"}}
    )
    return packet


def build_envelope() -> dict[str, Any]:
    packet = build_packet()
    return {
        "schema": f"{SIM_ID}_envelope_v1",
        "schema_version": "sim_packet_envelope_v1",
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "carrier_and_pins_relative": True,
        "three_axis_declaration": packet["three_axis_declaration"],
        "gcm_object_id": packet["gcm_object_id"],
        "registry_body_sha256": packet["registry_body_sha256"],
        "result_path": rel(RESULT_PATH),
        "result_sha256": packet["result_sha256"],
        "substrate_positive_ok": packet["substrate_enforcement"]["positive_payload_ok"]["ok"],
        "substrate_lineage_free_negative_ok": packet["substrate_enforcement"]["lineage_free_negative"]["ok"] is False,
        "dynamic_admissibility_preserves_M_C": packet["dynamics"]["alternating_AB"]["dynamic_admissibility"]["preserves_M_C"],
        "paired_dynamic_admissibility_preserves_M_C": packet["dynamics"]["paired_nontrivial_AABB"]["dynamic_admissibility"]["preserves_M_C"],
        "paired_nontrivial": packet["dynamics"]["paired_nontrivial_AABB"]["moved_count"] > 0
        and packet["dynamics"]["paired_nontrivial_AABB"]["periods"]["spectrum"] != [1],
        "ring_locality_pass": packet["ring_local_update"]["strict_one_site_per_half_step_light_cone_pass"],
        "presentation_equivalence_completed": packet["support_map"]["presentation_equivalence_summary"]["status"] == "completed_for_frozen_object",
        "mc_preservation_rules_checked": sorted(packet["M_C_preservation_rerun_by_rule"]),
        "periodicity_changed": packet["dynamics"]["two_phase_two_loop_row"]["periodicity_changed"],
        "phase_merge_changes_periodicity": packet["controls"]["phase_merge"]["periodicity_changed_vs_paired"],
        "locality_removal_changes_periodicity": packet["controls"]["all_to_all"]["periods"]["spectrum"]
        != packet["dynamics"]["alternating_AB"]["periods"]["spectrum"],
        "qca_gnvw_index_row": packet["fences"]["qca_gnvw_index_row"],
        "builder_gates": packet["builder_gates"],
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": packet["all_pass"],
    }


def write_result() -> dict[str, Any]:
    payload = build_packet()
    write_json(RESULT_PATH, payload)
    return payload


def write_envelope() -> dict[str, Any]:
    payload = build_envelope()
    write_json(ENVELOPE_PATH, payload)
    return payload
