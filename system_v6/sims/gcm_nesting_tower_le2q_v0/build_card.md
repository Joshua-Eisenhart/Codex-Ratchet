# gcm_nesting_tower_le2q_v0 Build Card

Task: build the first computed <=2Q inverse-limit tower object for THE NESTING LAW.

Authority:

- Spec: `system_v6/receipts/nesting_law_final_object_spec_20260612.md`
- Formula: `X_{<=2}^max = { (rho_1, rho_2, rho_12) : each in its survivor set, Tr_2(rho_12) ~ rho_1, Tr_1(rho_12) ~ rho_2 }`
- Axis declaration: nesting/tower axis, inverse-limit object, <=2Q rung.

Inputs:

- 1Q registry object: `gcmobj_a40e54e13cec01466c9d675028b3574b`
- 2Q registry object: `gcm2qobj_715e9424ea66468243108751fb59395f`
- Expected survivor counts: 16 1Q survivors and 544 2Q survivors.
- Expected 2Q lineage location: `gcm_lineage.gcm_2q_object_id`.

Contract:

- G.2a from birth.
- Classification: `scratch_diagnostic`.
- Ceiling: carrier-and-pins-relative first tower computation.
- No audit verdict is produced by the builder.
- NO git add/commit.

Packet outputs:

- Compatible families for exact equality and probe equivalence.
- exact-vs-probe equivalence adjudication, including rows where probe rescues exact tower-orphans.
- extension fibers `F_2(s)` for all 16 1Q survivors.
- tower-orphans for exact and probe relations.
- product-only sub-tower control.
- scrambled-pairing tower control.
- lineage-free negative controls.
- three-engine envelope over Julia, JAX, and PyTorch lanes.

Expected computed facts:

- Exact compatible 2Q rows: 256.
- Exact family triples: 256.
- Probe-compatible 2Q rows: 464.
- Probe family triples: 1856.
- Exact tower-orphans: 288.
- Probe tower-orphans: 80.
- Probe-rescued exact orphans: 208.
- Entangled 16: exact-B orphans and probe-compatible fiber members.

Run order:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_nesting_tower_le2q_v0/gcm_nesting_tower_le2q_v0_common.py
```

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/gcm_nesting_tower_le2q_v0/gcm_nesting_tower_le2q_v0_julia.jl
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_nesting_tower_le2q_v0/gcm_nesting_tower_le2q_v0_jax.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_nesting_tower_le2q_v0/gcm_nesting_tower_le2q_v0_pytorch.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_nesting_tower_le2q_v0/write_envelope_spec.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_nesting_tower_le2q_v0/validate_gcm_nesting_tower_le2q_v0.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/gcm_nesting_tower_le2q_v0/tests
```
