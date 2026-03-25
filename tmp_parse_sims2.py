import os
import glob
import ast
import json

import sys
sys.path.insert(0, '/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes')
from run_all_sims import TIERED_SIMS

# Extract mapping from file to tier
file_to_tier = {}
for tier, files in TIERED_SIMS.items():
    for f in files:
        file_to_tier[f] = tier

# We can also get output artifact from run_all_sims result_files inside run_sim map
# Since we can't easily import locals, let's just parse it out of the file
import re
with open('/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/run_all_sims.py', 'r') as f:
    run_all_content = f.read()

result_map = {}
match = re.search(r'result_files\s*=\s*({[^}]+})', run_all_content)
if match:
    # safe eval
    try:
        result_map = ast.literal_eval(match.group(1))
    except:
        pass

all_py_files = set(glob.glob('/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/*.py'))

# only catalog files that have 'sim' in the name or are in TIERED_SIMS
target_files = set()
for f in all_py_files:
    basename = os.path.basename(f)
    if 'sim' in basename.lower() or basename in file_to_tier:
        target_files.add(f)

data = []
for f in target_files:
    basename = os.path.basename(f)
    tier = file_to_tier.get(basename, 'N/A')
    artifact = result_map.get(basename, 'N/A')
    
    with open(f, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()
        
    # extract docstring thesis
    thesis = "N/A"
    doc_match = re.search(r'\"\"\"(.*?)\"\"\"', content, re.DOTALL)
    if not doc_match:
        doc_match = re.search(r"\'\'\'(.*?)\'\'\'", content, re.DOTALL)
        
    if doc_match:
        lines = [l.strip() for l in doc_match.group(1).split('\\n') if l.strip()]
        if lines:
            # take first 2-3 lines of docstring
            thesis = " ".join(lines[:3]).replace('|', '').replace('\\n', ' ')
            if len(thesis) > 100:
                thesis = thesis[:97] + "..."
    
    # extract PASS/KILL
    threshold = "N/A"
    if 'EvidenceToken' in content:
        if 'KILL' in content and 'PASS' in content:
            threshold = "Emits PASS or KILL"
        elif 'PASS' in content:
            threshold = "Emits PASS on config"
        else:
            threshold = "Emits Evidence"
            
    # extract runtime class
    runtime_class = "N/A"
    if 'apply_unitary_channel' in content or 'apply_lindbladian_step' in content:
        runtime_class = "Quantum CPTP"
    elif 'run_sim' in content:
        runtime_class = "Runner"
    elif 'class ' in content:
        runtime_class = "OOP"
    elif 'def ' in content:
        runtime_class = "Procedural"

    data.append({
        'filename': basename,
        'tier': tier,
        'thesis': thesis,
        'pass_kill': threshold,
        'artifact': artifact,
        'runtime': runtime_class
    })

data.sort(key=lambda x: (x['tier'], x['filename']))

out_path = '/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/SIM_CATALOG_AXIS_DISCOVERY.md'
os.makedirs(os.path.dirname(out_path), exist_ok=True)

with open(out_path, 'w', encoding='utf-8') as f:
    f.write('# SIM CATALOG AXIS DISCOVERY\n\n')
    f.write('| filename | tier | thesis | PASS/KILL threshold | output artifact | runtime class |\n')
    f.write('|---|---|---|---|---|---|\n')
    for d in data:
        # cleanup newlines
        thesis_clean = d['thesis'].replace('\n', ' ')
        f.write(f"| {d['filename']} | {d['tier']} | {thesis_clean} | {d['pass_kill']} | {d['artifact']} | {d['runtime']} |\n")

print(f"Wrote to {out_path} with {len(data)} SIMs")
