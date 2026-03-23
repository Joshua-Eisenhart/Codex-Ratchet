# THREAD_CLOSEOUT_AUDIT_AND_NEXT_BATCH_PLAN__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-09
Role: audit the first thread-closeout pass, record immediate system improvements, and state the next batch priorities

## 1) Audit read

The thread-closeout prompt was sent to the overlong worker threads.

Current controller-visible result:
- the closeout surface exists
- the threads processed the prompt
- but there is no standard repo-held return sink yet for the closeout packets

That means the system currently has:
- a send surface
- a diagnosis law
- but not yet a reliable artifact collection path for the returned audits

So the first audit conclusion is:
- closeout prompting now exists
- closeout capture still does not

## 2) Strongest current gains

The strongest recent structural gains are:

### A) Worker stop law now exists
- `work/zip_subagents/THREAD_CLOSEOUT_AUDIT_PROMPT__v1.md`
- `system_v3/a2_state/THREAD_RUN_DIAGNOSIS_AND_STOP_RULES__v1.md`

This is a real upgrade because overlong worker threads can now be asked for:
- strongest outputs
- lane diagnosis
- stop/continue/correct decision
- handoff packet

### B) External research refinery lane now exists
- concrete entropy / Carnot / Szilard external-research dropin exists
- narrow Pro boot exists
- the corrected narrow build now really is narrow

This means a new parallel refinery lane is now structurally available.

### C) Skill bottleneck is now explicit
- `system_v3/a2_state/SKILL_STACK_AND_BRAIN_UPDATE_STABILIZATION__v1.md`

This matters because the system now has a much clearer read that:
- inconsistent A2/A1 brain updates are partly a skill-layer failure
- not just a doc or thread-discipline failure

## 3) Main current weakness

The current weak point is not lack of worker output.

It is:
- thread outputs are still not consistently being captured as bounded reusable closeout artifacts
- brain updates still depend too much on thread-carried procedure
- controller routing still lacks a standard thread-result intake path

So the immediate bottleneck has shifted to:
- `capture`
- `diagnose`
- `stop cleanly`
- `convert returned work into a small number of reusable deltas`

## 4) Immediate system improvements needed

### Improvement 1: closeout result sink

Add one standard sink for returned closeout packets.

Minimum requirement:
- one fixed location or packet family for thread closeout results
- role label
- strongest outputs
- lane diagnosis
- stop/continue/correct decision
- handoff packet

Without this, the closeout prompt improves thread behavior but not controller memory.

### Improvement 2: thread closeout auditor skill

This is now the first skill to build.

It should:
- send the closeout prompt
- collect the result
- classify the lane
- preserve the packet in the repo

### Improvement 3: thread run monitor

Needed soon after the closeout auditor.

It should detect:
- overlong runs
- repeated low-yield continuation
- duplicate-lane behavior
- metadata-polish-only residue
- waiting-on-external states

### Improvement 4: A2 refresh and A1-from-A2 skill pair

These remain the next critical process skills after closeout handling.

Reason:
- stopping threads cleanly is necessary
- but the system still needs consistent conversion of outputs into refreshed A2 and derived A1

## 5) Next batch priorities

Current next-batch read from the queue surfaces:

### Priority A: `Constraints. Entropy` revisit anchor pair

Highest-value revisit anchor remains:
- `BATCH_refinedfuel_constraints_entropy_term_conflict__v1`
- `BATCH_refinedfuel_constraints_term_conflict__v1`

Use existing child fence packets as direct context:
- `BATCH_A2MID_constraints_entropy_chain_fences__v1`
- `BATCH_A2MID_constraints_foundation_governance_fences__v1`

Why first:
- still the highest-density refined-fuel revisit cluster
- already explicitly nominated by the residual inventory closure audit

### Priority B: duplicate-family quarantine

Keep the typo-family duplicate in quarantine:
- `BATCH_a2feed_grok_unified_phuysics_source_map__v1`

Do not spend a fresh reduction pass on it as if it were a new live doctrine parent.

### Priority C: archive-side revisit only if wanted

If one more bounded archive-side packet is wanted, the next clean target remains:
- `BATCH_archive_surface_heat_dumps_root_family_split__v1`

This is lower priority than Priority A.

### Priority D: launch external research refinery lane

The entropy / Carnot / Szilard external-research pack is ready.

That means a real next parallel batch can be:
- one Pro/deep-research external lane
- then one instant audit
- then one bounded A2 reduction from the returned report

## 6) Skills and automation read

Near-term priority order:

1. `thread closeout auditor`
2. `A2 brain refresh`
3. `A1-from-A2 distillation`
4. `A2/A1 memory admission guard`
5. `external research refinery launcher`
6. `Pro-return instant audit`
7. `brain delta consolidation`

Automation-facing counterparts:

- `thread-run-monitor`
- `thread-dispatch-controller`
- later:
  - `closeout-result-ingest`
  - `external-research-return-ingest`

## 7) Controller conclusion

The closeout pass was useful, but it exposed the next missing layer:

- the system can now ask threads to stop cleanly
- but it still needs a standard capture and ingestion path for those returned audits

So the best next controller move is:
- not more broad worker spawning
- but one bounded improvement to the thread-result capture path

Then:
- run the `Constraints. Entropy` revisit batch
- and launch the entropy / Carnot / Szilard external-research lane in parallel

