# A1_SECOND_SUBSTRATE_ENRICHMENT_FAMILY__v1
Status: PROPOSED / NONCANONICAL / SECOND CAMPAIGN SCAFFOLD
Date: 2026-03-06
Role: Pass-2 substrate enrichment family above the proven five-term base

## 1) Purpose
This is the next substrate-family target after the five-term base:
- `finite_dimensional_hilbert_space`
- `density_matrix`
- `probe_operator`
- `cptp_channel`
- `partial_trace`

It adds the smallest operator-level enrichment set that:
- already has runtime SIM support
- mostly stays inside the current L0 lexeme seed
- avoids the earlier superoperator/Hopf/axis inflation

## 2) Pass-2 Target Terms
Primary pass-2 enrichment terms:
1. `unitary_operator`
2. `commutator_operator`
3. `hamiltonian_operator`
4. `lindblad_generator`

Optional pass-2 compound capstone after the four terms survive:
5. `finite_dimensional_density_matrix_partial_trace_cptp_channel_unitary_operator`

## 3) Why This Family
Why these terms:
- `unitary_operator`, `commutator_operator`, `hamiltonian_operator`, and `lindblad_generator` already have dedicated SIM support in the current runtime
- their lexemes are already largely represented in the current L0 seed
- they extend the substrate into operator dynamics/control structure without jumping into:
  - superoperators
  - measurement stacks
  - Kraus families
  - eigenvalue/entropy overlays
  - Hopf/manifold/axis claims

## 4) Ordering Rule
Recommended order:
1. `unitary_operator`
2. `commutator_operator`
3. `hamiltonian_operator`
4. `lindblad_generator`
5. optional compound capstone only after the above survive

Reason:
- `unitary_operator` is the cleanest first extension
- `commutator_operator` pressures noncommutation explicitly
- `hamiltonian_operator` and `lindblad_generator` should only sit on top of that operator substrate

## 5) Required Family Shape
This pass-2 family should still use one family/path campaign:
- primary ordered branch
- alternatives that weaken one enrichment term at a time
- explicit negative branches
- graveyard rescue branches
- expected failure modes
- lineage
- SIM hooks

## 6) Explicit Negative Pressure
At minimum keep pressure on:
- `COMMUTATIVE_ASSUMPTION`
- `CLASSICAL_TIME`
- `PRIMITIVE_EQUALS`
- `INFINITE_SET`
- `KERNEL_VALID_BUT_MODEL_EMPTY`

Important caution:
- `hamiltonian_operator` and `lindblad_generator` must not silently import classical time or trajectory semantics

## 7) Explicit Deferrals
Still defer:
- `left_action_superoperator`
- `right_action_superoperator`
- `liouvillian_superoperator`
- `kraus_operator`
- `kraus_channel`
- `measurement_operator`
- `observable_operator`
- `projector_operator`
- `eigenvalue_spectrum`
- `density_purity`
- `density_entropy`
- `hopf_fibration`
- `hopf_torus`
- nested Hopf-tori conjunctions
- axis orthogonality claims

## 8) Main Goal
The goal of pass 2 is not broad expansion.
It is to prove the system can enrich the base substrate with the next clean operator family without reopening first-family inflation.

This current pass-2 ladder is still a scaffold run family, not the final graveyard-rich validity mode for the enrichment set.

Validity-mode requirement later:
- the family must tolerate graveyard-first pressure
- the whole enrichment model may need to enter graveyard competition first
- negative sims must be richer than the current minimal packet proofs
- rescue structure must be substantive, not just present
- use `A1_GRAVEYARD_FIRST_VALIDITY_PROFILE__v1` as the standard stricter follow-up profile

