---
name: sim-wizard
description: run a bounded three-engine sim build with the 4-lane codex2 council + fresh audit
when-to-use: any new sim or hardening batch
---

# Sim Wizard

Sim Wizard is the sim profile of the general Wizard: councils, auditors, and
managers instantiated for sims through bounded `codex2` effort lanes. It codifies
the end-to-end pattern proven on 2026-06-09 by
`foundation_nested_hopf_weyl_signed_cut_ratchet`.

Use this with `.claude/skills/three-engine-sim/SKILL.md`; do not duplicate its
engine roles, result contract, tool-depth rules, or deprecation roster.

## Phase 1: CARD
The overseer writes exactly one bounded build card before fan-out.

Required card fields:

- `object`: one finite object, named plainly.
- `claim`: one claim under test, not a bridge, axis, manifold, or canonical
  promotion unless that is exactly scoped and gate-backed.
- `controls`: positive, negative, and boundary controls that can fail.
- `PIN`: mandatory literal block copied into every engine leg; includes exact
  parameters, state family, cuts/observables, order convention, log base, and
  like-for-like scalar names.
- `files_to_create`: complete allowlist of repo files the builder may write.
- `persistence`: the card itself is COPIED INTO the packet as `build_card.md` —
  a packet without its card cannot prove which rules bound it (the basin-pilot
  lesson: the envelope-builder rule failed to bind because no card was persisted).
- `ceiling`: classification and promotion boundary, usually
  `scratch_diagnostic`, `promotion_allowed=false`,
  `formal_admission_allowed=false`.
- `envelope_builder`: builders construct envelopes via `scripts/build_three_engine_envelope.py` — hand-rolled envelopes are the known defect class.
- `TOOL_INTENT_MATRIX`: mandatory declared JSON block:
  `{"claim_classes":[],"engine_tool_intent":{"julia":{},"jax":{},"pytorch":{}}}`.
  Each engine/package entry names the exact observable or proof it carries.
  This matrix decides the engine mode: include PyTorch only for graph,
  network, autograd, equivariance, or existing torch claim paths; otherwise use
  the honest-omission mode and state the omitted lane in the envelope.

Fence salient claims explicitly. The card must say what the sim does not prove,
so no worker can skip to a top-floor bridge, Axis0, manifold, or canonical claim.

## Packet-Class Engine Routing

The `build_card.md` `TOOL_INTENT_MATRIX` routes packet class before any envelope
claims all-three execution. It is not blanket all-three doctrine; it is an
auditable mode decision. The envelope carries the same decision as `tool_intent`
when the stricter validator gate is intended.

| Packet class | Julia intent | JAX intent | PyTorch intent |
|---|---|---|---|
| basin / transition-graph packets | `Graphs` for finite graph witnesses; `Z3` for exact finite constraints; `Attractors` / `DynamicalSystems` only when a real basin/dynamics observable gates the claim | `vmap` for batched state sweeps; `jraph` or `networkx` for graph carriers; `z3` + `cvc5` for SMT pressure; `ott`, `gudhi`, or `toponetx` only when their distances/topology observables gate the claim | `torch_geometric` for graph tensors/message-passing readouts; `torch.func` for batched/autograd graph observables; omit honestly when there is no graph/network/autograd claim path |
| information packets | `QuantumOptics` for state/channel/entropy observables; `Z3` for finite proof pressure | `qutip` or `quimb` for independent state/tensor-network observables; `z3` + `cvc5` for SMT pressure; `ott` for transport/information geometry only when load-bearing | include only when `geomstats`, `e3nn`, `torch.func`, or `torch_geometric` carries a named information, geometry, equivariance, graph, or autograd observable |
| dynamic-manifold packets | `Manifolds`, `Attractors`, or `DynamicalSystems` for manifold/dynamics observables; `Z3` for exact side constraints | `diffrax` for ODE/SDE trajectory observables; `vmap` for batched families; `gudhi` / `toponetx` for topology observables; `z3` + `cvc5` for finite proof pressure | `geomstats` for manifold observables; `e3nn` for equivariance/irreps; `torch.func` for autograd/Jacobian observables; `torch_geometric` for graph-coupled dynamics |

