# Independent Audit Verdict - gcm_qca_runner_2q_v1

Audit mode: fresh read-only audit. Auditor: independent Codex audit. Freshness tier:
TIER-2 results-available plus no-write recomputation. The only authorized live repo
write for this audit was this `audit_verdict.md` file. No git add, commit, generated
result rewrite, validator-result rewrite, runner main, or pytest writer path was run.

## Bottom Line

VERDICT: GENUINE-INDEPENDENT-REFLECTION-INDEX / DRESSED-MIRROR-NOT-EARNED.

v1 repairs the 10bf57a1f tautology at the index-construction level: the
`reflected_L_spatial_to_R` row is built as independent spatial matrix conjugation,
`P_out @ U_L @ P_in^dagger`, and not by re-calling `brickwork_engine("right", ...)`.
Fresh no-write recomputation preserves the key index facts:

- `engine_L_flux_IN_left_O1`: `-2` log2-qubits/step.
- `engine_R_flux_OUT_right_O1`: `+2` log2-qubits/step.
- `reflected_L_spatial_to_R`: `+2` log2-qubits/step, matching R's index from the
  independent reflected operator.

But v1 does not earn a genuine mirror-conjugacy relation between L and R as bare
operators, and the dressed-conjugacy scan should not be cited as mirror proof. The
honest new operator fact is:

```text
bare reflected-L != R
max|diff| = 0.7728503990831611
phase-aligned max|diff| = 0.7730044893509423
```

So the correct citation is: independent spatial reflection flips the support-rank index
from L's `-2` to R's `+2`, while the bare reflected operator remains different from R.
The dressed scan is at most a packet-local local-circuit equivalence witness, not a
mirror-specific relation.

Claim ceiling remains `scratch_diagnostic; carrier-and-pins-relative`. No formal
admission, promotion, engine admission, runtime flux family closure, 3Q `J_ent`/`J_cut`,
finite-ring nonzero GNVW automorphism-class, bridge/axis/physics, or manifold claim is
earned.

## Dressing-Class Adjudication

The dressing class is not an arbitrary continuous local-unitary search. It is a finite
discrete family:

- 11 input candidates and 11 output candidates.
- 121 input/output pairs total.
- candidates are `identity`, full-chain onsite committed gates, packet-local brickwork
  layers, and daggers.
- global phase is aligned in the comparison metric.

That means the `~3e-16` fit is not the full `U(4)^3`-style "any index-matched operator
can be fitted" tautology. However, it is still too permissive for the mirror claim,
because the winning pair is exactly the constructor-layer cancellation:

```text
output_dressing = brickwork_L_dag
input_dressing  = brickwork_R
best diff       = 2.9893669801409083e-16
```

This is not pinned by a single physical reflection gauge. It uses the packet's own L and
R brickwork layers as free pre/post dressings and therefore removes the very local
brickwork distinction that makes bare reflected-L differ from R.

Decisive control result: the named non-mirror permutation control is not a valid dressed
negative. The stored packet only checks it bare. My no-write scan found:

```text
non_mirror_bare_vs_R = 0.7728503990831611
non_mirror_equals_reflected = 5.551115123125783e-17
non_mirror best dressed diff = 2.7755575615628914e-16
best dressing = brickwork_L_dag / brickwork_R
```

A broader 36-pair label-permutation sweep found 0 bare passes and 2 dressed passes. The
two dressed passes are the actual reflection and the packet's "translation-style"
non-mirror row. Therefore the dressing scan does not make everything pass, but it also
does not discriminate mirror from the packet's named non-mirror control. That is enough
to block the dressed result as genuine mirror evidence.

## What v1 Earns

Accepted:

- The old v0 constructor-swap tautology is repaired for the reflected-index row.
- `reflected_engine_rule()` constructs reflection by label permutation matrices and does
  not call `brickwork_engine`.
- Reflection is an involution: reflect twice returns original labels and matrix with
  `max_abs_diff = 0.0`.
- The independent reflected-L row has support ranks `right=16`, `left=1`, index ratio
  `4/1`, and signed log2 index `+2`.
- The original L/R rows still compute opposite indices: L `-2`, R `+2`.
- The v0 constructor-swap row is honestly retained as `BY_CONSTRUCTION`; its unitary hash
  is byte-identical to R.
- Stored and rebuilt validator function APIs pass no-write: `ok=true`, `errors=[]`.
- G.2a boundary is satisfied: builder surfaces set `no_builder_audit_verdict=true`, and
  this verdict declares an independent/fresh audit header.

Rejected:

- "L and R are bare mirror-conjugate operators."
- "The dressed scan proves a principled physical mirror relation."
- "The non-mirror control stays red under the same dressing scan."
- "The dressed relation can support promotion beyond scratch diagnostic."

## Fresh No-Write Evidence

Commands used the Makefile interpreter:
`/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`.

No-write recomputation summary:

```text
all_pass_recomputed_no_write = true
stored_validation_ok_no_write = true
rebuilt_validation_ok_no_write = true
stored_validation_errors = []
rebuilt_validation_errors = []
z3 contract negation = unsat
z3 same-sign mutation = unsat
cvc5 contract negation = unsat
cvc5 same-sign mutation = unsat
```

Target rows:

| rule | right rank | left rank | signed log2 | unitary hash role |
| --- | ---: | ---: | ---: | --- |
| `engine_L_flux_IN_left_O1` | 1 | 16 | -2 | independent L engine |
| `engine_R_flux_OUT_right_O1` | 16 | 1 | +2 | independent R engine |
| `reflected_L_spatial_to_R` | 16 | 1 | +2 | independent reflected L |
| `v0_constructor_swap_regression` | 16 | 1 | +2 | byte-identical to R by construction |

## Citation Rule

Allowed citation:

> `gcm_qca_runner_2q_v1` is a scratch-diagnostic, carrier-and-pins-relative 2Q QCA
> runner in which an independently reflected realized L operator, built by
> `P_out @ U_L @ P_in^dagger`, reproduces R's support-rank index `+2`, while L remains
> `-2`. The bare reflected-L operator is not equal to R (`max|diff| = 0.7728503990831611`).
> The old constructor-swap row is retained only as a `BY_CONSTRUCTION` regression.

Required caveat:

> The packet-local dressed scan finds a finite local-circuit equivalence, but it is not
> accepted as a mirror-specific relation because the same dressing also repairs the
> packet's named non-mirror permutation control.

Forbidden citation:

- "v1 proves genuine L/R mirror conjugacy."
- "bare reflected-L equals R."
- "the dressing scan is a principled small physical mirror gauge."
- "the non-mirror negative passed under dressing."
- "formal admission", "canonical promotion", "engine admitted", "runtime flux family
  confirmed", or "finite-ring nonzero GNVW automorphism-class invariant".

