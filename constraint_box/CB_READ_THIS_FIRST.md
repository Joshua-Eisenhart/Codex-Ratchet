# ConstraintBox — read this first

CLAUDE.md sends every session here before it touches `constraint_box/`. This file gives the
reading order and a map of the ConstraintBox documents, grouped by audience, with supersessions
named. It indexes; it does not relocate. No file was moved or renamed to produce it.
Consolidated 2026-08-08 from three reading lanes; coverage limits are stated in section 6.

**Scope warning — this index covers about 6% of the material.** ConstraintBox material is
often not labelled ConstraintBox. Owner ruling, 2026-08-08: *"CB materials might not be
labeled exactly CB. as in megaboot, thread a2 a1 a0 a b sim, codex ratchet, claimgate, and
the wizard are all CB."* Measured against that definition, the repo holds 958 CB-family
markdown documents:

| vocabulary | docs |
|---|---|
| codex ratchet | 546 |
| wizard | 198 |
| `a2_state` / THREAD_A2 | 186 |
| constraintbox | 119 |
| claimgate | 119 |
| megaboot | 20 |
| union, deduplicated | **958** |

This index describes **56** of them — the subset labelled ConstraintBox. The A2 thread
material alone (186 docs) is larger than the entire CB-labelled set and is not indexed here
at all. Unindexed CB-family material clusters in `docs` (85), `skill_specs` (73),
`READ ONLY Reference Docs` (13), `ops` (11), `constraint_core` (11), `thread_returns` (10),
`receipts` (9) and `legacy_docs` (8). Treat this file as a map of one district, not the city.

## 1. What ConstraintBox is

Owner canon, from `constraint_box/docs/CB_DEFINITION_OWNER_CANON_20260806.md` (owner-minted;
it supersedes every model-authored description in this repository):

> CB is a deterministic gating LLM constraint harness for mass looping swarms, of diverse
> LLMs, where the LLMs don't control their own gating.

Every clause carries weight. The gate is code, replayable without a model. The harness
constrains the option set and the format; it does not decide truth. The subject is many agents
over many waves, not one careful thread. Diversity is structural, through diverse MMMs and real
prompt diversity. And the decisive separation: a producer never sets its own ceiling. Five core
tools (z3, cvc5, sympy, rustworkx, maude) cover deciding and rewriting; the owner names a
measured secondary tier of deterministic libraries for format, range, custody, canonicalisation,
graph and diversity obligations.

## 2. Read in this order

1. `constraint_box/docs/CB_DEFINITION_OWNER_CANON_20260806.md` — the owner's definition of CB,
   clause by clause, and why LevOS alone is insufficient.
2. `constraint_box/docs/00_READ_FIRST.md` — how `docs/` is organised, the claim ceiling
   (`passes local rerun`, not promoted), and which inherited docs to trust.
3. `constraint_box/README.md` — install and the command surface (`constraintbox --help`).
4. `constraint_box/docs/01_THEORY.md` — why producer-visible receipt checks fail; the design
   argument behind the gates.
5. `constraint_box/docs/02_ARCHITECTURE.md` — what is built now: modules, claim flow, exit
   codes, and the live gaps.
6. `constraint_box/docs/04_FOR_LLM_AGENTS.md` — the testable rules that bind you if you are an
   agent working in this tree. (`03_PROCESSES.md` gives the commands; read it when you run things.)
7. `constraint_box/PROVENANCE.md` — the defect register: what is broken, unmeasured,
   duplicated, or awaiting an owner decision. Keep it open while changing code.
8. `MODEL_DOSSIER/owner_authority/03_CONSTRAINTBOX_TOP_VIEW_MASTER_PLAN_20260727.md` — the full
   architecture, gates, authority model, and the CB-M-000 to CB-M-100 roadmap.

## 3. The map

Every document below was read by a 2026-08-08 reading lane. Documents that exist but were not
read are listed in section 6, not here; their content is unverified. Paths are relative to the
repo root unless they start with `constraint_box/` internals shown in full.

### Read first

