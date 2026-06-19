# Fresh Adversarial Audit v2: axis_independence_discriminators_036

Audit date: 2026-06-10

VERDICT: DECORATIVE for the claimed 0/3/6 carrier-independence evidence.

The packet is an executable three-engine scratch artifact and the validator passes, including `--require-pytorch --strict-source-backed`. That does not make the independence claim earned. Source review confirms the main off-diagonal holds are guaranteed by fixture isolation, Axis-0 is a family-keyed coefficient template rather than a recomputation from committed terrain/operator/MCT dynamics, several controls cannot fail, SMT proves derived class bits rather than raw observable values, PyTorch autograd is synthetic, and the Axis-4 boundary cell does not compute deductive-vs-inductive loop order.

Ceiling remains: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, `axis0_status=readout_only_no_closure`. Do not use this packet as Axis-0 closure, axis admission, formal admission, real Axis-4/Axis-6 separation, IGT evidence, or carrier-level independence evidence.

## Evidence Boundary

Sources read:

- `/tmp/axi_pre_audit_checklist_20260610.md`
- `/tmp/axi_blind_expected_20260610.md`
- `system_v6/receipts/axis_independence_mine_20260610.md`
- `system_v6/sims/axis_independence_discriminators_036/build_card.md`
- `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_jax.py`
- `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_julia.jl`
- `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_pytorch.py`
- `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_envelope.py`
- Source comparators from `terrain_generator_sheet_packet`, `terrain_operator_precedence_64_matrix`, `working_math_scaffold_20260609.md`, and the Axis-6 reference doc.

Process caveat: this fresh audit thread read the prior `audit_verdict.md` before recomputation; that file contained result-derived values. The recompute below was still done by source import without rewriting results, but the "blind before any prior value exposure" condition is not perfectly clean. I did not use `results/*.json` as evidence for the manual source recomputation.

Fresh commands/checks:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3` was used, matching the Makefile alias (`Makefile:3-5`).
- Source import recomputed JAX diagonal cells, one off-diagonal hold, controls, z3, and cvc5 without calling `main()`.
- Source import recomputed the PyTorch class matrix and `torch.func.jacfwd` sensitivity.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/axis_independence_discriminators_036/results/axis_independence_discriminators_036_envelope_results.json` returned `ok:true`.
- Same validator with `--require-pytorch --strict-source-backed` returned `ok:true`.
- `git status --short -- system_v6/sims/axis_independence_discriminators_036` returned `?? system_v6/sims/axis_independence_discriminators_036/`; the packet directory is untracked in this checkout.

Pinned engine PIN hash:

`27372fb4661e43b53278c91f19b6e8bae484f3f058fbb23a7763d6c2793301b2`

The leg class tolerance is `TOL = 1.0e-8` in JAX/PyTorch/Julia (`axis_independence_discriminators_036_jax.py:38-42`, `axis_independence_discriminators_036_pytorch.py:30-33`, `axis_independence_discriminators_036_julia.jl:23-27`). The envelope comparator uses `TOL = 1.0e-6` for cross-engine scalar divergence (`axis_independence_discriminators_036_envelope.py:27`), so the checklist's "byte-identical across envelope" tolerance demand is not clean, although the per-cell criteria are leg-local.

## Manual Recompute Packet

Source-import recompute values:

| Cell | Recomputed values | Class result |
|---|---|---|
| `(axis0,O0)` | `Ne +0.7290954471054203 -> Se -0.07558159209734905` | moved |
| `(axis3,O3)` | `fiber 2.455493422156577e-16 -> base 0.7071067811865476` | moved |
| `(axis6,O6)` | `operator_first +0.08151115599412681 -> terrain_first -0.08151115599412681` | moved |
| `(axis0,O3)` | `fiber 2.455493422156577e-16 -> fiber 2.455493422156577e-16` | held |

SMT flip recompute:

- z3: positive `unsat`, erased `sat`.
- cvc5: positive `unsat`, erased `sat`.
- Encoded row values: `diag_move=1`, `offdiag_o0_move=0`, `offdiag_o3_move=0`.

The recompute matches the overseer numerical values. It also exposes why those values are weak evidence: the source functions are field-disjoint.

## Checklist Results

1. Insensitive-observable theater: FAIL IN SUBSTANCE. Each held observable has a diagonal mover somewhere else, but each observable reads only its own axis field. The off-diagonal holds therefore test fixture wiring, not carrier-coupled independence.

