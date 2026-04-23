---
skill_id: a2-skill-source-intake-operator
name: a2-skill-source-intake-operator
description: Run the first bounded A2-side source-intake audit for the broad skill-source corpus, with special focus on the first imported `lev-os/agents` intake/discovery/build cluster and whether the front-door corpus, A2 indexing, and local imported-skill reality still agree.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_HIGH_INTAKE, A2_MID_REFINEMENT]
applicable_graphs: [runtime, control, a2_high_intake_graph_v1]
inputs: [repo_root, report_path]
outputs: [intake_report]
related_skills: [autoresearch-operator, skill-improver-operator, witness-evermem-sync]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "lev-os/agents lev-intake + skill-discovery + skill-builder, retooled into a bounded A2 intake audit slice"
adapters:
  codex: system_v4/skill_specs/a2-skill-source-intake-operator/SKILL.md
  shell: system_v4/skills/a2_skill_source_intake_operator.py
---

# A2 Skill Source Intake Operator

Use this skill when the broad skill-source corpus, imported skill clusters, and
canonical A2 indexing need a bounded truth refresh.

## Purpose

- keep the broad source corpus from drifting away from local repo reality
- keep imported-cluster promotion grounded in actual downloaded sources
- keep canonical A2 indexing honest for the front-door corpus docs
- produce one structured intake report instead of more vague tracker prose

## Execute Now

1. Read:
   - [SKILL_SOURCE_CORPUS.md](/home/ratchet/Desktop/Codex%20Ratchet/SKILL_SOURCE_CORPUS.md)
   - [REPO_SKILL_INTEGRATION_TRACKER.md](/home/ratchet/Desktop/Codex%20Ratchet/REPO_SKILL_INTEGRATION_TRACKER.md)
   - [SKILL_CANDIDATES_BACKLOG.md](/home/ratchet/Desktop/Codex%20Ratchet/SKILL_CANDIDATES_BACKLOG.md)
   - [LOCAL_SOURCE_REPO_INVENTORY.md](/home/ratchet/Desktop/Codex%20Ratchet/LOCAL_SOURCE_REPO_INVENTORY.md)
   - [A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md)
2. Audit the first imported cluster:
   - `lev-intake`
   - `skill-discovery`
   - `skill-builder`
3. Verify:
   - front-door corpus doc presence
   - canonical A2 direct indexing for root corpus docs
   - local `lev-os/agents` skill counts
   - first imported-cluster map presence
4. Emit one structured report.
5. Default repo-held outputs when no explicit path is supplied:
   - `system_v4/a2_state/audit_logs/A2_SKILL_SOURCE_INTAKE_REPORT__CURRENT__v1.json`
   - `system_v4/a2_state/audit_logs/A2_SKILL_SOURCE_INTAKE_REPORT__CURRENT__v1.md`

## Quality Gates

- Do not claim imported-cluster live integration from source presence alone.
- Do not import workshop/toolchain assumptions like `.lev/workshop`, `qmd`, or `skill-seekers`.
- Keep the first slice bounded to inventory, classification, and staged proposal output.
- If a count or path mismatches, record it explicitly instead of smoothing it away.
