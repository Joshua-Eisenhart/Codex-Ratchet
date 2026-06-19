# M(C,t) geometric build - WIKI source map

Purpose: map the wiki half of the mine for the M(C,t) geometric build. This is a read lane, not a build. It reports standing wiki sources, conflicts/supersessions, and absence-rule searches. It does not resolve conflicts or promote any claim.

Authority and routing used:

- `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/README.md:3` defines the mine as v5 plus the wiki.
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/README.md:43-49` requires grep-quoted absence and novelty checks before "missing" or "new" claims.
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/README.md:67-73` puts M(C,t), geometry on M(C), terrain/operator/flux, and fenced later names in the current plan boundary.
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/doc_router_axes_terrains_operators_20260609.md:5-14` supplies the established reading order.
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/mct_reconciled_spec_20260609.md:12-43` supplies the repo-side reconciled M(C,t) object used only as comparison surface.

## A. SOURCE MAP BY REQUIREMENT

### 1. States = spinor samples on nested Hopf shells, with ring-checkerboard discretization

- `/Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md:58-68` supplies the constraint-manifold-to-carrier boundary: M(C) is built first, and spinor/quaternion/Hopf/nested-torus geometry is candidate carrier geometry induced on that admissible object, not the definition of the manifold.
- `/Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md:113-125` supplies the minimum finite support contract: candidate carrier geometry, finite support, finite probes, quotient, and adjacency/path structure.
- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Formal constraints and geometry.md:78-88` supplies the spinor/Hopf coordinate chart: `psi in S^3`, Hopf projection, fiber coordinate, base coordinates, torus stratum, and connection.
- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Formal constraints and geometry.md:157-166` supplies the nested Hopf torus state picture with `T_eta subset S^3` and left/right Weyl spinor fields on each torus.
- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/terrain rosetta strong math.md:3-20` supplies the same carrier layer in compact form: `H = C^2`, density states, left/right spinors, Hopf coordinates, torus strata, and fiber-blind density reduction.
- `/Users/joshuaeisenhart/wiki/concepts/hopf-fibration-mathematics.md:19-32` supplies the standard Hopf map math: `S^3 -> S^2`, fiber `S^1`, global phase, connection, curvature, and the note that same-fiber states are indistinguishable under density-matrix measurement.
- `/Users/joshuaeisenhart/wiki/concepts/hopf-fibration-mathematics.md:42-49` supplies nested tori and holonomy/Berry-phase framing as carrier geometry.
- `/Users/joshuaeisenhart/wiki/concepts/hopf-foliation-structure.md:23-29` supplies the nested foliation shape: a family of Hopf tori indexed by a nesting parameter, with leaves/strata and leafwise loops.
- `/Users/joshuaeisenhart/wiki/concepts/quaternion-and-spinor-carrier-foundations.md:20-32` supplies the standard identifications `S^3 = unit spinors = unit quaternions = SU(2)` and the Hopf projection to Bloch/base space.
- `/Users/joshuaeisenhart/wiki/concepts/ring-checkerboard-gradient.md:16-23` supplies the owner vocabulary annotation: checkerboard-like discrete pattern, curved into spherical/nested rings, with torus-like rings as a visual/support model.
- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Ring Checkerboard Gradient.md:6-14` supplies the raw ring-checkerboard source: flat and spherical checkerboards, nested spherical shells, discrete rings, torus made of ring loops, and recursive nesting.
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/pre-ai-rosetta-ring-checkerboard-provenance-2026-06-09.md:215-233` supplies the current mapping table from ring/checkerboard vocabulary into candidate formal roles: finite grid, nested radial shells, toroidal/fiber loops, and recursive nesting.
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/whole-physics-model-processing-ledger-2026-06-05.md:401-412` supplies the ladder from density/probe quotient upward to spinor lift, Hopf fibration, and nested Hopf tori.

Math supplied: finite state support should be read as admissible samples/lattice points on a carrier candidate whose standard geometry is spinors on `S^3`, Hopf fibers, and nested Hopf tori; ring-checkerboard is an annotation for finite/nested/toroidal discretization, not a separate admitted physics object.

### 2. Probes = binned observables

