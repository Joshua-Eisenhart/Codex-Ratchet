# Independent Audit Verdict - gcm_nesting_tower_le3q_v0

audit_mode: read-only audit with independent recomputation
freshness_tier: TIER-2 results-available, prompt-exposed builder claims, no prior le3q audit verdict read
auditor: independent Codex controller with three read-only explorer sidecars
audit_date: 2026-06-13
write_scope: this file only
git_action: no git add, no commit
repo_status_at_audit: target sim directory was untracked
claim_ceiling: scratch_diagnostic_le3q_tower_carrier_and_pins_relative
promotion_allowed: false
formal_admission_allowed: false

## Bottom Line

VERDICT: PASS_WITH_CAVEATS for the local scratch diagnostic.

The headline "EXACT all-cut tower = EMPTY at <=3Q" is real under the packet's declared exact predicate: frozen lower-rung registry-coordinate equality for the single and pair marginals, checked independently on all three 3Q cuts. I did not find a tolerance bug, id-space bug, or representation mismatch inside that declared predicate. The empty exact tower is structural for this carrier: the independently gridded lower-rung registries do not contain the exact all-cut marginal tuple needed by any 3Q survivor.

Claim ceiling: this is not a full-density theorem saying no 3Q marginal ever equals any lower-rung density matrix. Some pair marginals do equal stored lower-rung density rows. The accepted finding is narrower and sharper: all-cut exact compatibility is empty for the packet's frozen carrier-and-pin registry relation, while the probe quotient rescues 465 rows.

## Verdict Table

| Item | Verdict | Audit finding |
|---|---:|---|
| Exact all-cut tower | PASS | Recomputed 0 exact rows, 545 exact orphans. |
| Probe all-cut tower | PASS | Recomputed 465 rows, 80 probe orphans. |
| Probe multiplicity | PASS | Recomputed total 1,169,687,040 as 465 * 136^3. |
| Tripartite anchor | PASS | One anchor, `rhoabc_8325d0b8f1ead2ed0044791a`, multiplicity 2,515,456 = 136^3. |
| <=2Q regression | PASS | Reproduced exact/product and probe counts from the <=2Q root-axiom packet. |
| Scrambled control | PASS_WITH_NOTE | Red control holds, but it is asymmetric: A|BC scramble 0/544, B|AC scramble 24/544. |
| G.2a boundary | PASS | Builder/auditor file boundary is correct; this audit file declares independent/read-only status. |
| Strict green | PASS_WITH_CAVEAT | Packet validator is green, but one helper source-lock hash is stale against the live checkout. |

## Exact=0 Decision

The exact predicate is not raw density-matrix equality. It is explicitly defined as:

- 1Q exact: scaled Bloch coordinate lookup against the frozen 1Q survivor registry (`gcm_nesting_tower_le3q_v0_common.py:382-399`).
- 2Q exact: equality of the pair of local-pin scaled Bloch coordinates against the frozen 2Q registry (`gcm_nesting_tower_le3q_v0_common.py:406-430`).
- cut compatibility: single exact and pair exact must both resolve for each cut (`gcm_nesting_tower_le3q_v0_common.py:507-536`).
- all-cut compatibility: all three cuts must pass before a family row is emitted (`gcm_nesting_tower_le3q_v0_common.py:541-558`).

Independent recomputation of all 545 3Q survivors returned:

```text
exact_all_cut_compatible_3q_count: 0
exact_all_cut_compatible_family_count: 0
exact_all_cut_orphan_3q_count: 545
probe_all_cut_compatible_3q_count: 465
probe_all_cut_compatible_family_count: 1169687040
probe_all_cut_orphan_3q_count: 80
```

The decisive product-lift hand check is the C single marginal. Across all 544 product lifts:

```text
C_SINGLE_EXACT_HITS_PRODUCTS: 0 of 544
C_SINGLE_PROBE_HITS_PRODUCTS: 544 of 544
C_AB_PAIR_SOURCE_EXACT_PRODUCTS: 544 of 544
PRODUCT_EXACT_FAILED_CUT_SETS:
  A|BC|B|AC|C|AB: 288
  C|AB: 256
```

