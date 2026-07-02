# INFORMAL → FORMAL handoff — iter_312

Date: 2026-05-25
Author: Claude (informal sidequest thread)
Lane: `system_v5/grok_sim/` only. Not formal evidence.

Classification: `sidequest_local_manifold_ratchet_prototype_v1`
Claim ceiling: `side_quest_only`
`promotion_allowed = false` · `evidence_allowed = false` · `evidence_allowed_for_formal = false`

The 2026-05-23 boundary-damage audit and the 2026-05-24 substrate-violation gate bind this handoff. Nothing here is intended to function as formal-lane evidence, be ingested into formal indexes, or be written into `system_v5/ops/formal_scouts/`. The targets section below is a list of *reproduction prompts* for the formal lane, not a list of established results.

---

## 1. What ran

A single torch-native script that walks the manifold-ratchet chain end to end at smoke scale:

  F01 + N01 → finite probe quotient → PEPS3D-seeded local spinor carrier
  (2×2×2) → spinor / density readout → nested Hopf tori with Y_in / Y_out
  loop fields → L/R Weyl sheet (sign flip plus σ₋ / σ₊ structural difference)
  → 8 terrain generators X_(τ,s) → 16 loop placements → 64-cell embedding
  c = (engine, terrain, loop, operator_slot) with a local channel action per
  cell → blocked flux / Axis0 spec text.

The iter wrote one result JSON and ran in ~0.05s on the codex-ratchet env. Every audit boolean is derived from a computed torch tensor norm or from a count over real per-cell records; no hardcoded passes.

Files:

- `system_v5/grok_sim/iters/iter_312_claude_informal_manifold_ratchet.py`
- `system_v5/grok_sim/results/iter_312_claude_informal_manifold_ratchet_results.json`

---

## 2. What worked

Seven probe families, all derived from real tensor computation:

1. **POVM completeness.** A 6-effect cube-vertex frame `{(1/6)(I + r_a·σ) : r_a ∈ {±x, ±y, ±z}}`. The 6 directions sum to zero, so `Σ_a E_a = I` analytically; the Frobenius residual is `0.0` exact.

2. **F01 finite probe quotient.** Two spinor configs that differ only in χ (relative-phase angle between the two ψ components) give probe responses with distance `0.397` under the full 6-effect family and `0.0` under a truncated z-axis pair (which sees only diag(ρ), independent of χ). The quotient depends on |P|: real demonstration that `~_P` coarsens when probes are removed.

3. **N01 noncommutation witness.** `X_(Se,L)` and `X_(Ne,L)` applied in opposite orders (6 Euler steps each, dt=0.05) produce a probe-response gap of `2.5×10⁻⁴`. The same-terrain control is `0.0` exact. The witness scales with `dt² · ‖[X_Se, X_Ne]‖`; making it visible required multi-step integration.

4. **Hopf loop density visibility.** Inner loop `Y_in = ∂_φ` keeps ρ at `1.4×10⁻¹⁶` (machine epsilon); outer loop `Y_out = -cos(2η) ∂_φ + ∂_χ` traverses density space by `0.85` over the 1-parameter sweep. `A_Hopf(Y_out) = 0` by horizontality (computed: `0.0`).

5. **L/R Weyl sheet structural distinction.** Ni terrain on L uses σ₋ (Pit, lowering); on R uses σ₊ (Source, raising). Si terrain uses different projector axes per sheet. The full L/R difference on Ni is `0.0163`; the pure-sign-flip baseline (identical L = R = σ₋, only H sign differs) gives `0.0081`. Structural difference is ~2× sign-flip-only. L/R is not collapsed into bare H → −H.

6. **16-placement inventory.** Iteration over (τ ∈ {Se,Ne,Ni,Si}, s ∈ {L,R}, ℓ ∈ {in,out}) yields all 16 cells with non-zero local ρ action and non-zero spinor tangent.

7. **64-cell embedding.** All 64 cells `(engine, terrain, loop, operator_slot)` have a real local channel `Φ_c(ρ)` — terrain Lindblad + operator unitary composed per Axis6 sign — with per-cell ρ delta above 1e-6. The cross-cell N01 witness on `(1,Se,in,Ti-) ∘ (1,Ne,in,Fe-)` is `0.16`, well above noise.

---

## 3. What failed

Nothing crashed; all gates pass. But the **gates that pass are smoke-scale**. The real failures are by construction, labeled below.

- **No cross-cell tensor coupling.** The 64 cells act on a single 2×2 site each. No bond-link `Φ_(u,v)` is exercised. The cell embedding is not on the full PEPS3D lattice.
- **No full PEPS3D environment contraction.** The 2×2×2 tensor network has real 6-leg `T_v` tensors with virtual bond legs, but the contraction used is product-fixture (bond index = 0 on every leg). No boundary-MPS, no environment trace.
- **No real flux / Axis0.** Both are spec-only. `J_flux` and `A0` are written as target forms with admission tests but not executed; foundation_closed=false.
- **Spinor tangent fields not coupled to ρ dynamics.** Y_in / Y_out are computed and tested for density-visibility, but the script lets terrain Lindblad drive ρ independently of the spinor tangent. The placement tuple binds them only by label.