## 9) Runtime Result
Normalized family sources:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__SUBSTRATE_ENRICHMENT_FAMILY__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__SUBSTRATE_ENRICHMENT_FAMILY__v1.md`

First packet proof for the pass-2 family succeeded for the first ordered term:
- `unitary_operator`

Evidence:
- represented in the substrate-enrichment family anchor

Observed outcome:
- `unitary_operator` reached `CANONICAL_ALLOWED`
- the previous `left_action_superoperator` / `right_action_superoperator` inflation was removed by the minimal pass-2 math surface
- no extra helper term was admitted in this first pass-2 proof

Implication:
- keep the pass-2 order unchanged
- advance next to `commutator_operator`
- do not re-open superoperator or compound capstone terms until the single-term ladder survives in order

Second packet proof for the pass-2 family also succeeded for the next ordered term:
- `commutator_operator`

Evidence:
- represented in the substrate-enrichment family anchor

Observed outcome:
- `commutator_operator` reached `CANONICAL_ALLOWED`
- no auxiliary helper term was admitted
- the minimal pass-2 surface remains stable at the second rung

Next immediate target:
- `hamiltonian_operator`

Additional caution:
- `hamiltonian_operator` is the first pass-2 term with a higher risk of silent time/dynamics leakage
- keep the negative pressure concentrated on `CLASSICAL_TIME`, `COMMUTATIVE_ASSUMPTION`, and `PRIMITIVE_EQUALS`

Concept-local graveyard-first validity seed result:

Evidence:
- concept-local seed anchor:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__SUBSTRATE_ENRICHMENT_FAMILY__v1.md`
- normalized regeneration witness:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__SUBSTRATE_ENRICHMENT_FAMILY__v1.md`

Observed outcome:
- exact enrichment-family terms admitted under concept-local pressure:
  - `unitary_operator`
  - `commutator_operator`
  - `hamiltonian_operator`
  - `lindblad_generator`
- no broad-fuel spillover terms were admitted
- real graveyard/negative structure was created:
  - `graveyard_count = 36`
  - `kill_log_count = 36`
  - `sim_registry_count = 52`
- semantic/math substance gate passed in `graveyard_fill`
- run stopped at `STOPPED__PACK_SELECTOR_FAILED` before first executed cycle
- wrapper status is `PASS__CONCEPT_LOCAL_SEED_SATURATED`

Interpretation:
- this should be read as a concept-local enrichment-seed saturation result, not as a transport failure
- it proves the exact four-term enrichment family can survive concept-local graveyard/negative pressure cleanly enough to saturate the local selector
- it does not yet count as final enrichment-family validity closure

Focused dynamics-local follow-up:

Evidence:
- represented in the substrate-enrichment family anchor

Observed outcome:
- exact target terms remained allowed:
  - `hamiltonian_operator`
  - `lindblad_generator`
- `graveyard_count = 17`
- `kill_log_count = 17`
- `sim_registry_count = 25`
- semantic/math substance gate passed in `graveyard_fill`
- wrapper status is `PASS__CONCEPT_LOCAL_SEED_SATURATED`
- stop reason is `STOPPED__PACK_SELECTOR_FAILED`

Interpretation:
- this is a focused time/dynamics leakage pressure result, not a full enrichment-family closure
- the targeted pair survives concept-local graveyard pressure strongly enough to exhaust the local selector before an executed cycle
- it is best read as dynamics-local seed saturation

Bridge-profile follow-up:

Evidence:
- represented in the substrate-enrichment family anchor

Observed outcome:
- `executed_cycles = 1`
- wrapper status is `PASS__EXECUTED_CYCLE`
- `graveyard_count = 144`
- `kill_log_count = 144`
- `sim_registry_count = 232`
- exact target terms were **not** left in `CANONICAL_ALLOWED`
  - `hamiltonian_operator`
  - `lindblad_generator`

Interpretation:
- widening from concept-local rescue to bridge-level rescue is enough to recover an executed cycle
- it is not strict enough to preserve target specificity for the two dynamics terms
- treat this as negative evidence against using the bridge profile as the default strict dynamics-validity mode

Cluster-clamped seeded continuation result:

Evidence:
- represented in the substrate-enrichment family anchor

Observed outcome:
- `executed_cycles = 2`
- wrapper status is `PASS__PATH_BUILD_SATURATED`
- exact target terms remain primary admitted terms:
  - `hamiltonian_operator`
  - `lindblad_generator`
- witness-only enrichment companions remain present:
  - `unitary_operator`
  - `commutator_operator`
- no non-bridge residue terms are present
- `graveyard_count = 35`
- `kill_log_count = 35`
- `sim_registry_count = 51`

Interpretation:
- this is the missing family-specific executed-cycle counterpart to the earlier loose bridge profile
- the seeded cluster-clamp run recovers real execution while preserving specificity inside the four-term enrichment family
- best current read:
  - concept-local profiles prove strict seed saturation
  - bridge profile is useful negative evidence
  - cluster-clamped seeded continuation proves family-specific `path_build` execution up to saturation
- a fresh seeded continuation also saturates immediately after the seeded floor:
  - represented in the substrate-enrichment family anchor
  - wrapper status: `PASS__PATH_BUILD_SATURATED`
  - exact primary admitted terms remain:
    - `hamiltonian_operator`
    - `lindblad_generator`
  - witness-only terms remain:
    - `unitary_operator`
    - `commutator_operator`
- current best read:
  - the enrichment-family `T2_OPERATOR` lane is active / execution-proven under the current family fence
  - the seeded cluster-clamp route is now locally saturated under that fence
  - broader rescue closure should not be treated as the current next bottleneck

## 10) Default Admissibility Block
Apply the live family judgment explicitly on this lane:

- `executable_head`
  - `hamiltonian_operator`
  - `lindblad_generator`

- `active_companion_floor`
  - none beyond the two active dynamics heads on the current `T2_OPERATOR` lane

- `late_passengers`
  - none

- `witness_only_terms`
  - `unitary_operator`
  - `commutator_operator`

- `residue_terms`
  - none

- `landing_blockers`
  - do not treat broader bridge-style widening as the next move for this family
  - do not reopen compound-capstone or superoperator inflation from a locally saturated dynamics lane

- `witness_floor`
  - `unitary_operator`
  - `commutator_operator`

- `current_readiness_status`
  - `hamiltonian_operator = HEAD_READY`
  - `lindblad_generator = HEAD_READY`
  - `unitary_operator = WITNESS_ONLY`
  - `commutator_operator = WITNESS_ONLY`

## 11) Machine-Readable Admissibility Hints
```json
{
  "schema": "A1_ADMISSIBILITY_HINTS_v1",
  "family": "substrate_enrichment_t2_operator",
  "activation_terms": [
    "unitary_operator",
    "commutator_operator",
    "hamiltonian_operator",
    "lindblad_generator"
  ],
  "strategy_head_terms": [
    "hamiltonian_operator",
    "lindblad_generator"
  ],
  "forbid_strategy_head_terms": [
    "unitary_operator",
    "commutator_operator"
  ],
  "late_passenger_terms": [],
  "witness_only_terms": [
    "unitary_operator",
    "commutator_operator"
  ],
  "residue_only_terms": [],
  "landing_blocker_overrides": {
    "unitary_operator": "Earlier rung survivor; retain as a witness-only enrichment companion inside the active T2_OPERATOR lane.",
    "commutator_operator": "Earlier rung survivor; retain as a witness-only enrichment companion inside the active T2_OPERATOR lane."
  }
}
```

## 12) Integration Batch Companion
For the normalized cross-family read of this lane, use:
- `system_v3/a1_state/A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1.md`
- `system_v3/a1_state/A1_INTEGRATION_BATCH__ANCHOR_WITNESS_WORKFLOW__v1.md`
