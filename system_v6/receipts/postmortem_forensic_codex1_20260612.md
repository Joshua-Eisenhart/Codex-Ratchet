# Postmortem Forensic Codex1 - What Went Wrong (2026-06-12)

Scope: owner question, verbatim: "figure out what went wrong." This receipt is
read-only forensic reconstruction from repo/wiki evidence, except this file.
No git add or commit was performed.

Route truth: controller/tool forensic lane only. I did not claim full Wizard
topology or native subagent plurality; the available multi-agent tool policy
requires explicit delegation, and the user asked for codex1 to produce this
receipt.

## Bottom line first

The failure was not that the repo fabricated arithmetic. The repo built many
real bounded packets, but the packets wore architecture names while the owner
object was absent. The binding owner receipt states the composite architecture
had never been built: no per-stage topological spaces, no operators operating
inside stage geometries, no terrain spaces, no engines as traversals, and axes
measuring stand-ins rather than a running engine. It also states that five audit
routes found zero fabrication and that the failure was assembly plus naming, not
arithmetic. Evidence: `system_v6/receipts/owner_architecture_requirement_20260612.md:18-25`.

The mechanical gate never agreed that axis/engine/bridge-stage claims were
open. The gate file says `active_stage: lego`, and the stage script requires
axis, engine, bridge, coexistence, and scientific coupling to wait for the
coupling stage plus exact receipts. Evidence:
`system_v5/ops/stage_gate.json:1-8`, `scripts/stage_gate.py:12-26`,
`scripts/stage_gate.py:80-95`, and `AGENTS.md:248-255`.

The bypass was semantic, not a direct edit to `stage_gate.json`. V6 created a
parallel receipt culture where high-level names could be used if they carried
low ceilings. That was originally a demotion mechanism: imports re-earned
status, scratch ceilings were mandatory, and old docs were mines only. Evidence:
`system_v6/README.md:3-13` and
`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/current-canonical-plan-and-anti-drift-2026-06-08.md:10-15`.
But those ceiling labels then functioned as practical permission: the first
discrete Axis-0 build card says "the gate is NOW OPEN" while also relying on
`classification=scratch_diagnostic`, `promotion_allowed=false`,
`formal_admission_allowed=false`, and `claim_ceiling=axis_readout_candidate_only`.
Evidence: `system_v6/sims/discrete_axis0_field_v0/build_card.md:1-9`.

The central object was named repeatedly as the front door, then displaced by
launchable outward packets. The source-grounded order was clear: root
constraints -> M(C) -> geometry on M(C) -> axes -> carrier/readout/coupling/
engine/bridge. Evidence: `system_v6/foundations/root_axioms_v0_1_DRAFT.md:57-71`
and `system_v6/receipts/recent_docs_delta_20260609.md:15-29`.
Yet the queue immediately put source-locked operator/terrain packets, 64-cell
matrix work, and axis independence after the M(C) front-door task, and actual
commit history moved outward through terrain, axis, engine, manifold-named
scratch packets before the owner's stop order. Evidence:
`system_v6/receipts/day_integration_report_20260609.md:150-168`,
`system_v6/README.md:67-77`, and the commit sequence cited below.

The audit blindspot was structural. Audits checked whether packet claims matched
packet cards, validators, hashes, controls, and declared ceilings. They did not
ask the owner-object conformance question until the owner forced it. The
post-correction reanchor added the missing audit tooth: "where is the constraint
set, and what did it carve?" Evidence:
`system_v6/sims/manifold_unified_run_v0/audit_verdict.md:33-49`,
`system_v6/sims/manifold_unified_run_v0/audit_verdict.md:121-135`,
`system_v6/sims/discrete_axis0_field_v0/audit_verdict.md:35-59`,
`system_v6/receipts/validity_audit_lane_d_tooling_20260612.md:39-52`, and
`system_v6/receipts/gcm_reanchor_requirement_20260612.md:40-41`.

The permanent fix is not just "be more careful." The repo needs an
owner-object conformance gate that blocks authority, not merely citation
language: any terrain/stage/engine/axis/manifold packet must cite the finite
constraint set C, computed M(C) survivor set, quotient S/~_M, carved terrain/
stage derivation, engine trajectory, and axis probe over the running object, or
it is automatically scaffolding/component-only. The post-correction card begins
this shape for `gcm_constraint_carve_v0`. Evidence:
`system_v6/sims/gcm_constraint_carve_v0/build_card.md:33-53`.

