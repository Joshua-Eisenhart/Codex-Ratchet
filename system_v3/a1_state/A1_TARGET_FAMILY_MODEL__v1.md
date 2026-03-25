# A1_TARGET_FAMILY_MODEL__v1
Status: PROPOSED / NONCANONICAL / WORKING CAMPAIGN MODEL
Date: 2026-03-06
Role: A1 target family / path family model

## 1) Core Rule
One attempted concept or term target = one family/path campaign.

Substrate order rule:
- if a target depends on a sim substrate, ratchet the substrate family first
- axes should be explored as candidate orthogonal degrees of freedom inside candidate substrates, not as free primitives

## 2) Required Family Elements
Each target family should include:
1. primary target branch
2. alternative branches
3. explicit negative branch(es)
4. graveyard rescue branch(es)
5. expected failure modes
6. lineage fields
7. SIM hooks

## 3) Minimum Negative / Rescue Pressure
- at least one NEG kill path per family
- at least one rescue attempt per family

## 4) Required Lineage
Track:
- `branch_id`
- `parent_branch_id`
- `feedback_refs`
- rescue linkage

## 4.1) Minimum Cartridge Contract
A disciplined A1 cartridge is the smallest proposal object that is allowed to move toward A0-facing preparation.

Minimum required contents:
- one target family or target claim
- lineage back to A2 / rosetta inputs
- one kernel-safe candidate form
- one explicit negative/devil branch
- one rescue or alternate branch
- declared unresolved assumptions
- declared SIM/evidence hooks where relevant
- explicit proposal-only status

Not sufficient by itself:
- translation only
- de-jargonized prose only
- one elegant reformulation without adversarial structure
- a loose term cluster without branch obligations

Boundary read:
- rosetta/reformulation prepares cartridge inputs
- cartridge structure begins only when branch-diverse proposal obligations are made explicit

## 4.2) A0 Readiness Gate
A family cartridge may move toward A0-facing preparation only when:
- kernel-facing candidate fields are explicit and token-safe
- lineage is present
- one negative/devil branch is explicit
- one rescue or alternate branch is explicit
- unresolved assumptions are declared
- SIM/evidence hooks are declared where relevant
- proposal-only status remains explicit

Reject as not-ready when:
- the object is still only translation or explanatory prose
- A0 would need to infer the intended structure
- overlay or jargon terms still do hidden work inside kernel-facing fields

## 4.3) Diversity-Pressure Gate
Formal cartridge completeness is not enough.

Before A0-facing preparation, the branch set should include:
- one primary branch
- one genuinely different alternative branch
- one explicit negative/devil branch
- one rescue or alternate recovery path

Treat branch spread as too weak when:
- multiple branches are only paraphrases of the same structure
- the negative branch is only a softened primary branch
- the rescue branch only restates the primary in gentler language
- multiple branches share the same hidden assumptions and expected failure basin

Distinctness should appear in at least one of:
- assumption set
- decomposition/build order
- expected failure mode
- support/witness strategy
- path to admissibility

## 4.4) Default Admissibility Output
Every serious A1 family campaign should carry a short explicit admissibility block near its operational conclusion.

Required fields:
- `executable_head`
  - the one term currently allowed to lead lower pressure

- `active_companion_floor`
  - terms that are part of the executable floor but are not the main head

- `late_passengers`
  - richer or bookkeeping terms allowed to travel with the family but not lead execution yet

- `witness_only_terms`
  - terms allowed as support, probe, or semantic witnesses only

- `residue_terms`
  - terms still present as residue markers rather than success claims

- `landing_blockers`
  - current reasons a non-head term cannot be promoted

- `witness_floor`
  - the minimum already-surviving support terms required for the current executable shape

- `current_readiness_status`
  - one of:
    - `HEAD_READY`
    - `PASSENGER_ONLY`
    - `WITNESS_ONLY`
    - `RESIDUE_ONLY`
    - `PROPOSAL_ONLY`

Purpose:
- prevent admissibility judgment from staying scattered across campaign prose and run commentary
- make head/passenger/witness/residue placement part of normal A1 output rather than post-hoc interpretation

