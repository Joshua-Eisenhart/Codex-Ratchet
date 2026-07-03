140,307
## A. Formal Ratchet Definition

Source ceiling: the ratchet spec is a draft/spec surface, not admission or proof; it explicitly says “doctrine draft, no admission” and “formal_admission_allowed: false” (`system_v7/.../ratchet_definition_and_emergence_spec_DRAFT_20260614.md:1-5`, `:210-216`).

A finite ordered survivor ratchet is not mere dynamics. It is a finite, exclusion-first, history-carrying survivor process satisfying six primitives:

1. `R1` finitude: finite carrier `S`, finite probe families `M_k`, decidable terminating admissibility predicates (`ratchet_definition...:41-46`).
2. `R2` strict contraction: `X_{k+1} = {x in X_k : x admissible under C_{k+1}}`, hence `X_{k+1} subset X_k` (`:45-47`).
3. `R3` state/history dependence: `Adm(C, x, H, G)`, not `Adm(C, x)`; without history dependence, tests commute and there is no ratchet (`:47`).
4. `R4` typed noncommuting full-state update: some typed `C_i,C_j,S_0` satisfy `U_i o U_j(S_0) != U_j o U_i(S_0)` and the difference survives an observable quotient (`:48`).
5. `R5` append-only receipt memory plus no implicit re-introduction: deleted `x` only returns via explicit logged replay, as a fresh token/new branch/identity (`:49`).
6. `R6` trivalent status plus progress measure: `ACCEPT/PARK/REJECT`; non-strict/stalling steps must reduce `mu` or are non-steps (`:50`).

Formal object/registers: `(X_k, H_k, C_k, pi_k, M_k, E_k, G_k)`, where `X_k` is the finite survivor set, `H_k` append-only ledger/graveyard, `C_k` typed admissibility constraints, `pi_k` trivalent status map, `M_k` finite probe family plus quotient `~_k`, and `E_k/G_k` derived readouts, not core axioms (`ratchet_definition...:54-68`).

Distinguishing line: static predicates / commuting filters are not enough. The doc says static/extensional tests commute by set intersection; map noncommutation comes only when applying a constraint mutates history/geometry used by later tests (`ratchet_definition...:98-101`). Controls explicitly classify commuting filters, no-memory re-entry, and generation-first addition as “NOT a ratchet” failures (`:184-190`).

Emergence criterion: `F01 + exclusion-first + N01` only earns a skeleton. The corrected chain requires typed/full-state N01, append-only memory, and finite observable quotient/bounded readouts to earn an irreversible/terminating ratchet (`ratchet_definition...:74-85`). True emergence still requires deriving the ratchet from lower-level local rules, e.g. ring-checkerboard QCA, not just renaming the definition (`:103`, `:204-206`).

## B. Theorem Obligations

Measured by `manifold_dual_ratchet_foundations_v0/RESULTS.md`:

- No-readmission / Hell monotonicity: bounded run measured reentry `0`; z3/cvc5 prove axiomatized no-reentry `unsat/unsat`, erased control `sat/sat` for both `E_then_G` and `G_then_E` (`RESULTS.md:26-31`).
- Quotient plateau / endpoint-like bounded stabilization: stable quotient plateau first binds at step `14`; both recompute orders end with `42` quotient classes (`RESULTS.md:12-24`).
- E/G order load-bearing: final counts match, but binding-order measurements differ, so order matters in this bounded run (`RESULTS.md:33-35`).
- Downstream entropy discipline: `Adm_C` excludes entropy; entropy remains downstream readout (`RESULTS.md:82-88`).
- Quotient-grounded geometry: all geometry/region structure computed on quotient classes `S/~_P`, not raw state space (`RESULTS.md:86-88`).
- Proto-regions/readouts: 11 late quotient-regions with MI/entropy summaries were measured for both recompute orders (`RESULTS.md:44-80`).
- Cross-runtime parity: numpy/Julia parity at `1e-9` on class counts, entropy tables, metric spectra, tiers, flux, binding order, and narrow deltas (`RESULTS.md:82-84`).

