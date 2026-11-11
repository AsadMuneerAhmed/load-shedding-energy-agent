import json

from energy_agents.planner_agent import plan_schedule

appliances = [
    {"name": "Water Motor", "watts": 746, "hours_per_day": 1, "priority": "high", "shiftable": True},
    {"name": "Washing Machine", "watts": 500, "hours_per_day": 1, "priority": "low", "shiftable": True},
    {"name": "Fridge", "watts": 150, "hours_per_day": 24, "priority": "high", "shiftable": False},
]
free_hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21, 23]

result = plan_schedule(appliances, free_hours)
print(json.dumps(result, indent=2))