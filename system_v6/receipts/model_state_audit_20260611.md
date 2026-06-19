# Model State Audit - 2026-06-11

Scope: owner state-of-the-model audit from committed evidence only.

Write boundary: this receipt only. No `git add`; no commit.

Standing ceiling: every model row below remains `scratch_diagnostic` unless explicitly marked advisory or pending. No formal admission, bridge/axis, physics, Standard Model, QIT-engine, or `M(C,t)` theorem is claimed.

Route truth: the controller spawned three read-only Codex verification lanes for basin convergence, whole-model pillars, and information/dynamics. They returned after the first draft of this receipt and were folded into this version where they corrected or sharpened the committed-evidence reading. They are verification side evidence only; the cited facts below still come from committed repo artifacts and commit history.

Worktree boundary observed during this audit: this receipt is untracked as the allowed write. The pending basin lanes `system_v6/sims/basin_grid_refinement_control_v0/` and `system_v6/sims/basin_two_engine_joint_v0/` are also untracked and are not summarized as committed evidence.

## 0. Evidence Anchors

| Anchor | Commit(s) | Committed surface | Use in this receipt |
|---|---:|---|---|
| Program status table | `4bd575c08`, patched `9fb6907cc` | `system_v6/receipts/geometry_program_status_20260611.md` | S1-S11, ratchet, fibration, engine, and frontier summary. |
| Stack uniqueness profile | `7bc1af811`, addenda `0d766bb40`, `8f4fef471`, `f7c076f67` | `system_v6/receipts/stack_uniqueness_map_20260611.md` | Unique-by-geometry-and-dynamics, shared-at-topological/IC profile. |
| Basin criterion | `50f16d82d`, may/must patch `000f48e71` | `system_v6/receipts/attractor_basin_criterion_20260611.md` | Basin contract, vocabulary ladder, may/must semantics. |
| Basin pilot | `4e082f525` | `system_v6/sims/basin_criterion_pilot_v0/` | Operational affine criterion, negative affine-subbasin result. |
| Basin partition | `631f1c3db` | `system_v6/sims/basin_rc_transition_graph_v0/` | First finite `R_C` partition, terminal class, may/must split. |
| Basin generating-set sweep | `ba1bfc4d1` | `system_v6/sims/basin_generating_set_sweep_v0/` | First computed finite sub-basin split table. |
| 64 prediction | `d5914f67f`, amended `0bed51ac2` | `system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md` | Pending two-engine 64-product adjudication. |
| Dynamic manifold | `cdf437053` | `system_v6/sims/mct_dynamic_deformation_v0/` | Compression/warp/release ledger and two finite rigidity laws. |
| Entropy ledger | `a54224476` | `system_v6/sims/manifold_entropy_ledger_v0/` | Chain rule, typed entropy table, lens drops. |
| Unified run | `6903e0388` | `system_v6/sims/manifold_unified_run_v0/` | One-sequence n=3 run, step-dependent/invariant rows, in-situ controls. |
| Deep ratchet chain | `7909b1b1b` | `system_v6/sims/ratchet_deep_chain_v0/` | Saturation, branch mortality, exact lens drops `-ln4/-ln2`. |
| Compression-flow record | `eee9a7c41` | `system_v6/sims/compression_flow_radiated_record_v0/` | Finite record/radiation framing and information-loss controls. |
| Engine costs | `123b8e7d8` | `system_v6/sims/engine_stage_word_cost_discriminator_v0/` | Loop-local cost survives at computed sizes. |
| Engine readout | `e2d9d5407`, `f78868aa4` | `engine_readout_strategy_fidelity_v0`, `engine_readout_spinor_lift_v0` | Readout periodicity, 720 lift separation, quotient erasure. |
| S8 gap receipts | `0bd1cdf8a`, `21d6e7249` | `system_v6/receipts/s8_s9_adjudication_20260610.md`, `system_v6/receipts/lifted_ladder_spec_20260610.md` | S8-local `S(A|B)`, `I(A:B)`, and `I_c` table is missing. |

## 1. Basin-Campaign Convergence

### 1.1 Campaign Packet Table

