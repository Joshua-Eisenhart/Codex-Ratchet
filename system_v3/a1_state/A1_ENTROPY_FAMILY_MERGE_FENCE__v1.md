# A1_ENTROPY_FAMILY_MERGE_FENCE__v1

STATUS: NONCANONICAL
ROLE: A1_CONTROL_PACK
DOMAIN: ENTROPY_LANE

## 1) Purpose
This pack freezes the next correction after branch-budget tightening.

The tighter broad entropy route improved helper residue, but exposed a new problem:
- cross-family substrate bleed into the entropy lane.

Observed on:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BRIDGE_MERGE_FENCE_CLUSTER__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_MERGE_FENCE_CLUSTER__v1.md`

## 2) Observed Shift
Compared with `_0011`:
- `work` dropped out
- `probe` dropped out
- but `commutator_operator` entered

That is not entropy progress.
It is cross-family merge bleed from the substrate lane.

## 3) Rule
The active broad entropy route should stay inside the entropy family.

Allowed seed floor:
- `density_entropy`
- `correlation`
- `information_work_extraction_bound`
- `erasure_channel_entropy_cost_lower_bound`
- `correlation_polarity`
- `entropy_production_rate`

Allowed path-build floor:
- `probe_induced_partition_boundary`
- `correlation_diversity_functional`
- `information_work_extraction_bound`
- `erasure_channel_entropy_cost_lower_bound`
- `density_entropy`
- `entropy_production_rate`

Everything else is outside-family bleed unless explicitly added later.

## 4) Operational Meaning
Do not let substrate enrichment terms re-enter the active entropy broad route just because the route is broad.

Broad means:
- rich graveyard pressure
- rich negative pressure
- rich rescue surface

Broad does not mean:
- arbitrary cross-family term admission

## 5) Success Criterion
This fence is doing its job if a fresh broad entropy run:
- preserves `correlation_polarity`
- keeps broad graveyard pressure alive
- avoids substrate terms like `commutator_operator`
- does not need alias/path-build retuning

## 6) Trial Result
Fresh local-stub trials with the seed-phase family fence did remove substrate bleed, but they also over-tightened the seed phase:
- graveyard pressure collapsed to the thin seed frontier,
- the route stopped at the small `correlation / correlation_polarity / information / bound / polarity` floor,
- broad exploratory pressure did not recover.

Operational decision:
- do not keep the family fence active in the broad profile right now,
- keep it as a deferred control surface for a later narrower merge problem.

## 7) Reduced Active Form
The useful remainder of this control surface is later-phase only.

Active application:
- do not clamp `graveyard_seed` with a hard family allowlist,
- do clamp `rescue` back into the entropy family once broad seed pressure already exists.

Current rescue-family allowlist:
- `correlation`
- `correlation_polarity`
- `probe_induced_partition_boundary`
- `correlation_diversity_functional`
- `information_work_extraction_bound`
- `erasure_channel_entropy_cost_lower_bound`
- `density_entropy`
- `entropy_production_rate`

Meaning:
- broad seed pressure may still expose cross-family residue,
- but later merge / rescue work should not silently drift into substrate-enrichment terms.

Implementation note:
- the active broad profile now carries this as a `rescue_allowed_terms` control in
  `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_graveyard_first_validity_campaign.py`,
- but this exact later-phase fence is not yet empirically exercised in a live rescue step.
- current validation is:
  - no regression on the active broad route,
  - seed-phase family fencing remains rejected,
  - later-phase family fencing remains the retained next control when rescue is actually reached.

## 8) Bottom Line
After branch-budget tightening, the next real control surface is family-merge fencing, not more budget churn.
