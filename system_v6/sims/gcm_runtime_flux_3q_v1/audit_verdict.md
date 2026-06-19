# Independent Audit Verdict - gcm_runtime_flux_3q_v1

audit_mode: read-only audit except this `audit_verdict.md`
freshness_tier: TIER-3 annotation-verify; prompt supplied builder claims and prior v0/blind-panel framing, and this audit read v0/blind-panel standards before recomputation.
auditor: independent Codex audit of codex1-built packet
git_hygiene: no git add, no commit

Bottom line: VERDICT = `DOCTRINE_SPLIT_GENUINE_WITH_CAVEATS`. The v1 packet genuinely repairs the v0 `L=reverse(R)` tautology for the L/R generator-independence gate: stored recomputation gives distinct Type1-L and Type2-R schedule pins, `max|R-reflect(L)| = 0.864549516754901`, `max|R-reverse(L)| = 0.297293215054724`, and z3/cvc5 both show the required `UNSAT -> SAT` erasure polarity. But the discriminating doctrine result does not pass as a three-current opposition: `J_chi` remains `L=-2`, `R=+2`, while `J_cut` and `J_ent` are same-sign positive on the independent L/R engines. Therefore the information/entanglement-current half of the doctrine is killed for this independent-engine packet.

## Verdict

Earned:

- `INDEPENDENCE_GENUINE`: L and R are computed from distinct Type1-L and Type2-R schedule-derived generator pins, not from `reverse_current_row(...)`, reflection, or peer-row copying.
- `J_chi_OPPOSITION_SEMI_EARNED`: the `-2/+2` chirality opposition is real for the selected carrier-and-pins-relative L/R orientation row. Ceiling: chirality-design / orientation-row evidence only, not emergent runtime/QIT flux and not finite-ring GNVW admission.
- `3Q_FLOOR_SUPPORTED`: the packet preserves the 3Q floor row and substrate lineage controls at scratch ceiling.

Killed:

- `J_cut_LR_OPPOSITION`: killed. Fresh recompute gives L `+0.398385516067546`, R `+0.925568602579871`.
- `J_ent_LR_OPPOSITION`: killed. Fresh recompute gives L `+0.113040677029362`, R `+0.085911157808355`.
- `THREE_CURRENT_DOCTRINE_SIGNATURE`: killed for independent engines in this packet. The full doctrine requires `J_chi`, `J_cut`, and `J_ent` opposition; only `J_chi` survives.

Open caveat:

- `G1_UNTRACKED_PACKET`: the whole `system_v6/sims/gcm_runtime_flux_3q_v1/` directory is untracked in the current worktree (`git ls-files -- system_v6/sims/gcm_runtime_flux_3q_v1 | wc -l` returned `0`). The cited Type1-L/Type2-R generator source is committed, but this v1 packet itself is workspace evidence until intentionally staged/committed later.

## Recomputed Evidence

No-write recomputation used `common.build_packet(write=False)` from `system_v6/sims/gcm_runtime_flux_3q_v1/gcm_runtime_flux_3q_v1_common.py`. It returned `RECOMPUTE_OK True` and `VALIDATION_ERRORS []`. Normal pytest/validator entrypoints were not run because they write result JSONs, outside this audit's allowed write scope.

Generator independence:

| field | value |
|---|---|
| left generator | `engine64_Type1-L_32slot_local_update` |
| right generator | `engine64_Type2-R_32slot_local_update` |
| left schedule sha256 | `c1f7397837c0f9826015cf4a475a5c61311d55baa4f923bdd889673935af5a6c` |
| right schedule sha256 | `9c7382fc3a5c2ebb5c358eca98dfed6dc386c5b9337e55f2e8bd7be8cc006848` |
| distinct committed generator assignments | `true` |
| `R_not_reflection_of_L` | `true` |
| `R_not_reverse_of_L` | `true` |
| `max_abs_R_minus_reflect_L` | `0.864549516754901` |
| `max_abs_R_minus_reverse_L` | `0.297293215054724` |

Source locks:

- `system_v6/sims/engine_64_stage_full_run_v0/engine_64_stage_full_run_v0_common.py`: `git_last_commit=23cfa5536`, source lock hash `cba273d8a29a71a216aac238a636dcc44b503a017aeae9543af8acd15c9b5f05`.
- `system_v6/sims/engine_64_stage_full_run_v0/audit_verdict.md`: `git_last_commit=23cfa5536`, audit lock hash `721299fa3d52adc72e665e95b99fb02c6985a1a2660add87beb1e3c0ecf23e5f`.

The engine64 source pins Type1-L and Type2-R as separate engine-family rows with different `sheet`, `chirality_sign`, `base_order_name`, readout discipline, and terrain realizations. The engine64 audit independently recomputed 32 Type1-L slots and 32 Type2-R slots from the same pinned initial state and found different final states. That supports generator independence at the finite schedule-realization ceiling.

## Current Split

Fresh recomputed rows matched the stored JSON:

| row | `J_chi` | `J_cut` | `J_ent` | trajectory | constructed from peer |
|---|---:|---:|---:|---|---|
| `engine_L_flux_IN_left_3q` | `-2` | `0.398385516067546` | `0.113040677029362` | `own_engine_evolution` | `false` |
| `engine_R_flux_OUT_right_3q` | `+2` | `0.925568602579871` | `0.085911157808355` | `own_engine_evolution` | `false` |
| `time_reverse_of_R_flux_OUT_right_3q` | `-2` | `-0.925568602579871` | `-0.085911157808355` | `explicit_inverse_evolution_control` | `false` |
| `static_no_evolution_3q` | `0` | `0.0` | `0.0` | `identity_control` | `false` |

