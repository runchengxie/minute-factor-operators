import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from scripts.build_factor_snapshot import build_snapshot


class SnapshotBuilderTests(unittest.TestCase):
    def test_demo_snapshot_has_required_contract(self):
        output = Path(self.id().replace(".", "_") + ".json")
        try:
            result = build_snapshot(None, output, demo=True)
            self.assertEqual(result["source"], "demo")
            self.assertTrue(
                {
                    "generated_at", "datasets", "factor_groups", "factors",
                    "series", "cross_section", "jump_decomposition",
                } <= result.keys()
            )
        finally:
            output.unlink(missing_ok=True)

    def test_demo_snapshot_has_six_digit_tickers_and_finite_values(self):
        output = Path(self.id().replace(".", "_") + ".json")
        try:
            result = build_snapshot(None, output, demo=True)
            self.assertTrue(all(len(row["ticker"]) == 6 for row in result["series"]))
            self.assertTrue(all(
                value is None or math.isfinite(value)
                for row in result["series"] for value in row["values"]
            ))
        finally:
            output.unlink(missing_ok=True)

    def test_jump_decomposition_preserves_residual_relation(self):
        output = Path(self.id().replace(".", "_") + ".json")
        try:
            jump = build_snapshot(None, output, demo=True)["jump_decomposition"][0]
            self.assertAlmostEqual(jump["rjv"], jump["rljv"] + jump["rsjv"])
        finally:
            output.unlink(missing_ok=True)

    def test_snapshot_is_written_as_json(self):
        output = Path(self.id().replace(".", "_") + ".json")
        try:
            build_snapshot(None, output, demo=True)
            self.assertEqual(json.loads(output.read_text())["source"], "demo")
        finally:
            output.unlink(missing_ok=True)

    def test_missing_real_input_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            build_snapshot(Path("missing-factor-results"), Path("unused.json"), demo=False)
