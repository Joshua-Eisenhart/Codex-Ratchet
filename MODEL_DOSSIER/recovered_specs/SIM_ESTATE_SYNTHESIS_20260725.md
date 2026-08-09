# Sim estate — synthesis of the two layouts, with OD-11 resolved

**Date:** 2026-07-25
**Inputs:** the external "Sim-Engine Estate Audit and Target Layout" + my measured layout, both attached by the owner.
**Status:** proposed. `promotion_allowed: false`. Every number below was measured this session or read off a running interpreter.

---

## 0. The headline: OD-11 was mis-framed, and the external doc is why

The external doc insists on separating **`cycle_identity`** from **`start_stage`**:

> "A cyclic rotation changes the selected starting coordinate but does not define a different loop... A science-method interpretation may prefer a starting stage, but that preference must not be inserted into the mathematical identity of the cycle."

Applying that test to the three rival deductive orders — combinatorially, then on the actual engine:

| Order | Same oriented cycle as the doc order? | Spectrum of composed superoperator |
|---|---|---|
| doc `Se→Ne→Ni→Si` | — | 1.0, **0.138740074**, 0.060888082, 0.060888082 |
| owner `Ne→Ni→Si→Se` | **YES** (cyclic rotation) | 1.0, **0.138740074**, 0.060888082, 0.060888082 |
| AR01 `Ne→Si→Se→Ni` | **NO** | 1.0, **0.141200647**, 0.060355230, 0.060355230 |

- doc vs owner: **max |Δeigenvalue| = 2.2e-15** — conjugate maps, machine precision. Same loop.
- doc vs AR01: **max |Δeigenvalue| = 2.5e-3** — genuinely different loop.
- The **inductive** orders are character-for-character identical in both sources.

**Consequences, stated plainly:**

1. **The doc order and the owner's N→S hypothesis are the same loop.** There was never a conflict between them. I framed OD-11 as "two orders, yours to rule" — that framing was wrong.
2. **The real outlier is the AR01 / Gemini pack order**, which is a different cycle, not a rotation.
3. This also explains my own bridge result (doc-order 7 cells, owner-order 6 cells): the difference was the **transient from a different start stage**, not a different loop — exactly what the external doc predicts.

**What is still genuinely open** is much narrower than OD-11 as I stated it: *which start stage the science-method reading prefers*, which is a presentation choice, not a mathematical one — plus whether the AR01 cycle is admissible at all.

---

## 1. Adopt from the external doc (it is stronger here)

| Item | Why it wins |
|---|---|
| **Cyclic `EngineSpec`** with `cycle_identity` / `start_stage` / `direction` / `initial_state` recorded separately | Resolves OD-11 above; stops an LLM changing a loop by rewriting where the list begins |
| **Five-level capability ladder** — `AVAILABLE → EXERCISED → INTEGRATED → LOAD_BEARING_FOR_<claim> → AUTHORITATIVE_FOR_<claim>`, no level-jumping | Strictly better than my three states; makes "installed ≠ integrated" mechanical |
| **"NumPy can veto, but cannot independently admit"** | The crispest statement of the containment rule; matches the installed seal exactly |
| **Nonassociativity × GPU reassociation** — CUDA.jl scans/reductions require associative operators; bracket-sensitive octonionic/Jordan probes need an explicit bracket tree, ordered kernel, no generic parallel reduction, and a **bracket-tree hash in the receipt** | A real hazard I had not flagged, and directly load-bearing for the nonassoc lane |
| **Per-lane env locks** (stable + candidate-upgrade), not one giant environment | Makes backend-removal tests real and containment testable |
| **Claim-type authority matrix** | Same object as the applicability registry from the AR01 mine — two sources converging |

---

## 2. Keep from mine (measured, and the external doc lacks it)

| Item | Measurement |
|---|---|
| **The basin is a single point** | 4 independent artifacts agree: every native schedule → 1 attractor, whole-space basin. Bloch contraction 0.399 / 0.341 — strict contractions |
| **Structure appears only off the contraction** | self-consistent chiral record coupling → **2 stable fixed points, basins [8,8]**; each engine alone → 1; anti-consistent → 0 (period-2). Direct product is still a contraction |
| **ρ-space cannot see the fuzz** | coherent vs decohered history extensions differ (distance 0.756; Hartley **1 bit vs 4 bits**) yet partial-trace to identical ρ_out, difference **exactly 0.0** |
| **PyTorch-only numerics do not seal** | `schedule_tournament_v0` REJECTS today — single-engine numeric, no second witness |
| **Flip battery + chain BMC** | mechanical anti-theatre, 0 LLM tokens (§4) |

---

## 3. ClaimGate corrections — verified true, and what is already fixed

The external doc's correction table is largely right. Checked against the running code:

| Its claim | Verdict |
|---|---|
| "Called `three_engine_seal.py` but normally requires two" | **TRUE** — requires ≥2 authoritative. The name is a misnomer; rename to `numeric_witness_seal` |
| "Hardcoded personal Python path" | **TRUE** — `SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"`, line 31. Must resolve from the sealed env and record the executable digest |
| "Fixed global tolerances" | **TRUE** — one global `AGREE_TOL = 1e-6`. Needs a typed metric registry (abs / rel / ULP / solver-error budgets) |
| "JAX rerun treated as independence" | **TRUE** — it is *reproducibility*. Independence needs native Julia construction + asymmetric mutation |
| "Metadata-only mode can pass" | **TRUE** — `SEAL_METADATA_ONLY`. Should cap at `TRANSPORT_OK`, never scientific admission |
| "Ordinary JSON parsing" | **ALREADY FIXED today** — `intake_supervisor.py` rejects duplicate keys, non-finite (incl. `1e400→inf`, dict-value tokens), and vanished locked floors. Corpus 7 HOLD/3 GAP → **10 HOLD/0 GAP** |
| "Agreement can hide a shared builder" | **TRUE and unfixed** — the highest-value remaining gap (§5) |

