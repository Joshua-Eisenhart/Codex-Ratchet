# Adversarial pre-audit checklist: `twistor_incidence_finite_packet_v0`

This checklist is for a fresh auditor after the build exists. It is written before outcomes are known. I did not read any `results/*.json` while authoring it. The auditor must not accept builder prose, copied precedent values, or validator success as evidence; open the source and emitted results only during the actual audit and recompute the named rows.

Read first:

- `/tmp/twi_build_card_20260610.md`
- `system_v6/receipts/twistor_incidence_mine_20260610.md`
- `system_v6/README.md`
- `system_v6/sims/pg32_sedenion_incidence/` source files only, as construction precedent
- `system_v6/sims/mct_dynamic_admissibility_packet_v0/` source files, `build_card.md`, and `audit_verdict.md` for baseline shape and ceiling discipline
- cited external-standard anchors from the mine receipt: Adamo `arXiv:1712.02196` for twistor correspondence vocabulary, Cambridge finite-projective-geometry source for `PG(3,q)` counting, and the mine receipt's no-physics/no-Penrose fence

Expected build paths:

- `system_v6/sims/twistor_incidence_finite_packet_v0/twistor_incidence_finite_packet_v0_julia.jl`
- `system_v6/sims/twistor_incidence_finite_packet_v0/twistor_incidence_finite_packet_v0_jax.py`
- `system_v6/sims/twistor_incidence_finite_packet_v0/twistor_incidence_finite_packet_v0_envelope.py`
- `system_v6/sims/twistor_incidence_finite_packet_v0/build_card.md`
- `system_v6/sims/twistor_incidence_finite_packet_v0/results/*.json`

No PyTorch source file is expected in this declared diagnostic mode. A PyTorch omission is acceptable only when the envelope says so explicitly and avoids all three-engine language.

## 1. PRECEDENT BLIND-COPY: PG(3,2) construction is recomputed in this packet

Open:

- both leg source files;
- the envelope source;
- `system_v6/sims/pg32_sedenion_incidence/*.{jl,py}` source files for comparison;
- emitted per-leg results during the actual audit.

Recompute:

- From this packet's code path, enumerate nonzero vectors of `F_2^4`, apply the projective quotient map, and count projective points. Expected computed count: `15`.
- Enumerate 2D subspaces from pairs of independent projective representatives, canonicalize each subspace by its three nonzero member points, and count unique lines. Expected computed count: `35`.
- For every point, count incident lines. Expected computed multiset: fifteen copies of `7`.
- Compare construction paths against `pg32_sedenion_incidence`: this packet may reuse finite-table idioms, but it must not derive lines from sedenion multiplication, pasted triples, or prior result JSON values.

Fail condition:

- The 15/35/7 fields are literals with no local enumeration path, line triples are copied from `pg32_sedenion_incidence` without subspace generation, any leg reads the precedent result JSONs, or the envelope accepts a leg whose point/line/incidence counts were not computed inside this packet.

## 2. Projective quotient honesty and the `q=2` no-op limitation

Open:

- quotient-map source in Julia and JAX;
- emitted quotient classes and quotient-ablation control fields;
- `G4` or equivalent gate fields.

Recompute:

- For `q=2`, verify `F_2^* = {1}` and therefore each nonzero vector is its own scalar class, while the quotient map still runs explicitly.
- Drop the quotient step in a local scratch recomputation and compare named readouts: point count, line count, incidence membership, line-intersection graph invariants, reconstruction, and separation-table rows.
- Check that any "ablation changed result" claim identifies an actual named scalar that changed. At `q=2`, a no-change result is the expected limitation unless the implementation has introduced a nontrivial representation-level readout.

Fail condition:

- The packet fakes a quotient-ablation flip at `q=2`, hides a no-op as a pass, skips quotient construction because the scalar group is trivial, or fails to report the `q=2` limitation and `q=3` discriminating follow-up when ablation changes nothing.

## 3. SEPARATION THEATER: every separation row is like-for-like

Open:

- separation-table source;
- twistor readout fields;
- MCT baseline extraction source and any pinned baseline sample fields;
- emitted separation table during the actual audit.

Recompute:

- For every claimed separation, identify the exact scalar name on both sides. Examples: quotient class count vs quotient class count; relation-component count vs relation-component count; reconstruction mismatch count vs reconstruction mismatch count.
- Check that the compared twistor and baseline samples have matched declared shape where shape matters: `15`-object rows compare to `15`-object rows, `35`-object relation rows compare to `35`-object rows, and graph component counts normalize or account for vertex count.
- For each separation, recompute whether a size-only or shape-only explanation would produce the same difference. If so, mark the row as non-separating.
- Flag accidental numeric coincidences explicitly: equal numbers across different observables are not agreement; different numbers across different shapes are not separation.

Fail condition:

- Any separation row compares unlike observables, uses raw object-size differences as structure, omits the baseline sample shape, or calls a coincidental numeric mismatch a discriminator.

## 4. KILL-CONDITION DODGING: no genuine separation means `kill_condition_met=true`

Open:

- gate logic for `G5`;
- result fields for `separation_table`, `kill_condition_met`, `all_pass`, and summary text;
- envelope synthesis source.

Recompute:

- After applying check 3, count only separation rows that are named, like-for-like, control-surviving, and not size/shape artifacts.
- If that count is zero, verify the result emits `kill_condition_met=true`, `all_pass=false` or an equivalent demotion, and plain summary language saying the candidate is parked.
- Check that no downstream field overrides the kill by pointing to PG(3,2) counts, SMT success, reconstruction success, or twistor vocabulary alone.

Fail condition:

- No readout genuinely separates from the MCT baseline and controls, but the packet says pass, "promising," "partial separation," "supports twistor geometry," or any softened equivalent instead of setting `kill_condition_met=true`.

## 5. Manual recomputation packet: 35 lines from subspace enumeration

Open:

- this packet's line-enumeration code;
- emitted point list, line list, and incidence table.

Recompute:

- Independently enumerate all nonzero 4-bit vectors.
- For every unordered independent pair `(u, v)`, compute the 2D subspace `{u, v, u+v}` over `F_2`.
- Canonicalize each line as the sorted tuple of its three projective points.
- Deduplicate and count. Expected: `35` unique lines.
- Verify every line has exactly `3` points and every unordered pair of points occurs on exactly one line.

Fail condition:

- The source lacks a pair/subspace enumeration route, the emitted line count is not `35`, any line has size other than `3`, any point pair is missing or duplicated, or the line count is only asserted by a constant.

## 6. Manual recomputation packet: one line-intersection row

Open:

- emitted line list;
- line-intersection graph source and result fields.

Recompute:

- Pick one emitted line `L={a,b,c}`.
- Count all other lines intersecting `L`: for each of the three points on `L`, there are `7` incident lines total and `6` besides `L`; no other line can share two points without being `L`. Expected degree for `L`: `3 * 6 = 18`.
- Verify the adjacency row marks exactly those lines with nonempty set intersection and excludes `L` itself.
- Verify the non-neighbor count is `35 - 1 - 18 = 16`.

Fail condition:

- The intersection graph is built from line labels or precedent rows instead of set intersection, the chosen row degree is not `18`, self-adjacency appears, or non-neighbors are not the disjoint lines.

## 7. Manual recomputation packet: reconstruction from incidence

Open:

- incidence table;
- reconstruction source;
- reconstruction result fields.

Recompute:

- From the line membership table alone, take intersections of every pair of distinct lines.
- Keep nonempty singleton intersections and deduplicate them. Expected recovered point count: `15`.
- For each recovered singleton point, reconstruct its pencil as the `7` lines containing it.
- Verify reconstructed point identifiers are not accepted merely because original point labels were carried through; the reconstruction must be derivable from membership intersections.

Fail condition:

- Reconstruction uses original labels as an oracle, recovers fewer or more than `15` points from line memberships, omits per-point pencil size `7`, or reports success without a random-bipartite/scrambled control that fails or becomes non-isomorphic.

## 8. Manual recomputation packet: SMT flip rerun

Open:

- z3 source;
- cvc5 source;
- solver input construction;
- emitted crossover proof fields.

Recompute:

- Identify the exact finite incidence fact the solvers encode, such as "two distinct projective lines do not share two or more points" or "every point-pencil has exactly seven lines."
- Trace every solver constant back to the computed incidence table from this packet, not to handwritten line literals.
- Rerun the same positive proof in z3 and cvc5. Expected positive polarity: structural fact proves as `UNSAT` for the negation, or equivalent explicitly documented polarity.
- Rerun the scrambled-incidence control. Expected control polarity: the relevant negation becomes `SAT` or the claimed regularity fails.

Fail condition:

- Incidence literals are hardcoded into solver assertions, z3 and cvc5 share one pre-rendered SMT blob rather than independent encodings, the scrambled control does not flip, solver verdicts are not load-bearing for gate status, or either solver is absent without demotion.

## 9. DECORATIVE SMT: guard against proof theater

Open:

- `TOOL_MANIFEST`;
- `TOOL_INTEGRATION_DEPTH`;
- `crossover_proofs`;
- gate aggregation logic.

Recompute:

- Remove or falsify the SMT proof result in a scratch copy mentally or by inspection and check whether `all_pass`/gate status would change.
- Verify the SMT proof uses computed table hashes or row values from the current run.
- Verify both positive and negative/control cases are recorded with solver name, encoded claim, input source, verdict, and polarity.

Fail condition:

- SMT is imported but not wired to pass/fail, the proof could be deleted without changing the verdict, only the positive case exists, or the "proof" is a restatement of already-hardcoded expected counts.

## 10. CHIRALITY ROW: computed pairing, not label echo

Open:

- pinned pairing definition;
- chirality row source;
- orientation-reversal control source;
- label-shuffle control source;
- emitted chirality fields.

Recompute:

- Identify the pinned finite pairing or symplectic/dual split used for `P_chir`.
- For at least two emitted points or lines, recompute the chirality value from the pairing, not from object IDs, list order, or labels like `"left"`/`"right"`.
- Apply the orientation-reversal control and verify the chirality row flips under the declared rule.
- Apply the label shuffle and verify structural chirality values are invariant after unshuffling, while raw labels change.

Fail condition:

- `P_chir` is a label echo, object-index parity, file-order bit, or hardcoded split; orientation reversal does not flip; label shuffle changes the structural row; or chirality is used as a physics/helicity claim rather than a finite probe row.

## 11. Cross-leg parity without parity-by-copy

Open:

- Julia source;
- JAX source;
- envelope comparison source;
- per-leg source hashes and `reads_peer_result` fields.

Recompute:

- Verify Julia and JAX independently enumerate points, quotient classes, lines, incidence, graph rows, reconstruction, controls, and separation scalars.
- Check that neither leg reads the other's result JSON or imports a generated table from the other leg.
- Compare only like-for-like shared scalars in the envelope: point count, line count, pencil sizes, selected graph invariants, reconstruction mismatch count, solver polarity flags, kill/separation booleans.
- Confirm common scalar divergence is computed per named scalar, not as an aggregate across different observables.

Fail condition:

- One leg is a thin reader/mirror of the other, `reads_peer_result` is true or contradicted by source, the envelope compares unlike observables, or cross-engine agreement is promoted above smoke-test status.

## 12. NumPy leakage and bare-array control lanes

Open:

- Python imports;
- JAX source;
- any helper modules;
- `claim_path_tools` or equivalent manifest fields.

Recompute:

- Search for `import numpy`, `np.`, `.numpy()`, `np.asarray`, `scipy`, and hidden host-copy paths.
- If NumPy appears, classify whether it is control-lane serialization only or claim-path computation.
- Verify JAX claim-path arrays stay in JAX or plain finite integer data structures with explicit conversion boundaries.

Fail condition:

- NumPy, SciPy, or host-copy array operations compute claim-bearing incidence, graph, reconstruction, separation, or proof inputs; the manifest omits the leakage; or JAX is only a bare `jnp` mirror with no independent finite-workhorse role.

## 13. Label shuffle invariance

Open:

- label-shuffle control source;
- emitted pre/post shuffle structural invariants;
- raw label table fields.

Recompute:

- Apply the emitted permutation to point labels and line labels.
- Recompute incidence membership, line-intersection graph degree sequence, component count, clique/pencil structure, reconstruction count, and separation scalars after translating labels back.
- Verify raw labels changed while structural invariants stayed stable.

Fail condition:

- No label-shuffle control exists, the shuffle is identity, structural invariants change under relabeling, raw label fields do not change, or the packet treats label-sensitive values as structural evidence.

## 14. Scramble and random-bipartite controls actually break structure

Open:

- scramble-incidence source;
- random bipartite graph source;
- control result fields.

Recompute:

- For scramble-incidence, verify it changes incidence memberships while preserving enough superficial shape to be a real control, not total nonsense.
- Recompute graph invariants after scramble: at least one claimed invariant or reconstruction step must fail or become non-isomorphic.
- For the random bipartite graph control, verify it preserves the declared size or degree profile, then fails reconstruction or separates from the PG(3,2) incidence structure.

Fail condition:

- Controls are not run, controls are too malformed to test the claim, controls preserve every claimed readout, or the packet calls a control-surviving readout a pass without demotion.

## 15. DECLARED-MODE HONESTY: two-engine diagnostic, no three-engine laundering

Open:

- envelope source;
- emitted `engine_contract`;
- validator command receipt or validator outcome field;
- `system_v6/README.md` mode rule.

Recompute:

- Verify mode is exactly `julia_canon_plus_jax_diagnostic` or a semantically equivalent explicit two-engine diagnostic declaration.
- Confirm lanes are Julia and JAX only, with PyTorch omission explained by declared mode.
- Run the validator command expected by the card without `--require-pytorch` if the schema permits. If the current validator requires three legs, verify the result records that schema mismatch honestly and does not work around it by faking PyTorch.

Fail condition:

- Any field says `all_three_full_sims`, `three-engine`, PyTorch-ran, or equivalent; a dummy PyTorch result is fabricated; validator failure is hidden; or the envelope claims canonical/full-process status from a two-engine diagnostic.

## 16. FENCE LANGUAGE: no twistor-to-physics/manifold/Penrose promotion

Open:

- every source file;
- `build_card.md`;
- emitted result JSONs;
- envelope summary strings;
- any audit or README created accidentally in the sim folder.

Recompute:

- Search for forbidden promotion terms and phrases: `twistors =`, `manifold`, `spacetime`, `GR`, `general relativity`, `physics`, `light cone` as physics, `Penrose validates`, `canonical`, `formal admission`, `axis`, `bridge`.
- Allow only fenced external-standard vocabulary when it is explicitly marked as finite incidence/discriminator background.
- Verify exact ceilings everywhere: `classification="scratch_diagnostic"`, `promotion_allowed=false`, `formal_admission_allowed=false`.

Fail condition:

- Any result or source claims twistor incidence is the manifold, validates a physics/spacetime/GR/Penrose claim, implies bridge/axis/formal admission, or emits ceiling fields with any value other than the pinned false/scratch values.

## 17. Build-card atomicity and forbidden file shape

Open:

- sim folder file list;
- `build_card.md`;
- git diff/file status if auditing in-repo.

Recompute:

- Compare `system_v6/sims/twistor_incidence_finite_packet_v0/build_card.md` byte-for-byte against `/tmp/twi_build_card_20260610.md`.
- Verify only the expected source files, `build_card.md`, and `results/*.json` exist under the packet folder.
- Verify no `audit_verdict.md` was created by the builder.

Fail condition:

- Extra docs/audit files are created, existing files outside the packet are edited, the build card is not verbatim, or generated results are separated from the per-sim folder.

## 18. Minimum audit verdict classification

Open:

- all gate fields;
- all controls;
- separation table;
- kill condition;
- validator outcome;
- manual recomputation notes from checks 5-8.

Recompute:

- Classify the packet using only recomputed and source-backed evidence:
  - `BROKEN`: required legs do not run, core PG(3,2) counts fail, or source/result shape is unusable.
  - `DECORATIVE`: PG(3,2) arithmetic exists but SMT, controls, chirality, separation, or reconstruction are theater.
  - `KILLED-HONESTLY`: finite construction works but no valid separation survives, and `kill_condition_met=true` is emitted.
  - `GENUINE-WITH-CAVEATS`: at least one like-for-like separation survives controls, all hard fences hold, and remaining issues are named non-promotional caveats.

Fail condition:

- The verdict is stronger than the weakest surviving gate permits, a killed candidate is narrated as success, or any caveat is used to promote the packet rather than constrain it.

