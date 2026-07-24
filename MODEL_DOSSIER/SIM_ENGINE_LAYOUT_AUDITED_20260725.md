# Sim engine layout — audited, with numpy restored and the cloud GPU lane

**Date:** 2026-07-25
**Source:** owner's attached docs (`gemini 4 manifold layers and entropy.txt`, the Geometric-Entropy Ratchet PDF) + measured verification of every library and gate claim below.
**Status:** proposed layout. `promotion_allowed: false`. Every version number here was read off the running interpreter, not recalled.

---

## The one rule the whole layout hangs on

**One heavy runtime owns the machine at a time.** DLPack / zero-copy pointer sharing is dead on a 16 GB M1 — it creates memory-lifetime coupling across runtimes and risks axis corruption because row-major and column-major do not universally reverse dimensions.

Replaced by **tombstone-and-boot**: each process boots, reads the previous stage's immutable content-addressed artifact, does its bounded work, writes output + receipt, and **exits completely** to release RAM before the next boots.

```
Julia ──exit──► JAX ──exit──► numpy satellites ──exit──► SMT ──► ClaimGate ──► Lev
 (reference)    (workhorse)    (arbiters)         (proof)   (seal)      (decide)
```

---

## The layout

| # | Lane | Role | Libraries (verified installed) | Seal status |
|---|---|---|---|---|
| 1 | **Julia** | canonical reference semantics; exact quotients, extensions, cochain topology | QuantumOptics, QuantumClifford, ITensors, Z3, Attractors, CliffordAlgebras, Grassmann · *project-local:* Catlab, Metatheory | **authoritative** |
| 2 | **JAX x64** | atemporal workhorse — the 16 stage placements, dense trajectories | jax 0.10.1, diffrax 0.7.2, ott 0.6.0, quimb 1.14.0, netket 3.21.0, galois 0.4.11 | **authoritative** |
| 3 | **numpy satellites** | arbiters — read JAX trajectories, emit candidate ASTs + typed residuals | pysindy 2.1.0, pykoopman 1.2.1, pydmd, sympy 1.14.0, scipy 1.17.1, numba 0.65.0, numpy 2.3.4 | **never load_bearing** — by design |
| 4 | **SMT / proof** | exact discrete obligations over the satellites' ASTs | z3-solver, cvc5 | supportive; load-bearing in specific arrows |
| 5 | **Annealing / factor graph** | bounded search comparators | dimod 0.12.22, neal 0.6.0, pgmpy 1.1.2 | control-adjacent |
| 6 | **PyTorch / cloud GPU** | irregular + mutating topology, tensor-network compression | torch 2.11.0 (local, unused) → rented GPU | **authoritative** — see §4 |
| 7 | **ClaimGate → Lev** | trust, provenance, policy | three_engine_seal, claim_admission.mjs, `lev eval run` | control plane, not physics |

---

## 1. numpy is back — and it needs no gate change

This was the item worth checking hardest, and it resolves cleanly.

The attached doc says, in its own words, that the mechanical seal **"hard-rejects any receipt that labels `numpy`, `scipy`, or `mpmath` as load_bearing."** That is exactly what `three_engine_seal.py` already does (`CONTROL_ONLY = {"numpy","scipy","mpmath"}`). So the new layout and the installed gate agree; **nothing about the seal changes.**

What "numpy back in" actually means:

- numpy returns as **lane 3** — an independent *analytical satellite process*, not an engine.
- PySINDy / PyDMD / pykoopman are **candidate compilers**, not axiom discoverers. PySINDy fitting `ẋ = f(x)` to a JAX trajectory produces a *proposal*.
- Its residual must be **decomposed, never treated as one fuzz bound**:
  `r = r_diff + r_solver + r_projection + r_observation + r_library + r_model + r_unresolved`
- Output is a **parsed canonical AST**, never a free-form string.
- Current honest status: **AVAILABLE** (installed, importable), `load_bearing` in zero sealed arrows.

So the rule stays simple: numpy may *analyse* what the engines computed; it may never *be* what computed it.

---

## 2. Cloud GPU — the sealing rule that makes it work

`AUTHORITATIVE = ("julia", "jax", "torch", "pytorch")` — verified at `three_engine_seal.py:30`. **PyTorch already counts as an authoritative engine.** So a GPU lane can produce sealed receipts.

But the seal requires **≥2 authoritative engines carrying numeric values that agree < 1e-6**. That gives one binding rule for the whole cloud lane:

> **Every GPU result needs a CPU cross-check recorded as an engine_value** — either a JAX x64 or a Julia computation of the same observable. A GPU-only number cannot seal.

This is not hypothetical. The repo has exactly one receipt the seal rejects today, and it is this failure mode:

```
system_v8/schedule_tournament/results/schedule_tournament_v0/receipt.json
REJECT — verified=none
```

