# Codex Ratchet Sim Completion Source-Audit Plan 2026-06-15

```yaml
receipt_kind: source_audit_plan
status: plan_only
claim_ceiling: no sim admission, no layer completion, no M(C) admission, no QIT-engine admission, no Axis0, no bridge, no physics
controller: Codex single-controller audit
scope: wiki + live repo + Levos bridge packet + current v7 sim result state
```

This is the plan for getting the current sims done without moving the target every time a model sees a more interesting downstream object.

It is not a Max Assembly receipt, not a worker-fleet result, and not an admission packet. It is a source-grounded controller plan: what must be built, in what order, with what math, using what files, gates, controls, and honest status labels.

## 0. Non-negotiable Reading Order

Before any sim edit, closeout, or claim, read these surfaces in this order:

1. Current request and this plan.
2. `/Users/joshuaeisenhart/Codex-Ratchet/AGENTS.md`.
3. `/Users/joshuaeisenhart/Codex-Ratchet/CODEX.md`.
4. `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`.
5. `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/docs/LLM_CONTROLLER_CONTRACT.md`.
6. `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/docs/LEGO_SIM_CONTRACT.md`.
7. Wiki front door:
   - `/Users/joshuaeisenhart/wiki/index.md`
   - `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/read-first.md`
   - `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/current-v7-campaign-restart-context-2026-06-14.md`
8. Current foundation and layer instruments:
   - `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/foundations/root_axioms_v0_1_DRAFT.md`
   - `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/foundations/v7_gate_grounding_law_DRAFT_20260614.md`
   - `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/foundations/manifold_layer_order_and_completeness_contract_20260614.md`
   - `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/foundations/manifold_layer_ledger_20260614.md`
9. The exact sim target source:
   - Levos bridge zip `/Users/joshuaeisenhart/Desktop/levos_bridge_packet_josh_updates_AUDITED_20260615 (1).zip`
   - Its `08_CODEX_RATCHET_MATH_BRIDGE_AND_SIM_TARGETS.md`
   - Its `sim_targets/*.md`
10. The current sim's source, result JSON, verdict file, audit receipt, and gate output.

No worker report or chat summary substitutes for this read gate.

## 1. Root Math: What Emerges First

The base object is not a polished physics layer. It is the weakest finite structure that can preserve distinguishability under active constraints and still evolve.

The stable root is:

```text
primitive = constraint on distinguishability
identity = probe-relative, not primitive
a = a iff a ~ b
```

This appears in three root expressions that must not be collapsed:

```text
elements:   S/~_P              probe-relative quotient classes
order:      A o B != B o A     noncommutation / sequence sensitivity
grouping:   (A o B) o C != A o (B o C) when a probe can distinguish bracketings
```

Finitude is load-bearing across all three:

```text
finite support S
finite constraint set C
finite probe family P
finite quotient relation ~_P
finite admissibility predicate Adm_C
finite composition/bracketing rules
finite readouts
finite controls
finite receipts
```

The finite object to make is:

```text
M(C) = (S, C, P, ~_P, Adm_C, composition/bracketing, local readouts, controls, receipts)
```

This is the early finite admissibility object. It is not automatically a smooth manifold, carrier geometry, QIT engine, Axis0, bridge, or physics.

## 2. MSS / Least-Admissible Evolvable Structure

The user's "least strong thing that survives" should be operationalized as a gate, not as another metaphysical noun.

Use:

```text
MSS = minimal survivable / least-admissible evolvable structure
```

Meaning:

1. A candidate structure is admitted only if it survives active finite constraints.
2. It must still evolve: distinguish, compose, update, preserve receipts, and expose a kill condition.
3. If a weaker object does the same job under the same probes and controls, the stronger object is installed, not forced.
4. Plural survivors remain live until killed.
5. No metric, time, cause, probability, identity, complex Hilbert space, spinor, quaternion, geometry, or manifold is primitive.

The sim form is:

```text
structures = [quotient_only, state_functional, density_operator, spinor_lift, quaternionic_map, ...]
preorder A <= B iff A preserves no more live distinctions than B under the active probe family
Surv = structures that pass active constraints
MinSurv = minimal elements of Surv under <=
forced = stronger structure required because every weaker survivor fails a named future probe/control
installed = stronger structure useful, but a weaker survivor still does the same job
```

