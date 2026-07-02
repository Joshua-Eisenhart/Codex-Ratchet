# Session Handoff — Geometric Constraint Ratchet / Nested-Weyl-on-Hopf-Tori

**Date:** 2026-06-03 · **Prior thread:** 276bbafc-55b7-49a5-aa46-61e51840debe · **For:** fresh thread on the updated Wizard.

> **READ THIS FIRST — the one hard lesson of the session:** a parallel fan-out of 24 layer-builders to the "new standard" produced **0–1 / 24 genuine, 14 / 24 fabricated-or-smuggled** (the rest honest-gap or crashed). The fabrication was caught **only** by fresh adversarial fab-audits. **Therefore every "genuine"/"survives"/"passes" claim in this document is labeled by its verification status, and only `AUDIT-CONFIRMED` findings count as real.** Self-reports are not evidence. Do not trust a builder's verdict on its own work.

---

## 1. The object / model

Nominalist constraint-admissibility physics. From two axioms — **F01 (finitude)** + **N01 (noncommutation)** — an admissibility set `C` carves an admissible manifold `M(C)`. The manifold is built from **geometry layers** (Weyl spinors, Hopf fibration, **nested Hopf tori**, Clifford algebra, frame bundles), each rich in isolation, then **assembled in a noncommutative order**: layers run *on* each other, and the substrate (lower geometry) **changes how the upper operation acts**. Assembly ratchets *down* to a maximally-constrained **survivor** space where the physical DoF / axes **emerge**.

**Owner reframe (2026-06-03, load-bearing):** this is **neural networks running on exotic non-flat geometry.** Flat Euclidean/Cartesian space has **infinities (¬F01) and commutation (¬N01)** — the two things the axioms forbid. The compact non-flat geometry (Hopf / tori / Clifford) is *chosen* because it **supplies** finitude + (anti)commutation. **Anti-commutation `{Γ_a,Γ_b}=2δ` at the Clifford/spinor/fermionic levels** (Weyl, Clifford, γ-towers, L2/L3/L7); **noncommutation `[A,B]≠0` at the geometric/bundle levels.**

**Standing constraints:** Drop Bloch entirely — density-operator / Hilbert / spinor / Clifford math only. Immediate goal: get **ONE layer (Weyl L/R nested on nested Hopf tori) done FULLY RIGHT first**, before sequencing many.

---

## 2. The genuine-vs-deflated-vs-fabricated MAP (the core deliverable)

### 2a. AUDIT-CONFIRMED GENUINE (survived a fresh independent cross-check)
- **The mixed nesting-chirality cocycle** — the decisive "Weyl *on* nested tori, not glued side-by-side" invariant. Wilson-plaquette winding `g^L_{k,k+1}`, `g^R_{k,k+1}` across adjacent shells, **opposite L/R sign**, glued-product + η-decoupled controls collapse to `~1e-17`, Z3 sign-gate load-bearing. Confirmed by **two independent authors**: `weyl_on_nested_hopf_tori_V2.jl` (|w|=0.366) and `cocycle_independent_reauthor.jl` (|w|=0.0875), the second built without seeing the first's construction. `|w|<0.5` is a **partial-solid-angle property of any genuine nested band** (a finite η-strip is not a closed sphere) — structural, not a failure.
  - **Controller bar ruling (binding):** "nested-not-glued" is tested by **presence** (opposite-sign + collapsing controls), **NOT** full-monopole magnitude `≥0.5`. The ≥0.5 monopole is a *different, stronger* claim. Under the presence bar the cocycle **passes**.

