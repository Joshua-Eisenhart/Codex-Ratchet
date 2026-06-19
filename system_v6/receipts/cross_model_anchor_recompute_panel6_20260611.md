# Cross-model blind recomputation, panel 6 — entropy-ledger + dynamic-manifold rigidity targets (2026-06-11)

Protocol as prior panels (blind, temperature 0, no repo values). Routes: `grok-4.3` (API), `auto-gemini-3` (TUI), `gpt-5.5 medium` (codex1, empty workdir). Raw: `/tmp/panel6/*`. Pre-registers the targets of two lanes IN FLIGHT (`manifold_entropy_ledger_v0`, `mct_dynamic_deformation_v0`).

| # | target | expected | routes |
|---|---|---|---|
| q1 | h[sin(2η) marginal on [0,π/2]] (nats) | **1 − ln 2 ≈ 0.30685** | gemini + codex1 agree; grok gave (π/2)ln2 — ADJUDICATED AGAINST grok by hand: grok conflated ∫₀^π ln sin x dx = −π ln 2 (unweighted) with the sin-WEIGHTED integral; directly, ∫₀^{π/2} sin x ln sin x dx = ln 2 − 1 ⇒ h = 1 − ln 2 |
| q2 | h[uniform torus chart 2π×π] | ln(2π²) | 3/3 |
| q3 | free order-N quotient entropy change (uniform) | exactly −ln N | 3/3 |
| q4 | disintegration chain rule | h(X,Y) = h(X) + E_x[h(Y\|X=x)], EXACT equality for regular disintegrations | 3/3 |
| q5 | monotonicity rigidity | pure constraint ADDITION can never strictly grow the admissible set; growth requires release/relax/coarsen | 3/3 |
| q6 | projection/quotient flows | induced partitions monotone; erased distinctions unrecoverable downstream | 3/3 |

q5/q6 pre-register the dynamic-manifold lane's two lead rigidity rows; q1–q4 pre-register the entropy ledger's exact anchors. Grok's q1 miss is its fifth adjudicated divergence across six panels (line-geometry ×2, bits-vs-nats, odd-rank, identity-conflation) — a consistent pattern: grok errs on weighted/counted variants of classic identities; gemini TUI and codex1-blind remain clean.

Ceiling: advisory pre-registration; the in-flight packets must earn the values by computation; `promotion_allowed: false`.
