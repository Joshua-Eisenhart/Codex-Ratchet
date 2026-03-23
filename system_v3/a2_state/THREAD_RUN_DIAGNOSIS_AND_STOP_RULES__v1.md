# THREAD_RUN_DIAGNOSIS_AND_STOP_RULES__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-09
Role: define bounded worker-thread diagnosis and stop categories for controller use, automation, and future skill packaging

## 1) Purpose

The system now uses long-lived controller work plus bounded fresh-thread worker lanes.

A repeated failure mode is:
- workers continue too long
- useful outputs get buried under continuation churn
- threads drift into polish, recap, or side-quests
- stop decisions remain implicit and inconsistent

This note exists so stop behavior becomes explicit and later automatable.

## 2) Core rule

A worker thread should not continue just because:
- parallelism exists
- more material exists
- the lane is still interesting
- there are infinite plausible next steps

A worker thread continues only if one more bounded step has clear incremental reuse value.

Otherwise it should close with an audit packet.

## 3) Diagnosis classes

Every overlong worker thread should be classified as exactly one of:

### `healthy_but_ready_to_stop`
- produced useful bounded artifacts
- no clear high-value next bounded step remains
- continuing would mostly add recap, polish, or symmetric fill-in

### `healthy_but_needs_one_bounded_final_step`
- produced useful bounded artifacts
- exactly one more bounded step would materially improve reuse or correctness
- the stop condition after that step is explicit

### `stalled`
- repeated passes are not increasing reuse value
- outputs stay shallow, repetitive, or source-map-only
- the lane is consuming time without strengthening the system

### `duplicate`
- another lane or artifact family is already covering this work better
- continuation would create overlap rather than new value

### `drifted_off_scope`
- the thread started in-scope but widened into adjacent or meta work
- continuing would reinforce the drift instead of the original lane

### `metadata_polish_only`
- the remaining work is mostly naming, formatting, extra fields, or noncritical cleanup
- this should almost always stop unless a real downstream consumer is blocked

### `waiting_on_external_input`
- the lane cannot finish without a missing report, tool result, decision, or data source
- the right action is suspend/hold, not speculative continuation

## 4) Stop triggers

Any of these is sufficient to force a closeout audit:

- the next step is mainly recap/polish
- the lane has already emitted its strongest reusable artifact family
- repeated "go on" produces low-yield symmetry completion
- the lane has drifted into generic theory talk instead of bounded artifacts
- the work is now better handled by a different role/skill/template
- continuation relies on hidden thread memory more than repo-held artifacts
- the unresolved remainder is real but not this thread's job anymore

## 5) Allowed decisions

The controller-facing decision set is small:

- `STOP`
- `CONTINUE_ONE_BOUNDED_STEP`
- `CORRECT_LANE_LATER`

Meaning:

### `STOP`
- close the thread now
- preserve strongest outputs
- preserve the handoff packet
- do not ask for more `go on`s by default

### `CONTINUE_ONE_BOUNDED_STEP`
- allow exactly one more bounded step
- the stop condition must be explicit in advance
- after that step, re-audit instead of auto-continuing

### `CORRECT_LANE_LATER`
- stop this thread now
- later start a new bounded thread with a corrected role/scope/prompt

## 6) Output contract for closeout

An overlong worker thread should emit:
- `ROLE_AND_SCOPE`
- `STRONGEST_BOUNDED_OUTPUTS`
- `UNFINISHED_BUT_WORTH_KEEPING`
- `THREAD_DIAGNOSIS`
- `STOP_CONTINUE_CORRECT_DECISION`
- `IF_ONE_MORE_STEP`
- `OPEN_RISKS_AND_DRIFT_FLAGS`
- `HANDOFF_PACKET`
- `NO_MORE_WORK_STATEMENT`

This should become the standard closeout packet shape for future skill and automation work.

## 7) Automation implication

The automation/skill layer should eventually support:

### `thread-closeout-auditor`
- send the closeout prompt
- collect the returned packet
- classify the lane
- record the stop/continue/correct result

### `thread-run-monitor`
- detect overlong lanes
- detect low-yield continuation
- detect duplicate/overlap signatures
- trigger closeout audit instead of endless continuation

### `thread-dispatch-controller`
- launch bounded worker runs
- track role labels and expected outputs
- hand lanes to closeout auditor at the right time

## 8) Link to skill stack

This note extends the skill-stack read in:
- `system_v3/a2_state/SKILL_STACK_AND_BRAIN_UPDATE_STABILIZATION__v1.md`

This implies one additional high-priority skill near the front of the stack:
- `thread closeout auditor`

Because without explicit stop/closeout behavior, the system wastes worker time and weakens artifact quality.

## 9) Bottom line

The system now needs explicit stop law for worker threads.

Not:
- "continue until empty"
- "continue until the operator gets tired"
- "continue because more interesting ideas exist"

But:
- produce bounded artifacts
- diagnose lane health
- stop when marginal value falls below the bounded-step threshold
- preserve a handoff packet
- let the controller decide the next lane

