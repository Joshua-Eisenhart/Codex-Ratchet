# Independent audit verdict - spinor_network_surface_v0

Verdict: REJECT the headline doctrine claim. Retain the packet only as an
on-disk, validator-passing `scratch_diagnostic` finite n4 product-spinor
fixture. Do not cite it as evidence that the spinor-network surface recovers
the committed A-chart from an independent network substrate, and do not cite it
as a full basin-contract pass.

Public repo status label: `passes local rerun` for the generic three-engine
validator, packet-validator logic, pytest, and local recomputation probes run
in this audit. Packet ceiling remains `scratch_diagnostic`;
`promotion_allowed=false`; `formal_admission_allowed=false`.

The decisive failure is the A-chart recoverability row. The packet computes
single-site partial traces and Bloch coordinates, but it computes them from
hardcoded Pauli-axis product-spinor stored patterns. The six recovered cells are
therefore the six Pauli-axis cells already built into the seed patterns:

- `A33_xp10_y00_z00`
- `A33_xm10_y00_z00`
- `A33_x00_yp10_z00`
- `A33_x00_ym10_z00`
- `A33_x00_y00_zp10`
- `A33_x00_y00_zm10`

Worse, the registered no-structure falsifier is not genuinely reachable through
the implemented verdict predicate. `chart_cell_id()` emits the Bloch origin as
`A33_x00_y00_z00`, while the failure predicate checks for
`A33_x0_y0_z0`. A flat/maximally mixed quotient therefore returns
`partial_recovery_nontrivial` with only the origin cell instead of firing the
registered falsifier.

## Standards Applied

Authorities read in this audit:

- `AGENTS.md`
- `CODEX.md`
- `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`
- `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`
- `system_v5/docs/LEGO_SIM_CONTRACT.md`
- `system_v5/ops/SIM_FULL_WIZARD_PARALLEL_RUNBOOK.md`
- `system_v6/receipts/owner_doctrine_spinor_network_surface_20260611.md`
- `system_v6/receipts/spinor_network_surface_estate_20260611.md`
- `system_v6/receipts/attractor_basin_criterion_20260611.md`
- `system_v6/sims/spinor_network_surface_v0/build_card.md`

Git anchors verified:

- `833af4937f06aa682ea332dd0bb65aee649c6f0b` contains the owner doctrine.
- `0dc215ad30cf591ee40d6f59982a1420bd30b47e` contains the repaired estate
  receipt.
- The three authority receipts had no current diff during this audit.
- `system_v6/sims/spinor_network_surface_v0/` is currently untracked in this
  checkout.

## Fresh Checks

Commands/checks run without git mutation:

- Runtime doctor:
  `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py --json`
  returned `summary.ok=true`.
- Generic validator:
  `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/spinor_network_surface_v0/results/spinor_network_surface_v0_envelope_results.json`
  returned `ok=true`.
- Packet validator logic was rerun in-process without invoking its writing
  `main()`; result: `ok=true`, `error_count=0`.
- Pytest was run with `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider`;
  result: `2 passed`.
- Local recomputation of chart rows, coupling hermiticity, basin deltas, typed
  rows, and L/R signatures was performed via `core_surface_result()` and helper
  functions under `PYTHONPATH=system_v6/sims/spinor_network_surface_v0`.

Fresh recomputation values:

- `hermitian_residual_recomputed = 0.0`
- `max_lyapunov_delta_recomputed = 0.0`
- Lyapunov deltas:
  `[0.0, -0.15000000000000002, 0.0, -0.15000000000000002, 0.0, -0.15000000000000002, 0.0, -0.15000000000000002, 0.0, 0.0]`
- `nonhermitian_imag_energy_abs = 0.42677669529663675`
- `recovered_chart_cells = 6`
- Flat/maximally mixed falsifier probe:
  `flat_recovery = partial_recovery_nontrivial`,
  `recovered_cell_ids = ['A33_x00_y00_z00']`

## Decisive Chart-Recoverability Audit

Code path traced:

- Stored patterns are hardcoded in `pattern_rows()` as Pauli-axis labels:
  `L0=['x+','y+','z+','x-']`, `L1=['z+','x+','y+','z-']`,
  `R0=['x+','y-','z+','x-']`, `R1=['z+','x+','y-','z-']`
  (`spinor_network_surface_v0_common.py:149-155`).
- `build_patterns()` turns those labels into product states and density
  matrices (`spinor_network_surface_v0_common.py:162-171`).
- `chart_recoverability(patterns, retrieval)` loops over the stored patterns,
  ignores its `retrieval` argument, computes each single-site reduced density,
  computes Bloch coordinates, bins with `chart_cell_id()`, and counts recovered
  cells (`spinor_network_surface_v0_common.py:299-337`).
