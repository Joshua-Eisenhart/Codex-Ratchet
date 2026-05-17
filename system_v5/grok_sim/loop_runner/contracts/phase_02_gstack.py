"""phase_02_gstack.py — geometric constraint manifold (G-stack) layer.

The G-stack is the geometric substrate on which the axes' dynamics live.
This phase must pass BEFORE per-axis dynamics phases. The G-stack itself is
geometry (not toggleable), so we check that the carrier-level geometric
structures are well-formed and connected.

Checks (via function calls only — no stdout scraping):
  1. weyl_chirality_probe(): ψ_L and ψ_R have OPPOSITE-sign Bloch z components,
     |z_L|, |z_R| > 0.5 (so they're not near-zero degenerate states)
  2. flux_holonomy(): nonzero holonomy of U(1) connection around a closed loop
  3. gstack_layers(): exactly 4 nested layers with dependencies (1→0, 2→1, 3→2)
  4. Hopf projection consistency: ψ = |0⟩ → (0,0,1); ψ = |1⟩ → (0,0,-1); both
     have unit norm projection
  5. Clifford geometric product is non-trivial (the layer-2 product list contains
     ≥1 product not equal to a basis element)

Goal-stability: once green, the geometric structure is frozen for all
downstream axis phases.
"""
import numpy as np


def _check_weyl_chirality(candidate):
    failures = []
    metrics = {}
    try:
        r = candidate.weyl_chirality_probe()
    except Exception as e:
        return [{"check": "weyl_call", "msg": f"raised {type(e).__name__}: {str(e)[:300]}"}], {}

    for key in ("bloch_z_L", "bloch_z_R", "opposite_signs"):
        if key not in r:
            failures.append({"check": f"weyl_missing_key_{key}", "msg": f"key `{key}` not in weyl_chirality_probe()"})
    if failures:
        return failures, metrics

    zL = float(r["bloch_z_L"])
    zR = float(r["bloch_z_R"])
    metrics["bloch_z_L"] = zL
    metrics["bloch_z_R"] = zR

    if zL * zR >= 0:
        failures.append({
            "check": "weyl_opposite_signs",
            "msg": f"ψ_L Bloch z = {zL}, ψ_R Bloch z = {zR}. Their product is {zL * zR}, not negative — "
                   f"chirality requires opposite-sign Bloch projections.",
        })
    if abs(zL) < 0.5:
        failures.append({
            "check": "weyl_L_z_magnitude",
            "msg": f"|ψ_L Bloch z| = {abs(zL)} < 0.5 — ψ_L is too close to equator (degenerate chirality)",
        })
    if abs(zR) < 0.5:
        failures.append({
            "check": "weyl_R_z_magnitude",
            "msg": f"|ψ_R Bloch z| = {abs(zR)} < 0.5 — ψ_R is too close to equator (degenerate chirality)",
        })

    independent_opposite = (zL * zR) < 0
    if independent_opposite != bool(r["opposite_signs"]):
        failures.append({
            "check": "weyl_independent_recompute",
            "msg": f"opposite_signs reported as {r['opposite_signs']} but independent sign-product is {independent_opposite}",
        })
    return failures, metrics


def _check_flux_holonomy(candidate):
    failures = []
    metrics = {}
    try:
        f = candidate.flux_holonomy()
    except Exception as e:
        return [{"check": "flux_call", "msg": f"raised {type(e).__name__}: {str(e)[:300]}"}], {}

    if not isinstance(f, (int, float)):
        failures.append({"check": "flux_type", "msg": f"flux_holonomy() returned {type(f).__name__}, expected float"})
        return failures, metrics

    metrics["flux_holonomy"] = float(f)

    if abs(f) < 0.01:
        failures.append({
            "check": "flux_nonzero",
            "msg": f"flux_holonomy() = {f}. Magnitude below 0.01 indicates trivial U(1) connection "
                   f"(zero winding) or path-ordered exponential collapsing to identity. The bundle "
                   f"must have non-trivial winding/holonomy for flux to be real geometry.",
        })

    # Stability: same input → same output (deterministic geometry)
    f2 = candidate.flux_holonomy()
    metrics["flux_holonomy_repeat"] = float(f2)
    if abs(f - f2) > 1e-6:
        failures.append({
            "check": "flux_stable",
            "msg": f"flux_holonomy() returned {f} then {f2} — non-deterministic. Geometry must be reproducible.",
        })

    return failures, metrics


