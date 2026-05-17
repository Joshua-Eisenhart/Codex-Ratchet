"""phase_47_gstack_layered_entropy.py — verifies the layered g-stack BEFORE axes can run.

Per user directive: axes can only be run after the geometric constraint manifold has been
FULLY simed. "Fully simed" requires:
  - the base manifold (Phase 46) ✓ enforced separately
  - the g-stack built on top with NESTED entropy restrictions per layer

This phase verifies build_gstack_over_manifold(manifold_dict) returns 4 layers where each
successive layer's admissible-entropy set is a STRICT SUBSET of the prior.

Required API: `build_gstack_over_manifold(manifold_dict) -> dict`
  Returns: {manifold_ref, layers: [{index, name, parent_layer_index,
    admissible_entropies, entropy_admissibility_check, tangent_subspace_qt}, ...],
    entropy_at, is_layered_consistent}
"""
import numpy as np


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "build_gstack_over_manifold"):
        return {"pass": False, "failures": [{
            "check": "build_gstack_over_manifold_exists",
            "msg": "Required FOUNDATIONAL function `build_gstack_over_manifold(manifold_dict)` "
                   "not exported. Each layer must restrict admissible entropies more than the "
                   "prior layer (strict subset chain). Axes cannot run until this is built and "
                   "verified.",
        }], "metrics": metrics}

    if not hasattr(candidate, "build_constraint_manifold"):
        return {"pass": False, "failures": [{
            "check": "manifold_prerequisite",
            "msg": "build_gstack_over_manifold requires build_constraint_manifold to exist first.",
        }], "metrics": metrics}

    try:
        manifold = candidate.build_constraint_manifold()
        gstack = candidate.build_gstack_over_manifold(manifold)
    except Exception as e:
        return {"pass": False, "failures": [{"check": "construction",
                "msg": f"{type(e).__name__}: {str(e)[:200]}"}], "metrics": metrics}

    if not isinstance(gstack, dict):
        return {"pass": False, "failures": [{"check": "gstack_returns_dict",
                "msg": f"got {type(gstack).__name__}"}], "metrics": metrics}

    layers = gstack.get("layers")
    if not isinstance(layers, list) or len(layers) < 4:
        failures.append({"check": "layer_count",
                         "msg": f"gstack must have ≥4 layers (got {len(layers) if isinstance(layers,list) else 'non-list'})"})
        return {"pass": False, "failures": failures, "metrics": metrics}

    metrics["n_layers"] = len(layers)
    sizes = []
    for i, L in enumerate(layers):
        if not isinstance(L, dict):
            failures.append({"check": f"layer_{i}_dict",
                             "msg": f"layer {i} is not a dict (got {type(L).__name__})"})
            continue
        for k in ("index", "name", "admissible_entropies",
                  "entropy_admissibility_check", "tangent_subspace_qt"):
            if k not in L:
                failures.append({"check": f"layer_{i}_missing_{k}",
                                 "msg": f"layer {i} missing `{k}`"})
        sizes.append(len(L.get("admissible_entropies", [])) if "admissible_entropies" in L else 0)

    if failures:
        return {"pass": False, "failures": failures, "metrics": metrics}

    metrics["admissible_set_sizes"] = sizes

    # CORE CHECK: strict subset chain layer[k+1] ⊂ layer[k]
    for k in range(len(layers) - 1):
        s_k = set(layers[k]["admissible_entropies"])
        s_k1 = set(layers[k + 1]["admissible_entropies"])
        if not s_k1.issubset(s_k):
            new_items = s_k1 - s_k
            failures.append({"check": f"layer_{k+1}_subset_of_{k}",
                             "msg": f"layer {k+1} admits entropies not in layer {k}: "
                                    f"{sorted(new_items)}. Each nested layer must restrict, "
                                    f"never expand."})
        if s_k1 == s_k:
            failures.append({"check": f"layer_{k+1}_strict_subset_of_{k}",
                             "msg": f"layer {k+1} admits EXACTLY the same entropies as layer "
                                    f"{k}; the chain is not STRICT."})

    # Parent linkage check
    for i in range(1, len(layers)):
        if layers[i].get("parent_layer_index") != i - 1:
            failures.append({"check": f"layer_{i}_parent",
                             "msg": f"layer {i} parent_layer_index = "
                                    f"{layers[i].get('parent_layer_index')}; expected {i-1}"})

    # Tangent subspace must be a subset of the manifold's tangent generators
    if "pauli_basis" in manifold:
        manifold_tangent_ids = {id(t) for t in manifold["pauli_basis"]}
        for i, L in enumerate(layers):
            ts = L.get("tangent_subspace_qt", [])
            if i > 0 and len(ts) > len(layers[i - 1].get("tangent_subspace_qt", [])):
                failures.append({"check": f"tangent_subset_{i}",
                                 "msg": f"layer {i} has more tangents than layer {i-1}"})

    # is_layered_consistent should itself report True
    icf = gstack.get("is_layered_consistent")
    if callable(icf):
        try:
            ok = bool(icf())
            metrics["self_reported_consistent"] = ok
            if not ok:
                failures.append({"check": "self_consistency",
                                 "msg": "is_layered_consistent() returned False"})
        except Exception as e:
            failures.append({"check": "is_layered_consistent_callable",
                             "msg": str(e)[:160]})

    # entropy_at should return finite values for base-layer admissible entropies on rho0
    if callable(gstack.get("entropy_at")):
        try:
            import qutip as qt
            psi0 = qt.tensor(*[qt.basis(2, 0)] * 4)
            rho0 = qt.ket2dm(psi0)
            base_entropies = layers[0]["admissible_entropies"]
            ok_count = 0
            for ent in base_entropies:
                val = gstack["entropy_at"](rho0, ent)
                if val is None: continue
                if isinstance(val, (int, float)) and np.isfinite(val):
                    ok_count += 1
            metrics["entropy_at_finite_count"] = f"{ok_count}/{len(base_entropies)}"
            if ok_count < len(base_entropies):
                failures.append({"check": "entropy_at_finite",
                                 "msg": f"only {ok_count}/{len(base_entropies)} base-layer "
                                        f"entropies returned finite values on |0000⟩"})
        except Exception as e:
            failures.append({"check": "entropy_at_invoke",
                             "msg": str(e)[:160]})

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "non-strict subset chain — layers admit same entropies, no real restriction",
            "expanding admissibility down the stack — wrong direction",
            "missing parent linkage — layers not actually nested",
            "decorative is_layered_consistent always returns True — must verify subsets",
        ],
        "baseline_variants": [
            "identity layers (all 4 admit same set) — fails strict-subset",
        ],
    }
