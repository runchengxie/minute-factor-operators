import json
import unittest
from pathlib import Path


CATALOG = Path(__file__).parents[1] / "site/public/data/fundamental-factor-catalog.json"


class FundamentalFactorCatalogTests(unittest.TestCase):
    def test_catalog_has_eighteen_entries(self):
        catalog = json.loads(CATALOG.read_text())
        self.assertEqual(len(catalog["factors"]), 18)

    def test_catalog_marks_six_core_research_factors(self):
        catalog = json.loads(CATALOG.read_text())
        core = [factor for factor in catalog["factors"] if factor["priority"] == "core"]
        self.assertEqual(len(core), 6)
        self.assertIn("standardized_operating_profit", {factor["id"] for factor in core})

    def test_catalog_contains_research_safety_notes(self):
        catalog = json.loads(CATALOG.read_text())
        notes = " ".join(catalog["research_notes"])
        self.assertIn("point-in-time", notes)
        self.assertIn("operating_profit_ttm", notes)
        self.assertIn("TTM", notes)

    def test_local_pit_snapshot_is_real_and_representative(self):
        snapshot = json.loads((CATALOG.parent / "fundamental-snapshot.json").read_text())
        self.assertEqual(snapshot["source"], "local_pit_vintage")
        self.assertEqual(snapshot["vintage"], "20260802")
        self.assertGreaterEqual(len(snapshot["coverage"]["tickers"]), 3)
        self.assertTrue(any(item["metric"] == "standardized_operating_profit" for item in snapshot["series"]))


if __name__ == "__main__":
    unittest.main()
