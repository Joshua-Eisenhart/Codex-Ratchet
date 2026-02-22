"""A1 Fuel Ingestion: reads constraint ladder docs, extracts entries, reformulates for B.

This is A2's mining tool + A1's processing tool combined.
It takes E0-E1 constraint ladder docs and produces:
  1. Structured fuel entries (for fuel_queue.json)
  2. B-grammar proposals (EXPORT_BLOCK format) for A0/runner
  3. Pool seeds (for state.pool at init)

The constraint ladder docs use ASSUME/DERIVE/OPEN tagging with explicit IDs.
They still need:
  - B-grammar reformulation (SPEC_HYP, SPEC_KIND, REQUIRES, DEF_FIELD, ASSERT)
  - Jargon check (no derived-only words in non-string fields)
  - Dependency resolution (REQUIRES chains respect constraint order)
  - OPEN entries → graveyard pool as DEAD items

Usage:
  python3 a1_fuel_ingest.py --doc <path>          # parse and preview
  python3 a1_fuel_ingest.py --doc <path> --emit   # write EXPORT_BLOCK
  python3 a1_fuel_ingest.py --batch               # process all canon specs
  python3 a1_fuel_ingest.py --update-queue        # update fuel_queue.json
"""

import argparse
import json
import os
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPO = BASE.parent.parent
LADDER = REPO / "core_docs" / "a2 hand assembled docs" / "uploads" / "constraint ladder"
A2_STATE = REPO / "work" / "a2_state"

# Canon constraint ladder docs in dependency order
CANON_SPECS = [
    "COSMOLOGICALLY_CONSTRAINT_ADMISSIBLE_STRUCTURES_v1.md",
    "STATE_ABSTRACTION_ADMISSIBILITY_v1.md",
    "RELATIONAL_TRANSPORT_ADMISSIBILITY_v1.md",
    "OBSTRUCTION_ADMISSIBILITY_v1.md",
    "CONSTRAINT_MANIFOLD_DERIVATION_v1.md",
    "GEOMETRY_ADMISSIBILITY_v1.md",
    "METRIC_ADMISSIBILITY_v1.md",
    "COORDINATE_ADMISSIBILITY_v1.md",
    "DIMENSIONALITY_ADMISSIBILITY_v1.md",
    "AXIS_FUNCTION_ADMISSIBILITY_v1.md",
    "AXIS_SET_ADMISSIBILITY_v1.md",
    "ORTHOGONALITY_ADMISSIBILITY_v1.md",
    "COMPLETENESS_ADMISSIBILITY_v1.md",
    "COMPOSITION_CLASS_ADMISSIBILITY_v1.md",
    "DUALITY_CLASS_ADMISSIBILITY_v1.md",
    "CYCLE_CLASS_ADMISSIBILITY_v1.md",
    "DYNAMICAL_ADMISSIBILITY_BOUNDARY_v1.md",
    "CANDIDATE_PROPOSAL_v1.md",
]

# Derived-only words that need TERM_DEF before use in OBJECTS/OPERATIONS/INVARIANTS
DERIVED_ONLY_CHECK = {
    "identity", "equality", "equal", "function", "domain", "codomain",
    "metric", "distance", "coordinate", "time", "cause", "number",
    "probability", "complex", "set", "relation", "map",
}

# B lexeme set — safe to use directly
LEXEME_SET = {
    "finite", "dimensional", "hilbert", "space", "density", "matrix",
    "operator", "channel", "cptp", "unitary", "lindblad", "hamiltonian",
    "commutator", "anticommutator", "trace", "partial", "tensor",
    "superoperator", "generator",
}


def parse_entry_line(line: str):
    """Parse a constraint ladder entry line.
    Format: [TAG] ID LABEL: body
    Returns (tag, id, label, body) or None.
    """
    line = line.strip()
    # Strip bold markers
    line = line.replace("**", "").strip()
    m = re.match(r'\[(ASSUME|DERIVE|OPEN)\]\s+(\w+)\s+(\w+):\s*(.*)', line)
    if m:
        return m.group(1), m.group(2), m.group(3), m.group(4).strip()
    return None


