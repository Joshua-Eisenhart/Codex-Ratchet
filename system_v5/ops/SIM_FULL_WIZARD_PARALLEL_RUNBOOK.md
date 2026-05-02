# Sim Full Wizard Parallel Runbook

Status: active controller runbook for sim/proof/tool-stage work.

Purpose: prevent sim work from collapsing into a single-route or single-tool controller pass.

## Rule

Every sim/proof/tool-stage turn runs Full Wizard. For sims, Full Wizard means max-useful parallel packet work across independent tool/function surfaces, followed by serial controller synthesis and safe Git/runner handoff.

## Topology

Use this shape unless a concrete blocker forces a smaller pass:

```text
outer wave 1: preflight + tool/function registry scouts
outer wave 2: packet authors/auditors + child fanout
outer wave 3: council/checks + follow-up make/scout/audit
outer wave 4: controller synthesis + serial Git/queue/result handoff
```

The exact wave count is receipt-boundary count, not a quota. Prefer one broad lateral wave over many serial waits.

## Parallel-safe work

These can run concurrently when they touch separate files or return read-only receipts:

- tool/function surface scouting;
- micro packet proposals;
- proof fixture selection;
- tool-lego fit candidate audits;
- result-schema audits;
- follow-up Make/Scout/Audit options;
- voice/council/check routes;
- Claude/Gemini child reader/audit/scout jobs under Codex parents.

## Serial work

These stay single-controller:

- Python runner execution under the runner contract;
- shared queue file mutation;
- result JSON classification/ledger updates;
- Git index repair, staging, commit, and push;
- edits to the same file path.

## Parent/child expectation

For Full Wizard sim work, spawn Codex parent workers for route families. Parents should launch narrower child workers when the route has independent slices. A child can inspect one source slice, one tool row, one result schema, one falsifier, or one follow-up candidate.

If child fanout fails:

1. mark the child lane blocked or timed out;
2. reroute with a smaller child batch, different model, or shorter prompt;
3. do not call the run Full Wizard unless the child layer either completed or was explicitly blocked/deferred in the header.

## Default tool-stage fanout bank

Start from the current tool ledger and fan out across independent rows:

```text
z3
cvc5
sympy
clifford
geomstats
e3nn
rustworkx
XGI
TopoNetX
GUDHI
PyG
PyTorch/autograd
```

Each row should become one or more bounded triples:

```text
tool -> exact function/API surface -> tiny claim -> minimal fixture or useful lego target
```

## Acceptance

A sim-mode Wizard result is acceptable only if it preserves these distinctions:

- authored packet vs runner-executed result;
- queued row vs DONE row;
- result JSON vs ledger loopback;
- tool-function micro receipt vs tool-lego fit;
- tool-lego fit vs lego promotion;
- tool-tool coupling vs parallel imports.

## Follow-up format

Keep follow-up short and pasteable:

```text
Lanes
1. Direct - "Run the smallest sim check that moves this forward."
2. Alternative - "Try a second route and compare the tradeoff."
3. Reframe - "Restate the claim, unit, and pass/fail gate."
4. Wildcard - "Probe one off-axis idea; keep or retire it."
5. Back - "Return to the prior decision surface."

Compositions
6. All-A / Build - "Make the bounded move, falsify it, and name the check."
7. All-B / Divergence - "Keep live alternatives and test what excludes them."
8. All-C / Closeout - "Finish only after evidence, wording, hygiene, and security pass."
9. Full Wizard - "Run the full integrated route with honest blockers and receipts."
```
