# LevOS Extraction for a Lean Standalone ConstraintBox

This is a source/evidence map, not a claim that LevOS has been integrated.
The CR-side audit warns that older `claimgate-steering consume` and
orchestration paths were branch-only or deleted.  The active rebuild seam was
reported as an external patch plus Lev `core/eval`.

## Mechanisms worth retaining

| Lev mechanism | ConstraintBox implementation target | Pack status |
|---|---|---|
| harness-fired verifier | controller automatically runs configured evaluator | implemented in small form |
| GateRun completeness | command, exit, stdout, stderr and artifact hashes | implemented in worker profile |
| durable event log | append-only decision/branch ledger | implemented locally |
| evaluator packs | controller-owned task profiles | implemented |
| evidence references | content-addressed inputs and outputs | implemented |
| plugin boundary | CR, Sim and Lev attach through adapters | specified |
| trigger dispatch | events automatically fire maintenance/evaluation | open |
| one decision authority | workers observe; controller decides | implemented |
| schema admission | strict closed intake and finite-number policy | partially implemented |
| replay grading | rerun profile under same policy and source | open |
| near-duplicate finding | identify repeated/renamed proposals | optional/open |
| lifecycle vocabulary | declared, available, exercised, ready, stale | specified |

## Material deliberately not imported

| Surface | Reason |
|---|---|
| lost branch-only steering command | not a current stable dependency |
| full FlowMind architecture | parts reported as boot stubs/aspirational |
| full poly/context graph | too large for present function |
| declared ABAC C3-C5 | audit says not to depend on enforcement |
| inert term fence or nominal immutability | not demonstrated |
| ratchet-admission flow stub | replace with ordinary tested transitions |
| private Lev internal package imports | would destroy standalone operation |

## Adapter direction

```text
ConstraintBox standalone result
    -> external Lev evaluator-pack adapter
    -> Lev host observes/recomputes
```

LevOS is not the root of ConstraintBox policy.  ConstraintBox is not permitted
to write into a Lev checkout.  A future Lev developer can adopt the adapter or
equivalent evaluator pack without accepting the CR research stack.
