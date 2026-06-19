# Audit verdict - round3_s4_alias_pass_v0

Bottom line: ACCEPTED WITH NAMED CAVEATS as a bounded
`scratch_diagnostic` S4 light-symbolic phase-1 alias/convention-pinned audit.
The packet may be cited for the S4 anchor, deliberate alias control, the
`S4.R3.4_axis_permuted_committed` convention-pinned exclusion under the parent
z-probe/S4 role-order pin, and preservation of the phase-2 heavy-local queue.
It must not be cited as S4 uniqueness, heavy-local completion, PyTorch evidence,
or as proving the four not-run heavy S4 rows are co-survivors.

## Verdict

- Classification remains `scratch_diagnostic`.
- `promotion_allowed=false` and `formal_admission_allowed=false` are correct.
- The envelope is schema-conforming: `schema_version=three_engine_sim_result_v1`.
- Honest mode `julia_canon_plus_jax_diagnostic` is legitimate for this narrow
  phase: the claim path is exact symbolic channel-role comparison plus finite
  SMT witness checks, with no graph/network/autograd/tensor claim path.
- `S4.R3.4_axis_permuted_committed` is accepted only as
  `excluded-under-pinned-parent-z-probe-convention`. Relaxing the parent
  z-probe quotient or S4 role-order pin reopens it as a convention-relative
  alias/neighbor question.
- The four heavy-local registry rows are not accepted as co-survivors. Treat
  their packet label `co-survivor-open` as citation-demoted to `open +
  queued-heavy-local`:
  - `S4.R3.1_z_amplitude_damping_pair`
  - `S4.R3.2_x_amplitude_damping_pair`
  - `S4.R3.3_dephase_rotate_hybrid`
  - `S4.R3.5_weak_nonunital_pauli_channel`

## Canonical-Form Reality

The claim-bearing alias path is exact-symbolic, not numeric-closeness aliasing.
The Python lane builds exact SymPy role tuples over rational/surd entries,
compares tuple equality/hash equality, and I found no `evalf`, `isclose`,
`allclose`, tolerance, NumPy, JAX, or float threshold on the claim path.

The accepted anchor alias class is exact:

```text
S4.R3.0_committed_DzDxRxRz
control.anchor_self
control.alias_reparameterized_committed
```

Fresh scratch recomputation confirmed the two actual exclusion rows in this
phase:

```text
S4.R3.4 axis-permuted D_z role:
anchor M = diag(7/10, 7/10, 1)
candidate M = diag(1, 7/10, 7/10)
anchor z-probe image = (0, 0, 1/2)
candidate z-probe image = (0, 0, 7/20)
delta = (0, 0, -3/20)
```

```text
far A_y-frame control, first teeth row:
anchor M = diag(7/10, 7/10, 1)
candidate M = diag(7/10, 1, 7/10)
anchor z-probe image = (0, 0, 1/2)
candidate z-probe image = (0, 0, 7/20)
delta = (0, 0, -3/20)
```

Important boundary: if "at least two S4 exclusions" means two non-control S4
registry candidates, this packet does not have them. Phase 1 excludes exactly
one non-anchor S4 registry candidate, `S4.R3.4`; the second exclusion is the
far-candidate control.

I also recomputed exact heavy-row canonical separations as a sanity check, but
these are audit-side observations, not packet-earned heavy verdicts:

```text
AD_z(gamma=1/5): M00 gap vs D_z = (-7 + 4*sqrt(5))/10, c_z gap = 1/5,
Choi spectrum class = (0, 0, 1/10, 9/10)

AD_z(gamma=3/10): M00 gap vs D_z = (-7 + sqrt(70))/10, c_z gap = 3/10,
Choi spectrum class = (0, 0, 3/20, 17/20)

D_z(lambda) o R_x(pi/2): M12 gap vs committed R_x is 3/10 at lambda=7/10
and 1/2 at lambda=1/2.
```

These exact separations support that the heavy candidates are real finite
operator/channel neighbors, but they remain open because the registry's
heavy-local teeth were not run in this packet.

## Per-Candidate Adjudication

| Candidate | Packet verdict | Audit verdict |
| --- | --- | --- |
| `S4.R3.0_committed_DzDxRxRz` | `anchor` | ACCEPTED anchor |
| `S4.R3.1_z_amplitude_damping_pair` | `co-survivor-open` | DEMOTED to `open + queued-heavy-local` |
| `S4.R3.2_x_amplitude_damping_pair` | `co-survivor-open` | DEMOTED to `open + queued-heavy-local` |
| `S4.R3.3_dephase_rotate_hybrid` | `co-survivor-open` | DEMOTED to `open + queued-heavy-local` |
| `S4.R3.4_axis_permuted_committed` | `excluded-under-pinned-parent-z-probe-convention` | ACCEPTED convention-pinned exclusion |
| `S4.R3.5_weak_nonunital_pauli_channel` | `co-survivor-open` | DEMOTED to `open + queued-heavy-local` |

There are no accepted S4 known co-survivors in this verdict. The S3 standard
therefore applies negatively: without a cited prior co-survivor receipt, a
surviving/not-run S4 row must be `open + queued`, not a known co-survivor.

## Controls

Controls are accepted:

