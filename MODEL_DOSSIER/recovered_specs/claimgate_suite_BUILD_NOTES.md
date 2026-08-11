# Build Notes

This pack is a self-contained runnable prototype. The source-integration audit
now prevents "inspired by" or "pattern extracted" work from being called proper
integration.

## Smoke-tested commands

```bash
npm run doctor
npm run demo:all
npm test
npm run source:integration:audit
npm run manifest-gate:demo
npm run mass-run:source-pack-demo
npm run lev:mine:demo
npm run research-ratchet:demo
npm run model-pool:refresh
npm run live-swarm:run
npm run fused-wizard-loop:live
npm run product:run
npm run action:mock
npm run marketing:demo
npm run marketing:harness-demo
npm run product:zip
```

## v40 Cryptographic Trust-Root Authority Chain

v40 keeps the v39 four-artifact Research Ratchet shape and adds the missing
cryptographic authority check:

```text
MinedGateProposal
  -> OwnerGateApproval signed by owner key
  -> HostGateConsumptionRequest
  -> HostGateAdmissionReceipt signed by host key
```

Fixture signatures still exist for local demos. They are explicitly labeled
`LOCAL_SHA256_FIXTURE`. If an owner or host trust root is supplied, fixture
signatures fail closed with `owner_approval_signature_not_real` or
`host_receipt_signature_not_real`. Real ECDSA P-256 signatures admit only when
their key id appears in the supplied trust root and the signature verifies over
the hash-bound approval or receipt.

v40 also adds a replay ledger option so approval reuse is blocked by a durable
JSONL ledger instead of only by caller-threaded state, and it renames the
canonicalization scheme to `canonical-json-sorted-v1`. The package no longer
claims RFC8785/JCS conformance.

Allowed claim: v40 proves one owner-approved mined gate proposal can be
consumed by the local host admission path with optional real owner/host
signature verification and replay protection.

v40.1 acceptance repair: `npm run research-ratchet:demo` now defaults to a
probe-only fixture approval. It can emit a useful local host receipt, but the
summary stays `enforced:false`. Enforcement-grade consumption requires owner
and host trust roots, real owner and host signatures, hash-bound artifacts, and
replay protection.

Forbidden claims: public Leviathan admission, production KMS/HSM custody,
external connector identity proof, release admission, or autonomous mined-gate
enforcement. In the audited local checkout, the concrete eval/effect/receipt
targets live under `core/orchestration/src/*`; `core/eval` remains
compatibility/product-direction shorthand unless a host checkout exposes it.

System-map boundary: Lev's host eval/proof path is the proof brain; FlowMind is
the authoring plane; effect and receipt surfaces carry observed reality.
ClaimGate can prepare, sign, hash, gate, and locally receipt artifacts, but
final semantic closure requires host evidence refs, measurements, and
policy/eval output.

## v39 Tightened Owner-Admitted Authority Chain

This is the single v39 ratchet click:

```text
MinedGateProposal
  -> OwnerGateApproval
  -> HostGateConsumptionRequest
  -> HostGateAdmissionReceipt
```

Allowed claim: v39 proves one owner-approved mined gate proposal can be consumed
by the host evaluator/admission path and recorded with an independent host
receipt. The tightened v39 chain keeps local lifecycle separate from host
result and carries the proposal hash, approval hash, request hash, host result,
gate strength, evidence refs, and exercised code path in the receipt consumers
actually read.

Forbidden claims: Leviathan integration complete, final proof authority,
autonomous mined gates now enforced, release admitted, or Research Ratchet fully
implemented.

Tested invariants:

- proposal alone blocks with `owner_approval_required`;
- owner approval alone stays `approved_pending_host_consumption`;
- host consumption emits `host-gate-admission-receipt.json`;
- proposal hash mismatch blocks with `proposal_hash_mismatch`;
- LLM/digger claims of admitted/enforced block with
  `non_authoritative_promotion_claim`;
- canonical proposal hashes are stable across JSON key order;
- probe-only approvals can admit an observation but cannot set `enforced:true`;
- orphan host receipts block with `host_receipt_owner_approval_required`;
- replayed approvals block with `approval_replay_detected`;
- local absolute paths are redacted from host receipts;
- v37 self-attestation and v38 malformed evidence-manifest protections remain.

## v34 External Source-Pack MassRun

## v38 Evidence Manifest Parse Errors

Malformed evidence-manifest JSON now fails closed with an explicit record:

```text
evidence_manifest.details.parse_errors[
  { code: "evidence_manifest_parse_failed", ... }
]
```

