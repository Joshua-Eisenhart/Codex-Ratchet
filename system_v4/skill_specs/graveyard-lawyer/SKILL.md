---
skill_id: graveyard-lawyer
name: graveyard-lawyer
description: Re-argue rejected structures from the graveyard. Find bad kills, premature parking, conflation kills, or new evidence that justifies reopening.
skill_type: agent
source_type: repo_skill
applicable_layers: [GRAVEYARD, B_ADJUDICATED, SIM_EVIDENCED]
applicable_graphs: [graveyard, runtime, dependency]
inputs: [graveyard_records, routing_state, graph_nodes]
outputs: [reopen_candidates, reopen_arguments, rescue_proposals]
related_skills: [ratchet-verify, ratchet-overseer, b-kernel, sim-engine]
capabilities:
  can_spawn_subagents: true
  can_only_propose: true
  requires_human_gate: false
tool_dependencies: []
provenance: "system design — graveyard_router.py get_rescue_candidates/attempt_resurrection"
adapters:
  codex: system_v4/skill_specs/graveyard-lawyer/SKILL.md
  gemini: system_v4/skill_specs/graveyard-lawyer/SKILL.md
  shell: system_v4/skills/graveyard_lawyer.py
---

# Graveyard Lawyer — Advocate for Rejected Concepts

Re-argue structures that were killed, parked, or graveyarded. Find cases where:
- the rejection reason was wrong (bad kill)
- prerequisites have since been met (premature parking)
- a term conflation caused the failure (conflation kill)
- new evidence from later batches changes the picture

## When to Invoke

- After each batch completes, scan graveyard for rescue candidates
- When a new concept is admitted that could satisfy a parked prerequisite
- When Rosetta sense-splitting resolves an ambiguity that caused a prior kill
- Periodically as a graveyard health audit

## EXECUTE NOW Steps

1. **Load graveyard records** from `graveyard_router.get_rescue_candidates()`
2. **Classify each rejection** using the live runtime fields:
   - `B_KILL` or `SIM_KILL` from `failure_class`
   - `reason_tag` and `stage` for the actionable failure detail
   - `target_ref` when present for source/lineage hints
3. **For dependency-shaped or admission-shaped kills:**
   - Check if the missing term or prerequisite has since been admitted
   - If yes → propose `REOPEN` with evidence
4. **For schema-shaped kills:**
   - Propose `RECLASSIFY` or repair if the failure is now understood better
5. **For SIM_KILL:**
   - Check if later evidence contradicts the kill
   - If evidence exists → propose `REOPEN` with counter-evidence
6. **Emit rescue proposals** with:
   - `graveyard_id`
   - `original_failure_class`
   - `new_evidence`
   - `proposed_action`: REOPEN | KEEP_DEAD | RECLASSIFY
   - `confidence`: LOW | MEDIUM | HIGH

## Quality Gates

- Do NOT propose REOPEN without specific new evidence
- Do NOT reopen STRUCTURAL_FAIL unless the structure has actually been fixed
- A graveyard record can only be reopened once per batch cycle
- All proposals are logged, even rejected ones

## Pipeline Chaining

After graveyard-lawyer → reopened concepts re-enter A1 extraction →
B kernel re-adjudication → SIM re-evidence.

## Adapter Notes

- **Codex**: Can spawn subagent lanes to parallelize graveyard review
- **Gemini**: Run sequentially with isolated prompts per failure class
- **Shell**: Call `system_v4/skills/graveyard_lawyer.py` for a bounded report-only review
- **Future**: z3-constraint-guard can validate dependency DAGs before reopen
