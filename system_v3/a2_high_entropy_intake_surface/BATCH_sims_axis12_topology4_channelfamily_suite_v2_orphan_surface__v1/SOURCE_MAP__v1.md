# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis12_topology4_channelfamily_suite_v2_orphan_surface__v1`
Extraction mode: `SIM_AXIS12_TOPOLOGY4_CHANNELFAMILY_SUITE_V2_ORPHAN_SURFACE_PASS`
Batch scope: closure-exception batch for the previously read-but-unadmitted `results_axis12_topology4_channelfamily_suite_v2.json` local result surface
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_topology4_channelfamily_suite_v2.json`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_topology4_channelfamily_suite_v2.json`
- reason for bounded family:
  - the final closure aggregation detected this file as the only remaining sims file not yet admitted as a direct source member
  - the earlier topology4 seam batch read the file only as a comparison anchor to preserve the admission mismatch
  - this exception batch closes the direct-source coverage gap without rewriting the earlier seam reading
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_hygiene_residue_artifacts__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`
- deferred next residual-priority source:
  - none; this exception batch closes the final direct-source coverage gap

## 2) Source Membership
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_topology4_channelfamily_suite_v2.json`
  - sha256: `ffe8b0e3d5b640b1674f2826607b9540bb8e7ccad7df0a61717203234732b490`
  - size bytes: `1077`
  - line count: `37`
  - source role: local topology4 channelfamily result surface previously held comparison-only in the terrain8 admission seam batch

## 3) Structural Map Of The Family
### Result structure: `results_axis12_topology4_channelfamily_suite_v2.json`
- anchors:
  - `results_axis12_topology4_channelfamily_suite_v2.json:1-37`
- source role:
  - one compact local result surface with:
    - scalar metadata:
      - `H = Z`
      - `k = 0.18`
      - `p0 = 0.12`
      - `seed = 0`
      - `num_states = 4096`
      - `lin_trials = 512`
    - `families` map:
      - `EC_AD`
      - `EC_FX`
      - `EO_AD`
      - `EO_FX`
- bounded implication:
  - the local channelfamily surface is a compact topology4-family summary, not the terrain8 surface admitted under the same runner hash

### Family-level extrema
- anchors:
  - `results_axis12_topology4_channelfamily_suite_v2.json:1-37`
- bounded read:
  - maximum `lin_err_mean` family:
    - `EC_AD = 0.02232371509931299`
  - maximum `deltaH_absmean` family:
    - `EO_FX = 0.12029928053976777`
  - fixed families remain effectively linear:
    - `EC_FX.lin_err_mean = 2.947090052116208e-16`
    - `EO_FX.lin_err_mean = 3.0498805390193284e-16`
- bounded implication:
  - the local surface preserves the same adaptive-vs-fixed topology split seen when this file was first used as a seam anchor

### Seam preservation with the prior terrain8-admission batch
- comparison anchors:
  - `BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1/MANIFEST.json`
- bounded read:
  - the earlier seam batch chose:
    - current runner
    - repo-top admitted `results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
  - and kept the current local channelfamily result comparison-only on purpose
  - this exception batch does not collapse that seam; it only closes direct-source coverage
- bounded implication:
  - the admission mismatch remains preserved even though the local result now gets its own source-member batch

### Closure relation
- comparison anchors:
  - closure-audit manifest
  - hygiene-residue manifest
- bounded read:
  - this file was the only uncovered sims file in the aggregate direct-source scan
  - after admitting it, sims-file coverage reaches the full inventory
- bounded implication:
  - this batch corrects a coverage gap discovered during the final closure report

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_hygiene_residue_artifacts__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
- relevant anchors:
  - `BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1/MANIFEST.json`
  - `BATCH_sims_hygiene_residue_artifacts__v1/MANIFEST.json`
- bounded comparison read:
  - the prior seam batch remains valid as a seam-preservation read
  - the prior hygiene batch remains valid as the final artifact-class residue pass
  - only the direct-source coverage aggregate needed correction

## 5) Source-Class Read
- Best classification:
  - one-file closure-exception result-surface batch for the local topology4 channelfamily summary
- Not best classified as:
  - a replacement for the earlier terrain8-admission seam batch
  - new residual work outside the already-known sims corpus
  - a substantive new family discovery
- Theory-facing vs executable-facing split:
  - executable-facing:
    - compact topology4 summary families with local scalar metadata
  - theory-facing:
    - adaptive-vs-fixed and EC-vs-EO splits remain visible
  - evidence-facing:
    - this file is now admitted as a direct source member
    - the earlier terrain8 seam remains separately preserved
- possible downstream consequence:
  - no further sims-side intake is required after this correction; closure reporting can now use the full 120-of-120 source-member coverage figure
