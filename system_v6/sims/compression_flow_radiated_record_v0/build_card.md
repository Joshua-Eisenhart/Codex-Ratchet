# BUILD CARD: compression_flow_radiated_record_v0 — first finite compression-flow / radiated-record packet (weld 1)

One object, one claim, one card. CLAIM UNDER TEST (CANDIDATE MATH — the conservation/reconstruction laws are a candidate formalization per system_v6/receipts/shell_flow_radiated_information_mine_20260610.md §B-C: doctrine-level sources exist, exact math NOT on file; this sim is the FIRST receipt for that candidate math and does not promote it to standing doctrine):

On a finite carrier, a step process where the live admissible set contracts inward while excluded content is emitted to an append-only outward record satisfies, measurably:
  (a) conservation: |P_t| = |P_{t+1}| + |Delta R_t| at every step (cardinality ledger), plus a named entropy ledger;
  (b) append-only record: no emitted row is ever overwritten or deleted;
  (c) exact reconstruction: P_0 is recovered exactly from (P_T, full record) — and UNIQUELY (proof);
  (d) the erasure variant (classical boundary baseline) breaks (a) internally and (c) entirely;
  (e) the record-granularity comparison: a raw-row record reconstructs the raw set; a quotient-class record reconstructs ONLY the quotient — the difference IS the killed-information ledger, measured.

Owner sentence this operationalizes (2026-06-09, cited via the mine receipt): future possibilities on an inward-moving shell; past radiated outward on the same shell family; information radiated, not destroyed.

Ceiling (hard): classification="scratch_diagnostic", promotion_allowed=false, formal_admission_allowed=false. Status language: "a first finite compression-flow/radiated-record packet" — NOT "the manifold algorithm proven", NOT a QIT-separation claim (that is the later dual-stack rebuild; entropy objects here may be classical Shannon over finite sets plus density-derived rows — name every entropy object, never an unnamed H). No axis/bridge/physics claim.

## Read first (binding; cite into PIN provenance)
1. system_v6/README.md (rules, ladder)
2. system_v6/receipts/shell_flow_radiated_information_mine_20260610.md — the source map; candidate-math labels come from its §B/§C verbatim
3. system_v6/sims/mct_dynamic_admissibility_packet_v0/ — build_card.md + results: the COMMITTED carrier. REUSE its pinned support (chart, grid, PIN lineage). Do NOT rebuild the carrier; import its pinned chart/grid constants and cite its pin_block_sha256 in your PIN as carrier_lineage.
4. wiki/concepts/field-wide-compression-probe-contract.md:123-232 — whole-field dependency + compression-vs-expansion + readout contract (support_size, possibility_mass, named ambiguity)
5. system_v6/receipts/mct_reconciled_spec_20260609.md — killed-information ledger discipline (standing)