So even the 256 product lifts that pass A|BC and B|AC exact still fail the all-cut exact tower on C|AB because their C single coordinate is the local pin `[0, 0, 2]`, which is not present as an exact 1Q lower-rung survivor coordinate. That is the same kind of root-axiom issue as <=2Q, but stricter at <=3Q because all three cuts must close at once.

Important caveat: when I compared full stored density matrices rather than the packet's declared coordinate registry relation, some 2Q pair marginals did hit lower-rung density rows. Therefore, the correct claim is "exact-empty in the declared all-cut frozen registry-coordinate tower", not "no lower-rung density equality exists anywhere."

## Product Samples

I recomputed partial traces for product-lift samples and checked each cut by hand against lower-rung exact/probe relation tables:

| sample | source 2Q survivor | exact failed cuts | probe failed cuts | audit note |
|---:|---|---|---|---|
| 0 | `gcm2qsurv_d0e240413ea2b2160413` | A|BC, B|AC, C|AB | none | product lift fails exact all-cut but probe-resolves. |
| 1 | `gcm2qsurv_b5e1c316d2c5573fac82` | C|AB | none | product lift shows the minimal exact failure: C single exact miss only. |
| 10 | `gcm2qsurv_2d8bedce34384771ea7b` | A|BC, B|AC, C|AB | A|BC, B|AC | product lift is one of the 80 probe orphans. |
| 528 | `gcm2qsurv_395f873a062ac2f6a173` | A|BC, B|AC, C|AB | none | boundary-lift sample still probe-resolves. |

These samples support the aggregate finding: exact=0 is not caused by one malformed row or one orphan class.

## Probe Tower And Multiplicity

The packet's multiplicity rule is:

- per cut: `len(single ids) * len(pair ids)` (`gcm_nesting_tower_le3q_v0_common.py:465-474`);
- family: product of the three cut multiplicities (`gcm_nesting_tower_le3q_v0_common.py:541-558`).

Every probe-compatible row had the same cut multiplicity tuple:

```text
A|BC: 136
B|AC: 136
C|AB: 136
family_multiplicity: 136 * 136 * 136 = 2,515,456
```

Therefore:

```text
probe rows: 465
probe family count: 465 * 2,515,456 = 1,169,687,040
product probe family count: 464 * 2,515,456 = 1,167,171,584
tripartite anchor family count: 1 * 2,515,456 = 2,515,456
```

For the single tripartite anchor `rhoabc_8325d0b8f1ead2ed0044791a`, each cut had 2 single probe ids and 68 pair probe ids, giving `2 * 68 = 136` per cut and `136^3 = 2,515,456` for the anchor.

## Replication Of <=2Q Root-Axiom Finding

This is a strengthening, not a literal same-count replication.

The <=2Q packet had an exact product sub-tower: exact-compatible 2Q count 256, exact orphans 288, probe-compatible 2Q count 464. This <=3Q packet preserves the root-axiom pattern that probe-relative compatibility rescues rows the exact relation loses, but the all-cut exact result is now empty because the <=3Q law requires simultaneous closure over A|BC, B|AC, and C|AB.

That is an explained discontinuity:

- <=2Q: exact retains the product sub-tower.
- <=3Q: exact loses even products because the third cut introduces the C single local-pin mismatch against the independently gridded 1Q registry.
- Probe: quotient matching remains nonempty and admits 464 product lifts plus the one tripartite anchor.

The nesting law being tested is the inverse-limit compatibility law across subsystem survivor sets (`system_v6/receipts/nesting_law_final_object_spec_20260612.md:15-23`), and <=3Q is explicitly listed as the next testable tower (`system_v6/receipts/nesting_law_final_object_spec_20260612.md:48-52`).

## Scrambled Control

The scrambled-pairing control is red but not symmetric:

```text
correct C|AB source match: 544 / 544
scrambled A|BC source match: 0 / 544
scrambled B|AC source match: 24 / 544
```

