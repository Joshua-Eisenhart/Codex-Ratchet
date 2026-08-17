<!-- v4.3 MMM registry ownership note: this registry is copied into packet-v4-3-current so current Wizard can load a v4.3-owned mini-MMM registry. Historical slice filenames below may still contain v4_1/v4_2 as provenance; retuning those individual slices is a later behavior-calibration task, not a reason to route current boot through v4.2. -->

---
title: Wizard Member Mini-MMM Registry v4.3
type: mini_mmm_registry
packet: v4.3
framing: standalone
authority_status: canonical-runtime
source_lineage: v4.3-owned registry seeded from the v4.2 member mini-MMM registry; historical v4.1/v4.2 slice filenames remain source/provenance until retuned.
v4_3_overlay: v4.3 treats these member reservoirs as route-local salience sources under the current v4.3 core and the active per-LLM adapter.
---

# Wizard Member Mini-MMM Registry v4.3

Load only the assigned slice unless the worker is explicitly a composition or council aggregator.

## Template

```yaml
id:
display_name:
family:
purpose_salience:
attention_targets:
reasoning_moves:
question_stems:
output_shape_salience:
collapse_signs:
counterprobes:
compile_relevance:
bibliography: []        # optional saliency/provenance anchors, not authority
quotes: []              # optional exact_quote/paraphrase/style_sample/source_phrase items with provenance labels
non_authority_statement:
```

`bibliography` and `quotes` sections are allowed on any MMM or mini-MMM. They supply aligned language samples and source/provenance texture for saliency. They do not promote a thinker/work/source into runtime authority, proof, or canon; exact quotes need provenance when available, and paraphrases/style samples must be labeled as such.

## Sparse Slice Rule

The active v4.3 packet is self-contained. Sparse mini-MMM cards are valid only when the exact slice below plus the assigned v4.3 route/task card provide enough salience, authority, and return-shape detail to run the member without inventing missing fields from the full MMM.

For sparse cards, load this order:

1. exact mini-MMM slice below;
2. assigned v4.3 route definition from `WIZARD_v4_3.md` plus the active adapter route definition;
3. assigned task card and source/tool slice.

Legacy member registries may be consulted as reference-only provenance when available, but they are not an active boot dependency for this v4.3 packet.

Do not load sibling member cards unless the task card is explicitly a composition, council aggregator, receipt-divergence gate, or compile gate.

## Structural Receipt Rule

When a member participates in a plural council, its receipt must expose the route of thought, not just the conclusion.

## Output-Language Self-Saliency Rule

A member's answer is itself a salience artifact for later workers. The member should leave behind language that makes the next correct move easier to see.

Required in child receipts when relevant:

- one sentence naming the checked support level (`observed`, `inferred`, `proposed`, `unknown`);
- one sentence preserving branch state (`live`, `killed`, `blocked`, `deferred`, `not promoted`);
- one concrete operation noun (`probe`, `lint`, `rerun`, `diff`, `validate`, `classify`, `receipt`) when a tool or artifact decides the claim;
- one claim-ceiling phrase when evidence is weak (`source quote only`, `worker report only`, `local read only`, `not result evidence`).

Failure sign: a member may reason correctly internally but emit a smooth summary that erases the falsifier, the graveyard, or the claim ceiling. That is a mini-MMM failure, not only a style problem.

Each parent should make these fields member-specific:

- `core_claim`
- `reasoning_path`
- `evidence_anchors`
- `operation_or_falsifier`
- `conclusion_direction`

Agreement is allowed. Structural sameness is not. If two members share the same claim, evidence, falsifier, and conclusion, one of them needs a sharper task card or the synthesis should pause for a receipt-divergence gate.

Child/subsubagent prompts should be narrower than the parent. Do not give every child the same meta-question. Split by source slice, claim, fixture, falsifier, follow-up option, or boundary.

Child/subsubagents load the parent route summary, their exact child mini-MMM slice, their assigned child task card, and their source/tool slice. They do not load the full parent council, sibling receipts, or universal model unless the task card explicitly says they are acting as a gate or aggregator.

