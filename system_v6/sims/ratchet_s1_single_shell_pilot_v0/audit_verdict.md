# Audit verdict: ratchet_s1_single_shell_pilot_v0

Audit date: 2026-06-11

Scope: read-only fresh audit of `system_v6/sims/ratchet_s1_single_shell_pilot_v0/`, except this `audit_verdict.md`. I did not build this packet. I did not git add or commit anything.

Calibration used: `system_v6/receipts/audit_bar_calibration_20260610.md`. The binding bar keeps convention/order pins, route genuineness, can-fail controls, erasure honesty, source/capability honesty, scratch ceilings, and fresh-context audits; it relaxes over-strict byte/two-CAS/vocabulary requirements only when the math is otherwise checked. Source: `system_v6/receipts/audit_bar_calibration_20260610.md:5-11`.

Gate context used: mode-4 conditioning is authorized only through the committed `geo_disintegration_machinery_v0` rule. I verified `geo_disintegration_machinery_v0`, `geo_s1_finite_phase_lens_v0`, `geometry_sim_program_canonical_20260610.md`, and the audit calibration receipt are tracked and clean in this checkout: `git ls-files --stage -- ...` listed them, and `git diff --quiet -- ...` returned `diff_quiet_exit=0`. The pilot packet itself is untracked at audit time (`?? system_v6/sims/ratchet_s1_single_shell_pilot_v0/`), so this audits working-tree packet contents, not a committed pilot object.

## Sources checked

- `ratchet_s1_single_shell_pilot_v0.py`: `MODE = "RATCHETED"`, `ETA0_LABEL = "pi/6"`, `N = 4`; `PIN_SPEC` says `single_shell_only`, `step1=condition_T_eta0_via_geo_disintegration_machinery_v0_rule`, `conditional_chart_density=1/(4*pi^2)`, `step2=phase_lens_Z4_quotient_from_geo_s1_finite_phase_lens_v0`, and `no_nested_multi_shell_conditioning` (`ratchet_s1_single_shell_pilot_v0.py:28-55`).
- The committed disintegration rule says `conditional_on_T_eta=normalized_flat_torus_measure_in_phi_chi_chart`, `chart_double_cover=(phi,chi)~(phi+pi,chi+pi)`, and `conditional_chart_density=1/(4*pi^2)` (`geo_disintegration_machinery_v0_common.py:33-47`), with the convention pin repeating `physical_torus_area=2*pi^2*sin(2*eta)` and `conditional_chart_density=1/(4*pi^2) d_phi d_chi` (`geo_disintegration_machinery_v0_common.py:49-58`).
- The program rule defines `RATCHETED` as sequential constraint application with induced metric/connection/holonomy/measure recomputed at each step, and names narrowing, alteration, and path-specificity as computed signatures (`geometry_sim_program_canonical_20260610.md:10-14`).
- The finite lens packet authorizes the quotient family: build card says the cyclic group acts by `psi -> e^{2pi i/N} psi` (`geo_s1_finite_phase_lens_v0/build_card.md:3`), and the committed source/result rows record `action: psi -> exp(2pi i/N) psi` for the lens tower.

## Q1: Sequence and induced geometry

Verdict: PASS.

The sequence is genuine: step 0 is `S3 with round measure`; step 1 conditions to `T_eta0 where eta0=pi/6` through the committed `geo_disintegration_machinery_v0` prerequisite; step 2 quotients the already-conditioned leaf by `Z4` (`ratchet_s1_single_shell_pilot_v0.py:284-305`; result JSON `ratchet_sequence` lines 279-475). The step-1 rule citation is to the committed packet and matches the committed rule: the pilot cites `system_v6/sims/geo_disintegration_machinery_v0/geo_disintegration_machinery_v0_common.py#/PIN_SPEC` and records the conditional density `1/(4*pi^2) d_phi d_chi` (`ratchet_s1_single_shell_pilot_v0_envelope_results.json:264-271`, `300-309`).

Fresh recomputation:

