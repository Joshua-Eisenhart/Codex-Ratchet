# Independent audit verdict - discrete_axes12_pair_v0

Bottom line: VERDICT = `GENUINE-WITH-CAVEATS` at `scratch_diagnostic` strength.

`discrete_axes12_pair_v0` is a real finite Axis-1/Axis-2 paired readout candidate on the
Family-A 33-cell carrier. Fresh scratch reruns passed the three engine lanes, envelope rebuild,
packet validator, generic three-engine validator, and pytest. The legality and frame witness
values recompute from source and the four product classes `{Se, Ni, Ne, Si}` factor as
`axis1 x axis2`.

The caveats are binding: row classes are predeclared in `ROW_SPECS` and then witness-checked
rather than inferred by an independent classifier; `product_alias` is a post-computation alias
table, not a discovered label; JAX/PyTorch share the Python common builder and Julia is
aggregate/count-level only; Axis-5 comparison is still only against the partial family half, not
the missing `axis5 x axis6` substage product.

## Verdict Details

- Verdict: `GENUINE-WITH-CAVEATS`.
- Freshness tier: `TIER-2` results-available. I read packet source/results and then reran in a
  scratch copy before writing this audit file.
- Classification remains: `scratch_diagnostic`.
- Claim ceiling remains: `axis_readout_candidate_only`.
- `promotion_allowed=false`.
- `formal_admission_allowed=false`.
- Citation status ladder: `exists < scratch rerun passes validators/tests < audited candidate`.
  The packet directory is untracked in this checkout, so do not cite it as committed/canonical
  process evidence until a later commit exists.

Do not promote this packet to Axis-1 admission, Axis-2 admission, canonical terrain proof,
Carnot/Szilard stroke identity, bridge evidence, physics evidence, manifold evidence, or formal
axis closure.

## Fresh Checks

To preserve the read-only live checkout boundary, I copied the repo to:

```text
/tmp/codex_axes12_audit/Codex-Ratchet
```

Then I reran the builder/validator chain there:

- Julia lane: `ok=true`.
- JAX lane: `ok=true`.
- PyTorch lane: `ok=true`.
- `write_envelope_spec.py`: `ok=true`.
- `scripts/build_three_engine_envelope.py`: rebuilt the envelope in scratch.
- Packet validator: `errors=[]`, `ok=true`.
- Generic validator:
  `scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent ...`
  returned `ok=true`.
- Pytest: `3 passed`.

Live checkout write scope: only this `audit_verdict.md`.

Post-audit idempotency caveat: the packet-local validator still requires
`audit_verdict.md` to be absent in `validate_packet_files(...)`. That check passed in the scratch
pre-audit copy. After this legitimate audit file exists, the validator may fail unless interpreted
as a build-time no-builder-audit gate or repaired to the standards-codex independent-audit header
gate.

## Recomputed Witnesses

I recomputed the load-bearing witness values from source formulas, not from builder prose.

Axis-1 legality/kernel witnesses:

| row | recomputed result | adjudication |
|---|---|---|
| `Vortex:pure_hamiltonian` | `kraus_rank=1`, trace-preserving `true`, unital `true`, max purity delta `0.0` | supports `unitary` |
| `Pit` | `kraus_rank=2`, trace-preserving `true`, Choi min eigenvalue `-0.0`, unital `false`, max purity delta `0.455` | supports proper CPTP/non-unitary |

This satisfies the requested legality tooth as witness evidence: the unitary/proper-CPTP split is
not just label text. Caveat: `axis1_class` is assigned from the predeclared row spec and then
checked by witnesses; future hardening should derive the class field from the witness predicate.

Axis-2 frame witnesses:

| class | rows | recomputed `K_t` norm |
|---|---|---:|
| direct | `Funnel`, `Cannon`, `Vortex:pure_hamiltonian`, `Spiral:pure_hamiltonian`, `Vortex:weak_dissipator` | `0.0` |
| conjugated | `Spiral:weak_dissipator`, `Pit`, `Source`, `Hill`, `Citadel` | `1.414213562373095` on every row |

