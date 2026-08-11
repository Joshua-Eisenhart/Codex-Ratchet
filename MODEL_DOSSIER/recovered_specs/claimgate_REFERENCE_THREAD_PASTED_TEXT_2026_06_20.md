Yes — now we have the actual X content, and this materially changes the architecture.

I’ll be precise:

The X thread is now processed from the pasted source text.
The oh-my-openagent v4.12.0 release has now been processed from the GitHub release page.
The YouTube video still has not been processed beyond title/page metadata, because I could not access a transcript or video content through the available tool. I can only verify the title/page exists as “Every Level of Marketing ($0, $10k, $100k, $1m, $10m).”

The X thread plus oh-my-openagent make the missing architecture much clearer.

The real architecture is not “a swarm”

The X thread’s key lesson is:

A swarm gives speed. A loop gives trust.

The thread explicitly says the raw swarm is not the finish line. The finish line is a loop where one system plans/checks, another swarm executes, failed outputs get rejected, rejected tasks are requeued with reasons, and the loop stops only when the verifier has nothing left to reject.

That maps almost exactly to your hard-wall model:

SOFT SIDE:
  councils / swarms / Wizard / ScenarioFan / Kimi-style workers
  generate candidates, attacks, variants, checks, reports

HARD SIDE:
  live source / CI / oracle / test / rerun / hash / object binding
  verifies whether each claim traces to a real source

LOOP:
  failed items re-enter the swarm with rejection reason
  stop only when hard gate has zero rejects

The key sentence from the pasted X thread is functionally:

The loop only stops when nothing fails.

That is the correct exit condition.

Not:

the councils agree
the swarm converges
the model is confident
the report sounds good
the blind judge likes it

Only:

all claims survive the named oracle
What this changes

The previous ClaimGate builds were too GitHub-PR shaped. They were useful, but the bigger product is:

Oracle-Gated Work Loops

ClaimGate is one surface of that. GitHub PRs are the first market wedge. But the deeper product is:

bounded task
→ mass branch exploration
→ hard oracle verification
→ failure requeue
→ receipt
→ stop when clean

This applies to:

code
research
marketing
finance reports
product decisions
docs
agents
sim/proof runs

So the next architecture should not be “ClaimGate plus some tools.” It should be:

Project Harness Engineering

Where the harness composes:

prompt engineering
+ context engineering
+ loop engineering
+ gate engineering
+ oracle binding
+ graveyard learning

That phrase is strong. It names the new category better than “agent orchestration.”

The X thread decomposed

The thread has these primitives:

1. Planner/verifier split

In the X thread, Opus plans the work and verifies it. Kimi swarm executes.

Product translation:

Wizard Controller:
  plans branch topology
  writes WorkCards
  defines oracle checklist
  verifies branch outputs

Team/Swarm Workers:
  execute branches
  produce artifacts
  cannot promote
2. Per-item checklist

The pasted prompt includes a per-company checklist:

revenue + margin pulled from live feed
source URL attached and resolvable
figure matches source within tolerance
no field left empty

This is the real WorkCard upgrade.

Every WorkCard must contain:

oracle:
  type: live_source | ci | local_rerun | proof | human_review
  fields:
    - name: revenue
      source_required: true
      tolerance: ...
    - name: margin
      source_required: true
      tolerance: ...
  reject_if:
    - source_unresolved
    - value_mismatch
    - empty_required_field

The checklist is not a prompt detail. It is the gate contract.

3. Live source verification

The X thread’s example only works because the numbers are verified against live feeds.

That means v16’s evidence manifest gate was directionally right, but still not enough. The next system needs field-level oracle verification:

claim says revenue = X
source URL resolves
source value = Y
abs(X - Y) <= tolerance

For code:

claim says tests pass
GitHub check run exists
check conclusion = success
head_sha matches PR head
artifact hash matches receipt

For proofs/sims:

claim says UNSAT
z3/cvc5 actually ran
output says UNSAT
log hash exists
engine version recorded
4. Requeue with rejection reason

