# A2 to A1 Impact Note — Next-State Consumer Contract Landing

- date: `2026-03-22`
- surface_class: `DERIVED_A2`
- scope: `A2 continuity only; no A1 queue opening`

Impact:

- no new `A1` work is admitted from this contract landing
- do not reinterpret the explicit owner contract as permission to open a mutation lane or reopen `A1`
- the next-state lane now has a repo-held explicit first-target context contract, but its current next step remains `hold_consumer_as_audit_only`

Current fence:

- keep the next-state lane first-target-context-only
- keep `skill-improver-operator` on `hold_one_proven_target_only`
- keep the controller fail-closed unless a later separate consumer path is audited and landed
