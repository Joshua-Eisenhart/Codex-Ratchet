# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_work_surface_shadow_systemv3_and_curated_wrappers__v1`
Extraction mode: `SHADOW_SYSTEMV3_DUPLICATE_AND_CURATED_WRAPPER_PASS`

## T1) “canonical A2 state lives under `system_v3/a2_state/`” vs exact duplicate alias directory
- source markers:
  - derived-index README contract
  - equivalence count between `a2_derived_indices_noncanonical` and `a2_noncanonical_derived_index_cache_surface`
- tension:
  - the README declares one canonical fixed-interface home and one optional derived-index surface
  - the shadow tree still contains two byte-identical derived-index surfaces with different names
- preserved read:
  - interface discipline is declared, but alias duplication remains in the spillover tree

## T2) stable A2 intent surface vs drifting append files
- source markers:
  - identical `INTENT_SUMMARY.md`
  - differing `autosave_seq.txt`
  - differing `memory.jsonl`
- tension:
  - the mirror surfaces tell the same boot/intention story
  - their live-ish persistence counters and append logs have diverged
- preserved read:
  - the narrative shell is frozen while the persistence tail keeps moving

## T3) duplicated tooling tree vs one extra live helper
- source markers:
  - `tools` vs `deterministic_operational_tooling_surface` comparison
  - `a1_wiggle_autopilot.py`
- tension:
  - `60` shared tool files are byte-identical
  - `tools/` alone contains the extra `a1_wiggle_autopilot.py`
- preserved read:
  - the shadow tooling surface aims to freeze a known subset, but the live shadow tree continues to accrete helpers

## T4) frozen runtime subset vs substantive autowiggle code drift
- source markers:
  - `runtime` vs `deterministic_runtime_execution_surface` comparison
  - `a1_autowiggle.py` size/hash difference
- tension:
  - the frozen runtime subset largely mirrors the main runtime files it keeps
  - the shared `a1_autowiggle.py` is not identical across the two trees
- preserved read:
  - “frozen subset” still includes at least one substantive code divergence, not just file omission

## T5) shadow-tree duplication vs curated wrapper claims of reduced flooding
- source markers:
  - curated zip readmes
  - control-plane and ZIP_JOB package contents
- tension:
  - the wrapper readmes say they avoid flooding an existing Pro thread with the entire repo
  - they still package large slices of the duplicated shadow system and its template suites
- preserved read:
  - the wrappers are reduced relative to the whole repo, but they remain broad understanding-transfer bundles rather than tiny deltas

## T6) quarantined proposed-doc snapshot vs later shadow-system copies
- source markers:
  - quarantine hashes for `WORKSPACE_LAYOUT_v1.md`, `doc_index.json`, `index_v1.json`
  - non-matching hashes against later `work/system_v3` files
- tension:
  - the quarantine snapshot clearly belongs to the same document family
  - none of its sampled core files are byte-identical to the later shadow copies
- preserved read:
  - the spillover tree retains earlier or alternate proposals alongside later stabilized shadows

## T7) public explanatory “noncanon” status vs highly system-like document packaging
- source markers:
  - public-facing doc header
  - control-plane bundle plaque
  - curated mechanism-plus-upgrades readme
- tension:
  - several surfaces explicitly self-label as public/noncanon or explanatory
  - the same family is packaged and transferred as if it were a compact system-understanding bundle
- preserved read:
  - explanation-grade and mechanism-grade materials are being shipped together inside the wrapper lane
