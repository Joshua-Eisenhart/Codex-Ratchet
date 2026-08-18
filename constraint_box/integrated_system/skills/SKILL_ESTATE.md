# Curated ConstraintBox wave skill estate

This pack contains the seven named Layer-1 skills and their exact transitive
dependencies. It is not the complete 54-folder global estate.

## Layer 1

| Skill | Current disposition | Meaning |
|---|---|---|
| `cb-wave-self-loop` | EXTEND | Script-backed and path-portable; bounded score/no-improvement result only. |
| `cb-context-strategy-wave` | REUSE | Script-backed context projection. |
| `cb-exploration-wave` | REUSE | Script-backed rival-branch harvest. |
| `cb-goodhart-wave` | COMPOSE | Metadata plus context/proxy/scope/drift children. |
| `cb-object-loop-wave` | EXTEND | Path-portable object loop with 12 cell dependencies; no promotion authority. |
| `cb-maintenance-wave` | REUSE | Parameterized model-free maintenance. |
| `cb-management-plane` | EXTEND | Path-portable model-free management proof; route truth remains `NOT_FULL`. |

`wave.json` is definition metadata, never execution evidence. Instruction-only
skills can supply a role or procedure but cannot be counted as an executed
child without an operation receipt.

The portable bundle sets these run-data paths:

```text
CB_SKILLS_ROOT=<bundle>/PROJECT/constraint_box/integrated_system/skills
CB_BOX_ROOT=<bundle>/PROJECT/constraint_box
CB_MMM_ROOT=<bundle>/PROJECT/constraint_box/integrated_system/mmms/primary
```

The copied executable scripts resolve their roots from these run-data values.
The remaining EXTEND labels concern incomplete operational evidence, not
machine-specific import paths. Instruction-only references also refuse missing
packet-bound inputs instead of reaching into a workstation directory.

Promotion allowed: false.

## Public runnable cohort

The contained product exposes only the following direct, model-free runners:

| Public id | Script | Expected child result |
|---|---|---|
| `cb-maintenance-wave` | `skills/cb-maintenance-wave/scripts/run_maintenance_wave.py` | `READY` |
| `cb-context-strategy-wave` | `skills/cb-context-strategy-wave/scripts/run_context_strategy.py` | `CONTEXT_SNAPSHOT_READY` |
| `cb-exploration-wave` | `skills/cb-exploration-wave/scripts/run_exploration.py` | `ANTICHAIN_OPEN` |

Run them through the contained public surface:

```text
python integrated_system/scripts/run_wave.py list
python integrated_system/scripts/run_wave.py inspect cb-maintenance-wave
python integrated_system/scripts/run_wave.py run cb-maintenance-wave
```

`run_wave.py` pins the script and definition digests recorded in
`ACTIVE_WAVES.json`, checks declared inputs, rejects host-path escapes, runs
with `python -I`, and writes a subprocess receipt. A timeout, cancellation,
missing/tampered dependency, child return-code mismatch, or child status
mismatch is a HOLD/REFUSE; it is never relabeled as a successful wave.

The composite names (`cb-goodhart-wave`, `cb-object-loop-wave`,
`cb-premortem-wave`, `cb-failure-wave`, `cb-repair-wave`, and
`cb-strategy-wave`, among others) remain authored/specification surfaces. They
are listed as inactive until their complete executable dependency graph is
contained and has an independent runner receipt. A `wave.json` alone is not
execution evidence. No public runner calls a model or provider.
