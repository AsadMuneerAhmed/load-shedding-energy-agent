import pytest

from energy_agents.models import Appliance, Battery
from energy_agents.schedule_agent import parse_slots, blackout_hours, free_hours
from energy_agents.appliance_agent import plan_appliances
from energy_agents.battery_agent import plan_battery
from energy_agents.coordinator import build_daily_plan, format_hours


def test_parse_slots_valid():
    slots = parse_slots("14:00-16:00, 22:00-23:00")
    assert [(s.start, s.end) for s in slots] == [(14, 16), (22, 23)]


def test_parse_slots_invalid_format():
    with pytest.raises(ValueError):
        parse_slots("abc-def")


def test_parse_slots_invalid_range():
    with pytest.raises(ValueError):
        parse_slots("16:00-14:00")


def test_free_hours_exclude_blackout():
    slots = parse_slots("14:00-16:00")
    free = free_hours(slots)
    assert 14 not in free and 15 not in free
    assert len(free) == 22


def test_shiftable_appliance_avoids_blackout():
    slots = parse_slots("0:00-12:00")
    blackout = blackout_hours(slots)
    free = free_hours(slots)
    motor = Appliance("Motor", watts=746, hours_per_day=2, priority="high", shiftable=True)
    plan, _ = plan_appliances([motor], blackout, free)
    assert plan[0]["status"] == "shifted"
    assert all(h not in blackout for h in plan[0]["hours"])


def test_essential_appliance_uses_battery_during_blackout():
    slots = parse_slots("14:00-16:00")
    blackout = blackout_hours(slots)
    free = free_hours(slots)
    fridge = Appliance("Fridge", watts=150, hours_per_day=24, priority="high", shiftable=False)
    plan, _ = plan_appliances([fridge], blackout, free)
    assert plan[0]["status"] == "essential"
    assert plan[0]["battery_hours"] == 2


def test_partial_when_not_enough_free_hours():
    free = [0]  # sirf 1 free hour
    motor = Appliance("Motor", watts=500, hours_per_day=3, priority="high", shiftable=True)
    plan, warnings = plan_appliances([motor], set(range(1, 24)), free)
    assert plan[0]["status"] == "partial"
    assert plan[0]["battery_hours"] == 2
    assert warnings


def test_battery_charges_only_in_free_hours():
    slots = parse_slots("10:00-14:00")
    free = free_hours(slots)
    battery = Battery(capacity_wh=1000, charge_percent=0, max_charge_w=200)
    appliance_plan = [{"watts": 100, "battery_hours": 4, "status": "essential"}]
    result = plan_battery(battery, appliance_plan, free)
    assert result["charge_hours"]
    assert all(h not in range(10, 14) for h in result["charge_hours"])


def test_no_blackout_no_charging_needed():
    battery = Battery(capacity_wh=1000, charge_percent=50)
    plan = build_daily_plan([], [Appliance("Fan", 75, 8, "medium", False)], battery)
    assert plan["battery"]["charge_hours"] == []
    assert plan["battery"]["demand_wh"] == 0


def test_format_hours_ranges():
    assert format_hours([14, 15, 22]) == "14:00-16:00, 22:00-23:00"
    assert format_hours([]) == "-"

def test_shiftable_appliances_do_not_overlap():
    slots = parse_slots("14:00-16:00")
    blackout = blackout_hours(slots)
    free = free_hours(slots)
    motor = Appliance("Motor", watts=746, hours_per_day=1, priority="high", shiftable=True)
    washer = Appliance("Washer", watts=500, hours_per_day=1, priority="low", shiftable=True)
    plan, _ = plan_appliances([motor, washer], blackout, free)
    all_hours = [h for item in plan for h in item["hours"]]
    assert len(all_hours) == len(set(all_hours))