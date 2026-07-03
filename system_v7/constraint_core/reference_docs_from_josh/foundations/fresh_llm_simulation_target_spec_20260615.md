# Fresh-LLM Simulation Target Spec — Codex-Ratchet × LevOS Bridge (2026-06-15)

```yaml
status: DRAFT_FOR_SIM_BUILD
claim_ceiling: specification_only
promotion_allowed: false
formal_admission_allowed: false
purpose: >
  Give a fresh LLM enough explicit math, axioms, constraints, hypotheses,
  variants, strict gates, and exploration rules to begin building simulations
  without importing private project jargon as if it were math.
source_packet:
  zip: /Users/joshuaeisenhart/Desktop/levos_bridge_packet_josh_updates_AUDITED_20260615 (1).zip
  key_files:
    - 06_TECHNICAL_MAPPING_TO_LEV_REPO_PRIMITIVES.md
    - 08_CODEX_RATCHET_MATH_BRIDGE_AND_SIM_TARGETS.md
    - sim_targets/*.md
    - candidate_schemas/*.json
    - candidate_flows/ratchet_sim_eval_three_engine.flow.yaml
repo_sources:
  - system_v6/foundations/root_axioms_v0_1_DRAFT.md
  - system_v6/foundations/mss_and_rung_climb_foundations_DRAFT_20260615.md
  - system_v6/foundations/ratchet_definition_and_emergence_spec_DRAFT_20260614.md
  - system_v6/foundations/manifold_layer_order_and_completeness_contract_20260614.md
  - system_v6/foundations/ratchet_runbook_DRAFT_20260615.md
  - system_v6/foundations/entropic_monism_one_distinguishability_process_DRAFT_20260614.md
```

## 0. Instructions to the fresh LLM

You are not validating a theory. You are building bounded simulations that test a hypothesis.

Do not start from the owner's desired end-state. Do not name simulations after private model language. Do not treat density matrices, spinors, Hopf geometry, manifolds, QCA, Hopfield memory, entropy, or LevOS graph state as primitive unless a lower layer forces them.

You must keep two separate processes active:

1. **Wide Explorer / Defense Process (`A`)** — generate many legitimate mathematical variants at the gate.
2. **Strict Gate / Prosecutor Process (`B`)** — assume every candidate is trying to hack admission; reject anything with jargon, premature structure, fake proof, missing negatives, or name/math mismatch.

A candidate survives only when `A` presents a mathematically legitimate variant and `B` cannot kill it under the active gates.

All outputs must use honest status labels:

```text
exists < runs < passes local rerun < canonical by process
```

Nothing in this document is canonical proof. It is a simulation target specification.

---

# Part I — What is actually being simulated?

## 1. The object under test

The core object is not a manifold, not a person, not a company, not entropy, not a density matrix, not QCA, and not LevOS.

The core object is:

```text
finite constrained distinguishability
```

At a simulation step `t`, represent it as:

```text
D_t = (X_t, P_t, ~_{P_t}, C_t, Adm_t, U_t, H_t, R_t)
```

Where:

```text
X_t        finite candidate support / finite carrier set
P_t        finite probe family, each p ∈ P_t a total function p: X_t -> V_p
V_p        finite value set for probe p
~_{P_t}    probe-relative indistinguishability relation on X_t
C_t        active constraint set
Adm_t      admissibility predicate under C_t
U_t        optional supplied update / composition family
H_t        history / receipt / graveyard / branch ledger
R_t        finite readout registry produced after admission, never primitive
```

The first mathematical object to compute is the quotient:

```text
Q_t = X_t / ~_{P_t}
```

with canonical projection:

```text
q_t : X_t -> Q_t
```

The equivalence relation is:

```text
x ~_{P_t} y  iff  ∀p ∈ P_t, p(x) = p(y)
```

This is the first admissible identity object. Identity is earned by probe-indistinguishability, not assumed.

## 2. The LevOS bridge interpretation

The LEVOS bridge packet maps this math into LevOS primitives:

```text
LevOS runtime fabric       = FlowMind + Graph + Event Bus + Orchestration + Exec + AgentPing + AgentLease + Semantic Control + Receipts
Codex-Ratchet discipline   = quotient awareness + strict admission + minimal survivor gate + proof/eval discipline
Wizard                     = council/context/failure-review layer
Leviathan/OpenHR/OpenFinance = social/business/domain projections, not separate truth stores
```

