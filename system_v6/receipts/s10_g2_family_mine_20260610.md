# S10 G2 Family Mine - 2026-06-10

Status: read-lane mine only. No build, no sim run, no queue mutation.

Deliverable boundary: this file prepares the S10 G2-family round. It does not promote compact G2, split G2(2), SU(3) stabilizers, orientation classes, or any bridge/axis/physics claim.

Notation boundary: `G2(2)` below means the split real form often written `G_{2(2)}`. The finite Chevalley group `G2(2)` is a different object and should be a separate packet only if selected explicitly.

## 1. What committed packets already establish

### Compact G2 forced-vs-installed discriminator

- `system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json` is `scratch_diagnostic`, with claim ceiling "no promotion or canonical admission" (`classification`, `claim_ceiling`).
- The packet asks whether `G2=Aut(O)=Der(O), dim 14` is forced by bare root constraints or installed by the octonion carrier constraint. Bare root constraints are only finite multiplication table plus nonzero commutator/order-sensitivity witness; installed constraint is seven anticommuting imaginary units with Fano/Cayley-Dickson closure.
- Result: `forced_vs_installed_verdict=INSTALLED_NOT_FORCED`; `forced_by_root=false`; `installed_by_carrier_constraint=true`.
- Engine-stable derivation dimensions: `Der(H)=3`, `Der(M2R)=3`, `Der(O)=14`, `Der(O_corrupted)=3` across JAX, Julia, and PyTorch. The key local numbers for S10 are therefore `14` for compact octonion G2 and `3` for the corrupted/underinstalled control.
- Solver split: H and M2R bare-root lanes are SAT; O seven-unit closure is SAT; H seven-unit closure and three-unit alternative closure are UNSAT. This is the local guard against saying "the root forces G2."

### Bloch/weld orientation-translation machinery

- `system_v6/receipts/octonion_orientation_reconciliation_20260610.md` closes only a map-of-maps ledger. It explicitly says no carrier, nonassoc, bridge, axis, or formal-admission claim is promoted.
- Bloch root map: `octonion_permutation_old_to_new=[0,3,2,1,6,7,4,5]`, `octonion_signs_old_to_new=[1,-1,1,1,-1,-1,1,-1]`, with the same relabel/sign map lifted to both Cayley-Dickson halves before doubling.
- MCT weld map: `perm=[0,1,2,3,4,7,6,5]`, `signs=[1,1,1,1,1,-1,1,-1]`, `bracket_convention=left`, after reading the exported canon `C[k][i][j]` table.
- Rule for S10: no row may compare a Bloch-root witness against an MCT-weld row unless it names the map and lift rule. A raw `e_i` label is not an invariant.

### Bloch root packet facts relevant to orientation

- `system_v6/sims/bloch_root_admissibility_discriminator_v0/results/bloch_root_admissibility_discriminator_v0_envelope_results.json` is `scratch_diagnostic`, not carrier admission.
- The packet already gives Bloch/Pauli dimension separation: commuting sigma-z probes have affine dimension `1`; full noncommuting Pauli probes have affine dimension `3`.
- The same packet records the R/C/H/O Hopf ladder dimensions `base=[1,2,4,8]`, `fiber=[0,1,3,7]`.
- Its octonion alternativity row records `ordered_distinct_imaginary_triples=210`, `fano_line_ordered_triples_zero=42`, and `nonassociating_triples=168`; label-shuffle and orientation-flip controls keep the counts invariant.
- S10 can reuse these counts as compact-O controls, but not as a split-O fixture.

### MCT nonassoc weld facts relevant to G2-family build shape

- `system_v6/sims/mct_nonassoc_weld_packet_v0/results/mct_nonassoc_weld_packet_v0_envelope_results.json` imports `system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json` with bracket convention `left`, artifact sha `824a0a2c794a949a83e4bd650c9620464b96eb0d1dcb3d0fe4901a4e86d05f2c`, and table version `algebra_structure_constants_v1`.
- Main support branch is the three-spinor floor; direct-O is projection/lift only; sedenion is graveyard control; split-O is inactive `Var_t`.
- The weld packet computes the witness triple `(e1,e2,e4)` with residual norm `2`, density-erasure gap `0`, active bracketing class count `16`, dropped bracketing class count `8`, `O_dim_der=14`, and `O_corrupted_dim_der=3`.
- For S10: use the canon artifact and packet-local lift convention. Do not import compact-O as primitive carrier admission.

### Nesting-law / G2 rows