- The check is a real density-to-Bloch computation, but the network states are
  seeded from exactly the Pauli-axis spinors whose single-site quotients are the
  six recovered cells. That is by-construction partial recovery, not independent
  recovery of committed A-chart row structure from terminal network dynamics.

Manual recomputation for two network states:

- `L0=['x+','y+','z+','x-']` recovered:
  `A33_xp10_y00_z00`, `A33_x00_yp10_z00`,
  `A33_x00_y00_zp10`, `A33_xm10_y00_z00`.
- `R0=['x+','y-','z+','x-']` recovered:
  `A33_xp10_y00_z00`, `A33_x00_ym10_z00`,
  `A33_x00_y00_zp10`, `A33_xm10_y00_z00`.

What failure should have looked like:

- The implemented failure branch says the verdict should be
  `failed_registered_falsifier_no_nontrivial_structure` when the recovered set
  is empty or is only the Bloch origin (`spinor_network_surface_v0_common.py:317-319`).
- That branch is effectively broken for the origin case because the literal
  string is wrong. A flat quotient returns origin-only recovery but still gets
  `partial_recovery_nontrivial`.
- The packet-local validator then requires `partial_recovery_nontrivial` and
  `recovered_cell_count > 1` (`validate_spinor_network_surface_v0.py:124-129`),
  so it does not test the registered falsifier.

Adjudication: doctrine expectation 2 FAILS.

## Strict-Carrier Reality

Passable narrow evidence:

- The carrier is finite n4/dim16 with 4 sites, 5 edges, and 2 faces
  (`spinor_network_surface_v0_common.py:19-22`, `:543-551`).
- The coupling matrix is Hermitian by construction:
  `J_ji=conj(J_ij)` on support edges (`spinor_network_surface_v0_common.py:174-182`).
  Fresh recomputation returned residual `0.0`.
- `V(rho)=1-max_mu Tr(|P_mu><P_mu| rho)` is computed and monotone over the
  declared seed rows (`spinor_network_surface_v0_common.py:194-198`, `:251-268`).

Hard caveats:

- The stored-pattern construction is not source-quoted from the repaired estate
  paths. It is hardcoded locally as Pauli-axis product spinors.
- The envelope still lists stale missing consume paths for `basin3` and `npc2`:
  `system_v6/sims/basin3_hopfield_chiral_quaternion_network/basin3_julia.jl`
  and `system_v6/sims/npc2_connection_geometry/npc2_connection_geometry_julia.jl`
  (`spinor_network_surface_v0_envelope.py:35-44`;
  envelope result `consumed_inputs` records both as `exists=false`). The true
  repaired paths exist under `system_v5/julia_carrier/`.
- The retrieval dynamics is an argmax/threshold classifier plus terminal
  replacement (`spinor_network_surface_v0_common.py:227-241`), not an
  independently integrated dissipative Hopfield trajectory. Its "CPTP-class"
  status is declared as a string (`spinor_network_surface_v0_common.py:560-562`);
  the packet validator only checks that the string contains `CPTP`
  (`validate_spinor_network_surface_v0.py:107-110`).
- The exact `max_lyapunov_delta=0.0` is not suspicious by itself; it follows
  from the retrieval map. Stored and spurious rows stay fixed, while corrupt
  rows are replaced by stored patterns. This supports a bounded monotone seed
  fixture, not a full dynamical basin.
- The non-Hermitian control does not demonstrate a break of the same Lyapunov
  functional. It checks non-Hermitian residual plus imaginary Hopfield energy
  (`spinor_network_surface_v0_common.py:409-431`, `:493-498`), while the
  monotone functional is `1-max fidelity`. Therefore "non-Hermitian breaks
  Lyapunov" is overworded.

Adjudication: strict finite Hermitian carrier witness PASSES narrowly; strict
quantum-Hopfield/dissipative carrier claim FAILS.

## Basin Contract

The packet includes the basin-contract fields `S`, `Adm_C`, `M_C`, `R_C`, a
terminal partition, spurious terminal class, and the seven named negative
controls (`spinor_network_surface_v0_common.py:273-296`, `:432-507`).

Audit result:

- Trapping and absent-exit evidence are set directly to `True` in the partition
  table (`spinor_network_surface_v0_common.py:273-283`).
- Escape evidence is only `steps_to_terminal <= 1` over 10 declared seed rows,
  not an independent boundary/exit graph.
- Spurious attractor search is two seeded equal-mixture probes
  (`spinor_network_surface_v0_common.py:212-223`). This is useful as a
  spurious-family fixture, but it is not a hard search over a small carrier.
