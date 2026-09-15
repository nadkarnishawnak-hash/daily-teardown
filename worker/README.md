# Jarvis backend (Cloudflare Worker)

The public `jarvis.html` page never holds a secret. Everything sensitive lives here.

## Deploy (dashboard, no CLI) - about 10 minutes

1. https://dash.cloudflare.com -> sign up (free, email only) -> **Workers & Pages -> Create -> Create Worker** -> name it `jarvis` -> Deploy.
2. Click **Edit code**, delete the sample, paste the whole of `worker.js`, **Deploy**.
3. **Settings -> Variables and Secrets**. Add each of these (type = *Secret* for keys, *Text* for the rest):

| Name | Type | Value |
|---|---|---|
| `JARVIS_PIN` | Secret | any 4-8 digit PIN you'll type once on the page (keeps strangers from spending your money) |
| `OPENAI_API_KEY` | Secret | platform.openai.com -> API keys (needs a card; this is the voice engine) |
| `ANTHROPIC_API_KEY` | Secret | same key as the morning pipeline (for live research questions) |
| `PICOVOICE_ACCESS_KEY` | Secret | console.picovoice.ai -> AccessKey (free for personal use; powers "Hey Jarvis") |
| `GITHUB_TOKEN` | Secret | github.com -> Settings -> Developer settings -> Fine-grained tokens -> only this repo, permission **Contents: Read and write** (lets Jarvis queue businesses and save notes) |
| `GITHUB_REPO` | Text | `yourname/daily-teardown` |
| `ALLOWED_ORIGIN` | Text | `https://yourname.github.io` |
| `USER_NAME` | Text | what Jarvis calls you (default `sir`) |
| `REALTIME_VOICE` | Text | `cedar` (default), `marin`, `ash`, `echo`, `sage`, `verse`, `alloy`, `shimmer`, `coral`, `ballad` |

4. Copy the Worker URL (`https://jarvis.<your-subdomain>.workers.dev`).
5. In the GitHub repo: Settings -> Secrets and variables -> Actions -> **Variables** -> add `JARVIS_WORKER_URL` = that URL. From the next morning run on, the email has a **Talk to Jarvis** link and the page knows where its backend is. (Until then, the page will just ask you for the URL once.)

Optional: `PORCUPINE_KEYWORD_URL` - if you train a custom "Hey Jarvis" keyword at console.picovoice.ai (Web platform, download the `.ppn`), commit it to `docs/hey_jarvis.ppn` and set this to `https://yourname.github.io/daily-teardown/hey_jarvis.ppn`. Without it, the built-in wake word is just "Jarvis".

## Cost
Realtime audio is billed only while the mic is streaming (conversation mode), roughly $0.05-0.15 per minute of talking. Wake-word listening is free and on-device. A few minutes of questions a day lands around $5-15/month.
