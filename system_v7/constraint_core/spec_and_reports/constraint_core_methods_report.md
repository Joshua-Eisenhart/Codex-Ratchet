---
title: Constraint-Core Formalization — Methods, Tools, Thinking, and Suggestions
created: 2026-07-01
updated: 2026-07-01
type: project-methods-report
status: synced-not-canon
claim_ceiling: methods + exploration report. Documents the Claude Science agent toolkit, process, and findings. All model results are scratch_diagnostic; promotion_allowed=false. Suggestions are candidate directions, not admitted canon.
framing: codex-ratchet
provenance: Claude Science session 2026-07-01. Exploratory, ratchet-feeding work — NOT a formal proof process.
---

# Constraint-Core Formalization — Methods, Tools, Thinking & Suggestions

This report documents *how* the formalization work in this session was done — the
tools used (several the owner may not know about), the reasoning process, the
results, and concrete suggestions. Per owner guidance: this is exploratory work
that FEEDS the ratchet; the ratchet itself earns canon. Nothing here is admitted.

## 1. The toolkit (what the agent actually has)

The agent is **Claude Science**, not a plain chat model. Tools used this session:

| Tool | What it does | How it was used here |
|---|---|---|
| **Sandboxed code kernels** | Persistent Python / bash / (R) kernels with numpy, scipy, sympy, matplotlib, jax | All sims: GKSL integration, CPTP/Choi gates, symbolic proofs, basin iteration |
| **`jaxcarrier` env** | A dedicated JAX (x64) environment created on demand | Flux/holonomy transport, closed-form precision audits |
| **GitHub contents API** | Read + write to the wiki repo directly (git/gh CLI are blocked in sandbox) | Cloned Codex-Ratchet + wiki via tarball; pushed all results back to `projects/codex-ratchet/` |
| **Artifact store** | Versioned, durable outputs (figures, specs, JSON, scripts) with lineage tracking | Spec versioned v1→v10; every figure/script/JSON saved |
| **figure-style skill** | Publication-grade figure correctness (font ladder, overlap detection, colour threading) | Every figure rendered + auto-checked for label overlaps |
| **Skill catalog + search** | On-demand domain skills (loaded only when relevant) | Checked for JAX/Julia skills (none exist — catalog is biology-heavy) |
| **Sub-agent delegation** | Can fan out parallel sub-agents with isolated contexts | Available; not needed yet (work was single-threaded and state-coupled) |
| **Host LLM calls** | Can call an LLM programmatically for extraction/classification over many docs | Available for large doc-mining passes |
| **Symbolic math (sympy)** | Exact proofs, not float checks | T01 associator=0, N01 witnesses, Hopf flux ∫F=−4π, b₆=−b₀·b₃ exhaustive |

**Substrate alignment note (owner-flagged):** NumPy carries classical presumptions
(IEEE doubles as completed reals, primitive ==, free broadcasting). The audits here
use **tolerance-based** checks, never ==, so they are methodologically charter-safe;
but the owner's point stands that **Julia** (exact/dispatch-native) and **JAX**
(pure functional) are the aligned kernels. No Julia/JAX/PyTorch skill exists in the
catalog yet — running the *full* proper sim engines would need those installed. If
the goal is to run the owner's actual `system_v5/julia_carrier/*.jl` and
`system_v6/sims/*` engines, that is the next tooling step.

## 2. The process (how each layer was built)

The method throughout: **read the owner's real docs → implement the exact math →
gate it (CPTP/Choi/symbolic) → test the owner's claim → report honestly → sync**.
Key discipline that paid off:

1. **Read source, do not guess.** Every terrain generator, operator, and constant
   was read from repo files (`terrain rosetta strong math.md`,
   `QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH`, `igt-pattern-explicit-math-reference.md`
   §12 scratch Bloch maps), not invented.
2. **Reproduce before extending.** The finite path-integral packet was reproduced
   (8 admissible paths, AB−BA=√2, unconstrained amp to 14 digits) before building on it.
3. **Gate the substrate.** Operators checked CPTP (Choi ≥ 0), unital, purity behavior
   before use. Caught a real bug: Ti/Te implemented as Bloch maps failed Choi; fixed
   to exact Kraus form.
4. **Kill tests.** Basin claims run against the viability-vs-attractor kill test and a
   commuting control (order gap → 2e-17 when noncommutation removed).

## 3. Results this session (all scratch_diagnostic)

- **64 engine schedule** run: order-blind readout collapses (11/64 distinct); N01
  order-sensitive readout lifts to 64/64. Unique processing is a property of the
  ORDER-SENSITIVE observable, not of adding terrains.
