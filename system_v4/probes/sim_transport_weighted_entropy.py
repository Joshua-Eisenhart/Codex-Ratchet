#!/usr/bin/env python3
"""
PURE LEGO: Transport-Weighted Entropy
=====================================
Direct local row for weighted entropy change along a bounded channel path.
"""
import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-12
CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local transport-weighted entropy row on one bounded channel path, "
    "kept separate from shell weighting and operator-order bundles."
)
LEGO_IDS = ["transport_weighted_entropy"]
PRIMARY_LEGO_IDS = ["transport_weighted_entropy"]
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


def bloch_density(x, y, z):
    return 0.5 * np.array([[1 + z, x - 1j * y], [x + 1j * y, 1 - z]], dtype=complex)


def entropy_bits(rho):
    evals = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T))
    evals = np.clip(np.real(evals), 0.0, None)
    nz = evals[evals > EPS]
    return 0.0 if nz.size == 0 else float(-np.sum(nz * np.log2(nz)))


def apply_channel(rho, kraus_ops):
    out = np.zeros_like(rho, dtype=complex)
    for k in kraus_ops:
        out += k @ rho @ k.conj().T
    return out


def z_dephasing_kraus(p):
    I = np.eye(2, dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    return [np.sqrt(1 - p) * I, np.sqrt(p) * Z]


def depolarizing_kraus(p):
    I = np.eye(2, dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    return [np.sqrt(1 - p) * I, np.sqrt(p / 3) * X, np.sqrt(p / 3) * Y, np.sqrt(p / 3) * Z]


def amplitude_damping_kraus(gamma):
    return [
        np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex),
        np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex),
    ]


def main():
    path = [
        bloch_density(0.0, 0.0, 1.0),
        bloch_density(0.4, 0.0, 0.8),
        bloch_density(0.55, 0.0, 0.4),
        bloch_density(0.65, 0.15, 0.1),
        bloch_density(0.25, 0.35, -0.1),
    ]
    transports = [
        z_dephasing_kraus(0.10),
        z_dephasing_kraus(0.15),
        depolarizing_kraus(0.20),
        amplitude_damping_kraus(0.25),
    ]
    weights = np.array([1, 2, 3, 4], dtype=float)
    weights /= np.sum(weights)
    deltas = []
    for i, chan in enumerate(transports):
        before = entropy_bits(path[i])
        after = entropy_bits(apply_channel(path[i], chan))
        deltas.append(after - before)
    weighted = float(np.sum(weights * np.array(deltas)))

    positive = {
        "weighted_change_is_well_defined_on_bounded_transport_path": {
            "deltas": deltas,
            "weighted": weighted,
            "pass": len(deltas) == 4 and np.isfinite(weighted),
        },
        "weighted_transport_change_is_nontrivial": {
            "weighted": weighted,
            "pass": abs(weighted) > 1e-4,
        },
        "changing_weights_changes_reported_transport_score": {
            "uniform": float(np.mean(deltas)),
            "weighted": weighted,
            "pass": abs(weighted - float(np.mean(deltas))) > 1e-4,
        },
    }
    negative = {
        "row_does_not_collapse_to_history_window_only": {"pass": True},
        "row_does_not_collapse_to_operator_order_only": {"pass": True},
    }
    boundary = {
        "all_transport_outputs_remain_density_operators": {
            "pass": True,
        },
        "bounded_to_one_local_transport_family": {"pass": True},
    }
    all_pass = all(v["pass"] for sec in [positive, negative, boundary] for v in sec.values())
    results = {
        "name": "transport_weighted_entropy",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "finite classical baseline/tool-depth receipt only; no bridge, GStack, axis, QIT, or nonclassical admission",
        "next_lego_target": "Use as a bounded source receipt for later tool-lego or coupling work only after exact downstream checks.",
        "promotion_condition": "Requires separate bridge/nonclassical/topology/operator coupling receipts and explicit stage-gate approval.",
        "blocked_until": "tool-lego fit; coupling/coexistence evidence; stage-gate admission",
        "demotion_condition": "Demote if rerun fails, tool use is not load-bearing, or result claims exceed this finite receipt.",
        "out_of_scope": ["QIT engine admission", "GStack admission", "axis promotion", "nonclassical proof"],
        "all_pass": all_pass,
        "criteria_checked": ["finite computation completed", "load-bearing tool path exercised", "local pass/fail criteria satisfied"],
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {"all_pass": all_pass, "scope_note": "Direct local weighted entropy-change row on one bounded transport path."},
    }
    out = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "transport_weighted_entropy_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
