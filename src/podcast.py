"""Podcast plumbing: cover art, MP3 hosting on GitHub Releases, and the RSS feed on GitHub Pages."""
import sys
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

import requests

from .config import DOCS, Config

GITHUB_API = "https://api.github.com"


# ------------------------------------------------------------------ cover art

def ensure_cover(cfg: Config, path: Path = DOCS / "cover.png") -> Path:
    """Podcast directories require square art between 1400 and 3000 px. Generate once, keep forever."""
    if path.exists():
        return path
    from PIL import Image, ImageDraw, ImageFont

    size = 1400
    img = Image.new("RGB", (size, size), "#111827")
    d = ImageDraw.Draw(img)
    # Subtle diagonal band
    d.polygon([(0, 980), (size, 700), (size, size), (0, size)], fill="#1f2937")
    d.rectangle([(90, 90), (190, 190)], fill="#f59e0b")

    def font(sz):
        try:
            return ImageFont.truetype("DejaVuSans-Bold.ttf", sz)
        except OSError:
            return ImageFont.load_default(size=sz)

    words = cfg.podcast_title.upper().split()
    y = 330
    for w in words:
        d.text((90, y), w, fill="#ffffff", font=font(170))
        y += 190
    d.text((90, y + 40), "ONE REAL BUSINESS. EVERY MORNING.", fill="#f59e0b", font=font(52))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG", optimize=True)
    print(f"[podcast] generated cover art at {path}", file=sys.stderr)
    return path


# ------------------------------------------------------------------ MP3 hosting (GitHub Releases)

def _headers(cfg: Config) -> dict:
    return {"Authorization": f"Bearer {cfg.github_token}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"}


def upload_mp3(cfg: Config, *, tag: str, title: str, notes: str, mp3: Path) -> str:
    """Attach the MP3 to a release tagged `tag`; returns the permanent download URL.

    Release assets are free, unmetered for public repos, support HTTP range requests, and keep the git
    history free of binaries. The URL is deterministic, so a re-run replaces the asset in place.
    """
    repo, h = cfg.github_repo, _headers(cfg)
    r = requests.get(f"{GITHUB_API}/repos/{repo}/releases/tags/{tag}", headers=h, timeout=60)
    if r.status_code == 404:
        r = requests.post(f"{GITHUB_API}/repos/{repo}/releases", headers=h, timeout=60,
                          json={"tag_name": tag, "name": title, "body": notes, "make_latest": "false"})
    r.raise_for_status()
    release = r.json()

    for asset in release.get("assets", []):
        if asset["name"] == mp3.name:
            requests.delete(asset["url"], headers=h, timeout=60).raise_for_status()

    upload_url = release["upload_url"].split("{")[0]
    with open(mp3, "rb") as f:
        r = requests.post(upload_url, headers={**h, "Content-Type": "audio/mpeg"}, params={"name": mp3.name},
                          data=f, timeout=600)
    r.raise_for_status()
    return f"https://github.com/{repo}/releases/download/{tag}/{mp3.name}"


# ------------------------------------------------------------------ RSS

def _fmt_duration(seconds: int) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def build_feed(cfg: Config, episodes: list[dict]) -> str:
    """Standards-compliant RSS 2.0 + iTunes namespace (what Spotify, Apple and Pocket Casts read)."""
    items = []
    for ep in sorted(episodes, key=lambda e: e["date"], reverse=True):
        if not ep.get("mp3_url"):
            continue
        pub = datetime.fromisoformat(ep["pub_date"])
        items.append(f"""    <item>
      <title>{escape(ep["title"])}</title>
      <itunes:title>{escape(ep["title"])}</itunes:title>
      <description>{escape(ep.get("description", ""))}</description>
      <itunes:summary>{escape(ep.get("description", ""))}</itunes:summary>
      <link>{escape(ep.get("page_url") or cfg.site_url)}</link>
      <guid isPermaLink="false">{escape(ep["guid"])}</guid>
      <pubDate>{format_datetime(pub)}</pubDate>
      <enclosure url="{escape(ep["mp3_url"])}" length="{int(ep.get("bytes", 0))}" type="audio/mpeg"/>
      <itunes:duration>{_fmt_duration(ep.get("duration_sec", 0))}</itunes:duration>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:explicit>false</itunes:explicit>
      <itunes:image href="{escape(cfg.cover_url)}"/>
    </item>""")

    owner_email = cfg.recipient or cfg.gmail_address or ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:atom="http://www.w3.org/2005/Atom"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{escape(cfg.podcast_title)}</title>
    <link>{escape(cfg.site_url)}</link>
    <atom:link href="{escape(cfg.feed_url)}" rel="self" type="application/rss+xml"/>
    <language>en-us</language>
    <copyright>&#169; {datetime.now().year} {escape(cfg.podcast_author)}</copyright>
    <description>{escape(cfg.podcast_description)}</description>
    <itunes:subtitle>One real business torn down every morning.</itunes:subtitle>
    <itunes:author>{escape(cfg.podcast_author)}</itunes:author>
    <itunes:owner>
      <itunes:name>{escape(cfg.podcast_author)}</itunes:name>
      <itunes:email>{escape(owner_email)}</itunes:email>
    </itunes:owner>
    <itunes:image href="{escape(cfg.cover_url)}"/>
    <image>
      <url>{escape(cfg.cover_url)}</url>
      <title>{escape(cfg.podcast_title)}</title>
      <link>{escape(cfg.site_url)}</link>
    </image>
    <itunes:category text="Business">
      <itunes:category text="Entrepreneurship"/>
    </itunes:category>
    <itunes:explicit>false</itunes:explicit>
    <itunes:type>episodic</itunes:type>
    <lastBuildDate>{format_datetime(datetime.now().astimezone())}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
"""


def write_feed(cfg: Config, episodes: list[dict], path: Path = DOCS / "feed.xml") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_feed(cfg, episodes), encoding="utf-8")
    return path
