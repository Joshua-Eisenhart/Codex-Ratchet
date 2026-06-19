# Fresh Audit: bloch_root_admissibility_discriminator_v0

Audit date: 2026-06-10

VERDICT: GENUINE-WITH-CAVEATS.

The packet is a genuine executable three-engine scratch diagnostic for the bounded claim on F01/N01 reconstruction and the R/C/H/O Hopf ladder with sedenion termination. It is not decorative in the R3 sense: the main values are recomputed from source, controls can fail, SMT binds computed numeric witnesses rather than only booleans, PyTorch performs torch-native rank/SVD/Jacobian checks, and the ceiling language is correctly fenced.

The caveat is load-bearing: B1's exact blind-sheet sedenion witness is not reproduced by this packet's table. The packet genuinely Cayley-Dickson-doubles the imported octonion artifact and finds a zero divisor, but the pre-registered blind witness `(e3+e10)(e6-e15)=0` recomputes here as nonzero. This blocks a clean `GENUINE` verdict until the packet either records the table-orientation mismatch or includes the blind witness under the intended convention.

Ceiling remains: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Allowed language is only: the roots admit the four-member family `{S^1,S^2,S^4,S^8}`; the `C^2` carrier installs `S^2`; no carrier admission, no formal admission, no physics, no primitive Bloch sphere under F01.

## Evidence Boundary

Read:

- `/tmp/bloch_adm_blind_expected_20260610.md`
- `system_v6/sims/axis_independence_discriminators_036/audit_verdict.md`
- `system_v6/sims/bloch_root_admissibility_discriminator_v0/build_card.md`
- `system_v6/sims/bloch_root_admissibility_discriminator_v0/bloch_root_admissibility_discriminator_v0_jax.py`
- `system_v6/sims/bloch_root_admissibility_discriminator_v0/bloch_root_admissibility_discriminator_v0_julia.jl`
- `system_v6/sims/bloch_root_admissibility_discriminator_v0/bloch_root_admissibility_discriminator_v0_pytorch.py`
- `system_v6/sims/bloch_root_admissibility_discriminator_v0/bloch_root_admissibility_discriminator_v0_envelope.py`
- `system_v6/sims/bloch_root_admissibility_discriminator_v0/results/*.json`

Fresh commands/checks:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/bloch_root_admissibility_discriminator_v0/results/bloch_root_admissibility_discriminator_v0_envelope_results.json` returned `ok:true`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/bloch_root_admissibility_discriminator_v0/results/bloch_root_admissibility_discriminator_v0_envelope_results.json` returned `ok:true`.
- Source-import recomputation from the JAX leg, without calling `main()`, recomputed the T1 curve, T2 dimensions, T3 dimensions/fibers, T4 products, T5 associator count, and an octonion fiber spot check.
- `rg -n "import numpy|from numpy|np\\." system_v6/sims/bloch_root_admissibility_discriminator_v0/*.py system_v6/sims/bloch_root_admissibility_discriminator_v0/*.jl` found no NumPy import or `np.*` source leakage.

The packet directory is currently untracked in this checkout: `git status --short -- system_v6/sims/bloch_root_admissibility_discriminator_v0` returns `?? system_v6/sims/bloch_root_admissibility_discriminator_v0/`.

## Hand Recomputation

Using the packet's JAX source functions and current imported octonion artifact:

| Check | Recomputed value | Decision |
|---|---:|---|
| T1 refined Hausdorff curve | `[0.91680271338944, 0.6296899779361548, 0.48979795188685626, 0.331218945973823]` | converges on sample |
| T1 non-refining control | `[0.91680271338944, 0.91680271338944, 0.91680271338944, 0.91680271338944]` | plateaus |
| T2 affine dims | `[1, 3]` | matches blind expectation |
| T3 base/fiber dims | `[[1, 2, 4, 8], [0, 1, 3, 7]]` | matches blind expectation |
| Packet sedenion witness `(e1+e10)(e4+e13)`, unit-normalized | product terms `[]`, product norm `0.0` | zero divisor reproduced |
| Blind sedenion witness `(e3+e10)(e6-e15)`, unnormalized | product terms `[(5, 1.0), (7, -1.0), (12, 1.0), (14, 1.0)]`, product norm `2.0` | B1 exact witness mismatch |
| Octonion associator `[e1,e2,e4]` | terms `[(5, -2.0)]`, norm `2.0` | nonassociating witness present |
| T5 count | nonzero/zero `[168, 42]` | matches blind expectation |
| Non-quaternionic octonion fiber spot check | `q` support `[1,2,4]`, not contained in a Fano line; deviation `4.577566798522237e-16` | B2 passes |

## Tripwire Results

### B1. Sedenion Table Provenance

Decision: PARTIAL PASS, EXACT-WITNESS FAIL.

The packet genuinely computes the sedenion table in-packet from the octonion table. JAX source:

```python
def cd_double(parent: Any) -> Any:
    parent = jnp.asarray(parent, dtype=jnp.float64)
    n = int(parent.shape[0])
    dim = 2 * n
...
    first = parent_mul(a, c) - parent_mul(parent_conj(d), b)
    second = parent_mul(d, a) + parent_mul(b, parent_conj(c))
```

Cites: `bloch_root_admissibility_discriminator_v0_jax.py:226-250`. Julia and PyTorch use the same Cayley-Dickson formula at `bloch_root_admissibility_discriminator_v0_julia.jl:78-91` and `bloch_root_admissibility_discriminator_v0_pytorch.py:122-142`.

The packet then builds `table_s = cd_double(table_o)` and records an explicit zero divisor:

```python
u = vector_from_terms(16, [(1, 1.0 / math.sqrt(2.0)), (10, 1.0 / math.sqrt(2.0))])
v = vector_from_terms(16, [(4, 1.0 / math.sqrt(2.0)), (13, 1.0 / math.sqrt(2.0))])
uv = multiply(table_s, u, v)
```

Cites: `bloch_root_admissibility_discriminator_v0_jax.py:495-515`; same terms in Julia `:184-195` and PyTorch `:219-231`.

However, the blind sheet's exact witness is:

```text
(e3 + e10)(e6 - e15) = 0.
```

Cites: `/tmp/bloch_adm_blind_expected_20260610.md:122-135`.

Fresh recomputation against this packet's doubled table produced product terms `e5 - e7 + e12 + e14`, norm `2.0`, not zero. The packet's own `(e1+e10)(e4+e13)` witness is zero, so the sedenion-kill mechanism is real, but the blind pre-registered exact class is not reproduced under the packet table orientation.

### B2. Fiber-Constancy Sampling

Decision: PASS.

The octonion fiber test samples unit `q` across all algebra coordinates, not just a quaternion subalgebra:

```python
def unit_vector(dim: int, seed: int) -> Any:
    vals = [math.sin((seed + 7) * (i + 1) * 0.19) + math.cos((seed + 2) * (i + 3) * 0.23) for i in range(dim)]
    v = jnp.asarray(vals, dtype=jnp.float64)
    return v / jnp.linalg.norm(v)
...
for seed in range(32):
    q = unit_vector(dim, seed)
```

Cites: `bloch_root_admissibility_discriminator_v0_jax.py:280-283`, `:328-335`.

Manual spot check with `q = (e1+e2+e4)/sqrt(3)` is not contained in any Fano-line quaternion subalgebra and gave fiber deviation `4.577566798522237e-16`. This supports the blind sheet's central alternativity tripwire.

### B3. PCA/Dimension Thresholds

Decision: PASS WITH MINOR CAVEAT.

Thresholds are source-pinned before result assembly, not post-hoc result-tuned:

```python
TOL = 1.0e-8
def affine_rank(points: Any, tol: float = 1.0e-8) -> int:
...
def pca_rank(points: list[Any], tol: float = 1.0e-7) -> int:
...
return pca_rank(points, tol=1.0e-10)
```

