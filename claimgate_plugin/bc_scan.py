#!/usr/bin/env python3
"""
bc_scan — static by-construction signature triage across a receipt corpus.

The cheap partner to canfail_probe. canfail_probe PROVES a check is
by-construction (subprocess mutation, exact). bc_scan TRIAGES: it flags checks
whose NAME matches a by-construction signature — entropy theorems, algebraic
identities, counting tautologies, symmetry-forced controls — so you know which
of hundreds of checks to point the (more expensive) mutation prober at.

    bc_scan <glob> [<glob> ...]      # e.g. 'system_v8/**/receipt.json'
        exit 0 always (a triage report, not a gate). Prints per-sim ratios + corpus total.

HONEST CEILING: a name match is a SUSPECT, never a proof — a check named
`entropy_subadditivity` is almost certainly a theorem that cannot fail, but the
only proof is a mutation that fails to flip it (canfail_probe). And a
by-construction check with a NEUTRAL name is missed entirely, so the ratio is a
LOWER BOUND on by-construction inflation, never an upper one.

No third-party deps. Python 3.
"""
import json, glob, re, sys

SIGNATURES = {
    "entropy_theorem":     r"subadditiv|araki_lieb|spohn|monoton|dS_zero|entropy.*invarian|unitary.*flat",
    "algebraic_identity":  r"matches_cumulative|product_matches|log2|chain.*matches|cumulative_capacity|bigint.*matches|fisher.*diag_inv|chain_identity|cross_blocks_vanish|round_trip",
    "counting_tautology":  r"count_\d+|_16$|_64$|total_60|_4_isolated|stage_count|census_total|complete_30|all_4_families_visited|len_",
    "decorative_finite":   r"finite_varying|series.*finite|_finite$|std_|nontrivial$|_present$|reaches_",
    "symmetry_forced":     r"flatten.*zero|flatten_control|static.*flat|aligned.*killed|_flat$|refocus|decouple.*collapse|erase.*dies|exactly_zero",
}
COMP = {k: re.compile(v, re.I) for k, v in SIGNATURES.items()}

def scan(paths):
    rows, tc, ts = [], 0, 0
    seen = set()
    for pat in paths:
        for f in glob.glob(pat, recursive=True):
            if f in seen: continue
            seen.add(f)
            try: r = json.load(open(f))
            except Exception: continue
            checks = r.get("checks")
            if not isinstance(checks, dict) or not checks: continue
            flagged = {}
            for name in checks:
                for cls, cp in COMP.items():
                    if cp.search(name): flagged.setdefault(cls, []).append(name); break
            n = sum(len(v) for v in flagged.values())
            tc += len(checks); ts += n
            rows.append({"receipt": f, "n_checks": len(checks), "n_suspect": n,
                         "ratio": round(n / len(checks), 3), "flagged": flagged})
    rows.sort(key=lambda x: -x["ratio"])
    return rows, tc, ts

def main():
    paths = [a for a in sys.argv[1:] if not a.startswith("--")] or ["system_v8/**/receipt.json"]
    rows, tc, ts = scan(paths)
    report = {
        "tool": "bc_scan",
        "corpus_checks": tc, "corpus_suspect": ts,
        "corpus_ratio_lower_bound": round(ts / tc, 3) if tc else 0.0,
        "note": "name-only triage; a match is a SUSPECT to confirm with canfail_probe, and this ratio is a LOWER BOUND (neutral-named by-construction checks are missed).",
        "per_receipt": rows,
    }
    print(json.dumps(report, indent=1))
    sys.exit(0)

if __name__ == "__main__":
    main()