## 4.5) Family-Aware Admissibility Hints
When a family pack already contains stronger family-local role judgment than the selector can infer mechanically, it should carry a compact optional hint block.

Minimum useful hint fields:
- `strategy_head_terms[]`
  - terms explicitly allowed to lead if selected

- `forbid_strategy_head_terms[]`
  - terms that must not become heads even if selected

- `late_passenger_terms[]`
  - terms allowed in the family but not as current heads

- `witness_only_terms[]`
  - terms allowed only as support/witness

- `residue_only_terms[]`
  - terms that should not be counted as family success claims

- `landing_blocker_overrides{}`
  - optional map:
    - `term -> blocker string`

Working rule:
- keep this block short, family-local, and noncanon
- use it to anchor selector-side admissibility output when present
- do not use it to bypass lower-loop evidence or proposal-only limits

## 5) Purpose
This model prevents flat candidate dumping and keeps the A1 unit aligned with actual runtime rescue/negative behavior.

## 5.1) Two Run Modes
Do not treat all runs as the same thing.

Mode A — scaffold / proof run:
- purpose: prove transport, ordering, admissibility, and basic lower-loop survivability
- may use a tighter steelman-first or minimal family shape
- acceptable for early substrate/base-ladder proof work

Mode B — validity / basin run:
- purpose: produce the most valid pressure-tested result
- requires rich graveyard population
- requires rich negative sims
- may send the whole candidate model family to graveyard first and work outward from it
- should not collapse into one best-looking steelman branch

Working rule:
- use scaffold runs to prove the machinery and the first clean ladder
- use graveyard-rich validity runs to test whether the family actually survives under pressure
- use `A1_GRAVEYARD_FIRST_VALIDITY_PROFILE__v1` as the standard stricter follow-up profile

## 6) Axis-Specific Constraint
For axis work:
1. propose substrate/manifold/attractor families
2. bind axis candidates inside those families
3. test orthogonality and non-collapse under SIM
4. only then treat axis structure as more legitimate

## 7) First Campaign Seed
First concrete A1 family campaign should target:
- `finite_dimensional_hilbert_space`
- `density_matrix`
- `probe_operator`
- `cptp_channel`
- `partial_trace`

Required shape for this first campaign:
1. primary substrate branch using the full five-term family
2. alternatives that weaken or reorder parts of the family
3. explicit negatives that try to smuggle:
   - primitive equality
   - classical time
   - primitive probability
   - Euclidean metric
4. rescue branches from graveyard-linked substrate failures
5. SIM hooks tied to currently supported substrate sims

Defer until after this family is pressure-tested:
- `hopf_fibration`
- `hopf_torus`
- nested Hopf-tori conjunctions
- axis orthogonality claims

## 8) Helper Bootstrap Terms
Current lower-loop component-gating may force small auxiliary helper terms when a compound target decomposes against the fixed L0 lexeme seed.

Working rule:
- do not expand `L0_LEXEME_SET` casually
- do not rename target terms just to hide the issue
- keep helper terms explicit, minimal, and outside the primary target family

Current pass-1 decision:
- `probe` is accepted as an auxiliary bootstrap helper for `probe_operator`
- `probe` is not treated as a primary substrate-family target
- any broader lexeme-seed change stays deferred until a separate semantic review

## 9) Pass-2 Enrichment Rule
After the five-term base is proven, the next family should enrich the substrate with the smallest operator-level set that already has runtime SIM support and does not reopen superoperator/Hopf inflation.

Current pass-2 target set:
- `unitary_operator`
- `commutator_operator`
- `hamiltonian_operator`
- `lindblad_generator`

Still defer:
- superoperators
- Kraus families
- measurement/observable/projector stacks
- entropy/eigenvalue overlays
- Hopf/manifold/axis claims

## 10) Entropy-Engine Family Rule
Before classical engine lanes are ratcheted directly, A1 should prefer an operatorized entropy-processing family.

Current first entropy family:
- `probe_induced_partition_boundary`
- `correlation_diversity_functional`
- `entropy_bookkeeping_operator`
- `distinguishability_processing_machine`

