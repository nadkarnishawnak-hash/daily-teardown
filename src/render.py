"""Renders the HTML email (also reused as the archive page) and a plain-text fallback."""
import html
import re

# Inline styles only: email clients strip <style> blocks unpredictably.
_P = 'style="margin:0 0 14px;font-size:16px;line-height:1.55;color:#1f2937"'
_H2 = ('style="margin:30px 0 10px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;'
       'color:#6b7280;font-weight:700"')
_LI = 'style="margin:0 0 10px;font-size:16px;line-height:1.5;color:#1f2937"'
_SMALL = 'style="font-size:13px;line-height:1.5;color:#6b7280"'
_LINK = 'style="color:#1d4ed8;text-decoration:underline"'


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def inline(s) -> str:
    """Escape, then allow **bold** and *italic* only."""
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    return s


def paras(s) -> str:
    chunks = [c.strip() for c in re.split(r"\n\s*\n", str(s or "")) if c.strip()]
    return "".join(f"<p {_P}>{inline(c)}</p>" for c in chunks)


def h2(text: str) -> str:
    return f"<h2 {_H2}>{esc(text)}</h2>"


def link(url: str, text: str | None = None) -> str:
    url = str(url or "").strip()
    if not url.startswith(("http://", "https://")):
        return esc(text or url)
    return f'<a href="{esc(url)}" {_LINK}>{esc(text or url)}</a>'


def _shell(*, title: str, header_line: str, body: str, footer: str) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title></head>
<body style="margin:0;padding:0;background:#f3f4f6;-webkit-font-smoothing:antialiased">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f3f4f6"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:640px;background:#ffffff;border-radius:10px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif">
<tr><td style="padding:22px 28px 0">
  <div style="font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:#9ca3af;font-weight:700">{header_line}</div>
</td></tr>
<tr><td style="padding:8px 28px 28px">
{body}
</td></tr>
<tr><td style="padding:18px 28px 26px;border-top:1px solid #e5e7eb">
{footer}
</td></tr>
</table>
</td></tr></table>
</body></html>"""


def _audio_box(audio_url: str | None, duration: str | None, feed_url: str, archive_url: str | None,
               jarvis_url: str | None = None) -> str:
    if audio_url:
        primary = (f'<a href="{esc(audio_url)}" style="display:inline-block;background:#111827;color:#ffffff;'
                   f'text-decoration:none;font-weight:700;font-size:15px;padding:11px 18px;border-radius:8px">'
                   f'&#9654;&nbsp; Listen to this edition{(" (" + duration + ")") if duration else ""}</a>')
        if jarvis_url:
            primary += (f' <a href="{esc(jarvis_url)}" style="display:inline-block;background:#f59e0b;color:#111827;'
                        f'text-decoration:none;font-weight:700;font-size:15px;padding:11px 18px;border-radius:8px;'
                        f'margin-left:8px">&#127908;&nbsp; Talk to Jarvis</a>')
    else:
        primary = '<span style="font-size:14px;color:#6b7280">Audio unavailable for this edition.</span>'
    parts = [f'<a href="{esc(feed_url)}" {_LINK}>Podcast feed</a>']
    if archive_url:
        parts.append(f'<a href="{esc(archive_url)}" {_LINK}>Web version</a>')
    return (f'<div style="margin:18px 0 6px;padding:16px 18px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px">'
            f'{primary}<div style="margin-top:10px;font-size:13px;color:#6b7280">{" &middot; ".join(parts)}</div></div>')


def _quickhits(items: list[dict]) -> str:
    if not items:
        return ""
    lane_names = {"ai": "AI", "startup": "Startups", "dtc": "DTC / Marketing"}
    rows = []
    for it in items:
        lane = lane_names.get(str(it.get("lane", "")).lower(), "News")
        src = " · ".join(x for x in [it.get("source"), it.get("date")] if x)
        rows.append(
            f'<li {_LI}><span style="font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;'
            f'color:#6b7280">{esc(lane)}</span><br>{inline(it.get("what"))}'
            f'<br><span style="color:#4b5563">Why it matters: {inline(it.get("why"))}</span>'
            f'<br><span {_SMALL}>{link(it.get("url"), src or "source")}</span></li>')
    return h2("What else is moving") + f'<ul style="padding-left:20px;margin:0">{"".join(rows)}</ul>'


def _notes(notes: list[dict]) -> str:
    """Notes and sources you asked Jarvis to save during yesterday's session."""
    if not notes:
        return ""
    rows = []
    for n in notes:
        extra = f' <span {_SMALL}>{link(n["url"], "source")}</span>' if n.get("url") else ""
        when = f' <span {_SMALL}>({esc(n.get("edition") or n.get("created", "")[:10])})</span>'
        rows.append(f'<li {_LI}>{inline(n.get("text"))}{extra}{when}</li>')
    return h2("From your Jarvis session") + f'<ul style="padding-left:20px;margin:0">{"".join(rows)}</ul>'