This satisfies the requested frame tooth: the conjugated rows carry nonzero
`K_t = i V_t^dagger dot(V_t)` under the packet's dynamic-frame convention, while direct rows are
zero. Caveat: as with Axis 1, `axis2_frame_class` is predeclared and then witness-checked.

## Product Structure

The four topology product is a computed factor table with aliases attached after the two axis
values:

| `axis1` | `axis2` | alias | row count |
|---|---|---|---:|
| `proper_cptp` | `direct` | `Se` | 3 |
| `proper_cptp` | `conjugated` | `Ni` | 3 |
| `unitary` | `direct` | `Ne` | 2 |
| `unitary` | `conjugated` | `Si` | 2 |

On the 33-cell carrier projection, recomputed product counts are:

```text
Se=11, Ni=9, Ne=7, Si=6, total=33
```

The joint table factors as `axis1 x axis2`. Neither axis is recoverable from the other:

| scope | predictor | target | majority accuracy |
|---|---|---|---:|
| 10-row table | `axis1` | `axis2` | `0.5` |
| 10-row table | `axis2` | `axis1` | `0.6` |
| 33-cell table | `axis1` | `axis2` | `0.5454545454545454` |
| 33-cell table | `axis2` | `axis1` | `0.6060606060606061` |

Caveat: the alias table itself is definitional once the two axis classes are available. Cite the
aliases only as the packet's `axis1 x axis2` product readout, not as an independent discovery of
Jungian/IGT labels.

## Carnot Fence

The Carnot-stroke non-conflation fence holds.

This pair is built from the terrain-sheet substrate and the axes 1/2 work order:
`unitary/proper-CPTP legality x direct/conjugated frame`. It is not the Carnot thermodynamic stroke
ledger and does not identify Carnot's four thermodynamic strokes with `{Se, Ni, Ne, Si}`. The
packet's `carnot_strokes_fence.same_object_as_axis12_product=false` is correct.

## Independence Rows

I reran the cumulative no-identity-leak predictor rows against axes 0/4/5/6. Identity-inclusive
recovery is a known leak at `1.0` and is excluded under the standards-codex rule.

Identity-excluded majority accuracies for `product_alias`:

| prior axis feature | majority accuracy | witness pair |
|---|---:|---|
| `axis0_response` | `0.36363636363636365` | same `axis0_minus_homeostatic_response`: cell `0`=`Se`, cell `2`=`Ne` |
| `axis4_composition` | `0.3939393939393939` | same `neutral_commuting_or_zero_gap`: cell `0`=`Se`, cell `5`=`Ni` |
| `axis5_family_signature` | `0.3333333333333333` | same family signature: cell `0`=`Se`, cell `2`=`Ne` |
| `axis6_precedence` | `0.3939393939393939` | same `operator_first_precedence`: cell `0`=`Se`, cell `2`=`Ne` |

Adjudication: the no-identity-leak rows pass at candidate ceiling. Future citations must say that
identity leakage was detected and excluded, and that the best identity-excluded predictor accuracy
for these rows is below `1.0`.

Axis-5 caveat: the Axis-5 row is weak because current Axis-5 evidence is the partial family half.
It is evidence that the Axis-1/2 product is not recoverable from the current partial Axis-5 family
signature. It is not evidence against the still-missing `axis5 x axis6` substage product.

## Circularity Species

Six-species audit:

- `frozen-factor echo`: no verdict-bearing instance found. Caveat: the Axis-5 comparison uses the
  current partial family signature and must not be promoted to substage evidence.
- `definitional circularity`: caveat applies to the alias map. The aliases are assigned from
  `PRODUCT_ALIASES` after the two axis classes are available.
- `rule-table readback`: caveat applies to `product_alias` and to the class-field shape because
  row specs predeclare the intended class. The witness values independently support the assigned
  classes, so this does not force rejection.
- `post-hoc statistic`: no verdict-bearing instance found. No statistical promotion is claimed.
- `shift-relabeling`: no verdict-bearing instance found. Carnot-stroke rows are fenced as a
  different object.
- `structure-by-symmetry`: no verdict-bearing instance found. The four-class product is finite
  enumeration plus computed witnesses, not a symmetry proof.

Net circularity adjudication: `GENUINE-WITH-CAVEATS`, not `GENUINE`, because the witness computation
and the alias/class assignment are not fully separated.