```text
eta0 = pi/6
cos(eta0) = sqrt(3)/2
sin(eta0) = 1/2
cos(2*eta0) = cos(pi/3) = 1/2

metric in (phi, chi):
[[1, cos(2eta0)], [cos(2eta0), 1]] = [[1, 1/2], [1/2, 1]]
det = 1 - (1/2)^2 = 3/4

metric in (alpha=phi+chi, beta=phi-chi):
diag(cos^2 eta0, sin^2 eta0) = diag(3/4, 1/4)
radii = sqrt(3)/2, 1/2

A|_T = dphi + cos(2eta0)dchi = dphi + (1/2)dchi
```

These match the emitted rows: scalars at result lines 280-288, connection at lines 311-319, metric/radii at lines 358-393.

Holonomies recomputed from `A(delta_phi, delta_chi) = delta_phi + (1/2) delta_chi`:

```text
phi-cycle (2*pi, 0): 2*pi
chi-cycle (0, 2*pi): pi
alpha primitive (pi, pi): 3*pi/2
beta primitive (pi, -pi): pi/2
Z4 primitive quotient global cycle (pi/2, 0): pi/2
```

The packet records the same holonomies at result lines 324-356 and 417-445. Leaf area recomputation: chart area is `(2*pi)^2 * sqrt(3/4) = 2*sqrt(3)*pi^2`; quotient by the chart double cover gives physical leaf area `sqrt(3)*pi^2`; quotient by `|Z4|=4` gives `sqrt(3)*pi^2/4`. This matches result lines 287-288 and 404-405.

## Q2: Ratchet signatures

Verdict: PASS, with `G3_PATH_GAP_KIND` caveat below.

Narrowing is computed and names exact objects: `S3` dimension 3, `T_eta0` dimension 2 with ambient S3 measure 0 and conditional mass 1, then `T_eta0/Z4` dimension 2 with area ratio `1/4` (`ratchet_s1_single_shell_pilot_v0_envelope_results.json:486-514`).

Alteration is computed, not only asserted. The packet records before/after holonomy spectrum for the changed primitive global cycle: before step 2, the prequotient full global cycle is `2*pi`; after step 2, the primitive quotient global cycle is `pi/2`; identity `4 * h_quotient_global = h_prequotient_global` is recorded as `4 * 1 = 4` in `pi/2` units (`ratchet_s1_single_shell_pilot_v0_envelope_results.json:476-485`). Fresh recomputation matches.

The requested pair honestly commutes. The Z4 global phase action preserves eta, so condition-then-quotient and quotient-then-condition produce the same leaf quotient object. The packet records identical hashes for both orders, `74bd74da243642b75d5cac7c50aebb17bdc3f844784b918acd464a0e1fdf9b05`, and `same_pair_commutes=true` (`ratchet_s1_single_shell_pilot_v0_envelope_results.json:538-548`). I recomputed the same hash both ways.

The added noncommuting single-leaf extension is genuine. The third constraint is `phase_window_alpha_half: 0 <= alpha < pi on the single T_eta0 leaf`, with `nested_multi_shell_conditioning=false` (`ratchet_s1_single_shell_pilot_v0.py:375-384`; result lines 517-536). Fresh check of one Z4 orbit:

```text
alpha orbit under Z4 from pi/4:
[pi/4, 3*pi/4, 5*pi/4, 7*pi/4]
membership in 0 <= alpha < pi:
[true, true, false, false]
```

So the window is not Z4-saturated. Window-then-quotient cuts an orbit and keeps two of four representatives; quotient-then-window is not a well-defined quotient constraint without choosing a section. This gap can fail: it becomes zero if the window is Z4-saturated, if the quotient order is `N=1`, or if the window is empty/full on every orbit.

## Q3: Nested fence

Verdict: PASS.

No step jointly conditions on multiple leaves. The pin states `single_shell_only` and `no_nested_multi_shell_conditioning` (`ratchet_s1_single_shell_pilot_v0.py:48-55`). The envelope fence says `single_shell_only=true`, `nested_multi_shell_conditioning=false`, and `CAVEAT_NESTED_SCOPE respected; no nested or multi-layer conditioning is attempted` (`ratchet_s1_single_shell_pilot_v0_envelope_results.json:553-559`). The only broad grep hits for nested/multi-shell are these fence statements and the single-leaf phase window row.

## Q4: Controls

Verdict: PASS.

