# Source-Lock Refresh Wave - 2026-06-12

Bottom line first: 7 packets refreshed in place with normalized non-lock values unchanged, 7 packets stopped and were restored because current-source regeneration either changed non-lock result fields or failed a writer, and 1 RED_STATE_NOTE packet was skipped unchanged. No git add or commit was run.

Claim ceiling: source-lock refresh receipt only. This is not a promotion, admission, or broader validity claim.

## Scope

Authority inputs:

- Lane A commit `818da7d55`, receipt `system_v6/receipts/validity_audit_lane_a_geometry_20260612.md`: stale-3 at lines 21, 79, 116, and 127.
- Lane B commit `0abe953e2`, receipt `system_v6/receipts/validity_audit_lane_b_engines_20260612.md`: hash-freshness failure list at line 21.
- Codex plan #2 / stale-list additions as surfaced through `system_v6/receipts/codex_suggestions_unlock_plan_20260612.md` and `system_v6/receipts/standing_queue_20260612.md`.

Lane B hash-freshness failure list, verbatim packet names from line 21:

`basin_criterion_pilot_v0`, `basin_generating_set_sweep_v0`, `basin_information_fusion_v0`, `basin_rc_transition_graph_v0`, `basin_two_engine_joint_v0`, `basin_two_engine_joint_v2`, `basin_two_engine_joint_v3_convention_sweep`, `basin_two_engine_joint_v4_flux`, `carnot_szilard_landauer_ledger_v1`, `mct_dynamic_deformation_v0`, `ring_checkerboard_automaton_v0`, `ring_checkerboard_qca_v1`.

Method:

- Backed up named packet result JSONs under `/tmp/source_lock_refresh_wave_20260612_backups`.
- Ran each packet's current writers/envelope with Makefile interpreter `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`; Julia lanes used `/opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier`.
- Compared regenerated JSONs against committed JSONs after excluding lock/hash/source/provenance/timestamp fields.
- Kept regenerated results only when normalized values were unchanged and validators returned green.
- Restored original committed JSONs immediately for drift or writer failure. Candidate stopped outputs are preserved under `/tmp/source_lock_refresh_wave_20260612_candidates`.

Wizard truth: PARTIAL. Controller loaded v4.2 packet/compact MMM and ran two read-only Codex explorers for independent stale-list archaeology. Full nine-parent council and child topology were not run; no FULL v4.2 claim is made.

## Packet Table

