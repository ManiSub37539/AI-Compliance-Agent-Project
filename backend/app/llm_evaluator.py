from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from openai import OpenAI


Decision = Literal["ALLOW", "ALERT", "BLOCK"]

# Load repo-root .env explicitly
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

def load_policy():

    path = Path(__file__).parent / "policy.yaml"

    if not path.exists():
        raise FileNotFoundError(f"Missing policy.yaml at {path}")

    with open(path, "r") as f:
        return yaml.safe_load(f)


POLICY = load_policy()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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

USER PROMPT:
{user_prompt}

Return ONLY ONE label:
ALLOW
ALERT
BLOCK
"""


def evaluate_prompt(prompt: str) -> Decision:
    """
    Sends the prompt to the LLM policy evaluator.
    """

    policy_prompt = build_policy_prompt(prompt)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "user", "content": policy_prompt}
        ]
    )

    decision = response.choices[0].message.content.strip().upper()

    if decision not in ["ALLOW", "ALERT", "BLOCK"]:
        return "ALERT"

    return decision