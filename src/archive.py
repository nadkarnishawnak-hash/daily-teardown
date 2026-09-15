"""Persistent archive: markdown in the repo + a searchable static site on GitHub Pages."""
import json
from pathlib import Path

from .config import ARCHIVE_MD, DOCS, Config
from .render import esc


def write_markdown(*, date: str, slug: str, kind: str, data: dict, quick: list[dict], audio_url: str | None) -> Path:
    ARCHIVE_MD.mkdir(parents=True, exist_ok=True)
    path = ARCHIVE_MD / f"{date}-{slug}.md"
    lines = []
    if kind == "synthesis":
        lines += [f"# {data.get('title')}", "", f"*{date} · Sunday synthesis*", ""]
        if audio_url:
            lines += [f"Audio: {audio_url}", ""]
        lines += ["## This week", "", data.get("intro", ""), "", "## Recurring principles", ""]
        for p in data.get("principles") or []:
            lines += [f"- **{p.get('principle')}** {p.get('evidence')}"]
        lines += ["", "## How the archetypes relate", "", data.get("archetype_map", ""), "",
                  "## The through-line", "", data.get("through_line", ""), "",
                  "## Try this next week", "", data.get("action", ""), ""]
    else:
        m, hs = data.get("model") or {}, data.get("how_to_start") or {}
        lines += [f"# {data.get('business')}", "",
                  f"*{date} · Archetype: **{data.get('archetype')}** · {data.get('recency', '')}*", "",
                  f"**Hook:** {data.get('subject')}", ""]
        if audio_url:
            lines += [f"Audio: {audio_url}", ""]
        lines += ["## The setup", "", data.get("setup", ""), "", f"> {data.get('guess_prompt', '')}", "",
                  "## The numbers", "", "| | | |", "|---|---|---|"]
        for n in data.get("numbers") or []:
            lines.append(f"| {n.get('label')} | {n.get('value')} | [{n.get('source')}]({n.get('url')}) |")
        lines += ["", "## The model", ""]
        for key, label in [("economic_buyer", "Economic buyer"), ("emotional_driver", "Emotional driver"),
                           ("recurring_vs_one_time", "Recurring vs one-time"), ("margins", "Margins"),
                           ("capital_to_start", "Capital to start"), ("moat", "Moat"), ("distribution", "Distribution")]:
            if m.get(key):
                lines.append(f"- **{label}:** {m.get(key)}")
        lines += ["", "## Why it works", "", data.get("why_it_works", ""), "", "## Where else this shows up", ""]
        for w in data.get("where_else") or []:
            lines.append(f"- **{w.get('name')}**: {w.get('note')}")
        lines += ["", "## How you'd start one today", "", f"- **First step:** {hs.get('first_step')}",
                  f"- **Hardest part:** {hs.get('hardest_part')}", "", "## Takeaway", "", data.get("takeaway", ""), "",
                  f"*Confidence: {data.get('confidence', '')}*", "", "### Sources", ""]
        for s in data.get("sources") or []:
            lines.append(f"- [{s.get('title')}]({s.get('url')}) ({s.get('year', '')})")
    if quick:
        lines += ["", "## What else is moving", ""]
        for it in quick:
            lines.append(f"- **{it.get('what')}** Why it matters: {it.get('why')} [{it.get('source')}]({it.get('url')})")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return path


def write_edition_page(*, date: str, slug: str, html: str) -> tuple[Path, str]:
    """The email HTML doubles as the web page. Returns (path, relative url)."""
    rel = f"editions/{date}-{slug}.html"
    path = DOCS / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path, rel


def write_index(cfg: Config, log: list[dict]) -> Path:
    """Searchable archive index (client-side filter over an embedded JSON list). Also the podcast home page."""
    entries = sorted(log, key=lambda e: e.get("date", ""), reverse=True)
    payload = json.dumps([{
        "date": e.get("date"), "business": e.get("business"), "archetype": e.get("archetype"),
        "subject": e.get("subject"), "takeaway": e.get("takeaway"), "kind": e.get("kind", "teardown"),
        "url": e.get("page_rel"), "audio": e.get("mp3_url"),
    } for e in entries], ensure_ascii=False).replace("</", "<\\/")  # never let content close the <script>
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(cfg.podcast_title)}</title>
<link rel="alternate" type="application/rss+xml" title="{esc(cfg.podcast_title)}" href="feed.xml">
<style>
  :root{{color-scheme:light dark}}
  body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:#f3f4f6;color:#111827}}
  @media (prefers-color-scheme:dark){{body{{background:#0f172a;color:#e5e7eb}} .card{{background:#1e293b!important;border-color:#334155!important}} input{{background:#1e293b;color:#e5e7eb;border-color:#334155!important}} .meta,.take{{color:#94a3b8!important}}}}
  .wrap{{max-width:760px;margin:0 auto;padding:32px 16px}}
  header{{display:flex;gap:18px;align-items:center;margin-bottom:22px}}
  header img{{width:96px;height:96px;border-radius:12px}}
  h1{{margin:0 0 4px;font-size:26px}}
  .sub{{color:#6b7280;font-size:14px}}
  .links a{{margin-right:14px;font-size:14px}}
  input{{width:100%;box-sizing:border-box;padding:12px 14px;font-size:16px;border:1px solid #d1d5db;border-radius:10px;margin:18px 0}}
  .card{{display:block;background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:16px 18px;margin-bottom:12px;text-decoration:none;color:inherit}}
  .card:hover{{border-color:#9ca3af}}
  .meta{{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#6b7280;margin-bottom:4px}}
  .name{{font-size:18px;font-weight:700;margin-bottom:4px}}
  .hook{{font-size:15px;margin-bottom:6px}}
  .take{{font-size:14px;color:#4b5563}}
  .count{{font-size:13px;color:#6b7280;margin-bottom:10px}}
</style></head>
<body><div class="wrap">
<header><img src="cover.png" alt=""><div>
  <h1>{esc(cfg.podcast_title)}</h1>
  <div class="sub">{esc(cfg.podcast_description)}</div>
  <div class="links" style="margin-top:8px"><a href="feed.xml">RSS feed</a><a href="https://github.com/{esc(cfg.github_repo or '')}">Repo</a></div>
</div></header>
<input id="q" type="search" placeholder="Search businesses, archetypes, takeaways..." autofocus>
<div class="count" id="count"></div>
<div id="list"></div>
<script>
const DATA = {payload};
const list = document.getElementById('list'), count = document.getElementById('count'), q = document.getElementById('q');
function esc(s){{return String(s??'').replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));}}
function render(){{
  const term = q.value.trim().toLowerCase();
  const rows = DATA.filter(e => !term || [e.business,e.archetype,e.subject,e.takeaway,e.date].join(' ').toLowerCase().includes(term));
  count.textContent = rows.length + ' edition' + (rows.length===1?'':'s');
  list.innerHTML = rows.map(e => `<a class="card" href="${{esc(e.url||'#')}}">
    <div class="meta">${{esc(e.date)}} &middot; ${{esc(e.kind==='synthesis'?'Sunday synthesis':e.archetype)}}${{e.audio?' &middot; &#9654; audio':''}}</div>
    <div class="name">${{esc(e.business)}}</div>
    <div class="hook">${{esc(e.subject)}}</div>
    <div class="take">${{esc(e.takeaway)}}</div></a>`).join('');
}}
q.addEventListener('input', render); render();
</script>
</div></body></html>"""
    DOCS.mkdir(parents=True, exist_ok=True)
    path = DOCS / "index.html"
    path.write_text(html, encoding="utf-8")
    (DOCS / ".nojekyll").touch()
    return path
