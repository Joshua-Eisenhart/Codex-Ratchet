# Fresh cross-backend audit verdict -- carnot_szilard_basin_cycle_v0

Bottom line: `GENUINE-WITH-CAVEATS`.

The packet earns the core bounded claim: `m_sample=9` is recomputed from the actual parent RETURN trajectory rows, `m_full_graph=33` is recomputed in the packet controller from the 33-cell transition graph as the single-terminal full-carrier reading, floor arithmetic matches panel 7, closure defect is zero under a packet-local state-plus-record table, erased/misledgered/less-than-floor falsifiers flip the gates, and the classical/physics fences are preserved.

It is not clean enough for an uncaveated `GENUINE` citation. The full-graph `m=33` must be cited only as the full 33-cell single-terminal carrier reading, not as sampled perturbation evidence. The three engine lanes are source-backed and pass the strict validator, but they are not three fully independent recomputations of the parent trajectory graph. Boundary content is preserved, but the six stroke-map boundaries are not carried byte-for-byte verbatim in every emitted boundary surface.

## Verdict

- Repo verdict: `GENUINE-WITH-CAVEATS`.
- Classification ceiling stays: `scratch_diagnostic`.
- Promotion: `promotion_allowed=false`, `formal_admission_allowed=false`.
- Future citation status: cite as a bounded typed-counting connection packet only.

Rejected stronger readings:

- Not `GENUINE` without caveats because cross-engine independence and verbatim-boundary carriage are not clean.
- Not `DECORATIVE`: the sample floor, full-carrier floor, closure, SMT flips, and alternation coefficient check are computed and gate-bearing.
- Not `BY_CONSTRUCTION`: the floor rows are formulaic after `m`, but `m_sample=9` and the controller `m_full_graph=33` are earned from parent trajectory/graph structure, not only typed in from the map.
- Not `FABRICATED` or `BROKEN`: local validators and fresh read-only recomputation agree.

## Decisive Floor Check

`m_sample=9` is real for the RETURN rows. I traced `G0` directly from parent `trajectory_rows`: the distinct sampled perturbed cells are `[0, 2, 3, 5, 15, 16, 17, 30, 31]`, all returning to terminal cell `16`. That gives `m=9` before any `ln(m)` arithmetic.

`m_full_graph=33` is honest only under the explicitly scoped full-carrier reading. The packet controller recomputes it by iterating all 33 cells in the parent graph and checking `shortest_terminal_path(cell, graph)` against terminal class `[[16]]`; all 33 cells merge to the accepted terminal. That is not count inflation when cited as `full_graph`, but it would be count inflation if cited as the sampled perturbation branch count.

Fresh recomputation:

- `G0`: `m_sample=9`, `m_full_graph=33`.
- `G2`: `m_sample=9`, `m_full_graph=33`.
- `stage_shift_Rx_to_Rz`: `m_sample=9`, `m_full_graph=33`.
- Floors: `log(9)=2.197224577336220`, `log(33)=3.496507561466480`.

## Per-Expectation Adjudication

1. `THE BASIN-CYCLE LEDGER`: passes with caveat `G4`.
   The packet constructs packet-local syndrome tables for perfect, erased, and over-recorded records. Closure is computed separately from spatial return, with `ledger_defect_nats=0.0`, `cross_type_sum=false`, and reset charge equal to retained record size.

2. `THE BASIN-LANDAUER FLOOR`: passes with caveat `G1`.
   For both `sample` and `full_graph` readings, the floor is exactly `ln(m)` in typed counting nats. The erased-record control binds the full floor, and a less-than-floor paid/dissipated row flips both solver gates to `sat`, meaning the violation is caught.

3. `THE STRUCTURE MAP`: passes with caveat `G3`.
   The emitted map preserves the Carnot/Szilard/basin mechanic columns and keeps the heat/work/bath/admission boundaries. It does not smuggle basin heat/work/bath mechanics. However, strict verbatim carriage is not perfect across the emitted boundary strings, so future citations should quote the stroke-map receipt or this audit's citation rule, not paraphrased packet boundary text.

## Panel-Match Table