Sign products:

- `J_chi(L) * J_chi(R) = -4`: opposite.
- `J_cut(L) * J_cut(R) = 0.36873312539469927`: same sign.
- `J_ent(L) * J_ent(R) = 0.00971145544303281`: same sign.

This is the discriminating split. The blind panel's required independent-R control was the correct control. Once R is independent, `J_cut` and `J_ent` opposition disappears.

## J_chi Ceiling

`J_chi` is orientation-tied by definition. The packet does not recompute a new 3Q GNVW index from the runtime-density trajectory; it attaches the committed 2Q open-chain chirality seed as a 3Q survivor row current label/control. That makes `J_chi=-2/+2` real but not emergent in the same sense as the `J_cut`/`J_ent` trajectory values.

Adjudication: closer to (a) than (b), but with a strict ceiling. The independent L/R generators were already pinned as Type1-L and Type2-R schedule families in the committed engine64 source, and the packet proves R is not reflection/reverse of L under the unitary metric. However, those families are themselves selected chirality/orientation designs (`chirality_sign=+1` for Type1-L, `chirality_sign=-1` for Type2-R), so the `J_chi` sign opposition is a successful orientation-row readout of selected chirality pins, not an emergent runtime-flux discovery.

Allowed citation:

> `J_chi` chirality opposition survives at carrier-and-pins-relative, selected-L/R-orientation ceiling: independent Type1-L and Type2-R schedule generators carry `-2/+2` GNVW seed labels, with R not equal to reflect/reverse(L).

Disallowed citation:

> Independent engines show opposite information/entanglement/runtime flux currents.

## Load-Bearing Proofs

The z3/cvc5 proof rows are load-bearing for the generator-independence gate, not for `J_cut`/`J_ent` opposition. They enforce the negation of the real independence gate and flip under erasure:

| solver | real verdict | erased-control verdict | polarity | load-bearing for |
|---|---|---|---|---|
| z3 | `unsat` | `sat` | `negated_violation_unsat_real_erasure_sat` | distinct + not-reverse + not-reflection generator gate |
| cvc5 | `unsat` | `sat` | `negated_violation_unsat_real_erasure_sat` | same generator gate |

This is not decorative like v0. Erasing the independence facts makes the negated gate satisfiable, so the proof is genuinely can-fail for the independence claim. It still does not rescue the killed `J_cut`/`J_ent` doctrine half.

The Julia lane's Z3 receipt also reports `unsat -> sat`, but its scoped claim is chirality sign binding only. The Julia/JAX/PyTorch lanes agree on the sign readout: right `J_cut` positive, left `J_cut` positive, right `J_ent` positive, left `J_ent` positive, right `J_chi=2`, left `J_chi=-2`.

## Controls

Controls recomputed green within the packet's scratch ceiling:

- Scramble changes both current rows: L changes to `J_cut=0.309903879953025`, `J_ent=0.160088826919896`; R changes to `J_cut=1.817048950154995`, `J_ent=0.595036844753913`.
- Time reversal of R flips all three signs: `J_cut=-0.925568602579871`, `J_ent=-0.085911157808355`, `J_chi=-2`.
- Static no-evolution gives zero current.
- Product-control subset vanishes: selected count `8`, `all_selected_product_controls_zero=true`. The packet explicitly does not claim a full product-lift theorem, even though the current identity-baseline scan reports zero over the scanned product rows.
- Carve erasure is red as required: `substrate_check_ok=false`, with lineage/object mismatch errors.
- Substrate positive check is green and negative check fails as required.

## G.2a And Process Boundary

G.2a passes after this audit write because the packet used `scripts/builder_audit_boundary.py` from birth, builder output is `builder_self_assessment.md`, and this file's header declares independent/read-only audit status. The builder did not write `audit_verdict.md`.

Result label:

| path | current label | corrected label | evidence | blocker/demotion reason | next admissible step |
|---|---|---|---|---|---|
| `system_v6/sims/gcm_runtime_flux_3q_v1` | `scratch_diagnostic`, `all_pass=true` | `scratch_diagnostic`, `DOCTRINE_SPLIT_GENUINE_WITH_CAVEATS` | no-write recompute, independence deltas, z3/cvc5 flip, controls | packet untracked; `J_cut`/`J_ent` opposition killed | commit intentionally if accepted, then build a next packet testing whether any independent generator family produces `J_cut`/`J_ent` sign opposition without chirality selection carrying the result |
| `J_chi` | opposite | `J_chi_OPPOSITION_SEMI_EARNED` | `-2/+2`; independent generator pins; R not reflect/reverse(L) | orientation-tied by definition; selected chirality family | cite only as carrier/pins-relative chirality orientation evidence |
| `J_cut` / `J_ent` | non-opposite | `KILLED_FOR_INDEPENDENT_ENGINES` | both L/R signs positive from independent trajectories | doctrine info/entanglement-current opposition fails | do not cite as doctrine signature |

Keep: generator-independence repair, 3Q floor support, controls, load-bearing z3/cvc5 independence polarity, `J_chi` at guarded chirality-orientation ceiling.

Audit further: whether a different pre-pinned independent generator family can make `J_cut`/`J_ent` oppose without selecting labels around the desired chirality result.

Demote: any wording that says runtime/QIT information current or entanglement current opposes across independent L/R engines.

Broken/blocked: commit-level provenance for the v1 packet itself is blocked until the untracked directory is intentionally added in a later git hygiene lane.

Next build: a pre-registered independent-generator sweep where L/R labels are fixed before reading `J_cut`/`J_ent`, with `J_chi` reported separately from information/entanglement currents.
