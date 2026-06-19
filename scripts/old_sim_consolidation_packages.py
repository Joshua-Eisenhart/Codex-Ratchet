#!/usr/bin/env python3
"""Create bounded work packages and Codex TUI prompt cards for old-sim processing.

This script does not move, edit, or delete old sims. It converts the generated
old-sim reuse index into receipt-producing packages that Codex/Hermes workers can
process safely before any controller-owned consolidation or deletion.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_INDEX = Path("system_v5/evidence/old_sim_reuse_index_20260608.json")
DEFAULT_OUT = Path("system_v5/evidence/old_sim_processing/work_packages_20260608.json")
DEFAULT_PROMPT_DIR = Path("system_v5/ops/old_sim_processing/prompts")
DEFAULT_REPORT_DIR = Path("system_v5/ops/old_sim_processing/reports")
DEFAULT_ACTION_DIR = Path("system_v5/evidence/old_sim_processing/actions")

PACKAGE_DEFS: dict[str, dict[str, Any]] = {
    "P00_controller_receipt_and_gates": {
        "codex_route": "controller",
        "mission": "Audit the campaign gates, archive/delete criteria, and worker receipt schema before edits.",
        "families_any": [],
        "buckets_any": ["repo_inventory_or_validator_scripts", "current_machine_indexes", "v5_docs_and_ledgers"],
        "reuse_any": [],
        "max_rows": 180,
    },
    "P01_active_tri_engine_envelopes": {
        "codex_route": "codex1",
        "mission": "Verify current three-engine/scratch envelopes, extract reusable micro-lego patterns, and mark no-promotion ceilings.",
        "families_any": [],
        "buckets_any": ["current_formal_scout_results", "current_julia_carrier_results", "current_formal_scout_sources", "current_julia_carrier_sources"],
        "reuse_any": ["active_three_engine_scratch_template_or_receipt", "scratch_diagnostic_keep_under_no_promotion_ceiling", "formal_scout_revalidate_or_use_as_bounded_pressure"],
        "max_rows": 500,
    },
    "P02_foundation_carrier_geometry_donors": {
        "codex_route": "codex1",
        "mission": "Mine old foundation/carrier/Hopf/Weyl/spinor/Clifford sims into current micro-lego donors and controls.",
        "families_any": ["root_distinguishability", "finitude", "noncommutation_order", "quotient_admissibility", "mc_manifold", "carrier_division_algebra", "associator_nonassoc", "hopf_torus_holonomy", "weyl_spinor_chirality"],
        "buckets_any": ["v4_probe_sources", "v4_a2_state_results", "v4_docs", "read_only_legacy_reference"],
        "reuse_any": ["legacy_translate_to_micro_lego_or_baseline_control", "archive_mine_for_math_objects_controls_falsifiers"],
        "max_rows": 900,
    },
    "P03_qit_density_entropy_classical_baselines": {
        "codex_route": "codex2",
        "mission": "Mine QIT/density/entropy/Carnot/Szilard/classical-engine sims into side-lane baseline and future rich-tool packets.",
        "families_any": ["qit_density_entanglement", "entropy_classical_engine", "engine_axis_terrain_operator"],
        "buckets_any": ["v4_probe_sources", "v4_a2_state_results", "v4_docs", "read_only_legacy_reference", "v5_docs_and_ledgers"],
        "reuse_any": ["legacy_translate_to_micro_lego_or_baseline_control", "archive_mine_for_math_objects_controls_falsifiers"],
        "max_rows": 900,
    },
    "P04_graph_topology_tool_recipes": {
        "codex_route": "codex1",
        "mission": "Extract graph/topology/tensor tool recipes and convert them into reusable current tool-fuel rows.",
        "families_any": ["graph_topology", "tool_integration"],
        "buckets_any": ["v4_probe_sources", "v4_a2_state_results", "current_formal_scout_sources", "repo_inventory_or_validator_scripts"],
        "reuse_any": ["tool_recipe_or_capability_anchor", "legacy_translate_to_micro_lego_or_baseline_control"],
        "max_rows": 700,
    },
    "P05_proof_symbolic_negative_controls": {
        "codex_route": "codex2",
        "mission": "Extract z3/cvc5/sympy/proof-pressure recipes, failed rows, ablations, and negative-control banks.",
        "families_any": ["proof_symbolic", "noncommutation_order"],
        "buckets_any": ["v4_probe_sources", "v4_a2_state_results", "current_formal_scout_results", "current_formal_scout_sources", "repo_receipts"],
        "reuse_any": ["tool_recipe_or_capability_anchor", "legacy_negative_or_failed_control_mine", "legacy_translate_to_micro_lego_or_baseline_control"],
        "max_rows": 700,
    },
    "P06_bridge_axis_physics_graveyard": {
        "codex_route": "codex2",
        "mission": "Separate bridge/Axis0/physics-facing old sims into donor controls, graveyard rows, and blocked future gates without promotion.",
        "families_any": ["bridge_physics", "external_archive"],
        "buckets_any": ["v4_probe_sources", "v4_a2_state_results", "v4_docs", "read_only_legacy_reference", "grok_sim_archive", "v5_doc_archive"],
        "reuse_any": ["legacy_translate_to_micro_lego_or_baseline_control", "archive_mine_for_math_objects_controls_falsifiers"],
        "max_rows": 900,
    },
    "P07_duplicate_lineage_and_archive_candidates": {
        "codex_route": "codex1",
        "mission": "Audit duplicate basenames, lineage hazards, and archive/delete candidates. Propose moves only; do not delete.",
        "families_any": [],
        "buckets_any": ["v4_a2_state_results", "v4_probe_sources", "read_only_legacy_reference", "v5_doc_archive", "other_result_or_index_json", "other_sim_source", "other_doc_or_reference"],
        "reuse_any": ["classify_before_reuse", "doc_index_or_authority_surface"],
        "max_rows": 900,
    },
    "P08_unclassified_and_workbench_triage": {
        "codex_route": "codex2",
        "mission": "Triage unclassified, workbench, and miscellaneous surfaces into keep/rebuild/archive/delete-review buckets.",
        "families_any": ["unclassified"],
        "buckets_any": ["workbench_or_tmp", "other_result_or_index_json", "other_sim_source", "other_doc_or_reference"],
        "reuse_any": ["classify_before_reuse"],
        "max_rows": 900,
    },
}

ACTIONS_SCHEMA = {
    "schema": "old_sim_action_manifest.v1",
    "fields": [
        "source_path",
        "old_role",
        "recommended_action",
        "safe_current_reuse",
        "replacement_or_fuel_path",
        "delete_or_archive_gate",
        "required_validator",
        "claim_ceiling",
        "notes",
    ],
    "allowed_recommended_actions": [
        "keep_current",
        "mine_into_fuel_bank",
        "rebuild_as_micro_lego",
        "consolidate_duplicate",
        "archive_candidate",
        "delete_candidate_after_replacement_verified",
        "graveyard_keep_as_falsifier",
        "needs_human_review",
    ],
}


def load_index(repo: Path, index_path: Path) -> dict[str, Any]:
    path = index_path if index_path.is_absolute() else repo / index_path
    return json.loads(path.read_text(encoding="utf-8"))


def row_matches(row: dict[str, Any], spec: dict[str, Any]) -> bool:
    families = set(row.get("families") or [])
    bucket = row.get("bucket")
    reuse = row.get("reuse_mode")
    family_ok = not spec["families_any"] or bool(families & set(spec["families_any"]))
    bucket_ok = not spec["buckets_any"] or bucket in set(spec["buckets_any"])
    reuse_ok = not spec["reuse_any"] or reuse in set(spec["reuse_any"])
    return family_ok and bucket_ok and reuse_ok


def thin_row(row: dict[str, Any]) -> dict[str, Any]:
    summary = row.get("json_summary") if isinstance(row.get("json_summary"), dict) else {}
    return {
        "path": row.get("path"),
        "kind": row.get("kind"),
        "bucket": row.get("bucket"),
        "families": row.get("families"),
        "reuse_mode": row.get("reuse_mode"),
        "classification": summary.get("classification"),
        "all_pass": summary.get("all_pass"),
        "promotion_allowed": summary.get("promotion_allowed"),
        "formal_admission_allowed": summary.get("formal_admission_allowed"),
        "size_bytes": row.get("size_bytes"),
        "mtime": row.get("mtime"),
    }


def build_packages(index: dict[str, Any]) -> dict[str, Any]:
    rows = index.get("rows", [])
    packages: dict[str, Any] = {}
    assigned: dict[str, list[str]] = defaultdict(list)
    for package_id, spec in PACKAGE_DEFS.items():
        selected = [thin_row(row) for row in rows if row_matches(row, spec)]
        selected.sort(key=lambda item: (str(item.get("bucket")), str(item.get("path"))))
        if spec.get("max_rows"):
            selected = selected[: int(spec["max_rows"])]
        packages[package_id] = {
            "package_id": package_id,
            "codex_route": spec["codex_route"],
            "mission": spec["mission"],
            "row_count": len(selected),
            "rows": selected,
            "expected_report": f"system_v5/ops/old_sim_processing/reports/{package_id}.md",
            "expected_action_manifest": f"system_v5/evidence/old_sim_processing/actions/{package_id}_actions.json",
        }
        for item in selected:
            if item.get("path"):
                assigned[str(item["path"])].append(package_id)
    return {
        "schema": "old_sim_consolidation_work_packages.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_index": "system_v5/evidence/old_sim_reuse_index_20260608.json",
        "claim_ceiling": "Work packages are classification/fuel extraction only. Workers do not delete or promote.",
        "delete_policy": {
            "workers_may_delete": False,
            "controller_may_delete_only_after": [
                "action manifest marks exact path archive_candidate or delete_candidate_after_replacement_verified",
                "replacement_or_fuel_path exists or notes explicitly justify no-fuel duplicate",
                "path is not current route authority and not referenced by current front-door surfaces",
                "targeted validators/tests pass after removal in a separate controller cleanup tranche",
            ],
        },
        "actions_schema": ACTIONS_SCHEMA,
        "packages": packages,
        "assignment_overlap_count": sum(1 for package_ids in assigned.values() if len(package_ids) > 1),
    }


def package_prompt(package: dict[str, Any], package_path: str) -> str:
    package_id = package["package_id"]
    route = package["codex_route"]
    report = package["expected_report"]
    action_manifest = package["expected_action_manifest"]
    return f"""# Codex Ratchet old-sim processing task — {package_id}

