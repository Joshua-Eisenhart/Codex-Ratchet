# Audit verdict - round3_s6s7_heavy_discriminator_v0

Bottom line: VERDICT `GENUINE-WITH-CAVEATS` as a bounded S6/S7 phase-2
heavy-local `scratch_diagnostic` discriminator. The packet answers exactly the
five queued S6/S7 heavy rows from the registry/light verdict: all five are
excluded by their registry-named teeth across `N={8,16,32}`, no co-survivor is
minted, and no exclusion is size-relative. This does not prove global S6/S7
uniqueness, formal admission, canonical promotion, or any non-S6/S7 heavy queue
item.

This audit was read-only except for writing this file. I did not `git add` or
commit.

## Verdict

Accepted:

- Repo vocabulary: `GENUINE-WITH-CAVEATS`.
- Classification: `scratch_diagnostic`.
- `promotion_allowed=false`; `formal_admission_allowed=false`.
- Engine mode: `julia_canon_jax_with_pytorch_graph`.
- Registry binding: `de44219ed`, with matching registry SHA-256
  `aedae4224bf2f3fea6aa1b73981f0035589dbce352e9370bfe34dec402e491b3`.
- Scope: S6/S7 only; exactly five queued heavy-local rows.
- Co-survivors minted: none.
- Size-relative labels: none; every candidate separates at `N=8,16,32`.

Rejected or not promoted:

- S6/S7 uniqueness.
- Exhaustiveness beyond the registry's finite alternative space.
- Canonical-by-process or formal admission.
- Any claim that PyTorch/PyG is the semantic arbiter for cover/lens rows.
- Any claim that SMT proves the full S6/S7 canonical tuple.
- Any closure of S2 or S9 heavy rows.

## Certificate Reality

Accepted. The explicit reparameterized-cycle isomorphism certificate is present
in the result JSON and in the envelope under
`positive.explicit_isomorphism_certificate`. It contains:

```text
mapping_anchor_to_reparameterized = {0:3, 1:2, 2:1, 3:0, 4:7, 5:6, 6:5, 7:4}
bijection_size = 8
edge_by_edge_verified = true
mapped_edge_set_sha256 = target_edge_set_sha256 =
  6fb560a65293bcd2d199750750507396afb1bde2be608ce1c78b4b98cffcacdd
```

Fresh audit recomputation rebuilt the anchor cycle, applied the stored mapping,
and compared the mapped edge set to the reparameterized target edge set. Result:
`mapped_edges_equal_target=true`, `json_edge_checks_match_recompute=true`, and
all recomputed mapped edges were present in the target graph. This upgrades the
S6/S7 light-pass caveat from `isomorphism-call backed` to
`explicit-mapping-certificate backed` for this control.

## Exact Witness Recompute

Fresh scratch recomputation independent of builder prose confirmed the required
non-isomorphic witnesses:

```text
Klein double twist, N=8:
anchor orbit multiset = 32 classes, all size 2
candidate orbit multiset = [2,2,4,...,4], 17 classes total
candidate lens failure count = 13
separated = true

Klein double twist, N=16:
anchor orbit classes = 128, all size 2
candidate orbit classes = 65, head [2,2,4,4], tail [4,4,4,4]
candidate lens failure count = 61
separated = true

Klein double twist, N=32:
anchor orbit classes = 512, all size 2
candidate orbit classes = 257, head [2,2,4,4], tail [4,4,4,4]
candidate lens failure count = 253
separated = true
```

```text
Ladder/prism graph, N=8:
anchor cycle graph on 16 nodes: edges=16, degree sequence all 2, cycle rank=1
candidate prism graph: edges=24, degree sequence all 3, cycle rank=9
anchor charpoly =
  lambda**16 - 16*lambda**14 + 104*lambda**12 - 352*lambda**10
  + 660*lambda**8 - 672*lambda**6 + 336*lambda**4 - 64*lambda**2
candidate charpoly =
  lambda**16 - 24*lambda**14 + 212*lambda**12 - 856*lambda**10
  + 1630*lambda**8 - 1544*lambda**6 + 708*lambda**4
  - 136*lambda**2 + 9
```

Additional recomputed graph witness:

```text
Cycle with one chord, N=8:
anchor cycle rank=1, degree sequence all 2, distance(0,4)=4
candidate cycle rank=5, degree sequence all 3, distance(0,4)=1
candidate charpoly =
  lambda**8 - 12*lambda**6 + 34*lambda**4 - 16*lambda**3
  - 20*lambda**2 + 16*lambda - 3
```

