Use Ratchet A2/A1.

You are an A2 Codex worker thread.

Read first:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md

Launch packet:
MODEL: GPT-5.4 Medium
THREAD_CLASS: A2_WORKER
MODE: A2_ONLY
dispatch_id: A2_HIGH_REFINERY_PASS__STAGE1_OPERATORIZED_ENTROPY_HEAD__2026_03_13__v1
ROLE_LABEL: A2H Refined Fuel Non-Sims
ROLE_TYPE: A2_HIGH_REFINERY_PASS
ROLE_SCOPE: one bounded Stage-1 head grounding pass for probe_induced_partition_boundary and correlation_diversity_functional from the prime-corpus refinedfuel seam
required_a2_boot: /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md
source_artifacts:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__MAIN_TARGET_DECOMPOSITION__2026_03_13__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_IMPACT_NOTE__MAIN_TARGET_DECOMPOSITION__2026_03_13__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_TARGET_FAMILY_MODEL__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md
- /home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/constraint ladder/Constraints.md
- /home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/constraint ladder/Constraints. Entropy.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_refinedfuel_constraints_entropy_term_conflict__v1/A2_3_DISTILLATES__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_A2MID_constraints_entropy_chain_fences__v1/DOWNSTREAM_CONSEQUENCE_NOTES__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_refinedfuel_constraints_term_conflict__v1/A2_3_DISTILLATES__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_A2MID_constraints_foundation_governance_fences__v1/DOWNSTREAM_CONSEQUENCE_NOTES__v1.md
bounded_scope: Run one bounded Stage-1 head grounding pass that grounds only probe_induced_partition_boundary and correlation_diversity_functional, identifies the thinnest admissible source-anchored read for each, and identifies what remains blocked, witness-only, or rescue/residue-only.
stop_rule: Stop after one bounded Stage-1 head grounding pass.
go_on_count: 0
go_on_budget: 1

Prompt to execute:
Use $ratchet-a2-a1 and $a2-brain-refresh.

Use the current A2 boot:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md

Run one bounded A2_HIGH_REFINERY_PASS only.

dispatch_id: A2_HIGH_REFINERY_PASS__STAGE1_OPERATORIZED_ENTROPY_HEAD__2026_03_13__v1
ROLE_LABEL: A2H Refined Fuel Non-Sims
ROLE_TYPE: A2_HIGH_REFINERY_PASS
ROLE_SCOPE: one bounded Stage-1 head grounding pass for probe_induced_partition_boundary and correlation_diversity_functional from the prime-corpus refinedfuel seam

Use only these artifacts:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__MAIN_TARGET_DECOMPOSITION__2026_03_13__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_IMPACT_NOTE__MAIN_TARGET_DECOMPOSITION__2026_03_13__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_TARGET_FAMILY_MODEL__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md
- /home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/constraint ladder/Constraints.md
- /home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/constraint ladder/Constraints. Entropy.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_refinedfuel_constraints_entropy_term_conflict__v1/A2_3_DISTILLATES__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_A2MID_constraints_entropy_chain_fences__v1/DOWNSTREAM_CONSEQUENCE_NOTES__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_refinedfuel_constraints_term_conflict__v1/A2_3_DISTILLATES__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_A2MID_constraints_foundation_governance_fences__v1/DOWNSTREAM_CONSEQUENCE_NOTES__v1.md

Task:
- ground only the Stage-1 head family:
  - probe_induced_partition_boundary
  - correlation_diversity_functional
- identify the thinnest admissible source-anchored read for each term
- identify what remains blocked, witness-only, or rescue/residue-only
- if justified, emit:
  - one bounded A2 update note
  - one bounded A2->A1 impact note

Rules:
- A2 only
- no A1 work
- no canon claims
- no contradiction smoothing
- no direct manifold / attractor / engine / Hopf / axis closure
- no broad external entropy packet work

Stop rule:
- Stop after one bounded Stage-1 head grounding pass.

Required final output:
ROLE_AND_SCOPE:
WHAT_YOU_READ:
ACTION_CHOSEN:
- one exact bounded action
- why it beat the alternatives
WHAT_YOU_UPDATED:
RESULT:
- one short paragraph only
NEXT_STEP:
- STOP
- ONE_MORE_BOUNDED_A2_PASS_NEEDED
IF_ONE_MORE_PASS:
- omit unless NEXT_STEP = ONE_MORE_BOUNDED_A2_PASS_NEEDED
- if present, give one exact next bounded A2 action
CLOSED_STATEMENT:
- one sentence only

Keep the return compact and easy to scan.
Do not write a long recap.