2. Post-hoc tolerance: PASS WITH CAVEAT. The leg tolerance and class criteria are source-pinned before result assembly. Caveat: envelope tolerance differs (`1e-6` vs leg `1e-8`).

3. Label echo in Axis 0: FAIL. The class uses PPR arithmetic, but the coefficients are keyed by family labels and are not recomputed from committed terrain/operator/MCT dynamics.

4. Axis-4 / Axis-6 merge: FAIL. Axis 6 has a real local precedence gap; the alleged Axis-4 boundary uses inner/base density movement, not a deductive-vs-inductive loop-order computation.

5. Vary-operation contamination: PASS FORMALLY, FAIL AS INDEPENDENCE EVIDENCE. `state_for()` changes exactly one dictionary field, but that same isolation guarantees off-axis holds because held observables ignore the changed field.

6. `b6=-b0*b3` smuggling: PASS. Search found `b6` only in fences/prohibitions/envelope checks, not as the Axis-6 computation.

7. Decorative SMT: FAIL AS CLAIM-BEARING PROOF. The solvers are real and independently constructed, but they bind class-movement integers, not raw computed observable values.

8. Control circularity: FAIL. Sheet erasure checks `x-x`; loop and precedence erasures hardcode post-erasure zeros; the commuting control is a same-operation commuting path.

9. Runtime, parity, fence drift: PASS FOR SHAPE/CEILING. The three legs and envelope validate, `reads_peer_result=false` is recorded on legs, and ceiling/fence language stays bounded. This does not overcome H1-H7.

## H1-H7 Adjudication

H1. FIXTURE ISOLATION: TRUE.

Quoted source:

```python
base = {"axis0_family": "Ne", "axis3_placement": "fiber", "axis6_precedence": "operator_first"}
...
if observable == "O0":
    return ppr_response(state["axis0_family"])
if observable == "O3":
    return loop_density_delta(state["axis3_placement"])
if observable == "O6":
    return precedence_gap(state["axis6_precedence"])
```

Cites: `axis_independence_discriminators_036_jax.py:203-223`; same pattern in PyTorch `:194-214` and Julia `:155-173`.

Decision: `O0` reads only `axis0_family`; `O3` reads only `axis3_placement`; `O6` reads only `axis6_precedence`. The off-diagonal holds are guaranteed by construction when the varied field is not the observed field. This is not shared-carrier/dynamics-state evidence.

H2. AXIS-0 LABEL ECHO: TRUE.

Quoted source:

```python
finals = {
    "Ne": [1.0, 0.52, 0.38],
    "Ni": [1.0, 0.48, 0.36],
    "Se": [1.0, 0.10, 0.05],
    "Si": [1.0, 0.08, 0.04],
}
return jnp.asarray(finals[family], dtype=jnp.float64)
```

Cites: `axis_independence_discriminators_036_jax.py:116-125`; PyTorch `:107-116`; Julia `:70-78`.

Decision: the emitted Axis-0 numbers are computed from family-keyed coefficient templates, not from `delta_rho` evolved through committed terrain generators as in the terrain packet. The committed terrain packet computes `delta0`, applies `generator_fn(...)`, evolves via `channel_from_generator_at`, and then derives PPR from `delta_t` (`terrain_generator_sheet_packet_jax.py:537-616`). This packet does not do that.

Blind diff: blind expected grouped PPR response was `Ne ~= +0.08037043685314521` and `Se ~= -0.0018131249410586747`; this packet emits `Ne = +0.7290954471054203` and `Se = -0.07558159209734905`. That is about `9.07x` and `41.69x` off. No source pin in this packet explains the scale shift. The Axis-0 sign split is label-template arithmetic, not committed-form recomputation.

H3. WEAK SHUFFLE: TRUE.

Quoted source:

```python
normal_classes = [(cell["cell"], cell["class_verdict"], cell["pass"]) for cell in matrix]
shuffled_classes = [(cell["cell"], cell["class_verdict"], cell["pass"]) for cell in list(reversed(matrix))]
...
"label_shuffle": {
    "pass": sorted(normal_classes) == sorted(shuffled_classes),
    "class_verdicts_invariant": True,
}
```

Cites: `axis_independence_discriminators_036_jax.py:283-297`; PyTorch `:298-309`; Julia uses sorted/reversed class tuples at `:232-243`.

Decision: this reverses/sorts class records. It does not relabel families and recompute Axis-0 classes. It cannot catch H2.

