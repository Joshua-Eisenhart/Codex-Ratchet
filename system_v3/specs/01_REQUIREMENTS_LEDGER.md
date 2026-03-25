# Requirements Ledger
Status: DRAFT / NONCANON
Date: 2026-02-20

## Root Constraints
- `RQ-001` MUST: `F01_FINITUDE` is non-negotiable.
- `RQ-002` MUST: `N01_NONCOMMUTATION` is non-negotiable.
- `RQ-003` MUST: canon admission authority is B only.
- `RQ-004` MUST: survivor order is semantically meaningful.

## Thread Boundaries
- `RQ-010` MUST: A2 is high-entropy mining/design/debug layer.
- `RQ-011` MUST: A1 is nondeterministic Rosetta+planning layer with explicit wiggle.
- `RQ-012` MUST: A0 is deterministic compiler/dispatcher that also validates B full-state snapshots.
- `RQ-013` MUST: B is deterministic adjudicator.
- `RQ-014` MUST: SIM is deterministic evidence executor.

## B Kernel Requirements
- `RQ-020` MUST: B accepts only declared container types.
- `RQ-021` MUST: schema/grammar checks run before semantic checks.
- `RQ-022` MUST: undefined-term fence is enforced.
- `RQ-023` MUST: derived-only fence is enforced.
- `RQ-024` MUST: lexeme/compound component fence is enforced.
- `RQ-025` MUST: formula glyph guards are enforced.
- `RQ-026` MUST: probe-pressure policy is enforced.
- `RQ-027` MUST: outcomes are only ACCEPT/PARK/REJECT.
- `RQ-028` MUST: every REJECT writes replayable graveyard record.
- `RQ-029` MUST: deterministic stage order is fixed and cannot be reordered.

## A0 Compiler Requirements
- `RQ-030` MUST: A0 canonicalizes A1 strategy to stable JSON + hash.
- `RQ-031` MUST: A0 emits only B-grammar artifacts, no prose.
- `RQ-032` MUST: deterministic ordering of candidate compilation.
- `RQ-033` MUST: dependency ordering is explicit; forward refs parkable.
- `RQ-034` MUST: budget ceilings are enforced deterministically.
- `RQ-035` MUST: outbox/log sharding is append-only.
- `RQ-036` MUST: overflow truncation uses deterministic tie-break ordering.
- `RQ-037` MUST: compile report includes dependency DAG + unresolved edges.
- `RQ-038` MUST: compile preflight validates strategy schema, sim references, and forbidden-token policy.
- `RQ-039` MUST: artifact naming and sequence numbers are monotonic within run scope.

## A1 Strategy Requirements
- `RQ-040` MUST: A1 produces `A1_STRATEGY_v1` only.
- `RQ-041` MUST: strategy includes Rosetta mappings, targets, alternatives, and evidence plan.
- `RQ-042` MUST: A1 supports branch exploration and mutation operators.
- `RQ-043` MUST: A1 uses B rejection reasons to repair next proposals.
- `RQ-044` MUST: A1 never writes canon state directly.
- `RQ-045` MUST: A1 can propose runtime/spec fixes as explicit patch intents.
- `RQ-046` MUST: A1 uses an explicit branch scheduler with per-operator quotas.
- `RQ-047` MUST: A1 enforces novelty floor to suppress near-duplicate branch spam.
- `RQ-048` MUST: A1 tracks branch lifecycle (active, parked, retired, resurrectable).
- `RQ-049` MUST: fix-intent proposals include target layer, evidence, risk, and rollback shape.
- `RQ-097` MUST: anti-classical leakage is treated as drift (no conservative “proof thinking” proposals that bypass ratcheting).
- `RQ-098` MUST: batches are non-conservative by default; convergence is via massive exploration under `F01_FINITUDE` and `N01_NONCOMMUTATION`.

## SIM + Evidence Requirements
- `RQ-050` MUST: meaningful survivor requires positive evidence.
- `RQ-051` MUST: meaningful survivor requires negative evidence.
- `RQ-052` MUST: meaningful survivor requires plausible failed alternatives in graveyard.
- `RQ-053` MUST: negative sim is target-coupled + failure-mode-coupled.
- `RQ-054` MUST: sim evidence is deterministic and replayable.
- `RQ-055` MUST: tiered sim architecture (`T0..T6`) is used.
- `RQ-056` MUST: stress families are required (`BASELINE`, `BOUNDARY_SWEEP`, `PERTURBATION`, `ADVERSARIAL_NEG`, `COMPOSITION_STRESS`).
- `RQ-057` MUST: whole-system master sim is gated, not bypassed.
- `RQ-058` MUST: each tier has minimum stress-suite coverage thresholds.
- `RQ-059` MUST: promotion reports include per-gate deficit counts and blockers.

