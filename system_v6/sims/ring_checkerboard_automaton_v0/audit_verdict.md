# Independent audit verdict - ring_checkerboard_automaton_v0

Auditor: independent Codex audit, read-only except this file.
Date: 2026-06-12.

## Bottom line

Verdict: PASS as `scratch_diagnostic` / `passes local rerun` for a bounded classical floor over the owner's ring-checkerboard support.

The packet realizes an owner-shaped support, not a generic lattice CA wearing ring labels: base ring steps, parity coloring, and one attached-ring level are explicit. The decisive alternating-vs-paired phase test survives a label-free recomputation on the smallest realized size (`n=4`): alternating gives period-2 terminal/orbit structure; paired gives period-4 terminal/orbit structure; terminal state counts and SCC counts differ. Controls and falsifier branches execute. The packet remains fenced: no QCA/index, no 64/engine-placement, no quantum row, no full binary CA over all cells, and no canonical admission.

Main caveats:

- This is a single-active engine/readout-token transition graph over the support, not the full cellular-automaton configuration space of all cells.
- The built-in `alternating_vs_paired` equality helper compares full signatures that include the `discipline` label. That would be insufficient alone. Independent label-free recomputation still passes, so this is a hardening issue, not a kill.
- The three backend lanes are execution/backend mirrors, not three fully independent semantic implementations: JAX and PyTorch both call the shared Python packet builder; Julia independently mirrors a thinner signature.
- The packet's native nesting row compares nested `n=8` to bare `n=8`, so state count differs. I added a size-matched audit control (`nested n=4` vs `bare n=20`, both 20 support cells / 320 states), and nesting still changes terminal structure.

## Owner-structure fidelity

Adjudication: PASS for v0 support fidelity, bounded to flat one-level nesting.

Source obligation:

- Owner-source provenance names nested checkerboards: "defined size. Like 2x2, 4x4, 8 x8. Then these are nested" in the Apple-note excerpt recorded at `system_v6/receipts/ring_checkerboard_provenance_20260611.md:53-55`.
- It names discrete ring steps and attachment: "2, 4, 8, 16, 32, 64" and each discrete step having a ring attached in `system_v6/receipts/ring_checkerboard_provenance_20260611.md:59-62`.
- The curated raw construction says to attach rings at discrete edge points and then attach rings to those rings, one nesting layer and beyond, at `system_v6/receipts/ring_checkerboard_provenance_20260611.md:98-101`.

Realization checked:

- `support_cells()` constructs base ring cells and, when nested, one attached ring for every base step: `system_v6/sims/ring_checkerboard_automaton_v0/ring_checkerboard_automaton_v0_common.py:137-167`.
- Parity coloring is `kappa=(layer+step) mod 2`: `ring_checkerboard_automaton_v0_common.py:158`.
- The result object declares base ring plus one attached ring at each base step, flat mode only, QCA/index deferred: `ring_checkerboard_automaton_v0_common.py:993-1002`.
- Size rows cover the owner's named small steps `{4,8,16}` and fence 32/64 as later: `ring_checkerboard_automaton_v0_common.py:990-992`.

Not accepted: full nested depth 3-12, spherical/spinning mode, engine placement on spinors, or 32/64 engine claims.

## Doctrine expectations

Expectation 1, classical ring-checkerboard automaton plus basin contract: PASS, with scope ceiling.

- The doctrine's classical floor expects finite automaton, two update phases, and basin machinery at `system_v6/receipts/owner_doctrine_cellular_automata_ring_checkerboard_20260611.md:29-31`.
- Fresh recomputation on `n=4` found alternating: `scc_count=136`, `terminal_class_count=24`, `terminal_state_count=48`, `period_histogram={"2":160}`.
- Fresh recomputation on `n=4` found paired: `scc_count=88`, `terminal_class_count=24`, `terminal_state_count=96`, `period_histogram={"4":160}`.
- Basin contract machinery is real: SCC terminal rows with absent-exit proof, may/must basin maps, and monotone exclusion observable are built at `ring_checkerboard_automaton_v0_common.py:459-582`.

