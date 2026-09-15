"""Persistent state: teardown log, capture queue, episode list, archetype rotation."""
import json
import re
from pathlib import Path

from .config import DATA

LOG = DATA / "log.json"          # every edition ever produced
QUEUE = DATA / "queue.json"      # businesses you asked for by replying to an email
EPISODES = DATA / "episodes.json"  # podcast episodes (feeds the RSS)
NOTES = DATA / "notes.json"        # notes/sources you asked Jarvis to save; delivered in the next email

# The archetype map, rotated so every model gets covered systematically.
ARCHETYPES = [
    ("razor-and-blades", "cheap or loss-leader base product; the profit is in consumables, refills or add-ons"),
    ("arbitrage", "buy in one market, format or geography and sell in another; the margin is an information or access gap"),
    ("productized service", "a service packaged with fixed scope, fixed price and a repeatable delivery process, sold like a product"),
    ("marketplace", "matches supply and demand, takes a cut, owns neither side's inventory"),
    ("licensing", "rents IP, brand, data, formulas or tech to others at near-zero marginal cost"),
    ("subscription/consumable", "recurring revenue on something that is used up or always-on"),
    ("high-ticket niche", "a small number of customers paying a very high price for deep specialization"),
    ("commoditize-the-complement", "gives away or cheapens the adjacent thing so demand for its own thing rises"),
    ("aggregator", "owns the customer relationship and demand; suppliers come to it on its terms"),
    ("done-for-you", "sells an entire outcome, not a task, at a premium"),
    ("rip-and-rebrand", "takes a proven model or product and re-skins it for a new niche, geography or channel"),
]
ARCHETYPE_NAMES = [a for a, _ in ARCHETYPES]


def load(path: Path, default):
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as f:
        text = f.read().strip()
    return json.loads(text) if text else default


def save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def normalize_archetype(raw: str | None) -> str:
    """Map whatever the model wrote back onto the canonical list where possible."""
    s = (raw or "").strip().lower()
    for name in ARCHETYPE_NAMES:
        if name in s or s in name:
            return name
    compact = re.sub(r"[^a-z]", "", s)
    for name in ARCHETYPE_NAMES:
        if compact and compact == re.sub(r"[^a-z]", "", name):
            return name
    return s or "unclassified"


def next_archetype(log: list[dict]) -> str:
    """Least-recently-used archetype wins; never-used ones go first, in list order."""
    last_used = {name: "" for name in ARCHETYPE_NAMES}
    for entry in sorted(log, key=lambda e: e.get("date", "")):
        a = normalize_archetype(entry.get("archetype"))
        if a in last_used:
            last_used[a] = entry.get("date", "")
    never = [n for n in ARCHETYPE_NAMES if not last_used[n]]
    if never:
        return never[0]
    return min(ARCHETYPE_NAMES, key=lambda n: (last_used[n], ARCHETYPE_NAMES.index(n)))


def recent_archetypes(log: list[dict], n: int = 10) -> list[str]:
    entries = sorted(log, key=lambda e: e.get("date", ""))[-n:]
    return [f"{e.get('date')}: {e.get('archetype')} ({e.get('business')})" for e in entries]


def slugify(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:max_len].strip("-") or "edition"
