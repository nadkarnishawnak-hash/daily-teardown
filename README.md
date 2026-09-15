# The Daily Teardown

A fully automated daily business-intelligence brief. Every morning at 7am ET a GitHub Action:

1. Reads the log of past editions and picks the next **business-model archetype** in rotation
   (razor-and-blades, arbitrage, productized service, marketplace, licensing, subscription/consumable,
   high-ticket niche, commoditize-the-complement, aggregator, done-for-you, rip-and-rebrand).
2. Researches ONE real, recent business live on the web (Claude + server-side web search) and writes the
   teardown: hook, setup + "guess before you scroll", numbers with sources, model, why it works, where else it
   shows up, how you'd start one, takeaway, confidence note.
3. Adds 4-6 "what else is moving" quick hits from the last 24-48h (AI tools, startups, DTC/marketing).
4. Writes a separate listen-optimized script and turns it into a ~4-5 minute MP3.
5. Uploads the MP3 to GitHub Releases, regenerates the podcast RSS feed + searchable archive site on GitHub
   Pages, appends to the log and markdown archive, and commits it all.
6. Emails you the HTML brief with the audio link at the top.

Sundays replace the teardown with a **pattern synthesis** of the week. Reply to any email with a business
name or link and it gets **queued** for a future edition.

```
src/run.py       orchestrator (CLI)          src/render.py    HTML email / archive page
src/content.py   teardown / synthesis / hits src/tts.py       Edge (free) | Google | OpenAI | ElevenLabs
src/prompts.py   the prompts                 src/podcast.py   cover art, MP3 hosting, RSS feed
src/llm.py       Claude + web search         src/archive.py   markdown + static site + search index
src/store.py     log / queue / rotation      src/capture.py   IMAP reply capture
src/mailer.py    Gmail SMTP                  data/            log.json, queue.json, episodes.json
docs/            GitHub Pages site (feed.xml, cover.png, index.html, editions/, odin.html)
archive/         markdown copy of every edition
worker/          Cloudflare Worker backend for Odin (keys live here, never in the page)
```

## Setup (about 20 minutes, once)

### 1. Create the repo
1. Create a **public** GitHub repository (public = free unlimited Actions minutes + free Pages + free release hosting).
   Name it e.g. `daily-teardown`.
2. Upload this folder's contents to it (drag-and-drop in the GitHub web UI works, or `git push`).
   Make sure the `.github/workflows/daily.yml` file made it in.

### 2. Get the keys
| Key | Where |
|---|---|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com/ -> API Keys. Add a few dollars of credit. |
| `GMAIL_APP_PASSWORD` | Turn on 2-Step Verification for your Google account, then https://myaccount.google.com/apppasswords -> create one named "teardown". Copy the 16 characters. |
| `ELEVENLABS_API_KEY` *(optional, best voice)* | https://elevenlabs.io -> Profile -> API keys. Starter/Creator plan. |
| `OPENAI_API_KEY` *(optional, good voice, cheap)* | https://platform.openai.com/api-keys |
| `GOOGLE_TTS_API_KEY` *(optional)* | Google Cloud console -> enable "Cloud Text-to-Speech API" -> Credentials -> API key. Needs billing enabled. |

### 3. Add secrets and variables
Repo -> **Settings -> Secrets and variables -> Actions**.

**Secrets** (required): `ANTHROPIC_API_KEY`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `RECIPIENT_EMAIL`
**Secrets** (optional): `ELEVENLABS_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_TTS_API_KEY`
**Variables** (optional, tab next to Secrets): `CLAUDE_MODEL`, `CLAUDE_EFFORT`, `TTS_PROVIDER`, `TTS_VOICE`,
`PODCAST_TITLE`, `PODCAST_AUTHOR`, `SITE_URL`

`GITHUB_TOKEN` is provided automatically; do not add it.

### 4. Turn on GitHub Pages
Repo -> **Settings -> Pages -> Source: "GitHub Actions"**. (The workflow also tries to enable this itself.)
Your site will be `https://<you>.github.io/<repo>/` and the feed `https://<you>.github.io/<repo>/feed.xml`.

### 5. Allow the workflow to write
Repo -> **Settings -> Actions -> General -> Workflow permissions -> "Read and write permissions"** -> Save.

