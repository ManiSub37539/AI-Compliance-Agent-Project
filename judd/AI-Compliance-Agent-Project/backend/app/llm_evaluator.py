from __future__ import annotations

import json
import os
import yaml
from pathlib import Path
from typing import Literal, TypedDict

from dotenv import load_dotenv
from openai import OpenAI


Decision = Literal["ALLOW", "ALERT", "BLOCK"]


class LLMEvaluationResult(TypedDict):
    decision: Decision
    reason: str


# Load repo-root .env explicitly
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def load_policy() -> dict:
    path = Path(__file__).parent / "policy.yaml"

    if not path.exists():
        raise FileNotFoundError(f"Missing policy.yaml at {path}")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


POLICY = load_policy()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is missing from environment.")

client = OpenAI(api_key=api_key)


def build_policy_prompt(user_prompt: str) -> str:
    """
    Construct the Policy-as-Prompt instruction sent to the LLM.
    """

    role = POLICY["system_role"]
    instructions = POLICY["instructions"]

    return f"""
SYSTEM ROLE:
{role}

POLICY INSTRUCTIONS:
{instructions}

TASK:
Evaluate the USER PROMPT against the policy.

Return a JSON object with exactly these fields:
{{
  "decision": "ALLOW" | "ALERT" | "BLOCK",
  "reason": "A short one-sentence explanation."
}}

USER PROMPT:
{user_prompt}
""".strip()


def _fallback_result(reason: str) -> LLMEvaluationResult:
    return {
        "decision": "ALERT",
        "reason": reason,
    }


def evaluate_prompt(prompt: str) -> LLMEvaluationResult:
    """
    Sends the prompt to the LLM policy evaluator and returns:
    {
        "decision": "ALLOW" | "ALERT" | "BLOCK",
        "reason": "short explanation"
    }
    """

    policy_prompt = build_policy_prompt(prompt)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "user", "content": policy_prompt}
            ]
        )

        content = response.choices[0].message.content
        if not content:
            return _fallback_result("LLM returned an empty response.")

        content = content.strip()

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return _fallback_result("LLM returned malformed JSON.")

        decision = str(parsed.get("decision", "")).strip().upper()
        reason = str(parsed.get("reason", "")).strip()

        if decision not in {"ALLOW", "ALERT", "BLOCK"}:
            return _fallback_result("LLM returned an invalid decision label.")

        if not reason:
            reason = "No explanation provided by LLM."

        return {
            "decision": decision,
            "reason": reason,
        }

    except Exception as e:
        return _fallback_result(f"LLM evaluation failed: {str(e)}")