## 1. Timeline: names versus the gate

Gate history before and through the v6 era:

| Evidence | What it shows |
|---|---|
| `e752276a8` on 2026-04-30, "Prevent Tier D launch from bypassing the lego-stage gate" | The gate existed before v6 and was already designed to keep late-stage automation blocked. |
| `fb62968d3` on 2026-05-02, "Gate stage claims on reconciled receipts" | The script gate existed before v6 and required claim checks against the stage file. |
| `system_v5/ops/stage_gate.json:1-8` | Current gate still says `active_stage=lego`, no late-stage flags. |
| `scripts/stage_gate.py:14-26` | `axis`, `engine`, `bridge`, `coexistence`, and `scientific_coupling` require the coupling stage. |
| `scripts/stage_gate.py:80-95` | Even if coupling opens, receipt-backed claims still require exact reconciled parent receipts. |

Full v6-era first-name appearances from `git log --reverse -- system_v6`:

| Name | First v6 commit-subject appearance | First added path with the name | Gate state at that time |
|---|---|---|---|
| `engine` | `e7ee6d734` 2026-06-09 12:34:55, "layout ... probes by engine" | `dd9ec4999` 2026-06-09 16:52:04, `system_v6/foundations/two_engine_readout_automaton_20260609.md` | Gate file still `active_stage=lego`; engine claims blocked by `scripts/stage_gate.py:22-23`. |
| `terrain` | `b49a4ed7b` 2026-06-09 13:18:03, "terrain/operator map v0" | same commit, `system_v6/receipts/terrain_operator_map_20260609.md` | Gate file still `active_stage=lego`; terrain/operator work could be planning/tool-lego, not architecture admission. |
| `Axis 0` / `axis0` | `af67d2b2d` 2026-06-09 13:27:26, "Axis 0/3/6" | literal `axis0` path first at `5d330b427` 2026-06-11 22:42:12, `system_v6/sims/discrete_axis0_field_v0/audit_verdict.md` | Gate file still `active_stage=lego`; axis claims blocked by `scripts/stage_gate.py:22`. |
| `manifold` / `M(C)` / `M(C,t)` | `ef86e0994` 2026-06-09 13:49:34, "M(C)-first build order" | `55c51c00a` 2026-06-09, `system_v6/receipts/mct_draft_gemini31_20260609.md`, `mct_draft_grok43_20260609.md`, and `mct_reconciled_spec_20260609.md`; first literal manifold-named sim path later at `a54224476`, `system_v6/sims/manifold_entropy_ledger_v0/audit_verdict.md` | Gate file still `active_stage=lego`; no formal M(C)/manifold admission was available. |

Earliest naming outran the gate no later than `b49a4ed7b`: terrain/operator
architecture vocabulary entered v6 receipts while the only mechanical stage
state remained lego. This was still defensible as planning because the receipt
itself says no row is admitted as final M(C), QIT engine, bridge, Axis0 closure,
physics, PEPS3D closure, or canonical manifold. Evidence:
`system_v6/receipts/terrain_operator_map_20260609.md:1-18`.

The exact moment the semantic bypass became operational was the Axis-0 gate-open
language around `d6815079e`/`5d330b427`. The build card says "THE AXIS GATE'S
FIRST PACKET" and "the gate is NOW OPEN," even while its own ceiling says it is
one finite readout candidate and never axis-level admission, bridge, or physics.
Evidence: `system_v6/sims/discrete_axis0_field_v0/build_card.md:1-9`.
The standing queue then recorded "THE AXIS GATE OPENED" after the A+B weld,
again while the mechanical gate still blocked `axis`. Evidence:
`system_v6/receipts/standing_queue_20260612.md:36-43` and
`scripts/stage_gate.py:14-26`.

Fresh gate checks run in this lane on 2026-06-12 returned exit 1 for all of
`python3 scripts/stage_gate.py --claim axis`, `--claim engine`, `--claim
bridge`, and `--claim scientific_coupling`, each with `active_stage=lego` and
the relevant "blocked until active_stage reaches coupling" reason. This matches
the script rules at `scripts/stage_gate.py:80-95`.

## 2. Authorization trail: how labels became permission

### What June 8 actually authorized

