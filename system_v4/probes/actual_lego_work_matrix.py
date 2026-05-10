#!/usr/bin/env python3
"""Build a machine-readable work matrix for the actual lego registry.

The registry markdown preserves the owner's source labels.  This matrix keeps
those labels, then adds the current machine evidence surface so controller
work can distinguish stale source coverage from actual receipts.
"""

from __future__ import annotations

import json
import hashlib
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"

REGISTRY_PATH = RESULTS_DIR / "actual_lego_registry.json"
NORMALIZATION_QUEUE_PATH = RESULTS_DIR / "actual_lego_normalization_queue.json"
COUPLING_QUEUE_PATH = RESULTS_DIR / "lego_batch_queue.json"
INVENTORY_PATH = PROJECT_DIR / "system_v5" / "evidence" / "sim_inventory_index.json"
OUT_PATH = RESULTS_DIR / "actual_lego_work_matrix.json"
PROCESS_AUDIT_PATH = RESULTS_DIR / "actual_lego_process_receipt_audit.json"
INDEXED_AUDIT_PATH = RESULTS_DIR / "actual_lego_indexed_receipt_audit.json"
COUPLING_AUDIT_PATH = RESULTS_DIR / "actual_lego_coupling_receipt_audit.json"


NONCLASSICAL_ADJACENT_TOOLS = {
    "pytorch",
    "pyg",
    "qutip",
    "qiskit",
    "clifford",
    "gudhi",
    "toponetx",
    "xgi",
    "geomstats",
    "e3nn",
}
BRIDGE_TOOLS = {
    "sympy",
    "z3",
    "cvc5",
    "rustworkx",
    "xgi",
    "toponetx",
    "gudhi",
    "networkx",
}
CLASSICAL_TOOLS = {"numpy", "scipy", "sympy", "networkx"}

LEGO_PROBE_ALIASES = {
    "holonomy_geometry": "sim_pure_lego_wilczek_zee_holonomy.py",
    "transport_geometry": "sim_parallel_transport_s2_classical.py",
    "hopf_map_s3_to_s2": "sim_hopf_base_section_phase_recovery.py",
    "hopf_connection_form": "sim_hopf_connection_curvature_operators.py",
    "berry_holonomy": "sim_pure_lego_berry_phase_u1_abelian.py",
    "weyl_chirality_pair": "sim_weyl_chirality_bipartite.py",
    "composition_order_noncommutation": "sim_axiom_n01_composition_order_distinguishes.py",
    "composition_order_sensitivity": "sim_axiom_n01_composition_order_distinguishes.py",
    "channel_cptp_map": "sim_lego_cptp_channel_family.py",
    "kraus_operator_sum": "sim_kraus_operator_sum_classical.py",
    "lindbladian_evolution": "sim_lindbladian_evolution_classical.py",
    "werner_local_structure": "sim_pyg_dynamic_edge_werner.py",
}

LEGO_RESULT_ALIASES = {
    "holonomy_geometry": "wilczek_zee_holonomy_results.json",
    "berry_holonomy": "berry_phase_u1_abelian_results.json",
}


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))


def result_name_for_probe(probe: str | None) -> str | None:
    if not probe or not probe.endswith(".py"):
        return None
    stem = probe[:-3]
    if stem.startswith("sim_"):
        stem = stem[4:]
    return f"{stem}_results.json"


def result_path(result_name: str | None) -> Path | None:
    if not result_name:
        return None
    return RESULTS_DIR / result_name


def inventory_by_stem(inventory: dict) -> dict[str, dict]:
    return {row.get("stem", ""): row for row in inventory.get("rows", [])}


def stem_from_probe(probe: str | None) -> str | None:
    if not probe:
        return None
    stem = Path(probe).stem
    return stem


def stem_from_result_name(result_name: str | None) -> str | None:
    if not result_name:
        return None
    stem = result_name.removesuffix(".json")
    if stem.endswith("_results"):
        stem = stem[: -len("_results")]
    if not stem.startswith("sim_"):
        stem = f"sim_{stem}"
    return stem