def _footer(cfg, archive_index_url: str) -> str:
    return (f'<div {_SMALL}>Want a specific business torn down? <strong>Reply to this email</strong> with a company name '
            f'or link and it gets queued for a future edition.<br>'
            f'Archive &amp; search: {link(archive_index_url, archive_index_url)}<br>'
            f'Podcast feed (Spotify / Apple / Pocket Casts): {link(cfg.feed_url, cfg.feed_url)}</div>')


def render_teardown(t: dict, quick: list[dict], *, cfg, date_long: str, audio_url: str | None,
                    duration: str | None, archive_url: str | None, archive_index_url: str,
                    notes: list[dict] | None = None) -> str:
    m = t.get("model") or {}
    hs = t.get("how_to_start") or {}

    numbers_rows = "".join(
        f'<tr><td style="padding:9px 10px;border-bottom:1px solid #e5e7eb;font-size:14px;color:#6b7280;'
        f'white-space:nowrap;vertical-align:top">{esc(n.get("label"))}</td>'
        f'<td style="padding:9px 10px;border-bottom:1px solid #e5e7eb;font-size:15px;color:#111827;vertical-align:top">'
        f'{inline(n.get("value"))}<br><span {_SMALL}>{link(n.get("url"), n.get("source") or "source")}</span></td></tr>'
        for n in (t.get("numbers") or []))

    model_rows = "".join(
        f'<tr><td style="padding:7px 10px 7px 0;font-size:13px;color:#6b7280;white-space:nowrap;vertical-align:top">{esc(label)}</td>'
        f'<td style="padding:7px 0;font-size:15px;line-height:1.5;color:#1f2937;vertical-align:top">{inline(m.get(key))}</td></tr>'
        for key, label in [("economic_buyer", "Economic buyer"), ("emotional_driver", "Emotional driver"),
                           ("recurring_vs_one_time", "Recurring vs one-time"), ("margins", "Margins"),
                           ("capital_to_start", "Capital to start"), ("moat", "Moat"), ("distribution", "Distribution")]
        if m.get(key))

    where_else = "".join(f'<li {_LI}><strong>{esc(w.get("name"))}</strong>: {inline(w.get("note"))}</li>'
                         for w in (t.get("where_else") or []))
    sources = "".join(f'<li {_SMALL}>{link(s.get("url"), s.get("title") or s.get("url"))}'
                      f'{(" (" + esc(s.get("year")) + ")") if s.get("year") else ""}</li>'
                      for s in (t.get("sources") or []))

    body = f"""
{_audio_box(audio_url, duration, cfg.feed_url, archive_url, cfg.jarvis_url)}
<h1 style="margin:18px 0 6px;font-size:26px;line-height:1.2;color:#111827">{esc(t.get("business"))}</h1>
<div style="font-size:15px;color:#4b5563;margin-bottom:4px">{inline(t.get("subject"))}</div>
<div {_SMALL}>Archetype: <strong>{esc(t.get("archetype"))}</strong>{(" &middot; " + inline(t.get("recency"))) if t.get("recency") else ""}
{(" &middot; " + link(t.get("url"), "site")) if t.get("url") else ""}</div>

{h2("The setup")}
{paras(t.get("setup"))}
<div style="margin:14px 0 6px;padding:14px 16px;background:#fffbeb;border-left:4px solid #f59e0b;border-radius:6px">
  <div style="font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#b45309;margin-bottom:6px">Your call before you scroll</div>
  <div style="font-size:16px;line-height:1.5;color:#1f2937">{inline(t.get("guess_prompt"))}</div>
</div>
<div style="text-align:center;color:#9ca3af;font-size:13px;padding:22px 0 6px">&#9660; &nbsp;guessed? keep going&nbsp; &#9660;</div>

{h2("The numbers")}
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-top:1px solid #e5e7eb">{numbers_rows}</table>

{h2("The model")}
<table role="presentation" width="100%" cellspacing="0" cellpadding="0">{model_rows}</table>

{h2("Why it works")}
{paras(t.get("why_it_works"))}

{h2("Where else this shows up")}
<ul style="padding-left:20px;margin:0">{where_else}</ul>

{h2("How you'd start one today")}
<p {_P}><strong>First step:</strong> {inline(hs.get("first_step"))}</p>
<p {_P}><strong>Hardest part:</strong> {inline(hs.get("hardest_part"))}</p>

{h2("Takeaway")}
<div style="padding:16px 18px;background:#eef2ff;border-radius:8px;font-size:17px;line-height:1.5;color:#1e1b4b;font-weight:600">{inline(t.get("takeaway"))}</div>

<p style="margin:16px 0 0;font-size:13px;line-height:1.5;color:#6b7280"><strong>Confidence:</strong> {inline(t.get("confidence"))}</p>
<ul style="padding-left:18px;margin:8px 0 0">{sources}</ul>

{_quickhits(quick)}
{_notes(notes or [])}
"""
    return _shell(title=f'{t.get("business")} - {cfg.podcast_title}',
                  header_line=f'{esc(cfg.podcast_title)} &middot; {esc(date_long)}',
                  body=body, footer=_footer(cfg, archive_index_url))