## Citable Per-Candidate Table

| Candidate | Registry heavy row | Verdict | Sizes | Citable witness |
| --- | --- | --- | --- | --- |
| `S67.R3.1_mobius_reflection_shifted` | lens quotient commensurability | `excluded-by-lens-quotient-commensurability` | `8,16,32` | At `N=8`, anchor lens failures `0`; candidate lens failures `96`; first failure maps one class to image classes `[18,22]`. |
| `S67.R3.2_klein_double_twist` | cover-orbit well-definedness then lens row | `excluded-by-cover-orbit-well-definedness-then-lens-row` | `8,16,32` | At `N=8`, anchor orbit multiset all 2s with 32 classes; candidate multiset `[2,2,4,...,4]` with 17 classes; lens failures `13`. |
| `S67.R3.3_shear_torus` | lens descent and S6 leakage taxonomy | `excluded-by-lens-descent-and-S6-leakage-taxonomy` | `8,16,32` | At `N=8`, anchor leakage `{leak:0, move:32, preserve:0}`; candidate leakage `{leak:12, move:4, preserve:0}`; lens failures `12`. |
| `S67.R3.4_cycle_with_one_chord` | bounded word cost and cycle holonomy | `excluded-by-bounded-word-cost-and-cycle-holonomy` | `8,16,32` | At `N=8`, distance gap `4 -> 1`, cycle rank `1 -> 5`, degree sequence all `2 -> 3`. |
| `S67.R3.5_ladder_prism_graph` | locality cost plus leakage class row | `excluded-by-locality-cost-plus-leakage-class-row` | `8,16,32` | At `N=8`, anchor cycle rank `1`; prism cycle rank `9`; degree sequence all `2 -> 3`; cross-layer gap `8`. |

Known S6/S7 R3 co-survivor classes after this packet: none.

## Size Relativity

No size-relative rows were found. The envelope table reports
`N_sweep=[8,16,32]`, `separating_sizes=[8,16,32]`, and `size_relative=false`
for all five candidates. Fresh recomputation spot-checked the cover/lens and
graph rows and found the same pattern: every named candidate separates at all
three scoped sizes.

## Controls

Accepted controls:

- Anchor self-pass: `anchor_self.self_passes=true`; cycle and untwisted cover
  rows self-classify at `N=8`.
- Deliberate reparameterized cycle: accepted as an explicit
  mapping-certificate-backed alias, not merely an isomorphism-call-backed alias.
- Round-2 path far-control regression: remains
  `excluded-by-closed-cycle-graph-row`; at `N=8`, path degree sequence
  `[1,1,2,2,2,2,2,2]` and cycle rank `0` separate from the closed-cycle anchor
  degree sequence all `2` and cycle rank `1`.

## PyTorch/PyG Honesty

Accepted with a narrow scope. PyG is genuinely used for finite support-graph
N-sweeps, but only for the graph carrier rows:

- `round3_s6s7_heavy_discriminator_v0_pytorch.py` builds
  `torch_geometric.data.Data(edge_index=..., num_nodes=...)` for chord and
  ladder/prism graph edge lists at `N=8,16,32`.
- Fresh read-only import of the PyTorch lane recomputed:
  - `N=8`: chord `8` nodes / `24` directed edges; ladder `16` nodes / `48`
    directed edges; degree unique set `[3]`.
  - `N=16`: chord `16` nodes / `48` directed edges; ladder `32` nodes / `96`
    directed edges; degree unique set `[3]`.
  - `N=32`: chord `32` nodes / `96` directed edges; ladder `64` nodes / `192`
    directed edges; degree unique set `[3]`.
- The PyTorch source-backing probe passed:
  `torch.func.vmap` shape `[3,2]`, PyG probe nodes `3`, edges `2`, and z3/cvc5
  node-identity checks both `unsat`.

Boundary: PyG is not load-bearing for the cover/lens semantics of
`S67.R3.1`, `S67.R3.2`, or `S67.R3.3`; those remain Julia/JAX/Python finite
cover/lens rows. PyG is load-bearing for the packet's graph-carrier path and
the chord/ladder support-graph rows, not for global S6/S7 topology.

## SMT And Validator Evidence

SMT is accepted as finite computed-value binding with erased/flip controls:

```text
z3 verdict = unsat; flip_control_verdict = sat
cvc5 verdict = unsat; flip_control_verdict = sat
Julia Z3 verdict = unsat; flip_control_verdict = sat

N=8 witness values include:
excluded_candidate_count = 5
mobius lens failures = 96
klein orbit gap = 2
shear leak count = 12
chord cycle-rank gap = 4
chord distance gap = 3
prism cross-layer gap = 8
```

This is not a proof of the full S6/S7 canonical tuple; it binds finite witness
integers from the computed rows and demonstrates that erased/mutated controls
flip.

Fresh read-only validators run by this audit:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py \
  system_v6/sims/round3_s6s7_heavy_discriminator_v0/results/round3_s6s7_heavy_discriminator_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s6s7_heavy_discriminator_v0/results/round3_s6s7_heavy_discriminator_v0_envelope_results.json"}
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py --require-pytorch \
  system_v6/sims/round3_s6s7_heavy_discriminator_v0/results/round3_s6s7_heavy_discriminator_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s6s7_heavy_discriminator_v0/results/round3_s6s7_heavy_discriminator_v0_envelope_results.json"}
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py --require-pytorch \
  --strict-source-backed --require-tool-intent \
  system_v6/sims/round3_s6s7_heavy_discriminator_v0/results/round3_s6s7_heavy_discriminator_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s6s7_heavy_discriminator_v0/results/round3_s6s7_heavy_discriminator_v0_envelope_results.json"}
```

Packet-local validator caveat: I did not rerun
`validate_round3_s6s7_heavy_discriminator_v0.py` because it writes
`results/round3_s6s7_heavy_discriminator_v0_validator_results.json`, and this
audit was allowed to write only this verdict file. The existing on-disk
packet-local validator result reports `ok=true`, `validator_ok=true`, and
`errors=[]`.

## Builder-Self-Verdict Contamination Check

`builder_self_assessment.md` was read only after forming this verdict. Its core
bottom line matches the independently recomputed evidence: five registered rows
excluded, no co-survivors, no size-relative labels, explicit mapping
certificate present, and bounded `scratch_diagnostic` ceiling.

Contamination caveat:

- Treat all builder-authored verdict language as builder prose only.
- The builder's packet-local validator command is not independent audit
  evidence. It is supported only as an existing on-disk validator-result fact,
  because rerunning that validator would violate this audit's write boundary.
- Any wording in builder prose that sounds like "all validators rerun by the
  auditor" is not supported. The auditor freshly reran the generic
  read-only three-engine validators listed above and inspected the existing
  packet-local validator result.

No builder claim materially stronger than the evidence is accepted here.

## On-Disk State And Route Truth

`system_v6/sims/round3_s6s7_heavy_discriminator_v0/` is currently untracked in
this checkout. This verdict accepts current on-disk evidence only; it does not
make the packet committed repo truth.

Wizard/subagent route truth: this was an independent controller audit with
direct repo inspection, fresh scratch recomputation, and fresh read-only
validators. No Codex-native subagent/council topology is claimed for this
verdict.

## Future-Citation Rule

Future citations may say:

```text
round3_s6s7_heavy_discriminator_v0 is accepted as a bounded S6/S7 phase-2
heavy-local scratch_diagnostic: the five queued S6/S7 rows from the light
verdict/registry were run under the registry de44219ed teeth; the deliberate
reparameterized cycle has an explicit edge-by-edge mapping certificate; all
five candidates separate at N=8,16,32; R3.1 is excluded by lens quotient
commensurability, R3.2 by cover-orbit/lens, R3.3 by lens descent and S6
leakage taxonomy, R3.4 by bounded word cost and cycle holonomy, and R3.5 by
locality cost plus leakage class row; no S6/S7 R3 co-survivor was minted.
```

Future citations must not say:

```text
S6/S7 uniqueness is proved; the registry alternative space is exhaustive beyond
its finite declaration; the packet is canonical by process; PyG proves the
cover/lens rows; SMT proves the full S6/S7 canonical tuple; the packet closes
S2 or S9 heavy rows; the packet is committed repo truth before it is actually
committed.
```

## Remaining Heavy Queue

With S4 and S5 heavy verdicts already accepted and this S6/S7 packet accepted,
the remaining cross-layer phase-2 heavy queue is:

```text
S2.R3.5_boundary_conditioning_variant - cover/conditioning validity before flux comparison
S9.R3.5_path_ordered_loop_neighbor - path-ordered holonomy commutator
```

Do not relaunch S6/S7 heavy work for count inflation unless the registry,
light-verdict normalization, or a pinned convention changes.
