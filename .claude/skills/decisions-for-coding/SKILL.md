---
name: decisions-for-coding
description: Evaluate coding decisions with OpenAI Decisions API, local Ollama, or Jev. Use when Claude Code needs a structured choice, predicate, or score before choosing an implementation approach.
---

# Decisions for coding

Use the classifier packaged in `.agents/skills/decisions-for-coding/scripts/decisions_classifier.py` to evaluate a coding decision, then use the JSON result to choose the smallest appropriate engineering workflow. The result is advisory: inspect the code and requirements before making the final decision. Always choose the backend explicitly: OpenAI and Jev send the request to remote APIs; Ollama sends it to the configured Ollama server. Never retry with another backend automatically.

## Workflow

Use the classifier only when a bounded coding decision has multiple plausible outcomes and the answer could change the workflow. Skip it when the answer is obvious, a repository rule already settles the question, or the prompt is only a follow-up; gather context or clarify first if the decision itself is not yet clear. OpenAI and Jev are remote: never send sensitive or disallowed content to them. Use Ollama only when its configured server is approved for that data; otherwise skip classification.

1. Build a JSON request with `input`, `question`, and `type`. Add `choices` for `choice` or `levels` for `score`. For `choice`, include an `other` or `insufficient information` option when the listed alternatives may not cover the case; do not force a match when none fits.
2. Set `backend` to exactly `openai`, `ollama`, or `jev`; do not infer it from whether an API key happens to exist. For Ollama, ensure the daemon is running and the model is downloaded; default model is `tev1:0.8b`. Jev defaults to `jev-latest` and requires `TYPESAFE_API_KEY`.
3. From the repository root, send the request through standard input. Use the skill's virtual environment for OpenAI, or system Python (`python3` on macOS/Linux, `py -3` on Windows) for Ollama or Jev:

   ```bash
   printf '%s' '<JSON request>' | .agents/skills/decisions-for-coding/.venv/bin/python .agents/skills/decisions-for-coding/scripts/decisions_classifier.py
   ```

   For Ollama or Jev, use the same JSON request with the selected backend and invoke the script with `python3` (or `py -3` on Windows), without `.venv`.

4. Parse the JSON response from standard output and use the result as a routing hint:
   - `feature`: inspect callers, interfaces, tests, and configuration before implementing.
   - `bugfix`: reproduce or isolate the failure, then fix the shared root cause.
   - `refactor`: preserve behavior and run focused regression tests.
   - `test`: add the smallest test that proves the requested behavior.
   - `security`: treat inputs as untrusted and inspect exposure, authorization, and logging.
   - `docs`: update only documentation affected by the current behavior.
5. Treat the result as advisory. For `choice` or `score`, if returned confidence is low or the leading choice probabilities are close, describe the classification as tentative and rely on repository context and engineering judgment; do not block ordinary work or invent a numeric confidence threshold. For `predicate`, `probability` is the estimated truth of the statement, not a confidence score. Report confidence when provided and proceed only within the user's requested scope.

For Ollama, include `"backend":"ollama"` in the JSON request and optionally `"model":"tev1:0.8b"`. The classifier calls `http://localhost:11434/v1/systemone`; override the host with `OLLAMA_BASE_URL` if needed. For Jev, include `"backend":"jev"`; the classifier calls `https://api.typesafe.ai/v1/systemone` using `TYPESAFE_API_KEY` as a Bearer credential and defaults to `jev-latest`. You can override the model with the request's `model` field. Jev is remote; its response includes token usage when provided by the API. Ollama and Jev map `predicate` to the System One `noul` question type. If a request fails, continue with local engineering judgment and report that classification was skipped; never send it to another backend as a fallback. These backends need no OpenAI key or extra Python package.

Do not use this skill for arbitrary product, legal, medical, or financial decisions. Do not send source code, credentials, tokens, or personal data to a remote API. A failed classification must not block ordinary coding work.

Install the dependency from `.agents/skills/decisions-for-coding/requirements.txt` into that skill's virtual environment only when using OpenAI. This Claude Code mirror is for use when the repository is cloned; the self-contained distributable bundle is `.agents/skills/decisions-for-coding/`.
