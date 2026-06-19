# Axes 4+5 Deep Vein Receipt - 2026-06-12

Receipt lane: deep-read map for Axis 4 composition order and Axis 5 operator-family/substage block.

Write boundary: this receipt is the only intended write for this lane. No git add or commit was performed by this lane.

Claim ceiling: source-map and build-design receipt only. `promotion_allowed=false`. No canonical axis, Matrix64, or admission claim is made here.

## Bottom Line

Axis 4 is pinned strongly enough for build work as an order/commutator axis: deductive and inductive are different composition orders on the same carrier, with `Phi_D - Phi_I` read by a noncommuting witness. It must remain separate from Axis 6, which is precedence/order-of-application between operator-first and terrain-first frames.

Axis 5 has two layers that must not be collapsed. The operator-family split `{Ti,Te}` vs `{Fi,Fe}` is independently source-locked enough for a partial Axis 5 readout now. The four-substage product/readout layer, including the Matrix64-style `axis5 x axis6` substage convention, remains blocked because no owner source pins the transition convention.

The in-flight Axis 4 design `L_R=R_x` and `L_C=D_z` is usable as a minimal source-locked fixture for the commutator witness if it is fenced as a fixture realization. The vein does not support treating `R_x/D_z` as the canonical owner-pinned identity of Axis 4.

## Sources Read

- `system_v6/foundations/working_math_scaffold_20260609.md`
- `system_v6/receipts/doc_router_axes_terrains_operators_20260609.md`
- `system_v6/receipts/axis_work_order_20260612.md`
- `system_v6/receipts/substage_transition_convention_mining_20260611.md`
- `system_v6/foundations/two_engine_readout_automaton_20260609.md`
- Commit `dd9ec4999` metadata for the readout automaton packet.
- `system_v6/sims/source_locked_operator_base_packet/audit_verdict.md`
- `system_v6/sims/source_locked_operator_base_packet/results/source_locked_operator_base_20260610.json`
- `system_v6/sims/source_locked_operator_base_packet/{jax,pytorch,julia}_source_locked_operator_base.py`
- `system_v5/READ ONLY Reference Docs/operator math explicit.md`
- `~/wiki/concepts/igt-axes-terrain-source-extraction-2026-06-04.md`
- `~/wiki/concepts/taijitu-probe-reconciliation-card.md`
- `system_v5/READ ONLY Reference Docs/TAIJITU_PROBE_RECONCILIATION_CARD copy.md`
- `system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md`
- Targeted repo/wiki sweeps for Axis 5 S-curve, lobe, spin, `FeFi`, `TeTi`, and `TiTe` mentions near the axis material.

## Owner / Preserved Statements

From `working_math_scaffold_20260609.md`:

```text
"the carnot and szilard have to be dual stacked to resemble a qit engine. they need a deductive engine and a inductive engine. but without qit geometry they dont naturally flow together like on a 720 spinor."
```

```text
"Carnot and Szilard are not rival engines. They are two legality/readout grammars that must be dual-stacked on the same finite QIT carrier. Carnot contributes thermodynamic legality. Szilard contributes measurement-memory-feedback legality. The QIT engine witness is the noncommuting interaction of deductive and inductive loops on psi/rho, with controls that erase the gap. Without QIT channel structure, the dual stack is only analogy. Without the dual stack, the QIT channel sim is too thin to resemble the intended engine."
```

Axis scaffold statement:

```text
Axis 4 - composition / order class: Phi_D = e^{tau_R L_R} e^{tau_C L_C} vs Phi_I reversed; Phi_D - Phi_I approximately tau_R tau_C [L_R,L_C]; witness ||Phi_D(rho)-Phi_I(rho)||_1. Deductive often FeTi, inductive TeFi. ALTERNATIVES: symbolic spin / FeTi-TeFi / UEUE-EUEU / commutator witness (cleanest sim target).
```