- THE GUARD similarity-only control is present, but it is a reason-string
  failure, not an executed rival clustering dynamics.
- The other controls are mixed: pure-gauge and overload compute small values,
  while several mandatory controls are declarative boolean/prose rows.

Adjudication: basin-contract fixture EXISTS and passes validator shape; full
basin contract FAILS.

## Typed Row S(A|B)

Passable narrow evidence:

- The packet declares the bipartition `A=[0]`, `B=[1,2,3]`.
- `typed_information_rows()` computes trajectory density rows, reduced
  densities, von Neumann entropies, `S(A|B)`, and `I(A:B)`
  (`spinor_network_surface_v0_common.py:340-390`).
- Fresh recomputation returned three trajectory rows. Values are approximately
  zero for `S(A|B)` and mutual information because the terminal stored patterns
  are product states; the packet states this caveat.

Caveats:

- The source hardcodes the split during evaluation before emitting the
  `bipartition_declared` record. This is weaker than a separate predeclared
  co-ratchet structure object.
- The premature evaluation failures are recorded controls
  (`MissingStructure:*`) rather than actual exception paths.
- Julia reports row count only, not the row values.

Adjudication: doctrine expectation 3 PARTIAL. A typed row is computed, but it
does not yet reproduce chart-level values in a meaningful weld-anchor sense or
expose strong network-level structure invisible to charts.

## L/R Chiral Row

The L/R row passes its bounded claim:

- Left/right pattern families are explicitly distinct in the stored patterns
  (`spinor_network_surface_v0_common.py:149-155`).
- `lr_hook()` distinguishes left vs right under the declared probe family:
  single-site Bloch quotient cells plus retrieval terminal partition
  (`spinor_network_surface_v0_common.py:393-406`).
- The emitted row fences itself from engine/64 claims.

Caveat: the distinction is the hardcoded `y+` vs `y-` site in the product
patterns. It is a bounded quotient/partition distinction, not broader chiral
network evidence.

Adjudication: L/R hook PASSES narrowly at scratch ceiling.

## Cross-Engine And Tool Honesty

Cross-engine agreement is real only for selected scalar rows:

- JAX and PyTorch both import `core_surface_result()` from the same NumPy common
  module (`spinor_network_surface_v0_jax.py:21-33`;
  `spinor_network_surface_v0_pytorch.py:16-27`;
  `spinor_network_surface_v0_common.py:510-590`).
- Julia performs some separate package checks, but its key scalar/proof rows are
  hardcoded: `fill(0, 10)`, `426777`, fixed chart count, fixed terminal count
  (`spinor_network_surface_v0_julia.jl:55-84`, `:134-166`).
- The envelope comparison covers only `max_lyapunov_delta`,
  `recovered_chart_cells`, and `terminal_class_count`
  (`spinor_network_surface_v0_envelope.py:104-124`).

SMT:

- JAX/PyTorch z3/cvc5 rows bind computed Lyapunov deltas and a computed
  non-Hermitian perturbation scalar, producing UNSAT/SAT flips. This is
  non-tautological for the narrow monotonicity fixture.
- Julia Z3 is weaker because the values are hardcoded in the Julia lane.
- The SMT does not repair the chart-circularity/falsifier failure and does not
  prove a full basin.

PyTorch:

- `torch_geometric` checks graph shape.
- `torch.func` computes `jacrev/vmap` over `sum(row*row)` on the absolute
  coupling matrix (`spinor_network_surface_v0_pytorch.py:35-59`).
- This is supportive shape/sensitivity evidence, not a load-bearing
  energy-descent or retrieval-dynamics path.

Validators:

- Generic three-engine validator passed fresh.
- Packet-validator logic passed fresh in-process without writing.
- Existing on-disk packet validator receipt is `ok=true`.
- The envelope's `validator_statuses` list is empty; it has
  `validator_expected_commands`, not embedded fresh statuses.

## Per-Expectation Adjudication

1. Finite quantum-Hopfield carrier admits a basin partition passing the full
   basin contract: FAIL as full claim. PASS only as a finite Hermitian n4
   product-spinor fixture with declared seed partition and weak spurious probe.
2. A-chart rows recoverable as quotient readouts of network state: FAIL. The
   six-cell recovery is by-construction from Pauli-axis product patterns, and
   the no-structure falsifier is broken.
3. Typed information rows computed on network channels reproduce chart-level
   values and expose network-level structure: PARTIAL. The row is computed and
   typed, but the values are nearly degenerate/product-state telemetry, the
   channel/retrieval object is weak, and the weld-anchor requirement is not met.

