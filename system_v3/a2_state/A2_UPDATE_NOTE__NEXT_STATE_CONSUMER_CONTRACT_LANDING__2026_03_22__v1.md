# A2 Update Note — Next-State Consumer Contract Landing

- date: `2026-03-22`
- surface_class: `DERIVED_A2`
- scope: `system_v4 next-state signal lane / upper-loop controller continuity`

What changed:

- `skill-improver-operator` now exposes an explicit first-target context contract
- `a2-next-state-first-target-context-consumer-admission-audit-operator` now returns `candidate_first_target_context_consumer_admissible`
- current next step is `hold_consumer_as_audit_only`
- current graph / registry truth remains `116` active / `116` graphed / `0` missing / `0` stale

Meaning:

- the lane is one honest step past the fail-closed “missing contract” result
- the new owner contract is still metadata-only / first-target-context-only
- this is not permission for live learning, runtime import, graph backfill, second-target widening, or a runtime-live consumer path

Required continuity:

- front-door corpus and controller surfaces should treat the contract as landed
- the standing fence remains audit-only / first-target-context-only