H4. TAUTOLOGICAL ERASURE CONTROLS: TRUE.

Quoted source:

```python
"pass": abs(sheet_erased - sheet_erased) <= TOL
...
"axis3_loop_erasure": {"pass": True, ..., "post_erasure": {"fiber": 0.0, "base": 0.0}}
...
"axis6_precedence_erasure": {"pass": True, ..., "post_erasure": {"operator_first": 0.0, "terrain_first": 0.0}}
```

Cites: `axis_independence_discriminators_036_jax.py:298-319`; PyTorch `:310-328`; Julia `:244-260`.

Control classification:

- `commuting_control`: can fail numerically, but it uses `terrain_commuting = dephase_z` against `dephase_z`, so it is not the distinct commuting pair requested by the checklist (`axis_independence_discriminators_036_jax.py:177-199`, `:289-292`).
- `label_shuffle`: cannot catch label echo; it only reorders class tuples.
- `axis0_sheet_erasure`: cannot fail as written because it checks `sheet_erased - sheet_erased`.
- `axis3_loop_erasure`: cannot fail as written because `pass=True` and zeros are assigned.
- `axis6_precedence_erasure`: cannot fail as written because `pass=True` and zeros are assigned.

H5. DERIVED-BOOLEAN SMT: TRUE.

Quoted source:

```python
diag = 1 if row["O6"]["class_verdict"] == "moved" else 0
off0 = 1 if row["O0"]["class_verdict"] == "moved" else 0
off3 = 1 if row["O3"]["class_verdict"] == "moved" else 0
...
solver.add(d == diag, o0 == off0, o3 == off3)
```

Cites: z3 `axis_independence_discriminators_036_jax.py:323-345`; cvc5 `:349-384`; Julia Z3 `axis_independence_discriminators_036_julia.jl:266-291`.

Decision: `no_hardcoded_literals=true` is overstated. The solvers receive derived movement bits/integers, not raw PPR/density/gap values or scaled computed observable values. They prove a summary row, not the math.

H6. SYNTHETIC `torch.func`: TRUE.

Quoted source:

```python
scales = torch.tensor([ppr_scale, density_scale, prec_scale], dtype=RDTYPE, device=DEVICE)
return coords * scales
...
jac = jacfwd(sensitivity_vector)(coords)
```

Cites: `axis_independence_discriminators_036_pytorch.py:251-274`.

Decision: the Jacobian is diagonal because the function is constructed as elementwise `coords * scales`. It carries no independent information about the carrier, coupled observables, or actual vary/hold dynamics.

H7. AXIS-4/6 BOUNDARY ASSERTED: TRUE.

Quoted source:

```python
inner = loop_density_delta("fiber")
outer = loop_density_delta("base")
axis6 = precedence_gap("operator_first")
```

Cites: `axis_independence_discriminators_036_jax.py:262-280`; PyTorch `:277-295`; Julia `:211-230`.

Decision: the source does not compute Axis-4 deductive-vs-inductive loop order (`Phi_D` vs `Phi_I`). It reuses Axis-3-style fiber/base density visibility for the alleged Axis-4 side and a separate Axis-6 precedence gap. The source law requires Axis 4 order class and Axis 6 action-side/precedence to stay separate (`working_math_scaffold_20260609.md:303-309`; Axis-6 witness in `apple axes terrain operator math.md:1012-1020,1074-1078`). This cell establishes only "density loop readout plus precedence gap", not a real Axis-4 boundary.

## F1-F2 Adjudication

F1. Axis-6 gap echo risk: PARTIAL.

Quoted source:

```python
op_first = terrain(dephase_z(rho))
terrain_first = dephase_z(terrain(rho))
gap_matrix = op_first - terrain_first
gap = fro_norm(gap_matrix)
```

Cites: `axis_independence_discriminators_036_jax.py:181-200`.

Decision: the gap is recomputed through this packet's local source path, not read directly from the `terrain_operator_precedence_64_matrix` result JSON. However, it is a simplified local reimplementation using `terrain_ne()` and `dephase_z()`, while the stronger matrix64 source path imports source-locked terrain/operator packet code and computes `plus_out`, `minus_out`, and `delta` from the 64-cell machinery (`terrain_operator_precedence_64_matrix_jax.py:247-268`). So F1 is not a JSON echo, but it is not an independent source-locked matrix64-path recomputation either.

