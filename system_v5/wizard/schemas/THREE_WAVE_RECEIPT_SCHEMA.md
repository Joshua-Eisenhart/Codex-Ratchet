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
source_slice_used:
wiki_sources_read:
memory_surfaces_read:
  codex:
  claude:
  hermes:
raw_receipt_refs:
accepted_canonical_receipts:
input_basis:
claim_tested:
execution_evidence:
worker_surface: codex_native | claude_bridge | gemini | tool | controller_local
status: completed | blocked | timed_out | rerouted | superseded | simulated | deferred
artifact_or_conclusion:
blocked_reason:
evidence_boundary:
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
  operational_outcome: pass_to_execution | split_smaller | harden_then_execute | block_for_missing_input | kill
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
      immediate_action:
      owner_lane:
      owner:
      check:
      done_condition:
      success_check:
      stop_condition:
      artifact_output_surface:
      status: salience_only | proposal | bounded_work_candidate | ready_for_execution | executed | accepted | partial | blocked | deferred
      payoff:
      use_when:
      blocked_if:
      scout_status: scouted | not_scouted | blocked
```

## Bounded-Work Compile Gate

The Wizard is a general bounded-work compiler. Follow-up options cannot imply execution readiness from council agreement, salience lift, source-and-lift receipts, or polished language. Readiness requires a domain compile gate.

```yaml
bounded_work_compile_gate:
  target:
  immediate_action:
  owner_lane:
  success_check:
  stop_condition:
  artifact_output_surface:
  status: salience_only | proposal | bounded_work_candidate | ready_for_execution | executed | accepted | partial | blocked | deferred
```

For Codex Ratchet adapter sim/probe work, queue visibility requires the stricter packet profile:

```yaml
sim_packet_compile_gate:
  sim_stage:
  sim_claim:
  sim_carrier_fixture:
  sim_tool_function_or_admitted_coupling:
  sim_positive_check:
  sim_negative_or_boundary_check:
  sim_expected_result_path:
  sim_prior_receipts:
  sim_status: salience_only | queue_candidate | runner_done | admitted | partial | blocked
```

Strict sim fields are required only when the option is sim-classified and queue-visible: `queue_candidate`, `runner_done`, or `admitted`. Reject queue-visible sim packets when they are polished prose without a runnable packet, include multiple stages or claims, mention lego/coupling/bridge/topology/emergence/axis work without exact prior receipts, use source-and-lift receipts as runner evidence, omit a negative/boundary check, omit an expected result path, or cite only a library-level tool instead of an exact function surface.

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
verdict: accept | repair | downgrade | quarantine | kill
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

## Source-And-Lift Receipt Gate

Run this gate before expanding a three-wave council result into more routes, larger fanout, or canonical examples. The gate binds execution claims; MMMs and mini-MMMs only shape salience.

```yaml
source_and_lift_receipt_gate:
  gate_id:
  route_id:
  council: decision | failure | follow_up
  source_bundle_ref:
  source_slice_used:
  loaded_salience_surfaces:
  raw_launch_receipt_refs: []   # may be empty for blocked/deferred/simulated routes
  raw_completion_receipt_refs: []  # must be non-empty for completed route claims
  claim_tested:
  claim_scope:
  operation_changed:
  execution_evidence:
  evidence_path_or_observation:
  terminal_status: completed | blocked | timed_out | rerouted | superseded | simulated | deferred
  not_run_or_simulated_accounting:
  evidence_boundary:
  lift_probe:
  counter_probe_seed:
  label_strip_result:
  counter_probe_result:
  strongest_omitted_falsifier:
  salience_status:
    load_axis:
    salience_axis:
    counter_probe_axis:
    corpus_axis:
  gate_verdict: pass | harden | quarantine | kill
  expansion_permission: true | false
```

The four checks are separate:

- `source_slice_used` says which source object actually mattered.
- `execution_evidence` says what route action actually happened.
- `lift_probe` says whether loaded salience changed the reasoning move, not only the vocabulary.
- `not_run_or_simulated_accounting` says what must receive zero completion credit.

Execution truth and salience lift never satisfy each other. A route may show `strong_lift` and still receive zero execution credit. A route may execute correctly while the loaded surface shows `no_lift`.

`gate_verdict` is scoped to `claim_tested` and `claim_scope`. `pass` does not authorize broader Wizard expansion unless `expansion_permission` is true and the evidence boundary explicitly names that expansion.

Fail closed when raw launch or completion receipt refs are missing for a claimed completed route, when the evidence is self-report only, when controller synthesis is counted as route work, or when the label-stripped probe leaves only style fit.

For non-completed routes, keep the raw receipt ref keys present even if they are empty. The zero-credit state belongs in `not_run_or_simulated_accounting`.
