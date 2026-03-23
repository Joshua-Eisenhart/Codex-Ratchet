# A1_INTEGRATION_BATCH__EXTERNAL_TOOL_DRIFT_AUDIT__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A1 INTEGRATION BATCH
Date: 2026-03-09
Role: Record non-`a1_state` wording drift that still conflicts with the normalized live A1 family doctrine

## 1) Purpose
This batch exists to preserve one narrow external-audit result without widening scope into tool mutation.

Working result:
- the main live-family doctrine inside `system_v3/a1_state` is now normalized
- the nearby anchor and A2 control surfaces are materially aligned
- the remaining external drift is concentrated in profile-local wording inside:
  - `system_v3/tools/run_graveyard_first_validity_campaign.py`

This batch does not:
- edit tool behavior
- declare the tool invalid
- create a new family model

## 2) Non-Finding
The following external surfaces are already aligned enough with the live normalized family read:
- `system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
- `system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_DIVERSITY_FAMILY__v1.md`
- `system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_DIVERSITY_FAMILY__v1.md`
- `system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_RATE_FAMILY__v1.md`
- `system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_RATE_FAMILY__v1.md`
- `system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BRIDGE_RESCUE_CONTINUATION_CLUSTER__v1.md`
- `system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_RESCUE_CONTINUATION_CLUSTER__v1.md`

So the remaining external problem is not anchor doctrine.
It is stale profile-local role wording in one tool control surface.

## 3) External Drift Cluster
Affected surface:
- `system_v3/tools/run_graveyard_first_validity_campaign.py`

Affected profile blocks:
- `entropy_bridge_cluster_rescue_broad`
- `entropy_structure_local`
- `entropy_structure_diversity_alias_broad`
- `entropy_correlation_executable_broad`
- `entropy_correlation_executable_work_strip_broad`
- `entropy_correlation_executable_seed_clamped_broad`

## 4) Drift Items
### A) `entropy_bridge_cluster_rescue_broad`
Observed wording:
- the tool text still says:
  - keep `probe_induced_partition_boundary` and `correlation_diversity_functional` as primary `path_build` heads after the seed phase

Why this drifts:
- current live A1 doctrine now treats:
  - `correlation_polarity` as the executable head
  - `correlation_diversity_functional` as passenger-only
  - `probe_induced_partition_boundary` as witness-side / deferred

Accepted bounded read:
- keep the broader post-seed structure floor as a proposal/control surface only
- do not read this tool string as the current executable head-placement doctrine

### B) `entropy_structure_local`
Observed wording:
- the tool text still says:
  - every primary branch must lead with `probe_induced_partition_boundary` or `correlation_diversity_functional`
  - do not use `correlation_polarity` inside this local support floor

Why this drifts:
- current live doctrine does not let the local structure profile redefine the active head split
- `correlation_polarity` remains the live executable head even when the structure family is under pressure

Accepted bounded read:
- preserve this as an older structure-lift pressure profile
- do not treat it as live family placement law

### C) `entropy_structure_diversity_alias_broad`
Observed wording:
- the tool text still says:
  - build alias branches with late `pairwise_correlation_spread_functional`

Why this drifts:
- the stricter live anchor / witness read keeps:
  - `pairwise_correlation_spread_functional` as a colder alias candidate
  - witness-side rather than active passenger-side

Accepted bounded read:
- preserve the older late-passenger wording as profile-local history only
- live family doctrine should keep the alias below active passenger placement

### D) `entropy_correlation_executable_*`
Affected profiles:
- `entropy_correlation_executable_broad`
- `entropy_correlation_executable_work_strip_broad`
- `entropy_correlation_executable_seed_clamped_broad`

Observed wording:
- the tool text still says:
  - build `correlation_head` branches with `correlation` as the executable carrier and late `correlation_polarity`

Why this drifts:
- current live doctrine now fixes:
  - `correlation_polarity` as the executable head
  - `correlation` as the companion executable floor

Accepted bounded read:
- preserve this as stale branch-shaping wording inside the tool profile
- do not let it outrank the live family judgment carried by:
  - `A1_ENTROPY_CORRELATION_EXECUTABLE_PACK__v1.md`
  - `RUN_ANCHOR__ENTROPY_BRIDGE_EXECUTABLE_CLUSTER__v1.md`
  - `RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_EXECUTABLE_CLUSTER__v1.md`

## 5) Operational Rule
Until a later tooling-only pass happens:

- treat the tool profile strings as profile-local historical control text
- treat `system_v3/a1_state` plus the live anchor / regeneration-witness surfaces as the authoritative proposal-side family judgment
- do not cite tool `priority_claims` strings as the current source for head / passenger / witness placement

## 6) Recommended Next Pass
If a later pass is explicitly allowed to edit tools, the minimum safe change is:

1. keep the profile keys and branch families
2. rewrite only the role-language inside `priority_claims`
3. preserve the difference between:
   - proposal/control floor
   - executable head
   - passenger-only terms
   - witness-side terms
4. do not treat that tooling pass as a runtime behavior change unless the actual control fields change beyond wording

## 7) Source Anchors
- `system_v3/a1_state/A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1.md`
- `system_v3/a1_state/A1_INTEGRATION_BATCH__ANCHOR_WITNESS_WORKFLOW__v1.md`
- `system_v3/a1_state/A1_ENTROPY_CORRELATION_EXECUTABLE_PACK__v1.md`
- `system_v3/a1_state/A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__v1.md`
- `system_v3/a1_state/A1_ENTROPY_DIVERSITY_STRUCTURE_LIFT_PACK__v1.md`
- `system_v3/a1_state/A1_ENTROPY_RATE_LIFT_PACK__v1.md`
- `system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BRIDGE_EXECUTABLE_CLUSTER__v1.md`
- `system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_EXECUTABLE_CLUSTER__v1.md`
- `system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_DIVERSITY_FAMILY__v1.md`
- `system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_DIVERSITY_FAMILY__v1.md`
- `system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_RATE_FAMILY__v1.md`
- `system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_RATE_FAMILY__v1.md`
- `system_v3/tools/run_graveyard_first_validity_campaign.py`
