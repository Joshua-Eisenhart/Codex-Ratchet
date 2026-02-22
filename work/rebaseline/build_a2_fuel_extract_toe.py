from __future__ import annotations

from pathlib import Path


def find_windows(lines: list[str], needle: str, window: int = 2, max_windows: int = 2) -> list[tuple[int, int]]:
    needle_l = needle.lower()
    hits: list[tuple[int, int]] = []
    for i, line in enumerate(lines):
        if needle_l in line.lower():
            a = max(0, i - window)
            b = min(len(lines), i + window + 1)
            hits.append((a, b))
            if len(hits) >= max_windows:
                break
    return hits


def emit_snippets(out: list[str], lines: list[str], title: str, needles: list[str]) -> None:
    out.append(f"## {title}\n")
    for needle in needles:
        windows = find_windows(lines, needle)
        if not windows:
            out.append(f"- MISSING_IN_EXTRACT: {needle}\n")
            continue
        for a, b in windows:
            snippet = "\n".join(lines[a:b]).strip("\n")
            out.append("```text\n" + snippet + "\n```\n")


def main() -> None:
    raw_path = Path("work/rebaseline/x_grok_chat_TOE__RAW_EXTRACT.txt")
    raw = raw_path.read_text(encoding="utf-8")
    lines = raw.splitlines()

    out: list[str] = []
    out.append("# A2_FUEL_EXTRACT — x grok chat TOE (NONCANON)\n")
    out.append("SOURCE: core_docs/high entropy doc/x grok chat TOE.docx\n")
    out.append("RAW_EXTRACT: work/rebaseline/x_grok_chat_TOE__RAW_EXTRACT.txt\n")
    out.append("STATUS: A2 fuel artifact (quarantine-first; no canon claims)\n")
    out.append("\n---\n")

    emit_snippets(
        out,
        lines,
        "RAW_CLAIM_SNIPPETS (verbatim)",
        [
            "spacetime itself literal entropy",
            "many possible futures create the present",
            "only causal force is consciousness",
            "gravity acts ftl",
            "dark energy is positive entropy",
            "dark matter is negative entropy",
            "random field",
            "hypersphere",
        ],
    )

    out.append("## QUARANTINE_VECTORS (do not ratchet directly)\n")
    out.append('- Teleology / deity language ("god", "destiny", "ends of time")\n')
    out.append('- Explicit causality / time-first narratives ("future causes present")\n')
    out.append("- Claims of FTL signaling (must be separated from non-signaling correlations)\n")
    out.append('- Speculative psych / DMT / aliens / transmissions (overlay-only)\n')

    out.append("\n## OPERATIONAL_CANDIDATE_REWRITES (noncanon; A2 proposals)\n")
    out.append(
        '- Replace "future possibilities" with: set of compatible refinements under constraints (ensemble / admissible set).\n'
    )
    out.append(
        '- Replace "converging futures" with: boundary-value constraints / path-ensemble weighting (no privileged future).\n'
    )
    out.append(
        '- Replace "spacetime is entropy" with: scalar functional(s) on nested coarse-grainings / cuts (candidate i-scalar).\n'
    )
    out.append(
        '- Replace "dark energy / dark matter entropy polarity" with: two monotones / two regimes of a functional under perturbation (candidate axis-like split; keep killable).\n'
    )
    out.append(
        '- Replace "gravity inverse square = square of possibilities" with: a scaling law hypothesis about an observable monotone vs cut-size (must be sim-measurable, not asserted).\n'
    )

    out.append("\n## REPO_LINKS (pointers only; no claims)\n")
    out.append("- core_docs/a2 hand assembled docs/uploads/AXIS0_PHYSICS_BRIDGE_v0.1.md\n")
    out.append("- core_docs/a2 hand assembled docs/uploads/PHYSICS_FUEL_DIGEST_v1.0.md (legacy overlay digest)\n")
    out.append("- core_docs/a2 hand assembled docs/uploads/sims/simpy (Axis-0 boundary bookkeeping evidence path)\n")

    Path("work/rebaseline/A2_FUEL_EXTRACT_x_grok_chat_TOE.md").write_text("".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()