| packet | source list | status | validator / stop reason |
|---|---|---|---|
| `geo_s1_q4_finite_incidence_v0` | Lane A stale-3 | refreshed-identical | Generic validator green: `validate_three_engine_sim_result.py .../geo_s1_q4_finite_incidence_v0_envelope_results.json` returned `ok:true`. |
| `spinor_network_surface_v0` | Lane A stale-3 | refreshed-identical | Packet validator green in `post_audit` phase; generic validator green. |
| `terrain_spinor_flux_nest_n4_v0` | Lane A stale-3 | refreshed-identical | Packet validator green in `post_audit` phase; generic validator green. |
| `basin_criterion_pilot_v0` | Lane B hash-freshness | DIVERGED-stopped | Non-lock result field added at `$.engines.jax.package_observables`; committed JSONs restored. |
| `basin_generating_set_sweep_v0` | Lane B hash-freshness | DIVERGED-stopped | Non-lock `package_observables` fields added in envelope engine rows; committed JSONs restored. |
| `basin_information_fusion_v0` | Lane B hash-freshness | refreshed-identical | Packet validator green; generic validator green. |
| `basin_rc_transition_graph_v0` | Lane B hash-freshness | DIVERGED-stopped | Non-lock `package_observables` fields added in envelope engine rows; committed JSONs restored. |
| `basin_two_engine_joint_v0` | Lane B hash-freshness / plan #2 basin v0 | DIVERGED-stopped | Envelope writer failed: `lanes.julia.package_observables is required for load-bearing packages`; committed JSONs restored. |
| `basin_two_engine_joint_v2` | Lane B hash-freshness / plan #2 basin v2 | refreshed-identical | Packet validator green; generic validator green. |
| `basin_two_engine_joint_v3_convention_sweep` | Lane B hash-freshness / plan #2 basin v3 | refreshed-identical | Packet validator green; generic validator green. |
| `basin_two_engine_joint_v4_flux` | Lane B hash-freshness / plan #2 basin v4 flux | DIVERGED-stopped | JAX writer returned `ok:false`; committed JSONs restored. |
| `carnot_szilard_landauer_ledger_v1` | Lane B hash-freshness / plan #2 Carnot-Szilard ledger | refreshed-identical | Packet validator green; generic validator green. |
| `mct_dynamic_deformation_v0` | Lane B hash-freshness / plan #2 MCT deformation | DIVERGED-stopped | Non-lock runtime field drift at `$.runtime_preflight.load_path`: `@:@stdlib` -> `@:@v#.#:@stdlib`; committed JSONs restored. |
| `ring_checkerboard_qca_v1` | Lane B hash-freshness / plan #2 QCA v1 | DIVERGED-stopped | Envelope writer completed with `all_pass=false` and exit 1; committed JSONs restored. |
| `ring_checkerboard_automaton_v0` | Lane B hash-freshness | skipped-why | `RED_STATE_NOTE_20260612.md` documents the honest red state and says not to green-wash stored values without a fresh rebuild/re-adjudication lane. |

## Refreshed SHA256s

### `geo_s1_q4_finite_incidence_v0`

- `system_v6/sims/geo_s1_q4_finite_incidence_v0/results/geo_s1_q4_finite_incidence_v0_envelope_results.json`: `09546d3ead46c86205505ac28f4ef74dc869e50a890ceaea8926c37b31bbab7c`
- `system_v6/sims/geo_s1_q4_finite_incidence_v0/results/geo_s1_q4_finite_incidence_v0_jax_results.json`: `24087f4a38c33817d0973fd4c7ba6bca7b08a0a3c841ca8471b682cfce68f9fa`
- `system_v6/sims/geo_s1_q4_finite_incidence_v0/results/geo_s1_q4_finite_incidence_v0_julia_results.json`: `b77ba40b0c3c58e8100889df373f7d1a6f8acfcfaf15efca7d3774e9d13b8a52`

### `spinor_network_surface_v0`

- `system_v6/sims/spinor_network_surface_v0/results/spinor_network_surface_v0_envelope_results.json`: `82e8e4bbbccbe6cb5a5cbc876c6e6df4c1a9824af619a4424f100a2723187b7c`
- `system_v6/sims/spinor_network_surface_v0/results/spinor_network_surface_v0_jax_results.json`: `1018055baa90acb15c34358ba796b63f40d7717faba4057aafaaa6d1e346f89a`
- `system_v6/sims/spinor_network_surface_v0/results/spinor_network_surface_v0_julia_results.json`: `50feec962ef5ecf3f9c0c43b15491f2538f3fc74df44dab84ff710d85c1887b7`
- `system_v6/sims/spinor_network_surface_v0/results/spinor_network_surface_v0_pytorch_results.json`: `461ee14604459ebc73aa7115e51f719486f86dcf62867022ab76accc0265ecb3`
- `system_v6/sims/spinor_network_surface_v0/results/spinor_network_surface_v0_validator_results.json`: `9a7e542aacf29cb0b2c25923f1c6b939e3f4cc9bae2ced09f0c5be1c10378bdc`

### `terrain_spinor_flux_nest_n4_v0`

