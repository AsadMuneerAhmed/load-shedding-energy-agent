"""Appliance Agent: moves each appliance's work into free hours."""
import math

from .models import PRIORITY_RANK


def _contiguous_runs(hours: list[int]) -> list[list[int]]:
    """[0,1,2,5,6] -> [[0,1,2],[5,6]]"""
    runs: list[list[int]] = []
    for h in hours:
        if runs and h == runs[-1][-1] + 1:
            runs[-1].append(h)
        else:
            runs.append([h])
    return runs


def _pick_hours(needed: int, free_hrs: list[int]) -> list[int]:
    """Pick the first contiguous window long enough, otherwise the first free hours."""
    if needed <= 0 or not free_hrs:
        return []
    for run in _contiguous_runs(free_hrs):
        if len(run) >= needed:
            return run[:needed]
    return free_hrs[:needed]


def plan_appliances(appliances, blackout: set[int], free_hrs: list[int]):
    """
    Returns (plan, warnings).
    Each appliance gets hours that no other appliance has already taken.
    status:
      unused    - hours_per_day is 0
      shifted   - all of its work fits in free hours
      partial   - not enough free hours, the rest runs on battery
      essential - not shiftable, runs on battery during blackout
    """
    n_blackout = len(blackout)
    plan, warnings = [], []
    remaining = list(free_hrs)  # shrinks after each assignment

    # High priority first so they get the best hours
    for a in sorted(appliances, key=lambda x: PRIORITY_RANK[x.priority]):
        needed = math.ceil(a.hours_per_day)
        item = {
            "name": a.name,
            "priority": a.priority,
            "watts": a.watts,
            "hours": [],
            "battery_hours": 0,
        }

        if needed == 0:
            plan.append({**item, "status": "unused"})
            continue

        if not a.shiftable:
            item["battery_hours"] = min(needed, n_blackout)
            plan.append({**item, "status": "essential"})
            continue

        hours = _pick_hours(needed, remaining)
        remaining = [h for h in remaining if h not in hours]
        uncovered = needed - len(hours)
        item["hours"] = hours
        item["battery_hours"] = uncovered

        if uncovered:
            warnings.append(
                f"{a.name}: only {len(hours)} free hour(s) available, "
                f"the remaining {uncovered} hour(s) will run on battery"
            )
            plan.append({**item, "status": "partial"})
        else:
            plan.append({**item, "status": "shifted"})

    return plan, warnings