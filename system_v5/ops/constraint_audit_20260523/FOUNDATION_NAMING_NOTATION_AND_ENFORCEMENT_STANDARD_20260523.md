# Foundation Naming, Notation, And Enforcement Standard

Date: 2026-05-23

Status: naming/process standard proposal. Human-facing and LLM-facing. Not a
formal admission claim.

## 1. The Problem

The word `axiom` is doing too much work.

It has been used for at least five different things:

1. the owner's deep generative concepts;
2. the two executable root constraints;
3. derived anti-smuggling constraints;
4. process rules for bounded work;
5. sim gates or receipts that make a rule enforceable.

Those are not the same.

Saying:

```text
no primitive equality
```

is not the same as:

```text
we can enforce no primitive equality in a sim
```

And neither is the same as:

```text
this candidate survived a no-primitive-equality gate
```

The naming system must make those differences impossible to miss.

## 2. Core Rule

Do not use `axiom` as an operational status label.

Use `axiom` only in human prose when referring to the owner's deep thesis
language or to external mathematical systems.

Inside the ratchet, use role-specific names:

```text
TH   thesis
RC   root constraint
DC   derived constraint
CF   candidate fence
PL   process law
EG   enforcement gate
SIM  runnable sim/probe
REC  receipt/evidence artifact
OBJ  bounded object
REL  relation/bridge
GR   graveyard row for killed or demoted candidates
MC   machine-safe code for M(C), the admissible constraint manifold
```

## 3. The Naming Stack

### TH: Thesis

Meaning:

An owner/generative concept. It can be deep, true-to-intent, and important, but
it is not yet operationally enforceable.

Format:

```text
TH-<NN>-<slug>
```

Examples:

```text
TH-01-pure-randomness
TH-02-entropy-bridge
TH-03-retrocausal-convergence
TH-04-entropic-monism
TH-05-nominalist-identity
TH-06-emergence-by-survival
TH-07-spinor-qit-first-survivor
TH-08-feedback-loop-life-mind
```

Allowed claim:

```text
This is an owner thesis to translate.
```

Forbidden claim:

```text
This is enforced because it was named.
```

### RC: Root Constraint

Meaning:

A minimal operational constraint that the formal ratchet treats as root.

Keep the existing canonical codes:

```text
F01 = finitude
N01 = noncommutation
```

Optional expanded labels:

```text
RC-F01-finitude
RC-N01-noncommutation
```

Allowed claim:

```text
This root constrains every admissible formal object.
```

Forbidden claim:

```text
The root directly proves every downstream structure.
```

### DC: Derived Constraint

Meaning:

An enforceable anti-smuggling fence derived from one or both root constraints.

Use `DC` as the clean new role name even when old docs use `EA`, `EC`, `BC`, or
charter rows.

Format:

```text
DC-<NN>-<slug>
```

Examples:

```text
DC-01-no-primitive-identity
DC-02-no-primitive-equality
DC-03-boundary-contrast-identity
DC-04-no-primitive-time-causality
DC-05-no-primitive-metric-coordinate-geometry
DC-06-no-closure-by-default
DC-07-finite-witness-discipline
DC-08-no-cloning-broadcasting
DC-09-no-primitive-probability
DC-10-no-primitive-optimization-utility
DC-11-no-outside-observer
DC-12-no-global-total-order
DC-13-no-semantic-smuggling
```

Candidate additions:

```text
CF-14-no-primitive-continuity-smoothness
CF-15-no-primitive-tensor-factorization-independence
CF-16-no-primitive-classical-markov-chain
CF-17-no-primitive-classical-markov-blanket
CF-18-no-primitive-commutative-aggregation
CF-19-no-primitive-scalarization
CF-20-no-primitive-basis-gauge
CF-21-no-primitive-measurement-probe-apparatus
CF-22-no-primitive-simultaneity
CF-23-no-primitive-global-state-context
CF-24-no-primitive-convergence-limit
CF-25-no-free-reversibility
```

Allowed claim:

```text
This is a proposed derived constraint with root pressure and a gate path.
```