def load_result_summary(result_name: str | None) -> dict:
    path = result_path(result_name)
    if path is None or not path.exists():
        return {"result_exists": False}
    data = read_json(path)
    raw = path.read_bytes()
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    all_pass = data.get("all_pass")
    if all_pass is None:
        all_pass = summary.get("all_pass")
    return {
        "result_exists": True,
        "result_path": str(path),
        "result_sha256": hashlib.sha256(raw).hexdigest(),
        "classification": data.get("classification"),
        "all_pass": all_pass,
        "has_tool_manifest": bool(data.get("tool_manifest") or data.get("TOOL_MANIFEST")),
        "has_tool_integration_depth": bool(
            data.get("tool_integration_depth") or data.get("TOOL_INTEGRATION_DEPTH")
        ),
        "summary": summary,
    }


def coverage_slots(lego_id: str, section: str, inv_row: dict, result: dict) -> dict:
    families = set(inv_row.get("families", []))
    raw_tools = inv_row.get("tools") or {}
    tools = set(raw_tools.keys()) if isinstance(raw_tools, dict) else set(raw_tools)
    load_bearing = set(inv_row.get("load_bearing_tools", []))
    text = f"{lego_id} {section}".lower()

    classical = bool(
        result.get("classification") == "classical_baseline"
        or load_bearing & CLASSICAL_TOOLS
        or tools & CLASSICAL_TOOLS
    )
    bridge = bool(load_bearing & BRIDGE_TOOLS or tools & {"z3", "cvc5"})
    nonclassical_adjacent = bool(load_bearing & NONCLASSICAL_ADJACENT_TOOLS)
    entropy = "entropy_information" in families or "entropy" in text or "information" in text
    operator = "channel_operator" in families or any(tok in text for tok in ["operator", "channel", "pauli", "clifford", "commutator"])
    topology = "graph_topology" in families or "geometry_gstack_gtower" in families or any(
        tok in text for tok in ["topology", "graph", "geometry", "torus", "sphere", "bures", "fubini"]
    )
    order_variant = "graveyard_negative" in families or any(
        tok in text for tok in ["order", "variant", "graveyard", "falsifier"]
    )
    tool_coverage = bool(load_bearing)

    return {
        "classical_baseline": classical,
        "bridge_tool_fit": bridge,
        "nonclassical_adjacent_tool_fit": nonclassical_adjacent,
        "entropy": entropy,
        "operator": operator,
        "topology": topology,
        "order_variant_graveyard": order_variant,
        "tool_coverage": tool_coverage,
    }


def stage_gate_level(inv_row: dict, result: dict, slots: dict) -> str:
    if not result.get("result_exists"):
        return "0_missing_receipt"
    if result.get("all_pass") is False:
        return "0_result_failed"
    if result.get("all_pass") is not True:
        return "1_exists_pass_unknown"
    if not inv_row.get("load_bearing_tools"):
        return "2_passes_local_tool_depth_thin"
    if slots.get("order_variant_graveyard"):
        return "3_order_variant_graveyard_receipt"
    if slots.get("entropy") or slots.get("operator") or slots.get("topology"):
        return "3_entropy_operator_topology_receipt"
    if slots.get("bridge_tool_fit") or slots.get("nonclassical_adjacent_tool_fit"):
        return "2_tool_fit_receipt"
    return "1_passes_local_rerun"


def coverage_label_diverges(source_label: str | None, machine_label: str | None) -> bool:
    """Return true only for actionable source/machine coverage disagreement."""
    if source_label == machine_label:
        return False
    if source_label == "canonical by process" and machine_label == "covered":
        return False
    return True