Expectation 2, QCA/index and flux-signed L/R engines: NOT EVALUATED / FENCED.

- The doctrine explicitly puts QCA/index after the classical floor: `owner_doctrine_cellular_automata_ring_checkerboard_20260611.md:42-45`.
- Packet fences `qca_index` to `v1_or_later_not_here`: `ring_checkerboard_automaton_v0_common.py:1001`.

Expectation 3, locality as missing structure and coupling-law change: PARTIAL PASS.

- Locality exists for this bounded state family: updates consult the active cell, same-ring neighbor, paired partner, and immediate attachment neighbor, not global state tables. See `move_cell()`, `elementary_phase_update()`, `paired_block_update()`, and `transition_state()` at `ring_checkerboard_automaton_v0_common.py:236-421`.
- Controls show local structure matters: order shuffle, non-partitioned scramble, ring-off, checkerboard-off, nesting-off, and frozen-phase all change dynamics.
- Not accepted as a full comparison against global v2/v3 automata. This packet establishes the local classical floor and controls only.

## Phase test

Adjudication: PASS, but harden the built-in comparison.

The decisive row is structurally distinguishable under label-free checks:

| Check | Alternating n=4 | Paired n=4 | Adjudication |
|---|---:|---:|---|
| support cells | 20 | 20 | same support |
| states | 160 | 160 | same state count |
| SCC count | 136 | 88 | different |
| terminal classes | 24 | 24 | same count, not decisive |
| terminal states | 48 | 96 | different |
| cycle periods | all 2 | all 4 | different |

The B constraint is satisfied: both directed orders are preserved by `order_preservation_samples()` and `phase_test["verdict"]` gates on both, at `ring_checkerboard_automaton_v0_common.py:664-702` and `930-947`.

Important caveat: `signatures_equal()` compares the whole `partition_signature`, including the `discipline` string. For alternating-vs-paired this means the packet's internal `terminal_structure_distinguishable` would still become true from a label field. My independent recomputation stripped the claim down to structural fields (`scc_count`, terminal state count/sizes, period histogram, tail histogram), and the distinction remains. Future validators should compare a stripped signature that excludes `discipline` and any phase/name labels.

## Locality reality

Adjudication: PASS for the declared single-token local rule.

The active transition path is local:

- `same_ring_neighbor()` moves only to predecessor/successor on the current ring.
- `attachment_neighbor()` only connects a base step to the attached ring at that step, or attached step 0 back to its base anchor.
- `paired_partner()` uses the adjacent cell selected by local parity.
- `transition_state()` applies the chosen phase/update discipline without querying aggregate graph state.

No global terminal counts, SCCs, labels, or future state summaries are consulted by the update rule. The global analysis happens after the graph is built, which is appropriate.

Scope caveat: because the state is a single active token, locality means token-local movement on an owner-shaped support. It is not yet a homogeneous update of a full binary configuration over every cell.

## Nesting row

Adjudication: PASS for "one attached-ring level changes terminal structure"; size-count caveat closed by audit control.

Packet-native row:

- Nested `n=8`: 72 support cells, 1152 intrinsic states, 224 terminal classes, 672 terminal states.
- Bare `n=8`: 8 support cells, 128 intrinsic states, 32 terminal classes, 96 terminal states.

That proves the attached-ring construction changes the realized graph, but by itself it confounds nesting with larger support/state count.

Size-matched audit control:

- Nested `n=4`: 20 support cells, 320 intrinsic states, 48 terminal classes, 144 terminal states, SCC count 224.
- Bare `n=20`: 20 support cells, 320 intrinsic states, 80 terminal classes, 240 terminal states, SCC count 160.

So the nesting effect survives a support/state-count match. Future v1 should add this size-matched control to the packet and validator.