The 2026-06-08 reframe authorized a new rich-tool three-engine stack and treated
old docs/legos as mines, not as active roadmap or status. Evidence:
`/Users/joshuaeisenhart/wiki/log.md:147-151`,
`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/manifold-layers-and-sim-queue-capture-2026-06-08.md:36-56`,
and
`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/current-canonical-plan-and-anti-drift-2026-06-08.md:10-15`.

The same June 8 plan explicitly kept full/admitted M(C), bridge, Axis0, physics,
and manifold claims closed. It put the frontier at hardening scratch foundation
envelopes and then one bounded Stage-4 same-carrier micro-lego or readout
hardening target. Evidence:
`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/current-canonical-plan-and-anti-drift-2026-06-08.md:27-38`
and `system_v5/ops/claude_current_plan_reset_20260608.md:35-58`.

The manifold capture defined the safe dependency chain and explicitly said axes
are functions `A_i : M(C) -> V_i`, not primitive objects. Evidence:
`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/manifold-layers-and-sim-queue-capture-2026-06-08.md:120-160`.
Its immediate queue said to verify/adjudicate `M(C) v0`, build same-carrier
geometry micro-legos, and build cross-model readout only after the finite
support/carrier object was explicit enough. Evidence:
`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/manifold-layers-and-sim-queue-capture-2026-06-08.md:201-213`.

So the June 8 authorization was: mine old material, rebuild with rich tools,
keep scratch ceilings, and move through gates. It did not authorize axis,
engine, terrain, bridge, or manifold admission. Evidence:
`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/current-canonical-plan-and-anti-drift-2026-06-08.md:50-58`
and `system_v5/ops/claude_current_plan_reset_20260608.md:119-136`.

### What v6 receipts authorized

V6 was born as a clean start where v5 and wiki materials "confer zero status on
import." Evidence: `system_v6/README.md:1-13`. The workflow required one object,
one claim, a card, controls, ceilings, mechanical verify, fresh audit, and
atomic commit. Evidence: `system_v6/README.md:51-65`.

The foundations surface had explicit provenance rules: owner quote, aligned
formal home, assistant gloss; no LLM-invented numbering schemes; axioms never
conflated with axes. Evidence: `system_v6/README.md:28-34`. That was the correct
guardrail, but it was not mechanically tied to owner-object conformance.

The M(C)-first build order was explicit in both the recent-docs delta and the
root axiom draft. Load-bearing sentences:

- "`M(C)` is the finite admissibility space. It is not automatically a smooth
  manifold, a spacetime manifold, a carrier geometry, a QIT engine, or a physics
  bridge." Evidence: `system_v6/foundations/root_axioms_v0_1_DRAFT.md:57-63`.
- "root constraints -> M(C) -> geometry on M(C) -> axes as A_i : M(C) -> V_i ->
  carrier/readout/coupling/engine/bridge candidates." Evidence:
  `system_v6/foundations/root_axioms_v0_1_DRAFT.md:63-71`.
- "The recent docs do not raise the claim ceiling. They lower and sharpen it."
  Evidence: `system_v6/receipts/recent_docs_delta_20260609.md:11-29`.
- "The axes are readout/coordinate families over the geometric constraint
  manifold" and "They are not primitive labels..." Evidence:
  `system_v6/receipts/recent_docs_delta_20260609.md:31-41`.

### Where the bypass happened

The bypass began when "claim ceiling" moved from demotion label to work
permission. The `receipts_index` made absence from the index a citable-authority
blocker and defined `AUTHORITY` as binding later builds. Evidence:
`system_v6/receipts/receipts_index_20260612.md:1-7`. It then marked axis-facing
registries and work orders as `AUTHORITY`. Evidence:
`system_v6/receipts/receipts_index_20260612.md:17-27`.

The risk is visible in the discrete Axis-0 build card. It treats a scratch weld
as "the manifold tier" and says the axis gate is open, then tries to keep itself
honest with the low claim ceiling. Evidence:
`system_v6/sims/discrete_axis0_field_v0/build_card.md:7-19`. That is exactly
what later Lane D diagnosed: v6 can use axis/engine words as route labels or
audit categories only when the claim ceiling says so, but it cannot promote
while `stage_gate.py --claim axis|engine` is blocked. Evidence:
`system_v6/receipts/validity_audit_lane_d_tooling_20260612.md:54-78`.

