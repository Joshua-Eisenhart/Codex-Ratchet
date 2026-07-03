# Retrocausal Possibility Field Sim And Wizard Method

Status: design/method document, not a formal-sim admission, not Axis0 closure,
not a physics proof.

Date: 2026-05-26

Primary source surface:
`system_v5/docs/JOSHUA_EISENHART_AXIS0_PHYSICS_MODEL_CORE_20260526.md`

Purpose:

This document explains how to make Joshua Eisenhart's retrocausal
possibility-constraint structure the primary object of simulation and LLM
reasoning, instead of letting agents translate it into familiar proxies such as
forward dynamics, generic entropy, PEPS3D labels, QIT metric bakeoffs, or FEP
analogies.

It also explains how Wizard-like LLM councils should be modified so they can
preserve unfamiliar objects in general, not only this project.

## 1. The Problem

LLMs are biased toward familiar computational grammars.

When they see a hard unfamiliar object, they tend to translate it into one of
these easier objects:

```text
state_t -> operator -> state_t+1
entropy gradient
Bayesian prediction
FEP / active inference analogy
QIT metric score
PEPS3D carrier label
path-integral metaphor
many-worlds metaphor
ordinary causal graph
```

Those can be useful tools or adapters. They are not the object.

The model to preserve is:

```text
possible futures have nominal/material-like reality as admissible spacetime
configurations;

the present is compatibility-weighted compression/selection from that field of
possible futures;

the past is the outward record of what survived;

entropy is distinguishability / possibility capacity;

gravity/binding is global possibility-sync / convergence;

Axis0 reads expansion-opening versus binding-convergence;

FEP is the local prediction/evidence/posterior expression of the same process.
```

The sim process must therefore stop asking:

```text
Can I run entropy, PEPS3D, QIT, FEP, and Axis0-like scores?
```

It must instead ask:

```text
Can I instantiate the retrocausal possibility-constraint object, then derive
entropy, PEPS3D, QIT, FEP, and Axis0-like readouts from it?
```

## 2. The One-Sentence Rule

The primary object is not a forward state.

The primary object is a finite field of admissible possible futures, with
compatibility witnesses, compressed into a present survivor state and an
outward record.

Short form:

```text
future possibility field -> compatibility compression -> present survivor ->
past record
```

Any sim that starts as ordinary forward evolution and then adds entropy, FEP,
PEPS3D, or Axis0 labels is probably siming a proxy.

## 3. Human-Facing Explanation

The shell and jk language are handles. The model underneath is the important
part.

Plain terms:

```text
shell:
  a finite representation of the spherical possibility surface around an event.
  A one-light-year shell is the one-year possibility surface in the owner's
  model. In code this becomes Sigma_r(x), a finite shell/stratum around event x
  at radius/order r.

jk fuzz:
  the many possible futures carried on that shell. In code this becomes the
  finite admissible continuation set F_r or Omega_r, not a vague metaphor.

compatibility:
  the degree or witness showing whether a possible future can survive the
  active boundary, probe, carrier, and constraint conditions.

survivor:
  the compressed present state produced from compatible futures.

outward record:
  the trace, hash, boundary residue, or preserved correlation left by what
  survived; the past-facing record.

Axis0:
  the signed opening-vs-binding readout after the field has been bridged into a
  cut/readout state. It is not the shell, not entropy alone, and not a primitive
  label.
```

At any point/event, there is not merely one deterministic future. There is a
structured field of possible future configurations. Those possible futures are
not abstract possibilities in another world. They are possible spacetime
configurations carried by spacetime's distinguishability structure.

The present is not just the next state caused by the past. The present is the
survivor/compression of many compatible futures. A future that is not compatible
with the boundary, probes, constraints, and global consistency of the field does
not survive into the present. A future that remains compatible contributes to
the compressed present state.

The past is the outward record of what survived. It is not the primitive driver
of the present. It is the record left after compatibility compression.

The same pattern appears at different levels:

```text
physics scale:
  possible futures compress into the present; preserved correlation appears as
  binding/gravity-like convergence; opening possibility appears as expansion.

cognitive/FEP scale:
  a predicted world is projected first, boundary evidence corrects it, and the
  survivor posterior is kept.

Holodeck/perception-memory scale:
  a world model projects possible scenes, evidence selects/corrects, survivor
  traces are kept, rejected traces become graveyard/anti-hashes.

sim scale:
  a finite possible-future ensemble is built, compatibility is computed, the
  present state is compressed, and the record is emitted.
```

So the sim must make the possible-future ensemble real in the code. It cannot be
only a paragraph in the result summary.

## 4. The Executable Object

Use a first-class runtime object. Do not let the sim own only a state vector.

Recommended name:

```text
RetrocausalPossibilityField
```

Minimum conceptual fields:

```text
carrier:
  finite PEPS3D/spinor/QIT carrier, when the sim is nonclassical

shells:
  finite shell or shell-stratum objects Sigma_r(x), not only identifiers

event_x:
  the finite event/patch center whose shells are being represented

shell_radius_r:
  the shell clock/order parameter

shell_area_or_measure:
  finite area/cardinality/measure data used for area scaling or inverse-square
  residual controls

shell_orientation:
  future_inward and past_outward orientation maps

future_continuations:
  admissible candidate futures / histories / refinements

compatibility_weights:
  weights showing how strongly each future remains compatible with the active
  constraints and boundary evidence

branch_states:
  density/readout for each candidate future

compression_map:
  map from many weighted futures into the present survivor state

outward_record_map:
  map from the survivor/compression structure into a record trace

readouts:
  entropy, binding, path evidence, QIT cuts, Axis0 candidate vector, etc.,
  all derived from the field, not primary

controls:
  mutations that remove shell/field/order/cut/chirality structure and must
  weaken or kill the claim
```

Mathematically:

```text
F_r = {f_i}                         finite possible futures/refinements
w_i = compatibility_weight(f_i)     normalized weights
rho_i = density/readout(f_i)         branch state/readout

rho_present = C({(w_i, rho_i)}_i)   compression into present
record_past = R({f_i survived}, rho_present)
```

The most important rule:

```text
rho_present must be computed from the future-continuation field, not from
present_{t-1}.
```

Forward evolution may be run as a control. It must not be the primary object.

## 5. Bad And Good Computation Order

Bad default:

```text
rho_t
-> apply operator
-> rho_t+1
-> compute entropy / QIT / FEP / Axis0 score
```

This is ordinary forward dynamics plus metrics.

Good object-native order:

```text
future_continuation_field F
-> compatibility weights w_i
-> compression operator C
-> rho_present
-> outward record R
-> derived entropy / QIT / FEP / Axis0 readouts
```

The order is not cosmetic. It is the model.

## 6. Concrete CS Data Structures

The first implementation should be simple, typed, and fail-closed.

Pseudo-Python:

```python
@dataclass
class ShellStratum:
    shell_id: str
    event_x: torch.Tensor          # finite event/patch anchor
    radius: torch.Tensor           # shell order/clock parameter r
    support_sites: torch.Tensor    # PEPS3D sites/cells in Sigma_r(x)
    boundary_sites: torch.Tensor
    area_measure: torch.Tensor     # finite area/cardinality-like measure
    future_inward_to: str | None   # Sigma_r -> Sigma_{r-1}
    past_outward_to: str | None    # Sigma_r -> Sigma_{r+1}


@dataclass
class PEPS3DCarrier:
    sites: torch.Tensor          # long, shape [n_sites, 3] or structured ids
    bonds: torch.Tensor          # long, shape [n_bonds, 2]
    faces: torch.Tensor          # long, face membership
    cells: torch.Tensor          # long, cell membership
    site_tensors: dict[str, torch.Tensor]
    chirality: torch.Tensor      # left/right or sheet labels when relevant
    anchor_step: str             # first admitted carrier step


@dataclass
class PossibilityBranch:
    branch_id: str
    shell_id: str
    history_ops: list[str]
    kraus_ops: list[torch.Tensor]
    rho_branch: torch.Tensor
    weight: torch.Tensor
    admissible: bool
    exclusion_reason: str | None


@dataclass
class RetrocausalPossibilityField:
    sim_id: str
    run_id: str
    primary_object: Literal["retrocausal_possibility_field"]
    carrier: PEPS3DCarrier | None
    event_x: torch.Tensor
    shells: list[ShellStratum]
    shell_radii: torch.Tensor
    shell_flow_map: dict[str, dict[str, str | None]]
    branches: list[PossibilityBranch]
    compatibility_logits: torch.Tensor
    compatibility_weights: torch.Tensor
    compression_map: Callable[[list[PossibilityBranch]], torch.Tensor]
    compression_provenance: list[str]
    rho_present: torch.Tensor
    outward_record: "OutwardRecord"
    controls: list["ControlCase"]
    readouts: "FieldReadouts"
    blocked_consumers: list[str]
```

Outward record:

```python
@dataclass
class OutwardRecord:
    record_id: str
    survivor_branch_ids: list[str]
    excluded_branch_ids: list[str]
    boundary_trace: torch.Tensor
    record_hash: str
    provenance: list[str]
```

Readouts:

```python
@dataclass
class FieldReadouts:
    h_future: float
    shell_boundary_entropy: float
    path_entropy: float
    mutual_information: float | None
    coherent_information: float | None
    log_z_path: float | None
    order_gap: float
    chirality_split: float | None
    no_message_capacity: float
    a0_raw: dict[str, float]
    phi0_candidates: dict[str, float]
```

Controls:

```python
@dataclass
class ControlCase:
    control_id: str
    mutation: str
    expected_effect: str
    observed_effect: str
    passed: bool
    quantitative_delta: float | None
```

## 7. Result JSON Schema

Every model-native result should contain a first-class field section.

Minimal shape:

```json
{
  "name": "retrocausal_possibility_field_seed_probe",
  "classification": "tool_lego_fit_probe",
  "sim_execution_kind": "nonclassical",
  "primary_object": "retrocausal_possibility_field",
  "claim_ceiling": "field_object_only",
  "promotion_allowed": false,

  "finite_map": {
    "domain": "finite future-continuation field plus constraints",
    "codomain_or_output": "rho_present, outward_record, readout vector",
    "map": "(F_r, weights, branch states, compression map) -> (rho_present, record, readouts)"
  },

  "field": {
    "event_x_present": true,
    "shell_count": 0,
    "shells_have_sigma_r_support": true,
    "shells_have_area_measure": true,
    "future_continuation_count": 0,
    "branch_weight_sum": 1.0,
    "compression_map": "weighted_density_compression",
    "compression_provenance_present": true,
    "outward_record_map": "survivor_intersection_trace",
    "has_future_inward_orientation": true,
    "has_past_outward_record": true
  },

  "carrier": {
    "peps3d_present": true,
    "torch_native": true,
    "spinor_or_spinor_density_present": true,
    "dense_closure_required": false
  },

  "readouts": {
    "h_future": 0.0,
    "path_entropy": 0.0,
    "log_z_path": 0.0,
    "mutual_information": 0.0,
    "coherent_information": 0.0,
    "order_gap": 0.0,
    "a0_raw": {}
  },

  "controls": {
    "single_future_control": {"passed": false, "delta": null},
    "scrambled_future_control": {"passed": false, "delta": null},
    "forward_shadow_control": {"passed": false, "delta": null},
    "commuting_history_control": {"passed": false, "delta": null},
    "scalar_entropy_only_control": {"passed": false, "delta": null},
    "message_channel_leak_control": {"passed": false, "delta": null}
  },

  "tool_manifest": {
    "pytorch": "torch-native density, branch weights, and compression",
    "z3": "finite admissibility/control witness for at least one branch exclusion"
  },
  "tool_integration_depth": {
    "pytorch": "load_bearing",
    "z3": "load_bearing"
  },
  "blocked_consumers": [
    "flux",
    "Xi closure",
    "Phi0 closure",
    "Axis0 closure",
    "physics claims",
    "final manifold claims"
  ],
  "all_pass": false
}
```

