from __future__ import annotations

import unittest

from constraintbox.advisory_fanout import AdvisoryFanoutError, run_advisory_fanout


class AdvisoryFanoutTests(unittest.TestCase):
    def test_collects_routes_concurrently_without_creating_authority(self) -> None:
        seen: list[str] = []

        def runner(provider, decision, **_kwargs):
            seen.append(provider)
            return {"provider_state": "ADVICE_ACCEPTED", "provider": provider}

        result = run_advisory_fanout(["nvidia", "openrouter"], {"fixed": True}, runner=runner)
        self.assertEqual(result["state"], "COMPLETE")
        self.assertEqual(result["accepted_routes"], ["nvidia", "openrouter"])
        self.assertEqual({row["provider"] for row in result["provider_receipts"]}, set(seen))
        self.assertFalse(result["decision_authority"])
        self.assertFalse(result["release_allowed"])
        self.assertFalse(result["promotion_allowed"])

    def test_rejects_single_or_duplicate_route_sets(self) -> None:
        with self.assertRaises(AdvisoryFanoutError):
            run_advisory_fanout(["nvidia"], {})
        with self.assertRaises(AdvisoryFanoutError):
            run_advisory_fanout(["nvidia", "nvidia"], {})


if __name__ == "__main__":
    unittest.main()