- `/Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md:117-122` supplies finite probes and probe-induced quotient structure: finite support, finite probe/readout family, and equivalence relation induced by the probes.
- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Formal constraints and geometry.md:57-65` supplies the standard observable law: density states on `H = C^2`, Hermitian probe `O`, and `p_O(rho)=Tr(O rho)`.
- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/terrain rosetta strong math.md:71-73` supplies the stage readout packet form: a probe family `M_k` reads probabilities `Tr(M_k rho_j)` after each stage.
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/whole-physics-model-processing-ledger-2026-06-05.md:320-352` supplies finite probe family `M`, probe equivalence `a ~_M b`, quotient `Q=S/~_M`, state-on-algebra representation, and density matrix as expectation representation.
- `/Users/joshuaeisenhart/wiki/concepts/field-wide-compression-probe-contract.md:211-232` supplies the readout contract: named observable, finite object, probe family, contrast, pass condition, kill condition, and result field.
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/overall-aligned-execution-plan-2026-06-07.md:199-212` supplies the cross-model readout matrix shape: `S`, `C`, `M_i`, `R_i`, controls, and observable.

Math supplied: wiki sources define finite probe/readout families and observable expectation values. The exact phrase "binned observables" is not found in Codex Ratchet wiki sources; see section C. The nearest standing math is finite probe families over finite support, with readouts that can be binned by the build if the owner accepts that as implementation vocabulary.

### 3. Quotient `S/~_M` computed so phi-blindness emerges

- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/whole-physics-model-processing-ledger-2026-06-05.md:320-352` supplies the abstract quotient: finite set `S`, finite probe family `M`, `a ~_M b iff forall m in M: m(a)=m(b)`, quotient `Q=S/~_M`, and density matrices as compressed expectation representations.
- `/Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md:120-122` supplies the M(C) packet version: finite probe/readout family `P`, quotient/equivalence relation induced by `P`, and admissibility predicate `Adm_C`.
- `/Users/joshuaeisenhart/wiki/concepts/hopf-fibration-mathematics.md:19-23` supplies the carrier-specific blindness: Hopf fiber is global phase, and states on the same fiber are indistinguishable under density-matrix measurement.
- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/terrain rosetta strong math.md:15-20` supplies the density-reduction equation and explicitly labels it "fiber-blind reduction."
- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/terrain math.md:43-49` supplies the loop-level visibility rule: inner/fiber motion leaves density unchanged, while base motion changes density.
- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Formal constraints and geometry.md:94-99` supplies the same law as inner loop density-stationary and outer loop density-traversing.
- `/Users/joshuaeisenhart/wiki/concepts/terrain-laws-and-loop-geometry.md:53-62` supplies the terrain/loop restatement: fiber loops stay density-stationary; base loops traverse density.

Math supplied: `S/~_M` is the probe-equivalence quotient. In the Hopf carrier case, phi/global-phase blindness is not primitive; it is the result of reducing spinor samples through density/probe readouts that identify same-fiber states.

### 4. Dynamics = committed operator/terrain packet forms

