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
| Bekenstein finite-capacity | no (SAT with `F01 ∧ ¬Bekenstein`) | yes (UNSAT with `¬F01 ∧ Bekenstein`) | `derived_from_F01_with_additional_capacity_content` |
| no Cartesian center | no (SAT with `F01 ∧ N01 ∧ ¬no_center`) | yes, both (UNSAT with `¬N01 ∧ no_center`) | `derived_from_F01_and_N01_with_relational_invariance_content` |
| no global total order | no (SAT with `N01 ∧ ¬no_total_order`) | yes (UNSAT with `¬N01 ∧ no_total_order`) | `derived_from_N01_with_order_observability_content` |
| flux/chiral orientation | (not tested as direct entailment) | yes (UNSAT with `¬F01 ∧ flux`) | `open_candidate_dependent_on_F01_for_finite_sheet_count` |

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
| Semantic dependency fence | roots do not force capacity `sat`; capacity-with-roots witness `sat`; capacity requires F01 `unsat`; twistor-with-roots witness `sat`; twistor requires F01+N01 `unsat`; Clifford-order-with-N01 witness `sat`; Clifford order requires N01 `unsat`; holography-with-capacity witness `sat`; holography requires capacity `unsat` | **supportive consistency content** — these are stated-dependency checks with satisfiable antecedent witnesses, not root derivations |

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
| semantic dependency fence | roots do not force Axis0 `sat`; cut-capacity-with-F01 witness `sat`; cut capacity requires F01 `unsat`; ER=EPR-with-roots/capacity witness `sat`; ER=EPR requires F01+N01 `unsat`; holography-with-ER=EPR/capacity witness `sat`; holography requires ER=EPR `unsat`; raw-bridge Axis0 canon rejected `unsat` because the empirical raw bridge gate was killed |

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

Phi_0 final form — TWO Xi families now rejected
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
  — implication: do NOT try a third edge-pattern variation. The next move
    needs to be at a different layer: change either (i) the Xi -> ρ_AB
    construction altogether (e.g., spectral/operator-based, not state-based),
    or (ii) the Phi_0 functional (away from coherent information), or both.

holographic spacetime / ER=EPR
  — still claim-ceiling-fenced. Not tested by any scout in this set.
```

**Read this section as the actual audit signal.** The "all_pass = true" in
the receipt summarizes that every gate, control, and ablation behaved as
designed. The falsifying content lives here.
