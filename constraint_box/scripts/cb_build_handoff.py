#!/usr/bin/env python3
"""cb_build_handoff — assemble THE ENTIRE THING into one package.

Not a summary. Everything from this work: the owner's prompts first and
marked authoritative, then every spec he asked for, every script, every
config, every measurement, with a hash manifest.

Assembled from disk. Nothing typed from memory.
Output: constraint_box/handoff/CB_COMPLETE_<ts>/  + a .zip beside it.
promotion_allowed=false.
"""
from __future__ import annotations
import hashlib, json, shutil, subprocess, sys, time
from pathlib import Path

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
CB = REPO / "constraint_box"
TS = time.strftime("%Y%m%dT%H%M%SZ")
OUT = CB / "handoff" / f"CB_COMPLETE_{TS}"

# ---- what goes where. Owner material FIRST, and marked as winning.
LAYOUT = {
 "00_OWNER": [("docs/OWNER_RULINGS_VERBATIM_20260806.md",
               "THE OWNER'S OWN PROMPTS AND RULINGS. Wins over every other "
               "file in this package, including anything written by a model.")],
 "01_WHAT_CB_IS": [
   ("docs/CB_DEFINITION_OWNER_CANON_20260806.md", "CB's definition, owner canon"),
   ("docs/CB_BIAS_AND_DIVERSITY_MEASURE_20260806.md",
    "operationalist / nominalist / sentimentalist bias, and the deterministic "
    "diversity measure"),
   ("docs/VOICES_AND_MMM_DIVERGENCE_MECHANISM_20260806.md",
    "voices as pre-language, not rules"),
 ],
 "02_WAVES_AND_COUNCILS": [
   ("docs/WIZARD_WAVE_MODEL_OWNER_CANON_20260806.md", "the wave model, owner canon"),
   ("docs/WIZARD_NESTED_COUNCIL_WAVE_MODEL_20260806.md", "nested council topology"),
   ("docs/WIZARD_V4_3_ACTUAL_STRUCTURE_20260806.md", "the 33 agent specs, wired"),
   ("docs/WIZARD_V4_3_READ_FROM_PACKET_20260806.md", "route-truth contract"),
   ("docs/WIZARD_WAVES_COUNCILS_AND_SKILLS_20260806.md", "measured wave shapes"),
   ("docs/NESTED_COUNCILS_FULL_ENUMERATION_20260806.md",
    "every voice, agent, skill, enumerated with paths"),
   ("docs/WAVE_TAXONOMY_ROLES_AND_HARVEST_20260806.md",
    "wave kinds, member x role x wave, the harvest"),
   ("docs/INTEGRATION_WAVE_PROGRAM_20260806.md", "the five-wave integration program"),
   ("docs/CB_EXEMPLAR_PROGRAM_20260806.md",
    "exemplification: a gate that only ever passed is not exemplified"),
   ("docs/CB_SWARM_DRIVER_RECOVERED_DESIGN_20260806.md", "swarm driver, recovered"),
   ("docs/COUNCIL_MEMBER_CATALOG_20260806.md", "five member kinds by determinism class"),
 ],
 "03_TOOLS_AND_LIBRARIES": [
   ("docs/CB_LIGHT_LIBRARY_LIST_20260807.md", "all 44 libraries by tier"),
   ("docs/AUTORESEARCH_AND_NANOCHAT_FEASIBILITY_20260806.md",
    "autoresearch and nanochat, measured feasibility"),
 ],
 "04_REPO_AND_PLAN": [
   ("docs/CR_LEANOUT_INVENTORY_AND_PLAN_20260806.md", "CR lean-out, measured"),
   ("docs/V9_STATE_AND_PLAN_20260806.md", "v9 state"),
   ("docs/SESSION_SAVE_20260807.md", "run ledger and recovered canon"),
   ("PROJECT_STATE.md", "generated state, regenerable, with verified defects"),
 ],
}

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    t0 = time.time()
    # regenerate the state doc FIRST so the package carries current counts
    subprocess.run([str(Path.home()/".local/share/codex-ratchet/envs/main/bin/python3"),
                    str(CB/"scripts"/"cb_project_state.py")],
                   cwd=str(REPO), capture_output=True, text=True)
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": "cb.complete-handoff.v1", "generated": TS,
                "authority": "00_OWNER wins over every other file here",
                "sections": {}, "files": [], "promotion_allowed": False}
    missing = []

    for section, items in LAYOUT.items():
        d = OUT / section; d.mkdir(exist_ok=True)
        entries = []
        for rel, why in items:
            src = CB / rel
            if not src.is_file():
                missing.append(rel); continue
            dst = d / src.name
            shutil.copy2(src, dst)
            e = {"file": f"{section}/{src.name}", "why": why,
                 "sha256": sha(src), "lines": len(src.read_text(errors='ignore').splitlines())}
            entries.append(e); manifest["files"].append(e)
        manifest["sections"][section] = entries

    # code + config + measurements, copied wholesale
    for section, srcdir, pat in (("05_CODE", CB/"scripts", "cb_*.py"),
                                 ("06_CONFIG", CB/"config", "*.json"),
                                 ("07_MEASUREMENTS", CB/"receipts", "**/*.json")):
        d = OUT / section; d.mkdir(exist_ok=True)
        entries = []
        for src in sorted(srcdir.glob(pat)):
            if not src.is_file(): continue
            dst = d / src.name
            try: shutil.copy2(src, dst)
            except Exception: continue
            e = {"file": f"{section}/{src.name}", "sha256": sha(src),
                 "bytes": src.stat().st_size}
            entries.append(e); manifest["files"].append(e)
        manifest["sections"][section] = entries

    # the skills and agents this work depends on, listed not copied
    ext = {"agent_specs": sorted(p.name for p in (REPO/".claude"/"agents").glob("*.md")),
           "mini_mmms": sorted(p.name for p in
              (Path.home()/"wiki/wizard/packet-v4-3-current/mmm/mini/full/voices/md").glob("*.md"))
              if (Path.home()/"wiki/wizard/packet-v4-3-current/mmm/mini/full/voices/md").is_dir() else [],
           "cb_mmm_packs": sorted(p.name for p in (CB/"mmm"/"packs").glob("*.md"))
              if (CB/"mmm"/"packs").is_dir() else [],
           "codex_skills": sorted(p.name for p in (Path.home()/".codex/skills").iterdir()
                                  if p.is_dir())[:60],
           "interpreter": str(Path.home()/".local/share/codex-ratchet/envs/main/bin/python3")}
    (OUT/"08_EXTERNAL_DEPENDENCIES.json").write_text(json.dumps(ext, indent=1))

    readme = [
      "# CB COMPLETE HANDOFF", "",
      f"Generated {TS} from disk by `cb_build_handoff.py`. Nothing typed from memory.", "",
      "## Read in this order", "",
      "1. **00_OWNER/** — the owner's own prompts and rulings, verbatim. "
      "**This section wins over every other file here, including anything a model wrote.**",
      "2. **01_WHAT_CB_IS/** — the definition, the bias, the voice mechanism.",
      "3. **02_WAVES_AND_COUNCILS/** — the nested wave/council model and its enumeration.",
      "4. **03_TOOLS_AND_LIBRARIES/** — the 44-library list and the autoresearch/nanochat feasibility.",
      "5. **04_REPO_AND_PLAN/** — repo lean-out, v9 state, run ledger, and PROJECT_STATE.md.",
      "6. **05_CODE/** — every script, runnable with the interpreter in 08.",
      "7. **06_CONFIG/** — the registries.",
      "8. **07_MEASUREMENTS/** — every receipt produced.",
      "9. **08_EXTERNAL_DEPENDENCIES.json** — agent specs, mini-MMMs, MMM packs, "
      "skills and interpreter this work reaches for but does not contain.", "",
      "## Known defects", "",
      "See `04_REPO_AND_PLAN/PROJECT_STATE.md` — six verified defects, each with "
      "grep-able evidence. In particular: **do not run `cb_loop.py --cycles 20`**, "
      "it bills provider calls and its autoresearch leg has never executed.", "",
      "## Regenerating", "",
      "```bash",
      "PY=~/.local/share/codex-ratchet/envs/main/bin/python3",
      "$PY constraint_box/scripts/cb_project_state.py    # refresh state",
      "$PY constraint_box/scripts/cb_build_handoff.py    # rebuild this package",
      "```", ""]
    if missing:
        readme += ["## Files named in the layout but ABSENT from disk", ""] + \
                  [f"- `{m}`" for m in missing] + [""]
    (OUT/"README.md").write_text("\n".join(readme))
    manifest["missing_from_layout"] = missing
    manifest["file_count"] = len(manifest["files"])
    (OUT/"MANIFEST.json").write_text(json.dumps(manifest, indent=1, sort_keys=True))

    zip_path = shutil.make_archive(str(OUT), "zip", root_dir=str(OUT.parent),
                                   base_dir=OUT.name)
    print(f"HANDOFF PACKAGE  {OUT.relative_to(REPO)}")
    for s, e in manifest["sections"].items():
        print(f"   {s:<26}{len(e):>4} files")
    print(f"   08_EXTERNAL_DEPENDENCIES.json  {len(ext['agent_specs'])} agent specs, "
          f"{len(ext['mini_mmms'])} mini-MMMs, {len(ext['cb_mmm_packs'])} MMM packs, "
          f"{len(ext['codex_skills'])} codex skills")
    print(f"   TOTAL {manifest['file_count']} files")
    if missing: print(f"   MISSING from layout: {missing}")
    print(f"   zip: {Path(zip_path).relative_to(REPO)} "
          f"({Path(zip_path).stat().st_size//1024} KB)")
    print(f"   {time.time()-t0:.1f}s")

if __name__ == "__main__":
    main()