## Cross-Backend Scope

Three-lane rerun passed, but backend independence is scoped.

- JAX and PyTorch write separate lane files and have package/tool probes, but both call
  `common.engine_result(...)`, which calls the shared Python `build_axes12_object()`.
- Julia reruns in an independent runtime and uses `Graphs`/`Z3`, but it hardcodes the aggregate
  product counts and does not emit the same row-local table/hash as the Python lanes.
- The accepted backend claim is aggregate/count/tool-envelope agreement, not independent
  per-row derivation across all three backends.

Future hardening should make Julia emit the same canonical row table or a row-table hash derived
from an independent Julia implementation, and should derive axis classes from witness predicates
rather than from predeclared row labels.

## Seven-Axis Matrix Status

This audit completes the currently buildable 0-6 readout set at scratch candidate ceiling:

| axis | current packet/status | matrix implication |
|---|---|---|
| 0 | `discrete_axis0_field_v0`: `GENUINE-WITH-CAVEATS` | Family-A scalar-field readout candidate; same-carrier no-recovery rows exist against tested features |
| 1 | this packet | legality/kernel candidate as part of the Axis-1/2 pair |
| 2 | this packet | direct/conjugated frame candidate as part of the Axis-1/2 pair |
| 3 | `discrete_axis3_placement_v0`: `GENUINE-WITH-CAVEATS` | real Hopf placement candidate, but Axis0 comparison is surrogate/cross-carrier |
| 4 | `discrete_axis4_composition_v0`: `PASS/GENUINE-WITH-CAVEATS` fixture | R_x/D_z fixture readout; not canonical Axis-4 identity |
| 5 | `discrete_axis5_family_partial_v0`: `GENUINE-WITH-CAVEATS` partial | family half only; substage product missing |
| 6 | `discrete_axis6_precedence_v0`: `GENUINE-WITH-CAVEATS` | Family-A precedence candidate with no-identity-leak caveat |

What the full seven-axis independence matrix now shows:

- For the buildable readout packets, no current citable independence row may include cell identity,
  coordinates, direct fingerprints, source row id, or equivalent identity keys.
- Within the Family-A carrier surfaces, the new Axis-1/2 product is not perfectly recoverable from
  axes 0, 4, partial 5, or 6 under identity-excluded predictors.
- Existing individual packets provide candidate-level non-recovery evidence, but not a single
  formal all-pairs independence theorem.
- Axis 3 remains the main carrier mismatch: its strongest current packet is a Family-B Hopf
  placement candidate with surrogate projection rows, while the 33-cell faithful cover is still
  unbuilt.
- The prior `axis_independence_discriminators_036` fixture must not be used as carrier-level
  independence evidence; its own audit rejected that claim as field-isolated/decorative.

What is still missing:

- The Axis-5 substage half: the `axis5 x axis6` four-substage product remains blocked on the
  owner-pinned substage-transition convention.
- A faithful shared-carrier Axis-3 adapter or proof-backed fiber-augmented 33-cell cover.
- A consolidated all-pairs matrix that emits every pairwise predictor row under the same
  no-identity-leak rule and the same citation ceiling.

## Citation Rule

Allowed citation:

```text
`discrete_axes12_pair_v0` is an audited `GENUINE-WITH-CAVEATS` scratch Axis-1/Axis-2 paired readout
candidate on the Family-A 33-cell carrier: it witness-checks unitary/proper-CPTP legality and
direct/conjugated frame rows, emits the computed `axis1 x axis2` product aliases
`{Se, Ni, Ne, Si}`, and reports identity-excluded non-recovery from axes 0, 4, partial 5, and 6.
Carry caveats: row classes are predeclared then witness-checked, product aliases are table aliases,
backend independence is aggregate-scoped, Carnot thermodynamic strokes are a fenced different
object, and Axis-5 substage evidence is still missing.
```

Do not cite it as:

- Axis-1 admission.
- Axis-2 admission.
- completed formal seven-axis independence.
- Carnot/Szilard stroke identity.
- canonical terrain or topology proof.
- bridge, physics, manifold, or formal-admission evidence.