```text
Axis 5 - generator/operator-family selection: dephasing/dissipative/gradient/GKSL side vs rotation/spectral/Hamiltonian/projector/group side. Local: {Ti,Te} vs {Fi,Fe}. Witnesses: entropy production S(Phi_dephase(rho))-S(rho) >= 0 vs unitary purity preservation Tr(U rho U^dagger)^2 = Tr(rho^2); contractivity; orbit preservation. ALTERNATIVES: S-curve/lobe symbolic overlay (open); FeFi-vs-TiTe label drift (unresolved).
```

Scaffold line 179 boundary:

```text
AXIS PLACEMENT (dual-stack roles): Axis0 = entropy/coherent-info/shell-cut READOUT (field, not a bit); Axis1 = open-vs-closed/CPTP-vs-unitary legality; Axis2 = direct-vs-conjugated frame/bath lens; Axis3 = inner/fiber vs outer/base loop (IN/OUT flux candidate); **Axis4 = deductive-vs-inductive ORDER**; Axis5 = finite-gradient vs finite-spectral generator algebra; **Axis6 = operator-first vs terrain-first PRECEDENCE** (Axis4 and Axis6 are different order DOFs - never merge).
```

Readout automaton packet, commit `dd9ec4999`, preserved operational conclusion:

```text
Deductive order always reads alternating period-2 output. Inductive order always reads paired period-4 output. Engine type sets phase/casing, not the deductive/inductive law.
```

## Axis 4 Deep Map

Core object:

```text
Axis 4 = deductive-vs-inductive composition order on the same carrier.
Primary witness = ||Phi_D(rho)-Phi_I(rho)||_1.
Small-time readout = Phi_D - Phi_I approximately tau_R tau_C [L_R,L_C].
```

Axis 4 alternatives ladder, strongest to weakest:

1. Commutator witness: `Phi_D` versus reversed `Phi_I`, with a nonzero order gap and commuting/identity controls.
2. UEUE/EUEU or `U o E o U o E` versus `E o U o E o U`: the clean loop-order expression of the same order axis.
3. `FeTi` versus `TeFi`: runtime/IGT loop-family label anchor, usable only when mapped to the actual channel order.
4. Readout automaton periodicity: deductive gives alternating period-2 readout; inductive gives paired period-4 readout.
5. Symbolic spin direction: clockwise/counterclockwise remains symbolic unless a dedicated discriminator ties it to the runtime order better than chance.
6. Axis 6 is not on the ladder. Axis 6 is operator-first versus terrain-first precedence, not deductive versus inductive composition order.

The readout automaton strengthens Axis 4 but does not replace the commutator witness. It supplies a separate observable: if the same stage words are read by the two loop orders, deductive is alternating and inductive is paired. This is an order readout, not an operator-family proof.

### Axis 4 Design Check: `L_R=R_x`, `L_C=D_z`

The vein supports `R_x` and `D_z` as a minimal Axis 4 fixture because the source-locked operator packet pins `Fi` as an x-rotation family member and `Ti` as a z-dephasing family member. A fixture that compares `R_x o D_z`-style and `D_z o R_x`-style compositions can expose the required noncommuting order gap.

The vein corrects one possible overclaim: owner/source material does not pin `L_R=R_x` and `L_C=D_z` as the canonical Axis 4 identity. The owner-level pin is the order relation and the same-carrier noncommuting interaction. `R_x/D_z` is a good fixture, not the axis itself.

Recommended fixture fence:

```text
admissible_name: A4 commutator fixture using source-locked Fi/Ti representatives
fixture_pair: R_x / D_z
axis_claim: Axis 4 order-gap witness only
not_claimed: canonical operator identity, Axis 5 completion, Axis 6 precedence, symbolic spin pin
required_controls: commuting pair, identity/zero gap control, same-carrier check, label-swap check
```

## Axis 5 Deep Map

Axis 5 has an independently pinned operator-family half and a blocked substage-product half.

Pinned enough for partial Axis 5 now:

```text
{Ti,Te} = dephasing / dissipative / gradient-like family
{Fi,Fe} = rotation / unitary / spectral-like family
```

The source-locked operator base packet supports that split as a scratch diagnostic:

- `Ti`: z-dephasing channel, with source references into `operator math explicit.md`.
- `Te`: x-dephasing channel, with source references into `operator math explicit.md`.
- `Fi`: x-rotation unitary channel, with source references into `operator math explicit.md`.
- `Fe`: z-rotation unitary channel, with source references into `operator math explicit.md`.
- Diagnostic properties: `Ti/Te` show entropy/coherence effects consistent with dephasing; `Fi/Fe` preserve purity as unitary rotations.

Hard fence on that packet:

```text
classification: scratch_diagnostic
claim_ceiling: source-lock check for Ti/Te/Fi/Fe only
not_claimed: canonical admission, full operator-family completion, substage convention, Matrix64 completion
```

## Axis 5 Block: What The Substage Convention Must Pin

The substage mining receipt found no owner pin for the transition convention needed by the current cyclic-substage realization. This blocks the full Axis 5 substage/product readout and the 64-style schedule. It does not block the partial `{Ti,Te}` versus `{Fi,Fe}` operator-family readout.

To unblock full Axis 5, the owner/source convention must pin at least these items:

1. Whether the four substages are a state machine, a composed internal stage map, a schedule/fingerprint table, or some other object.
2. The exact two signs/states of Axis 5 inside the `axis5 x axis6` product.
3. The exact two signs/states of Axis 6 inside that same product.
4. The order of the four substages within a stage, if they are composed maps.
5. Whether substage wrap advances stage, and whether stage wrap advances loop.
6. How the Matrix64/Carnot product maps onto the owner product `2 engines x 2 loops x 4 stages x 4 substages`.
7. Which observable distinguishes substages: trajectory, entropy, coherence, commutator sign, operator family, stage word, terrain label, or another readout.
8. Which labels are decorative and which are load-bearing: `FeFi`, `TeTi`, `TiTe`, S-curve, lobe, spin, and token-family names.

Current adjudication:

```text
operator_family_half_independently_pinned: yes
partial_axis5_readout_buildable_now: yes, with scratch/source-lock ceiling
full_substage_product_buildable_now: no
owner_pinned_cyclic_substage_transition: no
owner_pinned_matrix64_terminal_64: no
```

## Label Drift

Observed unresolved drift:

- Some material preserves Axis 5 as `FeFi` versus `TeTi`.
- Some material preserves Axis 5 as `FeFi` versus `TiTe`.
- Stronger source-locked runtime anchor is `{Ti,Te}` versus `{Fi,Fe}`.
- S-curve, lobe size/shape, and spin-direction language remains symbolic overlay unless tested.

Resolution options:

1. Demote both `FeFi/TeTi` and `FeFi/TiTe` to legacy symbolic labels. Build Axis 5 only as `{Ti,Te}` versus `{Fi,Fe}`.
2. Preserve both label variants as unresolved overlays while using `{Ti,Te}` versus `{Fi,Fe}` for runnable packets.
3. Run a label-drift discriminator that maps each label pair to actual operator families and kills the pair that fails source-lock.
4. Ask for an owner pin only if the symbolic label layer must remain visible in an admitted packet.

Do not silently normalize `TeTi` and `TiTe`. They encode different token orderings, and Axis 4 already makes token order load-bearing.

## S-Curve / Lobe / Spin Read

The S-curve/lobe vein is consistently weaker than the operator-family vein. It appears as symbolic chart grammar, visual weighting, lobe size/shape, flatter/curvier claims, or possible fast/slow spin. The repeated safe reading is:

```text
S-curve/lobe = symbolic overlay candidate
operator family = stronger runtime/math anchor
spin direction = symbolic unless tied to Axis 4 order by a discriminator
```

