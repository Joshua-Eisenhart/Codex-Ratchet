# A2_UPDATE_NOTE__WORKER_PROMPT_WRAPPER_BUG_AND_RAW_PROMPTS__2026_03_16__v1

Status: `DERIVED_A2`
Date: 2026-03-16

## What happened

The prior four worker launches were sent using dispatch packet wrapper files instead of raw prompt bodies.

Observed effect:

- workers echoed or restated the packet wrapper
- no substantive bounded task work was performed
- no new valid worker output from that wave should be treated as earned system progress

## Fix

Created raw operator launch prompt files that contain only the sendable prompt body:

1. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_WORKER_PROMPT__RUNS_SAFE_MOVE_EXECUTION__2026_03_16__v1.txt`
2. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_WORKER_PROMPT__THREAD_CLOSEOUT_EXTRACTOR_PATCH__2026_03_16__v1.txt`
3. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_WORKER_PROMPT__A2_INTAKE_COLD_INDEX_PREP__2026_03_16__v1.txt`
4. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_WORKER_PROMPT__A2_STATE_DUPLICATE_SURFACE_PACK__2026_03_16__v1.txt`

## Operator rule going forward

For worker launches:

- use dispatch packet `.md` files as controller records only
- use worker prompt `.txt` files as the actual copy-paste launch surfaces