## Named Caveats

- `A_CHART_BY_CONSTRUCTION`: recovered cells are seeded by hardcoded Pauli-axis
  product spinors.
- `FALSIFIER_STRING_MISMATCH`: origin-only recovery does not fire the registered
  falsifier because `A33_x0_y0_z0` is not the emitted origin cell id.
- `STALE_CONSUMED_PATHS`: envelope preserves missing stale `system_v6/sims/...`
  paths for `basin3` and `npc2`; repaired paths live under
  `system_v5/julia_carrier/`.
- `DECLARATIVE_CPTP`: retrieval admissibility is a string/validator check, not a
  Kraus/Choi/trace-positivity proof of the actual map.
- `BOOLEAN_EXIT_EVIDENCE`: trapping and absent-exit are direct booleans over a
  tiny seed set, not boundary/escape graph evidence.
- `NONHERMITIAN_WRONG_ROW`: non-Hermitian control breaks complex Hopfield energy,
  not the actual `V(rho)=1-max fidelity` Lyapunov row.
- `SHARED_COMMON_MODULE`: JAX/PyTorch agreement largely echoes one common NumPy
  implementation.
- `JULIA_SCALAR_STUB`: Julia lane hardcodes key scalar/proof rows.
- `PYTORCH_SUPPORTIVE_NOT_LOAD_BEARING`: PyTorch checks graph shape and simple
  sensitivity, not retrieval energy descent.
- `POST_AUDIT_BOUNDARY`: builder-phase `no_builder_audit_verdict` is valid before
  this file exists; post-audit validation must use a post-audit phase or the
  builder gate will correctly become stale.

## Future-Citation Rule

Future docs may cite this packet only as:

> `spinor_network_surface_v0`: validator-passing, untracked-on-audit
> `scratch_diagnostic` n4 product-spinor finite-carrier fixture with Hermitian
> support-edge coupling, a weak seed-set retrieval partition, six
> by-construction Pauli-axis A-chart quotient cells, a scoped typed
> conditional-vN row, and a bounded L/R hook. The independent audit rejected the
> chart-recoverability headline and full basin-contract claim.

Forbidden citations:

- proof that Families A/B are views of this network surface;
- proof that the A33 chart is recovered from independent network dynamics;
- proof of a full quantum-Hopfield basin object;
- proof of independent all-three backend agreement;
- proof that PyTorch energy descent is load-bearing.

## What Surface v1 Must Add

1. Repair consumed-input lineage so every authority/source path exists and
   points to the repaired estate paths; quote the source lines used for stored
   patterns and Hopfield construction.
2. Separate the A-chart classifier from network-state generation. Predeclare the
   committed chart row set, then generate terminal network states without
   hardcoding Pauli-axis chart cells as the stored patterns.
3. Fix the falsifier string and add explicit no-structure controls: maximally
   mixed state, quotient-erased state, rotated/off-axis states, and a wrong-row
   chart classifier. The no-structure case must fail.
4. Replace the argmax replacement map with an explicit finite transition graph
   or a real CPTP/Kraus/Lindblad-class retrieval channel. Prove trace,
   positivity, and the exact update relation.
5. Compute trapping, absent exits, and boundary/escape evidence from the
   transition relation, not booleans.
6. Search spurious attractors harder: exhaustive where feasible for the n4
   finite abstraction, or a bounded enumerated/sampled search with a declared
   coverage denominator and negative controls.
7. Make the non-Hermitian control break the same Lyapunov/monotone row used by
   the positive basin claim, or demote the control to complex-energy sanity.
8. Make Julia independently recompute chart, basin, typed, and SMT rows rather
   than hardcoding selected scalars. Make JAX/PyTorch implementations independent
   enough that agreement is not common-module echo.
9. Make PyTorch load-bearing by wiring autograd/torch.func to the actual
   retrieval energy descent, update stability, or demotion condition.
10. Turn premature typed-row controls into actual structural failures or
    exceptions, then test them.
11. Store validator statuses or a fresh validation receipt without mutating
    builder outputs during audit; keep the post-audit validator path idempotent.
12. Keep v1 at `scratch_diagnostic` until the above are repaired and independently
    audited.

## Route Truth

Wizard v4.2 Max Assembly was partial, not full. Three Codex-native read-only
parent subagents completed independent slice audits:

- strict carrier / basin contract;
- consumed paths / envelope / validators / cross-engine / tool honesty;
- typed row / L-R chiral row.

No child subsubagent layer was completed. No Claude/Gemini/OMX route was used.
No `git add` or `git commit` was run. The only intentional repo write in this
audit turn is this `audit_verdict.md` file.