def next_action(
    row: dict,
    inv_row: dict,
    result: dict,
    coupling_rows: list[dict],
    process_audit_row: dict | None = None,
    indexed_audit_row: dict | None = None,
    coupling_audit_by_result: dict[str, dict] | None = None,
) -> dict:
    machine_coverage = row.get("machine_current_coverage") or row.get("current_coverage")
    source_coverage = row.get("current_coverage")
    inventory_status = inv_row.get("inventory_status")

    if machine_coverage == "blocked_as_late_surface":
        return {"status": "blocked", "reason": "late_surface_stage_gate", "packet": None}
    if machine_coverage == "canonical by process":
        if result.get("result_exists"):
            if result.get("all_pass") is False:
                return {"status": "result_failing_repair_needed", "reason": "linked result explicitly reports all_pass false", "packet": row.get("machine_best_probe")}
            if process_audit_row:
                if process_audit_row.get("hard_finding_count", 0):
                    return {
                        "status": "source_process_receipt_hard_blocked",
                        "reason": "source process receipt audit found hard validator findings",
                        "packet": row.get("machine_best_probe"),
                    }
                if process_audit_row.get("warning_count", 0):
                    return {
                        "status": "source_process_receipt_boundary_warnings",
                        "reason": "source process receipt is hard-green but still has run-boundary warning fields",
                        "packet": row.get("machine_best_probe"),
                    }
                return {
                    "status": "source_process_receipt_audited",
                    "reason": "source process receipt is hard-green with no validator warnings",
                    "packet": None,
                }
            return {
                "status": "source_process_receipt_linked_audit_needed",
                "reason": "source registry says canonical by process; local receipt is linked but still needs audit/admission boundary checks",
                "packet": row.get("machine_best_probe"),
            }
        return {
            "status": "source_process_claim_needs_receipt_link",
            "reason": "source registry says canonical by process but no local result is linked in the machine overlay",
            "packet": row.get("machine_best_probe"),
        }
    if machine_coverage == "passes local rerun":
        return {
            "status": "local_rerun_needs_canonical_receipt",
            "reason": "local rerun is useful but below canonical/admission status",
            "packet": row.get("machine_best_probe"),
        }
    if not result.get("result_exists"):
        return {"status": "needs_probe_or_result_repair", "reason": "machine result missing", "packet": row.get("machine_best_probe")}
    if result.get("all_pass") is False:
        return {"status": "result_failing_repair_needed", "reason": "linked result explicitly reports all_pass false", "packet": row.get("machine_best_probe")}
    if inventory_status == "legacy_result_or_repair_needed":
        return {"status": "repair", "reason": "inventory marks legacy result or repair needed", "packet": row.get("machine_best_probe")}
    if inventory_status == "contract_shaped_but_tool_depth_thin":
        return {"status": "audit_tool_depth", "reason": "result exists but load-bearing tool depth is thin", "packet": row.get("machine_best_probe")}
    ready_couplings = [c for c in coupling_rows if c.get("ready")]
    if ready_couplings:
        receipt_linked = []
        for coupling in ready_couplings:
            coupling_result_name = result_name_for_probe(coupling.get("recommended_sim"))
            coupling_result = load_result_summary(coupling_result_name)
            if coupling_result.get("result_exists") and coupling_result.get("all_pass") is True:
                receipt_linked.append((coupling, coupling_result, coupling_result_name))
        if receipt_linked:
            def coupling_priority(item: tuple[dict, dict, str]) -> tuple[int, int, int]:
                coupling, coupling_result, coupling_result_name = item
                audit = (coupling_audit_by_result or {}).get(coupling_result_name, {})
                if audit.get("audit_status") == "hard_green_closure_candidate":
                    audit_rank = 0
                elif coupling_result.get("summary", {}).get("closure_candidate") is True:
                    audit_rank = 0
                elif audit:
                    audit_rank = 1
                else:
                    audit_rank = 2
                classification_rank = 0 if coupling_result.get("classification") != "supporting" else 1
                status_rank = 0 if coupling.get("status") != "supporting_only" else 1
                return (audit_rank, classification_rank, status_rank)

            receipt_linked.sort(key=coupling_priority)
            coupling, coupling_result, coupling_result_name = receipt_linked[0]
            coupling_audit = (coupling_audit_by_result or {}).get(coupling_result_name)
            if coupling_audit:
                if coupling_audit.get("hard_finding_count", 0):
                    return {
                        "status": "coupling_receipt_hard_blocked",
                        "reason": "linked coupling receipt audit found hard validator findings",
                        "packet": coupling.get("recommended_sim"),
                        "coupling_result_classification": coupling_result.get("classification"),
                    }
                if coupling_audit.get("warning_count", 0):
                    return {
                        "status": "coupling_receipt_boundary_warnings",
                        "reason": "linked coupling receipt is hard-green but still has boundary warnings",
                        "packet": coupling.get("recommended_sim"),
                        "coupling_result_classification": coupling_result.get("classification"),
                    }
                if coupling_audit.get("audit_status") == "hard_green_closure_candidate":
                    return {
                        "status": "coupling_receipt_audited_closure_candidate",
                        "reason": "linked coupling receipt is hard-green and closure-candidate, but still not promoted",
                        "packet": coupling.get("recommended_sim"),
                        "coupling_result_classification": coupling_result.get("classification"),
                    }
                return {
                    "status": "coupling_receipt_audited_not_closure_grade",
                    "reason": "linked coupling receipt is hard-green but supporting/not closure-grade; keep as evidence only",
                    "packet": coupling.get("recommended_sim"),
                    "coupling_result_classification": coupling_result.get("classification"),
                }
            if coupling.get("status") == "supporting_only":
                return {
                    "status": "coupling_supporting_receipt_indexed",
                    "reason": (
                        "ready coupling packet has a fresh all_pass supporting receipt; "
                        "closure-grade coupling still blocked by its stop rule"
                    ),
                    "packet": coupling.get("recommended_sim"),
                    "coupling_result_classification": coupling_result.get("classification"),
                }
            return {
                "status": "coupling_receipt_linked_audit_needed",
                "reason": (
                    "ready coupling/coexistence packet has a fresh all_pass receipt; "
                    "audit/ablation boundary still required before promotion"
                ),
                "packet": coupling.get("recommended_sim"),
                "coupling_result_classification": coupling_result.get("classification"),
            }
        return {
            "status": "coupling_available",
            "reason": "one or more bounded coupling packets reference this lego family",
            "packet": ready_couplings[0].get("recommended_sim"),
        }
    if source_coverage == "canonical by process" and machine_coverage == "covered":
        if indexed_audit_row:
            if indexed_audit_row.get("hard_finding_count", 0):
                return {
                    "status": "indexed_receipt_hard_blocked",
                    "reason": "indexed receipt audit found hard validator findings",
                    "packet": row.get("machine_best_probe"),
                }
            if indexed_audit_row.get("warning_count", 0):
                return {
                    "status": "indexed_receipt_boundary_warnings",
                    "reason": "source process label is not stale; hard-green receipt still has run-boundary warning fields",
                    "packet": row.get("machine_best_probe"),
                }
            return {
                "status": "indexed_receipt_audited",
                "reason": "source process label is not stale; machine receipt is hard-green with no validator warnings",
                "packet": None,
            }
        return {
            "status": "indexed",
            "reason": "source process label is not stale; machine receipt covers the row",
            "packet": None,
        }
    if machine_coverage == "covered" and source_coverage != "covered":
        if result.get("all_pass") is not True:
            return {
                "status": "source_label_stale_pass_unknown",
                "reason": "machine receipt covers row but result pass status is not explicit",
                "packet": row.get("machine_best_probe"),
            }
        return {"status": "source_label_stale", "reason": "machine receipt covers row but source coverage label is older", "packet": None}
    if machine_coverage == "covered" and result.get("all_pass") is not True:
        return {
            "status": "result_pass_unknown_audit_needed",
            "reason": "machine says covered but linked result does not expose all_pass true",
            "packet": row.get("machine_best_probe"),
        }
    if indexed_audit_row:
        if indexed_audit_row.get("hard_finding_count", 0):
            return {
                "status": "indexed_receipt_hard_blocked",
                "reason": "indexed receipt audit found hard validator findings",
                "packet": row.get("machine_best_probe"),
            }
        if indexed_audit_row.get("warning_count", 0):
            return {
                "status": "indexed_receipt_boundary_warnings",
                "reason": "indexed receipt is hard-green but still has run-boundary warning fields",
                "packet": row.get("machine_best_probe"),
            }
        return {
            "status": "indexed_receipt_audited",
            "reason": "indexed receipt is hard-green with no validator warnings",
            "packet": None,
        }
    return {"status": "indexed", "reason": "receipt indexed; no immediate missing packet inferred", "packet": None}


