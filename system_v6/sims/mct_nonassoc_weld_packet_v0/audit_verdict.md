# Fresh audit verdict: mct_nonassoc_weld_packet_v0

Verdict: GENUINE-WITH-CAVEATS.

The arithmetic claim is genuine as a bounded scratch diagnostic: the associator is recomputed from the imported structure constants, the orientation reconciliation is a whole-table basis lift, the 512 ordered-triple sweep recomputes to 168 nonzero / 344 zero, density erasure and drop-bracketing quotient counts recompute, raw-value SMT flips, and G2 installed-only controls recompute.

The caveat is state-surface instrumentation: the packet encodes the M(C,t) update through `support_table` rows, quotient keys, `operations`, `controls`, and `kill_conditions`, but it does not emit a named `M_t` tuple with explicit `Probe_t`, `~_t`, `Q_t`, `H_t`, and `R_t` fields. That is not decorative, but it should block any stronger state-update claim until those fields are made explicit.

Ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; no primitive octonion carrier admission; no carrier admission; no final M(C); no Axis0; no bridge; no physics; G2 installed-only, not root-forced; one bounded weld packet, not tower integration.

## Audit discipline

- The lane card said "all 11 checks"; the checklist file contains 13 numbered checks. I audited all 13 rather than dropping checks 12-13.
- Builder output and validator status were not used as evidence. I did not intentionally open result JSON for value lookup. One exploratory `rg` command did print result-file matches after a glob miss; the verdict values below come from source, artifact, and independent recomputation.
- The Python interpreter used for recomputation was the Makefile sim-stack interpreter: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3` (`Makefile:2-5`).
- `system_v6/sims/mct_nonassoc_weld_packet_v0/` was untracked before this verdict was written. This audit evaluates the current working tree files, not a committed artifact.

## F1-F4 adjudication

### F1. Orientation reconciliation

Result: PASS.

Source quote:

```text
ARTIFACT_TO_COMMITTED_PERM = [0, 1, 2, 3, 4, 7, 6, 5]
ARTIFACT_TO_COMMITTED_SIGNS = [1, 1, 1, 1, 1, -1, 1, -1]
```

JAX, PyTorch, and Julia all define the same perm/sign lift (`mct_nonassoc_weld_packet_v0_jax.py:43-47`, `mct_nonassoc_weld_packet_v0_pytorch.py:41-42`, `mct_nonassoc_weld_packet_v0_julia.jl:30-31`). The lift is applied by `transform_table`, which remaps every table product through inverse target indices and source/target signs, not only the witness triple (`mct_nonassoc_weld_packet_v0_jax.py:129-142`, `mct_nonassoc_weld_packet_v0_pytorch.py:112-125`, `mct_nonassoc_weld_packet_v0_julia.jl:85-101`).

Manual recomputation:

- Raw artifact `(e1,e2,e4)`: `e1*e2=e3`; `(e1*e2)*e4=-e5`; `e2*e4=e6`; `e1*(e2*e4)=e5`; residual `-2e5`, vector `[0,0,0,0,0,-2,0,0]`.
- Lifted committed convention `(e1,e2,e4)`: left `e7`, right `-e7`, residual `2e7`, vector `[0,0,0,0,0,0,0,2]`.
- Spot-check 1: source triple `(1,2,5)` maps to target `(1,2,7)`; raw residual `[0,0,0,0,2,0,0,0]`; lifted residual `[0,0,0,0,-2,0,0,0]`; matches induced vector lift.
- Spot-check 2: source triple `(3,6,5)` maps to target `(3,6,7)`; raw residual `[0,0,-2,0,0,0,0,0]`; lifted residual `[0,0,2,0,0,0,0,0]`; matches induced vector lift.
- Spot-check 3: source triple `(4,5,1)` maps to target `(4,7,1)`; raw residual `[0,0,-2,0,0,0,0,0]`; lifted residual `[0,0,2,0,0,0,0,0]`; matches induced vector lift.

Conclusion: the reconciliation is a genuine whole-table basis transformation, not a per-triple patch.

### F2. The 168

Result: PASS.

Source quote:

```text
for i in 0:7, j in 0:7, k in 0:7
    row = associator(table, (i, j, k))
