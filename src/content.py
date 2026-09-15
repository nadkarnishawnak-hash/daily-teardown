"""Generates the three content types by calling the LLM with the prompts."""
import sys
from datetime import datetime

from . import prompts
from .config import Config
from .llm import complete_json
from .store import normalize_archetype

REQUIRED_TEARDOWN_KEYS = ["business", "subject", "setup", "guess_prompt", "numbers", "model",
                          "why_it_works", "where_else", "how_to_start", "takeaway", "sources", "audio_script"]


def date_strings(now: datetime) -> tuple[str, str]:
    """('Monday, September 14, 2026', 'Monday, September fourteenth, twenty twenty-six')"""
    long = now.strftime("%A, %B %d, %Y").replace(" 0", " ")
    ordinals = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth", 7: "seventh",
                8: "eighth", 9: "ninth", 10: "tenth", 11: "eleventh", 12: "twelfth", 13: "thirteenth",
                14: "fourteenth", 15: "fifteenth", 16: "sixteenth", 17: "seventeenth", 18: "eighteenth",
                19: "nineteenth", 20: "twentieth", 21: "twenty-first", 22: "twenty-second", 23: "twenty-third",
                24: "twenty-fourth", 25: "twenty-fifth", 26: "twenty-sixth", 27: "twenty-seventh",
                28: "twenty-eighth", 29: "twenty-ninth", 30: "thirtieth", 31: "thirty-first"}
    # 2026 -> "twenty twenty-six"
    tens = {20: "twenty", 30: "thirty", 40: "forty"}
    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    yy = now.year % 100
    if yy < 10:
        year_spoken = f"twenty oh-{ones[yy]}" if yy else "twenty twenty"
    else:
        year_spoken = f"twenty {tens.get(yy - yy % 10, str(yy - yy % 10))}" + (f"-{ones[yy % 10]}" if yy % 10 else "")
    spoken = f"{now.strftime('%A')}, {now.strftime('%B')} {ordinals[now.day]}, {year_spoken}"
    return long, spoken


def generate_teardown(cfg: Config, *, now: datetime, archetype: str | None, excluded: list[str],
                      recent: list[str], requested: str | None) -> dict:
    date_long, date_spoken = date_strings(now)
    user = prompts.teardown_user(date_long=date_long, date_spoken=date_spoken, archetype=archetype,
                                 excluded=excluded, recent=recent, requested=requested)
    for attempt in range(2):
        data = complete_json(cfg, prompts.TEARDOWN_SYSTEM, user, search=True)
        missing = [k for k in REQUIRED_TEARDOWN_KEYS if not data.get(k)]
        if not missing and data["business"].strip().lower() not in {e.lower() for e in excluded}:
            break
        print(f"[content] teardown attempt {attempt + 1} rejected (missing={missing}); retrying", file=sys.stderr)
        user += "\n\nYour previous attempt was rejected: " + (
            f"missing fields {missing}." if missing else "it repeated an excluded business. Pick a different one.")
    else:
        raise RuntimeError("could not produce a valid teardown")
    data["archetype"] = normalize_archetype(data.get("archetype") or archetype)
    data.setdefault("confidence", "Not stated.")
    return data


def generate_synthesis(cfg: Config, *, now: datetime, entries: list[dict]) -> dict:
    date_long, date_spoken = date_strings(now)
    user = prompts.synthesis_user(date_long=date_long, date_spoken=date_spoken, entries=entries)
    data = complete_json(cfg, prompts.SYNTHESIS_SYSTEM, user, search=False, max_tokens=16000)
    for k in ["subject", "title", "intro", "principles", "through_line", "audio_script"]:
        if not data.get(k):
            raise RuntimeError(f"synthesis missing field: {k}")
    data.setdefault("archetype_map", "")
    data.setdefault("action", "")
    return data


def generate_quickhits(cfg: Config, *, now: datetime) -> list[dict]:
    date_long, _ = date_strings(now)
    try:
        data = complete_json(cfg, prompts.QUICKHITS_SYSTEM, prompts.quickhits_user(date_long=date_long),
                             search=True, max_searches=8, max_tokens=8000)
        items = data.get("items") or []
        return [i for i in items if i.get("what") and i.get("url")][:6]
    except Exception as e:  # the digest is nice-to-have; never block the teardown on it
        print(f"[content] quick hits failed: {e}", file=sys.stderr)
        return []
