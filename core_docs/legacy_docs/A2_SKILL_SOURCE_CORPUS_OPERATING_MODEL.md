# A2 Skill Source Corpus Operating Model

Last updated: 2026-03-21

## Purpose

This document defines how `A2` should work with:

- the Skill Source Corpus
- candidate skills
- live skills
- downloaded source repos
- graph identity
- runtime integration

The goal is to stop losing source material, stop confusing storage with understanding, and make skillization a normal controlled loop.

## Core Rule

`A2` should treat the Skill Source Corpus as a first-class input surface, not as stray tracker notes.

The root corpus docs are the human-facing front door.
Canonical persistence still lives under `system_v3/a2_state`.

That means:

1. source families get appended immediately
2. local source presence gets recorded explicitly
3. candidate skills get derived from source families
4. graph identity follows source/corpus truth
5. runtime claims only happen after live verification

## The 6-Layer Model

### 1. Owner Law

Use first:

- [01_REQUIREMENTS_LEDGER.md](%USER_HOME%/Desktop/Codex%20Ratchet/system_v3/specs/01_REQUIREMENTS_LEDGER.md)
- [02_OWNERSHIP_MAP.md](%USER_HOME%/Desktop/Codex%20Ratchet/system_v3/specs/02_OWNERSHIP_MAP.md)
- [07_A2_OPERATIONS_SPEC.md](%USER_HOME%/Desktop/Codex%20Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md)
- [19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md](%USER_HOME%/Desktop/Codex%20Ratchet/system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md)

### 2. A2 Memory / Control

Use as the bounded recovery set:

- [A2_BOOT_READ_ORDER__CURRENT__v1.md](%USER_HOME%/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_BOOT_READ_ORDER__CURRENT__v1.md)
- [A2_KEY_CONTEXT_APPEND_LOG__v1.md](%USER_HOME%/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md)
- [A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md](%USER_HOME%/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md)
- standing A2 brain/control surfaces listed in the boot read order

### 3. Skill Source Corpus

Use as the naming and source-family layer:

- [SKILL_SOURCE_CORPUS.md](%USER_HOME%/Desktop/Codex%20Ratchet/SKILL_SOURCE_CORPUS.md)
- [LOCAL_SOURCE_REPO_INVENTORY.md](%USER_HOME%/Desktop/Codex%20Ratchet/LOCAL_SOURCE_REPO_INVENTORY.md)

### 4. Skill Tracking

Use for current reality and candidate build queue:

- [REPO_SKILL_INTEGRATION_TRACKER.md](%USER_HOME%/Desktop/Codex%20Ratchet/REPO_SKILL_INTEGRATION_TRACKER.md)
- [SKILL_CANDIDATES_BACKLOG.md](%USER_HOME%/Desktop/Codex%20Ratchet/SKILL_CANDIDATES_BACKLOG.md)

### 5. Graph Layer

Use for identity and relation storage, not as the first proof of understanding:

- `system_v4/a2_state/graphs/*`

### 6. Runtime Layer

Use for actual live integration claims:

- registry load works
- runner can discover skill
- runner can dispatch skill
- behavior is verified in smokes or live path

## Required A2 Loop When A New Source Appears

When a new repo, doc, or method family is referenced:

1. Append the source family to [SKILL_SOURCE_CORPUS.md](%USER_HOME%/Desktop/Codex%20Ratchet/SKILL_SOURCE_CORPUS.md).
2. Record local presence tier in [LOCAL_SOURCE_REPO_INVENTORY.md](%USER_HOME%/Desktop/Codex%20Ratchet/LOCAL_SOURCE_REPO_INVENTORY.md).
3. Append current integration reality in [REPO_SKILL_INTEGRATION_TRACKER.md](%USER_HOME%/Desktop/Codex%20Ratchet/REPO_SKILL_INTEGRATION_TRACKER.md).
4. Append skill candidates in [SKILL_CANDIDATES_BACKLOG.md](%USER_HOME%/Desktop/Codex%20Ratchet/SKILL_CANDIDATES_BACKLOG.md).
5. Append the durable significance to [A2_KEY_CONTEXT_APPEND_LOG__v1.md](%USER_HOME%/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md).
6. Refresh canonical A2 state:
   - `doc_index.json` if the source family should be indexed
   - `fuel_queue.json` if it creates real A2 work
   - source-bound A2 surfaces only if meaning, conflict, or downstream routing changed
7. Only then claim it is saved.

## Source Presence Tiers

`A2` needs to distinguish these:

- `repo_local`: inside the current workspace
- `home_local`: local clone outside the workspace but on this machine
- `tmp_local`: local clone in `/tmp`, useful but non-durable
- `doc_only`: represented in docs/session logs/staging only
- `url_only`: external reference only

This distinction matters because it changes what A2 can honestly claim.

## Corpus To Skill Pipeline

For each source family:

1. `source family`
2. `subfamily`
3. `candidate skill/operator/adapter`
4. `registry row`
5. `graph identity`
6. `runtime proof`

Do not skip directly from source family to “live skill.”

## Live-Skill Truth Rule

For any claim that a source family or candidate is now a real live skill, verify four states separately:

1. source tracked
2. raw registry row exists
3. graph identity exists
4. live runtime discovery or dispatch is proven

Do not collapse these into one word like `integrated`.

## Immediate Recovery Queue

1. Keep `doc_index.json` directly indexing the root front-door corpus docs as well as owner-law and active A2 boot surfaces.
2. Keep a location-aware local source inventory.
3. Keep one explicit skill-source intake procedure inside A2 instead of splitting the loop across many notes.
4. Process `lev-os` local checkouts into explicit subfamilies and imported skill corpora instead of leaving them as vague repo mentions.
5. Split Retooled External Methods into subfamilies and convert them into candidate skills systematically.
6. Promote first imported or corpus-derived clusters into live selection/use.
7. Keep the first imported-cluster slice bounded and honest:
   - `a2-skill-source-intake-operator` may audit, classify, and emit staged output
   - it does not yet prove a full workshop-style import loop exists

## Current Mismatch To Keep Visible

Live skill state is now more coherent, but not complete:

- raw registry rows: `109`
- live registry loader: `109`
- live graph skill nodes: `109`
- runner-discoverable corpus-derived seeds now include:
  - `autoresearch-operator`
  - `llm-council-operator`
  - `witness-evermem-sync`
  - `a2-skill-source-intake-operator`
  - `a2-tracked-work-operator`
  - `a2-research-deliberation-operator`

That does not mean the system is fully integrated.
It means coverage and discovery are repaired enough that depth of runtime use is now the main remaining gap.

## Current Practical Conclusion

`A2` should not try to do everything through graphs.

It should:

- remember the corpus
- know what is actually local
- know what candidate skills come from each source family
- know what is merely staged
- know what is actually live

That is the minimum operating model for making skills, corpus, graphs, and runtime work together.