codex1 traced it with file:line evidence: the producer imports and executes **only torch** (`schedule_tournament_v0.py:70-76, 98-116, 188-202`); the generated candidate subprocesses likewise use only `torch.matrix_exp`/`torch.linalg`; **no Julia or JAX execution path exists**. Numeric values were computed but there is no `engine_values` field and no second-engine witness. So it is *not* a case of values being omitted — it is a genuinely single-engine numeric sim. It must either gain a second engine or declare `numeric_engine_required=false` with a reason.

Treat that receipt as the cloud lane's preview: **PyTorch-only numerics do not seal.**

### Cloud lane libraries, by what they are actually for

| Need | Library | Why this one |
|---|---|---|
| irregular / **mutating** topology `G → G'` | PyTorch Geometric | message passing over arbitrary graphs; this is the renesting machinery the tournament listed as NOT RUN |
| compress large constraint manifolds | TensorNetwork / MPS-PEPS | contract without hitting memory limits |
| topological-stress gradients | torch autograd / EBM | exact gradient of a declared stress functional |
| fixed points / equilibria | JAXopt (Anderson) | **see §3a — target the hybrid map, not the contraction** |
| sampling the uncollapsed field | BlackJAX 1.5 | **see §3b — must run on history space, not ρ** |
| toroidal boundaries + jk-shell neighbours | **JAX MD — NOT INSTALLED** | named in the doc as the best fit; genuine gap |
| Julia on the same GPU | **Reactant.jl** | compiles Julia to XLA — the same backend JAX uses. This is the highest-value cloud addition: it lets the *reference* engine run on the rented GPU, supplying the mandatory second engine on the same hardware |

---

## 3. Audit — three corrections from this session's measurements

The proposed GPU plan is sound in shape. Three items are wrong against what has actually been measured.

### 3a. "Use fixed-point solvers to find the attractor basin" — the target is currently empty

Measured, four independent artifacts agreeing: every native engine schedule converges to **exactly one fixed point with the whole space as its basin**. Bloch contraction coefficients 0.399 / 0.341 — strict contractions, so Banach already guarantees the unique fixed point.

A GPU running Anderson acceleration would find that point instantly, and it would mean nothing. **Renting a GPU to solve a contraction is spending money to confirm a theorem.**

Where the structure actually appeared: a **self-consistent chiral record coupling** — read the mirror axis, let each engine select itself — gives **2 stable fixed points, basins [8,8]**. Controls: each engine alone → 1; anti-consistent rule → 0 fixed points (period-2 chattering). Also measured: the **direct product** of the two engines is still a contraction (1 unit eigenvalue, subdominant 0.1323), so product-coupling creates nothing.

**Correction:** the GPU target is the *hybrid / piecewise* map with record-mediated switching, where the basin count is unknown and worth searching. Not the smooth contraction.

### 3b. "Sample the fuzz with BlackJAX" — ρ-space cannot see the fuzz

Measured: for one stage with 12 Kraus histories, the coherent and decohered history extensions are genuinely different states (distance 0.756; Hartley rank **1 bit vs 4 bits**) — yet **both partial-trace to the identical `ρ_out`, difference exactly 0.0.**

So a sampler exploring density-matrix space is structurally incapable of recovering the `j ≠ k` content. **Correction:** if the fuzz is the history-pair field, the sampler must run on the **history / record space**, not on ρ.

### 3c. PyG for `G → G'` — correct, and it is the named missing piece

The tournament could not run the renesting test for exactly one reason: *"the graph-rewrite machinery does not exist in the repo."* PyG is the right tool for it. This one is an endorsement, not a correction — and it makes renesting the highest-value item in the cloud lane, because it is the only proposed mechanism whose test is currently unrunnable.

---

## 4. Gaps, plainly

| Gap | Status |
|---|---|
| `jax_md` | **not installed** — the doc's best-fit library for toroidal boundaries / jk shells |
| `Reactant.jl` | not installed — would give a same-GPU second engine and satisfy the seal natively |
| PySINDy/PyDMD/pykoopman | installed, **zero sealed arrows** — the residual-decomposition contract is specified but unwired |
| renesting `G → G'` | no machinery; blocks the tournament's renesting test |
| `schedule_tournament_v0` | **REJECTS** — single-engine numeric; needs a second engine or an exemption |
| Catlab, Metatheory | installed **project-local only** (`system_v5/julia_carrier`) — need `--project=` |

---

## 5. The layout in one line

**Julia proves and references → JAX computes → numpy analyses → SMT constrains → ClaimGate seals → Lev decides**, each in its own process, one runtime at a time; PyTorch joins as a rented-GPU lane for mutating topology, and every GPU number is paired with a CPU engine or it does not seal.
