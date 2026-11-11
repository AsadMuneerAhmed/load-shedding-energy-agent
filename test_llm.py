from energy_agents.llm_client import ask_json

result = ask_json(
    system="You are a helpful assistant.",
    user='Reply with exactly this JSON: {"status": "ok"}',
)
print(result)
print("Type:", type(result))