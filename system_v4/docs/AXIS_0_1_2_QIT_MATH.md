# Axis 0–1–2 QIT Math Packet

**Date:** 2026-03-29
**Epistemic status:** Axis 1 and Axis 2 are source-locked at the semantic class-split level. The reduced Axis 1 × Axis 2 terrain join is source-locked. Axis 0 has a source-backed candidate family, but its exact kernel and exact bridge from geometry to cut state are still open. Any local sign encoding, color/symbol overlay, and the closure `χ₀ = χ₁χ₂` are compiled conventions, not source-locked theorems.
**Status:** Working lock — tightened to the screenshot packet and corrected by multi-lane audit.

Focused follow-on packet:
- `system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md`

---

## Shared Objects

| Object | Pure Math | QIT Label |
|---|---|---|
| state space | D(C²) = {ρ ∈ B(C²) : ρ ≥ 0, Tr ρ = 1} | qubit density states |
| cut-state space | D(H_A ⊗ H_B) | two-part state for correlation functionals |
| topology set | T = {Se, Ne, Ni, Si} | four terrain addresses |
| Pauli triple | σ⃗ = (σ_x, σ_y, σ_z) | algebraic basis for density, Hamiltonians, operators |
| entropy | S(ρ) = -Tr(ρ log ρ) | von Neumann entropy |
| conditional entropy | S(A\|B)_ρ = S(ρ_AB) - S(ρ_B) | bipartite conditional entropy |
| coherent information | I_c(A⟩B)_ρ = -S(A\|B)_ρ = S(ρ_B) - S(ρ_AB) | directed coherent-information functional |
| mutual information | I(A:B)_ρ = S(ρ_A) + S(ρ_B) - S(ρ_AB) | total correlation |

---

## Pauli Basis

| Role | Pure Math | Status |
|---|---|---|
| density coordinates | ρ = ½(I + r⃗·σ⃗) | direct |
| Hamiltonian coordinates | H₀ = n_x σ_x + n_y σ_y + n_z σ_z | direct |
| projector/operator coordinates | P_±^Z = ½(I ± σ_z), Q_±^X = ½(I ± σ_x) | direct |
| generator ingredients | σ_±, σ_j | schematic reminder only |

---

## Geometry Spine

### Canon manifold layer

| Layer | Pure Math | Meaning |
|---|---|---|
| constraint manifold | M(C) = {x : x is admissible under C} | admissible configuration space induced by constraints |
| geometry | coordinate-free compatibility structure induced by C on M(C) | geometry is prior to axis labels |
| axis slice | A_i : M(C) → V_i | each axis is a function on the constraint manifold |

### Concrete realization used by the current packet

| Layer | Pure Math | Meaning |
|---|---|---|
| Hilbert space | H = C² | single-sheet carrier space |
| carrier sheet | S_s³ = {ψ_s ∈ C² : \|ψ_s\| = 1}, s ∈ {L,R} | normalized sheet carrier |
| paired carrier-density | M̂_geom = ⨆_{s∈{L,R}} Ŝ_s, Ŝ_s = {(ψ_s,ρ_s) ∈ S_s³ × D(H) : ρ_s = ψ_s ψ_s†} | concrete realization packet |
| realization map | ι : M̂_geom ↪ M(C) | concrete geometry lands inside the canon manifold |

### Direct geometry on the carrier

| Layer | Pure Math | Meaning |
|---|---|---|
| carrier | S³ = {ψ ∈ C² : \|ψ\| = 1} | normalized spinor carrier |
| Hopf projection | π(ψ) = ψ†σ⃗ψ ∈ S² | Bloch-sphere projection of the carrier |
| spinor chart | ψ_s(φ,χ;η) = \(\begin{pmatrix}e^{i(\phi+\chi)}\cos\eta\\ e^{i(\phi-\chi)}\sin\eta\end{pmatrix}\), s ∈ {L,R} | source-tight local chart on the carrier |
| torus stratum | T_η = {ψ_s(φ,χ;η) : φ,χ ∈ [0,2π)} ⊂ S³ | one nested Hopf torus |
| Hopf connection | 𝒜 = -i ψ† dψ = dφ + cos(2η) dχ | connection separating fiber from horizontal motion |
| fiber loop | γ_fiber^s(u) = ψ_s(φ₀+u,χ₀;η₀) | phase/fiber loop on one torus |
| base loop | γ_base^s(u) = ψ_s(φ₀-cos(2η₀)u,χ₀+u;η₀) | horizontal lifted-base loop on one torus |
| horizontal condition | 𝒜(\(\dot{\gamma}_{base}^s\)) = 0 | source-tight base-loop constraint |
| fiber density path | ρ_f^s(u) = \(|\gamma_f^s(u)\rangle\langle\gamma_f^s(u)|\) = ρ_f^s(0) | density-stationary loop family |
| base density path | ρ_b^s(u) = \(|\gamma_b^s(u)\rangle\langle\gamma_b^s(u)|\) = ½(I + r⃗(χ₀+u,η₀)·σ⃗) | density-traversing loop family |
| density reduction | ρ(ψ) = \lvert\psi\rangle\langle\psi\rvert = ½(I + r⃗·σ⃗) | Bloch reduction of a spinor |

