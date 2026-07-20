# NEGATIVE SIM BATTERY v1 — LEDGER

This ledger records the constraints that each negative sim failure imposes on the positive sims. Failure is the deliverable. All six sims were run with the exact interpreter `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`, one heavy stack per subprocess, using real repo objects (packets/structures from `system_v8/manifold/inputs`, `system_v8/nested_manifold`, `system_v8/unified`). Each sim preregistered its expected failure mode in a comment before execution and reported the actual outcome. promotion_allowed=false for the entire battery. No files were deleted. No commits were made.

## N1 shannon_early
- preregistered_expectation: admission frontier changes or the drive stalls/becomes degenerate where counting kept it moving; measure frontier delta and drive trajectory divergence
- observed: frontier_delta_ticks=30, frontier_size_delta=19996, stalls_where_count_moved=16, drive_L2_divergence=2.15, counting_dC_all_positive=false under the Shannon-uniform gate
- verdict: FAILED_AS_EXPECTED
- constraint on positive: The counting drive (S0 = log |X| from exact integer extension counts) is load-bearing for K1 (dC>0 every tick) and for frontier motion. Replacing it at the base with Shannon entropy over assumed uniform probabilities produces immediate stalls and a frozen frontier (final |X|=4 vs 20000). Any positive sim that treats "entropy drive" as interchangeable with counting drive is under-constrained; the distinction must be kept explicit in the carrier and in the growth law.

## N2 commuting_flux
- preregistered_expectation: loop holonomy differences (flux) collapse toward zero and order-sensitivity dies; measure flux magnitude vs the noncommuting reference
- observed: flux_comm=0.0, collapse_ratio=0.0, order_gap_comm=0.0 (vs non-zero reference flux -1.755 and order gap 1.85 on scrambled leaves)
- verdict: FAILED_AS_EXPECTED
- constraint on positive: Noncommuting stage generators are required for nonzero relative holonomy (flux) across nested leaves and for order-sensitivity of the information profile. Projecting the entire generator family to a commuting subfamily (identical channels) erases both. Positive sims that claim flux or order witnesses must keep the noncommuting generators; any reduction to a single commuting channel is a structural collapse, not a simplification.

## N3 conditional_before_cut
- preregistered_expectation: compute 'mutual information' from mismatched marginals WITHOUT an earned bipartition and show it goes negative (impossible for true MI, which is >=0); then compute the correct I on a proper cut and show >=0; this is the detector that licenses conditional/mutual only after cuts
- observed: I_correct_on_proper_cut=2.0 (>=0), I_fake=-0.070 and I_bad=-1.977 (both <0)
- verdict: FAILED_AS_EXPECTED
- constraint on positive: Mutual information, conditional entropy, and coherent information (Phi0) are only licensed on states that have passed an explicit bipartition cut. Synthesizing I from mismatched marginals (different joints) or from an impossible joint entropy produces negative values. Positive sims must compute cut readouts only after the cut is earned (ptrace on a declared joint carrier); pre-cut "MI" is not a real quantity and cannot be used to drive admission or readout.

## N4 entropy_as_master
- preregistered_expectation: the 16 stage patterns lose distinguishability (fingerprint distinctness collapses below the 16/16 unique baseline min-pairwise 0.336); measure how many remain distinct
- observed: distinct_under_entropy_only=8 (out of 16), min_pairwise=0.0 (below 0.336 baseline), collapsed_below_baseline=true
- verdict: FAILED_AS_EXPECTED
- constraint on positive: The 16 stage patterns (4 families × 2 sheets × 2 fields) are kept distinct by the typed K1/K2/K3 tournament (commutator norm, frame-sign selection, chirality flux sign). Driving admission by von Neumann entropy of a thermal proxy alone collapses the fingerprint to 8 indistinct signatures. Positive sims that use entropy (or any scalar summary) as the sole master variable for stage identity lose the 16-way distinction required by the stage64 ledger; the full typed constraint surface must be retained.

## N5 classical_simplex_carrier
- preregistered_expectation: monodromy/order witnesses die (U_R=U_L^-1 structure unavailable; order-sensitivity fraction drops); measure order-gap distribution vs quantum reference
- observed: classical_order_gap_P1P2=0.0 (collapse), order_gap_collapse=true; order-sensitivity fraction 0.695 still produces gaps under random permutations, but the conjugate/monodromy structure that produces the quantum sign flip and the specific noncommuting gap is absent
- verdict: FAILED_AS_EXPECTED
- constraint on positive: The conjugate representation (H_R = -H_L, jumps conjugated, U_R = U_L^-1) and the resulting signed flux/order witnesses are unavailable on a classical probability simplex. Replacing the density-matrix carrier with a matched-dimension simplex erases the chirality split and the noncommuting order gap that the rung-B C1 and manifold_one flux battery rely on. Positive sims claiming order or chirality witnesses must keep the quantum carrier; classical replacement is a different object.

## N6 mutual_info_front_load
- preregistered_expectation: attempt I(O;register) at tick 0 before any record exists; null/degenerate (no record => MI at permutation-null level); measure vs null
- observed: I_front_loaded=1.0 exactly at the permutation-null mean, z=0.0, at_null_level=true, I_rec_at_tick0=0.0
- verdict: FAILED_AS_EXPECTED
- constraint on positive: Record (I_rec) is a prerequisite for a non-degenerate I(O;register). At tick 0 the admissible set exists but no growth or lock-stroke has occurred; any mutual information computed against an arbitrary label assignment is statistically identical to a shuffled null. Positive sims must not front-load conditional or mutual readouts before the first drive increment and lock; such quantities are undefined or null at the initial surface.

## Aggregate constraint surface for positive sims
- Counting drive (integer extension counts) is not interchangeable with any entropy-over-uniform proxy.
- Noncommutation is load-bearing for flux and for order-sensitivity.
- Cuts are prerequisites for mutual/conditional quantities; pre-cut synthesis is ill-formed.
- Typed stage constraints (K1/K2/K3) are required to keep the 16 patterns distinct; entropy alone is insufficient.
- The density-matrix carrier with conjugate representation is required for monodromy/order/chirality witnesses; a classical simplex is a different theory.
- Record must exist before I(O;register) or conditional readouts are licensed.

These negative results map the boundary that any positive sim must respect. Each failure that occurred as expected tightens the admissible construction for the next positive layer.

NEGATIVE BATTERY DONE: A=6, B=0, C=0
