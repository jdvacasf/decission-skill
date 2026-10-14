#!/usr/bin/env python3
"""Evaluate a generic decision through the OpenAI Decisions API."""

import json
import sys

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

    question_data = {
        "type": question_type,
        "name": request.get("name", "decision"),
        "instructions": question,
    }
    if question_type == "choice":
        choices = request.get("choices")
        if not isinstance(choices, list) or not choices:
            error("'choices' must be a non-empty list for a choice decision")
        question_data["choices"] = [
            choice if isinstance(choice, dict) else {"value": choice}
            for choice in choices
        ]
    elif question_type == "score":
        levels = request.get("levels")
        if not isinstance(levels, list) or not levels:
            error("'levels' must be a non-empty list for a score decision")
        question_data["levels"] = levels

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