Do not route `torch_ga`; it is deprecated in the committed roster. A load-bearing
package in the matrix must also appear in the lane's `package_observables` and,
when `--require-tool-intent` is used, pass source-token backing on the claim
path.

## Phase 2: FAN-OUT
Launch all lanes in background, file-disjoint, with no waiters. Use mass-parallel
`codex2` where available.

- `xhigh BUILDER`: executes the card. This is the only lane that writes repo
  source/result files, and only the card's `files_to_create`.
- `low PREFLIGHT`: fresh-runs reuse assets, verifies capability receipts, and
  writes a `/tmp` report.
- `medium BLIND-DERIVER`: independently computes expected values and sanity
  bounds, never reading the build, and writes a `/tmp` report.
- `high PRE-AUDITOR`: enumerates likely failure modes keyed to recorded repo
  history plus executable checks, and writes a `/tmp` report.

Each support lane is read-only on the repo. Each lane returns paths, commands,
values, and open failures; prose verdicts alone are not evidence.

## Phase 3: VERIFY
The overseer verifies mechanically. The builder's verdict is never evidence.

Run the repo validator personally, using the Makefile interpreter where relevant:

```bash
scripts/validate_three_engine_sim_result.py --require-pytorch <envelope_results.json>
```

Add `--require-source-backed` whenever the result path is intended to support a
source-backed claim.

Then compare the build numbers against the blind lane's expected values. Check
the PIN match, per-observable like-for-like divergence, control flips, boundary
case, and proof/tool receipts directly in source and JSON.

## Phase 4: FRESH AUDIT
Launch a separate `codex2` auditor that did not build the sim.

The auditor executes the pre-audit checklist against actual sources and results,
recomputes at least one value by hand or small independent script, and returns
one of:

- `GENUINE`
- `GENUINE-WITH-CAVEATS`
- `DECORATIVE`
- `BROKEN`

The verdict must name the single most important caveat when caveats survive.
Caveats are NAMED (G1, G2, …) so they can be tracked individually. The auditor
applies the calibrated bar in `system_v6/receipts/audit_bar_calibration_20260610.md`:
a blind-sheet method mismatch is a finding-to-reconcile, not a fail; strength
tokens are never verdict-bearing; two-CAS end-to-end is preferred, not required.

## Phase 5: HARDEN
Run one bounded hardening batch per named caveat.

Stability under hardening follows EXACTNESS-CLASS STABILITY (calibrated bar,
2026-06-10 — not blanket byte-stability): exact/symbolic/integer rows stay
byte-stable; rigorous-bound rows stay within certified bounds; diagnostic-float
rows may move with route improvements, and the movement is reported, not failed.
A numerical-bug caveat may of course change values — say so. Re-run sources,
envelope, validator, blind-value comparison, and fresh-audit checks after each
batch. Hardening is FULL RERUNS of the legs, never in-place result-JSON edits.

Bound the loop: at most two hardening rounds per named caveat; a caveat still
open after two rounds is carried explicitly in the ceiling and surfaced to the
owner, not silently retried. Closed caveats are restated by name in the re-audit
addendum ("G1, G2 closed; G4, G5 remain open"); a commit message may claim
closure only for the caveats the addendum names.

**Caveat carry-forward (ladder rule):** when a packet is a rung of a ladder
(lifted n=3 → n=4 → …), every caveat left open at rung n becomes a NAMED check
in rung n+1's build card and fresh-audit card. Open caveats never silently
disappear between rungs.

Commit sim sources, result JSONs, and audit verdict together. Do not split the
evidence from the code that produced it.

## Rules To Cite

When writing cards, lanes, reviews, or commit notes, cite the relevant rule from
`.claude/skills/three-engine-sim/SKILL.md` instead of restating it:

- capability-probe: `load_bearing` requires a real function/API call that gates
  a control, quotient, proof, divergence, or demotion condition.
- like-for-like divergence: compare the same named observable across engines,
  never a `max_divergence` over incommensurable quantities.
