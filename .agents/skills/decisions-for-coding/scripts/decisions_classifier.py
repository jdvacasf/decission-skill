#!/usr/bin/env python3
"""Evaluate a decision through OpenAI, Ollama, or Jev."""

import json
import os
import sys
from urllib.request import Request, urlopen

def error(message: str) -> None:
    print(json.dumps({"error": message}, ensure_ascii=False))
    raise SystemExit(1)


def main() -> None:
    try:
        request = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        error(f"Invalid JSON input: {exc.msg}")

    if not isinstance(request, dict):
        error("Input must be a JSON object")

    input_text = request.get("input")
    question_type = request.get("type", "choice")
    question = request.get("question")
    if not isinstance(input_text, str) or not input_text.strip():
        error("'input' must be a non-empty string")
    if not isinstance(question, str) or not question.strip():
        error("'question' must be a non-empty string")
    if question_type not in {"choice", "predicate", "score"}:
        error("'type' must be 'choice', 'predicate', or 'score'")

    name = request.get("name", "decision")
    if not isinstance(name, str) or not name:
        error("'name' must be a non-empty string")
    question_data = {
        "type": question_type,
        "name": name,
        "instructions": question,
    }
    if question_type == "choice":
        choices = request.get("choices")
        if not isinstance(choices, list) or not choices:
            error("'choices' must be a non-empty list for a choice decision")
        if any(isinstance(choice, dict) and "value" not in choice for choice in choices):
            error("Each choice object must include 'value'")
        question_data["choices"] = [
            choice if isinstance(choice, dict) else {"value": choice}
            for choice in choices
        ]
    elif question_type == "score":
        levels = request.get("levels")
        if not isinstance(levels, list) or not levels:
            error("'levels' must be a non-empty list for a score decision")
        question_data["levels"] = levels

    backend = request.get("backend")
    if backend not in ("openai", "ollama", "jev"):
        error("'backend' must be explicitly set to 'openai', 'ollama', or 'jev'")

    if backend in ("ollama", "jev"):
        systemone_question = {"instructions": question}
        if question_type == "choice":
            systemone_question["type"] = "choice"
            systemone_question["criteria"] = {
                str(option["value"] if isinstance(option, dict) else option): (
                    option.get("description", "") if isinstance(option, dict) else ""
                )
                for option in choices
            }
        elif question_type == "predicate":
            systemone_question["type"] = "noul"
        else:
            systemone_question["type"] = "score"
            systemone_question["criteria"] = [
                level.get("label", level.get("value", str(level)))
                if isinstance(level, dict)
                else level
                for level in levels
            ]

        payload = {
            "model": request.get("model", "jev-latest" if backend == "jev" else "tev1:0.8b"),
            "state": {"input": input_text},
            "questions": {name: systemone_question},
        }
        if backend == "jev":
            api_key = os.environ.get("TYPESAFE_API_KEY")
            if not api_key:
                error("TYPESAFE_API_KEY is required for the Jev backend")
            base_url = "https://api.typesafe.ai"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        else:
            base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
            headers = {"Content-Type": "application/json"}
        try:
            http_request = Request(
                f"{base_url}/v1/systemone",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
            )
            with urlopen(http_request, timeout=120) as response:
                decision = json.load(response)
            answer = decision["answers"][name]
            if question_type == "predicate":
                answer = {"type": question_type, "name": name, "probability": answer["noul"]}
            else:
                answer = {"type": question_type, "name": name, **answer}
            result = {"backend": backend, "model": decision.get("model", payload["model"]), "answer": answer}
            if backend == "jev" and "usage" in decision:
                result["usage"] = decision["usage"]
        except Exception as exc:
            error(f"{backend.capitalize()} Decisions API error: {exc}")
    else:
        try:
            from openai import OpenAI

            decision = OpenAI().decisions.create(
                model=request.get("model", "gpt-6-luna"),
                input=input_text,
                questions=[question_data],
            )
        except Exception as exc:
            error(f"OpenAI Decisions API error: {exc}")

        answer = decision.answers[0]
        result = {
            "backend": backend,
            "model": decision.model,
            "answer": {
                key: value
                for key in (
                    "type", "name", "choice", "confidence", "probability", "score", "probabilities"
                )
                if (value := getattr(answer, key, None)) is not None
            },
        }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
