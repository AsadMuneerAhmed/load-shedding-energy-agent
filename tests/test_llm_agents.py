"""Tests for the LLM agents. The LLM is replaced with a fake, so no API key or internet is needed."""
import pytest

from energy_agents.models import Appliance, Battery
from energy_agents.schedule_agent import parse_slots, blackout_hours, free_hours
from energy_agents.planning_loop import run_planning_loop
from energy_agents import llm_coordinator
from energy_agents import explainer_agent


def make_fake_llm(responses):
    """Returns a fake ask_json that gives the given replies in order and records the prompts."""
    calls = []

    def fake_ask_json(system, user, max_tokens=1000):
        calls.append(user)
        if not responses:
            raise AssertionError("Fake LLM ran out of responses")
        return responses.pop(0)

    fake_ask_json.calls = calls
    return fake_ask_json


APPLIANCES = [
    {"name": "Water Motor", "watts": 746, "hours_per_day": 1, "priority": "high", "shiftable": True},
    {"name": "Washing Machine", "watts": 500, "hours_per_day": 1, "priority": "low", "shiftable": True},
    {"name": "Fridge", "watts": 150, "hours_per_day": 24, "priority": "high", "shiftable": False},
]
FREE_HOURS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21, 23]

GOOD_REPLY = {
    "assignments": [
        {"name": "Water Motor", "hours": [0]},
        {"name": "Washing Machine", "hours": [1]},
    ],
    "reasoning": "test",
}

BAD_REPLY = {
    "assignments": [
        {"name": "Water Motor", "hours": [14]},  # blackout hour
        {"name": "Washing Machine", "hours": [1]},
    ],
    "reasoning": "test",
}


def test_loop_accepts_valid_plan_in_first_round(monkeypatch):
    fake = make_fake_llm([GOOD_REPLY])
    monkeypatch.setattr("energy_agents.planner_agent.ask_json", fake)

    result = run_planning_loop(APPLIANCES[:2], FREE_HOURS)

    assert result["valid"] is True
    assert result["rounds"] == 1
    assert len(result["log"]) == 1
    assert result["log"][0]["accepted"] is True


def test_loop_sends_critic_feedback_on_retry(monkeypatch):
    fake = make_fake_llm([BAD_REPLY, GOOD_REPLY])
    monkeypatch.setattr("energy_agents.planner_agent.ask_json", fake)

    result = run_planning_loop(APPLIANCES[:2], FREE_HOURS)

    assert result["valid"] is True
    assert result["rounds"] == 2
    assert result["log"][0]["accepted"] is False
    # The second prompt must contain the Critic's feedback
    assert "Feedback from the Critic Agent" in fake.calls[1]


def test_loop_gives_up_after_max_rounds(monkeypatch):
    fake = make_fake_llm([BAD_REPLY, BAD_REPLY])
    monkeypatch.setattr("energy_agents.planner_agent.ask_json", fake)

    result = run_planning_loop(APPLIANCES[:2], FREE_HOURS, max_rounds=2)

    assert result["valid"] is False
    assert result["rounds"] == 2
    assert result["issues"]


def test_loop_handles_invalid_json_reply(monkeypatch):
    def broken_ask_json(system, user, max_tokens=1000):
        raise ValueError("Model did not return valid JSON")

    monkeypatch.setattr("energy_agents.planner_agent.ask_json", broken_ask_json)

    result = run_planning_loop(APPLIANCES[:2], FREE_HOURS, max_rounds=1)

    assert result["valid"] is False
    assert "could not be parsed" in result["issues"][0]


def test_llm_coordinator_falls_back_to_rule_based(monkeypatch):
    slots = parse_slots("14:00-16:00, 22:00-23:00")
    battery = Battery(capacity_wh=1200, charge_percent=40, max_charge_w=400, efficiency=0.85)
    appliances = [
        Appliance("Fridge", watts=150, hours_per_day=24, priority="high", shiftable=False),
        Appliance("Water Motor", watts=746, hours_per_day=1, priority="high", shiftable=True),
    ]

    def failing_loop(appliances, free_hrs, max_rounds=3):
        return {"valid": False, "plan": {"assignments": []}, "rounds": 3,
                "issues": ["bad"], "history": [], "log": []}

    monkeypatch.setattr(llm_coordinator, "run_planning_loop", failing_loop)

    plan = llm_coordinator.build_llm_plan(slots, appliances, battery)

    assert plan["source"] == "rule-based"
    assert "agent_log" in plan
    assert plan["warnings"][0].startswith("LLM planner could not produce")


def test_explainer_falls_back_to_summary_when_llm_fails(monkeypatch):
    slots = parse_slots("14:00-16:00")
    blackout = blackout_hours(slots)
    battery = Battery(capacity_wh=1200, charge_percent=40, max_charge_w=400, efficiency=0.85)
    appliances = [Appliance("Fridge", watts=150, hours_per_day=24, priority="high", shiftable=False)]
    from energy_agents.coordinator import build_daily_plan
    plan = build_daily_plan(slots, appliances, battery)

    def broken(system, user, max_tokens=600):
        raise RuntimeError("API is down")

    monkeypatch.setattr(explainer_agent, "ask_json", broken)

    text = explainer_agent.explain_plan(plan)

    assert "Blackout hours" in text
    assert blackout  # sanity check that the plan really had a blackout