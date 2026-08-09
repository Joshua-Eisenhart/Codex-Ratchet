# Current Lev Surface Audit

This note records the local Lev checkout audit used for this package cut.

## Checked Surfaces

Current hard root found in the local host Lev checkout audited for this build:

```text
core/flowmind/src/kernel/constraint-manifold.ts
core/flowmind/src/gate-evaluator.ts
core/flowmind/system/constraint-manifold.flow.yaml
core/orchestration/src/eval/index.ts
core/orchestration/src/eval/types.ts
core/orchestration/src/effect/types.ts
core/orchestration/src/receipt/types.ts
core/orchestration/src/proof/eval-job-types.ts
core/orchestration/src/proof/flows/eval-flow.ts
core/orchestration/src/proof/proof-spec-generator.ts
core/orchestration/src/handlers/claimgate-steering.ts
core/harness/src/substrates/tmux-substrate.ts
dna/graph.yaml
dna/gates.yaml
```

The built root validator exports and documents:

```text
F01_FINITUDE
N01_NONCOMMUTATION
```

The current proof/eval runtime target found in the host checkout is the
`claimgate-steering` run-dir contract plus `EvalJobOutput` / `ProofSpec` fabric:

```text
.lev/steering/runs/<run-id>/
  run.json
  proof-spec.json
  eval-job.json
  eval-job-output.json
  boundary.json

host write outputs:
  lev-consumption-receipt.json
  lev-consumption-boundary.json
  lev-consumption-events.jsonl

EvalJobOutput.verdict = pass | fail | conditional | deferred
generateProofSpec(dna/gates.yaml, targetRef)
executeProofSpec(...)
EvalFlow.run(targetRef)
```

The current gate evaluator also implements the semantic-computing sandwich:
variable triples enter as `{value, confidence, evidenceCount}`, deterministic
weighted formula evaluation decides the score/threshold result, and low
confidence can route to an uncertain/probe branch.

`dna/graph.yaml` marks `core/flowmind/src/kernel/constraint-manifold.ts` as
the built constraint manifold and describes `core/eval`-style work as direction,
not as the current concrete package.

## Product Boundary

ClaimGate may emit:

- Project Harness source under `.lev/eval/suites/`;
- FlowMind verify-slot proposals;
- typed observations and measurements;
- code-companion scaffolds;
- GateProof / proof.yaml projections;
- compatibility eval run projections under `.lev/runs/eval/`;
- Lev-runtime patch target projections under `.lev/steering/runs/<run-id>/`
  with `eval-job-output.json`, `eval-job.json`, and `proof-spec.json`;
- source and non-static gap ledgers.

ClaimGate may not claim:

- a live `@lev-os/eval` runtime is installed;
- `core/eval/src/constraint-manifold.ts` exists in the audited checkout;
- a `core/eval` directory exists in the audited checkout;
- Lev admitted a harness pack unless a live Lev command consumed it;
- a `.lev/steering/runs/<run-id>/eval-job-output.json` projection is admission
  by itself;
- LLM council agreement promoted anything across the hard wall.

## JP Translation

JP's "semantic control" shape maps to this product contract:

```text
ontology + scoring policy
  -> validator node on the graph
  -> lev exec / CLI agents produce structured eval facts
  -> deterministic gate outside agents decides pass/fail/requeue/block
```

The current package is therefore a Project Harness pack and local hard-wall
prototype. It is not a replacement Lev evaluator runtime.

## Patch Target

The next Lev-native patch target is concrete:

```text
ClaimGate run
  -> packages/claimgate-lev-adapter.projectRun(...)
  -> .lev/steering/runs/<run-id>/proof-spec.json
  -> .lev/steering/runs/<run-id>/eval-job-output.json
  -> host Lev EvalFlow / executeProofSpec consumes the obligations
  -> host Lev execution ledger records the real receipt
```

Until the host Lev runtime consumes that steering run, the adapter projection
must carry `live_lev_consumed:false`.
