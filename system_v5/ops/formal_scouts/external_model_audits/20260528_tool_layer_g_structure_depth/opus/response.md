## 1. Verdict

**PARTIAL_ON_TRACK.** The packet executes the right *structural* move for this stage: keep layers, G-structure candidates, and geometry surfaces as separate sim surfaces; refuse promotion; lock every downstream consumer (selection, embedding, stacking, flux, Xi/Phi0, Axis0, FEP, gravity, manifold). Boundary discipline is clean — classification=formal_scout, promotion_allowed=false, Bloch adapter rejected, scalar entropy demoted to readout, no single blended all-tools claim. What it does *not* yet earn is tool *depth*: each of the 15 tools is exercised through exactly one `function_surface`, and the stop condition for "we have actually worked this tool through all layer/G/geometry surfaces" is satisfied at the breadth axis but not yet at the per-tool internal axis. That's the canonical shallow risk the frame names, and it's present here.

## 2. Findings

- **P1 — One function_surface per tool is breadth-coverage, not depth.** `new_tool_by_tool_result.tool_rows` shows each tool with a single surface (e.g. `pytorch: torch autograd over relative spinor phase`, `quimb: quimb PEPS2D/PEPS3D construction`). The packet itself acknowledges this in `next_admissible_step` and proposes deepening. This is the active shallow spot, not a regression — but must not be treated as "tool worked through all layers" yet.
- **P1 — z3 and cvc5 ablations classed `map_unprovable` need non-vacuous audit.** `tool_ablations.z3` and `tool_ablations.cvc5` differ from the other 13 tools (which use `claim_fails`). Prior fabrication-incident memory and the repo's z3-UNSAT primacy doctrine both warrant reading the actual solver calls before counting these toward load-bearing depth. Packet alone cannot verify the constraint encodings are non-trivial.
- **P2 — Minimum mutual information ≈ 0.017 (L3 Clifford/quaternion) is small.** `min_mutual_information=0.016930…` and `min_log_negativity=0.07495…` are above zero but close enough to the floor that a single change in carrier seeding could flip a row. No floor-margin / seed-variation table in the packet.
- **P2 — `selected_official_g_structure: null` is correct, but no explicit "separability between layer rows and G-structure rows" probe is present.** The packet treats them as orthogonal axes; a future-relevant gate is that no layer row's pass *implicitly depends* on G-structure choice and vice versa.
- **P3 — `tool_ablations.*.stub_action` strings are descriptions, not committed code paths.** No evidence in the packet that the stub was actually executed and that `claim_delta=claim_fails` came from a rerun rather than from the sim's internal assertion.
- **P3 — `elapsed_seconds=25.19` at site_count=64 with bond=4 is fast.** Plausible for finite carriers, but no peak-memory / contraction-cost telemetry is in the receipt, so resource fences mentioned for the next packet ("resource-fenced 8/16/32/64 stress") have no current baseline to compare against.

## 3. What is genuinely earned

- A standalone tool-by-tool layer/G-structure/geometry **formal scout** receipt with `classification=formal_scout`, `promotion_allowed=false`, and 10 explicit blocked consumers.
- 44 layer rows × 9 layers and 48 G-structure rows × 12 candidates recomputed without the Bloch adapter, with torch-native spinors as the primary state and entropy as derived readout.
- 15-tool one-by-one ordering (`tool_order` matches the announced order; not blended).
- Non-vacuous ablation pattern for 13/15 tools (`claim_delta=claim_fails` plus `non_vacuous=true` per row).
- PEPS3D bond-4 carrier embedded for *every* row, 8/16/32/64 scale preserved.
- Locked consumer set matches the user's strict frame exactly.
- Lint + fresh validator rerun + 18 dependency-receipt fresh reruns all clean.

## 4. What is not earned and must stay locked

