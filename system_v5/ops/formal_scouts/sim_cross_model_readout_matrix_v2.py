import json
from pathlib import Path
import datetime

registry_path = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/audit_receipts/LAYER_REGISTRY.json")
output_dir = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results")
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / "cross_model_readout_matrix_v2_results.json"

registry_data = {}
if registry_path.exists():
    try:
        with registry_path.open('r', encoding='utf-8') as f:
            registry_data = json.load(f)
    except Exception:
        registry_data = {}

cleared_rungs = []
if isinstance(registry_data, dict):
    if "cleared_rungs" in registry_data:
        cleared_rungs = registry_data["cleared_rungs"]
    elif "rungs" in registry_data:
        rungs = registry_data["rungs"]
        if isinstance(rungs, list):
            for item in rungs:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("rung_name") or str(item)
                    cleared_rungs.append(name)
                else:
                    cleared_rungs.append(str(item))
        elif isinstance(rungs, dict):
            cleared_rungs = list(rungs.keys())
    else:
        cleared_rungs = [k for k in registry_data.keys() if isinstance(k, str)]
elif isinstance(registry_data, list):
    for item in registry_data:
        if isinstance(item, dict):
            name = item.get("name") or str(item)
            cleared_rungs.append(name)
        else:
            cleared_rungs.append(str(item))

cleared_rungs = [str(r) for r in cleared_rungs if r]

readout_languages = ["physics", "IGT", "QIT_engine", "holodeck"]

matrix = {}
for lang in readout_languages:
    matrix[lang] = {}
    for rung in cleared_rungs:
        matrix[lang][rung] = {
            "candidate": f"{lang} mapping to {rung}",
            "role": "unmapped",
            "earned": False,
            "needs": ["own finite support object", "probe family", "readout map", "failing control"]
        }

horizon_frame = {
    "name": "Observer Patch Holography (OPH)",
    "thesis": "each observer gets a local patch; physics = the public fixed point that survives agreement across overlaps. Map it: local patch=probe family M; agreement-across-overlaps = a=a iff a~b; surviving fixed point = admissibility quotient S/~_M; emergent spacetime = entropic monism; S^2 screens + icosahedral A5 = finite-geometry/spinor layer; recovers SU(3)xSU(2)xU(1)/Z6 = the FENCED octonion->SM horizon.",
    "earned": False
}

lovheim_cube_row = {
    "name": "LOVHEIM CUBE OF EMOTION",
    "description": "8 emotions on a cube = 2^3, three binary axes = serotonin/dopamine/noradrenaline (HIGH/LOW). Map it to the 3-bit cube = the 8-strategy IGT engine = the 3-qubit / Cl(6) floor. The 3 monoamine axes = the 3 binary coordinates; the 8 emotion-vertices = the 8 IGT strategies / 8 computational-basis states.",
    "role": "donor",
    "earned": False,
    "needs": ["own finite support object", "probe family", "readout map", "failing control"],
    "anti_collapse_note": "a different readout language over the same 3-bit/8-vertex cube, not the same thing by slogan"
}

results = {
    "cleared_rungs": cleared_rungs,
    "horizon_frame": horizon_frame,
    "lovheim_cube_row": lovheim_cube_row,
    "matrix": matrix,
    "classification": "scratch_diagnostic",
    "promotion_allowed": False,
    "formal_admission_allowed": False,
    "correspondences_unearned_until_support_probe_readout_failing_control": True,
    "generated_at": datetime.datetime.now().isoformat()
}

with output_path.open('w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

print(f"Codex-Ratchet cross_model_readout_matrix_v2: {len(cleared_rungs)} rungs, {len(readout_languages)} languages written.")
