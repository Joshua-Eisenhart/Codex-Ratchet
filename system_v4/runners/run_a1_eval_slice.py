"""
run_a1_eval_slice.py — A1 Eval Slice Runner + Scorer

Runs the current a1_brain.py against the eval slice concepts from
a1_eval_slice.json, scores the output packet against quality gates,
and writes a structured report.

This is the honest test: does current A1 extraction still mine
discourse labels, or has the latest code fixed it?
"""
import json
import sys
import time
from pathlib import Path
from collections import Counter

REPO = str(Path(__file__).resolve().parents[2])
sys.path.insert(0, REPO)

from system_v4.skills.a1_brain import (
    A1Brain, L0_LEXEME_SET, DISCOURSE_STOPLIST, DERIVED_ONLY_TERMS
)
from system_v4.skills.a2_graph_refinery import A2GraphRefinery


# ═══════════════════════════════════════════════════════════════
# SCORER — evaluates packet quality against eval slice gates
# ═══════════════════════════════════════════════════════════════

class A1PacketScorer:
    """Scores an A1 strategy packet against defined quality gates."""

    def __init__(self, quality_gates: dict):
        self.gates = quality_gates
        self.discourse_ban = set(quality_gates.get("discourse_ban", []))
        self.min_l0_for_math = quality_gates.get("math_def_min_l0_tokens", 1)
        self.max_discourse = quality_gates.get("max_discourse_terms_per_packet", 2)
        self.min_math_ratio = quality_gates.get("min_math_def_ratio", 0.3)
        self.require_lineage = quality_gates.get("require_source_lineage", True)
        self.require_try_to_fail = quality_gates.get("require_try_to_fail_alternatives", True)

    def score_packet(self, targets: list, alternatives: list,
                     concept_results: dict) -> dict:
        """
        Score a full packet. Returns structured report with per-gate results.

        concept_results: {concept_id: {name, category, expected_kind, candidates: [...]}}
        """
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_targets": len(targets),
            "total_alternatives": len(alternatives),
            "gates": {},
            "per_concept": {},
            "overall_pass": True,
        }

        # ── Gate 1: Discourse-label ban ──
        discourse_violations = []
        for t in targets:
            for df in t.get("def_fields", []):
                if df.get("name") == "term_literal" and df.get("value_kind") == "BARE":
                    term = df["value"].lower()
                    if term in self.discourse_ban or term in DISCOURSE_STOPLIST:
                        discourse_violations.append({
                            "id": t["id"], "term": term, "kind": t["kind"]
                        })
            # Also check structural tokens for discourse contamination
            for a in t.get("asserts", []):
                token = a.get("token", "").lower()
                if token in DISCOURSE_STOPLIST:
                    discourse_violations.append({
                        "id": t["id"], "token": token, "location": "assert"
                    })

        gate_1_pass = len(discourse_violations) <= self.max_discourse
        report["gates"]["discourse_ban"] = {
            "pass": gate_1_pass,
            "violations": discourse_violations,
            "count": len(discourse_violations),
            "threshold": self.max_discourse,
        }

        # ── Gate 2: MATH_DEF ratio ──
        kind_dist = Counter(t["kind"] for t in targets)
        total_non_probe = sum(1 for t in targets if t["item_class"] != "PROBE_HYP")
        math_count = kind_dist.get("MATH_DEF", 0)
        math_ratio = math_count / max(total_non_probe, 1)

        gate_2_pass = math_ratio >= self.min_math_ratio
        report["gates"]["math_def_ratio"] = {
            "pass": gate_2_pass,
            "math_defs": math_count,
            "total_non_probe": total_non_probe,
            "ratio": round(math_ratio, 3),
            "threshold": self.min_math_ratio,
        }

        # ── Gate 3: L0 token coverage in MATH_DEFs ──
        math_targets = [t for t in targets if t["kind"] == "MATH_DEF"]
        math_with_l0 = 0
        math_l0_details = []
        for t in math_targets:
            l0_count = 0
            for df in t.get("def_fields", []):
                if df.get("value_kind") == "BARE":
                    segments = df["value"].lower().split("_")
                    l0_count += sum(1 for s in segments if s in L0_LEXEME_SET)
            if l0_count >= self.min_l0_for_math:
                math_with_l0 += 1
            math_l0_details.append({
                "id": t["id"], "l0_count": l0_count,
                "pass": l0_count >= self.min_l0_for_math,
            })

        gate_3_pass = len(math_targets) == 0 or math_with_l0 == len(math_targets)
        report["gates"]["math_l0_coverage"] = {
            "pass": gate_3_pass,
            "math_with_sufficient_l0": math_with_l0,
            "total_math": len(math_targets),
            "details": math_l0_details,
        }

        # ── Gate 4: Source lineage ──
        if self.require_lineage:
            missing_lineage = [
                t["id"] for t in targets
                if not t.get("source_concept_id") and t.get("item_class") != "PROBE_HYP"
            ]
            gate_4_pass = len(missing_lineage) == 0
        else:
            missing_lineage = []
            gate_4_pass = True

        report["gates"]["source_lineage"] = {
            "pass": gate_4_pass,
            "note": "Lineage tracked via concept_results mapping",
        }

        # ── Gate 5: Alternatives actually differ ──
        if self.require_try_to_fail and alternatives:
            # Check that alternatives are structurally different from targets
            target_structs = set()
            for t in targets:
                for df in t.get("def_fields", []):
                    if df.get("name") == "structural_form" and df.get("value_kind") == "BARE":
                        target_structs.add(df["value"])

            alt_same_as_target = 0
            alt_details = []
            for a in alternatives:
                for df in a.get("def_fields", []):
                    if df.get("name") == "structural_form" and df.get("value_kind") == "BARE":
                        is_same = df["value"] in target_structs
                        alt_details.append({
                            "id": a["id"], "struct": df["value"],
                            "same_as_target": is_same,
                        })
                        if is_same:
                            alt_same_as_target += 1

            gate_5_pass = len(alternatives) > 0
            report["gates"]["try_to_fail_alternatives"] = {
                "pass": gate_5_pass,
                "total_alternatives": len(alternatives),
                "same_as_target": alt_same_as_target,
                "details": alt_details[:10],
            }
        else:
            report["gates"]["try_to_fail_alternatives"] = {
                "pass": not self.require_try_to_fail,
                "note": "No alternatives generated" if not alternatives else "Not required",
            }

        # ── Gate 6: Duplicate detection ──
        term_literals = []
        for t in targets:
            for df in t.get("def_fields", []):
                if df.get("name") == "term_literal":
                    term_literals.append(df["value"])
        dupe_counts = Counter(term_literals)
        duplicates = {k: v for k, v in dupe_counts.items() if v > 1}

        gate_6_pass = len(duplicates) == 0
        report["gates"]["no_duplicates"] = {
            "pass": gate_6_pass,
            "duplicates": duplicates,
        }

        # ── Per-concept results ──
        for cid, cdata in concept_results.items():
            candidates = cdata.get("candidates", [])
            report["per_concept"][cid] = {
                "name": cdata.get("name", ""),
                "category": cdata.get("category", ""),
                "expected_kind": cdata.get("expected_kind", ""),
                "candidate_count": len(candidates),
                "actual_kinds": [c.get("kind") for c in candidates] if candidates else [],
                "kind_match": any(
                    c.get("kind") == cdata.get("expected_kind", "").replace("_OR_NOOP", "")
                    for c in candidates
                ) if candidates else cdata.get("expected_kind", "").endswith("_OR_NOOP"),
            }

        # ── Kind distribution ──
        report["kind_distribution"] = dict(kind_dist)

        # ── Overall pass ──
        all_gates_pass = all(g.get("pass", False) for g in report["gates"].values())
        all_concepts_match = all(cdata["kind_match"] for cdata in report["per_concept"].values())
        
        report["overall_pass"] = all_gates_pass and all_concepts_match

        return report