Previously a bad manifest file could collapse into generic missing evidence.
The gate still failed for required evidence, but the receipt lost the actual
cause. v38 keeps the cause at the hard-gate surface.

## v37 Self-Attestation Disabled

The legacy `allowSelfAttested` option is now wired to a deterministic hard gate
instead of being a dead flag. Any caller that requests it receives:

```text
self_attestation_policy
ALLOW_SELF_ATTESTED_DISABLED
```

This is deliberately not a permissive mode. Self-attested evidence cannot weaken
object binding, evidence manifests, signed manifest refs, or hard-gate promotion.

## v36 Gate-Strength + Custody Receipts

Core ClaimGate results now include `gate_strength`:

```text
blocked
caveated
permissive
source_bound
signed_source_bound
```

The field is written to both `gate-result.json` and `receipt.json`. This keeps a
low-boundary evidence-light pass from looking equivalent to a source-bound or
signed-source-bound pass.

MassRun source-pack receipts now also include `key_custody` and
`protection_level` in the `manifest_gate` block. The bundled source-pack demo
uses fixture key custody, so its honest ceiling is:

```text
mass_run_proven_with_external_connector_fixture_key_manifest_refs
```

Only a connector pack with stronger key custody/protection should earn a
stronger external-key or HSM-key ceiling.

V35 exposes the source-pack issuer directly:

```bash
node packages/claimgate-cli/bin/claimgate.js source-pack issue \
  --workcards examples/mass_run/wc-alpha/workcard.json,examples/mass_run/wc-beta/workcard.json,examples/mass_run/wc-gamma/workcard.json \
  --out .cdo/source-packs/mass-run-demo
```

MassRun can take an external connector source pack:

```text
manifest-store.json
trust-root.json
bindings.json
payloads/<manifest-entry-id>.json
```

`npm run mass-run:source-pack-demo` builds a deterministic connector-style pack
from the bundled examples, verifies every `mf_*` source ref before model fanout,
copies verified payloads into `.cdo/mass-run-external/verified-workcards/`, and
runs the hard gate against those verified workcards. If any payload hash,
signature, trust root, expiry, scheme, or intent check fails, MassRun blocks
before spending provider calls.

The honest fixture-key ceiling is:

```text
mass_run_proven_with_external_connector_fixture_key_manifest_refs
```

The bundled demo still uses fixture key custody; production connectors should
issue the same pack shape with external key custody/HSM.

## v31 Lev Mining + Host Consumption

The package now has a real Lev-facing mining/consumption lane:

- `packages/claimgate-lev-miner` reads Lev-shaped source files and emits
  proposal-only Axiom -> Constraint -> Gate reports.
- `packages/claimgate-lev-host` projects a ClaimGate run and asks a local host
  CLI to consume it, writing `.cdo/lev-host-consumption/summary.json`.
- `claimgate lev-mine` and `claimgate lev-host consume` expose the path.
- The web UI has a Lev Mining view.

The honest ceilings are:

```text
lev-mining: proposal_only_until_owner_admits
lev-host: host_consumed_local_lev_checkout
proper integration: still false without public/release/signed evidence
```

## v30 Signed Manifest + Live Product Run

The signed manifest gate is now a real product surface:

- `packages/claimgate-manifest-gate` verifies signed manifest entries.
- `claimgate manifest-gate verify` exposes the verifier through the CLI.
- `packages/claimgate-core` includes an optional load-bearing
  `signed_manifest_gate` when a claim/effect requires signed source refs.
- `npm run manifest-gate:demo` writes compact public receipts under
  `.cdo/manifest-gate/`; fixture signing proves verifier behavior only.

Proper source integration now requires source processing, runtime integration,
in-repo receipts, and signed manifest refs for source-backed promotion claims.

## Fusion/Chinese Fleet Refresh

The current live-pool default does not run OpenRouter. Mass-spawn worker lanes
default to direct Claude Bridge Sonnet plus Codex native. Exact availability is
verified per run and failures are recorded literally:

```text
claude-bridge/claude-sonnet-4-6
openai-codex/codex-native
```

OpenRouter is an explicit counter-intelligence and variation lane only. Run
`npm run model-pool:counterintel-openrouter` or
`npm run product:run:counterintel-openrouter` when you intentionally want to
spend OpenRouter credits on current Chinese frontier routes:

```text
deepseek/deepseek-v4-pro
qwen/qwen3.7-max
moonshotai/kimi-k2.7-code
z-ai/glm-5.2
minimax/minimax-m3
```

