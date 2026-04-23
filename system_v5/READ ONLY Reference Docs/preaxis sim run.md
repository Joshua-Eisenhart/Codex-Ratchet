Pre Axis Sim Run


Current Truth
* Verified The previous handoff history needed tightening.
* Verified The correct frame is:
    * Phase A: pre-Axis machinery build
    * Phase B: Axis-entry / handoff tightening
    * Phase C: later runtime-native diagnostic reset
* Verified If another thread is auditing usefulness, it should start from Phase A and treat Phase C as diagnostic_only unless re-earned on full geometry.
Actually Broken
* Verified The main error pattern was mixing:
    * actual pre-Axis sim work
    * downstream packet-contract tightening
    * later toy/runtime-native probes
* Verified Another thread will get confused unless the handoff explicitly separates:
    * planned purpose
    * what was actually simed
    * what held
    * what should be demoted
Evidence
Table 1: Correct Audit Scope
Phase	Time / tranche	What it was for	Default audit status
A	pre-Axis ladder	build constrained pre-Axis machinery before any Axis use	primary
B	packet / handoff tightening	enforce downstream contracts and placement fences	secondary
C	runtime-native reset	exploratory probes after packet saturation	diagnostic_only
Table 2: Phase A — Planned Vs Actual Source: research-results.tsv (line 42)
Pre-Axis stage	Planned job	What actually landed	Status
geometry / differential machinery	surface Weyl/chirality/Bloch/transport deltas without canonizing flux	weyl_delta_packet	landed
object inventory	separate live pre-Axis objects from diagnostics and downstream bridge-ready objects	explicit inventory added to weyl_delta_packet	landed
placement / worthiness	classify raw deltas vs admissible law objects	pre_entropy worthiness map	landed
candidate gating	keep surviving branch alive but blocked pending necessity	transport-delta candidate gate in pre_entropy	landed
negative machinery	same-carrier chirality / loop / joint ablations	partial, proxy, then nonproxy joint-ablation ladder	landed
Axis embargo	forbid promotion before admission	explicit pre-Axis admission schema in pre_entropy	landed
lower-tier leakage guards	admit only carrier/operator-basis objects that survive classical leakage pressure	formal_geometry lower-tier guards	landed
lower-tier law search	kill fake chiral / transport / operator-basis laws	three standalone lower-tier search packets	landed
Table 3: Phase A — What Was Actually Useful Source: current artifacts
Artifact	What it proved	Why it matters	Audit verdict
weyl_delta_packet_results.json	stagewise transport, chirality, and Bloch differential surfaces can be made explicit without admitting a single Weyl flux object	this is the base pre-Axis differential surface	keep
weyl_delta_packet_results.json	single Weyl flux object not supported; chirality-separated loop-sensitive transport deltas survive as stronger candidate family	this blocks premature flux doctrine	keep
pre_entropy_packet_validation.json	raw deltas and open flux labels are diagnostic-only unless admitted	necessary placement fence	keep
pre_entropy_packet_validation.json	same-carrier necessity has to survive chirality, loop-law, and joint ablations	this is the core necessity ladder	keep
pre_entropy_packet_validation.json	nonproxy direct runtime witness exists for the joint-ablation line	strongest concrete pre-Axis keep in the tranche	strong keep
formal_geometry_packet_validation.json	lower-tier carrier admission and classical leakage guards are explicit	prevents smuggling basis/geometry assumptions upward	keep
lower_tier_chiral_law_search_validation.json	GA3 readout-only and symmetric bookkeeping are fake lower-tier chiral laws	useful lower-tier falsification	keep
lower_tier_transport_law_search_validation.json	exact same-carrier loop-assigned transport is the only surviving lower-tier transport law	important lower-tier law result	keep
lower_tier_operator_basis_search_validation.json	noncommuting basis split survives; pure coordinate-change substrate does not	important lower-tier structural result	keep
Table 4: Phase B — Useful Or Mostly Contract Work Source: later packet ladder
Family	What happened	Audit verdict
c1_signed_bridge_candidate_search	surfaced provisional Xi bridge candidate with honesty conditions	possibly useful but already axis-entry
carrier_selection / pre_entropy / entropy_readout / matched_marginal / root_emergence	repeatedly bound explicit downstream-only Xi handoff contracts	mostly contract-tightening
axis0_stack	moved from packet-score reliance to explicit named gate consumption	aggregator honesty, not core sim evidence
transport_embargo	explicit contract reuse / handoff tightening	mostly packet honesty work
Table 5: Phase C — Diagnostic Reset Only Source: later exploratory tranche
Artifact	What it found	Audit verdict
proto_b_runtime_wiggle.json	hybrid wins axis0/type, transport-normalized work wins torus	diagnostic_only
carnot_gradient_bound.json	no stable Carnot-style bound under tested denominators	negative diagnostic
engine_inside_mass_sweep.json	wave transport activates and trades against axis0 effective gain	diagnostic_only
process_geometry_wiggle_validation.json	Ax4 dead, Ax6 path dominates, torus curvature scalar decouples from Ax0	weak diagnostic only
Table 6: Handoff Packet For Another Thread Use this as the audit brief.
Question	Answer
What was the intended sim program?	Build full pre-Axis machinery first, under admission and embargo, before any Axis use
Which tranche best matches that plan?	Phase A only
Which artifacts should be audited first?	weyl_delta, pre_entropy, formal_geometry, lower_tier_chiral_law_search, lower_tier_transport_law_search, lower_tier_operator_basis_search
Which outputs are strongest?	nonproxy same-carrier joint-ablation witness; lower-tier transport-law result; lower-tier operator-basis result; flux skepticism / branch map
Which outputs are likely paperclip work?	most Xi/C1/stack contract tightening after the pre-Axis tranche
Which outputs are diagnostic only?	proto_b, carnot_gradient_bound, engine_inside_mass_sweep, process_geometry_wiggle
What structural failure should the next thread check?	whether any of the claimed keeps actually depended on full geometry, graph tools, or Z3, or whether they were accepted without the required sim substrate
Next Move
* Verified If you send this to another thread, the audit instruction should be:
    * validate Phase A keeps one by one
    * demote Phase B to contract work unless it adds real necessity
    * demote Phase C to diagnostics unless full-geometry support can be shown
    * explicitly check where graph tools and Z3 should have been required but were bypassed