Use classical engine families primarily as residue quarries and rescue sources until this family has survived pressure.

First campaign order:
1. `probe_induced_partition_boundary`
2. `correlation_diversity_functional`
3. only then `entropy_bookkeeping_operator`
4. only then `distinguishability_processing_machine`

Immediate rule:
- first entropy scaffold should target the first two terms only
- treat Carnot / Szilard / Maxwell-demon as graveyard-library rescue sources, not primary early ratchet targets

Executable bridge rule:
- first lower-loop executable pressure for the entropy lane should use the colder bridge sequence:
  1. `correlation_polarity`
  2. `entropy_production_rate`
  3. `information_work_extraction_bound`
  4. `erasure_channel_entropy_cost_lower_bound`
- keep the direct entropy-family names in proposal space while this bridge is being proven
- use `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_FIRST_ENTROPY_BRIDGE_CAMPAIGN__v1.md` as the executable bridge surface

Live normalization note:
- preserve the older bridge sequence as a pressure-order surface, not as the current head/passenger/witness split
- current live executable read is narrower:
  - `correlation_polarity` = executable head
  - `correlation` = companion executable floor
  - `entropy_production_rate` = late bookkeeping passenger
  - `information_work_extraction_bound` = witness-only / proposal-control bridge witness
  - `erasure_channel_entropy_cost_lower_bound` = witness-only / proposal-control bridge witness
- use `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1.md` and `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_INTEGRATION_BATCH__ANCHOR_WITNESS_WORKFLOW__v1.md` when a live-family admissibility question turns on this distinction

