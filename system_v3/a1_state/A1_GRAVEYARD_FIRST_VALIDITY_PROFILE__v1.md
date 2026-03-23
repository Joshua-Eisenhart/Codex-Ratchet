# A1_GRAVEYARD_FIRST_VALIDITY_PROFILE__v1
Status: PROPOSED / NONCANONICAL / VALIDITY CAMPAIGN PROFILE
Date: 2026-03-06
Role: Graveyard-first validity mode for family-level A1 campaigns

## 1) Purpose
This profile is for stronger validity runs, not scaffold proofs.

It exists to:
- populate a real same-concept graveyard
- force rich negative pressure before early steelman success is over-trusted
- allow rescue to emerge out of graveyard structure instead of only from minimal ladder ordering
- stress whether a family survives under pressure, not just whether it can be admitted cleanly once

## 2) Difference From Scaffold Mode
Scaffold mode:
- proves transport
- proves ordering
- proves basic admissibility
- proves a lean ladder can pass

Graveyard-first validity mode:
- starts by pushing the candidate family through graveyard pressure
- prefers rich negative classes and branch diversity
- delays rescue until graveyard structure is actually present
- uses recovery only after graveyard pressure and kill diversity are real

## 3) Core Policy
Working rule:
- the whole concept family may enter graveyard competition first
- recovery should come only after the family has generated real kill structure
- negative sims should be richer than the minimum scaffold packet
- rescue should be tied to actual graveyard lineage

This is one valid run mode, not the only run mode.

Current proven variant:
- broad-fuel graveyard seed
- concept family stays in focus, but graveyard fill is allowed to draw from the wider curated fuel surface
- this is the mode currently executed by `run_graveyard_first_validity_campaign.py`

Deferred variant:
- concept-local graveyard seed
- same-concept graveyard pressure with much tighter term-surface locality
- implemented as a separate wrapper profile:
  - `substrate_base_concept_local`

## 4) Default Driver Shape
Use:
- `preset = graveyard13`
- `process_mode = concept_path_rescue`
- `debate_strategy = graveyard_then_recovery`
- `debate_mode = graveyard_first`
- `memo_provider_mode = exchange`
- `focus_term_mode = concept_plus_rescue`

## 5) Fill / Recovery Gates
Default validity gates:
- stay in `graveyard_first` until graveyard dominates by count
- stay in `graveyard_first` until extracted family fuel is represented in graveyard
- require real kill diversity before rescue
- allow `rescue_start_min_canonical = 0`
- require `rescue_start_min_graveyard > 0`

This means the family does not need early canonical footholds before recovery begins.

## 6) Suggested Default Thresholds
Use these as the default validity profile:
- `fill_until_graveyard_dominates = true`
- `fill_graveyard_minus_canonical_min = 8`
- `fill_until_fuel_coverage = true`
- `fill_fuel_coverage_target = 0.85`
- `fill_min_graveyard_term_count = 8`
- `graveyard_fill_cycles = 10`
- `graveyard_fill_max_stall_cycles = 2`
- `path_build_min_cycles = 8`
- `path_build_max_cycles = 24`
- `path_build_novelty_stall_max = 6`
- `rescue_start_min_canonical = 0`
- `rescue_start_min_graveyard = 12`
- `rescue_start_min_kill_diversity = 6`
- `campaign_graveyard_fill_policy = fuel_full_load`
- `campaign_forbid_rescue_during_graveyard_fill = true`
- `target_executed_cycles = 24`
- `min_executed_cycles_before_goal = 12`

## 7) Family-Specific Use
### Base substrate family
Use for:
- `finite_dimensional_hilbert_space`
- `density_matrix`
- `probe_operator`
- `cptp_channel`
- `partial_trace`

Purpose:
- prove that the whole substrate family can survive graveyard pressure, not just a lean ladder

Available variants:
- `substrate_base`
  - broad-fuel graveyard seed
- `substrate_base_concept_local`
  - concept-local graveyard seed
  - no curated-fuel coverage forcing
  - `anchor_replay` fill policy instead of `fuel_full_load`