- evidence ladder: Julia canon first, then exact/symbolic checks, then
  `z3`+`cvc5`, then cross-engine smoke; numeric agreement is not promotion.
- deprecation roster: deprecated or out-of-system tools stay out unless a fresh
  capability probe and owner sign-off restore them.
- anti-self-match: never `ps`-hunt for "duplicate lanes" from inside the lane;
  you will see your own process tree. Use explicit receipt paths and job ids.
- quota: `codex2` lanes do the work; the overseer stays thin and verifies.
- absence-claim rule: never write "missing / needs foundations" without
  grep-quoted failed searches against the reference dirs and the lane's own
  cited sources; distinguish "math not on file" from "receipt not built".
- audit bar: cite `system_v6/receipts/audit_bar_calibration_20260610.md` for
  stability/blind-mismatch/two-CAS questions instead of improvising a stricter
  local rule — over-strict rules cost real cycles (the 4Q token rebuild).

## The work loop (launch → notify → verify → audit → harden → commit)

The standing controller loop, one packet at a time per lane, lanes file-disjoint:

1. Launch the codex2 lane with `run_in_background:true` (the REAL job, never a
   waiter shell that polls for it).
2. Assert lane state ONLY from harness notifications / task output / result
   JSONs — never from `ps`/`pgrep`/mtimes.
3. On the builder's return: run the validator yourself, compare blind values,
   then launch the FRESH audit (separate codex2, did not build it).
4. On the audit's return: REJECT → one bounded v2 rebuild (new card naming each
   defect); caveats → Phase 5 hardening (≤2 rounds per caveat); accepted →
   atomic commit (named-path `git add` of exactly that packet).
5. A packet with caveats blocks only the claims that depend on those caveats —
   file-disjoint audits, family variants, and foundation-breadth probes continue
   in parallel. Closeout (git) is the only serial point.

### Wizard council integration (owner directive 2026-06-11: "use more of the wizard's tools to help run the sims")

Wizard control functions fire at NAMED loop steps — each is load-bearing at its step, not decorative (the anti-decorative rule binds). These are route functions, not a promise that a `~/.claude/agents/wizard/` directory exists. Default them to codex lanes carrying the same brief + MMM head; when a Claude escalation trigger fires, use the actual top-level `.claude/agents/voice-*` agents and `council-collapse-auditor`.

| Loop step | Wizard tool | What it must affect |
|---|---|---|
| Before a flagship/integration build card | `premortem-agent` | failure modes already visible → card hardening lines |
| On any headline claim (saturation, uniqueness, SURVIVES) | `falsifier-agent` | the strongest falsifier named + checked before the commit message claims it |
| At packet acceptance (pre-commit) | `route-truth-agent` + `scripts/wizard_loop_state.py` | LOOP_STATE divergences (the mechanical script first; the agent for semantic claims) |
| At wave close | `evidence-mapper` | every wave claim mapped to its commit/receipt; unsupported claims demoted before memory distillation |
| When >3 lanes are queued | `route-sequencer` | dependency order; prevents bottleneck stacking; `changed_loop_state=false` is allowed when it affects route ordering or downstream inputs |
| At wave boundaries | `prompt-packetizer` | the next-wave PROMPT_PACKET from verified state (supersedes stale external packets) |
| For read-only pre-scout questions | `scout-runner` | findings without interpretation, feeding cards; `changed_loop_state=false` is allowed when the output affects card lines or downstream inputs |
| When council receipts pile up | `selector-compiler` | the ranked action list; preserves disagreements |
| Any scope question | `scope-keeper` | drift >1 level from the stated frontier → stop signal |

**MMM rule for wizard agents:** every agent invocation carries a mini-MMM head.
Salience is role-scoped:
- The main Fable/controller thread reads the full Wizard MMM when budget permits; otherwise it reads compact MMM + the complete relevant mini-MMM set before routing, judging, or synthesizing.
- Parent/council/lane-controller routes may carry sets: compact MMM + route mini-MMM + voice/lane/check/task mini-MMMs.
- Subagents/subsubagents do not read the global full MMM by default. They read compact shared salience when needed plus exact route/member mini-MMM set(s) and the task/source slice.
- Receipts must prove the set with `slices_loaded` / loaded mini-MMM paths. Fallback-only or path-naming-only receipts are receipt-candidates at reduced weight.