def render_synthesis(s: dict, quick: list[dict], *, cfg, date_long: str, audio_url: str | None,
                     duration: str | None, archive_url: str | None, archive_index_url: str,
                     week: list[dict], notes: list[dict] | None = None) -> str:
    week_rows = "".join(
        f'<li {_LI}><strong>{esc(e.get("business"))}</strong> <span {_SMALL}>({esc(e.get("archetype"))}, {esc(e.get("date"))})</span>'
        f'{(" &middot; " + link(e.get("archive_url"), "read")) if e.get("archive_url") else ""}<br>'
        f'<span style="color:#4b5563">{inline(e.get("takeaway"))}</span></li>' for e in week)
    principles = "".join(
        f'<li {_LI}><strong>{inline(p.get("principle"))}</strong><br><span style="color:#4b5563">{inline(p.get("evidence"))}</span></li>'
        for p in (s.get("principles") or []))
    body = f"""
{_audio_box(audio_url, duration, cfg.feed_url, archive_url, cfg.jarvis_url)}
<h1 style="margin:18px 0 6px;font-size:26px;line-height:1.2;color:#111827">{esc(s.get("title"))}</h1>
<div style="font-size:15px;color:#4b5563">{inline(s.get("subject"))}</div>

{h2("This week")}
{paras(s.get("intro"))}
<ul style="padding-left:20px;margin:0">{week_rows}</ul>

{h2("Recurring principles")}
<ol style="padding-left:22px;margin:0">{principles}</ol>

{h2("How the archetypes relate")}
{paras(s.get("archetype_map"))}

{h2("The through-line")}
<div style="padding:16px 18px;background:#eef2ff;border-radius:8px;font-size:17px;line-height:1.5;color:#1e1b4b;font-weight:600">{inline(s.get("through_line"))}</div>

{h2("Try this next week")}
{paras(s.get("action"))}

{_quickhits(quick)}
{_notes(notes or [])}
"""
    return _shell(title=f'{s.get("title")} - {cfg.podcast_title}',
                  header_line=f'{esc(cfg.podcast_title)} &middot; Sunday synthesis &middot; {esc(date_long)}',
                  body=body, footer=_footer(cfg, archive_index_url))


def render_text(script: str, quick: list[dict], *, audio_url: str | None, feed_url: str) -> str:
    """Plain-text alternative for clients that don't render HTML."""
    lines = []
    if audio_url:
        lines += [f"Listen: {audio_url}", f"Podcast feed: {feed_url}", ""]
    lines += [script.strip(), ""]
    if quick:
        lines += ["WHAT ELSE IS MOVING", ""]
        for it in quick:
            lines += [f"- {it.get('what')}", f"  Why: {it.get('why')}", f"  {it.get('url')}", ""]
    lines += ["Reply with a business name or link to queue it for a future teardown."]
    return "\n".join(lines)