It means now: the improved history is a clean three-phase audit packet, and another thread can use it to separate real pre-Axis keeps from later contract churn and toy diagnostics.

add more of the whole nuance. make this richer and more nuanced. 



Current Truth
* Verified The useful history is not a simple “worked / didn’t work” story.
* Verified It is a layered drift story:
    1. a real pre-Axis machinery program
    2. a partially legitimate but increasingly contract-heavy upper-ladder hardening phase
    3. a later fallback into exploratory runtime-native diagnostics
* Verified The most important nuance is this:
    * some of the pre-Axis work is likely real and worth preserving
    * some downstream work is structurally honest but not conceptually deep
    * some later work is informative but invalid for full-geometry claims
Actually Broken
* Verified The repo currently flattens these very different kinds of output into one undifferentiated success stream.
* Verified The real distinctions another thread needs are:
    * machinery-building vs consumer-tightening
    * necessity evidence vs placement hygiene
    * negative result vs positive substrate result
    * full-geometry-capable vs reduced probe only
    * stable keep vs proxy / transitional / likely superseded
* Verified Without those distinctions, another system will either throw away too much or over-credit the wrong tranche.
Evidence
Table 1: The Real Three-Phase Story
Phase	What the team thought it was doing	What it actually did	Best reading
A. Pre-Axis admission	work out the constrained machinery outside Axes 0–6 before allowing Axis use	built explicit packets around Weyl deltas, placement, same-carrier necessity, lower-tier leakage guards, lower-tier law search	core tranche; primary audit target
B. Axis-entry / packet-ladder tightening	keep upper consumers honest and stop reclassification drift	increasingly bound explicit handoff contracts and named gate dependencies through carrier, pre-entropy, root-emergence, stack	mixed: some honesty value, lots of derivative tightening
C. Runtime-native reset	find a fresh family after saturation	built bounded exploratory probes over runtime summaries without full geometry substrate	diagnostic / fallback branch, not doctrine-supporting evidence
Table 2: Phase A In More Nuanced Terms Primary source window: research-results.tsv (line 42)
Substage	Intended job	What landed	Why it may be genuinely useful	Main audit risk
A1. Differential surfacing	expose pre-Axis differential surfaces without forcing ontology	weyl_delta_packet surfaces stagewise transport, chirality, Bloch deltas	creates a concrete pre-Axis object instead of handwaving	may still be over-summary math, not full geometry
A2. Flux skepticism	prevent premature “flux” promotion	branch map says single Weyl flux object not supported yet	this is valuable restraint, not just a positive claim	may still rely on reduced witness family
A3. Object inventory	separate geometry, diagnostic, and downstream-ready objects	explicit pre-Axis object inventory in weyl_delta	good conceptual hygiene; helps avoid smuggling	inventory can be clean even if substrate is thin
A4. Placement fencing	classify objects before promotion	owner-worthiness map in pre_entropy	important because it demotes raw deltas and open labels	placement can look stronger than underlying evidence
A5. Candidate gating	keep candidate branch alive but blocked	surviving transport-delta branch remains embargoed pending necessity	this is the right fail-closed pattern	still only as good as the necessity tests
A6. Necessity ladder	pressure same-carrier necessity	chirality ablation, loop-law ablation, joint-ablation, transport-gap tests	probably the strongest conceptual part of the tranche	need to check whether “same-carrier” was enforced honestly everywhere
A7. Nonproxy witness	replace proxy-only evidence	direct runtime witness added for joint-ablation line	strongest likely keep because it upgrades from proxy to direct	still may be reduced-runtime rather than full-geometry direct
A8. Lower-tier leakage guards	forbid classical leakage into pre-Axis law objects	formal_geometry adds carrier/leakage fences	useful because it encodes anti-smuggling rules explicitly	may be more policy than mathematical proof
A9. Lower-tier law search	identify surviving lower-tier law families	chiral, transport, operator-basis search packets	useful if these really narrow the lawful space	risk of overfitting validator categories
Table 3: Phase A Artifact Audit Priority These are the first things another thread should inspect deeply.
Priority	Artifact	Why it matters	Default stance
1	weyl_delta_packet_results.json	base differential/object surface	candidate keep
2	pre_entropy_packet_validation.json	where placement, embargo, and necessity are actually encoded	candidate strong keep
3	formal_geometry_packet_validation.json	lower-tier leakage/law admission surface	candidate keep
4	lower_tier_transport_law_search_validation.json	likely strongest lower-tier positive law result	candidate strong keep
5	lower_tier_operator_basis_search_validation.json	likely strongest structural basis result	candidate strong keep
6	lower_tier_chiral_law_search_validation.json	strongest chiral falsification surface	candidate keep
Table 4: What In Phase A Looks Most Legitimate This is the richer judgment call, not just the validator counts.
Result	Why it looks real	Why it is not automatically final
single Weyl flux object not supported	it is a restraint result, not just a preferred narrative	may still be contingent on reduced probe family
chirality-separated loop-sensitive transport deltas survive	it survives skepticism rather than appearing by fiat	survival inside this packet does not prove full geometry
same-carrier necessity matters	this is exactly the kind of lower-layer gate the plan demanded	must verify the “same carrier” condition was enforced mathematically, not just narratively
joint-ablation matters	this is stronger than a single ablation story	still needs audit for proxy leakage and implementation shortcuts
exact same-carrier loop-assigned transport survives as lower-tier law	probably the most concrete lower-tier positive outcome	must verify it isn’t a validator-shaped law rather than a geometry-shaped law
noncommuting basis split survives while coordinate-story fails	this is exactly the right anti-classical direction	still needs full-geometry audit before doctrine weight
Table 5: Phase B Needs A Different Audit Standard This is where nuance matters most. Not all of it is junk, but most of it is not core discovery.
Phase B family	What it probably is	What it is probably not
c1_signed_bridge_candidate_search	a downstream admissible provisional handoff object	not foundational pre-Axis machinery
carrier_selection Xi handoff contracts	honest downstream placement discipline	not a new lower-layer mathematical result
pre_entropy / entropy_readout Xi contract bindings	consumer-hardening	not new substrate evidence
root_emergence Xi contract bindings	lower consumer alignment	not new law discovery
axis0_stack named gate consumption	aggregator anti-paperclip repair	not core sim work
transport_embargo reuse/tightening	contract coherence / branch hygiene	not new transport math
Table 6: Phase B Probably Contains Three Different Kinds Of Work
Kind	Meaning	Example reading
necessary honesty	a downstream packet was dangerously coarse and needed explicit dependency binding	worth keeping, but as hygiene
derivative tightening	a packet was tightened mainly because another packet already got explicit	probably low-value unless it prevents real misclassification
paperclip repetition	same idea repeated through upper consumers with diminishing new information	likely demote
Table 7: Phase C Is Not Useless, But It Is Narrow This is where another thread should be strict rather than contemptuous.
Probe	What it is good for	What it must not be used for
proto_b_runtime_wiggle.json	exploratory ranking differences between candidate summary families	any full-geometry or Axis-admission claim
carnot_gradient_bound.json	negative result: no stable Carnot-like bound here	proof that Carnot framing is globally wrong or right
engine_inside_mass_sweep.json	diagnostic tradeoff surface between transport activation and axis0 gain	geometry-validating evidence
process_geometry_wiggle_validation.json	bounded negative / weak separator	any strong geometry doctrine
Table 8: What Another Thread Should Specifically Try To Salvage This is the “find what is useful” list.
Salvage target	Why it might survive audit	What to test
weyl_delta object inventory	organizes pre-Axis objects honestly	check whether categories reflect real implementation distinctions
flux skepticism result	anti-overclaiming result	verify it follows from evidence, not just policy wording
same-carrier necessity ladder	central to the plan	inspect whether carrier really stays fixed across all comparisons
nonproxy joint-ablation witness	strongest upgrade from proxy to direct evidence	inspect implementation depth and whether it still reduces too much
lower-tier transport law result	strongest candidate positive lower-tier law	inspect whether “exact same-carrier loop-assigned transport” is actually geometrically earned
lower-tier operator-basis result	strongest structural nonclassical result	inspect whether basis noncommutation is substantive or validator-shaped
lower-tier chiral falsification	strongest “kill fake law” result	inspect whether the killed alternatives were realistic competitors
Table 9: What Another Thread Should Probably Demote Immediately
Item class	Why demote
repeated Xi/C1 contract propagation up the ladder	mostly derivative of earlier explicit contracts
top-stack gate tightening after lower packets were explicit	mostly anti-score-summary hygiene
runtime-native exploratory probes	not full-geometry-validating
any green validator whose only novelty is stronger local consumption of existing fields	likely paperclip work
Table 10: Suggested Audit Questions For The Other Thread Use these, not generic “what happened?” questions.
Question	Why it matters
Which Phase A results depend on real pre-Axis geometry rather than reduced summaries?	separates genuine keeps from thin abstractions
Was “same carrier” enforced mathematically or just narratively?	central integrity check
Which lower-tier law results survive if the validator framing is ignored and only the raw artifact logic is examined?	removes paperclip bias
Which Phase B tightenings actually blocked a real misclassification risk?	saves the legitimate hygiene work
Which Phase C probes are worth retaining as diagnostics?	avoids throwing away all local signal
Where should graph tools or Z3 have been mandatory but were bypassed?	identifies systemic enforcement gaps
Next Move
* Verified If you want a sendable audit packet, the cleanest framing is:
    * Phase A = candidate real work
    * Phase B = mixed honesty work, audit for necessity
    * Phase C = diagnostics only