- `system_v6/sims/terrain_spinor_flux_nest_n4_v0/results/terrain_spinor_flux_nest_n4_v0_envelope_results.json`: `0e5ec482f68aaa4d30fd0e0bcfaf2512cb6afb7d5b21054f6b9b3dc40f6ee6a5`
- `system_v6/sims/terrain_spinor_flux_nest_n4_v0/results/terrain_spinor_flux_nest_n4_v0_jax_results.json`: `9e481f013039cb8f08a124e24049dab15779ef14ceca4785433a533f05aec2c4`
- `system_v6/sims/terrain_spinor_flux_nest_n4_v0/results/terrain_spinor_flux_nest_n4_v0_julia_results.json`: `eada8ac9f00e314a0c7b631dd2c29383df88fd70045a1c2ae929ab8534dccd3f`
- `system_v6/sims/terrain_spinor_flux_nest_n4_v0/results/terrain_spinor_flux_nest_n4_v0_pytorch_results.json`: `d6ba493de43dca703bcd236442eeb26a6c38776c5e5a83d9d3f67c0a7e9a879d`
- `system_v6/sims/terrain_spinor_flux_nest_n4_v0/results/terrain_spinor_flux_nest_n4_v0_validator_results.json`: `f8e0190797ff173e8cf35d47f9dae6535e0f27401fe6e787eec85b822f22ab34`

### `basin_information_fusion_v0`

- `system_v6/sims/basin_information_fusion_v0/results/basin_information_fusion_v0_envelope_results.json`: `608fa2dd23715d7d8b519cfdd967f7b1ff1edec804483328e236f99f7ce60752`
- `system_v6/sims/basin_information_fusion_v0/results/basin_information_fusion_v0_jax_results.json`: `011423eb95de723215d232d9c83a89ae0be396e67de14d34a3c799bce3034072`
- `system_v6/sims/basin_information_fusion_v0/results/basin_information_fusion_v0_julia_results.json`: `e919447eb902b2ff187a7863f817c621b41cedacf0ae6785e2f73cfab4ef54f1`
- `system_v6/sims/basin_information_fusion_v0/results/basin_information_fusion_v0_validator_results.json`: `a19593ac704c02ff498cbc9f6726815cc3f5b683426e30a526f08669318f1e75`

### `basin_two_engine_joint_v2`

- `system_v6/sims/basin_two_engine_joint_v2/results/basin_two_engine_joint_v2_envelope_results.json`: `d9d38cac31d302589e3f8c6192a46f1366cba5c937ce708772af077dddd932b7`
- `system_v6/sims/basin_two_engine_joint_v2/results/basin_two_engine_joint_v2_jax_results.json`: `6dafe42f33f1411c4e110c3dc9ca06fc0e5518b1f35fffd33fb6f7e22a9da225`
- `system_v6/sims/basin_two_engine_joint_v2/results/basin_two_engine_joint_v2_julia_results.json`: `87764a7f1e87fd59f226015fef3b04e035aaa184b8a16529e89592fb03d32bb0`
- `system_v6/sims/basin_two_engine_joint_v2/results/basin_two_engine_joint_v2_pytorch_results.json`: `b332e81062aac3d4f2905155d90f54245646cff156cb5d516c4c71a58d743c70`
- `system_v6/sims/basin_two_engine_joint_v2/results/basin_two_engine_joint_v2_validator_results.json`: `b97e5064f0da8c279d762ed2eeb4627a78a152627d9c344a6661aee8fc44a4b9`

### `basin_two_engine_joint_v3_convention_sweep`

