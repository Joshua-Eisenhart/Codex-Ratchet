# ClaimGate / Core Lev OS v45 — Wizard v4.3 Topology State Model + Real Lev Self-Run

This complete max-500 package keeps the Lev steering-run adapter boundary, adds a load-bearing signed source-manifest gate, mines local Lev source material into proposal-only Axiom -> Constraint -> Gate reports, can record a local host-consumption receipt when a host checkout consumes a ClaimGate steering run, issues plus consumes MassRun connector source packs before hard-gate promotion, marks core gate receipts with `gate_strength` plus MassRun source-pack receipts with key-custody/protection fields, fails closed if a legacy caller tries to enable self-attested promotion, records malformed evidence-manifest JSON as explicit hard-gate evidence, and proves one owner-approved mined gate proposal can move through four typed, hash-bound artifacts: `MinedGateProposal`, `OwnerGateApproval`, `HostGateConsumptionRequest`, and `HostGateAdmissionReceipt`. v45 also repairs the Wizard claim ceiling to a v4.3 route-topology state model and adds a real-input long-horizon projection from mined Lev source. The 0xRicker and oh-my-openagent material remains adapter/pattern input unless a current run produces local receipts for the stronger claim.

The deterministic long-horizon harness core provides explicit project-state normalization, attractor basin maps, move classification (`basin_deepening`, `basin_leakage`, `basin_split`, `basin_kill`, `insufficient_evidence`), missing-concept ledgers, ColdStartPackets, memory operator preconditions, and hybrid memory reranking. This layer is projection-only. It helps a model stay in the project basin; it does not admit, enforce, or promote.

It includes Project Island conventions, OracleLoop, GrowthGate oracle demos, branch ledger helpers, source-grounded docs, a Lev source miner, an adapter projection into `.lev/steering/runs/<run-id>` `EvalJobOutput` / `ProofSpec` shape, and spend-guarded worker routing. Mass workers default to Claude Bridge Sonnet plus Codex native. Direct Claude Bridge routes support Sonnet, Sonnet-high, and Opus when explicitly selected. OpenRouter is for sparse Chinese counterintelligence only when explicitly enabled: one bounded call per named route per prompt/input-output surface. OpenRouter Opus/GPT routes are forbidden, and Fusion is not the normal Chinese counterintel path because it can hide non-Chinese/Opus-class routing.

Read first: `docs/00_RESEARCH_RATCHET_LONG_HORIZON_PROJECT_HARNESS.md`,
`ALT_VIEWS_USED.md`, `docs/100_JP_CORE_EVAL_ALIGNMENT.md`,
`docs/101_PROJECT_ISLAND_CONVENTIONS.md`, and
`docs/104_CURRENT_LEV_SURFACE_AUDIT.md`.

Current local Lev audit: the checked hard root is `core/flowmind/src/kernel/constraint-manifold.ts`; gate evaluation lives at `core/flowmind/src/gate-evaluator.ts`; concrete eval/effect/receipt/proof target types live under `core/orchestration/src/eval`, `core/orchestration/src/effect`, `core/orchestration/src/receipt`, and `core/orchestration/src/proof`. `core/eval` wording in this package is compatibility/product-direction shorthand unless a host Lev checkout exposes that runtime.

Lev boundary from the current system map: the host eval/proof path is the proof brain, FlowMind is the authoring plane, and effect/receipt surfaces carry reality and terminal evidence. ClaimGate can propose, bind, hash, sign, and locally gate artifacts, but no semantic proof counts as closed until an observed effect has evidence refs and a host eval/policy decision consumes it. LLMs and councils can witness or propose; code companions and gates decide.

The old `.lev/runs/eval/<run-id>/proof.yaml` output is compatibility/demo
projection. The current runtime patch target is
`.lev/steering/runs/<run-id>/eval-job-output.json` plus `proof-spec.json`, and
adapter projections stay marked `live_lev_consumed:false`. If a host checkout
consumes a projection, the evidence is attached beside it as
`.cdo/lev-host-consumption/summary.json` with claim ceiling
`host_consumed_local_lev_checkout`.

---

