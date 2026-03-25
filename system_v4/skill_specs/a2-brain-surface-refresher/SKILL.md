---
skill_id: a2-brain-surface-refresher
name: a2-brain-surface-refresher
description: Emit one bounded audit-only repo-held report that compares the primary standing A2 brain surfaces against current repo truth, without mutating canonical A2 owner surfaces.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_HIGH_INTAKE, A2_MID_REFINEMENT]
applicable_graphs: [runtime, control, a2_high_intake_graph_v1]
inputs: [repo_root, task_signal, changed_paths, changed_tools, new_run_evidence, pending_a1_work, report_path, markdown_path, packet_path]
outputs: [brain_surface_refresh_report, brain_surface_refresh_packet]
related_skills: [a2-brain-refresh, a2-tracked-work-operator, graph-capability-auditor, runtime-context-snapshot]
capabilities:
  can_write_repo: true
  can_only_propose: true
tool_dependencies: []
provenance: "Ratchet-native truth-maintenance slice for standing A2 refresh audit over current repo truth"
adapters:
  codex: system_v4/skill_specs/a2-brain-surface-refresher/SKILL.md
  shell: system_v4/skills/a2_brain_surface_refresher.py
---

# A2 Brain Surface Refresher

Use this skill when the standing controller-facing A2 brain surfaces may be
lagging current repo truth and we need one bounded audit packet before touching
canonical A2.

## Purpose

- compare the ten primary standing A2 surfaces against current repo truth
- catch explicit stale claims and missing surfaces before they keep steering work
- emit one machine packet and one human report without mutating canonical A2

## Execute Now

1. Read:
   - [A2_BOOT_READ_ORDER__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_BOOT_READ_ORDER__CURRENT__v1.md)
   - [A2_KEY_CONTEXT_APPEND_LOG__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md)
   - [V4_SYSTEM_SPEC__CURRENT.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/V4_SYSTEM_SPEC__CURRENT.md)
   - [GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.md)
2. Compare the primary standing A2 surfaces against:
   - owner-law indexing truth
   - front-door corpus indexing truth
   - live registry truth
   - live graph skill coverage truth
   - current repo-held imported-cluster and maintenance reports
3. Emit only bounded audit artifacts.

## Default Outputs

When no explicit paths are supplied, write:

- `system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.md`
- `system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_PACKET__CURRENT__v1.json`

## Quality Gates

- Do not emit `A2_UPDATE_NOTE` or `A2_TO_A1_IMPACT_NOTE`.
- Do not mutate `system_v3/a2_state` owner surfaces in this first slice.
- Keep the first slice audit-only, nonoperative, and explicit about non-promotion.
- Prefer patching existing standing surfaces over adding another same-scope note chain.
