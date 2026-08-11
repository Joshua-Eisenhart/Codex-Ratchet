---
name: premortem-remediation
description: Use when a CB premortem has discovered structured failure concerns and a bounded repair loop may attempt eligible fixes; deterministic gates decide every Issue, RepairAction, and completion state, never a model, council, MMM, or prose judgment, and the loop never opens a WebUI, HTML report, or browser.
---

# Premortem Remediation (CB-native)

## Overview

A premortem discovers structured failure concerns. This skill runs a bounded
loop that may repair eligible ones: classify each concern into a gate-derived
Issue, solicit non-authoritative RepairCandidates from skills, MMMs, formal
agents, and model providers, let a deterministic rule promote at most one
candidate per Issue *per declared repair round* into a RepairAction, apply it
as an append-only event, rerun the declared aggregate completion predicate as
a GateRun, and settle into an immutable receipt. CB Light stays independent of
CB Heavy and simulation engines throughout; this skill never imports or
invokes Heavy/simulation machinery.

Only a deterministic gate decides. Models, MMMs, councils, and formal agents
may only produce candidate or evidence artifacts. Nothing they emit —
vote, verdict, confidence, consensus, or prose — can set an Issue's
disposition, promote a RepairAction, or declare completion.

## Hard prohibitions (check before anything else)

- No HTML report, no action that opens a browser, no renderer, no report UI,
  no dashboard. The only externally visible output is the typed receipt objects
  below, persisted as structured (JSON) records. A run_policy or producer
  that requests a rendered/report/browser output surface is REFUSE at Step 0,
  reason `PROHIBITED_OUTPUT_SURFACE`.
- No vote, verdict, confidence, or consensus field from any producer may set
  disposition on an Issue, authorize a RepairAction, or declare completion.
  Such a field arriving from anything other than a deterministic gate
  function is logged as an EvidenceArtifact only, never acted on as
  authority.
- No invented budgets or stopping condition. The policy must declare a
  deterministic, well-founded `measure_id` and `measure_domain`, its
  `terminal_value`, and `strict_per_retry_decrease=true`. Numeric iteration
  and time bounds may supplement this policy, never replace it. A run with no
  numeric bound is legal only with all four declarations; missing or
  insufficient declarations → **HOLD**, reason `NO_DECLARED_STOP_CRITERION`.
- Any max-iteration or max-time field is a safety bound only. Reaching it
  never counts as success; it can only route to HOLD or EXHAUSTED (Step 6).

## Structured handoff chain

One direction, append-only, each stage typed:

1. **ConcernRecord** — `concern_id, source, locator, description,
   discovered_at`. Raw structured output from premortem discovery.
2. **Issue** — `issue_id, concern_id, gate_id, disposition
   (OPEN|RESOLVED|DUPLICATE|OUT_OF_SCOPE|EVIDENCE_INSUFFICIENT), reason_code`.
   A deterministic classification gate appends its opening `IssueEvent`;
   later deterministic aggregate evidence appends a `ResolutionEvent`.
   Neither event mutates an earlier Issue record.
3. **ProducerBinding** — `(producer_id, issue_id), binding_state`, with
   append-only binding evidence. This many-to-many record, not a candidate
   field, moves through the binding ladder.
4. **RepairCandidate** — `candidate_id, issue_id, producer_type
   (skill|mmm|formal_agent|model_provider), producer_id, proposed_action,
   evidence_refs, produced_at`. Non-authoritative. No disposition or binding
   state field exists on this type.
5. **RepairAction** — `action_id, issue_id, candidate_id, round_index,
   action_type, scope_paths, diff_bound`. Deterministic promotion of at most
   one RepairCandidate per `(issue_id, round_index)`. An `ActionApplication`
   is a later append-only event; it never edits the RepairAction.
6. **GateRun** — `gate_run_id, action_id, round_index, aggregate_gate_id,
   aggregate_result (PASS|FAIL), required_gate_results, measure`. Every run
   carries the deterministic measure and fresh results for the aggregate and
   every required regression gate.
7. **Receipt/Settlement** — `receipt_id, run_id, terminal, supersedes,
   emitted_by_gate_id`, joining 1–6. It is immutable. Only a deterministic
   gate may emit or supersede a receipt; correction appends, never rewrites.

## Operational steps

### Step 0 — Preconditions

Validate in this precedence before ingesting anything:

1. A requested HTML report, action that opens a browser, renderer, report UI, or
   dashboard — or a vote/verdict treated as authority — is **REFUSE** first,
   reason `PROHIBITED_OUTPUT_SURFACE` or `NONDETERMINISTIC_AUTHORITY`. It
   does not become a lesser HOLD because another policy field is absent.
2. `run_policy.completion_gate` names an executable deterministic *aggregate*
   predicate (function/command, never a model or council), and explicitly
   enumerates `required_regression_gates` (an explicit empty list is allowed).
   Its deterministic definition is PASS only when its primary condition and
   every required regression gate PASS. Missing/non-deterministic completion
   gate → **HOLD**, `NO_DECLARED_COMPLETION_GATE`; missing aggregate binding
   → **HOLD**, `NO_DECLARED_REGRESSION_AGGREGATE`.
3. The stop policy declares `measure_id`, well-founded `measure_domain`,
   `terminal_value`, and `strict_per_retry_decrease=true`. Numeric
   `iteration_bound`/`time_bound`, if present, must be this run's own safety
   fields. With no numeric bound, all four measure declarations are required;
   absent or insufficient stop policy → **HOLD**,
   `NO_DECLARED_STOP_CRITERION`, never an invented EXHAUSTED outcome.

### Step 1 — Ingest ConcernRecords

Accept only structured concerns: each needs `concern_id`, `source`,
`locator`, `description`. A concern without a `locator` cannot be classified
→ **HOLD** for that concern, reason `CONCERN_NOT_STRUCTURED`. Prose-only
findings do not enter the loop.

### Step 2 — Classify into Issues

A deterministic classification gate maps each ConcernRecord to an Issue.

- `OUT_OF_SCOPE` or `EVIDENCE_INSUFFICIENT` → append an owner-routing record
  with terminal **PROPOSED_FOR_OWNER** for that concern. An unresolved
  owner-routing record is terminal for the whole run and blocks VERIFIED_DONE;
  it is routed to the owner, never auto-fixed or silently dropped.
- `DUPLICATE` → merged into the existing Issue; no new repair path opens.
- `OPEN` → proceeds to Step 3.

### Step 3 — Solicit RepairCandidates

Skills, MMMs, formal agents, and model providers may each produce a
RepairCandidate. Its matching `ProducerBinding(producer_id, issue_id)` moves
through exactly these states, in order: `declared` → `bound_reference` →
`invoked` → `receipt_verified`. A `declared` producer is named in `run_policy`
but not yet referenced. A `bound_reference` means an Issue references the
producer as eligible; it has not run. `invoked` means it ran and returned
output. `receipt_verified` means that output carries a checkable receipt
(hash, log, or deterministic replay) proving the invocation happened and
produced the claimed artifact. **A bound_reference is never an invocation.**

Validate:

- A transition that skips a state (e.g. `declared` straight to `invoked`) →
  **REFUSE**, reason `BINDING_STATE_SKIPPED`.
- A RepairCandidate is eligible for Step 4 only when its matching
  ProducerBinding is `receipt_verified`. Anything less stays parked as
  evidence.
- Any vote/verdict/confidence/consensus field on a candidate is stripped
  from the authoritative record and logged only as an EvidenceArtifact.

### Step 4 — Deterministic promotion to RepairAction

A deterministic admissibility rule, declared before the run starts, selects
at most one eligible RepairCandidate per `(issue_id, round_index)` — for example, "first
receipt_verified candidate whose diff stays inside `scope_paths` and
`diff_bound`." The rule is fixed in advance; it is never "the best
candidate" by any model's or council's judgment.

- Candidate's change falls outside `run_policy.scope` → terminal
  **PROPOSED_FOR_OWNER**, not silently rejected or narrowed.
- Candidate's diff exceeds the declared `diff_bound` → **HOLD**, reason
  `ACTION_EXCEEDS_BOUND`.
- The first action has explicitly declared `round_index=0`. A second action
  for the same Issue requires an explicitly declared next `round_index`, a
  fresh pre-action GateRun, and its measure strictly lower than the immediately
  preceding round's GateRun. Otherwise → **HOLD**,
  `SECOND_ACTION_WITHOUT_DECREASING_ROUND`.
- Otherwise append a pending RepairAction. It is applied only by appending an
  `ActionApplication` event with immutable input/output hashes.

### Step 5 — Apply and rerun (GateRun)

Apply the RepairAction by appending ActionApplication, then rerun the
aggregate completion predicate and every required regression gate against the
fresh current state. Record their results and the deterministic measure in a
GateRun.