| Path | What it gives you |
|---|---|
| `constraint_box/CB_READ_THIS_FIRST.md` | This file: reading order and the map. |
| `constraint_box/docs/00_READ_FIRST.md` | Entry point for `docs/`: current series order, claim ceiling, which inherited docs to trust, and why `scripts/cb_*.py` are not the product. |

### Owner canon (top authority)

| Path | What it gives you |
|---|---|
| `MODEL_DOSSIER/owner_authority/03_CONSTRAINTBOX_TOP_VIEW_MASTER_PLAN_20260727.md` | Complete system architecture in 14 sections: definitions, boundaries, authority model, gates, loops, integration levels, formal agents, and milestones CB-M-000 to CB-M-100. |
| `MODEL_DOSSIER/owner_authority/03s_OWNER_NONASSOCIATIVITY_FLOOR_CORRECTION_20260711.md` | Binding language correction: the floor is association-unspecified, not nonassociative; nonassociativity is earned only by a nonzero witness. |
| `constraint_box/docs/CB_DEFINITION_OWNER_CANON_20260806.md` | The owner's one-line CB definition with five load-bearing clauses and the deterministic tool mapping. A second copy exists at `MODEL_DOSSIER/CB_DEFINITION_OWNER_CANON_20260806.md`; no primary has been named. |
| `constraint_box/docs/OWNER_RULINGS_VERBATIM_20260806.md` | The owner's verbatim policy statements and corrections from the 2026-08-06 CB session. Outranks all model summaries. A likely copy sits at `MODEL_DOSSIER/owner_authority/CB_OWNER_RULINGS_VERBATIM_20260806.md` (unread, unverified). |
| `constraint_box/docs/WIZARD_WAVE_MODEL_OWNER_CANON_20260806.md` | The owner's general Wizard wave model: nesting, why nesting is the mechanism, and the original purpose. |
| `constraint_box/docs/VOICES_AND_MMM_DIVERGENCE_MECHANISM_20260806.md` | The owner's explanation of voices and MMMs as pre-language salience, not rules, and the four-beat diverge-converge-sequence-loop cycle. |

### Operator (running and inspecting CB)

| Path | What it gives you |
|---|---|
| `constraint_box/README.md` | Package overview, formal kernel boundary, installation groups, and the public command surfaces. |
| `constraint_box/docs/01_THEORY.md` | Why producer-visible receipt checks fail; five failed candidates. |
| `constraint_box/docs/02_ARCHITECTURE.md` | Built modules, claim flow, exit codes, and documented live gaps. |
| `constraint_box/docs/03_PROCESSES.md` | Commands run on this host; procedures for checks and fixtures. |
| `constraint_box/docs/05_FINDING_SLOP.md` | The repo-root slop scanner, regression tracking, CI report, and declared limits. |
| `constraint_box/docs/07_CR_SIM_SLICE_INTEGRATION.md` | The CB-owned bridge to the Codex-Ratchet simulation estate: registered profiles and the receipt contract. |
| `constraint_box/docs/09_CR_SIM_ENGINE_INTEGRATION_INDEX.md` | Integration index separating CB controller, fixed external flows, and the CR slice; nine levels, 50+ tool rows. |
| `constraint_box/docs/FORMAL_KERNEL_STATUS.md` | Formal index of 14 tools with admission levels and the authority structure. |
| `constraint_box/docs/CB_SYSTEM_LAYOUT_20260807.md` | What CB actually is on disk: the packaged product versus swarm scripts that never import it. |
| `constraint_box/docs/CB_COMPONENT_INDEX_20260807.md` | 986 components across eight domains, each with a state label and a next action. |
| `constraint_box/docs/V9_STATE_AND_PLAN_20260806.md` | Checkout state and the v9 boundary scaffolding plan. |
| `constraint_box/docs/WIZARD_V4_3_ACTUAL_STRUCTURE_20260806.md` | The actual v4.3 instantiation enumerated from AGENTS_MANIFEST: 33 agent specs, 5 managers, 9 parents, 9 voices, 9 wizard-loop agents. |
| `constraint_box/docs/WIZARD_WAVES_COUNCILS_AND_SKILLS_20260806.md` | Skills on disk, measured wave structures, path truth, and scaling constraints. |
| `constraint_box/docs/WIZARD_READ_AND_CB_INTEGRATION_20260806.md` | Wizard as exploration engine, why CB needs it, three sequential councils, and two CB-compatibility rules. |
| `constraint_box/docs/NESTED_COUNCILS_FULL_ENUMERATION_20260806.md` | Councils and members read from disk: three living layers plus the deterministic floor. |
| `constraint_box/docs/WAVE_TAXONOMY_ROLES_AND_HARVEST_20260806.md` | Nine wave kinds, dead-loop rules, and member role reuse across waves. |
| `constraint_box/docs/COUNCIL_MEMBER_CATALOG_20260806.md` | All possible council members by five kinds, with deterministic members as the anchor. |
| `constraint_box/PROJECT_STATE.md` | Disk inventory generated 2026-08-07T21:49:17Z. Stale snapshot: it predates the 2026-08-08 MODEL_DOSSIER recovery (commit 5ab8fd26d). Regenerate with `cb_project_state.py` before trusting counts. |