## Controls and falsifier reachability

Adjudication: PASS.

Fresh audit recomputation at `n=4`:

- order shuffle changed dynamics: true.
- label rotation preserved counts/signature: true.
- frozen phase changed dynamics and exposed degeneracy: period histogram became `{"1":320}`.
- non-partitioned scramble changed dynamics: true.
- checkerboard-off changed dynamics: true.

The branch bodies are reachable in real code:

- non-partitioned scramble path executes `checkerboard=False` at `ring_checkerboard_automaton_v0_common.py:386-408`.
- frozen-phase path executes only phase 0 at `ring_checkerboard_automaton_v0_common.py:409-420`.
- controls are constructed and gated at `ring_checkerboard_automaton_v0_common.py:721-804` and `966-984`.

The similarity-only row is correctly barred from basin language, but it is a declared guard row rather than a deep mathematical falsifier. That is adequate for this packet's basin-contract hygiene.

## Fences and overclaim audit

Adjudication: PASS.

No accepted 64/engine-placement claim. The packet reports `{4,8,16}` microstate rows, with `reachable_later=[32,64]`, and the nesting claim ceiling says no 32/64 or engine-placement claim.

No QCA/index row. No quantum state claim. No Axis0 closure, manifold admission, cosmology, consciousness, or physics claim is accepted. Class language stays chart-relative to the transition graph and terminal SCC partition.

Future citation rule: cite this packet only as a local classical `scratch_diagnostic` showing an owner-shaped flat ring-checkerboard single-token automaton with local update rules, basin partition rows, controls, and alternating/paired structural separation. Do not cite it as a full CA over all cell configurations, QCA/index evidence, engine placement, Axis0 support admission, or 64-row result.

## SMT and tool honesty

Adjudication: PASS for scratch diagnostic; note proof granularity.

The Python z3/cvc5 proofs bind computed values (`scc_count`, `terminal_class_count`, `terminal_state_count`) and assert erased equality; the perturbation flip sets paired fields to alternating fields and returns SAT. See `z3_phase_proof()` and `cvc5_phase_proof()` at `ring_checkerboard_automaton_v0_common.py:807-905`.

This is a real computed-value flip, not a pure declared-enable. It is also aggregate-level, not a proof over full graph isomorphism or all transition edges. Julia's Z3 proof is thinner still, binding only SCC count. Acceptable ceiling: solver-backed aggregate separation for a scratch packet.

Backend scope:

- Julia, JAX, PyTorch, and envelope reran in `/tmp/rcaudit_rerun.FSnwZ2` with `ok:true`.
- Live strict envelope validator passed read-only:
  `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/ring_checkerboard_automaton_v0/results/ring_checkerboard_automaton_v0_envelope_results.json`
- Packet-local validator writes by design, so I reran it in scratch only; scratch result returned `ok:true`.
- Pytest rerun used `-p no:cacheprovider` and returned `6 passed`.

## QCA/index v1 requirements

Before any QCA/index citation, v1 needs:

1. Full classical-hardening first: stripped label-free phase signatures in validator, size-matched nesting control in packet, and explicit statement that v0 is single-token unless a full configuration CA is added.
2. A genuine local update on full finite configurations, or a clearly separate reason why the single-token carrier is the intended classical floor.
3. Quantum rule definition as local unitary/CPTP maps on the ring-checkerboard support.
4. Computed GNVW/index or finite proxy with L/R opposite-sign engines and index-0 non-chiral control.
5. Falsifier branches that execute: erased chirality, swapped handedness, nonlocal update, label permutation, order shuffle, and zero-index control.
6. No promotion from v0 tables to 64/engine placement unless the exact 32/64 rows are computed and fenced against engine-placement overclaim.

Accepted ceiling: `passes local rerun` for a source-shaped, local, classical, single-token ring-checkerboard automaton scratch diagnostic.