F2. Positive-sensitivity requirement: FORM PASS, SUBSTANCE FAIL.

The packet does show each held observable moving in its own diagonal cell:

- `O0`: `+0.7290954471054203 -> -0.07558159209734905`.
- `O3`: `2.455493422156577e-16 -> 0.7071067811865476`.
- `O6`: `+0.08151115599412681 -> -0.08151115599412681`.

But because of H1, this only proves each isolated observable can move when its own field changes. It does not prove an off-axis variation was recomputed through a shared carrier where movement was possible and then held.

## Required Gaps

Hardening-ready gaps:

1. Carrier-coupled observables: replace field-disjoint `observe(state, observable)` with observables computed from one shared carrier/dynamics state containing family, placement, precedence, terrain, operator, rho, and evolved intermediates.
2. Recomputed Axis-0 classes: compute Axis-0 by evolving `delta_rho` through committed terrain generator forms, matching the terrain packet path, not `finals[family]` coefficient templates.
3. Relabel-and-recompute shuffle: permute family labels while holding computed dynamics fixed, then recompute classes from the functional.
4. Can-fail erasure controls: remove `x-x`, `pass=True`, and hardcoded post-erasure zeros. Recompute erased channels/loops/preference maps and compare to non-erased positives.
5. Raw-value SMT: bind raw or scaled computed PPR/density/gap values, not `moved/not_moved` integers.
6. Honest PyTorch role: either compute a meaningful torch-side carrier sensitivity or demote `torch.func` to decorative/supportive.
7. Real Axis-4 loop-order cell: compute deductive-vs-inductive `Phi_D` vs `Phi_I` with Axis 6 held, separately from fiber/base density visibility and operator-first/terrain-first precedence.

## Final Boundary

This artifact exists, executes, records three engine legs, passes the strict source-backed validator, and stays inside the declared `scratch_diagnostic` ceiling. Those are real engineering facts.

The independence claim is not earned. The strongest honest status is: executable three-engine scratch artifact; strict validator passes; independence claim not earned without hardening. The current independence evidence is weak to decorative because the matrix mostly proves fixture isolation rather than carrier-coupled independence.

---

# v2 Rebuild Audit: axis_independence_discriminators_036

Audit date: 2026-06-10

VERDICT for v2: GENUINE-WITH-CAVEATS.

The v2 rebuild is not a renamed copy of the v1 decorative packet: Axis-0 now recomputes the committed terrain PPR response, the blind-scale match is generated through source paths, Axis-4 now computes a real `Phi_D`/`Phi_I` order cell, PyTorch's `torch.func` lane is no longer the old `coords * scales` synthetic vector, and the packet passes all local validator shapes, including `--require-pytorch --strict-source-backed`.

The caveats are material. H1 is only partially repaired because the shared-state envelope is real but `O3` is still a placement-only density readout and `O0` uses an inert trace coupling around an imported family response. H4 is not fully closed because the Axis-0 erasure still constructs a common response and compares it to itself. H5 binds raw values, but its positive contradiction requires every row to violate raw diagonal dominance simultaneously; a stricter any-row violation check is `sat` because the Axis-0 raw off-diagonal `O6` drift exceeds the Axis-0 diagonal delta. Independence-evidence strength: medium for class-level 3x3 discriminator behavior under the named pins; weak for raw diagonal-dominance and fully hardened control claims.

Ceiling remains: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, `axis0_status=readout_only_no_closure`. No promotion, no axis admission, no Axis-0 closure, Axis-0 readout-only, Axis-4 distinct from Axis-6, no IGT.

## Evidence Boundary

Sources read for this v2 audit:

- `/tmp/axi_blind_expected_20260610.md`
- `/tmp/axi_pre_audit_checklist_20260610.md`
- `system_v6/sims/axis_independence_discriminators_036/build_card.md`
- `system_v6/sims/axis_independence_discriminators_036/audit_verdict.md`
- `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_jax.py`
- `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_pytorch.py`
- `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_julia.jl`
- `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_envelope.py`
- Imported reference paths named by the packet: `terrain_generator_sheet_packet`, `source_locked_operator_base_packet`, `terrain_operator_precedence_64_matrix`, and `working_math_scaffold_20260609.md`.

