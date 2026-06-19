# Audit verdict - round3_s6s7_alias_pass_v0

Bottom line: VERDICT `GENUINE-WITH-CAVEATS` as a bounded S6/S7
light-symbolic phase-1 alias pass. Cite it only for the S6/S7 anchor
self-classification, the deliberate reparameterized cycle alias control, the
round-2 path far-control dying on the `closed-cycle graph row`, and the
preserved phase-2 `open + queued-heavy-local` disposition for all five
non-anchor S6/S7 rows. Do not cite it as S6/S7 uniqueness, heavy-local
completion, known co-survivor evidence, PyTorch/PyG evidence, or float-spectrum
alias evidence.

## Verdict

- Repo vocabulary: `GENUINE-WITH-CAVEATS`.
- Classification: `scratch_diagnostic`.
- `promotion_allowed=false`; `formal_admission_allowed=false`.
- Engine mode: `julia_canon_plus_jax_diagnostic`.
- Honest mode legitimacy: accepted. The packet scopes exact finite graph,
  cover, and SMT witness rows, not tensor/autograd/message-passing machinery;
  PyTorch/PyG omission is explicit and the generic validator is expected
  without `--require-pytorch`.
- S4 correction applied: every not-run heavy-local S6/S7 non-anchor row is
  `open + queued-heavy-local`, never `co-survivor-open`.

## Named Caveats

- C1 - Isomorphism certificate depth: the Python lane uses a real
  `networkx.is_isomorphic` gate for the deliberate alias control and for
  candidate-to-anchor graph checks. It does not persist a reusable node-mapping
  certificate in the result JSON. Independent scratch audit recomputed an
  explicit isomorphism mapping for the reparameterized cycle, so the alias
  control is accepted, but future citations must say `isomorphism-call backed`,
  not `stored certificate backed`.
- C2 - Heavy-local rows are not run: S67.R3.1-R3.5 are preserved in the phase-2
  queue by registry cost class. Their cover/lens/cost/leakage teeth were not
  executed and they are not known co-survivors.
- C3 - SMT witness depth: z3, cvc5, and Julia Z3 bind only the finite N=8
  closed-cycle degree-row witness for the far path control, with SAT flip after
  closing the path. SMT is not a proof of the full S6/S7 canonical tuple.
- C4 - Julia lane depth: Julia independently rebuilds graph degree/edge/cycle
  rows and the Z3 polarity check. The exact algebraic characteristic
  polynomial/spectrum row is carried by the Python/SymPy lane.

## Registry Standard

Registry source: `system_v6/receipts/round3_discriminator_registry_20260611.md`
at `de44219ed`. The working-tree SHA-256 matched the committed registry blob:
`aedae4224bf2f3fea6aa1b73981f0035589dbce352e9370bfe34dec402e491b3`.

S6/S7 canonicalizer:
`(graph_isomorphism_class_under_dihedral_lens_preserving_maps,
cover_equivalence_relation_classes, Z4_action_well_defined_boolean,
orbit_size_multiset, cost_profile[N=8,16,32],
S6_leakage_class_signature)`.

The Mobius lesson is preserved: same `2:1` cover count alone is not alias.

## Exact Recompute

Read-only scratch recomputation checked finite graph rows without rewriting
builder results:

| Row | Exact recompute result |
| --- | --- |
| Anchor cycle `N=8` | nodes `8`, edges `8`, degree sequence `[2,2,2,2,2,2,2,2]`, cycle rank `1`, charpoly `lambda**8 - 8*lambda**6 + 20*lambda**4 - 16*lambda**2` |
| Reparameterized cycle control | `networkx` isomorphism returned `true`; explicit mapping recomputed in audit |
| Round-2 path far control | nodes `8`, edges `7`, degree sequence `[1,1,2,2,2,2,2,2]`, cycle rank `0`, charpoly `lambda**8 - 7*lambda**6 + 15*lambda**4 - 10*lambda**2 + 1`; not isomorphic to anchor |
| `S67.R3.4_cycle_with_one_chord` | nodes `8`, edges `12`, degree sequence all `3`, cycle rank `5`, charpoly `lambda**8 - 12*lambda**6 + 34*lambda**4 - 16*lambda**3 - 20*lambda**2 + 16*lambda - 3`; not isomorphic to anchor |
| `S67.R3.5_ladder_prism_graph` | nodes `16`, edges `24`, degree sequence all `3`, cycle rank `9`, charpoly `lambda**16 - 24*lambda**14 + 212*lambda**12 - 856*lambda**10 + 1630*lambda**8 - 1544*lambda**6 + 708*lambda**4 - 136*lambda**2 + 9`; not isomorphic to anchor |

