# Host hook adapter

This shim relays a host hook payload to the thin ConstraintBox hook adapter.
The hook can strip authority from unmanaged LLM launches and record the event;
it does not run semantic gates or decide whether model output is good.

```text
CB_LIGHT_PYTHON=/path/to/light/python hooks/cb_hook.sh codex
```

Cancellation or hook exit never becomes PASS. A bypassed host action has no CB
receipt and therefore no authority inside the system.

Host configuration/trust/restart remains host-specific. The portable shim is
not proof that a particular host loaded it.

`claude/` contains a self-contained project-hook profile for a fresh bundle.
It deliberately excludes the old external session boot and binds only the
current CB Light pre-install, post-tool, and session-start lifecycle hooks.