def _check_gstack_layers(candidate):
    failures = []
    metrics = {}
    try:
        r = candidate.gstack_layers()
    except Exception as e:
        return [{"check": "gstack_call", "msg": f"raised {type(e).__name__}: {str(e)[:300]}"}], {}

    # 4 layers
    for n in range(4):
        key = f"layer_{n}"
        if key not in r:
            failures.append({"check": f"gstack_missing_{key}", "msg": f"key `{key}` not in gstack_layers()"})
    if failures:
        return failures, metrics

    # Layer parent links — each layer (1,2,3) should reference its predecessor
    for n in range(1, 4):
        layer_n = r.get(f"layer_{n}", {})
        if not isinstance(layer_n, dict):
            failures.append({"check": f"gstack_layer_{n}_dict",
                             "msg": f"layer_{n} is {type(layer_n).__name__}, expected dict"})
            continue
        parent = layer_n.get("parent")
        if parent is None:
            failures.append({"check": f"gstack_layer_{n}_parent",
                             "msg": f"layer_{n} missing 'parent' field — no dependency link to layer_{n-1}"})
        # Accept either a string reference "layer_{n-1}" or a dict containing the parent
        elif isinstance(parent, str) and parent != f"layer_{n-1}":
            failures.append({"check": f"gstack_layer_{n}_parent_target",
                             "msg": f"layer_{n}.parent = '{parent}', expected 'layer_{n-1}'"})

    # Dependencies field — must include the 3 ascending links
    deps = r.get("dependencies", [])
    metrics["dependencies"] = deps
    expected = [(1, 0), (2, 1), (3, 2)]
    deps_normalized = [tuple(d) if isinstance(d, (list, tuple)) else None for d in deps]
    missing = [e for e in expected if e not in deps_normalized]
    if missing:
        failures.append({
            "check": "gstack_dependencies",
            "msg": f"dependencies missing the required ascending links: {missing}. "
                   f"Got: {deps}. Must include all of [(1,0), (2,1), (3,2)].",
        })

    metrics["layers_present"] = sum(1 for n in range(4) if f"layer_{n}" in r)
    return failures, metrics


def _check_hopf_consistency(candidate):
    """Independently verify Hopf projection on basis states |0⟩ and |1⟩.

    Since the candidate may not expose a `hopf_project()` function directly,
    we read the weyl_chirality_probe() result (which uses the same ψ basis)
    and require ψ_L=|0⟩→Bloch_z=+1, ψ_R=|1⟩→Bloch_z=-1 within tolerance."""
    failures = []
    metrics = {}
    try:
        r = candidate.weyl_chirality_probe()
        zL = float(r["bloch_z_L"])
        zR = float(r["bloch_z_R"])
    except Exception as e:
        return [{"check": "hopf_via_weyl", "msg": f"could not get Bloch zs from weyl_chirality_probe: {e}"}], {}

    if not (abs(zL - 1.0) < 0.05):
        failures.append({
            "check": "hopf_psi_L_at_north",
            "msg": f"ψ_L Bloch z = {zL}, expected ≈ +1.0 (north pole) for canonical chirality choice |0⟩",
        })
    if not (abs(zR - (-1.0)) < 0.05):
        failures.append({
            "check": "hopf_psi_R_at_south",
            "msg": f"ψ_R Bloch z = {zR}, expected ≈ -1.0 (south pole) for canonical chirality choice |1⟩",
        })

    metrics["hopf_north_distance"] = abs(zL - 1.0)
    metrics["hopf_south_distance"] = abs(zR - (-1.0))
    return failures, metrics


def _check_clifford_nontrivial(candidate):
    """The Clifford layer (layer_2) should expose at least one non-trivial geometric product."""
    failures = []
    metrics = {}
    try:
        r = candidate.gstack_layers()
        layer_2 = r.get("layer_2", {})
    except Exception as e:
        return [{"check": "clifford_via_gstack", "msg": str(e)[:200]}], {}

    products = layer_2.get("products") if isinstance(layer_2, dict) else None
    if products is None or not isinstance(products, list) or len(products) < 1:
        failures.append({
            "check": "clifford_products_present",
            "msg": "layer_2 must expose a `products` list with at least 1 geometric product (e.g., e1*e2). "
                   "This proves the Clifford algebra is actually being used, not just imported.",
        })
        return failures, metrics

    metrics["clifford_products_count"] = len(products)
    # Non-trivial = not all products are single-blade strings like 'e0' or 'e1'
    # Heuristic: at least one product string should contain '*', '^', or be longer than 2 chars
    non_trivial = [p for p in products if isinstance(p, str) and (len(p) > 2 or "*" in p or "^" in p)]
    if not non_trivial:
        failures.append({
            "check": "clifford_products_nontrivial",
            "msg": f"layer_2.products = {products} — all are trivial single-blade. Need a real geometric product.",
        })
    return failures, metrics


def run(candidate):
    all_failures = []
    all_metrics = {}

    for name, check_fn in [
        ("weyl_chirality", _check_weyl_chirality),
        ("flux_holonomy",  _check_flux_holonomy),
        ("gstack_layers",  _check_gstack_layers),
        ("hopf",           _check_hopf_consistency),
        ("clifford",       _check_clifford_nontrivial),
    ]:
        f, m = check_fn(candidate)
        all_failures.extend(f)
        all_metrics[name] = m

    return {
        "pass": len(all_failures) == 0,
        "failures": all_failures,
        "metrics": all_metrics,
        "graveyard_companions": [
            "ψ_L and ψ_R same-sign Bloch z — fails opposite_signs (chirality not present)",
            "flux_holonomy ≈ 0 — fails nonzero (U(1) connection trivial)",
            "G-stack layer list with no parent links — fails dependencies (geometry not nested)",
            "Hopf basis projection of |0⟩ not at north pole — fails carrier convention",
            "Clifford layer with only single-blade entries — fails nontrivial product (algebra unused)",
        ],
        "baseline_variants": [
            "trivial U(1) connection (winding=0) baseline — must produce flux=0 in graveyard",
            "ψ_L = ψ_R = |0⟩ baseline — must fail chirality opposite-sign",
        ],
    }
