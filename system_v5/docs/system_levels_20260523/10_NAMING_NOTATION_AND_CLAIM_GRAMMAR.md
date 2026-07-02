# Naming, Notation, And Claim Grammar

Status: working naming system. Not canon by itself.

This document exists because the project has outgrown loose words like
"axiom", "constraint", "engine", "axis", "flux", and "proof". Those words are
useful in conversation, but they become dangerous when an LLM treats them as
already-operational objects.

The goal is not to make the language colder. The goal is to let the human
vision survive contact with code, sims, proofs, and other LLMs without being
flattened into metaphor.

## 1. The Problem

The project has at least six kinds of statements:

1. owner-origin generative ideas;
2. root pressures;
3. derived constraints;
4. operational enforcement rules;
5. executable sims or proof checks;
6. admitted receipts.

Calling all of them "axioms" makes the stack unreadable.

Example:

```text
"Reality begins as maximum-entropy fuzz."
```

That is not an axiom in the same operational sense as:

```text
Every nonclassical formal scout must use finite-dimensional carriers.
```

The first is a thesis pressure. The second can be enforced by code review,
schema checks, and sim construction.

The naming system therefore separates:

```text
thesis pressure
root constraint
derived constraint
candidate fence
operational extension
sim/proof gate
receipt
status label
```

## 2. Core Naming Rule

Every named object should answer five questions:

```text
1. What level is it?
2. What does it forbid?
3. What does it permit?
4. What would enforce it?
5. What would falsify or demote it?
```

If a named object cannot answer those five questions, it is not yet an
operational object. It may still be a useful idea, but it should stay in thesis
or candidate language.

## 3. Levels

### 3.1 TP: Thesis Pressure

Prefix:

```text
TP
```

Meaning:

Owner-origin idea, metaphor, model pressure, or philosophical claim that drives
the search.

Examples:

```text
TP-FUZZ: reality begins from undifferentiated high-entropy potential
TP-NOMINALISM: identity is not primitive sameness; it is survived distinction
TP-HOLODECK: memory/perception are predictive world-model operations
TP-ENTROPIC-MONISM: entropy/information is the unifying bridge vocabulary
```

Claim ceiling:

```text
translation target
```

Allowed language:

```text
This motivates a constraint.
This suggests a candidate carrier.
This should be translated into QIT language and tested.
```

Forbidden language:

```text
This proves the physics model.
This is already a formal axiom.
This is admitted because it sounds coherent.
```

### 3.2 RC: Root Constraint

Prefix:

```text
RC
```

Meaning:

Minimal operational root pressure that the formal system treats as foundational.

Current roots:

```text
RC-F01: finitude
RC-N01: noncommutation
```

Claim ceiling:

```text
root constraint
```

Root constraints should be few. If the list grows casually, the project loses
its force.

### 3.3 DC: Derived Constraint

Prefix:

```text
DC
```

Meaning:

An implication or anti-smuggling fence derived from the root constraints.

Examples:

```text
DC-IDENTITY: no primitive identity
DC-EQUALITY: no primitive equality
DC-PROBABILITY: no primitive probability
DC-TIME: no primitive time or causality
DC-METRIC: no primitive metric or coordinate distance
DC-CLOSURE: no closure by default
```

Claim ceiling:

```text
derived constraint, if a gate exists
candidate derived constraint, if no gate exists
```

### 3.4 CF: Candidate Fence

Prefix:

```text
CF
```

Meaning:

A plausible operational implication that has not yet earned full derived
constraint status.

Examples:

```text
CF-MARKOV: no primitive classical Markov chain
CF-BLANKET: no primitive classical Markov blanket
CF-SCALAR: no primitive scalarization
CF-SMOOTH: no primitive smoothness or continuity
CF-REVERSIBLE: no free reversibility
```

Candidate fences are important because they name likely future constraints
without pretending the gates are complete.

### 3.5 OE: Operational Extension

Prefix:

```text
OE
```

Meaning:

Concrete enforcement pattern used by code, sims, docs, or controllers.

Examples:

```text
OE-FINITE-REGISTRY: every operator/path family must be enumerable
OE-COMMUTING-CONTROL: every noncommuting signal needs a commuting ablation
OE-MATCHED-NUISANCE: candidate and control must match nonsemantic nuisance variables
OE-CLAIM-CEILING: every scout declares what it cannot claim
OE-RECEIPT: every executable claim writes a result JSON
```

### 3.6 SG: Sim Gate

Prefix:

```text
SG
```

Meaning:

Executable test that checks a narrow claim.

Examples:

```text
SG-QIT-FEP-BASIC: finite predictive world-model scout
SG-FLUX-HOLODECK: flux-guided QIT engine scout
SG-BRIDGE-PHI0: bridge candidate readout scout
SG-CONSTRAINT-ENUM: derived constraint enumeration scout
```

### 3.7 PG: Proof Gate

Prefix:

```text
PG
```

Meaning:

Formal or symbolic proof obligation.

Examples:

```text
PG-QVFE-FINITE: prove finite quantum variational free-energy identity
PG-CPTP-CLOSURE: prove a given engine token family composes into CPTP maps
PG-NO-CLONING: prove noncommuting carrier family cannot be copied/broadcast
PG-GAUGE-INVARIANCE: prove candidate readout survives allowed gauge changes
```

### 3.8 RX: Receipt

Prefix:

```text
RX
```

Meaning:

Evidence artifact produced by a sim, proof checker, or audit.

Examples:

```text
RX-json: result JSON
RX-lint: contract lint output
RX-rerun: fresh-rerun validator output
RX-audit: external or internal audit receipt
```

Receipts are not the same as truth. They are finite evidence tokens.

### 3.9 ST: Status

Prefix:

```text
ST
```

Meaning:

Current epistemic state.

Use a small controlled vocabulary:

```text
ST-thesis
ST-candidate
ST-formal-scout
ST-supported
ST-open
ST-blocked
ST-killed
ST-demoted
ST-canonical
```

Important:

```text
ST-formal-scout != ST-canonical
ST-supported != ST-solved
ST-open != failure
ST-killed under one readout != killed under all possible translations
```

## 4. Mathematical Notation

This section standardizes symbols so docs, sims, and LLMs do not drift.

### 4.1 Carriers

Use:

```text
H
```

for a finite-dimensional Hilbert space.

Use:

```text
D(H)
```

for density operators over H:

```text
D(H) = {rho in B(H): rho >= 0, Tr(rho) = 1}
```

Use:

```text
rho
```

for state.

Use:

```text
rho_AB
```

for a bipartite cut state.

Use:

```text
rho_M
```

for a mediator or memory state.

Avoid:

```text
x in R^n
```

as root language. It may be used only as a classical baseline or derived chart.

### 4.2 Operators And Channels

Use:

```text
O_i
```

for generic operators.

Use:

```text
K_{t,a}
```

for Kraus operators in an instrument at finite stage t.

Use:

```text
Phi
```

for CPTP maps:

```text
Phi(rho) = sum_a K_a rho K_a^dagger
sum_a K_a^dagger K_a = I
```

Use:

```text
Pi = (Phi_1, ..., Phi_T)
```

for a finite operator path.

Avoid:

```text
transition probability matrix
```

unless the doc explicitly labels it classical baseline.

### 4.3 Paths

Use:

```text
h = (a_1, ..., a_T)
K_h = K_{T,a_T} ... K_{1,a_1}
```

for finite hidden histories.

Use:

```text
Z_path = sum_h weight(h) observable(K_h rho K_h^dagger)
```

for finite path-sum evidence.

Avoid:

```text
integral over all paths
```

except as an analogy. The operational object is a finite sum.

### 4.4 Entropy And Information

Use:

```text
S(rho) = -Tr(rho log rho)
```

for von Neumann entropy.

Use:

```text
I(A:B) = S(rho_A) + S(rho_B) - S(rho_AB)
```

for quantum mutual information.

Use:

```text
I_c(A -> B) = S(rho_B) - S(rho_AB)
```

for coherent information.

Use:

```text
D(rho || sigma) = Tr(rho log rho - rho log sigma)
```

for quantum relative entropy.

Important:

```text
I(A:B) >= 0
I_c(A -> B) can be negative
```

Therefore coherent information must never be described as "the same thing as
mutual information" in quantum language.

### 4.5 QIT-FEP

Use:

```text
F_Q(sigma) = D(sigma || tau/Z) - log Z
```

for the finite quantum variational free-energy form when tau is an
unnormalized evidence state and Z = Tr(tau).

Use:

```text
rho_p
```

only when a prior/generative/reference state is actually constructed.

Avoid:

```text
E - T S
```

as the default FEP object, because temperature T imports extra structure.

### 4.6 Axis0

Use:

```text
Phi_0
```

for Axis0 candidate scalar or structured readout.

Use:

```text
Axis0_polarity
```

for feedback polarity:

```text
positive feedback: deviation/correlation diversity expands
negative feedback: deviation/correlation diversity contracts
```

Use:

```text
Axis0_candidate_family
```