The X thread’s rejected examples are not just failures; they are structured next work:

{
  "company": "co_041",
  "reason": "revenue != source"
}

This should be the universal graveyard object:

{
  "branch_id": "b-041",
  "claim_id": "revenue",
  "reject_reason": "value_mismatch",
  "oracle": "yahoo_finance",
  "expected": "...",
  "observed": "...",
  "next_constraint": "re-run branch with revenue pulled from source URL and value tolerance checked"
}

The failure is not a tombstone. It is the next branch prompt.

5. Stop when no rejects remain

This is the core loop controller:

while rejects > 0 and budget remains:
  requeue rejected branches with rejection reasons
  run swarm
  verify against oracle
stop when rejects == 0

This is the missing product engine.

The loop should show the same kind of progression as the X thread:

Pass 1: checked 100, rejected 12
Pass 2: checked 12, rejected 3
Pass 3: checked 3, rejected 0

That should become a UI primitive.

What oh-my-openagent contributes

The oh-my-openagent v4.12.0 release contributes the durable team substrate. It says TeamMode creates named groups of durable Codex threads under the current leader session, records teams in .omo/teams, assigns each member an ownership area or perspective, and keeps artifacts on disk for inspection, resume, archive, and deletion. It also says the controller owns team.json, guide.md, member bindings, status updates, artifacts, optional worktree paths, and cleanup.

That is important because your Wizard councils should not be ephemeral prompts. They should become durable team runs:

.cdo/teams/<team-id>/
  team.json
  guide.md
  members/
  status/
  artifacts/
  branches/
  collapse/
  cleanup.json

The release also says TeamMode guardrails reject weak or unsafe composition: single-member teams, duplicate member focus after trimming, spawn_agent substitutes, symlink writes into team guides, symlink delete escapes, unresolved state paths, and members are instructed to communicate with small frequent status updates.

Those become immediate ClaimGate/Wizard guardrails:

no single-member council
no duplicate focus
no fake spawned substitutes
no symlink writes into team guides
no unresolved state paths
status updates required
artifacts required

This is not fluff. This is how nested councils become auditable.

The real hybrid

Your Wizard councils plus oh-my-openagent plus the X loop becomes:

Durable TeamMode
  gives persistent council state

Wizard
  generates prompts, roles, next packets, collapse audits

ScenarioFan
  generates divergent attack branches

Blind Eval
  scores/tightens, cannot promote

Hard Gate
  verifies against named oracle

Graveyard
  stores rejects as next constraints

Loop Controller
  requeues failures until oracle clean

That is the actual product architecture.

What we missed before
1. The oracle is not optional

Previous versions had evidence manifests, but not enough field-level oracle checks.

The X thread’s system only works because every number traces to a live source. So every WorkCard must now name the oracle before running.

If no oracle exists, the system must do one of two things:

narrow the claim
or escalate to human

No strict loop without an oracle.

2. The fan is not just “more agents”

The X thread explicitly says more agents alone creates more confident garbage.

So the product must never sell “300 agents.”

Sell:

branching + rejection + requeue + oracle-clean exit

The fan only matters because the hard gate prunes it.

3. Team state must be durable

oh-my-openagent TeamMode shows the right product primitive: teams need team.json, guide.md, member bindings, status, artifacts, and cleanup. A council without durable state is just a prompt pile.

4. Failures are the product memory

The X loop’s rejected tasks are exactly the data that makes the next run better.

So Graveyard must be promoted from side feature to core loop memory.

reject reason
→ next constraint
→ requeue branch
→ saved pattern
→ future gate proposal
5. Marketing harness should be metric-oracle loop, not “content UI”

The marketing video still needs transcript processing. But even from the X thread, the marketing application becomes clear:

creative variants
→ live metric feed
→ reject weak variants
→ requeue with rejection reason
→ stop/scale when metric gate clean

For marketing, the oracle is not CI. It is:

CTR
conversion rate
watch retention
CAC
ROAS
revenue
qualified leads

The same loop works.

Upgrade architecture
New core object: OracleCard

WorkCard is incomplete without OracleCard.

workcard:
  id: research-ev-market-100
  goal: "Research 100 EV companies"
  scope:
    items: 100
  oracle_card:
    required_fields:
      - revenue
      - margin
      - source_url
    sources:
      - yahoo_finance
      - stock_market_feed
      - world_bank
      - imf
    checks:
      - source_resolves
      - value_matches_source_within_tolerance
      - no_required_field_empty
    exit_condition:
      rejects_count: 0
    budget:
      max_passes: 5
      max_branches: 300

For code:

oracle_card:
  sources:
    - git_diff
    - github_check_runs
    - local_rerun
    - artifact_hashes
  checks:
    - changed_files_match_envelope
    - required_checks_successful
    - required_artifacts_exist
    - rerun_commands_exit_zero
    - evidence_refs_bound_to_manifest
New package: packages/claimgate-oracle

Responsibilities:

resolve oracle source
fetch source value
compare claim value to source value
apply tolerance
emit oracle observation

Adapters:

github_check_run
github_diff
local_command
url_resolves
json_feed
csv_feed
manual_artifact
human_review
New package: packages/claimgate-wizard-loop

Responsibilities:

build nested council topology
generate prompt packets
run member branches
collapse branch outputs
requeue rejects
stop on oracle clean
New package: packages/claimgate-branch-ledger

Responsibilities:

branch_id
generation
input packet
output artifact
oracle result
reject reason
requeue status
final admission
UI upgrade

The UI should stop looking like a dashboard of modules and become a loop console.

Top-level screen:

Run: EV Market Research
Status: Pass 3 / Clean
Exit: zero rejects
Oracle: live finance feeds
Branches: 100
Rejected: 12 → 3 → 0
Receipt: sha256...

Main visualization:

Pass 1
  100 checked
  88 passed
  12 rejected

Pass 2
  12 requeued
  9 passed
  3 rejected

Pass 3
  3 requeued
  3 passed
  0 rejected

Each rejection card:

co_041
Reason: revenue != source
Source: Yahoo Finance
Expected/claimed: 12.4B
Observed: 11.8B
Action: requeued with constraint

The UI language should be:

Oracle
Checked
Rejected
Requeued
Clean
Receipt

Not:

AI confidence
belief score
semantic drift
holodeck
Product category upgrade

The category should become:

Oracle-Gated Agent Loops

or more marketable:

Trust Loops for AI Work

ClaimGate can remain the GitHub product.

The general platform is:

TrustLoop

Possible naming:

ClaimGate = product for GitHub
TrustLoop = platform category
OracleLoop = technical engine
WizardLoop = council runtime
How this changes the current suite
Keep
ClaimGate
GateDigger
WorkCard
Object Binding
Evidence Manifest
Blind Eval
ScenarioFan
TeamHarness
Graveyard
ReceiptVault
Add / upgrade
OracleCard
Oracle adapters
BranchLedger
RequeueController
WizardLoopController
NestedCouncilTopology
Pass-by-pass UI
Failure-as-signal mining
Demote
trust score
holodeck risk numbers
static decision preview

Replace with real loop state:

reject count
oracle mismatch count
passes until clean
requeue reasons
source-bound evidence count
The exact next build

The next build should be v19: OracleLoop Wizard Build.

It should include:

1. OracleCard schema
2. oracle check adapters:
   - url_resolves
   - json_value_match
   - github_check_run
   - local_command
3. branch ledger
4. wizard-loop run command
5. nested council config
6. requeue rejected branches
7. loop exits only when reject_count = 0
8. UI pass/reject/requeue view
9. demo based on the X thread:
   - 10 mock companies
   - first pass rejects 3
   - second pass rejects 1
   - third pass clean
10. GitHub PR demo:
   - first pass fails object binding / evidence
   - second pass clean

Command:

claimgate oracle-loop run \
  --workcard examples/oracle_loop/ev-research-workcard.json \
  --team examples/oracle_loop/team.json \
  --out .cdo/oracle-loop/ev-demo

Output:

.cdo/oracle-loop/ev-demo/
  oracle-card.json
  pass-1/
  pass-2/
  pass-3/
  branch-ledger.jsonl
  graveyard.jsonl
  receipt.json
  report.md
The final synthesis

The X thread proves your architecture in an outside domain:

mass agents are not enough
verification is the product
the checklist is the oracle
rejections are signal
the loop stops on zero hard failures

oh-my-openagent v4.12.0 gives the durable team substrate:

named teams
real threads
team.json
guide.md
member bindings
status updates
artifacts
guardrails

Your Wizard gives recursive prompt/context/loop engineering.

Codex Ratchet gives:

hard gate
graveyard
receipt
failure signal
no soft promotion

Leviathan gives:

core/eval
FlowMind
event/receipt substrate
runtime surfaces

So the new full product architecture is:

OracleCard defines clean.
Wizard councils explore.
TeamHarness makes councils durable.
ScenarioFan creates branches.
Blind eval tightens.
Hard gate verifies against oracle.
Graveyard captures rejection reasons.
RequeueController reruns failed branches.
ReceiptVault records clean admission.
UI shows pass-by-pass march to zero rejects.

That is the real system.

And yes: this is more important than another UI polish pass. The UI should now visualize the loop becoming clean, not just a static PR verdict.

has leviathan os stripped lots of its gate stuff? what is its current solution. process leviathan and my repos more . i am tring to make a viable high leverage product. and the other dev jp thinks we can do marketing too.
Looking for available tools
Thought for 5m 16s

Yes. JP’s criticism is right: we should stop reimplementing Lev concepts in the product ZIP. The product should become a Lev-native project harness: a plugin/eval-pack surface that uses core/eval, core/effect, FlowMind, and the execution ledger underneath.

Did Leviathan strip lots of gate stuff?

Not exactly. It looks like Lev removed duplicated gate/receipt/claim authority and consolidated it into a smaller proof/eval architecture.

The current Lev solution is:

core/effect owns the effect object.
core/eval owns evaluation/proof projection.
code companions compute deterministic facts.
FlowMind/orchestration owns lifecycle routing.
execution-ledger records terminal refs.
receipts stay narrow.

That is not “no gates.” It is one proof brain instead of five semi-overlapping proof systems.

core/eval is explicitly defined as the owner of suite discovery/loading, typed observation normalization, code-companion measurement, gate comparator discharge, measurement emission, GateProof/ProofBundle projection, proof manifests, and eval run artifacts.

The one_brain constraint is even sharper: core/eval is supposed to be the only core package emitting verdicts, scores, or proofs; effect packages envelopes, the ledger records, telemetry projects, and exec performs.

So the answer is:

Lev did not strip gates. It stripped duplicate proof authority.

That’s why JP is wary. He just spent a month removing extra receipt/claim/gate layers. If ClaimGate ships as another proof stack, it fights Lev. If ClaimGate ships as a Project Harness / EvalSuite family, it strengthens Lev.

What is Lev’s current solution?

Lev’s current solution is Semantic Control + core/eval.

Semantic Control says useful agent work is controlled looping: each tick is observable, programmable, gated, receipted, and routed by lifecycle decisions. It explicitly says domains do not need a new runtime; they need semantic targets, substrate-specific evaluators, proof-bearing receipts, and lifecycle decisions.

The hard guarantee is:

not “the model says done,” but candidate effects are accepted only when gates prove they satisfy the active semantic target under current constraints.

The newer canon is even more important:

LLM/witness emits typed observations.
Code companion validates and computes variable scores.
Policy maps scored facts to lifecycle decisions.
The agent never self-grades.

So JP’s “LLM can score but can’t promote” is close, but Lev’s current canon is stricter:

LLM can observe / judge / propose.
Code companion scores.
Policy decides.
Hard gate promotes.

spec-eval also says agent/witness outputs are typed observations, not proof. The separation is:

agent / witness / observer
→ typed observation + evidence refs

code companion
→ schema validation + deterministic scores + local verdict/action

core/eval
→ GateProofRef + claim verdicts + ProofBundle/proof-manifest

execution-ledger
→ RunSeal records refs

That is exactly the hard wall.

Where the current Lev system is still incomplete

Lev’s direction is right, but the current repo status is not “everything done.”

The MVP doc says manual event projection and S4 lev exec have proof, and some Pentagon/eval/security gates are green, but the product is still not launch-ready because always-on daemon/event automation and downstream MVP surfaces remain unimplemented or not rerun.

The same status table says the dispatch loop is partial, the self-managing SDLC demo is partial/not certifying, live trigger dispatch is partial, dynamic worker registration is missing/unverified, and cross-process event subscription is missing/unverified.

So the opportunity is not to replace Lev. It is to give Lev a killer first Project Harness.

What this means for our product

The product should not be framed as:

ClaimGate is its own platform.

It should become:

ClaimGate is a Lev Project Harness for SDLC and marketing.

More specifically:

ClaimGate SDLC Harness:
  GitHub PRs, issues, diffs, CI, tests, artifacts, receipts

GrowthGate / Marketing Harness:
  creative tasks, content variants, metrics, analytics feeds, campaign decisions

Both should compile to the same Lev shape:

WorkCard / Intent
→ Candidate Effect
→ EvalSuite
→ Sensors / witnesses
→ Code companions
→ GateProof / proof.yaml
→ NextTickPlan
→ lifecycle decision

spec-eval already describes this exact Eval pipeline: eval suite source, resolved scope, EvalPlan lanes, FlowMind lanes, probes, typed observations, deterministic code companions, proof lanes, scorecards/proof bundles/proof.yaml, then orchestration/lifecycle consumes proof facts for admission.

The key product reframing

The viable product is not “GitHub PR review tool” alone.

The viable product is:

Lev Project Harnesses

First two harnesses:

1. SDLC / ClaimGate
2. Marketing / GrowthGate

The shared thesis:

LLMs generate branches. Lev evaluates candidate effects against real oracles. The loop repeats until the hard gate is clean or budget is exhausted.

For code, the oracle is:

git diff
CI check-runs
tests
typecheck
security scans
artifact hashes
local rerun

For marketing, the oracle is:

CTR
conversion rate
watch retention
CAC
ROAS
pipeline generated
revenue
qualified leads

The product UI should not look like a GitHub-only tool anymore. It should look like a work-loop cockpit:

Goal
Branches generated
Oracle
Rejected branches
Requeue reasons
Next action
Clean / blocked / budget exhausted
Receipt
How to gate things without LLMs

A gate is not the LLM saying “good.”

A gate is code comparing an observed effect to a named oracle.

Examples:

Code gate
Claim:
"Fix auth cache leak."

Oracle:
GitHub check run + regression test + artifact hash.

Gate:
- did changed files match scope?
- did CI run on the same SHA?
- did required check conclude success?
- did artifact exist?
- did rerun command exit 0?
Marketing gate
Claim:
"This ad variant improves qualified lead conversion."

Oracle:
Campaign analytics feed.

Gate:
- did the campaign actually run?
- did the metric feed resolve?
- does conversion exceed baseline by policy threshold?
- is sample size above minimum?
- is spend within budget?
Research gate
Claim:
"Company revenue is $X."

Oracle:
Live source / data feed.

Gate:
- does source URL resolve?
- does source contain value?
- does claimed value match within tolerance?
- is source timestamp fresh?

That is how you gate without LLMs.

The LLM can help find candidate gates, failure modes, and checks. But it cannot be the thing that promotes.

How your Codex Ratchet work fits

Your Codex system gives the missing discipline Lev needs for project harnesses:

multiple boots / saliences
candidate-blind constraint enforcement
graveyard
no smoothing
failure as signal

Codex explicitly says multiple boots run simultaneously with different rules/goals/salience and must not contaminate each other. A1/recon maps the candidate, B/ratchet enforces blindly, S/compiler records deterministically, and A/orchestrator routes between them.

It also says A1 recon artifacts must not become B evidence without being translated, linted, blindly accepted/rejected, and recorded; otherwise it is contamination.

That is the same architecture JP is describing, but in your vocabulary:

soft branches explore
hard gate prunes
graveyard records
no soft promotion
What should be built next

Not another standalone ZIP that reimplements all concepts.

The next build should be a Lev-native harness pack:

lev-harnesses/
  plugins/
    claimgate-sdlc/
    growthgate-marketing/

  evals/
    sdlc-claimgate.eval.yaml
    marketing-experiment.eval.yaml

  code-companions/
    object-binding.ts
    github-checks.ts
    evidence-manifest.ts
    marketing-metrics.ts
    oracle-value-match.ts

  flowminds/
    sdlc-loop.flow.yaml
    marketing-loop.flow.yaml

  docs/
    claimgate-sdlc-harness.md
    growthgate-marketing-harness.md
    lev-core-eval-integration.md

It should not make a new receipt/proof stack.

It should output Lev-shaped artifacts:

.lev/eval/suites/...
.lev/runs/eval/<run-id>/
  run.yaml
  observations.jsonl
  receipts.jsonl
  gateproof/
  artifacts/
  proof.yaml

That is the layout Lev already defines.

The high-leverage product plan
Product 1: ClaimGate SDLC Harness

Immediate wedge:

AI-generated PRs cannot merge unless their claims bind to repo evidence.

This is still useful. But it should be presented as:

First Lev Project Harness: SDLC

not a separate startup called ClaimGate.

Product 2: GrowthGate Marketing Harness

JP is probably right that marketing may be bigger than programming.

Programming has strong deterministic oracles already. Marketing has the bigger business pain:

ideas are cheap
content is cheap
experiments are hard to operationalize
next actions get lost
metrics are disconnected from creative claims

GrowthGate turns marketing into the same loop:

campaign brief
→ variant swarm
→ publish/send
→ metric oracle
→ reject/scale/rework
→ save experience

The first useful marketing gate:

Content claim:
"This video/ad/email is working."

Oracle:
analytics envelope.

Gate:
- was it actually published?
- did it receive enough impressions?
- did retention/CTR/conversion beat baseline?
- did it produce qualified leads?
- should we scale, iterate, or kill?

This is probably more marketable than PR gates for non-dev customers.

But the first implementation should still use SDLC because it is easier to prove. Marketing comes second as the first non-code harness, exactly the kind of non-software-test suite Lev needs. spec-eval even leaves open the need for the first non-code suites proving eval is not merely a software test framework.

My recommendation

Stop building “ClaimGate as a full independent app.”

Build:

Lev Harness Pack 01: SDLC + Marketing

Contents:

1. SDLC ClaimGate Harness
   - GitHub PR evidence
   - object binding
   - CI/oracle checks
   - PR verdict UI

2. Marketing GrowthGate Harness
   - campaign brief
   - creative variants
   - metrics envelope
   - scale/kill/rework decision

3. GateDigger
   - project standards → eval suite proposals
   - human approval before enforcement

4. WizardLoop
   - council fanout
   - failure requeue
   - stop on hard gate clean

All using Lev underneath:

core/eval
core/effect
FlowMind
execution-ledger
project harness layout
The phrase to align with JP

Say this to him:

I think you’re right. I should stop making ClaimGate as a mini-Lev. The useful thing is a Lev-native Project Harness pack. ClaimGate becomes the SDLC harness. GrowthGate becomes the first marketing harness. GateDigger becomes the harness authoring/discovery layer. All proof/verdict authority routes through core/eval, core/effect, FlowMind, and the execution ledger — no separate proof stack.

That will land better.