| Row | Hash | What is earned | What splits | What remains open |
|---|---:|---|---|---|
| Criterion contract | `50f16d82d`, `000f48e71` | Basin requires finite `S`, admissible set `Adm_C`, explicit `R_C`, trapping, escape, partition, DoF perturbation, and controls. The may/must split is now contract language: `can_reach_terminal` is existential; `sure_basin_omega_containment` is universal. | No split computed here; this is the vocabulary and gate. | Contract is not a theorem; every later packet must earn the terms. |
| Criterion pilot | `4e082f525` | Criterion became executable on committed affine terrains. `Se_Funnel_L` and `Ni_Pit_L` give one attracting affine fixed point on the whole Bloch ball; bare affine terrains do not expose multiple isolated sub-basins. | None earned at bare-affine level. | Full `R_C`, basin partition, Morse/Conley graph, and sub-basin claims remain unearned here. |
| Finite `R_C` partition | `631f1c3db` | First true finite transition graph: 33-cell admitted Bloch grid, 6 generators, one singleton closed terminal class at the origin, absent-exit proof, all 7 negative controls, zero Lyapunov exclusion violations. | The basin forks by semantics: `can_reach_terminal=33` but `sure_basin/omega-containment=[16]`; 32 nonterminal cells form metastable/leaky structure. | Coarse 33-cell caveat; no refined sub-basin geometry; mostly simple one-terminal-class dissipative set. |
| Generating-set sweep | `ba1bfc4d1` | Partition fate table across `G0/G1/G2/G3L/G3R/G4/G5`; may/must sizes per set; SCCs independently recomputed; controls fire except caveated row-local `G4` control strength. | `G1` rotations-only splits to 3 terminal classes; `G3L` and `G3R` split with different terminal cells but same aggregate signature; `G5` composite word splits. `G2` full set re-merges to 1 terminal class. | Rotation classes are finite 33-cell SCC facts only. No grid-refinement or rotated-grid control yet; no invariant geometry reading yet. |
| 64-product adjudication | `d5914f67f`, `0bed51ac2` | Owner prediction is pre-registered and amended: primary candidate factorization is `2 engines x 2 loops x 4 stages x 4 substages`; product structure required, not count alone. | PENDING. | PENDING: the 64-test is not summarized as committed evidence. Any 64 without earned product decomposition is partial only. |
| Refinement control | `ba1bfc4d1` successor caveat | The needed control is named: grid-refinement/rotated-grid check before geometric interpretation of `G1` classes. | PENDING. | PENDING: continuum-vs-discretization question remains open. |

### 1.2 Convergence Picture

| Question | Current answer | Hashes |
|---|---|---:|
| What converges? | Dissipative/full generating sets converge to one terminal class at the finite 33-cell level. The pilot gives whole-ball affine attraction for named terrain rows; the finite `R_C` graph gives one closed terminal origin class; `G0` and `G2` one-terminal-class rows preserve the glue result. | `4e082f525`, `631f1c3db`, `ba1bfc4d1` |
| What is the glue? | Contraction/dissipative components are load-bearing. Removing dissipation to rotations-only (`G1`) splits to 3 terminal classes; full set `G2` re-merges to one. | `ba1bfc4d1` |
| What is the may/must structure? | The graph distinguishes existential reachability from universal omega containment. `can_reach_terminal=33` and `sure_basin/omega-containment=[16]` in the partition row; the sweep keeps both semantics per set. | `000f48e71`, `631f1c3db`, `ba1bfc4d1` |
| What splits? | Rotations-only: 3 terminal classes. L/R chirality subsets: both split, with same count/size signature but different terminal cell sets. Composite word `G5`: 5 terminal classes. | `ba1bfc4d1` |
| What is undecided? | Whether finite rotation classes survive grid refinement/rotated grids; whether the 64 two-engine product exists and decomposes as the owner-predicted product; whether continuum geometry rather than 33-cell discretization is being seen. | `ba1bfc4d1`, `d5914f67f`, `0bed51ac2` |
| Meta-convergence | The campaign itself is converging: criterion -> pilot negative on affine one-attractor rows -> explicit finite partition -> generating-set sweep. Each packet narrowed the open question from "is basin language earned?" to "which generator subsets split, and which pending controls decide whether those splits are geometric/product-structured?" | `50f16d82d`, `4e082f525`, `631f1c3db`, `ba1bfc4d1` |

## 2. Whole Model Pillars

