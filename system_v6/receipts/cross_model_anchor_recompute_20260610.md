# Cross-model blind recomputation of committed anchors — 2026-06-10

Purpose: independent same-sims-different-models verification (owner directive) of eight committed anchor values. Both models were prompted BLIND (no repo values in the prompt, temperature 0, pure math, no web). Raw responses: `/tmp/grok_xmodel_resp.json`, `/tmp/gemini_xmodel_resp.json` (volatile; JSON answers reproduced below).

Models: `grok-4.3` (x.ai API), `gemini-3.1-pro-preview` (Google API). Advisory cross-checks, not authorities; the committed values remain grounded in their own packets' constructions + fresh audits.

| # | anchor | committed value (packet) | gemini | grok |
|---|---|---|---|---|
| q1 | W_4 single-site entropy | −(3/4)ln(3/4)−(1/4)ln(1/4) ≈ 0.5623351446 (n=4 rung) | MATCH (as 2ln2−(3/4)ln3, algebraically identical) | MATCH |
| q2 | GHZ_4 S(A), all bipartitions | ln 2 (n=4 rung) | MATCH | MATCH |
| q3 | Tr_one GHZ_4 | classical mixture (|000⟩⟨000|+|111⟩⟨111|)/2; GHZ does NOT nest (n=4 rung) | MATCH | MATCH |
| q4 | Tr_one W_4 | (3/4) W_3 + (1/4)|000⟩⟨000| (n=4 rung) | MATCH | MATCH |
| q5 | max anticommuting 4Q Pauli family; general | 9; 2n+1 (n=4 rung, stored max-clique certificate) | MATCH | MATCH |
| q6 | Cl(8) chirality split | 8+8 (n=4 rung) | MATCH | MATCH |
| q7 | PG(3,3) points/lines/line-graph degree | 40 / 130 / 48 (q=3 packet, auditor hand-recomputed) | MATCH | **DEVIATION: degree 12** |
| q8 | PG(3,4) points/lines/quotient ratio | 85 / 357 / 3:1 (q=4 build card targets; 85 and 3:1 derived) | MATCH | MATCH (85, ratio 3; lines not asked back) |

## Adjudication of the single deviation (q7, grok)

Lines meeting a given line ℓ in PG(3,3): ℓ has q+1 = 4 points; through each point there are q²+q+1 = 13 lines, i.e. 12 besides ℓ; two distinct lines share at most one point, so the sets are disjoint: 4 × 12 = **48**. Grok reported the per-point count (12) without summing over the 4 points of ℓ. The committed 48 is independently forced by the audited edge count: 130 × 48 / 2 = 3120 edges (grok's 12 would give 780, contradicting the committed graph). Deviation adjudicated AGAINST grok by hand derivation; no repo defect.

Panel result: gemini 8/8 exact; grok 7/8 with the single miss adjudicated. The committed anchors stand.

Ceiling: advisory cross-check receipt only — no promotion, no admission; `promotion_allowed: false`.
