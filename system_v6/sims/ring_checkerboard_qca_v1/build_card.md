# BUILD CARD — ring_checkerboard_qca_v1 (the quantum/local-channel form + the index/flux invariant; the classical floor is committed)

You are codex2 (builder, xhigh). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build EVERYTHING inside system_v6/sims/ring_checkerboard_qca_v1/ (file-disjoint). NO git add/commit. Copy this card into build_card.md. FILE BOUNDARY: no audit_verdict.md; set the no_builder_audit_verdict gate.

## Authority
1. The CA doctrine + BOTH adjudication entries (system_v6/receipts/owner_doctrine_cellular_automata_ring_checkerboard_20260611.md, b7191aac6): the classical floor EARNED (fe06d49bd: alternating=period-2 vs paired=period-4 on the owner support); the QCA/index gate OPEN; expectations 2-3 are THIS packet's targets. The index/GNVW framing = standard-math alignment, labeled as such, never owner-source.
2. The committed classical packet (ring_checkerboard_automaton_v0) — reuse its support construction (ring steps, parity coloring, one attached-ring level) and realize the QUANTUM form ON THE SAME SUPPORT.
3. The coupling/flux context: O1 flux IN-left/OUT-right (b6a6d2ae9); the doctrine's expectation 2: L/R engines as local update rules w/ OPPOSITE index signs; index-0 controls must show NO L/R distinction.

## The object
A finite quantum cellular automaton on the committed ring support: qubits (or pinned-dim systems) on ring cells; LOCAL unitary/CPTP update rules in the two-phase partitioned (brickwork/checkerboard) form — the even-phase then odd-phase local gates realizing the alternating discipline, the block form realizing paired. Then:
A. THE INDEX/INFORMATION-FLUX INVARIANT: compute a quantized chirality/index invariant for the realized rules (for the brickwork/partitioned class, compute the standard index via the established finite procedure — overlap/rank data of the two-phase decomposition, exact rationals where feasible; document the exact definition used + cite it as standard math). A right-shift rule must give index +1, left-shift -1, a non-shifting local rule 0 — these three as computed CALIBRATION rows.
B. THE L/R REALIZATION (doctrine expectation 2): two rules realizing the L and R engines' chirality (per O1: opposite information-flux signs) — compute their indices; OPPOSITE signs = the expectation earned; the INDEX-0 CONTROL: a non-chiral rule must show NO L/R distinction under the same probe family (the flipping control — if it shows a distinction, the index alignment is killed, report plainly).
C. LOCALITY-CHANGES-COUPLING (doctrine expectation 3, bounded): one computed comparison — the local brickwork coupling of two ring engines vs the v3-style global coupling on matched state counts: do the joint terminal/orbit structures differ (the locality effect computed, not asserted)?
D. The typed-information hook (bounded): one row family — the information flux per step (the index's operational meaning) computed alongside the typed entropy discipline.

## Controls
index calibration rows (shift +1/-1/0 as computed); gauge/local-basis-change invariance of the index (a reparameterized rule must give the SAME index — if not, the computation is broken); the classical limit (dephased/classical restriction must reproduce the committed v0 phase structure); order-shuffle (B constraints still bind); falsifier branches reachable (test one).

## Engineering contract
Honest TOOL_INTENT_MATRIX (genuine quantum machinery: Julia reference w/ QuantumOptics/QuantumClifford + package_observables; JAX w/ real quantum packages where load-bearing; PyTorch honest); SMT binds computed index values/calibrations w/ non-tautological flips; envelope via scripts/build_three_engine_envelope.py; validators (honest combo) + packet validator (post-audit-idempotent) + pytest; classification scratch_diagnostic, promotion_allowed=false; small sizes (the resource guard). End with: the index table (calibrations + L/R + index-0 control), the locality comparison, every validator command + status.
