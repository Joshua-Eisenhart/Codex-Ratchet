# Direct rerun receipts for the formerly dark mathematics

These commands were executed from the v0.7 bundle root after repairing ten inherited `system_v7/constraint_core` self-path assumptions. They are direct work receipts, not promotion receipts.

| Instrument | Fresh status | Observed result |
|---|---|---|
| `j3o_bloch_body_entropy_pawl_sim.py` | PASS | Fano norm-composition residual \(3.55\times10^{-15}\); \([e_1,e_2,e_4]=2e_7\); trace/positivity preserved; epsilon-shadow pawl monotone; raw entropy and wrong-fixed-point controls nonmonotone; sedenion zero-divisor kill fires. |
| `jordan_octonion_entropy_pawl_sim.py` | PASS | J2(O) primitive-flow epsilon-shadow pawl monotone; raw entropy and wrong fixed point nonmonotone; sedenion control breaks construction. |
| `jordan_dissipator_pawl_v2_sim.py` | PASS diagnostic with negative | Broader rotated-Peirce/automorphism/quadratic dissipator gives `pawl_fails` for both J2(O) and J3(O); trace distance to the computed fixed point remains monotone. This blocks a general Jordan entropy-pawl claim. |
| `jordan_dpi_probe_v4_sim.py` | PASS | 72 states × 9 steps, zero DPI violations; all associator trajectories above floor; associative surrogate differs by 0.06437 in D and 0.12431 in spectrum; wrong sigma breaks. |
| `malcev_signature_search_sim.py` | PASS | Reference detector separates Im(H)=Lie, Im(O)=Malcev-not-Lie, random R7=neither; engine harvest has 7 Lie, 3 neither, and zero Malcev-not-Lie hits. |
| `spin9_stabilizer_op2_coset_sim.py` | PASS | F4=52, primitive stabilizer=36, OP2 coset=16; generic controls 28/24; corrupted Fano breaks 52; Spin7=21, G2=14, embedded-J3(C) stabilizer=16. Supportive z3 certificate was attempted but unavailable in this container. |
| `engine_field_choi_jordan_albert_probe_sim.py` | PASS | H2(O)/H3(O) Jordan patterns survive; H4(O), wrong-Fano, and sedenion controls fail; associative R/C/H H4 controls pass. Candidate remains noncanonical. |
| `choi_field_multiaxis_null_albert_stress_sim.py` | PASS | Finite Choi objects remain CP/TP and distinct; mirror measures are related but not strictly isomorphic; Albert dependency present with low claim ceiling. |
| `engine_pair_basin_map_sim.py` | PASS honest mix | One finite basin per engine; nesting holds; mirror relation fails; shuffle moves centers; commuting control collapses. |
| `fep_known_unknown_basin_v2_sim.py` | PASS honest mix | Occupied/transition partition holds; repaired schedule-only allocation is no-split; shuffled control no-split; entropy initialization has no measured shift. |
| `unified_attractor_basin_seven_axes_sim.py` | PASS | All seven axes load-bearing in its erasure battery; L0–L3 finite distinguishability checks pass; uniqueness and admission remain open. |
| `memory_carrier_belief_basin_sim.py` | BLOCKED CURRENT CONTAINER | Direct replay stopped at `ModuleNotFoundError: torch`. The preserved prior receipt reports four-pattern multistability surviving 10× dwell and a linear-smoother collapse. It remains preserved evidence, but this bundle does not call it a fresh local rerun. |

The first direct attempts at the J3(O), Jordan-DPI, and Spin(9) scripts completed their mathematics but failed while writing/importing through the absent desktop-style repository path. That was a real portability defect. The ten affected recent instruments now resolve `SOURCE_PATH`, `RESULT_PATH`, and sibling imports relative to their own `sims_and_scripts/` directory. `preservation/standalone_path_audit.py` enforces the repair.

All entries remain `scratch_diagnostic` / `promotion_allowed=false`. Direct execution has teeth as reproducibility evidence; it does not bypass the Ratchet gates.