- **Nested attractor-basin hierarchy**: 8 distinct terrain basins; kill test splits
  Ne/Ni=attractor vs Se/Si=viability (coincides with Axis-0 polarity); operators
  refine each into sub-basins; commuting control kills the structure (N01-driven).
- **Terrain source-locking**: all 8 terrains now GKSL generators pinned to their
  scratch fixed points (Se was generalized amplitude damping, not dephasing). The
  "agent-chose the dissipators" blocker is closed.
- **Axis-0 diagnosis** (the big one): **8 principled readouts tested, none realizes
  Axis-0** (intuition/sensing {Ne,Ni}|{Se,Si}). Of the eight, **four track Axis-1
  directly** (dissipative/unitary {Se,Ni}|{Ne,Si} — entropy production, response
  dD/dλ, future multiplicity, JK-fuzz bipartite MI); the rest are blind or partial
  (participation ratio: none; von Neumann: Ni only; trajectory activity: 3/4).
  Axis-1 is ORTHOGONAL to Axis-0, which is why the dissipative-tracking functionals
  cannot realize it. Only distinguishability-flow (a fuzz proxy) orders the family
  means correctly (intuition 0.731 > sensing 0.706).

## 4. The key finding: a contradiction and a candidate fix

**Contradiction:** the owner calls Ni "positive entropy," but Ni (Pit/Source)
converges to a PURE state — lowest STATE entropy (0.12). So "entropy" in the Axis-0
definition cannot be state entropy.

**Candidate resolution (falsifiable):** Axis-0 is the Jungian **intuition vs
sensing** axis — Ne/Ni (intuition) = perceiving MANY admissible futures; Se/Si
(sensing) = perceiving ONE actual present. "Positive entropy" then means
**fuzz-field entropy** — entropy over the admissible-FUTURE distribution (the JK
fuzz field), NOT state entropy. Operational form:

```text
Axis-0 polarity = sign of  d/dλ [ H_fuzz(future distribution) ]
                  NOT       d/dλ [ S(state) ]
```

This matches the teeth-map doctrine exactly (Axis-0 is a late object on the
Ω_r/JK → branch-kill → C_G → Ξ → ρ_AB → Φ0 spine) and explains from first
principles why every terrain-local scalar fails.

## 5. Suggestions for making the system work better

1. **Build the JK-fuzz field as a first-class object, not a readout.** The pipeline
   `probe-state → nested layer → F_jk field → Ξ_fuzz cut → ρ_AB → Φ_0` (from
   jk-fuzz-field.md) is the actual Axis-0 seat. Implement F_jk as a finite
   distribution over admissible continuations and measure its entropy — that is the
   test the 8 failed functionals point to.
2. **Split "entropy" into two named quantities everywhere.** STATE entropy S(ρ) and
   FUZZ entropy H(future distribution) are different and the docs conflate them. This
   one rename would resolve the Ni contradiction and de-drift many Axis-0 docs.
3. **Install the real engines.** To run the owner's Julia/JAX/PyTorch sims (not
   agent re-implementations), those runtimes need to be available. The
   re-implementations here agree with saved Julia to ~1e-12, so the port is faithful,
   but the owner's own engines are the ground truth.
4. **Use the kill-test + commuting-control pattern as a standard gate.** It cleanly
   separated real N01 structure from artifacts this session; making it a required
   receipt field would harden basin/engine claims.
5. **Axis-0 as a distinguishability-flow test is worth pursuing.** It is the only
   readout that trended correctly. A sharper version (proper fuzz-entropy over a
   ring-checkerboard support) may be the one that closes it.

## 6. Artifacts (this session)

Spec: `constraint-core-formal-spec-2026-07-01.md` (v10, §7a–7i).
Sims: `engine_64_schedule_sim.py`, `nested_basin_sim.py`, `terrain_sourcelock_axis0_sim.py`.
Figures: `engine_64_schedule.png`, `nested_attractor_basins.png`,
`axis0_sourcelock_diagnosis.png`, `axis0_fuzz_exploration.png`, `sixteen_stage_atlas.png`.
Data: matching JSON result files.

## 7. Honest status

This is exploration, not proof. Everything is `promotion_allowed=false`. The ratchet
— the owner's earning process — is what turns any of this into canon. The value here
is: a closed source-locking blocker, a first-principles diagnosis of the Axis-0
stall, and one falsifiable candidate (fuzz-entropy) for the next rung.