Fresh read-only checks:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/axis_independence_discriminators_036/results/axis_independence_discriminators_036_envelope_results.json` -> `ok:true`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/axis_independence_discriminators_036/results/axis_independence_discriminators_036_envelope_results.json` -> `ok:true`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/axis_independence_discriminators_036/results/axis_independence_discriminators_036_envelope_results.json` -> `ok:true`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/axis_independence_discriminators_036/results/axis_independence_discriminators_036_envelope_results.json` -> `ok:true`.

No leg `main()` was rerun in this audit because that would rewrite `results/*.json`; source-import recomputations below were read-only.

## H1-H7 Re-Adjudication

### H1 fixture isolation: NAMED GAP H1a

The v2 source now builds one shared state object and recomputes hashes/intermediates:

```python
def build_shared_state(polarities: dict[str, str]) -> dict[str, Any]:
    spec = terrain_spec_for(polarities)
    channel = terrain_channel(spec)
    rho = OP_SRC.pinned_states()["rho_1"]
    precedence = precedence_record(polarities, spec, channel, rho)
    packet = axis0_packet_response()
    axis0 = axis0_family_response(polarities["axis0_family"], precedence["selected_out"], packet)
    axis3 = loop_density_delta(polarities["axis3_placement"])
    axis4 = axis4_order_record(polarities, spec, channel, rho)
```

Source: `axis_independence_discriminators_036_jax.py:339-347`.

The shared-state rebuild is genuine for `O6` and for the state receipts. It is weaker for `O0` and `O3`: `O0` multiplies an imported family-group response by `trace(selected_out)`, which is effectively trace-preserving/inert in the audited rows; `O3` still accepts only `placement` and computes the loop density formula independently of the shared `rho`, terrain channel, and precedence. Therefore the v1 "field-disjoint fixture" failure is not simply present unchanged, but it is not fully gone.

Named gap H1a: `O3` remains placement-only and `O0` is only weakly coupled to the shared carrier through an inert trace factor. This supports class-level discriminator evidence, not full shared-evolved-carrier independence.

### H2 label echo: CLOSED

The old `finals[family]` template is gone from the claim path. JAX imports the committed terrain packet and reads its computed PPR group response:

```python
def axis0_packet_response() -> dict[str, Any]:
    return TERRAIN_SRC.axis0_response()

def axis0_family_response(family: str, selected_out: Any, packet: dict[str, Any]) -> dict[str, Any]:
    raw = float(packet["groups"][family]["responses"]["pauli_participation_ratio"])
    trace_factor = real_float(jnp.trace(selected_out))
    response = raw * trace_factor
```

Source: `axis_independence_discriminators_036_jax.py:249-256`.

The imported committed terrain path computes `delta0`, evolves it through `channel_from_generator_at`, and derives response values from the PPR functional:

```python
delta0 = axis0_delta_rho()
initial = pauli_diversity_metrics(delta0)
...
channel = channel_from_generator_at(gen, time_value)
delta_t = apply_channel_linear(channel, delta0)
series.append({"time": time_value, **pauli_diversity_metrics(delta_t)})
...
"responses": {functional: final[functional] - initial[functional] for functional in functionals}
```

Source: `terrain_generator_sheet_packet_jax.py:543-560`.

Manual source-import recompute through the committed terrain generator forms:

| family | members | recomputed grouped PPR response |
|---|---|---:|
| `Ne` | `Vortex:pure_hamiltonian`, `Spiral:pure_hamiltonian`, `Vortex:weak_dissipator`, `Spiral:weak_dissipator` | `+0.08037043685314521` |
| `Se` | `Funnel`, `Cannon` | `-0.0018131249410586747` |

Member values in the recompute:

- `Ne`: `-0.3861392234190144`, `+0.577657636162894`, `-0.3835008616145925`, `+0.5134641962832938`.
- `Se`: `-0.29593700321761673`, `+0.2923107533354994`.

This closes the v1 label echo for the audited `Ne`/`Se` diagonal. The result class is not assigned directly from the visible family label.

### H3 relabel shuffle: CLOSED

The relabel control now holds computed values and flips visible labels both ways:

```python
shuffle = {"Ne": "Se", "Se": "Ne"}
...
"dynamic_family_whose_computed_values_are_held": dynamic_family,
"shuffled_visible_label": shuffled_label,
"raw_computed_ppr_response": response,
"computed_class_after_recompute": computed_class,
"label_derived_class_after_shuffle": label_class[shuffled_label],
"label_derived_survives": label_class[shuffled_label] == computed_class,
"computed_class_survives": computed_class == label_class[dynamic_family],
```

