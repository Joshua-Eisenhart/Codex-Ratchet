# Sim Full Wizard Parallel Runbook

Status: active controller runbook for sim/proof/tool-stage work.

Purpose: prevent sim work from collapsing into a single-route or single-tool controller pass.

## Rule

Every sim/proof/tool-stage turn runs Full Wizard. For sims, Full Wizard means max-useful parallel packet work across independent tool/function surfaces, followed by serial controller synthesis and safe Git/runner handoff.

Sim Full Wizard uses a strict ratchet with wide search. Admission and promotion
are conservative, but candidate generation is deliberately broad: many
tool/function rows, lego targets, falsifiers, model variants, and child
subsubagents may be tried in parallel. Failed candidates are useful when they
record why they failed, what boundary they exposed, or what demotion condition
they proved. They support the ratchet without becoming admitted evidence.

Do not collapse this into one-at-a-time micro admission. The exploration surface
is all available micro-legos, legos, variants, negatives, and alternate tool
surfaces in mass batches. The controller should delineate each row as
classical, bridge, or nonclassical and record batch status for every row it can
see. The ratchet is conservative at the admission and promotion boundary, not
at the exploration boundary.

## Topology

Use this shape unless a concrete blocker forces a smaller pass:

```text
outer wave 1: preflight + tool/function registry scouts
outer wave 2: packet authors/auditors + child fanout
outer wave 3: council/checks + follow-up make/scout/audit
outer wave 4: controller synthesis + runner handoff with parallel workers only for independent admitted rows; Git, ledger, admission, and promotion remain serial
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

## Parallel runner work

Python runner execution is parallel when queue claims are atomic and rows have
distinct result paths, fixtures, logs, and ledger loopback surfaces. This is
the normal shape for mass micro-lego, lego, classical baseline, and
already-admitted independent coupling work. The runner pool may execute many
rows at once; each row remains row-local and cannot promote siblings.

Use the parallel queue-claim runner for this shape:

```text
make parallel-runner MINUTES=<n> LANE_A_PARALLEL=<k> LANE_B_PARALLEL=<k>
```

Use dry-run first when changing queue shape:

```text
make parallel-runner-dry MINUTES=1
```

## Serial work

These stay single-controller:

- shared queue file mutation where no atomic claim surface exists;
- result JSON classification, ledger updates, controller reconciliation, and promotion;
- Git index repair, staging, commit, and push;
- edits to the same file path.

## Parent/child expectation

For Full Wizard sim work, spawn Codex parent workers for route families. Parents should launch narrower child workers when the route has independent slices. A child can inspect one source slice, one tool row, one result schema, one falsifier, or one follow-up candidate.

If child fanout fails:

1. close or release every completed child/parent agent whose receipt has already been collected;
2. retry the missed child lane as a rolling batch at the observed capacity ceiling;
3. reroute with a smaller child batch, different model, or shorter prompt;
4. mark the child lane blocked or timed out only after cleanup plus retry fails;
5. do not call the run Full Wizard unless the child layer either completed or was explicitly blocked/deferred in the header.

`agent thread limit reached` is a liveness signal, not a terminal child blocker.
The controller must drain completed agents and retry smaller before accepting
capacity failure. A parent that returns after a thread-limit message without a
cleanup/retry ledger has failed its child rerouter obligation.

## Same-Triple Variant Fanout

Variant child/subsubagents may multiply only the same exact tool/function/claim/fixture triple.

Each variant must declare what differs:

- mini-MMM slice;
- model/runtime;
- task framing;
- assigned falsifier;
- source slice;
- audit angle.

Variants that differ only by label, prose, or worker count are redundancy, not breadth.

Variant agreement is not proof. A sim/QIT claim remains provisional unless normal executable evidence surfaces agree through runner/result/ledger reconciliation, or the variants produce useful falsifiers, boundary failures, or demotion conditions that improve the next admissible packet.

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
