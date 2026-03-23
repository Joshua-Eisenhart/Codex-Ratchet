Use Ratchet A2/A1.

You are an A1 Codex thread.

Read first:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md

Launch packet:
MODEL: GPT-5.4 Medium
THREAD_CLASS: A1_WORKER
MODE: PROPOSAL_ONLY
A1_QUEUE_STATUS: READY_FROM_NEW_A2_HANDOFF
dispatch_id: A1_DISPATCH__SUBSTRATE_BASE_CURRENT__2026_03_20__v1
target_a1_role: A1_PROPOSAL
required_a1_boot: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md
a1_reload_artifacts:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md
source_a2_artifacts:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/SIM_FAMILY_PROMOTION_CONTRACTS__ACTIVE_LANES__v1.md
bounded_scope: One bounded scaffold proof pass for the first substrate family using explicit family lanes, explicit negatives, and explicit rescue linkage.
stop_rule: Stop after one bounded family campaign object is generated with required lanes, required negatives, rescue linkage, admissibility block, and SIM hooks. Fail closed if any required handoff field is missing.
go_on_count: 0
go_on_budget: 1

Prompt to execute:
Use the current A1 boot:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md

Read these A1 reload artifacts before acting:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md

Use this bounded A2-derived family slice as the governing campaign object:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json

Use only these A2 fuel surfaces:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/SIM_FAMILY_PROMOTION_CONTRACTS__ACTIVE_LANES__v1.md

Run one bounded A1_PROPOSAL pass only.

Family slice identity:
- slice_id: A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1
- family_id: substrate_base_family
- family_label: First substrate family scaffold proof
- run_mode: SCAFFOLD_PROOF
- required_lanes: STEELMAN, ALT_FORMALISM, BOUNDARY_REPAIR, ADVERSARIAL_NEG, RESCUER
- primary_target_terms: finite_dimensional_hilbert_space, density_matrix, probe_operator, cptp_channel, partial_trace
- required_negative_classes: PRIMITIVE_EQUALS, CLASSICAL_TIME, PRIMITIVE_PROBABILITY, EUCLIDEAN_METRIC, COMMUTATIVE_ASSUMPTION

Task:
- generate one bounded A1_PROPOSAL family campaign from the supplied family slice
- obey the slice lane obligations, branch requirements, graveyard/rescue policy, admissibility, and sim hooks
- preserve contradictions and remain proposal-only

Rules:
- no A2 refinery
- no canon claims
- no lower-loop claims
- no hidden-memory continuation
- fail closed if family-slice obligations are missing
- stop_rule: Stop after one bounded family campaign object is generated with required lanes, required negatives, rescue linkage, admissibility block, and SIM hooks. Fail closed if any required handoff field is missing.
