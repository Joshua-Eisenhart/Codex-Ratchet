# Audit verdict - round3_s2_alias_pass_v0

Bottom line: ACCEPTED WITH NAMED CAVEATS as a bounded
`scratch_diagnostic` S2 light-symbolic alias pass. The packet does not repeat
the MUB failure: the claim path uses exact SymPy canonical tuple comparison
over rationals/surds, not numeric-threshold closeness wearing symbolic labels.
The result may be cited for phase-1 S2.R3.0-S2.R3.4 classification and for the
fact that S2.R3.5 remains the only queued heavy-local S2 row. It must not be
cited as S2 uniqueness, heavy-local completion, or full independent
Julia/SymPy canonical-tuple parity.

## Verdict

- Classification remains `scratch_diagnostic`.
- `promotion_allowed=false` and `formal_admission_allowed=false` are correct.
- The envelope is schema-conforming: `schema_version=three_engine_sim_result_v1`.
- Honest mode `julia_canon_plus_jax_diagnostic` is legitimate for this packet:
  there is no graph/network/autograd/tensor claim path, so PyTorch omission is
  valid when the generic validator is run without `--require-pytorch`.
- Candidate verdicts are accepted with the R3.1 vocabulary caveat below:
  - `S2.R3.0_committed`: anchor.
  - `S2.R3.1_large_gauge_chi_shift`: convention-pinned exclusion /
    convention-relative neighbor, not an intrinsic geometry kill.
  - `S2.R3.2_same_curvature_shifted_holonomy`: excluded by leaf holonomy
    spectrum.
  - `S2.R3.3_endpoint_chern_preserving_bump`: excluded by curvature density
    and annular Stokes.
  - `S2.R3.4_two_leaf_holonomy_match`: excluded by expanded leaf holonomy
    vector.
  - deliberate alias control: alias.
  - wrong-sign control: excluded by first teeth row.

## Canonical-Form Reality

The alias gate is exact-symbolic on the real claim path. The Python/JAX lane
defines candidates with `sp.Rational(...)` and `sp.sqrt(3)`, reduces canonical
tuples with `sympy.simplify`, `trigsimp`, and `factor`, and compares tuple
equality/hash equality before battery rows. I found no `evalf`, `isclose`,
float tolerance, or threshold-based alias decision in the packet source.

The deliberate alias control reduces exactly:

```text
2*cos(eta)^2 - 1 = cos(2*eta)
under x = cos(2*eta), canonical gap = 0
```

The anchor alias class in the JAX result contains exactly:

```text
S2.R3.0_committed
control.anchor_self
control.alias_reparameterized_committed
```

So the MUB canonical-form lesson is honored for the accepted claim: alias means
exact canonical tuple equality, not numerical closeness.

## Teeth-Row Fidelity

Fresh scratch recomputation over exact SymPy values confirmed the key rows.

For `S2.R3.2_same_curvature_shifted_holonomy`, with `c=1/4`, the leaf holonomy
gap is exact and nonzero:

```text
eta=pi/4: anchor=0, candidate=-1/4, gap=-1/4
eta=pi/12: anchor=-sqrt(3)/2, candidate=-(1 + 2*sqrt(3))/4, gap=-1/4
```

For `c=-1/4`, the corresponding gap is `+1/4`. This is the registry-named
leaf-holonomy-spectrum row, and it separates before any Chern/topology-only
claim.

For `S2.R3.4_two_leaf_holonomy_match`, the packet's intended subtlety is real.
With `epsilon=1/5`:

```text
eta=pi/6: anchor=-1/2, candidate=-1/2, gap=0
eta=pi/4: anchor=0, candidate=0, gap=0
eta=pi/12: gap=(-3 + sqrt(3))/20, nonzero
eta=pi/3: gap=-1/10, nonzero
```

With `epsilon=-1/5`, `pi/6` and `pi/4` still coincide, while the off-anchor
leaves separate exactly. This supports the expanded-leaf-holonomy-vector
verdict rather than a premature alias/co-survivor label.

## R3.1 Boundary