def parse_doc(path: Path) -> list:
    """Parse a constraint ladder doc, return list of entry dicts."""
    text = path.read_text(encoding="utf-8", errors="replace")
    entries = []
    # Extract doc name from path
    doc_name = path.name.replace("_v1.md", "").replace(".md", "")

    for line in text.splitlines():
        parsed = parse_entry_line(line)
        if parsed:
            tag, cid, label, body = parsed
            # Infer prefix from doc name
            prefix = _doc_prefix(doc_name)
            full_id = f"{prefix}{cid}"
            entries.append({
                "id": full_id,
                "constraint_id": cid,
                "tag": tag,
                "label": label,
                "body": body,
                "source_doc": path.name,
                "doc_name": doc_name,
            })
    return entries


def _doc_prefix(doc_name: str) -> str:
    """Get the ID prefix for a doc — use the doc's own constraint IDs."""
    # IDs like CAS01, RTA01 already have the prefix embedded
    return ""


def entries_to_proposals(entries: list, admitted_terms: set = None) -> list:
    """Convert parsed entries to B-grammar proposal tuples (spec_id, lines).

    ASSUME entries → AXIOM_HYP or foundational SPEC_HYP CONSTRAINT_DEF
    DERIVE entries → SPEC_HYP CONSTRAINT_DEF with REQUIRES chain
    OPEN entries → deposited in graveyard pool (not proposed to B directly)
    """
    admitted = admitted_terms or set()
    proposals = []
    graveyard_pool = []
    prev_id = None

    for entry in entries:
        tag = entry["tag"]
        spec_id = f"S_{entry['constraint_id']}"
        label = entry["label"]
        body = entry["body"]

        # Check for derived-only words in label/body
        flagged = _check_derived_only(label + " " + body)

        if tag == "OPEN":
            # OPEN entries go to graveyard pool — not proposed yet
            graveyard_pool.append({
                "id": spec_id,
                "source": entry["source_doc"],
                "label": label,
                "body": body,
                "chain_needs": [f"S_{entry['constraint_id'][:-2]}{int(entry['constraint_id'][-2:])-1:02d}"] if len(entry['constraint_id']) > 2 else [],
                "flagged_words": flagged,
            })
            prev_id = spec_id
            continue

        # Constraint ladder entries → MATH_DEF (the correct B kind for
        # mathematical relation structures with named objects and invariants)
        lines = [f"SPEC_HYP {spec_id}"]
        lines.append(f"SPEC_KIND {spec_id} CORR MATH_DEF")

        if tag == "ASSUME":
            lines.append(f"REQUIRES {spec_id} CORR F01_FINITUDE")
            lines.append(f"REQUIRES {spec_id} CORR N01_NONCOMMUTATION")
        else:  # DERIVE
            if prev_id:
                lines.append(f"REQUIRES {spec_id} CORR {prev_id}")

        # OBJECTS: use label words that are lexeme-safe
        obj_words = _safe_object_words(label)
        if obj_words:
            lines.append(f"DEF_FIELD {spec_id} CORR OBJECTS {obj_words}")
        else:
            lines.append(f"DEF_FIELD {spec_id} CORR OBJECTS finite operator")

        # OPERATIONS: generic — will need refinement per entry
        lines.append(f"DEF_FIELD {spec_id} CORR OPERATIONS operator")

        # INVARIANTS: finitude + noncommutation are the universal invariants
        lines.append(f"DEF_FIELD {spec_id} CORR INVARIANTS trace")

        # DOMAIN/CODOMAIN: hilbert space as default substrate
        lines.append(f"DEF_FIELD {spec_id} CORR DOMAIN hilbert space")
        lines.append(f"DEF_FIELD {spec_id} CORR CODOMAIN hilbert space")

        # SIM_CODE_HASH: placeholder
        lines.append(f"DEF_FIELD {spec_id} CORR SIM_CODE_HASH_SHA256 " + "0" * 64)

        # LABEL annotation — goes in quoted string, any words OK there
        lines.append(f'DEF_FIELD {spec_id} CORR LABEL "{label}"')

        lines.append(f"ASSERT {spec_id} CORR EXISTS MATH_TOKEN MT_{spec_id}")
        proposals.append((spec_id, lines))
        prev_id = spec_id

    return proposals, graveyard_pool