---

## 4. Stronger SMT + TLA+ — what exists now, and what is next

**Built and running today:**

| Tool | What it does | Result |
|---|---|---|
| `formal/ClaimGateChain.tla` | TLA+ module of the fired chain's **control flow** — not the science, because a checker cannot tell you a spec is faithful | 4 properties |
| `formal/chain_bmc_z3.py` | **Exhaustive** BMC (chain is acyclic → unroll to stage count covers all paths) + guard-erasure and structural-mutation polarity | all 4 unsat; `NoAdmitWithoutAllChecks` broken by 5 mutations |
| `formal/chain_bmc_cvc5.py` | Independent hand-built cvc5 encoding, not a z3 round-trip | agrees on every property and every load-bearing guard |
| `harness_patch/flip_harness.py` | erase / perturb / core battery on a **mechanism** | real loop flip_rate **1.0**, commuting control **0.0**, 0 tokens |
| `harness_patch/jax_smt_bridge.py` | JAX×SMT, three layers measured | batching **5.3×** at n=128, agreeing 5.6e-17 |

**Vacuity is reported, not hidden:** `NoSilentExit` is labelled **VACUOUS** — no erasure or mutation can express its counterexample, so it restates the encoding rather than testing it.

**Next, in value order:**

1. **TLC as a third checker** — needs a JRE (`brew install --cask temurin`). Would make the three-way genuinely independent at the *checker* level, not just two encodings of one spec.
2. **Spec the EngineSpec, not just the gate.** The cycle-identity result above is exactly the kind of thing TLA+ should own: state `cycle_identity` invariance under rotation as a property, and let the checker enforce that no backend can change a loop by re-listing it.
3. **Typed metric registry** replacing the single global tolerance — per-metric ID, units, dtype, shape, error budget. This is what makes cross-engine agreement meaningful instead of numerology.
4. **Interval / rational lane** (the external doc's "exact obligation lane") — currently absent; z3+cvc5 only cover discrete finite obligations.

---

## 5. The one gap both documents agree is the most serious

**A shared numerical builder can satisfy two witness roles.** The seal counts two engine values and re-runs the JAX leg — that is reproducibility, not independence. Neither document has fixed it, and the AR01 covert-cheat audit named the same thing (CHEAT-001: legs importing one `_common` result builder).

The fix is specified and unbuilt: give each lane only the frozen contract and raw fixture, never executable decisive common code; require **asymmetric mutation** (mutate Julia → only Julia changes; mutate JAX → only JAX changes), **dependency-kill** (kill a lane → it fails, no fallback), and classify decisive overlap as `schema-only | fixture-only | decisive`. Plus the common-mode control: two lanes can independently implement the *same wrong equation*, so a hand-derived exact-small oracle independent of both is required.

---

## 6. Cloud GPU — corrected targets

The external doc's phase ladder (C0–C5, cloud is a venue not an authority) is right and I adopt it. Three target corrections from measurement:

| Proposed GPU target | Correction |
|---|---|
| Fixed-point solvers (Anderson/JAXopt) for the attractor basin | **Wrong target.** The map is a strict contraction — Banach already gives the unique point. Renting a GPU to confirm a theorem. Aim at the **hybrid/piecewise map with record-mediated switching**, where the basin count is unknown |
| BlackJAX sampling "the fuzz" | **Wrong space.** ρ-space is structurally blind to `j≠k` (measured: identical ρ_out, difference exactly 0.0). Sample the **history/record space** |
| PyG for `G → G'` renesting | **Correct, and the highest-value item** — the only proposed mechanism whose test is currently unrunnable ("the graph-rewrite machinery does not exist in the repo") |

Binding rule for the whole lane, from the installed seal: **every GPU number needs a CPU engine value alongside it, or it does not seal.** `Reactant.jl` is the highest-value cloud addition — it compiles Julia to XLA, supplying the mandatory second engine on the same rented hardware.

---

## 7. Adoption order

1. Freeze the cyclic **`EngineSpec`** with `cycle_identity` / `start_stage` / `direction` — and record the OD-11 resolution in it.
2. Rename the seal, resolve the interpreter from the sealed env, cap metadata-only at `TRANSPORT_OK`.
3. Typed **metric registry** replacing the global tolerance.
4. **Independence harness** (§5) — asymmetric mutation + dependency-kill + decisive-overlap classification.
5. Five-level capability ladder over the installed estate; publish the honest level per library.
6. Per-lane env locks (stable + candidate).
7. TLC third checker; then spec the EngineSpec in TLA+.
8. Cloud pilot: JAX CPU-x64 → one GPU parity, then Reactant.jl for the second engine, then PyG renesting.

**Unchanged ceiling:** ClaimGate is admission control at `E2_SUPERVISED_EXECUTION`. It may not say "bypass prevented". Cloud GPU adds no authority vote. No backend, no cloud run, and no model promotes its own result.
