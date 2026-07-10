# ECA Observation Object Identifiability V0 Results

## Accepted Result

`EXACT_CROSS_RUNTIME_ECA_PARTIAL_OBSERVATION_OBJECT_IDENTIFIABILITY_CENSUS`

This is a `scratch_diagnostic` exact finite census. It is not formal admission,
learning success, or a general perception result.

Julia and JAX independently recomputed all 32,640 unordered rule-pair stable
partitions, all compatible ordered rule-pair version spaces, and every query
consensus. Their 2,655 fixture-budget records match fieldwise across all 20
frozen fields. The common ledger SHA256 is
`4ca51e158058737a30fd994943deb8cfff0bcd1b1b9c141639f34b985255b5cc`.

## Budget Census

| Budget | Global identifiable | Worst fixture | System identified | Qualifying fixtures | Consensus without ID | Regime |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 69.4694% | 20.9838% | 0/531 | 531 | 3,554,550 | information missing |
| 2 | 77.6759% | 20.9838% | 0/531 | 531 | 3,974,454 | information missing |
| 4 | 99.5457% | 69.7385% | 461/531 | 0 | 0 | information missing and system-ID dominated |
| 8 | 100% | 100% | 531/531 | 0 | 0 | system identification |
| 16 | 100% | 100% | 531/531 | 0 | 0 | system identification |

At budgets 1 and 2, all 531 fixtures retain at least eight effective unordered
hypotheses and at least two distinct stable relations. The identifiable target
is also balanced: same/different fractions are 30.43%/69.57% at budget 1 and
27.33%/72.67% at budget 2. Those budgets nevertheless fail both the 95% global
coverage gate and the 80% per-fixture floor.

Budget 4 reaches 99.55% global coverage, but its worst fixture remains at
69.74%; 86.82% of fixtures have already collapsed to singleton ordered rule
pairs. Budgets 8 and 16 identify every hidden ordered rule pair. None of the
five frozen budgets is a consensus candidate, so no consecutive pair exists.

## Verdict

`perception_like_regime_admitted = false`

`earliest_admitted_budget = null`

The observation schedule crosses directly from underdetermined object
relations to dynamics identification. It does not expose a broad, reliable
window where object relations are fixed across genuinely different compatible
dynamics. Training on this packet is therefore blocked: early-budget targets
are not sufficiently identifiable, while late-budget targets would primarily
reward system identification.

## Exact Scope

The result covers the preregistered periodic nine-bit ECA carrier, 531
symmetry-representative test fixtures, five cumulative action-labelled
trajectory budgets, and 9,636 same-initial-probe queries per fixture. It does
not cover all possible observation designs or all 2,016 raw test-block pairs.

The next valid move is a new preregistered observation-design search whose
objective is to widen consensus without collapsing the version space. It must
use untouched families for any later learner benchmark.
