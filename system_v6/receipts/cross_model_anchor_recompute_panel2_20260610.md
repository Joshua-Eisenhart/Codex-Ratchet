# Cross-model blind recomputation, panel 2 — the n=5..7 ladder anchors + certificate lemma (2026-06-10)

Same protocol as panel 1 (`cross_model_anchor_recompute_20260610.md`): blind prompts, temperature 0, no repo values shown, pure math. Models: `grok-4.3`, `gemini-3.1-pro-preview`. Advisory only. Raw: `/tmp/grok2_resp.json`, `/tmp/gemini2_resp.json`.

| # | anchor | committed | gemini | grok |
|---|---|---|---|---|
| q1 | W_n single-site entropy, n=5/6/7 | 0.5004024235 / 0.4505612089 / 0.4101163183 | MATCH (identical algebraic form ln n − ((n−1)/n)ln(n−1)) | formula right, **numerics in bits** (0.7219 > ln2 impossible in nats) |
| q2 | symplectic rank lemma + max anticommuting families | rank(K_m)=m even / m−1 odd; families 11/13/15 (=2n+1), explicit witnesses verified | **lemma MATCH + 2n+1 MATCH** | lemma MATCH, but concludes 2n (10/12/14) |
| q3 | Cl(14) chirality split | 64+64 | MATCH | MATCH |
| q4 | PG(3,4) points/lines/degree | 85 / 357 / 100 (fresh-enumerated, 17850 edges) | MATCH | 85 ✓, degree **52** ✗ |
| q5 | Tr_one W_7 weights | (6/7, 1/7) | MATCH | MATCH |
| q6 | S³ disintegration over η: marginal + volume | (machinery lane in flight; targets sin 2η, 2π²) | **sin(2η), 2π²** | **sin(2η), 2π²** |
| q7 | GHZ_8 proper cuts + S(A) | 254 subset-labeled cuts, all ln2 | 254 directed / 127 undirected, ln2 | 127, ln2 |

## Adjudications

- **q2 (the one that matters most):** BOTH models independently confirm the F₂ rank lemma underlying the symplectic-rank certificate now load-bearing at n=5/6/7 (and specced at n=8). Grok's 2n conclusion is wrong by its own lemma: for odd m=2n+1, rank(K_m)=m−1=2n fits the ambient F₂^{2n} — admissibility requires rank ≤ 2n, not m ≤ 2n. Settled constructively by the committed explicit witnesses (11 and 13 Paulis, all pairs recomputed by fresh auditors).
- **q1:** grok computed bits despite the natural-log instruction; its values exceed ln 2, impossible for nats. Repo+gemini agree exactly.
- **q4:** grok's second consecutive line-geometry degree miss (panel 1: 12; now 52). Repo's 100 = 5×20 hand-derived and fresh-enumerated (min=max=100).
- **q6:** both models independently land the disintegration lane's anchor targets (marginal ∝ sin 2η; total 2π²) before that lane reports — a pre-registered cross-check it must now hit.
- **q7:** convention split, not disagreement — 254 subset-labeled vs 127 unordered pairs. ACTION: the n=8 audit card must pin the cut-counting convention explicitly (subset-labeled, A vs complement counted separately).

Panel result: gemini 7/7 (q7 via stated convention); grok 4/7, all three misses adjudicated against grok by hand derivation + committed enumeration/witnesses. The committed anchors and the certificate lemma stand.

Ceiling: advisory cross-check receipt only; `promotion_allowed: false`.