---

## 4. What is likely fake / scaffold

Honestly labeled in the iter JSON as `shortcuts_labeled`:

- **S1 — PEPS3D contraction.** Real `T_v[α_x⁻, α_x⁺, α_y⁻, α_y⁺, α_z⁻, α_z⁺, a]` tensors at every site of a 2×2×2 lattice with bond_dim=2 and phys_dim=2. Readout is product-fixture per site. Not full-environment.
- **S2 — 64-cell local action.** Each cell carries a real `Φ_c` composed of terrain Lindblad step plus operator unitary, with Axis6 ordering. The action is single-site. Cross-cell coupling is not exercised.
- **S3 — Probe family.** 6 effects built from Pauli operators serve as the finite probe family. Pauli is the effect-builder (adapter), not Bloch components in disguise. Probe responses are `Tr(ρ E_a)`, finite per-effect.
- **S4 — Pauli as adapter chart.** SX, SY, SZ, σ₋, σ₊ appear as 2×2 complex matrices, generators of the operator algebra. Root state is the spinor ψ; ρ = ψψ† is a derived readout. No Bloch vector is used as state.
- **S5 — Flux / Axis0 blocked.** Specs are present as text only. No execution. Honors `foundation_closed=false` and the substrate ledger.

The bond_link_pair function honestly returns a Kronecker product of two product-fixture site spinors, labeled `bond_link_scaffold_is_kron_not_contraction: True`.

---

## 5. Best formal reproduction targets

Each row is a *prompt* for the formal lane to rebuild from source docs, not an established result. The format is exactly the seven fields requested.

### Target T1 — finite probe quotient as a real CPTP-invariant equivalence

| Field | Value |
|---|---|
| candidate map | `Q_P : S → S/~_P` where `s ~_P t iff p(s) = p(t)` for all `p ∈ P` |
| domain | finite admissible state set on a torch-native d=2 single-site carrier |
| codomain | quotient set with finite cardinality |
| control needed | truncated-probe-family collapse; CPTP-equivalent state stress; gauge-relabel control |
| why interesting | the iter demonstrates the quotient depends on |P|; the formal lane should prove |~_P| changes as a step function in |P| and that the quotient classes are CPTP-stable under the active probe set |
| why not evidence yet | sidequest computed on a single qubit with one chi-axis pair; not a finite-state-set quotient over a discrete admissible-state ensemble |

### Target T2 — Hopf horizontality checked on density-visibility metric

| Field | Value |
|---|---|
| candidate map | `(ψ_s, Y_field) → max_u ‖ρ(u) − ρ(0)‖` |
| domain | spinor `ψ_s(φ, χ; η)` at fixed (φ₀, χ₀, η₀), Y ∈ {Y_in, Y_out} |
| codomain | non-negative real (a finite path-visibility scalar) |
| control needed | shell-erase control (collapse η stack); Hopf-control (replace A by flat phase); a third loop field that is neither vertical nor horizontal as positive distinguisher |
| why interesting | inner = machine-ε exact stationarity; outer = ~0.85 traversal; A_Hopf(Y_out) = 0 by computed horizontality; this is exactly the Axis3 fiber-vs-base distinction that the iter_82-era chain only labeled |
| why not evidence yet | smoke-scale; no PEPS3D anchor; the formal lane must show this on a finite PEPS3D-carried spinor section, not on a free C² spinor |

### Target T3 — L/R sheet structural difference dominated by σ₋ / σ₊ swap

| Field | Value |
|---|---|
| candidate map | `(τ ∈ {Ni}, s ∈ {L, R}, ρ) → X_(τ,s)(ρ)` |
| domain | finite operator family `{σ₋ on L, σ₊ on R}` plus H_L = +H₀, H_R = −H₀ |
| codomain | sheet-specific Lindblad image of ρ |
| control needed | sign-flip-only baseline (force σ₋ on both sheets, vary only H sign) plus an L/R-erased control (collapse s to one sheet) |
| why interesting | iter found structural / sign-flip ratio ≈ 2.0 — half the L/R signal is the σ swap, not the H sign; formal lane should test whether structural ratio is invariant across (η, φ, χ) sweeps |
| why not evidence yet | single seed; no statistics; no PEPS3D carrier coupling; cross-shell behavior unknown |

### Target T4 — N01 cell-pair witness on a real bond-link

