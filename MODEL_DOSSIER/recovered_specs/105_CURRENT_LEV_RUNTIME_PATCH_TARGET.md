# Current Lev Runtime Patch Target

## Source Status

This note processes the latest Claude/JP context as a source-intake artifact and
checks it against the host Lev checkout.

Verified current Lev surfaces:

```text
core/flowmind/src/kernel/constraint-manifold.ts
core/flowmind/src/gate-evaluator.ts
core/orchestration/src/eval/index.ts
core/orchestration/src/eval/types.ts
core/orchestration/src/proof/eval-job-types.ts
core/orchestration/src/proof/flows/eval-flow.ts
core/orchestration/src/proof/proof-spec-generator.ts
core/harness/src/substrates/tmux-substrate.ts
dna/gates.yaml
.lev/validation-gates.yaml
plugins/sdlc/config.yaml
```

## Correction

The product must not claim that `.lev/runs/eval/<run-id>/proof.yaml` is the
host Lev proof authority. That tree is a standalone compatibility projection.

The current runtime patch target is:

```text
.lev/steering/runs/<run-id>/
  run.json
  proof-spec.json
  eval-job.json
  eval-job-output.json
  boundary.json
```

The `eval-job-output.json` projection uses Lev's current `EvalJobOutput`
vocabulary:

```text
verdict: pass | fail | conditional | deferred
evidence: ProofResult[]
repairCandidates?: RepairCandidate[]
receiptId?: string
```

## Implemented Product Delta

`packages/claimgate-lev-adapter.projectRun(...)` now writes the existing
compatibility eval projection and can also write a steering-run projection.

`packages/claimgate-lev-miner.mineLevSources(...)` mines the local host source
corpus into proposal-only Axiom -> Constraint -> Gate reports:

```text
dna/graph.yaml
dna/gates.yaml
.lev/validation-gates.yaml
plugins/sdlc/config.yaml
docs/VISION.md
```

`packages/claimgate-lev-host.consumeClaimGateRunWithLocalLev(...)` asks a local
host CLI to consume a ClaimGate steering-run projection and records a separate
receipt under:

```text
.cdo/lev-host-consumption/summary.json
```

The CLI exposes it:

```bash
node packages/claimgate-cli/bin/claimgate.js lev-adapter project-run \
  --run .cdo/runs/demo_block \
  --out .cdo/eval/demo_block \
  --steering-out .lev/steering/runs/demo_block

node packages/claimgate-cli/bin/claimgate.js lev-mine \
  --lev-root <host-lev-checkout> \
  --out .cdo/lev-mining/report.json

node packages/claimgate-cli/bin/claimgate.js lev-host consume \
  --run .cdo/runs/action_mock \
  --out .cdo/lev-host-consumption \
  --lev-root <host-lev-checkout>
```

Every steering-run projection includes:

```text
live_lev_consumed:false
```

That is intentional. The projection is the proposed patch seam, not proof that
the host Lev runtime consumed the run.

## Current Honest Ceiling

If `lev-host consume` succeeds, the product can claim:

```text
host_consumed_local_lev_checkout
```

That means a local host checkout consumed the projection and recomputed the same
verdict. It does not mean public host-repo merge, release admission, or proper
standalone integration.

Mined Lev gates also stay proposal-only:

```text
proposal_only_until_owner_admits
```

## Still Blocked

This package still does not prove:

- a public host release consumed the generated run;
- host release admission accepted ClaimGate obligations as proof authority;
- the host execution ledger emitted a release-admission receipt for the steering
  run;
- `projectRun` is wired into a real `lev exec` graph node;
- ClaimGate owns final proof authority;
- mined Lev gates are automatically enforced.

The next load-bearing patch is to make selected mined constraints owner-approved
and consumed by the host evaluator/admission path, then record a public/release
receipt beside the adapter projection. Do not mutate the adapter projection's
`live_lev_consumed:false`; attach the host receipt as separate evidence.