Final answer

Leviathan did not strip gate stuff in the sense of abandoning it.

It collapsed gate/proof authority into core/eval + Semantic Control + proof spine, and it is trying to avoid a second proof economy.

Your product becomes viable when it stops being a standalone clone and becomes:

Lev-native Project Harnesses

First surface:

SDLC / GitHub PRs

Second surface:

Marketing / growth experiments

The deep unifying product is:

Harness engineering: prompt/context/loop/gate/oracle design for real work.

That is the category.

did you forget about axiom digger becoming constraint and gate digger?
Thought for 2m 6s

No — I did not forget it. I underweighted it in the last synthesis.

The correct structure is:

Axiom Digger
→ Constraint Digger
→ Gate Digger
→ Lev core/eval Project Harness
→ ClaimGate / GrowthGate enforcement

Axiom Digger is not a side feature. It is the authoring layer for harnesses.

The corrected architecture

Axiom Digger answers:

What does this project/team/person implicitly believe must be true?

Constraint Digger answers:

What constraints follow from those beliefs?

Gate Digger answers:

What evals, probes, or deterministic checks enforce those constraints?

Lev core/eval answers:

Did the observed effect satisfy the approved gate with real evidence?

So the full Lev-native product is not just:

WorkCard → effect → eval → receipt

It is:

Axiom Digger discovers standards
→ Constraint Digger translates standards into constraints
→ Gate Digger proposes eval suites / probes / oracle checks
→ Human approves
→ core/eval enforces through Project Harness
→ failures go to graveyard
→ repeated failures become new GateDigger inputs

That is much stronger.

Why Axiom Digger matters

The existing Axiom Explorer workflow already has the exact pieces needed for gate discovery. It is file-based, auditable, resumable, modular, and designed around synthesis artifacts rather than one chat answer.

The dig-axioms workflow specifically asks “why?” through multiple levels, identifies root assumptions, then requires:

critical vulnerabilities
critical empirical tests
confidence assessment

That is basically a gate-authoring pipeline hiding inside a thinking tool.

The output contract requires a complete axiom hierarchy, level-by-level breakdown, critical vulnerabilities, critical empirical tests, confidence assessment, and metadata.

Those map directly to Lev harness objects:

Axiom Digger output	Constraint/Gate Digger output
Belief / claim	Semantic target
Root axiom	Project principle
Assumption chain	Constraint rationale
Critical vulnerability	Open risk / falsifier
Critical empirical test	Required eval / oracle check
Confidence assessment	Enforcement level
Unconceived alternative	Probe / adversarial branch
Final synthesis	Project Harness proposal
How this becomes Lev-native

The important correction from JP is: do not build this as a separate proof system.

GateDigger should emit Lev-native eval harness material:

.lev/eval/suites/<harness>.eval.yaml
.lev/eval/suites/<harness>/probe-ledger.yaml
.lev/eval/suites/<harness>/nonstatic-gaps.yaml
.lev/eval/suites/<harness>/fixtures/
.lev/eval/suites/<harness>/prompts/
.lev/eval/suites/<harness>/lib/code-companion.ts

Lev’s eval spec already defines a Project Harness as a durable owner-local eval pack that can include eval specs, FlowMind graphs, fixtures, scripts, parser/scorer companions, probe ledgers, and non-static gap ledgers.

It also says the probe lane reads ProbeLedger and NonStaticGapLedger, observers/witnesses produce typed observations, code companions measure deterministic facts, proof lanes emit GateProof refs, and lifecycle consumes proof facts for admission.

So Axiom/GateDigger should become the Project Harness generator.

The complete loop
1. Axiom Digger
   reads repo docs, owner notes, issues, prior failures, marketing brief, or project plan

2. Constraint Digger
   converts hidden standards into explicit constraints

3. Gate Digger
   proposes EvalSuites, ProbeLedgers, NonStaticGapLedgers, OracleCards, and code-companion checks

4. Human / project owner
   approves, edits, or rejects proposed gates

