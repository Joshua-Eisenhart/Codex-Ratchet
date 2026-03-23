# A2 To A1 Impact Note — Next-State Witness Batch Advance

Date: 2026-03-22
Surface class: `DERIVED_A2`
Status: support note for current A2 -> A1 boundary

Current boundary consequence:
- `A1` remains `NO_WORK`
- the next-state lane is now unblocked for a bounded A2 follow-on bridge, but this does not open a worker or queue by itself
- treat the new witness batch as A2 evidence and control-substrate input, not as direct dispatch pressure