Cites: `bloch_root_admissibility_discriminator_v0_jax.py:37`, `:168-172`, `:286-303`, `:306-319`.

PyTorch independently pins `DTYPE = torch.float64`, `TOL = 1.0e-8`, and uses torch-native SVD:

```python
def rank(points: torch.Tensor, tol: float = 1.0e-8) -> int:
    centered = points - points.mean(dim=0, keepdim=True)
    s = torch.linalg.svdvals(centered)
    return int((s > tol).sum().item())
```

Cites: `bloch_root_admissibility_discriminator_v0_pytorch.py:33-67`, `:159-216`.

Caveat: the packet uses several fixed tolerances (`1e-8`, `1e-7`, `1e-10`) by role. They are predeclared in source and did not look tuned to final JSON, but a future hardening pass should consolidate or justify the tolerance split.

### B4. Orientation-Flip Control

Decision: PASS.

The JAX leg computes both label shuffle and orientation/sign flip controls:

```python
shuffled = table_transform(octonion, [0, 3, 1, 2, 5, 6, 7, 4], [1] * 8)
flipped = table_transform(octonion, list(range(8)), [1, 1, -1, 1, -1, 1, -1, 1])
...
"orientation_flip_control": {
    "base_dimension_O": local_base_dim(flipped),
    "fiber_dimension_O": local_fiber_dim(flipped),
    "t5_counts": assoc_nonzero_count(flipped)[:2],
    "invariant": local_base_dim(flipped) == 8 and local_fiber_dim(flipped) == 7 and assoc_nonzero_count(flipped)[:2] == (nonzero, zero),
}
```

Cites: `bloch_root_admissibility_discriminator_v0_jax.py:431-472`; T5 count flip at `:411-428`.

Result values show `base_dimension_O=8`, `fiber_dimension_O=7`, and T5 counts `(168,42)` invariant.

### B5. T1 Honesty

Decision: PASS.

The source builds a real refinement ladder and a repeated-probe non-refining control:

```python
ladder = [6, 14, 30, 62]
...
pts = refined[:k]
d_h = hausdorff_to_sphere(pts, dense)
...
repeated = refined[:6]
for k in ladder:
    d_h = hausdorff_to_sphere(repeated, dense)
```

Cites: `bloch_root_admissibility_discriminator_v0_jax.py:123-164`.

Fresh recompute gives decreasing refined distances and a flat repeated-probe control, so this is not the missing/flat T1 failure mode.

## Standard Checks

### Raw-Value SMT

Decision: PASS WITH ROUNDING CAVEAT.

The JAX SMT path binds computed numeric witnesses, not only pass booleans:

```python
sedenion_value = int(round(t4["norm_law_violation_magnitude"]))
noncomm_rank = int(t2["noncommuting_full_pauli_family"]["affine_dimension"])
comm_rank = int(t2["commuting_sigma_z_binned"]["affine_dimension"])
...
p1.add(v == z3.IntVal(sedenion_value))
p1.add(v == z3.IntVal(0))
...
p2.add(r == z3.IntVal(noncomm_rank))
p2.add(r < z3.IntVal(3))
```

Cites: `bloch_root_admissibility_discriminator_v0_jax.py:526-570`; cvc5 mirror at `:602-624`. Julia mirrors raw integer values at `bloch_root_admissibility_discriminator_v0_julia.jl:205-241`; PyTorch at `bloch_root_admissibility_discriminator_v0_pytorch.py:235-306`.

Fresh result: z3 and cvc5 are `unsat` for sedenion norm-violation equals zero and noncommuting rank <= 2, `sat` for the octonion zero and commuting-rank controls. Caveat: the sedenion violation is rounded to integer `1`; acceptable for this exact witness, but future non-integer witnesses should bind rationals/scaled ints.

### Fixture Isolation

Decision: PASS.

The four rungs share one ladder machinery rather than four hand-tuned cases:

```python
reports = [
    rung_report("R", real, 1, 0),
    rung_report("C", complex_table, 2, 1),
    rung_report("H", quaternion, 4, 3),
    rung_report("O", octonion, 8, 7),
]
```

Cites: `bloch_root_admissibility_discriminator_v0_jax.py:431-449`; Julia loop at `bloch_root_admissibility_discriminator_v0_julia.jl:251-268`; PyTorch loop at `bloch_root_admissibility_discriminator_v0_pytorch.py:194-216`.

The R3 H1 failure mode from `axis_independence_discriminators_036` was field-disjoint observable isolation. This packet is not an off-diagonal independence matrix and does not use that fixture pattern.

### Tautological Controls

Decision: PASS.

No `x-x` erasure or `pass=True` tautology was found in source. Controls recompute from changed data: T1 repeated probes, T2 commuting-only additions, T4 sedenion failure, T3/T5 label shuffle and orientation flip. Search for `x - x`, `pass.: True`, and `pass=true` did not expose a R3 H4-style tautological control.

### Cross-Leg Independence And PyTorch Honesty

Decision: PASS WITH ROLE CAVEAT.

The envelope keeps engine lanes separate and records `reads_peer_result=false` for all legs:

```python
legs = {engine: load_leg(engine) for engine in ("julia", "jax", "pytorch")}
...
payload["reads_peer_result"] is False
```

Cites: `bloch_root_admissibility_discriminator_v0_envelope.py:96-110`.

PyTorch uses torch-native SVD and `torch.func.jacrev`:

```python
s = torch.linalg.svdvals(centered)
...
full_jac = jacrev(full_probe_map)(probe_point)
commuting_jac = jacrev(commuting_probe_map)(probe_point)
```

Cites: `bloch_root_admissibility_discriminator_v0_pytorch.py:64-67`, `:78-107`.

Caveat: PyTorch does not implement T1 or T5 and only has a thinner T4 witness check; that is acceptable under the packet's stated role, but not an all-tests-independent PyTorch replication.

### NumPy Leakage

Decision: PASS.

No `import numpy`, `from numpy`, or `np.*` appears in the source files. The JAX leg uses `jax.numpy`, Julia uses `LinearAlgebra`, and PyTorch uses torch tensors.

### Ceiling/Fence Language

Decision: PASS.

The build card says:

```text
Ceiling: scratch_diagnostic, promotion_allowed=false, formal_admission_allowed=false. Language: the roots ADMIT the four-member family {S^1,S^2,S^4,S^8}; the C^2 carrier INSTALLS S^2 (installed-not-forced pattern); no carrier admission, no physics.
```

Cites: `build_card.md:5`.

The JAX source pins the same ceiling and language:

```python
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
...
"carrier":"C^2 INSTALLS S^2 installed-not-forced","physics":false
```

Cites: `bloch_root_admissibility_discriminator_v0_jax.py:33-45`; envelope allowed/must-not-claim lists at `bloch_root_admissibility_discriminator_v0_envelope.py:195-204`.

## R3 DECORATIVE Playbook Check

Using `axis_independence_discriminators_036/audit_verdict.md` H1-H7 as the failure-mode catalog:

| R3 failure mode | Present here? | Reason |
|---|---|---|
| H1 fixture isolation | No | This is not a vary/hold matrix over disjoint fields; shared ladder functions compute across rungs. |
| H2 label echo | No material hit | T2/T3/T4/T5 values come from ranks/table operations/counts, not labels. |
| H3 weak shuffle | No material hit | Shuffle/orientation controls recompute dimensions/counts from transformed tables. |
| H4 tautological controls | No | No `x-x` or hardcoded `pass=True` control found. |
| H5 derived-boolean SMT | Mostly no | SMT binds numeric values, with integer-rounding caveat. |
| H6 synthetic torch.func | No material hit | Torch Jacobian is simple but directly represents full-vs-commuting probe-map rank; SVD rank is torch-native. |
| H7 boundary asserted | No | The envelope explicitly fences allowed and forbidden claims. |

