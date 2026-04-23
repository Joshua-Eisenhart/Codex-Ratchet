# A2 Next-State Directive Signal Probe Report

- generated_utc: `2026-03-22T00:56:48Z`
- status: `ok`
- cluster_id: `SKILL_CLUSTER::next-state-signal-adaptation`
- first_slice: `a2-next-state-directive-signal-probe-operator`
- witness_entry_count: `7`
- next_state_candidate_count: `3`
- directive_signal_count: `3`
- recommended_next_step: `candidate_next_state_improver_context_bridge`

## Sample Entries
- witness[0]: kind=intent transition=False evaluative=False directive=False
- witness[1]: kind=intent transition=False evaluative=False directive=False
- witness[2]: kind=intent transition=False evaluative=False directive=False
- witness[3]: kind=context transition=False evaluative=False directive=False
- witness[4]: kind=negative transition=True evaluative=True directive=True

## Recommended Actions
- Keep this slice audit-only and use it to measure signal quality, not to mutate the system.
- Record real post-action witness entries with before/after hashes and corrective notes before widening the lane.
- Do not treat intent/context preservation by itself as next-state or directive-correction proof.

## Issues
- none