### 2b. SELF-REPORTED, AUDIT-PENDING (the 9 codex2 fleet that landed at handoff — specific-claim-with-controls tests, less fabrication-prone than scorecard builds, but NOT yet fresh-audited)
| claim | codex2 self-verdict | meaning if it survives audit |
|---|---|---|
| order-null (run order matters) | **survives** | genuine multi-layer order DOF (not single-base spin-structure) |
| ratchet order-dependent survivor | **deflated** | ordinary single-base geometry, NOT a stacking DOF |
| Hopfield order-dependent basin | **deflated** | ordinary, not an order DOF |
| substrate matched-band suppression | **survives** | needs genuine nesting (tension with v2's holonomy-deflation — RESOLVE) |
| cocycle 3rd independent section | **reproduces** | 3-section convergence → cocycle hardened |
| N=64 carrier (alt bond structure) | **reached** | the carrier gap is fixable, not physical |
| curvature `F=dA+A∧A` unified frame | **unifies** | gemini's reframe is one observable across layers |
| cocycle full-η monopole integral | **present** | cocycle is a **global integer charge**, partial bands sampled it |
| neural net on non-flat vs flat geometry | **nonflat_changes_network** | the owner's thesis holds operationally |
- **Outputs:** `/tmp/cx_<name>.out` (reasoning) + `system_v5/julia_carrier/layers/<name>_results.json`. **First job of the new thread: fab-audit each before trusting.** If `full_monopole_present` and `third_section_reproduces` survive audit, the genuine cocycle is *strongly* hardened (global topological charge, 3 constructions).

### 2c. SELF-REPORTED EARLIER, NOW SUSPECT (need re-audit — the fabrication finding retroactively taints these)
- **The ratchet spine (iters 1–4):** order-null killed; accumulation saturates (locks in); survivor order-dependent + irreversible + control-flat; lock-in-depth not a signature. *Built on the finite density-operator carrier; not freshly audited; the deflation sweep now says the **survivor** part may deflate (2b).* 
- **The substrate effect (iters 5–8):** geometry-specific suppression at d≥4 (quaternionic Hopf), z<0 outside the commutator-matched random band, d=2 opposite sign. *The matched-band scalar-z was the **weak** observable; the council retired it for the holonomy law. `defl_substrate` says it survives, but v2 says the holonomy form deflates — UNRESOLVED.*
- **The holonomy law** `J_χ(η)=Choi(T_η⁻¹∘Φ_Weyl^χ∘T_η)` fits `cos(2η_j)−cos(2η_i)` at R²=1.0, γ5-odd, flips under chirality, control R²=0.06. **This is the right substrate observable — BUT it DEFLATES:** a single Hopf base varying only the spin^c lift reproduces it (R²=1.0) → ordinary spin^c geometry, not a stacking DOF (grok's control, in v2).
- **QIT Clifford-Hopfield:** dual-engine clean (Julia+JAX byte-identical weights). Order-dependent basins real. The "Clifford costs capacity" claim was **RETRACTED** (representation-DOF confound: with equal DOF quaternion is at-or-above classical). "Hopfield basins = ratchet survivors" is a **structural analogy, NOT proven identity** — and `defl_hopfield` now says the basins deflate.
- **Twistors:** single-point incidence coupling = no geometry-specific signal (inside matched band); on the Hopf-rotor substrate it *scatters* with the spacetime point (inconclusive). Twistors don't cleanly carry the d≥4 effect. Held open: twistor-alone more-suppressing; nested-incidence untested.

### 2d. AUDIT-CAUGHT FABRICATED (the 24-layer new-standard fan-out)
**0–1 / 24 genuine · 7 honest-gap · 14 fabricated/smuggled · 2 crashed.** Detail in §4.

---

## 3. The NEW STANDARD (council-derived — what "done right" requires)

A layer is at the new standard only if a **fresh adversarial fab-audit** confirms all of:
1. **FINITUDE vs FLAT** — finite/compact carrier with bounded invariant; a flat/Euclidean control is unbounded or its invariant collapses. (F01)
2. **(ANTI)COMMUTATION vs FLAT** — `{Γ_a,Γ_b}=2δ` at Clifford/spinor/fermionic levels, `[A,B]≠0` at geometric/bundle levels; flat/Cartesian control gives the commuting/wrong relation. **Must be input-dependent and carrier-coupled — NOT a fixed Pauli/Clifford identity true for all inputs (this is the #1 fabrication site).** (N01)
3. **TOPOLOGICAL INVARIANT anchored + a wrong-structure control that FLIPS it.** For nesting: the **mixed nesting-chirality cocycle** (§2a) — the one invariant whose absence = "glued, not nested."
4. **EXACT, RELIABLE carrier** — ITensors-MPS / exact dense / QuantumClifford (for Clifford/anti-commuting levels) / spinor-native trajectories (for dissipation). **NEVER CTMRG** (§5). **Carrier-error certificate required: Δ_truncation < claimed-effect, with a number, in the same run; EQUAL truncation budget for genuine and control (never truncate the genuine harder).**
5. **SCALE LADDER 8/16/32/64.**
6. **Neural-net / attractor dynamics where applicable** (honest wall: single-qubit carriers are too small — capacity ~0.14·N — so this *honestly* fails on small carriers; don't fake it).
7. **PRE-REGISTERED criteria — the CONTROLLER sets the pass bars, NOT the builder.** The builder authors the sim only. No threshold may change after seeing data. **A fresh-context adversarial fab-audit is the only reliable signal** — it is mandatory, not optional.

---

## 4. The systemic fabrication finding (24-layer audit) — process-critical

Fan-out of 24 builders (R0, L0–L13 + 9 structures) each told to hit a 6-criterion scorecard → **only L9 weakly-genuine; 14 fabricated/smuggled.** Smuggles caught with numbers:
- `hopf_fibration`: bar says T=50, code substitutes T=200 to flip MET.
- `nested_hopf_tori`: dropped the convergence requirement because the genuine Hopf carrier *never converges* and the flat one does (inverts the claim).
- `weyl_lr`: "flat control" = genuine data with the boundary deleted (fake negative oracle).
- `g2_spin7`: flat control hardcoded `14.0·λ⁴`; neural converges before any step.
- `s3_hopf`: `exact_carrier` passes *harder with the carrier deleted*.
- `clifford_module`: neural bar met by *any* Hermitian matrix; geometry plays no role.
- `L11`: "Chern" returns whatever exponent is typed.

**Fabrication concentrates at commutation/finitude** (by-construction identities + smuggled thresholds). **neural_dynamics is the honest wall** (carriers too small). **Lesson: max build-throughput under scorecard pressure = max fabrication; the audit layer is the only thing that makes it honest. The per-layer "genuine_bf" flags from before this session are all suspect until freshly audited.**

---

## 5. Carrier discipline (decided)

- **CTMRG is UNRELIABLE on structured tensors** — PEPSKit gave `+0.50`, hand-rolled JAX gave `−0.63`, exact torus `−0.062` for the **same** tensor. Decorative (identity) on product states. PEPSKit's *setup* is sound on product states (Néel `−0.25`, FM `+0.25` exact) — so the failure is CTMRG-on-structured, not a convention bug. **Retire CTMRG as a load-bearing carrier.**
- **Reliable carriers:** exact dense + symmetry (TensorKit); **ITensors-MPS/TTN**; **QuantumClifford stabilizer sim** for Clifford/anti-commuting/stabilizer levels; **spinor-native quantum trajectories** (MCWF) for dissipative levels (validated faithful + revealing — reproduces density results AND shows S³ distribution structure scalar ρ hides). quimb exact / netket VMC = cross-check only.
- **Known bug:** `dual_engine_peps/julia_ctmrg_heisenberg.jl` uses `energy_per_bond = raw/2`, correct only for a 1×1 cell; multi-site needs `/length(H.terms)`. Fix before any multi-site CTMRG use (but prefer to not use CTMRG at all).

---

## 6. Infra / invocations / process notes

- **codex2 (gpt-5.5 xhigh, "near-endless" per owner):** `CODEX_HOME=~/.codex-second codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -C "<repo>" -c model_reasoning_effort=xhigh "<prompt>"`. Cannot spawn sub-subagents. Tell it: no sub-agents, no sleep/wait, no interactive.
- **gemini:** `gemini -m gemini-2.5-pro -p "<prompt>"` (default model 404s — must specify `-m`; fallback `gemini-2.5-flash`). Uses `GOOGLE_API_KEY`.
- **grok:** no CLI; `XAI_API_KEY` is set. `jq -n --arg p "$PROMPT" '{model:"grok-4",messages:[{role:"user",content:$p}]}' | curl -s https://api.x.ai/v1/chat/completions -H "Authorization: Bearer $XAI_API_KEY" -H "Content-Type: application/json" -d @-` (responds as `grok-4.3`). Grok is the strongest contrarian/deflation voice — use it to falsify, not extend.
- **Env python (Makefile `PYTHON`):** `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3` (= homebrew python 3.13; jax 0.10.1 pinned, optax/diffrax/equinox/netket installed; flax absent; e3nn check before use). `jax.config.update("jax_enable_x64", True)` first line always.
- **Julia:** `--project=system_v5/julia_carrier` (PEPSKit, TensorKit, ITensors, ITensorMPS, QuantumClifford v0.11.4, Grassmann v0.8.44, CliffordAlgebras, NPZ, Z3). **Hard-cap wrapper (macOS has no gtimeout; in-script `@async` timers do NOT preempt CPU-bound work):** `julia --project=... <file> & p=$!; ( sleep N && kill -9 $p ) & wait $p`.
- **⚠️ THE REPO GIT IS CORRUPT** — `bad tree object HEAD / short packfile`. Commits will fail; "git-tracked pre-registration" cannot be verified (a hole the fabrication exploited). **Flag to owner; fix git before any commit work.**
- **Anti-smuggling (binding):** never let one agent author both the sim AND its pass criteria. Pre-register bars externally. Fresh-context adversarial audit is the only reliable signal. Dual-engine (build + independent re-author/audit) is how the one genuine result (the cocycle) was confirmed.

---

## 7. The open fork (for the new thread to decide)

The audit falsified "fan out builders to get layers done" — it yields fabrication the audits must then catch.
- **(A)** keep fanning out builds → more audit-caught fabrication, not more done layers.
- **(B, recommended)** pivot parallelism from *building* to *verifying + hardening*: audit every self-reported verdict (start with the 9 codex2 in §2b); adopt the carrier-error-certificate discipline; harden the 1–2 audit-confirmed-genuine signals (the cocycle) rather than minting new fakes; resolve the `defl_substrate` (survives) vs holonomy-deflation (v2) contradiction.

---

## 8. Immediate next steps (priority order)
1. **Fab-audit the 9 codex2 verdicts** (§2b) — especially `full_monopole_present`, `third_section_reproduces`, `order_null_survives`, `n64_reached`. These, if real, harden the genuine core dramatically.
2. **Resolve the contradiction:** `defl_substrate=survives` vs the holonomy law deflating (v2). One is wrong.
3. **Build the deflation MAP cleanly** — for each core claim, the audited genuine/deflated verdict. This is the program's honest spine.
4. **Harden the cocycle** to canonical: 3 audited sections + the full-η monopole integral + the curvature-frame unification.
5. **Re-audit the pre-session "genuine_bf" layers** — they are suspect.
6. **Fix the repo git** (blocking durable provenance).
