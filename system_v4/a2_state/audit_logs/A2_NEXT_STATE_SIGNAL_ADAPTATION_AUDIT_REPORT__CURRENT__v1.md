# A2 Next-State Signal Adaptation Audit Report

- generated_utc: `2026-03-21T20:54:07Z`
- status: `ok`
- cluster_id: `SKILL_CLUSTER::next-state-signal-adaptation`
- first_slice: `a2-next-state-signal-adaptation-audit-operator`
- paper: `OpenClaw-RL: Train Any Agent Simply by Talking`
- repo_url: `https://github.com/Gen-Verse/OpenClaw-RL`
- local_repo_state: `url_only`
- recommended_next_step: `candidate_next_state_directive_probe`

## Imported Member Disposition
- `next-state-signals`: adapt -> treat user reply, tool output, terminal state, and GUI state as first-class post-action evidence
- `directive-correction-supervision`: adapt -> separate richer directive correction from scalar evaluative judgment
- `async-serving-judging-training-loop`: mine -> decouple capture, review, and improvement work as an architectural pattern

## Ratchet Seam Mapping
- `witness-recorder`: exists=True -> captures post-action witness traces, replies, tool outputs, and context updates
- `runtime-state-kernel`: exists=True -> provides an explicit transition/state substrate instead of opaque interaction logs
- `bounded-improve-operator`: exists=True -> keeps improvement loops gated and measurable instead of unfenced online training
- `a2-skill-improver-readiness-operator`: exists=True -> audits whether an improvement lane is ready before any mutation claim
- `a2-skill-improver-first-target-proof-operator`: exists=True -> proves one bounded improvement loop with exact restore instead of admitting a general live learner

## Recommended Actions
- Keep this slice audit-only and use it as a pattern-mapping bridge, not as an imported RL runtime.
- Use the report to scope a later bounded next-state / directive-signal probe over Ratchet witness and skill-improver surfaces.
- Do not widen this source into online training, PRM/judge stack import, or automatic policy mutation claims.
- Verify the local OpenClaw-RL checkout later if network conditions allow, but do not block the bounded paper-derived slice on that clone.

## Non-Goals
- No OpenClaw runtime or server import.
- No PRM / judge / trainer stack import.
- No claim that Ratchet now improves online simply by being used.
- No unfenced live mutation or policy-update loop.
- No claim that the local OpenClaw repo checkout is stable until it is verified.

## Issues
- none