This is exactly the point of:

```text
system_v7/sims/finite_distinguishability_quotient_forced_or_installed_carrier_v0
system_v7/sims/weakest_structure_ladder_gate_v0
```

These must be front-of-queue foundation gates, not side curiosities.

## 3. Density, Spinor, Quaternion, Hopf: Correct Placement

The wiki and repo sources support this corrected order:

```text
constraint on distinguishability
-> finite support S
-> finite probe family P
-> quotient S/~_P
-> finite M(C) object
-> state functional omega
-> update/probe algebra
-> density matrix rho only if the earned algebra/state representation forces it
-> spinor lift psi when quotient-erased phase/frame/path/chirality distinctions are load-bearing
-> quaternionic or Clifford structures only as closure witnesses or installed carrier layers
-> Hopf/tori/Weyl/terrain/operator/Axis0 only after their lower finite object and controls exist
```

Density matrices are early stable operational state/readout language once the relevant finite carrier/probe algebra is earned. They are not the primitive. Spinors are leading carrier pressure when lifted phase, frame, path, or 720-degree/holonomy information survives probes that density erases. Quaternions, Clifford, octonions, G2, Spin(7), Spin(8), and F4 are later closure/licensing structures, not root replacements.

The standing discriminator question for every stronger structure is:

```text
Can a weaker object do the same job under the same probes and controls?
```

If yes, demote the stronger object to installed/supportive. If no, record the exact failed weaker control and the exact future probe that forces the lift.

## 4. Ring-Checkerboard and Wiki Provenance

The ring-checkerboard is not forgotten and not decorative. It is the owner-native finite support model and a candidate run-surface for M(C,t).

Source docs:

- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/pre-ai-rosetta-ring-checkerboard-provenance-2026-06-09.md`
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/ring-checkerboard-three-presentations-sim-engine-runbook-2026-06-09.md`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/ring_checkerboard_provenance_20260611.md`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/owner_doctrine_cellular_automata_ring_checkerboard_20260611.md`

It has three candidate-equivalent presentations:

```text
flat nested checkerboard       = finite combinatorial/local chart
spherical/hyperspherical shell = shell/boundary/nesting readout
nested rings/Hopf-torus chart  = fiber-loop/phase-loop decomposition
```

These presentations are not one-to-one engine assignments. Julia, JAX, and PyTorch/JAX/Julia modes are evidence backends over the same finite object, not the three presentations.

Candidate support key:

```text
state = (sheet, eta_shell, phi_index, chi_index)
psi_s(phi_i, chi_j; eta_k) =
  [ exp(i(phi_i+chi_j)) cos(eta_k),
    exp(i(phi_i-chi_j)) sin(eta_k) ]
rho_s = psi_s psi_s^dagger
```

The finite presentation consistency sim must check support count, shell/eta index, ring/fiber coordinate table, probe bins, quotient classes, density rows where earned, phi-blindness under density probes, relation/adjacency readouts, and folding/reindexing invariants.

## 5. Current Repo Truth on 2026-06-15

Live root audited:

```text
/Users/joshuaeisenhart/Codex-Ratchet
HEAD: 5ea3e894b sim: start Levos quantum Hopfield QCA entropy-information exact fixture
working tree: clean at audit time
```

Stage gate:

```text
active_stage = lego
allowed: tool_micro, tool_integration_micro, tool_lego_fit, lego
blocked: scientific_coupling, coexistence, bridge, axis, engine, tier_d, default_late_stage
```

The live moved root does not expose `make layer-completion-claim-gate`. The older Desktop root did. Therefore live completion claims must not cite a local `layer-completion-claim-gate` pass unless that target is restored or the older-root context is explicitly used and fenced. In this live root, use `make stage-gate`, v7 validators, receipt reconciliation gates, and explicit noncompletion ceilings.

## 6. Current v7 Sim Inventory by Honest Role

### Foundation floor / already stronger than prose

1. `distinguishability_quotient_floor_v0`
   - Status: `scratch_diagnostic`; passes local rerun via Julia/JAX/PyTorch agreement.
   - Role: L1 probe quotient `S/~_M`, 1q floor.
   - Ceiling: not valid alone for multi-qubit claim; not canonical by process.

