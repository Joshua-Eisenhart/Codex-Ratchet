# Independent Audit Verdict - gcm_entropy_family_sweep_v0

Fresh audit / read-only audit. Auditor: independent cross-backend auditor. Freshness tier:
TIER-2 results-available. Authorized live write: this file only. No git add/commit.

Bottom line: VERDICT = GENUINE-WITH-CAVEATS. The packet genuinely computes the available
1Q scalar entropy-family rows over the frozen GCM attached carrier, and the degeneracy is the
mathematics of rank-one density spectra, not a disguised computation failure. Claim ceiling:
`scratch_diagnostic_carrier_and_pins_relative_entropy_family_sweep_at_1Q`;
`promotion_allowed=false`; `formal_admission_allowed=false`; not THE manifold, not Axis0,
not bridge/runtime entropy, not 2Q+ entanglement evidence.

Caveats:

- `G1_shell_pattern_is_carved_grid_signature` is inherited from `gcm_geometry_attach_v0`.
  The shell readout is conditional on the attached carved-grid/probe-signature carrier, not
  independent manifold geometry.
- `G2_class_mixture_row_is_computed_but_collapsed_on_this_attached_object`. Panel 11 was
  right that class/mixture entropy is the informative 1Q level in principle. This packet did
  compute that row, so it is not a skipped-row gap. On this inherited attach object, however,
  each quotient class has two members with the same emitted 1Q density matrix, so the class
  average remains rank-one and all class mixed-state scalar entropies remain zero. Do not cite
  this v0 as evidence that class/mixture entropy has been made informative.

## What I Checked

- Standards and scope: `audit_standards_codex_v1`, especially G.2a builder/audit idempotency
  from birth; the entropy rule in `gcm_layer_stack_reference_20260612.md`; the wiki entropy
  protocol; panel 11; the co-ratchet availability doctrine; and the inherited attach audit.
- Coordinates: layers `3-12 (entropy dimension)`, nesting `integrated-onto-the-carve`, qubit
  depth `1Q`.
- Result surfaces: source, build card, builder self-assessment, result JSON, envelope JSON,
  validator script, test file, upstream attach result, attach audit verdict, and the boundary
  helper.
- Runtime hygiene: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
  scripts/codex_runtime_env_doctor.py --json` returned `summary.ok=true`,
  `install_state=stable_observed`, no failures, no warnings, and no active installers.

## Recomputations

Degeneracy check:

- Independently recomputed von Neumann, Renyi alpha `2`, Tsallis q `2`, and linear entropy
  from the attached 1Q density matrices for all 16 survivors, including the requested first
  six survivor rows.
- Every recomputed survivor spectrum was `[1.0, 0.0]`.
- Every recomputed family value was zero within tolerance: vN `0`, Renyi-2 `0`, Tsallis-2
  `0`, linear `0`.
- This confirms the builder's core claim: all 1Q scalar spectrum families degenerate on the
  pure attached carrier because that is what pure-state entropy does.

Class-level mixed-state question:

- The packet did compute `class_mixed_state_entropy_rows` for all 8 quotient classes.
- I recomputed the class matrices by averaging member density matrices from the upstream
  attach object maps.
- Each class had `member_count=2`; each averaged class density matrix still had spectrum
  `[1.0, 0.0]`; all class mixed vN and linear entropies recomputed as zero.
- Therefore this is not the panel-11 "missing row" failure. It is a real but collapsed row
  on this specific attached carrier. The eight density matrices are distinct as densities,
  but the scalar entropy spectrum does not separate them.

Shell-weighted row:

- Recomputed shell occupancy from the attach rows:
  `0:2`, `pi/8:4`, `pi/4:4`, `3pi/8:4`, `pi/2:2`.
- Recomputed shell log-surprisal values:
  `-ln(4/16)=1.386294361119891` and `-ln(2/16)=2.079441541679836`.
- Recomputed shell distribution entropy: `1.559581156259877`.
- The packet is scoped correctly: `shell_log_surprisal` separates two occupancy-count bins,
  not the five shell identities and not the eight quotient classes.

Availability ladder:

| family | packet status | audit verdict |
|---|---|---|
| `von_neumann_1q` | admissible at this layer | correct: needs a normalized 1Q density matrix |
| `renyi_ladder_1q` | admissible at this layer | correct: needs a normalized 1Q density spectrum plus alpha list |
| `tsallis_ladder_1q` | admissible at this layer | correct: needs a normalized 1Q density spectrum plus q list |
| `min_max_linear_1q` | admissible at this layer | correct: one-shot/extremal and linear spectrum readouts are available at 1Q |
| `shell_weighted_forms` | admissible at this layer | correct: needs shell strata and survivor-to-shell lineage |
| `class_level_mixed_state_entropies` | admissible at this layer | correct and computed, but collapsed on this attached object |
| `conditional_entropy` | requires more structure | correct: needs a named bipartition and joint state `rho_AB` |
| `mutual_information` | requires more structure | correct: needs `rho_A`, `rho_B`, and `rho_AB` for a bipartition |
| `coherent_information` | requires more structure | correct: needs a directed cut/channel state, not just 1Q density |
| `entanglement_negativity` | requires more structure | correct: needs 2Q+ bipartition and partial transpose operation |
| `entanglement_spectrum_and_log_negativity` | requires more structure | correct: needs 2Q+ entanglement/cut structure |
| `bridge_history_transport_weighted_variants` | requires more structure | correct: needs bridge/history/transport maps not installed here |

Controls and enforcement:

- Fresh read-only validator function call returned `ok=true`, `errors=[]`.
- Fresh substrate check via the packet validator path returned positive `ok=true`.
- Fresh lineage-free negative returned `ok=false` with the expected missing lineage errors.
- Phase-quotient invariance returned `all_entropy_families_invariant=true`.
- Scrambled-class control is honestly scoped: no scalar entropy family separates classes, so
  the control has no false separation to break.
- G.2a passed before this audit file was written: envelope boundary flags were true and
  `builder_boundary_errors=[]`.

## Panel-11 Conformance

Panel 11 expected pure-state 1Q vN/Renyi/Tsallis degeneracy; this packet conforms. It also
expected the informative levels to be class/mixture, shell-weighted, and 2Q+. The packet
covered class/mixture and shell-weighted rows, and correctly marked 2Q+/cut families as
unavailable. The class/mixture row did not become informative here because the inherited
attach object pairs same-density members inside each quotient class.

## Citation Rule

Allowed citation:

`gcm_entropy_family_sweep_v0` = `GENUINE-WITH-CAVEATS` scratch diagnostic showing that, on
the frozen GCM 1Q attached carrier, all pure survivor scalar spectrum entropy families
degenerate to zero; class-level mixed-state entropy rows were computed for all 8 classes but
also remain rank-one/zero on this object; shell log-surprisal separates exactly two
occupancy-count bins; conditional, mutual, coherent, and entanglement families are
unavailable until the required bipartition/cut/channel/2Q+ structure exists.

Required caveats on every citation:

- Carry inherited `G1_shell_pattern_is_carved_grid_signature` from `gcm_geometry_attach_v0`.
- Carry `G2_class_mixture_row_is_computed_but_collapsed_on_this_attached_object`.

Forbidden citation:

Do not cite this as class-separating entropy evidence, shell-identity separation, Axis0/cut
entropy, bridge/history/transport entropy, 2Q+ entanglement, runtime flux, THE manifold,
formal admission, or promotion beyond scratch diagnostic.