Forbidden claim:

```text
This is true because it sounds like F01/N01.
```

### CF: Candidate Fence

Meaning:

A suspected derived constraint that is not yet accepted as a `DC`.

Use this for implications that seem right but need a non-redundancy check and
a finite enforcement gate.

Format:

```text
CF-<NN>-<slug>
```

Examples:

```text
CF-14-no-primitive-continuity-smoothness
CF-15-no-primitive-tensor-factorization-independence
CF-16-no-primitive-classical-markov-chain
CF-17-no-primitive-classical-markov-blanket
CF-18-no-primitive-commutative-aggregation
CF-19-no-primitive-scalarization
CF-20-no-primitive-basis-gauge
CF-21-no-primitive-measurement-probe-apparatus
CF-22-no-primitive-simultaneity
CF-23-no-primitive-global-state-context
CF-24-no-primitive-convergence-limit
CF-25-no-free-reversibility
```

Allowed claim:

```text
This is a candidate fence; do not treat it as a numbered derived constraint yet.
```

Forbidden claim:

```text
This gets a number because it is philosophically appealing.
```

### PL: Process Law

Meaning:

A rule about how the work must be performed so the constraints are not violated
by the method.

Format:

```text
PL-<NN>-<slug>
```

Examples:

```text
PL-01-bounded-work
PL-02-ordered-receipts
PL-03-one-variable-of-uncertainty
PL-04-matched-controls
PL-05-graveyard-record
PL-06-no-bulk-stage-widening
PL-07-maintenance-closure
PL-08-clean-lane-before-formal-claim
```

Allowed claim:

```text
This law keeps the research method aligned with the constraints.
```

Forbidden claim:

```text
This process law is itself an ontology claim.
```

### EG: Enforcement Gate

Meaning:

A specific finite test that makes a `RC`, `DC`, `CF`, or `PL` operational.

Format:

```text
EG-<constraint-code>-<slug>
```

Examples:

```text
EG-F01-finite-carrier-path-witness
EG-N01-order-gap-commuting-collapse
EG-DC02-probe-relative-equality
EG-DC09-probe-indexed-probability
EG-CF-tensor-factorization-product-entangled-control
```

Every enforcement gate must name:

```text
positive case
negative/graveyard case
boundary case
observable
pass threshold
fail threshold
claim ceiling
```

### SIM: Runnable Sim Or Probe

Meaning:

Executable code that implements one or more enforcement gates.

Format:

```text
SIM-<gate-or-object>-<slug>
```

In files, keep repo naming:

```text
sim_<slug>.py
```

But in prose, link it to the gate:

```text
SIM implements EG-DC09-probe-indexed-probability
```

### REC: Receipt

Meaning:

Machine-readable evidence from running a sim/probe/check.

Format:

```text
REC-<sim-slug>-<date-or-result-path>
```

Allowed claim:

```text
This receipt shows the gate passed/failed under its claim ceiling.
```

Forbidden claim:

```text
This receipt proves the theory.
```

### MC: Constraint Manifold Projection

Meaning:

The current `M(C)` survivor surface: bounded objects and relations that have
passed active constraints and gates under explicit claim ceilings.

Use `MC` as the machine-safe role code and `M(C)` as the display notation.

Allowed claim:

```text
This is the current survivor surface under active gates.
```

Forbidden claim:

```text
This is a primitive manifold or final ontology.
```

Systems reading:

```text
M(C) is the ratchet attractor basin created by repeated finite,
noncommuting constraint pressure.
```

### OBJ: Bounded Object

Meaning:

The specific thing being moved through the ratchet.

Examples:

```text
OBJ-density-carrier
OBJ-hopf-fiber-loop
OBJ-weyl-sheet-pair
OBJ-cptp-channel-family
OBJ-xi-bridge-map
OBJ-axis0-readout-candidate
```

### REL: Relation / Bridge

Meaning:

A mapping or relation between objects or layers.

Examples:

```text
REL-geometry-to-rhoAB
REL-engine-path-to-cut-state
REL-thesis-to-finite-fixture
REL-clean-rebuild-to-current-registry
```

