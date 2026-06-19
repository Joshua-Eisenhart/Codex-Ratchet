#!/usr/bin/env python3
"""COMPOSING v7 ADMISSION RUNNER — runs ALL existing gates on ONE sim dir.

This is a thin ORCHESTRATOR. It owns no new admission math. It runs each
existing gate against a single sim directory and emits ONE pass/fail object
that names which gate failed. It never mutates a sim and never runs git in
this process (the per-sim scoping below deliberately avoids the repo-wide,
git-touching code paths of the underlying gates).

GATES COMPOSED (in order)
-------------------------
  1. math-only            scripts/validate_math_only_packet.py    (subprocess, sim dir)
  2. two-tier-authority   scripts/validate_two_tier_authority.py  (import: evaluate_sim, scoped to this sim)
  3. count-tautology-smt  scripts/validate_smt_not_tautology.py   (subprocess, sim dir)
  4. integrity            scripts/validate_result_integrity.py    (import: fragile-pin scoped to this sim)
  5. three-engine         scripts/validate_three_engine_sim_result.py --require-pytorch
                          (subprocess, on the *_envelope_results.json if one exists; N/A-ok otherwise)
  6. ancestry             (THIS file) the sim must cite F01/N01 lineage markers
                          and must NOT carry a top-floor name (axis / manifold /
                          bridge / engine-tier) WITHOUT that ancestry.

The ancestry gate is the only NEW check. It is mechanical and deterministic:
it scans the sim NAME and its result JSON for an AFFIRMATIVE, STRUCTURED
`F01` / `N01` lineage cite (a marker in a KEY with a non-denial value, or a
marker in a string VALUE under a lineage-signaling key), using whole-word
uppercase matching (so hex shas like `...f01cc84...` are NOT false hits). A
bare F01/N01 token loose in arbitrary prose — especially a negated note like
"no F01/N01 grounding" — does NOT count, and an explicit `f01_ancestry: null`
denial does NOT count. A top-floor-named sim (axis / manifold / bridge /
engine-tier) with no affirmative F01/N01 cite FAILS this gate; a non-top-floor
sim with no cite PASSES (the requirement only bites when a top-floor claim is
in the name).

SCOPING NOTE (honest): two of the underlying gates are written as repo-wide
sweeps (two-tier-authority sweeps --sims-root; integrity sweeps the whole repo
and reads `git`). To run them against ONE sim without a repo-wide sweep and
without git in this process, this runner imports and calls their per-sim
primitives directly (two_tier.evaluate_sim; integrity.detect_fragile_pins on
this sim's result files). The integrity gate's WORKING-TREE-DRIFT defect is a
repo+git concern, not a per-sim admission property, so it is intentionally NOT
run here and is named as such in that gate's detail.

OUTPUT: JSON {"ok": bool, "sim": str, "gate_results": [{"gate", "ok", "detail"}]}
EXIT:   0 if every gate ok (or N/A-ok), 1 if any gate fails, 2 on usage error.

USAGE:
  validate_v7_admission.py <sim_dir>
  validate_v7_admission.py --selftest
  validate_v7_admission.py --help

CEILING: this runner proves only that a sim dir clears the existing mechanical
gates plus the ancestry requirement. It recomputes no sim math and grants no
status above the gates it composes. classification=scratch_diagnostic,
promotion_allowed=false.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

# --- ancestry markers ------------------------------------------------------
# F01 / N01 matched as whole uppercase tokens so that lowercase hex fragments
# (e.g. a sha256 containing "f01") are NOT treated as a lineage marker.
ANCESTRY_MARKER_RE = re.compile(r"(?<![A-Za-z0-9])(F01|N01)(?![A-Za-z0-9])")

# Top-floor name tokens: a sim NAME carrying one of these makes a top-floor
# claim and therefore REQUIRES an F01/N01 ancestry marker. Whole-word match,
# case-insensitive (digit suffixes peeled so axis0/engine16 also match).
TOPFLOOR_TOKENS = frozenset({"axis", "manifold", "bridge", "engine"})


def _peel_tokens(text: str) -> set[str]:
    """Lowercase word-tokens with trailing digits peeled (axis0 -> axis)."""
    out: set[str] = set()
    for t in re.split(r"[^A-Za-z0-9]+", text.lower()):
        if not t:
            continue
        out.add(t)
        stripped = t.rstrip("0123456789")
        if stripped:
            out.add(stripped)
    return out


# ------------------------------------------------------------------------- #
# subprocess gate runner                                                     #
# ------------------------------------------------------------------------- #
def _run_subprocess_gate(script: str, args: list[str]) -> tuple[bool, str]:
    """Run an existing gate as a subprocess; ok == (exit code 0)."""
    cmd = [sys.executable, str(SCRIPTS_DIR / script), *args]
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    ok = proc.returncode == 0
    out = proc.stdout.strip()
    # Keep detail compact: prefer a one-line summary of the gate's JSON.
    detail = _summarize_gate_output(out, proc.returncode)
    return ok, detail


def _summarize_gate_output(out: str, returncode: int) -> str:
    """Compact one-line detail from a gate's JSON stdout."""
    try:
        doc = json.loads(out)
    except (json.JSONDecodeError, ValueError):
        return (out[:300] + (" ..." if len(out) > 300 else "")) or f"exit={returncode}"
    if isinstance(doc, dict):
        if "violations" in doc:
            v = doc["violations"]
            n = len(v) if isinstance(v, list) else 0
            if n == 0:
                return "clean (0 violations)"
            sample = v[0] if isinstance(v, list) and v else {}
            return f"{n} violation(s); first={json.dumps(sample)[:220]}"
        if "errors" in doc:
            e = doc["errors"]
            if isinstance(e, list) and e:
                return f"{len(e)} error(s); first={str(e[0])[:220]}"
            return "ok"
    return f"exit={returncode}"