# ClaimGate Complete System

This ZIP is intended to be the **complete working product branch**, not a delta pack.

It includes:

- CLI and deterministic gate engine
- GitHub App scaffold
- GitHub Action example
- Web UI dashboard
- WorkCard bounded-task module
- GateDigger / Axiom Digger policy proposal module
- Object Binding gate
- core/eval-compatible blind evaluator layer
- current Lev `EvalJobOutput` / `.lev/steering/runs` adapter projection
- Lev source miner for DNA/gates/validation/SDLC/vision material
- Local Lev host-consumption receipt runner
- ScenarioFan parallel explorer
- Hard-wall loop controller
- Wizard v4.3 object-preservation adapter
- Model-agnostic TeamHarness / durable council directory
- Volatile external-model receipt gate
- Oracle evidence-manifest gate
- Signed Manifest Gate for connector-bound source refs
- Evidence honesty detector
- Self-run harness for running ClaimGate against its own demo loop
- Live 3x3x3 swarm runner with provider-diverse typed member receipts
- MassRun runtime with signed fixture refs and external connector source-pack refs
- `claimgate source-pack issue` for reusable source-pack issuance
- Core `gate_strength` on gate results and receipts: `permissive`, `source_bound`, `signed_source_bound`, `caveated`, or `blocked`
- Custody-aware MassRun source-pack ceilings: fixture-key packs say `mass_run_proven_with_external_connector_fixture_key_manifest_refs`
- `self_attestation_policy` gate: `allowSelfAttested` is disabled and fails closed with `ALLOW_SELF_ATTESTED_DISABLED`
- Evidence-manifest parse errors are recorded in `evidence_manifest.details.parse_errors` and fail closed
- Research Ratchet v40: typed mined proposal -> scoped owner approval -> host consumption request -> independent host admission receipt, with probe-only fixture demos by default and optional owner/host ECDSA trust-root enforcement plus replay ledger
- Long-horizon harness core: attractor basin maps, move classification, missing-concept ledger, ColdStartPacket reconstruction, memory operator precondition checks, and hybrid rerank projection
- Real Lev long-horizon projection: mined Lev source plus local Lev host-consumption summary -> project state, attractor basin, ColdStartPacket, missing concepts, and preliminary spinor-memory operator receipts
- Mined axiom/constraint/gate output remains proposal-only until owner approval plus host receipt exists
- Unified full product run receipt
- Source-integration audit for Wizard/OpenAgent/X/video claim boundaries
- Manifest-driven zip packager
- Overall build/run receipt harness
- Standalone product boundary scanner
- GitHub Action required-check runner
- Core Lev OS plugin-first product docs
- Marketing Scientist plugin/demo
- Marketing Harness planner/verifier for creative variants and metric envelopes
- Rework Compiler
- ReceiptVault / Graveyard / Experience Compiler pieces
- Schemas, policy packs, examples, tests, and docs

## Start here

```bash
npm run doctor
npm run overall:build
npm run live-swarm:run
npm run product:run
npm run manifest-gate:demo
npm run mass-run:source-pack-demo
node packages/claimgate-cli/bin/claimgate.js source-pack issue --workcards examples/mass_run/wc-alpha/workcard.json,examples/mass_run/wc-beta/workcard.json,examples/mass_run/wc-gamma/workcard.json --out .cdo/source-packs/mass-run-demo
npm run source:integration:audit
npm run lev:mine:demo
npm run research-ratchet:demo
npm run long-horizon:demo
npm run lev-host:consume
npm run demo:block
node packages/claimgate-cli/bin/claimgate.js lev-adapter project-run --run .cdo/runs/demo_block --out .cdo/eval/demo_block --steering-out .lev/steering/runs/demo_block
npm run team:demo
npm run self:run
npm run action:mock
npm run marketing:demo
npm run demo:all
npm test
npm run standalone:check
npm run ui
```

Open:

```text
http://localhost:4317
```

## Core principle