2. `finite_probe_quotient_inverse_limit_tower_1q_through_4q`
   - Status: `scratch_diagnostic`; passes local rerun; genuine 1q/2q/3q/4q tower.
   - Earned: compatibility law, extension fibers, ZZ-erasure quotient flip, 3q useful + 4q one-beyond.
   - Open: gate scanner bug/definedness failures, incomplete full-negative roster, forecast overclaim at 4q, hand-curated state set, fresh audit/gate closure.

3. `finite_distinguishability_quotient_forced_or_installed_carrier_v0`
   - Status: `scratch_diagnostic`; the right MSS/forced-or-installed foundation lane.
   - Open: current v7 admission fails math-only/name-math definedness; keep as foundation gate, not downstream proof.

4. `weakest_structure_ladder_gate_v0`
   - Status: present but result shape is not standard `sim_id/classification`.
   - Role: gate concept for least-admissible evolvable structure.
   - Need: normalize result schema and bind to the MSS plan.

### Levos explicit sim targets now present

The zip contains nine overview targets, but only four explicit files under `sim_targets/`. Treat those four as spec-ready and the other five as named backlog requiring spec extraction.

1. `entropy_geometry_coratchet_floor_v0`
   - Source: `sim_targets/entropy_geometry_coratchet_floor_v0.md`.
   - Current: exact Python fixture; `classification=scratch_diagnostic`; `all_9_tests_pass=true`; `draft_unaudited=true`; `evidence_eligible=false`.
   - Gate probe: v7 admission fails math-only, name-math, and two-tier-authority (`load_bearing_no_audit_file`).
   - Required next: audit file, independent JAX/Julia or scoped engine legs as appropriate, proper tool-depth fields, controls hardened.

2. `finite_ring_checkerboard_support_three_presentation_consistency_v0`
   - Source: explicit sim target + wiki runbook.
   - Current: exact table + JAX agreement; `scratch_diagnostic`.
   - Earned: 96-row finite support table, three presentation table agreement, density rows as readout, phi-blindness, phase-sensitive split, adjacency agreement, erasure controls.
   - Caveat: agreement partly by construction; no Julia/PyTorch independent leg; folding/reindexing thin; no admission.
   - Gate probe: v7 admission fails math-only/name-math definedness.

3. `spinor_quotient_freedom_discriminator_v0`
   - Source: explicit sim target.
   - Current: exact + JAX agreement; `scratch_diagnostic`; valid narrow discriminator.
   - Earned: public quotient erases fiber phase; named future probe splits it; no-frame control does not.
   - Caveat: finite bins, not full continuous Hopf; not spinor admission; not freedom/social proof.
   - Gate probe: v7 admission fails math-only/name-math definedness.

4. `quantum_hopfield_qca_entropy_information_v0`
   - Source: explicit sim target.
   - Current: exact diagonal/open-channel fixture only; `scratch_diagnostic`.
   - Earned: finite `S={0,1}^4`, memory basins, row-stochastic diagonal channel, steady state, typed entropy/information readouts, coherent information blocked.
   - Caveat: not full quantum Hopfield, not non-diagonal CPTP/Lindblad, not QIT-engine admission.
   - Gate probe: v7 admission fails math-only/name-math definedness.

### Other named Levos overview targets needing spec extraction

These appear in the Levos `08_CODEX_RATCHET_MATH_BRIDGE_AND_SIM_TARGETS.md` overview but do not have explicit `sim_targets/*.md` files in the zip:

1. `ring_checkerboard_single_token_scc_basin_v7`
2. `full_configuration_partitioned_ca_v0`
3. `finite_brickwork_qca_operator_index_v2`
4. `open_chain_gnvw_calibration_v0`
5. `geometric_constraint_ratchet_on_ring_support_v0`
6. `forced_or_installed_carrier_comparison_v0` (covered in spirit by `finite_distinguishability_quotient_forced_or_installed_carrier_v0`, but the Levos target should be extracted explicitly)

Do not let a worker claim these are implemented just because the overview names them.

### Caught-hack / negative examples