This satisfies the hard audit requirement for at least two exact S6/S7
separations. No float spectrum or tolerance row is on the claim path.

## Controls

| Control | Builder verdict | Audit adjudication |
| --- | --- | --- |
| `control.anchor_self` | `anchor` | Accepted. Exact cycle/untwisted-cover canonical tuple self-classifies. |
| `control.alias_reparameterized_committed` | `alias` | Accepted with C1. Alias uses `networkx.is_isomorphic` plus exact canonical tuple equality; scratch audit recomputed an explicit mapping. |
| `control.round2_path_far_graph` | `excluded-by-closed-cycle-graph-row` | Accepted. This is the registry-named first teeth row for the far path control from the round-2 topology lesson. |

## Citable Per-Candidate Table

| Candidate | Registry cost | Verdict | Citable witness / disposition |
| --- | --- | --- | --- |
| `S67.R3.0_committed_torus_ring` | light-symbolic | `anchor` | Exact cycle/untwisted-cover canonical tuple; anchor self-classifies. |
| `S67.R3.1_mobius_reflection_shifted` | heavy-local | `open + queued-heavy-local` | Not run in phase 1; queued for `lens quotient commensurability`; no cited prior co-survivor receipt. |
| `S67.R3.2_klein_double_twist` | heavy-local | `open + queued-heavy-local` | Not run in phase 1; queued for `cover-orbit well-definedness then lens row`; no cited prior co-survivor receipt. |
| `S67.R3.3_shear_torus` | heavy-local | `open + queued-heavy-local` | Not run in phase 1; queued for `lens descent and S6 leakage taxonomy`; no cited prior co-survivor receipt. |
| `S67.R3.4_cycle_with_one_chord` | heavy-local | `open + queued-heavy-local` | Exact graph rows separate it from the anchor, but registry names its decisive row as heavy-local `bounded word cost and cycle holonomy`; queue preserved. |
| `S67.R3.5_ladder_prism_graph` | heavy-local | `open + queued-heavy-local` | Exact graph rows separate it from the anchor, but registry names its decisive row as heavy-local `locality cost plus leakage class row`; queue preserved. |

Known S6/S7 R3 co-survivor classes: none.

## Phase-2 Disposition

Queued by registry cost class:

```text
S67.R3.1_mobius_reflection_shifted - lens quotient commensurability
S67.R3.2_klein_double_twist - cover-orbit well-definedness then lens row
S67.R3.3_shear_torus - lens descent and S6 leakage taxonomy
S67.R3.4_cycle_with_one_chord - bounded word cost and cycle holonomy
S67.R3.5_ladder_prism_graph - locality cost plus leakage class row
```

Stop rule honored: no broad heavy-local battery was run for count inflation.

## Provenance And Schema Checks

Inspected artifacts:

- `build_card.md` includes the S4 binding correction.
- `round3_s6s7_alias_pass_v0_envelope_results.json` reports
  `all_pass=true`, `scratch_diagnostic`, `promotion_allowed=false`,
  `formal_admission_allowed=false`, `julia_canon_plus_jax_diagnostic`, and
  explicit PyTorch omission.
- `round3_s6s7_alias_pass_v0_jax_results.json` carries `networkx`, `sympy`,
  `z3`, and `cvc5` rows; `networkx.is_isomorphic` is load-bearing for the alias
  control.
- `round3_s6s7_alias_pass_v0_julia_results.json` carries `Graphs` and `Z3`
  rows; Julia/JAX verdict maps match.
- `round3_s6s7_alias_pass_v0_validator_results.json` reports `ok=true` and
  `errors=[]`.

I did not rerun packet scripts because this audit was read-only except for this
verdict file, and the packet scripts rewrite result JSONs. Instead, I used
read-only `jq` inspection and a separate scratch Python recomputation that did
not write repository files.

## Future-Citation Rule

Future citations may say:

> `round3_s6s7_alias_pass_v0` is a bounded S6/S7 phase-1
> `scratch_diagnostic`: anchor self-classifies; the deliberately
> reparameterized cycle is accepted as an isomorphism-call-backed exact alias;
> the round-2 path far control dies on the closed-cycle graph row; all five
> S6/S7 non-anchor R3 rows remain `open + queued-heavy-local`.

Future citations must not say:

> S6/S7 uniqueness was proved; heavy-local S6/S7 rows were completed; any
> S6/S7 non-anchor row is a known co-survivor; PyTorch/PyG evidence exists; SMT
> proved the full canonical tuple; float spectra established alias status; a
> reusable graph-isomorphism certificate was persisted in the packet.
