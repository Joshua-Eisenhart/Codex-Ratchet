# A2 Antigravity Finished-Run Audit

Date: 2026-03-24
Author: Codex audit pass
Scope: Current finished-run state after latest `run_all_sims.py` completion, plus bridge/doc/report contradictions that affect interpretation.

## Why This Exists

Recent NotebookLM and Antigravity-facing summaries have drifted across multiple repo eras:

- early bridge / graph repair state
- mid-run `129 / 128 / 1` state
- temporary narrowed `135 / 135 / 0` probe read
- current widened runner state including negative / graveyard / orthogonality lanes

This file is intended to anchor Antigravity on the actual finished-run artifacts now on disk.

## Current Finished-Run State

Source of truth:
- `system_v4/probes/a2_state/sim_results/unified_evidence_report.json`

Finished-run values:
- timestamp: `2026-03-24T23:43:22.093442+00:00`
- SIM entries: `51`
- total tokens: `146`
- PASS: `128`
- KILL: `18`

This is the current live counted state.

It supersedes earlier same-day states such as:
- `129 / 128 / 1`
- `135 / 135 / 0`

Those earlier reads are still useful as historical slope, but they are not the current finished-run truth.

## Main Correction To Prior Reads

The runner is not the old baseline anymore.

`system_v4/probes/run_all_sims.py` already includes:
- `axis_orthogonality_suite.py`
- `neg_commutative_engine_sim.py`
- `neg_infinite_d_sim.py`
- `neg_single_loop_sim.py`
- `neg_classical_probability_sim.py`
- `neg_no_dissipation_sim.py`
- `deep_graveyard_battery.py`
- `extended_graveyard_battery.py`

So any external read claiming the SIM pipeline is still only the old `18` baseline probes is stale.

## Current KILL Inventory

The current `18` KILL tokens come from the following files:

### Negative / falsifier lane
- `neg_infinite_d_sim.py`
  - `S_NEG_INFINITE_D_V1`
  - `INFINITE_D_DIVERGENCE`
- `neg_single_loop_sim.py`
  - `S_NEG_SINGLE_LOOP_V1`
  - `SINGLE_LOOP_SATURATES`
- `neg_no_dissipation_sim.py`
  - `S_NEG_NO_DISSIPATION_V2`
  - `NO_DISSIPATION_THERMAL_DEATH`

### Moloch lane
- `sim_moloch_trap_field.py`
  - `S_MOLOCH_FIELD_V1`
  - `CLASSICAL_AGENTS_SURVIVED_UNEXPECTEDLY`

### Graveyard / comparator battery lane
- `deep_graveyard_battery.py`
  - `S_NEG_C3` — `CPTP Violation`
  - `S_NEG_X2` — `Chirality Swap`
  - `S_NEG_Ti` — `No Measurement`
  - `S_NEG_Te` — `No Unitary Drive`
  - `S_NEG_Fi` — `No Spectral Proj`
  - `S_NEG_C4` — `Force Identity`
  - `S_CMP_F01_N01` — `COMMUTATIVE_BLOCKS_AXIS6_PRECEDENCE`
  - `S_CMP_C6_C8` — `SINGLE_LOOP_FAILS_NET_RATCHET_720`
- `extended_graveyard_battery.py`
  - `S_CMP_3` — `C3∧C5 Entropy Order`
  - `S_CMP_4` — `F01∧N01∧C3 TripleLock`
  - `S_CMP_5` — `C6∧X2 DualLoop+Chiral`
  - `S_NEG_SCRAMBLE` — `Random Order`
  - `S_NEG_SYMMETRIC` — `Self-Adjoint`
  - `S_NEG_DECOHERE` — `Max Decoherence`

## Immediate Interpretation Of The 18 KILLs

These KILLs are not all the same class.

### Likely expected / intended KILLs
These appear to be deliberate negative or graveyard-boundary falsifiers and should not automatically be treated as regressions:
- `neg_infinite_d_sim.py`
- `neg_single_loop_sim.py`
- `neg_no_dissipation_sim.py`
- most or all of `deep_graveyard_battery.py`
- most or all of `extended_graveyard_battery.py`

### Possibly meaningful / requires judgment
- `sim_moloch_trap_field.py`
  - `CLASSICAL_AGENTS_SURVIVED_UNEXPECTEDLY`

This one may be intended as a falsifier, but it reads more like a live contradiction than a neatly bounded “expected fail” surface. Antigravity should inspect this one separately rather than grouping it blindly with the graveyard battery.

## Important Non-KILL Problems Still Present

The finished run is not clean even apart from the `18` KILLs.

### Process FAIL but evidence PASS
These files still exit nonzero or otherwise fail process-level health while contributing PASS tokens:
- `math_foundations_sim.py`
- `godel_stall_sim.py`
- `navier_stokes_qit_sim.py`
- `quantum_gravity_sim.py`
- `chemistry_sim.py`
- `full_8stage_engine_sim.py`
- `nlm_batch2_sim.py`
- `rock_falsifier_enhanced_sim.py`

This means “counted evidence” and “healthy executable” still diverge.