- `/Users/joshuaeisenhart/wiki/concepts/terrain-laws-and-loop-geometry.md:21-25` supplies the current owner correction: terrain/flux belongs to geometry-on-manifold/ratchet layer, axes are readout maps, and the manifold is dynamic through expanding, compressing, folding, warping, and reindexing.
- `/Users/joshuaeisenhart/wiki/concepts/operator-math-explicit.md:25-39` supplies the operator domain: `H=C^2`, density states `D(H)`, Bloch form, and the requirement that operators presuppose an admitted density-state object.
- `/Users/joshuaeisenhart/wiki/concepts/operator-math-explicit.md:68-115` supplies the four local operator/channel families: `z`-basis dephasing, `x`-basis dephasing, `x`-rotation, `z`-rotation, plus effects/readouts.
- `/Users/joshuaeisenhart/wiki/concepts/operator-math-explicit.md:125-139` supplies order-sensitive composition guidance: terrain stage order is not flattened, and noncommutation gives one formal test for order sensitivity.
- `/Users/joshuaeisenhart/wiki/concepts/terrain-laws-and-loop-geometry.md:28-39` supplies the carrier setting for terrain loops: spinor carrier, Hopf projection, density matrix, and left/right Weyl split.
- `/Users/joshuaeisenhart/wiki/concepts/terrain-laws-and-loop-geometry.md:64-88` supplies the four terrain family classes with their mathematical operators: collapse/concentration, orientation/rotation, expansion/distribution, and resolution/measurement.
- `/Users/joshuaeisenhart/wiki/concepts/terrain-laws-and-loop-geometry.md:89-105` supplies the four loop slots and sixteen placements as design space, not admitted fact.
- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/terrain math.md:51-83` supplies state variables, left/right flows, eight terrain generators, and where each generator acts.
- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/terrain math.md:92-152` supplies sixteen loop placements and the separation between terrain families, terrains, and loop placements.
- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/terrain rosetta strong math.md:44-73` supplies Hamiltonians, Lindblad dissipators, stage generators/channels, and probe readout.
- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/terrain rosetta strong math.md:149-183` supplies the full sixteen placement table and structural lock.
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/igt-axes-terrain-source-extraction-2026-06-04.md:9-17` supplies only the boundary rule needed here: carrier geometry, operator/process, and IGT grammar must remain separate surfaces.

Math supplied: dynamic packets live on admitted density/carrier state objects, with local channels/generators, terrain family classes, loop placements, and order-sensitive composition. The wiki treats these as geometry-on-manifold/operator-process surfaces, not as primitive axes.

### 5. The five manifold operations as measured behaviors

- `/Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md:40-52` supplies the five operation names and their intended roles: compression, expansion, warping, folding, and reindexing.
- `/Users/joshuaeisenhart/wiki/concepts/terrain-laws-and-loop-geometry.md:21-25` repeats the owner correction that the manifold is dynamic through expanding, compressing, folding, warping, and reindexing.
- `/Users/joshuaeisenhart/wiki/concepts/field-wide-compression-probe-contract.md:123-153` supplies the finite whole-field dependency measurement frame: `C_n:B_n -> B_{n+1}`, relation fields `D_n(y)`, controls, and whole-field rather than local-only dependency.
- `/Users/joshuaeisenhart/wiki/concepts/field-wide-compression-probe-contract.md:165-203` supplies explicit measured compression/expansion variables: support size, possibility mass, accessible modes, expansion pass/fail, compression pass/fail, and falsifiers.
- `/Users/joshuaeisenhart/wiki/concepts/field-wide-compression-probe-contract.md:258-271` supplies candidate finite-witness invariants, including whole-field dependency, order asymmetry, probe-equivalence quotient, bracketing sensitivity, and no-pointwise-collapse.
- `/Users/joshuaeisenhart/wiki/concepts/field-wide-compression-probe-contract.md:288-305` supplies decisive falsifiers for that measurement packet.
- `/Users/joshuaeisenhart/wiki/concepts/support-first-constraint-manifold-dependency-chain.md:113-118` supplies sim design discipline: start with carrier/support/probe admissibility and run wrong-order variants as controls.

Math supplied: the wiki defines all five operation names and gives measurement discipline. It explicitly measures compression and expansion in the field-wide compression probe contract. It does not contain a direct pass/fail measurement contract for warping, folding, or reindexing under those exact operation names; see section C.

### 6. Composition/bracketing structure of the M(C) packet, including witness-step index `W_n` and time-dependence

- `/Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md:40-46` supplies time-dependence as `M(C,t)` and states that the manifold changes through active operations, not a static once-built set.
- `/Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md:98-104` supplies the M(C) packet shape: `S`, `C`, `P`, `~_P`, `Adm_C`, composition/bracketing, local readouts, controls, and receipts.
- `/Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md:120-123` supplies the specific packet requirements for quotient/equivalence, admissibility, and order-sensitive composition/bracketing.
- `/Users/joshuaeisenhart/wiki/concepts/field-wide-compression-probe-contract.md:64-102` supplies the finite witness-step packet `W_n=(X_n,P_n,E_n,H_n,Q_n,R_n,V_n)` and the update relation from `W_n` to `W_{n+1}`.
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/whole-physics-model-processing-ledger-2026-06-05.md:540-572` supplies the bracketing doctrine: associativity is not primitive, bracket equivalence is probe-relative, and sequence sensitivity and bracketing sensitivity must be separately tested.
- `/Users/joshuaeisenhart/wiki/concepts/support-first-constraint-manifold-dependency-chain.md:90-99` supplies the ordered dependency-chain view of the ratchet: admissible support, carrier, probes, induced geometry, operators, and couplings.
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/overall-aligned-execution-plan-2026-06-07.md:124-146` supplies a stage-2 M(C) packet with finite state support, constraints, probes/measurements, quotient, admissibility, composition/bracketing, local readouts, controls, receipts, and claim ceiling.
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/overall-aligned-execution-plan-2026-06-07.md:252-273` supplies the strong-gate packet contract: probe definition, relation, quotient, admissibility predicate, and composition/bracketing law.
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/read-first.md:15-23` supplies the current read-first chain from probe-relative identity through root constraints, M(C), spinor carrier, density/probe quotient, Hopf/Weyl objects, and terrain/operator surfaces.
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/read-first.md:31` supplies the warning that finite path-integral packet pressure introduces named probe quotients such as `S/~_M` but is not an admission by itself.