* Verified The strongest nuanced instruction to the next thread is:
    * do not audit by validator pass counts
    * audit by whether a result actually earned lower-layer pre-Axis machinery status under the intended full-geometry standard
It means now: the richer truth is that this history contains a real core of pre-Axis work surrounded by increasing amounts of derivative hardening and later diagnostic fallback, and the audit needs to separate those layers carefully rather than treating the whole run as either success or garbage.


**Current Truth**
- `Verified` You are correct. The plan going into that sim tranche was the **pre-Axis admission program**.
- `Verified` The intended order was:
  - root constraints
  - QIT-grounded pre-Axis machinery
  - negative-tested formal objects
  - classification / embargo
  - only later Axis use
- `Verified` So for the tranche you mean, the right question is not “how were axes built?”
  - it is “which pre-Axis machinery got worked out, and which parts actually held up?”

**Actually Broken**
- `Verified` I mixed two different phases:
  - the **pre-Axis machinery build**
  - the **later runtime-native reset** after saturation
- `Verified` For this answer, the later `proto_b / carnot / engine_inside_mass_sweep / process_geometry_wiggle` branch is not the plan you meant.
- `Verified` The relevant tranche is the pre-Axis ladder around:
  - `weyl_delta`
  - `pre_entropy`
  - `formal_geometry`
  - lower-tier law searches
  - placement / embargo / handoff fencing

