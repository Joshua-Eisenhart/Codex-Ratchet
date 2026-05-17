"""phase_26_unified_ai_tool_surface.py — single callable entry point for all primitives.

The architecture's ~13 primitives become AI-callable via a single dispatch function.
This is the "massive new tool set" framing: AI calls one function, picks a primitive
by name, gets back structured output.

Required API: `ai_tool_surface(tool: str, **kwargs) -> dict`
  Returns:
    {
      "tool": str,
      "available_tools": list[str],            # documented surface (for introspection)
      "result": dict,                          # primitive-specific output
      "error": str | None,
    }

Supported tools (must include at least these):
  - "szilard": calls extract_szilard_work; kwargs: p_bit
  - "axis_transform": calls axis_transform; kwargs: axis_index, input_rho_qt
  - "terrain": calls terrain_operation; kwargs: terrain, input_rho_qt, strength
  - "fisher": calls fisher_information_matrix; kwargs: theta_perturbation
  - "hexagram": calls stage_to_hexagram; kwargs: stage_index, engine
  - "compress": calls probe_quotient_compress; kwargs: input_rho_qt
  - "holonomic": calls holonomic_gate; kwargs: loop_angle
  - "dfs": calls decoherence_free_subspace; kwargs: noise_terrain
  - "petz": calls petz_recover; kwargs: channel_terrain, post_noise_rho_qt
  - "list": returns available_tools, no other action

Tests:
  - Function exists
  - "list" call returns ≥9 tools
  - Each tool dispatches to a working primitive without error
  - Unknown tool returns error field set to non-None
"""


REQUIRED_TOOLS = {
    "szilard": {"p_bit": 0.5},
    "axis_transform": {"axis_index": 3},   # input_rho_qt added separately
    "terrain": {"terrain": "Fi", "strength": 0.4},
    "fisher": {"theta_perturbation": 0.01},
    "hexagram": {"stage_index": 5, "engine": "A"},
    "compress": {},
    "holonomic": {"loop_angle": 1.5708},  # π/2
    "dfs": {"noise_terrain": "Ti"},
    "petz": {"channel_terrain": "Te"},
}


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "ai_tool_surface"):
        return {
            "pass": False,
            "failures": [{
                "check": "ai_tool_surface_exists",
                "msg": "Required function `ai_tool_surface(tool: str, **kwargs) -> dict` not exported. "
                       "Unified entry point for all architecture primitives. Should dispatch to: "
                       "szilard, axis_transform, terrain, fisher, hexagram, compress, holonomic, dfs, "
                       "petz, list. Returns {tool, available_tools (list), result (dict), error (str|None)}.",
            }],
            "metrics": metrics,
        }

    # 'list' call
    try:
        list_r = candidate.ai_tool_surface("list")
    except Exception as e:
        return {"pass": False,
                "failures": [{"check": "ai_tool_surface_list", "msg": str(e)[:200]}],
                "metrics": metrics}

    if not isinstance(list_r, dict):
        return {"pass": False,
                "failures": [{"check": "list_returns_dict", "msg": f"got {type(list_r).__name__}"}],
                "metrics": metrics}

    available = list_r.get("available_tools", [])
    metrics["available_tools"] = available
    metrics["available_count"] = len(available)
    if len(available) < 9:
        failures.append({
            "check": "available_tools_count",
            "msg": f"available_tools = {available}; needs ≥9 primitives covering "
                   f"{list(REQUIRED_TOOLS.keys())}",
        })
    for tool_name in REQUIRED_TOOLS:
        if tool_name not in available:
            failures.append({
                "check": f"tool_in_surface_{tool_name}",
                "msg": f"`{tool_name}` not in available_tools = {available}",
            })

    # Set up a reference state for tools that need it
    import qutip as qt
    psi_ref = qt.tensor(
        (qt.basis(2, 0) + 0.5 * qt.basis(2, 1)).unit(),
        qt.basis(2, 0), qt.basis(2, 0), qt.basis(2, 0))
    rho_ref = qt.ket2dm(psi_ref)

    # For petz we need a noisy state — build it from terrain_operation
    if hasattr(candidate, "terrain_operation"):
        try:
            noisy = candidate.terrain_operation("Te", rho_ref, 0.5)["output_rho_qt"]
        except Exception:
            noisy = rho_ref
    else:
        noisy = rho_ref

    state_kwargs = {
        "axis_transform": {"input_rho_qt": rho_ref},
        "terrain": {"input_rho_qt": rho_ref},
        "compress": {"input_rho_qt": rho_ref},
        "petz": {"post_noise_rho_qt": noisy},
    }

    # Dispatch each tool
    dispatched_ok = []
    for tool_name, kw in REQUIRED_TOOLS.items():
        full_kw = dict(kw)
        full_kw.update(state_kwargs.get(tool_name, {}))
        try:
            r = candidate.ai_tool_surface(tool_name, **full_kw)
        except Exception as e:
            failures.append({
                "check": f"dispatch_{tool_name}",
                "msg": f"ai_tool_surface('{tool_name}', ...) raised {type(e).__name__}: {str(e)[:200]}",
            })
            continue
        if not isinstance(r, dict):
            failures.append({"check": f"dispatch_dict_{tool_name}", "msg": f"got {type(r).__name__}"})
            continue
        if r.get("error") is not None:
            failures.append({
                "check": f"dispatch_no_error_{tool_name}",
                "msg": f"`{tool_name}` returned error: {r['error']}",
            })
            continue
        if r.get("result") is None:
            failures.append({"check": f"dispatch_result_{tool_name}", "msg": "result is None"})
            continue
        dispatched_ok.append(tool_name)

    metrics["dispatched_ok"] = dispatched_ok
    metrics["dispatched_ok_count"] = len(dispatched_ok)

    # Unknown tool: error should be set
    try:
        r = candidate.ai_tool_surface("nonexistent_tool_xyz")
        if r.get("error") is None:
            failures.append({
                "check": "unknown_tool_error",
                "msg": "ai_tool_surface('nonexistent_tool_xyz') returned error=None; should signal error",
            })
    except Exception:
        # OK to raise too
        pass

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "ai_tool_surface returns identity (just echoes kwargs) — dispatch fails",
            "unknown tool not flagged — fails error reporting",
            "available_tools list missing entries — fails per-tool checks",
        ],
        "baseline_variants": [
            "stub baseline returning {error: 'not implemented'} for all tools — fails dispatch_no_error",
        ],
    }
