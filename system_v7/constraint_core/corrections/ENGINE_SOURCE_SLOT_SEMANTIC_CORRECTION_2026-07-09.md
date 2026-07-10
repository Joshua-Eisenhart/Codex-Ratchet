---
title: Engine source-slot semantic correction
date: 2026-07-09
status: source-grounded correction; legacy sims unchanged
claim_ceiling: documentation-only; scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false
---

# Engine Source-Slot Semantic Correction

## Verdict

The source-native engine object is:

```text
16 source slots
  = 2 chirality schedules x 2 loop roles x 4 terrain steps

each source slot
  = one terrain + one loop role + one Axis-6 sign + one native-emphasis operator

each source slot expands to four substages
  = Ti, Te, Fi, Fe

all four substages inherit the source slot's one Axis-6 sign
```

The native operator marks the phase/emphasis of the four-operator cycle. It does
not select the only operator allowed in that slot, eliminate the other three,
or create a second stage identity. Type1 and Type2 name the left- and
right-chirality schedules. They are not the Axis-6 bit and they are not aliases
for candidate-first versus measurement-first science-method order.

This correction narrows the meaning of four old greens. It does not erase their
local measurements, edit their code, or grant any promotion. Axis0 and global
engine admission remain **RED**.

## Owner-Source Lock

The direct owner record separates the objects explicitly:

- Type1 is the left-handed schedule with outer deduction and inner induction;
  Type2 reverses which loop carries induction/deduction. Axis 6 then supplies
  the per-stage up/down terrain-operator order
  (`READ ONLY Legacy core_docs/a2_feed_high entropy doc/grok gemini having digested the model.md:237-248`).
- Every stage has four substages, uses all four operators, and gives all four
  the same up/down sign
  (`READ ONLY Legacy core_docs/a2_feed_high entropy doc/grok gemini having digested the model.md:248-248`,
  repeated verbatim at
  `READ ONLY Legacy core_docs/a2_feed_high entropy doc/grok gemini having digested the model.md:2961-2969`).
- The owner restates the same object as eight stages per engine, four
  deductive and four inductive, with four same-Axis-6-signed substages per
  stage
  (`READ ONLY Legacy core_docs/a2_feed_high entropy doc/gpt thread a1 trigram work out .txt:39065-39075`).
- The source consolidation describes the native operator as the operator that
  "leads/emphasizes" the cycle, while the stage still executes four operators
  (`READ ONLY Legacy core_docs/a2_feed_high entropy doc/gpt thread a1 trigram work out .txt:45259-45267`).

The source tables preserve that reading mechanically:

- The 16-slot table stores `engine`, `loop`, `step`, `terrain`, exactly one
  `axis6_sign`, and exactly one `canonical_operator` per source slot. Type1-left
  occupies eight slots and Type2-right occupies eight slots
  (`system_v7/constraint_core/reference_docs/engine_math/source_schedule_tables/engine_16_source_stage_slots.json:1-225`).
- The 64-row table expands each source slot across Ti, Te, Fi, and Fe while
  retaining the slot's terrain and sign. Only the native-emphasis row carries
  the source token marker; the other three rows still exist as substages
  (`system_v7/constraint_core/reference_docs/engine_math/source_schedule_tables/engine_64_source_schedule.json:1-1154`).
- The table linter states and checks the exact invariant: 16 slots, one sign per
  slot, and a 16 x 4 expansion in which all four operators share that slot's
  terrain and sign
  (`system_v7/constraint_core/sims_and_scripts/schedule_source_fidelity_linter.py:40-74`).

The lower math supplies the non-conflation fences:

- Ti, Te, Fi, and Fe are the four maps; up/down create signed placements of
  those maps rather than eight new maps
  (`system_v5/ops/QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md:8-35`).
- Pair-readout order, Axis-6 composition order, and four-step loop order are
  three different order concepts
  (`system_v7/constraint_core/reference_docs/engine_math/igt-pattern-explicit-math-reference.md:25-30`).