| Pillar | Strongest committed evidence | Current honest statement | Sharpest next falsifier | Hashes |
|---|---|---|---|---:|
| Geometry stack S1-S11 | Program-status table records S1-S11 with packet hashes; S2-S7 mode coverage; S8 lifted ladder; S9 Hopf stacks; S10 G2 family; S11 scratch/advisory only. | The stack is a valid committed scratch-diagnostic family member. S11 remains gated; no full constraint manifold admission. | A deeper alternative-space packet that reproduces the composite identity with a different layer family, or a validator showing a cited packet does not match its claimed row. | `4bd575c08`, `9fb6907cc`, plus per-stage hashes in that receipt |
| Ratchet | Committed `ratchet_*` packet directories count to 8 at HEAD: single shell, two-shell, S6 terrain/operator, G2 family, three-shell chain, S6 terrain sweep, deep chain, and order breadth. The status receipt separately says mode 4 lived in five RATCHETED packets at that time; later committed `ratchet_*` rows extend the family to 8 directories. The owner's requested "9 RATCHETED packets" is not stated as committed fact unless a ninth non-`ratchet_*` packet is separately defined. | Ratcheting is real for named packets: induced geometry recomputed under constraints, mortality/saturation observed, and exact lens entropy drops exist. Order breadth is now `k=2` signature-relative under the repaired order-blind signature, after a prior `k=5` full-signature echo was killed. | Any new order-blind signature that decodes order labels, a replay where the commuting control no longer groups `LZWT/ZLWT`, or a ninth-packet citation that cannot be resolved to committed evidence. | `f578b7181`, `15b1d1899`, `76597c8a8`, `b5649217c`, `de783dc79`, `826e716d1`, `7909b1b1b`, `187e96bdd` |
| Mortality and saturation | Deep chain reaches branch mortality and scoped saturation for cited constraints; order breadth has 19/24 mortality in 3 committed classes. | High path mortality is computed for one fixed alphabet/multiset; saturation is scoped to the cited committed constraint set. | A broader multiset where mortality disappears or saturation was a convention artifact. | `7909b1b1b`, `6d0d4bf3`, `187e96bdd` |
| Fibration tower | Disintegration tower plus Hopf stacks: complex/S1-S2 roots, quaternionic `S3->S7->S4`, octonionic `S7->S15->S8`, with Adams/sedenion boundary. | Three of four positive Hopf/fibration depths are computed as scratch stack rows; octonionic row has honest negative for tripartite entanglement detection and no fake principal S7 connection. | A fourth/fifth-rung claim that evades the sedenion norm/fiber-law kill, or a true octonionic connection/Chern substitute with controls. | `a0a673e93`, `b79036b1f`, `8a46c8627`, `33dc2323f`, `17d4698ab`, `a5637cb0f` |
| Entanglement detection | Quaternionic Hopf detects 2Q concurrence identity; octonionic base readout is only O2/A|BC bipartition and explicitly not tripartite tau. | Entanglement-detection exists at quaternionic 2Q depth; octonionic row is honest-negative for the stronger tripartite detector. | A committed octonionic packet that detects tau with can-fail controls rather than prompt wording. | `33dc2323f`, `17d4698ab` |
| Dynamics | Dynamic deformation ledger: compression rows, genuine warp at constant admissible count, expansion only under release; unified run re-fires deformation modes in situ. | Manifolds/finite support objects are dynamic under named operations: they compress, warp, and expand only when constraints are released. | A pure constraint-addition row that expands `Adm_C`, or a quotient-readout operation that recovers erased phase distinctions under the scoped operation family. | `cdf437053`, `6903e0388` |
| Rigidity laws | Two finite-scope laws: pure constraint addition cannot expand admissible set; quotient erasure is irreversible by available operations. | The "how it cannot deform" claim is earned only over the finite row universe and available operations. | SAT model for pure-addition expansion, or SAT recovery from no-phase quotient without phase-refined control. | `cdf437053`, `6903e0388` |
| Entropy ledger | Exact `h(S3)=h(eta)+E[h(T_eta)]`; typed table; lens loss magnitude `ln4` read as signed `-ln4`; terrain restriction delta; chain controls. | Entropy is a typed readout/summary of constraint structure, not primitive. The chain rule is the strongest committed cross-layer identity. | Wrong marginal or wrong group-order control stops firing, or typed entropy categories are collapsed in a later packet. | `a54224476`, `e2ca51b02`, `6903e0388` |
| Uniqueness profile | Original discriminator queue closed at first-discriminator depth. S4/S5/S6/S7/S9-geometric/ratchet alternatives killed or split; S3 SIC and S9 `c1` co-survive. | Unique-by-geometry-and-dynamics, shared-at-topological/IC levels. This is bounded stack identity, not global mathematical uniqueness. | Any next-round alternative that matches holonomy spectra, flow signatures, operator alphabet, order structure, and composite assembly while being genuinely distinct. | `7bc1af811`, `0d766bb40`, `8f4fef471`, `f7c076f67` |
| Engines: cost | Loop-local 8-stage engine word keeps max bond `[4,8,4]` at n=8/12/16 across full 720 double traversal; all-to-all/Haar controls fire. | Cost discriminator survives at computed sizes; no asymptotic or engine admission claim. | Same stored word replay no longer agrees, or a control matches the cost profile. | `123b8e7d8` |
| Engines: readout periodicity | 16 real loop-local strategy readouts show alternating/paired periodicity; 720 double traversal repeats 360 density classes. | The readout word alone does not see the second 360; spinor lift is needed. | A density-level strategy pair that separates only on double traversal. | `e2d9d5407` |
| Engines: 720 arc | Spinor-lift readouts separate first 360 from second 360 for all 16 strategy analogs; density quotient maps back byte-consistently. | Sign lives on the lift and is erased by the density/projective quotient. | Phase-randomized or quotient-erased control also separates 720, making the lift decorative. | `f78868aa4` |
| Engines: L/R mirror | Universal sigma_y mirror dies; family-local mirror law survives: Se/Ne rotational continuum, Ni unique affine mirror, Si its own frame. | L/R chirality is real but family-local/probe-local, not universal mirror law. | Common all-four mirror SAT, or family-local mirrors fail under exact solver replay. | `a706208c4`, `81b38c3e6` |
| Basins | Criterion, pilot, partition, and generating-set sweep now form a coherent basin campaign. | Finite basin structure is real at scratch scope; continuum/refinement and 64-product remain pending. | Grid refinement kills `G1` classes, or 64 product adjudication fails the factorization. | `50f16d82d`, `000f48e71`, `4e082f525`, `631f1c3db`, `ba1bfc4d1`, `d5914f67f`, `0bed51ac2` |