| Panel 7 target | Packet value/check | Adjudication |
|---|---|---|
| Floor `ln(m)` | `m_sample=9`, `floor=log(9)`; `m_full_graph=33`, `floor=log(33)` | Pass. `m_sample` is trajectory-earned; `m_full_graph` is full-carrier-earned only. |
| Closure relation `dissipation >= ln(m)-r` | Perfect record has `r=ln(m)`, immediate dissipation analog `0`, reset charge `ln(m)`, closure defect `0` | Pass. Packet-local record table, not Z4 carrier reuse. |
| Honesty clause | Perfect record does not make a free cycle; reset charge remains `ln(m)` | Pass. Erased/misledgered/less-than-floor falsifiers flip. |
| `2ue[A,B]` alternation gap | `u=e=1e-3`; observed gap norm `2.828428538852792e-6`; `2ue[A,B]` relative error `4.99962184e-7` | Pass with caveat. One stroke size, not a scaling sweep. |
| Commuting control | `U=I+uA`, `E=I+e(2A)` gives gap `0.0` | Pass. |
| Wrong-coefficient control | `1ue[A,B]` relative error about `1.000001`; `3ue[A,B]` relative error about `0.333333` | Has teeth: wrong coefficient mismatches. |

## Circularity Audit

1. Anchor-by-copy circularity: cleared for `m_sample=9` and controller `m_full_graph=33`; not cleared as three independent engine recomputations. The map's candidate counts are not merely echoed by the controller, but engine lanes lean on shared/common objects or parent JSON.

2. Map-echo circularity: mostly cleared for the floor rows. The structure-map table is still a map emission grounded in prior receipts, not a new independent archaeology pass.

3. Common-code validator circularity: partially present. The packet validator rebuilds through `carnot_szilard_basin_cycle_v0_common.py`, the same common builder used by the packet. Fresh read-only tracing of parent `G0` and direct object/result hash comparison mitigate this, but do not remove the caveat.

4. SMT constant-binding circularity: acceptable but bounded. Z3/cvc5 bind scaled integer values derived from the recomputed rows and catch erased/misledgered/less-than-floor controls. They do not independently derive the trajectory graph or symbolic logarithms.

## Named Caveats

- `G1_full_graph_scope`: `m_full_graph=33` is the accepted full-carrier merge reading. Cite it only with `m_source=full_graph`; the sampled RETURN trajectory floor remains `m_sample=9`.
- `G2_cross_engine_independence`: strict three-engine/source-backed validation passes, but the lanes are not three fully independent graph recomputations. JAX/PyTorch validate common-built values with tool-backed probes; Julia uses parent RETURN fields for full counts.
- `G3_boundary_verbatim`: the six honest boundaries are preserved in substance and fences, but not carried byte-for-byte verbatim everywhere.
- `G4_record_model_scope`: the record table is packet-local and follows the Z4 convention, but it is still a finite counting syndrome table, not a thermodynamic record or bath model.
- `G5_alternation_sweep`: alternation is checked at `u=e=1e-3` with a wrong-coefficient control; no multi-scale convergence sweep was run.

## Checks Run

- Read anchors: doctrine `24d03db89`, blind panel `1f8ddb9e1`, stroke map `e0d6f5055`, consumed RETURN parent `f41d4c311`.
- Read packet sources/results under `system_v6/sims/carnot_szilard_basin_cycle_v0/`.
- Fresh read-only recompute via import-level object rebuild:
  - packet validator errors: `0`;
  - rebuilt `basin_cycle_rows` hash matched result JSON;
  - `less_than_floor_z3=sat`, `less_than_floor_cvc5=sat`;
  - erased and misledger branches: `sat` for both z3 and cvc5.
- Ran generic validator read-only:
  - `scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent ...` -> `ok=true`.
- Ran tests with pytest cache disabled:
  - `5 passed`.

## Future Citation Rule

Allowed citation:

`carnot_szilard_basin_cycle_v0` is a `GENUINE-WITH-CAVEATS` scratch diagnostic showing that the committed RETURN rows support a packet-local typed-counting basin-cycle ledger: sampled floor `ln(9)`, full-carrier floor `ln(33)`, zero closure defect under a packet-local syndrome record, floor/honesty SMT falsifiers that flip, and a local D/I alternation check matching `2ue[A,B]` at small stroke size.

Forbidden citation:

Do not cite it as thermodynamic heat/work/bath mechanics, a physical Landauer engine, bridge admission, `M(C)` admission, Axis0 admission, engine placement, QCA/index, manifold admission, discovered absence of scrambling, or three fully independent backend derivations of the parent trajectory graph. Do not cite `m_full_graph=33` without saying it is the full 33-cell single-terminal carrier reading.
