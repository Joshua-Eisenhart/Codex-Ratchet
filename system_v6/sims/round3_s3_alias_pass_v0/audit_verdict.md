# Fresh Audit Verdict: round3_s3_alias_pass_v0

Bottom line: VERDICT `ACCEPTED_WITH_NAMED_CAVEATS` as a bounded S3
`scratch_diagnostic` light-symbolic alias pass. The SIC tetrahedron disposition
is accepted: `S3.R3.2_sic_tetrahedron` is a cited known IC co-survivor and is
not heavy-queued. Phase 2 for S3 is `no_heavy_local_s3_queue`; do not queue a
heavy-local discriminator for SIC from this registry row.

This audit was read-only except for writing this file. I did not run packet
entrypoints that rewrite result JSONs, and I did not `git add` or commit.

## Verdict

Accepted claim:

- `S3.R3.0_committed_pauli_xyz` self-classifies as anchor.
- `S3.R3.1_mub_xyz_alias_probe` is an exact canonical-form alias of the
  committed Pauli XYZ effect family.
- `S3.R3.2_sic_tetrahedron` remains the only non-alias open representative, but
  it is a known IC co-survivor from the cited prior S3 receipt, not a newly
  discovered heavy-local obligation.
- `S3.R3.3_noisy_pauli_ic`, `S3.R3.4_z_refined_equatorial_trine`, and
  `S3.R3.5_rank4_random_null_fixed` are excluded by their registry-named
  light-symbolic teeth rows.
- `heavy_local_queued_by_registry_cost_class` is correctly empty for S3.

Rejected claims:

- S3 uniqueness.
- Global stack uniqueness.
- Heavy-local S3 completion.
- PyTorch/tensor/autograd evidence.
- SMT proof of surd canonical forms.
- Julia/Symbolics independent full canonical-form rebuild.
- Numeric-threshold closeness as alias evidence.

Ceiling: `classification=scratch_diagnostic`, `promotion_allowed=false`,
`formal_admission_allowed=false`.

## Registry And Prior Receipt

The registry S3 section cites the prior round-2 discriminator:
`geo_s3_alternative_probe_families_v0` at `608bbd763`
(`system_v6/receipts/round3_discriminator_registry_20260611.md:81-85`).
That section states the accepted lesson: SIC is a genuine IC co-survivor and
MUB-XYZ is an exact alias of committed Pauli XYZ. The S3 row table lists
`S3.R3.2_sic_tetrahedron` with cost class `light-symbolic`, not `heavy-local`
(`system_v6/receipts/round3_discriminator_registry_20260611.md:92-97`).

The prior receipt supports the "known" status:

- `system_v6/sims/geo_s3_alternative_probe_families_v0/audit_verdict.md:127-129`
  names SIC as a genuine IC co-survivor and MUB as exact tie/alias.
- `system_v6/sims/geo_s3_alternative_probe_families_v0/audit_verdict.md:162-168`
  accepts the bounded co-survivor result at `scratch_diagnostic` ceiling.
- `system_v6/receipts/stack_uniqueness_map_20260611.md:138-147` records
  `608bbd763`, says `SIC` is a genuine IC co-survivor, and says the S3 gap row
  becomes a named co-survivor row, not a kill row.

The registry stop rule says a heavy battery should not run for count inflation
when representatives are aliases or already classified known co-survivors by
the light pass (`system_v6/receipts/round3_discriminator_registry_20260611.md:237-249`).
Because every S3 row is `light-symbolic` and SIC's known co-survivor status is
receipt-backed, the packet's empty S3 heavy-local queue is faithful.

## Fresh Exact Checks

I recomputed the S3 canonical and teeth rows with exact SymPy rationals/surds.
Selected output:

```json
{
  "anchor_hash": "636c192773985f0f004ef901f7c5b4bad3efcfdc57d76f62d1aabd84cd11ee05",
  "mub_hash": "636c192773985f0f004ef901f7c5b4bad3efcfdc57d76f62d1aabd84cd11ee05",
  "mub_exact_alias": true,
  "sic_hash": "80870eb0f38878de4170d682998fa744d446a8cb022d27aba0a1dff92cf58fa1",
  "anchor_nonparallel_count": 12,
  "sic_nonparallel_count": 6,
  "noisy_2_3_deficits": ["5/324", "5/324", "5/324", "5/324", "5/324", "5/324"],
  "rank4_deficits": ["1/64", "3/64", "3/64", "3/64"],
  "rank4_rank": 4
}
```

Two exact exclusion checks:

- `S3.R3.3_noisy_pauli_ic__lambda_2_3`: registry row `projective sharpness and
  N01/order row`; anchor sharpness deficits are all `0`; candidate deficits are
  all `5/324`; witness scale `20/1296`.
- `S3.R3.4_z_refined_equatorial_trine`: registry row `z-coarsening plus
  six-state separation`; anchor z-axis effects have weights `1/6`; candidate
  z-axis effects have weights `1/4`; witness gap is `1/12`, recorded as
  `z_trine_z_weight_gap_times_12 = 1`.

Additional exclusion check:

- `S3.R3.5_rank4_random_null_fixed`: registry row `composite IC+z+order row`;
  frame rank remains `4`, but projective sharpness defects are nonzero with
  minimum `1/64`, and z/order signatures differ from the anchor.

Canonical-form fidelity:

- The packet's canonicalizer sorts exact effect rows and weighted Bloch Gram
  matrices over axis permutations
  (`system_v6/sims/round3_s3_alias_pass_v0/round3_s3_alias_pass_v0_jax.py:205-226`).