- `system_v6/sims/basin_two_engine_joint_v3_convention_sweep/results/basin_two_engine_joint_v3_convention_sweep_envelope_results.json`: `fcbb6c1881ee61811945a605b6a6039acc563c2631935c8fd7840346250cc832`
- `system_v6/sims/basin_two_engine_joint_v3_convention_sweep/results/basin_two_engine_joint_v3_convention_sweep_jax_results.json`: `69700394fc1e3b5fd752f3be5b7b445290694ba96ed474cf8ba9ef1b9bbcd267`
- `system_v6/sims/basin_two_engine_joint_v3_convention_sweep/results/basin_two_engine_joint_v3_convention_sweep_julia_results.json`: `925e314eec3aaeff277d1184dc5d533bf48903ed9a2f00bdb1e246163f008657`
- `system_v6/sims/basin_two_engine_joint_v3_convention_sweep/results/basin_two_engine_joint_v3_convention_sweep_pytorch_results.json`: `d19b91551f4217d4767a94df5bc1ccab8a84cc8b5a2000701ab5ea73a2c7c813`
- `system_v6/sims/basin_two_engine_joint_v3_convention_sweep/results/basin_two_engine_joint_v3_convention_sweep_validator_results.json`: `4f01fe0e562c649b9f58ebfb9591c363c792b490509869caa2fc6cc4aa4dcc54`

### `carnot_szilard_landauer_ledger_v1`

- `system_v6/sims/carnot_szilard_landauer_ledger_v1/results/carnot_szilard_landauer_ledger_v1_envelope_results.json`: `1574192336245463d428baaf2186856559b894c21faa66dc85ca368d59261148`
- `system_v6/sims/carnot_szilard_landauer_ledger_v1/results/carnot_szilard_landauer_ledger_v1_jax_results.json`: `02b2ff8bc32d35d7afe009ab60d0a3b09839cee87800336a433ca0b6adc4d67f`
- `system_v6/sims/carnot_szilard_landauer_ledger_v1/results/carnot_szilard_landauer_ledger_v1_julia_results.json`: `d89992dc754958d27fac9b5356f0864b817c9638a8d5913937172486b89f088c`
- `system_v6/sims/carnot_szilard_landauer_ledger_v1/results/carnot_szilard_landauer_ledger_v1_pytorch_results.json`: `0453f0b10dbaed14d9f2280b8a5a55985cccd84309ccf7d43d4f606de0402c48`

## Stopped Discrepancy Records

### `DR-basin_criterion_pilot_v0-value-drift`

- Status: DIVERGED-stopped; committed JSONs restored.
- Candidate directory: `/tmp/source_lock_refresh_wave_20260612_candidates/basin_criterion_pilot_v0`.
- First non-lock diff: `system_v6/sims/basin_criterion_pilot_v0/results/basin_criterion_pilot_v0_envelope_results.json` added `$.engines.jax.package_observables`.
- Committed SHA256s: envelope `37b613732d6cd12d8ddcff6334170e8b2d9f9caf2abd505cfc8dc6400ee98314`; jax `03893a641b918eefd18f6d3df12e758382035d75c1b4b5140b8a964e0262ef24`; julia `b579446b427389e848822a2e78f0d8573bccbf9f96071dee41ac6baa7bd95773`.
- Candidate SHA256s: envelope `ae8c2134c81afc4d907794cb702f88c38a509943b65cfed574f28790de0ffc38`; jax `c91b28d09b67ae51344aae2c1f5139dfd8a6ca9c8aabd4d2962a19f541a35ca3`; julia `a71a457beeba4c6eaf9c40bb0b9de15b7043c6d0505a24aeddf80628fbae7873`.

### `DR-basin_generating_set_sweep_v0-value-drift`

