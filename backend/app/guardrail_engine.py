from rule_scanner import scan_prompt
from llm_evaluator import evaluate_prompt


def map_severity_to_decision(severity: str) -> str:
    if severity == "none":
        return "ALLOW"
    if severity == "alert":
        return "ALERT"
    if severity == "block":
        return "BLOCK"
    return "ALERT"


def evaluate_user_prompt(prompt: str):
    scan_result = scan_prompt(prompt)

    # Hard block from deterministic scanner
    if scan_result["severity"] == "block":
        scan_result["llm_decision"] = "SKIPPED"
        scan_result["triggered"] = True
        scan_result["final_decision"] = "BLOCK"
        return scan_result

    # Run LLM evaluator for non-blocked prompts
    llm_decision = evaluate_prompt(prompt)
    scan_result["llm_decision"] = llm_decision

    # Escalate severity only, never downgrade
    if llm_decision == "BLOCK":
        scan_result["severity"] = "block"
    elif llm_decision == "ALERT":
        if scan_result["severity"] == "none":
            scan_result["severity"] = "alert"

    # Recompute triggered AFTER final severity is set
    scan_result["triggered"] = scan_result["severity"] != "none"

    # Final decision
    scan_result["final_decision"] = map_severity_to_decision(scan_result["severity"])

    return scan_result