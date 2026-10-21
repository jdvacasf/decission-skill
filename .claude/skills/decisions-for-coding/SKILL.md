---
name: decisions-for-coding
description: Evaluate coding decisions with OpenAI Decisions API or local Ollama. Use when Claude Code needs a structured choice, predicate, or score before choosing an implementation approach.
---

# Decisions for coding

Use the classifier packaged in `.agents/skills/decisions-for-coding/scripts/decisions_classifier.py` to evaluate a coding decision, then use the JSON result to choose the smallest appropriate engineering workflow. The result is advisory: inspect the code and requirements before making the final decision. OpenAI is the default backend; use Ollama when local inference is preferred.

## Workflow

1. Build a JSON request with `input`, `question`, and `type`. Add `choices` for `choice` or `levels` for `score`.
2. Choose `backend`: use `openai` (default) when `OPENAI_API_KEY` is available, or `ollama` for local inference. For Ollama, ensure the daemon is running and the model is downloaded; default model is `tev1:0.8b`.
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

For Ollama, include `"backend":"ollama"` in the JSON request and optionally `"model":"tev1:0.8b"`. The classifier calls `http://localhost:11434/v1/systemone`; override the host with `OLLAMA_BASE_URL` if needed. Ollama maps `predicate` to its `noul` question type. No OpenAI key or extra Python package is needed for this backend.

Do not use this skill for arbitrary product, legal, medical, or financial decisions. Do not send source code, credentials, tokens, or personal data to a remote API. With Ollama, the request goes to the configured Ollama server. A failed classification must not block ordinary coding work.

Install the dependency from `.agents/skills/decisions-for-coding/requirements.txt` into that skill's virtual environment. This Claude Code mirror is for use when the repository is cloned; the self-contained distributable bundle is `.agents/skills/decisions-for-coding/`.