Use this concrete template:

```text
# Harness
Repo rule: finite probe-family/admissibility/quotient discipline. Agent/worker output is receipt_candidate until controller verifies git/files/results. No git add, commit, push, or shared-state mutation. Banned claim verbs unless directly earned by cited checks: prove, proves, canonical, admitted, unique, complete, closed, final, manifold, bridge, axis-level, physics, solved, verified.

# Frontier
{one-line LOOP_STATE frontier}

# Claim Under Test
Claim: {one exact sentence}
Ceiling before this pass: {exists | runs | passes_local | canonical | scratch_diagnostic | GENUINE-WITH-CAVEATS | etc.}
Promotion boundary: {promotion_allowed=false/formal_admission_allowed=false or exact gate}

# Evidence Pointers
Source/result/audit paths: {paths}
Current receipt/check command: {command or none}
Named falsifier/control: {strongest falsifier or control that can fail}

# Bar
Use the calibrated audit bar: {path, e.g. system_v6/receipts/audit_bar_calibration_20260610.md}. Distinguish mechanical file truth from semantic claim truth.

# Runtime Choice
Default runtime: codex lane. Use Claude-fresh-context only if same-family-blindness, semantic/factual split, owner-request, or high-stakes headline promotion trigger is present.
```

Highest-salience first and last; label each block; prune stale blocks per loop
(the MMM-as-testable-salience rules in `claude-wizard-loop-engineering`). An
agent receipt that arrives without having loaded its MMM head is
`receipt_candidate` at reduced weight.

Quota note (TIGHTENED, owner 2026-06-11 "too much fable"): wizard agents are
Claude-quota. DEFAULT every control function to a codex lane carrying the same
brief + MMM head. A codex-default control lane uses the same agent brief/output
schema and MMM head; it is accepted as the routine control receipt. Claude-side
agent invocation is reserved for the trigger conditions below. Invoke the
Claude-side wizard agent ONLY when (a) the owner asks, or (b)
fresh-Claude-context is specifically the point (e.g. checking a claim every
codex audit institutionalized — the one case where same-family review keeps
failing). The two live validations (route-truth, falsifier) are done; routine
loop steps run on codex. Fable = cards, 1-command verifies, commits, terse
replies.

### Claude-fresh-context triggers

1. Same-family institutionalization: two or more codex audits, codex workers, or repo status surfaces repeat the same headline, phrase, or inferred premise without an independent falsifier.
2. Headline-to-commit risk: a commit message, closeout, status receipt, or memory distillation would promote a claim containing `SURVIVES`, `unique`, `saturation`, `complete`, `canonical`, `killed`, `closed`, or equivalent strong language.
3. Circularity smell: the support path cites the same computation, same formula family, same control family, or same target-derived constants as both evidence and validator.
4. Semantic/factual split: `wizard_loop_state.py` can verify the files exist or the lane stage, but the disputed issue is whether the claim means more than those files prove.
5. Repeated no-delta review: the same codex lane family has produced two reviews without changing claim ceiling, caveat list, or falsifier set.
6. Owner pushback or high-stakes gate: the owner questions route truth or a gate decision would advance/build/commit/promote.

Anti-trigger:

- Do not use Claude just because a loop step names a wizard agent. If the check is local, deterministic, and not same-family-blind, run codex/default tools and record the receipt.

### Fleet roster + resource doctrine (owner, 2026-06-11)

**The fleet (binding):**
- **Fable (Claude, THIS terminal)** = sparse strategist + closeout hand. Best-from-least: cards,
  1-command verifies, atomic commits, terse synthesis, and Claude-side agents ONLY on the six
  escalation triggers. Everything else delegates.
- **codex1 + codex2** = the build/audit workhorses, ALL effort levels (low→xhigh), cross-backend
  pairing for fresh-context audits. Token-budgeted but the primary spend.