`inner/outer` is not used as a universal geometry label here. The source-tight carrier geometry is `fiber/base`; any `inner/outer` naming has to be attached later and engine-indexed.

### Compiled working layer on top of the geometry

| Layer | Pure Math | Meaning |
|---|---|---|
| sheet | s ∈ {L, R}, H_s = ±H₀ | compiled left/right sheet variable |
| terrain | X_{τ,s} | local flow law on the chosen sheet |
| operator | J_o | local map family |
| precedence | Ψ↑, Ψ↓ | later composition layer; not part of the direct geometry |

### Weyl-sheet working layer

| Object | Pure Math |
|---|---|
| left spinor | ψ_L ∈ S³ ⊂ C² |
| right spinor | ψ_R ∈ S³ ⊂ C² |
| left density | ρ_L = ψ_L ψ_L† |
| right density | ρ_R = ψ_R ψ_R† |
| left Hamiltonian | H_L = +H₀ |
| right Hamiltonian | H_R = -H₀ |

This Weyl-sheet block is a compiled working layer from screenshot math plus probe support. It is useful, but it is not a source-quoted theorem about live branch semantics.

---

## Required Ax0 Bridge

Axis 0 cannot be evaluated on a single isolated spinor. It needs a cut state.

| Object | Pure Math | Status |
|---|---|---|
| abstract bridge placeholder | Ξ : (geometry sample or history window) → ρ_AB ∈ D(H_A ⊗ H_B) | compiled umbrella for the still-missing bridge |
| pointwise bridge family | Ξ_pt : x ↦ (c_x, ρ_c_x(x)), c_x = A_x\|B_x | source-backed abstract pointwise family |
| shell-cut bridge family | Ξ_shell : x ↦ {(r, w_r, ρ_{A_rB_r}(x))}_r | strongest source-backed pointwise family |
| history-window bridge family | Ξ_hist : h\|_{[t0,t1]} ↦ {(t, c, w_c, ρ_c(t))}_{t,c} | canon-backed history family |
| Ax0 evaluation | Φ₀(ρ_AB) | source-backed: Ax0 acts on cut/bipartition states |
| open choice | choice of cut `A\|B`, construction of ρ_AB, and pointwise-vs-history realization | not locked |

`ρ_LR` is not used here, because current repo usage already gives `ρ_LR` a different meaning as an inter-chirality coherence block.

### Source-backed bridge surfaces

| Surface | Pure Math | Status |
|---|---|---|
| pointwise pullback | x ↦ ρ(x) ↦ Φ₀(ρ(x)) | screenshot-backed shape, with bipartite-state caveat |
| shell-cut pullback | x ↦ ρ_{A_rB_r}(x) ↦ Σ_r w_r I_c(A_r⟩B_r)_ρ | strongest screenshot-backed pointwise shape |
| history pullback | h ↦ \(\frac{1}{T}\int_0^T \sum_{cut\in C} w_{cut} I_c(cut;\rho_h(t))\,dt\) | canon-backed external history form |
| explicit Ξ construction | Ξ_pt or Ξ_shell or Ξ_hist | still missing as finished math |

---

## Axis 0

Detailed bridge and manifold options now live in [AXIS0_MANIFOLD_BRIDGE_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md).

### Shape family

| Shape | Pure Math | Status |
|---|---|---|
| pointwise manifold pullback | φ₀(x) = Φ₀(ρ(x)) | screenshot-backed |
| shell-cut pointwise pullback | φ₀(x) = Σ_r w_r I_c(A_r⟩B_r)_{ρ(x)} | strongest screenshot-backed pointwise family |
| history functional | φ₀[h] = \(\frac{1}{T}\int_0^T \sum_{cut\in C} w_{cut} I_c(cut;\rho_h(t))\,dt\) | strongest canon-backed family |

The pointwise manifold form and the history-functional form are both live surfaces. Their exact unification is still open.

### Candidate kernel family

