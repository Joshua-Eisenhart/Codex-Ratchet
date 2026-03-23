# A2-2 REFINED CANDIDATES

## Candidate 1: DETERMINISTIC_PROOF_SINGLE_WITNESS_SHELL

- status: `A2_2_CANDIDATE`
- type: `proof-family shell`
- claim:
  - `prove_foundation.py` should remain a one-file deterministic proof-family shell rather than being widened into a broader theorem packet or merged back into nearby diagnostic residue
- source lineage:
  - parent batch: `BATCH_sims_prove_foundation_proof_family__v1`
  - parent basis: cluster A, distillate D1, candidates C1-C3
- retained boundary:
  - one source member only
  - one local SIM_ID only

## Candidate 2: LOCAL_PROOF_EMISSION_WITHOUT_ADMISSION

- status: `A2_2_CANDIDATE`
- type: `provenance-strength packet`
- claim:
  - the proof emits one local `SIM_EVIDENCE v1` block for `S_FOUNDATION_PROOF`, but it has no catalog admission and no top-level evidence-pack admission, so local proof emission must stay weaker than repo-top visibility and much weaker than earned result lineage
- source lineage:
  - parent basis: tension T1, distillate D5, candidate C5
  - comparison anchor:
    - `BATCH_A2MID_sims_residual_coverage_split__v1`
- retained contradiction marker:
  - local proof emission exists
  - top-level admission does not

## Candidate 3: GATED_EXECUTABLE_WITNESS_CONTRACT

- status: `A2_2_CANDIDATE`
- type: `executable witness packet`
- claim:
  - the proof should be retained as a gated executable witness, because its local evidence emits only when noncommutation, subsystem mixedness, and trace preservation all hold rather than existing as unconditional prose or unconditional artifact output
- source lineage:
  - parent basis: cluster E, tension T2, distillate D6, candidate C2
- retained contradiction marker:
  - deterministic logic survives
  - evidence output still remains condition-gated

## Candidate 4: PAULI_NONCOMMUTATION_WITNESS_PACKET

- status: `A2_2_CANDIDATE`
- type: `operator witness packet`
- claim:
  - the proof’s first reusable core is the explicit Pauli `X`/`Z` commutator witness, which should stay concrete and executable rather than being abstracted into generic noncommutation language only
- source lineage:
  - parent basis: cluster B, distillate D2, candidate C3
- retained boundary:
  - operator-level witness stays explicit

## Candidate 5: GLOBAL_PURE_LOCAL_MIXED_BELL_SEAM

- status: `A2_2_CANDIDATE`
- type: `entanglement witness packet`
- claim:
  - the Bell-state section should be retained as a global-pure / local-mixed seam, because the pure Bell vector yields a reduced subsystem with source-based analytic purity `0.5`, forcing the mixed-subsystem witness to remain explicit
- source lineage:
  - parent basis: cluster C, tension T3, distillate D3, candidate C3
- retained contradiction marker:
  - pure global state survives
  - mixed local subsystem also survives

## Candidate 6: TRACE_PRESERVATION_LIMIT_AND_HYGIENE_NONCLOSURE

- status: `A2_2_CANDIDATE`
- type: `channel-limit and handoff packet`
- claim:
  - the depolarizing probe should be retained only as a narrow trace-preservation witness with `p = 0.1`, and proof-family completion must still stop short of total sims-side closure because the remaining hygiene artifact batch is separate and later
- source lineage:
  - parent basis: cluster D, tension T4, tension T6, distillates D4 and D6, candidate C6
  - comparison anchors:
    - `BATCH_A2MID_mega_diagnostic_strip_seams__v1`
    - `BATCH_sims_hygiene_residue_artifacts__v1`
- retained contradiction marker:
  - proof-family lane completes
  - total sims-side residue does not yet complete here