The packet's R3.1 math shows a pinned lifted-holonomy separation:

```text
g_chi= 1/2: holonomy gap at pi/12 = -1/2; at pi/4 = -1/2
g_chi=-1/2: holonomy gap at pi/12 =  1/2; at pi/4 =  1/2
```

Under the registry's canonical tuple, including the pinned lifted holonomy and
cover-period convention, R3.1 is not an exact alias. However, the registry also
calls this family a `near-alias / convention-neighbor` and says same-curvature
shifted lifted holonomy requires explicit classification before the battery.

Adjudication: cite R3.1 as `excluded-under-pinned-lifted-holonomy-convention`
or `convention-pinned exclusion`. Do not cite it as an intrinsic physical
exclusion. If a future argument changes or removes the lifted-holonomy pin,
R3.1 must be reopened as a convention-relative alias/neighbor question.

## Backend And Solver Caveats

Named caveat 1 - Julia lane depth:
The Julia lane did not independently rebuild the full S2 canonical tuple
including the surd holonomy vector and annular flux vector. It rebuilds
polynomial/derivative rows and carries expected verdict labels. It does not
read the JAX result, and the envelope's verdict-match hash is real provenance
for matching verdict maps, but it is not proof of full independent
Julia/SymPy canonical-tuple parity.

Named caveat 2 - SMT binding depth:
z3, cvc5, and Julia Z3 have the expected UNSAT positive polarity and SAT flip
controls. The rational witness constants match fresh exact recomputation. The
solver layer should still be cited as a finite rational nonzero-witness
cross-check, not as an independently extracted full canonical tuple proof,
because the solver witness table is constant-bound inside the proof functions.
Surd comparisons remain CAS-backed.

Named caveat 3 - validator freshness:
I freshly reran the generic read-only validator:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py \
  system_v6/sims/round3_s2_alias_pass_v0/results/round3_s2_alias_pass_v0_envelope_results.json
```

It returned:

```text
{"ok": true, "result_json": "system_v6/sims/round3_s2_alias_pass_v0/results/round3_s2_alias_pass_v0_envelope_results.json"}
```

I did not rerun `validate_round3_s2_alias_pass_v0.py` in place because that
script writes `results/round3_s2_alias_pass_v0_validator_results.json`, and the
audit instruction allowed only this verdict file as a repo write. The existing
validator result on disk reports `ok=true`, `validator_ok=true`, and no errors.

## Stop Rule And Phase-2 Disposition

The stop rule blocks any heavy battery over R3.1-R3.4: the light-symbolic pass
already classifies them, and there are zero open light-symbolic co-survivors.
There is no count-inflation justification for rerunning heavy rows against
those excluded light candidates.

The only warranted phase-2 S2 work is the predeclared heavy-local registry row:

```text
S2.R3.5_boundary_conditioning_variant
```

So the correct disposition is: no broad S2 heavy-local pass; queue only the
narrow S2.R3.5 cover/conditioning-validity packet, with no implication that
R3.0-R3.4 need or earned heavy-local reruns.

## Future-Citation Rule

Future citations may say:

```text
round3_s2_alias_pass_v0 accepted as scratch_diagnostic phase-1 S2
light-symbolic alias/exclusion evidence: exact canonical-form alias control
passed; R3.2/R3.3/R3.4 excluded by registry teeth rows; R3.1 excluded only
under the pinned lifted-holonomy convention; no open light-symbolic
co-survivors; S2.R3.5 remains queued heavy-local.
```

Future citations must not say:

```text
S2 is unique; R3.1 is intrinsically killed; heavy-local S2 is complete;
PyTorch evidence exists; Julia independently proved the full canonical tuple;
SMT proved the surd tuple; numeric closeness established alias status.
```

## Route-Truth Note

Wizard v4.2 Max Assembly was partial for this audit. The available subagent
tool's runtime contract permits spawning only when the user explicitly asks for
subagents/delegation, so no worker plurality is claimed here. Evidence is from
direct repo inspection, fresh scratch exact recomputation, the read-only generic
validator rerun, and existing packet result files.
