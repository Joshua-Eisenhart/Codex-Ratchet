#!/usr/bin/env python3
"""export_proposals.py — promote successful informal-loop patterns to formal-sim proposals.

The informal loop produces candidates that pass phases. Functions that:
  (a) come from a candidate passing at least N phases
  (b) survived the Codex audit (no P0 in the candidate's most recent review)
  (c) implement something with a clear math purpose (axes, terrains, manifold)

…get exported to `proposed_formal_sims/<name>.py` with:
  - the SIM_TEMPLATE header (classification, TOOL_MANIFEST, etc.)
  - the function body
  - provenance: which candidate, which generator, which audit findings

The user reviews these and decides which to promote into `system_v4/probes/` as
canonical legos. This loop's job ends at the proposal stage; the formal corpus
is the authority.
"""
import ast
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
CANDIDATES = HERE.parent / "candidates"
PROPOSED = HERE / "proposed_formal_sims"
RECEIPTS = HERE / "receipts"
PROBES = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes")


# Functions worth proposing if found clean. Math-named primitives only,
# retargeted at GAPS in the formal corpus.
#
# system_v4/probes/ saturation as of 2026-05-13:
#   hopf=266 weyl=285 clifford=174 gtower=118 spectral_triple=77 holonomy=74
#   chern=25 dephasing=9 mutual_info=8 berry=8 bipartite=9 landauer=7 kraus=6
#   coherent_info=4 petz=2 trace_distance=2 dfs=1 probe_class=0
#
# Saturated math themes are NOT promotion targets — duplicating them is noise.
# Gaps targeted: explicit 4-qubit Kraus channels, channel-order trace distance,
# dephasing-DFS basis identification, probe-quotient witness, quantum (not
# classical) Petz recovery, Kraus completeness + Choi roundtrip, and the two
# exploration-doc-§12 primitives (nested-constraint filtration, flux bakeoff).
PROPOSAL_TARGETS = {
    "nonidentity_kraus_channel_pair":      "channel_order_trace_distance_micro",
    "kraus_completeness_witness":          "kraus_completeness_witness_micro",
    "dephasing_channel_dfs":               "dephasing_fixed_subspace_basis_micro",
    "m_equivalence_witness":               "probe_expectation_equivalence_class_micro",
    "probe_expectation_quotient":          "probe_expectation_quotient_micro",
    "petz_recovery_quantum":               "petz_recovery_quantum_carrier_micro",
    "nested_constraint_filtration":        "nested_constraint_operator_set_filtration_micro",
    "flux_mechanism_bakeoff":              "flux_mechanism_observable_bakeoff_micro",
    "ordered_channel_composition_sequence": "ordered_channel_composition_sequence_micro",
}

# Auto-reject promotion if the extracted function body contains any of these.
# Treated as case-sensitive substring matches inside the function body text.
BANNED_TOKENS_IN_BODY = (
    "Ax0", "Ax1", "Ax2", "Ax3", "Ax4", "Ax5", "Ax6",
    "axis_index", "axis_transform", "axis_dof",
    "engine_stage", "engine_id", "Engine A", "Engine B", "Type 1", "Type 2",
    "stage_idx", "substage_idx", "stage_signature", "substage_signature",
    "gstack", "g_stack", "GStack",
    "terrain", "Terrain",
    "prime_resonance", "prime_score", "is_prime_classical",
    "hexagram", "trigram",
    "Carnot", "Szilard", "szilard",
    "IGT", "I_Ching", "I-Ching",
    "Jung", "MBTI",
)


SIM_TEMPLATE_HEADER = '''#!/usr/bin/env python3
"""{name} — PROPOSED formal sim lego (informal-scout output).

Source: {source_candidate}
Generator: {generator}
Origin run: {timestamp}
Scout phases passed: {phases_passed}

Status: PROPOSED — not yet canonical. Reviewer must promote into
system_v4/probes/ after validating against the SIM_TEMPLATE and the four-
sim-kinds doctrine (capability vs integration separation).

DO NOT use this file as authoritative until a human reviewer has graduated it
into system_v4/probes/. The informal scout is a proposal generator, not a
formal sim implementation.
"""

classification = "classical_baseline"          # promotion to canonical requires upgrade
admission_scope = "informal_scout_proposal"
promotion_allowed = False
claim_ceiling = ("proposal-only; final lego semantics, edge cases, and "
                  "tool integration depth must be validated by reviewer "
                  "before promotion to system_v4/probes/")

TOOL_MANIFEST = {{
    # Reviewer must fill in: which tools the canonical version will use load-bearingly.
}}

TOOL_INTEGRATION_DEPTH = {{
    # Reviewer must set: load_bearing / supportive / None per tool.
}}

# ============================================================================
# Function body extracted from {source_candidate}
# ============================================================================
'''