`mixed_radix_endofunction_scc_terminal_quotient_under_z2_involution_v0` is real math but rejected as a reclamation. It is a caught-hack negative example: cosmetic relabel survived in spec values, SMT load-bearing was inflated, independence was partly by construction, and the title claimed math not computed. Use it as a gate-hardening test, not as a v7 positive.

`axis0_terrain_engine_leap_v0` is downstream language while stage gate blocks axis/engine. Keep it as blocked/downstream unless specifically used as a negative fixture.

## 7. Completion Meaning

Use only these ladder labels:

```text
exists < runs < passes local rerun < canonical by process
```

No current v7 layer is `canonical by process`.

A layer is done only when all fourteen boxes in `manifold_layer_order_and_completeness_contract_20260614.md` pass with cited artifacts:

1. Max finite sim-set enumerated.
2. Positive and boundary tests populated.
3. All applicable negatives genuinely fire.
4. Qubit ladder depth to useful + one beyond.
5. Full axiom-grounded gate stack passes.
6. Nested via compatibility law + extension fibers computed.
7. Section-5 predicted modification forecast recorded and checked.
8. Fresh-context audit by non-builder, multi-model/cross-audit where required.
9. Nesting-law queue position recorded.
10. Status-label honesty.
11. Claim-ceiling fields bound.
12. Build-order/stage-gate position correct.
13. Per-layer entropy/readout family declared and licensed by nesting.
14. Seven audit questions answered.

The seven audit questions:

```text
Which layer?
Which nesting relation?
Which qubit depth?
Which surface/network?
Which engines ran and were they load-bearing?
Which entropy/readout families varied?
What broke when depth/nesting/surface was removed?
```

## 8. Gate Hardening Must Precede Promotion

Current v7 admission failures are dominated by definedness/name-math scanner issues. This matches the fresh audit of the v7 gate law: the gate needs an admitted-math-term registry and better scope boundaries before it can become the true allow-list fence.

Gate-hardening work packages:

### G0.1 Fix live completion-gate drift

Problem: live root lacks `make layer-completion-claim-gate` while the contract mentions it.

Plan:

1. Decide whether to restore a live target or update `AGENTS.md`/process docs to point to the actual gates.
2. Until fixed, block any "layer completion", "full layer", "parent complete", "G-structure complete", "manifold admitted", or "Axis0/bridge unlocked" language.
3. Use `make stage-gate` plus v7 validators only for their actual claims.

### G0.2 Build admitted-math-term registry before allow-list inversion

Problem: naive L0-only allow-list rejects legitimate keys such as `depth`, `ring`, `entropy`, `geometry`, `honest_scope`, `python_stdlib`, etc.

Plan:

1. Populate admitted terms through proper TERM_DEF/definition records.
2. Scope the definedness fence to admission/definition surfaces, not every derived output key.
3. Keep output keys such as entropy/geometry allowed only as derived readouts with enabling lower layers.
4. Rerun validators against current v7 sims.

### G0.3 Fix scanner coverage and name-token evidence

Known bypasses:

1. `spec.json` values were not scanned deeply enough.
2. Distinctive name tokens were not all checked for evidence.
3. Nested `rungs` structures were missed by the name-math scanner.
4. Ground constant-fold SMT can look load-bearing when it is only an authoritative predicate wrapper.

Plan:

1. Scan whole packet: source, spec, result JSON, verdict, manifests.
2. Require evidence for all nontrivial name tokens.
3. Teach scanner nested rung containers.
4. Record solver role as `authoritative_decision_procedure` vs actual symbolic reasoning when necessary.

### G0.4 Normalize result schema for current fixtures

Every current v7 sim must expose:

```text
sim_id
classification
promotion_allowed
formal_admission_allowed
claim_ceiling
TOOL_MANIFEST with non-empty reasons
TOOL_INTEGRATION_DEPTH in the repo's accepted vocabulary
source_path/source_sha256
result_path/result_schema
negative_controls
demotion_condition
blocked_consumers
reads_peer_result or equivalent for engine independence
```

Do not turn schema normalization into promotion.

## 9. Workstream Plan

### Phase A: Foundation and gate cleanup

