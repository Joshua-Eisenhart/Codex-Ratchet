# Independent Audit Verdict - ecd04_record_conditioned_navigation_v0

Audit mode: read-only audit except this verdict file. Freshness tier: `TIER-2`
results-available audit; no prior packet audit existed, but source/results/build
card/builder self-assessment were available before the equalizer recompute.

Bottom line: `SURVIVES_v0` is rejected as stated. Verdict species:
`BY_CONSTRUCTION / partition-access gap`. The packet's reported margin is real
for its implemented comparison, but it disappears under the required ECD.06-style
equalizer: grant the baseline the same committed typed-memory partition
read-only, and the baseline ties the engine exactly.

Claim ceiling remains `scratch_diagnostic`, `promotion_allowed=false`,
`formal_admission_allowed=false`. This is not the second earned engine
capability; `order-programmability` remains the only earned capability row from
this ECD wave.

## Decisive Equalizer

The implemented engine policy builds a three-class typed partition from the
shared action-success relation:

- `G0_only = [2, 5, 30]`
- `G2_only = [7, 11, 21]`
- `shared_return = [0, 3, 15, 16, 17, 31]`

The reported engine row succeeds on all 12 branch inputs with
`record_class_count=3`, so its cost is `ln(3) = 1.0986122886681098`.

The reported baseline winner is full branch identity: it uses the same branch
to action map, succeeds on all 12 branch inputs, and pays
`record_class_count=12`, so its cost is `ln(12) = 2.4849066497880004`. The
reported margin is therefore `ln(12) - ln(3) = ln(4) =
1.3862943611198906`.

The required equalized baseline is: same branch/action environment, same success
gate, same metric, same action map, but with the engine's typed partition
available read-only. It succeeds on all 12 branch inputs with
`record_class_count=3` and cost `ln(3) = 1.0986122886681098`.

Equalized margin: `ln(3) - ln(3) = 0.0`. That means the survival is partition
access, not a demonstrated navigation capability.

## Tooth Results

1. Partition status: the typed partition is not adjudicated as protected engine
architecture in this packet. It is a structuring of the disclosed record/action
space, and the baseline profits from it equally. The source itself lets the
baseline full-identity row use the engine action map branch-by-branch; the
withheld advantage is only the coarse typed grouping and its lower record cost.

2. Source recompute: the reported success rows and cost gap recompute from
`ecd04_record_conditioned_navigation_v0_common.py`. The branch universe has 12
inputs, QIT cost is `ln(3)`, baseline full-identity cost is `ln(12)`, and both
reported best rows have target success `1.0`.

3. Ledger lineage: the record-cost accounting is finite counting entropy over
record classes. I found no double-counting in the implemented metric: one record
entropy term is charged. But the audited Szilard fixture is lineage/anchor
support, not a load-bearing computation of the gap; the live gap is just
`ln(class_count)` over this packet's branch partition.

4. Record-erasure control: the engine erasure row degrades from success `1.0` to
`0.75`. The symmetric equalized-baseline erasure row degrades identically to
`0.75`. This supports "records matter"; it does not rescue a capability
separation.

5. Baseline search strength: insufficient for survival. The implemented baseline
search includes fixed `G0`, fixed `G2`, full branch identity, and a parity-sized
fixture row. It does not include the mandatory equalized typed-partition
baseline. The positive predicate is mechanically present, but the searched class
is missing the killer row.

6. Parity gate: the packet's information-parity manifest is equal on both sides:
start cell, target terminal class, branch universe, action success sets, graph
edges, and terminal classes are shared. That parity makes the missing partition
equalizer more decisive, not less.

7. Fair metric: the success-gated success-weighted record cost is the right
protection against trivially cheap non-navigation. Failed rows are not rewarded.
Under that same fair metric, the equalized baseline ties.

8. Identity leak, G.2a, and dropped-half: G.2a is wired through the boundary
helper and the validator. Dropped-half rows succeed on both sides in the emitted
packet. The no-identity-leak row is reported with identity-inclusive accuracy
`1.0` and identity-excluded best accuracy `0.75`; I did not treat that row as
load-bearing for survival because the equalizer already kills the claim.

## Backend And Validator Checks

The three-engine packet is green for the reported comparison, not for the
equalizer question. JAX and PyTorch recompute from the common source object;
Julia recomputes the finite row locally from the hardcoded branch/action sets.
The lanes agree on the reported scaled margin `1386294`.

Read-only checks run:

- In-memory packet validator call: `ok=true`, `error_count=0`.
- Generic strict three-engine validator:
  `scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent ...envelope_results.json`
  returned `ok=true`.
- Non-writing pytest subset:
  `2 passed, 2 deselected`.

I did not run the packet validator main or full pytest because those paths write
repo result files and/or temporarily write `audit_verdict.md`, which would
violate the audit write scope.

## Registry Row Language

Use this row:

`ECD.04 record-conditioned basin/Landauer navigation: v0 survival rejected as
stated - BY_CONSTRUCTION / partition-access gap. The packet computes a real
success-gated record-cost gap only when the baseline pays full branch identity
(`ln(12)`) while the engine pays its committed typed-memory partition (`ln(3)`).
The required equalizer grants the baseline that same typed partition read-only;
the equalized baseline succeeds with cost `ln(3)` and ties the engine exactly.
Record-erasure degrades both engine and equalized baseline identically to `0.75`
success. No earned ECD.04 capability, no QIT-engine admission, no basin theorem,
no physical Landauer/thermodynamic claim.`

## v1 Contract

Do not rebuild v1 until the partition question is pinned before execution:

1. Either prove and pre-register the typed-memory partition as protected engine
architecture, with a falsifier that would demote it to shared information, or
include the read-only typed-partition equalizer as a fair baseline candidate.
2. The fair baseline class must include at least: no-record fixed actions,
parity/coarse records, full branch identity, and same typed partition read-only.
3. Survival requires positive margin after the equalizer. A tie or baseline win
is an accepted bounded death.
4. Keep the same success-gated metric, symmetric erasure check, dropped-half
rows, and G.2a boundary.
5. State the scope as this carrier/target/RETURN-row family only; no basin,
physical Landauer, thermodynamic heat/work/bath, manifold, physics, or
QIT-engine admission follows from v1 either way.