| Role | Pure Math | Status |
|---|---|---|
| generic kernel family | Φ₀(ρ_AB) | source-backed family, not one locked final formula |
| preferred simple kernel | Φ₀(ρ_AB) = -S(A\|B)_ρ = I_c(A⟩B)_ρ | strongest current working candidate |
| saved shell-cut kernel | Φ₀(ρ) = Σ_r w_r I_c(A_r⟩B_r)_ρ = -Σ_r w_r S(A_r\|B_r)_ρ | strongest screenshot global form |
| companion diagnostic | I(A:B)_ρ | source-backed companion quantity |
| required input | ρ_AB or a higher-partite reduction | not a single isolated spinor |

### Discrete projection

| Topology | Projection |
|---|---|
| Ne | N / white |
| Ni | N / white |
| Se | S / black |
| Si | S / black |

### What is solid

| Layer | Math | Meaning |
|---|---|---|
| canon slice statement | A₀ : M(C) → V₀ | Ax0 lives as a slice on the constraint manifold |
| concrete realization into the manifold | ι : M̂_geom ↪ M(C) | current geometry is one realization inside the canon manifold |
| continuous Axis 0 | Φ₀(ρ_AB) after a chosen bridge Ξ | primitive continuous correlation family |
| history-shaped Axis 0 | φ₀[h] after a chosen cut family and trajectory map | strongest canon-backed Ax0 form |
| discrete Axis 0 projection | {Ne, Ni} vs {Se, Si} | N/S or white/black projection |

### Executable evidence

| Probe | Result | What it supports |
|---|---|---|
| [sim_L0_s3_valid.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_L0_s3_valid.py) and [L0_hopf_manifold_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/L0_hopf_manifold_results.json) | PASS; \(S^3\), SU(2), Hopf map, fiber preservation, Berry phase, torus coordinates, and Bloch round-trip validate numerically | the direct carrier geometry is executable, not just diagrammatic |
| [test_engine_dual_loop_grammar.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/test_engine_dual_loop_grammar.py) and [engine_core.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/engine_core.py) | PASS; live engine state carries explicit `psi_L`, `psi_R`, named nested-torus coordinates, and 32-step cycle execution per engine type | full left/right Weyl structure on nested Hopf tori exists in the executable engine |
| [engine_core.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/engine_core.py) | PASS; full 64-stage run executes with live axis deltas on Type 1 and Type 2 | the full geometry plus Weyl plus nested-torus engine path is real |
| [axis0_gradient_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_gradient_sim.py) and [axis0_gradient_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/axis0_gradient_results.json) | separable state: \(I(A:B)=0,\ S(A\|B)=1\); Bell state: \(I(A:B)=2,\ S(A\|B)=-1\) | \(-S(A\|B)\) / \(I_c(A⟩B)\) is the cleanest simple Ax0 candidate; mutual information alone cannot go negative |
| [axis0_correlation_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_correlation_sim.py) and [axis0_correlation_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/axis0_correlation_results.json) | PASS; MI is built up then burned, but the file uses retensorization and verdicts only on MI | older MI-battery proxy; not a credible finished bridge from geometry/history to a cut state |
| [axis0_path_integral_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_path_integral_sim.py) and [axis0_path_integral_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/axis0_path_integral_results.json) | PASS; negative conditional entropy, shell cuts, environment entropy, and MI monotonicity all appear in one bundle | shell-cut/history ideas stay live, but this is still an older mixed-proxy synthesis rather than a clean Ax0 proof |
| [sim_GA0_entropic_gradient.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_GA0_entropic_gradient.py) and [GA0_entropic_gradient_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/GA0_entropic_gradient_results.json) | PASS; entropy rises as more Hopf fibers are sampled and mixed | competing geometric coarse/fine semantics; useful as a runtime proxy, not the same object as the cut-state kernel |
| [sim_weyl_dof_analysis.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_weyl_dof_analysis.py) and `weyl_dof_analysis.json` | reports \(8\) independent DOF clusters from a Weyl pair and uses `ρ_LR` as the left-right coherence block | warns against reusing `ρ_LR` as the Ax0 cut-state symbol |
| [axis0_xi_strict_bakeoff_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_xi_strict_bakeoff_sim.py) and [axis0_xi_strict_bakeoff_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/axis0_xi_strict_bakeoff_results.json) | direct `L|R` stays MI-trivial on the live engine, shell-strata pointwise is geometry-blind, point-reference passes the fiber/base discriminator, and history-window stays nontrivial | strongest current executable bridge discriminator on the real Weyl/Hopf engine |