Observed comparison:
- normalized family sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__SUBSTRATE_BASE_VALIDITY_FAMILY__v1.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__SUBSTRATE_BASE_VALIDITY_FAMILY__v1.md`
- broad-fuel substrate-base profile:
  - `canonical_term_count = 39`
  - `graveyard_count = 153`
  - `sim_registry_count = 247`
- concept-local substrate-base profile:
  - `canonical_term_count = 9`
  - `graveyard_count = 53`
  - `sim_registry_count = 80`

Interpretation:
- the concept-local profile is now genuinely narrower
- it keeps the graveyard/negative pattern but avoids broad-fuel spillover
- it is the better validity mode when the goal is same-family pressure instead of broad exploratory saturation

### Pass-2 enrichment family
Use for:
- `unitary_operator`
- `commutator_operator`
- `hamiltonian_operator`
- `lindblad_generator`

Purpose:
- test operator-level enrichment under graveyard-first pressure before any Hopf/manifold/axis expansion

Available variant:
- `substrate_enrichment_concept_local`
  - concept-local graveyard seed for the four-term enrichment family
  - no curated-fuel coverage forcing
  - `anchor_replay` fill policy instead of `fuel_full_load`

Focused follow-up variant:
- `substrate_enrichment_dynamics_local`
  - concept-local graveyard seed for:
    - `hamiltonian_operator`
    - `lindblad_generator`
  - use when the goal is targeted time/dynamics leakage pressure instead of whole-family seed saturation

Bridge follow-up variant:
- `substrate_enrichment_dynamics_bridge`
  - keeps the same two-term target pair
  - widens rescue pressure enough to try for an executed-cycle follow-up
  - use only when explicitly testing the tradeoff between executed-cycle recovery and target specificity

## 8) Negative Pressure Requirements
Keep at minimum:
- `COMMUTATIVE_ASSUMPTION`
- `CLASSICAL_TIME`
- `PRIMITIVE_EQUALS`
- `INFINITE_SET`
- `KERNEL_VALID_BUT_MODEL_EMPTY`

For enrichment family, add special emphasis on:
- time leakage through `hamiltonian_operator`
- time leakage through `lindblad_generator`

## 9) Expected Outputs
A valid graveyard-first run should leave:
- dense graveyard records for the concept family
- explicit negative-class coverage
- rescue lineage linked to real graveyard rows
- richer than scaffold SIM structure
- a clearer picture of which family members survive pressure
- a sim-backed library of failure traces and surviving reformulations for that family

Important distinction:
- a graveyard-seed run may still fail final operational-integrity closure while it is building graveyard pressure
- the current broad-fuel proof should be read as:
  - execution path proven
  - rich graveyard/negative pressure proven
  - final validity closure still phase-dependent
- the current concept-local enrichment proof should be read as:
  - exact-family seed saturation proven
  - real graveyard/negative pressure proven
  - selector exhaustion reached before first executed cycle
  - final validity closure still phase-dependent

## 10) Not A Replacement
This profile does not replace scaffold runs.
It is the stricter follow-up mode after scaffold proof work.

## 11) Runnable Surface
Preferred wrapper:
- `system_v3/tools/run_graveyard_first_validity_campaign.py`

That wrapper should be treated as the standard easy-entry command for validity-mode campaigns.

Execution options:
- `--provider local_stub` for one-command local Codex stub execution
- `--provider exchange_only` when an external worker/exchange provider is supplying memos

## 12) Pass-2 Enrichment Concept-Local Proof
The concept-local enrichment graveyard profile is now execution-proven:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__SUBSTRATE_ENRICHMENT_FAMILY__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__SUBSTRATE_ENRICHMENT_FAMILY__v1.md`

Observed:
- exact admitted terms:
  - `unitary_operator`
  - `commutator_operator`
  - `hamiltonian_operator`
  - `lindblad_generator`
- `graveyard_count = 36`
- `kill_log_count = 36`
- `sim_registry_count = 52`
- semantic/math substance gate passes in `graveyard_fill`
- stop condition is `STOPPED__PACK_SELECTOR_FAILED`
- wrapper status is `PASS__CONCEPT_LOCAL_SEED_SATURATED`

Interpretation:
- for this profile, `STOPPED__PACK_SELECTOR_FAILED` is best read as concept-local enrichment-seed saturation, not as transport failure
- the selector has exhausted the local enrichment-family candidate surface after the four exact target terms survive pressure
- this is a good seed result, but not full family-validity closure

