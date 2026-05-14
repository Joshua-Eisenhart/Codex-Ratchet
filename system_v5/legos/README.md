# V5 Primitive Legos

Status: clean primitive shelf, not a scout surface.

Rules:

- One file per mathematical primitive.
- Names describe the math directly.
- Each result uses `classification: lego`.
- Each result has positive checks, graveyard companions, a boundary check, tool
  manifest, and claim ceiling.
- No target-system labels, no provider prose, no writes to `system_v4/probes`.

Current legos:

| Lego | Result | Tool |
|---|---|---|
| `density_matrix_trace_positive_semidefinite.py` | `results/density_matrix_trace_positive_semidefinite_results.json` | numpy |

Validate:

`/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/legos/validate_lego_results.py`