| Field | Value |
|---|---|
| candidate map | `(c_A, c_B) → ‖r_P(Φ_{c_A} ∘ Φ_{c_B}(ρ)) − r_P(Φ_{c_B} ∘ Φ_{c_A}(ρ))‖` |
| domain | pairs of cells `(c_A, c_B)` from the 64-cell set |
| codomain | non-negative real (probe-response gap) |
| control needed | commuting-pair control (same cell twice); CPTP-decomposed pair where [X_A, X_B] is analytically zero; full 64×64 / 2 = 2016 pair sweep with histogram |
| why interesting | the iter found a pair-N01 of 0.16 between (Se,in,Ti-) and (Ne,in,Fe-); a full sweep would give the noncommutation structure of the 64-cell algebra |
| why not evidence yet | iter checked one pair; PEPS-cross-cell action absent; the formal lane must run the full 2016 pairs against the right anchor and decide which pairs the engine schedule actually traverses |

### Target T5 — POVM completeness on cube-vertex frame as a model SIC-like family

| Field | Value |
|---|---|
| candidate map | `{r_a ∈ S² : a = 1..6} → {E_a = (1/6)(I + r_a·σ)}` |
| domain | finite direction set summing to 0 |
| codomain | POVM with `Σ_a E_a = I` exactly |
| control needed | direction perturbations (non-zero-sum control); 4-effect SIC comparison; over-complete frames at |P| = 9, 12 |
| why interesting | cube-vertex gives exact completeness with rational coefficients; baseline for probe-quotient experiments |
| why not evidence yet | not novel; this is a chart, not a result |

### Target T6 — terrain action on a finite spinor anchor

| Field | Value |
|---|---|
| candidate map | `(τ, s, ψ_v) → ρ_v + dt · X_(τ,s)(ψ_v ψ_v†)` |
| domain | (τ ∈ {Se,Ne,Ni,Si}) × (s ∈ {L,R}) × spinor at PEPS site v |
| codomain | post-step ρ_v plus tangent norm |
| control needed | label-only terrain control (X = 0); commuting-terrain control; gauge-invariance check under U(1) ⊕ U(1) on (φ, χ) |
| why interesting | iter shows all 16 placements act non-trivially; formal lane should test that the action is independent of φ_v (U(1) gauge), as theory predicts |
| why not evidence yet | smoke; not bound to PEPS3D bond legs; the formal lane must verify the action passes through a real PEPS contraction at small lattice (2×2×1) before scaling |

---

## 6. Formal blockers that remain

These are the gate flags the iter does **not** flip, by construction:

```
foundation_closed = false
peps3d_from_start_required = true
substage_cell_embedding_proven = false
quaternion_layer_closed = false
flux_queue_allowed = false
axis0_queue_allowed = false
shell_boundary_geometry_present = false
peps3d_full_environment_closed = false
```

Specific blockers the formal lane must clear before flux or Axis0 can be queued:

- **Real PEPS3D environment contraction.** This iter's `T_v` tensors exist but the contraction is product-fixture. The formal lane needs boundary-MPS at χ ≥ 4, a finite-environment trace, and a contraction-correctness check on a 2×2×1 reference.
- **Cross-cell bond-link channel `Φ_(u,v)`.** The iter applies channels per site only. A real lattice action requires bond-link channels that couple sites, plus an N01 witness on the bond-link order.
- **Quaternion shell orientation map / invariant.** The iter uses Pauli as adapter and does NOT advance a quaternion shell layer. If a quaternion layer is to be closed, the formal lane must build a map or invariant on PEPS3D-anchored spinor data — naming `i, j, k` is not enough (per CONSTRAINT_MANIFOLD_MATH_LEDGER §4).
- **64-cell tensor embedding.** Each cell here carries a local action only. A real 64-cell embedding needs each cell to carry its own PEPS3D tensor with its own bond geometry (per CONSTRAINT_MANIFOLD_MATH_LEDGER §8: T_c with six virtual bonds + physical), and to show that the engine schedule traverses 64 cells, not 16 stage placements.
- **Flux derivation.** All flux admission tests (F01 finite bound, N01 order swap, sheet-bound, shell-bound, engine-bound, topology-bound) require the lower chain to be closed first. Spec text in the iter is not flux evidence.

---

## 7. Exact files written

```text
system_v5/grok_sim/iters/iter_312_claude_informal_manifold_ratchet.py
system_v5/grok_sim/results/iter_312_claude_informal_manifold_ratchet_results.json
system_v5/grok_sim/INFORMAL_TO_FORMAL_HANDOFF_iter_312.md
```

No writes to `system_v5/ops/formal_scouts/`, `system_v5/docs/`, `system_v5/evidence/`, or any formal classifier / index. The result JSON uses sidequest-local vocabulary only: `classification: sidequest_local_*`, `claim_ceiling: side_quest_only`, `promotion_allowed: false`, `evidence_allowed_for_formal: false`. No formal-scout stamp.
