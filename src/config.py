"""All configuration comes from environment variables. Nothing secret lives in code."""
import os
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"          # published to GitHub Pages (feed, cover, archive site)
ARCHIVE_MD = ROOT / "archive"  # markdown archive, greppable in the repo
OUT = ROOT / "out"            # per-run scratch (mp3, html) - gitignored
SAMPLE = ROOT / "sample"

ET = ZoneInfo("America/New_York")


def env(name: str, default=None):
    v = os.environ.get(name)
    return v if v not in (None, "") else default


def _default_site_url(repo: str | None) -> str | None:
    if not repo or "/" not in repo:
        return None
    owner, name = repo.split("/", 1)
    if name.lower() == f"{owner.lower()}.github.io":
        return f"https://{owner}.github.io/"
    return f"https://{owner}.github.io/{name}/"


class Config:
    def __init__(self):
        # Brain
        self.model = env("CLAUDE_MODEL", "claude-opus-5")
        self.effort = env("CLAUDE_EFFORT", "high")
        self.max_searches = int(env("MAX_SEARCHES", "12"))

        # Email (Gmail SMTP + IMAP with one App Password)
        self.gmail_address = env("GMAIL_ADDRESS")
        self.gmail_app_password = env("GMAIL_APP_PASSWORD")
        self.recipient = env("RECIPIENT_EMAIL", self.gmail_address)

        # TTS
        self.tts_provider = env("TTS_PROVIDER", "auto")
        self.tts_voice = env("TTS_VOICE")
        self.google_tts_key = env("GOOGLE_TTS_API_KEY")
        self.openai_key = env("OPENAI_API_KEY")
        self.elevenlabs_key = env("ELEVENLABS_API_KEY")

        # Publishing
        self.github_repo = env("GITHUB_REPOSITORY")
        self.github_token = env("GITHUB_TOKEN")
        self.site_url = env("SITE_URL") or _default_site_url(self.github_repo) or "http://localhost/"
        if not self.site_url.endswith("/"):
            self.site_url += "/"

        # Jarvis (voice layer). Set to the Cloudflare Worker URL once it's deployed.
        self.jarvis_worker_url = env("JARVIS_WORKER_URL")

        # Podcast metadata
        self.podcast_title = env("PODCAST_TITLE", "The Daily Teardown")
        self.podcast_author = env("PODCAST_AUTHOR", "The Daily Teardown")
        self.podcast_description = env(
            "PODCAST_DESCRIPTION",
            "One real, recent business torn down every morning: the numbers, the model, "
            "why it works, and how you'd start one. Sundays connect the week's patterns.",
        )

    @property
    def feed_url(self) -> str:
        return self.site_url + "feed.xml"

    @property
    def cover_url(self) -> str:
        return self.site_url + "cover.png"

    @property
    def jarvis_url(self) -> str | None:
        return self.site_url + "jarvis.html" if self.jarvis_worker_url else None

    def can_email(self) -> bool:
        return bool(self.gmail_address and self.gmail_app_password and self.recipient)

    def can_publish(self) -> bool:
        return bool(self.github_repo and self.github_token)