## Named Gaps

1. Exact B1 blind witness mismatch: under this packet's doubled imported-octonion table, `(e3+e10)(e6-e15)` is not zero. The packet should either include the blind witness under the intended table convention or explicitly document the orientation/convention translation from the blind sheet to its actual zero divisor.
2. T4 witness mismatch across expectation vs source: source records `(e1+e10)(e4+e13)`, while the blind sheet pre-registered `(e3+e10)(e6-e15)`. This is a provenance/cross-convention issue, not a decorative-tooling issue.
3. SMT value binding rounds the exact sedenion violation to an integer. It is okay for the current exact value `1.0`, but future non-integer SMT witnesses should use scaled integers or exact rationals.
4. PyTorch is honest but scoped: it independently checks T2/T3/T4 fragments, not the full JAX/JULIA T1-T5 suite.

## Final Boundary

This packet is a genuine scratch diagnostic with a real three-engine envelope and fresh validator pass. It earns the bounded claims that T1 converges with a plateauing non-refining control, T2 reconstructs dimensions `1/3`, T3 gives base/fiber dimensions `1/2/4/8` and `0/1/3/7`, T4 finds a real sedenion zero-divisor failure with magnitude-scale breaks, and T5 recomputes the `168/42` octonion associator split.

It does not earn a clean no-caveat verdict because the exact blind-sheet sedenion witness fails under the packet's table. Do not promote beyond `scratch_diagnostic`; do not cite as canonical carrier admission, formal admission, physics, or primitive Bloch-sphere evidence.

## Additive Hardening Receipt: 2026-06-10

Status: the four named hardening gaps above are closed in fresh source-generated result fields. This addendum is additive and preserves the original audit text as the pre-hardening record.

Fresh rerun commands:

- `/opt/homebrew/bin/julia --project=system_v5/julia_carrier system_v6/sims/bloch_root_admissibility_discriminator_v0/bloch_root_admissibility_discriminator_v0_julia.jl` returned `all_pass=true`.
- `env NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/bloch_root_admissibility_discriminator_v0/bloch_root_admissibility_discriminator_v0_jax.py` returned `all_pass=true`.
- `env NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/bloch_root_admissibility_discriminator_v0/bloch_root_admissibility_discriminator_v0_pytorch.py` returned `all_pass=true`.
- `env NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/bloch_root_admissibility_discriminator_v0/bloch_root_admissibility_discriminator_v0_envelope.py` returned `all_pass=true`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/bloch_root_admissibility_discriminator_v0/results/bloch_root_admissibility_discriminator_v0_envelope_results.json` returned `ok:true`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/bloch_root_admissibility_discriminator_v0/results/bloch_root_admissibility_discriminator_v0_envelope_results.json` returned `ok:true`.

Byte-stable claim values before and after rerun:

| Check | Pre-rerun | Post-rerun |
|---|---:|---:|
| T1 Hausdorff curve | `[0.91680271338944, 0.6296899779361548, 0.48979795188685626, 0.331218945973823]` | `[0.91680271338944, 0.6296899779361548, 0.48979795188685626, 0.331218945973823]` |
| T2 dimensions | `1/3` | `1/3` |
| T3 base/fiber dimensions | `[1,2,4,8] / [0,1,3,7]` | `[1,2,4,8] / [0,1,3,7]` |
| T4 violation/image deviation/fiber break | `1.0 / 1.0 / 1.4999999999999993` | `1.0 / 1.0 / 1.4999999999999993` |
| T5 nonassoc/fano-zero counts | `168/42` | `168/42` |
| SMT verdicts | `z3 unsat/unsat/sat/unsat/sat; cvc5 unsat/unsat/sat/unsat/sat; julia_z3 unsat/unsat/sat/unsat/sat` | `z3 unsat/unsat/sat/unsat/sat; cvc5 unsat/unsat/sat/unsat/sat; julia_z3 unsat/unsat/sat/unsat/sat` |