- Deliberate reparameterization alias reduces to the anchor canonical tuple.
- Anchor self-classifies as anchor.
- Far `A_y`-frame control dies on the first z-probe quotient
  descent/mortality teeth row.
- z3/cvc5 and Julia Z3 report the expected nonzero-witness polarity with flip
  controls: positive nonzero-negation `unsat`; erased/zero flip `sat`.

SMT caveat: the solvers bind finite rational witness rows. They are legitimate
cross-checks for the pinned z-probe deltas, not an independently extracted full
channel-canonical proof and not evidence for the unrun heavy-local teeth.

## Backend And Validator Caveats

Named caveat 1 - heavy-row vocabulary:
The packet's `co-survivor-open` label is too strong for not-run heavy-local S4
rows. Future citations must rewrite those rows as `open + queued-heavy-local`
unless a later receipt runs their registry-named heavy teeth or cites a real
known-co-survivor precedent.

Named caveat 2 - Choi/Kraus depth:
The packet's accepted light exclusion separates by pinned role tuple/z-probe
operator rows, not by Choi spectrum. The Choi/Kraus-heavy S4 candidates remain
phase-2 work. Audit-side exact AD separations above do not promote them.

Named caveat 3 - Julia depth:
Julia and Python/JAX verdict maps match and Julia builds exact role tuples for
the scoped rows, but this is not full independent Julia proof of every heavy
candidate canonical form or heavy-local battery row.

Named caveat 4 - validator scope:
Fresh read-only generic validator reruns returned `ok=true` for plain,
`--require-source-backed`, `--strict-source-backed`, and
`--require-tool-intent`. However, `--require-tool-intent` passes while the
envelope uses `TOOL_INTENT_MATRIX_decision` rather than a stricter top-level
`tool_intent` object, so do not overcite that flag. `--require-pytorch` fails
as expected with `engines.pytorch must be an object`; this is compatible with
honest PyTorch omission, but blocks any PyTorch-scoped claim.

Named caveat 5 - rerun freshness:
I did not rerun the lane, envelope, or packet-local validator scripts in place
because they write result JSONs and the audit instruction allowed only this
file as a repo write. I mirrored the packet-local validator assertions in
scratch and reran the generic validator read-only.

## Stop Rule And Phase-2 Disposition

The stop rule is honored for phase 1. No heavy-local rows were run, and there
is no count-inflation justification for running heavy rows against already
classified light-cost representatives.

Phase 2 for S4 is exactly the registry heavy-local queue:

```text
S4.R3.1_z_amplitude_damping_pair - N01/commutator and fixed-axis rows
S4.R3.2_x_amplitude_damping_pair - z-probe quotient descent/mortality
S4.R3.3_dephase_rotate_hybrid - shell preservation/leakage then N01
S4.R3.5_weak_nonunital_pauli_channel - fixed-axis plus Choi positivity
```

Do not relaunch a broad S4 battery from this verdict. The next admissible S4
work is a narrow phase-2 heavy-local packet over the queued rows, or a validator
hardening patch for the `--require-tool-intent` loophole.

## Future-Citation Rule

Future citations may say:

```text
round3_s4_alias_pass_v0 accepted as scratch_diagnostic phase-1 S4
light-symbolic evidence: exact canonical-form alias control passed; anchor
self-classifies; S4.R3.4 is excluded only under the pinned parent z-probe/S4
role-order convention; relaxing that pin reopens it; heavy-local S4.R3.1,
R3.2, R3.3, and R3.5 remain open and queued by registry cost class.
```

Future citations must not say:

```text
S4 is unique; S4 heavy-local is complete; S4.R3.1/R3.2/R3.3/R3.5 are known
co-survivors; S4.R3.4 is intrinsically killed independent of convention; two
non-control S4 registry exclusions were proved; PyTorch evidence exists;
numeric closeness established alias status; SMT proved the full channel
canonical forms.
```

## Verification Commands

Fresh commands run by this audit:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py \
  system_v6/sims/round3_s4_alias_pass_v0/results/round3_s4_alias_pass_v0_envelope_results.json

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py --require-source-backed \
  system_v6/sims/round3_s4_alias_pass_v0/results/round3_s4_alias_pass_v0_envelope_results.json

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py --strict-source-backed \
  system_v6/sims/round3_s4_alias_pass_v0/results/round3_s4_alias_pass_v0_envelope_results.json

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py --require-tool-intent \
  system_v6/sims/round3_s4_alias_pass_v0/results/round3_s4_alias_pass_v0_envelope_results.json
```

Each returned `ok=true`. The expected PyTorch-required negative control:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py --require-pytorch \
  system_v6/sims/round3_s4_alias_pass_v0/results/round3_s4_alias_pass_v0_envelope_results.json
```

returned:

```text
{"ok": false, "errors": ["engines.pytorch must be an object"]}
```

## Route-Truth Note

Wizard v4.2 Max Assembly was partial. Three read-only Codex sidecars ran
bounded evidence-boundary, falsifier, and compile-gate checks; no Claude/Gemini
child hierarchy or full nine-parent matrix is claimed. Evidence for this
verdict is from direct repo inspection, sidecar receipts, fresh scratch exact
recomputation, read-only generic validator reruns, and existing packet result
files.
