from energy_agents.models import Appliance, Battery
from energy_agents.schedule_agent import parse_slots
from energy_agents.llm_coordinator import build_llm_plan

slots = parse_slots("14:00-16:00, 22:00-23:00")
battery = Battery(capacity_wh=1200, charge_percent=40, max_charge_w=400, efficiency=0.85)
appliances = [
    Appliance("Fridge", watts=150, hours_per_day=24, priority="high", shiftable=False),
    Appliance("Ceiling Fan", watts=75, hours_per_day=8, priority="medium", shiftable=False),
    Appliance("Water Motor", watts=746, hours_per_day=1, priority="high", shiftable=True),
    Appliance("Washing Machine", watts=500, hours_per_day=1, priority="low", shiftable=True),
    Appliance("Laptop", watts=60, hours_per_day=6, priority="medium", shiftable=False),
]

plan = build_llm_plan(slots, appliances, battery)

print("Source:", plan["source"])
print("LLM rounds:", plan.get("llm_rounds"))
print("Summary:")
for line in plan["summary"]:
    print(" -", line)
print("Warnings:", plan["warnings"])