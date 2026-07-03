
tokens used
100,121
**Xi Candidate Test Spec**

(a) **Exact construction**

- `Xi_pt`: pointwise bridge family `x -> (c_x, rho_c_x(x))`, with `c_x = A_x|B_x`. It is source-backed but still needs a real bipartite cut-state, not a single spinor. See [AXIS_0_1_2_QIT_MATH.md](/Users/joshuaeisenhart/Codex-Ratchet/system_v5/READ%20ONLY%20Reference%20Docs/AXIS_0_1_2_QIT_MATH.md:101).
- `Xi_shell`: pointwise shell-cut family `x -> {(r, w_r, rho_A_rB_r(x))}_r`; kernel form is `sum_r w_r I_c(A_r>B_r)`. Typed contract requires `(r, w_r, A_r|B_r, rho_r)` with real bipartite `rho_r`. See [AXIS_0_1_2_QIT_MATH.md](/Users/joshuaeisenhart/Codex-Ratchet/system_v5/READ%20ONLY%20Reference%20Docs/AXIS_0_1_2_QIT_MATH.md:107), [AXIS0_TYPED_SHELL_CUT_CONTRACT.md](/Users/joshuaeisenhart/Codex-Ratchet/system_v4/docs/AXIS0_TYPED_SHELL_CUT_CONTRACT.md:13), [AXIS0_TYPED_SHELL_CUT_CONTRACT.md](/Users/joshuaeisenhart/Codex-Ratchet/system_v4/docs/AXIS0_TYPED_SHELL_CUT_CONTRACT.md:27).
- `Xi_hist`: history-window bridge `h|[t0,t1] -> {(t, c, w_c, rho_c(t))}_{t,c}`; functional is `(1/T) int sum_c w_c I_c(c; rho_h(t)) dt`. Typed contract requires real sample `t`, typed cut `c in C`, cut weight `w_c`, and bipartite `rho_c(t)`. See [AXIS_0_1_2_QIT_MATH.md](/Users/joshuaeisenhart/Codex-Ratchet/system_v5/READ%20ONLY%20Reference%20Docs/AXIS_0_1_2_QIT_MATH.md:108), [AXIS0_TYPED_HISTORY_WINDOW_CUT_CONTRACT.md](/Users/joshuaeisenhart/Codex-Ratchet/system_v4/docs/AXIS0_TYPED_HISTORY_WINDOW_CUT_CONTRACT.md:13), [AXIS0_TYPED_HISTORY_WINDOW_CUT_CONTRACT.md](/Users/joshuaeisenhart/Codex-Ratchet/system_v4/docs/AXIS0_TYPED_HISTORY_WINDOW_CUT_CONTRACT.md:27).

(b) **Quotient-lift test**

For any active probe epoch `M`, quotient classes are `S/~_M` buckets keyed by `probe_vector(rho, probes)`, with class fields `class_id`, `probe_signature`, `member_keys`, `member_words`, and `representative_word`. See [manifold_dual_ratchet_foundations_v0_1_numpy.py](/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/manifold_dual_ratchet_foundations_v0_1/manifold_dual_ratchet_foundations_v0_1_numpy.py:343).

- `Xi_shell` passes only if for every quotient class `Q` with multiple representatives, every representative `s in Q` emits the same shell-family descriptor after projection to quotient-level observables:
  `ShellDesc_M(s) = {(r, w_r, cut_signature_M(A_r|B_r), Phi0_r/sign/rho_digest_M)}_r`.
  Any dependence on `representative_word` or raw token id is failure.
- `Xi_hist` passes only if for every quotient-class trajectory `Q_[t0,t1]`, the history-window output is independent of which representative trajectory is chosen inside each class. Precisely: for any two lifted histories `h` and `h'` such that `h_t ~_M h'_t` for all aligned `t` in the window,  
  `HistDesc_M(h|[t0,t1]) == HistDesc_M(h'|[t0,t1])`, where descriptor includes `(t or normalized window index, c, w_c, cut_signature_M(c), Phi0_c(t)/sign/rho_digest_M)` modulo permitted quotient relabeling. If appending different same-class reps changes `rho_c(t)`, sign structure, weighted `Phi_0`, or stabilization step, `Xi_hist` is not quotient-lifted.
