# Manifold capability campaign v1 — recovered source

This folder preserves the exact campaign source and the compact result/map
bytes recovered after the computer restart. The source was reconstructed from
the recorded `apply_patch` events in the Codex rollout and must hash to:

`b15212a5908b9be0010d42424549e684d5d392c9f8e7e9ce9f270841f11481ff`

The result and map were recovered from complete numbered command output and
must hash to:

- result: `6cde10de8957aa020ac95e71d0b8138f6bc4611c6e4ba7a7558d2d9596b715b0`
- map: `452105469c9a879fea7510dba100e60e13e732226f44f95d16a1208f1c882ed5`

The restart initially lost:

- `probe_rows.jsonl` — expected SHA
  `7648f2d338fbfbf30cf937e469f112c2a4bbf0c93ce5ca20a0cae01a2375b6e2`
- `gate_rows.jsonl` — expected SHA
  `eda6f185f7ea80f67254d34e335fd4a34304e880ee6799e236be5c48c4bf6683`
- the byte-identical `final2` replay directory.

The repo-held source was subsequently run twice. Both new runs reproduced the
expected probe-row, gate-row, and map hashes, and their four output files were
byte-identical. `REPLAY_CUSTODY.json` binds those observations. Raw row files
are deliberately not duplicated in this source folder or the lean bundle;
rerun the source to recreate them.

This remains a scratch diagnostic. Do not call it an admitted basin, Light
wheel, Heavy profile, manifold completion, or scientific result. It is not the
next research operation: structured support-extension/probe-restriction maps
must be tested before another integrated manifold campaign.
