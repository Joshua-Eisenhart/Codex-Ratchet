# Repo Skill Integration Tracker

Last updated: 2026-03-21

## What This Is

This is the simple front-door tracker for:

- repos and source docs you keep referencing
- method bundles you want turned into skills
- what is already saved
- what is already in the registry
- what is actually wired into runtime
- what still needs integration work

If a repo, document, paper, or idea-family is mentioned as "we should use this" or "make skills from this", it should be added here.

This file is the simple front-door append tracker for this concern.
It is a `SOURCE_CORPUS` working surface, not the canonical A2 brain.

Important rule:

- this tracker is for the broad referenced corpus, not one source doc
- [lev_nonclassical_runtime_design_audited.md](/home/ratchet/Desktop/Codex%20Ratchet/core_docs/v4%20upgrades/lev_nonclassical_runtime_design_audited.md) is an audited / reorganized rendering of the same 29-method source family rooted in [29 thing.txt](/home/ratchet/Desktop/Codex%20Ratchet/core_docs/v4%20upgrades/29%20thing.txt), not an independent second source family
- do not collapse the whole corpus back into that one file

Umbrella naming and source-family framing lives here:

- [SKILL_SOURCE_CORPUS.md](/home/ratchet/Desktop/Codex%20Ratchet/SKILL_SOURCE_CORPUS.md)

The older detailed supporting ledger is:

- [79_INTEGRATION_LEDGER__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/specs/79_INTEGRATION_LEDGER__v1.md)

Current A2 / `v4` recovery audit lives here:

- [A2_V4_RECOVERY_AUDIT.md](/home/ratchet/Desktop/Codex%20Ratchet/A2_V4_RECOVERY_AUDIT.md)
- [A2_SKILL_SOURCE_CORPUS_OPERATING_MODEL.md](/home/ratchet/Desktop/Codex%20Ratchet/A2_SKILL_SOURCE_CORPUS_OPERATING_MODEL.md)
- [LOCAL_SOURCE_REPO_INVENTORY.md](/home/ratchet/Desktop/Codex%20Ratchet/LOCAL_SOURCE_REPO_INVENTORY.md)
- [work/reference_repos/README.md](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/README.md)

## Status Words

- `saved`: the source or repo is durably recorded in the repo
- `graphed`: it is represented in graph/session surfaces
- `registry`: there are real skill records for it
- `runtime`: it is explicitly referenced in the live runner
- `partial`: some of the above are true, but not all
- `broken`: a registry entry or plan exists, but something important is missing

## Current Reality

### 1. Retooled External Methods

Main source:

- [29 thing.txt](/home/ratchet/Desktop/Codex%20Ratchet/core_docs/v4%20upgrades/29%20thing.txt)

Preferred system term:

- `Retooled External Methods`

Current state:

- `saved`
- `graphed`
- not fully converted into verified per-method live skill mappings yet

Important note:

- the `29 sources / 29 batches` graph cluster is not the same thing as `29 thing.txt`

### 2. Lev Runtime / Nonclassical Method Family

Main source:

- [lev_nonclassical_runtime_design_audited.md](/home/ratchet/Desktop/Codex%20Ratchet/core_docs/v4%20upgrades/lev_nonclassical_runtime_design_audited.md)

Current state:

- `saved`
- materially influencing the live system
- already expressed through runtime kernel, witness, intent, Z3, bounded-improve, and related runtime work

### 3. lev-os

Repos:

- [lev-os](https://github.com/lev-os)
- [lev-os/agents](https://github.com/lev-os/agents)
- [lev-os/leviathan](https://github.com/lev-os/leviathan)

Current state:

- `saved`
- staged as repo families
- external repo checkouts verified locally:
  - `work/reference_repos/lev-os/agents` at `fd5191f`
  - `work/reference_repos/lev-os/leviathan` at `f256434`
- local `Leviathan v3.2` source material has been materially processed in `system_v3` intake surfaces
- external `lev-os/agents` and `lev-os/leviathan` are only `partial`
- lightly adapted in places, but not deeply integrated yet
- huge future skill source family
- first imported cluster is now explicitly mapped:
  - `skill-source intake`
  - imported members: `lev-intake`, `skill-discovery`, `skill-builder`
  - first Ratchet-native slice: `a2-skill-source-intake-operator`
  - current staged audit output:
    - [A2_SKILL_SOURCE_INTAKE_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_SKILL_SOURCE_INTAKE_REPORT__CURRENT__v1.md)
- second imported/corpus-derived slice now exists:
  - `tracked work / planning`
  - first bounded slice: `a2-tracked-work-operator`
  - current staged audit output:
    - [A2_TRACKED_WORK_STATE__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_TRACKED_WORK_STATE__CURRENT__v1.md)
- third imported/corpus-derived slice now exists:
  - `research / deliberation`
  - first bounded slice: `a2-research-deliberation-operator`
  - current staged audit output:
    - [A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.md)

Important note:

- do not collapse the local `Leviathan v3.2` corpus, the external `lev-os/leviathan` repo, and the `lev-os/agents` repo into one blur
- `ratchet_prompt_stack.py` is one real Leviathan-derived transplant, but that does not make the full repo family hot-path integrated
- likely long-term role split:
  - `agents`: intake/admission/skill workflow mine
  - `leviathan`: outside wrapper, orchestration, memory-support, and runtime-host mine

### 4. Karpathy Family

Repos:

- [karpathy/autoresearch](https://github.com/karpathy/autoresearch)
- [karpathy/llm-council](https://github.com/karpathy/llm-council)
- [karpathy/nanochat](https://github.com/karpathy/nanochat)
- [karpathy/nanoGPT](https://github.com/karpathy/nanoGPT)
- [karpathy/llm.c](https://github.com/karpathy/llm.c)
- [karpathy/minbpe](https://github.com/karpathy/minbpe)

Current state:

- `saved`
- `registry` for `autoresearch` and `llm-council`
- runner references exist for `autoresearch` and `llm-council`
- live registry loading is now repaired
- runtime integration is still only `partial` until actual dispatch/use is re-verified cleanly
- `llm.c` and `minbpe` are locally present and now part of the umbrella corpus, but still only `partial` as skill-source inputs

### 4A. Context / Spec / Workflow / Memory Family

Repos:

- [davidkimai/Context-Engineering](https://github.com/davidkimai/Context-Engineering)
- [github/spec-kit](https://github.com/github/spec-kit)
- [obra/superpowers](https://github.com/obra/superpowers)
- [mem0ai/mem0](https://github.com/mem0ai/mem0)

Current state:

- `saved`
- local checkouts now exist:
  - `work/reference_repos/external_audit/Context-Engineering` at `6158def`
  - `work/reference_repos/external_audit/spec-kit` at `bf33980`
  - `work/reference_repos/external_audit/superpowers` at `8ea3981`
  - `work/reference_repos/external_audit/mem0` at `ec326f0`
- integration is still only `partial`
- currently most useful as a source family for:
  - append-safe context/state design
  - persistence and continuity patterns
  - live spec / plan / task coupling
  - subagent workflow, review, and verification discipline
  - scoped memory sidecars, mutation history, and export/import continuity patterns
- do not import these repos flat or treat their philosophical overlays as owner-law
- `mem0` belongs here only as a bounded sidecar-memory source family:
  - keep its scoped `user_id` / `agent_id` / `run_id` and mutation-history ideas
  - do not treat it as canonical A2/A1 memory, repo-memory replacement, or proof that the nested-graph substrate is solved
- best current role:
  - strengthen the persistent-brain / low-bloat continuity goal
  - strengthen spec-to-runtime coupling so specs do not drift into dead docs
  - strengthen workflow discipline for the broader skill ecosystem
  - strengthen memory-sidecar hygiene and continuity export/import patterns without replacing repo-held truth surfaces

### 5. Z3 / Formal Verification Family

Repo:

- [Z3Prover/z3](https://github.com/Z3Prover/z3)

Current state:

- `saved`
- `registry`
- `runtime` for `z3-constraint-checker`
- still partial for the broader verification family

### 6. pi-mono

Repo:

- [badlogic/pi-mono](https://github.com/badlogic/pi-mono)

Current state:

- `saved`
- `graphed`
- source family ingested through session work
- first bounded outside-control-shell / session-host slice now exists:
  - `outside-control-shell-operator`
  - status: read-only / repo-held report + packet / no durable state
  - current repo-held outputs:
    - [A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT__CURRENT__v1.json)
    - [A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT__CURRENT__v1.md)
    - [A2_PIMONO_OUTSIDE_SESSION_HOST_PACKET__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_PIMONO_OUTSIDE_SESSION_HOST_PACKET__CURRENT__v1.json)
- local checkouts verified at:
  - `/home/ratchet/Desktop/Codex Ratchet/work/reference_repos/other/pi-mono` at `3563cc4d`
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/pi-mono` at `3563cc4d`
- strongest current extraction seams are:
  - `resource-loader` / resource bundle host pattern
  - `plan-mode` and `subagent` controller pattern
  - `agent` + `ai` provider bridge
  - `mom` lane-memory split
- adapter skillization is still `partial`
- runtime integration depth is still `partial`
- likely best role: outside claw/control layer around A2 rather than internal A2 memory law

### 7. EverMem / EverMind / MSA

Requested family:

- EverMemOS / EverMind-style memory backend
- MSA / Memory Sparse Attention

Current state:

- `saved`
- local organized checkouts now exist:
  - `/home/ratchet/Desktop/Codex Ratchet/work/reference_repos/EverMind-AI/EverMemOS` at `3c9a2d0`
  - `/home/ratchet/Desktop/Codex Ratchet/work/reference_repos/EverMind-AI/MSA` at `8631c9d`
- raw EverMem adapter rows and files exist
- live registry loading is now repaired
- the first two honest EverMem runner seams are now repo-held:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/EVERMEM_WITNESS_SYNC_STATE__CURRENT__v1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.md`
- the next bounded EverMem slice is now landed as `witness-memory-retriever`:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/WITNESS_MEMORY_RETRIEVER_REPORT__CURRENT__v1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/WITNESS_MEMORY_RETRIEVER_REPORT__CURRENT__v1.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/WITNESS_MEMORY_RETRIEVER_PACKET__CURRENT__v1.json`
- the bounded backend-reachability audit slice is now landed:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_REPORT__CURRENT__v1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_REPORT__CURRENT__v1.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_PACKET__CURRENT__v1.json`
- current repo-held local report status is `sync_failed` because no reachable local EverMem service exists in this environment, but the cursor and report surfaces are now preserved correctly
- current retrieval-probe status is `attention_required` with bounded next step `hold_at_retrieval_probe`
- current backend-reachability status is `attention_required` with bounded next step `start_docker_daemon`
- the adapter search contract is now repaired in [evermem_adapter.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/evermem_adapter.py) to use `GET /api/v1/memories/search`
- EverMem runtime use is still `partial`
- EverMem is now explicitly a side-project lane, not the main build focus
- MSA is still mostly a future backend candidate, not a live system component
- likely role split:
  - EverMemOS first as outside memory/control support and witness backend
  - MSA later as model/backend expansion, not first-line A2 repair

### 8. Additional local source repos

Repos:

- [deepmind/alphageometry](https://github.com/google-deepmind/alphageometry)
- [aiming-lab/AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw)
- [ellisk42/dreamcoder-ec](https://github.com/ellisk42/dreamcoder)

Current state:

- `saved`
- locally present in the canonical reference tree
- now promoted into the umbrella corpus
- still only `partial` as skill-source inputs
- not yet turned into explicit Ratchet clusters or live runtime lanes

### 9. Local source-doc families

Sources:

- [Leviathan v3.2 word.txt](/home/ratchet/Desktop/Codex%20Ratchet/core_docs/a2_feed_high%20entropy%20doc/Leviathan%20v3.2%20word.txt)
- [holodeck docs.md](/home/ratchet/Desktop/Codex%20Ratchet/core_docs/a2_feed_high%20entropy%20doc/holodeck%20docs.md)
- [BOOTPACK_THREAD_B_v3.9.13.md](/home/ratchet/Desktop/Codex%20Ratchet/core_docs/upgrade%20docs/BOOTPACK_THREAD_B_v3.9.13.md)

Current state:

- `saved`
- part of the broad source corpus
- still only `partial` as skill-source inputs
- need better family-level tracking instead of disappearing into high-entropy doc piles

### 10. OpenClaw-RL / next-state signal family

Sources:

- [OpenClaw-RL paper](https://arxiv.org/abs/2603.10165)
- [Gen-Verse/OpenClaw-RL](https://github.com/Gen-Verse/OpenClaw-RL)
- [OPENCLAW_RL__REFERENCE_NOTE__2026_03_21__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/work/external_refs/OPENCLAW_RL__REFERENCE_NOTE__2026_03_21__v1.md)

Current state:

- `saved`
- first bounded paper-derived slice is now real:
  - `a2-next-state-signal-adaptation-audit-operator`
- second bounded paper-derived slice is now real:
  - `a2-next-state-directive-signal-probe-operator`
- `registry` and runner discovery are real for that slice
- `registry`, runner discovery, and graph presence are now real for the directive probe slice as well
- runtime integration is still only `partial`
- current role is source-bound pattern mining for:
  - next-state signals
  - directive correction
  - async improvement architecture
- current emitted outputs:
  - [A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.json)
  - [A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.md)
  - [A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_PACKET__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_PACKET__CURRENT__v1.json)
  - [A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_REPORT__CURRENT__v1.json)
  - [A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_REPORT__CURRENT__v1.md)
  - [A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_PACKET__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_PACKET__CURRENT__v1.json)
  - [A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT__CURRENT__v1.json)
  - [A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT__CURRENT__v1.md)
  - [A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_PACKET__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_PACKET__CURRENT__v1.json)
  - [A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_REPORT__CURRENT__v1.json)
  - [A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_REPORT__CURRENT__v1.md)
  - [A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_PACKET__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_PACKET__CURRENT__v1.json)

Important note:
- the directive probe now has real post-action witness material and currently returns `ok`
- current witness-side signal counts are `3` next-state candidates / `3` directive signals / `1` evaluative signal
- the new bridge slice is now landed as `a2-next-state-improver-context-bridge-audit-operator`
- current bridge result is `admissible_as_first_target_context_only`
- the new consumer-admission slice is now landed as `a2-next-state-first-target-context-consumer-admission-audit-operator`
- `skill-improver-operator` now exposes an explicit first-target context contract
- current consumer result is `candidate_first_target_context_consumer_admissible`
- the new consumer-proof slice is now landed as `a2-next-state-first-target-context-consumer-proof-operator`
- current proof result is `ok`
- current next step is `hold_consumer_proof_as_metadata_only`
- keep the lane audit-only / non-learning / non-runtime-live even though the witness blocker is now cleared
- keep the bridge limited to the one proven target class and do not treat it as second-target admission
- keep the consumer proof metadata-only / dry-run / no-write and do not treat the explicit owner contract as live-learning, runtime-import, or graph-backfill permission

- do not treat this as imported OpenClaw runtime or online RL
- do not claim live policy mutation or PRM/judge/trainer integration
- do not claim graph backfill or graph-link seeding from this bridge slice
- do not pretend a repo-held consumer packet preview means the live consumer path already exists
- current local checkout attempt at `work/reference_repos/Gen-Verse/OpenClaw-RL` is not yet verified as a stable local repo

## Skills Already Real

These exist as real repo files and/or raw registry rows, but that is not the same thing as proven live runtime integration:

- `autoresearch-operator`
- `llm-council-operator`
- `z3-constraint-checker`
- `z3-cegis-refiner`
- `property-pressure-tester`
- `differential-tester`
- `structured-fuzzer`
- `model-checker`
- `bounded-improve-operator`
- `fep-regulation-operator`
- `frontier-search-operator`
- `evermem-memory-backend-adapter`
- `witness-evermem-sync`
- `witness-memory-retriever`
- `pimono-evermem-adapter`
- `a2-skill-source-intake-operator`
- `a2-tracked-work-operator`
- `a2-research-deliberation-operator`
- `a2-workshop-analysis-gate-operator`
- `a2-skill-improver-dry-run-operator`

These runtime substrate files also matter even when they are not thought of as "skills" in the narrow sense:

- [runtime_state_kernel.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/runtime_state_kernel.py)
- [witness_recorder.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/witness_recorder.py)
- [runtime_graph_bridge.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/runtime_graph_bridge.py)
- [a2_graph_refinery.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/a2_graph_refinery.py)
- [intent_control_surface_builder.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/intent_control_surface_builder.py)

## Things Still Wrong

- graph coverage is now repaired at `110` active registry skills, `110` graphed skill nodes, `0` missing, and `0` stale
- graph presence is better than it was, but integration depth is still shallow
- `36` skill nodes still have only one graph edge
- current graph truth is still closer to coverage than to the intended control substrate
- the intended graph is not one flat skill graph; it is a nested graph family or graph-of-graphs that should reflect constraints, witnesses, transitions, intents, source families, and skills together
- active source-bound graph-shaping pressure includes `axis0` and nested Hopf-tori, but those remain design pressure, not earned runtime semantics
- `witness-evermem-sync` and `witness-memory-retriever` are the only EverMem seams on a proven runner/discoverable path today
- durable sync plus bounded witness-seam retrieval are now landed
- broader EverMem claims are still unearned:
  - no startup retrieval/bootstrap path
  - no pi-mono memory integration
  - no proof against a live local EverMem service yet
  - current retrieval probe is explicitly held at `hold_at_retrieval_probe`, not widened into a broader memory claim
  - current reachability audit is explicitly held at `start_docker_daemon`, not widened into service-start/bootstrap claims
- keep the EverMem lane as a bounded side project unless local backend reachability is actually earned
- `evermem-memory-backend-adapter` is real, but the file naming is inconsistent because the skill id maps to [evermem_adapter.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/evermem_adapter.py)
- some older audit notes still overclaim or are stale
- the deeper A2 persistent-brain / owner-law boot path is still weak, which means tracking can still drift unless it is actively refreshed
- `skill-improver-operator` is still not honest as a live repo-mutating meta-skill:
  - [SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json) currently marks it `bounded_ready_for_first_target`
  - that is still narrower than general live repo mutation; the explicit gate remains in place

## What We Need Next

1. Keep [SKILL_SOURCE_CORPUS.md](/home/ratchet/Desktop/Codex%20Ratchet/SKILL_SOURCE_CORPUS.md) updated as the structured umbrella meta doc instead of letting it regress back to a shallow family list.
2. Keep the A2-side intake loop live in [A2_SKILL_SOURCE_CORPUS_OPERATING_MODEL.md](/home/ratchet/Desktop/Codex%20Ratchet/A2_SKILL_SOURCE_CORPUS_OPERATING_MODEL.md) and [A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md).
3. Extract `lev-os/agents` further as a real imported skill corpus with keep/adapt/mine/skip classification and first live cluster promotion.
  - the bounded promotion-audit slice is now real:
    - `a2-lev-agents-promotion-operator`
  - `SKILL_CLUSTER::lev-formalization-placement` now has seven bounded landed slices:
    - `a2-lev-builder-placement-audit-operator`
    - `a2-lev-builder-formalization-proposal-operator`
    - `a2-lev-builder-formalization-skeleton-operator`
    - `a2-lev-builder-post-skeleton-readiness-operator`
    - `a2-lev-builder-post-skeleton-follow-on-selector-operator`
    - `a2-lev-builder-post-skeleton-disposition-audit-operator`
    - `a2-lev-builder-post-skeleton-future-lane-existence-audit-operator`
  - current live graph truth:
    - `110` active registry skills
    - `110` graphed `SKILL` nodes
    - `0` missing
    - `0` stale
  - the landed proposal slice remains proposal-only and non-migratory
  - the landed skeleton slice remains scaffold-only and non-migratory
  - the landed readiness slice remains selector-admission-only, non-migratory, and non-runtime-live
  - current admission decision: `admit_for_selector_only`
  - the landed follow-on selector slice remains selector-only, non-migratory, and non-runtime-live
  - current selected follow-on branch: `post_skeleton_follow_on_unresolved`
  - the landed disposition slice remains branch-governance-only, non-migratory, and non-runtime-live
  - current disposition: `retain_unresolved_branch`
  - the landed future-lane existence slice remains branch-governance-only, non-migratory, and non-runtime-live
  - current future-lane existence decision: `future_lane_exists_as_governance_artifact`
  - current bounded outcome: `hold_at_disposition`
  - any migration/runtime/imported-runtime-ownership follow-on remains separately gated and unresolved
  - refreshed selector truth now treats that cluster as landed and parked:
    - `landed_lev_cluster_count = 6`
    - `parked_lev_cluster_count = 1`
  - `SKILL_CLUSTER::lev-autodev-exec-validation` now has its first bounded landed slice:
    - `a2-lev-autodev-loop-audit-operator`
    - status: audit-only / nonoperative / non-migratory / non-runtime-live
  - `SKILL_CLUSTER::lev-architecture-fitness-review` now has its first bounded landed slice:
    - `a2-lev-architecture-fitness-operator`
    - status: audit-only / nonoperative / non-migratory / non-runtime-live
  - current lev selector state is:
    - `landed_lev_cluster_count = 7`
    - `parked_lev_cluster_count = 1`
    - `has_current_unopened_cluster = False`
  - current non-lev source-family reselection state is now explicit:
    - selector slice landed: `a2-source-family-lane-selector-operator`
    - `SKILL_CLUSTER::context-spec-workflow-memory` now has its first bounded landed slice:
      - `a2-context-spec-workflow-pattern-audit-operator`
      - status: audit-only / nonoperative / non-runtime-live
      - and a second bounded landed selector slice:
        - `a2-context-spec-workflow-follow-on-selector-operator`
      - and a third bounded landed continuity-shell slice:
        - `a2-append-safe-context-shell-audit-operator`
      - status: audit-only / nonoperative / non-runtime-live
      - and a fourth bounded landed post-shell selector slice:
        - `a2-context-spec-workflow-post-shell-selector-operator`
      - current next step: `hold_cluster_after_append_safe_shell`
      - first standby follow-on if explicitly reopened later: `a2-executable-spec-coupling-audit-operator`
      - `scoped_memory_sidecar` is blocked while EverMem stays `attention_required`
    - `SKILL_CLUSTER::karpathy-meta-research-runtime` now also has its first bounded landed slice:
      - `a2-autoresearch-council-runtime-proof-operator`
      - status: audit-only / proof-only / non-runtime-live
      - current next step: `hold_first_slice_as_runtime_proof_only`
    - current selector result is now fail-closed:
      - no bounded source-family lane is currently eligible for explicit reselection
    - there is no current bounded fallback while the other non-lev lanes remain held
4. Keep the first imported cluster honest:
  - `a2-skill-source-intake-operator` is now real as a bounded A2 audit slice
  - the wider workshop/discovery/build loop is still only partial
5. Design the graph substrate explicitly instead of only repairing graph counts:
  - separate coverage graph, control graph, witness graph, and transition/failure-basin projections where needed
  - make base constraints and their natural extensions graph-native instead of leaving them doc-only
  - keep graph contracts explicit enough that specs stay coupled to the system rather than drifting into unread prose
  - keep the current `pydantic + NetworkX + JSON` surfaces as the auditable carrier while testing a layered expansion path:
    - `TopoNetX`-class tools for higher-order topology
    - `PyG` / `DGL` for tensor-valued edge dynamics
    - `clifford` / `kingdon`-class geometric algebra as the preferred math sidecar, with quaternion tooling as the lighter early probe
    - sheaf tooling as a bounded transport/obstruction experiment
  - the next honest implementation move is a read-only adapter matrix, not a substrate replacement:
    - first bounded probe surface: `system_v4/a2_state/graphs/a2_low_control_graph_v1.json`
    - canonical owner graph remains `system_v4/a2_state/graphs/system_graph_a2_refinery.json`
    - first topological projection target: `TopoNetX`
    - first tensor-edge projection target: `PyG`
    - first graded-edge algebra target: `clifford`, with `kingdon` as the bridge candidate if PyTorch-coupled GA becomes useful
    - `DGL` remains optional and currently lower-priority than `PyG` for the local stack
    - that package-install blocker is now cleared inside `.venv_spec_graph`
    - the first bounded PyG contract slice now exists:
      - `pyg-heterograph-projection-audit`
      - current emitted outputs:
        - `system_v4/a2_state/audit_logs/PYG_HETEROGRAPH_PROJECTION_AUDIT__CURRENT__v1.json`
        - `system_v4/a2_state/audit_logs/PYG_HETEROGRAPH_PROJECTION_AUDIT__CURRENT__v1.md`
        - `system_v4/a2_state/audit_logs/PYG_HETEROGRAPH_PROJECTION_PACKET__CURRENT__v1.json`
    - that slice proves a read-only 6-node-store / 11-edge-store control-facing heterograph view while also showing the current bridge gaps:
      - skill nodes mostly remain a separate relation family
      - `B_OUTCOME` still lands through `EXECUTION_BLOCK`
      - `SIM_EVIDENCED` still lands through `B_SURVIVOR`
    - the first bounded bridge-gap slice now also exists:
      - `control-graph-bridge-gap-auditor`
      - current emitted outputs:
        - `system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_GAP_AUDIT__CURRENT__v1.json`
        - `system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_GAP_AUDIT__CURRENT__v1.md`
        - `system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_GAP_PACKET__CURRENT__v1.json`
    - current bridge truth from that slice:
      - `SKILL -> KERNEL_CONCEPT`: missing
      - `SKILL -> EXECUTION_BLOCK`: missing
      - `SKILL -> B_OUTCOME`: missing
      - `SKILL -> B_SURVIVOR`: missing
      - `SKILL -> SIM_EVIDENCED`: missing
      - `B_OUTCOME -> KERNEL_CONCEPT`: missing
      - `SIM_EVIDENCED -> KERNEL_CONCEPT`: missing
      - `B_SURVIVOR -> KERNEL_CONCEPT`: weak signal only
      - `B_OUTCOME -> EXECUTION_BLOCK`: present
      - `SIM_EVIDENCED -> B_SURVIVOR`: present
    - the first bounded bridge-source slice now also exists:
      - `control-graph-bridge-source-auditor`
      - current emitted outputs:
        - `system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_SOURCE_AUDIT__CURRENT__v1.json`
        - `system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_SOURCE_AUDIT__CURRENT__v1.md`
        - `system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_SOURCE_PACKET__CURRENT__v1.json`
    - current bridge-source truth from that slice:
      - `SKILL -> KERNEL_CONCEPT`: `heuristic_only`
      - `B_SURVIVOR -> KERNEL_CONCEPT`: `partial_property_trace`
      - `SIM_EVIDENCED -> KERNEL_CONCEPT`: `chain_partial`
      - `B_OUTCOME -> KERNEL_CONCEPT`: `not_derivable_now`
      - `EXECUTION_BLOCK -> KERNEL_CONCEPT`: `not_derivable_now`
    - the next honest graph-side follow-on is now:
      - `toponetx-projection-adapter-audit`
      - with survivor/source-chain limits carried forward and no auto-seeding of skill-to-kernel bridges from current skill metadata
    - the first bounded `TopoNetX` sidecar now also exists:
      - `toponetx-projection-adapter-audit`
      - current emitted outputs:
        - `system_v4/a2_state/audit_logs/TOPONETX_PROJECTION_ADAPTER_AUDIT__CURRENT__v1.json`
        - `system_v4/a2_state/audit_logs/TOPONETX_PROJECTION_ADAPTER_AUDIT__CURRENT__v1.md`
        - `system_v4/a2_state/audit_logs/TOPONETX_PROJECTION_ADAPTER_PACKET__CURRENT__v1.json`
    - current `TopoNetX` truth from that slice:
      - bounded probe remained kernel-only on `a2_low_control_graph_v1.json`
      - `244` admitted relation entries collapsed into `200` unique 1-cells
      - `OVERLAPS` remained quarantined with `614` preserved-only entries
      - `160` triangle motifs were observed, but `0` canonical 2-cells were emitted
      - the low-control topological sidecar is still fragmented: `300` components, `239` isolated nodes
    - immediate follow-on should now return to bridge strengthening / edge-policy work:
      - `survivor-kernel-bridge-backfill-audit`
      - `skill-kernel-link-seeding-policy-audit`
      - `clifford-edge-semantics-audit`
    - the first bounded survivor-kernel backfill slice now also exists:
      - `survivor-kernel-bridge-backfill-audit`
      - current emitted outputs:
        - `system_v4/a2_state/audit_logs/SURVIVOR_KERNEL_BRIDGE_BACKFILL_AUDIT__CURRENT__v1.json`
        - `system_v4/a2_state/audit_logs/SURVIVOR_KERNEL_BRIDGE_BACKFILL_AUDIT__CURRENT__v1.md`
        - `system_v4/a2_state/audit_logs/SURVIVOR_KERNEL_BRIDGE_BACKFILL_PACKET__CURRENT__v1.json`
    - current survivor backfill truth from that slice:
      - no new direct survivor-to-kernel backfill is currently admitted
      - `1` survivor is already directly linked to a live kernel concept
      - `46` survivors already resolve to live non-kernel concept classes (`34` extracted, `12` refined)
      - `31` survivors still have blank `source_concept_id`
    - the next honest bridge move is now:
      - `skill-kernel-link-seeding-policy-audit`
      - with direct survivor-kernel backfill kept fail-closed until concept-class normalization changes the witness-side substrate
    - the first bounded skill-kernel seeding policy slice now also exists:
      - `skill-kernel-link-seeding-policy-audit`
      - current emitted outputs:
        - `system_v4/a2_state/audit_logs/SKILL_KERNEL_LINK_SEEDING_POLICY_AUDIT__CURRENT__v1.json`
        - `system_v4/a2_state/audit_logs/SKILL_KERNEL_LINK_SEEDING_POLICY_AUDIT__CURRENT__v1.md`
        - `system_v4/a2_state/audit_logs/SKILL_KERNEL_LINK_SEEDING_POLICY_PACKET__CURRENT__v1.json`
    - current skill seeding truth from that slice:
      - no direct skill-to-kernel auto-seeding is currently admitted
      - `110` registry rows and `110` skill nodes still carry `0` owner-bound concept fields
      - current skill edge families remain only `RELATED_TO::SKILL` and `SKILL_FOLLOWS::SKILL`
      - source path, tags, descriptions, layers, related skills, and inferred skill-to-skill edges are all explicitly insufficient for kernel seeding
    - the next honest graph-side follow-on is now:
      - `clifford-edge-semantics-audit`
      - with run_real_ratchet dispatch/refactor debt held in watch-only mode rather than stealing the graph line
    - the first bounded `clifford` sidecar now also exists:
      - `clifford-edge-semantics-audit`
      - current emitted outputs:
        - `system_v4/a2_state/audit_logs/CLIFFORD_EDGE_SEMANTICS_AUDIT__CURRENT__v1.json`
        - `system_v4/a2_state/audit_logs/CLIFFORD_EDGE_SEMANTICS_AUDIT__CURRENT__v1.md`
        - `system_v4/a2_state/audit_logs/CLIFFORD_EDGE_SEMANTICS_PACKET__CURRENT__v1.json`
    - the first bounded edge-payload schema slice now also exists:
      - `edge-payload-schema-audit`
      - current emitted outputs:
        - `system_v4/a2_state/audit_logs/EDGE_PAYLOAD_SCHEMA_AUDIT__CURRENT__v1.json`
        - `system_v4/a2_state/audit_logs/EDGE_PAYLOAD_SCHEMA_AUDIT__CURRENT__v1.md`
        - `system_v4/a2_state/audit_logs/EDGE_PAYLOAD_SCHEMA_PACKET__CURRENT__v1.json`
    - current edge-semantics truth from those slices:
      - `clifford` is the primary GA sidecar and `kingdon` remains optional bridge tooling
      - deferred GA fields are explicit but still sidecar-only
      - admitted schema scope is limited to `DEPENDS_ON`, `EXCLUDES`, `STRUCTURALLY_RELATED`, and `RELATED_TO`
      - `OVERLAPS` and all skill-edge families remain outside admitted GA payload scope
    - the next bounded graph move is now also landed:
      - `edge-payload-schema-probe`
      - current probe relation is `STRUCTURALLY_RELATED`
      - current payload preview count is `3`
      - current next step is `hold_probe_as_sidecar_only`
    - keep that probe read-only and still separate from runtime mutation, training, or canonical graph replacement
    - current controller hold on the broader graph/control tranche:
      - `pyg-heterograph-projection-audit`
      - `control-graph-bridge-gap-auditor`
      - `control-graph-bridge-source-auditor`
      - `toponetx-projection-adapter-audit`
      - `survivor-kernel-bridge-backfill-audit`
      - `skill-kernel-link-seeding-policy-audit`
      - `clifford-edge-semantics-audit`
      - `edge-payload-schema-audit`
      - `edge-payload-schema-probe`
      - these slices are repo-held and emitted, but they remain intentionally outside the active admitted skill registry
      - until an explicit later controller decision, treat them as support-side sidecars only, not live graph/runtime expansion
6. Keep the next imported/corpus-derived slices honest:
  - `a2-tracked-work-operator` is now real as the bounded tracked-work slice
  - `a2-research-deliberation-operator` is now real as the bounded local research/deliberation slice
  - `lev-research` remains `adapt`, while `cdo` is only `mine` for now
7. Native maintenance cluster is now real and has six bounded slices:
  - `SKILL_CLUSTER::a2-skill-truth-maintenance`
  - landed first slice: `a2-brain-surface-refresher`
  - landed second slice: `a2-skill-improver-readiness-operator`
  - landed third slice: `a2-skill-improver-target-selector-operator`
  - landed fourth slice: `a2-skill-improver-dry-run-operator`
  - landed fifth slice: `a2-skill-improver-first-target-proof-operator`
  - landed sixth slice: `a2-skill-improver-second-target-admission-audit-operator`
  - current truth:
    - refresher report + packet are live, and the latest direct repo run is now `ok` with `0` lagging standing A2 surfaces
    - skill improver readiness report + packet are live, and the current verdict is `bounded_ready_for_first_target` with `do_not_promote` still in force for general mutation
    - skill improver target-selection report + packet are live, and the current selected first target is `a2-skill-improver-readiness-operator`
    - dry-run report + packet are live, and the current dry-run stays `ok` / `dry_run_only` / `do_not_promote`
    - first-target proof report + packet are live, and one bounded proof now succeeds with exact restore while the general mutation gate remains in force
    - second-target-admission report + packet are live, and the current verdict is `hold_one_proven_target_only` with `0` honest second-target candidates admitted
7. EverMem is now a bounded side-project lane:
  - `witness-memory-retriever`
  - current repo-held result is `attention_required` with bounded next step `hold_at_retrieval_probe`
  - `a2-evermem-backend-reachability-audit-operator`
  - current repo-held result is `attention_required` with bounded next step `start_docker_daemon`
  - do not let this lane drive the main-line build order
8. Current post-EverMem next-cluster ranking from the parallel audit lanes:
  - highest native maintenance priority:
    - `SKILL_CLUSTER::a2-skill-truth-maintenance`
    - landed slices:
      - `a2-brain-surface-refresher`
      - `a2-skill-improver-readiness-operator`
      - `a2-skill-improver-target-selector-operator`
      - `a2-skill-improver-dry-run-operator`
      - `a2-skill-improver-first-target-proof-operator`
      - `a2-skill-improver-second-target-admission-audit-operator`
    - current next step:
      - keep the standing A2 truth surfaces synced to the now-proven single admitted target class
      - hold at one proven target until a later slice produces an owner-grounded second-target class
  - landed imported continuation:
    - `SKILL_CLUSTER::workshop-analysis-gating`
    - first honest slice: `a2-workshop-analysis-gate-operator`
    - current repo-held outputs:
      - [A2_WORKSHOP_ANALYSIS_GATE_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_WORKSHOP_ANALYSIS_GATE_REPORT__CURRENT__v1.json)
      - [A2_WORKSHOP_ANALYSIS_GATE_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_WORKSHOP_ANALYSIS_GATE_REPORT__CURRENT__v1.md)
      - [A2_WORKSHOP_ANALYSIS_GATE_PACKET__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_WORKSHOP_ANALYSIS_GATE_PACKET__CURRENT__v1.json)
9. Current post-proof next tranche from the audit lanes:
  - the lev selector refresh is now landed:
    - `a2-lev-agents-promotion-operator` no longer recommends the already-landed builder/formalization lane
  - `SKILL_CLUSTER::lev-architecture-fitness-review` is now also landed:
    - first bounded slice: `a2-lev-architecture-fitness-operator`
    - status: audit-only / nonoperative / non-migratory / non-runtime-live
  - current lev selector state is:
    - `landed_lev_cluster_count = 7`
    - `parked_lev_cluster_count = 1`
    - `has_current_unopened_cluster = False`
  - do not infer a default next lev continuation
  - if imported work continues next, open a different bounded lane or admit a new lev candidate explicitly
  - landed Leviathan-derived continuity slice:
    - `SKILL_CLUSTER::outer-session-durability`
    - import label: `FlowMind Session Durability Bridge`
    - first honest slice: `outer-session-ledger`
    - current repo-held outputs:
      - [OUTER_SESSION_LEDGER_STATE__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/OUTER_SESSION_LEDGER_STATE__CURRENT__v1.json)
      - [OUTER_SESSION_LEDGER_EVENTS__APPEND_ONLY__v1.jsonl](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/OUTER_SESSION_LEDGER_EVENTS__APPEND_ONLY__v1.jsonl)
      - [OUTER_SESSION_LEDGER_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/OUTER_SESSION_LEDGER_REPORT__CURRENT__v1.json)
      - [OUTER_SESSION_LEDGER_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/OUTER_SESSION_LEDGER_REPORT__CURRENT__v1.md)
  - landed `pi-mono` slice:
    - `SKILL_CLUSTER::outside-control-shell-session-host`
    - first bounded slice: `outside-control-shell-operator`
    - current repo-held outputs:
      - [A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT__CURRENT__v1.json)
      - [A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT__CURRENT__v1.md)
      - [A2_PIMONO_OUTSIDE_SESSION_HOST_PACKET__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_PIMONO_OUTSIDE_SESSION_HOST_PACKET__CURRENT__v1.json)
    - bounded status: read-only / repo-held report + packet / no durable state
9. Keep appending every newly referenced repo or doc here and into canonical A2 indexing.
10. Turn source families into actual skill bundles and clusters, not just one-off notes.
11. Deepen runtime integration beyond discovery and graph presence.

## Append Here Next Time

When you reference a new repo, doc, framework, or skill family, append:

- name
- link or path
- why it matters
- target skill family or operator family
- current state: `saved`, `graphed`, `registry`, `runtime`, `partial`, or `broken`