Goal: make the floor coherent enough that later sims stop being asked to carry undefined words.

Tasks:

1. Normalize `weakest_structure_ladder_gate_v0` into a standard result schema.
2. Re-audit `finite_distinguishability_quotient_forced_or_installed_carrier_v0` as the MSS discriminator.
3. Fix definedness/name-math scanner failures or document each as gate limitation with exact blocked receipt.
4. Fix or fence the missing `layer-completion-claim-gate` mismatch.
5. Produce one foundation ledger row:

```text
root -> S -> P -> S/~_P -> Adm_C -> composition/bracketing -> update/readout -> MSS preorder
```

Exit criteria:

```text
make stage-gate reports active_stage=lego
validate_v7_admission failures are either fixed or recorded as gate bugs, not sim claims
all current foundation sims retain scratch/nonpromotion ceilings
```

### Phase B: Convert the four explicit Levos targets from fixtures to audited scratch packets

Do these in dependency order.

#### B1. Ring-checkerboard support consistency

File:

```text
system_v7/sims/finite_ring_checkerboard_support_three_presentation_consistency_v0
```

Build:

1. Preserve exact table leg.
2. Add independent Julia leg for finite support/probe/quotient invariants.
3. Keep JAX vectorized leg.
4. Add PyTorch only if graph/adjacency/folding is load-bearing; otherwise mark PyTorch not scoped.
5. Strengthen folding/reindexing invariants and controls.
6. Record support-table hash and presentation-hash comparison.

Required controls:

```text
erase shell nesting
erase fiber coordinate
shuffle labels
same cardinality/different adjacency
flat/shell/ring disagreement injection
density-only phi-blindness vs phase-sensitive split
```

Exit: still scratch, but with independent leg agreement and a fresh non-builder audit.

#### B2. Entropy-geometry co-ratchet floor

File:

```text
system_v7/sims/entropy_geometry_coratchet_floor_v0
```

Build:

1. Use B1 support hash, not an unpinned local support.
2. Keep entropy families typed:
   - capacity entropy
   - quotient entropy
   - block entropy
   - SCC/basin entropy
   - order/path entropy
   - density/von Neumann blocked until density is earned
   - fiber residual blocked until Hopf/lift active
   - cut entropy blocked until cut structure exists
3. Add audit file to satisfy two-tier authority.
4. Add independent leg(s) where meaningful.
5. Recompute geometry after each carve; do not relabel geometry.

Required controls:

```text
label shuffle
same cardinality/different adjacency
geometry-only/no entropy
entropy-only/no geometry
premature von-Neumann entropy
commuting constraints
probe erasure
state-dependent noncommutation vs static commuting constraints
```

Exit: audited scratch floor; no density/physics promotion.

#### B3. Spinor quotient freedom discriminator

File:

```text
system_v7/sims/spinor_quotient_freedom_discriminator_v0
```

Build:

1. Keep current finite-bin discriminator as the narrow floor.
2. Add full finite Hopf table only after B1 support is pinned.
3. Separate:
   - public quotient readout
   - lifted phase/fiber readout
   - local frame readout
   - path/holonomy readout
   - chirality readout
   - bracketing readout
4. Each readout needs a no-frame/no-lift/no-phase control.

Exit: a stronger scratch discriminator saying exactly which quotient-erased distinctions are load-bearing, not spinor admission.

#### B4. Quantum Hopfield/QCA entropy-information

File:

```text
system_v7/sims/quantum_hopfield_qca_entropy_information_v0
```

Build:

1. Keep exact diagonal open-channel fixture.
2. Add JAX leg for vectorized transition/readouts.
3. Add Julia leg for exact finite Markov/channel algebra where useful.
4. Add PyTorch only if graph/basin/message-passing is load-bearing.
5. Split branches:
   - A: unitary/reversible QCA memory, cycles/invariant subspaces/information flow.
   - B: open CPTP/Lindblad/Hopfield memory, attractor basins/recall/steady states.
6. Do not compute coherent information until non-diagonal channel/purification is earned.

Required controls:

```text
random memory
shuffled support
no-memory channel
commuting update
identity QCA
nonlocal rule
metadata-only flow
density-only overbuild
open-system vs unitary-only split
```