The exact classification depends on the repo stage. The key requirement is that
`primary_object` is not optional and is not merely a note.

## 8. Required Validators

These validators make the object hard for LLMs to translate away.

### 8.1 Schema Validator

Fail if:

```text
primary_object != retrocausal_possibility_field
event_x missing
shell Sigma_r support missing
shell area/measure missing when shell geometry is claimed
future_inward/past_outward orientation maps missing
field.future_continuation_count <= 1 for a non-degenerate claim
compression_map missing
compression provenance missing
outward_record_map missing
controls missing
blocked_consumers missing
```

### 8.2 Tensor Validator

Fail if:

```text
rho_present is not Hermitian
rho_present trace is not 1 within tolerance
rho_present has negative eigenvalues beyond tolerance
branch weights do not sum to 1
branch states contain NaN/Inf
claim-bearing path uses NumPy or .numpy()
```

### 8.3 Direction Validator

Fail if the sim cannot distinguish:

```text
future_continuations -> present compression
```

from:

```text
present_{t-1} -> forward evolution -> present_t
```

A forward-shadow control is mandatory.

### 8.4 Provenance Validator

Every readout must say where it came from:

```text
F -> weights -> compression -> rho_present -> readout
```

or:

```text
rho_present -> outward record -> record readout
```

If entropy, coherent information, FEP, or Axis0-like polarity has no provenance
back to the future-continuation field, it is a proxy-only metric.

### 8.5 Control Validator

Required controls:

```text
single_future_control:
  collapse many futures to one; many-futures claim must fail or weaken.

scrambled_future_control:
  preserve branch count but break compatibility; compatibility claim must fail
  or weaken.

forward_shadow_control:
  run ordinary forward dynamics; model-native readouts must not be identical
  across all sweeps.

no_shell_radius:
  remove or flatten radius/order r; shell-time claim must fail or weaken.

no_inward_outward_orientation:
  erase future-inward and past-outward flow maps; shell-polarity claim must
  fail or weaken.

area_erased:
  remove shell area/cardinality scaling; inverse-square or shell-measure claims
  must fail or weaken.

commuting_history_control:
  erase noncommutation/order sensitivity; N01/path claim must fail or weaken.

scalar_entropy_only_control:
  if scalar entropy alone explains the result, Axis0 is not load-bearing.

message_channel_leak_control:
  if controllable FTL messaging appears, fail the model.

dense_closure_control:
  if dense global state closure is required, block nonclassical manifold
  promotion.

FEP_without_kill_control:
  if FEP/Holodeck language excludes nothing, it is decorative.
```

### 8.6 Primary Object Linter

Fail or warn on these reductions in claim-bearing fields:

```text
Axis0 = entropy
Axis0 = i scalar
Axis0 = coherent information alone
flux = Axis0
PEPS3D = label only
FEP = imported metaphor
Holodeck = memory database
retrocausality = backward signal
present = one selected future
state_{n+1} = R(state_n) as the main model
```

The linter is not about banning words. It is about banning substitutions.

## 9. The First Sim Ladder

### Sim 1: Field Seed

Name:

```text
sim_retrocausal_possibility_field_seed_probe.py
```

Goal:

Build the minimum primary object.

Map:

```text
(finite branch set F, compatibility weights, branch densities, compression map)
-> (rho_present, outward_record, raw readouts)
```

Required:

```text
future_continuation_count >= 2
weights normalized
rho_present valid density
outward record emitted
single_future_control weakens/fails the many-futures claim
forward_shadow_control exists
```

No Axis0 closure claim.

### Sim 2: Noncommuting History Field