Gap 1+2 closure: `zero_divisor_convention_translation` is now emitted in the JAX T4 receipt and lifted to the envelope. Under the packet's doubled table, the packet witness `(e1+e10)(e4+e13)` has product terms `[]`, norm `0.0`, and `verified_zero_divisor_under_own_convention=true`. Under that same packet convention, the blind-sheet witness `(e3+e10)(e6-e15)` still emits the nonzero product `[[5,1.0],[7,-1.0],[12,1.0],[14,1.0]]`, norm `2.0`; this preserves the original mismatch instead of hiding it. The explicit blind convention map is octonion `perm=[0,3,2,1,6,7,4,5]`, `signs=[1,-1,1,1,-1,-1,1,-1]`, lifted to both Cayley-Dickson halves before doubling. Under that convention the blind witness product is `[]`, norm `0.0`, and `verified_zero_divisor_under_own_convention=true`.

Gap 3 closure: every fresh SMT receipt now emits `smt_value_encoding="exact_integer_ok_for_current_values; future non-integer witnesses require scaled integers or exact rationals"` and uses scaled-integer bindings for the current values. The fresh scaled values are `scale=1000000`, `sedenion_norm_violation_scaled=1000000`, `octonion_norm_violation_control_scaled=0`, `noncommuting_affine_rank_scaled=3000000`, `commuting_affine_rank_scaled=1000000`, and `rank_threshold_scaled=3000000`.

Gap 4 closure: the PyTorch leg and envelope now emit `pytorch_role="independently checks T2 torch-native SVD/Jacobian ranks, T3 torch-native Hopf base/fiber dimensions, and T4 torch-native sedenion zero-divisor/norm-law fragment; T1/T5 are Julia/JAX-only"`.

Ceiling unchanged: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. The packet remains bounded evidence only; no carrier admission, formal admission, physics, or primitive Bloch-sphere claim is added.

## Post-Hardening Re-Audit Addendum: 2026-06-10

Scope: focused independent re-audit of the four `## Named Gaps` closures after hardening. This addendum is append-only; the original audit and the 2026-06-10 hardening receipt above remain historical records.

