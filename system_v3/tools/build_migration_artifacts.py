#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    root = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet")
    v2_pack = root / "system_v2/specs/system_spec_pack_v2"
    v2_work = root / "system_v2/work/system_specs"
    v3_specs = root / "system_v3/specs"
    reports = v3_specs / "reports"

    v2_pack_files = sorted([p.name for p in v2_pack.glob("*.md")])
    v2_work_files = sorted([p.name for p in v2_work.glob("*.md")])
    v3_files = sorted([p.name for p in v3_specs.glob("*.md") if p.name[0:2].isdigit()])

    # Deterministic hand mapping for known surfaces.
    merge_map: Dict[str, List[str]] = {
        # v2 pack mappings
        "00_MANIFEST.md": ["00_MANIFEST.md", "01_REQUIREMENTS_LEDGER.md"],
        "01_OVERVIEW.md": ["01_REQUIREMENTS_LEDGER.md", "08_PIPELINE_AND_STATE_FLOW_SPEC.md"],
        "02_THREADS_AND_BOOT.md": ["01_REQUIREMENTS_LEDGER.md", "03_B_KERNEL_SPEC.md", "04_A0_COMPILER_SPEC.md", "05_A1_STRATEGY_AND_REPAIR_SPEC.md", "07_A2_OPERATIONS_SPEC.md"],
        "03_B_ARTIFACTS_AND_FENCES.md": ["03_B_KERNEL_SPEC.md"],
        "04_CANON_STATE_SCHEMA.md": ["03_B_KERNEL_SPEC.md", "08_PIPELINE_AND_STATE_FLOW_SPEC.md"],
        "05_EVIDENCE_SIMS_NEGATIVE.md": ["06_SIM_EVIDENCE_AND_TIERS_SPEC.md"],
        "06_GRAVEYARD_AND_ALTERNATIVES.md": ["03_B_KERNEL_SPEC.md", "06_SIM_EVIDENCE_AND_TIERS_SPEC.md"],
        "07_DOC_SYSTEM_AND_SHARDING.md": ["07_A2_OPERATIONS_SPEC.md", "09_CONFORMANCE_AND_REDUNDANCY_GATES.md"],
        "08_MODEL_SWITCH_PROTOCOL.md": ["07_A2_OPERATIONS_SPEC.md"],
        "09_A1_STRATEGY_DECLARATION.md": ["05_A1_STRATEGY_AND_REPAIR_SPEC.md", "04_A0_COMPILER_SPEC.md"],
        "10_TRANSLATOR_BOUNDARY_AND_POLICY.md": ["07_A2_OPERATIONS_SPEC.md", "04_A0_COMPILER_SPEC.md"],
        "11_PROVENANCE_CHAIN_AND_REPLAY.md": ["08_PIPELINE_AND_STATE_FLOW_SPEC.md", "09_CONFORMANCE_AND_REDUNDANCY_GATES.md"],
        "12_TERM_COMPOSITION_AND_RATCHET_COMPLETENESS.md": ["03_B_KERNEL_SPEC.md", "06_SIM_EVIDENCE_AND_TIERS_SPEC.md"],
        "13_A2_YAML_USAGE_AND_COMPACTION.md": ["07_A2_OPERATIONS_SPEC.md"],
        "14_DO_NOT_DO_AND_FORBIDDEN_MOVES.md": ["09_CONFORMANCE_AND_REDUNDANCY_GATES.md", "01_REQUIREMENTS_LEDGER.md"],
        "15_AUDIT_GATES_AND_SUCCESS_CRITERIA.md": ["09_CONFORMANCE_AND_REDUNDANCY_GATES.md", "06_SIM_EVIDENCE_AND_TIERS_SPEC.md"],
        "16_A2_PERSISTENT_BRAIN_SCHEMA.md": ["07_A2_OPERATIONS_SPEC.md"],
        "17_A1_REPAIR_LOOP_AND_WIGGLE_PROTOCOL.md": ["05_A1_STRATEGY_AND_REPAIR_SPEC.md"],
        "18_A1_A2_CONFORMANCE_CHECKLIST.md": ["09_CONFORMANCE_AND_REDUNDANCY_GATES.md"],
        "19_SIM_TIER_ARCHITECTURE.md": ["06_SIM_EVIDENCE_AND_TIERS_SPEC.md"],
        "20_SIM_PROMOTION_AND_MASTER_SIM.md": ["06_SIM_EVIDENCE_AND_TIERS_SPEC.md"],
        "21_SYSTEM_REQUIREMENTS_LEDGER.md": ["01_REQUIREMENTS_LEDGER.md"],
        "22_SPEC_COVERAGE_MATRIX.md": ["02_OWNERSHIP_MAP.md", "10_INITIAL_AUDIT_REPORT.md"],
        # v2 work mappings
        "A0_CONTRACT.md": ["04_A0_COMPILER_SPEC.md"],
        "A1_DESIGN.md": ["05_A1_STRATEGY_AND_REPAIR_SPEC.md"],
        "A2_DESIGN.md": ["07_A2_OPERATIONS_SPEC.md"],
        "A2_PROTOCOL.md": ["07_A2_OPERATIONS_SPEC.md"],
        "B_ACCEPTED_CONTAINERS.md": ["03_B_KERNEL_SPEC.md"],
        "B_FENCES.md": ["03_B_KERNEL_SPEC.md"],
        "DOC_ENTROPY_REGISTRY.md": ["11_MIGRATION_HANDOFF_SPEC.md"],
        "GOVERNANCE.md": ["09_CONFORMANCE_AND_REDUNDANCY_GATES.md"],
        "INDEX.md": ["00_MANIFEST.md", "11_MIGRATION_HANDOFF_SPEC.md"],
        "JARGON_GATE.md": ["03_B_KERNEL_SPEC.md", "07_A2_OPERATIONS_SPEC.md"],
        "PIPELINE_SPEC.md": ["08_PIPELINE_AND_STATE_FLOW_SPEC.md"],
        "PRO_GLOSSARY_OVERLAY.md": ["07_A2_OPERATIONS_SPEC.md"],
        "STATE_SCHEMA.md": ["08_PIPELINE_AND_STATE_FLOW_SPEC.md", "03_B_KERNEL_SPEC.md"],
        "THREAD_BOUNDARIES.md": ["01_REQUIREMENTS_LEDGER.md"],
    }

    inventory = []
    mapping = []
    unknowns = []

    def classify(file_name: str, source_group: str) -> None:
        targets = merge_map.get(file_name, [])
        if targets:
            status = "MERGED_INTO_V3"
        else:
            status = "KEEP_REFERENCE"
            unknowns.append(
                {
                    "source_group": source_group,
                    "source_file": file_name,
                    "reason": "no deterministic merge target in mapping table",
                }
            )
        inventory.append(
            {
                "source_group": source_group,
                "source_file": file_name,
                "status": status,
            }
        )
        mapping.append(
            {
                "source_group": source_group,
                "source_file": file_name,
                "target_v3_files": targets,
            }
        )

    for name in v2_pack_files:
        classify(name, "v2_pack")
    for name in v2_work_files:
        classify(name, "v2_work")

    status_counts = {}
    for row in inventory:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1

    promotion_report = {
        "migration_ready": len(unknowns) == 0,
        "status_counts": status_counts,
        "v2_pack_file_count": len(v2_pack_files),
        "v2_work_file_count": len(v2_work_files),
        "v3_spec_file_count": len(v3_files),
        "unknown_count": len(unknowns),
        "blocking_reasons": [
            "unknown mappings present" if unknowns else ""
        ],
    }
    promotion_report["blocking_reasons"] = [
        r for r in promotion_report["blocking_reasons"] if r
    ]

    write_json(reports / "migration_inventory.json", sorted(inventory, key=lambda x: (x["source_group"], x["source_file"])))
    write_json(reports / "migration_mapping.json", sorted(mapping, key=lambda x: (x["source_group"], x["source_file"])))
    write_json(reports / "migration_unknowns.json", sorted(unknowns, key=lambda x: (x["source_group"], x["source_file"])))
    write_json(reports / "migration_promotion_report.json", promotion_report)

    print(
        json.dumps(
            {
                "migration_ready": promotion_report["migration_ready"],
                "unknown_count": promotion_report["unknown_count"],
                "status_counts": status_counts,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