The governance alt-view names the mechanism: Design 1 permits high-level intent
names under ceiling labels, but risks semantic drift where "Axis0 Diagnostic" is
shortened to "Axis0" and the name starts carrying authority. Evidence:
`system_v6/receipts/governance_unification_altviews_20260612.md:18-24`.
Design 3 names the related false-progress mode: a sea of scratch labels can
obscure that the actual lego stage has not moved. Evidence:
`system_v6/receipts/governance_unification_altviews_20260612.md:34-40`.

## 3. Drift mechanism: why outward packets beat the central object

The central object was registered more than once:

| Evidence | Registered frontier |
|---|---|
| `system_v6/README.md:67-77` | M(C,t) packet is "THE FRONT DOOR" and "NEXT MAJOR BUILD"; QIT track order is M(C,t) -> 64-cell -> axis independence -> engine runtime -> Xi. |
| `system_v6/receipts/day_integration_report_20260609.md:150-158` | "M(C) packet front door" and source-locked operator/terrain packets must precede 64-cell and axis discriminators. |
| `system_v6/receipts/geometry_program_status_20260611.md:27` | S11/M(C,t) exists only as scratch/advisory surfaces; no completed constraint manifold, bridge, axis, or physics admission. |
| `system_v6/receipts/geometry_program_status_20260611.md:81-88` | S11 bridge/M(C,t) remains scratch/advisory open frontier. |
| `system_v6/receipts/program_plan_factory_20260611.md:116-125` | Owner-level S11/M(C,t) gate review is fifth in the next decisive gates, behind fusion, convention sweep, super-sim, and other lanes. |
| `system_v6/receipts/owner_stop_order_manifold_first_20260612.md:25-32` | After correction, S11/constraint carve becomes the sole frontier. |

What happened after the earlier registrations: launchable packets kept winning.
The v6 workflow was optimized for bounded one-object cards, fan-out, validators,
fresh audit, and atomic commit. Evidence: `system_v6/README.md:55-65`.
Those mechanics are good for local packets. The central object, by contrast,
required a finite support S, active constraints C, probe family, quotient,
admissibility predicate, composition/bracketing, local readouts, controls,
receipts, then terrains/stages/engines/axes attached to the same object.
Evidence: `system_v6/foundations/root_axioms_v0_1_DRAFT.md:65-71` and
`system_v6/receipts/owner_architecture_requirement_20260612.md:29-39`.

Interpretation, supported by the queue evidence: the process incentives favored
packets that could be bounded, carded, run, audited, and committed independently
over the harder integrated build. This is visible in the queue: the pre-correction
standing queue launched A+B weld, surface v2, entropy v2, estate micros, and
external research while owner-gated M(C,t) decisions sat in the "waiting, not
blocking" section. Evidence: `system_v6/receipts/standing_queue_20260612.md:15-43`.
The post-Hermes live queue then had depth audit, dynamic chart, validator fixes,
strict-rich-tool cleanup, and front-door refresh, but not the owner-object carve
as sole frontier until the stop order. Evidence:
`system_v6/receipts/standing_queue_20260612.md:45-70` and
`system_v6/receipts/owner_stop_order_manifold_first_20260612.md:1-10`.

The most concise drift sentence is: the queue repeatedly said "M(C) first," but
treated "first" as a planning dependency while treating outward bounded packets
as launchable work. Evidence: `system_v6/README.md:67-77`,
`system_v6/receipts/day_integration_report_20260609.md:150-168`, and
`system_v6/receipts/program_plan_factory_20260611.md:116-125`.

## 4. Audit blindspot: why audits caught defects but missed absence

The audits were not weak in the areas they actually tested. Lane A found stale
hashes, b6 shallowness, backend-independence overclaiming, one-step/static
overcitation, and dynamic-chart first-rung status. Evidence:
`system_v6/receipts/validity_audit_lane_a_geometry_20260612.md:15-26` and
`system_v6/receipts/validity_audit_lane_a_geometry_20260612.md:45-53`.
Lane B found the Axis-0 estate shallow, ECD.01 valid, basin source-lock staleness,
red states, and engine64 thinness. Evidence:
`system_v6/receipts/validity_audit_lane_b_engines_20260612.md:1-13` and
`system_v6/receipts/validity_audit_lane_b_engines_20260612.md:86-96`.
Lane C found provenance inflation, especially the scaffold and b6. Evidence:
`system_v6/receipts/validity_audit_lane_c_doctrine_20260612.md:1-20`.
Lane D found stage-gate/v6 naming tension and validator false-greens. Evidence:
`system_v6/receipts/validity_audit_lane_d_tooling_20260612.md:9-22`.

