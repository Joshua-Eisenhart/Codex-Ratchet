# Audit Verdict - gcm_nesting_tower_le4q_v0

Bottom line: **GENUINE_WITH_CAVEATS**.

The <=4Q tower computation is genuine against the committed 4Q freeze/cut-state artifacts. The exact all-cut tower recomputes to `0`; the probe-relative tower recomputes to `466` compatible 4Q rows with family multiplicity `15761408547092162412544`. The caveats are scope/status caveats, not falsifier kills: this `gcm_nesting_tower_le4q_v0` packet directory is currently untracked in this checkout, and I did not run the packet runner / full pytest because those commands rewrite result/cache artifacts and the audit instruction was read-only except this file.

Overall admissible ceiling: **scratch_diagnostic_le4q_tower_carrier_and_pins_relative**. No manifold, terrain, engine, Axis0, bridge, canonical, or formal admission claim is admitted.

## Checks Run

- Read source: `system_v6/sims/gcm_nesting_tower_le4q_v0/gcm_nesting_tower_le4q_v0_common.py`.
- Read validator/tests: `validate_gcm_nesting_tower_le4q_v0.py`, `tests/test_gcm_nesting_tower_le4q_v0.py`.
- Read committed upstream 4Q sources:
  - `system_v6/sims/gcm_4q_freeze_and_cuts_v0/results/gcm_4q_freeze_and_cuts_v0_results.json`
  - `system_v6/sims/gcm_4q_freeze_and_cuts_v0/results/gcm_4q_freeze_and_cuts_v0_registry.json`
- `git ls-files` confirms the upstream 4Q result and registry are tracked; `git log -n1` reports commit `84bcec53b` for those files.
- `git ls-files system_v6/sims/gcm_nesting_tower_le4q_v0` returned no tracked files, so the target packet itself is not committed.
- Read-only in-memory recompute with `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3` imported the packet module, loaded the frozen upstream JSON, called `build_tower(...)` and `summarize_counts(...)`, and compared to stored packet counts.
- Read-only validator call `validate_packet(packet)` returned `[]`.
- Read-only substrate helper call `gcm_substrate_check({"gcm_lineage": packet["gcm_lineage"]}, FOUR_Q_REGISTRY_PATH)` returned `ok: true`.

## Falsifier Verdicts

### 1. Exact Tower Genuinely Empty - PASS

Evidence: in-memory recompute produced:

- `exact_rows_len: 0`
- `exact_all_cut_compatible_4q_count: 0`
- `exact_all_cut_compatible_family_count: 0`
- `exact_all_cut_orphan_4q_count: 546`
- `matches_stored_counts: true`

Mechanism: `build_tower(...)` iterates the 546 committed 4Q `survivor_cut_rows`, then `build_cut_rows(...)` matches each of the seven cuts against lower-rung exact memberships. `compatible_family_row(..., "exact")` accepts a row only if every cut has non-empty exact IDs on both sides.

That condition fails for every 4Q survivor. Recomputed exact failed-cut sets:

- `290` rows fail all seven cuts: `1|234`, `2|134`, `3|124`, `4|123`, `12|34`, `13|24`, `14|23`.
- `256` rows fail `3|124`, `4|123`, and `12|34`.

Sample row `gcm4qsurv_ce96476df7bd02d1db24fa3f` fails exact compatibility on all seven cuts because at least one side of each required cut has `exact_count: 0`.

### 2. Probe Tower Genuinely Nonempty - PASS

Evidence: in-memory recompute produced:

- `probe_rows_len: 466`
- `probe_all_cut_compatible_4q_count: 466`
- `probe_all_cut_compatible_family_count: 15761408547092162412544`
- `probe_all_cut_orphan_4q_count: 80`
- `matches_stored_counts: true`

Mechanism: probe compatibility is computed from lower-rung probe quotient signatures, not exact matrix/object identity. `match_1q`, `match_2q`, and `match_3q` compute probe signatures from the reduced cut states; `compatible_family_row(..., "probe")` accepts a 4Q row only when every cut has non-empty probe IDs on both sides. Multiplicity is computed as the product of per-cut side-family multiplicities and then summed over the 466 compatible rows.

Substrate consumption is genuine. The tower source locks point at the committed 4Q result and registry, both at git commit `84bcec53b`; the committed 4Q result records `546` survivors, `7` cuts, and `3822 = 546 * 7` stored reduced matrix pairs. The read-only substrate helper check returned `ok: true` against `gcm_4q_freeze_and_cuts_v0_registry.json` with body hash `bf92c850a2880e26011080c900879cf729f8394ffc2e5d00bf1f70ed786020de`.

### 3. Exact vs Probe Strictly Separate - PASS

Evidence: source-level separation is real.

- Exact side membership uses `exact_ids`.
- Probe side membership uses `probe_ids`.
- `side_multiplicity(..., "exact")` returns `len(side["exact_ids"])`.
- `side_multiplicity(..., "probe")` returns `len(side["probe_ids"])`.
- `compatible_family_row(row, cut_rows, relation)` keys off either `exact_cut_compatible` or `probe_cut_compatible`.
- `relation_boundary.strict_separation` is `true`.

The sample first probe-compatible row demonstrates strict separation: the same row has zero exact membership on required sides while all probe side counts are nonzero. That row is exact-incompatible and probe-compatible; this cannot be the same relation relabeled.

### 4. Root-Axiom STRENGTHENS Backed - PASS_WITH_CAVEAT

Operational meaning in code: at 4Q, `STRENGTHENS` means:

- 4Q exact all-cut compatible count is `0`;
- 4Q probe all-cut compatible count is `> 0`;
- the <=3Q tower also had exact all-cut compatible count `0`.

Computed support:

- <=3Q exact count: `0`
- <=3Q probe count: `465`
- <=3Q probe family multiplicity: `1169687040`
- <=4Q exact count: `0`
- <=4Q probe count: `466`
- <=4Q probe family multiplicity: `15761408547092162412544`

Caveat: the label is a narrow mechanical verdict, not a theorem token. The code does not require multiplicity growth as the deciding condition for `STRENGTHENS`; it records that growth, but the branch condition is exact-empty/probe-nonempty at 4Q plus prior exact-empty at <=3Q. Under the audit-bar rule, the strength token is not verdict-bearing beyond that operational definition.

### 5. Ceiling Honest - PASS

Evidence:

- Packet classification: `scratch_diagnostic`.
- Packet claim ceiling: `scratch_diagnostic_le4q_tower_carrier_and_pins_relative`.
- `promotion_allowed: false`.
- `formal_admission_allowed: false`.
- Relation boundary explicitly excludes `manifold admission`, `terrain admission`, `engine admission`, `Axis0 or bridge admission`, and `full-density theorem beyond the declared carrier/pins relation`.
- Upstream 4Q result and registry are also `scratch_diagnostic`, `carrier_and_pins_relative: true`, `promotion_allowed: false`, `formal_admission_allowed: false`, and `not_THE_manifold: true`.

No overclaim found in the packet result/source surfaces inspected.

## Final Classification

**GENUINE_WITH_CAVEATS**.

Accepted claim: the committed 4Q cut-state substrate, when consumed through the packet's exact relation, has an empty all-cut compatibility tower; when consumed through the packet's probe quotient relation, it has `466` compatible 4Q rows and family multiplicity `15761408547092162412544`.

Not accepted: canonical manifold, terrain, engine, Axis0, bridge, full-density theorem, or formal admission.