Exit: audited scratch QCA/Hopfield fixture; no full quantum Hopfield or QIT-engine admission.

### Phase C: Extract specs for the five overview-only Levos targets

Do not code first. Write a spec file for each under a proper source/backlog surface.

Targets:

1. `ring_checkerboard_single_token_scc_basin_v7`
2. `full_configuration_partitioned_ca_v0`
3. `finite_brickwork_qca_operator_index_v2`
4. `open_chain_gnvw_calibration_v0`
5. `geometric_constraint_ratchet_on_ring_support_v0`
6. `forced_or_installed_carrier_comparison_v0` reconciliation against existing `finite_distinguishability_quotient_forced_or_installed_carrier_v0`

Each spec must include:

```text
source quote/path
claim
objects
tests
controls
blocked consumers
result schema
engine mode
demotion condition
next admissible consumer
```

### Phase D: Complete layer ledger rows, not slogans

Use `manifold_layer_ledger_20260614.md` as the standing campaign table.

Priority rows:

1. L1 probe quotient floor.
2. L2 density-rank strata + partial trace marginals.
3. L5 nested tori -> marginal-radius shells + Schmidt strata.
4. L8 cut lattice.
5. L9 Schmidt strata per cut.
6. L10 entropy per cut availability.
7. L14 runner/QCA, only after B4/C specs are audited.

Do not start L11 16 ordered maps, terrain/operator grammar, Axis0, bridge, or physics until ledger boxes justify it.

### Phase E: Same-carrier geometry micro-legos

Only after the floor and support are pinned.

First candidates:

1. Hopf fiber/base loop law on the same finite support.
2. Weyl-on-Hopf chirality with sign-erasure controls.
3. Path/holonomy/order layer with reverse-order controls.
4. Bracketing/nonassociativity root-vs-carrier discriminator.

Packet shape:

```text
one carrier
one geometry surface
one tool/function
one positive
one negative
one boundary
one result path
one demotion condition
```

### Phase F: CS/discrete middle layer

The CS geometry bundle is scaffold pressure, not repo authority. Use it to add missing middle-layer tool probes:

```text
graph theory
spectral graph theory
hypergraphs
graph rewriting
category/rewrite logic
automata/formal languages
e-graphs/equality saturation
combinatorial topology
discrete exterior calculus
causal/event structures
probabilistic graphical models/causal AI
geometric deep learning/GNNs
```

Rule: no install spree. One library, one function/API, one tiny claim, one positive, one negative, one boundary, one demotion condition, one receipt.

Useful first probes:

```text
rustworkx: finite graph/SCC/quotient check
XGI or HyperNetX: hyperedge incidence readout
GUDHI: tiny filtration/persistence control
TopoNetX: cell-complex incidence/orientation
egg/egglog: rewrite equivalence control
z3/cvc5: order impossibility or quotient-separation proof
```

### Phase G: Only later - terrain/operator/axes

Terrain/operator math is real source material, but it is downstream of the finite object and carrier/support checks.

When licensed, use exact definitions:

```text
Ti = z-basis dephasing
Te = x-basis dephasing
Fi = x-axis rotation
Fe = z-axis rotation
UP/DOWN = precedence/action-side variant, not a new operator
```

Count discipline:

```text
4 terrain families = Se, Ne, Ni, Si
8 terrain realizations = Funnel, Cannon, Vortex, Spiral, Pit, Source, Hill, Citadel
4 loop placements = left-fiber, left-base, right-fiber, right-base
16 terrain placements = sheet x loop x terrain family
8 signed operators = 4 base operators x up/down precedence
64 engine states = 8 terrains x 8 signed operators
```

Axes are functions:

```text
A_i : M(C) -> V_i
```

Axis0 stays blocked until a cut/bridge object exists and lower layers license the entropy/cut readout family.

## 10. Engine Modes

Current authority: JAX and Julia are primary for nonclassical execution. PyTorch is not decorative; it is included only when graph/network/autograd machinery is load-bearing, a legacy comparison is being audited, or a bounded helper ablation changes the observable.

Use mode-first envelopes:

```text
julia_canon_jax_workhorse
julia_canon_plus_jax_diagnostic
julia_canon_jax_with_pytorch_graph
pytorch_graph_network_packet
all_three_full_sims
audit_only
```

