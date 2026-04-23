# Axis 0 Manifold and Bridge Options

**Date:** 2026-03-29  
**Epistemic status:** Strict working owner packet for the `Axis 0` bridge layer. The upstream geometry packet is source-backed and probe-backed. The `Axis 0` kernel family is source-backed. The exact bridge `Xi : geometry/history -> rho_AB` is still open. This file tracks bridge contract, bridge families, executable evidence, killed options, and open gaps without upgrading proxies into doctrine.

---

## 1. Scope And Status

This file is only about the bridge layer for `Axis 0`.

It assumes the upstream separation already holds:

- constraints are not geometry
- geometry is not `Axis 0`
- `Axis 0` acts on a cut-state functional after a bridge has been chosen

Upstream owner packet:

- [CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md)

Broad proto basin index:

- [PROTO_RATCHET_CONSTRAINT_GEOMETRY_BASIN.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_CONSTRAINT_GEOMETRY_BASIN.md)
- [AXIS0_XI_HIST_STRICT_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_XI_HIST_STRICT_OPTIONS.md)
- [AXIS0_ACTIVE_PACKET_INDEX.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_ACTIVE_PACKET_INDEX.md)

---

## 2. Upstream Preconditions

The bridge layer starts only after these are already in place:

| Layer | Pure math | Status |
|---|---|---|
| constraint manifold | \(M(C)\) | thin canon |
| geometry carrier | \(S^3 \to T_\eta \to \gamma_{\mathrm{fiber}},\gamma_{\mathrm{base}} \to \rho(\psi)\) | source-backed, probe-backed |
| favored realization | \((\psi_L,\psi_R,\rho_L,\rho_R)\) with Weyl working layer | compiled working layer |
| `Axis 0` kernel family | \(\Phi_0(\rho_{AB})\in\{-S(A|B),\ \sum_r w_r I_c(A_r\rangle B_r),\ I(A:B)\}\) | source-backed family |

What geometry does **not** provide by itself:

- a bipartite cut-state \(\rho_{AB}\)
- a final cut \(A|B\)
- a finished bridge \(\Xi\)

---

## 3. Bridge Contract

The minimum bridge object is:

\[
\Xi:\text{geometry sample or history window}\to \rho_{AB}
\]

with

\[
\Phi_0(\rho_{AB})
\]

as the later `Axis 0` kernel evaluation.

### 3.1 Required contract

| Requirement | Meaning |
|---|---|
| bipartite target | bridge must output a real cut-state \(\rho_{AB}\) or a clearly typed shell/history generalization |
| no geometry-only shortcut | raw \(x\in T_\eta\), raw \(\eta\), raw transport, or one reduced density \(\rho(\psi)\) are not enough |
| cut declared | the cut \(A|B\) must be explicit or at least typed as a candidate family |
| kernel-compatible | output must be meaningful for \(-S(A|B)\), \(I_c\), or \(I(A:B)\) |
| notation-safe | do not reuse repo symbols in ways that collide with existing runtime meanings |

### 3.2 Hard non-admitted inputs

| Object | Why not enough |
|---|---|
| single isolated spinor \(\psi\) | not bipartite |
| single reduced density \(\rho(\psi)\) | not a cut-state |
| raw torus latitude \(\eta\) | coordinate only |
| raw local `L|R` product pair | honest control, but not enough for nontrivial `Axis 0` |

---

## 4. Bridge Family Table

| Family | Pure math shape | Current status | What it is not |
|---|---|---|---|
| abstract pointwise | \(\Xi_{\mathrm{pt}}:x\mapsto \rho_{AB}(x)\) | admitted shape only | not a finished executable bridge |
| shell family | \(\Xi_{\mathrm{shell}}:x\mapsto \rho_{AB}^{\mathrm{shell}}(x)\) | live family, exact shell algebra unfinished | not identical to old shell-strata implementation |
| history family | \(\Xi_{\mathrm{hist}}:h\mapsto \rho_{AB}^{\mathrm{hist}}(h)\) | strongest live bridge family | not final canon `Xi` |
| cross-temporal constructive family | chiral (Weyl/chirality-weighted) bridge on cross-time L/R pairings | current strongest exploratory constructive family from strict sweeps, but still a constructed cut-state | not earned fixed-marginal closure |
| point-reference family | \(\Xi_{\mathrm{ref}}:(x_{\mathrm{ref}},x)\mapsto \rho_{AB}^{\mathrm{ref}}(x)\) | strongest live pointwise discriminator | not full bridge doctrine |
| direct `L|R` control | \(\Xi_{L|R}:(\rho_L,\rho_R)\mapsto \rho_L\otimes \rho_R\) | killed as sufficient, keep as control | not a promoted bridge |
| coupled control | explicit nonlocal control coupling | control only | not a candidate bridge doctrine |

