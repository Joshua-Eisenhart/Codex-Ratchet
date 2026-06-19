# BUILD CARD: ring_checkerboard_support_graph_probe — owner-source support graph as measured behaviors (ladder D)

One object, one claim, one card. CLAIM UNDER TEST: the owner-source ring/checkerboard support structure — G = (V, E, kappa, V_inner, V_outer, phi0) — can be computed as measured graph behaviors on a declared finite size, with the five genuinely-new contents from the committed mine receipt (noncommutation-oriented adjacency, kappa 2-coloring/parity rows, inner/outer ring partition, phi0 discrete-gradient field, ring-step size ladder), each carrying controls that can fail.

Ceiling: classification="scratch_diagnostic", promotion_allowed=false, formal_admission_allowed=false. MUST NOT claim (mine receipt §D verbatim): Axis-0 closure; manifold admission; canonical ring-checkerboard support; settled Xi; physics/cosmology/consciousness/world-engine; collapse of the live readings preserved in the pre-AI provenance page. The Axis-0 rough-draft formalization enters as CANDIDATE only (its source doc is titled NOT CANON).

## Read first (binding)
1. system_v6/receipts/ring_checkerboard_support_mine_20260610.md — THE SPEC: §C adjudication (do NOT recompute the five already-in-mct items as claims; cite them), §D sim shape (implement verbatim), §B owner sources
2. system_v6/sims/mct_dynamic_admissibility_packet_v0/ — the committed support to anchor comparability (lineage cite); its presentation receipts for the three presentation keys
3. "Axis 0 rough and drifty. NOT CANON.md" — the candidate formalization (V, kappa, V_inner/V_outer, ordered E, phi0, discrete gradient) — quote what you implement
4. system_v5 READ ONLY .../Ring Checkerboard Gradient.md + apple notes pre-axex (discrete sizing, ring steps 2..64)

## PIN block (frozen; identical across legs)
- primary size n=8 (comparable to the mct 8x8 grid), with the full ladder sweep n in {2,4,8,16,32,64} as size-ladder rows
- graph construction per mine §D: V = ring/checkerboard cells at size n (declared layout: rings x steps, PINNED-CHOICE quoting the owner-source nesting); kappa(v) = checkerboard 2-coloring; V_inner/V_outer = ring partition; E oriented by a DECLARED noncommutation-sensitive rule (PINNED-CHOICE, tied to order-sensitive rows from committed forms — e.g. the sign of a computed commutator/order-gap quantity along the edge — NOT label order); phi0(v) = a bounded computed scalar candidate (PINNED-CHOICE with source note, e.g. a b0/eta-like shell scalar computed per cell), directed gradients phi0(dst)-phi0(src) per edge
- presentation keys: flat / spherical-shell / nested-ring row-location receipts (the committed mct presentation pattern)

## Build gates
G1. All graph objects computed: vertex/edge counts, parity-transition counts over edges, cross-partition edge counts, full orientation table with the rule's computed inputs emitted, phi0 vertex table + directed gradient edge table. Label-derived shortcuts = failure.
G2. Orientation is load-bearing: reversed-orientation control flips the directed gradients/readouts; the orientation rule's computed (not label) inputs shown per edge.
G3. phi0 non-degenerate: gradients not constant/all-zero/reproducible-from-labels (the mine's kill conditions are live tests — if any kill fires, emit kill_condition_met honestly).
G4. Ladder sweep: at least one NORMALIZED readout changes nontrivially across n (not just row counts); report which are scale-invariant vs scale-sensitive.
G5. Controls each fire: shuffled adjacency (kills orientation/locality readouts), erased coloring (kills parity rows), erased nesting (kills partition rows), reversed orientation (flips gradients), label shuffle (kills nothing structural).
G6. Three-presentation receipts: the same support read through flat/spherical/nested-ring keys with row-location receipts; disagreement controls break agreement where expected.
G7. Load-bearing SMT (z3 AND cvc5): derive a structural fact from the computed tables (e.g. the parity 2-coloring's proper-coloring property on the pinned adjacency -> UNSAT for a monochromatic edge; scrambled control -> SAT). No hardcoded literals.
G8. Comparability row: the n=8 support's relation to the committed mct 384-row support stated as computed comparison fields (counts/partitions), citing mine §C — no claim that this supersedes or closes anything in mct.

## Engines (three-engine claim-bearing; identical PIN)
Julia = canon (Graphs.jl + Z3.jl). JAX = ladder sweep batch + z3/cvc5. PyTorch = independent graph lane (torch_geometric or torch-native adjacency; its own computation path — the R1 lesson; emit source_sha256 fields per current convention). NumPy control-lane only.

## Files to create (one folder, atomic)
system_v6/sims/ring_checkerboard_support_graph_probe/
  ring_checkerboard_support_graph_probe_julia.jl / _jax.py / _pytorch.py / _envelope.py
  build_card.md (verbatim copy)
  results/*.json
No audit_verdict.md. No edits to existing files.

## Acceptance (re-run mechanically)
Legs exit 0 fresh; validator --require-pytorch ok:true; PIN identical; G1-G8 fields present; all controls fired with values; kill conditions evaluated honestly; ceiling + must-not-claim fences exact.
