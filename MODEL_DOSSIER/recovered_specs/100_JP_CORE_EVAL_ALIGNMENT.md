# v23 JP Core/Eval Alignment

## Decision

The latest JP note is accepted as a binding product constraint:

```text
Lev is the project harness / eval suite substrate.
ClaimGate must be a project harness pack, not a mini proof runtime.
```

The product shape is now:

```text
ClaimGate SDLC Harness
GrowthGate Marketing Harness
GateDigger Harness Author
WizardLoop Branch Explorer
OracleLoop Loop-Until-Clean Demo
```

All production proof authority should route through Lev-shaped evaluator/admission
layers. In the local Lev checkout audited for this build, the built hard root is
not an `@lev-os/eval` package. The current built root is:

```text
core/flowmind/src/kernel/constraint-manifold.ts
core/flowmind/src/gate-evaluator.ts
core/flowmind/system/constraint-manifold.flow.yaml
core/orchestration/src/eval/*
core/orchestration/src/proof/*
code companions
GateProof / ProofBundle / proof.yaml projections
execution-ledger run refs
```

`core/eval` remains product-direction and compatibility language here unless a
live Lev checkout actually exposes that runtime. The standalone package remains
useful because it proves the loop locally, but it must be treated as a prototype
harness pack and not as a separate claim/proof economy.

## Semantic-control translation

JP's explanation maps to this implementation boundary:

```text
for this task / loop / flowmind:
  declare ontology, target, measures, and scoring policy

validator node on graph:
  receives typed observations and evidence refs

lev exec:
  dispatches and controls CLI agents, sessions, and external tools

validator output:
  structured eval facts, scores, reasons, evidence refs

deterministic gate:
  outside the agents' authority; decides pass/fail/requeue/block
```

## No duplicate stack rule

Do not add a second universal receipt, proof, or gate substrate. ClaimGate may
emit project-harness source, FlowMind verify-slot proposals, code companions,
and proof-shaped projections; it may not claim that Lev admitted those artifacts
unless a live Lev validator consumed them.

Allowed:

- domain harnesses;
- eval-suite source files;
- code companions;
- probe and non-static gap ledgers;
- oracle adapters;
- pass/reject/requeue demos;
- exports that match Lev eval roots.

Not allowed:

- agent consensus as admission;
- LLM judge as final proof;
- receipts as proof by themselves;
- a separate universal proof store;
- a new runtime overlay engine;
- a separate promotion primitive owned by ClaimGate.

## Product implication

The strongest product sentence is now:

```text
ClaimGate/GrowthGate are Lev-native Project Harnesses for AI work loops.
```

ClaimGate is the SDLC harness. GrowthGate is the marketing harness. GateDigger is the authoring layer that proposes eval packs from project standards. OracleLoop is the loop controller demo that proves reject/requeue/clean behavior.

## Current Patch Seam

The current host Lev proof target is not only a `proof.yaml` projection. The
adapter now emits a steering-run patch target:

```text
.lev/steering/runs/<run-id>/proof-spec.json
.lev/steering/runs/<run-id>/eval-job.json
.lev/steering/runs/<run-id>/eval-job-output.json
```

Those files are still `live_lev_consumed:false` until host Lev consumes them
through its proof/eval fabric and writes a real receipt.