```

Julia loops over all ordered triples (`mct_nonassoc_weld_packet_v0_julia.jl:236-246`), PyTorch loops over all ordered triples (`mct_nonassoc_weld_packet_v0_pytorch.py:258-268`), and JAX constructs all `8^3` triples then vmaps the residual norm computation (`mct_nonassoc_weld_packet_v0_jax.py:287-304`). The associator function itself performs two binary multiplication paths and subtracts right from left (`mct_nonassoc_weld_packet_v0_jax.py:161-177`, `mct_nonassoc_weld_packet_v0_pytorch.py:144-161`, `mct_nonassoc_weld_packet_v0_julia.jl:133-150`).

Independent full sweep over the lifted table:

```text
total=512
nonzero=168
zero=344
max_norm_sq=4
```

This matches the blind Fano count: zero = identity-participating 169 + repeated-input 133 + Fano-line distinct 42 = 344; nonzero = 512 - 344 = 168 (`/tmp/weld2_blind_expected_20260610.md:86-118`).

Ten manual spot recomputations from the lifted table:

| triple | left | right | residual | norm_sq |
|---|---|---|---|---:|
| `(0,1,2)` | `e3` | `e3` | `0` | 0 |
| `(1,2,4)` | `e7` | `-e7` | `2e7` | 4 |
| `(1,2,3)` | `-1` | `-1` | `0` | 0 |
| `(1,1,4)` | `-e4` | `-e4` | `0` | 0 |
| `(2,3,5)` | `-e4` | `e4` | `-2e4` | 4 |
| `(3,4,6)` | `e1` | `-e1` | `2e1` | 4 |
| `(4,5,7)` | `e6` | `-e6` | `2e6` | 4 |
| `(5,6,1)` | `-e2` | `e2` | `-2e2` | 4 |
| `(6,7,2)` | `-e3` | `e3` | `-2e3` | 4 |
| `(7,1,3)` | `e5` | `-e5` | `2e5` | 4 |

Conclusion: the `168` is computed by ordered-triple associator evaluation, not transcribed from the blind sheet.

### F3. Earned vs by-construction density erasure

Result: PASS WITH CAVEAT.

Source quote:

```text
rho_left = density(left_spinor)
rho_right = density(right_spinor)
```

The density-erasure path uses the computed left/right products from the positive associator row, extracts their committed-component signs, builds two spinors, computes `rho_left` and `rho_right`, and then computes the norm gap (`mct_nonassoc_weld_packet_v0_jax.py:195-214`, `mct_nonassoc_weld_packet_v0_pytorch.py:179-198`, `mct_nonassoc_weld_packet_v0_julia.jl:157-178`). Independent recomputation gives left sign `+1`, right sign `-1`, spinor gap `2.0`, density gap `0`.

Quotient recomputation is row equality, not an asserted count. Active keys include `P_phase`, `P_assoc_vec`, `P_bracket_side`, and `left_or_right_product`; dropped keys keep only `psi_id`, `triple_name`, `P_density`, and `P_order` (`mct_nonassoc_weld_packet_v0_jax.py:258-284`, `mct_nonassoc_weld_packet_v0_pytorch.py:241-255`, `mct_nonassoc_weld_packet_v0_julia.jl:221-233`). Independent support-slice count:

```text
support_rows=16
active_bracketing_classes=16
dropped_bracketing_classes=8
refines_when_active=true
```

Positive-row merge witness:

- Active left key contains product `e7` and `P_bracket_side=left`.
- Active right key contains product `-e7` and `P_bracket_side=right`.
- Dropped key removes the bracketing and product fields, so the two rows merge.

Caveat: the lifted spinor row is a minimal sign-projection witness tied to the committed component, not a full three-spinor carrier action. That is admissible for this scratch diagnostic, but it should not be widened into carrier admission.

### F4. Shared-state update

Result: PASS WITH CAVEAT.

Source quote:

```text
"support_table": rows
"operations": {
    "retained_five": { ... },
    "sixth_operation": "associator_bracketing",
}
```

The associator is not a detached residual dictionary: `support_rows` creates per-state probe rows containing `P_density`, `P_order`, `P_phase`, `P_assoc_vec`, `P_assoc_norm`, `P_assoc_component`, `P_bracket_side`, `P_density_erasure`, and `P_alt_control` (`mct_nonassoc_weld_packet_v0_jax.py:217-255`, `mct_nonassoc_weld_packet_v0_pytorch.py:201-238`, `mct_nonassoc_weld_packet_v0_julia.jl:181-219`). `quotient_counts(rows)` recomputes class counts from the same rows. The emitted `operations.retained_five` records compression, expansion, warping, folding, and reindexing on those row-derived counts and values (`mct_nonassoc_weld_packet_v0_jax.py:657-666`, `mct_nonassoc_weld_packet_v0_pytorch.py:528-537`, `mct_nonassoc_weld_packet_v0_julia.jl:452-461`).

Caveat: the reconciled spec names `Probe_t`, `~_t`, `Q_t`, `H_t`, and `R_t` as first-class fields (`system_v6/receipts/mct_reconciled_spec_20260609.md:16-41`). This packet encodes those through row/probe/quotient/control/result surfaces but does not emit named `M_t.Probe_t`, `M_t.equiv_t`, `M_t.Q_t`, `M_t.H_t`, or `M_t.R_t`. That is the main ceiling on the shared-state update claim.

## Manual recomputation packet

### 1. Witness multiplication

Artifact table metadata:

- Basis labels are `1,e1,e2,e3,e4,e5,e6,e7`; dimension 8; shape `[8,8,8]`; table version `algebra_structure_constants_v1` (`algebra_structure_constants_v1.json:786-805`).
- Multiplication meaning is `mul(a,b)[k]=sum_ij C[k,i,j]*a[i]*b[j]` (`algebra_structure_constants_v1.json:820-826`).

Raw artifact convention:

```text
e1*e2 = e3
(e1*e2)*e4 = -e5
e2*e4 = e6
e1*(e2*e4) = e5
residual = -2e5 = [0,0,0,0,0,-2,0,0]
```

Committed lifted convention:

```text
e1*e2 = e3
(e1*e2)*e4 = e7
e2*e4 = e6
e1*(e2*e4) = -e7
residual = 2e7 = [0,0,0,0,0,0,0,2]
```

### 2. Quotient count both ways

Independent recomputation over the packet's finite eight-triple support:

```text
support_rows = 16
active bracketing quotient = 16 classes
dropped bracketing quotient = 8 classes
direction = coarsening when dropped
```

This satisfies the blind drop-bracketing direction (`/tmp/weld2_blind_expected_20260610.md:182-196`) and the checklist requirement to recompute the same slice active/inactive (`/tmp/weld2_pre_audit_checklist_20260610.md:61-71`).

### 3. SMT flip

Independent raw-value SMT recomputation:

```text
z3: positive residual == 0 -> unsat
z3: quaternion residual == 0 -> sat
cvc5: positive residual == 0 -> unsat
cvc5: quaternion residual == 0 -> sat
```

The source binds raw residual components, not derived booleans (`mct_nonassoc_weld_packet_v0_jax.py:448-510`, `mct_nonassoc_weld_packet_v0_pytorch.py:389-433`, `mct_nonassoc_weld_packet_v0_julia.jl:338-362`).

### 4. Control failure semantics

Quaternion control:

```text
e1*e2 = e3
(e1*e2)*e3 = -1
e2*e3 = e1
e1*(e2*e3) = -1
residual = 0
```

Repeated-input alternativity control:

```text
e1*e1 = -1
(e1*e1)*e4 = -e4
e1*e4 = e5 in lifted source row convention for that path
e1*(e1*e4) = -e4
residual = 0
```

Corrupted G2 control has a real failure value, not a pass flag. Independent exact-rank recomputation:

```text
H: rank=13, dim Der=3
M2R: rank=13, dim Der=3
O: rank=50, dim Der=14
O_corrupted: rank=61, dim Der=3
```

## Per-check results

### 1. Residual lookup echo

open: Could have been a residual lookup table.
recompute: Source associator performs `xy`, `yz`, `left`, `right`, and `left - right` using `multiply` over `C[k][i][j]`; independent witness and sweep spot recomputations match.
fail-condition: Not triggered. No triple-index residual dictionary or witness branch was found.
evidence-field: `associator`, `multiply`, `W1.artifact_raw_residual`, `W1.committed_lift_residual`.
source-citation: `mct_nonassoc_weld_packet_v0_jax.py:157-177`, `mct_nonassoc_weld_packet_v0_pytorch.py:140-161`, `mct_nonassoc_weld_packet_v0_julia.jl:120-150`.
result: PASS.

### 2. Quotient theater and density erasure

open: Density erasure could have been asserted.
recompute: Density is computed from left/right spinors; quotient counts are computed by row equality with and without bracketing fields; independent count is `16 -> 8`.
fail-condition: Not triggered, with caveat that the spinor lift is minimal sign-projection.
evidence-field: `density_erasure_receipt`, `quotient_counts`, `support_rows`.
source-citation: `mct_nonassoc_weld_packet_v0_jax.py:195-214`, `mct_nonassoc_weld_packet_v0_jax.py:258-284`, `mct_nonassoc_weld_packet_v0_julia.jl:157-178`, `mct_nonassoc_weld_packet_v0_julia.jl:221-233`.
result: PASS WITH CAVEAT.

### 3. Order/bracketing conflation

open: Binary order evidence could have been used as ternary bracketing evidence.
recompute: Positive associator uses both parenthesized products and residual; `P_order` is a separate row value used in quotient keys, not the associator proof.
fail-condition: Not triggered.
evidence-field: `left_product`, `right_product`, `residual_vector`, `P_order`, `order_and_bracketing_receipt_families_separate`.
source-citation: `mct_nonassoc_weld_packet_v0_jax.py:161-181`, `mct_nonassoc_weld_packet_v0_jax.py:217-255`, `mct_nonassoc_weld_packet_v0_jax.py:577-581`.
result: PASS.

### 4. Tautological controls

open: Controls could have been hardcoded zeros or `pass=true`.
recompute: Quaternion, alternativity, raw-matrix, drop-bracketing, G2 corruption, bare-root, and shuffle controls each compute values from table/tensor/solver paths.
fail-condition: Not triggered. Caveat: density erasure is still a designed sign-projection quotient.
evidence-field: `controls`, `raw_matrix_control`, `g2_receipt`, `shuffle_receipt`.
source-citation: `mct_nonassoc_weld_packet_v0_jax.py:307-318`, `mct_nonassoc_weld_packet_v0_jax.py:419-445`, `mct_nonassoc_weld_packet_v0_jax.py:513-524`, `mct_nonassoc_weld_packet_v0_jax.py:590-599`.
result: PASS WITH CAVEAT.

### 5. Derived-boolean SMT

open: SMT could have received booleans rather than raw values.
recompute: z3 and cvc5 variables are equated to integer residual components and density-erased norm; independent flip matches `unsat/sat`.
fail-condition: Not triggered.
evidence-field: `z3_raw_value_proof.bound_raw_values`, `cvc5_raw_value_proof.bound_raw_values`.
source-citation: `mct_nonassoc_weld_packet_v0_jax.py:448-510`, `mct_nonassoc_weld_packet_v0_pytorch.py:389-433`, `mct_nonassoc_weld_packet_v0_julia.jl:338-362`.
result: PASS.

### 6. Structure-constant provenance

open: Packet could have used a different table while claiming source lock.
recompute: All legs load `system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json`; artifact hash recomputed as `824a0a2c794a949a83e4bd650c9620464b96eb0d1dcb3d0fe4901a4e86d05f2c`; metadata matches table version, proof tag, proof pass, basis shape, and bracket convention.
fail-condition: Not triggered.
evidence-field: `ARTIFACT_PATH`, `artifact_sha256`, `source_sha256`, `table_version`, `bracket_convention`, `proof_tag`, `proof_pass`.
source-citation: `mct_nonassoc_weld_packet_v0_jax.py:30`, `mct_nonassoc_weld_packet_v0_jax.py:118-126`, `mct_nonassoc_weld_packet_v0_jax.py:627-639`, `algebra_structure_constants_v1.json:786-819`.
result: PASS.

### 7. Carrier overclaim and branch erasure

open: Packet could admit octonions as primitive carrier or force G2 from roots.
recompute: Source and build card preserve branch B as main support, direct O as projection/lift row only, sedenion as graveyard/control, split-O as `Var_t_inactive`, and G2 as installed-only.
fail-condition: Not triggered.
evidence-field: `PIN_BLOCK.ceiling`, `carrier_provenance.derived_default_note`, `branches`, `g2_language`.
source-citation: `build_card.md:5-7`, `mct_nonassoc_weld_packet_v0_jax.py:63-78`, `mct_nonassoc_weld_packet_v0_jax.py:627-639`, `mct_nonassoc_weld_packet_v0_envelope.py:187-189`.
result: PASS.

### 8. Fixture isolation from shared packet state

open: Associator could be a sidecar detached from packet state.
recompute: Associator values feed `support_rows`, quotient keys, `support_table`, `operations.retained_five`, `controls`, and `kill_conditions`; class counts change from row equality on the support table.
fail-condition: Not triggered as a sidecar-table failure, but explicit M(C,t) field names are underinstrumented.
evidence-field: `support_table`, `operations.retained_five`, `controls`, `kill_conditions`, `class_count_delta`.
source-citation: `mct_nonassoc_weld_packet_v0_jax.py:217-284`, `mct_nonassoc_weld_packet_v0_jax.py:657-672`, `mct_nonassoc_weld_packet_v0_julia.jl:181-233`, `mct_nonassoc_weld_packet_v0_julia.jl:451-468`.
result: PASS WITH CAVEAT.

### 9. Cross-leg parity-by-copy

open: Legs could read each other's result files or copy claim arrays.
recompute: Julia, JAX, and PyTorch each load the same source artifact and compute locally. No leg reads peer result files. The envelope reads leg results as an aggregator only (`mct_nonassoc_weld_packet_v0_envelope.py:39-41`), so envelope agreement is smoke, not proof.
fail-condition: Not triggered for legs. Envelope aggregation is expected but not evidence by itself.
evidence-field: `READS_PEER_RESULT=false`, `load_artifact`, `engine_contract.reads_peer_result=false`.
source-citation: `mct_nonassoc_weld_packet_v0_julia.jl:22`, `mct_nonassoc_weld_packet_v0_julia.jl:373-390`, `mct_nonassoc_weld_packet_v0_jax.py:35`, `mct_nonassoc_weld_packet_v0_jax.py:527-544`, `mct_nonassoc_weld_packet_v0_pytorch.py:31`, `mct_nonassoc_weld_packet_v0_pytorch.py:449-466`.
result: PASS.

### 10. PyTorch honesty

open: PyTorch could be decorative or NumPy/JAX-backed.
recompute: PyTorch uses `torch.einsum` for multiplication, torch tensors for associator values, torch density and rank paths, z3/cvc5 for raw-value flips, and `.detach().cpu().tolist()` only for serialization/readout.
fail-condition: Not triggered.
evidence-field: `multiply`, `associator`, `density_erasure_receipt`, `derivation_summary`, `tool_calls`.
source-citation: `mct_nonassoc_weld_packet_v0_pytorch.py:132-161`, `mct_nonassoc_weld_packet_v0_pytorch.py:179-198`, `mct_nonassoc_weld_packet_v0_pytorch.py:295-316`, `mct_nonassoc_weld_packet_v0_pytorch.py:549-583`.
result: PASS.

### 11. NumPy leakage

open: NumPy could be hidden claim path.
recompute: No `import numpy`, `np.`, `np.asarray`, CSV, or pickle claim path was found in source. JAX uses `jax.numpy`; PyTorch uses `torch`; Julia uses the artifact and Julia arrays. PyTorch host copies are `.detach().cpu().tolist()` serialization/readout after tensor computation.
fail-condition: Not triggered.
evidence-field: `TOOL_MANIFEST`, `foreign_runtime_manifest.forbidden_exchange`, source import scan.
source-citation: `mct_nonassoc_weld_packet_v0_jax.py:19`, `mct_nonassoc_weld_packet_v0_jax.py:83-94`, `mct_nonassoc_weld_packet_v0_pytorch.py:12-18`, `mct_nonassoc_weld_packet_v0_pytorch.py:79-83`, `mct_nonassoc_weld_packet_v0_envelope.py:157-164`.
result: PASS.

### 12. Source hash and build-card identity

open: Build card or source hash fields could be stale.
recompute: `cmp` shows `build_card.md` is byte-identical to `/tmp/weld2_build_card_20260610.md`. Source hashes computed fresh:

```text
build_card = 250a1351a29d67dd694897785ddb237962ecd451bdc35f776e07ff2c8425be6f
julia = 910c6dcfb7b4a9561c709a4342f92b5cfd70c94bf253951422c0a36a758b97be
jax = a858b1e8a82d6c26cc959ed2b1f217b7b3f0957a2eaa9a12e8e41d4319bcfc6e
pytorch = cda5586f6a78ce874afec7b12c9a7cbdd6f9475a2c3e016db725f3984d0f4042
envelope = e38cc6ea055f7ee7b3f3f584f55e722e77ee3c0e8ec144b0a0e62f9e2af81fbe
artifact = 824a0a2c794a949a83e4bd650c9620464b96eb0d1dcb3d0fe4901a4e86d05f2c
```

The source files compute `source_sha256` from their own `SOURCE_PATH` at runtime (`mct_nonassoc_weld_packet_v0_jax.py:619-620`, `mct_nonassoc_weld_packet_v0_pytorch.py:506-507`, `mct_nonassoc_weld_packet_v0_julia.jl:430-431`, `mct_nonassoc_weld_packet_v0_envelope.py:136-137`).
fail-condition: Not triggered, with the working-tree caveat that the packet directory is currently untracked.
evidence-field: `build_card_sha256`, `source_sha256.*`, runtime `sha256_file/file_sha256`.
source-citation: `build_card.md:34-42`, `/tmp/weld2_pre_audit_checklist_20260610.md:185-195`.
result: PASS WITH HYGIENE CAVEAT.

### 13. Ceiling drift and acceptance-gate honesty

open: Validator/all-pass could overstate the packet.
recompute: Source constants and build card keep the ceiling at `scratch_diagnostic`, with promotion/formal admission false; kill conditions include density-only, order/bracketing conflation, G2 root-forced language, and primitive carrier admission. Validator status is treated as shape evidence only, not scientific proof.
fail-condition: Not triggered.
evidence-field: `CLASSIFICATION`, `PROMOTION_ALLOWED`, `FORMAL_ADMISSION_ALLOWED`, `kill_conditions`, `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`.
source-citation: `build_card.md:7`, `mct_nonassoc_weld_packet_v0_jax.py:32-34`, `mct_nonassoc_weld_packet_v0_jax.py:577-588`, `mct_nonassoc_weld_packet_v0_envelope.py:20-22`, `mct_nonassoc_weld_packet_v0_envelope.py:169-190`.
result: PASS.

## Named gaps

1. Explicit M(C,t) state fields are underinstrumented. The packet should emit a named object containing `Probe_t`, `equiv_t` or `~_t`, `Q_t`, `H_t`, `R_t`, `Var_t`, `Ctrl_t`, and `Rec_t`, instead of relying on row/result-surface equivalents.
2. The density lift is a minimal sign-projection witness. It is computed and valid for this diagnostic, but it is not a full three-spinor carrier action.
3. The packet folder is untracked in the current worktree. Any later use as evidence needs deliberate staging/commit hygiene and should not bulk-stage surrounding generated estate.
4. The checklist hard-read rule and the lane-card result-input line conflict. I did not use result JSON contents as evidence; the audit should preserve that no-result lookup discipline for fresh reruns.

## Final verdict

VERDICT: GENUINE-WITH-CAVEATS.

This is a genuine bounded weld packet as a scratch diagnostic. It is not decorative: the decisive arithmetic and controls recompute from the source-pinned table and independent solvers. It is not promotable: no carrier admission, no canonical M(C), no Axis0, no bridge, no physics, no G2 root-forced claim, and no tower integration follows from this packet.
