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

    def test_fundamental_snapshot_records_all_market_validation(self):
        snapshot = json.loads((CATALOG.parent / "fundamental-snapshot.json").read_text())
        self.assertTrue(snapshot["validation"]["all_market_computed"])
        self.assertGreater(snapshot["coverage"]["tickers_count"], len(snapshot["coverage"]["representative_tickers"]))
        self.assertEqual(snapshot["validation"]["historical_ttm_window"], 6)

    def test_fundamental_snapshot_keeps_pit_dates_and_null_warmup(self):
        snapshot = json.loads((CATALOG.parent / "fundamental-snapshot.json").read_text())
        series = snapshot["series"][0]
        self.assertEqual(len(series["dates"][0]), 10)
        self.assertIn(None, series["values"])


if __name__ == "__main__":
    unittest.main()
