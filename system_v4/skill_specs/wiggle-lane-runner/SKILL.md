---
skill_id: wiggle-lane-runner
name: wiggle-lane-runner
description: Spawn parallel A1 narrative lanes with different biases — literal math, jargon preservation, anti-conflation, skeptic — then compare outputs before B adjudication.
skill_type: agent
source_type: repo_skill
applicable_layers: [A1_JARGONED, A1_STRIPPED, A1_CARTRIDGE]
applicable_graphs: [concept, dependency, rosetta]
inputs: [candidate_ids, graph_nodes, lane_configs]
outputs: [lane_results, comparison_matrix, merged_strategy_packet]
related_skills: [a1-brain, ratchet-reduce, ratchet-overseer, graveyard-lawyer]
capabilities:
  can_spawn_subagents: true
  can_run_parallel: true
  can_write_repo: false
  can_only_propose: true
tool_dependencies: []
provenance: "system design — A1 wiggle concept from user"
adapters:
  codex: system_v4/skill_specs/wiggle-lane-runner/SKILL.md
  gemini: system_v4/skill_specs/wiggle-lane-runner/SKILL.md
  shell: system_v4/skills/wiggle_lane_runner.py
---

# Wiggle Lane Runner — Multi-Narrative A1 Extraction

Current status: draft skill spec. The repo now has a bounded sequential shell
wrapper plus `lane_id` / `bias_config` support on `A1Brain`, but the richer
merge policy, lane provenance, and parallel/subagent execution are still draft.

Run multiple A1 extraction lanes in parallel, each with a different bias or emphasis.
Compare outputs and merge the strongest candidates before sending to B kernel.

## Why Wiggle

One deterministic path through A1 produces one framing. That framing may:
- flatten important distinctions (conflation)
- miss non-obvious structural forms
- over-weight the most recent context
- under-weight adversarial framings

Wiggle creates **branching and recombination** inside A1:

```
                    ┌─ literal-math-lane ─────┐
concept → wiggle →  ├─ jargon-preserve-lane ──┼─ compare → B kernel
                    ├─ anti-conflation-lane ──┤
                    └─ skeptic-lane ──────────┘
```

## Lane Definitions

| Lane | Bias | What it optimizes for |
|---|---|---|
| `literal-math` | Explicit structural math only | Formal precision |
| `jargon-preserve` | Keep domain distinctions | Semantic richness |
| `anti-conflation` | Flag false merges | Separation quality |
| `skeptic` | Attack overreach | Robustness |
| `rosetta-sense-split` | Split overloaded terms | Sense disambiguation |
| `dependency-first` | Build prerequisite DAGs | Ordering correctness |

## EXECUTE NOW Steps

1. **First implementation target:** add `lane_id` and `bias_config` support to `brain.build_strategy_packet()`
2. **Then** select lane configs for a batch (default: all 4 core lanes)
3. **For each lane**, call `brain.build_strategy_packet()` with the new lane bias inputs
4. **Compare lane outputs:**
   - Which concepts appear in multiple lanes? (high confidence)
   - Which appear in only one? (needs scrutiny)
   - Which lanes disagree on kind/structural_form? (conflation signal)
5. **Build merged strategy packet:**
   - Include concepts that appear in ≥2 lanes
   - Flag single-lane concepts for human review or skeptic re-run
   - Annotate each concept with `lane_provenance`
6. **Emit comparison matrix:**
   - Per-concept: which lanes included it, what framing, confidence

## Quality Gates

- Do NOT merge conflicting framings — flag them instead
- Do NOT suppress single-lane concepts — they may be the most important
- Each lane must produce at least 1 candidate or report why it couldn't
- The merged packet must not exceed 2× the single-lane average

## Adapter Notes

- **Codex**: planned parallel subagent lanes after the draft shell wrapper is promoted
- **Gemini**: planned sequential lane execution after the draft shell wrapper is promoted
- **ZIP**: planned worker-packet export after lane contract exists
- **Shell**: draft sequential wrapper at `system_v4/skills/wiggle_lane_runner.py`

## Pipeline Chaining

After wiggle → merged packet enters B kernel → SIM → bridge (normal flow).
Single-lane-only concepts → graveyard-lawyer for re-evaluation.
