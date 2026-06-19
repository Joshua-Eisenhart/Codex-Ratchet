# Floor Packet Provenance And Content Audit - `gcm_constraint_carve_floor_v0`

Bottom line: VERDICT = `quarantine-release-as-redundant-scratch`.

The packet is most probably an unattributed duplicate Codex-side scratch run created inside the stop-order/re-anchor window, after `/tmp/build_mc_carve.md` and before `/tmp/build_carve_v1.md`. Its computations are internally coherent at a narrow 24-state floor ceiling, but it is not a real new finding and should not be promoted over the audited `gcm_constraint_carve_v1` lane. It may be referenced only as redundant prior-art scratch: "24 finite states -> 6 closed survivors -> 6 singleton probe classes; no eight-region terrain split."

## Provenance Investigation

Evidence checked:

- Floor packet timestamps:
  - `build_card.md`, `gcm_constraint_carve_floor_v0.py`, and `validate_gcm_constraint_carve_floor_v0.py` were born/modified `2026-06-12T13:50:07-0700`.
  - result JSON was born/modified `2026-06-12T13:50:34-0700`.
  - `tests/` was born `2026-06-12T13:48:00-0700`.
- `/tmp` cards:
  - `/tmp/build_mc_carve.md` born/modified `2026-06-12T13:34:38-0700`.
  - `/tmp/build_carve_v1.md` born/modified `2026-06-12T14:10:25-0700`.
- Git state:
  - `git status --short -- system_v6/sims/gcm_constraint_carve_floor_v0` reports the directory as untracked.
  - `git log -- system_v6/sims/gcm_constraint_carve_floor_v0` has no committed history.
- Hashes:
  - floor build card: `48462a50da4376fb2937d7941ba95d42610fafb320a012af64a363f13a3a5695`
  - floor source: `6a8c00ca025e5b2c1b6318843f620090dea7d4def5a924b21b8f391d1ab2634a`
  - floor result: `25965e3e7194c2145a1b3182a1c1d85485d5d76f9a7f18e99a4a10595214346f`
  - `/tmp/build_mc_carve.md`: `ade332ab70eba58c8dc8fbca9c04df6a502115a1650324686a866a0fe7ae07fe`
  - `/tmp/build_carve_v1.md`: `81a2ab015b6900f7499eceaef6ecfab1c331b1016b5edeb2790a9ce77374c0fc`

Overlap finding: direct character-similarity was low, not copy-paste:

- floor build vs `/tmp/build_mc_carve.md`: `0.049`
- floor build vs `/tmp/build_carve_v1.md`: `0.033`
- floor source vs `/tmp/build_mc_carve.md`: `0.013`
- floor source vs `/tmp/build_carve_v1.md`: `0.007`

The style tells are nevertheless Codex-run-shaped: `Build Card` heading, "Status" line, explicit "Claim ceiling", stop-order/re-anchor authority list, pytest command, JSON result writer, validator, tests, and cautious negative terrain wording. The floor packet's birth at `13:50` places it after the real first-carve card at `13:34` and before the v1 repair card at `14:10`; the v1 card explicitly names `gcm_constraint_carve_floor_v0` as an "unattributed floor packet" and "PRIOR ART ONLY" whose provenance is under investigation.

Most probable origin: a duplicate or side Codex builder run in the stop-order window, likely attempting a smaller "finite floor" before the larger v0/v1 carve lane stabilized. It is not textually copied from either `/tmp` build card, but it shares the same live route context and phrasing patterns.

## Content Audit

The packet claims:

- `scratch_diagnostic` only;
- no manifold admission, no axis claims, no engine claims;
- a minimal finite object with `S`, `C`, `P`, `~_P`, executable admissibility, order maps, controls, and a negative terrain readout;
- authority from the stop order, GCM re-anchor, root axioms draft, and constraint-manifold architecture doc.

The computations support that narrow claim:

- candidate space: 24 states with schema `[shell, phase_parity, orientation, memory]`;
- constraints: `C_history_consistency`, `C_N01_order_visible`, and closure under `R`, `D`, `R_after_D`, `D_after_R`;
- carve result: 6 survivors, 18 killed;
- quotient: 6 singleton probe classes;
- carved structure: one connected component of size 6;
- terrain readout: `no_8_terrain_regions_in_this_floor`;
- controls: empty-C gives 24; drop-history gives 12; drop-N01 gives 12; drop-closure gives 10; overconstrained orientation-one-only gives 0.

Fresh checks run:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_constraint_carve_floor_v0/validate_gcm_constraint_carve_floor_v0.py system_v6/sims/gcm_constraint_carve_floor_v0/results/gcm_constraint_carve_floor_v0_results.json
```

Result: `ok=true`, `errors=[]`.

```text
PYTHONPATH=system_v6/sims/gcm_constraint_carve_floor_v0 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/gcm_constraint_carve_floor_v0/tests/test_gcm_constraint_carve_floor_v0.py
```

Result: `4 passed`.

The failed no-argument validator invocation was a CLI usage failure only: this validator requires a result JSON argument. It is not a content failure.

## Relation To Carve v0 And v1

This packet does not duplicate the audited `gcm_constraint_carve_v0` computation. It uses a different and much smaller carrier:

- floor: 24 tuple states -> 6 survivors -> 6 singleton classes;
- v0: 125 grid candidates -> 8 survivors -> 4 probe classes under a terrain-aware C4 pin;
- v1: 125 grid candidates -> 16 survivors -> 8 quotient classes after terrain-blind repair, but still failed the validator-tooth checkpoint.

It also does not contradict audited v1. The floor's negative terrain verdict is consistent with its own smaller carrier and does not bear on v1's 125-candidate terrain-blind repair lane. The v1 build card correctly quarantines the floor packet as prior art only; v1 does not depend on it as authority.

## Verdict

`quarantine-release-as-redundant-scratch`.

Meaning:

- release from hard quarantine only as a redundant scratch reference;
- keep it below v0/v1 and below any committed/canonical carve claim;
- do not cite it as the first real `M(C)`, a manifold substrate, a terrain result, a v1 confirmation, or source authority;
- do cite it, if useful, only as a small finite-floor smoke test that validates a 24-state closure/quotient/negative-terrain toy carve.

No real new finding is admitted.

