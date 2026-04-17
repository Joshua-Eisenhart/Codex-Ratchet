# QIT Engine Proto Ratchet and Sim Plan

Status: working plan
Purpose: define the immediate scientific program for getting the QIT engine prototype properly ratcheted and simulated before broad Axis or full-v5 inflation

This document exists because the immediate priority is not “finish the whole system.”
The immediate priority is to get the QIT engine prototype simulated in a way that is rich, honest, and scientifically respectable enough to matter.

---

## 1. Core mission

Build a legitimate pre-Axis QIT engine simulation substrate from the root constraints upward.

That means:
- start from the constraints
- ratchet admissible math and geometry step by step
- build small sims as legos
- make them real enough to count
- compose upward carefully
- finish the pre-Axis ladder before real Axis-entry work

---

## 2. Why this comes first

### 2.1 Scientific reason
The QIT engine prototype is the immediate scientific substrate.
It is the first thing that has to become legitimate enough to:
- support serious reasoning
- attract collaborators
- justify broader system work
- justify funding
- show that the system is more than narrative architecture

### 2.2 Architectural reason
The broader system should eventually inherit the shape of the QIT engines.
The graphs, architecture, and later system layers should reflect the engine and its constraints.
So the engine has to be made real first.

### 2.3 Practical reason
Sims are affordable.
They do not prove the model true.
But they can:
- make the work more legitimate
- narrow branches honestly
- support outside engagement
- make later work more disciplined

---

## 3. What this plan is not

This plan is not:
- final proof of the full model
- final proof of physics claims
- full v5 closure
- full Axis 0 closure
- an excuse to narrate away missing lower tiers

This is a pre-Axis scientific substrate plan.

---

## 4. Central model commitments for the sim program

### 4.1 Constraints do not generate geometry
The root constraints do not directly generate the geometry.
They progressively restrict admissible math and admissible geometry.

### 4.2 Geometry is nested
Broader carriers remain real hosting layers for narrower structures.
The ladder is not replacement by collapse.
It is progressive admissibility/narrowing.

The stronger current chain is:
- constraints
- admissibility charter `C`
- admissible manifold `M(C)`
- geometry buildup on `M(C)`
- Weyl working layer
- bridge family `Xi`
- cut family `A|B`
- kernel family `Phi_0(rho_AB)`

### 4.3 Bridge and cut are separate open layers
The bridge problem and the cut problem must not be collapsed.

- bridge layer: how geometry/history lands in a bipartite cut-state `rho_AB`
- cut layer: what the legitimate partition `A|B` actually is
- kernel layer: what `Phi_0(rho_AB)` should be once a legitimate cut-state exists

These are related, but they are not the same question.

### 4.4 Pre-Axis work is core work
Carrier, geometry, bridge, cut, transport, chirality, negatives, placement, and witness discipline are not optional scaffolding.
They are the actual lower scientific program.

### 4.5 Axis work comes later
Axis 0 must sit after a genuinely admitted lower stack.

---

## 5. Central method

### 5.1 Lego sim method
The simulation program is built from small sims as legos.

Each small sim should test a bounded structural claim and emit enough evidence to be composed upward later.

Each lego sim should also say which layer it is supporting:
- carrier
- geometry
- bridge
- cut
- kernel
- transport
- chirality
- placement
- negative

### 5.2 Ratchet method
The ratchet works by:
- testing admissibility
- killing disallowed structures
- keeping provisional survivors open
- keeping executable winners, doctrine-facing winners, and pointwise discriminators distinct when they differ
- composing only admitted or clearly fenced pieces upward

### 5.3 No toy closure
Reduced or flattened sims may still exist, but they are `diagnostic_only` unless they satisfy the richer contract required by the tier.

---

## 6. What a real lego sim must contain

Every lego sim should declare:
- `sim_id`
- `tier`
- `purpose`
- `root_constraints_in_force`
- `carrier_layer`
- `geometry_layer`
- `law_or_candidate_tested`
- `required_tools`
- `required_negatives`
- `required_artifacts`
- `pass_rule`
- `fail_rule`
- `promotion_status`
- `eligible_consumers` (what higher sims may consume it)

If these are absent, the sim is under-specified.

---

## 7. Pre-Axis tier ladder

## Tier 0 — Root constraints
Goal:
- establish mechanical admissibility restrictions
- no narrative-only constraint claims

Expected outputs:
- constraint objects
- admissibility/embargo checks
- witness traces

## Tier 1 — Finite carrier
Goal:
- establish admissible carrier families under the root constraints

Expected outputs:
- admitted carrier families
- explicit carrier negatives
- no free carrier inflation

## Tier 2 — Geometry
Goal:
- establish the nested geometry stack honestly enough to support later transport/chiral work

Expected outputs:
- explicit carrier ladder
- nested geometry structure
- reduced-geometry negatives
- graph/tensor/topology support where required

## Tier 3 — Transport
Goal:
- narrow transport law candidates under the admitted geometry stack

Expected outputs:
- surviving transport law family or bounded surviving branch set
- kills of fake or generic transport routes
- proof-pressure and branch-pressure artifacts

## Tier 4 — Differential / chirality / flux
Goal:
- narrow chiral/differential candidate structure without fake closure

