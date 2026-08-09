# CB v9 — state and plan, written IN the repo (2026-08-06)

**Location rule for this work:** everything lands in
`/Users/joshuaeisenhart/Codex-Ratchet/`. Nothing counts as done until it
exists in this checkout, on the branch the owner is standing on.

## Verified state of THIS checkout, at time of writing

| Fact | Value |
|---|---|
| Branch | `claimgate/bypass-regression` |
| `constraint_box/VERSION` | **absent** — v9 scaffolding from `a9909489` is not in this working tree |
| `constraint_box/formal/` | present here (it was missing from the shipped archive) |
| Products present | constraint_box, claimgate, claimgate_plugin, sim_engines, system_v4..v8, external_sim_estate, fuel_gate, ratchet_engine |
| `REPO_LAYOUT.md` | dated 2026-04-14, describes system_v4/v5 only — stale by four system generations |

`a9909489` ("feat(v9): separate products and index live engine estate")
is on `origin/main`: 75 files, 12,826 insertions — but the composition
is 6,637 lines of JSON, 4,133 other (a 4,020-line Julia
`Manifest.toml`), 816 markdown, 1,234 Python. It is boundary
scaffolding: VERSION files, PRODUCT_BOUNDARY stubs, registries,
READMEs. It is not the consolidation that was asked for.
