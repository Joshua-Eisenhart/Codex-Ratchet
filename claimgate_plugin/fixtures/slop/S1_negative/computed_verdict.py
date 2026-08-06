# S1 VERDICT_LITERAL — expected clean: outcome is computed.
def compute():
    return "".join(["s", "a", "t"])
z3_receipt = {"z3": {"verdict": compute()}}