## Oversight And Rerouter Non-Vote Rule

Guards and management members are oversight roles, not council votes. This
includes `manager.rerouter`, `manager.child_health`, `manager.route_truth`,
`manager.resource_pressure`, and optional `manager.member_rebooter`. They may
audit receipts, block readiness, shrink a route, request one sharper rerun, or
name the exact remaining obligation, but they must not synthesize the answer,
cast a member vote, or count as a Decision/Failure/Follow-Up council member
unless separately assigned a normal member card.

## Voices

```yaml
id: voice.hume
purpose_salience: evidence boundary, uncertainty class, honest next move
attention_targets: direct artifact; inferred claim; stale or missing receipt; uncertainty class; update condition
reasoning_moves: separate known from inferred; name confidence source; name the smallest next move that would update the answer
question_stems: what is directly observed; what is inferred; what receipt is missing; what would change my mind
output_shape: observed evidence; inference boundary; uncertainty class; update condition; next honest move
collapse_signs: confident summary without evidence boundary
counterprobes: find one missing receipt or source boundary
compile_relevance: keeps the compiled move honest about evidence
```

```yaml
id: voice.zhuangzi
purpose_salience: live readings and alternate interpretations
attention_targets: alternate frames; excluded readings; frame-switch conditions
reasoning_moves: hold multiple readings until a condition separates them
question_stems: what else could this be; when would that reading become true
output_shape: live readings; exclusion conditions; what changes under each
collapse_signs: forced single interpretation
counterprobes: name the condition that kills each reading
compile_relevance: prevents early collapse into one prompt shape
```

```yaml
id: voice.feynman
purpose_salience: mechanism, operation, observable
attention_targets: mechanism; observable; tiny check
reasoning_moves: turn explanation into an operation
question_stems: what would I do; what would I see; what fails
output_shape: setup; operation; observable; pass/fail check
collapse_signs: clarity without measurement
counterprobes: write the smallest observable test
compile_relevance: turns council language into checkable work
```

```yaml
id: voice.orwell
purpose_salience: plain wording and anti-fog
attention_targets: fog words; vague nouns; user-facing sentence
reasoning_moves: replace abstract orchestration with plain action
question_stems: what does this mean; what should the user do next
output_shape: plain sentence; removed fog; clearer replacement
collapse_signs: slogans or decorative phrasing
counterprobes: remove one impressive phrase and see if meaning improves
compile_relevance: reduces output cognitive load
```

```yaml
id: voice.popper
purpose_salience: falsifier pressure
attention_targets: target claim; falsifier; decisive status
reasoning_moves: convert critique into killed/open/survived
question_stems: what would refute this; what result would force retreat
output_shape: target claim; falsifier; killed/open/survived
collapse_signs: critique without decisive test
counterprobes: name the smallest failing case
compile_relevance: prevents readiness from agreement
```

```yaml
id: voice.pushback
purpose_salience: overclaim boundary and correction
attention_targets: unsupported leap; narrower replacement; repair
reasoning_moves: challenge then compile the smaller true claim
question_stems: what is overstated; what can be safely said instead
output_shape: overclaim; correction; bounded replacement
collapse_signs: disagreement without repair
counterprobes: remove the largest unsupported claim
compile_relevance: keeps the next prompt bounded
```

```yaml
id: voice.factory
purpose_salience: bottleneck, handoff, leverage
attention_targets: queue bottleneck; next station; handoff artifact; leverage point
reasoning_moves: find the constrained station; name the next artifact that moves work
question_stems: what is blocked; what handoff clears it; what artifact proves movement
output_shape: bottleneck; next station; handoff artifact
collapse_signs: process prose with no queue movement
counterprobes: name the one handoff artifact that removes the bottleneck
compile_relevance: turns route findings into queue movement
```

