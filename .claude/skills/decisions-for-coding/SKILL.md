---
name: decisions-for-coding
description: Evaluate coding decisions with the OpenAI Decisions API. Use when Codex needs a structured choice, predicate, or score before choosing an implementation approach.
---

# Decisions for coding

Use the classifier packaged in `.agents/skills/decisions-for-coding/scripts/decisions_classifier.py` to evaluate a coding decision, then use the JSON result to choose the smallest appropriate engineering workflow. The result is advisory: inspect the code and requirements before making the final decision.

## Workflow

1. Build a JSON request with `input`, `question`, and `type`. Add `choices` for `choice` or `levels` for `score`.
2. If `OPENAI_API_KEY` is not available, continue with a local engineering judgment and say that the API classification was skipped.
3. From the repository root, send the request through standard input and run the shared classifier with the Codex skill's virtual-environment interpreter:

   ```bash
   printf '%s' '<JSON request>' | .agents/skills/decisions-for-coding/.venv/bin/python .agents/skills/decisions-for-coding/scripts/decisions_classifier.py
   ```

4. Parse the JSON response from standard output and use the result as a routing hint:
   - `feature`: inspect callers, interfaces, tests, and configuration before implementing.
   - `bugfix`: reproduce or isolate the failure, then fix the shared root cause.
   - `refactor`: preserve behavior and run focused regression tests.
   - `test`: add the smallest test that proves the requested behavior.
   - `security`: treat inputs as untrusted and inspect exposure, authorization, and logging.
   - `docs`: update only documentation affected by the current behavior.
5. Report the decision and confidence when provided, then proceed only within the user's requested scope.

Do not use this skill for arbitrary product, legal, medical, or financial decisions. Do not send source code, credentials, tokens, or personal data to the API. The API call costs tokens and may fail; a failed classification must not block ordinary coding work.

Install the dependency from `.agents/skills/decisions-for-coding/requirements.txt` into that skill's virtual environment. This Claude Code mirror is for use when the repository is cloned; the self-contained distributable bundle is `.agents/skills/decisions-for-coding/`.