when the readout is not admitted.

Avoid:

```text
Axis0 = <one scalar>
```

unless a receipt actually admits that scalar under controls.

### 4.7 Flux

Use:

```text
J_flux
```

for a current-like flux candidate.

Use family labels:

```text
J_geom
J_chiral
J_bloch
J_phase
J_entropy
J_cut
```

Meaning:

```text
J_geom: geometric/transport current
J_chiral: left/right chirality-separation current
J_bloch: Bloch-vector differential current
J_phase: phase/winding current
J_entropy: entropy-production or entropy-transfer current
J_cut: bipartite/cut-state information current
```

Avoid:

```text
Flux is Axis3
Flux is a root
Flux is final
```

Flux is a derived candidate family until a specific current survives its
dependency chain and controls.

### 4.8 Holodeck

Use:

```text
Holodeck
```

for predictive world-model runtime, not for visual simulation alone.

Use:

```text
world_state W
prediction P
observation O
error E
update U
```

Basic pattern:

```text
W_t -> P_t
(P_t, O_t) -> E_t
(W_t, E_t) -> W_{t+1}
```

QIT-aligned pattern:

```text
rho_W -> Phi_predict(rho_W)
effect/observation -> instrument update
posterior rho_W|O
```

## 5. Claim Grammar

### 5.1 Good Claim Shape

Every serious claim should have this structure:

```text
Claim:
  <one sentence>

Level:
  TP / RC / DC / CF / OE / SG / PG / RX / ST

Carrier:
  <finite state object>

Operation:
  <operator, channel, proof rule, or process step>

Observable:
  <what is measured>

Controls:
  <what would kill the interpretation>

Receipt:
  <result path or not-yet-run>

Status:
  <controlled status label>

Claim ceiling:
  <what this does not prove>
```

### 5.2 Bad Claim Shapes

Bad:

```text
This proves Axis0.
```

Better:

```text
This formal scout supports one Axis0 candidate family under these controls.
It does not admit final Axis0.
```

Bad:

```text
Markov chain, but quantum.
```

Better:

```text
The classical Markov-chain role is replaced by finite CPTP instrument
composition over density states.
```

Bad:

```text
Flux explains it.
```

Better:

```text
The J_chiral candidate separates left/right engine basins under this topology
and fails when chirality is removed.
```

Bad:

```text
The old doc says spacetime is entropy.
```

Better:

```text
The old doc supplies TP-ENTROPIC-MONISM. The QIT translation must construct a
finite entropy/geometry readout and test whether it predicts engine behavior
under controls.
```

## 6. Constraint Naming

Use stable names even if numbers move.

Recommended labels:

```text
RC-F01-finitude
RC-N01-noncommutation
DC-no-primitive-identity
DC-no-primitive-equality
DC-no-primitive-probability
DC-no-primitive-time-causality
DC-no-primitive-metric-coordinate
DC-no-closure-by-default
DC-finite-witness-discipline
DC-no-cloning-broadcasting
DC-no-primitive-optimization
DC-no-outside-observer
DC-no-global-total-order
DC-no-semantic-smuggling
CF-no-primitive-tensor-factorization
CF-no-classical-markov-chain
CF-no-classical-markov-blanket
CF-no-primitive-scalarization
CF-no-primitive-smoothness
CF-no-free-reversibility
```

Numbers can be added for convenience, but the stable slug should carry the
meaning.

Why:

The project has old EC numbering in some side lanes. Those numbers are useful
for local receipts, but the docs need names that survive renumbering.

## 7. Axis Naming

Use:

```text
Axis0
Axis1
Axis2
...
```

only when referring to the historical axis stack.

For current technical work, prefer:

```text
Axis0_feedback_polarity
Axis0_cut_readout
Axis0_candidate_family
Axis0_bridge
Axis0_control_degeneracy
```

This prevents the common LLM error:

```text
Axis0 worked somewhere, therefore Axis0 is solved.
```

The current live doctrine is:

```text
Axis0 is open_partial.
Positive/negative feedback polarity is the strongest role-level reading.
Several candidate families are useful.
No final scalar or final cut is admitted.
```

Axis stack translation table:

| Axis | Stable technical name | QIT/operator translation | Claim boundary |
| --- | --- | --- | --- |
| Axis0 | `Axis0_entropy_or_cut_polarity` | chart `b0=sign(cos(2eta))`; bridge candidate `Phi_0(rho_AB)` | open; chart seat is not final cut kernel |
| Axis1 | `Axis1_terrain_branch_split` | `{Se,Ni}` dissipator-dominant vs `{Ne,Si}` Hamiltonian-dominant | derived from Axis0 and Axis2 |
| Axis2 | `Axis2_frame_choice` | direct `rho_tilde=rho` vs conjugated `V^dagger rho V` with gauge term | locked frame law |
| Axis3 | `Axis3_path_geometry` | fiber density-stationary vs lifted-base horizontal density-traversing | not flux; inner/outer is chart-relative |
| Axis4 | `Axis4_loop_order_family` | `U o E o U o E` vs `E o U o E o U` | likely engine-level, not per-stage |
| Axis5 | `Axis5_operator_family` | dephasing `{Ti,Te}` vs rotation `{Fi,Fe}` | locked channel/generator family |
| Axis6 | `Axis6_precedence_action_orientation` | token precedence plus `L_A(rho)=A rho`, `R_A(rho)=rho A` | derived; not a CPTP channel without closure |

When an agent writes an axis row, it should include both the legacy label and
the technical translation. A safe row looks like:

```text
axis_id: A6
legacy_axis_role: up/down token precedence
current_qit_translation: left/right primitive action plus physical closure
axis6_precedence: operator_first
axis6_action_side: left
closure_type: commutator or Kraus or GKSL or unitary_adjoint
claim_ceiling: formal_scout
```

## 8. Engine Naming

Avoid "engine" as a vague metaphor.

Use:

```text
engine_token
engine_registry
engine_path
engine_channel
engine_readout
engine_control
```

An engine token should specify:

```text
domain: state space it acts on
operation: unitary/channel/instrument
parameters: finite bounded set
composition: how it composes
controls: commuting/product/reversed/order-erased baselines
```

Example:

```text
engine_token: Pauli-X dephasing channel
domain: D(C^2)
operation: Phi(rho) = (1-q)rho + q X rho X
parameters: q in finite grid
control: q=0 identity, Z-commuting channel, order reversal
```

## 9. Manifold Naming

The constraint manifold should not be named as if it were a smooth manifold by
default.

Use:

```text
M(C)
```

for the admitted constraint surface:

```text
M(C) = finite structure surviving active constraints C
```

Use:

```text
chart
cell
graph
hypergraph
operator registry
cut
coarse-graining
basin
```

as concrete realizations.

Avoid:

```text
the manifold
```

when the carrier has not been named.

Better:

```text
the finite cellular constraint manifold for this scout
the graph-cut manifold in this receipt
the spinor/Hopf carrier manifold candidate
```

## 10. Ratchet Naming

Use:

```text
ratchet
```

for the directional filtering process that admits structures only after they
survive constraints and controls.

Do not use ratchet to mean:

```text
any progress
any repeated process
any positive result
```

Operational ratchet requirements:

```text
candidate space
constraint pressure
finite gate
negative controls
receipt
status update
next stricter gate
```

## 11. LLM Enforcement

LLMs should be given the following instruction:

```text
When a user says "axiom", classify the statement first:
TP, RC, DC, CF, OE, SG, PG, RX, or ST.
Do not preserve the word axiom if it hides the operational level.
```

LLMs should also be forced to output:

```text
claim ceiling
controls
receipt status
unknowns
```

for every theory claim.

## 12. Machine-Readable Schema Fragment

Every registry item should support this shape:

```json
{
  "id": "DC-no-primitive-probability",
  "level": "derived_constraint_candidate",
  "human_statement": "Probability is not primitive.",
  "forbidden_import": "standalone probability distribution",
  "qit_translation": "probabilities arise from state plus probe/effect",
  "cs_enforcement": "require named probe/effect for probability readouts",
  "positive_gate": "same state produces different distributions under noncommuting probes",
  "negative_gate": "classical-probability baseline fails",
  "status": "candidate_needs_gate_or_receipt",
  "claim_ceiling": "not a final theorem without formal gate"
}
```

## 13. Current Best Short Vocabulary

For humans:

```text
The project starts from finite order-sensitive distinction.
The world is modeled as constrained high-entropy possibility becoming
stable, probe-surviving structure.
```

For CS:

```text
Finite state carriers, ordered noncommuting operations, explicit probes,
negative controls, bounded receipts.
```

For QIT:

```text
finite density states, CPTP maps, instruments, quantum relative entropy,
coherent/mutual information, cut states, noncommuting controls.
```

For LLMs:

```text
No word promotes itself. Every claim needs level, carrier, operation,
observable, controls, receipt, status, and claim ceiling.
```

For the system:

```text
Docs propose. Sims test. Receipts constrain. Status surfaces admit or demote.
```