- Status: DIVERGED-stopped; committed JSONs restored.
- Candidate directory: `/tmp/source_lock_refresh_wave_20260612_candidates/basin_generating_set_sweep_v0`.
- First non-lock diff: envelope added engine `package_observables` for JAX and PyTorch.
- Committed SHA256s: envelope `a833df81f9be68406ecb598a022ba8ba8cb80aa9876f12c5c0617b658b6398c0`; jax `c958e1eabe3f79824da1292df303fe46572a18d386fa3566d4e9b5edc124847b`; julia `aa72290826bd9d3fd0b7a9b7924b0c59d4ac7c9f945642c0e604f0440b0841d6`; pytorch `d2dc1d240b9eee06671360421fef1e22913675b4dc74877bc3541a995dc02d2c`; validator `97246d896fcc244e5dbb1ce4ec4632c5326983f7d2c47cd16a6b72be25e12dd1`.
- Candidate SHA256s: envelope `be4a53aaaad03925aa71ac6c71cb8abf3b33a76869f14249906c82fb55b9af4b`; jax `ed7f9ebbbc293e887ebe18000cfe3f9fbc7184611542a1571a796b9c4396afb5`; julia `5b70ce87be5635b675981fa86245efc10d772e2926fc0b3e022b9ed366a1b387`; pytorch `116e4265501d1f882245674724007bb9131d12b7d2d699d23a7c0a66c5f8e4a4`; validator unchanged `97246d896fcc244e5dbb1ce4ec4632c5326983f7d2c47cd16a6b72be25e12dd1`.

### `DR-basin_rc_transition_graph_v0-value-drift`

- Status: DIVERGED-stopped; committed JSONs restored.
- Candidate directory: `/tmp/source_lock_refresh_wave_20260612_candidates/basin_rc_transition_graph_v0`.
- First non-lock diff: envelope added engine `package_observables` for JAX and PyTorch.
- Committed SHA256s: envelope `58f7cdce5974881bf86f68a9a94a7b967ca8cea6b69ffa3b1e3aea981ae9a0a8`; jax `f7847ed6e9f35577f24d58a2380abb31c7e71fd90646d1081ad60a541fdb24fd`; julia `6658f91cdd6ffaef359866f7e3b0e4c8f4ec2927b4c1a18309bede89b0b21db8`; pytorch `ed4b65df378fbaf9f2433b5f94d0943f901c015e0864fe4357bc0f3b739fa852`; validator `1a6198141771f72230cd4437bb684b76cfbcecb9dadd2109360e4b3657985276`.
- Candidate SHA256s: envelope `b3b35e2e0d547718333b7c0b09dc5eface7cef69947e459d70a15436eceecc8a`; jax `43a72708ba82cf981eb7c65e2e03bd6ba62187d2e3b95345e2afd43aa6cacfcf`; julia `6236554dfea3ab47a04f016a2ff55a2967776bed3132708d24e2d9cef92cc215`; pytorch `8251f72de6c62bd105fc5e609cdc21f525d76053a9f7265ea8a57bd294a9843e`; validator unchanged `1a6198141771f72230cd4437bb684b76cfbcecb9dadd2109360e4b3657985276`.

### `DR-basin_two_engine_joint_v0-writer-failed`

