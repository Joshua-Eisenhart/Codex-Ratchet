# A2 to A1 Impact Note — Next-State First-Target Consumer Hold

- date: `2026-03-22`
- surface_class: `DERIVED_A2`
- scope: `A2 continuity only; no A1 queue opening`

Impact:

- no new `A1` work is admitted from this landing
- do not reinterpret the new slice as permission to widen `skill-improver-operator`, open a mutation lane, or reopen `A1`
- the next-state lane now carries a repo-held fail-closed answer on the first consumer question

Current fence:

- keep the next-state lane blocked at `hold_no_explicit_first_target_context_consumer`
- keep `skill-improver-operator` on `hold_one_proven_target_only`
- keep the controller fail-closed unless a later explicit context consumer contract is audited and landed