### 4.1 Current strict bridge read

- strongest live executable bridge family = `Xi_hist`
- strongest exploratory constructive search family = cross-temporal chiral (Weyl/chirality-weighted) bridge
- strongest live pointwise discriminator = point-reference
- fixed-marginal preserving bridge lane = certified near-zero on the current carrier
- therefore the current bridge problem is earned-versus-constructed closure, not mere winner discovery

---

## 5. Cut Candidates

| Cut candidate | Status | Why it matters |
|---|---|---|
| generic bipartite cut \(A|B\) | admitted abstract form | minimum QIT requirement |
| shell/interior-boundary cut | strongest geometric-QIT cut candidate | best match to shell-cut coherent-information family |
| history-window cut | strongest live executable family | aligns with surviving `Xi_hist` behavior |
| raw `L|R` cut | control only | useful guardrail, not enough alone |

Open point:

\[
A|B
\]

is still not fixed as one final doctrine-level cut.

Exact-cut owner packet:

- [AXIS0_CUT_TAXONOMY.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_CUT_TAXONOMY.md)

Shell-specific cut clarification:

- shell/interior-boundary doctrine belongs to the cut owner packet, not this bridge packet
- this file only owns how a future strict `Xi_shell` might land in that cut family

Typed shell cut contract:

- [AXIS0_TYPED_SHELL_CUT_CONTRACT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_TYPED_SHELL_CUT_CONTRACT.md)

History-window cut clarification:

- history-window cut ownership remains in the cut owner packet
- this file only owns how a strict `Xi_hist` might land in that cut family
- typed history-window cut contract = minimum executable cut target for Xi_hist
- Xi_hist emission is owned in AXIS0_XI_HIST_EMISSION_PACKET.md
- the typed contract packet owns the minimum (t,c,w_c,rho_c(t)) target that Xi_hist must land in

Typed history-window cut contract:

- [AXIS0_TYPED_HISTORY_WINDOW_CUT_CONTRACT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_TYPED_HISTORY_WINDOW_CUT_CONTRACT.md)

Strict shell replacement packet:

- [AXIS0_XI_SHELL_STRICT_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_XI_SHELL_STRICT_OPTIONS.md)

Strict history replacement packet:

- [AXIS0_XI_HIST_STRICT_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_XI_HIST_STRICT_OPTIONS.md)

Strict point-reference packet:

- [AXIS0_XI_REF_STRICT_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_XI_REF_STRICT_OPTIONS.md)

Point-reference cut-role lock:

- point-reference cut-role is OPEN but SECONDARY
- point-reference cut-role does not outrank history-window as executable cut family
- point-reference cut-role does not outrank shell/interior-boundary as doctrine-facing cut family
- point-reference remains the strongest live pointwise discriminator and must stay visible in ranking work even when it does not settle doctrine by itself

Bridge relation packet:

- [AXIS0_BRIDGE_RELATION_PACKET.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_BRIDGE_RELATION_PACKET.md)

Typed cut sync card:

- typed cut sync card = non-equivalence lock between typed history and typed shell targets
- [AXIS0_TYPED_CUT_SYNC_CARD.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_TYPED_CUT_SYNC_CARD.md)

Closeout card:

- [AXIS0_BRIDGE_CLOSEOUT_CARD.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_BRIDGE_CLOSEOUT_CARD.md)

---

## 6. Acceptance Tests

A bridge candidate should be judged against these tests.

| Test | Desired outcome | Kill condition |
|---|---|---|
| nontriviality | \(I(A:B)\) not identically zero on the live target family | remains trivial everywhere like raw local `L|R` |
| geometry sensitivity | varies with real geometry where appropriate | constant on both fiber and base |
| pointwise discrimination | can distinguish fiber from base if it claims to be pointwise | no difference between fiber and base |
| history sensitivity | history version should reflect actual trajectory windows | independent of history choice |
| kernel compatibility | works with \(-S(A|B)\), \(I_c\), \(I(A:B)\) | only supports an unsigned or ad hoc scalar |
| notation safety | does not collide with repo runtime symbols | reuses `rho_LR` or similar in conflicting ways |

---

## 7. Runtime Proxy Separation

These distinctions must stay explicit.

| Object | Current role | Why not promote directly |
|---|---|---|
| runtime `GA0` | live engine proxy | not the same object as source-backed \(\Phi_0(\rho_{AB})\) |
| `rho_LR` in repo probes | inter-chirality coherence block naming | collides with generic `Axis 0` cut-state notation |
| per-sheet Hopf coarse-graining | runtime executable mechanism | useful proxy, not a finished bridge theorem |