- Candidate-first versus measurement-first is an explanatory gloss for the
  deductive/inductive loop-order family, and each engine contains one loop of
  each family
  (`system_v7/constraint_core/reference_docs/engine_math/igt-pattern-explicit-math-reference.md:300-334`).
- Type1 is left Weyl and Type2 is right Weyl; Type1 carries outer-deductive and
  inner-inductive, while Type2 carries outer-inductive and inner-deductive
  (`system_v7/constraint_core/reference_docs/engine_math/igt-pattern-explicit-math-reference.md:515-525`).
- Axis 6 distinguishes token precedence/action side and explicitly cannot, by
  itself, define chirality, loop order, operator family, or engine type
  (`system_v5/ops/AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md:1242-1297`).

## Correct Semantic Schema

Let `S` be the 16 source slots and let:

```text
OPS = (Ti, Te, Fi, Fe)

s in S = {
  slot_id,
  engine_chirality,   # Type1_left | Type2_right
  loop_role,          # outer_deductive | inner_inductive |
                      # outer_inductive | inner_deductive
  step,
  terrain,
  axis6_sign,         # up | down; one value for the whole source slot
  native_operator     # phase/emphasis marker in OPS
}
```

The only source-faithful four-substage expansion is:

```text
substages(s) = [
  (s, Ti, s.axis6_sign, Ti == s.native_operator),
  (s, Te, s.axis6_sign, Te == s.native_operator),
  (s, Fi, s.axis6_sign, Fi == s.native_operator),
  (s, Fe, s.axis6_sign, Fe == s.native_operator),
]
```

For every `O in OPS`, the inherited Axis-6 sign determines the same composition
orientation:

```text
up:   stage_map(s, O, rho) = Phi_terrain_s(O(rho))
down: stage_map(s, O, rho) = O(Phi_terrain_s(rho))
```

Thus a source slot is not `(terrain, both signs)`, and it is not
`(terrain, one member of a native pair)`. The slot already has a chirality/loop
seat and one sign. The four operators are its substages. `native_operator`
marks the cycle's source phase/emphasis; it is not an admissibility filter.

This is a semantic schema. Whether the native emphasis should be implemented as
cycle rotation, weighting, a drive/control distinction, or another finite map
is a separate dynamical question. No invented `native` casing is admitted by
this document.

## UP-130 Does Not Derive Four

The later `four_substages_emerge_from_dual_ratchet_sim.py` claim is rejected for
its exact audited source hash. Its central predicate requires exactly two `A`
and two `B` symbols
(`system_v7/constraint_core/sims_and_scripts/four_substages_emerge_from_dual_ratchet_sim.py:76-79`).
That condition fixes the word length to `2 + 2 = 4` before the length scan, so
the scan cannot independently derive four
(`system_v7/constraint_core/sims_and_scripts/four_substages_up130_fabrication_audit_sim_results.json:85-112`).

The other claimed mechanisms also fail their stated interpretation:

- `exp(-i*pi*sigma/2)` induces a 180-degree Bloch rotation, not a quarter-turn
  (`system_v7/constraint_core/sims_and_scripts/four_substages_up130_fabrication_audit_sim_results.json:114-168`);
- the two adjoint Pauli channels commute to numerical tolerance, so the packet
  has no order-sensitive dual-ratchet channel
  (`system_v7/constraint_core/sims_and_scripts/four_substages_up130_fabrication_audit_sim_results.json:170-176`);
- all audited legs are unitary and change von Neumann entropy by at most
  `3.89e-16` nats, so the entropy-sector ratchet is only a label
  (`system_v7/constraint_core/sims_and_scripts/four_substages_up130_fabrication_audit_sim_results.json:324-358`);
- `ABAB` and `BABA` are one cyclic orbit, not two cyclic chiralities
  (`system_v7/constraint_core/sims_and_scripts/four_substages_up130_fabrication_audit_sim_results.json:61-83`);
- the declared controls do not isolate the claimed conditions
  (`system_v7/constraint_core/sims_and_scripts/four_substages_up130_fabrication_audit_sim_results.json:203-308`); and