The 24 B|AC scrambled matches are real partial-structure collisions, not a full control collapse. They occur where the scrambled B|AC coordinate pair still collides with lower-rung source coordinates under the fixed C-pin/product-lift structure. The control still kills the intended false pairing sharply, but future claims should say "scrambled control is red with residual 24/544 B|AC collisions", not "all scrambled pairings go to zero."

## G.2a, Lineage, And Coordinates

G.2a is satisfied for this audit boundary:

- The standards codex requires every audit to state a freshness tier (`system_v6/receipts/audit_standards_codex_v1.md:120-126`).
- Builder files must not author `audit_verdict.md`, and validators must accept only independent/fresh/read-only audit headers after audit time (`system_v6/receipts/audit_standards_codex_v1.md:152-180`).
- The local validator delegates that boundary check to `builder_audit_boundary_errors(...)` (`validate_gcm_nesting_tower_le3q_v0.py:142`), and the header gate accepts independent/fresh/read-only audit declarations (`scripts/builder_audit_boundary.py:21-38`, `scripts/builder_audit_boundary.py:54-66`).

Lineage/provenance spot checks:

```text
<=2Q source result last commit: 28052037d
3Q parent source result last commit: 5544ad21c
nesting law spec last commit: afe7aa57b
audit standards last commit: 443e474b2
builder audit boundary helper last commit: aed311e85
gcm_substrate_check.py live last commit: e7a56e517
```

Caveat: the packet's helper source-lock for `scripts/gcm_substrate_check.py` records an older commit/hash than the live checkout. The live helper still passed the positive/negative payload checks I reran, and the packet validator remains green, but consumers should cite the helper-lock drift as a caveat rather than treating the stored lock as fully current.

## Verification Commands

Commands were run read-only except for writing this audit file.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
  import gcm_nesting_tower_le3q_v0_common
  load 1Q/2Q/3Q sources
  build_tower(...)
  summarize_counts(...)
```

Result: recomputed exact=0, probe rows=465, probe family count=1,169,687,040, product probe family count=1,167,171,584, tripartite anchor family count=2,515,456.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
  recompute product-lift partial traces and exact/probe cut failures
```

Result: all 544 product lifts miss C single exact; 544/544 hit C single probe; 256 fail exact only on C|AB and 288 fail exact on all three cuts.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
  recompute probe rows and family multiplicities
```

Result: all 465 probe-compatible rows have cut tuple `(136, 136, 136)` and family multiplicity `2,515,456`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
  import validate_gcm_nesting_tower_le3q_v0.validate_packet
```

Result before this file was written: `ok: true`, zero errors. A post-write import check should remain green because this header declares independent/read-only audit status.

## Citation Rule For Downstream Use

Downstream summaries may cite:

1. This audit verdict for the adjudicated claim: exact-empty at <=3Q is structural under the declared frozen registry-coordinate all-cut relation.
2. `gcm_nesting_tower_le3q_v0_common.py:382-430`, `:465-474`, and `:507-558` for the exact/probe predicate and multiplicity rule.
3. The recomputed counts above for the 465 probe rows and 1,169,687,040 family multiplicity.

Downstream summaries must not cite this packet as:

1. A proof of full-density exact emptiness.
2. A promoted tower, admitted object, or bridge/axis-level result.
3. A symmetric zero-scramble control.
4. A helper-lock-current packet until the stale `gcm_substrate_check.py` lock is repaired or explicitly waived.

## Final Ceiling

Accepted claim:

```text
At <=3Q, under the independently gridded frozen survivor registries and the packet's carrier-and-pin exact relation, the all-cut exact nesting tower is empty: 0 exact-compatible rows and 545 exact orphans. The probe quotient rescues 465 rows, with total all-cut probe family multiplicity 1,169,687,040, including 464 product lifts and one tripartite anchor.
```

Rejected upgrades:

```text
formal admission
promotion beyond scratch_diagnostic
full-density exact no-go theorem
G2/geometry layer claim
axis-level bridge claim
```