Nothing-excluded control passes byte-exactly on exact rows: `before_sha256` and `after_sha256` are both `96069cb44451ef8d7b50d0ba5b6ed9d6f9e20c8483c09d2710905771c8d69493` (`ratchet_s1_single_shell_pilot_v0_envelope_results.json:95-101`). This can fail if an identity/no-op constraint mutates the exact row subtree.

The naive-conditioning failure control is re-fired through the committed rule: denominator mass `0`, numerator mass `0`, naive quotient `nan`, and the source control cites the disintegration packet control (`ratchet_s1_single_shell_pilot_v0_envelope_results.json:103-110`). This can fail if the singleton leaf is treated as positive-mass or if the source rule is no longer cited.

The wrong-order control is distinct from the path-specificity row. It checks a local holonomy misuse: reusing the prequotient full global cycle as the primitive after Z4 quotient gives `2*pi`, while recomputing the primitive quotient holonomy gives `pi/2`; `control_fired=true` (`ratchet_s1_single_shell_pilot_v0_envelope_results.json:112-118`). This can fail at the `Z1` boundary, where the quotient generator holonomy equals the old full global holonomy; the packet records that boundary row at lines 85-90.

## Q5: Solver rows

Verdict: PASS.

The solver claim is the computed identity `4 * h_Z4_global = h_full_global` in `pi/2` units with bound values `h_Z4_global=1`, `h_full_global=4`. The source binds z3/cvc5 to integer variables and checks the negated positive identity for multiplier 4; for the erased flip, it replaces multiplier 4 by 3 (`ratchet_s1_single_shell_pilot_v0.py:128-154`, `434-463`).

Fresh solver recomputation:

```text
z3, positive negated identity 4*q != full with q=1, full=4: unsat
cvc5, positive negated identity 4*q != full with q=1, full=4: unsat
z3, erased multiplier 3 forced as 3*q == full: unsat
cvc5, erased multiplier 3 forced as 3*q == full: unsat
```

The result JSON records matching solver rows at lines 120-140 and tool-call rows at lines 604-640.

## Q6: Schema, mode, lanes, tools

Verdict: PASS for standard repo validation and ceilings; `G1_SOURCE_BACKED_LANES` and `G2_MISSING_PRE_FIX_HASH_NOTE` remain.

The envelope uses `schema_version=three_engine_sim_result_v1`, `mode=RATCHETED`, and `engine_contract.mode=RATCHETED` (`ratchet_s1_single_shell_pilot_v0_envelope_results.json:201-224`, `551-552`). Standard repo validator passed:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/ratchet_s1_single_shell_pilot_v0/results/ratchet_s1_single_shell_pilot_v0_envelope_results.json
{
  "ok": true,
  "result_json": "system_v6/sims/ratchet_s1_single_shell_pilot_v0/results/ratchet_s1_single_shell_pilot_v0_envelope_results.json"
}
```

The source hash matches current bytes: recorded and recomputed `source_sha256` are both `5ead05d53008b98a1e980ed5a8c6cbf8e5c2433ee26cc8190a0d1e58dec63880`. The current subtree hashes I recomputed are:

```text
ratchet_sequence_sha256_current = 7f0b8a230b5725263c556542b8cb43a1bfd4dc55832aaf1222a2b289b7ad525c
ratchet_signatures_sha256_current = d99750d49e42470a7cd249e3f52e4d55c8544ae1e02d9e9fcec420f30aa58fdf
controls_sha256_current = ce2f5032776312261078a3a8330f04018979f4b09368551567de3860970fad51
crossover_proofs_sha256_current = facf881098da7753df990f54ba0b4025acf82932b31ee3d9d0a1e6d6809fec51
```

I found no fix note with recorded pre-fix hashes to compare these against. The local `lane_log.md` says only that the exact row subtrees were preserved and that the repair was envelope-shape-only (`lane_log.md:6-8`). That statement is not a hash receipt.

Declared lanes are honest only with a caveat. The envelope itself says both `julia` and `jax` lanes are represented by the single Python builder, and that shared exact rows are computed once (`ratchet_s1_single_shell_pilot_v0_envelope_results.json:213`, `220-258`). That is honest prose, but not an actual Julia/JAX dual-engine execution. Standard validation accepts it; stricter source-backed validation fails:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/ratchet_s1_single_shell_pilot_v0/results/ratchet_s1_single_shell_pilot_v0_envelope_results.json
{
  "ok": false,
  "errors": [
    "julia: source-backed audit failed (declared_rich_but_source_thin_or_baseline): no source-backed rich package evidence for this engine; declared load-bearing packages not imported in source: Z3"
  ]
}
```