Bridges are high-risk. Every `REL` should carry a semantic-smuggling warning
until gated.

## 4. The Status Ladder

Every named item needs a status. Names alone do not admit anything.

Use these statuses:

| Status | Meaning |
|---|---|
| `stated` | exists in owner or repo prose |
| `translated` | has CS/QIT/process forms |
| `gated` | has an enforcement-gate design |
| `implemented` | has a runnable sim/check |
| `receipted` | has a result artifact |
| `passed_under_ceiling` | passed within explicit claim ceiling |
| `failed` | gate failed |
| `killed` | strong falsifier fired |
| `demoted` | still useful but lower-status than claimed |
| `blocked` | cannot advance until named dependency |
| `candidate` | plausible but not accepted |
| `accepted_constraint` | accepted as a constraint role in the current standard and linked to at least one gate |

Forbidden status:

```text
axiomatically true
```

That phrase hides too much.

## 5. Conversion Pipeline

The clean pipeline is:

```text
TH -> RC/DC/CF/PL -> EG -> SIM -> REC -> state update
```

Expanded:

```text
owner thesis
  -> finite translation
  -> root pressure
  -> primitive ban
  -> CS form
  -> QIT/math form
  -> process form
  -> enforcement gate
  -> runnable sim/probe
  -> receipt
  -> survivor/graveyard/update
```

Example:

```text
TH-01-pure-randomness
  -> finite high-entropy rho_N
  -> F01 root pressure
  -> no completed infinity
  -> CS: finite bounded state representation
  -> QIT: rho in D(H), dim(H)<infinity
  -> EG-F01-finite-carrier-path-witness
  -> sim finite carrier gate
  -> receipt
```

Example:

```text
TH-05-nominalist-identity
  -> identity through a ~ b
  -> DC-02-no-primitive-equality
  -> CS: contract/probe equivalence, not bare substitution
  -> QIT: finite probe-vector indistinguishability
  -> EG-DC02-probe-relative-equality
  -> receipt
```

Example:

```text
TH-07-spinor-qit-first-survivor
  -> finite spinor carrier candidate
  -> F01+N01 root pressure
  -> no primitive carrier assumption
  -> OBJ-spinor-carrier
  -> EG-carrier-admission-spinor-controls
  -> receipt
```

## 6. Count Discipline

The system should not optimize for a large number of named constraints.

There are three failure modes:

1. **Undercount**: missing a real implication, so classical assumptions leak
   back in.
2. **Overcount**: giving a new number to a duplicate, making the system look
   larger but less clear.
3. **Mixed count**: counting process laws, candidate fences, and receipts as if
   they were the same kind of thing.

The registry should count separately:

```text
TH count: owner theses
RC count: root constraints
DC count: accepted derived constraints
CF count: candidate fences
PL count: process laws
EG count: enforcement gates
SIM count: runnable implementations
REC count: receipts
OBJ count: bounded objects
REL count: relations/bridges
GR count: killed/demoted candidate rows
MC count: machine-safe manifold code
```

This means a statement can be important without being a `DC`.

## 7. Current Proposed Naming Map

### Thesis Layer

| New code | Old wording | Status |
|---|---|---|
| TH-01 | pure randomness / max entropy fuzz | owner thesis |
| TH-02 | entropy as universal bridge | owner thesis |
| TH-03 | no primitive past-causation / retrocausal convergence | owner thesis |
| TH-04 | entropic monism | owner thesis |
| TH-05 | nominalist identity, `a=a` through `a~b` | owner thesis |
| TH-06 | emergence by survival | owner thesis |
| TH-07 | spinor/QIT first survivor hypothesis | owner thesis |
| TH-08 | feedback-loop life/mind/oracle structure | owner thesis |

### Root Constraint Layer

| New code | Existing code | Status |
|---|---|---|
| RC-F01 | F01 / RC-1 | root constraint |
| RC-N01 | N01 / RC-2 | root constraint |

### Derived Constraint Layer