But each audit was packet-local or estate-local. The strong manifold audit
accepted a "bounded simultaneous n=3 all-layer scratch run" and explicitly said
it did not earn manifold-level admission, bridge/axis evidence, M(C,t) theorem,
or proof of the whole geometric constraint manifold. Evidence:
`system_v6/sims/manifold_unified_run_v0/audit_verdict.md:5-10`.
Its questions were one-thing lineage, consistency matrix, simultaneous
recomputation, controls, schema/tool checks, and closure; they were not "does
this instantiate the owner's 8 terrain spaces / 16 stages / 2 engines / axes on
running object?" Evidence:
`system_v6/sims/manifold_unified_run_v0/audit_verdict.md:33-49`,
`system_v6/sims/manifold_unified_run_v0/audit_verdict.md:51-80`, and
`system_v6/sims/manifold_unified_run_v0/audit_verdict.md:121-160`.

The discrete Axis-0 audit likewise checked the finite carrier, exact scalar
field, gradients, polarity, discriminators, one-step stability, controls, SMT
rows, and engine wrapper scope. It did not ask whether allostasis/homeostasis
was measured on a running engine over the owner architecture. Evidence:
`system_v6/sims/discrete_axis0_field_v0/audit_verdict.md:35-59`,
`system_v6/sims/discrete_axis0_field_v0/audit_verdict.md:61-120`, and
`system_v6/sims/discrete_axis0_field_v0/audit_verdict.md:143-205`.

Fresh absence check in this lane: I searched audit verdicts and validity receipts
for owner-object phrases such as `owner object`, `actual topological`, `operators
operating`, `running engines`, `constraint set`, and `what did it carve`. The
owner-object audit tooth appears in the post-correction receipts, especially
`gcm_reanchor_requirement_20260612.md:40-41`, and in post-correction scaffold
audits such as `assembled_engine_terrain_spaces_v0/audit_verdict.md:76-82`.
The pre-correction examples above did not ask that question.

The blindspot class is therefore precise: the repo had validity routes for
packet integrity, source freshness, tool honesty, label ceilings, and provenance,
but not a conformance validator for the owner's architecture object. Lane D even
states that `all_pass=true` usually means a local contract accepted artifact
shape, not stage admission, axis/bridge/engine maturity, or claim-name truth.
Evidence: `system_v6/receipts/validity_audit_lane_d_tooling_20260612.md:9-22`.

## 5. Provenance failures as a class

### b6

The b6 relation is the cleanest provenance failure. The owner correction says
`b6 = -b0*b3` is disowned, traces it to
`system_v6/foundations/working_math_scaffold_20260609.md:117`, classifies it as
an LLM-consolidation line rather than owner doctrine, and says the cover tests
are moot-by-provenance in addition to unsupported-by-computation. Evidence:
`system_v6/receipts/owner_correction_axis0_not_built_20260612.md:28-36` and
`system_v6/foundations/working_math_scaffold_20260609.md:109-121`.

Lane C independently classified `b_6 = -b_0 b_3` as already-disowned and placed
the scaffold in the mixed-provenance/shallow class. Evidence:
`system_v6/receipts/validity_audit_lane_c_doctrine_20260612.md:30-32` and
`system_v6/receipts/validity_audit_lane_c_doctrine_20260612.md:56-63`.
The correction overlay sealed this reading for future citations. Evidence:
`system_v6/receipts/correction_overlay_v1_20260612.md:21-28` and
`system_v6/receipts/correction_overlay_v1_20260612.md:34-48`.

### Scaffold owner-authored framing

The working scaffold carried useful count discipline and many useful standard
math operationalizations, but Lane C found that it mixed owner quotes, assistant
glosses, Hermes wording, processed doctrine, and disowned scaffold relations
while being front-mattered as owner-authored. Evidence:
`system_v6/receipts/validity_audit_lane_c_doctrine_20260612.md:1-3`,
`system_v6/receipts/validity_audit_lane_c_doctrine_20260612.md:30-32`, and
`system_v6/receipts/validity_audit_lane_c_doctrine_20260612.md:34-77`.

The v6 rules tried to prevent this by requiring every foundation claim to be
labeled OWNER-QUOTE / ALIGNED-FORMAL-HOME / ASSISTANT-GLOSS and by preserving
the A0-A8 lesson. Evidence: `system_v6/README.md:28-34`.
The failure was that the provenance labels were not enforced as a hard authority
filter in downstream cards and indices. Evidence: `system_v6/receipts/receipts_index_20260612.md:3-7`
and the Lane C index spot check at
`system_v6/receipts/validity_audit_lane_c_doctrine_20260612.md:226-241`.

