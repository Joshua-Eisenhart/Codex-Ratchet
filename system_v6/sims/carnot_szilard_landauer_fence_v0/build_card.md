# BUILD AUTHORIZATION + CARD — carnot_szilard_landauer_fence_v0 (classical-boundary lane)

You are codex2 (builder, high). Repo: /Users/joshuaeisenhart/Codex-Ratchet. The phase-1 gate below is NOW OPEN (controller authorization 2026-06-11: load gate ok_to_launch, basin/fusion frontier committed through 1c48f1050/de0c8f637). Build EVERYTHING inside system_v6/sims/carnot_szilard_landauer_fence_v0/ (file-disjoint). NO git add/commit. Copy this whole file into the packet as build_card.md.

## Purpose (the classical-boundary lane)
This packet calibrates the CLASSICAL FENCE: what classical thermodynamic legality already explains, as exact solver rows — so the nonclassical stack must exceed it, never silently reproduce it. Findings are exclusion/boundary evidence ONLY: no physics admission, no bridge claims, classification scratch_diagnostic (classical_baseline rows labeled as such), promotion_allowed=false, formal_admission_allowed=false.

## Parent + context (read first)
- system_v6/receipts/old_estate_mine_20260611.md (commit 77fb7ca52) — ranked queue item 2, the source of this card
- the prior decorative verdict on dual_stack_carnot_szilard_hopf_weyl_probe (9dad43b2b) — the failure mode this packet must not repeat: solver rows must bind COMPUTED quantities, not restate definitions
- the typed-entropy discipline (manifold_entropy_ledger_v0): bits vs nats NEVER mixed without an explicit conversion row
- sim-wizard SKILL: TOOL_INTENT_MATRIX in build_card.md; envelope via scripts/build_three_engine_envelope.py

## The object (exact, finite, pinned)
1. Pin exact rational temperatures/energies (e.g., T_h=2, T_c=1 in pinned units) and finite cycle descriptions. Compute exactly (fractions, not floats): Carnot efficiency eta_C = 1 - T_c/T_h; Szilard single-bit work k T ln2 (in nats: ln2, with the typed-entropy conversion row explicit); Landauer minimum erasure cost.
2. ADMITTED rows (SAT/feasible, computed): sub-Carnot engines at named efficiencies; paid erasure; equality-boundary rows (eta = eta_C exactly) — adjudicate and REPORT whether the boundary is admitted or excluded under the pinned formalization, with the convention named.
3. EXCLUDED rows (UNSAT, computed): super-Carnot (eta > eta_C); single-bath positive-work cycles (Kelvin-Planck row); below-Landauer erasure; unpaid-erasure surplus (Szilard cycle claiming net work without the measurement/erasure ledger entry).
4. The pre-registered falsifiers from the phase-1 card (each must behave as named, else the packet FAILS itself): super-Carnot SAT = fence broken; below-Landauer SAT = fence broken; equality-boundary handled inconsistently = fence broken; free-erasure surplus SAT = fence broken; any mixed bits/nats row = typed-entropy violation.
5. CONNECTION ROW (read-only consumption, no new claims): cite the committed conservation-account pair (manifold_information_throughput_v0 + z4_syndrome_record_v0, w/ the state-plus-record convention) and state — as a labeled observation, not an admission — how the Landauer ledger row and the quotient-loss/record row relate under the finite-counting convention (same typed account or explicitly different conventions; if different, name the conversion).

## Controls: a deliberately broken fence (drop one constraint -> super-Carnot must go SAT, computed); a shuffled-ledger control (permute the cycle's step order -> the legality verdict must change where order matters, N01); a trivial-cycle boundary (zero-work row).

## Engineering contract
Three engines (Julia reference w/ exact Rational arithmetic + package_observables; JAX; PyTorch — scope per TOOL_INTENT_MATRIX honestly: if a leg is exact-arithmetic + SMT dominant, declare the mode honestly rather than faking tensor work), z3+cvc5 bind COMPUTED exact values (UNSAT fence + broken-fence SAT flips), envelope via scripts/build_three_engine_envelope.py, validate --require-pytorch --strict-source-backed --require-tool-intent (if the honest mode excludes a full PyTorch sim, run the validator WITHOUT --require-pytorch and say so explicitly), positive+negative+boundary sections. End by listing every validator command + ok status.

## TOOL_INTENT_MATRIX

| Engine | Mode | Load-bearing packages | Exact observable/proof |
|---|---|---|---|
| Julia | exact Rational reference plus Julia Z3/Graphs checks | `Z3`, `Graphs` | `Z3.Solver/Z3.IntVar/Z3.add/Z3.check` binds scaled rational efficiency and ledger coefficients; `Graphs.SimpleDiGraph/Graphs.add_edge!` computes cycle-order reachability and the shuffled-ledger N01 verdict change. |
| JAX/Python | exact integer-array workhorse plus SMT/CAS proof | `z3`, `cvc5`, `sympy` | JAX x64 integer arrays carry row coefficients; `sympy.Rational` computes exact fractions and `sp.log(2)` conversion rows; z3/cvc5 bind those computed values for SAT/UNSAT and broken-fence flips. |
| PyTorch | torch-native finite coefficient lane plus SMT/CAS proof | `torch.func`, `z3`, `cvc5`, `sympy` | `torch.func.vmap` computes row coefficient tensors before conversion to exact rational rows; z3/cvc5 bind those torch-derived coefficients; `sympy.Rational` preserves exact typed entropy coefficients. |

