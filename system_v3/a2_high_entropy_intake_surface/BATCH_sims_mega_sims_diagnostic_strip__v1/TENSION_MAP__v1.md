# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_mega_sims_diagnostic_strip__v1`
Extraction mode: `SIM_MEGA_SIMS_DIAGNOSTIC_STRIP_PASS`

## T1) The mega diagnostic strip emits local evidence, but none of it is cataloged or top-level evidenced
- source markers:
  - `mega_sims_failure_detector.py:1-40`
  - `mega_sims_run_02.py:1-85`
  - `mega_sims_trivial_check.py:1-43`
  - negative search in `SIM_CATALOG_v1.3.md`
  - negative search in `SIM_EVIDENCE_PACK_autogen_v2.txt`
- tension:
  - all three scripts emit `SIM_EVIDENCE v1` blocks locally
  - none of their filenames, SIM_IDs, or evidence tokens appears in the catalog
  - none appears in the repo-held evidence pack
- preserved read:
  - keep local evidence emission distinct from top-level visibility admission
- possible downstream consequence:
  - this strip should stay proposal-side in provenance strength

## T2) The two boolean detectors are near-duplicates, but they use different SIM_IDs and slightly different boolean contracts while reusing one evidence token
- source markers:
  - `mega_sims_failure_detector.py:13-40`
  - `mega_sims_trivial_check.py:13-44`
- tension:
  - both scripts use the same state and step counts
  - both emit only if a boolean flag is true
  - both reuse `E_MS_TRIVIAL`
  - the source bodies are highly similar, but not identical
- preserved read:
  - keep the detectors together as one subcluster without collapsing them into one identical file
- possible downstream consequence:
  - later synthesis should preserve the duplicated-token seam instead of silently deduplicating it

## T3) `mega_sims_run_02.py` looks like a stress sweep, but it still rides the same preservation-biased runtime lane
- source markers:
  - `mega_sims_run_02.py:1-85`
- tension:
  - the file scales up states and steps and emits four SIM_IDs
  - source-based inference says it still evolves pure one-qubit states only by unitary conjugation
  - that keeps purity-preservation built into the engine path
- preserved read:
  - do not overstate `run_02` as a fundamentally different physics regime from the boolean detectors
- possible downstream consequence:
  - later summaries should treat `run_02` as a scaled diagnostic variant, not a new sim family

## T4) `mega_sims_run_02.py` reports `collapse`, but the metric is hard-coded inert
- source markers:
  - `mega_sims_run_02.py:25-38`
- tension:
  - the return payload includes `collapse`
  - the variable is initialized to `0`
  - it is never incremented or updated
- preserved read:
  - keep `collapse` visible as a metric label while preserving that it is nonresponsive under current source
- possible downstream consequence:
  - later readers should avoid treating `collapse` as an actually measured discriminator from this script alone

## T5) The scripts are framed as failure or triviality detectors, but the current code path preserves purity by construction
- source markers:
  - `mega_sims_failure_detector.py:8-21`
  - `mega_sims_run_02.py:15-23`
  - `mega_sims_trivial_check.py:8-24`
- tension:
  - inputs are pure one-qubit states
  - updates are unitary conjugations
  - unitary conjugation preserves purity
- preserved read:
  - this is a source-based inference, not a runtime claim
- possible downstream consequence:
  - any observed failure under this strip would likely indicate numerical drift or implementation error rather than genuine mixing

## T6) `prove_foundation.py` is residual-neighboring but not part of the mega diagnostic strip
- source markers:
  - `prove_foundation.py:1-88`
- tension:
  - `prove_foundation.py` emits `SIM_EVIDENCE v1` too
  - but it is deterministic two-qubit proof logic around noncommutation, entanglement entropy, and channel trace preservation
  - the mega strip is stochastic one-qubit random-unitary diagnostics
- preserved read:
  - keep `prove_foundation.py` as the next separate bounded proof family
- possible downstream consequence:
  - the next residual pass should process proof logic separately from diagnostics
