"""LLM coordinator: builds the daily plan using the Planner/Critic loop.
Falls back to the rule-based plan if the loop cannot produce a valid plan."""
import math
from dataclasses import asdict

from .models import Appliance, Battery, BlackoutSlot
from .schedule_agent import blackout_hours, free_hours
from .battery_agent import plan_battery
from .planning_loop import run_planning_loop
from .coordinator import build_daily_plan, _build_summary


def build_llm_plan(slots: list[BlackoutSlot], appliances: list[Appliance], battery: Battery) -> dict:
    blackout = blackout_hours(slots)
    free = free_hours(slots)

    # Only shiftable appliances with work to do go to the LLM
    shiftable = [a for a in appliances if a.shiftable and a.hours_per_day > 0]
    if shiftable:
        loop_result = run_planning_loop([asdict(a) for a in shiftable], free)
    else:
        loop_result = {"valid": True, "plan": {"assignments": []}, "rounds": 0, "log": []}

    # Fallback: LLM plan was not valid, use the rule-based plan
    if not loop_result["valid"]:
        fallback = build_daily_plan(slots, appliances, battery)
        fallback["source"] = "rule-based"
        fallback["warnings"].insert(0, "LLM planner could not produce a valid plan, rule-based plan used.")
        fallback["agent_log"] = loop_result["log"]
        return fallback

    llm_hours = {item["name"]: item["hours"] for item in loop_result["plan"]["assignments"]}

    # Build the appliance plan in the same format as the rule-based version
    appliance_plan = []
    for a in appliances:
        needed = math.ceil(a.hours_per_day)
        item = {
            "name": a.name,
            "priority": a.priority,
            "watts": a.watts,
            "hours": [],
            "battery_hours": 0,
        }

        if needed == 0:
            status = "unused"
        elif not a.shiftable:
            status = "essential"
            item["battery_hours"] = min(needed, len(blackout))
        else:
            status = "shifted"
            item["hours"] = sorted(llm_hours.get(a.name, []))

        appliance_plan.append({**item, "status": status})

    # Hours used by appliances are not available for charging
    used = {h for item in appliance_plan for h in item["hours"]}
    charge_slots = [h for h in free if h not in used]

    battery_plan = plan_battery(battery, appliance_plan, charge_slots)
    warnings = list(battery_plan["warnings"])

    summary = _build_summary(blackout, free, appliance_plan, battery_plan)

    return {
        "source": "LLM planner",
        "blackout_hours": sorted(blackout),
        "free_hours": free,
        "appliances": appliance_plan,
        "battery": battery_plan,
        "warnings": warnings,
        "summary": summary,
        "llm_rounds": loop_result["rounds"],
        "agent_log": loop_result["log"],
    }