Route: {route}
Repo: /Users/joshuaeisenhart/Codex-Ratchet
Work package JSON: {package_path}
Package id: {package_id}

## Mission
{package['mission']}

## Read first
- AGENTS.md
- system_v5/docs/CURRENT_DOCS_MAP.md
- system_v5/docs/LLM_CONTROLLER_CONTRACT.md
- system_v5/docs/LEGO_SIM_CONTRACT.md
- system_v5/docs/maintenance/old_sim_reuse_index_20260608.md
- system_v5/docs/maintenance/three_engine_source_claim_audit_20260608.md
- system_v5/docs/maintenance/sim_tool_library_coverage_20260608.md
- system_v5/evidence/old_sim_reuse_index_20260608.json
- system_v5/evidence/three_engine_source_claim_audit_20260608.json
- system_v5/evidence/sim_tool_library_coverage_20260608.json
- this package row list inside {package_path}

## Source-truth correction
- Do not trust `packages_used`, `aligned_packages_load_bearing`, or an envelope-validator pass by itself.
- For current three-engine envelopes, use `scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed`; use `--strict-source-backed` when deciding whether a declared package claim is clean enough to become future fuel.
- Treat the coverage audit as a gap signal: current JAX/PyTorch lanes are narrow unless they use full sim libraries such as `diffrax`, `dynamiqs`, `qutip`, `quimb`, `netket`, `toponetx`, `gudhi`, `torch_ga`, `torch_geometric`, `geomstats`, or `e3nn` in a claim-carrying way.

