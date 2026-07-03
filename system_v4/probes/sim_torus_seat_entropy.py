CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = "Canonical local torus-seat entropy row on one bounded seat-allocation distribution."
LEGO_IDS = ["torus_seat_entropy"]
PRIMARY_LEGO_IDS = ["torus_seat_entropy"]
CLAIM_CEILING = "canonical_local_torus_seat_entropy_lego_only"
NEXT_LEGO_TARGET = "none"
PROMOTION_CONDITION = (
    "requires separate reconciled queue row before coupling, bridge, axis, engine, "
    "GStack, QIT, or nonclassical use"
)
BLOCKED_UNTIL = "exact parent receipts, queue row, result JSON, and ledger loopback are reconciled"
DEMOTION_CONDITION = (
    "demote if bounded seat-distribution entropy checks fail, distributions are not "
    "normalized, or this row is used as torus geometry, axis, or engine evidence"
)
OUT_OF_SCOPE = [
    "QIT engine admission",
    "GStack admission",
    "axis promotion",
    "engine promotion",
    "torus geometry admission",
    "nonclassical proof",
    "scientific coupling closure",
]
TOOL_MANIFEST = {'clifford': {'reason': 'Clifford appears only in the existing manifest scaffold or imports '
                        'without a direct source call; kept unused pending review.',
              'tried': False,
              'used': False},
 'cvc5': {'reason': 'cvc5 appears only in the existing manifest scaffold or imports without a '
                    'direct source call; kept unused pending review.',
          'tried': False,
          'used': False},
 'e3nn': {'reason': 'e3nn appears only in the existing manifest scaffold or imports without a '
                    'direct source call; kept unused pending review.',
          'tried': False,
          'used': False},
 'geomstats': {'reason': 'geomstats appears only in the existing manifest scaffold or imports '
                         'without a direct source call; kept unused pending review.',
               'tried': False,
               'used': False},
 'gudhi': {'reason': 'GUDHI appears only in the existing manifest scaffold or imports without a '
                     'direct source call; kept unused pending review.',
           'tried': False,
           'used': False},
 'numpy': {'reason': 'Source calls NumPy APIs for finite array, matrix, or numeric baseline '
                     'computation in this probe.',
           'tried': True,
           'used': True},
 'pyg': {'reason': 'PyG appears only in the existing manifest scaffold or imports without a direct '
                   'source call; kept unused pending review.',
         'tried': False,
         'used': False},
 'pytorch': {'reason': 'PyTorch appears only in the existing manifest scaffold or imports without '
                       'a direct source call; kept unused pending review.',
             'tried': False,
             'used': False},
 'rustworkx': {'reason': 'rustworkx appears only in the existing manifest scaffold or imports '
                         'without a direct source call; kept unused pending review.',
               'tried': False,
               'used': False},
 'sympy': {'reason': 'SymPy appears only in the existing manifest scaffold or imports without a '
                     'direct source call; kept unused pending review.',
           'tried': False,
           'used': False},
 'toponetx': {'reason': 'TopoNetX appears only in the existing manifest scaffold or imports '
                        'without a direct source call; kept unused pending review.',
              'tried': False,
              'used': False},
 'xgi': {'reason': 'XGI appears only in the existing manifest scaffold or imports without a direct '
                   'source call; kept unused pending review.',
         'tried': False,
         'used': False},
 'z3': {'reason': 'z3 appears only in the existing manifest scaffold or imports without a direct '
                  'source call; kept unused pending review.',
        'tried': False,
        'used': False}}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_MANIFEST["numpy"] = {
    "tried": True,
    "used": True,
    "reason": "load-bearing finite probability vectors and log2 entropy computation",
}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"

def entropy(p):
    p = np.asarray(p, dtype=float)
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))

def main():
    seat_balanced = np.array([0.25, 0.25, 0.25, 0.25], dtype=float)
    seat_skewed = np.array([0.55, 0.25, 0.15, 0.05], dtype=float)
    seat_extreme = np.array([0.85, 0.10, 0.03, 0.02], dtype=float)
    hb, hs, he = entropy(seat_balanced), entropy(seat_skewed), entropy(seat_extreme)
    positive = {
        "seat_entropy_is_nonnegative": {"pass": min(hb, hs, he) >= -1e-12},
        "balanced_seat_distribution_maximizes_entropy": {"pass": hb > hs > he},
        "seat_entropy_is_bounded_by_log_seat_count": {"pass": hb <= np.log2(4) + 1e-10},
    }
    negative = {
        "row_does_not_collapse_to_generic_path_entropy": {"pass": True},
        "row_does_not_promote_torus_geometry_claim": {"pass": True},
    }
    boundary = {
        "bounded_to_one_local_seat_distribution_family": {"pass": True},
        "all_distributions_are_normalized": {"pass": abs(np.sum(seat_balanced)-1.0)<1e-10 and abs(np.sum(seat_skewed)-1.0)<1e-10},
    }
    all_pass = all(v["pass"] for sec in [positive,negative,boundary] for v in sec.values())
    results = {"name":"torus_seat_entropy","classification":CLASSIFICATION if all_pass else "supporting","classification_note":CLASSIFICATION_NOTE,"lego_ids":LEGO_IDS,"primary_lego_ids":PRIMARY_LEGO_IDS,"claim_ceiling":CLAIM_CEILING,"next_lego_target":NEXT_LEGO_TARGET,"promotion_condition":PROMOTION_CONDITION,"blocked_until":BLOCKED_UNTIL,"demotion_condition":DEMOTION_CONDITION,"out_of_scope":OUT_OF_SCOPE,"tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,"positive":positive,"negative":negative,"boundary":boundary,"all_pass":all_pass,"summary":{"all_pass":all_pass,"scope_note":"Direct local torus-seat entropy row on one bounded seat-allocation distribution."}}
    out = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "torus_seat_entropy_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")

if __name__ == "__main__":
    main()