The clean Axis 5 discriminator is not "which lobe looks right." It is whether the proposed S-curve/lobe partition tracks `{Ti,Te}` versus `{Fi,Fe}` better than chance, without importing Axis 4 order or Axis 6 precedence.

## Contender Seeds

Axis 4 seeds:

```text
A4.CP.0_commutator_fixture_Ux_Dz
Goal: compare Phi_D and reversed Phi_I on the same carrier using source-locked rotation/dephasing representatives.
Witness: ||Phi_D(rho)-Phi_I(rho)||_1.
Controls: commuting pair, identity/zero parameters, same-carrier check.
Fence: Axis 4 order only; no Axis 5 completion or Axis 6 precedence claim.
```

```text
A4.CP.1_readout_periodicity
Goal: use the dd9ec4999 readout automaton to test deductive=alternating and inductive=paired.
Witness: period-2 alternating versus period-4 paired output on the stage-word table.
Fence: readout/order observable only; not an operator generator proof.
```

```text
A4.CP.2_FeTi_TeFi_runtime_anchor
Goal: map FeTi/TeFi labels to actual UEUE/EUEU channel schedules.
Witness: labels survive only if they preserve the same composition order as the channel maps.
Fence: label layer cannot override channel order.
```

```text
A4.CP.3_symbolic_spin_overlay
Goal: test whether clockwise/counterclockwise spin tracks Axis 4 runtime order.
Witness: better-than-chance mapping to Phi_D/Phi_I across controlled fixtures.
Fence: otherwise spin remains symbolic.
```

```text
A4.CP.4_axis4_axis6_nonalias
Goal: vary deductive/inductive order while holding operator-first/terrain-first precedence fixed, then vary precedence while holding order fixed.
Witness: independent deltas.
Fence: never merge Axis 4 with Axis 6.
```

Axis 5 seeds:

```text
A5.CP.0_partial_operator_family_T_vs_F
Goal: build the partial Axis 5 readout from source-locked Ti/Te versus Fi/Fe.
Witness: dephasing entropy/coherence behavior versus unitary purity/orbit preservation.
Fence: scratch/source-lock operator-family readout only.
```

```text
A5.CP.1_generator_algebra_FGA_vs_FSA
Goal: broaden from four local tokens to finite-gradient/GKSL/Lindblad semigroup versus finite-spectral/Hamiltonian/projector group.
Witness: semigroup contractivity/entropy production versus unitary/spectral orbit preservation.
Fence: requires source-backed functions, not visual labels.
```

```text
A5.CP.2_substage_product_axis5xaxis6
Goal: build the four-substage product only after a convention pins the product order and transition law.
Witness: pinned substage map plus stage/loop advance rule.
Status: blocked.
```

```text
A5.CP.3_scurve_lobe_overlay
Goal: test whether S-curve/lobe symbolic overlay tracks the T/F split better than chance.
Witness: stable mapping to Ti/Te versus Fi/Fe across fixtures.
Fence: no visual-symbolic promotion without discriminator.
```

```text
A5.CP.4_label_drift_resolution
Goal: resolve FeFi-vs-TeTi versus FeFi-vs-TiTe drift.
Witness: source-lock each token pair to actual operator-family content and order.
Fence: unresolved labels stay out of admitted runtime claims.
```

## Fences

- Axis 4 is order/commutator. It is not Axis 6 precedence.
- Axis 5 operator-family partial readout is buildable now, but only under scratch/source-lock ceiling.
- Axis 5 full substage product is blocked until the substage transition convention is owner/source pinned.
- `R_x/D_z` is a good Axis 4 fixture, not a canonical owner-pinned identity.
- `{Ti,Te}` versus `{Fi,Fe}` is stronger than S-curve/lobe symbolism.
- `FeFi` versus `TeTi` and `FeFi` versus `TiTe` remain unresolved label drift.
- No terminal Matrix64 or 64-completion claim is admitted from this vein.
- No cyclic substage machine is owner-pinned by the read sources.
- No git staging or commit belongs to this lane.
