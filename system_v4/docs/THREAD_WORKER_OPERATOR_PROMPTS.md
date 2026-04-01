# Thread Worker Operator Prompts

**Date:** 2026-03-29  
**Purpose:** Ready-to-send controller prompts for the two non-controller worker threads after consolidation.  
**Status:** Active operator packet.

---

## 1. Controller Recommendation

Current recommended routing:

- shell-math worker: `CONTINUE_ONE_BOUNDED_STEP`
- Thread B worker: `CONTINUE_ONE_BOUNDED_STEP` if you still want one last registry-facing artifact, otherwise `STOP`

Reason:

- the shell lane still has one clean bounded reuse step left
- the Thread B lane is already staging-only and should not keep expanding, but one last registry/validation closeout packet could still be useful

---

## 2. Shell Worker Continue Prompt

Copy-paste prompt:

You are now in `BOUNDED_SHELL_WORKER` mode.

ROLE_LABEL:
- `Ax0 Shell Math Worker`

ROLE_TYPE:
- bounded worker lane

ROLE_SCOPE:
- shell-local microscopic math only

Do exactly one bounded final worker step.

Allowed scope:

- [AXIS0_SHELL_ALGEBRA_STRICT_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_SHELL_ALGEBRA_STRICT_OPTIONS.md)
- [AXIS0_SHELL_BOUNDARY_INTERIOR_MICRO_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_SHELL_BOUNDARY_INTERIOR_MICRO_OPTIONS.md)
- [AXIS0_TYPED_SHELL_CUT_CONTRACT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_TYPED_SHELL_CUT_CONTRACT.md)

Your task:

- produce one compact shell-local packet only
- title it: `AXIS0_SHELL_LOCAL_STATUS_CARD.md`
- limit it to:
  - `earned`
  - `live but open`
  - `killed`
  - `still unvalidated`

Hard guardrails:

- do not reopen `Xi_hist` ranking
- do not reopen point-reference ranking
- do not claim shell outranks history executably
- do not change final `A|B` status
- do not broaden back into general Ax0 controller summaries
- do not spawn new lanes

Required lock language:

- shell/interior-boundary remains strongest doctrine-facing cut family
- typed shell cut contract is real but still partially open
- `I_r|B_r` remains strongest shell-algebra target
- core-vs-interface remains strongest refined microscopic read
- raw repeated `L|R` stays control only

Stop condition:

- stop immediately after writing the single shell-local status card and reporting its path

Output:

- file path written
- 4-8 line controller summary
- one-sentence stop statement

---

## 3. Shell Worker Closeout Prompt

Copy-paste prompt:

You are now in `THREAD_CLOSEOUT_AUDIT` mode.

Close out this worker as a bounded shell-math lane.

Use only the work already done in this thread plus repo files this lane has actually touched.

Special controller instruction:

- treat this as a shell-local closeout only
- do not reopen global Ax0 doctrine
- emphasize reusable shell-local outputs
- make clear whether any one remaining bounded shell step is still worth doing

Priority artifacts:

- [AXIS0_SHELL_ALGEBRA_STRICT_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_SHELL_ALGEBRA_STRICT_OPTIONS.md)
- [AXIS0_SHELL_BOUNDARY_INTERIOR_MICRO_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_SHELL_BOUNDARY_INTERIOR_MICRO_OPTIONS.md)
- [AXIS0_TYPED_SHELL_CUT_CONTRACT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_TYPED_SHELL_CUT_CONTRACT.md)

Required output sections:

1. `ROLE_AND_SCOPE`
2. `STRONGEST_BOUNDED_OUTPUTS`
3. `UNFINISHED_BUT_WORTH_KEEPING`
4. `THREAD_DIAGNOSIS`
5. `STOP_CONTINUE_CORRECT_DECISION`
6. `IF_ONE_MORE_STEP`
7. `OPEN_RISKS_AND_DRIFT_FLAGS`
8. `HANDOFF_PACKET`
9. `NO_MORE_WORK_STATEMENT`