Name:

```text
sim_retrocausal_kraus_history_field_probe.py
```

Goal:

Represent the future-continuation field as noncommuting finite histories.

Map:

```text
{K_h histories, rho_base, evidence/boundary E}
-> branch weights, Z_path, posterior rho_present, order_gap
```

Required:

```text
commuting_history_control collapses order gap
log_z_path and coherent_information measured separately
FEP not allowed to be a decorative label
```

### Sim 3: PEPS3D Spinor Carrier

Name:

```text
sim_retrocausal_peps3d_spinor_field_carrier_probe.py
```

Goal:

Put the primary object on a PEPS3D spinor-network carrier.

Required:

```text
8/16/32/64 site stress plan
site/bond/face/cell anchors
spinor or spinor-derived density
chirality/sheet metadata when relevant
no dense closure
no scalar PEPS3D label
```

### Sim 4: Xi Bridge

Name:

```text
sim_xi_retrocausal_field_to_rho_ab_bridge_probe.py
```

Goal:

Build the bridge from the primary field into a QIT cut state.

Map:

```text
RetrocausalPossibilityField
-> rho_AB plus shell/history/chirality metadata
```

Required:

```text
rho_AB valid
cut bookkeeping explicit
product/no-entanglement control weakens QIT binding claim
no_boundary_bookkeeping control weakens shell-cut claim
```

### Sim 5: Phi0 Candidate Bakeoff

Name:

```text
sim_phi0_retrocausal_field_polarity_bakeoff_probe.py
```

Goal:

Test candidate projections from `A0_raw` to signed polarity.

Do not start with one scalar.

Preserve:

```text
A0_raw = {
  delta_future_possibility_entropy,
  delta_boundary_entropy,
  delta_binding_correlation,
  log_z_path,
  order_gap,
  chirality_split,
  no_message_capacity
}
```

Then test projections:

```text
coherent_information projection
log_z_path + coherent_information projection
shell_weighted_cut projection
opening_minus_binding projection
```

Pass only if controls separate model-native polarity from scalar proxies.

### Sim 6: Holodeck/FEP Loop

Name:

```text
sim_holodeck_retrocausal_prediction_record_probe.py
```

Goal:

Represent prediction-first perception/memory as the local expression of the
same primary object.

Map:

```text
future model projections + evidence
-> posterior survivor
-> survivor hash and graveyard/anti-hash
```

Required:

```text
hash_without_model fails
FEP_without_kill fails
graveyard/rejected possibilities preserved
```

## 10. How To Use Existing Sims

Do not throw old sims away.

Reclassify them by relation to the primary object:

```text
model-native:
  builds or consumes RetrocausalPossibilityField directly.

model-component:
  tests a useful carrier, readout, operator, proof surface, or control that can
  be used inside the field.

descriptor-only:
  uses nearby language or metrics but does not instantiate the field.
```

Examples:

```text
entropy readout:
  component unless it is derived from future-continuation compression.

PEPS3D anchor:
  component unless it carries the future field and cut metadata.

QIT-FEP:
  component unless path evidence/posterior is tied to compatibility compression.

Axis0 score:
  descriptor-only unless it reads opening-vs-binding polarity from A0_raw over
  the bridged field.
```

The old sim result may remain useful. Its claim ceiling changes.

## 11. Wizard v4.2 Modification

Wizard must not merely run more models. More models can create stronger shared
normalization pressure.

Wizard needs a primary-object preservation gate.

### 11.1 Primary Object Card

Every council parent must fill this before giving advice:

```yaml
primary_object:
native_terms:
human_explanation:
domain:
codomain_or_output:
allowed_operations:
required_invariants:
forbidden_substitutions:
allowed_adapters:
negative_controls:
artifact_or_receipt_surface:
blocked_consumers:
```

If the card is empty, generic, or proxy-based, the route is partial/blocked.

### 11.2 Decision Council Change

Decision Council asks:

```text
What move acts on the primary object directly?
What move only improves a proxy?
What object field would this move clarify?
```

Decision routes:

```text
decision.context_strategy:
  Extract the primary object and the substitutions that would destroy it.

decision.move_selection:
  Choose the smallest action that changes evidence about the primary object.

decision.evidence_boundary:
  Separate object-native evidence from proxy evidence.
```

### 11.3 Failure Council Change

Failure Council assumes the answer failed because the object was translated into
a familiar framework.

Failure routes:

```text
failure.premortem:
  Six months later, the work produced proxy slop again. How?

failure.falsifier:
  Remove the primary object. If the answer still works, it was proxy-only.

failure.loophole_auditor:
  Search for synonym smuggling, label promotion, and adapter promotion.
```

### 11.4 Follow-Up Council Change

Follow-Up Council may not offer generic options such as "audit more" or "run
Axis0 next."

Each option must specify:

```text
which primary-object field it improves;
which proxy failure it blocks;
which artifact or sim it will produce;
which control would kill it.
```

Follow-up routes:

```text
follow_up.next_move_selector:
  Pick the next primary-object field to earn.

follow_up.lane_builder:
  Build direct-object, source-lift, proxy-falsifier, and adapter-quarantine
  lanes.

follow_up.compile_gate:
  Refuse synthesis if the final output does not preserve the object card.
```

### 11.5 Compile Gate

Compiled Wizard output needs these fields:

```yaml
target:
  primary_object:
  not_proxy:

action:
  acts_on_native_object_by:
  proxy_use_if_any:

success_check:
  primary_object_pass_signal:
  proxy_only_fail_signal:

stop_condition:
  stop_if_primary_object_fields_missing:
  stop_if_proxy_substitution_detected:

artifact_surface:
  source_or_receipt_path:
  evidence_class:

status:
  accepted | partial | blocked | killed | deferred
  reason:
  blocked_consumers:
```

### 11.6 v4.2 Integration Contract

This is not only a wording change. It changes v4.2 receipt requirements.

```text
Parent receipt:
  must include a completed Primary Object Card.

Child receipt:
  must state which primary-object field it touched or audited.

Management.run_controller:
  checks that the selected route acts on the primary object, not only a proxy.

Management.child_health:
  checks that child receipts did not collapse the object into forward dynamics,
  scalar entropy, label-only PEPS3D, or decorative FEP language.

Management.route_truth:
  marks the run partial/blocked if object cards are missing, if child receipts
  are missing, or if a model family returned only proxy summaries.

Output compiler:
  may synthesize only after object-native evidence, proxy boundary, success
  check, and stop condition are all present.
```

If a run has many child outputs but no complete Primary Object Cards, it is not
a successful Wizard run. It is plurality without object preservation.

## 12. MMM / Salience Design

MMM material should bias attention toward the object's causal structure, not
just its vocabulary.

A good MMM front-loads:

```text
the primary object;
the computation order;
the forbidden substitutions;
the controls that distinguish object success from proxy success;
the route's exact obligation.
```

For this model, the first paragraph of every sim/council prompt should say:

```text
Do not implement forward dynamics plus metrics. The primary object is the
finite admissible future-continuation field. The present is computed by
compatibility-weighted compression over that field. Metrics such as entropy,
FEP, PEPS3D, QIT, and Axis0 are derived views unless they can show provenance
back to that field. If the result survives single-future collapse,
future-field scrambling, or forward-shadow replacement, it is proxy-only.
```

That is stronger than telling the LLM to "remember jk fuzz." It makes the task
hard to complete without the object.

## 13. Premortem Findings

Frame:

It is six months from now. This process failed. The system is again producing
proxy entropy, proxy PEPS3D, and proxy Axis0.

Likely failures:

### 13.1 Preservation Doc Becomes Proof

Failure:

The source/model document is cited as if it admitted a formal sim.

Early warning:

Summaries cite the doc rather than result paths.

Repair:

No Axis0/FEP/physics/manifold claim from a doc alone. Require a same-session
result path and finite-map record.

### 13.2 Possibility Field Becomes Story Language

Failure:

Specs say "possibility field" but omit the finite future-continuation set,
weights, compression, and record.

Early warning:

No branch list. No compatibility weights. No compression map.

Repair:

Validator requires the runtime object fields.

### 13.3 Axis0 Collapses To Scalar

Failure:

One entropy, coherent-information, logZ, or sign score is reported as Axis0.

Early warning:

No `A0_raw`, no control killing scalar-only interpretation.

Repair:

Preserve `A0_raw`; treat `Phi0` as a discovered projection.

### 13.4 Xi/Phi0 Bridge Is Skipped

Failure:

Axis0 is read directly from a terrain table, engine stage, flux sign, or isolated
spinor.

Early warning:

No `rho_AB`; no `Xi_shell` or `Xi_hist`.

Repair:

No Axis0 statement without explicit bridge.

### 13.5 PEPS3D Becomes Branding

Failure:

PEPS3D appears as a label while the claim-bearing computation is dense,
Cartesian, or generic-tensor.

Early warning:

No site/bond/face/cell anchors; no chirality; dense closure required.

Repair:

PEPS3D is carrier discipline from the start, not a label.

### 13.6 Retrocausality Becomes Backward Signaling

Failure:

Agents treat the model as a future event sending a signal backward.

Early warning:

No no-message-capacity control; one-future collapse still passes.

Repair:

Message-channel leak fails the model. Single-future collapse kills the many-
futures claim.

### 13.7 FEP/Holodeck Becomes Decorative

Failure:

Every result is redescribed as prediction-first; nothing is excluded.

Early warning:

No graveyard hashes, no rejected futures, no separate `logZ_path` and `I_c`.

Repair:

FEP/Holodeck terms must kill or weaken at least one candidate.

## 14. Model Council Synthesis

This document was shaped by multiple advisory routes. This section is a route
truth note, not formal evidence. The Codex subagent ids and external receipt
paths are recorded here only so future readers do not confuse author synthesis
with anonymous consensus.

```text
Codex model-fidelity lane:
  agent 019e6762-42ea-7102-b18c-960009e0e772.
  Preserve shell-cut many-futures packet; forbid Axis0 scalar collapse.

Codex CS-architecture lane:
  agent 019e6762-4366-73f1-b59e-1b6faa5060a1.
  Add RetrocausalPossibilityField, PEPS3DCarrier, PossibilityBranch, controls,
  result JSON schema, and validators.

Codex premortem lane:
  agent 019e6762-43db-71d2-a763-e56c5b12f957.
  Main failure is narrative substitution for gate obedience.

Codex Wizard lane:
  agent 019e6762-4454-72f0-a42f-21f8534047ee.
  Add Primary Object Card and object-preservation compile gate.

Claude Opus advisory:
  receipt:
  /tmp/codex_claude_bridge/20260527T030254Z-design-audit-task-for-joshua-eisenhart-s-codex-r-e51970b58c17.receipt.json
  Make the future-configuration bundle plus admissibility witness the only
  primary object on disk; every metric must have provenance.

Grok advisory:
  response:
  /tmp/retrocausal_object_council/grok_response.json
  Useful pressure: typed constraint graph and survival trace.
  Rejected pressure: argmax-only present selection, banning PEPS/QIT/FEP/KL, and
  token-ban validation. Those contradict the project need for QIT/PEPS3D and
  would replace object fidelity with vocabulary policing.

Gemini advisory:
  response:
  /tmp/retrocausal_object_council/gemini.json
  Degraded. CLI returned invalid/empty response after tool activity. Do not
  count as content-bearing council evidence.

Wizard v4.2:
  partial/blocked run root:
  /tmp/retrocausal_object_council/wizard_v4_2/wizard-medium-20260527T030326Z
  Attempted as a medium loop. Route truth must be read from the run artifact if
  used; this doc does not claim a FULL Wizard run.
```

