"""Coordinator loop: runs the Planner and Critic until the plan is valid or rounds run out."""
from .planner_agent import plan_schedule
from .critic_agent import review_plan

MAX_ROUNDS = 3


def run_planning_loop(appliances: list[dict], free_hrs: list[int], max_rounds: int = MAX_ROUNDS) -> dict:
    """
    Returns a dict with:
      - plan: the last Planner output (dict with 'assignments')
      - valid: True if the Critic found no issues
      - rounds: how many rounds were used
      - issues: the issues from the last round (empty if valid)
      - history: list of (round, issues) for every round
      - log: detailed record of every round, for the UI
    """
    feedback = None
    history = []
    log = []
    plan = {"assignments": []}
    issues = []

    for round_no in range(1, max_rounds + 1):
        try:
            plan = plan_schedule(appliances, free_hrs, feedback=feedback)
            issues = review_plan(plan, appliances, free_hrs)
        except ValueError as e:
            # The LLM returned something that is not valid JSON
            plan = {"assignments": []}
            issues = [f"Planner output could not be parsed: {e}"]

        history.append((round_no, issues))
        log.append({
            "round": round_no,
            "planner": {
                "assignments": plan.get("assignments", []),
                "reasoning": plan.get("reasoning", ""),
            },
            "critic_issues": issues,
            "accepted": not issues,
        })

        if not issues:
            return {
                "plan": plan,
                "valid": True,
                "rounds": round_no,
                "issues": [],
                "history": history,
                "log": log,
            }

        feedback = "\n".join(f"- {issue}" for issue in issues)

    return {
        "plan": plan,
        "valid": False,
        "rounds": max_rounds,
        "issues": issues,
        "history": history,
        "log": log,
    }