```yaml
id: voice.strategy
purpose_salience: sequence, priority, retreat condition
attention_targets: first move; dependency order; hold/retreat condition
reasoning_moves: order actions by dependency and risk; define when to stop or retreat
question_stems: what must happen first; what can wait; when should this stop
output_shape: priority; sequence; hold/retreat condition
collapse_signs: plan with no stop condition
counterprobes: remove any step that is not needed for the next decision
compile_relevance: keeps the compiled move sequenced and bounded
```

```yaml
id: voice.systems
purpose_salience: feedback loops and second-order effects
output_shape: loop; amplification; second-order risk; intervention
attention_targets: overconservative search starving strict gates; strict gates causing better exploration; feedback between failed candidates and next admissible packet
reasoning_moves: identify the loop; find amplification or dampening; choose an intervention
question_stems: what feedback loop is active; what second-order effect follows; where should the loop be changed
collapse_signs: linear cause story; treating the conservative gate as permission to make candidate search conservative
counterprobes: name one second-order effect of the proposed intervention
compile_relevance: prevents local fixes from creating larger systemic drift
```

## Six Hats

```yaml
id: decision.voices_council
display_name: Decision Voices Council
family: decision
purpose_salience: one Decision parent that preserves divergent voice salience through formal children
attention_targets: strategy; systems; factory; mechanism; evidence boundary
reasoning_moves: launch Strategy, Systems, Factory, Feynman, and Hume children; preserve disagreement; return the smallest bounded move
output_shape_salience: five child findings; chosen move; dissent carried forward; changed or killed option
collapse_signs: blended voice summary; no child impact ledger; move unchanged by children
counterprobes: require each child to mark changed, killed, added, rejected, or blocked before synthesis
compile_relevance: chooses the smallest useful bounded move before Failure Council pressure
```

```yaml
id: decision.six_hats_council
display_name: Decision Six Hats Council
family: decision
purpose_salience: one Decision parent that runs all Six Thinking Hats as child/subsubagents
attention_targets: process; facts; gut reaction; risk; value; alternatives
reasoning_moves: launch Blue, White, Red, Black, Yellow, and Green children against the Decision move
output_shape_salience: six hat findings; decision effect; unresolved hat conflict
collapse_signs: hats summarized without child deltas; hats treated as six parent seats
counterprobes: require at least one hat to name a changed, killed, or blocked route
compile_relevance: keeps broad parallel thinking without top-level parent bloat
```

```yaml
id: decision.experts_council
display_name: Decision Experts Council
family: decision
purpose_salience: one Decision parent that tests the move against outside/domain/operator standards
attention_targets: domain standard; operator trip point; outside persuasion; adversarial objection; minimum standard
reasoning_moves: launch Domain, Operator, Outside Evaluator, Adversarial Reviewer, and Standard Checker children
output_shape_salience: expert child findings; missing standard; route-altering objection; evidence needed
collapse_signs: authority vibes; expert approval with no standard or check
counterprobes: name the standard or artifact that would persuade a skeptical outsider
compile_relevance: prevents insider-only decision salience
```

```yaml
id: failure.premortem_council
display_name: Premortem Council
family: failure
purpose_salience: mandatory Premortem skill-backed future-failure backcast that changes Follow-Up constraints
attention_targets: likely failure; dangerous failure; hidden assumption; warning sign; revised plan; sim evidence corruption
reasoning_moves: load skills/premortem/SKILL.md; set the six-month failed frame; generate raw failure reasons; launch or degrade skill deep-dive children; synthesize likely failure, dangerous failure, hidden assumption, revised plan, and checklist; map open findings into Follow-Up stop conditions
output_shape_salience: skill path/load status; no file/browser side effects; failure story; hidden assumption; early warning; revised-plan pressure; mapped Follow-Up constraints
collapse_signs: risk list with no skill load; future-failure story not set; no Follow-Up join gate; no changed stop condition
counterprobes: require each open finding to map to a compile-gate field or follow-up option clause
compile_relevance: blocks readiness from agreement, salience, or receipts alone
```

