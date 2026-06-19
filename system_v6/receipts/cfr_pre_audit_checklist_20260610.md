# Adversarial pre-audit checklist: `compression_flow_radiated_record_v0`

This checklist is for a fresh auditor after the build exists. It is written before outcomes are known. Do not accept builder prose, self-checks, or validator success as evidence. Open the emitted source and result JSONs, recompute the named rows, and record only audit findings in the later audit verdict. This file contains no verdicts.

Central attack surface: by-construction triviality. A raw record that stores every emitted row can reconstruct exactly by storage alone. Raw-mode exact reconstruction earns no claim unless the packet also shows load-bearing uniqueness proof, measured quotient-mode information loss, and erasure/lossy variants failing with numbers.

Read first:

- `/tmp/cfr_build_card_20260610.md`
- `system_v6/README.md`
- `system_v6/receipts/shell_flow_radiated_information_mine_20260610.md`
- `system_v6/receipts/mct_reconciled_spec_20260609.md`
- `system_v6/sims/mct_dynamic_admissibility_packet_v0/build_card.md`
- `system_v6/receipts/mct_pre_audit_checklist_20260610.md`
- `/Users/joshuaeisenhart/wiki/concepts/field-wide-compression-probe-contract.md:123-232,288-305`
- any `SOURCE*` or `source*` files inside `system_v6/sims/compression_flow_radiated_record_v0/`, if present.

Expected build paths:

- `system_v6/sims/compression_flow_radiated_record_v0/compression_flow_radiated_record_v0_julia.jl`
- `system_v6/sims/compression_flow_radiated_record_v0/compression_flow_radiated_record_v0_jax.py`
- `system_v6/sims/compression_flow_radiated_record_v0/compression_flow_radiated_record_v0_pytorch.py`
- `system_v6/sims/compression_flow_radiated_record_v0/compression_flow_radiated_record_v0_envelope.py`
- `system_v6/sims/compression_flow_radiated_record_v0/build_card.md`
- `system_v6/sims/compression_flow_radiated_record_v0/results/*.json`

## 1. Build-card copy, ceiling, and candidate-math fence

Open:

- emitted `build_card.md`;
- all leg source files;
- all per-leg and envelope result JSONs;
- generated report/status fields, if any;
- `system_v6/receipts/shell_flow_radiated_information_mine_20260610.md` sections B and C.

Recompute:

- Compare emitted `build_card.md` byte-for-byte or semantically against `/tmp/cfr_build_card_20260610.md`; any deliberate build-time disposition must be separately named and fenced.
- Check exact ceiling fields everywhere: `classification == "scratch_diagnostic"`, `promotion_allowed == false`, `formal_admission_allowed == false`.
- Search result keys and strings for promoted language: `canonical`, `admitted`, `formal`, `standing doctrine`, `manifold algorithm proven`, `QIT separation`, `axis`, `bridge`, `physics`, unless the field explicitly negates or fences it.
- Check every conservation or reconstruction law field carries a candidate-formalization label that cites the mine receipt sections B/C and says the exact math is not standing doctrine.

Fail condition:

- The build card is missing or materially changed without a disposition; any ceiling field is absent or stronger than pinned; conservation/reconstruction is phrased as established doctrine; any QIT/axis/bridge/physics promotion appears; or validator success is used as admission.

## 2. Carrier lineage and 384-row support reuse

Open:

- CFR source files and PIN/PIN_SPEC definitions;
- CFR per-leg and envelope result JSONs;
- `system_v6/sims/mct_dynamic_admissibility_packet_v0/build_card.md`;
- MCT source files defining `PIN_BLOCK_CANONICAL`, `PIN_BLOCK_SHA256`, chart/grid, and support/probe rows.

Recompute:

- Recompute the MCT base `pin_block_sha256` from the committed MCT `PIN_BLOCK_CANONICAL` source string; compare it to every CFR `carrier_lineage` field.
- Count the pinned carrier by hand: `2 sheets * 3 eta shells * 8 phi values * 8 chi values = 384`.
- Pick one CFR carrier row and recompute `psi_s(phi_i, chi_j; eta_k) = (exp(i(phi_i+chi_j))*cos(eta_k), exp(i(phi_i-chi_j))*sin(eta_k))`; check unit norm and `rho = psi psi^dagger`.
- Check that CFR row IDs, chart/grid constants, density/bin/probe fields, and support hash are imported from or recomputed to match the committed MCT carrier, not rebuilt from a new ad-hoc table.

Fail condition:

- `carrier_lineage` is absent or does not match the committed MCT pin hash; support size is not 384; chart/grid constants differ silently; row IDs are incompatible; probe rows are invented from indices; or a fresh carrier table is used without being tied back to the MCT pin.

## 3. Exclusion predicates and predicate-gaming controls

Open:

- PIN/PIN_SPEC predicate definitions;
- source code implementing each `c_t`;
- per-step membership tables;
- result fields for trivial-predicate, record-shuffle, label-shuffle, and order controls;
- blind-lane expected-values card or receipt, if present.

Recompute:

- For each step, inspect the predicate source: it must be a computed probe-row predicate from the committed carrier family, not a row-id, step-id, hardcoded count, or post-hoc class list.
- Recompute the predicate truth values over the live set and count excluded/survivor rows.
- Check each predicate excludes a nonempty proper subset of the then-live set.
- Check the predicates are not disjoint in a way that voids order sensitivity: there must be an explicit overlap/dependency or a measured statement that the order test is not claimed.
- Check no one-step exhaustion makes later steps vacuous.
- Run the trivial-predicate control: an empty exclusion predicate must be flagged as invalid, not silently accepted.

Fail condition:

- Any predicate excludes zero rows or all rows without a failed-control label; predicates are pinned to make reconstruction/order trivial; the order test is void because predicates are disjoint or later live sets are empty; a predicate is defined by labels instead of computed rows; or the blind lane flagged a risk that is not answered by a measured control.

## 4. Full cardinality ledger hand recomputation

Open:

- per-step live-set tables `P_t`;
- per-step survivor tables `P_{t+1}`;
- emitted-record tables `Delta R_t`;
- cardinality ledger fields;
- injected-violation control fields.

Recompute:

- First reconcile the emitted time convention. The card mentions shells `3pi/8 -> pi/4 -> pi/8` and reconstruction from `P_2`; if the implementation uses `t=0,1,2`, identify the actual final `P_T` and ensure the convention is explicit.
- For every emitted step, compute by hand or with a small independent script: `|P_t|`, `|P_{t+1}|`, `|Delta R_t|`, and `|P_t| - |P_{t+1}| - |Delta R_t|`.
- Check row-set partitioning, not just counts: `P_{t+1}` and `Delta R_t` must be disjoint subsets of `P_t`, and their union must equal `P_t`.
- Sum the full ledger: `|P_0|` must equal `|P_T| + sum_t |Delta R_t|` for raw/radiative mode.
- Inspect injected violation: deliberately dropping one row mid-flight must report a nonzero defect and must flip a pass field or control status.

Fail condition:

- Any step has nonzero cardinality defect; disjointness/union is not checked as row sets; the step convention is ambiguous; the full ledger does not close; the injected-violation control is absent, does not fire, or does not affect the gate status.

## 5. One raw reconstruction by hand

Open:

- raw-mode final live set `P_T`;
- raw-mode full record;
- canonical row table;
- reconstruction source code;
- reconstruction result fields.

Recompute:

- Pick one emitted final survivor row and one emitted record row from different steps; verify their canonical row IDs and row payloads match the carrier table.
- Reconstruct the initial set as a row-set union: `P_T union Delta R_0 union Delta R_1 ...`.
- Check exact set equality against `P_0` by canonical row ID and by at least one full canonical row payload.
- Check duplicates: if a row appears twice in the record or both final and record, the reconstruction must fail or ledger the duplicate explicitly.

Fail condition:

- Raw reconstruction uses stored `P_0` or result JSON echo instead of rebuilding from `(P_T, full record)`; row payloads are not canonical carrier rows; duplicate/missing rows are ignored; mismatch count is absent; or exact success is treated as sufficient proof without the separate anti-triviality defenses below.

## 6. Triviality defense A: SMT uniqueness on computed values

Open:

- z3 and cvc5 constraint-building source;
- solver input dumps if emitted;
- computed record/final-state tables used by the solver;
- raw-mode uniqueness proof fields;
- dropped-record/erased-row control fields and exhibited model.

Recompute:

- Trace every solver variable and assertion back to computed row values from the emitted record/final state. The solver may encode row IDs only if it also ties them to computed canonical-row payloads or hashes.
- Independently state the raw uniqueness query: find a candidate `P_0'` consistent with `(P_T, full raw record)` and `P_0' != P_0`. Expected polarity for the complete raw record is `UNSAT`.
- Check z3 and cvc5 both solve this query separately. Same math obligation is fine; byte-identical pre-rendered SMT blobs or copied verdict strings are not.
- For the dropped-record control, remove the pinned fraction/rows from the record and solve the alternate query. Expected polarity is `SAT`.
- Inspect the SAT model: it must exhibit an alternative initial set or row assignment that differs from `P_0` and remains consistent with the erased record.

Fail condition:

- SMT encodes hardcoded row literals or stored verdicts; either solver is absent; z3/cvc5 share one encoding artifact without independent construction; full-record uniqueness is not `UNSAT`; dropped-record control is missing, non-flipping, or lacks an exhibited alternative model; or solver results do not feed the gate.

## 7. Triviality defense B: quotient-mode killed-information ledger

Open:

- `record_mode=quotient_class` source and result fields;
- quotient-class definition under the density-only probe family;
- raw reconstruction mismatch fields;
- quotient-level reconstruction fields;
- killed-information ledger.

Recompute:

- Pick one quotient class with more than one raw carrier row, using the emitted class table.
- Count raw candidates represented by that class and compute the number of raw distinctions killed by quotienting.
- Attempt raw reconstruction from `(P_T, quotient-class record)` and count the raw symmetric-difference or missing/ambiguous rows exactly as defined by the packet.
- Reconstruct at quotient level and check class-set equality.
- Compare the measured raw mismatch/ambiguity ledger against the class sizes; the mismatch must be arithmetic, not prose.

Fail condition:

- Quotient mode stores enough raw data to reconstruct the raw set exactly; raw mismatch is zero or absent; quotient-level reconstruction is not separately checked; killed information is asserted but not computed from class sizes; or quotient classes are labels not recomputable from the density-only probe family.

## 8. Triviality defense C: erasure and lossy variants fail with numbers

Open:

- erasure boundary-baseline source and result fields;
- lossy-record/counts-only variant source and result fields;
- reconstruction mismatch fields for both variants;
- ledger fields for bits erased, nats, and environment charge.

Recompute:

- For erasure mode, identify exactly which rows or record registers are reset at each step.
- Count erased bits or log-cardinality loss under the implementation's stated base; convert to nats with the explicit `ln(2)` factor where bits are used.
- Recompute the environment charge: `environment_charge_nats = bits_erased * ln(2)` or the explicitly stated equivalent.
- Attempt reconstruction from the erasure and lossy variants and recompute the mismatch counts.
- Check radiative mode has zero internal erasure charge, while erasure mode balances only with explicit environment charge.

Fail condition:

- Erasure or lossy variants reconstruct exactly without explanation; mismatch numbers are absent; `ln(2)` conversion is missing or arithmetically wrong; erasure is called a failing control rather than a classical boundary baseline; or the books are declared balanced without explicit environment charge.

## 9. Decorative SMT and solver-proof integrity

Open:

- all z3/cvc5 imports and constraint builders;
- solver input dumps, if emitted;
- proof/receipt fields in every leg and envelope;
- source-to-result gate mapping.

Recompute:

- Search source for large handwritten row literal tables, manually enumerated satisfying sets, or solver verdict constants.
- For one proof obligation, trace the computation path: carrier row -> flow/record value -> solver assertion -> solver verdict -> result field.
- Compare z3 and cvc5 construction paths: they must be separate calls or separately constructed formulas, not one solver's verdict echoed under two names.
- Confirm both full-record `UNSAT` and erased/dropped-record `SAT` are represented in each claimed solver lane.

Fail condition:

- Solver proof is a decorative wrapper around hardcoded row values; no erased-control model is exhibited; z3 and cvc5 share one precomputed encoding or verdict; or proof fields are not gate-bearing.

## 10. Entropy and ledger-theater check

Open:

- entropy ledger source;
- named entropy result fields;
- cardinality, record-composition, erasure, and environment-charge ledgers;
- injected-violation control source/results.

Recompute:

- For one step, compute `H_live` from the emitted live-set class distribution under the named density probes, base `e`.
- For the record so far, compute `H_record` from the emitted record-composition distribution, base `e`.
- Verify no scalar is called entropy unless it names object, partition, distribution, base, and control.
- Recompute the conservation identity from the row tables; do not accept a stored identity string.
- Check injected violation changes the conservation defect and trips the control.
- For erasure, recompute `bits_erased`, `bits_erased * ln(2)`, and the environment charge field.

Fail condition:

- Conservation is asserted but not computed; entropy is unnamed; `H_live`/`H_record` cannot be recomputed from emitted distributions; injected violation is absent or non-firing; environment charge is not tied arithmetically to erased bits with the `ln(2)` factor.

## 11. Append-only record and hash-chain immutability

Open:

- append-only record source code;
- per-step record states;
- hash-chain fields;
- immutability/recomputation demonstration fields;
- any mutation/overwrite controls.

Recompute:

- Starting from the initial record hash, recompute every step hash. Each step hash must include the previous hash and the new emitted rows in a canonical order.
- Check that previous record entries are not overwritten, re-sorted in a way that hides deletion, or regenerated from final state.
- Attempt the documented immutability check: delete, reorder, or mutate one prior record entry and recompute the chain; the final hash must change or the control must fail.
- Check the hash chain is independent of result JSON storage order unless canonicalization is explicitly defined.

Fail condition:

- Hashes are stored but not recomputable; each hash does not include the previous hash; the record can be rewritten while preserving final claimed hash; immutability is asserted only in prose; or append-only status is not gate-bearing.

## 12. Record-shuffle and order-sensitivity

Open:

- step-tagged record rows;
- reconstruction code;
- record-shuffle and label-shuffle controls;
- predicate-overlap/dependency evidence from check 3.

Recompute:

- Shuffle step tags while preserving the multiset of record rows and rerun reconstruction/order-sensitive checks.
- Separately relabel row IDs with a bijection that preserves carrier row payloads and recompute invariant ledgers.
- Confirm record-shuffle fails or changes the intended result where predicates overlap, while label-shuffle preserves row-set/cardinality/reconstruction verdicts.

Fail condition:

- Step tags are ignored while order-sensitive language is claimed; record shuffle has no effect and no explicit "order not claimed" fence; label shuffle changes invariant results; or order correctness is collapsed into content correctness.

## 13. Boundary-engine language and erasure-baseline framing

Open:

- erasure variant source/results;
- boundary certificate fields;
- generated report strings;
- source/provenance fields for Szilard/Landauer-style language, if used.

Recompute:

- Check the erasure variant is framed as `classical boundary baseline` or equivalent, not as a "failing control."
- Verify the boundary certificate states internal imbalance and explicit environment charge, with arithmetic from erased bits to nats.
- Search all outputs for QIT-separation or quantum-information-separation language.

Fail condition:

- The erasure baseline is described as a mere failing control; the boundary certificate is absent; books are balanced without environment charge; or any QIT-separation claim appears. QIT separation is fenced to the later dual-stack rebuild.

## 14. Cross-leg independence and parity-by-copy check

Open:

- all three leg source files;
- envelope source;
- all per-leg and envelope result JSONs;
- `engines.*` metadata;
- `reads_peer_result` fields;
- `TOOL_MANIFEST` and `TOOL_INTEGRATION_DEPTH` fields.