- matching the already-four-step chart to the already-count-four predicate is
  circular consistency, not an independent architecture derivation
  (`system_v7/constraint_core/sims_and_scripts/four_substages_up130_fabrication_audit_sim_results.json:178-201`).

The fabrication audit passes as an overclaim detector and rejects the target
claim; it does not supply a replacement derivation
(`system_v7/constraint_core/sims_and_scripts/four_substages_up130_fabrication_audit_sim_results.json:24-57`,
`system_v7/constraint_core/sims_and_scripts/four_substages_up130_fabrication_audit_sim_results.json:360-394`).

## Current Source-Faithful Consumer

`system_v7/sims/dual_ratchet_stage_interior_learning_v0/` is the first bounded
consumer in this correction lane that directly realizes all 16 source slots,
expands each slot across Ti/Te/Fi/Fe, gives all four the slot's one Axis-6 sign,
and emits 32 microsteps per engine. Its combined PyTorch/JAX validator passes
all 22 artifact-integrity checks
(`system_v7/sims/dual_ratchet_stage_interior_learning_v0/results/dual_ratchet_stage_interior_learning_v0_validation.json:2-32`).

Its scientific gate remains red. PyTorch does not select a seed-stable Type-2
cycle, and the independent JAX scoring implementation finds the Type-2 ranking
unstable or tied under its declared 1,080-scenario sweep. Type 1's local
`Ti, Fe, Fi, Te` candidate survives; Type 2 does not. The result is therefore a
source-faithful, explicit 64-microstep **candidate carrier**, not a derivation
of universal four, a canonical per-stage order, canonical engines, or Axis0
(`system_v7/sims/dual_ratchet_stage_interior_learning_v0/results/dual_ratchet_stage_interior_learning_v0_validation.json:34-47`).

## Legacy Green 1: `engine_64_schedule_definition_sim.py`

### What the green actually validated

The sim defines its stage as `(terrain, sign)` and builds the full cross-product
`(terrain, sign, operator)`
(`system_v7/constraint_core/sims_and_scripts/engine_64_schedule_definition_sim.py:7-13`,
`system_v7/constraint_core/sims_and_scripts/engine_64_schedule_definition_sim.py:87-93`).
Under its chosen finite GKSL terrain maps and probes, it measured:

- 16 constructed terrain/sign rows and 64 constructed entries;
- all four operators present in each constructed terrain/sign row;
- up/down composition differences under the nontrivial terrain drive;
- collapse of that order difference under the no-drive control; and
- 64 distinct channel signatures under that probe battery, with a
  single-operator control reducing the count.

Those checks are implemented at
`system_v7/constraint_core/sims_and_scripts/engine_64_schedule_definition_sim.py:95-154`,
and the stored green reports the corresponding values at
`system_v7/constraint_core/sims_and_scripts/engine_64_schedule_definition_sim_results.json:2-21`.

### What it did not validate

It did **not** validate the owner's 16 source slots. Its 16 rows are
`8 terrains x both Axis-6 signs`; the source rows are
`2 chirality schedules x 2 loop roles x 4 steps`, each already carrying one
sign. The code has no engine chirality, loop-role, step, or native-emphasis
field in its stage key
(`system_v7/constraint_core/sims_and_scripts/engine_64_schedule_definition_sim.py:87-93`).

Therefore its green supports an overcomplete terrain/sign/operator cross-product
diagnostic. It does not establish source-schedule fidelity, native phase,
Type1/Type2 semantics, or global engine closure. The result's own classification
remains `scratch_diagnostic` with `promotion_allowed: false`
(`system_v7/constraint_core/sims_and_scripts/engine_64_schedule_definition_sim_results.json:2-4`).

## Legacy Green 2: `sixteen_intelligences_substages_terrain_ratchet_sim.py`

### What the green actually validated

The sim creates 16 constructed rows as `8 terrains x 2 entries from NATIVE[t]`
(`system_v7/constraint_core/sims_and_scripts/sixteen_intelligences_substages_terrain_ratchet_sim.py:49-84`).
On that constructed object it measured:

- 16 distinct processing fingerprints under the selected terrain/operator maps;
- four effective, ordered, distinct outputs under an invented native-dependent
  casing;
- separation of Ti/Te entropy-changing dephasings from Fi/Fe
  entropy-preserving rotations; and
- monotone coherence loss under repeated application of the selected native
  dephasing operator.

The casing experiment is at
`system_v7/constraint_core/sims_and_scripts/sixteen_intelligences_substages_terrain_ratchet_sim.py:111-167`;
the dephasing/rotation and monotone-pinch checks are at
`system_v7/constraint_core/sims_and_scripts/sixteen_intelligences_substages_terrain_ratchet_sim.py:169-223`;
the stored green is at
`system_v7/constraint_core/sims_and_scripts/sixteen_intelligences_substages_terrain_ratchet_sim_results.json:2-39`
and
`system_v7/constraint_core/sims_and_scripts/sixteen_intelligences_substages_terrain_ratchet_sim_results.json:203-207`.

### What it did not validate

It did **not** validate 16 source slots: the second coordinate of `STAGES` is a
member of a two-operator native pair rather than chirality/loop/step identity.
It also did not execute an Axis-6 comparison in the four-substage lane.
`substages_of(t, o)` has no sign argument; it flows the terrain once and then
applies four native-cased operators
(`system_v7/constraint_core/sims_and_scripts/sixteen_intelligences_substages_terrain_ratchet_sim.py:121-132`).

Consequently:

- the green for four cased outputs is not a green for four same-sign
  terrain/operator compositions;
- `casing_frame(o)` is an experimental construction, not source-native
  evidence for what `native` means;
- the measured T/F entropy split is an Axis-5 operator-family result, not "two
  signed types" under Axis 6; and
- the 16-fingerprint count is not evidence for the Type1-left/Type2-right source
  schedule.

The useful local measurements survive at `scratch_diagnostic`; the engine-stage
semantics do not.

## Legacy Green 3: `qit_full_type1_type2_64_live_v1`

### What the green actually validated

This packet explicitly defines its four substages as `candidate`, `measurement`,
`gate`, and `receipt`
(`system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1_common.py:43-68`).
It repeats each macro row across those four incremental observation schemas
(`system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1_common.py:367-391`).
The resulting green
validated, for that metadata carrier:

- 16 macro rows repeated to 64 metadata slots and split 32/32 by Type label;
- recovery of four ordered loop-object IDs;
- collapse of object identity under bag/static erasures;
- JAX/Julia/PyTorch agreement on the bounded object count; and
- SMT polarity for the packet's count/recovery gate.

The controller's actual gate is at
`system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1.py:188-213`.
The result records `all_pass: true` at
`system_v7/sims/qit_full_type1_type2_64_live_v1/results/qit_full_type1_type2_64_live_v1_results.json:24-24`
and the constructed counts at
`system_v7/sims/qit_full_type1_type2_64_live_v1/results/qit_full_type1_type2_64_live_v1_results.json:1732-1739`.
The envelope correctly keeps the claim on an atlas-derived ordered-object
carrier
(`system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1_envelope.py:127-151`).

### What it did not validate

`candidate/measurement/gate/receipt` are not the source engine substages. The
four substages are Ti/Te/Fi/Fe. The packet repeats the macro row's one operator
family across all four metadata phases instead of executing all four operators.
It therefore did not validate:

- the source-native 16 x 4 operator schedule;
- one inherited Axis-6 sign applied to all four operators in each source slot;
- native phase/emphasis versus the three supporting operator phases;
- chirality dynamics; or
- any engine, Axis0, FEP, manifold, physics, or runtime admission.

The README already calls the atlas non-final and fences those broader claims
(`system_v7/sims/qit_full_type1_type2_64_live_v1/README.md:57-62`). The envelope
also classifies the green as `scratch_diagnostic` and lists Axis0/global
consumers as out of scope
(`system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1_envelope.py:127-151`).

