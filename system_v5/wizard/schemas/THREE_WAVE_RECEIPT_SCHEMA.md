# Three-Wave Receipt Schema

Status: proposal / salience-probe stage.

Receipt rules bind; MMMs and mini-MMMs lift.

## Common Receipt Fields

```yaml
council: decision | failure | follow_up
wave_index: 1 | 2 | 3
role:
route_id:
task_card_ref:
loaded_salience_surfaces:
suppressed_adapters:
source_bundle_ref:
wiki_sources_read:
memory_surfaces_read:
  codex:
  claude:
  hermes:
raw_receipt_refs:
accepted_canonical_receipts:
input_basis:
worker_surface: codex_native | claude_bridge | gemini | tool | controller_local
status: completed | blocked | timed_out | rerouted | superseded | simulated | deferred
artifact_or_conclusion:
blocked_reason:
handoff:
receipt_states:
  spawned:
  completed:
  accepted:
  superseded:
  late:
  blocked:
  deferred:
  simulated:
strongest_omitted_falsifier:
```

## Decision Council Additions

```yaml
decision:
  selected_move:
  live_alternatives:
  evidence_boundary:
  accepted_risks:
  risky_claims_for_failure:
  falsifier_seed:
```

## Failure Council Additions

```yaml
failure:
  verdict: kill | quarantine | harden | pass
  target_claim:
  strongest_falsifier:
  decisive_check:
  hidden_assumption:
  required_hardening:
  return_to_decision: true | false
```

## Follow-up Council Additions

```yaml
follow_up:
  options:
    - label:
      target:
      owner:
      check:
      done_condition:
      payoff:
      use_when:
      blocked_if:
      scout_status: scouted | not_scouted | blocked
```

## Canonical Receipt Gate

A canonical receipt requires:

- assigned route id;
- source slice;
- claim tested;
- evidence path or concrete observation;
- terminal status;
- explicit supersession relation if rerouted.

Duplicate receipts for the same route/source/claim are supplemental by default, not canonical. Controller synthesis cannot increase receipt count.

## Audit Receipt Fields

```yaml
audit_id:
auditor_model:
auditor_runtime:
audit_mode: execution_truth | salience_lift
audit_register: operational_plain | adversarial | contract_only | salience_measure
worker_receipts_inspected:
artifacts_inspected:
salience_surface_seen: none | loaded_for_measurement | quoted_object_only | execution_audit_contaminated
execution_evidence:
self_report_rejected_or_used:
route_contract_checked:
failure_modes_checked:
salience_lift_observed:
drift_signal_observed:
counter_probe_result:
verdict: pass | harden | quarantine | kill
confidence:
open_questions:
fail_closed_triggered: true | false
reason:
```

Execution audit fails closed when auditor and worker inhabit the same salience surface, when execution evidence is self-report only, or when claimed subagents/subsubagents lack launch and completion receipts.

Salience audit does not fail closed on vocabulary alone. It records load, lift, drift, no-lift, stale-surface, cosmetic-only, and counter-probe survival as continuous or adversarial-continuous signals.

## Salience Status Axes

```yaml
salience_status:
  load_axis: missing | present_not_loaded | loaded | stale_loaded
  salience_axis: drift | no_lift | lift | strong_lift
  counter_probe_axis: untested | folded | partial_survival | survived
  corpus_axis: unnamed | named_stale | named_current | refreshed_from_wiki
```

The axes do not collapse into one score. A surface may be `loaded`, show `lift`, and still be `folded` under counter-probe.
