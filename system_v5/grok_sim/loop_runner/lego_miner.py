#!/usr/bin/env python3
"""lego_miner.py — find relevant formal-sim lego patterns for a given problem.

Two roles in the loop:

1. INPUT: for each iteration, given the failing-phase ID and the failure
   category, surface the top-K formal sims in `system_v4/probes/` that are
   most likely to inform the fix. Their function signatures + docstrings are
   injected into the generator prompt as reference patterns.

2. OUTPUT: after a candidate passes all phases AND audits cleanly, scan its
   functions for any that look novel (not present in the existing lego corpus)
   and propose them as new legos (writes to `proposed_legos/<name>.py` for
   user review).

The user's mental model:
- Formal sims under `system_v4/probes/` are the reusable lego library.
- The audit loop mines them as reference patterns for generators.
- When a candidate produces a clean novel function, it's a candidate lego —
  the loop proposes it, the user decides whether to promote.
"""
import re
import sys
from pathlib import Path

PROBES_DIR = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes")
PROPOSED_DIR = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/grok_sim/loop_runner/proposed_legos")

# Keyword index per phase category — maps a failure topic to lego search terms
PHASE_KEYWORDS = {
    "axioms":           ["mequivalence", "noncomm", "finitude", "M-equivalence"],
    "gstack":           ["gstack", "g_stack", "g_tower", "clifford", "hopf"],
    "axes":             ["axis", "axis_transform", "Ax_", "orthogonality", "axis_lie",
                         "compositional", "triplet"],
    "smt":              ["z3", "cvc5", "smt", "constraint"],
    "engine_traversal": ["engine", "traversal", "stage_sequence"],
    "tool_integration": ["tool_manifest", "load_bearing"],
    "engine_coupling":  ["coupling", "couple", "cross_engine"],
    "lie_bracket":      ["lie", "commutator", "bracket"],
    "entropy":          ["entropy", "monotonic", "von_neumann"],
    "replay":           ["replay", "determinism"],
    "stage_enumeration": ["stage_enumeration", "32_stages"],
    "summary":          ["summary_receipt", "consolidated"],
    "szilard":          ["szilard", "info_work", "landauer"],
    "axis_info_processor": ["axis_as_info", "info_processor"],
    "fisher":           ["fisher", "information_matrix", "IGT"],
    "iching":           ["iching", "hexagram", "i_ching"],
    "terrain":          ["terrain", "Ti_dephasing", "Te_dephasing", "Fi_", "Fe_"],
    "16stages":         ["16_stages", "4_substages", "stage_substage"],
    "probe_quotient":   ["probe_quotient", "compression", "M_class"],
    "holonomic":        ["holonomic", "berry_phase", "wilson_loop"],
    "dfs":              ["dfs", "decoherence_free"],
    "petz":             ["petz", "recovery_map", "channel_inverse"],
    "ai_tool_surface":  ["unified_tool", "ai_tool"],
    "prime_scaling":    ["prime", "totient", "euler", "coprime"],
    "stage_uniqueness": ["stage_uniqueness", "pairwise_distinct"],
    "manifold":         ["constraint_manifold", "manifold_rank", "svd"],
    "non_commutation":  ["noncomm", "ab_ba", "trace_distance"],
    "classifier":       ["classify_state", "trajectory_affinity"],
    "interpret":        ["explain_state", "interpretability"],
    "confidence":       ["confidence_calibration", "stage_confidence"],
    "prime_chain":      ["prime_chain", "signature_to_density"],
    "factorization":    ["factor", "smallest_prime_factor"],
    "denoise":          ["denoise", "channel_inverse", "petz"],
    "manifold_proj":    ["project_to_manifold", "nearest_reference"],
}


def phase_to_keywords(phase_id: str) -> list:
    """Map phase ID stem to a list of search keywords."""
    pid_lower = phase_id.lower()
    matched = []
    for key, kws in PHASE_KEYWORDS.items():
        if key in pid_lower:
            matched.extend(kws)
    if not matched:
        # Fall back to using the phase id parts themselves
        matched = [tok for tok in re.split(r"[_\d]+", pid_lower) if len(tok) > 3]
    return matched


def search_legos(keywords: list, top_k: int = 5) -> list:
    """Return [(path, score)] of top-K most relevant legos. Score = number of
    keyword matches in filename + docstring."""
    if not PROBES_DIR.exists():
        return []
    matches = []
    for p in PROBES_DIR.glob("*.py"):
        if p.name.startswith("_") or p.name.startswith("test_"):
            continue
        score = 0
        name_lower = p.name.lower()
        for kw in keywords:
            if kw.lower() in name_lower:
                score += 3   # filename match weighted higher
        # Light docstring scan (top of file only, to avoid reading 4000 files in full)
        try:
            head = p.read_text(errors="ignore")[:2000].lower()
            for kw in keywords:
                if kw.lower() in head:
                    score += 1
        except Exception:
            continue
        if score > 0:
            matches.append((p, score))
    matches.sort(key=lambda kv: -kv[1])
    return matches[:top_k]


