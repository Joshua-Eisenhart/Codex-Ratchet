import os
import glob
import re

def parse_sims():
    files = glob.glob('/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/*.py')
    
    data = []
    
    for f in files:
        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read(2000) # Read the first 2000 chars for header
            
            # Use regex to extract fields
            tier_match = re.search(r'(?i)(?:tier|tier level):\s*(.*)', content)
            thesis_match = re.search(r'(?i)(?:thesis|goal|purpose):\s*(.*)', content)
            pass_kill_match = re.search(r'(?i)(?:pass/kill|pass/fail|threshold|success condition):\s*(.*)', content)
            artifact_match = re.search(r'(?i)(?:output artifact|artifact|output):\s*(.*)', content)
            runtime_class_match = re.search(r'(?i)(?:runtime class|class|category):\s*(.*)', content)
            
            if tier_match or thesis_match or pass_kill_match or artifact_match or runtime_class_match:
                tier = tier_match.group(1).strip() if tier_match else 'N/A'
                thesis = thesis_match.group(1).strip() if thesis_match else 'N/A'
                pass_kill = pass_kill_match.group(1).strip() if pass_kill_match else 'N/A'
                artifact = artifact_match.group(1).strip() if artifact_match else 'N/A'
                runtime_class = runtime_class_match.group(1).strip() if runtime_class_match else 'N/A'
                
                # Clean up newlines in matched groups if any, although group(1) normally stops at newline
                data.append({
                    'filename': os.path.basename(f),
                    'tier': tier,
                    'thesis': thesis,
                    'pass_kill': pass_kill,
                    'artifact': artifact,
                    'runtime': runtime_class
                })
                
    # Sort data by filename
    data.sort(key=lambda x: x['filename'])
    
    # Write to Markdown
    out_path = '/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/SIM_CATALOG_AXIS_DISCOVERY.md'
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('# SIM CATALOG AXIS DISCOVERY\n\n')
        f.write('This document catalogs the configuration, tiering, and execution thresholds of all Simulation Probes in the system.\n\n')
        f.write('| Filename | Tier | Thesis | PASS/KILL Threshold | Output Artifact | Runtime Class |\n')
        f.write('|---|---|---|---|---|---|\n')
        for d in data:
            f.write(f"| {d['filename']} | {d['tier']} | {d['thesis']} | {d['pass_kill']} | {d['artifact']} | {d['runtime']} |\n")

if __name__ == '__main__':
    parse_sims()