### 6. Test it in the cloud (no local Python needed)
Repo -> **Actions -> Daily Teardown -> Run workflow**.
- First tick **fixture** = true. This sends a `[TEST]` email with sample content and real audio, publishes nothing.
  Cost: $0.
- Then run again with both boxes unticked. This is a real edition: it researches, emails you, uploads the MP3,
  builds the feed, deploys the site, and commits. Takes 3-6 minutes.

After the first real run, open `https://<you>.github.io/<repo>/feed.xml` in a browser and confirm it has one `<item>`.

### 7. Submit the feed to podcast apps (once)
- **Spotify**: https://creators.spotify.com -> Get started -> "I have a podcast" / add via RSS -> paste the feed URL.
  Spotify emails a verification code to the `<itunes:owner>` email (your `RECIPIENT_EMAIL`). Paste it. Done: every
  new episode appears automatically within an hour or so of 7am.
- **Apple Podcasts**: https://podcastsconnect.apple.com -> add show via RSS (needs an Apple ID; review takes a few days).
- **Pocket Casts / Overcast / any app**: "Add by URL" and paste the feed URL. Works immediately, no submission.

That's it. From here it runs itself.

## Odin (voice layer, optional)
`docs/odin.html` turns the edition into a conversation: it plays the MP3, listens on-device for "Odin",
pauses, lets you ask anything (barge-in works), can look things up live, queue businesses, and save notes
(delivered in the next morning's email), then resumes where it left off. Setup is in
[worker/README.md](worker/README.md): one Cloudflare Worker (free) holding an OpenAI key (voice), your
Anthropic key (research), a Picovoice key (wake word) and a GitHub token (queue/notes). Set the repo variable
`ODIN_WORKER_URL` and every email gets a **Talk to Odin** button. Add the page to your phone's home screen;
the screen must stay on (iOS kills background mic access), so mount the phone.

## Running locally (optional)
Requires Python 3.12+ (https://www.python.org/downloads/ — tick "Add to PATH").
```bash
pip install -r requirements.txt
copy .env.example .env      # fill it in; on Mac/Linux: cp .env.example .env
```
Load the `.env` into your shell (PowerShell: `Get-Content .env | ForEach-Object { if ($_ -match '^\s*([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim()) } }`), then:

```bash
python -m src.run --fixture            # $0: sample content, real email + audio, nothing persisted
python -m src.run                      # full edition: research + email + audio (audio link is a local file)
python -m src.run --publish            # same, plus upload MP3 to GitHub Releases (needs GITHUB_REPOSITORY + a PAT in GITHUB_TOKEN)
python -m src.run --no-email --no-audio  # render only; open out/<date>-<slug>.html
python -m src.run --synthesis          # force a Sunday-style edition
```

## Schedule details
GitHub cron is UTC and ignores DST, so the workflow fires at 11:10 and 12:10 UTC and a guard step keeps only
the one that lands in the 7-8am ET window. The Python side is idempotent (one edition per ET date), so the
second firing during EDT is a no-op. GitHub may delay scheduled runs by a few minutes at busy times.

## The capture loop
Reply to any brief with a company name or URL in the body. The next morning's run reads unread replies from
`RECIPIENT_EMAIL` in the `GMAIL_ADDRESS` inbox over IMAP, queues them in `data/queue.json`, and marks them
read. Queued requests take priority over the rotation (Mondays through Saturdays). You can also edit
`data/queue.json` directly and commit.

## Costs
See the table in the setup message, or the comments in `.env.example`. Short version: the Claude research call is
the only meaningful cost (roughly $0.35-0.70 per edition on Opus 5, about half that on Sonnet 5 via
`CLAUDE_MODEL`). Everything else runs on free tiers.

## Troubleshooting
- **Email not arriving**: check the Actions log for `[mail] sent`. If SMTP auth fails, regenerate the App
  Password and make sure 2-Step Verification is on. Check spam once; mark as "not spam".
- **Audio failed**: the email still sends. Check the log for `[tts]`. If Edge TTS is flaky, add an
  `OPENAI_API_KEY` or `ELEVENLABS_API_KEY`; the provider auto-switches.
- **Feed not updating in Spotify**: open `feed.xml` directly; if the new `<item>` is there, Spotify just hasn't
  polled yet (usually < 1h).
- **Re-run today**: Actions -> Run workflow -> tick **force**.
