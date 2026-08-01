"""PRAXIS LLM Client — §5, §7.

Wraps Gemini GenAI SDK with structured output support, multi-key rotation,
and local Ollama fallback.
"""

import os
import json
import logging
from typing import Any, Type, TypeVar
import httpx
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import APIError

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger("praxis.llm")

# Model configuration from environment variables
MODEL_HARD = os.environ.get("GEMINI_MODEL_HARD", "gemini-2.5-flash")
MODEL_EASY = os.environ.get("GEMINI_MODEL_EASY", "gemini-2.5-flash")

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")


def get_api_keys() -> list[str]:
    """Retrieve all available Gemini API keys from the environment."""
    keys = []
    # Try multiple key variables
    for key_name in ["GEMINI_API_KEY", "GEMINI_API_KEY_1", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"]:
        val = os.environ.get(key_name)
        if val:
            keys.append(val)
    return keys


# Global key rotation state
_current_key_idx = 0


def get_next_client() -> tuple[genai.Client, str] | None:
    """Retrieve the next Gemini client based on key rotation."""
    global _current_key_idx
    keys = get_api_keys()
    if not keys:
        return None

    # Rotate
    _current_key_idx = _current_key_idx % len(keys)
    key = keys[_current_key_idx]
    _current_key_idx += 1

    try:
        # Initialize Google GenAI client
        client = genai.Client(api_key=key)
        return client, key
    except Exception as e:
        logger.error(f"Failed to initialize GenAI client with key index {_current_key_idx - 1}: {e}")
        return None


def call_ollama_fallback(prompt: str, schema: Type[T]) -> T:
    """Call local Ollama service as fallback when Gemini is unavailable."""
    logger.info(f"Invoking Ollama fallback ({OLLAMA_MODEL}) on {OLLAMA_BASE_URL}...")
    
    # We construct a system prompt instructing Ollama to output strictly valid JSON
    # matching the Pydantic schema structure.
    schema_json = json.dumps(schema.model_json_schema(), indent=2)
    system_prompt = (
        f"You are a structured parser. You must respond ONLY with a raw JSON object matching this schema:\n{schema_json}\n"
        "Do not include any introductory text, markdown formatting blocks (like ```json), or trailing notes. Output raw JSON only."
    )

    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "format": "json"  # Instruct Ollama to format output as JSON
    }

    try:
        response = httpx.post(url, json=payload, timeout=30.0)
        response.raise_for_status()
        result_json = response.json()
        content = result_json["message"]["content"]
        
        # Strip code blocks if Ollama ignored the system prompt
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        return schema.model_validate_json(content)
    except Exception as e:
        logger.error(f"Ollama fallback execution failed: {e}")
        raise RuntimeError("Both Gemini and Ollama fallback services failed.") from e


def generate_structured_output(
    prompt: str,
    response_schema: Type[T],
    model_tier: str = "hard",
    retries: int = 1
) -> T:
    """Generate structured output from the LLM, validating it against response_schema.

    Rotates API keys on 403/429 limits, retries on schema verification errors,
    and falls back to Ollama if all cloud keys are exhausted.
    """
    model_name = MODEL_HARD if model_tier == "hard" else MODEL_EASY
    keys = get_api_keys()

    if not keys:
        # If no Gemini keys are present, skip directly to local Ollama fallback
        return call_ollama_fallback(prompt, response_schema)

    last_error = None
    # We attempt up to the number of keys we have, plus retries for parsing errors
    for attempt in range(len(keys) * (retries + 1)):
        client_info = get_next_client()
        if not client_info:
            continue
        
        client, key = client_info

        try:
            # Native structured output via gemini client
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
            )
            
            # The response text should already be valid JSON conforming to the schema
            text = response.text
            if not text:
                raise ValueError("Received empty response from Gemini model.")
                
            return response_schema.model_validate_json(text)

        except (APIError, httpx.HTTPStatusError) as e:
            # 403, 429, or general API errors -> rotate key and retry next loop
            logger.warning(f"Gemini API error (key rotated): {e}")
            last_error = e
            continue
        except Exception as e:
            # Validation error or value error -> retry within key or fail
            logger.warning(f"Content structure parsing failure (attempt {attempt + 1}): {e}")
            last_error = e
            # If it's a structural parsing error, we try again
            continue

    # If all keys/attempts failed, execute local Ollama fallback
    logger.warning("All Gemini API keys exhausted or failed. Falling back to Ollama.")
    return call_ollama_fallback(prompt, response_schema)