# ------------------------------------------------------------------------- #
# individual gate adapters                                                   #
# ------------------------------------------------------------------------- #
def gate_math_only(sim_dir: Path) -> dict:
    ok, detail = _run_subprocess_gate("validate_math_only_packet.py", [str(sim_dir)])
    return {"gate": "math-only", "ok": ok, "detail": detail}


def gate_name_math(sim_dir: Path) -> dict:
    """B-side prosecutor: the sim NAME tokens must correlate to its actual math
    (a clean name over mismatched math is itself a hack)."""
    ok, detail = _run_subprocess_gate("validate_name_math_correlation.py", [str(sim_dir)])
    return {"gate": "name-math-correlation", "ok": ok, "detail": detail}


def gate_qubit_ladder(sim_dir: Path) -> dict:
    """Validity-tier: a 1q sim RUNS and is permitted as scratch, but is NOT valid
    alone. Fires only when a result claims validity without running the ladder to
    useful depth + one beyond."""
    ok, detail = _run_subprocess_gate("validate_qubit_ladder_depth.py", [str(sim_dir)])
    return {"gate": "qubit-ladder-depth", "ok": ok, "detail": detail}


def gate_smt_not_tautology(sim_dir: Path) -> dict:
    ok, detail = _run_subprocess_gate("validate_smt_not_tautology.py", [str(sim_dir)])
    return {"gate": "count-tautology-smt", "ok": ok, "detail": detail}


def gate_two_tier_authority(sim_dir: Path) -> dict:
    """Scoped to ONE sim via the gate's own per-sim primitive (no repo sweep)."""
    sys.path.insert(0, str(SCRIPTS_DIR))
    import validate_two_tier_authority as tt  # type: ignore

    violation, hard, soft = tt.evaluate_sim(sim_dir)
    if violation is None:
        return {
            "gate": "two-tier-authority",
            "ok": True,
            "detail": f"clean (hard_tokens={hard}, soft_tokens={soft})",
        }
    detail = (
        f"{violation.reason()} | audit_decision={violation.decision} | "
        f"decisive='{violation.decisive_sentence}' | "
        f"hard_paths={violation.hard_paths} | soft_paths={violation.soft_paths}"
    )
    return {"gate": "two-tier-authority", "ok": False, "detail": detail[:400]}


def gate_integrity(sim_dir: Path) -> dict:
    """Scoped to ONE sim: fragile-pin defect only (no git, no repo sweep).

    The working-tree-drift defect is a repo+git concern, not a per-sim
    admission property, so it is named-skipped here.
    """
    sys.path.insert(0, str(SCRIPTS_DIR))
    import validate_result_integrity as ri  # type: ignore

    result_files = sorted((sim_dir / "results").glob("*.json")) if (sim_dir / "results").is_dir() else sorted(sim_dir.glob("*.json"))
    fragile = ri.detect_fragile_pins(result_files)
    if fragile:
        return {
            "gate": "integrity",
            "ok": False,
            "detail": f"{len(fragile)} fragile-pin(s); first={json.dumps(fragile[0])[:260]} "
            "(working-tree-drift not run: repo+git scope)",
        }
    return {
        "gate": "integrity",
        "ok": True,
        "detail": f"clean (fragile-pin scoped to {len(result_files)} result file(s); "
        "working-tree-drift not run: repo+git scope)",
    }


