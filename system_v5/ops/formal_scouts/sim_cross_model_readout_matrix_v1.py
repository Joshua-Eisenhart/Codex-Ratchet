import json
import glob
from pathlib import Path
import datetime
import re

def find_first_non_null(obj, key):
    if isinstance(obj, dict):
        if key in obj and obj[key] is not None:
            return obj[key]
        for value in obj.values():
            result = find_first_non_null(value, key)
            if result is not None:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = find_first_non_null(item, key)
            if result is not None:
                return result
    return None

def extract_concept(filename):
    fname = Path(filename).name
    match = re.search(r'(r3_associator|g2)', fname, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    match = re.search(r'foundation_r3_([a-zA-Z0-9_]+?)(?:_envelope|_results|\.json)', fname, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    cleaned = fname.lower()
    cleaned = cleaned.replace('foundation_r3_', '').replace('foundation_foundation_r3_', '')
    cleaned = cleaned.replace('_envelope', '').replace('_results', '').replace('.json', '')
    cleaned = re.sub(r'[^a-z0-9_]', '', cleaned)
    return cleaned if cleaned else fname.lower()

def get_preference(filename):
    fname = Path(filename).name.lower()
    if 'xhigh' in fname:
        return 4
    if 'high' in fname:
        return 3
    if 'medium' in fname:
        return 2
    if 'low' in fname:
        return 1
    return 0

base_dir = "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/"
patterns = [
    base_dir + "foundation_r3_*envelope*results.json",
    base_dir + "foundation_foundation_r3_*envelope*results.json"
]

files = []
for pattern in patterns:
    files.extend(glob.glob(pattern))

concept_to_files = {}
for f in files:
    concept = extract_concept(f)
    if concept not in concept_to_files:
        concept_to_files[concept] = []
    concept_to_files[concept].append(f)

invariant_keys = [
    "O_associator_norm",
    "O_derivation_dimension",
    "S_witness_product_normsq",
    "jordan_identity_residual_norm",
    "O_alternative",
    "max_divergence"
]

canonical_to_invariants = {}
for concept, flist in concept_to_files.items():
    if not flist:
        continue
    best_file = max(flist, key=get_preference)
    try:
        with open(best_file, 'r') as fh:
            data = json.load(fh)
    except Exception:
        continue
    invariants = {}
    for key in invariant_keys:
        invariants[key] = find_first_non_null(data, key)
    canonical_to_invariants[concept] = invariants

rungs = []
for name in sorted(canonical_to_invariants.keys()):
    rungs.append({
        "name": name,
        "invariants": canonical_to_invariants[name]
    })

readout_languages = ["physics", "IGT", "QIT_engine", "holodeck"]
matrix = {}
for rung in rungs:
    name = rung["name"]
    matrix[name] = {}
    for lang in readout_languages:
        matrix[name][lang] = {
            "candidate": f"{name} readout",
            "role": "unmapped",
            "earned": False,
            "needs": ["own finite support object", "probe family", "readout map", "failing control"]
        }

result = {
    "rungs": rungs,
    "matrix": matrix,
    "classification": "scratch_diagnostic",
    "promotion_allowed": False,
    "formal_admission_allowed": False,
    "correspondences_unearned_until_support_probe_readout_failing_control": True,
    "anti_collapse_note": "These are different readout languages over the SAME finite pattern, NOT the same thing by slogan; none is earned until it has its own support/probe/readout/failing-control.",
    "timestamp": datetime.datetime.now().isoformat()
}

output_path = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/cross_model_readout_matrix_v1_results.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w") as f:
    json.dump(result, f, indent=2)

non_null_count = 0
for rung in rungs:
    for val in rung["invariants"].values():
        if val is not None:
            non_null_count += 1
rung_count = len(rungs)
print(f"{rung_count} rungs, {non_null_count} invariants non-null")