Still unformalized/unproven globally:

- Full-object termination: survivor sets terminate under finite descent, but `(X,H,G,E)` does not terminate unless history/readouts are finite, quotiented, or the test stream is finite (`ratchet_definition...:93-97`).
- Fixed-point existence/uniqueness for co-ratchet `E<->G`: the doc calls the simultaneous equations a fixed-point problem requiring sequentialization or a joint variational fixed point with existence + uniqueness (`entropic_monism...:137-145`).
- Background independence as theorem: recomputing `E` and `G` each step is the intended background-independent move, but the order/fixed-point mechanics remain open (`entropic_monism...:124-151`).
- Bridge theorem `Phi`: homomorphism only if the sim constructs `Phi` and verifies `Phi o Update_lex = Update_geo o Phi`; otherwise analogy/spec only (`ratchet_definition...:107-121`, `:170-178`).

## C. Xi Candidates

Axis packet baseline: Axis 0 needs a cut state; `Xi : geometry sample or history window -> rho_AB in D(H_A otimes H_B)` is still the missing bridge (`AXIS_0_1_2_QIT_MATH.md:99-110`, `:334-358`).

- `Xi_pt`: `x -> (c_x, rho_{c_x}(x))`, where `c_x = A_x|B_x`; admitted pointwise family, not finished (`AXIS_0_1_2_QIT_MATH.md:105-108`, `:118-121`).
- `Xi_shell`: `x -> {(r, w_r, rho_{A_rB_r}(x))}_r`; shell-cut pointwise pullback evaluates `sum_r w_r I_c(A_r>B_r)` (`AXIS_0_1_2_QIT_MATH.md:107`, `:119`, `:133-145`).
- `Xi_hist`: `h|_[t0,t1] -> {(t,c,w_c,rho_c(t))}_{t,c}`; history functional `1/T int_0^T sum_{cut in C} w_cut I_c(cut; rho_h(t)) dt` (`AXIS_0_1_2_QIT_MATH.md:108`, `:120`, `:134-137`).
- `Xi_ref`: not fully defined in the Axis packet itself; the linked bridge packet defines `Xi_ref : (x_ref, x) -> rho_AB^ref(x)` with candidate cut `A_ref|B_x`, as strongest pointwise discriminator, not final doctrine (`system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md:90-104`; `system_v4/docs/AXIS0_XI_REF_STRICT_OPTIONS.md:13-25`, `:66-76`).

Weights: `w_r`/`w_c` are required shell/cut weight or measure factors, but not uniquely fixed. Shell contract: `w_r = shell weight or measure factor`; exact weighting discipline is open (`AXIS0_TYPED_SHELL_CUT_CONTRACT.md:27-46`, `:100-107`). History contract: `w_c = cut weight or measure factor`; exact weighting discipline is open (`AXIS0_TYPED_HISTORY_WINDOW_CUT_CONTRACT.md:27-46`, `:99-106`).

`Phi_0` forms:

- Simple preferred kernel: `Phi_0(rho_AB) = -S(A|B)_rho = I_c(A>B)_rho` (`AXIS_0_1_2_QIT_MATH.md:139-147`).
- Shell/global form: `Phi_0(rho)=sum_r w_r I_c(A_r>B_r)_rho = -sum_r w_r S(A_r|B_r)_rho` (`AXIS_0_1_2_QIT_MATH.md:143-145`; `AXIS0_TYPED_SHELL_CUT_CONTRACT.md:42-48`).
- History form: `phi_0[h] = 1/T int_0^T sum_{cut in C} w_cut I_c(cut; rho_h(t)) dt` (`AXIS_0_1_2_QIT_MATH.md:134-137`; `AXIS0_TYPED_HISTORY_WINDOW_CUT_CONTRACT.md:42-48`).