## Legacy Green 4: `qit_bidirectional_science_type1_type2_v0`

### What the green actually validated

This packet defines two finite **method algorithms**:

```text
candidate -> measurement -> counter_projection -> update -> falsifier -> receipt
measurement -> candidate -> counter_projection -> update -> falsifier -> receipt
```

The implementations are at
`system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0_common.py:108-177`
and
`system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0_common.py:195-268`.
On four projection object cards and five views, its green validated
candidate-first confirmation accuracy, measurement-first reconstruction
accuracy, wrong-candidate/erasure controls, and three-runtime agreement for that
method comparison
(`system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0_common.py:298-365`).
The stored result reports `all_pass: true`, Type1-method accuracy `1.0`, and
Type2-method accuracy `0.9`
(`system_v7/sims/qit_bidirectional_science_type1_type2_v0/results/qit_bidirectional_science_type1_type2_v0_results.json:24-49`,
`system_v7/sims/qit_bidirectional_science_type1_type2_v0/results/qit_bidirectional_science_type1_type2_v0_results.json:253-265`).

### What it did not validate

The packet assigns `Type-1` to candidate-first and `Type-2` to
measurement-first in its constants and method records
(`system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0_common.py:42-50`,
`system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0_common.py:165-176`,
`system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0_common.py:254-267`).
That naming is not source-native engine typing.

Actual Type1 and Type2 are chirality schedules, and **each contains both** a
deductive and an inductive loop. Candidate-first/measurement-first may remain a
bounded science-method comparison, but it must use neutral method names and
cannot stand in for engine chirality. The green therefore says nothing about
Type1-left versus Type2-right dynamics, four operator substages, native
emphasis, or Axis-6 schedule fidelity.

The packet's own controller limits the claim to a finite method scout and
blocks full QIT engine and Axis0 admission
(`system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0.py:199-247`).
The envelope's cross-engine agreement is agreement on this method object, not
independent confirmation of the source engine semantics
(`system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0_envelope.py:121-163`).

## Current Source-Faithful Learning And Independent Oracles

`system_v7/sims/dual_ratchet_stage_interior_learning_v0` now executes the
corrected structural contract rather than merely describing it. PyTorch runs
both engine charts, all six oriented Ti/Te/Fi/Fe cycles, and three seeds while
preserving one Axis-6 sign across the four phases of every source slot. Type 1
selects `Ti>Fe>Fi>Te` on all three seeds. Type 2 splits between
`Ti>Te>Fi>Fe` and `Ti>Te>Fe>Fi`, so the local scientific gate is red.

The independent JAX sweep reproduces the PyTorch scores and evaluates 1,080
scenarios / 6,480 cycle scores. Type 1 wins 540/540 without ties. Type 2's
reference wins 385/540, the main competitor 142/540, a third cycle 13/540,
and eight scenarios tie. All 18 mechanical/destructive controls pass; the
scientific verdict remains `cycle_ranking_unstable_or_tied_under_declared_jax_sweep`.

`system_v7/sims/stage_interior_spectral_kinetic_discriminator_v0` gives a
shared hashed trajectory contract independently to PyDMD and deeptime. Their
clean held-out accuracies are `1.0` and `0.9444444444`; temporal shuffle,
block permutation, and reversal collapse near chance. This earns finite
distinguishability of the two supplied Type-2 orders, not selection of truth.

`system_v7/sims/alco_j3o_exact_oracle_v0` passes ALCO's six-file upstream GAP
suite with zero failures and 23/23 local exact gates over five frozen J3(O)
cases. That earns exact finite Albert-algebra oracle parity only. It supplies
no spectral logarithm, entropy, positive map, DPI, engine, Axis0, perception,
object, or physics result.

`system_v7/sims/qics_entropy_dpi_numeric_oracle_v0` passes 11/11 producer
checks and a byte-identical rerun under pinned QICS 1.1.3. Nine optimal solves
agree with direct spectral Umegaki relative entropy within
`8.16396894531835e-10`; six pinching/depolarizing cases contract, while six
invalid-map controls are rejected before solving. This earns a bounded
associative relative-entropy/DPI numerical oracle only. It does not supply the
missing J3(O) spectral logarithm, Jordan-positive map, or exceptional DPI.

