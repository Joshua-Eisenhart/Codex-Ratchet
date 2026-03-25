# CURRENT_CALLABLE_STACK_AND_FIRST_MONITORED_LAUNCHES__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-10
Role: compress the current callable skill stack into one controller-facing operational memo and name the first monitored launches

## 1) Current callable stack

### Core repo-understanding skill
- `ratchet-a2-a1`

### Upper-loop control spine
- `thread-closeout-auditor`
- `a2-brain-refresh`
- `a1-from-a2-distillation`
- `a2-a1-memory-admission-guard`
- `brain-delta-consolidation`

### External research refinery spine
- `external-research-refinery-launcher`
- `pro-return-instant-audit`
- `external-research-return-ingest`

### Controller automation spine
- `thread-dispatch-controller`
- `thread-run-monitor`
- `closeout-result-ingest`

## 2) What the stack now covers

The system now has callable skills for:
- bounded thread launch
- overrun / low-yield detection
- closeout prompt and packet capture
- A2 refresh
- A1-from-A2 derivation
- A2/A1 write-gate discipline
- external research launch
- external return audit
- external return routing
- delta consolidation

The remaining bottleneck is no longer missing workflow law.
It is actual execution and capture of returns.

## 3) First monitored launches

### Launch 1: internal `Constraints. Entropy` revisit lane

Primary runbook:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/SKILL_STACK_APPLICATION__CONSTRAINTS_ENTROPY_REVISIT_LANE__v1.md`

Use:
- `a2-brain-refresh`
- `a1-from-a2-distillation`
- `a2-a1-memory-admission-guard`
- `brain-delta-consolidation`

Monitor with:
- `thread-run-monitor`

Close out with:
- `thread-closeout-auditor`
- `closeout-result-ingest`

Expected bounded outputs:
- one `A2_UPDATE_NOTE`
- one `A1_IMPACT_NOTE`
- one admitted delta set

Stop condition:
- do not go past the bounded delta set
- do not reopen warm notes as raw doctrine sources

### Launch 2: external entropy / Carnot / Szilard refinery lane

Primary operator checklist:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/EXTERNAL_LANE_OPERATOR_CHECKLIST__ENTROPY_CARNOT_SZILARD__2026_03_10__v1.md`

Secondary runbook/context:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/SKILL_STACK_APPLICATION__ENTROPY_CARNOT_SZILARD_EXTERNAL_LANE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/EXTERNAL_LAUNCH_PACKET__ENTROPY_CARNOT_SZILARD__2026_03_10__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/EXTERNAL_RETURN_AUDIT_AND_INGEST_PACKET__ENTROPY_CARNOT_SZILARD__2026_03_10__v1.md`

Use:
- `external-research-refinery-launcher`
- `pro-return-instant-audit`
- `external-research-return-ingest`
- then:
  - `a2-brain-refresh`
  - `a1-from-a2-distillation`
  - `a2-a1-memory-admission-guard`
  - `brain-delta-consolidation`

Monitor with:
- `thread-run-monitor`

Close out with:
- `thread-closeout-auditor`
- `closeout-result-ingest`

Expected bounded outputs:
- full external research output contract
- audit result
- one bounded A2 reduction path if audit passes

Stop condition:
- if the external return is weak, stop at hold/rerun
- do not ingest into A2 without audit pass
- use the narrow `204341Z` boot zip named in the launch packet, not the earlier oversized `204020Z` build

## 4) Launch ordering

Recommended immediate order:

1. run the internal `Constraints. Entropy` revisit lane
2. in parallel, launch the external entropy / Carnot / Szilard research lane
3. monitor both with the same stop law
4. ingest returns
5. consolidate into small A2/A1 deltas

Reason:
- this matches the current next-batch priority read
- one lane is internal and already reduced enough for bounded revisit
- one lane is external and ready for Pro/deep-research execution

## 5) Current no-spawn rule

Do not open broader new lanes until one of the two launches above has either:
- completed with bounded outputs
- or failed and been diagnosed through the monitor/closeout path

Priority remains:
- run what is already prepared
- capture outputs cleanly
- consolidate into A2/A1 deltas

## 6) Controller summary

The system is now ready to stop building first-order skill scaffolding and start using the skills on real lanes.

The first two monitored launches should be:
- the internal `Constraints. Entropy` revisit lane
- the external entropy / Carnot / Szilard refinery lane

Everything after that should be driven by:
- actual monitored outputs
- closeout packets
- audited external returns
- admitted delta sets
