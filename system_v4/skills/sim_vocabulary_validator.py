import os
import re
from pathlib import Path
import sys

REPO = str(Path(__file__).resolve().parents[2])
sys.path.insert(0, REPO)

from system_v4.skills.a1_brain import L0_LEXEME_SET, DERIVED_ONLY_TERMS, DISCOURSE_STOPLIST, OVERLAY_TERMS, JARGON_TERMS

def scan_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Find all words in comments and string literals
    words_in_strings_and_comments = []
    
    # Simple regex to get strings and comments
    for match in re.finditer(r'(#.*)|(\'[^\']*\'|"[^"]*")', content):
        text = match.group(0).lower()
        words = re.findall(r'[a-z]+', text)
        words_in_strings_and_comments.extend(words)

    # Word counts
    word_set = set(words_in_strings_and_comments)
    
    overlay_violations = word_set & OVERLAY_TERMS
    jargon_violations = word_set & JARGON_TERMS
    
    # Note: SIMs are allowed to use derived/overlay terms *if* they are tracking the metrics,
    # but the strict V3 interpretation might prohibit them entirely in the canon core.
    
    return overlay_violations, jargon_violations

def main():
    probes_dir = Path(REPO) / "system_v4" / "probes"
    violation_count = 0
    
    for f in sorted(os.listdir(probes_dir)):
        if f.endswith("_sim.py"):
            o_viol, j_viol = scan_file(probes_dir / f)
            if o_viol or j_viol:
                print(f"Warning in {f}:")
                if o_viol:
                    print(f"  Overlay Terms: {', '.join(o_viol)}")
                if j_viol:
                    print(f"  Jargon Terms: {', '.join(j_viol)}")
                violation_count += 1
                
    print(f"\nTotal SIM files with terminology violations: {violation_count}")

if __name__ == "__main__":
    main()