Source: `axis_independence_discriminators_036_jax.py:511-529`.

Fresh source-import recompute returned both directions:

- `Ne` values under visible `Se`: computed class survived as `allostatic_positive_feedback`; label-derived class broke.
- `Se` values under visible `Ne`: computed class survived as `homeostatic_negative_feedback`; label-derived class broke.

This closes the v1 "reverse/sort class tuple" shuffle failure.

### H4 erasure controls: NAMED GAP H4a

Axis-3 and Axis-6 erasures are materially better than v1:

```python
fiber_erased = loop_density_delta("fiber", erased=True)
base_erased = loop_density_delta("base", erased=True)
axis3_erased_gap = abs(base_erased["density_delta_fro"] - fiber_erased["density_delta_fro"])
...
merged_operator_first = 0.5 * (plus_out + minus_out)
merged_terrain_first = 0.5 * (minus_out + plus_out)
axis6_erased_gap = trace_norm(merged_operator_first - merged_terrain_first)
```

Source: `axis_independence_discriminators_036_jax.py:565-587`.

Fresh recompute:

- Axis-3 positive gap `0.7071067811865474`, erased gap `0.0`.
- Axis-6 positive gap `0.11527418229160312`, erased gap `0.0`, plus/minus distinct before erasure.
- Commuting distinct-pair control: `Si/Hill` with `Ti`, gap `9.813077866773595e-18`.

But Axis-0 erasure is still structurally tautological:

```python
erased_family_common = (ne + se) / 2.0
axis0_erased_gap = abs(erased_family_common - erased_family_common)
axis0_positive_gap = abs(ne - se)
```

Source: `axis_independence_discriminators_036_jax.py:557-563`.

Named gap H4a: Axis-0 erasure is still common-minus-itself. It reports a positive pre-erasure gap `0.08218356179420389` and an erased gap `0.0`, but the erased side is constructed equal by definition rather than recomputed as two independently erased family/channel outputs. H4 is not fully closed.

### H5 raw-value SMT: NAMED GAP H5a

The v2 solver path is no longer the v1 derived-boolean SMT. It binds scaled raw deltas and raw values:

```python
diag_value = scaled(row["diag_delta"])
off_values = [scaled(value) for value in row["offdiag_deltas"].values()]
solver.add(diag == diag_value)
for var, value in zip(off_vars, off_values, strict=True):
    solver.add(var == value)
solver.add(z3.Or(diag <= 0, *[diag <= var for var in off_vars]))
```

Source: `axis_independence_discriminators_036_jax.py:662-674`.

Fresh JAX recompute:

- z3 positive verdict `unsat`; erased verdict `sat`.
- cvc5 positive verdict `unsat`; erased verdict `sat`.
- Axis-6 erased scaled value `0`.

However, the positive proof asserts a violation formula for every axis row in the same solver. A stricter "any row violates raw diagonal dominance" check is `sat`:

| row | diagonal delta scaled | off-diagonal scaled | raw dominance status |
|---|---:|---:|---|
| `axis0` | `821836` | `O3=0`, `O6=947088` | violation: `diag <= O6` is true |
| `axis3` | `7071068` | `O0=0`, `O6=106667` | no violation |
| `axis6` | `2305484` | `O0=0`, `O3=0` | no violation |

Named gap H5a: raw values are bound, but the SMT contradiction does not prove that every row satisfies raw diagonal dominance. It proves that not all rows violate simultaneously. The class-level 3x3 still passes; the raw-value SMT claim is overstated.

### H6 `torch.func`: CLOSED WITH CAVEAT

The old synthetic `coords * scales` pattern is gone. PyTorch now runs `jacrev` through a torch-native function that recomputes the Axis-0 family response, loop-density readout, and source-locked precedence gap:

```python
def torch_carrier_readouts(coords: torch.Tensor) -> torch.Tensor:
    axis0_coord, placement_coord, precedence_coord = coords[0], coords[1], coords[2]
    ne = axis0_family_response_tensor("Ne")
    se = axis0_family_response_tensor("Se")
    axis0 = (1.0 - axis0_coord) * ne + axis0_coord * se
    axis3 = loop_density_delta_tensor(placement_coord)
    ...
    plus_out = TERRAIN_SRC.apply_channel(channel, op_mid)
    minus_out = OP_SRC.source_channel("Ti", terrain_mid)
    gap = trace_norm_tensor(plus_out - minus_out)
    axis6 = (1.0 - 2.0 * precedence_coord) * gap
    return torch.stack([axis0.real, axis3.real, axis6.real])

def autograd_sensitivity() -> dict[str, Any]:
    coords = torch.tensor([0.5, 0.5, 0.25], dtype=RDTYPE)
    jac = jacrev(torch_carrier_readouts)(coords)
```

