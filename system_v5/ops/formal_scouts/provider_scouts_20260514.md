# Provider Scouts 2026-05-14

Status: proposal-only, noncanonical

## Grok / xAI

Route: direct xAI API through `OpenAI(base_url="https://api.x.ai/v1")`

Result: completed.

Proposal returned:

> SU(2) principal bundle over Hopf-fibered S^3 base, with Weyl spinor sections
> on the total space enforcing noncommutative holonomy reduction;
> entropy-minimized topological constraints (Chern-Simons classes) define the
> manifold harness immediately prior to projection.

Codex classification: useful theme, not code-ready. Needs mapping to real repo
callables before any formal-scout translation.

Likely repo-grounded translation targets:

- `sim_su2_unit_quaternion_vector_action_survivor_classes.py`
- `sim_hopf_connection_one_form_loop_integral_survivor_classes.py`
- `sim_weyl_nested_shell.py`
- `sim_clifford_spinor_double_cover_micro.py`
- `sim_pure_lego_knots_topo_entropy.py`

Importability check: completed. All five target files loaded through
`importlib.util.spec_from_file_location`.

Callable surfaces seen:

| Path | Callable examples |
|---|---|
| `sim_su2_unit_quaternion_vector_action_survivor_classes.py` | `qmul`, `qconj`, `qnorm2`, `vector_action`, `boundary_predicates`, `main` |
| `sim_hopf_connection_one_form_loop_integral_survivor_classes.py` | `connection_integral`, `fiber_loop_row`, `base_lift_loop_row`, `z3_orientation_boundary`, `main` |
| `sim_weyl_nested_shell.py` | `build_spinor_cloud`, `betti_from_cloud`, `run_positive_tests`, `run_negative_tests`, `run_boundary_tests` |
| `sim_clifford_spinor_double_cover_micro.py` | `_rotor`, `_same_sandwich_report`, `run_positive_tests`, `run_negative_tests`, `run_boundary_tests` |
| `sim_pure_lego_knots_topo_entropy.py` | `partial_trace_clean`, `von_neumann_entropy`, `block_2_kauffman_yang_baxter`, `block_3_topological_entropy`, `block_4_braid_group`, `main` |

## Gemini

Route: `gemini -p ... --output-format text`

Result: blocked.

Reason: CLI entered interactive browser authentication flow. The stuck worker
process was killed and is not counted as a completed scout.

Next liveness task: configure Gemini CLI for headless API-key use or use a
different direct Gemini API wrapper that writes a receipt without opening auth.

## Sonnet

Route: Claude Bridge direct Sonnet audit.

Result: completed.

Model: `claude-sonnet-4-6`

Receipt:

`/tmp/codex_claude_bridge/20260514T180451Z-in-users-joshuaeisenhart-desktop-codex-ratchet-a-33f03f6b4eb2.receipt.json`

Output:

`/tmp/codex_claude_bridge/20260514T180451Z-in-users-joshuaeisenhart-desktop-codex-ratchet-a-33f03f6b4eb2.json`

Key findings:

- Existing scouts were mostly gate-compliant.
- Missing schema fields: explicit boundary section, nearby-variant count/pass
  summary, and why the result does not live in `system_v4/probes`.
- Gemini needs a closure criterion.
- Grok translation targets needed importability verification.

Codex action taken:

- Added `boundary`, `nearby_variants`, and `why_not_v4_probes` to both scout
  result schemas.
- Updated `validate_formal_scout_results.py` to enforce those fields.
- Verified the five Grok translation target files are importable.
