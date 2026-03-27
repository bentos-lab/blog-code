"""Context Routing — maps current task state to the appropriate sub-agent."""

from typing import Literal

AgentType = Literal["analyzer", "researcher", "executor", "tester"]


def route(task_state: dict) -> AgentType:
    """Route the current task state to the right sub-agent.

    Routing rules (rule-based for determinism — no LLM needed):
    - No bug report yet → analyzer
    - Has bug report, no proposed fix → researcher
    - Has fix, not applied yet → executor
    - Fix applied → tester

    Args:
        task_state: Dict with keys like 'bug_report', 'proposed_fix', 'fix_applied'

    Returns:
        AgentType to dispatch next.
    """
    if not task_state.get("bug_report"):
        return "analyzer"
    if not task_state.get("proposed_fix"):
        return "researcher"
    if not task_state.get("fix_applied"):
        return "executor"
    return "tester"
