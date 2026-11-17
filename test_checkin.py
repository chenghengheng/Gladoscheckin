"""Offline regression tests for the GLaDOS challenge handshake."""
import hashlib
import unittest
from unittest.mock import Mock, patch

from checkin import API, CheckinStatus


class CheckinChallengeTests(unittest.TestCase):
    def setUp(self):
        self.api = API("glados.cloud")
        self.addCleanup(self.api.close)

    def test_nonce_proof_and_delay(self):
        challenge_response = Mock()
        challenge_response.json.return_value = {"code": 0, "nonce": "example-nonce"}
        with patch.object(self.api, "_make_request", return_value=challenge_response) as request, \
             patch("checkin.time.sleep") as sleep:
            payload = self.api._get_checkin_data("fake-cookie")
        self.assertEqual(payload["token"], "glados.cloud")
        self.assertEqual(payload["nonce"], "example-nonce")
        self.assertEqual(payload["proof"], hashlib.sha256(b"example-nonce.glados-observe-v1").hexdigest())
        sleep.assert_called_once_with(2.5)
        request.assert_called_once_with(
            "https://glados.cloud/api/user/checkin/challenge", "GET", cookies="fake-cookie"
        )

    def test_challenge_unavailable_falls_back(self):
        with patch.object(self.api, "_make_request", return_value=None), \
             patch("checkin.time.sleep") as sleep:
            payload = self.api._get_checkin_data("fake-cookie")
        self.assertEqual(payload, {"token": "glados.cloud"})
        sleep.assert_not_called()

    def test_cloudflare_code_five_is_failure(self):
        challenge_response = Mock()
        challenge_response.json.return_value = {"code": 0, "nonce": "x"}
        checkin_response = Mock()
        checkin_response.json.return_value = {
            "code": 5, "message": "Cloudflare verification failed. Nothing was recorded — please retry."
        }
        with patch.object(self.api, "_make_request", side_effect=[challenge_response, checkin_response]), \
             patch("checkin.time.sleep"):
            result = self.api.checkin("fake-cookie")
        self.assertEqual(result["code"], CheckinStatus.FAILURE)
        self.assertEqual(result["status"], "Cloudflare 验证失败")

    def test_challenge_diagnostics_do_not_expose_secrets(self):
        self.api.verbose = True
        challenge_response = Mock()
        challenge_response.json.return_value = {"code": 0, "nonce": "private-nonce"}
        with patch.object(self.api, "_make_request", return_value=challenge_response), \
             patch.object(self.api, "_log") as write_log, \
             patch("checkin.time.sleep"):
            result = self.api._get_checkin_data("private-cookie")
        messages = " ".join(str(call.args[2]) for call in write_log.call_args_list)
        self.assertIn("code=0", messages)
        self.assertIn("nonce_present=True", messages)
        self.assertNotIn("private-cookie", messages)
        self.assertNotIn("private-nonce", messages)
        self.assertNotIn(result["proof"], messages)

    def test_code_five_reports_whether_challenge_was_submitted(self):
        challenge_response = Mock()
        challenge_response.json.return_value = {"code": 0, "nonce": "private-nonce"}
        checkin_response = Mock()
        checkin_response.json.return_value = {
            "code": 5, "message": "Cloudflare verification failed. Nothing was recorded — please retry."
        }
        with patch.object(self.api, "_make_request", side_effect=[challenge_response, checkin_response]), \
             patch.object(self.api, "_log") as write_log, \
             patch("checkin.time.sleep"):
            result = self.api.checkin("private-cookie")
        messages = " ".join(str(call.args[2]) for call in write_log.call_args_list)
        self.assertIn("已提交 challenge proof=True", messages)
        self.assertNotIn("private-cookie", messages)
        self.assertNotIn("private-nonce", messages)
        self.assertEqual(result["code"], CheckinStatus.FAILURE)

    def test_domain_mismatch_is_not_false_success(self):
        challenge_response = Mock()
        challenge_response.json.return_value = {"code": 0, "nonce": "x"}
        checkin_response = Mock()
        checkin_response.json.return_value = {"code": 0, "message": "Please checkin via https://railgun.info"}
        with patch.object(self.api, "_make_request", side_effect=[challenge_response, checkin_response]), \
             patch("checkin.time.sleep"):
            result = self.api.checkin("fake-cookie")
        self.assertEqual(result["code"], CheckinStatus.FAILURE)

    def test_invalid_json_does_not_crash(self):
        challenge_response = Mock()
        challenge_response.json.side_effect = ValueError("invalid JSON")
        checkin_response = Mock()
        checkin_response.json.side_effect = ValueError("invalid JSON")
        with patch.object(self.api, "_make_request", side_effect=[challenge_response, checkin_response]):
            result = self.api.checkin("fake-cookie")
        self.assertEqual(result["code"], CheckinStatus.FAILURE)


if __name__ == "__main__":
    unittest.main()