| New code | Existing aliases | Status |
|---|---|---|
| DC-01-no-primitive-identity | EA01, BC04 | accepted |
| DC-02-no-primitive-equality | EA02, EC07, BC05 | accepted |
| DC-03-boundary-contrast-identity | EA03 | accepted |
| DC-04-no-primitive-time-causality | EA04, EC11 | accepted |
| DC-05-no-primitive-metric-coordinate-geometry | EA05, EC15, BC10 | accepted |
| DC-06-no-closure-by-default | EA06, EC12, BC07 | accepted |
| DC-07-finite-witness-discipline | EA07 | accepted |
| DC-08-no-cloning-broadcasting | EC08 | accepted |
| DC-09-no-primitive-probability | EC09, BC09 | accepted |
| DC-10-no-primitive-optimization-utility | EC10, BC11 | accepted |
| DC-11-no-outside-observer | EC13 | accepted |
| DC-12-no-global-total-order | EC14, BC06 | accepted |
| DC-13-no-semantic-smuggling | EC16, BC12 | accepted |

### Candidate Fence Layer

These are not accepted derived constraints yet. They are root-pressured
anti-smuggling fences that need non-redundancy checks and runnable gates before
promotion.

| New code | Root pressure | Required gate scaffold |
|---|---|---|
| CF-14-no-primitive-continuity-smoothness | F01 | EG-CF14-finite-discrete-vs-continuum-smuggling |
| CF-15-no-primitive-tensor-factorization-independence | F01+N01 | EG-CF15-product-entangled-matched-cut |
| CF-16-no-primitive-classical-markov-chain | F01+N01 | EG-CF16-cptp-instrument-vs-classical-markov-chain |
| CF-17-no-primitive-classical-markov-blanket | F01+N01 | EG-CF17-cut-instrument-vs-classical-markov-blanket |
| CF-18-no-primitive-commutative-aggregation | N01 | EG-CF18-path-resolved-vs-order-erasing-average |
| CF-19-no-primitive-scalarization | F01+N01 | EG-CF19-vector-tensor-vs-scalar-loss |
| CF-20-no-primitive-basis-gauge | F01+N01 | EG-CF20-basis-scramble-gauge-invariance |
| CF-21-no-primitive-measurement-probe-apparatus | F01+N01 | EG-CF21-declared-instrument-vs-primitive-probe |
| CF-22-no-primitive-simultaneity | F01+N01 | EG-CF22-order-race-vs-primitive-simultaneity |
| CF-23-no-primitive-global-state-context | F01+N01 | EG-CF23-scoped-view-vs-global-oracle |
| CF-24-no-primitive-convergence-limit | F01+N01 | EG-CF24-finite-epsilon-step-vs-limit-smuggling |
| CF-25-no-free-reversibility | F01+N01 | EG-CF25-irreversible-channel-vs-free-inverse |

Current receipt note:

```text
CF-14 through CF-25 have candidate-gate receipts:
system_v5/ops/constraint_audit_20260523/results/cf14_finite_discrete_vs_continuum_smuggling_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf15_product_entangled_matched_cut_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf16_cptp_instrument_vs_classical_markov_chain_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf17_cut_instrument_vs_classical_markov_blanket_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf18_path_resolved_vs_order_erasing_average_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf19_vector_tensor_vs_scalar_loss_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf20_basis_scramble_gauge_invariance_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf21_declared_instrument_vs_primitive_probe_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf22_order_race_vs_primitive_simultaneity_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf23_scoped_view_vs_global_oracle_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf24_finite_epsilon_step_vs_limit_smuggling_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf25_irreversible_channel_vs_free_inverse_gate_results.json
system_v5/ops/constraint_audit_20260523/results/candidate_fence_nonredundancy_audit_results.json
```

Those receipts implement gate scaffolds and a non-redundancy ceiling audit for
CF-14 through CF-25, but they do not promote any of those candidates
into the accepted derived constraint layer.

The non-redundancy audit is two-part: token overlap is a conservative proxy,
and structural fixture signatures separately reject exact duplicate gate
shapes. A nonempty `structural_duplicate_pairs` list blocks the ceiling audit.
It is still not a formal independence proof.