def _safe_object_words(label: str) -> str:
    """Extract lexeme-safe words from a label for OBJECTS field."""
    words = re.findall(r'[a-z]+', label.lower())
    safe = [w for w in words if w in LEXEME_SET and len(w) > 2]
    return " ".join(safe[:4]) if safe else ""


def _check_derived_only(text: str) -> list:
    """Return list of derived-only words found in text (outside quoted strings)."""
    # Remove quoted content
    text_no_quotes = re.sub(r'"[^"]*"', '', text.lower())
    found = []
    words = re.findall(r'\b\w+\b', text_no_quotes)
    for word in words:
        if word in DERIVED_ONLY_CHECK:
            found.append(word)
    return list(set(found))


def build_export_block(proposals: list, export_id: str) -> str:
    """Wrap proposals in an EXPORT_BLOCK for B."""
    from containers import build_export_block as _build
    content = []
    # Add one probe per 10 specs
    spec_count = len(proposals)
    n_probes = max(1, spec_count // 10)
    for i in range(n_probes):
        pid = f"P_CL_{export_id[:6]}_{i+1:03d}"
        content += [
            f"PROBE_HYP {pid}",
            f"PROBE_KIND {pid} CORR PROBE_HYP",
            f"ASSERT {pid} CORR EXISTS PROBE_TOKEN PT_{pid}",
        ]
    for _, lines in proposals:
        content.extend(lines)
    return _build(export_id, "CONSTRAINT_LADDER", content, version="v1")


def update_fuel_queue(new_entries: list):
    """Merge new entries into fuel_queue.json."""
    path = A2_STATE / "fuel_queue.json"
    if path.exists():
        fuel = json.loads(path.read_text())
    else:
        fuel = {"version": 1, "entries": []}

    existing_ids = {e["id"] for e in fuel["entries"]}
    added = 0
    for entry in new_entries:
        if entry["id"] not in existing_ids:
            fuel["entries"].append({
                "id": entry["id"],
                "tag": entry["tag"],
                "label": entry["label"],
                "body": entry["body"][:200],
                "source_doc": entry["source_doc"],
                "concepts_needed": [],
            })
            added += 1

    path.write_text(json.dumps(fuel, indent=2))
    return added


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc", type=str, help="Path to a single constraint ladder doc")
    parser.add_argument("--emit", action="store_true", help="Emit EXPORT_BLOCK to stdout")
    parser.add_argument("--batch", action="store_true", help="Process all canon specs")
    parser.add_argument("--update-queue", action="store_true", help="Update fuel_queue.json")
    parser.add_argument("--run-dir", default=os.path.join("runs", "ratchet_v2"))
    args = parser.parse_args()

    docs_to_process = []

    if args.doc:
        docs_to_process = [Path(args.doc)]
    elif args.batch:
        for name in CANON_SPECS:
            p = LADDER / name
            if p.exists():
                docs_to_process.append(p)
            else:
                print(f"  MISSING: {name}")

    if not docs_to_process:
        print("No docs to process. Use --doc <path> or --batch")
        return

    all_entries = []
    all_proposals = []
    all_pool = []

    for doc_path in docs_to_process:
        entries = parse_doc(doc_path)
        proposals, pool_items = entries_to_proposals(entries)
        all_entries.extend(entries)
        all_proposals.extend(proposals)
        all_pool.extend(pool_items)

        tag_counts = {}
        for e in entries:
            tag_counts[e["tag"]] = tag_counts.get(e["tag"], 0) + 1

        flagged_count = sum(1 for _, lines in proposals
                            if any("BODY_QUARANTINED" in l for l in lines))

        print(f"\n{doc_path.name}")
        print(f"  entries: {len(entries)} ({tag_counts})")
        print(f"  proposals: {len(proposals)} → B")
        print(f"  pool (OPEN): {len(pool_items)}")
        print(f"  flagged (derived-only): {flagged_count}")

    print(f"\nTotal: {len(all_proposals)} proposals, {len(all_pool)} pool items")

    if args.emit and all_proposals:
        block = build_export_block(all_proposals, "CL_BATCH_001")
        print("\n" + block)

    if args.update_queue and all_entries:
        added = update_fuel_queue(all_entries)
        print(f"\nFuel queue updated: {added} new entries added")


if __name__ == "__main__":
    main()
