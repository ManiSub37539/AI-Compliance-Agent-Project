from rule_scanner import scan_prompt
from llm_evaluator import evaluate_prompt


def evaluate_user_prompt(prompt: str):

    scan_result = scan_prompt(prompt)

    # If deterministic scanner already blocks it
    if scan_result["severity"] == "block":
        scan_result["final_decision"] = "BLOCK"
        return scan_result

    # Otherwise run LLM evaluator
    llm_decision = evaluate_prompt(prompt)

    scan_result["llm_decision"] = llm_decision

    if llm_decision == "BLOCK":
        scan_result["severity"] = "block"

    elif llm_decision == "ALERT" and scan_result["severity"] != "block":
        scan_result["severity"] = "alert"

    scan_result["final_decision"] = scan_result["severity"].upper()

    return scan_result