Mathematically, LevOS graph state should be treated as a finite contextual claim graph:

```text
G_Lev = (E, K, L, Ev, Rcpt, Lease, Status)
```

Where:

```text
E       finite entity set: persons, teams, orgs, roles, skills, needs, capacities, sessions, dictionaries
K       finite contextual claim set
L       typed links among entities and claims
Ev      evidence references
Rcpt    receipts / provenance / audit traces
Lease   scoped authority / visibility grants
Status  draft | proposed | admitted | rejected | parked | expired | disputed | superseded
```

A LevOS graph claim is a quotient readout, not the full carrier.

Example:

```text
public skill credential != full person
KPI != full company
shared action vector != full local intent carrier
org dictionary term != universal meaning
```

The simulation target is therefore two-layered:

1. **Mathematical foundation simulations** — test finite constrained distinguishability and what structures are forced.
2. **LevOS projection simulations** — test whether LevOS graph/claim/receipt primitives preserve quotient discipline and avoid collapsing private carriers into public scores.

---

# Part II — Root axioms and meta-constraints

## 3. Root axiom A0 — constraint on distinguishability

There is one primitive:

```text
constraint on distinguishability
```

Local formalization:

```text
P = finite active probe family
x ~_P y iff probes in P fail to distinguish x,y
identity_P(x,y) := [x ~_P y]
```

No global identity is primitive.

The slogan:

```text
a = a iff a ~ b
```

means: identity is relative to admitted probes and constraints.

## 4. Axiom A1 — finitude (`F01`)

Every object inside a simulation witness is finite:

```text
|X| < ∞
|P| < ∞
|C| < ∞
|H| < ∞ at each finite step
|R| < ∞ at each finite step
```

No completed infinity may appear as root furniture.

Allowed: finite approximations, finite rings, finite arrays, finite graphs, finite Hilbert spaces if and only if a lower admissible layer forces them.

Not allowed as primitive: continuum, smooth manifold, infinite chain, completed Hilbert space, global metric, global time.

## 5. Axiom A2 — exclusion-first

Constraints eliminate; they do not generate ontology.

Given an admissibility predicate:

```text
Adm_C : Q -> {0,1}
```

survivors are:

```text
Surv(C) = { q ∈ Q : Adm_C(q) = 1 }
```

For a stepwise process:

```text
X_{t+1} = { x ∈ X_t : Adm_{C_{t+1}}(x, context_t) = 1 }
```

Then:

```text
X_{t+1} ⊆ X_t
```

If a step adds entities, it is not an exclusion step unless additions are explicitly modeled as a new branch or replay receipt.

## 6. Axiom A3 — weak noncommutation (`N01`)

Order is not presumed swappable.

For two supplied operations or constraints:

```text
σ_A, σ_B : state -> state
```

N01 witness:

```text
σ_B(σ_A(S_0)) ≠ σ_A(σ_B(S_0))
```

But this must be measured on the actual survivor object, not only on abstract maps.

Valid survivor-set witness:

```text
δ(A,B;X) = | σ_B(σ_A(X)) △ σ_A(σ_B(X)) |
```

where `△` is symmetric difference.

Order dependence is present iff:

```text
δ(A,B;X) > 0
```

Control:

```text
if σ_A, σ_B reduce to static predicates on X, then they commute by intersection
```

So a valid noncommutation sim must show why the operations are not merely static filters.

## 7. Axiom A4 — nonassociativity / bracketing is separate from order

Order swap and bracketing are different tests.

Order:

```text
A ∘ B vs B ∘ A
```

Bracketing:

```text
(A ∘ B) ∘ C vs A ∘ (B ∘ C)
```

A valid composite-layer simulation must test both when grouping carries a claim.

Nonassociativity witness:

```text
α(A,B,C;X) = | σ_C(σ_B(σ_A(X))) △ σ_{BC}(σ_A(X)) |
```

or another explicitly defined associator-like witness over survivor sets.

No claim about nonassociativity is valid if only order-swap was tested.

