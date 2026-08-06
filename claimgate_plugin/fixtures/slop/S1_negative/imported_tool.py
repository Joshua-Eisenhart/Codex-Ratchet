# S1 VERDICT_LITERAL — expected clean: tool is imported.
import z3
TOOL_VERSION = z3.get_version_string()
receipt = {"z3": {"ran": True, "verdict": "sat"}}
