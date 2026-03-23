# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis0_traj_corr_suite_v2_orphan_family__v1`
Extraction mode: `SIM_AXIS0_TRAJ_CORR_SUITE_V2_ORPHAN_PASS`

## T1) The current orphan is clearly trajectory-correlation related, but it has no direct runner-name anchor in current `simpy/`
- source markers:
  - `results_axis0_traj_corr_suite_v2.json:1-939`
  - direct runner-name inventory of `simpy/`
- tension:
  - the surface is catalog-visible as `axis0_traj_corr_suite_v2`
  - no direct `traj_corr_suite_v2` runner name is recoverable in current `simpy/`
- preserved read:
  - keep the family relation explicit without fabricating a runner anchor
- possible downstream consequence:
  - later summaries should distinguish "family relation inferred from result structure" from "family relation anchored by a present runner"

## T2) The file claims a four-sequence family, but stores absolute values only for `SEQ01` and pushes `SEQ02-04` into deltas
- source markers:
  - `results_axis0_traj_corr_suite_v2.json:1-939`
- tension:
  - base entries:
    - `32`
    - all `SEQ01`
  - delta entries:
    - `96`
    - all `SEQ02`, `SEQ03`, `SEQ04`
- preserved read:
  - the storage contract is seq01-baseline-plus-deltas, not full absolute reporting
- possible downstream consequence:
  - later summaries should not read missing absolute `SEQ02-04` values as absent runs; they are implicit via deltas

## T3) The current orphan resembles the earlier local trajectory-correlation family, but its lattice and storage contract are materially different
- source markers:
  - `results_axis0_traj_corr_suite_v2.json:1-939`
  - `BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
  - `results_axis0_traj_corr_suite.json:1-364`
- tension:
  - earlier local family:
    - `32` absolute cases
    - no gate axis
    - no repetition axis
    - explicit sign labels
    - local max `MI_traj_mean = 0.29728021483432243`
  - current orphan:
    - `128` entries
    - `32` seq01 absolutes plus `96` deltas
    - gate axis `CNOT` / `CZ`
    - repetition axis `R1` / `R2`
    - hidden `T1` / `T2` axis
    - base max `MI_traj_mean = 0.03093941684451413`
- preserved read:
  - current orphan is not just a later serialization of the earlier local suite
- possible downstream consequence:
  - later summaries should not collapse the two surfaces into one version line without naming the contract shift

## T4) The current orphan also differs sharply from repo-top descendants `V4` and `V5`
- source markers:
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json:1-16`
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json:1-23`
- tension:
  - `V4`:
    - one-sequence aggregate
    - `cycles = 16`
    - `trials = 256`
  - `V5`:
    - two-sequence entangled-init delta
    - `cycles = 64`
    - `trials = 256`
  - current orphan:
    - `128` case lattice
    - four sequences
    - `cycles = 64`
    - `trials = 128`
- preserved read:
  - the orphan is neither the local full suite nor the repo-top compressed descendants
- possible downstream consequence:
  - later summaries should preserve current-orphan distinctness instead of forcing a false continuity line through `V4` or `V5`

## T5) One important axis is hidden in key prefixes rather than exposed as explicit metadata
- source markers:
  - `results_axis0_traj_corr_suite_v2.json:1-939`
- tension:
  - top-level metadata exposes:
    - sequences
    - trials
    - cycles
    - `n_vec`
    - `theta`
  - key lattice additionally encodes:
    - `T1`
    - `T2`
  - `T1` and `T2` each carry `16` absolute base prefixes
- preserved read:
  - the file's real axis count exceeds what top-level metadata directly states
- possible downstream consequence:
  - later summaries should not pretend the full lattice is transparent from metadata alone

## T6) The orphan is catalog-visible by filename alias only, while the top-level evidence pack omits it entirely
- source markers:
  - `SIM_CATALOG_v1.3.md:51-52`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
- tension:
  - catalog visibility:
    - yes
  - evidence-pack family or filename visibility:
    - no
- preserved read:
  - keep catalog listing separate from evidence admission
- possible downstream consequence:
  - later summaries should not mistake catalog presence for proof of a maintained evidence surface
