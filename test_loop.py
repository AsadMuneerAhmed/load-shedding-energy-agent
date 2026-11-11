import json

from energy_agents.planning_loop import run_planning_loop

appliances = [
    {"name": "Water Motor", "watts": 746, "hours_per_day": 1, "priority": "high", "shiftable": True},
    {"name": "Washing Machine", "watts": 500, "hours_per_day": 1, "priority": "low", "shiftable": True},
    {"name": "Fridge", "watts": 150, "hours_per_day": 24, "priority": "high", "shiftable": False},
]
free_hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21, 23]

result = run_planning_loop(appliances, free_hours)

print("Valid:", result["valid"])
print("Rounds used:", result["rounds"])
print("Final plan:")
print(json.dumps(result["plan"], indent=2))
print("History:")
for round_no, issues in result["history"]:
    print(f"  Round {round_no}: {issues if issues else 'OK'}")