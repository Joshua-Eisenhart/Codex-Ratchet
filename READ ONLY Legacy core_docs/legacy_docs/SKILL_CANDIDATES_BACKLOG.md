# Skill Candidates Backlog

Last updated: 2026-03-21

## What This Is

This is the simple backlog of skills we can make from the repos, docs, and method bundles you keep referencing.

It is not a promise that every item is already implemented.
It is the place to keep the exploding list from getting lost.

This file is the simple front-door append backlog for candidate skills from those sources.
It is a `SOURCE_CORPUS` working surface, not canonical A2 brain memory by itself.

Detailed source and status tracking lives in:

- [SKILL_SOURCE_CORPUS.md](/home/ratchet/Desktop/Codex%20Ratchet/SKILL_SOURCE_CORPUS.md)
- [REPO_SKILL_INTEGRATION_TRACKER.md](/home/ratchet/Desktop/Codex%20Ratchet/REPO_SKILL_INTEGRATION_TRACKER.md)
- [79_INTEGRATION_LEDGER__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/specs/79_INTEGRATION_LEDGER__v1.md)
- [A2_V4_RECOVERY_AUDIT.md](/home/ratchet/Desktop/Codex%20Ratchet/A2_V4_RECOVERY_AUDIT.md)

## Buckets

- `real now`: already exists as a real repo skill file or raw registry record
- `runtime real now`: verified as live in the current runner path
- `partial now`: partly real, but not fully integrated
- `should build next`: concrete near-term candidates
- `big source family`: many possible future skills from one repo/doc family

## Runtime Real Now

- `z3-constraint-checker`

## Real Now

- `autoresearch-operator`
- `llm-council-operator`
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

## Partial Now

- `a2-skill-source-intake-operator`
  - file, spec, registry row, and dispatch binding now exist
  - current scope is a bounded A2 intake audit slice, not the full workshop-style import loop
- `a2-tracked-work-operator`
  - file, spec, registry row, and dispatch binding now exist
  - current scope is one bounded repo-held tracked-work note, not a general planning subsystem
- `a2-research-deliberation-operator`
  - file, spec, registry row, dispatch binding, and current report output now exist
  - current scope is a bounded local research/deliberation route, not the full lev-research or CDO stack
- `a2-workshop-analysis-gate-operator`
  - file, spec, registry row, dispatch binding, and current report/packet outputs now exist
  - current scope is one bounded workshop-analysis/gate slice, not the full lev workshop / align / work stack
- `a2-next-state-signal-adaptation-audit-operator`
  - file, spec, registry row, dispatch binding, and current report/packet outputs now exist
  - current scope is a bounded paper-derived next-state / directive-correction audit slice, not OpenClaw runtime or online RL import
- `autoresearch-operator`
  - file and runner hook exist, and registry loading is now repaired, but runtime use still needs a clean verification pass
- `llm-council-operator`
  - file and runner hook exist, and registry loading is now repaired, but runtime use still needs a clean verification pass
- `pimono-evermem-adapter`
  - file exists, but runtime integration depth is still partial
- `evermem-memory-backend-adapter`
  - file and raw registry row exist, but live runner use is not yet verified
- `witness-evermem-sync`
  - file, registry row, durable cursor/error/report handling, and live runner seam now exist
  - broader EverMem bootstrap and outside-control memory work are still partial
- `witness-memory-retriever`
  - file, spec, registry row, dispatch binding, and current report/packet outputs now exist
  - current bounded result is `attention_required` with `hold_at_retrieval_probe`; broader bootstrap / pi-mono memory claims remain separate
  - keep this lane side-project only for now
- `a2-evermem-backend-reachability-audit-operator`
  - file, spec, registry row, dispatch binding, and current report/packet outputs now exist
  - current bounded result is `attention_required` with `start_docker_daemon`; keep service-start/bootstrap claims out of the main line
- `intent-memory-loader`
  - implied by the intent/memory work, but not yet a named finished operator
- broader Retooled External Methods family
  - source is present, but method-by-method conversion is incomplete
- `lev-os` family imports
  - staged as source families, not yet deeply turned into system_v4 skill bundles
- broader A2 recovery / owner-law tooling
  - the append and boot docs now exist, and doc-index coverage is repaired, but the standing A2 brain content still needs refresh

## Should Build Next

### Tracking / Repair

- `a2-owner-law-indexer`
  - get the key owner specs and active A2 brain surfaces into the canonical A2 doc index
