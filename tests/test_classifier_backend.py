import json
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / ".agents/skills/decisions-for-coding/scripts/decisions_classifier.py"


class BackendSelectionTests(unittest.TestCase):
    def test_backend_is_required_before_any_provider_call(self):
        request = {
            "input": "A task description",
            "question": "Classify the task",
            "type": "choice",
            "choices": ["feature", "bugfix"],
        }
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("explicitly set", json.loads(result.stdout)["error"])
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
