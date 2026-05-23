# Spinor / Twistor Entanglement Information Network Audit

Status: noncanonical formal-scout synthesis.

Date: 2026-05-22

Primary evidence:

- `system_v5/ops/formal_scouts/sim_two_root_constraint_extended_stack_validity_probe.py`
- `system_v5/ops/formal_scouts/sim_spinor_twistor_entanglement_information_network_root_gate_probe.py`
- `system_v5/ops/formal_scouts/sim_spinor_twistor_network_clifford_tensor_boundary_next_wave_probe.py`
- `system_v5/ops/formal_scouts/sim_spinor_twistor_flux_basin_binding_probe.py`
- `system_v5/ops/formal_scouts/sim_spinor_twistor_xi_cut_phi0_bridge_candidate_probe.py`
- `system_v5/ops/formal_scouts/results/two_root_constraint_extended_stack_validity_probe_results.json`
- `system_v5/ops/formal_scouts/results/spinor_twistor_entanglement_information_network_root_gate_probe_results.json`
- `system_v5/ops/formal_scouts/results/spinor_twistor_network_clifford_tensor_boundary_next_wave_probe_results.json`
- `system_v5/ops/formal_scouts/results/spinor_twistor_flux_basin_binding_probe_results.json`
- `system_v5/ops/formal_scouts/results/spinor_twistor_xi_cut_phi0_bridge_candidate_probe_results.json`

This note audits the proposed shift:

```text
tensor-network-as-substrate
  -> reject

bounded tensor contraction as tool
  -> allowed

spinor/twistor entanglement information network
  -> serious candidate carrier, not canon
```

The claim ceiling is strict: this does not admit full twistor theory, holographic spacetime, ER=EPR, a final Axis 0 bridge, or a canonical replacement for every tensor-network tool.

---

## 1. Root Stack

The thin root pair remains:

```text
F01_FINITUDE:
  finite encodings, bounded distinguishability, no completed infinities,
  decidable admissibility.

N01_NONCOMMUTATION:
  order-sensitive composition, no swap-by-default, sequence belongs to the object.
```

The current source doctrine keeps these roots narrow. The roots do not by themselves equal geometry, Axis 0, entropic monism, a finished identity/equality theory, or a finished oracle theory.

The richer layer is derived or proto-foundational pressure:

```text
entropic monism
no primitive identity
no primitive equality
no primitive center point
no primitive coordinate or metric
no primitive time or causality
no free closure / no free global objecthood
axes are discovered, not primitive
```

The safe order is:

```text
thin root pair -> extended constraint pressure -> allowed math -> realization
```

So the mistake is not "you added too many constraints." The mistake would be promoting derived constraints back into independent roots. They are gates and implications of the two roots.

---

## 2. What Was Missed Besides No Cartesian Center

Your "no Cartesian center points" was not derived by the agent until you named it. The source docs now show it belongs in a wider family. The missed constraints were:

| Constraint | Why it follows | Test pressure |
|---|---|---|
| no primitive identity | finite probes are required before `a = a` is admissible | equality must be probe-relative |
| no primitive equality | `a = b` becomes indistinguishability under a finite probe family | collisions under weak probes must be exposed by stronger probes |
| no primitive center point | a distinguished origin smuggles in a coordinate substrate | recentering must not change admissible readout |
| no primitive coordinate grid | global coordinates require precision and commutative position assumptions | invariant/relational readouts outrank index readouts |
| no primitive metric | distance is earned from admissible probes, not primitive | metric claims need finite witness |
| no primitive time | order exists algebraically before temporal narration | use precedence/composition, not before/after causality |
| no primitive causality | noncommuting order is not a causal story by default | use "coupled" / "selected" / "survived" |
| no primitive global objecthood | completed all-at-once objects smuggle infinitude and closure | use bounded regions/cuts |
| no free algebraic closure | closure and completeness need finite witness | no "all operators/all roots/all states" by default |
| no unrestricted real continuum | infinite precision is not admitted by default | finite discretization/probe precision required |

These constraints are not new roots. They are the natural discipline needed so F01 and N01 are applied consistently.

---

## 3. Bekenstein Bound Placement

The Bekenstein bound is not a third root in the current stack.

It is an extended finite-capacity constraint:

```text
log(dim H_region) <= boundary_capacity(region)
```

Interpretation:

- F01 says admissible information must be finite and finitely witnessable.
- The Bekenstein-style gate makes that finite information budget explicit for bounded regions.
- It is therefore a test constraint: a candidate carrier must fit inside a finite boundary capacity.

This matters because the model needs finite potential information. Without a capacity gate, "potential" silently becomes an unbounded Platonic reservoir, which violates F01.

Executable scout gate:

```text
node_count = 4
log_dim = node_count * log(2)
capacity_ok = node_count * log(2)
capacity_too_small = (node_count - 1) * log(2)

assert log_dim <= capacity_ok
assert not (log_dim <= capacity_too_small)
```

Result: passed in both root-stack and spinor/twistor scouts.

---

## 4. Flux And Chirality Placement

Current safe status:

```text
chirality:
  carrier/sheet structure, represented by H_L = +H_0 and H_R = -H_0.

flux:
  open derived candidate family, not admitted as root and not yet admitted as Axis 3.
```

The working carrier has real chiral sheet dynamics:

```text
rho_dot_L = -i[+H_0, rho_L]
rho_dot_R = -i[-H_0, rho_R]
```

In Bloch form:

```text
r_dot_L = +2 n x r_L
r_dot_R = -2 n x r_R
```

That is an actual sign-reversed spinor/sheet flow. It is not a metaphor.

The flux question has two possible placements:

### Option A: Flux As Geometry

Flux is part of the constraint manifold:

```text
manifold orientation / sheet transport / Berry-Hopf circulation
```

Then flux is not an axis. Engines couple to a pre-existing orientation of the carrier. This fits the idea that Type 1 and Type 2 engine basins differ even under identical local operator sequences.

### Option B: Flux As Axis 3

Flux is an engine degree of freedom:

```text
A_3 = in-flow vs out-flow
```

Then fiber/base or inner/outer would have to be derived from flux plus loop-order:

```text
chart_role = flux_bit * path_order_pair
b_6 = -b_0 * chart_role
```

This repairs the chart-A_3 vs geometric-A_3 mismatch, but it changes the meaning of A_3. It makes flux selectable at the engine layer, not a property of the carrier.

### Current Audit Verdict

Do not canonize flux as Axis 3 yet.

The safer stack is:

```text
chirality/sheet sign:
  present in carrier geometry

flux:
  open derived candidate over sheet + loop + entanglement deltas

A_3:
  remains fiber/base or chart inner/outer depending on convention,
  but the convention mismatch must be patched explicitly
```

The decisive sim is:

```text
hold tokens fixed, flip sheet sign
hold sheet sign fixed, flip loop path
flip flux globally
flip flux per stage

measure:
  basin convergence
  b_6 parity
  chiral entanglement asymmetry
  admissibility of mid-cycle T1/T2 transition
```

If per-stage flux flips break engine coherence, flux is manifold/engine-binding. If per-stage flips survive as coherent engines, flux can be axis-like.

---

## 5. Why Tensor Networks Felt Wrong

The corrected statement:

```text
Tensor networks are not globally invalid.
Tensor networks as primitive substrate are invalid.
Bounded tensor contractions as tools remain admissible.
```

The invalid version smuggles in:

1. A raw index grid.
2. A privileged contraction order or hidden global ordering.
3. A Cartesian product substrate as if it came before admissibility.
4. Free global objecthood of the full tensor.
5. Free closure under contraction/decomposition.
6. Equality of network states by array identity rather than finite probe equivalence.

The admissible version is:

```text
finite tensor contraction as a compression or computational tool
```

with required guards:

```text
finite region
finite bond dimension
finite probe family
explicit contraction order
invariance or equivariance test under relabeling/gauge changes
no raw index readout as ontology
no global all-at-once objecthood claim
```

In the spinor/twistor scout, the graveyard control is:

```text
raw_tensor_index_readout(net) changes under node relabeling
```

while the admissible spinor readout is:

```text
entropy spectrum survives relabeling
incidence magnitude spectrum survives global SU(2)
```

So the failed object is the tensor-index substrate, not the bounded tensor operation.

---

## 6. Candidate Replacement: Spinor Entanglement Information Network

The minimal candidate carrier is:

```text
node i:
  normalized spinor psi_i in C^2

density:
  rho_i = |psi_i><psi_i|

edge ij:
  finite entangled cut state |Psi_ij>

readout:
  S(rho_i|edge) = von Neumann entropy of reduced edge state
```

The scout uses a finite four-node ring:

```text
V = {0,1,2,3}
E = {(0,1),(1,2),(2,3),(3,0)}
```

Each edge state is:

```text
|Psi_ij> =
  cos(lambda_ij) |psi_i psi_j>
  + sin(lambda_ij) exp(i phase(I_ij)) |psi_i_perp psi_j_perp>
```

where:

```text
psi_perp = [-conj(psi_1), conj(psi_0)]
rho_edge = |Psi_ij><Psi_ij|
rho_i|edge = Tr_j(rho_edge)
S_ij = -Tr(rho_i|edge log rho_i|edge)
```

This gives an information-network carrier:

```text
network state = finite graph of spinors plus entanglement cut readouts
```

The primitive information is not a coordinate distance. It is a finite cut entropy plus finite incidence witnesses.

---

## 7. Twistor-Like Extension

The scout does not implement full Penrose twistor theory. It implements a local finite witness inspired by twistor incidence.

Each node carries:

```text
Z_i = (omega_i, pi_i)
omega_i in C^2
pi_i in C^2
```

The local incidence witness is:

```text
I_ij = <pi_i | omega_j> - <pi_j | omega_i>
```

Edge entanglement uses:

```text
phase(I_ij)
```

Readouts:

```text
abs(I_ij) spectrum
phase(I_ij) ordered probes
edge cut entropy spectrum
```

This matters because entropy alone can collide:

```text
same entanglement entropy
different incidence phase
```

That directly supports the no-primitive-equality doctrine. Equality is not "same entropy." It is indistinguishability under the finite probe family currently admitted.

---

## 8. Holography / ER=EPR Status

Current safe statement:

```text
Entanglement is the information carrier.
Boundary capacity is required.
Chiral spinor sheet structure is present.
ER=EPR and holographic spacetime are not admitted yet.
```

The admissible scout-level analogy is:

```text
finite region boundary capacity
  constrains
finite entanglement network information
```

This is not yet:

```text
bulk spacetime emerges from entanglement
wormhole equals Bell pair
twistor space is the final manifold
```

Those need bridge evidence:

```text
Xi : geometry/history -> rho_AB
Phi_0(rho_AB) = signed cut functional
```

The next hard bridge should test:

```text
boundary cut capacity
vs
allowed spinor-entanglement graph states
vs
basin convergence under chiral sheet sign
```

---

## 9. Actual Sim Evidence

### Scout 1: Two-Root Extended Stack Validity

Script:

```text
system_v5/ops/formal_scouts/sim_two_root_constraint_extended_stack_validity_probe.py
```

Fresh result:

```text
all_pass = true
```

What it tested:

| Gate | Meaning |
|---|---|
| z3 dependency-consistency fence (rewritten) | documents stated dependency direction with predicates and satisfiable witnesses: each derived constraint is consistent with its required roots and inconsistent without them. This is no longer the old counting fence, but it is still an assumption-consistency check, not an independent derivation from numeric witnesses |
| finite capacity | log dimension must fit finite capacity |
| no Cartesian center | origin/centroid controls fail as primitives; relational readout survives |
| Axis3/flux factorization | raw fiber/base XOR fails; chart-role factoring can repair parity |
| chiral entanglement carrier | sheet-entangled carrier is finite and admissible |

**Derived-constraint dependency verdicts (from the z3 consistency fence):**

| Derived constraint | F01 alone forces it | Requires at least one root | Verdict |
|---|---|---|---|
| Bekenstein finite-capacity | no (SAT with `F01 ∧ ¬Bekenstein`) | yes (UNSAT with `¬F01 ∧ Bekenstein`) | `consistent_with_F01_dependence_and_additional_capacity_content_under_stated_axioms` |
| no Cartesian center | no (SAT with `F01 ∧ N01 ∧ ¬no_center`) | yes, both (UNSAT with `¬N01 ∧ no_center`) | `consistent_with_F01_and_N01_dependence_and_relational_invariance_content_under_stated_axioms` |
| no global total order | no (SAT with `N01 ∧ ¬no_total_order`) | yes (UNSAT with `¬N01 ∧ no_total_order`) | `consistent_with_N01_dependence_and_order_observability_content_under_stated_axioms` |

**Important caveat (added post-3-model-audit):** The "yes (UNSAT)" entries in
the third column above follow by modus tollens from axioms hand-encoded into
the scout (`z3.Implies(bekenstein, f01)` etc. at `sim_two_root_constraint_
extended_stack_validity_probe.py:132-137`). The z3 check verifies that the
stated dependency axioms are internally consistent and that they entail the
expected SAT/UNSAT pattern. It does NOT independently derive those dependencies
from external semantics or numerical witnesses. The scout's own docstring at
lines 113-115 says this explicitly. Headline-1 framing as "semantic-entailment-
verified" was overclaim; the correct framing is "dependency-consistency-verified
under hand-encoded axioms."
| flux/chiral orientation | yes (Scout 4 z3 dependency fence: `flux requires F01∧N01 unsat`; Gemini R13 P2 clarification) | yes (UNSAT with `¬F01 ∧ flux`) | `open_candidate_dependent_on_F01_for_finite_sheet_count` |

**Negative-control section (5 expected-to-fail ablations, all fired):**

| Row | Ablation | What it shows |
|---|---|---|
| NC1 commutative chart_role | force `chart_role = +1` (no N01) | `b_6` factorization mismatches when commutative; N01 dependence of A_3 factoring is real |
| NC2 pure translation | translate the 2D point cloud by (5, -2) with no rotation | pairwise distance survives; origin radius readout breaks — confirms `no Cartesian center` bites at the readout level |
| NC3 overcapacity | 5 qubits trying to fit in a 4-qubit boundary | row marked inadmissible — gate measures capacity, not arithmetic |
| NC4 single chirality | `(α, β) = (1, 0)` only left sheet | chiral entropy → 0; entanglement load-bearing |
| NC5 label equality | `rho_a` z-aligned vs `rho_b` x-aligned (same trace, same purity) | scalar probes collide; `σ_x` commutator distinguishes — confirms probe-relative identity is needed, not label equality |

### Scout 2: Spinor/Twistor Entanglement Network Root Gate

Script:

```text
system_v5/ops/formal_scouts/sim_spinor_twistor_entanglement_information_network_root_gate_probe.py
```

Fresh result:

```text
all_pass = true
nearby_variants = 19 / 19 passed
total_cut_entropy = 1.6941989028488988
```

Positive gates:

| Gate | Result |
|---|---|
| finite_capacity_bekenstein_gate | ok capacity `sat`; too-small capacity `unsat`; roots do not force capacity `sat`; capacity-with-F01 witness `sat`; capacity requires F01 `unsat`; spinor-network-with-roots witness `sat`; spinor network requires capacity `unsat` |
| spinor_twistor_readout_global_su2_invariant | passed |
| spinor_network_relabel_invariant | passed |
| noncommuting_spinor_transport | passed |
| probe_relative_identity | passed |

Graveyard controls:

| Control | Result |
|---|---|
| cartesian_center_origin_control_rejected | passed as rejection |
| raw_tensor_index_substrate_rejected | passed as rejection |
| entanglement_only_identity_is_insufficient | passed as rejection |

Boundary rows:

| Boundary | Meaning |
|---|---|
| tensor_networks_allowed_only_as_finite_tools | tensor tools allowed; tensor substrate rejected |
| twistor_status_is_local_incidence_witness_not_full_twistor_theory | no full twistor admission |
| holographic_status_open | no ER=EPR or holographic spacetime admission |

Honest classification of the 5 positive gates: they are pass-by-construction (the readouts are designed to have the properties tested). They confirm the readouts are well-formed, not that any constraint bites. The audit weight lives in the negative controls and the tensor-network ablation below.

**Negative controls — §11 falsifiers encoded as runnable ablations, with measured gaps:**

| Row | Ablation | Measured gap | Verdict |
|---|---|---|---|
| F1 raw-tensor-index fails relabel | node relabel `[2,0,3,1]` | spinor entropy spectrum gap `0.0`; raw weighted-index gap `4.44` | spinor readout survives; tensor-index readout breaks |
| F2 edge-order scramble | permute edge list | spectrum gap `7.6e-16`; basis-sensitive edge-feature gap `0.20873807567290767` | sorted entropy spectrum is permutation-flat, but edge-identity readout moves; F2 is now explicitly readout-bound instead of overclaiming all edge geometry is killed |
| F3 product-state ablation | force `λ=0` on every edge | product total entropy `≈4.4e-16`; gap to entangled `0.88` | entanglement is load-bearing |
| F4 chirality-off ablation | `H_R = +H_0` instead of `-H_0` | chiral `‖ρ_L − ρ_R‖_F > 0`; nonchiral `= 0` | sheet sign is load-bearing |
| F5 random-S² phase | replace incidence phase by pseudorandom phase | phase gap `4.83`; spectrum gap `5.6e-16` | genuine twistor incidence is not interchangeable with a random label |
| F6 qutrit countermodel | finite-dim 3 noncommuting carrier | `dim=3` finite; `‖[a, a†]‖ = 2.45` | a `dim=3` alternative satisfies F01+N01 — roots do **not** uniquely force the C² ring carrier |
| F7 commuting-pair replacement | `(σ_x, σ_z) → (σ_z, σ_z)` | direct gap `> 0`; commuting gap `= 0` | the transport gate is detecting N01, not transformation magnitude |

7 / 7 negative controls fired in the expected direction; `audit_signal_rows = []`. F2 now carries both the invariant-spectrum result and the basis-sensitive counter-readout so the receipt no longer hides the readout dependency.

**Tensor-network ablation — three reps of edge state |Ψ_01⟩ (Schmidt rank ≤ 2):**

| Representation | Single-qubit entropy | Fidelity to full state |
|---|---|---|
| Full edge entangled state | `0.257` | `1.000` |
| Bond-1 Schmidt truncation | `≈ 0` | `0.929` |
| Bond-2 Schmidt truncation | `0.257` | `1.000` |

```text
raw 4-d index readout under qubit swap:      delta > 0 -> fails (substrate rejected)
raw 4-d index readout under local SU(2):     delta > 0 -> fails (substrate rejected)
spinor entropy spectrum under relabel:       delta < 1e-9 -> survives (carrier OK)
spinor entropy spectrum under SU(2) gauge:   delta < 1e-9 -> survives (carrier OK)
bond=1 single-qubit entropy:                 ≈ 0  -> entanglement collapsed (rank-1 forced)
bond=2 fidelity:                             ≈ 1  -> faithful tool (exact for 2-qubit state)
bond=1 fidelity strictly < bond=2 fidelity:  confirmed (compression cost is real)
```

This is the empirical content of "tensor was wrong as substrate, not as a tool": raw tensor-index ontology fails invariance under both qubit swap and local unitary; bond-2 truncation is a faithful compression tool within the rank ceiling; bond-1 demonstrably loses entanglement information; the spinor carrier's readouts survive both transforms at the network level.

### Scout 3: Clifford / Tensor Boundary / Twistor Hardening

Script:

```text
system_v5/ops/formal_scouts/sim_spinor_twistor_network_clifford_tensor_boundary_next_wave_probe.py
```

Fresh result:

```text
all_pass = true
nearby_variants = 11 / 11 passed
```

Gate-by-gate result summary (with honest classification):

| Gate | Earned result | Honest classification |
|---|---|---|
| Clifford rotor spinor transport | rotor/SU(2) agreement gap `2.2887833992611187e-16`; rotor order gap `0.16735344299025126` | **correctness verification** — Cl(3) and SU(2) are isomorphic at the group level, so the agreement to machine epsilon is expected. Clifford is a faithful representation of the same transport, not an additional load-bearing structure |
| Twistor incidence hardening | entropy gap after local twistor rephase `3.510833468576701e-16`; incidence phase gap `3.2154466655046847` | **construction check** — the phase-sensitive readout moves while entropy is phase-flat by construction; Scout 2's basis-sensitive F2 is the stronger load-bearing witness |
| Bounded tensor contraction tool | dense vs bounded entropy gap `2.220446049250313e-16` | **tool-faithful** — bounded contraction matches dense within precision; this validates the tool, not a substrate claim |
| Raw tensor-index substrate rejection | raw weighted tensor-index readout gap under relabel `5.246561341152059` | **load-bearing rejection** — substrate-as-ontology fails relabel |
| Boundary capacity graph | total edge cut entropy `1.4837807659258322`; ok capacity `sat`; too-small capacity `unsat` | **numeric capacity check plus dependency fence** — capacity comparison bites; z3 dependency rows document assumptions rather than deriving them |
| Dependency-consistency fence | roots do not force capacity `sat`; capacity-with-roots witness `sat`; capacity requires F01 `unsat`; twistor-with-roots witness `sat`; twistor requires F01+N01 `unsat`; Clifford-order-with-N01 witness `sat`; Clifford order requires N01 `unsat`; holography-with-capacity witness `sat`; holography requires capacity `unsat` | **supportive consistency content** — these are stated-dependency checks with satisfiable antecedent witnesses, not root derivations |