## 11) A2-first family construction discipline
Governing source surfaces:
- `system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
- `system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md`
- `system_v3/a2_state/FOUNDATION_MODE_AND_SCAFFOLD_MODE_SPLIT__v1.md`
- `/home/ratchet/Desktop/codex thread save.txt`

Working rule:
- each A1 family/path campaign must be traceable to refreshed A2 inputs
- family construction should not begin from isolated local debug state, thread-memory summaries, or recency-weighted assistant synthesis
- if A2 correction history changes the ordering or authority of a family, A1 should inherit that change directly

Sequencing implication:
- before broader runtime work resumes, A1 family construction should explicitly preserve:
  - refreshed A2 invariant locks
  - proposal-only status
  - negative/rescue obligations
  - ZIP/fail-closed boundary obligations

Mode implication:
- treat recent local route/debug work as scaffold evidence only
- do not let scaffold evidence outrun the foundation-oriented A2->A1 rebuild sequence

## 11.1) First Cartridge Pressure-Test Procedure
Use a very small clean example set before treating the rosetta -> cartridge -> readiness -> diversity chain as trustworthy.

Current first example set:
- `probe_operator`
- `correlation_polarity`
- `correlation_diversity_functional`

For each target, run the same four-stage check:

1. rosetta stage
- can the target be reformulated without overlay-heavy jargon doing the real work?
- are hidden assumptions exposed?
- do multiple interpretations remain visible rather than collapsing immediately?

2. cartridge stage
- is there one target family or target claim?
- is lineage explicit?
- is there one kernel-safe candidate form?
- is there one explicit negative branch?
- is there one explicit rescue or alternate branch?
- are unresolved assumptions declared?

3. readiness stage
- could A0 compile or reject this without inferring intent?
- are kernel-facing fields explicit and token-safe?
- are blockers declared rather than hidden?

4. diversity stage
- are the branches genuinely distinct in assumptions, decomposition, witness strategy, expected failure, or admissibility path?
- is the negative branch real?
- is the rescue branch real?

Useful failure rule:
- failure is still productive if it clearly identifies whether the weakness is in:
  - rosetta/reformulation
  - cartridge incompleteness
  - readiness ambiguity
  - fake diversity
  - lower-loop term-surface mismatch

### First Observed Result: `probe_operator`
Current read from existing substrate-family surfaces and run reports:

- rosetta: pass
  - `probe_operator` is already framed as a structural operator target rather than loose metaphor
  - auxiliary `probe` is kept explicit as helper/bootstrap residue rather than hidden ontology

- cartridge: pass
  - the surrounding substrate family already contains target shape, alternatives, negatives, rescue paths, lineage, and SIM hooks

- readiness: partial pass
  - lower-loop proof exists for `probe_operator`
  - but the target still depends on the unresolved helper/bootstrap semantic choice around auxiliary `probe`

- diversity: partial pass
  - real alternatives and family-coupled negatives exist at the substrate-family level
  - but `probe_operator` is not yet pressure-tested as its own richly differentiated branch set apart from the broader five-term family

Current blocker read:
- the main remaining blocker is not transport or missing family structure
- it is the helper/bootstrap semantic caveat around `probe`

### Second Observed Result: `correlation_polarity`
Current read from existing entropy-bridge surfaces and run reports:

- rosetta: pass
  - `correlation_polarity` is already framed as a colder runtime-facing bridge term rather than loose entropy rhetoric
  - classical engine language stays explicitly quarantined behind bridge translation and residue stripping

- cartridge: pass
  - the bridge campaign contains explicit target shape, alternatives, bridge-specific negatives, rescue sources, failure modes, and SIM policy

- readiness: pass
  - `correlation_polarity` is an admitted executable head in the active correlation branch
  - broad and cluster-clamp runs both show real executed cycles with `correlation` and `correlation_polarity` as primary admitted terms

- diversity: partial pass
  - real alternatives, negatives, and rescue structure exist
  - but one honest executable route still dominates, while narrower variants usually collapse, thin out, or lose execution

Current blocker read:
- the main remaining blocker is no longer basic executability
- it is route diversity: the family is real, but not yet richly multi-route in a strong sense

### Third Observed Result: `correlation_diversity_functional`
Current read from existing entropy-structure lift surfaces and run reports:

- rosetta: pass
  - the diversity-side lift already has real reformulation pressure
  - the warmer term `correlation_diversity_functional` is explicitly separated from the colder alias `pairwise_correlation_spread_functional`
  - the runtime anchor and term-surface problem are both made explicit

- cartridge: pass
  - the structure-lift and alias-lift packs contain a real target family, branch families, negatives, rescue logic, and explicit blocker decomposition

- readiness: fail
  - the direct target still does not land in executed-cycle broad pressure
  - the colder alias also fails to become a productive strategy head
  - so the family is proposal-rich but not yet a clean A0/B/SIM-ready executable object

- diversity: pass
  - the family does show meaningful branch spread:
    - direct lift
    - alias lift
    - helper-floor witness branches
    - bound-support variants
    - explicit negatives
  - the problem is not fake diversity
  - the problem is that these distinct routes still converge on the same landing failure

Current blocker read:
- the main remaining blocker is richer-term executable landing
- term-surface, alias, and decomposition pressure are still not strong enough to make the diversity-side target land cleanly

## 11.2) Landing-Pressure Rule For Richer Terms
A richer family term is not landing-ready just because it has:
- good rosetta
- good cartridge structure
- explicit negatives
- explicit rescue

It also needs a clean executable landing path.

Required landing floors:
- alias floor
  - either the main term is already cold enough to land
  - or there is a colder executable alias that is explicit and justified

- decomposition floor
  - the richer term can be decomposed into lower witnessable parts
  - those parts are named rather than implied

- witness floor
  - at least one already-earned or already-probe-capable support term exists
  - the richer term is not being asked to land from pure proposal air

- head/passenger decision
  - every richer-term cartridge must say whether the term is acting as:
    - strategy head
    - late passenger
    - witness-only term

- landing blocker disclosure
  - if the term is still warm, alias-heavy, decomposition-thin, or witness-poor, that must be stated directly

Classification rule:
- strategy head
  - may be sent toward A0-facing preparation only if alias, decomposition, and witness floors are satisfied strongly enough

- late passenger
  - may travel inside a cartridge family but should not be the executable leading term yet

- witness-only
  - may be preserved as interpretive or supporting structure but should not drive readiness claims

A0-side rejection rule:
- reject as landing-thin when:
  - semantic guessing is still required
  - alias remains aspirational only
  - decomposition is implied but not explicit
  - witness support is missing or too weak
  - the richer term is still functioning as a warm ontology label rather than an executable head
