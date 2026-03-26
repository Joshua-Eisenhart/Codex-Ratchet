import json, os

with open('/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/exploratory_process_cycle_stage_matrix_results.json') as f:
    data = json.load(f)

out_lines = [
    "# Macro-Stage Process Cycle Matrix Analysis",
    "",
    "The 16 macro-stages (8 terrains x 2 engine types) each execute the strictly ordered `Ti -> Fe -> Te -> Fi` subcycle. Below is the dominance matrix mapping the 'Native' operator claim against actual measurements of $|\\Delta\\Phi|$ (negentropy change) and $\\delta\\rho$ (trace distance).",
    ""
]

rows_by_type = {1: [], 2: []}
for row in data.get("matrix_rows", []):
    etype = row.get("engine_type", 1)
    rows_by_type[etype].append(row)

for etype, rows in rows_by_type.items():
    out_lines.append(f"## Engine Type {etype}")
    out_lines.append("")
    out_lines.append("| Terrain | Native | $|\\Delta\\Phi|$ Dom | Trace Dom | Mixed Dom | $Ti/Fe/Te/Fi$ $\\Delta\\Phi$ | $Ti/Fe/Te/Fi$ Trace |")
    out_lines.append("|---|---|---|---|---|---|---|")
    
    for row in rows:
        name = row["terrain"]
        native = row["native_operator_doc"]
        rep = row["representative"]
        dphi_dom = rep["observed_native_by_abs_dphi"]
        trace_dom = rep["observed_native_by_trace"]
        
        # calculate mixed dominance
        sub_dphi = []
        sub_trace = []
        max_mixed = -1
        mixed_dom = None
        for micro in rep["subcycles"]:
            op = micro["operator"]
            d = round(abs(micro["dphi_L"]), 4) # simplified using just left or avg
            t = round(micro["trace_L"], 4)
            sub_dphi.append(str(d))
            sub_trace.append(str(t))
            # Arbitrary score: sum of normalized values or just raw sum 
            # (dphi is usually larger scale than trace distance, let's just 2x dphi + trace)
            score = d * 2.0 + t
            if score > max_mixed:
                max_mixed = score
                mixed_dom = op
                
        dphi_str = "/".join(sub_dphi)
        trace_str = "/".join(sub_trace)
        
        out_lines.append(f"| {name} | **{native}** | {dphi_dom} | {trace_dom} | {mixed_dom} | `{dphi_str}` | `{trace_str}` |")
        
    out_lines.append("")

out_path = '/Users/joshuaeisenhart/.gemini/antigravity/brain/351be0f2-e55d-441a-86ad-3b8bfa0629e3/STAGE_MATRIX_ANALYSIS.md'
with open(out_path, 'w') as f:
    f.write("\n".join(out_lines))
print(f"Wrote to {out_path}")
