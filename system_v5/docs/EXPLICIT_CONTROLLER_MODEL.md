# Explicit Controller Model

Status: CONCEPTUAL AUTHORITY / FRAMING DOC — not the live queue, not the live truth-status surface, and not the live run-operations checklist.

## Status

- Date: 2026-04-11
- Role: execution-facing controller model
- Purpose: make the operational unit, allowed transitions, and real progress criteria explicit

## Why This Exists

The repo already has strong process rules, truth labels, and build-order guidance.
What has remained too implicit is the controller's actual runtime model.

This file makes one thing explicit:

- the controller is not here to "understand the theory"
- the controller is here to move bounded objects through honest state transitions
- the computer-science translation of that job lives in `new docs/ANOMALOUS_COMPUTER_SCIENCE_TRANSLATION.md`

## Short Description

Codex Ratchet is a staged research-construction system.
It compiles speculative math material into explicit bounded objects, tests those objects with local probes and sims, records evidence with strict labels, and advances only the next honest state transition.

The system is not a wiki summarizer.
It is not a prose-first theory assistant.
It is a controller for machine-checkable research object construction.

## System Purpose

The system exists to:

1. ingest high-entropy source material
2. normalize it into explicit local math objects
3. express those objects as bounded candidates with dependencies
4. run honest local probes or sims against them
5. classify outcomes with strict truth labels
6. keep queue, ledger, registry, and maintenance surfaces aligned with actual evidence

The controller's job is to preserve this order.
If a run does not advance one bounded object or clean one false/stale state surface, it is not real progress.

## What The Controller Is Actually Controlling

The controller is controlling state, not documents.

Its real control surfaces are:

- queue state: what bounded object is allowed to run next
- dependency state: what must exist before a candidate can move
- evidence state: what was actually observed, rerun, or falsified
- truth-label state: what can honestly be said now
- maintenance state: which docs, ledgers, and registries became stale because evidence changed

The interface layer is only transport.
Telegram or iMessage is not the system.

## Core Objects

### 1. Lego

A lego is the default unit of constructive work.
It is a small local math object or tightly bounded structure that should be testable without bridge inflation.

Examples:

- carrier admission
- local geometry object
- operator family
- graph or cell-complex view
- bipartite witness
- local entropy quantity

Authority surfaces:

- `new docs/16_lego_build_catalog.md`
- `new docs/17_actual_lego_registry.md`

### 2. Candidate

A candidate is a proposed explicit object, relation, or build move that is not yet earned as process-canonical.
A candidate may be viable, blocked, rejected, partial, or late-surface only.

Examples:

- a local math object that still lacks a clean probe
- a proposed dependency chain
- a possible shell stacking or coexistence successor
- a late bridge object that is listed but not yet admissible for default promotion

### 3. Probe or Sim

A probe is the bounded execution unit that tests one object or one narrow relation.
A probe is not a general theory run.
Its job is to return evidence that changes a bounded object's state.

### 4. Result Artifact

A result artifact is the machine output from a fresh run.
It is the primary evidence surface for repo-state claims about execution.

Typical forms:

- result JSON
- rerun log
- validator output
- audit output

### 5. Evidence Record

Evidence is what supports, contests, or refutes a bounded claim.
Evidence is append-only and path-specific.

The controller should prefer:

- current result artifacts
- current rerun outputs
- current validator outputs

over prose summaries.

### 6. Queue Item

A queue item is a controller-ready bounded move.
It should name:

- the object to advance
- the exact dependency or blocker
- the expected artifact
- the verification step
- the maintenance closure required after the run

### 7. Registry or Ledger Row

A registry row is the persistent state summary for one object.
It is not evidence by itself.
It is a controller-facing projection of evidence and queue state.

### 8. Maintenance Surface

A maintenance surface is any doc or machine ledger that must be updated when evidence changes.

Examples:

- lego catalog
- actual lego registry
- backlog matrix
- truth audit
- gap matrix
- controller checklist

## Unit Of Work

The unit of work is not "read docs."
The unit of work is one bounded candidate or lego transition.

Good units of work:

- split one bundled row into explicit local objects
- build one missing local probe for one named lego
- rerun one existing probe and relabel its truth state honestly
- test one pairwise successor relation after its prerequisites are real
- repair one stale registry or audit surface after new evidence landed

Bad units of work:

- "understand the theory better"
- "read the wiki and summarize"
- "write a broad controller overview" with no queue effect
- "run a lot of sims" with no named object transition

## Allowed State Transitions

The controller should think in object transitions like these:

### A. Source Material -> Normalized Object

Allowed when:

- a source doc names a concrete object clearly enough to isolate
- the object is still hidden inside bundled prose or mixed rows

Output:

- explicit lego or candidate row
- explicit dependency note
- explicit suggested probe

### B. Normalized Object -> Queued Build Target

Allowed when:

- the object is local enough to test honestly
- its prerequisites are known
- a bounded probe can be named

Output:

- queue item with probe path, expected result path, and verify step

### C. Queued Build Target -> Fresh Evidence

Allowed when:

- the exact bounded probe is run
- the run produces a path-citable artifact
- the output is reviewed under the repo truth-label rules

Output:

- result artifact
- explicit status label
- blocker or successor note

### D. Fresh Evidence -> Registry Or Ledger Update

Allowed when:

- the evidence actually changes what is honestly claimable
- the update cites the evidence path

Output:

- registry row updated
- backlog or truth-audit update
- stale prose marked or corrected

### E. Local Lego -> Pairwise Or Coexistence Successor

Allowed only when:

- the local lego is already real enough for upward movement
- the next successor is still bounded
- the successor does not smuggle bridge claims prematurely

Output:

- one pairwise or coexistence queue item

### F. Candidate -> Blocked Or Rejected

Allowed when:

- the dependency chain fails
- the local negative case kills the proposal
- the surface is real but too late for current build order

Output:

- blocked, rejected, or late-surface classification
- preserved evidence
- no silent deletion

## Not Allowed

The controller should refuse these moves:

- prose promotion without evidence path
- treating "exists" as "runs"
- treating "runs" as "passes local rerun"
- treating "passes local rerun" as "canonical by process"
- merging lane progress across unrelated programs
- skipping from local object work to bridge claims
- using docs as authority when fresher result artifacts disagree
- counting broad reading as progress if queue or evidence state did not change

## What Counts As Real Progress

Real progress means at least one of these happened:

1. one vague object became an explicit normalized object with a clear row and probe target
2. one blocked object gained a real bounded execution path
3. one probe produced fresh evidence that changed the honest status label
4. one stale registry, backlog, or audit surface was corrected to match current evidence
5. one local lego became strong enough to feed one bounded successor
6. one invalid, inflated, or late-surface claim was fenced, downgraded, or rejected with evidence

If none of those happened, the run was probably documentation motion, not controller progress.

## What The Current Frontier Actually Is

The frontier is not "all theory in the repo."
The frontier is the set of next honest bounded moves where:

- the object is explicit enough to name
- the dependency chain is known enough to test
- the probe is bounded enough to run
- the expected evidence could change queue or truth state

In practice, the controller should prefer:

1. missing or weak local legos
2. stale truth-label or registry repairs
3. bounded pairwise or coexistence successors fed by already-real legos
4. only later, bridge or seam work

## What To Ignore Unless It Changes Queue Or Evidence State

An agent should mostly ignore material that does not change the live operational state.

Usually reference-only unless it changes queue or evidence state:

- broad theory prose
- old summary docs
- conceptual essays without explicit object extraction
- narrative comparisons with no probe consequence
- wiki growth that does not create or repair a registry row, queue item, or evidence-backed label

This does not mean the material is worthless.
It means it is not the current unit of control.

## Controller Selection Rule

When choosing the next task, the controller should ask:

1. what exact object can move one state forward now
2. what dependency blocks it
3. what smallest honest probe or maintenance action would resolve that blocker
4. what artifact would prove the move happened
5. what docs or ledgers must be updated if that artifact changes truth state

If the answer is still "read more," the object is probably not normalized enough yet.

## Operational Hierarchy

Use this order when deciding what is true:

1. fresh result artifacts and reruns
2. validator and audit outputs
3. machine ledgers and queue surfaces
4. execution docs and controller contracts
5. reference prose and theory docs

The higher layer may explain.
The lower layer decides.

## Bottom Line

The controller should behave like a state-transition manager for bounded research objects.

It should:

- extract explicit objects
- choose the next bounded move
- demand fresh evidence
- apply strict truth labels
- keep ledgers honest

It should not behave like a general reader, summarizer, or theory narrator unless that reading directly produces the next valid object transition.