Bias:

- if only a single compact shell-local status card remains, classify as `healthy_but_needs_one_bounded_final_step`
- otherwise bias to `STOP`

---

## 4. Thread B Continue Prompt

Copy-paste prompt:

You are now in `BOUNDED_THREAD_B_WORKER` mode.

ROLE_LABEL:
- `Thread B Registry Worker`

ROLE_TYPE:
- bounded worker lane

ROLE_SCOPE:
- lexeme registration validation and term-admission hygiene only

Do exactly one bounded final worker step.

Allowed scope:

- [THREAD_B_LEXEME_ADMISSION_CANDIDATES.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_LEXEME_ADMISSION_CANDIDATES.md)
- [THREAD_B_TERM_ADMISSION_MAP.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_TERM_ADMISSION_MAP.md)
- [THREAD_B_STACK_AUDIT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_STACK_AUDIT.md)

Your task:

- produce one short packet only
- title it: `THREAD_B_STAGING_VALIDATION_CARD.md`
- limit it to:
  - `validated for staging`
  - `still blocked`
  - `not allowed yet`

Hard guardrails:

- do not push permit work for `coherent_information`
- do not claim Thread B export readiness
- do not reopen bridge/cut doctrine
- do not outrank the local Ax0 owner stack
- do not let staging language drift into canon language
- do not spawn new lanes

Required lock language:

- Thread B remains staging-only
- `THREAD_B_TERM_ADMISSION_MAP` survives
- `THREAD_B_LEXEME_ADMISSION_CANDIDATES` survives
- shared export wrappers stay review-only
- `coherent_information` remains fenced and downstream

Stop condition:

- stop immediately after writing the single staging-validation card and reporting its path

Output:

- file path written
- 4-8 line controller summary
- one-sentence stop statement

---

## 5. Thread B Closeout Prompt

Copy-paste prompt:

You are now in `THREAD_CLOSEOUT_AUDIT` mode.

Close out this worker as a bounded Thread B staging lane.

Use only the work already done in this thread plus repo files this lane has actually touched.

Special controller instruction:

- treat this as a staging/registry closeout only
- do not reopen bridge/cut doctrine
- do not promote review wrappers into readiness claims
- make clear whether one final registry-validation card is still worth doing

Priority artifacts:

- [THREAD_B_CONSTRAINT_RATCHET_CARD.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_CONSTRAINT_RATCHET_CARD.md)
- [THREAD_B_TERM_ADMISSION_MAP.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_TERM_ADMISSION_MAP.md)
- [THREAD_B_LEXEME_ADMISSION_CANDIDATES.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_LEXEME_ADMISSION_CANDIDATES.md)
- [THREAD_B_STACK_AUDIT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_STACK_AUDIT.md)

Required output sections:

1. `ROLE_AND_SCOPE`
2. `STRONGEST_BOUNDED_OUTPUTS`
3. `UNFINISHED_BUT_WORTH_KEEPING`
4. `THREAD_DIAGNOSIS`
5. `STOP_CONTINUE_CORRECT_DECISION`
6. `IF_ONE_MORE_STEP`
7. `OPEN_RISKS_AND_DRIFT_FLAGS`
8. `HANDOFF_PACKET`
9. `NO_MORE_WORK_STATEMENT`

Bias:

- if the only remaining work is the compact staging-validation card, classify as `healthy_but_needs_one_bounded_final_step`
- if the lane has already crossed into wrapper cleanup only, bias to `STOP`

---

## 6. Fast Controller Use

Use these if you want the shortest clean routing:

- send the shell worker the continue prompt
- send Thread B either the continue prompt for one last card or the closeout prompt if you want immediate consolidation

Shortest recommendation:

- shell worker: continue once, then close
- Thread B worker: close now unless you still want the single staging-validation card