- `system_v6/receipts/nesting_law_audited_20260610.md` keeps `G2=Aut(O)` as a preservation-group row and `G2/SU(3)=S6`, `Spin(7)/G2=S7` as group-action/orbit rows. It also names algebra extension as a separate arrow type.
- `system_v6/sims/nesting_consistency_family_v0/results/nesting_consistency_family_v0_envelope_results.json` is `scratch_diagnostic`; family comparison promoted no variant. Its allowed arrow types include algebra extension, filtration, fibration, quotient, subset/submanifold, and tensor.
- S10 should preserve heterogeneous arrow typing: compact/split forms are not the same row as quotient, stabilizer, or group-action rows.

### Nemo/Hecke toolchain

- `system_v6/receipts/toolset_expansion_20260610.md` classifies the Nemo+Hecke result as `tool_lego_fit_probe`, `promotion_allowed=false`.
- `system_v6/probes/toolset_expansion_20260610_nemo_hecke_results.json` gives `SL(2,7)=336`, `PSL(2,7)=168`, subgroup chain `[168,21,7,1]`, and dimension chain `SU(2)=3`, `SU(3)=8`, `G2=14`.
- Use this for finite group/orientation-class sanity checks and representation-chain scouting, not as proof of a compact/split G2 packet.

## 2. External-standard family facts

External-standard means standard math input, not a Codex Ratchet result. It must be rederived or checked inside any future packet before promotion.

Sources used:

- Baez, "The Octonions": construction routes include multiplication table, Fano plane, Cayley-Dickson, Clifford/spinor/triality. URL: https://webhomes.maths.ed.ac.uk/~v1ranick/papers/baezocto.pdf
- Salamon, "Notes on the octonions": `G(V,phi)` is 14-dimensional and has isotropy `SU(3)` at a unit vector, giving `SU(3) -> G2 -> S6`. URL: https://people.math.ethz.ch/~salamon/PREPRINTS/Octonions.pdf
- Gyenge, "The Transition Function of G2 over S6": compact `G2` is identified with `Aut(O)` and the fibration `G2 -> S6` is a locally trivial `SU(3)` bundle. URL: https://www.emis.de/journals/SIGMA/2019/078/sigma19-078.pdf
- Asok-Hoyois-Wendt, "Generically split octonion algebras and A1-homotopy theory": the split octonion automorphism group is the split semisimple algebraic group `G2`. URL: https://hoyois.app.uni-regensburg.de/papers/octonionbundles.pdf
- Draper, "Notes on G2": division octonions give compact real form, split octonions give split real form; real generic 3-forms have two open orbits; the 3-form determines a nondegenerate symmetric form up to scale. URL: https://arxiv.org/pdf/1704.07819
- Pene, "Octonion multiplication and Heawood's map": Fano plane has seven points and seven three-point lines, with each pair in a unique line. URL: https://www.numdam.org/item/10.5802/cml.9.pdf
- MathOverflow orientation count note, used only as a counting pointer: 30 Fano triad arrangements times 16 sign choices gives 480 valid octonion tables; `PSL(2,7)` has order 168 as Fano-plane symmetry group. URL: https://mathoverflow.net/questions/131167/octonions-and-the-fano-plane

### Compact G2 / division octonion member

- Object: automorphism/derivation group of real division octonions, equivalently stabilizer of the compact positive 3-form on the 7D imaginary octonions.
- Standard invariant: positive-definite octonion norm; imaginary metric signature `(7,0)`; full algebra norm signature `(8,0)`.
- Local packet target: recompute `Der(O)=14`, seven Fano lines, phi preservation, SU(3) stabilizer row, and orientation-class invariants under named basis/sign maps.
- Controls: H and M2R bare-root controls, corrupted-O dimension drop to `3`, erased Fano/closure controls, density-erasure where relevant.

### Split G2(2) / split octonion member

- Object: automorphism/derivation group of the split octonions; split real form `G_{2(2)}`.
- Standard invariant: split-octonion norm signature `(4,4)` on the 8D algebra; imaginary trace-zero part has signature `(3,4)` or `(4,3)` depending on sign convention. A packet must state the sign convention and not mix it with compact `(7,0)`.
- Standard differences from compact O: still noncommutative, nonassociative, alternative, and composition; not division; has isotropic nonzero elements / zero divisors; stabilizes a split stable 3-form and an indefinite metric.
- Local packet target: build a source-pinned split-O multiplication table, compute derivation/stabilizer dimension `14`, verify preservation of the split 3-form and indefinite metric, and run compact-O as a wrong-sign control.
- Required controls: compact O must fail the split signature row; split-O must fail division/positive-norm row; zero-divisor/isotropic witness must be computed, not asserted.

### 3-form choices

