# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_top_level_docs_source_map__v1`
Extraction mode: `SIM_SOURCE_MAP_PASS`
Batch scope: first bounded sims batch in folder order; top-level docs only; no per-runner or per-result deep extraction
Date: 2026-03-08

## 1) Sims Root Inventory
- root:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims`
- file count excluding `.DS_Store`: `119`
- top-level docs before recursive subtrees: `3`
- executable-facing runner scripts under `simpy/`: `51`
- generated result JSONs under `simson/`: `62`
- committed cache artifacts under `simpy/__pycache__/`: `3`
- first docs in folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_RUNBOOK_v1.4.md`
- first non-doc paths after this batch in exact folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_axis0_boundary_bookkeep_sweep_v2.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_axis12_axis0_link_v1.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_mega_axis0_ab_stage16_axis6.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/__pycache__/ run_axis0_boundary_bookkeep_sweep_v2.cpython-313.pyc`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/__pycache__/ run_axis12_axis0_link_v1.cpython-313.pyc`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/__pycache__/ run_mega_axis0_ab_stage16_axis6.cpython-313.pyc`
- inventory note:
  - six paths begin with a literal leading space in the basename; three are `.py` runners and three are matching `.pyc` cache artifacts

## 2) Batch Selection
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_RUNBOOK_v1.4.md`
- reason for this bounded triad:
  - these are the first three non-hidden sources in folder order
  - together they already separate the sims class into catalog, evidence-pack, and engineering-runbook roles
  - this is enough to map sim families, evidence assumptions, runtime expectations, failure modes, and theory-facing vs executable-facing boundaries without mixing in deeper runner/result extraction yet
- deferred next in exact folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_axis0_boundary_bookkeep_sweep_v2.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_axis12_axis0_link_v1.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_mega_axis0_ab_stage16_axis6.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/__pycache__/ run_axis0_boundary_bookkeep_sweep_v2.cpython-313.pyc`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/__pycache__/ run_axis12_axis0_link_v1.cpython-313.pyc`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/__pycache__/ run_mega_axis0_ab_stage16_axis6.cpython-313.pyc`
- normalized next meaningful noncache sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_axis0_boundary_bookkeep_sweep_v2.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_axis12_axis0_link_v1.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_mega_axis0_ab_stage16_axis6.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/axis4_seq_cycle_sim.py`

## 3) Source Membership
- Primary source A:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - sha256: `0875a516fe8ed7d7ca5724b6655d13c5b07eb4b580829e598dce97e833254748`
  - size bytes: `7893`
  - line count: `158`
  - source class: derived filename catalog / family map
- Primary source B:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - sha256: `63b7e2029a9a3f5b06294b301ffcc62dd386077bed0ff4a3b9ef561b9f99140a`
  - size bytes: `30407`
  - line count: `663`
  - source class: generated evidence-pack surface
- Primary source C:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_RUNBOOK_v1.4.md`
  - sha256: `88bdfddc16e06cd8d086664deba4a84dd311340a6f9f7fcafe7b5c371c2ec6a1`
  - size bytes: `3988`
  - line count: `130`
  - source class: engineering workflow / run discipline

## 4) Structural Map Of The Source Family
### Source A: `SIM_CATALOG_v1.3.md`
- lines `1-5`
- source role:
  - derived catalog over `simson` result filenames
  - explicitly a map over result-file names, not raw result-body interpretation
- lines `8-21`
- source role:
  - theory-facing interpretation notes for Axis4, Topology4, Axis3, and one noncanon planning note
- lines `23-131`
- source role:
  - family coverage map across Axis0, Axis12, Topology4, Axis4, Axis5, Axis6, Stage16, Ultra, operator-role, Axis3, terrain, and Ultra4 groups
- lines `133-159`
- source role:
  - executable-facing entrypoint list and suggested repeatable execution order

### Source B: `SIM_EVIDENCE_PACK_autogen_v2.txt`
- lines `1-10`
- source role:
  - repeated `SIM_EVIDENCE v1` block grammar with `SIM_ID`, code hash, output hash, metric lines, and `EVIDENCE_SIGNAL`
- lines `30-98`
- source role:
  - Axis12, Topology4, and Axis3 evidence surfaces
- lines `102-289`
- source role:
  - Axis4, Axis56, Axis5, and Axis6 evidence surfaces
- lines `302-377`
- source role:
  - negative-control and Stage16 evidence surfaces
- lines `418-635`
- source role:
  - per-sequence Axis4 forward/reverse expansion blocks
- current bounded read:
  - `29` `BEGIN SIM_EVIDENCE v1` blocks were detected in this pack

### Source C: `SIM_RUNBOOK_v1.4.md`
- lines `1-4`
- source role:
  - self-classifies as engineering rather than truth-claims
- lines `8-18`
- source role:
  - strict Thread-B evidence container purity rule
- lines `22-47`
- source role:
  - deterministic fast-start and no-manual-editing workflow
- lines `51-72`
- source role:
  - failure handling via sharding, binary search, and negative controls
- lines `76-100`
- source role:
  - theory-facing test-priority notes for Axis4, Topology4, Axis3, Axis0, Axis12, and Ultra sequencing
- lines `104-121`
- source role:
  - paste hygiene and contamination rules
- lines `125-129`
- source role:
  - role labels for catalog, evidence pack, and harness locations

## 5) Source-Class Read
- Best classification:
  - top-level sims boundary docs linking interpretive family mapping, engineering run discipline, and generated evidence wire format
- Not best classified as:
  - full sims corpus coverage
  - earned SIM truth by themselves
  - active runtime law
- Theory-facing vs executable-facing split:
  - theory-facing:
    - Axis4 variance-order interpretation
    - Topology4 base-class interpretation
    - Axis3 chirality and Terrain8 interpretation
    - suggested family priority order
  - executable-facing:
    - `run_*` entrypoints
    - sharded run discipline
    - fixed seeds / hash / normalize guidance
    - exact `SIM_EVIDENCE` block grammar
  - evidence-facing:
    - auto-generated blocks with code hashes, output hashes, metrics, and evidence signals
- possible downstream consequence:
  - useful as the root batch for later sims-specific intake because it separates family naming, execution contract, and evidence payload shape without collapsing them into one doctrine surface
