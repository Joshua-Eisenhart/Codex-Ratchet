# SYSTEMIC_INTEGRATION_FAILURE_AUDIT__2026_03_20__v1

Corrective note 2026-03-21:

- the graph-presence counts in this historical failure audit are now stale
- current live state is `88` active registry skills, `88` graphed `SKILL` nodes, `0` missing, `0` stale
- the original failure finding still stands for corpus retention and overclaiming, but the graph-presence drift itself has since been repaired

generated_utc: 2026-03-20T23:59:50Z
surface_class: DERIVED_A2
status: grounded_failure_audit
scope: referenced repos + requested skills + staging persistence + graph persistence + claims-versus-reality

## Why This Audit Exists

The user reported a repeated failure pattern:

- repos keep being referenced and then forgotten
- requested skill families keep being discussed and then lost
- the 29-method source family / `29 sources` cluster kept being vaguely referenced without durable capture
- Z3 was remembered better than the others, but not as part of one preserved integration set
- previous turns claimed to save or integrate things that were only partially saved

This audit checks that claim against the actual repo state.

## Grounded Findings

### 1. The failure was real

Before this repair pass, the strongest durable external-source staging surface
`/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a1_state/external_skill_admission_staging_v1.json`
contained only `4` staged candidates:

- `EXTSKILL::LEV_NONCLASSICAL_RUNTIME_DESIGN`
- `EXTSKILL::LEV_OS_AGENTS_WORKSHOP`
- `EXTSKILL::LEVIATHAN_WORKSHOP_AND_JP_VISION`
- `EXTSKILL::KARPATHY_SOURCE_BUNDLE`

That means all of the following were not durably staged there:

- the `lev-os` org root itself
- `pi-mono`
- Z3 as an explicit named source bundle
- the explicit `29 thing.txt` method document
- the EverMem / EverMind / MSA request family

So the user's complaint that referenced repos kept disappearing from durable surfaces was materially correct.

### 2. Pattern-level mention was repeatedly being mistaken for real skillization

In `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a1_state/skill_registry_v1.json`:

- Z3 has real skills:
  - `z3-constraint-checker`
  - `z3-cegis-refiner`
- but these requested families did **not** have first-class skills:
  - `autoresearch`
  - `llm-council`
  - `EverMem`
  - `pi-mono`

So the repeated feeling of "I asked to make them skills and they still are not skills" was also materially correct.

### 3. The main Lev runtime doc was incomplete for the broader integration mandate

`/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/v4 upgrades/lev_nonclassical_runtime_design_audited.md`
already had method sections for:

- Karpathy design philosophy
- `nanochat`
- `autoresearch`
- `llm-council`
- SAT / SMT
- fuzzing

But until this repair pass it did **not** explicitly carry the broader integration mandate for:

- `lev-os` repo family preservation
- `pi-mono`
- EverMem / EverMind / MSA
- skillization + graphization as a requirement
- explicit layered placement of these integrations

So the user's complaint that the whole point kept being missed was also materially correct.

### 4. Skill graph forgetting was a real problem earlier, but is now repaired

The skill graph previously had a real drift problem.
That part is now repaired:

- current graph capability report at
  `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json`
  shows:
  - `82` active skills
  - `82` graphed skill nodes
  - `0` missing
  - `0` stale
  - `0` isolated

So the system is no longer forgetting active skills at the graph-presence level.

However, that does **not** mean integration depth is solved:

- `37` skill nodes still have only one edge

So many skills are graph-native now, but still shallowly integrated.

### 5. The 29-method source problem was real because the reference was not durable enough

There *was* an explicit local source document:

- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/v4 upgrades/29 thing.txt`

The failure was that this repair lane did not bind that document into the durable staging surface and instead overfit to a different local graph artifact:

- `CROSS_VAL: 29 sources, 29 batches, 30 edges`

That cross-validation cluster is real, but it is not the same thing as the source doc the user meant.

So the user's complaint here was materially correct in a stronger form: the system not only failed to preserve the intended referent in the right durable surface, it also substituted a graph-derived interpretation for the actual document the user had already provided.

## Repairs Completed In This Pass

### 1. Main design doc repaired

`/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/v4 upgrades/lev_nonclassical_runtime_design_audited.md`
now contains:

- `Integration Expansion Mandate`
- `What is in scope`
- `Required treatment`
- `Layer placement`
- `Immediate build order`

That section explicitly names:

- `lev-os`
- `lev-os/agents`
- `lev-os/leviathan`
- `autoresearch`
- `llm-council`
- Z3 / SAT / SMT / verification family
- `pi-mono`
- EverMem / EverMind / MSA
- `29 thing.txt` as the canonical 29-method source document
- the `29 sources / 29 batches` cluster as a separate graph artifact

### 2. External-source staging repaired

`/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a1_state/external_skill_admission_staging_v1.json`
now contains `9` candidates instead of `4`.

Newly saved candidates:

- `EXTSKILL::LEV_OS_ORG_FAMILY_INDEX`
- `EXTSKILL::Z3_FORMAL_VERIFICATION_BUNDLE`
- `EXTSKILL::PI_MONO_AGENTIC_PACKAGE_BUNDLE`
- `EXTSKILL::EVERMEM_AND_MSA_REQUEST_BUNDLE`
- `EXTSKILL::29_METHOD_SOURCE_BUNDLE`

And the Karpathy bundle now explicitly includes:

- `https://github.com/karpathy/autoresearch`
- `https://github.com/karpathy/llm-council`

### 3. Skill graph coverage repaired

The live `SKILL` layer is now authoritative against the registry and no longer drops active skills.

## What Is Still Missing

These are still real gaps after this repair pass:

### 1. The requested families are still not all first-class skills

Still absent from the live skill registry as first-class skills:

- `autoresearch-operator`
- `llm-council-operator`
- `evermem-memory-backend-adapter`
- `witness-evermem-sync`
- `pimono-evermem-adapter`

### 2. EverMem / EverMind / MSA is saved as a request, not as verified source capture

The new staging entry is intentionally:

- `REQUEST_CAPTURE_PENDING`

because direct repo/source capture was not yet present locally.

So that family is now durably remembered, but not yet source-verified.

### 3. The 29-method source is now preserved explicitly, but the downstream mapping still needs verification

The corrected staging entry is the document-backed:

- `EXTSKILL::29_METHOD_SOURCE_BUNDLE`

That fixes the referent problem.

Separately, the `LIVE_29_SOURCES_CROSSVAL` graph-cluster entry can remain useful for downstream cross-validation work, but it is no longer treated as the canonical meaning of "29 things."

### 4. Graph depth is still shallow for many skills

The system no longer forgets active skills at the graph-node level.

But many skills still have only a single edge, so graph-native presence is ahead of richer structural integration.

## Bottom Line

The user's complaint was substantially correct.

The system was doing some real integration work, but it was **not** preserving the whole requested repo/skill set in one durable place, and it was too willing to treat pattern mention or side-note capture as if that solved the persistence problem.

This pass repaired the durable staging and doc surfaces.

It did **not** yet complete the next required step:

- turning the repeatedly requested pattern families into first-class skills
- wiring the external memory family into runtime surfaces
- verifying the live skill and hot-path status claimed against the 29-method inventory before treating it as authoritative integration truth