- Compact 3-form row: phi from compact octonion multiplication on `Im(O)`, metric positive definite, stabilizer compact G2.
- Split 3-form row: phi_split from split-O multiplication on the trace-zero subspace, metric indefinite `(3,4)` or `(4,3)` by convention, stabilizer split G2(2).
- Orientation/sign-row variants: same multiplication family under relabel/sign basis maps; row must report table hash, phi hash, metric signature, and whether the induced 3-form sits in the compact or split open orbit.
- Kill condition: if a packet reports "G2" without saying compact vs split and metric signature, it is not S10-admissible.

### SU(3) stabilizer picks

- Compact standard: choosing a unit imaginary octonion gives stabilizer `SU(3)` in compact G2 and orbit `G2/SU(3)=S6`.
- Packet-level choice: pick the unit vector explicitly, e.g. `e1`, and record the induced complex structure on its orthogonal 6-space. Changing the picked unit should be an orbit-equivalent row, not a new theorem.
- Split standard: stabilizers depend on causal type of the chosen vector under the split metric. Do not reuse compact `SU(3)` automatically for split rows; split rows need their own stabilizer class check.
- Recommended split stabilizer work: first compute signature class of the picked vector, then derive stabilizer dimension/type from the split table and metric preservation equations.

### Signature hybrids

- Admissible as S10 family members only when explicitly fenced as hybrid controls.
- Examples: compact multiplication with split metric, split multiplication with compact metric, compact phi with wrong metric, split phi with wrong metric.
- Expected role: designed-to-fail controls that prevent accidental collapse of compact and split rows. They should not become promoted family members unless a later owner directive explicitly changes the target.

## 3. The 480 orientations

Working interpretation for S10: the "480 orientations" are multiplication-table variants obtained from Fano-plane triad arrangements and sign/orientation choices over seven imaginary units. The standard counting pointer is `30` labelled Fano triad arrangements times `16` valid sign/orientation choices, giving `480`. `PSL(2,7)` of order `168` is the Fano-plane automorphism/symmetry group and should be used as an orbit sanity check, not as a substitute for table-level computation.

What varies per orientation:

- oriented Fano lines / structure constants `C[k][i][j]`;
- phi components and phi hash;
- basis/sign map into the repo's canon artifact convention;
- which component label carries a witness residual, e.g. the MCT weld residual moves under lift while norm survives;
- table hash and orientation-class id.

What should be invariant under valid compact orientation changes:

- algebra isomorphism class as compact O;
- alternativity and two-generated associativity controls;
- counts `42` Fano-line ordered triples zero, `168` ordered nonassociating triples, `210` ordered distinct imaginary triples;
- derivation dimension `14`;
- compact metric signature `(7,0)` on imaginary part;
- SU(3) stabilizer dimension `8` for a unit imaginary pick, after transporting the pick through the basis map.

What a family sim computes per orientation class:

1. table construction receipt: line triples, sign vector, `C[k][i][j]` hash, phi hash, metric signature;
2. convention bridge: map into `algebra_structure_constants_v1` or a named new orientation artifact;
3. compact invariants: `Der(O)=14`, alternativity, two-generated associativity, nonassoc count `168`, Fano-zero count `42`;
4. stabilizer row: chosen imaginary unit, stabilizer dimension/type, orbit relation to `G2/SU(3)=S6`;
5. controls: corrupted product, wrong sign, erased Fano line, label-only comparison, density-erasure where a spinor/weld row is active.

Batching recommendation: do not run 480 full packets first. First build an orientation-class enumerator that reduces the 480 tables into orbit classes under signed basis changes and Fano automorphisms, with a representative table for each class. Then run full invariant packets on representatives. Run the full 480 sweep only as a regression/coverage sidecar after representative rows pass.

## 4. Bounded build sequence for the S10 family round

Recommended sequence, grounded in existing packet state:

1. `s10_g2_family_registry_v0`: read-only/generated registry of family members and controls. Rows: compact-O G2, split-O G2(2), 480 compact orientation representatives, SU(3) stabilizer picks, 3-form choices, signature hybrids. Acceptance: every row has status `built`, `missing_fixture`, or `control_only`; no row has promotion.
2. `s10_compact_g2_orientation_representative_v0`: one compact representative using the committed canon artifact and MCT lift policy. Acceptance: recompute local invariants already established elsewhere, not new claims: `Der(O)=14`, `O_corrupted=3`, `42/168/210`, phi preservation, one SU(3) stabilizer pick.
3. `s10_orientation_class_enumerator_v0`: enumerate 480 candidate compact orientation tables, compute hashes and orbit keys under signed basis changes / Fano automorphism action, and select representatives. Acceptance: exact count receipt, duplicate/orbit ledger, no stabilizer theorem beyond classing.
4. `s10_split_octonion_fixture_v0`: build split-O constants and metric/signature conventions before any split G2 claim. Acceptance: norm signature `(4,4)` on algebra, trace-zero signature stated, zero-divisor/isotropic witness, alternativity controls, compact wrong-sign control.
5. `s10_split_g2_discriminator_v0`: derive split `G2(2)` from split-O. Acceptance: derivation/stabilizer dimension `14`, split phi and metric preservation, compact-vs-split controls, no finite `G2(2)` conflation.
6. `s10_su3_stabilizer_pick_family_v0`: compact unit-pick family first; split causal-type picks later. Acceptance: compact pick gives stabilizer dimension `8`; picked unit and transported basis map are explicit; split row deferred until split fixture is green.
7. `s10_signature_hybrid_controls_v0`: wrong-pair controls only. Acceptance: wrong metric/form pair fails the intended preservation or signature gate; controls remain `control_only`.

Packet granularity recommendation:

- One member per packet for compact representative, split fixture, split discriminator, SU(3) stabilizer pick family, and signature hybrids.
- Orientation classes batched by enumerator first, then representative packets. Do not make 480 independent packets unless the enumerator shows all 480 are materially distinct under the repo's intended invariants.
- Split-O must precede split G2(2); compact orientation enumeration can run before or beside split-O because it reads compact artifact conventions only.

## 5. Per-member tooling map

| family member | primary tools | role | controls |
|---|---|---|---|
| compact O / compact G2 | Julia carrier artifact, LinearAlgebra, JAX/PyTorch mirrors, z3/cvc5 | derive `Der(O)=14`, phi preservation, Fano closure, orientation-invariant counts | H/M2R bare root, O_corrupted=3, erased Fano line |
| compact 480 orientations | Nemo/Hecke for `PSL(2,7)` sanity, Python/JAX/Julia table enumerator, canon artifact conventions | enumerate table hashes/orbit keys; pick representatives | label-only false comparison, duplicate orbit collapse, wrong-sign rows |
| split O fixture | Julia + Python table builder, LinearAlgebra signature, z3/cvc5 raw-value controls | build split constants, `(4,4)` norm, trace-zero signature, isotropic/zero-divisor witness | compact-O wrong signature, nonzero isotropic witness, division claim killed |
| split G2(2) | LinearAlgebra derivation equations, z3/cvc5 preservation checks | derive dimension `14`, split phi and metric preservation | compact phi/metric mismatch, finite `G2(2)` name guard |
| SU(3) compact stabilizer pick | LinearAlgebra stabilizer equations, Nemo/Hecke dimension-chain sidecar | fixed unit imaginary pick, stabilizer dimension `8`, orbit row `G2/SU(3)=S6` | changed unit transported through orbit, label-only pick rejected |
| split stabilizer picks | split metric + derivation/stabilizer equations | classify stabilizer by vector signature class | compact `SU(3)` copy-paste killed |
| signature hybrids | same table/metric tooling as compact/split rows | fail-fast controls for wrong pairing | must remain `control_only` |

Nemo/Hecke use:

- Good fit for `PSL(2,7)=168`, subgroup chains, finite field matrix sanity checks, and representation-chain scouting.
- Not sufficient for table-level compact/split G2 proof without structure constants and preservation equations.

CliffordAlgebras / Clifford route:

- Use as supportive route for Cl(6) / three-spinor floor links and compact installed-carrier explanation.
- Do not let Clifford-side convenience replace octonion table/phi/signature checks in S10.

Octonion artifact conventions:

- Default compact artifact: `system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json`.
- Required fields for any new artifact: `table_version`, `bracket_convention`, basis labels, shape, `source_sha256`, `proof_tag`, table hash, phi hash, metric signature, orientation metadata, and named map/lift rule if translated from another packet.
- Required consumer rule: any downstream packet reads by named artifact/version/hash and recomputes invariants from `C[k][i][j]`; it must not use prose labels as evidence.

## 6. Open blockers / next admissible step

Open blockers:

- No committed split-O/split-G2 fixture exists in the inspected v6/v5 receipts.
- No committed 480-orientation enumerator exists as an S10 artifact.
- Existing compact G2 evidence is scratch/fit-probe only and remains bounded by its local ceilings.
- Split stabilizer picks cannot be specified by copying compact `SU(3)` without first classifying vector signature under the split metric.

Next admissible step:

`s10_g2_family_registry_v0` followed by `s10_compact_g2_orientation_representative_v0` and `s10_split_octonion_fixture_v0`. That sequence preserves compact evidence, opens the missing split branch correctly, and avoids a 480-packet explosion before orbit classes are known.