- Every GateRun carries `measure`, computed from the declared well-founded
  domain. Before a retry, its fresh measure must strictly decrease from the
  preceding round; a non-decrease is **HOLD**, `NONDECREASING_RETRY_MEASURE`.
- Any required regression-gate FAIL makes the aggregate completion predicate
  FAIL, even if the primary condition passes. The deterministic
  `gate_failure_to_issue` mapping appends or retains an OPEN Issue for that
  failure; a regression FAIL can never be hidden by a primary PASS.
- Aggregate FAIL keeps the Issue OPEN and appends CandidateExclusion for the
  failed `candidate_id`; that candidate may not be promoted in a later round.
  Return to Step 3 only through the declared next round above.

### Step 6 — Completion check and terminals

Exactly one terminal ends the run, decided only by declared deterministic
gates:

- **VERIFIED_DONE** — the declared aggregate completion predicate PASSes on a
  fresh GateRun, every required regression gate PASSes, deterministic
  ResolutionEvents are appended for resolved Issues, no Issue remains OPEN,
  and no unresolved owner-routing record remains. This is the only terminal
  that means the run is done.
- **HOLD** — missing declared authority: no completion gate, ambiguous
  scope, an undeclared/insufficient stop criterion, a non-decreasing retry,
  or a binding-state gap. It also settles a terminal measure with a failing
  aggregate. Recoverable only by the owner supplying the missing declaration;
  the loop does not proceed on its own.
- **REFUSE** — a prohibited action or policy violation was attempted
  (report/WebUI output, a vote/verdict treated as authority, a scope
  violation, an invented budget). The loop stops; the violation is
  receipted.
- **EXHAUSTED** — a declared iteration/time safety bound was reached under a
  complete stop policy while its measure had not reached terminal value (for
  example, OPEN Issues > 0). Missing policy is HOLD, not EXHAUSTED; EXHAUSTED
  never claims success.
- **PROPOSED_FOR_OWNER** — a candidate or change would exceed this run's
  authority to decide (out-of-scope, or evidence-increasing beyond the
  declared claim ceiling). Routed to the owner for an explicit ruling.

No terminal other than VERIFIED_DONE means done. Every terminal is written
as an immutable receipt.

### Runtime profile boundary

This generic contract is for a sealed issue set and may govern multiple
Issues. The first runtime profile must declare and receipt `single_issue_run`;
its VERIFIED_DONE applies only to that sealed one-Issue run, never to project
or multi-Issue completion. A future multi-Issue controller must bind a
`sealed_issue_set` artifact before it uses this run-level terminal.

## Rationalization table

RED-baseline phrasing this contract refutes:

| RED baseline phrasing (exact) | Why it fails this contract | Counter-rule enforced here |
|---|---|---|
| "treat each prose finding as self-evident" | Prose is not a ConcernRecord; nothing is actionable until gate-classified | Step 1/2: unstructured concerns HOLD before classification; only gate-derived Issues proceed |
| "fix the first apparent symptom" | "Apparent" is a judgment call, not a declared rule | Step 4: the promotion rule is fixed before the run and applied uniformly, never chosen by apparentness |
| "rely on a targeted green test, and stop after a clean rerun" | A targeted test is not the declared completion gate; a clean rerun of the wrong gate proves nothing about done-ness | Step 6: VERIFIED_DONE requires the declared completion gate, not an arbitrary targeted test |
| "each council member returns ACCEPT, REJECT, or HOLD" | A verdict from any producer is non-authoritative by definition | Step 3: RepairCandidate carries no disposition field; verdicts are logged as EvidenceArtifact only |
| "a repair council authorizes one bounded implementation action" | Councils cannot authorize; only a deterministic gate promotes | Step 4: promotion is a deterministic admissibility rule, never a council decision |
| invented example budgets (20 iterations, 90 minutes) | No owner-supplied budget existed; the numbers were fabricated | Step 0: no numeric bound is acceptable only with the declared well-founded measure; absent or insufficient stop policy is HOLD, never a default |

## Scope of this document

This is a contract and design for a later runtime implementation. It does
not modify package source, configuration, receipts, or global skill
directories. Implementing code must use this file's vocabulary exactly:
ConcernRecord, Issue, ProducerBinding, RepairCandidate, RepairAction,
GateRun, Receipt/Settlement; terminals VERIFIED_DONE, HOLD, REFUSE,
EXHAUSTED, PROPOSED_FOR_OWNER; binding states declared, bound_reference,
invoked, receipt_verified.