- `Xi_pt` should be tested the same way if kept in Gate 4: `PtDesc_M(s)` must be constant on representatives in `Q`. If not, it stays point/raw-carrier diagnostic only.

(c) **Ratchet inputs**

Minimum supply:

- Active quotient epoch: probe family `M`, rounding/digest discipline, class roster, class ids, class members, and representative map.
- Cut lattice over quotient classes before Axis 0 readout; current v0_1 says `quotient_classes -> cut_lattice -> Xi_candidate_density -> Phi_0_readout`. See [manifold_dual_ratchet_foundations_v0_1_numpy.py](/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/manifold_dual_ratchet_foundations_v0_1/manifold_dual_ratchet_foundations_v0_1_numpy.py:277).
- For `Xi_hist`, append-only ledger `H`: v0_1 has Hell and Purgatory JSONL append surfaces plus in-memory `history["Xi_hist"][cut_id]` windows. Map `H` fields as:
  `step -> t`; `candidate_id/candidate_key/word/bracket -> representative token`; `origin_purgatory_id/lineage_parent_purgatory_id/fresh_replay_candidate_id -> lineage/replay`; `tier/status/tier_event/status_before/status_after/reason -> admissibility event`; `admitted_key/admitted_word -> accepted representative`; `dwell_time/attempts -> window metadata`. See [manifold_dual_ratchet_foundations_v0_1_numpy.py](/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/manifold_dual_ratchet_foundations_v0_1/manifold_dual_ratchet_foundations_v0_1_numpy.py:657), [manifold_dual_ratchet_foundations_v0_1_numpy.py](/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/manifold_dual_ratchet_foundations_v0_1/manifold_dual_ratchet_foundations_v0_1_numpy.py:701), [manifold_dual_ratchet_foundations_v0_1_numpy.py](/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/manifold_dual_ratchet_foundations_v0_1/manifold_dual_ratchet_foundations_v0_1_numpy.py:739).

(d) **Discriminating experiment**

Run the docs’ bakeoff, but with quotient-lift added: same geometry/history sample under `Xi_shell`, `Xi_hist`, and brief `Xi_pt`; measure sign, monotonicity, perturbation sensitivity, loop-family stability, plus representative-independence on multi-rep quotient classes. The older bakeoff language says shell-strata pointwise was geometry-blind, point-reference passed fiber/base, and history-window stayed nontrivial; bounded next sims include `History-vs-pointwise Ax0` and `Xi-bridge bakeoff`. See [AXIS_0_1_2_QIT_MATH.md](/Users/joshuaeisenhart/Codex-Ratchet/system_v5/READ%20ONLY%20Reference%20Docs/AXIS_0_1_2_QIT_MATH.md:180), [AXIS_0_1_2_QIT_MATH.md](/Users/joshuaeisenhart/Codex-Ratchet/system_v5/READ%20ONLY%20Reference%20Docs/AXIS_0_1_2_QIT_MATH.md:217).

(e) **Failure semantics**

Use the `Xi_ref` precedent exactly: full singleton-class success is only `constructed_untested_nontrivially_at_full_resolution`; nontrivial multi-rep failure demotes the candidate. `Xi_shell` failure => `demoted_to_raw_or_shell_labeled_carrier_discriminator`, not a quotient bridge. `Xi_hist` failure => `demoted_to_history_proxy_or_raw_trajectory_discriminator`, not a quotient-lifted history bridge. `Xi_pt` failure => pointwise/raw discriminator only. Precedent: `Xi_ref` failed coarse single-Z representative-independence with 3 multi-rep classes and 9 failures, then was demoted to `raw-carrier discriminator`. See [RESULTS.md](/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/ratchet_formal_gates_v1/results/RESULTS.md:23), [RESULTS.md](/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/ratchet_formal_gates_v1/results/RESULTS.md:40), [RESULTS.md](/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/ratchet_formal_gates_v1/results/RESULTS.md:55).


