# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis12_seq_constraints_family__v1`
Extraction mode: `SIM_AXIS12_SEQ_CONSTRAINTS_PASS`
Batch scope: standalone residual axis12 sequence-constraint family centered on `run_axis12_seq_constraints.py` and `results_axis12_seq_constraints.json`, with repo-top `V2` descendant separation preserved
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_seq_constraints.py`
- selected sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_seq_constraints.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_seq_constraints.json`
- reason for bounded family:
  - the prior residual paired-family batch deferred this exact pair next
  - one runner emits one paired result surface with one local SIM_ID
  - the current family is a local combinatorial constraint surface over wraparound sequence edges and should stay separate from the repo-top `V2` descendant that keeps only a narrower subset of the constraint layer
- comparison-only anchors read:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_channel_realization_suite_family__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_SEQ_CONSTRAINTS_V2.json`
- deferred next residual-priority source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_topology4_channelfamily_suite_v2.py`

## 2) Source Membership
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_seq_constraints.py`
  - sha256: `45a914e43629cbd18486c08e8fe4716488bc39b91c9222ccb4ad267d86c6a725`
  - size bytes: `3030`
  - line count: `104`
  - source role: local axis12 combinatorial sequence-constraint runner
- Result surface:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_seq_constraints.json`
  - sha256: `fbc7996fa266458c62b6a155ea89c5d92d4a19e7dbf5f34257f1519ea0e1b8a6`
  - size bytes: `737`
  - line count: `45`
  - source role: compact local axis12 constraint result surface

## 3) Structural Map Of The Family
### Runner contract: `run_axis12_seq_constraints.py`
- anchors:
  - `run_axis12_seq_constraints.py:20-99`
- source role:
  - one four-sequence constraint family:
    - `SEQ01 = [Se, Ne, Ni, Si]`
    - `SEQ02 = [Se, Si, Ni, Ne]`
    - `SEQ03 = [Se, Ne, Si, Ni]`
    - `SEQ04 = [Se, Si, Ne, Ni]`
  - edge treatment:
    - cycle edges include wraparound
  - axis1 pairing tokens:
    - `SENI = {Se, Ni}`
    - `NESI = {Ne, Si}`
  - axis2 adjacency sets:
    - `SETA_allowed = {(Ne,Ni), (Se,Si)}`
    - `SETB_allowed = {(Ne,Se), (Ni,Si)}`
  - stored metric families:
    - `seta_bad_*`
    - `setb_bad_*`
    - `seni_within_*`
    - `nesi_within_*`
  - emits one local SIM_ID:
    - `S_SIM_AXIS12_SEQ_CONSTRAINTS`

### Result structure: `results_axis12_seq_constraints.json`
- top-level shape:
  - one compact result surface with:
    - `seqs`
    - `metrics`
- strongest bounded metrics:
  - balanced axis2 counts:
    - `SEQ01`: `seta_bad = 2`, `setb_bad = 2`
    - `SEQ02`: `seta_bad = 2`, `setb_bad = 2`
  - extreme axis2 counts:
    - `SEQ03`: `seta_bad = 4`
    - `SEQ04`: `setb_bad = 4`
  - dual within-pair cohesion:
    - `SEQ03`: `seni_within = 1`, `nesi_within = 1`
    - `SEQ04`: `seni_within = 1`, `nesi_within = 1`
- bounded implication:
  - the local family carries both axis1-style within-pair counts and axis2-style nonmembership counts
  - `SEQ03` and `SEQ04` are the only sequences that activate both within-pair counters

### Balanced pair vs asymmetric pair split
- bounded read:
  - `SEQ01` and `SEQ02` are balanced on axis2:
    - `seta_bad = setb_bad = 2`
    - both within-pair counts are zero
  - `SEQ03` and `SEQ04` are asymmetric on axis2 and active on both within-pair counts:
    - `SEQ03`: `seta_bad = 4`, `setb_bad = 2`
    - `SEQ04`: `seta_bad = 2`, `setb_bad = 4`
- bounded implication:
  - the local constraint surface splits cleanly into a balanced pair and an asymmetric pair

### Top-level descendant relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:58`
  - `SIM_CATALOG_v1.3.md:67`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:39-50`
  - `results_S_SIM_AXIS12_SEQ_CONSTRAINTS_V2.json:1-24`
- bounded read:
  - the repo-held top-level evidence pack admits:
    - `S_SIM_AXIS12_SEQ_CONSTRAINTS_V2`
  - that evidence block carries the same code hash as the current runner:
    - `45a914e43629cbd18486c08e8fe4716488bc39b91c9222ccb4ad267d86c6a725`
  - the repo-held evidence pack omits the local SIM_ID:
    - `S_SIM_AXIS12_SEQ_CONSTRAINTS`
  - the repo-top `V2` descendant keeps only:
    - `nesi_edges`
    - `seni_edges`
  - the local surface additionally keeps:
    - `seta_bad_*`
    - `setb_bad_*`
    - `seni_within_*`
    - `nesi_within_*`
  - the descendant also diverges on stored `seni` values:
    - `V2` stores `SEQ03_seni_edges = 0`, `SEQ04_seni_edges = 0`
    - the local surface stores `seni_within_SEQ03 = 1`, `seni_within_SEQ04 = 1`
- bounded implication:
  - code-level provenance aligns, but the repo-top admitted artifact is a narrower and behaviorally divergent descendant rather than the local result surface itself

## 4) Comparison Anchors
- comparison sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_channel_realization_suite_family__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_SEQ_CONSTRAINTS_V2.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:58,67`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:39-50`
  - `BATCH_sims_axis12_channel_realization_suite_family__v1/MANIFEST.json`
- bounded comparison read:
  - the prior residual batch set this pair next
  - the current family is a local full constraint surface
  - the repo-top `V2` descendant should stay comparison-only here because it is a narrower admitted surface under the same runner hash, not the local result surface itself

## 5) Source-Class Read
- Best classification:
  - standalone local axis12 combinatorial sequence-constraint family with one local SIM_ID surface
- Not best classified as:
  - the repo-top admitted `V2` surface
  - a runtime or endpoint realization family
  - a merged batch with the next topology4 family
- Theory-facing vs executable-facing split:
  - executable-facing:
    - current runner computes wraparound edge sets and four metric families over the same four sequences
    - the local result is purely combinatorial and contains no runtime state evolution
  - theory-facing:
    - `SEQ01/SEQ02` form the balanced pair
    - `SEQ03/SEQ04` form the asymmetric pair with both within-pair counters active
  - evidence-facing:
    - local evidence is explicit in the runner contract
    - repo-top evidence-pack admission exists only for the narrower `V2` descendant under the same code hash
- possible downstream consequence:
  - later residual intake should preserve this family as the local full constraint surface and let `run_axis12_topology4_channelfamily_suite_v2.py` begin the next bounded paired family