## Graveyard Requirements
- `RQ-060` MUST: graveyard is structural exploration memory, not filler.
- `RQ-061` MUST: graveyard entries tie to concrete target/alternative IDs.
- `RQ-062` MUST: graveyard stores failure reason + raw artifact lines.
- `RQ-063` MUST: B-kills and SIM-kills are both tracked.
- `RQ-064` MUST: meaningful survivors carry explicit links to negative-sim ids and alternative graveyard ids.

## A2 Operations Requirements
- `RQ-070` MUST: A2 is the mining layer and maintains persistent memory and context seals.
- `RQ-071` MUST: A2 tracks contradictions and unresolved risks.
- `RQ-072` MUST: A2 performs system-level debug/upgrade planning.
- `RQ-073` MUST: A2 controls doc sprawl via fixed file interfaces + sharding.
- `RQ-074` MUST: A2 upgrades are additive and reversible.
- `RQ-075` MUST: A2 maintains explicit thread-seal cadence and pending-action queue.
- `RQ-076` MUST: every spec upgrade set includes a machine-readable delta manifest.
- `RQ-077` MUST: each task declares active model and reason at execution start.
- `RQ-078` MUST: legacy docs remain read-only; promotion uses versioned paths only.
- `RQ-145` MUST: fresh `A2_CONTROLLER` relaunches use one explicit launch packet declaring model, thread class, mode, primary corpus, state record, go-on count, go-on budget, stop rule, dispatch rule, and initial bounded scope.
- `RQ-146` MUST: fresh `A2_CONTROLLER` relaunches recover weighted current truth from one small controller state record rather than inferring launch priority from mixed execution history alone.
- `RQ-147` MUST: `A2_CONTROLLER` substantive processing is dispatch-first; if a bounded worker packet can express the work, the controller must dispatch rather than absorb worker/refinery behavior itself.

## A1 Wiggle Execution Requirements
- `RQ-100` MUST: A1 branch exploration uses explicit operator quotas and deterministic quota accounting.
- `RQ-101` MUST: A1 branch records include prompt lineage, operator lineage, and rejection/evidence references.
- `RQ-102` MUST: A1 branch scoring separates novelty score from viability score and logs both deterministically.
- `RQ-103` MUST: A1 emits at least one graveyard-targeted alternative per primary target cluster.
- `RQ-104` MUST: A1 repair loop consumes exact B tags and sim failure classes, not natural-language summaries.
- `RQ-105` MUST: A1 candidate objects are compile-ready (`item_class`, `id`, `kind`, `requires`, `def_fields`, `asserts`) before A0 ingestion.
- `RQ-106` MUST: A1 keeps kernel-lane fields free of free-English payloads; explanatory text stays overlay-lane only.
- `RQ-107` MUST: A1 stall detection triggers deterministic quota rebalancing before branch retirement.
- `RQ-108` MUST: A1 strategy packets include explicit expected failure modes for alternatives and negative sims.

## A2 Persistent Brain Requirements
- `RQ-109` MUST: A2 canonical memory schema versions are declared and checked before writes.
- `RQ-110` MUST: A2 seal operations write deterministic `SEAL_RECORD` entries with source hashes and pending actions.
- `RQ-111` MUST: A2 compaction from high entropy to low entropy is append-only and trace-linked to source memory entries.
- `RQ-112` MUST: A2 fuel queue entries carry source provenance, dependency hints, and invalidation status.
- `RQ-113` MUST: A2 rosetta mappings are overlay-only and can be disabled without changing canonical kernel state.
- `RQ-114` MUST: A2 contradiction registry tracks unresolved/waived/resolved states with evidence pointers.
- `RQ-115` MUST: A2 doc index refresh is deterministic and path-sorted with stable hash fields.
- `RQ-116` MUST: A2 state sharding policy is explicit (size/line ceilings, shard suffix rules, merge rules).

## Controlled Tuning and Upgrade Requirements
- `RQ-117` MUST: A0/B/SIM tuning runs are proposal-bound (`TUNING_PROPOSAL`) and never mutate authoritative specs in-place.
- `RQ-118` MUST: every tuning change set defines objective metric, stop condition, and rollback target before execution.
- `RQ-119` MUST: tuning experiments log baseline hash, candidate hash, and delta report in deterministic JSON.
- `RQ-120` MUST: any tuning change that alters admission outcomes requires conformance replay against fixed fixture suites.
- `RQ-121` MUST: tuning proposals are classified as `SAFE_PARAM`, `RULE_INTERPRETATION`, or `SEMANTIC_CHANGE`.
- `RQ-122` MUST: only `SAFE_PARAM` proposals may auto-apply; other classes require explicit review gate pass.
- `RQ-123` MUST: failed tuning branches are preserved in a tuning graveyard with failure evidence and revert recipe.
- `RQ-124` MUST: production promotion requires two identical deterministic replays on the selected candidate.

