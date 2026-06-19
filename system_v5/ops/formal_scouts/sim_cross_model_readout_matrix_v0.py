import json
import glob
from pathlib import Path
import datetime

base = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/")
patterns = [
    "foundation_r3_*envelope*results.json",
    "foundation_foundation_r3_*envelope*results.json"
]

json_files = set()
for p in patterns:
    for match in glob.glob(str(base / p)):
        json_files.add(match)
json_files = sorted(json_files)

rungs_list = []
for fpath_str in json_files:
    fpath = Path(fpath_str)
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        continue
    stem = fpath.stem
    rung_name = stem.replace('_envelope_results', '').replace('_results', '')
    rung_name = rung_name.replace('foundation_foundation_r3_', 'r3_').replace('foundation_r3_', 'r3_')
    if rung_name.startswith('foundation_'):
        rung_name = rung_name[len('foundation_'):]
    invariants = {}
    for key in ['O_associator_norm', 'O_derivation_dimension', 'S_witness_product_normsq', 'jordan_identity_residual_norm', 'O_alternative']:
        invariants[key] = data.get(key, None)
    rungs_list.append({
        "rung": rung_name,
        "invariants": invariants
    })

rungs_list.sort(key=lambda x: x["rung"])

readout_languages = ["physics", "IGT", "QIT_engine", "holodeck"]
matrix = {}
for entry in rungs_list:
    rung = entry["rung"]
    matrix[rung] = {}
    for lang in readout_languages:
        short_phrase = f"non-associativity R3 as {lang} readout"
        matrix[rung][lang] = {
            "candidate": short_phrase,
            "earned": False,
            "needs": ["own finite support object", "probe family", "readout map", "failing control"]
        }

output_path = base / "cross_model_readout_matrix_v0_results.json"
output_path.parent.mkdir(parents=True, exist_ok=True)

generated_note = f"Generated {datetime.datetime.now().isoformat()} - stdlib only. Correspondences are unearned candidates requiring explicit finite support, probe family, readout map, and failing control."

result = {
    "rungs_found": rungs_list,
    "matrix": matrix,
    "classification": "scratch_diagnostic",
    "promotion_allowed": False,
    "formal_admission_allowed": False,
    "correspondences_unearned_until_support_probe_readout_failing_control": True,
    "generated_note": generated_note
}

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2)

print(f"Cross-model readout matrix v0: {len(rungs_list)} rungs.")
