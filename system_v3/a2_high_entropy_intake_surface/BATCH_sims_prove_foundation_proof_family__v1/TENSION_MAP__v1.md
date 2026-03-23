# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_prove_foundation_proof_family__v1`
Extraction mode: `SIM_PROVE_FOUNDATION_PROOF_PASS`

## T1) The proof emits local evidence, but none of it is cataloged or top-level evidenced
- source markers:
  - `prove_foundation.py:1-88`
  - negative search in `SIM_CATALOG_v1.3.md`
  - negative search in `SIM_EVIDENCE_PACK_autogen_v2.txt`
- tension:
  - the script emits `S_FOUNDATION_PROOF` locally
  - the proof filename, SIM_ID, and evidence token do not appear in the catalog
  - they also do not appear in the repo-held evidence pack
- preserved read:
  - keep local proof emission distinct from top-level visibility admission
- possible downstream consequence:
  - this proof family should stay proposal-side in provenance strength

## T2) The script is called a proof, but its evidentiary surface is still a gated executable witness
- source markers:
  - `prove_foundation.py:62-88`
- tension:
  - the logic is deterministic
  - the evidence emission is still conditional on:
    - noncommutation
    - subsystem mixedness
    - trace preservation
- preserved read:
  - do not collapse the script into pure prose or pure theorem statement; it is an executable gated witness
- possible downstream consequence:
  - later summaries should preserve both the proof framing and the executable gate

## T3) A pure entangled whole yields a mixed subsystem
- source markers:
  - `prove_foundation.py:35-50`
- tension:
  - `rho_bell` is constructed from a pure Bell vector
  - `rho_a` becomes mixed after partial trace
  - source-based analytic purity is `0.4999999999999998`
- preserved read:
  - keep the global-pure/local-mixed seam explicit
- possible downstream consequence:
  - later conceptual summaries should not erase the subsystem mixedness witness into general language only

## T4) The channel witness is narrow: it proves trace preservation, not full dynamical adequacy
- source markers:
  - `prove_foundation.py:52-60`
- tension:
  - the depolarizing probe verifies trace conservation
  - it does not test broader stability, recurrence, or sequence behavior
- preserved read:
  - keep the channel section as a limited witness
- possible downstream consequence:
  - later interpretation should avoid overstating what this source proves about channels

## T5) The proof shares local `SIM_EVIDENCE v1` formatting with the mega strip, but it is not the same bounded family
- source markers:
  - `prove_foundation.py:74-83`
  - `BATCH_sims_mega_sims_diagnostic_strip__v1/MANIFEST.json`
- tension:
  - both emit local `SIM_EVIDENCE v1`
  - the mega strip is stochastic one-qubit diagnostics
  - the current proof is deterministic two-qubit matrix logic
- preserved read:
  - shared formatting does not imply shared source class family
- possible downstream consequence:
  - proof logic and diagnostics should remain separate in later residual handling

## T6) The diagnostic/proof residual class is now exhausted, but sims-side residue is not
- source markers:
  - `BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
- tension:
  - this batch clears the last diagnostic/proof script
  - residual hygiene artifacts still remain:
    - three `__pycache__` entries
    - one top-level `.DS_Store`
- preserved read:
  - do not confuse proof-family completion with total residual completion
- possible downstream consequence:
  - the next residual pass should process hygiene residue only