### Builder (designing or extending CB)

| Path | What it gives you |
|---|---|
| `constraint_box/docs/04_FOR_LLM_AGENTS.md` | Testable rules for agents working in this tree. |
| `constraint_box/docs/08_MANIFOLD_FOUNDATION_TIME_FIRST.md` | Finite manifold carrier seed with time-opening and constraint layers; testable notation, not physics. |
| `constraint_box/docs/10_PAIRED_EXTENSION_NOMINALIST_PACKET.md` | Finite set-level witness for a two-sector extension; three lanes with a shared fixture and deterministic observation. |
| `constraint_box/docs/CB_EXEMPLAR_PROGRAM_20260806.md` | Exemplification versus integration; three exemplar classes and what each member kind requires. |
| `constraint_box/docs/CB_SWARM_DRIVER_RECOVERED_DESIGN_20260806.md` | Recovered design: soft side proposes, hard wall decides, promotion via deterministic gate. |
| `constraint_box/docs/INTEGRATION_WAVE_PROGRAM_20260806.md` | Proposed five-wave integration structure with a deterministic exit condition. Not yet run. |
| `constraint_box/docs/WIZARD_V4_3_READ_FROM_PACKET_20260806.md` | Reading from the actual v4.3 runtime file; the Route-Truth field contract with five explicit fields. |
| `constraint_box/doctrine/00_START_HERE/README.md` | The doctrine pack's design intent and its 11-step load order. Note: the load order cites `../06_MANIFEST/ESTATE_VERIFICATION.md`, which does not exist; the file is at `constraint_box/doctrine/ESTATE_VERIFICATION.md`. |
| `constraint_box/doctrine/00_START_HERE/STATUS_AND_AUTHORITY.md` | The doctrine status vocabulary and what the pack does not claim. |
| `constraint_box/doctrine/PACK_CONTENTS.md` | The ideal doctrine directory structure; shows `04_SPEC` and `06_MANIFEST` directories are missing. |
| `constraint_box/doctrine/01_FOUNDATION/NOMINALIST_CR_ALIGNMENT.md` | Foundation rules: identity, equality, probability and metrics are never implicit. |
| `constraint_box/doctrine/02_ARCHITECTURE/SYSTEM_BOUNDARIES.md` | Named boundaries: CB core, MMM compiler, LLM provider, deterministic checker, ClaimGate lineage, sim estates, Codex Ratchet, LevOS, Wizard, owner, consumer. |
| `constraint_box/mmm/packs/cr-ratchet.md` | MMM pack; correctly states the composition floor is association-unspecified, with N01 order rules. |

### Auditor (checking claims against evidence)