The important convergence is not agreement on wording. It is agreement that the
data structure and validators must force object preservation.

## 15. Generalization Beyond Codex Ratchet

The general method:

```text
1. Identify the unfamiliar primary object.
2. Name familiar proxies the LLM will translate it into.
3. Build a runtime/data object that makes the primary object first-class.
4. Make all metrics derived views with provenance.
5. Add controls that distinguish object success from proxy success.
6. Force every council worker to fill a Primary Object Card.
7. Refuse synthesis when workers agree only on the proxy.
```

Examples:

```text
Law:
  Do not translate a statute into "fairness" unless statutory elements survive.

Medicine:
  Do not translate a patient-specific mechanism into a generic diagnosis unless
  the differential constraints survive.

Product:
  Do not translate a user workflow into funnel metrics unless the user job
  survives.

Mathematics:
  Do not translate a new object into a standard dynamics/probability/category
  proxy unless the preserving map/invariant is explicit.

Research systems:
  Do not let consensus among models count unless the models agree on the
  primary-object card, not only on the proxy summary.
```

## 16. Formal Sim Prompt

Use this prompt when restarting formal sims:

```text
Goal: stop siming proxies and build the primary object.

Read AGENTS.md, CODEX.md, system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md,
system_v5/docs/LLM_CONTROLLER_CONTRACT.md, system_v5/docs/LEGO_SIM_CONTRACT.md,
system_v5/docs/JOSHUA_EISENHART_AXIS0_PHYSICS_MODEL_CORE_20260526.md, and
system_v5/docs/RETROCAUSAL_POSSIBILITY_FIELD_SIM_AND_WIZARD_METHOD_20260526.md.

Task:
Implement the first bounded formal scout for
RetrocausalPossibilityField, the finite admissible future-continuation field.

Do not implement ordinary forward dynamics plus metrics.

The primary finite map is:

  (finite future-continuation set F_r, compatibility weights, branch states,
   compression map C, outward record map R)
  ->
  (rho_present, outward_record, readouts, controls)

Required:
- primary_object = retrocausal_possibility_field
- future_continuation_count >= 2 in the positive case
- compatibility weights normalized
- rho_present valid torch-native density state
- branch provenance from futures to rho_present
- outward record emitted
- forward-shadow control
- single-future control
- scrambled-future control
- commuting-history control if path operators are used
- scalar-entropy-only control
- message-channel-leak control
- dense-closure block
- blocked consumers: flux, Xi closure, Phi0 closure, Axis0 closure, physics,
  final manifold

Use PEPS3D/spinor carrier if the claim is nonclassical. If PEPS3D cannot be
made real in the first scout, classify the result as a lower carrier/bootstrap
probe and block nonclassical manifold consumers.

Run Wizard v4.2 with Primary Object Card discipline:
- Decision Council: choose the smallest move that acts on the primary object.
- Failure Council: try to show the result is only forward dynamics or scalar
  entropy.
- Follow-Up Council: produce the next object-field repair, not a generic
  follow-up.

Success:
The result JSON records a bounded runtime instantiation of the object and
supports only the status actually checked: `exists`, `runs`, `passes local
rerun`, or `canonical by process`. It does not prove Axis0/FEP/flux/manifold
closure. The controls must distinguish it from proxy dynamics before stronger
consumers can cite it.

Stop/block:
If the result can pass without future-continuation field, compatibility
weights, compression provenance, or controls, stop and write a blocked-reason
artifact. Do not claim Axis0/FEP/flux/manifold progress.
```

## 17. What This Document Is Not

This document is not:

```text
formal-sim evidence;
Axis0 closure;
Xi/Phi0 closure;
flux admission;
physics proof;
PEPS3D closure;
permission to skip lower legos;
permission to cite the model doc as a receipt;
permission to use Wizard orchestration instead of executable sims.
```

It is a method for making the right object executable and making LLM councils
protect that object instead of smoothing it into familiar proxies.