## Hard boundaries
- Do not delete files.
- Do not stage, commit, push, rebase, or git-clean.
- Do not rewrite shared result trees.
- Do not promote old results to canonical/admitted.
- Treat old docs/logs/results as mines for math objects, controls, negatives, tool recipes, and rebuild fuel.
- Worker prose is not evidence; write artifacts and include exact paths.

## Required output
1. Report: `{report}`
2. Action manifest: `{action_manifest}`

The action manifest must be JSON with:
```json
{{
  "schema": "old_sim_action_manifest.v1",
  "package_id": "{package_id}",
  "route": "{route}",
  "claim_ceiling": "classification/fuel extraction only; no deletion/promotion",
  "rows": [
    {{
      "source_path": "...",
      "old_role": "...",
      "recommended_action": "keep_current|mine_into_fuel_bank|rebuild_as_micro_lego|consolidate_duplicate|archive_candidate|delete_candidate_after_replacement_verified|graveyard_keep_as_falsifier|needs_human_review",
      "safe_current_reuse": "...",
      "replacement_or_fuel_path": "... or null",
      "delete_or_archive_gate": "...",
      "required_validator": "...",
      "claim_ceiling": "...",
      "notes": "..."
    }}
  ]
}}
```

## Report contents
- What this package covered.
- Top reusable fuel extracted.
- Candidate micro-legos to rebuild under current tri-engine/rich-tool contracts.
- Negative controls / graveyard rows worth preserving.
- Duplicate/archive/delete candidates, but only as proposals.
- Open blockers and required validators.