## 13) Pass-2 Dynamics-Local Follow-Up
The focused time/dynamics graveyard profile is now execution-proven as a targeted seed result:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__SUBSTRATE_ENRICHMENT_FAMILY__v1.md`

Observed:
- exact target terms allowed:
  - `hamiltonian_operator`
  - `lindblad_generator`
- `graveyard_count = 17`
- `kill_log_count = 17`
- `sim_registry_count = 25`
- semantic/math substance gate passes in `graveyard_fill`
- wrapper status is `PASS__CONCEPT_LOCAL_SEED_SATURATED`
- stop condition is `STOPPED__PACK_SELECTOR_FAILED`

Interpretation:
- for this focused profile, `STOPPED__PACK_SELECTOR_FAILED` is best read as dynamics-local seed saturation, not as transport failure
- the targeted time/dynamics pair survives concept-local pressure strongly enough to saturate the local selector before an executed cycle
- this is a useful leakage-pressure result, but not final validity closure

## 14) Dynamics-Bridge Follow-Up
The bridge variant is now also tested:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__SUBSTRATE_ENRICHMENT_FAMILY__v1.md`

Observed:
- `executed_cycles = 1`
- wrapper status is `PASS__EXECUTED_CYCLE`
- `graveyard_count = 144`
- `kill_log_count = 144`
- `sim_registry_count = 232`
- exact target terms are not left in `CANONICAL_ALLOWED`:
  - `hamiltonian_operator`
  - `lindblad_generator`

Interpretation:
- the bridge variant is useful as a proof that broader rescue pressure can recover an executed cycle
- it is not acceptable as the default strict dynamics-validity mode because it loses target specificity
- keep `substrate_enrichment_dynamics_local` as the strict target-preserving profile

## 15) Entropy-Bridge Follow-Up
The entropy bridge now has two graveyard-first profiles:

### A) Strict local seed
- profile: `entropy_bridge_local`
- run:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BRIDGE_LOCAL_BROAD_PAIR__v1.md`
- observed:
  - wrapper status = `PASS__EXECUTED_CYCLE`
  - `executed_cycles = 1`
  - `graveyard_count = 9`
  - `kill_log_count = 9`
  - `sim_registry_count = 17`
- interpretation:
  - this proves a real lower-loop seed cycle for the entropy bridge
  - it is too thin to stand as the default rich-validity mode

### B) Broad graveyard saturation
- profile: `entropy_bridge_broad`
- run:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BRIDGE_LOCAL_BROAD_PAIR__v1.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_LOCAL_BROAD_PAIR__v1.md`
- observed:
  - wrapper status = `PASS__EXECUTED_CYCLE`
  - `executed_cycles = 1`
  - `canonical_term_count = 39`
  - `graveyard_count = 153`
  - `kill_log_count = 153`
  - `sim_registry_count = 247`
  - semantic/math substance gate passes in `graveyard_fill`
- interpretation:
  - this is the correct broad-fuel exploratory saturation surface for the entropy bridge family
  - it proves rich graveyard and negative pressure
  - it does not preserve the direct target pair as a strict local acceptance result

Working rule:
- keep `entropy_bridge_local` as the narrow seed-proof surface
- keep `entropy_bridge_broad` as the rich exploratory graveyard surface
- do not treat either one alone as final closure for the higher entropy-family proposal terms

### C) Focused bookkeeping follow-ups
- single-term local:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_RATE_FAMILY__v1.md`
  - result: `FAIL__SUBPROCESS`
  - interpretation: too thin to sustain a useful local graveyard-first path
- bookkeeping pair local:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_RATE_FAMILY__v1.md`
  - result: no executed cycle, no graveyard growth, no negative pressure
  - interpretation: bookkeeping remains dependent on the broad exploratory bridge mode for now

Operational rule:
- do not keep tuning isolated local bookkeeping profiles
- keep `entropy_bridge_broad` as the rich pressure surface
- advance the next lean executable entropy step through `correlation_polarity` first

Entropy broad-mode residue rule:
- for the entropy lane, `entropy_bridge_broad` is the primary executable surface for:
  - classical residue pressure
  - negative-class saturation
  - rescue-from-residue transforms