- **grok** = `grok-4.3` (blind panels, advisory alt-views, temperature 0) AND `grok-build`
  (a validated BUILDER backend — usable for build lanes when codex backends are saturated).
- **gemini = TUI ONLY** (`gemini -m auto-gemini-3 -p "<prompt>"`) — do NOT use the API route.
- **Local sims = zero tokens.** Julia/Python/JAX/torch runs cost only compute — run them freely,
  SUBJECT TO the resource guard below.

**Resource guard (local compute is free, the machine is not):**
- Before launching a heavy local lane (dense d>=64 carriers, MPS sweeps, long ODE integrations),
  read `loop_state`'s `system_load` block (load average vs core count, memory pressure).
- Caps: keep 1-minute load average below ~core count; at most 2 concurrent HEAVY local sims
  (a codex lane that runs Julia/JAX inside counts as one); stagger launches rather than bursting.
- If load is high: queue, don't launch. Long-running local sims get `nice`d. A lane that will run
  >30 min wall-clock says so in its card so the controller schedules around it.

### Long-horizon campaigns (owner: "longer running goals and workflows with effective loops")

A CAMPAIGN = a goal that outlives single waves/sessions. Mechanics:
1. **Campaign state file** (`/tmp/cr_campaign_<name>.json` during a session; distilled to memory
   at boundaries): the LOOP_STATE shape w/ `horizon.original_goal`, `current_claim_under_test`,
   `open_branches`, `blocked_on`, the standing queue.
2. **Every wave starts mechanical:** `wizard_loop_state.py --prior-state <campaign file>
   --original-goal "<goal>"` — the loop_health block then computes no_delta / same_blocker /
   scope_drift / verification_fail MECHANICALLY against the prior wave. A fired stop signal
   surfaces to the owner before the wave launches.
3. **Every wave ends with three steps in one turn:** evidence-map the wave's claims (codex lane),
   distill memory, write the next PROMPT_PACKET from VERIFIED state (never from a stale external
   packet — the receipt_candidate rule).
4. **Saliency per lane:** every worker card carries the mini-MMM head (harness line, frontier
   line, claim-under-test + strongest falsifier, key paths, bar pointer) — highest-salience
   first and last; stale blocks pruned each wave.
5. **The campaign closes** when its original_goal's claims are all mapped to commits (or
   explicitly retired) — not when a wave happens to end.


### The knowledge stack: wiki research vs MMMs (owner, 2026-06-11)

Three tiers, hard boundaries:

1. **The wiki research corpus** (deep, broad, polluted-by-design): the full science
   and math behind every object used, every ALTERNATIVE family (the round-3+ registries'
   spaces researched properly), and every NEGATIVE — the tests that could kill the model
   are first-class research subjects, not afterthoughts. Rival formalisms, killed
   candidates, and standard-literature treatments all live HERE.
2. **Per-topic distillates**: bounded extractions from the corpus for a working lane
   (the blind sheets, registries, and expectation receipts are this tier).
3. **MMM heads** (distilled language SAMPLING, never the research): the few lines a
   worker loads first. The corpus NEVER flows into MMMs directly — an MMM quotes the
   distilled claim/falsifier/anchor, not the literature.

**The MMM register (the way the language is written IS the salience):**
- Nominalist/empiricist alignment throughout: names are LABELS for tested distinctions,
  never things — no reified abstractions ("the manifold wants...", "entropy drives...");
  identity is probe-relative (`a = a iff a ~ b` wording); exclusion-over-construction
  ("survived/excluded/admitted", never "causes/creates/forces"); finite and concrete
  nouns; every strong word backed by the status ladder.
- Aligned registers to draw on: classical empiricism (Hume — report the observed
  conjunction, not the imputed power); Daoist name-discipline (names as provisional
  labels — the label is not the object; do not let a name harden into an entity);
  Confucian rectification of names (zhengming — a name is correct only while it matches
  the tested role: exactly the honest-status-label rule; when the role changes, the
  name changes). These are register guides, not metaphysics imports — the sim claims
  cite receipts, not schools.