## Closeout check
Run local JSON parsing on your action manifest and report exact command/output in the report. If you touched Python, run py_compile on touched Python files. Do not call the package done until report + action manifest exist.
"""


def render_controller_plan(packages: dict[str, Any], work_package_path: str) -> str:
    lines = [
        "# Old Sim Consolidation Campaign — 2026-06-08",
        "",
        "Status: launch plan + work-package manifest. This is not deletion authorization.",
        "",
        "## Bottom line",
        "",
        "The goal is good: thousands of old sims are too hard to use as-is. The safe version is not mass deletion first; it is: index -> package -> extract fuel -> rebuild/consolidate -> verify replacements -> archive/delete in a separate controller tranche.",
        "",
        "## Non-negotiable gates",
        "",
        "- Workers may classify, write reports, create action manifests, and propose replacements.",
        "- Workers may not delete, stage, commit, push, rebase, or `git clean`.",
        "- Deletion requires an exact action-manifest row plus replacement/fuel verification or explicit no-fuel duplicate justification.",
        "- Current `three_engine_sim_result_v1` envelopes validate with `scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed`; old pass labels do not promote anything.",
        "- For cleanup/fuel decisions, use `--strict-source-backed` or the source-claim audit to catch thin/decorative declared package claims.",
        "- Old docs/logs/results are mines, not route authority.",
        "",
        "## Work-package manifest",
        "",
        f"Full package JSON: `{work_package_path}`",
        "",
        "## Package roster",
        "",
        "| package | route | rows | expected report | expected action manifest |",
        "|---|---|---:|---|---|",
    ]
    for package_id, package in packages["packages"].items():
        lines.append(
            f"| `{package_id}` | `{package['codex_route']}` | {package['row_count']} | `{package['expected_report']}` | `{package['expected_action_manifest']}` |"
        )
    lines.extend(
        [
            "",
            "## Codex TUI launch shape",
            "",
            "Use the generated prompt cards under `system_v5/ops/old_sim_processing/prompts/`.",
            "",
            "Observed local CLI: `codex-cli 0.137.0`; on this CLI `-p` is `--profile`. The user-corrected route is Codex TUI `-p` lanes for codex1/codex2. Record the exact command/session in each receipt.",
            "",
            "Example launch pattern, if the local profiles/sessions are available:",
            "",
            "```text",
            "codex -p codex1 <prompt text or pasted prompt card>",
            "codex -p codex2 <prompt text or pasted prompt card>",
            "```",
            "",
            "Do not count a launched TUI as complete until its report and action manifest exist and parse.",
            "",
            "## First wave recommendation",
            "",
            "1. `P00_controller_receipt_and_gates` locally/Hermes first, to keep delete gates honest.",
            "2. `P01_active_tri_engine_envelopes` on codex1, because current envelopes define the new standard.",
            "3. `P02_foundation_carrier_geometry_donors` on codex1 and `P03_qit_density_entropy_classical_baselines` on codex2 in parallel.",
            "4. Then `P04`/`P05` tool/proof packages, then bridge/graveyard/unclassified packages.",
            "",
            "## Final cleanup tranche, later",
            "",
            "After action manifests exist, the controller builds a reviewed archive/delete manifest, reruns affected validators/tests, then performs deletes/moves in a separate commit-sized tranche. No worker performs the final deletion.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--prompt-dir", type=Path, default=DEFAULT_PROMPT_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--action-dir", type=Path, default=DEFAULT_ACTION_DIR)
    args = parser.parse_args()

    repo = args.repo.resolve()
    index = load_index(repo, args.index)
    packages = build_packages(index)

    out = args.out if args.out.is_absolute() else repo / args.out
    prompt_dir = args.prompt_dir if args.prompt_dir.is_absolute() else repo / args.prompt_dir
    report_dir = args.report_dir if args.report_dir.is_absolute() else repo / args.report_dir
    action_dir = args.action_dir if args.action_dir.is_absolute() else repo / args.action_dir
    plan_path = repo / "system_v5/docs/maintenance/old_sim_consolidation_campaign_20260608.md"

    out.parent.mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    action_dir.mkdir(parents=True, exist_ok=True)

    out.write_text(json.dumps(packages, indent=2, sort_keys=True), encoding="utf-8")
    package_rel = out.relative_to(repo).as_posix()
    for package_id, package in packages["packages"].items():
        prompt_path = prompt_dir / f"{package_id}_{package['codex_route']}.md"
        prompt_path.write_text(package_prompt(package, package_rel), encoding="utf-8")
    plan_path.write_text(render_controller_plan(packages, package_rel), encoding="utf-8")

    print(json.dumps({
        "status": "ok",
        "work_packages": package_rel,
        "plan": plan_path.relative_to(repo).as_posix(),
        "prompt_dir": prompt_dir.relative_to(repo).as_posix(),
        "package_count": len(packages["packages"]),
        "assignment_overlap_count": packages["assignment_overlap_count"],
        "packages": {k: {"route": v["codex_route"], "rows": v["row_count"]} for k, v in packages["packages"].items()},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
