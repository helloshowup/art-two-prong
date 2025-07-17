"""OpenAI chat completion client utilities."""

from __future__ import annotations

from typing import Iterable
import base64
import time

import openai

from .config import OPENAI_API_KEY

# Instantiate a single client for reuse
_client = openai.OpenAI(api_key=OPENAI_API_KEY)


def _chat_request(
    messages: Iterable[dict],
    model: str,
    temperature: float,
    max_tokens: int | None = None,
):
    """Send a chat completion request with retry logic."""
    last_exc: Exception | None = None
    for attempt in range(4):
        try:
            params = dict(model=model, messages=list(messages), temperature=temperature)
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            response = _client.chat.completions.create(**params)
            return response.choices[0].message.content
        except openai.RateLimitError as exc:
            last_exc = exc
        except openai.APIStatusError as exc:
            last_exc = exc
            if exc.status_code not in {429, 502}:
                raise
        except openai.APIConnectionError as exc:
            last_exc = exc
        if attempt < 3:
            time.sleep(2**attempt)
    # If we fall through, raise the last captured exception
    if last_exc:
        raise last_exc
    raise RuntimeError("Unknown error sending prompt")


def send_prompt(
    prompt: str,
    content: str,
    model: str,
    max_tokens: int | None,
) -> str:
    """Send `content` with a system `prompt` and return the assistant message text."""
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": content},
    ]
    return _chat_request(messages, model=model, temperature=1, max_tokens=max_tokens)


def generate_image(
    prompt: str, model: str = "dall-e-3", size: str = "1024x1024"
) -> bytes:
    """Return image bytes generated from *prompt* using the OpenAI image API."""
    # newer OpenAI client doesn't accept ``response_format``; default returns URLs
    resp = openai.Image.create(
        prompt=prompt,
        model=model,
        size=size,
    )
    node = resp["data"][0]
    if "url" in node:
        import requests
        return requests.get(node["url"]).content
    if "b64_json" in node:
        return base64.b64decode(node["b64_json"])
    raise RuntimeError("No image data in API response")