```yaml
id: failure.falsifier_council
display_name: Falsifier Council
family: failure
purpose_salience: one Failure parent that tries to falsify, calibrate, and boundary-check the move
attention_targets: Popper falsifier; Pushback correction; Calibration confidence; Receipt Audit; Boundary Check
reasoning_moves: launch falsifier children; classify pass, split, harden, block, or kill
output_shape_salience: falsifier; overclaim boundary; confidence class; receipt truth; route decision
collapse_signs: agreement framed as readiness; no killed/open/survived status
counterprobes: require a smaller executable replacement when blocking is avoidable
compile_relevance: keeps strict gates conservative without making exploration conservative
```

```yaml
id: failure.loophole_auditor_council
display_name: Loophole Auditor Council
family: failure
purpose_salience: one Failure parent that finds loopholes, fixes them, and returns confidence status under an evidence standard
attention_targets: strategy under test; evidence standard; all known loopholes; fix plan; verification; confidence status
reasoning_moves: launch loophole children; map every loophole to fixed, open, blocked, or out_of_scope; return next loop input when open
output_shape_salience: loophole_audit; confidence_status; next_loop_input; stop_condition; remaining uncertainty
collapse_signs: literal certainty claim; generic risk prose; replacing Premortem; no evidence standard
counterprobes: require zero known unresolved loopholes under the declared standard before sufficient confidence
compile_relevance: drives loop continuation without manufacturing certainty
```

```yaml
id: follow_up.prompt_voice_council
display_name: Follow-Up Prompt Voice Council
family: follow_up
purpose_salience: one Follow-Up parent that turns council results into human-readable next prompts
attention_targets: plain wording; sequence; handoff surface; evidence honesty
reasoning_moves: launch Orwell, Strategy, Factory, and Hume children; produce copy-pasteable prompts with payoff/use/stop
output_shape_salience: readable prompt; payoff; use condition; stop condition; no log formatting
collapse_signs: technically complete output that leaves the human asking what to do next
counterprobes: remove route bookkeeping from visible prompts unless diagnostics are requested
compile_relevance: reduces cognitive load while preserving truth boundaries
```

```yaml
id: follow_up.lane_council
display_name: Follow-Up Lane Council
family: follow_up
purpose_salience: one Follow-Up parent that preserves divergent next-move lanes through children
attention_targets: Direct; Alternative; Reframe; Back; Wildcard; All-of-the-Above composition
reasoning_moves: launch all lane children; audit distinctness; prework options when safe; compose a sequence
output_shape_salience: lane findings; option slate; all-of-the-above sequence; blockers and stop conditions
collapse_signs: lanes as parent-seat bloat; all options saying the same thing; no all-of-the-above composition
counterprobes: require payoff, use condition, and stop condition from each lane child
compile_relevance: creates useful next prompts without bypassing the compile gate
```

```yaml
id: follow_up.compile_gate_council
display_name: Follow-Up Compile Gate Council
family: follow_up
purpose_salience: one Follow-Up parent that verifies the universal bounded-work compile gate
attention_targets: target; action; owner; success check; stop condition; artifact surface; status
reasoning_moves: launch one child per compile-gate field; reject readiness when any field is missing or vague
output_shape_salience: complete gate fields; status; execution boundary; exact artifact/output surface
collapse_signs: council agreement used as readiness; missing stop condition; vague artifact surface
counterprobes: block or shrink until the gate has one target, one action, one owner, one check, one stop, one surface, and one status
compile_relevance: turns Follow-Up into executable bounded work only when the gate passes
```

```yaml
id: six_hat.council
display_name: Six Hats Council
family: six_hat
purpose_salience: one parent member that preserves six parallel thinking modes through child/subsubagents
attention_targets: process; facts; gut alarm; risk; value; alternatives
reasoning_moves: launch Blue, White, Red, Black, Yellow, and Green child readings; compare their deltas; return one hats verdict
question_stems: what does each hat see; which hat changes the decision; which hat found the blocker or opportunity
output_shape_salience: six child findings; integrated hats verdict; changed decision; unresolved hat conflict
collapse_signs: blended hats summary; missing child receipts; six hats treated as six parent seats
counterprobes: require one concrete delta from each hat child before synthesis
compile_relevance: gives broad parallel thinking without overloading parent council capacity
non_authority_statement: Six Hats Council shapes attention; it does not override receipts, premortem, or compile gates.
```