Key refs:

- [engine_core.py#L376](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/engine_core.py#L376)
- [engine_core.py#L602](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/engine_core.py#L602)
- [sim_weyl_dof_analysis.py#L84](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_weyl_dof_analysis.py#L84)

---

## 8. Executable Evidence

### 8.1 Strongest real surfaces

| Surface | What it supports | Current read |
|---|---|---|
| [axis0_full_constraint_manifold_guardrail_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_full_constraint_manifold_guardrail_sim.py) | real geometry + honest raw `L|R` control | local-only `L|R` stays MI-trivial; coupling works only as control |
| [axis0_xi_strict_bakeoff_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_xi_strict_bakeoff_sim.py) | strict bridge audit on live Hopf/Weyl engine | shell-strata pointwise killed, point-reference survives as pointwise discriminator, history stays live, direct `L|R` trivial |
| [axis0_full_spectrum_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_full_spectrum_sim.py) | broad bridge-family ranking | useful option sweep, but imports older bridge family surfaces and must stay lower-authority than the strict bakeoff |

### 8.2 Key result anchors

| Result | Anchor |
|---|---|
| raw local `L|R` remains trivial | [axis0_full_constraint_manifold_guardrail_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/axis0_full_constraint_manifold_guardrail_results.json) |
| shell-strata pointwise is loop-blind | [axis0_xi_strict_bakeoff_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/axis0_xi_strict_bakeoff_results.json) |
| point-reference varies on base but stays constant on fiber | [axis0_xi_strict_bakeoff_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/axis0_xi_strict_bakeoff_results.json) |
| history family stays nontrivial | [axis0_xi_strict_bakeoff_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/axis0_xi_strict_bakeoff_results.json) |
| broad sweep keeps `Xi_shell` and `Xi_hist_*` as options, but not as final doctrine | [axis0_full_spectrum_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/axis0_full_spectrum_results.json) |

---

## 9. Current Verdict

### 9.1 Strongest live bridge candidates

| Candidate | Verdict |
|---|---|
| `Xi_hist` | strongest live bridge family |
| point-reference | strongest live pointwise discriminator |
| shell family | still live only as a family; strongest replacement read is a boundary/interior shell-indexed cut-state family, while old shell-strata pointwise is killed |

### 9.2 Killed or demoted options

| Candidate | Verdict |
|---|---|
| raw local `L|R` | killed as sufficient |
| shell-strata pointwise | killed as pointwise bridge |
| coupled control | keep only as control |
| runtime `GA0` | keep only as proxy |

### 9.3 Short read

\[
\text{real geometry} + (L|R\ \text{cut}) \Rightarrow \text{trivial Axis 0}
\]

\[
\text{real geometry} + \Xi_{\mathrm{hist}} \Rightarrow \text{strongest live bridge family}
\]

\[
\text{real geometry} + \Xi_{\mathrm{ref}} \Rightarrow \text{best current pointwise discriminator}
\]

---

## 10. Open Items

| Open item | Why it remains open |
|---|---|
| exact cut \(A|B\) | still not fixed as one doctrine-level cut |
| exact `Xi_shell` | old shell-strata pointwise implementation is killed; strict shell replacement still needed, with the minimum shell cut target now typed in [AXIS0_TYPED_SHELL_CUT_CONTRACT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_TYPED_SHELL_CUT_CONTRACT.md) and the strongest live replacement read tracked in [AXIS0_XI_SHELL_STRICT_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_XI_SHELL_STRICT_OPTIONS.md) |
| exact `Xi_hist` construction | strongest live family, but still needs a typed history-window cut family and explicit \(\rho_c(t)\) construction before it becomes a strict contract |
| point-reference doctrinal role | strongest live pointwise discriminator, but still needs a clean answer to whether it remains only a discriminator or matures into an explicit open cut family |
| pointwise vs history unification | both remain live shapes |
| relation to runtime `GA0` | proxy-to-kernel relation still unresolved |

---

## 11. Do Not Smooth

- Do not promote raw `L|R` from guardrail control to doctrine.
- Do not promote runtime `GA0` from proxy to kernel.
- Do not reuse `rho_LR` as the generic `Axis 0` cut-state symbol.
- Do not promote old shell-strata pointwise behavior as the surviving shell story.
- Do not confuse point-reference discrimination with a finished bridge theorem.
- Do not confuse broad-spectrum ranking with strict bridge-quality proof.