Source: `axis_independence_discriminators_036_pytorch.py:370-390`.

Fresh recompute:

- Jacobian diagonal abs: `[0.08218356179420483, 0.7256132880348577, 0.23054836458320604]`.
- Off-diagonal max abs: `0.0`.
- `through_torch_native_recomputation=true`, `not_coords_times_scales=true`, role `claim_bearing_torch_func_carrier_sensitivity`.

Caveat: the PyTorch sensitivity is a local continuous-coordinate probe over the selected readout parameterization, not a stronger proof of full carrier-coupled independence. It earns the specific v2 role label, not promotion.

### H7 Axis-4 / Axis-6 boundary: CLOSED

The v2 source now computes the requested Axis-4 `Phi_D`/`Phi_I` cell instead of reusing fiber/base density movement:

```python
phi_d = apply_u(channel, apply_e(apply_u(channel, apply_e(rho))))
phi_i = apply_e(apply_u(channel, apply_e(apply_u(channel, rho))))
gap = trace_norm(phi_d - phi_i)
signed = gap if polarities["axis4_loop_order"] == "deductive" else -gap
```

Source: `axis_independence_discriminators_036_jax.py:317-321`.

The boundary check varies Axis-4 loop order with Axis-6 held, and separately varies Axis-6 precedence while checking Axis-4 hold:

```python
loop_varied_pol["axis4_loop_order"] = "inductive"
...
precedence_varied_pol["axis6_precedence"] = "terrain_first"
...
loop_moves = base["axis4"]["class"] != loop_varied["axis4"]["class"] and base["axis4"]["absolute_gap"] > TOL
precedence_holds = base["axis4"]["class"] == precedence_varied["axis4"]["class"]
```

Source: `axis_independence_discriminators_036_jax.py:460-469`.

Fresh recompute:

- Axis-4 order gap trace `0.14204848183630314`.
- Axis-4 base class `deductive_D`; varied class `inductive_I`.
- Axis-4 holds under Axis-6 precedence variation.
- Axis-6 before/after in the same boundary check: `+0.11527418229160312` to `-0.11527418229160312`.

This closes the v1 Axis-4/Axis-6 merge finding for the audited source path.

## N1 Blind-Match Integrity

N1 is CLOSED.

The source contains blind expected constants for comparison, but the audited values are not transcribed into the computed side. The computed side calls the imported committed terrain packet:

```python
packet = axis0_packet_response()
...
dummy_state = build_shared_state({**BASE_POLARITIES, "axis0_family": family})
got = observe(dummy_state, "O0")["response_value"]
...
"abs_diff": abs(got - expected),
```

Source: `axis_independence_discriminators_036_jax.py:491-503`.

Independent hand recomputation through `terrain_generator_sheet_packet_jax.py` produced:

- `Ne`: `+0.08037043685314521`.
- `Se`: `-0.0018131249410586747`.

JAX source-import diff was exactly `0.0` against the comparison constants. The committed result set records cross-engine machine-epsilon differences: Julia `blind_ne_abs_diff=5.551115123125783e-16`, `blind_se_abs_diff=1.1102230246251565e-16`; PyTorch `4.996003610813204e-16` and `4.436555289810684e-16`. These are computed comparisons, not copied result values.

## N2 Vary-Purity

N2 is CLOSED for the JAX/envelope receipt path.

The source emits before/after polarity diffs plus derived recomputation hashes:

```python
"vary_purity_state_diff": state_diff(base_state, varied_state),
...
"polarity_input_diff": polarity_changes,
"changed_polarity_count": len(polarity_changes),
"changed_only_requested_polarity": len(polarity_changes) == 1,
"derived_recomputed_diff": derived_changes,
```

Source: `axis_independence_discriminators_036_jax.py:445` and `388-418`.

Fresh examples:

- `(axis0,O0)`: only `axis0_family` changed `Ne -> Se`; terrain/channel/output hashes also recomputed.
- `(axis3,O3)`: only `axis3_placement` changed `fiber -> base`; terrain/channel/output hashes also recomputed.
- `(axis6,O6)`: only `axis6_precedence` changed `operator_first -> terrain_first`; selected/counterfactual output hashes swapped while terrain hash stayed fixed.

