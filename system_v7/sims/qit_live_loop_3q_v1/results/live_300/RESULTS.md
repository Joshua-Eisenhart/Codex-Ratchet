# QUARANTINE_EXPLORATORY: qit_live_loop_3q_v1 results

classification='scratch_diagnostic'; promotion_allowed=false.

`belief_bloch` is the reduced q0/signal-qubit projection of the 3q belief state, not the full 3q state.

L/R non-claim: 3q files expose the 16-stage contract, not separate runnable L/R sheet engines.

Python trio passed: `True`.
Julia passed: `True`.
All-substrate action match count: `300/300`.
Python trio action match count: `300/300`.
Max belief_pauli_63 abs dev: `4.196643033083092e-14`.
Max surprise_bits abs dev: `5.329070518200751e-12`.
Max fe_gradient abs dev: `5.329070518200751e-12`.
Max efe_scores_16 abs dev: `1.1723955140041653e-13`.
local stream integrity check ok: `True` over `300` ticks.
Detector report: `detector_report.json`.

## v1.1 repairs

- R1: Lüders conditioning on the q0 projective outcome + hill relaxation channel; no RATE=0.5 convex belief blend.
- R2: `efe_scores_16` is a schema-stable legacy field name; the quantity is the cost surrogate, not active-inference EFE. It is a reactive-risk + entropy cost surrogate with persistence-prior preference.
- R3: chosen stage channel feeds back as the next tick predict step; world outcomes remain fixture-driven.
- R4: NumPy, JAX, PyTorch, and Julia execute their per-tick loops in their own stacks; only fixture and JSONL writing are shared.
- R5: validator gates every per-tick comparison including `efe_scores_16` and exact action indices.
- R6: `surprise_bits` is an EPS-regularized Umegaki surrogate, not exact relative entropy.
- R7: `signal_povm` is fixture metadata echoed for audit, not used in inference.
- R8: Julia implements the same R1-R3 loop semantics in native Julia operations.
- R9: Page-Hinkley + CUSUM detector report is written over the fresh live stream.

## Detector

Tick 100 dual fire: `None`; near 100: `False`.
Tick 200 dual fire: `None`; near 200: `False`.

## Julia parity

Julia bar: `1e-09`.
Julia vs oracle belief_pauli_63 max abs dev: `2.1316282072803006e-14`.
Julia vs oracle surprise_bits max abs dev: `5.329070518200751e-12`.
Julia vs oracle fe_gradient max abs dev: `5.329070518200751e-12`.
Julia vs oracle efe_scores_16 max abs dev: `1.1723955140041653e-13`.
Julia action indices exact: `True`.

Fixture sha256: `84d44b4c5969a921b39e4dbcfb68db3678b58dbbc0d1d385e0ce8f13b43436eb`.