Negative controls:

| Control | Measured result |
|---|---|
| commuting rotor pair | same-axis rotor order gap `5.551115123125783e-17` while true noncommuting gap `0.16735344299025126` |
| nonunit rotor | norm gap `0.14676253603696043` |
| entropy-only twistor collision | entropy gap `3.510833468576701e-16`; incidence phase gap `3.2154466655046847` |
| random phase vs twistor incidence | twistor/random score gap `0.25150389609880325` |
| too-small boundary capacity | `unsat` |

Interpretation:

```text
Clifford is faithful for rotor/SU(2) transport in this scout.
It is not yet proven load-bearing beyond the SU(2) matrix form.
Twistor-like incidence is phase-sensitive beyond entropy-only equality, but this specific gate is construction-bound.
Bounded tensor contraction is admissible as a tool.
Raw tensor index substrate remains rejected.
```

### Scout 4: Flux Basin Binding Toy Probe

Script:

```text
system_v5/ops/formal_scouts/sim_spinor_twistor_flux_basin_binding_probe.py
```

Fresh result:

```text
all_pass = true
nearby_variants = 10 / 10 passed
```

Result summary with scope:

| Gate | Earned result |
|---|---|
| Global plus/minus basin split | basin distance `1.608458914112709` |
| Global plus basin coherence | alignment `0.9945941014198594`, seed spread `7.56189422206706e-05` |
| Global minus basin coherence | alignment `0.9940498646088217`, seed spread `9.213404277440997e-05` |
| Per-stage flux flip control | centroid norm `0.04384336042353561`, collapsing toward weak/neutral basin |
| Flux-erased control | centroid norm `0.07724181022798664`, no strong basin |
| Raw fiber/base XOR rejection | mismatch count `4` |
| Engine-binding vs per-stage flux axis | roots do not force flux `sat`; flux-with-roots witness `sat`; flux requires F01+N01 `unsat`; engine-binding-with-roots witness `sat`; per-stage axis under engine binding `unsat`; per-stage axis without engine binding `sat` |
| Finite flux capacity | ok capacity `sat`; too-small capacity `unsat`; capacity-with-F01 witness `sat`; capacity requires F01 `unsat`; F01 does not force capacity `sat` |
| Same-mode seed control | same-mode seed distance `7.435284766989797e-05` versus plus/minus basin distance `1.608458914112709` |

Interpretation:

```text
Flux currently looks more like a global-binding hypothesis inside this toy
basin than a free per-stage bit. This is not decisive against every Axis 3
placement; it is a scoped discriminator for the tested dynamics.
```

This does not canonize flux as a root, Axis 3, or final engine-type law. It only says the next live hypothesis should treat flux as global binding unless a stronger per-stage factoring law survives later controls.

### Scout 5: Xi / Phi0 Bridge Candidate

Script:

```text
system_v5/ops/formal_scouts/sim_spinor_twistor_xi_cut_phi0_bridge_candidate_probe.py
```

Fresh result:

```text
all_pass = true
nearby_variants = 10 / 10 passed
verdict = naive raw incidence-phase bridge rejected
```

This scout intentionally accepts a killed candidate. It tests:

```text
Xi(history/spinor-twistor graph) -> rho_AB
Phi0(rho_AB) = I_c(A -> B) = S(rho_B) - S(rho_AB)
```

Earned result:

| Readout | Value |
|---|---|
| candidate `I_c(A -> B)` | `-0.05680538956864856` |
| zero-phase control `I_c(A -> B)` | `0.14870669693351435` |
| product control `I_c(A -> B)` | `-0.6763958448758803` |
| history-erased control `I_c(A -> B)` | `-0.6931471805599453` |
| candidate minus product | `0.6195904553072318` |
| candidate minus erased | `0.6363417909912967` |
| candidate minus zero-phase | `-0.2055120865021629` |
| candidate minus random-phase | `0.2945792762910695` |
| Dependency-consistency fence | roots do not force Axis0 `sat`; cut-capacity-with-F01 witness `sat`; cut capacity requires F01 `unsat`; ER=EPR-with-roots/capacity witness `sat`; ER=EPR requires F01+N01 `unsat`; holography-with-ER=EPR/capacity witness `sat`; holography requires ER=EPR `unsat`; raw-bridge Axis0 canon rejected `unsat` because the empirical raw bridge gate was killed |

Bridge-mode sweep:

| Mode | `I_c(A -> B)` | Status |
|---|---:|---|
| raw incidence phase | `-0.05680538956864856` | rejected |
| absolute incidence phase | `0.142201` | near tie, still below zero-phase control |
| oriented phase class | `-0.024039` | rejected |
| incidence magnitude lambda | `0.076142` | below zero-phase control |
| inverse magnitude lambda | `0.137683` | near tie, still below zero-phase control |
| history-coupled edge weight | `-0.023933` | rejected |

Interpretation:

```text
The finite cut-state construction is healthy and rejects product/history-erased
controls, but no tested phase/magnitude/history bridge mode beat the zero-phase
control. Raw phase(I_ij) is killed; the broader bridge family remains open.
```

This is a useful kill. It narrows the bridge search:

```text
Do not use raw twistor incidence phase as Phi0 bridge logic.
Try incidence magnitude, phase orientation classes, optimized finite probe
families, or history-coupled edge weights next.
```

---

## 10. Worked Constraint Mapping

| Root or derived gate | Tensor-substrate risk | Spinor/twistor network response |
|---|---|---|
| F01 finitude | global high-rank objecthood and free bond growth | finite node count, finite Hilbert dimension, capacity gate |
| N01 noncommutation | contraction treated as swappable bookkeeping | noncommuting SU(2) spinor transport tested |
| no center | raw origin / centroid sneaks in | relational readout survives recentering |
| no coordinate grid | index order becomes ontology | relabel-invariant entropy spectrum |
| no equality | array equality treated as identity | entropy collision exposed by incidence phase probe |
| no free closure | arbitrary contraction/decomposition assumed | finite operation set and claim ceiling |
| entropic carrier | distance or tensor norm becomes primitive | cut entropy is load-bearing readout |
| Bekenstein bound | unbounded potential state space | finite boundary capacity gate |

---

## 11. Advisory Audit Falsifiers

A separate bounded audit lane agreed with the local executable result: tensor networks are admissible as bounded compression/representation tools, but not as primitive substrate, canonical manifold, or proof-forcing layer.

Hard falsifiers carried forward:

| Candidate claim | Falsifier |
|---|---|
| tensor network is load-bearing substrate | exact dense small-state evolution and MPS/PEPS compression give the same admitted readouts |
| tensor geometry is meaningful | bond-dimension clamp, static contraction tree, topology scramble, or path/order erasure preserves the claimed basin or `Phi_0` separation |
| spinor entanglement network is load-bearing | product, maximally mixed, single-chirality, commuting-channel, or order-erased controls match the candidate |
| chiral spinor structure is load-bearing | L/R Weyl histories collapse to a scalar chirality proxy without loss |
| twistor incidence is load-bearing | incidence can be replaced by an `S^2` label or random projection with the same survivor/coherent-information readout |
| operator-axis manifold promotion is admissible | runtime rows omit ordered token, exact operator, family, Axis 6 side/precedence/sign, channel, and readout |
| roots force a unique tensor/spinor/twistor stack | a countermodel satisfies F01/N01 without that exact stack |

These falsifiers matter because they stop the new spinor/twistor language from becoming another unearned substrate.

---

## 12. Valid Stack After Audit

The current valid stack is:

```text
Root pair:
  F01_FINITUDE
  N01_NONCOMMUTATION

Derived/extended constraints:
  no primitive identity
  no primitive equality
  no primitive center
  no primitive coordinates/metric
  no primitive time/causality
  no free closure/global objecthood
  Bekenstein-style finite capacity

Carrier:
  finite spinor sheets in C^2
  chiral sign H_L = +H_0, H_R = -H_0
  entangled edge cut states
  twistor-like incidence witnesses

Manifold:
  admissible constraint surface over spinor/Hopf/sheet dynamics

Open derived flux:
  candidate observable over sheet/path/loop/cut deltas

Operators/axes:
  existing A0-A6 layer remains separate from carrier tests

Rejected substrate:
  Cartesian center-first coordinate grids
  raw tensor-index ontology
  primitive equality by array identity

Allowed tools:
  PyTorch complex tensors
  bounded tensor contraction
  z3 dependency-consistency gates (supportive, not derivational)
  future Clifford/SymPy/geomstats/e3nn/TopoNetX/GUDHI/PyG as load-bearing rows when matched to claims
```

---

## 13. Next Sim Sequence

The next work should be micro-first, not a broad queue launch.

1. Clifford spinor transport receipt

```text
Claim:
  spinor/rotor transport is better expressed by Clifford/geometric algebra
  than raw tensor indices for this carrier.

Test:
  same finite spinor network, compare SU(2)/rotor invariants and
  noncommuting transport gap.

Status:
  initial v5 formal-scout receipt passed in
  sim_spinor_twistor_network_clifford_tensor_boundary_next_wave_probe.py.
```

2. Twistor incidence hardening

```text
Claim:
  I_ij = <pi_i|omega_j> - <pi_j|omega_i> is a useful finite incidence probe.

Test:
  phase/magnitude stability under allowed gauge;
  sensitivity under forbidden primitive-index transforms.

Status:
  initial incidence-hardening receipt passed; full projective twistor theory
  still not admitted.
```

3. Boundary capacity vs entanglement graph