Expected outputs:
- explicit surviving candidate(s) or explicit non-closure
- kills of fake lower-tier chiral laws
- rich chirality/tensor support

## Tier 5 — Negatives
Goal:
- explicit kill surfaces against disallowed or flattened structures

Expected outputs:
- negative witnesses
- counterexamples
- kill classifications

## Tier 6 — Placement / pre-entropy
Goal:
- explicit placement structure and downstream relation before Axis-entry

Expected outputs:
- placement law objects
- pre-entropy packet structure
- no prose-only packet closure
- explicit relation between bridge family, cut family, and later kernel use

## Tier 7 — Axis-entry
Goal:
- not to be run prematurely

Expected outputs:
- only allowed after lower closure criteria are met

Rule:
- if tiers 3–6 are open, Tier 7 remains embargoed

---

## 8. Tool requirements by scientific need

### 8.1 Proof pressure
Needed because LLMs and weak workflows will smooth things into classical closure.

Core proof/use stack:
- `z3`
- `cvc5`
- `hypothesis`
- `pytest`
- `differential_tester`
- `structured_fuzzer`
- `model_checker`
- `z3_cegis_refiner`
- `sympy`
- optionally `egglog`

### 8.2 Graph/tensor/chirality richness
Needed because the system is not meant to collapse into scalar toy state.

Core richness stack:
- `networkx`
- `PyG`
- `TopoNetX`
- `clifford`
- `pyquaternion`
- `torch`
- optionally `kingdon`, `hypernetx`, `xgi`

### 8.3 Topology-pressure
Needed because the ratchet is about narrowing admissible geometry, not just graph decoration.

Core topology-pressure stack:
- `gudhi`
- optionally `ripser.py`

---

## 9. What “pseudo-properly” should mean right now

The near-term goal is not perfection.
The near-term goal is a bounded, honest, rich enough scientific slice.

Pseudo-properly means:
- bounded
- honest
- tool-backed
- negative-tested
- witness/artifacted
- rich enough to matter
- not over-promoted

Pseudo-properly does NOT mean:
- flat toy sim
- narrative-only closure
- full-system claims from local evidence
- skipping the lower ladder because a script ran

---

## 10. First practical working target

The first target should be:
- one bounded full-geometry pre-Axis QIT prototype slice

Recommended shape:
1. explicit carrier ladder
2. left/right Weyl pair on admitted geometry
3. one real transport/chirality candidate family
4. one negative suite
5. one proof-pressure surface
6. one graph/writeback artifact

This is enough to “just see it work” without pretending the whole theory is done.

---

## 11. What counts as legit evidence right now

A result is more legitimate if it has:
- explicit constraints in force
- explicit geometry/carrier layer
- required tools actually used
- required negatives run
- witness trace
- graph/tensor artifacts where required
- explicit status: admitted / open / diagnostic / blocked

A result is less legitimate if it is:
- scalar-only
- graphless
- proofless
- negative-free
- under-specified
- missing branch status

---

## 12. Open-branch policy

Open branches must stay open until mechanically narrowed.

This means:
- non-admission != elimination
- only explicit kill or evidence-gated failure eliminates a branch
- unresolved structure should remain fenced, not normalized away
- higher layers may consume only what is admitted or explicitly fenced for that purpose

---

## 13. Promotion policy

A lego sim may be marked:
- `admitted`
- `keep but open`
- `audit further`
- `diagnostic_only`
- `broken`

General rule:
- underpowered sims are `diagnostic_only`
- no lower-tier closure without negatives and proof pressure
- no geometry/Axis promotion from flattened or reduced sims

---

## 14. Immediate practical work order

1. stabilize/install/use the proper proof/graph/geometry stack
2. make the lower lego sim contract explicit
3. classify existing pre-Axis sims honestly
4. repair or rebuild the key lower-tier sims
5. get one bounded rich prototype slice visibly working
6. then continue upward through the pre-Axis ladder

---

## 15. Relation to broader v5

The broader system should not outrun the QIT engine substrate.

What should happen is:
- QIT engine proto gets ratcheted properly
- pre-Axis sims become legitimate
- the system architecture later reflects this engine structure
- Hermes helps process and organize the work
- broader v5 growth comes after the substrate is real enough

---

## 16. What not to do yet

Do not:
- attempt full v5 closure first
- treat packet scores as enough
- promote Axis-entry early
- use broad prompts instead of bounded sim plans
- confuse “script ran” with “scientific substrate earned”
- let Hermes replace sims, negatives, proofs, or graph artifacts with prose

---

## 17. Likely next companion docs after this one

After this plan, the most useful next docs are likely:
- `CURRENT_PRE_AXIS_SIM_STATUS__KEEP_OPEN_DIAGNOSTIC_BROKEN.md`
- `LEGO_SIM_CONTRACT.md`
- `CURRENT_TOOL_STATUS__INSTALLED_VS_MISSING_VS_NOT_WIRED.md`

---

## 18. Current best summary

The immediate scientific mission is:
- make the QIT engine prototype real enough to count
- by building a ratcheted library of small, honest, tool-backed pre-Axis sims from the root constraints upward
- and only then composing upward into larger sims and later Axis work

That is the path to making the work more legitimate without pretending it is already proven.