### What the executable layer currently suggests

| Claim | Current status |
|---|---|
| `Ax0` needs a signed entropy/correlation primitive | supported |
| \(-S(A\|B)\) / \(I_c(A⟩B)\) is the strongest simple working primitive | supported |
| weighted shell-cut coherent-information forms remain live | supported, but not yet cleanly realized by one executable bridge |
| direct `L|R` on the live engine is enough by itself | not supported; MI stays trivial |
| one naive shell-strata pointwise bridge closes the pointwise problem | not supported |
| a fixed-reference pointwise bridge can distinguish fiber from base on the live geometry | supported as a compiled executable candidate |
| a history-window bridge can be nontrivial on the live engine geometry | supported |
| the current runtime proxy is fiber coarse-graining / coarse-fine control | supported |
| the runtime proxy is already the same object as the source-backed Ax0 kernel | not supported |
| torus transport by itself is the full `Ax0` kernel | not supported |
| the geometry-to-cut-state bridge `Ξ` is finished math | not supported |

### Stronger full-geometry standard

| Requirement | Current status |
|---|---|
| full and real `S^3` / Hopf / nested-torus geometry | supported |
| explicit left and right Weyl spinors on that geometry | supported |
| live executable engine on that combined geometry + Weyl stack | supported |
| true `Ax0` cut-state kernel on top of that same combined stack | not supported |
| explicit end-to-end bridge `geometry/history -> rho_AB` on the live Weyl/torus engine | not supported |

Under this stronger standard, the earlier Ax0 sim batch was only partial:

- `sim_L0_s3_valid.py` covers real geometry, but not joint Weyl Ax0
- `axis0_gradient_sim.py` covers the clean cut-state kernel candidate, but not geometry or Weyl
- `sim_GA0_entropic_gradient.py` covers geometric coarse/fine behavior, but not joint Weyl or cut-state Ax0
- `engine_core.py` covers full geometry plus full Weyl plus named nested tori, but its `Ax0` is still a per-sheet coarse-graining proxy, not a cut-state correlation functional

### Bounded next sims

| Sim design | Input object | Bridge assumption | Observable(s) | What it would discriminate |
|---|---|---|---|---|
| `A0-kernel discriminator` | small bipartite cut states \(ρ_{AB}\) | none | \(-S(A\|B)\), \(I(A:B)\), \(Σ_r w_r I_c(A_r⟩B_r)\) | strongest entropy primitive for Ax0 |
| `Hopf pointwise pullback` | geometry samples \(x \in S^3\) on fixed \(T_η\) | compare shell-strata and fixed-reference pointwise bridges | \(φ_0(x)\), constancy on fiber loops, variation on base loops | whether Ax0 can be pointwise on the manifold and which pointwise bridge is not empty |
| `History-vs-pointwise Ax0` | short stage-channel trajectories \(h(t)\) | fixed-reference pointwise vs history-window bridge | \(φ_0(x_t)\) vs \(φ_0[h]\) | whether Ax0 is pointwise, history-shaped, or both |
| `Ξ-bridge bakeoff` | same geometry/history sample under multiple bridge proposals | compare shell-cut, point-reference, history-window, and left/right paired noncanon candidates | sign, monotonicity, perturbation sensitivity, loop-family stability | least-arbitrary bridge family |
| `Fiber/base transport test` | paired fiber/base trajectories with explicit \(V(t)\) on the base loop | conjugated-frame bridge on a fixed cut | \(Φ_0(ρ_{AB}(t))\) under direct vs transported evaluation | whether transport geometry changes Ax0 or belongs only to Ax2 |

---

## Axis 1

### Source-locked semantic split

| Class | Pure Math | QIT Label |
|---|---|---|
| unitary branch | Φ(ρ) = UρU† | unitary *-automorphism dynamics |
| proper CPTP branch | Φ(ρ) = Σ_k K_k ρ K_k†, Σ_k K_k†K_k = I | proper CPTP dynamics |
| Markovian working realization | ρ̇ = -i[H,ρ] + Σ_j (L_jρL_j† - ½L_j†L_jρ - ½ρL_j†L_j) | concrete GKLS subclass, not the whole definition |

### Reduced topology projection used by the screenshot packet

| Side | Topologies |
|---|---|
| proper CPTP side | Se, Ni |
| unitary side | Ne, Si |

This is the reduced kernel-regime split used by the screenshot packet. It should not be confused with the richer full terrain-law packet.

---

## Axis 2

### Source-locked semantic split

