"""Coordinator: combines the output of all agents into a daily plan."""
from .models import Appliance, Battery, BlackoutSlot
from .schedule_agent import blackout_hours, free_hours
from .appliance_agent import plan_appliances
from .battery_agent import plan_battery


def format_hours(hours: list[int]) -> str:
    """[14, 15, 22] -> '14:00-16:00, 22:00-23:00'"""
    if not hours:
        return "-"
    hours = sorted(hours)
    ranges = []
    start = prev = hours[0]
    for h in hours[1:]:
        if h == prev + 1:
            prev = h
            continue
        ranges.append((start, prev))
        start = prev = h
    ranges.append((start, prev))
    return ", ".join(f"{a:02d}:00-{b + 1:02d}:00" for a, b in ranges)


def build_daily_plan(slots: list[BlackoutSlot], appliances: list[Appliance], battery: Battery) -> dict:
    blackout = blackout_hours(slots)
    free = free_hours(slots)

    appliance_plan, warnings = plan_appliances(appliances, blackout, free)

    # Hours already used by appliances are not available for charging
    used = {h for item in appliance_plan for h in item["hours"]}
    charge_slots = [h for h in free if h not in used]

    battery_plan = plan_battery(battery, appliance_plan, charge_slots)
    warnings.extend(battery_plan["warnings"])

    summary = _build_summary(blackout, free, appliance_plan, battery_plan)

    return {
        "blackout_hours": sorted(blackout),
        "free_hours": free,
        "appliances": appliance_plan,
        "battery": battery_plan,
        "warnings": warnings,
        "summary": summary,
    }


def _build_summary(blackout, free, appliance_plan, battery_plan) -> list[str]:
    lines = []

    if not blackout:
        lines.append("There is no load-shedding scheduled today. All appliances can run normally.")
    else:
        lines.append(f"Blackout hours: {format_hours(sorted(blackout))}")
        lines.append(f"Free hours: {format_hours(free)}")

    for item in appliance_plan:
        name = item["name"]
        if item["status"] == "shifted":
            lines.append(f"{name}: run between {format_hours(item['hours'])}.")
        elif item["status"] == "partial":
            lines.append(
                f"{name}: run between {format_hours(item['hours'])}, "
                f"the remaining ~{item['battery_hours']} hour(s) on battery."
            )
        elif item["status"] == "essential":
            if item["battery_hours"]:
                lines.append(f"{name}: will run on battery for ~{item['battery_hours']} hour(s) during blackout.")
            else:
                lines.append(f"{name}: no battery needed for this schedule.")

    if battery_plan["charge_hours"]:
        lines.append(f"Charge the battery: {format_hours(battery_plan['charge_hours'])}")
    else:
        lines.append("The battery does not need to be charged right now.")

    if battery_plan["runtime_hours"] is not None:
        lines.append(
            f"At the current charge, essential loads will run for ~{battery_plan['runtime_hours']:.1f} hour(s)."
        )

    return lines