- `a2-brain-surface-refresher`
  - landed as the first audit-only slice of `SKILL_CLUSTER::a2-skill-truth-maintenance`
  - next work is to keep the maintenance loop converged as new current-truth slices land
- `a2-skill-improver-readiness-operator`
  - landed as the second audit-only slice of `SKILL_CLUSTER::a2-skill-truth-maintenance`
  - current verdict is `bounded_ready_for_first_target` for `skill-improver-operator`
  - `do_not_promote` still applies for general live mutation
- `a2-skill-improver-target-selector-operator`
  - landed as the third audit-only slice of `SKILL_CLUSTER::a2-skill-truth-maintenance`
  - current selected first target is `a2-skill-improver-readiness-operator`
  - next work is to prove that selected target under allowlist + approval-token control
- `a2-skill-improver-dry-run-operator`
  - landed as the fourth audit-only slice of `SKILL_CLUSTER::a2-skill-truth-maintenance`
  - current result is `ok`, `dry_run_only`, and still `do_not_promote`
- `a2-skill-improver-first-target-proof-operator`
  - landed as the fifth audit/proof slice of `SKILL_CLUSTER::a2-skill-truth-maintenance`
  - current result is one bounded successful proof with exact restore; general live mutation remains gated
- `a2-skill-improver-second-target-admission-audit-operator`
  - landed as the sixth audit-only slice of `SKILL_CLUSTER::a2-skill-truth-maintenance`
  - current result is `hold_one_proven_target_only`; no honest second target class is admitted yet
- refresh the standing A2 brain surfaces from the owner law and current repo reality
- `a2-tracked-work-operator`
  - landed as the first bounded tracked-work slice
  - tracked-work truth is now normalized so it reports itself as current, not as its own next slice
  - next work is to verify whether it should write to session logs as well as audit logs
- `a2-lev-architecture-fitness-operator`
  - landed as the next bounded lev-os/agents slice
  - keep it audit-only, non-migratory, and non-runtime-live
  - current lev selector state is `no_current_unopened_cluster`; admit any further lev slice only after explicit audit
- `a2-next-state-directive-signal-probe-operator`
  - landed as the second bounded slice of `SKILL_CLUSTER::next-state-signal-adaptation`
  - current result is `ok` after real post-action witness capture
  - current signal counts are `3` next-state candidates / `3` directive signals / `1` evaluative signal
  - next bounded bridge is now landed as `a2-next-state-improver-context-bridge-audit-operator`
  - keep it audit-only and do not widen it into live-learning or runtime-import claims
- `a2-next-state-improver-context-bridge-audit-operator`
  - landed as the third bounded slice of `SKILL_CLUSTER::next-state-signal-adaptation`
  - current result is `admissible_as_first_target_context_only`
  - next bounded consumer-admission slice is now landed as `a2-next-state-first-target-context-consumer-admission-audit-operator`
  - keep it audit-only, first-target-context-only, and explicitly separate from second-target admission, graph backfill, and live-learning claims
- `a2-next-state-first-target-context-consumer-admission-audit-operator`
  - landed as the fourth bounded slice of `SKILL_CLUSTER::next-state-signal-adaptation`
  - `skill-improver-operator` now exposes an explicit first-target context contract
  - current result is `candidate_first_target_context_consumer_admissible`
  - next bounded proof slice is now landed as `a2-next-state-first-target-context-consumer-proof-operator`
  - current next step is `hold_consumer_proof_as_metadata_only`
  - keep it audit-only and first-target-context-only; do not widen it into live-learning, runtime-import, second-target, or graph-backfill claims
- `a2-next-state-first-target-context-consumer-proof-operator`
  - landed as the fifth bounded slice of `SKILL_CLUSTER::next-state-signal-adaptation`
  - current result is `ok`
  - keep it metadata-only / dry-run / no-write; do not widen it into live-learning, runtime-import, second-target, or graph-backfill claims
- `a2-persistence-compat-auditor`
  - make the live `memory.jsonl` / `fuel_queue` / `rosetta` / `constraint_surface` contract explicit instead of silently mixed
- `skill-registry-loader-repair`
  - landed; keep as follow-up hardening and verification, not greenfield repair
- `skill-graph-refresh-audit`
  - refresh graph coverage against the current live registry after each new slice lands
- `local-source-repo-manifest-refresher`
  - keep remote URLs, commits, and presence tiers honest for downloaded source repos
- `pimono-evermem-adapter`
  - deepen runtime integration and prove actual use
- `retooled-external-methods-auditor`
  - verify each of the 29 methods against registry, source file, and runtime use