- Anchor and MUB rows both use exact `pauli_xyz(1)` effect rows
  (`system_v6/sims/round3_s3_alias_pass_v0/round3_s3_alias_pass_v0_jax.py:72-90`).
- Stored alias classes group anchor, MUB, anchor control, and deliberate
  reordered alias under the same hash
  (`system_v6/sims/round3_s3_alias_pass_v0/results/round3_s3_alias_pass_v0_envelope_results.json:47-59`).

## Controls

Controls pass the S2-style bar:

- Anchor self-classifies as `anchor`.
- Deliberate reordered Pauli XYZ classifies as `alias`.
- Far Z-only control dies on the first teeth row:
  `excluded-by-first-teeth-row-frame-rank-and-six-state-separation`.

Packet-local validator result is green and records these verdicts in
`system_v6/sims/round3_s3_alias_pass_v0/results/round3_s3_alias_pass_v0_validator_results.json:1-26`.
I did not rerun `validate_round3_s3_alias_pass_v0.py` because its CLI writes
`results/round3_s3_alias_pass_v0_validator_results.json`.

## Convention Pins

No S3 exclusion in this packet is only a pinned-convention separation. The
packet states the policy that a convention-only separation would use
`excluded-under-pinned-<convention>-convention`, and each current candidate has
`relaxing_pin_reopens=false`.

Future rule: if an S3 candidate later separates only by an axis/order convention
pin, it must be cited as a convention-pinned exclusion and marked reopenable if
the pin is relaxed. Do not cite such a row as an intrinsic kill.

## SMT, Julia, And Validator Scope

Generic validators passed read-only:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/round3_s3_alias_pass_v0/results/round3_s3_alias_pass_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s3_alias_pass_v0/results/round3_s3_alias_pass_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/round3_s3_alias_pass_v0/results/round3_s3_alias_pass_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s3_alias_pass_v0/results/round3_s3_alias_pass_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/round3_s3_alias_pass_v0/results/round3_s3_alias_pass_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s3_alias_pass_v0/results/round3_s3_alias_pass_v0_envelope_results.json"}
```

`--require-pytorch` fails as expected with `engines.pytorch must be an object`.
That is legitimate here because the packet explicitly declares honest PyTorch
omission for a light-symbolic exact canonicalization pass with no graph,
network, autograd, or tensor claim path.

SMT depth matches the S2 caveat. z3, cvc5, and Julia Z3 all bind finite rational
nonzero witness rows with SAT flip controls, but they do not prove the surd
canonical forms themselves. Cite SMT here only as a finite rational
nonzero-witness cross-check.

Julia depth also matches the S2 caveat. The Julia lane matches verdict rows and
binds finite rational witness constants through Z3.jl; it is not an independent
full canonical-form rebuild of the SymPy canonical tuple.

Source hashes checked:

```text
9b076f60b806dba22576e726005045ded9a806ac6c06ded54fa64181081e1ca4  system_v6/sims/round3_s3_alias_pass_v0/round3_s3_alias_pass_v0_jax.py
33dc175135c3d050b8c05f1084bdea2c3b9ac2afd494198715ebe0485eadc366  system_v6/sims/round3_s3_alias_pass_v0/round3_s3_alias_pass_v0_julia.jl
4d26f62032e81d7d947d3228c90c56629a63699fb7ed37424b57020a2917a707  system_v6/sims/round3_s3_alias_pass_v0/round3_s3_alias_pass_v0_envelope.py
```

## Named Caveats

- C1 - On-disk packet state: `system_v6/sims/round3_s3_alias_pass_v0/` is
  currently untracked in this checkout. This audit accepts current on-disk
  evidence only; it does not make the packet committed repo truth.
- C2 - MUB alias derivation depth: MUB-XYZ is encoded as the same exact
  `pauli_xyz(1)` effect-row representation as the anchor. That is faithful to
  the registry's alias calibrator, but it should be cited as canonical-form
  alias fidelity, not as an independent derivation from basis vectors in this
  packet.
- C3 - SIC wording: the result table uses `co-survivor-open`, while the phase-2
  queue uses `known_co_survivors_not_heavy_queued`. This is acceptable only
  because the registry cites prior receipt `608bbd763`; future citations should
  say `known IC co-survivor, receipt-backed by 608bbd763`.
- C4 - SMT caveat: SMT is finite rational nonzero-witness cross-check only; surd
  canonical forms remain CAS-backed.
- C5 - Julia caveat: Julia is verdict/Z3 sidecar parity, not independent full
  canonical tuple proof.
- C6 - No uniqueness promotion: this packet does not prove S3 uniqueness,
  stack uniqueness, or heavy-local completion.

## Phase-2 Disposition

S3 phase-2 disposition: `STOP_NO_HEAVY_LOCAL_S3`.

Reason: all S3 registry rows are cost-class `light-symbolic`; the MUB
representative is an exact alias; SIC is a prior-receipt-backed known
co-survivor; and R3.3-R3.5 are classified by registry-named light teeth. There
is no S3 heavy-local row to queue from
`round3_discriminator_registry_20260611.md`.

Future-citation rule:

> Cite `round3_s3_alias_pass_v0` only as bounded S3 light-symbolic alias/exclusion
> evidence: MUB canonical-form alias; SIC known IC co-survivor backed by
> `geo_s3_alternative_probe_families_v0` (`608bbd763`); R3.3-R3.5 excluded by
> named light teeth; no S3 heavy-local row queued by registry cost class. Do not
> cite it as S3 uniqueness, heavy-local S3 completion, PyTorch evidence, formal
> admission, or global stack uniqueness.
