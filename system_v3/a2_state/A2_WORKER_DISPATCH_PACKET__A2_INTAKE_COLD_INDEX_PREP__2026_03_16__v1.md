# A2_WORKER_DISPATCH_PACKET__A2_INTAKE_COLD_INDEX_PREP__2026_03_16__v1

Status: ACTIVE OPERATOR SURFACE / NONCANON
Date: 2026-03-16
Owner: current `A2` controller
Role: exact bounded `A2_WORKER` dispatch packet for turning the intake bloat audit into a reusable cold-index prep artifact

## Dispatch identity

- `dispatch_id: A2_WORKER__A2_INTAKE_COLD_INDEX_PREP__2026_03_16__v1`
- `thread_class: A2_WORKER`
- `model: GPT-5.4 Medium`
- `BOOT_SURFACE: /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `ROLE_LABEL: A2H Refined Fuel Non-Sims`
- `ROLE_TYPE: A2_HIGH_REFINED_FUEL_NON_SIMS`
- `ROLE_SCOPE: one bounded pass to produce a cold-index prep artifact for A2 intake de-bloat routing`

## Source artifacts

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/processed/2026-03-16/A2_WORKER__A2_INTAKE_BLOAT_TRIAGE__2026_03_15__v1__return.txt`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`

## BOUNDED_SCOPE

Run one bounded pass that:
- produces one machine-readable or markdown cold-index prep artifact listing which intake classes should stay warm, go cold, or remain blocked
- does not move or rename any intake batch

Do not:
- mutate intake artifacts
- redesign intake status taxonomy
- touch runs, A2 state, or specs

## EXPECTED_OUTPUTS

- one bounded cold-index prep artifact under `work/audit_tmp`
- one raw returned result file written by the worker itself into:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__A2_INTAKE_COLD_INDEX_PREP__2026_03_16__v1__return.txt`
- one raw closeout staging text file written by the worker itself into:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__A2_INTAKE_COLD_INDEX_PREP__2026_03_16__v1.txt`

## Exact prompt to send

```text
Use $ratchet-a2-a1.

Use the current A2 boot:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md

Run one bounded A2_HIGH_REFINED_FUEL_NON_SIMS pass only.

dispatch_id: A2_WORKER__A2_INTAKE_COLD_INDEX_PREP__2026_03_16__v1
ROLE_LABEL: A2H Refined Fuel Non-Sims
ROLE_TYPE: A2_HIGH_REFINED_FUEL_NON_SIMS
ROLE_SCOPE: one bounded pass to produce a cold-index prep artifact for A2 intake de-bloat routing

Use only these artifacts:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/processed/2026-03-16/A2_WORKER__A2_INTAKE_BLOAT_TRIAGE__2026_03_15__v1__return.txt
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md

Task:
- produce one machine-readable or markdown cold-index prep artifact listing which intake classes should stay warm, go cold, or remain blocked
- do not move or rename any intake batch

Rules:
- do not mutate intake artifacts
- do not redesign intake status taxonomy
- do not touch runs, A2 state, or specs
- stop after one bounded pass

Before your final answer:
- write the exact final closeout body to:
  - /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__A2_INTAKE_COLD_INDEX_PREP__2026_03_16__v1__return.txt
  - /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__A2_INTAKE_COLD_INDEX_PREP__2026_03_16__v1.txt
- if the folders do not exist, create them
- do not ask the operator to save, paste back, or carry files
- if you cannot self-save, report that exact blocker and stop
```

## STOP_RULE

Stop after one cold-index prep artifact.
