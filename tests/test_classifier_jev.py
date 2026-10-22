import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parents[1] / ".agents/skills/decisions-for-coding/scripts"
sys.path.insert(0, str(SCRIPT_DIR))
import decisions_classifier


class JevBackendTests(unittest.TestCase):
    def invoke(self, request, response=None):
        stdout = io.StringIO()
        response_file = io.BytesIO(json.dumps(response or {}).encode())
        response_context = patch.object(decisions_classifier, "urlopen")
        with response_context as urlopen, patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-key"}), patch.object(
            sys, "stdin", io.StringIO(json.dumps(request)
        )), patch.object(sys, "stdout", stdout):
            urlopen.return_value.__enter__.return_value = response_file
            decisions_classifier.main()
        return json.loads(stdout.getvalue()), urlopen

    def test_choice_request_uses_typesafe_contract_and_normalizes_usage(self):
        result, urlopen = self.invoke(
            {
                "backend": "jev",
                "input": "A task",
                "question": "Classify the task",
                "type": "choice",
                "choices": [
                    {"value": "bugfix", "description": "Fix a defect"},
                    "feature",
                ],
            },
            {
                "model": "jev-latest",
                "answers": {
                    "decision": {
                        "type": "choice",
                        "choice": "bugfix",
                        "confidence": 0.9,
                        "probabilities": {"bugfix": 0.9, "feature": 0.1},
                    }
                },
                "usage": {"input_tokens": 10, "output_tokens": 2},
            },
        )

        http_request = urlopen.call_args.args[0]
        payload = json.loads(http_request.data)
        self.assertEqual(http_request.full_url, "https://api.typesafe.ai/v1/systemone")
        self.assertEqual(http_request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(payload["model"], "jev-latest")
        self.assertEqual(payload["state"], {"input": "A task"})
        self.assertEqual(payload["questions"]["decision"]["criteria"], {
            "bugfix": "Fix a defect", "feature": ""
        })
        self.assertEqual(result["answer"]["choice"], "bugfix")
        self.assertEqual(result["usage"]["input_tokens"], 10)

    def test_predicate_and_score_map_to_systemone_types(self):
        for kind, extra, expected_type in (
            ("predicate", {}, "noul"),
            ("score", {"levels": ["low", "high"]}, "score"),
        ):
            with self.subTest(kind=kind):
                request = {
                    "backend": "jev",
                    "input": "A task",
                    "question": "Evaluate it",
                    "type": kind,
                    **extra,
                }
                answer = {"type": "noul", "noul": 0.8} if kind == "predicate" else {
                    "type": "score",
                    "score": 0.8,
                    "confidence": 0.7,
                    "legend": {"0": "low", "1": "high"},
                    "probabilities": {"0": 0.2, "1": 0.8},
                }
                result, urlopen = self.invoke(request, {"answers": {"decision": answer}})
                payload = json.loads(urlopen.call_args.args[0].data)
                self.assertEqual(payload["questions"]["decision"]["type"], expected_type)
                if kind == "predicate":
                    self.assertEqual(result["answer"]["probability"], 0.8)
                else:
                    self.assertEqual(result["answer"]["score"], 0.8)

    def test_missing_key_returns_json_error_without_request(self):
        request = {
            "backend": "jev",
            "input": "A task",
            "question": "Classify it",
            "type": "choice",
            "choices": ["bugfix", "feature"],
        }
        stdout = io.StringIO()
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": ""}), patch.object(
            sys, "stdin", io.StringIO(json.dumps(request))
        ), patch.object(sys, "stdout", stdout), patch.object(decisions_classifier, "urlopen") as urlopen:
            with self.assertRaises(SystemExit) as raised:
                decisions_classifier.main()

        self.assertEqual(raised.exception.code, 1)
        self.assertIn("TYPESAFE_API_KEY", json.loads(stdout.getvalue())["error"])
        urlopen.assert_not_called()

    def test_provider_failure_returns_json_error_without_fallback(self):
        request = {
            "backend": "jev",
            "input": "A task",
            "question": "Classify it",
            "type": "choice",
            "choices": ["bugfix", "feature"],
        }
        stdout = io.StringIO()
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-key"}), patch.object(
            sys, "stdin", io.StringIO(json.dumps(request))
        ), patch.object(sys, "stdout", stdout), patch.object(
            decisions_classifier, "urlopen", side_effect=OSError("connection refused")
        ) as urlopen:
            with self.assertRaises(SystemExit) as raised:
                decisions_classifier.main()

        self.assertEqual(raised.exception.code, 1)
        self.assertIn("Jev Decisions API error", json.loads(stdout.getvalue())["error"])
        urlopen.assert_called_once()


if __name__ == "__main__":
    unittest.main()
