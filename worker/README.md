# Odin backend (Cloudflare Worker)

The public `odin.html` page never holds a secret. Everything sensitive lives here.

## Deploy (dashboard, no CLI) - about 10 minutes

1. https://dash.cloudflare.com -> sign up (free, email only) -> **Workers & Pages -> Create -> Create Worker** -> name it `odin` -> Deploy.
2. Click **Edit code**, delete the sample, paste the whole of `worker.js`, **Deploy**.
3. **Settings -> Variables and Secrets**. Add each of these (type = *Secret* for keys, *Text* for the rest):

| Name | Type | Value |
|---|---|---|
| `ODIN_PIN` | Secret | any 4-8 digit PIN you'll type once on the page (keeps strangers from spending your money) |
| `OPENAI_API_KEY` | Secret | platform.openai.com -> API keys (needs a card; this is the voice engine) |
| `ANTHROPIC_API_KEY` | Secret | same key as the morning pipeline (for live research questions) |
| `PICOVOICE_ACCESS_KEY` | Secret | **optional** - console.picovoice.ai -> AccessKey (free). Only for the most accurate "Hey Odin" wake word; without it the page uses "just talk" mode (or browser speech recognition) |
| `GITHUB_TOKEN` | Secret | github.com -> Settings -> Developer settings -> Fine-grained tokens -> only this repo, permission **Contents: Read and write** (lets Odin queue businesses and save notes) |
| `GITHUB_REPO` | Text | `yourname/daily-teardown` |
| `ALLOWED_ORIGIN` | Text | `https://yourname.github.io` |
| `USER_NAME` | Text | what Odin calls you (default `sir`) |
| `REALTIME_VOICE` | Text | `ash` (default, deeper), `cedar`, `marin`, `echo`, `sage`, `verse`, `alloy`, `shimmer`, `coral`, `ballad` |

4. Copy the Worker URL (`https://odin.<your-subdomain>.workers.dev`).
5. In the GitHub repo: Settings -> Secrets and variables -> Actions -> **Variables** -> add `ODIN_WORKER_URL` = that URL. From the next morning run on, the email has a **Talk to Odin** link and the page knows where its backend is. (Until then, the page will just ask you for the URL once.)

## Wake modes
The page has four ways to interrupt, chosen under **Settings** on the page (default: `voice` if no Picovoice key, else `keyword`):
- `voice` - just start talking; the mic stays open while the teardown plays. No account needed. Best with headphones.
- `phrase` - say "Hey Odin"; the browser's own speech recognition listens. No account needed. Less accurate.
- `keyword` - say "Hey Odin" / "Jarvis"; Picovoice Porcupine runs on-device. Most accurate. Needs `PICOVOICE_ACCESS_KEY`.
- `button` - press pause on your headphones or tap the on-screen button.

For `keyword` mode, train "Hey Odin" once at console.picovoice.ai -> Porcupine -> type `Hey Odin` -> platform **Web (WASM)** -> Train -> download the `.ppn`. Save it as `docs/hey_odin.ppn` in the repo and push; the page picks it up automatically. Until that file exists, the page falls back to Porcupine's built-in wake word "Jarvis" (there is no built-in "Odin"). `PORCUPINE_KEYWORD_URL` is only needed if you host the `.ppn` somewhere other than the site.

## Cost
Realtime audio is billed only while the mic is streaming (conversation mode), roughly $0.05-0.15 per minute of talking. Wake-word listening is free and on-device. A few minutes of questions a day lands around $5-15/month.
