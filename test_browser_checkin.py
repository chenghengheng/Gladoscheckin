"""Offline unit tests; no browser and no GLaDOS account are required."""
import json
import tempfile
import unittest
from pathlib import Path

from browser_checkin import classify_result, has_completed, is_checkin_response, remember_completed


class BrowserCheckinTests(unittest.TestCase):
    def test_endpoint_filter(self):
        self.assertTrue(is_checkin_response("https://glados.cloud/api/user/checkin", "POST"))
        self.assertFalse(is_checkin_response("https://glados.cloud/api/user/checkin/challenge", "GET"))
        self.assertFalse(is_checkin_response("https://evil.example/api/user/checkin", "POST"))
        self.assertFalse(is_checkin_response("https://glados.cloud/api/user/checkin", "GET"))

    def test_result_classification(self):
        self.assertEqual(classify_result({"code": 0, "message": "Checkin! Got 5"}), "success")
        self.assertEqual(classify_result({"code": 1, "message": "Today's observation logged."}), "repeat")
        self.assertEqual(classify_result({"code": 5, "message": "Cloudflare verification failed"}), "cloudflare")
        self.assertEqual(classify_result({"code": 0, "message": "Please checkin via another site"}), "failure")
        self.assertEqual(classify_result({"code": "oops"}), "failure")
        self.assertEqual(classify_result(None), "failure")

    def test_completion_marker_is_local_and_minimal(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private" / "completed.json"
            self.assertFalse(has_completed("2026-11-17", path))
            remember_completed("2026-11-17", "repeat", path)
            self.assertTrue(has_completed("2026-11-17", path))
            self.assertFalse(has_completed("2026-11-18", path))
            self.assertEqual(json.loads(path.read_text()), {"date": "2026-11-17", "result": "repeat"})


if __name__ == "__main__":
    unittest.main()