OpenRouter Fusion remains cataloged but requires separate opt-in because it can
hide non-Chinese/Opus-class routing. DeepSeek Flash, Qwen Plus, and Gemini
Flash are fallback/override lanes, not proof seats for stronger claims.
OpenRouter Claude Opus and OpenRouter GPT routes are forbidden in this product
path. Direct Claude Bridge Opus and Sonnet-high are allowed when explicitly
selected; the spend guard is about not buying those model families through
OpenRouter.

The latest real live `3x3x3` swarm attempted all 27 members and stayed blocked:
4 members completed, 23 failed, and the accepted set had only 2 providers / 2
models. That blocked product-run status is intentional because the live swarm
requires at least 9 completed seats across at least 3 providers and 3 models.

`fused-wizard-loop:live` is the closed-loop bridge, not the 27-seat swarm. It
models the current Wizard v4.3 route-truth topology: Decision -> Failure ->
Follow-Up, 9 core parent routes, 5 management side routes, 56 formal child roles
per council cycle, and three sequential council cycles. Legacy v4.2 material is
lineage/provenance here, not live-runtime proof. The default fixture is 168
agent seats before model-family multiplication. The hard oracle rejects
mismatches, reject reasons feed the next prompt, and the run exits only when the
deterministic oracle has no remaining rejections. Model/council output remains
proposal-only.

The overall build passed with provider/model-diverse accepted observations. The
evidence-manifest hard wall now keeps controller-generated placeholder evidence
out of the admitted path; `honesty:check` is expected to report
`admitted_on_synthesized_evidence: 0`.

`overall:build` uses bundled advisory-only fixture receipts under
`examples/model_pool/fixture-live-pool` so `product:verify` stays deterministic.
`product:run` refreshes the real live model pool and may block when provider
credits, auth, or routes are unavailable.

## LiveSwarm / unified product run

`tools/live-swarm-run.js` now attempts the full `3x3x3` TeamHarness topology
through the live provider adapters exported by `tools/live-model-pool.js`.
Completed seats require parseable typed JSON. Blocked, malformed, or unavailable
provider seats are recorded literally and do not count toward provider/model
diversity. The swarm remains soft and non-promoting.

`tools/product-run.js` is the unified local product run:

```text
live model pool refresh
-> signed manifest gate
-> live 3x3x3 swarm
-> live fused Wizard loop
-> npm run product:verify
-> Lev source mining
-> Research Ratchet owner-approved mined-gate host consumption
-> local Lev host consumption
-> product-run receipt
```

`tools/package-zip.js` rebuilds `PACKAGE_MANIFEST.txt`, updates
`ZIP_ENTRY_COUNT.txt`, and creates the max-500 zip from the manifest boundary.

## Core Lev OS / Marketing Scientist cut

This pack adds the plugin-first Core Lev OS direction:

- ClaimGate/SDLC remains the first proof-friendly manifestation domain.
- `action/run-github-action.js` turns GitHub PR metadata into the required-check path.
- `plugins/marketing-scientist` and `examples/marketing_scientist` demonstrate
  creative/business work as bounded experiments with delayed telemetry gates.
- `packages/claimgate-marketing` and `examples/marketing` add the concrete
  planner/verifier loop: campaign brief -> variants -> metrics envelope -> verdict.
- `policy-packs/marketing-experiment.json` names the first marketing-domain gate policy.

## Components

- CLI: `packages/claimgate-cli/bin/claimgate.js`
- Core gate engine: `packages/claimgate-core/src/index.js`
- Web UI: `apps/web-ui/`
- GitHub App scaffold: `apps/github-app/server.js`
- GitHub Action: `action/action.yml`
- GitHub Action runner: `action/run-github-action.js`
- Marketing Scientist plugin: `plugins/marketing-scientist/`
- Marketing Harness package: `packages/claimgate-marketing/`
- Lev source miner: `packages/claimgate-lev-miner/`
- Local Lev host consumption: `packages/claimgate-lev-host/`
- LiveSwarm runner: `tools/live-swarm-run.js`
- Unified product runner: `tools/product-run.js`
- Manifest zip builder: `tools/package-zip.js`
- Specs/docs: `docs/`
- Schemas: `schemas/`
- Policies: `policy-packs/`
- Claude Design import/reference: `design/claude-design-import/`

## Honest caveat

The local CLI/UI are runnable now. The GitHub App server is functionally scaffolded, including auth/signature/check/comment code, but requires registering a GitHub App and setting real environment variables before it can post live checks and comments.

## Suite v2 additions

This pack adds WorkCard, Rework Compiler, Graveyard Intelligence, Experience Compiler, proposal cards, suite demo, and expanded UI views.

Smoke-tested commands:

```bash
npm run doctor
npm run demo:suite
npm test
npm run ui:smoke
```
