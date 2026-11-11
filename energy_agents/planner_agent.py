"""Planner Agent: asks the LLM to assign free hours to shiftable appliances."""
import json

from .llm_client import ask_json

SYSTEM_PROMPT = """You are the Planner Agent in a load-shedding energy system.
You receive a list of appliances and the free hours (hours with electricity).
Your job: assign the free hours to shiftable appliances.

Rules:
- Only assign hours from the provided free_hours list.
- Each appliance gets exactly the number of hours in its hours_per_day (rounded up).
- No hour can be given to two appliances.
- Give high priority appliances the earliest good hours.
- Do not assign hours to non-shiftable appliances.

Reply with JSON in this exact shape:
{
  "assignments": [
    {"name": "<appliance name>", "hours": [<integer hours>]}
  ],
  "reasoning": "<one or two short sentences>"
}
"""


def plan_schedule(appliances: list[dict], free_hrs: list[int], feedback: str | None = None) -> dict:
    """
    appliances: list of dicts with keys name, watts, hours_per_day, priority, shiftable
    free_hrs: list of free hours, e.g. [0, 1, 2, 6, 7]
    feedback: optional message from the Critic Agent, used in later rounds
    Returns the parsed JSON dict from the LLM.
    """
    payload = {
        "appliances": appliances,
        "free_hours": free_hrs,
    }
    user_message = json.dumps(payload, indent=2)
    if feedback:
        user_message += f"\n\nFeedback from the Critic Agent, fix these issues:\n{feedback}"

    return ask_json(system=SYSTEM_PROMPT, user=user_message)