def summarize_lego(path: Path, max_chars: int = 800) -> str:
    """Return a short summary: module docstring + function signatures (no bodies)."""
    try:
        src = path.read_text(errors="ignore")
    except Exception:
        return f"# {path.name} (unreadable)"
    # Module docstring
    docstring_match = re.match(r'^\s*"""(.*?)"""', src, re.DOTALL)
    doc = docstring_match.group(1).strip() if docstring_match else ""
    doc_first_para = doc.split("\n\n")[0] if doc else ""
    # Function signatures
    sigs = re.findall(r"^def\s+(\w+\([^)]*\)(?:\s*->\s*[^\n:]+)?):", src, re.MULTILINE)
    sigs_text = "\n".join(f"def {s}:" for s in sigs[:8])
    out = f"### {path.name}\n{doc_first_para[:400]}\n\n{sigs_text}"
    return out[:max_chars]


def mine_for_phase(phase_id: str, top_k: int = 4) -> str:
    """Top-level: given a phase ID, return a formatted reference-lego block
    for injection into a generator prompt."""
    kws = phase_to_keywords(phase_id)
    if not kws:
        return ""
    matches = search_legos(kws, top_k=top_k)
    if not matches:
        return ""
    blocks = ["## Reference lego patterns (system_v4/probes — mine these for reusable structures)"]
    blocks.append(f"Failure category keywords: {', '.join(kws[:6])}")
    blocks.append("")
    for path, score in matches:
        blocks.append(summarize_lego(path))
        blocks.append(f"(full file: `{path}`)\n")
    blocks.append("")
    blocks.append("If your implementation duplicates the structure of one of these legos, "
                  "import or adapt it rather than reimplementing. If your fix produces "
                  "something genuinely new not in this list, that's a candidate for "
                  "promotion to a new lego — the loop will detect and propose it.")
    return "\n".join(blocks)


# ---------- tool-pattern mining (canonical load-bearing examples) ----------
# Each tool the candidate imports has a canonical isolated capability sim
# under system_v4/probes/. These show MINIMAL LOAD-BEARING use of one tool,
# per the four-sim-kinds doctrine (capability vs integration separation).
# Generators MUST see these to avoid the decorative-import cheat.
TOOL_CANONICALS = {
    "z3":        "sim_both_engines_axes_0_to_7_z3_cvc5_structural_guard.py",
    "cvc5":      "sim_capability_cvc5_isolated.py",
    "clifford":  "sim_capability_clifford_isolated.py",
    "sympy":     "sim_compound_autograd_sympy_z3_fisher_admissibility.py",
    "gudhi":     "sim_capability_gudhi_isolated.py",
    "toponetx":  "sim_capability_toponetx_isolated.py",
    "torch":     "sim_pytorch_density_entropy_gradient_micro.py",
    "qutip":     "qutip_mesolve_amplitude_damping_channel_fit_probe.py",
    "pyg":       "sim_capability_pyg_isolated.py",
    "geomstats": "sim_capability_geomstats_isolated.py",
    "e3nn":      "sim_capability_e3nn_isolated.py",
    "rustworkx": "sim_compound_cvc5_rustworkx_toponetx_graph_topology.py",
    "networkx":  "sim_capability_networkx_isolated.py",
    "igraph":    "sim_capability_igraph_isolated.py",
    "hypothesis": "sim_capability_hypothesis_isolated.py",
    "hdbscan":   "sim_capability_hdbscan_isolated.py",
    "optuna":    "sim_capability_optuna_isolated.py",
    "datasketch": "sim_capability_datasketch_isolated.py",
    "cma":       "sim_capability_cma_isolated.py",
    "deap":      "sim_capability_deap_isolated.py",
    "evotorch":  "sim_capability_evotorch_isolated.py",
}


def detect_imports(code: str) -> list:
    """Extract imported module names from candidate code (top-level imports only)."""
    imports = set()
    for m in re.finditer(r"^(?:import|from)\s+([\w.]+)", code, re.MULTILINE):
        # Take the top-level package name
        imports.add(m.group(1).split(".")[0])
    return sorted(imports)