| Class | Pure Math | QIT Label |
|---|---|---|
| direct representation | ρ̇ = L(ρ) | direct representation |
| unitarily conjugated representation | ρ̃ = V†ρV, K = iV†V̇, ρ̃̇ = V†L(Vρ̃V†)V - i[-K, ρ̃] | conjugated representation |

### Unitary special case

| Class | Pure Math |
|---|---|
| direct unitary form | ρ̇ = -i[H,ρ] |
| conjugated unitary form | H̃ = V†HV, ρ̃̇ = -i[H̃ - K, ρ̃] |

### Label layers

| Layer | Meaning | Status |
|---|---|---|
| kernel | direct vs unitarily conjugated representation | source-locked |
| readable overlay | Eulerian vs Lagrangian | overlay only |
| note overlay | teardrops vs dots | informal note layer only |
| weak metaphor | expansion/compression | do not use as the kernel |

The grouping `Se/Ne` on the direct side and `Ni/Si` on the conjugated side belongs to the reduced `Axis 1 × Axis 2` product surface, not to the primitive Axis 2 kernel by itself.

---

## Axis 1 × Axis 2

### Source-locked reduced terrain join

| Axis 1 class | Axis 2 class | Topology | Reduced product equation |
|---|---|---|---|
| proper CPTP | direct representation | Se | ρ̇ = L(ρ) |
| proper CPTP | unitarily conjugated representation | Ni | ρ̃̇ = V†L(Vρ̃V†)V - i[-K, ρ̃] |
| unitary | direct representation | Ne | ρ̇ = -i[H,ρ] |
| unitary | unitarily conjugated representation | Si | ρ̃̇ = -i[H̃ - K, ρ̃] |

This is the reduced kernel-regime table from the screenshot packet. It is not the full terrain-law table.

---

## Local Sign Encoding

The source packet locks the semantic partitions and the four-way join. It does **not** lock a canonical `±1` polarity. The encoding below is a local bookkeeping convention only.

| Encoding | Definition | Status |
|---|---|---|
| χ₁ | χ₁(Se) = χ₁(Ni) = +1, χ₁(Ne) = χ₁(Si) = -1 | local sign coding of the Axis 1 partition |
| χ₂ | χ₂(Se) = χ₂(Ne) = -1, χ₂(Ni) = χ₂(Si) = +1 | local sign coding of the Axis 2 partition |
| χ₀ | χ₀(Ne) = χ₀(Ni) = +1, χ₀(Se) = χ₀(Si) = -1 | local sign coding of the Axis 0 projection |

### Compatible derived closure inside that sign convention

| Topology | χ₁χ₂ | χ₀ |
|---|---|---|
| Se | (+1)(-1) = -1 | -1 |
| Ne | (-1)(-1) = +1 | +1 |
| Ni | (+1)(+1) = +1 | +1 |
| Si | (-1)(+1) = -1 | -1 |

\[
\chi_0 = \chi_1 \chi_2
\]

This closure is compatible and useful, but it is derived from the local sign convention above. It is not a source-locked theorem.

---

## Informal Symbol Overlay

This table is preserved because it is useful, but it stays at the note/overlay layer.

| Topology | Informal symbol | Status |
|---|---|---|
| Se | black teardrop | note-layer overlay |
| Ne | white teardrop | note-layer overlay |
| Ni | white dot | note-layer overlay |
| Si | black dot | note-layer overlay |

The note source itself says one of the symbol-axis orientations could be inverted, so this overlay is not promoted to kernel status.

---

## Open Points

| Missing | Why it still matters |
|---|---|
| explicit bridge Ξ | Ax0 still needs a concrete map from geometry/history data to a chosen cut state |
| exact cut `A\|B` for Ax0 | needed before the Ax0 kernel can be evaluated concretely |
| explicit V(t) tied to geometry | Ax2 has clean representation math, but not yet a geometry-locked transport law |
| η not assigned to any axis | torus latitude is real geometry with no settled axis role yet |
| full terrain laws vs reduced product equations | the reduced `Ax1 × Ax2` packet is solid, but it is not yet the full terrain law ledger |
| symbol orientation caveat | the note-layer symbol projection is still not fully closed |

### Epistemic status summary

| Item | Status |
|---|---|
| Axis 1 semantic split | source-locked |
| Axis 2 semantic split | source-locked |
| reduced Axis 1 × Axis 2 terrain join | source-locked |
| Axis 0 candidate family | source-backed, not final |
| local sign encoding `χ₀, χ₁, χ₂` | compiled convention |
| `χ₀ = χ₁χ₂` | compatible derived closure |
| symbol/color overlay | note-layer only |
| explicit bridge Ξ | missing |