def _find_envelope(sim_dir: Path) -> Path | None:
    results_dir = sim_dir / "results"
    search = results_dir if results_dir.is_dir() else sim_dir
    envs = sorted(p for p in search.glob("*_envelope_results.json") if p.stat().st_size > 0)
    return envs[0] if envs else None


def gate_three_engine(sim_dir: Path) -> dict:
    """Run the three-engine validator --require-pytorch on the envelope if one
    exists; otherwise N/A-ok (this gate only applies to three-engine packets)."""
    envelope = _find_envelope(sim_dir)
    if envelope is None:
        return {
            "gate": "three-engine",
            "ok": True,
            "detail": "N/A: no *_envelope_results.json in this sim (three-engine gate not applicable)",
        }
    ok, detail = _run_subprocess_gate(
        "validate_three_engine_sim_result.py", [str(envelope), "--require-pytorch"]
    )
    return {"gate": "three-engine", "ok": ok, "detail": f"envelope={envelope.name}: {detail}"}


# ------------------------------------------------------------------------- #
# ancestry gate (the one NEW check)                                          #
# ------------------------------------------------------------------------- #
def _result_files(sim_dir: Path) -> list[Path]:
    results_dir = sim_dir / "results"
    search = results_dir if results_dir.is_dir() else sim_dir
    return sorted(search.glob("*.json"))


# A KEY name signals a lineage/ancestry record; only such a key's VALUE is
# trusted to carry an affirmative F01/N01 cite. A bare F01/N01 token loose in
# arbitrary prose (a note, a comment, an unrelated description) is NOT a cite.
LINEAGE_KEY_RE = re.compile(r"(ancestry|lineage|provenance|derived_from|grounded_in|rung)", re.IGNORECASE)

# Denial phrasing: a value that MENTIONS F01/N01 only to deny grounding. Such a
# value does not establish ancestry even when it sits under a lineage key.
DENIAL_RE = re.compile(
    r"\b(no|not|none|never|without|absent|missing|lacks?|null|undefined|unestablished|"
    r"not\s+established|no\s+grounding|chosen)\b",
    re.IGNORECASE,
)


def _is_denial_value(value: object) -> bool:
    """True if the value denies / negates ancestry (null, false, empty, or a
    denial phrase)."""
    if value is None or value is False:
        return True
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return True
        return bool(DENIAL_RE.search(s))
    return False