5. core/eval
   enforces approved gates through typed observations + deterministic code companions

6. Graveyard
   stores failed branches and recurring failures

7. Experience Compiler
   feeds recurring graveyard patterns back into Axiom Digger

This becomes self-improving without letting the LLM promote anything.

Product translation

The actual product suite should have three authoring modes:

1. Axiom Digger

For extracting standards.

“Why does this repo care about this?”
“What would violate this project’s values?”
“What are the hidden assumptions behind this standard?”
2. Constraint Digger

For turning standards into enforceable rules.

“This implies every security claim needs regression evidence.”
“This implies every marketing claim needs a metric oracle.”
“This implies every API claim needs compatibility proof.”
3. Gate Digger

For producing actual Lev eval assets.

EvalSuite
ProbeLedger
NonStaticGapLedger
OracleCard
CodeCompanion
FlowMind verify slot
Example: SDLC

Input belief:

AI PRs should not merge unless their claim is actually proven.

Axiom chain:

AI agents overclaim.
Reviewers cannot inspect everything manually.
A PR is only trustworthy if its claim binds to out-of-band evidence.

Critical vulnerability:

The PR summary can claim “security fixed” while only proving a narrow cache change.

Critical empirical test:

Does the PR include a regression test or source-bound artifact for the claimed security failure?

GateDigger output:

eval_suite: security_claim_requires_regression_evidence
oracle:
  - github_check_run
  - local_rerun
  - artifact_hash
blocks_if:
  - security_claim_without_regression
  - evidence_not_bound_to_current_sha
  - falsifier_closed_without_evidence_ref
Example: marketing

Input belief:

Creative content is only valuable if it creates measurable market response.

Axiom chain:

Marketing is not just communication.
It is operationalized testing of audience response.
Creative work must connect to metrics.

Critical vulnerability:

The team may generate lots of good-looking content that produces no pipeline, revenue, or learning.

Critical empirical test:

Did the campaign produce CTR, retention, conversion, qualified leads, or revenue above threshold?

GateDigger output:

eval_suite: campaign_claim_requires_metric_oracle
oracle:
  - analytics_feed
  - ad_platform_metrics
  - crm_lead_quality
blocks_if:
  - metric_missing
  - sample_size_below_minimum
  - claim_not_supported_by_metric
The missing product module

The next build should add a real Lev-native module called something like:

harness-author

or:

gatedigger

Its commands:

lev harness dig-axioms --source README.md --out .lev/eval/proposals/
lev harness propose-gates --from .lev/eval/proposals/axioms.json
lev harness approve-gate --proposal security-claims-require-regression
lev harness compile-eval --proposal security-claims-require-regression

For the standalone prototype:

claimgate dig-axioms
claimgate dig-constraints
claimgate dig-gates
claimgate export-lev-eval
Important rule

Axiom Digger must not directly create active gates.

It creates gate proposals.

LLM can discover.
LLM can propose.
LLM can explain.
LLM can score as typed observation.

LLM cannot promote.
LLM cannot activate gates.
LLM cannot close proof obligations.

That matches Lev’s Semantic Control canon: the LLM/witness emits typed observations with evidence refs; code companions validate and compute scores; policy maps scored facts to lifecycle decisions; the agent never self-grades.

Correct final product stack
Axiom Digger
  discovers implicit standards

Constraint Digger
  turns standards into explicit constraints

Gate Digger
  compiles constraints into Lev Project Harness proposals

core/eval
  owns evaluator/proof authority

core/effect
  owns observed effect and effect envelope

FlowMind
  owns loop topology and lifecycle routing

execution-ledger
  records terminal run state

ClaimGate / GrowthGate
  are domain harnesses, not separate proof systems

So no, Axiom Digger is not forgotten.

It is the front door to the whole product:

Axiom Digger finds what should matter. Constraint Digger defines what must hold. Gate Digger builds the evals. core/eval decides what survives.

so create a full updated zip. and deep process everytthing.