def main() -> int:
    registry = read_json(REGISTRY_PATH)
    normalization = read_json(NORMALIZATION_QUEUE_PATH)
    coupling_queue = read_json(COUPLING_QUEUE_PATH)
    inventory = read_json(INVENTORY_PATH)
    process_audit = read_json(PROCESS_AUDIT_PATH)
    indexed_audit = read_json(INDEXED_AUDIT_PATH)
    coupling_audit = read_json(COUPLING_AUDIT_PATH)

    inv_by_stem = inventory_by_stem(inventory)
    norm_by_id = {row.get("lego_id"): row for row in normalization.get("rows", [])}
    coupling_by_family: dict[str, list[dict]] = defaultdict(list)
    coupling_by_probe: dict[str, list[dict]] = defaultdict(list)
    process_audit_by_id = {row.get("lego_id"): row for row in process_audit.get("rows", [])}
    indexed_audit_by_id = {row.get("lego_id"): row for row in indexed_audit.get("rows", [])}
    coupling_audit_by_result = {
        Path(row.get("coupling_result", "")).name: row
        for row in coupling_audit.get("rows", [])
        if row.get("coupling_result")
    }
    for row in coupling_queue.get("rows", []):
        coupling_by_family[row.get("lego_or_pair")].append(row)
        for probe in row.get("depends_on", []):
            if probe:
                coupling_by_probe[probe].append(row)
        sim = row.get("recommended_sim")
        if sim:
            coupling_by_probe[sim].append(row)

    rows = []
    for reg_row in registry.get("rows", []):
        lego_id = reg_row.get("lego_id")
        norm_row = norm_by_id.get(lego_id, {})
        probe = reg_row.get("machine_best_probe") or norm_row.get("reusable_probe")
        result_name = (
            reg_row.get("machine_best_result")
            or norm_row.get("existing_result_json")
            or result_name_for_probe(probe)
        )
        if not probe and lego_id in LEGO_PROBE_ALIASES:
            alias_probe = LEGO_PROBE_ALIASES[lego_id]
            if (SCRIPT_DIR / alias_probe).exists():
                probe = alias_probe
                result_name = result_name_for_probe(probe)
        if lego_id in LEGO_RESULT_ALIASES:
            alias_result = LEGO_RESULT_ALIASES[lego_id]
            if result_path(alias_result) and result_path(alias_result).exists():
                result_name = alias_result
        if result_name and not (result_path(result_name) and result_path(result_name).exists()) and probe:
            probe_stem_result = f"{stem_from_probe(probe)}_results.json"
            if result_path(probe_stem_result) and result_path(probe_stem_result).exists():
                result_name = probe_stem_result
        if not result_name and lego_id:
            lego_result_name = f"{lego_id}_results.json"
            if result_path(lego_result_name) and result_path(lego_result_name).exists():
                result_name = lego_result_name
        if not probe and lego_id:
            lego_probe = f"sim_{lego_id}.py"
            if (SCRIPT_DIR / lego_probe).exists():
                probe = lego_probe
        stem = stem_from_probe(probe) or stem_from_result_name(result_name) or ""
        inv_row = inv_by_stem.get(stem, {})
        result = load_result_summary(result_name)
        couplings = []
        couplings.extend(coupling_by_family.get(lego_id, []))
        if probe:
            couplings.extend(coupling_by_probe.get(probe, []))
        if result_name:
            coupling_stem = stem_from_result_name(result_name)
            coupling_probe = f"{coupling_stem}.py" if coupling_stem else None
            couplings.extend(coupling_by_probe.get(coupling_probe, []))
        deduped_couplings = []
        seen_task_ids = set()
        for coupling in couplings:
            task_id = coupling.get("task_id")
            if task_id in seen_task_ids:
                continue
            seen_task_ids.add(task_id)
            deduped_couplings.append(coupling)
        couplings = deduped_couplings
        slots = coverage_slots(lego_id or "", reg_row.get("section", ""), inv_row, result)
        stage = stage_gate_level(inv_row, result, slots)
        action = next_action(
            reg_row,
            inv_row,
            result,
            couplings,
            process_audit_by_id.get(lego_id),
            indexed_audit_by_id.get(lego_id),
            coupling_audit_by_result,
        )
        source_label = reg_row.get("current_coverage")
        machine_label = reg_row.get("machine_current_coverage")
        stale_label_risk = coverage_label_diverges(source_label, machine_label)
        negative_evidence = bool(
            "graveyard_negative" in inv_row.get("families", [])
            or any(tok in f"{lego_id} {reg_row.get('section', '')}".lower() for tok in ["graveyard", "falsifier", "rejection"])
        )
        admitted = bool(inv_row.get("admitted"))
        promotion_allowed = False
        promotion_blocker = (
            "matrix boundary: work index only, not admission or promotion"
            if not admitted
            else "admitted stem still requires exact admission receipt and current contract verification before promotion"
        )

        rows.append(
            {
                "lego_id": lego_id,
                "lego_name": reg_row.get("lego_name"),
                "section": reg_row.get("section"),
                "lego_type": reg_row.get("lego_type"),
                "concrete_math": reg_row.get("concrete_math"),
                "minimal_honest_sim": reg_row.get("minimal_honest_sim"),
                "source_docs": reg_row.get("source_docs"),
                "source_path": str(REGISTRY_PATH),
                "source_label": source_label,
                "source_label_date": registry.get("generated_at"),
                "source_current_coverage": source_label,
                "registry_current_coverage": source_label,
                "machine_current_coverage": machine_label,
                "machine_mapping_confidence": reg_row.get("machine_mapping_confidence") or norm_row.get("mapping_confidence"),
                "machine_needs_new_probe": reg_row.get("machine_needs_new_probe") if reg_row.get("machine_needs_new_probe") is not None else norm_row.get("needs_new_probe"),
                "machine_best_probe": probe,
                "machine_best_result": result_name,
                "result_exists": result["result_exists"],
                "result_path": result.get("result_path"),
                "result_sha256": result.get("result_sha256"),
                "result_sha256_verified": False,
                "result_classification": result.get("classification"),
                "result_all_pass": result.get("all_pass"),
                "result_paths": inv_row.get("result_paths", []),
                "result_count": inv_row.get("result_count", 0),
                "result_classifications": inv_row.get("result_classifications", []),
                "inventory_gap": not bool(inv_row),
                "source_has_tool_manifest": inv_row.get("source_has_tool_manifest"),
                "source_has_tool_integration_depth": inv_row.get("source_has_tool_integration_depth"),
                "normalization_priority": norm_row.get("priority"),
                "reusable_probe": norm_row.get("reusable_probe"),
                "existing_result_json": norm_row.get("existing_result_json"),
                "existing_result_classification": norm_row.get("existing_result_classification"),
                "existing_result_all_pass": norm_row.get("existing_result_all_pass"),
                "result_truth_warning": norm_row.get("result_truth_warning"),
                "tool_pressure": norm_row.get("tool_pressure", []),
                "stop_rule": norm_row.get("stop_rule"),
                "inventory_stem": stem,
                "admitted": admitted,
                "admission_status": inv_row.get("admission_status", "no_admission"),
                "inventory_status": inv_row.get("inventory_status"),
                "families": inv_row.get("families", []),
                "load_bearing_tools": inv_row.get("load_bearing_tools", []),
                "coverage_slots": slots,
                "coverage_slot_count": sum(1 for value in slots.values() if value),
                "stage_gate_level": stage,
                "coupling_task_ids": [c.get("task_id") for c in couplings],
                "batch_task_id": couplings[0].get("task_id") if couplings else None,
                "target_stage": couplings[0].get("target_stage") if couplings else None,
                "depends_on": couplings[0].get("depends_on") if couplings else [],
                "recommended_sim": couplings[0].get("recommended_sim") if couplings else None,
                "ready": couplings[0].get("ready") if couplings else None,
                "blocked_by": couplings[0].get("blocked_by") if couplings else [],
                "blocked_from_assembly": couplings[0].get("blocked_from_assembly") if couplings else False,
                "next_action": action,
                "receipt_status": "local_result_present" if result["result_exists"] else "missing_or_unlinked",
                "queue_status_raw": couplings[0] if couplings else None,
                "queue_status_normalized": "ready" if couplings and couplings[0].get("ready") else ("blocked" if couplings else "not_in_coupling_queue"),
                "stale_label_risk": stale_label_risk,
                "use_as_negative_evidence": negative_evidence,
                "boundary_note": "inventory/work-matrix only; not admission or promotion",
                "promotion_allowed": promotion_allowed,
                "promotion_blocker": promotion_blocker,
                "evidence_boundary": "local receipt/index evidence only unless separate admission receipt verifies exact result and current contract",
                "claim_ceiling": "lego_work_matrix_only_not_admission",
            }
        )

    next_counts: dict[str, int] = defaultdict(int)
    machine_counts: dict[str, int] = defaultdict(int)
    slot_counts: dict[str, int] = defaultdict(int)
    for row in rows:
        next_counts[row["next_action"]["status"]] += 1
        machine_counts[row.get("machine_current_coverage") or "unknown"] += 1
        for slot, value in row["coverage_slots"].items():
            if value:
                slot_counts[slot] += 1

    report = {
        "name": "actual_lego_work_matrix",
        "schema": "actual_lego_work_matrix.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "boundary": "work_matrix_only_not_admission_or_promotion",
        "inputs": {
            "registry": str(REGISTRY_PATH),
            "normalization_queue": str(NORMALIZATION_QUEUE_PATH),
            "coupling_queue": str(COUPLING_QUEUE_PATH),
            "inventory": str(INVENTORY_PATH),
            "coupling_audit": str(COUPLING_AUDIT_PATH),
        },
        "summary": {
            "row_count": len(rows),
            "machine_coverage_counts": dict(sorted(machine_counts.items())),
            "next_action_counts": dict(sorted(next_counts.items())),
            "coverage_slot_counts": dict(sorted(slot_counts.items())),
            "result_exists_count": sum(1 for row in rows if row["result_exists"]),
            "missing_result_count": sum(1 for row in rows if not row["result_exists"]),
            "coupling_linked_row_count": sum(1 for row in rows if row["coupling_task_ids"]),
            "inventory_gap_count": sum(1 for row in rows if row["inventory_gap"]),
            "stale_label_risk_count": sum(1 for row in rows if row["stale_label_risk"]),
            "negative_evidence_row_count": sum(1 for row in rows if row["use_as_negative_evidence"]),
            "promotion_allowed_count": sum(1 for row in rows if row["promotion_allowed"]),
        },
        "rows": rows,
    }
    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