This is genuine before/after state-diff evidence, not just a label list.

## Manual Recompute Packet

Manual recomputations used source imports and did not read `results/*.json` for the values below.

Diagonal cells:

| cell | base | varied | raw delta | class |
|---|---:|---:|---:|---|
| `(axis0,O0)` | `+0.08037043685314521` | `-0.0018131249410586747` | `0.08218356179420389` | moved |
| `(axis3,O3)` | `2.455493422156577e-16` | `0.7071067811865476` | `0.7071067811865474` | moved |
| `(axis6,O6)` | `+0.11527418229160312` | `-0.11527418229160312` | `0.23054836458320624` | moved |

One off-diagonal hold:

| cell | base | varied | raw delta | base class | varied class | class verdict |
|---|---:|---:|---:|---|---|---|
| `(axis0,O6)` | `+0.11527418229160312` | `+0.02056542129344229` | `0.09470876099816083` | `operator_first_UP` | `operator_first_UP` | not_moved |

This off-diagonal row is important: class hold is real, but raw drift is larger than the Axis-0 diagonal raw delta, which is why H5a is named.

SMT flip rerun:

- z3 source proof: positive `unsat`, erased `sat`.
- cvc5 source proof: positive `unsat`, erased `sat`.
- stricter audit-side any-row raw-dominance violation check: `sat`, with Axis-0 `diag=821836`, `O6 offdiag=947088`.

## Final Boundary

The v2 packet is a real improvement over v1 and should not be collapsed back to the old decorative verdict. The strongest honest status is:

`Genuine-with-caveats scratch diagnostic: source-backed class-level 3x3 independence discriminator under named pins; not raw diagonal-dominance proof; not fully can-fail-erasure-hardened; not axis admission.`

Do not promote it beyond `scratch_diagnostic`. Do not cite it for Axis-0 closure, axis-level admission, formal admission, IGT, or an unrestricted carrier-independence theorem.

# v3 Hardening Note: axis_independence_discriminators_036

Audit note date: 2026-06-10.

Scope: bounded hardening pass to close the v2 caveat handling without changing the v2 class-level claim values. Fresh rerun regenerated all three leg results and the envelope.

## V1 / H4a Axis-0 Erasure

The Axis-0 erasure control no longer constructs a common response and subtracts it from itself. It reruns two independent erased-H family/channel paths and emits both sides:

| side | erased-H grouped PPR response |
|---|---:|
| `Ne` | `-0.38482004251680346` |
| `Se` | `-0.29593700321761673` |

Pre-erasure positive gap remains `0.08218356179420389`. Erased-H recompute gap is `0.08888303929918673`. Honest outcome: the tautology is removed; raw erasure collapse is not claimed.

## V2 / H1 O0 and O3 Scope

The v2 values are byte-stable. Because strengthening `O0` or `O3` through a non-inert shared evolved state would change the accepted v2 scalar values in this bounded pass, the results now emit explicit scope fields:

- `o0_scope`: committed terrain family PPR response multiplied by `trace(selected_out)`; trace is preserved in the audited rows, so this is an honest scoped readout rather than a strengthened non-inert shared-state coupling.
- `o3_scope`: placement density-loop readout; value is byte-stable with v2 and does not consume the terrain/operator evolved `rho` beyond shared-state receipt hashes in this bounded pass.

## V3 / H5 Raw Dominance

The any-row raw-dominance check is a separate labeled receipt: `H5_any_row_raw_dominance_check`. Fresh outcome is `sat`, with witness row `axis0`: `diag=821836`, `O3=0`, `O6=947088`. This means raw diagonal dominance is violated by the Axis-0 row and is not claimed.

The class-level 3x3 result is unchanged: `matrix_cell_count=9`, `diagonal_move_count=3`, `offdiagonal_hold_count=6`. The blind Axis-0 responses remain `Ne=0.08037043685314521` and `Se=-0.0018131249410586747`; Axis-3 base/fiber and Axis-6 gap values remain the v2 values.

Validation after this append and envelope refresh:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/axis_independence_discriminators_036/results/axis_independence_discriminators_036_envelope_results.json` -> `ok:true`.

Final boundary: class-level independence under the named pins, medium strength; raw dominance is not claimed; `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, `axis0_status=readout_only_no_closure`.
