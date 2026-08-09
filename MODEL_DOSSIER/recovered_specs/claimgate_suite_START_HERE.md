# ClaimGate / Lev Harness Pack v45 — Start Here

This is a complete portable prototype of a Lev-native Project Harness pack.

New in v45 Wizard v4.3 route-topology state-model bridge: the fused Wizard loop no longer
pretends that a flat 27-seat advisory fan is the Wizard runtime. It now models
the current Wizard v4.3 route-truth topology, with legacy v4.2 lineage treated
as provenance rather than live-runtime proof. A default fixture run is:

```text
1 parallel Wizard stack
x 3 sequential council cycles
x Decision -> Failure -> Follow-Up
x 9 core parent routes + 5 management side routes per cycle
x 56 formal child roles per cycle
x 1 model agent per child role
= 168 agent seats
```

The packaged fused-loop receipt is deterministic fixture evidence for topology,
requeue, and hard-oracle fan-in. It is not a live spawned-Codex-subagent proof.
The 27-seat TeamHarness remains an advisory swarm/team substrate, not the full
Wizard runtime.

New in v44 long-horizon harness core: the package carries the deterministic
`@claimgate/long-horizon-harness` projection layer from the v42 line. It builds
explicit project state, attractor basin maps, move classifications, missing
concept ledgers, ColdStartPackets, memory operator precondition checks, and
hybrid memory reranks. This is intentionally projection-only: it helps a model
stay inside the project basin, but it does not admit, enforce, or promote.

Model policy is now explicit: mass workers default to Claude Bridge Sonnet plus
Codex native. Direct Claude Bridge routes may use Sonnet, Sonnet-high, or Opus
when explicitly selected. OpenRouter is a sparse counterintelligence lane only,
using the named Chinese routes once per prompt/input-output surface when
explicitly enabled. OpenRouter Opus/GPT routes are forbidden, and Fusion is not
the normal Chinese counterintel path because it can hide non-Chinese/Opus-class
routing.

New in v40 cryptographic trust-root: the bounded Research Ratchet authority
chain now has optional ECDSA P-256 owner and host trust roots. Fixture
signatures remain available for local demos, but once a trust root is supplied
they fail closed with explicit reason codes. Trusted signed owner approvals and
host receipts can admit; untrusted keys, invalid signatures, and replayed
approval hashes block. The canonicalization label is now the honest
`canonical-json-sorted-v1`, not an RFC8785 claim.

Carried from v39 tightened: one mined gate proposal can move through the bounded
Research Ratchet authority chain only as four separate artifacts:
`MinedGateProposal -> OwnerGateApproval -> HostGateConsumptionRequest ->
HostGateAdmissionReceipt`. Local lifecycle is separate from host result:
`proposed -> approved_pending_host_consumption -> host_consumption_recorded`,
while the host result is `admitted`, `caveated`, `rejected`, or `blocked`.
Mined gates still do not become canon, admitted, or enforced from proposal text,
LLM output, digger output, or council agreement. Probe-only approval cannot
escalate to enforcement, and orphan/replayed/mismatched receipts fail closed.

New in v38: malformed evidence-manifest JSON is recorded as
`evidence_manifest.details.parse_errors` and fails closed instead of being
silently treated as an empty manifest.

New in v37: `allowSelfAttested` is no longer a dead or permissive flag. If a
legacy caller requests it, ClaimGate emits `self_attestation_policy` and blocks
with `ALLOW_SELF_ATTESTED_DISABLED`.

New in v36: core ClaimGate verdicts and receipts include `gate_strength`, so a
permissive pass is visibly weaker than source-bound or signed-source-bound
evidence. MassRun source-pack receipts also expose `key_custody` and
`protection_level`, and fixture-key source packs use the self-disclosing ceiling
`mass_run_proven_with_external_connector_fixture_key_manifest_refs`.

New in v35: `claimgate source-pack issue` exposes the source-pack issuer as a
reusable CLI/API instead of leaving pack creation inside the demo script.

