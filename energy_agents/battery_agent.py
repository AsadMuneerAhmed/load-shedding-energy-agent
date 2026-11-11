"""Battery Agent: battery charging plan and runtime estimate."""
import math

from .models import Battery


def plan_battery(battery: Battery, appliance_plan: list[dict], free_hrs: list[int]) -> dict:
    warnings = []

    # Energy (Wh) needed from the battery during blackout
    demand_wh = sum(i["watts"] * i["battery_hours"] for i in appliance_plan)
    essential_watts = sum(i["watts"] for i in appliance_plan if i["status"] == "essential")

    # Stored energy must be higher to cover inverter losses
    target_stored = min(battery.capacity_wh, demand_wh / battery.efficiency)
    deficit_wh = max(0.0, target_stored - battery.stored_wh)

    charge_needed = math.ceil(deficit_wh / battery.max_charge_w) if deficit_wh else 0
    if charge_needed > len(free_hrs):
        warnings.append(
            f"Full charging needs {charge_needed} hour(s), but only "
            f"{len(free_hrs)} free hour(s) are available"
        )
    # Charge as early as possible within the free hours
    charge_hours = free_hrs[:charge_needed]

    if demand_wh > battery.capacity_wh * battery.efficiency:
        warnings.append(
            "Battery capacity is lower than the blackout demand. "
            "Some appliances will have to be turned off"
        )

    stored_after = min(battery.capacity_wh, battery.stored_wh + len(charge_hours) * battery.max_charge_w)
    runtime_hours = battery.usable_wh / essential_watts if essential_watts > 0 else None

    return {
        "demand_wh": round(demand_wh, 1),
        "charge_hours": charge_hours,
        "final_charge_percent": round(stored_after / battery.capacity_wh * 100, 1),
        "runtime_hours": round(runtime_hours, 2) if runtime_hours is not None else None,
        "warnings": warnings,
    }