def extract_function_body(src: str, fn_name: str) -> str:
    """Extract `def fn_name(...): ... end` from source. Returns None if not found."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == fn_name:
            # AST gives line numbers; slice the source
            lines = src.split("\n")
            start = node.lineno - 1
            # Conservative end: next top-level def/class or EOF
            rest = "\n".join(lines[start:])
            m = re.search(r"\n(?:def|class)\s", rest)
            end = start + (rest[:m.start()].count("\n") + 1 if m else len(lines) - start)
            return "\n".join(lines[start:end])
    return None


def candidate_phase_count(candidate_path: Path) -> int:
    """Find the most recent runner _summary.json for this candidate; return
    the number of passing phases."""
    if not RECEIPTS.exists():
        return 0
    cand_str = str(candidate_path)
    runs = sorted([d for d in RECEIPTS.iterdir()
                   if d.is_dir() and (d / "_summary.json").exists()],
                  key=lambda d: d.name, reverse=True)
    for run in runs:
        try:
            s = json.loads((run / "_summary.json").read_text())
        except Exception:
            continue
        if s.get("candidate") == cand_str:
            return sum(1 for p in s.get("phases", []) if p.get("pass"))
    return 0


def already_in_formal_corpus(fn_name: str) -> bool:
    """Check if a function by that name already lives in system_v4/probes/."""
    if not PROBES.exists():
        return False
    pattern = re.compile(rf"^def\s+{re.escape(fn_name)}\s*\(", re.MULTILINE)
    for p in PROBES.glob("*.py"):
        try:
            if pattern.search(p.read_text(errors="ignore")):
                return True
        except Exception:
            continue
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: export_proposals.py <candidate_path> [--min-phases N]")
        sys.exit(1)
    cand_path = Path(sys.argv[1]).resolve()
    min_phases = int(sys.argv[sys.argv.index("--min-phases") + 1]) if "--min-phases" in sys.argv else 15
    if not cand_path.exists():
        print(f"candidate not found: {cand_path}"); sys.exit(1)
    phases_passed = candidate_phase_count(cand_path)
    if phases_passed < min_phases:
        print(f"candidate only passes {phases_passed} phases (< min {min_phases}); not promoting.")
        sys.exit(0)
    print(f"Candidate passes {phases_passed} phases; scanning for promotable functions...")

    src = cand_path.read_text()
    # Identify generator from filename
    name = cand_path.name
    if "grok" in name: gen = "grok-4.3"
    elif "gemini" in name: gen = "gemini-3.1-pro"
    elif "codex" in name: gen = "codex-gpt5.5"
    else: gen = "(mixed)"

    PROPOSED.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    promoted = []
    skipped_existing = []
    skipped_missing = []
    skipped_contaminated = []
    for fn_name, slug in PROPOSAL_TARGETS.items():
        body = extract_function_body(src, fn_name)
        if not body:
            skipped_missing.append(fn_name); continue
        if already_in_formal_corpus(fn_name):
            skipped_existing.append(fn_name); continue
        hits = [tok for tok in BANNED_TOKENS_IN_BODY if tok in body]
        if hits:
            skipped_contaminated.append((fn_name, hits[:5])); continue
        out = PROPOSED / f"sim_proposed_{slug}_{ts}.py"
        header = SIM_TEMPLATE_HEADER.format(
            name=out.name,
            source_candidate=cand_path.name,
            generator=gen,
            timestamp=ts,
            phases_passed=phases_passed,
        )
        out.write_text(header + body + "\n")
        promoted.append((fn_name, out.name))

    print(f"\nPromoted {len(promoted)} proposed lego(s):")
    for fn, path in promoted:
        print(f"  - {fn}  →  proposed_formal_sims/{path}")
    if skipped_existing:
        print(f"\nAlready in formal corpus (skipped): {skipped_existing}")
    if skipped_missing:
        print(f"\nNot present in candidate (no function): {skipped_missing[:5]}{'...' if len(skipped_missing)>5 else ''}")
    if skipped_contaminated:
        print(f"\nContaminated (banned identifier in body — NOT promoted):")
        for fn, toks in skipped_contaminated:
            print(f"  - {fn}: hit on {toks}")
    print(f"\nProposal dir: {PROPOSED}")
    print(f"Reviewer next step: check each proposed_formal_sims/*.py, fill in")
    print(f"TOOL_MANIFEST + TOOL_INTEGRATION_DEPTH, validate against SIM_TEMPLATE.py,")
    print(f"then move to system_v4/probes/ if it earns canonical status.")


if __name__ == "__main__":
    main()
