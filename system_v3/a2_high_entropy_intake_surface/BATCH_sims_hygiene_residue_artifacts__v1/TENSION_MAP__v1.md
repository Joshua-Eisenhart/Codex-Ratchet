# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_hygiene_residue_artifacts__v1`
Extraction mode: `SIM_HYGIENE_RESIDUE_ARTIFACT_PASS`

## T1) The pycache artifacts carry meaningful runner names, but they are only committed bytecode residue
- source markers:
  - current `.pyc` filenames
  - `BATCH_sims_leading_space_runner_result_family__v1/MANIFEST.json`
- tension:
  - each `.pyc` file names a meaningful previously batched runner
  - none is source code or a result surface
- preserved read:
  - keep executable lineage visible without inflating the caches into new sim sources
- possible downstream consequence:
  - later closure summaries should attribute them to prior families as hygiene residue only

## T2) The leading-space runner batch excluded the `.pyc` files early as nonprimary noise, but they remained part of final sims-side residual coverage
- source markers:
  - `BATCH_sims_leading_space_runner_result_family__v1/MANIFEST.json`
  - closure-audit manifest
- tension:
  - the `.pyc` files were excluded from source membership in the first executable-facing batch
  - they still had to be closed out explicitly at the end
- preserved read:
  - early exclusion did not mean they vanished from residual accounting
- possible downstream consequence:
  - artifact exclusion and artifact completion should stay separate concepts in later audits

## T3) `.DS_Store` shares residual status with pycache, but it is a different artifact class
- source markers:
  - current `.DS_Store` metadata read
- tension:
  - `.DS_Store` is top-level Apple Desktop Services metadata
  - the `.pyc` files are compiled Python bytecode under `simpy/__pycache__`
- preserved read:
  - keep platform noise distinct from bytecode cache residue
- possible downstream consequence:
  - final closure should preserve the pycache-vs-noise split instead of flattening all residue into one label

## T4) The hygiene batch is inside the sims source class, but it contributes no new sim claim content
- source markers:
  - current four artifact members
- tension:
  - the files physically live under the sims directory
  - they add no new simulation, proof, or evidence claim
- preserved read:
  - the batch exists for source-class closure, not for conceptual extraction
- possible downstream consequence:
  - downstream summaries should call this a closure artifact batch, not a substantive sim batch

## T5) Residual completion is real only after this batch, not after proof-family completion
- source markers:
  - prior proof-family manifest
  - closure-audit manifest
- tension:
  - the proof family exhausted diagnostics/proofs
  - hygiene residue still remained until now
- preserved read:
  - do not misdate full sims-side completion to the prior turn
- possible downstream consequence:
  - closure reporting should mark this batch as the true end of sims-side residual intake

## T6) The artifacts are hashable and size-distinct, but those properties do not turn them into evidence surfaces
- source markers:
  - current size and sha256 reads
  - file-type reads
- tension:
  - each artifact has stable byte-level metadata
  - none has a simulation-facing schema or evidence contract
- preserved read:
  - do not confuse file integrity metadata with source-layer evidentiary content
- possible downstream consequence:
  - later artifact inventories should keep integrity metadata and semantic status separate
