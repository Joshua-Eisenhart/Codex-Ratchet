# Cross-model blind recomputation, panel 3 — frontier-lane targets, three independent routes, UNANIMOUS (2026-06-10)

Same protocol as panels 1–2 (blind prompts, no repo values, pure math), now with THREE independent routes including the newly-restored codex1 as a no-context deriver and the gemini TUI route (owner-directed):

- `grok-4.3` (x.ai API, temperature 0) — raw `/tmp/blind_panel3/grok_resp.json`
- `auto-gemini-3` (gemini CLI 0.42.0 headless `-p`, routes to the gemini-3 family) — raw `/tmp/blind_panel3/gemini_tui_resp.txt`
- `gpt-5.5 high` (codex1, run in an empty /tmp workdir with NO repo access) — raw `/tmp/blind_panel3/codex1_resp.txt`

Pre-registration purpose: these targets are the expected values for the three frontier lanes IN FLIGHT when the panel ran (`geo_nested_disintegration_v0`, `geo_s10_g2_family_v0`, `geo_s9_octonionic_hopf_stack_v0`). The packets must EARN the values by computation; this panel turns their results into pre-registered hits or real discrepancies. The codex2-authored S10 blind sheet (`/tmp/s10_g2_blind_expectations.md`) is a fourth, more detailed pre-registration for the G2 lane.

| # | target | expected (all three routes AGREE) |
|---|---|---|
| q1 | Der(C)/Der(H)/Der(O) dims | 0 / 3 / 14 |
| q2 | G2: 7⊗7 decomposition | 1 + 7 + 14 + 27 (Sym² = 1+27, Λ² = 7+14) |
| q3 | dims G2 ⊂ Spin(7) ⊂ Spin(8); \|Out(Spin(8))\| | 14 / 21 / 28; 6 (triality S₃) |
| q4 | \|PSL(2,7)\|; \|Aut(Fano)\|; octonion table count | 168; 168; 480 |
| q5 | octonionic Hopf | S¹⁵ → S⁸, fiber S⁷, fiber NOT a Lie group, Adams: last fibration |
| q6a | torus stage-2 marginal | uniform on χ (dχ/2π) |
| q6b | two-leaf union conditional weights | w_i = sin(2η_i) / (sin(2η₁)+sin(2η₂)) |
| q7 | G2 stabilizer of an imaginary unit | SU(3), dim 8, coset dim 6 (S⁶) |
| q8 | 3-tangle τ(GHZ₃) / τ(W₃) | 1 / 0 |

Panel result: **3/3 routes unanimous on all 8 targets**, zero adjudications needed. Notable: grok, which missed line-geometry/odd-rank items on panels 1–2, is clean here; the union-weight formula (q6b) — the exact load-bearing rule of the nested-disintegration packet — is independently derived identically by all three routes.

Ceiling: advisory pre-registration receipt only; the in-flight packets must earn these values by their own computations; `promotion_allowed: false`.