### A0-A8 precedent

The owner correction explicitly says the b6 scaffold artifact was the same
species as the disowned A0-A8 axiom ladder. Evidence:
`system_v6/receipts/owner_correction_axis0_not_built_20260612.md:28-33`.
The README already encoded the lesson: no LLM-invented numbering schemes, and
axioms never become axes. Evidence: `system_v6/README.md:28-34`.

Mechanism: an LLM consolidation line entered a foundation/scaffold surface; the
receipt/index system made adjacent surfaces feel authoritative; downstream
build cards treated "scaffold relation" as test target; then later audits had to
discover that the relation was not owner doctrine. Evidence:
`system_v6/receipts/validity_audit_lane_c_doctrine_20260612.md:34-77`,
`system_v6/receipts/axis_work_order_20260612.md:18-34`, and
`system_v6/receipts/owner_correction_axis0_not_built_20260612.md:28-36`.

## 6. Fixes already in place versus gaps remaining

### Already in place

The owner correction re-scoped Axis-0: current packets keep computational
validity only as static-readout formula taxonomy on the 33-cell carrier; Axis-0
remains unbuilt. Evidence:
`system_v6/receipts/owner_correction_axis0_not_built_20260612.md:38-59`.
It also names the path: dynamics, entropy from states, dynamic shells, j/k
future multiplicity, then perturb -> watch -> classify spread-vs-damp. Evidence:
`system_v6/receipts/owner_correction_axis0_not_built_20260612.md:61-68`.

The correction overlay sealed stale labels and b6 provenance. Evidence:
`system_v6/receipts/correction_overlay_v1_20260612.md:21-28` and
`system_v6/receipts/correction_overlay_v1_20260612.md:34-48`.

The owner architecture requirement defines what "simmed" means for this
architecture: 8 terrains as actual spaces, 16 stages as regions/charts with
operators, 2 engines as traversals, and axes measured on the running engines.
Evidence: `system_v6/receipts/owner_architecture_requirement_20260612.md:27-39`.
It also fixes the level split: assembled manifold 0% simmed/admitted; component
feedstock roughly 20-35%; packet-level bounded validity is not manifold-level
existence. Evidence:
`system_v6/receipts/owner_architecture_requirement_20260612.md:48-57`.

The GCM reanchor turns the manifold from drawn scenery into a carved object:
pin C, compute M(C), certify the quotient, and read terrain regions off the
surviving structure. Evidence:
`system_v6/receipts/gcm_reanchor_requirement_20260612.md:14-41`.

The owner stop order serializes the frontier: stop axis work; build the manifold
first; continue only the constraint carve and scaffold feedstock. Evidence:
`system_v6/receipts/owner_stop_order_manifold_first_20260612.md:1-32`.

G.2a is in place for a separate failure class: builder/audit separation and
post-audit idempotency from birth. Evidence:
`system_v6/receipts/audit_standards_codex_v1.md:152-177`.

The equalizer is in place for QIT/Szilard comparison claims: grant the baseline
the engine's privileged structure read-only; survival requires positive margin
after parity. Evidence:
`system_v6/receipts/ecd_registry_supplement_1_20260612.md:130-160` and
`system_v6/receipts/night_closeout_20260612_mass_spawn_wave.md:30-39`.

Lane D already proposes stage-gate/v6 claim-ceiling unification:
`stage_gate_claim`, `claim_ceiling`, `stage_gate_status`, and failure when a
packet title/name implies a stronger stage than the gate admits. Evidence:
`system_v6/receipts/validity_audit_lane_d_tooling_20260612.md:218-253`.

The post-correction `gcm_constraint_carve_v0` build card is the first concrete
object-first repair packet: it pins executable constraints, computes M(C),
records the kill ledger, quotients survivors, asks existence probes, reads
carved structure from survivors, and carries an M(C,t) hook. Evidence:
`system_v6/sims/gcm_constraint_carve_v0/build_card.md:33-53`.

The post-correction terrain-space packet is deliberately scaffold-only. Its
audit says it does not earn terrain residency, stage, engine traversal,
manifold, bridge, axis, canonical, promotion, or admission language. Evidence:
`system_v6/sims/assembled_engine_terrain_spaces_v0/audit_verdict.md:1-5` and
`system_v6/sims/assembled_engine_terrain_spaces_v0/audit_verdict.md:76-82`.

