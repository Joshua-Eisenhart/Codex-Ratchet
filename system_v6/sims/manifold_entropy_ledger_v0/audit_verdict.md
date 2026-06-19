# Fresh audit verdict: manifold_entropy_ledger_v0

Auditor: codex1 cross-backend auditor.
Date: 2026-06-11.
Scope: read-only audit of the codex2-built `manifold_entropy_ledger_v0` packet, with this `audit_verdict.md` as the only allowed write.
Status of packet surface: untracked worktree packet, not committed; panel 6 preregistration is committed at `e2ca51b02`.

## Source standard

- Calibration bar: `system_v6/receipts/audit_bar_calibration_20260610.md` keeps "exactness-class stability", "can-fail controls", route genuineness, and scratch ceilings.
- Panel 6 preregistration: `system_v6/receipts/cross_model_anchor_recompute_panel6_20260611.md` pins `h[sin(2eta)] = 1 - ln 2`, `h[torus chart] = ln(2*pi^2)`, signed quotient entropy change `-ln N`, and exact disintegration chain rule.
- Build card ceiling: `classification="scratch_diagnostic"`, `promotion_allowed=false`, `formal_admission_allowed=false`.
- Owner framing cited as framing only: `system_v5/docs/OWNER_THESIS_AND_COSMOLOGY.md` says entropy is a later admissible measure; this packet must not promote entropy to the primitive object.

## Commands and checks run

```bash
python3 system_v6/sims/manifold_entropy_ledger_v0/validate_manifold_entropy_ledger_v0.py \
  system_v6/sims/manifold_entropy_ledger_v0/results/manifold_entropy_ledger_v0_envelope_results.json
# -> {"ok": true, "result_json": ".../manifold_entropy_ledger_v0_envelope_results.json"}

python3 scripts/validate_three_engine_sim_result.py \
  system_v6/sims/manifold_entropy_ledger_v0/results/manifold_entropy_ledger_v0_envelope_results.json
# -> {"ok": true, "result_json": ".../manifold_entropy_ledger_v0_envelope_results.json"}
```

Independent recomputation was done with a fresh SymPy one-shot, not by importing the packet module. It returned:

```text
h_eta = 1 - log(2) = 0.3068528194400547
h_s3 = log(2*pi**2) = 2.9826069522587457
Econd = -1 + log(4*pi**2) = 2.675754132818691
chain_defect = 0
flat_eta_chain_defect = log(4/pi)
signed Z4 quotient entropy change = -log(4)
terrain restriction delta log(40)-log(16) = log(5/2)
```

## Q1 - measure-level exact rows

Verdict: PASS for the exact S3, eta marginal, conditional-torus, and chain-rule rows.

Source rows:

- Packet result: `ledger.measure_level.round_s3.value_exact = "log(2*pi**2)"`.
- Packet result: `ledger.measure_level.eta_marginal.value_exact = "1 - log(2)"`.
- Packet result: `ledger.measure_level.conditional_expectation.value_exact = "-1 + log(4*pi**2)"`.
- Packet result: `ledger.measure_level.chain_rule_check.defect_exact = "0"`.
- Julia leg: `Manifolds.manifold_volume(Sphere(3))` feeds `h_s3`.
- Python leg: `sympy.integrate / sympy.simplify / sympy.log` feeds the exact integrals.

Hand derivation:

- Round unit `S^3` volume is `2*pi^2`; a uniform density against Riemannian volume has differential entropy `log(2*pi^2)`.
- For eta density `p(eta)=sin(2eta)` on `[0,pi/2]`:
  - `h(eta) = - int_0^(pi/2) sin(2eta) log(sin(2eta)) d eta`
  - substitute `u=2eta`; `h = -(1/2) int_0^pi sin(u) log(sin(u)) du`
  - weighted identity gives `h = 1 - log(2)`.
- Conditional leaf entropy under the packet's induced physical area convention is `h(T_eta)=log(2*pi^2*sin(2eta))`.
- Expected conditional entropy:
  - `E[h(T_eta)] = int sin(2eta) log(2*pi^2*sin(2eta)) d eta`
  - `= -1 + log(4*pi^2)`.
- Chain rule:
  - `(1 - log 2) + (-1 + log(4*pi^2)) = log(2*pi^2)`.
  - Exact defect is `0`.

Conditional torus spot checks:

```text
eta=pi/12: h(T_eta)=2*log(pi)
eta=pi/6:  h(T_eta)=log(3)/2 + 2*log(pi)
eta=pi/4:  h(T_eta)=log(2*pi**2)
```

k-leaf mixture entropy:

- Packet emits the 3-leaf row for `(pi/12, pi/6, pi/4)` with weights:
  - `1/2 - sqrt(3)/6`
  - `-1/2 + sqrt(3)/2`
  - `1 - sqrt(3)/3`
