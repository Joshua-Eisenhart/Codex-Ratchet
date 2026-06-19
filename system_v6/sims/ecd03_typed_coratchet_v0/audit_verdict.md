# Independent audit verdict - ecd03_typed_coratchet_v0

Bottom line: CANDIDATE-DEATH ACCEPTED under the pinned ECD.03 schedule-rigidity reading. Verdict class: `GENUINE-WITH-CAVEATS`; discriminator verdict: `DIES_v0`; claim ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

If ECD.03 is later widened so the QIT side admits full weighted/full-engine strategy schedules, this v0 becomes `BY_CONSTRUCTION / scope-gap` for that widened question. That is not the current registry row: weighted all-strategy engines are registered under ECD.10 / axes 7-12, while ECD.03 is the typed entropy/information co-ratchet row over the narrowed entropy-type ladder feed.

## Freshness and Scope

- Freshness tier: `TIER-2` results-available fresh audit. I read the build card, standards, registry rows, source, tests, and result JSON, then recomputed from source in memory.
- Live repo write scope: this file only. No git add/commit.
- Scratch rerun: copied the packet and required support files to `/tmp/ecd03_audit.ApDFeO` and ran the five packet tests there, so the live result files were not rewritten.

## Binding Standards Checked

- `system_v6/receipts/audit_standards_codex_v1.md`: G.2a, no-identity-leak standard, freshness tier, scratch ceiling.
- `system_v6/receipts/ecd_registry_supplement_1_20260612.md`: two-sided search, equal-information, fair-metric lessons.
- `system_v6/receipts/engine_capability_differentiators_20260612.md`: ECD.03 registry row and ECD.10 weighted-strategy separation.
- `system_v6/receipts/owner_doctrine_entropy_type_ratchet_20260611.md`: typed ladder doctrine and v1/v2 narrowed scope.

## Schedule-Space Adjudication

The death survives under the FAIR reading because the build card pins this v0's QIT side to "committed parent stage schedules plus the feed's order-sensitive controls" and the source implements exactly that as three committed schedules, collapsing to two distinct typed availability trajectories. The baseline is explicitly strongest equal-information same-alphabet schedules with arbitrary order and repetition under the same type-ladder rules.

The suspicious "QIT 2" is therefore not a nominal schedule count. Recomputed source gives QIT nominal schedules `3`, QIT distinct trajectories `2`, baseline nominal schedules `46656`, baseline distinct trajectories `77`.

Weighted strategies do not belong to this v0's ECD.03 admissible space. The owner axes 7-12 receipt says weights bias all strategies for a full independent engine/agent, and the registry maps that to ECD.10. If the owner wants ECD.03 v1 to test that wider weighted-schedule space, the v1 contract is: enumerate the QIT full weighted/admissible schedule space under equal information, then compare against the same fair metric.

## Recomputed Counts

Using `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3` with `PYTHONDONTWRITEBYTECODE=1`, in-memory source recomputation matched the stored result:

- QIT distinct trajectories: `2`
- baseline distinct trajectories: `77`
- QIT-only: `0`
- baseline-only: `75`
- symmetric difference: `75`
- verdict: `DIES_v0`
- stored validator: `ok=true`, `errors=[]`
- in-memory validator: `errors=[]`
- scratch pytest: `5 passed in 10.16s`

The two QIT trajectory fingerprints are a subset of the baseline fingerprints, so there is no QIT-only typed availability trajectory under this metric.

## Baseline-Only Spot Checks

I recomputed three baseline-only representative schedules directly through `schedule_trajectory`; all matched their stored fingerprints and status-code trajectories.

1. `chart_measure, finite_support, chart_measure, finite_support, finite_support, density_quotient`
   - Reachable: invalid early `chart_measure` no-ops until `finite_support`; later `chart_measure` and `density_quotient` apply.
   - Final types: counting, chart-uniform differential, von Neumann.

2. `finite_support, finite_support, chart_measure, finite_support, finite_support, density_quotient`
   - Reachable: repeated `finite_support` no-ops after the first application; valid `chart_measure` and `density_quotient` apply.
   - Final types: counting, chart-uniform differential, von Neumann.

3. `chart_measure, chart_measure, finite_support, finite_support, finite_support, density_quotient`
   - Reachable: two early `chart_measure` attempts no-op honestly; `finite_support` then `density_quotient` apply.
   - Final types: counting, von Neumann.

These are typed-valid trajectories under the shared ladder rules, not label readouts.

## Gates and Controls

- Availability-nontriviality gate: passed; unlocked types are counting entropy, chart-uniform differential entropy, and von Neumann entropy. This is not a void row.
- Equal information: passed for the v0 scope; QIT and baseline share the same type order, operation alphabet, operation requirements, type requirements, step budget, and environment hash.
- Fair metric: passed; the discriminator uses label-free status-code availability trajectories, not operation labels or injective ordered schedule strings.
- Two-sided search: passed under the pinned ECD.03 scope; QIT searched its committed finite schedule set, baseline searched the full same-alphabet repetition space.
- Permuted-ops regression: fired; availability moved.
- Order-blind collapse: fired; 77 full trajectories collapse to 35 under order-blind key, and that collapsed metric is not used for the discriminator.
- Dropped-half sensitivity: fired on both sides; QIT `3 -> 2`, baseline `27 -> 12`.
- No identity leak: passed; fingerprints do not read operation labels and are stable under operation-label renaming.
- G.2a: passed from birth; validator delegates audit verdict handling through `scripts/builder_audit_boundary.py`, and this file has an independent/fresh audit header.

## Caveat

`G1_SCOPE_WEIGHTED_STRATEGY_NOT_SCOPED`: the accepted death is only for ECD.03 v0 as pinned: typed availability trajectories over the narrowed entropy-type ladder feed with QIT schedule rigidity. It does not kill a future ECD.03 v1 or ECD.10 packet where the QIT side is explicitly granted full weighted/full-engine strategy schedules.

## Registry Row Language

Recommended registry update:

`ECD.03 typed entropy/information co-ratchet: DIES v0 under the pinned typed-ladder schedule discriminator. The QIT side searched its committed parent/order-sensitive schedules (3 nominal, 2 distinct trajectories); the strongest equal-information same-alphabet baseline searched arbitrary order and repetition over the same ladder (46656 nominal, 77 distinct trajectories). QIT-only = 0, baseline-only = 75. Typed co-ratcheting is not an engine capability under this v0: the ladder is environment, and schedule rigidity subtracts. Ceiling: scratch_diagnostic only; no QIT-engine admission, no universal entropy scalar, no formal theorem. Reopen/v1 only if the registry explicitly widens the QIT admissible space to weighted/full-engine schedules under equal information and the same fair metric.`