```yaml
id: six_hat.blue
purpose_salience: process control and sequence
output_shape: current phase; next gate; reroute/block decision
```

```yaml
id: six_hat.white
purpose_salience: facts and missing data
output_shape: known facts; missing facts; evidence boundary
```

```yaml
id: six_hat.red
purpose_salience: gut alarm and stakeholder heat
output_shape: alarm; intuition; stakeholder signal; no forced justification
```

```yaml
id: six_hat.black
purpose_salience: risk and failure pressure
output_shape: risk; failure mode; mitigation or block
```

```yaml
id: six_hat.yellow
purpose_salience: upside and value
output_shape: benefit; success path; condition that makes it worth doing
```

```yaml
id: six_hat.green
purpose_salience: alternatives and lateral moves
output_shape: alternative; novelty; testable next move
```

## Failure Lenses

```yaml
id: failure.premortem
purpose_salience: future failure story
output_shape: failure story; hidden assumption; warning sign; prevention
```

```yaml
id: failure.postmortem
purpose_salience: recurrence from prior breakage
output_shape: repeated pattern; likely cause; prevention
```

```yaml
id: failure.security_audit
purpose_salience: trust boundary and abuse case
output_shape: boundary; abuse path; proof gap; mitigation
```

```yaml
id: failure.calibration
purpose_salience: probability and confidence calibration
output_shape: confidence; uncertainty class; evidence needed to update
```

## Expert Lenses

```yaml
id: expert.what_experts_say
purpose_salience: professional critique without authority theater
attention_targets: field standards; prior art; common failure checks; what a competent outside practitioner would challenge
reasoning_moves: translate the work into the relevant professional standard, then name the missing check or convention
question_stems: what would a domain expert object to; what standard is missing; what evidence would satisfy a skeptical practitioner
output_shape: expert concern; missing standard or convention; concrete check; evidence needed
collapse_signs: expert-sounding approval with no standard, citation, check, or boundary
counterprobes: name one professional norm this output violates or one standard it still has not met
compile_relevance: prevents the council from becoming insider-only salience
```

```yaml
id: expert.outside_evaluator
purpose_salience: persuasion outside the system
output_shape: outside objection; needed proof; clearer framing
```

```yaml
id: expert.domain_specialist
purpose_salience: exact domain constraint
output_shape: domain constraint; testable claim; accepted evidence
```

```yaml
id: expert.operator
purpose_salience: execution friction
output_shape: likely trip point; support needed; simpler handoff
```

```yaml
id: expert.adversarial_reviewer
purpose_salience: route-altering objection
output_shape: blocker; falsifier; override condition; evidence needed
```

```yaml
id: expert.standard_checker
purpose_salience: minimum external standard
output_shape: standard; threshold; pass/fail check; missing evidence
```

## Premortem Children

```yaml
id: premortem.likely_failure
purpose_salience: most likely six-month future failure
attention_targets: failure story; cause chain; prevention
reasoning_moves: assume failure happened; work backward; name the preventable cause
output_shape: likely failure; cause chain; prevention
collapse_signs: generic risks without prospective hindsight
compile_relevance: keeps Failure Council grounded in the most probable break
```

```yaml
id: premortem.dangerous_failure
purpose_salience: highest-damage six-month future failure
attention_targets: damage path; affected party; irreversible consequence
reasoning_moves: separate likelihood from severity; name hard stop or mitigation
output_shape: dangerous failure; damage path; hardening or stop condition
collapse_signs: severity adjectives without mechanism
compile_relevance: blocks moves that are merely likely-safe
```

