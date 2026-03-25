# BROWSER_ASSISTED_GO_ON_EXECUTION__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for bounded browser-assisted continuation execution

## Purpose

This note defines the next automation layer after:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/43_AUTO_GO_ON_EXECUTION_PATH__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/45_AUTO_GO_ON_RUNNER__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/44_AUTO_GO_ON_SENDER_PACKET__v1.md`

It does not authorize blind autonomy.

It answers:
- when browser assistance is allowed
- what the browser layer may do
- what remains manual
- what must still be captured back into repo-held state

## Current role

`PATH_BROWSER_AUTOMATED` is not yet the live default.

This note defines the allowed browser-assisted path so later implementation does not improvise policy.

Current live order remains:
1. runner decides
2. sender packet emitted
3. operator sends manually

Browser assistance is the next layer after that.

## Allowed scope

Browser-assisted continuation may only do the final send action for a thread that has already passed:
1. normalized result capture
2. applicator decision
3. sender packet emission

It may not:
- reinterpret thread results
- widen scope
- change the continuation text
- decide continuation policy

## Required browser input

Before browser-assisted execution is allowed, the controlling system must have:
- one valid `AUTO_GO_ON_SENDER_PACKET_v1`
- one stable thread identifier or addressable thread target
- one explicit thread platform label
- one expected post-send capture path

Minimum required fields:
- `target_thread_id`
- `thread_platform`
- `message_to_send`
- `continuation_count`
- `stop_condition`
- `expected_return_shape`

## Allowed message

The only allowed browser-sent continuation text is:

```text
go on
```

No added explanation.
No prompt reshaping.
No appended qualifiers.

## Browser-assisted stages

1. `LOAD_TARGET`
- navigate to the exact thread target

2. `VERIFY_TARGET`
- confirm the visible thread identity matches the sender packet

3. `VERIFY_COMPOSER_READY`
- confirm a sendable input surface exists

4. `SEND_EXACT_MESSAGE`
- send exactly:
  - `go on`

5. `CAPTURE_SEND_PROOF`
- capture one minimal proof artifact:
  - timestamp
  - target thread id
  - sent text
  - execution mode

6. `RETURN_TO_WAIT_STATE`
- hand control back to the result-capture path

## Hard blockers

Browser-assisted execution is blocked if:
- thread identity is uncertain
- the visible target does not match the sender packet
- the composer is missing or disabled
- the packet asks for any text other than `go on`
- the thread class is controller-class
- the thread platform is external `Pro`

## Pro-thread rule

External web UI `Pro` threads are still excluded from browser-assisted auto-`go on`.

Reason:
- `Pro` remains a separate operator-mediated generation/audit lane
- continuation semantics there are not yet constrained enough for automatic continuation

## Required post-send capture

Browser assistance must emit one repo-holdable proof packet or proof note with:
- `target_thread_id`
- `sent_at`
- `message_sent`
- `continuation_count`
- `execution_path = PATH_BROWSER_AUTOMATED`

Without proof capture:
- execution is treated as incomplete

## Relationship to existing paths

Current path classes:
- `PATH_MANUAL_OPERATOR`
- `PATH_CODEX_ASSISTED`
- `PATH_BROWSER_AUTOMATED`

Current live default:
- `PATH_MANUAL_OPERATOR`

Next intended implementation target:
- `PATH_BROWSER_AUTOMATED` for bounded Codex worker threads only

## Immediate implication

After this note:
- the manual/operator continuation chain is complete
- the browser-assisted continuation path is now policy-defined

Remaining gap:
- actual browser implementation and proof-capture helper