- Status: DIVERGED-stopped; committed JSONs restored.
- Candidate directory: `/tmp/source_lock_refresh_wave_20260612_candidates/basin_two_engine_joint_v0`.
- Failed command: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/basin_two_engine_joint_v0/basin_two_engine_joint_v0_envelope.py`.
- Failure: `ValueError: lanes.julia.package_observables is required for load-bearing packages`.
- Committed SHA256s: envelope `f76e8a5de177df559d6f8be7452583120429f0320290b1ff062be89872c86cc6`; jax `a76aff9bd82b5385a7fd3b2400303fedc4edd50c5773cc579c0b693e2d3d233a`; julia `7c3d267d7dbe8bc79eacb1e4ffe88c71ec5233b05754d497254d3bd072ad754f`; pytorch `6c55aa1ea7b49b4aa4592185e7e9900f75ce5a35966d5b2e518405b9de45431e`; validator `c195717928e1b0b512232d4f098c26b1eed04bb50b12f3c0d7fdb44116a7cea8`.
- Candidate SHA256s: envelope unchanged `f76e8a5de177df559d6f8be7452583120429f0320290b1ff062be89872c86cc6`; jax `0e71e3002b62143c190cb405828db0329837c771e74e320d7f60773dbd7798ce`; julia `74b4a077aa2e75d093e6b9e9044a508c7d22ae4eca88baa2c3ac961c412fbbf9`; pytorch `ec7acfa1a607d6a2b28ee1779252e88d95b313b3b434a6cb00e9c87132780a61`; validator unchanged `c195717928e1b0b512232d4f098c26b1eed04bb50b12f3c0d7fdb44116a7cea8`.

### `DR-basin_two_engine_joint_v4_flux-writer-failed`

- Status: DIVERGED-stopped; committed JSONs restored.
- Candidate directory: `/tmp/source_lock_refresh_wave_20260612_candidates/basin_two_engine_joint_v4_flux`.
- Failed command: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/basin_two_engine_joint_v4_flux/basin_two_engine_joint_v4_flux_jax.py`.
- Failure: writer emitted `{"ok": false, "result_path": "system_v6/sims/basin_two_engine_joint_v4_flux/results/basin_two_engine_joint_v4_flux_jax_results.json"}` and exited 1.
- Committed SHA256s: envelope `e5657a670957ea319882867a39ec75dfb11ca9875597925a3779154e7361ba2c`; jax `f39b5ec7b99d384523f23a758b6429583412c774866244f2adc6fb050d0e7acd`; julia `9294e585d1be237f30dae18ac593319aba5f563621e006f798e9e76a33dfe63b`; pytorch `b7506e23a6c07e2a8e063f09ded88a36c6aa83373612d0eb6f6cac250b2d2775`; validator `25d7fca7a634995c6af4bed37b731ba22f7b656e11003b34010452f211578d81`.
- Candidate SHA256s: envelope unchanged `e5657a670957ea319882867a39ec75dfb11ca9875597925a3779154e7361ba2c`; jax `525005f91ce836e4253ad937625b826540f70bef0ce29da80ae2e2f690402569`; julia unchanged `9294e585d1be237f30dae18ac593319aba5f563621e006f798e9e76a33dfe63b`; pytorch unchanged `b7506e23a6c07e2a8e063f09ded88a36c6aa83373612d0eb6f6cac250b2d2775`; validator unchanged `25d7fca7a634995c6af4bed37b731ba22f7b656e11003b34010452f211578d81`.

### `DR-mct_dynamic_deformation_v0-value-drift`

- Status: DIVERGED-stopped; committed JSONs restored.
- Candidate directory: `/tmp/source_lock_refresh_wave_20260612_candidates/mct_dynamic_deformation_v0`.
- First non-lock diff: `system_v6/sims/mct_dynamic_deformation_v0/results/mct_dynamic_deformation_v0_julia_results.json` changed `$.runtime_preflight.load_path` from `@:@stdlib` to `@:@v#.#:@stdlib`.
- Committed SHA256s: envelope `1cca3d18f7bc5343b2b965e9a71f2406fc2c94b2c684e4d2e4a8263261f48dfa`; jax `7aa6b0eb73fc744350a41b86ccc2d88c9c0a6ce2455495e43b04b3e418b15a47`; julia `670e54795a06a85a7ba29e4f577d4b42337766e5e08e9c89ee41ddc83bcf5250`; validator `49bceedde506319cb39adbb1b03c7b183c89d03ad38f8474ec1cedd27706ef6d`.
- Candidate SHA256s: envelope `0821d3d8e835b3158a1809dfb8ba73e2b53c4265ab69066cfb5780c8579e17f9`; jax `f29e2699cb5b678ad485fc32577241405858fcd5c5475c2a08c48618281ba886`; julia `f58ddb82b0883e55e4398d8caee3a069fbddace8d172a9f3576818e37c179037`; validator unchanged `49bceedde506319cb39adbb1b03c7b183c89d03ad38f8474ec1cedd27706ef6d`.

### `DR-ring_checkerboard_qca_v1-writer-failed`