### Memory / Context

- `a2-context-spec-workflow-pattern-audit-operator`
  - now landed as the first bounded slice of `SKILL_CLUSTER::context-spec-workflow-memory`
  - follow-on selector slice is now landed as `a2-context-spec-workflow-follow-on-selector-operator`
  - append-safe continuity-shell follow-on is now landed as `a2-append-safe-context-shell-audit-operator`
- `a2-context-spec-workflow-follow-on-selector-operator`
  - now landed as the second bounded slice of `SKILL_CLUSTER::context-spec-workflow-memory`
  - selected pattern is `append_safe_context_shell`
  - keep this selector-only and do not widen into multiple pattern families at once
- `a2-append-safe-context-shell-audit-operator`
  - now landed as the third bounded slice of `SKILL_CLUSTER::context-spec-workflow-memory`
  - append-safe shell landing is now followed by `a2-context-spec-workflow-post-shell-selector-operator`
  - keep this slice audit-only; it does not authorize canonical brain replacement, multi-pattern widening, or memory-platform ownership
- `a2-context-spec-workflow-post-shell-selector-operator`
  - now landed as the fourth bounded slice of `SKILL_CLUSTER::context-spec-workflow-memory`
  - current next step is `hold_cluster_after_append_safe_shell`
  - first standby follow-on if explicitly reopened later is `a2-executable-spec-coupling-audit-operator`
  - keep this selector-only; do not widen the cluster by momentum
- `a2-autoresearch-council-runtime-proof-operator`
  - now landed as the first bounded slice of `SKILL_CLUSTER::karpathy-meta-research-runtime`
  - current result is `hold_first_slice_as_runtime_proof_only`
- `intent-memory-loader`
- `pi-mono-memory-bridge`
- `evermem-context-bootstrap`
- `outside-control-memory-shell`
- `leviathan-memory-support-adapter`

### Deliberation / Improvement

- `skill-improver-operator`
  - now audit-cleared for one bounded first target class in [SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json)
  - current selected first target is [a2-skill-improver-readiness-operator](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skill_specs/a2-skill-improver-readiness-operator/SKILL.md)
  - still not honest as a general live repo-mutating loop
- `repo-pattern-miner`
- `method-to-skill-converter`
- `multi-skill-council-router`
- `outside-claw-controller`

### Graph / Control Substrate

- `nested-graph-architecture-auditor`
- `constraint-surface-graph-operator`
- `graph-of-graphs-schema-operator`
- `axis0-constraint-graph-audit`
- `axis0-correlation-entropy-graph-probe`
- `hopf-tori-graph-shaper`
- `elastic-edge-semantics-audit`
- `tensor-edge-feasibility-audit`
- `witness-transition-failure-basin-bridge`
- `spec-graph-coupling-auditor`
- `bounded-graph-adapter-matrix-audit`
- `toponetx-projection-adapter-audit`
  - current first bounded TopoNetX contract now exists in code and emitted report form
- `pyg-heterograph-projection-audit`
  - current first bounded contract now exists in code and emitted report form
- `control-graph-bridge-gap-auditor`
  - current first bounded bridge-gap contract now exists in code and emitted report form
- `control-graph-bridge-source-auditor`
  - current first bounded bridge-source contract now exists in code and emitted report form
- `survivor-kernel-bridge-backfill-audit`
  - current first bounded survivor backfill contract now exists in code and emitted report form
- `skill-kernel-link-seeding-policy-audit`
  - current first bounded skill-kernel seeding-policy contract now exists in code and emitted report form
- `clifford-edge-semantics-audit`
  - current first bounded clifford sidecar contract now exists in code and emitted report form
- `edge-payload-schema-audit`
  - current first bounded edge-payload schema contract now exists in code and emitted report form
- `edge-payload-schema-probe`
  - current first bounded payload-preview probe now exists in code and emitted report form
  - current relation is `STRUCTURALLY_RELATED`
  - current result is `ok`
  - current next step is `hold_probe_as_sidecar_only`
  - the current graph/control tranche remains intentionally unadmitted to the live skill registry; treat these as repo-held sidecars until an explicit later controller decision

### Retooled External Methods Conversion Candidates

These are examples of named skills that could come out of the Retooled External Methods family:

- `bayesian-update-operator`
- `markov-transition-operator`
- `information-geometry-operator`
- `trace-compression-operator`
- `program-synthesis-operator`
- `motif-library-learner`
- `evolutionary-search-operator`
- `constrained-decoding-operator`
- `graph-topology-miner`
- `negative-simulation-operator`
- `witness-basin-mapper`