def _scan_for_ancestry(node: object) -> bool:
    """True iff the tree carries an AFFIRMATIVE, STRUCTURED F01/N01 lineage cite.

    A marker counts only when it is one of:
      * an F01/N01-bearing KEY whose VALUE is affirmative (truthy, non-denial) —
        e.g. {"F01_pass": true} or {"f01_ancestry": "rung F01"};  a key like
        {"f01_ancestry": null} is a DENIAL and does NOT count.
      * an F01/N01 token in a string VALUE under a lineage-signaling key
        (ancestry/lineage/provenance/derived_from/grounded_in/rung) where the
        value is not a denial phrase.

    A bare F01/N01 token sitting in arbitrary non-lineage prose (a stray note or
    comment, especially a negated one like "no F01/N01 grounding") does NOT
    establish ancestry.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            key_str = str(key)
            key_has_marker = bool(ANCESTRY_MARKER_RE.search(key_str))
            key_is_lineage = bool(LINEAGE_KEY_RE.search(key_str))

            # (1) F01/N01 in the KEY itself: affirmative iff the value is not a denial.
            if key_has_marker and not _is_denial_value(value):
                return True

            # (2) F01/N01 in a string VALUE under a lineage-signaling key,
            #     affirmative phrasing only.
            if (
                key_is_lineage
                and isinstance(value, str)
                and ANCESTRY_MARKER_RE.search(value)
                and not _is_denial_value(value)
            ):
                return True

            # Recurse into the value (nested structured cites still count).
            if _scan_for_ancestry(value):
                return True
        return False
    if isinstance(node, list):
        return any(_scan_for_ancestry(item) for item in node)
    return False


def gate_ancestry(sim_dir: Path) -> dict:
    """The sim must cite F01/N01 lineage markers, and must NOT carry a top-floor
    name (axis/manifold/bridge/engine-tier) WITHOUT that ancestry.

    Rule:
      - top_floor_name AND no F01/N01 marker  -> FAIL (overreaching name w/o lineage)
      - everything else                       -> PASS
    """
    name = sim_dir.name
    topfloor_hits = sorted(_peel_tokens(name) & TOPFLOOR_TOKENS)
    is_topfloor = bool(topfloor_hits)

    # An F01/N01 marker may sit in the sim NAME or in any result JSON.
    has_marker = bool(ANCESTRY_MARKER_RE.search(name))
    files = _result_files(sim_dir)
    for f in files:
        if has_marker:
            break
        try:
            data = json.loads(f.read_text(encoding="utf-8", errors="replace"))
        except (json.JSONDecodeError, OSError):
            continue
        if _scan_for_ancestry(data):
            has_marker = True

    if is_topfloor and not has_marker:
        return {
            "gate": "ancestry",
            "ok": False,
            "detail": (
                f"top-floor name tokens {topfloor_hits} present but NO F01/N01 "
                f"lineage marker found in the sim name or any of {len(files)} result file(s)"
            ),
        }
    if is_topfloor:
        return {
            "gate": "ancestry",
            "ok": True,
            "detail": f"top-floor name tokens {topfloor_hits} present AND F01/N01 lineage marker found",
        }
    return {
        "gate": "ancestry",
        "ok": True,
        "detail": (
            "no top-floor name token; ancestry requirement not triggered"
            + (" (F01/N01 marker also present)" if has_marker else "")
        ),
    }


# ------------------------------------------------------------------------- #
# driver                                                                     #
# ------------------------------------------------------------------------- #
GATES = (
    gate_math_only,
    gate_name_math,
    gate_two_tier_authority,
    gate_smt_not_tautology,
    gate_integrity,
    gate_three_engine,
    gate_ancestry,
    gate_qubit_ladder,
)


def run(sim_dir: Path) -> dict:
    gate_results = [gate(sim_dir) for gate in GATES]
    ok = all(g["ok"] for g in gate_results)
    failed = [g["gate"] for g in gate_results if not g["ok"]]
    return {
        "ok": ok,
        "sim": sim_dir.name,
        "failed_gates": failed,
        "gate_results": gate_results,
    }


# ------------------------------------------------------------------------- #
# self-test (deterministic, in-process; touches no repo sim)                 #
# ------------------------------------------------------------------------- #
def _selftest() -> int:
    import tempfile

    failures: list[str] = []

    # --- ancestry marker regex: uppercase token yes, hex fragment no ---
    if not ANCESTRY_MARKER_RE.search("F01_pass"):
        failures.append("ancestry: missed F01_pass marker")
    if not ANCESTRY_MARKER_RE.search('"row_id": "N01"'):
        failures.append("ancestry: missed N01 marker")
    if ANCESTRY_MARKER_RE.search("bc1f720fe0b00df56f012c2c20df102847b9"):
        failures.append("ancestry: false-hit on hex fragment containing f01")
    if ANCESTRY_MARKER_RE.search("f012"):
        failures.append("ancestry: false-hit on lowercase f012")

    # --- top-floor token peel ---
    if "axis" not in _peel_tokens("axis0_contender_heavy_v0"):
        failures.append("topfloor: axis0 did not peel to axis")
    if "engine" not in _peel_tokens("engine_64_stage_full_run_v0"):
        failures.append("topfloor: engine token missed")
    if "manifold" in _peel_tokens("bloch_root_admissibility_v0"):
        failures.append("topfloor: false manifold token")
    gate_names = [gate.__name__ for gate in GATES]
    if "gate_name_math" not in gate_names:
        failures.append("composed gates: gate_name_math missing")
    if "gate_qubit_ladder" not in gate_names:
        failures.append("composed gates: gate_qubit_ladder missing")

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        def build(name: str, result: dict) -> Path:
            d = tmp / name / "results"
            d.mkdir(parents=True)
            (d / f"{name}_results.json").write_text(json.dumps(result), encoding="utf-8")
            return tmp / name

        # 1) top-floor name, no ancestry marker -> ancestry FAIL
        sim = build("manifold_super_sim_v0", {"all_pass": True, "density_trace": 1.0})
        g = gate_ancestry(sim)
        if g["ok"]:
            failures.append("ancestry gate: top-floor + no marker should FAIL")

        # 2) top-floor name, marker in a result key -> ancestry PASS
        sim = build("axis_triple_consistency_v0", {"F01_pass": True, "N01_pass": True})
        g = gate_ancestry(sim)
        if not g["ok"]:
            failures.append("ancestry gate: top-floor + F01/N01 marker should PASS")

        # 3) non-top-floor name, no marker -> ancestry PASS (not triggered)
        sim = build("bloch_root_admissibility_v0", {"all_pass": True})
        g = gate_ancestry(sim)
        if not g["ok"]:
            failures.append("ancestry gate: non-top-floor should PASS even without marker")

        # 4) top-floor name, marker only in the NAME-adjacent provenance value
        sim = build("engine_readout_v0", {"provenance_path": "lineage from F01/N01 rungs"})
        g = gate_ancestry(sim)
        if not g["ok"]:
            failures.append("ancestry gate: marker in lineage-key string value should PASS")

        # 4a) top-floor name, F01/N01 ONLY in a NEGATED prose note + null
        #     ancestry fields -> this must FAIL (the bad-twin dodge vector).
        sim = build(
            "axis_terrain_engine_dodge_v0",
            {
                "f01_ancestry": None,
                "n01_ancestry": None,
                "_ancestry_note": "axis/terrain names chosen; no F01/N01 grounding established",
            },
        )
        g = gate_ancestry(sim)
        if g["ok"]:
            failures.append("ancestry gate: negated-prose + null ancestry should FAIL (dodge vector)")

        # 4b) top-floor name, F01/N01 loose in an UNRELATED prose value (not a
        #     lineage key) -> must FAIL (a stray mention is not a cite).
        sim = build("axis_loose_prose_v0", {"comment": "see also F01 and N01 in the appendix"})
        g = gate_ancestry(sim)
        if g["ok"]:
            failures.append("ancestry gate: loose non-lineage prose marker should FAIL")

        # 4c) top-floor name, AFFIRMATIVE structured ancestry value -> PASS.
        sim = build("axis_grounded_v0", {"f01_ancestry": "rung F01 distinguishability constraint"})
        g = gate_ancestry(sim)
        if not g["ok"]:
            failures.append("ancestry gate: affirmative f01_ancestry value should PASS")

        # 5) three-engine N/A when no envelope present
        sim = build("plain_probe_v0", {"all_pass": True})
        g = gate_three_engine(sim)
        if not g["ok"] or "N/A" not in g["detail"]:
            failures.append("three-engine gate: should be N/A-ok without an envelope")

        # 6) integrity: clean fragile-pin scan on a non-self-pinned result
        sim = build("clean_probe_v0", {"all_pass": True, "x": 1})
        g = gate_integrity(sim)
        if not g["ok"]:
            failures.append("integrity gate: clean result should PASS fragile-pin scan")

        # 7) full run end-to-end on a clean math-pure sim whose NAME tokens are
        #    each backed by a result-JSON math structure (name<->math correlate).
        sim = build(
            "quotient_entropy_partition_v0",
            {
                "all_pass": True,
                "quotient_classes": [[0, 1], [2, 3]],
                "von_neumann_entropy": 0.6931471805599453,
                "partition_cut": {"AB": 0.5},
            },
        )
        report = run(sim)
        if not report["ok"]:
            failures.append(f"full run: clean sim should pass all gates, got failed={report['failed_gates']}")

    if failures:
        print("SELFTEST FAILED")
        for f in failures:
            print("  -", f)
        return 1
    print("SELFTEST PASSED")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Composing v7 admission runner: run ALL existing gates on ONE sim dir; "
        "emit one pass/fail naming which gate failed."
    )
    p.add_argument("sim_dir", nargs="?", help="path to a sim directory (with results/*.json).")
    p.add_argument("--selftest", action="store_true", help="run the built-in self-test and exit.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.selftest:
        return _selftest()
    if not args.sim_dir:
        print(json.dumps({"ok": False, "error": "provide a sim dir (or --selftest)"}))
        return 2
    sim_dir = Path(args.sim_dir)
    if not sim_dir.is_dir():
        print(json.dumps({"ok": False, "error": f"not a directory: {sim_dir}"}))
        return 2
    report = run(sim_dir)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
