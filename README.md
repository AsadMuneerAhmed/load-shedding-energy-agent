# Load-shedding Energy Agent

Ek multi-agent system jo load-shedding ke din ka plan banata hai:
- **Schedule Agent**: blackout aur free hours nikalta hai
- **Appliance Agent**: shiftable appliances ko free hours mein chalata hai
- **Battery Agent**: battery charge karne ka time aur blackout runtime batata hai
- **Coordinator**: teeno ka output mila kar plain-language plan deta hai

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Test

```bash
python -m pytest tests/
```

## Limitations
- Granularity ek ghante ki hai.
- Power limit (MCB/load capacity) abhi model nahi hota.
- Logic rule-based hai. Future mein Coordinator mein LLM add kar sakte hain jo plan ko natural language mein explain kare.

## Ideas for next steps
- Schedule ko online source se fetch karna
- Notification (WhatsApp/Telegram bot) jab blackout shuru ho
- Solar panel ka input add karna