## Big Source Families

### lev-os/agents

This is not one skill. It is a huge source family.

Possible bundles:

- workshop intake skills
- source-family mining skills
- skill-source corpus append skills
- workshop lifecycle skills
- skill-builder skills
- alignment / gate skills
- repo-to-skill intake skills
- agent packaging skills
- companion-skill bundle skills

Immediate imported cluster candidates:

- `skill-source intake cluster`
  - first Ratchet-native slice now exists as `a2-skill-source-intake-operator`
- `tracked work / planning cluster`
  - first bounded slice now exists: `a2-tracked-work-operator`
- `research / deliberation cluster`
  - first bounded slice now exists: `a2-research-deliberation-operator`

### lev-os/leviathan

Possible bundles:

- prompt-stack host adapters
- flowmind wrapper adapters
- outside control-shell adapters
- append-log and memory-support adapters
- workshop-to-ratchet intake skills
- star-skill packaging
- node capability inheritance
- workshop-to-production promotion
- JP-vision-derived runtime shaping

Current bounded continuity slice:

- `outer-session-ledger`
  - first bounded Leviathan-derived slice now exists
  - keep it to session id, cursor, receipts, resume support, and repo-held continuity outputs only

### Context / spec / workflow / memory repos

This is not one skill. It is a source family for making the system more append-safe,
spec-coupled, and continuity-aware.

Current repo probes:

- `Context-Engineering`
- `spec-kit`
- `superpowers`
- `mem0`

Possible bundles:

- append-safe context schema skills
- thread continuity / context compaction skills
- live spec coupling / spec drift audit skills
- protocol-shell / intent-capture skills
- subagent workflow / review discipline skills
- low-bloat memory consolidation skills
- scoped memory admission / mutation-history skills
- export/import / continuity receipt skills
- graph-backed memory overlay skills

### pi-mono

Current bounded pi-mono slice:

- `outside-control-shell-operator`
  - first bounded `pi-mono` outside-control-shell/session-host slice now exists
  - keep follow-on work separate from this landed report + packet operator

Possible bundles:

- resource-loader host skills
- plan-mode controller skills
- isolated subagent chain skills
- lane-memory split skills
- outside claw controller skills
- controller console / operator shell skills
- agent context skills
- AI package bridge skills
- coding-agent bridge skills
- TUI / web-ui bridge skills
- memory backend adaptors

### Karpathy minimal-core family

Possible bundles:

- minimal runtime-core skills
- tokenizer / compression boundary skills
- council / deliberation skills
- research / mutation loop skills
- chat-shell / controller-shell skills

Primary repos:

- `autoresearch`
- `llm-council`
- `nanochat`
- `nanoGPT`
- `llm.c`
- `minbpe`

### EverMem / EverMind / MSA

Possible bundles:

- external memory adaptors
- witness sync operators
- context restore operators
- episodic retrieval operators
- semantic memory bridge skills
- long-context backend audit skills
- outside control-memory backend skills

Current rule:

- useful side project, not the current main-line build focus

### OpenClaw-RL / next-state signals

Current bounded slice:

- `a2-next-state-signal-adaptation-audit-operator`
  - first bounded paper-derived next-state / directive-correction slice now exists
  - keep follow-on work separate from this landed audit/report/packet operator

Possible bundles:

- next-state signal classification
- directive-correction probe skills
- hindsight-hint extraction audits
- async-improvement architecture audits
- witness-to-improvement bridge skills

### Retooled External Methods

Possible bundles:

- retooled external method operators
- runtime kernel / geometry operators
- probe / witness / regulation operators
- deliberation / bounded-improve operators
- verification / admissibility operators
- search / synthesis / library-growth operators
- runtime interface / guardrail / graph-projection operators
- runtime geometry operators
- probe / witness operators
- search / abstraction / synthesis operators
- topology mining and transform operators

### AlphaGeometry / AutoResearchClaw / DreamCoder

Possible bundles:

- geometry theorem-search operators
- research-claw controller skills
- abstraction learning and library-growth operators
- synthesis and concept-invention operators

### Local Leviathan / Holodeck / Bootpack docs

Possible bundles:

- workshop memory and world-model skills
- external handoff / bootpack intake skills
- local Leviathan source-mining skills
- rosetta / translation / external-model bridge skills

## Working Rule

Do not wait for perfect naming.

If a possible skill family is referenced, add it here in the simplest good-enough words.
Then we can refine names later.

What matters is that it stops disappearing.