### NO_TOKENS / timeout / contract residue
These files are still not producing clean counted evidence:
- `constraint_gap_sim.py` — `FAIL`, `NO_TOKENS`
- `neg_commutative_engine_sim.py` — `PASS`, `NO_TOKENS`
- `neg_classical_probability_sim.py` — `PASS`, `NO_TOKENS`
- `type2_engine_sim.py` — `PASS`, `NO_TOKENS`
- `axis_orthogonality_suite.py` — `TIMEOUT`, `NO_TOKENS`
- `egglog_graph_rewrite_probe.py` — `FAIL`, `NO_TOKENS`
- `consciousness_sim.py` — `FAIL`, `NO_TOKENS`

These are not headline KILLs, but they are real trust breaks in the runner contract.

## Stale Secondary Surfaces

The finished run has not propagated into the secondary reporting layer.

`system_v4/probes/a2_state/sim_results/latest_triage.json` is stale and still says:
- timestamp: `2026-03-24T11:19:12.107872+00:00`
- `128 PASS`
- `1 KILL`
- `S_SIM_AXIS3_ORTHOGONALITY_V1`

That file is no longer aligned with the current finished-run report.

Antigravity should therefore treat:
- `unified_evidence_report.json`
as the current runner truth,
and treat:
- `latest_triage.json`
- `probe_evidence_graph.json`
- `probe_evidence_graph_audit.md`
- `A2_FULL_SYSTEM_HEALTH__v1.md`
as potentially stale until regenerated after the finished run.

## Graph-Side Warning Still Active

Separate from the probe runner, the graph-policy layer still looks unresolved unless newer graph audits were generated elsewhere.

Current graph-policy evidence still on disk:
- `system_v4/a2_state/audit_logs/POLICY_ENGINE_EVALUATION_REPORT__v1.md`
- `system_v4/a2_state/audit_logs/GRAPH_HEALTH_DASHBOARD__v1.md`

These still report:
- `418` Rule 1 admissibility violations in `a2_low_control_graph_v1.json`
- `811` Rule 1 admissibility violations in `system_graph_a2_refinery.json`
- `164` Rule 5 graveyard-live edge violations in `a2_high_intake_graph_v1.json`
- `259` Rule 5 graveyard-live edge violations in `system_graph_a2_refinery.json`
- severe fragmentation in low-control and mid-refinement graphs

## Nested Graph Contradiction

There is still a direct contradiction between:
- `system_v4/a2_state/audit_logs/NESTED_GRAPH_BUILD_REPORT__v1.md`
and
- `system_v4/a2_state/graphs/nested_graph_v1.json`

The build report says:
- `11034` nodes
- `22599` edges
- `8903` cross-layer edges

But the actual `nested_graph_v1.json` on disk is still empty:
- `0` nodes
- `0` edges

This needs explanation. Either:
- the build persisted elsewhere,
- the report was written without the graph being durably saved,
- or a later overwrite/truncation occurred.

## NotebookLM / External Audit Caution

Do not anchor on external summaries that:
- claim the runner is still the old flat baseline,
- refer to nonexistent files such as `system_v4/skills/graph_policy_checker.py`,
- or treat older graph or handoff state as present truth.

At this point the repo has moved faster than those summaries.

## What Antigravity Should Do Next

1. Classify the `18` current KILLs into:
   - expected negative / graveyard KILLs
   - meaningful contradictions
   - accidental residue

2. Decide whether `sim_moloch_trap_field.py` is:
   - a healthy falsifier,
   - or a real unresolved contradiction.

3. Audit the `NO_TOKENS` lane and determine whether each case is:
   - schema mismatch,
   - stale output mapping,
   - timeout,
   - or actual missing evidence.

4. Audit the process-FAIL / evidence-PASS files and decide whether they are:
   - acceptable partial-write scripts,
   - or runtime defects that must be fixed before trust can increase.

5. Reconcile graph truth:
   - `POLICY_ENGINE_EVALUATION_REPORT__v1.md`
   - `GRAPH_HEALTH_DASHBOARD__v1.md`
   - `NESTED_GRAPH_BUILD_REPORT__v1.md`
   - `nested_graph_v1.json`

## Questions For Antigravity

Please answer the following with repo-grounded evidence:

1. Of the current `18` KILLs, which are expected falsifier/graveyard KILLs that should remain KILL?
2. Which KILLs represent actual contradictions or failed claims rather than healthy negative tests?
3. Is `sim_moloch_trap_field.py` behaving as intended?
4. Why is `axis_orthogonality_suite.py` timing out instead of emitting a counted result?
5. Why do `constraint_gap_sim.py`, `neg_commutative_engine_sim.py`, `neg_classical_probability_sim.py`, `type2_engine_sim.py`, `egglog_graph_rewrite_probe.py`, and `consciousness_sim.py` still show `NO_TOKENS`?
6. Why are multiple positive-lane probes still `process_status = FAIL` while emitting PASS evidence?
7. Are the graph-policy reports current, or stale relative to repaired graph artifacts?
8. Why does `NESTED_GRAPH_BUILD_REPORT__v1.md` claim a successful build while `nested_graph_v1.json` remains empty?

## Working Model

The project has definitely ratcheted upward.

But the finished-run truth is now:
- wider
- harsher
- and more honest

The system is no longer mainly suffering from “missing work.”
It is suffering from:
- mixed KILL semantics
- stale secondary reports
- incomplete runner/report contracts
- graph persistence / graph-audit contradictions

That is the state Antigravity should audit from.
