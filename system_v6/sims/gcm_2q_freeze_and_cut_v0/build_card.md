# gcm_2q_freeze_and_cut_v0

BUILD: the 2Q registry freeze plus the first pinned bipartition cut for the GCM availability ladder.

DECLARE: layers 3-12 entropy availability rung | 2Q freeze plus first bipartition cut | 2Q

Authority consumed:

- 2Q carve PASS surface: `system_v6/sims/gcm_constraint_carve_2q_v0/` with 544 survivors, 8 classes, and 16 entangled purification-boundary survivors.
- 1Q freeze: `gcmobj_a40e54e13cec01466c9d675028b3574b` with registry body hash `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`.
- Entropy sweep availability ladder: 1Q marks conditional entropy, mutual information, coherent information, and negativity as requiring a 2Q cut. This packet supplies that cut.
- G.2a builder/audit boundary: builder emits no audit verdict.

Packet obligations:

- 2Q freeze: content-derived `gcm_2q` IDs for 544 survivors, 8 quotient classes, and 6 candidate regions.
- Cross-rung lineage: each frozen 1Q survivor maps to its product-embedding 2Q ID; each 2Q survivor maps back to its partial trace A 1Q survivor ID and, when available, partial trace B 1Q survivor ID.
- First cut: qubit A | qubit B, basis order `|00>, |01>, |10>, |11>`, with `rho_AB`, `rho_A = Tr_B`, and `rho_B = Tr_A` emitted per survivor.
- Entropy families: `S(rho_A)`, `S(rho_B)`, `S(rho_AB)`, `S(A|B)`, `I(A:B)`, `I_c(A>B)`, and negativity over all 544 survivors plus class-level summaries.
- Controls: product survivor entanglement measures vanish exactly; same-marginal scrambled/productized pairing erases entangled signals; partial trace A reproduces the 1Q frozen-ID fiber degeneracy.
- Monogamy row: the 2Q surrogate is computed where definable, but CKW-style monogamy remains OPEN until a 3Q `rho_ABC` object exists.

Substrate checks:

- Positive: `scripts/gcm_substrate_check.py` accepts the packet against the base 1Q freeze and against the new 2Q registry.
- Negative: lineage-free negative variants fail red.

Claim boundary:

- `classification`: `scratch_diagnostic`
- `promotion_allowed`: false
- `formal_admission_allowed`: false
- `carrier-and-pins-relative`: true
- Not THE manifold.
- NO git add/commit.