- use the residue packs defined in:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a1_state/A1_FIRST_ENTROPY_BRIDGE_CAMPAIGN__v1.md`
- do not spend more time tuning:
  - single-term local `correlation_polarity`
  - isolated `entropy_production_rate`
  - narrow bookkeeping witness routes
  until a colder alias-layer exists

### D) Focused correlation local follow-up
- run:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_RATE_FAMILY__v1.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_RATE_FAMILY__v1.md`
- result:
  - `FAIL__SUBPROCESS`
  - no executed cycle
  - no graveyard growth
  - no negative pressure
  - stop condition remains `WAITING_FOR_MEMOS`
  - external-response prepack passes, but memo ingestion stays `NO_VALID_MEMOS`
- interpretation:
  - `correlation_polarity` as a single-term strict local route is still too thin under the current exchange/memo path
  - treat this as negative evidence for the narrow local route, not as a reason to retune the broad entropy bridge

Operational rule:
- do not keep tuning `correlation_polarity_local`
- keep `entropy_bridge_broad` as the rich pressure surface for the entropy lane
- if a later narrow route is needed, it should likely come from a stronger bridge pair or a direct packet-only path, not the current memo-local profile

### E) Direct packet-only entropy bridge
- normalized family sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BRIDGE_PACKET_SMOKE_FAMILY__v1.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_PACKET_SMOKE_FAMILY__v1.md`
- observed:
  - early packet proof admits:
    - `correlation`
    - `correlation_polarity`
    - `polarity`
  - strongest positive packet witness extends the residue to:
    - `entropy`
    - `production`
  - the bookkeeping-side target still fails on:
    - `UNDEFINED_LEXEME:rate`
    - `TERM_DEF_REQUIRES_MATH_DEF`
    - `CANON_PERMIT_REQUIRES_TERM_DEF`
- interpretation:
  - direct packet-only pressure is useful helper/bootstrap evidence on the correlation side of the entropy bridge
  - it is stronger than the memo-local single-term route, but it does not currently prove `correlation_polarity` as a narrow executable survivor
  - the bookkeeping side is still blocked by lower-loop `rate` leakage and should not be forced through helper admission

Operational rule:
- if a narrow entropy route is needed, use direct packet-only pressure only as helper/bootstrap evidence on the correlation side
- do not keep tuning memo-local single-term entropy routes
- keep bookkeeping-side pressure inside the broad exploratory entropy bridge until a colder witness path avoids `rate` leakage

### F) Entropy residue-broad variant
- run:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BRIDGE_RESIDUE_BROAD_CLUSTER__v1.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_RESIDUE_BROAD_CLUSTER__v1.md`
- wrapper result:
  - `PASS__EXECUTED_CYCLE`
  - `canonical_term_count = 41`
  - `graveyard_count = 153`
  - `kill_log_count = 153`
  - `sim_registry_count = 247`
- direct target read:
  - `correlation_polarity` survives under this broad residue pressure
  - `entropy_production_rate` survives under this broad residue pressure
- residue-library read:
  - configured terms:
    - `carnot_engine`
    - `szilard_engine`
    - `maxwell_demon`
  - explicit library coverage remains:
    - `0 / 3`
  - final fill status:
    - `force_fill_by_fuel = true`
    - `force_fill_by_library = false`
    - `fuel_coverage = 0.5333333333333333`
    - `library_coverage = 0.0`

Interpretation:
- this profile is the correct broad executable entropy pressure surface when residue-quarry tagging is needed
- it gives rich graveyard / kill / sim pressure without narrowing down to the thin bookkeeping route
- it should not yet be read as direct engine-name graveyard ingestion for:
  - `carnot_engine`
  - `szilard_engine`
  - `maxwell_demon`

Operational rule:
- keep `entropy_bridge_residue_broad` as a broad-mode validity profile
- use it for residue-tagged entropy pressure, not for claiming literal classical-engine graveyard occupancy
- if direct engine-name graveyard occupancy becomes a real goal later, add a stronger injection mechanism instead of over-interpreting the current library-term flag

Seeded rescue-stop rule:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BRIDGE_RESCUE_CONTINUATION_CLUSTER__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_RESCUE_CONTINUATION_CLUSTER__v1.md`
- observed family read:
  - seeded continuation can terminate cleanly on `STOPPED__RESCUE_NOVELTY_STALL`
  - the rescue-side stop remains a valid saturation proof rather than a runner fault
  - later retained rescue controls keep the driver tail in `process_phase = rescue`
- operational reading:
  - a seeded continuation may terminate cleanly on `STOPPED__RESCUE_NOVELTY_STALL`
  - this is a valid rescue-side saturation proof, not a runner fault
