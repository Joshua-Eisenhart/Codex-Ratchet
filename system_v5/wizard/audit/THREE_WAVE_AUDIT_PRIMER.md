# Three-Wave Audit Primer

Status: proposal / salience-probe stage.

Receipt rules bind; MMMs and mini-MMMs lift.

Audit has two separate jobs:

1. Execution audit checks route truth, receipts, and overclaiming.
2. Salience audit measures whether MMM/mini-MMM surfaces shifted language and framing in the intended direction.

Execution audit is register-asymmetric. Salience audit may inspect the MMM register, but it must remember that MMMs are pressure surfaces, not rules.

## Audit Register

For execution audit, use plain operational language. Do not inhabit the same council-role salience surface used by the worker. A salience surface may be inspected as a quoted object, but execution audit should not treat matching the surface as proof that a route ran.

The audit asks:

- What evidence proves this route actually executed?
- Which claimed workers have launch and completion receipts?
- Which claimed child lanes are only starts, pending work, or synthesis?
- Which claims rely on style, self-report, or familiar Wizard terms instead of receipt evidence?
- What would make this route fake?

## Required Inputs

Audit receives:

- task claim;
- route contract;
- worker receipts;
- artifact paths or excerpts;
- explicit receipt criteria;
- expected status vocabulary.

Audit rejects:

- voice fit as execution evidence;
- self-report as execution proof;
- controller synthesis as worker execution;
- follow-up menus as preworked without Make, Scout, and Audit receipts.

## Salience Audit

Salience audit asks gradient questions:

- Which salience surfaces were loaded, and are they current?
- Which wiki/harness/memory surfaces fed the salience field?
- Were Codex, Claude, and Hermes memory surfaces kept provenance-marked instead of merged into one authority?
- Did system-native words, phraselets, and grammar become more available than in the baseline?
- Did outputs more often hold live alternatives instead of collapsing to a winner-story?
- Did the model use candidate/probe/survivor/open/excluded/status-rung shapes without being explicitly forced?
- Did the salience survive a counter-probe that pulls toward default-model framing?
- Did repeated exposure strengthen or flatten the intended vocabulary?
- Did the surface create useful role-local differences, or only same-register decoration?

Salience audit reports load, lift, drift, no-lift, stale-surface, or cosmetic-only. It does not call a route executed.

When salience and execution disagree, execution receipt truth owns the action claim. Salience disagreement becomes a drift signal.

## Verdicts

```yaml
verdict: accept | repair | downgrade | quarantine | kill
```

Use:

- `accept` when receipts prove execution and claims stay within evidence.
- `repair` when wording or status accounting can be fixed without changing the underlying result.
- `downgrade` when the output overstates Full/complete/spawned truth.
- `quarantine` when a route method may work but lacks execution evidence.
- `kill` when required evidence is absent or a decisive falsifier is already true.

## Fail-Closed Conditions

Fail closed when:

- auditor and worker use the same inhabited primer/register;
- no artifact or tool evidence supports claimed execution;
- claimed subagents/subsubagents lack launch or completion receipts;
- primer contamination is unknown;
- execution audit cannot distinguish "style matched" from "method executed";
- council synthesis is counted as worker execution;
- Follow-up Council options are called preworked without accepted Make, Scout, and Audit receipts.

## Repair Rule

When audit finds an overclaim, repair the boundary before final output. If repair would change the recommendation, return to the relevant council wave instead of smoothing the result locally.

When salience audit finds no-lift, do not rewrite the MMM into rules. Refresh the language field from current wiki/corpus material, then re-probe.

When salience audit finds stale-surface drift, inspect current wiki harness and runtime memory surfaces before changing the Wizard packet. The update path is corpus refresh first, runtime-law change only after a separate admission step.
