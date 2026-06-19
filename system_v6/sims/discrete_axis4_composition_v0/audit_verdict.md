# Fresh Audit Verdict: discrete_axis4_composition_v0

auditor: Codex independent audit
generated_at: 2026-06-12T08:35:10Z
freshness_tier: TIER-2
write_scope: wrote this verdict only; no git add or commit
standards_codex: system_v6/receipts/audit_standards_codex_v1.md
binding_vein: system_v6/receipts/axes45_deep_vein_20260612.md

## Bottom Line

VERDICT: PASS_WITH_CAVEATS at `scratch_diagnostic` / `axis_readout_candidate_only` ceiling.

The packet passes the requested hard checks as a minimal source-locked Axis-4 fixture realization on the shared Family-A 33-cell carrier. It does not earn canonical owner-pinned Axis-4 identity, axis admission, Axis-5 completion, Axis-6 precedence, bridge, physics, or manifold promotion.

Citable fixture-fenced sentence:

`discrete_axis4_composition_v0 computes a source-locked Axis-4 commutator fixture using the committed S4 representatives L_R=R_x and L_C=D_z on the shared Family-A 33-cell carrier, yielding 28 non-neutral and 5 neutral W4 cells with commuting, leading-order, and same-carrier Axis-0/Axis-6 non-recovery controls; cite it only as a fixture realization of the Axis-4 order-gap witness, not as the canonical owner-pinned Axis-4 identity.`

## Binding Fence

The Axes 4/5 vein controls this verdict: `R_x/D_z` is a good minimal fixture for the Axis-4 commutator witness, not the owner-pinned identity of Axis 4. The packet mostly carries this fence through `classification="scratch_diagnostic"`, `claim_ceiling="axis_readout_candidate_only"`, `promotion_allowed=false`, `formal_admission_allowed=false`, and explicit disallowed claims including `canonical Axis-4 readout`.

Named caveat `fixture_fence_language`: result fields say `pinned R_x/D_z order-gap table emitted` and `Axis-4 here is R_x/D_z composition order over Family A`. These are acceptable only under the fixture reading above. Future citations should say `R_x/D_z fixture`, not `Axis-4 identity`.

Named caveat `alternatives_preservation`: the verdict preserves the vein alternatives `FeTi/TeFi` and `UEUE/EUEU` as live source alternatives. The packet computes the clean commutator fixture and panel `UEUE/EUEU` leading form; it does not close symbolic spin, `FeTi/TeFi`, or other alternative realizations.

## Recomputed Witnesses

The finite witness recomputes exactly from pinned generators:

- `R_x = [[1,0,0],[0,0,-1],[0,1,0]]`
- `D_z = diag(7/10, 7/10, 1)`
- `Delta = (R_x D_z - D_z R_x) r = (0, -3z/10, -3y/10)`
- `W4 = ||Delta rho||_1 = ||Delta Bloch||_2`

Sample cells:

| cell | coord | exact Delta | exact W4 | sign |
|---:|---|---|---|---:|
| 1 | `[-0.5,-0.5,-0.5]` | `[0,3/20,3/20]` | `3*sqrt(2)/20` | `1` |
| 3 | `[-0.5,-0.5,0.5]` | `[0,-3/20,3/20]` | `3*sqrt(2)/20` | `-1` |
| 5 | `[-0.5,0,0]` | `[0,0,0]` | `0` | `0` |

All-cell exact recomputation gives `positive=14`, `negative=14`, `neutral=5`, `nonneutral=28`, matching the packet.

## Leading-Order Tooth

Panel 7 q3 requires `D=UEUE`, `I=EUEU`, and leading order `D-I ~ 2ue[A,B]`.

Independent recomputation:

- `u=e=0.001`
- `gap_norm = 1.5843824177398846e-06`
- `2ue[A,B] leading_norm = 1.584665022893986e-06`
- `relative_error_2ue = 0.0001783374719693662`, below the packet threshold `0.0005`
- wrong coefficient `ue[A,B]` gives `relative_error_1ue_wrong_coeff = 0.9996433250560613`

This is a real coefficient tooth: the factor-1 version fails hard.

## Independence And No-Identity-Leak

Same-carrier Axis-4 vs Axis-6 discriminator passes:

- Axis-6 readout predicting Axis-4: majority accuracy `0.48484848484848486`, not `1.0`
- Axis-0 readout predicting Axis-4: majority accuracy `0.5757575757575758`, not `1.0`
- identity-inclusive recovery: `1.0`, reported as a leak
- identity-excluded best predictor: `axis0_axis6_readout_pair`
- identity-excluded best accuracy: `0.6060606060606061`, below `1.0`

This satisfies the standards-codex no-identity-leak rule for the reported independence rows. The positive claim is only readout non-recovery under excluded identity fields, not ontological independence.

## EPS And G7 Caveat

Named caveat `eps_pin_g7_class`: `EPS=1e-10` is predeclared in the build card and source, but I did not find an owner/source pin for that exact tolerance. Under the standards codex this is a G7-class adapter/tolerance question.

This does not change the verdict because the sampled neutral cells are exactly zero and the nonzero W4 values are separated from EPS by large margins (`0.15`, `0.212132034355964`, `0.3`). The current result is not balanced on the threshold. A canonical version should either owner-pin the tolerance or enumerate finite tolerance subvariants before evaluation.

## Standards Check

SMT: PASS. z3 and cvc5 bind computed counts and controls, return `unsat` for the negated identity, and flip to `sat` under erasure.

Honest mode and ceiling: PASS. The envelope is `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, and `axis_readout_candidate_only`.

Schema and validators: PASS before this audit file was written. No-write packet-local validation returned `ok=true`; generic three-engine validation returned `ok=true`; pytest returned `4 passed`.

Named caveat `post_audit_idempotency`: `validate_discrete_axis4_composition_v0.py` still contains a pre-audit builder check requiring `audit_verdict.md` to be absent. That is not post-audit-idempotent under `audit_standards_codex_v1` after a legitimate independent verdict exists. The builder boundary field is fine; the validator absence check should be relaxed to the standard independent-audit-header gate in a future repair.

Boundary: PASS. The packet names blocked consumers and disallows canonical Axis-4, Axis-6, bridge, physics, and manifold claims.

Circularity species: none found as verdict-bearing species. Identity leakage is detected and excluded rather than used.

## Canonical-Identity Version Needs

To pursue canonical owner-pinned Axis-4 identity, a future packet needs:

- owner/source pin that Axis 4 is exactly this generator identity, or a finite pre-registered representative set where `R_x/D_z` is one enumerated fixture;
- explicit preservation and testing of `FeTi/TeFi`, `UEUE/EUEU`, symbolic spin, and other Axis-4 alternatives rather than silent collapse to one fixture;
- G7-pinned or enumerated EPS/polarity/adaptor convention before result inspection;
- same-carrier Axis-0/Axis-4/Axis-6 no-identity-leak rows retained;
- commuting, identity/zero, shuffled-order, and leading-order coefficient teeth retained;
- post-audit-idempotent validator behavior;
- a separate promotion/admission gate if stronger than `scratch_diagnostic` is claimed.

## Verification Commands

No repo result files were regenerated. Commands were run with bytecode/cache suppression where applicable.

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# scratch exact recomputation of W4, all-cell counts, leading-order coefficient teeth, and independence accuracies
PY
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# imported validate_discrete_axis4_composition_v0.validate_payload without writing validator_results.json
PY
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/discrete_axis4_composition_v0/results/discrete_axis4_composition_v0_envelope_results.json
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/discrete_axis4_composition_v0/tests
```