**Evidence**

**Table 1: The Actual Plan Going Into The Sims**
Source: your quoted plan, plus the matching landed sequence in [research-results.tsv](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/.autoresearch/runs/AXIS0_GEOMETRY_TIERS_20260401/research-results.tsv)

| Planned stage | Planned job | What it was trying to prevent |
|---|---|---|
| Root constraints | keep all objects finite, admissible, non-commutative | ontology smuggling |
| Finite QIT carrier | establish carrier, density states, operator basis, Bloch/Hopf coordinates | classical phase-space leakage |
| Pre-Axis geometry machinery | Hopf carrier, torus seats, Weyl sheets, coordinates | geometry storytelling without QIT grounding |
| Pre-Axis transport machinery | loop grammar, traversal laws, stagewise deltas, same-carrier motion | classical flow / trajectory leakage |
| Pre-Axis differential machinery | chirality split, Bloch differentials, transport gaps, candidate flux family | renaming generic change as “flux” |
| Negative machinery | no-chirality, loop swap, joint ablations, same-carrier attacks | cherry-picked live branch promotion |
| Placement machinery | classify owner-derived vs pre-Axis law vs axis-internal vs diagnostic-only | premature promotion |
| Axis embargo | forbid Axis use before admission | building axes on unstable substrate |