## 8. Meta-constraint M0 — MSS / minimal admissible survivor

MSS is not a new root axiom. It is an admission meta-gate.

Canonical rule:

```text
Admit only the least-assumptive structures that survive the active constraints and still support nontrivial admissible continuation.
```

Formal candidate:

Let `Struct(C)` be the candidate structures compatible with active constraints `C`.
Let `Surv(C)` be the subset that survives all active tests.
Define a structure-strength preorder:

```text
A ⪯ B  means  A assumes no more structure than B
```

Then the admissible frontier is:

```text
Min(Surv(C)) = { A ∈ Surv(C) : no B ∈ Surv(C) with B ≺ A }
```

Important: `Min(Surv(C))` may contain several incomparable structures. Keep them live.

### 8.1 Operational definitions of `A ⪯ B` to explore

The preorder is itself a hypothesis and must be explored in variants.

Candidate preorder variants:

```text
V1 quotient/coarsening: A ⪯ B iff B projects onto A by a structure-preserving surjection
V2 definitional strength: A ⪯ B iff A uses a strict subset of primitive operations/relations used by B
V3 automorphism freedom: A ⪯ B iff Aut(B) is more restricted than Aut(A), so B assumes more structure
V4 representation dependence: A ⪯ B iff A is invariant under more representation changes than B
V5 data requirement: A ⪯ B iff A needs fewer fields in the witness tuple than B
V6 prediction compression: A ⪯ B iff A explains the same test outcomes with no stronger carrier
```

Do not choose one preorder globally without tests. Run variants and compare.

## 9. Meta-constraint M1 — no raw entropy at the foundation

Entropy is not primitive.

Entropy is a typed readout licensed by an already-existing structure.

Allowed entropy forms only when their enabling object exists:

```text
capacity entropy      log |X|                         requires finite support X
quotient entropy      log |X/~_P|                     requires quotient Q
branch entropy        H(status distribution)          requires status/branch ledger
state entropy         S(ρ)                            requires density/operator representation ρ
cut entropy           S(ρ_A), I(A:B), etc.             requires cut structure and density object
fiber residual        H(lift) - H(base)               requires projection/lift pair
```

`E_t` may be recomputed after a carve. It must not be a primitive argument that decides admissibility at the root.

Forbidden:

```text
Adm_C(x, entropy) at the foundation
```

unless a later layer has explicitly licensed a typed entropy form as a downstream readout and the claim is not root-level.

## 10. Meta-constraint M2 — quotient is not carrier

Public or compressed readouts are not the full object.

Mathematical form:

```text
q : Carrier -> Quotient
```

Never infer:

```text
q(a) = q(b)  =>  a = b globally
```

Only infer:

```text
q(a) = q(b)  =>  a ~_q b under that quotient
```

LevOS form:

```text
public credential / KPI / trust score / role fit / shared action vector
```

is a quotient readout. It is not the full person, company, community, or local carrier.

Required for every quotient readout:

```text
what it preserves
what it erases
what future probe could split it
what private/local carrier it does not expose
```

---

# Part III — Constraints and extended constraints

## 11. Base constraints

### C0 — finite support

```text
X finite
```

Reject if witness requires infinite support.

### C1 — finite probes

```text
P = {p_i}_{i=1..m}, m finite
p_i : X -> V_i, V_i finite
```

Reject if probe family is undefined, infinite, or non-computable.

### C2 — quotient well-defined

```text
~_P is reflexive, symmetric, transitive
Q = X/~_P exists as a finite partition
```

This should follow from probe equality, but must be computed.

### C3 — admissibility predicate explicit

```text
Adm_C : Q or X -> {0,1}
```

Every constraint must name its domain:

```text
on raw support X
on quotient Q
on history H
on geometry G
on graph state
on carrier representation
```

Reject if the predicate silently changes domain.

### C4 — no primitive equality

All equality-like claims must name the relation:

```text
same under P
same under quotient q
same under status map
same under graph projection
same under public credential
```

Reject bare:

```text
same
identical
canonical
true identity
```

unless the probe/quotient relation is explicitly named.

### C5 — source of dynamics explicit

Static exclusions commute.

If a sim claims order-dependence, it must state what supplies dynamics:

```text
update maps U
history dependence H
running survivor set X_t
local QCA rule
graph operation sequence
FlowMind transition
```

Reject if dynamics are implied but not defined.

## 12. Extended constraints

### EC1 — weak-to-strong lift criterion

A stronger layer `L_{k+1}` is admitted only with a failure receipt showing:

```text
L_k cannot carry required distinction d
L_{k+1} can carry d
L_{k+1} is weakest among tested alternatives that carries d
projection π: L_{k+1} -> L_k is defined
residual R = information in L_{k+1} not visible in L_k is measured
```

### EC2 — nesting compatibility

For upper object `A` and lower object `B`:

```text
B ⊆ A
π_{A->B}: X_A -> X_B
```

Compatibility:

```text
π_{A->B}(x_A) ~_B x_B
```

Quantum/density version when licensed:

```text
Tr_{A\B}(ρ_A) ~_B ρ_B
```

But the trace form is allowed only after density objects are earned.

### EC3 — extension fibers

For a lower object `b ∈ X_B`, define admissible lifts:

```text
F_A(b) = { a ∈ X_A : π_{A->B}(a) ~_B b and Adm_A(a)=1 }
```

A nesting layer must enumerate or sample fibers and show at least one negative:

```text
bad a projects incorrectly or fails Adm_A
```

### EC4 — order and bracketing controls

For any ordered claim:

```text
AB vs BA
```

must be tested.

For any composite claim:

```text
(AB)C vs A(BC)
```

must be tested.

### EC5 — multi-depth / ladder constraint

A result at one depth does not validate a layer.

For a depth-indexed structure:

```text
run depth d_min
run useful depth d_useful
run one beyond: d_useful + 1
```

If qubits are involved:

```text
1q = diagnostic only
2q = first nontrivial cut/nesting
3q = QIT/runtime floor if cuts/memory/Cl(6) matter
4q = one-beyond control for 3q floor
```

### EC6 — graph/LevOS admission constraint

LevOS graph state changes only after a receipt-backed admission loop:

```text
INGEST -> OBSERVE -> PROPOSE -> ADMISSION_GATE -> ACT -> VERIFY_GATE -> ADAPT -> DECIDE/APPLY -> UPDATE -> EMIT
```

No LLM observation is admitted graph state.

Graph update must cite:

```text
evidenceRefs
proofRefs
receiptRefs
leaseRefs if sensitive
sourceRefs
status
```

### EC7 — privacy / carrier sovereignty constraint

Private carrier and public quotient must be separated.

```text
private draft space != company memory
promoted work artifact = candidate graph update
admitted claim + receipt = company memory
```

Simulations involving people/orgs must not collapse private carrier into public score.

---

# Part IV — Two separate processes: Explorer and Gate

## 13. Process A — Wide Explorer / Defense Lawyer

Explorer's job: generate legitimate mathematical candidates, variants, and repairs.

Explorer must not decide admission.

Inputs:

```text
current rung L_k
active constraints C
known failures
old v6/v5 sims as fuel
a desired next distinction d
```

Explorer outputs a candidate packet:

```yaml
candidate_id: pure_math_name
rung: integer_or_fork
object: explicit math object
weaker_object: L_k
stronger_object_if_any: L_{k+1}
what_weaker_loses: distinction/order/entropy/readout/continuation
variant_family: name
positive_tests: []
negative_tests: []
projection_back: formula
residual: formula
expected_failure_modes: []
claim_ceiling: scratch_diagnostic
```

Explorer must produce variants, not one favorite.

Variant families to generate at each gate:

```text
preorder variants for MSS
probe-family variants
constraint-family variants
update-family variants
carrier variants
readout variants
nesting-map variants
control variants
representation variants
```

## 14. Process B — Strict Gate / Prosecutor

Gate's job: assume the candidate is a hack.

Reject for:

```text
jargon in names/keys/formulas
name does not match actual math
private model term used as math object
stronger structure entered without failure receipt
missing negative controls
single-model audit only
self-audit only
static filter miscalled ratchet
count tautology miscalled proof
metadata/hash/prose miscalled evidence
quotient miscalled carrier
1q-only result miscalled valid
entropy used raw at foundation
```

Gate outputs:

```yaml
verdict: ACCEPT | REJECT | PARK
status_ceiling: exists | runs | passes_local_rerun | canonical_by_process
killed_because: []
survives_because: []
missing_controls: []
required_next_variant: []
graveyard_entry: true|false
```

Gate must distinguish:

```text
mechanical pre-filter pass != validity
multi-model cross-audit clean != canon
passes local rerun != canonical by process
```

## 15. Interaction loop

```text
A proposes many variants
B kills malformed / overbuilt / under-tested variants
A repairs or branches
B re-tests
survivors remain plural until evidence excludes them
failures enter graveyard
```

Failure is useful. A killed candidate is evidence.

---

# Part V — First simulations to run

## 16. Sim 0 — finite_probe_quotient_floor_v0

Purpose: establish the first forced object.

Math:

```text
X finite
P finite probe family
f_P(x) = (p_1(x), ..., p_m(x))
Q = image(f_P)
x ~_P y iff f_P(x)=f_P(y)
```

Outputs:

```text
class table
fiber sizes
quotient entropy log |Q| as typed readout
probe erase/add flip
label shuffle invariant
```

Controls:

```text
remove p_i -> classes merge or stay same with reason
add p_new -> classes split or stay same with reason
shuffle labels -> same partition structure
constant probe -> no split
duplicate probe -> no split
```

Pass condition:

```text
Q computed from probes; controls behave as predicted; no stronger carrier used
```

## 17. Sim 1 — admissible_survivor_subset_v0

Purpose: test constraints as exclusion.

Math:

```text
Adm_C : Q -> {0,1}
Surv_C = {q ∈ Q : Adm_C(q)=1}
```

Variants:

```text
constraint on quotient value
constraint on fiber size
constraint on local relation
constraint on update continuation
constraint on graph receipt status
```

Controls:

```text
relaxed constraint -> Surv grows
strengthened constraint -> Surv shrinks
invalid class -> rejected
boundary class -> explicitly classified
```

## 18. Sim 2 — survivor_restriction_order_v0

Purpose: test whether order-dependence is present only when supplied operations actually make it present.

Math:

```text
σ_A(X) = {x ∈ X : Adm_A(x, X, H)=1}
σ_B(X) = {x ∈ X : Adm_B(x, X, H)=1}
δ(A,B;X) = |σ_B(σ_A(X)) △ σ_A(σ_B(X))|
```

Variants:

```text
static predicates
running-survivor-set predicates
history-dependent predicates
local QCA predicates
nonlocal aggregate predicates
```

Controls:

```text
static/fixed-reference -> δ=0
commuting operations -> δ=0
label shuffle -> δ invariant
state-dependent but confluent rule -> δ=0
```

Pass condition:

```text
if δ>0, source of noncommutation is isolated and not handpicked
```

## 19. Sim 3 — bracketing_nonassociativity_v0

Purpose: test grouping, not order swap.

Math:

For operations `A,B,C`:

```text
L = σ_C(σ_B(σ_A(X)))
R = σ_{BC}(σ_A(X))       or another explicitly defined grouped composite
α(A,B,C;X)=|L△R|
```

Controls:

```text
known associative family -> α=0
different order but same bracketing -> separated from associativity test
label shuffle -> invariant
```

## 20. Sim 4 — forced_or_installed_carrier_comparison_v0

Purpose: test whether stronger carriers are forced or merely installed.

Candidate carriers:

```text
C0 bare quotient Q
C1 Boolean algebra of Q-invariant subsets
C2 weighted finite measure over Q
C3 state functional ω on a probe/update expression set
C4 classical probability simplex
C5 operator algebra representation
C6 density matrix ρ
C7 spinor / lifted carrier
```

Criterion:

For a stronger carrier `S`, reduce it to quotient-observable behavior:

```text
Obs(S) -> behavior on Q under active probes/updates
```

Then enumerate compatible extensions:

```text
Ext(Q,C) = { S_i : Obs(S_i) matches all active probe/constraint data }
```

If there exist non-isomorphic `S_i, S_j` with same observed behavior, then `S` is not forced.

Forced only if:

```text
∀S_i,S_j ∈ Ext(Q,C), S_i ≅ S_j at the relevant observable level
```