`system_v7/sims/dual_ratchet_substage_survivor_discovery_v0` removes the four
operator names from independent geometry and entropy selectors. Julia and JAX
both find four quotient classes from six survivors inside the finite Pauli
registry, but the preregistered generic-axis challenge finds eight classes
from ten survivors. Foundational-four emergence, a history-dependent dual
ratchet, and per-stage four substages therefore remain false.

Packet 107 reruns `141/0/0`, but its two additions do not alter an engine file.
The independent audit at
`system_v7/constraint_core/external_packet_audits/packet_107_20260709` rejects
both promotions. Current MUSE-DARK III evidence reports increasing
characteristic `a0` and evolution faster than `H(z)`, contradicting the
packet's constant/de-Sitter selection. Its pole `-2*pi` is a gauge-dependent
connection integral over a constant projective ray; the endpoint-corrected
geometric phase is zero. Neither result moves Axis0 or the schedule.

These packets strengthen the implementation and falsification surface without
altering the source correction: four operators and the searched cycles remain
premises, and Type 2 remains unresolved.

## Axis0 And Global Admission

**RED stays RED.** The source math says the local Axis0 chart seat exists but
the final bridge seat remains open
(`system_v5/ops/AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md:138-152`). The final
`Phi_0(rho_AB)` requires a still-open `Xi -> rho_AB` bridge and a cut-state
discriminator
(`system_v5/ops/AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md:204-231`); claiming
Axis0 while `Xi` is absent is an explicit falsifier
(`system_v5/ops/AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md:286-301`).

The four old greens already carry lower ceilings:

| Artifact | On-disk ceiling |
|---|---|
| `engine_64_schedule_definition_sim` | `scratch_diagnostic`; promotion false (`system_v7/constraint_core/sims_and_scripts/engine_64_schedule_definition_sim_results.json:2-4`) |
| `sixteen_intelligences_substages_terrain_ratchet_sim` | `scratch_diagnostic`; promotion false (`system_v7/constraint_core/sims_and_scripts/sixteen_intelligences_substages_terrain_ratchet_sim_results.json:2-4`) |
| `qit_full_type1_type2_64_live_v1` | formal admission false; Axis0 blocked (`system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1.py:220-247`, `system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1.py:282-290`) |
| `qit_bidirectional_science_type1_type2_v0` | formal/release admission false; Axis0 blocked (`system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0.py:199-239`, `system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0.py:285-286`) |

No local green in this correction is evidence for:

- Axis0 admission;
- source-native 64-slot dynamic closure;
- full QIT engine admission;
- manifold, FEP, physics, cognition, ontology-writer, MMM-driver, or Lev runtime
  admission; or
- global/canonical engine completion.

## Downstream Use Rule

Until a corrected source-slot consumer is built and rerun, cite the old greens
only as follows:

| Old green | Allowed surviving description |
|---|---|
| `engine_64_schedule_definition_sim` | terrain x both-sign x operator cross-product channel diagnostic |
| `sixteen_intelligences_substages_terrain_ratchet_sim` | native-casing experiment plus Axis-5 dephasing/rotation and monotone-pinch diagnostic |
| `qit_full_type1_type2_64_live_v1` | ordered metadata-object recovery and erasure-control scout |
| `qit_bidirectional_science_type1_type2_v0` | candidate-first versus measurement-first finite method scout |

A source-faithful engine sim must consume the 16 source slots directly, expand
each slot across Ti/Te/Fi/Fe, inherit exactly one Axis-6 sign across those four
rows, retain native as phase/emphasis metadata unless a separate dynamical test
earns more, and keep Type1-left/Type2-right chirality separate from both Axis 6
and science-method order. The current learned packet now satisfies that
structural contract, but its red scientific gates mean the dynamics and order
remain candidates rather than admitted engine architecture.
