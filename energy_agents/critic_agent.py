"""Critic Agent: checks the Planner's output with hard rules written in Python."""
import math


def review_plan(plan: dict, appliances: list[dict], free_hrs: list[int]) -> list[str]:
    """
    Check the Planner's output against the rules.
    Returns a list of issue messages. An empty list means the plan is valid.
    """
    issues = []
    free_set = set(free_hrs)
    appliances_by_name = {a["name"]: a for a in appliances}

    assignments = plan.get("assignments", [])
    if not isinstance(assignments, list):
        return ["'assignments' must be a list"]

    used_hours: dict[int, str] = {}  # hour -> appliance name that took it
    assigned_names = set()

    for item in assignments:
        name = item.get("name")
        hours = item.get("hours", [])

        # Rule: appliance must exist in the input
        if name not in appliances_by_name:
            issues.append(f"Unknown appliance in plan: '{name}'")
            continue

        appliance = appliances_by_name[name]
        assigned_names.add(name)

        # Rule: only shiftable appliances get hours
        if not appliance["shiftable"]:
            issues.append(f"'{name}' is not shiftable, it must not get scheduled hours")
            continue

        # Rule: correct number of hours
        needed = math.ceil(appliance["hours_per_day"])
        if len(hours) != needed:
            issues.append(f"'{name}' needs {needed} hour(s) but got {len(hours)}")

        for h in hours:
            # Rule: hour must be a free hour
            if h not in free_set:
                issues.append(f"'{name}' is given hour {h}, which is not a free hour")
                continue

            # Rule: no hour can be shared
            if h in used_hours:
                issues.append(
                    f"Hour {h} is given to both '{used_hours[h]}' and '{name}'"
                )
            else:
                used_hours[h] = name

    # Rule: every shiftable appliance must be in the plan
    for a in appliances:
        if a["shiftable"] and a["hours_per_day"] > 0 and a["name"] not in assigned_names:
            issues.append(f"'{a['name']}' is missing from the plan")

    return issues