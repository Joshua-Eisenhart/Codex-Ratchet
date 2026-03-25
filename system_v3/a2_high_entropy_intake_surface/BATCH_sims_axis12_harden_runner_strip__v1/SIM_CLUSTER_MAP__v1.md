# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis12_harden_runner_strip__v1`
Extraction mode: `SIM_AXIS12_HARDEN_RUNNER_STRIP_PASS`

## Cluster A
- cluster label:
  - core runner-only strip
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_harden_triple_v1.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_harden_v2_triple.py`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - two adjacent bundled producers
  - no result surfaces admitted as source members in this batch
- tension anchor:
  - source membership stays runner-only even though both scripts declare concrete result outputs

## Cluster B
- cluster label:
  - v1 harden triple contract
- members:
  - `results_axis12_paramsweep_v1.json`
  - `results_axis12_altchan_v1.json`
  - `results_axis12_negctrl_swap_v1.json`
  - `S_SIM_AXIS12_PARAMSWEEP_V1`
  - `S_SIM_AXIS12_ALTCHAN_V1`
  - `S_SIM_AXIS12_NEGCTRL_SWAP_V1`
- family role:
  - declared v1 producer layer
- executable-facing read:
  - full `by_seq` plus summary storage for the first two surfaces
  - pure combinatorial negative control for the third surface
- tension anchor:
  - these declared v1 outputs are not source members here even though the runner contract names them explicitly

## Cluster C
- cluster label:
  - v2 harden successor contract
- members:
  - `results_axis12_paramsweep_v2.json`
  - `results_axis12_altchan_v2.json`
  - `results_axis12_negctrl_label_v2.json`
  - `S_SIM_AXIS12_PARAMSWEEP_V2`
  - `S_SIM_AXIS12_ALTCHAN_V2`
  - `S_SIM_AXIS12_NEGCTRL_LABEL_V2`
- family role:
  - declared v2 producer layer
- executable-facing read:
  - `num_states` increases to `512`
  - all surfaces compress to `rows` plus discriminative summaries
  - negative control becomes a relabeled-channel rerun
- tension anchor:
  - `v2` is a real contract change, not a cosmetic rename

## Cluster D
- cluster label:
  - shared axis12 lattice and evidence emission
- members:
  - `SEQ01`
  - `SEQ02`
  - `SEQ03`
  - `SEQ04`
  - `seni_within`
  - `nesi_within`
  - `seta_bad`
  - `setb_bad`
  - `sim_evidence_pack.txt`
- family role:
  - shared harden-strip executable scaffolding
- executable-facing read:
  - both scripts use the same sequence-edge logic
  - both scripts emit three SIM_EVIDENCE blocks into the same evidence-pack filename
- tension anchor:
  - the shared evidence filename is overwrite-prone if both scripts are run in the same directory

## Cluster E
- cluster label:
  - closure-audit split and top-level omission
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- family role:
  - comparison-only residual classification and visibility cluster
- executable-facing read:
  - closure audit splits the runners and the declared outputs into separate residual classes
  - catalog and evidence pack omit the harden strip entirely
- tension anchor:
  - repo-top invisibility and explicit local write contracts coexist

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B and Cluster C show the six deferred outputs the runner strip claims it can produce
- Cluster D shows the shared axis12 lattice and the shared evidence overwrite risk
- Cluster E preserves the operational residual-class split and the repo-top visibility absence without collapsing the classes together
