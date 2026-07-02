"""Mirror the canonical engine_v6 L0 purification-bridge witness results into a
browser payload for the v6 visualizer. Values are copied verbatim; nothing is
recomputed or invented.

Canonical source:
system_v5/ops/formal_scouts/results/engine_v6_l0_purification_bridge_witness_probe_results.json
Output: visualizer/engine-v6-witness-data.js (window.ENGINE_V6_WITNESS)
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE.parent / "system_v5" / "ops" / "formal_scouts" / "results"
       / "engine_v6_l0_purification_bridge_witness_probe_results.json")

d = json.loads(SRC.read_text())
pm = d["positive"]["per_method_full_data"]

def slim(run):
    return {k: run[k] for k in (
        "n_qubits", "engine_type", "seed", "purify_method", "n_substages",
        "l0_metrics", "autograd_clean", "l0_metric_mean", "l0_metric_std",
        "l0_metric_range") if k in run}

payload = {
    "meta": {
        "probe": d.get("probe"),
        "timestamp_utc": d.get("timestamp_utc"),
        "classification": d.get("classification"),
        "canonical_path": "system_v5/ops/formal_scouts/results/engine_v6_l0_purification_bridge_witness_probe_results.json",
        "claim_ceiling": d.get("claim_ceiling"),
        "promotion_allowed": d.get("promotion_allowed"),
    },
    "methods": {
        m: {
            "type1_runs": [slim(r) for r in pm[m].get("type1_runs", [])],
            "type2_runs": [slim(r) for r in pm[m].get("type2_runs", [])],
        } for m in pm
    },
    "controls": [slim(r) for r in d["negative"].get("random_purified_controls", [])],
    "random_metric_mean_band": d["negative"].get("random_metric_mean_band"),
    "checks": {
        section: {
            name: {k: v for k, v in check.items() if not isinstance(v, (dict, list))}
            for name, check in d.get(section, {}).items() if isinstance(check, dict)
        } for section in ("positive", "boundary", "graveyard_companions")
    },
}
# drop the huge per_method blob duplicated inside checks.positive if present
payload["checks"]["positive"].pop("per_method_full_data", None)

out = HERE / "engine-v6-witness-data.js"
out.write_text("// mirrored verbatim from canonical results JSON — do not hand-edit\n"
               "window.ENGINE_V6_WITNESS = " + json.dumps(payload) + ";\n")
print(f"wrote {out} ({out.stat().st_size} bytes)")