Capability receipts exist for Python, SymPy, z3, and cvc5, with API smokes (`ratchet_s1_single_shell_pilot_v0_envelope_results.json:59-75`). Tool calls are one-to-one with claim-path tools: `sympy`, `z3`, `cvc5` (`ratchet_s1_single_shell_pilot_v0_envelope_results.json:78-82`, `593-640`). `rg -ni "fixture" system_v6/sims/ratchet_s1_single_shell_pilot_v0` returned no fixture wording. Seeds are deterministic and explicit: `symbolic_seed=2026061011`, `smt_seed=2026061011`, `eta0=pi/6`, `phase_lens_N=4` (`ratchet_s1_single_shell_pilot_v0_envelope_results.json:561-567`). Ceilings are correct: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false` (`ratchet_s1_single_shell_pilot_v0_envelope_results.json:83`, `261-263`, `553-559`).

## Q7: Closure

Verdict: GENUINE-WITH-CAVEATS.

This pilot earns: mode-4/RATCHETED demonstrated on one fixed Hopf shell, `eta0=pi/6`, using the committed single-leaf disintegration rule, followed by a Z4 quotient with recomputed induced metric, area, connection, holonomies, narrowing rows, alteration row, honest commuting base pair, and one genuine noncommuting single-leaf phase-window extension.

It does not earn: nested ratchet, multi-shell conditioning, multi-leaf conditioning, manifold-level trend, axis-level claim, bridge claim, S11/M(C,t), formal admission, canonical status, or evidence that a real Julia/JAX two-engine execution occurred for this pilot. It also does not prove that the shape-only repair preserved pre-fix exact rows, because no pre-fix hash receipt was found.

## Named caveats

- `G1_SOURCE_BACKED_LANES`: The math rows and standard repo validator pass, but the declared `julia`/`jax` lanes are scoped labels over one Python/SymPy/z3/cvc5 builder, not actual separate Julia and JAX executions. The stricter source-backed validator fails the Julia lane because declared load-bearing `Z3` is not imported in source. This blocks any "fresh two-engine Julia/JAX execution" language.
- `G2_MISSING_PRE_FIX_HASH_NOTE`: The packet/lane log says the schema fork fix was shape-only, but I found no recorded pre-fix hashes. Current subtree hashes are emitted above, but preservation across the repair is unverified.
- `G3_PATH_GAP_KIND`: The noncommuting extension is a valid quotient well-definedness/equivariance failure, not two fully defined quotient outputs compared by the same numeric invariant. This is enough for branch mortality/path-specificity, but the ceiling should state the gap as non-Z4-saturation, not as a full numeric order-gap family.

## Final verdict

GENUINE-WITH-CAVEATS.

Ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; single fixed-eta shell only; no nested ratchet; no multi-shell claim; no M(C,t), manifold, axis, bridge, or trend claim. The admissible earned claim is: one single-shell RATCHETED pilot with recomputed induced geometry and one genuine noncommuting single-leaf phase-window extension, subject to `G1`, `G2`, and `G3`.

## Focused re-audit addendum: G1/G2/G3 hardening

Re-audit date: 2026-06-11. Scope was read-only except this addendum; I did not git add or commit anything.

### G1: real Julia leg and strict source-backed lanes

Closed.

The Julia leg is an actual separate Julia execution path: `ratchet_s1_single_shell_pilot_v0_julia.jl` imports `Z3`, constructs its own exact rows, writes its own result JSON, and records `reads_peer_result=false` (`ratchet_s1_single_shell_pilot_v0_julia.jl:3-13`, `54-87`, `122-147`). To avoid overwriting the packet result during this read-only re-audit, I executed the Julia source with only `RESULT_DIR` redirected in-memory to a temporary directory. It returned:

```text
{"ok":true,"result_path":".../ratchet_s1_single_shell_pilot_v0_julia_results.json"}
```

The fresh temp result matched the packet Julia exact rows and engine values exactly. Hand-check rows:

```text
A|_T dchi coefficient = 1/2
quotient_area = sqrt(3)*pi**2/4
all_pass = true
reads_peer_result = false
source_sha256 = d216cd9c8016af398e0a0838a11ef721dac3eddedb26a4015e8ee1a8d7f21b7b
```

Z3.jl is load-bearing on the caveat row. The source binds `q=1`, `full=4`, checks the negated multiplier-4 identity as `unsat`, checks the multiplier-3 erased control as `unsat`, and gates the row with `["G1_SOURCE_BACKED_LANES", "proof", "all_pass"]` (`ratchet_s1_single_shell_pilot_v0_julia.jl:29-50`, `107-120`, `140-160`). The fresh result quoted:

```text
julia_z3_verdict = unsat
julia_z3_gates = ["G1_SOURCE_BACKED_LANES", "proof", "all_pass"]
tool_call_gates = ["G1_SOURCE_BACKED_LANES"]
```

Strict validators pass for the declared lanes:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/ratchet_s1_single_shell_pilot_v0/results/ratchet_s1_single_shell_pilot_v0_envelope_results.json
{
  "ok": true,
  "result_json": "system_v6/sims/ratchet_s1_single_shell_pilot_v0/results/ratchet_s1_single_shell_pilot_v0_envelope_results.json"
}
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/ratchet_s1_single_shell_pilot_v0/results/ratchet_s1_single_shell_pilot_v0_envelope_results.json
{
  "ok": true,
  "result_json": "system_v6/sims/ratchet_s1_single_shell_pilot_v0/results/ratchet_s1_single_shell_pilot_v0_envelope_results.json"
}
```