```text
Claim:
  Bekenstein-style capacity bounds allowed potential information.

Test:
  reject graphs whose entropy/cut budget exceeds boundary capacity.

Status:
  initial boundary-capacity graph receipt passed; needs scaling and bridge
  coupling next.
```

4. Tensor network ablation

```text
Claim:
  bounded tensor contraction is tool-admissible, but tensor-index substrate is not.

Test:
  same network represented as raw tensor array, MPS-style bounded tool,
  and spinor incidence graph. Compare invariant readouts under relabel/gauge.

Status:
  initial bounded tensor contraction vs raw tensor-index ablation passed.
  MPS/PEPS-specific ablation remains next.
```

5. Flux basin scout

```text
Claim:
  flux may be manifold-level or engine-level, but not both without a factoring law.

Test:
  fixed token chart; flip sheet sign, loop path, and global/per-stage flux.
  Measure attractor basins and b_6 parity.

Status:
  initial global-binding scout passed; per-stage flux failed the coherence
  gate under engine-binding assumptions.
```

6. Xi bridge scout

```text
Claim:
  Axis 0 must eventually read a bipartite cut state.

Test:
  Xi maps spinor-network history to rho_AB.
  Phi_0 candidates: coherent information, conditional entropy, mutual information.

Status:
  first raw phase(I_ij) bridge was killed. The cut-state construction is valid,
  but raw incidence phase is not the admitted bridge.
```

---

## 14. Bottom Line

The stronger position is:

```text
The primitive carrier should be finite spinor-entanglement information,
with twistor-like incidence as a probe family and Bekenstein-style capacity
as a derived finite-information gate.
```

The forbidden position is:

```text
The world is a raw tensor network over a hidden Cartesian index substrate.
```

The allowed engineering position is:

```text
Use tensor operations as bounded finite tools when they preserve the admitted
relational, finite, noncommuting readouts.
```

That resolves the tensor objection without throwing away useful tensor methods.

---

## 15. What Was Actually Falsified (negative-control verdicts)

### 15.0.0 Round-7-prep CONFOUND FINDING: Lambda-magnitude mismatch in `incidence_derived` vs `random_seeded`