## 3. Information Processed Over The Manifolds

### 3.1 Existing Committed Information-Theoretic Rows

| Row family | What exists | Claim ceiling | Hashes |
|---|---|---|---:|
| Entropy ledger and chain rule | Exact measure entropy rows, typed entropy table, `h(S3)=h(eta)+E[h(T_eta)]`, controls for wrong base/marginal/group order. | Scratch-diagnostic entropy readout, not primitive information doctrine. | `a54224476`, `6903e0388` |
| Lens quotient drops | Deep chain and ratchet-order breadth record exact signed quotient drops `-ln4` and `-ln2`; entropy ledger labels lens loss magnitude `ln4` with signed caveat. | Exact finite quotient entropy deltas under committed convention. | `7909b1b1b`, `a54224476`, `187e96bdd` |
| Ladder entropies | Lifted ladder n=3..8 carries vN entropy anchors for GHZ/W rows and IC/cut data; entropy ledger cites the carrier anchors. | Carrier-level vN anchors; no trend/stage-closure. | `3a53d16af`, `30d21022e`, `4047dc73b`, `0f47decd5`, `70fe9aa68`, `08037882e`, `a54224476` |
| S8-local QIT table | Not yet closed. The S8 adjudication explicitly says `S(A|B)`, `I(A:B)`, and `I_c` are missing from the committed S8 packets; the lifted-ladder spec defines them as required rows for the next bounded packet. | Missing row, not existing throughput evidence. | `0bd1cdf8a`, `21d6e7249` |
| Compression-flow radiated record | 384-row finite compression/record packet; exact cardinality ledger; append-only hash chain; raw reconstruction; quotient-mode mismatch; erasure/lossy failures; payload-bound SMT after hardening. | Candidate finite record/radiation formalization; no physics/no conservation theorem. | `eee9a7c41` |
| Readout distinguishability matrices | 16x16 density readout matrix and spinor-lift separation matrix; density repeats 360 groups, lift separates 720 from 360 but not slot-copy groups. | Readout/probe distinguishability only. | `e2d9d5407`, `f78868aa4` |

### 3.2 Missing Rows For A Real Throughput Account