The packet-local validator also passes:

```text
{
  "errors": [],
  "generated_at": "2026-06-11T00:51:20Z",
  "ok": true,
  "validated_mode": "RATCHETED"
}
```

### G2: packet-local shape-only-repair hash receipt

Closed.

The hash receipt now lives in the packet envelope at `computed_subtree_hashes`, with `kind=shape_only_repair_hash_receipt`, `fresh_full_rerun=true`, and algorithm `sha256(stable_json(sort_keys=True,separators=(',',':')))`. It records `{subtree, hash}` pairs including:

```text
ratchet_sequence -> 7f0b8a230b5725263c556542b8cb43a1bfd4dc55832aaf1222a2b289b7ad525c
controls -> ce2f5032776312261078a3a8330f04018979f4b09368551567de3860970fad51
crossover_proofs_python_z3_cvc5 -> facf881098da7753df990f54ba0b4025acf82932b31ee3d9d0a1e6d6809fec51
crossover_proofs_with_julia_z3 -> b44cbe07475a33a876efd37d5dde5ddc09ad2f511c9aa4216d2de08d35e59390
julia_exact_rows -> da12ca66893d72fd480997b05541c266b6d6aaa3f4ef428b7460f45cb23d042d
```

I recomputed the `ratchet_sequence` hash directly from the envelope using the declared algorithm and got:

```text
ratchet_sequence 7f0b8a230b5725263c556542b8cb43a1bfd4dc55832aaf1222a2b289b7ad525c
```

This matches the recorded packet hash.

### G3: path-specificity language

Closed.

The envelope claim now states:

```text
path-specificity is a non-Z4-saturation quotient well-definedness/equivariance failure, not a numeric order-gap family.
```

The hardening evidence states:

```text
claim_kind = quotient_well_definedness_equivariance_failure
is_Z4_saturated = false
branch_mortality = quotient-first branch kills this non-Z4-saturated window as a coherent quotient constraint
```

The summary preserves the ceiling: `not_numeric_order_gap_family=true` and `path_specificity_kind=quotient_well_definedness_equivariance_failure`. This closes the old caveat; the packet no longer frames the extension as a numeric order-gap family.

### Focused conclusion

G1 closed; G2 closed; G3 closed. The pilot earns exactly one single-shell `RATCHETED` scratch diagnostic: condition `S3` to `T_eta0` at `eta0=pi/6` via the committed disintegration rule, quotient the induced leaf by `Z4`, recompute induced metric/area/connection/holonomy, and exhibit one non-Z4-saturated single-leaf phase-window branch mortality row. Ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`; no nested ratchet, multi-shell conditioning, M(C,t), manifold, axis, bridge, trend, canonical, or formal-admission claim is earned.