Controls:

```text
classical baseline
overbuilt carrier ablation
probe erase
added closure constraint
future held-out probe
```

## 21. Sim 5 — finite_ring_checkerboard_support_consistency_v0

Purpose: test owner-native finite run-surface as support, not as late metaphor.

Math:

```text
R_N = Z/NZ
Alphabet A finite, e.g. {0,1}
X = A^{R_N}
checkerboard partition = even/odd local blocks
local block update u : A^k -> A^k
brickwork update U = U_odd ∘ U_even
```

Tests:

```text
flat checkerboard presentation
spherical/shell presentation
nested ring/fiber presentation
```

Compare:

```text
support count
probe bins
quotient classes
adjacency/readout invariants
reindexing invariants
```

Controls:

```text
random relabel
broken adjacency
non-reversible local update when reversibility claimed
identity update
left/right shift calibration
```

## 22. Sim 6 — qca_operator_index_v0

Purpose: test finite QCA directional flow invariant without hardcoding shift.

Math:

For a finite ring operator algebra, define a locality algebra across a cut:

```text
A_L, A_R
U operator automorphism induced by brickwork circuit
U(A_L), U(A_R)
```

Compute an index-like support flow from realized operator images, not metadata.

Controls:

```text
identity circuit -> index 0
finite-depth local circuit -> index 0
right shift -> +1 calibration
left shift -> -1 calibration
shift by k -> k up to finite-ring ceiling
```

Pass condition:

```text
index computed from conjugated operator support, not from a stored shift label
```

## 23. Sim 7 — geometric_constraint_ratchet_on_finite_support_v0

Purpose: test the geometric ratchet carefully, without overclaiming emergence.

Math:

```text
X_t finite survivor set
Q_t = X_t / ~_{P_t}
G_t = InducedGeometry(Q_t)
σ_i(X_t) = {x ∈ X_t : Adm_i(x, Q_t, G_t, H_t)=1}
X_{t+1}=σ_i(X_t)
Q_{t+1}=X_{t+1}/~_{P_{t+1}}
G_{t+1}=InducedGeometry(Q_{t+1})
```

Readouts:

```text
|X_t|
|Q_t|
relation graph of Q_t
branch entropy / quotient entropy if licensed
order witness δ(i,j;X)
terminal set
```

Controls:

```text
fixed reference set
static predicate
commuting constraints
amnesic history
label shuffle
empty-set behavior
```

Pass condition:

```text
ordered constraints produce different survivor/readout histories for structural reasons, not handpicked graveyard logic
```

## 24. Sim 8 — LevOS contextual_claim_admission_v0

Purpose: project the math into LevOS graph semantics.

Objects:

```text
Entity set E
Claim set K
Context set Ctx
Evidence set Ev
Receipt set Rcpt
Lease set Lease
Status map π: K -> statuses
```

A contextual claim:

```text
k = (subjectId, context, predicate, value, visibility, evidenceRefs, proofRefs, receiptRefs, leaseRefs, status)
```

Quotient relation over claims:

```text
k1 ~_ctx k2 iff subject/context/predicate/readout agree under admitted org dictionary and visibility policy
```

Tests:

```text
same public readout, different private evidence -> not globally same
missing evidence -> not admitted
lease absent -> sensitive proof inaccessible
contradictory claim -> parked/disputed
superseded receipt -> old claim inactive
```

Controls:

```text
LLM-only claim -> rejected
vector similarity merge -> rejected unless witnesses preserved
label shuffle -> graph semantics invariant
private draft -> not company memory
admitted receipt -> company memory
```

## 25. Sim 9 — shared_action_vector_quotient_v0

Purpose: test shared action vector as temporary downstream artifact, not root identity.

Objects:

```text
participants I={1..n}
local intent carriers L_i
translation maps τ_i : L_i -> A_public
shared action vector a ∈ A_public
residual disagreement refs D_i
```

Pass condition:

```text
shared action accepted only if residual disagreements are recorded and local carriers remain sovereign
```

Controls:

```text
same action, different residuals -> not identical contexts
missing translation -> reject
coerced merge -> reject
expired proof -> reject
```

---

# Part VI — Variant exploration matrix

## 26. Variants to explore at every gate

