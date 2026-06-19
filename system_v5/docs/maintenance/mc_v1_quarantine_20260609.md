# M(C) v1 admissibility-object build — graveyard scratch fuel (2026-06-09)

**Label:** `fenced scratch graveyard fuel; built one phase early (tool-tuning, not ladder); KEEP, rebuild with tuned tools when the ladder resumes`

**Disposition: KEEP in place.** It is fenced scratch (`promotion=false`), and the program runs a large scratch graveyard by design. No quarantine action. The only real issue was a sequencing slip (a ladder build auto-ran during the tool-tuning phase) — a process lesson, not a file decision. Note it was built on the UN-tuned tool stack, so when the ladder resumes, rebuild it with the tuned skills rather than reusing these receipts.

## What this is
A foundation-ladder M(C) v1 build that ran 23:59–00:07 on 2026-06-09 and wrote files to the repo
**despite the ladder being deferred** under current sequencing (current goal = tool-integration +
skill/agent/tool-stack tuning FIRST, ladder AFTER). An earlier kill caught only `model_reasoning_effort=xhigh`;
this build ran at `high` and completed before the kill.

## Files (do NOT stage, promote, or build from these now)
- `system_v5/ops/formal_scouts/foundation_mc_v1_admissibility_object_envelope.py`
- `system_v5/ops/formal_scouts/foundation_mc_v1_admissibility_object_jax.py`
- `system_v5/ops/formal_scouts/foundation_mc_v1_admissibility_object_pytorch.py`
- `system_v5/julia_carrier/foundation_mc_v1_admissibility_object_julia.jl`
- their result JSONs (gitignored).

## Why keep, not delete
The receipt is fenced and not garbage:
`classification=scratch_diagnostic`, `all_pass=True`, `promotion_allowed=False`, `formal_admission_allowed=False`,
source-pinned. It is a mistake relative to current sequencing, but it is potentially useful when the ladder
actually resumes. Deleting it silently while session state is messy is the wrong move.

## Disposition
- Now: leave in place, quarantined. Do not let it drive the current tool-tuning task.
- Later (owner's call): either (a) move into a quarantine/maintenance folder, or (b) remove in one explicit
  cleanup commit — not a silent delete.
- Do not resume ladder/M(C) work until the tuned tool-stack has a clean post-patch integration receipt.