## Running-System Build Sequence Requirements
- `RQ-125` MUST: implementation proceeds through ordered phases with explicit phase entry/exit criteria.
- `RQ-126` MUST: B implementation cannot advance past Phase 2 unless bootpack conformance fixtures are green.
- `RQ-127` MUST: A1->A0->B integration must pass deterministic 50-cycle smoke replay before sim scale-out.
- `RQ-128` MUST: SIM integration requires evidence-ingest pass criteria before enabling promotion gates.
- `RQ-129` MUST: meaningful survivor gate requires positive sim, negative sim, and graveyard alternatives linked by IDs.
- `RQ-130` MUST: long-run execution enforces bounded write surfaces and deterministic sharding policies.
- `RQ-131` MUST: release candidate is valid only if two full end-to-end replays produce identical state and event-log hashes.
- `RQ-132` MUST: release candidate must include a frozen checklist artifact referencing all mandatory gate outputs.

## Run Surface Template Requirements
- `RQ-133` MUST: run surface scaffolding is deterministic from `(run_id, baseline_state_hash, strategy_hash)` and emits the same file tree for identical inputs.
- `RQ-134` MUST: scaffolder emits required phase/gate report templates before execution begins.
- `RQ-135` MUST: scaffolder emits tape/log placeholders with deterministic shard naming.
- `RQ-136` MUST: run manifest includes immutable source hashes for active spec set and bootpack references used by the run.
- `RQ-137` MUST: run initialization fails closed if target run directory already exists and is non-empty.
- `RQ-138` MUST: template updates are versioned; no in-place mutation of prior template versions.

## Bootpack Conformance Fixture Requirements
- `RQ-139` MUST: conformance suite defines fixture IDs with fixed expected outcomes (`PASS|PARK|REJECT`) and fixed expected tags.
- `RQ-140` MUST: each fixture declares its targeted rule family and minimal reproducible artifact payload.
- `RQ-141` MUST: conformance replay output includes per-fixture status, observed tags, and mismatch diagnostics.
- `RQ-142` MUST: fixture updates are versioned and never mutate historical expected outcomes in place.
- `RQ-143` MUST: semantic tuning proposals cannot promote unless conformance suite passes 100% on frozen fixture version.
- `RQ-144` MUST: conformance reports include bootpack hash and fixture-pack hash used for execution.

## Governance Requirements
- `RQ-080` MUST: no normative duplication across owner docs.
- `RQ-081` MUST: unknowns are recorded as `UNKNOWN`, never guessed.
- `RQ-082` MUST: no policy bypass of root constraints.
- `RQ-083` MUST: no fake evidence or fake graveyard padding.
- `RQ-084` MUST: conformance gates run before long runs.
- `RQ-085` MUST: machine lint verifies owner collisions and orphan requirements.
- `RQ-086` MUST: normative clause hash baseline is recorded for drift detection.
- `RQ-087` MUST: spec-pack promotion requires unresolved-risk list and audit report.
- `RQ-088` MUST: authority coverage audit runs against Megaboot + upgrade docs and produces a gap report.

## ZIP + Save + Tape Requirements
- `RQ-090` MUST: inter-thread communication uses `ZIP_JOB` bundles as atomic deterministic carriers.
- `RQ-091` MUST: ZIPs never split; documents inside ZIPs may shard.
- `RQ-092` MUST: text limits are enforced and sharding is deterministic (`MAX_TEXT_FILE_BYTES=65536`, `MAX_TEXT_FILE_LINES=2000`, ASCII-only, LF-only, shard suffix `_0001`...).
- `RQ-093` MUST: save levels `MIN`, `FULL+`, `FULL++` are explicitly defined and used as the persistence contract.
- `RQ-094` MUST: `CAMPAIGN_TAPE v1` is mandatory and append-only; records `(EXPORT_BLOCK + THREAD_B_REPORT)` pairs in canonical order.
- `RQ-095` MUST: `EXPORT_TAPE v1` is pre-run ordered `EXPORT_BLOCK` list; can be promoted into `CAMPAIGN_TAPE v1` post-run.
- `RQ-096` MUST: when graveyard is non-empty, A0 targets `>= 50%` graveyard-rescue share in batches (by count), subject to caps.

## Current Repair-Target Companions
- staged SIM campaign/process recovery target:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/72_SIM_CAMPAIGN_AND_SUITE_MODES__v1.md`
- semantic `FULL+` restore-bundle recovery target:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/73_FULL_PLUS_SEMANTIC_SAVE_ZIP__v1.md`
- A0 save/report tooling recovery target:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/74_A0_SAVE_REPORT_SURFACES__v1.md`
- A2 mining/Rosetta artifact-pack recovery target:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/75_A2_MINING_AND_ROSETTA_ARTIFACT_PACKS__v1.md`
