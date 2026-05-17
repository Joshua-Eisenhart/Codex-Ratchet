#!/usr/bin/env python3
"""build_fully_stripped.py — strip every function with known P0 cheats.

Takes candidate_iter_02 and replaces these 8 functions with raise NotImplementedError stubs:
  prime_resonance, engine_stage, fisher_information_matrix,
  holonomic_gate, flux_holonomy, probe_quotient_compress,
  denoise_pipeline, classify_state

Plus the cheat-extension functions added later:
  explain_state, signature_to_density_matrix, project_to_manifold

The stripped candidate cannot inherit cheats from input — generators must
implement these from the public contract.
"""
import re
import sys
from pathlib import Path

SRC = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/grok_sim/candidates/candidate_iter_02_20260513T092900Z.py")
DST = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/grok_sim/candidates/candidate_fully_stripped.py")

STRIP_FUNCS = [
    "prime_resonance",
    "engine_stage",
    "fisher_information_matrix",
    "holonomic_gate",
    "flux_holonomy",
    "probe_quotient_compress",
    "denoise_pipeline",
    "classify_state",
    "explain_state",
    "signature_to_density_matrix",
    "project_to_manifold",
]

STUB_TEMPLATE = '''def {name}(*args, **kwargs):
    """STRIPPED — must be reimplemented from public_api_contract.md.
    Original Claude-authored version contained P0 cheats (see OPUS_AUDIT_2026_05_13.md).
    """
    raise NotImplementedError("STRIPPED for clean regeneration; see public_api_contract.md")


'''


def strip_function(src: str, name: str) -> str:
    """Replace a function definition with a stub. Handles multi-line defs."""
    pattern = re.compile(
        rf"^def\s+{re.escape(name)}\s*\([^)]*\)[^:]*:\s*\n",
        re.MULTILINE,
    )
    m = pattern.search(src)
    if not m:
        return src
    # Find the end: next ^def or ^class or end of file
    rest = src[m.end():]
    end_match = re.search(r"^(?:def|class)\s", rest, re.MULTILINE)
    body_end = m.end() + (end_match.start() if end_match else len(rest))
    # Replace
    return src[:m.start()] + STUB_TEMPLATE.format(name=name) + src[body_end:]


def main():
    src = SRC.read_text()
    for fn in STRIP_FUNCS:
        before = src
        src = strip_function(src, fn)
        if src == before:
            print(f"  (skipped: {fn} not found)")
        else:
            print(f"  stripped: {fn}")
    DST.write_text(src)
    print(f"\nWrote: {DST}")
    print(f"Size: {len(src)} chars (was {len(SRC.read_text())} chars)")


if __name__ == "__main__":
    main()