### 26.1 Probe variants

```text
single probe
multiple independent probes
duplicate probe
constant probe
coarse probe
fine probe
local probe
global aggregate probe
future/held-out probe
```

### 26.2 Constraint variants

```text
static predicate
running-survivor predicate
history-dependent predicate
geometry-dependent predicate
local QCA predicate
nonlocal aggregate predicate
receipt-dependent predicate
visibility/lease predicate
```

### 26.3 Carrier variants

```text
bare quotient
Boolean lattice
finite graph
weighted finite set
state functional
classical probability simplex
operator algebra
density matrix
spinor/lift
QCA support
Hopfield basin
```

### 26.4 Nesting variants

```text
projection by quotient
projection by partial trace when licensed
projection by graph homomorphism
projection by support restriction
extension by fiber enumeration
extension by compatible lift
```

### 26.5 Gate variants

```text
blacklist pre-filter
definedness allow-list
multi-model cross-audit
formal solver flip
three-engine agreement
fresh-context audit
manual source-trace audit
```

---

# Part VII — Strict gates

## 27. Gate G0 — naming and vocabulary

Simulation names must describe exact math.

Bad:

```text
axis0_terrain_engine_leap_v0
rpf_dual_chiral_engines_v0
```

Good pattern:

```text
finite_probe_quotient_floor_v0
survivor_set_running_mean_threshold_noncommutation_v0
finite_ring_block_partition_reversible_qca_index_v0
```

Reject if name contains private jargon unless the term is standard math and defined.

## 28. Gate G1 — name/math correlation

Every noun in the name must correspond to a computed object.

If name says:

```text
quotient -> result must include equivalence relation and classes
ring -> result must include cyclic index arithmetic
reversible -> result must prove inverse or bijection
qca -> result must define local update algebra/circuit
index -> result must compute invariant from operator/support structure
noncommutation -> result must compute AB vs BA witness
```

## 29. Gate G2 — MSS gate

Reject if stronger structure appears without lower-layer failure receipt.

For every structure field, require:

```yaml
structure: density_matrix | spinor | geometry | metric | qca | graph | entropy_form
installed_by: constraint_or_failure_receipt
weaker_layer_failed_because: path
projection_back: formula
residual: formula
```

## 30. Gate G3 — proof/solver gate

A solver proof is load-bearing only if it solves a structural condition.

Reject tautologies:

```text
count == computed_count
count == expected_constant
n == product
```

Accept only with real/erased or positive/negative flip:

```text
real structure -> SAT/UNSAT
structure erased -> opposite verdict
```

## 31. Gate G4 — engine independence gate

At least two independent representations for early sims; three for serious layers.

Examples:

```text
exact Python sets
JAX boolean masks / batched arrays
PyTorch graph/tensor implementation
Julia exact algebra implementation
SMT proof
```

Reject if engines read each other's outputs or share one hidden `build_packet()`.

## 32. Gate G5 — multi-model audit gate

No single model decides.

Minimum for serious result:

```text
codex2 arbiter lane
Claude orchestrator/fresh audit lane
at least two finder models: grok/gemini/openrouter
```

Disagreement is not averaged. It is held and resolved by evidence.

## 33. Gate G6 — status ceiling

Every result must set:

```yaml
classification: scratch_diagnostic | classical_baseline | tool_lego_fit_probe | canonical
promotion_allowed: false unless all gates pass
formal_admission_allowed: false unless canonical by process
claim_ceiling: exact label
```

---

# Part VIII — Required outputs for every sim

Each sim directory must contain:

```text
spec.json                       pure data and hypothesis, no precomputed answer
*_exact.py or equivalent         exact reference leg
*_jax.py                         if batched/exhaustive useful
*_torch.py or *_julia.jl          if graph/algebra useful
check_agreement.py               compares invariants, not prose
results/*_results.json           per-engine result JSONs
results/*_agreement.json         agreement summary
audit_verdict.md                 honest status and caveats
FLEET_VERDICT_*.md               multi-model verdict when run
```

Each result JSON must include:

```yaml
schema: codex_ratchet.engine_leg_result.v1
sim_id: string
classification: scratch_diagnostic
promotion_allowed: false
formal_admission_allowed: false
objects:
  X: description
  P: description
  quotient: description
claims:
  claimed_fact: bool_or_value
controls:
  positive: result
  negative: result
  boundary: result
honest_scope:
  earns: string
  does_not_earn: string
packages_used: []
TOOL_MANIFEST: []
```

---

# Part IX — Hypotheses, not truths

## 34. Active hypotheses

H1:

```text
Finite probe-relative quotient S/~_P is the first forced object.
```

H2:

```text
Density matrices are installed representation rungs, not the floor.
```

H3:

```text
Spinors are closure witnesses, not primitive starts.
```

H4:

```text
Ring-checkerboard / QCA finite support may be the owner-native run-surface for ordered distinguishability.
```

H5:

```text
LevOS graph semantics can enforce quotient-aware identity: public graph claims are contextual quotient readouts, not full carriers.
```

H6:

```text
The ratchet is not a metaphor but a repeatable finite ordered exclusion process with memory; however, its emergence from local rules is not yet earned.
```

## 35. Null hypotheses

N0:

```text
A weaker quotient-only structure can carry the same distinctions; stronger carrier is unnecessary.
```

N1:

```text
Observed order dependence is handpicked, metadata-driven, or convention-driven.
```

N2:

```text
Multi-engine agreement is shared implementation, not independent confirmation.
```

N3:

```text
LevOS public claims collapse private carrier distinctions and therefore fail quotient discipline.
```

N4:

```text
The proposed stronger layer is only a relabel of already-known data.
```

---

# Part X — First execution plan for a fresh LLM

Run in this order. Do not skip.

## Step 1 — build or inspect Sim 0

```text
finite_probe_quotient_floor_v0
```

If absent, build it from scratch.

If present, audit it.

Do not use density matrices unless specifically testing whether they are installed.

## Step 2 — build Sim 1

```text
admissible_survivor_subset_v0
```

Use a toy but nontrivial finite support.

## Step 3 — build Sim 2 with variants

```text
survivor_restriction_order_v0
```

Run at least:

```text
static predicate family
running-survivor predicate family
history-dependent family
local QCA family
nonlocal aggregate family
```

Record which are confluent and which noncommute.

## Step 4 — run forced-or-installed carrier comparison

Do not assert density matrix status. Test it.

## Step 5 — run LevOS projection sim

Use schemas:

```text
lev.contextual-claim.v1
lev.org-dictionary.v1
lev.shared-action-vector.v1
```

Test whether graph admission preserves quotient discipline.

## Step 6 — only then attempt QCA/Hopf/spinor/manifold candidates

Each stronger layer must cite the failure receipt from a weaker layer.

---

# Part XI — Minimal fresh-LLM prompt

Give a fresh LLM this instruction:

```text
You are building Codex-Ratchet v7 simulations. Do not validate the theory. Test hypotheses.

The primitive is finite constrained distinguishability. Start with a finite support X, finite probes P, the quotient X/~_P, and admissibility predicates. Use MSS: admit only least-assumptive survivor structures. Keep plural incomparable survivors. No density matrix, spinor, geometry, manifold, entropy-as-master, time, metric, or global identity as primitive.

Run two separate processes:
A = wide explorer/defense lawyer: generate legitimate variants.
B = strict gate/prosecutor: assume every candidate is a hack.

Build small exact sims with positives, negatives, boundary cases, controls, independent implementations, and honest status ceilings. A stronger layer enters only after a weaker layer fails to carry a required distinction and the failure is receipted.

First build: finite probe quotient. Then admissible survivors. Then order/noncommutation. Then forced-or-installed carrier comparison. Then LevOS graph quotient-readout simulations. Only then test QCA/Hopf/spinor/manifold candidates.

Never confuse quotient readout with full carrier. Never promote a result beyond the evidence. Preserve variants until gates kill them.
```

---

# Part XII — What this spec does NOT claim

This spec does not claim:

```text
the ratchet is proven
the manifold is built
density matrices are unnecessary in all cases
QCA is the final substrate
spinors are admitted
LevOS already implements this
OpenHR/OpenFinance are validated
```

It claims only:

```text
This is the explicit simulation target and discipline required to test those hypotheses without collapsing them.
```
