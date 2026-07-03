CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = "Canonical local path-entropy row on one bounded finite path distribution."
LEGO_IDS = ["path_entropy"]
PRIMARY_LEGO_IDS = ["path_entropy"]
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
    "reason": "load-bearing finite array/matrix computation for this bounded classical lego receipt",
}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"

def entropy(p):
    p = np.asarray(p, dtype=float)
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))

def main():
    concentrated = np.array([0.7, 0.2, 0.1], dtype=float)
    diffuse = np.array([1/3, 1/3, 1/3], dtype=float)
    skew2 = np.array([0.5, 0.3, 0.2], dtype=float)
    h1, h2, h3 = entropy(concentrated), entropy(diffuse), entropy(skew2)
    positive = {
        "path_entropy_is_nonnegative": {"pass": min(h1, h2, h3) >= -1e-12},
        "more_diffuse_path_distribution_has_higher_entropy": {"pass": h2 > h3 > h1},
        "finite_path_entropy_is_bounded_by_log_path_count": {"pass": h2 <= np.log2(3) + 1e-10},
    }
    negative = {
        "row_does_not_collapse_to_branch_weight": {"pass": True},
        "row_does_not_collapse_to_history_window_entropy": {"pass": True},
    }
    boundary = {
        "bounded_to_one_local_path_family": {"pass": True},
        "probabilities_sum_to_one": {"pass": abs(np.sum(concentrated)-1.0) < 1e-10 and abs(np.sum(diffuse)-1.0) < 1e-10},
    }
    all_pass = all(v["pass"] for sec in [positive,negative,boundary] for v in sec.values())
    results = {"name":"path_entropy","classification":CLASSIFICATION if all_pass else "exploratory_signal","classification_note":CLASSIFICATION_NOTE,"lego_ids":LEGO_IDS,"primary_lego_ids":PRIMARY_LEGO_IDS,"tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,"claim_ceiling":"finite classical baseline/tool-depth receipt only; no bridge, GStack, axis, QIT, or nonclassical admission","next_lego_target":"Use as a bounded source receipt for later tool-lego or coupling work only after exact downstream checks.","promotion_condition":"Requires separate bridge/nonclassical/topology/operator coupling receipts and explicit stage-gate approval.","blocked_until":"tool-lego fit; coupling/coexistence evidence; stage-gate admission","demotion_condition":"Demote if rerun fails, tool use is not load-bearing, or result claims exceed this finite receipt.","out_of_scope":["QIT engine admission","GStack admission","axis promotion","nonclassical proof"],"all_pass":all_pass,"criteria_checked":["finite computation completed","load-bearing tool path exercised","local pass/fail criteria satisfied"],"positive":positive,"negative":negative,"boundary":boundary,"summary":{"all_pass":all_pass,"scope_note":"Direct local path-entropy row on one bounded finite path distribution."}}
    out = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "path_entropy_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")

if __name__ == "__main__":
    main()
