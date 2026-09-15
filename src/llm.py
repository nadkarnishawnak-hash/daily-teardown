"""Thin wrapper around the Claude API: web-search-enabled research calls that return JSON."""
import json
import re
import sys

import anthropic

from .config import Config

WEB_TOOLS_MAX_FETCH = 6


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic()  # reads ANTHROPIC_API_KEY


def _tools(cfg: Config, max_searches: int) -> list[dict]:
    return [
        {"type": "web_search_20260209", "name": "web_search", "max_uses": max_searches},
        {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": WEB_TOOLS_MAX_FETCH},
    ]


def _extra(cfg: Config) -> dict:
    # Opus 5 / Sonnet 5 run adaptive thinking by default; effort tunes depth.
    # Haiku 4.5 rejects output_config.effort, so only pass it for models that accept it.
    if "haiku" in cfg.model:
        return {}
    return {"output_config": {"effort": cfg.effort}}


def complete(cfg: Config, system: str, user: str, *, search: bool, max_searches: int | None = None,
             max_tokens: int = 32000) -> str:
    """One research+write turn. Handles pause_turn continuations from server-side tools."""
    client = _client()
    kwargs = dict(model=cfg.model, max_tokens=max_tokens, system=system, **_extra(cfg))
    if search:
        kwargs["tools"] = _tools(cfg, max_searches or cfg.max_searches)
    messages = [{"role": "user", "content": user}]

    response = None
    for _ in range(8):
        with client.messages.stream(messages=messages, **kwargs) as stream:
            response = stream.get_final_message()
        if response.stop_reason == "pause_turn":
            # Server-side tool loop hit its iteration cap; resend to let it continue.
            messages = [messages[0], {"role": "assistant", "content": response.content}]
            continue
        break

    if response is None:
        raise RuntimeError("no response from model")
    if response.stop_reason == "refusal":
        details = getattr(response, "stop_details", None)
        raise RuntimeError(f"model refused: {details}")
    if response.stop_reason == "max_tokens":
        print("warning: response hit max_tokens; JSON may be truncated", file=sys.stderr)

    u = response.usage
    searches = sum(1 for b in response.content if b.type == "server_tool_use" and b.name == "web_search")
    print(f"[llm] {cfg.model} in={u.input_tokens} out={u.output_tokens} searches~{searches} stop={response.stop_reason}",
          file=sys.stderr)
    return "".join(b.text for b in response.content if b.type == "text")


def extract_json(text: str):
    """Pull the JSON object out of a model response (prefers the last ```json block)."""
    candidates = []
    for m in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S):
        candidates.append(m.group(1))
    candidates.reverse()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start:end + 1])
    for c in candidates:
        try:
            return json.loads(c)
        except json.JSONDecodeError:
            continue
    raise ValueError("no valid JSON object found in model output")


def complete_json(cfg: Config, system: str, user: str, *, search: bool, max_searches: int | None = None,
                  max_tokens: int = 32000) -> dict:
    text = complete(cfg, system, user, search=search, max_searches=max_searches, max_tokens=max_tokens)
    try:
        return extract_json(text)
    except ValueError:
        print("[llm] JSON parse failed; asking the model to repair it", file=sys.stderr)
        repaired = complete(
            cfg,
            "You convert text into strictly valid JSON. Output ONLY a single ```json fenced block. "
            "Preserve every field and value; fix only syntax (quotes, commas, escaping).",
            "Repair this into valid JSON:\n\n" + text[-60000:],
            search=False,
            max_tokens=16000,
        )
        return extract_json(repaired)