**This is a load-bearing scope-specific finding for the bridge probe.** It invalidates parts of B.1 and the Ising "admission" but does not rank above root-stack, carrier, or capacity findings across the full audit (Grok R8 P1 #1 — earlier "most consequential" framing was an overclaim).

The bridge probe has had an undetected confound from day 1 (R1 and earlier). The `incidence_derived` and `random_seeded` modes used DIFFERENT lambda (entangler-strength) distributions:

- `incidence_derived`: `lam = 0.20 + 0.40·|I_ij|`. Empirically (100 graphs × 4 edges Haar sample): **mean 0.576, range [0.22, 0.95]**.
- `random_seeded`: `lam = U[0.20, 0.60]`. **mean 0.400, range [0.20, 0.60]**.
- **Mean difference: +0.176.** Incidence states received systematically stronger entangling rotations than random states.

This confound was masked under XY (XX+YY) and Heisenberg (XX+YY+ZZ) entanglers because the phi (angle) parameter dominated state structure. It became visible under Ising (ZZ-only) where lam directly controls coupling strength without phase scrambling.

**Empirical impact of the confound** (depolarizing/interleaved/log_negativity pure half, K=30):

| entangler | z (vs random_seeded) | z (vs lambda_matched_random_phi) |
|---|---|---|
| Ising | +7.16 (admits) | **−0.10 (no signal)** |
| XY | +1.36 | −0.49 |
| Heisenberg | −2.64 (sign-reversal claim) | **+0.56 (no signal)** |
| random_unitary | −0.09 | −0.31 |

The lambda-matched control (`mode = "lambda_matched_random_phi"`: same lam = 0.20+0.40·|I_ij| as inc, but uniform random phi) collapses signal across all entangler families. The Ising "17-cell Bonferroni admission" (after R9 partition-dedup; was naively 20/36 before, then 17/33; see §15.0 detail below) collapses to small |z| < 0.6 under matched control across non-degenerate cells, consistent with lambda magnitude as the dominant driver. Some Ising I_ABCD cells have machine-epsilon `lammatch_SE` and are degenerate-by-construction, not independent confound evidence. The B.1 sign-reversal claim (XY positive, Heisenberg negative) was confounded at K=30; the residual "p ≈ 0.021 partially surviving" was further falsified at K=300 (R10-prep) — see §15.0 detail below.

**Updated verdict:** The bridge probe shows **no detectable Φ_0 signal under matched-lambda controls** across any of {XY, Heisenberg, Ising, random_unitary} × 5 functionals × 4 cells. The prior 7-round "no signal" verdict survives the confound fix (still no signal), but for a **different and weaker reason**: prior rounds were comparing inc to a weakly-entangling control; the matched control shows inc and lambda-matched-random are statistically indistinguishable under the tested readouts.

**What this rescues from prior rounds:**
- The 7-round "no admission" verdict survives (in fact strengthens — was masked by confound, now consistent across matched and unmatched comparisons).
- The constraint-admissibility framing (F01+N01 as roots) is unaffected.
- The negative controls (NC1-NC3, F1-F7) still hold; they tested different invariances.

**What this kills from prior rounds:**
- B.1 sign-reversal claim: **SIGN-REVERSAL FALSIFIED at K=300 (R10-prep power confirmation)**; a smaller same-sign magnitude residual between XY and Heisenberg persists under matched control at K=300 and is power-limited (Opus R11 C1 — the "FALSIFIED" header refers to the sign-reversal claim specifically, not to all entangler-basis effects). Prior framing said "partially confounded, partially survives, p ≈ 0.021 one-sided" based on K=30 evidence. Running the matched-control test at K=300 (10× the K=30 sample size) on XY and Heisenberg shows: **2/30 pure-half flips, p ≈ 1.0** (and 3/30 noisy-half flips, also p ≈ 1.0). At K=300 the XY and Heisenberg lambda-matched-control means have **the SAME sign** in 28/30 cells — XY values are slightly larger in magnitude on I_c/LN/MI and slightly more negative on M_2/M_3, but the entangler choice does NOT flip the sign once SE shrinks below the bias floor. The residual B.1 SIGN-REVERSAL effect was K=30 sampling noise where individual seed-batches happened to flip sign. (Receipts: `system_v5/ops/formal_scouts/results/spinor_twistor_xi_cut_phi0_bridge_K300_power_confirm.json` — generated by `/tmp/k300_power_confirm.py`, calls existing `rng_ensemble_bridge_gate(num_seeds=300, entangler_family="xy"/"heisenberg")` from the bridge probe.) **The K=30 caveat the audit loop documented all along ("median K_required ≈ 800-1000 for the residual effect at 80% power") was load-bearing. At K=300, the residual signal is dead, not just weak.**

  **Historical retraction trail for B.1:**
  - R5: "16/16 paired sign flips, p ≈ 1.5e-5" (claimed at K=30 with 2 functionals × 2 partitions × 2 noise = 16 paired comparisons; over-counted because not all 16 actually flipped).
  - R6: corrected arithmetic → 13/16 combined, p ≈ 0.011 (still K=30, still vs unmatched random_seeded).
  - R7-prep: lambda confound discovered → "10/12 pure-half flips under matched, p ≈ 0.019" on the I_c+LN+MI subset.
  - R8/R9: recomputed over full 20-cell superset → "15/20 pure-half flips under matched, p ≈ 0.021 one-sided" (Opus R8 A3 independently verified).
  - **R10-prep: K=300 power confirmation. Apples-to-apples on the original K=30 20-cell subset (2 noise × 2 partition × 5 functional, depolarizing + z_dephasing only): 2/20 pure flips (p ≈ 1.0), 1/20 noisy flips (p ≈ 1.0) — was 15/20 + 11/20 at K=30. On the expanded 30-cell K=300 grid (3 noise channels including amplitude_damping): 2/30 pure flips, 3/30 noisy flips, both p ≈ 1.0.** The cell grid expansion (20 → 30) from adding `amplitude_damping` is noted explicitly per Opus R11 B1 — the falsification holds on both the original 20-cell subset (apples-to-apples) and the expanded 30-cell superset, so the K-scaling conclusion is unaffected by the scope change. Four progressively-more-honest weakening rounds (R5 → R6 → R7-prep → R8/R9), then definitive falsification at K=300. The R8/R9 multi-pair Bonferroni discussion ("1-pair vs 3-pair vs 6-pair") is now moot — at K=300 the sign-flip count is below chance under any denominator on any cell grid. The K=30 framing was sampling noise; the historical "p ≈ 0.021 partially survives" claim is retracted.
- Round-5 "elevated finding" → fully retracted; **no entangler-basis bias-sign-reversal signal survives proper K=300 power** under matched control.
- All point-estimate admissions under lambda-matched comparison are 0/20 across all entangler families.
- Power caveat (Grok R8 P2): "no signal under matched control" is more honestly "no detectable signal at K=30 under matched control; small undetected effects possible below the SE floor."

**Why this took 7 rounds to find:** the audit loop checked statistical power, multiple-testing correction, RNG independence, analytic correctness, vocabulary, but never explicitly compared inc vs rand under MATCHED entangler parameters. The "random_seeded" control was treated as if it were a proper null distribution; it was actually a null distribution with a different mean entangler strength than incidence-derived. Adding the Ising entangler (which doesn't mix phi) exposed this in a single run.

**Seed-pairing convention for lambda_matched_random_phi** (Opus R8 C2 clarification): the `lambda_matched_random_phi` mode uses `lam = 0.20 + 0.40·|I_ij|` (graph-paired with `incidence_derived` — both modes get the SAME lam value from the SAME graph edge) and draws φ uniformly with `rng_seed = seed_nc + 2`. The original `random_seeded` mode uses `rng_seed = seed_nc + 1`. Both share `seed_nc` (graph seed), so the underlying spinor/twistor graph IS paired across all three modes (inc, rand, lammatch). lam is paired between inc and lammatch (both derived from |I_ij|) but differs from rand (which uses a uniform draw). φ is paired between rand and lammatch only insofar as both use deterministic torch.Generator draws from related seeds; for practical purposes treat them as independent. Net effect: the matched comparison cleanly isolates the φ-structure contribution (everything else paired) and the lam-magnitude contribution (only inc-vs-rand differs in lam).

**Round-7-prep status:** CRITICAL CONFOUND identified; one-line fix to add `lambda_matched_random_phi` mode landed; K=30 reran across 4 entangler families with both unmatched and matched controls; results in `spinor_twistor_xi_cut_phi0_bridge_candidate_probe_results.json` under `pure_z_vs_lammatch` / `noisy_z_vs_lammatch` fields per cell.

**Round-8-prep additions** (post-R7-audit, pre-R8-audit triple):
- I(A:B:C:D) multipartite information added as 6th functional (closes Grok R6 C.1 + Opus R6 P1.2 "multipartite information named-but-unimplemented" gap with structurally different readout from M_2/M_3 which are correlated with I_c). **Important caveat (Opus R9 B1+B2):** I_ABCD on 4 single-qubit marginals is **partition-independent by construction** (block 0,1|2,3 and interleaved 0,2|1,3 give bit-identical values since the sum over single-qubit entropies doesn't depend on the bipartition choice). Under Ising entangler specifically, `lammatch_SE` for I_ABCD is at machine epsilon (~1.7e-16) because ZZ preserves single-qubit populations and matched lam values, so I_ABCD becomes a deterministic function of lambdas alone — **degenerate-by-construction on Ising**. The "I_ABCD doesn't escape the confound" framing holds on XY/Heisenberg/random_unitary but is vacuous on Ising (cannot escape any confound there even in principle). I_ABCD is correctly characterized as a control diagnostic on Ising, not an independent multipartite probe there.
- amplitude_damping channel added as 3rd noise channel (closes Grok R6 C.2 noise-model gap; non-unital, fixed point |0⟩⟨0|, distinct from dephasing/depolarizing). Same Ising-population-preservation degeneracy: amplitude damping rows under Ising have `lammatch_SE` at machine epsilon for the lam-determined functionals. Amplitude damping is genuinely informative on XY/Heisenberg/random_unitary; Ising rows add no information beyond what dephasing already showed (Opus R9 C1).
- n_cells_screened = **33 per entangler family** after Round-9 partition-dedup fix (Opus R9 B1: was naively counted as 36 = 6 functionals × 2 partitions × 3 channels; corrected to 33 = 5 partition-dependent functionals × 2 partitions × 3 channels + 1 partition-independent functional × 1 partition × 3 channels). z_FWE = **2.9646** (was 2.991 at the inflated count; 2.807 at R7-prep with n_cells=20; 2.638 at R6; 2.498 at R5). Under Bonferroni at z=2.965: 0/33 admitted in xy/heisenberg/random_unitary; **17/33 in Ising** (was 20/36, partition-duplicates collapsed) — all 17 confounded under lammatch control.

**Round-8 audit triple (this audit lane):**
- Grok R8: 2 P1 ("most consequential" overclaim, claimed 10/12 cherry-picking from 20-cell space — but Opus's independent 20-cell re-derivation shows 15/20, p=0.021 one-sided, refuting the cherry-pick claim).
- Opus R8: 2 P1 (sidedness annotation — p=0.019 was one-sided not two-sided; silent §15.0 Ising-admission retraction needed). Confirmed §15.0.0 confound code, ran independent 20-cell test, confirmed 15/20 result.
- Gemini R8: 1 P1 (same cherry-pick selection-bias as Grok, refuted by Opus's 20-cell test). Disagreement with Grok: Gemini says "most consequential" framing IS justified.

**R8 fixes landed in this commit:**
- "Most consequential" → "load-bearing scope-specific" (Grok P1).
- Sidedness annotation added (one-sided p ≈ 0.021, two-sided p ≈ 0.041) on B.1 residual; pre-specification of XY-vs-Heisenberg sign-reversal in R5 documented (Opus P1 B1).
- §15.0 Ising-admission paragraph retracted with explicit RETRACTED tag pointing to §15.0.0 (Opus P1 B3).
- B.1 recomputed over full 20-cell set, per-functional breakdown reported (closes cherry-pick concern — both audits' P1 #1).

**Round-9 audit must verify:** (1) sidedness annotations are present; (2) §15.0 Ising retraction is explicit; (3) 15/20 number and p=0.021 / 0.041 reconcile with JSON; (4) "most consequential" language is gone; (5) I_ABCD / amplitude_damping additions reconcile with code.

**Round-10-prep additions** (after R9 audit returned 2 P1 + 3 P2 from Opus):
- Opus R9 B1: partition-redundancy in n_cells fixed by adding `PARTITION_INDEPENDENT_FUNCTIONALS = {"I_ABCD"}` constant + dedupe loop. n_cells dropped 36 → 33; z_FWE dropped 2.991 → 2.9646. Ising Bonferroni admits dropped 20 → 17 (partition-duplicate I_ABCD entries collapsed).
- Opus R9 B2: Ising I_ABCD degeneracy framing added — under Ising entangler, lammatch_SE for I_ABCD is at machine epsilon (~1.7e-16) because ZZ preserves single-qubit populations. The "I_ABCD doesn't escape confound" claim is now correctly scoped to XY/Heisenberg/random_unitary (vacuous on Ising).
- Opus R9 C1-C3 P2 fixes: amplitude_damping Ising degeneracy noted; "subset not selection-biased" inference replaced with pre-specification defense; multi-pair Bonferroni denominator corrected from 6 to 3 with arithmetic fixed.
- **K=300 power confirmation (this commit, addresses Grok R10 main P2):** standalone script `/tmp/k300_power_confirm.py` calls `rng_ensemble_bridge_gate(num_seeds=300, entangler_family="xy" / "heisenberg")` on the full 30-cell (3 noise × 2 partition × 5 partition-dependent functional) grid under lambda-matched control. Result: **2/30 pure-half flips, 3/30 noisy-half flips, p ≈ 1.0 in both cases.** The residual B.1 sign-reversal effect FALSIFIED at K=300. Receipt: `spinor_twistor_xi_cut_phi0_bridge_K300_power_confirm.json`. Total runtime: 25s.

**Round-11 audit must verify:** (1) K=300 receipt exists and contains 2/30 + 3/30 flip counts; (2) §15.0.0 B.1 retraction trail is honest (R5 → R6 → R8/R9 → R10 falsification); (3) the multi-pair Bonferroni paragraph has been moot'd out; (4) no new overclaim introduced by the falsification framing.

**Round-12 audit triple verdict:**
- Grok R12: 0 P1, 0 P2 — CLEAN (4th consecutive Grok-clean).
- Opus R12: 0 P1, 2 P2 (optional polish: quote magnitude residual K_required; archive R5→R10 stratum trail) — CLEAN. **First Opus-clean verdict in the 12-round loop.** Opus verified the apples-to-apples 2/20 + 1/20 reconciles bit-for-bit with the K=300 JSON details[] array.
- Gemini R12: 1 P1 claim (alleging 1/30 noisy flips not 3/30), **REFUTED by cold verification**. Gemini missed the 2 amplitude_damping flips (amplitude_damping/interleaved/M_2 with means -0.0020 vs +0.0055; amplitude_damping/interleaved/M_3 with means -0.0013 vs +0.0073). The actual 3 noisy flips are: depolarizing/block/M_3, amplitude_damping/interleaved/M_2, amplitude_damping/interleaved/M_3 — verified by independent cold count. Receipt's `noisy_flips_under_matched: 3` is correct. Gemini's R12 P1 is a counting error, not a real audit finding.

**Round-13 audit must verify:** (1) the Gemini R12 miscount is correctly documented as Gemini-side error (not a real inconsistency); (2) the 3/30 noisy-flip count holds under independent cold verification; (3) no new claim introduced by the R12-fix documentation. R13 is the second-clean confirmation needed for the two-consecutive-clean fixed-point criterion (with R12 being the first).

---

### 15.0 Executive Summary (current verdict, post-Round-5 cross-audit)

**Single source of truth for the Φ_0 bridge question — all retracted strata kept below as audit trail.**

- **Roots stay F01_FINITUDE + N01_NONCOMMUTATION** — semantic-entailment-verified retracted; framing is now "dependency-consistency under hand-encoded axioms."
- **7 incidence-derived Φ_0 candidates tested** across two Xi families (edge-mixture, joint-graph). NOT 10 — earlier count included controls.
- **K=30 Haar ensemble × 2 partitions × 2 functionals × 2 noise channels × 2 entanglers = 8 independent cells × 2 paired entangler readouts on the same Haar draws** (per Opus Round-5 A.2 — XY and Heisenberg share `seed_idx`, so the two ensembles are paired, not independent. This sharpens the statistical strength of the bias-sign-reversal finding below).
- **Admission verdict under Bonferroni-corrected SE-aware criterion (z_FWE = 2.638 for FWE α=0.05/12 after Round-6 MI addition; previously 2.498 for n_cells=8): 0/12 cells admit incidence in either entangler family.** FDR (Benjamini-Hochberg) at α=0.05 also rejects all cells at K=30; the choice of correction does not change the verdict.
- **Round-7-prep readout-family + entangler-family extension:** added (a) Schmidt-spectrum moments `M_2 = Tr(ρ_A^2)`, `M_3 = Tr(ρ_A^3)` as structurally-different readouts from entropy-based functionals; (b) per-cell quantum relative entropy `D(ρ_A_inc || ρ_A_rand)` as a per-cell scalar (FEP-aligned, not inc-rand difference); (c) `random_unitary` as a third entangler family, NEGATIVE CONTROL for the B.1 sign-reversal claim. K=30 reran with all 3 entanglers × 5 functionals × 4 cells = 60 cells across the three entangler ensembles. **Key new results:**
  - **Random-unitary entangler shows no detectable signal at K=30** (0 point-estimate admits, all |z| < 1.5). **Consistent with the B.1 sign-reversal being basis-structure-specific at K=30** (Opus R7 B2 — earlier "confirms" framing was an overclaim; K=30 power on the negative control is the same low-power regime documented for the positive cells, so a small generic-mixing bias of magnitude ≤ 0.05 could be present and undetectable here). K=1000 random_unitary run would tighten this; current evidence is suggestive, not confirmatory.
  - **Schmidt moments M_2, M_3 flip sign anti-correlated** with I_c/MI/LN: XY pure interleaved/M_2 z=-2.75, Heisenberg pure interleaved/M_2 z=+1.77 (opposite direction, same flip pattern). **Opus R7 B1 correctly noted that this is NOT independent evidence:** for qubit-rank reductions M_2 = Tr(ρ²) is a monotone function of S(ρ) (purity = 1 - 2p(1-p), entropy is -p log p - (1-p) log(1-p)); for 2-qubit reductions of pure 4-qubit states (the pure half), M_2 and S have correlated but not deterministic relationship. Empirically M_2 z-scores differ from I_c z-scores (e.g., XY/depolarizing/block: I_c z=+1.68, M_2 z=-1.84) — so M_2/M_3 add partial independent statistical evidence but cannot be counted as a structurally different readout family for the Grok C.1 gap. Demoted from "extends to spectrum-moment readouts" to "re-expresses I_c finding with weakly-correlated functional; not a structurally independent admission test."
  - **Strongest cell across all entanglers**: XY pure `depolarizing/interleaved/M_3`, z = -2.92 (i.e., M_3 _decreases_ under incidence-derived edges by 2.92σ vs random-seeded). Just under one-tailed Bonferroni z_FWE = 2.807 for n_cells=20. A two-sided test would clear.
  - **Quantum relative entropy** `D(ρ_inc || ρ_rand)`: ranges 0.4-0.9 across cells; asymmetry `D(i||r) - D(r||i)` ≈ 0 ± 0.04 across all cells. **Asymmetry threshold ±0.04 is at the K=30 noise floor** (Opus R7 C3 — should be framed as power-limited "no detectable asymmetry at K=30," not a result that asymmetry is genuinely zero). Random-unitary distances notably smaller (~0.4) than structured entanglers (~0.5-0.9); also power-limited but consistent with basis-bias-specific story.
  - Bonferroni z_FWE updated 2.498 (R5, n_cells=8) → 2.638 (R6, n_cells=12 with MI) → 2.807 (R7-prep, n_cells=20 with M_2 M_3 added) → 2.991 (R8-prep with I_ABCD+amp damp, naive count 36, later corrected) → **2.9646 (R9 partition-dedup fix, n_cells=33)**. Still 0/33 admitted under Bonferroni in xy/heisenberg/random_unitary ensembles. **Ising entangler admission (RETRACTED 2026-05-22 post-R8-audit per Opus R8 B3):** prior text said "10/20 cells under Bonferroni AND FDR, strongest z=+7.16; controls needed." Under R7-prep lambda_matched_random_phi control, all Ising admission cells collapse to small |z| < 0.6, consistent with lambda-magnitude as the dominant driver (Opus R10 B2 — earlier "100% the confound" framing was a point-estimate overclaim that ignored K=30 SE; some cells with I_ABCD under Ising have machine-epsilon `lammatch_SE` and are degenerate by construction, not independent confound evidence). R9 partition-dedup fix reduced Ising Bonferroni admits from 20/36 to **17/33** as I_ABCD partition-duplicates collapsed. Ising admission is **fully retracted** as load-bearing geometric Φ_0 signal; it remains a useful confound diagnostic on the non-degenerate functionals.
- **Round-6 readout-family extension (preserved as audit trail):** mutual information `I(A:B) = S(ρ_A) + S(ρ_B) − S(ρ_AB)` added as a third Φ_0 candidate (Opus R6 P1.2, Grok R6 P1 readout-family gap, and FEP design lane share this move). MI also fails to admit in all 12 cells per entangler under Bonferroni. **Caveat on independence:** for pure bipartite states `S(ρ_AB) = 0`, so `MI_pure = 2·I_c_pure` is determined by I_c on the pure half. MI noisy IS independent of I_c noisy (when `S(ρ_AB) > 0`). Strongest XY MI z = 2.09 (depolarizing/interleaved/I_A_B, mean +0.1654, SE 0.0791), under z_FWE=2.638. Strongest noisy XY MI cell: depolarizing/interleaved, mean +0.0381, SE 0.0155, z=2.46 — also under threshold but close. **Point-estimate admission count rose 1 → 6** with MI added (z_dephasing+depolarizing on block partition; depolarizing on interleaved), all because MI scales ~2× I_c on pure states; correction-aware admission (Bonferroni z_FWE=2.638) still rejects all 6. **Reader caution:** point-estimate count is misleading without correction. MI is still a bipartite-cut readout, not a structurally different readout family. Grok R6 C.1 readout-family gap is only partially closed (1 of 4 named alt-readouts implemented; entanglement-spectrum statistics, relative-entropy distance, and projective cross-ratios remain unimplemented).
- **ROUND-5 ELEVATED FINDING (CORRECTED Round-6): entangler-basis bias-sign-reversal** (Opus Round-5 B.1; arithmetic corrected per Opus Round-6 A.4). Under XY all 8 paired cell **pure** means are POSITIVE (+0.004 to +0.083); under Heisenberg all 8 paired cell pure means are NEGATIVE (-0.025 to -0.142). **8/8 paired pure-half sign flips on identical Haar draws has binomial p ≈ 3.9e-3 under the null "entangler choice does not affect bias direction."** Combined pure+noisy is 13/16 flips (3 noisy cells — `depolarizing/block/I_c`, `depolarizing/interleaved/I_c`, `z_dephasing/interleaved/I_c` — do NOT flip), binomial p ≈ 0.011. (RETRACTED: Round-5 reported "16/16 ... p ≈ 1.5e-5"; that number is 0.5^16, which holds only if all 16 flipped. Verified cold against `spinor_twistor_xi_cut_phi0_bridge_candidate_probe_results.json` `per_cell_statistics` `pure_inc_minus_rand.mean` / `noisy_inc_minus_rand.mean`. The qualitative direction survives; the headline p-value was overstated by ~250-700×.) **Reframing (survives, weaker confidence margin):** the pure-half bias sign of (incidence − random) co-varies with the entangler basis choice on identical Haar draws. The cut-state readout family (I_c, LN under XY or Heisenberg) registers entangler-basis bias more strongly than incidence content **on the pure half**; on the noisy half the dependency is partial (5/8). The "no signal in this readout family" verdict survives. Strategic response: **alternative readouts before higher K** is still the right call directionally, but the dismissal of K=1000 as "would not discriminate" was unverified — at the strongest XY cell (`depolarizing/interleaved/I_c`, mean +0.0827, SE ≈ 0.040, current z = 2.09), shrinking SE by √(1000/30) ≈ 5.77× would lift z to ≈ 12, well past FWE z = 2.498. So K=1000 **might** discriminate at the strongest cell; this is a prediction, not a tested claim.
- **K=30 is severely underpowered** for a 0.02 effect at observed std ≈ 0.04-0.07: K_required ≈ 200-1000.
- **Analytic correctness baselines pass** — Bell, GHZ4 (block + interleaved), 2-qubit product, 4-qubit product all match analytic S and LN values to machine precision. The "simulation bug" alternative explanation (d) is closed.

**Strategic call (Round 6, REVISED from Round 5):**
- **Priority 1 (alt-readouts) — PARTIAL CLOSURE after Round 6:** Bipartite-cut mutual information `I(A:B)` added and tested; it also fails to admit. Still UNIMPLEMENTED: entanglement spectrum statistics (eigenvalue moments of `ρ_A`), multipartite information `I(A:B:C:D)`, relative-entropy distance `S(ρ_geometry || ρ_random)`, projective cross-ratios on π-ω pairs. The remaining four are genuinely different readout families (not just different functionals on the same bipartite cut). Until at least one structurally-different family is tested, the "no signal in this readout family" verdict is bipartite-cut-conditioned.
- **Priority 2 (higher K) — REVISED:** Round-6 audit (Opus B.2) noted that `K=1000` on the strongest XY cell (depolarizing/interleaved, current z=2.09) would shrink SE by √(1000/30) ≈ 5.77×, plausibly lifting z to ≈ 12 — well past z_FWE = 2.638. Previous Round-5 framing ("K=1000 would not discriminate") was unverified prediction, not tested. K=1000 might discriminate at the strongest cell; this is now a candidate experiment, not a foreclosed option.
- **Items 5 (scale N=6, N=8) and 6 (alt topology K_4, star, path) remain `terminal-deferred`.** Rationale survives directionally — readout family is more likely the binding constraint than scale or topology — but the confidence margin from B.1 is weaker after the p-value correction (3.9e-3 instead of 1.5e-5). If at least one structurally-different alt-readout family fails AND K=1000 on the strongest cell fails, then re-open 5 and 6.

The detailed audit trail below preserves the per-round retraction layers. Each row marked "(RETRACTED post-Round-N-audit)" should be read as audit history, not current claims.

**Convergence status (post-Round-6, REVISED):** Round-5 audit reported "0 CRITICAL findings" but **missed a 2.5-OOM arithmetic error** in the B.1 promotion above (Opus Round-6 A.4). Round-5 was a near-miss audit, not a fixed point. The same failure mode the loop has caught every round (count/p inflation) appeared in the most recent layer. Round-6 returns: 1 P1 (this arithmetic correction), 1 P1 (Priority 1 alt-readouts named but unimplemented after 6 rounds), 1 P1 (constants-table wired through one site, ten still raw literals), 4 P2, 3 P3. **Two-consecutive-clean-rounds criterion NOT met.**

**Round-6 fix lane (this commit):**
- P1a corrected p-values in §15.0 (8/8 pure → 3.9e-3; 13/16 combined → 0.011; retraction of 1.5e-5 claim documented; "K=1000 wouldn't discriminate" walked back to "might at z=12 — prediction, not tested").
- P1b wired ADMISSION_THRESHOLD / PRODUCT_GAP_THRESHOLD / NONTRIVIAL_PURE_THRESHOLD / BEATS_PRODUCT_MARGIN / NC1-NC3 / HAAR_NUM_SEEDS through the 10 call sites previously holding raw literals.
- P1c added mutual information `I(A:B)` as a third Φ_0 candidate; K=30 ensemble reran with 12 cells per entangler (was 8); Bonferroni z_FWE updated 2.498 → 2.638 automatically via dynamic `n_cells`. MI also fails (verdict survives across 3 functionals on bipartite cuts). Caveat: MI mathematically equals 2·I_c on pure states (does not add independent evidence on pure half); MI on noisy half IS independent.

**Audit-cycle discipline addendum (Opus R6 P2.5):** One clean round (zero P1) is necessary but not sufficient for convergence. Quantitative claims (counts, p-values, threshold-z values) must receive a separate arithmetic-check pass independent of qualitative review. Round-5 missed B.1's p-value error precisely because the qualitative reframing absorbed audit attention. Round-7 readers must explicitly check: (a) does each numerical claim re-derive from the JSON receipts? (b) does each named threshold reference the same constant the table promises? (c) is "all cells flipped" actually all-cell, or some-subset?

**Round-7 must verify:** (1) corrected p-values land in §15.0 without regression; (2) the MI ensemble cells are present in JSON `per_cell_statistics` under `I_A_B`; (3) all 10 raw-literal call sites now reference named constants; (4) this audit-cycle-discipline note is present and unmoved; (5) the "K=1000 might discriminate" reframing has not collapsed back into either direction.

---


This section answers "what would have caused the audit to surface a blocker?" It lists what the ablation suite actually killed or left open.

**Falsified by ablation (load-bearing distinction confirmed):**

```text
F01+N01 alone do not uniquely force the C^2 spinor/twistor carrier
  — falsifier:  a dim=3 noncommuting alternative (qutrit raising/lowering)
                satisfies both roots; the carrier choice is downstream of
                additional admissibility content beyond the roots themselves.

raw tensor-index ontology is not admissible as a primitive substrate
  — falsifier:  raw weighted-index readout changes under qubit swap (delta > 0)
                and under local SU(2) (delta > 0); the spinor entropy spectrum
                is unchanged (delta < 1e-9). Tensor INDEX is rejected.

bond-1 Schmidt truncation is not a faithful tool for the edge state
  — falsifier:  bond=1 forces rank-1 product on |Psi_01>, collapsing single-qubit
                entanglement entropy from 0.257 to 0 and dropping fidelity to
                0.929. Bond=2 is exact (fidelity 1.0).

product state is not the entangled network
  — falsifier:  forcing lambda=0 across all 4 edges drives total cut entropy
                to ~0 while the entangled baseline is 1.69. Entanglement is
                load-bearing as the cut readout.

H_L = H_R is not the chiral carrier
  — falsifier:  with sheet sign reversed (H_R = -H_0), short-time transport
                drives ||rho_L - rho_R||_F > 0; with sheet sign collapsed
                (H_R = +H_0), the same transport gives ||rho_L - rho_R||_F = 0.
                Sheet sign is load-bearing structure.

random S^2 phase is not the twistor incidence
  — falsifier:  pseudo-random per-edge phase produces a different
                incidence_phase_ordered readout (gap ~4.83) while leaving the
                entropy spectrum unchanged. Twistor incidence is not
                interchangeable with a random label at the phase readout.

scalar (trace + purity) equality is not probe-relative identity
  — falsifier:  rho_a = (I + 0.6 sigma_z)/2 and rho_b = (I + 0.6 sigma_x)/2
                have the same trace and purity; commutator with sigma_x
                separates them. Scalar equality is rejected as identity.
```

**NOT falsified (still open or weak):**

```text
F2 "no extra tensor geometry beyond the spectrum" is narrowed, not open-ended
  — what we showed: edge-order permutation does not move the sorted entropy
    spectrum (gap ~7.6e-16), but it does move an edge-identity-sensitive
    entropy*incidence feature (gap ~0.2087).
  — verdict: spectrum-only geometry is killed; basis-sensitive edge geometry
    is not killed. Future claims must name which readout is being used.

flux as Axis 3 vs flux as engine binding
  — Scout 4 (flux basin binding) currently shows global-binding behavior;
    per-stage flux flip fails the coherence gate. Not canonized; further
    controls needed before either placement is admitted.

Phi_0 cross-family pressure — what receipts honestly support (rev. post-3-model-audit)

  Counting honestly:
  — 6 incidence-derived edge-mixture candidates (Family 1)
  — 1 incidence-derived joint-graph candidate (Family 2)
  — Total: **7** incidence-derived candidates tested, not 10. The four
    Family-2 modes include product_baseline, random_seeded, and
    uniform_lambda_zero_phase — those are controls and baselines, not
    candidates. Earlier "10 Φ_0 candidates killed" framing was overcount.

  All 7 incidence-derived candidates lose admission against zero-phase or
  random baselines under the **single tested configuration** (XY entangler,
  z-dephasing γ=0.30, partition A={0,1}/B={2,3}, coherent information,
  N=4, 4-node ring, π built from spinors).

  This is NOT yet a "Φ_0 family killed" verdict. Three-model independent
  cross-audit (Gemini 2.5 Pro, Claude Opus, Grok-4) converged that
  within-family pressure was not exhausted. The previous draft of this
  section said "do NOT try a third edge-pattern variation" — that strategic
  call has been **retracted** as premature pending the Open Within-Family
  Tests below.

Phi_0 cross-family — earlier draft (kept for trail, marked retracted)
  ============================================================================
  ============================================================================

  Family 1: edge-mixture Xi (six candidates killed)
  — Scout 5's bridge_gate evaluates six edge-mixture bridge candidates against
    zero-phase baseline (I_c = +0.149) and random/product/history-erased
    controls. Admission threshold: I_c > 0 AND I_c > zero+0.02 AND
    I_c > random+0.02 AND I_c > product+0.5 AND I_c > erased+0.5.
  — candidate_modes_admitted = [] (count = 0)
  — measured per-mode I_c:
      raw incidence phase           : -0.057
      absolute_incidence_phase      : +0.142 (loses to zero by ~0.007)
      oriented_phase_class          : -0.024
      incidence_magnitude_lambda    : +0.076
      inverse_magnitude_lambda      : +0.138 (loses to zero by ~0.011)
      history_coupled_edge_weight   : -0.024
  — verdict: edge-mixture-then-coherent-information has zero-phase as its
    best tested member. Every attempt to inject incidence-derived structure
    leaves I_c at or below the structureless zero-phase construction.

  Family 2: joint-graph partition Xi (new construction, also killed)
  — Scout 5's joint_graph_partition_bridge_gate (added after family 1 kill)
    builds a single 4-qubit pure state by applying per-edge XY entanglers
    `exp(-i (λ·X_i X_j + φ·Y_i Y_j))` to a product of node spinors, then
    partitions A={0,1}, B={2,3}. This is structurally distinct from the
    edge-mixture family.
  — Modes: incidence_derived, random_seeded, product_baseline, uniform.
  — Admission requires: nontrivial pure I_c, beats product by >0.1,
    survives 30% dephasing, beats random_seeded under noise by >0.02.
  — incidence_admitted = False.
  — measured I_c values:
      pure incidence_derived       : +0.222
      pure random_seeded           : +0.468  (RANDOM BEATS INCIDENCE BY 0.246)
      pure product_baseline        : +0.000  (no entangler applied)
      pure uniform_lambda          : +0.172
      dephased incidence_derived   : -0.714
      dephased random_seeded       : -0.598  (random still beats incidence)
      dephased product_baseline    : -0.636
      dephased uniform_lambda      : -0.719
  — verdict: across both pure and dephased readouts, RANDOM parameters
    produce more bipartite entanglement than incidence-derived parameters
    under the same entangler structure.

  Cross-family pattern (the real audit signal)
  — Across two structurally distinct Xi constructions (edge-mixture and
    joint-graph), the result is the same: geometry-derived (twistor
    incidence) parameters consistently fail to beat baseline noise.
    Random or zero-phase controls match or exceed every incidence-derived
    candidate tested.
  — possible structural reasons:
      (a) the twistor incidence `<π_i|ω_j> − <π_j|ω_i>` may carry less
          discriminating information than uncorrelated random parameters
          because the twistor nodes are themselves derived from correlated
          spinors, so incidence values cluster in a narrow range;
      (b) the phase φ_ij from incidence may correlate across edges in ways
          that create destructive interference under both summation and
          serial application;
      (c) coherent information of a bipartite cut from a graph-derived
          mixture or partition is not the right Phi_0 functional —
          something else (relative-entropy asymmetry, squashed entanglement,
          log-negativity, or a non-cut readout) may be needed.
  — implication (RETRACTED post-3-model-audit): the original draft said
    "do NOT try a third edge-pattern variation; change either the Xi
    construction altogether or the Phi_0 functional." All three external
    audits (Gemini, Opus, Grok) independently flagged this as premature
    because the following within-family axes were never varied:
    partition, entangler family, dephasing channel, Phi_0 functional, scale.

Open Within-Family Tests (added post-3-model-audit, what must be done before
any "family killed" conclusion is admissible):

  Convergent recommendations from 3-model audit (Gemini 2.5 Pro + Claude
  Opus code-reviewer + Grok-4) — each item flagged by ≥2 of 3 models:

  1. Alternative partition: A={0,2}, B={1,3} interleaved (cuts all 4 ring
     edges, not just 2). All three models name this. Cheap test (~10 lines).
  2. Alternative entangler: Heisenberg (XX+YY+ZZ) or Ising (ZZ) replacing
     current XY (cos(λ)XX + sin(φ)YY).
  3. Alternative noise channel: x-dephasing, depolarizing, amplitude damping
     — current z-only γ=0.30 is structurally orthogonal to XY entangler basis
     and may bias the kill.
  4. Alternative Phi_0 functional: log-negativity, squashed entanglement,
     relative entropy of entanglement. Coherent information rewards generic
     bipartite entanglement, which random params produce by default.
  5. Scale: N=6, N=8 nodes (currently fixed N=4).
  6. Topology: complete graph K_4, star, path (currently fixed 4-node ring).
  7. RNG ensemble: replace fixed pseudo-random formulas with 30+ realization
     statistics. The Family-1 "random_fixed" uses formula `1.7 * (idx+1)`,
     not a sampled distribution.

  Until at least items 1-4 are tested, the cross-family kill verdict
  remains: "7 incidence-derived candidates lose under the single tested
  configuration," not "Φ_0 family is dead."

  Round-1 fix: items 1 and 4 now tested. Joint-graph Xi was extended to
  evaluate two partitions and two Phi_0 functionals — 4 cells total.

  Admission matrix (Round 1):

  | Functional | Partition         | Inc pure | Rand pure | Inc-Rand pure | Admitted |
  |------------|-------------------|----------|-----------|---------------|----------|
  | I_c        | block {0,1}|{2,3} | 0.222    | 0.468     | -0.246        | False    |
  | I_c        | interleaved {0,2}|{1,3} | 0.686 | 0.727 | -0.041     | False    |
  | log-neg    | block             | 0.681    | 0.998     | -0.317        | False    |
  | log-neg    | interleaved       | 1.155    | 1.403     | -0.248        | False    |

  Interpretation (rev. post-Round-2-audit, arithmetic corrected):
  — In all 4 cells, random_seeded parameters give larger entanglement-cut
    readouts than incidence_derived parameters; admission fails.
  — The interleaved-partition × I_c cell shows the SMALLER of the four
    pure-state shortfalls (Inc - Rand = -0.041 vs -0.246 / -0.317 / -0.248
    in the other three cells). Round-1 framing said this was "within 6% of
    the 0.02 admission threshold band" — that was arithmetically wrong:
    admission requires `inc - rand > +0.02`, so the gap from admission is
    -0.041 - 0.02 = -0.061, i.e., **incidence would have to improve by 0.061
    (3x the threshold band) just to reach the admission boundary**.
  — Even if the pure-state cell hit admission, this row also fails the
    `survives_dephasing > 0` criterion: I_c-interleaved-incidence-dephased
    = -0.540. So the cell fails 2 of 4 admission criteria, not 1.
  — Log-negativity behaves similarly to I_c — random wins by a larger margin
    under both partitions. The functional change does not save geometry.
    Caveat (Opus D9): the `survives_dephasing > 0` criterion is meaningful
    for coherent information (positive I_c ≡ positive quantum capacity), but
    trivial for log-negativity (LN > 0 for any entangled state). For LN, the
    more honest threshold is `LN_inc_dep > LN_rand_dep + margin`. Under that
    threshold, log-neg cells also fail (inc_dep loses to rand_dep by 0.21
    and 0.07 in block and interleaved respectively).

  Remaining items from the 7-item list (items 2, 3, 5, 6, 7 still untested):
    2. Alternative entangler (Heisenberg / Ising replacing XY)
    3. Alternative noise channel (x-dephasing / depolarizing / amplitude damping)
    5. Scale: N=6, N=8
    6. Topology: K_4, star, path
    7. RNG ensemble: 30+ realizations for random baseline

  After Round 1 (partition × functional tested), the SINGLE-INSTANCE verdict
  was: across 4 cells (2 partitions × 2 functionals), incidence_derived loses
  to random_seeded in 4 of 4 cells. Earlier "16 readouts ... every comparison"
  framing was inflated — only 1 of 4 modes is geometry-derived; the real
  comparison count is 4 cells, not 16.

  After Round 2 (K=30 Haar-random RNG ensemble × 2 noise channels), the
  verdict reverses: the single-instance result was a TAIL SAMPLE, not the
  family's central tendency.

  Scope of conclusions (Round-3 fix, Opus D5 + Gemini explicit-scoping):
  All RNG-ensemble verdicts below are conditioned on the following fixed
  configuration. Conclusions DO NOT generalize beyond these parameters:
    - N=4 nodes, 4-node ring topology (edges (0,1),(1,2),(2,3),(3,0))
    - C^2 spinor at each node
    - XY entangler family only: exp(-i (λ·X_i X_j + φ·Y_i Y_j))
    - Two partitions tested: A={0,1}/B={2,3} (block, cuts 2 edges) and
      A={0,2}/B={1,3} (interleaved, cuts 4 edges)
    - Two Phi_0 functionals tested: coherent information I_c, log-negativity
    - Two noise channels tested: z-dephasing, depolarizing (both γ=0.30)
    - K=30 Haar-random spinor seeds
    - Items 2 (alt entangler XX+YY+ZZ Heisenberg / ZZ Ising), 5 (scale N=6,
      N=8), 6 (alt topology K_4, star, path) from the 7-item list remain
      UNTESTED. K=30 result does NOT settle them.

  RNG ensemble result (K=30 Haar-random spinor graphs):
    - 4 pure-state cells (2 partitions × 2 functionals) — by mathematical
      construction, pure-state readouts are independent of noise channel, so
      the 2 noise channels do NOT multiply this count.
    - 4 noisy cells under z-dephasing + 4 noisy cells under depolarizing
      (the 2 noise channels DO differ on the noisy half).
    - Reported as "8 cells" in earlier Round-2 framing was inflated for the
      same template-reason that "16 readouts" was inflated in Round-1
      framing (Opus D3 from Round-3 audit). Honest count: 4 pure cells +
      4 noisy cells per noise channel = 4 pure + 8 noisy entries when
      reporting noisy means, but only 4 pure means (identical across the
      noise dimension).

  | Cell                                  | Pure mean(Inc-Rand) | Pure std | inc-beats-rand rate |
  |---------------------------------------|---------------------|----------|---------------------|
  | z-deph / block / I_c                  | +0.036              | 0.229    | 60%                 |
  | z-deph / block / log-neg              | +0.034              | 0.261    | 57%                 |
  | z-deph / interleaved / I_c            | +0.004              | 0.223    | 53%                 |
  | z-deph / interleaved / log-neg        | +0.005              | 0.258    | 50%                 |
  | depolarizing / block / I_c            | +0.036              | 0.229    | 60%                 |
  | depolarizing / block / log-neg        | +0.034              | 0.261    | 57%                 |
  | depolarizing / interleaved / I_c      | +0.004              | 0.223    | 53%                 |
  | depolarizing / interleaved / log-neg  | +0.005              | 0.258    | 50%                 |

  Interpretation (rev. post-Round-3-audit, statistical-claim corrected):
  — Ensemble means are small (+0.004 to +0.036) and dominated by standard
    deviations (0.22 to 0.26). Signal-to-noise < 0.2.
  — Inc-beats-rand rate is 50-60% across all cells — consistent with chance
    plus an unmeasured small bias.
  — Power analysis (Round-3 fix): SE = std / sqrt(K) = 0.23 / sqrt(30) ≈
    0.042. 95% CI on the largest cell mean (+0.034) is approximately
    [-0.048, +0.116]. The CI straddles the +0.02 admission threshold.
    Minimum K to detect a 0.02 effect at 80% power with α=0.05 is
    K ≈ (2.8 * 0.23 / 0.02)² ≈ 1000. **K=30 is severely underpowered for
    this question.**
  — Round-2 framing said incidence_derived and random_seeded were
    "STATISTICALLY INDISTINGUISHABLE." Round-3 audit flagged this as
    overclaim (Gemini CRITICAL, Opus D2): hypothesis testing rejects
    null, not proves it. **The honest framing is "the K=30 ensemble
    failed to show a statistically significant difference between
    incidence-derived and random-seeded parameterizations; the experiment
    is underpowered to settle the question."**
  — Doc-vs-JSON consistency (Round-3 fix, Opus D1): under the previous
    point-estimate-only admission criterion (mean > +0.02), the JSON
    reported `any_ensemble_admission = True` with cell
    `z_dephasing/block/log_negativity` admitted at mean +0.034. Under the
    new SE-aware admission criterion (mean > 2 * SE = 0.084), NO cell
    clears. The doc verdict ("no significant signal") and the scout
    verdict ("no SE-aware admission") now agree.
  — The previous Family-2 single-instance Inc-Rand = -0.246 was a tail
    sample, not a representative measurement. The "kill" framing was an
    artifact of insufficient sampling.

  Alternative readouts NOT tested (Round-3 fix, Opus D6 + Gemini):
  The "no signal" verdict applies only to the bipartite-cut readout family
  (coherent information I_c and log-negativity LN of ρ_AB, where ρ_AB is
  built by either edge-mixture or joint-graph partition). It does NOT rule
  out signal in other readout families that may be sensitive to twistor
  incidence even when bipartite entanglement is not:
    - Entanglement spectrum statistics (Schmidt-value distribution shape,
      not just S = -Σ p log p)
    - Multipartite mutual information I(A:B:C:D) on a 4-node split
    - Relative entropy distance S(ρ_geometry || ρ_random) between
      graph-derived and random-parameterized states
    - Projective cross-ratios on the twistor π-ω pairs
    - π-ω correlation invariants (e.g., basis-rotation-equivariant operators
      acting on the joint twistor space)
    - Non-cut operator-algebra observables (e.g., commutator spectra of
      operators built from incidence values)

  Until at least 2-3 of these are tested, the verdict is "no signal in this
  readout family at this construction," not "no signal in twistor geometry."

  Alternative explanations for the K=30 null (Round-3 fix, Gemini):
  A null result has multiple admissible explanations. Listing them for
  intellectual rigor:
    a. The signal is real but smaller than the K=30 noise floor.
       Power analysis shows K ≈ 767-1057 needed to detect a 0.02 effect
       at 80% power. K=30 is severely underpowered.
    b. The readouts (I_c, LN) are insensitive to twistor incidence even
       though some other observable would distinguish it. See
       "Alternative readouts NOT tested" above.
    c. The Xi constructions tested (edge-mixture, joint-graph partition)
       happen to symmetrize incidence into noise. A third Xi construction
       (e.g., operator-algebraic, spectral, or non-cut) might preserve it.
    d. There is a subtle simulation bug. The construction has been
       cross-audited 3 times with no bug-level findings, but no formal
       correctness check against an analytic baseline has been run yet
       (Gemini Round-2 S2 finding).
    e. The "no signal" verdict is correct: twistor incidence does not
       carry information that distinguishes ρ_AB readouts from random
       parameterizations in this readout family.
  At K=30, the evidence cannot select among (a)-(e); higher-K runs and
  alternative readouts are needed to discriminate.

  Honest current verdict (revision after RNG ensemble):
  — Phi_0 family is NOT killed. The previous "10 candidates killed" → "7
    candidates killed" → "kill is strengthened across 4 cells" framing has
    been incrementally corrected by external audits at each round; the
    ensemble test finally exposes the underlying issue.
  — The HONEST verdict from current evidence: across Haar-random spinor
    networks, the geometric signal (twistor incidence) does not generate
    detectable bias in cut-state entanglement readouts vs. random
    parameters. This is a "no signal detected" result, not a "geometry
    fails" result.
  — Distinction matters: "no signal" leaves open whether the signal is real
    but hidden by readout / Xi construction choices, or whether there is no
    signal to find. The framing should be "Xi/Phi_0 with current
    construction and readouts is not sensitive to twistor incidence" — not
    "twistor incidence is killed."

  Earlier draft kept for trail (RETRACTED post-Round-2):
  "Two Xi families now rejected; cross-family pattern shows geometry loses
  to baseline noise; do not try a third edge-pattern variation."

  However, items 2, 3, 5, 6, 7 remain open. The verdict is still
  configuration-conditioned: it has been falsified across 2 partitions and
  2 functionals at N=4 with XY entangler + z-dephasing on a 4-node ring.

holographic spacetime / ER=EPR
  — still claim-ceiling-fenced. Not tested by any scout in this set.
```

**Read this section as the actual audit signal.** The "all_pass = true" in
the receipt summarizes that every gate, control, and ablation behaved as
designed. The falsifying content lives here.