| Path | What it gives you |
|---|---|
| `constraint_box/PROVENANCE.md` | The defect register: 51 indexed defects with severity and grep-paths, plus 8 owner decisions blocking forward progress. The authority on what is broken. |
| `constraint_box/doctrine/ESTATE_VERIFICATION.md` | Execution results from the 2026-07-25 build: estates E0-E3, fixtures F0-F9, cross-estate parity, TLA+ result. |
| `constraint_box/handoff/CB_COMPLETE_20260807T205441Z/README.md` | The 2026-08-07 structured handoff snapshot with MANIFEST.json and external dependencies. |
| `MODEL_DOSSIER/recovered_specs/CB_START_HERE.md` | Triage summary: what works, what is broken (with grep patterns), what has not been built. |
| `MODEL_DOSSIER/recovered_specs/04_CONSTRAINTBOX_CLAIMGATE_AND_SIMULATION_SYSTEM_20260727.md` | CB's relationship to ClaimGate, LevOS, Codex-Ratchet and the simulation fleet. |
| `MODEL_DOSSIER/recovered_specs/06_DETERMINISTIC_GATES_WITH_LLM_EXPLORATION.md` | The core product principle: wide LLM exploration inside bounded deterministic gates. |

### Historical (kept, not trusted for current behavior)

| Path | What it gives you | Status |
|---|---|---|
| `constraint_box/docs/01_ARCHITECTURE.md` | 2026-07-25 handoff-pack architecture (control plane, estate, adapters) at design time. | Superseded for current behavior by the current series (see `02_ARCHITECTURE.md`); kept for design context. |
| `constraint_box/docs/02_SIM_SETUP_TIERS.md` | 2026-07-25 S1-S4 estate ladder design. | Superseded for current behavior by the current series; kept for design context. |
| `constraint_box/docs/03_CLAIMGATE_FOUNDATION_FROM_MANIFOLD.md` | 2026-07-25 ClaimGate-from-manifold derivation. | Superseded for current behavior by the current series; kept for design context. |
| `constraint_box/docs/04_INSTALL_BOOT_MAINTENANCE.md` | 2026-07-25 install, boot and maintenance procedures. | Superseded for current behavior by the current series; kept for design context. |
| `constraint_box/docs/05_CR_MANIFOLD_FIXTURES.md` | 2026-07-25 CR manifold fixtures. | Superseded for current behavior by the current series; kept for design context. |
| `constraint_box/docs/06_LIMITS_AND_DEFERRED.md` | Limits and deferred work. Listed by `00_READ_FIRST.md` as an inherited pack member, though its number continues the current sequence. | Inherited; remeasure before relying on any claim in it. |
| `constraint_box/docs/WIZARD_NESTED_COUNCIL_WAVE_MODEL_20260806.md` | Machine reading of the v4.1 nested-council correction. | Superseded by `WIZARD_WAVE_MODEL_OWNER_CANON_20260806.md`; owner canon outranks the machine reading where they disagree. |
| `constraint_box/00_SEED_STATUS.md` | What the seed pack's standalone separation was aiming for. | Historical design note. |
| `constraint_box/docs/SESSION_WORK_INDEX_20260807.md` | Session record: 18 fixes (four recurring shapes), 7 builds, 8 landings, 11 runs. | Session record, not product documentation. |
| `constraint_box/docs/SESSION_SAVE_20260807.md` | Session save: 11 runs with results, four recovered lost-canon items, 16 files written. | Session record, not product documentation. |

## 4. Authority order

`MODEL_DOSSIER/owner_authority/` outranks everything machine-authored. Owner-verbatim documents
carry that rank wherever they sit, including the two owner-canon files in `constraint_box/docs/`.

Below owner canon, two surfaces bind different things and neither outranks the other. The
current `docs/` series (`00_READ_FIRST.md` through `05_FINDING_SLOP.md`, plus `PROVENANCE.md`)
binds what is true on disk now. The `doctrine/` pack binds design intent; it is design-stage
and its own load order has a broken path. Below both sit the inherited 2026-07-25 pack and
`MODEL_DOSSIER/recovered_specs/` (context; remeasure before relying), and last the 2026-08-06/07
session notes (working notes, except the owner-verbatim files).

Contradictions the reading phase found between owner canon and machine-authored docs:

1. `WIZARD_NESTED_COUNCIL_WAVE_MODEL_20260806.md` (machine reading) disagrees with
   `WIZARD_WAVE_MODEL_OWNER_CANON_20260806.md` (owner canon) on the wave model. The owner
   canon wins; the machine reading is marked superseded above.
2. The owner's association-floor correction (`03s_OWNER_NONASSOCIATIVITY_FLOOR_CORRECTION`)
   is respected inside the CB tree (checked in `docs/` and `mmm/packs/cr-ratchet.md`), but no
   sweep has verified older `system_v*` docs repo-wide. Inside CB: no live contradiction.