Math supplied: wiki sources define M(C) as a finite packet with quotient, admissibility, readouts, controls, receipts, and composition/bracketing. `W_n` supplies the time-indexed finite witness-step packet and update frame.

## B. CONFLICTS / SUPERSESSIONS

### 1. Static/simultaneous M(C) surface vs dynamic M(C,t) update object

Wiki static/simultaneous surface:

> "The admissible structure is:
> M(C) = {x : x satisfies all active constraints C}."
> - `/Users/joshuaeisenhart/wiki/raw/articles/new-docs/CONSTRAINT_SURFACE_AND_PROCESS.md:22-23`

> "Every point in M(C) is already simultaneously constrained. The constraints do not form a ladder in the ontology. They coexist."
> - `/Users/joshuaeisenhart/wiki/raw/articles/new-docs/CONSTRAINT_SURFACE_AND_PROCESS.md:25-26`

Wiki dynamic correction:

> "Owner correction: The manifold is dynamic:
> M(C,t)
> not merely M(C)."
> - `/Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md:40-43`

Repo reconciled comparison:

> "Use a dynamic finite admissibility object:
> M(C,t) = (S_t, C_t, Probe_t, Val_t, ~_t, Q_t, Adm_t, E_t,
>           Poss_t, H_t, R_t, Var_t, U_t, Ctrl_t, Rec_t)"
> - `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/mct_reconciled_spec_20260609.md:14-16`

Status: unresolved here. The wiki contains both a simultaneous-surface statement and a later dynamic correction. The repo spec reconciles by retaining finite M(C) packet structure with time-indexed update fields.

### 2. Geometry chart order vs build-order discipline

Wiki chart statement:

> "The arrow:
> Spinor -> Hopf -> Weyl -> Pauli -> density -> terrain -> operator -> graph
> is a dependency/chart relation, not a runtime sequence."
> - `/Users/joshuaeisenhart/wiki/raw/articles/new-docs/CONSTRAINT_SURFACE_AND_PROCESS.md:87-89`

Wiki build-order statement:

> "The corrected order is:
> 1. root constraints
> 2. M(C)
> 3. geometry induced on or fitted to M(C)
> 4. axes as readouts/functions on that geometry
> 5. physical/IGT candidates only after that"
> - `/Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md:73-80`

Repo comparison:

> "Build-card order:
> 1. finite support S;
> 2. probes/readouts first;
> 3. quotient Q=S/~_M;
> 4. constraints/admissibility;
> 5. update operators and five operations;
> 6. controls."
> - `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/mct_reconciled_spec_20260609.md:213-220`

Status: unresolved here. The chart relation can coexist with build order, but the report does not collapse them. Any sequence claim must keep chart-dependency order separate from implementation/test order.

### 3. Strong "verified"/"current truth" wording vs current v6 ceiling

Wiki/raw strong wording:

> "Verified Weyl-spinor layer belongs exactly at the inner spinor/Hopf/torus carrier level, not at the later density/operator/graph layers."
> - `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Formal constraints and geometry.md:134-137`

Wiki parity-audit caution:

> "Do not say 'the geometry manifold is done'. Say: same-carrier geometry has explicit anchors and partial parity across several standard packages, while missing math remains in connections, metrics, and graph/cell realization."
> - `/Users/joshuaeisenhart/wiki/concepts/geometry-manifold-parity-audit.md:135-138`

Repo/v6 ceiling:

> "scratch_diagnostic / formal_probe_plan until promoted by new gates"
> - `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/README.md:69-70`

Status: unresolved here. Older raw sources contain stronger local "verified" language for placement, while the v6 surface requires scratch/formal-probe ceilings until gates promote the claim.

### 4. Terrain/operator content near axis surfaces vs terrain/flux as geometry-on-manifold layer