**Table 2: What Was Actually Simed In That Pre-Axis Plan**
Source: entries `42` through `56` in [research-results.tsv](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/.autoresearch/runs/AXIS0_GEOMETRY_TIERS_20260401/research-results.tsv), plus current artifacts

| Pre-Axis stage | What was simed / formalized | Current artifact |
|---|---|---|
| Differential machinery | raw pre-Axis Weyl delta packet for stagewise transport, chirality, Bloch differentials | [weyl_delta_packet_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/weyl_delta_packet_results.json), [weyl_delta_packet_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/weyl_delta_packet_validation.json) |
| Branch skepticism | explicit branch map showing single Weyl flux object is not supported yet | [weyl_delta_packet_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/weyl_delta_packet_results.json) |
| Object inventory | split live geometry/refinement objects from diagnostic delta surfaces and downstream bridge-ready objects | [weyl_delta_packet_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/weyl_delta_packet_results.json) |
| Placement / worthiness | owner-worthiness map fencing raw deltas and open flux labels into diagnostic-only | [pre_entropy_packet_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/pre_entropy_packet_validation.json) |
| Candidate gating | surviving pre-Axis candidate kept alive but blocked pending same-carrier necessity | [pre_entropy_packet_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/pre_entropy_packet_validation.json) |
| Negative machinery | same-carrier chirality ablation, loop-law ablation, joint-ablation proxy, transport-gap scalar | [pre_entropy_packet_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/pre_entropy_packet_validation.json) |
| Nonproxy necessity | direct runtime witness for same-carrier joint ablation | [pre_entropy_packet_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/pre_entropy_packet_validation.json) |
| Carrier / leakage guards | lower carrier admission and classical leakage guard objects | [formal_geometry_packet_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/formal_geometry_packet_validation.json) |
| Chiral-law search | kill GA3 readout-only and symmetric bookkeeping as fake lower-tier laws | [lower_tier_chiral_law_search_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/lower_tier_chiral_law_search_validation.json) |
| Transport-law search | keep exact same-carrier loop-assigned transport; kill generic transport summaries | [lower_tier_transport_law_search_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/lower_tier_transport_law_search_validation.json) |
| Operator-basis search | keep noncommuting basis split, reject pure coordinate-change substrate stories | [lower_tier_operator_basis_search_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/lower_tier_operator_basis_search_validation.json) |