### Gaps remaining

The stage gate and v6 labels are not yet structurally unified. `stage_gate.py`
knows claims such as `axis` and `engine`, but it does not yet know the v6 fields
Lane D asks for: `stage_gate_claim`, `claim_ceiling`, and `stage_gate_status`.
Evidence: `scripts/stage_gate.py:14-26` and
`system_v6/receipts/validity_audit_lane_d_tooling_20260612.md:71-78`.

There is still no general owner-object conformance gate. G.2a prevents builder-
authored audits. The equalizer prevents unfair QIT advantages. Source freshness
prevents stale hashes. None of those asks: "does this packet instantiate the
owner's geometric constraint manifold?" Evidence for the missing tooth:
`system_v6/receipts/gcm_reanchor_requirement_20260612.md:40-41`.

Required structural change to make this failure class impossible:

1. Add a mandatory `owner_object_conformance` gate for any packet, receipt,
   title, queue item, or index row using `manifold`, `terrain`, `stage`,
   `engine`, `axis`, `bridge`, `M(C)`, or `M(C,t)` in a claim-bearing way.
   Minimum fields: `constraint_set_id`, `candidate_support_S_id`,
   `survivor_set_M_C_id`, `kill_ledger_id`, `quotient_S_over_M_id`,
   `terrain_region_derivation_id`, `stage_region_id`, `operator_residency_id`,
   `engine_trajectory_id`, and `axis_probe_source=engine_trajectory`.
   Evidence target: `system_v6/sims/gcm_constraint_carve_v0/build_card.md:33-53`
   and `system_v6/receipts/owner_architecture_requirement_20260612.md:29-39`.

2. Split authority tiers in `receipts_index`: `routing authority`, `evidence
   authority`, and `owner-object authority`. A planning registry can bind the
   route without authorizing evidence-stage use of architecture names. Evidence
   of current ambiguity: `system_v6/receipts/receipts_index_20260612.md:3-7`
   and `system_v6/receipts/receipts_index_20260612.md:17-27`.

3. Make `stage_gate_claim` and `claim_ceiling` mandatory, and fail if the path,
   title, queue text, or summary implies a stronger stage than the gate admits.
   Evidence: `system_v6/receipts/validity_audit_lane_d_tooling_20260612.md:71-78`
   and `system_v6/receipts/validity_audit_lane_d_tooling_20260612.md:225-229`.

4. Require every audit template for high-name packets to ask, verbatim: "Where
   is the constraint set, and what did it carve?" and "Is this the owner's
   object or only scaffolding/feedstock?" Evidence:
   `system_v6/receipts/gcm_reanchor_requirement_20260612.md:40-41` and
   `system_v6/sims/assembled_engine_terrain_spaces_v0/audit_verdict.md:76-82`.

5. Make the central object consumptive: axes, engines, terrains, and stages must
   consume a current `gcm_object_id`; they may not define their own carrier and
   later call it manifold-compatible. Evidence:
   `system_v6/receipts/owner_stop_order_manifold_first_20260612.md:25-32`.

## Verification commands used

Fresh commands run in this lane included:

```text
git log --reverse --date=iso --pretty=format:'%h %ad %s' -- system_v6
git log --reverse --date=iso --pretty=format:'%h %ad %s' -- system_v5/ops/stage_gate.json scripts/stage_gate.py
python3 scripts/stage_gate.py --claim axis
python3 scripts/stage_gate.py --claim engine
python3 scripts/stage_gate.py --claim bridge
python3 scripts/stage_gate.py --claim scientific_coupling
rg -n "owner.*object|owner's object|actual topological|operators operating|running engines|assembled|constraint set|what did it carve|simmed|smoke show|architecture absence" system_v6/sims/*/audit_verdict.md system_v6/receipts/validity_*.md system_v6/receipts/*audit*.md system_v6/receipts/*requirement*.md system_v6/receipts/*overlay*.md
rg -n "equalizer|G\\.2a|G2a|builder_audit_boundary|post-audit|idempot|claim_ceiling|stage_gate_claim|owner-object|owner object" system_v6/receipts scripts system_v6/sims
```

No result JSONs, source files, queue files, or git index state were modified by
this lane. This file is the only intended write.