- Independent recomputation gives `H(weights)=1.0603402105196595` and mixture entropy `3.8438184547752363`, matching the packet.
- Committed two-leaf parent weights from `geo_union_rule_k_leaves_v0` are:
  - `eta1: -3 + 2*sqrt(3)` / ratio `sqrt(3)/(sqrt(3)+2)`
  - `eta2: 4 - 2*sqrt(3)` / ratio `2/(sqrt(3)+2)`
- Independent two-leaf entropy recomputation for leaves `(pi/6, pi/4)` gives weights `-3 + 2*sqrt(3)`, `4 - 2*sqrt(3)` and mixture entropy `3.2945123104411813`.

Named caveat: `CAVEAT_2LEAF_MIXTURE_NOT_NATIVE_ROW`. The packet hash-cites the k-leaf parent and emits the correct 3-leaf entropy row, but it does not emit its own native 2-leaf mixture entropy row. The two-leaf weights pass by parent citation plus fresh recomputation, not by a packet-local ledger row.

## Q2 - conditioning deltas

Verdict: PASS for measure-zero conditioning convention and terrain restriction; SIGN CAVEAT for the lens quotient row.

Measure-zero conditioning:

- Packet states `status="singular_measure_zero_conditioning"`.
- Packet states `honest_drop="infinite"`.
- Packet uses a symmetric finite band convention: `[eta0-epsilon, eta0+epsilon]`.
- At `eta0=pi/6`, packet records `h_band_asymptotic_exact = log(2*sqrt(3)*pi**2*epsilon)`, so `h_band -> -oo` as `epsilon -> 0`.

Terrain restriction:

- Packet records `before_rows=40`, `after_rows=16`, and `drop_exact=log(5/2)`.
- Parent `geo_s6_s7_mode_sweep_v0` records the same narrowing: `before=40`, `after=16`, excluded rows `24`.
- Independent recomputation: `log(40)-log(16)=log(5/2)=0.9162907318741551`.

Lens quotient:

- Panel 6 registered signed entropy change `-ln N`.
- Packet records `group_order=4`, `drop_exact=log(4)`, with derivation `log(Vol)-log(Vol/|G|)=log|G|`.
- This is correct as positive loss magnitude, but the signed entropy change is `h_after - h_before = -log(4)`.

Named caveat: `CAVEAT_SIGNED_LENS_DELTA_LABEL`. The math is right, but the row label is not aligned with the preregistered signed convention. Downstream consumers must read it as `loss_magnitude=+log(4)` and `signed_entropy_change=-log(4)`.

## Q3 - entropy type table and carrier anchors

Verdict: PASS WITH ANCHOR EXTRACTION CAVEAT.

The envelope type table is coherent:

- measure layer: differential entropy against Riemannian or induced area measure.
- conditioning bands/unions: mixed differential plus discrete Shannon term.
- carrier layer: von Neumann entropy from density-matrix parents, cited not recomputed.
- terrain restrictions: lattice/counting entropy.

Carrier anchors:

- n=3 through n=8 parent result paths are hash-cited under `carrier_level_anchors`.
- n=4 through n=8 expose sampled parent entropy rows in `sample_cited_entropy_rows`.
- n=3 is hash-cited, but `sample_cited_entropy_rows` is empty in this packet even though the parent result contains `P5_entropy` rows such as `GHZ_A_B_I`, `GHZ_A_B_conditional`, and `rho_AB_entropy_bits`.

Named caveat: `CAVEAT_N3_ANCHOR_SAMPLE_EMPTY`. This does not break the hash citation, but it weakens reviewer ergonomics and should be repaired if the packet is promoted from scratch diagnostic to a cleaner evidence surface.

Owner doctrine citation is correctly framing-only: the packet's ceiling and type table prevent entropy from becoming the master variable.

## Q4 - cross-layer meeting point

Verdict: PASS.

The packet's meeting row is:

```text
leaf: T_pi/6
measure_entropy_exact: log(3)/2 + 2*log(pi)
carrier_entropy_nats_exact: log(2)
product_bookkeeping_if_independent_exact: log(2*sqrt(3)*pi**2)
```

Reconciliation:

- The measure row is a differential entropy on the leaf's induced physical area.
- The carrier row is a cited vN entropy anchor, not recomputed here.
- The packet explicitly says they are typed separately and only an explicit product convention adds them.

This is a genuine computed meeting row, not entropy-type collapse.

## Q5 - controls and SMT rows

Verdict: PASS.

Wrong log base:

- Packet detects natural-log versus bit-log mismatch.
- It records `natural_value_exact = 1 - log(2)`.
- It records `bit_value_misread_as_nats_exact = -1 + 1/log(2)`.
- Defect is nonzero.

Wrong marginal:

- Packet flat-eta control gives chain defect `log(4/pi)`.
- Independent recomputation matches.

Wrong group order:

- Packet records actual order `4`, wrong order `3`, and defect `log(4/3)`.

SMT:

- z3 verdict: `unsat`.
- cvc5 verdict: `unsat`.
- Julia Z3 verdict: `unsat`.
- Erased conditional control verdict is `unsat` in all three rows.

The coefficient identity is load-bearing enough for this exact symbolic row: the solvers bind coefficient vectors over `[constant, log(2), log(pi)]`, and the erased conditional term makes the identity impossible.

## Q6 - process, lanes, tool calls, ceiling, and wording

Verdict: PASS WITH MODE-TRUTH CAVEAT.

Mode and lanes:

- Envelope says `mode="julia_canon_plus_jax_diagnostic"`.
- Lanes are Julia plus a Python exact sidecar in the JAX slot.
- PyTorch is explicitly omitted as not scoped because there is no graph/network/autograd claim path.
- This is honest enough for the stated diagnostic, but it is not a full three-engine/PyTorch claim.

Lineage:

- `parent_lineage` hash-cites all required parents, including the disintegration, nested disintegration, k-leaf union, S6/S7 mode sweep, terrain shell, compression, n=3..8 lifted shells, and scaling stress parents.
- `git ls-files` shows the packet itself is untracked; parent citations are to committed HEAD blobs.

Capabilities and versions:

- Python sidecar reports `sympy=1.14.0`, `z3-solver=4.16.0.0`, `cvc5=1.3.3`.
- Julia side reports active project `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml`, `Manifolds.Sphere=Sphere(3)`, and `Z3.Solver=imported_and_checked`.

One-to-one tools:

- `tool_calls_one_to_one=true`.
- Declared tools match emitted calls: `sympy`, `z3`, `cvc5`, `hashlib`, `json`, `pathlib`, `Manifolds`, `Z3`, `JSON`.

Ceiling:

- `classification="scratch_diagnostic"`.
- `promotion_allowed=false`.
- `formal_admission_allowed=false`.
- Blocked claims include formal admission, canonical manifold entropy theorem, physics/bridge claims, and recomputed carrier ladder entropy values.

No entropy-as-master-variable language:

- Scan found no target-packet use of `entropy-as-master`, `master variable`, or equivalent promotion wording.
- Source doctrine says entropy is later measure; the packet follows that by typing entropy rows as summaries of the constraint structure.

Forbidden wording:

- Before this audit file existed, the packet-local validator scanned `.py`, `.jl`, `.md`, and `.json` packet files and returned `ok:true`.
- That validator also required no preexisting `audit_verdict.md`; this audit file intentionally changes that precondition because the user explicitly requested it.

Named caveat: `CAVEAT_MODE_IS_TWO_LANE_DIAGNOSTIC`. The envelope schema is `three_engine_sim_result_v1`, but the actual evidence is Julia plus Python exact sidecar in a JAX slot. Do not cite it as a full Julia/JAX/PyTorch result.

## Verdict

VERDICT: ACCEPTED AS SCRATCH_DIAGNOSTIC_WITH_NAMED_CAVEATS.

Accepted:

- Exact measure-level S3, eta marginal, conditional torus, and disintegration chain-rule rows.
- k-leaf mixture entropy with weight term for the emitted 3-leaf row.
- Parent-cited and independently recomputed two-leaf weight check.
- Measure-zero conditioning handled by a stated band-limit convention, not naive finite conditioning.
- Terrain restriction delta `log(5/2)`.
- Coherent entropy type table.
- Cross-layer meeting point with types reconciled.
- Wrong-log-base, wrong-marginal, wrong group-order, and SMT erased-term controls.
- Honest diagnostic mode, parent lineage, capability receipts, one-to-one tool calls, versions, deterministic seed, and scratch ceiling.

Named caveats:

1. `CAVEAT_SIGNED_LENS_DELTA_LABEL`: packet emits `+log(4)` as loss magnitude; panel 6 signed entropy change is `-log(4)`.
2. `CAVEAT_2LEAF_MIXTURE_NOT_NATIVE_ROW`: committed 2-leaf weights pass by parent citation plus fresh recomputation, but the packet-local mixture row is 3-leaf.
3. `CAVEAT_N3_ANCHOR_SAMPLE_EMPTY`: n=3 parent is hash-cited, but auto-extracted sample entropy rows are empty despite entropy rows existing in the parent.
4. `CAVEAT_MODE_IS_TWO_LANE_DIAGNOSTIC`: the evidence is Julia plus Python exact sidecar, not a full three-runtime/PyTorch envelope.
5. `CAVEAT_UNTRACKED_PACKET`: the audited packet is currently untracked worktree state; this verdict does not imply committed admission.

Ceiling restated:

This packet supports a typed entropy-ledger scratch diagnostic over committed parent layers. It does not admit a canonical manifold entropy theorem, a physics/bridge claim, a master-variable entropy framing, or recomputed carrier-ladder evidence. Entropy rows here are summaries/readouts of the constraint structure under pinned conventions, not the primitive object.
