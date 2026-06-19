# G2 Blind Math Panel (grok-4.3 + gemini, 2026-06-12)

```yaml
receipt_kind: blind_panel
routes: [grok-4.3 temp-0, gemini TUI]
protocol: pure-math questions, no project context; pre-registered vs the in-flight G2 attach audit
raw: /tmp/g2_grok.json, /tmp/g2_gemini.txt
```

## Convergent confirmations (both routes, independent)

- phi = e123+e145+e167+e246-e257-e347-e356 is the standard positive G2 3-form; the cross
  product g(x×y,z)=phi(x,y,z) gives e1×e2=e3, e1×e4=e5, e1×e6=e7, e2×e4=e6, e2×e5=-e7,
  e3×e4=-e7, e3×e5=-e6 (signs from the 7 monomials).
- dim G2 = 14 = dim Der(O); dim Der(H) = 3 (= so(3)). [the packet's corrupt control = 3 is
  the quaternion Der — a REAL discriminator, confirmed]
- G2/SU(3) = S^6 (14-8=6); Spin(7)/G2 = S^7 (dim Spin(7)=21, 21-14=7); F4 = Aut(J3(O)),
  dim F4 = 52, dim J3(O) = 27 (3 real + 3 octonionic off-diagonal = 3+24). ALL confirmed.

## THE LOAD-BEARING ANSWER (gemini Q2 — the canonicity criterion)

A W ⊂ su(8) (dim 63) + a pinned basis identification W ≅ R^7 + copied phi is
**CONVENTION-DEPENDENT, NOT canonical**, UNLESS: W is identified as a specific
G2-IRREDUCIBLE 7-subspace under a specific embedding g2 ↪ su(8) (su(8) decomposes under G2;
the 7 is one irreducible piece), with the basis pinned to the OCTONION STRUCTURE CONSTANTS
from the G2 root system. grok: phi is unique up to GL(7,R) (one open positive orbit), so the
CHOICE of W and the identification carry all the content.

## Consequence for the G2 attach (gcm_g2_licensing_attach_v0)

The packet's self-flag natural_W_A_from_owner_sources=FALSE / met_by_explicit_pinned_
convention_only is INDEPENDENTLY VINDICATED as the correct status. The blind panel supplies
the exact upgrade path the attach must meet to ever escape convention-only: W_A must be a
g2-irreducible 7 from a real g2↪su(8) embedding w/ octonion-structure-constant basis pinning
— NOT an arbitrary 6-single-qubit + XXX span. Until then, the layer is a standard-G2-test
fixture on a pinned subspace, not a manifold-canonical G2 attachment.