Wiki axis atlas scope:

> "This atlas gathers the explicit lower-axis math, constraint-manifold ladder, and terrain/operator realization currently scattered across v5/v6 notes."
> - `/Users/joshuaeisenhart/wiki/concepts/axes-0-6-and-constraint-manifold-explicit-atlas.md:31-32`

Wiki terrain-law correction:

> "Owner correction (2026-06-09): terrain/flux belong to the geometry-on-manifold/ratchet layer; axes are readout maps, not primitive buckets."
> - `/Users/joshuaeisenhart/wiki/concepts/terrain-laws-and-loop-geometry.md:25`

Repo router boundary:

> "Keep the three layers separate:
> 1. carrier geometry
> 2. operator/process math
> 3. IGT macro grammar"
> - `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/doc_router_axes_terrains_operators_20260609.md:17-20`

Status: unresolved here. The axis atlas is a useful collection surface, but newer doctrine says terrain/flux/operator content must not be treated as primitive axis content.

### 5. Ring-checkerboard mapping is live, not collapsed

Wiki anchor statement:

> "Ring-checkerboard imagery visualizes finite surfaces and shell/ring decompositions, but does not by itself determine the admissible mathematical carrier."
> - `/Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md:54`

Wiki provenance live readings:

> "There are at least two live readings:
> 1. Engine-stage / microstate-support reading...
> 2. Cosmological-substrate reading..."
> - `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/pre-ai-rosetta-ring-checkerboard-provenance-2026-06-09.md:108-115`

Wiki unresolved owner question:

> "Does ring-checkerboard map best to:
> - nested Hopf tori;
> - 64-cell/division-algebra carrier;
> - engine-stage microstate board;
> - or a separate pre-geometric support grid?"
> - `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/pre-ai-rosetta-ring-checkerboard-provenance-2026-06-09.md:313-317`

Status: unresolved here. Ring-checkerboard can annotate discretization, shells, and toroidal loops, but the wiki explicitly preserves multiple readings.

## C. NOT FOUND

### Exact wiki phrase: "binned observables"

Search command:

```sh
rg -n "binned|binning|bins|bucketed|coarse[- ]grained observable|coarse[- ]grained observables" /Users/joshuaeisenhart/wiki/concepts /Users/joshuaeisenhart/wiki/projects/codex-ratchet /Users/joshuaeisenhart/wiki/raw || true
```

Quoted output was irrelevant to the M(C,t) wiki packet. Representative hits:

```text
/Users/joshuaeisenhart/wiki/raw/papers/open_access/text/1906.10184__friston_particular_physics.txt:1232:used a discretised state-space of 128 bins...
/Users/joshuaeisenhart/wiki/raw/papers/open_access/text/1906.10184__friston_particular_physics.txt:1258:This figure illustrates a vector field obtained using 1024 bins...
/Users/joshuaeisenhart/wiki/raw/papers/open_access/text/1906.10184__friston_particular_physics.txt:5600:Small lines show the vector field over different bins...
/Users/joshuaeisenhart/wiki/raw/papers/open_access/text/2006.06694__bender_koller_climbing_towards_nlu.txt:2318:I saw a boy with binoculars...
```

Conclusion: no Codex Ratchet wiki source in the searched scope directly defines probes as "binned observables." Standing wiki math defines finite probe/readout families, observable expectation values, and probe-equivalence quotients; those are cited in section A.2.

### Explicit measured contracts for warping, folding, and reindexing

Search command:

```sh
rg -n "measured behavior|measured behaviors|measure.*warping|measure.*folding|measure.*reindexing|warping.*pass|folding.*pass|reindexing.*pass|warping.*control|folding.*control|reindexing.*control" /Users/joshuaeisenhart/wiki/concepts /Users/joshuaeisenhart/wiki/projects/codex-ratchet /Users/joshuaeisenhart/wiki/raw || true
```

Quoted output:

```text
(no output)
```

Conclusion: wiki sources name all five manifold operations, and the field-wide compression contract gives measured behavior for compression/expansion plus general finite-witness controls. No wiki source found gives exact pass/fail measurement contracts for warping, folding, and reindexing under those names. The repo-side reconciled spec supplies fixture behavior for those operations, but that is not a wiki source.

## D. SOURCES-READ LINE

Repo authority/comparison files read:

- `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/README.md:1-75`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/doc_router_axes_terrains_operators_20260609.md:1-20`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/mct_reconciled_spec_20260609.md:1-320`

Wiki concept/project files read:

- `/Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md:1-223`
- `/Users/joshuaeisenhart/wiki/concepts/axes-0-6-and-constraint-manifold-explicit-atlas.md:1-86`
- `/Users/joshuaeisenhart/wiki/concepts/support-first-constraint-manifold-dependency-chain.md:1-195`
- `/Users/joshuaeisenhart/wiki/concepts/ring-checkerboard-gradient.md:1-28`
- `/Users/joshuaeisenhart/wiki/concepts/hopf-fibration-mathematics.md:1-66`
- `/Users/joshuaeisenhart/wiki/concepts/hopf-foliation-structure.md:1-68`
- `/Users/joshuaeisenhart/wiki/concepts/quaternion-and-spinor-carrier-foundations.md:1-70`
- `/Users/joshuaeisenhart/wiki/concepts/geometry-manifold-parity-audit.md:1-157`
- `/Users/joshuaeisenhart/wiki/concepts/constraint-geometry-axis0-separation.md:1-49`
- `/Users/joshuaeisenhart/wiki/concepts/field-wide-compression-probe-contract.md:1-400`
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/read-first.md:1-311`
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/overall-aligned-execution-plan-2026-06-07.md:1-320`
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/model-convergence-qit-engine-full-stack.md:1-189`
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/igt-axes-terrain-source-extraction-2026-06-04.md:1-220`
- `/Users/joshuaeisenhart/wiki/concepts/operator-math-explicit.md:1-181`
- `/Users/joshuaeisenhart/wiki/concepts/terrain-laws-and-loop-geometry.md:1-169`
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/pre-ai-rosetta-ring-checkerboard-provenance-2026-06-09.md:1-317`
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/whole-physics-model-processing-ledger-2026-06-05.md:300-450,540-575,790-825,1228-1246`

Wiki raw files read:

- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Formal constraints and geometry.md:1-195`
- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/terrain rosetta strong math.md:1-188`
- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/terrain math.md:1-152`
- `/Users/joshuaeisenhart/wiki/raw/articles/new-docs/CONSTRAINT_SURFACE_AND_PROCESS.md:1-270`
- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Ring Checkerboard Gradient.md:1-14`

Searches run for absence/source discovery:

- `rg -n "M\(C|M\(C,t\)|constraint[- ]manifold|ring[- ]checkerboard|nested Hopf|Hopf|spinor|quotient|probe|binned|witness|W_n|compression|expansion|warping|folding|reindexing|terrain|operator" /Users/joshuaeisenhart/wiki/concepts /Users/joshuaeisenhart/wiki/projects/codex-ratchet /Users/joshuaeisenhart/wiki/raw`
- `rg -n "constraint[- ]manifold|M\(C\)|M\(C,t\)|ring checkerboard|ring-checkerboard|nested Hopf|Hopf tor|spinor|quotient|~_M|probe|witness|W_n" /Users/joshuaeisenhart/wiki/raw`
- `rg -n "binned|binning|bins|bucketed|coarse[- ]grained observable|coarse[- ]grained observables" /Users/joshuaeisenhart/wiki/concepts /Users/joshuaeisenhart/wiki/projects/codex-ratchet /Users/joshuaeisenhart/wiki/raw || true`
- `rg -n "measured behavior|measured behaviors|measure.*warping|measure.*folding|measure.*reindexing|warping.*pass|folding.*pass|reindexing.*pass|warping.*control|folding.*control|reindexing.*control" /Users/joshuaeisenhart/wiki/concepts /Users/joshuaeisenhart/wiki/projects/codex-ratchet /Users/joshuaeisenhart/wiki/raw || true`
- `rg -n "phi[- ]blind|fiber[- ]blind|global phase|density[- ]stationary|same fiber|same-fiber|S/~_M|~_M" /Users/joshuaeisenhart/wiki/concepts /Users/joshuaeisenhart/wiki/projects/codex-ratchet /Users/joshuaeisenhart/wiki/raw`
- `rg -n "W_n|witness-step|witness step|finite witness|M\(C,t\)|time-depend|dynamic finite" /Users/joshuaeisenhart/wiki/concepts /Users/joshuaeisenhart/wiki/projects/codex-ratchet /Users/joshuaeisenhart/wiki/raw`
