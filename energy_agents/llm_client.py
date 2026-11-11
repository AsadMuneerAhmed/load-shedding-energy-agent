"""LLM client: sends a prompt to Gemini and returns the reply parsed as JSON."""
import json
import os
import re

from google import genai
from google.genai import types

MODEL = "gemini-3.8-flash"

_client = None


def _get_client() -> genai.Client:
    """Create the API client once and reuse it."""
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set")
        _client = genai.Client(api_key=api_key)
    return _client


def _extract_json_text(raw: str) -> str:
    """Remove markdown code fences like ```json ... ``` if the model adds them."""
    match = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw.strip()


def ask_json(system: str, user: str, max_tokens: int = 2000) -> dict:
    """
    Send a system prompt and a user message to Gemini.
    Returns the reply as a Python dict.
    Raises ValueError if the reply is not valid JSON.
    """
    response = _get_client().models.generate_content(
        model=MODEL,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system + "\n\nReturn only one valid JSON object. No markdown, no extra text.",
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )

    raw = response.text or ""
    text = _extract_json_text(raw)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model did not return valid JSON: {e}\nRaw reply: {raw[:300]}") from e