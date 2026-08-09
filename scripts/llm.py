#!/usr/bin/env python3
"""
Model routing for the curator.

Two providers, picked by which key is present:

  ANTHROPIC_API_KEY -> Claude Sonnet. Used for editorial judgement — writing
                       decision guides, rewriting weak entry copy. This is
                       comparison and synthesis over a known set of tools,
                       which is exactly the kind of work worth paying for.
  GEMINI_API_KEY    -> Gemini 2.5 Flash. Free tier, and the only provider with
                       Google Search grounding, so it keeps doing discovery
                       (finding tools that launched this week) regardless.

Discovery wants live search; judgement wants a stronger model. The curator
uses whichever is available and degrades to the other rather than failing.
"""
from __future__ import annotations

import json
import os
import re
import sys

ANTHROPIC_MODEL = "claude-sonnet-5"
GEMINI_MODEL = "gemini-2.5-flash"


def have_anthropic() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def have_gemini() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


def active_judgement_model() -> str | None:
    if have_anthropic():
        return f"anthropic:{ANTHROPIC_MODEL}"
    if have_gemini():
        return f"gemini:{GEMINI_MODEL}"
    return None


def _anthropic(prompt: str, max_tokens: int, temperature: float, system: str | None) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    kwargs = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    resp = client.messages.create(**kwargs)
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


def _gemini(prompt: str, max_tokens: int, temperature: float, system: str | None) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    cfg = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        system_instruction=system or None,
    )
    resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=cfg)
    return resp.text or ""


def complete(
    prompt: str,
    *,
    max_tokens: int = 2000,
    temperature: float = 0.3,
    system: str | None = None,
    prefer: str = "judgement",
) -> tuple[str, str]:
    """
    Run a completion. Returns (text, model_used).

    prefer="judgement" tries Claude first; "cheap" tries Gemini first.
    Raises RuntimeError if no provider is configured or both fail.
    """
    order = []
    if prefer == "cheap":
        order = [("gemini", have_gemini), ("anthropic", have_anthropic)]
    else:
        order = [("anthropic", have_anthropic), ("gemini", have_gemini)]

    errors = []
    for name, available in order:
        if not available():
            continue
        try:
            fn = _anthropic if name == "anthropic" else _gemini
            text = fn(prompt, max_tokens, temperature, system)
            if text.strip():
                model = ANTHROPIC_MODEL if name == "anthropic" else GEMINI_MODEL
                return text, f"{name}:{model}"
            errors.append(f"{name}: empty response")
        except Exception as e:  # provider down, quota, bad key — try the next
            errors.append(f"{name}: {type(e).__name__}: {e}")
            print(f"  {name} failed ({type(e).__name__}), trying next provider", file=sys.stderr)

    raise RuntimeError("no LLM provider succeeded: " + "; ".join(errors) if errors
                       else "no LLM provider configured (set ANTHROPIC_API_KEY or GEMINI_API_KEY)")


def complete_json(prompt: str, **kwargs) -> tuple[dict, str]:
    """complete() plus tolerant JSON extraction. Returns (obj, model_used)."""
    text, model = complete(prompt, **kwargs)

    cleaned = re.sub(r"^\s*```(?:json)?\s*\n?", "", text.strip())
    cleaned = re.sub(r"\n?\s*```\s*$", "", cleaned)

    for candidate in (cleaned, text):
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj, model
        except json.JSONDecodeError:
            pass

    # last resort: grab the outermost {...}
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0)), model
        except json.JSONDecodeError:
            pass

    raise ValueError(f"could not parse JSON from {model} response: {text[:400]}")