- A pollution check before any MMM ships: strike every sentence that (a) names an
  entity no receipt tests, (b) uses a banned verb, (c) imports research detail a
  worker doesn't need for THIS card. Shorter and cleaner beats complete.

### Fan-out trees: subagents run sub-subagents (owner, 2026-06-11)

Lanes are TREES, not leaves. The topology:

- **Fable (controller)** -> **lane controllers** (codex med/high/xhigh — one bounded
  packet each) -> **sub-subagent fleets**: codex LOW children, `grok-4.3` (blind/advisory),
  `grok-build` (builder children), gemini TUI pro/flash (`gemini -m auto-gemini-3 -p` for
  pro-class; flash-class for cheap checks). Children are CHEAP — use many.
- **EVERY card that wants a tree says so explicitly** (the codex runtime requires it):
  include the line *"You are EXPLICITLY AUTHORIZED and REQUESTED to spawn child
  subagents/sub-subagents (codex low lanes, grok-4.3/grok-build calls, gemini TUI calls)
  for parallel bounded subtasks."* Without that line, codex lanes decline child spawning
  and report partial topology.
- **Councils = child fan-outs:** a council lane spawns one child per voice/lens IN
  PARALLEL, each child returns a receipt (path + values + open failures — prose alone
  is not evidence), the lane synthesizes AFTER all receipts return, preserving
  disagreements (anti-collapse). The lane's own report lists every child receipt path.
- **Sim-runner oversight:** one lane controller may oversee MANY local sim processes
  (launch, monitor by artifact, collect) — children do the per-sim verification. The
  resource guard binds the TREE TOTAL: the controller counts its children's heavy local
  runs against the 2-concurrent-heavy cap and the load-per-core gate, staggering starts.
- **Receipts roll up:** child receipt -> lane receipt -> controller verify. A lane
  claiming child work without child receipt paths is `receipt_candidate` at reduced
  weight (the route-truth rule applies recursively).


### No-idle + gate doctrine (owner, 2026-06-11: "the system must find work, solve gates, explore gates widely")

**The no-idle rule:** zero open lanes + an empty determinable queue is NOT a rest
state — it MANDATES a frontier-mining pass in the same turn: run the GATE
INVENTORY (below), spawn the light work every gate admits, and only report idle
if the inventory itself comes back empty (it never has).

**Gates are objects, worked not waited on.** Every gate gets: a NAME, its
OPENING CONDITION, and the light work that ADVANCES it while closed:
- the LOAD gate (heavy local sims) — advanced by: staging cards, corpora,
  pre-registrations, policies; checked mechanically (system_load).
- EVIDENCE gates (a claim needs prerequisite results) — advanced by: building
  the prerequisites, mining the estate, researching the negatives.
- OWNER gates (direction/promotion decisions) — advanced by: preparing the
  decision surface (the receipts, forks, and honest options) so the decision
  costs the owner minutes, never by pre-empting it.
- MATH gates (something unproven blocks a step) — advanced by: corpus research,
  blind derivations, symbolic pilots at light cost.
Gate-window work menu (merged from the Hermes tune-up): alternative-space research,
negative/control design, card hardening, blind expectation sheets, route-truth checks,
validator/schema repairs, queue ordering, distillates, source/witness mining.

**Explore gates WIDELY:** breadth at the gate, not downstream of it — many
independent probes of what would open a gate beat one deep bet (the committed
broad-at-the-gate pattern).