New in v34: MassRun can consume an external connector source pack
(`manifest-store.json`, `trust-root.json`, `bindings.json`, payloads), verify
every WorkRun source ref before model fanout, and run the hard gate against
verified copied workcards.

New in v31: the package mines Lev-shaped source material into proposal-only
Axiom -> Constraint -> Gate reports and can record a local host-consumption
receipt when a host checkout consumes a ClaimGate steering-run projection.

New in v30: signed source manifest verification is a product gate. A source
reference can only become gate evidence when it resolves through a signed,
connector-bound manifest entry; local paths and unsigned refs fail closed.

New in v28: the source-integration truth ledger now treats the 0xRicker
self-verifying-loop post as operator-supplied source text that was processed
into an adapter/pattern implementation, while still blocking claims that the X
source was independently fetched or that the article-scale runtime was
reproduced.

New in v27: the Lev adapter is no longer dead code. It can project a ClaimGate
run into both the older compatibility eval tree and a current
`.lev/steering/runs/<run-id>` patch target with `EvalJobOutput` /
`ProofSpec`-shaped files. The projection is still marked
`live_lev_consumed:false`; local host consumption is recorded as a separate
`.cdo/lev-host-consumption/summary.json` receipt.

The product shape is:

```text
Axiom Digger -> Constraint Digger -> Gate Digger -> Lev Project Harness
Lev source miner -> proposal-only gates -> owner review
WorkCard + OracleCard -> Wizard/Team/Swarm branches -> hard oracle gate -> requeue rejects -> zero-reject receipt
```

## Run

```bash
npm run doctor
npm run demo:all
npm run manifest-gate:demo
npm run mass-run:source-pack-demo
node packages/claimgate-cli/bin/claimgate.js source-pack issue --workcards examples/mass_run/wc-alpha/workcard.json,examples/mass_run/wc-beta/workcard.json,examples/mass_run/wc-gamma/workcard.json --out .cdo/source-packs/mass-run-demo
npm run lev:mine:demo
npm run research-ratchet:demo
npm run long-horizon:demo
npm test
npm run ui
```

Open:

```text
http://localhost:4317
```

## Most important demos

```bash
npm run swarm-loop:demo
npm run fused-wizard-loop:live
npm run manifest-gate:demo
npm run mass-run:source-pack-demo
npm run lev:mine:demo
npm run research-ratchet:demo
npm run long-horizon:demo
npm run long-horizon:from-real-lev
npm run harness:demo
npm run gate-loop:demo
npm run marketing:demo
```

## Important boundary

This ZIP is not a replacement for Lev OS. It is a proposed Lev-native harness pack. It emits Lev-shaped eval suite source, eval run projections, mined gate proposals, and local host-consumption receipts when the host CLI consumes a steering run.

The current system-map boundary is "one brain, many surfaces": the host
eval/proof path is the proof brain; FlowMind is the authoring plane; effect and
receipt surfaces carry observed reality. In the audited local checkout, concrete
targets are `core/orchestration/src/eval`, `core/orchestration/src/effect`,
`core/orchestration/src/receipt`, `core/orchestration/src/proof`, and
`core/orchestration/src/handlers/claimgate-steering.ts`. ClaimGate can bind,
sign, gate, and record local artifacts, but semantic proof closure still
requires evidence refs, measurements, and a host policy/eval result from the
runtime that owns promotion.

The current host Lev audit says the actual runtime seam is
`.lev/steering/runs/<run-id>/eval-job-output.json` plus `proof-spec.json`, not
the older `.lev/runs/eval/<run-id>/proof.yaml` compatibility tree.

A successful local host-consumption receipt means
`host_consumed_local_lev_checkout`, not public merge, release admission, or
proper standalone integration.

A successful default v40.1 Research Ratchet demo receipt means one probe-only
mined gate proposal was consumed by the local host admission path and recorded
with a separate request plus independent receipt. It stays `enforced:false`.
If trust roots were supplied, the owner approval and host receipt also passed
real signature checks. It does not mean Leviathan integration is complete,
public `core/eval` admitted the change, or autonomous mined gates are now
enforced.