def mine_tool_patterns(candidate_code: str, max_per_tool_chars: int = 1500) -> str:
    """Given candidate source, identify imported tools and surface the canonical
    load-bearing pattern for each. This is INJECTED INTO EVERY GENERATOR PROMPT
    regardless of failing phase — the tool-integration audit fires on any
    decorative import, so generators must always see the right patterns.
    """
    imports = detect_imports(candidate_code)
    relevant_tools = [t for t in imports if t in TOOL_CANONICALS]
    if not relevant_tools:
        return ""
    blocks = [
        "## Canonical load-bearing tool-use patterns (system_v4/probes)",
        "Your candidate imports these tools. Each must be USED (not just imported)",
        "for `tool_manifest()` to truthfully report it. Decorative imports get flagged",
        "as cheats. See the corresponding canonical sim for the minimal load-bearing",
        "pattern (TOOL_MANIFEST + TOOL_INTEGRATION_DEPTH conventions):",
        "",
    ]
    for tool in relevant_tools[:8]:   # cap to avoid prompt bloat
        sim_name = TOOL_CANONICALS[tool]
        sim_path = PROBES_DIR / sim_name
        if not sim_path.exists():
            continue
        try:
            src = sim_path.read_text(errors="ignore")
        except Exception:
            continue
        # Extract: module docstring + TOOL_MANIFEST line for this tool + first
        # load-bearing function signature
        doc_m = re.match(r'^\s*"""(.*?)"""', src, re.DOTALL)
        doc = doc_m.group(1).strip().split("\n\n")[0] if doc_m else ""
        # Find the tool's manifest entry
        manifest_entry = ""
        m = re.search(rf'"{tool}"\s*:\s*\{{[^}}]+\}}', src)
        if m:
            manifest_entry = m.group(0)[:200]
        # Find first non-trivial function signature
        sigs = re.findall(r"^def\s+(\w+\([^)]*\))", src, re.MULTILINE)
        first_sig = sigs[0] if sigs else ""
        block = (
            f"### {tool} → `{sim_name}`\n"
            f"  {doc[:200]}\n"
            f"  manifest pattern: `{manifest_entry}`\n"
            f"  example fn: `{first_sig}`"
        )
        blocks.append(block[:max_per_tool_chars])
    return "\n".join(blocks)


# ---------- proposed-lego detection (output side) ----------
def propose_legos_from_candidate(candidate_path: Path) -> list:
    """Scan a passing+audited candidate for novel functions and propose them as legos.

    Returns a list of (function_name, source_snippet) for each function that:
      - is defined at module level in the candidate
      - does NOT appear by name in any existing lego under system_v4/probes
      - is non-trivial (>10 lines of code)

    Writes each proposed lego to `proposed_legos/<func_name>.py` for user review.
    """
    if not candidate_path.exists():
        return []
    src = candidate_path.read_text()
    # Extract module-level function defs
    funcs = []
    pattern = re.compile(r"^def\s+(\w+)\s*\(([^)]*)\)([^:]*):\s*$", re.MULTILINE)
    for m in pattern.finditer(src):
        name = m.group(1)
        start = m.start()
        # Find the end of the function (next ^def or ^class or EOF)
        rest = src[m.end():]
        end_match = re.search(r"^(?:def|class)\s", rest, re.MULTILINE)
        body_end = m.end() + (end_match.start() if end_match else len(rest))
        body = src[start:body_end].rstrip()
        line_count = body.count("\n")
        if line_count < 10:
            continue   # skip trivial helpers
        funcs.append((name, body))
    # Check which names are NOT in any existing lego
    proposed = []
    for name, body in funcs:
        try:
            r = list(PROBES_DIR.glob("*.py"))
            already_exists = False
            for p in r:
                if name in p.read_text(errors="ignore"):
                    already_exists = True
                    break
            if not already_exists:
                proposed.append((name, body))
        except Exception:
            continue
    # Write proposals
    PROPOSED_DIR.mkdir(parents=True, exist_ok=True)
    for name, body in proposed:
        out = PROPOSED_DIR / f"{name}.py"
        out.write_text(
            f'"""Proposed lego — extracted from candidate {candidate_path.name}.\n'
            f'Status: candidate (audit-pending). User must review before promotion.\n"""\n'
            f"# Source: {candidate_path}\n\n{body}\n"
        )
    return proposed


# ---------- CLI ----------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: lego_miner.py mine <phase_id>  |  lego_miner.py propose <candidate.py>")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "mine":
        phase_id = sys.argv[2]
        print(mine_for_phase(phase_id))
    elif cmd == "propose":
        path = Path(sys.argv[2])
        props = propose_legos_from_candidate(path)
        print(f"Proposed {len(props)} new legos:")
        for name, _ in props:
            print(f"  - {name}  →  {PROPOSED_DIR / (name + '.py')}")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
