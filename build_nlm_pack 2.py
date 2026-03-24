#!/usr/bin/env python3
import os
import zipfile
import shutil
from pathlib import Path

def main():
    repo_root = Path(__file__).resolve().parent
    artifacts_dir = Path("/Users/joshuaeisenhart/.gemini/antigravity/brain/351be0f2-e55d-441a-86ad-3b8bfa0629e3")
    desktop_dir = Path("/Users/joshuaeisenhart/Desktop")
    
    staging_dir = repo_root / "nlm_pack_staging"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True)
    
    # 1. Collect all recent artifact MD files
    print("Collecting System Audit & Task artifacts...")
    for f in artifacts_dir.glob("*.md"):
        shutil.copy(f, staging_dir / f.name)
        
    # 2. Collect user's recent spec files
    core_docs = repo_root / "core_docs" / "a1_refined_Ratchet Fuel"
    print("Collecting Axis spec documents...")
    for f in core_docs.glob("*.md"):
        shutil.copy(f, staging_dir / f.name)

    # 3. We rebuilt the core physics in Python (V2 SIMs). NLM needs this math!
    # Convert the Python logic into `.txt` logs.
    print("Extracting Python QIT Math into Text digests...")
    probes_dir = repo_root / "system_v4" / "probes"
    all_sims = list(probes_dir.glob("*.py"))
    
    for sim_path in all_sims:
        if sim_path.is_file():
            with open(sim_path, "r") as src:
                content = src.read()
            # Save as txt
            out_name = sim_path.name.replace(".py", "_CODE_DIGEST.txt")
            with open(staging_dir / out_name, "w") as dst:
                dst.write(f"--- SOURCE CODE FOR {sim_path.name} ---\n\n")
                dst.write(content)

    # 4. Grab unified evidence JSONs as txt
    state_dir = probes_dir / "a2_state" / "sim_results"
    ev_pack = state_dir / "SIM_EVIDENCE_PACK.txt"
    if ev_pack.exists():
        shutil.copy(ev_pack, staging_dir / "SIM_EVIDENCE_PACK.txt")

    # 5. Zip it all up
    zip_path = desktop_dir / "Codex_Ratchet_NLM_Batch3_Update.zip"
    print(f"Zipping to {zip_path}...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(staging_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, file)
                
    shutil.rmtree(staging_dir)
    print("Done! NLM Zip pack generated on Desktop.")

if __name__ == "__main__":
    main()
