# FIRST_PARALLEL_CODEX_WAVE_C0_EVALUATION_PACKET__v1

Status: DRAFT / NONCANON / ACTIVE OPERATOR SURFACE
Date: 2026-03-11
Owner: current `A2` controller

## Purpose

This note is the matching `C0` controller-side intake/evaluation packet for:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/68_FIRST_PARALLEL_CODEX_WAVE_OPERATOR_PACKET__v1.md`

It answers:
- how `C0` should receive the returned `W1` result from the shared sink
- how `C0` should evaluate it
- when `C0` should stop, continue once, route to closeout, or require manual review

## Scope

This packet is only for:
- first parallel Codex wave
- slot `W1`
- role:
  - `A2_HIGH_REFINERY_PASS__REFINEDFUEL_RUN_NOW_WAVE_1`

It should not be reused for:
- `W2`
- `A1`
- controller self-evaluation
- unrelated worker families

## Governing surfaces

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/67_FIRST_PARALLEL_CODEX_WAVE_PACKET__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/68_FIRST_PARALLEL_CODEX_WAVE_OPERATOR_PACKET__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/41_AUTO_GO_ON_RULE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/42_AUTO_GO_ON_APPLICATOR__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/PARALLEL_CODEX_WORKER_RESULT_SINK__v1.md`

## What `C0` should expect from the shared sink

The staged `W1` result file should exist at:
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_HIGH_REFINERY_PASS__REFINEDFUEL_RUN_NOW_WAVE_1__A2_WORKER__return.txt`

Before controller evaluation, `C0` should normalize that raw return into:
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_HIGH_REFINERY_PASS__REFINEDFUEL_RUN_NOW_WAVE_1__A2_WORKER__return.json`

Use:

```text
python3 system_v3/tools/extract_parallel_codex_worker_result.py \
  --reply-text "work/audit_tmp/parallel_codex_worker_returns/A2_HIGH_REFINERY_PASS__REFINEDFUEL_RUN_NOW_WAVE_1__A2_WORKER__return.txt" \
  --dispatch-id "A2_HIGH_REFINERY_PASS__REFINEDFUEL_RUN_NOW_WAVE_1" \
  --thread-class "A2_WORKER" \
  --out-json "work/audit_tmp/parallel_codex_worker_returns/A2_HIGH_REFINERY_PASS__REFINEDFUEL_RUN_NOW_WAVE_1__A2_WORKER__return.json"
```

That sink-held worker result should contain:
1. `ROLE_AND_SCOPE`
2. `WHAT_YOU_READ`
3. `WHAT_YOU_UPDATED`
4. `REFINEDFUEL_WAVE_RESULT`
5. `NEXT_STEP`
6. `IF_ONE_MORE_PASS` if and only if `NEXT_STEP = ONE_MORE_BOUNDED_A2_PASS_NEEDED`
7. `CLOSED_STATEMENT`

If any of those are missing:
- do not send `go on`
- route to closeout or manual review per the applicator rules

## Exact controller evaluation prompt

If you want to run the `C0` evaluation as one bounded controller step in a Codex thread, use this exact prompt:

```text
Use $ratchet-a2-a1.

Run one bounded A2 controller evaluation pass only.

You are evaluating the returned result of:
- A2_HIGH_REFINERY_PASS__REFINEDFUEL_RUN_NOW_WAVE_1

Use these governing surfaces:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/67_FIRST_PARALLEL_CODEX_WAVE_PACKET__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/68_FIRST_PARALLEL_CODEX_WAVE_OPERATOR_PACKET__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/41_AUTO_GO_ON_RULE__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/42_AUTO_GO_ON_APPLICATOR__v1.md

Task:
- read and evaluate the normalized sink-held W1 result only
- decide exactly one:
  - STOP_NOW
  - SEND_ONE_GO_ON
  - ROUTE_TO_CLOSEOUT
  - MANUAL_REVIEW_REQUIRED
- do not broaden into new planning
- do not launch W2
- do not launch A1

Required final output:
1. ROLE_AND_SCOPE
2. WHAT_YOU_READ
3. WORKER_RESULT_EVALUATION
- one short paragraph on the returned W1 result
4. DECISION
Choose exactly one:
- STOP_NOW
- SEND_ONE_GO_ON
- ROUTE_TO_CLOSEOUT
- MANUAL_REVIEW_REQUIRED
5. REASON
- one short paragraph only
6. NEXT_CONTROLLER_ACTION
- one exact next bounded controller action
7. CLOSED_STATEMENT
- one sentence saying whether this controller evaluation pass should now stop
```

## Decision rules for `C0`

### `STOP_NOW`

Use when:
- `W1` returned `NEXT_STEP = STOP`
- metadata is complete
- result is bounded and intelligible

Immediate consequence:
- wave 1 ends
- no automatic continuation
- capture result into controller state

### `SEND_ONE_GO_ON`

Use only when:
- `W1` returned `NEXT_STEP = ONE_MORE_BOUNDED_A2_PASS_NEEDED`
- `IF_ONE_MORE_PASS` names one exact bounded step
- touched artifacts/families are explicit
- stop condition is explicit
- worker class/role purity is intact
- no blocked condition from:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/41_AUTO_GO_ON_RULE__v1.md`

Immediate consequence:
- emit exactly:

```text
go on
```

### `ROUTE_TO_CLOSEOUT`

Use when:
- return shape is incomplete
- next step is vague
- role drift happened
- boundedness was lost

Immediate consequence:
- send the thread to closeout handling

### `MANUAL_REVIEW_REQUIRED`

Use when:
- no sink artifact exists
- the continuation ceiling is already hit
- the worker result is structurally unusual
- the result has mixed signals that the applicator cannot safely resolve

Immediate consequence:
- no automatic `go on`
- controller review required

## Wave-level stop rule

This packet ends when one `W1` result has been classified into exactly one controller decision.

It does not itself:
- launch `W2`
- launch `A1`
- run another worker

Those require a fresh controller note if needed.
