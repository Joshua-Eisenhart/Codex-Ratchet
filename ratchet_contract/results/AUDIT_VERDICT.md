# Contract v0 audit — CLEAN (fresh-context opus adversarial, 2026-07-20)

CONTRACT V0 AUDIT: CLEAN — MSS is pure partition_coarser (no smuggled score), the
IDENTITY_GATE FAIL is behaviorally earned, gates flip on constructed inputs, the kernel is
a faithful port, no verdict is LLM-judged or hardcoded.

Attacks + results (found_fabrication:false on all 6):
1. pairwise_mss = 4 boolean guards over partition_coarser only; cells_A/B appear only in the
   report dict, never a guard. No score/count/weighted sum. Stages 1-2 gate eligibility (HOLD)
   and drop out when both pass.
2. toy_raw_label IDENTITY_GATE FAIL recomputed (reidentify [0,1,2,3,4] strictly finer than
   probes [0,1,0,2,3]); falsifier: stripping declared_primitives label still FAILs on behavior;
   no name-branching (grep clean).
3. Gates non-vacuous: persistence + extension verdicts flipped on constructed mutant inputs.
4. persistence/evolvability/extension push D through a continuation and re-check with the same
   kernel -> PASS/FAIL eligibility only, no score. D-collapse and primitive-smuggle FAIL
   branches fire on constructed inputs.
5. partition_coarser character-identical to ratchet_engine.py:414-421; normalise_partition
   identical up to variable names.
6. No network/model imports; every verdict a boolean over computed partitions; reason strings
   are post-hoc labels.
Anti-tautology falsifier: altering the measured reidentify relation moved the verdict off
A_WEAKER -> by-construction-constant hypothesis KILLED, load-bearing claim SURVIVED.
Hand re-derivations matched selfcheck.json sha256 digests exactly.

TWO FINDINGS back to builder (neither fabricates a verdict):
- F1 (low-med): contract.py ControlSet.negative / expected_distinguishable are declared and
  populated by toys but NO gate reads them (grep: zero consumers). Docstring promises an
  ablation check that does not run. Dead scaffolding + over-promising docstring. (Alias
  discrimination is really earned by IDENTITY_GATE, so no verdict faked.)
- F2 (low): roster toys exercise evolvability FAIL only via evolve()->None; D-collapse /
  primitive-smuggle / buildability-FAIL branches verified by the auditor on constructed inputs
  but ABSENT from the selfcheck receipt. Code genuine; receipt under-shows discrimination.