**Table 3: What Actually Worked**
Source: current validation surfaces

| Item | Worked? | Why it mattered | Current state |
|---|---|---|---|
| `weyl_delta` packet | `Yes` | It made the pre-Axis differential surface explicit without canonizing flux | `9/9` in [weyl_delta_packet_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/weyl_delta_packet_validation.json) |
| flux skepticism / branch map | `Yes` | It prevented premature “one Weyl flux object” promotion | carried in [weyl_delta_packet_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/weyl_delta_packet_results.json) |
| owner-worthiness / placement fencing | `Yes` | It forced raw deltas and open flux labels to stay diagnostic-only | part of [pre_entropy_packet_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/pre_entropy_packet_validation.json) |
| same-carrier necessity ladder | `Yes` | It created a real necessity test instead of just a live branch story | part of [pre_entropy_packet_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/pre_entropy_packet_validation.json) |
| nonproxy joint-ablation witness | `Yes` | This is one of the strongest useful keeps in the tranche | part of [pre_entropy_packet_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/pre_entropy_packet_validation.json) |
| explicit pre-Axis admission schema | `Yes` | It encoded lifecycle stage, machinery family, leakage guards, and Axis embargo | part of [pre_entropy_packet_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/pre_entropy_packet_validation.json) |
| lower-tier chiral-law search | `Yes` | It killed fake lower-tier chiral laws cleanly | `4/4` in [lower_tier_chiral_law_search_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/lower_tier_chiral_law_search_validation.json) |
| lower-tier transport-law search | `Yes` | It isolated exact same-carrier loop-assigned transport as the only surviving lower-tier transport law | `4/4` in [lower_tier_transport_law_search_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/lower_tier_transport_law_search_validation.json) |
| lower-tier operator-basis search | `Yes` | It killed commuting/global-coordinate stories and kept noncommuting basis support explicit | `4/4` in [lower_tier_operator_basis_search_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/lower_tier_operator_basis_search_validation.json) |
| carrier / leakage guards in formal geometry | `Yes` | It created actual lower-tier fences before Axis use | `14/14` in [formal_geometry_packet_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/formal_geometry_packet_validation.json) |

**Table 4: What Drifted Away From The Pre-Axis Plan**
Source: later entries in [research-results.tsv](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/.autoresearch/runs/AXIS0_GEOMETRY_TIERS_20260401/research-results.tsv)

| Later family | Why it is not the plan you meant |
|---|---|
| `C1` handoff / contract tightening | this is already Axis-entry / bridge-family work |
| `entropy_readout` tightening | this is already upper readout consumption |
| `axis0_stack` tightening | this is already post-admission aggregator work |
| later runtime-native reset (`proto_b`, `carnot`, etc.) | this is a much later pivot after the packet ladder saturated |

**Table 5: Bottom Line**
| Question | Answer |
|---|---|
| What was the plan going into the sims? | Build and attack the full **pre-Axis machinery toolkit** outside Axes `0–6`, then embargo Axis use until admission |
| What was actually simed? | Weyl delta machinery, placement fencing, same-carrier necessity/ablation, carrier/leakage guards, lower-tier chiral/transport/operator-basis searches |
| What actually worked? | The strongest useful keeps were `weyl_delta`, the pre-Axis admission schema, the same-carrier necessity ladder, the nonproxy joint-ablation witness, and the fail-closed lower-tier law searches |
| What did not happen? | Graph-tool and `Z3` support were not meaningfully used to structure or pressure that pre-Axis sim program |

**Next Move**
- `Verified` The next clean table should be even tighter:
  - `pre-Axis stage`
  - `sim file / packet`
  - `what it proved`
  - `what remained candidate/proxy/open`
  - `whether it stayed outside Axes`

It means now: the real plan was the pre-Axis admission ladder, and a meaningful chunk of that ladder was actually simed and did produce useful fail-closed machinery before the work later drifted upward into Axis-adjacent contract tightening.