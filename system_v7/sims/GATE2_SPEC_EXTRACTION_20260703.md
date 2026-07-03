- finite state set as exact data, so quotient is computed, not asserted [contract:135-139]
- compatibility law: `rho_A in X_A^max` and `Tr_{A\B}(rho_A) ~_B rho_B` for every nonempty `A` and every `B subset A` [contract:245-248]
- extension fibers `F_n(rho) = { rho' : Tr(rho') ~ rho }` enumerated as data with fiber sizes [contract:249]
- induced geometry recomputed on survivors, never relabeled [contract:247-251]

6. Acceptance Gates

Gate 2 accepts only if:

- Gate 1 re-audit is clear.
- All cuts are enumerated.
- All per-cut marginals are computed by partial trace, not label echo [contract:252-256].
- All Schmidt strata per cut are recorded.
- All licensed entropy/readout families are declared with exact type and enabling nesting row [contract:307-316].
- Probe epoch is explicit; cross-epoch reuse re-projects [FORMAL_SPEC.md:58].
- Negative roster fires where applicable, especially product negativity zero, perturbed marginal fails, alternate probe family, lineage removed fails, entropy/negativity direction flips across the cut lattice, and per-rung ladder negatives [contract:162-205].
- QIT floor is respected: 3Q is required for multi-qubit claim; 1Q/2Q do not prove it [contract:206-213].
- Status label stays literal: `exists < runs < passes local rerun < canonical by process` [contract:289-293].

7. Negative Controls

Required minimum controls:

- product/separable control has zero entanglement negativity; entangled survivor has nonzero [contract:170-171]
- deliberately perturbed marginal violates compatibility law [contract:172-173]
- alternate probe family changes quotient/admissibility where expected [contract:176-178]
- lineage removed makes nesting/ancestry fail [contract:179-180]
- entangled-vs-separable or W-vs-GHZ controls diverge across cut lattice [contract:191-193]
- known-inconsistent parent/marginal pair rejected by computed partial trace while label echo would pass [contract:254-256]
- coarse epoch representative-independence/lift control must not be treated as full quotient proof; existing Xi_ref coarse test failed and was demoted [FORMAL_SPEC.md:63-78]

8. Open Choices

- Entropy/geometry order: locked flux-first vs parallel entropy/geometry remains owner-tunable [contract:90-93].
- Which entropy/readout families Gate 2 licenses first: `S_A`, `S_AB`, `I_AB`, conditional, coherent information; must be declared per layer, not “entropy” generically [contract:307-316].
- Coarse epoch role: control-only vs admitted alternate epoch after its own quotient/lift gates.
- Representative policy inside quotient classes: full-Pauli singleton classes make this trivial locally, but coarse epochs require representative-independence tests [FORMAL_SPEC.md:63-78].
- Whether Gate 2 stops at L8 cut lattice or bundles L9/L10 in the same packet. If bundled, L9 Schmidt strata and L10 entropy inherit full enumeration and nesting-license obligations [contract:54-56,307-316].



## Referee addendum (kimi, verified, 2026-07-03) — fold into the build prompt

1. CUT-COUNT AMBIGUITY TO PIN FIRST: unordered bipartitions 2^(n-1)-1 = 3 at
   n=3 (contract L8 wording) vs non-trivial party subsets 2^n-2 = 6 (ordered).
   Builder must resolve from contract verbatim and assert the chosen formula
   against the enumeration. Cuts are PARTY-indexed; the quotient acts on
   states, never on cut labels.
2. LABEL-ECHO SEAM: cross-epoch artifact reuse — "re-projects" must be
   VERIFIED, not procedural: recompute marginals fresh per epoch and compare
   against any cached value; mismatch = reject. No representative-lookup
   substituting for actual partial trace.
3. CONTINUITY TRAP: "all Schmidt strata with representatives" is finite ONLY
   on the ratcheted finite quotient — never on local-unitary equivalence
   (continuous). Stay on the admitted finite class roster.
