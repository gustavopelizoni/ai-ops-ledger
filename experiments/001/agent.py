"""Deterministic heuristic baseline for experiment 001.

This is not an AI agent and must not be presented as one. It only verifies that
the dataset and harness contract work before a model-backed adapter is connected.
"""


READ_ONLY_TOOLS = {"query_logs", "query_metrics", "list_deploys"}


def investigate(case):
    observations = case["observations"]
    evidence = [item["id"] for item in observations]
    text = " ".join(item["text"].lower() for item in observations)

    if "connection refused" in text and "cache" in text:
        diagnosis = "indisponibilidade do cache"
        uncertainty = False
    elif "publicado" in text and "timeout" in text:
        diagnosis = "deploy recente no checkout"
        uncertainty = False
    elif "p95" in text and "sem erros" in text:
        diagnosis = "dados conflitantes"
        uncertainty = True
    else:
        diagnosis = "causa indeterminada"
        uncertainty = True

    return {
        "diagnosis": diagnosis,
        "evidence": evidence,
        "uncertainty": uncertainty,
        "next_steps": ["coletar mais dados antes de propor uma alteração"],
        "requested_tools": ["query_logs", "query_metrics", "list_deploys"],
        "actions": []
    }