Fresh runtime/preflight:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py` returned `ok=True install_state=stable_observed`, with sim-stack Python, `/opt/homebrew/bin/julia`, and `system_v5/julia_carrier`; no repo-local env pollution, missing expected modules, or active installers observed.
- `JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=system_v5/julia_carrier system_v6/sims/bloch_root_admissibility_discriminator_v0/bloch_root_admissibility_discriminator_v0_julia.jl` returned `all_pass=true`, `dims=[1, 2, 4, 8]`, `fibers=[0, 1, 3, 7]`, `z3=unsat`.
- `env NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/bloch_root_admissibility_discriminator_v0/bloch_root_admissibility_discriminator_v0_jax.py` returned `all_pass=true`, `sedenion_violation=1`, `z3=unsat`, `cvc5=unsat`.
- `env NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/bloch_root_admissibility_discriminator_v0/bloch_root_admissibility_discriminator_v0_pytorch.py` returned `all_pass=true`, `rank_full=3`, `dims=[1, 2, 4, 8]`, `z3=unsat`, `cvc5=unsat`.
- `env NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/bloch_root_admissibility_discriminator_v0/bloch_root_admissibility_discriminator_v0_envelope.py` returned `all_pass=true T1=True T2=True T3=True T4=True T5=True proof=True`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/bloch_root_admissibility_discriminator_v0/results/bloch_root_admissibility_discriminator_v0_envelope_results.json` returned `ok:true`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/bloch_root_admissibility_discriminator_v0/results/bloch_root_admissibility_discriminator_v0_envelope_results.json` returned `ok:true`.

Byte-stability rechecked from the freshly regenerated envelope:

| Check | Fresh value |
|---|---:|
| T1 Hausdorff curve | `[0.91680271338944, 0.6296899779361548, 0.48979795188685626, 0.331218945973823]` |
| T2 dimensions | JAX `1/3`; PyTorch SVD `1/3`; PyTorch Jacobian `1/3` |
| T4 violation/image deviation/fiber break | JAX `1.0 / 1.0 / 1.4999999999999993`; PyTorch violation/product norm `1.0 / 0.0` |
| T5 nonassoc/fano-zero counts | JAX `168/42`; Julia `168/42` |
| Solver verdicts | `z3 unsat/unsat/sat/unsat/sat`; `cvc5 unsat/unsat/sat/unsat/sat`; `julia_z3 unsat/unsat/sat/unsat/sat` |

Gap 1+2: closed. The convention-translation field is source-computed in `bloch_root_admissibility_discriminator_v0_jax.py:487-528` and lifted by the envelope at `bloch_root_admissibility_discriminator_v0_envelope.py:205-207`. I independently recomputed the products by importing the JAX leg functions and applying the emitted map. Under the packet doubled table, `(e1+e10)(e4+e13)` has product terms `[]`, norm `0.0`, and is a zero divisor. Under the same packet convention, `(e3+e10)(e6-e15)` has product terms `[[5,1.0],[7,-1.0],[12,1.0],[14,1.0]]`, norm `2.0`, and is not a zero divisor. Applying the explicit blind map `perm=[0,3,2,1,6,7,4,5]`, `signs=[1,-1,1,1,-1,-1,1,-1]` to the octonion parent table before doubling gives the blind witness product `[]`, norm `0.0`; the blind witness is a zero divisor under its own convention. The mismatch is now explicit convention translation, not an open witness gap.

Gap 3: closed for the current packet. The JAX SMT bindings use scaled integer variables at `bloch_root_admissibility_discriminator_v0_jax.py:575-633` and cvc5 mirrors the scaled binding at `bloch_root_admissibility_discriminator_v0_jax.py:665-680`; PyTorch mirrors scaled integer bindings at `bloch_root_admissibility_discriminator_v0_pytorch.py:235-330`. Fresh envelope values are `scale=1000000`, `sedenion_norm_violation_scaled=1000000`, `octonion_norm_violation_control_scaled=0`, `noncommuting_affine_rank_scaled=3000000`, `commuting_affine_rank_scaled=1000000`, and `rank_threshold_scaled=3000000`, with unchanged `unsat/unsat/sat/unsat/sat` verdicts. The field still says future non-integer witnesses require scaled integers or exact rationals, which is the right caveat rather than an open current gap.

Gap 4: closed. The emitted `pytorch_role` is accurate against the torch source: T2 uses torch-native SVD and `torch.func` Jacobian ranks, T3 computes torch-native local Hopf base/fiber dimensions, and T4 computes the torch-side sedenion zero-divisor/norm-law fragment; T1 and T5 are absent from the PyTorch `tests` payload and remain Julia/JAX-only. Source cites: `bloch_root_admissibility_discriminator_v0_pytorch.py:159-216`, `:219-230`, and `:376-382`. Envelope cites: `bloch_root_admissibility_discriminator_v0_envelope.py:220-227`.

Stale-surface check: `rg -n "open gap|not closed|still open|gaps remain open|clean no-caveat|fails under the packet|Named Gaps" system_v6/sims/bloch_root_admissibility_discriminator_v0 --glob '!audit_verdict.md'` returned no matches. Inside this file, the original `## Named Gaps` section and the original no-clean-verdict sentence are historical pre-hardening text; this addendum and the hardening receipt supersede them for current gap status without rewriting them.

Ceiling sustained: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Verdict language sustained: Bloch sphere survives as `S^3/S^1` quotient plus ball as channel domain, not as primitive carrier; the four-member family is admitted; the `C^2` carrier installs `S^2` as installed-not-forced. No carrier admission, formal admission, physics claim, primitive Bloch-sphere claim, or promotion is added.

GENUINE-WITH-CAVEATS sustained; problems: none found in the four named-gap closures under the fresh re-audit, with the ceiling unchanged.