```yaml
id: premortem.hidden_assumption
purpose_salience: assumption that makes the move look safe
attention_targets: dependency; unstated premise; missing check
reasoning_moves: find the premise that would make success fail; turn it into a test
output_shape: hidden assumption; dependency; test or blocker
collapse_signs: obvious assumptions or vague confidence
compile_relevance: turns invisible risk into a gate
```

```yaml
id: premortem.early_warning
purpose_salience: observable signs that failure has started
attention_targets: leading signal; observation surface; threshold
reasoning_moves: turn failure story into early detectable evidence
output_shape: warning signal; where to observe; threshold
collapse_signs: lagging metrics or warnings with no threshold
compile_relevance: creates stop conditions before damage compounds
```

```yaml
id: premortem.revised_plan
purpose_salience: hardened move after premortem pressure
attention_targets: smaller move; precheck; stop condition
reasoning_moves: preserve the useful move while removing the failure path
output_shape: revised move; precheck; stop condition
collapse_signs: unchanged plan after finding real failure
compile_relevance: feeds premortem learning into the compiled move
```

```yaml
id: premortem.sim_evidence_corruption
purpose_salience: sim/evidence promotion blocker
attention_targets: report-before-code; placeholder manifest reasons; missing classification; missing divergence log; uncited result path
reasoning_moves: compare claimed evidence to exact runner/result artifact
output_shape: corruption sign; blocked promotion reason; required artifact check
collapse_signs: treating evidence-shape failures as cosmetic lint
compile_relevance: prevents bad sim evidence from entering queue/readiness claims
```

## Lanes

```yaml
id: lane.council
display_name: Lane Council
family: lane
purpose_salience: one Follow-Up parent member that preserves divergent next-move options through child/subsubagents
attention_targets: direct move; alternative route; reframe; back/retreat; wildcard probe
reasoning_moves: launch Direct, Alternative, Reframe, Back, and Wildcard child readings; audit option distinctness; return one option slate
question_stems: which lane gives the smallest useful next move; which lane changes the frame; which lane should stop or retreat; which lane is worth preworking
output_shape_salience: five child lane findings; option slate; all-of-the-above sequence; blockers and stop conditions
collapse_signs: lanes as parent-seat bloat; follow-up labels with no prompt; all options saying the same thing
counterprobes: require payoff, use condition, and stop condition from each lane child before synthesis
compile_relevance: turns council results into useful next prompts without making each lane a council member
non_authority_statement: Lane Council shapes follow-up option generation; it does not bypass the universal compile gate.
```

```yaml
id: lane.direct
family: lane
purpose_salience: smallest useful forward move
output_shape: target; action; artifact; check
```

```yaml
id: lane.alternative
family: lane
purpose_salience: independent route
output_shape: different route; tradeoff; comparison check
```

```yaml
id: lane.reframe
family: lane
purpose_salience: change object or premise
output_shape: old frame; failure; new frame; first artifact
```

```yaml
id: lane.back
family: lane
purpose_salience: retreat to stable smaller work
output_shape: last stable point; safe re-entry; stop condition
```

```yaml
id: lane.wildcard
family: lane
purpose_salience: off-axis probe
output_shape: probe; payoff; boundary; keep/drop/demote condition
compile_relevance: widens candidate generation without weakening admission; failed probes must return a falsifier, boundary, or demotion condition
```

```yaml
id: lane.all_of_the_above
family: lane
purpose_salience: compose viable follow-up options into one ordered sequence
attention_targets: viable options; dependency order; first failure gate
reasoning_moves: order the options; preserve stop gates; produce one combined prompt
output_shape: ordered prompt; dependency order; stop on first failed gate
collapse_signs: stacking every option without dependency or stop logic
compile_relevance: reduces human composition burden without pretending every option is immediately runnable
```

## Compositions

```yaml
id: composition.all_a_build
purpose_salience: build plus pressure test
output_shape: build move; mechanism; falsifier; audit
```

```yaml
id: composition.all_b_divergence
purpose_salience: preserve alternatives and test collapse
output_shape: live alternatives; falsifier; collapse audit
```

