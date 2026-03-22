#!/usr/bin/env python3
"""
egglog_graph_rewrite_probe.py
─────────────────────────────
Reusable probe: models graph-node tier promotion as egglog rewrite rules.

Takes a set of nodes with support counts, runs equality-saturation to
derive all valid promotions (CANDIDATE → PROPOSED → KERNEL), and returns
a dict of {node_name: final_tier_str}.

Usage:
    python egglog_graph_rewrite_probe.py           # runs self-test
    from egglog_graph_rewrite_probe import run_promotion_probe
"""
from __future__ import annotations

from egglog import (
    EGraph,
    Expr,
    String,
    StringLike,
    i64,
    i64Like,
    relation,
    rule,
    union,
    var,
)


# ── Sort definitions ──────────────────────────────────────────────────

class Tier(Expr):
    """Promotion tier: CANDIDATE → PROPOSED → KERNEL."""

    @classmethod
    def CANDIDATE(cls) -> "Tier": ...

    @classmethod
    def PROPOSED(cls) -> "Tier": ...

    @classmethod
    def KERNEL(cls) -> "Tier": ...


class GNode(Expr):
    """A graph node with a name and a tier."""

    def __init__(self, name: StringLike, tier: Tier) -> None: ...


class Support(Expr):
    """Records that a node has N supporting edges."""

    def __init__(self, node: GNode, count: i64Like) -> None: ...


# ── Relations ─────────────────────────────────────────────────────────

promoted = relation("promoted", GNode)


# ── Promotion rules ──────────────────────────────────────────────────

def _build_rules(
    proposed_threshold: int = 2,
    kernel_threshold: int = 4,
):
    """Return the two promotion rules with configurable thresholds."""

    promote_to_proposed = rule(
        GNode(var("name", String), Tier.CANDIDATE()),
        Support(
            GNode(var("name", String), Tier.CANDIDATE()),
            var("n", i64),
        ),
        var("n", i64) >= i64(proposed_threshold),
    ).then(
        union(GNode(var("name", String), Tier.CANDIDATE())).with_(
            GNode(var("name", String), Tier.PROPOSED())
        ),
        promoted(GNode(var("name", String), Tier.PROPOSED())),
    )

    promote_to_kernel = rule(
        GNode(var("name", String), Tier.PROPOSED()),
        Support(
            GNode(var("name", String), Tier.PROPOSED()),
            var("n", i64),
        ),
        var("n", i64) >= i64(kernel_threshold),
    ).then(
        union(GNode(var("name", String), Tier.PROPOSED())).with_(
            GNode(var("name", String), Tier.KERNEL())
        ),
        promoted(GNode(var("name", String), Tier.KERNEL())),
    )

    return promote_to_proposed, promote_to_kernel


# ── Public API ────────────────────────────────────────────────────────

def run_promotion_probe(
    nodes_with_support: dict[str, dict[str, int]],
    proposed_threshold: int = 2,
    kernel_threshold: int = 4,
    max_iterations: int = 20,
) -> dict[str, str]:
    """
    Run the tier-promotion probe.

    Args:
        nodes_with_support: Mapping of node_name → {tier_level: support_count}.
            Example: {"alpha": {"CANDIDATE": 3, "PROPOSED": 5}, "beta": {"CANDIDATE": 1}}
        proposed_threshold: Minimum support to promote CANDIDATE → PROPOSED.
        kernel_threshold:   Minimum support to promote PROPOSED → KERNEL.
        max_iterations:     Max e-graph saturation iterations.

    Returns:
        Dict of {node_name: highest_promoted_tier} for nodes that were promoted.
        Nodes not promoted are omitted.
    """
    tier_map = {
        "CANDIDATE": Tier.CANDIDATE,
        "PROPOSED": Tier.PROPOSED,
        "KERNEL": Tier.KERNEL,
    }

    rules = _build_rules(proposed_threshold, kernel_threshold)
    egraph = EGraph()

    # Register nodes and support facts
    node_refs = {}
    for name, supports in nodes_with_support.items():
        for tier_name, count in supports.items():
            tier_fn = tier_map[tier_name]
            gnode = GNode(name, tier_fn())
            if name not in node_refs:
                node_refs[name] = egraph.let(name, gnode)
            else:
                egraph.register(gnode)
            egraph.register(Support(gnode, i64(count)))

    # Register rules and run
    egraph.register(*rules)
    egraph.run(max_iterations)

    # Check which promotions occurred
    results = {}
    # Check in reverse priority order so highest tier wins
    for tier_name in ["PROPOSED", "KERNEL"]:
        tier_fn = tier_map[tier_name]
        for name in nodes_with_support:
            try:
                egraph.check(promoted(GNode(name, tier_fn())))
                results[name] = tier_name
            except Exception:
                pass

    return results


# ── Self-test ─────────────────────────────────────────────────────────

def _self_test():
    """Run the probe against known inputs and validate results."""
    print("=" * 60)
    print("egglog graph rewrite probe — self-test")
    print("=" * 60)

    test_data = {
        # alpha: qualifies at both tiers → KERNEL
        "alpha": {"CANDIDATE": 3, "PROPOSED": 5},
        # beta: below threshold → stays CANDIDATE
        "beta": {"CANDIDATE": 1},
        # gamma: support=2 qualifies for PROPOSED only (< kernel_threshold=4)
        "gamma": {"CANDIDATE": 2},
        # delta: support=5 cascades through both tiers → KERNEL
        "delta": {"CANDIDATE": 5},
    }

    results = run_promotion_probe(
        test_data,
        proposed_threshold=2,
        kernel_threshold=4,
    )

    print(f"\nInput:   {test_data}")
    print(f"Results: {results}")

    # Assertions
    assert results.get("alpha") == "KERNEL", (
        f"alpha should be KERNEL, got {results.get('alpha')}"
    )
    assert results.get("gamma") == "PROPOSED", (
        f"gamma should be PROPOSED, got {results.get('gamma')}"
    )
    assert results.get("delta") == "KERNEL", (
        f"delta should be KERNEL, got {results.get('delta')}"
    )
    assert "beta" not in results, (
        f"beta should NOT be promoted, got {results.get('beta')}"
    )

    print("\n✅ All assertions passed.")
    print("=" * 60)


if __name__ == "__main__":
    _self_test()
