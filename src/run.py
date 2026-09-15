"""Produce one edition end to end: research -> email HTML -> audio -> podcast feed -> archive -> send.

    python -m src.run                 # full edition (needs ANTHROPIC_API_KEY + Gmail vars); no upload
    python -m src.run --publish       # also upload the MP3 to GitHub Releases (needs GITHUB_REPOSITORY/TOKEN)
    python -m src.run --fixture       # skip the LLM, use sample/ JSON (tests email + audio + feed for $0)
    python -m src.run --no-email --no-audio   # just render to out/
"""
import argparse
import hashlib
import json
import sys
import uuid
from datetime import datetime, timedelta

from . import archive, capture, content, mailer, podcast, render, tts
from .config import DOCS, ET, OUT, SAMPLE, Config
from .store import EPISODES, LOG, NOTES, QUEUE, load, next_archetype, recent_archetypes, save, slugify


def parse_args():
    p = argparse.ArgumentParser(description="Build and send one edition of The Daily Teardown.")
    p.add_argument("--publish", action="store_true", help="upload MP3 to GitHub Releases (else audio link is local)")
    p.add_argument("--fixture", action="store_true", help="use sample/*.json instead of calling the model")
    p.add_argument("--force", action="store_true", help="regenerate even if today's edition already exists")
    p.add_argument("--no-email", action="store_true")
    p.add_argument("--no-audio", action="store_true")
    p.add_argument("--no-capture", action="store_true", help="skip reading email replies")
    p.add_argument("--synthesis", action="store_true", help="force a Sunday-style synthesis edition")
    p.add_argument("--date", help="override today's date (YYYY-MM-DD), for testing")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    cfg = Config()
    now = datetime.now(ET)
    if args.date:
        now = datetime.fromisoformat(args.date).replace(hour=7, tzinfo=ET)
    today = now.date().isoformat()
    date_long, _ = content.date_strings(now)

    log = load(LOG, [])
    queue = load(QUEUE, [])
    episodes = load(EPISODES, [])
    notes = load(NOTES, [])
    pending_notes = [n for n in notes if not n.get("included")]

    if any(e["date"] == today for e in episodes) and not args.force:
        print(f"Edition for {today} already exists; nothing to do (use --force to regenerate).")
        return 0

    # 1. Capture loop: pull any businesses you replied with since last run.
    if not args.no_capture and not args.fixture:
        new = capture.fetch_requests(cfg)
        if new:
            queue.extend(new)
            save(QUEUE, queue)

    # 2. Decide what kind of edition today is.
    week_start = (now - timedelta(days=7)).date().isoformat()
    week = [e for e in log if e.get("kind", "teardown") == "teardown" and week_start < e.get("date", "") <= today]
    is_sunday = now.weekday() == 6
    if args.synthesis or (is_sunday and len(week) >= 2):
        kind = "synthesis"
    elif queue:
        kind = "requested"
    else:
        kind = "teardown"
    print(f"[run] {today} ({date_long}) -> {kind} edition", file=sys.stderr)

    # 3. Generate content.
    excluded = sorted({e["business"] for e in log if e.get("business")})
    requested = queue[0]["request"] if kind == "requested" else None
    archetype = None if kind != "teardown" else next_archetype(log)

    if args.fixture:
        data = load(SAMPLE / ("synthesis.json" if kind == "synthesis" else "teardown.json"), {})
        quick = load(SAMPLE / "quickhits.json", {}).get("items", [])
        if kind != "synthesis":
            data["archetype"] = data.get("archetype") or archetype
    elif kind == "synthesis":
        data = content.generate_synthesis(cfg, now=now, entries=week)
        quick = content.generate_quickhits(cfg, now=now)
    else:
        data = content.generate_teardown(cfg, now=now, archetype=archetype, excluded=excluded,
                                         recent=recent_archetypes(log), requested=requested)
        quick = content.generate_quickhits(cfg, now=now)

    title = data.get("title") if kind == "synthesis" else data.get("business")
    subject = data["subject"]
    slug = slugify("sunday-synthesis" if kind == "synthesis" else title)
    ep_title = f"Weekly synthesis: {data.get('title')}" if kind == "synthesis" \
        else f"{title} ({data.get('archetype')})"

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{today}-{slug}.json").write_text(json.dumps({"kind": kind, "data": data, "quick": quick}, indent=2,
                                                          ensure_ascii=False), encoding="utf-8")

    # 4. Audio.
    audio_url, duration_str, audio_meta = None, None, {}
    mp3 = OUT / f"{today}-{slug}.mp3"
    if not args.no_audio:
        try:
            audio_meta = tts.synthesize(cfg, data["audio_script"], mp3)
            duration_str = tts.fmt_duration(audio_meta["duration_sec"])
            if args.publish and cfg.can_publish():
                # Fixture runs go to a throwaway "test" release so the test email has a playable link;
                # the feed is built from episodes.json, which fixture runs never touch.
                audio_url = podcast.upload_mp3(cfg, tag="test" if args.fixture else f"ep-{today}",
                                               title="Test audio" if args.fixture else ep_title,
                                               notes=data.get("takeaway") or data.get("through_line") or "",
                                               mp3=mp3)
            else:
                audio_url = mp3.resolve().as_uri()
                print(f"[run] not publishing; audio at {audio_url}", file=sys.stderr)
        except Exception as e:  # a voice failure must never kill the email
            print(f"[run] audio failed: {e}", file=sys.stderr)
            audio_url, audio_meta = None, {}

    # 5. Render email (also becomes the archive page).
    page_rel = f"editions/{today}-{slug}.html"
    page_url = cfg.site_url + page_rel
    index_url = cfg.site_url
    published_audio = audio_url if (audio_url and audio_url.startswith("http")) else None
    if kind == "synthesis":
        for e in week:
            e["archive_url"] = cfg.site_url + e["page_rel"] if e.get("page_rel") else None
        html = render.render_synthesis(data, quick, cfg=cfg, date_long=date_long, audio_url=audio_url,
                                       duration=duration_str, archive_url=page_url, archive_index_url=index_url,
                                       week=week, notes=pending_notes)
    else:
        html = render.render_teardown(data, quick, cfg=cfg, date_long=date_long, audio_url=audio_url,
                                      duration=duration_str, archive_url=page_url, archive_index_url=index_url,
                                      notes=pending_notes)
    text = render.render_text(data["audio_script"], quick, audio_url=audio_url, feed_url=cfg.feed_url)
    (OUT / f"{today}-{slug}.html").write_text(html, encoding="utf-8")

    # Fixture runs are for testing delivery only: never touch the real log, feed or archive.
    if args.fixture:
        if not args.no_email and cfg.can_email():
            mailer.send(cfg, subject=f"[TEST] {subject}", html=html, text=text)
        print(f"Fixture run complete (nothing persisted). Preview: {OUT / (today + '-' + slug + '.html')}")
        print(f"  audio: {audio_url or 'none'}")
        return 0

    # 6. Archive + podcast feed (files under docs/ and archive/ get committed by the workflow).
    archive.write_markdown(date=today, slug=slug, kind=kind, data=data, quick=quick, audio_url=published_audio)
    archive.write_edition_page(date=today, slug=slug, html=html)
    podcast.ensure_cover(cfg)

    # Structured copy of the edition for the Odin voice page (+ pointer to the latest one).
    edition_rel = f"editions/{today}-{slug}.json"
    save(DOCS / edition_rel, {
        "date": today, "kind": kind, "title": title, "archetype": data.get("archetype", "synthesis"),
        "mp3_url": published_audio, "page_url": page_url, "duration_sec": audio_meta.get("duration_sec", 0),
        "data": data, "quick": quick,
    })
    save(DOCS / "latest.json", {"date": today, "slug": slug, "title": title, "kind": kind,
                                "archetype": data.get("archetype", "synthesis"), "json_url": edition_rel,
                                "mp3_url": published_audio, "page_url": page_url})
    if cfg.odin_worker_url:
        save(DOCS / "odin-config.json", {"workerUrl": cfg.odin_worker_url.rstrip("/")})

    if published_audio:
        description = (data.get("setup") or data.get("intro") or "").strip()
        if data.get("takeaway"):
            description += f"\n\nTakeaway: {data['takeaway']}"
        description += f"\n\nRead it: {page_url}"
        episodes = [e for e in episodes if e["date"] != today]
        episodes.append({
            "date": today, "title": ep_title, "slug": slug, "kind": kind, "description": description,
            "mp3_url": published_audio, "bytes": audio_meta.get("bytes", 0),
            "duration_sec": audio_meta.get("duration_sec", 0), "page_url": page_url,
            "guid": f"{cfg.github_repo or 'local'}:{today}:{hashlib.sha1(slug.encode()).hexdigest()[:10]}",
            "pub_date": now.isoformat(), "tts": audio_meta.get("provider"),
        })
        save(EPISODES, episodes)
    podcast.write_feed(cfg, episodes)

    # 7. Log (read before picking, appended after) and queue.
    log = [e for e in log if e["date"] != today]
    log.append({
        "date": today, "kind": kind, "business": title, "archetype": data.get("archetype", "synthesis"),
        "subject": subject, "takeaway": data.get("takeaway") or data.get("through_line", ""),
        "recency": data.get("recency", ""), "confidence": data.get("confidence", ""),
        "url": data.get("url", ""), "page_rel": page_rel, "mp3_url": published_audio,
        "requested": requested, "id": str(uuid.uuid4())[:8],
    })
    archive.write_index(cfg, log)
    save(DOCS / "log.json", [{k: e.get(k) for k in ("date", "kind", "business", "archetype", "subject", "takeaway",
                                                     "page_rel", "mp3_url")} for e in log])

    # 8. Send. Do this last so a failed send leaves no half-committed state.
    if not args.no_email:
        if not cfg.can_email():
            print("[run] GMAIL_ADDRESS / GMAIL_APP_PASSWORD not set; skipping email", file=sys.stderr)
        else:
            mailer.send(cfg, subject=subject, html=html, text=text)

    save(LOG, log)
    if kind == "requested":
        save(QUEUE, queue[1:])
    if pending_notes:
        for n in notes:
            n["included"] = True
        save(NOTES, notes)
    print(f"Done: {kind} edition for {today} -> {title}")
    print(f"  email:   {'sent to ' + cfg.recipient if (not args.no_email and cfg.can_email()) else 'skipped'}")
    print(f"  audio:   {audio_url or 'none'}")
    print(f"  page:    {page_url}")
    print(f"  feed:    {cfg.feed_url}")
    print(f"  preview: {OUT / (today + '-' + slug + '.html')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
