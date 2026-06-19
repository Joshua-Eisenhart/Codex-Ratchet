# Ratchet Runbook — MASS run (wf wohhmsn1o, 2026-06-15)

**33 agents, 1.1M tokens. 4 contested projections × 2 DISJOINT-model passes × 4 roles + codex2-xhigh ledger.** Full roster: max codex2 (high/xhigh) + gemini-API + grok-4.3 + deepseek/qwen/glm/kimi (OpenRouter). All roles covered — gemini-API + grok rerouted the Minimalist the capped gemini-TUI kept dropping (no PARTIAL rows). `process_ran=true`.

## Cross-pass result (the robustness test — does pass A agree with pass B?)
| Projection | Pass A (gemini-API/deepseek/qwen/codex2-high) | Pass B (grok/glm/kimi/codex2-xhigh) | |
|---|---|---|---|
| **spinor** | REJECT_LIFT | REJECT_LIFT | **AGREE** — quotient + update logs + parity readout, not continuous spinor/Clifford |
| **qca_ordered_update** | REJECT_LIFT | REJECT_LIFT | **AGREE** — ordered local update carries noncommutation, no ρ |
| **entropy_von_neumann** | REJECT_LIFT | REJECT_LIFT | **AGREE** — finite quotient/readout entropy suffices (matches "von-Neumann = installed, no flip") |
| **density_rho** | REJECT_LIFT | ACCEPT_LIFT | **DIVERGE (principled)** |

**3/4 robustly reject the lift across disjoint model sets** — strong, no-single-model-dependence.

## The principled divergence (density_rho) — the real finding
Pass A rejected the lift (mixedness/channel/cut distinctions carried by entropy/readout on the composite-probe quotient). Pass B accepted it — but *only* via a **contextuality / parity-product global-gluing obstruction**. CORRECTED per deep audit w2qgptvqb (do NOT say "ρ forced"): on the contextuality class, a **fixed-cover noncontextual gluing obstruction** holds — z3+cvc5 UNSAT — so a **non-classical carrier is required on that cover**; ρ is one realization, **not uniquely forced**, and context-indexed/refined quotients are **not excluded**. Rejected for ordinary mixedness. The genuine executable content is the UNSAT/SAT flip; the carrier identity is narrower than "ρ".

## Grades (codex2-xhigh ledger, per §13)
- spinor / qca / entropy: **adjudication-grade REJECT**, robust across passes.
- density_rho contextuality class: **evidence-grade ACCEPT** (executable z3/cvc5 flip), rejected outside it.

## next_required_discriminator (codex2-xhigh, verbatim intent)
Sharpen the contextuality control to the **marginal-gluing form**: the SAME context marginals that the weaker carrier admits are each independently satisfiable, but NO global classical joint distribution glues them under the parity-product constraints, while ρ represents them. If that executable flip holds, density_rho is admitted *only* for the contextuality projection class. → Building `finite_contextuality_marginal_gluing_*` as the upgrade.