**Strong gates, constraint-bound (the root grounding):** every gate criterion
is expressed in the harness's terms — probe family + admissibility + quotient;
exclusion language (a gate opens when alternatives are EXCLUDED or survivors
ADMITTED, never when "the true X is found"). The metaphysical floor is the
owner's: anti-platonic monist nominalism w/ entropic monism — ONE substrate,
names as labels for tested distinctions, NO gate may quantify over platonic
objects ("the correct manifold exists" is banned gate language; "this candidate
survives the active constraint set C under probe family M" is the form).
Entropy rows in gate criteria are READOUTS of constraint structure, never the
primitive. A gate whose criterion cannot cite its constraint grounding is a
WEAK gate — flag it for repair before relying on it.

### Lane saturation (owner directive 2026-06-10: "more active management and respawning")

Target: **4–6 concurrent lanes** whenever a frontier exists; never let the
pipeline drain below 2 while determinable next packets are known. The respawn
rule is part of EVERY landing: when a lane's verify→audit→commit chain closes,
the SAME turn that commits it launches replacement lane(s) from the standing
queue — committing without respawning is an incomplete closeout. Maintain the
standing queue explicitly (next rungs, trailing extensions, caveat packets,
mode sweeps, pre-registration panels, depth extensions); when the queue runs
dry, that itself is the signal for a frontier-mining pass, not for idling.
Wave boundaries are for memory distillation, not for stopping: distill, then
relaunch in the same turn.

## Fable budget + roster (loop doctrine, audited 2026-06-10)

Roster (binding; corrects the Hermes loop draft on two points):
- **Fable (Claude)** = sparse strategist + gate arbiter + the ONLY closeout hand.
  Workers never `git add`/`commit` — Fable runs the 1-command verify and the
  named-path atomic commit per packet. That per-packet touch is O(one command),
  not a strategy call; "Fable stays out of the inner loop" applies to STRATEGY,
  not to closeout, which is non-delegable (verification-discipline kernel).
- **codex2 (all effort levels)** = the build/audit/harden workhorse. NOT Sonnet/
  Claude agents — Claude agent fleets are off-roster (quota rule).
- **grok / gemini APIs** = blind pre-registration panels and advisory
  cross-checks (temperature 0, no repo values in prompt, divergences
  adjudicated by hand derivation) — never builders, never authorities.
- **Hermes** = external controller whose audits are inputs to verify, not
  truth labels; Hermes does not own commits or acceptance.

Budget rule (confirmed empirically): one Fable strategy decision should govern
~5–20 workhorse actions. Fable strategy calls fire at: wave start, hard
blockers, conflicting audits, gate-advance decisions, end-of-wave memory
distillation — not per worker run.

Verdict vocabulary: keep the practiced repo set (GENUINE / GENUINE-WITH-CAVEATS
/ DECORATIVE / REJECT AS CLAIMED / BROKEN / EARNED / PARTIAL PASS + named
G-caveats). Do not introduce a parallel vocabulary; two vocabularies create
mapping bugs.

Proven loop mechanics the draft lacked (keep these):
- **Trail-by-one-rung**: dedicated caveat packets read only COMMITTED exports
  (hash-bound), so closures never depend on uncommitted evidence.
- **Focused re-audit for extensions**: narrow scope, prior verdicts stand,
  anti-relabeling check = diff the encodings across rungs (structural scaling
  proves derivation).
- **Caveat carry-forward**: open caveats become named checks in the next
  rung's build AND audit cards; closure language in commits names exactly the
  caveats the addendum names.
- **Blind pre-registration**: derive expected values (cross-model panels or
  /tmp blind sheets) BEFORE a lane lands; the lane's result is then a
  pre-registered hit or a real discrepancy, never a post-hoc match.

## Closure Standard

A sim-wizard run is complete only when the build artifacts exist, the validator
passes with named flags, blind expected values match or explain the deltas, the
fresh auditor returns an accepted verdict, and all surviving caveats are either
hardened or explicitly carried in the result ceiling.

## Builder/auditor file boundary (BINDING, 2026-06-11)

The file `audit_verdict.md` is written ONLY by the fresh cross-backend auditor lane. A builder
lane NEVER creates or edits it — a builder-written verdict is self-grading (never evidence) and
spoofs the mechanical stage detection (`audited_awaiting_closeout` keys on that file's existence).
If a builder produces self-assessment prose, it goes in `builder_self_assessment.md`. Every build
card should state this; the controller strikes violations on sight (rename + provenance warning),
as first enforced on round3_s6s7_heavy_discriminator_v0.
Packet validators check the build-time envelope boundary field, not current absence of
`audit_verdict.md`; after a fresh audit writes that file, validators must require an
independent/fresh-audit header instead of failing on existence alone.