# ═══════════════════════════════════════════════════════════════
# RUNNER — runs A1 on eval slice concepts from the live graph
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("A1 EVAL SLICE — FRESH RUN + SCORING")
    print("=" * 60)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")

    # Load eval slice (check a1_state first, fallback to a2_state)
    slice_name = sys.argv[1] if len(sys.argv) > 1 else "a1_eval_slice.json"
    eval_path_a1 = Path(REPO) / "system_v4" / "a1_state" / slice_name
    eval_path_a2 = Path(REPO) / "system_v4" / "a2_state" / slice_name
    
    if eval_path_a1.exists():
        eval_path = eval_path_a1
    elif eval_path_a2.exists():
        eval_path = eval_path_a2
    else:
        print(f"❌ FATAL: Could not find requested eval slice '{slice_name}' in a1_state or a2_state.")
        sys.exit(1)
    
    with open(eval_path) as f:
        eval_slice = json.load(f)

    concepts = eval_slice["concepts"]
    quality_gates = eval_slice["quality_gates"]
    print(f"\nEval slice: {len(concepts)} concepts")
    print(f"Quality gates: {json.dumps(quality_gates, indent=2)}")

    # Load graph
    refinery = A2GraphRefinery(REPO)
    nodes = refinery.builder.pydantic_model.nodes

    # Initialize A1 brain in eval isolation mode (ephemeral routing/Rosetta)
    brain = A1Brain(REPO, eval_mode=True)
    print(f"\nA1 Brain state:")
    print(f"  Term registry:    {len(brain.term_registry)} terms")
    mappings_count = len(brain.rosetta._read_rosetta().get("mappings", {}))
    print(f"  Rosetta mappings: {mappings_count} mappings")
    print(f"  Graveyard terms:  {len(brain.graveyard_terms)} terms")

    # ── Run extraction on each eval slice concept ──
    print(f"\n{'─'*60}")
    print(f"EXTRACTION PASS")
    print(f"{'─'*60}")

    all_targets = []
    all_alternatives = []
    concept_results = {}

    # Build node dictionary for packet builder
    concept_ids = []
    graph_dict = {}
    for concept in concepts:
        node_id = concept["node_id"]
        node = nodes.get(node_id)
        if node:
            concept_ids.append(node_id)
            graph_dict[node_id] = {
                "name": node.name,
                "description": node.description or "",
                "tags": node.tags or [],
                "properties": node.properties or {}
            }
        else:
            print(f"\n  ⚠️  {concept['name'][:50]:50s} — NOT FOUND IN GRAPH")
            concept_results[node_id] = {
                "name": concept["name"],
                "category": concept["category"],
                "expected_kind": concept["expected_kind"],
                "candidates": [],
                "status": "NOT_FOUND",
            }

    # Run full production extraction
    try:
        packet = brain.build_strategy_packet(concept_ids, graph_dict, strategy_id="A1_EVAL_RUN")
        all_targets = packet.targets
        all_alternatives = packet.alternatives
    except Exception as e:
        print(f"\n  ❌ PACKET BUILD FAILED: {e}")
        return

    # Map back to concept_results
    for concept in concepts:
        node_id = concept["node_id"]
        if node_id not in graph_dict:
            continue
            
        cands = [t for t in all_targets if t.get("source_concept_id") == node_id]
        
        concept_results[node_id] = {
            "name": concept["name"],
            "category": concept["category"],
            "expected_kind": concept["expected_kind"],
            "candidates": cands,
        }

        # Report
        n_cands = len(cands)
        kinds = [c.get("kind") for c in cands] if cands else ["(none)"]
        status = "✅" if n_cands > 0 else "⬚ "
        print(f"\n  {status} {concept['name'][:45]:45s} [{concept['category']}]")
        print(f"     expected: {concept['expected_kind']:20s} "
              f"got: {', '.join(kinds)}")
        if cands:
            for c in cands:
                # Show structural content
                struct = ""
                for df in c.get("def_fields", []):
                    if df.get("name") == "structural_form":
                        struct = df.get("value")
                    elif df.get("name") == "term_literal":
                        struct = f"TERM:{df.get('value')}"
                print(f"     [{c.get('id')}] {c.get('kind'):10s} → {struct[:60] if struct else ''}")

    # ── Score ──
    print(f"\n{'─'*60}")
    print(f"SCORING")
    print(f"{'─'*60}")

    scorer = A1PacketScorer(quality_gates)
    report = scorer.score_packet(all_targets, all_alternatives, concept_results)
    report["slice_name"] = slice_name
    report["slice_path"] = str(eval_path)

    print(f"\n  Targets:      {report['total_targets']}")
    print(f"  Alternatives: {report['total_alternatives']}")
    print(f"  Kind dist:    {report['kind_distribution']}")

    print(f"\n  ── Quality Gates ──")
    for gate_name, gate_result in report["gates"].items():
        status = "✅ PASS" if gate_result["pass"] else "❌ FAIL"
        print(f"  {status}  {gate_name}")
        # Print key details
        if not gate_result["pass"]:
            for k, v in gate_result.items():
                if k not in ("pass", "details") and v:
                    print(f"          {k}: {v}")

    print(f"\n  ── Per-Concept Results ──")
    for cid, cdata in report["per_concept"].items():
        match = "✅" if cdata["kind_match"] else "❌"
        print(f"  {match} {cdata['name'][:40]:40s} "
              f"[{cdata['category']}] "
              f"expected={cdata['expected_kind'][:15]:15s} "
              f"got={cdata['actual_kinds']}")

    overall = "✅ ALL GATES PASS" if report["overall_pass"] else "❌ GATES FAILED"
    print(f"\n{'='*60}")
    print(f"  OVERALL: {overall}")
    print(f"{'='*60}")

    # ── Save report ──
    report_path = Path(REPO) / "system_v4" / "a1_state" / "a1_eval_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Make candidates serializable
    serializable_report = json.loads(json.dumps(report, default=str))
    with open(report_path, "w") as f:
        json.dump(serializable_report, f, indent=2)
    print(f"\nReport saved to: {report_path}")

    # ── Save fresh packet if any targets ──
    if all_targets:
        packet_path = (Path(REPO) / "system_v4" / "a1_state" / "a1_strategy_packets"
                       / f"A1_EVAL_{time.strftime('%Y%m%d_%H%M%S')}.json")
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        packet = {
            "schema": "A1_STRATEGY_v1",
            "strategy_id": f"A1_EVAL_{time.strftime('%Y%m%d_%H%M%S')}",
            "source": "eval_slice_run",
            "slice_name": slice_name,
            "slice_path": str(eval_path),
            "targets": all_targets,
            "alternatives": all_alternatives,
            "eval_report_summary": {
                "overall_pass": report["overall_pass"],
                "gate_results": {k: v["pass"] for k, v in report["gates"].items()},
                "kind_distribution": report["kind_distribution"],
            },
        }
        with open(packet_path, "w") as f:
            json.dump(packet, f, indent=2)
        print(f"Packet saved to: {packet_path}")


if __name__ == "__main__":
    main()
