# Results

Status: `PREREGISTERED_CONFIRMATION_RED`

## What Ran

- 2,500 size-two through size-four observation subsets were screened on 128
  frozen train-only design fixtures.
- The top 32 per size were exact-scored independently in JAX and Julia.
- The controller independently rederived the shortlists and shortlist-relative
  winners: S2 `[0,1]`, S3 `[0,1,9]`, S4 `[3,5,9,12]`.
- Separate confirmation sources reconstructed all 325 validation pair-orbit
  fixtures and exact-scored each winner plus hash-order and
  system-identification baselines: 2,925 fixture/design records per runtime.
- All 2,925 shared record projections agree field by field across JAX and
  Julia. The controller independently recomputed every primary gate.

## Validation Result

| Size | Global coverage | Worst fixture | Disjoint global | Diversity fixtures | System identified | Passed |
|---:|---:|---:|---:|---:|---:|:---:|
| 2 | 73.38% | 20.98% | 73.09% | 279/325 | 0 | no |
| 3 | 76.43% | 20.98% | 76.15% | 277/325 | 0 | no |
| 4 | 80.73% | 20.98% | 80.41% | 165/325 | 38 | no |

All three sizes fail the every-fixture diversity requirement, 95% global
coverage, 80% fixture floor, 90% query-disjoint global coverage, and 70%
query-disjoint fixture floor. S2 is exactly the hash-order baseline and also
fails baseline separation. S4 additionally violates the zero-system-ID gate.

```text
passing_sizes = []
candidate_exists = false
robust_design_family = false
test_block_opened = false
```

## Interpretation

The search machinery is real finite experimental design, but the proposed
fixed global subsets do not create the desired consensus-without-identification
window. Adding observations raises aggregate identifiability while destroying
model and partition diversity; size four already uniquely identifies 38 hidden
systems and still leaves a worst fixture near 21% coverage.

The next admissible design family must change the experiment class, not relax
the gate after seeing this result. Candidate directions are adaptive
relation-directed interventions, per-fixture or policy-conditioned sensing,
and sequential distinguishing experiments with an explicit cost budget.

No PyTorch learner was run because the target measurement design failed before
learning admission.
