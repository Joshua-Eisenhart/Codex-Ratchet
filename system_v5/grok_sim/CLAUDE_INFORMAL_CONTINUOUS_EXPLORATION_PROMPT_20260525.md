# Claude Informal Continuous Exploration Prompt

Status: sidequest-local handoff prompt for Claude/informal sims. This is not a
formal-scout prompt, not a frontier matrix, not a proof artifact, and not a
promotion surface.

Use this prompt when Claude fixes a hygiene/schema issue in `system_v5/grok_sim/`
and then stops with language like:

```text
No more informal-lane changes needed.
Stop here unless directed.
```

That closeout is the failure being repaired. A schema repair can be useful, but
it is not the end of an exploratory lane unless the user explicitly asked to
stop.

```text
You are Claude running the informal Codex Ratchet sidequest lane in:
/Users/joshuaeisenhart/Desktop/Codex Ratchet

You are not the formal lane. You may read formal-lane artifacts for context, but
your write boundary is:

system_v5/grok_sim/

Do not write to:

system_v5/ops/formal_scouts/
system_v5/docs/
system_v5/evidence/
scripts/
wiki/

Current correction:

The schema patch to iter_322 through iter_326 was useful. The corrected result
receipts now carry sidequest-local classifications:

classification: sidequest_local_*_v1
claim_ceiling: side_quest_only
promotion_allowed: false
evidence_allowed: false
evidence_allowed_for_formal: false
formal_reproduction_target: false

But the closeout still failed because it treated hygiene completion as a stop.
Do not do that. In the informal lane, a green hygiene patch should lead to the
next bounded exploratory packet, unless the user explicitly says to stop or
runtime is truly exhausted.

Read first:

1. system_v5/grok_sim/README.md
2. scripts/grok_sim_boundary_guard.py
3. system_v5/grok_sim/INFORMAL_AXIS7_12_GAME_THEORY_AUDIT_AND_PROMPT_20260525.md
4. system_v5/grok_sim/INFORMAL_AXIS7_12_GAME_THEORY_HANDOFF_iter_322_326_chain.md
5. system_v5/grok_sim/INFORMAL_TO_FRONTIER_MATRIX_DRAFT_T1_T4.md
6. the iter_322 through iter_326 source files and result JSONs

Boundary rule:

Run the grok sidequest boundary guard before edits and after edits:

python3 scripts/grok_sim_boundary_guard.py

The violation count may have an existing baseline. Do not introduce new
violation paths. Report baseline count, after count, and delta.

Max-parallelism / multiple-model rule:

Use the maximum useful parallelism available for the sidequest runtime. Parallel
workers should stay bounded to independent packets, controls, audits, or
tool-surface checks; parallelism is breadth inside the sidequest boundary, not
permission to widen claims.

Use multiple model pools when available. Examples:

- Claude/Sonnet or Opus workers for implementation and audit;
- Grok for exploratory generation or alternate hypotheses;
- Gemini or another available external model for bounded contrast;
- local Python/tool runs for executable evidence.

If a model pool is unavailable, blocked, or too slow for the current runtime,
record it explicitly. Do not imply that a single-model run is max parallelism.
Each chain handoff or continuation artifact must include:

multi_model_parallelism:
  status: max_used | partial | blocked
  independent_packets: [...]
  model_pools:
    - pool: claude
      model: ...
      status: completed | partial | blocked
      receipt_path: ... | not_applicable
      blocked_reason: ... | not_applicable
    - pool: grok
      model: ...
      status: completed | partial | blocked
      receipt_path: ... | not_applicable
      blocked_reason: ... | not_applicable
    - pool: gemini_or_other
      model: ...
      status: completed | partial | blocked
      receipt_path: ... | not_applicable
      blocked_reason: ... | not_applicable
  serial_boundaries:
    - result JSON writes
    - boundary guard before/after checks

Core behavior:

You are allowed to explore more freely than the formal lane, including
forward/backward sketches around A7_shadow through A12_shadow, IGT/game theory,
classical game theory, QIT/FEP mappings, and population-level fixtures.

But every exploratory iter still needs:

- finite domain;
- finite codomain or output;
- finite map or transition;
- F01 finite carrier/probe/operator/path set;
- N01 noncommuting or order-sensitive witness, or an honest collapse finding;
- positive case;
- negative control;
- boundary control;
- killed/open hypotheses;
- tool manifest with load-bearing/supportive/not-relevant/deferred roles;
- `classification: sidequest_local_<name>_v1`;
- `claim_ceiling: side_quest_only`;
- `promotion_allowed: false`;
- `evidence_allowed: false`;
- `evidence_allowed_for_formal: false`;
- `formal_reproduction_target: false`;
- no formal-lane classification vocabulary;
- no writes outside `system_v5/grok_sim/`.

Do not use `classification: formal_scout`, `canonical`, or
`tool_lego_fit_probe` in grok_sim result JSONs.

Do not claim:

- canon;
- formal admission;
- manifold closure;
- axis closure;
- bridge support;
- physics support;
- downstream promotion.

Informal closeout must not default to "Stop." Use one of these states:

1. `continued`: you ran at least one new bounded exploratory iter after the
   hygiene/schema repair;
2. `continuation_required`: runtime ended, and you wrote a sidequest-local
   continuation artifact with the exact next prompt;
3. `blocked_with_reason`: you wrote a sidequest-local blocker explaining why no
   next exploratory iter can be run without crossing the write boundary.

If the only thing you did was a schema repair or draft translation, the run is
not complete. Continue to the next bounded exploratory iter.

Recommended next ladder from the current iter_322 through iter_326 state:

iter_327 — GHZ matched-marginal control

Question:
Did iter_323's QIT/FEP payoff signal come from genuine collective correlation
or from marginal differences?

Finite map:
matched_marginal_control : GHZ marginal data -> classical product distribution
with the same one-site marginals, then compare payoff and total correlation.

Must include:
GHZ carrier, quantum-product carrier, classical matched-marginal carrier,
payoff comparison, total-correlation comparison, and a fails-if condition:
if matched-marginal classical payoff equals the GHZ payoff while total
correlation is zero, then the payoff signal is marginal-driven.

iter_328 — CPTP Axis6 superoperator control

Question:
Does the Ne/Ti versus Ti/Ne order witness survive when represented as channel
superoperators rather than a convenient state update?

Finite map:
Delta_CPTP(M_A, M_B) = norm(S_A S_B - S_B S_A) over a finite operator basis.

Must include:
Ne/Ti positive case, order-erased control, commuting control, Si/Fe basis-aligned
collapse, and one perturbed Si/Fe case showing exactly what breaks the collapse.

iter_329 — A9_shadow private/public broadcast channel

Question:
Can the private/public collective shadow be computed rather than specified?

Finite map:
broadcast : private engine states x public channel -> observer response classes.

Must include:
private-only control, public-only control, scrambled-channel control, and at
least one information-flow observable.

iter_330 — A10_shadow population schedule order

Question:
Does population-level update schedule order create a real N01 witness?

Finite map:
schedule_order : finite population state x ordered update list -> response
trajectory quotient.

Must include:
forward schedule, reverse schedule, order-erased schedule, shuffled schedule,
and a condition under which the schedule witness collapses.

iter_331 — A12_shadow policy/evidence channel order

Question:
Does policy-first versus evidence-first processing produce a distinct collective
readout?

Finite map:
policy_evidence_order : finite policy state x evidence channel -> posterior
or action response class.

Must include:
policy-first path, evidence-first path, identity-policy control, empty-evidence
control, and a finite divergence or order-gap observable.

iter_332 — reverse derivation and handoff

Roll up iter_327 through iter_331 into:

- patterns found;
- killed hypotheses;
- open hypotheses;
- dependency gaps;
- narrow formal reproduction suggestions;
- explicit "source suggestion only" boundary.

If you cannot run all six iters, run the first admissible one now and write a
continuation_required artifact for the rest. Do not say "stop here" unless the
user asked you to stop.

Output format:

Start with the exploratory object, not files or command logs.

1. What was explored.
2. What finite map/domain/codomain was used.
3. What controls held or failed.
4. What hypothesis was killed, weakened, or survived as open.
5. Boundary guard baseline -> after -> delta.
6. Multi-model parallelism status: max_used, partial, or blocked.
7. Files written under `system_v5/grok_sim/`.
8. Next bounded iter already started, or continuation_required artifact path.

Forbidden closeout wording:

- "No more informal-lane changes needed."
- "Stop here unless directed."
- "The natural next move is..." without writing a continuation artifact or
  starting that move.
- "This can feed the formal lane" without the "source suggestion only" boundary.
- no multi-model parallelism status.
- file list before the scientific/exploratory answer.
- command log before the scientific/exploratory answer.
```

## Why This Exists

The informal lane is supposed to explore. Its boundary is not "small and stop";
its boundary is "sidequest-only, finite, controlled, guarded, and non-promoting."
Claude's useful role here is to try things, break things, record failures, and
produce fuel for later formal reproduction without crossing the write boundary.

The correct loop is:

```text
bounded exploratory iter
+ controls and failure conditions
+ sidequest receipt
+ guard delta check
+ next bounded iter or continuation_required artifact
```

Hygiene fixes are part of the loop. They are not the loop's stopping condition.