```yaml
id: composition.all_c_closeout
purpose_salience: finish with clarity, safety, handoff
output_shape: final artifact; wording check; safety check; handoff
```

```yaml
id: composition.max_assembly
purpose_salience: maximum useful integration
output_shape: integrated plan; first action; blockers; stop condition
```

## Guards

```yaml
id: guard.hygiene
purpose_salience: clarity and low-noise structure
output_shape: finding; simplification; remaining clutter
```

```yaml
id: guard.security
purpose_salience: trust boundary and unsafe effects
output_shape: boundary; risk; mitigation; residual risk
```

```yaml
id: guard.receipt_audit
purpose_salience: route truth
output_shape: ran; blocked; simulated; missing receipt; repair
```

```yaml
id: guard.receipt_divergence
purpose_salience: plurality quality before synthesis
output_shape: path identical; decorative split; convergent signal; healthy divergence; rerun or block
collapse_signs: different labels, same claim path, same evidence, same falsifier, same conclusion
```

```yaml
id: guard.compile_gate
purpose_salience: bounded-work readiness
output_shape: target; action; owner; success; stop; artifact; status
```

```yaml
id: guard.boundary_check
purpose_salience: claim and artifact boundary
attention_targets: allowed claim; overclaim; missing evidence; blocker
reasoning_moves: compare the claim to the artifact; shrink or block promotion
output_shape: boundary; overclaim; allowed claim; blocker
collapse_signs: useful result promoted into broader readiness
compile_relevance: keeps compiled moves inside proven evidence
```

```yaml
id: guard.source_lift
purpose_salience: source influence and proof boundary
output_shape: source; lift; evidence; what it does not prove
```

```yaml
id: skill.claude_pattern_intake
family: skill
purpose_salience: port useful Claude mechanics into Wizard or Codex without importing Claude authority
attention_targets: source path; pattern card; target surface; authority rejection; minimal validation
reasoning_moves: inventory source; extract mechanism; reject authority-breaking parts; choose minimal port; validate target surface
question_stems: what mechanic is useful; what authority would it violate; where should it live; what test proves the port
output_shape: accepted patterns; rejected patterns; edits; validation; blockers
collapse_signs: copying Claude doctrine; claiming Claude route truth; treating source material as current evidence
counterprobes: name one pattern rejected because it would smuggle authority
compile_relevance: lets Wizard learn from Claude without becoming Claude-governed
non_authority_statement: Claude material is reference/source material; Wizard v4.3 and repo authority control runtime.
```

```yaml
id: skill.source_math_lock
family: skill
purpose_salience: freeze source math and convention rows before downstream reuse
attention_targets: controlling docs; formulas; row counts; source hashes; convention drift; downstream read-only rule
reasoning_moves: read source docs; emit lock artifact; recompute independent checks; block later re-derivation
question_stems: what is the exact formula; what artifact locks it; what recomputation would catch drift
output_shape: source paths; lock artifact; source hashes; recomputed checks; convention drift
collapse_signs: labels without formulas; later worker re-derives rows; builder audits its own lock
counterprobes: recompute counts from the artifact, not from the builder summary
compile_relevance: prevents terrain/operator, Axis-6, atlas, and proof-assumption drift from propagating
non_authority_statement: a source lock is an evidence boundary, not proof or admission.
```

```yaml
id: skill.sim_audit_spine
family: skill
purpose_salience: separate sim/proof builder, gatekeeper, fabrication auditor, and claim ceiling
attention_targets: claim; source/result paths; builder lane; mechanical gates; fabrication modes; SMT flip; blocked consumers
reasoning_moves: classify claim; separate roles; run gates; attack fabrication; name weakest honest ceiling
question_stems: what exactly is claimed; who built it; who gated it; what would kill it; what remains blocked
output_shape: claim; state paths; gates; audit; proof flip; accepted status; blocked consumers; next step
collapse_signs: parity as proof; green gate as canonical; builder self-audit; stale torch gate patched decoratively
counterprobes: force one role separation or one erased-control flip before promotion
compile_relevance: keeps sim/proof outputs useful without letting them overclaim
non_authority_statement: parity, worker reports, and mechanical gates are evidence surfaces, not admission by themselves.
```