3. The owner-authority master plan (CB-CON-005) records that the historic May and July
   readiness indexes conflict materially and rules that a fresh scoped rerun is required.
   Never choose between them by larger count.

## 5. The collided numbering in docs/

`constraint_box/docs/` contains two numbered series that share prefixes 01-05. This was two
documentation packs landing in one directory, not one series.

Current series (2026-08-06/08, authority for current behavior): `00_READ_FIRST.md`,
`01_THEORY.md`, `02_ARCHITECTURE.md`, `03_PROCESSES.md`, `04_FOR_LLM_AGENTS.md`,
`05_FINDING_SLOP.md`, continued by `07` to `10`.

Inherited series (2026-07-25 handoff pack, design context only): `01_ARCHITECTURE.md`,
`02_SIM_SETUP_TIERS.md`, `03_CLAIMGATE_FOUNDATION_FROM_MANIFOLD.md`,
`04_INSTALL_BOOT_MAINTENANCE.md`, `05_CR_MANIFOLD_FIXTURES.md`, and (per `00_READ_FIRST.md`)
`06_LIMITS_AND_DEFERRED.md`.

The tell when you open a file: the current series describes what runs on this host now; the
inherited series describes the 2026-07-25 design and cites receipts nobody has recently
rechecked. `00_READ_FIRST.md` states that some inherited statements overstate current wiring.

Renaming was deliberately not done. Other docs and code hold references to these filenames,
and this consolidation is bound to index, not relocate. A rename proposal is recorded for the
owner in the cleanup ledger.

## 6. Gaps

What a newcomer needs that no read document currently covers, plus where this map is blind:

- Unread files: 17 files in `constraint_box/docs/` were not read by any lane
  (`ATTRACTOR_BASIN_EXTERNAL_VALIDATION`, `AUTORESEARCH_AND_NANOCHAT_FEASIBILITY_20260806`,
  `BOUNDARY_CONTRACT`, `CAPABILITY_EXECUTION_MATRIX`, `CB_BIAS_AND_DIVERSITY_MEASURE_20260806`,
  `CB_LIGHT_LIBRARY_LIST_20260807`, `CONTAINED_CORE_PRODUCT`, `CONTAINED_LOCAL_SIM_PRODUCT`,
  `CORE_INSTALL`, `CROSS_ENGINE_INTEGRATION`, `CR_LEANOUT_INVENTORY_AND_PLAN_20260806`,
  `EXTERNAL_SIM_RUNTIME_CONTRACT`, `EXTERNAL_VALIDATION_RUNBOOK`,
  `LEVIATHAN_MINILEV_CONFORMANCE`, `MINILEV_PROVIDER_RUNTIME`, `SIM_INTEGRATION_EVIDENCE`,
  `SIM_SETUP`). Most of `doctrine/` (the `03_EXECUTION/` and `05_AUDIT/` trees,
  `SOURCE_LINEAGE.md`, `VERIFICATION_RECEIPT.md`), most of `handoff/`, most of
  `MODEL_DOSSIER/recovered_specs/`, and most of `MODEL_DOSSIER/owner_authority/` are likewise
  unread. Their one-line descriptions do not appear above because nobody verified them.
- No document explains what the numbering continuation `06` to `10` collectively covers, or
  why the current series keeps counting past the collision.
- Two ClaimGate implementations exist and are diverging: repo-root `claimgate_plugin/` and
  `constraint_box/claimgate_plugin/`. No authority names which is canonical.
- No porting guide exists for moving ideas from `scripts/cb_*.py` (which do not import
  `constraintbox`) into the `mini_levos.py` kernel.
- No document states the evidence standard for moving from `promotion_allowed: false` to
  `true`; the milestone roadmap describes features, not the completion bar.
- `PROJECT_STATE.md` has no automated regeneration hook, so it goes stale within hours of any
  code edit; three staleness events are documented in one day.
- No document maps which `MODEL_DOSSIER/recovered_specs/` files duplicate `constraint_box/docs/`
  content topic by topic.
