# Audit verdict - axis0_contender_sweep_v0

Bottom line: GENUINE-WITH-CAVEATS as a bounded `scratch_diagnostic`
phase-1 exact/light Axis-0 contender sweep. The anchor alias and the three
light exclusions are accepted. The seven CP.3-CP.9 rows are not accepted as
computed or known co-survivors; cite them as named `open + queued-heavy`
contender families, or at most `light-co-survivor/open` only when the same
sentence says their 33-cell adapters and heavy teeth did not run.

Expectation-1 adjudication: Axis-0 is currently a FAMILY pending the heavy
pass, not unique-up-to-alias and not "THE Axis-0 readout"; the family consists
of the accepted anchor alias class plus seven named open queued contender
families whose heavy rows must decide whether they survive.

## Verdict

- Repo vocabulary: `GENUINE-WITH-CAVEATS`.
- Classification remains `scratch_diagnostic`.
- `promotion_allowed=false` and `formal_admission_allowed=false` are correct.
- Schema is valid for the scoped result: `schema_version=three_engine_sim_result_v1`.
- Honest mode is `julia_mirror_plus_jax_exact_light`: Python/JAX-role exact
  Fraction/networkx/z3/cvc5 lane plus a narrow Julia mirror lane. PyTorch is
  correctly omitted because no tensor, graph, autograd, or neural claim path is
  scoped.
- Do not cite this packet as Axis-0 admission, uniqueness, full strict-source
  backed evidence, PyTorch evidence, heavy-pass completion, or known
  co-survivors.

## Alias Reality

The anchor alias path is accepted. Fresh scratch recomputation found the
deliberate sign-flip/monotone-control alias true under the registry canonical
tuple comparison:

```text
alias_relation(anchor_recompute, sign_flip_recompute) = true
matched fields = carrier_state_object_id, cell_order, zero_set, positive_set,
negative_set, rank_partition, generator_stability_signature
```

The stored canonical hashes for the anchor and sign-flip controls differ
because the hash payload includes candidate/convention metadata. That is not a
counterexample to alias status; the alias procedure compares the reduced
canonical tuple fields before teeth rows. The MUB lesson held: the deliberate
variant did not inflate the independent tested count.

## Exclusions

Accepted light exclusions:

```text
A0.CP.1_unweighted_edge_gradient_count_balance
verdict: excluded-by-Hamming-disagreement-from-committed-sign-vector
hamming disagreement count: 11
first disagreement: cell 1, anchor -1 vs candidate 0

A0.CP.2_incoming_vs_outgoing_gradient_current
verdict: excluded-by-source-sink-imbalance
hamming disagreement count: 25
incoming_equals_global_sign_reversal: false
first disagreement: cell 3, anchor -1 vs candidate +1

A0.CP.10_transition_graph_in_out_degree_imbalance
verdict: excluded-by-degree-teeth-wrong-distinction
hamming disagreement count: 25
first disagreement: cell 0, anchor -1 vs candidate +1
reason: pure distinct_successor_count - distinct_predecessor_count structural row
```

CP.10's wrong-distinction verdict is computed enough for this light pass: the
raw value is the registry-named degree baseline on the same carrier, and the
different-distinction control fires. Caveat G2 below still applies: the broader
Axis-0 distinction-boundary predicate is not fully operationalized for the
heavy rows.

## Seven Heavy Rows

The packet's bare row verdict `co-survivor-open` is too strong if quoted without
its boundary. The rows did not compute 33-entry vectors and did not run heavy
teeth:

```text
vector_status = not_computed_adapter_required
teeth_run = false
queued_heavy = true
```

Accepted citation label for each:

```text
A0.CP.3_entropy_gradient_sign - open + queued-heavy; Which-entropy teeth pending
A0.CP.4_pauli_participation_feedback_polarity - open + queued-heavy; Adapter teeth pending
A0.CP.5_flux_direction_annular_or_edge_current - open + queued-heavy; Flux teeth pending
A0.CP.6_flux_continuity_n3_n4_current_sign - open + queued-heavy; Continuity teeth pending
A0.CP.7_lyapunov_descent_direction - open + queued-heavy; Functional teeth pending
A0.CP.8_hopfield_energy_gradient_sign - open + queued-heavy; Retrieval teeth pending
A0.CP.9_holonomy_spectrum_sign - open + queued-heavy; Holonomy teeth pending
```

I could not recompute CP.3 entropy-gradient or CP.7 Lyapunov vectors because
the packet intentionally has no source-backed 33-cell adapters for them. That
is acceptable for an open queue result, but it blocks any "computed
co-survivor" or "known co-survivor" language.

## Backend And Tool Caveats

G1 - heavy-row vocabulary:
Bare `co-survivor-open` overstates the CP.3-CP.9 evidence. The envelope's
phrasing, "open+queued by heavy/adapter guard", is the correct future-citation
surface.

G2 - distinction-boundary operationalization:
CP.10 is correctly killed as a pure degree/order row in this light pass. The
registry's later correction says future sweeps need a positive computable
predicate for "reads Axis-0" before classifying adaptable heavy probes. This
packet does not supply that predicate for CP.3-CP.9.

G3 - Julia depth:
The Julia lane is a real mirror for the scoped light counts: it reads the
committed anchor envelope, recomputes CP.1/CP.2/CP.10 hamming counts, and binds
the verdict table through Z3.jl. It is not a full independent Julia
implementation of canonical forms, heavy adapters, or all 33-entry vector
payloads.

G4 - strict source-backed tool claim:
Plain validator, source-backed validator, and tool-intent validator pass, but
`--strict-source-backed` fails because `sympy` is declared load-bearing while
the source use is token-thin. Treat `sympy` as supportive unless a later patch
adds real source-level SymPy use or demotes the manifest claim.

G5 - SMT scope:
z3, cvc5, and Julia Z3 all bind computed verdict-table counts with SAT flip
controls. This is legitimate for the table shape and light-row witnesses. It is
not a proof of Axis-0 admission, full canonical-form equivalence, or heavy-row
survival.

## Verification

Fresh read-only checks run:

```text
validate_three_engine_sim_result.py envelope -> ok=true
validate_three_engine_sim_result.py --require-source-backed envelope -> ok=true
validate_three_engine_sim_result.py --require-tool-intent envelope -> ok=true
validate_three_engine_sim_result.py --strict-source-backed envelope -> ok=false; sympy source-token-thin
validate_three_engine_sim_result.py --require-pytorch envelope -> ok=false; engines.pytorch missing, expected for honest omission
pytest -q -p no:cacheprovider system_v6/sims/axis0_contender_sweep_v0/tests -> 6 passed
scratch recomputation -> alias control true; CP.1/CP.2/CP.10 counts match; z3/cvc5 UNSAT positives and SAT flip controls
```

I did not rerun the packet writer scripts or packet-local validator because
they rewrite result JSONs and this audit's write boundary allowed only this
verdict file.

## Future-Citation Rule

Future citations may say:

```text
axis0_contender_sweep_v0 accepted as GENUINE-WITH-CAVEATS scratch_diagnostic
phase-1 exact/light contender evidence: anchor self and deliberate alias
controls pass; CP.1, CP.2, and CP.10 are excluded by named light teeth with
exact witnesses; CP.3-CP.9 remain named open + queued-heavy contender families;
Axis-0 is currently a family pending the heavy pass.
```

Future citations must not say:

```text
Axis-0 is unique; CP.3-CP.9 are known co-survivors; entropy-gradient or
Lyapunov vectors were computed; THE Axis-0 readout is established; heavy local
teeth are complete; PyTorch evidence exists; strict-source-backed validation
passed; SMT proved Axis-0 admission.
```
