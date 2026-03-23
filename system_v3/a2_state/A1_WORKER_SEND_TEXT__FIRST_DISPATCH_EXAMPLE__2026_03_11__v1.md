Use Ratchet A2/A1.

You are an A1 Codex thread.

Read first:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md

Launch packet:
MODEL: GPT-5.4 Medium
THREAD_CLASS: A1_WORKER
MODE: PROPOSAL_ONLY
A1_QUEUE_STATUS: READY_FROM_EXISTING_FUEL
dispatch_id: A1_DISPATCH__ENTROPY_RESIDUE_NEGATIVE_AND_RESCUE__2026_03_11__v1
target_a1_role: A1_PROPOSAL
required_a1_boot: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md
a1_reload_artifacts:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md
source_a2_artifacts:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__CONSTRAINTS_ENTROPY_REVISIT__2026_03_10__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_IMPACT_NOTE__CONSTRAINTS_ENTROPY_REVISIT__2026_03_10__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_A1_DELTA__CONSTRAINTS_ENTROPY_REVISIT__2026_03_10__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__ENTROPY_LOCAL_PACK_RETURN__2026_03_11__v1.md
bounded_scope: One bounded A1_PROPOSAL pass that turns current entropy and engine residue fuel into one explicit proposal family with one steelman lane, one adversarial negative lane, and one rescue lane.
stop_rule: Stop after one bounded proposal-family pass.
go_on_count: 0
go_on_budget: 1

Prompt to execute:
Use the current A1 boot: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md . Read these A1 reload artifacts before acting: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md ; /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md . Run one bounded A1_PROPOSAL pass only. Use only these artifacts: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__CONSTRAINTS_ENTROPY_REVISIT__2026_03_10__v1.md ; /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_IMPACT_NOTE__CONSTRAINTS_ENTROPY_REVISIT__2026_03_10__v1.md ; /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_A1_DELTA__CONSTRAINTS_ENTROPY_REVISIT__2026_03_10__v1.md ; /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__ENTROPY_LOCAL_PACK_RETURN__2026_03_11__v1.md . Task: generate one bounded A1_PROPOSAL family with one steelman lane, one adversarial negative lane, and one rescue lane. Rules: no A2 refinery, no canon claims, no lower-loop claims. Stop rule: Stop after one bounded proposal-family pass.