### Process Law Layer

| New code | Rule |
|---|---|
| PL-01-bounded-work | every work unit has finite scope, input, output, verification |
| PL-02-ordered-receipts | order of evidence is part of evidence |
| PL-03-one-variable-of-uncertainty | one packet tests one uncertainty |
| PL-04-matched-controls | controls must preserve nuisance variables |
| PL-05-graveyard-record | failures are recorded as map data |
| PL-06-no-bulk-stage-widening | widen one axis after receipt |
| PL-07-maintenance-closure | evidence changes must update stale surfaces |
| PL-08-clean-lane-before-formal-claim | contaminated evidence requires clean rebuild |
| PL-09-no-role-confusion | thesis, constraint, gate, sim, receipt, object, relation, and manifold roles must not collapse |
| PL-10-manifold-recompute-on-constraint-change | DC demotion, CF promotion, or accepted constraint change requires M(C) recomputation or archived stale-state marking |

### Graveyard Layer

`GR` rows are allowed to be empty. They exist so killed or demoted candidates do
not stay live in `CF` or `DC` after a falsifying receipt.

## 8. LLM-Facing Rule Set

LLMs need hard wording because they blur status levels.

The machine-readable companion is:

```text
system_v5/ops/constraint_audit_20260523/foundation_operational_process_spec_20260523.json
```

Use this rule set in prompts and docs:

1. Do not call a `TH` enforceable.
2. Do not call a `CF` accepted.
3. Do not call a `PL` ontology.
4. Do not call an `EG` evidence.
5. Do not call a `SIM` successful until it has a `REC`.
6. Do not call a `REC` proof beyond its claim ceiling.
7. Do not count aliases as new constraints.
8. Do not use `axiom` as a status.
9. Always name the forbidden primitive.
10. Always name the CS form and QIT/math form before sim work.

Short LLM prompt:

```text
For every statement, label it as TH, RC, DC, CF, PL, EG, SIM, REC, OBJ, REL, or MC.
If you cannot label it, do not operationalize it.
If it is TH, translate it before enforcing it.
If it is CF, do not count it as accepted.
If it has no EG, it is not enforceable.
If it has no REC, it is not evidence.
```

## 9. Human-Facing Translation

Plainly:

```text
An axiom-like idea is not yet a constraint.
A constraint is not yet a gate.
A gate is not yet evidence.
Evidence is not yet final truth.
```

The correct chain is:

```text
idea -> translated constraint -> enforceable gate -> run -> receipt -> status
```

This is the central correction.

## 10. Operational Checklist

Before any new sim, doc, or registry update, answer:

```text
1. What is the item code? TH, RC, DC, CF, PL, EG, SIM, REC, OBJ, or REL?
2. If it is a thesis, what is its finite translation?
3. If it is a constraint, what primitive does it forbid?
4. If it is derived, what root pressure derives it?
5. What is the CS form?
6. What is the QIT/math form?
7. What is the process consequence?
8. What finite gate enforces it?
9. What receipt proves the gate ran?
10. What is the claim ceiling?
```

If those cannot be answered, the item is not ready for formal work.

## 11. Recommended Immediate Changes

1. Stop titling new docs `axioms` unless they are explicitly owner-thesis docs.
2. Rename the current human-facing packet in future revisions to:

```text
FOUNDATIONS_THESIS_CONSTRAINT_PROCESS_EXPLAINER
```

3. Keep old aliases in mapping tables, but use `TH/RC/DC/CF/PL/EG/SIM/REC`
   in new work.
4. Build a machine-readable registry with these fields:

```yaml
code:
role: TH | RC | DC | CF | PL | EG | SIM | REC | OBJ | REL | MC
name:
aliases:
statement:
root_pressure:
forbidden_primitive:
cs_form:
qit_math_form:
process_form:
gate:
sim:
receipt:
status:
claim_ceiling:
```

5. Make the next executable audit check for role confusion:

```text
flag any doc that calls a TH enforced,
calls a CF accepted,
or cites a SIM without a REC.
```
