from energy_agents.critic_agent import review_plan

appliances = [
    {"name": "Water Motor", "watts": 746, "hours_per_day": 1, "priority": "high", "shiftable": True},
    {"name": "Washing Machine", "watts": 500, "hours_per_day": 1, "priority": "low", "shiftable": True},
    {"name": "Fridge", "watts": 150, "hours_per_day": 24, "priority": "high", "shiftable": False},
]
free_hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21, 23]

good_plan = {
    "assignments": [
        {"name": "Water Motor", "hours": [0]},
        {"name": "Washing Machine", "hours": [1]},
    ]
}

bad_plan = {
    "assignments": [
        {"name": "Water Motor", "hours": [14]},          # blackout hour
        {"name": "Washing Machine", "hours": [14]},      # same hour as motor
        {"name": "Fridge", "hours": [2]},                # non-shiftable
    ]
}

print("Good plan issues:", review_plan(good_plan, appliances, free_hours))
print("Bad plan issues:")
for issue in review_plan(bad_plan, appliances, free_hours):
    print(" -", issue)

duplicate_plan = {
    "assignments": [
        {"name": "Water Motor", "hours": [0]},
        {"name": "Washing Machine", "hours": [0]},  # same free hour as motor
    ]
}
print("Duplicate issues:", review_plan(duplicate_plan, appliances, free_hours))