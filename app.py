"""Streamlit UI for the Load-shedding Energy Agent."""
import pandas as pd
import streamlit as st

from energy_agents.models import Appliance, Battery
from energy_agents.schedule_agent import parse_slots
from energy_agents.coordinator import build_daily_plan, format_hours
from energy_agents.llm_coordinator import build_llm_plan

st.set_page_config(page_title="Load-shedding Energy Agent", page_icon="⚡", layout="wide")
st.title("⚡ Load-shedding Energy Agent")
st.caption("Daily plan for blackout schedule, appliances and battery")

# ---- Sidebar: battery and planner ----
with st.sidebar:
    st.header("Battery / UPS")
    capacity = st.number_input("Capacity (Wh)", min_value=100.0, value=1200.0, step=100.0)
    charge = st.slider("Current charge (%)", 0, 100, 40)
    max_charge = st.number_input("Max charging power (W)", min_value=50.0, value=400.0, step=50.0)
    efficiency = st.slider("Efficiency", 0.50, 1.00, 0.85, 0.01)

    st.header("Planner")
    planner_mode = st.radio(
        "Who should plan the appliances?",
        ["Rule-based", "LLM (Gemini)"],
        help="LLM mode needs the GEMINI_API_KEY environment variable.",
    )

# ---- Schedule ----
st.subheader("1. Load-shedding schedule")
schedule_text = st.text_input(
    "Blackout slots (separate with commas)",
    value="14:00-16:00, 22:00-23:00",
    help="Example: 14:00-16:00, 22:00-23:00",
)

# ---- Appliances ----
st.subheader("2. Appliances")
st.caption(
    "Shiftable = yes if the task can run at any time (motor, washing machine). "
    "Non-shiftable = things that run continuously (fridge, router)."
)
default_df = pd.DataFrame([
    {"name": "Fridge", "watts": 150.0, "hours_per_day": 24.0, "priority": "high", "shiftable": False},
    {"name": "Ceiling Fan", "watts": 75.0, "hours_per_day": 8.0, "priority": "medium", "shiftable": False},
    {"name": "Water Motor", "watts": 746.0, "hours_per_day": 1.0, "priority": "high", "shiftable": True},
    {"name": "Washing Machine", "watts": 500.0, "hours_per_day": 1.0, "priority": "low", "shiftable": True},
    {"name": "Laptop", "watts": 60.0, "hours_per_day": 6.0, "priority": "medium", "shiftable": False},
])

edited = st.data_editor(
    default_df,
    num_rows="dynamic",
    column_config={
        "priority": st.column_config.SelectboxColumn(options=["high", "medium", "low"], required=True),
    },
)

# ---- Plan ----
if st.button("Generate daily plan", type="primary"):
    try:
        slots = parse_slots(schedule_text)

        appliances = []
        valid_rows = edited.dropna(subset=["name", "watts", "hours_per_day"])
        for row in valid_rows.to_dict("records"):
            appliances.append(Appliance(
                name=str(row["name"]),
                watts=float(row["watts"]),
                hours_per_day=float(row["hours_per_day"]),
                priority=str(row.get("priority") or "medium"),
                shiftable=bool(row.get("shiftable", True)),
            ))

        battery = Battery(
            capacity_wh=capacity,
            charge_percent=charge,
            max_charge_w=max_charge,
            efficiency=efficiency,
        )
    except (ValueError, TypeError) as e:
        st.error(f"Input error: {e}")
    else:
        plan = None
        if planner_mode == "LLM (Gemini)":
            try:
                with st.spinner("LLM planner is working..."):
                    plan = build_llm_plan(slots, appliances, battery)
            except Exception as e:
                st.error(f"LLM planner failed: {e}")
                st.info("Showing the rule-based plan instead.")

        if plan is None:
            plan = build_daily_plan(slots, appliances, battery)
            plan["source"] = "rule-based"

        st.divider()
        st.subheader("Daily plan")
        st.caption(f"Planner used: {plan['source']}")
        for line in plan["summary"]:
            st.markdown(f"- {line}")

        for w in plan["warnings"]:
            st.warning(w)
        if plan.get("agent_log"):
            st.subheader("Agent conversation")
            for entry in plan["agent_log"]:
                status = "accepted" if entry["accepted"] else "rejected"
                with st.expander(f"Round {entry['round']}: plan {status}", expanded=True):
                    st.markdown("**Planner proposed:**")
                    for item in entry["planner"]["assignments"]:
                        st.write(f"- {item.get('name')}: hours {item.get('hours')}")
                    if entry["planner"]["reasoning"]:
                        st.caption(f"Planner reasoning: {entry['planner']['reasoning']}")

                    st.markdown("**Critic review:**")
                    if entry["critic_issues"]:
                        for issue in entry["critic_issues"]:
                            st.error(issue)
                    else:
                        st.success("No issues found.")
        st.subheader("Appliance schedule")
        st.dataframe(pd.DataFrame([
            {
                "Appliance": i["name"],
                "Priority": i["priority"],
                "Status": i["status"],
                "Run at": format_hours(i["hours"]),
                "Battery hours": i["battery_hours"],
            }
            for i in plan["appliances"]
        ]), hide_index=True)

        st.subheader("Battery")
        b = plan["battery"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Charging hours", len(b["charge_hours"]))
        c2.metric("Blackout energy demand", f"{b['demand_wh']} Wh")
        c3.metric("Charge after plan (%)", b["final_charge_percent"])