Recompute:

- Verify every leg declares and behaves as `reads_peer_result: false`; search source for reads of another leg's result JSON.
- Trace one claim-bearing value in each lane to that lane's own computation path.
- Compare common scalar values only like-for-like. Agreement is smoke, not proof.
- Inspect serialization/metadata for parity-by-copy: byte-identical large arrays, copied solver dumps, or identical timestamps/hashes where independent engines should differ require explanation.
- Check Julia is semantic/canon, JAX is batched/exhaustive/proof-side where scoped, PyTorch is graph/record/flow machinery, and NumPy is not a claim-bearing engine.

Fail condition:

- Any leg reads or echoes a peer result; a leg is a thin wrapper over copied JSON; cross-engine agreement is treated as proof; role-specific tool use is absent; or one shared Python/NumPy path supplies all claim-bearing values.

## 15. NumPy leakage and control-lane boundary

Open:

- all Python imports;
- source for support, flow, record, proof, and graph computations;
- NumPy baseline/control fields;
- envelope `all_pass` or gate aggregation code.

Recompute:

- For every claim-bearing field in gates, reconstruction, SMT, ledger, append-only, and variants, trace at least one non-NumPy path through the declared engine role.
- Identify every NumPy-only value and check it is marked baseline/control/supportive.
- Check NumPy is not used as the hidden canonical table that Julia/JAX/PyTorch merely serialize.

Fail condition:

- Any claim-bearing value is NumPy-only; NumPy baseline values feed `all_pass`; NumPy is treated as a fourth evidence engine; or engine legs only wrap a NumPy-computed table.

## 16. Source provenance and cited-source discipline

Open:

- `source_paths`, `source_sha256`, and source-ref fields;
- cited slices from the build card and mine receipt;
- source files implementing carrier import, probe predicates, ledgers, proof, and variants.

Recompute:

- Match each source-backed claim to a cited source path and line/slice.
- Check the owner-language doctrine level is separated from exact math formalization level: shell/radiation/no-destruction doctrine may be sourced; `|P_t| = |P_{t+1}| + |Delta R_t|` and exact reconstruction remain candidate math.
- Verify field-wide compression/readout language obeys the wiki contract: finite object, probe family, pass condition, kill condition, and controls.

Fail condition:

- The build claims source support for math not on file; source hashes are absent; candidate formalizations are promoted to doctrine; readouts lack finite object/probe/pass/kill fields; or owner-kernel prose/LLM agreement is treated as proof.

## 17. Envelope validator and gate-to-field traceability

Open:

- envelope source;
- envelope result JSON;
- validator output if emitted;
- gate/result-field mapping for all CFR gates and controls.

Recompute:

- Run the repo validator command required by the build card on the envelope result with `--require-pytorch`.
- For every build gate G1-G8, trace the gate status to named computed fields and source code.
- Check every required control has a fired/not-fired value plus a flip/fail measurement, not only a boolean label.
- Ensure `all_pass` cannot be true if any required computed field/control/model/mismatch/charge/hash-chain check is absent.

Fail condition:

- Validator fails; a gate has no named computed receipt field; a control is missing or non-firing; `all_pass` ignores missing anti-triviality defenses; or envelope synthesis upgrades the evidence ceiling.

## 18. Minimum manual recomputation packet for the auditor

Open:

- the same artifacts as checks 4, 5, 6, 7, 8, 10, and 11.

Recompute:

- Full cardinality ledger for every emitted step.
- One raw reconstruction by hand from one final survivor plus one record row, then full set equality from `P_T union record`.
- One quotient-class killed-information count from class size greater than one.
- One erasure environment-charge arithmetic line: `bits_erased * ln(2)`.
- One hash-chain step, including previous hash.
- One SMT proof trace from computed row values to solver assertions, plus the dropped-record SAT alternative model.

Fail condition:

- Any of these minimum recomputations cannot be performed from emitted artifacts; any value differs without a declared tolerance/defect; or the packet requires trusting builder prose for a load-bearing claim.