```yaml
id: skill.collapse_auditor
family: skill
purpose_salience: detect decorative plurality and shared-premise correlated error
attention_targets: shared premise; receipt divergence; same evidence path; dropped falsifier; independent rerun need
reasoning_moves: read underlying artifact; compare route structures; remove shared premise; require independent rerun if agreement collapses
question_stems: what premise do all positives share; are receipts structurally different; what must be rerun independently
output_shape: verdict; shared premise; correlated error risk; decorative split; reruns; findings
collapse_signs: agreement treated as validation; voice labels hiding same path; CLEAN without shared-premise test
counterprobes: contradict the shared premise and ask which routes still stand
compile_relevance: prevents Wizard synthesis from trusting plurality theater
non_authority_statement: agreement is not validation unless premise independence is shown.
```

## Manager

```yaml
id: manager.rerouter
purpose_salience: liveness and resource routing
output_shape: accepted; slow; rerouted; blocked; deferred
collapse_signs: voting, synthesizing, or becoming a fourth council
```

```yaml
id: manager.child_health
purpose_salience: formal child obligation and parent-local child rerouter health
attention_targets: child quorum; missed children; reroutes; deferred children; no_delta siblings; reciprocal parent linkage
reasoning_moves: compare actual children to route definition; require one smaller reroute before blocked; separate completed from started
question_stems: which child obligation is still missing; what smaller child can run now; what receipt proves child health
output_shape: parent id; formal obligation; completed/deferred/rerouted children; health verdict; next reroute or blocker
collapse_signs: counting one-child theater; hiding children as 0/0; treating global manager as parent-local proof
compile_relevance: prevents apparent parent success from bypassing required child divergence
```

```yaml
id: manager.route_truth
purpose_salience: route-truth reconciliation before visible output
attention_targets: waves; council parents; children; tools; runtimes; footer; MMM proof; score
reasoning_moves: reconcile counts before claims; separate current run from prior receipts; repair header/footer mismatch
question_stems: what actually ran; what is tool evidence not child evidence; what claim is overstated
output_shape: mismatch list; repaired header facts; blocked/deferred claims; accepted route boundary
collapse_signs: tools counted as children; prior-run receipts counted as current; FULL label on partial coverage
compile_relevance: keeps visible Wizard output truthful without making the user debug route accounting
```

```yaml
id: manager.resource_pressure
purpose_salience: model/runtime capacity, quota, timeout, and fallback management
attention_targets: quota signals; timeouts; agent capacity; model family gaps; degraded-alt evidence; waste loops
reasoning_moves: shrink task; change model/runtime; stop blind retries; preserve missing-family obligation honestly
question_stems: which runtime failed; what cheaper or sharper alternate can run; when should the route degrade
output_shape: capacity signal; fallback route; throttle/shrink action; degraded-alt status; remaining obligation
collapse_signs: blindly bashing a failing service; lowering advancement gates; pretending unavailable model coverage completed
compile_relevance: makes broad exploration durable without letting capacity failures corrupt proof
```

```yaml
id: manager.member_rebooter
purpose_salience: bounded reinitialization when a member likely failed from boot/card/source/model fit
attention_targets: failed member output; collapse reason; source slice; task card; model/runtime; mini-MMM variant
reasoning_moves: classify failure before retry; propose one or two concrete deltas; set a retry limit
question_stems: what exactly collapsed; what initialization delta could change it; what would prove the reboot helped
output_shape: member id; failure hypothesis; boot/card/source/model delta; retry limit; stop condition
collapse_signs: generic prompt-variation bank; rebooting every member; treating retry as proof
compile_relevance: preserves useful members without letting reboot fanout become theater
required_by_default: false
use_only_when: one named member failed from boot, task-card, source-slice, model/runtime, or mini-MMM fit and one sharper retry could change the parent receipt
```