| Missing row | Why missing matters | Proposed information-throughput packet spec | Gates / dependencies |
|---|---|---|---|
| Channel capacities for committed terrain/operator maps | Current rows say distinguishability, entropy deltas, and readout classes, not bits/nats per map/channel. | For each committed terrain/operator transition, define input ensemble, output readout, channel matrix, capacity/objective, and controls. | Depends on stable terrain/operator map set (`S4/S5/S6`) and readout probe family. |
| S8 local QIT table | The S8 floor has reduced-density and entropy fixtures, but not the local conditional/mutual/coherent information table. | Compute `S(A)`, `S(B)`, `S(AB)`, `S(A|B)=S(AB)-S(B)`, `I(A:B)=S(A)+S(B)-S(AB)`, and `I_c=S(B)-S(AB)` for product/Bell/GHZ/W controls and named bipartitions. | Depends on `s8_s9_adjudication_20260610.md` and `lifted_ladder_spec_20260610.md`; keep it bounded and scratch. |
| Information flow along stage word | Engine rows show cost and periodic readout; they do not quantify information transmitted per stage or lost/erased per operation. | Stage-word throughput ledger: per step input state class, output class, retained distinctions, erased distinctions, radiated/recorded distinctions, and cumulative balance. | Depends on `engine_readout_strategy_fidelity_v0`, `engine_readout_spinor_lift_v0`, and ratchet-order convention. |
| Ratchet destroys vs radiates per step | Entropy drops and compression record exist separately; no packet binds them into a conservation test over the same ratchet sequence. | For the committed ratchet sequence, report `destroyed_by_quotient`, `retained_in_live_state`, `emitted_to_record`, `unaccounted`, with raw and quotient controls. | Depends on entropy ledger (`a54224476`), deep chain (`7909b1b1b`), compression-flow (`eee9a7c41`). |
| Owner "no information destroyed" as testable conservation | Current committed packet supports exact finite reconstruction when raw record is kept, and failure under quotient/erasure; it does not prove no information destroyed globally. | Conservation packet must pre-register register basis and compare full-support, remaining-live, emitted-step, quotient, and raw-record conventions. It should fail closed when unaccounted mass exists. | Depends on compression-flow hardening and a chosen manifold/ratchet sequence. |
| Throughput over basins | Basin campaign has may/must and terminal classes, but no information-throughput measure for transitions to terminal classes or split classes. | Add basin-transition channel: generator choices as inputs, SCC/terminal class as output, may/must uncertainty, and entropy over terminal fate. | Gated by 64-product and refinement-control verdicts. |

## 4. How Dynamic The Manifolds Are

| Object / row family | Moves under | Rigid under | Evidence / details | Hashes |
|---|---|---|---|---:|
| Admissible finite support `Adm_C` | Constraint release expands: `206->256/384`; constraint addition compresses `384->256->206`. | Pure constraint addition cannot expand within computed finite row universe. | Compression rows have real excluded counts and entropy decreases; release controls are SAT. | `cdf437053` |
| Relation graph / shape invariant | Warp operation changes relation edges `1664->1600` and spectrum while admissible count stays `206`. | Pinned invariants `c1_abs=1`, chain additivity defect `0`, cover factor `2` do not move under available deformations. | This is the genuine WARP row: constant size, changed shape. | `cdf437053` |
| Quotient/readout distinctions | Phase-refined control can recover phase; no-phase quotient cannot. | Quotient erasure irreversible under available operations/readouts. | Same no-phase quotient pair with different phase values gives UNSAT recovery; phase-refined control SAT. | `cdf437053`, `6903e0388` |
| S2 holonomy in unified run | Lens step changes primitive holonomy value; post-lens holds changed value. | Invariant row families are carried only with stated justification, not silently recomputed. | Unified run classifies step-dependent vs step-invariant rows. | `6903e0388` |
| Entropy ledger | Lens quotient and terrain restrictions change entropy/readout measures; k-leaf/conditioning rows change typed entropy. | Exact chain rule remains zero-defect under committed measure convention. | Wrong marginal/group-order controls fire. | `a54224476`, `6903e0388` |
| Ratchet path object | Leaf -> lens -> phase window -> Z2 -> terrain changes denominator, chart volume, holonomy, and entropy deltas. | Scoped saturation reached for cited constraints; not global saturation. | Branch mortality and exclusion of `Z8`/quotient-collapse alternatives. | `7909b1b1b` |
| Order structure | Most orderings die; live order-blind classes split by terrain-support precedence. | Commuting anchor `LZWT/ZLWT` same-class under order-blind signature. | Current corrected result is `k=2` signature-relative; not absolute/global. | `187e96bdd` |
| Basin fate table | Generator-set changes move fate: rotations split, full set re-merges, chirality subsets split, conditioned row shrinks. | One-terminal dissipative baseline persists for `G0/G2`; terminal absent-exit proofs hold in finite graph. | Basin fates are generator-set-dependent. | `631f1c3db`, `ba1bfc4d1` |
| Engine cost/readout | Lift phase readout separates 720 from 360; density readout repeats. | Density/projective quotient erases lift sign and maps back to parent classes. | Cost structure survives computed sizes; readout periodicity survives. | `123b8e7d8`, `e2d9d5407`, `f78868aa4` |