Discriminators: `A0-kernel discriminator`, `Hopf pointwise pullback`, `History-vs-pointwise Ax0`, `Xi-bridge bakeoff`, and `Fiber/base transport test` distinguish entropy primitive, pointwise viability, history-vs-pointwise status, least-arbitrary bridge family, and transport effects (`AXIS_0_1_2_QIT_MATH.md:215-223`). Current strict bakeoff says direct `L|R` MI-trivial, shell-strata pointwise geometry-blind, point-reference fiber/base-discriminating, history-window nontrivial (`AXIS_0_1_2_QIT_MATH.md:180-197`).

## D. Pipeline Spec

Build order:

1. Dual/co-ratchet: update survivors, quotient, entropy readout, and induced geometry each step: `X_{t+1}=Adm_C(X_t,Q_t,...)`, `Q_{t+1}=X_{t+1}/~_P`, then recompute `E` and `G` (`entropic_monism...:122-133`). Corrected discipline: `Adm_C` reads `Q_t` and already-induced `G_t`, not `E_t` (`entropic_monism...:147-151`).
2. Cut lattice on quotient: layer order requires probe quotient `S/~_M` first, then density/marginals, then L8 cut lattice `2^{n-1}-1` bipartitions, L9 Schmidt strata, L10 entropy per cut (`manifold_layer_order...:47-56`).
3. Ratchet-within-layer: `X_{A,k+1} = {rho in X_{A,k}: C_{A,k+1}(rho, geometry already induced)}`, with geometry recomputed per constraint step (`manifold_layer_order...:245-256`).
4. Entropy/readout licensing: entropy form must name its enabling lower layer/cut/channel/record; unlicensed entropy use fails (`manifold_layer_order...:307-316`).
5. Bridge: choose `Xi : geometry/history -> rho_AB`; until then Axis 0 cut-state evaluation is open (`AXIS_0_1_2_QIT_MATH.md:99-121`, `:334-358`).
6. Read `Phi_0`: evaluate `-S(A|B)`, coherent information, shell-weighted coherent information, or history functional only after `rho_AB`/cut family exists (`AXIS_0_1_2_QIT_MATH.md:139-147`).

Exists now: bounded dual-ratchet foundation diagnostic, quotient regions, Hell/Purgatory separation, E-not-in-Adm, quotient-computed geometry (`RESULTS.md:10-35`, `:82-88`). Missing now: canonical cut lattice output from that foundation run, exact `Xi`, exact cut `A|B`, exact `rho_AB`, and final `Phi_0` evaluation (`AXIS_0_1_2_QIT_MATH.md:334-358`; `AXIS0_MANIFOLD_BRIDGE_OPTIONS.md:274-283`).

## E. Open Gaps

OPEN: whole-object termination beyond survivor-set stabilization (`ratchet_definition...:93-97`).

OPEN: co-ratchet `E/G` recompute order or fixed-point existence + uniqueness (`entropic_monism...:137-151`).

OPEN: exact bridge `Xi : geometry/history -> rho_AB` (`AXIS_0_1_2_QIT_MATH.md:334-358`).

OPEN: exact cut `A|B` for Axis 0 numerical evaluation (`AXIS_0_1_2_QIT_MATH.md:334-339`).

OPEN: exact `Xi_shell`; old shell-strata pointwise is killed, strict shell replacement still needed (`AXIS0_MANIFOLD_BRIDGE_OPTIONS.md:274-281`).

OPEN: exact `Xi_hist` construction; strongest live family, but still needs typed cut family and explicit `rho_c(t)` (`AXIS0_MANIFOLD_BRIDGE_OPTIONS.md:274-281`; `AXIS0_TYPED_HISTORY_WINDOW_CUT_CONTRACT.md:99-106`).

OPEN: point-reference doctrinal role; strongest pointwise discriminator, not final bridge theorem (`AXIS0_XI_REF_STRICT_OPTIONS.md:121-143`, `:188-202`).

OPEN: exact shell weights `w_r` and history/cut weights `w_c` (`AXIS0_TYPED_SHELL_CUT_CONTRACT.md:100-107`; `AXIS0_TYPED_HISTORY_WINDOW_CUT_CONTRACT.md:99-106`).


