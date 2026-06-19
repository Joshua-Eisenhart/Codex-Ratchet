# PREFLIGHT: compression_flow_radiated_record_v0

Read-only preflight for reused MCT carrier assets.

## Summary

1. Committed carrier validates with `--require-pytorch`: PASS
2. Carrier lineage constants reachable and importable 384-row probe tables present: PASS
3. Julia environment imports required packages: PASS
4. Python environment imports required packages and reports versions: PASS
5. No pre-existing `system_v6/sims/compression_flow_radiated_record_v0` content: PASS

## Check 1: committed carrier validation

PASS

Command:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json --require-pytorch
```

Output:

```text
{
  "ok": true,
  "result_json": "system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json"
}
```

## Check 2: carrier lineage constants and 384-row probe tables

PASS

Command:

```bash
rg -n "pin_block_sha256|chart|probe_row_table|384" system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl system_v6/sims/mct_dynamic_admissibility_packet_v0/results/*.json
```

Relevant output excerpt:

```text
system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:37:const PIN_BLOCK_CANONICAL = "{\"axis0_boundary_policy\":\"b0=0 at eta=pi/4 boundary shell\",\"axis0_status\":\"readout_only_no_closure\",\"bin_edges\":{\"density\":[-1.000001,-0.5,0.0,0.5,1.000001],\"order_gap\":[0.0,1e-09,0.001,0.01,1000000000.0],\"phase_bins\":8},\"choice_points\":{\"constraint_form\":\"state_predicate main + probe_row_predicate transported view\",\"fixed_root_C\":\"fixed root C with explicit C_t view\",\"folding\":\"equivalence-respecting default; aggregation branch ledgered only\",\"pass_condition\":\"owner_pending\",\"relation_updates\":\"finite delta (E union Delta+) minus Delta-\",\"representation_mode\":\"carrier_retained main + quotient_materialized side branch\",\"self_loop_policy_default\":\"owner_pending\"},\"grid\":{\"chi_j\":\"2*pi*j/8 for j=0..7\",\"eta_k\":[\"pi/8\",\"pi/4\",\"3*pi/8\"],\"phi_i\":\"2*pi*i/8 for i=0..7\",\"sheets\":[\"L\",\"R\"],\"support_size\":384},\"lr_sheet_realization\":{\"source_quote\":\"H_L=+H_0, H_R=-H_0\",\"status\":\"PINNED-CHOICE\",\"summary\":\"spinor chart stays source-identical; sheet enters through Weyl Hamiltonian sign and computed chirality probe\"},\"probe_families\":[\"P_density\",\"P_shell\",\"P_loop\",\"P_order\",\"P_phase\",\"P_chirality\"],\"ring_checkerboard_note\":\"eta-shell rings x (phi,chi) checkerboard; mapping question stays OPEN\",\"spinor_chart\":\"psi_s(phi_i,chi_j;eta_k)=(exp(i(phi_i+chi_j))*cos(eta_k), exp(i(phi_i-chi_j))*sin(eta_k))\"}"
system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:38:const PIN_BLOCK_SHA256 = bytes2hex(sha256(collect(codeunits(PIN_BLOCK_CANONICAL))))
system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:39:const PIN_BLOCK_EXTENSIONS_CANONICAL = "\"chart_agreement_receipt\":\"pinned_chart_agrees_with_formal_geometry_78_88_no_divergence\",\"computed_sheet_probe\":{\"name\":\"P_weyl_gap\",\"source\":\"order_gap_noncommuting_matched_LR_difference\",\"quotient_key\":\"q_without_phase_computed_sheet\"},\"pin_extended_from\":{\"sha256\":\"$(PIN_BLOCK_SHA256)\",\"lineage_note\":\"additive instrumentation plus derived defaults only; previous PIN retained as pin_block_sha256\"},\"probe_family_metadata\":{\"P_chirality\":\"label_transcription\",\"P_weyl_gap\":\"computed_dynamic_sheet_sensitive\"},\"variant_ledger_key\":\"variant_ledger\""
system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:255:        "probe_row_table" => probe_rows,
system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:572:        "support_counts_agree" => length(rows) == 384,
system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:731:        "G3" => Dict("full_probe_row_table_emitted" => length(rows) == 384, "probe_families_computed" => PIN_SPEC["probe_families"], "probe_family_metadata" => Dict("P_chirality" => "label_transcription", "P_weyl_gap" => "computed_dynamic_sheet_sensitive"), "sheet_sensitive_probe_receipt" => sheet_sensitive_probe_receipt(rows, q_computed_sheet)),
system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:767:        "pin_block_sha256" => PIN_BLOCK_SHA256,
system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:778:        "probe_row_table" => rows,
system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_jax_results.json:27128:  "probe_row_table": [
system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_pytorch_results.json:27130:  "probe_row_table": [
system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_julia_results.json:44512:  "probe_row_table": [
```

Structured JSON count check:

Command:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
import json
from pathlib import Path
paths = sorted(Path('system_v6/sims/mct_dynamic_admissibility_packet_v0/results').glob('*.json'))
for p in paths:
    data = json.loads(p.read_text())
    table = data.get('probe_row_table')
    print(f'{p}: top_level_probe_row_table_len={len(table) if isinstance(table, list) else "MISSING"}')
    for key in ('pin_block_sha256', 'pin_block_canonical_json', 'pin_block_extended_canonical_json'):
        print(f'  {key}={"present" if key in data else "missing"}')
PY
```

Output:

```text
system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json: top_level_probe_row_table_len=MISSING
  pin_block_sha256=missing
  pin_block_canonical_json=present
  pin_block_extended_canonical_json=present
system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_jax_results.json: top_level_probe_row_table_len=384
  pin_block_sha256=present
  pin_block_canonical_json=present
  pin_block_extended_canonical_json=present
system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_julia_results.json: top_level_probe_row_table_len=384
  pin_block_sha256=present
  pin_block_canonical_json=present
  pin_block_extended_canonical_json=present
system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_pytorch_results.json: top_level_probe_row_table_len=384
  pin_block_sha256=present
  pin_block_canonical_json=present
  pin_block_extended_canonical_json=present
```

Conclusion: the Julia, JAX, and PyTorch per-engine result JSONs contain top-level 384-row `probe_row_table` arrays. The envelope result validates and contains the pin canonical JSON fields, but does not expose a top-level `probe_row_table`.

## Check 3: Julia environment

PASS

Command:

```bash
julia -e 'using QuantumOptics, Z3, Graphs, JSON, SHA; println("ok")'
```

Output:

```text
ok
```

## Check 4: Python environment

PASS

Command:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
mods = ['jax', 'z3', 'cvc5', 'sympy', 'torch', 'torch_geometric']
for name in mods:
    try:
        m = __import__(name)
        version = getattr(m, '__version__', None)
        if version is None and name == 'z3':
            version = m.get_version_string()
        if version is None and name == 'cvc5':
            version = getattr(m, '__version__', 'unknown')
        print(f'{name} {version}')
    except Exception as e:
        print(f'{name} IMPORT_FAILED {type(e).__name__}: {e}')
        raise
PY
```

Output:

```text
jax 0.10.1
z3 4.16.0
cvc5 1.3.3
sympy 1.14.0
torch 2.11.0
torch_geometric 2.7.0
```

## Check 5: no pre-existing target content

PASS

Command:

```bash
if [ -e system_v6/sims/compression_flow_radiated_record_v0 ]; then find system_v6/sims/compression_flow_radiated_record_v0 -maxdepth 3 -print | sort; else echo 'ABSENT'; fi
```

Output:

```text
ABSENT
```
