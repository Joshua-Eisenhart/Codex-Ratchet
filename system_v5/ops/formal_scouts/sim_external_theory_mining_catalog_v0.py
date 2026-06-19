import json
import pathlib
import datetime

theories = [
    "Furey/Dixon division-algebra Standard Model",
    "octonionic QM / Jordan algebra",
    "twistor/Hopf geometry",
    "IGT 8-strategy game theory",
    "QIT engine (Carnot/Szilard)",
    "holodeck/simulation",
    "entropic-monism cosmology"
]

rows = []
for theory in theories:
    if theory == "Furey/Dixon division-algebra Standard Model":
        role = "donor"
        what = "R(x)C(x)H(x)O ladder + the G2->SU(3) color target"
    elif theory == "octonionic QM / Jordan algebra":
        role = "donor"
        what = "J3(O) Jordan algebra and G2=Aut(O) dim 14 structures"
    elif theory == "twistor/Hopf geometry":
        role = "falsifier"
        what = "twistor space and Hopf fibration predictions that could falsify the Cl(6) bridge"
    elif theory == "IGT 8-strategy game theory":
        role = "donor"
        what = "8-strategy game theory finite structures for constraint admissibility"
    elif theory == "QIT engine (Carnot/Szilard)":
        role = "falsifier"
        what = "Carnot/Szilard engine bounds that could kill entropic readout claims"
    elif theory == "holodeck/simulation":
        role = "falsifier"
        what = "holodeck simulation artifacts that could falsify finite object admissibility"
    elif theory == "entropic-monism cosmology":
        role = "graveyard"
        what = "entropic monism correspondence already killed by non-associativity discriminator"
    row = {
        "theory": theory,
        "role": role,
        "what": what,
        "earned": False,
        "needs": ["own finite support object", "probe family", "readout map", "failing control"],
        "anti_collapse_note": "a different readout language over the same finite pattern, not the same thing by slogan"
    }
    rows.append(row)

graveyard_already_killed = [
    "non-associativity FORCED by bare root (killed by the discriminator: H passes the bare root)",
    "S3-minimum forced",
    "chirality forced",
    "sequential-universe toy",
    "old Rosetta relabeling"
]

result = {
    "catalog": rows,
    "graveyard_already_killed": graveyard_already_killed,
    "classification": "scratch_diagnostic",
    "promotion_allowed": False,
    "formal_admission_allowed": False,
    "correspondences_unearned_until_support_probe_readout_failing_control": True,
    "note": f"External theory mining catalog v0 generated at {datetime.datetime.now().isoformat()}"
}

output_path = pathlib.Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/external_theory_mining_catalog_v0_results.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w") as f:
    json.dump(result, f, indent=2)

donor_count = sum(1 for r in rows if r["role"] == "donor")
falsifier_count = sum(1 for r in rows if r["role"] == "falsifier")
graveyard_count = sum(1 for r in rows if r["role"] == "graveyard")
print(f"Catalog v0: {donor_count} donors, {falsifier_count} falsifiers, {graveyard_count} graveyards")