- Official G-structure selection.
- Layer embedding into any G-structure.
- Stacking, cross-layer order closure, post-stack stress.
- Flux, Xi/Phi0, Axis0, FEP/Holodeck, physics/gravity, IGT, axes 7–12, final manifold admission.
- Tool-tool coupling (the next stage in `repo_gates.tool_stage_order` is still in front of this work; the current receipt is at the micro tool/function stage).
- "Tool worked through all surfaces" in a load-bearing sense — *one* surface per tool is admitted; deeper surfaces are TBD.
- z3/cvc5 load-bearing claims (until the `map_unprovable` calls are audited as non-vacuous).
- Floor-stability across seeds (no seed sweep in receipt).

## 5. Shallow / fake-depth risks

- **Single-surface-per-tool fallacy.** A 15-row "all tools passed" table is rhetorically strong but each tool only proved one function. Calling this "every tool worked through every layer/G/geometry" would be the same drift as previous incidents.
- **Ablation surface-narrowness.** If a tool's `function_surface` is narrow, removing it will of course break the claim — the ablation tests narrow load-bearing, not deep load-bearing.
- **z3/cvc5 vacuous-solver risk** — recurring failure mode in this repo's history (fabrication memory). The `map_unprovable` delta needs source-read confirmation.
- **Floor-margin fragility** at L3 mutual_information ≈ 0.017.
- **PEPS3D "embedding" via bond-4** may be a finite *view* rather than a load-bearing contraction; without contraction-cost or peak-memory receipts, "PEPS3D carrier" is being asserted, not measured.
- **All-pass momentum** — 92 rows × 15 tools all green in 25s is exactly the shape the harness has been burned by before. The boundary discipline is sound this time; the risk is the *next* turn rolling this forward as if it were tool-tool coupling readiness.

## 6. Next 5 bounded packets (priority order)

1. **pytorch_autograd_per_row_depth_packet** — replace the single global relative-phase witness with per-layer and per-G-structure gradient maps; add left/right Weyl separation; record peak memory at 64 sites. **Stop:** fresh validator rerun passes with one gradient receipt per layer row *and* per G-structure row, finite norm bounded from zero, plus an explicit resource ceiling row.
2. **z3_cvc5_non_vacuous_depth_audit_packet** — audit the existing z3/cvc5 surfaces by reading the actual SMT constraints and adding a positive-control (a row that SHOULD be SAT) and a negative-control (a row that SHOULD be UNSAT). **Stop:** receipt records control-row outcomes matching expectations and lists the exact constraint formula per row; no `map_unprovable` rows count toward depth until both controls hit.
3. **clifford_twistor_hopf_algebraic_depth_packet** — push Clifford/SymPy beyond identities into a full Hopf / nested-tori / Clifford-torus / twistor reduction graph at 16/32/64 sites with quaternion-invariant checks. **Stop:** fresh rerun passes or the first algebraic relation that cannot be expressed over a finite carrier is recorded as a blocker artifact.
4. **quimb_cotengra_peps3d_contraction_depth_packet** — independent PEPS2D and PEPS3D contraction variants per layer/G-row with contraction-cost + memory telemetry; verify the carrier is load-bearing, not nominal. **Stop:** receipt records contraction cost and peak memory per row and a control row where contraction is forced to fail.
5. **topology_hypergraph_persistence_layer_separability_packet** — PyG / rustworkx / XGI / TopoNetX / GUDHI deepened with an explicit *separability* check: layer row's pass does not depend on G-structure choice, and vice versa, at fixed site count. **Stop:** receipt either confirms separability across all (layer, G) pairs at 32 sites or names the first pair where it fails.

## 7. Falsifier

If the next two tool-depth packets each add only one additional `function_surface` per tool and again report `all_pass=true` with `claim_delta=claim_fails` from narrowly-scoped stubs — without per-row gradient/contraction-cost/SMT-control receipts — then the campaign is producing more breadth-flavored "all-pass" rows instead of depth, and tool-stage drift has restored itself under cleaner boundary discipline.

## 8. One sentence for the formal sim TUI

The single-surface-per-tool depth scout passes boundary discipline cleanly and is admitted as a formal scout, but tool depth is not yet earned; run the pytorch per-row autograd packet next, audit z3/cvc5 for non-vacuous solver use before counting them, and keep selection / embedding / stacking / Xi/Phi0 / Axis0 / FEP / gravity / final manifold locked.