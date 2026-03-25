# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_mega_sims_diagnostic_strip__v1`
Extraction mode: `SIM_MEGA_SIMS_DIAGNOSTIC_STRIP_PASS`

## Cluster A
- cluster label:
  - core mega diagnostic strip
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/mega_sims_failure_detector.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/mega_sims_run_02.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/mega_sims_trivial_check.py`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one stochastic diagnostic strip
  - local stdout evidence only
  - no committed result surfaces
- tension anchor:
  - the strip behaves like a family, but it never graduates into repo-held result artifacts

## Cluster B
- cluster label:
  - boolean triviality detectors
- members:
  - `mega_sims_failure_detector.py`
  - `mega_sims_trivial_check.py`
  - `MS_TRIVIAL_DETECT`
  - `MS_TRIVIAL_CHECK`
  - `E_MS_TRIVIAL`
- family role:
  - boolean detector subcluster
- executable-facing read:
  - same state count and step count
  - near-duplicate source bodies
  - same evidence token reused under different SIM_IDs
- tension anchor:
  - duplicated token semantics exist even though the SIM_ID labels differ

## Cluster C
- cluster label:
  - metric stress sweep
- members:
  - `mega_sims_run_02.py`
  - `MS_B_AXIS6`
  - `MS_C_AXIS3`
  - `MS_D_OPCHAOS`
  - `MS_E_LONGRUN`
  - `collapse`
  - `vn_entropy_mean`
  - `purity_min`
- family role:
  - scaled diagnostic stress subcluster
- executable-facing read:
  - emits four always-signaled diagnostic surfaces
  - shares the same one-qubit random-unitary engine family
- tension anchor:
  - the script looks more substantial than the boolean detectors, but it still sits on the same trivial-preservation runtime path

## Cluster D
- cluster label:
  - source-based trivial-preservation inference
- members:
  - pure-state initialization
  - random unitary conjugation
  - purity preservation
  - entropy near-zero expectation
- family role:
  - inference cluster derived from direct code structure
- executable-facing read:
  - unitary conjugation preserves purity of pure states
  - any flagged failure is likely numerical rather than structural under the current code path
- tension anchor:
  - the scripts are framed as failure/chaos detectors, but the current engine path is preservation-biased by construction

## Cluster E
- cluster label:
  - proof boundary anchor
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/prove_foundation.py`
  - `S_FOUNDATION_PROOF`
- family role:
  - next bounded-family boundary anchor
- executable-facing read:
  - deterministic two-qubit proof logic
  - not part of the stochastic mega diagnostic lane
- tension anchor:
  - residual proximity exists without family identity

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B and Cluster C show the two internal mega diagnostic subclusters
- Cluster D preserves the source-based trivial-preservation read
- Cluster E keeps `prove_foundation.py` outside the current batch as the next separate proof family
