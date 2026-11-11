"""Explainer Agent: turns the final plan into a short, plain-language explanation."""
import json

from .llm_client import ask_json

SYSTEM_PROMPT = """You are the Explainer Agent in a load-shedding energy system.
You receive a finished daily plan as JSON. Your job is to explain it to a normal
household user in simple, clear language.

Rules:
- Use only the facts in the plan. Do not invent hours, numbers or appliances.
- Keep it to one short paragraph of 3 to 5 sentences.
- Say what to run and when, when to charge the battery, and any warning.
- Do not repeat the raw JSON.

Reply with JSON in this exact shape:
{
  "explanation": "<the paragraph>"
}
"""


def explain_plan(plan: dict) -> str:
    """
    plan: the dict returned by build_daily_plan or build_llm_plan.
    Returns a plain-language explanation string.
    Falls back to the plain summary lines if the LLM call fails.
    """
    facts = {
        "blackout_hours": plan.get("blackout_hours", []),
        "free_hours": plan.get("free_hours", []),
        "appliances": [
            {
                "name": i["name"],
                "status": i["status"],
                "run_at_hours": i["hours"],
                "battery_hours": i["battery_hours"],
            }
            for i in plan.get("appliances", [])
        ],
        "battery": {
            "charge_hours": plan["battery"]["charge_hours"],
            "runtime_hours": plan["battery"]["runtime_hours"],
            "final_charge_percent": plan["battery"]["final_charge_percent"],
        },
        "warnings": plan.get("warnings", []),
    }

    try:
        reply = ask_json(
            system=SYSTEM_PROMPT,
            user=json.dumps(facts, indent=2),
            max_tokens=600,
        )
        text = reply.get("explanation", "").strip()
        if text:
            return text
        raise ValueError("Explainer returned an empty explanation")
    except Exception:
        # Fallback: show the plain summary lines instead
        return " ".join(plan.get("summary", []))