```text
Soft side:
  LLMs, councils, ScenarioFan branches, GateDigger proposals, blind witnesses.
  They may explore, score, and propose.
  They cannot promote.

Hard side:
  Object binding, source-bound checks, evidence refs, hashes, reruns, receipts.
  Deterministic gates decide what counts.

Self-attestation:
  There is no permissive self-attestation bypass. A legacy caller that requests
  `allowSelfAttested` is blocked by `self_attestation_policy`.

Gate strength:
  A passing verdict is not all the same. Receipts now label whether the pass is
  permissive, source-bound, signed-source-bound, caveated, or blocked.

Signed source refs:
  A promoted source_ref must resolve through a signed connector-produced
  manifest entry. Local paths, expired entries, untrusted keys, and payload hash
  mismatches fail closed.

Evidence manifests:
  Malformed manifest JSON is not ignored. Parse failures are written to
  `parse_errors` and block the evidence-manifest gate.

Research Ratchet v40:
  Mined gates stay proposal-only. Owner approval records the selected proposal
  hash, target, and scope. Host consumption then emits a separate request and
  independent receipt that reference the proposal hash, approval hash, and
  request hash at the point downstream consumers read.
  Without owner approval plus host receipt, no mined gate is admitted or
  enforced. Probe-only approvals may admit an observation but cannot escalate
  into enforcement. Orphan receipts, replayed approvals, hash mismatches, and
  non-authoritative LLM/digger promotion claims fail closed. When an owner or
  host trust root is supplied, fixture signatures fail closed and only trusted
  ECDSA P-256 signatures admit. The replay ledger blocks reused approvals
  without relying on caller-threaded state. This is a local host-consumption
  proof, not complete Leviathan integration, public core/eval admission, or
  autonomous mined-gate enforcement.

MassRun source packs:
  WorkRun truth can be supplied by an external connector pack. MassRun verifies
  every ref first, copies verified payloads into authority workcards, and runs
  the hard gate against those verified workcards.
  The bundled issuer uses fixture key custody and says so at the receipt point;
  production connectors should issue the same shape with external key custody or
  HSM signing.

Exit condition:
  Stop only when the hard gate is clean, or budget is exhausted.
  Never stop because councils agreed.
```

## Core Lev OS direction

ClaimGate is the first hard-wall product surface. Core Lev OS is the larger
plugin-first operating loop:

```text
capture -> classify -> owner -> next action -> execute -> evidence -> gate -> receipt -> memory
```

The first manifestation domain is SDLC because repos, diffs, checks, and CI
artifacts are easy to gate. The sleeper expansion domain is marketing/creative
work: ideas and content become bounded experiments, then source-bound telemetry
from GA4, Meta Ads, YouTube, CRM, Stripe, email, or local fixtures decides what
the claim earned.

The included `marketing-scientist` plugin is deliberately an experiment gate,
not a copy generator. It can mark a campaign asset as ready to launch, but it
cannot claim performance lift until a delayed telemetry gate matures.

The included `claimgate-marketing` harness turns a campaign brief into variants
and then verifies a metrics envelope against named gates: source oracle, publish
and measure, truthful claim language, and owner/next action. This is the first
standalone creative/business harness inside the product boundary.

## Model pool boundary

Model availability is treated as volatile. A model that works in one run may be
blocked, renamed, downgraded, auth-gated, or malformed in the next run. Valid
overall runs still require multiple accepted model observations; the flexible
part is which provider/model seats satisfy the pool on that run.

External model output is accepted only as proposal/advisory signal when the
receipt validates as strict structured JSON with provider/model/status metadata,
`support_level` of `proposed` or `advisory`, and `promotion_allowed:false`.
Loose text, truncated output, missing provider metadata, or unparsable stdout is
blocked rather than promoted into route truth.

Default live-pool refreshes use the direct mass-worker lanes only:

```text
claude-bridge/claude-sonnet-4-6
codex-native
```

OpenRouter is reserved for sparse counter-intelligence and variation, and it
requires explicit opt-in with `CLAIMGATE_ALLOW_OPENROUTER=1` or the
`model-pool:counterintel-openrouter` / `product:run:counterintel-openrouter`
scripts. The normal OpenRouter counterintel script calls the named Chinese
frontier routes, one bounded call per route:

```text
deepseek/deepseek-v4-pro
qwen/qwen3.7-max
moonshotai/kimi-k2.7-code
z-ai/glm-5.2
minimax/minimax-m3
```

OpenRouter Fusion remains cataloged but requires separate opt-in because it can
hide non-Chinese/Opus-class routing.
DeepSeek Flash, Qwen Plus, and Gemini Flash can be fallback/override lanes, but
they are not primary proof seats for stronger current-model claims. OpenRouter
Claude Opus and OpenRouter GPT routes are forbidden in this product path. Direct
Claude Bridge Opus and Sonnet-high are allowed when explicitly selected; the ban
is on spending OpenRouter credits for those model families.

Default overall validity requires at least 3 accepted observations, at least 3
distinct providers, and at least 3 distinct models. The provider names are not
pinned, but same-provider temperature jitter is rejected as provider monoculture,
and same-model collapse is rejected as model monoculture.

## TeamHarness boundary

TeamHarness turns Wizard-style nested councils into durable, provider-neutral
team directories: `team.json`, member prompts, status files, artifacts,
observations, collapse audit, and typed failure signals. Any model provider can
run a member prompt if it returns the expected JSON. `live-swarm:run` attempts
the full 3x3x3 topology across the current provider fleet, records failed or
malformed seats literally, and requires provider/model diversity before the
swarm counts. The harness is still soft: it can propose and tighten only. It
never promotes.

## Most important demos

```bash
npm run demo:block        # PR blocked: open risk + overclaim
npm run demo:pass         # PR admitted
npm run axiom:demo        # GateDigger proposes project gates
npm run scenario:fan-demo # parallel adversarial branches
npm run eval:demo         # core/eval-compatible blind judge
npm run demo:block && node packages/claimgate-cli/bin/claimgate.js lev-adapter project-run --run .cdo/runs/demo_block --out .cdo/eval/demo_block --steering-out .lev/steering/runs/demo_block
npm run wizard-v43:demo   # v4.3 object card -> WorkCard/LoopPlan/route receipts
npm run team:demo         # 3x3x3 provider-neutral durable team run
npm run live-swarm:run    # 27-seat live worker swarm using Claude Bridge + Codex by default
npm run fused-wizard-loop:live # current v4.3 route loop, hard-gate reject -> requeue
npm run lev:mine:demo    # mine bundled Lev-shaped fixture into proposal-only gates
npm run research-ratchet:demo # probe-approve one mined gate, consume it, emit non-enforcing host receipt
npm run long-horizon:demo # project basin, missing concepts, ColdStartPacket, move classification
npm run lev-host:consume # ask local host Lev CLI to consume a ClaimGate steering run
npm run gate-loop:demo    # fan -> gate -> graveyard/requeue -> admitted
npm run overall:build     # v4.3 adapter + live flexible model pool + hard gate loop receipt
npm run product:run       # safe live worker pool + live swarm + fused loop + product receipt
npm run product:run:counterintel-openrouter # explicit OpenRouter counterintel spend path
npm run source:integration:audit # source claims ledger; blocks fake "properly integrated" claims
npm run self:run          # mass provider refresh + team + overall + controller + honesty audit
npm run honesty:check     # fail if admitted candidates used synthesized evidence
npm run action:mock       # local GitHub Action PR metadata/check-run path
npm run marketing:demo    # Marketing Scientist readiness gate + Marketing Harness metric gate
npm run marketing:harness-demo # campaign brief -> variants -> metrics verdict
npm run standalone:check  # no outside repo/private-path/missing require deps
npm run product:zip       # manifest-driven zip builder, max-500 checked
npm run demo:all          # full suite data for UI
```

## Standalone boundary

ClaimGate is the product boundary. Source systems can contribute design
patterns, but the zip must contain every runtime dependency it references. The
standalone check fails on private machine paths, source-world repo references,
and missing relative runtime imports.

## Production boundary

Local CLI and UI run now. The GitHub App scaffold is included, but live GitHub use requires registering a GitHub App and setting `apps/github-app/.env.example` values.

This package is capped under 500 archive entries for Claude Design / tool processing.