Consolidated degree: the manifolds are dynamic in finite, operation-scoped ways. They move by compression, warp, release, quotient, conditioning, generator choice, and stage/order word. They are rigid where the committed finite laws bind: pure constraint addition cannot expand, quotient erasure cannot be undone by available no-phase readouts, and pinned invariants do not move under the tested deformation family.

## 5. Improved Next-Wave Plan

| Rank | Next wave | Why now | Dependencies | Cost class | Pending verdicts that gate it |
|---:|---|---|---|---|---|
| 1 | Basin refinement control | Decides whether `G1` rotations-only 3 classes are geometric or 33-cell artifacts. | `basin_generating_set_sweep_v0` (`ba1bfc4d1`). | Medium local, finite graph sweep. | Refinement/rotated-grid PENDING. |
| 2 | Two-engine 64 product adjudication | Owner prediction is already pre-registered; resolves whether chirality/engine product structure exists. | Basin sweep, L/R mirror family-locality, readout/matrix64 lineage. | Heavy local / controlled fanout. | 64-test PENDING; must require product factorization, not count alone. |
| 3 | Information-throughput packet | Turns the new vein into a falsifiable accounting object rather than prose. | Entropy ledger, deep chain, compression-flow, engine readouts. | Medium-heavy, mostly finite/JAX+Julia+SMT. | Should wait for chosen sequence; basin 64 can add a basin-throughput branch later. |
| 4 | S8 QIT table closure | Closes an explicitly adjudicated missing row before broader throughput claims lean on ladder information. | S8 adjudication and lifted-ladder spec. | Light-medium exact/symbolic packet. | Not gated by 64; stop if it starts importing bridge/physics claims. |
| 5 | Stage-word throughput ledger | Quantifies retained/erased/radiated distinctions per engine stage. | Engine cost/readout, spinor lift, ratchet order. | Medium. | Not gated by 64, but 64 may change target product rows. |
| 6 | Basin information channel | Measures entropy/uncertainty of generator choices to terminal/must classes. | Basin partition/sweep. | Light-medium. | Stronger after refinement; can run as current-33-cell scout before geometry reading. |
| 7 | Ratchet-count adjudication | Resolves the owner-facing "9 RATCHETED packets" phrase against the 8 committed `ratchet_*` directories and any non-directory RATCHETED-mode packets. | `git ls-tree` count, program status, packet modes. | Light receipt/audit. | Required before any future summary repeats "9 RATCHETED." |
| 8 | Next-round uniqueness depth | Original queue is closed at first-discriminator depth; deeper alternatives remain. | Stack uniqueness addendum 3. | Rolling medium-heavy by layer. | Not gated, but should not preempt basin/information active gates. |
| 9 | Continuum bridge preflight, not bridge | Prepare exact criteria for any future continuum/admission move without claiming it. | Refinement control, entropy-throughput spec, dynamic rigidity scope. | Light docs + small formal scouts. | Blocked until refinement and throughput produce cleaner finite objects. |

## 6. Bottom-Line State

The model, as of committed evidence now, is not "proved" as a global theory. It is a coherent scratch-diagnostic research object with unusually strong bounded structure:

- Geometry stack: valid S1-S10 family member, S11 gated.
- Ratchet: real sequential induced-geometry machinery with mortality, scoped saturation, and repaired order-blind structure; current committed `ratchet_*` directory count is 8, while "9 RATCHETED" remains a phrase to adjudicate before reuse.
- Fibrations: three positive stacked Hopf/fibration depths plus honest termination/negative rows.
- Dynamics: finite manifolds/supports move by compression, warp, release, quotient, order, and basin generator choice; two finite rigidity laws currently survive.
- Entropy/information: exact typed entropy and record packets exist, but a throughput/conservation account is still missing and should be built as the next vein.
- Uniqueness: unique-by-geometry-and-dynamics among tested alternatives; shared at topological and IC levels; no global uniqueness claim.
- Basins: the campaign is converging and now has real finite sub-basin structure, but the decisive next gates are refinement and 64-product adjudication.

No new claims are admitted by this receipt.
