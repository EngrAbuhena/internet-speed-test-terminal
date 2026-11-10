"""Offline unit tests for the speed-test CLI."""

import importlib.util
import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import TestCase, mock

SCRIPT = Path(__file__).resolve().parents[1] / "internet_speed_test_v1.0.0.py"
spec = importlib.util.spec_from_file_location("internet_speed_test", SCRIPT)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class RatingTests(TestCase):
    def test_overall_requires_both_thresholds(self):
        self.assertEqual(app.quality_rating(100, 20)[0], "EXCELLENT")
        self.assertEqual(app.quality_rating(100, 4)[0], "NEUTRAL")
        self.assertEqual(app.quality_rating(4, 100)[0], "WORST")

    def test_individual_rating_boundaries(self):
        thresholds = (100, 20, 10, 5)
        for speed, label in [(100, "EXCELLENT"), (20, "GOOD"),
                             (10, "NEUTRAL"), (5, "BAD"), (4.99, "WORST")]:
            with self.subTest(speed=speed):
                self.assertEqual(app.individual_rating(speed, *thresholds)[0], label)

    def test_bar_is_bounded(self):
        self.assertEqual(app.bar(-1, 100, 4), "░" * 4)
        self.assertEqual(app.bar(200, 100, 4), "█" * 4)
        self.assertEqual(app.bar(50, 100, 4), "██░░")
        self.assertEqual(app.bar(10, 0, 4), "░" * 4)

    def test_stats_rows(self):
        rows = app.stats_rows("DOWNLOAD", [10, 20, 30], 100, "green")
        self.assertTrue(any("20.00 Mbps" in text for text, _ in rows))


class MainTests(TestCase):
    def test_main_with_fake_measurements(self):
        tester = mock.MagicMock()
        tester.get_best_server.return_value = {
            "sponsor": "Example", "name": "Test City", "country": "Test Country"
        }
        tester.results.ping = 12.5
        tester.download.side_effect = [100_000_000, 110_000_000, 120_000_000]
        tester.upload.side_effect = [20_000_000, 22_000_000, 24_000_000]
        output = io.StringIO()
        with mock.patch.object(app.speedtest, "Speedtest", return_value=tester), redirect_stdout(output):
            result = app.main()
        self.assertEqual(result, 0)
        self.assertEqual(tester.download.call_count, 3)
        self.assertEqual(tester.upload.call_count, 3)
        self.assertIn("OVERALL RATING:   EXCELLENT", output.getvalue())
        self.assertIn("110.00 Mbps", output.getvalue())

    def test_rejects_zero_tests(self):
        with mock.patch.object(app, "NUM_TESTS", 0), redirect_stderr(io.StringIO()) as err:
            self.assertEqual(app.main(), 1)
        self.assertIn("at least 1", err.getvalue())

    def test_speedtest_error_returns_failure(self):
        with mock.patch.object(app.speedtest, "Speedtest", side_effect=app.speedtest.SpeedtestException("offline")):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                result = app.main()
        self.assertEqual(result, 1)
        self.assertIn("Speed test failed", err.getvalue())