## PIN block (frozen; identical across legs; per-leg PIN_SPEC convention as in the mct packet)
- carrier: the 384-sample table psi_s(phi_i,chi_j;eta_k) from mct_dynamic_admissibility_packet_v0 (same chart formula, same grid, carrier_lineage = its pin_block_sha256). Shell coordinate eta_k = the flow coordinate; shells ordered outer->inner: 3pi/8 -> pi/4 -> pi/8 (b0: -1 -> 0 -> +1).
- flow: P_0 = all 384 samples at the outer stage. Steps t=0,1,2: apply the pinned exclusion predicate c_t to the live set; survivors advance one shell inward; excluded samples are emitted as Delta R_t, each emitted row tagged (step t, full canonical probe row or class id per record mode). Pin THREE exclusion predicates as named computed probe-row predicates sourced from the carrier packet's probe families (e.g. a density-bin predicate, a loop-class predicate, a phase-bin predicate) — exact choices pinned by you in PIN_SPEC with status PINNED-CHOICE and the source quoted; predicates must each exclude a nonempty proper subset (no trivial steps).
- record modes (BOTH run, this is the load-bearing comparison): record_mode=raw_row (emitted rows carry full canonical rows) vs record_mode=quotient_class (emitted rows carry only quotient-class ids under the carrier's density-only probe family). 
- ledgers: cardinality ledger per step; entropy ledger with NAMED objects only (H_live = class-distribution entropy of live set under density probes, H_record = entropy of record composition, both base e; bits-erased ledger for the erasure variant reported in nats with ln2 factor explicit).
- variants: (1) radiative (the claim); (2) erasure boundary baseline (Szilard-style: record register reset each step — content destroyed; classical boundary engine, NOT a "failing control": its books must balance ONLY via an explicit environment charge = the boundary certificate); (3) lossy-record (counts only, no rows).

## Build gates
G1. Flow actually runs on the geometric carrier rows (the 384 spinor-derived canonical rows), not on abstract indices. Per-step membership tables emitted.
G2. Conservation: |P_t| = |P_{t+1}| + |Delta R_t| exact at every step in every leg; any injected-violation control (deliberately drop one row mid-flight) must be CAUGHT by the ledger (nonzero defect reported).
G3. Append-only: record hash chain emitted (each step's record state hash includes the previous hash); demonstrate immutability by recomputation.
G4. Reconstruction, raw mode: reconstruct P_0 from (P_2, full raw record); compare as canonical-row set equality; mismatch count must be 0. Quotient mode: raw reconstruction must FAIL with a measured mismatch count, while quotient-level reconstruction succeeds — report both numbers (this is the killed-information ledger, measured).
G5. LOAD-BEARING PROOF (z3 AND cvc5, separately): from the COMPUTED record + final state, derive UNIQUENESS — assert a candidate initial set P_0' consistent with (P_2, record) and P_0' != P_0: must be UNSAT in raw mode. ERASED control: drop a pinned fraction of record rows -> SAT (multiple consistent P_0'), with a model exhibited. Both solver verdicts recorded separately; hardcoded literals = build failure.
G6. Erasure baseline: reconstruction fails (mismatch > 0 measured); internal ledger does not balance without the explicit environment charge; the charge equals ln2 x bits erased (report the arithmetic). Radiative variant: zero internal erasure charge; ledger balances through the record.
G7. Order matters (N01-aligned): reconstruction with shuffled step tags must fail or change the result where the pinned predicates overlap; report.
G8. By-construction fence: the pre-audit will attack triviality. Your defense receipts: the uniqueness PROOF (G5), the quotient-mode measured failure (G4), the erasure/lossy variants (G6), and the injected-violation catch (G2) — each must be a computed value that COULD have come out the other way.

## Controls that must fire
erasure variant, lossy-record variant, record-shuffle, injected conservation violation, label shuffle (relabeling changes no ledger/reconstruction verdict), trivial-predicate control (a predicate excluding nothing must be flagged, not silently passed).

## Engines (three-engine claim-bearing mode; identical PIN)
Julia = canon (sets/ledgers/proof via Z3.jl; QuantumOptics only where density rows are recomputed). JAX = batched sweep (all steps, both record modes, variants; z3+cvc5 python proofs). PyTorch = the record/flow graph lane (append-only log as a DAG; torch_geometric or adjacency machinery; flow connectivity readouts). NumPy = control-lane only. Like-for-like shared scalars; evidence ladder Julia -> exact -> solvers -> cross-engine smoke.

## Files to create (exactly; one folder, atomic)
system_v6/sims/compression_flow_radiated_record_v0/
  compression_flow_radiated_record_v0_julia.jl / _jax.py / _pytorch.py / _envelope.py
  build_card.md (this card verbatim)
  results/*.json
No audit_verdict.md (fresh audit writes it). No edits to any existing file.

## Acceptance (re-run mechanically by overseer)
All legs exit 0 fresh; envelope passes scripts/validate_three_engine_sim_result.py --require-pytorch; PIN identical across legs with carrier_lineage cited; every gate G1-G8 has named computed receipt fields; every control fired with recorded flip/fail; candidate-math labels present on the conservation/reconstruction claims; ceiling fields exact.