- Status: DIVERGED-stopped; committed JSONs restored.
- Candidate directory: `/tmp/source_lock_refresh_wave_20260612_candidates/ring_checkerboard_qca_v1`.
- Failed command: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ring_checkerboard_qca_v1/ring_checkerboard_qca_v1_envelope.py`.
- Failure: envelope wrote a candidate but exited 1 with `RING_CHECKERBOARD_QCA_V1_ENVELOPE_DONE all_pass=false L=-1 R=1 local_terminal=1600 global_terminal=160`.
- Committed SHA256s: envelope `64c15f124503593b4e125ad39b1ae991cd64fa7527e0da5804558d099d9b5aa5`; jax `375e3fddeaccda46c0be1fdad3614808707be2c726a6861e6edf6ac2f7c23ad1`; julia `503571b43564d62eaee19a4de63aa52f906a2d119215857812fb11c0987ffab2`; pytorch `b98d11106b6fb05688d253b1173c9febeb79d5bdf6825f8437d338022f11877d`; validator `a69bce4ead985f11041dbdb20b8cfe2e3d7f1d4ce19f2cfcf98ef78a6ba03948`.
- Candidate SHA256s: envelope `a2dbb21555376faca32f1af6142e308c8ca863ad1258510a2b95db2f98a1a784`; jax `5968ef9b8e3cec67406c1b519576314ac2638ed3cf115e0900760aa49d4db044`; julia `6ffb65714b38da3c8121e6b66e425f5300fda393d002524669d6aebc19f1e976`; pytorch `e885f256f86e5617cd2513cccf60232a245b5ef145d23ba19bb30e5a305cac6f`; validator unchanged `a69bce4ead985f11041dbdb20b8cfe2e3d7f1d4ce19f2cfcf98ef78a6ba03948`.

## Skipped Red-State SHA256s

`ring_checkerboard_automaton_v0` was not rerun.

- `system_v6/sims/ring_checkerboard_automaton_v0/results/ring_checkerboard_automaton_v0_envelope_results.json`: `474460b9630731cc7492cd68a68c1c72c4ce4d7953a48368ab28e32bdbea27d4`
- `system_v6/sims/ring_checkerboard_automaton_v0/results/ring_checkerboard_automaton_v0_jax_results.json`: `c2da3449204000ab2475d63e20876329c8244db78b48648a2a1b8f5a3899a6a7`
- `system_v6/sims/ring_checkerboard_automaton_v0/results/ring_checkerboard_automaton_v0_julia_results.json`: `c9d62828f3b51c7b86119de5b3bbeb1dc7fb4e14390c8c90c649284b092a7bdc`
- `system_v6/sims/ring_checkerboard_automaton_v0/results/ring_checkerboard_automaton_v0_pytorch_results.json`: `cf4405f5a0519569f5922925282e2b084a00832de219942f945e997ac371e710`
- `system_v6/sims/ring_checkerboard_automaton_v0/results/ring_checkerboard_automaton_v0_validator_results.json`: `67405a19fb55ed17bfed12b4e06d504dc13226df1d28882ced4e1c6df0b45d02`

## Hygiene / Block K

Gates cited: current user request; `AGENTS.md`; `CODEX.md`; `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`; `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`; `system_v5/docs/LEGO_SIM_CONTRACT.md`; Lane A and Lane B validity audit receipts; packet-local validators; generic `scripts/validate_three_engine_sim_result.py`.

Admission decisions: none. Refreshed packets are only source-lock-refresh current, with their prior packet ceilings unchanged.

Narrative substitutions intercepted: validator green did not override source-lock drift; current-source value drift was recorded as evidence; RED_STATE_NOTE packet was not green-washed.

Worker claims verified: two read-only Codex explorers confirmed the stale lists and command surfaces; controller reran writers and validators locally before accepting refreshes.

Worker claims not verified: no external model claims accepted as evidence without local file/tool checks.

Status label changes to registry: none.

Blocked actions: no git add/commit; no overwrites retained for stopped packets; no RED_STATE_NOTE rewrite.