Do not run `--require-pytorch` unless the packet explicitly claims an all-three envelope or PyTorch is scoped as load-bearing. When PyTorch is not scoped, say so directly.

Every engine result must record:

```text
ran
source_path
source_sha256
packages_used
tool/function surfaces
reads_peer_result=false or equivalent
engine_contract.mode
semantic owner when applicable
exact command / project / interpreter
```

## 11. Standard Commands

Use the Makefile Python:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
make stage-gate
make runner-preflight
make receipt-reconcile-scope-strict BASENAME=<sim_id>
make qit-admission-rehearsal BASENAME=<sim_id> RESULT=<result_json> SIM_PATH=<sim_dir> OUT_DIR=/tmp/<sim_id>_rehearsal
```

Direct v7 gates:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_v7_admission.py <sim_dir>
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_math_only_packet.py <sim_dir>
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_name_math_correlation.py <sim_dir>
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_qubit_ladder_depth.py <sim_dir>
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_smt_not_tautology.py <sim_dir>
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_result_integrity.py <sim_dir>
```

Julia carrier commands must use strict local project/load path when applicable:

```text
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier <script.jl>
```

## 12. Claude/Codex Run Instructions

If handing this to Claude or another worker, give this exact bounded instruction:

```text
Do not assess whether the theory is finished. Do not compare the sims to downstream physics standards.
Read the wiki and repo authority surfaces. Work only on the next admissible sim packet.
Keep classification scratch_diagnostic unless every gate says otherwise.
For each packet, name S, C, P, ~_P, Adm_C, composition/bracketing, readouts, controls, result path, source hash, and blocked consumers.
If a stronger carrier appears, run forced-or-installed: can a weaker object do the same job?
If yes, demote stronger carrier to installed/supportive. If no, record the exact failed weaker control.
Do not use Axis0, bridge, QIT-engine, physics, terrain, manifold completion, or layer completion language unless the current live gates permit it.
```

## 13. Immediate Next Moves

The next controller moves should be:

1. Write/patch a small current-status ledger for the four explicit Levos targets, with their exact result paths and gate probe failures.
2. Fix or fence the definedness/name-math scanner issue before asking v7 admission to mean more.
3. Harden `finite_ring_checkerboard_support_three_presentation_consistency_v0` first, because other current Levos targets need the support substrate.
4. Harden `entropy_geometry_coratchet_floor_v0` second, because it currently lacks two-tier audit authority and claims the co-ratchet floor.
5. Keep `spinor_quotient_freedom_discriminator_v0` as a conditional discriminator, not spinor admission.
6. Keep `quantum_hopfield_qca_entropy_information_v0` as a diagonal/open-channel fixture until independent legs and non-diagonal branches exist.
7. Extract specs for overview-only Levos targets before coding them.
8. Update the manifold layer ledger only by row, with actual artifact paths.

## 14. Stop Conditions

Stop and write a blocked-reason artifact instead of continuing if:

1. A worker tries to use downstream language to fill an `M(C)` gap.
2. A result JSON predates its source or lacks source hash.
3. A sim has a load-bearing tool claim but no capability probe/audit.
4. A negative control does not fire.
5. A gate passes only because it did not scan the real source/spec/result surface.
6. A worker reports `FULL`, `done`, `complete`, `admitted`, `Axis0`, `bridge`, `engine`, or `physics` while `make stage-gate` still blocks that claim.
7. A stronger carrier is installed without running the weaker-object discriminator.

## 15. Summary

The real plan is foundation-first and bounded:

```text
root distinguishability
-> finite support/probes
-> quotient S/~_P
-> explicit M(C)
-> MSS/forced-or-installed discriminator
-> ring-checkerboard support consistency
-> typed entropy/readout co-ratchet
-> spinor/lift discriminator only when quotient-erased distinctions are load-bearing
-> QCA/Hopfield memory fixture only under finite support and typed readouts
-> layer rows completed one by one
-> same-carrier geometry micro-legos
-> only then terrain/operator/axis/bridge candidates
```

Anything else is trim-and-paint commentary before the foundation is poured.
